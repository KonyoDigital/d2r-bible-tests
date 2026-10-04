# -*- coding: utf-8 -*-
"""⏻ Quit closes the window. The shadow reader keeps running.

The X and Esc hide the window and the lanes keep going. Quit used to take the other road: it
asked the process to exit, stopped ON AIR and armed os._exit. His words: the quit or the X does
not change the shadow reader; it stays in the background, and it stops only from its own switch.

A rolling reel keeps rolling because the service stays up. An exit that was already requested,
a window-only view and TV_CLOSE_EXITS still stop the process.
"""
import os
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import control_app as ca  # noqa: E402


class _FakeWin(object):
    def __init__(self):
        self.calls = []

    def hide(self):
        self.calls.append("hide")


class QuitLeavesTheShadowReaderRunning(unittest.TestCase):

    def setUp(self):
        keys = ("_MAIN_WIN", "_QUIT_KEEPS_SERVICE", "_EXIT_REQUESTED", "_WINDOW_LIVE",
                "_ENGINE_ALIVE", "_ENGINE_READY", "_FORCE_EXIT_ARMED", "_WINDOW_ONLY",
                "_request_console_exit", "_schedule_exit_stop", "_arm_force_exit",
                "_REOPEN_WINDOW", "_REOPEN_WHY", "_REOPEN_SHOW")
        self._had = {k: hasattr(ca, k) for k in keys}
        self._saved = {k: getattr(ca, k, None) for k in keys}
        self._bg = dict(ca._BACKGROUND)
        self.exits = []
        self.stops = []
        self.arms = []
        ca._request_console_exit = lambda reason="quit", hard_delay=None: self.exits.append(reason) or {"ok": True}
        ca._schedule_exit_stop = lambda reason="quit": self.stops.append(reason)
        ca._arm_force_exit = lambda reason="quit", delay=None: self.arms.append(reason) or True
        ca._EXIT_REQUESTED = None
        ca._QUIT_KEEPS_SERVICE = None
        ca._WINDOW_ONLY = False
        ca._FORCE_EXIT_ARMED = False
        ca._WINDOW_LIVE = True
        ca._ENGINE_ALIVE = True
        ca._ENGINE_READY = True
        ca._BACKGROUND.update(on=False, since=None, by=None, wasFullscreen=None)
        ca._REOPEN_WINDOW = None
        ca._REOPEN_WHY = None
        ca._REOPEN_SHOW = None
        ca._WIN_FS_CACHE["t"] = 0.0
        ca._WIN_FS_CACHE["v"] = None
        self.win = _FakeWin()
        ca._MAIN_WIN = self.win
        self.shadow_on = ca._shadow_state()["on"]
        self.port = ca.CONTROL_PORT
        try:
            st = os.stat(ca._shadow_path())
            self.shadow_mark = (st.st_mtime_ns, st.st_size)
        except OSError:
            self.shadow_mark = None

    def tearDown(self):
        for k, v in self._saved.items():
            if self._had[k]:
                setattr(ca, k, v)
            elif hasattr(ca, k):
                delattr(ca, k)
        ca._BACKGROUND.clear()
        ca._BACKGROUND.update(self._bg)
        ca._WIN_FS_CACHE["t"] = 0.0
        ca._WIN_FS_CACHE["v"] = None

    def _shadow_untouched(self):
        self.assertEqual(ca._shadow_state()["on"], self.shadow_on)
        self.assertEqual(ca.CONTROL_PORT, self.port)
        try:
            st = os.stat(ca._shadow_path())
            mark = (st.st_mtime_ns, st.st_size)
        except OSError:
            mark = None
        self.assertEqual(mark, self.shadow_mark, "quit wrote the shadow switch")

    def test_quit_closes_the_window_and_the_reader_stays(self):
        def destroy():
            self.win.calls.append("destroy")
            self.allowed = ca._on_console_window_closing()
            ca._on_console_window_closed()
        self.win.destroy = destroy
        r = ca._quit_window_keeps_service("api-quit:quit-button")
        self.assertTrue(r["ok"], r)
        self.assertTrue(r["windowDestroyed"], r)
        self.assertFalse(r["armed"], r)
        self.assertEqual(r["service"], "running")
        self.assertEqual(self.win.calls, ["destroy"])
        self.assertIs(self.allowed, True, "the closing handler cancelled a quit")
        self.assertEqual(self.exits, [], "quit stopped the process: %r" % self.exits)
        self.assertEqual(self.stops, [], "quit stopped ON AIR: %r" % self.stops)
        self.assertEqual(self.arms, [], "quit armed a force exit: %r" % self.arms)
        self.assertIsNone(ca._EXIT_REQUESTED)
        self.assertFalse(ca._FORCE_EXIT_ARMED)
        self.assertEqual(ca._QUIT_KEEPS_SERVICE, "api-quit:quit-button")
        self.assertIsNone(ca._MAIN_WIN)
        self.assertEqual(ca.window_mode_payload()["mode"], "background",
                         "the fleet cannot see that the service is still up")
        self._shadow_untouched()

    def test_a_destroy_that_fails_puts_the_window_back(self):
        def destroy():
            raise RuntimeError("the view would not close")
        self.win.destroy = destroy
        r = ca._quit_window_keeps_service("api-quit:quit-button")
        self.assertFalse(r["ok"], r)
        self.assertIs(ca._MAIN_WIN, self.win, "a failed destroy left the probes pointed at nothing")
        self.assertIsNone(ca._QUIT_KEEPS_SERVICE)
        self.assertTrue(ca._WINDOW_LIVE)
        self.assertTrue(ca._ENGINE_ALIVE)
        self.assertTrue(ca._ENGINE_READY)
        self.assertEqual(ca.window_mode_payload()["mode"], "front")
        self.assertEqual(self.exits, [])
        self.assertEqual(self.stops, [])
        self.assertEqual(self.arms, [])
        self._shadow_untouched()

    def test_the_closed_event_still_exits_when_nobody_asked_to_keep_the_service(self):
        ca._on_console_window_closed()
        self.assertEqual(self.exits, ["window-closed"])

    def test_a_real_exit_still_stops_when_the_flag_is_also_set(self):
        ca._QUIT_KEEPS_SERVICE = "api-quit:quit-button"
        ca._EXIT_REQUESTED = "webview-finally"
        allowed = ca._on_console_window_closing()
        self.assertIs(allowed, True)
        self.assertEqual(self.exits, ["window-closing"],
                         "an exit already requested was turned into a hide")

    def test_the_window_returning_does_not_stop_the_service_after_quit(self):
        """destroy() makes webview.start() return. That return used to call the process exit."""
        def destroy():
            self.win.calls.append("destroy")
            ca._on_console_window_closing()
            ca._on_console_window_closed()
        self.win.destroy = destroy
        r = ca._quit_window_keeps_service("api-quit:quit-button")
        self.assertTrue(r["ok"], r)
        self.assertFalse(ca._after_the_window_returns("webview-finally"),
                         "the window returning asked the process to exit")
        self.assertFalse(ca._after_the_window_returns("main-after-window"))
        self.assertEqual(self.exits, [])
        self.assertEqual(self.stops, [])
        self.assertEqual(self.arms, [])
        self.assertIsNone(ca._EXIT_REQUESTED)
        n = {"n": 0}

        def sleep(_s):
            n["n"] += 1
            if n["n"] >= 2:
                ca._EXIT_REQUESTED = "signal-SIGTERM"

        self.assertTrue(ca._park_until_a_real_exit(sleep=sleep))
        self.assertEqual(self.exits, [], "parking after quit stopped the process")
        self.assertGreaterEqual(n["n"], 2)
        self._shadow_untouched()

    def test_a_real_close_still_exits_when_the_window_returns(self):
        self.assertTrue(ca._after_the_window_returns("webview-finally"))
        self.assertEqual(self.exits, ["webview-finally"])
        self.assertFalse(ca._park_until_a_real_exit(sleep=lambda _s: self.fail("parked a real close")))

    def test_the_park_opens_one_window_when_asked_and_does_not_stop(self):
        ca._QUIT_KEEPS_SERVICE = "api-quit:quit-button"
        ca._MAIN_WIN = None
        ca._REOPEN_WINDOW = True
        opened = []

        def opener():
            opened.append(1)
            ca._MAIN_WIN = _FakeWin()

        n = {"n": 0}

        def sleep(_s):
            n["n"] += 1
            ca._EXIT_REQUESTED = "signal-SIGTERM"

        self.assertTrue(ca._park_until_a_real_exit(sleep=sleep, open_window=opener))
        self.assertEqual(opened, [1], "a second window was opened, or none was")
        self.assertIsInstance(ca._MAIN_WIN, _FakeWin)
        self.assertFalse(ca._REOPEN_WINDOW)
        self.assertFalse(ca._REOPEN_SHOW, "the reopen flag stayed set after the window call returned")
        self.assertEqual(self.exits, [])
        self.assertEqual(self.arms, [])
        self.assertEqual(ca._QUIT_KEEPS_SERVICE, "api-quit:quit-button")
        self._shadow_untouched()

    def test_a_front_request_after_quit_opens_a_window_in_this_process(self):
        def destroy():
            self.win.calls.append("destroy")
            ca._on_console_window_closing()
            ca._on_console_window_closed()
        self.win.destroy = destroy
        r = ca._quit_window_keeps_service("api-quit:quit-button")
        self.assertTrue(r["ok"], r)
        self.assertIsNone(ca._MAIN_WIN)
        new = _FakeWin()

        def opener():
            ca._MAIN_WIN = new

        def park_sleep(_s):
            time.sleep(0.01)

        t = threading.Thread(
            target=lambda: ca._park_until_a_real_exit(sleep=park_sleep, open_window=opener),
            daemon=True)
        t.start()
        got = ca.console_to_front("win-launcher", sleep=time.sleep)
        ca._EXIT_REQUESTED = "test-done"
        t.join(2)
        self.assertTrue(got["ok"], got)
        self.assertEqual(got["did"], ["opened"])
        self.assertIs(ca._MAIN_WIN, new)
        self.assertEqual(ca._QUIT_KEEPS_SERVICE, "api-quit:quit-button",
                         "opening the new window cleared the quit, so the next close stops the service")
        self.assertEqual(self.exits, [])
        self.assertEqual(self.arms, [])
        self.assertFalse(t.is_alive(), "the park thread did not notice the test was done")
        self._shadow_untouched()

    def test_a_headless_console_still_has_nothing_to_bring_forward(self):
        ca._MAIN_WIN = None
        ca._QUIT_KEEPS_SERVICE = None
        got = ca.console_to_front("mac-launcher", sleep=lambda _s: self.fail("waited for a window"))
        self.assertFalse(got["ok"])
        self.assertIn("nothing to bring forward", got["why"])
        self.assertFalse(ca._REOPEN_WINDOW)
        self.assertEqual(self.exits, [])

    def test_a_front_request_that_gets_no_window_does_not_stop_the_service(self):
        ca._QUIT_KEEPS_SERVICE = "api-quit:quit-button"
        ca._MAIN_WIN = None
        got = ca.console_to_front("win-launcher", sleep=lambda _s: None)
        self.assertFalse(got["ok"], got)
        self.assertIn("did not open", got["why"])
        self.assertEqual(self.exits, [])
        self.assertEqual(self.arms, [])
        self.assertEqual(ca._QUIT_KEEPS_SERVICE, "api-quit:quit-button")
        self._shadow_untouched()

    def test_a_reopened_window_is_shown_even_when_the_process_started_hidden(self):
        saved = list(sys.argv)
        try:
            sys.argv[:] = ["tv/control_app.py", "--open", "--background"]
            ca._REOPEN_SHOW = None
            hidden = ca._control_window_kwargs("http://127.0.0.1:1/")
            self.assertIs(hidden.get("hidden"), True, "--background no longer starts hidden")
            ca._REOPEN_SHOW = True
            kw = ca._control_window_kwargs("http://127.0.0.1:1/")
            self.assertNotIn("hidden", kw)
            self.assertIs(kw.get("focus"), True)
            self.assertIs(kw.get("fullscreen"), True)
        finally:
            sys.argv[:] = saved
            ca._REOPEN_SHOW = None

    def test_a_second_open_does_not_start_a_second_driver(self):
        hold = threading.Event()

        def target():
            hold.wait(2)

        try:
            self.assertTrue(ca._start_daemon_once("tvd-test-once"))
            threading.Thread(target=target, daemon=True, name="tvd-test-once").start()
            self.assertFalse(ca._start_daemon_once("tvd-test-once"),
                             "a second open started a second copy of a named thread")
        finally:
            hold.set()
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        i = src.find("def open_control_window(")
        blk = src[i:src.find("\ndef ", i + 1)]
        self.assertLess(blk.find("_WINDOW_ONLY"), blk.find('tvd-engine-driver'))
        self.assertIn('_start_daemon_once("tvd-engine-driver"', blk)
        self.assertIn('_start_daemon_once("tvd-kai-closer"', blk)
        arm = src.find('_console_rescue_loop, name="console-rescue"')
        start = src.find("webview.start(**_start_kw)")
        self.assertGreater(arm, 0)
        self.assertLess(arm, start)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "quit cancels the close again, so the window stays and the button does nothing",
        "file": "tv/control_app.py",
        "find": "    if globals().get(\"_QUIT_KEEPS_SERVICE\") and not globals().get(\"_EXIT_REQUESTED\"):\n"
                "        return True\n",
        "replace": "    if False:\n"
                   "        return True\n",
        "matches": 1,
    },
    {
        "why": "quit asks the process to exit again, so the shadow reader stops with the window",
        "file": "tv/control_app.py",
        "find": "    globals()[\"_QUIT_KEEPS_SERVICE\"] = who\n",
        "replace": "    globals()[\"_EXIT_REQUESTED\"] = who\n",
        "matches": 1,
    },
    {
        "why": "the window returning after quit asks the process to exit, so the shadow reader stops",
        "file": "tv/control_app.py",
        "find": "    if _quit_left_the_service_up():\n        return False\n",
        "replace": "    if False:\n        return False\n",
        "matches": 1,
    },
    {
        "why": "a front request after Quit no longer asks for a window, so the launcher replaces the process",
        "file": "tv/control_app.py",
        "find": "        win = _wait_for_a_window_after_quit(sleep)\n",
        "replace": "        win = None\n",
        "matches": 1,
    },
]
