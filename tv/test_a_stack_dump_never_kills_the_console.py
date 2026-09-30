# -*- coding: utf-8 -*-
"""REG-1641 — ASKING THE CONSOLE FOR ITS STACKS MAY NEVER KILL IT.

control_app registers faulthandler on SIGUSR1 so a wedged console can say which frame holds the lock
(`kill -USR1 <pid>` -> every thread's stack on stderr). It registered with `chain=True`: after the
dump, a chained handler restores the PREVIOUS action and re-raises the signal, and SIGUSR1's previous
action is the default one - which TERMINATES the process. MEASURED 2026-10-01: the one SIGUSR1 ever
sent to his live console for a stack took it down; it was relaunched through start_tvd_mac.sh.

  · DRIVEN, the real module: a child imports control_app (the registration runs at import), starts a
    parked worker thread, sends ITSELF SIGUSR1, and must still be alive to print ALIVE, with a stack
    on stderr that names the parked worker - every thread, not only the one that took the signal.
  · A platform with no SIGUSR1 (Windows) is SKIPPED with its reason - the registration is guarded by
    the same hasattr, so there is nothing there to prove, and a skip is not a pass.
RED_PROOF below. [[the-cure-that-kills-the-patient]]
"""
import os
import signal
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_ledgers as _fx_ledgers  # noqa: E402  the child inherits the redirect
_fx_ledgers.redirect()

CHILD = r"""
import os, signal, sys, threading, time
sys.path.insert(0, %(here)r)
import control_app          # its stack-dump handler is registered at import

def _parked_worker_for_the_dump():
    time.sleep(30)

t = threading.Thread(target=_parked_worker_for_the_dump, daemon=True)
t.start()
time.sleep(0.2)
os.kill(os.getpid(), signal.SIGUSR1)
time.sleep(0.5)
print("ALIVE")
sys.stdout.flush()
"""


@unittest.skipIf(not hasattr(signal, "SIGUSR1"),
                 "this platform has no SIGUSR1; control_app guards the registration with the same hasattr")
class AStackDumpNeverKillsTheConsole(unittest.TestCase):

    def _run(self):
        return subprocess.run([sys.executable, "-c", CHILD % {"here": HERE}], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=180, cwd=HERE)

    def test_the_console_survives_its_own_stack_dump(self):
        r = self._run()
        self.assertNotEqual(r.returncode, -signal.SIGUSR1,
                            "the console DIED on SIGUSR1 - a stack request killed it (stderr tail: %s)"
                            % r.stderr[-400:])
        self.assertEqual(r.returncode, 0, "the child did not finish cleanly (exit %s): %s"
                         % (r.returncode, r.stderr[-900:]))
        self.assertIn("ALIVE", r.stdout, "the console did not outlive its stack dump")
        self.assertIn("most recent call first", r.stderr,
                      "no stack was printed - the signal answered nothing, so a wedged console could not "
                      "name the frame that holds its lock")
        self.assertIn("_parked_worker_for_the_dump", r.stderr,
                      "the dump named only the thread that took the signal - the frame holding the lock is on "
                      "ANOTHER thread, which is the whole reason this handler exists")


RED_PROOF = [
    {"why": "REG-1641 - the handler chains to SIGUSR1's default action again: a stack request kills his console",
     "file": "control_app.py",
     "find": "        _fh.register(_sig.SIGUSR1, all_threads=True, chain=False)\n",
     "replace": "        _fh.register(_sig.SIGUSR1, all_threads=True, chain=True)\n",
     "matches": 1},
    {"why": "REG-1641 - the dump names only the thread that took the signal, never the one holding the lock",
     "file": "control_app.py",
     "find": "        _fh.register(_sig.SIGUSR1, all_threads=True, chain=False)\n",
     "replace": "        _fh.register(_sig.SIGUSR1, all_threads=False, chain=False)\n",
     "matches": 1},
    {"why": "REG-1641 - nothing is registered: SIGUSR1 falls to its default and kills the console, stackless",
     "file": "control_app.py",
     "find": "        _fh.register(_sig.SIGUSR1, all_threads=True, chain=False)\n",
     "replace": "        pass\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
