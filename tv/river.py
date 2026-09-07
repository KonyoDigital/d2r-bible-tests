"""THE RIVER — stream one fish through every joint and report which ones actually carry.

Konyo, 2026-09-01: *"i want you streaming little tiny fish down streams and see that they are
connected and running properly — my analogy is for reels going through. monitor and reverse
engineer it, see how its connected and synced, and make sure these are unified where they need
to be and individually coded as PARTS like we mentioned already for a reason. just design it
correctly."*

WHAT IT IS. The pipeline is a river: material enters at CAPTURE and flows through SURVEY, READ,
GATE, SEAL and PRUNE. Between each pair of stages is a JOINT — a place one stage hands something
to the next. This module walks every joint and asks one question: **is anything actually
crossing it?**

WHY IT EXISTS, and it is the same failure four times in one day. A joint can be wired at both
ends, tested, and carry nothing — and a joint carrying nothing looks EXACTLY like a joint with
nothing to carry. Every instance found so far:

    surface     the reader knows which tab a frame showed; the sighting does not record it
                -> 8,300 sightings, 0 surfaces, and v2380's cross-surface witness can never fire
    slot        `slot_identity.slot_tags()` earns `same-slot` corroboration and had NO caller
                outside its own tests; joined at v2393 and STILL dry, because real sightings
                carry no point/panelBox/container either
    per-frame   `gate()` returns a tab name per frame; the store was handed `{"panel": N}`
                -> the prune is stuck at REEL granularity, 3.2 GB held for 104 frames
    vault lane  ran every 45s since it was built and swept nothing; `owed: 0` read as healthy

Each was found BY HAND, after he asked. He asked the right question — *"how do we find these
before i tell you about them?"* — and this file is the answer.

THE FOUR VERDICTS, and the third is the entire point:

    CARRIES   material crossed. n > 0.
    STARVED   nothing crossed AND nothing was upstream. Correct silence — not a defect.
    DRY       nothing crossed WHILE MATERIAL WAS WAITING UPSTREAM. **This is a defect.**
    UNKNOWN   the joint could not be measured. Never reported as either of the above.

⚠ DRY vs STARVED IS THE WHOLE INSTRUMENT. Collapsing them is what let every defect above hide:
a lane with nothing to do and a lane that cannot do anything publish identical numbers.
[[unknown-stays-unknown]] [[the-unjoined-end]] [[heart-first]]

⚠ IT READS AND DECIDES NOTHING. No deletion, no seal, no write of any kind. It is an instrument,
and an instrument that can change what it measures is not one. The apply stays his.
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ THIS FILE PRINTS ⚠ AND ARROWS. Without this, a non-UTF-8 console makes it crash while
# REPORTING — so a perfectly healthy tree exits non-zero for a reason that has nothing to do with
# the river. Caught by TestToolsCanReportTheirVerdict before it shipped.
try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass

CARRIES, STARVED, DRY, UNKNOWN = "CARRIES", "STARVED", "DRY", "UNKNOWN"

# order matters — it is the river
STAGES = ("capture", "survey", "frame-verdict", "read", "sighting",
          "surface", "slot", "gate", "seal", "prune", "disk")


def _ring(pattern):
    """Every file in a rotating journal's ring, oldest first.

    ⚠ THE LIVE FILE IS NOT THE RECORD. `sessions.jsonl` is 2.3 MB while the rotated
    `sessions.1.jsonl` beside it is 4.0 MB — reading only the live file loses more than half the
    history and has already caused one CORRECT measurement to be retracted.
    [[journal-ring-not-the-live-file]]
    """
    import glob
    return sorted(glob.glob(os.path.join(HERE, pattern)))


def _hist_dir():
    """Where the footage actually is. -> path or None

    ⚠ RESOLVED THE SAME WAY THE CONSOLE DOES, and the first cut of this did not. It guessed
    `~/Library/Application Support/TV DIABLO/history`, found nothing, and reported capture,
    prune and disk as UNKNOWN — which reads as "the pipeline could not be measured" when the real
    answer was "the instrument looked in the wrong place". A probe that fails on its own REACH
    and reports it as a fact about the system is worse than no probe.
    `control_app.py:113` is the authority: TV_HIST, else <tv>/frames/hist.
    [[source-reading-guard]] [[feedback-suspect-the-instrument]]
    """
    c = os.environ.get("TV_HIST")
    if c and os.path.isdir(c):
        return c
    d = os.path.join(HERE, "frames", "hist")
    return d if os.path.isdir(d) else None


def _joint(name, what, n, upstream, why="", unit="item"):
    """Grade one joint. -> dict

    `n` is what CROSSED. `upstream` is what was WAITING. Either may be None for UNKNOWN, and None
    is never silently turned into 0 — that substitution is the defect this module exists to find.
    """
    if n is None or upstream is None:
        state = UNKNOWN
    elif n > 0:
        state = CARRIES
    elif upstream > 0:
        state = DRY
    else:
        state = STARVED
    return {"joint": name, "what": what, "crossed": n, "upstream": upstream,
            "state": state, "why": why, "unit": unit}


# ══ THE JOINTS ══════════════════════════════════════════════════════════════════════════════
# Each returns a dict from _joint(). Each is INDEPENDENTLY coded — his standing instruction is
# that the parts stay parts ("anything with exceptions are already coded properly by design
# individually in parts... i want it connecting and synced"). What is unified is the QUESTION
# they answer and the vocabulary they answer it in, never their internals.

def j_capture():
    """disk -> reels. Is footage arriving at all?"""
    h = _hist_dir()
    if not h:
        return _joint("capture", "reels on disk", None, None,
                      "no history directory found — TV_HIST unset and the default is absent",
                      "reel")
    try:
        reels = [d for d in os.listdir(h) if os.path.isdir(os.path.join(h, d))]
    except OSError as e:
        return _joint("capture", "reels on disk", None, None, str(e)[:70], "reel")
    # upstream for capture is the game itself, which we cannot measure — so a zero here is
    # UNKNOWN-shaped, not STARVED. Report the count and say the upstream is unmeasurable.
    return _joint("capture", "reels on disk", len(reels), len(reels) or None,
                  "the upstream of capture is him playing, which this cannot measure", "reel")


def j_survey():
    """reels -> surveyed. Has the free structural filter looked at them?"""
    try:
        import retro_triage as RT
        blob, ok = RT.load(None)
        if not ok:
            return _joint("survey", "reels surveyed", None, None, "survey store unreadable", "reel")
        full = sum(1 for v in (blob or {}).values() if v.get("full"))
    except Exception as e:
        return _joint("survey", "reels surveyed", None, None, str(e)[:70], "reel")
    cap = j_capture()
    return _joint("survey", "reels surveyed", full, cap.get("crossed"),
                  "a reel nobody surveyed is UNKNOWN, never empty", "reel")


def j_frame_verdict():
    """surveyed -> per-frame verdict. Can the prune act on ONE frame, or only a whole reel?"""
    try:
        import retro_triage as RT
        blob, ok = RT.load(None)
        if not ok:
            return _joint("frame-verdict", "reels with a per-frame verdict", None, None,
                          "survey store unreadable", "reel")
        withpf = sum(1 for v in (blob or {}).values() if v.get("panelFrames") is not None)
        full = sum(1 for v in (blob or {}).values() if v.get("full"))
    except Exception as e:
        return _joint("frame-verdict", "reels with a per-frame verdict", None, None, str(e)[:70], "reel")
    return _joint("frame-verdict", "reels with a per-frame verdict", withpf, full,
                  "without this the prune is stuck at REEL granularity — v2393 writes it, but "
                  "only for reels surveyed SINCE v2393; older rows are UNKNOWN, not empty", "reel")


def j_read():
    """surveyed -> read. Has a paid reader actually looked at what carries something?"""
    try:
        import retro_triage as RT
        blob, ok = RT.load(None)
        if not ok:
            return _joint("read", "reels sealed", None, None, "survey store unreadable", "reel")
        worth = sum(1 for v in (blob or {}).values() if v.get("full") and v.get("panels"))
    except Exception as e:
        return _joint("read", "reels sealed", None, None, str(e)[:70], "reel")
    sealed = None
    try:
        p = os.path.join(HERE, "chronicle_swept.json")
        if os.path.isfile(p):
            d = json.load(io.open(p, encoding="utf-8"))
            sealed = len(d) if isinstance(d, (dict, list)) else None
    except Exception:
        sealed = None
    return _joint("read", "reels sealed", sealed, worth,
                  "a reel the survey says CARRIES something and nobody read is the backlog", "reel")


def _sightings():
    """Every sighting in the evidence store, flattened. -> list (possibly empty) or None."""
    p = os.path.join(HERE, "chron_evidence.json")
    if not os.path.isfile(p):
        return None
    try:
        ev = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        return None
    out = []
    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                if isinstance(v, dict) and ("reel" in v or "frame" in v):
                    out.append(v)
                else:
                    walk(v)
    walk(ev)
    return out


def j_sighting():
    """read -> sighting. Did the reads leave evidence behind?"""
    ss = _sightings()
    if ss is None:
        return _joint("sighting", "sightings recorded", None, None,
                      "chron_evidence.json absent or unreadable", "sighting")
    r = j_read()
    return _joint("sighting", "sightings recorded", len(ss), r.get("crossed"),
                  "", "sighting")


def j_surface():
    """sighting -> surface. Does a sighting say WHERE on screen it was seen?

    v2380 built a `cross-surface` witness: the same item on the floor, in the inventory and in
    the Chronicle list is three independent looks. It can only fire if sightings carry a surface.
    """
    ss = _sightings()
    if ss is None:
        return _joint("surface", "sightings carrying a surface", None, None,
                      "chron_evidence.json absent or unreadable", "sighting")
    n = sum(1 for s in ss if str(s.get("surface") or "").strip())
    return _joint("surface", "sightings carrying a surface", n, len(ss),
                  "the reader knows which tab the frame showed and does not persist it — so the "
                  "cross-surface witness cannot fire on any of them", "sighting")


def j_slot():
    """sighting -> slot. Does a sighting carry the material to name its CELL?

    `slot_identity.slot_tags()` earns `same-slot`: two reads agreeing on the cell agree about a
    second, independent fact, which a shared misread of the TEXT cannot fake. Joined into
    `witnesses()` at v2393.

    ⚠ A SLOT IS A WITNESS, NEVER A NAME. A stash grid carries no item names — v1861 design,
    re-confirmed on his 31 reels. The cell corroborates a name something else proposed.
    """
    ss = _sightings()
    if ss is None:
        return _joint("slot", "sightings with a derivable slot", None, None,
                      "chron_evidence.json absent or unreadable", "sighting")
    try:
        import slot_identity as SI
        n = sum(1 for s in ss if SI.slot_of_sighting(s))
    except Exception as e:
        return _joint("slot", "sightings with a derivable slot", None, None, str(e)[:70], "sighting")
    return _joint("slot", "sightings with a derivable slot", n, len(ss),
                  "needs point + panelBox + container on the sighting; the reader has all three "
                  "at the moment it reads and records none of them", "sighting")


def j_gate():
    """sighting -> grounded. Did evidence become a name he can act on?"""
    ss = _sightings()
    up = len(ss) if ss is not None else None
    p = os.path.join(HERE, "chron_last_result.json")
    if not os.path.isfile(p):
        return _joint("gate", "names grounded", None, up, "no last-result store", "name")
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception as e:
        return _joint("gate", "names grounded", None, up, str(e)[:70], "name")
    # ⚠⚠ v2761 — THIS JOINT ASKED FOR THREE KEYS THE STORE HAS NEVER WRITTEN, and reported the
    # miss as a hard 0. MEASURED on his live chron_last_result.json — the result carries
    # ['calibration','contested','contestedExpired','denial','fold','held','hunt','lanes',
    #  'newlyDated','notFoundDatable','reels','refused','refusedEver','resolverOk','setGroups',
    #  'totals','verdict','wouldAdd'] — and NOT grounded, applied or accepted. So the river's own
    # diagnosis said "gate DRY, 0 names grounded of 14,034" for a joint that was never measured.
    # A zero with no denominator, living inside the instrument that diagnoses the river.
    # [[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]
    #
    # ⚠ AND THE TRUE STATE IS NOT "BLOCKED". `newlyDated` is what a sweep writes when a name
    # actually grounds. His last sweep: wouldAdd 271 uniques + 83 sets = 354 proposed, and
    # /api/chronicle_crossref answers "354 of the 354 read are already in your chronicle; 0 are
    # new". So NOTHING NEW TO GROUND is the honest reading — a legitimate state that this joint
    # could not tell apart from a blockage, because both rendered as 0.
    #
    # THREE STATES, NOT TWO:
    #   nothing was proposed          -> UNKNOWN, there is no question to answer yet
    #   proposed, and some grounded   -> CARRIES
    #   proposed, and NONE grounded   -> DRY, and that is a real blockage worth his attention
    # ⚠⚠ AND THE ORIGINAL MISS WAS TWO DEFECTS, NOT ONE. Reading the right keys exposed the
    # second immediately: the sweep store is {"proposal", "result", "savedTs"} and EVERY figure
    # lives under `result`. So the old code asked the TOP level for grounded/applied/accepted and
    # would have missed them even if they had been the right names. Two wrong things pointing the
    # same way is why this read as a confident 0 for so long.
    d = (d.get("result") if isinstance(d.get("result"), dict) else d)
    wa = d.get("wouldAdd")
    proposed = 0
    if isinstance(wa, dict):
        for v in wa.values():
            proposed += (len(v) if isinstance(v, (list, dict)) else int(v or 0))
    elif isinstance(wa, (list, dict)):
        proposed = len(wa)
    nd = d.get("newlyDated")
    grounded = len(nd) if isinstance(nd, (list, dict)) else None
    held = d.get("held")
    n_held = len(held) if isinstance(held, (list, dict)) else 0
    if grounded is None:
        return _joint("gate", "names grounded", None, up,
                      "this sweep result carries no `newlyDated`, so nothing here can say whether "
                      "a name grounded — absent is not zero", "name")
    if not proposed:
        return _joint("gate", "names grounded", None, up,
                      "no name was proposed by the last sweep (%d held), so there was nothing to "
                      "ground — that is an empty question, not a dry joint" % n_held, "name")
    why = ("" if grounded else
           "%d name(s) were proposed and none grounded (%d held). ⚠ CHECK BEFORE ACTING: if the "
           "crossref says he already has them all, this is 'nothing NEW to ground' and not a "
           "blockage." % (proposed, n_held))
    return _joint("gate", "names grounded", grounded, proposed, why, "name")


def j_seal():
    """grounded -> sealed. Is the reel's verdict durable?"""
    p = os.path.join(HERE, "chronicle_swept.json")
    if not os.path.isfile(p):
        return _joint("seal", "seals written", None, None, "no seal store", "seal")
    try:
        d = json.load(io.open(p, encoding="utf-8"))
        n = len(d) if isinstance(d, (dict, list)) else None
    except Exception as e:
        return _joint("seal", "seals written", None, None, str(e)[:70], "seal")
    return _joint("seal", "seals written", n, j_read().get("upstream"), "", "seal")


