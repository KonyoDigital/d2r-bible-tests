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
  8. REG-2356 (the review of REG-2350): a signal of the law's own never explains a kill from outside. Each of these is
     UNKNOWN: a teardown that signals a helper already dead (killpg + kill, or a by-pid SIGTERM), a death reaped before
     the signal was sent, a signal of another number, a group member already dead, and a killpg of a pid that leads no
     group. The review's BLIND law banks nothing. The same teardown on a LIVE helper is still the law's own kill
     (PROVEN). The hook marks `dead=1` / `gone=` from real zombies and never reaps one to do it, and the reader is
     driven one rule at a time.
  9. REG-2358 (round 3): a signal explains only the FIRST death of each pid it reached - by pid, by group, to every
     process. The next death of that pid is a recycled pid's, and a signal sent before the first death never ended it.
     Round 4: and only a death before any other END of that pid. The review's shapes end a helper without a K - one
     that handles the law's SIGTERM and exits 0, one killed and dropped unwaited, one still running when its parent
     exits - and the next process to get its pid, killed from outside, read as the law's own kill. The hook says each
     of those ends (E), from the real hook; a forked copy says nothing about its parent's children; and through the
     real prover such a run is UNKNOWN and banks nothing. The OS cannot be asked to hand a pid out again, so that next
     process's death is written as the hook writes one.
 10. REG-2357 (round 3): every case of 1-8 skips off POSIX, so on Windows a proof that declared no need filed BLIND and
     shut every lock there. Every proof declares "posix-signals": on Windows each one is ELSEWHERE and never run (a
     class that runs everywhere checks both).
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
from unittest import mock

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
import gc, io, os, signal, subprocess, sys, time, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import subject

#: REG-2358 (round 4) - a helper that handles SIGTERM by exiting 0: its end is no death by a signal
GRACEFUL = ("import signal, sys, time; signal.signal(signal.SIGTERM, lambda *a: sys.exit(0)); print('ready', flush=True);"
            " time.sleep(30)")


def zombie(pid):
    """until `pid` is a ZOMBIE (dead, not yet reaped by this law) or gone"""
    for _ in range(400):
        st = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], stdout=subprocess.PIPE,
                            universal_newlines=True).stdout.strip()
        if not st or st.startswith("Z"):
            return
        time.sleep(0.05)


def outside(pid):
    """killed from OUTSIDE the run (a shell sends it, so no X line - jetsam and a by-pid reap write none either), and
    waited on until it is a ZOMBIE: dead, and not yet reaped by this law"""
    subprocess.run(["/bin/sh", "-c", "kill -9 %d" % pid])
    zombie(pid)


def recycled(pid, sig):
    """REG-2358 (round 4) - the NEXT process to get `pid` (a child of this run), killed from OUTSIDE by `sig`. The OS
    cannot be asked to hand a pid out again, so its death is written exactly as the hook writes one"""
    with io.open(os.environ["TV_GATE_KILLS"], "a", encoding="utf-8") as fh:
        fh.write("K\t%d\tpid=%d pgid=- sig=%d head=sleep\n" % (os.getpid(), pid, sig))


def teardown(p):
    """child_guard._kill_tree_default's shape: the group, then the pid, never polled first, then reaped"""
    for f in (lambda: os.killpg(p.pid, signal.SIGKILL), lambda: os.kill(p.pid, signal.SIGKILL)):
        try:
            f()
        except OSError:
            pass
    p.wait()


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
        # REG-2356 - each mode below is red ONLY because a helper was killed from outside, and each one ends with a
        # signal of the law's own that once explained that kill away
        if m == "zombie_killpg":      # the reviewer's shape: the teardown signals a helper that is already dead
            p = subprocess.Popen(["sleep", "30"], start_new_session=True)
            outside(p.pid)
            teardown(p)
            self.fail("red only because its helper was killed from outside")
        if m == "zombie_oskill":      # the same with a by-pid SIGTERM that never polls first
            p = subprocess.Popen(["sleep", "30"])
            outside(p.pid)
            try:
                os.kill(p.pid, signal.SIGTERM)
            except OSError:
                pass
            p.wait()
            self.fail("red only because its helper was killed from outside")
        if m == "sigmismatch":        # the law's SIGTERM reached a LIVE helper that ignores it; a SIGKILL ended it
            p = subprocess.Popen(["/bin/sh", "-c", "trap '' TERM; echo ready; exec sleep 30"], stdout=subprocess.PIPE)
            p.stdout.readline()
            os.kill(p.pid, signal.SIGTERM)
            outside(p.pid)
            p.wait()
            p.stdout.close()
            self.fail("red only because its helper was killed from outside")
        if m in ("member_reaped", "member_zombie"):   # a member of the helper's group, killed from outside
            lead = subprocess.Popen(["sleep", "30"], preexec_fn=os.setpgrp)
            mem = subprocess.Popen(["sleep", "30"], preexec_fn=lambda: os.setpgid(0, lead.pid))
            mem.poll()                # its group is read while it is alive
            outside(mem.pid)
            if m == "member_reaped":
                mem.wait()            # reaped BEFORE the group is signalled
            os.killpg(lead.pid, signal.SIGKILL)
            lead.wait()
            mem.wait()
            self.fail("red only because a member of its helper's group was killed from outside")
        if m == "nonleader":          # a killpg of a pid that leads no group reaches no one (ESRCH)
            p = subprocess.Popen(["sleep", "30"])
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass
            outside(p.pid)
            p.wait()
            self.fail("red only because its helper was killed from outside")
        if m == "ownteardown":        # the control: the same teardown on a LIVE helper is the law's own kill
            p = subprocess.Popen(["sleep", "30"], start_new_session=True)
            teardown(p)
            self.fail("caught - this law ended its own helper on the way")
        # REG-2358 (round 4) - the law's signal ends a helper WITHOUT a K line, and the next process to get that pid is
        # killed from outside: red only because of that outside kill. The plain modes are the controls.
        if m in ("graceful", "graceful_recycled"):    # it handles the law's SIGTERM and exits 0
            p = subprocess.Popen([sys.executable, "-c", GRACEFUL], stdout=subprocess.PIPE)
            p.stdout.readline()
            p.terminate()
            p.wait()
            p.stdout.close()
            if m == "graceful_recycled":
                recycled(p.pid, signal.SIGTERM)
                self.fail("red only because the next process to get its helper's pid was killed from outside")
            self.fail("caught - this law ended its own helper on the way")
        if m in ("dropped", "dropped_recycled"):      # killed and dropped unwaited: Popen's own finalizer reaps it
            p = subprocess.Popen(["sleep", "30"])
            pid = p.pid
            p.kill()
            zombie(pid)
            del p
            gc.collect()
            if m == "dropped_recycled":
                recycled(pid, signal.SIGKILL)
                self.fail("red only because the next process to get its helper's pid was killed from outside")
            self.fail("caught - this law ended its own helper on the way")


