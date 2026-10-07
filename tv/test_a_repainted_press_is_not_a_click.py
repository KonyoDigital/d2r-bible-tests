# -*- coding: utf-8 -*-
"""REG-1951 - A SHELF CLICK WHOSE PRESS WAS REPAINTED AWAY IS NOT A DECISION.

GrokBot (#230 tick 381, 07:13:08, v3601): "the first click on card 6 didn't open the theatre; the whole drawer closed
onto the TV.D body", and the shelf reopened at the top. The shelf re-renders itself when its /api/sessions answer lands
(innerHTML replaced), so a press on a card that the repaint removed ends as a click on the overlay between the new
cards - and the handler's rule "a click outside a card dismisses, the same way the X does" closed the door.

The law runs the REAL helper (lifted from tv/control_ui.html) in node: a press whose element left the page, or a click
on a node that is gone, is ignored; an ordinary press-and-release, and a click with no press (keyboard, .click()), is
not; the press is consumed by its click. And the shelf's click handler asks it before anything else, with its press
recorded on pointerdown.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


def _ui():
    with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        return fh.read()


def _helper(ui):
    i = ui.find("  function _shPressWasRepainted(ov, e){")
    if i < 0:
        return None
    j = ui.find("\n  }\n", i)
    return ui[i:j + 4]


HARNESS = r"""
%s
function N(connected){ return {isConnected: connected}; }
var out = {};
var card = N(true), ov = {__pressT: card};
out.ordinary = _shPressWasRepainted(ov, {target: card});
out.consumed = ov.__pressT === null;
var gone = N(false); ov.__pressT = gone;
out.pressRepainted = _shPressWasRepainted(ov, {target: N(true)});
ov.__pressT = null;
out.clickOnGone = _shPressWasRepainted(ov, {target: N(false)});
out.noPress = _shPressWasRepainted({}, {target: N(true)});
process.stdout.write(JSON.stringify(out));
"""


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class ARepaintedPressIsNotAClick(unittest.TestCase):

    def test_the_helper_tells_a_repainted_press_from_a_real_click(self):
        h = _helper(_ui())
        self.assertIsNotNone(h, "_shPressWasRepainted is gone from tv/control_ui.html")
        p = subprocess.run(["node", "-"], input=HARNESS % h, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr[-600:])
        out = json.loads(p.stdout)
        self.assertIs(out["ordinary"], False, "an ordinary press-and-release on a card was ignored")
        self.assertIs(out["consumed"], True, "the press was not consumed by its click")
        self.assertIs(out["pressRepainted"], True,
                      "a press whose card the repaint removed still counted as a click (REG-1951)")
        self.assertIs(out["clickOnGone"], True, "a click on a node that left the page still counted")
        self.assertIs(out["noPress"], False, "a click with no press (keyboard, .click()) was ignored")

    def test_the_shelf_handler_asks_first_and_records_the_press(self):
        ui = _ui()
        self.assertEqual(ui.count("    ov.onpointerdown = function(e){ ov.__pressT = e.target; };"), 1,
                         "the shelf no longer records what its press landed on")
        i = ui.find("    ov.onclick = function(e){\n      if (_shPressWasRepainted(ov, e)) return;")
        self.assertGreaterEqual(i, 0, "the shelf's click handler no longer asks before it dismisses")


RED_PROOF = [
    {
        "why": "REG-1951 - a press the repaint removed counts again: a click between the new cards closes the shelf door",
        "file": "tv/control_ui.html",
        "find": "      return !!(p && p.isConnected === false);\n",
        "replace": "      return false;\n",
        "matches": 1,
    },
    {
        "why": "REG-1951 - the shelf's click handler stops asking, so the dismiss rule sees the repainted click",
        "file": "tv/control_ui.html",
        "find": "      if (_shPressWasRepainted(ov, e)) return;   // REG-1951",
        "replace": "      // REG-1951",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
