# -*- coding: utf-8 -*-
"""REG-2164 (#252) - a watchdog row is not missed text.

Session 74's shelf card said "1 miss" beside a dossier that said
"no missed text — a full read". The card's "miss" was the watchdog
count (journal rows whose lane is watchdog). The dossier's sentence
is kaiMissed. Those are different counters. _watchdogCountSay is the
word the dossier seal already used. A missing count and a measured 0
stay blank. Missed text keeps its own sentence.

Drives the shipped functions, cut from control_ui.html and run in node.
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

CARD = (
    "      var _shRs = _runSeal(sm);\n",
    "        vparts.push('<span class=\"sh-clean\">🛡 clean</span>');\n      }\n",
)
HOME = (
    "          var wd = st.watchdog;\n",
    "          return '<span class=\"hd-chip warn\" title=\"expected-vs-happened check on the last sealed session\">🚨 WATCHDOG · ' + _watchdogCountSay(wd.violations) + ' last session</span>';\n",
)
LEDGER = (
    "    var ldStat = (journalUnread ? '—' : (st.journalMB + ' MB')) + (viol ? ' <span class=\"eh-x\">·</span> <span style=\"color:#ff9a7a\">' + _watchdogCountSay(viol) + '</span>' : '');\n",
    "    var ldStat = (journalUnread ? '—' : (st.journalMB + ' MB')) + (viol ? ' <span class=\"eh-x\">·</span> <span style=\"color:#ff9a7a\">' + _watchdogCountSay(viol) + '</span>' : '');\n",
)


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _fn(src, name):
    needle = "function %s" % name
    start = src.find(needle)
    if start < 0:
        raise AssertionError("%s is gone" % name)
    if src.find(needle, start + 1) != -1:
        raise AssertionError("%s is declared more than once" % name)
    i = src.find("{", start)
    depth = 0
    for j in range(i, len(src)):
        ch = src[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[start:j + 1]
    raise AssertionError("%s never closed" % name)


def _cut(src, pair):
    start, end = pair
    n = src.count(start)
    if n != 1:
        raise AssertionError("anchor %r matched %d times" % (start[:60], n))
    i = src.index(start)
    j = src.index(end, i)
    if j < 0:
        raise AssertionError("end anchor missing after the start")
    return src[i:j + len(end)]


def _paint():
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    src = _src()
    js = """
