# -*- coding: utf-8 -*-
"""REG-2083 - THE MISSED-TEXT COUNTS SAY HOW THEY RELATE: STILL UNREAD, RECOVERED, AND THE FRAMES THE FIRST PASS MISSED.

GrokBot tick 424 on #230 (K08/K09): Session 29's chip read 'swept · 3 missed-text', its MISSED TEXT list held 5 rows (two
'Heart of the Oak', three '— unreadable text —') and the recovery chip 'recovered 2/5'. MEASURED in control_app: all three are
true - kai.missedFrames is len(missed), the still-unread ledger; superRecovery.missed is recovered + still unread; the list
is those same frames. The chip and the list header now say which number is which.

Drives the SHIPPED _missedSay, cut from control_ui.html and run in node; the list header is pinned by its full expression.
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
CUT = ("  function _missedSay(sm){\n", "\n    return 'swept · ' + sm.kaiMissed + ' missed-text still unread';\n  }\n")
HEAD = ("' · ' + _msr.missed + ' frame' + (_msr.missed === 1 ? '' : 's') + ': ' + (_msr.recovered || 0) + ' recovered (named), '"
        " + (_msr.missed - (_msr.recovered || 0)) + ' still unread'")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _say(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    start, end = CUT
    if s.count(start) != 1:
        raise AssertionError("_missedSay's anchor matched %d times - re-point this law" % s.count(start))
    i = s.index(start)
    fn = s[i:s.index(end, i) + len(end)]
    js = "%s\nconsole.log(JSON.stringify(%s.map(_missedSay)));\n" % (fn, json.dumps(cases))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("_missedSay did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheMissedTextCountsSayHowTheyRelate(unittest.TestCase):

    def test_session_29_says_still_unread_and_recovered_of_missed(self):
        out = _say([{"kaiMissed": 3, "superRecovery": {"recovered": 2, "missed": 5}}])[0]
        self.assertEqual(out, "swept · 3 still unread · 2 of 5 missed frames recovered",
                         "the chip's 3 still does not say it is the still-unread part of 5: %r" % out)

    def test_with_nothing_recovered_it_says_still_unread(self):
        self.assertEqual(_say([{"kaiMissed": 4}])[0], "swept · 4 missed-text still unread")
        self.assertEqual(_say([{"kaiMissed": 4, "superRecovery": {"recovered": 0, "missed": 4}}])[0],
                         "swept · 4 missed-text still unread")

    def test_an_unswept_reel_says_nothing(self):
        self.assertEqual(_say([{}])[0], "", "an unswept reel was given a missed-text count")

    def test_the_chip_the_shelf_and_the_list_header_use_it(self):
        s = _src()
        self.assertEqual(s.count("chips.push('<span class=\"dsr-chip\">🧠 ' + esc(_missedSay(sm)) + '</span>');"), 1, "the dossier chip counts on its own again")
        self.assertEqual(s.count("vparts.push('🧠 ' + esc(_missedSay(sm)));"), 1, "the shelf card counts on its own again")
        self.assertEqual(s.count(HEAD), 1, "the MISSED TEXT list no longer says what its rows are")


RED_PROOF = [
    {"why": "REG-2083 - the chip prints a bare count again, beside a list of a different length",
     "file": "tv/control_ui.html",
     "find": "      return 'swept · ' + sm.kaiMissed + ' still unread · ' + sr.recovered + ' of ' + sr.missed + ' missed frames recovered';\n",
     "replace": "      return 'swept · ' + sm.kaiMissed + ' missed-text';\n",
     "matches": 1},
    {"why": "REG-2083 - the list header stops naming its parts",
     "file": "tv/control_ui.html",
     "find": "    var missSec = missDrill ? '<div class=\"dsr-sec\"><div class=\"dsr-h\">🔬 Missed text' + _mHead + ' · tap to jump</div>'",
     "replace": "    var missSec = missDrill ? '<div class=\"dsr-sec\"><div class=\"dsr-h\">🔬 Missed text · tap to jump</div>'",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
