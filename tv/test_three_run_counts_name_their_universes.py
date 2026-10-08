# -*- coding: utf-8 -*-
"""#283 (REG-2077) - THE THREE RUN COUNTS SAY WHAT THEY COUNT, SO THEY CAN BE RECONCILED ON SCREEN.

GrokBot tick 418 on #230 (K11): TV·D HISTORY '162 RUNS', the Theatre 'session 41/216', the River '8 RUNS' - three numbers
for "runs" and nothing saying how they relate. Measured in the code: the TV·D strip is /api/sessions without its empty
stubs (216 - 54 = 162), the Theatre indexes every run journaled (216, empty ones too), and the shelf shows the runs that
kept film. Now TV·D says '162 runs · 54 empty not shown (all 216)' and the Theatre 'session 41 of all 216', so the two
meet in one number; the shelf's own header already names its population (v3191).
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

UI = os.path.join(HERE, "control_ui.html")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


class ThreeRunCountsNameTheirUniverses(unittest.TestCase):

    def test_the_tvd_strip_says_what_it_left_out_and_of_what(self):
        s = _src()
        self.assertEqual(s.count("      HD_TOTAL = (j.sessions || []).length;"), 1, "the strip no longer keeps the whole universe it filtered")
        self.assertEqual(s.count("      + (_hdEmpty ? ' · ' + _hdEmpty + ' empty not shown (all ' + HD_TOTAL + ')' : '') + ' · tap to explore';"), 1,
                         "the TV·D count no longer says how many empty runs it left out of how many")
        self.assertEqual(s.count("    var _hdEmpty = (typeof HD_TOTAL === 'number' && HD_TOTAL > runs.length) ? HD_TOTAL - runs.length : 0;"), 1,
                         "an unknown total must say nothing, never a number")

    def test_the_theatre_index_names_its_universe(self):
        s = _src()
        self.assertEqual(s.count("    $('th-sess').textContent = 'session ' + TH.sn + ' of all ' + TH.sessions.length"), 1,
                         "the theatre's 'session N/M' no longer says M is every run journaled")
        self.assertEqual(s.count("'session ' + TH.sn + '/' + TH.sessions.length"), 0, "the bare 'N/M' is back")


RED_PROOF = [
    {"why": "REG-2077 - the TV·D strip stops saying how many empty runs it left out",
     "file": "tv/control_ui.html",
     "find": "      + (_hdEmpty ? ' · ' + _hdEmpty + ' empty not shown (all ' + HD_TOTAL + ')' : '') + ' · tap to explore';",
     "replace": "      + ' · tap to explore';",
     "matches": 1},
    {"why": "REG-2077 - the theatre's index goes back to a bare 'N/M'",
     "file": "tv/control_ui.html",
     "find": "    $('th-sess').textContent = 'session ' + TH.sn + ' of all ' + TH.sessions.length",
     "replace": "    $('th-sess').textContent = 'session ' + TH.sn + '/' + TH.sessions.length",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
