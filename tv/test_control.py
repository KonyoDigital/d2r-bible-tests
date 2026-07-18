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

    def test_session_beats_expose_capture_and_frame_lock(self):
        """v784 — every beat carries captureTs + frameId for exact SIM scrub."""
        # session n=2 = older fixture with 3 beats (2 framed, 1 empty frame)
        st, body, _ = _get(self.port, "/api/session?n=2")
        j = json.loads(body)
        beats = j["beats"]
        self.assertEqual(len(beats), 3)
        for b in beats:
            self.assertIn("captureTs", b)
            self.assertIn("frameId", b)
            self.assertIn("frameOk", b)
        self.assertEqual(beats[0]["frame"], "1_a.jpg")
        self.assertTrue(beats[0]["frameOk"])
        self.assertEqual(beats[1]["frame"], "2_a.jpg")
        self.assertEqual(beats[2]["frame"], "")              # honest: no frame archived
        self.assertFalse(beats[2]["frameOk"])

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

    def test_off_and_stop_call_stop_agent_sync(self):
        """v847 — OFF/STOP must run stop_agent (session save), not fire-and-forget only."""
        import inspect
        src = inspect.getsource(ca.Handler.do_POST)
        off = src.split('"/api/off"')[1].split('"/api/stop"')[0]
        stop = src.split('"/api/stop"')[1].split('"/api/restart"')[0]
        self.assertIn("stop_agent", off)
        self.assertIn("stop_agent", stop)
        # no async thread hide for off (must wait for session seal)
        self.assertNotIn("threading.Thread(target=stop_agent", off)
        self.assertIn("_ask_agent_shutdown", inspect.getsource(ca))

    def test_on_restart_sim_never_open_board(self):
        """v781 — primary console buttons must never spawn a second window."""
        import inspect
        src = inspect.getsource(ca.Handler.do_POST)
        for key in ('"/api/on"', '"/api/sim"', '"/api/restart"', '"/api/off"'):
            # slice until next path key
            i = src.find(key)
            self.assertGreater(i, 0, key)
            chunk = src[i:i + 400]
            self.assertNotIn("open_board(", chunk, f"{key} must not call open_board")

    def test_api_board_default_is_nav_not_spawn(self):
        """Default /api/board returns same-window nav; popout only with ?popout=1."""
        import inspect
        src = inspect.getsource(ca.Handler.do_POST)
        board = src.split('"/api/board"')[1].split('"/api/quit"')[0]
        self.assertIn("same-window nav", board)
        self.assertIn("spawned", board)
        self.assertIn("popout", board)

    def test_board_opens_once_per_session(self):
        ca._BOARD_OPENED = False
        calls = []
        orig = ca.open_board
        ca.open_board = lambda auto_on=True, tab="tvd": calls.append(1)
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

    def test_second_control_launch_does_not_open_window(self):
        """v781 — port-in-use path must exit, not open_control_window()."""
        import inspect
        src = inspect.getsource(ca.main)
        # the OSError branch should refuse a second window
        self.assertIn("not opening a second window", src)
        # ensure the old "opening another app window" path is gone
        self.assertNotIn("opening another app window", src)


class TestBoardHost(unittest.TestCase):
    """🌙 v774 — THE APP HOSTS THE BOARD: /board serves the local bible same-origin."""

    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ca.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def test_board_serves_bible(self):
        st, body, hdr = _get(self.port, "/board")
        self.assertEqual(st, 200)
        self.assertIn("text/html", hdr.get("Content-Type", ""))
        self.assertIn(b"D2R_BUILD", body)

    def test_hist_alias_traversal_blocked(self):
        try:
            st, _, _ = _get(self.port, "/tv/frames/hist/..%2Fcontrol_app.py")
        except urllib.error.HTTPError as e:
            st = e.code
        self.assertIn(st, (403, 404))

    def test_api_board_tab_whitelist(self):
        import inspect
        src = inspect.getsource(ca.Handler.do_POST)
        self.assertIn('"session", "tools", "forge", "funi", "fsets"', src)


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
        self.assertIn("/board#", src)   # v774 — board window is SAME-ORIGIN (/board), not file://
        self.assertIn("_open_browser_app_fallback(url)", src)



