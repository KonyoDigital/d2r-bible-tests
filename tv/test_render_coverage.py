"""v2475 — the render gate can now notice its own coverage shrinking.

⚠ THE GAP THIS CLOSES, in TASKS.md's own words under STILL OWED BY ME:

    "The render gate does not cover what I changed. The `console` target went 3/3 -> 2/2 when a
     control was hidden and RE-BASELINED SILENTLY... Unmeasured reads identical to clean in a
     green run."

That is tv/render_check.py's own thesis turned on itself. It refuses a zero-size element, a black
capture, an unsettled page, a dropped socket — every way ONE reading can lie — and had no way to
notice it was taking FEWER readings than before. A control that disappears takes its own check with
it, and two clean measurements are two clean measurements.

The ratchet is tv/swallow_census.py's, INVERTED: that one counts a defect and may only fall; this
counts COVERAGE and may only rise.

⚠ WHAT I COULD NOT ESTABLISH, said plainly rather than guessed. The console target's selector has
been `#btn-mini, #btn-miniauto` since it was introduced in v2378 — measured with
`git log -L '/"sel": "#btn-mini/,+1:tv/render_check.py'`, one commit, no edits. So the 3 -> 2 drop
was a change in the DOM, not in the spec: two ID selectors matching three nodes means a duplicate
id existed, and losing it was most likely a FIX rather than a loss. I did not confirm that, so the
floor blessed today records 2 and this file does not claim to know what the third node was.
The ratchet stops the NEXT silent drop; it cannot recover one that already happened.
"""
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable  # noqa: E402

enable()

import render_check as R  # noqa: E402


def _run(**widths):
    """A fake per-target result in the shape main() accumulates."""
    return {"ok": True, "why": "", "refusals": [],
            "widths": {k: {"found": v, "painted": v} for k, v in widths.items()}}


class TheRatchetRefusesAShrink(unittest.TestCase):

    def setUp(self):
        self._real = R.COVERAGE
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        R.COVERAGE = self.path
        self.said = []

    def tearDown(self):
        R.COVERAGE = self._real
        try:
            os.unlink(self.path)
        except Exception:
            pass

    def _say(self, m):
        self.said.append(m)

    def _floor(self, d):
        io.open(self.path, "w", encoding="utf-8").write(json.dumps({"floor": d}))

    def test_a_dropped_node_count_is_refused(self):
        """The whole point: 3 -> 2 must not be a green run."""
        self._floor({"console": {"1120x628": 3}})
        bad = R._coverage_check({"console": _run(**{"1120x628": 2})}, self._say)
        self.assertEqual(bad, 1, "a target measuring 2 nodes where its floor says 3 was accepted")
        self.assertTrue(any("was 3" in m and "console" in m for m in self.said),
                        "the refusal does not name both numbers: %s" % self.said)

    def test_an_unchanged_count_passes(self):
        self._floor({"console": {"1120x628": 2}})
        self.assertEqual(R._coverage_check({"console": _run(**{"1120x628": 2})}, self._say), 0)

    def test_growth_passes_and_is_reported(self):
        """Coverage may rise freely — and it says so, or nobody re-blesses."""
        self._floor({"console": {"1120x628": 2}})
        bad = R._coverage_check({"console": _run(**{"1120x628": 5})}, self._say)
        self.assertEqual(bad, 0, "coverage growing was treated as a failure")
        self.assertTrue(any("grew" in m for m in self.said),
                        "growth was silent, so the floor would never be raised: %s" % self.said)

    def test_a_target_that_stops_reporting_entirely_is_refused(self):
        """A surface that vanishes from the run is UNMEASURED, not clean."""
        self._floor({"console": {"1120x628": 2}, "vault": {"1120x628": 11}})
        bad = R._coverage_check({"console": _run(**{"1120x628": 2})}, self._say)
        self.assertEqual(bad, 1, "a target absent from the whole run was accepted")
        self.assertTrue(any("vault" in m for m in self.said))

    def test_a_width_that_stops_being_measured_is_refused(self):
        """Dropping a viewport is dropping coverage, even if the rest is clean."""
        self._floor({"console": {"1120x628": 2, "375x800": 2}})
        bad = R._coverage_check({"console": _run(**{"1120x628": 2})}, self._say)
        self.assertEqual(bad, 1, "a width silently disappearing was accepted")
        self.assertTrue(any("375x800" in m for m in self.said))

    def test_an_absent_floor_is_UNKNOWN_not_zero(self):
        """No file must not mean 'everything is fine'. [[unknown-stays-unknown]]"""
        os.unlink(self.path)
        self.assertIsNone(R._coverage_floor())
        bad = R._coverage_check({"console": _run(**{"1120x628": 2})}, self._say)
        self.assertEqual(bad, 0, "an absent floor should not fail a run")
        self.assertTrue(any("UNKNOWN" in m for m in self.said),
                        "an absent floor was silently treated as satisfied: %s" % self.said)


class BlessingIsNotAWayToLowerTheBar(unittest.TestCase):

    def setUp(self):
        self._real = R.COVERAGE
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        R.COVERAGE = self.path
        self.said = []

    def tearDown(self):
        R.COVERAGE = self._real
        try:
            os.unlink(self.path)
        except Exception:
            pass

    def _say(self, m):
        self.said.append(m)

    def test_a_partial_run_may_not_write_a_floor(self):
        """One busy afternoon must not become the new normal."""
        rc = R._coverage_bless({"console": _run(**{"1120x628": 1})}, False, self._say)
        self.assertEqual(rc, 2, "a run that did not report every target was allowed to bless")
        self.assertFalse(os.path.getsize(self.path),
                         "a refused bless still wrote the floor file")

    def test_a_clean_run_writes_and_MERGES_rather_than_replacing(self):
        """A target absent from this run keeps its old floor instead of vanishing from the file."""
        io.open(self.path, "w", encoding="utf-8").write(
            json.dumps({"floor": {"vault": {"1120x628": 11}}}))
        rc = R._coverage_bless({"console": _run(**{"1120x628": 2})}, True, self._say)
        self.assertEqual(rc, 0)
        got = json.load(io.open(self.path, encoding="utf-8"))["floor"]
        self.assertIn("vault", got,
                      "blessing dropped a target that was not in this run — the floor may only be "
                      "lowered deliberately, never by omission")
        self.assertEqual(got["console"]["1120x628"], 2)


class TheFloorInTheRepoIsReal(unittest.TestCase):

    def test_it_exists_and_covers_every_target(self):
        """A floor missing a target is a target nobody would notice losing."""
        floor = R._coverage_floor()
        self.assertIsNotNone(
            floor, "tv/render_coverage.json is missing — run: python3 tv/render_check.py --bless")
        missing = sorted(set(R.TARGETS) - set(floor))
        self.assertEqual(missing, [],
                         "these render targets have no coverage floor, so losing them would be "
                         "invisible: %s" % missing)

    def test_every_floor_entry_is_a_positive_count(self):
        """A floor of 0 ratchets nothing — it is the absent case wearing a number."""
        floor = R._coverage_floor() or {}
        zero = ["%s/%s" % (t, w) for t in floor for w, n in floor[t].items() if not n]
        self.assertEqual(zero, [],
                         "these floors are 0, which permits the surface to vanish entirely: %s"
                         % zero)


if __name__ == "__main__":
    unittest.main(verbosity=2)
