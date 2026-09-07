# -*- coding: utf-8 -*-
"""v2760 — THE SHELF BUILT 3,086 CARDS TO SHOW 529, AND THAT STOPPED THE WHOLE WINDOW PAINTING.

Konyo, five separate reports in one afternoon: "shelf its not rendering again", "advanced tab is
collapsed open and not rendering anything", "close theatre but nothing to really close lol", "this
middle section within sessions disappeared". FOUR SYMPTOMS, ONE CAUSE.

MEASURED on a private console (never :17772):

    start                 11,744 elements    shelf hidden
    open the shelf     -> 84,414 elements    +72,671 IN ONE BUILD
    re-open x3         -> ~84,4xx            +0        (so it is NOT a leak)
    idle 60s           -> +0
    rail icon x6       -> -99
    river/newest x6    -> +0

    .sh-card built         3,086      <- EVERY run in his history
      VISIBLE                529
      HIDDEN               2,557      <- built, then display:none'd
    elements per card         23
    wasted on hidden     ~58,811      = 70% OF THE WHOLE PAGE, built only to be invisible

The panel's own chip already said it: "529 of 3086 · 2,557 empty runs — hidden". It built all
3,086 and `_shFilter` judged them afterwards.

⚠⚠ WHY IT WENT BLACK. Past roughly 84k elements WebKit stops producing frames, so once the shelf
had been opened ONCE, panels he never touched went dark too. His console diagnosed itself and
nothing surfaced it:
    uiBeat: painting=false, frozenBeats=12, "no frame has been drawn for 12 beat(s), while the
            page keeps beating and its DOM is intact (84470 elements)"
and tv/ui_faults.jsonl carries days of "console-rescued-by-server ... BEATING AND DRAWING NOTHING".
Proven by relaunch: 84,470 -> 11,796 and painting=true, frozenBeats=0.

AFTER THE FIX, measured the same way: 84,414 -> 27,415 on open, 529 cards, and the chip still
reads 2,557.

⚠ MY FIRST TWO READS WERE BOTH WRONG, and the measurement corrected each:
  1. "it appends without clearing" — REFUTED, `ov.innerHTML =` replaces and re-opens add 0.
  2. `_shellPaintAgain` (the rAF timer fallback) — that made a page which COULD NOT paint try
     again. A symptom fix. [[feedback-verify-not-proxy]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()


def _between(src, start, end):
    """Anchored at BOTH ends — never a fixed window. [[source-reading-guard]]"""
    i = src.find(start)
    if i < 0:
        return None
    j = src.find(end, i + len(start))
    return None if j < 0 else src[i:j + len(end)]


class TheShelfBuildsWhatItShows(unittest.TestCase):

    # ── the guard can find its subject ───────────────────────────────────────────────────────
    def test_the_card_builder_is_still_here(self):
        """⚠ A law that cannot find the build site passes having graded nothing."""
        self.assertIn("var cards = (TH.sessions || []).map(function(sm, i){", UI,
                      "the shelf card builder moved — fix this guard before trusting a green")

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_a_withheld_ghost_is_NOT_BUILT(self):
        blk = _between(UI, "var cards = (TH.sessions || []).map(function(sm, i){", "data-stub=")
        self.assertIsNotNone(blk, "could not read the card builder")
        self.assertIn("if (!_shBuildGhosts && sm && sm.stub) return '';", blk,
                      "the builder makes a card for every session again. 2,557 of his 3,086 are "
                      "empty runs the filter immediately hides — 58,811 elements, 70% of the "
                      "page, built only to be invisible, which is what stops the window painting.")

    def test_it_RETURNS_EMPTY_rather_than_filtering_the_array(self):
        """★ THE TRAP. Cards carry data-n="'+n+'" derived from THIS index. `.filter()` would
        renumber every card and silently break the card->session join — a defect nothing on screen
        would reveal. map() keeps positions, so '' costs a string and nothing else."""
        blk = _between(UI, "var _shBuildGhosts", "data-stub=")
        self.assertIsNotNone(blk)
        self.assertNotIn(".filter(function(sm", blk,
                         "the session list is being FILTERED before the map, which renumbers "
                         "data-n on every card")
        self.assertIn("return '';", blk, "the skip no longer returns an empty string")

    # ── ⚠ THE COUNT MUST SURVIVE, OR THE FIX TELLS A WORSE LIE THAN THE SLOWNESS ────────────
    def test_the_ghost_count_comes_from_the_DATA_not_from_hidden_nodes(self):
        """Those cards are ABSENT from the DOM now. Walking `data-stub` nodes would find nothing
        and the chip would read "0 empty runs — hidden" while 2,557 were withheld — a zero with no
        denominator. [[zero-needs-a-denominator]]"""
        blk = _between(UI, "var _stubTotal = 0;", "var _ghostVisible = 0;")
        self.assertIsNotNone(blk, "the data-derived stub count is gone")
        self.assertIn("TH.sessions[_st].stub", blk,
                      "the stub total is not counted off the session data")
        self.assertIn("if (!SHELF_F.ghosts) _ghostN = _stubTotal;", blk,
                      "the chip's number is not taken from the data while the ghosts are unbuilt")

    # ── ⚠ THE CHIP MUST REBUILD, NOT UNHIDE ────────────────────────────────────────────────
    def test_toggling_ghosts_REBUILDS(self):
        """★ Without this the chip goes DEAD while still looking exactly like a chip that works:
        `_shFilter` can only show cards that exist, and these no longer do. [[the-unjoined-end]]"""
        blk = _between(UI, "function _shToggleFilter(f){", "else if (f === 'pin')")
        self.assertIsNotNone(blk, "the filter toggle is gone")
        self.assertIn("thShelf(true)", blk,
                      "toggling the ghosts chip does not rebuild the shelf, so the empty runs can "
                      "never come back — the chip is inert and looks fine")
        self.assertIn("return;", blk,
                      "the ghosts branch falls through to _shFilter as well, so it rebuilds and "
                      "then immediately re-filters the fresh DOM for nothing")

    # ── the arithmetic that makes the ceiling meaningful ────────────────────────────────────
    def test_the_saving_is_stated_as_a_measurement_not_a_hope(self):
        """A ceiling with no denominator is a number nobody can re-derive. 2,557 x 23 = 58,811."""
        self.assertEqual(58811, 2557 * 23,
                         "the stated saving no longer follows from cards x elements-per-card")
        self.assertLess(3086 * 23, 84414 + 1)
        self.assertGreater(84414 - 58811, 25000,
                           "the predicted post-fix page (~25.6k) is not in the range measured "
                           "after the change (27,415) — one of the two numbers is wrong")

    def test_the_symptom_fix_is_not_mistaken_for_the_cause(self):
        """⚠ `_shellPaintAgain` stays — it is harmless and helps a genuinely throttled window —
        but it must never be the only thing standing between him and a black console. If the
        builder skip is gone and only the repaint remains, this says so."""
        self.assertIn("_shellPaintAgain", UI, "the rAF fallback vanished")
        self.assertIn("_shBuildGhosts", UI,
                      "the DOM-weight fix is gone and only the repaint fallback remains — that is "
                      "a page which cannot paint being asked to try again")


if __name__ == "__main__":
    unittest.main(verbosity=2)
