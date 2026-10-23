# -*- coding: utf-8 -*-
"""REG-2614 - A WINDOWS CONSOLE THAT DIED IS BROUGHT BACK WITHIN MINUTES, WITH NO SIGN-IN; ONE CLOSED ON PURPOSE IS NOT.

2026-10-16: the ALT's console died with no error and nothing relaunched it until someone signed in to Windows - it
missed 302 commits. The sign-in start (REG-1660) only runs at sign-in. console_keepalive.py now runs every 5 minutes
from a per-user scheduled task that the console makes for itself beside its sign-in start.

  · DRIVEN: only a port that REFUSES (nothing listening) is "gone"; up, slow and unknown are left alone.
  · DRIVEN: a console closed on purpose, or a stood-down supervisor, is never relaunched; one launch per cooldown,
    booked before it is tried, so a pass is idempotent beside a running console or another pass.
  · DRIVEN: the launch is the sign-in start's own shape (hidden launcher, -Background), windowless on Windows.
  · DRIVEN: the task rides the sign-in consent: made beside it (on battery too, as the user, no admin, hidden, never
    two at once), never re-made after a removal, withdrawn with the sign-in start, nothing done on UNKNOWN.
  · DRIVEN: control_app writes "closed on purpose" on its one exit surface, where the keepalive reads it, and clears
    it at the next boot - only on the primary Windows console.
RED_PROOF below.
"""
import json
import os
import shutil
import socket
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import console_keepalive as KA  # noqa: E402
import console_doctor as CD  # noqa: E402

WIN_PY = r"C:\Program Files\Python312\python.exe"
WIN_TV = r"C:\TV DIABLO\d2r-bible-tests\tv"
NS = "{http://schemas.microsoft.com/windows/2004/02/mit/task}"


class _R:
    def __init__(self, rc, out="", err=""):
        self.returncode, self.stdout, self.stderr = rc, out, err


class _Win:
    """A fake Windows that answers schtasks like the real one."""

    def __init__(self, exists=False, create_rc=0, query_says=None, encoding=None):
        self.exists, self.create_rc, self.query_says, self.calls, self.xml = exists, create_rc, query_says, [], None
        self.encoding = encoding   # None: answers str (the logic laws); "utf-16" etc.: answers bytes like a pipe

    def run(self, argv, **kw):
        r = self._run(argv, **kw)
        if self.encoding is None:
            return r
        # a real pipe: bytes in the console's encoding; text=True decodes them with the ANSI page (cp1255 on
        # the ALT), strictly - which is what raised on a UTF-16 list (review r2)
        def enc(x):
            return x.encode(self.encoding) if isinstance(x, str) else x
        out, err = enc(r.stdout), enc(r.stderr)
        if kw.get("text"):
            out, err = out.decode("cp1255"), err.decode("cp1255")
        return _R(r.returncode, out, err)

    def _run(self, argv, **kw):
        self.calls.append(list(argv))
        verb = argv[1]
        if verb == "/Query":
            if self.query_says is not None:
                return _R(1, "", self.query_says)
            if "/FO" in argv:
                # the whole list, as CSV with no header - a near-name decoy that must not count
                rows = ['"\\Microsoft\\Windows\\Defrag\\ScheduledDefrag","N/A","Ready"',
                        '"\\TV DIABLO keepalive old","N/A","Ready"']
                if self.exists:
                    rows.append('"\\TV DIABLO keepalive","10/23/2026 9:05:00 PM","Ready"')
                return _R(0, "\n".join(rows) + "\n")
            # review r1: a localized "not found" (German here) - no English words to match
            return _R(0, "TV DIABLO keepalive  Ready") if self.exists else _R(
                1, "", "FEHLER: Das System kann die angegebene Datei nicht finden.")
        if verb == "/Create":
            self.xml = self.written
            if self.create_rc == 0:
                self.exists = True
            return _R(self.create_rc, "", "" if self.create_rc == 0 else "ERROR: Access is denied.")
        if verb == "/Delete":
            self.exists = False
            return _R(0)
        return _R(1)

    def write_xml(self, path, xml):
        self.written = xml

    def verbs(self):
        return [c[1] for c in self.calls]


class _Popen:
    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    def __call__(self, argv, **kw):
        self.calls.append((list(argv), kw))
        if self.fail:
            raise OSError("no powershell")
        return mock.Mock(pid=4242)


