# -*- coding: utf-8 -*-
"""#50 — EVERY PC PROVES ITS OWN INSTRUMENTS, IN THE BACKGROUND (REG-1447).

His ruling 2026-09-29: the ALT and Dean's PC must prove their own gates - a Mac proof does not speak for
Windows (measured: different gate fingerprints at one commit; the river-outlet law BLIND on the ALT and
red on the Mac). Until today only his Mac's pre-push gate ever wrote a heart census, so on every other PC
`self_arming.may()` said "the heart has never run here" and every lock stayed shut - 76 ALT reels at
EMPTY never routed.

DRIVEN: `self_prove.decide` across every state; `self_prove.tick` end to end with a recording spawn, a
temp memory file and stubbed census/tree/load - never a real prover; `tree_state` on a real temporary
git repo (clean + at upstream -> installed; a local edit or an unpushed commit -> dev); `pid_alive` on
this process and on a dead pid; the rescue loop asks. RED_PROOF below.
"""
import inspect
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import self_prove as SP  # noqa: E402

INSTALLED = ("installed", "level with origin")
STALE = {"state": "stale", "why": "gates changed", "fingerprint": "abc"}
MISSING = {"state": "missing", "why": "never proved"}
CURRENT = {"state": "current", "why": "proved 600 of 650, 0 blind", "fingerprint": "abc", "blind": []}


class TheOneDecision(unittest.TestCase):

    def d(self, census=STALE, tree=INSTALLED, pid=None, busy=5.0, mem=None, now=10_000.0, on=True):
        return SP.decide(census, tree, pid, busy, mem or {}, now, on=on)

    def test_an_idle_installed_pc_with_no_census_proves(self):
        for c in (MISSING, STALE):
            self.assertTrue(self.d(census=c)["start"], "an idle installed PC with %s census did not prove"
                            % c["state"])

    def test_a_current_census_is_left_alone(self):
        self.assertFalse(self.d(census=CURRENT)["start"])

    def test_a_development_tree_never_proves_in_the_background(self):
        r = self.d(tree=("dev", "3 local commit(s)"))
        self.assertFalse(r["start"], "a dev tree started a background prove - it would fight the pre-push gate")
        self.assertEqual(r["key"], "dev")
        self.assertFalse(self.d(tree=("unknown", "no upstream"))["start"], "an UNKNOWN tree was proved on a guess")

    def test_a_busy_or_unmeasured_machine_does_not_start(self):
        self.assertFalse(self.d(busy=SP.MAX_BUSY_TO_START)["start"], "a proof started while he was playing")
        r = self.d(busy=None)
        self.assertFalse(r["start"], "a proof started on an UNKNOWN load")
        self.assertEqual(r["key"], "load-unknown")

    def test_one_proof_at_a_time(self):
        self.assertFalse(self.d(pid=4242)["start"], "a second proof started over a running one")

    def test_a_failed_proof_backs_off_for_the_same_gates_only(self):
        mem = {"lastFailAt": 9_000.0, "lastFailFingerprint": "abc", "lastFailWhy": "x"}
        self.assertFalse(self.d(mem=mem)["start"], "a prover that just failed was restarted at once")
        self.assertTrue(self.d(mem=mem, now=9_000.0 + SP.RETRY_AFTER_FAIL_S + 1)["start"],
                        "the backoff never ends")
        self.assertTrue(self.d(mem=dict(mem, lastFailFingerprint="other"))["start"],
                        "a failure on OLD gates blocked proving the new ones")

    def test_the_switch_turns_it_off(self):
        self.assertFalse(self.d(on=False)["start"])
        self.assertFalse(SP.enabled({"TV_SELF_PROVE": "0"}))
        self.assertTrue(SP.enabled({}))


