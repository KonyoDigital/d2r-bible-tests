# -*- coding: utf-8 -*-
"""#48 (REG-2453) - THE "SECOND EYE ASKED TWICE" ROW READS THE LEDGER ONCE, AND STILL SEES A NEW ROW.

MEASURED 2026-10-22 on a COPY of his 7.3 MB, 2,274-row ledger: console_doctor's row asks current_version, agreement(v)
and agreement_census(), and the census asks agreement() once per recent asked-twice version - each of which re-read and
re-parsed the WHOLE file. 43 parses a tick: the census alone 3.96 s profiled, 6-11 s on a loaded Mac (REG-1990's 1.8 s
on a quiet one). After: one parse on the first tick, none on the next while the ledger has not moved, and the census
output byte-identical to the old walk's (compared on the same copy). This law drives the REAL row on a FIXTURE ledger:

  1. one tick parses the ledger once; a second tick parses it zero times and answers the same;
  2. a row appended to the ledger is seen on the very next tick (a new signature is a new parse);
  3. a file written in the last SETTLE_S is never served from memory: rewritten in place to the same size with its old
     mtime put back (the coarse-clock case), the next read still sees the new bytes;
  4. the census is walked once per ledger state, and the copy handed back cannot edit the kept one.
Nothing of his is read: the ledger is this law's own file, the row's version is the fixture's. RED_PROOF below.
"""
import io
import json
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402  (the docstrings carry non-ASCII)
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import second_eye_ledger as L  # noqa: E402
import console_doctor as cd  # noqa: E402


def _row(version, ts, model, verdict="clean"):
    return {"version": version, "model": model, "verdict": verdict, "reached": True,
            "answerHead": "a look at %s" % version, "ts": ts}


class TheSecondEyeRowReadsTheLedgerOnce(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="se-once-")
        self.path = os.path.join(self.d, "ledger.jsonl")
        rows = [_row("v9100", 1000, "grok-4-1-fast-reasoning"), _row("v9100", 2000, "grok-4-1-fast-reasoning"),
                _row("v9101", 3000, "grok-4-1-fast-reasoning")]
        with io.open(self.path, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        self._age()
        p = mock.patch.object(L, "LEDGER_PATH", self.path)
        p.start()
        self.addCleanup(p.stop)
        self.version = "v9101"
        cv = mock.patch.object(L, "current_version", lambda *a, **k: self.version)
        cv.start()
        self.addCleanup(cv.stop)
        self.parses = []
        real = L._parse_ledger
        pl = mock.patch.object(L, "_parse_ledger", lambda path: (self.parses.append(path), real(path))[1])
        pl.start()
        self.addCleanup(pl.stop)

    def _age(self, path=None, at=None):
        t = time.time() - 3600 if at is None else at
        os.utime(path or self.path, (t, t))          # settled: its signature may stand for its bytes

    def _tick(self):
        del self.parses[:]
        state, say = cd._check_the_second_eye_was_asked_twice()
        return state, say, len(self.parses)

    # 1 ---------------------------------------------------------------------------------------------------------------
    def test_one_tick_parses_once_and_the_next_tick_not_at_all(self):
        s1, say1, n1 = self._tick()
        self.assertEqual(n1, 1, "one tick of the row parsed the ledger %d times - agreement() and every census "
                                "question re-read the whole file" % n1)
        s2, say2, n2 = self._tick()
        self.assertEqual(n2, 0, "a second tick over an unchanged ledger parsed it %d more time(s)" % n2)
        self.assertEqual((s1, say1), (s2, say2), "the kept parse answered differently from the fresh one")

    # 2 ---------------------------------------------------------------------------------------------------------------
    def test_an_appended_row_is_seen_on_the_next_tick(self):
        s1, say1, _n = self._tick()
        self.assertIn("ONCE", say1, "PREMISE: v9101 starts as a single look: %r" % say1)
        with io.open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(_row("v9101", 4000, "gpt-5", verdict="clean")) + "\n")
        self._age()
        s2, say2, n2 = self._tick()
        self.assertEqual(n2, 1, "the appended ledger was not parsed again (%d parses) - a stale answer" % n2)
        self.assertIn("AGREE", say2, "the row did not see the appended second look: %r" % say2)
        self.assertEqual(s2, cd.OK, "two identifiable families agreeing must read OK: %r %r" % (s2, say2))

    # 3 ---------------------------------------------------------------------------------------------------------------
    def test_a_file_written_just_now_is_never_served_from_memory(self):
        fresh = os.path.join(self.d, "fresh.jsonl")
        one = json.dumps(_row("v9200", 1000, "grok-4-1-fast-reasoning", verdict="clean")) + "\n"
        two = json.dumps(_row("v9200", 1000, "grok-4-1-fast-reasoning", verdict="dirty")) + "\n"
        self.assertEqual(len(one), len(two), "PREMISE: the two writes are the same size")
        with io.open(fresh, "w", encoding="utf-8") as fh:
            fh.write(one)
        st = os.stat(fresh)
        self.assertEqual(L._rows(fresh)[0]["verdict"], "clean")
        with io.open(fresh, "r+", encoding="utf-8") as fh:  # same inode, same size, and the old mtime put back
            fh.write(two)
        os.utime(fresh, ns=(st.st_atime_ns, st.st_mtime_ns))
        self.assertEqual(L._sig(fresh), (st.st_size, st.st_mtime_ns, st.st_ino, st.st_dev),
                         "PREMISE: the rewrite kept the signature (the coarse-clock case)")
        self.assertEqual(L._rows(fresh)[0]["verdict"], "dirty",
                         "a file written moments ago was served from memory: two writes a coarse clock gave one "
                         "mtime read as the first")

    # 4 ---------------------------------------------------------------------------------------------------------------
    def test_the_census_is_walked_once_per_ledger_state_and_handed_back_as_a_copy(self):
        walks = []
        real = L._census_walk
        with mock.patch.object(L, "_census_walk", lambda *a, **k: (walks.append(1), real(*a, **k))[1]):
            c1 = L.agreement_census()
            c1["say"] = "edited by a caller"
            c2 = L.agreement_census()
        self.assertEqual(len(walks), 1, "the census walked the ledger %d times over one unchanged state" % len(walks))
        self.assertNotEqual(c2["say"], "edited by a caller", "a caller's edit reached the kept census")


RED_PROOF = [
    {"why": "#48 - the memo is served whatever the file's signature says: an appended look is never seen and the row "
            "answers about a ledger that no longer exists",
     "file": "second_eye_ledger.py",
     "find": "    if hit is not None and hit[\"sig\"] == sig:\n        return hit\n",
     "replace": "    if hit is not None:\n        return hit\n",
     "matches": 1},
    {"why": "#48 - the parse is never kept: every question re-reads the whole 7.3 MB ledger again (43 parses a tick)",
     "file": "second_eye_ledger.py",
     "find": "        _PARSED[p] = state\n",
     "replace": "        pass\n",
     "matches": 1},
    {"why": "#48 - a file written moments ago is trusted by its signature: two same-size writes a coarse clock gave one "
            "mtime read as the first",
     "file": "second_eye_ledger.py",
     "find": "    return sig is not None and (time.time_ns() - sig[1]) >= SETTLE_S * 1e9\n",
     "replace": "    return sig is not None\n",
     "matches": 1},
    {"why": "#48 - the census is walked on every tick again (one agreement() per recent version each time)",
     "file": "second_eye_ledger.py",
     "find": "        if hit is not None and hit[0] == st[\"sig\"]:\n            return copy.deepcopy(hit[1])\n",
     "replace": "        if False:\n            return copy.deepcopy(hit[1])\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
