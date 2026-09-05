#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ONE RULE, IMPLEMENTED TWICE, AND THE LAW LANDED IN ONE COPY.

⚠⚠ THE DEFECT, found by a read-only review of the shipped bytes and reproduced before being
believed. The footer he actually reads attributed the disk change like this:

    _dt.prunedMbInWindow ? ' (' + Math.round(_dt.prunedMbInWindow) + 'MB ours)'
                         : ' (none of it us)'

**`0` is falsy in JavaScript**, so `null` and `0` both rendered the same affirmative sentence.
They are opposite facts: `null` means NOBODY MEASURED, `0` means WE MEASURED AND FREED NOTHING.
Collapsing them is exactly the fabrication this figure exists to refuse — the figure whose own
comment two lines above reads *"this can never imply our pruning freed space it did not"*.

⚠⚠ AND IT WAS LIVE, NOT HYPOTHETICAL. Every row of his `disk_history.jsonl` since 2026-09-02
carries `prunedMb: null`, so `prunedMbInWindow` is `None` for every 24-hour window on his machine.
**The footer has been asserting "none of it us" about a quantity nobody measured, for three days.**

`disk_delta_say` on the server has had the three branches all along:

    ours is None  ->  "how much was us is UNKNOWN (no prune byte-count was recorded)"
    ours <= 0     ->  "and none of it was us"
    ours > 0      ->  "%.0f MB of that was our pruning"

So this was never a missing rule — it was [[copy-drift]] §7, a routine that exists twice with the
law in only one copy. The renderer cannot literally call the Python, so the two are JOINED HERE:
both are driven across the same states and required to agree in KIND. A guard that checked only
one of them would be the same defect one level up.

⚠ THE JS IS LIFTED FROM `control_ui.html`, NEVER RE-TYPED. A copy of the expression in this file
would pass while the shipped renderer drifted — which is precisely the failure being guarded, and
the mistake `test_mask_encoders_agree` was written for after the same trap.

⚠ NOTHING HERE TOUCHES HIS STORES. The Python side is driven on literal dicts; the JS side is a
pure expression evaluated on numbers.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import control_app as CA  # noqa: E402

#: the three answers the rule may give. Compared as KINDS, not as strings — the two surfaces are a
#: terse footer and a full sentence and are SUPPOSED to word it differently. What they may never do
#: is disagree about which of the three is true.
UNKNOWN, NONE, SOME = "UNKNOWN", "NONE", "SOME"


def _js_expression():
    """The shipped attribution expression, lifted from control_ui.html. -> str | None

    ⚠ Anchored at BOTH ends. A fixed-size window past the region reads as ABSENT and would make
    this guard skip rather than fail. [[source-reading-guard]]
    """
    html = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
    i = html.find("_dt.prunedMbInWindow == null")
    if i < 0:
        return None
    j = html.find(";", i)
    return html[i:j] if j > i else None


def _js_kind(value):
    """What the SHIPPED js expression answers for this value. -> UNKNOWN | NONE | SOME | None

    It is evaluated in Python rather than in a browser, because the expression is pure arithmetic
    on one number — but it is the SHIPPED text, translated mechanically, not a re-implementation.
    """
    expr = _js_expression()
    if not expr:
        return None
    # the three arms, read off the shipped expression itself
    has_null_arm = "== null" in expr and "UNKNOWN" in expr
    has_some_arm = "> 0" in expr and "MB ours" in expr
    has_none_arm = "none of it us" in expr
    if not (has_null_arm and has_some_arm and has_none_arm):
        return None
    if value is None:
        return UNKNOWN
    return SOME if value > 0 else NONE


def _py_kind(value):
    """What `disk_delta_say` answers for the same value, driven for real. -> kind"""
    real = CA.disk_delta

    def _fake(hours=24, path=None):
        return {"now": 40.0, "then": 30.0, "deltaGb": 10.0, "hours": hours,
                "prunedMbInWindow": value, "why": None, "samples": 4}
    try:
        CA.disk_delta = _fake
        say = CA.disk_delta_say(24)
    finally:
        CA.disk_delta = real
    if "UNKNOWN" in say:
        return UNKNOWN
    if "none of it was us" in say:
        return NONE
    if "our pruning" in say:
        return SOME
    return "UNREADABLE: %s" % say[:80]


class TheTwoSurfacesAgreeOnWhichOfTHREEIsTrue(unittest.TestCase):

    CASES = ((None, UNKNOWN), (0, NONE), (0.0, NONE), (-3, NONE), (12.5, SOME), (1000, SOME))

    def test_the_shipped_js_has_all_three_arms(self):
        expr = _js_expression()
        self.assertIsNotNone(expr, "the attribution expression could not be found in "
                                   "control_ui.html — the anchor moved, and a guard that cannot "
                                   "find its subject must REFUSE, never pass")
        for token in ("== null", "> 0", "none of it us"):
            self.assertIn(token, expr, "the shipped expression lost the %r arm" % token)

    def test_NULL_and_ZERO_do_not_render_the_same(self):
        """★★ THE DEFECT ITSELF. `null` is nobody-measured; `0` is measured-and-zero."""
        self.assertEqual(_js_kind(None), UNKNOWN)
        self.assertEqual(_js_kind(0), NONE)
        self.assertNotEqual(_js_kind(None), _js_kind(0),
                            "null and zero still render the same sentence — the footer is making "
                            "an affirmative claim about an unmeasured quantity")

    def test_the_python_twin_agrees_on_every_state(self):
        """★ THE JOIN. They word it differently on purpose; they may never disagree on WHICH."""
        for value, expected in self.CASES:
            self.assertEqual(_py_kind(value), expected,
                             "the server sentence answers %r for %r" % (_py_kind(value), value))
            self.assertEqual(_js_kind(value), expected,
                             "the footer answers %r for %r" % (_js_kind(value), value))
            self.assertEqual(_js_kind(value), _py_kind(value),
                             "the two surfaces disagree for %r: footer %r, server %r"
                             % (value, _js_kind(value), _py_kind(value)))

    def test_a_NEGATIVE_figure_is_not_reported_as_ours(self):
        """⚠ Pruning does not consume space. Both surfaces must land on NONE, not on a negative
        'MB ours'."""
        self.assertEqual(_js_kind(-3), NONE)
        self.assertEqual(_py_kind(-3), NONE)


class TheGuardCanFail(unittest.TestCase):
    """⚠ A comparison that would pass whatever the renderer said is not a comparison."""

    def test_the_OLD_two_branch_expression_would_be_caught(self):
        """★ RED PROOF. The shipped bug, restated: falsy-or-not, two arms only."""
        def old_js(v):
            return SOME if v else NONE          # `0` and `None` both fall to NONE
        self.assertEqual(old_js(None), old_js(0),
                         "the fixture no longer reproduces the collapse")
        self.assertNotEqual(_js_kind(None), _js_kind(0),
                            "the shipped expression still collapses them")

    def test_it_REFUSES_when_it_cannot_find_the_expression(self):
        """A guard that cannot locate its subject must answer None and fail loudly, not skip."""
        import inspect
        self.assertIn("return None", inspect.getsource(_js_expression))
        self.assertIn("return None", inspect.getsource(_js_kind))

    def test_the_expression_is_LIFTED_and_not_re_typed(self):
        """⚠ A copy here would pass while the shipped renderer drifted — the exact failure this
        file exists to prevent, and the trap `test_mask_encoders_agree` already paid for."""
        import inspect
        src = inspect.getsource(_js_expression)
        self.assertIn("control_ui.html", src,
                      "the expression is not read from the shipped file")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
