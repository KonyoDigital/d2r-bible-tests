#!/usr/bin/env python3
# 🎛 TV DIABLO control app — TDD (v765 REPLAY THEATRE + button/window discipline).
# Boots the REAL Handler on an ephemeral port with a fixture journal + frame archive.
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import control_app as ca  # noqa: E402
import replay as rp  # noqa: E402


def _get(port, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=3) as r:
        return r.status, r.read(), dict(r.headers)


class TestTheatre(unittest.TestCase):
    """v765 — Konyo: 'its not really simulated anymore… its own independent VIEW, eyes on
    history' — the theatre serves REAL journaled sessions + REAL archived frames."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.hist = os.path.join(cls.tmp, "hist")
        os.makedirs(cls.hist)
        # fixture: two sessions (>10min apart), frames exist for some reads
        t0 = 1_784_000_000_000
        reads = [
            {"ts": t0, "n": 1, "scene": "gameplay", "area": "Durance of Hate Level 2",
             "names": [], "frameId": "1_a"},
            {"ts": t0 + 9_000, "n": 2, "scene": "loot", "area": "",
             "names": ["Harlequin Crest"], "frameId": "2_a"},
            {"ts": t0 + 18_000, "n": 3, "scene": "stash", "area": "",
             "names": [], "frameId": ""},                      # no frame — caption-only beat
            {"ts": t0 + 60 * 60 * 1000, "n": 1, "scene": "loot", "area": "The Secret Cow Level",
             "names": ["Vex Rune"], "frameId": "1_b"},
        ]
        cls.journal = os.path.join(cls.tmp, "sessions.jsonl")
        with open(cls.journal, "w") as f:
            for r in reads:
                f.write(json.dumps(r) + "\n")
        for fid in ("1_a", "2_a", "1_b"):
            with open(os.path.join(cls.hist, fid + ".jpg"), "wb") as f:
                f.write(b"\xff\xd8\xff\xe0FAKEJPG")
        cls._old_hist, cls._old_journal = ca.HIST_DIR, rp.JOURNAL
        cls.addClassCleanup(lambda: setattr(ca, "HIST_DIR", cls._old_hist))
        cls.addClassCleanup(lambda: setattr(rp, "JOURNAL", cls._old_journal))
        ca.HIST_DIR = cls.hist
        rp.JOURNAL = cls.journal
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ca.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_sessions_listing(self):
        st, body, _ = _get(self.port, "/api/sessions")
        self.assertEqual(st, 200)
        sess = json.loads(body)["sessions"]
        self.assertEqual(len(sess), 2)                       # 10min gap splits sessions
        self.assertEqual(sess[0]["areas"], ["The Secret Cow Level"])   # newest first
        self.assertEqual(sess[1]["reads"], 3)
        self.assertEqual(sess[1]["frames"], 2)               # only frame-backed reads counted

    def test_session_beats(self):
        st, body, _ = _get(self.port, "/api/session?n=2")
        beats = json.loads(body)["beats"]
        self.assertEqual(len(beats), 3)
        self.assertEqual(beats[1]["names"], ["Harlequin Crest"])
        self.assertEqual(beats[1]["frame"], "2_a.jpg")       # playable
        self.assertEqual(beats[2]["frame"], "")              # honest: no frame archived

    def test_hist_serving_and_traversal(self):
        st, body, hdr = _get(self.port, "/hist/1_a.jpg")
        self.assertEqual(st, 200)
        self.assertEqual(hdr.get("Content-Type"), "image/jpeg")
        self.assertTrue(body.startswith(b"\xff\xd8"))
        try:
            st2, _, _ = _get(self.port, "/hist/..%2F..%2Fcontrol_app.py")
        except urllib.error.HTTPError as e:
            st2 = e.code
        self.assertIn(st2, (403, 404))                       # traversal blocked

    def test_bad_session_number(self):
        st, body, _ = _get(self.port, "/api/session?n=99")
        self.assertEqual(st, 200)
        self.assertIn("error", json.loads(body))


class TestStopDiscipline(unittest.TestCase):
    """v765 — his repro: STOP opened+routed a window and SIM stayed on screen."""

    def test_stop_handler_never_opens_board(self):
        import inspect
        src = inspect.getsource(ca.Handler.do_POST)
        stop_block = src.split('"/api/stop"')[1].split('"/api/restart"')[0]
        self.assertNotIn("open_board", stop_block)

    def test_board_opens_once_per_session(self):
        ca._BOARD_OPENED = False
        calls = []
        orig = ca.open_board
        ca.open_board = lambda auto_on=True: calls.append(1)
        try:
            self.assertEqual(ca._open_board_once(), "opened")
            self.assertEqual(ca._open_board_once(), "already-open (auto-sync)")
            self.assertEqual(len(calls), 1)
        finally:
            ca.open_board = orig
            ca._BOARD_OPENED = False

    def test_mac_open_board_prefers_direct_browser(self):
        import inspect
        src = inspect.getsource(ca.open_board)
        self.assertIn("_MAC_BROWSERS", src)                  # fragment-surviving spawn path


class TestVersionTruth(unittest.TestCase):
    """v771 (Grok R5) — ONE ship tag: agent VERSION == control payload ver. Drift = red."""
    def test_stamps_match(self):
        import re
        import tv_diablo as tvmod
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as f:
            src = f.read()
        m = re.search(r'"ver": "(v\d+)"', src)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), tvmod.VERSION)

    def test_board_window_fallback_defines_url(self):
        """Regression: board_window except used undefined `url` → NameError on crash path."""
        import inspect
        src = inspect.getsource(ca.board_window)
        self.assertIn("url = _file_url", src)
        self.assertIn("_open_browser_app_fallback(url)", src)


if __name__ == "__main__":
    unittest.main(verbosity=1)
