# -*- coding: utf-8 -*-
"""A file this package could not READ must never be reported as a name that does not EXIST.

Found by the second eye on the SHIPPED v3151 diff, and it was damage from that ship's own fix.
v3151 memoised `_defined_anywhere` (it re-parsed every tv/*.py per NAME — 11.0s of a 12.7s
heart.vessels()). The cache key is built from os.stat BEFORE the parse loop, so a file that stats
and then fails to open was dropped from the set and that short set was stored as a finished answer.

⚠ WHAT THAT COSTS. `kind_of` returns FOREIGN — "not ours, stop watching" — only when
`_defined_anywhere` is False. An fd-exhausted console would cache an EMPTY set, classify every
dotted in-package target FOREIGN for the rest of the process, and the census would read complete
while the heart quietly stopped watching a real lane. No stat would move to let it recover.

The pre-v3151 code swallowed the same exception PER CALL, so a later census still saw the file.
Caching is what turned a transient failure permanent. [[unknown-stays-unknown]] [[stale-reading]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import lane_census as LC  # noqa: E402


class TestASkippedFileIsNeverAnAbsentName(unittest.TestCase):

    def setUp(self):
        self._real = LC._package_files
        self._cache = LC._DEFINED_CACHE

    def tearDown(self):
        LC._package_files = self._real
        LC._DEFINED_CACHE = self._cache

    def test_a_clean_read_is_complete_and_answers_precisely(self):
        LC._DEFINED_CACHE = {"key": None, "names": None}
        names, complete = LC._all_defined_names()
        self.assertTrue(complete, "a clean package read reported INCOMPLETE")
        self.assertTrue(names, "no names parsed at all — this law is reading the wrong package")
        self.assertTrue(LC._defined_anywhere("census"), "a name this package really defines")
        self.assertFalse(LC._defined_anywhere("zzz_no_such_function_zzz"),
                         "a name nothing defines must still be answerable as absent, or FOREIGN "
                         "can never be reached and the classification is dead")

    def test_an_unreadable_file_is_never_stored_as_a_finished_answer(self):
        """DRIVEN, because the live package reads fine every time — the defect only appears when
        a file cannot be opened, which no amount of watching a healthy tree will produce."""
        LC._DEFINED_CACHE = {"key": None, "names": None}
        LC._package_files = lambda: self._real() + [os.path.join(HERE, "zzz_unreadable_zzz.py")]
        names, complete = LC._all_defined_names()
        self.assertFalse(complete,
                         "a file that could not be opened was reported as a COMPLETE read")
        self.assertIsNone(
            LC._DEFINED_CACHE.get("names"),
            "the short set was CACHED. The stat key cannot move to invalidate it, so the next "
            "call is a hit and the missing file is never retried.")

    def test_an_incomplete_read_never_answers_ABSENT(self):
        """The whole point. False here means FOREIGN, and FOREIGN means stop watching."""
        LC._DEFINED_CACHE = {"key": None, "names": None}
        LC._package_files = lambda: [os.path.join(HERE, "zzz_unreadable_zzz.py")]
        self.assertTrue(
            LC._defined_anywhere("zzz_no_such_function_zzz"),
            "the package could not be read and the answer was still 'this name does not exist'. "
            "That retires a live lane on the strength of a failed open.")


    def test_a_file_that_will_not_PARSE_never_disables_the_cache(self):
        """The second eye's High on v3152. A parse failure is DETERMINISTIC for those bytes — the
        same file fails the same way forever, and fixing it moves its mtime — so it is a complete
        answer, not an unreadable one. Treating the two alike meant ONE saved syntax error in any
        tv/*.py (tests included) stopped the cache being written at all: the 11s heart.vessels()
        stall came back for the whole process, and FOREIGN could never fire, so `serve_forever`
        and `wait` would be taken for vessels to watch."""
        import shutil
        import tempfile
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)   # a law that leaks temp dirs is a law with a cost
        bad = os.path.join(d, "zz_broken.py")
        io.open(bad, "w", encoding="utf-8").write("def oops(:\n")
        LC._DEFINED_CACHE = {"key": None, "names": None}
        LC._package_files = lambda: self._real() + [bad]
        names, complete = LC._all_defined_names()
        self.assertTrue(complete,
                        "a file that will not PARSE was reported as an incomplete READ. That "
                        "stops the cache ever being written and brings the whole-package walk "
                        "back on every call.")
        self.assertIsNotNone(LC._DEFINED_CACHE.get("names"),
                             "the set was not cached, so the stall returns for the process")
        self.assertFalse(
            LC._defined_anywhere("zzz_no_such_function_zzz"),
            "FOREIGN became unreachable because one file would not parse — every dotted stdlib "
            "target then reads UNKNOWN and is taken for a vessel to watch")

    def test_a_NUL_byte_is_a_parse_failure_too(self):
        """The second eye on v3154. NUL is VALID UTF-8, so io.open succeeds and ast.parse raises
        ValueError — not SyntaxError, and not UnicodeDecodeError. Naming only the subclass let a
        NUL-bearing file fall to the broad handler and reinstate the whole-package stall."""
        import shutil
        import tempfile
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        bad = os.path.join(d, "zz_nul.py")
        io.open(bad, "w", encoding="utf-8").write("x = 1\x00\n")
        LC._DEFINED_CACHE = {"key": None, "names": None}
        LC._package_files = lambda: self._real() + [bad]
        _names, complete = LC._all_defined_names()
        self.assertTrue(complete,
                        "a NUL byte was treated as an unreadable file, so the cache is never "
                        "written and the whole-package walk returns on every call")
        self.assertIsNotNone(LC._DEFINED_CACHE.get("names"), "not cached — the stall is back")

RED_PROOF = [
    {
        "why": "folds a PARSE failure back into the unreadable path, so one saved syntax error in "
               "any tv/*.py stops the cache being written at all — the 11s heart.vessels() stall "
               "returns for the whole process and FOREIGN can never fire again",
        "file": "lane_census.py",
        "find": "        except (SyntaxError, ValueError):",
        "replace": "        except (ZeroDivisionError,):",
        "matches": 1,
    },

    {
        "why": "caches the set even when a file could not be opened, so a transient failure is "
               "frozen under a stat key that cannot move — an fd-exhausted console classifies "
               "every dotted in-package target FOREIGN for the rest of the process",
        "file": "lane_census.py",
        "find": "    if _complete:\n        globals()[\"_DEFINED_CACHE\"] = {\"key\": _key, \"names\": _names}   # ONE binding: threaded",
        "replace": "    globals()[\"_DEFINED_CACHE\"] = {\"key\": _key, \"names\": _names}",
        "matches": 1,
    },
    {
        "why": "answers ABSENT on a package it could not read, which is the False that becomes "
               "FOREIGN and stops the heart watching a real lane",
        "file": "lane_census.py",
        "find": "    return not _complete",
        "replace": "    return False",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
