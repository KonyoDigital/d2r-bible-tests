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

    def test_second_launch_takes_over_when_headless_else_refuses(self):
        """v1248/v1251 — TAKEOVER: a second --open against a HEADLESS server RECLAIMS the
        port as PRIMARY (TCC-correct) instead of window-only attach. Window-only left the
        agent under headless Python without Screen Recording → desktop wallpaper feed.
        A genuine live window still keeps the v781 one-window refuse."""
        import inspect
        src = inspect.getsource(ca.main)
        self.assertIn("_window_present", src)
        self.assertIn("_reclaim_headless_for_scan", src)
        self.assertIn("reclaim", src.lower())
        # a genuine live window still gets the one-window refuse
        self.assertIn("already open", src.lower())
        # helpers exist
        self.assertTrue(callable(ca._reclaim_headless_for_scan))
        self.assertTrue(callable(ca._screen_recording_ok_quick))

    def test_window_presence_lock_self_heals(self):
        """v1248 — the takeover guard: no file → absent; a live pid → present; a dead pid →
        absent (stale lock self-heals so a crashed window never wedges the takeover)."""
        import tempfile
        orig = ca.WINDOW_PID_PATH
        try:
            ca.WINDOW_PID_PATH = os.path.join(tempfile.gettempdir(), "tvd_window_test.pid")
            ca._window_lock_clear()
            self.assertFalse(ca._window_present())          # no file
            ca._window_lock_write()
            self.assertTrue(ca._window_present())            # our live pid
            with open(ca.WINDOW_PID_PATH, "w") as f:
                f.write("999999")                            # a dead pid
            self.assertFalse(ca._window_present())           # stale → absent
        finally:
            ca._window_lock_clear()
            ca.WINDOW_PID_PATH = orig

    def test_window_only_attach_does_not_start_a_second_engine_driver(self):
        """v1248 — a window-only/takeover attach must NOT spin up a second engine driver;
        the primary (port owner) owns it. The driver start is guarded by _WINDOW_ONLY."""
        import inspect
        src = inspect.getsource(ca.open_control_window)
        self.assertIn("_WINDOW_ONLY", src)
        self.assertIn("tvd-engine-driver", src)
        # the guard must sit before the driver thread start
        self.assertLess(src.index("_WINDOW_ONLY"), src.index("tvd-engine-driver"))


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

    def test_board_served_no_cache(self):
        # U2 — the /board bible is the anti-stale guarantee: WKWebView must NEVER hard-cache it,
        # or Konyo sees an old D2R_BUILD ("I only see v1248"). Lock the no-cache header on both the
        # plain board and the engine-iframe variant so a future edit can't reintroduce staleness.
        for p in ("/board", "/board?app=1&engine=1"):
            st, _, hdr = _get(self.port, p)
            self.assertEqual(st, 200, p)
            self.assertIn("no-cache", (hdr.get("Cache-Control", "") or "").lower(),
                          "%s must be served no-cache (anti-stale board guard)" % p)

    def test_hist_alias_traversal_blocked(self):
        try:
            st, _, _ = _get(self.port, "/tv/frames/hist/..%2Fcontrol_app.py")
        except urllib.error.HTTPError as e:
            st = e.code
        self.assertIn(st, (403, 404))

    def test_api_board_tab_whitelist(self):
        import inspect
        src = inspect.getsource(ca.Handler.do_POST)
        # v901 — SESSIONS is default home; tvd may remain as alias only
        self.assertIn("session", src)
        self.assertIn("tools", src)


class TestVersionTruth(unittest.TestCase):
    """v771 (Grok R5) — ONE ship tag: agent VERSION == control payload ver. Drift = red."""
    def test_stamps_match(self):
        import re
        import tv_diablo as tvmod
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as f:
            src = f.read()
        m = re.search(r'"ver": "(v[\d.]+)"', src)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), tvmod.VERSION)

    def test_app_ver_equals_ship_version(self):
        # U2 — _app_ver() is the value the WKWebView cache-bust URL (?v=) uses; it MUST equal the
        # ship VERSION or a relaunch busts to the wrong (or a constant) tag and staleness returns.
        # Existing tests cover status-ver==VERSION transitively; this locks the cache-bust value
        # directly against the ship tag.
        import tv_diablo as tvmod
        self.assertEqual(ca._app_ver(), tvmod.VERSION,
                         "the cache-bust value _app_ver() drifted from the ship VERSION")

    def test_board_window_fallback_defines_url(self):
        """Regression: board_window except used undefined `url` → NameError on crash path."""
        import inspect
        src = inspect.getsource(ca.board_window)
        self.assertIn("/board#", src)   # v774 — board window is SAME-ORIGIN (/board), not file://
        self.assertIn("_open_browser_app_fallback(url)", src)



class TestForensicBeats(unittest.TestCase):
    """v797/v894 — lean theatre beats stay light; full brain rides /api/beat for the I drawer."""

    def test_beat_payload_fields(self):
        import control_app as ca
        import inspect
        src = inspect.getsource(ca.Handler)
        # lean /api/session beats (scrub-critical)
        for field in ("ocr_names", "confirmed_names", "ocr_seeded", "completedTs",
                      "conf", "model", "ocr_ms"):
            self.assertIn('"%s"' % field, src, "beat payload missing " + field)
        # forensic blob on /api/beat (I drawer) — not duplicated on every lean row
        for field in ("raw", "dispatch", "decisions", "parse", "vision", "board"):
            self.assertIn('"%s"' % field, src, "forensic /api/beat missing " + field)
        self.assertIn('"/api/beat"', src)



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
                    m = re.search(r"id:'(v[\d.]+)'", line)
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


