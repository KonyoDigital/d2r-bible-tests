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
  · His own frames, where they exist (his Mac): his 1440-wide panel frames mostly read - found, never named, since a
    reel id in a test pins that footage for ever. Absent footage or absent numpy SKIPS, and a skip is not a pass.
⚠ The cell inset is scaled too; measured, it changes 2 of 268 real frames, both a tooltip-dimmed corner of the
2x2 cube, where the scaled answer (occupied) is the true one. No sabotage claims it - nothing here could tell.
RED_PROOF below. [[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]
"""
import io
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

import importlib.util  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import vault_corpus as vc  # noqa: E402

# the lattice needs numpy and CI installs only pillow: ASKED, never imported here (a third-party import in a suite
# takes the CI runner down - test_control's TestNoSuiteImportsSomethingCIDoesNotHave)
np = importlib.util.find_spec("numpy")
_NO_NUMPY = "numpy is not on this machine - the lattice cannot run, so this law is UNMEASURED here, not passing"

HEIGHTS = ((2940, 1912), (1440, 936), (1440, 904))
SOME = {(0, 0), (0, 1), (1, 0), (1, 1), (0, 4), (2, 7), (3, 9), (3, 2), (1, 5), (2, 2)}


def _draw(path, W, H, filled, cp_cal=86.75, rp_cal=85.75, panel=True, black=False, seed=7):
    """A D2R-like inventory: near-black empty cells (4), noisy item cells, borders brighter than item art (as in the
    game, so a full bag keeps its grid), placed in the crop the way his game places it, every length in this frame's
    pixels (x H/1912). PIL only - deterministic, and nothing CI lacks."""
    if black:
        Image.new("L", (W, H), 0).save(path)
        return
    img = Image.effect_noise((W, H), 12).point(lambda v: max(0, v - 88))      # the world behind the panel, mean ~40
    if panel:
        d = ImageDraw.Draw(img)
        s = H / 1912.0
        cp, rp = cp_cal * s, rp_cal * s
        x0 = int(vc.INV_CROP[0] * W) + int(0.35 * cp)
        y0 = int(vc.INV_CROP[1] * H) + int(0.30 * rp)
        bw = max(1, int(round(3 * s)))
        d.rectangle([x0 - bw, y0 - bw, x0 + int(10 * cp) + bw, y0 + int(4 * rp) + bw], fill=8)
        for i in range(4):
            for j in range(10):
                cx0, cy0 = int(round(x0 + j * cp)), int(round(y0 + i * rp))
                cx1, cy1 = int(round(x0 + (j + 1) * cp)), int(round(y0 + (i + 1) * rp))
                if (i, j) in filled:
                    cell = Image.effect_noise((cx1 - cx0 - bw, cy1 - cy0 - bw), 30).point(lambda v: max(0, v - 43))
                    img.paste(cell, (cx0 + bw, cy0 + bw))
                else:
                    d.rectangle([cx0 + bw, cy0 + bw, cx1 - 1, cy1 - 1], fill=4)
                d.rectangle([cx0, cy0, cx1 + bw - 1, cy0 + bw - 1], fill=150)
                d.rectangle([cx0, cy0, cx0 + bw - 1, cy1 + bw - 1], fill=150)
        yb, xb = int(round(y0 + 4 * rp)), int(round(x0 + 10 * cp))
        d.rectangle([x0, yb, xb + bw - 1, yb + bw - 1], fill=150)
        d.rectangle([xb, y0, xb + bw - 1, yb + bw - 1], fill=150)
    img.convert("RGB").save(path)


@unittest.skipIf(np is None, _NO_NUMPY)
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


@unittest.skipIf(np is None, _NO_NUMPY)
class HisOwnFrames(unittest.TestCase):
    """Where his footage is on this machine: the panel frames of every 1440-wide reel mostly read 10x4.

    ⚠ NO REEL IS NAMED HERE. A reel id in test code holds that footage as a fixture for ever
    (test_a_gate_may_not_pin_his_footage, REG-1027) - so this witness finds its frames, it never pins them.
    MEASURED 2026-10-01: 268 of 273 at 1440 wide; the 5 refused were 12x4 / 11x4 / 9x4 / not-square - the
    refusals doing their job."""

    def test_his_1440_frames_read_where_they_exist(self):
        import json
        try:
            with io.open(os.path.join(HERE, "retro_triage.json"), encoding="utf-8") as fh:
                store = json.load(fh)
        except Exception:
            store = None
        store = (store or {}).get("reels", store or {})
        seen = ok = 0
        for reel in sorted(os.listdir(HIST)) if os.path.isdir(HIST) else []:
            for name in sorted(((store.get(reel) or {}).get("panelFrames") or {}))[:6]:
                p = os.path.join(HIST, reel, name)
                if not os.path.isfile(p):
                    continue
                with Image.open(p) as im:
                    if im.size[0] != 1440:
                        continue
                seen += 1
                ok += 1 if vc.inventory_lattice(p).get("ok") else 0
        if not seen:
            self.skipTest("no 1440-wide panel frame of his on this machine - this witness is UNMEASURED here")
        self.assertGreaterEqual(ok, int(seen * 0.9), "only %d of %d of his 1440-wide panel frames read" % (ok, seen))


RED_PROOF = [
    {"why": "REG-1648 - every pixel constant at the calibration height again: no 1440 frame is ever cross-checked",
     "file": "vault_corpus.py",
     "find": "    _s = _ui_scale(H)\n",
     "replace": "    _s = 1.0\n",
     "matches": 1, "needs": "numpy"},
    {"why": "REG-1648 - the square tolerance stops scaling: a 3 px-off lattice at 1440 passes as square",
     "file": "vault_corpus.py",
     "find": "    if abs(cp - rp) > 4.0 * _s:\n",
     "replace": "    if abs(cp - rp) > 4.0:\n",
     "matches": 1, "needs": "numpy"},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
