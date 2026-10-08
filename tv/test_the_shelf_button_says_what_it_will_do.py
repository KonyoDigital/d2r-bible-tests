# -*- coding: utf-8 -*-
"""#282 (REG-2067) - THE THEATRE'S SHELF BUTTON SAYS WHAT A PRESS WILL DO: OPEN THE SHELF, OR CLOSE IT.

GrokBot tick 418 on #230 (K04/K05): "'The shelf — pick any recorded session (S)' doesn't open a picker; it closes the River".
The 📚 button toggles the shelf, and with the shelf already open (it was the door) a press closes it and returns to the tab
it was opened from - correct behaviour under words promising a session picker.

  * with the shelf hidden the button says "The shelf — pick any recorded session (S)";
  * with it open, "Close the shelf (S) — back to where you opened it";
  * the words follow the overlay's own `hidden` attribute (a MutationObserver), so every door that shows or hides the shelf
    is covered - and a hover that is holding the title (data-tip-held) is updated instead of clobbered.
Drives the SHIPPED block, cut from control_ui.html and run in node with the DOM stubbed. A missing node raises.
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
BLOCK = ("  window._thShelfBtnSay = function(shelfOpen){\n", "  } catch (_sb) {}\n")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _run():
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    start, end = BLOCK
    if s.count(start) != 1:
        raise AssertionError("the shelf-button block's anchor matched %d times - re-point this law" % s.count(start))
    i = s.index(start)
    block = s[i:s.index(end, i) + len(end)]
    js = r"""
var window = {};
function mk(){ var a = {}; return { hidden: true, attrs: a,
  setAttribute: function(k, v){ a[k] = String(v); }, hasAttribute: function(k){ return k in a; },
  getAttribute: function(k){ return a[k]; } }; }
var OV = mk(), BTN = mk(), CB = null;
function $(id){ return id === 'th-shelfov' ? OV : id === 'th-shelf' ? BTN : null; }
function MutationObserver(cb){ CB = cb; this.observe = function(){}; }
%s
var out = [BTN.attrs.title];
OV.hidden = false; CB(); out.push(BTN.attrs.title);
BTN.attrs['data-tip-held'] = 'x'; OV.hidden = true; CB(); out.push(BTN.attrs['data-tip-held']);
console.log(JSON.stringify(out));
""" % block
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut block did not run in node: %s" % r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheShelfButtonSaysWhatItWillDo(unittest.TestCase):

    def test_its_words_follow_the_shelf(self):
        closed, opened, held = _run()
        self.assertIn("pick any recorded session", closed, closed)
        self.assertTrue(opened.startswith("Close the shelf"), "with the shelf open the button still promises a picker: %r" % opened)
        self.assertIn("pick any recorded session", held, "a held hover title was not updated: %r" % held)


RED_PROOF = [
    {"why": "REG-2067 - the shelf button promises a picker while a press closes the shelf again",
     "file": "control_ui.html",
     "find": "    return shelfOpen ? 'Close the shelf (S) \\u2014 back to where you opened it' : 'The shelf \\u2014 pick any recorded session (S)';\n",
     "replace": "    return 'The shelf \\u2014 pick any recorded session (S)';\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
