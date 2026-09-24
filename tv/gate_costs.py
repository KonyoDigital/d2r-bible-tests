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


def main(argv):
    if len(argv) < 2:
        print("usage: python3 tv/gate_costs.py <ci-job-log> [<ci-job-log> ...]")
        return 2
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