%s
%s
%s
%s
function _cardLine(sm){
  var vparts = [];
%s
  return vparts.join(' | ');
}
function _homeWatch(st){
%s
}
function _ledgerStat(st, journalUnread, viol){
%s
  return ldStat;
}
var flagged = {kaiMissed: 0, watchdogViolations: 1, reads: 3, coverage: {gaps: 0}};
var two = {kaiMissed: 0, watchdogViolations: 2, reads: 3, coverage: {gaps: 0}};
var gaps = {kaiMissed: 5, watchdogViolations: 0, reads: 9, coverage: {gaps: 0}};
var clean = {kaiMissed: 0, watchdogViolations: 0, reads: 4, coverage: {gaps: 0}};
console.log(JSON.stringify({
  say1: _watchdogCountSay(1),
  say2: _watchdogCountSay(2),
  say0: _watchdogCountSay(0),
  sayMissing: _watchdogCountSay(null),
  card1: _cardLine(flagged),
  card2: _cardLine(two),
  cardGaps: _cardLine(gaps),
  cardClean: _cardLine(clean),
  chip: _dossierRecovery(flagged),
  seal: _runSeal(flagged),
  home1: _homeWatch({watchdog: {violations: 1}}),
  home0: _homeWatch({watchdog: {violations: 0}}),
  homeMissing: _homeWatch({}),
  led1: _ledgerStat({journalMB: 2}, false, 1),
  led0: _ledgerStat({journalMB: 2}, false, 0)
}));
""" % (
        _fn(src, "_watchdogCountSay(n){"),
        _fn(src, "_runSeal(sm){"),
        _fn(src, "_runSealGapsSay(rs){"),
        _fn(src, "_dossierRecovery(sm){"),
        _cut(src, CARD),
        _cut(src, HOME),
        _cut(src, LEDGER),
    )
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut did not run in node: %s" % r.stderr[-800:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AWatchdogFlagIsNotMissedText(unittest.TestCase):

    def test_one_watchdog_row_says_flagged_beside_a_full_read(self):
        got = _paint()
        self.assertEqual(got["say1"], "1 flagged")
        self.assertEqual(got["say2"], "2 flagged")
        self.assertEqual(got["say0"], "")
        self.assertEqual(got["sayMissing"], "")
        self.assertEqual(got["seal"]["k"], "flag")
        self.assertEqual(got["seal"]["n"], 1)
        self.assertIn("1 flagged", got["card1"])
        self.assertNotIn("miss", got["card1"])
        self.assertIn("2 flagged", got["card2"])
        self.assertNotIn("miss", got["card2"])
        self.assertIn("no missed text", got["chip"])
        self.assertIn("a full read", got["chip"])
        self.assertNotIn("miss", got["home1"])
        self.assertIn("1 flagged", got["home1"])
        self.assertIn("WATCHDOG", got["home1"])
        self.assertEqual(got["home0"], "")
        self.assertEqual(got["homeMissing"], "")
        self.assertIn("1 flagged", got["led1"])
        self.assertNotIn("miss", got["led1"])
        self.assertNotIn("flagged", got["led0"])

    def test_missed_text_keeps_its_own_word_and_a_clean_run_is_not_flagged(self):
        got = _paint()
        self.assertIn("missed-text", got["cardGaps"])
        self.assertNotIn("flagged", got["cardGaps"])
        self.assertIn("clean", got["cardClean"])
        self.assertNotIn("flagged", got["cardClean"])
        self.assertNotIn("miss", got["cardClean"])

    def test_every_watchdog_count_asks_the_one_word(self):
        src = _src()
        self.assertEqual(src.count("function _watchdogCountSay(n){"), 1)
        self.assertEqual(src.count("_watchdogCountSay("), 6)
        for call in (
            "_watchdogCountSay(_shRs.n)",
            "_watchdogCountSay(wd.violations)",
            "_watchdogCountSay(viol)",
            "_watchdogCountSay(_rs.n)",
            "_watchdogCountSay(_rsV.n)",
        ):
            self.assertEqual(src.count(call), 1, call)


RED_PROOF = [
    {
        "why": "REG-2164 - a watchdog row is called a miss again",
        "file": "tv/control_ui.html",
        "find": "    return n + ' flagged';\n",
        "replace": "    return n + ' miss' + (n > 1 ? 'es' : '');\n",
        "matches": 1,
    },
    {
        "why": "REG-2164 - the shelf card prints 1 miss beside a full read again",
        "file": "tv/control_ui.html",
        "find": "        vparts.push('<span class=\"sh-warn\">🚨 ' + _watchdogCountSay(_shRs.n) + '</span>');\n",
        "replace": "        vparts.push('<span class=\"sh-warn\">🚨 ' + _shRs.n + ' miss' + (_shRs.n > 1 ? 'es' : '') + '</span>');\n",
        "matches": 1,
    },
    {
        "why": "REG-2164 - the home chip calls a watchdog row a miss again",
        "file": "tv/control_ui.html",
        "find": "          return '<span class=\"hd-chip warn\" title=\"expected-vs-happened check on the last sealed session\">🚨 WATCHDOG · ' + _watchdogCountSay(wd.violations) + ' last session</span>';\n",
        "replace": "          return '<span class=\"hd-chip warn\" title=\"expected-vs-happened check on the last sealed session\">🚨 WATCHDOG · ' + wd.violations + ' miss' + (wd.violations > 1 ? 'es' : '') + ' last session</span>';\n",
        "matches": 1,
    },
    {
        "why": "REG-2164 - the ledger stat calls a watchdog row a miss again",
        "file": "tv/control_ui.html",
        "find": " + _watchdogCountSay(viol) + '</span>' : '');\n",
        "replace": " + viol + ' miss</span>' : '');\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
