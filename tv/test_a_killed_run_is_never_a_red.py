# -*- coding: utf-8 -*-
"""REG-2350 (#42 R5) - A RUN A SIGNAL ENDED IS UNKNOWN, NEVER A RED.

heart2's _run_gate_once returned `returncode == 0`. A law process killed by a signal (reap's by-pid kill, jetsam, a
Ctrl-C) therefore read RED: in a tampered run that is PROVEN, banked after a green closing run and standing until an
input moves - a lie; in a clean run it read ALREADY RED and refused a good push. The same holds for a shell's 128+N
exit and for a GRANDCHILD a signal ended (a headless Chrome, the node demo, a python helper): the law exits 1 with an
ERROR case. The kill watch (gate_trace/sitecustomize.py, armed by heart2 through TV_GATE_KILLS) now writes a K line for
every child that a signal ended and an X line for every signal the run itself sent; a K no X explains is a kill from
outside, and the run is UNKNOWN.

DRIVEN, real code and real signals:
  1. _run_gate_once over a probe gate: a law killed by SIGKILL, a law exiting 137, a helper killed from outside (red
     AND green) are UNKNOWN (None); an ordinary red, exit 2, a helper the law killed itself (kill, killpg) and a helper
     that died of SIGPIPE are judged exactly as before.
  2. _prove_one: a tamper that kills is UNPROVABLE, never PROVEN; a helper killed from outside while the law stays green
     is UNPROVABLE, never BLIND.
  3. _prove_push_one with a fixture verdict cache: the killed tamper banks NOTHING; the red one banks (the baseline).
  4. the narrow path (a recalled red memory): a killed tampered subset falls through to the full proof, and a killed run
     teaches the memory nothing.
  5. a killed CLEAN run is UNKNOWN, not "ALREADY RED", and does not stop a push; a really red one still does.
  6. the kill watch itself: K for an outside kill (waited, or swept at exit), X for a kill the process sent (pid, group,
     a 0 probe is none), SIGPIPE is not a kill; two copies of the hook on sys.path boot once.
  7. SIGINT ends a prover like SIGTERM: its sandbox is removed and it exits 128+2.
Every scenario that kills on purpose runs in a DRIVER subprocess whose environment holds no watch of its own, so the
watch heart2 arms over THIS law's run is never fed by them. RED_PROOF below. [[unknown-stays-unknown]]
"""
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
from console_safe import enable as _console_safe_enable  # noqa: E402  (its red-proofs carry non-ASCII)
_console_safe_enable()
import heart2 as H  # noqa: E402

_POSIX = os.name == "posix" and hasattr(signal, "SIGKILL")

PROBE = r'''
import os, signal, subprocess, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import subject


class T(unittest.TestCase):
    def test_x(self):
        m = subject.MODE
        if m == "red":
            self.fail("the tamper is caught")
        if m == "selfkill":
            os.kill(os.getpid(), signal.SIGKILL)
        if m == "exit137":
            sys.stdout.flush()
            os._exit(137)
        if m == "exit2":
            sys.stdout.flush()
            os._exit(2)
        if m == "grandchild":
            subprocess.run(["/bin/sh", "-c", "kill -9 $$"])
            self.fail("a helper died")
        if m == "greenkill":
            subprocess.run(["/bin/sh", "-c", "kill -9 $$"])
        if m == "ownkill":
            p = subprocess.Popen(["sleep", "30"])
            p.kill()
            p.wait()
            self.fail("caught - this law ended its own helper on the way")
        if m == "groupkill":
            p = subprocess.Popen(["sleep", "30"], start_new_session=True)
            os.killpg(p.pid, signal.SIGTERM)
            p.wait()
            self.fail("caught - this law ended its own helper's group on the way")
        if m == "pipe":
            subprocess.run(["/bin/sh", "-c", "kill -PIPE $$"])
            self.fail("caught - a helper's closed pipe is not a kill")


if __name__ == "__main__":
    unittest.main()
'''

