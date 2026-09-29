# -*- coding: utf-8 -*-
"""2026-09-29 — CLOSING THE WINDOW NO LONGER STOPS THE CONSOLE (REG-1430).

His words: *"make sure after the console is up and running there is a default ON true for shadow reader and
tooltips pass on and background service running with the console hidden always by design"* and *"that way
sessions are always working and running based on games and sessions being done regardless if the console is
on or not. a one time update to the newer version should keep it backgrounded"*.

✕ used to END everything (v935.8: "exiting the console must stop ON AIR"), so a session he played with the
window shut was never filmed. Now ✕ and Esc HIDE the console completely - his second word, 02:55: "make sure
this thing and window is completely hidden" - no window, no taskbar button, no Dock icon, and every lane keeps
running. v1460's scar (a hidden window no focus path could find) is answered by a BUILT way back: the Desktop
icon and a second launch ask the running console to show itself. ⏻ quit, /api/quit with a `from`, a
window-only view and TV_CLOSE_EXITS=1 still exit.

DRIVEN on the shipped functions with a fake pywebview window (no real window is ever opened, no quit is ever
armed - `_request_console_exit` is replaced by a recorder in every case that could reach it):
  · the close handler CANCELS the close and hides the window (not minimize); a real quit lets it close
  · a real exit records itself FIRST, so the handler knows to let it through
  · macOS leaves fullscreen before hiding and goes back to fullscreen when it returns, drops its Dock icon while
    hidden, and reads fullscreen from the window's own style bit (frame and flag both lied, measured);
    Windows hides as is and comes back with Show + SW_RESTORE, never pywebview's restore()
  · the OS minimize / restore events keep the state true to the window
  · the rescue watchdog holds while backgrounded; an update relaunch stays backgrounded; a quiet boot is
    backgrounded from its first second
  · a second launch and both launchers bring a hidden console FORWARD instead of replacing it
RED_PROOF below.
"""
import inspect
import io
import json
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
import fixture_tmp as _fx_tmp  # noqa: E402  — this run's scratch dirs leave with it
_fx_tmp.contain()
import control_app as ca  # noqa: E402

LAUNCHER = os.path.join(HERE, "start_tvd_mac.sh")
WIN_LAUNCHER = os.path.join(HERE, "start_tvd_win.ps1")


class _Ev(object):
    def is_set(self):
        return True


class _Events(object):
    shown = _Ev()


class _FakeWin(object):
    """What the shipped code touches on a pywebview Window - and nothing that could open or close one."""

    def __init__(self, w=1440, h=900):
        self.events = _Events()
        self.width, self.height = w, h
        self.calls = []

    def minimize(self):
        self.calls.append("minimize")

    def hide(self):
        self.calls.append("hide")

    def restore(self):
        self.calls.append("restore")

    def show(self):
        self.calls.append("show")

    def toggle_fullscreen(self):
        self.calls.append("toggle_fullscreen")


def _no_sleep(_s):
    return None


class _Base(unittest.TestCase):
    KEEP = ("_MAIN_WIN", "_EXIT_REQUESTED", "_WINDOW_ONLY", "_BG_SPAWN", "_request_console_exit",
            "_win_is_fullscreen", "_win_focus_existing_console", "_RE_FULLSCREEN_BUSY", "_mac_set_dock_icon",
            "_mac_fullscreen_bit")

    def setUp(self):
        self._saved = {k: getattr(ca, k, None) for k in self.KEEP}
        self._had = {k: hasattr(ca, k) for k in self.KEEP}
        self._bg = dict(ca._BACKGROUND)
        self._plat = sys.platform
        self.exits = []
        ca._request_console_exit = lambda reason="quit", hard_delay=None: self.exits.append(reason) or {"ok": True}
        ca._BG_SPAWN = lambda fn: fn()
        ca._EXIT_REQUESTED = None
        ca._WINDOW_ONLY = False
        ca._RE_FULLSCREEN_BUSY = False
        ca._BACKGROUND.update(on=False, since=None, by=None, wasFullscreen=None)
        self.win = _FakeWin()
        ca._MAIN_WIN = self.win
        self.dock = []
        ca._mac_set_dock_icon = lambda show: self.dock.append(bool(show)) or sys.platform == "darwin"

    def tearDown(self):
        sys.platform = self._plat
        for k in self.KEEP:
            if self._had[k]:
                setattr(ca, k, self._saved[k])
            elif hasattr(ca, k):
                delattr(ca, k)
        ca._BACKGROUND.clear()
        ca._BACKGROUND.update(self._bg)