if __name__ == "__main__":
    unittest.main()
'''

#: REG-2358 (round 4) - every probe mode that ends a helper without a K and then has its pid's next process killed from
#: outside, and its control (the same end, no outside kill: judged as before)
ENDED_THEN_RECYCLED = (
    ("graceful_recycled", "graceful", "a helper that handled the law's SIGTERM and exited 0"),
    ("dropped_recycled", "dropped", "a helper the law killed and dropped unwaited (reaped by Popen's own finalizer)"),
)

#: REG-2356 - every probe mode that is red only because of a kill from outside, and the rule that makes each UNKNOWN
OUTSIDE_THEN_SIGNALLED = (
    ("zombie_killpg", "a teardown that signals (killpg, then kill) a helper already killed from outside"),
    ("zombie_oskill", "a by-pid SIGTERM to a helper already killed from outside"),
    ("sigmismatch", "a SIGTERM the helper ignored, then a SIGKILL from outside: another signal number"),
    ("member_reaped", "a group member killed from outside and reaped BEFORE its group was signalled"),
    ("member_zombie", "a group member killed from outside and not yet reaped when its group was signalled"),
    ("nonleader", "a killpg of a pid that leads no group, which reached no one"),
)

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
for m in ("ok", "red", "selfkill", "exit137", "exit2", "grandchild", "greenkill", "ownkill", "groupkill",
          "pipe") + %(outside)r + ("ownteardown",) + %(ended)r:
    mode(m)
    ok, tail = H._run_gate_once(TV, "probe_gate.py", timeout=60)
    once[m] = [ok, str(tail)[:300]]
OUT["once"] = once

mode("ok")
OUT["prove_one"] = dict((m, H._prove_one(TV, "probe", "probe_gate.py", proof(m), 0, say))
                        for m in ("red", "selfkill", "exit137", "grandchild", "greenkill", "ownkill", "groupkill",
                                  "zombie_killpg", "ownteardown", "graceful", "graceful_recycled"))

cache = H._VerdictCache(path=os.path.join(%(tmp)r, ".heart2_cache.json"), say=say)
H._PUSH = H._PushRun(order={}, browser=(), cache=cache)
try:
    OUT["push_killed"] = H._prove_push_one(TV, "probe", "probe_gate.py", proof("selfkill"), 0, say, {})
    OUT["push_killed_banked"] = len(cache.entries)
    OUT["push_red"] = H._prove_push_one(TV, "probe", "probe_gate.py", proof("red"), 1, say, {})
    OUT["push_red_banked"] = len(cache.entries)
    OUT["push_zombie"] = H._prove_push_one(TV, "probe", "probe_gate.py", proof("zombie_killpg"), 4, say, {})
    OUT["push_zombie_banked"] = len(cache.entries)
    OUT["push_recycled"] = H._prove_push_one(TV, "probe", "probe_gate.py", proof("graceful_recycled"), 5, say, {})
    OUT["push_recycled_banked"] = len(cache.entries)
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

#: REG-2356 - signals sent to children that were ALREADY dead (killed from outside, not yet reaped), and to a pid that
#: leads no group. Each X must say so before the signal leaves; nothing here may be reaped early by the watch.
ZOMBIES = r'''
import os, signal, subprocess, sys, time


def outside(pid):
    subprocess.run(["/bin/sh", "-c", "kill -9 %d" % pid])
    for _ in range(400):
        st = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], stdout=subprocess.PIPE,
                            universal_newlines=True).stdout.strip()
        if not st or st.startswith("Z"):
            return
        time.sleep(0.05)


