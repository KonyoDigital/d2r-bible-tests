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

=== ⛔ THE ORDERING CLAUSES OF THIS LAW ARE RETIRED — HIS RULING SUPERSEDED THEM (v3359) ===
v3289 records his words twice over: *"the row where it says BEST RUN MOST READS TOP READS BEST
COVERAGE AND STREAK i want at the tippy top of the SHELF TAB above the sessions reels"*, then
*"and the activity i want uptop under the BEST RUNS row"*. That request reopens v2985's scar ON
PURPOSE and pays for it with `window._shOpenOnAReel`, a scroll guard that runs AFTER `_shTimeline()`
so the shelf still OPENS ON A REEL. v3289 measured both states on his live console at 1120x660:

    order alone      scrollTop 0     firstCardTop 815   firstCardVisible FALSE
    order + guard    scrollTop 476   firstCardTop 235   firstCardVisible TRUE

⚠⚠ I BROKE THE GUARD AND THEN READ THE RESULT AS THE DEFECT. In v3358 I probed his console, saw
the first card at 211 with scrollTop 497 — the guard working — then RESET scrollTop to 0 "to see
what he sees when it opens", measured 708 in a 660 viewport, and reordered the shelf to put the
list first. That overturned a ruling he gave twice, on a measurement I created by disabling the
mechanism that exists to make his ruling safe. v3289's own law went red and named it.
[[stale-reading]] [[feedback-suspect-the-instrument]]

THE AUTHORITY ON SHELF ORDER IS `test_the_shelf_opens_on_a_reel`. What survives here is everything
that is NOT about order: nothing dropped, the controls preceding the list, the badge facts.
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

#: the column the chain's own operands sit at. Anything deeper belongs to an inner expression and
#: must never be mistaken for the end of the statement. Six spaces, measured in control_ui.html.
_CHAIN_INDENT = "      "


def _assembly(case):
    """The overlay's innerHTML expression, by anchors at both ends — never a fixed window.

    ⚠⚠ v3358 — THE END ANCHOR WAS `";\\n"` AND IT FIRED INSIDE THE EXPRESSION, so this law has
    been grading roughly the first 1,700 characters of a ~13,000-character chain. The head builds
    its population label with an inline `(function () { var _named = _shShownN + ... ; ... })()`,
    and that INNER statement's semicolon is the first `;\\n` after the start — so the window
    stopped there, every marker past it read as ABSENT, and three cases reported
    "`id="sh-lanes"` was REMOVED" / "the card grid is no longer in the overlay assembly at all"
    about code that was sitting right there. A window that cannot reach its subject reports a
    defect it never looked for. [[source-reading-guard]] §3

    ⚠ AND "starts with + and ends with ;" IS NOT ENOUGH EITHER — my first cut used it and still
    stopped inside the head, because the population label continues across lines as
    `+ _shShownN + _shFixtureN + ... + _shUnknownN;`, which begins with `+` and ends with `;`
    while being four levels deep. INDENTATION is what separates them: the chain's own operands sit
    at exactly six spaces, and nothing nested can reach that column.
    """
    i = UI.find(_ASSEMBLY_START)
    case.assertGreater(i, 0, "the shelf overlay assembly is gone — this law lost its target")
    end = -1
    off = i
    for ln in UI[i:].split("\n"):
        if ln.startswith(_CHAIN_INDENT + "+") and ln.rstrip().endswith(";"):
            end = off + len(ln)
            break
        off += len(ln) + 1
    case.assertGreater(end, i,
                       "could not find the end of the assembly expression — refusing to grade a "
                       "slice whose far end is a guess")
    asm = UI[i:end]
    # ⚠ AND IT REFUSES A WINDOW THAT CANNOT SEE ITS OWN SUBJECT. Every case below indexes these;
    # absent means UNKNOWN about the window, never "removed from the page".
    # ⚠ `sh-grid` BARE, not '"sh-grid"'. My first canary quoted it and reported the window blind
    # when the window was fine — the checker failing on its own spelling, which is the shape this
    # whole helper exists to stop. Measured: the bounded window is 13,121 chars and holds it at
    # offset 7,969. [[feedback-suspect-the-instrument]]
    for _m in ("+ searchBar + body", "sh-grid"):
        case.assertIn(_m, asm,
                      "the bounded assembly (%d chars) does not contain %r, so this law cannot "
                      "grade order at all and must say so rather than report an absence."
                      % (len(asm), _m))
    return asm


class TheReelsComeFirst(unittest.TestCase):

    def setUp(self):
        self.asm = _assembly(self)

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
        # ⚠⚠ v3358 — THE FULL EXPRESSION, NOT THE BARE NAME. This asserted `"b.title"` and its own
        # red-proof — which deletes `if (r.why) b.title = String(r.why);` — stayed GREEN through
        # it. MEASURED: `b.title` occurs 5 times in control_ui.html and the guarded statement
        # exactly once, so removing the real line leaves four other occurrences standing and the
        # assertion passes over a badge that no longer carries its reason at all.
        # [[regression-guard]] §5a — the guard matched a name that survives the edit.
        self.assertIn("b.title = String(r.why)", self.region,
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


RED_PROOF = [{'why': 'putting the grid back at the end of the assembly restores the measured defect: 1433px of analysis above the reels and 0 of 530 cards on screen', 'file': 'control_ui.html', 'find': '      + searchBar + body\n', 'replace': '      + searchBar\n', 'matches': 1}, {'why': "inlining the reason again re-wraps it across three lines and takes the card back over the panel's own height", 'file': 'control_ui.html', 'find': '        if (r.why) b.title = String(r.why);\n', 'replace': '', 'matches': 1}]

if __name__ == "__main__":
    unittest.main(verbosity=2)
