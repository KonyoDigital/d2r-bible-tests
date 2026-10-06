# -*- coding: utf-8 -*-
"""REG-1712 - ONE UI LAW PLACES EVERY PANEL: D2R SCALES ITS PANELS WITH HEIGHT AND KEEPS THEM CENTRED.

His ask, 2026-10-02: "join them all to have a unified logic ... the architecture and flow the items and reels flow
through", and "simulate on current sessions or reels so we dont fuck up anything working".

MEASURED on his reels (reel_s_1790869575044_77535, 1440x904 - aspect 1.593, while every box was measured on the
2940x1912 film, 1.538): the inventory's real cells run x 872..1282, square at 41.06 px; width-scaling put them at
877..1303 (half a cell off by the last column) and the stash at x 138 where it starts at 158. Only height-scaled and
centred lands both panels on their seams. That miscount kept the vault's pixel cross-check refusing every FULL
inventory ("found 9x4 cells; the D2 inventory is ALWAYS 10x4"), so reels were retired at PRINTER for good.

What this law drives - slot_identity.frame_box / panel_box_for / worn_slot_of, stash_eye.crops_for_aspect and
vault_corpus._calibrated_lattice + inventory_lattice:
  * his film comes back byte-identical (every panel, every doll slot, every locked tally band)
  * at his reel size the boxes sit where the pixels are, and the cells are square at every calibrated aspect
  * his Mac's tally bands stay locked; at 16:9 with no measured route the centred band holds the whole stash (derived,
    not measured: no 16:9 GeForce NOW frame has been looked at)
  * REG-1875 - the ALT's Boosteroid film (800x450, measured 2026-10-07) holds each panel to its own edge: a frame of
    that route gets that law, the box lands on its seams where the centred one misses by two and a half cells, and
    every route nobody measured keeps refusing outside the calibrated band
  * a line fit that SAW the inventory's cell size and miscounted gets the calibrated grid - ONLY when the frame's own
    ridges put their seams on it (_seams_on_the_grid, measured on 158 frames + 150 held out, each looked at); one that
    saw some other grid, none, or seams somewhere else still refuses
RED_PROOF below.
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

import slot_identity as SI  # noqa: E402
import stash_eye as SE  # noqa: E402
import vault_corpus as VC  # noqa: E402

try:
    from PIL import Image as _Img
except Exception:          # pragma: no cover - Pillow is installed in CI and on his Mac
    _Img = None

CW, CH = SI._PANEL_CAL_FRAME


class HisFilmIsUntouched(unittest.TestCase):

    def test_every_panel_and_doll_slot_comes_back_byte_identical(self):
        for name, (fx, fy, fw, fh) in SI.PANELS.items():
            self.assertEqual(SI.panel_box_for(CW, CH, name)[0], (fx * CW, fy * CH, fw * CW, fh * CH), name)
        for name, (fx, fy, fw, fh) in SI.EQUIP_SLOTS.items():
            cx, cy = (fx + fw / 2.0) * CW, (fy + fh / 2.0) * CH
            self.assertEqual(SI.worn_slot_of((cx, cy), CW, CH)[0], name)

    def test_his_macs_tally_bands_stay_locked(self):
        for lay, band in SE._TALLY_CROPS.items():
            for a in (CW / float(CH), 1440 / 904.0, 1.50, 1.60):
                self.assertEqual(SE.crops_for_aspect(lay, a), band, (lay, a))


class HisReelSizeLandsOnTheSeams(unittest.TestCase):

    def test_the_boxes_sit_where_his_pixels_are(self):
        (sx, sy, sw, sh), _ = SI.panel_box_for(1440, 904, "stash")
        (ix, iy, iw, ih), _ = SI.panel_box_for(1440, 904, "inventory")
        self.assertAlmostEqual(sx, 157.8, delta=1.0)            # the stash starts at 158 on his frame
        self.assertAlmostEqual(ix, 871.8, delta=1.0)            # the inventory runs 872..1282
        self.assertAlmostEqual(ix + iw, 1282.4, delta=1.0)

    def test_the_cells_keep_the_films_shape_at_every_calibrated_aspect(self):
        """the LAW, not a pixel count: height-scaling keeps each panel's cell exactly the shape the film measured (the
        stash box was measured 0.12% off square on the film - a ruler's width - and that is what every size keeps)"""
        def ratio(w, h, name, cols, rows):
            (_, _, bw, bh), why = SI.panel_box_for(w, h, name)
            self.assertIsNone(why, "%dx%d" % (w, h))
            return (bw / float(cols)) / (bh / float(rows))
        film = {"inventory": ratio(CW, CH, "inventory", 10, 4), "stash": ratio(CW, CH, "stash", 10, 10)}
        for name, r in film.items():
            self.assertAlmostEqual(r, 1.0, delta=0.005, msg="the film's %s cells are not square" % name)
        for w, h in ((1440, 904), (1470, 956), (1500, 960), (1560, 990), (1390, 950)):
            self.assertAlmostEqual(ratio(w, h, "inventory", 10, 4), film["inventory"], places=9, msg="%dx%d" % (w, h))
            self.assertAlmostEqual(ratio(w, h, "stash", 10, 10), film["stash"], places=9, msg="%dx%d" % (w, h))


