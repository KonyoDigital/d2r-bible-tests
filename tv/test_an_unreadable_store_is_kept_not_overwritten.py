# -*- coding: utf-8 -*-
"""R4 (REG-2341) - A STORE THAT WILL NOT READ IS KEPT, NEVER WRITTEN OVER, AND NO WRITE THINS WHAT IT HELD.

FOUND in the v1 writers (read 2026-10-21): an unreadable verdict cache was read as empty and rewritten by the first
PROVEN, and a flush whose merge-read failed (its `_dwhy` ignored) wrote that run's entries alone - one bad read and main's
7,991 entries would have become a handful. Now every write keeps
the store's last good generation as `.prev`; a store that will not read is renamed aside (`.unreadable-<ms>`, the newest
one kept), and `.prev` stands in for it - at the open and at the write. Driven on fixtures:

  1. the cache, unreadable at the OPEN: said, its .prev serves lookups, and the first write keeps the bad bytes aside
     byte for byte while writing .prev's entries plus the new one;
  2. the cache, turned unreadable AFTER the open (the failed merge-read): the write keeps it aside and merges .prev - the
     entries another prover banked are still there;
  3. only the newest unreadable generation is kept.
EVERYTHING HERE IS A FIXTURE. RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402  (its docstrings carry non-ASCII)
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

GARBAGE = '{"entries": {"half a write'


def _entry(t):
    return {"verdict": H.PROVEN, "provedAt": t, "gate": "g", "proof": t}


class AnUnreadableStoreIsKeptNotOverwritten(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="h2aside.")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.path = os.path.join(self.dir, ".heart2_cache.json")
        self.said = []

    def asides(self, base=".heart2_cache.json"):
        return sorted(n for n in _fx_tmp.list_own(self.dir) if n.startswith(base + ".unreadable-"))

    def entries(self):
        with io.open(self.path, encoding="utf-8") as fh:
            return json.load(fh)["entries"]

    def bank(self, key, t):
        c = H._VerdictCache(path=self.path, say=self.said.append)
        c.store(key, _entry(t))
        self.assertTrue(c.flush(), "PREMISE: a write failed: %s" % self.said[-3:])
        return c

    def test_unreadable_at_the_open_its_prev_stands_in_and_the_bad_bytes_are_kept(self):
        """★ said at the open; .prev's entries are served; the first write sets the bad bytes aside UNCHANGED and
        writes .prev's entries plus the new one - nothing shrank"""
        self.bank("k1", 1)
        self.bank("k2", 2)                       # k1 + k2 on disk, k1 alone in .prev
        with io.open(self.path, "w", encoding="utf-8") as fh:
            fh.write(GARBAGE)
        c = H._VerdictCache(path=self.path, say=self.said.append)
        self.assertTrue(any("UNREADABLE" in l and "would not parse" in l and ".prev" in l for l in self.said),
                        "the unreadable store was not said, or its .prev was not named: %s" % self.said[-2:])
        self.assertIsNotNone(c.lookup("k1"), "the last good generation (.prev) did not stand in at the open")
        c.store("k3", _entry(3))
        self.assertTrue(c.flush(), "the write over an unreadable store failed: %s" % self.said[-3:])
        self.assertEqual(sorted(self.entries()), ["k1", "k3"], "the write did not merge .prev's entries in")
        kept = self.asides()
        self.assertEqual(len(kept), 1, "the unreadable bytes were not kept aside: %s" % _fx_tmp.list_own(self.dir))
        with io.open(os.path.join(self.dir, kept[0]), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), GARBAGE, "the bytes kept aside are not the unreadable store's")

    def test_a_failed_merge_read_never_thins_the_store(self):
        """★ the store read fine at the OPEN and turned unreadable before the write (another writer's torn file): the
        write keeps it aside and merges .prev, so what another prover banked is still there"""
        self.bank("k1", 1)
        self.bank("k2", 2)
        c = H._VerdictCache(path=self.path, say=self.said.append)       # opened while readable: k1 + k2
        self.bank("k3", 3)                                              # another prover: k1 + k2 + k3, .prev k1 + k2
        with io.open(self.path, "w", encoding="utf-8") as fh:
            fh.write(GARBAGE)
        c.entries.pop("k1", None)               # this run never held k1 - only the disk did
        c.store("k4", _entry(4))
        self.assertTrue(c.flush(), self.said[-3:])
        got = sorted(self.entries())
        self.assertIn("k1", got, "a failed merge-read thinned the store: .prev's entries were not merged (%s)" % got)
        self.assertIn("k4", got)
        self.assertEqual(len(self.asides()), 1, "the unreadable store was written over, not kept aside")

    def test_only_the_newest_unreadable_generation_is_kept(self):
        """★ two bad files in a row: one aside remains, and it holds the newer bad bytes"""
        self.bank("k1", 1)
        for n, junk in enumerate(("{first", "{second")):
            with io.open(self.path, "w", encoding="utf-8") as fh:
                fh.write(junk)
            time.sleep(0.01)
            self.bank("n%d" % n, 10 + n)
        kept = self.asides()
        self.assertEqual(len(kept), 1, "every unreadable generation was kept: %s" % kept)
        with io.open(os.path.join(self.dir, kept[0]), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "{second", "the aside kept is not the newest")



RED_PROOF = [
    {"why": "R4 - an unreadable store is not set aside: the next write overwrites the only copy of what it held",
     "file": "heart2.py",
     "find": "    try:\n        os.replace(path, aside)\n    except FileNotFoundError:\n",
     "replace": "    try:\n        pass\n    except FileNotFoundError:\n",
     "matches": 1},
    {"why": "R4 - the merge-read's failure is ignored (_dwhy): an unreadable disk reads as empty and the write thins it",
     "file": "heart2.py",
     "find": "        disk, why = _read_store(self.path, self.valid)\n        if why is not None:\n",
     "replace": "        disk, why = _read_store(self.path, self.valid)\n        if False:\n",
     "matches": 1},
    {"why": "R4 - the last good generation is not read at the open: an unreadable cache serves nothing it held",
     "file": "heart2.py",
     "find": "        prev = _load_cache(self.path + \".prev\")[0] if why and os.path.exists(self.path + \".prev\") else None\n",
     "replace": "        prev = None\n",
     "matches": 1},
    {"why": "R4 - no .prev generation is kept, so a store that goes bad has nothing to stand in for it",
     "file": "heart2.py",
     "find": "                    os.replace(self._tmp() + \".prev\", self.path + \".prev\")\n",
     "replace": "                    pass\n",
     "matches": 1},
    {"why": "R4 - every unreadable generation is kept, and repeated bad writes fill the disk",
     "file": "heart2.py",
     "find": "                os.remove(os.path.join(folder, n))      # keep ONE: the newest unreadable generation\n",
     "replace": "                pass\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