class Decide(unittest.TestCase):
    def test_only_a_refused_port_is_gone(self):
        for st in ("up", "slow", "unknown", None):
            self.assertEqual(KA.decide(st, False, False, None, 1000)[0], "leave", st)
        self.assertEqual(KA.decide("gone", False, False, None, 1000)[0], "launch")

    def test_a_choice_is_not_a_crash(self):
        self.assertEqual(KA.decide("gone", True, False, None, 1000)[0], "leave")
        self.assertEqual(KA.decide("gone", False, True, None, 1000)[0], "leave")

    def test_one_launch_per_cooldown(self):
        cd = KA.LAUNCH_COOLDOWN_S
        self.assertEqual(KA.decide("gone", False, False, 1000, 1000 + cd - 1)[0], "held")
        self.assertEqual(KA.decide("gone", False, False, 1000, 1000 + cd)[0], "launch")
        self.assertEqual(KA.decide("gone", False, False, 5000, 1000)[0], "launch", "a clock that went back holds nothing")
        self.assertLessEqual(cd, 15 * 60, "within a few minutes, not an hour")


class Probe(unittest.TestCase):
    def test_a_listening_port_is_up_and_a_closed_one_is_gone(self):
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]
        try:
            self.assertEqual(KA.probe(port, 3.0), "up")
        finally:
            srv.close()
        self.assertEqual(KA.probe(port, 3.0), "gone")

    def test_slow_and_unknown_are_not_gone(self):
        def slow(*a, **k):
            raise socket.timeout("timed out")

        def odd(*a, **k):
            raise OSError(10065, "host unreachable")
        self.assertEqual(KA.probe(1, 1, connect=slow), "slow")
        self.assertEqual(KA.probe(1, 1, connect=odd), "unknown")


class RunOnce(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="ka-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.kw = dict(here=self.d, state_path=os.path.join(self.d, "st.json"), log_path=os.path.join(self.d, "k.log"),
                       on_purpose_path=os.path.join(self.d, "purpose"), pause_path=os.path.join(self.d, "pause"))

    def test_a_dead_console_is_launched_once_then_held(self):
        p = _Popen()
        r = KA.run_once(now_s=1000, probe_fn=lambda: "gone", popen=p, **self.kw)
        self.assertEqual(r["action"], "launch")
        self.assertEqual(len(p.calls), 1)
        argv = p.calls[0][0]
        self.assertIn("-Background", argv)
        self.assertEqual(argv[argv.index("-WindowStyle") + 1], "Hidden")
        self.assertEqual(argv[argv.index("-File") + 1], os.path.join(self.d, "start_tvd_win.ps1"))
        r2 = KA.run_once(now_s=1060, probe_fn=lambda: "gone", popen=p, **self.kw)
        self.assertEqual((r2["action"], len(p.calls)), ("held", 1))
        r3 = KA.run_once(now_s=1000 + KA.LAUNCH_COOLDOWN_S, probe_fn=lambda: "gone", popen=p, **self.kw)
        self.assertEqual((r3["action"], len(p.calls)), ("launch", 2))

    def test_a_running_or_purposely_closed_console_is_never_launched(self):
        p = _Popen()
        self.assertEqual(KA.run_once(now_s=1000, probe_fn=lambda: "up", popen=p, **self.kw)["action"], "leave")
        open(self.kw["on_purpose_path"], "w").close()
        self.assertEqual(KA.run_once(now_s=1000, probe_fn=lambda: "gone", popen=p, **self.kw)["action"], "leave")
        self.assertEqual(p.calls, [])

    def test_a_failed_launch_still_holds_the_cooldown(self):
        r = KA.run_once(now_s=1000, probe_fn=lambda: "gone", popen=_Popen(fail=True), **self.kw)
        self.assertEqual(r["action"], "failed")
        p = _Popen()
        self.assertEqual(KA.run_once(now_s=1100, probe_fn=lambda: "gone", popen=p, **self.kw)["action"], "held")
        self.assertEqual(p.calls, [])

    def test_a_torn_memory_does_not_keep_a_dead_console_down(self):
        with open(self.kw["state_path"], "w") as fh:
            fh.write("{torn")
        p = _Popen()
        r = KA.run_once(now_s=1000, probe_fn=lambda: "gone", popen=p, **self.kw)
        self.assertEqual((r["action"], len(p.calls)), ("launch", 1))
        self.assertIn("could not be read", r["why"], "the lost cooldown is not said")
        self.assertEqual(KA.run_once(now_s=1060, probe_fn=lambda: "gone", popen=p, **self.kw)["action"], "held",
                         "the launch did not rewrite the memory")

    def test_a_window_loop_death_is_not_a_choice(self):
        # review r1: a WebView crash returns the window loop and leaves through the same exit as a close
        for reason in KA.WINDOW_LOOP_EXITS:
            with open(self.kw["on_purpose_path"], "w") as fh:
                fh.write("1700000000 %s\n" % reason)
            self.assertFalse(KA.closed_on_purpose(self.kw["on_purpose_path"]), reason)
        with open(self.kw["on_purpose_path"], "w") as fh:
            fh.write("1700000000 window-closing\n")
        self.assertTrue(KA.closed_on_purpose(self.kw["on_purpose_path"]))
        with open(self.kw["on_purpose_path"], "w") as fh:
            fh.write("1700000000 webview-finally\n")
        p = _Popen()
        self.assertEqual(KA.run_once(now_s=1000, probe_fn=lambda: "gone", popen=p, **self.kw)["action"], "launch",
                         "a console whose window loop died is left down as if he had closed it")

    def test_the_last_action_never_drops_the_booked_cooldown(self):
        real, n = KA._read_state, []

        def _flaky(path):
            n.append(path)
            return real(path) if len(n) == 1 else None     # any re-read after the booking comes back torn
        with mock.patch.object(KA, "_read_state", _flaky):
            KA.run_once(now_s=1000, probe_fn=lambda: "gone", popen=_Popen(), **self.kw)
        with open(self.kw["state_path"]) as fh:
            st = json.load(fh)
        self.assertEqual((st.get("lastLaunch"), st.get("lastAction")), (1000, "launch"), st)

    def test_never_raises(self):
        def boom():
            raise RuntimeError("x")
        self.assertEqual(KA.run_once(now_s=1, probe_fn=boom, **self.kw)["action"], "error")

    def test_windowless_on_windows(self):
        p = _Popen()
        KA.launch(popen=p, here=WIN_TV, is_win=True)
        self.assertTrue(p.calls[0][1]["creationflags"] & 0x08000000, "CREATE_NO_WINDOW")
        self.assertTrue(os.path.isfile(os.path.join(HERE, "start_tvd_win.ps1")))
        with open(os.path.join(HERE, "start_tvd_win.ps1"), encoding="utf-8-sig") as fh:
            self.assertIn("param([switch]$Background)", fh.read())


