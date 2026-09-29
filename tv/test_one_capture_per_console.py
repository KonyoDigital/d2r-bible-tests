# -*- coding: utf-8 -*-
"""REG-1502 — ONE CAPTURE PER CONSOLE, AND A CAPTURE NOBODY OWNS LEAVES.

His words, 2026-09-29: *"my boosteroid app keeps crashing on me! something is related to the console i think"*.
MEASURED on the ALT that afternoon: FIVE capture_win.ps1 alive at once - four children of one console (10:23, 10:44,
14:31, 14:42) and one from the day before (22,052 s of CPU) - each PrintWindow-ing his Boosteroid window every 400 ms.
Windows logged a low-virtual-memory condition every ~5 min; dwm.exe died of memory exhaustion (0xc00001ad) eight
times in an hour and Boosteroid hung and crashed with it. The console's stop was a taskkill whose result nobody read,
and the spawn's "is one running?" check and its pid write were not atomic.

Four joints, each DRIVEN through the real function with the Windows edges stubbed (never a real process, never the
live tv/ pid file):
  · the spawn: two starts at once spawn ONE capture, and the capture is told which console started it;
  · the stop: a kill that did not land is counted and said, never assumed;
  · the boot sweep: ends a capture only when it is not ours AND its console is gone; an unreadable process table
    ends nothing and says UNKNOWN;
  · the capture itself (capture_win.ps1 Get-LeaseVerdict): leaves when its console is gone, its lease withdrawn or
    handed on - run in real PowerShell wherever one exists (Windows, CI), skipped by name on a Mac without one.
RED_PROOF below.
"""
import io
import os
import re
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
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import control_app as ca  # noqa: E402


class _FakeProc(object):
    def __init__(self, pid):
        self.pid = pid

    def poll(self):
        return None


class _World(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="one_capture_")
        self.pidfile = os.path.join(self.d, "control_capture.pid")
        self.log = io.StringIO()
        self.saved = (ca._capture_proc, dict(ca._CAP_STOP), dict(ca._CAP_SWEEP))
        ca._capture_proc = None

    def tearDown(self):
        ca._capture_proc = self.saved[0]
        ca._CAP_STOP.clear()
        ca._CAP_STOP.update(self.saved[1])
        ca._CAP_SWEEP.clear()
        ca._CAP_SWEEP.update(self.saved[2])
        shutil.rmtree(self.d, ignore_errors=True)


class TheSpawnIsOneAtATime(_World):

    def _start_twice(self):
        spawned = []
        pids = iter((7001, 7002, 7003))

        def popen(args, **kw):
            time.sleep(0.3)                     # the window the race lived in
            p = _FakeProc(next(pids))
            spawned.append((p.pid, dict(kw.get("env") or {})))
            return p

        def alive(pid):
            return pid in [s[0] for s in spawned]

        with mock.patch.object(ca, "IS_WIN", True), \
                mock.patch.object(ca, "CAP_PID_PATH", self.pidfile), \
                mock.patch.object(ca.os.path, "isfile", lambda p: True if p == ca.CAPTURE_PS1 else os.path.exists(p)), \
                mock.patch.object(ca, "_stub_never_films", lambda **k: False), \
                mock.patch.object(ca, "_capture_off", lambda *a, **k: False), \
                mock.patch.object(ca, "_pid_alive", alive), \
                mock.patch.object(ca.subprocess, "Popen", popen):
            ts = [threading.Thread(target=ca._start_capture, args=({"PATH": "x"}, self.log)) for _ in range(2)]
            for t in ts:
                t.start()
            for t in ts:
                t.join(10)
        return spawned

    def test_two_starts_at_once_spawn_one_capture(self):
        spawned = self._start_twice()
        self.assertEqual(1, len(spawned),
                         "two starts at once spawned %d captures - the second pid write orphans the first" % len(spawned))

    def test_the_capture_is_told_which_console_started_it(self):
        spawned = self._start_twice()
        self.assertTrue(spawned)
        self.assertEqual(str(os.getpid()), spawned[0][1].get("TV_CONSOLE_PID"),
                         "the capture does not know its console - a crashed console leaves it filming forever")


