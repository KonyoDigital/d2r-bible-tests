# -*- coding: utf-8 -*-
"""REG-2466 (#170) — A SWEEP HOLDS THIS PC AWAKE FOR EXACTLY AS LONG AS IT RUNS, AND LETS GO ON A CRASH TOO.

His ruling 2026-10-21 (#170): "YES, ONLY WHILE WORKING" - Dean's laptop slept in the middle of a proof. Measured on his
PC 2026-10-22 (read-only powercfg): standby never on AC or battery, hibernate after 2 h on battery only, and the drop
that day was a lid close (Kernel-Power 42). So a hold matters on battery, never against a lid - low value for Dean, and
the cheapest correct thing: the console's vault and chronicle sweeps run inside tv/keep_awake.py's `held(why)` (Track
C's contract: this thread, the with-block; never raises), entered when the sweep starts and left when it ends.

THE LAW, with a STAND-IN keep_awake in sys.modules (the real one is never imported here) and the sweeps in a fixture
world (TV_HIST, the sweep lock and the swept memory in this law's scratch; the reader switch stubbed so each sweep stops
at its first step):
  · the vault sweep and the chronicle sweep each enter the hold before their first step and leave it after their last;
  · a crash that escapes the sweep still leaves the hold - and the crash is not swallowed;
  · with no keep_awake the sweep still runs and the record SAYS nothing was held.
RED_PROOF below. [[unknown-stays-unknown]]
"""
import os
import sys
import tempfile
import shutil
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp  # noqa: E402

fixture_tmp.contain()

import control_app as CA  # noqa: E402


class _Crash(BaseException):
    """A crash the sweep's own `except Exception` cannot catch - the shape that leaves a hold behind."""


