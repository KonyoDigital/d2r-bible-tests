# -*- coding: utf-8 -*-
"""REG-1788 — AN OWED REEL WITH NO EXTRACT MEMORY IS NOT MOVING.

/api/doctor never asked whether a reel that still owes a chronicle read had a sweep
memory. The eagle already calls a never-written memory MISSING. This payload had no
row. Zero owed is a pass, even when the file is absent. Owed reels and a file that
was never written is a warn. A file whose clock is strictly before the oldest owed
reel is the same warn. An equal clock is not older. One owed reel with no capture
clock makes the age unknown. Anything that will not read is UNMEASURED.

  · DRIVEN: the row, on facts, never opens his shelf.
  · DRIVEN: the gather stats a path it is handed and does not write the memory.
  · DRIVEN: the payload he is served carries the row.

Nothing here writes chronicle_swept.json or walks his footage. RED_PROOF below.
[[unknown-stays-unknown]] [[copy-drift]]
"""
import inspect
import json
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


OLD = 1700000000000
NEW = 1700000005000


def _facts(**over):
    base = {
        "owed": 0,
        "memory": "absent",
        "memoryMtimeMs": None,
        "oldestMs": None,
        "ageKnown": True,
    }
    base.update(over)
    return base


class AnOwedReelWithNoExtractMemoryIsNotMoving(unittest.TestCase):

    def test_zero_owed_passes_even_when_the_file_was_never_written(self):
        row = ca._extract_moving_doctor_row(_facts(owed=0, memory="absent"))
        self.assertIs(row["ok"], True, row)
        self.assertIn("0 reels owe a read", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])
        self.assertNotIn("older than", row["detail"])
        self.assertNotIn("fix", row)

    def test_an_owed_reel_with_no_extract_memory_is_not_moving(self):
        row = ca._extract_moving_doctor_row(_facts(owed=3, memory="absent", ageKnown=False))
        self.assertIs(row["ok"], False, row)
        self.assertEqual(row["severity"], "warn")
        self.assertIn("3 reel(s) owe a read", row["detail"])
        self.assertIn("no extract memory has ever been written", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])
        self.assertIn("does not write", row["fix"])

    def test_a_memory_older_than_the_oldest_owed_reel_is_not_moving(self):
        row = ca._extract_moving_doctor_row(_facts(
            owed=2, memory="present", ageKnown=True,
            oldestMs=OLD, memoryMtimeMs=OLD - 1))
        self.assertIs(row["ok"], False, row)
        self.assertIn("extract memory is older than the oldest owed reel", row["detail"])
        self.assertIn("2 reel(s) owe a read", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])

    def test_an_equal_clock_is_not_older(self):
        row = ca._extract_moving_doctor_row(_facts(
            owed=1, memory="present", ageKnown=True,
            oldestMs=OLD, memoryMtimeMs=OLD))
        self.assertIs(row["ok"], True, row)
        self.assertIn("not older than the oldest", row["detail"])
        self.assertNotIn("extract memory is older", row["detail"])
        self.assertNotIn("fix", row)

    def test_a_newer_memory_still_passes(self):
        row = ca._extract_moving_doctor_row(_facts(
            owed=1, memory="present", ageKnown=True,
            oldestMs=OLD, memoryMtimeMs=NEW))
        self.assertIs(row["ok"], True, row)
        self.assertNotIn("extract memory is older", row["detail"])

    def test_one_reel_with_no_clock_makes_the_age_unknown(self):
        row = ca._extract_moving_doctor_row(_facts(
            owed=2, memory="present", ageKnown=False,
            oldestMs=OLD, memoryMtimeMs=NEW))
        self.assertIs(row["ok"], False, row)
        self.assertIn("UNMEASURED", row["detail"])
        self.assertIn("no capture clock", row["detail"])
        self.assertNotIn("extract memory is older than the oldest owed reel", row["detail"])
        self.assertNotIn("has ever been written", row["detail"])

    def test_a_missing_count_is_not_zero(self):
        for owed in (None, True, False, 1.5, -1, "3"):
            row = ca._extract_moving_doctor_row(_facts(owed=owed))
            self.assertIs(row["ok"], False, owed)
            self.assertIn("UNMEASURED", row["detail"])
            self.assertIn("was not counted", row["detail"])
            self.assertNotIn("0 reels owe a read", row["detail"])

    def test_an_unreadable_memory_is_not_a_missing_file(self):
        row = ca._extract_moving_doctor_row(_facts(owed=4, memory="unreadable"))
        self.assertIs(row["ok"], False, row)
        self.assertIn("UNMEASURED", row["detail"])
        self.assertIn("could not be read", row["detail"])
        self.assertNotIn("has ever been written", row["detail"])

    def test_a_clock_that_is_not_a_filmed_time_is_not_a_pass(self):
        for oldest in (None, True, OLD - 10 ** 12, 1.0):
            row = ca._extract_moving_doctor_row(_facts(
                owed=1, memory="present", ageKnown=True,
                oldestMs=oldest, memoryMtimeMs=NEW))
            self.assertIs(row["ok"], False, oldest)
            self.assertIn("UNMEASURED", row["detail"])
            self.assertNotIn("not older than", row["detail"])

    def test_a_memory_clock_that_is_not_an_int_is_not_a_pass(self):
        for mtime in (None, True, float(OLD)):
            row = ca._extract_moving_doctor_row(_facts(
                owed=1, memory="present", ageKnown=True,
                oldestMs=OLD, memoryMtimeMs=mtime))
            self.assertIs(row["ok"], False, mtime)
            self.assertIn("UNMEASURED", row["detail"])
            self.assertNotIn("extract memory is older", row["detail"])

    def test_facts_that_are_not_a_dict_are_not_a_pass(self):
        row = ca._extract_moving_doctor_row(None)
        self.assertIs(row["ok"], False, row)
        self.assertIn("did not come back", row["detail"])

    def test_the_row_does_not_read_or_write_the_memory(self):
        src = inspect.getsource(ca._extract_moving_doctor_row)
        self.assertNotIn("_chron_swept_path(", src)
        self.assertNotIn("_chron_owed_count(", src)
        self.assertNotIn("open(", src)
        gather = inspect.getsource(ca._extract_moving_facts)
        self.assertNotIn("_chron_owed_count(", gather)
        self.assertNotIn("_chron_swept_save(", gather)
        self.assertNotIn("_json_store_load(", gather)
        self.assertNotIn("_chron_swept_mem(", gather)

    def test_the_gather_reports_an_absent_file_and_does_not_create_one(self):
        d = tempfile.mkdtemp(prefix="extract_absent_")
        self.addCleanup(__import__("shutil").rmtree, d, True)
        path = os.path.join(d, "chronicle_swept.json")
        name = "reel_s_%d_1" % OLD
        before = set(ca._UNREADABLE)

        def owes(rid, mem=None, prompt_ver=None):
            return True

        with mock.patch.object(ca, "_chron_swept_path", lambda: path), \
                mock.patch.object(ca, "_chron_reel_owes_a_read", owes), \
                mock.patch("chronicle_retro.reel_dirs",
                           lambda *a, **k: [os.path.join(d, name)]):
            facts = ca._extract_moving_facts()
        self.assertFalse(os.path.exists(path))
        self.assertEqual(set(ca._UNREADABLE), before)
        self.assertEqual(facts["owed"], 1)
        self.assertEqual(facts["memory"], "absent")
        self.assertIs(facts["ageKnown"], True)
        self.assertEqual(facts["oldestMs"], OLD)
        row = ca._extract_moving_doctor_row(facts)
        self.assertIs(row["ok"], False, row)
        self.assertIn("has ever been written", row["detail"])

    def test_one_nameless_clock_keeps_the_parseable_reel_out_of_the_age(self):
        d = tempfile.mkdtemp(prefix="extract_age_")
        self.addCleanup(__import__("shutil").rmtree, d, True)
        path = os.path.join(d, "chronicle_swept.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({}, fh)
        os.utime(path, (time.time(), time.time()))
        names = ["reel_s_%d_1" % OLD, "reel_not_a_clock"]

        with mock.patch.object(ca, "_chron_swept_path", lambda: path), \
                mock.patch.object(ca, "_chron_reel_owes_a_read",
                                  lambda rid, mem=None, prompt_ver=None: True), \
                mock.patch("chronicle_retro.reel_dirs",
                           lambda *a, **k: [os.path.join(d, n) for n in names]):
            facts = ca._extract_moving_facts()
        self.assertEqual(facts["owed"], 2)
        self.assertEqual(facts["memory"], "present")
        self.assertIs(facts["ageKnown"], False)
        self.assertIsNone(facts["oldestMs"])
        row = ca._extract_moving_doctor_row(facts)
        self.assertIs(row["ok"], False, row)
        self.assertIn("UNMEASURED", row["detail"])
        self.assertNotIn("extract memory is older than the oldest owed reel", row["detail"])

    def test_a_torn_file_is_unreadable_and_is_left_byte_for_byte(self):
        d = tempfile.mkdtemp(prefix="extract_torn_")
        self.addCleanup(__import__("shutil").rmtree, d, True)
        path = os.path.join(d, "chronicle_swept.json")
        raw = "{not json"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(raw)
        before = set(ca._UNREADABLE)
        with mock.patch.object(ca, "_chron_swept_path", lambda: path):
            facts = ca._extract_moving_facts()
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), raw)
        self.assertEqual(set(ca._UNREADABLE), before)
        self.assertIsNone(facts["owed"])
        self.assertEqual(facts["memory"], "unreadable")
        row = ca._extract_moving_doctor_row(facts)
        self.assertIs(row["ok"], False, row)
        self.assertIn("could not be read", row["detail"])

    def test_a_memory_older_on_disk_reaches_the_row(self):
        d = tempfile.mkdtemp(prefix="extract_old_")
        self.addCleanup(__import__("shutil").rmtree, d, True)
        path = os.path.join(d, "chronicle_swept.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"other": {"pages": 1}}, fh)
        os.utime(path, (OLD / 1000.0 - 50, OLD / 1000.0 - 50))
        name = "reel_s_%d_1" % OLD
        with mock.patch.object(ca, "_chron_swept_path", lambda: path), \
                mock.patch.object(ca, "_chron_reel_owes_a_read",
                                  lambda rid, mem=None, prompt_ver=None: True), \
                mock.patch("chronicle_retro.reel_dirs",
                           lambda *a, **k: [os.path.join(d, name)]):
            facts = ca._extract_moving_facts()
        self.assertEqual(facts["memory"], "present")
        self.assertLess(facts["memoryMtimeMs"], facts["oldestMs"])
        row = ca._extract_moving_doctor_row(facts)
        self.assertIs(row["ok"], False, row)
        self.assertIn("extract memory is older than the oldest owed reel", row["detail"])

    def test_the_doctor_payload_carries_the_row(self):
        asked = []

        def facts():
            asked.append(1)
            return _facts(owed=3, memory="absent")

        with mock.patch.object(ca, "fleet_origin_status",
                                lambda force_fetch=False: {"ok": True, "behind": 0, "head": "x", "howTo": ""}), \
                mock.patch.object(ca, "_reels_missing_index", lambda hist=None: []), \
                mock.patch.object(ca, "_screen_recording_ok_quick", lambda: True), \
                mock.patch.object(ca, "_screen_recording_probe", lambda: True), \
                mock.patch.object(ca, "_one_capture_check",
                                  lambda alive=None: ca._chk("one_capture", True, "warn", "stub")), \
                mock.patch.object(ca, "_one_of_each_check",
                                  lambda: ca._chk("one_of_each", True, "warn", "stub")), \
                mock.patch.object(ca, "_river_outlet_ask",
                                  lambda: ({"ok": True, "onDisk": 0}, {"ok": True, "reels": 0}, [])), \
                mock.patch.object(ca, "_extract_moving_facts", facts):
            got = ca.doctor_payload()
        self.assertEqual(asked, [1])
        row = next(c for c in got["checks"] if c["id"] == "extract_moving")
        self.assertIs(row["ok"], False, row)
        self.assertEqual(row["severity"], "warn")
        self.assertIn("no extract memory has ever been written", row["detail"])
        self.assertNotIn("UNMEASURED", row["detail"])
        self.assertNotEqual(row["severity"], "block")


RED_PROOF = [
    {"why": "REG-1788 - owed reels and a memory that was never written read as a pass",
     "file": "control_app.py",
     "find": "    if memory == \"absent\":\n"
             "        return _chk(\n"
             "            \"extract_moving\", False, \"warn\",\n"
             "            \"%d reel(s) owe a read and no extract memory has ever been written\" % owed,\n",
     "replace": "    if memory == \"absent\":\n"
                "        return _chk(\n"
                "            \"extract_moving\", True, \"warn\",\n"
                "            \"%d reel(s) owe a read and no extract memory has ever been written\" % owed,\n",
     "matches": 1},
    {"why": "REG-1788 - an extract that could not be read reads as a pass",
     "file": "control_app.py",
     "find": "    return _chk(\n"
             "        \"extract_moving\", False, \"warn\",\n"
             "        \"UNMEASURED: %s - not an extract that is moving\" % why)\n",
     "replace": "    return _chk(\n"
                "        \"extract_moving\", True, \"warn\",\n"
                "        \"UNMEASURED: %s - not an extract that is moving\" % why)\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