DRIVER = r'''
import io, json, os, sys, threading
sys.path.insert(0, %(here)r)
import heart2 as H

TV = %(tv)r
OUT = {}
LINES = []
say = lambda *a: LINES.append(" ".join(str(x) for x in a))


def mode(m):
    with io.open(os.path.join(TV, "subject.py"), "w", encoding="utf-8") as fh:
        fh.write('MODE = "%%s"\n' %% m)


def proof(m):
    return {"why": "fixture", "file": "subject.py", "find": 'MODE = "ok"', "replace": 'MODE = "%%s"' %% m, "matches": 1}


once = {}
for m in ("ok", "red", "selfkill", "exit137", "exit2", "grandchild", "greenkill", "ownkill", "groupkill", "pipe"):
    mode(m)
    ok, tail = H._run_gate_once(TV, "probe_gate.py", timeout=60)
    once[m] = [ok, str(tail)[:300]]
OUT["once"] = once

mode("ok")
OUT["prove_one"] = dict((m, H._prove_one(TV, "probe", "probe_gate.py", proof(m), 0, say))
                        for m in ("red", "selfkill", "exit137", "grandchild", "greenkill", "ownkill", "groupkill"))

cache = H._VerdictCache(path=os.path.join(%(tmp)r, ".heart2_cache.json"), say=say)
H._PUSH = H._PushRun(order={}, browser=(), cache=cache)
try:
    OUT["push_killed"] = H._prove_push_one(TV, "probe", "probe_gate.py", proof("selfkill"), 0, say, {})
    OUT["push_killed_banked"] = len(cache.entries)
    OUT["push_red"] = H._prove_push_one(TV, "probe", "probe_gate.py", proof("red"), 1, say, {})
    OUT["push_red_banked"] = len(cache.entries)
    learned = []
    H._red_recall = lambda key: ["T.test_x"]
    H._red_remember = lambda *a, **k: learned.append(a)
    del LINES[:]
    OUT["narrow_killed"] = H._prove_one(TV, "probe", "probe_gate.py", proof("selfkill"), 2, say)
    OUT["narrow_killed_learned"] = len(learned)
    OUT["narrow_killed_lines"] = list(LINES)
    del LINES[:]
    OUT["narrow_red"] = H._prove_one(TV, "probe", "probe_gate.py", proof("red"), 3, say)
    OUT["narrow_red_lines"] = list(LINES)
finally:
    H._PUSH = None

mode("selfkill")
why = {}
OUT["clean_killed"] = [H._prove_one(TV, "probe", "probe_gate.py", proof("red"), 0, say, why=why), bool(why.get("red"))]
run = H._PushRun(order={}, browser=(), cache=None)
H._PUSH = run
try:
    OUT["clean_killed_push"] = list(H._prove_gate_push(TV, "probe", "probe_gate.py", [proof("red")], say, run)[1])
    OUT["clean_killed_push_stop"] = run.first
finally:
    H._PUSH = None
mode("red")
why = {}
OUT["clean_red"] = [H._prove_one(TV, "probe", "probe_gate.py", proof("red"), 0, say, why=why), bool(why.get("red"))]
run = H._PushRun(order={}, browser=(), cache=None)
H._PUSH = run
try:
    H._prove_gate_push(TV, "probe", "probe_gate.py", [proof("red")], say, run)
    OUT["clean_red_push_stop"] = run.first
finally:
    H._PUSH = None
OUT["signal_runs"] = H._SIGNAL_RUNS["n"]
print("DRIVER-RESULT " + json.dumps(OUT))
'''

