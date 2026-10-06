# -*- coding: utf-8 -*-
"""#86 gap audit 18 (REG-1785) — OLD REELS AND ZERO TOMBSTONES ARE NOT A DOCTOR THAT PASSED.

/api/doctor never asked whether this console had closed a reel out. Reels older than two
days that sit outside the newest KEEP_RECENT, with a lifetime tombstone count of zero,
read as a pass.

  · DRIVEN: one reel past that shield and that age, and a read ledger of zero, is not ok.
  · DRIVEN: the same reel inside the newest KEEP_RECENT is kept by law, and is not this warn.
  · DRIVEN: a reel outside the shield that is still young is not this warn.
  · DRIVEN: a lifetime above zero is not this warn.
  · DRIVEN: a missing ledger is that zero, measured absent. A file that will not parse is
    UNMEASURED. A census that did not come back is UNMEASURED. A torn name list is UNMEASURED.
  · DRIVEN: a fixture is not his footage. An empty shelf is not a shut outlet.
  · DRIVEN: the payload he is served carries the row. The row does not ask may().

Nothing here deletes a reel. RED_PROOF below. [[unknown-stays-unknown]]
"""
import inspect
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
import reel_retention as rr  # noqa: E402


NOW = 1780000000000
KEEP = rr.KEEP_RECENT


def _reel(ms, n, tag=None):
    rec = {"reel": "reel_s_%d_%d" % (ms, n)}
    if tag is not None:
        rec["tag"] = tag
    return rec


def _census(n):
    return {"ok": True, "onDisk": n, "why": "measured"}


def _stones(n):
    return {"ok": True, "reels": n}


def _outside(now, old=1):
    """KEEP young reels, then `old` ancient ones, so the ancient ones fall outside the shield."""
    rows = [_reel(now - 3600 * 1000 - i * 1000, i) for i in range(KEEP)]
    for j in range(old):
        rows.append(_reel(now - (3 + j) * 86400000, 1000 + j))
    return rows


def _rows(checks):
    return {c["id"]: c for c in checks}