class TheStopChecksItsKill(_World):

    def _stop(self, survives):
        ca._capture_proc = _FakeProc(8100)
        with io.open(self.pidfile, "w") as fh:
            fh.write("8100")
        with mock.patch.object(ca, "CAP_PID_PATH", self.pidfile), \
                mock.patch.object(ca, "_kill_pid", lambda pid, force=False: None), \
                mock.patch.object(ca, "_pid_alive", lambda pid: survives), \
                mock.patch.object(ca, "_log_fp", self.log):
            ca._CAP_STOP.update(survived=0, last=None)
            ca._stop_capture()

    def test_a_kill_that_did_not_land_is_counted_and_said(self):
        self._stop(survives=True)
        self.assertEqual(1, ca._CAP_STOP["survived"], "a capture that outlived its kill was assumed dead")
        self.assertIn("8100", (ca._CAP_STOP.get("last") or {}).get("say", ""))
        self.assertIn("outlived its kill", self.log.getvalue())
        self.assertFalse(os.path.exists(self.pidfile), "the lease was not withdrawn - the survivor would never leave")

    def test_a_kill_that_landed_says_nothing(self):
        self._stop(survives=False)
        self.assertEqual(0, ca._CAP_STOP["survived"])
        self.assertEqual("", self.log.getvalue())


class TheBootSweepEndsOnlyOrphans(_World):

    def test_the_rule(self):
        live = {10, 20}
        end, kept = ca.orphan_captures([(1, 10), (2, 99), (3, 0), (4, 20), (5, 99)], mine={4}, alive=lambda p: p in live)
        self.assertEqual([2, 3, 5], end, "the sweep ended the wrong captures")
        self.assertEqual([1, 4], [k for k, _w in kept])

    def test_the_sweep_ends_what_the_rule_says_and_says_what_would_not_end(self):
        gone = set()
        with mock.patch.object(ca, "CAP_PID_PATH", self.pidfile), mock.patch.object(ca, "_log_fp", self.log):
            st = ca._sweep_orphan_captures(rows_fn=lambda: [(31, 900), (32, 901), (33, 555)],
                                           kill=lambda pid: gone.add(pid) if pid != 32 else None,
                                           alive=lambda pid: pid == 555 or (pid in (31, 32, 33) and pid not in gone),
                                           now_ms=1)
        self.assertEqual([31], st["killed"])
        self.assertEqual([32], st["failed"], "a capture that would not end was reported as ended")
        self.assertEqual([33], st["kept"], "a capture whose console lives was ended")
        self.assertIn("would NOT end", st["say"])

    def test_an_unreadable_process_table_ends_nothing(self):
        killed = []
        st = ca._sweep_orphan_captures(rows_fn=lambda: None, kill=killed.append, alive=lambda p: True, now_ms=1)
        self.assertEqual([], killed)
        self.assertIsNone(st["found"], "an unreadable table was reported as 'found 0'")
        self.assertIn("UNKNOWN", st["say"])

    def test_the_rescue_loop_runs_it_once_and_status_and_the_doctor_carry_it(self):
        import inspect
        loop = inspect.getsource(ca._console_rescue_loop)
        self.assertIn("== CAPTURE_SWEEP_TICK", loop, "nothing runs the boot sweep")
        self.assertIn("_sweep_orphan_captures()", loop)
        src = inspect.getsource(ca)
        self.assertIn('"captureSweep": dict(_CAP_SWEEP)', src)
        self.assertIn('"one_capture", not _c_bad', src)


def _powershell():
    for exe in ("powershell.exe", "pwsh", "powershell"):
        p = shutil.which(exe)
        if p:
            return p
    return None


