#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#63 — A TV_STUB AGENT NEVER FILMS HIS SCREEN.

MEASURED 2026-09-28 (tv_diablo.py ~7697): under TV_STUB the live loop called the REAL capture_mac(frame)
FIRST and used capture_stub_synth only when that FAILED. On his Mac Screen Recording is granted, so a
stub agent filmed + OCR'd whatever was on his screen, and test_roundtrip_sim passed at 17:12 and failed
at 19:05 on the same commit. His words: "make sure nothing is running on my pc for nothing".

AND THE HALF THE BRIEF DID NOT NAME, MEASURED 2026-09-29 before building: test_roundtrip_sim's agent is
NOT a stub agent. Its console runs with TV_STUB=1, but /api/on spawns with sim=False and _env_clean
POPS TV_STUB — a probe read the running agent's environment: TV_STUB absent. So a guard inside the
agent alone could not have made that verdict independent of his screen. A TV_STUB console now hands
its live agent TV_CAPTURE=off (the door #236 proved never touches a window).

THE LAWS
  · DRIVEN, a real agent process: under TV_STUB, with capture_mac, every Quartz grab and the window
    picker patched to RECORD-AND-RAISE, the agent still settles and reads on synthetic frames, and none
    of them was ever called — not by the live loop, not by the film thread (handed a pinned window), not
    by the farewell look.
  · TV_STUB_REAL_CAPTURE=1 restores the old order: capture_mac is asked first (patched to fail), the
    synthetic frames still flow.
  · the console: a TV_STUB console's live agent gets TV_CAPTURE=off (unless the opt-in); on Windows a
    stub agent's capture half (capture_win.ps1) is never spawned, and its lamp reads OFF, not a death.
[[feedback-fixtures-never-touch-live-data]] [[the-unjoined-end]] [[unknown-stays-unknown]]
"""
import io
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

GRABBERS = ("capture_mac", "_quartz_grab_screen", "_quartz_grab_window", "_grab_full_screen_frame",
            "_capture_window_to_file", "find_d2r_window_mac")

# The runner is the real agent (tv_diablo.main), with every screen reader swapped for a recorder.
# `raise` mode: a call is a defect, so it is written down and then refused.
# `fail` mode (the opt-in case): capture_mac answers False, the way a failed grab does.
_RUNNER = r'''
import os, signal, sys
TV = os.environ["LAW_TV"]
sys.argv = [os.path.join(TV, "tv_diablo.py")]
sys.path.insert(0, TV)
import tv_diablo as T
SENT, MODE = os.environ["LAW_SENTINEL"], os.environ["LAW_MODE"]

def _rec(name):
    def f(*a, **k):
        with open(SENT, "a") as fh:
            fh.write(name + "\n")
        if MODE == "fail" and name == "capture_mac":
            return False
        raise RuntimeError("law: a stub agent called %s" % name)
    return f

for _n in os.environ["LAW_GRABBERS"].split(","):
    setattr(T, _n, _rec(_n))
# the film thread is handed a PINNED window, so only its own guard can keep it off the screen
T._CAP_TARGET = {"mode": "window", "label": "law: a pinned window", "wid": 1}
signal.signal(signal.SIGTERM, T._shutdown_handler)
T.main()
'''


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class _Agent(object):
    """One real agent process in a sandbox of its own; always reaped by PID."""

    def __init__(self, mode, real_capture=False):
        self.dir = tempfile.mkdtemp(prefix="tvd-stubcap-")
        self.hist = os.path.join(self.dir, "hist")
        self.frames = os.path.join(self.dir, "frames")
        os.makedirs(self.hist)
        os.makedirs(self.frames)
        self.sentinel = os.path.join(self.dir, "grabbed.txt")
        self.port = _free_port()
        runner = os.path.join(self.dir, "runner.py")
        with io.open(runner, "w", encoding="utf-8") as fh:
            fh.write(_RUNNER)
        env = dict(os.environ, TV_STUB="1", TV_PORT=str(self.port), TV_HIST=self.hist,
                   TV_FRAMES_DIR=self.frames, TV_SESSIONS=os.path.join(self.dir, "sessions.jsonl"),
                   TV_POOL="1", TV_FAREWELL="1", TV_POLL="0.25", TV_PLAY_GAP="0.8",
                   TV_CLAUDE_BIN="/bin/echo", TV_FILM="1", PYTHONUNBUFFERED="1",
                   LAW_TV=HERE, LAW_SENTINEL=self.sentinel, LAW_MODE=mode,
                   LAW_GRABBERS=",".join(GRABBERS))
        for k in ("ANTHROPIC_API_KEY", "TV_STUB_REAL_CAPTURE", "TV_CAPTURE", "TV_STUB_MANIFEST"):
            env.pop(k, None)
        if real_capture:
            env["TV_STUB_REAL_CAPTURE"] = "1"
        self.log = open(os.path.join(self.dir, "agent.log"), "wb")
        self.proc = subprocess.Popen([sys.executable, runner], env=env, cwd=self.dir,
                                     stdout=self.log, stderr=subprocess.STDOUT)

    def state(self):
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/state" % self.port, timeout=3) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception:
            return None

    def grabbed(self):
        """Every recorded call. The sentinel is only ever CREATED by a call, so absent is 'none';
        a sentinel that exists and cannot be read raises — it is never read as an empty list."""
        if not os.path.exists(self.sentinel):
            return []
        with open(self.sentinel) as fh:
            return [l.strip() for l in fh if l.strip()]

    def wait_for(self, pred, secs):
        end = time.time() + secs
        while time.time() < end:
            if self.proc.poll() is not None:
                return False
            if pred():
                return True
            time.sleep(0.25)
        return False

    def stop(self, farewell_secs=25):
        """SIGTERM first (the farewell path runs), then kill; always wait on OUR pid."""
        if self.proc.poll() is None:
            try:
                self.proc.send_signal(signal.SIGTERM)
                self.proc.wait(timeout=farewell_secs)
            except Exception:
                try:
                    self.proc.kill()
                    self.proc.wait(timeout=10)
                except Exception:
                    pass
        self.log.close()

    def tail(self):
        try:
            with open(os.path.join(self.dir, "agent.log"), "rb") as fh:
                return fh.read()[-1500:].decode("utf-8", "replace")
        except OSError as e:
            return "(the agent log could not be read: %s)" % type(e).__name__

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class AStubAgentNeverCallsAScreenReader(unittest.TestCase):

    def test_a_stub_agent_settles_and_reads_on_synthetic_frames_and_grabs_nothing(self):
        a = _Agent("raise")
        try:
            read = a.wait_for(lambda: int((a.state() or {}).get("readCount") or 0) >= 1, 90)
            st = a.state() or {}
            live_ok = a.proc.poll() is None
            a.stop()
            grabbed = a.grabbed()
            self.assertEqual(grabbed, [], "a TV_STUB agent reached for the real screen: %s\n%s"
                             % (grabbed, a.tail()))
            self.assertTrue(live_ok, "the stub agent died (a refused grab raises): %s" % a.tail())
            self.assertTrue(read, "no read in 90 s — synthetic frames never settled into a read "
                            "(readCount=%r)\n%s" % (st.get("readCount"), a.tail()))
            live = [f for f in os.listdir(a.frames) if f.startswith("live")]
            self.assertTrue(live, "no live frame was written into the sandbox: %s" % os.listdir(a.frames))
            with open(os.path.join(a.frames, live[0]), "rb") as fh:
                self.assertEqual(fh.read(2), b"BM", "the live frame is not the synthetic BMP")
        finally:
            a.stop()
            a.cleanup()

    def test_TV_STUB_REAL_CAPTURE_restores_the_old_order(self):
        """The opt-in: capture_mac is asked FIRST, and its failure still falls through to synthetic."""
        a = _Agent("fail", real_capture=True)
        try:
            asked = a.wait_for(lambda: "capture_mac" in a.grabbed(), 45)
            flowed = a.wait_for(lambda: os.path.isfile(os.path.join(a.frames, "live.jpg"))
                                or any(f.startswith("live") for f in os.listdir(a.frames)), 20)
            a.stop(farewell_secs=10)
            self.assertTrue(asked, "with TV_STUB_REAL_CAPTURE=1 capture_mac was never asked:\n%s" % a.tail())
            self.assertTrue(flowed, "the synthetic fallback no longer runs after a failed grab")
        finally:
            a.stop(farewell_secs=10)
            a.cleanup()


class AStubAgentIsDecidedByTwoVariables(unittest.TestCase):

    def test_the_predicate(self):
        import tv_diablo as T
        cases = (({"TV_STUB": "1"}, True),
                 ({"TV_STUB": "1", "TV_STUB_REAL_CAPTURE": "1"}, False),
                 ({}, False),
                 ({"TV_STUB_REAL_CAPTURE": "1"}, False))
        for env, want in cases:
            with mock.patch.dict(os.environ, env, clear=False):
                for k in ("TV_STUB", "TV_STUB_REAL_CAPTURE"):
                    if k not in env:
                        os.environ.pop(k, None)
                self.assertIs(T._stub_capture_only(), want, env)


class TheConsoleKeepsItsAgentsOffTheScreen(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import control_app as ca
        cls.ca = ca

    def _env(self, console, sim):
        with mock.patch.dict(os.environ, console, clear=False):
            for k in ("TV_STUB", "TV_STUB_REAL_CAPTURE", "TV_CAPTURE"):
                if k not in console:
                    os.environ.pop(k, None)
            return self.ca._env_clean(sim=sim)

    def test_a_stub_consoles_LIVE_agent_gets_capture_off(self):
        env = self._env({"TV_STUB": "1"}, sim=False)
        self.assertNotIn("TV_STUB", env, "premise: /api/on on a stub console spawns a non-stub agent")
        self.assertEqual(env.get("TV_CAPTURE"), "off",
                         "a TV_STUB console's live agent can read his real screen")

    def test_the_opt_in_and_his_own_console_are_untouched(self):
        env = self._env({"TV_STUB": "1", "TV_STUB_REAL_CAPTURE": "1"}, sim=False)
        self.assertNotEqual(env.get("TV_CAPTURE"), "off", "the explicit opt-in was overridden")
        env = self._env({}, sim=False)
        self.assertNotEqual(env.get("TV_CAPTURE"), "off", "HIS console's live agent lost its capture")

    def test_a_stub_agents_windows_capture_half_is_never_spawned(self):
        ca = self.ca
        spawned = []

        class _P(object):
            pid = 4242

        def _rec(*a, **k):
            spawned.append(a)
            return _P()
        with mock.patch.object(ca, "IS_WIN", True), mock.patch.object(ca.subprocess, "Popen", _rec), \
                mock.patch.object(ca, "_read_pid", lambda *a, **k: None), \
                mock.patch.object(ca, "_write_pid", lambda *a, **k: None), \
                mock.patch.dict(sys.modules, {"psutil": None}):     # never renice a real pid
            log = io.StringIO()
            self.assertIsNone(ca._start_capture({"TV_STUB": "1", "TV_CAPTURE": "auto"}, log))
            self.assertEqual(spawned, [], "capture_win.ps1 was spawned for a stub agent")
            self.assertIn("never reads the real screen", log.getvalue(), "the refusal is silent")
            # the premise: the same call with the opt-in DOES start it
            ca._start_capture({"TV_STUB": "1", "TV_CAPTURE": "auto", "TV_STUB_REAL_CAPTURE": "1"},
                              io.StringIO())
            self.assertEqual(len(spawned), 1, "premise failed: the opt-in no longer starts capture")

    def test_a_stub_agents_lamp_is_OFF_never_a_death(self):
        ca = self.ca
        starts = []
        with mock.patch.object(ca, "IS_WIN", True), mock.patch.object(ca, "_agent_mode", "sim"), \
                mock.patch.object(ca, "_capture_proc", None), \
                mock.patch.object(ca, "_read_pid", lambda *a, **k: None), \
                mock.patch.object(ca, "_start_capture", lambda env, fp: starts.append(1)), \
                mock.patch.object(ca, "_log_fp", io.StringIO()), \
                mock.patch.object(ca, "_CAP_RESTART_N", 0), mock.patch.object(ca, "_CAP_RESTART_TS", 0.0), \
                mock.patch.dict(os.environ, {"TV_CAPTURE": "auto"}):
            os.environ.pop("TV_STUB_REAL_CAPTURE", None)
            for _ in range(6):
                self.assertEqual(ca._capture_health(), "OFF")
            self.assertEqual(starts, [], "a never-started stub capture was restarted as if it had died")


RED_PROOF = [
    {
        "why": "#63 - without the synthetic branch FIRST a stub agent calls the real capture_mac and films his screen",
        "file": "tv_diablo.py",
        "find": "        if _stub_capture_only() and not WATCH_MODE:",
        "replace": "        if False:",
        "matches": 1,
    },
    {
        "why": "#63 - the predicate itself: a stub agent that is not recognised as one films his screen",
        "file": "tv_diablo.py",
        "find": "    return bool(os.environ.get(\"TV_STUB\"))\n",
        "replace": "    return False\n",
        "matches": 1,
    },
    {
        "why": "#63 - the film thread with a pinned window grabs his screen unless the stub guard stops it",
        "file": "tv_diablo.py",
        "find": "            if _stub_capture_only():\n                time.sleep(1.5)\n                continue\n",
        "replace": "            if False:\n                time.sleep(1.5)\n                continue\n",
        "matches": 1,
    },
    {
        "why": "#63 - the farewell look of a stub agent must be synthetic too, never a last grab of his screen",
        "file": "tv_diablo.py",
        "find": "            elif _stub_capture_only():\n                # #63 \u2014 a stub agent's last look",
        "replace": "            elif False:\n                # #63 \u2014 a stub agent's last look",
        "matches": 1,
    },
    {
        "why": "#63 - a TV_STUB console's live agent (TV_STUB popped) read his real screen - the roundtrip's agent",
        "file": "control_app.py",
        "find": "    if not sim and _stub_never_films(False):\n        env[\"TV_CAPTURE\"] = \"off\"\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#63 - on Windows the SCREEN is read by capture_win.ps1, which must not start for a stub agent",
        "file": "control_app.py",
        "find": "    if _stub_never_films(env=env) and not _capture_off(env):",
        "replace": "    if False:",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
