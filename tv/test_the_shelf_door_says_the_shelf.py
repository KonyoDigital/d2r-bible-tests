# -*- coding: utf-8 -*-
"""#287 (REG-2076) - OPENING THE SHELF SAYS "THE SHELF", NEVER THE LAST REEL'S HEADER.

GrokBot ticks 419 and 423 on #230: the Shelf card showed 'THEATRE · SESSION 1 · PAST REPLAY · NOT LIVE' (tick 423: SESSION 41)
for seconds before the River gallery painted. The shelf opens inside the theatre shell, and thOpen's ribbon painted from TH.sn
- the last reel, or 'session 1' on a fresh console - though no reel had been picked. A door open now says the shelf, as does
the ribbon after a reel's ✕ steps back to it (REG-2074); a reel he picks still names its session.

Drives the SHIPPED thRibbon, cut from control_ui.html and run in node. A missing node raises; this law does not skip.
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
CUT = ("  function thRibbon(door){\n", "\n  }\n")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _ribbon(th, door, on_air=False):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    start, end = CUT
    if s.count(start) != 1:
        raise AssertionError("thRibbon's anchor matched %d times - re-point this law" % s.count(start))
    i = s.index(start)
    fn = s[i:s.index(end, i) + len(end)]
    if fn.count("{") != fn.count("}"):
        raise AssertionError("the cut is not a whole function - its end anchor stopped inside it")
    js = """
var TH = %s, EL = { textContent: '', classList: { add: function(){}, remove: function(){} } };
function $(id){ return id === 'th-ribbon' ? EL : null; }
var document = { body: { getAttribute: function(k){ return k === 'data-state' ? %s : null; } } };
function thFmtFull(){ return 'Oct 8, 14:00:00'; } function thFmtT(){ return '14:30:00'; }
%s
thRibbon(%s);
console.log(JSON.stringify(EL.textContent));
""" % (json.dumps(th), json.dumps("on" if on_air else "off"), fn, "true" if door else "")
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("thRibbon did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheShelfDoorSaysTheShelf(unittest.TestCase):
    LAST = {"sn": 41, "sessions": [{}] * 40 + [{"t0": 1, "t1": 2}]}

    def test_a_door_open_says_the_shelf_not_the_last_reel(self):
        txt = _ribbon(dict(self.LAST, shelfIsDoor=False), door=True)
        self.assertIn("THE SHELF", txt)
        self.assertNotIn("session 41", txt, "the shelf door wore the last reel's header: %r" % txt)

    def test_the_shelf_as_the_door_after_a_step_back_says_the_shelf(self):
        self.assertIn("THE SHELF", _ribbon(dict(self.LAST, shelfIsDoor=True), door=False))

    def test_a_picked_reel_still_names_its_session(self):
        txt = _ribbon(dict(self.LAST, shelfIsDoor=False), door=False)
        self.assertIn("session 41", txt, "a loaded reel lost its own header: %r" % txt)

    def test_on_air_keeps_its_own_warning(self):
        self.assertIn("ON AIR", _ribbon(dict(self.LAST, shelfIsDoor=True), door=True, on_air=True))

    def test_the_door_open_and_the_step_back_ask_for_it(self):
        s = _src()
        self.assertEqual(s.count("    try { thRibbon(_shelfDoor); thCoachOnce(); } catch (e) {}"), 1,
                         "thOpen no longer tells the ribbon it is opening the shelf")
        self.assertEqual(s.count("      if (_bk && !_bk.hidden) { try { thRibbon(); } catch (e) {} thLit(); return; }"), 1,
                         "the step back to the shelf no longer repaints the ribbon")


RED_PROOF = [
    {"why": "REG-2076 - the shelf door paints the last reel's header again",
     "file": "tv/control_ui.html",
     "find": "    if (!onAir && (door || TH.shelfIsDoor)){\n",
     "replace": "    if (false){\n",
     "matches": 1},
    {"why": "REG-2076 - thOpen stops telling the ribbon it is the shelf door",
     "file": "tv/control_ui.html",
     "find": "    try { thRibbon(_shelfDoor); thCoachOnce(); } catch (e) {}",
     "replace": "    try { thRibbon(); thCoachOnce(); } catch (e) {}",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