class DeansScreenHoldsTheWholeStash(unittest.TestCase):

    def test_a_16_9_band_holds_the_stash_panel(self):
        a = 16 / 9.0
        x0, _, x1, _ = SE.crops_for_aspect("runes", a)
        k = (CW / float(CH)) / a
        fx, _, fw, _ = SI.PANELS["stash"]
        left, right = 0.5 + (fx - 0.5) * k, 0.5 + (fx + fw - 0.5) * k
        self.assertLessEqual(x0, left)
        self.assertGreaterEqual(x1, right, "the 16:9 band cuts the right of the stash off")

    def test_premise_the_left_anchor_cut_it(self):
        """the case above can only pass by the centred law: the left anchor's band ended inside the panel"""
        a = 16 / 9.0
        k = (CW / float(CH)) / a
        fx, _, fw, _ = SI.PANELS["stash"]
        self.assertLess(SE._TALLY_CROPS["runes"][2] * k, 0.5 + (fx + fw - 0.5) * k)


def _inventory_picture(W=1440, H=904, shift=0.0):
    """D2R's inventory as the seam gate sees it: navy cells, a dark gap ON each calibrated seam, item art mid-cell.
    shift moves the whole grid off the calibrated seams (a frame whose lattice is somewhere else)."""
    from PIL import ImageDraw
    (bx, by, bw, bh), _ = SI.panel_box_for(W, H, "inventory")
    pc, pr = bw / 10.0, bh / 4.0
    im = _Img.new("L", (W, H), 25)
    d = ImageDraw.Draw(im)
    for i in range(10):
        for j in range(4):
            x0, y0 = bx + i * pc + shift, by + j * pr + shift
            d.rectangle([x0, y0, x0 + pc, y0 + pr], fill=40)
            d.line([(x0 + pc / 2, y0 + 6), (x0 + pc / 2, y0 + pr - 6)], fill=230, width=3)
            d.line([(x0 + 6, y0 + pr / 2), (x0 + pc - 6, y0 + pr / 2)], fill=230, width=3)
    for i in range(11):
        d.line([(bx + i * pc + shift, by), (bx + i * pc + shift, by + bh)], fill=0, width=2)
    for j in range(5):
        d.line([(bx, by + j * pr + shift), (bx + bw, by + j * pr + shift)], fill=0, width=2)
    return im


def _ridges(im):
    """the ridges the REAL inventory_lattice computes on a picture, captured at the fit it hands them to -> (rcol, rrow)
    | None. No numpy here (CI installs only Pillow): where the lattice cannot read a frame, nothing is captured."""
    d = tempfile.mkdtemp(prefix="ui_law_r_")
    p = os.path.join(d, "f_1.png")
    im.save(p)
    seen, saved = [], VC._fit
    VC._fit = lambda v, *a, **k: seen.append(v)
    try:
        VC.inventory_lattice(p)
    finally:
        VC._fit = saved
    return (seen[0], seen[1]) if len(seen) >= 2 else None


