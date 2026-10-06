# -*- coding: utf-8 -*-
"""REG-1787 — AN UNREADABLE DISK IS NOT A FARMGATE PASS.

The eagle already says UNKNOWN when disk usage will not read. The one-button gate
caught that raise and filed ok true: "disk usage unreadable". A button can say GO
over a disk nobody measured. Below 2 GB still blocks. Between 2 and 8 GB the night
warning still appears. At 8 GB and above the disk row still passes and the night
warning is absent.

  · DRIVEN: None, a bool, and a non-number are not room.
  · DRIVEN: below 2 GB still blocks, with the night sentence.
  · DRIVEN: between 2 and 8 still warns for the night. At 8 and above that row is absent.
  · DRIVEN: the gate he presses carries the unread row, and the verdict is not GO.

Nothing here asks his disk, git, Claude, or his console. RED_PROOF below.
[[unknown-stays-unknown]] [[copy-drift]]
"""
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca  # noqa: E402


COUNTED = {"ok": True, "behind": 0, "head": "abc1234", "howTo": "level"}


def _rows(free_gb):
    return ca._disk_farmgate_rows(free_gb)


def _by_id(rows):
    return {r["id"]: r for r in rows}


class AnUnreadableDiskIsNotAFarmgatePass(unittest.TestCase):

    def test_a_missing_read_is_not_room(self):
        got = _by_id(_rows(None))
        self.assertIs(got["disk"]["ok"], False, got["disk"])
        self.assertEqual(got["disk"]["severity"], "warn")
        self.assertIn("UNMEASURED", got["disk"]["detail"])
        self.assertIn("could not be read", got["disk"]["detail"])
        self.assertNotIn("disk_low", got)

    def test_a_bool_is_not_a_free_count(self):
        for bad in (True, False):
            got = _by_id(_rows(bad))
            self.assertIs(got["disk"]["ok"], False, got["disk"])
            self.assertIn("could not be read", got["disk"]["detail"])
            self.assertNotIn("disk_low", got)

    def test_a_non_number_is_not_room(self):
        got = _by_id(_rows("plenty"))
        self.assertIs(got["disk"]["ok"], False, got["disk"])
        self.assertIn("UNMEASURED", got["disk"]["detail"])
        self.assertNotIn("disk_low", got)

    def test_below_two_gigabytes_still_blocks(self):
        got = _by_id(_rows(1.0))
        self.assertIs(got["disk"]["ok"], False, got["disk"])
        self.assertEqual(got["disk"]["severity"], "block")
        self.assertEqual(got["disk"]["detail"], "only 1.0 GB free")
        self.assertIn("clear space", got["disk"]["fix"])
        self.assertNotIn("disk_low", got)

    def test_between_two_and_eight_still_warns_for_the_night(self):
        got = _by_id(_rows(3.0))
        self.assertIs(got["disk"]["ok"], True, got["disk"])
        self.assertEqual(got["disk"]["detail"], "3.0 GB free")
        self.assertNotIn("fix", got["disk"])
        self.assertIs(got["disk_low"]["ok"], False, got["disk_low"])
        self.assertEqual(got["disk_low"]["severity"], "warn")
        self.assertIn("fine for one night", got["disk_low"]["detail"])

    def test_eight_gigabytes_and_above_passes_with_no_night_warning(self):
        for free in (8.0, 20):
            got = _by_id(_rows(free))
            self.assertIs(got["disk"]["ok"], True, got["disk"])
            self.assertNotIn("disk_low", got, free)

    def _payload(self, disk):
        with mock.patch.object(ca, "status_payload", lambda *a, **k: {"ver": None}), \
                mock.patch.object(ca, "fleet_origin_status", lambda *a, **k: dict(COUNTED)), \
                mock.patch.object(ca, "_find_claude_bin", lambda *a, **k: None), \
                mock.patch.object(ca, "_G5", None), \
                mock.patch.object(ca, "_sock_open", lambda *a, **k: False), \
                mock.patch.object(ca, "_d2r_running_here", lambda: (True, "stub")), \
                mock.patch.object(ca.shutil, "disk_usage", disk):
            return ca.farmgate_payload()

    def test_the_gate_carries_the_unread_disk_and_does_not_say_go(self):
        def _raise(*_a, **_k):
            raise OSError("disk unreadable")

        got = self._payload(_raise)
        row = next(c for c in got["checks"] if c["id"] == "disk")
        self.assertIs(row["ok"], False, row)
        self.assertIn("UNMEASURED", row["detail"])
        self.assertIn("could not be read", row["detail"])
        self.assertNotIn("unreadable", row["detail"].lower())
        self.assertFalse(any(c["id"] == "disk_low" for c in got["checks"]))
        self.assertNotEqual(got["verdict"], "GO")
        self.assertIs(got["ok"], True)

    def test_a_roomy_disk_on_the_gate_still_passes(self):
        usage = type("U", (), {"free": 20 * (1024 ** 3)})()
        got = self._payload(lambda *_a, **_k: usage)
        row = next(c for c in got["checks"] if c["id"] == "disk")
        self.assertIs(row["ok"], True, row)
        self.assertFalse(any(c["id"] == "disk_low" for c in got["checks"]))


RED_PROOF = [
    {"why": "REG-1787 - a disk read that did not come back reads as room again",
     "file": "control_app.py",
     "find": "        return [_chk(\n"
             "            \"disk\", False, \"warn\",\n"
             "            \"UNMEASURED: disk usage could not be read - not a disk that has room\")]\n",
     "replace": "        return [_chk(\n"
                "            \"disk\", True, \"warn\",\n"
                "            \"UNMEASURED: disk usage could not be read - not a disk that has room\")]\n",
     "matches": 1},
    {"why": "REG-1787 - a disk below 2 GB reads as a pass again",
     "file": "control_app.py",
     "find": "        \"disk\", ok_d, \"block\" if free_gb < 2 else \"warn\",\n",
     "replace": "        \"disk\", True, \"block\" if free_gb < 2 else \"warn\",\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
