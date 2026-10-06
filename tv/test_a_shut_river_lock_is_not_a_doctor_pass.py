# -*- coding: utf-8 -*-
"""#86 gap audit 18 (REG-1784) — A SHUT RIVER LOCK IS NOT A DOCTOR THAT PASSED.

/api/doctor never asked may() for the river doors. The self-prove row reads the lane's
last tick, so it can stay green while reel.route, frame.release, vault.sweep_start and
vault.apply are shut.

  · DRIVEN: those four are the doors asked, in that order, through may().
  · DRIVEN: a stale refusal on frame.release and vault.sweep_start stays shut. The
    doctor does not open them.
  · DRIVEN: a shut lock with no reason is still shut.
  · DRIVEN: an answer that is not a pair, and an ask that raises, are UNMEASURED.
  · DRIVEN: the payload he is served carries the row.

Nothing here reads his census. RED_PROOF below. [[unknown-stays-unknown]]
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


DOORS = ("reel.route", "frame.release", "vault.sweep_start", "vault.apply")


def _rows(checks):
    return {c["id"]: c for c in checks}


class AShutRiverLockIsNotADoctorPass(unittest.TestCase):

    def test_the_four_doors_are_the_ones_named(self):
        self.assertEqual(ca._RIVER_LOCKS_ASKED, DOORS)

    def test_four_open_locks_may_act(self):
        asked = []

        def ask(lock):
            asked.append(lock)
            return True, "instruments watched"

        row = ca._river_locks_doctor_row(ask)
        self.assertEqual(tuple(asked), DOORS)
        self.assertIs(row["ok"], True, row)
        self.assertEqual(row["severity"], "warn")
        self.assertIn("may act here", row["detail"])
        self.assertNotIn("are shut", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])
        self.assertNotIn("fix", row)

    def test_a_stale_refusal_on_a_destructive_lock_stays_shut(self):
        why = "the heart census is STALE: it is still being proven (3 gate(s) owed)"

        def ask(lock):
            if lock in ("frame.release", "vault.sweep_start"):
                return False, why
            return True, "open on merit"

        row = ca._river_locks_doctor_row(ask)
        self.assertIs(row["ok"], False, row)
        self.assertEqual(row["severity"], "warn")
        self.assertIn("2 of 4 river locks are shut here", row["detail"])
        self.assertIn("frame.release (%s)" % why, row["detail"])
        self.assertIn("vault.sweep_start (%s)" % why, row["detail"])
        self.assertNotIn("reel.route", row["detail"])
        self.assertNotIn("vault.apply", row["detail"])
        self.assertNotIn("may act here", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])
        self.assertIn("fix", row)

    def test_a_shut_lock_with_no_reason_is_still_shut(self):
        def ask(lock):
            if lock == "reel.route":
                return False, ""
            return True, "open"

        row = ca._river_locks_doctor_row(ask)
        self.assertIs(row["ok"], False, row)
        self.assertIn("reel.route (shut, and no reason was given)", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])
        self.assertNotIn("may act here", row["detail"])

    def test_an_answer_that_is_not_a_pair_is_unmeasured(self):
        def ask(lock):
            return "yes"

        row = ca._river_locks_doctor_row(ask)
        self.assertIs(row["ok"], False, row)
        self.assertIn("UNMEASURED", row["detail"])
        self.assertIn("may(reel.route) did not answer", row["detail"])
        self.assertNotIn("may act here", row["detail"])

    def test_a_raise_after_an_open_lock_is_not_a_pass(self):
        def ask(lock):
            if lock == "reel.route":
                return True, "open"
            raise OSError("census unreadable")

        row = ca._river_locks_doctor_row(ask)
        self.assertIs(row["ok"], False, row)
        self.assertIn("UNMEASURED", row["detail"])
        self.assertIn("OSError", row["detail"])
        self.assertNotIn("may act here", row["detail"])
        self.assertNotIn("are shut", row["detail"])

    def test_the_doctor_payload_asks_may_and_carries_the_row(self):
        asked = []

        def fake(lock):
            asked.append(lock)
            return False, "the heart has never run here"

        with mock.patch.object(ca, "fleet_origin_status",
                                lambda force_fetch=False: {"ok": True, "behind": 0, "head": "x", "howTo": ""}), \
                mock.patch.object(ca, "_reels_missing_index", lambda hist=None: []), \
                mock.patch.object(ca, "_screen_recording_ok_quick", lambda: True), \
                mock.patch.object(ca, "_screen_recording_probe", lambda: True), \
                mock.patch.object(ca, "_one_capture_check",
                                  lambda alive=None: ca._chk("one_capture", True, "warn", "stub")), \
                mock.patch.object(ca, "_one_of_each_check",
                                  lambda: ca._chk("one_of_each", True, "warn", "stub")), \
                mock.patch("self_arming.may", fake), \
                mock.patch.object(ca, "_extract_moving_facts",
                                  lambda: {"owed": 0, "memory": "absent", "ageKnown": True}):
            got = ca.doctor_payload()
        rows = _rows(got["checks"])
        self.assertIn("river_locks", rows)
        self.assertIs(rows["river_locks"]["ok"], False, rows["river_locks"])
        self.assertEqual(rows["river_locks"]["severity"], "warn")
        self.assertEqual(tuple(asked), DOORS)
        for lock in DOORS:
            self.assertIn(lock, rows["river_locks"]["detail"])
        self.assertIn("4 of 4 river locks are shut here", rows["river_locks"]["detail"])
        self.assertNotEqual(rows["river_locks"]["severity"], "block")


RED_PROOF = [
    {"why": "REG-1784 - a shut lock is reported as a pass, so the doctor stays green while the river is shut",
     "file": "control_app.py",
     "find": "        return _chk(\n"
             "            \"river_locks\", False, \"warn\",\n"
             "            \"%d of %d river locks are shut here: %s\" % (\n",
     "replace": "        return _chk(\n"
                "            \"river_locks\", True, \"warn\",\n"
                "            \"%d of %d river locks are shut here: %s\" % (\n",
     "matches": 1},
    {"why": "REG-1784 - an ask that did not come back reads as a pass",
     "file": "control_app.py",
     "find": "    return _chk(\n"
             "        \"river_locks\", False, \"warn\",\n"
             "        \"UNMEASURED: %s - not a river that may act\" % why)\n",
     "replace": "    return _chk(\n"
                "        \"river_locks\", True, \"warn\",\n"
                "        \"the river locks may act here (%s)\" % why)\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
