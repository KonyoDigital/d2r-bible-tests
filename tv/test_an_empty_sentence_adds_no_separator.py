# -*- coding: utf-8 -*-
"""GrokBot bug 10 (2026-10-27) - AN EMPTY PUBLISHED SENTENCE ADDS NO " · ".

In the shadow, a lane whose list was sent empty answers sentence '' from _publishedLane (pinned on purpose by
test_shadow_mode_reads_their_console). Seven places glued ' · ' + sentence on anyway, so the shadow read
"0 / 99 runewords forged · · 91 workable" and the Sessions KPI tiles ended in a stray " · ".

The seven joins are written as `X.sentence ? ' · ' + X.sentence : ''`. This reads bible.html's code (comments dropped)
and counts the guarded joins and the bare ones by their full expression - every published lane's sentence that is glued
to a separator must be guarded.
RED_PROOF below.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")

# a separator glued straight onto a published lane's sentence, in either string form the page uses
BARE = (re.compile(r"·\s*'\s*\+\s*_pub\w+\.sentence\b"), re.compile(r"·\s*\$\{_pub\w+\.sentence\}"),
        re.compile(r"=\s*'\s*·\s*'\s*\+\s*_pub\w+\.sentence\s*;"))
GUARDED = re.compile(r"_pub(\w+)\.sentence\s*\?\s*' · '\s*\+\s*_pub\1\.sentence\s*:\s*''")


class AnEmptySentenceAddsNoSeparator(unittest.TestCase):

    def setUp(self):
        with io.open(BIBLE, encoding="utf-8") as fh:
            self.src = fh.read()

    def test_no_separator_is_glued_to_a_bare_sentence(self):
        rest = GUARDED.sub("", self.src)       # a guarded join contains the bare shape inside it; look at the rest
        hits = []
        for rx in BARE:
            hits += [rest[max(0, m.start() - 60):m.end()].replace("\n", " ") for m in rx.finditer(rest)]
        self.assertEqual(hits, [], "a ' · ' is glued to a published sentence that can be empty (bug 10): %r" % hits)

    def test_the_seven_joins_are_guarded(self):
        lanes = sorted(m.group(1) for m in GUARDED.finditer(self.src))
        self.assertGreaterEqual(len(lanes), 7, "a guarded join is gone: %r" % lanes)
        for lane in ("Forge", "Uni", "Sets", "KpiRw", "KpiUni", "KpiSets", "Ring"):
            self.assertIn(lane, lanes, "the %s join is not guarded" % lane)


RED_PROOF = [
    {"why": "bug 10 - the runeword line glues ' · ' to an empty sentence again ('forged · · 91 workable')",
     "file": "bible.html",
     "find": "        _rwGap = _pubForge.sentence ? ' · ' + _pubForge.sentence : '';",
     "replace": "        _rwGap = ' · ' + _pubForge.sentence;",
     "matches": 1},
    {"why": "bug 10 - the Sessions runeword KPI ends in a stray ' · ' again",
     "file": "bible.html",
     "find": "<span>Runewords'+(_pubKpiRw.sentence ? ' · '+_pubKpiRw.sentence : '')+'</span>",
     "replace": "<span>Runewords · '+_pubKpiRw.sentence+'</span>",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
