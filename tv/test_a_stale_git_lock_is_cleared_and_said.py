#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#64 — AN ABANDONED GIT LOCK WEDGED EVERY PULL FOR ELEVEN HOURS, AND NOTHING READ THE FAILURE.

MEASURED 2026-09-29 on his ALT: `.git/index.lock` dated 2026-09-28 14:09, 0 bytes, no git process
running. Every automatic pull after that failed with "Unable to create ... index.lock: File exists",
so the ALT stayed on v3521 for 11 h. `_pull_once` RECORDED it in `_PULL.say` ("the fast-forward did
not succeed ... UNKNOWN, NOT up to date") — and no doctor row read `_PULL`, the fleet beacon said
"clear to pull" off a cached origin view, and nothing cleared the lock. His words for the class:
"the windows needs proper care and attention"; "make sure nothing is running on my pc for nothing".

THE LAWS, each on a REAL git fixture in a temp dir (never his checkout):
  · a stale lock (empty, older than the bar, no git running) is cleared and the pull LANDS, with a
    receipt on the lane's record; and git's own error naming the lock is a second trigger
  · a YOUNG lock, a NON-EMPTY lock, a RUNNING git, or a probe that cannot answer -> the lock is
    left untouched and the lane SAYS why
  · the doctor row 'this checkout can update' reads MISSING after failures past the bar (reason and
    since when), OK after a success or a deliberate stand-down, UNKNOWN when nobody tried
  · the row reads the lane OVER THE WIRE, and /api/status publishes it under the key the row reads
  · the fleet beacon's pull.why says the pulls are failing instead of "clear to pull"

⚠ The git-running probe is stubbed in the lock cases: a real `pgrep -x git` on his Mac answers
about whatever git HE is running, and a verdict that depends on his machine is not a law.
[[feedback-fixtures-never-touch-live-data]] [[the-unjoined-end]] [[unknown-stays-unknown]]
"""
import ast
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca          # noqa: E402
import console_doctor as cd       # noqa: E402

_PULL0 = dict(ca._PULL)

# git must not read his global/system config (pull.rebase, signing, hooks) inside the fixture
_GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0"}
_ID = ["-c", "user.name=law", "-c", "user.email=law@example.invalid", "-c", "commit.gpgsign=false"]


def _git(cwd, *args):
    r = subprocess.run(["git"] + _ID + list(args), cwd=cwd, capture_output=True, text=True,
                       timeout=30, env=dict(os.environ, **_GIT_ENV))
    if r.returncode != 0:
        raise AssertionError("fixture git %s failed: %s" % (" ".join(args), r.stderr.strip()[-200:]))
    return (r.stdout or "").strip()


def _fixture():
    """origin (bare) <- seed pushes 2 commits; clone holds only the first. -> (root, clone, origin_head)"""
    root = tempfile.mkdtemp(prefix="tvd-gitlock-")
    origin = os.path.join(root, "origin.git")
    seed = os.path.join(root, "seed")
    clone = os.path.join(root, "clone")
    _git(root, "-c", "init.defaultBranch=main", "init", "-q", "--bare", origin)
    _git(root, "-c", "init.defaultBranch=main", "init", "-q", seed)
    with open(os.path.join(seed, "f.txt"), "w") as fh:
        fh.write("one\n")
    _git(seed, "add", "f.txt")
    _git(seed, "commit", "-q", "-m", "one")
    _git(seed, "push", "-q", origin, "HEAD:refs/heads/main")
    _git(root, "clone", "-q", "--branch", "main", origin, clone)
    with open(os.path.join(seed, "f.txt"), "w") as fh:
        fh.write("two\n")
    _git(seed, "commit", "-q", "-am", "two")
    _git(seed, "push", "-q", origin, "HEAD:refs/heads/main")
    return root, clone, _git(seed, "rev-parse", "--short", "HEAD")


def _plant(clone, age_s, body=b""):
    lk = os.path.join(clone, ".git", "index.lock")
    with open(lk, "wb") as fh:
        fh.write(body)
    t = time.time() - age_s
    os.utime(lk, (t, t))
    return lk, int(t * 1000)


class _Base(unittest.TestCase):

    def setUp(self):
        self.root, self.clone, self.origin_head = _fixture()
        self._env = mock.patch.dict(os.environ, _GIT_ENV)
        self._env.start()
        os.environ.pop("TV_NO_AUTO_PULL", None)
        self._repo = mock.patch.object(ca, "REPO", self.clone)
        self._repo.start()
        ca._PULL.clear()
        ca._PULL.update(_PULL0)
        self.seen = []
        self._real_run = ca._git_run

        def _counting(argv, **kw):
            self.seen.append(" ".join(list(argv)[1:3]))
            return self._real_run(argv, **kw)
        self._run = mock.patch.object(ca, "_git_run", _counting)
        self._run.start()

    def tearDown(self):
        self._run.stop()
        self._repo.stop()
        self._env.stop()
        ca._PULL.clear()
        ca._PULL.update(_PULL0)
        shutil.rmtree(self.root, ignore_errors=True)

    def head(self):
        return _git(self.clone, "rev-parse", "--short", "HEAD")

    def probe(self, answer, how):
        return mock.patch.object(ca, "_git_running_here", lambda: (answer, how))


class TestAStaleLockIsClearedAndThePullLands(_Base):

    def test_BASELINE_the_fixture_reproduces_the_ALT(self):
        """Without this, every case below could pass on a fixture where a lock blocks nothing."""
        _plant(self.clone, 20 * 60)
        _git(self.clone, "fetch", "-q", "origin", "main")
        r = subprocess.run(["git", "merge", "--ff-only", "origin/main"], cwd=self.clone,
                           capture_output=True, text=True, timeout=30, env=dict(os.environ, **_GIT_ENV))
        self.assertNotEqual(r.returncode, 0, "a held index.lock did not block the fast-forward")
        self.assertIn("index.lock", r.stderr, "git's refusal does not name the lock: %r" % r.stderr)
        self.assertTrue(ca._names_index_lock(r))
        self.assertTrue(ca._git_err_line(r).lower().startswith("error:"),
                        "the reason picked is git's advice, not its error: %r" % ca._git_err_line(r))

    def test_a_stale_lock_is_cleared_and_the_pull_lands(self):
        lk, planted_ms = _plant(self.clone, 20 * 60)
        with self.probe(False, "stub: no git running"):
            out = ca._pull_once()
        self.assertIs(out, True, "the pull did not land: %r" % ca._PULL.get("say"))
        self.assertFalse(os.path.exists(lk), "the abandoned lock is still there")
        self.assertEqual(self.head(), self.origin_head, "HEAD did not reach origin/main")
        self.assertEqual(self.seen.count("merge --ff-only"), 1,
                         "the lock was cleared only AFTER a failed fast-forward (%s) — the check "
                         "before the fetch is not running" % self.seen)
        self.assertEqual(ca._PULL.get("outcome"), "pulled")
        self.assertIsNone(ca._PULL.get("failSince"))
        rec = ca._PULL.get("lockCleared") or {}
        self.assertIn("cleared a stale git lock", rec.get("say") or "", "no receipt: %r" % rec)
        self.assertEqual(rec.get("lockMtime"), planted_ms, "the receipt does not carry the lock's time")
        self.assertTrue(isinstance(rec.get("at"), int) and rec["at"] > planted_ms)
        self.assertIn("cleared a stale git lock", ca._PULL.get("say") or "",
                      "the lane's own sentence hides that it removed a lock")

    def test_a_lock_that_appears_AFTER_the_check_is_cleared_when_git_names_it(self):
        """The second trigger: git's own error naming index.lock (a lock left between the check and the merge)."""
        planted = {}
        real = self._real_run

        def _plant_at_merge(argv, **kw):
            key = " ".join(list(argv)[1:3])
            self.seen.append(key)
            if key == "merge --ff-only" and not planted:
                planted["lk"] = _plant(self.clone, 20 * 60)[0]
            return real(argv, **kw)
        with mock.patch.object(ca, "_git_run", _plant_at_merge), self.probe(False, "stub: none"):
            out = ca._pull_once()
        self.assertTrue(planted, "the fixture never planted its lock")
        self.assertIs(out, True, "the pull did not land: %r" % ca._PULL.get("say"))
        self.assertFalse(os.path.exists(planted["lk"]), "git named the lock and it was not cleared")
        self.assertEqual(self.seen.count("merge --ff-only"), 2, "expected one refused + one retried "
                         "fast-forward, saw %s" % self.seen)
        self.assertIn("cleared a stale git lock", (ca._PULL.get("lockCleared") or {}).get("say") or "")

    def test_the_in_app_update_door_clears_it_too(self):
        lk, _ = _plant(self.clone, 20 * 60)
        with self.probe(False, "stub: none"):
            out = ca.fleet_pull()
        self.assertTrue(out.get("ok") and out.get("pulled"), "the /api/update door did not pull: %r" % out)
        self.assertFalse(os.path.exists(lk))
        self.assertEqual(self.seen.count("pull --ff-only"), 1,
                         "the door cleared the lock only after a refused pull: %s" % self.seen)
        self.assertIn("cleared a stale git lock", out.get("lock") or "")
        self.assertIn("cleared a stale git lock", (ca._PULL.get("lockCleared") or {}).get("say") or "")


class TestAnyOtherLockIsLeftAndSaid(_Base):

    def _left(self, lk, body):
        self.assertTrue(os.path.exists(lk), "a lock this law must LEAVE was removed")
        with open(lk, "rb") as fh:
            self.assertEqual(fh.read(), body, "the lock's bytes changed")
        self.assertNotEqual(self.head(), self.origin_head, "HEAD moved past a lock that stayed")
        self.assertEqual(ca._PULL.get("outcome"), "failed")
        self.assertIsNone(ca._PULL.get("lockCleared"), "a receipt for a clearing that did not happen")
        return ca._PULL.get("say") or ""

    def test_a_YOUNG_lock_is_left_and_said(self):
        lk, _ = _plant(self.clone, 5)
        with self.probe(False, "stub: none"):
            self.assertIsNone(ca._pull_once())
            since = ca._PULL.get("failSince")
            self.assertIsNone(ca._pull_once())
        say = self._left(lk, b"")
        self.assertIn("left the git lock", say)
        self.assertIn("the bar is %ds" % ca._GIT_LOCK_STALE_S, say, "the age refusal is not said: %s" % say)
        self.assertEqual(ca._PULL.get("failures"), 2)
        self.assertEqual(ca._PULL.get("failSince"), since, "a second failure restarted the clock")
        self.assertIn("index.lock", ca._PULL.get("lastErr") or "", "the reason lost the lock")

    def test_a_NON_EMPTY_lock_is_left_and_said(self):
        lk, _ = _plant(self.clone, 20 * 60, b"0123456789")
        with self.probe(False, "stub: none"):
            self.assertIsNone(ca._pull_once())
        say = self._left(lk, b"0123456789")
        self.assertIn("holds 10 bytes", say, "the size refusal is not said: %s" % say)

    def test_a_RUNNING_git_leaves_the_lock(self):
        lk, _ = _plant(self.clone, 20 * 60)
        with self.probe(True, "stub: pgrep -x git found pid 4242"):
            self.assertIsNone(ca._pull_once())
        say = self._left(lk, b"")
        self.assertIn("a git process is running", say)
        self.assertIn("pid 4242", say, "the lane does not name what it saw running")

    def test_a_probe_that_CANNOT_ANSWER_leaves_the_lock(self):
        lk, _ = _plant(self.clone, 20 * 60)
        with self.probe(None, "stub: pgrep could not run"):
            self.assertIsNone(ca._pull_once())
        say = self._left(lk, b"")
        self.assertIn("could not be asked", say)


class TestTheRunningProbeAnswersThreeWays(unittest.TestCase):

    def test_pgrep_exit_codes_map_to_three_answers(self):
        class _R(object):
            def __init__(self, rc, out=""):
                self.returncode, self.stdout, self.stderr = rc, out, ""
        with mock.patch.object(ca, "IS_WIN", False):
            for rc, want in ((0, True), (1, False), (2, None)):
                with mock.patch.object(ca.subprocess, "run", lambda *a, **k: _R(rc, "4242\n")):
                    self.assertIs(ca._git_running_here()[0], want, "pgrep exit %d" % rc)

            def _boom(*a, **k):
                raise FileNotFoundError("pgrep")
            with mock.patch.object(ca.subprocess, "run", _boom):
                self.assertIsNone(ca._git_running_here()[0], "a missing pgrep read as 'no git'")

    def test_windows_asks_the_process_table_not_tasklist(self):
        for procs, want in (({4: "explorer.exe", 7: "git.exe"}, True),
                            ({4: "explorer.exe", 9: "git-remote-https.exe"}, True),
                            ({4: "explorer.exe", 5: "D2R.exe"}, False),
                            (None, None), ({}, None)):
            stub = types.SimpleNamespace(_win_process_names=lambda p=procs: p)
            with mock.patch.object(ca, "IS_WIN", True), \
                    mock.patch.dict(sys.modules, {"tv_diablo": stub}):
                self.assertIs(ca._git_running_here()[0], want, "snapshot %r" % (procs,))


class TestTheDoctorRowReadsTheLane(unittest.TestCase):
    NOW = 1790000000000

    def lane(self, **kw):
        base = {"checked": self.NOW, "on": True, "outcome": None, "failSince": None, "failures": 0,
                "failBarS": 3600, "now": self.NOW, "lastTs": None, "say": "",
                "lockCleared": None}
        base.update(kw)
        return base

    def test_failing_PAST_the_bar_is_MISSING_with_the_reason_and_since_when(self):
        st, why = cd.pull_lane_verdict(self.lane(
            outcome="failed", failSince=self.NOW - 2 * 3600 * 1000, failures=24,
            say="the fast-forward did not succeed (exit 128: error: Unable to create "
                "'C:/d2r/.git/index.lock': File exists.) — UNKNOWN, NOT up to date"))
        self.assertEqual(st, cd.MISSING, why)
        self.assertIn("index.lock", why, "the reason is not named")
        self.assertIn("since ", why, "since when is not named")
        self.assertIn("24 attempt", why)

    def test_failing_UNDER_the_bar_is_not_yet_a_finding(self):
        st, why = cd.pull_lane_verdict(self.lane(outcome="failed", failSince=self.NOW - 10 * 60 * 1000,
                                                 failures=2, say="the fetch did not succeed"))
        self.assertEqual(st, cd.UNKNOWN, "a ten-minute blip graded as %s: %s" % (st, why))

    def test_a_pull_that_worked_is_OK(self):
        for oc in ("pulled", "level"):
            st, why = cd.pull_lane_verdict(self.lane(outcome=oc, lastTs=self.NOW - 60000,
                                                     say="already level with origin/main at abc1234"))
            self.assertEqual(st, cd.OK, "%s -> %s: %s" % (oc, st, why))

    def test_a_deliberate_stand_down_is_OK_and_says_so(self):
        st, why = cd.pull_lane_verdict(self.lane(on=False, outcome="off",
                                                 say="auto-pull is switched off here by TV_NO_AUTO_PULL"))
        self.assertEqual(st, cd.OK)
        self.assertIn("TV_NO_AUTO_PULL", why)
        st, why = cd.pull_lane_verdict(self.lane(outcome="dirty", say="local tracked edits are present"))
        self.assertEqual(st, cd.OK)
        self.assertIn("ON PURPOSE", why)

    def test_nobody_tried_is_UNKNOWN_never_OK(self):
        self.assertEqual(cd.pull_lane_verdict(self.lane(checked=None))[0], cd.UNKNOWN)
        self.assertEqual(cd.pull_lane_verdict(None)[0], cd.UNKNOWN)

    def test_the_row_asks_the_console_OVER_THE_WIRE(self):
        failing = self.lane(outcome="failed", failSince=self.NOW - 3 * 3600 * 1000, failures=30,
                            say="the fast-forward did not succeed (index.lock)")
        with mock.patch.object(cd, "_get", lambda path, timeout=4: {cd._PULL_LANE_KEY: failing}):
            self.assertEqual(cd._check_this_checkout_can_update()[0], cd.MISSING)
        with mock.patch.object(cd, "_get", lambda path, timeout=4: None):
            self.assertEqual(cd._check_this_checkout_can_update()[0], cd.UNKNOWN)
        with mock.patch.object(cd, "_get", lambda path, timeout=4: {"ok": True}):
            st, why = cd._check_this_checkout_can_update()
            self.assertEqual(st, cd.UNKNOWN)
            self.assertIn("predates", why)

    def test_the_row_is_on_the_roster(self):
        self.assertIs(dict(cd.CHECKS).get("this checkout can update"), cd._check_this_checkout_can_update)


class TestTheLaneIsPublishedWhereTheRowReads(unittest.TestCase):

    def tearDown(self):
        ca._PULL.clear()
        ca._PULL.update(_PULL0)

    def test_status_publishes_the_lane_under_the_key_the_row_reads(self):
        """THE JOINT: the route must EMIT the key the row asks for. Read as a parsed dict, never as text."""
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "status_payload")
        hits = []
        for node in ast.walk(fn):
            if isinstance(node, ast.Dict):
                for k, v in zip(node.keys, node.values):
                    if isinstance(k, ast.Constant) and k.value == cd._PULL_LANE_KEY:
                        hits.append(v)
        self.assertEqual(len(hits), 1, "status_payload emits %r %d time(s) — the row reads a key the "
                         "route does not send" % (cd._PULL_LANE_KEY, len(hits)))
        v = hits[0]
        self.assertTrue(isinstance(v, ast.Call) and getattr(v.func, "id", "") == "_t"
                        and len(v.args) == 2 and getattr(v.args[1], "id", "") == "pull_state",
                        "the key is not fed by pull_state() through the timing wrapper")

    def test_what_the_console_publishes_grades_as_the_row_says(self):
        now = int(time.time() * 1000)
        with ca._PRUNE_LOCK:
            ca._PULL.update({"checked": now, "on": True, "outcome": "failed", "failures": 12,
                             "failSince": now - 2 * 3600 * 1000,
                             "say": "the fast-forward did not succeed (exit 128: error: Unable to "
                                    "create '.git/index.lock': File exists.)"})
        pl = ca.pull_state()
        self.assertEqual(pl.get("failBarS"), ca._PULL_FAIL_MISSING_S, "the bar is not published")
        st, why = cd.pull_lane_verdict(pl)
        self.assertEqual(st, cd.MISSING, why)

    def test_the_fleet_beacon_says_the_pulls_are_FAILING(self):
        now = int(time.time() * 1000)
        view = {"ok": True, "behind": 3, "dirty": False}
        with mock.patch.dict(os.environ, {}), mock.patch.object(ca, "fleet_origin_status", lambda *a, **k: dict(view)):
            os.environ.pop("TV_NO_AUTO_PULL", None)
            with ca._PRUNE_LOCK:
                ca._PULL.update({"outcome": "failed", "failures": 30, "failSince": now - 11 * 3600 * 1000,
                                 "lastErr": "error: Unable to create '.git/index.lock': File exists."})
            rep = ca._pull_report()
            self.assertIs(rep.get("can"), False, "the beacon still says clear to pull: %r" % rep)
            self.assertIn("auto-pull FAILING", rep.get("why") or "")
            self.assertIn("index.lock", rep.get("why") or "")
            self.assertLessEqual(len(rep.get("why") or ""), 160, "the worker keeps 160 chars of why")
            with ca._PRUNE_LOCK:
                ca._PULL.update({"failSince": now - 5 * 60 * 1000})
            self.assertIs(ca._pull_report().get("can"), True, "a five-minute blip refused the fleet pull")