a = subprocess.Popen(["sleep", "30"], start_new_session=True)          # a: killed from outside, THEN signalled
outside(a.pid)
try:
    os.killpg(a.pid, signal.SIGKILL)                                    # EPERM on macOS: a group of one zombie
except OSError:
    pass
os.kill(a.pid, signal.SIGKILL)       # a zombie takes a kill (POSIX). A watch that REAPED it first would make this raise
a.wait()
lead = subprocess.Popen(["sleep", "30"], preexec_fn=os.setpgrp)          # a group whose member is already dead
mem = subprocess.Popen(["sleep", "30"], preexec_fn=lambda: os.setpgid(0, lead.pid))
mem.poll()
outside(mem.pid)
os.killpg(lead.pid, signal.SIGKILL)
lead.wait()
mem.wait()
b = subprocess.Popen(["sleep", "30"])                                   # b: alive, and it leads no group
try:
    os.killpg(b.pid, signal.SIGTERM)
except OSError:
    pass
b.kill()
b.wait()
print("WATCHED-DONE %d %d %d %d %d" % (a.pid, lead.pid, mem.pid, b.pid, os.getpid()))
sys.stdout.flush()
os._exit(0)
'''

#: REG-2358 (round 4) - the review's three ways a child the law signalled ENDS WITHOUT A K, each of which must now say
#: that its pid ended: g handles SIGTERM and exits 0; d is killed and dropped unwaited (Popen's own finalizer reaps it);
#: l ignores SIGTERM and is still running when this process exits normally (its exit sweep leaves it to init).
ENDS = r'''
import gc, os, signal, subprocess, sys, time
g = subprocess.Popen([sys.executable, "-c", "import signal, sys, time; signal.signal(signal.SIGTERM, lambda *a: "
                      "sys.exit(0)); print('ready', flush=True); time.sleep(30)"], stdout=subprocess.PIPE)
g.stdout.readline()
g.terminate()
g.wait()
g.stdout.close()
d = subprocess.Popen(["sleep", "30"])
dpid = d.pid
d.kill()
for _ in range(400):                  # until it is a zombie: the finalizer then reaps it at once
    st = subprocess.run(["ps", "-o", "stat=", "-p", str(dpid)], stdout=subprocess.PIPE,
                        universal_newlines=True).stdout.strip()
    if not st or st.startswith("Z"):
        break
    time.sleep(0.05)
del d
gc.collect()
l = subprocess.Popen(["/bin/sh", "-c", "trap '' TERM; echo ready; exec sleep 30"], stdout=subprocess.PIPE,
                     stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL)    # it outlives this process: no pipe of ours
l.stdout.readline()
os.kill(l.pid, signal.SIGTERM)        # ignored: it is still running when this process exits
print("WATCHED-DONE %d %d %d %d" % (g.pid, dpid, l.pid, os.getpid()))
sys.stdout.flush()
'''

#: REG-2358 (round 4) - a forked copy of a process inherits its Popen objects. There a wait answers ECHILD, which Popen
#: reads as an exit 0, and the copy's exit sweep runs over them too: the copy must say nothing of a child it never
#: started. Its line would land between the parent's own kill of e and e's death, and close the parent's own signal.
FORKED = r'''
import os, subprocess, sys
e = subprocess.Popen(["sleep", "30"])
r, w = os.pipe()
f = os.fork()
if f == 0:
    os.close(w)
    os.read(r, 1)                     # until the parent has signalled e
    e.wait()                          # not its child: ECHILD, read as an exit 0
    sys.exit(0)                       # a normal exit: the copy's exit sweep runs