def _evidence(im, W=1440, H=904, lines_shift=0.0):
    """the fit's own answer on a picture: its ridges, and the 9x4 lines his full inventory produced (one column lost)"""
    rid = _ridges(im)
    if rid is None:
        return None
    x0, y0 = int(VC.INV_CROP[0] * W), int(VC.INV_CROP[1] * H)
    (bx, by, bw, bh), _ = SI.panel_box_for(W, H, "inventory")
    pc, pr = bw / 10.0, bh / 4.0
    cols = [bx - x0 + i * pc + lines_shift for i in range(10)]
    rows = [by - y0 + j * pr + lines_shift for j in range(5)]
    return (cols, rows, rid[0], rid[1])


@unittest.skipIf(_Img is None, "Pillow is absent - no frame can be built, UNMEASURED")
class AMiscountedGridGetsTheCalibratedOne(unittest.TestCase):

    def setUp(self):
        self.s = VC._ui_scale(904)
        if _ridges(_Img.new("L", (1440, 904), 60)) is None:
            self.skipTest("the lattice cannot read a frame on this machine (numpy absent - CI installs only Pillow): "
                          "the seam gate is UNMEASURED here, never passed")

    def test_a_fit_that_measured_the_inventory_cells_is_given_the_calibrated_grid(self):
        fit = _evidence(_inventory_picture())
        got = VC._calibrated_lattice(1440, 904, 44.35, 40.85, self.s, 9, 4, fit=fit)   # his frame f_1790874262534
        self.assertIsNotNone(got)
        self.assertEqual((len(got["cols"]) - 1, len(got["rows"]) - 1), (10, 4))
        self.assertEqual(got["source"], "calibrated")

    def test_the_pitch_is_no_evidence_without_seams_on_the_grid(self):
        """REG-1712 second cut: the first admitted a webcam, a fire and the Join Game screen as full inventories -
        the pitch search is a narrow band around this very cell size, so every frame's best pitch lands near it"""
        for name, fit in (("no evidence at all", None),
                          ("a lattice half a cell off the seams", _evidence(_inventory_picture(shift=20.5))),
                          ("a flat frame", _evidence(_Img.new("L", (1440, 904), 60))),
                          ("the fit's lines between the seams", _evidence(_inventory_picture(), lines_shift=20.5))):
            self.assertIsNone(VC._calibrated_lattice(1440, 904, 44.35, 40.85, self.s, 9, 4, fit=fit),
                              "%s was handed the calibrated grid on its pitch alone" % name)

    def test_some_other_grid_still_refuses(self):
        fit = _evidence(_inventory_picture())
        self.assertIsNone(VC._calibrated_lattice(1440, 904, 11.71, 11.96, self.s, 37, 3, fit=fit))  # a stash-tab texture
        self.assertIsNone(VC._calibrated_lattice(1920, 1080, 44.35, 40.85, VC._ui_scale(1080), 9, 4, fit=fit),
                          "a frame of no calibrated aspect was handed a grid nobody measured")

    def _lattice_with_his_fit(self, im):
        """the REAL inventory_lattice on a picture, its fit stubbed to the 9x4 his full inventory produced"""
        d = tempfile.mkdtemp(prefix="ui_law_")
        p = os.path.join(d, "f_1.png")
        im.save(p)
        cols, rows, _, _ = _evidence(_inventory_picture())
        fits = iter([(5.0, 44.35, 0.0, cols), (5.0, 40.85, 0.0, rows)])
        saved = VC._fit
        VC._fit = lambda *a, **k: next(fits)
        try:
            return VC.inventory_lattice(p)
        finally:
            VC._fit = saved

    def test_the_lattice_itself_takes_it(self):
        got = self._lattice_with_his_fit(_inventory_picture())
        self.assertTrue(got.get("ok"), got)
        self.assertEqual(got.get("source"), "calibrated")

    def test_the_lattice_refuses_a_frame_whose_seams_are_elsewhere(self):
        got = self._lattice_with_his_fit(_inventory_picture(shift=20.5))
        self.assertFalse(got.get("ok"), got)


#: REG-1875 - his ALT's Boosteroid film, 800x450 (a 1920x1080 window), measured 2026-10-07 by a lattice fit on three
#: shared/personal stash frames from two sessions and five inventory frames (seams dark against cell interiors). The
#: jpegs are not on CI; the numbers are, and the frames below are drawn from them.
ALT_W, ALT_H = 800, 450
ALT_STASH_X0, ALT_STASH_Y0, ALT_PITCH = 68.5, 90.0, 20.43
ALT_INV_X0 = 529.25


