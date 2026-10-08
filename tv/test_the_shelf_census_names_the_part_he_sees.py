# -*- coding: utf-8 -*-
"""#236 (REG-2084) - THE SHELF'S "ON DISK IN ALL" CLAUSE NAMES THE PART HE SEES, AND WHAT HAS NO CARD HERE.

GrokBot ticks 380, 400, 401 and 425 on #230: the River header read '8 RUNS · 12 on disk in all (3 hidden fixtures)' while the
strip said '9 on the shelf' - 8 + 3 is 11, and nothing on screen said what the twelfth reel was. reel_census already counts
`his` (the recent reels retention keeps for him: 9 that tick) and the clause never printed it. Now it does, and when more
recent reels sit on disk than this shelf draws (cards + pushed past the cap) it says how many have no card here - a measured
difference, never a guessed reason.

Drives the SHIPPED _shelfPopClause, cut from control_ui.html and run in node. A missing node raises.
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
START, END = "  function _shelfPopClause(P, shown, pushed){\n", "\n  }\n  window._shelfPopClause = _shelfPopClause;"


def _clause(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    with open(UI, encoding="utf-8") as f:
        s = f.read()
    if s.count(START) != 1:
        raise AssertionError("_shelfPopClause's anchor matched %d times - re-point this law" % s.count(START))
    i = s.index(START)
    fn = s[i:s.index(END, i) + len("\n  }\n")]
    js = ("function esc(x){ return String(x); }\n%s\nconsole.log(JSON.stringify(%s.map(function(c){ return _shelfPopClause(c[0], c[1], c[2]); })));\n"
          % (fn, json.dumps(cases)))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("_shelfPopClause did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


TICK425 = {"sums": True, "onDisk": 12, "his": 9, "fixtures": 3, "owed": 0, "releasable": 0, "other": {}}


class TheShelfCensusNamesThePartHeSees(unittest.TestCase):

    def test_tick_425_adds_up_on_screen(self):
        out = _clause([[TICK425, 8, 0]])[0]
        self.assertEqual(out, " · 12 on disk in all (9 recent · 3 hidden fixtures) · 1 recent reel on disk with no card on this shelf",
                         "the clause does not account for the reels he sees: %r" % out)

    def test_a_reel_pushed_past_the_cap_is_drawn_not_missing(self):
        out = _clause([[TICK425, 8, 1]])[0]
        self.assertNotIn("no card", out, "a reel the river pushed past the cap was called missing: %r" % out)

    def test_a_census_that_does_not_sum_still_prints_nothing(self):
        self.assertEqual(_clause([[dict(TICK425, sums=False), 8, 0], [dict(TICK425, sums=None), 8, 0]]), ["", ""])

    def test_a_malformed_recent_count_is_silence_not_a_number(self):
        out = _clause([[dict(TICK425, his="x"), 8, 0]])[0]
        self.assertNotIn("recent", out, "a malformed 'his' printed a number: %r" % out)


RED_PROOF = [
    {"why": "REG-2084 - the clause forgets the reels he sees again (8 RUNS beside 12 = 3 fixtures + ?)",
     "file": "tv/control_ui.html",
     "find": "                  if (_his) bits.unshift(_his + ' recent');\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2084 - a recent reel with no card on this shelf goes unsaid again",
     "file": "tv/control_ui.html",
     "find": "                  var _noCard = (_his > _shown) ? (_his - _shown) : 0;\n",
     "replace": "                  var _noCard = 0;\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
