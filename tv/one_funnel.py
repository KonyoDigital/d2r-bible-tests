#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A15 clause 2 — ONE FUNNEL: *"they all flow down the same river together, through the same
feeding and routing system, for as long as they are indistinguishable."*

⚠⚠ THE CLAUSE SPLITS INTO TWO QUESTIONS AND ONLY ONE OF THEM HAS AN ANSWER TODAY. Answering the
easy one and calling the clause done is how a task gets marked shipped while the thing he asked for
is still unbuilt, so both are reported side by side and neither speaks for the other.

    THE LADDER   — is there ONE stage vocabulary, or does a lane have its own rungs?   ANSWERABLE
    THE PASSAGE  — did each reel actually FLOW down it, in order?                      MOSTLY NOT

MEASURED 2026-09-04, his 40 reels:

    STAGES declares 6 rungs — filmed · triaged · swept · banked · vault-done · releasable
    stageIdx <-> stage is a bijection on every reel; 0 reels at a stage the ladder does not know
    OCCUPIED: idx 2 `swept` 28 · idx 5 `releasable` 12.  FOUR RUNGS EMPTY.

⚠⚠ AND AN EMPTY RUNG IS NOT AN UNUSED ONE. `reel_story._stage_of` maps a reel's current HOLD TAG to
the rung it is stuck BEFORE — so `stage` is a BLOCKER, not a trajectory. "No reel sits at `banked`"
and "no reel ever passed `banked`" are opposite facts and the field cannot tell them apart. Reading
occupancy as a route is precisely the [[measured-true-read-wrong]] defect that opened A10.

⚠ SO THE PASSAGE IS ASKED OF THE DATED WAYPOINTS INSTEAD, and it is only PARTIAL: of the six rungs,
exactly two leave a timestamp behind — `retro_triage` (40 of 40 reels) and the seal store
`vault_swept` (15 of 40). The other four leave nothing dated, so for those rungs the order a reel
travelled in is not recorded anywhere and no probe can recover it. That is the honest state of
clause 2, and it names what would change it: a dated waypoint per rung.

    python3 tv/one_funnel.py
    python3 tv/one_funnel.py --json
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: Each rung, and WHERE THE NAME OF ITS STORE COMES FROM: the module that owns the store already
#: declares it, so this quotes the constant rather than restating the filename. `None` means no
#: store records that rung at all — a fact about the pipeline, not about a reel.
#:
#: ⚠⚠ THE FIRST CUT HARDCODED "retro_triage.json" AND "vault_swept.json", AND THE CONSEQUENCE WAS
#: REPRODUCED, not imagined: rename the store in its owning module and this probe does not follow,
#: so `triaged` — 40 of 40 reels covered — silently vanishes from the dated rungs while the verdict
#: stays PARTIAL and nothing looks wrong. A wrong answer wearing a measurement's clothes.
#: [[copy-drift]] §1: name ONE source, everything else quotes it.
WAYPOINT_SOURCES = {
    "filmed":     None,
    "triaged":    ("retro_triage", "STORE"),
    "swept":      ("frame_authority", "SEAL_STORE"),
    "banked":     None,
    "vault-done": None,
    "releasable": None,
}


def _store_of(rung):
    """The store filename for a rung, asked of the module that owns it. -> (name, why)

    ⚠ A store whose owner will not import, or which stopped declaring its constant, returns None
    WITH A REASON — never a guessed filename. A guess here would read a file that may not be the
    store and report its coverage as the rung's.
    """
    src = WAYPOINT_SOURCES.get(rung)
    if not src:
        return None, "no store records this rung, so passing it leaves no trace"
    mod, const = src
    try:
        m = __import__(mod)
    except Exception as e:
        return None, "%s would not import, so its store cannot be named (%s)" % (mod, str(e)[:50])
    name = getattr(m, const, None)
    if not name:
        return None, "%s no longer declares %s, so its store cannot be named" % (mod, const)
    return str(name), ""


#: Kept as a plain name->filename view for readers and for the guard that pins it against the
#: owning modules. Built once, from the constants, never typed out a second time.
WAYPOINTS = {rung: _store_of(rung)[0] for rung in WAYPOINT_SOURCES}


def _ladder():
    """-> (rungs, why). The stage vocabulary, asked of the module that owns it."""
    try:
        import reel_story as RS
        st = tuple(getattr(RS, "STAGES", ()) or ())
        return st, ("" if st else "reel_story declares no STAGES")
    except Exception as e:
        return (), "reel_story would not import (%s)" % str(e)[:80]


def _rows():
    try:
        import reel_story as RS
        st = RS.story()
        return (st.get("reels") or []) if isinstance(st, dict) else [], ""
    except Exception as e:
        return [], "reel_story would not answer (%s)" % str(e)[:80]


