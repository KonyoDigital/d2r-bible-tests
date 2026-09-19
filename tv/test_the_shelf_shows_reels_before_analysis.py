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


RED_PROOF = [{'why': 'putting the grid back at the end of the assembly restores the measured defect: 1433px of analysis above the reels and 0 of 530 cards on screen', 'file': 'control_ui.html', 'find': '      + searchBar + body\n', 'replace': '      + searchBar\n', 'matches': 1}, {'why': 'putting the river strip back ABOVE the list is the v2965 order that helped push every card off his 660px screen — the clause added in v2985 must turn red on it. ⚠ v3358 RE-ANCHORED: the old anchor quoted the v2985 comment as it sat directly under `+ searchBar + body`, and v3358 moved that line, so this proof matched 0 times and proved nothing while the law it guards was itself red', 'file': 'control_ui.html', 'find': '      + searchBar + body\n      + timelineDiv\n      /* @@RULING v2985: the RIVER STRIP and the PIPELINE BOARD stay BELOW the reel list. Measured\n         at his real 1120x660: 1433px of furniture above the list put the first card 2101px below\n         the panel\'s own bottom edge - 530 cards rendered and not one on screen. v3289 later raised\n         the records strip and the chart ONLY, and only with an open-on-a-reel guard; these two did\n         not move and must not.\n         ⚠⚠ v2985 (#58) — THE RIVER STRIP MOVES BELOW THE LIST, AND THIS REVERSES v2965 ON PURPOSE.\n         v2965 put the strip ABOVE the list and called it "the organisation he asked for", quoting\n         him: "those reels coming in should be seen timestamped and recent 8 left there... and the\n         rest organized relating and relevant to the coding and backend."\n\n         MEASURED at his real 1120x660: the overlay is trapped inside .stage — a grid row worth\n         ~449px of a 660px window — and 549px of furniture sits above the first reel card, so THE\n         CARDS ARE ENTIRELY OFF-SCREEN. The panel named "your reels" was showing none of them. The\n         half of his sentence that v2965 served was "organized"; the half it broke was "should be\n         SEEN". This restores the second without discarding the first.\n\n         Weighed and rejected: raising the ceiling with position:fixed buys ~210px but covers the\n         transport deck, and :1738 is a recorded ruling — "the shelf must never bury the transport\n         deck (📚 stays a true toggle)". A scar outranks a layout preference.\n\n         ⚠ NOTHING IS REMOVED, NO ID MOVES, NOTHING IS COLLAPSED behind a click. The strip renders\n         in full — all four lanes, the station tallies, the ledger chip and both footnotes — it is\n         an ORDER change only, and _shLanesLoad/_shLanesRender find it by getElementById exactly as\n         before. It now sits with the other analytic blocks (pipeline board, highlights, timeline)\n         that v2965 itself placed below the list. */\n      /* ⚠⚠ v3121 (#58) — ACTIVITY LEADS THE ANALYTIC BAND, AND THAT IS AS HIGH AS IT MAY GO.\n         Konyo: *"for the ACTIVITY section i like i just want it stretched from top to bottom more\n         so its more representing chart and uptop organized with the other data/anlytics TOP of the\n         SHELF section move"*. Read literally that is "above the list", and v2985 already MEASURED\n         what that costs at his real 1120x660: the overlay is trapped inside `.stage` — a grid row\n         worth ~449px of a 660px window — and 549px of furniture above the first card put every\n         reel off-screen, so the panel named "your reels" showed none of them. A scar outranks a\n         layout preference, so the half of his sentence this serves is "organized WITH the other\n         data/analytics": the chart moves to the FRONT of the band instead of the back of it.\n         ⚠ ORDER ONLY. No id moves, nothing is removed, and `_shTimeline`/`_shLanesLoad`/\n         `_shStoryRender` each still find their block by getElementById exactly as before.\n         [[borrowed-surface]] [[visual-regression-detector]] */\n      + \'<div class="sh-lanes" id="sh-lanes"><div class="shr-wait">reading the river…</div></div>\'\n      + \'<div class="sh-story" id="sh-story"><div class="shs-wait">reading the pipeline…</div></div>\'\n      + _shHighlights();', 'replace': '      + \'<div class="sh-lanes" id="sh-lanes"><div class="shr-wait">reading the river…</div></div>\'\n      + searchBar + body\n      /* @@RULING v2985: the RIVER STRIP and the PIPELINE BOARD stay BELOW the reel list. Measured\n         at his real 1120x660: 1433px of furniture above the list put the first card 2101px below\n         the panel\'s own bottom edge - 530 cards rendered and not one on screen. v3289 later raised\n         the records strip and the chart ONLY, and only with an open-on-a-reel guard these two did\n         not move and must not.\n         ⚠⚠ v2985 (#58) — THE RIVER STRIP MOVES BELOW THE LIST, AND THIS REVERSES v2965 ON PURPOSE.\n         v2965 put the strip ABOVE the list and called it "the organisation he asked for", quoting\n         him: "those reels coming in should be seen timestamped and recent 8 left there... and the\n         rest organized relating and relevant to the coding and backend."\n\n         MEASURED at his real 1120x660: the overlay is trapped inside .stage — a grid row worth\n         ~449px of a 660px window — and 549px of furniture sits above the first reel card, so THE\n         CARDS ARE ENTIRELY OFF-SCREEN. The panel named "your reels" was showing none of them. The\n         half of his sentence that v2965 served was "organized" the half it broke was "should be\n         SEEN". This restores the second without discarding the first.\n\n         Weighed and rejected: raising the ceiling with position:fixed buys ~210px but covers the\n         transport deck, and :1738 is a recorded ruling — "the shelf must never bury the transport\n         deck (📚 stays a true toggle)". A scar outranks a layout preference.\n\n         ⚠ NOTHING IS REMOVED, NO ID MOVES, NOTHING IS COLLAPSED behind a click. The strip renders\n         in full — all four lanes, the station tallies, the ledger chip and both footnotes — it is\n         an ORDER change only, and _shLanesLoad/_shLanesRender find it by getElementById exactly as\n         before. It now sits with the other analytic blocks (pipeline board, highlights, timeline)\n         that v2965 itself placed below the list. */\n      /* ⚠⚠ v3121 (#58) — ACTIVITY LEADS THE ANALYTIC BAND, AND THAT IS AS HIGH AS IT MAY GO.\n         Konyo: *"for the ACTIVITY section i like i just want it stretched from top to bottom more\n         so its more representing chart and uptop organized with the other data/anlytics TOP of the\n         SHELF section move"*. Read literally that is "above the list", and v2985 already MEASURED\n         what that costs at his real 1120x660: the overlay is trapped inside `.stage` — a grid row\n         worth ~449px of a 660px window — and 549px of furniture above the first card put every\n         reel off-screen, so the panel named "your reels" showed none of them. A scar outranks a\n         layout preference, so the half of his sentence this serves is "organized WITH the other\n         data/analytics": the chart moves to the FRONT of the band instead of the back of it.\n         ⚠ ORDER ONLY. No id moves, nothing is removed, and `_shTimeline`/`_shLanesLoad`/\n         `_shStoryRender` each still find their block by getElementById exactly as before.\n         [[borrowed-surface]] [[visual-regression-detector]] */\n      + timelineDiv\n      + \'<div class="sh-story" id="sh-story"><div class="shs-wait">reading the pipeline…</div></div>\'\n      + _shHighlights();', 'matches': 1}, {'why': "inlining the reason again re-wraps it across three lines and takes the card back over the panel's own height", 'file': 'control_ui.html', 'find': '        if (r.why) b.title = String(r.why);\n', 'replace': '', 'matches': 1}]

if __name__ == "__main__":
    unittest.main(verbosity=2)
