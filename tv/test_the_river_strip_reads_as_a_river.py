# -*- coding: utf-8 -*-
"""v2772/v2773 — THE FOUR-LANE RIVER STRIP MUST STILL SAY "RIVER" AT EVERY WIDTH.

This strip's whole job is one sentence: *these four stages are one pipeline, and reels move
left to right through them.* Every defect below broke that sentence WITHOUT breaking a pixel
test — the strip still rendered, still carried the right numbers, and still said the wrong thing.

=== THE MEASUREMENT THAT MADE THIS A GATE, NOT A TASTE CALL ===
Handed ONLY a 901px picture of the strip, with none of the vocabulary from the brief, a
DIFFERENT model family read it as:
    @1440  "four boxes are workflow stages ... reels move left to right (FIFO)"
    @901   "INTAKE -> PRINTER -> CAPTURE form a processing pipeline (arrows show flow);
            TOMBSTONE is a SEPARATE END-STATE"
THE WRAP CHANGED THE MEANING. A reader was told the last stage sits outside the river, which is
the one thing this strip exists to deny. [[grok-second-eye]] [[visual-regression-detector]]

=== THE FOUR LAWS, AND THE MEASUREMENT BEHIND EACH ===

  L1  THE LANES DO NOT WRAP AT 901-904.  At viewport 901 the flow measures 489px, and four lanes
      at a 120px basis plus three arrows plus six 6px gaps need >=543px. Four pixels short at 901;
      at >=905 they shrink and fit; at <=900 a different shell gives them 181px. So the broken
      band was exactly 901-904 — and 901 is the width this repo already has a scar at, one pixel
      above a breakpoint. Pinned as the LAW (the basis must leave room in the narrowest flow this
      layout ever hands the lanes), not as the number 104. [[regression-guard]]

  L2  THE STICKY CLOSE BUTTON HAS ITS OWN GUTTER.  `#th-shelf-x` is position:sticky, top:0,
      z-index:4, 36x36. At scrollTop 0 it clears the strip at every width — which is why an
      open-and-measure pass called this clean for two rounds. At scrollTop 60 and 120 its rect
      INTERSECTED `.shr-lane` at 1440, 1120, 901 AND 375: at 1440 it sat x1003-1039 while the
      TOMBSTONE tile ended at 1025, covering that tile's top-right corner. The fix is the same
      48px gutter `.sh-head` has carried all along. [[stale-reading]] — a reading taken at one
      scroll position is not a reading of the page.

  L3  THE HEADING IS A SENTENCE, NOT A SET OF COLUMNS.  Bare text inside a flex container becomes
      an anonymous flex item, so `the river · ` / `49` / ` reel(s) on the shelf` were THREE items
      that each wrapped in their own column. MEASURED at 375: three ragged columns with the
      middot stranded alone at the end of a line, the FIFO qualifier crushed into a 61px column
      three lines tall. Heights: 16px at >=561, 31px at 480-560, 47px at <=414.

  L4  THE ORDER SURVIVES THE ARROWS.  Below 700px the connectors are hidden and NOTHING replaced
      them: four tiles in a 2+2 block with no direction reads as a scoreboard — four independent
      tallies — not as a river with a first and a last. The strip now numbers its lanes the way
      the printer spine 12px below it has numbered its stations since v2587.

  L5  THE TALLIES ARE SEPARATED BY ALIGNMENT, NOT BY A GLYPH.  `CAPTURE 12 JOIN 4` parsed as one
      four-word phrase across an 8px gap. ⚠ THE FIRST FIX WAS WRONG AND THE PIXELS SAID SO: a
      middot riding on the FOLLOWING chip (so it could never dangle at a line END) simply orphaned
      at the other end — `· STATION 7 · EMPTY 0` opening the second line, and a bare
      `· TOMBSTONE 0` under `ROUTED 1`. A separator that wraps is orphaned somewhere; choosing
      which end is not a fix. This file's own printer spine already settled it — it dropped its
      '›' glyphs for a grid after they dangled at 939px, because a grid cannot orphan a separator.

⚠⚠ EVERY LAW HERE READS EXECUTABLE TEXT WITH THE COMMENTS STRIPPED. Six times in one session a
law in this repo was satisfied — or broken — by prose, including the notes above, which quote the
very declarations they describe (`120px`, `::after`, `· STATION 7`). A guard that greps a file
that documents itself must strip `<!-- -->` and `/* */` first or it is grading its own paragraphs.
[[source-reading-guard]] [[feedback-comments-vs-code]]
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

UI_PATH = os.path.join(HERE, "control_ui.html")
RAW = io.open(UI_PATH, encoding="utf-8").read()


def _strip_comments(src):
    """`<!-- -->` and `/* */` out. ⚠ THE NOTES IN THIS FILE AND IN control_ui.html BOTH QUOTE THE
    DEFECTS THEY FIXED, so an un-stripped grep finds `120px`, `::after` and `flex-wrap` inside the
    paragraph explaining why they are gone. Line comments are dropped only when the line's first
    non-space characters are `//`, because `//` also appears inside http:// URLs and inside JS
    strings this file builds its markup from. [[source-reading-guard]]
    """
    src = re.sub(r"<!--.*?-->", " ", src, flags=re.S)
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    return "\n".join("" if ln.lstrip().startswith("//") else ln for ln in src.split("\n"))


CODE = _strip_comments(RAW)


def _decl(code, selector):
    """The declaration block for one selector, anchored at BOTH ends.

    Anchored on `{` ... `}` from the selector's own occurrence rather than a fixed character
    window: a `src[i:i+N]` slice that runs past the region reads as ABSENT, which is how a rule
    that was demonstrably present got reported missing four times in one session.

    ⚠ THE SELECTOR MUST END WHERE IT SAYS IT ENDS, AND THIS GUARD FAILED ON ITS FIRST RUN FOR
    EXACTLY THAT REASON. A plain `find("#th-shelfov .shr-st")` matches `#th-shelfov .shr-sts`
    fourteen lines earlier — a longer selector that merely starts the same way — so L5 read the
    grid container's block, found no `white-space`, and reported a defect in a rule it had never
    looked at. A prefix is not a match. [[source-reading-guard]] [[feedback-suspect-the-instrument]]
    """
    m = re.search(re.escape(selector) + r"\s*(?:,[^{]*)?\{", code)
    if not m:
        return None
    j = m.end() - 1
    k = code.find("}", j)
    return None if k < 0 else code[j + 1:k]


def _px(text, prop):
    if text is None:
        return None
    m = re.search(re.escape(prop) + r"\s*:\s*([^;}]+)", text)
    return None if not m else m.group(1).strip()


class RiverStripLaws(unittest.TestCase):

    # ── the instrument first: a law that cannot see its subject proves nothing ──────────────
    def test_00_the_strip_is_actually_in_this_file(self):
        """⚠ A GUARD THAT CANNOT REACH ITS SUBJECT PASSES EVERY OTHER TEST BELOW BY ACCIDENT."""
        for anchor in ("#th-shelfov .shr-lane", "#th-shelfov .shr-head",
                       "#th-shelfov .shr-sts", "#th-shelfov .shr-n",
                       "class=\"shr-lane", "_shLanesRender"):
            self.assertIn(anchor, CODE,
                          "%r is not in the STRIPPED source — this guard is reading the wrong "
                          "file or the strip has been renamed, and every law below is vacuous"
                          % anchor)
        self.assertLess(len(CODE), len(RAW),
                        "the comment stripper removed nothing, so every law below is grading "
                        "prose as well as code")

    # ── L1 ──────────────────────────────────────────────────────────────────────────────────
    def test_L1_four_lanes_fit_the_narrowest_flow_they_are_ever_given(self):
        """The basis must leave room for 4 lanes + 3 arrows + 6 gaps inside 489px.

        489px is the MEASURED flow width at viewport 901 — the narrowest this layout ever hands
        the four-across arrangement, because at <=900 a different shell widens it to 181px per
        lane and below 700 the row deliberately goes 2+2. The number pinned is the arithmetic,
        not the current 104px: raise the basis to 120 and this fails, which is what shipped.
        """
        d = _decl(CODE, "#th-shelfov .shr-lane")
        self.assertIsNotNone(d, "could not read the .shr-lane rule")
        flex = _px(d, "flex")
        self.assertIsNotNone(flex, ".shr-lane no longer declares a flex shorthand")
        m = re.search(r"(\d+(?:\.\d+)?)px", flex)
        self.assertIsNotNone(m, "the flex basis is not a px length: %r" % flex)
        basis = float(m.group(1))

        FLOW_AT_901 = 489.0     # measured, viewport 901, .shr-flow
        ARROWS, GAPS, GAP = 3, 6, 6.0
        arrow_w = 8.0           # measured, the ▸ glyph's own box at --fs-sm
        need = basis * 4 + arrow_w * ARROWS + GAP * GAPS
        self.assertLessEqual(
            need, FLOW_AT_901,
            "four lanes at a %gpx basis need %gpx and the flow at viewport 901 is only %gpx, so "
            "they wrap 3+1 — TOMBSTONE becomes a full-width banner, the third connector points at "
            "nothing, and a cold cross-family reader called TOMBSTONE 'a SEPARATE END-STATE'."
            % (basis, need, FLOW_AT_901))

    # ── L2 ──────────────────────────────────────────────────────────────────────────────────
    def test_L2_the_lanes_card_reserves_the_sticky_close_buttons_gutter(self):
        """`#th-shelf-x` is 36x36 and sticky; the card must keep a gutter wider than that."""
        d = _decl(CODE, "#th-shelfov .sh-lanes")
        self.assertIsNotNone(d, "could not read the .sh-lanes rule")
        pr = _px(d, "padding-right")
        self.assertIsNotNone(
            pr, ".sh-lanes has no padding-right. `#th-shelf-x` is position:sticky top:0 and 36px "
                "wide: without a gutter its rect intersects .shr-lane at scrollTop 60 and 120 at "
                "1440, 1120, 901 and 375 — clean at scrollTop 0, which is the only place a "
                "single open-and-measure pass ever looks")
        m = re.search(r"(\d+(?:\.\d+)?)px", pr)
        self.assertIsNotNone(m, "padding-right is not a px length: %r" % pr)
        self.assertGreaterEqual(
            float(m.group(1)), 44.0,
            "the gutter is %s but the sticky ✕ is 36px wide and sits inset from the overlay's "
            "own padding — measured, it needs 48px, the same gutter .sh-head has carried all "
            "along" % pr)
        head = _decl(CODE, "#th-shelfov .sh-head")
        self.assertIsNotNone(head, "could not read the .sh-head rule")
        self.assertIsNotNone(_px(head, "padding-right"),
                             ".sh-head lost the gutter this one was copied from — if the heading "
                             "no longer needs it, this law's premise has moved")

    # ── L3 ──────────────────────────────────────────────────────────────────────────────────
    def test_L3_the_river_heading_is_one_element_not_three_anonymous_flex_items(self):
        d = _decl(CODE, "#th-shelfov .shr-head")
        self.assertIsNotNone(d, "could not read the .shr-head rule")
        self.assertIn("flex", _px(d, "display") or "",
                      ".shr-head is no longer a flex row; this law's premise has moved")
        self.assertIn(
            "wrap", _px(d, "flex-wrap") or "",
            ".shr-head is a nowrap flex row again. With nowrap the label and the FIFO qualifier "
            "are forced onto one line and each shrinks into its own ragged column — measured at "
            "375: three columns, 47px tall, with the middot alone at the end of a line")

        # the label must be its own element in the BUILDER, not a bare text run
        self.assertIn(
            'class="shr-lbl"', CODE,
            "the builder no longer wraps the heading text in .shr-lbl. A run of text sitting "
            "directly inside a flex container becomes its own anonymous flex item, so "
            "`the river · `, `<b>49</b>` and ` reel(s) on the shelf` become THREE items that "
            "each wrap independently")
        lbl = _decl(CODE, "#th-shelfov .shr-lbl")
        self.assertIsNotNone(lbl, ".shr-lbl is emitted by the builder but has no rule — an "
                                  "unstyled span does not stop the columns")

        fifo = _decl(CODE, "#th-shelfov .shr-fifo")
        self.assertIsNotNone(fifo, "could not read the .shr-fifo rule")
        self.assertEqual(
            (_px(fifo, "white-space") or "").strip(), "nowrap",
            ".shr-fifo may break again. Measured at 375 it was crushed to a 61px column three "
            "lines tall reading 'oldest / first · / FIFO'")

    # ── L4 ──────────────────────────────────────────────────────────────────────────────────
    def test_L4_every_lane_carries_an_ordinal_so_the_order_survives_the_arrows(self):
        """Below 700px `.shr-arrow` is display:none. Something else must carry the direction."""
        hidden_narrow = re.search(
            r"@media[^{]*max-width:\s*700px[^{]*\{[^}]*\.shr-arrow\s*\{[^}]*display:\s*none",
            CODE, flags=re.S)
        self.assertIsNotNone(
            hidden_narrow,
            "the <=700px rule that hides .shr-arrow is gone. If the arrows now survive, this "
            "law's premise has moved and the ordinal may be redundant — re-measure before "
            "deleting it")

        m = re.search(r"'<div class=\"shr-n\">(.{0,80}?)</div>'", CODE, flags=re.S)
        if m is None:
            m = re.search(r'class="shr-n"><u>', CODE)
        self.assertIsNotNone(
            m,
            "the .shr-n builder no longer emits an ordinal. With the arrows hidden below 700px "
            "and no numeral, four tiles in a 2+2 block carry no direction at all — they read as "
            "a scoreboard of four independent tallies, not as one river")
        self.assertIn(
            'class="shr-n"><u>', CODE,
            "the ordinal is not the printer spine's `<u>n</u>NAME` shape. The two boards sit 12px "
            "apart; two different ways of numbering the same kind of thing is the 'two engines' "
            "defect v2587 was fixed to close")
        n = _decl(CODE, "#th-shelfov .shr-n u")
        self.assertIsNotNone(n, ".shr-n u has no rule, so the numeral renders at the lane name's "
                                "own weight and colour and reads as part of the name")

    # ── L5 ──────────────────────────────────────────────────────────────────────────────────
    def test_L5_the_station_tallies_are_separated_by_alignment_not_by_a_glyph(self):
        sts = _decl(CODE, "#th-shelfov .shr-sts")
        self.assertIsNotNone(sts, "could not read the .shr-sts rule")
        self.assertEqual(
            (_px(sts, "display") or "").strip(), "grid",
            ".shr-sts is not a grid. These chips wrap, and a separator glyph between wrapping "
            "items is orphaned at one end or the other — measured both ways: an ::after strands "
            "it at a line end (the printer spine's '›' at 939px), a ::before strands it at a line "
            "start (`· STATION 7 · EMPTY 0`, and a bare `· TOMBSTONE 0` under `ROUTED 1`). "
            "A grid cannot orphan a separator because there is no separator")

        st = _decl(CODE, "#th-shelfov .shr-st")
        self.assertIsNotNone(st, "could not read the .shr-st rule")
        self.assertEqual(
            (_px(st, "white-space") or "").strip(), "nowrap",
            "a chip may split between its label and its number again — which is how `STASH` and "
            "`11` landed on different lines in the spine")

        # and no pseudo-element may reintroduce one
        bad = re.findall(r"\.shr-st[^{\n]*::(?:before|after)[^{]*\{[^}]*content\s*:", CODE)
        self.assertEqual(
            len(bad), 0,
            "%d pseudo-element(s) inject content beside a .shr-st chip: %r. That is the fix that "
            "was tried and refuted on pixels — see L5 in this file's docstring" % (len(bad), bad))


if __name__ == "__main__":
    unittest.main(verbosity=2)
