# -*- coding: utf-8 -*-
"""v3289 — THE RECORDS STRIP LEADS THE SHELF, AND THE SHELF STILL OPENS ON A REEL.

Konyo, 2026-09-18: *"the row where it says BEST RUN MOST READS TOP READS BEST COVERAGE AND STREAK
i want at the tippy top of the SHELF TAB above the sessions reels"*, then *"and the activity i
want uptop under the BEST RUNS row"*.

⚠⚠ **THIS REOPENS A MEASURED SCAR ON PURPOSE, AND THE SECOND HALF OF THIS FILE IS THE PRICE.**
v2965 measured furniture above the list at his real 1120x660: the first card at y=2491, 2101px
below the panel's own bottom edge, behind **1433px** of header, board, highlights, controls and
timeline — 530 cards rendered and not one on screen. v3121 refused the same request for the chart
for the same reason. He has now asked twice and more specifically, so it is granted — but only
with the guard that keeps the half he did not say out loud: *"those reels coming in should be
SEEN"*.

MEASURED BEFORE AND AFTER, on his live console at 1120x660:

    order alone      scrollTop 0    firstCardTop 815   firstCardVisible FALSE
    order + guard    scrollTop 476  firstCardTop 235   firstCardVisible TRUE   (clientH 390)

**The guard is a timing fix, and the bug it fixes was already there.** v3029 chose the opening
scroll BEFORE `_shTimeline()` runs, and `#sh-timeline` ships with the `hidden` attribute — so at
decision time it contributes 0px and then becomes 156px, shifting everything below it after the
scroll was chosen. That went unnoticed while the timeline sat BELOW the list, where its height
could not move the cards. Putting it above turned a latent miscalculation into a shelf that opens
on furniture. [[stale-reading]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

from frame_authority import _executable_only  # noqa: E402

UI = os.path.join(ROOT, "tv", "control_ui.html")


class TestTheShelfOpensOnAReel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = _executable_only(io.open(UI, encoding="utf-8").read(), ".js")

    def test_the_records_strip_and_the_chart_lead_the_list(self):
        """His ask, as an ORDER fact rather than a string that merely appears somewhere."""
        hi = self.code.find("+ _shHighlights()")
        tl = self.code.find("+ timelineDiv")
        lst = self.code.find("+ searchBar + body")
        for name, idx in (("_shHighlights()", hi), ("timelineDiv", tl), ("searchBar + body", lst)):
            self.assertGreater(idx, -1, "%s vanished from the shelf builder" % name)
        self.assertLess(hi, lst,
                        "the BEST RUN / STREAK strip must come BEFORE the list - he asked for it "
                        "at the tippy top of the shelf")
        self.assertLess(tl, lst, "ACTIVITY must come before the list")
        self.assertLess(hi, tl, "he asked for ACTIVITY UNDER the BEST RUNS row, not above it")

    def test_the_opening_scroll_is_decided_AFTER_the_blocks_above_the_list_are_real(self):
        """The guard that pays for the order change.

        Ordering is the whole assertion: a call placed before `_shTimeline()` measures a layout
        that is about to grow by the timeline's height, which is exactly the bug v3029 shipped
        with and nobody could see while the timeline sat below the cards.
        """
        self.assertIn("window._shOpenOnAReel = function (ov)", self.code,
                      "the opening-scroll logic is not a named function, so it cannot be run "
                      "again once the layout is settled")
        tline = self.code.find("_shTimeline();")
        self.assertGreater(tline, -1, "_shTimeline() call vanished")
        after = self.code.find("window._shOpenOnAReel(ov)", tline)
        self.assertGreater(after, -1,
                           "nothing re-decides the opening scroll after _shTimeline() fills the "
                           "chart, so the shelf opens on furniture: MEASURED firstCardVisible "
                           "false, scrollTop 0 at his real 1120x660")

    def test_it_still_only_scrolls_when_the_card_is_below_the_fold(self):
        """A shelf whose first card is already visible must be left alone - scrolling a healthy
        panel away from its own head is the failure the original guard was careful about."""
        i = self.code.find("window._shOpenOnAReel = function (ov)")
        j = self.code.find("};", self.code.find("} catch (e) {}", i))
        body = self.code[i:j if j > i else i + 1400]
        self.assertIn("_top >= _ovH", body,
                      "the below-the-fold condition is gone, so it would scroll a shelf whose "
                      "card is already on screen")
        self.assertIn("_ovH > 0", body,
                      "an unlaid-out overlay reads all-zero and would compute a confident scroll "
                      "of 0 - the guard against measuring before layout must stay")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "putting the strip back below the list un-does what he asked for twice",
        "file": "tv/control_ui.html",
        "find": "      + _shHighlights()\n      + timelineDiv\n      + searchBar + body",
        "replace": "      + searchBar + body\n      + timelineDiv\n      + _shHighlights()",
        "matches": 1,
    },
    {
        "why": "dropping the second call restores the shelf that opens on furniture",
        "file": "tv/control_ui.html",
        "find": "    try { window._shOpenOnAReel(ov); } catch (e) {}",
        "replace": "    try { void 0; } catch (e) {}",
        "matches": 1,
    },
    {
        "why": "removing the below-the-fold test scrolls a healthy shelf away from its own head",
        "file": "tv/control_ui.html",
        "find": "        if (_ovH > 0 && _top >= _ovH){",
        "replace": "        if (true){",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
