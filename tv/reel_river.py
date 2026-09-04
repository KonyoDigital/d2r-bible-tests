#!/usr/bin/env python3
"""A10 — THE FISH DOWN THE STREAM: follow one reel through every stage, and name who decided.

His ask: *"the fish needs to go down the stream.. probe it down the stream meaning the reel needs
to go do the river stream an see that its properly syncned and no gaps... and everything is working
and collaborating.. and all is working an nothing is stale"*.

⚠⚠ WHAT THIS IS FOR, AND THE MISTAKE THAT SHAPED IT. Building this, I measured two stage reports
and read them as a contradiction:

    reel_story      12 reels are RELEASABLE — "both lanes done; it may be pruned"
    printer_reach    0 seals satisfy frame_authority's EXTRACTION_CONTRACT

Twelve reels cleared to go, and the deletion authority refusing every one. It looks like exactly
the defect this repo keeps producing — and it is NOT one. `reel_retention` already settled it in
v2314, in a comment I had not read when I took the measurement:

    "frame_authority is stricter because it answers a DIFFERENT question — may this FRAME go,
     protecting the witness frames behind his vault rows — not may this REEL go. Two authorities
     at two granularities is correct; collapsing them was my error."

The v2312 attempt to collapse them was WITHDRAWN because it would have stopped the prune firing on
every existing reel. So the two numbers are both right and answer different questions.

**AND NOTHING ON ANY SCREEN SAYS SO.** That is the actual gap, and it is the one A10 names: two
stages that each work, meeting only in a reader's head, where they read as a contradiction. I am
the reader it already misled. So this module reports every stage WITH THE DECIDER AND THE QUESTION
IT ANSWERED, and calls a disagreement a GAP only when two deciders answer the SAME question
differently. [[measured-true-read-wrong]] [[the-unjoined-end]]

    python3 tv/reel_river.py                  # every reel on the shelf, one line each
    python3 tv/reel_river.py <reel>           # one fish, every stage it passed
    python3 tv/reel_river.py --json
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: Each stage, the module that DECIDES it, and — the part that matters — the question it answers.
#: Two deciders may disagree freely while answering different questions; that is not a gap.
QUESTIONS = {
    "filmed":     ("reel_retention.plan", "does this reel exist on disk?"),
    "triaged":    ("retro_triage",        "did a structural pass record what this reel holds?"),
    "swept":      ("reel_retention.plan", "did the chronicle lane read its pages?"),
    "banked":     ("reel_retention.plan", "did its rows reach the durable ledger?"),
    "vault-done": ("reel_retention.plan", "is the vault lane finished with this REEL?"),
    "releasable": ("reel_retention.plan", "may this REEL go? (reel granularity)"),
}

#: ⚠ A DIFFERENT QUESTION, DELIBERATELY, AND NOT A SECOND OPINION ON THE ONE ABOVE.
FRAME_QUESTION = ("frame_authority.seal_covers_extraction",
                  "may this FRAME go? (frame granularity — it protects the witness frames behind "
                  "his vault rows, which is why it is stricter and why collapsing the two was "
                  "withdrawn in v2314)")


def _story():
    try:
        import reel_story as RS
        st = RS.story()
        return (st.get("reels") or []) if isinstance(st, dict) else [], ""
    except Exception as e:
        return [], "reel_story would not answer (%s)" % str(e)[:80]


def _seals():
    try:
        import frame_authority as FA
        blob, ok = FA.sealed_sessions()
        return (blob if ok and isinstance(blob, dict) else {}), FA, ("" if ok else "unreadable")
    except Exception as e:
        return {}, None, "frame_authority would not answer (%s)" % str(e)[:80]


def _session_of(reel):
    r = str(reel or "")
    return r[len("reel_"):] if r.startswith("reel_") else r


def river(reel=None):
    """Walk the river. -> {"ok", "rows", "gaps", "why"}

    A row per reel, carrying every stage it has reached and, separately, what the FRAME authority
    says. `gaps` holds only same-question disagreements — of which there are, correctly, none.
    """
    rows, why = _story()
    if not rows:
        # ⚠ THE FRAMING IS PART OF THE ANSWER AND THE FIRST CUT DROPPED IT. When _story() supplied
        # a reason, that reason was returned verbatim — so "reel_story would not answer" reached
        # the reader with nothing saying whether the shelf is EMPTY or merely UNREAD. Those are
        # opposite facts about his footage. [[unknown-stays-unknown]]
        # ⚠⚠ REG-560 — EVERY RETURN CARRIES THE SAME KEYS, and this one dropped `clean` and
        # `namelessRows` on exactly the path that means nothing was established. The same defect as
        # REG-544/546/547, in a module the cross-probe SHAPE LAW HAD NEVER BEEN ASKED ABOUT —
        # `reel_river` feeds the printer and is not in PROBES, so the law that exists to catch this
        # could not see it. A law is only asked of what you put in front of it.
        return {"ok": False, "state": "UNKNOWN", "rows": [], "gaps": [], "namelessRows": 0,
                "clean": {"byReelDoor": 0, "byFrameContract": 0, "byBoth": 0, "walked": 0,
                          "notYetAtReelDoor": 0, "byFrameRefused": 0, "byFrameUnasked": 0,
                          "why": "nothing was walked, so neither door was asked"},
                "why": ("UNKNOWN, not an empty shelf — %s"
                        % (why or "no reel reached this probe and nothing said why"))}
    seals, FA, seal_why = _seals()
    out, gaps, nameless = [], [], 0
    for r in rows:
        if not isinstance(r, dict):
            continue
        # ⚠⚠ REG-559 — THE PHANTOM AT ITS SOURCE. This emitted a row for anything the shelf
        # returned, including a row naming NO reel, and every stage then reported on ''. The
        # printer was taught to drop those downstream (REG-550/551) — which meant the two
        # DISAGREED on the same input: measured, reel_river walked 3 rows where the printer kept 1
        # and dropped 2. Fixing a class downstream while the source keeps producing it is how two
        # readings of one shelf come to differ. Counted, not silently skipped.
        name = str(r.get("reel") or r.get("name") or "").strip()
        if not name:
            nameless += 1
            continue
        if reel and reel not in name:
            continue
        stage = str(r.get("stage") or "")
        row = seals.get(_session_of(name)) or seals.get(name)
        if FA is None or seal_why:
            frame_answer, frame_why = None, (seal_why or "the seal store could not be read")
        elif row is None:
            frame_answer, frame_why = None, "no seal exists for this reel, so the frame question is UNASKED — not answered no"
        else:
            covers, cwhy = FA.seal_covers_extraction(row)
            frame_answer, frame_why = bool(covers), str(cwhy)
        decider, question = QUESTIONS.get(stage, ("?", "a stage this probe has not been taught"))
        out.append({
            "reel": name, "stage": stage, "decider": decider, "question": question,
            "reelAnswer": (stage == "releasable"),
            "frameDecider": FRAME_QUESTION[0], "frameQuestion": FRAME_QUESTION[1],
            "frameAnswer": frame_answer, "frameWhy": frame_why,
            "yield": r.get("yield"),
        })
    # ⚠ A GAP IS TWO DECIDERS ANSWERING THE SAME QUESTION DIFFERENTLY. The reel question and the
    # frame question are NOT the same question, so their disagreement is never counted here. If it
    # were, this probe would report 12 gaps on a healthy tree and teach him to skip the row — the
    # exact defect that made the v2312 collapse wrong.
    for o in out:
        if o["stage"] not in QUESTIONS:
            gaps.append({"reel": o["reel"], "gap": "stage %r has no declared decider, so nothing "
                                                   "here knows what answered it" % o["stage"]})
    # ⚠⚠ A15's LAST CLAUSE: "every one comes out clean at the far end... 'clean' is a state the
    # pipeline must be able to ASSERT per reel, not a hope." IT DOES NOT SAY WHICH DOOR DECIDES,
    # and the two candidates disagree — measured on the 40 reels of his shelf:
    #
    #     finished by the REEL door (stage == releasable)          12
    #     satisfying the FRAME contract (seal covers extraction)    0
    #     BOTH                                                      0
    #
    # So there is no single assertable definition of clean today. ⚠ AND I MUST NOT PICK ONE:
    # conjoining the two doors is exactly the collapse v2312 attempted and WITHDREW, because they
    # answer different questions at different granularities (v2314). Reporting both readings is
    # the honest shape; choosing between them is a decision about what "finished" means, and it
    # gates the prune. [[unknown-stays-unknown]]
    # ⚠⚠ AND THE FIRST CUT OF THIS BLOCK THREW AWAY THE TRI-STATE THE ROWS WERE BUILT TO KEEP.
    # It published `byFrameContract: 0` as a flat zero. Measured on his shelf the same run:
    # frame UNASKED 25, frame no 15, frame yes 0 — so that zero is fifteen REFUSALS and
    # twenty-five questions NOBODY PUT, and only one of those is evidence about the door. Every
    # row already says so (`frameWhy`: "no seal exists for this reel, so the frame question is
    # UNASKED — not answered no"); the summary collapsed the distinction the rows preserve, which
    # is the [[unknown-stays-unknown]] §1 defect one layer up from where it is usually caught.
    #
    # ⚠ THE SAME SHAPE ON THE OTHER DOOR, swept by class: stages are swept 28 / releasable 12, and
    # `swept` is mid-river, not a refusal. So byReelDoor is *12 ARRIVED*, never *28 refused*.
    # Both numerators now travel with what the rest of the shelf actually is.
    _reel_door = sum(1 for o in out if o["reelAnswer"])
    _frame_door = sum(1 for o in out if o["frameAnswer"] is True)
    _both = sum(1 for o in out if o["reelAnswer"] and o["frameAnswer"] is True)
    _frame_unasked = sum(1 for o in out if o["frameAnswer"] is None)
    _frame_refused = sum(1 for o in out if o["frameAnswer"] is False)
    _not_yet = len(out) - _reel_door
    return {"ok": True, "state": "FLOWING", "rows": out, "gaps": gaps, "namelessRows": nameless,
            "clean": {"byReelDoor": _reel_door, "byFrameContract": _frame_door, "byBoth": _both,
                      "walked": len(out),
                      "notYetAtReelDoor": _not_yet,
                      "byFrameRefused": _frame_refused, "byFrameUnasked": _frame_unasked,
                      "why": ("A15 requires a far-end state the pipeline can ASSERT, and does not "
                              "say which door decides. These two answer DIFFERENT questions "
                              "(v2314), so neither is 'the' answer and conjoining them is the "
                              "collapse v2312 withdrew. Reported, not chosen. ⚠ AND THE TWO ARE "
                              "NOT COMPARABLE ACROSS THE SHELF: byFrameContract is a count over "
                              "the %d reel(s) the frame question was actually PUT to — %d were "
                              "never asked, because no seal exists for them, and a question "
                              "nobody put is not a refusal. byReelDoor likewise counts reels that "
                              "ARRIVED; the other %d are mid-river, not turned away."
                              % (_frame_refused + _frame_door, _frame_unasked, _not_yet))},
            "why": ("%d reel(s) walked. %d gap(s) — a gap is two deciders answering the SAME "
                    "question differently, which is why the reel/frame split is not one."
                    % (len(out), len(gaps)))}


def main(argv):
    reel = next((a for a in argv if not a.startswith("-")), None)
    r = river(reel)
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    print("\nTHE FISH DOWN THE STREAM — every stage, and who decided it\n")
    if not r["ok"]:
        print("  UNKNOWN — %s" % r["why"])
        return 0
    rows = r["rows"]
    if reel:
        for o in rows:
            print("  %s" % o["reel"])
            print("     stage        %s" % o["stage"])
            print("     decided by   %s — %s" % (o["decider"], o["question"]))
            print("     frame door   %s" % o["frameDecider"])
            print("                  %s" % o["frameQuestion"])
            print("     frame says   %s — %s"
                  % ({True: "yes", False: "no", None: "UNASKED"}[o["frameAnswer"]], o["frameWhy"][:90]))
    else:
        from collections import Counter
        st = Counter(o["stage"] for o in rows)
        fr = Counter({True: "frame: yes", False: "frame: no", None: "frame: UNASKED"}[o["frameAnswer"]]
                     for o in rows)
        for k, n in st.most_common():
            print("  %-14s %d" % (k, n))
        print()
        for k, n in fr.most_common():
            print("  %-14s %d" % (k, n))
        print()
        print("  ⚠ THE REEL DOOR AND THE FRAME DOOR ANSWER DIFFERENT QUESTIONS, and a reader who")
        print("     does not know that reads 'releasable' beside 'frame: no' as a contradiction.")
        print("     It is not one — v2314 withdrew the attempt to collapse them, because doing so")
        print("     would have stopped the prune firing on every reel he owns.")
    c = r.get("clean") or {}
    if c:
        print()
        _asked = (c.get("byFrameRefused") or 0) + (c.get("byFrameContract") or 0)
        print("  CLEAN AT THE FAR END (A15) — and the two doors disagree:")
        print("     by the REEL door        %s of %s   (%s still mid-river, NOT turned away)"
              % (c.get("byReelDoor"), c.get("walked"), c.get("notYetAtReelDoor")))
        print("     by the FRAME contract   %s of %s asked   (%s refused, %s NEVER ASKED)"
              % (c.get("byFrameContract"), _asked, c.get("byFrameRefused"),
                 c.get("byFrameUnasked")))
        print("     by BOTH                 %s" % c.get("byBoth"))
        print("     ⚠ A15 does not say which decides, and these answer different questions.")
        print("       Reported, not chosen — picking one is the collapse v2312 withdrew.")
        print("     ⚠ AND THE DENOMINATORS DIFFER. A flat '0 by the frame contract' reads as a")
        print("       door refusing everything; %s of those reels were never put to it at all."
              % c.get("byFrameUnasked"))
    print("\n  %s" % r["why"])
    for g in r["gaps"][:8]:
        print("     ⚠ %s — %s" % (g["reel"], g["gap"]))
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    raise SystemExit(main(sys.argv[1:]))
