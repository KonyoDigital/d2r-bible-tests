#!/usr/bin/env python3
"""THE HUMAN-EYES LEDGER, READ BY SOMETHING. gh #201 (A13).

Konyo, 2026-09-01: *"i want this part of the workflow.. what about the visual harness with grok bot
where is that?"*

It was already built — `tv/ask_view.py`, `tv/human_eyes_ledger.py`, the `human-eyes-harness` skill,
briefs HE-1…HE-5 as GitHub issues. And it reached NOTHING. Its ledger held a real catch:

    2026-09-01 16:21:45   verdict LOOKED
    "the whole webview is white. taskforce not visible. forge not visible. The beat still
     reports taskforce shown H=502 top=1050 and forge shown H=181 top=1599 — both BELOW a
     660px window. uiBeat.hidden=true while the window chrome is on screen."

That observation was correct, it was the first sighting of what became gh #200, and it sat in an
untracked `.jsonl` that nothing read. **An observation that reaches nothing is a diagnosis nobody
made.** This file is the reaching.

⚠ WHAT THIS CAN AND CANNOT ASSERT, STATED UP FRONT. The full A13 ask is that a LOOKED observation
CONTRADICTING the live console raises a blocker. That comparison needs a running console, and a
gate does not have one — so this asserts the half that is provable from the record alone:

  · the loop has completed end to end at least once (`proven()`), because a harness that is
    designed, documented and never exercised is indistinguishable from a working one
  · no brief has been OWED past its patience, because a question nobody answered must not fade
  · the ledger is READABLE — and if it is not, that is UNKNOWN (exit 2), never a pass

The contradiction check belongs beside the render gate, where a live console already exists. Filed
rather than faked; a gate that claims a comparison it never made is the defect this whole harness
exists to catch. [[the-unjoined-end]] [[unknown-stays-unknown]]

    python3 tv/human_eyes_gate.py             # the gate
    python3 tv/human_eyes_gate.py --prove     # make it go RED for its own reason
"""
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: how long a brief may sit unanswered before it is a finding rather than a wait. Generous on
#: purpose — his eye is a person and a game session, not a CI runner.
OWED_PATIENCE_H = 24.0


