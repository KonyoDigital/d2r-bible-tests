# -*- coding: utf-8 -*-
"""#278 (REG-2050) - A BOSS CARD'S "SHOW ALL" SUMMARY COUNTS THE TABLE IT OPENS, AGAINST THE WHOLE.

The #231 second eye read the May commit e45c1d36 (v43); re-measured at HEAD 2026-10-08: the boss card's <summary> said
"Show all ${dropTable.length} droppable items" where dropTable is _bossFilteredDrops(boss) - the FILTERED copy. Mephisto
under the grail filter read "Show all 32 droppable items" while the pill beside it counts boss.dropTable.length (267).
"All" was a claim the number under it did not make.

  * no filter took rows out -> "Show all N droppable items" (N = the whole table);
  * a filter took rows out  -> "Show n of N droppable items".
Drives the SHIPPED _allDropsSummaryLabel, cut from bible.html and run in node. A missing node raises; this law does not
skip.
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

PAGE = os.path.join(os.path.dirname(HERE), "bible.html")
START = "function _allDropsSummaryLabel(shown, total){\n"
CALL = "${_allDropsSummaryLabel(dropTable.length, boss.dropTable.length)}"


def _src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


def _fn_src(s):
    if s.count(START) != 1:
        raise AssertionError("_allDropsSummaryLabel's anchor matched %d times - re-point this law" % s.count(START))
    i = s.index(START)
    return s[i:s.index("\n}\n", i) + 3]


def _label(shown, total):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    js = "%s\nconsole.log(JSON.stringify(_allDropsSummaryLabel(%d, %d)));\n" % (_fn_src(_src()), shown, total)
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut function did not run in node: %s" % r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class ASummaryCountsTheTableItOpens(unittest.TestCase):

    def test_a_filtered_table_says_n_of_the_whole(self):
        self.assertEqual(_label(32, 267), "Show 32 of 267 droppable items",
                         "a filtered table still says 'Show all' over its filtered count")

    def test_an_unfiltered_table_says_all_of_the_whole(self):
        self.assertEqual(_label(267, 267), "Show all 267 droppable items")

    def test_the_card_hands_it_the_filtered_count_and_the_whole(self):
        s = _src()
        self.assertEqual(s.count(CALL), 1, "the boss card summary does not ask the label with (shown, whole)")
        self.assertEqual(s.count("Show all ${dropTable.length} droppable items"), 0,
                         "the summary prints the filtered count under the word 'all' again")


RED_PROOF = [
    {"why": "REG-2050 - a filtered table says 'Show all' over its filtered count again",
     "file": "bible.html",
     "find": "  return shown < total ? ('Show ' + shown + ' of ' + total + ' droppable items') : ",
     "replace": "  return false ? ('Show ' + shown + ' of ' + total + ' droppable items') : ",
     "matches": 1},
    {"why": "REG-2050 - the card hands the label its filtered count as the whole",
     "file": "bible.html",
     "find": "${_allDropsSummaryLabel(dropTable.length, boss.dropTable.length)}",
     "replace": "${_allDropsSummaryLabel(dropTable.length, dropTable.length)}",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
