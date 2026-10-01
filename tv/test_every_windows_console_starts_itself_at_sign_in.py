# -*- coding: utf-8 -*-
"""REG-1660 — EVERY WINDOWS CONSOLE STARTS ITSELF AT SIGN-IN, HIDDEN, AND NEVER FIGHTS A REMOVAL.

His ruling, 2026-10-01, answering #229's question for every PC at once: "set it up there and for dean too.. like in
general ... so it starts at startup". MEASURED that morning on his Windows PC: no task, nothing in the Startup
folder - "after a reboot it stays off until someone opens it" - and Dean's laptop had last reported on 09-29, still
on v3522. A console that is not running has no shadow reader, no beacon and no pull: it cannot film, cannot show its
lights in the fleet and cannot update itself.

  · DRIVEN (stubbed PowerShell, a temp Startup folder, a temp record, a temp answers store): a console with nothing
    starting it makes the installer's own shortcut shape with -Background and records it; one already started by
    something is left alone; one whose entry it made and someone removed is NEVER made again; a PC that answered
    "No, I open it myself" is never overruled; UNKNOWN (tasks unaskable, record unreadable) makes nothing; a write
    the check cannot then see is "failed", never "created".
  · DRIVEN: only the primary console process does it - never a harness, never a scratch console, never twice.
  · READ (PowerShell cannot run here; CI's Windows boot runs the launcher): start_tvd_win.ps1 -Background passes
    --background, leaves a running console exactly as it is, skips the window wait and never pops a dialog.
RED_PROOF below. [[unknown-stays-unknown]] [[the-unjoined-end]]
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as cd  # noqa: E402
import his_answers as ha  # noqa: E402


class _R(object):
    def __init__(self, rc, err=""):
        self.returncode, self.stdout, self.stderr = rc, "", err


def _no_task(argv, **kw):
    return _R(1)                                    # schtasks /Query: no such task


class TheConsoleMakesItsOwnSignInStart(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="signin_")
        self.startup = os.path.join(self.d, "Startup")
        os.makedirs(self.startup)
        self.marker = os.path.join(self.d, ".sign_in_start.json")
        self.answers = os.path.join(self.d, "his_answers.json")
        self.made = []

    def tearDown(self):
        shutil.rmtree(self.d, True)

    def _make(self, writes=True):
        def make(startup_dir, repo_dir):
            self.made.append((startup_dir, repo_dir))
            if writes:
                with io.open(os.path.join(startup_dir, cd.SIGN_IN_LNK), "wb") as fh:
                    fh.write('-File "C:\\repo\\tv\\start_tvd_win.ps1" -Background'.encode("utf-16-le"))
            return True, ""
        return make

    def _ensure(self, make=None, run=_no_task, **kw):
        return cd.ensure_sign_in_start(self.marker, answers_path=self.answers, run=run, startup_dir=self.startup,
                                       is_win=True, make=make or self._make(), repo_dir="C:\\repo", now_ms=1000, **kw)

    def test_nothing_starts_it_so_it_makes_one_and_records_it(self):
        r = self._ensure()
        self.assertEqual(r["did"], "created", r)
        self.assertEqual(len(self.made), 1)
        with io.open(self.marker, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh).get("madeMs"), 1000)
        self.assertEqual(cd._sign_in_start(run=_no_task, startup_dir=self.startup, is_win=True)["state"], cd.OK)

    def test_something_already_starts_it_so_it_is_left_alone(self):
        with io.open(os.path.join(self.startup, "TV DIABLO.lnk"), "wb") as fh:
            fh.write("start_tvd_win.ps1".encode("utf-16-le"))
        r = self._ensure()
        self.assertEqual(r["did"], "already", r)
        self.assertEqual(self.made, [], "an entry was made beside one that already starts it")
        self.assertFalse(os.path.exists(self.marker))

    def test_an_entry_someone_removed_is_never_made_again(self):
        with io.open(self.marker, "w", encoding="utf-8") as fh:
            json.dump({"madeMs": 5}, fh)
        r = self._ensure()
        self.assertEqual(r["did"], "left", r)
        self.assertEqual(self.made, [], "the console fought a removal by making it again")

    def test_a_pc_that_said_no_is_never_overruled(self):
        ask = cd._ask_sign_in_start({"state": cd.MISSING, "why": ""})[0]
        ok, why = ha.record(self.answers, ask, "no", now_ms=900)
        self.assertTrue(ok, "PREMISE: the answer could not be stored (%s)" % why)
        r = self._ensure()
        self.assertEqual(r["did"], "left", r)
        self.assertEqual(self.made, [], "a 'No, I open it myself' was overruled")

    def test_unknown_makes_nothing(self):
        def boom(argv, **kw):
            raise OSError("no schtasks")
        self.assertIsNone(self._ensure(run=boom)["did"])
        with io.open(self.marker, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        self.assertIsNone(self._ensure()["did"])
        self.assertEqual(self.made, [], "something was made on an UNKNOWN")

    def test_a_failed_or_invisible_write_is_never_called_created(self):
        r = self._ensure(make=lambda s, rd: (False, "PowerShell refused"))
        self.assertEqual((r["did"], r["why"]), ("failed", "PowerShell refused"))
        r = self._ensure(make=self._make(writes=False))
        self.assertEqual(r["did"], "failed", r)
        self.assertIn("still cannot see it", r["why"])
        self.assertFalse(os.path.exists(self.marker), "a write nobody can see was recorded as made")

    def test_not_windows_touches_nothing(self):
        r = cd.ensure_sign_in_start(self.marker, startup_dir=self.startup, is_win=False, make=self._make())
        self.assertIsNone(r["did"])
        self.assertEqual(self.made, [])


class TheShortcutIsTheInstallersWithBackground(unittest.TestCase):

    def test_the_powershell_it_runs(self):
        d = tempfile.mkdtemp(prefix="signin_mk_")
        try:
            repo = os.path.join(d, "repo")
            os.makedirs(os.path.join(repo, "tv"))
            io.open(os.path.join(repo, "tv", "start_tvd_win.ps1"), "w").close()
            startup = os.path.join(d, "Startup")
            os.makedirs(startup)
            seen = []
            ok, why = cd._make_sign_in_shortcut(startup, repo, run=lambda argv, **kw: seen.append(argv) or _R(0))
            self.assertTrue(ok, why)
            cmd = seen[0][-1]
            for want in (cd.SIGN_IN_LNK, "'powershell.exe'", "-WindowStyle Hidden", "start_tvd_win.ps1",
                         "-Background", "$l.Save()"):
                self.assertIn(want, cmd, "the shortcut is missing %r" % want)
            ok, why = cd._make_sign_in_shortcut(startup, repo, run=lambda argv, **kw: _R(1, "Access denied"))
            self.assertEqual((ok, why), (False, "PowerShell refused to write the shortcut: Access denied"))
            ok, why = cd._make_sign_in_shortcut(startup, os.path.join(d, "nowhere"), run=lambda argv, **kw: _R(0))
            self.assertFalse(ok)
            self.assertIn("launcher is not at", why)
        finally:
            shutil.rmtree(d, True)


class OnlyTheConsoleItselfDoesIt(unittest.TestCase):

    def setUp(self):
        import control_app as ca
        import frame_ref as fr
        self.ca, self.fr = ca, fr
        self.calls = []
        self.saved = (sys.platform, ca._SIGN_IN_SETUP, ca._is_primary_console, cd.ensure_sign_in_start,
                      fr.on_console_path(), os.environ.get("TV_STUB"))
        cd.ensure_sign_in_start = lambda marker, answers_path=None, **kw: (
            self.calls.append((marker, answers_path)) or {"did": "created", "why": "stub"})
        sys.platform = "win32"
        os.environ.pop("TV_STUB", None)

    def tearDown(self):
        sys.platform, self.ca._SIGN_IN_SETUP, self.ca._is_primary_console, cd.ensure_sign_in_start = self.saved[:4]
        self.fr.mark_console_path(self.saved[4])
        if self.saved[5] is None:
            os.environ.pop("TV_STUB", None)
        else:
            os.environ["TV_STUB"] = self.saved[5]

    def _once(self):
        self.ca._SIGN_IN_SETUP = {}
        return self.ca._sign_in_setup_once()

    def test_the_primary_console_does_it_once(self):
        self.ca._is_primary_console = lambda: True
        self.fr.mark_console_path(True)
        r = self._once()
        self.assertEqual(r["did"], "created", r)
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(self.calls[0][0].endswith(".sign_in_start.json"), self.calls[0])
        self.assertEqual(self.calls[0][1], self.ca._his_answers_path())
        self.ca._sign_in_setup_once()
        self.assertEqual(len(self.calls), 1, "one process set up the sign-in start twice")

    def test_never_a_harness_a_scratch_console_or_a_bystander(self):
        self.ca._is_primary_console = lambda: True
        self.fr.mark_console_path(True)
        os.environ["TV_STUB"] = "1"
        self.assertIn("harness", self._once()["why"])
        os.environ.pop("TV_STUB", None)
        self.ca._is_primary_console = lambda: False
        self._once()
        self.ca._is_primary_console = lambda: True
        self.fr.mark_console_path(False)
        self._once()
        self.assertEqual(self.calls, [], "a process that is not the console touched the PC's sign-in")

    def test_the_drift_loop_asks_for_it_beside_the_pull(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_drift_loop")
        at = {}
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id in ("_pull_once", "_sign_in_setup_once"):
                at.setdefault(node.func.id, node.lineno)
        self.assertIn("_sign_in_setup_once", at, "the drift loop never sets up the sign-in start")
        self.assertLess(at["_pull_once"], at["_sign_in_setup_once"])


class TheLauncherStartsHidden(unittest.TestCase):
    """start_tvd_win.ps1, read: PowerShell cannot run on this PC, and CI's Windows boot runs the file itself."""

    @classmethod
    def setUpClass(cls):
        with io.open(os.path.join(HERE, "start_tvd_win.ps1"), "rb") as fh:
            raw = fh.read()
        cls.raw = raw
        cls.src = raw[3:].decode("utf-8") if raw[:3] == b"\xef\xbb\xbf" else raw.decode("utf-8")

    def _block(self, begin, end):
        i = self.src.index(begin)
        return self.src[i:self.src.index(end, i)]

    def test_the_switch_is_its_first_statement(self):
        first = next(ln.strip() for ln in self.src.splitlines() if ln.strip() and not ln.strip().startswith("#"))
        self.assertEqual(first, "param([switch]$Background)")

    def test_a_sign_in_start_opens_hidden(self):
        spawn = self._block("$exeCmd = Get-Command $py.Cmd", "# v1460/v1463 - never spawn")
        self.assertIn("if ($Background) { $argLine += ' --background' }", spawn)

    def test_a_running_console_is_left_exactly_as_it_is(self):
        branch = self._block("if (Test-TvdControlUp) {\n  if ($Background) {", "    return\n  }")
        for wrong in ("Focus-TvdWindow", "Invoke-RestMethod", "front"):
            self.assertNotIn(wrong, branch, "a sign-in start would bring a running console forward (%s)" % wrong)
        after = self.src[self.src.index(branch) + len(branch):][:40]
        self.assertTrue(after.startswith("    return\n  }"), "the sign-in branch does not leave: %r" % after)

    def test_no_window_wait_and_no_dialog(self):
        self.assertIn("if ($ready -and $Background) {", self.src)
        self.assertLess(self.src.index("if ($ready -and $Background) {"), self.src.index("$unhideAfterMs = 8000"))
        err = self._block("function Show-TvdError", "\n}\n")
        self.assertIn("if ($Background) {", err)

    def test_it_stays_ascii(self):
        body = self.raw[3:] if self.raw[:3] == b"\xef\xbb\xbf" else self.raw
        self.assertTrue(all(b < 128 for b in body), "Windows PowerShell 5.1 mis-parses non-ASCII in this file")


