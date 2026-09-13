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

    def test_the_lane_header_counts_cards_so_it_must_not_say_reels(self):
        """PARSED out of the lane-header builder, comments stripped. [[source-reading-guard]]"""
        blk = _between(UI, "_lh.className = 'sh-daygroup sh-riverlane'", "grid.insertBefore(_lh")
        self.assertIsNotNone(blk, "the lane-header builder could not be located")
        code = re.sub(r"/\*.*?\*/", "", blk, flags=re.S)
        # it must still be counting CARDS — that is what makes the noun matter
        # ⚠ the index is NESTED (`byStation[_lst[_lk]]`), so a [^\]]+ class cannot reach past
        # the inner bracket — it matched 0 and looked like the header had stopped counting
        # cards. The instrument, not the code. [[feedback-suspect-the-instrument]]
        counts_cards = re.findall(r"_lc\s*\+=\s*\(\(byStation\[.+?\]\s*\|\|\s*\[\]\)\.length\)", code)
        print("card-counting expressions in the lane header: %d" % len(counts_cards))
        self.assertEqual(1, len(counts_cards),
                         "this law is about a CARD count wearing the wrong noun; if the header "
                         "stopped counting cards, re-derive the law rather than deleting it")
        said_reel = re.findall(r"'\s*reel'", code)
        said_run = re.findall(r"'\s*run'", code)
        print("noun printed -> reel: %d · run: %d" % (len(said_reel), len(said_run)))
        self.assertEqual(0, len(said_reel),
                         "the lane header counts CARDS; calling them reels puts two populations "
                         "under one word on a screen that also prints a real reel count")
        self.assertEqual(1, len(said_run), "it must name what it counted")

    def test_the_shelf_uses_run_for_a_card_everywhere_it_already_speaks(self):
        """The noun is not invented here — the shelf already calls a card a RUN."""
        code = re.sub(r"/\*.*?\*/", "", UI, flags=re.S)
        empties = re.findall(r"empty runs", code)
        searchbar = re.findall(r"Search runs", code)
        print("existing 'run' vocabulary on the shelf -> 'empty runs': %d · 'Search runs': %d"
              % (len(empties), len(searchbar)))
        self.assertGreaterEqual(len(empties) + len(searchbar), 2,
                                "RUN must already be this shelf's word for a card, or the rename "
                                "introduces a THIRD vocabulary instead of removing a second")

    def test_the_river_strips_own_reel_count_is_untouched(self):
        """The strip is correct. A fix here must not spread into it."""
        code = re.sub(r"/\*.*?\*/", "", UI, flags=re.S)
        hits = re.findall(r"</b>\s*reel\(s\) on the shelf", code)
        print("river strip reel(s)-on-the-shelf phrases: %d" % len(hits))
        self.assertEqual(1, len(hits),
                         "the strip counts REELS from /api/river and says so; that phrase must "
                         "survive, or a correct surface was collateral damage")

    def test_the_count_carries_a_title_saying_which_population(self):
        blk = _between(UI, "_lh.className = 'sh-daygroup sh-riverlane'", "grid.insertBefore(_lh")
        code = re.sub(r"/\*.*?\*/", "", blk or "", flags=re.S)
        has = re.findall(r'class="shg-n"\s*\+?\s*title=|class="shg-n"\s+title=', code)
        print("lane count carries an explaining title: %d" % len(has))
        self.assertEqual(1, len(has),
                         "the number must say, on hover, which population it counted and that "
                         "the strip above counts a different one")


RED_PROOF = [
    {
        "why": "the lane header goes back to calling its CARD count 'reels', putting two "
               "populations under one word on a screen that also prints a real reel count",
        "file": "control_ui.html",
        "find": "                + _lc + ' run' + (_lc === 1 ? '' : 's') + '</span>'",
        "replace": "                + _lc + ' reel' + (_lc === 1 ? '' : 's') + '</span>'",
        "matches": 1,
    },
    {
        "why": "the number stops saying which population it counted, so a reader has nothing to "
               "tell it from the reel figure four inches above it",
        "file": "control_ui.html",
        "find": '                + \'<span class="shg-n" title="runs on the shelf stationed in this lane — the \'\n'
                '                + \'river strip above counts REELS, which is a different population">\'',
        "replace": '                + \'<span class="shg-n">\'',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
