# -*- coding: utf-8 -*-
"""#236 — A SCRATCH CONSOLE NEVER FILMS HIS SCREEN.

MEASURED 2026-09-24, mid-push: the render gate's private console (TV_STUB) went live by itself, the
new game-route picker found HIS GeForce NOW stream in Chrome, and the stub agent captured it frame
after frame into the harness sandbox — the console at 84% CPU, the render step starved at load 12.6,
the push refused. Earlier the same console had filmed a Finder window. A throwaway console has no
business reading his screen at all.

  · DRIVEN: capture_mac with TV_CAPTURE=off returns False, says why, and calls NOTHING that lists or
    grabs a window (the picker, the window grab and every subprocess are stubbed to record calls).
  · STRUCTURAL (AST, not text): render_check's private console is spawned with TV_CAPTURE="off".
RED_PROOF below.
"""
import ast
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import tv_diablo as tv  # noqa: E402


class CaptureOffNeverTouchesTheScreen(unittest.TestCase):

    def setUp(self):
        self._env = os.environ.get("TV_CAPTURE")
        self._saved = {k: getattr(tv, k) for k in ("find_d2r_window_mac", "_capture_window_to_file")}
        self._run = tv.subprocess.run
        self.calls = []
        tv.find_d2r_window_mac = lambda *a, **k: self.calls.append("pick") or (1, "GeForce NOW · x")
        tv._capture_window_to_file = lambda *a, **k: self.calls.append("grab") or True
        tv.subprocess.run = lambda *a, **k: self.calls.append("subprocess %r" % (a[:1],))

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(tv, k, v)
        tv.subprocess.run = self._run
        if self._env is None:
            os.environ.pop("TV_CAPTURE", None)
        else:
            os.environ["TV_CAPTURE"] = self._env

    def test_off_reads_nothing_and_says_so(self):
        os.environ["TV_CAPTURE"] = "off"
        out = os.path.join(tempfile.mkdtemp(prefix="capoff-"), "frame.bmp")
        self.assertFalse(tv.capture_mac(out))
        self.assertEqual(self.calls, [], "capture OFF still reached for the screen: %r" % self.calls)
        self.assertEqual(tv._CAP_TARGET.get("mode"), "off")
        self.assertIn("OFF", tv._CAP_WHY)
        self.assertFalse(os.path.exists(out), "a frame was written with capture off")

    def test_premise_auto_does_reach_for_the_screen(self):
        os.environ["TV_CAPTURE"] = "auto"
        out = os.path.join(tempfile.mkdtemp(prefix="capauto-"), "frame.bmp")
        try:
            tv.capture_mac(out)
        except Exception:
            pass
        self.assertIn("pick", self.calls, "premise: in AUTO the picker is consulted, so the case above can fail")


class ACaptureOffConsoleNeverStartsAReel(unittest.TestCase):
    """The second half, measured on the NEXT push: with capture off, the console's own preflight still
    ran the window finder, saw his GeForce NOW stream, and the SHADOW reader rolled a reel."""

    def setUp(self):
        import control_app as ca
        self.ca = ca
        self._env = os.environ.get("TV_CAPTURE")
        self._find = tv.find_d2r_window_mac
        self.looked = []
        tv.find_d2r_window_mac = lambda *a, **k: self.looked.append(1) or (1, "GeForce NOW \u00b7 Google Chrome")

    def tearDown(self):
        tv.find_d2r_window_mac = self._find
        if self._env is None:
            os.environ.pop("TV_CAPTURE", None)
        else:
            os.environ["TV_CAPTURE"] = self._env

    def test_the_preflight_sees_no_window_and_never_looks(self):
        os.environ["TV_CAPTURE"] = "off"
        pre = self.ca.capture_preflight("shadow", look_for_window=True)
        self.assertIs(pre.get("windowSeen"), False, "a capture-off console reported a game window: %r" % pre)
        self.assertEqual(self.looked, [], "a capture-off console still ran the window finder")
        self.assertIn("capture is OFF", pre.get("windowWhy") or "")

    def test_premise_with_capture_on_the_finder_is_asked(self):
        os.environ["TV_CAPTURE"] = "auto"
        pre = self.ca.capture_preflight("shadow", look_for_window=True)
        self.assertEqual(self.looked, [1], "premise: in AUTO the preflight asks the finder")
        self.assertIs(pre.get("windowSeen"), True)


