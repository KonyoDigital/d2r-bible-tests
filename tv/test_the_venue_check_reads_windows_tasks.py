# -*- coding: utf-8 -*-
"""#171 (REG-2481) - THE VENUE ROW READS TASK SCHEDULER ON WINDOWS, BY THE SAME RULE IT READS LAUNCHD WITH.

MEASURED on Dean's PC 2026-10-22: 'test venue' UNKNOWN for 49 days - "this check only knows launchd, so it cannot speak
for this machine". His order is that browser suites run on GitHub and never on a PC of his; on Windows nothing was
checking it at all. The row now reads Task Scheduler (`schtasks /query /fo CSV /v`, the 'Task To Run' column, and every
script a task names by an absolute path) and judges each task with reaches_a_browser_suite - the ONE rule launchd's
plists are judged by, so the routine_Q lesson (an invocation, not a mention) holds on both.

And the same OS-awareness for 'console painted whole': its witnesses read macOS's window server (Quartz). On a PC
without one the row stays UNKNOWN - never OK without a look - and says which witness that PC lacks.

Every case is driven by a fixture listing, on any PC: no real Task Scheduler, no real window. [[test-venue]]
"""
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

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

import console_doctor as CD  # noqa: E402
import region_witness as RW  # noqa: E402

HEADER = ('"HostName","TaskName","Next Run Time","Status","Logon Mode","Last Run Time","Last Result","Author",'
          '"Task To Run","Start In","Comment","Scheduled Task State"')


def _task(name, run, comment="N/A"):
    q = lambda s: '"%s"' % s.replace('"', '""')
    return ",".join(q(x) for x in ("PC", name, "N/A", "Ready", "Interactive only", "N/A", "0", "him", run, "N/A",
                                   comment, "Enabled"))


def _listing(*tasks):
    """schtasks prints the header once per task folder - the fixture does too"""
    return "\r\n".join(["", HEADER, _task("\\Microsoft\\Windows\\Defrag\\ScheduledDefrag",
                                          "%windir%\\system32\\defrag.exe -c -h -o"),
                        "", HEADER] + list(tasks)) + "\r\n"


class TaskSchedulerIsJudgedByTheOneRule(unittest.TestCase):

    def test_a_task_that_runs_a_browser_suite_is_named(self):
        st, why = CD._venue_on_windows(query=lambda: _listing(
            _task("\\TVD nightly", '"C:\\Program Files\\nodejs\\npx.cmd" playwright test --reporter=line'),
            _task("\\TVD sweep", "C:\\Python312\\python.exe C:\\repo\\tv\\run_gates.py")))
        print("   %s: %s" % (st, why[:150]))
        self.assertEqual(st, CD.MISSING, why)
        self.assertIn("\\TVD nightly", why)
        self.assertNotIn("\\TVD sweep", why, "a python-only task was accused")

    def test_a_python_only_schedule_is_ok_and_says_what_it_read(self):
        st, why = CD._venue_on_windows(query=lambda: _listing(
            _task("\\TVD sweep", "C:\\Python312\\python.exe C:\\repo\\tv\\run_gates.py"),
            _task("\\Watchdog", "powershell.exe -File C:\\x\\watch.ps1", comment="run `npx playwright test` in CI")))
        self.assertEqual(st, CD.OK, why)
        self.assertIn("Task Scheduler", why)
        self.assertIn("3 Task Scheduler task(s)", why, "the OK does not carry how many tasks it judged")

    def test_the_rule_reads_the_script_a_task_names(self):
        d = tempfile.mkdtemp(prefix="venue_law_")
        self.addCleanup(shutil.rmtree, d, True)
        bat = os.path.join(d, "nightly.bat")
        with io.open(bat, "w", encoding="utf-8") as fh:
            fh.write("cd /d C:\\repo\r\nnpx playwright test tests/\r\n")
        st, why = CD._venue_on_windows(query=lambda: _listing(_task("\\Nightly", 'cmd.exe /c "%s"' % bat)))
        self.assertEqual(st, CD.MISSING, "the task's own script ran a suite and the row did not read it: %s" % why)

    def test_a_task_that_only_mentions_playwright_is_not_accused(self):
        st, why = CD._venue_on_windows(query=lambda: _listing(
            _task("\\Doctor", "powershell.exe -Command \"Write-Host 'run npx playwright install'\"")))
        self.assertEqual(st, CD.OK, "an install hint was read as a suite (the routine_Q lesson): %s" % why)

    def test_a_listing_that_cannot_be_read_is_unknown_never_an_empty_schedule(self):
        def _refused():
            raise OSError("schtasks exited 1")
        for q, what in ((_refused, "a refused query"),
                        (lambda: '"Hostname","Nom de la tache","Tache a executer"\r\n"PC","\\x","y"\r\n',
                         "a listing in another language"),
                        (lambda: "", "an empty listing")):
            st, why = CD._venue_on_windows(query=q)
            self.assertEqual(st, CD.UNKNOWN, "%s read as %s: %s" % (what, st, why))

    def test_a_task_whose_actions_cannot_be_seen_is_never_judged_clean(self):
        st, why = CD._venue_on_windows(query=lambda: _listing(
            _task("\\Microsoft\\Windows\\Maintenance\\WinSAT", "Multiple actions"),
            _task("\\Someone's job", "Multiple actions")))
        self.assertEqual(st, CD.UNKNOWN, "a task whose commands were never seen was judged: %s" % why)
        self.assertIn("\\Someone's job", why)
        self.assertNotIn("WinSAT", why, "Windows' own folder was counted against the venue")

    def test_launchd_and_task_scheduler_share_the_rule(self):
        self.assertTrue(CD.reaches_a_browser_suite("npx playwright test"))
        self.assertTrue(CD.reaches_a_browser_suite('"C:\\Program Files\\nodejs\\npx.cmd" playwright test'))
        self.assertTrue(CD.reaches_a_browser_suite("C:\\r\\node_modules\\.bin\\playwright.cmd test"))
        self.assertFalse(CD.reaches_a_browser_suite("run `npx playwright install`"))


