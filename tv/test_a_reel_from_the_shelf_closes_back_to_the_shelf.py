# -*- coding: utf-8 -*-
"""#235 / #291 (REG-2074) - ✕ ON A REEL OPENED THROUGH THE SHELF GOES BACK TO THE SHELF, ONE LAYER; THEN THE SHELF'S ✕ LEAVES.

GrokBot ticks 379, 403, 415, 419, 420 and 421 on #230: a reel picked from the River gallery closed onto Sessions or TV·D -
"✕ returns to the TAB the Shelf was opened from but always skips the River gallery it came through". The stage's ✕ and the
last Esc called thClose, which tears down the theatre AND the shelf. Now a reel that came through the shelf (its dossier's
▶, Last session, or a load while the shelf was the door) steps back to the shelf, which becomes the door; its own ✕ then
closes everything as before, and a reel NOT from the shelf still closes the theatre.

Drives the SHIPPED thCloseReel, cut from control_ui.html and run in node over stubs; the doors that mark a reel are pinned
by their full expressions. A missing node raises; this law does not skip.
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
CUT = ("  function thCloseReel(){\n", "    thClose();\n  }\n")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _cut(s):
    start, end = CUT
    if s.count(start) != 1:
        raise AssertionError("thCloseReel's anchor matched %d times - re-point this law" % s.count(start))
    i = s.index(start)
    fn = s[i:s.index(end, i) + len(end)]
    if fn.count("{") != fn.count("}"):
        raise AssertionError("the cut is not a whole function - its end anchor stopped inside it")
    return fn


def _press(th, shelf_opens=True):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    js = """
var TH = %s, CALLS = [], OV = { hidden: true };
function $(id){ return id === 'th-shelfov' ? OV : null; }
function clearTimeout(){}
function thShelf(on){ CALLS.push('shelf:' + on); if (on && %s) OV.hidden = false; }
function thClose(){ CALLS.push('close'); }
function thLit(){ CALLS.push('lit'); }
%s
thCloseReel();
console.log(JSON.stringify({ calls: CALLS, th: TH, shelfShown: !OV.hidden }));
""" % (json.dumps(th), "true" if shelf_opens else "false", _cut(_src()))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("thCloseReel did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AReelFromTheShelfClosesBackToTheShelf(unittest.TestCase):

    def test_a_reel_from_the_shelf_steps_back_to_the_shelf(self):
        out = _press({"open": True, "reelFromShelf": True, "shelfIsDoor": False, "playing": True})
        self.assertNotIn("close", out["calls"], "✕ on a reel from the shelf closed the whole theatre: %r" % out["calls"])
        self.assertTrue(out["shelfShown"], "the shelf it came through did not come back: %r" % out)
        self.assertTrue(out["th"]["shelfIsDoor"], "the shelf is not the door now - its ✕ would leave a bare stage")
        self.assertFalse(out["th"]["reelFromShelf"], "the mark survived the step back - a second ✕ would loop")
        self.assertFalse(out["th"]["playing"], "the reel kept playing under the shelf")

    def test_a_reel_not_from_the_shelf_closes_the_theatre(self):
        out = _press({"open": True, "reelFromShelf": False, "shelfIsDoor": False})
        self.assertEqual(out["calls"], ["close"], "a reel opened elsewhere did not close the theatre: %r" % out["calls"])

    def test_a_shelf_that_will_not_open_still_closes(self):
        out = _press({"open": True, "reelFromShelf": True}, shelf_opens=False)
        self.assertIn("close", out["calls"], "a shelf that would not come back left him on the reel: %r" % out["calls"])

    def test_the_doors_that_mark_a_reel_and_the_presses_that_ask(self):
        s = _src()
        for expr, what in (
                ("    try { if (TH.shelfIsDoor) TH.reelFromShelf = true; TH.shelfIsDoor = false; } catch (e) {}", "a load through the door"),
                ("    if (sov && !sov.hidden && typeof TH !== 'undefined') TH.reelFromShelf = true;   // REG-2074 - ✕ on this reel goes back to the shelf",
                 "the dossier's ▶"),
                ("    if (sov && !sov.hidden && typeof TH !== 'undefined') TH.reelFromShelf = true;   // REG-2074\n", "Last session"),
                ("  $('th-close').onclick = thCloseReel;", "the stage's ✕"),
                ("    thCloseReel();   /* REG-2074 - the last Esc", "the last Esc"),
                ("    TH.reelFromShelf = false;   /* REG-2074 - a full teardown forgets the door */", "the full teardown")):
            self.assertEqual(s.count(expr), 1, "%s no longer takes part in the step back to the shelf" % what)


RED_PROOF = [
    {"why": "REG-2074 - ✕ on a reel from the shelf closes the whole theatre again",
     "file": "tv/control_ui.html",
     "find": "    if (TH.open && TH.reelFromShelf) {\n",
     "replace": "    if (false) {\n",
     "matches": 1},
    {"why": "REG-2074 - the step back leaves the shelf as a layer, not the door (its ✕ would leave a bare stage)",
     "file": "tv/control_ui.html",
     "find": "      try { TH.shelfIsDoor = true; } catch (e) {}\n      try { thShelf(true); } catch (e) {}\n",
     "replace": "      try { thShelf(true); } catch (e) {}\n",
     "matches": 1},
    {"why": "REG-2074 - the stage's ✕ goes straight to thClose again",
     "file": "tv/control_ui.html",
     "find": "  $('th-close').onclick = thCloseReel;",
     "replace": "  $('th-close').onclick = thClose;",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
