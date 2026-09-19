# -*- coding: utf-8 -*-
"""v3315 — A LOOK THAT FOUND NOTHING IS NEVER FILED AS ONE THAT FOUND SOMETHING.

THE FIFTH PHRASING, AND IT IS A DIFFERENT PART OF SPEECH. `_NO_DEFECT_RX` is a NOUN-PHRASE
pattern: it needs `no <...> defects|issues|bugs|problems`. Four versions widened its vocabulary
(v3216 `evident`, v3216 `present`, v3267 `meeting`, v3268 the bare full stop) and the lesson drawn
was *"the declaration is the NOUN PHRASE"*. This shape has no such noun at all.

MEASURED 2026-09-18 on the real v3301 look. Grok answered:

    **Findings**

    none found

and the row was filed `verdict="findings", findings=2` — the ledger asserting the eye found two
things when it had said the opposite, in the ledger whose entire job is to record what another
family concluded. Of the three conditions in `_verdict_for`, exactly ONE failed: the declaration
never matched. `_claims_a_defect` was False for both blocks.

⚠ AND THE REPO'S OWN PROMPT ASKS FOR THIS WORDING — *"If you genuinely find nothing in a category,
say 'none found'"* — so the instrument was refusing the phrasing it requested.

⚠ SAFE BY CONSTRUCTION, and the asymmetry is the point: `_declares_none` can only ever GRANT
clean, and only when `_claims_a_defect` is false for EVERY block. A review that says "off-by-one:
none found" and then lists a real P1 still lands in `findings`. Over-reporting a finding costs a
re-read; under-reporting one ships a defect with a clean stamp on it. That dangerous direction is
pinned below as a BASELINE, not left to inference. [[regression-guard]]

AND TWO THINGS THE LEDGER NOW SAYS ABOUT ITS OWN HISTORY:
  · every new row records WHICH parser generation judged it (`judgedBy`); 824 rows predate that
  · `verdict_provenance()` re-judges what it can and keeps FOUR reasons for "cannot" apart —
    prefix-only, no answer, a hand-written verdict no parser produced, and (by omission) an
    unstamped row. Collapsing any of them into "agrees" is the defect.
    Measured: 540 agree, 133 disagree, 91 + 17 + 47 UNKNOWN.
[[unknown-stays-unknown]] [[zero-needs-a-denominator]] [[stale-reading]]
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Its docstrings and failure messages carry non-ASCII, and a unittest failure PRINTS them. On a
# cp1255 console that crash happens while REPORTING, so a clean tree exits non-zero for a reason
# that has nothing to do with the law. Caught by test_control's encoding-safety gate.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_run as R          # noqa: E402
import second_eye_ledger as L       # noqa: E402

#: The real v3301 answer, verbatim in the shape that was misfiled.
PRONOUN_CLEAN = (
    "**Findings**\n\nnone found\n\n"
    "The shown diff introduces a new interlock with consistent call signatures and defensive "
    "exception handling around the new state.\n\n"
    "**Visibility note**\n\nI examined the entire supplied diff (both files, all hunks)."
)


class TestACleanLookIsNeverFiledAsFindings(unittest.TestCase):

    def test_the_pronoun_form_of_a_clean_declaration_is_recognised(self):
        """BEHAVIOURAL, on the exact text that was misfiled."""
        self.assertTrue(
            R._declares_none("none found"),
            "'none found' is not recognised as a declaration that nothing was found. That is the "
            "wording this repo's own COLD_FRAMING asks a reviewer to use.")

        verdict, kept = R._verdict_for(PRONOUN_CLEAN, R._findings_from(PRONOUN_CLEAN))
        self.assertEqual(
            verdict, "clean",
            "the real v3301 answer — '**Findings**' then 'none found' — was filed as %r. The eye "
            "said it found nothing and the ledger recorded that it found something." % (verdict,))
        self.assertEqual(
            kept, [],
            "%d finding(s) were kept from an answer that declares none." % len(kept))

    def test_a_declaration_still_cannot_clear_a_real_defect(self):
        """⚠ THE BASELINE, AND THE DANGEROUS DIRECTION. Without it, 'always clean' would pass."""
        danger = ("**Findings**\n\nnone found\n\n"
                  "P1: the caller crashes on empty input, which is a real defect.")
        verdict, kept = R._verdict_for(danger, R._findings_from(danger))
        self.assertEqual(
            verdict, "findings",
            "a declaration followed by a REAL P1 was cleared to %r. Widening the declaration "
            "vocabulary is only safe while `_claims_a_defect` still refuses — under-reporting a "
            "finding ships a defect with a clean stamp on it." % (verdict,))
        self.assertTrue(
            kept, "the real defect block was discarded along with the verdict.")

    def test_the_noun_phrase_form_still_works(self):
        """Adding a pattern must not cost the one it sits beside. [[two-fixes-broke-each-other]]"""
        for txt in ("**No defects found.**", "No concrete defects.",
                    "No concrete functional defect is evident in this diff"):
            self.assertTrue(
                R._declares_none(txt),
                "the noun-phrase declaration %r stopped being recognised — a previous "
                "correction was undone by this one." % txt)

    # ── v3376: the ledger vocabulary is `clean`, and the parser did not know the word ────────
    #
    # MEASURED LIVE on v3375 own look. The answer FIRST LINE was "VERDICT: clean"; the row came
    # back verdict=findings with FOUR findings, every one of them the answer explaining why it is
    # clean, finding [0] containing the words VERDICT: clean inside itself. `_declares_none`
    # recognises the NOUN PHRASE and the PRONOUN and has never known the adjective the ledger
    # itself uses. agreement() reads verdicts, so the ledger asserted four defects that do not
    # exist. Sixth phrasing to defeat this check. [[the-unjoined-end]]

    #: the real v3375 answer, in the shape that was misfiled.
    STATED_CLEAN = (
        "VERDICT: clean\n\n"
        "The visible diff only performs three narrow, mechanical things, all of which are "
        "internally consistent on the code shown:\n\n"
        "- version strings are bumped in the two places that contain them;\n"
        "- record() grows a new optional keyword parameter stripped=None;\n"
        "- the two test files are updated to assert the new call-site spelling.\n"
    )

    def test_a_STATED_verdict_of_clean_is_read_as_clean(self):
        """BEHAVIOURAL, on the exact text that was misfiled at v3375."""
        self.assertEqual(
            R._stated_verdict(self.STATED_CLEAN), "clean",
            "an answer whose first line is literally 'VERDICT: clean' does not state a verdict "
            "this parser can read.")
        verdict, kept = R._verdict_for(self.STATED_CLEAN, R._findings_from(self.STATED_CLEAN))
        self.assertEqual(
            verdict, "clean",
            "the real v3375 answer was filed as %r. It says VERDICT: clean on its first line."
            % (verdict,))
        self.assertEqual(kept, [],
                         "%d finding(s) kept from an answer that states it is clean." % len(kept))

    def test_a_STATED_verdict_of_findings_is_honoured_too(self):
        """Reading the declared field must work in BOTH directions, or it is a clean-stamp."""
        txt = "VERDICT: findings\n\n1. control_app.py:12 crashes on empty input"
        self.assertEqual(R._stated_verdict(txt), "findings")
        self.assertEqual(R._verdict_for(txt, R._findings_from(txt))[0], "findings")

    def test_a_MENU_of_verdicts_is_not_a_declaration(self):
        """⚠ A line naming TWO verdict words offers a CHOICE; it does not declare one.

        ⚠⚠ THE FIXTURE HERE IS LOAD-BEARING AND MY FIRST ONE WAS NOT. I wrote this case with
        "1. VERDICT: clean / findings" — the numbered form the review prompt actually uses — and
        its red-proof came back BLIND at a correct match count of 1. Measured: the numbered form
        never matches the line anchor at all (a leading "1. " is not in the character class), so
        it returned None for a reason that has nothing to do with the menu guard. The sabotage was
        right and the CASE could not see it. The bare form below does reach the guard.
        [[source-reading-guard]] section 4c, cause 2: the test was too weak, not the law.
        """
        self.assertTrue(
            R._VERDICT_LINE_RX.search("VERDICT: clean / findings"),
            "the bare menu form no longer reaches the line anchor, so this case is measuring "
            "the anchor and not the guard it was written for.")
        self.assertIsNone(
            R._stated_verdict("VERDICT: clean / findings"),
            "a line offering a CHOICE of verdicts was read as declaring one, so an eye echoing "
            "its instructions would clear any review it appears in.")

    def test_a_NUMBERED_instruction_line_is_not_a_declaration(self):
        """The separate protection: the review prompt own line is "1. VERDICT: clean / findings",
        and a declaration has to START the line. This is the anchor doing the work, not the menu
        guard — they are two different doors and each needs its own case."""
        echo = "1. VERDICT: clean / findings\n2. For each finding: FILE:LINE"
        self.assertIsNone(
            R._stated_verdict(echo),
            "the review prompt own numbered instruction line was read as declaring a verdict.")

    def test_a_STATED_clean_still_cannot_clear_a_real_defect(self):
        """⚠ THE DANGEROUS DIRECTION — without this, reading the field is an off switch."""
        danger = "VERDICT: clean\n\nP1: the caller crashes on empty input, which is a race."
        verdict, kept = R._verdict_for(danger, R._findings_from(danger))
        self.assertEqual(
            verdict, "findings",
            "a STATED clean verdict cleared a block claiming a P1 crash and a race, filing %r. "
            "Under-reporting a finding ships a defect with a clean stamp on it." % (verdict,))
        self.assertTrue(kept, "the real defect block was discarded along with the verdict.")

    def test_the_prose_paths_still_work_beside_the_stated_one(self):
        """[[two-fixes-broke-each-other]] — the new door must not close the two beside it."""
        v, k = R._verdict_for(PRONOUN_CLEAN, R._findings_from(PRONOUN_CLEAN))
        self.assertEqual(v, "clean", "the pronoun path stopped working when the stated one landed")
        self.assertTrue(R._declares_none("**No defects found.**"),
                        "the noun-phrase path stopped working when the stated one landed")

    def test_a_row_says_which_parser_generation_judged_it(self):
        """A verdict with no provenance is not a verdict. [[stale-reading]]"""
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            row = L.record(version="v9999", model="grok-4-1-fast-reasoning", verdict="clean",
                           findings=[], answer_head="none found", path=path)
            self.assertEqual(
                row.get("judgedBy"), L.PARSER_GEN,
                "a freshly written row carries judgedBy=%r rather than %r. Without it a reader "
                "cannot tell a verdict written by today's parser from one written by a parser "
                "since corrected — and 824 rows already have that problem."
                % (row.get("judgedBy"), L.PARSER_GEN))
        finally:
            os.unlink(path)

    def test_a_row_that_cannot_be_rejudged_is_UNKNOWN_and_never_agreement(self):
        """FOUR reasons a row cannot be re-judged, and none of them is agreement."""
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            # a HAND-WRITTEN verdict no parser ever produced
            L.record(version="v9001", model="m", verdict="CORRECTION-to-my-own-earlier-row",
                     findings=[], answer_head="some prose", path=path)
            # nothing of the answer stored at all
            L.record(version="v9002", model="m", verdict="clean",
                     findings=[], answer_head="", path=path)
            # a genuine, re-judgeable agreement
            L.record(version="v9003", model="m", verdict="clean",
                     findings=[], answer_head="No defects found.", path=path)

            p = L.verdict_provenance(path)
            self.assertEqual(
                p["handWritten"], 1,
                "a hand-written verdict was re-judged as though a parser had written it. "
                "Comparing an annotation against a parser verdict is a comparison between two "
                "populations — the same defect v3313 removed from the seed row.")
            self.assertEqual(
                p["noAnswer"], 1,
                "a row storing no answer was not counted as UNKNOWN (noAnswer=%d)." % p["noAnswer"])
            self.assertEqual(
                p["agree"], 1,
                "the one genuinely re-judgeable agreeing row was not counted (agree=%d). If this "
                "is 0 the measurement reaches nothing and its other numbers mean nothing."
                % p["agree"])
            self.assertEqual(
                p["disagree"], 0,
                "a disagreement was manufactured from rows that cannot be re-judged.")
            for word in ("HAND-WRITTEN", "UNKNOWN"):
                self.assertIn(
                    word, p["say"],
                    "the say line does not carry %r, so a reader gets the counts without the "
                    "reason any of them could not be judged." % word)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "dropping the pronoun pattern re-files the real v3301 clean look as 2 findings",
        "file": "tv/second_eye_run.py",
        "find": "    return bool(_NO_DEFECT_RX.search(t) or _NO_FINDING_RX.search(t))",
        "replace": "    return bool(_NO_DEFECT_RX.search(t))",
        "matches": 1,
    },
    {
        "why": "re-judging hand-written annotations manufactures disagreements nobody claimed",
        "file": "tv/second_eye_ledger.py",
        "find": '        if str(r.get("verdict") or "") not in PARSER_VERDICTS:\n            out["handWritten"] += 1\n            continue',
        "replace": '        if False:\n            out["handWritten"] += 1\n            continue',
        "matches": 1,
    },
    {
        "why": "a row with no parser stamp cannot be told from one today's parser wrote",
        "file": "tv/second_eye_ledger.py",
        "find": '        "judgedBy": PARSER_GEN,',
        "replace": '        "judgedBy": None,',
        "matches": 1,
    },
    {
        "why": "not reading a STATED verdict puts v3375 back: an answer whose first line is "
               "VERDICT: clean filed as findings, with the explanation harvested as the findings",
        "file": "tv/second_eye_run.py",
        "find": "    stated = _stated_verdict(answer)",
        "replace": "    stated = None",
        "matches": 1,
    },
    {
        "why": "dropping the menu guard lets the review prompt own echoed instruction line "
               "(VERDICT: clean / findings) clear every review it appears in",
        "file": "tv/second_eye_run.py",
        "find": "        if len(set(words)) == 1:",
        "replace": "        if words:",
        "matches": 1,
    },
    {
        "why": "letting a stated clean verdict skip the defect-claim check turns reading the "
               "declared field into an off switch for the whole law",
        "file": "tv/second_eye_run.py",
        "find": "        _claimed = [f for f in findings if _claims_a_defect(f)]",
        "replace": "        _claimed = []",
        "matches": 1,
    },
]