def _lattice(W, H, x0, y0, pitch, cols, rows, base=None):
    """dark seams on a measured lattice, bright cell interiors - the picture a contrast fit reads a grid from"""
    from PIL import ImageDraw
    im = base or _Img.new("L", (W, H), 60)
    d = ImageDraw.Draw(im)
    d.rectangle([x0, y0, x0 + cols * pitch, y0 + rows * pitch], fill=120)
    for i in range(cols + 1):
        d.line([(x0 + i * pitch, y0), (x0 + i * pitch, y0 + rows * pitch)], fill=15, width=2)
    for j in range(rows + 1):
        d.line([(x0, y0 + j * pitch), (x0 + cols * pitch, y0 + j * pitch)], fill=15, width=2)
    return im


def _contrast(im, box, cols, rows):
    """interior minus seam luminance at a box's predicted lattice: high on the grid, near 0 off it"""
    bx, by, bw, bh = box
    pc, pr = bw / float(cols), bh / float(rows)
    px = im.load()
    W, H = im.size
    def at(x, y):
        return px[min(W - 1, max(0, int(round(x)))), min(H - 1, max(0, int(round(y))))]
    seam = [at(bx + i * pc, by + (j + 0.5) * pr) for i in range(cols + 1) for j in range(rows)]
    mid = [at(bx + (i + 0.5) * pc, by + (j + 0.5) * pr) for i in range(cols) for j in range(rows)]
    return sum(mid) / float(len(mid)) - sum(seam) / float(len(seam))


