# -*- coding: utf-8 -*-
"""REG-2025 - ONE DRIFT GETS ONE ADVICE: THE PAGE-NEWER LINE DEFERS WHILE "RELAUNCH NOW" IS ARMED. #266, GrokBot K11.

GrokBot, ticks 409 and 413: the fleet bar's "v3617 is on disk - this window is still running the old one. Relaunch to use
it. [RELAUNCH NOW]" and the pink #page-newer line "this window is newer than the console behind it - reopen TV DIABLO from
the Desktop icon" were on screen at once. Both fire on the SAME fact (the console process runs an older build than the
files on disk) and give opposite advice. The relaunch banner is the answer whenever it is armed - the console can relaunch
itself - so the Desktop-icon line now speaks only when that banner is not showing. armRelaunch marks the bar
data-stage="ready" (and the behind-the-fleet announcement marks it "behind", a different fact that keeps both lines).

Source-reading law, comments stripped, every anchor counted once; the decision is driven in node on the exact lines cut
from the page.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

UI = os.path.join(HERE, "control_ui.html")
NODE = shutil.which("node")
DEFER = "      if (_newer && _fb && !_fb.hidden && _fb.getAttribute('data-stage') === 'ready') _newer = '';\n"


def _code():
    with io.open(UI, encoding="utf-8") as fh:
        raw = fh.read()
    return re.sub(r"/\*.{0,4000}?\*/", "", raw, flags=re.S), raw


class OneDriftGetsOneAdvice(unittest.TestCase):

    def test_the_relaunch_banner_marks_its_stage(self):
        code, _raw = _code()
        self.assertEqual(code.count("      stage = 'ready';\n      bar.setAttribute('data-stage', 'ready');"), 1,
                         "armRelaunch no longer marks the bar as armed, so the page-newer line cannot tell it is showing")
        self.assertEqual(code.count("        stage = 'behind';\n        bar.setAttribute('data-stage', 'behind');"), 1,
                         "the behind-the-fleet announcement is not marked apart from an armed relaunch")

    @unittest.skipUnless(NODE, "no node on this machine - UNMEASURED here, not passing")
    def test_the_page_newer_line_defers_only_while_the_relaunch_is_armed(self):
        _code_, raw = _code()
        self.assertEqual(raw.count(DEFER), 1, "the deferral line is gone or doubled")
        prog = """
          var DEFER = %s;
          function decide(newer, hidden, stage){
            var _newer = newer;
            var _fb = { hidden: hidden, getAttribute: function(k){ return k === 'data-stage' ? stage : null; } };
            eval(DEFER);
            return _newer;
          }
          var T = 'this window is newer than the console behind it';
          process.stdout.write(JSON.stringify({
            armed: decide(T, false, 'ready'), behind: decide(T, false, 'behind'),
            hidden: decide(T, true, 'ready'), none: decide('', false, 'ready') }));
        """ % json.dumps(DEFER)
        out = json.loads(subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30).stdout)
        self.assertEqual(out["armed"], "", "both lines still show while RELAUNCH NOW is armed (K11)")
        self.assertEqual(out["behind"], "this window is newer than the console behind it",
                         "the behind-the-fleet bar (a different fact) silenced the page-newer line")
        self.assertEqual(out["hidden"], "this window is newer than the console behind it",
                         "a dismissed relaunch bar still silenced the only other advice")
        self.assertEqual(out["none"], "", out)


RED_PROOF = [
    {"why": "REG-2025 - the page-newer line shows beside an armed RELAUNCH NOW again",
     "file": "tv/control_ui.html",
     "find": DEFER,
     "replace": "",
     "matches": 1},
    {"why": "REG-2025 - armRelaunch stops marking its stage",
     "file": "tv/control_ui.html",
     "find": "      bar.setAttribute('data-stage', 'ready');   /* #266 (K11) - the page-newer line reads this and defers to RELAUNCH NOW */\n",
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
