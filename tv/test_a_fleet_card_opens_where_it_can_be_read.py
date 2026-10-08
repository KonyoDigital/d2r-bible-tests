# -*- coding: utf-8 -*-
"""#280 (REG-2058) - A FLEET NAME CARD OPENS WHERE IT CAN BE READ: ABOVE ITS ROW WHEN IT FITS, ELSE BELOW.

GrokBot tick 418 on #230 (v3621, K02): "The ALT TEST name card's header line runs off the top under the tab bar." The card is
`position:absolute; bottom: calc(100% + 8px)` - always above its row - and the rail's top row has no room above it.

  * _fttPlace(rowTop, cardH, ceiling): 'above' when the card fits between the row and the tab bar, else 'below';
  * a hover on a fleet row asks it and toggles .ftt-below, which the stylesheet opens under the row.
(K01 - the Wife PC card drawn over the rows above it - is a hover card covering its neighbours, by design; it now never
leaves the screen.) Drives the SHIPPED _fttPlace, cut from control_ui.html and run in node. A missing node raises.
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
FN = ("  function _fttPlace(rowTop, cardH, ceiling){\n", "\n  }\n")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _place(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    start, end = FN
    if s.count(start) != 1:
        raise AssertionError("_fttPlace's anchor matched %d times - re-point this law" % s.count(start))
    i = s.index(start)
    fn = s[i:s.index(end, i) + len(end)]
    # #231 eye on v3623: the end anchor is the FIRST match after the start - a cut that stops inside the function runs
    # a truncated body in node. A whole function balances its braces; anything else refuses loudly.
    if fn.count("{") != fn.count("}"):
        raise AssertionError("the cut is not a whole function (%d '{' vs %d '}') - the end anchor stopped inside it; "
                             "re-point this law" % (fn.count("{"), fn.count("}")))
    js = "%s\nconsole.log(JSON.stringify(%s.map(function(c){ return _fttPlace(c[0], c[1], c[2]); })));\n" % (fn, json.dumps(cases))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut function did not run in node: %s" % r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AFleetCardOpensWhereItCanBeRead(unittest.TestCase):

    def test_the_top_row_opens_below_and_a_low_row_above(self):
        # the rail's first row sits just under a 56 px tab bar; a 240 px card cannot fit above it
        self.assertEqual(_place([[70, 240, 56], [600, 240, 56], [304, 240, 56]]), ["below", "above", "above"])

    def test_the_hover_asks_it_and_the_stylesheet_opens_below(self):
        s = _src()
        self.assertEqual(s.count("card.classList.toggle('ftt-below', _fttPlace(row.getBoundingClientRect().top, "
                                 "card.offsetHeight, ceil) === 'below');"), 1, "a fleet row hover no longer asks _fttPlace")
        self.assertEqual(s.count("  .fleet-row.has-ftt .ftt.ftt-below { bottom: auto; top: calc(100% + 8px); }\n"), 1,
                         "the stylesheet no longer opens a .ftt-below card under its row")


RED_PROOF = [
    {"why": "REG-2058 - the top row's card runs under the tab bar again (always above)",
     "file": "control_ui.html",
     "find": "    return ((+rowTop || 0) - (+cardH || 0) - 8 < (+ceiling || 0)) ? 'below' : 'above';\n",
     "replace": "    return 'above';\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
