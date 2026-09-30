# -*- coding: utf-8 -*-
"""REG-1555 (2026-09-30) — THE HEART MAP COUNTS A SURFACE AS WATCHED ONLY WHERE A WATCHER'S CODE NAMES IT WHOLE.

The skeptic pass over #41 rank 25 (REG-1538): heart_map's `seen` was `i in blob` over the four watcher files as
written — comments, docstrings and all — so a surface read WATCHED when a COMMENT mentioned it, and a short id read
WATCHED when a longer one contained it. MEASURED on the tree that blessed a console floor of 17: nine of the
seventeen (`bug`, `heart-chip`, `sh-stationbar`, `sigil`, `stage-hold`, `th-shelfov`, `theatre`, `vault-body`,
`win-ctl`) stood only in comments and docstrings — `heart-chip` in the very comment in console_doctor recording that
it had been REMOVED from WATCHES "because it could never match" — and `th-shelf` only inside `th-shelf-x`. Thirteen
of seventeen. The organ that exists to say a surface is unwatched said WATCHED, and the ratchet banked it.
[[source-reading-guard]] [[regression-guard]]

WHAT THIS LAW DRIVES, over a planted page and a planted watcher (heart_map._read stood in; the real tree is never
written), and once over the real tree as a corroborator:
  · ONLY CODE, ONLY WHOLE: a page carrying planted-code, planted-comment, planted-doc, planted-prefix and
    planted-prefix-x, against a watcher whose code names "planted-code" and "planted-prefix-x", whose comment names
    planted-comment and whose docstrings name planted-doc, reads seen == [planted-code, planted-prefix-x] on BOTH
    pages. Every other name is UNWATCHED, however loudly the prose says it.
  · A WATCHER THAT DOES NOT PARSE IS MISSING, never read as prose: watched() names it and measure() withholds seen.
  · THE STRIPPER KEEPS THE LINE COUNT and keeps ordinary strings: a message that names a surface is code.
  · THE REAL TREE, CORROBORATED: what measure() and measure_pages() count equals an independent reading — a
    word-boundary search of each name over the same code-only text — and the console's list no longer carries a
    name only prose names, checked against the code rather than pinned to a roster.
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
from console_safe import enable; enable()

import heart_map as HM

PAGE = ('<div id="planted-code"></div><div id="planted-comment"></div><div id="planted-doc"></div>'
        '<div id="planted-prefix"></div><div id="planted-prefix-x"></div>')
WATCHER = ('"""planted-doc is named here, in the module docstring."""\n'
           'import os\n'
           '\n'
           'class W(object):\n'
           '    """planted-doc again, a class docstring."""\n'
           '\n'
           '    def f(self):\n'
           '        """planted-doc a third time,\n'
           '        across two lines."""\n'
           '        x = "planted-code"  # planted-comment is named here, in a trailing comment\n'
           '        # planted-comment again, on a line of its own\n'
           '        y = "the id planted-prefix-x is named whole here"\n'
           '        return x, y\n')
BROKEN = "def f(:\n    return 1\n"


def _stand_in(watcher_text):
    real = HM._read

    def read(name):
        if name in (n for n, _l in HM.PAGES):
            return PAGE
        if name == HM.WATCHERS[0]:
            return watcher_text
        if name in HM.WATCHERS:
            return ""                      # readable, and names nothing
        return real(name)
    return real, read


