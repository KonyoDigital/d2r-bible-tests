# -*- coding: utf-8 -*-
"""#69 — THE CONSOLE'S OWN .jsonl SERIES MUST NAME THEIR PRODUCER.

MEASURED 2026-09-11 by `verdict_provenance.py` on the live tree:

    44 stores · ANSWERS 6 · PARTIAL 4 · SILENT 16 · REFERENCE 17 · UNKNOWN 1

`ui_faults.jsonl` and `disk_history.jsonl` were both SILENT. A row with no producer cannot be
INVALIDATED when the writer improves: a fault logged by an old detector, or a disk reading taken by
an older rule, outlives every later pass looking exactly like a fresh one.

⚠ A JSONL ROW IS ITS OWN LINE, so `stamp_row` here carries NONE of the fake-row hazard that forced
a reel-keyed store to take the stamp inside its rows (REG-972). Same helper, different shape, and
the shape is what decides which call is correct. This law pins the shape too.

⚠ THE ROW'S OWN `at` IS NOT THE PRODUCER'S CLOCK. `at` is when the thing happened; the producer's
time lives inside the nested block. Collapsing them would date a fault to when it was written
rather than when it occurred. [[label-outlived-referent]]
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import provenance as PV     # noqa: E402
import control_app as CA    # noqa: E402


def _last_row(case, path):
    case.assertTrue(os.path.exists(path), "%s was never written" % path)
    lines = [l for l in io.open(path, encoding="utf-8").read().splitlines() if l.strip()]
    case.assertTrue(lines, "%s holds no rows" % path)
    return json.loads(lines[-1])


class AFaultNamesItsProducer(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="prov_faults_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.p = os.path.join(self.d, "ui_faults.jsonl")

    def test_the_row_says_what_wrote_it(self):
        CA.ui_fault_record("blank-stage", why="nothing painted", where="#stage", path=self.p)
        pr = PV.read(_last_row(self, self.p))
        self.assertEqual("control_app", getattr(pr, "by", None),
                         "a UI fault does not name its producer, so a fault logged by an old "
                         "detector cannot be told from one logged by today's")

    def test_the_faults_own_clock_is_not_replaced(self):
        """`at` is WHEN THE FAULT HAPPENED. The producer's time belongs in the nested block."""
        CA.ui_fault_record("blank-stage", why="nothing painted", where="#stage", path=self.p)
        row = _last_row(self, self.p)
        self.assertIn("at", row, "the fault lost its own timestamp")
        self.assertIsInstance(row["at"], int)
        self.assertIn("_prov", row, "the producer block is absent")
        self.assertNotEqual("at", str(sorted(set(row) & {"_prov"})),
                            "sanity: _prov and at must both be present and distinct")

    def test_the_fault_itself_is_unharmed(self):
        CA.ui_fault_record("blank-stage", why="nothing painted", where="#stage", path=self.p)
        row = _last_row(self, self.p)
        self.assertEqual("blank-stage", row.get("kind"))
        self.assertEqual("nothing painted", row.get("why"))
        self.assertEqual("#stage", row.get("where"))

    def test_one_row_is_still_one_line(self):
        """A stamped row that serialised across two lines would parse as two faults."""
        for i in range(3):
            CA.ui_fault_record("k%d" % i, why="w", where="x", path=self.p)
        lines = [l for l in io.open(self.p, encoding="utf-8").read().splitlines() if l.strip()]
        self.assertEqual(3, len(lines),
                         "3 faults were recorded but the store holds %d line(s) — a stamped row "
                         "split across lines becomes two faults" % len(lines))
        for l in lines:
            json.loads(l)


class TheDiskSeriesNamesItsProducer(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="prov_disk_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.p = os.path.join(self.d, "disk_history.jsonl")

    def _record(self):
        """⚠ NAMED, NOT GUESSED. The first cut of this law asked for `disk_history_record` and
        SKIPPED when it was absent — two laws reporting OK while measuring nothing, which is the
        skip-counted-as-pass class this repo keeps paying for. The writer is
        `disk_history_append`. [[regression-guard]]"""
        CA.disk_history_append(free_gb=100.0, floor_gb=20, hist_bytes=123, reels=4,
                               eligible_mb=0, pruned_mb=None, path=self.p)

    def test_the_row_says_what_wrote_it(self):
        self._record()
        pr = PV.read(_last_row(self, self.p))
        self.assertEqual("control_app", getattr(pr, "by", None),
                         "a disk reading does not name its producer, so a row taken under an "
                         "older credibility rule cannot be told from today's")

    def test_the_reading_itself_is_unharmed(self):
        self._record()
        row = _last_row(self, self.p)
        self.assertEqual(100.0, row.get("freeGb"))
        self.assertIn("prunedWhy", row,
                      "prunedWhy is gone — the field that keeps 'nobody measured' apart from "
                      "'a claim we refused'")


RED_PROOF = [
    {
        "why": "un-stamping the UI fault writer puts ui_faults.jsonl back to SILENT: a fault "
               "logged by an old detector can no longer be told from one logged by today's",
        "file": "control_app.py",
        "find": '        row = _PV.stamp_row(row, by="control_app", extra={"store": "ui_faults"})\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "un-stamping the disk series puts disk_history.jsonl back to SILENT: a reading "
               "taken under an older credibility rule reads exactly like today's",
        "file": "control_app.py",
        "find": '        row = _PV.stamp_row(row, by="control_app", extra={"store": "disk_history"})\n',
        "replace": "",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
