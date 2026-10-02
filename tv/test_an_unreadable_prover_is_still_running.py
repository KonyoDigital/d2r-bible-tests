# -*- coding: utf-8 -*-
"""REG-1652 / REG-1653 — A PROVER WHOSE IDENTITY CANNOT BE READ RIGHT NOW IS STILL RUNNING, AND THE READ NEVER FORKS.

Raised by the v3537 cross-family eye, on REG-1643 (mine), and both reproduced by reading the code:

  REG-1652 — is_ours() answered False for a reused pid AND for a proc_birth() that returned None (ps timing out at
  3 s on a paging machine, ps refused, ps missing) while pid_alive() was still True. guard() and the tick read that
  False as "the proof ended": booked it, _forget() dropped the pid, and the prover ran on beside his game with nothing
  tracking it. The tick's `unverified` branch kept a live pid only when NO birth had ever been stored, and end_tree's
  wait after a kill ended on the same False - "gone" - for a prover that may have survived.
  REG-1653 — proc_birth() ran ["ps", ...] with the default close_fds=True INSIDE his console (the 10 s rescue loop calls
  guard(), and since REG-1643 every healthy tick of a running proof asks who holds the pid). With the Objective-C
  runtime loaded, a bare name or close_fds=True takes fork_exec, which has wedged a console for 28 minutes at 0% CPU.

  · DRIVEN: identity() - gone False, ours True, a stranger False, and alive-but-unreadable None in BOTH shapes.
  · DRIVEN: the real guard and the real tick keep an alive-but-unreadable prover tracked - never booked ended, never
    forgotten, never killed, nothing started beside it - and say which unknown it is.
  · DRIVEN: end_tree reports SURVIVED when the read fails after the signal (the signal itself is a recorder), on EVERY
    OS - REG-1724: it ran only where killpg exists, so the ALT read this law BLIND.
  · DRIVEN: the ps read takes the posix_spawn shape - an absolute exe, close_fds=False, no cwd.
Nothing here starts or signals a process. RED_PROOF below. [[unknown-stays-unknown]]
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import self_prove as SP  # noqa: E402

PID, BIRTH = 4242, "ps:Tue Sep 30 21:00:00 2026"


class _Store(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="unreadable_prover_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.store = os.path.join(self.d, ".self_prove.json")
        saved = dict(SP._STARTED)
        SP._STARTED.update(pid=None, birth=None)
        self.addCleanup(lambda: (SP._STARTED.clear(), SP._STARTED.update(saved)))

    def _running(self, birth=BIRTH, read=None):
        """a prover this lane started is ALIVE; `read` is what proc_birth answers NOW (None = ps did not answer)"""
        with io.open(self.store, "w", encoding="utf-8") as fh:
            json.dump({"pid": PID, "pidBirth": birth, "startedFor": "fp"}, fh)
        for name, fake in (("pid_alive", lambda pid: pid == PID), ("proc_birth", lambda pid: read)):
            p = mock.patch.object(SP, name, fake)
            p.start()
            self.addCleanup(p.stop)


class WhoHoldsThePid(_Store):

    def test_the_four_answers(self):
        with mock.patch.object(SP, "pid_alive", lambda pid: False):
            self.assertIs(SP.identity(PID, BIRTH), False, "a dead pid is not a running prover")
        with mock.patch.object(SP, "pid_alive", lambda pid: True):
            with mock.patch.object(SP, "proc_birth", lambda pid: BIRTH):
                self.assertIs(SP.identity(PID, BIRTH), True)
            with mock.patch.object(SP, "proc_birth", lambda pid: "ps:someone else"):
                self.assertIs(SP.identity(PID, BIRTH), False, "a reused pid was taken for the prover")
            with mock.patch.object(SP, "proc_birth", lambda pid: None):
                self.assertIsNone(SP.identity(PID, BIRTH), "a read that FAILED was answered as a fact")
            self.assertIsNone(SP.identity(PID, None), "no recorded birth was answered as a fact")

    def test_the_kill_question_stays_strict(self):
        with mock.patch.object(SP, "pid_alive", lambda pid: True), mock.patch.object(SP, "proc_birth", lambda pid: None):
            self.assertFalse(SP.is_ours(PID, BIRTH), "an identity that cannot be read was trusted with a kill")


class TheGuardAndTheTickKeepIt(_Store):

    def test_the_guard_does_not_book_it_ended(self):
        self._running(read=None)
        r = SP.guard(now_s=5000.0, path=self.store, playing=False, free=3000)
        mem = SP.load(self.store)
        self.assertEqual(mem.get("pid"), PID, "the guard forgot a prover that is still running: %r" % r)
        self.assertIsNone(mem.get("lastFailAt"), "an unreadable prover was booked as a failed proof")

    def test_the_tick_keeps_it_tracked_and_starts_nothing_beside_it(self):
        self._running(read=None)
        started = []
        r = SP.tick(now_s=5000.0, path=self.store, census={"state": "missing", "why": "fixture"},
                    tree=("installed", "fixture"), busy=0.0, playing=False, free=3000,
                    spawn_fn=lambda *a, **k: started.append(1) or {"pid": 1, "birth": None})
        mem = SP.load(self.store)
        self.assertEqual(mem.get("pid"), PID, "the tick forgot a prover that is still running: %r" % r)
        self.assertIsNone(mem.get("lastFailAt"), "an unreadable prover was booked as a failed proof")
        self.assertEqual(started, [], "a second prover was started beside one whose identity could not be read")
        self.assertEqual(r.get("key"), "running-unverified", r)
        self.assertIn("could not be read right now", str(r.get("say") or r.get("why") or r))

    def test_no_recorded_birth_keeps_its_own_words(self):
        self._running(birth=None, read=None)
        r = SP.tick(now_s=5000.0, path=self.store, census={"state": "missing", "why": "fixture"},
                    tree=("installed", "fixture"), busy=0.0, playing=False, free=3000,
                    spawn_fn=lambda *a, **k: {"pid": 1, "birth": None})
        self.assertEqual(r.get("key"), "running-unverified", r)
        self.assertIn("never recorded", str(r.get("say") or r.get("why") or r))


class TheWaitAfterTheKill(_Store):
    """REG-1724 - the wait after the signal is ONE loop on every OS, so the case that proves it runs on every OS. It
    sat in the posix-only class below, so on Windows its red-proof stayed green through its own defeat and the ALT
    read the law BLIND. Only the recorder standing in for the signal differs: taskkill there, killpg here."""

    def test_a_read_that_fails_after_the_signal_is_survived_not_gone(self):
        reads = iter([BIRTH])                           # ours before the signal, unreadable after it

        def _birth(pid):
            return next(reads, None)
        signalled = []
        if SP.IS_WIN:
            signal = mock.patch.object(SP.subprocess, "run", lambda argv, **kw: signalled.append(int(argv[2])))
        else:
            signal = mock.patch.object(SP.os, "killpg", lambda pid, sig: signalled.append(pid))
        with mock.patch.object(SP, "pid_alive", lambda pid: True), mock.patch.object(SP, "proc_birth", _birth), signal:
            gone = SP.end_tree(PID, BIRTH, wait_s=0.5)
        self.assertEqual(signalled, [PID], "PREMISE: the prover was not signalled")
        self.assertFalse(gone, "a prover whose identity could not be read after the kill was reported gone")


@unittest.skipIf(SP.IS_WIN, "the posix ps shape - Windows reads the birth through OpenProcess, no process")
class TheKillAndTheRead(_Store):

    def test_the_ps_read_takes_posix_spawn(self):
        seen = []

        class _R(object):
            returncode, stdout, stderr = 0, "S Tue Sep 30 21:00:00 2026\n", ""

        def _run(argv, **kw):
            seen.append((list(argv), kw))
            return _R()
        with mock.patch.object(SP.subprocess, "run", _run):
            got = SP.proc_birth(os.getpid())
        self.assertTrue(seen, "PREMISE: proc_birth never asked ps")
        argv, kw = seen[0]
        self.assertTrue(os.path.isabs(argv[0]), "a bare %r forks inside his console" % argv[0])
        self.assertIs(kw.get("close_fds"), False, "close_fds defaults to True, which forks")
        self.assertIsNone(kw.get("cwd"), "a cwd forks")
        self.assertTrue(got and got.startswith("ps:"), got)


RED_PROOF = [
    {"why": "REG-1652 - a read that failed is answered 'not ours' again: a live prover is booked ended and forgotten",
     "file": "self_prove.py",
     "find": "            return None                     # alive, and who it is cannot be read right now - never \"ended\"\n",
     "replace": "            return False\n",
     "matches": 1},
    {"why": "REG-1652 - the wait after a kill ends on a failed read again: a survivor is reported gone",
     "file": "self_prove.py",
     "find": "    while identity(pid, birth) is not False:\n",
     "replace": "    while is_ours(pid, birth):\n",
     "matches": 1},
    {"why": "REG-1653 - the birth read runs a bare ps again: fork_exec inside a process holding the ObjC runtime",
     "file": "self_prove.py",
     "find": "        r = subprocess.run([_ps, \"-o\", \"stat=,lstart=\", \"-p\", str(pid)], capture_output=True, text=True,\n",
     "replace": "        r = subprocess.run([\"ps\", \"-o\", \"stat=,lstart=\", \"-p\", str(pid)], capture_output=True, text=True,\n",
     "matches": 1, "needs": "posix"},
    {"why": "REG-1653 - the birth read drops close_fds=False: the default True forks",
     "file": "self_prove.py",
     "find": "                           encoding=\"utf-8\", errors=\"replace\", close_fds=False,\n                           timeout=3, env=dict(os.environ, LC_ALL=\"C\", TZ=\"UTC\"))\n",
     "replace": "                           encoding=\"utf-8\", errors=\"replace\",\n                           timeout=3, env=dict(os.environ, LC_ALL=\"C\", TZ=\"UTC\"))\n",
     "matches": 1, "needs": "posix"},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
