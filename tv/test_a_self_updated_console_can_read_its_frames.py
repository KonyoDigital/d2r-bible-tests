# -*- coding: utf-8 -*-
"""#227 / REG-1260 — A SELF-UPDATED CONSOLE CAN READ ITS OWN FRAMES.

MEASURED 2026-09-24 over SSH on the Windows ALT: its tree held the launcher's Pillow step (6ed85ece),
its consoles were started at 20:26 and 21:06, and Pillow was still missing - start_tvd_win.log's last
line was 19:04. Every later start was the console's own os.execv after a self-update, which never runs
start_tvd_win.ps1. So the console now makes sure of Pillow itself, at boot.

  · DRIVEN: on Windows with PIL absent, the boot step runs `python.exe -m pip install --user Pillow`
    (never pythonw), hidden, and records the attempt on console_doctor.PILLOW_BOOT.
  · DRIVEN: PIL present -> no pip at all. Not Windows, or a scratch console -> nothing.
  · DRIVEN: a pip failure is recorded as a failure, with pip's words - never as "installed".
  · DRIVEN: the doctor row, with PIL unimportable, quotes the boot attempt - and no longer promises
    that the launcher will install it.
  · COMPILER: main() starts the step in its own thread.
RED_PROOF below.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as cd  # noqa: E402
import control_app as ca  # noqa: E402
import win_relaunch as wr  # noqa: E402


class _P(object):
    def __init__(self, rc, err=""):
        self.returncode, self.stderr, self.stdout = rc, err, ""


class ASelfUpdatedConsoleCanReadItsFrames(unittest.TestCase):

    def setUp(self):
        self._win, self._exe = ca.IS_WIN, sys.executable
        self._scratch = wr.scratch_console
        self._boot = cd.PILLOW_BOOT
        ca.IS_WIN = True
        wr.scratch_console = lambda *a, **k: False
        sys.executable = r"C:\Py\pythonw.exe"
        self.calls = []
        self.present = [False]

    def tearDown(self):
        ca.IS_WIN, sys.executable = self._win, self._exe
        wr.scratch_console = self._scratch
        cd.PILLOW_BOOT = self._boot

    def _find(self, name):
        return object() if self.present[0] else None

    def _run(self, rc=0, err="", becomes=True):
        def run(argv, **kw):
            self.calls.append((argv, kw))
            if rc == 0 and becomes:
                self.present[0] = True
            return _P(rc, err)
        return run

    def test_a_missing_pillow_is_installed_by_the_console_itself(self):
        rec = ca._ensure_pillow_at_boot(_find=self._find, _run=self._run())
        self.assertEqual(len(self.calls), 1, "the console never tried to install Pillow")
        argv, kw = self.calls[0]
        self.assertEqual(argv[0], r"C:\Py\python.exe", "pip must run under python.exe, never pythonw")
        self.assertEqual(argv[1:], ["-m", "pip", "install", "--user", "--quiet", "Pillow"])
        self.assertEqual(kw.get("creationflags"), ca._WIN_CREATE, "the install would flash a window on his screen")
        self.assertIs(rec.get("ok"), True)
        self.assertIs(cd.PILLOW_BOOT, rec, "the doctor cannot see the attempt")

    def test_present_pillow_is_left_alone(self):
        self.present[0] = True
        rec = ca._ensure_pillow_at_boot(_find=self._find, _run=self._run())
        self.assertEqual(self.calls, [])
        self.assertIs(rec.get("tried"), False)

    def test_not_windows_or_scratch_does_nothing(self):
        ca.IS_WIN = False
        self.assertIsNone(ca._ensure_pillow_at_boot(_find=self._find, _run=self._run()))
        ca.IS_WIN = True
        wr.scratch_console = lambda *a, **k: True
        self.assertIsNone(ca._ensure_pillow_at_boot(_find=self._find, _run=self._run()))
        self.assertEqual(self.calls, [], "a scratch console installed packages on the runner")

    def test_a_failed_pip_is_a_failure_with_its_words(self):
        rec = ca._ensure_pillow_at_boot(_find=self._find, _run=self._run(rc=1, err="no network"))
        self.assertIs(rec.get("ok"), False)
        self.assertIn("no network", rec.get("why") or "")

    def test_the_row_quotes_the_boot_attempt_and_promises_no_launcher(self):
        cd.PILLOW_BOOT = {"tried": True, "ok": False, "why": "pip exited 1: no network"}
        real_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def no_pil(name, *a, **k):
            if name == "PIL" or name.startswith("PIL."):
                raise ImportError("No module named 'PIL'")
            return real_import(name, *a, **k)
        import builtins
        builtins.__import__ = no_pil
        try:
            state, why = cd._check_this_machine_can_decode_a_frame()
        finally:
            builtins.__import__ = real_import
        self.assertEqual(state, cd.MISSING)
        self.assertIn("tried to install it at boot", why)
        self.assertIn("no network", why)
        self.assertNotIn("launcher installs it", why, "the row still promises a launcher run that a self-updated console never makes")

    def test_main_starts_the_step(self):
        self.assertIn("_ensure_pillow_at_boot", ca.main.__code__.co_names,
                      "main() never starts the boot Pillow step - only a double-click would ever install it")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1260 - main() stops starting the boot Pillow step: a self-updated console never gets Pillow again",
        "file": "control_app.py",
        "find": "    threading.Thread(target=_ensure_pillow_at_boot, daemon=True, name=\"tvd-pillow\").start()\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1260 - pip runs under pythonw again (no stdout; the install silently does nothing useful)",
        "file": "control_app.py",
        "find": "        exe = exe[:-len(\"pythonw.exe\")] + \"python.exe\"     # pythonw has no stdout for pip to write to\n",
        "replace": "        pass\n",
        "matches": 1,
    },
]