class EveryGrabberHonoursCaptureOff(unittest.TestCase):
    """The second eye on 298de387 (grok-4.7): TV_CAPTURE=off stopped capture_mac ONLY. The Mac film thread
    idled on "waiting" alone and fell through to its fullscreen fallback under "off"; the Windows loop
    treated "off" like auto and still found, grabbed and filmed the desktop."""

    def test_the_film_thread_consults_the_switch(self):
        self.assertIn("_capture_is_off", tv._film_loop.__code__.co_names,
                      "the film thread does not ask whether capture is off - it films under TV_CAPTURE=off")
        was = os.environ.get("TV_CAPTURE")
        try:
            os.environ["TV_CAPTURE"] = "off"
            self.assertTrue(tv._capture_is_off())
            os.environ["TV_CAPTURE"] = "auto"
            self.assertFalse(tv._capture_is_off(), "premise: auto is not off")
        finally:
            if was is None:
                os.environ.pop("TV_CAPTURE", None)
            else:
                os.environ["TV_CAPTURE"] = was

    def test_the_windows_loop_leaves_before_it_grabs(self):
        src = io.open(os.path.join(HERE, "capture_win.ps1"), encoding="utf-8-sig").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        i = code.find("if ($mode -eq 'off' -or $mode -eq 'none') {")
        self.assertGreater(i, -1, "the Windows capture loop has no stop for TV_CAPTURE=off")
        self.assertLess(i, code.find("while ($true) {"), "the stop comes after the loop starts grabbing")
        self.assertIn("exit 0", code[i:code.find("}", i + 1)])   # bounded by the block's own brace


class TheRenderHarnessSpawnsItsConsoleWithCaptureOff(unittest.TestCase):

    def test_the_private_console_env_carries_TV_CAPTURE_off(self):
        src = io.open(os.path.join(HERE, "render_check.py"), encoding="utf-8").read()
        fn = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "_serve_console"]
        self.assertEqual(len(fn), 1, "premise: render_check._serve_console moved")
        found = False
        for c in ast.walk(fn[0]):
            if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "dict":
                for kw in c.keywords or ():
                    if kw.arg == "TV_CAPTURE" and isinstance(kw.value, ast.Constant) and kw.value.value == "off":
                        found = True
        self.assertTrue(found, "the render harness's private console can film his screen again (no TV_CAPTURE='off')")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the second eye on 298de387 - the Mac film thread films under TV_CAPTURE=off again (fullscreen fallback)",
        "file": "tv_diablo.py",
        "find": "            if _capture_is_off() or (_CAP_TARGET or {}).get(\"mode\") == \"off\":\n",
        "replace": "            if False:\n",
        "matches": 1,
    },
    {
        "why": "the second eye on 298de387 - the Windows capture loop treats TV_CAPTURE=off like auto again and films the desktop",
        "file": "capture_win.ps1",
        "find": "if ($mode -eq 'off' -or $mode -eq 'none') {\n",
        "replace": "if ($false) {\n",
        "matches": 1,
    },
    {
        "why": "#236 - a capture-off console runs the window finder again, sees his stream, and its shadow reader rolls a reel mid-push",
        "file": "control_app.py",
        "find": "    if look_for_window and (os.environ.get(\"TV_CAPTURE\") or \"\").strip().lower() in (\"off\", \"none\"):\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "#236 - TV_CAPTURE=off falls through to the picker again: a scratch console films his screen",
        "file": "tv_diablo.py",
        "find": "    if mode in (\"off\", \"none\"):\n        _CAP_WHY = \"capture is OFF",
        "replace": "    if False:\n        _CAP_WHY = \"capture is OFF",
        "matches": 1,
    },
    {
        "why": "#236 - the render harness spawns its private console without TV_CAPTURE=off (it filmed his GeForce NOW stream mid-push)",
        "file": "render_check.py",
        "find": "               TV_CAPTURE=\"off\",\n",
        "replace": "",
        "matches": 1,
    },
]
