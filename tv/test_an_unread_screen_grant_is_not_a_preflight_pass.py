# -*- coding: utf-8 -*-
"""REG-1795 — AN UNREAD SCREEN GRANT IS NOT A PREFLIGHT PASS.

The doctor and the poll already say the probe was not measured. The preflight
still filed the action bool, and that bool is true when the probe cannot
answer, so the door's fact said the grant was held. The door memory then kept
that true under the new look. The action stays: an unreadable grant does not
refuse a reel. The fact is None. A held grant is still true. An absent grant
still refuses. A replaced action bool still decides the door.

Nothing here calls Quartz, and nothing starts a reel. RED_PROOF below.
[[unknown-stays-unknown]]
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca  # noqa: E402


class AnUnreadScreenGrantIsNotAPreflightPass(unittest.TestCase):

    def setUp(self):
        self._probe = ca._screen_recording_probe
        self._action = ca._screen_recording_ok_quick
        self._floor = ca.ON_AIR_FLOOR_GB
        ca.ON_AIR_FLOOR_GB = 0

    def tearDown(self):
        ca._screen_recording_probe = self._probe
        ca._screen_recording_ok_quick = self._action
        ca.ON_AIR_FLOOR_GB = self._floor

    def _pre(self, door="onair"):
        return ca.capture_preflight(door, look_for_window=False)

    def test_an_unread_probe_is_not_a_grant_the_preflight_calls_held(self):
        ca._screen_recording_probe = lambda: None
        pre = self._pre()
        self.assertIsNone(pre["screenRecOk"], pre)
        self.assertIs(ca._screen_recording_ok_quick(), True,
                      "an unread probe refused the reel")
        self.assertNotIn("Screen Recording", pre.get("why") or "")
        self.assertIs(pre["ok"], True, pre)

    def test_a_held_grant_is_still_held(self):
        ca._screen_recording_probe = lambda: True
        pre = self._pre()
        self.assertIs(pre["screenRecOk"], True, pre)
        self.assertNotIn("Screen Recording", pre.get("why") or "")
        self.assertIs(pre["ok"], True, pre)

    def test_an_absent_grant_still_refuses(self):
        ca._screen_recording_probe = lambda: False
        pre = self._pre()
        self.assertIs(pre["screenRecOk"], False, pre)
        self.assertIn("Screen Recording", pre.get("why") or "")
        self.assertIs(pre["ok"], False, pre)

    def test_a_replaced_action_bool_still_decides_the_door(self):
        ca._screen_recording_probe = lambda: True
        ca._screen_recording_ok_quick = lambda: False
        pre = self._pre("mini")
        self.assertIs(pre["screenRecOk"], False, pre)
        self.assertIn("Screen Recording", pre.get("why") or "")

    def test_an_unread_look_does_not_keep_a_previous_held_bit(self):
        store = {}
        real_load, real_save = ca._capture_door_load, ca._capture_door_save

        def _load():
            return json.loads(json.dumps(store))

        def _save(d):
            store.clear()
            store.update(json.loads(json.dumps(d)))

        ca._capture_door_load = _load
        ca._capture_door_save = _save
        try:
            ca._screen_recording_probe = lambda: True
            ca._capture_door_note("onair", self._pre())
            self.assertIs(store["onair"]["last_screenRecOk"], True)
            ca._screen_recording_probe = lambda: None
            ca._capture_door_note("onair", self._pre())
            self.assertIsNone(store["onair"]["last_screenRecOk"],
                              "an unread look left the previous held bit in place: %r"
                              % store["onair"])
        finally:
            ca._capture_door_load = real_load
            ca._capture_door_save = real_save


RED_PROOF = [
    {"why": "REG-1795 - an unread probe is filed as a grant the preflight calls held",
     "file": "control_app.py",
     "find": "        facts[\"screenRecOk\"] = _screen_recording_preflight_fact()\n",
     "replace": "        facts[\"screenRecOk\"] = bool(_screen_recording_ok_quick())\n",
     "matches": 1},
    {"why": "REG-1795 - an unread look leaves the previous held bit in place",
     "file": "control_app.py",
     "find": "        if val is None and k != \"screenRecOk\":\n"
             "            continue\n"
             "        row[\"last_\" + k] = val\n",
     "replace": "        if val is None:\n"
                "            continue\n"
                "        row[\"last_\" + k] = val\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
