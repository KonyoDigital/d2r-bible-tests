# -*- coding: utf-8 -*-
"""v2709 — THE PRINTER'S TEMPLATE STATION COULD NOT NAME WHICH CHRONICLE PAGE A REEL SHOWED.

His check, 2026-09-05: *".mini-foc this should be the printer 3d/4d and processing unified station
for reels the template and classifier ... just making sure when we built the 3d and 4d printer anr
architured it we have these in the processing system there too"*. He was right to ask.

MEASURED: `MINI_FOCUSES` has six entries. A stash reel resolved all the way to
`stash · gems/personal`; a chronicle reel stopped at the bare word `chronicle`. Four of six
resolved, two reached the doorstep — because `tabs` is built ONLY from `stashTab`, deliberately
("a tab is evidence about WHICH stash panel was open").

=== THE DATA WAS ALWAYS THERE, AND I ELIMINATED THIS ROUTE TWICE BEFORE FINDING IT ===
`tv_diablo` asks for `chronicleTab` on EVERY frame, and v1689's `chron_visit_flush` writes a
`{lane:'chronicle', kind:'visit'}` row carrying the LEDGER at session close. Measured on his ring:
13 visit rows across 12 sessions — uniques 9, sets 3, one unknown. No frame read, no new intake
field, no image decoding anywhere near the snapshot path.

⚠⚠ WHY THIS FILE HAS TO EXIST: THE JOIN IS UNEXERCISED BY HIS OWN DATA.
    sessions with a chronicle visit row : 12
    sessions on the current shelf       : 40
    OVERLAP                             : 0
Not one reel on his shelf can exercise this path today. The single CHRONICLE reel there,
`s_1786385768689_67392`, is named in chron_visit_flush's own docstring — 8 deep frames,
`chronicleTab='uniques'`, and ZERO visit rows written, because the state machine only closed a
visit on the way OUT and he looked at the Chronicle LAST. v1689 fixed that; the reel predates it.

So on his machine this code runs, answers UNKNOWN, and is RIGHT to — which is indistinguishable
from a join that does not work at all. That is [[gate-blind-to-unexercised-input]] exactly: real
data, correct code, and no evidence either way. This file supplies the input his shelf never does.
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

import reel_templates as RT


class ChronicleLedgerRefinesTheTemplate(unittest.TestCase):
    """Drives templates() against a synthetic journal, because his shelf cannot."""

    def _run(self, journal_rows, activity="chronicle"):
        """-> the single row templates() produces for one synthetic reel."""
        sid = "s_TEST_0001"
        real_rows = RT._journal_rows
        real_segs = RT._segments_for
        RT._journal_rows = lambda *a, **k: ({sid: journal_rows}, "")
        # ⚠ PATCH THE SEGMENTER TOO, and for a reason worth stating: segments come from
        # _segments_for(name, by_session), NOT from the river row. Without this the synthetic reel
        # has no activity, `template` resolves to None, and every assertion below fails on a
        # fixture fault while the code under test is fine — which is how a real defect gets
        # buried under an instrument one. This test is about the LEDGER JOIN; segmentation has
        # its own tests and is not what is being graded here.
        RT._segments_for = lambda name, by: ([{"activity": activity}], "")
        try:
            river = {"rows": [{"reel": "reel_" + sid, "segments": [{"activity": activity}]}]}
            out = RT.templates(river=river)
            rows = out.get("rows") if isinstance(out, dict) else out
            self.assertTrue(rows, "the synthetic river produced no rows — this measures NOTHING")
            return rows[0]
        finally:
            RT._journal_rows = real_rows
            RT._segments_for = real_segs

    def test_a_visit_row_names_the_ledger(self):
        """The whole point: chronicle · uniques, not a bare `chronicle`."""
        row = self._run([
            {"lane": "deep", "scene": "chronicle", "sessionId": "s_TEST_0001"},
            {"lane": "chronicle", "kind": "visit", "ledger": "uniques", "sessionId": "s_TEST_0001"},
        ])
        self.assertEqual(row.get("ledgers"), ["uniques"],
                         "the visit row's ledger did not reach the template station: %r"
                         % (row.get("ledgers"),))
        self.assertIn("uniques", str(row.get("subTemplate")),
                      "subTemplate is %r — a chronicle reel that knows its ledger must say so, "
                      "the way a stash reel says `stash - gems/personal`"
                      % (row.get("subTemplate"),))

    def test_a_deep_row_carrying_chronicleTab_also_works(self):
        """tv_diablo asks for chronicleTab on every frame; a visit row is not the only source."""
        row = self._run([
            {"lane": "deep", "scene": "chronicle", "chronicleTab": "sets", "sessionId": "s_TEST_0001"},
        ])
        self.assertEqual(row.get("ledgers"), ["sets"])
        self.assertIn("sets", str(row.get("subTemplate")))

    def test_no_ledger_recorded_answers_EMPTY_not_a_guess(self):
        """His one real chronicle reel is exactly this case, and it must stay honest.

        Pre-v1689 reels have deep chronicle frames and no visit row. UNKNOWN is the correct
        answer; inventing 'uniques' because it is the commonest would be a lie with no author.
        """
        row = self._run([
            {"lane": "deep", "scene": "chronicle", "sessionId": "s_TEST_0001"},
        ])
        self.assertEqual(row.get("ledgers"), [],
                         "a reel with no recorded ledger reported %r — nobody-recorded is not "
                         "the same fact as a ledger" % (row.get("ledgers"),))
        self.assertEqual(row.get("subTemplate"), row.get("template"),
                         "the template was refined by something that was never recorded")

    def test_an_empty_ledger_string_is_not_a_ledger(self):
        """tv_diablo's own instruction: 'leave chronicleTab "" — an unknown ledger is ...'."""
        row = self._run([
            {"lane": "chronicle", "kind": "visit", "ledger": "", "sessionId": "s_TEST_0001"},
            {"lane": "deep", "scene": "chronicle", "chronicleTab": "", "sessionId": "s_TEST_0001"},
        ])
        self.assertEqual(row.get("ledgers"), [],
                         "an empty ledger string was treated as a ledger: %r" % (row.get("ledgers"),))

    def test_a_stash_reel_that_ALSO_has_a_ledger_keeps_its_tab(self):
        """⚠ THE CASE THAT MAKES THE ZONE GUARD MEAN ANYTHING, and my first cut did not have it.

        Sabotaging the guard — letting a ledger refine ANY zone — left the suite GREEN, because
        every other stash case here has no ledger data at all, so removing the guard changed
        nothing. A law that only holds on inputs where it cannot be violated is not a law.

        A session that visited the Chronicle AND opened the stash produces both a visit row and a
        stashTab. The zone decides which one names the template: a STASH reel is refined by its
        tab, whatever else the session recorded.
        """
        row = self._run([
            {"lane": "deep", "stashTab": "runes", "sessionId": "s_TEST_0001"},
            {"lane": "chronicle", "kind": "visit", "ledger": "uniques", "sessionId": "s_TEST_0001"},
        ], activity="stash")
        self.assertIn("runes", str(row.get("subTemplate")),
                      "a STASH reel was named by a chronicle ledger instead of its stash tab: %r"
                      % (row.get("subTemplate"),))
        self.assertNotIn("uniques", str(row.get("subTemplate")),
                         "the chronicle ledger reached across the zone boundary and refined a "
                         "stash reel: %r" % (row.get("subTemplate"),))

    def test_a_stash_reel_is_untouched_by_this(self):
        """The refinement must not reach across zones — a stash tab is still a stash tab."""
        row = self._run([
            {"lane": "deep", "stashTab": "gems", "sessionId": "s_TEST_0001"},
        ], activity="stash")
        self.assertIn("gems", str(row.get("subTemplate")),
                      "the stash path stopped naming its tab: %r" % (row.get("subTemplate"),))
        self.assertEqual(row.get("ledgers"), [],
                         "a stash reel was given a chronicle ledger: %r" % (row.get("ledgers"),))


if __name__ == "__main__":
    unittest.main(verbosity=2)
