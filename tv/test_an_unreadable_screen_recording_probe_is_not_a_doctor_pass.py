# -*- coding: utf-8 -*-
"""REG-1792 — AN UNREADABLE SCREEN-RECORDING PROBE IS NOT A GRANT THE DOCTOR CALLS HELD.

The doctor asked the action bool. That bool returns true when the probe cannot answer, so
the row said the grant was held. The action stays: an unreadable grant does not refuse a
reel. The report says UNMEASURED. A held grant still says granted. An absent grant still
blocks. The relaunch lamp does not publish that unread as a denial.

Nothing here calls Quartz. RED_PROOF below. [[unknown-stays-unknown]]
"""
import inspect
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca  # noqa: E402


def _boom():
    raise OSError("quartz missing")


class AnUnreadableScreenRecordingProbeIsNotADoctorPass(unittest.TestCase):

    def test_an_ask_that_raises_is_not_measured(self):
        measured = ca._screen_recording_probe(platform="darwin", ask=_boom)
        self.assertIsNone(measured, "an ask that raised came back as a grant")

    def test_an_unreadable_probe_is_not_a_grant_the_doctor_calls_held(self):
        measured = ca._screen_recording_probe(platform="darwin", ask=_boom)
        row = ca._screen_recording_doctor_row(measured)
        self.assertIsNone(measured)
        self.assertIs(row["ok"], False, row)
        self.assertEqual(row["severity"], "warn")
        self.assertEqual(row["id"], "screen_recording")
        self.assertIn("UNMEASURED", row["detail"])
        self.assertNotIn("granted to this process", row["detail"])
        self.assertNotIn("NOT granted", row["detail"])

    def test_a_held_grant_still_says_granted(self):
        row = ca._screen_recording_doctor_row(True)
        self.assertIs(row["ok"], True, row)
        self.assertEqual(row["severity"], "block")
        self.assertIn("granted to this process", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])

    def test_an_absent_grant_still_blocks(self):
        row = ca._screen_recording_doctor_row(False)
        self.assertIs(row["ok"], False, row)
        self.assertEqual(row["severity"], "block")
        self.assertIn("NOT granted", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])

    def test_this_os_does_not_ask_when_it_is_not_darwin(self):
        asked = []

        def ask():
            asked.append(1)
            return False

        self.assertIs(ca._screen_recording_probe(platform="linux", ask=ask), True)
        self.assertEqual(asked, [], "a non-darwin probe asked Quartz")

    def test_a_darwin_ask_is_its_own_answer(self):
        self.assertIs(ca._screen_recording_probe(platform="darwin", ask=lambda: False), False)
        self.assertIs(ca._screen_recording_probe(platform="darwin", ask=lambda: True), True)

    def test_an_unreadable_probe_does_not_refuse_the_action(self):
        with mock.patch.object(ca, "_screen_recording_probe", lambda: None):
            self.assertIs(ca._screen_recording_ok_quick(), True,
                          "an unreadable grant refused a reel")
        with mock.patch.object(ca, "_screen_recording_probe", lambda: False):
            self.assertIs(ca._screen_recording_ok_quick(), False)
        with mock.patch.object(ca, "_screen_recording_probe", lambda: True):
            self.assertIs(ca._screen_recording_ok_quick(), True)

    def test_the_relaunch_lamp_does_not_call_an_unread_a_denial(self):
        self.assertIsNone(ca._screen_recording_grant_lamp(False, "warn"))
        self.assertIs(ca._screen_recording_grant_lamp(False, "block"), False)
        self.assertIs(ca._screen_recording_grant_lamp(True, "block"), True)
        self.assertIs(ca._screen_recording_grant_lamp(True, "warn"), True)

    def test_the_doctor_asks_the_probe(self):
        src = inspect.getsource(ca.doctor_payload)
        self.assertIn("_screen_recording_doctor_row(_screen_recording_probe())", src)
        relaunch = inspect.getsource(ca._screen_recording_grant_lamp)
        self.assertIn("return True if held else None", relaunch)

    def test_the_payload_carries_the_unmeasured_row(self):
        """The helper is not a second doctor. The payload he is served asks it."""
        if sys.platform != "darwin":
            self.skipTest("the screen_recording row is published on darwin only")
        d = tempfile.mkdtemp(prefix="sr_unmeasured_")
        self.addCleanup(__import__("shutil").rmtree, d, True)
        missing = os.path.join(d, "sessions.jsonl")
        with mock.patch.object(ca, "fleet_origin_status",
                                lambda force_fetch=False: {"ok": True, "behind": 0, "head": "x", "howTo": ""}), \
                mock.patch.object(ca, "_reels_missing_index", lambda hist=None: []), \
                mock.patch.object(ca, "_screen_recording_probe", lambda: None), \
                mock.patch.object(ca, "_journal_path", lambda: missing), \
                mock.patch.object(ca, "_one_capture_check",
                                  lambda alive=None: ca._chk("one_capture", True, "warn", "stub")), \
                mock.patch.object(ca, "_one_of_each_check",
                                  lambda: ca._chk("one_of_each", True, "warn", "stub")), \
                mock.patch.object(ca, "_river_outlet_ask",
                                  lambda: ({"ok": True, "onDisk": 0}, {"ok": True, "reels": 0}, [])), \
                mock.patch.object(ca, "_extract_moving_facts",
                                  lambda: {"owed": 0, "memory": "absent", "ageKnown": True}), \
                mock.patch("self_arming.may", lambda lock: (True, "open")):
            got = ca.doctor_payload()
        row = next(c for c in got["checks"] if c["id"] == "screen_recording")
        self.assertIs(row["ok"], False, row)
        self.assertEqual(row["severity"], "warn")
        self.assertIn("UNMEASURED", row["detail"])
        self.assertNotIn("granted to this process", row["detail"])
        blocked = [c for c in got["checks"] if c["severity"] == "block" and not c["ok"]]
        self.assertEqual(blocked, [], "an unread probe turned the doctor into a block: %r" % blocked)


RED_PROOF = [
    {"why": "REG-1792 - an ask that raises is reported as a grant that is held",
     "file": "control_app.py",
     "find": "    try:\n"
             "        return bool(ask())\n"
             "    except Exception:\n"
             "        return None\n",
     "replace": "    try:\n"
                "        return bool(ask())\n"
                "    except Exception:\n"
                "        return True\n",
     "matches": 1},
    {"why": "REG-1792 - an unmeasured row is filed as a pass, so the doctor calls the grant held",
     "file": "control_app.py",
     "find": "        return _chk(\n"
             "            \"screen_recording\", False, \"warn\",\n"
             "            \"UNMEASURED: Screen Recording could not be asked - not a grant that is held\",\n",
     "replace": "        return _chk(\n"
                "            \"screen_recording\", True, \"warn\",\n"
                "            \"UNMEASURED: Screen Recording could not be asked - not a grant that is held\",\n",
     "matches": 1},
    {"why": "REG-1792 - an unreadable probe refuses the reel, which is the action question collapsing into the report",
     "file": "control_app.py",
     "find": "    v = _screen_recording_probe()\n"
             "    return True if v is None else bool(v)\n",
     "replace": "    v = _screen_recording_probe()\n"
                "    return bool(v)\n",
     "matches": 1},
    {"why": "REG-1792 - the relaunch lamp publishes an unread probe as a denial",
     "file": "control_app.py",
     "find": "    if severity == \"block\":\n"
             "        return bool(held)\n"
             "    return True if held else None\n",
     "replace": "    if severity == \"block\":\n"
                "        return bool(held)\n"
                "    return bool(held)\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
