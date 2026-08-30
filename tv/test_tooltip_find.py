#!/usr/bin/env python3
"""FINDING A D2R TOOLTIP IN ONE FRAME — and refusing when there is none.

★ This is the blocker everything downstream sat behind: the cursor->cell offset, slot identity,
and MINI(AUTOMATIC) driving the hovers itself all need a tooltip located in a frame.

EVERY OBVIOUS METHOD FAILED FIRST, and each was killed by measurement rather than opinion:
  · DIFFERENCING (tooltip_crop.changed_rect) — 39 consecutive pairs on his reel produced 38 rects
    and every one was the WHOLE SCREEN, because the D2R world never stops animating behind the
    panels. vault_retro discarded all of them at its 60 KB cap, silently, on every reel.
  · DARKNESS — 48.7% of his frame is near-black. D2R is a dark game.
  · A GOLD BORDER / FLAT PANEL — only rendering the frame and LOOKING revealed that the D2R
    tooltip is SEMI-TRANSPARENT: the stash grid shows through it, its edges are soft. There is no
    border to find and the region is not flat.
  · WHAT IS TRUE — a tooltip is the one place on screen with DENSE HORIZONTAL TEXT.

⚠ AND DENSITY ALONE FINDS THE HUD. On a reel that registered nothing it returned the same
(2450, 0, 490, 318) top-right box on five consecutive frames. The separation is SIZE and it is not
close: his real tooltip is 33.4% of the frame, the impostor 2.8%.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import tooltip_find as TF


def _frame(tmp, w=1200, h=900):
    """A real image file. density() opens the frame before it ever calls the reader, so a .py
    path stands in for nothing — it fails on the OPEN and the tile logic is never exercised.
    That is the fixture being the thing under test instead of the code.
    [[feedback-blind-fixture-green-gate]]"""
    from PIL import Image
    p = os.path.join(tmp, "frame.jpg")
    Image.new("RGB", (w, h), (12, 10, 8)).save(p, "JPEG", quality=60)
    return p


def _fake(grid):
    """A reader that returns N lines for the tile it is asked about, driven by a grid."""
    state = {"i": 0}
    flat = [n for row in grid for n in row]

    def read(_path):
        n = flat[state["i"]] if state["i"] < len(flat) else 0
        state["i"] += 1
        return {"lines": ["a line of text"] * n}
    return read


class TestItFindsTheDenseTextRegion(unittest.TestCase):

    def test_it_grows_from_the_densest_tile_through_its_neighbours(self):
        grid = [[0, 0, 0, 0],
                [0, 3, 4, 0],
                [0, 9, 5, 0],
                [0, 0, 0, 0]]
        import tempfile
        d, why = TF.density(_frame(tempfile.mkdtemp()), cols=4, rows=4, reader=_fake(grid))
        self.assertIsNone(why)
        self.assertEqual(d["grid"], grid)

    def test_a_frame_with_almost_no_text_is_REFUSED(self):
        import tempfile
        grid = [[0, 0], [0, 1]]
        rect, why = TF.locate(_frame(tempfile.mkdtemp()), cols=2, rows=2, reader=_fake(grid))
        self.assertIsNone(rect, "it returned a rectangle for a frame with one line of text")
        self.assertIn("below the", why)

    def test_a_SMALL_dense_box_is_refused_as_game_chrome(self):
        """The HUD false positive: one tile of dense text in a corner. Real tooltips are big."""
        import tempfile
        grid = [[0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 40]]
        rect, why = TF.locate(_frame(tempfile.mkdtemp()), cols=4, rows=4, reader=_fake(grid))
        self.assertIsNone(rect, "a single corner tile was accepted as a tooltip")
        self.assertIn("chrome", why)
        self.assertIn("33", why, "the refusal does not cite the measurement it is based on")

    def test_a_LARGE_dense_region_is_accepted(self):
        import tempfile
        grid = [[0, 0, 0, 0],
                [0, 6, 6, 0],
                [0, 9, 7, 0],
                [0, 5, 5, 0]]
        rect, why = TF.locate(_frame(tempfile.mkdtemp()), cols=4, rows=4, reader=_fake(grid))
        self.assertIsNotNone(rect, why)
        self.assertEqual(len(rect), 4, "the rect is not (left, top, width, height)")

    def test_a_missing_frame_is_refused_not_crashed(self):
        rect, why = TF.locate("/nope/not/here.jpg")
        self.assertIsNone(rect)
        self.assertIn("no frame", why)


class TestTheLedgerKeepsPENDINGOutOfTheScore(unittest.TestCase):

    def setUp(self):
        self._real = TF._load, TF._save
        self.db = {}
        TF._load = lambda: self.db
        TF._save = lambda d: self.db.update(d)

    def tearDown(self):
        TF._load, TF._save = self._real

    def test_a_located_tooltip_nobody_judged_counts_in_NEITHER_side(self):
        TF.bank(True, named=None)
        TF.bank(True, named=None)
        r = TF.report()
        self.assertEqual(r["pending"], 2)
        self.assertEqual(r["judged"], 0)
        self.assertIsNone(r["wilson"], "a score was invented from two unjudged locations")

    def test_named_and_blank_are_the_two_sides(self):
        TF.bank(True, named=True)
        TF.bank(True, named=True)
        TF.bank(True, named=False)
        r = TF.report()
        self.assertEqual((r["named"], r["blank"], r["judged"]), (2, 1, 3))
        self.assertIsNotNone(r["wilson"])
        self.assertLess(r["wilson"], 0.67,
                        "2-of-3 scored at or above the naive ratio — that is not a lower bound")

    def test_a_refusal_is_counted_and_is_not_a_failure(self):
        TF.bank(False, why="only 2 text lines")
        r = TF.report()
        self.assertEqual(r["refused"], 1)
        self.assertEqual(r["judged"], 0, "a refusal leaked into the Wilson denominator")


if __name__ == "__main__":
    try:
        import console_safe as _cs; _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
