# -*- coding: utf-8 -*-
"""REG-2613 (board #34) - THE BACKGROUND PROVER GOES THROUGH child_guard'S ONE DOOR: THE CONSOLE THAT STARTS IT OWNS IT.

self_prove.spawn started heart2 --prove with a bare Popen: on Windows nothing tied it to the console, so a console that
closed or crashed left a prover (and every gate process under it) running beside his game, and the next console could
start a second one. Elad 2026-10-23: put the prover under child_guard; prove it Windows-correct for Dean's PC and the
ALT (the Windows sync check), on the box and in CI.

  · DRIVEN: a real spawn goes through child_guard.spawn as role "prover"; on Windows it lands in a Job Object with
    KILL_ON_JOB_CLOSE and keeps its below-normal, no-window flags; on POSIX it leads its own session under nice.
  · DRIVEN: a law's recording popen never enters the real door's ledger (a fake pid there would be ended by pid).
  · DRIVEN: the watchdog knows a self-prover by the -X marker only self_prove's argv carries - a Windows command line
    with spaces in its paths included - and never takes a pre-push or hand-run `heart2.py --prove` for one.
  · DRIVEN: an orphaned self-prover (its console gone) is ended; one whose console lives is not.
  · DRIVEN: a prover that ended because ITS console ended is booked a stand-aside, never a failure and the 3 h backoff.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
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
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import child_guard as cg  # noqa: E402
import self_prove as SP  # noqa: E402
from test_child_guard_one_tree_per_role import _World, _FakeKernel32  # noqa: E402

WIN_PY = r"C:\Program Files\Python312\python.exe"
WIN_TV = r"C:\TV DIABLO\d2r-bible-tests\tv"


class _Recorder(object):
    def __init__(self):
        self.calls = []

    def door(self, role, argv, popen=None, **kw):
        self.calls.append((role, list(argv), dict(kw)))

        class _P(object):
            pid = 4242
        return _P()


class TheProverGoesThroughTheDoor(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="prover_door_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.log = os.path.join(self.d, "log")

    def test_a_real_spawn_uses_the_door_as_the_prover(self):
        rec = _Recorder()
        with mock.patch.object(SP, "_guard_spawn", rec.door):
            pid = SP.spawn(self.log, python=sys.executable, workers=1, names=["g1"])
        self.assertEqual(pid, 4242)
        self.assertEqual(len(rec.calls), 1, "the prover was started outside child_guard's door")
        role, argv, kw = rec.calls[0]
        self.assertEqual(role, "prover")
        self.assertEqual(cg.role_of_command(subprocess.list2cmdline(argv)), "prover",
                         "the watchdog cannot tell the self-prover's own command line apart")
        self.assertEqual(argv[-3:], ["--prove", "g1", "--slice"], "the slice shape changed")

    def test_on_windows_it_keeps_its_flags_and_takes_no_posix_kwarg(self):
        rec = _Recorder()
        pyw = os.path.join(self.d, "pythonw.exe")
        for n in ("pythonw.exe", "python.exe"):
            io.open(os.path.join(self.d, n), "w").close()
        with mock.patch.object(SP, "_guard_spawn", rec.door), mock.patch.object(SP, "IS_WIN", True):
            SP.spawn(self.log, python=pyw, workers=1)
        role, argv, kw = rec.calls[0]
        self.assertEqual(kw.get("creationflags"), SP._BELOW_NORMAL | SP._CREATE_NO_WINDOW,
                         "on Windows the prover lost its below-normal, no-window flags going through the door")
        self.assertNotIn("start_new_session", kw)
        self.assertNotEqual(argv[0], "/usr/bin/nice", "a Windows prover was started under a POSIX nice")
        self.assertTrue(argv[0].endswith("python.exe") and not argv[0].endswith("pythonw.exe"),
                        "pythonw (no stdout) would leave the prover's log empty: %r" % argv[0])

    def test_a_laws_recording_popen_never_enters_the_real_ledger(self):
        seen = []

        def popen(cmd, **kw):
            seen.append(cmd)

            class _P(object):
                pid = 4242
            return _P()
        with mock.patch.object(SP, "_guard_spawn", mock.Mock(side_effect=AssertionError("door"))):
            SP.spawn(self.log, popen=popen, workers=1)
        self.assertEqual(len(seen), 1)


class TheWatchdogKnowsASelfProver(unittest.TestCase):

    def _argv(self, win):
        rec = _Recorder()
        with mock.patch.object(SP, "_guard_spawn", rec.door), mock.patch.object(SP, "IS_WIN", win), \
                mock.patch.object(SP, "HERE", WIN_TV if win else HERE):
            SP.spawn(os.path.join(tempfile.gettempdir(), "prover_law.log"),
                     python=WIN_PY if win else sys.executable, workers=1, names=["g1"])
        return rec.calls[0][1]

    def test_a_windows_command_line_with_spaces_reads_as_the_prover(self):
        line = subprocess.list2cmdline(self._argv(True))    # what Win32_Process.CommandLine holds for Popen's list
        self.assertEqual(cg.role_of_command(line), "prover", line)
        self.assertIn(WIN_TV.lower(), line.lower(), "the checkout path the watchdog's query filters on is missing")

    def test_a_posix_command_line_reads_as_the_prover(self):
        self.assertEqual(cg.role_of_command(" ".join(self._argv(False))), "prover")

    def test_a_hand_run_or_pre_push_prover_is_never_the_watchdogs(self):
        for line in ("python3 %s/heart2.py --prove" % HERE,
                     subprocess.list2cmdline([WIN_PY, WIN_TV + r"\heart2.py", "--prove", "g1", "--slice"]),
                     "python3 heart2.py --prove-ci"):
            self.assertIsNone(cg.role_of_command(line), "a prover not started by self_prove read as one: %s" % line)

    def test_an_orphaned_self_prover_is_ended_and_a_live_consoles_is_not(self):
        line = subprocess.list2cmdline(self._argv(True))
        rows = [(9101, 9000, 500, line), (9102, 9001, 500, line)]
        alive = lambda pid: pid == 9001                       # noqa: E731 - console 9000 is gone, 9001 lives
        to_end, kept, strangers, bypass = cg.classify_unrecorded(rows, {}, {os.getpid()}, alive, lambda pid: 100)
        self.assertEqual([r[0] for r in to_end], [9101], "an orphaned prover was left running: %r" % (to_end,))
        self.assertEqual([r[0] for r in strangers], [9102], "a live console's prover was taken for an orphan")


class TheRealDoorOnWindows(_World):

    def test_the_prover_lands_in_a_job_that_kills_on_close(self):
        k32 = _FakeKernel32()
        log = os.path.join(self.d, "log")
        with mock.patch.object(cg, "IS_WIN", True), mock.patch.object(cg, "_kernel32", lambda: k32), \
                mock.patch.object(SP, "IS_WIN", True):
            SP.spawn(log, python=WIN_PY, workers=1, popen=self.popen([9990071], handle=4242), door=SP._guard_spawn)
            rec = cg.record_of("prover")
        self.assertIsNotNone(rec, "the prover holds no record in child_guard")
        self.assertIn(("AssignProcessToJobObject", 77, 4242), k32.calls,
                      "the prover was never put in a Job: Dean's console closing would leave it running")
        self.assertEqual(cg.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE, k32.flags)
        self.assertEqual(self.spawned[0][2].get("creationflags"), SP._BELOW_NORMAL | SP._CREATE_NO_WINDOW)

    def test_a_second_prover_ends_the_first(self):
        log = os.path.join(self.d, "log")
        popen = self.popen([9990081, 9990083])
        with mock.patch.object(SP, "IS_WIN", False):
            SP.spawn(log, python=sys.executable, workers=1, popen=popen, door=SP._guard_spawn)
            SP.spawn(log, python=sys.executable, workers=1, popen=popen, door=SP._guard_spawn)
        self.assertNotIn(9990081, self.live, "two provers of one checkout ran side by side")
        self.assertTrue(self.spawned[0][2].get("start_new_session"), "a POSIX prover did not lead its own session")


def _census(fp="fp1"):
    return {"state": "stale", "why": "fixture", "fingerprint": fp, "owed": 2,
            "owedGates": [("gate_a", 1), ("gate_b", 1)], "owedWhy": "fixture: 2 owed"}


class AProverEndedWithItsConsoleIsAStandAside(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="prover_console_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.store = os.path.join(self.d, ".self_prove.json")
        self._started = dict(SP._STARTED)
        SP._STARTED.update(pid=None, birth=None)
        self.addCleanup(lambda: (SP._STARTED.clear(), SP._STARTED.update(self._started)))
        for name, fake in (("identity", lambda pid, birth: False), ("_gate_costs", lambda path=None: {})):
            p = mock.patch.object(SP, name, fake)
            p.start()
            self.addCleanup(p.stop)

    def _ended(self, started_by):
        with io.open(self.store, "w", encoding="utf-8") as fh:
            json.dump({"pid": 4242, "pidBirth": 1.0, "startedFor": "fp1", "startedBy": started_by}, fh)
        SP.tick(now_s=time.time(), busy=3.0, tree=("installed", "fixture"), census=_census(), path=self.store,
                spawn_fn=lambda log_path, names=None: 999_999_3, env={}, playing=True, free=8000,
                kill_fn=lambda pid, birth=None: True)
        with io.open(self.store, encoding="utf-8") as fh:
            return json.load(fh)

    def test_a_prover_whose_console_ended_is_not_a_failure(self):
        mem = self._ended("1:a console that has ended")
        self.assertIsNone(mem.get("lastFailAt"), "a prover child_guard ended with its console was booked a FAILURE "
                                                 "and the 3 h backoff: %r" % mem)
        self.assertEqual(mem.get("stoodAside"), 1)

    def test_a_prover_that_ended_under_this_console_still_fails(self):
        mem = self._ended(SP.console_id())
        self.assertEqual(mem.get("lastFailKind"), "proof", "this console's own failed proof stopped being a failure")

    def test_a_start_records_its_console(self):
        with io.open(self.store, "w", encoding="utf-8") as fh:
            json.dump({}, fh)
        SP.tick(now_s=time.time(), busy=3.0, tree=("installed", "fixture"), census=_census(), path=self.store,
                spawn_fn=lambda log_path, names=None: 999_999_3, env={}, playing=False, free=8000,
                kill_fn=lambda pid, birth=None: True)
        with io.open(self.store, encoding="utf-8") as fh:
            mem = json.load(fh)
        self.assertEqual(mem.get("pid"), 999_999_3, "PREMISE: the tick did not start a proof: %r" % mem)
        self.assertEqual(mem.get("startedBy"), SP.console_id(), "a start did not record the console that owns it")


RED_PROOF = [
    {"why": "REG-2613 - the prover is started with a bare Popen again, outside child_guard's door",
     "file": "tv/self_prove.py",
     "find": "        if popen is None or door is not None:\n",
     "replace": "        if False:\n",
     "matches": 1},
    {"why": "REG-2613 - the prover's argv loses the marker, so the watchdog cannot tell it from any heart2 --prove",
     "file": "tv/self_prove.py",
     "find": "    cmd = ([py] + list(PROVER_MARK) + [",
     "replace": "    cmd = ([py] + [",
     "matches": 1},
    {"why": "REG-2613 - the role's signature is bare heart2.py --prove, so a hand-run or pre-push prover is ended",
     "file": "tv/child_guard.py",
     "find": "\"signature\": (\"-X tvd_self_prove\", \"heart2.py\"),",
     "replace": "\"signature\": (\"heart2.py\", \"--prove\"),",
     "matches": 1},
    {"why": "REG-2613 - the prover role carries no signature, so an orphaned prover is never ended",
     "file": "tv/child_guard.py",
     "find": "\"signature\": (\"-X tvd_self_prove\", \"heart2.py\"),",
     "replace": "\"signature\": (),",
     "matches": 1},
    {"why": "REG-2613 - a law's recording popen goes through the real door and its fake pid is ledgered",
     "file": "tv/self_prove.py",
     "find": "        if popen is None or door is not None:\n",
     "replace": "        if True:\n",
     "matches": 1},
    {"why": "REG-2613 - the console that started a prover is not recorded",
     "file": "tv/self_prove.py",
     "find": "            mem[\"startedBy\"] = console_id()",
     "replace": "            pass",
     "matches": 1},
    {"why": "REG-2613 - a prover ended with its console is booked a failure and the 3 h backoff",
     "file": "tv/self_prove.py",
     "find": "        elif mem.get(\"startedBy\") and mem.get(\"startedBy\") != console_id():\n",
     "replace": "        elif False:\n",
     "matches": 1},
    {"why": "REG-2613 - every ended prover reads as its console's end, so a real failed proof is never backed off",
     "file": "tv/self_prove.py",
     "find": "        elif mem.get(\"startedBy\") and mem.get(\"startedBy\") != console_id():\n",
     "replace": "        elif mem.get(\"startedBy\"):\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main()