#: os._exit at the end: no exit sweep runs, so only the wait / poll wrappers can say what ended these children
WAITED = r'''
import os, signal, subprocess, sys
subprocess.run(["/bin/sh", "-c", "kill -9 $$"])                       # a: killed from outside, waited on
p = subprocess.Popen(["sleep", "30"]); p.kill(); p.wait()               # b: this process killed it
q = subprocess.Popen(["sleep", "30"], start_new_session=True)
os.killpg(q.pid, signal.SIGTERM); q.wait()                             # c: this process killed its group
r = subprocess.Popen(["/bin/sh", "-c", "sleep 0.3; kill -9 $$"])
os.kill(r.pid, 0)                                                      # e: a 0 probe sends nothing,
r.wait()                                                               #    and only wait() reaps this one
subprocess.run(["/bin/sh", "-c", "kill -PIPE $$"])                     # f: a closed pipe
print("WATCHED-DONE %d %d %d %d" % (p.pid, q.pid, r.pid, os.getpid()))
sys.stdout.flush()
os._exit(0)
'''

#: a normal exit: the child nobody waited on is found by the exit sweep alone
SWEPT = r'''
import os, subprocess, time
d = subprocess.Popen(["/bin/sh", "-c", "kill -TERM $$"]); time.sleep(0.4)   # d: never waited
print("WATCHED-DONE %d" % d.pid)
'''


def _quiet(*a, **k):
    pass


def _env_without_watch():
    """The driver's own environment: no kill watch and no hook on its path - heart2 inside it arms its own."""
    env = dict(os.environ)
    env.pop("TV_GATE_KILLS", None)
    env.pop("PYTHONPATH", None)
    env["HEART2_RED_MEMORY"] = "0"
    return env


