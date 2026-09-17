# -*- coding: utf-8 -*-
"""v3287 — A KPI CHIP MUST NAME THE QUANTITY IT COUNTS, AND WEAR ITS ROOM'S COLOUR.

Konyo, 2026-09-18: *"even top corner chronicles set uniques and runewords should color match the
tabs in main console.. same keywords and typography and structural pass visually so its properly
structured and architected and logically synced"*. Grok Bot's brief #5721489103 says the same from
the other side: *"Full Bible item colors must match the rest of the console (sets green, uniques
gold, runewords/crafts reds/oranges)"*.

MEASURED IN HIS SCREENSHOT AND THEN IN SOURCE: the Sessions header drew

    99/99   CHRONICLE      <- runewords forged        (bible.html:49849)
    309/403 CHRONICLE      <- chronicle uniques found (bible.html:49852)

**Two different quantities under one word, four inches apart.** That is the
"a number under a word naming another quantity" shape that cost the Kai console six versions, and
it is the same family as [[label-outlived-referent]]: the NUMBERS were both right.

THE COLOUR RULE IS NOT INVENTED HERE. Both files already declare the identical values
(--q-unique #c7b377, --q-set #00fc00, --rune #ff7d3c), and v1631 settled which one a LABEL takes:
*"an item NAME obeys the game... a TAB is a label for a ROOM, and the Forge's room is where runes
become words, so it wears the RUNE colour"*. These chips label rooms, so Runewords takes --rune
rather than the gold a runeword's NAME is painted. Do not "correct" that to gold: it would be
re-litigating a ruling that was measured against his own install.

⚠ COMMENTS ARE STRIPPED BEFORE READING, and here that is load-bearing rather than hygienic: the
CSS block this law guards carries a comment containing the word CHRONICLE, describing the very
defect being removed. A law grepping raw source would read its own commentary.
[[presence-law-vs-reachability-law]]
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

BIBLE = os.path.join(ROOT, "bible.html")
CONSOLE = os.path.join(ROOT, "tv", "control_ui.html")


def _between(src, start, end, what):
    i = src.find(start)
    if i < 0:
        raise AssertionError("anchor START vanished for %s: %r" % (what, start[:70]))
    j = src.find(end, i + len(start))
    if j < 0:
        raise AssertionError("anchor END vanished for %s: %r" % (what, end[:70]))
    return src[i:j]


class TestAKpiChipNamesWhatItCounts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # ".js" not the real path — _executable_only dispatches on EXTENSION; an .html path falls
        # through to the python branch where ast.parse throws and the source returns UNSTRIPPED.
        cls.code = _executable_only(io.open(BIBLE, encoding="utf-8").read(), ".js")
        cls.css = _executable_only(io.open(BIBLE, encoding="utf-8").read(), ".js")
        cls.ui = _executable_only(io.open(CONSOLE, encoding="utf-8").read(), ".js")

    def _kpi_block(self):
        return _between(self.code,
                        # ⚠ NOT `var rwT = ...`: that line appears TWICE, and its first hit is
                        # the unrelated `chron` builder. The slice then ran to the sc-kpis end
                        # anchor across a huge span and read a "Chronicle" belonging to neither
                        # chip. A non-unique anchor is a wrong region, not a near miss.
                        # [[source-reading-guard]]
                        "if (rwT) kh.push(",
                        "var kEl = document.getElementById('sc-kpis');",
                        "the sc-kpi builder")

    def test_no_two_chips_hide_behind_one_word(self):
        blk = self._kpi_block()
        self.assertNotIn("Chronicle", blk,
                         "a chip still says 'Chronicle'. Two DIFFERENT quantities wore that one "
                         "word — 99/99 runewords and 309/403 uniques — and neither number was "
                         "wrong; the noun was")
        for label in ("<span>Runewords</span>", "<span>Uniques</span>", "<span>Sets</span>"):
            self.assertIn(label, blk, "%s must name the quantity it counts" % label)

    def test_each_chip_declares_its_room(self):
        blk = self._kpi_block()
        for cls_ in ("sc-kpi k-rw", "sc-kpi k-uni", "sc-kpi k-set"):
            self.assertIn(cls_, blk,
                          "%s is missing, so the chip cannot take its room's colour" % cls_)

    def test_the_colours_come_from_the_shared_tokens(self):
        """Never a literal: bible.html and control_ui.html already agree on these values, and a
        hex typed here would be a second vocabulary that can drift. [[copy-drift]]"""
        for rule in ("#tab-session .sc-kpi.k-rw  b{color:var(--rune)}",
                     "#tab-session .sc-kpi.k-uni b{color:var(--q-unique)}",
                     "#tab-session .sc-kpi.k-set b{color:var(--q-set)}"):
            self.assertIn(rule, self.css,
                          "missing or hard-coded: %s — the chip must read the shared token" % rule)

    def test_the_door_to_the_full_bible_is_not_a_footnote(self):
        """His words: 'upgraded and emphasized and seen better and stretched and bigger and
        glowing'. It was --gold-dim on --edge at the smallest type the shell declares."""
        blk = _between(self.ui,
                       'body[data-view="sessions"] .hub-bible {',
                       'body[data-view="sessions"] .hub-bible:hover',
                       "the hub-bible rule")
        self.assertIn("justify-self: stretch", blk, "the door must span the row, not hug the end")
        self.assertIn("box-shadow", blk, "the door must glow")
        self.assertNotIn("--gold-dim", blk, "the door must carry the live gold, not the dim one")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "putting 'Chronicle' back on the runewords chip restores the two-quantities-one-word defect",
        "file": "bible.html",
        "find": "<b>'+_scRwMade()+'/'+rwT+'</b><span>Runewords</span>",
        "replace": "<b>'+_scRwMade()+'/'+rwT+'</b><span>Chronicle</span>",
        "matches": 1,
    },
    {
        "why": "dropping the room class leaves the chip unable to take its colour",
        "file": "bible.html",
        "find": '<div class="sc-kpi k-uni">',
        "replace": '<div class="sc-kpi">',
        "matches": 1,
    },
    {
        "why": "a hard-coded hex forks a second colour vocabulary that can drift from the console",
        "file": "bible.html",
        "find": "#tab-session .sc-kpi.k-set b{color:var(--q-set)}",
        "replace": "#tab-session .sc-kpi.k-set b{color:#00fc00}",
        "matches": 1,
    },
    {
        "why": "hugging the end again makes the door the quietest thing on the screen",
        "file": "tv/control_ui.html",
        "find": "justify-self: stretch; width: 100%;",
        "replace": "justify-self: end;",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
