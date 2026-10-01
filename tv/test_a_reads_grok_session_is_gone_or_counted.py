#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REG-1687 - A READ'S GROK SESSION DIRECTORY IS GONE, OR IT IS COUNTED - NEVER SILENTLY LEFT.

MEASURED on his ALT 2026-10-01: ~/.grok/sessions held 115 directories (86.6 MB) again - 76 from 09-30, 35 from 10-01 -
every one named after a G5 scene read's throwaway tvd-g5- cwd. REG-1549 had each read remove its own; the removal was
shutil.rmtree(ignore_errors=True), and on Windows a file grok still held (chat_history.jsonl.lock) cannot be deleted,
so it failed silently and the directory stayed. The class once filled his Mac's disk (11 GB, ENOSPC).

Driven through the REAL g5_grok_eyes._cleanup over a temp Grok home (never his):
  1. the read's own session directory is removed, retried while a lock holds it;
  2. a directory that still will not go is COUNTED (session_dirs_left), never pretended gone;
  3. every read also sweeps EARLIER reads' leftovers older than G5_SESSION_STALE_S - by the unique tvd-g5- name only:
     a concurrent read's fresh one and his own sessions are never touched.
RED_PROOF below.
"""
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import g5_grok_eyes as G  # noqa: E402


class _Home(unittest.TestCase):

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="g5_home_")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.sd = os.path.join(self.home, "sessions")
        os.makedirs(self.sd)
        self.work = tempfile.mkdtemp(prefix="tvd-g5-")
        self.addCleanup(shutil.rmtree, self.work, True)
        self.base = os.path.basename(self.work)
        for p in (mock.patch.object(G, "_real_grok_home", lambda: self.home),
                  mock.patch.object(G.time, "sleep", lambda s: None)):
            p.start()
            self.addCleanup(p.stop)
        self._stats = dict(G._STATS)
        self.addCleanup(lambda: (G._STATS.clear(), G._STATS.update(self._stats)))
        G._STATS.pop("session_dirs_left", None)
        G._STATS.pop("session_dirs_swept", None)

    def session(self, name, age_s=0):
        p = os.path.join(self.sd, name)
        os.makedirs(p)
        with open(os.path.join(p, "chat_history.jsonl.lock"), "w") as fh:
            fh.write("")
        if age_s:
            t = time.time() - age_s
            os.utime(p, (t, t))
        return p


class AReadsSessionIsGone(_Home):

    def test_the_reads_own_session_is_removed(self):
        mine = self.session("C%3A%5CTemp%5C" + self.base)
        G._cleanup(self.work)
        self.assertFalse(os.path.exists(mine), "the read left its own Grok session directory")

    def test_a_lock_that_lifts_is_waited_out(self):
        mine = self.session("C%3A%5CTemp%5C" + self.base)
        real, calls = shutil.rmtree, []

        def rmtree(path, ignore_errors=False, onerror=None):
            calls.append(path)
            if len(calls) < 3:
                return                  # Windows: the lock still held, nothing removed, nothing raised
            real(path, ignore_errors=True)
        with mock.patch.object(G.shutil, "rmtree", rmtree):
            G._cleanup(self.work)
        self.assertFalse(os.path.exists(mine), "one silent failed delete left the directory for ever")

    def test_a_directory_that_will_not_go_is_counted(self):
        mine = self.session("C%3A%5CTemp%5C" + self.base)
        with mock.patch.object(G.shutil, "rmtree", lambda path, ignore_errors=False, onerror=None: None):
            G._cleanup(self.work)
        self.assertTrue(os.path.exists(mine), "PREMISE: the stand-in lock did not hold")
        self.assertGreaterEqual(G._STATS.get("session_dirs_left") or 0, 1,
                                "a session directory that would not go was not counted - silence again")


class EarlierLeftoversAreSwept(_Home):

    def test_old_leftovers_go_fresh_and_his_own_stay(self):
        old = self.session("C%3A%5CTemp%5Ctvd-g5-oldread1", age_s=G.G5_SESSION_STALE_S + 60)
        fresh = self.session("C%3A%5CTemp%5Ctvd-g5-liveread", age_s=5)
        his = self.session("C%3A%5CUsers%5Chim%5Cproject", age_s=10 * 86400)
        home = self.session("C%3A%5CTemp%5Ctvd-g5-home", age_s=10 * 86400)
        G._cleanup(self.work)
        self.assertFalse(os.path.exists(old), "an earlier read's leftover was never swept")
        self.assertTrue(os.path.exists(fresh), "a concurrent read's fresh session was swept from under it")
        self.assertTrue(os.path.exists(his), "one of HIS own Grok sessions was removed")
        self.assertTrue(os.path.exists(home), "the lean home's own directory was treated as a read's leftover")
        self.assertEqual(G._STATS.get("session_dirs_swept"), 1)


RED_PROOF = [
    {"why": "REG-1687 - the read's own session directory is never removed",
     "file": "g5_grok_eyes.py",
     "find": "                    _drop_session_dir(os.path.join(sd, name))\n",
     "replace": "                    pass\n",
     "matches": 1},
    {"why": "REG-1687 - one silent failed delete is final again (no retry)",
     "file": "g5_grok_eyes.py",
     "find": "    for k in range(max(1, int(attempts))):\n",
     "replace": "    for k in range(1):\n",
     "matches": 1},
    {"why": "REG-1687 - a directory that will not go is not counted",
     "file": "g5_grok_eyes.py",
     "find": "    _STATS[\"session_dirs_left\"] = int(_STATS.get(\"session_dirs_left\") or 0) + 1\n",
     "replace": "    pass\n",
     "matches": 1},
    {"why": "REG-1687 - earlier reads' leftovers are never swept",
     "file": "g5_grok_eyes.py",
     "find": "            _sweep_stale_sessions(sd)\n",
     "replace": "            pass\n",
     "matches": 1},
    {"why": "REG-1687 - the sweep takes a concurrent read's fresh session",
     "file": "g5_grok_eyes.py",
     "find": "            if now - os.path.getmtime(p) < G5_SESSION_STALE_S:\n",
     "replace": "            if False:\n",
     "matches": 1},
    {"why": "REG-1687 - the sweep reaches beyond the reads' own tvd-g5- names",
     "file": "g5_grok_eyes.py",
     "find": "        if \"tvd-g5-\" not in name or \"tvd-g5-home\" in name:\n",
     "replace": "        if False:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