def check(path=None, now_ms=None):
    """-> (code, lines). 0 green · 1 a real finding · 2 UNKNOWN (which is not a pass)."""
    import human_eyes_ledger as H
    out, red = [], []
    st = H.state(path)
    if st is None:
        return 2, ["⚪ UNKNOWN — the human-eyes ledger could not be read. That is not agreement, "
                   "and it is not an empty ledger: the two are opposite facts."]
    if not st:
        # ⚠ v2428 (cont) — "THERE IS NO LEDGER HERE" AND "THE LEDGER IS EMPTY" ARE DIFFERENT FACTS,
        # AND THIS GATE COLLAPSED THEM. `_rows()` returns [] for a missing file, deliberately and
        # correctly — a ledger that does not exist genuinely has no rows, and its own docstring
        # argues that at length. But THIS layer then read [] as "no brief has ever been sent",
        # which is a claim about the HARNESS. The ledger is gitignored (.gitignore:202), so on CI
        # it can never exist, and the real check therefore went RED on every CI run for a reason
        # that is about the VENUE and not about the harness at all. Measured:
        #     TV_HUMAN_EYES_LEDGER=/nonexistent python3 tv/human_eyes_gate.py  ->  exit 1
        # A gate that is red on a venue for existing there is a gate switched off within a week —
        # and this is the third state discipline this very file preaches two paragraphs above.
        # [[unknown-stays-unknown]] [[feedback-blind-fixture-green-gate]]
        p = path or getattr(H, "LEDGER_PATH", None)
        if p and not os.path.exists(p):
            return 2, ["⚪ UNKNOWN — there is no human-eyes ledger on this venue (%s). The harness "
                       "records a loop that runs on HIS machine, and its ledger is a runtime "
                       "record, not a tracked file. 'It has not run here' is not 'it has never "
                       "run', and only the second would be a finding." % p]
        return 1, ["🔴 the ledger EXISTS and is EMPTY — no brief has ever been sent, so the harness "
                   "is designed and not exercised. That is the shape of every defect it exists to "
                   "catch: built at both ends, joined at neither."]
    ok, why = H.proven(path)
    if not ok:
        red.append(1)
        out.append("🔴 the loop has never completed end to end: %s" % why)
    else:
        out.append("🟢 the loop has completed end to end at least once.")

    now = now_ms if now_ms is not None else int(time.time() * 1000)
    owed = H.owed(path) or []
    stale = []
    for r in owed:
        # ⚠ state() RENAMES IT. The rows on disk carry `ts`; state() hands back `sentTs`, and a
        # first cut of this gate read `ts`/`at` and therefore reported "age UNKNOWN" for every
        # brief on a ledger that timestamps all of them. It blamed his record for a field my own
        # reader was asking for by the wrong name — the instrument, not the data.
        # [[feedback-suspect-the-instrument]]
        ts = r.get("sentTs") or r.get("ts") or r.get("at") or 0
        age_h = (now - int(ts)) / 3600000.0 if ts else None
        # ⚠ A BRIEF FROM THE FUTURE IS UNREADABLE, NOT FRESH. If the clock moved back, or a row
        # carries a timestamp ahead of now, the age goes NEGATIVE — and negative is never
        # `> OWED_PATIENCE_H`, so a brief stuck forever reads as comfortably within patience. That
        # is a green produced by an impossible number, which is the worst kind. An age I cannot
        # compute is UNKNOWN and gets flagged, exactly like a missing timestamp.
        # [[unknown-stays-unknown]] [[stale-reading]]
        if age_h is not None and age_h < 0:
            age_h = None
        if age_h is None:
            stale.append((r.get("brief"), None))
        elif age_h > OWED_PATIENCE_H:
            stale.append((r.get("brief"), age_h))
    if stale:
        red.append(1)
        out.append("🔴 %d brief(s) asked and never answered past %.0fh:" % (len(stale), OWED_PATIENCE_H))
        for b, age in stale:
            out.append("     %-28s %s" % (b, ("%.1fh" % age) if age is not None else
                                          "age UNKNOWN — the row carries no timestamp"))
        out.append("   A question nobody answered must not fade into silence. UNKNOWN closes a "
                   "brief honestly; nothing at all does not.")
    else:
        out.append("🟢 no brief is owed past its patience (%d open, all within %.0fh)."
                   % (len(owed), OWED_PATIENCE_H))

    looked = [r for r in st if r.get("verdict") == "LOOKED"]
    out.append("   %d brief(s) recorded · %d answered with a LOOK · %d still owed"
               % (len(st), len(looked), len(owed)))
    # ⚠ THE VERDICT IS A FLAG, NEVER A STRING MATCH ON ITS OWN OUTPUT. This read
    # `any(l.startswith("🔴") for l in out)`, which makes the exit code a property of how the
    # messages are WORDED: reword a finding, or lose an emoji to an encoding round trip, and a real
    # RED silently returns 0. Found by a cold cross-family read of this function (v2404's owed
    # second-eye look) — and it is the SECOND instance of this exact shape today: the visual lock's
    # footer selector read `"weight" in f` and matched the word "weight" inside the SIZE failure's
    # own explanation. A verdict derived from prose is a verdict any editor can flip.
    # [[source-reading-guard]] [[feedback-comments-vs-code]]
    return (1 if red else 0), out


