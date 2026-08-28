#!/usr/bin/env python3
"""WILSON ON THE PRUNE — so arming is EARNED rather than declared.

Konyo, 2026-08-28: "put wilson badge tier confluence system here too so its proves itself and then
gets coded.. for everywhere uncertainty this is the system needs to be implanted."

⚠ WHY THE PRUNE IS THE RIGHT PLACE FOR IT, and why it was stuck without it. `_PRUNE_SAFE_TO_RUN`
is a BOOLEAN over a question that is not boolean. Measured on his 30 reels:

    measured "no"   ~5%   a frame the reader positively read and found nothing on
    panel           ~7%   held, correctly
    SILENT         ~88%   the crop was made and OCR returned ZERO lines

The disk is in that 88%, and freeing it needs proof the OCR lane was ALIVE at that moment —
otherwise "no text on this frame" and "the reader was busy" are the same observation. That is an
UNCERTAINTY, and a flag can only answer it by guessing. Wilson can answer it by accumulating.

WHAT THIS DOES: scores every pass the pruner WOULD make, against the same lower-bound and tier
weights the vault and chronicle gates use, and records it. It DECIDES NOTHING and deletes nothing.
When the record shows the bound holding above the floor across enough independent passes, arming
stops being a coin flip and becomes a reading. Until then the honest answer is "not yet, and here
is how far off it is" — which is a number he can watch, instead of a flag he has to trust.

⚠ IT CANNOT UNBLOCK THE ARCHITECTURAL FAULT ON ITS OWN, and must not pretend to. _GATE_SILENT and
_GATE_HEARD are PROCESS GLOBALS (control_app:15662-3); the console runs sweeps on other threads that
move them, so a sweep ticking _GATE_SILENT inside a prune's delta collapses a tooltip frame into the
deletable class. Per-read counters remain the prerequisite. This measures how confident the pass
WOULD be given honest inputs; it does not make dishonest inputs honest. [[unknown-stays-unknown]]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# What counts as INDEPENDENT evidence that a frame carries nothing worth keeping. Additive, and
# deliberately not capped: two kinds really are worth more than one.
PRUNE_WITNESS_TIER = {
    "reader-alive":   1.00,   # the OCR lane demonstrably answered on this pass — the load-bearing one
    "panel-agrees":   0.75,   # the panel gate independently says this is not an ownership screen
    "sig-far":        0.50,   # the frame differs materially from the kept one, so it is not a dupe
    "no-tooltip":     0.35,   # no tooltip-shaped rectangle here, so no name can be hiding on it
}
# Reasoned from the tier table, and stated as reasoned. A prune is IRREVERSIBLE, so the bar sits
# above the vault's throw bar (0.51 / 1.75): reader-alive is mandatory and one more kind is needed.
PRUNE_WILSON_FLOOR = 0.60
PRUNE_CONFLUENCE_FLOOR = 1.75


def tags_for(frame):
    """Which kinds of independence back this candidate. -> [tag]

    `frame` is a dict as the prune authority yields it. A key that is ABSENT scores nothing — it is
    not evidence, and defaulting it to true is how a bar gets cleared by silence.
    """
    t = []
    if frame.get("readerAlive") is True:
        t.append("reader-alive")
    if frame.get("panelSaysNotOwnership") is True:
        t.append("panel-agrees")
    if frame.get("sigFar") is True:
        t.append("sig-far")
    if frame.get("tooltipRect") is None and "tooltipRect" in frame:
        t.append("no-tooltip")
    return t


def score(candidates, live_would_free=None):
    """What Wilson WOULD say about this prune pass. Decides nothing. -> dict

    k = candidates whose reader was demonstrably ALIVE (the honest successes)
    n = every candidate this pass considered
    """
    import confidence as cf
    cands = [c for c in (candidates or []) if isinstance(c, dict)]
    n = len(cands)
    k = sum(1 for c in cands if c.get("readerAlive") is True)
    # confluence over the WEAKEST candidate, not the average: a pass is only as safe as the frame it
    # is least sure about, and averaging is exactly how one bad deletion hides behind ninety good
    # ones. [[feedback-contradiction-is-the-finding]]
    if cands:
        worst = min(cands, key=lambda c: cf.confluence(tags_for(c), PRUNE_WITNESS_TIER))
        tags = tags_for(worst)
    else:
        tags = []
    live = bool(live_would_free) if live_would_free is not None else bool(n)
    return cf.shadow(k, n, tags, PRUNE_WITNESS_TIER,
                     PRUNE_WILSON_FLOOR, PRUNE_CONFLUENCE_FLOOR,
                     live, lane="prune", subject="%d candidate(s)" % n)


def floors_are_reachable():
    """PROVE the bar can be cleared by evidence a real pass can produce. -> (ok, why)"""
    import confidence as cf
    ceiling = round(sum(PRUNE_WITNESS_TIER.values()), 3)
    if PRUNE_CONFLUENCE_FLOOR > ceiling:
        return False, ("the confluence floor %.2f is above the %.2f the tiers can sum to"
                       % (PRUNE_CONFLUENCE_FLOOR, ceiling))
    real = round(PRUNE_WITNESS_TIER["reader-alive"] + PRUNE_WITNESS_TIER["panel-agrees"], 3)
    if PRUNE_CONFLUENCE_FLOOR > real:
        return False, ("the floor %.2f needs more than reader-alive + panel-agrees (%.2f), which is "
                       "the cheapest pair a real pass produces" % (PRUNE_CONFLUENCE_FLOOR, real))
    # and the wilson floor must be clearable by a plausible pass size
    if cf.wilson_lower(40, 40) < PRUNE_WILSON_FLOOR:
        return False, ("40 clean candidates score %.3f, below the %.2f floor — no realistic pass "
                       "could ever clear it" % (cf.wilson_lower(40, 40), PRUNE_WILSON_FLOOR))
    return True, None


def say(row):
    """One sentence he can read on the console. -> str"""
    if not row:
        return "the prune shadow has not scored a pass yet"
    if row["n"] == 0:
        return "nothing to score — this pass had no candidates"
    verdict = ("would clear the bar" if row["wouldPass"]
               else "does NOT clear the bar")
    return ("prune confidence %s: %d of %d candidates had a live reader -> wilson %.3f "
            "(needs %.2f), confluence %.2f (needs %.2f) from %s"
            % (verdict, row["k"], row["n"], row["wilson"], row["wilsonFloor"],
               row["confluence"], row["confluenceFloor"], ", ".join(row["tags"]) or "nothing"))


def main(argv=None):
    try:
        from console_safe import enable  # noqa: F401
    except Exception:
        pass
    ok, why = floors_are_reachable()
    print("prune shadow — floors %s" % ("\U0001f7e2 reachable" if ok else "\U0001f534 %s" % why))
    demo = [{"readerAlive": True, "panelSaysNotOwnership": True, "sigFar": True,
             "tooltipRect": None} for _ in range(40)]
    print("  40 clean candidates : %s" % say(score(demo)))
    demo2 = demo[:39] + [{"readerAlive": False}]     # one frame where the reader never answered
    print("  ...one reader silent: %s" % say(score(demo2)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
