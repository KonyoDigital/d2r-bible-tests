# -*- coding: utf-8 -*-
"""REG-1720 (#42 lever 2) - A GREEN SUITE RUN IS REUSED ONLY ON IDENTICAL BYTES.

MEASURED on v3556's landed push (17m16s): the two python suites took 10m26s of it, re-running a commit that had already
passed them. tv/suite_verdict.py lets a push reuse a GREEN run of the same suite over the same commit tree. This law
drives the real module against a throwaway git repository (never his tree) and holds every condition a reuse needs:
  * the key is the commit's tree, and a working tree whose tracked files moved has NO key (the run's own records aside)
  * two checkouts of one commit share the key (a run in the signin worktree serves the push from main)
  * only a GREEN run is stored; a red run, another commit, another python, a stale run, an unageable run - no reuse
  * SUITE_VERDICT_REUSE=0 closes it; a run of the same bytes still in flight is waited for, and a dead one is not
  * the pre-push hook asks before each heavy suite and records its own green run after
RED_PROOF below.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

import suite_verdict as SV  # noqa: E402


def _git(cwd, *args):
    return subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True, text=True, check=True).stdout


def _repo():
    d = tempfile.mkdtemp(prefix="suite_verdict_")
    _git(d, "init", "-q")
    _git(d, "config", "user.email", "t@t")
    _git(d, "config", "user.name", "t")
    os.makedirs(os.path.join(d, "tv"))
    for name, body in (("tv/a.py", "x = 1\n"), ("tv/.self_arming.jsonl", "{}\n")):
        with io.open(os.path.join(d, name), "w", encoding="utf-8") as fh:
            fh.write(body)
    _git(d, "add", "-A")
    _git(d, "commit", "-q", "-m", "one")
    return d


class TheKeyIsTheCommitsBytes(unittest.TestCase):

    def setUp(self):
        self.d = _repo()
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_a_clean_tree_has_the_commits_tree_as_its_key(self):
        key, why = SV.tree_key(self.d)
        tree = _git(self.d, "rev-parse", "HEAD^{tree}").strip()
        self.assertTrue(key and key.startswith(tree + "|"), (key, why))
        self.assertIn(SV.env_key(), key, "the key does not carry the python it was measured on")

    def test_a_moved_tracked_file_has_no_key(self):
        with io.open(os.path.join(self.d, "tv", "a.py"), "a", encoding="utf-8") as fh:
            fh.write("y = 2\n")
        key, why = SV.tree_key(self.d)
        self.assertIsNone(key, "a working tree that is not the commit was given the commit's verdict")
        self.assertIn("tv/a.py", why)

    def test_the_runs_own_record_does_not_move_the_key(self):
        before, _ = SV.tree_key(self.d)
        with io.open(os.path.join(self.d, "tv", ".self_arming.jsonl"), "a", encoding="utf-8") as fh:
            fh.write('{"ran": 1}\n')
        after, why = SV.tree_key(self.d)
        self.assertEqual(before, after, why)

    def test_two_checkouts_of_one_commit_share_the_key_and_the_store(self):
        wt = tempfile.mkdtemp(prefix="suite_verdict_wt_")
        os.rmdir(wt)
        _git(self.d, "worktree", "add", "-q", wt)
        self.addCleanup(shutil.rmtree, wt, True)
        self.assertEqual(SV.tree_key(self.d)[0], SV.tree_key(wt)[0])
        self.assertEqual(os.path.realpath(SV.store_path(self.d)), os.path.realpath(SV.store_path(wt)),
                         "a run in one worktree cannot serve a push from the other")


class OnlyAGreenYoungRunOfTheseBytesIsReused(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="suite_store_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = os.path.join(self.tmp, "suite_verdicts.json")
        self.key = "tree123|" + SV.env_key()

    def test_a_green_run_is_reused(self):
        self.assertTrue(SV.record("test_control", self.key, True, cases=2259, seconds=600, path=self.path))
        r, why = SV.reusable("test_control", self.key, path=self.path)
        self.assertIsNotNone(r, why)
        self.assertEqual(r["cases"], 2259)

    def test_a_red_run_is_never_stored(self):
        self.assertFalse(SV.record("test_control", self.key, False, path=self.path))
        self.assertIsNone(SV.reusable("test_control", self.key, path=self.path)[0])

    def test_another_commit_or_suite_or_python_is_not_reused(self):
        SV.record("test_control", self.key, True, path=self.path)
        self.assertIsNone(SV.reusable("test_control", "tree999|" + SV.env_key(), path=self.path)[0])
        self.assertIsNone(SV.reusable("test_agent", self.key, path=self.path)[0])
        self.assertIsNone(SV.reusable("test_control", "tree123|py2.7-other", path=self.path)[0])

    def test_a_stale_or_unageable_run_is_not_reused(self):
        SV.record("test_control", self.key, True, path=self.path, now=1000.0)
        self.assertIsNone(SV.reusable("test_control", self.key, path=self.path, now=1000.0 + SV.MAX_AGE_S + 1)[0])
        self.assertIsNotNone(SV.reusable("test_control", self.key, path=self.path, now=1000.0 + 60)[0])
        with io.open(self.path, "w", encoding="utf-8") as fh:
            json.dump({"runs": [{"suite": "test_control", "key": self.key, "ok": True, "at": "yesterday"}]}, fh)
        self.assertIsNone(SV.reusable("test_control", self.key, path=self.path)[0])

    def test_an_unreadable_store_is_unknown_never_empty(self):
        """CI's swallow ratchet on 86e2b3da: a store that failed to read answered {} - 'no runs' - like a real empty"""
        SV.record("test_control", self.key, True, path=self.path)
        with io.open(self.path, "w", encoding="utf-8") as fh:
            fh.write("{ not json")
        r, why = SV.reusable("test_control", self.key, path=self.path)
        self.assertIsNone(r)
        self.assertIn("could not be read", why)
        self.assertTrue(SV.record("test_control", self.key, True, path=self.path), "a corrupt cache blocked a new run")
        self.assertIsNotNone(SV.reusable("test_control", self.key, path=self.path)[0])

    def test_the_switch_closes_it(self):
        SV.record("test_control", self.key, True, path=self.path)
        with mock.patch.dict(os.environ, {"SUITE_VERDICT_REUSE": "0"}):
            r, why = SV.reusable("test_control", self.key, path=self.path)
        self.assertIsNone(r)
        self.assertIn("SUITE_VERDICT_REUSE=0", why)


