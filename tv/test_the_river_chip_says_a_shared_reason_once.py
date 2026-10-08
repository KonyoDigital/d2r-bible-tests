# -*- coding: utf-8 -*-
"""REG-2072 - THE FLEET ROW'S "river stuck" CHIP SAYS A SHARED REASON ONCE, AND AN OLDER ROW WEARS ITS AGE AS A LABEL.

GrokBot tick 423 on #230 (v3623, K07): hovering Konyo's "river stuck" printed 'PRINTER 2: older than the newest 16 - vault
lane: owes 7 ...' and again 'PRINTER 1: vault lane: owes 7 ...', 'the reel sweep owes 9 ...' twice under STATION 5, and the
deleter's refusal for ROUTED 8 and CAPTURE 5 - "Rows that share a reason are never named together before it". REG-2059
had grouped the fleet CARD's tip through _fleetStuckWhy; the chip kept a row-by-row copy of its own, and a row past the
keep window carries the server's 'older than the newest N - ' in front of the same reason, so even grouping could not
see two spellings of one reason as one.

  * every distinct reason is said exactly once, with the rows that share it named together in front of it;
  * the server's 'older than the newest N - ' prefix becomes the row's ' older' label (the card's own word).
Drives the SHIPPED _fleetStuckChip and _fleetStuckWhy, cut from control_ui.html and run in node. A missing node raises.
"""
import html
import json
import os
import re
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
CHIP = ("  var _fleetStuckChip = function (m) {\n", "    return bits.join('');\n  };\n")
WHY = ("  function _fleetStuckWhy(list, label){\n", "join('  |  ');\n  }\n")

VAULT = "vault lane: owes 7, 4318 read(s) on record; 3 ruled empty by the triage"
SWEEP = "the reel sweep owes 9 read(s) - its last word: the sweep door is LOCKED"
DELETER = "the deleter refused: frame.release is LOCKED"
ROWS = [{"station": "PRINTER", "n": 2, "window": False, "why": "older than the newest 16 - " + VAULT},
        {"station": "STATION", "n": 5, "why": SWEEP},
        {"station": "ROUTED", "n": 8, "why": DELETER},
        {"station": "STATION", "n": 5, "why": "older than the newest 16 - " + SWEEP},
        {"station": "PRINTER", "n": 1, "why": VAULT},
        {"station": "CAPTURE", "n": 5, "why": DELETER}]


def _cut(s, pair):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start.strip()[:40], s.count(start)))
    i = s.index(start)
    fn = s[i:s.index(end, i) + len(end)]
    if fn.count("{") != fn.count("}"):
        raise AssertionError("the cut %r is not a whole function - its end anchor stopped inside it" % start.strip()[:40])
    return fn


def _tip(rows):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    with open(UI, encoding="utf-8") as f:
        s = f.read()
    js = """
var window = {};
function escC(x){ return String(x).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
%s
%s
var m = { system: { river: { stuck: %s, heart: { census: 'current' } } } };
console.log(JSON.stringify(_fleetStuckChip(m)));
""" % (_cut(s, WHY), _cut(s, CHIP), json.dumps(rows))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut functions did not run in node: %s" % r.stderr[-600:])
    out = json.loads(r.stdout.strip().splitlines()[-1])
    m = re.search(r'class="fleet-riverstuck" title="river stuck on this PC - ([^"]*)"', out)
    if not m:
        raise AssertionError("premise: the chip painted no river-stuck tip: %r" % out[:300])
    return html.unescape(m.group(1))


class TheRiverChipSaysASharedReasonOnce(unittest.TestCase):

    def test_every_reason_is_said_once(self):
        tip = _tip(ROWS)
        for reason in (VAULT, SWEEP, DELETER):
            self.assertEqual(tip.count(reason), 1, "%r is said %d times in the chip's tip: %r" % (reason, tip.count(reason), tip))

    def test_rows_that_share_a_reason_are_named_together_in_front_of_it(self):
        tip = _tip(ROWS)
        self.assertIn("PRINTER 2 older · PRINTER 1: " + VAULT, tip)
        self.assertIn("STATION 5 · STATION 5 older: " + SWEEP, tip)
        self.assertIn("ROUTED 8 · CAPTURE 5: " + DELETER, tip)

    def test_the_server_prefix_becomes_the_older_label(self):
        tip = _tip(ROWS)
        self.assertNotIn("older than the newest", tip, "the row's age is printed as part of its reason again: %r" % tip)


RED_PROOF = [
    {"why": "REG-2072 - the chip prints its own row-by-row copy again instead of the shared grouping",
     "file": "tv/control_ui.html",
     "find": "      var tip = _fleetStuckWhy(sk.map(function (e) {\n",
     "replace": "      var tip = (function (L, lab) { return L.map(function (r) { return lab(r) + ': ' + r.why; }).join(' | '); })(sk.map(function (e) {\n",
     "matches": 1},
    {"why": "REG-2072 - the server's 'older than the newest N' prefix stays in the reason, so one reason has two spellings",
     "file": "tv/control_ui.html",
     "find": "                 why: w.replace(_olderRe, '') };\n",
     "replace": "                 why: w };\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
