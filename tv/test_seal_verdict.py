# -*- coding: utf-8 -*-
"""v2702 — A SEAL CAN SAY THREE THINGS, AND THE CONTRACT COULD ONLY HEAR TWO.

`seal_covers_extraction` answers yes or no. That is the right answer to the question it asks —
"did this seal record name, location and provenance?" — and the wrong shape for the fact it was
being used to report, because a `no` covers two opposite situations:

    a seal that examined a session and recorded THERE WAS NOTHING TO TAKE
    a seal that never says what it took at all

Those are measured-zero and nobody-looked, and collapsing them is the defect this repo has a name
for. It happened inside the function whose entire job is policing evidence.

=== WHAT IT COST, MEASURED ON HIS 30 SEALS ===
`seals_certify_nothing` was filed as "ALL 30 seals certify nothing: 0 satisfy the extraction
contract", read as thirty records asserting work with no evidence behind it. The real split:

    22 seals  `extracted: []`, extractedWhy "examined and there was nothing to take",
              and `rows` == 0 for EVERY ONE. Seals over EMPTY sessions. No row existed to
              take a name from, so there is no failure here at all.
     8 seals  no `extracted` key (they predate the contract). SIX of those cover 7 rows each —
              42 rows of real content sealed without recording what was taken.

So the actual defect is SIX seals, not thirty, and the report said thirty because the vocabulary
had no word for "empty".

⚠ `rows == 0` IS THE LOAD-BEARING HALF OF THE RULE. A seal claiming "nothing to take" while
covering seven rows is not empty — it is unevidenced wearing an excuse, the same shape as a probe
returning 0 for a container it never opened. The DECLARATION alone can never be enough, which is
why this file tests the liar case explicitly and not just the honest one.

⚠ AND IT LOOSENS NOTHING. `seal_covers_extraction` is untouched, because two gates depend on its
strictness: test_control asserts the frame authority is "the stricter of the two", and
reel_retention is asserted never to consult it (every existing seal predates the contract, so the
prune would never fire again). This adds a word; it takes none away.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import frame_authority as FA


class SealVerdictSaysWhichKindOfNo(unittest.TestCase):

    def test_the_three_words_exist_and_are_distinct(self):
        vals = {FA.COVERED, FA.EMPTY, FA.UNEVIDENCED}
        self.assertEqual(len(vals), 3, "the three verdicts collapsed into %d value(s)" % len(vals))

    def test_an_examined_empty_session_is_EMPTY_not_a_failure(self):
        v, why = FA.seal_verdict({"rows": 0, "extracted": [], "examinedEmpty": True})
        self.assertEqual(v, FA.EMPTY,
                         "a seal over 0 rows that RECORDS there was nothing to take is a "
                         "measurement, and reporting it as a failure is what made 22 honest "
                         "seals read as defects")
        self.assertIn("MEASUREMENT", why.upper())

    def test_the_declaration_alone_is_never_enough(self):
        """The liar case. Without this, `examinedEmpty: true` becomes a way to opt out."""
        v, why = FA.seal_verdict({"rows": 7, "extracted": [], "examinedEmpty": True})
        self.assertEqual(v, FA.UNEVIDENCED,
                         "a seal covering 7 rows claimed there was nothing to take and was "
                         "believed. `rows == 0` is the check that makes the declaration mean "
                         "something; without it the word EMPTY is self-certifying")

    def test_zero_rows_without_a_declaration_is_still_UNEVIDENCED(self):
        v, _ = FA.seal_verdict({"rows": 0, "extracted": []})
        self.assertEqual(v, FA.UNEVIDENCED,
                         "a seal that covers nothing and never SAYS it examined an empty session "
                         "is indistinguishable from one that did not look")

    def test_a_seal_predating_the_contract_is_UNEVIDENCED(self):
        """Pins the existing test_control expectation from the other side."""
        v, _ = FA.seal_verdict({"ts": 1, "rows": 0, "promptVer": "vp2017"})
        self.assertEqual(v, FA.UNEVIDENCED)

    def test_a_full_seal_is_COVERED(self):
        v, _ = FA.seal_verdict({"rows": 3, "extracted": list(FA.EXTRACTION_CONTRACT)})
        self.assertEqual(v, FA.COVERED)

    def test_the_strict_bool_is_unchanged(self):
        """Two gates depend on seal_covers_extraction staying strict. It may not soften."""
        for row in ({"rows": 0, "extracted": [], "examinedEmpty": True},
                    {"rows": 7, "extracted": [], "examinedEmpty": True},
                    {"ts": 1, "rows": 0, "promptVer": "vp2017"}):
            ok, _ = FA.seal_covers_extraction(row)
            self.assertFalse(ok, "seal_covers_extraction went soft on %r — reel_retention is "
                                 "asserted never to consult it precisely because it is strict, "
                                 "and test_control pins it as the stricter of the two" % row)

    def test_a_verdict_is_never_invented_for_a_non_record(self):
        for junk in (None, 3, "seal", [], object()):
            v, _ = FA.seal_verdict(junk)
            self.assertEqual(v, FA.UNEVIDENCED,
                             "%r produced %s — a thing that is not a record establishes "
                             "nothing, and must never read as EMPTY" % (junk, v))


if __name__ == "__main__":
    unittest.main(verbosity=2)