class Breakaway(unittest.TestCase):
    def test_the_console_leaves_the_tasks_job(self):
        # review r1: whatever ends the task's job must not take the console it started with it
        p = _Popen()
        self.assertTrue(KA.launch(popen=p, here=WIN_TV, is_win=True)[0])
        self.assertEqual(len(p.calls), 1)
        self.assertTrue(p.calls[0][1]["creationflags"] & 0x01000000, "CREATE_BREAKAWAY_FROM_JOB")

    def test_a_job_that_forbids_breakaway_still_gets_its_console(self):
        calls = []

        def _popen(argv, **kw):
            calls.append(kw["creationflags"])
            if kw["creationflags"] & 0x01000000:
                raise PermissionError(5, "Access is denied")
            return mock.Mock(pid=7)
        ok, how = KA.launch(popen=_popen, here=WIN_TV, is_win=True)
        self.assertTrue(ok, how)
        self.assertEqual(len(calls), 2)
        self.assertFalse(calls[1] & 0x01000000)
        self.assertTrue(calls[1] & 0x08000000)

    def test_no_breakaway_off_windows(self):
        p = _Popen()
        KA.launch(popen=p, here="/tmp/tv", is_win=False)
        self.assertEqual(len(p.calls), 1)
        self.assertNotIn("creationflags", p.calls[0][1])


