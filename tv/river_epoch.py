#!/usr/bin/env python3
"""THE RIVER EPOCH — drive real reels down the river and record where each one STOPS.

Konyo, 2026-09-13: *"run them through the printer .. in 10 batches each.. and monistor and test
and see"*, *"keep yo-yoing it and looping it through until it finally ends up where its suppose
to"*, and *"then epoch it so its like it was an isolated test demonstration.. but on real live and
real reel sessions"*.

⚠⚠ WHY THIS EXISTS, AND THE NUMBER THAT MAKES IT NECESSARY. `reel_retention.plan()` reports its
own rule coverage, and on his footage it says:

    FIRED (3)       recent · panels-never-banked · test-fixture
    NEVER FIRED (7) eligible · holds-proof · never-chronicle-swept · no-witness-index
                    rows-not-banked · vault-owes · zero-pages

in the lane's own words: *"nothing in this footage gets far enough down the chain to test them.
That is UNMEASURED, not fine and not broken."* **`eligible` has never fired.** Not once has a reel
been ruled safe to release, which is exactly why he says the vault has never worked. Two more rules
— `ledger-unreadable`, `target-met` — cannot fire without a free_mb target and the lane does not
count them as gaps; neither does this.

⚠⚠ NOTHING HERE DELETES ANYTHING. It reads, it re-admits (a door that only ever puts a reel BACK
at the top of the lane), and it records. Deletion is a separate act and must not happen on a lane
that has never reached its own terminus — that would be destroying his footage on the strength of
code nothing has exercised. [[unknown-stays-unknown]] [[regression-guard]]

THE EPOCH: a recorded run of N cycles. Each cycle snapshots every reel's station and every rule's
fire count, applies one pass, and snapshots again. It stops when nothing has moved for K cycles —
a fixed point — or when every target rule has fired. A stall is recorded WITH the station it
stalled at, which is the finding when it happens.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass

#: the surfaces this harness speaks for, declared in the registry's own vocabulary
SURFACES = ("river.epoch", "reel.route")

#: rules the lane itself counts as GAPS. `ledger-unreadable` and `target-met` are excluded here
#: for the lane's own stated reason — they cannot fire without a free_mb target — and excluding
#: them silently would be the thing this file exists to refuse, so they are named.
EXCLUDED = ("ledger-unreadable", "target-met")
EXCLUDED_WHY = "cannot fire without a free_mb target; the retention plan does not count them as gaps"

EPOCH_PATH = os.path.join(HERE, ".river_epoch.json")


def snapshot():
    """Where every reel stands and which rules have fired. -> dict

    Never raises. A field that could not be read comes back None, because an epoch that quietly
    records 0 for an unreadable lane would prove the opposite of what it claims.
    """
    out = {"ok": True, "why": "", "stations": {}, "tags": {}, "rules": {},
           "onDisk": None, "order": [], "candidates": None}
    try:
        import shelf_driver as SD
        st = SD.stages()
        if isinstance(st, tuple):
            st = st[0]
        rows = st.get("rows") or []
        for r in rows:
            k = str(r.get("stage"))
            out["stations"][k] = out["stations"].get(k, 0) + 1
            t = str(r.get("tag"))
            out["tags"][t] = out["tags"].get(t, 0) + 1
        out["onDisk"] = st.get("onDisk")
        out["order"] = list(st.get("stageOrder") or [])
    except Exception as e:
        out["ok"] = False
        out["why"] = "the river could not be read (%s)" % type(e).__name__
        return out
    try:
        import reel_retention as RR
        plan = RR.plan()
        if isinstance(plan, tuple):
            plan = plan[0]
        out["rules"] = dict(plan.get("coverage") or {})
        c = plan.get("candidates")
        out["candidates"] = len(c) if isinstance(c, list) else c
        out["say"] = str(plan.get("say") or "")[:300]
    except Exception as e:
        out["ok"] = False
        out["why"] = "the retention plan could not be read (%s)" % type(e).__name__
    return out


def never_fired(rules):
    """Rules the lane counts as gaps that have not fired. -> sorted list"""
    return sorted(k for k, v in (rules or {}).items() if not v and k not in EXCLUDED)


def moved(a, b):
    """Did anything change between two snapshots? -> (bool, list of what)"""
    diffs = []
    for key in ("stations", "tags", "rules"):
        for k in sorted(set((a.get(key) or {})) | set((b.get(key) or {}))):
            x = (a.get(key) or {}).get(k, 0)
            y = (b.get(key) or {}).get(k, 0)
            if x != y:
                diffs.append("%s.%s %s->%s" % (key, k, x, y))
    if a.get("onDisk") != b.get("onDisk"):
        diffs.append("onDisk %s->%s" % (a.get("onDisk"), b.get("onDisk")))
    return (bool(diffs), diffs)


def pass_once(apply=False):
    """One trip down the lane. -> dict

    ⚠ RE-ENTRY ONLY. `vault_reentry_sweep` clears a retirement so a held reel is picked up again.
    It never retires, never deletes and never touches the ledger; the worst it can cost is another
    read. `apply=False` is the default so a caller must ASK to change anything.
    """
    out = {"reentry": None, "why": ""}
    try:
        import control_app as ca
        r = ca.vault_reentry_sweep(dry=not apply)
        out["reentry"] = {"ok": r.get("ok"), "checked": r.get("checked"),
                          "readmitted": list(r.get("readmitted") or []),
                          "kept": len(r.get("kept") or []), "dry": r.get("dry")}
        out["why"] = str(r.get("why") or "")[:300]
    except Exception as e:
        out["why"] = "the re-entry door could not be opened (%s)" % type(e).__name__
    return out


def run(cycles=10, quiet_for=2, apply=False):
    """Drive the river until it stops moving or every gap rule fires. -> epoch dict"""
    first = snapshot()
    target = never_fired(first.get("rules"))
    ep = {"cycles": [], "startedRules": dict(first.get("rules") or {}),
          "targetRules": target, "excluded": list(EXCLUDED), "excludedWhy": EXCLUDED_WHY,
          "apply": bool(apply), "ok": first.get("ok"), "why": first.get("why"),
          "first": first, "last": None, "fired": [], "stillNeverFired": list(target),
          "stoppedBecause": ""}
    if not first.get("ok"):
        ep["stoppedBecause"] = "the first snapshot could not be taken: %s" % first.get("why")
        return ep
    quiet = 0
    prev = first
    for i in range(1, int(cycles) + 1):
        p = pass_once(apply=apply)
        cur = snapshot()
        did, diffs = moved(prev, cur)
        ep["cycles"].append({"n": i, "moved": did, "diffs": diffs[:20],
                             "reentry": p.get("reentry"), "why": p.get("why"),
                             "neverFired": never_fired(cur.get("rules"))})
        quiet = 0 if did else quiet + 1
        prev = cur
        if not never_fired(cur.get("rules")):
            ep["stoppedBecause"] = "every gap rule fired"
            break
        if quiet >= int(quiet_for):
            ep["stoppedBecause"] = ("nothing moved for %d consecutive cycle(s) — a fixed point. "
                                    "The river cannot advance these reels any further on its own."
                                    % quiet)
            break
    else:
        ep["stoppedBecause"] = "ran out of cycles (%d)" % cycles
    ep["last"] = prev
    still = never_fired(prev.get("rules"))
    ep["stillNeverFired"] = still
    ep["fired"] = sorted(set(target) - set(still))
    return ep


def write(ep, path=None):
    p = path or EPOCH_PATH
    io.open(p, "w", encoding="utf-8").write(json.dumps(ep, indent=1, ensure_ascii=False) + "\n")
    return p


def main():
    apply = "--apply" in sys.argv
    cycles = 10
    for i, a in enumerate(sys.argv):
        if a == "--cycles" and i + 1 < len(sys.argv):
            cycles = int(sys.argv[i + 1])
    ep = run(cycles=cycles, apply=apply)
    f = ep["first"]
    print("RIVER EPOCH — %s" % ("APPLY (re-entry will really clear retirements)" if apply else "DRY"))
    print("  stageOrder : %s" % (f.get("order") or []))
    print("  onDisk     : %s   candidates to release: %s" % (f.get("onDisk"), f.get("candidates")))
    print("  stations   : %s" % json.dumps(f.get("stations")))
    print("  tags       : %s" % json.dumps(f.get("tags")))
    print()
    print("  gap rules that had NEVER fired (%d): %s" % (len(ep["targetRules"]), ep["targetRules"]))
    print("  excluded (%d): %s" % (len(EXCLUDED), EXCLUDED_WHY))
    print()
    for c in ep["cycles"]:
        print("  cycle %-2d moved=%-5s %s" % (c["n"], c["moved"], (", ".join(c["diffs"]) or "-")[:110]))
    print()
    print("  STOPPED: %s" % ep["stoppedBecause"])
    print("  fired this epoch (%d): %s" % (len(ep["fired"]), ep["fired"] or "-"))
    print("  STILL never fired (%d): %s" % (len(ep["stillNeverFired"]), ep["stillNeverFired"]))
    p = write(ep)
    print("  epoch written to %s" % os.path.relpath(p, HERE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
