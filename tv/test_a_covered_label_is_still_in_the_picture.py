# -*- coding: utf-8 -*-
"""#54 — THE LABEL THAT IS OVERLAPPED MUST NOT BE THE ONE THE SOLVER CANNOT SEE.

`leaves()` ends with a hit test: it asks `document.elementFromPoint` at each element's centre and
DROPS the element if something else answers. That is right for "what is actually visible on the
page" and `pxCount()` — the overlap ratchet's arithmetic — depends on it.

It is exactly wrong as the input to a solver whose job is to separate overlapping labels, because
for a label that is OVERLAPPED something else always answers. The one label the fit pass most needs
to place is the one it never receives.

MEASURED 2026-09-09 on a live headless render at scale 1.074, of 20 authored fan labels:

    vault.sweep_start   dropped — elementFromPoint at its centre returned
                        "56/64 refused · 0.772 >= 0..." , an hrt-fan-arith label lying on top of it

Consequences, all three measured:
  · it entered no `items`, so the solver read **1 collision where there were 2**
  · it entered no stack, so when the stack at x=417.7 moved dx=-16 the NAME stayed behind and
    drifted 16 units from its own arithmetic line
  · `pxCount()` calls the same `leaves()`, so the ratchet could not see it either

Four instruments and the covered label was invisible to all of them at once — which is why this
panel reported clean while his screenshot showed labels running through each other.

AFTER taking the fan's own labels from the authored NodeList instead:

    painted 19 -> 20 of 20 · unpainted [] · collisions seen 1 -> 2 · moves 3 -> 4 · final 0

⚠ `leaves()` IS UNCHANGED and is still the obstacle set. Only the fan's labels bypass the hit test,
because a fan label that is covered is one that must be MOVED, not one that has gone away.
[[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()


def _region(case, start, end, what):
    i = UI.find(start)
    case.assertGreater(i, 0, "anchor %r is gone — this law lost its target (%s)" % (start, what))
    j = UI.find(end, i + len(start))
    case.assertGreater(j, i, "closing anchor %r not found (%s)" % (end, what))
    return UI[i:j]


class TheFanIsNotFilteredByTheHitTest(unittest.TestCase):

    def setUp(self):
        self.build = _region(self, "  function _hrtFanFit(root) {", "    stacks.sort(",
                             "the fan-fit input build")

    def test_the_fan_labels_come_from_the_svg(self):
        self.assertIn("svg.querySelectorAll('text.hrt-fan')", self.build,
                      "the fan's own labels are no longer taken from the authored NodeList, so a "
                      "COVERED label — the one the solver most needs — is filtered out by "
                      "leaves()' hit test before it is ever considered")

    def test_the_item_set_is_not_leaves_alone(self):
        """`var els = leaves()` alone is the defect verbatim."""
        n = len(re.findall(r"var\s+els\s*=\s*leaves\(\)\s*,", self.build))
        self.assertEqual(0, n,
                         "the item set is built from leaves() alone (%d occurrence(s)). Every fan "
                         "label that is overlapped is dropped by the hit test at the end of "
                         "leaves(), so the solver undercounts collisions and the covered label "
                         "never receives its stack's transform." % n)

    def test_leaves_still_carries_the_hit_test(self):
        """[[the-unjoined-end]] — the fix must not be 'delete the hit test'."""
        lv = _region(self, "    function leaves() {", "    function pxCount()", "leaves()")
        self.assertIn("elementFromPoint", lv,
                      "leaves() lost its hit test. It is the OBSTACLE set and the ratchet's own "
                      "leaf rule; removing the test there would start counting elements nobody "
                      "can see, which is a different lie in the same panel")

    def test_the_ratchet_still_uses_leaves(self):
        px = _region(self, "    function pxCount() {", "\n    function ", "pxCount()")
        self.assertIn("leaves()", px,
                      "pxCount stopped using leaves(), so the ratchet and the page no longer agree "
                      "about what is on screen")


class TheGapIsNamedNotCounted(unittest.TestCase):

    def setUp(self):
        self.build = _region(self, "  function _hrtFanFit(root) {", "    stacks.sort(",
                             "the fan-fit input build")

    def test_a_missing_label_is_named(self):
        """`painted 19 of 20` is a count with no name attached — it took a probe to learn which."""
        self.assertIn("unpainted", self.build,
                      "nothing records WHICH authored fan label failed to reach a stack, so the "
                      "next occurrence is again a bare count and again needs a bespoke probe")
        for field in ("text", "why", "cls"):
            self.assertIn('"%s"' % field if ('"%s"' % field) in self.build else "%s:" % field,
                          self.build,
                          "the unpainted record drops %r — a name without a reason cannot be "
                          "acted on" % field)

    def test_the_three_causes_are_kept_apart(self):
        """no rect / no x / not returned by leaves() are different defects.

        ⚠⚠ THE QUOTED LITERAL, NOT THE PHRASE — heart2 called the first version BLIND. The bare
        phrase "no client rect" also appears in the explanatory COMMENT a few lines above the
        code, so tampering the actual string left the law satisfied by prose describing it. That
        is this repo's most repeated guard defect and it caught me inside the very gate whose
        subject is an instrument that could not see itself. [[feedback-comments-vs-code]]
        """
        for cause in ("'no client rect (not painted)'",
                      "'no x attribute to group a stack on'",
                      "'painted, but leaves() did not return it'"):
            self.assertIn(cause, self.build,
                          "the unpainted reason no longer distinguishes %r — collapsing the causes "
                          "sends the next reader to the wrong place, which is what happened here: "
                          "the first instrument recorded no-rect and measured an EMPTY list while "
                          "a label was missing" % cause)

    def test_the_gap_is_taken_against_the_authored_list(self):
        self.assertIn("_seen.indexOf(", self.build,
                      "the difference is no longer taken against the authored NodeList, so a cause "
                      "nobody anticipated falls out silently again")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "restoring leaves() as the sole item set is the defect verbatim — the overlapped "
               "label is dropped by the hit test, the solver undercounts, and the covered name "
               "never receives its stack's transform",
        "file": "control_ui.html",
        "find": "    var _lv = leaves(), _fan = svg.querySelectorAll('text.hrt-fan'), els = _lv.slice(0);",
        "replace": "    var els = leaves(), _fan = [];",
        "matches": 1,
    },
    {
        "why": "taking the difference against the walked set instead of the AUTHORED list is how "
               "the first instrument measured an empty unpainted list while a label was missing",
        "file": "control_ui.html",
        "find": "      if (_seen.indexOf(_auth[ai]) >= 0) continue;",
        "replace": "      if (true) continue;",
        "matches": 1,
    },
    {
        "why": "collapsing the three causes into one sentence sends the next reader to the wrong "
               "edge — which cost a whole measurement round here",
        "file": "control_ui.html",
        "find": "        why: (!_ar || !_ar.length) ? 'no client rect (not painted)'",
        "replace": "        why: (!_ar || !_ar.length) ? 'missing'",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