class AZeroTombstoneIsNotADoctorPass(unittest.TestCase):

    def test_an_old_reel_outside_the_newest_with_zero_tombstones_is_not_a_pass(self):
        rows = _outside(NOW)
        row = ca._river_outlet_doctor_row(_census(len(rows)), _stones(0), rows, NOW)
        self.assertIs(row["ok"], False, row)
        self.assertEqual(row["severity"], "warn")
        self.assertIn(
            "1 reel(s) on disk are older than %d days and outside the newest %d"
            % (ca.RIVER_OUTLET_OLD_DAYS, KEEP),
            row["detail"])
        self.assertIn("0 lifetime tombstones", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])
        self.assertNotIn("not a shut outlet", row["detail"])
        self.assertNotIn("measured absent", row["detail"])
        self.assertIn("does not open a lock", row["fix"])
        self.assertIn("does not delete", row["fix"])

    def test_reels_inside_the_newest_are_not_a_shut_outlet(self):
        rows = [_reel(NOW - 10 * 86400000 - i * 1000, i) for i in range(KEEP)]
        row = ca._river_outlet_doctor_row(_census(len(rows)), _stones(0), rows, NOW)
        self.assertIs(row["ok"], True, row)
        self.assertIn("not a shut outlet", row["detail"])
        self.assertIn("0 lifetime tombstones", row["detail"])
        self.assertNotIn("are older than", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])
        self.assertNotIn("fix", row)

    def test_a_young_reel_outside_the_newest_is_not_a_shut_outlet(self):
        rows = [_reel(NOW - 3600 * 1000 - i * 1000, i) for i in range(KEEP + 1)]
        row = ca._river_outlet_doctor_row(_census(len(rows)), _stones(0), rows, NOW)
        self.assertIs(row["ok"], True, row)
        self.assertIn("not a shut outlet", row["detail"])
        self.assertNotIn("are older than", row["detail"])
        self.assertNotIn("fix", row)

    def test_a_lifetime_above_zero_is_not_this_warn(self):
        rows = _outside(NOW)
        row = ca._river_outlet_doctor_row(_census(len(rows)), _stones(4), rows, NOW)
        self.assertIs(row["ok"], True, row)
        self.assertIn("closed out 4", row["detail"])
        self.assertNotIn("are older than", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])
        self.assertNotIn("fix", row)

    def test_a_missing_ledger_is_zero_not_unmeasured(self):
        missing = os.path.join(HERE, "reel_tombstones.json.not-here-%d" % os.getpid())
        rows = _outside(NOW)
        with mock.patch.object(rr, "_tombstone_path", lambda *a, **k: missing):
            view = ca.tombstone_view()
        self.assertIs(view.get("ledgerAbsent"), True)
        self.assertIsNone(view.get("reels"))
        self.assertFalse(view.get("ok"))
        row = ca._river_outlet_doctor_row(_census(len(rows)), view, rows, NOW)
        self.assertIs(row["ok"], False, row)
        self.assertIn("measured absent", row["detail"])
        self.assertIn("0 lifetime tombstones", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])

    def test_an_empty_ledger_is_zero_tombstones(self):
        fd, path = tempfile.mkstemp(prefix="tomb-empty-", suffix=".json")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write('{"reels": []}')
            rows = _outside(NOW)
            with mock.patch.object(rr, "_tombstone_path", lambda *a, **k: path):
                view = ca.tombstone_view()
            self.assertTrue(view.get("ok"), view)
            self.assertEqual(view.get("reels"), 0)
            self.assertIsNot(view.get("ledgerAbsent"), True)
            row = ca._river_outlet_doctor_row(_census(len(rows)), view, rows, NOW)
            self.assertIs(row["ok"], False, row)
            self.assertIn("0 lifetime tombstones", row["detail"])
            self.assertNotIn("measured absent", row["detail"])
            self.assertNotIn("UNMEASURED", row["detail"])
        finally:
            os.unlink(path)

    def test_a_ledger_that_will_not_parse_is_not_a_pass(self):
        fd, path = tempfile.mkstemp(prefix="tomb-bad-", suffix=".json")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("{")
            rows = _outside(NOW)
            with mock.patch.object(rr, "_tombstone_path", lambda *a, **k: path):
                view = ca.tombstone_view()
            self.assertIsNone(view.get("reels"))
            self.assertIsNot(view.get("ledgerAbsent"), True)
            row = ca._river_outlet_doctor_row(_census(len(rows)), view, rows, NOW)
            self.assertIs(row["ok"], False, row)
            self.assertIn("UNMEASURED", row["detail"])
            self.assertNotIn("are older than", row["detail"])
            self.assertNotIn("not a shut outlet", row["detail"])
            self.assertNotIn("fix", row)
        finally:
            os.unlink(path)

    def test_a_census_that_did_not_come_back_is_not_a_pass(self):
        row = ca._river_outlet_doctor_row(
            {"ok": False, "onDisk": None, "why": "plan raised OSError"}, None, None, NOW)
        self.assertIs(row["ok"], False, row)
        self.assertIn("UNMEASURED", row["detail"])
        self.assertIn("OSError", row["detail"])
        self.assertNotIn("not a shut outlet", row["detail"])
        self.assertNotIn("closed out", row["detail"])

    def test_a_torn_name_list_is_not_a_pass(self):
        rows = _outside(NOW)
        row = ca._river_outlet_doctor_row(_census(len(rows) - 1), _stones(0), rows, NOW)
        self.assertIs(row["ok"], False, row)
        self.assertIn("UNMEASURED", row["detail"])
        self.assertIn("torn read", row["detail"])
        self.assertNotIn("are older than", row["detail"])

    def test_names_that_were_not_read_are_not_a_pass(self):
        row = ca._river_outlet_doctor_row(_census(KEEP + 1), _stones(0), None, NOW)
        self.assertIs(row["ok"], False, row)
        self.assertIn("UNMEASURED", row["detail"])
        self.assertIn("names could not be read", row["detail"])
        self.assertNotIn("not a shut outlet", row["detail"])

    def test_a_name_with_no_age_is_not_a_pass(self):
        rows = [_reel(NOW - 3600 * 1000 - i * 1000, i) for i in range(KEEP)]
        rows.append({"reel": "reel_backup_junk"})
        row = ca._river_outlet_doctor_row(_census(len(rows)), _stones(0), rows, NOW)
        self.assertIs(row["ok"], False, row)
        self.assertIn("UNMEASURED", row["detail"])
        self.assertIn("carry no age", row["detail"])
        self.assertNotIn("not a shut outlet", row["detail"])
        self.assertNotIn("are older than", row["detail"])

    def test_a_fixture_is_not_his_footage(self):
        rows = [_reel(NOW - 10 * 86400000 - i * 1000, i, "test-fixture")
                for i in range(KEEP + 1)]
        row = ca._river_outlet_doctor_row(_census(len(rows)), _stones(0), rows, NOW)
        self.assertIs(row["ok"], True, row)
        self.assertIn("not a shut outlet", row["detail"])
        self.assertNotIn("are older than", row["detail"])
        self.assertNotIn("fix", row)

    def test_an_empty_shelf_is_not_a_shut_outlet(self):
        row = ca._river_outlet_doctor_row(_census(0), _stones(0), [], NOW)
        self.assertIs(row["ok"], True, row)
        self.assertIn("nothing has piled up", row["detail"])
        self.assertNotIn("are older than", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])
        self.assertNotIn("fix", row)

    def test_the_row_does_not_ask_may(self):
        for fn in (ca._river_outlet_doctor_row, ca._river_outlet_ask, ca._river_outlet_lifetime):
            src = inspect.getsource(fn)
            self.assertNotIn("self_arming", src)
            self.assertNotIn(".may(", src)

    def test_the_doctor_payload_carries_the_row(self):
        now = int(time.time() * 1000)
        rows = _outside(now)
        asked = []

        def ask():
            asked.append(1)
            return _census(len(rows)), {"ok": True, "reels": 0}, rows

        with mock.patch.object(ca, "fleet_origin_status",
                                lambda force_fetch=False: {"ok": True, "behind": 0, "head": "x", "howTo": ""}), \
                mock.patch.object(ca, "_reels_missing_index", lambda hist=None: []), \
                mock.patch.object(ca, "_screen_recording_ok_quick", lambda: True), \
                mock.patch.object(ca, "_one_capture_check",
                                  lambda alive=None: ca._chk("one_capture", True, "warn", "stub")), \
                mock.patch.object(ca, "_one_of_each_check",
                                  lambda: ca._chk("one_of_each", True, "warn", "stub")), \
                mock.patch.object(ca, "_river_outlet_ask", ask), \
                mock.patch.object(ca, "_extract_moving_facts",
                                  lambda: {"owed": 0, "memory": "absent", "ageKnown": True}):
            got = ca.doctor_payload()
        self.assertEqual(asked, [1])
        got_rows = _rows(got["checks"])
        self.assertIn("river_outlet", got_rows)
        row = got_rows["river_outlet"]
        self.assertIs(row["ok"], False, row)
        self.assertEqual(row["severity"], "warn")
        self.assertIn("0 lifetime tombstones", row["detail"])
        self.assertIn("are older than %d days" % ca.RIVER_OUTLET_OLD_DAYS, row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])
        self.assertIn("fix", row)
        self.assertNotEqual(row["severity"], "block")


RED_PROOF = [
    {"why": "REG-1785 - old reels and zero tombstones are reported as a pass, so the doctor stays green while the outlet never fired",
     "file": "control_app.py",
     "find": "    return _chk(\n"
             "        \"river_outlet\", False, \"warn\",\n"
             "        \"%d reel(s) on disk are older than %d days and outside the newest %d, \"\n"
             "        \"and this console has 0 lifetime tombstones%s%s\" % (\n",
     "replace": "    return _chk(\n"
                "        \"river_outlet\", True, \"warn\",\n"
                "        \"%d reel(s) on disk are older than %d days and outside the newest %d, \"\n"
                "        \"and this console has 0 lifetime tombstones%s%s\" % (\n",
     "matches": 1},
    {"why": "REG-1785 - an outlet that could not be read reads as a pass",
     "file": "control_app.py",
     "find": "    return _chk(\n"
             "        \"river_outlet\", False, \"warn\",\n"
             "        \"UNMEASURED: %s - not a river that has closed a reel out\" % why)\n",
     "replace": "    return _chk(\n"
                "        \"river_outlet\", True, \"warn\",\n"
                "        \"the outlet has closed a reel out (%s)\" % why)\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
