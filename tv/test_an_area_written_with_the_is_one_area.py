# -*- coding: utf-8 -*-
"""REG-2709 (GrokBot's 02:05 pass on v3816) - AN AREA WRITTEN WITH "THE" IS ONE AREA.

The Shelf's "Where you farm" ranked "Rogue Encampment" (22 runs) and "The Rogue Encampment" (6 runs) as two places - the
reader writes an area both ways. _hmAggregate folds a leading "The" off the key and names the row without it; an area
still counts once per run. GrokBot's v3818 pass: "Secret Cow Level" and "Moo Moo Farm" are one place too (the game's name
is Moo Moo Farm), and the line over the list said "24 areas" above 12 rows - a cut list now says it is the top 12.

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
  { areas: ['Theater of Blood'], reads: 1, finds: [] },
  { areas: ['Secret Cow Level'], reads: 3, finds: [] },
  { areas: ['The Secret Cow Level', 'Moo Moo Farm'], reads: 4, finds: [] },
  { areas: ['Moo Moo Farm'], reads: 1, finds: [] }
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


class TheCowLevelIsOnePlaceAndACutListSaysSo(unittest.TestCase):

    def test_secret_cow_level_and_moo_moo_farm_are_one_row(self):
        rows = {a["name"]: a for a in _run()["areas"]}
        self.assertNotIn("Secret Cow Level", rows, "the cow level ranks under two names: %r" % sorted(rows))
        self.assertEqual(rows["Moo Moo Farm"]["runs"], 3, "a run that wrote both names counted twice: %r" % rows)

    def _sub(self, n_areas):
        with open(UI, encoding="utf-8") as fh:
            s = fh.read()
        a, b = "  window._hmOpen = function(){\n", "\n  };\n  window._hmClose = "
        self.assertEqual((s.count(a), s.count(b)), (1, 1), "PREMISE: _hmOpen moved")
        i = s.index(a)
        fn = s[i:s.index(b, i) + 5]
        js = ("var window = {}, OV = { hidden: true, innerHTML: '', scrollTop: 0 };\n"
              "var document = { getElementById: function(){ return OV; } };\n"
              "function esc(x){ return String(x); } function _kpiFmt(x){ return String(x); }\n"
              "function _hmAggregate(){ var a = []; for (var i = 0; i < %d; i++) a.push({ name: 'Area ' + i, runs: 9 - (i %% 9), "
              "reads: 1, grails: 0 }); return { areas: a, totalRuns: 9 }; }\n" % n_areas + fn + "\nwindow._hmOpen();\n"
              "var m = OV.innerHTML.match(/<div class=\"hm-sub\">([^<]*)</); var rows = OV.innerHTML.split('class=\"hm-row\"').length - 1;\n"
              "console.log(JSON.stringify({ sub: m && m[1], rows: rows }));")
        if NODE is None:
            raise AssertionError("node is not on this machine - this gate does not skip")
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise AssertionError("_hmOpen did not run in node: %s" % r.stderr[-800:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_a_cut_list_says_it_is_the_top_twelve(self):
        o = self._sub(24)
        self.assertEqual(o["rows"], 12, "PREMISE: the list is not cut at 12: %r" % o)
        self.assertIn(" · the top 12 of 24 areas · ", o["sub"], "the line counts 24 areas over 12 rows: %r" % o)

    def test_a_whole_list_counts_plainly(self):
        o = self._sub(5)
        self.assertEqual(o["rows"], 5)
        self.assertIn(" · 5 areas · ", o["sub"])
        self.assertNotIn("top", o["sub"])


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
    {"why": "GrokBot v3818 - 'Secret Cow Level' and 'Moo Moo Farm' rank as two places again",
     "file": "tv/control_ui.html",
     "find": "        bare = _HM_SAME[bare.toLowerCase()] || bare;\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "GrokBot v3818 - the line counts every area over a list cut to 12",
     "file": "tv/control_ui.html",
     "find": "      + (agg.areas.length > HM_SHOWN ? 'the top ' + HM_SHOWN + ' of ' : '') + agg.areas.length",
     "replace": "      + agg.areas.length",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
