# -*- coding: utf-8 -*-
"""#292 (REG-2066) - THE "ENGINES JOINED TO THE RIVER" HEADER COUNTS WHAT EACH ROW SAYS.

GrokBot ticks 419-422 on #230 (K13/K18): the Heart printed "ENGINES JOINED TO THE RIVER · 13 OF 14 · 1 REACH NO REEL" over
rows that read 9 JOINED, 4 NO DATA (declared_vs_content, main_character, slot_identity, write_witness) and 1 UNJOINED
(tooltip_find). The header was rows - unjoined, so an engine with no data counted as joined.

  * _hrtJoinsHead(rows, gap): "N of M joined", then each other state that is present ("by design", "no data yet",
    "reach no reel"), "all connected" only when every engine is joined or by design;
  * the Heart's joined section prints it.
Drives the SHIPPED _hrtJoinsHead, cut from control_ui.html and run in node. A missing node raises.
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
FN = ("  function _hrtJoinsHead(rows, gap){\n", "    return bits.join(' · ');\n  }\n")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _head(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    start, end = FN
    if s.count(start) != 1:
        raise AssertionError("_hrtJoinsHead's anchor matched %d times - re-point this law" % s.count(start))
    i = s.index(start)
    fn = s[i:s.index(end, i) + len(end)]
    js = "var window = {};\n%s\nconsole.log(JSON.stringify(%s.map(function(c){ return _hrtJoinsHead(c[0], c[1]); })));\n" % (
        fn, json.dumps(cases))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut function did not run in node: %s" % r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def _rows(**states):
    out = []
    for st, n in states.items():
        out += [{"state": st.replace("_", " ")} for _ in range(n)]
    return out


class TheJoinedCensusCountsWhatEachRowSays(unittest.TestCase):

    def test_his_heart_reads_nine_of_fourteen(self):
        rows = _rows(JOINED=9, NO_DATA=4, UNJOINED=1)
        got = _head([[rows, 1]])[0]
        self.assertTrue(got.startswith("9 of 14 joined"), "an engine with no data was counted as joined: %r" % got)
        self.assertIn("4 no data yet", got)
        self.assertIn("1 reach no reel", got)

    def test_all_connected_only_when_it_is_true(self):
        got = _head([[_rows(JOINED=5, BY_DESIGN=1), 0], [_rows(JOINED=5, NO_DATA=1), 0]])
        self.assertIn("all connected", got[0], got)
        self.assertNotIn("all connected", got[1], "a no-data engine was called connected: %r" % got[1])

    def test_the_heart_prints_it(self):
        self.assertEqual(_src().count("'<div class=\"hrt-sec\"><div class=\"hrt-h\">Engines joined to the river · ' + _hrtJoinsHead(rows, gap)"), 1,
                         "the joined section no longer prints the per-state header")


RED_PROOF = [
    {"why": "REG-2066 - the joined header counts no-data engines as joined again (13 of 14 over 9 joined)",
     "file": "control_ui.html",
     "find": "    var tot = (rows || []).length, bits = [n.JOINED + ' of ' + tot + ' joined'];\n",
     "replace": "    var tot = (rows || []).length, bits = [(tot - (gap || 0)) + ' of ' + tot + ' joined'];\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
