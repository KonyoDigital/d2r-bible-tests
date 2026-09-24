# -*- coding: utf-8 -*-
"""#229 / REG-1266 — THE KAI CLOSER READS FRAMES ON EVERY OS.

The closer hard-coded bin/ocr_mac and returned when it was not executable, so on Windows it ended at boot
while tv_diablo's _ocr_worker_cmd() had returned the Windows worker (ocr_win.ps1) since v818. MEASURED on the
ALT 2026-09-25: the OS OCR engine is present and ocr_win.ps1 read "Harlequin Crest" / "Shako" in 208 ms.

  · COMPILER: _kai_closer_loop asks tv_diablo._ocr_worker_cmd and names no single-platform binary.
  · DRIVEN: with the seam answering nothing the closer returns at once (not plugged, honestly); with the
    seam answering a worker it gets past the gate (it reaches its first sleep).
  · COMPILER: the worker spawn passes creationflags, so a pythonw console never flashes a window.
RED_PROOF below.
"""
import ast
import inspect
import os
import sys
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as ca  # noqa: E402
import tv_diablo as tvd  # noqa: E402


class _Reached(Exception):
    pass


class TheCloserReadsFramesOnEveryOs(unittest.TestCase):

    def setUp(self):
        self._cmd, self._sleep, self._kai = tvd._ocr_worker_cmd, ca.time.sleep, os.environ.get("TV_KAI")
        os.environ["TV_KAI"] = "1"

    def tearDown(self):
        tvd._ocr_worker_cmd, ca.time.sleep = self._cmd, self._sleep
        if self._kai is None:
            os.environ.pop("TV_KAI", None)
        else:
            os.environ["TV_KAI"] = self._kai

    def _tree(self):
        return ast.parse(textwrap.dedent(inspect.getsource(ca._kai_closer_loop)))

    def test_it_asks_the_platform_seam(self):
        tree = self._tree()
        attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        self.assertIn("_ocr_worker_cmd", attrs, "the closer no longer asks tv_diablo which OCR worker this OS has")
        consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        self.assertNotIn("ocr_mac", consts, "the closer hard-codes the Mac binary again - Windows is dark")

    def test_no_worker_returns_at_once(self):
        tvd._ocr_worker_cmd = lambda: None

        def no_sleep(s):
            raise _Reached()
        ca.time.sleep = no_sleep
        self.assertIsNone(ca._kai_closer_loop(), "with no worker the closer must end before it sleeps")

    def test_a_worker_gets_past_the_gate(self):
        tvd._ocr_worker_cmd = lambda: ["powershell.exe", "-File", "ocr_win.ps1"]

        def stop(s):
            raise _Reached()
        ca.time.sleep = stop
        with self.assertRaises(_Reached, msg="a Windows worker was offered and the closer still quit at the gate"):
            ca._kai_closer_loop()

    def test_the_spawn_is_windowless(self):
        calls = [n for n in ast.walk(self._tree()) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == "Popen"]
        self.assertTrue(calls, "premise: the closer spawns its worker")
        self.assertTrue(all(any(k.arg == "creationflags" for k in c.keywords) for c in calls),
                        "the worker spawn has no creationflags - powershell opens a window under pythonw")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1266 - the closer hard-codes bin/ocr_mac again: Windows never reads a frame",
        "file": "control_app.py",
        "find": "        ocr_argv = list(_tvd_ocr._ocr_worker_cmd() or [])\n",
        "replace": "        ocr_argv = [os.path.join(HERE, \"bin\", \"ocr_mac\")] if os.access(os.path.join(HERE, \"bin\", \"ocr_mac\"), os.X_OK) and not IS_WIN else []\n",
        "matches": 1,
    },
    {
        "why": "REG-1266 - the worker spawn loses its creationflags: a powershell window flashes on his screen",
        "file": "control_app.py",
        "find": "                                      creationflags=_WIN_CREATE if IS_WIN else 0)\n",
        "replace": "                                      )\n",
        "matches": 1,
    },
]
