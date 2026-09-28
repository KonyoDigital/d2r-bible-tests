# -*- coding: utf-8 -*-
"""2026-09-28 — THE CAPTURE PIN SHOWED ON THE STANDBY BOARD WHILE A SHADOW REEL STILL ROLLED.

Second eye on v3520 (ca60116a), confirmed on main: #sig-capture was hidden only when `_shadowArmed && !on`.
Turn the shadow switch OFF while a shadow reel is still rolling and `_shadowArmed` is false (shadowOn false)
while `_shadowRun` is true, so the pin appeared on the standby board until the reel stopped - the background
lane showing itself, which v2362 exists to prevent ("shadow reader is suppose to be behind the scenes").

Read on the shipped page: the pin's hide rule covers the ROLLING lane as well as the armed one, and the rule
sits on #sig-capture itself. RED_PROOF below.
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


def _pin_block():
    with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        ui = fh.read()
    i = ui.find("var capEl = $('sig-capture');")
    assert i > 0, "the capture pin element is gone"
    j = ui.find("capEl.style.display = 'none';", i)
    assert j > i, "the pin is never hidden at all"
    code = "\n".join(l.split("//", 1)[0] for l in ui[i:j].splitlines())
    return re.sub(r"/\*.*?\*/", "", code, flags=re.S)


class TheBackgroundLaneNeverShowsThePin(unittest.TestCase):

    def test_a_rolling_shadow_reel_hides_the_pin_even_with_the_switch_off(self):
        block = _pin_block()
        conds = re.findall(r"if\s*\((.*)\)\s*\{", block)
        self.assertTrue(conds, "no guard hides the pin")
        last = conds[-1]
        self.assertIn("_shadowRun", last,
                      "the pin hides only for an ARMED reader - a reel still rolling after the switch goes off "
                      "shows the pin on the standby board: %r" % last)
        self.assertIn("_shadowArmed", last, "the armed reader no longer hides the pin: %r" % last)
        self.assertIn("!on", last, "a session he started himself would lose its pin: %r" % last)


RED_PROOF = [
    {
        "why": "2026-09-28 - a shadow reel still rolling after the switch goes off shows the pin on the standby board again",
        "file": "control_ui.html",
        "find": "      if ((_shadowArmed || _shadowRun) && !on) {\n",
        "replace": "      if (_shadowArmed && !on) {\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