def prove():
    """Founding rule 2 — it must be seen RED for its own reason, on fixtures, never on his record."""
    import shutil
    import tempfile
    import human_eyes_ledger as H
    bad = 0
    d = tempfile.mkdtemp(prefix="he_gate_")
    try:
        # 1. an EMPTY ledger is a finding, not a pass
        empty = os.path.join(d, "empty.jsonl")
        io.open(empty, "w").close()
        code, _ = check(empty)
        ok = code == 1
        bad += 0 if ok else 1
        print("   %s empty ledger          want 1  got %d" % ("🟢" if ok else "🔴", code))

        # 2. a brief sent and never answered, older than the patience, is a finding
        # ⚠ v2405 — THIS FIXTURE WAS VACUOUS AND PASSED FOR THE WRONG REASON FOR A WHOLE SHIP.
        # It held ONE unanswered brief and nothing else, so `proven()` failed it ("no round trip
        # has completed") and appended its own RED line — the gate returned 1 whether or not the
        # staleness check existed at all. Proof: deleting the age comparison entirely left this
        # case green. A sabotage that survives the removal of the code it targets is measuring
        # something else. So the fixture now carries a COMPLETED round trip FIRST, which makes
        # proven() green and leaves the stuck brief as the ONLY thing that can turn it red.
        # [[sabotage-is-usually-the-wrong-one]] [[feedback-blind-fixture-green-gate]]
        owed_p = os.path.join(d, "owed.jsonl")
        H.send("HE-DONE", "an answered brief, so proven() cannot be the thing that reds this",
               path=owed_p)
        H.observed("HE-DONE", "the pane showed 16", "LOOKED", path=owed_p)
        H.send("HE-TEST", "a claim nobody answered", path=owed_p)
        old = int(time.time() * 1000) + int(OWED_PATIENCE_H * 3600000) + 60000
        code, _ = check(owed_p, now_ms=old)
        ok = code == 1
        bad += 0 if ok else 1
        print("   %s brief owed too long    want 1  got %d" % ("🟢" if ok else "🔴", code))

        # 3. a completed round trip is GREEN — the gate must be able to pass, or it is furniture
        done_p = os.path.join(d, "done.jsonl")
        H.send("HE-TEST", "a claim that got answered", path=done_p)
        H.observed("HE-TEST", "the pane showed 16", "LOOKED", path=done_p)
        code, lines = check(done_p)
        ok = code == 0
        bad += 0 if ok else 1
        print("   %s answered round trip    want 0  got %d" % ("🟢" if ok else "🔴", code))
        if not ok:
            for l in lines:
                print("        %s" % l)

        # 5. ⚠ A BRIEF FROM THE FUTURE. v2405 — a cold cross-family read of check() pointed out
        #    that `now - sentTs` goes NEGATIVE under clock skew, and negative is never
        #    `> OWED_PATIENCE_H`, so a permanently stuck brief reads as comfortably fresh. Same
        #    fixture as case 2, same stuck brief, only the clock disagrees — and before the fix
        #    this returned 0. An impossible age must be UNKNOWN, never young.
        skew_p = os.path.join(d, "skew.jsonl")
        H.send("HE-DONE", "an answered brief, for the same anti-vacuity reason as case 2",
               path=skew_p)
        H.observed("HE-DONE", "the pane showed 16", "LOOKED", path=skew_p)
        H.send("HE-TEST", "a brief whose clock ran backwards", path=skew_p)
        past = int(time.time() * 1000) - 90 * 86400000     # 'now' is 90 days BEFORE it was sent
        code, lines = check(skew_p, now_ms=past)
        ok = code == 1
        bad += 0 if ok else 1
        print("   %s brief from the future   want 1  got %d" % ("🟢" if ok else "🔴", code))
        if not ok:
            for l in lines:
                print("        %s" % l)

        # 3b. v2428 — AN ABSENT LEDGER IS UNKNOWN, AND AN EXISTING EMPTY ONE IS A FINDING.
        # These were one branch and the difference is the whole CI story: the ledger is gitignored,
        # so "absent" is the normal state of every venue that is not his Mac.
        missing = os.path.join(d, "no-such-ledger.jsonl")
        code, _ = check(missing)
        ok = code == 2
        bad += 0 if ok else 1
        print("   %s absent ledger         want 2  got %d" % ("🟢" if ok else "🔴", code))

        # 4. an unreadable ledger is UNKNOWN, never a pass
        broken = os.path.join(d, "broken.jsonl")
        io.open(broken, "w", encoding="utf-8").write("{not json at all\n")
        code, _ = check(broken)
        ok = code in (1, 2)
        bad += 0 if ok else 1
        print("   %s unreadable ledger      want 1 or 2  got %d" % ("🟢" if ok else "🔴", code))
    finally:
        shutil.rmtree(d, True)
    print()
    if bad:
        print("🔴 %d case(s) wrong — this gate may not be trusted." % bad)
        return 1
    print("🟢 the gate goes red for a finding, green for an answered brief, and UNKNOWN for a "
          "ledger it cannot read.")
    return 0


def gate_mode():
    """BOTH halves: is the checker trustworthy, and what does HIS ledger actually say?

    ⚠ v2428 (cont) — REGISTERED AS `--prove` AND ONLY `--prove`, so for its whole life this gate
    ran its own sabotage on temp fixtures and never once opened the real ledger. The record it was
    built to make reachable stayed unread by the thing built to read it. That is the harness's own
    defect one level up: an observation that reaches nothing is a diagnosis nobody made, and a
    checker that never looks is the same silence wearing a green tick. [[the-unjoined-end]]

    The sabotage still runs first — a checker that cannot be trusted must not be believed about
    his record — and the real read follows, with an absent ledger reported as UNKNOWN rather than
    folded into either verdict.
    """
    print("PROVING THE HUMAN-EYES GATE — on fixtures, never on his record.\n")
    if prove() != 0:
        print("\n🔴 human-eyes: the SABOTAGE failed — the checker is broken, so nothing it reports "
              "about his ledger can be trusted. Fix the checker before reading its verdict.")
        return 1
    print("\n── AND NOW HIS ACTUAL LEDGER ──")
    code, lines = check()
    for l in lines:
        print(l)
    if code == 1:
        print("🔴 human-eyes: a REAL finding in the human-eyes ledger — see the lines above.")
        return 1
    if code == 2:
        print("⚪ human-eyes: checker PROVEN · his ledger could not be read on this venue, so "
              "NOTHING was asserted about the loop. UNKNOWN, not a pass.")
        return 0
    print("🟢 human-eyes: checker proven on fixtures AND his real ledger read clean.")
    return 0


def main(argv):
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    if "--prove" in argv:
        print("PROVING THE HUMAN-EYES GATE — on fixtures, never on his record.\n")
        return prove()
    if "--gate" in argv:
        return gate_mode()
    code, lines = check()
    for l in lines:
        print(l)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
