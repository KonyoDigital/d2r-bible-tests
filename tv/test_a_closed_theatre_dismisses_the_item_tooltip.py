# -*- coding: utf-8 -*-
"""#44 (REG-2240, GrokBot #230 tick 371) — LEAVING THE THEATRE DISMISSES THE FLOATING ITEM TOOLTIP.

GrokBot on #230: the theatre ✕ drops to Sessions and leaves a stale Trang-Oul's Wing tooltip behind. #itip is a
document.body child at z-index 9999, OUTSIDE #theatre (thOpen's own note: "tooltips live outside #theatre at a
higher z-index"), so hiding the stage never hides it. A reel's read card carries [data-itip] items; one hovered as
the theatre is torn down stranded its HD-art card over whatever view the ✕ lands on. Teardown already dismisses
every other floating layer it opened (the ⋯ drawer v940.5, the shelf overlay v2451, the coach) — it must own this
one too, not lean on the pointer/Esc handlers a driven close can bypass.

Drives the SHIPPED thClose, cut from control_ui.html and run in node over stubs: it must call window._itemTip.hide().
A second law pins the publish seam (window._itemTip = _itemTip) so the dismissal can actually reach the tooltip
([[the-unjoined-end]]). A missing node raises; this law does not skip.
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
START = "  function thClose(){\n"
END = "    try { if (window.__lastStatus && typeof paint === 'function') paint(window.__lastStatus); } catch(e){}\n  }\n"


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _cut(s):
    if s.count(START) != 1:
        raise AssertionError("thClose's start anchor matched %d times - re-point this law" % s.count(START))
    if s.count(END) != 1:
        raise AssertionError("thClose's end anchor matched %d times - re-point this law" % s.count(END))
    i = s.index(START)
    fn = s[i:s.index(END, i) + len(END)]
    if fn.count("{") != fn.count("}"):
        raise AssertionError("the cut is not a whole function - its end anchor stopped inside it")
    return fn


def _close():
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    js = """
var CALLS = [];
var TH = { gen: 0, open: true, timer: 1, playing: true, loadGen: 0, reelFromShelf: true,
           beats: ['S53-a'], allBeats: ['S53-a'], i: 1 };
function clearTimeout(){}
function $(id){ return { hidden: false, __want: 'x', __url: 'x', title: 'x',
                         removeAttribute: function(k){ delete this[k]; } }; }
function thMore(){ CALLS.push('more'); }
function thCinema(){ CALLS.push('cinema'); }
function thLit(){ CALLS.push('lit'); }
function thTimeline(){ CALLS.push('timeline'); }
var document = { body: { classList: { remove: function(){ CALLS.push('unflag'); } } } };
var window = { _backFromLive: function(){ CALLS.push('back'); }, __lastStatus: null,
               _itemTip: { hide: function(){ CALLS.push('itip-hide'); } } };
%s
thClose();
console.log(JSON.stringify({ calls: CALLS, open: TH.open }));
""" % _cut(_src())
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("thClose did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AClosedTheatreDismissesTheItemTooltip(unittest.TestCase):

    def test_thClose_dismisses_the_floating_item_tooltip(self):
        out = _close()
        self.assertIn("itip-hide", out["calls"],
                      "leaving the theatre did not dismiss #itip - a hovered item strands over the next view: %r" % out["calls"])

    def test_the_teardown_actually_ran_to_completion(self):
        # the dismissal is worthless if it rode in on a cut that never executed: prove the rest of the teardown fired
        out = _close()
        for mark in ("back", "unflag", "timeline", "cinema", "lit"):
            self.assertIn(mark, out["calls"],
                          "thClose stopped before %r - the cut is not the whole teardown: %r" % (mark, out["calls"]))
        self.assertFalse(out["open"], "thClose left TH.open true")

    def test_the_dismissal_is_in_the_shipped_teardown(self):
        fn = _cut(_src())
        self.assertEqual(fn.count("if (window._itemTip) window._itemTip.hide();"), 1,
                         "the item-tooltip dismissal is not inside the shipped thClose")

    def test_the_tooltip_is_published_so_the_teardown_can_reach_it(self):
        # [[the-unjoined-end]] a dismissal that cannot find _itemTip is a no-op
        self.assertEqual(_src().count("  window._itemTip = _itemTip;"), 1,
                         "window._itemTip is not published - thClose's dismissal can never reach the tooltip")


RED_PROOF = [
    {"why": "REG-2240 (#44) - thClose does not dismiss the floating item tooltip, so a reel read-card [data-itip] item (Trang-Oul's Wing) hovered at close strands over Sessions",
     "file": "control_ui.html",
     "find": "    try { if (window._itemTip) window._itemTip.hide(); } catch(e){}\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2240 (#44) - _itemTip is not published on window, so the teardown's dismissal can never reach it (the-unjoined-end)",
     "file": "control_ui.html",
     "find": "  window._itemTip = _itemTip;",
     "replace": "  window.__itemTipUnpublished = _itemTip;",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