class WhatTheCloseButtonDoes(_Base):

    def test_the_default_is_the_background_and_every_real_quit_still_quits(self):
        self.assertTrue(ca.close_means_background(None, False, env={})[0],
                        "✕ still quits by default - the sessions he plays with the window shut are never filmed")
        self.assertFalse(ca.close_means_background("api-quit:quit-button", False, env={})[0],
                         "⏻ quit no longer quits - he cannot stop the console on purpose")
        self.assertFalse(ca.close_means_background(None, True, env={})[0],
                         "closing a window-only view backgrounds it instead of closing just that view")
        self.assertFalse(ca.close_means_background(None, False, env={"TV_CLOSE_EXITS": "1"})[0],
                         "TV_CLOSE_EXITS=1 no longer restores the old ✕")
        self.assertTrue(ca.close_means_background(None, False, env={"TV_CLOSE_EXITS": "0"})[0],
                        "TV_CLOSE_EXITS=0 read as set")

    def test_the_shipped_close_handler_cancels_the_close_and_minimizes(self):
        ca._win_is_fullscreen = lambda win, screens=None: False
        allowed = ca._on_console_window_closing()
        self.assertIs(allowed, False, "the close handler let the window close - pywebview cancels only on False")
        self.assertEqual(self.win.calls, ["hide"], "the window was not hidden completely (his words: 'completely "
                                                   "hidden'): %r" % self.win.calls)
        self.assertEqual(self.exits, [], "a ✕ that should background asked the console to EXIT: %r" % self.exits)
        m = ca.window_mode_payload()
        self.assertEqual(m["mode"], "background", m)
        self.assertEqual(m["by"], "window-close", m)

    def test_a_real_quit_lets_the_window_close_and_never_minimizes(self):
        ca._EXIT_REQUESTED = "api-quit:quit-button"
        allowed = ca._on_console_window_closing()
        self.assertIs(allowed, True, "a real quit was turned into a minimize - he could never stop the console")
        self.assertEqual(self.win.calls, [], "a real quit minimized the window: %r" % self.win.calls)
        self.assertEqual(self.exits, ["window-closing"], self.exits)
        self.assertFalse(ca._BACKGROUND["on"])

    def test_a_real_exit_records_itself_before_anything_else(self):
        """The window's destroy() fires the same `closing` event, so the exit must be on record first."""
        saved = {k: getattr(ca, k) for k in ("_mark_window_gone", "_schedule_exit_stop", "_arm_force_exit")}
        real_exit = self._saved["_request_console_exit"]
        try:
            seen = []
            ca._mark_window_gone = lambda reason="": seen.append(ca._EXIT_REQUESTED)
            ca._schedule_exit_stop = lambda reason="quit": None
            ca._arm_force_exit = lambda reason="quit", delay=None: None
            ca._MAIN_WIN = None
            real_exit("api-quit:quit-button")
        finally:
            for k, v in saved.items():
                setattr(ca, k, v)
        self.assertEqual(seen, ["api-quit:quit-button"],
                         "the exit was not on record when the window started to go - the close handler "
                         "would minimize a console he asked to quit")


