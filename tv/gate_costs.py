# -*- coding: utf-8 -*-
"""v3477 (#184 follow-up) — what each gate REALLY costs on the CI runner, so the shards balance.

⚠⚠ WHY: v3472 split the gate set by DECLARED timeout and the first sharded run came back 8m41s /
17m25s — declared timeouts do not track cost. MEASURED from that run's two job logs: 548 gates,
1,457 s of gate time, and test_control ALONE is 430 s. Balanced on the measured table the same
split is 729 s / 728 s.

The table is a MEASUREMENT with a source (the run it came from), committed so every machine cuts the
same slices. A gate the table has never seen gets the MEDIAN measured cost — new gates are usually
small, and a guess that large would re-lopside the split. Refresh from CI job logs:

    python3 tv/gate_costs.py <job-log> [<job-log> ...]

A gate no CI log has timed yet can be filled from a LOCAL run's log, as a labelled estimate that never overwrites a
measured cost (REG-1836):  python3 tv/gate_costs.py --fill-missing "<label>" <date> <log>
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE = os.path.join(HERE, "gate_costs.json")

try:
    sys.path.insert(0, HERE)
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

_ROW = re.compile(r"(✅|❌|⚠|⛔)\s+(\S+)\s+([0-9.]+)s\s")


def load(path=None):
    """-> {gate: seconds}; {} when there is NO table; None when a table exists and cannot be read.

    ⚠ #219 — v3477 answered {} for both, and swallow_ratchet caught it on CI (0 -> 1): a corrupt
    table and an absent one are different facts. Absent is a state the caller acts on (fall back to
    declared timeouts); unreadable is UNKNOWN and must say so, or the shards are silently re-cut on
    the proxy v3477 replaced and nothing tells anyone. [[unknown-stays-unknown]]
    """
    p = path or TABLE
    try:
        with io.open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        return dict((k, float(v)) for k, v in (d.get("costs") or {}).items())
    except FileNotFoundError:
        return {}
    except Exception as e:
        print("gate_costs: %s exists but could not be read (%s) — shards fall back to DECLARED "
              "timeouts, which is UNKNOWN balance, not measured" % (os.path.basename(p),
                                                                   type(e).__name__),
              file=sys.stderr)
        return None


def from_logs(paths):
    """Parse run_gates' own per-gate rows out of CI job logs. -> {gate: seconds}"""
    out = {}
    for p in paths:
        with io.open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = _ROW.search(line)
                if m:
                    out[m.group(2)] = round(float(m.group(3)), 1)
    return out


def _lock_path(table):
    return table + ".lock"


class _table_lock(object):
    """REG-1859 - an exclusive lock around load -> edit -> replace, so a writer that commits between our load and our
    replace is not lost. fcntl where it exists; where it does not (Windows) the table is edited unlocked, as before."""

    def __init__(self, table):
        self.p = _lock_path(table)
        self.fh = None

    def __enter__(self):
        try:
            import fcntl
            self.fh = io.open(self.p, "a")
            fcntl.flock(self.fh, fcntl.LOCK_EX)
        except Exception:
            pass
        return self

    def __exit__(self, *a):
        try:
            if self.fh:
                self.fh.close()          # closing releases the flock
        except Exception:
            pass


def _normalise(rec):
    """REG-1858/1860 - the header counts MEASURED gates only; estimates are counted beside them, and each fill keeps its own
    source and date (an earlier fill never reads as from the latest log). -> rec"""
    est = rec.get("localEstimates")
    if est:
        if "fills" not in est:
            est["fills"] = [{"source": est.pop("source", "unknown"), "date": est.pop("date", "unknown"),
                             "count": len(est.get("gates", []))}]
        est["count"] = len(est.get("gates", []))
    names = set((est or {}).get("gates", []))
    costs = rec.get("costs") or {}
    meas = dict((k, v) for k, v in costs.items() if k not in names)
    rec["gates"] = len(meas)
    rec["totalSeconds"] = round(sum(meas.values()), 1)
    if est:
        rec["estimatedGates"] = len(names & set(costs))
        rec["estimatedSeconds"] = round(sum(costs[k] for k in names if k in costs), 1)
    return rec


def fill_missing(paths, label, date, table=None):
    """REG-1836 - add ONLY the gates the table has never timed, from a non-CI log, and say so in the header. -> n added

    A CI-measured cost is never overwritten: a local, niced run is an ESTIMATE, recorded under `localEstimates` (names +
    one {source, date, count} per fill) so the table never passes a guess off as the runner's measurement; the headline
    gates/totalSeconds stay MEASURED-only (REG-1858). Refresh from CI logs replaces them."""
    table = table or TABLE
    found = from_logs(paths)                     # the slow read, outside the lock
    with _table_lock(table):
        with io.open(table, encoding="utf-8") as fh:
            rec = json.load(fh)
        have = rec.get("costs") or {}
        new = dict((k, v) for k, v in found.items() if k not in have)
        if not new:
            return 0
        have.update(new)
        rec["costs"] = dict(sorted(have.items()))
        est = rec.get("localEstimates") or {"gates": [], "fills": []}
        est["gates"] = sorted(set(est.get("gates", [])) | set(new))
        est.setdefault("fills", []).append({"source": label, "date": date, "count": len(new)})
        rec["localEstimates"] = est
        _normalise(rec)
        with io.open(table + ".tmp", "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
        os.replace(table + ".tmp", table)
    return len(new)


def main(argv):
    if len(argv) < 2:
        print("usage: python3 tv/gate_costs.py <ci-job-log> [<ci-job-log> ...]")
        return 2
    if argv[1] == "--fill-missing":
        # python3 tv/gate_costs.py --fill-missing "<label>" <YYYY-MM-DD> <log> [<log> ...]
        if len(argv) < 5:
            print("usage: python3 tv/gate_costs.py --fill-missing <label> <date> <log> [<log> ...]")
            return 2
        n = fill_missing(argv[4:], argv[2], argv[3])
        print("added %d local estimate(s); CI-measured costs untouched" % n)
        return 0
    costs = from_logs(argv[1:])
    if not costs:
        print("no per-gate rows found in %s — nothing written (a table of nothing is not a table)" % argv[1:])
        return 2
    rec = {"source": "run_gates per-gate rows from %d CI job log(s)" % (len(argv) - 1),
           "gates": len(costs), "totalSeconds": round(sum(costs.values()), 1),
           "costs": dict(sorted(costs.items()))}
    with io.open(TABLE + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    os.replace(TABLE + ".tmp", TABLE)
    print("wrote %s — %d gates, %.0f s" % (TABLE, len(costs), rec["totalSeconds"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
