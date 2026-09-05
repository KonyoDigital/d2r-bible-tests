#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A 70-CHARACTER WINDOW MANUFACTURED A FINDING, AND THE MODULE PUBLISHED IT.

⚠⚠ WHAT HAPPENED. `printer_reach` tallied its refusals with `blocked[str(cwhy)[:70]]`. The refusal
sentence names EVERY missing contract fact in one line:

    "the sweep never extracted name (the item's name, which only ever appears in a hover
     tooltip), location (WHERE it was — the container and the cell box inside it (his slot
     identity)), provenance (…)"

Seventy characters lands part-way through the FIRST fact's explanation, so every distinct refusal
collapsed into one bucket whose text happened to end inside the word `name`. The module's own
docstring then stated, as a measurement:

    "22 carry an `extracted` record, and ALL 22 fail on the SAME single fact: `name`"

**That was false.** Re-measured untruncated, 2026-09-05: `name`, `location` AND `provenance` are
missing on **all 30** seals.

⚠ WHY THE CORRECTION MATTERS RATHER THAN BEING PEDANTRY. The two readings imply different work.
One missing fact is a reader change. `location` missing is a CAPTURE question — 0 of 1,065 deep
rows carry a cell or slot — and that is his ruling to make, not something to code around. A finding
that names the wrong blocker sends the next person to the wrong file.

⚠ AND IT IS THE SAME SHAPE AS `source_window_shortcut`: a fixed-size slice of something whose
length you did not check does not shorten the answer, it produces a different one.

⚠ NOTHING HERE TOUCHES HIS STORES. Every case drives the pure tally logic or reads the seal store
read-only through `frame_authority`.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import frame_authority as FA  # noqa: E402
import printer_reach as PR  # noqa: E402


class TheRefusalIsNotCutInHalf(unittest.TestCase):

    def test_the_tally_key_is_the_WHOLE_reason(self):
        """★ RED for the original defect, GRADED ON BEHAVIOUR NOT ON TEXT.

        ⚠ My first cut of this asserted `"[:70]" not in inspect.getsource(...)` and FAILED — on the
        comment that DESCRIBES the defect, and on an unrelated `str(e)[:70]` in an error message.
        That is the third guard I have written in two versions that grades prose instead of code,
        and the second to be defeated by its own explanation. A guard must drive the thing.
        [[source-reading-guard]]

        The behaviour: a blocked reason is keyed by its FULL sentence, so a bucket key longer than
        70 characters proves the cut is gone. The live refusals run to ~200 characters.
        """
        r = PR.report()
        blocked = r.get("blocked") or {}
        if not blocked:
            self.skipTest("nothing is blocked on this tree — no key to measure, not a pass")
        longest = max(len(k) for k in blocked)
        self.assertGreater(longest, 70,
                           "every blocked reason is <= 70 chars, which is what the truncation "
                           "produced; longest key is %d" % longest)

    def test_two_reasons_differing_late_stay_DISTINCT(self):
        a = "the sweep never extracted name (the item's name, which only ever appears in a tooltip)"
        b = "the sweep never extracted name (the item's name, which only ever appears in a HAT)"
        self.assertEqual(a[:70], b[:70], "the fixture no longer reproduces the collapse")
        blocked = {}
        for why in (a, b):
            blocked[why] = blocked.get(why, 0) + 1
        self.assertEqual(len(blocked), 2,
                         "two different refusals still collapse into one bucket")

    def test_the_docstring_STATES_the_corrected_measurement(self):
        """⚠ A corrected number under an uncorrected sentence is label-outlived-referent. The prose
        has to move with the measurement.

        ⚠⚠ AND THIS CASE ORIGINALLY ASSERTED THE WRONG THING — that the false claim is ABSENT.
        It failed, correctly: the correction QUOTES the false claim in order to retract it, and a
        retraction that may not name what it retracts is a worse document. Assert the presence of
        the truth, never the absence of a string.
        """
        import inspect
        doc = inspect.getdoc(PR) or ""
        self.assertIn("USED TO READ", doc,
                      "the docstring does not mark the corrected line as a correction, so a reader "
                      "cannot tell which of the two numbers is current")
        for fact in FA.EXTRACTION_CONTRACT:
            self.assertIn(fact, doc,
                          "the corrected measurement does not name %r — it was the omission of "
                          "`location` that made this look like a one-fact problem" % fact)


class EveryMissingFactIsCounted(unittest.TestCase):

    def test_report_carries_a_per_fact_tally(self):
        r = PR.report()
        self.assertIn("missingByFact", r)
        self.assertIsInstance(r["missingByFact"], dict)

    def test_it_names_ALL_THREE_facts_not_just_name(self):
        """★★ THE CORRECTED MEASUREMENT. If this ever shows only `name`, the truncation is back
        or the contract changed — either way the docstring above is wrong again."""
        r = PR.report()
        m = r.get("missingByFact") or {}
        if not m:
            self.skipTest("no seals blocked on this tree — nothing to count, and that is not a pass")
        self.assertEqual(set(m), set(FA.EXTRACTION_CONTRACT),
                         "the per-fact tally does not cover the whole contract: %r" % (m,))
        self.assertGreater(m.get("location", 0), 0,
                           "`location` shows as satisfied — if that is true the capture question is "
                           "answered and the docstring must say so")

    def test_the_key_is_present_on_EVERY_return_shape(self):
        """⚠ REG-546's own law, restated in this file: 'every return carries the same keys'. A
        shape that changes with the verdict is not a shape, and the UNKNOWN paths are exactly the
        ones a consumer hits when nothing was established."""
        import inspect
        src = inspect.getsource(PR.report)
        returns = src.count('"blocked"')
        tallies = src.count('"missingByFact"')
        self.assertEqual(returns, tallies,
                         "%d returns carry `blocked` but only %d carry `missingByFact` — a "
                         "consumer reading it breaks on the paths that mean nothing was "
                         "established" % (returns, tallies))


class TheStateStaysHonest(unittest.TestCase):
    """⚠ The correction must not quietly change the verdict. 0 seals satisfy the contract either
    way; only the REASON was wrong."""

    def test_it_still_reports_UNREACHABLE_not_a_cheerful_zero(self):
        r = PR.report()
        self.assertIn(r.get("state"), (PR.UNREACHABLE, PR.UNKNOWN, PR.CLEAN, PR.CONTRADICTION))
        if r.get("state") == PR.UNREACHABLE:
            self.assertTrue(r.get("blocked"),
                            "UNREACHABLE with no blocked reasons is a zero through a filter that "
                            "rejected everything, reported as if it measured something")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