class ARunInFlightIsWaitedFor(unittest.TestCase):

    def setUp(self):
        self.d = _repo()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.key = SV.tree_key(self.d)[0]
        self.path = SV.store_path(self.d)

    def test_a_dead_runner_is_not_in_flight(self):
        SV._inflight_set("test_control", self.key, 999999, self.path)
        self.assertIsNone(SV.inflight("test_control", self.key, path=self.path))

    def test_the_check_waits_for_a_live_run_and_reuses_its_green(self):
        SV._inflight_set("test_control", self.key, os.getpid(), self.path)

        def finish():
            time.sleep(0.3)
            SV.record("test_control", self.key, True, cases=5, seconds=1, path=self.path)
        threading.Thread(target=finish).start()
        real_sleep = time.sleep
        with mock.patch.object(SV.time, "sleep", lambda s: real_sleep(0.05)):
            ok, line = SV.check("test_control", wait_s=30, cwd=self.d)
        self.assertTrue(ok, line)
        self.assertIn("REUSED", line)
        self.assertIn("CI still runs it in full", line)

    def test_no_run_and_no_flight_means_run_it(self):
        ok, line = SV.check("test_control", wait_s=0, cwd=self.d)
        self.assertFalse(ok)
        self.assertIn("runs", line)


class ThePushAsksBeforeEachHeavySuite(unittest.TestCase):

    def setUp(self):
        with io.open(os.path.join(os.path.dirname(HERE), "hooks", "pre-push"), encoding="utf-8") as fh:
            raw = fh.read()
        self.code = "\n".join(re.sub(r"(^|\s)#.*$", "", l) for l in raw.split("\n"))

    def test_each_heavy_suite_is_asked_then_run_then_recorded(self):
        for name, wait in (("test_agent", 900), ("test_control", 1500)):
            ask = 'python3 "$REPO/tv/suite_verdict.py" --check %s --wait %d' % (name, wait)
            run = 'gate_run "%s" "python3 tv/%s.py"' % (name, name)
            rec = 'python3 "$REPO/tv/suite_verdict.py" --record %s' % name
            for part in (ask, run, rec):
                self.assertEqual(self.code.count(part), 1, "%s: %r" % (name, part))
            self.assertLess(self.code.index(ask), self.code.index(run), "%s runs before it asks" % name)
            self.assertLess(self.code.index(run), self.code.index(rec), "%s records before it ran" % name)


RED_PROOF = [
    {
        "why": "REG-1720 - an unreadable verdict store reads as an empty one again (the swallow CI caught on 86e2b3da)",
        "file": "suite_verdict.py",
        "find": "    if store is None:\n        return None, \"the verdict store exists and could not be read - UNKNOWN, so the suite runs\"\n",
        "replace": "    if store is None:\n        store = {}\n",
        "matches": 1,
    },
    {
        "why": "REG-1720 - a working tree whose tracked files moved is graded by the commit's green run",
        "file": "suite_verdict.py",
        "find": "    if moved:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-1720 - a red run is stored and reused as a pass",
        "file": "suite_verdict.py",
        "find": "    if not (path and key and ok is True and name in SUITES):\n",
        "replace": "    if not (path and key and name in SUITES):\n",
        "matches": 1,
    },
    {
        "why": "REG-1720 - a verdict of any age is reused: a suite with clocks in it keeps an old pass for ever",
        "file": "suite_verdict.py",
        "find": "        if now - at > limit or now - at < -60:\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-1720 - the key forgets the python it was measured on",
        "file": "suite_verdict.py",
        "find": "    return \"%s|%s\" % (tree.strip(), env_key()), \"the commit's tree, unchanged\"\n",
        "replace": "    return tree.strip(), \"the commit's tree, unchanged\"\n",
        "matches": 1,
    },
    {
        "why": "REG-1720 - SUITE_VERDICT_REUSE=0 no longer closes the reuse",
        "file": "suite_verdict.py",
        "find": "    if os.environ.get(\"SUITE_VERDICT_REUSE\", \"1\") == \"0\":\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