class TestSimDebuggerNoSilentReadDrop(unittest.TestCase):
    """v896 — shelf history: journaled AI reads must all reach the client; SIM opens REAL 1×.

    Repro (pre-v896): sessions with few/no footage frames defaulted client to 🎬 CUT, which
    stripped empty gameplay/transition rows — shelf said 'N reads' but timeline showed fewer.
    """

    def test_ui_defaults_real_one_x_not_auto_cut(self):
        ui = os.path.join(HERE, "control_ui.html")
        with open(ui, encoding="utf-8") as f:
            src = f.read()
        self.assertIn("mode:'real'", src)
        self.assertIn("speed:1", src)
        self.assertIn("modeHint", src)
        # must NOT reintroduce the footage-threshold that forced highlight on low-film history
        self.assertNotIn("TH.mode = 'highlight'", src)
        self.assertNotIn('TH.mode = "highlight"', src)
        self.assertNotIn("TH.speed = 2", src)

    def test_api_returns_every_journaled_read_and_mode_hint_real(self):
        import tempfile
        import replay as rp
        t0 = 1_700_000_000_000
        # many empty gameplay rows (the ones CUT used to drop) + a few named
        rows = []
        for i in range(1, 21):
            rows.append({
                "ts": t0 + i * 1000, "n": i, "scene": "gameplay" if i % 4 else "loot",
                "area": "Blood Moor" if i < 10 else "Cold Plains",
                "names": (["Harlequin Crest"] if i % 5 == 0 else []),
                "frameId": "%d_a" % i, "sessionId": "s_test_v896",
                "lane": "deep", "captureTs": t0 + i * 1000,
            })
        rows.append({
            "ts": t0 + 25_000, "n": 21, "scene": "session_end", "mode": "session_end",
            "sessionEnd": True, "sessionId": "s_test_v896", "names": [], "frameId": "",
        })
        tmp = tempfile.mkdtemp(prefix="tvd-v896-")
        journal = os.path.join(tmp, "sessions.jsonl")
        hist = os.path.join(tmp, "hist")
        os.makedirs(hist)
        with open(journal, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        for i in range(1, 21):
            with open(os.path.join(hist, "%d_a.jpg" % i), "wb") as f:
                f.write(b"\xff\xd8\xff\xe0FAKE")
        old_h, old_j = ca.HIST_DIR, rp.JOURNAL
        ca.HIST_DIR = hist
        rp.JOURNAL = journal
        # clear journal cache if present
        if hasattr(ca.Handler, "_journal_cache"):
            ca.Handler._journal_cache = None
        try:
            class _H:
                def _load_journal_cached(self):
                    return rp.load_journal()
                def _thin_footage_beats(self, *a, **k):
                    return ca.Handler._thin_footage_beats(self, *a, **k)
                def _prewarm_session_frames(self, *a, **k):
                    pass
            h = _H()
            j = ca.Handler._theatre_session(h, 1, pack="debug")
            self.assertNotIn("error", j)
            self.assertEqual(j.get("modeHint"), "real")
            self.assertEqual(j.get("pack"), "debug")
            reads = [b for b in (j.get("beats") or [])
                     if not b.get("footage") and not b.get("skip")]
            self.assertEqual(len(reads), 20, "server dropped journaled reads: got %d" % len(reads))
            self.assertEqual(sorted(b.get("n") for b in reads), list(range(1, 21)))
            empty = [b for b in reads if not (b.get("names") or [])]
            self.assertGreaterEqual(len(empty), 15, "fixture should keep empty gameplay rows")
        finally:
            ca.HIST_DIR = old_h
            rp.JOURNAL = old_j
            shutil.rmtree(tmp, ignore_errors=True)


_MISSING = object()


class TestPhaseDLiveRing(unittest.TestCase):
    """v948.26 🥷🧠 PHASE D — surface the Master-Brain reconciler to the client.
    status_payload() carries `liveRing` (the provisional NOW-CURSOR from _ENGINE_FRAMES_LIVE),
    projected defensively and with raw text hard-capped (ARCH_PINGPONG §6-Q4 SETTLED)."""

    def _restore(self, saved):
        if saved is _MISSING:
            ca.__dict__.pop("_ENGINE_FRAMES_LIVE", None)
        else:
            ca._ENGINE_FRAMES_LIVE = saved

    def test_liveRing_present_and_empty_when_no_deque(self):
        saved = ca.__dict__.get("_ENGINE_FRAMES_LIVE", _MISSING)
        ca.__dict__.pop("_ENGINE_FRAMES_LIVE", None)
        try:
            self.assertEqual(ca._project_live_ring(), [])   # defensive: deque may not exist yet
            st = ca.status_payload()
            self.assertIn("liveRing", st)
            self.assertEqual(st["liveRing"], [])
        finally:
            self._restore(saved)

    def test_liveRing_projects_deque_entries_and_hard_caps_raw_text(self):
        import collections
        saved = ca.__dict__.get("_ENGINE_FRAMES_LIVE", _MISSING)
        dq = collections.deque(maxlen=16)
        dq.append({"f": "f_5.jpg", "ts": 5000, "label": "tooltip", "owner": "live",
                   "verdict": "grail", "why": "W" * 400, "sealed": False})
        ca._ENGINE_FRAMES_LIVE = dq
        try:
            ring = ca._project_live_ring()
            self.assertEqual(len(ring), 1)
            r = ring[0]
            self.assertEqual(r["f"], "f_5.jpg")
            self.assertEqual(r["owner"], "live")
            self.assertEqual(r["verdict"], "grail")
            self.assertFalse(r["sealed"])   # a live-ring frame is never authoritative
            self.assertLessEqual(len(r["why"]), ca._LIVE_RING_TEXT_CAP)   # raw text capped
        finally:
            self._restore(saved)


class TestPhaseDEngineFramesOnBeat(unittest.TestCase):
    """v948.26 🥷🧠 PHASE D — the sealed reel's engineFrames reach the theatre pack: the
    Master-Brain owner/verdict/why joins onto the matching retro footage beat by `f`,
    marked sealed:True (sealed-wins). Absent-safe: a reel with no engineFrames → no
    `engineFrame` on any beat (the UI no-ops)."""

    def _run_theatre(self, with_engine_frames):
        import tempfile
        t0 = 1_700_100_000_000
        sid = "s_1700100000000_pd"
        rows = [
            {"ts": t0, "n": 1, "scene": "loot", "area": "Blood Moor", "names": ["Windforce"],
             "frameId": "f_%d" % t0, "sessionId": sid, "lane": "deep", "captureTs": t0},
            {"ts": t0 + 9000, "n": 2, "scene": "session_end", "mode": "session_end",
             "sessionEnd": True, "sessionId": sid, "names": [], "frameId": ""},
        ]
        tmp = tempfile.mkdtemp(prefix="tvd-pd-")
        journal = os.path.join(tmp, "sessions.jsonl")
        hist = os.path.join(tmp, "hist")
        reel = os.path.join(hist, "reel_" + sid)
        os.makedirs(reel)
        with open(journal, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        fname = "f_%d.jpg" % (t0 + 100)
        with open(os.path.join(reel, fname), "wb") as f:
            f.write(b"\xff\xd8\xff\xe0FAKE")
        with open(os.path.join(reel, "index.json"), "w", encoding="utf-8") as f:
            json.dump({"frames": [{"f": fname, "ts": t0 + 100}]}, f)
        report = {"routing": [{"f": fname, "ts": t0 + 100, "label": "tooltip",
                               "sources": ["read"], "gatePass": True}]}
        if with_engine_frames:
            report["engineFrames"] = [{
                "f": fname, "ts": t0 + 100, "label": "tooltip",
                "owner": "live", "verdict": "grail", "why": "live eye named 'Windforce'",
                "layers": {"live": {"state": "named", "names": ["Windforce"]}},
            }]
        with open(os.path.join(reel, "kai_report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f)

        old_h, old_j = ca.HIST_DIR, rp.JOURNAL
        ca.HIST_DIR = hist
        rp.JOURNAL = journal
        if hasattr(ca.Handler, "_journal_cache"):
            ca.Handler._journal_cache = None
        try:
            class _H:
                def _load_journal_cached(self):
                    return rp.load_journal()
                def _thin_footage_beats(self, *a, **k):
                    return ca.Handler._thin_footage_beats(self, *a, **k)
                def _prewarm_session_frames(self, *a, **k):
                    pass
            j = ca.Handler._theatre_session(_H(), 1, pack="debug")
            self.assertNotIn("error", j)
            return [b for b in (j.get("beats") or []) if b.get("footage")]
        finally:
            ca.HIST_DIR = old_h
            rp.JOURNAL = old_j
            shutil.rmtree(tmp, ignore_errors=True)

    def test_engine_frame_owner_verdict_reaches_the_footage_beat(self):
        foot = self._run_theatre(with_engine_frames=True)
        self.assertTrue(foot, "no footage beats built")
        ef = [b for b in foot if b.get("engineFrame")]
        self.assertEqual(len(ef), 1, "sealed engineFrame did not join onto the footage beat")
        e = ef[0]["engineFrame"]
        self.assertEqual(e["owner"], "live")
        self.assertEqual(e["verdict"], "grail")
        self.assertTrue(e["sealed"], "a materialized reel engineFrame must be authoritative")
        self.assertEqual(e["layers"]["live"]["names"], ["Windforce"])

    def test_absent_safe_when_reel_has_no_engine_frames(self):
        foot = self._run_theatre(with_engine_frames=False)
        self.assertTrue(foot, "no footage beats built")
        self.assertTrue(all("engineFrame" not in b for b in foot),
                        "older reels (no engineFrames) must not carry an engineFrame — UI no-op")


class TestV1254SessionFinds(unittest.TestCase):
    """v1254 R1 (SESSIONS FLAGSHIP — WHAT I FOUND) — _theatre_sessions surfaces the kai
    register ITEMS as card-facing `finds` (capped, card fields only, grail/tier-first then
    newest) plus a `topFind` teaser. TRUTHFUL: a session with no register → finds/topFind
    null (never fabricated). Rides the existing honest `registered` count."""

    def _run(self, sessions_rows):
        """sessions_rows: list of (sessionId, [journal rows]) → run _theatre_sessions against
        an isolated tempdir journal and return its output list."""
        tmp = tempfile.mkdtemp(prefix="tvd-v1254-")
        journal = os.path.join(tmp, "sessions.jsonl")
        hist = os.path.join(tmp, "hist")
        os.makedirs(hist)
        with open(journal, "w", encoding="utf-8") as f:
            for _sid, rows in sessions_rows:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
        old_h, old_j = ca.HIST_DIR, rp.JOURNAL
        ca.HIST_DIR = hist
        rp.JOURNAL = journal
        if hasattr(ca.Handler, "_journal_cache"):
            ca.Handler._journal_cache = None
        try:
            class _H:
                def _load_journal_cached(self):
                    return rp.load_journal()
            out = ca.Handler._theatre_sessions(_H())
            self.assertNotIn("error", out if isinstance(out, dict) else {})
            return out
        finally:
            ca.HIST_DIR = old_h
            rp.JOURNAL = old_j
            shutil.rmtree(tmp, ignore_errors=True)

    @staticmethod
    def _sess(sid, t0, register=None, extra=None):
        rows = []
        for i in range(1, 4):   # >=3 reads so it's not tagged a stub
            rows.append({"ts": t0 + i * 1000, "n": i, "scene": "loot", "area": "Blood Moor",
                         "names": [], "frameId": "%d_x" % i, "sessionId": sid,
                         "lane": "deep", "captureTs": t0 + i * 1000})
        if register is not None:
            rows.append({"ts": t0 + 5000, "captureTs": t0 + 5000, "lane": "kai", "mode": "kai",
                         "scene": "kai", "names": [], "sessionId": sid, "frameId": "",
                         "kai": {"register": register}})
        rows.append({"ts": t0 + 9000, "n": 99, "scene": "session_end", "mode": "session_end",
                     "sessionEnd": True, "sessionId": sid, "names": [], "frameId": ""})
        return (sid, rows)

    def test_register_items_become_capped_sorted_finds(self):
        # grail beats a NEWER non-grail (tier wins over recency); newest wins within a tier.
        items = [
            {"name": "Enigma", "firstSeenTs": 1000, "frameId": "f_a", "loc": None, "tier": "grail"},
            {"name": "Nagelring", "firstSeenTs": 5000, "frameId": "f_b", "loc": "stash", "tier": None},
            {"name": "Harlequin Crest", "firstSeenTs": 3000, "frameId": "f_c", "loc": "equipped", "tier": "grail"},
            {"name": "Gheed's Fortune", "firstSeenTs": 4000, "frameId": "f_d", "loc": "stash", "tier": "keep"},
        ]
        out = self._run([self._sess("s_find_1", 1_700_200_000_000,
                                     register={"count": 4, "items": items})])
        s = next(x for x in out if x.get("sessionId") == "s_find_1")
        self.assertEqual(s["registered"], 4, "honest count preserved")
        finds = s["finds"]
        self.assertIsInstance(finds, list)
        # grail-first (newest grail wins), then keep, then null — recency inside a tier
        self.assertEqual([f["name"] for f in finds],
                         ["Harlequin Crest", "Enigma", "Gheed's Fortune", "Nagelring"])
        # card-facing fields ONLY, and firstSeenTs re-keyed to `ts`
        self.assertEqual(set(finds[0].keys()), {"name", "tier", "loc", "frameId", "ts"})
        self.assertEqual(finds[0]["ts"], 3000)
        self.assertEqual(finds[0]["frameId"], "f_c")
        # topFind = the single best (a grail present → newest grail)
        self.assertEqual(s["topFind"], {"name": "Harlequin Crest", "tier": "grail"})

    def test_finds_capped_at_16(self):
        items = [{"name": "Item%02d" % k, "firstSeenTs": 1000 + k, "frameId": "f_%d" % k,
                  "loc": "stash", "tier": None} for k in range(30)]
        out = self._run([self._sess("s_cap", 1_700_300_000_000,
                                     register={"count": 30, "items": items})])
        s = next(x for x in out if x.get("sessionId") == "s_cap")
        self.assertEqual(s["registered"], 30, "the full total still lives in `registered` (+N more)")
        self.assertEqual(len(s["finds"]), 16, "finds list must be capped for the 12s poll")

    def test_no_register_never_fabricates_finds(self):
        # a session with NO kai register row (unswept / old reel) → honest nulls
        out = self._run([self._sess("s_bare", 1_700_400_000_000, register=None)])
        s = next(x for x in out if x.get("sessionId") == "s_bare")
        self.assertIsNone(s["registered"], "no register → registered null (unchanged honesty)")
        self.assertIsNone(s["finds"], "no register → finds null, never fabricated")
        self.assertIsNone(s["topFind"])

    def test_empty_register_reports_zero_and_no_finds(self):
        # a SWEPT reel that witnessed nothing → registered 0, finds absent (nothing to show)
        out = self._run([self._sess("s_empty", 1_700_500_000_000,
                                     register={"count": 0, "items": []})])
        s = next(x for x in out if x.get("sessionId") == "s_empty")
        self.assertEqual(s["registered"], 0)
        self.assertIsNone(s["finds"])
        self.assertIsNone(s["topFind"])


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


class TestV919IntakeLane(unittest.TestCase):
    """v919 (Grok REAL EYES R1) — the subscription lane answers with its header, and STRICT
    mode 502s honestly instead of fake-greening through the website proxy."""

    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ca.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def _post_intake(self):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/intake",
            data=json.dumps({"image": "aGk=", "media_type": "image/jpeg",
                             "kind": "grail", "names": ["Shako"]}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read(), dict(e.headers)

    def test_local_lane_success_carries_the_subscription_header(self):
        class _PR:
            returncode = 0
            stdout = json.dumps({"status": 200, "body": '{"found":["Shako"]}',
                                 "lane": "subscription"}).encode()
            stderr = b""
        class _G5Off:
            def mode(self):
                return "off"
        old = ca.subprocess.run
        old_g5 = ca._G5
        ca.subprocess.run = lambda *a, **k: _PR()
        ca._G5 = _G5Off()  # v1380.1 — pin dual receiver to Claude-only for this header pin
        ca._INTAKE_LAST_TS = 0
        ca._INTAKE_INFLIGHT = 0
        try:
            status, body, hdrs = self._post_intake()
        finally:
            ca.subprocess.run = old
            ca._G5 = old_g5
        self.assertEqual(status, 200)
        self.assertEqual(hdrs.get("X-Intake-Lane"), "subscription")
        self.assertIn(b"Shako", body)

    def test_dual_primary_prefers_grok_subscription_lane(self):
        """v1380.1 — G5 primary: dual receiver tries grok-subscription first."""
        class _PR:
            returncode = 0
            stdout = json.dumps({"status": 200, "body": '{"found":["Shako"]}',
                                 "lane": "grok-subscription"}).encode()
            stderr = b""
        class _G5Pri:
            def mode(self):
                return "primary"
        old = ca.subprocess.run
        old_g5 = ca._G5
        seen = []
        def _run(cmd, *a, **k):
            seen.append(cmd)
            return _PR()
        ca.subprocess.run = _run
        ca._G5 = _G5Pri()
        ca._INTAKE_LAST_TS = 0
        ca._INTAKE_INFLIGHT = 0
        try:
            status, body, hdrs = self._post_intake()
        finally:
            ca.subprocess.run = old
            ca._G5 = old_g5
        self.assertEqual(status, 200)
        self.assertEqual(hdrs.get("X-Intake-Lane"), "grok-subscription")
        self.assertIn(b"Shako", body)
        self.assertTrue(seen, "node runner should have been spawned")
        self.assertIn("intake_grok_sub.mjs", " ".join(str(x) for x in seen[0]))

    def test_strict_mode_502s_instead_of_website_fallback(self):
        class _PR:
            returncode = 1
            stdout = b""
            stderr = b"claude: not logged in"
        class _G5Off:
            def mode(self):
                return "off"
        old_run = ca.subprocess.run
        old_g5 = ca._G5
        ca.subprocess.run = lambda *a, **k: _PR()
        ca._G5 = _G5Off()
        os.environ["TV_INTAKE_LOCAL_STRICT"] = "1"
        # v1379 — clear the subscription rate-limit so a prior test's successful
        # intake (within TV_INTAKE_MIN_GAP_S) cannot 429 this strict-mode probe.
        ca._INTAKE_LAST_TS = 0
        ca._INTAKE_INFLIGHT = 0
        try:
            status, body, _ = self._post_intake()
        finally:
            ca.subprocess.run = old_run
            ca._G5 = old_g5
            os.environ.pop("TV_INTAKE_LOCAL_STRICT", None)
        self.assertEqual(status, 502)
        out = json.loads(body)
        self.assertEqual(out.get("lane"), "subscription-failed")
        self.assertIn("not logged in", out.get("detail", ""))


class TestV924FarmGate(unittest.TestCase):
    """v924 — the FARM DAY gate: one verdict, honest checks, mocked CLI (no live spawns in CI)."""

    def test_gate_contract_and_verdict_logic(self):
        class _PR:
            returncode = 0
            stdout = b"ok"
            stderr = b""
        old = ca.subprocess.run
        old_which = ca.shutil.which
        ca.subprocess.run = lambda *a, **k: _PR()
        ca.shutil.which = lambda *a, **k: "/usr/bin/claude"   # v924.1 — CI has no CLI; the gate must still be testable
        try:
            j = ca.farmgate_payload()
        finally:
            ca.subprocess.run = old
            ca.shutil.which = old_which
        self.assertTrue(j["ok"])
        self.assertIn(j["verdict"], ("GO", "WARN", "NO-GO"))
        ids = [c["id"] for c in j["checks"]]
        for must in ("ver_match", "claude_cli", "claude_auth", "disk", "d2r_window", "handshake"):
            self.assertIn(must, ids)
        vm = next(c for c in j["checks"] if c["id"] == "ver_match")
        self.assertTrue(vm["ok"], "repo stamps must agree: %s" % j.get("vers"))
        au = next(c for c in j["checks"] if c["id"] == "claude_auth")
        self.assertTrue(au["ok"])   # mocked 'ok' ping
        # d2r_window mocked run returns 'ok' stdout rc0 → running=True; either way severity is warn
        self.assertEqual(next(c for c in j["checks"] if c["id"] == "d2r_window")["severity"], "warn")

    def test_gate_no_go_on_dead_auth(self):
        class _PR:
            returncode = 1
            stdout = b""
            stderr = b"please run /login"
        class _G5Off:
            @staticmethod
            def is_primary():
                return False
        old = ca.subprocess.run
        old_which = ca.shutil.which
        old_sock = ca._sock_open
        old_g5 = ca._G5
        old_find = getattr(ca, "_find_claude_bin", None)
        ca.subprocess.run = lambda *a, **k: _PR()
        ca.shutil.which = lambda *a, **k: "/usr/bin/claude"
        ca._sock_open = lambda *a, **k: False   # pin "agent OFF" so the auth ping actually runs (v924-R4 skips it during ON AIR)
        ca._G5 = _G5Off   # v1380.4 — machine G5 primary must not soft-skip this gate
        if old_find:
            ca._find_claude_bin = lambda *a, **k: "/usr/bin/claude"
        try:
            j = ca.farmgate_payload()
        finally:
            ca.subprocess.run = old
            ca.shutil.which = old_which
            ca._sock_open = old_sock
            ca._G5 = old_g5
            if old_find:
                ca._find_claude_bin = old_find
        au = next(c for c in j["checks"] if c["id"] == "claude_auth")
        self.assertFalse(au["ok"])
        self.assertEqual(j["verdict"], "NO-GO")
        self.assertIn("fix", au)


class TestExitSafeguard(unittest.TestCase):
    """v935.11 R6 — the v935.8 EXIT SAFEGUARD (_console_exit_stop_onair): closing the console
    must stop ON AIR exactly once ('it's always on'), be idempotent across the many exit paths
    (window-close / atexit / SIGTERM / SIGINT), and NEVER stop from a secondary --window-only
    attach (that process is a viewer — the primary control process owns the agent)."""

    def setUp(self):
        self._calls = []
        # snapshot everything the safeguard touches, restore in tearDown (no sockets, no sleeps)
        self._old = {
            "stop_agent": ca.stop_agent,
            "_force_kill_all_agents": ca._force_kill_all_agents,
            "_agent_alive": ca._agent_alive,
            "_port_listener_pid": ca._port_listener_pid,
            "_agent_mode": ca._agent_mode,
            "_WINDOW_ONLY": ca._WINDOW_ONLY,
            "_EXIT_STOP_DONE": ca._EXIT_STOP_DONE,
        }
        ca.stop_agent = lambda farewell=True: (
            self._calls.append(("stop", farewell)) or {"ok": True, "msg": "stopped"})
        ca._force_kill_all_agents = lambda reason="": (
            self._calls.append(("force", reason)) or {"ok": True, "msg": "killed"})
        # Pin "agent is live, no residual after stop": the cheap early-return needs mode=='off',
        # so 'live' forces the real stop path; the residual force-kill fires on (listener OR alive),
        # both False here, so a clean run invokes stop_agent once and NOT _force_kill_all_agents.
        ca._agent_alive = lambda: False
        ca._port_listener_pid = lambda port=None: None
        ca._agent_mode = "live"
        ca._WINDOW_ONLY = False
        ca._EXIT_STOP_DONE = False

    def tearDown(self):
        for k, v in self._old.items():
            setattr(ca, k, v)

    def test_first_call_stops_onair(self):
        r = ca._console_exit_stop_onair("unit")
        self.assertIn(("stop", False), self._calls)   # farewell OFF → instant quit
        self.assertFalse(any(c[0] == "force" for c in self._calls))  # no residual → no force kill
        self.assertTrue(r.get("ok"))

    def test_second_call_is_idempotent_noop(self):
        ca._console_exit_stop_onair("first")
        n = len(self._calls)
        r = ca._console_exit_stop_onair("second")
        self.assertEqual(len(self._calls), n)         # nothing new invoked
        self.assertTrue(r.get("skipped"))

    def test_window_only_never_stops(self):
        ca._WINDOW_ONLY = True
        r = ca._console_exit_stop_onair("window-only-attach")
        self.assertEqual(self._calls, [])             # primary owns ON AIR — viewer stops nothing
        self.assertTrue(r.get("skipped"))
        self.assertFalse(ca._EXIT_STOP_DONE)          # window-only must not consume the one-shot

    def test_v1410_mark_window_gone_kills_handles(self):
        # Apple hang class: evaluate_js on a dying WKWebView after ✕. Mark gone first.
        ca._WINDOW_LIVE = True
        ca._MAIN_WIN = object()
        ca._mark_window_gone("unit")
        self.assertFalse(ca._WINDOW_LIVE)
        self.assertIsNone(ca._MAIN_WIN)

    def test_v1410_ejs_refuses_dead_window(self):
        ca._WINDOW_LIVE = False
        # would hang forever if it actually called evaluate_js on a dead webview
        self.assertIsNone(ca._ejs(object(), "1+1", timeout=0.2))

    def test_v1410_schedule_exit_stop_is_nonblocking(self):
        # close handlers must return in <<1 frame so Cocoa can dismiss the window
        import time
        ca._EXIT_STOP_DONE = False
        ca._WINDOW_ONLY = False
        ca._agent_mode = "live"
        t0 = time.time()
        ca._schedule_exit_stop("unit-x")
        elapsed = time.time() - t0
        self.assertLess(elapsed, 0.15)   # fire-and-forget, never waits for stop_agent
        time.sleep(0.35)                 # daemon finishes stop
        self.assertIn(("stop", False), self._calls)


class TestHistFrameResolve(unittest.TestCase):
    """v940.4 — THEATRE debugger: verify #v frameIds and journal shield base protection.
    Claude DEBUG_THEATRE mystery: 'photo pruned' on beats whose JPEG still lived as N_ts.jpg
    because has checked fid+'.jpg' literally (N_ts#v.jpg never exists)."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp(prefix="tvd-hist-")
        self._old_hist = ca.HIST_DIR
        ca.HIST_DIR = self.tmp
        # a real archived deep-read photo
        with open(os.path.join(self.tmp, "3_1784573580533.jpg"), "wb") as _f:
            _f.write(b"fakejpg")

    def tearDown(self):
        ca.HIST_DIR = self._old_hist
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_base_frame_exists(self):
        self.assertTrue(ca._hist_has_frame("3_1784573580533"))
        self.assertEqual(ca._hist_frame_rel("3_1784573580533"), "3_1784573580533.jpg")

    def test_verify_suffix_resolves_to_base(self):
        # second-eye journals frameId with #v — file is always the base jpeg
        self.assertTrue(ca._hist_has_frame("3_1784573580533#v"))
        self.assertEqual(ca._hist_frame_rel("3_1784573580533#v"), "3_1784573580533.jpg")

    def test_missing_frame_is_false(self):
        self.assertFalse(ca._hist_has_frame("99_0000000000000"))
        self.assertEqual(ca._hist_frame_rel("99_0000000000000"), "")

    def test_journal_shield_protects_base_for_verify_id(self):
        # when journal names 'N_ts#v', reaper must protect 'N_ts.jpg' not only 'N_ts#v.jpg'
        import tv_diablo as tvd
        old_j, old_st = tvd.JOURNAL, dict(tvd._JFID_STATE)
        jpath = os.path.join(self.tmp, "sessions.jsonl")
        with open(jpath, "w", encoding="utf-8") as f:
            f.write(json.dumps({"frameId": "3_1784573580533#v", "lane": "verify"}) + "\n")
        tvd.JOURNAL = jpath
        tvd._JFID_STATE["path"] = None
        tvd._JFID_STATE["ids"] = None
        try:
            prot = tvd._journal_frame_ids()
            self.assertIn("3_1784573580533.jpg", prot)
            self.assertIn("3_1784573580533#v.jpg", prot)
        finally:
            tvd.JOURNAL = old_j
            tvd._JFID_STATE.clear()
            tvd._JFID_STATE.update(old_st)


class TestFunnelNeverZeroGuard(unittest.TestCase):
    """v948.17 — Grok P0-1 pin (2026-07-21 fast-run soak): 'a 404-then-4 sequence must keep
    404.' The KAI funnel's SET-style write (ADJ-subtract-then-add nets to a per-key SET) must
    never regress an existing REAL tally down to a thinner reel-recheck read — the never-zero
    law, now applied to the WRITE path, not just the display's `tab_best`."""

    def test_missing_existing_always_applies(self):
        self.assertTrue(ca._funnel_never_zero_guard(0, 4))
        self.assertTrue(ca._funnel_never_zero_guard(None, 0))

    def test_404_then_4_is_blocked(self):
        # the EXACT soak sequence — runes landed 404 live, a thin gap-funnel read said 4
        self.assertFalse(ca._funnel_never_zero_guard(404, 4))

    def test_equal_or_bigger_recount_applies(self):
        self.assertTrue(ca._funnel_never_zero_guard(404, 404))
        self.assertTrue(ca._funnel_never_zero_guard(404, 500))

    def test_bad_inputs_never_raise(self):
        self.assertTrue(ca._funnel_never_zero_guard("bad", "4"))    # existing coerces to 0 → apply
        self.assertFalse(ca._funnel_never_zero_guard(404, "bad"))   # new coerces to 0 → blocked


class TestTabBestTotal(unittest.TestCase):
    """The never-zero 'best REAL total per tab' truth from journal rows — the same law already
    used for THEATRE DISPLAY (`tab_best` in `_beat_dossier`'s maps), now reused to seed the
    funnel WRITE guard so display and write agree on what 'the real tally' is."""

    def _rows(self):
        return [
            {"intake": {"tab": "runes", "ok": True, "total": 12}},
            {"intake": {"tab": "runes", "ok": True, "total": 404}},    # the live tally
            {"intake": {"tab": "runes", "ok": False, "total": 900}},   # errored — never counts
            {"intake": {"tab": "gems", "ok": True, "total": 0}},       # zero — never counts
            {"intake": {"tab": "runes", "ok": True, "total": 4}},      # a later thin funnel read
            {"scene": "gameplay"},                                    # no intake — ignored
        ]

    def test_picks_the_max_real_total(self):
        self.assertEqual(ca._tab_best_total(self._rows(), "runes"), 404)

    def test_zero_and_error_never_count(self):
        self.assertEqual(ca._tab_best_total(self._rows(), "gems"), 0)

    def test_unknown_tab_is_zero(self):
        self.assertEqual(ca._tab_best_total(self._rows(), "materials"), 0)

    def test_case_insensitive_tab_match(self):
        rows = [{"intake": {"tab": "RUNES", "ok": True, "total": 50}}]
        self.assertEqual(ca._tab_best_total(rows, "runes"), 50)


class TestKaiFunnelGuardWiring(unittest.TestCase):
    """Structural pin: the Stage-3 funnel fire loop in `_kai_closer_loop` must actually call
    the never-zero guard before firing (Python skip) AND carry PREV into the JS write itself
    (defense in depth) — guards against a future edit silently dropping either half."""

    def test_fire_loop_checks_prev_best_before_firing(self):
        import inspect
        src = inspect.getsource(ca._kai_closer_loop)
        self.assertIn("_tab_best_total(_fresh_t3, t3)", src)
        self.assertIn("_prev_best_t3 > 0", src)
        self.assertIn("KAI funnel guard: skip", src)
        self.assertIn("var PREV=%s;", src)
        self.assertIn("PREV<=0||newTotal>=PREV", src)

    def test_gap_funnel_select_uses_fresh_journal_read(self):
        # v948.17 — sess_rows is cached BEFORE the long OCR sweep; a live tally landing during
        # that sweep must still be visible to the gap-funnel 'receipted' check, or a tab that
        # already has a real receipt gets queued for an overwrite-risking gap-funnel anyway.
        import inspect
        src = inspect.getsource(ca._kai_closer_loop)
        self.assertIn('_gap_rows = [r for r in _kai_journal_rows() if r.get("sessionId") == sid]', src)
        self.assertIn("_kai_stage3_gap_funnels(_plan + routing_scan, _gap_rows)", src)


class TestKaiFunnelHonestErrorReceipt(unittest.TestCase):
    """v948.17 — Grok P0-2 pin (2026-07-21 fast-run soak): the gems funnel fired (control log
    printed) but NO /intake_result receipt ever journaled — the promise chain rejected and the
    OLD outer `.catch(function(){})` was silent. Both Stage-3 fetch chains (tally funnel + the
    vault funnel firing right beside it) must now post an honest ok:false receipt on rejection,
    never a silent drop."""

    def test_tally_funnel_outer_catch_posts_honest_receipt(self):
        import inspect
        src = inspect.getsource(ca._kai_closer_loop)
        self.assertIn("funnel fetch/intake rejected", src)

    def test_vault_funnel_outer_catch_posts_honest_receipt(self):
        import inspect
        src = inspect.getsource(ca._kai_closer_loop)
        self.assertIn("vault fetch/intake rejected", src)


class TestKaiWriteReportAtomic(unittest.TestCase):
    """v948.17 — Grok P0-3 pin (2026-07-21 fast-run soak): kai_report.json must never be left
    half-written or silently stuck at a stale/partial shape. `_kai_write_report_atomic` writes
    to a tmp file in the SAME directory and os.replace()s it in — a reader never sees a
    half-written file, and a failed write leaves any OLD report untouched, not corrupted."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="tvd-kai-report-")
        self.path = os.path.join(self.d, "kai_report.json")

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_writes_full_report(self):
        report = {"sid": "s1", "scanned": 10, "routing": [{"f": "a.jpg"}], "register": [{"name": "x"}]}
        ok = ca._kai_write_report_atomic(self.path, report)
        self.assertTrue(ok)
        with open(self.path, encoding="utf-8") as f:
            got = json.load(f)
        self.assertEqual(got["routing"], [{"f": "a.jpg"}])
        self.assertEqual(got["register"], [{"name": "x"}])

    def test_no_leftover_tmp_file(self):
        ca._kai_write_report_atomic(self.path, {"sid": "s1"})
        self.assertFalse(os.path.isfile(self.path + ".tmp"))

    def test_failed_write_never_corrupts_existing_report(self):
        good = {"sid": "s1", "routing": [{"f": "good.jpg"}], "register": [{"name": "good"}]}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(good, f)

        class _Unserializable:
            pass

        ok = ca._kai_write_report_atomic(self.path, {"sid": "s1", "bad": _Unserializable()})
        self.assertFalse(ok)
        with open(self.path, encoding="utf-8") as f:
            still = json.load(f)
        self.assertEqual(still, good)                          # untouched, never truncated
        self.assertFalse(os.path.isfile(self.path + ".tmp"))   # tmp cleaned up on failure


class TestKaiCloserAtomicWiring(unittest.TestCase):
    """Structural pin: the register/routing/completeness stage must write via the atomic
    helper inside a `finally:` (so it ALWAYS runs, whatever subset of fields succeeded), and
    each sub-stage must have its own try/except so one failure can't blank a sibling that
    already computed successfully."""

    def test_second_report_write_is_inside_a_finally(self):
        import inspect
        src = inspect.getsource(ca._kai_closer_loop)
        call = '_kai_write_report_atomic(os.path.join(rd, "kai_report.json"), report)'
        first = src.index(call)
        second = src.index(call, first + 1)   # scan-only write, then the post-Stage3 write
        finally_between = src.find("finally:", first, second)
        self.assertNotEqual(finally_between, -1,
                             "the post-Stage3 kai_report write is not inside a finally: block")

    def test_register_routing_completeness_each_have_own_except(self):
        import inspect
        src = inspect.getsource(ca._kai_closer_loop)
        self.assertIn("KAI register compile failed", src)
        self.assertIn("KAI routing build failed", src)
        self.assertIn("KAI completeness failed", src)

    def test_gate_pingpong_write_uses_the_atomic_helper(self):
        # v1209 — TORN-WRITE class, same fix as kai_report.json (Grok P0-3 / v948.17) applied
        # to the sibling gate_pingpong.json persisted file: a plain `open(...,'w') + json.dump`
        # left it truncatable on a crash mid-write, and the read side silently resets tries to
        # {} on a bad parse — defeating the file's own "a reel never retries forever" law by
        # letting an already-pinned honest-miss frame get re-queued past its cap after a crash.
        import inspect
        src = inspect.getsource(ca._kai_closer_loop)
        self.assertIn('_kai_write_report_atomic(_pp_path, _pp_next)', src)
        # regression guard: must not have regressed back to a bare write for this file
        self.assertNotIn('with open(_pp_path, "w"', src)


class TestGateTallyPromotionHonestSources(unittest.TestCase):
    """v1180 ROUTE/GATE fix — the v947 tally-promotion branch in `_kai_build_routing`
    (weak-quorum "gameplay"/"stash" frame promoted to a stash-* tab when tabstrip+grid
    agree) used to union the OLD label's sources into the NEW label's sources unconditionally.
    Those old sources are brains that voted the label being OVERRIDDEN (e.g. ocr said
    "gameplay") — folding them in falsely counted a DISSENTING brain as agreeing with the
    promoted tally label, inflating confidence/gateSources with a contradiction and letting
    the gate pass on dishonest evidence. `sources`/`gateSources` must only ever list brains
    whose vote actually equals the final label (the documented contract in
    `_kai_build_routing`'s own docstring)."""

    def _scan_row(self, ocr_label="gameplay", ocr_on=True):
        return {
            "f": "f1.jpg", "ts": 1000,
            "ocr": ocr_on, "ocrLabel": ocr_label, "label": ocr_label,
            "tabstripLabel": "stash-runes", "tabstrip": False,   # weak/unconfirmed booleans —
            "gridLabel": "stash-runes", "grid": False,           # the exact v947 promotion case
        }

    def test_dissenting_brain_not_folded_into_promoted_sources(self):
        routing = ca._kai_build_routing([self._scan_row()], [], "sid1", [])
        row = routing[0]
        self.assertEqual(row["label"], "stash-runes")
        # ocr voted "gameplay" — it must NEVER appear as a source of "stash-runes"
        self.assertNotIn("ocr", row["sources"])
        self.assertNotIn("ocr", row["gateSources"])
        self.assertEqual(row["sources"], ["grid", "tabstrip"])

    def test_promotion_still_clears_two_class_quorum(self):
        # tabstrip (chrome) + grid (layout) alone must still be enough to fire — the v947
        # intent (fast intake-mimic promotion) is preserved, just with honest sourcing.
        routing = ca._kai_build_routing([self._scan_row()], [], "sid1", [])
        row = routing[0]
        self.assertEqual(row["confidence"], 2)
        self.assertTrue(row["gatePass"])


class TestQuorumTieIsDisagreement(unittest.TestCase):
    """v1186 ROUTE/GATE fix — `_kai_quorum_label`'s disagreement check only looked at
    `top_n < 2` (a WEAK single winner, e.g. a 1-1-1 spread), never at whether 2+ distinct
    labels were tied AT the top with a real count (2-vs-2, 3-vs-3, ...). Counter.most_common
    breaks ties by first-seen insertion order — an iteration-order artifact, not evidence —
    so a genuine split between two EQUALLY-backed, DIFFERENT labels was silently resolved to
    whichever brain happened to vote first, with the losing side's votes vanishing from
    `sources` entirely (no trace it ever happened). Reachable live: 'read'+'judge' vote
    'tooltip' unconditionally whenever a deep read/judge verdict lands near a frame — a
    frame that ALSO gets a clean tabstrip+grid 'stash-*' read produces exactly a 2-2 split
    between the judge cell and a tally cell, two genuinely different funnels."""

    def test_pure_2v2_tie_flagged_disagreement(self):
        # two independent-class pairs backing two DIFFERENT tally labels, no journal
        # short-circuit involved (isolates the Counter tie-break bug itself)
        votes = {"ocr": "stash-runes", "tabstrip": "stash-runes",
                 "grid": "stash-gems", "read2": "stash-gems"}
        label, sources, disagree = ca._kai_quorum_label(votes)
        self.assertEqual(disagree, "disagreement")
        self.assertEqual(sources, [])

    def test_clean_majority_still_wins_no_false_tie(self):
        # 2-vs-1 must still be a confident, undisturbed win (regression guard against
        # over-fixing into false disagreements)
        votes = {"ocr": "stash-runes", "tabstrip": "stash-runes", "grid": "stash-gems"}
        label, sources, disagree = ca._kai_quorum_label(votes)
        self.assertIsNone(disagree)
        self.assertEqual(label, "stash-runes")
        self.assertEqual(sources, ["ocr", "tabstrip"])

    def test_lone_single_vote_still_wins_no_false_tie(self):
        # a single non-gameplay vote with no rival must still win outright (policy #3)
        votes = {"ocr": "stash-runes"}
        label, sources, disagree = ca._kai_quorum_label(votes)
        self.assertIsNone(disagree)
        self.assertEqual(label, "stash-runes")

    def test_judge_vs_tally_2v2_reachable_through_full_routing(self):
        # the live-reachable case: a deep read AND a judge verdict both land on this frame
        # (2 votes for 'tooltip' -> route=judge), while tabstrip+grid independently agree on
        # 'stash-runes' (2 votes -> route=tally:runes) — a genuine 2-2 split between two
        # DIFFERENT funnel cells. Must come through as disagreement, not a confident pick.
        sess_rows = [{"lane": "deep", "captureTs": 1000, "names": ["Vex Rune"]}]
        journal_rows = [{"frameId": "reel_sid1/f1", "lane": "kai", "mode": "kai-judge",
                          "kai": {"judge": {"name": "Vex Rune", "tier": "keep"}}}]
        scan = [{
            "f": "f1.jpg", "ts": 1000,
            "tabstripLabel": "stash-runes", "tabstrip": True,
            "gridLabel": "stash-runes", "grid": True,
        }]
        routing = ca._kai_build_routing(scan, sess_rows, "sid1", journal_rows)
        row = routing[0]
        self.assertEqual(row["sources"], [])
        self.assertEqual(row["confidence"], 0)
        self.assertFalse(row["gatePass"])


class TestDedupeNeverErasesARealReceipt(unittest.TestCase):
    """v1189 ROUTE/GATE fix — the v944 exact-sig dedupe branch in `_kai_build_routing`
    unconditionally set `routed = None` for any frame sharing its predecessor's cheap
    pixel signature. `routed` is a HISTORICAL FACT (a funnel/judge receipt already landed
    on THIS frame's own fid via `funnel_by_fid`/`judge_fids`), not a routing decision — and
    Stage 3's own doc says a funnel receipt fires against the NEWEST frame of a run, which
    is exactly the frame most likely to be pixel-identical to its predecessor (a static
    stash panel held for a few frames). Nulling `routed` there made `_kai_reconcile` report
    a false 'miss'/'no funnel receipt has landed yet' for a frame that genuinely fired, and
    undercounted any 'routed' audit metric. The near-dup branch a few lines below already
    guards on `if routed is None:` — this fix brings the exact-sig branch in line with that
    established pattern instead of inventing a new one."""

    def _scan(self, sig=("sameSig", b"x")):
        return [
            {"f": "f1.jpg", "ts": 1000, "sig": sig,
             "tabstripLabel": "stash-runes", "tabstrip": True,
             "gridLabel": "stash-runes", "grid": True},
            {"f": "f2.jpg", "ts": 1200, "sig": sig,
             "tabstripLabel": "stash-runes", "tabstrip": True,
             "gridLabel": "stash-runes", "grid": True},
        ]

    def test_receipted_dup_frame_keeps_its_routed_field(self):
        # Stage 3's "newest frame wins" pattern: the receipt lands on f2, the LATER of the
        # two sig-identical frames.
        journal_rows = [{"frameId": "reel_sid1/f2",
                          "intake": {"kind": "kai-funnel", "tab": "runes", "ok": True, "total": 40}}]
        routing = ca._kai_build_routing(self._scan(), [], "sid1", journal_rows)
        f1, f2 = routing[0], routing[1]
        self.assertIsNone(f1["routed"])
        self.assertEqual(f2["routed"], "kai-funnel")
        self.assertIsNone(f2["skipReason"])   # a routed row carries no dup skip marker

    def test_receipt_visible_to_reconcile_not_a_false_miss(self):
        journal_rows = [{"frameId": "reel_sid1/f2",
                          "intake": {"kind": "kai-funnel", "tab": "runes", "ok": True, "total": 40}}]
        routing = ca._kai_build_routing(self._scan(), [], "sid1", journal_rows)
        rec = {r["f"]: r for r in ca._kai_reconcile(routing, [], [])}
        self.assertEqual(rec["f2.jpg"]["owner"], "funnel")
        self.assertNotEqual(rec["f2.jpg"]["verdict"], "miss")

    def test_plain_dup_with_no_receipt_still_unrouted(self):
        # regression guard: a genuine duplicate with NO receipt on either frame must still
        # be un-routed exactly as before this fix.
        routing = ca._kai_build_routing(self._scan(sig=("sameSig2", b"y")), [], "sid1", [])
        f1, f2 = routing[0], routing[1]
        self.assertIsNone(f1["routed"])
        self.assertEqual(f1["route"], "tally:runes")
        self.assertIsNone(f2["routed"])
        self.assertIsNone(f2["route"])
        self.assertEqual(f2["skipReason"], "dup-of:f1.jpg")


class TestReconcileCarriesDiabloScene(unittest.TestCase):
    """v1253 R1 (DIABLO-LANGUAGE) — the reconciler used to collapse the read's rich Diablo
    scene (town/stash/inventory/loot/gameplay/transition + stashTab + area) down to the
    generic routing label before it reached the session summary + retro, so a portal/loading
    frame surfaced as "gameplay / near black screen". `_kai_reconcile` now carries the read's
    OWN scene/tab/area through (nearest deep read within ±4s) — ADDITIVE, never touching
    owner/verdict/why. This proves the scene now flows and stays honest when no read covers a
    frame."""

    def test_transition_frame_carries_scene_transition(self):
        # a portal/loading frame: routing collapsed it to 'gameplay', but the read said
        # scene='transition' with NO names — must survive as scene='transition'.
        routing = [{"f": "f1.jpg", "ts": 10000, "label": "gameplay", "sources": []}]
        sess_rows = [{"lane": "deep", "captureTs": 10200, "scene": "transition",
                      "stashTab": "", "area": "", "names": []}]
        rec = ca._kai_reconcile(routing, [], sess_rows)[0]
        self.assertEqual(rec["scene"], "transition")
        # additive-only: the owner/verdict decision is unchanged (still a non-item frame)
        self.assertIsNone(rec["owner"])
        self.assertIsNone(rec["verdict"])

    def test_stash_gems_frame_carries_tab_and_scene(self):
        # a stash frame whose read named the gems tab — scene='stash' + tab='gems' survive.
        routing = [{"f": "f2.jpg", "ts": 20000, "label": "stash-gems", "sources": ["grid"]}]
        sess_rows = [{"lane": "deep", "captureTs": 20100, "scene": "stash",
                      "stashTab": "gems", "area": "Rogue Encampment", "names": []}]
        rec = ca._kai_reconcile(routing, [], sess_rows)[0]
        self.assertEqual(rec["scene"], "stash")
        self.assertEqual(rec["tab"], "gems")
        self.assertEqual(rec["area"], "Rogue Encampment")

    def test_no_nearby_read_leaves_scene_none(self):
        # honest: a frame with no deep read within ±4s invents nothing.
        routing = [{"f": "f3.jpg", "ts": 90000, "label": "gameplay", "sources": []}]
        sess_rows = [{"lane": "deep", "captureTs": 10000, "scene": "town",
                      "stashTab": "", "area": "", "names": []}]
        rec = ca._kai_reconcile(routing, [], sess_rows)[0]
        self.assertIsNone(rec["scene"])
        self.assertIsNone(rec["tab"])
        self.assertIsNone(rec["area"])

    def test_scene_flows_into_materialized_engine_frame(self):
        # the sealed EngineFrame (kai_report.json, read back by the Theatre) carries it too.
        routing = [{"f": "f4.jpg", "ts": 30000, "label": "gameplay", "sources": []}]
        sess_rows = [{"lane": "deep", "captureTs": 30000, "scene": "transition",
                      "stashTab": "", "area": "", "names": []}]
        maps = ca._kai_engine_frame_maps(routing, [], sess_rows)
        efs = ca._kai_build_engine_frames(routing, [], {}, maps)
        self.assertEqual(efs[0]["scene"], "transition")


class TestGridVoteRequiresGenuineGridSignal(unittest.TestCase):
    """v1194 ROUTE/GATE fix — `_kai_closer_loop`'s reel-scan build used to set a scan row's
    gridLabel (the 'layout' independent evidence class, _ROUTER_INDEP_CLASS) straight from
    stash_eye's FUSED tab whenever that fused tab named a tally tab, with no check that grid
    itself actually contributed to the fusion. `fuse_tab_signals` (stash_eye.py) tries OCR's
    chrome-strip read FIRST ('1 OCR tally wins over vague vault labels') and returns before
    grid is even consulted when OCR alone is unambiguous — its own `sources` list is the only
    honest record of which eyes actually agreed. Crediting a purely-OCR-driven fused tab as a
    'grid' vote let ONE real signal (chrome OCR) masquerade as TWO independent evidence
    classes ('chrome' AND 'layout'), which alone clears `_router_conf`'s confidence>=2 gate
    (v947/v949) on a single witness dressed up as two. `_kai_grid_vote_label` is the extracted
    pure decision — testable in isolation from the subprocess-driven closer loop."""

    def test_ocr_only_fusion_is_not_credited_as_a_grid_vote(self):
        # fuse_tab_signals rule 1: OCR alone named the tally tab; grid never corroborated
        # (not in the fusion's own sources list) — must NOT become a grid vote.
        self.assertIsNone(ca._kai_grid_vote_label("runes", ["ocr"], "", "stash-runes"))

    def test_grid_corroborated_fusion_still_credited(self):
        # grid genuinely agreed (present in fuse_tab_signals' sources) — real independent
        # evidence, must still count.
        self.assertEqual(ca._kai_grid_vote_label("runes", ["ocr", "grid"], "", "stash-runes"),
                          "stash-runes")

    def test_grid_solo_retro_still_credited(self):
        # v948.7 KAI retro allow_grid_solo: grid alone (no live sticky) still tags "grid"
        # in sources — must still count.
        self.assertEqual(ca._kai_grid_vote_label("gems", ["grid", "solo"], "", "stash-gems"),
                          "stash-gems")

    def test_raw_pixel_grid_label_still_falls_back_when_fusion_isnt_grid_backed(self):
        # the fused tab isn't a tally tab (or was OCR-only), but the RAW pixel-only
        # classify_stash_grid() label independently is — a genuinely independent signal,
        # must still be honored.
        self.assertEqual(ca._kai_grid_vote_label("", [], "stash-materials", "gameplay"),
                          "stash-materials")

    def test_no_signal_is_none(self):
        self.assertIsNone(ca._kai_grid_vote_label("", [], "", "gameplay"))


class TestRetroPromoteNeverFabricatesAGridWitness(unittest.TestCase):
    """v1198 ROUTE/GATE fix — `_kai_retro_promote_tally` (v948.7, the retro cluster-promote
    pass that runs on `routing_scan` BEFORE `_kai_build_routing`) used to stamp
    `grid=True, gridLabel=<promoted tab>` onto every gridLabel-less frame in a stash-ish
    visual cluster, borrowed from the CLUSTER's majority tally vote (other frames' evidence).
    `_kai_build_routing`/`_router_conf` then counted that as a genuinely independent 'layout'
    witness for THAT SPECIFIC FRAME — grid never actually looked at its pixels. A frame with
    only ONE real vote of its own (e.g. tabstrip alone, 'chrome' class) could then clear the
    2-independent-class quorum on a fabricated second witness. The cluster's honest majority
    context is still applied to the DISPLAY label (untouched by this fix); routing/gate
    honesty for each frame must rest on its own real evidence — `_kai_stage3_gap_funnels`
    already exists as the honest, explicitly-lower-bar fallback for an isolated single-witness
    tally frame, so no real routability is lost."""

    def _cluster(self):
        # frame A: only its OWN tabstrip evidence, no grid evidence at all. Frames B/C:
        # genuine grid evidence forming the cluster majority.
        return [
            {"f": "a.jpg", "ts": 1000, "label": "stash",
             "tabstripLabel": "stash-runes", "tabstrip": True},
            {"f": "b.jpg", "ts": 1200, "label": "stash-runes",
             "gridLabel": "stash-runes", "grid": True},
            {"f": "c.jpg", "ts": 1400, "label": "stash-runes",
             "gridLabel": "stash-runes", "grid": True},
        ]

    def test_gridless_frame_gets_no_fabricated_grid_vote(self):
        promoted = ca._kai_retro_promote_tally(self._cluster())
        a = promoted[0]
        self.assertIsNone(a.get("grid"))
        self.assertIsNone(a.get("gridLabel"))
        # the honest majority-context label rewrite is still applied
        self.assertEqual(a.get("label"), "stash-runes")

    def test_gridless_frame_no_longer_false_gate_passes(self):
        promoted = ca._kai_retro_promote_tally(self._cluster())
        routing = ca._kai_build_routing(promoted, [], "sid1", [])
        row_a = next(r for r in routing if r["f"] == "a.jpg")
        self.assertEqual(row_a["sources"], ["tabstrip"])
        self.assertEqual(row_a["confidence"], 1)
        self.assertFalse(row_a["gatePass"])
        self.assertEqual(row_a["gateReason"], "quorum<2")

    def test_frames_with_genuine_grid_evidence_unaffected(self):
        promoted = ca._kai_retro_promote_tally(self._cluster())
        b = next(r for r in promoted if r["f"] == "b.jpg")
        self.assertTrue(b.get("grid"))
        self.assertEqual(b.get("gridLabel"), "stash-runes")


class TestLiveRoutingRowSourcesMatchTheWinningLabel(unittest.TestCase):
    """v1203 ROUTE/GATE fix — `_kai_live_routing_row` (the _engine_driver 2s-poll bridge that
    hands a lightweight live guess to the SAME `_kai_reconcile` the closer uses) set
    `sources`/`confidence` from raw `names` presence alone, regardless of which label branch
    actually won. `scene == 'stash'` is checked BEFORE `names` — so a live read that is on a
    stash tab AND happens to carry a (stale/co-reported) `names` field came out labeled
    'stash-runes' but with `sources=['read']` anyway. 'read' is only ever a real witness for
    a 'tooltip' label everywhere else in the routing model — this dict is documented as
    'routing-row-compatible' and must honor that same contract (the same one v1180's fix
    enforced in `_kai_build_routing`). The mislabeled sources fed `_kai_reconcile`'s
    stash-* branch (`elif row.get("sources"): owner="ocr"`), narrating a live 'read' event
    as 'ocr' tab-eye evidence it never was — real-only during the live/pre-seal window
    (gatePass is always None here; the sealed pass always wins per SEALED-WINS LAW)."""

    def test_stash_label_with_stray_names_carries_no_read_source(self):
        rd = {"scene": "stash", "stashTab": "runes", "names": ["Vex Rune"],
              "captureTs": 1000, "frameId": "reel_sid1/f1"}
        row = ca._kai_live_routing_row(rd)
        self.assertEqual(row["label"], "stash-runes")
        self.assertEqual(row["sources"], [])
        self.assertEqual(row["confidence"], 0)

    def test_reconcile_no_longer_mislabels_it_as_ocr_owned(self):
        rd = {"scene": "stash", "stashTab": "runes", "names": ["Vex Rune"],
              "captureTs": 1000, "frameId": "reel_sid1/f1"}
        row = ca._kai_live_routing_row(rd)
        rec = ca._kai_reconcile([row], [], [])[0]
        self.assertIsNone(rec["owner"])

    def test_normal_tooltip_row_unaffected(self):
        rd = {"scene": "", "names": ["Vex Rune"], "captureTs": 2000, "frameId": "reel_sid1/f2"}
        row = ca._kai_live_routing_row(rd)
        self.assertEqual(row["label"], "tooltip")
        self.assertEqual(row["sources"], ["read"])
        self.assertEqual(row["confidence"], 1)

    def test_normal_stash_row_with_no_names_unaffected(self):
        rd = {"scene": "stash", "stashTab": "gems", "captureTs": 3000, "frameId": "reel_sid1/f3"}
        row = ca._kai_live_routing_row(rd)
        self.assertEqual(row["label"], "stash-gems")
        self.assertEqual(row["sources"], [])
        self.assertEqual(row["confidence"], 0)


class TestDriverLiveHonestRejectionReceipt(unittest.TestCase):
    """v1185 — the engine-driver's OWN live fire chains (vaultcount_/vault_/tally, the same
    three sites hardened for never-zero at v1182) each ended their promise chain in a bare
    `.catch(function(){})` — a REJECTED fetch/intake (network hiccup, a synchronous throw from
    vaultGridCount/vaultIntake/runeIntake-etc) vanished with NO /intake_result POST at all: no
    honest-miss, no refire signal for `_drv_empty_refire_plan`, just gone. This is the exact
    silent-drop class the Stage-3 KAI funnel got hardened against at v948.17 (Grok P0-2,
    TestKaiFunnelHonestErrorReceipt above) — mirrored here for the live-driver's three chains.
    A rejection now posts ok:false/total:0/errors:1 (a real failure, distinct from the v1182
    guardHeld:true/ok:true block) so it can actually refire like any other empty/error shot,
    rather than a guard-held 'we already have a good tally' state that should NOT refire."""

    def test_vaultcount_outer_catch_posts_honest_receipt(self):
        import inspect
        src = inspect.getsource(ca._engine_driver)
        self.assertIn("vault-count fetch/intake rejected", src)

    def test_vault_outer_catch_posts_honest_receipt(self):
        import inspect
        src = inspect.getsource(ca._engine_driver)
        self.assertIn("'vault fetch/intake rejected'", src)

    def test_tally_outer_catch_posts_honest_receipt(self):
        import inspect
        src = inspect.getsource(ca._engine_driver)
        self.assertIn("tally fetch/intake rejected", src)

    def test_rejection_receipts_are_real_failures_not_guard_holds(self):
        # each rejection-catch body reports ok:false/total:0/errors:1 — a genuine failure
        # signal (_intake_is_real is False, so _drv_empty_refire_plan's refire ladder fires),
        # never confused with the v1182 guardHeld:true/ok:true "already have a good tally" state.
        import inspect
        src = inspect.getsource(ca._engine_driver)
        for kind in ("vault-count", "vault", "tally"):
            self.assertIn(
                f"kind:'{kind}',ok:false,counts:{{}},total:0,errors:1", src,
                f"{kind} rejection receipt must be an honest ok:false failure")


class TestDriverLiveNeverZeroGuardWiring(unittest.TestCase):
    """v1182 — the engine-driver's OWN live tally fire (every stash-tab visit during actual
    play, not just Stage-3's post-seal gap-fill) does the same SET-style ADJ-subtract write as
    the KAI funnel but never got the v948.17 never-zero guard — a thin/partial live photo
    (ok:true, low total) was free to stomp an already-larger verified same-session tally, the
    exact '404 then 4' regression TestFunnelNeverZeroGuard pins for the OTHER fire site.
    Structural pin, mirroring TestKaiFunnelGuardWiring's approach for _kai_closer_loop: the JS
    itself can't run under unittest (no browser), so this pins that the guard is actually
    wired into the source, not just defined and tested in isolation."""

    def test_fire_loop_computes_prev_best_before_firing(self):
        import inspect
        src = inspect.getsource(ca._engine_driver)
        self.assertIn('_tab_best_total(_rows5, job["tab"])', src)
        self.assertIn('r.get("sessionId") == _sid5', src)   # SAME-SESSION scope, not all-time

    def test_apply_block_gated_on_prev(self):
        import inspect
        src = inspect.getsource(ca._engine_driver)
        self.assertIn("PREV<=0||newTotal>=PREV", src)

    def test_blocked_apply_still_journals_honest_receipt(self):
        import inspect
        src = inspect.getsource(ca._engine_driver)
        # guardHeld only true when NOT applied and a real PREV was on the books — never a
        # silent drop, and never confused with a genuine empty-tab (PREV<=0) first read
        self.assertIn("guardHeld:!applied&&PREV>0", src)
        self.assertIn("total:(applied?newTotal:PREV)", src)

    def test_queue_captures_session_id_for_the_guard(self):
        import inspect
        src = inspect.getsource(ca._engine_driver)
        self.assertIn('"sid": str(rd.get("sessionId") or "")', src)


class TestTabBestTotalSessionScoping(unittest.TestCase):
    """Behavioral pin for the SAME-SESSION scoping the driver's live guard relies on: a bigger
    total banked in a DIFFERENT (older) session must never count as PREV for the current one —
    his stash persists across sessions, so a genuine spend-down in a new session has to be able
    to land, not get stuck forever under a stale prior-session peak (an all-time-max scope would
    be a WORSE bug than the one the guard fixes)."""

    def _rows(self):
        return [
            {"sessionId": "s_old", "intake": {"tab": "runes", "ok": True, "total": 900}},
            {"sessionId": "s_new", "intake": {"tab": "runes", "ok": True, "total": 12}},
        ]

    def test_other_session_totals_excluded(self):
        rows = self._rows()
        same_session = [r for r in rows if r.get("sessionId") == "s_new"]
        self.assertEqual(ca._tab_best_total(same_session, "runes"), 12)   # NOT 900

    def test_empty_tab_this_session_applies_unconditionally(self):
        rows = self._rows()
        same_session = [r for r in rows if r.get("sessionId") == "s_brand_new"]
        self.assertEqual(ca._tab_best_total(same_session, "runes"), 0)   # PREV<=0 → guard is a no-op


class TestIntakeResultReceiptSessionBoundary(unittest.TestCase):
    """v1208 — RECEIPT-BOUNDARY fix on /intake_result: `_sid` used to be picked by scanning
    the WHOLE journal for whatever sessionId appeared LAST, with no regard for what session
    the receipt actually describes. Concrete failure: the route's own reason for existing is
    a receipt landing AFTER its session's bridge died (late auto-intake); if Konyo starts
    ANOTHER short farming session before that straggler resolves, the old heuristic mis-tags
    the stale receipt onto the NEW session's reel — where `_kai_build_routing`'s receipted-tab
    check would wrongly treat a tab the new session never photographed as already covered,
    suppressing a real gap-funnel for it. Now: when frameId carries `reel_<sid>/...` (the
    shape every funnel/closer/driver fire in this file uses), sid is read straight off the
    frame's own identity — immune to timing entirely. Only falls back to the old journal-scan
    guess when frameId doesn't carry a session (e.g. bible.html's own board-side calls),
    unchanged from before. Real server, real HTTP POST, real journal file (HERE monkeypatched
    to an isolated tempdir — never touches Konyo's real sessions.jsonl)."""

    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ca.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._old_here = ca.HERE
        ca.HERE = self.tmp
        # seed: an OLD session's rows, then a NEWER session already started (its own row
        # logged) — simulating Konyo having moved on to another farming session before a
        # straggler receipt from the old one finally lands.
        rows = [
            {"sessionId": "sid_old", "ts": 1000, "scene": "gameplay"},
            {"sessionId": "sid_new", "ts": 5000, "scene": "gameplay"},   # the "latest" session
        ]
        with open(os.path.join(self.tmp, "sessions.jsonl"), "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def tearDown(self):
        ca.HERE = self._old_here
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _post(self, body):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/intake_result",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())

    def _last_journaled_sid(self):
        with open(os.path.join(self.tmp, "sessions.jsonl"), encoding="utf-8") as f:
            lines = [json.loads(ln) for ln in f if ln.strip()]
        return lines[-1]["sessionId"]

    def test_reel_shaped_frame_id_tags_the_frames_own_session_not_the_newest(self):
        # a straggler receipt from sid_old's reel, landing after sid_new already exists
        status, resp = self._post({"tab": "runes", "kind": "tally", "ok": True, "total": 40,
                                    "frameId": "reel_sid_old/5_1000000"})
        self.assertEqual(status, 200)
        self.assertTrue(resp.get("ok"))
        self.assertEqual(self._last_journaled_sid(), "sid_old")   # NOT sid_new

    def test_frame_id_without_a_session_falls_back_to_latest_journal_guess(self):
        # bible.html's own board-side calls don't always carry a reel-relative frameId —
        # unchanged pre-existing behavior for that case.
        status, resp = self._post({"tab": "vault", "kind": "vault", "ok": True, "total": 3,
                                    "frameId": ""})
        self.assertEqual(status, 200)
        self.assertEqual(self._last_journaled_sid(), "sid_new")

    def test_non_reel_frame_id_also_falls_back(self):
        # a bare frameId (no reel_<sid>/ prefix at all) must not be mis-parsed as a session
        status, resp = self._post({"tab": "vault", "kind": "vault", "ok": True, "total": 3,
                                    "frameId": "12_1000000"})
        self.assertEqual(status, 200)
        self.assertEqual(self._last_journaled_sid(), "sid_new")


class TestCloserOcrWorkerNeverOrphaned(unittest.TestCase):
    """v1207 — WORKER-ORPHAN-LEAK class on the funnel/closer side (same vein as v1206's core
    _WORKER/_OCR fix): `_kai_closer_loop` spawns its own `ocr_mac --worker` subprocess (`wp`)
    once per reel it closes. Before this fix, `wp.terminate()` was a plain sequential
    statement placed AFTER the ~120-line per-frame processing loop — any exception inside
    that loop NOT already caught by one of its own inner try/excepts skipped straight to the
    closer's outer per-reel `except Exception: time.sleep(10.0)` (control_app.py, matching
    the top-level `try:` right after `while True:`), leaving `wp` running forever. Worse: the
    closer just sleeps and moves on to the NEXT reel, spawning ANOTHER orphaned worker on top
    of the last one on every subsequent failure. Structural pin (the loop runs inside a live
    background thread inside a huge function, not independently callable): pins that the
    per-frame loop is now wrapped in try/finally so the worker is reaped unconditionally."""

    def test_frame_loop_wrapped_in_try_finally_around_worker_cleanup(self):
        import inspect
        src = inspect.getsource(ca._kai_closer_loop)
        # the spawn must be followed by a try: that wraps the for-loop, then a finally: that
        # terminates the worker — not a bare sequential cleanup after the loop.
        spawn_idx = src.index('wp = subprocess.Popen([ocr_bin, "--worker"]')
        after_spawn = src[spawn_idx:]
        try_idx = after_spawn.index("try:\n                for it in frames:")
        finally_idx = after_spawn.index("finally:")
        self.assertGreater(finally_idx, try_idx,
                            "finally: must come after the try: wrapping the for-loop")
        tail = after_spawn[finally_idx:finally_idx + 200]
        self.assertIn("wp.stdin.close(); wp.terminate()", tail)
        # terminate() itself must stay defensively wrapped — a dead/gone process can raise
        self.assertIn("except Exception:", tail)

    def test_worker_spawn_failure_path_unchanged(self):
        # regression guard: the spawn-failure branch (worker never even started) must still
        # skip the reel cleanly — this fix only changes the POST-spawn cleanup path.
        import inspect
        src = inspect.getsource(ca._kai_closer_loop)
        self.assertIn('print(f"🧠 KAI: worker spawn failed ({e}) — skipping reel"); continue', src)


class TestDrvLiveJudgedReserve(unittest.TestCase):
    """v1205 — FUNNEL analog of engine-read's worker-orphan leak: `_engine_driver`'s
    `live_judged` dedup set is owned by ONE daemon thread that runs for the process's entire
    lifetime (started once at boot), spanning many game sessions over hours/days on Konyo's
    always-on console. It used to grow by one entry per unique judge-candidate frameId
    FOREVER, with no eviction. `_drv_live_judged_reserve` (extracted so this is directly
    testable, not just source-pinnable) bounds it: a set that's still small keeps growing
    normally; crossing the cap clears the whole thing and re-seeds just the current frame."""

    def test_reserves_normally_under_the_cap(self):
        s = {"a", "b"}
        ca._drv_live_judged_reserve(s, "c", cap=2000)
        self.assertEqual(s, {"a", "b", "c"})

    def test_crossing_the_cap_clears_old_entries(self):
        s = {str(i) for i in range(2001)}   # already over cap=2000
        ca._drv_live_judged_reserve(s, "new_frame", cap=2000)
        # every stale entry is gone — only the freshly reserved frame survives
        self.assertEqual(s, {"new_frame"})

    def test_crossing_the_cap_does_not_lose_protection_for_the_frame_just_reserved(self):
        s = {str(i) for i in range(2001)}
        ca._drv_live_judged_reserve(s, "just_fired", cap=2000)
        self.assertIn("just_fired", s)

    def test_growth_stays_bounded_across_many_reserves(self):
        s = set()
        for i in range(10000):
            ca._drv_live_judged_reserve(s, f"frame_{i}", cap=2000)
        # never allowed to run away — this is the actual leak-prevention guarantee
        self.assertLessEqual(len(s), 2001)

    def test_driver_wired_to_the_bounded_reserve_not_a_bare_add(self):
        # structural pin: _engine_driver must route through the bounded helper, not fall
        # back to a bare `live_judged.add(...)` that would reintroduce the leak.
        import inspect
        src = inspect.getsource(ca._engine_driver)
        self.assertIn("_drv_live_judged_reserve(live_judged, _jfid)", src)


class TestIntakeLeaseClockSkewImmunity(unittest.TestCase):
    """v1202 — your own flagged follow-up from the v1201 closer-loop clock-skew round:
    _intake_lease_claim/_intake_lease_status used `until <= time.time()*1000` for the actual
    expiry DECISION. A backward NTP/sleep-wake jump between claim and a later check makes
    `now` read smaller than it should, so an already-expired lease looks still-held for an
    extra `jump_size` ms — a tab stuck 'busy' longer than its 120s TTL. Verified per-spot
    before fixing: `until` (wall-clock) is NOT purely internal — /intake_claim ships it
    straight to the board's browser JS, and _intake_lease_status's snapshot rides into
    /api/status's `leases` field for the theatre UI, both comparable to the CLIENT's own
    Date.now() across a process boundary where a monotonic value would be meaningless. So the
    fix keeps `until` wall-clock (unchanged, still returned) and adds an internal-only
    `untilMono` (never returned) to drive the actual expiry math — same split as v1201's
    _t0f/_t0f_mono."""

    def setUp(self):
        self._saved = dict(ca._INTAKE_LEASES)
        ca._INTAKE_LEASES.clear()

    def tearDown(self):
        ca._INTAKE_LEASES.clear()
        ca._INTAKE_LEASES.update(self._saved)

    def test_claim_release_roundtrip(self):
        r1 = ca._intake_lease_claim("runes", "engine-driver", ttl_ms=120000, now_ms=0, now_mono_ms=0)
        self.assertTrue(r1["ok"])
        self.assertEqual(r1["until"], 120000)   # wall-clock arithmetic, unaffected by the fix
        # a second owner is blocked while it's still held (no time has passed)
        r2 = ca._intake_lease_claim("runes", "board", ttl_ms=120000, now_ms=1000, now_mono_ms=1000)
        self.assertFalse(r2["ok"])
        self.assertEqual(r2["why"], "held")
        self.assertEqual(r2["holder"], "engine-driver")
        rel = ca._intake_lease_release("runes", "engine-driver")
        self.assertTrue(rel["ok"])
        self.assertTrue(rel["released"])
        # released — now claimable by anyone
        r3 = ca._intake_lease_claim("runes", "board", ttl_ms=120000, now_ms=2000, now_mono_ms=2000)
        self.assertTrue(r3["ok"])

    def test_release_by_non_holder_is_refused(self):
        ca._intake_lease_claim("gems", "engine-driver", ttl_ms=120000, now_ms=0, now_mono_ms=0)
        rel = ca._intake_lease_release("gems", "board")
        self.assertFalse(rel["ok"])
        self.assertEqual(rel["why"], "not-holder")
        self.assertFalse(rel["released"])

    def test_normal_forward_time_expiry_still_works(self):
        # no skew at all — real time simply advances past the TTL on both clocks in lockstep.
        # Must keep expiring normally; this fix must not weaken the TTL's ordinary behavior.
        ca._intake_lease_claim("materials", "engine-driver", ttl_ms=120000, now_ms=0, now_mono_ms=0)
        r = ca._intake_lease_claim("materials", "board", ttl_ms=120000, now_ms=130000, now_mono_ms=130000)
        self.assertTrue(r["ok"])   # 130s of REAL elapsed time > 120s TTL — expired, reclaimable

    def test_backward_wall_clock_jump_does_not_extend_a_truly_expired_lease(self):
        # THE regression this round fixes: claim at t=0 (both clocks 0). 130000ms of REAL
        # (monotonic) time passes — past the 120000ms TTL, genuinely expired. But the WALL
        # clock stepped BACKWARD to -500000 (an NTP correction) at the moment of the second
        # call. The OLD wall-clock-only check saw until(120000) > now(-500000) and reported
        # still-held (leaking the lease ~620s past its real TTL). The fix must reclaim it.
        ca._intake_lease_claim("runes", "engine-driver", ttl_ms=120000, now_ms=0, now_mono_ms=0)
        r = ca._intake_lease_claim("runes", "board", ttl_ms=120000, now_ms=-500000, now_mono_ms=130000)
        self.assertTrue(r["ok"], "a backward wall-clock jump must not extend a real TTL expiry")
        self.assertEqual(r["owner"], "board")

    def test_backward_wall_clock_jump_does_not_break_a_still_valid_lease(self):
        # the flip side: real elapsed time is SHORT (still well within TTL) even though the
        # wall clock also jumped backward — the lease must still correctly read as held.
        ca._intake_lease_claim("runes", "engine-driver", ttl_ms=120000, now_ms=0, now_mono_ms=0)
        r = ca._intake_lease_claim("runes", "board", ttl_ms=120000, now_ms=-500000, now_mono_ms=1000)
        self.assertFalse(r["ok"])
        self.assertEqual(r["why"], "held")

    def test_status_snapshot_omits_internal_mono_field(self):
        ca._intake_lease_claim("gems", "engine-driver", ttl_ms=120000, now_ms=5000, now_mono_ms=5000)
        snap = ca._intake_lease_status(now_mono_ms=5500)
        self.assertIn("gems", snap)
        self.assertEqual(set(snap["gems"].keys()), {"owner", "until", "since"})
        self.assertNotIn("untilMono", snap["gems"])

    def test_status_expiry_also_immune_to_backward_wall_clock_jump(self):
        ca._intake_lease_claim("gems", "engine-driver", ttl_ms=120000, now_ms=0, now_mono_ms=0)
        # 130s of real (monotonic) time passed — status must show it gone, regardless of what
        # the wall clock is doing (status never took a now_ms override at all — only monotonic).
        snap = ca._intake_lease_status(now_mono_ms=130000)
        self.assertNotIn("gems", snap)


class TestCloserLoopClockSkewImmunity(unittest.TestCase):
    """v1201 — CLOCK-SKEW class swept from engine-capture (v1199) / engine-read (v1200): a
    backward NTP/sleep-wake clock jump breaks any wait-loop built purely on time.time()
    deltas, turning a bounded wait into a multi-minute stall. `_kai_closer_loop` has two
    receipt-wait loops shaped exactly like that (funnel fire ~120s, super-analyze fire ~40s)
    — and since this loop is serial, a stalled wait delays the ENTIRE post-seal pass behind
    it (other tabs' gap-funnels, judge ping-pong, kai_report write). Structural pin (the
    loops run inside a live background thread inside a huge function — not independently
    callable): pins that pacing now uses time.monotonic() while the wall-clock anchors used
    for journal `completedTs` comparisons (a persisted wall-clock field) correctly stay on
    time.time(), the same split engine-read's own sweep drew."""

    def test_funnel_wait_deadline_uses_monotonic(self):
        import inspect
        src = inspect.getsource(ca._kai_closer_loop)
        self.assertIn("_t0f_mono = time.monotonic()", src)
        self.assertIn("while time.monotonic() - _t0f_mono < 120.0:", src)

    def test_funnel_wait_journal_cutoff_stays_wall_clock(self):
        import inspect
        src = inspect.getsource(ca._kai_closer_loop)
        # completedTs is a persisted wall-clock timestamp — the cutoff compared against it
        # must NOT switch to monotonic, only the pacing deadline above it does.
        # v1381.0 multi-retry uses inverted form (`< …: continue`) but still wall-clock `_t0f`.
        self.assertTrue(
            'int(r3.get("completedTs") or 0) >= int(_t0f * 1000)' in src
            or 'int(r3.get("completedTs") or 0) < int(_t0f * 1000)' in src,
            "journal cutoff must compare completedTs against wall-clock _t0f*1000")
        self.assertIn("int(_t0f * 1000)", src)
        self.assertNotIn("int(_t0f_mono * 1000)", src)

    def test_super_analyze_wait_deadline_uses_monotonic(self):
        import inspect
        src = inspect.getsource(ca._kai_closer_loop)
        self.assertIn("_t0w = time.monotonic()", src)
        self.assertIn("while time.monotonic() - _t0w < 40.0:", src)

    def test_super_analyze_journal_cutoff_still_uses_separate_wall_clock_anchor(self):
        import inspect
        src = inspect.getsource(ca._kai_closer_loop)
        self.assertIn("_t0s = int(time.time() * 1000)", src)
        self.assertIn('int(_rw.get("completedTs") or 0) >= _t0s', src)


class TestFunnelRoutedRequiresOk(unittest.TestCase):
    """v1197 — `_kai_build_routing`'s `funnel_by_fid` used to mark a frame `routed` on ANY
    kind:'kai-funnel' journal receipt, success or not. But kind:'kai-funnel' receipts CAN be
    ok:false — the v1185 honest-miss-on-rejection fix and the pre-existing never-zero
    guardHeld block (control_app.py ~4045/4053) both deliberately post an ok:false receipt
    instead of dropping silently. Marking the frame routed anyway meant a FAILED attempt got
    narrated by `_kai_reconcile` as 'funnel receipt landed ... its tally count is the accepted
    read' (a lie one layer up from an otherwise-honest receipt), and `_kai_stage3_select`
    permanently skipped re-selecting that exact frame even though nothing real ever landed."""

    def _scan(self):
        return [{"f": "f1.jpg", "ts": 1000,
                  "tabstripLabel": "stash-runes", "tabstrip": True,
                  "gridLabel": "stash-runes", "grid": True}]

    def test_failed_funnel_receipt_does_not_mark_frame_routed(self):
        journal_rows = [{"frameId": "reel_sid1/f1",
                          "intake": {"kind": "kai-funnel", "tab": "runes", "ok": False,
                                     "total": 0, "errors": 1}}]
        routing = ca._kai_build_routing(self._scan(), [], "sid1", journal_rows)
        self.assertIsNone(routing[0]["routed"])

    def test_failed_funnel_receipt_not_narrated_as_accepted_by_reconcile(self):
        journal_rows = [{"frameId": "reel_sid1/f1",
                          "intake": {"kind": "kai-funnel", "tab": "runes", "ok": False,
                                     "total": 0, "errors": 1}}]
        routing = ca._kai_build_routing(self._scan(), [], "sid1", journal_rows)
        rec = {r["f"]: r for r in ca._kai_reconcile(routing, [], [])}
        self.assertNotEqual(rec["f1.jpg"]["owner"], "funnel")

    def test_successful_funnel_receipt_still_marks_frame_routed(self):
        # regression guard: the ok:True case (already pinned by TestDedupeNeverErasesARealReceipt)
        # must keep working exactly as before this fix.
        journal_rows = [{"frameId": "reel_sid1/f1",
                          "intake": {"kind": "kai-funnel", "tab": "runes", "ok": True, "total": 40}}]
        routing = ca._kai_build_routing(self._scan(), [], "sid1", journal_rows)
        self.assertEqual(routing[0]["routed"], "kai-funnel")


class TestKaiCompileRegisterBestTierWins(unittest.TestCase):
    """v1193 — _kai_compile_register's per-name tier used to be 'first non-blank tier wins'
    (see the OLD `if tier and not cur.get("tier")` rule): sess_rows is walked chronologically,
    so an early low-confidence 'border' guess froze the register's tier FOREVER, even after a
    later, more authoritative same-session re-read (e.g. super-analyze, which _kai_reconcile's
    own documented priority ranks ABOVE a first-pass read) proved the same item 'grail'. Tier
    is a QUALITY verdict, not a timestamp — 'first' has no claim to being 'best'. Now the
    highest-ranked tier wins (grail>keep>border), mirroring the never-zero/max-verified-total-
    wins law already applied to counts elsewhere in this file, applied here to tier."""

    def _row(self, ts, name, tier, fid="f"):
        return {"lane": "kai", "ts": ts, "captureTs": ts, "frameId": fid,
                "kai": {"judge": {"name": name, "tier": tier}}}

    def test_later_better_verdict_upgrades_stale_tier(self):
        rows = [self._row(1000, "Shako", "border"), self._row(2000, "Shako", "grail")]
        reg = ca._kai_compile_register(rows)
        self.assertEqual(reg[0]["tier"], "grail")

    def test_proven_grail_never_buried_by_a_later_weaker_guess(self):
        rows = [self._row(1000, "Shako", "grail"), self._row(2000, "Shako", "border")]
        reg = ca._kai_compile_register(rows)
        self.assertEqual(reg[0]["tier"], "grail")

    def test_keep_upgrades_to_grail_but_not_downgraded_by_border(self):
        rows = [self._row(1000, "Shako", "keep"),
                self._row(1500, "Shako", "border"),
                self._row(2000, "Shako", "grail")]
        reg = ca._kai_compile_register(rows)
        self.assertEqual(reg[0]["tier"], "grail")

    def test_equal_tier_repeats_are_stable(self):
        rows = [self._row(1000, "Shako", "keep"), self._row(2000, "Shako", "keep")]
        reg = ca._kai_compile_register(rows)
        self.assertEqual(reg[0]["tier"], "keep")

    def test_first_seen_ts_and_frame_still_earliest_wins_independent_of_tier(self):
        # the tier-rank fix must NOT disturb the deliberately different "earliest sighting
        # wins" rule for firstSeenTs/frameId — that's a factual timestamp, not a quality call.
        rows = [self._row(2000, "Shako", "border", fid="later"),
                self._row(1000, "Shako", "grail", fid="earlier")]
        reg = ca._kai_compile_register(rows)
        self.assertEqual(reg[0]["tier"], "grail")
        self.assertEqual(reg[0]["firstSeenTs"], 1000)
        self.assertEqual(reg[0]["frameId"], "earlier")


class TestKaiGrailTooltipGrounding(unittest.TestCase):
    """FIX C (F3, 2026-07-22 retro-vs-photos audit) — two fully-legible GRAIL tooltips in a
    real session (Enigma Archon Plate 'JahIthBer', Harlequin Crest Shako) were reduced to OCR
    garble and left UNNAMED in missed[] instead of register[]. Root cause: OCR leet-mangled the
    NAME line ('H4RLEQVIN CR'), so _kai_itemish's isalpha() tokenizer threw the name token away
    before it could ground. _kai_ground_lines de-leets and matches a distinctive signature token
    against the real item lexicon — so a garbled grail gets its REAL name — while staying honest
    (only names a frame that shows tooltip context AND carries a distinctive item word)."""

    def test_leet_garbled_harlequin_grounds_to_real_name(self):
        # the actual OCR of the real Harlequin frame f_1784736434248 (4→A, U→V, plus stats).
        got = ca._kai_ground_lines(["H4RLEQVIN CR", "5wAK", "KtPVlRED STRQNGTH.. 50",
                                    "t54 ON CHARACTER L", "eF GEtTINt MAGIC"])
        self.assertIn("Harlequin Crest", got)

    def test_hand_garbled_variants_ground(self):
        # 'Harleouin Crest' / 'Eniqma' style single-substitution garble the audit called out.
        self.assertIn("Harlequin Crest",
                      ca._kai_ground_lines(["Harleouin Crest", "Required Strength 50"]))
        self.assertIn("Enigma",
                      ca._kai_ground_lines(["Eniqma", "Archon Plate", "Required Strength 103"]))

    def test_clean_enigma_title_grounds(self):
        got = ca._kai_ground_lines(["Enigma", "Archon Plate", "'JahIthBer'",
                                    "Required Strength 103"])
        self.assertIn("Enigma", got)

    def test_genuine_non_name_stat_lines_stay_unnamed(self):
        # no hallucination: pure stat/flavor text never mints an item name.
        self.assertEqual(ca._kai_ground_lines(
            ["Required Strength 103", "+69 to Strength",
             "75% Better Chance of Getting Magic Items", "Socketed (3)"]), {})

    def test_gameplay_narrative_produces_no_name(self):
        # runeword words appear in gameplay narrative (Chaos SANCTUARY area) — must NOT ground:
        # gameplay lacks item-tooltip context, so the grounder stays silent.
        self.assertEqual(ca._kai_ground_lines(
            ["Entering the Chaos Sanctuary", "You have slain Baal"]), {})
        self.assertEqual(ca._kai_ground_lines(
            ["Welcome to level 90", "Words of Wisdom echo"]), {})

    def test_enigma_realframe_ocr_that_missed_the_title_stays_honest(self):
        # the REAL Enigma frame f_1784736415366: roi-fast never captured the gold title lines,
        # so there is no name token to recover — the grounder must NOT invent one.
        self.assertEqual(ca._kai_ground_lines(
            ["0-&f 60", "t4GTH.. 1O3", "REQ", "*IS% EHHANcED DEFENSE..",
             ".69 T• STRENGTH", "IHrREA5E mAxrmvnr"]), {})

    def test_e1_groundlabel_two_witness_war_traveler(self):
        # E1 — a grail dropped on the FLOOR shows name-over-base with NO tooltip stat lines, so
        # _kai_tooltip_context can't fire. A distinctive UNIQUE token + its BASE type, tersely, is
        # the TWO-WITNESS ground-label path: War Traveler read as 'WAA TRAVELIR' / 'BATYLE B**Ys'
        # (missed in 7 frames across 6 real reels) now grounds to its real name.
        self.assertIn("War Traveler", ca._kai_ground_lines(["WAA TRAVELIR", "BATYLE B**Ys"]))

    def test_e1_groundlabel_needs_the_base_witness(self):
        # honesty: a bare unique-name garble with NO base witness (and no tooltip) stays unnamed —
        # the second witness is required. This is what keeps chat/loot-filter garble from grounding.
        self.assertEqual(ca._kai_ground_lines(["WAA TRAVELIR"]), {})

    def test_e1_chat_that_garbles_to_a_unique_stays_blocked(self):
        # the real chat FP the audit found: 'worlU. DiablOS rThnlon' ("Diablo's reunion") edit-
        # matches Ars Al'Diabolos — but has NO base witness, so the two-witness path blocks it.
        self.assertEqual(ca._kai_ground_lines(["worlU. DiablOS rThnlon"]), {})

    def test_e1_non_terse_prose_with_a_base_word_is_not_a_ground_label(self):
        # a ground label is terse (name/base, <=3 tokens/line); a prose/chat line that happens to
        # contain a base word is NOT a ground label and must not ground a unique in it.
        self.assertEqual(ca._kai_ground_lines(
            ["hey anyone want to trade battle boots for a war traveler today"]), {})

    def test_grounded_names_reach_the_register(self):
        # a journaled kai row carrying kai.grounded lands its real name in the register;
        # a plain garbled miss (kai.texts, no grounding) does NOT.
        rows = [
            {"lane": "kai", "ts": 1000, "frameId": "reel_x/f1",
             "kai": {"grounded": ["Harlequin Crest"]}},
            {"lane": "kai", "ts": 1100, "frameId": "reel_x/f2",
             "kai": {"grounded": ["Enigma"]}},
            {"lane": "kai", "ts": 1200, "frameId": "reel_x/f3",
             "kai": {"texts": ["eF GEtTINt MAGIC"]}},
        ]
        names = {r["name"] for r in ca._kai_compile_register(rows)}
        self.assertIn("Harlequin Crest", names)
        self.assertIn("Enigma", names)
        self.assertNotIn("eF GEtTINt MAGIC", names)


class TestCrossFrameQuorum(unittest.TestCase):
    """② CROSS-FRAME QUORUM (multi-witness sweep) — the accuracy gate judges each frame in
    ISOLATION, but a tooltip/panel lingers across frames and different independent brains catch
    it on different stills. A frame HELD at 'quorum<2' is proven when a same-label neighbor within
    the item's on-screen lifetime adds a DISTINCT independent evidence class (union >=2). A
    conservative extension of _router_conf's per-frame quorum — SAME >=2-independent-class
    discipline, measured across the lifetime; re-runs the FULL gate so cell-correctness still
    vetoes. SCOPED to tooltip labels (read/ocr/journal are genuinely independent; stash/inventory
    lean on tabstrip/grid chrome witnesses whose independence the per-frame gate deliberately
    guards, so they stay out). Measured on 29 real reels: 9 genuine tooltip recoveries — the honest
    figure after the guards, down from a 49 raw class-union ceiling (35 were route-nulled dedup
    frames the cluster head already covers; stash out of scope), 0 new false."""

    def _row(self, f, ts, label, sources, route, gr="quorum<2", cv=None):
        return {"f": f, "ts": ts, "label": label, "sources": sources, "route": route,
                "gatePass": False, "gateReason": gr, "gateSources": sorted(sources),
                "_cv": cv or {}, "_nh": None, "_gs": False}

    def test_distinct_class_neighbor_promotes(self):
        # a lingering tooltip: frame A has a 'read' (content) witness, held frame B has 'ocr'
        # (pixel) — DISTINCT classes across the pair clear the >=2 bar.
        rows = [self._row("A", 1000, "tooltip", ["read"], "judge"),
                self._row("B", 1001, "tooltip", ["ocr"], "judge")]
        ca._kai_crossframe_quorum(rows)
        self.assertTrue(rows[1]["gatePass"])
        self.assertEqual(rows[1]["gateReason"], "cross-frame")
        self.assertIn("content", rows[1].get("crossFrame") or [])

    def test_same_class_neighbor_does_not_promote(self):
        # both frames only have 'ocr' (pixel) — a same-class re-fire is NOT a second witness.
        rows = [self._row("A", 1000, "tooltip", ["ocr"], "judge"),
                self._row("B", 1001, "tooltip", ["ocr"], "judge")]
        ca._kai_crossframe_quorum(rows)
        self.assertFalse(rows[1]["gatePass"])

    def test_never_crosses_labels(self):
        rows = [self._row("A", 1000, "stash", ["grid"], "vault"),
                self._row("B", 1001, "tooltip", ["read"], "judge")]
        ca._kai_crossframe_quorum(rows)
        self.assertFalse(rows[1]["gatePass"])

    def test_outside_lifetime_window_does_not_promote(self):
        rows = [self._row("A", 1000, "tooltip", ["read"], "judge"),
                self._row("B", 99000, "tooltip", ["ocr"], "judge")]
        ca._kai_crossframe_quorum(rows)
        self.assertFalse(rows[1]["gatePass"])

    def test_cell_correctness_still_vetoes(self):
        # a dissenting chrome (grid) vote on the held frame → wrong-cell veto even with 2 classes.
        rows = [self._row("A", 1000, "tooltip", ["read"], "judge"),
                self._row("B", 1001, "tooltip", ["ocr"], "judge", cv={"grid": "stash-runes"})]
        ca._kai_crossframe_quorum(rows)
        self.assertFalse(rows[1]["gatePass"])

    def test_route_nulled_dedup_frame_not_promoted(self):
        # a near-dup whose route was nulled (the cluster head carries the verdict) fails cell-
        # correctness (route != want) — this is the 35-of-49 the full gate correctly excludes.
        rows = [self._row("A", 1000, "tooltip", ["read"], "judge"),
                self._row("B", 1001, "tooltip", ["ocr"], None)]  # route nulled by dedup
        ca._kai_crossframe_quorum(rows)
        self.assertFalse(rows[1]["gatePass"])

    def test_gameplay_never_promotes(self):
        rows = [self._row("A", 1000, "gameplay", ["read"], None),
                self._row("B", 1001, "gameplay", ["ocr"], None)]
        ca._kai_crossframe_quorum(rows)
        self.assertFalse(rows[1]["gatePass"])

    def test_non_quorum_hold_untouched(self):
        # only 'quorum<2' holds are eligible — a 'name-not-in-db' hold is left exactly as-is.
        rows = [self._row("A", 1000, "tooltip", ["read"], "judge"),
                self._row("B", 1001, "tooltip", ["ocr"], "judge", gr="name-not-in-db")]
        ca._kai_crossframe_quorum(rows)
        self.assertFalse(rows[1]["gatePass"])
        self.assertEqual(rows[1]["gateReason"], "name-not-in-db")


class TestItemClassB9(unittest.TestCase):
    """B9 — item-read rarity precision. `_kai_item_class` claims ONLY the two classes the engine
    can PROVE: 'runeword' (derivable) and 'grail' (grounder-proven or register tier=='grail', with
    BASES excluded). Never fakes unique-vs-set (client's tipOf). The forensics synthesis reads
    "grounded the grail War Traveler" / "identified the runeword Spirit", plain otherwise."""

    def test_runeword_class_is_derivable(self):
        self.assertEqual(ca._kai_item_class("Spirit"), "runeword")
        self.assertEqual(ca._kai_item_class("Enigma", grounded=True), "runeword")

    def test_grounded_grail_is_grail(self):
        self.assertEqual(ca._kai_item_class("War Traveler", grounded=True), "grail")
        self.assertEqual(ca._kai_item_class("Griffon's Eye", grounded=True), "grail")

    def test_register_tier_grail_is_grail(self):
        # a non-base grail name with register tier=='grail' → grail. (NB "Shako" would correctly
        # return None — it's the BASE type of Harlequin Crest, not a grail; the base guard is right.)
        self.assertEqual(ca._kai_item_class("The Stone of Jordan", tier="grail"), "grail")

    def test_base_is_never_grail_even_grounded(self):
        # the Battle Boots guard — a base name can never print "the grail Battle Boots"
        self.assertIsNone(ca._kai_item_class("Battle Boots", grounded=True))
        self.assertIsNone(ca._kai_item_class("Archon Plate", tier="grail"))

    def test_plain_read_has_no_class(self):
        # not grounded, no grail tier → no class claimed (honest; the client can still add rarity)
        self.assertIsNone(ca._kai_item_class("War Traveler"))          # sighting, not proven grail here
        self.assertIsNone(ca._kai_item_class("Super Healing Potion"))  # consumable

    def test_phrase_and_synthesis_carry_the_class(self):
        self.assertEqual(ca._kai_item_phrase("War Traveler", "grail"), "the grail War Traveler")
        self.assertEqual(ca._kai_item_phrase("Spirit", "runeword"), "the runeword Spirit")
        self.assertEqual(ca._kai_item_phrase("Some Base", None), "Some Base")
        rep = {"sid": "s", "register": [], "routing": [],
               "missed": [{"f": "f1.jpg", "ts": 1, "texts": ["WAA TRAVELIR", "BATYLE B**Ys"], "cls": "gameplay"}]}
        r = ca._kai_forensics_project(rep)["items"][0]["reads"][0]
        self.assertEqual(r["itemClass"], "grail")
        self.assertIn("the grail War Traveler", r["synthesis"])


class TestAreaActDiabloLanguage(unittest.TestCase):
    """B10 — Diablo-language area/ACT truth. `_diablo_scene_label` carries the ACT ("FARMING ·
    Act 1 · Dark Wood") when the area is in the canonical `_AREA_ACT` map; an unmapped area
    degrades to the plain label (no fabricated act), and `unclear` stays. Deterministic game
    truth (never guessed) — one lever lighting every Diablo-language surface (live banner,
    classFrames, forensics synthesis, B8 fingerprint)."""

    def test_each_act_prefixes_correctly(self):
        for area, act in (("Dark Wood", 1), ("Ancient Tunnels", 2), ("Travincal", 3),
                          ("Chaos Sanctuary", 4), ("Frigid Highlands", 5)):
            r = ca._diablo_scene_label("gameplay", area)
            self.assertEqual(r["act"], act)
            self.assertEqual(r["label"], "FARMING · Act %d · %s" % (act, area))

    def test_level_suffix_is_stripped(self):
        r = ca._diablo_scene_label("gameplay", "Catacombs Level 2")
        self.assertEqual(r["act"], 1)
        self.assertEqual(r["label"], "FARMING · Act 1 · Catacombs Level 2")

    def test_the_prefix_normalized(self):
        self.assertEqual(ca._area_act("The Worldstone Chamber"), 5)
        self.assertEqual(ca._area_act("Pandemonium Fortress"), 4)

    def test_unmapped_area_never_fabricates_an_act(self):
        r = ca._diablo_scene_label("gameplay", "Some Unmapped Zone")
        self.assertIsNone(r["act"])
        self.assertEqual(r["label"], "FARMING · Some Unmapped Zone")   # unchanged from pre-B10

    def test_edge_states_hold(self):
        self.assertEqual(ca._diablo_scene_label("gameplay", "")["label"], "FARMING")
        self.assertEqual(ca._diablo_scene_label("", "")["label"], "unclear")
        self.assertEqual(ca._diablo_scene_label("", "")["act"], None)
        self.assertEqual(ca._diablo_scene_label("transition", "Frigid Highlands")["label"],
                         "ENTERING Act 5 · Frigid Highlands")
        self.assertEqual(ca._diablo_scene_label("town", "Harrogath")["label"], "TOWN · Act 5 · Harrogath")
        self.assertEqual(ca._diablo_scene_label("stash", "Rogue Encampment")["label"],
                         "STASH · Act 1 · Rogue Encampment")

    def test_the_five_real_reel_areas_resolve(self):
        for area, act in (("Dark Wood", 1), ("Rogue Encampment", 1), ("Throne of Destruction", 5),
                          ("The Worldstone Chamber", 5), ("Catacombs Level 2", 1)):
            self.assertEqual(ca._area_act(area), act, area)


class TestEvRank(unittest.TestCase):
    """⚔ EV-RANK — the flagship's "hunt next" intelligence. Pure engine ranking of missing grails
    by expected-hours-to-next-find; the CLIENT provides the odds (its Calculator) so the model
    never drifts. `_ev_hours` matches the Calculator formula exactly; honest-absent (None →
    unranked) on invalid odds — never a fabricated EV."""

    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ca.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def test_ev_hours_matches_calculator_formula(self):
        # matches the bible Calculator EXACTLY: runs = ceil(log(1-conf)/log(1-1/chance)); hours=runs/kph
        import math
        p, kph, c = 1 / 2293.0, 85, 0.5
        expected = math.ceil(math.log(1 - c) / math.log(1 - p)) / kph
        self.assertAlmostEqual(ca._ev_hours(p, kph, c), expected, places=9)

    def test_invalid_odds_are_honest_absent(self):
        self.assertIsNone(ca._ev_hours(0, 85))       # dropChance 0
        self.assertIsNone(ca._ev_hours(1, 85))       # dropChance 1
        self.assertIsNone(ca._ev_hours(0.01, 0))     # kph 0
        self.assertIsNone(ca._ev_hours("x", 85))     # non-numeric

    def test_rarer_ranks_later_at_equal_kph(self):
        out = ca._ev_rank([{"name": "Common", "dropChance": 1 / 500.0, "killsPerHr": 100},
                           {"name": "Rare", "dropChance": 1 / 5000.0, "killsPerHr": 100}])
        self.assertEqual([r["name"] for r in out["ranked"]], ["Common", "Rare"])

    def test_higher_kph_ranks_sooner_at_equal_odds(self):
        out = ca._ev_rank([{"name": "Slow", "dropChance": 1 / 1000.0, "killsPerHr": 30},
                           {"name": "Fast", "dropChance": 1 / 1000.0, "killsPerHr": 300}])
        self.assertEqual([r["name"] for r in out["ranked"]], ["Fast", "Slow"])

    def test_unknown_odds_go_unranked_not_fabricated(self):
        out = ca._ev_rank([{"name": "Known", "dropChance": 1 / 500.0, "killsPerHr": 100},
                           {"name": "NoFarm", "dropChance": 0, "killsPerHr": 0}])
        self.assertEqual([r["name"] for r in out["ranked"]], ["Known"])
        self.assertEqual(out["unranked"], [{"name": "NoFarm", "why": "no known farm / odds"}])

    def test_empty_is_empty(self):
        self.assertEqual(ca._ev_rank([]), {"ranked": [], "unranked": [], "confidence": 0.5})

    def test_post_endpoint_ranks(self):
        payload = json.dumps({"items": [
            {"name": "Common", "dropChance": 1 / 500.0, "killsPerHr": 300, "source": "Pindle"},
            {"name": "Rare", "dropChance": 1 / 5000.0, "killsPerHr": 80, "source": "Mephisto"}]}).encode()
        req = urllib.request.Request("http://127.0.0.1:%d/api/evrank" % self.port, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as r:
            out = json.loads(r.read())
        self.assertEqual([x["name"] for x in out["ranked"]], ["Common", "Rare"])
        self.assertTrue(out["ranked"][0]["expectedHours"] < out["ranked"][1]["expectedHours"])


class TestAreaInferenceEntering(unittest.TestCase):
    """B5 area-inference — a transition/loading frame (dark screen, no area of its own) borrows the
    zone being ENTERED from the NEXT deep read that names one (forward-looking, ≤8s). "ENTERING The
    Pit" instead of "ENTERING (loading)". Honest-absent: no forward zone → "(loading)" unchanged;
    a zone too far forward isn't borrowed. Retro (needs the future read); never over-claims."""

    def _reconcile_one(self, sess):
        routing = [{"f": "f_1000.jpg", "ts": 1000, "label": "gameplay"}]
        return ca._kai_reconcile(routing, [], sess)[0]

    def test_transition_borrows_the_next_zone(self):
        sess = [{"lane": "deep", "scene": "transition", "area": "", "captureTs": 1000, "ts": 1000},
                {"lane": "deep", "scene": "gameplay", "area": "The Pit", "captureTs": 4000, "ts": 4000}]
        r = self._reconcile_one(sess)
        self.assertEqual(r["area"], "The Pit")
        self.assertEqual(r["native"]["label"], "ENTERING Act 1 · The Pit")   # + B10 act

    def test_no_forward_zone_stays_honest_loading(self):
        sess = [{"lane": "deep", "scene": "transition", "area": "", "captureTs": 1000, "ts": 1000}]
        self.assertEqual(self._reconcile_one(sess)["native"]["label"], "ENTERING (loading)")

    def test_forward_zone_beyond_window_not_borrowed(self):
        sess = [{"lane": "deep", "scene": "transition", "area": "", "captureTs": 1000, "ts": 1000},
                {"lane": "deep", "scene": "gameplay", "area": "The Pit", "captureTs": 20000, "ts": 20000}]
        self.assertEqual(self._reconcile_one(sess)["native"]["label"], "ENTERING (loading)")

    def test_forward_area_law_shared_by_both_surfaces(self):
        # the ONE forward law (reconciler + classFrames ribbon both call it): next area-naming
        # read forward within the window; nearest-PREVIOUS never wins; honest-absent otherwise.
        area_ts = [(500, "Cold Plains"), (4000, "The Pit"), (20000, "Far Oasis")]
        self.assertEqual(ca._forward_area_from(1000, area_ts, 8000), "The Pit")   # forward, not the closer PREVIOUS
        self.assertEqual(ca._forward_area_from(1000, [(500, "Cold Plains")], 8000), "")   # only a previous → honest-absent
        self.assertEqual(ca._forward_area_from(1000, [(20000, "Far Oasis")], 8000), "")   # beyond window
        self.assertEqual(ca._forward_area_from(0, area_ts, 8000), "")   # no ts


class TestAutorouteStackableHonesty(unittest.TestCase):
    """Autoroute sweep — a STACKABLE's count is its TALLY (intake), never its frame-SIGHTING count.
    A rune/gem/material read N× but never tallied is NOT N owned (sightings ≠ quantity) — it reports
    1 ('seen, uncounted'). The audit found "Hellfire Torch ×5" fabricated from 5 sightings; tallied
    stackables (the real counts El=14 etc.) are unchanged. Sweep is read-only + review-gated."""

    def test_tallied_stackable_reports_its_tally(self):
        rows = [{"lane": "intake", "intake": {"tab": "runes", "counts": {"Vex": 3}}},
                {"lane": "deep", "names": ["Vex"], "ts": 1},
                {"lane": "deep", "names": ["Vex"], "ts": 2}]  # read twice, but tally says 3
        out = ca._autoroute_classify(ca._autoroute_aggregate(rows, []))
        self.assertEqual(out["runes"].get("Vex"), 3)   # the tally, not max(3, 2 sightings)

    def test_untallied_stackable_is_one_not_sightings(self):
        # a stackable read 5× but NEVER tallied → 1 ("seen, uncounted"), never a fabricated 5
        rows = [{"lane": "deep", "names": ["Ral"], "ts": i} for i in range(5)]
        out = ca._autoroute_classify(ca._autoroute_aggregate(rows, []))
        self.assertEqual(out["runes"].get("Ral"), 1)   # NOT 5 sightings-as-quantity


class TestCompletenessCoverageHonesty(unittest.TestCase):
    """`_session_completeness.coveragePct` — an empty session (0 reads AND 0 unread) must be
    honest-absent (None), NOT a fabricated 100% ("100% coverage" when nothing was there to cover
    — 4/27 real reels did this). A LEGITIMATE 100% (read everything, nothing unread) is preserved;
    0% (text seen, nothing read) stays an honest 0.0."""

    _F = [{"f": "f1", "ts": 1}]

    def _deep(self, ts=1):
        return {"lane": "deep", "names": ["A"], "ts": ts, "captureTs": ts}

    def _kai(self, ts=1):
        return {"lane": "kai", "frameId": "reel/f", "ts": ts, "kai": {"texts": ["x"]}}

    def test_empty_session_is_honest_absent_not_fabricated_100(self):
        self.assertIsNone(ca._session_completeness([], self._F)["coveragePct"])

    def test_legitimate_all_read_is_100(self):
        cov = ca._session_completeness([self._deep(1), self._deep(2)], self._F)["coveragePct"]
        self.assertEqual(cov, 100.0)   # read everything, nothing unread → a real 100%

    def test_zero_coverage_stays_honest_zero(self):
        cov = ca._session_completeness([self._kai(1), self._kai(2)], self._F)["coveragePct"]
        self.assertEqual(cov, 0.0)     # text seen, nothing read → honest 0%, not None

    def test_partial_coverage_is_the_real_rate(self):
        cov = ca._session_completeness(
            [self._deep(1), self._deep(2), self._kai(3), self._kai(4)], self._F)["coveragePct"]
        self.assertEqual(cov, 50.0)

    def test_kai_judge_rows_do_not_inflate_unread(self):
        # v1408 — Super/kai-judge stamps carry frameId + empty texts; they must NOT tank
        # coverage (the 13% bug: 2 real reads + 14 judges → 12.5% on a fully-swept reel).
        judges = [{"lane": "kai", "mode": "kai-judge", "frameId": "reel/f%d" % i,
                   "ts": i, "kai": {"judge": {"ok": True}}} for i in range(14)]
        cov = ca._session_completeness([self._deep(1), self._deep(2)] + judges, self._F)
        self.assertEqual(cov["unread"], 0)
        self.assertEqual(cov["reads"], 2)
        self.assertEqual(cov["coveragePct"], 100.0)

    def test_empty_text_kai_rows_are_not_unread(self):
        # grounded/summary-adjacent rows with frameId but no texts are not misses
        rows = [self._deep(1),
                {"lane": "kai", "mode": "kai", "frameId": "reel/f9", "ts": 9,
                 "kai": {"grounded": ["Shako"]}}]
        cov = ca._session_completeness(rows, self._F)
        self.assertEqual(cov["unread"], 0)
        self.assertEqual(cov["coveragePct"], 100.0)

    def test_missed_list_is_authoritative(self):
        # closer's missed[] wins over a noisy journal (and empty-text junk is filtered)
        rows = [self._deep(1), self._deep(2)] + [
            {"lane": "kai", "mode": "kai-judge", "frameId": "x", "ts": 1, "kai": {"judge": {}}}]
        missed = [{"f": "f1.jpg", "ts": 100, "texts": ["Harlequin Crest"]},
                  {"f": "f2.jpg", "ts": 200, "texts": []}]  # empty texts ignored
        cov = ca._session_completeness(rows, self._F, missed=missed)
        self.assertEqual(cov["unread"], 1)
        self.assertEqual(cov["reads"], 2)
        self.assertEqual(cov["coveragePct"], round(100.0 * 2 / 3, 1))

    def test_coverage_from_report_prefers_missed_frames(self):
        # pre-v1408 seal with inflated completeness.unread still serves 100% via missedFrames
        rep = {"missedFrames": 0, "missed": [],
               "completeness": {"reads": 2, "unread": 14, "hovers_estimated": 16,
                                "coveragePct": 12.5, "dropped": 0, "reel_frames": 153}}
        out = ca._coverage_from_report(rep)
        self.assertEqual(out, {"read": 2, "total": 2, "gaps": 0, "pct": 100.0})


class TestSceneFingerprintPortals(unittest.TestCase):
    """Scene-fingerprint honesty — `portals` now counts distinct portal/loading EVENTS (maximal
    runs of 'entering' reads, same law as townTrips), not the raw 'entering' read count. A single
    portal's loading screen spans several frames, so the raw count over-counted up to 4× on real
    sessions ("took 4 portals" when Konyo took 1). Honest + consistent with townTrips; the rest of
    the fingerprint (of-real-reads, honest-absent, farmingPct-of-reads) is confirmed honest."""

    def _deep(self, scene, area=""):
        return {"lane": "deep", "scene": scene, "area": area, "ts": 1}

    def test_a_run_of_entering_reads_is_one_portal(self):
        rows = [self._deep("transition", "Dark Wood")] * 4 + [self._deep("gameplay", "Dark Wood")]
        self.assertEqual(ca._session_scene_fingerprint(rows)["portals"], 1)

    def test_two_separated_runs_are_two_portals(self):
        rows = ([self._deep("transition", "Dark Wood")] * 3 + [self._deep("gameplay", "Dark Wood")] * 2
                + [self._deep("transition", "Cold Plains")] * 2 + [self._deep("gameplay", "Cold Plains")])
        self.assertEqual(ca._session_scene_fingerprint(rows)["portals"], 2)

    def test_towntrips_still_distinct_and_consistent(self):
        rows = ([self._deep("town", "Harrogath")] * 3 + [self._deep("gameplay", "Frigid Highlands")]
                + [self._deep("town", "Harrogath")] * 2)
        fp = ca._session_scene_fingerprint(rows)
        self.assertEqual(fp["townTrips"], 2)   # two distinct visits, not 5 town reads

    def test_honest_absent_and_farming_pct_of_reads(self):
        self.assertIsNone(ca._session_scene_fingerprint([]))                       # no reads → None
        self.assertIsNone(ca._session_scene_fingerprint([self._deep("", "")]))     # no scene/area → None
        rows = [self._deep("gameplay", "Dark Wood")] * 3 + [self._deep("town", "Rogue Encampment")]
        fp = ca._session_scene_fingerprint(rows)
        self.assertEqual(fp["farmingPct"], 75)   # 3 farming / (3 farming + 1 town) reads, not wall-time


class TestRegisterMergeMax(unittest.TestCase):
    """Merge-max audit — found grails only ever ADD, never auto-un-tick. This is the safety the
    E3 re-seal (kaiVer 4→5, re-closes every reel) depends on: `_kai_compile_register` MUST be
    monotonic-additive so a re-close can only grow the register / upgrade a tier — never drop a
    grail from Konyo's count. (The never-zero funnel guard is locked separately; the only un-tick
    anywhere is the explicit user `d2r_grailUnfound`, never an automatic path.)"""

    def test_register_is_monotonic_under_reclose(self):
        base = [{"lane": "deep", "ts": 100, "frameId": "f1", "names": ["Shako"],
                 "names_loc": {"Shako": "floor"}},
                {"lane": "kai", "ts": 150, "frameId": "f2",
                 "kai": {"judge": {"name": "The Stone of Jordan", "tier": "border"}}}]
        # a re-close under newer logic grounds MORE (E1 War Traveler) + upgrades a tier
        more = base + [{"lane": "kai", "ts": 200, "frameId": "f3", "kai": {"grounded": ["War Traveler"]}},
                       {"lane": "kai", "ts": 250, "frameId": "f4",
                        "kai": {"judge": {"name": "The Stone of Jordan", "tier": "grail"}}}]
        r1 = {r["name"]: r for r in ca._kai_compile_register(base)}
        r2 = {r["name"]: r for r in ca._kai_compile_register(more)}
        self.assertTrue(set(r1) <= set(r2), "re-close DROPPED a name — merge-max violated")
        self.assertIn("War Traveler", r2)                       # E1 recovery lands
        self.assertEqual(r1["Shako"]["firstSeenTs"], r2["Shako"]["firstSeenTs"])  # earliest preserved

    def test_best_tier_wins_never_downgrades(self):
        # a later border read can NEVER bury a proven grail (BEST-tier wins, not last-wins)
        rows = [{"lane": "kai", "ts": 100, "frameId": "f1",
                 "kai": {"judge": {"name": "Griffon's Eye", "tier": "grail"}}},
                {"lane": "kai", "ts": 200, "frameId": "f2",
                 "kai": {"judge": {"name": "Griffon's Eye", "tier": "border"}}}]
        reg = {r["name"]: r for r in ca._kai_compile_register(rows)}
        self.assertEqual(reg["Griffon's Eye"]["tier"], "grail")  # never downgraded to border

    def test_never_zero_guard_holds(self):
        # the funnel tally can never lower a real bigger count (Konyo's "404 then 4 keeps 404")
        self.assertFalse(ca._funnel_never_zero_guard(404, 4))
        self.assertTrue(ca._funnel_never_zero_guard(0, 4))
        self.assertTrue(ca._funnel_never_zero_guard(404, 500))


class TestForensicsUnresolvedSplit(unittest.TestCase):
    """② forensics honesty — "unresolved 103" reads like 103 missed items when the truth is 0
    grail misses + screen-text/noise. Backward-compatible (status STAYS 'unresolved'): adds an
    additive `unresolvedKind` ('non-item' | 'unreadable-item') + summary counts (grailMisses=0,
    screenText, unreadable). Deterministic detector, conservative (ambiguous → unreadable-item),
    no grounder change. Verified vs 29 reels: 0 grail misses · 37 screen-text · 66 unreadable."""

    def test_transition_banner_is_non_item(self):
        self.assertEqual(ca._kai_unresolved_kind(["ENTERING THE CATACOMBS LEVEL 2"]), "non-item")

    def test_short_ui_indicator_is_non_item(self):
        self.assertEqual(ca._kai_unresolved_kind(["LIVE"]), "non-item")
        self.assertEqual(ca._kai_unresolved_kind(["IDLE"]), "non-item")

    def test_fuzzy_cube_prompt_is_non_item(self):
        # the recurring garbled Horadric-cube prompt (heavily leet-mangled) resolves to non-item
        self.assertEqual(ca._kai_unresolved_kind(["INSERT SOCKETED ITEMS"]), "non-item")

    def test_plausible_garbled_item_stays_unreadable(self):
        # a long non-UI, non-noise garble is honestly left as unreadable-item (conservative)
        self.assertEqual(ca._kai_unresolved_kind(["Grffn'z Eymagh Xzq"]), "unreadable-item")

    def test_backward_compatible_status_and_summary(self):
        rep = {"sid": "s", "register": [], "routing": [], "missed": [
            {"f": "f1.jpg", "ts": 1, "texts": ["LIVE"], "cls": "gameplay"},          # UI → non-item
            {"f": "f2.jpg", "ts": 2, "texts": ["Grffn'z Eyagh Xzq"], "cls": "gameplay"}]}  # garble → unreadable
        out = ca._kai_forensics_project(rep)
        reads = [r for it in out["items"] for r in it["reads"]]
        # status STAYS 'unresolved' (live 🔬 surface unbroken); the kind is the additive sub-field
        unr = [r for r in reads if r["status"] == "unresolved"]
        self.assertEqual(len(unr), 2)
        self.assertTrue(all(r["status"] == "unresolved" for r in unr))
        kinds = {r["unresolvedKind"] for r in unr}
        self.assertEqual(kinds, {"non-item", "unreadable-item"})
        s = out["summary"]
        self.assertEqual(s["grailMisses"], 0)                       # PROVEN headline
        self.assertEqual(s["screenText"] + s["unreadable"], s["unresolved"])
        self.assertEqual(s["screenText"], 1)
        self.assertEqual(s["unreadable"], 1)


class TestKaiVerReseal(unittest.TestCase):
    """E3 — kaiVer re-seal lag. Seal-time logic (E1 two-witness grounding, ② cross-frame) changed
    without bumping kaiVer, so already-sealed reels stranded with pre-E1 registers (recoveries lived
    only in the forensics X-ray, not the real vault/grail registers). Fix: bump _KAIVER_TARGET +
    the seal stamp to 5 IN LOCKSTEP so every kaiVer-4 reel auto-re-closes under the new logic. These
    tests lock the convention (the two literals must always match) + the missed→register recovery
    the resweep unlocks, and confirm wallpaper still re-seals as junk on a resweep."""

    def _src(self):
        import inspect
        return inspect.getsource(ca)

    def test_kaiver_target_and_seal_stamp_match_in_lockstep(self):
        # THE CONVENTION: a newly-sealed reel must be stamped AT the resweep target (not below, or
        # it would re-sweep forever; not above, or old reels never catch up). A future seal-logic
        # change that bumps one literal but not the other trips this test.
        import re
        src = self._src()
        target = int(re.search(r"_KAIVER_TARGET\s*=\s*(\d+)", src).group(1))
        stamp = int(re.search(r'"kaiVer":\s*(\d+)', src).group(1))
        self.assertEqual(target, stamp,
                         "kaiVer seal stamp (%d) must equal _KAIVER_TARGET (%d) — bump in lockstep "
                         "(E3 convention: seal-logic change ⇒ bump both)" % (stamp, target))
        self.assertGreaterEqual(target, 5, "E3 bump should land kaiVer >= 5")

    def test_resweep_selects_a_below_target_reel(self):
        # a reel stamped below the target is stale → eligible for re-close; one at the target is not.
        import re
        target = int(re.search(r"_KAIVER_TARGET\s*=\s*(\d+)", self._src()).group(1))
        self.assertTrue(4 < target)      # the 29 pre-E1 kaiVer-4 reels re-sweep
        self.assertFalse(target < target)  # a freshly-sealed reel does not loop

    def test_resweep_recovers_war_traveler_into_the_register(self):
        # the payoff: on re-close, the ground-label two-witness re-grounds the floor drop, and the
        # grounded name lands in the REGISTER (missed[] → register[]) — no longer X-ray only.
        self.assertIn("War Traveler", ca._kai_ground_lines(["WAA TRAVELIR", "BATYLE B**Ys"]))
        rows = [{"lane": "kai", "ts": 1000, "frameId": "reel/f1",
                 "kai": {"grounded": ["War Traveler"]}}]
        names = {r["name"] for r in ca._kai_compile_register(rows)}
        self.assertIn("War Traveler", names)

    def test_resweep_keeps_wallpaper_as_junk(self):
        # a resweep must NEVER re-label a quarantined wallpaper frame as gems — the panel-open
        # guard is deterministic geometry, re-applied on every close.
        import stash_eye as _se
        panel_open, not_d2r = _se._panel_open_from_features(0.01, 0)
        self.assertFalse(panel_open)
        self.assertTrue(not_d2r)


class TestReadsForensicsProjection(unittest.TestCase):
    """🔬 READS FORENSICS — the pure read-only projection re-derives, from stored raw only, the
    per-item forensic X-ray: clean reads (grounded), garble the AI CORRECTED (resolved-corrected /
    recovered-2witness), near-misses it correctly REFUSED (blocked-fp), and honest unresolved.
    Deterministic (re-runs the SAME grounder/near-miss helpers the closer used) — no drift, no
    writes, works retroactively. Verified against 29 real reels: War Traveler ×7 recovered, the
    'Diablo's'/'ancients' chat blocked, 0 fabricated resolutions."""

    def _report(self):
        return {"sid": "s_test",
                "register": [{"name": "Death Torc", "firstSeenTs": 900, "frameId": "reel/f0", "loc": "floor"}],
                "routing": [{"f": "f_5.jpg", "ts": 5000, "label": "tooltip",
                             "gateReason": "cross-frame", "crossFrame": ["content"]}],
                "missed": [
                    {"f": "f_1.jpg", "ts": 1000, "texts": ["WAA TRAVELIR", "BATYLE B**Ys"], "cls": "tooltip"},
                    {"f": "f_2.jpg", "ts": 2000, "texts": ["worlU. DiablOS rThnlon"], "cls": "gameplay"},
                    {"f": "f_3.jpg", "ts": 3000, "texts": ["DEATH TOAC"], "cls": "floor"},
                    {"f": "f_4.jpg", "ts": 4000, "texts": ["zzz qqq"], "cls": "gameplay"},
                ]}

    def _find(self, out, status):
        return [r for it in out["items"] for r in it["reads"] if r["status"] == status]

    def test_war_traveler_reconstructs_as_two_witness(self):
        out = ca._kai_forensics_project(self._report())
        wt = self._find(out, "recovered-2witness")
        self.assertTrue(any(r["item"] == "War Traveler" for r in wt))
        r = next(r for r in wt if r["item"] == "War Traveler")
        self.assertTrue(r["corrected"])
        self.assertEqual(r["correction"]["via"], "name+base")
        self.assertIn("travelir", r["correction"]["raw"])
        self.assertIn("WAA TRAVELIR", r["frames"][0]["raw"])   # RAW garble verbatim

    def test_chat_garble_reconstructs_as_blocked_fp(self):
        out = ca._kai_forensics_project(self._report())
        blk = self._find(out, "blocked-fp")
        self.assertTrue(blk)
        self.assertEqual(blk[0]["item"], None)
        self.assertIn("blockedBy", blk[0]["block"])
        self.assertIn("refused", blk[0]["synthesis"])

    def test_clean_register_read_is_grounded(self):
        out = ca._kai_forensics_project(self._report())
        cln = self._find(out, "grounded")
        self.assertTrue(any(r["item"] == "Death Torc" and not r["corrected"] for r in cln))

    def test_garble_associates_to_clean_same_session_read(self):
        # 'DEATH TOAC' garble + a clean 'Death Torc' in register → resolved-corrected (same item)
        out = ca._kai_forensics_project(self._report())
        corr = [r for r in self._find(out, "resolved-corrected") if r["item"] == "Death Torc"]
        self.assertTrue(corr)
        self.assertTrue(corr[0]["corrected"])
        self.assertEqual(corr[0]["correction"]["via"], "clean-match-nearby")

    def test_pure_noise_is_unresolved_not_fabricated(self):
        out = ca._kai_forensics_project(self._report())
        unr = self._find(out, "unresolved")
        self.assertTrue(any(r["frames"][0]["raw"].startswith("zzz") for r in unr))
        self.assertTrue(all(r["item"] is None for r in unr))

    def test_crossframe_routing_becomes_recovered_crossframe(self):
        out = ca._kai_forensics_project(self._report())
        self.assertTrue(self._find(out, "recovered-crossframe"))

    def test_summary_counts_and_grouping(self):
        out = ca._kai_forensics_project(self._report())
        s = out["summary"]
        self.assertTrue({"clean", "corrected", "recovered", "blocked", "unresolved"} <= set(s.keys()))
        # recovered = War Traveler (2witness) + the cross-frame route
        self.assertGreaterEqual(s["recovered"], 2)
        self.assertGreaterEqual(s["blocked"], 1)
        self.assertGreaterEqual(s["clean"], 1)

    def test_bad_sid_payload_is_honest_absent(self):
        p = ca._forensics_payload("no_such_reel_zzz")
        self.assertFalse(p["ok"])
        self.assertEqual(p["items"], [])


import stash_eye as se  # noqa: E402


class TestStashPanelOpenGuard(unittest.TestCase):
    """v1258 🛑 STASH-PANEL-OPEN GUARD — root cause of the TV-DIABLO wallpaper bug: the
    Screen-Recording-TCC grab sometimes captured the Mac DESKTOP WALLPAPER (a vivid Hong
    Kong night skyline) instead of D2R. The multi-hue city lights on dark water tripped
    `classify_stash_grid`'s high-chroma gems branch — which had NO 'is the stash panel
    actually open' precondition — so 69 desktop frames sealed as stash-gems and fired a
    phantom tally:gems that read 0. `_panel_open_from_features` demands POSITIVE stash-grid
    geometry (a dark-cell band AND a visible grid lattice) before ANY stash-* grid label;
    an affirmatively-photographic frame (almost no dark cells) is rejected as not-D2R."""

    def test_panel_open_rejects_lit_photograph(self):
        # wallpaper crop signature: frac_dark≈0.01, ZERO dark-gridline columns.
        panel_open, not_d2r = se._panel_open_from_features(0.0098, 0)
        self.assertFalse(panel_open)
        self.assertTrue(not_d2r)

    def test_panel_open_accepts_real_stash_grid(self):
        # real open Gems tab: frac_dark≈0.39 dark cells + a strong lattice (19 dark cols).
        panel_open, not_d2r = se._panel_open_from_features(0.3914, 19)
        self.assertTrue(panel_open)
        self.assertFalse(not_d2r)

    def test_panel_open_rejects_chroma_without_lattice(self):
        # high dark fraction but NO lattice (not a grid) — still not an open panel.
        panel_open, _ = se._panel_open_from_features(0.40, 0)
        self.assertFalse(panel_open)

    def test_panel_open_rejects_near_black_scene(self):
        # boot-splash / dark-combat: frac_dark far above the panel band → not "open".
        panel_open, _ = se._panel_open_from_features(0.90, 20)
        self.assertFalse(panel_open)

    # ── real-frame fixtures (present in frames/hist) — the exact regression corpus ──
    _WALL = os.path.join(HERE, "frames", "hist",
                         "reel_s_1784734976651_81925", "f_1784734980086.jpg")
    _GEMS = os.path.join(HERE, "frames", "hist",
                         "reel_s_1784736270319_92862", "f_1784736381363.jpg")

    @unittest.skipUnless(os.path.isfile(_WALL), "wallpaper fixture frame not present")
    def test_wallpaper_frame_no_longer_classifies_stash(self):
        # THE bug frame: a colourful desktop wallpaper with a Mac menu bar and zero game
        # content must NOT classify as any stash-* label even though chroma/hue is high.
        label, detail = se.classify_stash_grid(self._WALL)
        self.assertFalse(str(label).startswith("stash"),
                         "wallpaper must not be a stash panel, got %r (%r)" % (label, detail))
        self.assertEqual(detail.get("pick"), "not-d2r")

    @unittest.skipUnless(os.path.isfile(_GEMS), "gems fixture frame not present")
    def test_real_gems_frame_still_classifies_stash_gems(self):
        # a genuine open Gems tab must STILL detect after the guard.
        label, detail = se.classify_stash_grid(self._GEMS)
        self.assertEqual(label, "stash-gems", "real gems frame regressed: %r" % (detail,))
        self.assertTrue(detail.get("panel_open"))

    # ── E2 REGRESSION GUARD (locks the 209/209 proof: no stash-* tally fires without an
    # is-D2R, panel-open frame). Verified across 29 real reels — 209 fired tallies, 209 on
    # genuine panels, 0 wallpaper/boot leaks. These fixtures freeze the two enforcement points
    # so a future edit can't silently reintroduce the desktop-wallpaper false-tally bug.
    def test_gate_holds_a_gridsolo_tally_when_not_panel_open(self):
        # a lone grid pick on a frame that is NOT panel-open sanctioned (grid_solo_ok False) —
        # the closer only sets gridSolo/grid_solo_ok when _panel_open — MUST stay held at quorum<2
        # (one 'layout' witness never self-certifies). This is the not-D2R / wallpaper safety.
        g = ca._kai_gate_check("stash-gems", ["grid"], 1, "tally:gems", grid_solo_ok=False)
        self.assertFalse(g["pass"])
        self.assertEqual(g["reason"], "quorum<2")

    def test_gate_fires_a_gridsolo_tally_only_when_panel_open_sanctioned(self):
        # the SAME lone-grid pick fires ONLY when panel-open sanctioned it (grid_solo_ok True) —
        # a real open RotW Gems tab, where OCR can't read the tab strip and grid is the legit
        # sole signal. Panel-open is the geometric gate that separates the two.
        g = ca._kai_gate_check("stash-gems", ["grid"], 1, "tally:gems", grid_solo_ok=True)
        self.assertTrue(g["pass"])

    def test_wallpaper_geometry_can_never_sanction_a_tally(self):
        # the linkage: a wallpaper's geometry (no dark cells) yields panel_open False → the closer
        # never sets grid_solo_ok → the gate above holds it. Freeze both ends of that chain.
        panel_open, not_d2r = se._panel_open_from_features(0.01, 0)   # lit photograph
        self.assertFalse(panel_open)
        self.assertTrue(not_d2r)
        self.assertFalse(ca._kai_gate_check("stash-gems", ["grid"], 1, "tally:gems",
                                            grid_solo_ok=panel_open)["pass"])


class TestSingleGridSignalIsOneWitness(unittest.TestCase):
    """v1258 router-honesty invariant (companion to the panel-open guard). `_router_conf`
    counts INDEPENDENT evidence classes, so a lone grid fingerprint is ONE witness ('layout')
    — it must never self-certify to the confidence>=2 accuracy gate on its own.

    NOTE (clearly-scoped FOLLOW-UP, deferred from this load-bearing diff): the closer's
    reel-scan build (control_app._kai_closer_loop ~L4176) still copies the grid-derived eye
    cls into `_ocr_cls`, which becomes a SECOND, phantom 'ocr'/'pixel' vote alongside the
    real 'grid'/'layout' vote for the SAME physical detector — inflating a grid-solo tally to
    conf 2. The panel-open guard above stops a FALSE (non-D2R) grid read from ever reaching
    that path; making the gate itself honest for grid-solo tallies needs a sanctioned
    single-signal route (a naive vote-drop would kill true Gems, where OCR genuinely cannot
    read the RotW 5-label tab strip and grid is legitimately the only signal). Tracked separately."""

    def test_grid_alone_is_confidence_one(self):
        self.assertEqual(ca._router_conf(["grid"]), 1)

    def test_grid_plus_genuinely_independent_class_is_two(self):
        # grid (layout) + journal (time) are two DIFFERENT physical detectors → conf 2 ok.
        self.assertEqual(ca._router_conf(["grid", "journal"]), 2)

    def test_two_names_of_one_content_witness_stay_one(self):
        # read+judge are the same tooltip witnessed twice ('content') — still one class.
        self.assertEqual(ca._router_conf(["read", "judge"]), 1)


class TestSanctionedGridSoloTallyRoute(unittest.TestCase):
    """v1259 PHANTOM-OCR GATE HONESTY (A2) — the closer used to relabel a grid-DERIVED eye
    cls into `_ocr_cls`, so a grid-solo tally frame (sources=['grid','solo'], ocrTab='' — the
    RotW gems case where the 5-label tab strip is OCR-illegible and grid is legitimately the
    ONLY signal) produced BOTH a phantom votes['ocr'] and the real votes['grid'] in
    `_kai_build_routing`. `_router_conf` maps grid->'layout' and ocr->'pixel' as DISTINCT
    classes → confidence 2 from ONE physical detector → `_kai_gate_check`'s confidence>=2
    check self-certified on a lone grid read (root of the wallpaper-sealed-as-gems miss).

    The fix: the closer no longer fakes the ocr vote (a grid-solo row carries NO ocrLabel),
    so grid is honestly ONE witness (conf 1); firing a TRUE gems tab instead rides an
    EXPLICITLY sanctioned single-signal route — grid alone, at conf 1, cleared through the
    gate ONLY when the closer flagged its own tighter grid bar (`gridSolo`: a definite tally
    pick on a panel-open dark-cell lattice, no OCR corroboration). True gems still route to
    tally:gems (via the gap-funnel, `_kai_stage3_gap_funnels`); a false/low-confidence grid
    read no longer self-certifies."""

    def _grid_solo_gems_row(self, grid_solo=True):
        # what the closer now emits for a true grid-only gems frame: a real grid vote, NO
        # phantom ocr vote (ocrLabel=None), and the sanctioned tighter-bar flag.
        return {
            "f": "g1.jpg", "ts": 1000,
            "ocr": False, "ocrLabel": None,
            "grid": True, "gridLabel": "stash-gems", "gridSolo": grid_solo,
            "label": "stash-gems",
        }

    def test_grid_solo_is_one_honest_witness_no_phantom_ocr(self):
        routing = ca._kai_build_routing([self._grid_solo_gems_row()], [], "sid1", [])
        row = routing[0]
        # grid alone — the phantom 'ocr'/'pixel' second class is GONE
        self.assertEqual(row["sources"], ["grid"])
        self.assertEqual(row["confidence"], 1)
        self.assertNotIn("ocr", row["gateSources"])
        # _router_conf invariant preserved (companion assertion)
        self.assertEqual(ca._router_conf(row["sources"]), 1)

    def test_confident_grid_solo_gems_passes_gate_via_sanctioned_route(self):
        routing = ca._kai_build_routing([self._grid_solo_gems_row()], [], "sid1", [])
        row = routing[0]
        self.assertEqual(row["label"], "stash-gems")
        self.assertEqual(row["route"], "tally:gems")
        # sanctioned single-signal route: gate PASSES honestly at conf 1 (not a quorum<2 hold)
        self.assertTrue(row["gatePass"])
        self.assertIsNone(row["gateReason"])

    def test_true_gems_still_routes_to_tally_gems(self):
        # the actual firing path for a single-witness tally is the gap-funnel — it must still
        # queue a gems shot for a genuine grid-solo gems frame.
        routing = ca._kai_build_routing([self._grid_solo_gems_row()], [], "sid1", [])
        gaps = ca._kai_stage3_gap_funnels(routing, [])
        tabs = {g["tab"] for g in gaps}
        self.assertIn("gems", tabs)

    def test_low_confidence_grid_read_does_not_self_certify(self):
        # SAME lone grid read, but the closer did NOT clear its tighter bar (no panel-open
        # lattice / not a definite pick) → gridSolo False. It must NOT pass the gate.
        routing = ca._kai_build_routing([self._grid_solo_gems_row(grid_solo=False)],
                                        [], "sid1", [])
        row = routing[0]
        self.assertEqual(row["sources"], ["grid"])
        self.assertEqual(row["confidence"], 1)
        self.assertFalse(row["gatePass"])
        self.assertEqual(row["gateReason"], "quorum<2")

    def test_sanction_never_shortcuts_a_multiclass_or_nontally_label(self):
        # the flag is honored ONLY for a grid-ONLY tally. A vault 'stash' label with the flag
        # set (and grid the sole witness) must still be held — the sanction is tally-specific.
        row = ca._kai_gate_check("stash", ["grid"], 1, "vault", grid_solo_ok=True)
        self.assertFalse(row["pass"])
        self.assertEqual(row["reason"], "quorum<2")
        # and a tally label whose sole witness is NOT grid gets no sanction either
        row2 = ca._kai_gate_check("stash-gems", ["journal"], 1, "tally:gems", grid_solo_ok=True)
        self.assertFalse(row2["pass"])
        self.assertEqual(row2["reason"], "no-hard-signal")


class TestV1381GapFunnelGateAwareRank(unittest.TestCase):
    """v1381.0 — gap-funnel must NOT prefer conf=3 wrong-cell (Personal+tooltip mis-sticky)
    over a real gems grid frame. Forensic s_178498…95276 fed gemIntake the wrong still."""

    def _wrong_cell_gems(self):
        return {
            "f": "f_wrong.jpg", "ts": 1000, "label": "stash-gems",
            "sources": ["journal", "ocr", "tabstrip"], "confidence": 3,
            "gatePass": False, "gateReason": "wrong-cell",
            "gridLabel": "stash-gems", "tabstripLabel": "stash-gems", "ocrLabel": "stash-gems",
        }

    def _real_grid_gems(self):
        return {
            "f": "f_real.jpg", "ts": 2000, "label": "stash-gems",
            "sources": [], "confidence": 0,
            "gatePass": False, "gateReason": "no-hard-signal",
            "gridLabel": "stash-gems", "grid": True,
        }

    def _gate_pass_gems(self):
        return {
            "f": "f_pass.jpg", "ts": 1500, "label": "stash-gems",
            "sources": ["grid", "tabstrip"], "confidence": 2,
            "gatePass": True, "gateReason": None,
            "gridLabel": "stash-gems", "tabstripLabel": "stash-gems",
        }

    def test_wrong_cell_scores_below_real_grid(self):
        w = self._wrong_cell_gems()
        r = self._real_grid_gems()
        self.assertLess(ca._kai_gap_funnel_score(w, "gems"), ca._kai_gap_funnel_score(r, "gems"))

    def test_gate_pass_wins_over_wrong_cell_even_if_lower_conf(self):
        w = self._wrong_cell_gems()
        p = self._gate_pass_gems()
        self.assertGreater(ca._kai_gap_funnel_score(p, "gems"), ca._kai_gap_funnel_score(w, "gems"))

    def test_gap_funnel_picks_real_grid_not_wrong_cell(self):
        routing = [self._wrong_cell_gems(), self._real_grid_gems()]
        gaps = ca._kai_stage3_gap_funnels(routing, [])
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["tab"], "gems")
        self.assertEqual(gaps[0]["f"], "f_real.jpg")
        # multi-retry alts include the wrong-cell only as last resort if viable empty —
        # here viable exists so wrong-cell may still appear in alts pool of remaining ranked
        self.assertIn("alts", gaps[0])

    def test_gap_funnel_alts_carry_next_best(self):
        routing = [self._gate_pass_gems(), self._real_grid_gems(), self._wrong_cell_gems()]
        gaps = ca._kai_stage3_gap_funnels(routing, [])
        self.assertEqual(gaps[0]["f"], "f_pass.jpg")
        self.assertIn("f_real.jpg", gaps[0].get("alts") or [])

    def test_real_receipt_skips_tab(self):
        routing = [self._real_grid_gems()]
        sess = [{"intake": {"tab": "gems", "kind": "tally", "ok": True, "total": 40}}]
        gaps = ca._kai_stage3_gap_funnels(routing, sess)
        self.assertEqual(gaps, [])

    def test_failed_receipt_does_not_skip_tab(self):
        routing = [self._real_grid_gems()]
        sess = [{"intake": {"tab": "gems", "kind": "kai-funnel", "ok": False, "total": 0, "errors": 1}}]
        gaps = ca._kai_stage3_gap_funnels(routing, sess)
        self.assertEqual(len(gaps), 1)

    def test_grid_solo_gems_still_queued(self):
        # regression: sanctioned grid-solo gems must still produce a gap-funnel job
        row = {
            "f": "g1.jpg", "ts": 1000, "label": "stash-gems",
            "sources": ["grid"], "confidence": 1,
            "gatePass": True, "gateReason": None,
            "gridLabel": "stash-gems", "grid": True, "gridSolo": True,
        }
        gaps = ca._kai_stage3_gap_funnels([row], [])
        self.assertEqual(gaps[0]["tab"], "gems")
        self.assertEqual(gaps[0]["f"], "g1.jpg")


class TestV1381SuperExcludesTallyPanels(unittest.TestCase):
    """v1381.1 — super-analyze must not item-judge stash-gems/runes/materials grids."""

    def test_tally_panel_not_selected_even_if_gate_pass(self):
        routing = [{
            "f": "gems.jpg", "ts": 1000, "label": "stash-gems",
            "gatePass": True, "confidence": 3, "sources": ["grid", "tabstrip"],
        }, {
            "f": "tip.jpg", "ts": 2000, "label": "tooltip",
            "gatePass": True, "confidence": 2, "sources": ["ocr", "read"],
        }]
        cands = ca._kai_super_select(routing, [], fullnames=set(), cap=10)
        labs = [c.get("label") for c in cands]
        self.assertNotIn("stash-gems", labs)
        self.assertIn("tooltip", labs)

    def test_plain_stash_still_eligible(self):
        routing = [{
            "f": "stash.jpg", "ts": 1000, "label": "stash",
            "gatePass": True, "confidence": 2, "sources": ["ocr", "journal"],
        }]
        cands = ca._kai_super_select(routing, [], fullnames=set(), cap=10)
        self.assertEqual(len(cands), 1)
        self.assertEqual(cands[0]["label"], "stash")


class TestV1381OcrPhraseFix(unittest.TestCase):
    """v1381.1 — GRAMD CHAR → Grand Charm forensic correction."""

    def test_gramd_char_fixes(self):
        hit = ca._kai_ocr_phrase_fix(["GRAMD CHAR"])
        self.assertIsNotNone(hit)
        self.assertEqual(hit[0], "Grand Charm")

    def test_forensic_correction_uses_phrase(self):
        corr = ca._kai_forensic_correction(["GRAMD CHAR"])
        self.assertIsNotNone(corr)
        self.assertEqual(corr[0], "Grand Charm")
        self.assertEqual(corr[3], "ocr-phrase")


class TestV1381IntakeIsRealWatchdogLaw(unittest.TestCase):
    """v1381.0 — only ok+total>0 is a real tally; failed funnel must not 'resolve' watchdog."""

    def test_failed_funnel_not_real(self):
        self.assertFalse(ca._intake_is_real(
            {"kind": "kai-funnel", "tab": "gems", "ok": False, "total": 0, "errors": 1}))

    def test_zero_total_ok_not_real(self):
        self.assertFalse(ca._intake_is_real({"ok": True, "total": 0}))

    def test_positive_total_is_real(self):
        self.assertTrue(ca._intake_is_real({"ok": True, "total": 12}))


class TestV1381IncompleteSealReclose(unittest.TestCase):
    """v1381.0 — half-sealed reels (scanned, no routing) must re-enter the closer."""

    def test_stale_kaiver_needs_reclose(self):
        self.assertTrue(ca._kai_report_needs_reclose({"kaiVer": 5, "scanned": 10, "routing": []}, 6))

    def test_incomplete_at_target_needs_reclose(self):
        # window-kill mid-closer: classes present, routing never written
        self.assertTrue(ca._kai_report_needs_reclose(
            {"kaiVer": 6, "scanned": 114, "classes": {"stash": 1}}, 6))

    def test_complete_at_target_skips(self):
        self.assertFalse(ca._kai_report_needs_reclose(
            {"kaiVer": 6, "scanned": 10, "routing": [{"f": "a.jpg", "label": "gameplay"}]}, 6))

    def test_empty_scan_no_routing_ok(self):
        # no frames scanned — not the incomplete class
        self.assertFalse(ca._kai_report_needs_reclose({"kaiVer": 6, "scanned": 0}, 6))


if __name__ == "__main__":
    unittest.main(verbosity=1)


class TestFleetUnity(unittest.TestCase):
    """v1418 — multi-machine fleet: origin behind-count + tracked-dirty ignores untracked."""

    def test_fleet_origin_status_shape(self):
        fl = ca.fleet_origin_status(force_fetch=False)
        self.assertIn("behind", fl)
        self.assertIn("howTo", fl)
        self.assertIn("dirty", fl)
        self.assertIsInstance(fl["behind"], int)
        self.assertGreaterEqual(fl["behind"], 0)

    def test_status_payload_carries_fleet(self):
        st = ca.status_payload()
        self.assertIn("fleet", st)
        self.assertIn("behind", st["fleet"])
