# -*- coding: utf-8 -*-
"""v3746 (REG-2256) — A SELF-UPDATE RELAUNCH OPENS MINIMIZED, NOT OVER HIS GAME.

His words: *"is there a way to relaunch the console after it updates and relaunches itself instead of
alt-tabbing me from my game or something im doing maybe it can open automatically minimized?"*

The machinery to open minimized + unfocused already exists: TV_QUIET_RELAUNCH crosses os.execv and
_control_window_kwargs turns it into `minimized=True, focus=False`. It was wired for the shadow-reel relaunch
and for a console that was already in the tracked background. The GAP his request names: while he plays, the
console is usually fullscreen BEHIND the game and _BACKGROUND["on"] is False, so a self-update relaunch
(_drift_loop) — or a rescue / green-light exec — was NOT quiet and opened fullscreen, pulling focus off D2R.

The fix joins the half that was already there: quiet_relaunch_reason now takes `where` (the os.execv site
_before_exec already knows) and returns a quiet reason for an AUTOMATIC relaunch regardless of background. A
MANUAL relaunch (/api/relaunch, which he clicks from the foreground; or a fresh Desktop launch, which carries
no `where`) stays normal/focused — he asked for that window.

Trace-level only. Whether the Cocoa window really keeps focus off D2R is GrokBot's live check on his screen.
RED_PROOF below mutates control_app.py back to the old behaviour and this file goes red.
"""
import ast
import inspect
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
try:
    import fixture_tmp as _fx_tmp  # noqa: E402 — this run's scratch dirs leave with it
    _fx_tmp.contain()
except Exception:
    pass
import control_app as ca  # noqa: E402

AUTO = ("_drift_loop", "_exec_relaunch_now", "_exec_relaunch_soon")


class _EnvBase(unittest.TestCase):
    """Saves every global and env key _control_window_kwargs reads, so no test leaks into another."""

    _ENV = ("TV_QUIET_RELAUNCH", "TV_START_HIDDEN", "TV_WINDOWED")
    _GLOB = ("_REOPEN_SHOW", "_QUIET_BOOT", "_HIDDEN_BOOT")

    def setUp(self):
        self._env = {k: os.environ.get(k) for k in self._ENV}
        self._glob = {k: getattr(ca, k, None) for k in self._GLOB}
        self._had = {k: hasattr(ca, k) for k in self._GLOB}
        self._bg = dict(ca._BACKGROUND)
        self._argv = list(sys.argv)
        for k in self._ENV:
            os.environ.pop(k, None)
        for k in self._GLOB:
            setattr(ca, k, None)
        ca._BACKGROUND.update(on=False, since=None, by=None, wasFullscreen=None)
        sys.argv[:] = ["control_app.py", "--open"]

    def tearDown(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        for k in self._GLOB:
            if self._had.get(k):
                setattr(ca, k, self._glob[k])
            elif hasattr(ca, k):
                delattr(ca, k)
        ca._BACKGROUND.clear()
        ca._BACKGROUND.update(self._bg)
        sys.argv[:] = self._argv


class AnAutomaticRelaunchIsQuietRegardlessOfBackground(_EnvBase):

    def test_each_auto_exec_site_is_quiet_even_with_the_window_in_front(self):
        for where in AUTO:
            reason = ca.quiet_relaunch_reason(None, {"on": False}, where)
            self.assertTrue(
                reason,
                "an automatic relaunch (%s) with the console in front was NOT marked quiet — it would open "
                "fullscreen and alt-tab him out of his game" % where)
            self.assertIn(where, reason, "the quiet reason should name the exec site that fired it")

    def test_a_manual_relaunch_in_front_opens_normally(self):
        # /api/relaunch is the button he clicks from the foreground; a fresh Desktop launch carries no `where`.
        self.assertIsNone(
            ca.quiet_relaunch_reason(None, {"on": False}, "/api/relaunch"),
            "the relaunch BUTTON he pressed opened minimized — he asked for the window and wants to see it")
        self.assertIsNone(
            ca.quiet_relaunch_reason(None, {"on": False}, None),
            "a fresh launch with no exec-site opened minimized")

    def test_membership_is_exact_not_substring(self):
        # a naive `"relaunch" in where` would wrongly catch the manual button, whose name contains "relaunch".
        self.assertIsNone(ca.quiet_relaunch_reason(None, {"on": False}, "/api/relaunch"))
        self.assertIsNone(ca.quiet_relaunch_reason(None, {"on": False}, "some_other_relaunch_caller"))

    def test_the_old_rules_are_unchanged(self):
        # a backgrounded console is still quiet whoever relaunches it; an earlier (shadow-reel) reason wins.
        self.assertIsNone(ca.quiet_relaunch_reason(None, {"on": False}))
        self.assertIn("background",
                      ca.quiet_relaunch_reason(None, {"on": True, "by": "window-close"}, "/api/relaunch") or "",
                      "a backgrounded console stopped opening minimized")
        self.assertEqual(ca.quiet_relaunch_reason("shadow reel", {"on": False}, "_drift_loop"), "shadow reel",
                         "an auto `where` overwrote the shadow-reel reason that was set first")


class TheExecPathActuallyPassesTheSite(_EnvBase):
    """the-unjoined-end: quiet_relaunch_reason only helps if _before_exec hands it the real exec site."""

    def _quiet_call(self):
        tree = ast.parse(inspect.getsource(ca._before_exec))
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "quiet_relaunch_reason"]
        self.assertEqual(len(calls), 1, "expected exactly one quiet_relaunch_reason call in _before_exec")
        return calls[0]

    def test_before_exec_passes_where_as_the_third_argument(self):
        call = self._quiet_call()
        self.assertGreaterEqual(
            len(call.args), 3,
            "_before_exec calls quiet_relaunch_reason WITHOUT the exec site — an auto relaunch can never be "
            "told from a manual one, so the fix is a dead end")
        third = call.args[2]
        self.assertTrue(isinstance(third, ast.Name) and third.id == "where",
                        "the third argument is not _before_exec's own `where` parameter")