def j_prune():
    """sealed -> releasable. Would the planner let anything go?"""
    h = _hist_dir()
    if not h:
        return _joint("prune", "reels the planner would release", None, None,
                      "no history directory", "reel")
    try:
        import reel_retention as RR
        plan = RR.plan(h)
        gone = len(plan.get("delete") or plan.get("remove") or [])
        kept = len(plan.get("kept") or [])
    except Exception as e:
        return _joint("prune", "reels the planner would release", None, None, str(e)[:70], "reel")
    return _joint("prune", "reels the planner would release", gone, gone + kept,
                  "a planner that releases nothing while the disk is full is the blockage", "reel")


def j_disk():
    """releasable -> freed. Did the disk actually change?"""
    h = _hist_dir()
    if not h:
        return _joint("disk", "GB free", None, None, "no history directory", "GB")
    try:
        st = os.statvfs(h)
        free_gb = (st.f_bavail * st.f_frsize) / (1024.0 ** 3)
    except Exception as e:
        return _joint("disk", "GB free", None, None, str(e)[:70], "GB")
    pr = j_prune()
    return _joint("disk", "GB free", round(free_gb, 1), pr.get("crossed"),
                  "capture refuses below its floor, so this joint gates the whole river", "GB")


JOINTS = (j_capture, j_survey, j_frame_verdict, j_read, j_sighting,
          j_surface, j_slot, j_gate, j_seal, j_prune, j_disk)


