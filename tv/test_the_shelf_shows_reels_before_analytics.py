# -*- coding: utf-8 -*-
"""THE PANEL NAMED AFTER ITS REELS MUST REACH A REEL BEFORE IT REACHES ITS ANALYTICS.

This regression has landed TWICE, both times measured on his own console, and nothing in the repo
prevents a third.

    v2965  put the analytic blocks ABOVE the list. MEASURED at his real 1120x660: the overlay is
           811x390 and the first card sat at y=2491 — 2101px BELOW the panel's own bottom edge —
           behind 1433px of header, pipeline board, highlights, controls and a 14-day timeline,
           inside a 60561px scroll. 530 cards rendered and NOT ONE was on screen.
    v2985  reversed it. MEASURED: 549px of furniture above the first reel card inside a ~449px
           stage, so the cards were entirely off-screen. "The half of his sentence that v2965
           served was 'organized'; the half it broke was 'should be SEEN'."

⚠⚠ AND THE PULL TO REDO IT IS CONSTANT, because he asks for analytics at the top in his own words —
"at the top of the SHELF section along with the other diagnosics and search bar". Both halves of
that are real. What this law pins is only the part that was MEASURED to break: the HEAVY analytic
blocks — the river strip, the pipeline board, the highlights, the timeline — render AFTER the grid.
A compact summary row beside the search bar is not what broke it and is not forbidden here.

⚠ THE RENDER GATE REPORTS BUT DOES NOT REFUSE. `shelf-cards` prints "BELOW-FOLD at load: y=…" as an
ⓘ note, and an ⓘ is not a failure — which is why both regressions shipped. A number nobody can fail
on is documentation, not a guard. [[regression-guard]]
"""
import io
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))

#: the blocks v2965 put above the list and v2985 pushed back down, by their ids
HEAVY = ("sh-lanes", "sh-story")


class TestTheShelfShowsReelsBeforeAnalytics(unittest.TestCase):

    def setUp(self):
        with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
            self.src = fh.read()
        i = self.src.find("ov.innerHTML = '<button class=\"sh-x th-x\"")
        self.assertGreater(i, 0, "could not find the shelf overlay assembly — re-point this guard")
        j = self.src.find("ov.hidden = false;", i)
        self.assertGreater(j, i, "could not find the end of the shelf overlay assembly")
        self.asm = self.src[i:j]

    def test_the_grid_is_assembled_before_every_heavy_analytic_block(self):
        body_at = self.asm.find("+ searchBar + body")
        self.assertGreater(body_at, 0,
                           "the card list is no longer assembled as `searchBar + body` — if that "
                           "moved, this guard must be re-pointed rather than deleted")
        print("card list assembled at offset %d" % body_at)
        for block in HEAVY:
            at = self.asm.find(block)
            self.assertGreater(at, 0, "%s is not in the overlay at all" % block)
            print("   %-10s at %d  %s" % (block, at, "AFTER the list" if at > body_at else "BEFORE"))
            self.assertGreater(
                at, body_at,
                "%s is assembled BEFORE the card list. That is exactly v2965, which put 549px of "
                "furniture above the first reel inside a ~449px stage and showed 530 cards with "
                "NOT ONE on screen. v2985 reversed it on his measurement." % block)

    def test_the_timeline_and_highlights_come_last(self):
        body_at = self.asm.find("+ searchBar + body")
        for tail in ("_shHighlights()", "timelineDiv"):
            at = self.asm.find(tail)
            self.assertGreater(at, 0, "%s left the overlay" % tail)
            self.assertGreater(at, body_at,
                               "%s is assembled before the card list — it is analytic, it is tall, "
                               "and it is the toll v2985 removed" % tail)
        print("highlights + timeline both after the list")

    def test_nothing_analytic_hides_between_the_title_and_the_list(self):
        """Only the title and the live card may precede the list."""
        # ⚠ STRIP THE COMMENTS FIRST. This region carries the long v2965/v2985 rulings, which
        # NAME these blocks in prose — so the first cut failed on documentation explaining why the
        # blocks are where they are. Comments are read when judging a MEASUREMENT and ignored when
        # judging CODE. [[measured-true-read-wrong]]
        import re as _re
        raw = self.asm[:self.asm.find("+ searchBar + body")]
        head = _re.sub(r"/\*.*?\*/", " ", raw, flags=_re.S)
        head = "\n".join(ln for ln in head.splitlines() if not ln.strip().startswith("//"))
        for banned in HEAVY + ("_shHighlights", "timelineDiv"):
            self.assertNotIn(banned, head,
                             "%s appears in the head region, above the reels" % banned)
        # the live card is allowed: it is one row, and it is the run he is recording NOW
        self.assertIn("sh-live", head,
                      "the live 'recording now' card left the head — if that was deliberate, "
                      "re-point this law; it is allowed there precisely because it is not analytic")
        print("head carries only: title + live card")


RED_PROOF = [
    {
        "why": "the river strip is assembled above the reel list again — v2965 exactly, which "
               "measured 549px of furniture above the first card in a ~449px stage and showed 530 "
               "cards with not one of them on screen",
        "file": "control_ui.html",
        "find": "      + searchBar + body\n",
        "replace": "      + '<div class=\"sh-lanes\" id=\"sh-lanes\"></div>'\n      + searchBar + body\n",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
