# -*- coding: utf-8 -*-
"""THE CARDS COME FIRST, AND ACTIVITY LEADS THE ANALYTIC BAND BEHIND THEM.

⚠⚠ TWO OF HIS ASKS PULL IN OPPOSITE DIRECTIONS AND ONE OF THEM IS A MEASURED SCAR.

Konyo, 2026-09-14, on the runs-per-day chart: *"for the ACTIVITY section i like i just want it
stretched from top to bottom more so its more representing chart and uptop organized with the other
data/anlytics TOP of the SHELF section move and stretched a little bit so its more seen the
difference bettween 1 run and 10 runs"*.

Read literally that is "put it above the list", and v2985 already MEASURED what that costs on his
real screen at 1120x660: the overlay is trapped inside `.stage` — a grid row worth ~449px of a 660px
window — and **549px of furniture above the first card put every reel off-screen**. The panel named
"your reels" was showing none of them, and Grok Bot photographed it three times and called it blank.
"BLANK" and "below-fold" were one defect.

So this law holds both halves at once and refuses to let either quietly win:

    THE LIST comes before every analytic block                  <- v2985's scar, never re-broken
    ACTIVITY leads the analytic band, not trails it             <- his 2026-09-14 ask

⚠ IT READS THE ASSEMBLY, NOT A CLASS NAME. The shelf is built as one flat string concatenation, so
the order of those pieces IS the DOM order. This law extracts that statement between two anchors,
asserts each marker occurs exactly ONCE inside it — a marker that matched twice would make any
index comparison meaningless — and PRINTS the order it found. [[source-reading-guard]]
[[zero-needs-a-denominator]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

UI = os.path.join(HERE, "control_ui.html")

#: marker -> what it is on his screen. Order here is the order that must hold.
BAND = [
    ("+ searchBar + body",            "the reel cards"),
    ("+ timelineDiv",                 "ACTIVITY (runs per day)"),
    ('id="sh-lanes"',                 "the river strip"),
    ('id="sh-story"',                 "the pipeline"),
    ("_shHighlights()",               "the highlights"),
]


def _between(src, start, end):
    """Text between two anchors, BOTH required. A fixed-size window reads a moved region as
    ABSENT, which is how this repo has lost measurements before. [[source-window-shortcut]]"""
    i = src.index(start)
    j = src.index(end, i + len(start))
    return src[i:j + len(end)]


def _assembly():
    src = io.open(UI, encoding="utf-8").read()
    return _between(src, "ov.innerHTML = '<button class=\"sh-x th-x\"", "+ _shHighlights();")


class TestTheShelfShowsReelsBeforeItShowsCharts(unittest.TestCase):

    def setUp(self):
        self.asm = _assembly()

    def test_every_marker_is_unique_inside_the_assembly(self):
        """⚠ A COUNT BEFORE A COMPARISON. Two matches and `index()` silently reads the first one,
        so the order this law reports would be about a piece it was not asked about."""
        for marker, what in BAND:
            n = self.asm.count(marker)
            print("   %-24s x%d   (%s)" % (marker, n, what))
            self.assertEqual(n, 1,
                             "%r occurs %d time(s) in the shelf assembly — an index comparison "
                             "over it means nothing" % (marker, n))

    def test_the_cards_come_before_every_analytic_block(self):
        """⚠⚠ v2985's SCAR, PINNED SO IT CANNOT BE RE-BROKEN BY THE NEXT LAYOUT ASK. 549px of
        furniture above the first card is how the panel named 'your reels' came to show none."""
        cards = self.asm.index("+ searchBar + body")
        for marker, what in BAND[1:]:
            at = self.asm.index(marker)
            self.assertLess(cards, at,
                            "%s is assembled BEFORE the reel cards — that is the 549px of "
                            "furniture that put every reel off-screen at his real 1120x660"
                            % what)

    def test_activity_leads_the_analytic_band(self):
        """His 2026-09-14 ask, and the highest the chart may sit without re-breaking the scar
        above."""
        order = [(self.asm.index(m), what) for m, what in BAND]
        order.sort()
        print("   order: %s" % " -> ".join(w for _, w in order))
        self.assertEqual([w for _, w in order], [w for _, w in BAND],
                         "the shelf assembles in a different order than this law describes")
        act = self.asm.index("+ timelineDiv")
        for marker, what in BAND[2:]:
            self.assertLess(act, self.asm.index(marker),
                            "ACTIVITY is assembled after %s — he asked for it up with the other "
                            "data and analytics, not trailing them" % what)


RED_PROOF = [
    {
        "why": "ACTIVITY drops back to the END of the analytic band, behind the river, the "
               "pipeline and the highlights — the position he looked at and asked to change, "
               "where a 14-day chart sits under ~1400px of other furniture",
        "file": "control_ui.html",
        "find": "      + timelineDiv\n",
        "replace": "      ",
        "matches": 1,
    },
    {
        "why": "the reel cards are assembled AFTER the analytic band, which is the exact v2985 "
               "defect: 549px of furniture above the first card at his real 1120x660, and the "
               "panel named 'your reels' shows none of them",
        "file": "control_ui.html",
        "find": "      + searchBar + body\n",
        "replace": "      ",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