@unittest.skipIf(_Img is None, "Pillow is absent - no frame can be built, UNMEASURED")
class TheALTsFilmHoldsEachPanelToItsEdge(unittest.TestCase):

    def test_the_boosteroid_route_lands_on_the_alts_measured_seams(self):
        (sx, sy, sw, sh), why = SI.panel_box_for(ALT_W, ALT_H, "stash", route="boosteroid")
        self.assertIsNone(why)
        self.assertAlmostEqual(sx, ALT_STASH_X0, delta=0.5)     # the grid's measured gap, not the edge law's 66.1
        self.assertAlmostEqual(sy, ALT_STASH_Y0, delta=1.0)
        self.assertAlmostEqual(sw / 10.0, ALT_PITCH, delta=0.1)
        (ix, _iy, iw, _ih), why = SI.panel_box_for(ALT_W, ALT_H, "inventory", route="boosteroid")
        self.assertIsNone(why)
        self.assertAlmostEqual(ix, ALT_INV_X0, delta=1.0)
        self.assertAlmostEqual(iw / 10.0, ALT_PITCH, delta=0.1)
        # the edge law alone (what the doll and the crop bands ride) lands both grids within a ruler's width of the fit
        self.assertAlmostEqual(SI.frame_box(SI.PANELS["inventory"], ALT_W, ALT_H, route="boosteroid")[0],
                               ALT_INV_X0, delta=1.0)
        self.assertAlmostEqual(SI.frame_box(SI.PANELS["stash"], ALT_W, ALT_H, route="boosteroid")[0],
                               ALT_STASH_X0, delta=3.0)

    def test_premise_the_centred_law_misses_the_alts_film_by_two_cells(self):
        sx = SI.frame_box(SI.PANELS["stash"], ALT_W, ALT_H)[0]
        ix = SI.frame_box(SI.PANELS["inventory"], ALT_W, ALT_H)[0]
        self.assertGreater(sx - ALT_STASH_X0, 2 * ALT_PITCH)
        self.assertGreater(ALT_INV_X0 - ix, 2 * ALT_PITCH)

    def test_the_box_it_returns_sits_on_a_lattice_drawn_where_the_alt_measured_it(self):
        im = _lattice(ALT_W, ALT_H, ALT_STASH_X0, ALT_STASH_Y0, ALT_PITCH, 10, 10)
        edge = _contrast(im, SI.panel_box_for(ALT_W, ALT_H, "stash", route="boosteroid")[0], 10, 10)
        centred = _contrast(im, SI.frame_box(SI.PANELS["stash"], ALT_W, ALT_H), 10, 10)
        self.assertGreater(edge, 60, "the boosteroid box is not on the ALT's seams (contrast %.1f)" % edge)
        self.assertLess(centred, edge / 3.0, "the centred box reads the lattice as well (%.1f vs %.1f)" % (centred, edge))

    def test_a_route_nobody_measured_still_refuses_outside_the_band(self):
        for route in (None, "geforce-now", "native", "unknown", "BOOSTEROID"):
            box, why = SI.panel_box_for(ALT_W, ALT_H, "stash", route=route)
            self.assertIsNone(box, route)
            self.assertIn("nothing here has been measured", why)
        self.assertIsNone(SI.panel_box_for(800, 400, "stash", route="boosteroid")[0],
                          "the ALT's law was carried to an aspect it was not measured at (2:1, its own app)")
        self.assertEqual(SI.panel_box_for(1440, 904, "stash", route="boosteroid"), SI.panel_box_for(1440, 904, "stash"),
                         "a measured route moved his Mac's calibrated band")

    def test_the_alts_stamped_film_is_cropped_around_the_whole_stash(self):
        a = ALT_W / float(ALT_H)
        x0, _y0, x1, _y1 = SE.crops_for_aspect("runes", a, route="boosteroid")
        self.assertEqual(SE.last_crop_decision()["branch"], "derived-edge")
        self.assertLessEqual(x0 * ALT_W, ALT_STASH_X0)
        self.assertGreaterEqual(x1 * ALT_W, ALT_STASH_X0 + 10 * ALT_PITCH,
                                "the band cuts the right of the ALT's stash off")
        c0, _, _, _ = SE.crops_for_aspect("runes", a)
        self.assertGreater(c0 * ALT_W, ALT_STASH_X0 + ALT_PITCH, "premise: the centred band starts inside the stash")
        d = tempfile.mkdtemp(prefix="ui_law_alt_")
        self.addCleanup(shutil.rmtree, d, True)
        src, dst = os.path.join(d, "f_1500000000001.jpg"), os.path.join(d, "crop.jpg")
        _lattice(ALT_W, ALT_H, ALT_STASH_X0, ALT_STASH_Y0, ALT_PITCH, 10, 10).convert("RGB").save(src)
        got = SE.prep_stash_grid(src, dst, "runes", stamp={"route": "boosteroid", "w": 1920, "h": 1080})
        self.assertEqual(got, dst)
        self.assertEqual(SE.last_crop_decision()["branch"], "derived-edge",
                         "the reel's stamped route did not reach the crop")

    def test_a_stamp_of_some_other_window_does_not_move_the_band(self):
        self.assertEqual(SE._stamp_route(ALT_W, ALT_H, {"route": "boosteroid", "w": 1920, "h": 1080}), "boosteroid")
        self.assertIsNone(SE._stamp_route(1600, 900, {"route": "boosteroid", "w": 2940, "h": 1912}),
                          "a stamp naming a 1.538 window moved the band of a 16:9 frame")
        for bad in (None, {"route": "boosteroid"}, {"route": "boosteroid", "w": True, "h": 1080},
                    {"route": "", "w": 1920, "h": 1080}):
            self.assertIsNone(SE._stamp_route(ALT_W, ALT_H, bad), bad)

    def test_the_live_vault_read_crops_by_the_route_it_filmed_through(self):
        """the agent's live tally read has no seam to drive from here, so its one call is pinned, code only"""
        with open(os.path.join(HERE, "tv_diablo.py"), encoding="utf-8") as fh:
            code = "\n".join(l.split("#", 1)[0] for l in fh.read().split("\n"))
        call = "_se.crops_for_aspect(_layout, float(_W) / float(_H), route=_route)"
        self.assertEqual(code.count(call), 1, "the live vault crop does not pass the route it filmed through")
        self.assertEqual(code.count("_route = (_capture_for_seal() or {}).get(\"route\")"), 1)


