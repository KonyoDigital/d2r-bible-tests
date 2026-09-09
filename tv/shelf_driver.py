#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎞🚚 THE SHELF DRIVER — it RUNS what retention decides, and decides nothing itself.

Konyo, 2026-09-10, choosing this over a manager AI for THE SHELF: *"1. A driver — something that
executes what reel_retention.plan() already decides. No opinions, no second predicate... 2. Heart
2.0 supervision over the driver — so a lane that stops reading goes RED on its own"*.

⚠⚠ WHY THERE IS NO SECOND PREDICATE HERE, AND WHY THAT IS THE WHOLE DESIGN.
Every serious defect found on 2026-09-10 was TWO AUTHORITIES ANSWERING ONE QUESTION:

    _chron_owed_count()   41   vs   vaultAutoread.owed        0
    _vault_lane_owes      40   vs   _vault_owed_reels         0
    plan()                 2   vs   the watchdog's predicate 19   (2026-08-28: 17 needless paid sweeps)
    `--prove` "fix the skip"   vs   propose() "the law is weak"

`control_app._vault_owed_reels` already carries the ruling in its own docstring: *"ONE DEFINITION.
The reason string is retention's, so a reel leaves this list the moment retention stops calling it
vault-blocked, and the panel and the sweeper cannot drift apart."* A manager with judgement would be
a THIRD opinion about "is this reel done" — the exact failure mode, added on purpose.

So this module asks `reel_retention.plan()` and nothing else. It carries retention's own `tag` and
`why` through untouched. If it ever starts deciding, it has become the defect it was built to avoid.
[[the-unjoined-end]] [[copy-drift]] [[feedback-contradiction-is-the-finding]]

⚠ IT NEVER DELETES. `_PRUNE_SAFE_TO_RUN` is Konyo's to arm, not this module's. `work()` reports;
`stages()` draws; neither removes a frame.
"""
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: The driver's own heartbeat. Untracked, like every other runtime record.
BEAT = os.path.join(HERE, ".shelf_driver.json")

#: Which retention tag means "a lane still owes this reel work", and which lane owes it.
#: ⚠ KEYED ON THE TAG, NOT THE SENTENCE — v2392's lesson: a `why` string is prose and improving
#: the wording must not silently change what runs. Tags come from reel_retention.RULES.
OWED_BY = {
    "never-chronicle-swept": "chronicle",
    "zero-pages":            "chronicle",
    "panels-never-banked":   "vault",
    "rows-not-banked":       "vault",
    "vault-owes":            "vault",
}

#: Tags that mean the reel is finished and held for a reason no lane can clear.
HELD = ("recent", "test-fixture", "holds-proof", "target-met",
        "no-witness-index", "ledger-unreadable")


def plan(hist=None):
    """Retention's own answer, unmodified. -> dict"""
    import reel_retention as _rr
    h = hist or os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    return _rr.plan(h)


def work(hist=None):
    """What the lanes still owe, straight off retention's plan. -> dict

    ⚠ UNKNOWN IS NOT "NOTHING OWED". A plan that could not be built returns ok False and an
    explicit why, never an empty work list — an empty list is a MEASUREMENT ("every lane is
    caught up") and must never be produced by a failed read. [[unknown-stays-unknown]]
    [[zero-needs-a-denominator]]
    """
    try:
        p = plan(hist)
    except Exception as e:
        return {"ok": False, "why": "retention could not plan (%s)" % type(e).__name__,
                "owed": None, "held": None, "releasable": None}
    if not p.get("ok"):
        return {"ok": False, "why": str(p.get("say") or "retention could not read this shelf"),
                "owed": None, "held": None, "releasable": None}
    owed, held = [], []
    for k in (p.get("kept") or []):
        tag = k.get("tag")
        row = {"reel": k.get("reel"), "tag": tag, "why": k.get("why"), "mb": k.get("mb")}
        if tag in OWED_BY:
            row["lane"] = OWED_BY[tag]
            owed.append(row)
        else:
            held.append(row)
    return {"ok": True, "why": "", "owed": owed, "held": held,
            "releasable": [c.get("reel") if isinstance(c, dict) else str(c)
                           for c in (p.get("candidates") or [])],
            "onDisk": p.get("onDisk"), "say": p.get("say")}


