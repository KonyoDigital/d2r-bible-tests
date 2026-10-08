# -*- coding: utf-8 -*-
"""#277 (REG-2055) - A SESSION IS A "CLEAN RUN" ONLY WHEN NOTHING WENT UNREAD; "A FULL READ" NEEDS SOMETHING READ.

GrokBot ticks 416-418 on #230 (v3621): Session 30 read "CLEAN RUN" beside "0% coverage · 0 of 10 item reads · 10 gaps" and
ten "- unreadable text -" rows; Session 41 read "CLEAN RUN", "0 READS" and the chip "no missed text - a full read" directly
under "- no reads on this reel -". The seal asked only the watchdog; the chip asked only the missed-text count.

  * _runSeal: unsealed -> open; a watchdog flag -> flag; unread item moments or missed-text frames -> gaps; else clean.
    The card's seal and the copied summary read the same verdict;
  * the recovery chip says "a full read" only when the reel was read and no item moment is unread;
  * REG-2071 (GrokBot tick 423 K14): the Shelf card's verdict line, seal badge and filter token ask the same _runSeal.
Drives the SHIPPED _runSeal and _dossierRecovery, cut from control_ui.html and run in node. A missing node raises; this law
does not skip.
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
SEAL = ("  function _runSeal(sm){\n", "    return { k: 'clean' };\n  }\n")
SAY = ("  function _runSealGapsSay(rs){\n", "    return b.join(' · ');\n  }\n")
RECOV = ("  function _dossierRecovery(sm){\n", "a full read</span>';\n  }\n")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _cut(s, pair):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start[:50], s.count(start)))
    i = s.index(start)
    return s[i:s.index(end, i) + len(end)]


def _node(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    js = """
var window = {};
%s
%s
%s
var C = %s, O = [];
C.forEach(function(sm){ O.push({ seal: _runSeal(sm), chip: _dossierRecovery(sm) }); });
console.log(JSON.stringify(O));
""" % (_cut(s, SEAL), _cut(s, SAY), _cut(s, RECOV), json.dumps(cases))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut functions did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class ACleanRunHasNoGaps(unittest.TestCase):

    def test_the_seal_reads_every_state(self):
        out = _node([{}, {"kaiMissed": 0, "watchdogViolations": 2}, {"kaiMissed": 5, "reads": 9},
                     {"kaiMissed": 0, "reads": 0, "coverage": {"gaps": 10, "total": 10, "read": 0}},
                     {"kaiMissed": 0, "reads": 7, "coverage": {"gaps": 0, "total": 7, "read": 7}}])
        self.assertEqual([o["seal"]["k"] for o in out], ["open", "flag", "gaps", "gaps", "clean"],
                         "a run with gaps was sealed clean (or a clean one was not): %r" % [o["seal"] for o in out])

    def test_a_reel_with_no_reads_is_never_a_full_read(self):
        out = _node([{"kaiMissed": 0, "reads": 0}, {"kaiMissed": 0, "reads": 4, "coverage": {"gaps": 3}},
                     {"kaiMissed": 0, "reads": 4, "coverage": {"gaps": 0}}])
        self.assertNotIn("a full read", out[0]["chip"], "a reel nobody read was called a full read")
        self.assertIn("nothing on this reel was read", out[0]["chip"])
        self.assertNotIn("a full read", out[1]["chip"], "a reel with unread item moments was called a full read")
        self.assertIn("a full read", out[2]["chip"])

    def test_the_card_and_the_summary_ask_the_same_seal(self):
        s = _src()
        self.assertEqual(s.count("    var _rs = _runSeal(sm);"), 1, "the card's seal no longer asks _runSeal")
        self.assertEqual(s.count("    var _rsV = _runSeal(sm);"), 1, "the copied summary no longer asks _runSeal")

    def test_every_shelf_surface_asks_the_same_seal(self):
        """REG-2071 (GrokBot tick 423 K14) - Session 48's Shelf card wore '🛡 clean' over a dossier reading 'SEALED WITH GAPS ·
        8 gaps': the card's verdict line, its seal badge and its filter token each kept their own `kaiMissed != null` rule."""
        s = _src()
        for expr, what in (("      var _shRs = _runSeal(sm);\n", "the shelf card's verdict line"),
                           ("      var _sealRs = _runSeal(sm);", "the shelf card's seal badge"),
                           ("      var _verd = ({ flag: 'flagged', gaps: 'gaps', clean: 'clean' })[_runSeal(sm).k] || 'unsealed';",
                            "the shelf filter's verdict token")):
            self.assertEqual(s.count(expr), 1, "%s no longer asks _runSeal" % what)
        self.assertEqual(s.count(": (sm.kaiMissed != null ? '<span class=\"shc-seal clean\">"), 0,
                         "a shelf seal decides 'clean' on the missed-text count alone again")

    def test_the_last_session_and_history_badges_ask_the_same_seal(self):
        """REG-2086 - TV·D's LAST SESSION badge and the HISTORY card's shield read the watchdog alone: '🛡 CLEAN' over a reel
        sealed with gaps, the third and fourth copies of the rule."""
        s = _src()
        self.assertEqual(s.count("      var _lsRs = _runSeal(t);"), 1, "the LAST SESSION badge no longer asks _runSeal")
        self.assertEqual(s.count("      var _hhRs = _runSeal(sm);"), 1, "the HISTORY card's shield no longer asks _runSeal")
        self.assertEqual(s.count("clean = !(t.watchdogViolations > 0);"), 0, "a badge decides CLEAN on the watchdog alone again")
        self.assertEqual(s.count("clean = !(sm.watchdogViolations > 0);"), 0, "a badge decides CLEAN on the watchdog alone again")


RED_PROOF = [
    {"why": "REG-2055 - a run with unread gaps is sealed clean again",
     "file": "control_ui.html",
     "find": "    if (gaps || missed) return { k: 'gaps', gaps: gaps, missed: missed };\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2055 - a reel nobody read is called a full read again",
     "file": "control_ui.html",
     "find": "    if (sm.reads === 0) return '<span class=\"dsr-recov dsr-recov-plain\">",
     "replace": "    if (false) return '<span class=\"dsr-recov dsr-recov-plain\">",
     "matches": 1},
    {"why": "REG-2071 - the shelf card's verdict line decides clean on its own again",
     "file": "control_ui.html",
     "find": "      var _shRs = _runSeal(sm);\n",
     "replace": "      var _shRs = { k: sm.kaiMissed != null ? 'clean' : 'open' };\n",
     "matches": 1},
    {"why": "REG-2071 - the shelf card's seal badge reads clean over gaps again",
     "file": "control_ui.html",
     "find": "      var _sealRs = _runSeal(sm);",
     "replace": "      var _sealRs = { k: sm.kaiMissed != null ? 'clean' : 'open' };",
     "matches": 1},
    {"why": "REG-2086 - the LAST SESSION badge decides CLEAN on its own again",
     "file": "control_ui.html",
     "find": "      var _lsRs = _runSeal(t);",
     "replace": "      var _lsRs = { k: (t.watchdogViolations > 0) ? 'flag' : 'clean', n: t.watchdogViolations };",
     "matches": 1},
    {"why": "REG-2086 - the HISTORY card's shield reads clean over gaps again",
     "file": "control_ui.html",
     "find": "      var _hhRs = _runSeal(sm);",
     "replace": "      var _hhRs = { k: (sm.kaiMissed == null) ? 'open' : (sm.watchdogViolations > 0 ? 'flag' : 'clean') };",
     "matches": 1},
    {"why": "REG-2055 - the card's seal stops asking the shared verdict",
     "file": "control_ui.html",
     "find": "    var _rs = _runSeal(sm);",
     "replace": "    var _rs = { k: 'clean' };",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
