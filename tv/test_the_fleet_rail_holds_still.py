# -*- coding: utf-8 -*-
"""#237/#285 (REG-2062) - THE FLEET RAIL HOLDS STILL: A BEACON ARRIVING NEVER RESHUFFLES IT.

GrokBot ticks 418-420 on #230: with nothing clicked the rail went ALT TEST / Konyo / GrokBot / Dean / Wife PC (11:37) ->
GrokBot / ALT TEST / Konyo / Dean / Wife PC (11:57), and #237 saw rows "re-sort and churn mid-tick". The site sends the rows
newest-beacon-first (functions/console.js sorts by `t`), and the rail painted them in that order.

  * _fleetStableOrder(list, me): this console first, then by the name each row shows, then by machine id - the same
    order whatever order the beacons arrived in;
  * the rail paints both groups (online, offline) through it; a machine that changes group still moves (that is news).
Drives the SHIPPED _fleetStableOrder, cut from control_ui.html and run in node. A missing node raises.
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
FN = ("  var _fleetStableOrder = function (list, me) {\n", "\n    });\n  };\n")
ROWS = [{"machine": "m-alt", "nickname": "Konyo ALT TEST", "t": "3"}, {"machine": "m-mac", "nickname": "Konyo", "t": "1"},
        {"machine": "m-gb", "nickname": "GrokBot", "t": "5"}, {"machine": "m-dean", "nickname": "Dean", "t": "2"}]


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _order(lists, me):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    start, end = FN
    if s.count(start) != 1:
        raise AssertionError("_fleetStableOrder's anchor matched %d times - re-point this law" % s.count(start))
    i = s.index(start)
    fn = s[i:s.index(end, i) + len(end)]
    js = ("%s\nconsole.log(JSON.stringify(%s.map(function(l){ return _fleetStableOrder(l, %s).map(function(m){ "
          "return m.nickname; }); })));\n" % (fn, json.dumps(lists), json.dumps(me)))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut function did not run in node: %s" % r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheFleetRailHoldsStill(unittest.TestCase):

    def test_every_beacon_order_paints_the_same_rail(self):
        newest_first_a = sorted(ROWS, key=lambda m: m["t"], reverse=True)
        newest_first_b = [ROWS[1], ROWS[3], ROWS[0], ROWS[2]]
        got = _order([newest_first_a, newest_first_b, list(reversed(ROWS))], "m-mac")
        self.assertEqual(got[0], got[1], "two beacon orders painted two rails: %r" % got)
        self.assertEqual(got[0], got[2], got)
        self.assertEqual(got[0], ["Konyo", "Dean", "GrokBot", "Konyo ALT TEST"],
                         "this console first, then by name: %r" % got[0])

    def test_with_no_known_self_it_is_still_one_order(self):
        got = _order([ROWS, list(reversed(ROWS))], None)
        self.assertEqual(got[0], got[1], got)

    def test_both_groups_paint_through_it(self):
        s = _src()
        self.assertEqual(s.count("      var rows = _fleetStableOrder(j.online, j.me).map(function (m) { return _row(m, true); })\n"
                                 "        .concat(_fleetStableOrder(j.offline, j.me).map(function (m) { return _row(m, false); }));"),
                         1, "the rail paints the site's newest-beacon order again")


RED_PROOF = [
    {"why": "REG-2062 - the rail paints the newest-beacon order again (rows churn with nothing clicked)",
     "file": "control_ui.html",
     "find": "      var an = key(a), bn = key(b);\n      if (an !== bn) return an < bn ? -1 : 1;\n",
     "replace": "      var an = String(a && a.t), bn = String(b && b.t);\n      if (an !== bn) return an < bn ? 1 : -1;\n",
     "matches": 1},
    {"why": "REG-2062 - this console stops leading its own rail",
     "file": "control_ui.html",
     "find": "      if (am !== bm) return am - bm;\n",
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
