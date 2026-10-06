# -*- coding: utf-8 -*-
"""REG-1917 - THE LAUNCHER RELOOK SAYS WHAT THIS OS CAN FILM, AND A BOOL IS NOT A DEADLINE.

From a Grok look at v3596 (the windows slice re-asked at --effort low, 2026-10-07): off a Mac the relook said "this PC
films only inside a reel" - true of Windows, false of Linux, which films no window at all; and `launcherUntil` passed
`isinstance(x, (int, float))` when it was a bool, so True read as 1 ms and the wait was over at once. Three sites read
that deadline; all three refuse a bool. Fixtures only: the shadow-watch store and its note are stubbed.
"""
import os
import sys
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as CA  # noqa: E402


class TheRelookSaysWhatThisOSCanFilm(unittest.TestCase):

    def _say(self, platform):
        with mock.patch.object(CA.sys, "platform", platform):
            return CA._bare_relook_one_frame(10 ** 12, {}, {})

    def test_windows_films_inside_a_reel(self):
        self.assertIn("films only inside a reel", self._say("win32"))

    def test_linux_is_not_said_to_film(self):
        say = self._say("linux")
        self.assertNotIn("films only inside a reel", say, "Linux was told it films inside a reel (REG-1917)")
        self.assertIn("cannot film a window outside a reel", say)


class ABoolIsNotADeadline(unittest.TestCase):

    def setUp(self):
        self.notes = []
        self.p1 = mock.patch.object(CA, "_shadow_watch_note", lambda **kw: self.notes.append(kw))
        self.p1.start()

    def tearDown(self):
        self.p1.stop()

    def test_an_unknown_relook_with_a_bool_deadline_holds_the_door(self):
        out = CA._relook_unknown(10 ** 12, {}, {"launcherUntil": True}, "the frame could not be taken")
        self.assertIsInstance(out, dict, "a bool deadline read as 1 ms and opened the reel at once (REG-1917): %r" % (out,))

    def test_a_real_deadline_still_opens_when_it_is_over(self):
        out = CA._relook_unknown(10 ** 12, {}, {"launcherUntil": 1}, "the frame could not be taken")
        self.assertIsInstance(out, str)

    def test_the_open_check_reads_a_bool_as_no_deadline(self):
        with mock.patch.object(CA, "_shadow_watch_stored", lambda: {"launcherUntil": False}):
            self.assertTrue(CA._bare_relook_open(10 ** 12))


RED_PROOF = [
    {
        "why": "REG-1917 - Linux is told it films inside a reel again",
        "file": "tv/control_app.py",
        "find": "        if sys.platform.startswith(\"win\"):\n            return (\"this PC films only inside a reel, so the relook cannot be one frame; \"\n",
        "replace": "        if True:\n            return (\"this PC films only inside a reel, so the relook cannot be one frame; \"\n",
        "matches": 1,
    },
    {
        "why": "REG-1917 - a bool deadline is a time again: True reads as 1 ms and the reel opens at once",
        "file": "tv/control_app.py",
        "find": "    if isinstance(until, (int, float)) and not isinstance(until, bool) \\\n            and now >= float(until) + _BARE_HUD_RELOOK_S * 1000:",
        "replace": "    if isinstance(until, (int, float)) \\\n            and now >= float(until) + _BARE_HUD_RELOOK_S * 1000:",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