class TestForensicBeats(unittest.TestCase):
    """v797 — every beat carries the FULL read truth (Konyo: in-depth per-frame detail)."""

    def test_beat_payload_fields(self):
        import control_app as ca
        import inspect
        src = inspect.getsource(ca.Handler)
        for field in ("ocr_names", "confirmed_names", "ocr_seeded", "completedTs",
                      "lifecycle_tags", "conf", "model", "ocr_ms"):
            self.assertIn('"%s"' % field, src, "beat payload missing " + field)



class TestDoctor(unittest.TestCase):
    """v801 (Grok R7) — Windows self-diagnosis. /api/doctor is fast, read-only, and
    NEVER spawns the CLI; agent OFF / no D2R must never fail it (pin issues = warn)."""

    _CONTRACT = ("ok", "platform", "checks", "logTail", "logPath", "ver")
    _IDS = ("claude_cli", "claude_probe", "port_agent", "port_control", "python",
            "webview2", "capture_proc", "live_frames", "bridge", "pid_files")

    def test_doctor_route_registered(self):
        import inspect
        src = inspect.getsource(ca.Handler.do_GET)
        self.assertIn('"/api/doctor"', src)
        self.assertIn("doctor_payload()", src)

    def test_doctor_payload_contract(self):
        d = ca.doctor_payload()
        for key in self._CONTRACT:
            self.assertIn(key, d, "doctor payload missing " + key)
        self.assertIsInstance(d["checks"], list)
        self.assertTrue(d["checks"])
        ids = {c["id"] for c in d["checks"]}
        for cid in self._IDS:
            self.assertIn(cid, ids, "doctor missing check " + cid)
        for c in d["checks"]:
            self.assertIn(c["severity"], ("block", "warn"))
            self.assertIn("detail", c)
            self.assertIsInstance(c["ok"], bool)
            if "fix" in c:                       # fix only ever rides a FAILING check
                self.assertFalse(c["ok"])

    def test_doctor_ok_is_no_block_failure(self):
        d = ca.doctor_payload()
        blockers = [c for c in d["checks"] if c["severity"] == "block" and not c["ok"]]
        self.assertEqual(d["ok"], not blockers)

    def _shim_claude_on_path(self):
        """v884 — CI runners have no claude CLI; the doctor's claude_cli check is REAL and
        should stay — the TEST supplies a fake executable so it stays hermetic everywhere."""
        import tempfile, stat
        d = tempfile.mkdtemp()
        fake = os.path.join(d, "claude")
        with open(fake, "w") as f:
            f.write("#!/bin/sh\necho ok\n")
        os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
        old = os.environ.get("PATH", "")
        os.environ["PATH"] = d + os.pathsep + old
        self.addCleanup(lambda: os.environ.__setitem__("PATH", old))

    def test_doctor_ok_ignores_offline_agent(self):
        self._shim_claude_on_path()
        """Agent OFF (no bridge / no frames) must NEVER flip ok to False."""
        old = ca._agent_mode
        ca._agent_mode = "off"
        try:
            d = ca.doctor_payload()
            self.assertTrue(d["ok"], "doctor blocked with the agent merely OFF: "
                            + repr([c for c in d["checks"]
                                    if c["severity"] == "block" and not c["ok"]]))
        finally:
            ca._agent_mode = old

    def test_doctor_never_spawns_cli(self):
        import inspect
        src = inspect.getsource(ca.doctor_payload)
        self.assertIn("never spawns the CLI", src)
        self.assertIn("not probed", src)
        probe = next(c for c in ca.doctor_payload()["checks"] if c["id"] == "claude_probe")
        self.assertTrue(probe["ok"])

    def test_doctor_ver_mirrors_status(self):
        """Doctor's ver is derived from status_payload's stamp — it can never drift."""
        self.assertEqual(ca.doctor_payload()["ver"], ca._app_ver())

    def test_doctor_endpoint_live(self):
        srv = ThreadingHTTPServer(("127.0.0.1", 0), ca.Handler)
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            st, body, _ = _get(port, "/api/doctor")
            self.assertEqual(st, 200)
            j = json.loads(body)
            self.assertIn("checks", j)
            self.assertRegex(str(j["ver"]), r"^v")
        finally:
            srv.shutdown()