RED_PROOF = [
    {
        "why": "REG-1875 - the ALT's route stops counting as measured: its 16:9 boxes go back to the centred law",
        "file": "slot_identity.py",
        "find": "    return anchor == \"edge\" and a > 0 and abs(a - a0) / a0 <= _ANCHOR_ASPECT_TOL\n",
        "replace": "    return False\n",
        "matches": 1,
    },
    {
        "why": "REG-1875 - a right panel is held to the LEFT edge on the ALT's film",
        "file": "slot_identity.py",
        "find": "            x = fw - (cw - x_cal) * s                           # a right panel keeps its gap to the right edge\n",
        "replace": "            x = x_cal * s\n",
        "matches": 1,
    },
    {
        "why": "REG-1875 - the reel's stamped route never reaches the stash crop",
        "file": "stash_eye.py",
        "find": "        derived = crops_for_aspect(layout, aspect, route=_stamp_route(w, h, stamp))   # REG-1875\n",
        "replace": "        derived = crops_for_aspect(layout, aspect, route=None)\n",
        "matches": 1,
    },
    {
        "why": "REG-1875 - the stash's measured gap is dropped for the edge law's, 2.4 px off the ALT's seams",
        "file": "slot_identity.py",
        "find": "        box = ((gap * fh) if left else (fw - gap * fh - bw), by, bw, bh)   # the grid's own measured gap\n",
        "replace": "        pass\n",
        "matches": 1,
    },
    {
        "why": "REG-1875 - a stamp naming some other window moves this frame's band",
        "file": "stash_eye.py",
        "find": "    if abs((w / float(h)) - client) / client > 0.02:\n        return None\n    r = stamp.get(\"route\")\n",
        "replace": "    r = stamp.get(\"route\")\n",
        "matches": 1,
    },
    {
        "why": "REG-1875 - the live vault read crops every route by the centred law again",
        "file": "tv_diablo.py",
        "find": "            _band = (_se.crops_for_aspect(_layout, float(_W) / float(_H), route=_route)\n",
        "replace": "            _band = (_se.crops_for_aspect(_layout, float(_W) / float(_H))\n",
        "matches": 1,
    },
    {
        "why": "REG-1875 - the ALT's law is carried to every aspect, its own 2:1 app window included",
        "file": "slot_identity.py",
        "find": "    return anchor == \"edge\" and a > 0 and abs(a - a0) / a0 <= _ANCHOR_ASPECT_TOL\n",
        "replace": "    return anchor == \"edge\" and a > 0\n",
        "matches": 1,
    },
    {
        "why": "REG-1712 - the panel box scales x and width by the frame's WIDTH again: half a cell off on his reels",
        "file": "slot_identity.py",
        "find": "    return (fw / 2.0 + (fx * cw - cw / 2.0) * s, fy * fh, fwf * cw * s, fhf * fh)\n",
        "replace": "    return (fx * fw, fy * fh, fwf * fw, fhf * fh)\n",
        "matches": 1,
    },
    {
        "why": "REG-1712 - Dean's 16:9 band goes back to the left anchor and cuts a third of his stash off",
        "file": "stash_eye.py",
        "find": "    x0, y0, x1, y1 = _si.frame_band(frac, aspect, route=route)\n",
        "replace": "    x0, y0, x1, y1 = frac[0] * _CROP_CAL_ASPECT / aspect, frac[1], frac[2] * _CROP_CAL_ASPECT / aspect, frac[3]\n",
        "matches": 1,
    },
    {
        "why": "REG-1712 - the calibrated grid is handed to a fit that measured some other grid",
        "file": "vault_corpus.py",
        "find": "    if not (abs(cp - pc) <= tol or abs(rp - pr) <= tol):\n        return None\n",
        "replace": "    if False:\n        return None\n",
        "matches": 1, "needs": "numpy",
    },
    {
        "why": "REG-1712 - the calibrated grid is taken on its pitch alone: a webcam or a fire becomes a full inventory",
        "file": "vault_corpus.py",
        "find": "    if not _ok:\n        return None\n",
        "replace": "    if False:\n        return None\n",
        "matches": 1, "needs": "numpy",
    },
    {
        "why": "REG-1712 - the lattice refuses a miscounted full inventory again instead of taking the calibrated grid",
        "file": "vault_corpus.py",
        "find": "        _cal = _calibrated_lattice(W, H, cp, rp, _s, nc, nr, fit=(cols, rows, _rcol, _rrow))\n",
        "replace": "        _cal = None\n",
        "matches": 1, "needs": "numpy",
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
