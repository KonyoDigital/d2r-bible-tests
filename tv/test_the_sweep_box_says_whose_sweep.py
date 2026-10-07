# -*- coding: utf-8 -*-
"""REG-1947 - THE RAIL'S SWEEP BOX SAYS WHOSE SWEEP IT IS.

GrokBot (#230 tick 378): "Konyo's STATION tips say 'a sweep is already running' while the rail SWEEP box reads IDLE".
Both were right: the box paints THIS console's chronicle sweep (_swmPaint, fed by this console's own state), and the
tips were Konyo's Mac's. The box sits directly under THE FLEET's list of PCs with a bare "SWEEP" head, so it read as a
fact about the fleet. The law: the head names this PC and its hover says another PC's sweep is told on its own row.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


class TheSweepBoxSaysWhoseSweep(unittest.TestCase):

    def setUp(self):
        with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
            self.ui = fh.read()

    def test_the_head_names_this_pc(self):
        m = re.search(r'<div class="fleet-box sweep-box" id="sweep-box" hidden>\s*<div class="fleet-head"([^>]*)>([^<]*)<', self.ui)
        self.assertIsNotNone(m, "the sweep box's head is gone - this law lost its subject")
        self.assertIn("this PC", m.group(2), "the SWEEP box under THE FLEET does not say whose sweep it is (REG-1947)")
        self.assertIn("another PC", m.group(1), "the head's hover does not say where another PC's sweep is told")

    def test_it_still_paints_this_consoles_own_state(self):
        self.assertEqual(self.ui.count("function _swmPaint(st) {"), 1, "the box's painter moved - re-point this law")


RED_PROOF = [
    {
        "why": "REG-1947 - the SWEEP box goes back to a bare head that reads as the whole fleet's sweep",
        "file": "tv/control_ui.html",
        "find": ">🧠 SWEEP · this PC <span",
        "replace": ">🧠 SWEEP <span",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
