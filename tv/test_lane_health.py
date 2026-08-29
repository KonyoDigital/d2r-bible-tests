#!/usr/bin/env python3
"""Guards for lane health. Every one asserts a REFUSAL as well as a pass — the thing being replaced
is a watchdog that stayed silent for five days, so silence must never be a pass here."""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lane_health as LH

HOUR = 3600000.0


class _Tree(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="lane-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self._here = LH.HERE
        LH.HERE = self.root
        self.addCleanup(setattr, LH, "HERE", self._here)
        self.now = 1_000_000 * HOUR

    def _write(self, name, blob):
        with io.open(os.path.join(self.root, name), "w", encoding="utf-8") as fh:
            json.dump(blob, fh)

    def _seal(self, n, hours_ago):
        return {"s_%d" % i: {"ts": self.now - hours_ago * HOUR, "rows": 1} for i in range(n)}


class TestFreshness(_Tree):
    def test_a_lane_that_worked_recently_is_FRESH(self):
        self._write("chronicle_swept.json", self._seal(3, 2))
        self.assertEqual(LH.lane("chronicle", self.now)["state"], "fresh")

    def test_a_lane_past_its_threshold_is_STALLED_and_says_how_long(self):
        self._write("vault_swept.json", self._seal(8, 136.7))
        r = LH.lane("vault", self.now)
        self.assertEqual(r["state"], "stalled")
        self.assertAlmostEqual(r["ageHours"], 136.7, places=0)
        self.assertIn("STOPPED", r["why"])

    def test_an_UNREADABLE_store_is_UNKNOWN_never_healthy(self):
        # ⚠ the whole point: "cannot tell" must not read the same as "fine"
        with io.open(os.path.join(self.root, "vault_swept.json"), "w", encoding="utf-8") as fh:
            fh.write("{not json")
        r = LH.lane("vault", self.now)
        self.assertEqual(r["state"], "unknown")
        self.assertIn("never healthy", r["why"])

    def test_a_MISSING_store_is_UNKNOWN_not_fresh(self):
        self.assertEqual(LH.lane("vault", self.now)["state"], "unknown")

    def test_seals_with_NO_TIMESTAMP_are_UNKNOWN_not_fresh(self):
        # a lane with 40 sealed rows and no clock cannot answer "how long ago"
        self._write("vault_swept.json", {"s_%d" % i: {"rows": 1} for i in range(40)})
        r = LH.lane("vault", self.now)
        self.assertEqual(r["state"], "unknown")
        self.assertIn("unanswerable", r["why"])


class TestDivergenceIsTheCorroborator(_Tree):
    def test_one_lane_ahead_of_the_other_is_DIVERGED_and_names_the_deleter(self):
        self._write("chronicle_swept.json", self._seal(36, 49))
        self._write("vault_swept.json", {"s_0": {"ts": self.now, "rows": 1}})
        d = LH.divergence("chronicle", "vault")
        self.assertEqual(d["state"], "diverged")
        self.assertEqual(d["onlyInFirst"], 35)
        self.assertIn("frame deleter", d["why"])

    def test_lanes_covering_the_same_sessions_are_ALIGNED(self):
        same = self._seal(5, 1)
        self._write("chronicle_swept.json", same)
        self._write("vault_swept.json", same)
        self.assertEqual(LH.divergence("chronicle", "vault")["state"], "aligned")

    def test_divergence_with_an_unreadable_side_is_UNKNOWN(self):
        self._write("chronicle_swept.json", self._seal(3, 1))
        self.assertEqual(LH.divergence("chronicle", "vault")["state"], "unknown")

    def test_divergence_is_DIRECTIONAL(self):
        # vault ahead of chronicle is a different fact and must not read as the same defect
        self._write("chronicle_swept.json", {"s_0": {"ts": self.now, "rows": 1}})
        self._write("vault_swept.json", self._seal(9, 1))
        self.assertEqual(LH.divergence("chronicle", "vault")["state"], "aligned")
        self.assertEqual(LH.divergence("vault", "chronicle")["state"], "diverged")


class TestTheReportRefusesToBeGreenOnAnyProblem(_Tree):
    def test_everything_fresh_and_aligned_is_ok(self):
        same = self._seal(4, 1)
        self._write("chronicle_swept.json", same)
        self._write("vault_swept.json", same)
        self.assertTrue(LH.report(self.now)["ok"])

    def test_ONE_stalled_lane_makes_the_whole_report_not_ok(self):
        self._write("chronicle_swept.json", self._seal(4, 1))
        self._write("vault_swept.json", self._seal(4, 200))
        self.assertFalse(LH.report(self.now)["ok"])

    def test_a_DIVERGENCE_ALONE_makes_it_not_ok_even_when_both_lanes_are_fresh(self):
        # ⚠ this is the exact shape that hid the five-day stall: each lane correct on its own
        self._write("chronicle_swept.json", self._seal(9, 1))
        self._write("vault_swept.json", {"s_0": {"ts": self.now, "rows": 1}})
        rep = LH.report(self.now)
        self.assertTrue(all(l["state"] == "fresh" for l in rep["lanes"].values()))
        self.assertFalse(rep["ok"], "both lanes fresh but diverged, and the report called it ok")

    def test_it_writes_nothing(self):
        import inspect
        src = inspect.getsource(LH)
        for forbidden in ('open(', "os.remove", "unlink", "rmtree"):
            if forbidden == 'open(' and 'io.open' in src:
                continue          # io.open for READING is the module's whole job
            self.assertNotIn(forbidden, src, "lane_health must stay a reader; found %r" % forbidden)
        self.assertNotIn('"w"', src, "lane_health opened something for writing")


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
