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


class TheRatchetIsActuallyJOINEDToTheVerdict(unittest.TestCase):
    """⚠⚠ EVERY OTHER TEST IN THIS FILE CALLS `_coverage_check` DIRECTLY, SO NOTHING GUARDED THE
    JOIN. The ratchet could be correct in every case and never consulted by the run that decides
    the exit code — [[the-unjoined-end]], the defect class this repo repeats most. Gate the call
    behind `if False:` and all of this file stays green while a vanished surface ships.

    It also pins the SEPARATION that v2481 introduced: coverage refusals must not be added to the
    render-failure counter. Mixing them made `clean = len(targets) - bad` go NEGATIVE and skipped
    both branches that exist to say 'nothing was established'.
    """

    def setUp(self):
        self._realcov, self._realup, self._realdown, self._realcheck = (
            R.COVERAGE, R._chrome_up, R._chrome_down, R.check)
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        R.COVERAGE = self.path
        R._chrome_up = lambda *a, **k: True
        R._chrome_down = lambda *a, **k: None

    def tearDown(self):
        R.COVERAGE, R._chrome_up, R._chrome_down, R.check = (
            self._realcov, self._realup, self._realdown, self._realcheck)
        try:
            os.unlink(self.path)
        except Exception:
            pass

    def _main(self):
        """Run main([]) with every target rendering CLEAN, capturing what it printed."""
        out = []
        import builtins
        real = builtins.print
        builtins.print = lambda *a, **k: out.append(" ".join(str(x) for x in a))
        try:
            rc = R.main([])
        finally:
            builtins.print = real
        return rc, "\n".join(out)

    def test_main_consults_the_ratchet_and_a_shrink_fails_the_RUN(self):
        # a floor demanding a width nobody will report, for a target that DOES render clean
        name = sorted(R.TARGETS)[0]
        io.open(self.path, "w", encoding="utf-8").write(
            json.dumps({"floor": {name: {"1120x628": 99}}}))
        R.check = lambda *a, **k: _run(**{"1120x628": 1})
        rc, out = self._main()
        self.assertNotEqual(rc, 0,
                            "main() exited 0 while the coverage floor was not met — the ratchet "
                            "is not JOINED to the verdict, so it can be right and ignored.\n%s"
                            % out[-600:])

    def test_a_coverage_refusal_is_not_counted_as_a_render_failure(self):
        name = sorted(R.TARGETS)[0]
        io.open(self.path, "w", encoding="utf-8").write(
            json.dumps({"floor": {name: {"1120x628": 99}}}))
        R.check = lambda *a, **k: _run(**{"1120x628": 1})
        _rc, out = self._main()
        self.assertNotIn(
            "-", [w for w in out.split() if w.lstrip("-").isdigit() and w.startswith("-")] and "-" or "",
            "a negative count was printed")
        self.assertTrue(
            "COVERAGE refusal" in out or "ratchet expected" in out,
            "a coverage shortfall was not reported AS a coverage shortfall — it was folded into "
            "the render-failure count, which is how a dead browser printed 'did not render "
            "cleanly, LOOK AT THE PNGs' for PNGs that were never written.\n%s" % out[-600:])


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


class TheFloorMayOnlyRISE(unittest.TestCase):
    """⚠⚠ REG-568 — THE RATCHET DID NOT RATCHET. `render_coverage.json`'s own `_why` says *"It may
    only RISE"*, and `--bless` merged with a plain `dict.update()` — which OVERWRITES with whatever
    the run measured, including a LOWER number. Reproduced: a floor of 65 and a run measuring 12
    wrote **12**. So a bless after a real coverage loss silently adopted the loss as the new
    normal, which is exactly what the sentence above it promised could not happen.

    TASKS.md has carried this as still-owed since the `console` target went 3/3 -> 2/2 and was
    re-baselined with nobody noticing. **A floor that can be lowered by the thing it is measuring
    is not a floor.**
    """

    def _bless(self, old, now):
        import render_check as RC
        said, real_floor, real_of = [], RC._coverage_floor, RC._coverage_of
        bak = io.open(RC.COVERAGE, encoding="utf-8").read()
        try:
            RC._coverage_floor = lambda: old
            RC._coverage_of = lambda results: now
            RC._coverage_bless({}, True, said.append)
            written = json.loads(io.open(RC.COVERAGE, encoding="utf-8").read())["floor"]
        finally:
            RC._coverage_floor, RC._coverage_of = real_floor, real_of
            io.open(RC.COVERAGE, "w", encoding="utf-8").write(bak)
        return written, said

    def test_a_LOWER_measurement_does_not_lower_the_floor(self):
        written, said = self._bless({"heart": {"1440x1000": 65}}, {"heart": {"1440x1000": 12}})
        self.assertEqual(written["heart"]["1440x1000"], 65,
                         "a run measuring 12 wrote the floor DOWN from 65 — the loss became the "
                         "new normal, silently")
        self.assertTrue(any("HELD" in x for x in said),
                        "the floor held and said nothing, so a real coverage loss passes as a "
                        "clean bless: %s" % said)

    def test_a_HIGHER_measurement_still_raises_it(self):
        """⚠ BASELINE: or the fix froze the ratchet and new coverage could never be recorded."""
        written, _ = self._bless({"heart": {"1440x1000": 65}}, {"heart": {"1440x1000": 70}})
        self.assertEqual(written["heart"]["1440x1000"], 70,
                         "growth was refused too, so the floor can never rise again")

    def test_a_NEW_target_is_recorded_rather_than_ignored(self):
        written, _ = self._bless({"heart": {"1440x1000": 65}}, {"brand_new": {"1440x1000": 4}})
        self.assertEqual(written["brand_new"]["1440x1000"], 4,
                         "a target with no prior floor was not recorded at all")
        self.assertEqual(written["heart"]["1440x1000"], 65, "an untouched target lost its floor")


if __name__ == "__main__":
    unittest.main(verbosity=2)