def stages(hist=None):
    """Every reel placed on the river, newest first. -> dict

    ⚠ NEWEST FIRST, because that is how he reads it: *"timestamps organzied from what came in
    last"*. The reel id carries the stamp (`reel_s_<ms>_<n>`), so the order is the film's own,
    never the filesystem's.
    """
    import reel_story as _rs
    w = work(hist)
    if not w.get("ok"):
        return {"ok": False, "why": w.get("why"), "rows": None}
    rows = []
    for row in (w["owed"] or []) + (w["held"] or []):
        stage = _rs.TAG_STAGE.get(row["tag"])
        rows.append(dict(row, stage=stage, ts=_reel_ts(row["reel"])))
    for r in (w["releasable"] or []):
        rows.append({"reel": r, "tag": "eligible", "why": "every lane is finished with it",
                     "lane": None, "stage": _rs.TAG_STAGE.get("eligible"), "ts": _reel_ts(r)})
    rows.sort(key=lambda r: (r["ts"] is None, -(r["ts"] or 0)))
    unplaced = [r["reel"] for r in rows if not r["stage"]]
    return {"ok": True, "why": "", "rows": rows, "stageOrder": list(_rs.STAGES),
            "unplaced": unplaced, "onDisk": w.get("onDisk")}


def _reel_ts(reel):
    """The millisecond stamp inside `reel_s_<ms>_<n>`. -> int|None (None is UNKNOWN, not 0)."""
    try:
        return int(str(reel).split("_")[2])
    except Exception:
        return None


def beat(hist=None, write=True):
    """Record that the driver looked, and what it saw. -> dict

    This is what Heart 2.0 supervises: a lane with work owed and a heartbeat that has stopped is
    the state `vaultAutoread` sat in for weeks with `reads: 0, lastTs: null` and nothing said so.
    """
    w = work(hist)
    lanes = {}
    for row in (w.get("owed") or []):
        lanes[row["lane"]] = lanes.get(row["lane"], 0) + 1
    out = {"at": int(time.time() * 1000), "ok": bool(w.get("ok")), "why": w.get("why") or "",
           "owedByLane": lanes,
           "owed": None if w.get("owed") is None else len(w["owed"]),
           "held": None if w.get("held") is None else len(w["held"]),
           "releasable": None if w.get("releasable") is None else len(w["releasable"]),
           "onDisk": w.get("onDisk")}
    if write:
        try:
            with io.open(BEAT, "w", encoding="utf-8") as fh:
                json.dump(out, fh, indent=1)
        except Exception:
            pass
    return out


def last_beat():
    """The last recorded look. -> dict|None (None means it has NEVER run — not 'nothing owed')."""
    try:
        with io.open(BEAT, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def main(argv):
    b = beat()
    print("🎞🚚 SHELF DRIVER — retention decides, this runs it")
    if not b["ok"]:
        print("   ⚠ UNMEASURED: %s" % b["why"])
        return 1
    print("   %s reel(s) on disk · %s owed · %s held · %s releasable"
          % (b["onDisk"], b["owed"], b["held"], b["releasable"]))
    for lane, n in sorted((b["owedByLane"] or {}).items()):
        print("      %-10s owes %d reel(s)" % (lane, n))
    st = stages()
    if st["ok"]:
        if st["unplaced"]:
            print("   ⚠ %d reel(s) have no stage on the river: %s"
                  % (len(st["unplaced"]), st["unplaced"][:3]))
        for s in st["stageOrder"]:
            n = sum(1 for r in st["rows"] if r["stage"] == s)
            print("      %-12s %d" % (s, n))
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable as _cs
        _cs()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
