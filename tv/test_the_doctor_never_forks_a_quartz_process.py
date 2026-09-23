# -*- coding: utf-8 -*-
"""v3429 (#150) — THE DOCTOR MUST NOT fork() A PROCESS THAT HAS LOADED THE OBJECTIVE-C RUNTIME.

`test_control HUNG — killed after 1500s on an IDLE machine` has refused FOUR pushes since
2026-09-20, and the standing diagnosis ("the cheap subset is over budget") was wrong. MEASURED
2026-09-23, back to back, same idle machine:

    run 1 — cd.run(include_slow=False) hung 28 MINUTES at 0.0% CPU and had to be killed
    run 2 — the SAME call FINISHED IN 15.4 SECONDS, 107 rows

⚠ SO IT IS A DEADLOCK, NOT A COST, and RESUME_HERE's ">8 min alone" measured the HUNG case. Its
own puzzle — "the whole is minutes; every part is seconds" — dissolves: the parts ARE seconds. A
hang must never be averaged with a cost.

WHAT IT IS, from the stuck process: the hung parent had exactly ONE child, at 0.0% CPU, with no
grandchildren, **wearing the PARENT'S OWN ARGV** — the signature of a `subprocess.Popen` caught
BETWEEN fork and exec — and holding Quartz / CoreGraphics / QuickLookUI / PyObjC. control_app and
health_engine import those, so by the time any check shells out the Obj-C runtime is initialised,
and forking such a process without immediately exec'ing is the macOS fork-safety deadlock. 0% CPU
for 28 minutes is a lock wait; a busy loop cannot produce it.

THE ESCAPE, PROVEN BY RECORDING WHICH SYSCALL CPYTHON ACTUALLY TAKES rather than reading its
conditions:

    close_fds default (True)          -> fork_exec x1, posix_spawn x0      <- the hang
    absolute exe + close_fds=False    -> posix_spawn x1, fork_exec x0
    bare name "ps" + close_fds=False  -> fork_exec x1                      <- dirname condition

⚠ BOTH HALVES ARE LOAD-BEARING and `close_fds` DEFAULTS TO TRUE, which is why every ordinary call
forks. ⚠ AND close_fds=False IS SCOPED TO SHORT-LIVED READS: the child inherits open descriptors,
which for a long-lived worker would mean holding this console's listening socket past a restart.
"""
import ast
import io
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

SRC = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8", errors="replace").read()


class _SyscallSpy(object):
    """Record which of fork_exec / posix_spawn CPython actually reaches for."""

    def __enter__(self):
        import _posixsubprocess
        self.counts = {"spawn": 0, "fork": 0}
        self._mod = _posixsubprocess
        self._rs, self._rf = os.posix_spawn, _posixsubprocess.fork_exec

        def spawn(*a, **k):
            self.counts["spawn"] += 1
            return self._rs(*a, **k)

        def fork(*a, **k):
            self.counts["fork"] += 1
            return self._rf(*a, **k)

        os.posix_spawn = spawn
        _posixsubprocess.fork_exec = fork
        return self

    def __exit__(self, *e):
        os.posix_spawn = self._rs
        self._mod.fork_exec = self._rf
        return False


class TestTheDoctorNeverForksAQuartzProcess(unittest.TestCase):

    # ---- driven on the real syscall ------------------------------------------------------

    def test_the_corpse_row_takes_posix_spawn_and_never_forks(self):
        """THE ONE THAT MATTERS. Not "does it pass the conditions" — does CPython take the
        non-forking path when this row actually runs."""
        import console_doctor as cd
        fn = dict(cd.CHECKS)["nothing we started is a corpse"]
        with _SyscallSpy() as spy:
            st, say = fn()
        self.assertEqual(spy.counts["fork"], 0,
                         "the doctor still fork()s a Quartz-loaded process — that is the 28-minute "
                         "deadlock path, and it refused four pushes (%s)" % say)
        self.assertGreaterEqual(spy.counts["spawn"], 1,
                                "nothing was spawned at all, so this case measured nothing")

    def test_the_baseline_shape_REALLY_DOES_fork(self):
        """⚠ THE PREMISE, PINNED. If a future CPython made close_fds=True spawn anyway, the case
        above would pass for a reason that has nothing to do with this fix, and the comments here
        would be describing a hazard that no longer exists."""
        with _SyscallSpy() as spy:
            subprocess.run(["/bin/ps", "-o", "pid="], stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, timeout=20)
        self.assertEqual(spy.counts["fork"], 1,
                         "the default shape no longer forks on this interpreter — re-measure "
                         "before trusting anything else in this file")

    def test_a_BARE_executable_name_still_forks(self):
        """The dirname condition is half the fix and it is invisible: `close_fds=False` alone reads
        like a complete change and still forks."""
        with _SyscallSpy() as spy:
            subprocess.run(["ps", "-o", "pid="], stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, close_fds=False, timeout=20)
        self.assertEqual(spy.counts["fork"], 1,
                         "a bare executable name no longer forks — the dirname condition changed")

    # ---- the class, so the next shell-out cannot reopen it --------------------------------

    def test_EVERY_subprocess_call_in_the_doctor_is_spawn_eligible(self):
        """A law about one row would have the reach the fix did. Any NEW shell-out added to this
        module is a new deadlock site unless it declares close_fds=False."""
        bad = []
        for node in ast.walk(ast.parse(SRC)):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in ("run", "Popen", "check_output", "call"):
                continue
            recv = node.func.value
            recv_name = getattr(recv, "id", "") or getattr(recv, "attr", "")
            if recv_name not in ("subprocess", "_sp", "sp"):
                continue
            kws = {k.arg for k in node.keywords if k.arg}
            if "close_fds" not in kws:
                bad.append(node.lineno)
        self.assertEqual(bad, [], "subprocess call(s) at line(s) %r in console_doctor do not "
                                  "declare close_fds, so they fork a process that has the "
                                  "Objective-C runtime loaded — the 28-minute hang" % (bad,))


RED_PROOF = [
    {
        "why": "v3429 - close_fds REMOVED. CPython takes posix_spawn only when close_fds is false, "
               "and it DEFAULTS TO TRUE - so dropping the keyword silently restores the fork that "
               "deadlocked for 28 minutes at 0% CPU and refused four pushes.",
        "file": "console_doctor.py",
        "find": "                      close_fds=False, timeout=15).stdout.decode(\"utf-8\", \"replace\")",
        "replace": "                      timeout=15).stdout.decode(\"utf-8\", \"replace\")",
        "matches": 1,
    },
    {
        "why": "v3429 - THE ABSOLUTE PATH REMOVED. The other half, and the invisible one: with a "
               "bare name the executable has no dirname, CPython's gate fails, and it forks again "
               "while close_fds=False makes the call LOOK fixed.",
        "file": "console_doctor.py",
        "find": "    _PS = \"/bin/ps\" if os.path.exists(\"/bin/ps\") else \"ps\"",
        "replace": "    _PS = \"ps\"",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