@unittest.skipUnless(_POSIX, "no POSIX signals here - a run cannot be ended by one, so there is nothing to judge")
class ARunASignalEndedIsUnknown(unittest.TestCase):
    """1-5 through the real prover, in one driver run (the kills are real)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="h2killed.")
        tv = os.path.join(cls.tmp, "repo", "tv")
        os.makedirs(tv)
        with io.open(os.path.join(tv, "probe_gate.py"), "w", encoding="utf-8") as fh:
            fh.write(PROBE)
        with io.open(os.path.join(tv, "subject.py"), "w", encoding="utf-8") as fh:
            fh.write('MODE = "ok"\n')
        drv = DRIVER % {"here": HERE, "tv": tv, "tmp": cls.tmp}
        r = subprocess.run([sys.executable, "-c", drv], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=600, env=_env_without_watch(), cwd=cls.tmp)
        line = [ln for ln in (r.stdout or "").splitlines() if ln.startswith("DRIVER-RESULT ")]
        cls.out = json.loads(line[-1][len("DRIVER-RESULT "):]) if line else None
        cls.err = "exit %s: %s %s" % (r.returncode, (r.stdout or "")[-800:], (r.stderr or "")[-1500:])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.assertIsNotNone(self.out, "PREMISE: the driver produced no result - %s" % self.err)

    def test_a_law_a_signal_ended_is_unknown(self):
        o = self.out["once"]
        self.assertIs(o["ok"][0], True, "PREMISE: the probe gate is green untampered: %s" % o["ok"])
        self.assertIs(o["red"][0], False, "PREMISE: an ordinary red still reads red: %s" % o["red"])
        self.assertIsNone(o["selfkill"][0], "a law killed by SIGKILL read as a verdict: %s" % o["selfkill"])
        self.assertIn("signal 9", o["selfkill"][1])
        self.assertIsNone(o["exit137"][0], "a shell's 128+9 read as a red: %s" % o["exit137"])
        self.assertIs(o["exit2"][0], False, "an ordinary exit 2 stopped being a red: %s" % o["exit2"])

    def test_a_helper_killed_from_outside_is_unknown_red_or_green(self):
        o = self.out["once"]
        self.assertIsNone(o["grandchild"][0], "a law red because its helper was killed from outside read as a red "
                                              "verdict: %s" % o["grandchild"])
        self.assertIn("nothing in the run sent", o["grandchild"][1])
        self.assertIsNone(o["greenkill"][0], "a law that stayed green while its helper was killed from outside read "
                                             "as a verdict: %s" % o["greenkill"])

    def test_a_law_that_ends_its_own_helper_is_judged_as_before(self):
        o = self.out["once"]
        self.assertIs(o["ownkill"][0], False, "a law that killed its own helper is no longer judged: %s" % o["ownkill"])
        self.assertIs(o["groupkill"][0], False, "a law that killed its helper's group is no longer judged: %s"
                      % o["groupkill"])
        self.assertIs(o["pipe"][0], False, "a helper's closed pipe was read as a kill: %s" % o["pipe"])

    def test_a_tamper_that_kills_is_never_proven_and_never_blind(self):
        p = self.out["prove_one"]
        self.assertEqual(p["red"], H.PROVEN, "PREMISE: a red tamper is PROVEN: %s" % p)
        for m in ("selfkill", "exit137", "grandchild"):
            self.assertEqual(p[m], H.UNPROVABLE, "a tampered run a signal ended was filed %s, never UNKNOWN: %s"
                             % (p[m], m))
        self.assertEqual(p["greenkill"], H.UNPROVABLE, "a green tampered run whose helper was killed from outside was "
                                                       "filed %s - the tamper was never fairly judged" % p["greenkill"])
        self.assertEqual(p["ownkill"], H.PROVEN, "a law that kills its own helper can no longer be proven")
        self.assertEqual(p["groupkill"], H.PROVEN, "a law that kills its helper's group can no longer be proven")

    def test_a_killed_tamper_banks_nothing_at_push_time(self):
        self.assertEqual(self.out["push_killed"], H.UNPROVABLE)
        self.assertEqual(self.out["push_killed_banked"], 0, "a killed tampered run was banked in the verdict cache")
        self.assertEqual(self.out["push_red"], H.PROVEN, "PREMISE: the red tamper is proven at push time")
        self.assertEqual(self.out["push_red_banked"], 1, "PREMISE: a proven push proof is banked")

    def test_the_narrow_path_falls_through_on_a_killed_subset(self):
        self.assertEqual(self.out["narrow_red"], H.PROVEN)
        self.assertTrue(any("case(s) that caught it before" in ln for ln in self.out["narrow_red_lines"]),
                        "PREMISE: the narrow path ran: %s" % self.out["narrow_red_lines"])
        self.assertEqual(self.out["narrow_killed"], H.UNPROVABLE,
                         "a narrowed proof whose tampered subset a signal ended was filed %s" % self.out["narrow_killed"])
        self.assertFalse(any("case(s) that caught it before" in ln for ln in self.out["narrow_killed_lines"]),
                         "the narrow path credited a killed subset: %s" % self.out["narrow_killed_lines"])
        self.assertEqual(self.out["narrow_killed_learned"], 0, "a killed run taught the red memory which cases caught it")

    def test_a_killed_clean_run_is_unknown_not_already_red(self):
        v, red = self.out["clean_killed"]
        self.assertEqual((v, red), (H.UNPROVABLE, False), "a clean run a signal ended read as ALREADY RED")
        self.assertIsNone(self.out["clean_killed_push_stop"], "a killed clean run stopped (refused) the push: %s"
                          % (self.out["clean_killed_push_stop"],))
        self.assertEqual((self.out["clean_red"][0], self.out["clean_red"][1]), (H.UNPROVABLE, True),
                         "PREMISE: a really red clean run is ALREADY RED")
        self.assertIsNotNone(self.out["clean_red_push_stop"], "PREMISE: a really red clean run still stops the push")
        self.assertGreaterEqual(self.out["signal_runs"], 6, "the prover did not count the runs a signal ended")


@unittest.skipUnless(_POSIX, "no POSIX signals here")
class TheKillWatchSaysWhoSentIt(unittest.TestCase):
    """6 - gate_trace/sitecustomize.py's K and X lines, read by heart2._kills_in."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="h2watch.")
        self.addCleanup(shutil.rmtree, self.d, True)

    def _watched(self, script):
        kills = os.path.join(self.d, "kills-%d.tsv" % len(os.listdir(self.d)))
        env = dict(os.environ, TV_GATE_KILLS=kills, PYTHONPATH=os.path.join(HERE, "gate_trace"))
        r = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=120, env=env,
                           cwd=self.d)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("WATCHED-DONE")]
        self.assertTrue(line, "PREMISE: the watched process did not finish: %s %s" % (r.stdout, r.stderr[-800:]))
        text = ""
        if os.path.exists(kills):
            with io.open(kills, encoding="utf-8") as fh:
                text = fh.read()
        return line[0].split()[1:], text, H._kills_in(kills)

    def test_an_outside_kill_is_said_and_a_sent_one_is_explained(self):
        (own, grp, probed, me), text, left = self._watched(WAITED)
        ks = [ln for ln in text.splitlines() if ln.startswith("K\t")]
        self.assertGreaterEqual(len(ks), 5, "the watch did not say every child a signal ended:\n%s" % text)
        self.assertIn("X\t%s\tpid=%s sig=9" % (me, own), text, "a kill this process sent left no X line:\n%s" % text)
        self.assertIn("X\t%s\tpgid=%s sig=15" % (me, grp), text, "a group kill this process sent left no X line")
        self.assertNotIn("pid=%s sig=0" % probed, text, "a 0 probe was written as a kill:\n%s" % text)
        got = sorted((k["pid"], k["sig"], k["head"]) for k in left)
        self.assertEqual(len(got), 2, "the unexplained kills are not exactly the two from outside: %s\n%s" % (got, text))
        self.assertIn((probed, "9", "sh"), got, "an outside kill reaped by wait() alone was not said, or a 0 probe "
                                                "explained it away:\n%s" % text)
        self.assertEqual([h for _p, _s, h in got], ["sh", "sh"], got)

    def test_a_child_nobody_waited_on_is_swept_at_exit(self):
        (swept,), text, left = self._watched(SWEPT)
        self.assertEqual([(k["pid"], k["sig"]) for k in left], [(swept, "15")],
                         "a child a signal ended that nobody waited on was not said at exit:\n%s" % text)

    def test_the_reader_explains_by_pid_by_group_and_never_by_a_pipe(self):
        p = os.path.join(self.d, "k.tsv")
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write("X\t1\tpid=100 sig=9\nK\t1\tpid=100 pgid=- sig=9 head=a\n"          # explained by pid
                     "X\t1\tpgid=200 sig=15\nK\t1\tpid=200 pgid=- sig=15 head=b\n"       # a group leader, no pgid read
                     "X\t1\tpgid=300 sig=15\nK\t1\tpid=301 pgid=300 sig=15 head=c\n"     # a member of a sent group
                     "K\t1\tpid=400 pgid=7 sig=13 head=d\n"                               # a closed pipe
                     "K\t1\tpid=500 pgid=7 sig=9 head=e\n"                                # from outside
                     "garbage line\nK\t1\tpid=600 pgid=7 sig=x head=f\n")
        self.assertEqual([k["head"] for k in H._kills_in(p)], ["e"])
        with io.open(p, "a", encoding="utf-8") as fh:
            fh.write("X\t1\tall sig=9\n")
        self.assertEqual(H._kills_in(p), [], "a signal sent to every process explains every kill")
        self.assertEqual(H._kills_in(os.path.join(self.d, "absent.tsv")), [], "an unreadable watch granted something")

    def test_a_shell_word_for_a_signal_is_a_signal(self):
        for rc, n in ((-9, 9), (-2, 2), (130, 2), (134, 6), (137, 9), (143, 15), (129, 1), (142, 14)):
            self.assertEqual((H._ended_by_signal(rc) or (None,))[0], n, "exit %d is not read as signal %d" % (rc, n))
        for rc in (0, 1, 2, 77, 128, 255, None):
            self.assertIsNone(H._ended_by_signal(rc), "exit %r was read as a signal" % (rc,))

    def test_two_copies_of_the_hook_boot_once(self):
        a, b, root = (os.path.join(self.d, n) for n in ("a", "b", "root"))
        for x in (a, b):
            shutil.copytree(os.path.join(HERE, "gate_trace"), x)
        os.makedirs(root)
        trace = os.path.join(self.d, "trace.tsv")
        env = dict(os.environ, TV_GATE_TRACE=trace, TV_GATE_TRACE_ROOT=root, PYTHONPATH=os.pathsep.join((a, b)))
        env.pop("TV_GATE_KILLS", None)
        r = subprocess.run([sys.executable, "-c", "print('booted')"], capture_output=True, text=True, timeout=120,
                           env=env, cwd=self.d)
        self.assertIn("booted", r.stdout, r.stderr[-800:])
        with io.open(trace, encoding="utf-8") as fh:
            boots = [ln for ln in fh.read().splitlines() if ln.startswith("B\t")]
        self.assertEqual(len(boots), 1, "two copies of the trace hook booted each other %d times" % len(boots))


