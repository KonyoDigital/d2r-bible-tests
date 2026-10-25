# -*- coding: utf-8 -*-
"""THE CONSOLE'S WEBKIT LOCALSTORAGE WAL IS PRUNED, AND A GROWING ONE IS NEVER SILENT.

Konyo 2026-10-25: "not only shrink it it needs a automatic pruning there too" - his Mac's
localstorage.sqlite3-wal reached 26 GB. ls_wal_guard runs before the WebView exists.

  · DRIVEN: an over-threshold WAL nobody holds is checkpointed to zero bytes, integrity ok.
  · DRIVEN: every row survives the truncate (read back through a fresh connection).
  · DRIVEN: a WAL some process holds is SKIPPED, its size untouched, and the holder REPORTED.
  · DRIVEN: holders that cannot be read are UNKNOWN - skipped, never treated as free.
  · DRIVEN: off macOS it is a no-op, even over a huge WAL.
  · DRIVEN: the 30-min look only ever PASSIVE-checkpoints a held db (never shrinks it under
    WebKit), and publishes the over-threshold warning that /api/status carries as lsWal.
  · WIRED: control_app --open calls startup_prune before the window and status carries lsWal.

Temp sqlite fixtures only; lsof is a seam. Nothing touches his Mac. RED_PROOF below.
"""
import os
import sqlite3
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import ls_wal_guard as g  # noqa: E402

THRESH = 64 * 1024
ROWS = 400


def _lsof(rc, out="", err="", raises=False):
    def run(argv, **_k):
        if raises:
            raise FileNotFoundError("lsof")
        if argv[0] == "ps":
            return types.SimpleNamespace(returncode=0, stdout="1-07:00:00 com.apple.WebKit.Networking", stderr="")
        return types.SimpleNamespace(returncode=rc, stdout=out, stderr=err)
    return run


FREE = _lsof(1)
HELD = _lsof(0, "4242\n")
UNREAD = _lsof(0, raises=True)


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = os.path.join(self.tmp.name, "WebsiteData", "Default", "h1", "h2", "LocalStorage")
        os.makedirs(d)
        self.root = os.path.join(self.tmp.name, "WebsiteData")
        self.db = os.path.join(d, "localstorage.sqlite3")
        # the writer stays open, like WebKit: closing it would checkpoint and remove the WAL itself
        self.w = sqlite3.connect(self.db)
        self.w.execute("PRAGMA journal_mode=WAL")
        self.w.execute("PRAGMA wal_autocheckpoint=0")
        self.w.execute("CREATE TABLE ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE PRIMARY KEY, value BLOB)")
        for i in range(ROWS):
            self.w.execute("INSERT INTO ItemTable VALUES (?, ?)", ("k%d" % i, os.urandom(1024)))
        self.w.commit()
        self.logs = []

    def tearDown(self):
        self.w.close()
        self.tmp.cleanup()

    def wal(self):
        return os.path.getsize(self.db + "-wal")

    def prune(self, run, platform="darwin"):
        return g.startup_prune(roots=[self.root], platform=platform, threshold=THRESH,
                               run=run, log=self.logs.append)


class TestStartupPrune(Fixture):
    def test_a_big_unheld_wal_is_truncated(self):
        before = self.wal()
        self.assertGreater(before, THRESH)
        res = self.prune(FREE)
        self.assertEqual(res[0]["action"], "truncated", res)
        self.assertEqual(self.wal(), 0)
        self.assertEqual(res[0]["integrity"], "ok")
        self.assertEqual(res[0]["walBefore"], before)
        self.assertTrue(any("TRUNCATE" in m for m in self.logs), self.logs)

    def test_the_data_survives(self):
        want = dict(self.w.execute("SELECT key, value FROM ItemTable"))
        self.prune(FREE)
        fresh = sqlite3.connect(self.db)
        try:
            self.assertEqual(dict(fresh.execute("SELECT key, value FROM ItemTable")), want)
            self.assertEqual(len(want), ROWS)
        finally:
            fresh.close()
        self.assertTrue(os.path.exists(self.db))

    def test_a_held_wal_is_skipped_and_its_holder_reported(self):
        before = self.wal()
        res = self.prune(HELD)
        self.assertEqual(res[0]["action"], "skipped-held")
        self.assertEqual(self.wal(), before)
        self.assertIn(4242, res[0]["leftover"])
        self.assertTrue(any("LEFTOVER" in m and "not killed" in m for m in self.logs), self.logs)

    def test_unreadable_holders_are_not_free(self):
        before = self.wal()
        res = self.prune(UNREAD)
        self.assertEqual(res[0]["action"], "skipped-unknown-holders")
        self.assertEqual(self.wal(), before)

    def test_off_mac_it_is_a_noop(self):
        before = self.wal()
        self.assertEqual(self.prune(FREE, platform="linux"), [])
        self.assertEqual(self.prune(FREE, platform="win32"), [])
        self.assertEqual(self.wal(), before)

    def test_a_small_wal_is_left_alone(self):
        before = self.wal()
        res = g.startup_prune(roots=[self.root], platform="darwin", threshold=before + 1,
                              run=FREE, log=self.logs.append)
        self.assertEqual(res[0]["action"], "none")
        self.assertEqual(self.wal(), before)


