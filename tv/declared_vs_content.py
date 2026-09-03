#!/usr/bin/env python3
"""A15 — the route must be DERIVED FROM THE CONTENT, never guessed from a declared stamp.

His words: *"the same feeding system and same routing system... depending on what inititially has
been processed through out 3d printer that filters properly"* — and TASKS.md's clause: **the route
is derived from the content, never declared up front, never guessed from a filename or a focus
stamp.** ⚠ Precedent v1783 — *a default is not a declaration*: trusting an untouched "stash" stamp
labelled a town, a fight and a Chronicle page as stash panels.

⚠⚠ THE ANSWER TODAY IS **UNTESTABLE**, AND THAT IS THE POINT OF THIS FILE. Measured on his tree:

    reel dirs on disk                      40
    with an index.json                     40
    DECLARING a chronicle focus             1   ← and it carries 0 surveyed panels
    declared-vs-content disagreements       0

**Zero disagreements over one declaring reel with no content measures the SAMPLE, not the
pipeline.** Reported as CLEAN it would say the routing law holds, which nobody has shown.
[[unknown-stays-unknown]] [[gate-blind-to-unexercised-input]]

⚠ TWO SITES DO ROUTE ON A DECLARED STAMP, and one of them was nearly reported here as a defect
before its own docstring refuted me:

  · `chronicle_retro._declared_kind` reads `index.json["focus"]` to decide WHICH SWEEP owns a reel.
    That is routing by declaration — the sweep then judges content, so the declaration selects the
    reader rather than labelling the contents. Whether A15's letter forbids it is a judgement, and
    the measurement above cannot settle it either way today.
  · `reel_retention._vault_lane_owes` returns True when there is NO declared focus — which looks
    exactly like v1783 and is NOT: its docstring says *"Errs toward KEEPING... 'I could not tell'
    must never resolve to 'delete it'"*. An absent stamp HOLDS the reel. That is the safe
    direction, deliberately. [[measured-true-read-wrong]]

    python3 tv/declared_vs_content.py
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

HIST = os.path.join(HERE, "frames", "hist")
TRIAGE = os.path.join(HERE, "retro_triage.json")

AGREES = "AGREES"
DISAGREES = "DISAGREES"
UNTESTABLE = "UNTESTABLE"

#: Below this many DECLARING reels carrying surveyed content, a zero is the sample speaking.
#: Deliberately not 1: one agreeing reel is an anecdote, and this check exists because a clean
#: reading from a corpus that cannot exercise it is the failure it is guarding against.
MIN_EXERCISED = 3

#: Panel kinds that are NOT a chronicle page. A reel declaring a chronicle focus whose survey found
#: only these has a declaration its content does not support.
_NOT_CHRONICLE = ("stash", "personal", "shared", "materials", "runes", "gems")


def _triage():
    try:
        blob = json.load(io.open(TRIAGE, encoding="utf-8"))
        return (blob if isinstance(blob, dict) else None), ""
    except Exception as e:
        return None, "retro_triage.json could not be read (%s)" % str(e)[:70]


def report():
    """-> {"state", "rows", "why"}. Never says AGREES on a sample that cannot disagree."""
    tri, why = _triage()
    if tri is None:
        # ⚠ Both unreadable branches must SAY unknown. A reader who sees only the errno cannot
        # tell "the corpus is clean" from "I could not look", and this file exists for exactly
        # that distinction.
        return {"state": UNTESTABLE, "rows": [],
                "why": "UNKNOWN, not agreement — %s" % (why or "no triage store")}
    if not os.path.isdir(HIST):
        return {"state": UNTESTABLE, "rows": [],
                "why": "no reel directory at %s — that is UNKNOWN, not an empty corpus" % HIST}
    rows, declaring, exercised = [], 0, 0
    for d in sorted(os.listdir(HIST)):
        p = os.path.join(HIST, d)
        if not (d.startswith("reel_") and os.path.isdir(p)):
            continue
        try:
            ix = json.load(io.open(os.path.join(p, "index.json"), encoding="utf-8"))
        except Exception:
            continue
        focus = str((ix or {}).get("focus") or "").strip().lower()
        if not focus.startswith("chronicle"):
            continue
        declaring += 1
        t = tri.get(d) or {}
        kinds = t.get("kinds") or {}
        panels = int(t.get("panels") or 0)
        if panels <= 0 or not kinds:
            # ⚠ NO SURVEYED CONTENT IS NOT AGREEMENT. Nothing was found to compare the
            # declaration against, so this reel says nothing either way.
            rows.append({"reel": d, "focus": focus, "panels": panels, "kinds": kinds,
                         "state": UNTESTABLE,
                         "why": "the survey found no panels, so the declaration has nothing to "
                                "be checked against"})
            continue
        exercised += 1
        off = sorted(k for k in kinds if k in _NOT_CHRONICLE)
        rows.append({"reel": d, "focus": focus, "panels": panels, "kinds": kinds,
                     "state": DISAGREES if off else AGREES,
                     "why": ("declared %s, and the survey found %s — the route was taken from the "
                             "stamp, not the content" % (focus, ", ".join(off))) if off else
                            "declared %s and the survey found nothing contradicting it" % focus})
    bad = [r for r in rows if r["state"] == DISAGREES]
    if bad:
        return {"state": DISAGREES, "rows": rows, "declaring": declaring, "exercised": exercised,
                "why": "%d reel(s) carry a declaration their own content does not support" % len(bad)}
    if exercised < MIN_EXERCISED:
        return {"state": UNTESTABLE, "rows": rows, "declaring": declaring, "exercised": exercised,
                "why": ("only %d declaring reel(s) carry surveyed content (need %d). Zero "
                        "disagreements here measures the SAMPLE, not the pipeline — reported as "
                        "agreement it would say the routing law holds, which nobody has shown."
                        % (exercised, MIN_EXERCISED))}
    return {"state": AGREES, "rows": rows, "declaring": declaring, "exercised": exercised,
            "why": "%d declaring reel(s) with content, none contradicted by its own survey" % exercised}


def main(argv):
    r = report()
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    print("\nDECLARED vs CONTENT — is the route taken from the stamp or from what is in the reel?\n")
    for row in r["rows"]:
        mark = {DISAGREES: "⚠ ", AGREES: "  ", UNTESTABLE: "? "}.get(row["state"], "  ")
        print("%s%-30s %-20s panels=%-4s %s" % (mark, row["reel"][:30], row["focus"],
                                                row["panels"], row["why"][:60]))
    print("\n  %s\n  %s" % (r["state"], r["why"]))
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    raise SystemExit(main(sys.argv[1:]))
