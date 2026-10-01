# -*- coding: utf-8 -*-
"""REG-1648 — THE INVENTORY LATTICE READS HIS FRAMES AT EVERY HEIGHT HIS CAPTURE RECORDS.

vault_corpus.inventory_lattice is the vault sweep's FREE cross-check: it finds the 10x4 inventory and counts the
occupied cells, so a paid read that names more items than the panel holds is caught, and a read that names none
can still be sealed as a complete answer. Its crop is in FRACTIONS of the frame, and every other constant - the
pitch search 70-100, the ridge window 12, the square tolerance 4, the cell inset 12 - was PIXELS measured on his
2940x1912 reel. From 2026-08-31 his Mac records 1440x936 and 1440x904, where a cell is ~42 px: the rows crop is
192 px tall, no pitch >= 70 fits four rows into it, and every frame came back "no grid is visible here".
MEASURED 2026-10-01, the panel frames of every reel on his Mac:
    before   2940x1912 ok 12 of 12 sampled  ·  1440-wide ok 0 of 76 sampled (8 reels, up to 12 each)
    after    2940x1912 ok 94 of 94 (pitch 86.8 x 85.8, 22/18 on 93 frames - unchanged)  ·  1440-wide ok 268 of 273
and six panels from five reels checked by eye against the counted grid, cell for cell. So no read frame had been
cross-checked for a month, no seal could be definitive, and the vault lane re-read two reels on every relaunch.
D2R draws its UI in proportion to the frame HEIGHT: row pitch 85.75 @1912, 42.0 @936, 40.5 @904.

  · DRIVEN on drawn inventories at 2940x1912, 1440x936 and 1440x904 - the three heights on his disk: 10x4 found,
    pitch = 86.75 x H/1912, and the occupied count is exactly the cells that were drawn full (also 0 and 40).
  · The REFUSALS hold at the small height: black, no panel, and cells 3 px from square (6 px at 1912) all refused.
  · His own frames, where they exist (his Mac): the two reels that could never seal now read, and the reel the
    constants came from reads exactly as before. Absent footage SKIPS, and a skip is not a pass.
⚠ The cell inset is scaled too; measured, it changes 2 of 268 real frames, both a tooltip-dimmed corner of the
2x2 cube, where the scaled answer (occupied) is the true one. No sabotage claims it - nothing here could tell.
RED_PROOF below. [[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import vault_corpus as vc  # noqa: E402

HEIGHTS = ((2940, 1912), (1440, 936), (1440, 904))
SOME = {(0, 0), (0, 1), (1, 0), (1, 1), (0, 4), (2, 7), (3, 9), (3, 2), (1, 5), (2, 2)}


def _draw(path, W, H, filled, cp_cal=86.75, rp_cal=85.75, panel=True, black=False, seed=7):
    """A D2R-like inventory: near-black empty cells (mean 4.3), bright item cells, lighter borders, placed in the
    crop the way his game places it, every length in this frame's pixels (x H/1912)."""
    rng = np.random.RandomState(seed)
    if black:
        Image.fromarray(np.zeros((H, W), dtype=np.uint8)).save(path)
        return
    img = rng.normal(40, 12, (H, W)).clip(0, 255)
    if panel:
        s = H / 1912.0
        cp, rp = cp_cal * s, rp_cal * s
        x0 = int(vc.INV_CROP[0] * W) + int(0.35 * cp)
        y0 = int(vc.INV_CROP[1] * H) + int(0.30 * rp)
        bw = max(1, int(round(3 * s)))
        img[y0 - bw:y0 + int(4 * rp) + bw, x0 - bw:x0 + int(10 * cp) + bw] = 8
        for i in range(4):
            for j in range(10):
                cx0, cy0 = int(round(x0 + j * cp)), int(round(y0 + i * rp))
                cx1, cy1 = int(round(x0 + (j + 1) * cp)), int(round(y0 + (i + 1) * rp))
                mu, sd = (85, 30) if (i, j) in filled else (4.3, 0.8)
                img[cy0 + bw:cy1, cx0 + bw:cx1] = rng.normal(mu, sd, (cy1 - cy0 - bw, cx1 - cx0 - bw)).clip(0, 255)
                img[cy0:cy0 + bw, cx0:cx1 + bw] = 150      # a border stays brighter than item art,
                img[cy0:cy1 + bw, cx0:cx0 + bw] = 150      # as in the game: a full bag keeps its grid
        yb, xb = int(round(y0 + 4 * rp)), int(round(x0 + 10 * cp))
        img[yb:yb + bw, x0:xb + bw] = 150
        img[y0:yb + bw, xb:xb + bw] = 150
    Image.fromarray(img.astype(np.uint8)).convert("RGB").save(path)


class _Drawn(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="lattice_heights_")
        self.addCleanup(shutil.rmtree, self.d, True)

    def _frame(self, W, H, filled=SOME, **kw):
        p = os.path.join(self.d, "f_%dx%d_%d.png" % (W, H, len(os.listdir(self.d))))
        _draw(p, W, H, filled, **kw)
        return p