os.close(r)
e.kill()
os.write(w, b"x")
os.waitpid(f, 0)
e.wait()
print("WATCHED-DONE %d %d %d" % (e.pid, f, os.getpid()))
sys.stdout.flush()
os._exit(0)
'''


def _kill_quietly(pid):
    try:
        os.kill(int(pid), signal.SIGKILL)
    except (OSError, ValueError):
        pass


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
        drv = DRIVER % {"here": HERE, "tv": tv, "tmp": cls.tmp,
                        "outside": tuple(m for m, _why in OUTSIDE_THEN_SIGNALLED),
                        "ended": tuple(m for pair in ENDED_THEN_RECYCLED for m in pair[:2])}
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

    def test_a_signal_of_the_law_never_explains_a_kill_from_outside(self):
        """REG-2356 - the review's finding: a helper killed from outside, then signalled by the law's own teardown
        before it was reaped, read as a death the run caused - an ordinary red."""
        o = self.out["once"]
        for m, shape in OUTSIDE_THEN_SIGNALLED:
            self.assertIsNone(o[m][0], "%s was explained away and read as a verdict: %s" % (shape, o[m]))
            self.assertIn("nothing in the run sent", o[m][1], "%s: not said as an outside kill: %s" % (shape, o[m]))
        self.assertIs(o["ownteardown"][0], False, "PREMISE: the same teardown on a LIVE helper is still the law's own "
                                                  "kill, judged as before: %s" % o["ownteardown"])

    def test_a_signal_never_explains_a_death_after_its_target_ended(self):
        """REG-2358 (round 4) - the review's shapes: the law's signal ends its helper WITHOUT a K (it exits 0, or it is
        dropped unwaited and Popen's finalizer reaps it), and the next process to get that pid is killed from outside.
        The run is UNKNOWN, never a red, and it banks nothing; the same end with no outside kill is judged as before."""
        o = self.out["once"]
        for m, control, shape in ENDED_THEN_RECYCLED:
            self.assertIs(o[control][0], False, "PREMISE: %s, with no kill from outside, is judged as before: %s"
                          % (shape, o[control]))
            self.assertIsNone(o[m][0], "%s, then the next process to get its pid killed from outside: the law's old "
                                       "signal explained that kill and the run read as a verdict: %s" % (shape, o[m]))
            self.assertIn("nothing in the run sent", o[m][1], "%s: not said as an outside kill: %s" % (shape, o[m]))
        p = self.out["prove_one"]
        self.assertEqual(p["graceful"], H.PROVEN, "PREMISE: a law that ends its graceful helper can still be proven")
        self.assertEqual(p["graceful_recycled"], H.UNPROVABLE, "a tamper red only because a recycled pid was killed from "
                                                               "outside was filed %s" % p["graceful_recycled"])
        self.assertEqual(self.out["push_recycled"], H.UNPROVABLE)
        self.assertEqual(self.out["push_recycled_banked"], self.out["push_red_banked"],
                         "a tampered run red only because a recycled pid was killed from outside was banked")

    def test_a_blind_law_whose_helper_was_killed_from_outside_banks_nothing(self):
        p = self.out["prove_one"]
        self.assertEqual(p["zombie_killpg"], H.UNPROVABLE, "a tamper red only because its helper was killed from "
                                                           "outside was filed %s" % p["zombie_killpg"])
        self.assertEqual(p["ownteardown"], H.PROVEN, "a law whose teardown kills its live helper can no longer be "
                                                     "proven: %s" % p["ownteardown"])
        self.assertEqual(self.out["push_zombie"], H.UNPROVABLE)
        self.assertEqual(self.out["push_zombie_banked"], self.out["push_red_banked"],
                         "a tampered run red only because its helper was killed from outside was banked")


@unittest.skipUnless(_POSIX, "no POSIX signals here")
class TheKillWatchSaysWhoSentIt(unittest.TestCase):
    """6 - gate_trace/sitecustomize.py's K and X lines, read by heart2._kills_in."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="h2watch.")
        self.addCleanup(shutil.rmtree, self.d, True)

    def _watched(self, script):
        fd, kills = tempfile.mkstemp(prefix="kills-", suffix=".tsv", dir=self.d)   # never a listing: it keeps this law keyable
        os.close(fd)
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

    def _read(self, text):
        p = os.path.join(self.d, "k.tsv")
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return [k["head"] for k in H._kills_in(p)]

    def test_the_reader_explains_by_pid_by_group_and_never_by_a_pipe(self):
        text = ("X\t1\tpid=100 sig=9\nK\t1\tpid=100 pgid=- sig=9 head=a\n"          # explained by pid
                "X\t1\tpgid=200 sig=15\nK\t1\tpid=200 pgid=- sig=15 head=b\n"       # a group leader, no pgid read
                "X\t1\tpgid=300 sig=15\nK\t1\tpid=301 pgid=300 sig=15 head=c\n"     # a member of a sent group
                "K\t1\tpid=400 pgid=7 sig=13 head=d\n"                               # a closed pipe
                "K\t1\tpid=500 pgid=7 sig=9 head=e\n"                                # from outside
                "garbage line\nK\t1\tpid=600 pgid=7 sig=x head=f\n")
        self.assertEqual(self._read(text), ["e"])
        self.assertEqual(self._read("X\t1\tall sig=9\n" + text), [], "a signal sent to every process explains every "
                                                                    "kill of its number below it")
        self.assertEqual(H._kills_in(os.path.join(self.d, "absent.tsv")), [], "an unreadable watch granted something")

    def test_the_reader_explains_only_by_a_signal_that_could_have_caused_the_death(self):
        """REG-2356 - one rule at a time; each fixture holds a K that the old reader explained away."""
        self.assertEqual(self._read("K\t1\tpid=700 pgid=- sig=9 head=g\nX\t1\tpid=700 sig=9\n"
                                    "K\t1\tpid=701 pgid=- sig=9 head=g2\nX\t1\tall sig=9\n"), ["g", "g2"],
                         "a death reaped BEFORE the signal was sent was explained by it")
        self.assertEqual(self._read("X\t1\tpid=800 sig=15\nK\t1\tpid=800 pgid=- sig=9 head=h\n"
                                    "X\t1\tall sig=15\nK\t1\tpid=801 pgid=- sig=9 head=h2\n"), ["h", "h2"],
                         "a SIGTERM explained a SIGKILL death")
        self.assertEqual(self._read("X\t1\tpgid=900 sig=9 dead=1\nX\t1\tpid=900 sig=9 dead=1\n"
                                    "K\t1\tpid=900 pgid=- sig=9 head=i\n"), ["i"],
                         "a signal sent to a pid that was ALREADY dead explained its death")
        self.assertEqual(self._read("X\t1\tpgid=1000 sig=9 gone=1001,1003\nK\t1\tpid=1001 pgid=1000 sig=9 head=j\n"
                                    "K\t1\tpid=1002 pgid=1000 sig=9 head=k\nK\t1\tpid=1000 pgid=1000 sig=9 head=l\n"),
                         ["j"], "a group member that was already dead when its group was signalled was explained "
                                "(or a live one, or the leader, was not)")

    def test_a_signal_explains_only_the_first_death_of_each_pid_it_reached(self):
        """REG-2358 - a pid that died once is a NEW process the next time it dies (the pid was recycled): no signal sent
        before the first death explains the second, by pid, by group or to every process."""
        self.assertEqual(self._read("X\t1\tpid=1100 sig=9\nK\t1\tpid=1100 pgid=- sig=9 head=m\n"
                                    "K\t1\tpid=1100 pgid=- sig=9 head=n\n"), ["n"],
                         "a signal the law sent its own helper explained a later death of whatever got that pid next")
        self.assertEqual(self._read("X\t1\tpgid=1200 sig=9\nK\t1\tpid=1201 pgid=1200 sig=9 head=o\n"
                                    "K\t1\tpid=1200 pgid=1200 sig=9 head=o2\nK\t1\tpid=1201 pgid=1200 sig=9 head=p\n"),
                         ["p"], "a group signal explained a second death of one of its members")
        self.assertEqual(self._read("X\t1\tall sig=9\nK\t1\tpid=1300 pgid=- sig=9 head=q\n"
                                    "K\t1\tpid=1300 pgid=- sig=9 head=r\n"), ["r"],
                         "a signal to every process explained a second death of the same pid")
        self.assertEqual(self._read("X\t1\tpid=1400 sig=9\nK\t1\tpid=1400 pgid=- sig=13 head=s0\n"
                                    "K\t1\tpid=1400 pgid=- sig=9 head=s\n"), ["s"],
                         "a death by a closed pipe left the X's one chance at that pid for the next process")
        self.assertEqual(self._read("X\t1\tpid=1500 sig=9\nK\t1\tpid=1500 pgid=- sig=9 head=t\n"
                                    "X\t1\tpid=1500 sig=9\nK\t1\tpid=1500 pgid=- sig=9 head=u\n"), [],
                         "PREMISE: the law killing the recycled pid AGAIN is its own kill again, each X its own death")
        self.assertEqual(self._read("X\t1\tpgid=1550 sig=9\nK\t1\tpid=1551 pgid=- sig=9 head=t2\n"
                                    "K\t1\tpid=1551 pgid=1550 sig=9 head=u2\n"), ["t2", "u2"],
                         "a death the group signal never reached still left it a chance at that pid's next process")

    def test_a_pid_that_ended_without_a_signal_is_a_new_process_next_time(self):
        """REG-2358 (round 4) - an E line (the pid ended with an exit code, or was left to init when the process that
        started it exited) closes every chance an X above it had at that pid, exactly as a death does."""
        self.assertEqual(self._read("X\t1\tpid=1600 sig=15\nE\t1\tpid=1600 rc=0 head=python3\n"
                                    "K\t1\tpid=1600 pgid=- sig=15 head=v\n"), ["v"],
                         "a helper that handled the law's SIGTERM and exited 0 left the X's chance at its pid open")
        self.assertEqual(self._read("X\t1\tpgid=1700 sig=9\nE\t1\tpid=1701 rc=1 head=a\n"
                                    "K\t1\tpid=1701 pgid=1700 sig=9 head=w\n"), ["w"],
                         "a group member that ended with an exit code left the group signal a chance at its pid")
        self.assertEqual(self._read("X\t1\tall sig=9\nE\t1\tpid=1800 rc=0 head=a\n"
                                    "K\t1\tpid=1800 pgid=- sig=9 head=x\n"), ["x"],
                         "a pid that ended with an exit code left a signal to every process a chance at it")
        self.assertEqual(self._read("X\t1\tpid=1900 sig=15\nE\t1\tpid=1900 rc=left head=sleep\n"
                                    "K\t1\tpid=1900 pgid=- sig=15 head=y\n"), ["y"],
                         "a child left to init when its parent exited kept the X's chance at its pid")
        self.assertEqual(self._read("X\t1\tpid=2000 sig=9\nE\t1\tpid=2001 rc=0 head=a\n"
                                    "K\t1\tpid=2000 pgid=- sig=9 head=z\n"
                                    "E\t1\tpid=2100 rc=0 head=a\nX\t1\tpid=2100 sig=9\n"
                                    "K\t1\tpid=2100 pgid=- sig=9 head=z2\n"), [],
                         "PREMISE: an end closes only its own pid, and an X sent after it is the next process's own kill")

    def test_a_child_that_ends_without_a_signal_says_its_pid_ended(self):
        """REG-2358 (round 4) - the review's script, through the real hook: each of the three ends is said, the law's own
        signals stay explained, and the next process to get any of those pids, killed from outside, is unexplained."""
        (gp, dp, lp, me), text, left = self._watched(ENDS)
        self.addCleanup(_kill_quietly, lp)            # still running (it ignores SIGTERM), now init's child
        for line, why in (("E\t%s\tpid=%s rc=0 " % (me, gp), "a helper that handled SIGTERM and exited 0"),
                          ("K\t%s\tpid=%s pgid=" % (me, dp), "a helper killed and dropped unwaited"),
                          ("E\t%s\tpid=%s rc=left " % (me, lp), "a helper still running when this process exited")):
            self.assertIn(line, text, "%s left no line saying its pid ended:\n%s" % (why, text))
        self.assertEqual(left, [], "PREMISE: the run's own signals are explained:\n%s" % text)
        nxt = "".join("K\t%s\tpid=%s pgid=- sig=%d head=next-%s\n" % (me, p, s, h)
                      for p, s, h in ((gp, 15, "g"), (dp, 9, "d"), (lp, 15, "l")))
        self.assertEqual(self._read(text + nxt), ["next-g", "next-d", "next-l"],
                         "the next process to get a pid the law had signalled, killed from outside, read as the law's "
                         "own kill:\n%s" % (text + nxt))

    def test_a_forked_copy_says_nothing_of_its_parents_children(self):
        """REG-2358 (round 4) - a forked copy inherits the Popen objects; their waitpid there answers ECHILD, which Popen
        reads as an exit 0. Said, that end would close the parent's own kill of the same child."""
        (ep, fp, me), text, left = self._watched(FORKED)
        self.assertEqual([ln for ln in text.splitlines() if ln.split("\t")[1:2] == [fp]], [],
                         "a forked copy wrote a line about a child it never started:\n%s" % text)
        self.assertIn("K\t%s\tpid=%s " % (me, ep), text, "PREMISE: the parent's own kill of its child was said")
        self.assertEqual(left, [], "the parent's own kill of its child read as a kill from outside:\n%s" % text)

    def test_a_signal_to_a_child_already_dead_says_so(self):
        """REG-2356 - the hook marks an X before its signal leaves, from real zombies, and never reaps one to do it."""
        (a, lead, mem, b, me), text, left = self._watched(ZOMBIES)
        for line, why in (("pgid=%s sig=9 dead=1" % a, "a killpg of a helper already dead"),
                          ("pid=%s sig=9 dead=1" % a, "a kill of a helper already dead"),
                          ("pgid=%s sig=9 gone=%s" % (lead, mem), "a killpg of a live leader whose member was dead"),
                          ("pgid=%s sig=15 dead=1" % b, "a killpg of a live pid that leads no group"),
                          ("pid=%s sig=9" % b, "a kill of a live child")):
            self.assertIn("X\t%s\t%s\n" % (me, line), text, "%s was not written as `%s`:\n%s" % (why, line, text))
        self.assertEqual(sorted(k["pid"] for k in left), sorted([a, mem]),
                         "the kills from outside are not exactly the two dead children:\n%s" % text)

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


class OnWindowsEveryProofIsElsewhere(unittest.TestCase):
    """REG-2357 (the round-3 review) - every case above skips off POSIX, so on Windows the clean run and the tampered
    run both skip everything: a proof that declared no need filed BLIND there, and one BLIND shuts every lock on that
    PC. Each proof declares "posix-signals", so REG-1686 files it ELSEWHERE there and never runs it. This class runs
    everywhere, Windows included."""

    def test_every_proof_declares_it_needs_posix_signals(self):
        bare = [i for i, pr in enumerate(RED_PROOF) if str(pr.get("needs") or "") not in H._OFF_POSIX_NEEDS]
        self.assertEqual(bare, [], "red-proof(s) %s declare no POSIX need: on Windows every case here skips, so each of "
                                   "them files BLIND there and shuts every lock on that PC" % bare)

    def test_on_windows_each_proof_is_elsewhere_and_never_run(self):
        d = tempfile.mkdtemp(prefix="h2win.")
        self.addCleanup(shutil.rmtree, d, True)
        runs, said = [], []
        with mock.patch.object(H.sys, "platform", "win32"), \
                mock.patch.object(H, "_run_gate", lambda *a, **k: runs.append(a) or (True, "Ran 17 tests | OK")):
            got = [H._prove_one(d, "test_a_killed_run_is_never_a_red", "test_a_killed_run_is_never_a_red.py", pr, i,
                                said.append) for i, pr in enumerate(RED_PROOF)]
        self.assertEqual(sorted(set(got)), [H.ELSEWHERE], "on Windows a proof of this law was filed %s" % got)
        self.assertEqual(runs, [], "on Windows this law was run for a proof it can never judge there")


RED_PROOF = [
    {"why": "REG-2350 - a law killed by a signal is read as a red again: a killed tampered run is banked PROVEN",
     "file": "heart2.py",
     "find": "    if rc < 0:\n        return -rc, \"the law was killed by %s\" % _signal_words(-rc)\n",
     "replace": "    if rc < -999:\n        return -rc, \"the law was killed by %s\" % _signal_words(-rc)\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - a shell's 128+N (a child killed by signal N) is read as a red again",
     "file": "heart2.py",
     "find": "    if rc - 128 in _SHELL_SIGNALS:\n",
     "replace": "    if False:\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - the kill watch is armed and never read: a helper killed from outside makes the law red, PROVEN",
     "file": "heart2.py",
     "find": "        _killed = _kills_in(_watch) if _watch else []\n",
     "replace": "        _killed = []\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - the run is never given the watch file, so no child's kill is ever written",
     "file": "heart2.py",
     "find": "    env[\"TV_GATE_KILLS\"] = path\n",
     "replace": "    env[\"TV_GATE_KILLS_OFF\"] = path\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - the hook is never put on the run's path, so nothing in the run watches its children",
     "file": "heart2.py",
     "find": "        env[\"PYTHONPATH\"] = hook_dir + (os.pathsep + old if old else \"\")  # KILL-WATCH-ARM\n",
     "replace": "        pass  # KILL-WATCH-ARM\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - a kill the law sent itself by pid is no longer explained: every law that ends its helper is "
            "UNKNOWN",
     "file": "heart2.py",
     "find": "                 and (x[\"all\"] or (\"pid\" in x and x[\"pid\"] == p)\n",
     "replace": "                 and (x[\"all\"] or False\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - a group kill of a leader whose group was never read is not explained",
     "file": "heart2.py",
     "find": "                      or (\"pgid\" in x and x[\"pgid\"] in (p, k.get(\"pgid\"))))]\n",
     "replace": "                      or (\"pgid\" in x and x[\"pgid\"] == k.get(\"pgid\")))]\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - a closed pipe (SIGPIPE) is read as a kill from outside",
     "file": "heart2.py",
     "find": "        if k[\"n\"] == _pipe:\n            continue\n",
     "replace": "        if k[\"n\"] == -1:\n            continue\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - a Ctrl-C leaves the prover's lanes and sandboxes running behind a KeyboardInterrupt",
     "file": "heart2.py",
     "find": "    for name in (\"SIGTERM\", \"SIGALRM\", \"SIGHUP\", \"SIGINT\"):  # REG-2350 - SIGINT\n",
     "replace": "    for name in (\"SIGTERM\", \"SIGALRM\", \"SIGHUP\"):  # REG-2350 - SIGINT\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - the narrow path credits a tampered subset that a signal ended",
     "file": "heart2.py",
     "find": "    if ok_t is False:\n        say(",
     "replace": "    if ok_t is not True:\n        say(",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - a child a signal ended is never written when it is waited on",
     "file": "gate_trace/sitecustomize.py",
     "find": "                judged(self)  # KILL-WATCH-WAIT\n",
     "replace": "                pass  # KILL-WATCH-WAIT\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - a child a signal ended is never written when it is polled (Chrome's teardown polls) - nor, since "
            "REG-2358 round 4, when Popen's own finalizer reaps it (dropped unwaited)",
     "file": "gate_trace/sitecustomize.py",
     "find": "                judged(self)  # KILL-WATCH-POLL\n",
     "replace": "                pass  # KILL-WATCH-POLL\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - a child nobody waited on (a jetsam'd Chrome) is never swept at exit",
     "file": "gate_trace/sitecustomize.py",
     "find": "                p.poll() if p.returncode is None else judged(p)  # KILL-WATCH-SWEEP\n",
     "replace": "                pass  # KILL-WATCH-SWEEP\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - a kill the run sent is never written, so a law that ends its own helper is UNKNOWN for ever",
     "file": "gate_trace/sitecustomize.py",
     "find": "            emit(\"X\", \"%s sig=%d%s\" % (who, sig, tail))  # KILL-WATCH-SENT\n",
     "replace": "            pass  # KILL-WATCH-SENT\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - a 0 probe is written as a kill and explains away a real outside kill of the same pid",
     "file": "gate_trace/sitecustomize.py",
     "find": "            if not sig:\n                return  # a probe (signal 0) ends nothing\n",
     "replace": "            if False:\n                return  # a probe (signal 0) ends nothing\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - two copies of the trace hook on sys.path chain into each other (~160 boots in one process)",
     "file": "gate_trace/sitecustomize.py",
     "find": "and not _is_trace_dir(p)]  # TRACE-CHAIN-ONCE\n",
     "replace": "]  # TRACE-CHAIN-ONCE\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2350 - a member of a group the law killed is not explained, only its leader",
     "file": "heart2.py",
     "find": "                      or (\"pgid\" in x and x[\"pgid\"] in (p, k.get(\"pgid\"))))]\n",
     "replace": "                      or (\"pgid\" in x and x[\"pgid\"] == p))]\n",
     "matches": 1, "needs": "posix-signals"},
    # REG-2356 - the review's finding: a teardown signal explained a kill from outside, and a BLIND law banked PROVEN
    {"why": "REG-2356 - a death reaped BEFORE the law's signal was sent is explained by it",
     "file": "heart2.py",
     "find": "                 if x[\"at\"] < k[\"at\"]  # KILL-WATCH-ORDER\n",
     "replace": "                 if True  # KILL-WATCH-ORDER\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2356 - a signal of another number explains a death (a SIGTERM the helper ignored explains a SIGKILL)",
     "file": "heart2.py",
     "find": "        if any(x[\"n\"] == k[\"n\"]  # KILL-WATCH-SAME-SIGNAL\n",
     "replace": "        if any(True  # KILL-WATCH-SAME-SIGNAL\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2356 - a group member already dead when its group was signalled is explained by that signal",
     "file": "heart2.py",
     "find": "               and p not in x[\"gone\"]  # KILL-WATCH-GONE-PID\n",
     "replace": "               and True  # KILL-WATCH-GONE-PID\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2356 - the reader ignores `dead=1`: a teardown signal to a helper killed from outside explains it",
     "file": "heart2.py",
     "find": "        if f.get(\"dead\") == \"1\":\n            continue  # KILL-WATCH-DEAD-X",
     "replace": "        if False:\n            continue  # KILL-WATCH-DEAD-X",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2356 - the hook never asks whether a signal's target is already dead: the review's BLIND is PROVEN",
     "file": "gate_trace/sitecustomize.py",
     "find": "            dead = unreachable(kind, n)  # KILL-WATCH-DEAD\n",
     "replace": "            dead = False  # KILL-WATCH-DEAD\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2356 - on macOS a zombie's ESRCH is read as alive, so a signal to it explains the kill from outside",
     "file": "gate_trace/sitecustomize.py",
     "find": "        except ProcessLookupError:\n            return True  # macOS: a zombie and a missing pid",
     "replace": "        except ProcessLookupError:\n            return False  # macOS: a zombie and a missing pid",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2356 - a killpg of a pid that leads no group (it reached no one) explains that pid's later death",
     "file": "gate_trace/sitecustomize.py",
     "find": "        if kind == \"pgid\" and g != n:\n            return True",
     "replace": "        if False:\n            return True",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2356 - a group's members already dead are never named, so the group signal explains their deaths",
     "file": "gate_trace/sitecustomize.py",
     "find": "                        late.append(\"%d\" % p.pid)  # KILL-WATCH-GONE\n",
     "replace": "                        pass  # KILL-WATCH-GONE\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2356 - the watch REAPS a dead child before its X (the poll-first fix): the law's own os.kill on that "
            "zombie then raises ESRCH where it succeeded, so the watch changes what the law does",
     "file": "gate_trace/sitecustomize.py",
     "find": "            dead = unreachable(kind, n)  # KILL-WATCH-DEAD\n",
     "replace": "            [p.poll() for p in list(st[\"live\"] or ()) if p.pid == n]\n"
                "            dead = unreachable(kind, n)  # KILL-WATCH-DEAD\n",
     "matches": 1, "needs": "posix-signals"},
    # REG-2358 - the round-3 review: a signal the law sent to its own helper explained the next death of that pid
    {"why": "REG-2358 - an X explains every later death of its pid: a recycled pid killed from outside reads as the "
            "law's own kill, and the run reads red",
     "file": "heart2.py",
     "find": "                 and x[\"at\"] > before  # KILL-WATCH-FIRST-END\n",
     "replace": "                 and True  # KILL-WATCH-FIRST-END\n",
     "matches": 1, "needs": "posix-signals"},
    # REG-2357 - the round-3 review: every case here skips off POSIX, and no proof said so, so Windows filed all of them BLIND
    {"why": "REG-2357 - the first proof declares no need: on Windows every case skips and it files BLIND, shutting every "
            "lock there",
     "file": "test_a_killed_run_is_never_a_red.py",
     "find": "     \"matches\": 1, \"needs\": \"posix-signals\"},\n    {\"why\": \"REG-2350 - a shell's 128+N",
     "replace": "     \"matches\": 1},\n    {\"why\": \"REG-2350 - a shell's 128+N",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2358 - no end of a pid is remembered, so an X explains the second death of its pid too",
     "file": "heart2.py",
     "find": "        last[p] = k[\"at\"]  # KILL-WATCH-ENDED\n",
     "replace": "        pass  # KILL-WATCH-ENDED\n",
     "matches": 1, "needs": "posix-signals"},
    # REG-2358 (round 4) - the review: an X's chance at a pid closed only on a K, so a target that ended any other way
    # left it open for the next process to get that pid
    {"why": "REG-2358 - the reader drops E lines: a helper that exited 0 on the law's SIGTERM leaves the X's chance at "
            "its pid open, and the next process to get it, killed from outside, reads as the law's own kill",
     "file": "heart2.py",
     "find": "_KILL_LINE = re.compile(r\"^([KXE])\\t\\d+\\t(.*)$\")\n",
     "replace": "_KILL_LINE = re.compile(r\"^([KX])\\t\\d+\\t(.*)$\")\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2358 - the hook writes no line for a child that ends with an exit code (a helper that handles SIGTERM)",
     "file": "gate_trace/sitecustomize.py",
     "find": "                    emit(\"E\", \"pid=%s rc=%d head=%s\" % (p.pid, rc, headof(p)))  # KILL-WATCH-END\n",
     "replace": "                    pass  # KILL-WATCH-END\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2358 - a child still running when its parent exits is left to init unsaid, so a signal the parent sent "
            "it explains the death of the next process to get its pid",
     "file": "gate_trace/sitecustomize.py",
     "find": "                    emit(\"E\", \"pid=%s rc=left head=%s\" % (p.pid, headof(p)))  # KILL-WATCH-LEFT\n",
     "replace": "                    pass  # KILL-WATCH-LEFT\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2358 - a forked copy says the end of its parent's child (ECHILD, read as exit 0), which closes the "
            "parent's own kill of it: a law that ends its helper after a fork reads UNKNOWN for ever",
     "file": "gate_trace/sitecustomize.py",
     "find": "        return p.__dict__.get(\"_tv_owner\", getpid()) == getpid()  # KILL-WATCH-OWNER\n",
     "replace": "        return True  # KILL-WATCH-OWNER\n",
     "matches": 1, "needs": "posix-signals"},
    {"why": "REG-2358 - nobody records which process started a child, so a forked copy says its parent's children's ends",
     "file": "gate_trace/sitecustomize.py",
     "find": "                        me.__dict__[\"_tv_owner\"] = getpid()  # KILL-WATCH-OWNED",
     "replace": "                        pass  # KILL-WATCH-OWNED",
     "matches": 1, "needs": "posix-signals"},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