class TheTickEndToEnd(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="self_prove_law_")
        self.path = os.path.join(self.dir, ".self_prove.json")
        self.spawned = []

    def _spawn(self, log_path):
        self.spawned.append(log_path)
        return 999_999_1                     # a pid that is not alive

    def test_it_spawns_once_then_records_the_outcome(self):
        r = SP.tick(now_s=1000.0, busy=3.0, tree=INSTALLED, census=MISSING, path=self.path,
                    spawn_fn=self._spawn, env={})
        self.assertEqual(len(self.spawned), 1, "an idle installed PC with no census did not start a proof")
        self.assertEqual(r["owed"], 1)
        mem = json.load(io.open(self.path, encoding="utf-8"))
        self.assertEqual(mem.get("pid"), 999_999_1, "the lane did not remember the prover it started")
        # the prover has ended (the pid is dead) and left a current census -> worked, and nothing new starts
        r = SP.tick(now_s=2000.0, busy=3.0, tree=INSTALLED, census=CURRENT, path=self.path,
                    spawn_fn=self._spawn, env={})
        self.assertEqual(len(self.spawned), 1, "a PC with a current census started another proof")
        self.assertEqual(r["worked"], 1, "a finished proof was not counted as work")
        self.assertEqual(r["owed"], 0)
        self.assertIsNotNone(r["lastTs"])

    def test_a_proof_that_leaves_no_census_backs_off(self):
        SP.tick(now_s=1000.0, busy=3.0, tree=INSTALLED, census=STALE, path=self.path,
                spawn_fn=self._spawn, env={})
        r = SP.tick(now_s=1600.0, busy=3.0, tree=INSTALLED, census=STALE, path=self.path,
                    spawn_fn=self._spawn, env={})
        self.assertEqual(len(self.spawned), 1, "a prover that failed was restarted ten minutes later")
        self.assertEqual(r["key"], "backoff")

    def test_an_update_during_the_proof_is_not_a_failure(self):
        SP.tick(now_s=1000.0, busy=3.0, tree=INSTALLED, census=STALE, path=self.path,
                spawn_fn=self._spawn, env={})
        moved = dict(STALE, fingerprint="def")          # the console pulled new gates mid-proof
        r = SP.tick(now_s=1600.0, busy=3.0, tree=INSTALLED, census=moved, path=self.path,
                    spawn_fn=self._spawn, env={})
        self.assertEqual(len(self.spawned), 2, "an update during the proof was punished with the failure "
                                                "backoff instead of proving the new gates")
        self.assertEqual(r["key"], "start")

    def test_a_lost_save_never_starts_a_second_prover(self):
        """second eye: if saving fails right after a spawn, the next tick must still know a proof runs."""
        from unittest import mock
        alive = {"pid": None}

        def _spawn_live(log_path):
            self.spawned.append(log_path)
            alive["pid"] = 4_242_424
            return 4_242_424
        SP._STARTED["pid"] = None
        with mock.patch.object(SP, "save", side_effect=OSError("disk full")), \
                mock.patch.object(SP, "pid_alive", lambda pid: pid == alive["pid"]):
            SP.tick(now_s=1000.0, busy=3.0, tree=INSTALLED, census=MISSING, path=self.path,
                    spawn_fn=_spawn_live, env={})
            r = SP.tick(now_s=1600.0, busy=3.0, tree=INSTALLED, census=MISSING, path=self.path,
                        spawn_fn=_spawn_live, env={})
        SP._STARTED["pid"] = None
        self.assertEqual(len(self.spawned), 1, "a failed save made the lane forget its running proof and "
                                               "start a second one - a runaway every ten minutes")
        self.assertEqual(r["key"], "running")

    def test_a_corrupt_memory_or_load_never_raises_and_never_starts(self):
        io.open(self.path, "w", encoding="utf-8").write(json.dumps({"worked": "x", "pid": 999_999_1,
                                                                    "lastFailAt": "bad"}))
        r = SP.tick(now_s=1000.0, busy=float("nan"), tree=INSTALLED, census=CURRENT, path=self.path,
                    spawn_fn=self._spawn, env={})
        self.assertEqual(self.spawned, [])
        self.assertIn("key", r)
        self.assertEqual(SP.decide(STALE, INSTALLED, None, float("nan"), {}, 1.0)["key"], "load-unknown",
                         "a NaN load reading passed the idle check")
        self.assertEqual(SP.decide(STALE, INSTALLED, None, "5", {}, 1.0)["start"], True)
        self.assertEqual(SP.decide(STALE, INSTALLED, None, "junk", {}, 1.0)["key"], "load-unknown")

    def test_an_unreadable_memory_is_unknown_and_starts_nothing(self):
        io.open(self.path, "w", encoding="utf-8").write("{not json")
        r = SP.tick(now_s=1000.0, busy=3.0, tree=INSTALLED, census=MISSING, path=self.path,
                    spawn_fn=self._spawn, env={})
        self.assertEqual(self.spawned, [])
        self.assertIsNone(r["owed"], "an unreadable lane memory reported a measured figure")


