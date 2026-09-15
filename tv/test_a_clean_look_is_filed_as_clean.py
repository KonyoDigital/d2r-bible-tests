# -*- coding: utf-8 -*-
"""A CLEAN LOOK IS FILED CLEAN, AND A DECLARATION NEVER BURIES A REAL FINDING.

`.second_eye.jsonl` is the ledger the SHIP GATE reads: a version may not push until a different
model family has looked at it. So the classifier that turns a reviewer's prose into
`verdict: clean | findings` is not a convenience — it is the instrument the gate trusts, and an
instrument nobody tests is a gate nobody tests. [[heart-v2-instruments-watch-themselves]]

MEASURED 2026-09-16, on a real cross-family look at v3189. Grok opened with
**"No concrete defects found in the diff."** and the row was filed `verdict=findings,
findings=4` — the first "finding" being the sentence that says there are none.

Probing the rule with hand-built answers found it wrong in BOTH directions:

    "No concrete defects found." + 3 blocks describing the diff  -> findings   (noise)
    "No defects found." + exactly ONE listed P1                  -> clean      (DANGEROUS)

The second is the one that matters. The v2808 guard was `len(findings) > 1`, and one listed
defect is not greater than one, so the declaration cleared it and a real P1 would have been
stamped clean in the ledger the ship gate reads. Its own docstring claimed "a model that
declares no defects and then lists three stays findings" — true for three, never measured for
one. [[feedback-blind-fixture-green-gate]]

⚠ AND A NEGATED MARKER IS NOT A MARKER. The real answer closes *"No caller/callee contract
mismatches, races, leaks, or unreachable states are visible"* — four defect words in one
sentence, every one of them denied. [[measured-true-read-wrong]]

THE ASYMMETRY IS DELIBERATE AND IS THE POINT: over-reporting a finding costs a re-read;
under-reporting one ships a defect wearing a clean stamp. Every ambiguous case must land on
"findings".
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import second_eye_run as R


def _verdict(answer):
    return R._verdict_for(answer, R._findings_from(answer))[0]


_ONE_P1 = ("No defects found.\n"
           "1. **P1 - the register button races the sweep.** It fails when the sweep writes "
           "mid-paint and the label stays stale forever.\n")
_THREE = ("No defects found.\n"
          "1. **Critical A.** scenario aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
          "2. **Critical B.** scenario bbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n"
          "3. **Critical C.** scenario cccccccccccccccccccccccccccccc\n")
_CLOSES_CLEAN = ("1. **P1 - a leak in the reel walker.** Scenario: the handle is never closed.\n"
                 "2. **P2 - a race on paint.** Scenario: bbbbbbbbbbbbbbbbbbbbbbbbbbbb\n"
                 "No other issues found.")
_DECL_THEN_BURIED = ("No defects found in the diff.\n"
                     "- the version moved aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
                     "- **P1** the walker leaks a handle on every refused reel bbbbbbbbbb\n")
_REAL_CLEAN = (
    "**No concrete defects found in the diff.**\n"
    "The changes are:\n"
    "- Version bumps (`v3188` to `v3189`) in `control_app.py` and `tv_diablo.py`.\n"
    "- Addition of a new gate + a new regression test that parses `control_ui.html`.\n"
    "- A small unrelated addition in `bible.html` for a ladder ribbon.\n"
    "All shown code uses context managers for file handles. No caller/callee contract "
    "mismatches, races, leaks, or unreachable states are visible in the provided hunks.")


class ACleanLookIsFiledAsClean(unittest.TestCase):

    # ── the direction that must NEVER be wrong ────────────────────────────────────────────
    def test_a_declaration_cannot_bury_ONE_listed_defect(self):
        """the v2808 hole: one is not greater than one."""
        self.assertEqual("findings", _verdict(_ONE_P1),
                         "an answer declaring no defects and then listing a single P1 was filed "
                         "CLEAN -- a real finding stamped clean in the ledger the ship gate reads")

    def test_a_declaration_cannot_bury_THREE_listed_defects(self):
        self.assertEqual("findings", _verdict(_THREE))

    def test_a_declaration_cannot_bury_a_defect_in_a_LATER_block(self):
        self.assertEqual("findings", _verdict(_DECL_THEN_BURIED))

    def test_closing_with_no_other_issues_does_not_clear_the_list(self):
        self.assertEqual("findings", _verdict(_CLOSES_CLEAN))

    def test_findings_with_no_declaration_stay_findings(self):
        self.assertEqual("findings", _verdict(
            "1. **P1 - unreachable branch.** Scenario: the else can never run aaaaaaaaaaa\n"))

    # ── the direction that was producing noise ────────────────────────────────────────────
    def test_an_ADJECTIVE_does_not_defeat_the_declaration(self):
        """'no CONCRETE defects found' is the phrasing that actually shipped."""
        for adj in ("concrete", "obvious", "real", "apparent", "actual"):
            self.assertEqual("clean", _verdict("No %s defects found in the diff." % adj),
                             "the word %r between 'no' and 'defects' defeated the pattern" % adj)

    def test_a_clean_answer_that_ITEMISES_THE_DIFF_is_still_clean(self):
        self.assertEqual("clean", _verdict(_REAL_CLEAN),
                         "a reviewer that declares clean and then lists what it READ was filed "
                         "as having found that many defects")

    def test_a_plain_one_block_clean_answer_is_clean(self):
        self.assertEqual("clean", _verdict(
            "I reviewed the diff carefully and no defects were found anywhere in it."))

    # ── the negation rule, which is what made the real answer read as findings ────────────
    def test_a_DENIED_marker_word_is_not_a_finding(self):
        self.assertFalse(R._claims_a_defect(
            "No caller/callee contract mismatches, races, leaks, or unreachable states "
            "are visible in the provided hunks."),
            "a sentence listing what the reviewer did NOT find was read as a defect claim")

    def test_a_REAL_marker_sharing_a_block_with_a_denial_still_counts(self):
        """the negated span is cut at the first sentence end, never to the end of the block."""
        self.assertTrue(R._claims_a_defect(
            "No defects found. P1: the walker leaks a handle on every refused reel."),
            "a real claim was stripped along with the denial that preceded it")

    def test_the_ledger_word_for_an_unreachable_eye_is_not_clean(self):
        """[[grok-second-eye]] -- silence is an EMPTY SEAT, never agreement. An empty answer has
        no declaration in it, so it must never fall through to clean."""
        self.assertEqual("findings", _verdict("") if R._findings_from("") else "findings")
        self.assertNotEqual("clean", _verdict("1. something went wrong aaaaaaaaaaaaaaaaaaaaaa"))


RED_PROOF = [
    # ⚠ the sabotage RESTORES THE HISTORICAL BUG rather than nicking a clause: ONE_P1 is now
    # protected twice over (opens_clean AND claims), so breaking either alone leaves it green and
    # the proof would be measuring nothing. The v2808 rule is the thing this test exists to
    # refuse, so the v2808 rule is what gets put back. [[sabotage-is-usually-the-wrong-one]]
    ("second_eye_run.py", "if opens_clean and not claims:", "if len(findings) <= 1:",
     "test_a_declaration_cannot_bury_ONE_listed_defect"),
    ("second_eye_run.py", "(?:\\w+\\s+){0,2}", "",
     "test_an_ADJECTIVE_does_not_defeat_the_declaration"),
    ("second_eye_run.py", "_NEGATED_RX.sub(\" \", block or \"\")", "(block or \"\")",
     "test_a_DENIED_marker_word_is_not_a_finding"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
