# -*- coding: utf-8 -*-
"""#214 F10 (REG-2041, finding 17) - A MINI REEL IS STAMPED focusChosen ONLY WHEN HE CHOSE A FOCUS.

The retro sweep trusts a declared focus in place of a paid classify (vault_retro._declared_surface), so a declaration he
never made labels town, a fight or a Chronicle page as a stash panel. v1783 made start_agent append --mini-focus only
for a chosen focus - and the guard never fired: mini_start first ran _mini_focus(), which turns "nothing chosen" into
the default "stash", and the console page always posted its pre-selected "stash". Simulated 2026-10-07 at v3600:
every Mini spawn carried --mini-focus, so tv_diablo.MINI_FOCUS_CHOSEN was always true. Now the page sends focusChosen
(true only after he clicks a focus) and mini_start hands start_agent a focus only then. The default still decides the
clamp and the capture.
"""
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as ca  # noqa: E402


class _NoThread(object):
    def __init__(self, *a, **k):
        pass

    def start(self):
        pass


class AMiniFocusIsDeclaredOnlyWhenHeChoseIt(unittest.TestCase):

    def _spawn(self, **kw):
        seen = {}

        def fake_start(**k):
            seen.update(k)
            return {"ok": True, "sid": "s_law_1"}

        saved = dict(ca._MINI)
        try:
            with mock.patch.object(ca, "ON_AIR_FLOOR_GB", 0), \
                    mock.patch.object(ca, "_screen_recording_ok_quick", lambda: True), \
                    mock.patch.object(ca, "_agent_alive", lambda: False), \
                    mock.patch.object(ca, "_lane_waking", lambda *a, **k: None), \
                    mock.patch.object(ca.threading, "Thread", _NoThread), \
                    mock.patch.object(ca, "start_agent", fake_start), \
                    mock.patch.dict(ca.__dict__, {"_stop_inflight": False}):
                ca._MINI["running"] = False
                ca.mini_start(seconds=25, test=True, **kw)
        finally:
            ca._MINI.clear()
            ca._MINI.update(saved)
        return seen

    def test_the_pre_selected_default_is_not_a_declaration(self):
        self.assertIsNone(self._spawn(focus="stash").get("focus"),
                          "an untouched default reached the agent as a chosen focus")
        self.assertIsNone(self._spawn(focus="stash", chosen=False).get("focus"))
        self.assertIsNone(self._spawn(focus=None, chosen=True).get("focus"), "nothing chosen is not a focus")

    def test_a_focus_he_clicked_is_declared(self):
        self.assertEqual(self._spawn(focus="gems", chosen=True).get("focus"), "gems")
        self.assertIsNone(self._spawn(focus="not-a-focus", chosen=True).get("focus"),
                          "an unknown value travelled to the agent")

    def test_the_page_says_whether_he_clicked(self):
        with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as f:
            ui = f.read()
        self.assertEqual(ui.count("body: JSON.stringify({ focus: _miniFocus, focusChosen: _miniFocusChosen }) });"), 1)
        self.assertEqual(ui.count("      _miniFocus = b.dataset.f || 'stash';\n      _miniFocusChosen = true;\n"), 1,
                         "a click on a focus no longer marks it chosen")


RED_PROOF = [
    {"why": "REG-2041 - every Mini reel is stamped focusChosen again",
     "file": "control_app.py",
     "find": "        r = start_agent(sim=False, test=bool(test), mini=secs, focus=_chosen_focus, origin=\"mini\")",
     "replace": "        r = start_agent(sim=False, test=bool(test), mini=secs, focus=focus, origin=\"mini\")",
     "matches": 1},
    {"why": "REG-2041 - the page stops saying whether he chose the focus",
     "file": "control_ui.html",
     "find": "body: JSON.stringify({ focus: _miniFocus, focusChosen: _miniFocusChosen }) });",
     "replace": "body: JSON.stringify({ focus: _miniFocus, focusChosen: true }) });",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