class FullscreenOnEachPlatform(_Base):

    def test_the_mac_leaves_fullscreen_then_hides_drops_the_dock_icon_and_goes_back(self):
        sys.platform = "darwin"
        state = {"fs": True}
        ca._win_is_fullscreen = lambda win, screens=None: state["fs"]

        def _tog():
            self.win.calls.append("toggle_fullscreen")
            state["fs"] = not state["fs"]
        self.win.toggle_fullscreen = _tog
        r = ca.console_to_background("window-close", sleep=_no_sleep)
        self.assertEqual(self.win.calls, ["toggle_fullscreen", "hide"],
                         "a fullscreen window was ordered out without leaving fullscreen first (an empty Space "
                         "is left behind): %r" % self.win.calls)
        self.assertEqual(r["did"], ["left-fullscreen", "hidden", "no-dock-icon"], r)
        self.assertEqual(self.dock, [False], "the Dock icon stayed while the window was hidden - a dead icon")
        self.assertIs(ca._BACKGROUND["wasFullscreen"], True)
        self.win.calls[:] = []
        r = ca.console_to_front("mac-launcher", sleep=_no_sleep)
        self.assertEqual(self.win.calls, ["show", "restore", "toggle_fullscreen"],
                         "the console came back windowed although it left fullscreen: %r" % self.win.calls)
        self.assertEqual(self.dock, [False, True], "the Dock icon did not come back with the window")
        self.assertIn("fullscreen-again", r["did"], r)
        self.assertFalse(ca._BACKGROUND["on"], "the console is up but still reads as backgrounded")

    def test_windows_hides_as_is_and_comes_back_with_show_and_sw_restore(self):
        """The console shows ITSELF in-process (a cross-process ShowWindow does not reliably un-hide a WinForms
        window - v1460). pywebview's restore() forces WindowState=Normal, which leaves a fullscreen (borderless,
        maximized) form as a borderless half-window, so it is never called on Windows."""
        sys.platform = "win32"
        ca._win_is_fullscreen = lambda win, screens=None: True
        ca._win_focus_existing_console = lambda: self.win.calls.append("SW_RESTORE") or True
        saved_is_win = ca.IS_WIN
        try:
            ca.IS_WIN = True
            ca.console_to_background("window-close", sleep=_no_sleep)
            self.assertEqual(self.win.calls, ["hide"], "Windows left fullscreen to hide: %r" % self.win.calls)
            self.win.calls[:] = []
            r = ca.console_to_front("win-launcher", sleep=_no_sleep)
        finally:
            ca.IS_WIN = saved_is_win
        self.assertEqual(self.win.calls[:1], ["show"], "the console did not show itself in-process: %r" % self.win.calls)
        self.assertIn("SW_RESTORE", self.win.calls, r)
        self.assertNotIn("restore", self.win.calls,
                         "pywebview's restore() forced a fullscreen form to Normal: %r" % self.win.calls)
        self.assertNotIn("toggle_fullscreen", self.win.calls,
                         "a form that came back fullscreen was toggled OUT of it: %r" % self.win.calls)

    def test_the_mac_style_bit_beats_a_stale_flag(self):
        """MEASURED 2026-09-29 on his MacBook: fullscreen frame 1470x887 on a 1470x956 screen (frame-vs-screen
        says NO), and after the green traffic light pywebview's flag still said True for a windowed window. The
        window's own style bit was right both times, so it decides."""
        class _Inst(object):
            is_fullscreen = False                       # stale: the green button put it in fullscreen

        class _BV(object):
            instances = {7: _Inst()}

        class _Gui(object):
            BrowserView = _BV
        self.win.gui, self.win.uid = _Gui(), 7
        ca._mac_fullscreen_bit = lambda win, timeout=1.0: True
        self.assertIs(ca._win_is_fullscreen(self.win), True, "a stale flag outvoted the window's own style bit")
        ca._mac_fullscreen_bit = lambda win, timeout=1.0: None   # not a Mac / could not ask
        self.assertIs(ca._win_is_fullscreen(self.win), False, "with no style bit the flag is the next witness")
        del self.win.gui
        self.win.width, self.win.height = 1512, 982
        self.assertIs(ca._win_is_fullscreen(self.win, screens=[(1512, 982)]), True)
        self.win.width, self.win.height = 1120, 660
        self.assertIs(ca._win_is_fullscreen(self.win, screens=[(1512, 982)]), False)


