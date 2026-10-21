# -*- coding: utf-8 -*-
"""#225 — A RELAUNCH LEAVES A RECEIPT, A BOOT LEAVES A LOG, AND A WINDOWS CHILD WAITS FOR ITS PARENT.

⚠⚠ MEASURED 2026-09-24 over SSH on the Windows ALT box: its console died relaunching into v3419 — the new
process imported and fetched, then exited before its first beacon — and left NO trace, because pythonw drops
stdout and no log file existed. On Windows os.execv starts a NEW pid, so the child can contest the named mutex
and :17772 while the parent still holds them, and both checks exit quietly. Which one killed it is UNKNOWN;
this makes the next death say. DRIVEN on temp files (never his tv/ stores) plus an AST pin on the ordering in
main(). The Windows half of wait_for_parent is measured on the ALT box, not simulated here. RED_PROOF below.

REG-2381 - and what a pythonw console SAYS is kept too: a None stdout/stderr is routed to tv/control_app.log, the file
the Mac's launcher appends to and console_doctor reads (APythonwConsoleKeepsWhatItSays).
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import win_relaunch as WR  # noqa: E402


class ARelaunchLeavesAReceipt(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="relaunch-receipt-")
        self._env = {k: os.environ.get(k) for k in ("TV_CONSOLE_BOOT_LOG", "TV_RELAUNCH_RECEIPT", WR.ENV_PARENT)}
        os.environ["TV_CONSOLE_BOOT_LOG"] = os.path.join(self.d, "boot.log")
        os.environ["TV_RELAUNCH_RECEIPT"] = os.path.join(self.d, "receipt.json")
        os.environ.pop(WR.ENV_PARENT, None)

    def tearDown(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.d, ignore_errors=True)

    def _log(self):
        with io.open(os.environ["TV_CONSOLE_BOOT_LOG"], encoding="utf-8") as fh:
            return fh.read()

    def test_a_boot_and_an_exit_reason_land_in_the_file(self):
        self.assertTrue(WR.boot_log("boot", ver="v9999"))
        self.assertTrue(WR.boot_log("exit-mutex-not-owned", port=17772))
        log = self._log()
        self.assertIn(" boot ", log)
        self.assertIn('"ver": "v9999"', log)
        self.assertIn("exit-mutex-not-owned", log, "the quiet exit left no reason on disk")

    def test_the_receipt_round_trips_and_names_the_parent(self):
        self.assertTrue(WR.write_receipt("_drift_loop", to_version="v9999"))
        r = WR.read_receipt()
        self.assertEqual((r["where"], r["fromPid"], r["toVersion"]), ("_drift_loop", os.getpid(), "v9999"))
        self.assertEqual(os.environ.get(WR.ENV_PARENT), str(os.getpid()),
                         "the child cannot know whom to wait for")

    def test_no_receipt_is_UNKNOWN_never_an_empty_one(self):
        self.assertIsNone(WR.read_receipt())
        io.open(os.environ["TV_RELAUNCH_RECEIPT"], "w").write("{not json")
        self.assertIsNone(WR.read_receipt())

    def test_on_POSIX_the_same_pid_has_nothing_to_wait_for(self):
        os.environ[WR.ENV_PARENT] = str(os.getpid())
        w = WR.wait_for_parent(timeout_s=1)
        self.assertEqual((w["parent"], w["waited"], w["exited"]), (os.getpid(), False, None))
        self.assertIn("same pid", w["why"])
        self.assertNotIn(WR.ENV_PARENT, os.environ, "the parent marker leaks into the next relaunch")
        self.assertIn("not a relaunch", WR.wait_for_parent()["why"])

    def test_an_uncaught_exception_at_boot_is_written_down(self):
        real = sys.excepthook
        sys.excepthook = lambda *a: None          # the previous hook the new one defers to
        try:
            hook = WR.install_excepthook()
            try:
                raise RuntimeError("boot blew up here")
            except RuntimeError:
                hook(*sys.exc_info())
        finally:
            sys.excepthook = real
        log = self._log()
        self.assertIn("uncaught-exception", log)
        self.assertIn("boot blew up here", log)


class AScratchConsoleNeverWritesThisMachinesRecord(unittest.TestCase):
    """MEASURED the day the log shipped: 8 of its 9 lines were render_check's served consoles booting
    beside his real one. A record padded with harness boots answers the ALT-death question wrongly."""

    KEYS = ("TV_CONSOLE_BOOT_LOG", "TV_RELAUNCH_RECEIPT", "TV_STUB", "TV_CONTROL_PORT")

    def setUp(self):
        self._env = {k: os.environ.get(k) for k in self.KEYS}
        for k in self.KEYS:
            os.environ.pop(k, None)

    def tearDown(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _mine(self):
        return (os.path.dirname(WR._log_path()) == HERE, os.path.dirname(WR._receipt_path()) == HERE)

    def test_the_real_console_writes_beside_its_code(self):
        self.assertEqual(self._mine(), (True, True), "premise: the machine's own console lost its record")
        os.environ["TV_CONTROL_PORT"] = "17772"
        self.assertEqual(self._mine(), (True, True), "the primary port was mistaken for a scratch one")

    def test_a_stub_agent_console_writes_elsewhere(self):
        os.environ["TV_STUB"] = "1"
        self.assertEqual(self._mine(), (False, False),
                         "a TV_STUB console (render_check, test launchers) wrote this machine's boot log")

    def test_a_scratch_port_console_writes_elsewhere(self):
        os.environ["TV_CONTROL_PORT"] = "17990"
        self.assertEqual(self._mine(), (False, False), "a console on a scratch port wrote this machine's record")

    def test_an_explicit_path_still_wins(self):
        os.environ["TV_STUB"] = "1"
        os.environ["TV_CONSOLE_BOOT_LOG"] = os.path.join(HERE, "x.log")
        self.assertEqual(WR._log_path(), os.path.join(HERE, "x.log"))


class MainWritesItDownBeforeItCanExitQuietly(unittest.TestCase):

    def setUp(self):
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.main = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "main"][0]
        self.calls = [n for n in ast.walk(self.main) if isinstance(n, ast.Call)]

    def _lines(self, attr=None, name=None):
        return sorted(c.lineno for c in self.calls
                      if (attr and isinstance(c.func, ast.Attribute) and c.func.attr == attr)
                      or (name and isinstance(c.func, ast.Name) and c.func.id == name))

    def test_the_parent_is_waited_for_before_the_mutex_is_contested(self):
        wait, mutex = self._lines(attr="wait_for_parent"), self._lines(name="_win_primary_mutex")
        self.assertTrue(wait and mutex, "premise: main() no longer waits for the parent or takes the mutex")
        self.assertLess(wait[0], mutex[0], "the child contests the mutex before its parent has exited")

    def test_both_quiet_exits_leave_a_reason(self):
        logs = [c for c in self.calls if isinstance(c.func, ast.Attribute) and c.func.attr == "boot_log"]
        events = {c.args[0].value for c in logs if c.args and isinstance(c.args[0], ast.Constant)}
        for ev in ("boot", "exit-mutex-not-owned", "bind-failed"):
            self.assertIn(ev, events, "main() exits without writing %r to the boot log" % ev)

    def test_every_exec_site_leaves_a_receipt(self):
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        f = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "_before_exec"][0]
        self.assertIn("write_receipt", {c.func.attr for c in ast.walk(f)
                                        if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)},
                      "_before_exec no longer leaves a relaunch receipt")


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
        "why": "#225 - a TV_STUB harness console writes this machine's boot log again (8 of 9 lines on 2026-09-24 were render_check's)",
        "file": "win_relaunch.py",
        "find": "    if os.environ.get(\"TV_STUB\") == \"1\":\n        return True\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#225 - a console on a scratch port is taken for the machine's own and writes its record",
        "file": "win_relaunch.py",
        "find": "    return bool(port) and port != PRIMARY_PORT\n",
        "replace": "    return False\n",
        "matches": 1,
    },
    {
        "why": "#225 - the boot log writes nothing: a pythonw death on Windows leaves no trace again (the v3419 ALT death)",
        "file": "win_relaunch.py",
        "find": "        with io.open(p, \"a\", encoding=\"utf-8\") as fh:\n            fh.write(line)\n        return True\n",
        "replace": "        return True\n",
        "matches": 1,
    },
    {
        "why": "#225 - the receipt no longer names the parent, so a Windows child cannot wait for it",
        "file": "win_relaunch.py",
        "find": "        os.environ[ENV_PARENT] = str(os.getpid())          # inherited by the exec'd child\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#225 - the mutex exit is quiet again: no reason on disk",
        "file": "control_app.py",
        "find": "            _wr and _wr.boot_log(\"exit-mutex-not-owned\", port=CONTROL_PORT)\n",
        "replace": "            pass\n",
        "matches": 1,
    },
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