@unittest.skipUnless(_POSIX, "no POSIX signals here")
class ACtrlCEndsTheProverCleanly(unittest.TestCase):
    """7 - before, a Ctrl-C raised KeyboardInterrupt in the main thread only; lanes ran on with their sandboxes."""

    CHILD = r"""
import os, sys, tempfile, time
sys.path.insert(0, %(here)r)
import heart2 as H
H.install_sandbox_cleanup()
root = H._track_sandbox(tempfile.mkdtemp(prefix="heart2.", dir=%(tmp)r))
print(root, flush=True)
time.sleep(30)
print("NOT ENDED", flush=True)
"""

    def test_sigint_removes_the_sandbox_and_says_so_in_the_exit(self):
        tmp = tempfile.mkdtemp(prefix="h2sigint.")
        self.addCleanup(shutil.rmtree, tmp, True)
        p = subprocess.Popen([sys.executable, "-c", self.CHILD % {"here": HERE, "tmp": tmp}], stdout=subprocess.PIPE,
                             text=True)
        root = p.stdout.readline().strip()
        self.assertTrue(root and os.path.isdir(root), "PREMISE: the child made no sandbox")
        p.send_signal(signal.SIGINT)
        rc = p.wait(timeout=30)
        p.stdout.close()
        self.assertEqual(rc, 128 + signal.SIGINT, "a Ctrl-C did not end the prover the way its handler says (rc %s)" % rc)
        self.assertFalse(os.path.exists(root), "a Ctrl-C'd prover left its sandbox behind")


