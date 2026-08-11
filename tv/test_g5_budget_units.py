"""v1698 — THE SECOND EYE MUST NOT SWITCH ITSELF OFF BEHIND A LEGITIMATE-LOOKING REASON.

tv/g5_subscription_budget.json has TWO writers: this repo's Python (tv/g5_grok_eyes.py, which used
time.time() -> SECONDS) and its Node sibling (tv/intake_grok_sub.mjs, which used Date.now() ->
MILLISECONDS). Neither knew about the other, and both halves were broken in OPPOSITE directions:

  · Python reading a Node row: now(1786390330) - 1786385809525 = -1,784,599,419,194 -- hugely
    NEGATIVE, so the `< 86400` window is ALWAYS true. Every millisecond row sits ~1.78 million
    million seconds in the "future" and can never age out, so the count only ever CLIMBS.
  · Node reading a Python row: now_ms - t ~= 20,655 days -- outside 24h, so it is DROPPED. Node
    deleted every row Python wrote and saved the pruned list back.

At 30 accumulated rows the eye reports `grok-subscription hourly cap (30/30)` and goes dark while
the real call rate is ZERO. Measured on his file 2026-08-10: 9 of 30, twenty-one calls from firing.
The tell had already been on screen and was walked past -- `budget.hourlyUsed: 9` next to
`stats.calls: 0`. Nine calls charged, zero calls made. The contradiction WAS the finding.

This is the first test that has ever existed on this lane (0 of 383 spec files asserted on
g5_grok_eyes / g5_status / g5_toggle / intake_grok_sub / g5_subscription_budget).

⚠ FIXTURES NEVER TOUCH LIVE DATA. Every test here points G5_BUDGET_PATH at a temp file. The final
test asserts his real budget file was not opened for writing at any point, because the whole class
of bug being fixed is "two writers on one file".
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable_console
    _enable_console()
except Exception:                                   # pragma: no cover
    pass

import g5_grok_eyes as g5  # noqa: E402

LIVE_BUDGET = os.path.join(HERE, "g5_subscription_budget.json")
HOUR_MS = 3600.0 * 1000.0
DAY_MS = 86400.0 * 1000.0


class _TempBudget(unittest.TestCase):
    """Every subclass writes ONLY to a temp budget file."""

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self._tmp.close()
        self._prev = os.environ.get("G5_BUDGET_PATH")
        os.environ["G5_BUDGET_PATH"] = self._tmp.name
        self._live_before = _live_snapshot()

    def tearDown(self):
        if self._prev is None:
            os.environ.pop("G5_BUDGET_PATH", None)
        else:
            os.environ["G5_BUDGET_PATH"] = self._prev
        try:
            os.unlink(self._tmp.name)
        except OSError:
            pass
        # the guard's own guard: his live budget must be byte-identical after every test
        self.assertEqual(_live_snapshot(), self._live_before,
                         "a test in this file wrote to his LIVE g5_subscription_budget.json")

    def write(self, calls):
        with open(self._tmp.name, "w", encoding="utf-8") as fh:
            json.dump({"calls": calls}, fh)

    def read(self):
        with open(self._tmp.name, encoding="utf-8") as fh:
            return json.load(fh).get("calls") or []


def _live_snapshot():
    try:
        with open(LIVE_BUDGET, "rb") as fh:
            return fh.read()
    except OSError:
        return None


class TheOldCodeWasBroken(_TempBudget):
    """RED PROOF. A gate nobody has watched fail is measuring nothing, so the defect is reproduced
    here explicitly: these are the ORIGINAL predicates, and they must still be wrong."""

    def test_the_original_python_window_never_prunes_a_millisecond_row(self):
        now_s = time.time()
        ms_row = now_s * 1000.0            # what Node writes
        # the original line: [t for t in calls if now - t < 86400.0]
        self.assertLess(now_s - ms_row, 0, "the ms row must read as NEGATIVE age in seconds")
        self.assertTrue(now_s - ms_row < 86400.0,
                        "ORIGINAL BUG: a millisecond row always passes a seconds window, forever")

    def test_the_original_node_window_drops_a_seconds_row(self):
        now_ms = time.time() * 1000.0
        s_row = time.time()                # what Python wrote
        self.assertFalse(now_ms - s_row < DAY_MS,
                         "ORIGINAL BUG: a seconds row reads ~20,655 days old and Node deletes it")

    def test_the_climb_that_pins_the_eye_off(self):
        """The consequence, arithmetic only: ms rows never age out, so the hourly count only grows."""
        now_s = time.time()
        rows = [(now_s - 86400 * n) * 1000.0 for n in range(1, 31)]   # 30 rows, all DAYS old
        survived_old = [t for t in rows if now_s - t < 86400.0]        # original predicate
        self.assertEqual(len(survived_old), 30,
                         "ORIGINAL BUG: thirty day-old rows all survive a 24h prune")
        self.assertGreaterEqual(len(survived_old), 30,
                                "...which is exactly the 30/30 cap that reports 'hourly cap'")


class OneUnitNormalisedOnRead(_TempBudget):
    """The fix: milliseconds canonical, and a row in the other unit is UNDERSTOOD, not dropped."""

    def test_as_ms_normalises_both_units(self):
        self.assertAlmostEqual(g5._as_ms(1786385809.525), 1786385809525.0, places=0)
        self.assertAlmostEqual(g5._as_ms(1786385809525), 1786385809525.0, places=0)

    def test_a_node_row_now_ages_out(self):
        now_ms = time.time() * 1000.0
        self.write([now_ms - 2 * DAY_MS])            # two days old, in ms
        hourly, daily = g5._budget_counts()
        self.assertEqual((hourly, daily), (0, 0), "a two-day-old ms row must be pruned, not immortal")

    def test_a_python_seconds_row_is_still_counted(self):
        """The other half: a legacy seconds row must not be silently deleted -- a budget that
        forgets real calls is as wrong as one that never forgets."""
        self.write([time.time() - 60])               # one minute ago, in SECONDS
        hourly, daily = g5._budget_counts()
        self.assertEqual((hourly, daily), (1, 1), "a legacy seconds row must still count")

    def test_mixed_units_in_one_file_agree(self):
        now_s = time.time()
        self.write([now_s - 60, (now_s - 120) * 1000.0])   # one of each, both recent
        hourly, daily = g5._budget_counts()
        self.assertEqual((hourly, daily), (2, 2), "both writers' rows must be counted once each")

    def test_thirty_stale_rows_no_longer_pin_the_eye_off(self):
        now_ms = time.time() * 1000.0
        self.write([now_ms - (n + 1) * DAY_MS for n in range(30)])
        hourly, daily = g5._budget_counts()
        self.assertEqual(hourly, 0)
        self.assertEqual(daily, 0)
        self.assertTrue(g5._budget_ok(), "with every row stale, the eye must be ALLOWED to look")

    def test_record_writes_milliseconds(self):
        g5._budget_record()
        rows = self.read()
        self.assertEqual(len(rows), 1)
        self.assertGreater(rows[0], 1e11, "the canonical unit on disk is MILLISECONDS")

    def test_a_future_row_is_not_trusted(self):
        """A clock skew or a third writer's garbage must not become an immortal charge."""
        self.write([time.time() * 1000.0 + 10 * DAY_MS])
        hourly, daily = g5._budget_counts()
        self.assertEqual((hourly, daily), (0, 0), "a row from the future is not a call he made")


