# -*- coding: utf-8 -*-
"""REG-1957 - A PROOF THAT ONLY LACKS MEMORY FREES THE VIEW OF AN IDLE PC, AND NEVER ONE HE IS USING.

His ALT (7.9 GB), 2026-10-07 09:2x over SSH: 653 MB free with nothing playing - the console window up (WebView2 ~2 GB
over 18 processes, the console ~1.6 GB). A proof needs ~1.1 GB on top of a 700 MB floor (REG-1715) and starts at
1536 MB, so the ALT never proved itself: census stale -> frame.release LOCKED -> 446 reels piled up (#221). His word
on the open question: "no RAM ruling - make it and fix it". The console now frees ITS OWN VIEW - exactly what the
Quit button already does (_quit_window_keeps_service: every lane keeps running, the Desktop icon brings the window
back) - only when memory is the one thing refusing the proof, he is measured NOT playing, and either the window was
already sent away or nobody has touched the PC for 30 minutes. An idle time that cannot be read frees nothing.

Fixtures only: every window, idle, playing and quit hook is stubbed; nothing closes a real window.
"""
import io
import os
import sys
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as CA  # noqa: E402

LOW = {"key": "low-memory", "why": "only 653 MB of memory free - a proof starts at 1536 MB"}
IDLE = CA.VIEW_RELEASE_IDLE_S


class TheRule(unittest.TestCase):

    def test_an_idle_pc_whose_proof_lacks_only_memory_frees_its_view(self):
        ok, why = CA.view_release_for_proof("low-memory", False, "fullscreen", IDLE + 60)
        self.assertTrue(ok, why)
        self.assertIn("Desktop icon brings the window back", why)

    def test_a_pc_he_is_using_keeps_its_window(self):
        for idle in (0, 300, IDLE - 1):
            with self.subTest(idle=idle):
                self.assertFalse(CA.view_release_for_proof("low-memory", False, "front", idle)[0],
                                 "the window was taken from a PC used %d s ago (REG-1957)" % idle)

    def test_playing_or_unknown_playing_never_frees(self):
        self.assertFalse(CA.view_release_for_proof("low-memory", True, "fullscreen", IDLE * 4)[0])
        self.assertFalse(CA.view_release_for_proof("low-memory", None, "fullscreen", IDLE * 4)[0])

    def test_only_a_memory_refusal_frees(self):
        for key in ("start", "playing", "busy", "backoff", "mem-unknown", None):
            with self.subTest(key=key):
                self.assertFalse(CA.view_release_for_proof(key, False, "fullscreen", IDLE * 4)[0])

    def test_an_unreadable_idle_time_frees_nothing(self):
        for idle in (None, "x", -5, float("nan")):
            with self.subTest(idle=idle):
                self.assertFalse(CA.view_release_for_proof("low-memory", False, "front", idle)[0])

    def test_a_hidden_window_is_freed_and_no_view_is_left_alone(self):
        self.assertTrue(CA.view_release_for_proof("low-memory", False, "background", 0)[0],
                        "a window he already sent away still holds its view and memory")
        for mode in ("headless", "window-only", None):
            with self.subTest(mode=mode):
                self.assertFalse(CA.view_release_for_proof("low-memory", False, mode, IDLE * 4)[0])


class TheTickActs(unittest.TestCase):

    def run_tick(self, r, mode="fullscreen", playing=False, idle=IDLE + 60):
        calls = []
        with mock.patch.object(CA, "window_mode_payload", lambda: {"mode": mode}), \
             mock.patch.object(CA, "_sp_playing_here", lambda: playing), \
             mock.patch.object(CA, "_os_input_idle_s", lambda: idle), \
             mock.patch.object(CA, "_quit_window_keeps_service",
                               lambda reason="": calls.append(reason) or {"windowDestroyed": True}):
            out = CA._self_prove_free_view(dict(r))
        return out, calls

    def test_a_memory_refused_tick_on_an_idle_pc_frees_the_view_once(self):
        out, calls = self.run_tick(LOW)
        self.assertEqual(len(calls), 1, "the owed proof's memory was never freed (REG-1957)")
        self.assertIs(out.get("viewFreed"), True)
        self.assertIn("nobody has touched this PC", out.get("say") or "")

    def test_a_busy_user_a_game_or_another_refusal_frees_nothing(self):
        for kw in ({"idle": 120}, {"playing": True}, {"playing": None}, {"mode": "headless"}, {"idle": None}):
            with self.subTest(**{k: str(v) for k, v in kw.items()}):
                out, calls = self.run_tick(LOW, **kw)
                self.assertEqual(calls, [], "the view was freed when it must not be: %s" % kw)
                self.assertTrue(out.get("viewRelease"), "the tick does not say why the window stays")
        out, calls = self.run_tick({"key": "start"})
        self.assertEqual(calls, [])

    def test_the_prover_tick_asks(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        i = src.find("def _self_prove_tick():")
        body = src[i:src.find("\ndef ", i + 10)]
        self.assertIn("r = _self_prove_free_view(r)", body, "the console's prover tick never asks to free memory")

    def test_the_idle_reader_answers_a_number_or_unknown(self):
        v = CA._os_input_idle_s()
        self.assertTrue(v is None or (isinstance(v, float) and v >= 0), v)


RED_PROOF = [
    {
        "why": "REG-1957 - the idle bar is gone: the console frees the window of a PC he is using",
        "file": "tv/control_app.py",
        "find": "    if idle < bar:\n        return False, \"this PC was used %d min ago, so the window stays\" % int(idle // 60)\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1957 - a game on the PC no longer keeps its window",
        "file": "tv/control_app.py",
        "find": "    if playing is not False:\n        return False, (\"he is playing here\" if playing else \"whether he is playing could not be asked\")\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1957 - the prover tick stops asking: the ALT never frees memory for its owed proof",
        "file": "tv/control_app.py",
        "find": "        r = _self_prove_free_view(r)     # REG-1957",
        "replace": "        pass     # REG-1957",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
