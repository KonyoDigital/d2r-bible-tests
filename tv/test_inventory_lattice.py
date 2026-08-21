#!/usr/bin/env python3
"""The inventory lattice and its refusals.

The refusals ARE the feature. Without them this returned a confident "18 occupied, 9 free" for the
game-creation LOBBY MENU — a column of checkboxes is periodic, so a lattice fitter finds a lattice
in it and nothing about the answer looks wrong. That is the plausible-but-wrong detector this
subsystem has already paid for twice (v1857, v1859).

Every case below is a real frame from his own reel, named, so a future change that loosens a gate
fails here rather than on his screen. [[feedback-verify-not-proxy]] [[feedback-blind-fixture-green-gate]]
"""
import glob
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

import vault_corpus as vc  # noqa: E402

REEL = os.path.join(HERE, "frames", "hist", "reel_s_1784984019250_95276")
GOOD = os.path.join(REEL, "f_1784984271825.jpg")   # a real inventory panel
LOBBY = os.path.join(REEL, "f_1784984170804.jpg")  # the game-creation menu
BLACK = os.path.join(REEL, "f_1784984136680.jpg")  # an all-black loading frame
TOOLTIP = os.path.join(REEL, "f_1784984248692.jpg")  # inventory under an item tooltip


def _have(p):
    return os.path.isfile(p)


class TestTheLatticeIsFoundOnARealPanel(unittest.TestCase):
    def setUp(self):
        if not _have(GOOD):
            self.skipTest("his reel is not on this machine")

    def test_it_is_ten_by_four_with_square_cells(self):
        r = vc.inventory_lattice(GOOD)
        self.assertTrue(r["ok"], r.get("why"))
        self.assertEqual(r["cells"], 40)
        self.assertAlmostEqual(r["colPitch"], 86.75, delta=1.5)
        self.assertAlmostEqual(r["rowPitch"], 85.75, delta=1.5)
        self.assertLess(abs(r["colPitch"] - r["rowPitch"]), 4.0, "inventory cells are square")

    def test_occupancy_is_bimodal_enough_that_the_threshold_does_not_matter(self):
        o = vc.inventory_occupancy(GOOD)
        self.assertTrue(o["ok"], o.get("why"))
        self.assertEqual((o["occupied"], o["free"]), (22, 18))
        self.assertEqual(o["cells"], 40)


class TestItRefusesWhatItCannotRead(unittest.TestCase):
    """A detector that never says NO is not a detector."""

    def test_the_lobby_menu_is_refused(self):
        if not _have(LOBBY):
            self.skipTest("frame missing")
        r = vc.inventory_lattice(LOBBY)
        self.assertFalse(r["ok"],
                         "the game-creation menu was accepted as an inventory — this is the exact "
                         "false positive that reported 18 occupied / 9 free")
        self.assertIn("ALWAYS", r["why"] + " " + r.get("why", ""))

    def test_a_black_loading_frame_is_refused(self):
        if not _have(BLACK):
            self.skipTest("frame missing")
        r = vc.inventory_lattice(BLACK)
        self.assertFalse(r["ok"])
        self.assertTrue("bound" in r["why"] or "noise floor" in r["why"], r["why"])

    def test_an_unreadable_path_is_refused_not_guessed(self):
        r = vc.inventory_lattice(os.path.join(HERE, "definitely-not-a-frame.jpg"))
        self.assertFalse(r["ok"])

    def test_occupancy_refuses_when_the_lattice_did(self):
        if not _have(LOBBY):
            self.skipTest("frame missing")
        o = vc.inventory_occupancy(LOBBY)
        self.assertFalse(o["ok"],
                         "occupancy must not answer on a panel the lattice refused — that is how a "
                         "menu produced a free-space count")


class TestOneFrameIsAFixture(unittest.TestCase):
    def test_a_tooltip_frame_reads_differently_and_that_is_why_frames_are_pooled(self):
        if not (_have(TOOLTIP) and _have(GOOD)):
            self.skipTest("frames missing")
        a = vc.inventory_occupancy(GOOD)
        b = vc.inventory_occupancy(TOOLTIP)
        self.assertTrue(a["ok"] and b["ok"])
        self.assertNotEqual((a["occupied"], a["free"]), (b["occupied"], b["free"]),
                            "the tooltip frame is supposed to disagree — if it stops, this test is "
                            "no longer measuring what it claims")

    def test_the_modal_reading_over_the_reel_survives_the_outlier(self):
        fs = sorted(glob.glob(os.path.join(REEL, "f_*.jpg")))
        if len(fs) < 20:
            self.skipTest("his reel is not on this machine")
        r = vc.inventory_reading(fs)
        self.assertTrue(r["ok"])
        self.assertEqual((r["occupied"], r["free"]), (22, 18))
        self.assertGreater(r["agreed"], 50, "a modal reading backed by a handful of frames is not "
                                            "corroboration")
        self.assertTrue(r["minority"], "the disagreeing frame must be REPORTED, not averaged away")

    def test_no_readable_frame_is_unknown_not_empty(self):
        r = vc.inventory_reading([BLACK] if _have(BLACK) else [])
        self.assertIsNone(r["ok"])
        self.assertIn("not the same as", r["say"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
