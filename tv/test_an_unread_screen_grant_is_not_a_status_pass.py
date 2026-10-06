# -*- coding: utf-8 -*-
"""REG-1794 — AN UNREAD SCREEN GRANT IS NOT A STATUS PASS.

The doctor already says UNMEASURED. The poll still published the action bool,
and that bool is true when the probe cannot answer, so the stall copy said the
grant was held. The action stays: an unreadable grant does not refuse a reel.
The poll says None. The stall copy says granted only when the bit is true.

Nothing here calls Quartz. RED_PROOF below. [[unknown-stays-unknown]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca  # noqa: E402

_UI = os.path.join(HERE, "control_ui.html")
_CAPTION_TRUE = "          : (st.screenRecOk === true\n"
_HOLD_TRUE = "            else if (st.screenRecOk === true) shb.innerHTML = isWin\n"


def _clear():
    ca._SCREEN_REC_CACHE["t"] = 0.0
    ca._SCREEN_REC_CACHE["v"] = None
    ca._SCREEN_REC_CACHE["known"] = False


class AnUnreadScreenGrantIsNotAStatusPass(unittest.TestCase):

    def setUp(self):
        self._probe = ca._screen_recording_probe
        _clear()

    def tearDown(self):
        ca._screen_recording_probe = self._probe
        _clear()

    def test_an_unread_probe_is_not_a_grant_the_poll_publishes(self):
        ca._screen_recording_probe = lambda: None
        self.assertIsNone(ca.screen_recording_ok_cached())
        self.assertIs(ca._screen_recording_ok_quick(), True,
                      "an unread probe refused the reel")

    def test_an_unread_answer_is_remembered_for_the_poll(self):
        calls = {"n": 0}

        def ask():
            calls["n"] += 1
            return None

        ca._screen_recording_probe = ask
        self.assertIsNone(ca.screen_recording_ok_cached())
        self.assertIsNone(ca.screen_recording_ok_cached())
        self.assertEqual(calls["n"], 1, "an unread answer asked Quartz again on the next poll")

    def test_a_held_grant_and_an_absent_one_still_say_what_they_are(self):
        ca._screen_recording_probe = lambda: True
        self.assertIs(ca.screen_recording_ok_cached(), True)
        _clear()
        ca._screen_recording_probe = lambda: False
        self.assertIs(ca.screen_recording_ok_cached(), False)

    def test_a_raise_is_not_measured_and_not_asked_again(self):
        calls = {"n": 0}

        def boom():
            calls["n"] += 1
            raise OSError("quartz missing")

        ca._screen_recording_probe = boom
        self.assertIsNone(ca.screen_recording_ok_cached())
        self.assertIsNone(ca.screen_recording_ok_cached())
        self.assertEqual(calls["n"], 1)

    def test_the_stall_copy_claims_the_grant_only_when_it_is_true(self):
        with open(_UI, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn(_CAPTION_TRUE, src)
        self.assertIn(_HOLD_TRUE, src)
        self.assertIn("Screen Recording was not measured", src)
        self.assertIn("Screen Recording was <b>not measured</b>", src)
        self.assertNotIn("st.screenRecOk !== false", src)


RED_PROOF = [
    {"why": "REG-1794 - an unread probe is published as a grant the poll calls held",
     "file": "control_app.py",
     "find": "    if v is not None:\n"
             "        v = bool(v)\n"
             "    c[\"t\"], c[\"v\"], c[\"known\"] = now, v, True\n",
     "replace": "    v = True if v is None else bool(v)\n"
                "    c[\"t\"], c[\"v\"], c[\"known\"] = now, v, True\n",
     "matches": 1},
    {"why": "REG-1794 - the caption calls every non-false a grant that is held",
     "file": "control_ui.html",
     "find": "          : (st.screenRecOk === true\n",
     "replace": "          : (st.screenRecOk !== false\n",
     "matches": 1},
    {"why": "REG-1794 - the hold card calls every non-false a grant that is held",
     "file": "control_ui.html",
     "find": "            else if (st.screenRecOk === true) shb.innerHTML = isWin\n",
     "replace": "            else if (st.screenRecOk !== false) shb.innerHTML = isWin\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
