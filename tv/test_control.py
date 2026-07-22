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
        old = ca.subprocess.run
        ca.subprocess.run = lambda *a, **k: _PR()
        try:
            status, body, hdrs = self._post_intake()
        finally:
            ca.subprocess.run = old
        self.assertEqual(status, 200)
        self.assertEqual(hdrs.get("X-Intake-Lane"), "subscription")
        self.assertIn(b"Shako", body)

    def test_strict_mode_502s_instead_of_website_fallback(self):
        class _PR:
            returncode = 1
            stdout = b""
            stderr = b"claude: not logged in"
        old_run = ca.subprocess.run
        ca.subprocess.run = lambda *a, **k: _PR()
        os.environ["TV_INTAKE_LOCAL_STRICT"] = "1"
        try:
            status, body, _ = self._post_intake()
        finally:
            ca.subprocess.run = old_run
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
        old = ca.subprocess.run
        old_which = ca.shutil.which
        old_sock = ca._sock_open
        ca.subprocess.run = lambda *a, **k: _PR()
        ca.shutil.which = lambda *a, **k: "/usr/bin/claude"
        ca._sock_open = lambda *a, **k: False   # pin "agent OFF" so the auth ping actually runs (v924-R4 skips it during ON AIR)
        try:
            j = ca.farmgate_payload()
        finally:
            ca.subprocess.run = old
            ca.shutil.which = old_which
            ca._sock_open = old_sock
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


if __name__ == "__main__":
    unittest.main(verbosity=1)
