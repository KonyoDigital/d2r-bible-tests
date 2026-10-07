# -*- coding: utf-8 -*-
"""REG-1995 - A GATE BUSY AT ITS DEADLINE GETS ONE EXTENSION; A GATE QUIET AT ITS DEADLINE IS KILLED.

REG-1993 scaled the render's bound by the load measured when the render STARTS. On the v3603 push #6 the load at the
start was 3.8 (x1.0, 353 s) and the Grok Bot app began a tick two minutes in: load 15 with 2 minutes left. Load that
arrives after the start was not covered. So the gate wrapper in hooks/pre-push now asks again AT THE DEADLINE, for a
gate its caller marked GATE_LOAD_GRACE: busy then (1-min load above 5) and it is given ONE extension, to the measured
base x load/5 (capped 2.5x); quiet then, and it is killed exactly as before - a slow run on a quiet machine is the hang
this bound exists for.

Drives the hook's REAL perl wrapper (lifted out of hooks/pre-push) on `sleep`, with a stand-in `sysctl` first on PATH so
the load it reads is the case's, not the machine's.
"""
import io
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

HOOK = os.path.join(os.path.dirname(HERE), "hooks", "pre-push")
GRACE_EXPORT = '    export GATE_SCALE="${_rs:-1.00}" TV_RENDER_SCALE="${_rs:-1.00}" GATE_LOAD_GRACE=1\n'
GRACE_UNSET = '    unset GATE_SCALE TV_RENDER_SCALE GATE_LOAD_GRACE\n'


def _hook():
    with io.open(HOOK, encoding="utf-8") as fh:
        return fh.read()


def _wrapper():
    s = _hook()
    i = s.find("  perl -e 'my $t = shift;")
    if i < 0:
        return None
    i += len("  perl -e '")
    j = s.find("' \"$limit\" \"$@\"", i)
    return s[i:j] if j > i else None


@unittest.skipUnless(shutil.which("perl"), "perl is not installed")
class AGateBusyAtItsDeadlineGetsOneExtension(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="gategrace.")
        self.addCleanup(shutil.rmtree, self.d, True)
        prog = _wrapper()
        self.assertIsNotNone(prog, "the gate wrapper is gone from hooks/pre-push")
        self.wrap = os.path.join(self.d, "wrap.pl")
        with io.open(self.wrap, "w", encoding="utf-8") as fh:
            fh.write(prog)

    def _run(self, load, grace, limit=4, base=4, sleep_s=7):
        fake = os.path.join(self.d, "sysctl")
        with io.open(fake, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\necho '{ %s 1.00 1.00 }'\n" % load)
        os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
        env = dict(os.environ)
        env["PATH"] = self.d + os.pathsep + env.get("PATH", "")
        env.pop("GATE_LOAD_GRACE", None)
        if grace:
            env["GATE_LOAD_GRACE"] = "1"
        env["GATE_BASE"] = str(base)
        t0 = time.time()
        p = subprocess.run(["perl", self.wrap, str(limit), "sleep", str(sleep_s)], env=env, capture_output=True,
                           text=True, timeout=60)
        return p.returncode, time.time() - t0, p.stderr

    def test_busy_at_the_deadline_is_given_one_extension_and_finishes(self):
        rc, took, err = self._run("12.00", grace=True)
        self.assertEqual(rc, 0, "a gate busy at its deadline was killed (rc %s, %.1f s): %s" % (rc, took, err[-200:]))
        self.assertGreaterEqual(took, 6.5)
        self.assertIn("busy at the deadline (load 12.00) - one extension to 10s", err)

    def test_quiet_at_the_deadline_is_still_a_kill(self):
        rc, took, err = self._run("2.00", grace=True)
        self.assertEqual(rc, 142, "a gate QUIET at its deadline was not killed - the hang detector is gone")
        self.assertLess(took, 6.0)

    def test_without_the_mark_no_gate_is_extended(self):
        rc, took, err = self._run("12.00", grace=False)
        self.assertEqual(rc, 142, "a gate nobody marked was extended")
        self.assertLess(took, 6.0)

    def test_the_extension_is_one_and_bounded(self):
        rc, took, err = self._run("40.00", grace=True, limit=4, base=4, sleep_s=14)
        self.assertEqual(rc, 142, "the extension was not capped at 2.5x the measured base (4 s -> 10 s), or came twice")
        self.assertIn("one extension to 10s", err)
        self.assertLess(took, 12.5)

    def test_only_the_render_gate_is_marked(self):
        code = "\n".join(l for l in _hook().split("\n") if not l.lstrip().startswith("#"))
        self.assertEqual(code.count(GRACE_EXPORT), 1, "the render call site no longer marks its gate for the grace")
        self.assertEqual(code.count(GRACE_UNSET), 1, "the grace mark outlives the render gate")


RED_PROOF = [
    {"why": "REG-1995 - a gate busy at its deadline is killed again (load that arrived mid-run starves the render)",
     "file": "hooks/pre-push",
     "find": "             if ($grace) { $grace = 0;\n",
     "replace": "             if (0) { $grace = 0;\n",
     "matches": 1},
    {"why": "REG-1995 - the grace no longer asks the load: every marked gate is extended, quiet or not",
     "file": "hooks/pre-push",
     "find": "               my $s = $l > 5 ? $l / 5 : 1; $s = 2.5 if $s > 2.5;",
     "replace": "               my $s = 2.5;",
     "matches": 1},
    {"why": "REG-1995 - the render call site never marks its gate, so the grace never applies to it",
     "file": "hooks/pre-push",
     "find": '    export GATE_SCALE="${_rs:-1.00}" TV_RENDER_SCALE="${_rs:-1.00}" GATE_LOAD_GRACE=1\n',
     "replace": '    export GATE_SCALE="${_rs:-1.00}" TV_RENDER_SCALE="${_rs:-1.00}"\n',
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