class Task(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="kat-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.marker = os.path.join(self.d, ".keepalive_task.json")

    def _go(self, w, did="created", **kw):
        return CD.ensure_keepalive_task(self.marker, did, run=w.run, is_win=True, tv_dir=WIN_TV, python=WIN_PY,
                                        now_ms=1_700_000_000_000, write_xml=w.write_xml,
                                        isfile=lambda p: True, **kw)

    def test_made_beside_the_sign_in_start_and_seen(self):
        for did in ("created", "already"):
            w = _Win()
            r = self._go(w, did)
            self.assertEqual(r["did"], "created", r)
            self.assertEqual(w.verbs(), ["/Query", "/Query", "/Create", "/Query"])
            self.assertEqual(w.calls[2][w.calls[2].index("/TN") + 1], CD.KEEPALIVE_TASK)
            with open(self.marker, encoding="utf-8") as fh:
                self.assertTrue(json.load(fh)["madeMs"])
            os.remove(self.marker)

    def test_the_task_is_hidden_on_battery_as_the_user_and_never_twice(self):
        w = _Win()
        self._go(w)
        t = ET.fromstring(w.xml.replace('encoding="UTF-16"', ""))
        st = t.find(NS + "Settings")
        self.assertEqual(st.find(NS + "DisallowStartIfOnBatteries").text, "false")
        self.assertEqual(st.find(NS + "StopIfGoingOnBatteries").text, "false")
        self.assertEqual(st.find(NS + "MultipleInstancesPolicy").text, "IgnoreNew")
        self.assertEqual(st.find(NS + "Hidden").text, "true")
        self.assertEqual(st.find(NS + "ExecutionTimeLimit").text, "PT0S",
                         "a time limit's job kill would end the console the pass started (review r1)")
        pr = t.find(NS + "Principals/" + NS + "Principal")
        self.assertEqual(pr.find(NS + "LogonType").text, "InteractiveToken")
        self.assertEqual(pr.find(NS + "RunLevel").text, "LeastPrivilege")
        rep = t.find(NS + "Triggers/" + NS + "TimeTrigger/" + NS + "Repetition")
        self.assertEqual(rep.find(NS + "Interval").text, "PT5M")
        self.assertIsNone(rep.find(NS + "Duration"), "no duration = for ever")
        ex = t.find(NS + "Actions/" + NS + "Exec")
        self.assertEqual(ex.find(NS + "Command").text, r"C:\Program Files\Python312\pythonw.exe")
        self.assertEqual(ex.find(NS + "Arguments").text, '"%s\\console_keepalive.py"' % WIN_TV)
        self.assertEqual(ex.find(NS + "WorkingDirectory").text, WIN_TV)

    def test_an_existing_task_is_left_as_it_is(self):
        w = _Win(exists=True)
        self.assertEqual(self._go(w)["did"], "already")
        self.assertEqual(w.verbs(), ["/Query"])

    def test_a_removed_task_is_never_made_again(self):
        with open(self.marker, "w") as fh:
            json.dump({"madeMs": 1}, fh)
        w = _Win()
        self.assertEqual(self._go(w)["did"], "left")
        self.assertNotIn("/Create", w.verbs())

    def test_withdrawn_with_the_sign_in_start_only_if_this_console_made_it(self):
        w = _Win(exists=True)
        self.assertEqual(self._go(w, "left")["did"], "left")
        self.assertNotIn("/Delete", w.verbs(), "a task someone else made is not ours to remove")
        with open(self.marker, "w") as fh:
            json.dump({"madeMs": 1}, fh)
        w = _Win(exists=True)
        self.assertEqual(self._go(w, "left")["did"], "withdrawn")
        self.assertIn("/Delete", w.verbs())
        w = _Win()
        self.assertEqual(self._go(w, "left")["did"], "left")
        self.assertNotIn("/Create", w.verbs())

    def test_unknown_does_nothing(self):
        for did in (None, "failed"):
            w = _Win()
            self.assertIsNone(self._go(w, did)["did"])
            self.assertEqual(w.calls, [])
        w = _Win(query_says="ERROR: The RPC server is unavailable.")
        self.assertIsNone(self._go(w)["did"])
        self.assertNotIn("/Create", w.verbs())
        self.assertIsNone(CD.ensure_keepalive_task(self.marker, "created", run=_Win().run, is_win=False)["did"])

    def test_a_refused_create_is_said(self):
        w = _Win(create_rc=1)
        r = self._go(w)
        self.assertEqual(r["did"], "failed")
        self.assertFalse(os.path.exists(self.marker))

    def test_a_refusal_said_on_stdout_is_kept(self):
        w = _Win(create_rc=1)
        real = w.run

        def _run(argv, **kw):
            r = real(argv, **kw)
            if argv[1] == "/Create":
                return _R(1, "ERROR: The task XML contains a value which is incorrectly formatted.", "")
            return r
        w.run = _run
        r = self._go(w)
        self.assertIn("incorrectly formatted", r["why"], r)

    def test_the_list_settles_a_missing_task_in_any_language(self):
        w = _Win()
        self.assertIs(CD._keepalive_task_exists(w.run), False, "the near-name decoy was taken for the task")
        w.exists = True
        self.assertIs(CD._keepalive_task_exists(w.run), True)

        def _named_fails_list_has_it(argv, **kw):
            if "/FO" in argv:
                return _R(0, '"\\TV DIABLO keepalive","N/A","Bereit"\n')
            return _R(1, "", "FEHLER")
        self.assertIs(CD._keepalive_task_exists(_named_fails_list_has_it), True)

        def _list_fails(argv, **kw):
            return _R(1, "", "Fehler beim Abfragen")
        self.assertIsNone(CD._keepalive_task_exists(_list_fails), "a list that failed was read as 'no task'")

    def test_a_utf16_or_oem_list_still_settles_the_task(self):
        # review r2: piped, schtasks writes UTF-16 (BOM or NUL stride) or the OEM page, never reliably ANSI
        for enc in ("utf-16", "utf-16-le", "cp862", "utf-8"):
            w = _Win(encoding=enc)
            self.assertIs(CD._keepalive_task_exists(w.run), False, "%s: the near-name decoy was taken" % enc)
            w.exists = True
            self.assertIs(CD._keepalive_task_exists(w.run), True, "%s: the task in the list was not seen" % enc)
        for enc in ("utf-16", "utf-16-le"):
            if os.path.exists(self.marker):
                os.remove(self.marker)          # each Windows starts with no record of a keepalive
            w = _Win(encoding=enc)
            r = self._go(w)
            self.assertEqual(r["did"], "created", "%s: a UTF-16 Windows never gets its keepalive: %s" % (enc, r))
            self.assertIn("/Create", w.verbs())

    def test_a_list_that_cannot_be_parsed_is_unknown_not_a_crash(self):
        w = _Win(encoding="utf-16")
        with mock.patch.object(CD, "_schtasks_text", side_effect=__import__("csv").Error("line contains NUL")):
            self.assertIsNone(CD._keepalive_task_exists(w.run), "a list that cannot be read raised or read as 'no'")

    def test_a_utf16_refusal_is_said_in_words(self):
        w = _Win(create_rc=1, encoding="utf-16")
        r = self._go(w)
        self.assertEqual(r["did"], "failed")
        self.assertIn("Access is denied", r["why"], r)

    def test_the_decoder(self):
        row = '"\\TV DIABLO keepalive","N/A","\u05de\u05d5\u05db\u05df"\r\n'
        for enc in ("utf-16", "utf-16-le", "utf-8"):
            self.assertEqual(CD._schtasks_text(row.encode(enc)), row, enc)
        self.assertTrue(CD._schtasks_text(row.encode("cp862")).startswith('"\\TV DIABLO keepalive",'))
        self.assertEqual(CD._schtasks_text(None), "")
        self.assertEqual(CD._schtasks_text("a\x00b"), "ab")

    def test_pythonw_beside_python(self):
        self.assertEqual(CD._keepalive_pythonw(WIN_PY, isfile=lambda p: True),
                         r"C:\Program Files\Python312\pythonw.exe")
        self.assertEqual(CD._keepalive_pythonw(WIN_PY, isfile=lambda p: False), WIN_PY)


class PassDeadline(unittest.TestCase):
    def test_a_hung_pass_ends_itself(self):
        # review r2: the task has no time limit and IgnoreNew, so only this timer stops a hung pass holding every
        # later one off. Driven in a child: the timer's os._exit would end the test runner.
        import subprocess as _sp
        import time as _t
        code = ("import sys, time; sys.path.insert(0, %r); import console_keepalive as k; "
                "sys.exit(k.main(run=lambda: time.sleep(30) or {'action': 'leave'}, deadline_s=1))" % HERE)
        t0 = _t.time()
        r = _sp.run([sys.executable, "-c", code], capture_output=True, timeout=25)
        self.assertEqual(r.returncode, 3, "a hung pass was not ended by its deadline (rc %s)" % r.returncode)
        self.assertLess(_t.time() - t0, 20)
        self.assertEqual(KA.PASS_DEADLINE_S, 90)

    def test_a_pass_that_ends_returns_its_code(self):
        self.assertEqual(KA.main(run=lambda: {"action": "leave"}, deadline_s=60), 0)
        self.assertEqual(KA.main(run=lambda: {"action": "error"}, deadline_s=60), 1)


class ConsoleSide(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import control_app
        cls.ca = control_app

    def test_the_console_writes_where_the_keepalive_reads(self):
        self.assertEqual(os.path.abspath(self.ca._exit_on_purpose_path()), os.path.abspath(KA.EXITED_ON_PURPOSE))

    def test_closed_on_purpose_is_written_and_cleared_only_on_the_primary_windows_console(self):
        d = tempfile.mkdtemp(prefix="kac-")
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, "purpose")
        env = {k: v for k, v in os.environ.items() if k != "TV_STUB"}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(self.ca, "_is_primary_console", return_value=True):
            self.assertFalse(self.ca._note_exit_on_purpose("quit", path=p, is_win=False))
            self.assertFalse(os.path.exists(p))
            self.assertTrue(self.ca._note_exit_on_purpose("quit", path=p, is_win=True))
            self.assertTrue(os.path.exists(p))
            self.assertTrue(self.ca._clear_exit_on_purpose(path=p, is_win=True))
            self.assertFalse(os.path.exists(p))
        with mock.patch.dict(os.environ, dict(env, TV_STUB="1"), clear=True), \
                mock.patch.object(self.ca, "_is_primary_console", return_value=True):
            self.assertFalse(self.ca._note_exit_on_purpose("quit", path=p, is_win=True))
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(self.ca, "_is_primary_console", return_value=False):
            self.assertFalse(self.ca._note_exit_on_purpose("quit", path=p, is_win=True))
        self.assertFalse(os.path.exists(p))

    def test_a_window_loop_death_writes_no_on_purpose_mark(self):
        self.assertEqual(tuple(self.ca._WINDOW_LOOP_EXITS), tuple(KA.WINDOW_LOOP_EXITS),
                         "the console and the keepalive disagree on which exits are deaths")
        d = tempfile.mkdtemp(prefix="kaw-")
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, "purpose")
        env = {k: v for k, v in os.environ.items() if k != "TV_STUB"}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(self.ca, "_is_primary_console", return_value=True):
            for reason in self.ca._WINDOW_LOOP_EXITS:
                self.assertFalse(self.ca._note_exit_on_purpose(reason, path=p, is_win=True), reason)
            self.assertFalse(os.path.exists(p))
            self.assertTrue(self.ca._note_exit_on_purpose("window-closing", path=p, is_win=True))
            self.assertFalse(self.ca._note_exit_on_purpose("window-closed", path=p, is_win=True))
            with open(p) as fh:
                self.assertIn("window-closing", fh.read(), "the death after a real close overwrote its reason")

    def test_the_one_exit_surface_says_on_purpose(self):
        ca = self.ca
        with mock.patch.object(ca, "_note_exit_on_purpose") as note, \
                mock.patch.object(ca, "_mark_window_gone"), mock.patch.object(ca, "_schedule_exit_stop"), \
                mock.patch.object(ca, "_arm_force_exit"), mock.patch.dict(ca.__dict__, {"_MAIN_WIN": None}), \
                mock.patch.dict(ca.__dict__, {"_EXIT_REQUESTED": ca.__dict__.get("_EXIT_REQUESTED")}):
            ca._request_console_exit("window-closed")
        note.assert_called_once_with("window-closed")

    def test_the_sign_in_setup_makes_the_keepalive_with_its_own_answer(self):
        ca = self.ca
        import frame_ref
        env = {k: v for k, v in os.environ.items() if k != "TV_STUB"}
        with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(ca.sys, "platform", "win32"), \
                mock.patch.object(ca, "_is_primary_console", return_value=True), \
                mock.patch.object(frame_ref, "on_console_path", return_value=True), \
                mock.patch.object(CD, "ensure_sign_in_start", return_value={"did": "already", "why": "x"}), \
                mock.patch.object(CD, "ensure_keepalive_task", return_value={"did": "created", "why": "y"}) as ek, \
                mock.patch.object(ca, "_clear_exit_on_purpose") as clr, \
                mock.patch.object(ca, "_decision_path", side_effect=lambda n: "/nowhere/" + n), \
                mock.patch.object(ca, "_his_answers_path", return_value=None), \
                mock.patch.dict(ca.__dict__, {"_SIGN_IN_SETUP": {}}):
            out = ca._sign_in_setup_once()
        ek.assert_called_once_with("/nowhere/.keepalive_task.json", "already")
        clr.assert_called_once_with()
        self.assertEqual(out.get("keepalive"), "created")