class TheHeartMapReadsCodeNotProse(unittest.TestCase):

    def setUp(self):
        self.real_read = HM._read

    def tearDown(self):
        HM._read = self.real_read

    def test_only_a_whole_name_in_a_watchers_code_counts_on_every_page(self):
        _real, HM._read = _stand_in(WATCHER)
        pages, missing = HM.measure_pages()
        self.assertEqual([], missing)
        for name, _label in HM.PAGES:
            self.assertEqual(sorted(["planted-code", "planted-comment", "planted-doc", "planted-prefix", "planted-prefix-x"]),
                             pages[name]["ids"], "the planted page was not the page measured for %s" % name)
            self.assertEqual(["planted-code", "planted-prefix-x"], pages[name]["seen"],
                             "%s: a name the watcher only mentions in prose, or only inside a longer id, counted as "
                             "watched: %r" % (name, pages[name]["seen"]))
        ids, seen, missing = HM.measure()
        self.assertEqual(["planted-code", "planted-prefix-x"], seen, "measure() and measure_pages() disagree")

    def test_a_watcher_that_does_not_parse_is_missing_not_read_as_prose(self):
        _real, HM._read = _stand_in(BROKEN)
        blob, missing = HM.watched()
        self.assertEqual([HM.WATCHERS[0]], missing, "a watcher that does not parse was read as text")
        ids, seen, missing2 = HM.measure()
        self.assertIsNotNone(ids)
        self.assertIsNone(seen, "seen was measured through a watcher that does not parse")
        self.assertEqual([HM.WATCHERS[0]], missing2)

    def test_the_stripper_keeps_the_line_count_and_ordinary_strings(self):
        code = HM._code_only(WATCHER)
        self.assertIsNotNone(code)
        self.assertEqual(WATCHER.count("\n"), code.count("\n"), "blanking prose moved the lines")
        self.assertIn('"planted-code"', code)
        self.assertIn("planted-prefix-x", code, "an ordinary string naming a surface is code and must survive")
        self.assertNotIn("planted-comment", code, "a comment survived the stripper")
        self.assertNotIn("planted-doc", code, "a docstring survived the stripper")
        self.assertIsNone(HM._code_only(BROKEN))
        self.assertEqual("", HM._code_only(""))

    def test_the_real_tree_is_counted_the_way_an_independent_reader_counts_it(self):
        """a corroborator with a different implementation: a word-boundary search per name over the same code-only
        text. Whatever the numbers are today, the two readings must agree on every page — and a name that only
        prose names (measured 2026-09-30: heart-chip, whose removal from WATCHES console_doctor's own comment records)
        must not be in the console's list unless code now names it, which is asked of the code, never pinned."""
        pages, missing = HM.measure_pages()
        self.assertEqual([], missing, "a watcher is genuinely unreadable on this tree: %r" % missing)
        code = "\n".join(HM._code_only(self.real_read(w)) for w in HM.WATCHERS)
        for name, _label in HM.PAGES:
            ids, seen = pages[name]["ids"], pages[name]["seen"]
            self.assertIsNotNone(ids)
            alt = sorted(i for i in ids if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(i), code))
            self.assertEqual(alt, seen, "%s: the map and an independent whole-name reading disagree" % name)
        console = pages["control_ui.html"]["seen"]
        named_in_code = re.search(r"(?<![\w-])heart-chip(?![\w-])", code) is not None
        self.assertEqual(named_in_code, "heart-chip" in console,
                         "heart-chip is %s the console's watched list while the watchers' code %s it"
                         % ("in" if "heart-chip" in console else "not in", "names" if named_in_code else "does not name"))
        self.assertGreater(len(pages["control_ui.html"]["ids"]), 100)


RED_PROOF = [
    {
        "why": "REG-1555 - comments are read as code again: a surface a comment names counts as watched",
        "file": "heart_map.py",
        "find": "        if t.type == tokenize.COMMENT:\n            spans.append((t.start, t.end))\n",
        "replace": "        if t.type == tokenize.COMMENT:\n            pass\n",
        "matches": 1,
    },
    {
        "why": "REG-1555 - docstrings are read as code again: a surface a docstring names counts as watched",
        "file": "heart_map.py",
        "find": "        elif t.type == tokenize.STRING and t.start[0] in doc_lines:\n            spans.append((t.start, t.end))\n",
        "replace": "        elif t.type == tokenize.STRING and t.start[0] in doc_lines:\n            pass\n",
        "matches": 1,
    },
    {
        "why": "REG-1555 - the substring match is back: th-shelf-x vouches for th-shelf",
        "file": "heart_map.py",
        "find": "    names = set(_NAME_RX.findall(blob))\n    return sorted(i for i in ids if i in names)\n",
        "replace": "    return sorted(i for i in ids if i in blob)\n",
        "matches": 1,
    },
    {
        "why": "REG-1555 - a watcher that does not parse is read as prose instead of named MISSING",
        "file": "heart_map.py",
        "find": "        c = None if t is None else _code_only(t)\n        if c is None:\n",
        "replace": "        c = None if t is None else (_code_only(t) if _code_only(t) is not None else t)\n        if c is None:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
