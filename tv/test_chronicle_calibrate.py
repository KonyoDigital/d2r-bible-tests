#!/usr/bin/env python3
"""The Chronicle completion-bar reader — and the property it did not have.

v1920 shipped `bar_fill` as a SAFEGUARD with a docstring claiming ±1.5 points. Measured across 36
frames from three different reels it returned **0.8395 on every frame it answered for** — one
distinct value, which is not a measurement. On a page printing 63% it said 83.9%.

A reader that returns the same number for different inputs is dead, and nothing in the suite could
tell. That is the test below.
"""
import glob
import os
import sys
import unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

import chronicle_calibrate as cal  # noqa: E402

# reel -> the percentage the GAME printed on those frames, read by eye
REELS = {
    "reel_s_1787307553811_9452": 85,
    "reel_s_1786385768689_67392": 63,
}


def _frames(reel, cap=40):
    return sorted(glob.glob(os.path.join(HERE, "frames", "hist", reel, "f_*.jpg")))[:cap]


class TestTheBarReaderIsNotAConstant(unittest.TestCase):
    """THE GUARD THAT WOULD HAVE CAUGHT v1920 ON THE DAY."""

    def test_two_reels_at_different_completions_read_differently(self):
        seen = {}
        for reel in REELS:
            fs = _frames(reel)
            if not fs:
                self.skipTest("his reels are not on this machine")
            vals = [v for v in (cal.bar_fill(p) for p in fs) if v is not None]
            if not vals:
                self.fail("%s: the reader answered on NO frame — it has stopped reading, and a "
                          "reader that only refuses is as useless as one that only agrees" % reel)
            seen[reel] = Counter(round(v, 3) for v in vals).most_common(1)[0][0]
        self.assertEqual(len(set(seen.values())), len(seen),
                         "two reels at different completions returned the SAME value %s — that is "
                         "a constant wearing a measurement, which is exactly what v1920 shipped"
                         % seen)

    def test_it_lands_within_about_two_points_of_the_printed_figure(self):
        for reel, printed in REELS.items():
            fs = _frames(reel)
            if not fs:
                self.skipTest("his reels are not on this machine")
            vals = [v for v in (cal.bar_fill(p) for p in fs) if v is not None]
            self.assertTrue(vals, "%s: no frame answered" % reel)
            got = Counter(round(v, 3) for v in vals).most_common(1)[0][0] * 100
            self.assertLess(abs(got - printed), 2.5,
                            "%s reads %.1f%% where the game prints %d%% — the reader is a watchdog "
                            "for a 3-point gap, so it has to be inside that gap itself"
                            % (reel, got, printed))

    def test_it_answers_on_most_frames_of_a_reel_that_has_a_bar(self):
        """Coverage is part of the contract: a reader that refuses everything never disagrees."""
        for reel in REELS:
            fs = _frames(reel)
            if not fs:
                self.skipTest("his reels are not on this machine")
            n = sum(1 for p in fs if cal.bar_fill(p) is not None)
            self.assertGreater(n, len(fs) * 0.5,
                               "%s: answered on only %d of %d frames" % (reel, n, len(fs)))


class TestItStillRefusesWhatHasNoBar(unittest.TestCase):
    def test_a_black_loading_frame_is_refused(self):
        p = os.path.join(HERE, "frames", "hist", "reel_s_1784984019250_95276", "f_1784984136680.jpg")
        if not os.path.isfile(p):
            self.skipTest("frame missing")
        self.assertIsNone(cal.bar_fill(p))

    def test_an_unreadable_path_is_refused_not_guessed(self):
        self.assertIsNone(cal.bar_fill(os.path.join(HERE, "not-a-frame.jpg")))


class TestTheVerdictSaysUnknownRatherThanAgreeing(unittest.TestCase):
    def test_no_bar_is_not_agreement(self):
        v = cal.verdict(None, 118, 135)
        self.assertIsNone(v["ok"])
        self.assertIn("not the same as", v["say"])

    def test_no_total_is_not_agreement(self):
        v = cal.verdict(0.85, 118, 0)
        self.assertIsNone(v["ok"])

    def test_HIS_ACTUAL_DEFECT_IS_INSIDE_THE_TOLERANCE_and_that_is_recorded(self):
        """⚠ THE WATCHDOG WOULD NOT HAVE CAUGHT THE THING IT WAS BUILT FOR.

        His board read 118/135 = 87.4% while the game printed 85%. The gap is 2.4 points and the
        tolerance is 3, so this returns "agree". The tolerance is deliberately NOT tightened — the
        reader is only good to ~2 points itself, and a gate that fires on its own noise is a gate
        nobody reads. The exact instrument for a 2-row error is counter_ledger, which reads the
        game's own Remaining page and NAMES the rows.

        This test exists so that limit is a recorded fact rather than a surprise.
        [[feedback-threshold-above-the-ceiling]]"""
        v = cal.verdict(0.85, 118, 135)
        self.assertTrue(v["ok"],
                        "if this now fails, someone tightened TOLERANCE — check it against the "
                        "reader's own ~2-point error before believing the new verdicts")
        self.assertLess(abs((118 / 135.0) - 0.85) * 100, cal.TOLERANCE * 100)

    def test_a_gap_LARGER_than_the_tolerance_is_called(self):
        v = cal.verdict(0.80, 122, 135)          # board 90.4% vs game 80% -> 10 points
        self.assertFalse(v["ok"])
        self.assertIn("DISAGREE", v["say"])

    def test_agreement_within_tolerance_passes(self):
        v = cal.verdict(0.859, 116, 135)         # both ~85.9%
        self.assertTrue(v["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
