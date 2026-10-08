# -*- coding: utf-8 -*-
"""REG-2082 - A FLEET NAME CARD'S CEILING IS WHATEVER CLIPS IT: THE TAB BAR, THE RAIL'S EDGE, OR WHAT STICKS AT THE RAIL'S TOP.

GrokBot tick 425 on #230 (K06): the top row's card ("GROKBOT this console · where its rows came from ...") opened ABOVE the
row and its header was cut off at the top edge. REG-2058 sends a card below when it would not fit under the TAB BAR - but the
fleet sits inside the rail, a scroll container (the rail scroller travels 1,608 px at 1120x628), so a card above the top
visible row is clipped by the RAIL's edge, and by the rail's own sticky title, neither of which the tab-bar ceiling saw.

Drives the SHIPPED _fttCeiling, cut from control_ui.html and run in node over a fake ancestor chain. A missing node raises.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
from cb_node_harness import NODE  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")
CUT = ("  function _fttCeiling(row){\n", "\n    return c;\n  }\n")


def _ceiling(chain):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    with open(UI, encoding="utf-8") as f:
        s = f.read()
    start, end = CUT
    if s.count(start) != 1:
        raise AssertionError("_fttCeiling's anchor matched %d times - re-point this law" % s.count(start))
    i = s.index(start)
    fn = s[i:s.index(end, i) + len(end)]
    if fn.count("{") != fn.count("}"):
        raise AssertionError("the cut is not a whole function - its end anchor stopped inside it")
    js = """
var BODY = {}, HTML = {};
function El(o){ this.o = o; this.children = (o.kids || []).map(function(k){ return new El(k); }); }
El.prototype.getBoundingClientRect = function(){ return { top: this.o.top || 0, bottom: this.o.bottom || 0 }; };
function getComputedStyle(e){ return { overflowY: e.o.oy || 'visible', position: e.o.pos || 'static' }; }
var CH = %s, prev = null, row = null;
for (var i = CH.length - 1; i >= 0; i--){ var e = new El(CH[i]); e.parentElement = prev || BODY; prev = e; }
row = { parentElement: prev };
var document = { body: BODY, documentElement: HTML, getElementById: function(id){ return id === 'head-tabs' ? { getBoundingClientRect: function(){ return { bottom: 90 }; } } : null; } };
%s
console.log(JSON.stringify(_fttCeiling(row)));
""" % (json.dumps(chain), fn)
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("_fttCeiling did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


# innermost first: the fleet list, then the rail (the scroller), then the page
RAIL = {"oy": "auto", "top": 120, "bottom": 660, "kids": [{"pos": "sticky", "top": 120, "bottom": 160}, {"pos": "static", "top": 160, "bottom": 900}]}


class AFleetCardKnowsWhatClipsIt(unittest.TestCase):

    def test_the_rail_edge_and_its_sticky_title_are_the_ceiling(self):
        self.assertEqual(_ceiling([{"oy": "visible", "top": 300}, RAIL, {"oy": "visible"}]), 160,
                         "the card's ceiling ignored the rail's sticky title")

    def test_a_scroller_with_nothing_stuck_clips_at_its_edge(self):
        bare = dict(RAIL, kids=[{"pos": "static", "top": 120, "bottom": 900}])
        self.assertEqual(_ceiling([{"oy": "visible"}, bare]), 120, "the card's ceiling ignored the rail's own edge")

    def test_with_no_scroller_the_tab_bar_is_the_ceiling(self):
        self.assertEqual(_ceiling([{"oy": "visible"}, {"oy": "visible"}]), 90)

    def test_the_hover_asks_it(self):
        with open(UI, encoding="utf-8") as f:
            s = f.read()
        self.assertEqual(s.count("        var ceil = _fttCeiling(row);"), 1, "the fleet row hover no longer asks what clips the card")


RED_PROOF = [
    {"why": "REG-2082 - the rail's edge is not a ceiling again (the card above the top row is cut)",
     "file": "tv/control_ui.html",
     "find": "        if (top > c) c = top;\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2082 - a sticky title at the rail's top is not a ceiling again",
     "file": "tv/control_ui.html",
     "find": "          if (kr.top <= top + 2 && kr.bottom > c) c = kr.bottom;\n",
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
