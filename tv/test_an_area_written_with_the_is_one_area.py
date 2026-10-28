# -*- coding: utf-8 -*-
"""REG-2709 (GrokBot's 02:05 pass on v3816) - AN AREA WRITTEN WITH "THE" IS ONE AREA.

The Shelf's "Where you farm" ranked "Rogue Encampment" (22 runs) and "The Rogue Encampment" (6 runs) as two places - the
reader writes an area both ways. _hmAggregate folds a leading "The" off the key and names the row without it; an area
still counts once per run.

Drives the SHIPPED _hmAggregate (cut from control_ui.html) in node over a stub run list. RED_PROOF below.
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
START = "  function _hmAggregate(){\n"
END = "\n    return { areas: arr, totalRuns: runs.length };\n  }\n"

PROGRAM = r"""
var RUNS = [
  { areas: ['Rogue Encampment', 'The Pit'], reads: 10, finds: [] },
  { areas: ['The Rogue Encampment', 'Rogue Encampment'], reads: 5, finds: [{ tier: 'grail' }] },
  { areas: ['the rogue encampment'], reads: 2, finds: [] },
  { areas: ['Theater of Blood'], reads: 1, finds: [] }
];
function _cmpList(){ return RUNS; }
%s
console.log(JSON.stringify(_hmAggregate()));
"""


def _run():
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    with open(UI, encoding="utf-8") as fh:
        s = fh.read()
    if s.count(START) != 1:
        raise AssertionError("PREMISE: _hmAggregate moved (%d)" % s.count(START))
    i = s.index(START)
    fn = s[i:s.index(END, i) + len(END)]
    r = subprocess.run([NODE, "-"], input=PROGRAM % fn, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut function did not run in node: %s" % r.stderr[-800:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AnAreaWrittenWithTheIsOneArea(unittest.TestCase):

    def test_the_two_spellings_are_one_row_counted_once_per_run(self):
        o = _run()
        rows = {a["name"]: a for a in o["areas"]}
        self.assertNotIn("The Rogue Encampment", rows, "an area written with 'The' ranked as its own place: %r" % o)
        self.assertEqual(rows["Rogue Encampment"]["runs"], 3, "a run that wrote it both ways counted twice: %r" % rows)
        self.assertEqual(rows["Rogue Encampment"]["grails"], 1)
        self.assertIn("Pit", rows, "the row is not named without its 'The'")

    def test_a_word_that_only_begins_with_the_letters_is_untouched(self):
        o = _run()
        self.assertIn("Theater of Blood", [a["name"] for a in o["areas"]], "'Theater' lost its 'The'")


RED_PROOF = [
    {"why": "REG-2709 - 'The Rogue Encampment' ranks as its own place again",
     "file": "tv/control_ui.html",
     "find": "        var bare = a.replace(/^the\\s+/i, '');\n",
     "replace": "        var bare = a;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2709 - the fold eats the start of any word that begins with 'the'",
     "file": "tv/control_ui.html",
     "find": "        var bare = a.replace(/^the\\s+/i, '');\n",
     "replace": "        var bare = a.replace(/^the\\s*/i, '');\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
