#!/usr/bin/env python3
"""v1712 — THE MISSED-FRAME SET MUST BE RECOVERABLE, NOT JUST COUNTED.

THE DEFECT. At session close KAI reports "N frames held text no eye read" — frames whose OCR found
NAME-LIKE text that no vision read ever covered. Those are exactly the frames that might hold an
item he found. It journalled one verbose row per frame for the first 20 and nothing at all for the
rest, so on his real session s_1786385768689_67392 the summary said 108 while sessions.jsonl held
20 'unread text' rows. The 88 others existed only inside a number.

That is worse than an ordinary silent cap. The count was perfectly honest, which made the loss
invisible: nothing downstream — no retro sweep, no re-read, no audit — could name a single one of
the frames the headline referred to. The verbose rows stay capped (they carry OCR text for the UI);
the frame IDS are ~20 bytes each and are now all carried, with `missedShown` naming the cap out
loud so the two numbers cannot drift apart unnoticed again.

⚠ NOTHING HERE READS OR WRITES HIS LIVE JOURNAL. The summary row is rebuilt from a fixture.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable  # noqa: E402

enable()


class TheSummaryRowCarriesEveryMissedFrame(unittest.TestCase):
    """Grades the SHIPPED row-builder by extracting it from control_app.py and running it."""

    def setUp(self):
        """Extract the WHOLE row-building region, starting at the verbose-row loop.

        A narrower slice starting at `_missed_ids` was the first attempt and it could not see the
        defect: truncating `missed` one line ABOVE the slice left every test green. The block must
        begin where `missed` is first consumed, or the guard only grades data the test itself
        supplied."""
        src = open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.src = src
        i = src.index("            for m in missed[:20]:")
        k = src.index("})", src.index('"note": f"\U0001f9e0 KAI closed the session', i)) + 2
        block = src[i:k]
        self.block = "\n".join(ln[12:] if ln.startswith(" " * 12) else ln
                                for ln in block.split("\n"))

    def _build(self, n_missed):
        missed = [{"f": "f_%d.jpg" % i, "ts": 1000 + i, "texts": ["Windforce"], "cls": "tooltip"}
                  for i in range(n_missed)]
        ns = {"missed": missed, "rows": [], "_sess_last": 9000, "now_ms": 9999, "sid": "s_fix",
              "grounded_reads": [],
              "report": {"scanned": 217, "textFrames": 158, "missedFrames": n_missed},
              "classes": {}, "scanned": 217}
        exec(compile(self.block, "<control_app summary row>", "exec"), ns)
        return ns["rows"][-1]

    def test_every_missed_frame_is_NAMED_even_past_the_verbose_cap(self):
        row = self._build(108)          # his real number
        ids = row["kai"]["missedIds"]
        self.assertEqual(len(ids), 108,
                         "88 frames that held unread text are unrecoverable again — the count is "
                         "honest but nothing can say WHICH frames it means")
        self.assertEqual(row["kai"]["missedFrames"], 108)

    def test_the_cap_on_verbose_rows_is_stated_rather_than_silent(self):
        row = self._build(108)
        self.assertEqual(row["kai"]["missedShown"], 20)
        self.assertIn("108", row["note"])
        self.assertIn("missedIds", row["note"])

    def test_a_small_session_says_nothing_about_a_cap_it_did_not_hit(self):
        row = self._build(5)
        self.assertEqual(row["kai"]["missedShown"], 5)
        self.assertNotIn("missedIds", row["note"], "no cap was applied, so none must be implied")
        self.assertEqual(len(row["kai"]["missedIds"]), 5)

    def test_a_clean_session_carries_an_empty_list_not_a_missing_key(self):
        # an absent key and 'nothing was missed' must not look the same to a reader
        row = self._build(0)
        self.assertEqual(row["kai"]["missedIds"], [])
        self.assertIn("missedIds", row["kai"])

    def test_the_row_is_json_serialisable_because_it_is_written_as_a_line(self):
        json.dumps(self._build(108), ensure_ascii=False)

    def test_the_verbose_rows_are_still_capped_at_20(self):
        # the cap itself is deliberate — 108 rows of OCR text would bury the journal
        self.assertIn("for m in missed[:20]:", self.src)


if __name__ == "__main__":
    unittest.main()