def _waypoint_cover(sids):
    """For each rung with a store, how many of these reels it has a dated row for. -> dict"""
    out = {}
    for rung in WAYPOINT_SOURCES:
        store, swhy = _store_of(rung)
        if not store:
            out[rung] = {"store": None, "covered": None, "why": swhy}
            continue
        p = os.path.join(HERE, store)
        try:
            blob = json.loads(io.open(p, encoding="utf-8").read())
        except Exception as e:
            # ⚠ UNREADABLE IS NOT ZERO COVERAGE. A store we could not open tells us nothing about
            # how many reels it holds. [[unknown-stays-unknown]]
            # ⚠ AND IT NAMES THE STORE. The first cut printed only str(e)[:60], which on a real
            # path cut off mid-directory — "/Users/konyo/d2r_bible" — hiding the one word that
            # would diagnose it. The filename comes first now, then as much of the error as fits.
            out[rung] = {"store": store, "covered": None,
                         "why": "%s would not read (%s)" % (store, str(e)[-70:])}
            continue
        if not isinstance(blob, dict):
            out[rung] = {"store": store, "covered": None,
                         "why": "the store is %s, not an object" % type(blob).__name__}
            continue
        n = sum(1 for s in sids if s in blob or ("reel_" + s) in blob)
        out[rung] = {"store": store, "covered": n,
                     "why": "%d of %d reel(s) have a dated row here" % (n, len(sids))}
    return out


def funnel():
    """-> {"ok", "ladder", "passage", "rungs", "occupancy", "why"}

    Two independent readings, never merged:
      ladder  — ONE_LADDER / SPLIT_LADDER / UNKNOWN
      passage — RECORDED / PARTIAL / UNRECORDED / UNKNOWN
    """
    rungs, lwhy = _ladder()
    rows, rwhy = _rows()
    if not rungs:
        return {"ok": False, "ladder": "UNKNOWN", "passage": "UNKNOWN", "rungs": [],
                "why": "UNKNOWN, not a split ladder — %s" % (lwhy or "no ladder was found")}
    if not rows:
        return {"ok": False, "ladder": "UNKNOWN", "passage": "UNKNOWN", "rungs": list(rungs),
                "why": ("UNKNOWN, not an empty shelf — %s"
                        % (rwhy or "no reel reached this probe and nothing said why"))}

    by_idx, by_stage, unknown, occupancy = {}, {}, 0, {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        stage, idx = r.get("stage"), r.get("stageIdx")
        if not r.get("stageKnown", True) or stage not in rungs:
            unknown += 1
            continue
        by_idx.setdefault(idx, set()).add(stage)
        by_stage.setdefault(stage, set()).add(idx)
        occupancy[stage] = occupancy.get(stage, 0) + 1
    # A rung naming two stages, or a stage sitting at two rungs, is two ladders sharing a vocabulary
    collisions = ([{"index": i, "stages": sorted(s)} for i, s in by_idx.items() if len(s) > 1]
                  + [{"stage": s, "indexes": sorted(i)} for s, i in by_stage.items() if len(i) > 1])
    ladder = "ONE_LADDER" if (not collisions and not unknown) else "SPLIT_LADDER"

    sids = set()
    for r in rows:
        nm = str((r or {}).get("reel") or "")
        sids.add(nm[len("reel_"):] if nm.startswith("reel_") else nm)
    cover = _waypoint_cover(sids)
    dated = [k for k, v in cover.items() if isinstance(v.get("covered"), int) and v["covered"] > 0]
    if len(dated) >= len(rungs):
        passage = "RECORDED"
    elif dated:
        passage = "PARTIAL"
    else:
        passage = "UNRECORDED"

    return {
        "ok": True, "ladder": ladder, "passage": passage,
        "rungs": list(rungs), "collisions": collisions, "unknownStage": unknown,
        "occupancy": occupancy, "waypoints": cover, "walked": len(rows),
        "datedRungs": sorted(dated), "rungCount": len(rungs),
        "why": ("ONE stage vocabulary across %d reel(s) — %d rung(s), no rung naming two stages "
                "and no stage at two rungs. ⚠ BUT THE PASSAGE IS %s: %d of %d rung(s) leave a "
                "dated waypoint (%s), so for the rest the order a reel travelled in is recorded "
                "NOWHERE. ⚠ And occupancy is not a route: `stage` is the rung a reel is stuck "
                "BEFORE, so an empty rung means nobody is stuck there — never that nobody passed."
                % (len(rows), len(rungs), passage, len(dated), len(rungs),
                   ", ".join(sorted(dated)) or "none")) if ladder == "ONE_LADDER" else
               ("SPLIT LADDER — %d collision(s) and %d reel(s) at a stage the ladder does not "
                "know. A lane with its own rungs is a lane with its own routing system, which is "
                "what A15 forbids." % (len(collisions), unknown)),
    }


def main(argv):
    r = funnel()
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True, default=list))
        return 0
    print("\nA15 clause 2 — ONE FUNNEL: do they all flow down the same river?\n")
    if not r["ok"]:
        print("  %s\n" % r["why"])
        return 0
    print("  THE LADDER   %s" % r["ladder"])
    print("  THE PASSAGE  %s   (%d of %d rungs leave a dated waypoint)"
          % (r["passage"], len(r["datedRungs"]), r["rungCount"]))
    print()
    for rung in r["rungs"]:
        w = r["waypoints"].get(rung) or {}
        occ = r["occupancy"].get(rung, 0)
        print("     %-12s occupied %2d   waypoint: %s" % (rung, occ, w.get("why", "")))
    print()
    print("  ⚠ OCCUPANCY IS NOT A ROUTE. `stage` is the rung a reel is stuck BEFORE, so an empty")
    print("    rung means nobody is stuck there — a different fact from nobody passing through.")
    print("\n  %s\n" % r["why"])
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
