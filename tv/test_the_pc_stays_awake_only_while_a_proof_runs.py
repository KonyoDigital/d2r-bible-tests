# -*- coding: utf-8 -*-
"""#170 (REG-2483) - THE PC STAYS AWAKE ONLY WHILE A PROOF RUNS, AND SLEEPS AGAIN THE MOMENT IT ENDS.

His ruling, 2026-10-21 22:45: *only while working* - Dean's laptop slept in the middle of a proof. tv/keep_awake.py is
the one door: SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED) on Windows, `caffeinate -i -w <pid>` on macOS,
and self_prove takes a hold for the prover it spawns AND for a running prover a relaunched console adopts.

What this pins, each against the code that would break it:
  * the flags are EXACTLY 0x80000001 - never the display flag (his screen still turns off), never away mode;
  * the hold is RELEASED (ES_CONTINUOUS alone, on the same thread that took it) when the block ends, when it raises,
    when the prover exits, and when the prover is killed - a hold never outlives the work;
  * a pid hold is idempotent, and a pid that cannot be waited on holds nothing;
  * macOS argv is exactly ['caffeinate', '-i', '-w', str(pid)]: bound to the pid, no -d / -u / -s;
  * self_prove holds a prover it spawns from its first second, and a relaunched console holds an ADOPTED prover again;
  * a law's stand-in pid is never held for real - whether the law hands its own spawn_fn or stubs SP.spawn or the
    process table instead (the REG-1628 chain law's route, which started three real caffeinates a run in the first
    cut) - while a pid the module's own doors verified still is.
Windows is driven through a fake kernel on every PC; one REAL macOS case watches caffeinate end within seconds of the
`sleep` it watches dying, and its red-proof declares "needs": "macos" so other PCs file it ELSEWHERE.
[[heart-first]] [[i-own-everything-i-start]]
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

import keep_awake as KA  # noqa: E402
import self_prove as SP  # noqa: E402

HOLD, RELEASE = 0x80000001, 0x80000000
INSTALLED = ("installed", "level with origin")
MISSING = {"state": "missing", "why": "never proved"}


class FakeKernel(object):
    """kernel32 as the module calls it. Every call is recorded with the THREAD that made it - the execution state is
    per thread, so a release on another thread would release nothing."""

    def __init__(self, unopenable=(), wait_raises=False):
        self.calls = []
        self.ends = {}
        self.unopenable = set(unopenable)
        self.wait_raises = wait_raises
        self.lock = threading.Lock()

    def _rec(self, *row):
        with self.lock:
            self.calls.append((threading.current_thread().ident,) + row)

    def SetThreadExecutionState(self, flags):
        self._rec("state", int(flags))
        return 0x80000000

    def OpenProcess(self, access, inherit, pid):
        self._rec("open", int(access), int(pid))
        if int(pid) in self.unopenable:
            return 0
        h = 70000 + int(pid)
        with self.lock:
            self.ends.setdefault(h, threading.Event())
        return h

    def WaitForSingleObject(self, h, ms):
        self._rec("wait", int(h), int(ms))
        if self.wait_raises:
            raise OSError("the wait itself failed")
        self.ends[h].wait(30)
        return 0

    def CloseHandle(self, h):
        self._rec("close", int(h))
        return 1

    def end(self, pid):
        """the process `pid` ends - its handle is signalled, exactly as a normal exit or a kill signals it"""
        self.ends[70000 + int(pid)].set()

    def states(self, thread=None):
        return [r[2] for r in self.calls if r[1] == "state" and (thread is None or r[0] == thread)]

    def threads_that_took(self):
        return [r[0] for r in self.calls if r[1] == "state" and r[2] == HOLD]


class _KeepAwakeCase(unittest.TestCase):
    PLATFORM = "win32"

    def setUp(self):
        self.k = FakeKernel()
        for name, val in (("_platform", lambda: self.PLATFORM), ("_kernel", lambda: self.k)):
            p = mock.patch.object(KA, name, val)
            p.start()
            self.addCleanup(p.stop)
        with KA._LOCK:
            KA._HOLDS.clear()
        KA._LOCAL.depth, KA._LOCAL.took = 0, False
        self.addCleanup(self._end_everything)

    def _end_everything(self):
        for k in [self.k] + list(getattr(self, "old_kernels", [])):
            for ev in list(k.ends.values()):
                ev.set()
        for t in list(threading.enumerate()):
            if t.name.startswith("keep-awake-"):
                t.join(5)
        with KA._LOCK:
            KA._HOLDS.clear()

    def _watcher(self, pid):
        for t in threading.enumerate():
            if t.name == "keep-awake-%d" % pid:
                return t
        return None

    def _released(self, pid):
        t = self._watcher(pid)
        if t is not None:
            t.join(5)
        return t is None or not t.is_alive()


class TheFlagsAreExactlySystemRequired(_KeepAwakeCase):

    def test_a_block_asks_for_0x80000001_and_releases_with_es_continuous_on_the_same_thread(self):
        me = threading.current_thread().ident
        with KA.held("a vault sweep"):
            inside = KA.status()
            self.assertEqual(self.k.states(me), [HOLD],
                             "the hold asked for %r - it must be ES_CONTINUOUS | ES_SYSTEM_REQUIRED and nothing "
                             "else (no display, no away mode)" % ["0x%08x" % s for s in self.k.states(me)])
        print("   block flags on this thread: %s" % ["0x%08x" % s for s in self.k.states(me)])
        self.assertTrue(inside["on"], "the block held nothing: %r" % inside)
        self.assertEqual(inside["holds"], 1, inside)
        self.assertEqual(self.k.states(me), [HOLD, RELEASE], "the block's hold was not released with ES_CONTINUOUS")
        after = KA.status()
        self.assertFalse(after["on"], "the hold outlived the block: %r" % after)
        self.assertEqual(after["holds"], 0, after)

    def test_a_block_that_raises_still_lets_the_pc_sleep(self):
        me = threading.current_thread().ident
        with self.assertRaises(ValueError):
            with KA.held("a sweep that fails"):
                raise ValueError("the work failed")
        self.assertEqual(self.k.states(me), [HOLD, RELEASE], "a block that raised kept the PC awake")
        self.assertFalse(KA.status()["on"])

    def test_nested_blocks_take_once_and_release_once(self):
        me = threading.current_thread().ident
        with KA.held("outer"):
            with KA.held("inner"):
                pass
            self.assertEqual(self.k.states(me), [HOLD],
                             "the inner block's end released the outer block's hold - the state is per thread")
        self.assertEqual(self.k.states(me), [HOLD, RELEASE])

    def test_the_door_never_names_a_display_or_away_flag(self):
        self.assertEqual(KA.HOLD_FLAGS, HOLD)
        self.assertEqual(KA.HOLD_FLAGS & 0x00000002, 0, "ES_DISPLAY_REQUIRED is in the hold")
        self.assertEqual(KA.HOLD_FLAGS & 0x00000040, 0, "ES_AWAYMODE_REQUIRED is in the hold")


class AProofsHoldEndsWithTheProof(_KeepAwakeCase):

    def test_a_proof_that_exits_releases_the_hold_on_its_own_thread(self):
        r = KA.hold_for_pid(4242, "a heart proof is running")
        self.assertTrue(r["held"], r)
        opened = [c for c in self.k.calls if c[1] == "open"]
        self.assertEqual([(c[2], c[3]) for c in opened], [(KA.SYNCHRONIZE, 4242)],
                         "the prover was not opened to WAIT on: %r" % opened)
        took = self.k.threads_that_took()
        self.assertEqual(len(took), 1, self.k.calls)
        self.assertNotEqual(took[0], threading.current_thread().ident,
                            "the pid hold was taken on the caller's thread - it would end with the caller, not "
                            "with the prover")
        self.assertTrue(KA.status()["on"], KA.status())
        self.k.end(4242)                                    # the proof finished
        self.assertTrue(self._released(4242), "the watcher never ended")
        self.assertEqual(self.k.states(took[0]), [HOLD, RELEASE],
                         "the proof ended and the hold was not released on the thread that took it")
        self.assertIn(("close", 70000 + 4242), [c[1:] for c in self.k.calls], "the process handle leaked")
        st = KA.status()
        print("   after the proof ended: %s" % st["why"])
        self.assertFalse(st["on"], st)

    def test_a_killed_prover_releases_the_hold_too(self):
        r = KA.hold_for_pid(5353, "a heart proof is running")
        self.assertTrue(r["held"], r)
        took = self.k.threads_that_took()
        self.k.end(5353)                                    # stood aside / stalled / crashed: the handle signals
        self.assertTrue(self._released(5353))
        self.assertEqual(self.k.states(took[0]), [HOLD, RELEASE], "a killed prover left the PC held awake")
        self.assertFalse(KA.status()["on"])

    def test_a_wait_that_fails_still_releases(self):
        self.k.wait_raises = True
        r = KA.hold_for_pid(5454, "a heart proof is running")
        self.assertTrue(self._released(5454))
        took = self.k.threads_that_took()
        self.assertTrue(took, r)
        self.assertEqual(self.k.states(took[0]), [HOLD, RELEASE], "a failed wait kept the PC held awake for good")
        self.assertFalse(KA.status()["on"])

    def test_a_pid_hold_is_idempotent(self):
        a = KA.hold_for_pid(6161, "x")
        b = KA.hold_for_pid(6161, "x")
        self.assertTrue(a["held"] and b["held"], (a, b))
        self.assertTrue(b.get("already"), b)
        self.assertEqual(len([c for c in self.k.calls if c[1] == "open"]), 1, "a second watcher was started")
        self.assertEqual(KA.status()["holds"], 1)

    def test_a_pid_that_cannot_be_waited_on_holds_nothing(self):
        self.k.unopenable.add(6262)
        r = KA.hold_for_pid(6262, "x")
        self.assertFalse(r["held"], r)
        self.assertEqual(self.k.states(), [], "a hold was taken for a process nothing can watch end")
        self.assertFalse(KA.status()["on"])


class AnOsWithNoDoorHoldsNothing(_KeepAwakeCase):
    PLATFORM = "linux"

    def test_it_says_so_and_holds_nothing(self):
        r = KA.hold_for_pid(4242, "x")
        self.assertFalse(r["held"], r)
        self.assertIn("no keep-awake door", r["why"])
        with KA.held("y"):
            self.assertFalse(KA.status()["on"])
        self.assertEqual(self.k.calls, [])


class TheMacHoldIsBoundToThePid(_KeepAwakeCase):
    PLATFORM = "darwin"

    class _Proc(object):
        def __init__(self):
            self.rc = None
            self.ended = threading.Event()

        def poll(self):
            return self.rc

        def wait(self, timeout=None):
            self.ended.wait(timeout if timeout is not None else 30)
            return self.rc

        def terminate(self):
            self.rc = -15
            self.ended.set()

        def kill(self):
            self.terminate()

    def setUp(self):
        super(TheMacHoldIsBoundToThePid, self).setUp()
        self.spawned = []

        def _spawn(argv):
            p = self._Proc()
            self.spawned.append((list(argv), p))
            return p
        p = mock.patch.object(KA, "_spawn", _spawn)
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(lambda: [pr.terminate() for _a, pr in self.spawned])

    def test_the_argv_is_exactly_caffeinate_i_w_pid(self):
        self.assertEqual(KA.caffeinate_argv(4242), ["caffeinate", "-i", "-w", "4242"])
        r = KA.hold_for_pid(4242, "a heart proof is running")
        self.assertTrue(r["held"], r)
        self.assertEqual([a for a, _p in self.spawned], [["caffeinate", "-i", "-w", "4242"]],
                         "the macOS hold is not bound to the prover's pid")
        for a, _p in self.spawned:
            for bad in ("-d", "-u", "-s", "-m"):
                self.assertNotIn(bad, a, "caffeinate was asked for %s - only idle sleep is ever held" % bad)

    def test_a_mac_block_is_bound_to_this_console_and_ended_with_the_block(self):
        with KA.held("a sweep"):
            self.assertEqual([a for a, _p in self.spawned], [["caffeinate", "-i", "-w", str(os.getpid())]])
            self.assertTrue(KA.status()["on"])
        self.assertIsNotNone(self.spawned[0][1].poll(), "the block ended and its caffeinate was left running")
        self.assertFalse(KA.status()["on"])


@unittest.skipUnless(sys.platform == "darwin" and os.path.isfile("/usr/bin/caffeinate"),
                     "the real caffeinate exists only on macOS - this case is judged there (\"needs\": \"macos\")")
class ARealMacHoldEndsWithItsProcess(unittest.TestCase):

    def test_caffeinate_ends_within_seconds_of_the_sleep_it_watches(self):
        with KA._LOCK:
            KA._HOLDS.clear()
        sleeper = subprocess.Popen(["/bin/sleep", "60"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, close_fds=False)
        self.addCleanup(lambda: (sleeper.poll() is None and sleeper.kill(), sleeper.wait()))
        r = KA.hold_for_pid(sleeper.pid, "a stand-in proof")
        rec = KA._HOLDS.get(("pid", sleeper.pid)) or {}
        caf = rec.get("proc")

        def _no_leftover():
            if caf is not None and caf.poll() is None:
                caf.kill()
                caf.wait(5)
        self.addCleanup(_no_leftover)
        self.assertTrue(r["held"], r)
        self.assertIsNotNone(caf, "no caffeinate was started")
        self.assertIsNone(caf.poll(), "caffeinate ended while the process it watches was still running")
        self.assertTrue(KA.status()["on"])
        sleeper.kill()
        sleeper.wait(5)
        t0 = time.time()
        while time.time() - t0 < 6 and (caf.poll() is None or KA.status()["on"]):
            time.sleep(0.1)
        took = time.time() - t0
        print("   caffeinate (pid %s) ended %.2f s after the watched process died" % (caf.pid, took))
        self.assertIsNotNone(caf.poll(), "caffeinate outlived the process it was bound to - the hold never ends")
        self.assertFalse(KA.status()["on"], "status still says held after the process ended: %r" % KA.status())


class SelfProveHoldsTheProofItRuns(_KeepAwakeCase):

    def setUp(self):
        super(SelfProveHoldsTheProofItRuns, self).setUp()
        self.dir = tempfile.mkdtemp(prefix="keep_awake_law_")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store = os.path.join(self.dir, ".self_prove.json")
        saved = dict(SP._STARTED)
        SP._STARTED.update(pid=None, birth=None)
        self.addCleanup(lambda: (SP._STARTED.clear(), SP._STARTED.update(saved)))
        p = mock.patch.object(SP, "AWAKE_DOOR", KA.hold_for_pid)
        p.start()
        self.addCleanup(p.stop)

    def _tick(self, spawn_fn):
        return SP.tick(now_s=5000.0, busy=3.0, tree=INSTALLED, census=MISSING, path=self.store,
                       spawn_fn=spawn_fn, env={}, playing=False, free=8000, sandbox=(True, ""))

    def test_a_spawned_proof_is_held_awake_from_its_first_second(self):
        with mock.patch.object(SP, "proc_birth", lambda pid: "b%s" % pid):
            r = self._tick(lambda log_path, names=None: 5151)
        self.assertEqual(SP.load(self.store).get("pid"), 5151, "PREMISE: the tick did not start the proof: %r" % r)
        held = [x["pid"] for x in KA.status()["list"]]
        print("   after the spawn: %s" % KA.status()["why"])
        self.assertEqual(held, [5151], "the proof was started and the PC was not held awake for it")
        self.assertEqual([c[2:] for c in self.k.calls if c[1] == "open"], [(KA.SYNCHRONIZE, 5151)])

    def test_a_relaunched_console_holds_an_adopted_prover_again(self):
        with io.open(self.store, "w", encoding="utf-8") as fh:
            json.dump({"pid": 6262, "pidBirth": "b6262", "startedFor": "fp"}, fh)
        never = []
        with mock.patch.object(SP, "pid_alive", lambda pid: pid == 6262), \
                mock.patch.object(SP, "proc_birth", lambda pid: "b6262" if pid == 6262 else None):
            self._tick(lambda *a, **k: never.append(1) or 1)
            self._tick(lambda *a, **k: never.append(1) or 1)
            self.assertEqual(never, [], "PREMISE: a second prover was started beside the adopted one")
            self.assertEqual(len(self.k.threads_that_took()), 1,
                             "the adopted prover was not held exactly once over two ticks: %r" % self.k.calls)
            # the console relaunches: the old process - and with it its watcher and its hold - is gone
            self.old_kernels = [self.k]
            self.k = FakeKernel()
            with KA._LOCK:
                KA._HOLDS.clear()
            self._tick(lambda *a, **k: never.append(1) or 1)
        self.assertEqual(len(self.k.threads_that_took()), 1,
                         "the relaunched console did not hold the prover it adopted: %r" % self.k.calls)
        self.assertEqual([x["pid"] for x in KA.status()["list"]], [6262])

    def test_a_laws_stand_in_pid_is_never_held_for_real(self):
        seen = []
        with mock.patch.object(SP, "AWAKE_DOOR", None), \
                mock.patch.object(KA, "hold_for_pid", lambda pid, why="": seen.append(pid) or {"held": True}):
            self.assertIsNone(SP._hold_awake(5151, real=False))
            self.assertEqual(seen, [], "a law's recording spawn held this PC awake for a process that is not there")
            SP._hold_awake(5151, real=True)
        self.assertEqual(seen, [5151], "a REAL prover was not held through keep_awake")


class AStandInProverIsNeverHeldForReal(unittest.TestCase):
    """The review of the first cut, 2026-10-22: self_prove judged a pid REAL from `spawn_fn is None` alone. The REG-1628
    chain law stubs SP.spawn, pid_alive and proc_birth instead and passes no spawn_fn - so each run of it started three
    REAL `caffeinate -i -w 5151` through ca._self_prove_guard -> SP.guard -> tick. With any process holding pid 5151,
    that caffeinate was reparented to launchd and kept the Mac awake after the law had exited, owned by nobody.

    Every route a law takes is driven here with keep_awake's REAL door (hold_for_pid, the one the tick asks when no law
    door is set) replaced by a recorder: a stubbed SP.spawn, a stubbed process table (pid_alive + proc_birth, or
    identity alone), and the chain law's own guard() route. A stand-in pid must never reach the door. And a process the
    REAL doors verify (this law's own pid - alive, its real start time recorded) is still held through it: a guard that
    held nothing at all would pass the first three cases alone."""

    STAND_IN, ADOPTED = 5151, 6262
    CENSUS = {"state": "stale", "why": "fixture", "fingerprint": "fp", "owed": 2,
              "owedGates": [("gate_c", 1), ("gate_d", 1)], "owedWhy": "fixture; 2 owed"}

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="keep_awake_standin_")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store = os.path.join(self.dir, ".self_prove.json")
        saved = dict(SP._STARTED)
        SP._STARTED.update(pid=None, birth=None)
        self.addCleanup(lambda: (SP._STARTED.clear(), SP._STARTED.update(saved)))
        self.door, self.caffeinates, self.ended = [], [], []

        def _door(pid, why=""):
            self.door.append(pid)
            return {"held": False, "pid": pid, "why": "recorded by the law - nothing is held"}

        def _no_caffeinate(argv):
            self.caffeinates.append(list(argv))
            raise OSError("this law starts no caffeinate")

        def _never_end(pid, birth=None, wait_s=None):
            self.ended.append(pid)
            return False
        self._never_end = _never_end
        for target, name, val in ((SP, "AWAKE_DOOR", None), (KA, "hold_for_pid", _door), (KA, "_spawn", _no_caffeinate),
                                  (SP, "end_tree", _never_end),
                                  (SP, "ensure_prover_deps", lambda *a, **k: {"ok": True, "installed": [], "why": "law"}),
                                  (SP, "sandbox_ready", lambda: (True, "")),
                                  (SP, "silent_bound_s", lambda *a, **k: 7200),
                                  (SP, "_gate_costs", lambda path=None: None)):
            p = mock.patch.object(target, name, val)
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        self.assertEqual(self.caffeinates, [], "a REAL caffeinate was asked for: %r" % self.caffeinates)
        self.assertEqual(self.ended, [], "PREMISE: the lane tried to end a process: %r" % self.ended)

    def _store(self, **mem):
        with io.open(self.store, "w", encoding="utf-8") as fh:
            json.dump(mem, fh)

    def _tick(self, **kw):
        args = dict(now_s=5000.0, busy=3.0, tree=INSTALLED, census=MISSING, path=self.store, spawn_fn=None, env={},
                    playing=False, free=8000, sandbox=(True, ""), kill_fn=self._never_end)
        args.update(kw)
        return SP.tick(**args)

    def _stand_in_spawn(self, started):
        return lambda log_path, names=None, **k: started.append(names) or self.STAND_IN

    def test_a_stubbed_spawn_is_never_held_for_real(self):
        started = []
        with mock.patch.object(SP, "spawn", self._stand_in_spawn(started)):
            r = self._tick()
        self.assertEqual((r.get("key"), started, SP.load(self.store).get("pid")), ("start", [None], self.STAND_IN),
                         "PREMISE: the tick did not start its stand-in proof through SP.spawn: %r" % (r,))
        print("   a stubbed SP.spawn started pid %d; the real door was asked for %r" % (self.STAND_IN, self.door))
        self.assertEqual(self.door, [], "a law's stand-in SP.spawn (no spawn_fn) reached keep_awake's REAL door - pid "
                                        "%d is whatever process owns that number on this PC" % self.STAND_IN)

    def test_a_stubbed_process_table_never_holds_an_adopted_pid(self):
        alive = lambda pid: pid == self.ADOPTED                                    # noqa: E731
        tables = (("pid_alive + proc_birth", {"pid_alive": alive,
                                              "proc_birth": lambda pid: "b6262" if pid == self.ADOPTED else None}),
                  ("identity", {"identity": lambda pid, birth: pid == self.ADOPTED}))
        for label, stubs in tables:
            self._store(pid=self.ADOPTED, pidBirth="b6262", startedFor="fp")
            started = []
            patches = [mock.patch.object(SP, n, f) for n, f in stubs.items()]
            patches.append(mock.patch.object(SP, "spawn", self._stand_in_spawn(started)))
            for p in patches:
                p.start()
            try:
                r = self._tick()
            finally:
                for p in reversed(patches):
                    p.stop()
            self.assertEqual((r.get("key"), started), ("running", []),
                             "PREMISE (%s): the lane did not adopt the stand-in prover: %r" % (label, r))
            self.assertEqual(self.door, [], "a stand-in process table (%s) made pid %d a prover, and the REAL door was "
                                            "asked to hold it" % (label, self.ADOPTED))

    def test_the_chain_laws_guard_route_holds_nothing(self):
        """REG-1628's own shape: the ended prover 4242, the next slice spawned as 5151 through guard(), then the lane's
        own tick adopting 5151 - every door stubbed, no spawn_fn anywhere."""
        self._store(pid=4242, pidBirth=1234.5, startedFor="fp", sliceGates=["gate_a", "gate_b"])
        started = []
        for name, fake in (("pid_alive", lambda pid: pid == self.STAND_IN),
                           ("proc_birth", lambda pid: 77.0 if pid == self.STAND_IN else None),
                           ("census_state", lambda: dict(self.CENSUS)),
                           ("tree_state", lambda git=None: INSTALLED),
                           ("spawn", self._stand_in_spawn(started))):
            p = mock.patch.object(SP, name, fake)
            p.start()
            self.addCleanup(p.stop)
        r = SP.guard(path=self.store, playing=False, free=8000.0, busy=5.0, kill_fn=self._never_end)
        self.assertEqual((len(started), SP.load(self.store).get("pid")), (1, self.STAND_IN),
                         "PREMISE: guard() did not start the next slice: %r" % (r,))
        r2 = SP.tick(path=self.store, playing=False, free=8000.0, busy=5.0, kill_fn=self._never_end, env={})
        self.assertEqual(r2.get("key"), "running", "PREMISE: the lane's tick did not adopt the stand-in: %r" % (r2,))
        print("   guard() then tick() over the chain law's stubs: the real door was asked for %r" % self.door)
        self.assertEqual(self.door, [], "the chain law's route reached keep_awake's REAL door for its stand-in pid")

    def test_a_process_the_real_doors_verify_is_held_through_the_real_door(self):
        me = os.getpid()
        birth = SP.proc_birth(me)
        self.assertIsNotNone(birth, "PREMISE: this PC cannot read a process's start time, so the lane cannot verify "
                                    "a prover here at all")
        self._store(pid=me, pidBirth=birth, startedFor="fp")
        started = []
        with mock.patch.object(SP, "spawn", self._stand_in_spawn(started)):   # nothing may start beside it
            r = self._tick()
        self.assertEqual((r.get("key"), started), ("running", []), "PREMISE: the lane did not adopt pid %d: %r"
                                                                   % (me, r))
        print("   a pid the real doors verified (this law, pid %d): the real door was asked for %r" % (me, self.door))
        self.assertEqual(self.door, [me], "a prover the module's OWN doors verified was not held through keep_awake "
                                          "- the guard holds nothing at all, and Dean's laptop sleeps mid-proof")


RED_PROOF = [
    {
        "why": "REG-2483 - the display flag joins the hold: his screen never turns off while a proof runs",
        "file": "keep_awake.py",
        "find": "HOLD_FLAGS = ES_CONTINUOUS | ES_SYSTEM_REQUIRED\n",
        "replace": "HOLD_FLAGS = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | 0x00000002\n",
        "matches": 1,
    },
    {
        "why": "REG-2483 - the proof's hold is never released: the PC stays awake after the proof ends, for as long "
               "as the console lives",
        "file": "keep_awake.py",
        "find": "                k.SetThreadExecutionState(RELEASE_FLAGS)\n",
        "replace": "                pass\n",
        "matches": 1,
    },
    {
        "why": "REG-2483 - a held() block is never released: the first sweep keeps the PC awake for good",
        "file": "keep_awake.py",
        "find": "                _kernel().SetThreadExecutionState(RELEASE_FLAGS)\n",
        "replace": "                pass\n",
        "matches": 1,
    },
    {
        "why": "REG-2483 - caffeinate is no longer bound to the pid (-w dropped): the Mac stays awake after the "
               "proof ends",
        "file": "keep_awake.py",
        "find": "    return [\"caffeinate\", \"-i\", \"-w\", str(int(pid))]\n",
        "replace": "    return [\"caffeinate\", \"-i\"]\n",
        "matches": 1,
    },
    {
        "why": "REG-2483 - the real spawn stops binding caffeinate to the pid it was handed: only a REAL caffeinate "
               "shows it outliving the process",
        "file": "keep_awake.py",
        "find": "    return subprocess.Popen(argv, executable=exe, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,\n",
        "replace": "    return subprocess.Popen(argv[:2] + [\"-t\", \"60\"], executable=exe, stdin=subprocess.DEVNULL, "
                   "stdout=subprocess.DEVNULL,\n",
        "matches": 1,
        "needs": "macos",
    },
    {
        "why": "REG-2483 - self_prove starts a proof and never holds the PC awake for it: Dean's laptop sleeps "
               "mid-proof again",
        "file": "self_prove.py",
        "find": "            _hold_awake(mem[\"pid\"], real=_real_prover(spawn_fn, \"spawn\"))  # REG-2483 - awake from its "
                "first second\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2483 - a relaunched console adopts a running prover and never holds the PC awake for it",
        "file": "self_prove.py",
        "find": "    if running:\n        _hold_awake(running, real=_real_prover(spawn_fn, \"pid_alive\", \"proc_birth\", "
                "\"identity\"))\n",
        "replace": "    if False:\n        _hold_awake(running, real=_real_prover(spawn_fn, \"pid_alive\", \"proc_birth\", "
                   "\"identity\"))\n",
        "matches": 1,
    },
    {
        "why": "REG-2483 (review) - 'real' is judged from spawn_fn alone again: a law that stubs SP.spawn or the process "
               "table starts a REAL caffeinate for its stand-in pid, and it outlives the law on any PC where that "
               "number is a live process",
        "file": "self_prove.py",
        "find": "        return all(g.get(d) is _REAL_DOORS.get(d) for d in doors) and bool(doors)\n",
        "replace": "        return True\n",
        "matches": 1,
    },
    {
        "why": "REG-2483 (review) - the guard refuses every pid, a verified prover too: nothing is ever held awake and "
               "Dean's laptop sleeps mid-proof - the stand-in cases alone cannot tell this from the fix",
        "file": "self_prove.py",
        "find": "        return all(g.get(d) is _REAL_DOORS.get(d) for d in doors) and bool(doors)\n",
        "replace": "        return False\n",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