class TheTreeIsToldApart(unittest.TestCase):

    def _repo(self):
        root = tempfile.mkdtemp(prefix="self_prove_git_")
        up, wk = os.path.join(root, "up.git"), os.path.join(root, "wk")
        run = lambda *a, cwd=root: subprocess.run(["git"] + list(a), cwd=cwd, capture_output=True, text=True)
        run("init", "-q", "--bare", up)
        run("clone", "-q", up, wk)
        for k, v in (("user.email", "law@x"), ("user.name", "law")):
            run("config", k, v, cwd=wk)
        io.open(os.path.join(wk, "f.txt"), "w").write("a\n")
        run("add", "f.txt", cwd=wk)
        run("commit", "-qm", "one", cwd=wk)
        run("push", "-q", "origin", "HEAD", cwd=wk)
        run("branch", "--set-upstream-to=origin/" + run("rev-parse", "--abbrev-ref", "HEAD", cwd=wk).stdout.strip(),
            cwd=wk)

        def git(*args, timeout=15):
            r = subprocess.run(["git"] + list(args), cwd=wk, capture_output=True, text=True, timeout=timeout)
            return r.returncode, (r.stdout or "").strip()
        return wk, git, run

    def test_clean_and_level_is_installed_and_an_edit_or_a_local_commit_is_dev(self):
        wk, git, run = self._repo()
        self.assertEqual(SP.tree_state(git)[0], "installed", SP.tree_state(git))
        io.open(os.path.join(wk, "f.txt"), "w").write("b\n")
        self.assertEqual(SP.tree_state(git)[0], "dev", "a tree with local edits read as an installed console")
        run("commit", "-qam", "two", cwd=wk)
        self.assertEqual(SP.tree_state(git)[0], "dev", "a tree with an unpushed commit read as installed")


class TheProcessProbeIsSafe(unittest.TestCase):

    def test_alive_and_dead(self):
        self.assertTrue(SP.pid_alive(os.getpid()))
        self.assertFalse(SP.pid_alive(None))
        self.assertFalse(SP.pid_alive(0))
        p = subprocess.Popen([sys.executable, "-c", "pass"])
        p.wait()
        self.assertFalse(SP.pid_alive(p.pid), "a finished process read as alive")

    def test_the_heart_never_sends_signal_zero_on_windows(self):
        """Driven as Windows: os.name is 'nt', os.kill records, and the answer must come from the safe probe."""
        import heart2
        from unittest import mock
        kills, asked = [], []

        def _kill(pid, sig):
            kills.append((pid, sig))

        def _safe(pid):
            asked.append(pid)
            return True
        with mock.patch.object(heart2.os, "name", "nt"), mock.patch.object(heart2.os, "kill", _kill), \
                mock.patch.object(SP, "pid_alive", _safe):
            got = heart2._pid_alive(4242)
        self.assertEqual(kills, [], "heart2._pid_alive sent os.kill(pid, 0) on Windows, where signal 0 is "
                                    "CTRL_C_EVENT - a Ctrl-C, not a probe")
        self.assertEqual((got, asked), (True, [4242]), "the Windows answer did not come from the safe probe")


