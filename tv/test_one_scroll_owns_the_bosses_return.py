# -*- coding: utf-8 -*-
"""REG-2112 (#231 eye on v43 fbdcf7a0, #314) - ONE SCROLL OWNS THE RETURN TO BOSSES.

navClean('bosses') cleared the active item, which schedules setActiveItem(null)'s route-back scroll to the boss nav 60 ms
later ("the top of bosses tab so they can pick another item"), and then scrolled to 0 itself - two writers, and the later one
always won, so the scroll navClean asked for never stuck. Now the route-back owns the scroll when an item was cleared, and
navClean scrolls to the top only when there was none. Drives the SHIPPED navClean, cut from bible.html, in node.
"""
import io
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

PAGE = os.path.join(os.path.dirname(HERE), "bible.html")
START = "function navClean(name) {\n"


def _cut():
    with io.open(PAGE, encoding="utf-8") as f:
        s = f.read()
    if s.count(START) != 1:
        raise AssertionError("navClean's anchor matched %d times - re-point this law" % s.count(START))
    i = s.index(START)
    return s[i:s.index("\n}\n", i) + 3]


def _run(active, tab):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    js = """
var CALLS = [], activeItem = %s;
var window = { closeDrop: function(){}, closeItemDetail: function(){}, clearActiveBoss: function(){},
  clearActiveItem: function(){ CALLS.push('clearItem'); activeItem = null; },
  switchTab: function(n){ CALLS.push('tab:' + n); }, scrollTo: function(o){ CALLS.push('scroll:' + o.top); } };
%s
navClean(%s);
console.log(JSON.stringify(CALLS));
""" % (json.dumps(active), _cut(), json.dumps(tab))
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("navClean did not run in node: %s" % r.stderr[-500:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class OneScrollOwnsTheBossesReturn(unittest.TestCase):

    def test_a_cleared_item_leaves_the_scroll_to_its_route_back(self):
        calls = _run("Harlequin Crest (Shako)", "bosses")
        self.assertIn("clearItem", calls, "premise: the active item is cleared on the way back to bosses")
        self.assertNotIn("scroll:0", calls, "navClean races the item's route-back scroll again: %r" % calls)

    def test_no_item_means_navclean_scrolls_to_the_top(self):
        self.assertIn("scroll:0", _run(None, "bosses"), "with no item to clear nobody scrolls to the top")
        self.assertIn("scroll:0", _run("Harlequin Crest (Shako)", "uniques"),
                      "another tab never clears the item, so navClean still owns its scroll")


RED_PROOF = [
    {"why": "REG-2112 - navClean scrolls to 0 even after clearing an item, racing the route-back again",
     "file": "bible.html",
     "find": "  if (!_hadItem) window.scrollTo({ top: 0, behavior: \"smooth\" });\n",
     "replace": "  window.scrollTo({ top: 0, behavior: \"smooth\" });\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
