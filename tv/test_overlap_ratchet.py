#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The overlap ratchet's own arithmetic — the half that does not need a browser.

⚠⚠ THIS FILE IS A DEBT BEING PAID. `overlap_ratchet` shipped at v2605 with no unit suite, and its
gate `why` said so out loud. One version earlier I had been bitten by exactly that: `reel_templates`
had classified all forty of his reels since v2571 with nothing testing it (REG-586). Shipping the
same shape twice in two versions is how a rule becomes a thing you write down instead of a thing
you do.

⚠ NOTHING HERE STARTS A BROWSER. `measure()` is replaced per test, so these grade the RATCHET —
rise, fall, unknown, malformed — and never the page. The pixel half is exercised by the gate itself
against real pixels every run, which is the stronger check and a different one.
[[feedback-fixtures-never-touch-live-data]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import overlap_ratchet as OR  # noqa: E402


def _counts(**kw):
    """A measurement in the shape `measure()` returns."""
    return {k: {"count": v, "leaves": 50, "sample": []} for k, v in kw.items()}


class _Swap(unittest.TestCase):

    def grade(self, baseline, now, capture=True):
        """Run check() against an injected baseline and measurement. -> (exit, printed)."""
        said = []
        real_m, real_b, real_p = OR.measure, OR._baseline, __builtins__["print"] if isinstance(
            __builtins__, dict) else print
        OR.measure = lambda *a, **k: (now, "") if now is not None else (None, "chrome refused")
        OR._baseline = lambda: (baseline, "") if baseline is not None else (None, "no baseline")
        import builtins
        builtins.print = lambda *a, **k: said.append(" ".join(str(x) for x in a))
        try:
            code = OR.check()
        finally:
            builtins.print = real_p
            OR.measure, OR._baseline = real_m, real_b
        return code, "\n".join(said)


class ARiseFailsAndSaysWHERE(_Swap):
    """★ The whole point. A clipping check cannot see text drawn on text, so this is the only thing
    standing between a new overlap and nobody noticing."""

    def test_a_rise_fails(self):
        code, out = self.grade({"counts": {"375x800": 24}}, _counts(**{"375x800": 26}))
        self.assertEqual(code, 1, "two new overlapping text pairs passed the gate")
        self.assertIn("ROSE", out)

    def test_the_failure_NAMES_the_width(self):
        """A count with no address is how the swallow ratchet next door became unactionable and got
        re-baselined instead of read (REG-579)."""
        _, out = self.grade({"counts": {"375x800": 24, "1440x1000": 3}},
                            _counts(**{"375x800": 24, "1440x1000": 5}))
        self.assertIn("1440x1000", out)
        self.assertIn("3 -> 5", out)

    def test_an_unchanged_count_holds(self):
        code, out = self.grade({"counts": {"375x800": 24}}, _counts(**{"375x800": 24}))
        self.assertEqual(code, 0, out)
        self.assertIn("held", out)


class AFallFailsTOO(_Swap):
    """⚠ NOT AN OVERSIGHT. If a drop passed quietly the baseline would keep old slack, and a later
    real regression would fit inside it unseen — the exact defect v2389 found in the swallow
    ratchet. The win has to be recorded to be kept."""

    def test_a_fall_fails_and_asks_to_be_blessed(self):
        code, out = self.grade({"counts": {"375x800": 24}}, _counts(**{"375x800": 20}))
        self.assertEqual(code, 1, "a fall passed silently, leaving 4 overlaps of slack")
        self.assertIn("fell", out)
        self.assertIn("--write-baseline", out)


class NothingMeasuredIsNeverAPASS(_Swap):
    """[[unknown-stays-unknown]]"""

    def test_a_run_that_could_not_measure_is_UNKNOWN_and_non_zero(self):
        code, out = self.grade({"counts": {"375x800": 24}}, None)
        self.assertEqual(code, 1, "a run that measured nothing reported clean")
        self.assertIn("UNKNOWN", out)
        self.assertIn("not the same as no overlaps", out)

    def test_an_absent_baseline_is_UNCONFIGURED_not_clean(self):
        """⚠ EXERCISES THE REAL `_baseline()`, not a stub of it. The first cut of this test injected
        its own short reason and then asserted the MODULE's wording against it — grading my fixture
        rather than the code. Point BASELINE at a path that does not exist and let the real function
        answer."""
        real_path, real_m = OR.BASELINE, OR.measure
        said = []
        import builtins
        real_p = builtins.print
        OR.BASELINE = os.path.join(HERE, ".no-such-baseline-%d.json" % os.getpid())
        OR.measure = lambda *a, **k: (_counts(**{"375x800": 0}), "")
        builtins.print = lambda *a, **k: said.append(" ".join(str(x) for x in a))
        try:
            code = OR.check()
        finally:
            builtins.print = real_p
            OR.BASELINE, OR.measure = real_path, real_m
        out = "\n".join(said)
        self.assertEqual(code, 1, "an unconfigured gate exited 0")
        self.assertIn("UNCONFIGURED", out)
        self.assertIn("not clean", out,
                      "it reported unconfigured without saying that is different from clean")

    def test_a_MALFORMED_count_is_not_read_as_zero(self):
        """⚠ v2389's lesson, ported: `int(was.get(k, 0))` turns a missing key into 0 and reports a
        healthy tree as entirely new overlaps — or, worse here, a corrupt baseline as a clean one."""
        code, out = self.grade({"counts": {"375x800": None}}, _counts(**{"375x800": 24}))
        self.assertEqual(code, 1)
        self.assertIn("MALFORMED", out)

    def test_a_width_in_the_baseline_that_was_NOT_measured_fails(self):
        """A partial run graded against a full baseline would read every unmeasured width as fine."""
        code, out = self.grade({"counts": {"375x800": 24, "901x900": 3}},
                               _counts(**{"375x800": 24}))
        self.assertEqual(code, 1)
        self.assertIn("was NOT measured", out)


class TheThresholdIsNotZero(unittest.TestCase):
    """⚠ A 1-2px kiss between two boxes is antialiasing and letter-spacing, not two labels on top of
    each other. A zero threshold would make this gate cry wolf on every ordinary layout, and a gate
    that cries wolf is one he learns to skip."""

    def test_the_minimum_overlap_is_stated_and_above_one_pixel(self):
        self.assertGreaterEqual(OR.MIN_OVERLAP_PX, 2,
                                "a 1px box kiss would count as text on text")

    def test_the_js_uses_that_constant_rather_than_a_literal(self):
        """[[copy-drift]] — a second copy of the threshold inside the JS would drift from the one
        the docstring explains."""
        self.assertIn("__MIN__", OR._JS,
                      "the JS hardcodes its own threshold instead of taking MIN_OVERLAP_PX")

    def test_the_narrow_width_is_still_asked_about(self):
        """[[workflow-topology]]'s render rule: layout dies at breakpoints, so 375 must stay."""
        self.assertIn((375, 800), OR.WIDTHS)


class ItGradesAFIRSTPaintAtEachWidth(unittest.TestCase):
    """⚠ Measuring four widths by resizing one tab grades 1440 on a layout just squeezed to 375 and
    back. It reloads per width instead.

    ⚠⚠ AND THE HONEST NOTE THIS PINS: that change measured IDENTICALLY (2/3/24/3 both ways). It is
    here because grading a first paint is the right thing to measure, NOT because it fixed a
    defect — and the comment in the module says exactly that, so nobody later reads it as a
    discovery that never happened."""

    def test_it_navigates_again_after_setting_the_width(self):
        import inspect
        src = inspect.getsource(OR.measure)
        self.assertIn("Page.navigate", src,
                      "widths are measured by resize alone, so later ones are graded on an earlier "
                      "width's settled layout")
        self.assertLess(src.index("setDeviceMetricsOverride"), src.index("Page.navigate"),
                        "it reloads BEFORE setting the width, so the load uses the old size")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
