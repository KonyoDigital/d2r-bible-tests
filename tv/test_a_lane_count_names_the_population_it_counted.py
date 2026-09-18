# -*- coding: utf-8 -*-
"""A LANE COUNT MUST NAME THE POPULATION IT ACTUALLY COUNTED.

Konyo, 2026-09-13: *"i want it reading real.. and synced to the related sessions ... the anayltics
and diagnostics should be relevant and real and accurate!"*

MEASURED on his console, the same lane in the same overlay, the same second:

    shelf lane header   INTAKE  8 REELS     <- 8 CARDS   (byStation built from `vis`, :16271)
    river strip         1 INTAKE  4         <- 4 REELS   (/api/river lanes[].byStation)
    whole shelf         425 cards                16 reels on the shelf

Two populations differing by 26x, one word covering both, four inches apart on one screen.

⚠ THE NUMBER WAS NEVER WRONG. 8 is the correct count of cards stationed in that lane. Only the
NOUN was wrong — the same shape as `stash ×19` counting frames of a scene and `frames` counting
journal rows in a group. This file guards the noun. [[label-outlived-referent]]

@@RULING: THE RIVER STRIP IS NOT THE DEFECT - do not "fix" its arithmetic. Its lanes sum to its
own headline and that was verified. When surfaces disagree about a count, the number was never
wrong - only the NOUN was. Guard the noun; leave the strip alone.

⚠ AND THE STRIP IS NOT THE DEFECT — DO NOT "FIX" IT. Its arithmetic is internally consistent and
was verified: lane sum 16 == L.shelf 16, and 16 + 446 closed = 462 lifetimes. v2822 (#36) already
solved the denominator problem for that header after one of its figures covered 8.7% of the river.
A second attempt there would undo work that is correct. [[verify-before-building-console]]
"""
import io
import os
import re
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()


def _between(src, start, end):
    i = src.find(start)
    if i < 0:
        return None
    j = src.find(end, i + len(start))
    return src[i:j] if j > i else None


class TestALaneCountNamesThePopulationItCounted(unittest.TestCase):

    # ⚠⚠ v3191 — RE-DERIVED, NOT DELETED, AND THE OLD BODY SAID TO DO EXACTLY THAT: "if the
    # header stopped counting cards, re-derive the law rather than deleting it". His one-river
    # ruling (#97) removed the per-lane sections, so `sh-riverlane` headers and their `_lc`
    # counter no longer exist — but the DEFECT is untouched. There is now ONE river header and it
    # still counts CARDS, while the river STRIP a few pixels above still counts REELS off the
    # router. Two populations, and only one of them can own the word.

    def test_the_river_header_counts_cards_so_it_must_not_say_reels(self):
        """PARSED out of the river header builder, comments stripped. [[source-reading-guard]]"""
        blk = _between(UI, "var mkHead = function(lab, n, before, cls){", "grid.insertBefore(h, before);")
        self.assertIsNotNone(blk, "the river header builder could not be located — fix this "
                                  "anchor before believing anything below it")
        code = re.sub(r"/\*.*?\*/", "", blk, flags=re.S)
        said_reel = re.findall(r"'[^']*\breels?\b[^']*'", code)
        print("river-header strings saying reel: %r" % (said_reel,))
        self.assertEqual([], said_reel,
                         "the header counts CARDS on the shelf and called them reels — the strip "
                         "above counts reels off the router and the two are different numbers")
        self.assertIn("' run'", code, "the header no longer names what it counts at all")

    def test_the_count_carries_a_title_saying_which_population(self):
        """A number that cannot say what it counted is a number he has to guess about — and the
        guess is available right above it, in a strip counting something else."""
        blk = _between(UI, "var mkHead = function(lab, n, before, cls){", "grid.insertBefore(h, before);")
        self.assertIsNotNone(blk, "the river header builder could not be located")
        code = re.sub(r"/\*.*?\*/", "", blk, flags=re.S)
        has_title = 'class="shg-n" title=' in code
        print("the count carries a title: %s" % has_title)
        self.assertTrue(has_title,
                        "the number must say, on hover, which population it counted and that the "
                        "strip above counts a different one")
        self.assertIn("REELS", code,
                      "the title does not name the OTHER population, so it explains nothing")



RED_PROOF = [
    {
        "why": 'the law requires the river header to NAME what it counts; deleting the noun must '
               'turn the gate red',
        "file": 'control_ui.html',
        "find": "+ n + ' run' + (n === 1 ? '' : 's') + '</span>';",
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": 'the law requires the count to say on hover WHICH population it counted, because '
               'the river strip directly above counts a different one',
        "file": 'control_ui.html',
        "find": 'REELS off the router, which is a different population',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