class TheListingIsReadAtMostOnceAnHour(unittest.TestCase):
    """schtasks costs seconds on a Windows PC, and tasklist HUNG under his game (REG-1414): the every-tick row reads
    the listing at most hourly and says how old it is; a listing that could not be taken is asked again only after
    ten minutes, so a hang costs one bounded wait per tick, never one per ask."""

    def setUp(self):
        saved = dict(CD._TASKS)
        self.addCleanup(lambda: (CD._TASKS.clear(), CD._TASKS.update(saved)))
        CD._TASKS.update(at=None, text=None, err=None)
        self.asked = []

    def _schtasks(self, answer):
        def fn():
            self.asked.append(1)
            if isinstance(answer, Exception):
                raise answer
            return answer
        return mock.patch.object(CD, "_schtasks_csv", fn)

    def test_a_listing_is_reused_within_the_hour_and_says_its_age(self):
        with self._schtasks(_listing(_task("\\TVD sweep", "C:\\Python312\\python.exe C:\\r\\run_gates.py"))):
            st1, why1 = CD._venue_on_windows(now=5000.0)
            st2, why2 = CD._venue_on_windows(now=5000.0 + 1800)
            st3, _w3 = CD._venue_on_windows(now=5000.0 + 3601)
        self.assertEqual((st1, st2, st3), (CD.OK, CD.OK, CD.OK))
        self.assertIn("read just now", why1)
        self.assertIn("read 30 min ago", why2, "a reused listing did not carry its age")
        self.assertEqual(len(self.asked), 2, "Task Scheduler was asked %d times over 61 minutes" % len(self.asked))

    def test_a_failed_listing_is_unknown_and_not_asked_again_at_once(self):
        with self._schtasks(OSError("schtasks timed out")):
            st1, _w1 = CD._venue_on_windows(now=9000.0)
            st2, why2 = CD._venue_on_windows(now=9000.0 + 60)
            st3, _w3 = CD._venue_on_windows(now=9000.0 + CD._TASKS_FAIL_TTL_S + 1)
        self.assertEqual((st1, st2, st3), (CD.UNKNOWN, CD.UNKNOWN, CD.UNKNOWN))
        self.assertIn("asked again", why2)
        self.assertEqual(len(self.asked), 2, "a failing schtasks was asked again at once - a hang would repeat")


class AUtf16ListingIsReadNotCachedAsGarbage(unittest.TestCase):
    """REG-2481 round 2 (second eye) - a Windows tool piped to a file may write UTF-16. Decoded as utf-8/mbcs it is a
    NUL between every letter, no 'Task To Run' header, UNKNOWN for ever - and that garbage was cached for an hour as a
    GOOD listing. The real _schtasks_csv is driven here through its git_quiet door with both UTF-16 shapes."""

    def setUp(self):
        saved = dict(CD._TASKS)
        self.addCleanup(lambda: (CD._TASKS.clear(), CD._TASKS.update(saved)))
        CD._TASKS.update(at=None, text=None, err=None)

    def _run_with(self, raw):
        import git_quiet
        r = mock.Mock(returncode=0, stdout=raw)
        return mock.patch.object(git_quiet, "run", lambda *a, **k: r)

    def test_both_utf16_shapes_read_as_the_listing(self):
        text = _listing(_task("\\TVD sweep", "C:\\Python312\\python.exe C:\\r\\run_gates.py"))
        for label, raw in (("BOM", text.encode("utf-16")), ("bare LE", text.encode("utf-16-le"))):
            CD._TASKS.update(at=None, text=None, err=None)
            with self._run_with(raw):
                st, why = CD._venue_on_windows(now=1000.0)
            self.assertEqual(st, CD.OK, "%s UTF-16 listing: %s" % (label, why))

    def test_a_listing_that_will_not_parse_is_a_failure_on_the_short_ttl(self):
        with self._run_with(b"not a listing at all\r\n"):
            st, _why = CD._venue_on_windows(now=2000.0)
        self.assertEqual(st, CD.UNKNOWN)
        self.assertIsNone(CD._TASKS["text"], "an unparseable listing was cached as a good one")
        self.assertTrue(CD._TASKS["err"], "an unparseable listing was not recorded as a failed read")


