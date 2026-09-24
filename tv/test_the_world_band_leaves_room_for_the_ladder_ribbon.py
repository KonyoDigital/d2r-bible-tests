# -*- coding: utf-8 -*-
"""#218 — THE WORLD BAND LEAVES ROOM FOR THE LADDER RIBBON IT STACKS ABOVE.

Found by LOOKING at Grok Bot's native Linux pack (visual-pass-20260924T012231Z, full-bible/03a): the
🐧 LINUX band covered the top half of "🪜 LADDER ACCOUNT — separate economy · your main account is
untouched" on every tick, while every gate stayed green and the bot filed the page SAW.

MEASURED in a headless render of the same seat (Linux UA, machine=windows, profile=ladder), before:

    width   band                      ladder ribbon      overlap
    1280    top 96  h 35  font 16px   top 120  h 21      11 px
    1120    top 96  h 35  font 16px   top 120  h 21      11 px
     901    top 128 h 35  font 16px   top 152  h 21      11 px
     375    top 167 h 21  font 9px    top 191  h 21       0 px   (the <=700px rule sets a size)

The band was DECLARED `font:var(--fw-semibold) 11px/1 inherit`. `inherit` is a CSS-wide keyword, not a
font family, so the shorthand is invalid — and because it contains var() it is invalid at
COMPUTED-value time, which drops the whole `font` to the inherited value: 16px, 35px tall, painting
over a ladder ribbon whose stack offset (`body.cousin-shell #ladder-ribbon{top:24px}`, v665.1) was
sized for the 11px band the author wrote. The ladder ribbon carries the identical shorthand and is
rescued only by a later `font-size:9.5px!important`. After the longhands: band 22px, overlap 0 at all
five widths.

⚠ A GEOMETRY GATE WOULD RUN ONLY ON CI; THIS IS A PARSE, DETERMINISTIC ON EVERY MACHINE — the same
choice visual-regression-detector ④b records for the grid track that blew the page open. It pins the
RESERVE law (the band's line box + padding fits inside the stack offset, both read from the file),
never the number 22. [[visual-regression-detector]] [[two-fixes-broke-each-other]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

#: a font shorthand whose FAMILY slot is a CSS-wide keyword — invalid, and silently dropped
_BAD_FONT = re.compile(r"(?<![-\w])font\s*:\s*[^;{}]*?\d(?:\.\d+)?(?:px|em|rem)(?:\s*/\s*[\d.]+[a-z%]*)?\s+"
                       r"(?:inherit|initial|unset|revert)\s*(?:[;}]|!important)")


def _css():
    with io.open(BIBLE, encoding="utf-8") as fh:
        src = fh.read()
    # comments stripped, so a rule QUOTED in a comment cannot satisfy or fail anything
    return re.sub(r"/\*.*?\*/", " ", src, flags=re.S)


def _rule(css, selector):
    """The declaration block of the FIRST rule whose selector is exactly `selector`."""
    m = re.search(r"(?:^|[}\s])" + re.escape(selector) + r"\s*\{([^}]*)\}", css)
    return m.group(1) if m else None


def _px(decls, prop):
    m = re.search(r"(?<![-\w])" + re.escape(prop) + r"\s*:\s*([\d.]+)px", decls or "")
    return float(m.group(1)) if m else None


class TheWorldBandLeavesRoomForTheLadderRibbon(unittest.TestCase):

    def setUp(self):
        self.css = _css()
        self.band = _rule(self.css, "#cousin-ribbon")
        self.assertIsNotNone(self.band, "premise: the #cousin-ribbon rule is gone — this law "
                                        "judges nothing, which is UNMEASURED, not clean")

    def test_the_band_declares_a_font_the_browser_will_keep(self):
        self.assertIsNone(_BAD_FONT.search(self.band),
                          "#cousin-ribbon uses a font shorthand whose family is a CSS-wide keyword — "
                          "invalid, so the band falls back to the page font (measured 16px, 35px tall)")
        self.assertIsNotNone(_px(self.band, "font-size"), "the band declares no font size at all")

    def test_the_band_fits_inside_the_stack_offset_the_ladder_ribbon_was_given(self):
        """THE RESERVE, read from the file on both sides — never the number 22."""
        m = re.search(r"body\.cousin-shell\s+#ladder-ribbon\s*\{[^}]*?top\s*:\s*([\d.]+)px", self.css)
        self.assertIsNotNone(m, "premise: the ladder ribbon's stack offset is gone")
        offset = float(m.group(1))
        fs = _px(self.band, "font-size")
        lh = re.search(r"(?<![-\w])line-height\s*:\s*([\d.]+)(px)?", self.band)
        self.assertTrue(fs and lh, "the band's font-size or line-height is not declared as a number")
        line = float(lh.group(1)) if lh.group(2) else float(lh.group(1)) * fs
        pad = re.search(r"(?<![-\w])padding\s*:\s*([\d.]+)px\s+[\d.]+px\s+([\d.]+)px", self.band)
        self.assertIsNotNone(pad, "premise: the band's vertical padding is not in the shape read here")
        tall = line + float(pad.group(1)) + float(pad.group(2))
        self.assertLessEqual(tall, offset,
                             "the band is %.1fpx tall (line %.1f + padding %s/%s) and the ladder ribbon "
                             "is stacked %.1fpx below its top — it paints over the ribbon"
                             % (tall, line, pad.group(1), pad.group(2), offset))
        tog = _rule(self.css, "#cousin-ribbon .cr-tog")
        self.assertIsNotNone(tog, "premise: the band's toggle rule is gone")
        tfs = _px(tog, "font-size")
        self.assertTrue(tfs is None or tfs <= fs,
                        "the toggle declares a font larger than the band (%s > %s) — it sets the height"
                        % (tfs, fs))

    def test_the_invalid_font_shorthand_class_does_not_grow(self):
        """⚠ NINE OTHER SITES carry the same shorthand and were deliberately NOT changed: each renders
        at its inherited size today, and correcting it resizes text he has accepted. A ratchet, not a
        silence: the count may only fall, and every site is named."""
        sites = [m.start() for m in _BAD_FONT.finditer(self.css)]
        self.assertLessEqual(len(sites), 9,
                             "a NEW font shorthand with a CSS-wide keyword as its family arrived — it "
                             "is dropped at computed time and renders at whatever it inherits (%d sites)"
                             % len(sites))
        self.assertGreater(len(sites), 0, "premise: the scan finds none at all, so it may be blind — "
                                          "if the nine were fixed, lower the ceiling to 0 and delete "
                                          "this line")


RED_PROOF = [
    {
        "why": "#218 - the band's font shorthand restored: `inherit` as the family is invalid, the band "
               "falls back to 16px and paints over the ladder ribbon",
        "file": "bible.html",
        "find": "font-weight:var(--fw-semibold);font-size:11px;line-height:1;/* #218",
        "replace": "font:var(--fw-semibold) 11px/1 inherit;/* #218",
        "matches": 1,
    },
    {
        "why": "#218 - a band taller than its stack offset: the reserve law, not the number",
        "file": "bible.html",
        "find": "font-weight:var(--fw-semibold);font-size:11px;line-height:1;/* #218",
        "replace": "font-weight:var(--fw-semibold);font-size:16px;line-height:1;/* #218",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