class ABackgroundProofIsPatient(unittest.TestCase):
    """REG-1454 - on the ALT a 120 s law timed out on every background proof (BELOW_NORMAL, console filming)."""

    def test_the_heart_honours_the_patience_it_is_given_and_bounds_it(self):
        import heart2
        self.assertEqual(heart2._deadline_scale(1, env={}), 1, "the default single-lane deadline moved")
        self.assertEqual(heart2._deadline_scale(4, env={}), heart2.LANE_DEADLINE_SCALE)
        self.assertEqual(heart2._deadline_scale(1, env={"HEART2_DEADLINE_SCALE": "4"}), 4,
                         "the patience a background caller asked for was ignored")
        self.assertEqual(heart2._deadline_scale(1, env={"HEART2_DEADLINE_SCALE": "999"}),
                         heart2.DEADLINE_SCALE_MAX, "an unbounded deadline would let a hung gate hang forever")
        self.assertEqual(heart2._deadline_scale(1, env={"HEART2_DEADLINE_SCALE": "junk"}), 1)

    def test_the_lane_asks_for_it(self):
        seen = {}

        class _P(object):
            pid = 4242

        def _popen(cmd, **kw):
            seen.update(kw.get("env") or {})
            return _P()
        d = tempfile.mkdtemp(prefix="self_prove_spawn_")
        SP.spawn(os.path.join(d, "log"), python=sys.executable, popen=_popen)
        self.assertEqual(seen.get("HEART2_DEADLINE_SCALE"), "4",
                         "the background prover runs with the Mac's deadlines on a slower, busier PC")


class TheConsoleAsks(unittest.TestCase):

    def test_the_rescue_loop_ticks_the_lane_and_status_publishes_it(self):
        import control_app as ca
        loop = inspect.getsource(ca._console_rescue_loop)
        self.assertIn("_self_prove_tick()", loop, "nothing asks - no PC ever proves itself")
        self.assertIn('"selfProve": dict(_SELF_PROVE)', inspect.getsource(ca), "the lane is invisible")


RED_PROOF = [
    {
        "why": "2026-09-29 - the heart ignores the patience a background proof asks for (REG-1454)",
        "file": "tv/heart2.py",
        "find": "    raw = (env if env is not None else os.environ).get(\"HEART2_DEADLINE_SCALE\")\n",
        "replace": "    raw = None\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (second eye) - a failed save after a spawn makes the lane start a second prover",
        "file": "tv/self_prove.py",
        "find": "            _STARTED[\"pid\"] = mem[\"pid\"]\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (second eye) - a NaN load reading passes the idle check",
        "file": "tv/self_prove.py",
        "find": "    if busy_pct is None or busy_pct != busy_pct:",
        "replace": "    if busy_pct is None:",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (second eye) - a corrupt lane memory makes every tick raise into the rescue loop",
        "file": "tv/self_prove.py",
        "find": "        return _tick(now_s, busy, tree, census, path, spawn_fn, env)\n    except Exception as e:\n",
        "replace": "        return _tick(now_s, busy, tree, census, path, spawn_fn, env)\n    except ZeroDivisionError as e:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - an update during a proof is booked as a failure and the new gates wait 3 hours",
        "file": "tv/self_prove.py",
        "find": "        elif mem.get(\"startedFor\") and census.get(\"fingerprint\") != mem.get(\"startedFor\"):\n",
        "replace": "        elif False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - a development tree proves in the background and fights the pre-push gate for the CPU",
        "file": "tv/self_prove.py",
        "find": "    if kind != \"installed\":\n",
        "replace": "    if kind == \"unknown\":\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - a proof starts while he is playing",
        "file": "tv/self_prove.py",
        "find": "    if busy_pct >= MAX_BUSY_TO_START:\n",
        "replace": "    if busy_pct >= 1000:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - a prover that failed is restarted every ten minutes, all day",
        "file": "tv/self_prove.py",
        "find": "            and now_s - last_fail < RETRY_AFTER_FAIL_S:\n",
        "replace": "            and now_s - last_fail < 0:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the heart sends signal 0 (a Ctrl-C) on Windows again",
        "file": "tv/heart2.py",
        "find": "    if os.name == \"nt\":\n        try:\n            import self_prove as _sp\n",
        "replace": "    if False:\n        try:\n            import self_prove as _sp\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - nothing asks: no PC ever proves itself",
        "file": "tv/control_app.py",
        "find": "                _self_prove_tick()          # #50 — has THIS PC proved its own instruments?\n",
        "replace": "                pass\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
