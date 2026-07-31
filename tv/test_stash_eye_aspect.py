#!/usr/bin/env python3
"""v1536 — THE CROPS WERE CALIBRATED ON KONYO'S MACBOOK, and only his MacBook got them.

Konyo: *"THE AI READERS arent working properly my cuzin just did a ON AIR and it didnt read his
runestash"* … *"there might be something to do with resolution for MACBOOK/WINDOWS?"*

He was right. Every crop band in stash_eye.py was measured on 2940×1912 (aspect 1.538) and the
caller applied them only for 1.45 <= aspect <= 1.62. A normal Windows monitor is 16:9 = 1.778 —
outside that gate — so every one of his cousin's frames fell to the "foreign/windowed" fallback:
the whole left 46% of the screen. On 1920×1080 that is a 954k-pixel slab where the Mac gets a
177k-pixel band, so the grid arrived 5.4× more diluted and both the tab OCR and the grid
fingerprint were reading a much emptier picture.

The first test here is the one that matters most: KONYO'S OWN MACHINE MUST NOT CHANGE. A fix for
the cousin that moves the Mac would trade one broken machine for another.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: F401,E402
import stash_eye as se  # noqa: E402


class TestKonyosMacIsUntouched(unittest.TestCase):
    def test_the_locked_band_comes_back_BYTE_IDENTICAL_on_his_film(self):
        # ★ 2940×1912 is the actual film every band was measured on
        for layout in ("runes", "gems", "materials", "shared", "personal"):
            self.assertEqual(se.crops_for_aspect(layout, 2940 / 1912.0),
                             se._TALLY_CROPS[layout],
                             layout + " moved on Konyo's own machine")

    def test_every_aspect_inside_the_calibrated_gate_is_untouched(self):
        for a in (1.45, 1.50, 1.538, 1.60, 1.62):
            self.assertEqual(se.crops_for_aspect("runes", a), se._TALLY_CROPS["runes"])


class TestTheCousinGetsARealBand(unittest.TestCase):
    def test_16_9_no_longer_falls_off_the_calibrated_gate(self):
        band = se.crops_for_aspect("runes", 16 / 9.0)
        self.assertIsNotNone(band, "16:9 must get a band, not the 46% slab")
        self.assertNotEqual(band, se._TALLY_CROPS["runes"])

    def test_the_derived_band_keeps_the_PANEL_the_same_physical_size(self):
        # the derivation's whole claim: D2R scales its UI with HEIGHT and anchors the panel left, so
        # the panel's WIDTH IN PIXELS should barely move between a Mac and a Windows box of the same
        # height. If this drifts, the derivation is wrong.
        mac_w, mac_h = 2940, 1912
        win_w, win_h = 1920, 1080
        mb = se.crops_for_aspect("runes", mac_w / float(mac_h))
        wb = se.crops_for_aspect("runes", win_w / float(win_h))
        mac_px_per_h = (mb[2] - mb[0]) * mac_w / mac_h      # panel width, in units of frame height
        win_px_per_h = (wb[2] - wb[0]) * win_w / win_h
        self.assertAlmostEqual(mac_px_per_h, win_px_per_h, places=6)

    def test_the_vertical_band_does_NOT_move(self):
        # the panel is anchored vertically the same way; only the horizontal fraction changes
        mb = se._TALLY_CROPS["runes"]
        wb = se.crops_for_aspect("runes", 16 / 9.0)
        self.assertEqual((mb[1], mb[3]), (wb[1], wb[3]))

    def test_it_stays_inside_the_frame_at_absurd_aspects(self):
        for a in (2.37, 3.55, 8.0):          # ultrawide, super-ultrawide, nonsense
            b = se.crops_for_aspect("runes", a)
            self.assertGreaterEqual(b[0], 0.0)
            self.assertLessEqual(b[2], 1.0)
            self.assertLess(b[0], b[2])

    def test_a_WINDOWED_frame_still_refuses_a_band(self):
        # ★ the derivation only holds for a fullscreen game. A windowed or letterboxed frame has the
        # panel somewhere else entirely, and inventing a band there would be worse than the slab.
        for a in (1.29, 1.0, 0.75, 0):
            self.assertIsNone(se.crops_for_aspect("runes", a))

    def test_an_unknown_layout_falls_back_to_the_generic_left_panel(self):
        self.assertEqual(se.crops_for_aspect("wat", 1.538), se._TALLY_CROPS["runes"])


class TestTheFixIsHonestlyLabelled(unittest.TestCase):
    def test_the_source_says_it_is_DERIVED_and_not_yet_measured(self):
        # this band has never been checked against a real 16:9 stash frame. Saying so in the file is
        # the difference between a fix and a claim.
        src = open(os.path.join(HERE, "stash_eye.py"), encoding="utf-8").read()
        self.assertIn("DERIVED, NOT YET MEASURED", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
