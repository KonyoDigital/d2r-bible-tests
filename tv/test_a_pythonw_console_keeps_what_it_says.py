# -*- coding: utf-8 -*-
"""REG-2381 — A PYTHONW CONSOLE KEEPS WHAT IT SAYS: a None stdout/stderr is routed to tv/control_app.log.

pythonw (every Windows console) leaves sys.stdout and sys.stderr None, and print() to None is silent. MEASURED on Dean's
PC 2026-10-21: his console starts as pythonw.exe (start_tvd_win.log), there is no tv/control_app.log at all, and
console_doctor's hunt-economy eye answered "no console log on this machine ... unaskable for 48d (891 attempts)" -
every line the console printed, the CONSOLE BOOT marker that eye slices on included, went nowhere. His Mac's launcher
appends the same stream to that file. Adapted from Dean diff 04.

DRIVEN on a temp HERE with the streams set to None the way pythonw leaves them - his tv/ is never written - and the
doctor's own eye is asked to read what the routed console wrote (the join). A file of its own on purpose: the #225 law
(test_a_relaunch_leaves_a_receipt) keys on 7 files, and importing control_app here keys this one on the whole suite;
folded together, the relaunch law's proofs would re-prove on every test edit. [[the-unjoined-end]]  RED_PROOF below.
"""
import ast
import io
import os
import shutil
import sys
import tempfile
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


