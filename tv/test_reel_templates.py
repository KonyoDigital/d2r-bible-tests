#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""What a reel IS — and, when that cannot be said, WHY, naming the right component.

⚠⚠ THIS MODULE HAD NO SUITE. `reel_templates` shipped at v2571 and classifies all forty reels on
his shelf, and nothing anywhere tested it — the inverse of REG-079, which catches a suite no gate
runs. It was found while chasing the printer's PARTIAL state.

⚠ NOTHING HERE READS HIS JOURNAL. `_journal_rows` is replaced per test, so these cases pass or fail
on the fixture and never on what he happened to record.
[[feedback-fixtures-never-touch-live-data]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import reel_templates as RT  # noqa: E402


class _Swap(unittest.TestCase):
    """Feed `templates()` a journal and a river of our own."""

    REEL = "reel_s_1_1"

    def run_with(self, rows):
        import reel_river as RR
        real_j, real_r = RT._journal_rows, RR.river
        RT._journal_rows = lambda: ({self.REEL[len("reel_"):]: rows}, "")
        RR.river = lambda *a, **k: {"rows": [{"reel": self.REEL}]}
        try:
            rep = RT.templates()
        finally:
            RT._journal_rows, RR.river = real_j, real_r
        rows_out = rep.get("rows") or []
        self.assertTrue(rows_out, "templates() returned no row for the fixture reel")
        return rows_out[0]

    def why_of(self, rows):
        r = self.run_with(rows)
        return str(r.get("zoneWhy") or r.get("why") or r.get("zwhy") or "")


class WhenItCannotSayWHATAReelIsItNamesTheRIGHTCOMPONENT(_Swap):
    """★ THE REGRESSION THAT PRODUCED THIS FILE. Every un-classifiable reel used to say *"the
    segmenter returned no activity"*.

    MEASURED on his shelf: **14 of 40 reels are UNKNOWN, and all fourteen have ZERO deep rows** —
    while every classified reel has 1 to 9. Their footage is not gone: those fourteen carry **22 to
    2,385 frames on disk**, and they hold 7 to 40 shallow journal rows each. **They were read, and
    never read DEEPLY.** The segmenter was working perfectly and had been handed nothing.

    A label that points at the wrong component is how a working part gets investigated and a
    missing input does not. [[label-outlived-referent]]"""

    def test_a_reel_NOBODY_has_read_says_so(self):
        """⚠ PINS THE RULE, NOT MY WORDING — and the first cut of this test got that wrong. It
        asserted the sentence I had just written, and failed against a BETTER one the module
        already produced upstream: *"no journal row carries this reel's sessionId"*. That is the
        exact mistake REG-580 was about, made while fixing its sibling. What matters is that the
        reason names the ABSENT ROWS and does not blame the segmenter."""
        why = self.why_of([]).lower()
        self.assertTrue(("no journal row" in why) or ("nothing has read" in why),
                        "the reason does not say the rows are absent: %r" % why)
        self.assertNotIn("segmenter returned no activity", why,
                         "it points the reader at the segmenter for a missing input: %r" % why)

    def test_a_reel_read_SHALLOWLY_says_so_and_counts_the_rows(self):
        """His fourteen, exactly. The count matters: 40 shallow rows and no deep one is a very
        different picture from a reel nobody touched."""
        why = self.why_of([{"lane": "shallow"}] * 40)
        self.assertIn("NONE on the deep lane", why)
        self.assertIn("40", why, "it did not say HOW MANY rows exist: %r" % why)

    def test_a_reel_with_DEEP_rows_but_no_activity_says_THAT(self):
        why = self.why_of([{"lane": "deep", "sessionId": "s_1_1", "ts": 1}] * 3)
        self.assertIn("carries an activity", why)
        self.assertNotIn("NONE on the deep lane", why,
                         "a reel WITH deep rows was reported as having none: %r" % why)

    def test_the_three_cases_produce_THREE_different_sentences(self):
        """⚠ The point of the fix. If any two collapse, the label is back to naming one thing for
        three different states and a reader cannot act on it."""
        seen = {self.why_of([]),
                self.why_of([{"lane": "shallow"}] * 2),
                self.why_of([{"lane": "deep", "sessionId": "s_1_1", "ts": 1}])}
        self.assertEqual(len(seen), 3,
                         "two of the three unknown-reasons are the same sentence: %s" % seen)

    def test_it_never_blames_the_segmenter_when_the_segmenter_got_NOTHING(self):
        """⚠ THE SHARP ONE, and it is what the old wording did. When there is no deep row at all,
        the segmenter has not failed — it was never given anything to segment."""
        for rows in ([], [{"lane": "shallow"}] * 5):
            why = self.why_of(rows).lower()
            self.assertNotIn("the segmenter returned no activity", why,
                             "it blames the segmenter for an absent input: %r" % why)


class TheReelIsStillCLASSIFIEDWhenTheReadsAreThere(_Swap):
    """⚠ BASELINE. A file that only proves the failure paths would pass with the classifier
    deleted."""

    def test_a_reel_with_a_stash_activity_is_not_UNKNOWN(self):
        r = self.run_with([{"lane": "deep", "sessionId": "s_1_1", "ts": 1000,
                            "activity": "stash", "scene": "stash"},
                           {"lane": "deep", "sessionId": "s_1_1", "ts": 2000,
                            "activity": "stash", "scene": "stash"}])
        self.assertNotEqual(str(r.get("template")).upper(), "UNKNOWN",
                            "a reel with two stash reads was not classified: %r" % r)


class ItReportsAShapeThatDoesNotCHANGEWithTheVerdict(_Swap):
    """REG-547 — every row carries every key on every path, or a consumer has to know which
    branch produced it."""

    KEYS = ("reel", "template")

    def test_every_path_returns_the_same_keys(self):
        rows = [self.run_with([]),
                self.run_with([{"lane": "shallow"}]),
                self.run_with([{"lane": "deep", "sessionId": "s_1_1", "ts": 1,
                                "activity": "stash", "scene": "stash"}])]
        for k in self.KEYS:
            for r in rows:
                self.assertIn(k, r, "a row is missing %r — the shape changes with the verdict" % k)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
