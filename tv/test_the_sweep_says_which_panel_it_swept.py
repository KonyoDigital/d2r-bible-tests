#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2808 — THE PANEL WAS ON THE WIRE THE WHOLE TIME AND NO SURFACE DREW IT.

v2807 fixed the wrong-panel bug: the reader infers which panel it actually read from the lattice
SHAPE (stash 10x10, inventory 10x4, cube 3x4) and the caller hovers THAT one, so the frame wins
over the argument. Correct — and invisible.

Measured on the shipped source: `hover_mode._STATE` carries "container", `hover_mode.status()`
returns it, and the endpoint spreads it onto the wire with `dict(hover_mode.status(), ok=True)`.
Then `control_ui.html` mentions "container" 17 times and SIXTEEN are CSS or prose about layout
containers. The one functional occurrence hardcodes the request:

    body: JSON.stringify({on: !running, container: 'stash'})

So the button always says stash, the server may correctly sweep the INVENTORY, and the panel under
his hand reports "sweeping — press to stop" either way.

★ WHY THIS IS THE ONE CASE THE NUMBERS CANNOT COVER. `moved` counts up whichever panel got swept.
`planned` does too. Every figure on that button reads as success for a sweep of the wrong grid —
which is precisely what REG-743 WAS. He is recalibrating this by hand, and a recalibration scored
against numbers that cannot show which panel produced them is not a calibration.
[[the-unjoined-end]] [[unknown-stays-unknown]]
"""
import os
import sys
import io
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import source_window as _sw  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")


def _ui():
    with io.open(UI, encoding="utf-8") as fh:
        return fh.read()


class TestTheSweepSaysWhichPanelItSwept(unittest.TestCase):

    def setUp(self):
        self.src = _ui()

    def test_the_helper_exists_and_is_anchored_not_guessed(self):
        """The window is anchored at BOTH ends — never src[i:i+N]. [[source-window-shortcut]]"""
        body = _sw.block(self.src, "function _miniPanelText(j){",
                         what="the panel-name helper")
        self.assertGreater(len(body), 80, "the helper is a stub")
        self.assertIn("container", body,
                      "the helper never reads j.container — it cannot name the panel")

    def test_an_absent_panel_is_unknown_and_never_silently_stash(self):
        """A missing container must not render as the panel the button happened to ask for."""
        body = _sw.block(self.src, "function _miniPanelText(j){", what="the panel-name helper")
        self.assertIn("UNKNOWN", body,
                      "an absent container does not render UNKNOWN. Defaulting it to the "
                      "requested panel re-creates REG-743 in the one surface built to expose it.")

    def test_a_mismatch_names_both_panels(self):
        """Read INVENTORY while he asked for STASH — that must be loud, not silent."""
        body = _sw.block(self.src, "function _miniPanelText(j){", what="the panel-name helper")
        self.assertIn("asked", body,
                      "the helper never compares against what was requested, so the wrong-panel "
                      "case is indistinguishable from the right one")
        self.assertIn("you asked for", body,
                      "a mismatch does not say which panel he asked for — half a comparison")

    def test_the_sweeping_line_actually_calls_it(self):
        """A helper nothing calls is the [[plumbing-with-no-tap]] shape."""
        paint = _sw.block(self.src, "function _miniPaint(j){", what="_miniPaint")
        self.assertIn("_miniPanelText(j)", paint,
                      "_miniPaint never calls the panel-name helper — the value stays on the wire")

    def test_what_the_button_asked_for_is_recorded(self):
        """Without this the mismatch is not computable. Both ends, or neither. [[the-unjoined-end]]"""
        region = _sw.between(self.src,
                             "body: JSON.stringify({on: !running, container: 'stash'})});",
                             "}", what="the mini_auto POST site", include_end=True)
        self.assertIn("dataset.asked", region,
                      "the requested panel is never recorded, so _miniPanelText can never tell a "
                      "mismatch from a match — it would silently report every sweep as expected")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "un-calling the helper returns the button to 'sweeping' with no panel named",
        "file": "control_ui.html",
        "find": "      if (sub) sub.textContent = 'sweeping' + _miniPanelText(j)",
        "replace": "      if (sub) sub.textContent = 'sweeping' + ''",
        "matches": 1,
    },
    {
        "why": "dropping the recorded request makes every mismatch read as a match",
        "file": "control_ui.html",
        "find": "        try { $('btn-miniauto').dataset.asked = 'stash'; } catch(e){}",
        "replace": "        /* removed */",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
