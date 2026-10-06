# -*- coding: utf-8 -*-
"""#86 gap audit 28 (REG-1779) — A BOOT SWEEP THAT NEVER RAN IS NOT A CLEAN CAPTURE.

The one-capture row said OK, "not asked yet", for the whole life of a console whose boot sweep
never ran. On Windows that sweep is the rescue loop's second tick, about 20 s after boot. Past
a minute, never-ran means the loop may be dead, and a capture an older console left may still
be filming. That was a green row.

  · DRIVEN: Windows, past the minute, sweep never ran -> not ok, UNKNOWN, and it says the boot
    sweep never ran. The same through the doctor's own payload, and through the clock the row
    uses when nobody hands it an age.
  · DRIVEN: an age that will not parse is that same unknown, not a young console.
  · DRIVEN: the first minute on Windows is still not a fault. A Mac at any age never runs this
    sweep and stays ok. A sweep that did run is still judged by what it found, not by the clock.
Nothing here starts a capture, asks his process table, or reads his shelf. RED_PROOF below.
[[unknown-stays-unknown]]
"""
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca  # noqa: E402


_NEVER = {"ran": None, "found": None, "killed": [], "kept": [], "failed": [], "say": "not asked yet"}


class ABootSweepThatNeverRan(unittest.TestCase):

    def setUp(self):
        self._sweep = dict(ca._CAP_SWEEP)
        self._stop = dict(ca._CAP_STOP)
        ca._CAP_SWEEP.clear()
        ca._CAP_SWEEP.update(_NEVER)
        ca._CAP_STOP.clear()
        ca._CAP_STOP.update({"survived": 0, "last": None})
        self.addCleanup(self._restore)

    def _restore(self):
        ca._CAP_SWEEP.clear()
        ca._CAP_SWEEP.update(self._sweep)
        ca._CAP_STOP.clear()
        ca._CAP_STOP.update(self._stop)

    def _row(self, win, uptime_s=None, omit_age=False):
        with mock.patch.object(ca, "IS_WIN", win):
            if omit_age:
                return ca._one_capture_check(alive=lambda p: False)
            return ca._one_capture_check(alive=lambda p: False, uptime_s=uptime_s)

    def test_a_windows_console_past_the_minute_is_not_clean(self):
        row = self._row(True, 3600)
        self.assertIs(row["ok"], False, row)
        self.assertEqual(row["severity"], "warn")
        self.assertIn("UNKNOWN - the boot sweep never ran", row["detail"])
        self.assertIn("past that", row["detail"])
        self.assertIn("Restart TV DIABLO", row.get("fix") or "")
        self.assertNotIn("not asked yet", row["detail"])

    def test_the_clock_the_row_reads_itself_is_the_same_rule(self):
        with mock.patch.object(ca, "_BOOT_MONO", time.monotonic() - 4000):
            row = self._row(True, omit_age=True)
        self.assertIs(row["ok"], False, row)
        self.assertIn("boot sweep never ran", row["detail"])

    def test_an_age_that_will_not_parse_is_not_a_young_console(self):
        row = self._row(True, "nope")
        self.assertIs(row["ok"], False, row)
        self.assertIn("boot sweep never ran", row["detail"])
        young = self._row(True, -1)
        self.assertIs(young["ok"], False, young)

    def test_the_first_minute_and_a_mac_and_a_sweep_that_ran_stay_clean(self):
        inside = self._row(True, 60.0)
        self.assertIs(inside["ok"], True, inside)
        self.assertNotIn("boot sweep never ran", inside["detail"])
        early = self._row(True, 10)
        self.assertIs(early["ok"], True, early)
        mac = self._row(False, 4000)
        self.assertIs(mac["ok"], True, mac)
        self.assertNotIn("boot sweep never ran", mac["detail"])
        ca._CAP_SWEEP.update(ran=1, found=0, say="0 capture script(s) of this checkout: ended 0 orphan(s), kept 0")
        ran = self._row(True, 4000)
        self.assertIs(ran["ok"], True, ran)
        self.assertNotIn("boot sweep never ran", ran["detail"])
        self.assertIn("ended 0 orphan", ran["detail"])

    def test_the_doctor_payload_carries_the_row(self):
        """The helper is not a second doctor. The payload he is served asks it."""
        d = tempfile.mkdtemp(prefix="sweep_never_")
        self.addCleanup(__import__("shutil").rmtree, d, True)
        missing = os.path.join(d, "sessions.jsonl")
        with mock.patch.object(ca, "IS_WIN", True), \
                mock.patch.object(ca, "_BOOT_MONO", time.monotonic() - 4000), \
                mock.patch.object(ca, "_capture_health", lambda: ""), \
                mock.patch.object(ca, "fleet_origin_status",
                                  lambda force_fetch=False: {"ok": True, "behind": 0, "head": "x", "howTo": ""}), \
                mock.patch.object(ca, "_reels_missing_index", lambda hist=None: []), \
                mock.patch.object(ca, "_screen_recording_ok_quick", lambda: True), \
                mock.patch.object(ca, "_journal_path", lambda: missing), \
                mock.patch.object(ca, "_one_of_each_check",
                                  lambda alive=None: ca._chk("one_of_each", True, "warn", "stub")), \
                mock.patch.object(ca, "_extract_moving_facts",
                                  lambda: {"owed": 0, "memory": "absent", "ageKnown": True}):
            got = ca.doctor_payload()
        row = next(c for c in got["checks"] if c["id"] == "one_capture")
        self.assertIs(row["ok"], False, row)
        self.assertIn("boot sweep never ran", row["detail"])
        self.assertIn("Restart TV DIABLO", row.get("fix") or "")


RED_PROOF = [
    {"why": "REG-1779 - a Windows boot sweep that never ran, past the minute it was due, reads as a clean capture",
     "file": "control_app.py",
     "find": "    _late = bool(IS_WIN and _never and (_asked is None or _asked > CAPTURE_SWEEP_LATE_S))\n",
     "replace": "    _late = False\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