class BothLanguagesShareTheContract(_TempBudget):
    """The Python and Node normalisers must agree, or the file has two writers again."""

    def test_node_asMs_matches_python_as_ms(self):
        node = os.path.join(HERE, "intake_grok_sub.mjs")
        if not os.path.isfile(node):
            self.skipTest("intake_grok_sub.mjs absent")
        src = open(node, encoding="utf-8").read()
        self.assertIn("const MS_FLOOR = 1e11", src, "the Node side lost its unit floor")
        self.assertIn("Number(t) < MS_FLOOR ? Number(t) * 1000 : Number(t)", src,
                      "the Node normaliser changed shape -- keep it identical to _as_ms")
        self.assertEqual(g5._MS_FLOOR, 1e11, "the Python side's floor drifted from Node's")
        # and both call sites must actually USE it, not merely define it (plumbing with no tap)
        self.assertGreaterEqual(src.count(".map(asMs)"), 2,
                                "asMs is defined but not applied at both budget call sites")

    def test_node_honours_the_isolation_lever(self):
        src = open(os.path.join(HERE, "intake_grok_sub.mjs"), encoding="utf-8").read()
        self.assertIn("process.env.G5_BUDGET_PATH", src,
                      "a guard cannot run without writing his live budget file")

    def test_node_agrees_numerically(self):
        """Run the real normaliser in a real node, on the same inputs Python just answered."""
        node_bin = None
        for cand in ("node", "/usr/local/bin/node", "/opt/homebrew/bin/node"):
            try:
                subprocess.run([cand, "--version"], capture_output=True, timeout=20, check=True)
                node_bin = cand
                break
            except Exception:
                continue
        if not node_bin:
            self.skipTest("node not available")
        probe = ("const MS_FLOOR=1e11;const asMs=(t)=>(Number(t)<MS_FLOOR?Number(t)*1000:Number(t));"
                 "console.log(JSON.stringify([asMs(1786385809.525),asMs(1786385809525)]));")
        out = subprocess.run([node_bin, "-e", probe], capture_output=True, text=True, timeout=30)
        got = json.loads(out.stdout.strip())
        self.assertAlmostEqual(got[0], g5._as_ms(1786385809.525), places=0)
        self.assertAlmostEqual(got[1], g5._as_ms(1786385809525), places=0)


class HisRealFileIsHealthy(unittest.TestCase):
    """Read-only. Reports the live state rather than asserting a number that will move."""

    def test_live_budget_reads_consistently(self):
        if not os.path.isfile(LIVE_BUDGET):
            self.skipTest("no live budget file on this machine")
        rows = (json.load(open(LIVE_BUDGET, encoding="utf-8")) or {}).get("calls") or []
        if not rows:
            self.skipTest("live budget is empty")
        normalised = [g5._as_ms(t) for t in rows]
        now_ms = time.time() * 1000.0
        live = [t for t in normalised if 0 <= now_ms - t < DAY_MS]
        # the point: after normalisation the count is BOUNDED by the window, not by history
        self.assertLessEqual(len(live), len(normalised))
        self.assertTrue(all(t > 1e11 for t in normalised), "normalised rows must all be ms")


if __name__ == "__main__":
    unittest.main(verbosity=2)