class TheQuietFlagReachesTheWindow(_EnvBase):
    """The chassis the fix connects to: TV_QUIET_RELAUNCH (set by _before_exec) -> a minimized, unfocused
    window; its absence -> a normal fullscreen one. Proven green so a later change here cannot silently
    unwire the minimized relaunch."""

    def test_the_quiet_env_opens_the_window_minimized_and_unfocused(self):
        os.environ["TV_QUIET_RELAUNCH"] = ca.quiet_relaunch_reason(None, {"on": False}, "_drift_loop")
        kw = ca._control_window_kwargs("http://127.0.0.1:1/")
        self.assertIs(kw.get("minimized"), True, "a self-update relaunch did not open minimized: %r" % kw)
        self.assertIs(kw.get("focus"), False, "a self-update relaunch stole focus: %r" % kw)
        self.assertNotIn("fullscreen", kw, "a quiet relaunch asked for fullscreen, which shows over his game")
        self.assertIsNone(os.environ.get("TV_QUIET_RELAUNCH"), "the quiet mark was not consumed ONCE")

    def test_a_manual_relaunch_opens_normal_and_fullscreen(self):
        # no TV_QUIET_RELAUNCH (manual /api/relaunch in front produced no quiet reason) -> the usual window.
        self.assertIsNone(os.environ.get("TV_QUIET_RELAUNCH"))
        kw = ca._control_window_kwargs("http://127.0.0.1:1/")
        self.assertNotIn("minimized", kw, "a manual relaunch opened minimized: %r" % kw)
        self.assertIs(kw.get("fullscreen"), True, "a manual relaunch did not open fullscreen as always: %r" % kw)


# ── RED_PROOF ─ each mutation reverts one half of the fix in control_app.py; this file must then go red.
RED_PROOF = [
    {
        "why": "v3746 (REG-2256) - without the auto-site clause a self-update relaunch in front opens over his game",
        "file": "tv/control_app.py",
        "find": "    # The os.execv sites that fire on their own (see _before_exec's where). /api/relaunch is NOT one of them.\n    if where in (\"_drift_loop\", \"_exec_relaunch_now\", \"_exec_relaunch_soon\"):\n        return \"an automatic relaunch (%s) opens minimized so it never pulls focus from his game\" % where\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "v3746 (REG-2256) - if _before_exec drops `where`, an auto relaunch can never be told from a manual one",
        "file": "tv/control_app.py",
        "find": "    _q = quiet_relaunch_reason(os.environ.get(\"TV_QUIET_RELAUNCH\"), _BACKGROUND, where)\n",
        "replace": "    _q = quiet_relaunch_reason(os.environ.get(\"TV_QUIET_RELAUNCH\"), _BACKGROUND)\n",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