class TestPeriodic(Fixture):
    def test_a_held_db_is_never_shrunk_and_the_warning_is_published(self):
        before = self.wal()
        st = g.periodic_check(roots=[self.root], platform="darwin", threshold=THRESH,
                              log=self.logs.append, state={})
        self.assertEqual(self.wal(), before)       # PASSIVE only - never truncated under WebKit
        self.assertTrue(st["over"])
        self.assertEqual(st["walBytes"], before)
        self.assertIn("WAL", st["warning"])

    def test_under_threshold_has_no_warning(self):
        st = g.periodic_check(roots=[self.root], platform="darwin", threshold=self.wal() + 1,
                              log=self.logs.append, state={})
        self.assertFalse(st["over"])
        self.assertIsNone(st["warning"])

    def test_off_mac_says_it_does_not_apply(self):
        st = g.periodic_check(roots=[self.root], platform="linux", state={})
        self.assertIs(st["applies"], False)


class TestWiring(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as f:
            self.src = f.read()

    def test_open_runs_the_prune_before_the_window(self):
        i = self.src.index("_lswal.startup_prune()")
        j = self.src.index("        open_control_window()\n        _park_until_a_real_exit()")
        self.assertLess(i, j)
        self.assertIn('target=_lswal.loop, daemon=True, name="tvd-lswal"', self.src)

    def test_status_carries_lswal(self):
        self.assertIn('_out["lsWal"] = dict(_lswal.STATE)', self.src)

    def test_home_is_never_literal(self):
        with open(os.path.join(HERE, "ls_wal_guard.py"), encoding="utf-8") as f:
            self.assertNotIn("/Users/", f.read())


RED_PROOF = [
    {"why": "an over-threshold WAL is only PASSIVE-checkpointed at startup - it never shrinks",
     "file": "ls_wal_guard.py",
     "find": '                busy, _n, _c, integ = checkpoint(db, "TRUNCATE")\n',
     "replace": '                busy, _n, _c, integ = checkpoint(db, "PASSIVE")\n',
     "matches": 1},
    {"why": "a held WAL is truncated anyway",
     "file": "ls_wal_guard.py",
     "find": "        elif held:\n",
     "replace": "        elif False:\n",
     "matches": 1},
    {"why": "unreadable holders are read as nobody",
     "file": "ls_wal_guard.py",
     "find": "    except Exception:\n        return None\n",
     "replace": "    except Exception:\n        return set()\n",
     "matches": 1},
    {"why": "the guard runs off macOS",
     "file": "ls_wal_guard.py",
     "find": '    return (platform or sys.platform) == "darwin"\n',
     "replace": "    return True\n",
     "matches": 1},
    {"why": "the WAL is cut by truncating the file instead of checkpointing - the rows are lost",
     "file": "ls_wal_guard.py",
     "find": '                busy, _n, _c, integ = checkpoint(db, "TRUNCATE")\n',
     "replace": '                os.truncate(wal, 0); busy, integ = 0, "ok"\n',
     "matches": 1},
    {"why": "the 30-min look truncates under a live WebKit",
     "file": "ls_wal_guard.py",
     "find": '                checkpoint(db, "PASSIVE")\n',
     "replace": '                checkpoint(db, "TRUNCATE")\n',
     "matches": 1},
    {"why": "status stops carrying lsWal - silent again",
     "file": "control_app.py",
     "find": '        _out["lsWal"] = dict(_lswal.STATE)\n',
     "replace": "        pass\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
