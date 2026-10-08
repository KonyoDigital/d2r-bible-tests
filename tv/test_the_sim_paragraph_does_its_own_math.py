# -*- coding: utf-8 -*-
"""REG-2079 - THE SIMULATOR'S PROSE DOES ITS OWN MATH: EVERY FIGURE IS DERIVED FROM THE RATE THE SAME PARAGRAPH NAMES.

The #231 code seat, on May's 13f8e944 and re-measured at HEAD 2026-10-08: the simulator help says a Shako is "1-in-836",
then "not guaranteed in 912 runs", "~58% of 500-kill Meph sessions get zero" and "0.55 is the math-expected number" -
all three are the old 1:912 arithmetic (500/912 = 0.548, (1-1/912)^500 = 57.8%). The anchor moved and its sentences did
not. This law reads the rate out of the paragraph and recomputes the rest, so the next rate change cannot strand them.
"""
import io
import math
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

PAGE = os.path.join(os.path.dirname(HERE), "bible.html")
ANCHOR = 'Shako" means each kill rolls a fresh 1-in-'


def _paragraphs():
    with io.open(PAGE, encoding="utf-8") as f:
        s = f.read()
    if s.count(ANCHOR) != 1:
        raise AssertionError("the simulator paragraph's anchor matched %d times - re-point this law" % s.count(ANCHOR))
    i = s.index(ANCHOR)
    start = s.rindex("<p>", 0, i)
    end = s.index("</p>", s.index("</p>", i) + 4) + 4      # this paragraph and the one after it
    return re.sub(r"<[^>]+>", "", s[start:end])


class TheSimParagraphDoesItsOwnMath(unittest.TestCase):

    def test_every_figure_follows_from_the_named_rate(self):
        t = _paragraphs()
        n = int(re.search(r"1-in-(\d+)", t).group(1))
        self.assertEqual(int(re.search(r'"1:(\d+) Shako"', t).group(1)), n, "the quoted odds and the 1-in-N disagree: %r" % t)
        g = int(re.search(r"guaranteed in (\d+) runs", t).group(1))
        self.assertEqual(g, n, "'not guaranteed in %d runs' beside a 1-in-%d rate" % (g, n))
        m = re.search(r"~(\d+)% of (\d+)-kill", t)
        pct, kills = int(m.group(1)), int(m.group(2))
        want_zero = 100 * (1 - 1.0 / n) ** kills
        self.assertLessEqual(abs(pct - want_zero), 1.0,
                             "'~%d%% of %d-kill sessions get zero' - at 1:%d it is %.1f%%" % (pct, kills, n, want_zero))
        exp = float(re.search(r"([\d.]+) is the math-expected number", t).group(1))
        self.assertLessEqual(abs(exp - kills / float(n)), 0.01,
                             "'%.2f is the math-expected number' - at 1:%d over %d kills it is %.3f" % (exp, n, kills, kills / float(n)))


RED_PROOF = [
    {"why": "REG-2079 - the zero-Shako share goes back to the old 1:912 arithmetic",
     "file": "bible.html",
     "find": "that ~55% of 500-kill Meph sessions",
     "replace": "that ~58% of 500-kill Meph sessions",
     "matches": 1},
    {"why": "REG-2079 - the expected count goes back to the old 1:912 arithmetic",
     "file": "bible.html",
     "find": "even though 0.60 is the math-expected number",
     "replace": "even though 0.55 is the math-expected number",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