RED_PROOF = [
    {"why": "REG-1660 - the console makes a removed sign-in entry again on every boot (it fights his choice)",
     "file": "console_doctor.py",
     "find": "    if m.get(\"madeMs\"):\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-1660 - a PC that answered 'No, I open it myself' is overruled",
     "file": "console_doctor.py",
     "find": "    if no:\n        return {\"did\": \"left\", \"why\": \"this PC answered 'No, I open it myself' - that stands\"}\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1660 - a write the check cannot see is recorded as made",
     "file": "console_doctor.py",
     "find": "    if st2[\"state\"] != OK:\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-1660 - the shortcut starts the console with its window: a sign-in pops it over his game",
     "file": "console_doctor.py",
     "find": "    args = '-NoLogo -WindowStyle Hidden -ExecutionPolicy Bypass -File \"%s\" -Background' % launcher\n",
     "replace": "    args = '-NoLogo -WindowStyle Hidden -ExecutionPolicy Bypass -File \"%s\"' % launcher\n",
     "matches": 1},
    {"why": "REG-1660 - no console ever sets up its sign-in start: the setup is never asked for",
     "file": "control_app.py",
     "find": "                _sign_in_setup_once()   # never raises: every failure is kept as its reason\n",
     "replace": "                pass\n",
     "matches": 1},
    {"why": "REG-1660 - a test harness writes the PC's sign-in start",
     "file": "control_app.py",
     "find": "        elif os.environ.get(\"TV_STUB\"):\n            out[\"why\"] = \"a harness console never touches the PC's sign-in\"\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1660 - the launcher's sign-in start opens the window",
     "file": "start_tvd_win.ps1",
     "find": "if ($Background) { $argLine += ' --background' }   # REG-1660 - hidden from its first second\n",
     "replace": "\n",
     "matches": 1},
    {"why": "REG-1660 - a sign-in start brings an already-running console forward",
     "file": "start_tvd_win.ps1",
     "find": "    Write-TvdLaunchLog 'sign-in start: control already up - left exactly as it is'\n",
     "replace": "    Write-TvdLaunchLog 'sign-in start: control already up'\n    [void](Focus-TvdWindow)\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