def trace():
    """Walk every joint. -> list of joint dicts, in river order."""
    out = []
    for f in JOINTS:
        try:
            out.append(f())
        except Exception as e:
            out.append(_joint(f.__name__[2:], "(the probe itself failed)", None, None,
                              "%s: %s" % (type(e).__name__, str(e)[:60])))
    return out


def summary(rows=None):
    """One line per state, plus the first DRY joint — which is where the river is blocked."""
    rows = rows if rows is not None else trace()
    by = {}
    for r in rows:
        by.setdefault(r["state"], []).append(r["joint"])
    first_dry = next((r for r in rows if r["state"] == DRY), None)
    return {
        "counts": {k: len(v) for k, v in sorted(by.items())},
        "dry": by.get(DRY, []),
        "unknown": by.get(UNKNOWN, []),
        "firstBlockage": (first_dry or {}).get("joint"),
        "say": ("the river is blocked at %r — %s" % (first_dry["joint"], first_dry["why"])
                if first_dry else "no joint is dry"),
    }


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    rows = trace()
    if "--json" in argv:
        print(json.dumps({"joints": rows, "summary": summary(rows)}, indent=2))
        return 0
    print("THE RIVER — one fish, every joint\n")
    print("  %-14s %-34s %10s %10s  %s" % ("joint", "what crosses", "crossed", "upstream", "state"))
    print("  " + "-" * 92)
    for r in rows:
        c = "?" if r["crossed"] is None else str(r["crossed"])
        u = "?" if r["upstream"] is None else str(r["upstream"])
        print("  %-14s %-34s %10s %10s  %s" % (r["joint"], r["what"][:34], c, u, r["state"]))
    s = summary(rows)
    print("\n  " + json.dumps(s["counts"]))
    print("  " + s["say"])
    for r in rows:
        if r["state"] in (DRY, UNKNOWN) and r["why"]:
            print("\n  %-8s %-14s %s" % (r["state"], r["joint"], r["why"]))
    # ⚠ EXIT 0 ALWAYS. This is an instrument, not a gate. A DRY joint is a finding to act on,
    # and turning it into a build failure is how a real signal becomes furniture.
    return 0


if __name__ == "__main__":
    sys.exit(main())