RED_PROOF = [
    {
        "why": "#64 - without the size refusal a lock a LIVE git is filling (its new index) would be removed from under it",
        "file": "control_app.py",
        "find": "    if st.st_size != 0:\n        out[\"say\"] = (\"left the git lock from %s: it holds",
        "replace": "    if False:\n        out[\"say\"] = (\"left the git lock from %s: it holds",
        "matches": 1,
    },
    {
        "why": "#64 - without the age bar a lock a git took a moment ago would be removed mid-operation",
        "file": "control_app.py",
        "find": "    if age < float(_GIT_LOCK_STALE_S):",
        "replace": "    if False:",
        "matches": 1,
    },
    {
        "why": "#64 - without the running-git refusal a lock whose owner is alive would be removed",
        "file": "control_app.py",
        "find": "    if running:\n        out[\"say\"] = (\"left the git lock from %s: a git process",
        "replace": "    if False:\n        out[\"say\"] = (\"left the git lock from %s: a git process",
        "matches": 1,
    },
    {
        "why": "#64 - a probe that CANNOT answer would read as 'no git running' and license a removal",
        "file": "control_app.py",
        "find": "    if running is None:\n        out[\"say\"] = (\"left the git lock from %s: whether",
        "replace": "    if False:\n        out[\"say\"] = (\"left the git lock from %s: whether",
        "matches": 1,
    },
    {
        "why": "#64 - without the check before the fetch every pull pays a refused fast-forward before the lock is judged",
        "file": "control_app.py",
        "find": "    _lock = _clear_stale_git_lock(REPO)\n    _pull_note_lock(_lock)\n    try:\n",
        "replace": "    _lock = {}\n    try:\n",
        "matches": 1,
    },
    {
        "why": "#64 - without the second trigger a lock that appears after the check wedges the lane exactly like the ALT's",
        "file": "control_app.py",
        "find": "            if _r.returncode != 0 and _names_index_lock(_r):",
        "replace": "            if False:",
        "matches": 1,
    },
    {
        "why": "#64 - the in-app update door (/api/update) must judge the lock before its pull too",
        "file": "control_app.py",
        "find": "        _lk = _clear_stale_git_lock(REPO)\n        _pull_note_lock(_lk)\n        r = _git_run(",
        "replace": "        _lk = {}\n        r = _git_run(",
        "matches": 1,
    },
    {
        "why": "#64 - pulls failing for 11 h must read MISSING on the doctor, not a quiet UNKNOWN",
        "file": "console_doctor.py",
        "find": "        if fail_s > bar:",
        "replace": "        if False:",
        "matches": 1,
    },
    {
        "why": "#64 - the lane must be ON the route the row reads, or the row reads 'predates' forever (the unjoined end)",
        "file": "control_app.py",
        "find": "        \"pullLane\": _t(\"pullLane\", pull_state),\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#64 - the fleet beacon said 'clear to pull' for 11 h while every pull failed",
        "file": "control_app.py",
        "find": "    _failing = _pull_failing_words()\n",
        "replace": "    _failing = None\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
