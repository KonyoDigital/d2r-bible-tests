# -*- coding: utf-8 -*-
"""#281 (REG-2059) - A RIVER TIP SAYS A SHARED REASON ONCE, NAMING EVERY ROW IT HOLDS.

GrokBot tick 418 on #230 (v3621, K03): Konyo's river tip repeated "STATION 5: the reel sweep owes 9 read(s) … vault.sweep_start
is LOCKED — 3 instrument(s) are BLIND…" twice word for word, and PRINTER 2 and PRINTER 1 each carried the same "vault lane:
owes 7, 4168 read(s) on record …" paragraph; the tip ended cut off with "…".

  * _fleetStuckWhy(list, label): rows sharing a reason are named together in front of it, first-seen order kept;
    different reasons stay separate;
  * the stuck tip builds both halves (inside the newest-N window and older) through it.
Drives the SHIPPED _fleetStuckWhy, cut from control_ui.html and run in node. A missing node raises.
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
FN = ("  function _fleetStuckWhy(list, label){\n", "join('  |  ');\n  }\n")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _why(rows):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    start, end = FN
    if s.count(start) != 1:
        raise AssertionError("_fleetStuckWhy's anchor matched %d times - re-point this law" % s.count(start))
    i = s.index(start)
    fn = s[i:s.index(end, i) + len(end)]
    # #231 eye on v3623: the end anchor is the FIRST match after the start - a cut that stops inside the function runs
    # a truncated body in node. A whole function balances its braces; anything else refuses loudly.
    if fn.count("{") != fn.count("}"):
        raise AssertionError("the cut is not a whole function (%d '{' vs %d '}') - the end anchor stopped inside it; "
                             "re-point this law" % (fn.count("{"), fn.count("}")))
    js = ("%s\nconsole.log(JSON.stringify(_fleetStuckWhy(%s, function(e){ return e.station + ' ' + e.n; })));\n"
          % (fn, json.dumps(rows)))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut function did not run in node: %s" % r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class ASharedReasonIsSaidOnce(unittest.TestCase):

    def test_two_rows_with_one_reason_say_it_once(self):
        lane = "vault lane: owes 7, 4168 read(s) on record"
        got = _why([{"station": "PRINTER 2", "n": 1, "why": lane}, {"station": "PRINTER 1", "n": 2, "why": lane},
                    {"station": "STATION 5", "n": 3, "why": "the reel sweep owes 9 read(s)"}])
        self.assertEqual(got.count(lane), 1, "a shared reason was printed once per row: %r" % got)
        self.assertEqual(got, "PRINTER 2 1 · PRINTER 1 2: " + lane + "  |  STATION 5 3: the reel sweep owes 9 read(s)")

    def test_different_reasons_stay_apart(self):
        got = _why([{"station": "A", "n": 1, "why": "x"}, {"station": "B", "n": 1, "why": "y"}])
        self.assertEqual(got, "A 1: x  |  B 1: y")

    def test_the_stuck_tip_builds_both_halves_through_it(self):
        s = _src()
        self.assertEqual(s.count("_fleetStuckWhy(inside, _stuckLabel)"), 1, "the newest-N half repeats shared reasons again")
        self.assertEqual(s.count("whyBits.push(_fleetStuckWhy(beyond, _stuckLabel));"), 1,
                         "the older half repeats shared reasons again")


RED_PROOF = [
    {"why": "REG-2059 - two rows with one reason print it twice again",
     "file": "control_ui.html",
     "find": "      if (!Object.prototype.hasOwnProperty.call(by, w)) { by[w] = []; order.push(w); }\n",
     "replace": "      w = w + '\\u200b' + order.length; by[w] = []; order.push(w);\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