class TheRowAsksTheSchedulerThisPcHas(unittest.TestCase):

    def test_windows_asks_task_scheduler(self):
        seen = []
        with mock.patch.object(CD, "_this_os", lambda: "win32"), \
                mock.patch.object(CD, "_venue_on_windows", lambda: seen.append(1) or (CD.OK, "fixture")):
            st, why = CD._check_no_browser_suite_is_scheduled_on_this_mac()
        self.assertEqual(seen, [1], "on Windows the row did not read Task Scheduler: %s %s" % (st, why))

    def test_an_os_with_neither_scheduler_is_unknown(self):
        with mock.patch.object(CD, "_this_os", lambda: "linux"):
            st, why = CD._check_no_browser_suite_is_scheduled_on_this_mac()
        self.assertEqual(st, CD.UNKNOWN, why)
        self.assertIn("Task Scheduler", why)


class ThePaintedRowNamesTheWitnessWindowsLacks(unittest.TestCase):
    QUARTZ = {"ok": False, "half": None, "looks": 1,
              "why": "look 1 of 3 could not be taken (Quartz is not importable here - the window server cannot be "
                     "asked), so NOTHING is known about this window"}

    def test_on_windows_it_stays_unknown_and_names_the_missing_windows_witness(self):
        with mock.patch.object(CD, "_this_os", lambda: "win32"), \
                mock.patch.object(RW, "half_blank_strikes", lambda pid, **kw: dict(self.QUARTZ)):
            st, why = CD._check_the_console_painted_all_of_itself()
        print("   painted whole on Windows: %s - %s" % (st, why[:140]))
        self.assertEqual(st, CD.UNKNOWN, "a window nobody could look at was graded: %s" % why)
        for part in ("Windows", "Quartz", "never OK without a look"):
            self.assertIn(part, why)

    def test_on_a_mac_a_covered_window_keeps_its_own_words(self):
        covered = {"ok": False, "why": "the console is covered by another window"}
        with mock.patch.object(CD, "_this_os", lambda: "darwin"), \
                mock.patch.object(RW, "half_blank_strikes", lambda pid, **kw: dict(covered)):
            st, why = CD._check_the_console_painted_all_of_itself()
        self.assertEqual((st, why), (CD.UNKNOWN, covered["why"]))


RED_PROOF = [
    {
        "why": "REG-2481 - the Windows venue answers OK without reading Task Scheduler: a nightly browser suite on "
               "Dean's PC reads as a clean venue",
        "file": "console_doctor.py",
        "find": "            text, age = query(), 0.0\n",
        "replace": "            return OK, \"no scheduled task runs a browser suite here\"\n",
        "matches": 1,
    },
    {
        "why": "REG-2481 - the row stops asking Task Scheduler on Windows: 'only knows launchd' for good",
        "file": "console_doctor.py",
        "find": "    if _os.startswith(\"win\"):\n        return _venue_on_windows()",
        "replace": "    if False:\n        return _venue_on_windows()",
        "matches": 1,
    },
    {
        "why": "REG-2481 - the Windows spelling of the invocation is dropped from the one rule: npx.cmd playwright "
               "test runs unseen",
        "file": "console_doctor.py",
        "find": "    r\"(?:npx(?:\\.cmd|\\.exe)?[\\\"']?\\s+|",
        "replace": "    r\"(?:npx\\s+|",
        "matches": 1,
    },
    {
        "why": "REG-2481 - a listing that could not be taken is asked again on every call: a schtasks that hangs under "
               "his game costs a full wait per ask",
        "file": "console_doctor.py",
        "find": "        elif _TASKS[\"err\"] is not None and now - _TASKS[\"at\"] < _TASKS_FAIL_TTL_S:\n",
        "replace": "        elif False:\n",
        "matches": 1,
    },
    {
        "why": "REG-2481 - the painted-whole row on Windows goes back to the witness's bare words, and the missing "
               "Windows witness is never named",
        "file": "console_doctor.py",
        "find": "        if _os != \"darwin\":\n            # #171 (REG-2481) - ON WINDOWS THE WITNESS IS MISSING",
        "replace": "        if False:\n            # #171 (REG-2481) - ON WINDOWS THE WITNESS IS MISSING",
        "matches": 1,
    },
    {
        "why": "REG-2481 round 2 - a UTF-16 listing is decoded as utf-8/mbcs again: a NUL between every letter, no "
               "header, the venue row UNKNOWN on every Windows PC",
        "file": "console_doctor.py",
        "find": "    if raw[:2] in (b\"\\xff\\xfe\", b\"\\xfe\\xff\") or b\"\\x00\" in raw[:200]:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-2481 round 2 - a listing that will not parse is cached for an hour as a good one again",
        "file": "console_doctor.py",
        "find": "                text, age = _schtasks_csv(), 0.0\n                tasks = windows_tasks_from_csv(text)\n",
        "replace": "                text, age = _schtasks_csv(), 0.0\n",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