class _Sweeps(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sweep-awake-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.events = []
        stub = types.ModuleType("keep_awake")
        events = self.events

        class _Hold(object):
            taken = True              # keep_awake.held() yields a token; a refusal is taken False, never a raise

            def __init__(self, why):
                self.why = why

            def __enter__(self):
                events.append(("enter", self.why))
                return {"taken": _Hold.taken, "why": self.why}

            def __exit__(self, et, ev, tb):
                events.append(("exit", et.__name__ if et else None))
                return False
        stub.held = _Hold
        self.Hold = _Hold
        stub.status = lambda: {"held": False}
        vault, chron = dict(CA._VAULT_JOB), dict(CA._CHRON_JOB)
        self.addCleanup(lambda: (CA._VAULT_JOB.clear(), CA._VAULT_JOB.update(vault)))
        self.addCleanup(lambda: (CA._CHRON_JOB.clear(), CA._CHRON_JOB.update(chron)))
        for p in (mock.patch.dict(os.environ, {"TV_HIST": self.tmp,
                                               "TV_SWEEP_LOCK": os.path.join(self.tmp, ".sweep.lock"),
                                               "TV_CHRON_SWEPT": os.path.join(self.tmp, "chronicle_swept.json")}),
                  mock.patch.dict(sys.modules, {"keep_awake": stub}),
                  mock.patch.object(CA, "KEEP_AWAKE_LAST", None)):
            p.start()
            self.addCleanup(p.stop)

    def first_step(self, raise_=None):
        """The sweep's first step, recorded; it stops the sweep there (a skip), or raises."""
        def _skip():
            self.events.append(("step",))
            if raise_ is not None:
                raise raise_
            return {"why": "stopped by the law at its first step", "grokOnly": False}
        p = mock.patch.object(CA, "_sweep_skipped_because_reader_is_grok", _skip)
        p.start()
        self.addCleanup(p.stop)


class TheHoldLastsExactlyAsLongAsTheSweep(_Sweeps):

    def test_the_vault_sweep_is_held_from_its_start_to_its_end(self):
        self.first_step()
        CA._vault_sweep_run(self.tmp, 1)
        self.assertEqual(self.events, [("enter", "vault sweep running"), ("step",), ("exit", None)],
                         "the PC was not held awake for exactly the vault sweep: %r" % self.events)
        self.assertIs(CA.KEEP_AWAKE_LAST["held"], True)

    def test_the_chronicle_sweep_is_held_from_its_start_to_its_end(self):
        self.first_step()
        CA._chron_sweep_run(self.tmp, 1)
        self.assertEqual(self.events, [("enter", "chronicle sweep running"), ("step",), ("exit", None)],
                         "the PC was not held awake for exactly the chronicle sweep: %r" % self.events)

    def test_a_sweep_that_fails_inside_still_lets_go(self):
        self.first_step(RuntimeError("a lane died"))
        CA._vault_sweep_run(self.tmp, 1)
        self.assertEqual(self.events[-1], ("exit", None), "a failed sweep left the PC held: %r" % self.events)
        self.assertEqual(CA._VAULT_JOB.get("phase"), "error", "PREMISE: the sweep did not fail")

    def test_a_crash_that_escapes_the_sweep_still_lets_go_and_is_not_swallowed(self):
        self.first_step(_Crash())
        with self.assertRaises(_Crash):
            CA._chron_sweep_run(self.tmp, 1)
        self.assertEqual(self.events, [("enter", "chronicle sweep running"), ("step",), ("exit", "_Crash")],
                         "a crash left the PC held awake: %r" % self.events)


class WithoutKeepAwakeItSaysSo(_Sweeps):

    def test_a_refused_hold_is_not_recorded_as_held(self):
        """REG-2466 round 2 - held() never raises; on Linux, or when SetThreadExecutionState answers 0, it yields
        taken False. The record must say NOT held, and the refused hold is still left (a Windows depth unwinds)."""
        self.Hold.taken = False
        self.first_step()
        CA._vault_sweep_run(self.tmp, 1)
        self.assertEqual(self.events, [("enter", "vault sweep running"), ("step",), ("exit", None)],
                         "a refused hold was not entered and left around the sweep: %r" % self.events)
        rec = CA.KEEP_AWAKE_LAST
        self.assertIs(rec["held"], False, "a refused hold was recorded as held: %r" % rec)
        self.assertIn("NOT held", rec["why"])

    def test_no_keep_awake_runs_the_sweep_and_says_nothing_was_held(self):
        self.first_step()
        with mock.patch.dict(sys.modules, {"keep_awake": None}):
            CA._vault_sweep_run(self.tmp, 1)
        self.assertEqual(self.events, [("step",)], "PREMISE: the sweep did not run")
        rec = CA.KEEP_AWAKE_LAST
        self.assertIs(rec["held"], False)
        self.assertIn("NOT held", rec["why"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2466 - the vault sweep runs unheld: the PC may sleep in the middle of it",
        "file": "control_app.py",
        "find": "@_held_awake(\"vault sweep\")\ndef _vault_sweep_run(",
        "replace": "def _vault_sweep_run(",
        "matches": 1,
    },
    {
        "why": "REG-2466 - the chronicle sweep runs unheld: the PC may sleep in the middle of it",
        "file": "control_app.py",
        "find": "@_held_awake(\"chronicle sweep\")\ndef _chron_sweep_run(",
        "replace": "def _chron_sweep_run(",
        "matches": 1,
    },
    {
        "why": "REG-2466 - a crash that escapes a sweep never lets go: the PC stays held awake after the work is gone",
        "file": "control_app.py",
        "find": "        cm, self.cm = self.cm, None\n        if cm is not None:\n",
        "replace": "        cm, self.cm = self.cm, None\n        if cm is not None and et is None:\n",
        "matches": 1,
    },
    {
        "why": "REG-2466 round 2 - 'held() returned' is read as 'it holds': a refused hold (taken False) is recorded as held",
        "file": "control_app.py",
        "find": "            if isinstance(tok, dict) and tok.get(\"taken\") is True:\n",
        "replace": "            if True:\n",
        "matches": 1,
    },
]