RED_PROOF = [
    {"why": "REG-2350 - a law killed by a signal is read as a red again: a killed tampered run is banked PROVEN",
     "file": "heart2.py",
     "find": "    if rc < 0:\n        return -rc, \"the law was killed by %s\" % _signal_words(-rc)\n",
     "replace": "    if rc < -999:\n        return -rc, \"the law was killed by %s\" % _signal_words(-rc)\n",
     "matches": 1},
    {"why": "REG-2350 - a shell's 128+N (a child killed by signal N) is read as a red again",
     "file": "heart2.py",
     "find": "    if rc - 128 in _SHELL_SIGNALS:\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-2350 - the kill watch is armed and never read: a helper killed from outside makes the law red, PROVEN",
     "file": "heart2.py",
     "find": "        _killed = _kills_in(_watch) if _watch else []\n",
     "replace": "        _killed = []\n",
     "matches": 1},
    {"why": "REG-2350 - the run is never given the watch file, so no child's kill is ever written",
     "file": "heart2.py",
     "find": "    env[\"TV_GATE_KILLS\"] = path\n",
     "replace": "    env[\"TV_GATE_KILLS_OFF\"] = path\n",
     "matches": 1},
    {"why": "REG-2350 - the hook is never put on the run's path, so nothing in the run watches its children",
     "file": "heart2.py",
     "find": "        env[\"PYTHONPATH\"] = hook_dir + (os.pathsep + old if old else \"\")  # KILL-WATCH-ARM\n",
     "replace": "        pass  # KILL-WATCH-ARM\n",
     "matches": 1},
    {"why": "REG-2350 - a kill the law sent itself is no longer explained: every law that ends its helper is UNKNOWN",
     "file": "heart2.py",
     "find": "        if every or k.get(\"pid\") in pids or k.get(\"pid\") in groups or (k.get(\"pgid\") or \"-\") in groups:\n",
     "replace": "        if every:\n",
     "matches": 1},
    {"why": "REG-2350 - a group kill of a leader whose group was never read is not explained",
     "file": "heart2.py",
     "find": "        if every or k.get(\"pid\") in pids or k.get(\"pid\") in groups or (k.get(\"pgid\") or \"-\") in groups:\n",
     "replace": "        if every or k.get(\"pid\") in pids or (k.get(\"pgid\") or \"-\") in groups:\n",
     "matches": 1},
    {"why": "REG-2350 - a closed pipe (SIGPIPE) is read as a kill from outside",
     "file": "heart2.py",
     "find": "            if int(k.get(\"sig\")) == _pipe:\n                continue\n",
     "replace": "            if int(k.get(\"sig\")) == -1:\n                continue\n",
     "matches": 1},
    {"why": "REG-2350 - a Ctrl-C leaves the prover's lanes and sandboxes running behind a KeyboardInterrupt",
     "file": "heart2.py",
     "find": "    for name in (\"SIGTERM\", \"SIGALRM\", \"SIGHUP\", \"SIGINT\"):  # REG-2350 - SIGINT\n",
     "replace": "    for name in (\"SIGTERM\", \"SIGALRM\", \"SIGHUP\"):  # REG-2350 - SIGINT\n",
     "matches": 1},
    {"why": "REG-2350 - the narrow path credits a tampered subset that a signal ended",
     "file": "heart2.py",
     "find": "    if ok_t is False:\n        say(",
     "replace": "    if ok_t is not True:\n        say(",
     "matches": 1},
    {"why": "REG-2350 - a child a signal ended is never written when it is waited on",
     "file": "gate_trace/sitecustomize.py",
     "find": "                judged(self)  # KILL-WATCH-WAIT\n",
     "replace": "                pass  # KILL-WATCH-WAIT\n",
     "matches": 1},
    {"why": "REG-2350 - a child a signal ended is never written when it is polled (Chrome's teardown polls)",
     "file": "gate_trace/sitecustomize.py",
     "find": "                judged(self)  # KILL-WATCH-POLL\n",
     "replace": "                pass  # KILL-WATCH-POLL\n",
     "matches": 1},
    {"why": "REG-2350 - a child nobody waited on (a jetsam'd Chrome) is never swept at exit",
     "file": "gate_trace/sitecustomize.py",
     "find": "                p.poll() if p.returncode is None else judged(p)  # KILL-WATCH-SWEEP\n",
     "replace": "                pass  # KILL-WATCH-SWEEP\n",
     "matches": 1},
    {"why": "REG-2350 - a kill the run sent is never written, so a law that ends its own helper is UNKNOWN for ever",
     "file": "gate_trace/sitecustomize.py",
     "find": "            emit(\"X\", \"%s sig=%d\" % (who, sig))  # KILL-WATCH-SENT\n",
     "replace": "            pass  # KILL-WATCH-SENT\n",
     "matches": 1},
    {"why": "REG-2350 - a 0 probe is written as a kill and explains away a real outside kill of the same pid",
     "file": "gate_trace/sitecustomize.py",
     "find": "            if not sig:\n                return  # a probe (signal 0) ends nothing\n",
     "replace": "            if False:\n                return  # a probe (signal 0) ends nothing\n",
     "matches": 1},
    {"why": "REG-2350 - two copies of the trace hook on sys.path chain into each other (~160 boots in one process)",
     "file": "gate_trace/sitecustomize.py",
     "find": "and not _is_trace_dir(p)]  # TRACE-CHAIN-ONCE\n",
     "replace": "]  # TRACE-CHAIN-ONCE\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