class APythonwConsoleKeepsWhatItSays(unittest.TestCase):
    """REG-2381 - MEASURED on Dean's PC 2026-10-21 (his console starts as pythonw.exe): no tv/control_app.log at all, so
    every print() of his console went nowhere and console_doctor's hunt-economy eye answered "no console log on this
    machine ... unaskable for 48d (891 attempts)"; his Mac's launcher appends the same stream to that file. DRIVEN on a
    temp HERE with the streams set to None the way pythonw leaves them - his tv/ is never written - and the doctor's
    own eye is asked to read what the routed console wrote."""

    def setUp(self):
        import control_app as CA
        self.CA = CA
        self.d = tempfile.mkdtemp(prefix="pythonw-log-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.tmp = os.path.join(self.d, "tmp")
        os.makedirs(self.tmp)
        env = mock.patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        for k in ("TV_STUB", "TV_CONTROL_PORT"):      # this machine's own console unless a case says otherwise
            os.environ.pop(k, None)

    def _route(self, out=None, err=None, size=None, say=("a console line",)):
        with mock.patch.object(self.CA, "HERE", self.d), mock.patch.object(sys, "stdout", out), \
                mock.patch.object(sys, "stderr", err), mock.patch("tempfile.gettempdir", lambda: self.tmp):
            if size is None:
                got = self.CA._route_pythonw_output()
            else:
                with mock.patch.object(self.CA.os.path, "getsize", lambda p: size):
                    got = self.CA._route_pythonw_output()
            routed = (sys.stdout, sys.stderr)
            if got:
                for line in say:
                    print(line, flush=True)
                if sys.stderr is not err:
                    sys.stderr.write("an error line\n")
                    sys.stderr.flush()
        for s in set(routed):
            if s is not None and s is not out and s is not err:
                s.close()
        return got

    def _read(self, p):
        with io.open(p, encoding="utf-8") as fh:
            return fh.read()

    def test_a_pythonw_console_writes_to_the_log_the_doctor_reads(self):
        import console_doctor as CD
        boot = "\U0001f680 CONSOLE BOOT v9999 pid=%d 2026-10-21T00:00:00" % os.getpid()
        got = self._route(say=(boot, "a console line"))
        self.assertEqual(got, os.path.join(self.d, "control_app.log"))
        log = self._read(got)
        self.assertIn("a console line", log, "a pythonw console's print went nowhere")
        self.assertIn("an error line", log, "a pythonw console's stderr went nowhere")
        with mock.patch.object(CD, "HERE", self.d):
            state, say = CD._check_the_hunt_is_buying_something()
        self.assertNotIn("no console log", say, "the doctor still cannot find the log the console wrote")
        self.assertIn("since this console booted", say,
                      "the doctor did not find the CONSOLE BOOT marker the routed console printed: %r" % ((state, say),))

    def test_a_console_with_its_own_streams_is_left_alone(self):
        buf = io.StringIO()
        self.assertIsNone(self._route(out=buf, err=buf))
        self.assertFalse(os.path.exists(os.path.join(self.d, "control_app.log")),
                         "a console that has a terminal had its output taken away")

    def test_only_the_missing_stream_is_routed(self):
        buf = io.StringIO()
        got = self._route(out=buf, err=None)
        self.assertEqual(got, os.path.join(self.d, "control_app.log"))
        self.assertIn("a console line", buf.getvalue(), "a stdout that existed was taken into the log")
        self.assertIn("an error line", self._read(got), "the missing stderr was not routed")

    def test_a_full_log_rolls_aside_first(self):
        with io.open(os.path.join(self.d, "control_app.log"), "w", encoding="utf-8") as fh:
            fh.write("old\n")
        self._route(size=self.CA.CONSOLE_LOG_ROLL_BYTES + 1)
        prev = os.path.join(self.d, "control_app.prev.log")
        self.assertTrue(os.path.exists(prev), "a full log was not rolled aside")
        self.assertEqual(self._read(prev), "old\n")
        self.assertNotIn("old", self._read(os.path.join(self.d, "control_app.log")))

    def test_a_scratch_console_never_writes_this_machines_log(self):
        os.environ["TV_STUB"] = "1"
        got = self._route()
        self.assertTrue(got and os.path.dirname(got) == self.tmp, "a TV_STUB console's log went to %r" % (got,))
        self.assertFalse(os.path.exists(os.path.join(self.d, "control_app.log")),
                         "a scratch console wrote this machine's console log - the doctor would slice on its boot")

    def test_main_routes_it_before_it_says_or_asks_anything(self):
        src = self._read(os.path.join(HERE, "control_app.py"))
        main =[n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "main"][0]
        calls = [n for n in ast.walk(main) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        route = sorted(c.lineno for c in calls if c.func.id == "_route_pythonw_output")
        said = sorted(c.lineno for c in calls if c.func.id in ("print", "status_payload"))
        self.assertTrue(route and said, "premise: main() no longer routes pythonw's output, or says nothing at all")
        self.assertLess(route[0], said[0], "main() prints or asks its status before a pythonw console can keep it")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2381 - pythonw's stdout is dropped again: every Windows console says nothing (Dean's PC, 48 days)",
        "file": "control_app.py",
        "find": "    if sys.stdout is None:\n        sys.stdout = fh\n",
        "replace": "    if False:\n        sys.stdout = fh\n",
        "matches": 1,
    },
    {
        "why": "REG-2381 - a console that has a terminal is routed too: its log file is opened and its output taken",
        "file": "control_app.py",
        "find": "    if sys.stdout is not None and sys.stderr is not None:\n        return None\n    try:\n        import win_relaunch as _wr_out\n",
        "replace": "    try:\n        import win_relaunch as _wr_out\n",
        "matches": 1,
    },
    {
        "why": "REG-2381 - main() no longer routes pythonw's output, so the doctor's log eye is blind on Windows again",
        "file": "control_app.py",
        "find": "    _route_pythonw_output()\n    try:\n        import frame_ref as _fr_console\n",
        "replace": "    try:\n        import frame_ref as _fr_console\n",
        "matches": 1,
    },
    {
        "why": "REG-2381 - a scratch (TV_STUB / scratch-port) console writes this machine's console log under pythonw",
        "file": "control_app.py",
        "find": "        _scratch = bool(_wr_out.scratch_console())\n",
        "replace": "        _scratch = False\n",
        "matches": 1,
    },
    {
        "why": "REG-2381 - the console log never rolls: under pythonw it grows without bound across every boot",
        "file": "control_app.py",
        "find": "            os.replace(p, os.path.splitext(p)[0] + \".prev.log\")\n",
        "replace": "            pass\n",
        "matches": 1,
    },
]
