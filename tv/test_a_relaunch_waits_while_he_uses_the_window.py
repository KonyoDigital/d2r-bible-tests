# -*- coding: utf-8 -*-
"""REG-2010 - A WAITING BUILD NEVER REPLACES THE WINDOW UNDER HIS HAND. #254, GrokBot ticks 400, 401 and 404.

GrokBot, 2026-10-07: the console replaced itself three times with an overlay up - the Shelf at 18:21, the Heart
mid-census at 18:47, the Heart again at 20:18 - each a white flash, a black window and ~10 s of nothing, minutes after
a version landed. The drift relaunch waited for WORK (a sweep reading, a reel rolling) and never for the person at the
window. Now the page reports how long ago it was last touched (pointer, key, wheel) in its 5 s beat, and once nothing is
in flight the relaunch still waits until the window has been still for 60 s - never for an unknown age, never for a
hidden window, and never past 20 minutes of continuous use, so a build always lands. His own ⟲ relaunch is not this
path (it asks nothing_in_flight directly), so pressing it is never held.

Drives the REAL relaunch_in_use, ui_beat_record + ui_input_age_s, and drift_may_relaunch with every other interlock
stubbed clear; anchors the page's listener and beat field (code only, once each).
"""
import io
import os
import re
import sys
import time
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

os.environ["TVD_NO_BEACON"] = "1"
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import control_app as CA  # noqa: E402


class ARelaunchWaitsWhileHeUsesTheWindow(unittest.TestCase):

    def setUp(self):
        keep = dict(CA._IN_USE_HOLD)
        self.addCleanup(lambda: (CA._IN_USE_HOLD.clear(), CA._IN_USE_HOLD.update(keep)))
        CA._IN_USE_HOLD["since"] = None

    def test_the_rule(self):
        hold, why = CA.relaunch_in_use(5.0, False, 0.0)
        self.assertTrue(hold, "a window touched 5 s ago was replaced under his hand (REG-2010)")
        self.assertIn("you are using the window", why)
        self.assertFalse(CA.relaunch_in_use(90.0, False, 0.0)[0], "a window still for 90 s kept a build waiting")
        self.assertFalse(CA.relaunch_in_use(5.0, True, 0.0)[0], "a hidden window held the build")
        self.assertFalse(CA.relaunch_in_use(None, False, 0.0)[0], "an UNKNOWN input age held the build for ever")
        hold, why = CA.relaunch_in_use(5.0, False, CA.RELAUNCH_IN_USE_MAX_S + 1)
        self.assertFalse(hold, "a window in use past the ceiling starved the build")
        self.assertIn("lands now", why)

    def test_the_beat_carries_the_age_and_it_keeps_ageing_between_beats(self):
        keep = dict(CA._UI_BEAT)
        self.addCleanup(lambda: (CA._UI_BEAT.clear(), CA._UI_BEAT.update(keep)))
        CA.ui_beat_record({"inputAgeS": 3.0, "hidden": False})
        age = CA.ui_input_age_s(now=CA._UI_BEAT["t"] + 4.0)
        self.assertAlmostEqual(age, 7.0, places=3, msg="the input age did not carry the beat's own age")
        self.assertIsNone(CA.ui_input_age_s(now=CA._UI_BEAT["t"] + 31.0), "a silent page read as a window in use")
        CA.ui_beat_record({"hidden": False})
        self.assertIsNone(CA.ui_input_age_s(), "a page that did not say read as idle or in use rather than UNKNOWN")

    def _decide(self, input_age):
        keep = dict(CA._UI_BEAT)
        self.addCleanup(lambda: (CA._UI_BEAT.clear(), CA._UI_BEAT.update(keep)))
        CA.ui_beat_record({"hidden": False} if input_age is None else {"inputAgeS": input_age, "hidden": False})
        detail = {}
        with mock.patch.object(CA, "_env_tristate", lambda k: True), \
                mock.patch.object(CA, "board_identity_drift", lambda: {"state": "ok"}), \
                mock.patch.object(CA, "_sweep_lock_path", lambda: "/nonexistent/.sweep.lock"), \
                mock.patch.object(CA, "_tree_is_mid_edit", lambda: (False, "")), \
                mock.patch.object(CA, "nothing_in_flight", lambda parts=None: (True, "nothing in flight")):
            ok, why = CA.drift_may_relaunch(detail=detail)
        return ok, why, detail.get("blocker")

    def test_the_drift_relaunch_asks_his_hands_last(self):
        ok, why, blocker = self._decide(2.0)
        self.assertFalse(ok, "with nothing in flight the build replaced a window he touched 2 s ago (REG-2010)")
        self.assertEqual(blocker, "in-use")
        ok, _w, blocker = self._decide(None)
        self.assertTrue(ok, "a page that never reported an input age kept every build out")

    def test_the_page_reports_its_last_touch(self):
        with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
            ui = fh.read()
        code = re.sub(r"/\*.{0,4000}?\*/", "", ui, flags=re.S)
        self.assertEqual(code.count("['pointerdown', 'pointermove', 'keydown', 'wheel'].forEach"), 1,
                         "the page stopped listening for his touch")
        self.assertEqual(code.count("inputAgeS: (window.__lastInputTs ?"), 1, "the beat no longer carries the input age")


RED_PROOF = [
    {"why": "REG-2010 - the drift relaunch stops asking his hands: the window is replaced mid-use again",
     "file": "tv/control_app.py",
     "find": "        if _hold:\n            _detail[\"blocker\"] = \"in-use\"\n            return False, _iu\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2010 - a window touched seconds ago reads as still",
     "file": "tv/control_app.py",
     "find": "    if hidden or input_age_s is None or float(input_age_s) >= still:\n",
     "replace": "    if True:\n",
     "matches": 1},
    {"why": "REG-2010 - the ceiling is gone: a window he never leaves never gets its update",
     "file": "tv/control_app.py",
     "find": "    if float(held_for_s or 0.0) >= cap:\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-2010 - the beat's own age is not added, so a quiet window never ages between beats",
     "file": "tv/control_app.py",
     "find": "    return float(a) + gap\n",
     "replace": "    return float(a)\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
