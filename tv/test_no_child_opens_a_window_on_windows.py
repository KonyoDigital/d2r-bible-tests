# -*- coding: utf-8 -*-
"""REG-1307 — NO CHILD OF THE CONSOLE OR THE AGENT MAY OPEN A WINDOW ON WINDOWS.

His report, 2026-09-26: "a window terminal keeps jumping up and alt tabbing me and even deans computer ... it has some
background process that jumps all the time and exits us from the game.. i need this hidden... no window should be
opening". pythonw.exe has no console, so every console-subsystem child it starts gets a NEW visible window unless the
spawn says CREATE_NO_WINDOW. MEASURED: 82 spawn sites across 38 tv/ modules pass no creationflags - 24 of them in
control_app / tv_diablo / console_doctor, which run on his Windows machine every tick. tv/win_quiet.py replaces
subprocess.Popen ONCE per process (run / call / check_output all build Popen from the module's globals), so every
spawn - present and future - is windowless. Nothing here can spawn a real Windows process, so the shipped install()
is driven against a fake subprocess module shaped like Windows' (STARTUPINFO, Popen, and a run() that looks Popen up
at call time exactly as CPython's does).

  · DRIVEN: on win32 every child gets CREATE_NO_WINDOW and SW_HIDE - through Popen AND through run().
  · DRIVEN: a caller that asks for a window on purpose (CREATE_NEW_CONSOLE / DETACHED_PROCESS) keeps it; other flags
    (CREATE_NEW_PROCESS_GROUP) are kept and NO_WINDOW is added; a caller's own startupinfo is left alone.
  · DRIVEN: off Windows it changes nothing; a second install is a no-op.
  · JOINED: control_app.py and tv_diablo.py install it BEFORE their first spawn call.
RED_PROOF below.
"""
import ast
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import win_quiet as WQ  # noqa: E402


def _fake_windows_subprocess():
    class STARTUPINFO(object):
        def __init__(self):
            self.dwFlags = 0
            self.wShowWindow = 1

    calls = []

    class Popen(object):
        def __init__(self, args, **kw):
            calls.append((args, kw))

    mod = type(sys)("fake_subprocess")
    mod.STARTUPINFO = STARTUPINFO
    mod.Popen = Popen

    def run(args, **kw):              # CPython's run(): `with Popen(*popenargs, **kwargs)` from module globals
        return mod.Popen(args, **kw)
    mod.run = run
    mod.calls = calls
    return mod


class NoChildOpensAWindowOnWindows(unittest.TestCase):

    def test_every_child_is_windowless_through_popen_and_run(self):
        m = _fake_windows_subprocess()
        ok, why = WQ.install(mod=m, platform="win32")
        self.assertTrue(ok, why)
        m.Popen(["git", "fetch"])
        m.run(["schtasks", "/query"], capture_output=True)
        self.assertEqual(len(m.calls), 2)
        for args, kw in m.calls:
            self.assertTrue(kw.get("creationflags", 0) & WQ.CREATE_NO_WINDOW,
                            "%s would open a window on his screen: %r" % (args[0], kw))
            si = kw.get("startupinfo")
            self.assertIsNotNone(si, "%s has no STARTUPINFO, so SW_HIDE is not asked for" % args[0])
            self.assertEqual(si.wShowWindow, WQ.SW_HIDE)
            self.assertTrue(si.dwFlags & WQ.STARTF_USESHOWWINDOW)
        self.assertEqual(m.calls[1][1].get("capture_output"), True, "the caller's own arguments were changed")

    def test_a_window_asked_for_on_purpose_is_kept_and_other_flags_survive(self):
        m = _fake_windows_subprocess()
        WQ.install(mod=m, platform="win32")
        m.Popen(["cmd"], creationflags=WQ.CREATE_NEW_CONSOLE)
        m.Popen(["python"], creationflags=0x00000200)          # CREATE_NEW_PROCESS_GROUP
        own = m.STARTUPINFO()
        m.Popen(["x"], startupinfo=own)
        self.assertEqual(m.calls[0][1]["creationflags"], WQ.CREATE_NEW_CONSOLE, "a deliberate window was hidden")
        self.assertEqual(m.calls[1][1]["creationflags"], 0x00000200 | WQ.CREATE_NO_WINDOW)
        self.assertIs(m.calls[2][1]["startupinfo"], own, "a caller's own STARTUPINFO was replaced")

    def test_off_windows_nothing_changes_and_install_is_idempotent(self):
        m = _fake_windows_subprocess()
        orig = m.Popen
        ok, _ = WQ.install(mod=m, platform="darwin")
        self.assertFalse(ok)
        self.assertIs(m.Popen, orig)
        self.assertTrue(WQ.install(mod=m, platform="win32")[0])
        first = m.Popen
        self.assertFalse(WQ.install(mod=m, platform="win32")[0], "a second install wrapped Popen twice")
        self.assertIs(m.Popen, first)

    def test_both_windows_processes_install_it_before_their_first_spawn(self):
        for name in ("control_app.py", "tv_diablo.py"):
            with open(os.path.join(HERE, name), encoding="utf-8") as fh:
                src = fh.read()
            tree = ast.parse(src)
            inst = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute) and n.func.attr == "install"
                    and isinstance(n.func.value, ast.Name) and n.func.value.id == "_win_quiet"]
            spawns = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call)
                      and isinstance(n.func, ast.Attribute)
                      and n.func.attr in ("Popen", "run", "call", "check_output", "check_call")
                      and isinstance(n.func.value, ast.Name) and n.func.value.id == "subprocess"]
            self.assertEqual(len(inst), 1, "%s does not install win_quiet exactly once" % name)
            self.assertTrue(spawns, "%s: no spawn found - the law measures nothing" % name)
            self.assertLess(inst[0], min(spawns), "%s spawns a child before win_quiet is installed" % name)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1307 - Popen is never replaced: every child of the console opens a window on his screen again",
        "file": "win_quiet.py",
        "find": "    mod.Popen = QuietPopen\n",
        "replace": "    pass\n",
        "matches": 1,
    },
    {
        "why": "REG-1307 - children get no CREATE_NO_WINDOW flag, so the terminal jumps up and pulls him out of the game",
        "file": "win_quiet.py",
        "find": "        kw[\"creationflags\"] = flags | CREATE_NO_WINDOW\n",
        "replace": "        pass\n",
        "matches": 1,
    },
    {
        "why": "REG-1307 - the console process never installs it, so its 10 spawn sites open windows again",
        "file": "control_app.py",
        "find": "    import win_quiet as _win_quiet\n    _win_quiet.install()\n",
        "replace": "    import win_quiet as _win_quiet\n",
        "matches": 1,
    },
    {
        "why": "REG-1307 - the agent process never installs it, so its spawn sites open windows again",
        "file": "tv_diablo.py",
        "find": "    import win_quiet as _win_quiet\n    _win_quiet.install()\n",
        "replace": "    import win_quiet as _win_quiet\n",
        "matches": 1,
    },
]
