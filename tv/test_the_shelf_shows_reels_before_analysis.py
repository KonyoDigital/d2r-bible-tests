# -*- coding: utf-8 -*-
"""#58 — THE PANEL CALLED "your reels" MUST PUT THE REELS ABOVE THE ANALYSIS.

MEASURED on his live console at his real window size 1120x660, before this fix:

    overlay      811 x 390
    first card   y = 2491   — 2101px BELOW the panel's own bottom edge
    above it     1433px of header, pipeline board, highlights, controls and a 14-day timeline
    scroll       60561px
    cards        530 rendered, 0 visible

The panel named "THE SHELF — your reels" showed no reels. After the reorder the first card sits at
y=738, a 70% cut, with nothing removed and no id moved — the async renderers still find every block
by id. [[the-unjoined-end]] is not the defect here; the order is.

⚠ THE CARD'S OWN HEIGHT IS PART OF THIS. `.shc-river` never rendered until v2963 joined the card to
the river, so its height had never been paid: the card went 332px -> 376px the moment the join
worked, inside a 390px panel. An 80-char `why` wrapping to three lines was most of it, so the reason
moved to the badge's `title` and the card came back to 318px. I added that height; trimming it is
not a taste call on his design.

⚠ STILL TRUE AND NOT FIXED BY THIS: the panel is 390px and a card is 318px, so with the river strip
at 325px above it NO card is fully visible at his window size. That is a structural choice — a
taller home for the shelf, or a shorter card — and it is stated here rather than quietly closed.
[[unknown-stays-unknown]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()

_ASSEMBLY_START = "ov.innerHTML = '<button class=\"sh-x th-x\""


def _assembly(case):
    """The overlay's innerHTML expression, by anchors at both ends — never a fixed window."""
    i = UI.find(_ASSEMBLY_START)
    case.assertGreater(i, 0, "the shelf overlay assembly is gone — this law lost its target")
    j = UI.find(";\n", i)
    case.assertGreater(j, i, "could not find the end of the assembly expression")
    return UI[i:j]


class TheReelsComeFirst(unittest.TestCase):

    def setUp(self):
        self.asm = _assembly(self)

    def test_the_grid_is_assembled_before_every_analytic_block(self):
        """`body` is the card grid. Anything analytic that precedes it is chrome the reader must
        scroll past to reach the thing the panel is named after."""
        grid = self.asm.find("+ body")
        self.assertGreater(grid, 0,
                           "the card grid (`body`) is no longer in the overlay assembly at all")
        # ⚠⚠ v2985 (#58) — THE RIVER STRIP JOINS THIS LIST. It was deliberately absent before, and
        # correctly so: v2965 defined "everything analytic" as exactly the three blocks below and
        # placed the strip ABOVE the list as "the organisation he asked for". That was one half of
        # his sentence; the other half was "those reels coming in should be SEEN", and measured at
        # his real 1120x660 the strip's ~337px helped put every card off-screen — the panel named
        # "your reels" showed none. So the strip moved below too, and this law now pins it there;
        # without the entry, a future edit could restore the old order and silently undo #58 while
        # this gate stayed green. [[label-outlived-referent]]
        for name, token in (("the pipeline board", 'id="sh-story"'),
                            ("the highlights strip", "_shHighlights()"),
                            ("the 14-day timeline", "timelineDiv"),
                            ("the river strip", 'id="sh-lanes"')):
            at = self.asm.find(token)
            self.assertGreater(at, 0, "%s is gone from the assembly (%r)" % (name, token))
            self.assertGreater(at, grid,
                               "%s is assembled BEFORE the reels. Measured at his window size, "
                               "1433px of blocks like this put the first card 2101px below the "
                               "panel's bottom edge and showed 0 of 530 cards." % name)

    def test_the_controls_still_precede_the_list_they_filter(self):
        """A filter bar below the list it filters is a different defect, not a fix."""
        self.assertLess(self.asm.find("searchBar"), self.asm.find("+ body"),
                        "the search/filter controls now come AFTER the grid they act on")

    def test_nothing_was_dropped_to_buy_the_space(self):
        """[[sweep-dont-ask]] — reordering is safe; deleting a block to win pixels is not."""
        for token in ('id="sh-lanes"', 'id="sh-story"', "_shHighlights()", "timelineDiv",
                      "searchBar", 'id="sh-live"'):
            self.assertIn(token, self.asm,
                          "%r was REMOVED from the shelf rather than reordered — the fix was "
                          "meant to cost nothing" % token)


class TheRiverBadgeIsOneLine(unittest.TestCase):

    def setUp(self):
        i = UI.find("b.className = 'shc-river';")
        self.assertGreater(i, 0, "the river badge is gone — this law lost its target")
        j = UI.find("c.appendChild(b);", i)
        self.assertGreater(j, i, "could not find the end of the badge build")
        self.region = UI[i:j]

    def test_the_reason_is_a_tooltip_not_three_wrapped_lines(self):
        self.assertIn("b.title", self.region,
                      "the badge no longer carries its `why` as a title, so either the reason is "
                      "lost or it is back to wrapping across the card")
        n = self.region.count("shcr-why")
        self.assertEqual(0, n,
                         "the badge inlines the `why` again in %d place(s) — an 80-char reason "
                         "wraps to three lines and took the card from 332px to 376px inside a "
                         "390px panel" % n)

    def test_the_station_and_the_age_are_still_on_the_card(self):
        """Trimming must not cost the two facts that are readable at a glance."""
        for token in ("shcr-st", "shcr-at"):
            self.assertIn(token, self.region,
                          "the badge lost %r — the station and its age are the reason the badge "
                          "exists at all" % token)


RED_PROOF = [
    {
        "why": "putting the grid back at the end of the assembly restores the measured defect: "
               "1433px of analysis above the reels and 0 of 530 cards on screen",
        "file": "control_ui.html",
        "find": "      + searchBar + body\n",
        "replace": "      + searchBar\n",
        "matches": 1,
    },
    {
        "why": "putting the river strip back ABOVE the list is the v2965 order that helped push "
               "every card off his 660px screen — the clause added in v2985 must turn red on it",
        "file": "control_ui.html",
        "find": "      + searchBar + body\n      /* \u26a0\u26a0 v2985 (#58)",
        "replace": "      + '<div class=\"sh-lanes\" id=\"sh-lanes\"></div>'\n      + searchBar + body\n      /* \u26a0\u26a0 v2985 (#58)",
        "matches": 1,
    },
    {
        "why": "inlining the reason again re-wraps it across three lines and takes the card back "
               "over the panel's own height",
        "file": "control_ui.html",
        "find": "        if (r.why) b.title = String(r.why);\n",
        "replace": "",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