class TheOsKeepsTheStateHonest(_Base):

    def test_a_minimize_is_the_background_and_a_dock_click_brings_it_back_fullscreen(self):
        ca._on_console_minimized()
        self.assertEqual(ca.window_mode_payload()["mode"], "background")
        ca._BACKGROUND["wasFullscreen"] = True
        state = {"fs": False}
        ca._win_is_fullscreen = lambda win, screens=None: state["fs"]
        saved_sleep = ca.time.sleep
        try:
            ca.time.sleep = _no_sleep
            ca._on_console_restored()
        finally:
            ca.time.sleep = saved_sleep
        self.assertEqual(ca.window_mode_payload()["mode"], "front", "a Dock / taskbar restore left it 'background'")
        self.assertIn("toggle_fullscreen", self.win.calls,
                      "a window that left fullscreen to go to the background came back windowed: %r" % self.win.calls)

    def test_the_rescue_holds_while_backgrounded(self):
        due, why = ca.ui_rescue_due(backgrounded=True)
        self.assertFalse(due, "the rescue would reload a console that is minimized on purpose")
        self.assertIn("background", why)
        src = inspect.getsource(ca._console_rescue_loop)
        self.assertIn("backgrounded=_bg_now", src, "the rescue loop no longer tells the rule it is backgrounded")

    def test_headless_and_window_only_say_so(self):
        ca._MAIN_WIN = None
        self.assertEqual(ca.window_mode_payload()["mode"], "headless")
        ca._WINDOW_ONLY = True
        self.assertEqual(ca.window_mode_payload()["mode"], "window-only")


