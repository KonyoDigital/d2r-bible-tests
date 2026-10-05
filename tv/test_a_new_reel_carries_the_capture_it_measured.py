# -*- coding: utf-8 -*-
"""A new reel records the window it was filmed from. An old reel does not grow a route.

Board #155. The pick already knows native / geforce-now / boosteroid, and the Windows
capture half already measured the client size and the DPI. Neither of those reached the
reel index, so a later crop had to guess from the jpeg. The seal copies only what was
measured. A narrow film is cropped with the one UI law only when that record says the
jpeg is the same window. No record, no crop.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import capture_stamp as CS  # noqa: E402
import stash_eye as SE  # noqa: E402
import tv_diablo as TVD  # noqa: E402

RED_PROOF = [
    {
        "why": "the seal copies the measured capture onto the index; deleting that copy leaves the route off every new reel",
        "file": "tv_diablo.py",
        "find": "                    _ixdoc[\"capture\"] = _cap\n",
        "replace": "                    pass\n",
        "matches": 1,
    },
]


def _jpeg(w, h):
    from PIL import Image
    d = tempfile.mkdtemp(prefix="capstamp_")
    p = os.path.join(d, "f.jpg")
    Image.new("RGB", (w, h), (30, 24, 18)).save(p, "JPEG", quality=90)
    return d, p


class TheStampCopiesOnlyWhatWasMeasured(unittest.TestCase):

    def test_a_real_pin_is_kept_and_a_guess_is_not(self):
        got = CS.from_measured({
            "route": "boosteroid", "windowLabel": "  Boosteroid  ",
            "w": 1920, "h": 1080, "os": "windows",
            "dpi": 144, "dpiMeasured": True,
        })
        self.assertEqual(got["route"], "boosteroid")
        self.assertEqual(got["windowLabel"], "Boosteroid")
        self.assertEqual((got["w"], got["h"], got["os"], got["dpi"]), (1920, 1080, "windows", 144))

    def test_a_fallback_dpi_and_a_route_outside_the_four_names_are_dropped(self):
        got = CS.from_measured({
            "route": "phone", "w": 800, "h": None, "os": "android",
            "dpi": 96, "dpiMeasured": False,
        })
        self.assertNotIn("route", got)
        self.assertNotIn("w", got)
        self.assertNotIn("h", got)
        self.assertNotIn("dpi", got)
        self.assertNotIn("os", got)

    def test_unknown_is_a_measured_failure_and_stays(self):
        self.assertEqual(CS.from_measured({"route": "unknown", "os": "mac"})["route"], "unknown")

    def test_an_old_index_has_no_route(self):
        got = CS.from_index({"sessionId": "s_1", "n": 1, "frames": [], "route": "native"})
        self.assertEqual(got, {k: None for k in CS.KEYS})

    def test_a_recorded_stamp_reads_back_and_a_strange_route_does_not(self):
        got = CS.from_index({"capture": {
            "route": "native", "windowLabel": "D2R", "w": 1440, "h": 900,
            "os": "mac", "dpi": 144,
        }})
        self.assertEqual(got["route"], "native")
        self.assertEqual(got["dpi"], 144)
        strange = CS.from_index({"capture": {"route": "local", "w": 10}})
        self.assertIsNone(strange["route"])
        self.assertIsNone(strange["w"])


class TheSealAsksThePinAndTheCaptureHalf(unittest.TestCase):

    def setUp(self):
        self._pr = TVD._PICK_ROUTE
        self._frames = TVD.FRAMES
        self.d = tempfile.mkdtemp(prefix="capseal_")
        TVD.FRAMES = self.d
        TVD._PICK_ROUTE = None

    def tearDown(self):
        TVD._PICK_ROUTE = self._pr
        TVD.FRAMES = self._frames
        shutil.rmtree(self.d, True)

    def test_the_finder_records_the_label_and_the_client_size_with_the_route(self):
        TVD._note_pick_route(
            [{"owner": "D2R.exe", "title": "Diablo II: Resurrected", "w": 1920, "h": 1080, "wid": 7}],
            (1, 1, 7, "D2R.exe · Diablo II: Resurrected"))
        rec = TVD._PICK_ROUTE
        self.assertEqual(rec["route"], "native")
        self.assertEqual(rec["windowLabel"], "D2R.exe · Diablo II: Resurrected")
        self.assertEqual((rec["w"], rec["h"]), (1920, 1080))

    def test_the_capture_half_wins_when_it_named_the_window(self):
        TVD._PICK_ROUTE = {"route": "native", "w": 100, "h": 100, "windowLabel": "stale"}
        with open(os.path.join(self.d, "cap_target.json"), "w", encoding="utf-8") as fh:
            json.dump({"mode": "window", "route": "boosteroid", "windowLabel": "Boosteroid",
                       "w": 1920, "h": 1080, "dpi": 120, "dpiMeasured": True}, fh)
        got = TVD._capture_for_seal()
        self.assertEqual(got["route"], "boosteroid")
        self.assertEqual((got["w"], got["h"]), (1920, 1080))
        self.assertEqual(got["dpi"], 120)
        self.assertEqual(got["windowLabel"], "Boosteroid")
        self.assertIn(got["os"], CS.OSES)

    def test_a_waiting_file_does_not_erase_the_pin_and_a_bare_dpi_is_not_copied(self):
        TVD._PICK_ROUTE = {"route": "geforce-now", "w": 1600, "h": 900, "windowLabel": "GeForce NOW"}
        with open(os.path.join(self.d, "cap_target.json"), "w", encoding="utf-8") as fh:
            json.dump({"mode": "waiting", "route": "native", "w": 800, "h": 450, "dpi": 96}, fh)
        got = TVD._capture_for_seal()
        self.assertEqual(got["route"], "geforce-now")
        self.assertEqual((got["w"], got["h"]), (1600, 900))
        self.assertNotIn("dpi", got)

    def test_local_from_the_capture_half_is_native(self):
        with open(os.path.join(self.d, "cap_target.json"), "w", encoding="utf-8") as fh:
            json.dump({"mode": "window", "route": "local", "w": 800, "h": 450}, fh)
        self.assertEqual(TVD._capture_for_seal()["route"], "native")

    def test_a_reel_that_recorded_nothing_does_not_inherit_the_live_pin(self):
        TVD._PICK_ROUTE = {"route": "boosteroid", "w": 1920, "h": 1080, "windowLabel": "Boosteroid"}
        reel = os.path.join(self.d, "reel_s_1")
        os.makedirs(reel)
        with open(os.path.join(reel, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"sessionId": "s_1", "n": 0, "frames": []}, fh)
        frame = os.path.join(reel, "f_1.jpg")
        open(frame, "wb").close()
        self.assertIsNone(CS.beside_frame(frame))
        with open(os.path.join(reel, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"capture": {"route": "native", "w": 1440, "h": 900, "os": "mac"}}, fh)
        self.assertEqual(CS.beside_frame(frame)["route"], "native")
        self.assertIsNone(CS.beside_frame(os.path.join(self.d, "f_loose.jpg")))

    def test_the_seal_copies_the_stamp_onto_the_index(self):
        with open(os.path.join(HERE, "tv_diablo.py"), encoding="utf-8") as fh:
            src = fh.read()
        line = "                    _ixdoc[\"capture\"] = _cap\n"
        self.assertEqual(src.count(line), 1)
        i = src.find(line)
        self.assertLess(i, src.find("_reel_index_write(_ixdoc)", i))


class ANarrowFilmIsCroppedOnlyFromItsStamp(unittest.TestCase):

    def _grid(self, w, h, stamp):
        d, p = _jpeg(w, h)
        self.addCleanup(shutil.rmtree, d, True)
        dest = os.path.join(d, "out.jpg")
        return SE.prep_stash_grid(p, dest, stamp=stamp)

    def test_a_wide_frame_keeps_the_band_with_or_without_a_stamp(self):
        self.assertTrue(self._grid(1600, 900, None))
        self.assertEqual(SE._LAST_CROP["branch"], "derived")
        self.assertTrue(self._grid(1600, 900, {"route": "boosteroid", "w": 2940, "h": 1912}))
        self.assertEqual(SE._LAST_CROP["branch"], "derived",
                         "the stamp named a Mac window and the frame is 16:9; the pixels decide")

    def test_a_narrow_frame_needs_a_window_of_the_same_aspect(self):
        self.assertIsNone(self._grid(800, 450, None))
        self.assertIsNone(self._grid(800, 450, {"route": "boosteroid", "w": 2940, "h": 1912}))
        self.assertTrue(self._grid(800, 450, {"route": "boosteroid", "w": 1920, "h": 1080}))
        self.assertEqual(SE._LAST_CROP["branch"], "derived")


class TheCaptureHalfDoesNotInventADpi(unittest.TestCase):

    def test_an_unmeasured_dpi_stays_zero_and_the_pin_is_what_gets_written(self):
        with open(os.path.join(HERE, "capture_win.ps1"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count("int dpi = 0;"), 1)
        self.assertEqual(src.count("if (dpi < 72) dpi = 0;"), 1)
        call = ("Write-CapTarget 'window' (\"{0} [{1}] - {2} via {3}\" -f "
                "$best.Proc, $best.Route, $best.Title, $how) $best")
        self.assertEqual(src.count(call), 1)
        self.assertNotIn("dpi = 96", src)