class TheCaptureLeavesByItself(unittest.TestCase):
    """capture_win.ps1's own verdict, in real PowerShell. Seen on the ALT's Windows PowerShell 5.1: 7/7."""

    CASES = (
        ("dead console", "999991", 30, None, "is gone"),
        ("inside the grace", "$PID", 3, None, ""),
        ("lease withdrawn", "$PID", 30, None, "withdrew"),
        ("a newer capture holds it", "$PID", 30, "5151", "newer capture"),
        ("my lease", "$PID", 30, "4242", ""),
        ("unreadable lease", "$PID", 30, "garbage", ""),
        ("no console pid given", "0", 30, "4242", ""),
    )

    def test_the_lease_verdict(self):
        ps = _powershell()
        if not ps:
            self.skipTest("no PowerShell on this machine - capture_win.ps1 is proven where it runs (Windows, CI)")
        src = io.open(os.path.join(HERE, "capture_win.ps1"), encoding="utf-8").read()
        m = re.search(r"(function Get-LeaseVerdict\(.*?\n\}\n)", src, re.S)
        self.assertIsNotNone(m, "capture_win.ps1 no longer defines Get-LeaseVerdict")
        self.assertRegex(src, r"Get-LeaseVerdict \$leasePath \$PID \$consolePid",
                         "the capture loop no longer asks its own lease")
        d = tempfile.mkdtemp(prefix="lease_law_")
        try:
            lf = os.path.join(d, "control_capture.pid")
            lines = [m.group(1), "$lf = '%s'" % lf.replace("'", "''")]
            for name, parent, age, lease, _want in self.CASES:
                lines.append("Remove-Item -LiteralPath $lf -ErrorAction SilentlyContinue")
                if lease is not None:
                    lines.append("Set-Content -LiteralPath $lf -Value '%s' -NoNewline" % lease)
                lines.append("$v = Get-LeaseVerdict $lf 4242 %s %d 15; Write-Output ('%s=' + $v)" % (parent, age, name))
            script = os.path.join(d, "t.ps1")
            io.open(script, "w", encoding="utf-8").write("\n".join(lines) + "\n")
            out = subprocess.run([ps, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", script],
                                 capture_output=True, text=True, timeout=120)
            got = dict(l.split("=", 1) for l in out.stdout.splitlines() if "=" in l)
            for name, _p, _a, _l, want in self.CASES:
                self.assertIn(name, got, "PowerShell did not answer %r: %s" % (name, out.stderr[-400:]))
                if want:
                    self.assertIn(want, got[name], "%s: the capture stayed (%r)" % (name, got[name]))
                else:
                    self.assertEqual("", got[name].strip(), "%s: the capture left for no reason (%r)" % (name, got[name]))
        finally:
            shutil.rmtree(d, ignore_errors=True)


RED_PROOF = [
    {
        "why": "2026-09-29 - two starts at once each see no capture and each spawn one; the second pid write orphans the first",
        "file": "tv/control_app.py",
        "find": "    with _CAP_START_LOCK:\n        return _start_capture_locked(env, log_fp)\n",
        "replace": "    return _start_capture_locked(env, log_fp)\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the capture is never told its console, so a crashed console leaves it filming forever",
        "file": "tv/control_app.py",
        "find": "        env2[\"TV_CONSOLE_PID\"] = str(os.getpid())\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - a kill that did not land is assumed to have landed (the five-capture shape)",
        "file": "tv/control_app.py",
        "find": "    if pid and _pid_alive(pid):\n        _CAP_STOP[\"survived\"]",
        "replace": "    if False:\n        _CAP_STOP[\"survived\"]",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the boot sweep ends a capture whose console is alive (another console's camera)",
        "file": "tv/control_app.py",
        "find": "        elif ppid and alive(ppid):\n",
        "replace": "        elif False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - an unreadable process table is read as 'no captures' and the sweep says found 0",
        "file": "tv/control_app.py",
        "find": "    if rows is None:\n        _CAP_SWEEP.update(ran=now, found=None,",
        "replace": "    if rows is None:\n        rows = []\n    if False:\n        _CAP_SWEEP.update(ran=now, found=None,",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