class UpdatesAndLaunchesKeepItBackgrounded(_Base):

    def test_an_update_relaunch_while_backgrounded_opens_minimized(self):
        self.assertIsNone(ca.quiet_relaunch_reason(None, {"on": False}))
        self.assertIn("background", ca.quiet_relaunch_reason(None, {"on": True, "by": "window-close"}) or "",
                      "an update landing while the console is in the background pops it up over his game")
        self.assertEqual(ca.quiet_relaunch_reason("shadow reel", {"on": True}), "shadow reel",
                         "the backgrounded reason overwrote the shadow-reel one")
        self.assertIn("quiet_relaunch_reason(", inspect.getsource(ca._before_exec),
                      "the exec path no longer asks - every os.execv passes through _before_exec")

    def test_a_quiet_boot_is_backgrounded_from_its_first_second(self):
        saved = os.environ.get("TV_QUIET_RELAUNCH"), os.environ.get("TV_WINDOWED")
        try:
            os.environ.pop("TV_WINDOWED", None)
            os.environ["TV_QUIET_RELAUNCH"] = "the console was in the background (window-close)"
            kw = ca._control_window_kwargs("http://127.0.0.1:1/")
        finally:
            for k, v in zip(("TV_QUIET_RELAUNCH", "TV_WINDOWED"), saved):
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.assertTrue(kw.get("minimized"), kw)
        self.assertTrue(ca._BACKGROUND["on"], "a console born minimized reads as 'front'")
        self.assertIs(ca._BACKGROUND["wasFullscreen"], True,
                      "a quiet boot would come back windowed although fullscreen is his default")

    def test_a_hidden_console_relaunches_hidden_and_a_shown_one_shown(self):
        """His words: "a one time update to the newer version should keep it backgrounded"."""
        env, argv = {}, ["tv/control_app.py", "--open", "--background"]
        self.assertTrue(ca.hidden_relaunch_env({"on": True, "by": "window-close"}, env, argv))
        self.assertIn("TV_START_HIDDEN", env, "an update relaunch of a hidden console would show its window")
        env, argv = {"TV_START_HIDDEN": "stale"}, ["tv/control_app.py", "--open", "--background"]
        self.assertIsNone(ca.hidden_relaunch_env({"on": False}, env, argv))
        self.assertNotIn("TV_START_HIDDEN", env, "a window he brought forward relaunches hidden")
        self.assertNotIn("--background", argv, "--background crossed os.execv and hid a window he had brought back")
        env = {}
        ca.hidden_relaunch_env({"on": True, "by": "minimized"}, env, [])
        self.assertNotIn("TV_START_HIDDEN", env, "a window HE minimized was relaunched hidden")
        self.assertIn("hidden_relaunch_env(", inspect.getsource(ca._before_exec),
                      "the exec path no longer asks - every os.execv passes through _before_exec")

    def test_a_hidden_start_is_hidden_from_its_first_second(self):
        saved = {k: os.environ.get(k) for k in ("TV_START_HIDDEN", "TV_QUIET_RELAUNCH", "TV_WINDOWED")}
        try:
            for k in saved:
                os.environ.pop(k, None)
            os.environ["TV_START_HIDDEN"] = "the console was hidden (window-close)"
            os.environ["TV_QUIET_RELAUNCH"] = "the console was in the background (window-close)"
            kw = ca._control_window_kwargs("http://127.0.0.1:1/")
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.assertIs(kw.get("hidden"), True, "a hidden console relaunched with a window: %r" % kw)
        self.assertNotIn("minimized", kw, "hidden and minimized both asked for: %r" % kw)
        self.assertNotIn("fullscreen", kw, "a hidden start asked for fullscreen, which shows the window: %r" % kw)
        self.assertTrue(ca._BACKGROUND["on"])
        self.assertIs(ca._BACKGROUND["wasFullscreen"], True, "it would come back windowed")
        saved_argv = list(sys.argv)
        try:
            sys.argv[:] = ["tv/control_app.py", "--open", "--background"]
            self.assertIs(ca._control_window_kwargs("http://127.0.0.1:1/").get("hidden"), True,
                          "--background did not start the console hidden")
        finally:
            sys.argv[:] = saved_argv

    def test_the_window_route_takes_background_and_front(self):
        ca._win_is_fullscreen = lambda win, screens=None: False
        self.assertTrue(ca.window_action("background", by="escape-empty-stack")["ok"])
        self.assertEqual(ca._BACKGROUND["by"], "escape-empty-stack")
        self.assertFalse(ca.window_action("explode")["ok"], "a bad action name is no longer refused")

    def test_a_second_launch_asks_the_running_console_forward(self):
        sent = []

        class _R(object):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return json.dumps({"ok": True, "did": ["restored"]}).encode()

        def _open(req, timeout=None):
            sent.append(json.loads(req.data.decode()))
            return _R()
        r = ca.ask_running_console_front(17999, "second-launch", _urlopen=_open)
        self.assertTrue(r["ok"], r)
        self.assertEqual(sent, [{"do": "front", "from": "second-launch"}])

        def _boom(req, timeout=None):
            raise OSError("refused")
        self.assertFalse(ca.ask_running_console_front(17999, "x", _urlopen=_boom)["ok"],
                         "an unreachable console read as brought forward")

    def test_the_mac_launcher_brings_a_hidden_console_forward_before_it_would_kill_one(self):
        with io.open(LAUNCHER, encoding="utf-8") as fh:
            sh = fh.read()
        probe = sh.find('if [ "$_tvd_mode" = "background" ]; then')
        kill = sh.find("# soft-kill anything still listening on the control port")
        self.assertGreater(probe, -1, "the launcher no longer asks whether the console is hidden")
        self.assertLess(probe, kill, "the launcher kills :17772 BEFORE asking - a hidden console filming "
                                     "a session would be replaced")
        block = sh[probe:kill]
        self.assertIn('"do":"front"', block)
        yes = block.find('if [ "$_tvd_front" = "yes" ]; then')
        self.assertGreater(yes, -1, "the launcher no longer checks that the console ANSWERED - a hidden console that "
                                    "did not come forward would leave the Desktop icon doing nothing (v1460)")
        self.assertIn("exit 0", block[yes:yes + 400], "the launcher asks it forward and then replaces it anyway")

    def test_the_windows_launcher_asks_the_console_to_show_itself_before_focusing(self):
        with io.open(WIN_LAUNCHER, encoding="utf-8-sig") as fh:
            ps = fh.read()
        up = ps.find("if (Test-TvdControlUp) {")
        focus = ps.find("[void](Focus-TvdWindow)", up)
        self.assertGreater(up, -1)
        branch = ps[up:focus]
        self.assertIn("Invoke-RestMethod -Uri 'http://127.0.0.1:17772/api/window'", branch,
                      "the Desktop icon on Windows only focuses from outside - a WinForms window hidden by the "
                      "console does not reliably come back that way (v1460)")
        self.assertIn("front", branch)
        self.assertIn("win-launcher", branch, "the Windows launcher's front request does not name itself")
        self.assertTrue(all(ord(c) < 128 for c in branch), "non-ASCII in a file Windows PowerShell 5 reads")