class EveryHeightIsRead(_Drawn):

    def test_the_grid_is_found_at_every_height_his_capture_records(self):
        for W, H in HEIGHTS:
            lat = vc.inventory_lattice(self._frame(W, H))
            self.assertTrue(lat.get("ok"), "%dx%d: %s" % (W, H, lat.get("why")))
            self.assertEqual(lat["cells"], 40, "%dx%d is not 10x4: %r" % (W, H, lat))
            s = H / 1912.0
            self.assertAlmostEqual(lat["colPitch"], 86.75 * s, delta=1.5 * s,
                                   msg="%dx%d column pitch %.2f - a harmonic, or the wrong scale" % (W, H, lat["colPitch"]))
            self.assertAlmostEqual(lat["rowPitch"], 85.75 * s, delta=1.5 * s,
                                   msg="%dx%d row pitch %.2f" % (W, H, lat["rowPitch"]))

    def test_the_count_is_the_cells_that_hold_an_item(self):
        for W, H in HEIGHTS:
            for filled in (SOME, set(), {(i, j) for i in range(4) for j in range(10)}):
                p = self._frame(W, H, filled)
                o = vc.inventory_occupancy(p, vc.inventory_lattice(p))
                self.assertTrue(o.get("ok"), "%dx%d: %s" % (W, H, o.get("why")))
                self.assertEqual((o["occupied"], o["free"]), (len(filled), 40 - len(filled)),
                                 "%dx%d with %d drawn full" % (W, H, len(filled)))

    def test_the_calibration_height_is_exactly_what_it_was(self):
        """At 1912 the scale is 1 and every constant is the number it always was - his 2940 reel cannot move."""
        self.assertEqual(vc._ui_scale(1912), 1.0)
        lat = vc.inventory_lattice(self._frame(2940, 1912))
        self.assertAlmostEqual(lat["colPitch"], 86.75, delta=0.6)


class TheRefusalsStillHold(_Drawn):

    def test_a_black_frame_is_refused_at_every_height(self):
        for W, H in HEIGHTS:
            self.assertFalse(vc.inventory_lattice(self._frame(W, H, black=True)).get("ok"), "%dx%d" % (W, H))

    def test_no_panel_is_refused_at_every_height(self):
        for W, H in HEIGHTS:
            self.assertFalse(vc.inventory_lattice(self._frame(W, H, panel=False)).get("ok"), "%dx%d" % (W, H))

    def test_cells_three_pixels_from_square_are_refused_at_1440(self):
        """80.0 calibration pixels tall against 86.75 wide: 6.75 px apart at 1912, refused there - and 3.2 px apart at
        936, which an unscaled 4-pixel tolerance would wave through as square."""
        lat = vc.inventory_lattice(self._frame(1440, 936, rp_cal=80.0))
        self.assertFalse(lat.get("ok"), "a lattice 3 px from square at 1440 was accepted: %r" % lat)
        self.assertIn("not square", str(lat.get("why")))
        self.assertFalse(vc.inventory_lattice(self._frame(2940, 1912, rp_cal=80.0)).get("ok"))


HIST = os.path.join(HERE, "frames", "hist")
REAL = (("reel_s_1789330829280_66296", "f_1789330894463.jpg", 26, 14),   # could never seal (1440x936)
        ("reel_s_1790672854775_82142", "f_1790674010905.jpg", 0, 40),    # could never seal (1440x904), empty bag
        ("reel_s_1784984019250_95276", "f_1784984271825.jpg", 22, 18))   # the reel the constants came from


class HisOwnFrames(unittest.TestCase):

    def test_his_frames_read_where_they_exist(self):
        seen = 0
        for reel, name, occ, free in REAL:
            p = os.path.join(HIST, reel, name)
            if not os.path.isfile(p):
                continue
            seen += 1
            lat = vc.inventory_lattice(p)
            self.assertTrue(lat.get("ok"), "%s/%s: %s" % (reel, name, lat.get("why")))
            o = vc.inventory_occupancy(p, lat)
            self.assertEqual((o["occupied"], o["free"]), (occ, free), "%s/%s" % (reel, name))
        if not seen:
            self.skipTest("his footage is not on this machine - this witness is UNMEASURED here, not passing")


RED_PROOF = [
    {"why": "REG-1648 - every pixel constant at the calibration height again: no 1440 frame is ever cross-checked",
     "file": "vault_corpus.py",
     "find": "    _s = _ui_scale(H)\n",
     "replace": "    _s = 1.0\n",
     "matches": 1},
    {"why": "REG-1648 - the square tolerance stops scaling: a 3 px-off lattice at 1440 passes as square",
     "file": "vault_corpus.py",
     "find": "    if abs(cp - rp) > 4.0 * _s:\n",
     "replace": "    if abs(cp - rp) > 4.0:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