RED_PROOF = [
    {"matches": 1, "file": "console_doctor.py",
     "find": "        lst = run([\"schtasks\", \"/Query\", \"/FO\", \"CSV\", \"/NH\"], capture_output=True, timeout=60)",
     "replace": "        lst = run([\"schtasks\", \"/Query\", \"/FO\", \"CSV\", \"/NH\"], capture_output=True, text=True, timeout=60)",
     "why": "review r2: the list decoded with the ANSI page raises on a UTF-16 pipe, so the task is never made"},
    {"matches": 1, "file": "console_doctor.py",
     "find": "    if len(b) >= 4 and b[1:2] == b\"\\x00\" and b[3:4] == b\"\\x00\":\n", "replace": "    if False:\n",
     "why": "review r2: a BOM-less UTF-16 list is read as NUL-strided text and never matches"},
    {"matches": 1, "file": "console_doctor.py",
     "find": "    if b[:2] == b\"\\xff\\xfe\" or b[:2] == b\"\\xfe\\xff\":\n", "replace": "    if False:\n",
     "why": "review r2: a UTF-16 list with a BOM is never matched"},
    {"matches": 1, "file": "console_doctor.py",
     "find": "    except Exception:                   # csv.Error, a decode, a timeout: UNKNOWN, never a guessed \"no\"",
     "replace": "    except OSError:", "why": "review r2: a list that cannot be parsed raises out of the sign-in setup"},
    {"matches": 1, "file": "console_keepalive.py", "find": "    _t.start()\n", "replace": "",
     "why": "review r2: a hung pass is never ended, and IgnoreNew holds every later pass off for ever"},
    {"matches": 1, "file": "console_keepalive.py", "find": '    except (socket.timeout, TimeoutError):\n        return "slow"',
     "replace": '    except (socket.timeout, TimeoutError):\n        return "gone"',
     "why": "a slow console read as gone would be relaunched under load (the ALT stalls for minutes)"},
    {"matches": 1, "file": "console_keepalive.py", "find": "    if on_purpose:\n",
     "replace": "    if False:\n", "why": "a console closed on purpose relaunched - a choice treated as a crash"},
    {"matches": 1, "file": "console_keepalive.py", "find": "0 <= now_s - last_launch_s < LAUNCH_COOLDOWN_S",
     "replace": "0 <= now_s - last_launch_s < 0", "why": "no cooldown: a console that dies at boot relaunched every pass"},
    {"matches": 1, "file": "console_keepalive.py",
     "find": "            mem = dict(mem, lastLaunch=now_s, launches=int(mem.get(\"launches\") or 0) + 1)\n            _write_state(state_path, mem)\n            ok, how = launch(popen=popen, here=here)\n",
     "replace": "            ok, how = launch(popen=popen, here=here)\n            if ok:\n                mem = dict(mem, lastLaunch=now_s)\n                _write_state(state_path, mem)\n",
     "why": "the launch booked only on success: a failing launcher is retried every pass"},
    {"matches": 1, "file": "console_keepalive.py", "find": '"-File", os.path.join(here, "start_tvd_win.ps1"), "-Background"]',
     "replace": '"-File", os.path.join(here, "start_tvd_win.ps1")]',
     "why": "without -Background the launcher can pop a dialog or fight a running console"},
    {"matches": 1, "file": "console_keepalive.py", "find": "    if is_win:\n        kw[\"creationflags\"]",
     "replace": "    if False:\n        kw[\"creationflags\"]", "why": "a console window flashes on every relaunch"},
    {"matches": 1, "file": "console_doctor.py", "find": "'<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>'",
     "replace": "'<DisallowStartIfOnBatteries>true</DisallowStartIfOnBatteries>'",
     "why": "the task would never run on Dean's laptop on battery"},
    {"matches": 1, "file": "console_doctor.py", "find": "    if rec.get(\"madeMs\"):\n        return {\"did\": \"left\", \"why\": \"the keepalive this console made is gone",
     "replace": "    if False:\n        return {\"did\": \"left\", \"why\": \"the keepalive this console made is gone",
     "why": "a removed keepalive re-made at every boot - fighting a removal"},
    {"matches": 1, "file": "console_doctor.py", "find": "        if exists and rec.get(\"madeMs\"):\n",
     "replace": "        if exists:\n", "why": "a task this console never made deleted"},
    {"matches": 1, "file": "console_doctor.py", "find": "    consent = sign_in_did in (\"created\", \"already\")\n",
     "replace": "    consent = sign_in_did in (\"created\", \"already\", \"left\")\n",
     "why": "a PC that said no to the sign-in start still gets a self-starting console"},
    {"matches": 1, "file": "console_doctor.py", "find": "        if getattr(lst, \"returncode\", 1) != 0:\n            return None\n",
     "replace": "", "why": "an RPC error read as 'no task' - UNKNOWN acted on"},
    {"matches": 1, "file": "console_doctor.py", "find": "'<Hidden>true</Hidden>",
     "replace": "'<Hidden>false</Hidden>", "why": "the task shows in his Task Scheduler list as an unexplained entry"},
    {"matches": 1, "file": "control_app.py", "find": "    _note_exit_on_purpose(reason)\n", "replace": "",
     "why": "✕/Quit never said 'on purpose': the keepalive would reopen a console he closed"},
    {"matches": 1, "file": "control_app.py", "find": "    return bool(is_win and not os.environ.get(\"TV_STUB\") and _is_primary_console())",
     "replace": "    return bool(is_win)", "why": "a harness or scratch console would write his real on-purpose flag"},
    {"matches": 1, "file": "control_app.py", "find": "            k = _cd_si.ensure_keepalive_task(_decision_path(\".keepalive_task.json\"), r.get(\"did\"))",
     "replace": "            k = {}", "why": "the keepalive is never made"},
    {"matches": 1, "file": "control_app.py", "find": "            _clear_exit_on_purpose()\n", "replace": "",
     "why": "a console reopened after a quit stays 'closed on purpose' and is never brought back"},
    {"matches": 1, "file": "console_keepalive.py", "find": "        unread = mem is None\n", "replace": "        unread = False\n",
     "why": "a torn memory file stops every relaunch (or crashes the pass) instead of being said and rewritten"},
    {"matches": 1, "file": "console_doctor.py", "find": "<ExecutionTimeLimit>PT0S</ExecutionTimeLimit>",
     "replace": "<ExecutionTimeLimit>PT2M</ExecutionTimeLimit>",
     "why": "review r1: the task's 2-minute limit kills its job, and the console the pass started with it"},
    {"matches": 1, "file": "console_keepalive.py", "find": "creationflags=kw[\"creationflags\"] | _CREATE_BREAKAWAY_FROM_JOB",
     "replace": "creationflags=kw[\"creationflags\"]", "why": "review r1: the console stays in the task's job"},
    {"matches": 1, "file": "console_keepalive.py", "find": "            p = None                    # the job forbids breakaway",
     "replace": "            return False, \"no breakaway\"  #", "why": "review r1: a job that forbids breakaway gets no console"},
    {"matches": 1, "file": "console_doctor.py", "find": "        if row and row[0].strip().lower() == want:\n",
     "replace": "        if row and want in row[0].strip().lower():\n",
     "why": "review r1: a near-name task in the list is taken for the keepalive, so it is never made"},
    {"matches": 1, "file": "console_doctor.py",
     "find": "% ((\"%s %s\" % (_schtasks_text(getattr(r, \"stdout\", None)),\n",
     "replace": "% ((\"%s %s\" % (\"\",\n",
     "why": "review r1: a refusal schtasks prints on stdout is logged as 'no reason given'"},
    {"matches": 1, "file": "control_app.py", "find": " or str(reason or \"\") in _WINDOW_LOOP_EXITS:\n", "replace": ":\n",
     "why": "review r1: a WebView crash that returns the window loop is marked 'closed on purpose'"},
    {"matches": 1, "file": "console_keepalive.py",
     "find": "    return (words[1] if len(words) > 1 else \"\") not in WINDOW_LOOP_EXITS\n", "replace": "    return True\n",
     "why": "review r1: a window-loop death already on disk keeps the console down"},
    {"matches": 1, "file": "console_keepalive.py", "find": "            _write_state(state_path, dict(mem, lastAction=action))\n",
     "replace": "            _write_state(state_path, dict(_read_state(state_path) or {}, lastAction=action))\n",
     "why": "review r1: a torn re-read rewrites the memory without the cooldown it just booked"},
]


if __name__ == "__main__":
    unittest.main()
