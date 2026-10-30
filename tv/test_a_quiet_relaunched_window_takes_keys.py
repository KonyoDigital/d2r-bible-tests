# -*- coding: utf-8 -*-
"""v3846 - A QUIET-RELAUNCHED CONSOLE WINDOW TAKES KEYS (Elad 2026-10-30 14:23: the d2jsp search would not type).

Root cause: a quiet relaunch creates the window with focus=False, and pywebview's cocoa WindowHost answers
canBecomeKeyWindow with that flag forever. A click put the caret in the field (activeElement right, ui_faults
'framed true, hasFocus false') but the window never became key, so every key went elsewhere. Once loaded, and on
every raise, the window may now become key again.

Measured once by hand in an offscreen WKWebView inside pywebview's own WindowHost: focus=False left a framed
field empty after a real click and keys 'anni'; after _mac_windows_take_keys the keys landed. That probe opened
visible windows on his Mac, so it is NOT a gate - never open a window here.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import control_app as CA  # noqa: E402


class _W(object):
    def __init__(self, focus):
        self.focus = focus; self.key = False
    def isVisible(self): return True
    def isMiniaturized(self): return False
    def makeKeyAndOrderFront_(self, _): self.key = self.focus
    def orderFrontRegardless(self): pass


class _App(object):
    def __init__(self, ws): self.ws = ws
    def windows(self): return self.ws
    def activateIgnoringOtherApps_(self, _): pass


class AQuietWindowTakesKeys(unittest.TestCase):
    def test_loaded_frees_a_window_born_unfocusable(self):
        w = _W(False)
        self.assertEqual(CA._mac_windows_take_keys(_App([w])), 1)
        self.assertIs(w.focus, True, "a window born focus=False can still never become key")

    def test_a_raise_makes_it_key(self):
        w = _W(False)
        did = CA._mac_raise_windows(_App([w]))
        self.assertTrue(w.key, "a Dock raise left a quiet-relaunched window unable to become key: %r" % did)

    def test_the_loaded_event_is_wired(self):
        src = open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.assertIn("win.events.loaded += _mac_windows_take_keys_on_main  # LOADED-TAKES-KEYS", src)


RED_PROOF = [
    {"why": "the window born focus=False is never freed, so the board takes no keys",
     "file": "tv/control_app.py",
     "find": "            if hasattr(w, \"focus\") and w.focus is not True:  # WINDOW-TAKES-KEYS\n                w.focus = True",
     "replace": "            if hasattr(w, \"focus\") and w.focus is not True:  # WINDOW-TAKES-KEYS\n                pass", "matches": 1},
    {"why": "a Dock raise leaves the window unable to become key",
     "file": "tv/control_app.py",
     "find": "            if hasattr(w, \"focus\") and w.focus is not True:  # RAISE-TAKES-KEYS\n                w.focus = True",
     "replace": "            if hasattr(w, \"focus\") and w.focus is not True:  # RAISE-TAKES-KEYS\n                pass", "matches": 1},
]

if __name__ == "__main__":
    unittest.main()
