# -*- coding: utf-8 -*-
"""THE RIVER STRIP MAY BE FOLDED AWAY — IT MAY NOT BE THINNED AWAY.

Konyo, 2026-09-16, on the strip above the pipeline:
    "for the river above the pipeline this section here is it needed visually?
     do i need this information? it can be hidden by me."

The answer shipped in v3198 was a <details> whose CLOSED line carries the one figure he acts
on and whose OPEN body still carries every defence the strip has accumulated. That shape has
exactly two ways to rot, and this file is the only thing standing in front of either:

  1. SOMEONE "SIMPLIFIES" THE FOLD BY DELETING THE BODY. The four-line TOMBSTONE note, the
     STATIONS chips and the ledger chip each exist because a real reader misread a real number
     (v2822, v2903, v2819). Folded they cost nothing; deleted they take three fixed defects
     with them. `test_a_zero_TOMBSTONE_carries_its_denominator` guards the note's phrase; this
     guards that the note is still reachable at all, i.e. that a BODY exists to hold it.
  2. THE CLOSED LINE DRIFTS FROM THE OPEN CARDS. The summary and the card must be two views of
     ONE number. The moment the summary reads its own source, the strip can say 6 closed and 4
     open on the same data and nothing notices. [[copy-drift]] [[label-outlived-referent]]

⚠ AND IT MUST DEFAULT CLOSED, because that is the whole of what he asked for. A fold that
ships `open` is the old surface wearing a caret.
"""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# ⚠ his Windows console is cp1255: printing a single non-ASCII glyph CRASHES the script WHILE
# REPORTING, so a clean tree exits non-zero and the failure is about the terminal, not the code.
try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass

_HERE = os.path.dirname(os.path.abspath(__file__))
_UI = os.path.join(_HERE, "control_ui.html")


def _between(src, start, end):
    """the whole region or nothing -- never a fixed window past the anchor.

    [[source-reading-guard]] [[source-window-shortcut]]: `src[i:i+N]` reports a region as
    ABSENT the moment it grows past N, which has produced four false readings in this repo.
    """
    i = src.find(start)
    if i < 0:
        return ""
    j = src.find(end, i + len(start))
    if j < 0:
        return ""
    return src[i:j]


_BLOCK = re.compile(r"/\*.*?\*/", re.S)
_LINE = re.compile(r"^[ \t]*//.*$", re.M)


def _code_only(src):
    """my own prose is not evidence about my own code.

    [[carved-skill-unloaded-is-unapplied]] -- this exact assertion went red on its FIRST run
    because the comment four lines above the listener contains the word `ontoggle` while
    explaining why an inline ontoggle is banned. A guard a comment can satisfy (or break) is
    measuring the file's prose, and this repo has shipped that defect five times.
    """
    return _LINE.sub("", _BLOCK.sub(" ", src))


class TheRiverFoldsWithoutLosingAFigure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(_UI, encoding="utf-8") as fh:
            cls.ui = fh.read()
        cls.fn = _between(cls.ui, "function _shLanesRender(d){", "window._shLanesRender")
        assert cls.fn, "could not find _shLanesRender -- this law is reading nothing"

    def test_the_strip_is_actually_folded(self):
        n = self.fn.count("<details class=\"shr-fold\"")
        self.assertEqual(1, n,
                         "expected exactly one <details class=\"shr-fold\"> in _shLanesRender, "
                         "found %d -- the fold is the whole fix" % n)

    def test_it_defaults_CLOSED(self):
        """he asked for it hidden; `open` on first paint is not hidden."""
        self.assertIn("var _foldOpen = false;", self.fn,
                      "the fold's default is not false -- he asked for it closed")
        self.assertIn("_foldOpen ? ' open' : ''", self.fn,
                      "the open attribute is not driven by the stored preference")

    def test_the_body_still_carries_the_full_strip(self):
        """the defences are FOLDED, never dropped."""
        self.assertIn("class=\"shr-body\">' + H.join('')", self.fn,
                      "the fold body no longer contains H.join('') -- the strip's own markup "
                      "(head, lanes, stations, ledger chip, TOMBSTONE note) has been dropped "
                      "rather than folded")

    def test_the_closed_line_reads_the_SAME_figure_as_the_open_card(self):
        """one number, two views -- never two sources."""
        mini = _between(self.fn, "var _mini = rows.map(", "}).join('');")
        self.assertTrue(mini, "the summary's mini-river could not be found")
        self.assertIn("l.count", mini,
                      "the closed summary does not read l.count -- the same expression the open "
                      "lane card uses. A second source here lets the two halves disagree.")
        self.assertNotIn("byStation", mini,
                         "the summary is reading station counts while the card reads lane "
                         "counts -- that is the v2903 misread, rebuilt one level up")

    def test_no_inline_toggle_handler(self):
        """[[console-ui-two-script-blocks]] -- an inline ontoggle fires during PARSE."""
        self.assertNotIn("ontoggle", _code_only(self.fn),
                         "an inline ontoggle attribute is back; this file has been bitten four "
                         "times by handlers in the markup")
        self.assertIn("addEventListener('toggle'", _code_only(self.fn),
                      "the toggle listener is not attached in script after the node is real")

    def test_the_preference_survives_a_repaint(self):
        """this renderer repaints on every shelf reload; an unstored state re-opens each time."""
        self.assertIn("d2r_shRiverOpen", self.fn,
                      "the fold state is not persisted -- it will spring open on every repaint")
        self.assertEqual(2, self.fn.count("d2r_shRiverOpen"),
                         "expected the key read once and written once, found %d uses"
                         % self.fn.count("d2r_shRiverOpen"))


RED_PROOF = [
    # each tampers the REAL thing the assertion is about, in a safe_copy sandbox
    ("control_ui.html", "<details class=\"shr-fold\"", "<div class=\"shr-fold\"",
     "test_the_strip_is_actually_folded"),
    ("control_ui.html", "var _foldOpen = false;", "var _foldOpen = true;",
     "test_it_defaults_CLOSED"),
    ("control_ui.html", "class=\"shr-body\">' + H.join('')", "class=\"shr-body\">' + ('')",
     "test_the_body_still_carries_the_full_strip"),
    ("control_ui.html", "addEventListener('toggle'", "addEventListenerX('toggle'",
     "test_no_inline_toggle_handler"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
