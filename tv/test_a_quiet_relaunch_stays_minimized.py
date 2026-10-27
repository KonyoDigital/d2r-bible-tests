# -*- coding: utf-8 -*-
"""#179 - A QUIET RELAUNCH STAYS MINIMIZED; THE NEXT ONE DOES NOT HIDE IT.

GrokBot's Linux seat lost its window (WINDOW_GONE) and Dean's console "came back hidden" after self-updates. Read in
code at v3812: a quiet relaunch opens the window minimized and records the background reason "quiet relaunch: ...";
hidden_relaunch_env treated every reason but exactly "minimized" as HIDDEN, so the next automatic relaunch set
TV_START_HIDDEN and the window started hidden - no window, no Dock tile - while window_mode_payload told him the
Desktop icon brings it back.

Driven on the real functions: a quiet-relaunch background relaunches minimized (no TV_START_HIDDEN) and is said as
minimized; a window-close background still relaunches hidden; his own minimize is unchanged.
RED_PROOF below.
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
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

QUIET = {"on": True, "by": "quiet relaunch: the console was in the background (window-close)", "since": 1792800000000}


class AQuietRelaunchStaysMinimized(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import control_app as ca
        cls.ca = ca

    def test_the_next_relaunch_after_a_quiet_one_is_not_hidden(self):
        env, argv = {}, ["control_app.py"]
        self.assertIsNone(self.ca.hidden_relaunch_env(dict(QUIET), env, argv),
                          "a window the quiet relaunch opened minimized was relaunched HIDDEN (#179)")
        self.assertNotIn("TV_START_HIDDEN", env)

    def test_a_hidden_window_still_comes_back_hidden_and_his_minimize_is_unchanged(self):
        env = {}
        self.assertTrue(self.ca.hidden_relaunch_env({"on": True, "by": "window-close"}, env, []))
        self.assertIn("TV_START_HIDDEN", env)
        env = {}
        self.assertIsNone(self.ca.hidden_relaunch_env({"on": True, "by": "minimized"}, env, []))
        self.assertNotIn("TV_START_HIDDEN", env)

    def test_the_console_says_minimized_for_a_quiet_boot(self):
        with mock.patch.object(self.ca, "_BACKGROUND", dict(QUIET)):
            say = self.ca.window_mode_payload().get("say") or ""
        self.assertIn("minimized since", say, "a quiet boot's window was described as hidden: %r" % say)
        self.assertNotIn("Desktop icon", say)


RED_PROOF = [
    {"why": "#179 - a quiet relaunch's window is read as hidden again, so the next relaunch hides it",
     "file": "tv/control_app.py",
     "find": "    return by == \"minimized\" or by.startswith(\"quiet relaunch:\")\n",
     "replace": "    return by == \"minimized\"\n",
     "matches": 1},
    {"why": "#179 - the relaunch ignores the minimized rule again",
     "file": "tv/control_app.py",
     "find": "    if bg.get(\"on\") and not _bg_minimized(bg):\n",
     "replace": "    if bg.get(\"on\") and bg.get(\"by\") != \"minimized\":\n",
     "matches": 1},
    {"why": "#179 - a quiet boot is described as hidden behind the Desktop icon again",
     "file": "tv/control_app.py",
     "find": "                       if _bg_minimized(_BACKGROUND) else",
     "replace": "                       if _BACKGROUND.get(\"by\") == \"minimized\" else",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
