# -*- coding: utf-8 -*-
"""#53 — THE SOLVER'S REPORT IS KEPT, so "did it revert or find nothing?" is answerable.

`_hrtFanFit` returns the whole record of what it tried — `reverted`, `solve.from` -> `solve.to`,
`passes`, `moves`, `before`/`after`/`wouldHaveBeen` — and its ONLY caller was
`try { _hrtFanFit(ov); } catch (e) {}`. Everything was discarded, including the exception.

That one line is why #53's central question was UNKNOWN. On his screenshot the labels collide and
a probe measured `withTransform: 0`, which is consistent with TWO OPPOSITE causes — the solver
found no improving move, or it found one and the all-or-nothing revert put it back — and the fix
differs between them. Three distinct root causes are already on record for this symptom, so a
fourth guess was the likeliest outcome of not measuring. [[plumbing-with-no-tap]]

MEASURED 2026-09-09 once the report was kept, over a live headless render at scale 1.074:

    reverted   false          <- the revert did NOT fire
    solve      from {collisions 1, adjacent 2}  ->  to {collisions 0, adjacent 0}
    ratchet    before 1  ->  after 0
    moves      3 stacks kept · DOM: 5 of 20 fan labels carry a transform
    painted    19 of 20 authored          <- one authored label never painted

★ So in the render world the solver WORKS and keeps its solution, and #53's premise as written
does not describe what happens there. ⚠ THAT IS NOT A VERDICT ON HIS CONSOLE: this is the fixture
world, and his lock set has different labels at different widths. What changed is that the
question is now one attribute read away instead of unanswerable. [[unknown-stays-unknown]]

⚠ TWO SURFACES, TWO READERS: `window._hrtFanLast` for a CDP probe, `data-fanfit` on the overlay for
the render harness, which photographs the DOM and cannot reach a JS global. Neither is visible to
him — this changes no pixel.
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
    """The slice between two ANCHORS — never a fixed window. [[source-window-shortcut]]"""
    i = UI.find(start)
    case.assertGreater(i, 0, "anchor %r is gone, so this law has lost its target and is "
                             "measuring nothing (%s)" % (start, what))
    j = UI.find(end, i + len(start))
    case.assertGreater(j, i, "closing anchor %r not found after %r (%s)" % (end, start, what))
    return UI[i:j]


class TheReportIsNotThrownAway(unittest.TestCase):

    def setUp(self):
        self.call = _region(self, "var _ff = _hrtFanFit(ov);", "_heartChipPaint(d);",
                            "the fan-fit call and what it does with the answer")

    def test_the_return_value_is_bound(self):
        """`_hrtFanFit(ov);` on its own line discards the entire record."""
        n = len(re.findall(r"var\s+_ff\s*=\s*_hrtFanFit\(", UI))
        self.assertEqual(1, n,
                         "expected exactly ONE bound call to _hrtFanFit; found %d. Unbound, the "
                         "solver's verdict — reverted, from->to, moves — is computed and dropped, "
                         "which is what made #53 unanswerable." % n)
        bare = re.findall(r"(?<![=\s]\s)\btry\s*\{\s*_hrtFanFit\(ov\)\s*;", UI)
        self.assertEqual([], bare, "the discarding call is back: %s" % bare)

    def test_a_cdp_probe_can_read_it(self):
        self.assertIn("window._hrtFanLast = _ff", self.call,
                      "the report is bound and then not published anywhere a probe can reach — "
                      "bound-and-dropped is the same defect wearing a variable name")

    def test_the_render_harness_can_read_it(self):
        """A JS global is invisible to a harness that photographs the DOM."""
        # ⚠⚠ COUNT, NOT MEMBERSHIP — heart2 called the first version BLIND. `data-fanfit` is
        # written TWICE by design (the success path and the catch path), so `assertIn` was
        # satisfied by whichever copy the tamper had not touched. Third time tonight this exact
        # shape produced a law that sailed through its own defeat. [[regression-guard]]
        n = self.call.count("data-fanfit")
        self.assertEqual(2, n,
                         "expected the verdict in the DOM on BOTH paths (the fit, and the throw); "
                         "found %d. Nothing puts it there for one of them, so the render harness — "
                         "the only instrument that looks at this panel every push — sees an "
                         "absence and cannot tell it from a fan that never ran." % n)
        for key in ("reverted", "passes", "moves"):
            self.assertIn(key, self.call,
                          "the DOM record drops %r, and that field is one of the three that "
                          "separate 'it reverted' from 'it found nothing'" % key)

    def test_a_throw_is_recorded_as_a_throw(self):
        """A crashed fan and a fan that declined to move must not read the same."""
        tail = self.call[self.call.find("catch (e)"):]
        self.assertTrue(tail, "the catch branch is gone")
        # ⚠ SAME LESSON: the catch records the throw on BOTH surfaces — the JS global and the DOM
        # attribute — so a membership test passes while one of them has been gutted.
        n = tail.count("threw")
        self.assertEqual(2, n,
                         "expected the throw recorded on BOTH surfaces (window._hrtFanLast for a "
                         "probe, data-fanfit for the harness); found %d. On the surface that lost "
                         "it, a fan that CRASHED and a fan that found no move are the same empty "
                         "result." % n)

    def test_the_two_surfaces_are_not_one(self):
        """[[the-unjoined-end]] — the probe surface and the DOM surface have different readers."""
        self.assertIn("window._hrtFanLast", self.call)
        self.assertIn("setAttribute('data-fanfit'", self.call)

    def test_writing_the_record_cannot_break_the_panel(self):
        """A diagnostic that can throw is a diagnostic that can take the heart down with it."""
        i = self.call.find("setAttribute('data-fanfit'")
        self.assertGreater(i, 0)
        head = self.call[:i]
        self.assertIn("try {", head,
                      "the data-fanfit write is not inside its own try — a JSON.stringify failure "
                      "would abort the open and the heart would render nothing")


class TheOverlayIdIsTheOneTheCodeUses(unittest.TestCase):
    """⚠ MY OWN PROBE READ `heartov` AND THE ELEMENT IS `heart-ov`, so the first measurement came
    back 'NO OVERLAY' and a DOM count of None. The retention was fine; the reader was wrong. A law
    that pins the id keeps the next probe from repeating it."""

    def test_the_heart_overlay_id(self):
        self.assertIn("document.getElementById('heart-ov')", UI,
                      "the heart overlay id changed; every probe and harness that reads "
                      "data-fanfit off it is now reading nothing and will report an absence")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "restoring the discarding call is the defect verbatim — the solver's whole record "
               "computed and dropped, which is what made #53 unanswerable",
        "file": "control_ui.html",
        "find": "        var _ff = _hrtFanFit(ov);",
        "replace": "        _hrtFanFit(ov); var _ff = null;",
        "matches": 1,
    },
    {
        "why": "dropping the DOM surface leaves the verdict in a JS global the render harness "
               "cannot reach — the only instrument that looks at this panel every push",
        "file": "control_ui.html",
        "find": "          ov.setAttribute('data-fanfit', JSON.stringify({",
        "replace": "          ov.setAttribute('data-NOTHING', JSON.stringify({",
        "matches": 1,
    },
    {
        "why": "swallowing the throw again makes a crashed fan and a fan that found no move "
               "the same empty result",
        "file": "control_ui.html",
        "find": "        window._hrtFanLast = { ok: false, threw: String((e && e.message) || e) };",
        "replace": "        window._hrtFanLast = { ok: false };",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
