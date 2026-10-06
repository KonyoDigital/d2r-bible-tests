# -*- coding: utf-8 -*-
"""REG-1786 — A FAILED FLEET COUNT IS NOT A FARMGATE PASS.

REG-141 made /api/doctor refuse a rev-list that did not answer. The one-button gate
kept the old copy: behind 0, including the 0 a failed count leaves behind, was
"unified with origin/main", and a raise was "fleet check skipped" with ok true.
The button can say GO over a PC that never asked origin.

  · DRIVEN: ok false and behind 0 is not unified.
  · DRIVEN: a raise, and a report that is not a dict, are not a skip that passed.
  · DRIVEN: a behind that is not an int is not zero.
  · DRIVEN: a counted zero is still unified. A counted gap is still behind.
  · DRIVEN: the gate he presses carries the row, and does not publish that 0.

Nothing here asks git or his console. RED_PROOF below. [[unknown-stays-unknown]] [[copy-drift]]
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


FAILED = {
    "ok": False,
    "behind": 0,
    "head": "abc1234",
    "howTo": "could not count commits vs origin/main",
}


class AFailedFleetCountIsNotAFarmgatePass(unittest.TestCase):

    def test_a_failed_count_with_behind_zero_is_not_unified(self):
        row = ca._fleet_origin_farmgate_row(FAILED)
        self.assertIs(row["ok"], False, row)
        self.assertEqual(row["severity"], "warn")
        self.assertNotIn("unified with origin/main", row["detail"].lower())
        self.assertIn("could not ask origin", row["detail"])
        self.assertIn("UNMEASURED", row["detail"])
        self.assertEqual(row["fix"], "could not count commits vs origin/main")

    def test_a_raise_is_not_a_skip_that_passed(self):
        row = ca._fleet_origin_farmgate_row(None, OSError("git missing"))
        self.assertIs(row["ok"], False, row)
        self.assertIn("OSError", row["detail"])
        self.assertIn("git", row["fix"])
        self.assertNotIn("skipped", row["detail"].lower())
        self.assertNotIn("unified with origin/main", row["detail"].lower())

    def test_a_report_that_is_not_a_dict_is_not_a_pass(self):
        row = ca._fleet_origin_farmgate_row("nope")
        self.assertIs(row["ok"], False, row)
        self.assertIn("no report", row["detail"])

    def test_a_missing_behind_is_not_zero(self):
        row = ca._fleet_origin_farmgate_row({"ok": True, "head": "abc"})
        self.assertIs(row["ok"], False, row)
        self.assertIn("did not say how far behind", row["detail"])
        self.assertNotIn("unified with origin/main", row["detail"].lower())

    def test_a_bool_behind_is_not_a_count(self):
        row = ca._fleet_origin_farmgate_row({"ok": True, "behind": True, "head": "abc"})
        self.assertIs(row["ok"], False, row)
        self.assertNotIn("unified with origin/main", row["detail"].lower())

    def test_a_counted_zero_is_still_unified(self):
        row = ca._fleet_origin_farmgate_row(
            {"ok": True, "behind": 0, "head": "abc1234", "howTo": "level"})
        self.assertIs(row["ok"], True, row)
        self.assertIn("unified with origin/main (abc1234)", row["detail"])
        self.assertNotIn("fix", row)

    def test_a_counted_gap_is_still_behind(self):
        row = ca._fleet_origin_farmgate_row(
            {"ok": True, "behind": 3, "head": "abc", "latest": "fix: x", "howTo": "pull"})
        self.assertIs(row["ok"], False, row)
        self.assertIn("3 commit(s) BEHIND origin", row["detail"])
        self.assertEqual(row["fix"], "pull")

    def test_the_gate_carries_the_failed_count_and_does_not_publish_zero(self):
        with mock.patch.object(ca, "status_payload", lambda *a, **k: {"ver": None}), \
                mock.patch.object(ca, "fleet_origin_status", lambda *a, **k: dict(FAILED)), \
                mock.patch.object(ca, "_find_claude_bin", lambda *a, **k: None), \
                mock.patch.object(ca, "_G5", None), \
                mock.patch.object(ca, "_sock_open", lambda *a, **k: False), \
                mock.patch.object(ca, "_d2r_running_here", lambda: (True, "stub")), \
                mock.patch.object(ca.shutil, "disk_usage",
                                  lambda *_a, **_k: type("U", (), {"free": 20 * (1024 ** 3)})()):
            got = ca.farmgate_payload()
        row = next(c for c in got["checks"] if c["id"] == "fleet_origin")
        self.assertIs(row["ok"], False, row)
        self.assertNotIn("unified with origin/main", row["detail"].lower())
        self.assertNotIn("fleetBehind", got["vers"])
        self.assertNotEqual(got["verdict"], "GO")


RED_PROOF = [
    {"why": "REG-1786 - a failed fleet count with behind 0 reads as unified again",
     "file": "control_app.py",
     "find": "    if report.get(\"ok\") is False:\n"
             "        return _chk(\n"
             "            \"fleet_origin\", False, \"warn\",\n"
             "            \"UNMEASURED: could not ask origin - not a PC unified with origin\",\n",
     "replace": "    if report.get(\"ok\") is False:\n"
                "        return _chk(\n"
                "            \"fleet_origin\", True, \"warn\",\n"
                "            \"UNMEASURED: could not ask origin - not a PC unified with origin\",\n",
     "matches": 1},
    {"why": "REG-1786 - a fleet check that raised reads as a skip that passed",
     "file": "control_app.py",
     "find": "        return _chk(\n"
             "            \"fleet_origin\", False, \"warn\",\n"
             "            \"UNMEASURED: the fleet check did not run (%s) - not a PC unified with origin\"\n",
     "replace": "        return _chk(\n"
                "            \"fleet_origin\", True, \"warn\",\n"
                "            \"UNMEASURED: the fleet check did not run (%s) - not a PC unified with origin\"\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