RED_PROOF = [
    {
        "why": "2026-09-29 - ✕ quits by default again: every session he plays with the window shut goes unfilmed",
        "file": "tv/control_app.py",
        "find": "    return True, (\"✕ sends the console to the background - the shadow reader, triage and drain keep \"\n",
        "replace": "    return False, (\"✕ sends the console to the background - the shadow reader, triage and drain keep \"\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the close handler lets the window close after hiding it, so pywebview exits anyway",
        "file": "tv/control_app.py",
        "find": "        _request_console_exit(\"window-closing\")\n        return True\n    return False\n\n\ndef quiet_relaunch_reason(",
        "replace": "        _request_console_exit(\"window-closing\")\n        return True\n    return True\n\n\ndef quiet_relaunch_reason(",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - a real exit is not on record when the window goes, so ⏻ quit only hides the console",
        "file": "tv/control_app.py",
        "find": "    globals()[\"_EXIT_REQUESTED\"] = str(reason or \"quit\")[:60]\n",
        "replace": "    pass\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - his 'completely hidden': ✕ only minimizes, leaving the window in the Dock / taskbar",
        "file": "tv/control_app.py",
        "find": "        win.hide()\n        did.append(\"hidden\")\n",
        "replace": "        win.minimize()\n        did.append(\"hidden\")\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the Mac keeps a Dock icon for a hidden console, whose click shows nothing (a dead icon)",
        "file": "tv/control_app.py",
        "find": "        if _mac_set_dock_icon(False):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the Mac orders out a fullscreen window without leaving fullscreen (an empty Space is left)",
        "file": "tv/control_app.py",
        "find": "            win.toggle_fullscreen()\n            did.append(\"left-fullscreen\")\n",
        "replace": "            did.append(\"left-fullscreen\")\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - a stale pywebview flag outvotes the window's own fullscreen bit (measured: frame and flag both lied)",
        "file": "tv/control_app.py",
        "find": "    bit = _mac_fullscreen_bit(win)\n    if bit is not None:\n        return bit\n",
        "replace": "    bit = None\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - Windows comes back through pywebview restore(), a borderless half-window",
        "file": "tv/control_app.py",
        "find": "        else:\n            win.restore()                          # deminiaturize - harmless on a window that was not minimized\n",
        "replace": "        if True:\n            win.restore()                          # deminiaturize - harmless on a window that was not minimized\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the pixel rescue reloads a console that is hidden on purpose",
        "file": "tv/control_app.py",
        "find": "    if backgrounded:\n        return False, (\"the console is in the background by design",
        "replace": "    if False:\n        return False, (\"the console is in the background by design",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - an update landing while hidden pops the console up over his game",
        "file": "tv/control_app.py",
        "find": "    if bg.get(\"on\"):\n        return \"the console was in the background",
        "replace": "    if False:\n        return \"the console was in the background",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - a Dock / taskbar restore leaves the console windowed although it left fullscreen",
        "file": "tv/control_app.py",
        "find": "    if win is not None and was_fs:\n        try:\n            _BG_SPAWN(lambda: _refullscreen_after_restore(win, was_fs))\n",
        "replace": "    if win is not None and False:\n        try:\n            _BG_SPAWN(lambda: _refullscreen_after_restore(win, was_fs))\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - an update relaunch of a hidden console opens its window (his 'keep it backgrounded')",
        "file": "tv/control_app.py",
        "find": "        env[\"TV_START_HIDDEN\"] = \"the console was hidden (%s)\" % (bg.get(\"by\") or \"?\")\n",
        "replace": "        env[\"TV_START_HIDDEN_X\"] = \"the console was hidden (%s)\" % (bg.get(\"by\") or \"?\")\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - a hidden start still creates its window shown",
        "file": "tv/control_app.py",
        "find": "        kwargs.update(hidden=True, focus=False)\n",
        "replace": "        kwargs.update(focus=False)\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the Mac launcher replaces a hidden console (stopping its reel) instead of asking it forward",
        "file": "tv/start_tvd_mac.sh",
        "find": "  if [ \"$_tvd_mode\" = \"background\" ]; then\n",
        "replace": "  if [ \"$_tvd_mode\" = \"never\" ]; then\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the Mac launcher ends the launch whether or not the console came forward (v1460's dead icon)",
        "file": "tv/start_tvd_mac.sh",
        "find": "    if [ \"$_tvd_front\" = \"yes\" ]; then\n",
        "replace": "    if true; then\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the Windows Desktop icon only focuses from outside, which does not un-hide a WinForms window",
        "file": "tv/start_tvd_win.ps1",
        "find": "    $front = Invoke-RestMethod -Uri 'http://127.0.0.1:17772/api/window'",
        "replace": "    $front = $null # -Uri 'http://127.0.0.1:17772/api/none'",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
