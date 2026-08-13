#!/usr/bin/env python3
"""v1712 — THE CHRONICLE'S STILL THRESHOLD MUST STAY BELOW WHAT THE SIGNAL CAN PRODUCE.

THE DEFECT THIS PINS. still_runs() groups consecutive frames whose fingerprints differ by no more
than max_diff, and candidate_runs() keeps the runs long enough to be worth one classify. At
STILL_MAX_DIFF = 0.22 the whole of his reel_s_1786385768689_67392 — 217 frames, 220 seconds,
containing a journalled 8-frame Chronicle visit — collapsed into ONE run. live_probe() then picked
a single frame to stand for 220 seconds, that frame was gameplay, and the entire session was
discarded as not-a-Chronicle. Nine of his ten reels read ZERO pages for this reason; only the reel
with a journalled visit was rescued, and through a different door (known_chronicle= marks).

WHY IT COULD NEVER FIRE: jpeg_sig is 16x16 grayscale and sig_diff counts cells differing by more
than tol=28. The LARGEST frame-to-frame diff anywhere in that reel is 0.133; the median is 0.000.
A threshold of 0.22 is above the ceiling of what the measurement can produce, so no pair ever broke
a run. **A threshold nothing can cross is not loose — it is absent**, and it reads as a working
parameter forever.

These tests are SYNTHETIC on purpose: they run on a CI runner, where his footage does not exist
and never will (tv/frames/ is gitignored — they are his screenshots). The footage-backed
calibration lives in the constant's own comment, with its numbers.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable  # noqa: E402

enable()

import chronicle_retro as cr  # noqa: E402


def _sig(*vals):
    """A fingerprint of 256 cells, `vals` giving the value of each sixteenth."""
    out = bytearray()
    for v in vals:
        out.extend([v] * (256 // len(vals)))
    return bytes(out)


class TheThresholdMustBeInsideTheSignalsRange(unittest.TestCase):
    def test_it_is_far_below_the_largest_diff_his_footage_can_produce(self):
        # 0.133 was the max over 217 real frames. A threshold at or above that can never break a
        # run, which is exactly how one run swallowed a whole session.
        self.assertLess(cr.CHRON_STILL_MAX_DIFF, 0.133,
                        "the chronicle threshold is above the largest diff his reels produce, so "
                        "no frame pair can ever break a run and every session becomes ONE run")
        self.assertGreater(cr.CHRON_STILL_MAX_DIFF, 0.0,
                           "0 would break a run on every frame and cost a classify per frame")

    def test_the_shipped_default_STILL_MAX_DIFF_is_the_one_that_failed(self):
        # kept deliberately: vault_retro.py:452 borrows it. This documents the split rather than
        # letting a future reader 'tidy' the two back together.
        self.assertEqual(cr.STILL_MAX_DIFF, 0.22)
        self.assertLess(cr.CHRON_STILL_MAX_DIFF, cr.STILL_MAX_DIFF)


class ASceneChangeMustBreakTheRun(unittest.TestCase):
    """The property that actually matters, stated without any footage."""

    def _frames(self, n):
        return [{"f": "f_%d.jpg" % i, "ts": 1000 + i * 500} for i in range(n)]

    def _run_with(self, sigs, thr):
        frames = self._frames(len(sigs))
        by = {fr["f"]: s for fr, s in zip(frames, sigs)}
        return cr.still_runs(frames, lambda n: by[n], max_diff=thr)

    def test_a_modest_but_real_change_SPLITS_at_the_chronicle_threshold(self):
        # 8 cells of 256 move = 0.031 — the shape of a D2R scene change at 16x16, well under 0.22
        held = _sig(*([100] * 16))
        after = _sig(*([100] * 15 + [200]))          # one sixteenth changes => 0.0625
        runs = self._run_with([held, held, held, after, after, after], cr.CHRON_STILL_MAX_DIFF)
        self.assertEqual(len(runs), 2, "a real scene change must start a new run, or one probe "
                                       "ends up representing two different screens")

    def test_the_SAME_change_is_invisible_at_0_22_which_is_the_bug(self):
        held = _sig(*([100] * 16))
        after = _sig(*([100] * 15 + [200]))
        runs = self._run_with([held, held, held, after, after, after], 0.22)
        self.assertEqual(len(runs), 1,
                         "if this ever becomes 2, the 0.22 story in the constant's comment is "
                         "wrong and the calibration should be re-read")

    def test_a_held_panel_still_stays_ONE_run(self):
        # the whole point of grouping: a page he holds must not cost one classify per frame
        held = _sig(*([100] * 16))
        runs = self._run_with([held] * 12, cr.CHRON_STILL_MAX_DIFF)
        self.assertEqual(len(runs), 1)
        self.assertEqual(len(runs[0]["frames"]), 12)

    def test_read_reel_passes_the_chronicle_threshold_and_not_the_default(self):
        """The constant is worthless if the call site does not use it."""
        src = open(os.path.join(HERE, "chronicle_retro.py"), encoding="utf-8").read()
        call = src.split("    runs = still_runs(idx_frames, sig_of", 1)[1][:60]
        self.assertIn("CHRON_STILL_MAX_DIFF", call,
                      "read_reel is back on the shared default — the chronicle sweep is blind again")


if __name__ == "__main__":
    unittest.main()