class TestTripleParity(unittest.TestCase):
    """v816 (Grok R8 #9) — agent VERSION == control ver == bible D2R_BUILD id. Drift = red."""

    def test_bible_matches_agent(self):
        import re
        import tv_diablo as tvmod
        bib = os.path.join(os.path.dirname(HERE), "bible.html")
        v = ""
        with open(bib, encoding="utf-8") as f:
            for line in f:
                if "window.D2R_BUILD" in line:
                    m = re.search(r"id:'(v\d+)'", line)
                    if m:
                        v = m.group(1)
                        break   # v816.1 — keep scanning past bare mentions until the stamp line
        self.assertEqual(v, tvmod.VERSION, "bible D2R_BUILD drifted from agent VERSION")



class TestSessionDelete(unittest.TestCase):
    """v834 (Konyo) — deleting a session removes ONLY that session's rows; others survive."""

    def test_delete_handler_registered(self):
        import inspect
        src = inspect.getsource(ca.Handler.do_POST)
        self.assertIn('"/api/session/delete"', src)
        self.assertIn("removedReads", src)


class TestV872StickyBridge(unittest.TestCase):
    """v877 (army suite-audit #6) — the STANDBY-flash fix must stay fixed."""

    def test_sticky_bridge_survives_one_missed_probe(self):
        import time as _t
        old_cache = dict(ca._BR_CACHE)
        old_ok = getattr(ca, "_BRIDGE_LAST_OK", 0.0)
        old_alive = ca._agent_alive
        try:
            ca._BR_CACHE.update({"ping": False, "st": None, "ts": _t.time()})   # probe just missed
            ca._BRIDGE_LAST_OK = _t.time() - 3.0                                 # but seen 3s ago
            ca._agent_alive = lambda: True                                       # and the process lives
            st = ca.status_payload()
            self.assertTrue(st.get("bridge"), "one missed probe flipped the console to STANDBY")
        finally:
            ca._BR_CACHE.update(old_cache)
            ca._BRIDGE_LAST_OK = old_ok
            ca._agent_alive = old_alive

    def test_dead_bridge_goes_dark_after_the_window(self):
        import time as _t
        old_cache = dict(ca._BR_CACHE)
        old_ok = getattr(ca, "_BRIDGE_LAST_OK", 0.0)
        old_alive = ca._agent_alive
        try:
            ca._BR_CACHE.update({"ping": False, "st": None, "ts": _t.time()})
            ca._BRIDGE_LAST_OK = _t.time() - 30.0    # silent for 30s
            ca._agent_alive = lambda: False
            st = ca.status_payload()
            self.assertFalse(st.get("bridge"), "a truly dead bridge must not stay ON")
        finally:
            ca._BR_CACHE.update(old_cache)
            ca._BRIDGE_LAST_OK = old_ok
            ca._agent_alive = old_alive


class TestV875Beacon(unittest.TestCase):
    def test_beacon_shape_and_silence_on_failure(self):
        import urllib.request as _ur
        sent = {}
        def fake_urlopen(req, timeout=None):
            sent["url"] = req.full_url
            sent["auth"] = req.get_header("Authorization") or ""
            sent["body"] = json.loads(req.data.decode())
            class R:
                def __enter__(self): return self
                def __exit__(self, *a): return False
                def read(self): return b"{}"
            return R()
        old = _ur.urlopen
        _ur.urlopen = fake_urlopen
        try:
            ca._console_beacon("boot")
            self.assertEqual(sent["url"], "https://bull-4-u.com/api/console")
            self.assertTrue(sent["auth"].startswith("Basic "))
            self.assertEqual(sent["body"]["event"], "boot")
            self.assertIn("machine", sent["body"])
            self.assertIn("ver", sent["body"])
            # failure is silent — never raises into a caller
            _ur.urlopen = lambda *a, **k: (_ for _ in ()).throw(OSError("net down"))
            ca._console_beacon("hb")   # must not raise
        finally:
            _ur.urlopen = old


if __name__ == "__main__":
    unittest.main(verbosity=1)
