#!/usr/bin/env python3
# 🎛 TV DIABLO control app — TDD (v765 REPLAY THEATRE + button/window discipline).
# Boots the REAL Handler on an ephemeral port with a fixture journal + frame archive.
import glob
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
import urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# v1462 — never point the module globals at a LIVE console. The suite boots its own Handler
# on an ephemeral port, so nothing here binds 17772 today; but control_app reads these at
# import time and helpers like _sock_open(CONTROL_PORT) / _reclaim_headless_for_scan() would
# reach straight into Konyo's running app if a future test ever called one. test_agent.py has
# guarded its agent port this way since v711 ("never collide with a live agent") — same
# courtesy here. Must precede the import: both are captured at module load.
os.environ["TV_CONTROL_PORT"] = "17972"
os.environ["TV_PORT"] = "17971"
import control_app as ca  # noqa: E402
import replay as rp  # noqa: E402


def _get(port, path, timeout=3):
    # v1463 — timeout is a parameter now. /api/doctor genuinely takes seconds (it shells out
    # to probe the Claude CLI, WebView2, ports, pid files and frame ages — start_tvd_win.ps1
    # says so in its own comments), so a flat 3s made TestDoctor a load-dependent flake:
    # 1 error in 5 runs, always urlopen timing out, never a real assertion failure.
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=timeout) as r:
        return r.status, r.read(), dict(r.headers)



def _dump_dom(browser, url, budget=6000, timeout=45):
    """v1579 — launch Chrome --dump-dom WITHOUT the hang that held a push hostage.

    Two tests here still used the pre-v1490 shape: `--headless=old` plus a bare
    subprocess.run(timeout=...). Both parts are wrong on Konyo's Mac and together they hang
    forever rather than timing out:

      - `--headless=old` does not answer on this Chrome. tv/js_syntax_gate.py already knows this
        and skips with the words "this browser never answers --dump-dom over http://127.0.0.1 on
        this machine". These tests asked anyway.
      - subprocess.run's timeout kills the LAUNCHER, not the renderer helpers Chrome forks. Those
        grandchildren keep the stdout pipe open, so capture_output waits on a pipe that will never
        close - past the timeout, forever, in poll().

    That is the ten-minute stall that blocked the v1578 push. It was invisible in every re-run
    because it needs Chrome to be reachable AND to stall, and the kept log ended mid dot-stream
    with no summary. Caught live by sampling the blocked pid: main thread parked in poll(), two
    orphan "Google Chrome for Testing" processes burning CPU beside it.

    Returns a CompletedProcess, or None if no mode answered - callers skipTest on None, because a
    probe that could not run proves nothing and must not be reported as a pass.
    """
    for mode in ("--headless=new", "--headless=old"):
        with tempfile.TemporaryDirectory() as prof:
            proc = subprocess.Popen(
                [browser, mode, "--disable-gpu", "--no-sandbox",
                 "--user-data-dir=%s" % prof,
                 "--blink-settings=imagesEnabled=false",
                 "--virtual-time-budget=%d" % budget, "--dump-dom", url],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True)      # its own group, so the kill reaches the helpers
            try:
                out, err = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except Exception:
                    proc.kill()
                try:
                    proc.communicate(timeout=10)
                except Exception:
                    pass
                continue
            return subprocess.CompletedProcess(
                proc.args, proc.returncode,
                (out or b"").decode("utf-8", "replace"),
                (err or b"").decode("utf-8", "replace"))
    return None


def _screenish(size, seed, shade=None):
    """v1543 — a fixture frame that looks like a SCREEN, not a paint swatch.

    These stood in for captured frames as a single flat colour, which is precisely what
    chronicle_retro.is_dead_frame() now refuses as a blank capture — so every fixture run read as a
    dead one and the sweep stopped being exercised at all. A fixture that could not survive the
    product's own liveness check was never simulating a frame; it was simulating a bug.

    Deterministic, so frames built with the same seed are byte-identical and still group into one
    still run.
    """
    import random
    from PIL import Image
    w, h = size
    rnd = random.Random(seed)
    im = Image.new("RGB", (w, h))
    base = shade if shade is not None else 40
    im.putdata([(rnd.randrange(256), (base + rnd.randrange(120)) % 256, rnd.randrange(256))
                for _ in range(w * h)])
    return im

# ── FIXTURES NEVER TOUCH LIVE DATA, FOR EVERY CLASS IN THIS FILE ──────────────────────────────
# The console's state files live beside control_app.py and belong to the RUNNING console on his
# Mac: the persisted sweep, the swept-reel marks, the visit marks. Individual classes here already
# redirected _CHRON_RESULT_PATH when they happened to think of it, and two did not
# (TestChronicleSweepJob, TestSweepOneVisit) — so running the gates overwrote tv/chron_last_result.json
# with fixture findings. That stopped being cosmetic the day v1765 taught his board to ADOPT a
# persisted sweep on its own.
#
# Per-class redirects are the wrong shape for this: the guarantee has to hold for classes nobody has
# written yet, and the failure is silent. One module-level redirect covers the file, and
# run_gates.py fingerprints the live files around the whole set so a miss anywhere fails the run.
def setUpModule():
    global _MOD_TMP, _MOD_PATHS
    import tempfile as _tf
    _MOD_TMP = _tf.mkdtemp(prefix="d2r_state_")
    _MOD_PATHS = {}
    for attr, name in (("_CHRON_RESULT_PATH", "result.json"),
                       ("_CHRON_AUTOREAD_PATH", "autoread.json"),
                       ("_CHRON_SWEPT_PATH", "swept.json"),
                       # v1776 — a NEW state file must join this list the day it is created, or the
                       # suite starts writing his console again (REG-179, by me, twice)
                       ("_CHRON_EVIDENCE_PATH", "evidence.json"),
                       # v1778 — the VAULT sweep keeps its own swept-memory beside the console, and
                       # nothing here isolated it: the suite has been writing his live vault state
                       # the whole time. Same class as REG-179, different feature. Found by
                       # review_lite.py comparing this list against the _*_PATH constants.
                       ("_VAULT_SWEPT_PATH", "vault_swept.json")):
        if hasattr(ca, attr):
            _MOD_PATHS[attr] = getattr(ca, attr)
            setattr(ca, attr, os.path.join(_MOD_TMP, name))


def tearDownModule():
    for attr, orig in (globals().get("_MOD_PATHS") or {}).items():
        setattr(ca, attr, orig)
    shutil.rmtree(globals().get("_MOD_TMP") or "", ignore_errors=True)


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
        cls.srv.server_close()   # v1473 — shutdown() stops serving; only server_close() frees the listening socket
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
        cls.srv.server_close()   # v1473 — shutdown() stops serving; only server_close() frees the listening socket
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
        """Agent OFF (no bridge / no frames) must NEVER flip ok to False.

        ⚠ v1687 — THIS ASSERTED A PROXY. The property is "nothing the AGENT does blocks";
        it asserted the WHOLE doctor verdict, which also carries machine facts about this
        Mac. `screen_recording` (v1607, severity 'block') is granted per-binary by macOS
        TCC and a headless launch does not inherit it — so on any Mac where the tests run
        outside the granted app, this test failed for a reason that has nothing to do with
        the agent, and kept the whole pre-push gate red. CI never saw it: the check sits
        inside `if sys.platform == "darwin"` and CI is ubuntu.

        The grant is stubbed rather than tolerated. Tolerating it (ignoring that check id)
        would also swallow a real regression where the agent somehow caused it; stubbing
        says exactly what is being held constant. The check itself is UNCHANGED and still
        blocks on his console, which is the whole reason it was added.
        """
        self._shim_claude_on_path()
        old = ca._agent_mode
        old_sr = getattr(ca, "_screen_recording_ok_quick", None)
        ca._agent_mode = "off"
        if old_sr is not None:
            ca._screen_recording_ok_quick = lambda: True
        try:
            d = ca.doctor_payload()
            self.assertTrue(d["ok"], "doctor blocked with the agent merely OFF: "
                            + repr([c for c in d["checks"]
                                    if c["severity"] == "block" and not c["ok"]]))
        finally:
            ca._agent_mode = old
            if old_sr is not None:
                ca._screen_recording_ok_quick = old_sr

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
            st, body, _ = _get(port, "/api/doctor", timeout=45)   # v1463 — doctor is slow by design
            self.assertEqual(st, 200)
            j = json.loads(body)
            self.assertIn("checks", j)
            self.assertRegex(str(j["ver"]), r"^v")
        finally:
            srv.shutdown()
            srv.server_close()   # v1473 — shutdown() stops serving; only server_close() frees the listening socket
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


class TestSessionsHomeDashOrder(unittest.TestCase):
    """v1424 — Sessions storyline is document-order, not CSS-order-only.
    Konyo: 'routines … are out of order' — Ⅰ HUNT → Ⅱ MISSIONS → Ⅲ RECORD must
    each own banner + body in sequence (banners stacked then content later = broken)."""

    def test_zone_content_interleaved(self):
        import re
        ui = os.path.join(HERE, "control_ui.html")
        with open(ui, encoding="utf-8") as f:
            html = f.read()
        # v1468 — the dash now CONTAINS <section class="zone"> wrappers (one per movement), so a
        # non-greedy ...</section> stopped at the first ZONE's close and only ever saw zone Ⅰ.
        # Scan forward balancing section tags to get the real home-dash body. The assertion below
        # is unchanged: the storyline order this guards is exactly the same, it is only the
        # container nesting that moved.
        # Strip HTML comments first: the v1468 notes discuss "<section>" in prose, and a naive
        # tag scan counts those words as real tags (this exact trap cost a debug cycle).
        html = re.sub(r"<!--[\s\S]*?-->", "", html)
        start = html.index('<section class="home-dash"')
        i, depth, end = html.index(">", start) + 1, 1, None
        for mm in re.finditer(r"<section\b|</section>", html[i:]):
            depth += 1 if mm.group(0).startswith("<section") else -1
            if depth == 0:
                end = i + mm.start()
                break
        self.assertIsNotNone(end, "home-dash section never closes")
        sec = html[i:end]
        self.assertIn('class="zone"', sec, "v1468 — each movement must be its own <section class='zone'>")
        # track zone banners + main board ids in document order
        tokens = re.findall(
            r'class="zone-banner (zone-[a-z]+)"|id="(hd-(?:taskforce|forge|kpi|tallybar|lastsession|history))"',
            sec,
        )
        seq = [a or b for a, b in tokens]
        expected = [
            "zone-hunt", "hd-taskforce",
            "zone-mission", "hd-forge",
            "zone-record", "hd-kpi", "hd-tallybar", "hd-lastsession", "hd-history",
        ]
        self.assertEqual(seq, expected, f"Sessions home-dash out of order:\n  got {seq}\n  exp {expected}")

    def test_forge_ready_chips_before_pipeline(self):
        """Ready crafts ride with MAKE NOW, not after the pipeline waiting list."""
        ui = os.path.join(HERE, "control_ui.html")
        with open(ui, encoding="utf-8") as f:
            html = f.read()
        # scope to hdForge
        i = html.find("function hdForge(")
        self.assertGreater(i, 0)
        chunk = html[i:i + 2500]
        self.assertLess(
            chunk.find("concat((craftNow || []).slice(0, 6)"),
            chunk.find(".concat((f.pipeline || []).map"),
            "craftNow chips must render before pipeline chips",
        )


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
        # v1496 — OWN THE ENVIRONMENT YOU ASSERT ON. The beacon now stays silent under CI (a runner
        # is not one of Konyo's machines and had been showing up in his fleet), so this test has to
        # say which side of that it is testing. It passed on the Mac and ERRORed on the runner purely
        # because CI=true is set there — the same local-vs-CI blindness as REG-082, inverted.
        _saved_env = {k: os.environ.pop(k, None) for k in ("CI", "GITHUB_ACTIONS", "TVD_NO_BEACON")}
        try:
            ca._console_beacon("boot")
            self.assertEqual(sent["url"], "https://bull-4-u.com/api/console")
            self.assertTrue(sent["auth"].startswith("Basic "))
            self.assertEqual(sent["body"]["event"], "boot")
            self.assertIn("machine", sent["body"])
            self.assertIn("ver", sent["body"])
            self.assertIn("nickname", sent["body"], "v1496 — the friendly name must ride the beacon")
            # failure is silent — never raises into a caller
            _ur.urlopen = lambda *a, **k: (_ for _ in ()).throw(OSError("net down"))
            ca._console_beacon("hb")   # must not raise
            # …and the other side of the contract: under CI it must not send AT ALL
            sent.clear()
            _ur.urlopen = fake_urlopen
            os.environ["CI"] = "true"
            ca._console_beacon("boot")
            self.assertEqual(sent, {}, "a CI runner must never check in to Konyo's fleet")
        finally:
            _ur.urlopen = old
            os.environ.pop("CI", None)
            for k, v in _saved_env.items():
                if v is not None:
                    os.environ[k] = v


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
        cls.srv.server_close()   # v1473 — shutdown() stops serving; only server_close() frees the listening socket
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
        old_find = ca._find_claude_bin
        ca.subprocess.run = lambda *a, **k: _PR()
        ca.shutil.which = lambda *a, **k: "/usr/bin/claude"   # v924.1 — CI has no CLI; the gate must still be testable
        # v1456 — patching which() alone was NOT enough: _find_claude_bin verifies os.path.isfile()
        # on the hit, so on a host with no real CLI (the Linux runner) exe came back empty and
        # claude_auth flipped to "skipped — no CLI". This test PASSED on the Mac only because a real
        # ~/.local/bin/claude exists there — same Mac-hides-CI class as REG-047. Patch the seam.
        ca._find_claude_bin = lambda *a, **k: "/usr/bin/claude"
        try:
            j = ca.farmgate_payload()
        finally:
            ca.subprocess.run = old
            ca.shutil.which = old_which
            ca._find_claude_bin = old_find
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

    def test_v1420_arm_force_exit_is_nonblocking_idempotent(self):
        # Force-Quit killer: arm once, never block Cocoa, never double-arm.
        import time
        old_exit = ca.os._exit
        exits = []
        ca.os._exit = lambda code=0: exits.append(code)
        old_armed = ca._FORCE_EXIT_ARMED
        try:
            ca._FORCE_EXIT_ARMED = False
            t0 = time.time()
            self.assertTrue(ca._arm_force_exit("unit-force", delay=0.05))
            self.assertLess(time.time() - t0, 0.1)
            self.assertTrue(ca._FORCE_EXIT_ARMED)
            self.assertFalse(ca._arm_force_exit("unit-force-2", delay=0.05))  # idempotent
            deadline = time.time() + 1.0
            while not exits and time.time() < deadline:
                time.sleep(0.02)
            self.assertEqual(exits, [0])
        finally:
            ca._FORCE_EXIT_ARMED = old_armed
            ca.os._exit = old_exit

    def test_v1420_request_console_exit_marks_gone_and_arms(self):
        # Unified ✕ / Esc path: mark gone + async stop + force-exit arm, no hang.
        import time
        old_exit = ca.os._exit
        ca.os._exit = lambda code=0: None
        old_armed = ca._FORCE_EXIT_ARMED
        old_done = ca._EXIT_STOP_DONE
        try:
            ca._FORCE_EXIT_ARMED = False
            ca._EXIT_STOP_DONE = False
            ca._WINDOW_LIVE = True
            ca._MAIN_WIN = object()
            ca._WINDOW_ONLY = False
            ca._agent_mode = "live"
            t0 = time.time()
            # v1463 — the old 30.0s "so the test never dies" was backwards: the finally block
            # restores the REAL os._exit ~0.35s later, and _die() resolves os._exit at FIRE
            # time, so at t+30s the runner was killed with exit 0 and no summary — a false
            # green whenever the suite ran slower than the deadline (observed 17-24s).
            # Short delay + an explicit disarm in finally.
            ca._request_console_exit("unit-x", hard_delay=5.0)
            self.assertLess(time.time() - t0, 0.15)
            self.assertFalse(ca._WINDOW_LIVE)
            self.assertIsNone(ca._MAIN_WIN)
            self.assertTrue(ca._FORCE_EXIT_ARMED)
            time.sleep(0.35)
            self.assertIn(("stop", False), self._calls)
        finally:
            ca._FORCE_EXIT_CANCEL = True     # v1463 — call off the armed deadline for real
            ca._FORCE_EXIT_ARMED = old_armed
            ca._EXIT_STOP_DONE = old_done
            ca.os._exit = old_exit

    def test_v1420_esc_empty_stack_hits_api_quit(self):
        # UI contract: empty-stack Escape posts /api/quit (Mac Force-Quit class).
        # v1472 — context manager; the bare open().read() here was the last unclosed-file
        # ResourceWarning the suite emitted (the sibling at ~3399 already did it correctly).
        with open(os.path.join(os.path.dirname(ca.__file__), "control_ui.html"),
                  encoding="utf-8") as _uf:
            ui = _uf.read()
        self.assertIn("/api/quit", ui)
        self.assertIn("v1420", ui)
        self.assertIn("Leaving console", ui)
        self.assertRegex(ui, r"key\s*!==\s*['\"]Escape['\"]")


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
        cls.srv.server_close()   # v1473 — shutdown() stops serving; only server_close() frees the listening socket
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
        cls.srv.server_close()   # v1473 — shutdown() stops serving; only server_close() frees the listening socket
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

    # v1712 — THESE TWO HAVE NOT RUN SINCE THE CORPUS WAS PRUNED, AND CANNOT RUN AGAIN.
    # Both reels (s_1784734976651_81925, s_1784736270319_92862) are gone from frames/hist, and
    # tv/frames/ is gitignored on purpose — they are his screenshots. So the skip is not "not on
    # this machine today"; it is permanent, in both venues. A skip that reads like a passing
    # environment check is the friendlier face of a gate that never runs.
    # WHAT STILL COVERS THE BUG: the DECISION is `_panel_open_from_features(frac_dark, dark_cols)`,
    # which is pure and takes the two already-computed features — and it is tested above at the
    # real measured values, including the wallpaper case (0.01, 0) and the genuine open-panel case
    # (0.3914, 19). Those run everywhere, with no footage. What is genuinely lost here is only the
    # END-TO-END path (crop -> features -> label) on real pixels, which is why these are kept
    # rather than deleted: if the footage ever returns they are immediately valuable again.
    @unittest.skipUnless(os.path.isfile(_WALL),
                         "wallpaper fixture reel s_1784734976651_81925 was pruned — PERMANENTLY "
                         "skipped in both venues; the decision itself is covered by the "
                         "_panel_open_from_features tests above")
    def test_wallpaper_frame_no_longer_classifies_stash(self):
        # THE bug frame: a colourful desktop wallpaper with a Mac menu bar and zero game
        # content must NOT classify as any stash-* label even though chroma/hue is high.
        label, detail = se.classify_stash_grid(self._WALL)
        self.assertFalse(str(label).startswith("stash"),
                         "wallpaper must not be a stash panel, got %r (%r)" % (label, detail))
        self.assertEqual(detail.get("pick"), "not-d2r")

    def test_the_wallpaper_DECISION_is_still_covered_without_any_footage(self):
        """v1712 — the two real-frame tests below are permanently skipped, so this is what
        actually holds the wallpaper bug now. If someone deletes the pure-predicate tests, the
        skipped pair would silently become the ONLY coverage — i.e. none at all."""
        # the exact features the 69 sealed wallpaper frames produced: lit photo, no dark cells
        panel_open, not_d2r = se._panel_open_from_features(0.01, 0)
        self.assertTrue(not_d2r, "a lit photograph with no dark stash cells must be rejected as "
                                 "not-D2R before it can reach ANY stash-* label")
        self.assertFalse(panel_open)
        # and the converse, so this proves DISCRIMINATION rather than a one-sided reject:
        # a genuine open stash panel must survive the same guard
        panel_open, not_d2r = se._panel_open_from_features(0.3914, 19)
        self.assertFalse(not_d2r, "a real open stash panel must not be thrown out as not-D2R")
        self.assertTrue(panel_open)
        # the boundary is a named constant, not a literal buried in a comparison
        self.assertLess(se._NOT_D2R_DARK_MAX, se._PANEL_DARK_MIN,
                        "the not-D2R ceiling must sit below the open-panel floor, or the two "
                        "bands overlap and a wallpaper can be read as a panel")

    @unittest.skipUnless(os.path.isfile(_GEMS),
                         "gems fixture reel s_1784736270319_92862 was pruned — PERMANENTLY "
                         "skipped in both venues; see the note above")
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

    def test_rev_list_fail_is_not_unified(self):
        """v1709 — git rev-list failing must not paint 'unified with origin/main'."""
        real = ca.subprocess.run

        def fake(args, **kw):
            if isinstance(args, (list, tuple)) and len(args) >= 2 and args[0] == "git" and args[1] == "rev-list":
                class R:
                    returncode = 1
                    stdout = ""
                    stderr = "fail"
                return R()
            return real(args, **kw)

        saved = dict(ca._FLEET_CACHE)
        try:
            ca._FLEET_CACHE["val"] = None
            ca._FLEET_CACHE["t"] = 0
            with mock.patch.object(ca.subprocess, "run", side_effect=fake):
                fl = ca.fleet_origin_status(force_fetch=False)
            self.assertFalse(fl["ok"], fl)
            self.assertNotIn("unified", (fl.get("howTo") or "").lower())
        finally:
            ca._FLEET_CACHE.clear()
            ca._FLEET_CACHE.update(saved)


class TestV1704UnknownStaysUnknown(unittest.TestCase):
    """v1709 — a thrown journal walk is not an idle night."""

    def test_journal_throw_is_unknown_not_idle(self):
        saved = ca.__dict__.get("_STATUS_JOURNAL_CACHE")
        try:
            ca._STATUS_JOURNAL_CACHE = None
            with mock.patch.object(ca, "_kai_journal_rows", side_effect=RuntimeError("boom")):
                st = ca.status_payload()
            sh = st.get("sessionHealth") or {}
            self.assertEqual(sh.get("verdict"), "unknown", sh)
            self.assertNotEqual(sh.get("verdict"), "idle")
            self.assertEqual(sh.get("error"), "journal unread")
        finally:
            if saved is None:
                ca.__dict__.pop("_STATUS_JOURNAL_CACHE", None)
            else:
                ca._STATUS_JOURNAL_CACHE = saved


class TestV1456HonestyDefaults(unittest.TestCase):
    """v1456 — the KAI-accuracy audit's honesty gaps in the top-level status defaults.

    The gate / engine-bay / reference-ID machinery was already honest; what dented it was
    top-of-payload optimism: an empty bridge body cached as good, a 15s last-good snapshot that
    looked as live as a fresh fetch, gameOk claiming "fine" when nothing was known, a watchdog
    lamp that could never report down, and a receipt feed that showed gate-REFUSED reads as
    authoritative. Every fix here SURFACES the truth — nothing is hidden or dropped."""

    def test_empty_bridge_body_is_not_a_good_state(self):
        """A degenerate /state body ({} or a list) must read as a MISS, not a good snapshot."""
        import io
        import urllib.request as ur

        class _Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        saved = ur.urlopen
        try:
            for body, why in ((b"{}", "empty object"),
                              (b"[]", "not even a dict"),
                              (b'{"junk": 1}', "no online/now — carries no state")):
                ur.urlopen = lambda *a, **k: _Resp(body)
                self.assertIsNone(ca._bridge_state(), "%s must not count as bridge state" % why)
            ur.urlopen = lambda *a, **k: _Resp(b'{"online": true, "now": 5, "readCount": 2}')
            got = ca._bridge_state()
            self.assertIsInstance(got, dict, "a real payload still comes through")
            self.assertEqual(got.get("readCount"), 2)
        finally:
            ur.urlopen = saved

    def test_status_marks_stale_state_and_unknown_game(self):
        """stateAgeMs/stateFresh/gameOkKnown exist and tell the truth in both directions."""
        st = ca.status_payload()
        for k in ("stateAgeMs", "stateFresh", "gameOkKnown"):
            self.assertIn(k, st, "%s must ride the payload" % k)
        self.assertIsInstance(st["stateFresh"], bool)
        self.assertIsInstance(st["gameOkKnown"], bool)
        self.assertIsInstance(st["stateAgeMs"], int)
        # no agent running under the suite → no bridge state → nothing may be claimed known
        if not st.get("bridge"):
            self.assertEqual(st["stateAgeMs"], -1, "no state → no age, not 0 (which reads as 'now')")
            self.assertFalse(st["stateFresh"])
            self.assertFalse(st["gameOkKnown"], "missing bridge data is not a claim that the game is fine")

    def test_status_stale_grace_is_marked_not_silent(self):
        """With a last-good snapshot 6s old and no fresh poll, the payload says stale + its age."""
        saved = dict(ca._BR_CACHE)
        saved_alive = ca._agent_alive
        try:
            now = ca.time.time()
            ca._agent_alive = lambda: True
            ca._BR_CACHE["ping"] = True
            ca._BR_CACHE["ts"] = now - 20.0            # ping itself is old → not a fresh poll
            ca._BR_CACHE["st"] = {"online": True, "now": 1, "gameOk": True}
            ca._BR_CACHE["st_ts"] = now - 6.0          # inside the 15s last-good grace
            ca._BRIDGE_LAST_OK = now - 6.0
            st = ca.status_payload()
            self.assertFalse(st["stateFresh"], "a graced snapshot is not a fresh one")
            self.assertGreaterEqual(st["stateAgeMs"], 5000)
            self.assertLess(st["stateAgeMs"], 15000)
            self.assertTrue(st["gameOkKnown"], "this snapshot DID carry gameOk")
        finally:
            ca._BR_CACHE.clear()
            ca._BR_CACHE.update(saved)
            ca._agent_alive = saved_alive

    def test_watchdog_lamp_can_report_down_and_idle(self):
        """The lamp speaks the shared vocabulary: down when dead-hard, idle before any seal."""
        saved_wl = ca.__dict__.get("_WATCHDOG_LAST", _MISSING)
        saved_dh = ca.__dict__.get("_ENGINE_DEAD_HARD", _MISSING)
        try:
            ca.__dict__.pop("_WATCHDOG_LAST", None)
            ca._ENGINE_DEAD_HARD = False
            wd = ca._engines_status()["watchdog"]
            self.assertEqual(wd["state"], "idle", "never-fired watchdog is idle, not permanently 'armed'")
            self.assertIn("no seal checked yet", wd["note"])
            ca._ENGINE_DEAD_HARD = True
            wd = ca._engines_status()["watchdog"]
            self.assertEqual(wd["state"], "down", "a dead-hard engine cannot arm the watchdog")
            self.assertFalse(wd["wired"])
            ca._ENGINE_DEAD_HARD = False
            ca._WATCHDOG_LAST = {"sid": "s_1", "violations": 0, "rules": [],
                                 "ts": int(ca.time.time() * 1000), "verdict": "clean"}
            wd = ca._engines_status()["watchdog"]
            self.assertEqual(wd["state"], "live", "a just-checked seal is a live beat")
            self.assertEqual(wd["verdict"], "clean")
        finally:
            if saved_wl is _MISSING:
                ca.__dict__.pop("_WATCHDOG_LAST", None)
            else:
                ca._WATCHDOG_LAST = saved_wl
            if saved_dh is _MISSING:
                ca.__dict__.pop("_ENGINE_DEAD_HARD", None)
            else:
                ca._ENGINE_DEAD_HARD = saved_dh

    def test_receipts_carry_the_gate_verdict(self):
        """A gate-REFUSED read still appears (nothing hidden) but is marked held with its reason."""
        tmp = tempfile.mkdtemp()
        old_here = ca.HERE
        saved_cache = ca.__dict__.get("_RECEIPTS_CACHE", _MISSING)
        try:
            ca.HERE = tmp
            ca.__dict__.pop("_RECEIPTS_CACHE", None)
            rows = [
                {"ts": 1, "completedTs": 1000, "lane": "deep", "scene": "stash", "area": "Harrogath",
                 "names": ["Harlequin Crest"], "sessionId": "s_1", "frameId": "f_1",
                 "gatePass": True, "gateReason": "quorum>=2"},
                {"ts": 2, "completedTs": 2000, "lane": "deep", "scene": "stash", "area": "Harrogath",
                 "names": ["Shako"], "sessionId": "s_1", "frameId": "f_2",
                 "gatePass": False, "gateReason": "wrong-cell"},
            ]
            with open(os.path.join(tmp, "sessions.jsonl"), "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
            got = ca._receipts_stream()
            by_name = {(r.get("refs") or {}).get("itemName"): r for r in got}
            self.assertIn("Harlequin Crest", by_name)
            self.assertIn("Shako", by_name, "a refused read is SURFACED, never dropped")
            proven, held = by_name["Harlequin Crest"], by_name["Shako"]
            self.assertIs(proven["held"], False)
            self.assertIs(proven["gate"]["pass"], True)
            self.assertIs(held["held"], True)
            self.assertIs(held["gate"]["pass"], False)
            self.assertEqual(held["gate"]["reason"], "wrong-cell")
        finally:
            ca.HERE = old_here
            if saved_cache is _MISSING:
                ca.__dict__.pop("_RECEIPTS_CACHE", None)
            else:
                ca._RECEIPTS_CACHE = saved_cache
            shutil.rmtree(tmp, ignore_errors=True)


class TestV1457HonestySurfacesInUi(unittest.TestCase):
    """v1457 — the honesty fields are useless if the console silently stops rendering them.
    Cheap source-contract check (no server, no browser): the console must still SAY the three
    unknown/stale/refused truths the backend now ships."""

    def _ui(self):
        with open(os.path.join(os.path.dirname(ca.__file__), "control_ui.html"),
                  encoding="utf-8") as f:
            return f.read()

    def test_capture_lamp_speaks_unknown_and_stale(self):
        ui = self._ui()
        self.assertIn("gameOkKnown", ui, "the lamp must read the known/unknown flag")
        self.assertIn("game state unknown", ui)
        self.assertIn("stateFresh", ui)
        self.assertIn("last known ", ui, "a graced snapshot must say how old it is")

    def test_receipt_row_marks_a_gate_refused_read(self):
        ui = self._ui()
        self.assertIn("rcpt-held", ui)
        self.assertIn("HELD", ui)
        self.assertIn("gate.pass === false", ui, "held state comes from the gate verdict itself")

    def test_g5_card_shows_its_last_error(self):
        ui = self._ui()
        self.assertIn("last Grok error", ui, "a swallowed primary-lane failure is not honest")


class TestRunnerIsLast(unittest.TestCase):
    """v1476 — enforce the v1456 lesson instead of only documenting it.

    `unittest.main()` exits the interpreter, so ANY class defined after it is never defined and
    never runs — silent zero coverage that still prints OK. v1456 fixed one instance and left a
    comment; this session I appended a new test class after the runner anyway and the suite
    happily reported 267 OK with my test uncollected. A comment is not a guard.
    """

    def test_no_test_class_is_defined_after_the_runner(self):
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            src = fh.read()
        # Anchor at column 0: this test mentions the marker itself in a string literal, and an
        # unanchored search finds THAT first — the guard then reports the class below it and
        # fails on a correct file. Only a top-level `if __name__` is the real runner.
        m = None
        for m in re.finditer(r'^if __name__ == "__main__":', src, re.M):
            pass
        self.assertIsNotNone(m, "the runner block moved or was renamed")
        tail = src[m.start():]
        stranded = re.findall(r"^class\s+(\w+)\(", tail, re.M)
        self.assertEqual(
            stranded, [],
            "these classes are defined AFTER unittest.main() and can never run: %s. "
            "Move them above the runner block." % ", ".join(stranded))


class TestJsSyntaxGate(unittest.TestCase):
    """v1476 — the two surfaces must PARSE. Twice in one session an edit produced a hard
    `Uncaught SyntaxError` that blanked a 37k-line page (REG-060: a heredoc ate \n escapes and
    left a raw newline inside a quoted literal; REG-072: a // comment appended mid-line swallowed
    the rest of a statement). Both were caught only because a human ran headless Chromium by hand.

    A hand-rolled tokenizer was tried first and rejected — it reported 14-16 problems on files
    that parse perfectly, because these pages use `${…}` templates with nested backticks, embedded
    HTML, and regex literals a heuristic cannot separate from division. A gate with false alarms
    gets ignored, so this asks a real JS engine instead.
    """

    def test_surfaces_parse_in_a_real_js_engine(self):
        import js_syntax_gate
        problems, skipped = js_syntax_gate.check()
        if skipped:
            self.skipTest("JS syntax gate unavailable: %s" % skipped)
        self.assertEqual(problems, [], "JS SYNTAX ERROR — the page would be blank:\n  " +
                         "\n  ".join(problems))


class TestConsoleReadsTheActiveWorld(unittest.TestCase):
    """v1478 — REG-076. The console must read the SAME world the board writes.

    The console shares an origin with the board and reads the chronicle straight out of
    localStorage through its own `lsFork()`. That function carried a hand-copied second
    implementation of the board's fork rule, and the copy still asserted "machine fork (W·/WL·)
    never applies on this Mac console" — untrue from the moment a Windows PC got its own world.
    The board wrote W·, the console read BARE, and a machine that is supposed to start empty
    greeted its owner with someone else's chronicle: "HOLY GRAIL 243 / 403 · 60% claimed".

    This is the THIRD of its family (REG-069 read a key raw; REG-075 gated on a differently-named
    function), so a grep-level assertion is not enough — all three passed a reading. This test
    EXECUTES the shipped lsFork in a real JS engine against seeded storage and checks which key it
    lands on, including the case that actually bit: THIS PC's key absent, the owner's key present.
    Absence must stay absence; zero is the correct answer for a machine that has farmed nothing.
    """

    # v1736 — REWRITTEN TO THE v:2 VOCABULARY, because the function under test had moved and
    # this test had not. It seeded `{v:1, m:'windows'|'mac'}` and asserted W·/WL·/bare/L· — the
    # PRE-v1499 protocol. v1499 replaced `m` with 'owner'/'guest' and began publishing the literal
    # prefixes, so every case here was feeding the console an input the board had stopped writing
    # three versions earlier. The test stayed green the whole time and the console stayed broken:
    # a real gate, on real data, that never once fed the input that breaks it.
    # [[gate-blind-to-unexercised-input]]
    ID = "abcd1234efgh"
    PFX, LPFX = "I·abcd1234·", "IL·abcd1234·"

    @classmethod
    def _route(cls, owner, prof):
        return {"v": 2, "owner": owner, "id": cls.ID,
                "m": "owner" if owner else "guest", "p": prof,
                "pfx": "" if owner else cls.PFX,
                "lpfx": "L·" if owner else cls.LPFX,
                "lp": ["K"], "wp": ["K"]}

    # (label, route | None, seeded keys, expected return)
    CASES = [
        ("owner main reads bare",       {"owner": True,  "p": "main"},   {"K": "owner"},              "owner"),
        ("owner ladder reads L",        {"owner": True,  "p": "ladder"}, {"L·K": "owner-l"},          "owner-l"),
        ("guest main reads I<id8>",     {"owner": False, "p": "main"},   {"I·abcd1234·K": "mine"},     "mine"),
        ("guest ladder reads IL<id8>",  {"owner": False, "p": "ladder"}, {"IL·abcd1234·K": "mine-l"}, "mine-l"),
        # THE LEAK: this world has farmed nothing, the owner has. Must NOT fall back to bare.
        # Executed against the SHIPPED pre-fix function this returned "owner" — the
        # "HOLY GRAIL 243 / 403" bleed REG-076 closed, reopened by v1499's vocabulary change.
        ("guest empty stays empty",     {"owner": False, "p": "main"},   {"K": "owner"},              None),
        ("guest ladder no fallback",    {"owner": False, "p": "ladder"}, {"K": "owner", "L·K": "x"},   None),
        # A reader that cannot identify the world must read NOTHING. bible.html:3690 in its own
        # words: "Guessing bare is how the harm happened."
        ("no route reads nothing",      None,                            {"K": "owner"},              None),
        ("v:1 route reads nothing",     "v1",                            {"K": "owner"},              None),
    ]

    def _extract_lsfork(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "control_ui.html")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        start = src.find("function lsFork(bare){")
        self.assertNotEqual(start, -1, "lsFork() vanished from control_ui.html")
        i, depth = src.index("{", start), 0
        for j in range(i, len(src)):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    return src[start:j + 1]
        self.fail("could not find the end of lsFork()")

    def test_lsfork_lands_on_the_active_worlds_key(self):
        import js_syntax_gate
        browser = js_syntax_gate.find_browser()
        if not browser:
            self.skipTest("no Chromium/Edge found — cannot execute lsFork")
        # v1490 — and skip when the browser cannot answer over loopback on this
        # machine: it would burn the full timeout and ERROR on an environment fact.
        if not js_syntax_gate.browser_can_load_localhost(browser):
            self.skipTest(js_syntax_gate.NO_LOOPBACK + " — " + "cannot execute lsFork")
        fn = self._extract_lsfork()

        # The board publishes the route; mirror a realistic payload where 'K' IS a forked key.
        def _route_for(c):
            if c[1] is None:
                return None
            if c[1] == "v1":
                return {"v": 1, "m": "mac", "p": "main", "lp": ["K"], "wp": ["K"]}
            return self._route(c[1]["owner"], c[1]["p"])

        cases_js = json.dumps([
            {"label": c[0], "route": _route_for(c), "seed": c[2], "want": c[3]}
            for c in self.CASES
        ])
        html = (
            "<!doctype html><meta charset=utf-8><pre id=out></pre><script>\n"
            + fn + "\n"
            "var CASES = " + cases_js + ";\n"
            "var res = [];\n"
            "CASES.forEach(function(c){\n"
            "  localStorage.clear();\n"
            "  if (c.route) localStorage.setItem('d2r_lsrRoute', JSON.stringify(c.route));\n"
            "  for (var k in c.seed) localStorage.setItem(k, c.seed[k]);\n"
            "  var got = lsFork('K');\n"
            "  res.push({label:c.label, want:c.want, got:got});\n"
            "});\n"
            "document.getElementById('out').textContent = 'RESULT:' + JSON.stringify(res);\n"
            "</script>"
        )
        repo = js_syntax_gate.REPO
        tmp = os.path.join(repo, "_lsfork_probe.html")
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(html)
        srv, port = js_syntax_gate._serve(repo)
        try:
            with tempfile.TemporaryDirectory() as prof:
                r = _dump_dom(browser, "http://127.0.0.1:%d/_lsfork_probe.html" % port)
                if r is None:
                    self.skipTest("Chrome never answered --dump-dom over http on this "
                                  "machine (js_syntax_gate reports the same); a probe "
                                  "that could not run proves nothing")
            blob = (r.stdout or "") + (r.stderr or "")
        finally:
            srv.shutdown()
            srv.server_close()
            try:
                os.remove(tmp)
            except OSError:
                pass

        m = re.search(r"RESULT:(\[.*?\])</pre>", blob, re.S)
        self.assertIsNotNone(
            m, "the probe never reported — lsFork threw or the page failed to run:\n"
               + blob[-800:])
        bad = []
        for row in json.loads(m.group(1)):
            if row["got"] != row["want"]:
                bad.append("%s: read %r, expected %r" % (row["label"], row["got"], row["want"]))
        self.assertEqual(
            bad, [],
            "the console is reading the WRONG world — this is how the owner's chronicle leaks "
            "onto a fresh machine:\n  " + "\n  ".join(bad))

    def test_board_publishes_the_route_the_console_consumes(self):
        """One rule, one source. The console routes from the board's payload, so the board must
        actually publish it — otherwise the console silently falls back and the two drift again."""
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(repo, "bible.html"), encoding="utf-8") as fh:
            board = fh.read()
        self.assertIn("'d2r_lsrRoute'", board,
                      "the board no longer publishes d2r_lsrRoute; the console cannot route")
        for field in ("_LP_FORKED", "_WP_FORKED", "D2R_MACHINE", "D2R_PROFILE"):
            self.assertIn(field, board, "the published route lost %s" % field)
        with open(os.path.join(repo, "tv", "control_ui.html"), encoding="utf-8") as fh:
            console = fh.read()
        self.assertIn("'d2r_lsrRoute'", console, "the console stopped reading the board's route")
        self.assertNotIn(
            "never applies on this Mac console", console,
            "the false claim that the machine fork never applies is back — that comment WAS the bug")


class TestForkedKeysAreRouted(unittest.TestCase):
    """v1479 — close the bug FAMILY, not just the third instance.

    Three separate defects have now shipped from the same root: a key that belongs to a per-machine
    or per-account world was reached WITHOUT going through the router.

      REG-069  d2r_rwMade read raw          -> the cousin saw the owner's forged runewords
      REG-075  a differently-named gate     -> the Forge counts contradicted its own note
      REG-076  the console's private lsFork -> a fresh PC showed the owner's 243/403 chronicle

    Every one of them passed a careful code reading, and the third took a user report to find. So
    the invariant is enforced mechanically: if a key is in `_LP_FORKED` or `_WP_FORKED`, the only
    ways to touch it are `LSR.*` (the board) or `lsFork()` (the console).

    Raw access is still legal where it is the POINT — the one-time migrations that must address
    `L·`/`W·` namespaces explicitly, regardless of which world is active. Those sites carry an
    inline `/* raw-ok: … */` marker, which makes the exemption a deliberate, reviewable act rather
    than an accident. A new unmarked raw access fails here.
    """

    RAW = re.compile(r"(window\.localStorage|localStorage|RAW)\.(getItem|setItem|removeItem)"
                     r"\(\s*'(d2r_\w+)'")

    def _fork_sets(self, board):
        lp = set(re.findall(r'"(d2r_\w+)"', re.search(
            r"window\._LP_FORKED = new Set\(\[(.*?)\]\)", board, re.S).group(1)))
        extra = set(re.findall(r"'(d2r_\w+)'", re.search(
            r"window\._WP_FORKED = new Set\(Array\.from\(window\._LP_FORKED\)\.concat\(\[(.*?)\]\)",
            board, re.S).group(1)))
        return lp, lp | extra

    def test_no_unrouted_access_to_a_forked_key(self):
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(repo, "bible.html"), encoding="utf-8") as fh:
            board = fh.read()
        lp, wp = self._fork_sets(board)
        # sanity: the sets must be real, or this gate silently passes on everything
        self.assertGreater(len(lp), 30, "the ladder fork set looks wrong — gate would be toothless")
        self.assertGreater(len(wp), len(lp), "the windows fork set must extend the ladder set")

        offenders = []
        for rel in ("bible.html", os.path.join("tv", "control_ui.html")):
            with open(os.path.join(repo, rel), encoding="utf-8") as fh:
                src = fh.read()
            for n, line in enumerate(src.split("\n"), 1):
                if "raw-ok:" in line:
                    continue
                for m in self.RAW.finditer(line):
                    if m.group(3) in wp:
                        offenders.append("%s:%d  %s.%s('%s')"
                                         % (rel, n, m.group(1), m.group(2), m.group(3)))
        self.assertEqual(
            offenders, [],
            "these touch a per-world key WITHOUT the router — this is the REG-069/075/076 family, "
            "and it leaks one person's progress onto another person's machine:\n  "
            + "\n  ".join(offenders)
            + "\nUse LSR.* (board) or lsFork() (console). If the raw access is deliberate — a "
              "migration that must name L·/W· explicitly — mark the line /* raw-ok: why */.")

    def test_the_marker_cannot_silence_the_whole_file(self):
        """A guard with an escape hatch needs its hatch bounded: `raw-ok` exempts ONE line, and the
        exemptions must stay few enough that nobody can wave the gate away wholesale."""
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        total = 0
        for rel in ("bible.html", os.path.join("tv", "control_ui.html")):
            with open(os.path.join(repo, rel), encoding="utf-8") as fh:
                total += sum(1 for ln in fh if "raw-ok:" in ln)
        self.assertLessEqual(
            total, 12,
            "%d raw-ok exemptions — the hatch is being used as a habit. Each one is a place the "
            "router does not protect; route them instead." % total)
        self.assertGreater(total, 0, "the deliberate migration markers vanished — did a rewrite "
                                     "drop them? The gate would now be untested against real raw code.")


class TestToolsCanReportTheirVerdict(unittest.TestCase):
    """v1480 — a tool whose verdict is its exit code must not die reporting it.

    Fourth instance of one bug: REG-044 (tv_diablo could not print its status lines), REG-054 (both
    suites were only green because PYTHONIOENCODING was set by hand off-screen — a plain run went
    red AND corrupted a tracked fixture), REG-077 (visual_lock_invariant and js_syntax_gate each
    PASSED, reached the success branch, then died inside `print("✅ …")`).

    This machine's console is Hebrew (cp1255) and cannot encode the check marks, arrows and box
    characters the tooling prints everywhere. The failure always lands in the dangerous direction:
    a CORRECT tree reports FAILURE, which teaches people to ignore the tool, and then the next real
    failure is ignored too. `tv/test_button_matrix.py` proves the cost — it died on encoding, and
    hidden underneath was a `^v8\\d\\d` version assertion that had been wrong since v900.

    So: any CLI script that prints non-ASCII must make its own output encoding-safe, rather than
    inherit safety from the operator's shell.
    """

    TV = os.path.dirname(os.path.abspath(__file__))
    REPO = os.path.dirname(TV)
    # These get their safety from a module they import, which installs it at import time.
    VIA_IMPORT = re.compile(r"^\s*(?:import|from)\s+(control_app|tv_diablo|console_safe)\b", re.M)

    def _scripts(self):
        import glob
        out = list(glob.glob(os.path.join(self.TV, "*.py")))
        out.append(os.path.join(self.REPO, "visual_lock_invariant.py"))
        return sorted(out)

    def test_every_cli_that_prints_non_ascii_is_encoding_safe(self):
        unsafe = []
        for path in self._scripts():
            with open(path, encoding="utf-8", errors="replace") as fh:
                src = fh.read()
            if "__main__" not in src:
                continue                                    # importable module, not an entry point
            if not re.search(r"[^\x00-\x7F]", src):
                continue                                    # pure ASCII output cannot hit this
            if "reconfigure" in src or self.VIA_IMPORT.search(src):
                continue
            unsafe.append(os.path.relpath(path, self.REPO))
        self.assertEqual(
            unsafe, [],
            "these print non-ASCII but never make stdout encoding-safe, so on a non-UTF-8 console "
            "they crash while REPORTING and a clean tree exits non-zero:\n  " + "\n  ".join(unsafe)
            + "\nAdd `from console_safe import enable; enable()` (see tv/console_safe.py).")

    def test_console_safe_never_raises(self):
        """The helper's whole job is to stop crashes, so it must not become a new source of them —
        including on stream objects that cannot be reconfigured at all."""
        sys.path.insert(0, self.TV)
        import console_safe
        import io as _io
        self.assertTrue(console_safe.enable(_io.TextIOWrapper(_io.BytesIO())))
        # a stream with no reconfigure(): reports False, raises nothing
        class Dumb:
            pass
        self.assertFalse(console_safe.enable(Dumb()))
        self.assertFalse(console_safe.enable(_io.StringIO()))
        console_safe.enable(None)          # tolerated, no exception


class TestNoOrphanSuite(unittest.TestCase):
    """v1483 — a test suite that nobody runs is not a test suite.

    `tv/test_routes.py` exited 1 for about a hundred versions and nothing said so (REG-079). It was
    not broken subtly — v1381.1 changed a rule and two tests kept asserting the old one — it was
    simply outside everyone's habit. It still passed 181 of its 183 assertions, which is the trap:
    a mostly-green orphan looks maintained.

    "The gate set" used to be something people carried in their heads and typed by hand, so it was
    different for every person and every session and a suite could fall out of it in silence. It is
    now a list in `tv/run_gates.py`, and this test makes falling out of it impossible.
    """

    def test_no_suite_defines_a_class_BELOW_unittest_main(self):
        """v1533 — the trap this repo already paid for once (v1457: 7 tests in test_control.py were
        defined below the guard and had NEVER run, while the suite reported OK). It has no automated
        check, so it is still live — I walked straight into it appending a class to
        test_chronicle_chain.py: 6 tests written, 0 defined, suite green.

        unittest.main() exits the interpreter. Anything after it is dead code that LOOKS like
        coverage, which is the most expensive kind of nothing."""
        here = os.path.dirname(os.path.abspath(__file__))
        bad = []
        for path in sorted(glob.glob(os.path.join(here, "test_*.py"))):
            with open(path, encoding="utf-8") as fh:
                src = fh.read()
            # anchor on the REAL guard, not the string: this very test's own docstring mentions
            # unittest.main(), and a naive find() matched that and flagged this file (caught on the
            # first run — a guard whose first victim is itself is not yet a guard)
            m = re.search(r'^if __name__ == ["\']__main__["\']:', src, re.M)
            if not m:
                continue
            tail = src[m.start():]
            if re.search(r"^class\s+\w+", tail, re.M):
                bad.append(os.path.basename(path))
        self.assertEqual(
            bad, [],
            "these suites define a test class AFTER unittest.main(), which exits the interpreter — "
            "every class below it is NEVER DEFINED and the suite still reports OK:\n  "
            + "\n  ".join(bad) + "\nMove the class above the `if __name__` guard.")

    def test_every_suite_is_in_the_gate_set(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "run_gates.py"), encoding="utf-8") as fh:
            runner = fh.read()
        suites = sorted(os.path.basename(p) for p in glob.glob(os.path.join(here, "test_*.py")))
        self.assertGreater(len(suites), 3, "suite discovery found almost nothing — check the glob")
        missing = [s for s in suites if s not in runner]
        self.assertEqual(
            missing, [],
            "these suites exist but no gate runs them, so they can rot for a hundred versions "
            "while still looking maintained (REG-079):\n  " + "\n  ".join(missing)
            + "\nAdd each to GATES in tv/run_gates.py, with a `why` saying what it protects.")

    def test_gate_set_names_only_things_that_exist(self):
        """The other direction: a gate pointing at a deleted file would 'skip' forever and quietly
        shrink the real coverage."""
        here = os.path.dirname(os.path.abspath(__file__))
        repo = os.path.dirname(here)
        sys.path.insert(0, here)
        import run_gates
        missing = []
        for g in run_gates.GATES:
            # v1614 — the last argv element is not always the file. A gate may pass a FLAG
            # (`extract_ui_icons.py --check`), and reading argv[-1] blindly reported the flag
            # itself as a missing file: a true guard failing on correct configuration, which is
            # the kind of red that teaches people to ignore the gate. Take the last argument that
            # is not an option instead.
            target = next((a for a in reversed(g.argv) if not a.startswith("-")), g.argv[-1])
            if not os.path.isfile(target):
                missing.append("%s -> %s" % (g.name, os.path.relpath(target, repo)))
        self.assertEqual(missing, [], "gates point at files that do not exist:\n  "
                                      + "\n  ".join(missing))

    def test_every_gate_says_what_it_protects(self):
        here = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, here)
        import run_gates
        silent = [g.name for g in run_gates.GATES if not (g.why or "").strip()]
        self.assertEqual(silent, [], "a gate with no `why` cannot be triaged when it goes red, and "
                                     "an untriageable gate is the one people start ignoring: %s"
                                     % ", ".join(silent))


class TestAFreshMachineStartsEmpty(unittest.TestCase):
    """v1484 — the promise a new PC makes, finally under test.

    Konyo: *"everyone should start fresh.. except my macbook one. like the chronicles and forges
    should be 0/0 that way new PC starts with its own profile and builds on it."*

    Every part of that promise has been enforced by hand until now — v1469 added the rule, v1478
    fixed the console that was ignoring it, and both were checked by launching the app and reading
    numbers off the screen. The one thing never checked automatically is the whole point: boot the
    REAL board on a machine that has never seen it, and confirm the chronicle is empty.

    This is the test that would have caught REG-076 on its own, without a user report.

    It boots `bible.html` in a virgin browser profile (no storage at all), lets it initialise, then
    re-opens the SAME profile on a probe page to read what the board actually wrote. Two loads
    rather than one because the board must be allowed to run its own first-boot path — deriving the
    machine, publishing the route, and applying (or correctly NOT applying) the grail seed.
    """

    def _browser(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import js_syntax_gate
        b = js_syntax_gate.find_browser()
        if not b:
            self.skipTest("no Chromium/Edge found — cannot boot the board")
        # v1490 — and skip when the browser cannot answer over loopback on this
        # machine: it would burn the full timeout and ERROR on an environment fact.
        if not js_syntax_gate.browser_can_load_localhost(b):
            self.skipTest(js_syntax_gate.NO_LOOPBACK + " — " + "cannot boot the board")
        return b, js_syntax_gate

    def test_a_never_seen_machine_has_an_empty_chronicle(self):
        browser, gate = self._browser()
        repo = gate.REPO
        probe = os.path.join(repo, "_freshpc_probe.html")
        # Reads the raw namespaces directly: the point is to verify what is ON DISK for this
        # machine's world, independent of any helper that might itself be routing wrongly.
        with open(probe, "w", encoding="utf-8") as fh:
            fh.write(
                "<!doctype html><meta charset=utf-8><pre id=o></pre><script>\n"
                "function g(k){ try { return localStorage.getItem(k); } catch(e){ return null; } }\n"
                "function count(raw){ if (raw==null) return 0;\n"
                "  try { var v = JSON.parse(raw);\n"
                "    if (Array.isArray(v)) return v.length;\n"
                "    if (v && typeof v === 'object') return Object.keys(v).length;\n"
                "  } catch(e){}\n"
                "  return -1; }\n"
                "var out = { machine: g('d2r_activeMachine'), source: g('d2r_machineSource'),\n"
                "  route: g('d2r_lsrRoute') ? JSON.parse(g('d2r_lsrRoute')).m : null,\n"
                "  W_foundLog: count(g('W\\u00b7d2r_foundLog')),\n"
                "  W_rwMade:   count(g('W\\u00b7d2r_rwMade')),\n"
                "  W_setPieces:count(g('W\\u00b7d2r_setPieces')),\n"
                "  bare_foundLog: count(g('d2r_foundLog')) };\n"
                "document.getElementById('o').textContent = 'RESULT:' + JSON.stringify(out);\n"
                "</script>")
        srv, port = gate._serve(repo)
        try:
            with tempfile.TemporaryDirectory() as profile:
                # Observed once in a full-suite run: a cold Chromium start under contention blew a
                # 180s budget and the test ERRORed. That is latency in the harness, not a verdict
                # about the board, so it gets one retry — and if it still cannot run, it says the
                # result is UNKNOWN rather than inventing either colour. A flaky test that cries
                # wolf gets muted, and a muted test is REG-079 all over again.
                timed_out = []

                # v1490 — BOUNDED. The old budget was 300s per attempt × 2 attempts × 2 loads =
                # up to 20 MINUTES, and this suite is in the pre-push gate: measured on Konyo's
                # Mac, a stalled `Chrome --headless=old` sat here past 10 minutes and would have
                # held a push hostage before skipping and proving nothing anyway. The page is
                # given 9s of VIRTUAL time, so a load that has not answered in 45s of real time
                # is stuck, not slow — waiting 300 more seconds cannot change the verdict.
                # Also: subprocess.run's timeout kills the launcher, NOT the renderer helpers
                # Chrome forks, so a timed-out attempt used to leave orphan Chrome processes
                # burning CPU (found two on this machine). Own the whole process group and kill it.
                # v1490 — HEADLESS MODE FIRST, then a bound. Measured on Konyo's Mac (Chrome 150):
                # `--headless=old` HANGS — not on the board, on a 40-byte hello-world page. So this
                # test never actually ran here; it burned the budget and skipped, and the skip read
                # as "the machine is busy" rather than "this flag is dead on this Chrome".
                # `--headless=new` returns instantly on the same binary, so we ask for it FIRST and
                # keep old as the fallback for a Chrome too old to know it. Recovering the run
                # matters more than the timeout: a test that always skips is not coverage.
                _MODES = ["--headless=new", "--headless=old"]
                # The page gets 9s of VIRTUAL time, so a load that has not answered in 45s of real
                # time is stuck, not slow — the old 300s × 2 attempts × 2 loads was up to 20 MINUTES
                # with this suite sitting in the pre-push gate.
                LOAD_TIMEOUT_S = 45
                mode_ok = []   # the mode that answered — the second load reuses it, no re-probing

                def load(rel, budget=9000):
                    for mode in (mode_ok or _MODES):
                        proc = subprocess.Popen(
                            [browser, mode, "--disable-gpu", "--no-sandbox",
                             "--user-data-dir=%s" % profile,
                             "--blink-settings=imagesEnabled=false",
                             "--virtual-time-budget=%d" % budget, "--dump-dom",
                             "http://127.0.0.1:%d/%s" % (port, rel)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True)   # its own group, so the kill reaches the helpers
                        try:
                            out, err = proc.communicate(timeout=LOAD_TIMEOUT_S)
                        except subprocess.TimeoutExpired:
                            # subprocess timeouts kill the launcher, NOT the renderer helpers Chrome
                            # forks — that left orphan Chrome processes burning CPU (two found on
                            # this machine). Own the group and take the whole tree down.
                            try:
                                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                            except Exception:
                                proc.kill()
                            try:
                                proc.communicate(timeout=10)
                            except Exception:
                                pass
                            continue
                        if not mode_ok:
                            mode_ok.append(mode)
                        return subprocess.CompletedProcess(
                            proc.args, proc.returncode,
                            (out or b"").decode("utf-8", "replace"),
                            (err or b"").decode("utf-8", "replace"))
                    timed_out.append(rel)
                    return None

                first = load("bible.html")              # first boot: the board initialises itself
                # v1490 — if the board never loaded there is nothing for the probe to read, and a
                # second doomed load only doubles the stall. Measured: Chrome answers a hello-world
                # page instantly in --headless=new but does NOT return for bible.html + --dump-dom
                # on this Mac, so the worst case is real and worth short-circuiting.
                r = load("_freshpc_probe.html", 4000) if first is not None else None
                if timed_out or r is None:
                    self.skipTest(
                        "the browser did not finish loading %s within %ds in ANY headless mode "
                        "(%s), so this run proves NOTHING about the fresh-machine promise either "
                        "way. The page gets 9s of VIRTUAL time, so this is a stuck browser, not a "
                        "slow one — check that %s can run headless here."
                        % ((timed_out or ["probe"])[0], LOAD_TIMEOUT_S, ", ".join(_MODES), browser))
                blob = (r.stdout or "") + (r.stderr or "")
        finally:
            srv.shutdown()
            srv.server_close()
            try:
                os.remove(probe)
            except OSError:
                pass

        m = re.search(r"RESULT:(\{.*?\})</pre>", blob, re.S)
        self.assertIsNotNone(m, "the probe never reported — the board may not have booted:\n"
                                + blob[-800:])
        got = json.loads(m.group(1))

        # A headless Chromium on this platform reports a desktop UA; if it derived 'mac' the
        # premise of the test is gone and a silent pass would be worthless.
        if got["machine"] != "windows":
            self.skipTest("this browser derived machine=%r, so there is no W· world to check"
                          % got["machine"])
        self.assertEqual(got["source"], "auto",
                         "a machine nobody has clicked through must be auto-derived, not 'user'")
        # v1501 — v1499 replaced the route's mac/windows vocabulary with owner/guest, because the
        # world is now decided by which INSTALL holds the claim rather than by the OS. The PROMISE
        # this test defends is unchanged and is the whole point: a machine nobody has claimed starts
        # empty. An unclaimed machine is a GUEST.
        self.assertIn(got["route"], ("guest", "windows"),
                      "an unclaimed machine must publish a non-owner route (v1499: 'guest'; "
                      "pre-v1499 builds said 'windows')")
        for key in ("W_foundLog", "W_rwMade", "W_setPieces"):
            self.assertEqual(
                got[key], 0,
                "%s = %r on a machine that has never been used. A brand-new PC must start at 0/0 "
                "— this is the seed leaking into a fresh world, which is what Konyo asked for and "
                "what REG-076 broke." % (key, got[key]))
        self.assertEqual(
            got["bare_foundLog"], 0,
            "the OWNER's namespace was written on a machine that is not the owner's; a fresh PC "
            "must not touch the bare world at all")


class TestForgeCountsAddUp(unittest.TestCase):
    """v1485 — pin the arithmetic Konyo actually asked about.

    He sent a screenshot: *"how come for forges ONESTEP is 91 … if there is 99 forges to create?
    doesnt that counter it? i need this synced and accurate."* The answer was the eight ladder-only
    runewords being filtered out of a non-ladder world — a real, correct rule that nobody had told
    the count about. v1475 half-fixed it (four call sites, but the counts gate on a differently
    named predicate — REG-075) and v1477 finished it, verified live at ALL 103 · ONE STEP 99 ·
    CRAFTS 4.

    "Verified live" means someone looked at a screen once. These numbers are load-bearing for the
    user's trust in the whole Forge, and every input to them is a plain data structure, so the
    relationship is worth pinning: 99 runewords + 4 craft types = the 103 the UI promises, with
    exactly 8 of those runewords ladder-only.

    This does not re-implement the forge logic — it pins the INPUTS, so a silent edit to the
    dictionaries (a dropped runeword, a new craft, a ladder word added or removed) has to come here
    and state its intent instead of quietly moving a number the user reads as truth.
    """

    @classmethod
    def setUpClass(cls):
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(repo, "bible.html"), encoding="utf-8") as fh:
            cls.src = fh.read()

    def _brace_body(self, start_pat):
        m = re.search(start_pat, self.src)
        self.assertIsNotNone(m, "could not find %s — the Forge inputs moved" % start_pat)
        i = self.src.index("{", m.start())
        depth = 0
        for j in range(i, len(self.src)):
            if self.src[j] == "{":
                depth += 1
            elif self.src[j] == "}":
                depth -= 1
                if depth == 0:
                    return self.src[i:j + 1]
        self.fail("unbalanced braces after %s" % start_pat)

    def test_there_are_99_runewords(self):
        body = self._brace_body(r"RUNEWORD_TIP\s*=\s*\{")
        names = re.findall(r'"([^"]+)"\s*:', body)
        self.assertEqual(len(names), 99,
                         "RUNEWORD_TIP holds %d runewords, not 99. The Forge tells the user "
                         "'ONE STEP 99'; if this changed on purpose, change the promise too."
                         % len(names))
        self.assertEqual(len(set(names)), len(names),
                         "a runeword name appears twice — the count would double-report it")

    def test_exactly_eight_runewords_are_ladder_only(self):
        m = re.search(r"const _RW_LADDER_ONLY = (\{.*?\});", self.src)
        self.assertIsNotNone(m, "_RW_LADDER_ONLY moved")
        ladder = re.findall(r'"([^"]+)"\s*:', m.group(1))
        self.assertEqual(
            sorted(ladder),
            ["Bulwark", "Cure", "Ground", "Hearth", "Hysteria", "Mania", "Metamorphosis", "Temper"],
            "the ladder-only set changed. These eight are exactly why ONE STEP read 91 instead of "
            "99 in a non-ladder world; the Forge now includes them deliberately, so any change "
            "here moves a number the user checks.")

    def test_every_ladder_only_word_is_a_real_runeword(self):
        """A typo here would silently stop filtering that word and quietly shift the count."""
        body = self._brace_body(r"RUNEWORD_TIP\s*=\s*\{")
        names = set(re.findall(r'"([^"]+)"\s*:', body))
        m = re.search(r"const _RW_LADDER_ONLY = (\{.*?\});", self.src)
        ladder = re.findall(r'"([^"]+)"\s*:', m.group(1))
        unknown = [w for w in ladder if w not in names]
        self.assertEqual(unknown, [], "ladder-only names that are not runewords: %s" % unknown)

    def test_ninety_nine_runewords_plus_four_crafts_is_the_103_the_ui_promises(self):
        body = self._brace_body(r"(?:const|var|let)\s+CRAFTS\s*=\s*\[?\s*\{")
        # CRAFTS is a list of objects each carrying a `key`; count the top-level entries by key.
        m = re.search(r"(?:const|var|let)\s+CRAFTS\s*=\s*(\[.*?\n\s*\];)", self.src, re.S)
        self.assertIsNotNone(m, "CRAFTS moved — the craft type count cannot be checked")
        crafts = re.findall(r"\bkey\s*:\s*['\"]([^'\"]+)['\"]", m.group(1))
        self.assertEqual(len(crafts), 4,
                         "CRAFTS holds %d types (%s), not the 4 the Forge reports as CRAFTS 4"
                         % (len(crafts), crafts))
        rw = len(re.findall(r'"([^"]+)"\s*:', self._brace_body(r"RUNEWORD_TIP\s*=\s*\{")))
        self.assertEqual(rw + len(crafts), 103,
                         "%d runewords + %d craft types = %d, but the Forge shows ALL 103"
                         % (rw, len(crafts), rw + len(crafts)))


class TestProfileSigil(unittest.TestCase):
    """v1486 — the chip that answers "whose console am I in".

    Konyo: *"how can there like really be a unique generated login symbol logo for a profile so my
    cuzin knows its his console and hes logged into his profile.. and same for me.. how can we
    compare the differences?"*

    v1465 built it and left a comment saying `window.TVD_SIGIL` is "exposed so tests/console can
    assert determinism" — and then no test was ever written. So the three properties the feature
    rests on have never been checked:

      * STABLE   — the same install shows the same sigil forever, or it cannot mean "this is mine"
      * DISTINCT — two installs should look different, or it cannot mean "this is NOT yours"
      * HONEST   — the colour and the name must agree

    That last one is not hypothetical. The first cut hashed the adjective and the hue separately
    and produced "AMBER ANVIL" rendered in blue, which defeats the entire point: the whole job of
    the chip is that a colour seen across a room and a name said out loud describe the same
    console. The fix was to index-lock them, and nothing has been pinning that since.

    Runs the SHIPPED generator in a real JS engine rather than a Python re-implementation — a
    re-implementation would agree with itself while disagreeing with the product.
    """

    IDS = ["konyo-macbook", "cousin-pc", "adi-windows", "windows-pc-2"]

    def _extract(self, src, needle):
        start = src.index(needle)
        i, depth = src.index("{", start), 0
        for j in range(i, len(src)):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    return src[start:j + 1]
        self.fail("could not close %s" % needle)

    def test_sigils_are_stable_distinct_and_index_locked(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import js_syntax_gate
        browser = js_syntax_gate.find_browser()
        if not browser:
            self.skipTest("no Chromium/Edge found — cannot execute the sigil generator")
        # v1490 — and skip when the browser cannot answer over loopback on this
        # machine: it would burn the full timeout and ERROR on an environment fact.
        if not js_syntax_gate.browser_can_load_localhost(browser):
            self.skipTest(js_syntax_gate.NO_LOOPBACK + " — " + "cannot execute the sigil generator")
        repo = js_syntax_gate.REPO
        with open(os.path.join(repo, "tv", "control_ui.html"), encoding="utf-8") as fh:
            src = fh.read()

        # the three tables + the two functions, lifted verbatim from the shipped file
        parts = [src[src.index("  var GLYPHS = ["):src.index("  function h32(")],
                 self._extract(src, "  function h32("),
                 self._extract(src, "  function sigilFor(")]
        # 200 synthetic installs to measure collisions, plus the named ones
        ids = self.IDS + ["install-%d" % i for i in range(200)]
        harness = (
            "<!doctype html><meta charset=utf-8><pre id=o></pre><script>\n"
            + "\n".join(parts) + "\n"
            "var A_LEN = A.length, IDS = " + json.dumps(ids) + ";\n"
            "var res = {};\n"
            "IDS.forEach(function(id){\n"
            "  var s1 = sigilFor(id), s2 = sigilFor(id);\n"
            "  res[id] = { s: s1, stable: JSON.stringify(s1) === JSON.stringify(s2),\n"
            "              hueIdx: HUES.indexOf(s1.hue), adjIdx: A.indexOf(s1.name.split(' ')[0]) };\n"
            "});\n"
            "res._empty = sigilFor('');\n"
            "document.getElementById('o').textContent = 'RESULT:' + JSON.stringify(res);\n"
            "</script>")
        tmp = os.path.join(repo, "_sigil_probe.html")
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(harness)
        srv, port = js_syntax_gate._serve(repo)
        try:
            with tempfile.TemporaryDirectory() as prof:
                r = _dump_dom(browser, "http://127.0.0.1:%d/_sigil_probe.html" % port)
                if r is None:
                    self.skipTest("Chrome never answered --dump-dom over http on this "
                                  "machine (js_syntax_gate reports the same); a probe "
                                  "that could not run proves nothing")
            blob = (r.stdout or "") + (r.stderr or "")
        finally:
            srv.shutdown()
            srv.server_close()
            try:
                os.remove(tmp)
            except OSError:
                pass

        m = re.search(r"RESULT:(\{.*?\})</pre>", blob, re.S)
        self.assertIsNotNone(m, "the sigil probe never reported:\n" + blob[-800:])
        got = json.loads(m.group(1))

        self.assertIsNone(got.pop("_empty"),
                          "an install with no id must yield NO sigil — a chip that renders for an "
                          "unknown identity is claiming to identify something it cannot")

        for ident, row in got.items():
            self.assertTrue(row["stable"], "%s produced two different sigils in one run" % ident)
            # HONEST: colour and word are one decision, not two
            self.assertEqual(
                row["hueIdx"], row["adjIdx"],
                "%s renders %r in hue index %d but its adjective is index %d — this is the "
                "'AMBER ANVIL in blue' bug the index-lock exists to prevent. A colour seen across "
                "a room and a name said out loud must describe the same console."
                % (ident, row["s"]["name"], row["hueIdx"], row["adjIdx"]))
            self.assertRegex(row["s"]["code"], r"^[0-9A-F]{4}$",
                             "%s has a malformed tiebreak code %r" % (ident, row["s"]["code"]))

        # DISTINCT: the four real machines must not collide with each other at all
        named = [json.dumps(got[i]["s"], sort_keys=True) for i in self.IDS]
        self.assertEqual(len(set(named)), len(named),
                         "two of Konyo's own machines share a sigil, so the chip cannot tell him "
                         "whose console he is looking at: %s"
                         % [got[i]["s"]["name"] for i in self.IDS])

        # and across 200 installs, full-identity collisions must stay rare
        allsig = [json.dumps(r["s"], sort_keys=True) for r in got.values()]
        dupes = len(allsig) - len(set(allsig))
        self.assertLessEqual(
            dupes, len(allsig) // 20,
            "%d/%d installs collide on the FULL sigil (glyph+name+code). The chip stops "
            "distinguishing consoles well before that." % (dupes, len(allsig)))


class TestLauncherStaysLaunchable(unittest.TestCase):
    """v1487 — the launcher is the one file whose failure looks like "the app is gone".

    The bug that started this whole run was Konyo double-clicking the TV DIABLO icon and getting
    two black terminal flashes and nothing else. The launcher is the single point where a mistake
    presents as the product not existing — there is no error dialog, no log the user thinks to
    open, just an icon that does nothing. Both surfaces get a syntax gate (v1476); the launcher
    never got one.

    Two invariants, both of which have already cost a session:

    ENCODING — the file is ASCII with a UTF-8 BOM. PowerShell 5.1 decides a BOM-less file's
    encoding by the system codepage, and on this machine that is Hebrew cp1255. A single smart
    quote or box-drawing character then decodes to mojibake, and the failure surfaces far from the
    character that caused it. The file was ASCII-cleaned by hand once; nothing has held it since.

    SYNTAX — a parse error means the icon does nothing at all. Checked with PowerShell's own
    parser, for the same reason the JS gate uses a real browser: only the actual engine gets to
    decide what parses.
    """

    PS1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "start_tvd_win.ps1")

    def test_launcher_is_ascii_with_a_bom(self):
        with open(self.PS1, "rb") as fh:
            raw = fh.read()
        self.assertTrue(
            raw.startswith(b"\xef\xbb\xbf"),
            "start_tvd_win.ps1 lost its UTF-8 BOM. Without it PowerShell 5.1 falls back to the "
            "system codepage (Hebrew cp1255 here), so any non-ASCII byte decodes to mojibake and "
            "fails somewhere far from its cause.")
        bad = [(i, raw[i]) for i in range(3, len(raw)) if raw[i] > 127]
        self.assertEqual(
            bad, [],
            "%d non-ASCII byte(s) in the launcher, first at offset %s. Keep it plain ASCII: this "
            "file runs before anything can report an error, so a decoding problem here shows up as "
            "an icon that does nothing." % (len(bad), bad[0][0] if bad else "-"))

    def test_launcher_parses_in_powershell(self):
        if not sys.platform.startswith("win"):
            self.skipTest("PowerShell parser is Windows-only")
        exe = shutil.which("powershell") or shutil.which("pwsh")
        if not exe:
            self.skipTest("no PowerShell on PATH — cannot verify launcher syntax")
        script = (
            "$errs = $null; $toks = $null; "
            "[void][System.Management.Automation.Language.Parser]::ParseFile("
            "'%s', [ref]$toks, [ref]$errs); "
            "if ($errs -and $errs.Count) { $errs | ForEach-Object { "
            "'PARSE_ERROR: ' + $_.Extent.StartLineNumber + ': ' + $_.Message } } "
            "else { 'PARSE_OK' }" % self.PS1.replace("'", "''")
        )
        r = subprocess.run([exe, "-NoProfile", "-NonInteractive", "-Command", script],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        out = (r.stdout or "") + (r.stderr or "")
        self.assertIn("PARSE_OK", out,
                      "the launcher does not parse — the desktop icon would do NOTHING:\n" + out)


class TestTheFourWorldsNeverBleed(unittest.TestCase):
    """v1488 — the routing table itself, exercised rather than read.

    Everything Konyo asked for about profiles reduces to one table:

        OWNER   main = bare      OWNER   ladder = L·
        THIS PC main = W·        THIS PC ladder = WL·

    …with a deliberate asymmetry: only ACCOUNT state forks. UI preferences (active tab, dock, sort
    orders) match no fork set and stay bare everywhere, which is what makes every machine LOOK
    identical while holding different data. And on Windows the chronicle family forks to `W·` on
    BOTH profiles, because the cousin's main and ladder share the COUSIN's grail.

    That table is four lines of code and has produced three separate leaks (REG-069, REG-075,
    REG-076), every one of which was invisible to a code reading. So this executes the SHIPPED
    `LSR.key()` across all four worlds and checks the properties that actually matter, rather than
    checking that the source still looks the way someone remembers.
    """

    def test_key_routing_is_isolated_where_it_must_be_and_shared_where_it_must_be(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import js_syntax_gate
        browser = js_syntax_gate.find_browser()
        if not browser:
            self.skipTest("no Chromium/Edge found — cannot execute LSR.key")
        # v1490 — and skip when the browser cannot answer over loopback on this
        # machine: it would burn the full timeout and ERROR on an environment fact.
        if not js_syntax_gate.browser_can_load_localhost(browser):
            self.skipTest(js_syntax_gate.NO_LOOPBACK + " — " + "cannot execute LSR.key")
        repo = js_syntax_gate.REPO
        with open(os.path.join(repo, "bible.html"), encoding="utf-8") as fh:
            board = fh.read()

        lp = re.search(r"window\._LP_FORKED = new Set\(\[.*?\]\);", board, re.S).group(0)
        wp = re.search(r"window\._WP_FORKED = new Set\(Array\.from\(window\._LP_FORKED\)"
                       r"\.concat\(\[.*?\]\)\);", board, re.S).group(0)
        keyfn = re.search(r"  function key\(k\)\{.*?\n  \}", board, re.S).group(0)

        probe = os.path.join(repo, "_worlds_probe.html")
        with open(probe, "w", encoding="utf-8") as fh:
            fh.write(
                "<!doctype html><meta charset=utf-8><pre id=o></pre><script>\n"
                "window._LP_FORKED = null; window._WP_FORKED = null;\n"
                + lp + "\n" + wp + "\n" + keyfn + "\n"
                # v1501 — v1499 routes on the RESOLVED PREFIXES (window._D2R_PFX / _D2R_LPFX), not on
                # D2R_MACHINE, so setting the old globals alone produced 'undefined' + key. Each world
                # is now expressed as the pair of prefixes the board would publish for it, which is
                # exactly what every other surface consumes from d2r_lsrRoute.v2.
                "var WORLDS = [['mac','main','','L\u00b7'],['mac','ladder','','L\u00b7'],"
                "['windows','main','W\u00b7','WL\u00b7'],['windows','ladder','W\u00b7','WL\u00b7']];\n"
                # a forked ACCOUNT key, a windows-only CHRONICLE key, and a bare UI PREFERENCE
                "var SAMPLES = ['d2r_owned','d2r_foundLog','d2r_activeTab'];\n"
                "var res = {};\n"
                "WORLDS.forEach(function(w){\n"
                "  window.D2R_MACHINE = w[0]; window.D2R_PROFILE = w[1];\n"
                "  window._D2R_OWNER = (w[0] === 'mac'); window._D2R_PFX = w[2]; window._D2R_LPFX = w[3];\n"
                "  SAMPLES.forEach(function(k){ res[w[0]+'/'+w[1]+'|'+k] = key(k); });\n"
                "});\n"
                "document.getElementById('o').textContent = 'RESULT:' + JSON.stringify(res);\n"
                "</script>")
        srv, port = js_syntax_gate._serve(repo)
        try:
            with tempfile.TemporaryDirectory() as prof:
                r = _dump_dom(browser, "http://127.0.0.1:%d/_worlds_probe.html" % port)
                if r is None:
                    self.skipTest("Chrome never answered --dump-dom over http on this "
                                  "machine (js_syntax_gate reports the same); a probe "
                                  "that could not run proves nothing")
            blob = (r.stdout or "") + (r.stderr or "")
        finally:
            srv.shutdown()
            srv.server_close()
            try:
                os.remove(probe)
            except OSError:
                pass

        m = re.search(r"RESULT:(\{.*?\})</pre>", blob, re.S)
        self.assertIsNotNone(m, "the worlds probe never reported:\n" + blob[-800:])
        got = json.loads(m.group(1))
        DOT = "·"

        # 1) ACCOUNT STATE: all four worlds must land on four DIFFERENT keys.
        owned = [got["%s|d2r_owned" % w] for w in
                 ("mac/main", "mac/ladder", "windows/main", "windows/ladder")]
        self.assertEqual(owned, ["d2r_owned", "L%sd2r_owned" % DOT,
                                 "W%sd2r_owned" % DOT, "WL%sd2r_owned" % DOT])
        self.assertEqual(len(set(owned)), 4,
                         "two worlds share an account key, so one person's progress is another "
                         "person's progress: %s" % owned)

        # 2) UI PREFERENCES: bare in every world, or the machines stop looking identical.
        tabs = [got["%s|d2r_activeTab" % w] for w in
                ("mac/main", "mac/ladder", "windows/main", "windows/ladder")]
        self.assertEqual(set(tabs), {"d2r_activeTab"},
                         "a UI preference got forked (%s). v663 did this and the cousin's shell "
                         "rendered structurally different; only ACCOUNT state may fork." % tabs)

        # 3) THE CHRONICLE ASYMMETRY: shared across the owner's two accounts, isolated per machine.
        self.assertEqual(got["mac/main|d2r_foundLog"], "d2r_foundLog")
        self.assertEqual(got["mac/ladder|d2r_foundLog"], "d2r_foundLog",
                         "the owner's main and ladder must share ONE grail chronicle (v949)")
        self.assertEqual(got["windows/main|d2r_foundLog"], "W%sd2r_foundLog" % DOT)
        self.assertEqual(got["windows/ladder|d2r_foundLog"], "W%sd2r_foundLog" % DOT,
                         "the cousin's main and ladder must share the COUSIN's grail — and it must "
                         "never be the owner's")
        self.assertNotEqual(got["windows/main|d2r_foundLog"], got["mac/main|d2r_foundLog"],
                            "the cousin's chronicle resolved to the owner's key — REG-076 exactly")


class TestVersionStampsAgree(unittest.TestCase):
    """v1489 — four files carry the version, and nothing has ever checked they say the same thing.

    The version lives in the board's `D2R_BUILD`, `control_app.py`'s `/api/status`, `tv_diablo.py`'s
    `VERSION`, and `tv/WINDOWS_SHIP.json`. Bumping by hand is four chances to miss one, and the
    result is not cosmetic: `test_button_matrix` compares the LIVE app to the ship manifest, so a
    half-bumped tree reads as "the running app is a different build than the tree you are testing"
    and sends the next person hunting a phantom.

    This checks the tree agrees with ITSELF. The live-vs-manifest comparison stays where it is —
    that one is about a stale running process, which is a different question.
    """

    @classmethod
    def setUpClass(cls):
        cls.tv = os.path.dirname(os.path.abspath(__file__))
        cls.repo = os.path.dirname(cls.tv)

    def _read(self, rel):
        with open(os.path.join(self.repo, rel), encoding="utf-8") as fh:
            return fh.read()

    def test_all_four_stamps_are_the_same_version(self):
        # v1616.1 — POINT RELEASES ARE REAL VERSIONS. `v\d+` rejected v1616.1 outright, so the
        # stamp read as MISSING and this guard fired on a correctly-stamped tree. It disagreed
        # with tv/bump_version.py, which deliberately accepts `^v\d+(\.\d+)*$` — and the repo
        # has shipped point releases for a thousand versions (v342.8, v665.3, v693.2). Two
        # guards holding different definitions of "a version" is the actual defect.
        VER = r"(v\d+(?:\.\d+)*)"
        board = re.search(r"window\.D2R_BUILD = \{ id:'" + VER + "'", self._read("bible.html"))
        control = re.search(r'"ver": "' + VER + '"', self._read(os.path.join("tv", "control_app.py")))
        agent = re.search(r'VERSION = "' + VER + '"', self._read(os.path.join("tv", "tv_diablo.py")))
        with open(os.path.join(self.tv, "WINDOWS_SHIP.json"), encoding="utf-8") as fh:
            ship = json.load(fh).get("ver")

        for label, m in (("bible.html D2R_BUILD", board), ("control_app /api/status", control),
                         ("tv_diablo VERSION", agent)):
            self.assertIsNotNone(m, "%s no longer carries a parseable version stamp" % label)

        stamps = {"bible.html D2R_BUILD": board.group(1),
                  "control_app /api/status": control.group(1),
                  "tv_diablo VERSION": agent.group(1),
                  "tv/WINDOWS_SHIP.json": ship}
        self.assertEqual(
            len(set(stamps.values())), 1,
            "the four version stamps disagree, so the tree is half-bumped: %s. Use "
            "tv/bump_version.py, which writes all four and verifies each one landed."
            % json.dumps(stamps, indent=2))

    def test_the_board_note_has_no_apostrophe(self):
        """`D2R_BUILD.note` is a single-quoted JS literal. An apostrophe terminates it early and
        throws a SyntaxError that blanks the whole 37k-line board — which happened in v1478."""
        m = re.search(r"window\.D2R_BUILD = \{ id:'v\d+(?:\.\d+)*', name:'([^']*)', date:'[^']*', "
                      r"note:'(.*)' \};", self._read("bible.html"))
        self.assertIsNotNone(m, "D2R_BUILD is not in the expected single-quoted shape — if it was "
                                "reformatted, this guard needs to follow it")
        for label, text in (("name", m.group(1)), ("note", m.group(2))):
            self.assertNotIn("'", text,
                             "an apostrophe in D2R_BUILD.%s would terminate the literal and blank "
                             "the board" % label)

    def test_the_bump_tool_refuses_an_apostrophe(self):
        sys.path.insert(0, self.tv)
        import bump_version
        with self.assertRaises(SystemExit,
                               msg="the tool must refuse a note that would blank the board"):
            bump_version.bump("v9999", "test", "someone else's chronicle")


class TestV1493JournalIsolation(unittest.TestCase):
    """v1493 — TV_SESSIONS must isolate EVERY journal site, reads and writes alike.

    It existed since v877 and exactly one of eleven sites honoured it. A harness that set it believed
    it was isolated while the receipts stream read the REAL journal: a fixture run with four seeded
    rows came back with 25 receipts of Konyo's actual session data. Five of the unrouted sites APPEND,
    so an isolated-looking test could have written into the record of his real farming nights."""

    def test_every_site_resolves_through_one_path(self):
        src = open(ca.__file__, encoding="utf-8").read()
        built = src.count('os.path.join(HERE, "sessions.jsonl")')
        self.assertEqual(built, 1,
                         "EXACTLY ONE site may construct the journal path (the resolver itself); "
                         "found %d — every extra one is a hole in TV_SESSIONS isolation" % built)
        self.assertIn("def _journal_path():", src, "and that one site is the resolver")
        self.assertGreater(src.count("_journal_path()"), 5, "every reader/writer goes through it")
        # v1709 — the generation ring used HERE/sessions (no .jsonl) and so
        # escaped the v1493 count. Export + delete + doctor gens now derive
        # from _journal_ring() / _journal_path().
        # The ring hole was join(HERE, "sessions") + ".jsonl" — that is NOT a
        # prefix of the resolver's join(HERE, "sessions.jsonl") (quote lands
        # after .jsonl). Zero of the stem form is the gate.
        self.assertEqual(src.count('os.path.join(HERE, "sessions")'), 0,
                         "no site may build HERE/sessions — that is the ring hole")
        self.assertIn("def _journal_ring():", src)

    def test_tv_sessions_redirects_reads_and_the_real_journal_is_untouched(self):
        real = os.path.join(os.path.dirname(ca.__file__), "sessions.jsonl")
        before = (os.path.getsize(real), os.path.getmtime(real)) if os.path.isfile(real) else None
        tmp = tempfile.mkdtemp()
        fixture = os.path.join(tmp, "sessions.jsonl")
        row = {"ts": 1, "completedTs": 1000, "lane": "deep", "scene": "stash", "area": "Harrogath",
               "names": ["Isolation Canary"], "sessionId": "s_iso", "frameId": "f_iso",
               "gatePass": True, "gateReason": "quorum>=2"}
        with open(fixture, "w", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        old_env = os.environ.get("TV_SESSIONS")
        saved_cache = ca.__dict__.get("_RECEIPTS_CACHE", _MISSING)
        try:
            os.environ["TV_SESSIONS"] = fixture
            ca.__dict__.pop("_RECEIPTS_CACHE", None)
            self.assertEqual(ca._journal_path(), fixture)
            names = [(r.get("refs") or {}).get("itemName") for r in ca._receipts_stream()]
            self.assertIn("Isolation Canary", names, "reads must come from the fixture")
            self.assertEqual(len(ca._kai_journal_rows()), 1,
                             "the fixture has ONE row; more means the real journal leaked in")
        finally:
            if old_env is None:
                os.environ.pop("TV_SESSIONS", None)
            else:
                os.environ["TV_SESSIONS"] = old_env
            if saved_cache is _MISSING:
                ca.__dict__.pop("_RECEIPTS_CACHE", None)
            else:
                ca._RECEIPTS_CACHE = saved_cache
            shutil.rmtree(tmp, ignore_errors=True)
        if before is not None:
            self.assertEqual((os.path.getsize(real), os.path.getmtime(real)), before,
                             "the REAL journal must not be read-stamped or appended to by a test")

    def test_journal_ring_follows_tv_sessions(self):
        tmp = tempfile.mkdtemp()
        fixture = os.path.join(tmp, "sessions.jsonl")
        old_env = os.environ.get("TV_SESSIONS")
        try:
            os.environ["TV_SESSIONS"] = fixture
            ring = ca._journal_ring()
            self.assertEqual(ring[-1], fixture)
            self.assertTrue(all(p.startswith(tmp) for p in ring), ring)
            self.assertFalse(any("/tv/sessions" in p.replace("\\", "/") and tmp not in p
                                 for p in ring), ring)
        finally:
            if old_env is None:
                os.environ.pop("TV_SESSIONS", None)
            else:
                os.environ["TV_SESSIONS"] = old_env
            shutil.rmtree(tmp, ignore_errors=True)


class TestV1496MachineNickname(unittest.TestCase):
    """v1496 — naming a machine, and the fleet answer. Konyo: "can it just be more nicknamed? like
    more UX and friendlier... i want to have a tracker for whose logged in and when."."""

    def test_nickname_round_trips_without_touching_the_identity(self):
        tmp = tempfile.mkdtemp()
        old_path = ca.IDENTITY_PATH
        try:
            ca.IDENTITY_PATH = os.path.join(tmp, ".tvd_identity.json")
            born = ca.install_identity()
            self.assertTrue(born.get("id"), "an install must mint an id")
            named = ca.set_install_nickname("Konyo's MacBook")
            self.assertEqual(named["nickname"], "Konyo's MacBook")
            self.assertEqual(named["id"], born["id"], "naming a machine must NOT change its identity")
            self.assertEqual(ca.install_identity()["nickname"], "Konyo's MacBook", "and it must persist")
            # clearing falls back to the hostname, it does not invent one
            self.assertEqual(ca.set_install_nickname("")["nickname"], "")
            self.assertEqual(ca.install_identity()["id"], born["id"])
            # a runaway name can never bloat the beacon
            self.assertLessEqual(len(ca.set_install_nickname("x" * 200)["nickname"]), 40)
        finally:
            ca.IDENTITY_PATH = old_path
            shutil.rmtree(tmp, ignore_errors=True)

    def test_footer_fallback_is_not_a_stale_version(self):
        """v1709 — missing st.ver must not paint v927 (776 versions behind)."""
        ui = open(os.path.join(HERE, "control_ui.html"), encoding="utf-8", errors="surrogateescape").read()
        self.assertNotIn("st.ver || 'v927'", ui)
        self.assertIn("st.ver || '—'", ui)

    def test_fleet_presence_is_honest_when_it_cannot_reach_the_site(self):
        """Offline must read as UNREACHABLE, never as an empty fleet — an empty list would say
        'no machine is online', which is a claim this function did not make."""
        import urllib.request as ur
        saved, savedcache = ur.urlopen, dict(ca._FLEET_PRESENCE_CACHE)
        try:
            ca._FLEET_PRESENCE_CACHE["d"] = None
            def _boom(*a, **k):
                raise OSError("no network")
            ur.urlopen = _boom
            out = ca.fleet_presence(force=True)
            self.assertIs(out["ok"], False)
            self.assertTrue(out.get("error"), "it must SAY why, not just return empty lists")
            self.assertEqual(out["online"], [])
        finally:
            ur.urlopen = saved
            ca._FLEET_PRESENCE_CACHE.clear()
            ca._FLEET_PRESENCE_CACHE.update(savedcache)


class TestV1500BundleVersionIsNotAFifthTruth(unittest.TestCase):
    """v1500 — the .app bundle was a FIFTH version surface that nobody checked.

    v1489 gave the repo one place to bump and a gate proving the four agreed — board, control, agent
    and ship manifest. The macOS bundle was outside that set: tv/install-tvd.sh hardcoded 787 while
    the installed apps advertised 1379.3 and the tree was at v1498. Re-running the installer would
    have REGRESSED the advertised version by 600. A stamp nobody reads is a stamp that lies."""

    def _installer(self):
        with open(os.path.join(os.path.dirname(ca.__file__), "install-tvd.sh"), encoding="utf-8") as fh:
            return fh.read()

    def test_installer_never_hardcodes_a_version(self):
        src = self._installer()
        # Check the two VERSION keys specifically. A 200-char window also caught
        # LSMinimumSystemVersion's <string>12.0</string> — a real literal, and a correct one.
        for key in ("CFBundleVersion", "CFBundleShortVersionString"):
            m = re.search(r"<key>%s</key>\s*<string>([^<]*)</string>" % key, src)
            self.assertIsNotNone(m, "%s must still be written by the installer" % key)
            self.assertNotRegex(m.group(1).strip(), r"^\d+(\.\d+)*$",
                                "%s is a hardcoded literal — that is how the installer came to "
                                "advertise 787 against a v1498 tree" % key)
        self.assertIn("TVD_VER", src, "it must read the one source of truth instead")

    def test_installer_reads_the_same_source_as_everything_else(self):
        src = self._installer()
        self.assertIn("tv_diablo.py", src,
                      "the bundle version must come from the SAME file the other four stamps come from")


class TestV1501ThirdEyeFindsItsBinary(unittest.TestCase):
    """v1501 — THE THIRD EYE WAS SWITCHED ON AND DARK.

    Konyo had G5 set to PRIMARY — his mandated vision lane, grok CLI on the SuperGrok subscription.
    The console reported cliInstalled=False, mode=off, and calls=0 / errors=0 / last_error=None,
    because a lane that never ATTEMPTS never records a failure. Meanwhile `which grok` in his shell
    resolved /Users/konyo/.grok/bin/grok perfectly.

    The cause: `shutil.which` searches the PATH OF THIS PROCESS, and the console runs as a GUI app
    under launchd/pywebview whose PATH is the bare /usr/bin:/bin:/usr/sbin:/sbin — it never inherits
    the shell PATH where ~/.grok/bin lives. control_app.py already carries `_find_claude_bin` for
    exactly this reason; the third eye had no equivalent.

    This test IS the GUI's environment. It fails on any build where the lane can only be found by a
    friendly PATH."""

    def _g5(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(ca.__file__)))
        try:
            import g5_grok_eyes
            return g5_grok_eyes
        except Exception:
            self.skipTest("g5_grok_eyes not present (removable lane)")

    def test_binary_is_found_with_a_launchd_style_PATH(self):
        g5 = self._g5()
        real = os.path.expanduser("~/.grok/bin/grok")
        if not os.path.isfile(real):
            self.skipTest("no grok CLI installed on this machine — nothing to find")
        saved = os.environ.get("PATH")
        try:
            os.environ["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"      # exactly what the GUI app gets
            found = g5._grok_bin()
            self.assertTrue(found, "the third eye must find its binary without the shell's PATH — "
                                   "this is the bug that left it switched to PRIMARY and dark")
            self.assertTrue(os.path.isfile(found))
        finally:
            if saved is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = saved

    def test_intent_and_reality_disagreeing_is_reported(self):
        """A switch set to primary while the mode is off must SAY so — silence is what hid this."""
        g5 = self._g5()
        st = g5.status()
        self.assertIn("intentBlocked", st)
        self.assertIn("blockedWhy", st)
        # v1767 — THREE states, not two. The third is a lane that starts fine and hard-stops on
        # every call; it resolves mode() to primary, so the old `else` branch below asserted it was
        # NOT blocked while it had been dark for a hundred calls.
        hard = st.get("blockedWhy") if st.get("mode") != "off" else ""
        if st.get("switch") != "off" and (st.get("mode") == "off" or hard):
            self.assertTrue(st["intentBlocked"], "a blocked lane must declare itself blocked")
            self.assertTrue(st["blockedWhy"].strip(), "and it must say WHY, in words")
        else:
            self.assertFalse(st["intentBlocked"])

    def test_a_lane_that_hard_stops_every_call_is_not_reported_healthy(self):
        """v1767 — MEASURED LIVE ON HIS CONSOLE: 165 calls, 107 errors, last_error "402 Payment
        Required: Grok Build usage balance exhausted" — and intentBlocked False with an empty
        blockedWhy. The field invented to publish intent-vs-reality said nothing was wrong while the
        second eye had been dark for a hundred calls.

        The two states it already knew are structural (no binary, not signed in) and both resolve
        mode() to "off". This one resolves to PRIMARY, which is why it slipped through: the lane is
        installed, authorised, and answering every request with a refusal from the far end.

        A hard stop is not a flaky call. It is stated by the other side and will not clear by
        retrying, so it belongs in the headline exactly like the other two - and only the LAST call
        is consulted, so a lane that recovers stops announcing a blockage."""
        g5 = self._g5()
        self.assertTrue(g5._hard_stop_why("API error (status 402 Payment Required): balance exhausted"),
                        "a 402 is not recognised as a hard stop")
        self.assertIn("topped up",
                      g5._hard_stop_why("Internal error: 402 Payment Required"),
                      "the reason is not in words he can act on")
        self.assertTrue(g5._hard_stop_why("HTTP 401 unauthorized"), "a credential refusal is not caught")
        # ...and the things that are NOT hard stops must stay quiet, or the headline becomes wallpaper
        self.assertEqual(g5._hard_stop_why("timed out after 240s"), "",
                         "a timeout was reported as a permanent blockage")
        self.assertEqual(g5._hard_stop_why(""), "", "an empty error was read as a blockage")
        self.assertEqual(g5._hard_stop_why(None), "",
                         "an explicit no-error was confused with 'go look it up'")

        # AND THE WIRING, not just the helper. The assertion above this one goes red on HIS machine
        # because his live stats hold the 402 — on CI those stats are clean, so removing the wiring
        # from status() would sail through there. That is a gate blind to data CI never has, which
        # is the same defect as a gate blind to data he never has. Stub the stats and the wiring
        # becomes provable on any machine.
        real = g5.stats_view
        try:
            g5.stats_view = lambda: {"calls": 9, "errors": 9,
                                     "last_error": "API error (status 402 Payment Required)"}
            st2 = g5.status()
            if st2.get("switch") != "off" and st2.get("mode") != "off":
                self.assertTrue(st2["intentBlocked"],
                                "status() ignores a hard stop the stats are reporting")
                self.assertIn("topped up", st2["blockedWhy"])
            # a clean lane must come back quiet, or the headline is permanent and unreadable
            g5.stats_view = lambda: {"calls": 9, "errors": 0, "last_error": None}
            st3 = g5.status()
            if st3.get("mode") != "off":
                self.assertFalse(st3["intentBlocked"],
                                 "a healthy lane is still announcing a blockage: %r" % st3.get("blockedWhy"))
        finally:
            g5.stats_view = real


class TestV1503FourStatesOnly(unittest.TestCase):
    """v1503 — Konyo: "standardize to four visual states app-wide... no fifth 'kinda ok purple'."

    Every surface that reports a STATE draws from four tokens and nothing else, so the colour is
    learned once and holds everywhere. --sim and --info are deliberately NOT states: one marks the
    PAST/simulation mode, the other marks explanation. This test is the thing that keeps a fifth
    state from being invented by accident on a busy night."""

    def _ui(self):
        with open(os.path.join(os.path.dirname(ca.__file__), "control_ui.html"), encoding="utf-8") as fh:
            return fh.read()

    def test_the_four_tokens_exist_and_are_named_for_meaning(self):
        ui = self._ui()
        for tok in ("--st-good", "--st-working", "--st-needs", "--st-broken"):
            self.assertIn(tok + ":", ui, "%s must be defined — it is one of the four states" % tok)

    def test_state_surfaces_draw_from_the_tokens_not_loose_hexes(self):
        ui = self._ui()
        for sel in (".eh-organ.eh-ok   .eh-dot", ".eh-organ.eh-bad  .eh-dot"):
            i = ui.find(sel)
            self.assertGreater(i, 0, "%s must still exist" % sel)
            rule = ui[i:i + 160]
            self.assertIn("var(--st-", rule,
                          "a state surface must draw from the four-state tokens, not a loose hex — "
                          "loose hexes are how seven state-ish colours accumulated")


class TestV1504TypeFloor(unittest.TestCase):
    """v1504 — Konyo's own mandate, still open until now: "nothing important under ~12-13px at
    fullscreen."

    The :root scale already declares --fs-2xs (13px) as the smallest anything may render, and the
    visual-lock keeps WEIGHTS honest — but a raw `font-size: 10px` slipped past both, because
    neither gate looked at size. Three surfaces were under the floor, and two of them were the G5
    card: the buttons that decide whether the third eye runs, and the line that says WHY it is not
    running. A warning nobody can read is not a warning."""

    def _ui(self):
        with open(os.path.join(os.path.dirname(ca.__file__), "control_ui.html"), encoding="utf-8") as fh:
            return fh.read()

    def test_nothing_renders_below_the_declared_floor(self):
        ui = self._ui()
        bad = re.findall(r"font-size: *(\d+(?:\.\d+)?)px", ui)
        bad += re.findall(r"font: [^;]*?\b(\d+(?:\.\d+)?)px", ui)
        under = sorted({float(x) for x in bad if float(x) < 13})
        self.assertEqual(under, [],
                         "these raw px sizes render below the 13px fullscreen floor: %s — use a "
                         "--fs-* token instead, which clamps and scales" % under)

    def test_the_floor_token_still_exists_to_use(self):
        ui = self._ui()
        self.assertRegex(ui, r"--fs-2xs:\s*clamp\(13px",
                         "the floor is the token; if it moves, this test should be the thing that notices")


class TestV1506EveryVerdictSaysHowSure(unittest.TestCase):
    """v1506 — Konyo: "never let a live guess wear the same wax-seal chrome as a sealed verdict."

    v1457 gave the REFUSED reads a ⚠ HELD chip. The more dangerous pair was left untouched: a read
    the accuracy gate CERTIFIED and a read nothing has checked at all rendered identically, so an
    unverified guess wore the same chrome as a verdict. Three states now, taken from the gate itself
    and never inferred: certified · held · live guess."""

    def _ui(self):
        with open(os.path.join(os.path.dirname(ca.__file__), "control_ui.html"), encoding="utf-8") as fh:
            return fh.read()

    def test_all_three_provenance_states_render(self):
        ui = self._ui()
        for cls in ("rcpt-sure", "rcpt-held", "rcpt-guess"):
            self.assertIn(cls, ui, "%s must exist — certainty needs its own mark, and so does its "
                                   "absence" % cls)

    def test_the_states_come_from_the_gate_not_a_guess(self):
        ui = self._ui()
        self.assertIn("r.gate && r.gate.pass === true", ui,
                      "certified must be read from the gate verdict, never inferred from the row")
        self.assertIn("r.gate.pass === false", ui, "held likewise")

    def test_an_unchecked_read_is_never_dressed_as_certified(self):
        ui = self._ui()
        i = ui.find(".rcpt-guess {")
        self.assertGreater(i, 0)
        rule = ui[i:i + 260]
        self.assertNotIn("--st-good", rule,
                         "an unchecked guess must not borrow the GOOD state's colour — that is the "
                         "exact confusion this change exists to remove")

class TestChronicleSpeaksDiablo(unittest.TestCase):
    """v1509 — the Chronicle names itself in HIS words, in the receipts feed AND in Theatre.

    v1508 wired the theatre caption to this same `_diablo_scene_label`, deliberately one source, so
    a single label here reaches both surfaces and cannot drift the way REG-076 drifted."""

    def test_the_two_ledgers_are_named_apart(self):
        u = ca._diablo_scene_label("chronicle-uniques", "")["label"]
        st = ca._diablo_scene_label("chronicle-sets", "")["label"]
        self.assertIn("Holy Grail", u)
        self.assertIn("Set", st)
        self.assertNotEqual(u, st)        # ★ the whole point: never one word for two ledgers

    def test_an_unknown_tab_still_names_the_screen(self):
        r = ca._diablo_scene_label("chronicle", "")
        self.assertIn("CHRONICLE", r["label"])
        # ...but must NOT claim a ledger it could not read
        self.assertNotIn("Grail", r["label"])
        self.assertNotIn("Set", r["label"])

    def test_the_LEDGER_reaches_the_label_from_the_read(self):
        # v1517 — the reader reports scene=chronicle + chronicleTab; the label is where they meet.
        # Optional and last in the signature, so no existing caller changed.
        self.assertIn("Holy Grail", ca._diablo_scene_label("chronicle", "", "uniques")["label"])
        self.assertIn("Set", ca._diablo_scene_label("chronicle", "", "sets")["label"])
        # ★ and a chronicle read whose ledger the reader could NOT name still says so honestly
        bare = ca._diablo_scene_label("chronicle", "", "")["label"]
        self.assertIn("CHRONICLE", bare)
        self.assertNotIn("Grail", bare)

    def test_a_tab_on_a_non_chronicle_scene_changes_nothing(self):
        self.assertEqual(ca._diablo_scene_label("stash", "Harrogath", "uniques")["label"],
                         ca._diablo_scene_label("stash", "Harrogath")["label"])

    def test_chronicle_is_a_menu_not_farming(self):
        # it is a screen he is READING, not a run he is farming — kind drives the theatre icon
        self.assertEqual(ca._diablo_scene_label("chronicle-sets", "Harrogath")["kind"], "menu")

class TestChronicleSweepJob(unittest.TestCase):
    """v1519 — THE REAL SWEEP, driven end to end at zero cost.

    Both lanes honour TV_STUB, so this exercises the whole path — group frames, classify each still
    run, read the chronicle pages on two lanes, fold into a proposal, run the gate — without a single
    model call. A sweep nobody can test cheaply is a sweep nobody exercises, and a second lane nobody
    exercises is a second lane nobody trusts."""

    def setUp(self):
        # v1776 — EVIDENCE ACCUMULATES NOW, so a test that asserts an exact result needs a clean
        # ledger or it inherits the previous test's sightings and grounds names this run never saw.
        # The module redirect gives one temp file for the whole file; this empties it per test.
        try:
            os.remove(ca._CHRON_EVIDENCE_PATH)
        except Exception:
            pass
        try:
            from PIL import Image  # noqa: F401
        except Exception:
            self.skipTest("Pillow absent — frame grouping needs to decode the JPEGs")
        self.d = tempfile.mkdtemp()
        from PIL import Image
        for sid in ("s_100", "s_200", "s_300"):
            rd = os.path.join(self.d, "reel_" + sid)
            os.makedirs(rd)
            for n in range(6):
                _screenish((64, 48), 11).save(os.path.join(rd, "f%d.jpg" % n))
            with open(os.path.join(rd, "index.json"), "w", encoding="utf-8") as fh:
                json.dump({"sessionId": sid,
                           "frames": [{"f": "f%d.jpg" % n, "ts": 1000 + n} for n in range(6)]}, fh)
        self.man = os.path.join(self.d, "man.json")
        self._env = {k: os.environ.get(k) for k in ("TV_STUB", "TV_STUB_MANIFEST", "TV_HIST")}
        # v1524 — every sweep test owns its OWN memory file. Sharing the real one made the second
        # test in the class skip every reel the first one read: a green suite that had stopped
        # exercising the sweep at all (the v1497 lesson, in a new place).
        self._swept = mock.patch.object(ca, "_CHRON_SWEPT_PATH", os.path.join(self.d, "swept.json"))
        self._swept.start()

    def tearDown(self):
        self._swept.stop()
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.d, ignore_errors=True)
        with ca._CHRON_LOCK:
            ca._CHRON_JOB.update({"running": False, "phase": "idle", "result": None, "error": None})

    def _sweep(self, manifest, timeout=30.0):
        with open(self.man, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh)
        os.environ.update({"TV_STUB": "1", "TV_STUB_MANIFEST": self.man, "TV_HIST": self.d})
        started = ca.chronicle_sweep_start(hist_dir=self.d)
        self.assertTrue(started.get("ok"), started)
        deadline = time.time() + timeout
        while time.time() < deadline and ca.chronicle_sweep_state()["running"]:
            time.sleep(0.05)
        st = ca.chronicle_sweep_state()
        self.assertFalse(st["running"], "the sweep never finished")
        self.assertIsNone(st["error"])
        return st["result"] or {}

    BOTH = {
        "*": {"scene": "chronicle", "chronicleTab": "uniques", "names": [], "conf": 0.9},
        "*#chronicle": {"found": ["Harlequin Crest", "Windforce"], "notFound": ["Stormshield"],
                        "printedFound": 2, "printedTotal": 3, "conf": 0.9},
        "*#chronicle-grok": {"found": ["Harlequin Crest"],
                             "notFound": ["Stormshield", "Windforce"], "conf": 0.85},
    }

    def test_the_whole_sweep_runs_and_the_gate_EXPLAINS_every_name(self):
        res = self._sweep(self.BOTH)
        add = res["wouldAdd"]["uniques"]
        self.assertTrue(add, "the sweep found nothing at all")
        for row in add:
            self.assertTrue(row["why"], "a grounded name with no reason is not reviewable")
            self.assertGreaterEqual(len(row["witnesses"]), 2)

    def test_the_lane_that_DISAGREED_shows_in_the_witness_list(self):
        # Grok put Windforce in notFound. Both names still ground here (3 sessions), but only the one
        # BOTH lanes saw carries cross-lane — the disagreement is visible, not averaged away.
        res = self._sweep(self.BOTH)
        by = {r["name"]: r["witnesses"] for r in res["wouldAdd"]["uniques"]}
        self.assertIn("cross-lane", by.get("Harlequin Crest", []))
        self.assertNotIn("cross-lane", by.get("Windforce", []))

    def test_a_SILENT_grok_lane_never_reads_as_agreement(self):
        # no grok entry in the manifest ⇒ the lane returns None ⇒ nothing may claim cross-lane
        man = dict(self.BOTH)
        man.pop("*#chronicle-grok")
        res = self._sweep(man)
        for row in res["wouldAdd"]["uniques"]:
            self.assertNotIn("cross-lane", row["witnesses"])

    def test_a_page_the_reader_REFUSED_grounds_nothing(self):
        man = dict(self.BOTH)
        man["*#chronicle"] = {"found": ["Harlequin Crest"], "stateVisible": False}
        res = self._sweep(man)
        self.assertEqual(res["wouldAdd"]["uniques"], [])
        self.assertTrue(res["refused"], "a refusal must be REPORTED, not silently dropped")

    def test_the_sweep_writes_NOTHING_it_only_proposes(self):
        res = self._sweep(self.BOTH)
        self.assertIn("wouldAdd", res)
        self.assertNotIn("applied", res)
        self.assertNotIn("wrote", res)

    def test_two_sweeps_at_once_are_refused(self):
        # two sweeps over the same reels would double the spend and produce two proposals that each
        # look like the whole truth
        with ca._CHRON_LOCK:
            ca._CHRON_JOB["running"] = True
        try:
            r = ca.chronicle_sweep_start(hist_dir=self.d)
            self.assertFalse(r["ok"])
            self.assertIn("already running", r["why"])
        finally:
            with ca._CHRON_LOCK:
                ca._CHRON_JOB["running"] = False

    def test_a_reel_swept_ONCE_is_not_paid_for_twice(self):
        # ★ v1524 — a sealed reel never changes. The second sweep should read nothing and say so.
        first = self._sweep(self.BOTH)
        self.assertGreater(first["totals"]["classified"], 0)
        second = self._sweep(self.BOTH)
        self.assertEqual(second["totals"]["classified"], 0)
        self.assertEqual(second["totals"]["skippedReels"], 3)

    def test_a_reel_that_was_SKIPPED_never_enters_the_memory_as_read(self):
        # one bad run must not permanently hide footage from every future sweep
        self._sweep(self.BOTH)
        self._sweep(self.BOTH)              # everything skipped this time
        mem = json.load(open(os.path.join(self.d, "swept.json"), encoding="utf-8"))
        self.assertEqual(len(mem), 3)       # still the 3 REAL reads, not 6 rows
        for v in mem.values():
            self.assertGreater(v["classified"], 0)

    def test_he_can_FORGET_and_re_read_everything(self):
        # the memory is an optimisation, and an optimisation he cannot clear is a cage
        self._sweep(self.BOTH)
        ca.chronicle_forget_swept()
        again = self._sweep(self.BOTH)
        self.assertGreater(again["totals"]["classified"], 0)

    def test_FORCE_re_reads_what_the_memory_says_is_done(self):
        self._sweep(self.BOTH)
        ca.chronicle_sweep_start(hist_dir=self.d, force=True)
        deadline = time.time() + 30
        while time.time() < deadline and ca.chronicle_sweep_state()["running"]:
            time.sleep(0.05)
        forced = ca.chronicle_sweep_state()["result"] or {}
        self.assertGreater(forced["totals"]["classified"], 0)

    def test_the_lanes_in_play_are_NAMED(self):
        # "claude only" and "both lanes agreed" are different confidences and the gate scores them
        # differently — so which lanes ran is part of the answer, not a detail
        res = self._sweep(self.BOTH)
        self.assertIn("claude", res["lanes"])


class TestChronicleVisitsOffer(unittest.TestCase):
    """v1522 — the Chronicle panels he opened IN GAME, surfaced as an offer rather than an auto-spend."""

    def setUp(self):
        self.rows = [
            {"lane": "chronicle", "kind": "visit", "ts": 100, "ledger": "uniques",
             "n": 14, "frames": ["a", "b"]},
            {"lane": "read", "kind": "read", "ts": 150},
            {"lane": "chronicle", "kind": "visit", "ts": 200, "ledger": "", "n": 3, "frames": ["c"]},
        ]

    def _visits(self, **kw):
        with mock.patch.object(ca, "_kai_journal_rows", return_value=self.rows):
            return ca.chronicle_visits(**kw)

    def test_newest_visit_first(self):
        v = self._visits()["visits"]
        self.assertEqual([x["ts"] for x in v], [200, 100])

    def test_each_visit_is_named_in_HIS_words(self):
        # newest first, so the uniques visit (ts 100) is second
        labels = [x["label"] for x in self._visits()["visits"]]
        self.assertIn("Holy Grail", labels[1])
        self.assertIn("🏆", labels[1])

    def test_a_visit_whose_ledger_was_never_read_says_SO(self):
        # ★ not a guess, and not silence either — "ledger unread" is the reviewable state
        v = self._visits()["visits"][0]
        self.assertEqual(v["ledger"], "")
        self.assertIn("unread", v["label"])

    def test_non_chronicle_journal_rows_are_ignored(self):
        self.assertEqual(len(self._visits()["visits"]), 2)

    def test_it_spends_NOTHING(self):
        # the whole point: recording was free, and looking at what was recorded is free too
        self.assertEqual(self._visits()["spent"], 0)

    def test_a_journal_that_cannot_be_read_returns_no_visits_not_a_crash(self):
        with mock.patch.object(ca, "_kai_journal_rows", side_effect=RuntimeError("boom")):
            self.assertEqual(ca.chronicle_visits()["visits"], [])


class TestRegateIsFree(unittest.TestCase):
    """v1531 — CHRONICLE_ARC.md calls the gate thresholds "reasoned, not measured". They cannot be
    measured without seeing what they do to real evidence, and that was impossible while tuning them
    meant paying for the whole sweep again."""

    def setUp(self):
        import chronicle_retro as cr
        s = lambda **kw: dict({"reel": "s1", "frame": "f1.jpg", "witness": "none",
                               "conf": 0.9, "lane": "claude"}, **kw)
        # Windforce: 2 witnesses (cross-frame + cross-lane) — grounds today
        # Shako:     1 witness (printed only)               — held today
        self._prev = ca.__dict__.get("_CHRON_LAST_PROPOSAL")
        ca._CHRON_LAST_PROPOSAL = {
            "uniques": {
                "Windforce": [s(frame="a.jpg"), s(frame="b.jpg", lane="grok")],
                # v1789 — was "Shako", which is a BASE name, not a roster unique. Once the gate began
                # folding onto the roster, the tuner folded too (it must preview the same input the
                # live gate judges) and retired it as reader debris — correctly: the Chronicle prints
                # a base name for a row he has NOT found. The fixture needed a real grail item, which
                # is what it was always standing in for.
                "Goldwrap": [s(witness="agree")],
            },
            "sets": {}, "completeSets": {},
        }

    def tearDown(self):
        ca._CHRON_LAST_PROPOSAL = self._prev

    def test_it_reads_the_evidence_again_and_SPENDS_NOTHING(self):
        r = ca.chronicle_regate()
        self.assertTrue(r["ok"])
        self.assertEqual(r["spent"], 0)

    def test_LOOSENING_names_exactly_what_it_would_let_in(self):
        # ★ named, not counted — a count cannot be argued with
        r = ca.chronicle_regate(min_witnesses=1)
        self.assertIn("Goldwrap", r["wouldGainNames"])
        self.assertEqual(r["wouldLoseNames"], [])

    def test_TIGHTENING_names_exactly_what_it_would_keep_out(self):
        r = ca.chronicle_regate(min_witnesses=3)
        self.assertIn("Windforce", r["wouldLoseNames"])

    def test_raising_the_confidence_floor_above_the_reads_holds_everything(self):
        r = ca.chronicle_regate(conf_floor=0.99)
        self.assertEqual(r["asked"]["grounded"], 0)
        self.assertIn("Windforce", r["wouldLoseNames"])

    def test_the_CURRENT_thresholds_are_reported_beside_the_asked_ones(self):
        # the difference is the answer; either number alone is just a claim
        import chronicle_retro as cr
        r = ca.chronicle_regate(min_witnesses=1)
        self.assertEqual(r["current"]["minWitnesses"], cr.MIN_WITNESSES)
        self.assertEqual(r["asked"]["minWitnesses"], 1)

    def test_nonsense_thresholds_are_refused_not_coerced_into_a_lie(self):
        self.assertFalse(ca.chronicle_regate(conf_floor="banana")["ok"])

    def test_with_no_sweep_in_memory_it_says_so(self):
        ca._CHRON_LAST_PROPOSAL = None
        self.assertIn("run a sweep first", ca.chronicle_regate()["why"])


class TestSweepOneVisit(unittest.TestCase):
    """v1527 — sweeping a RECORDED visit: the cheapest path in the arc, and the one with the most
    dangerous shortcut available to it."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self._env = {k: os.environ.get(k) for k in ("TV_STUB", "TV_STUB_MANIFEST", "TV_HIST")}

    def tearDown(self):
        for k, v in self._env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        shutil.rmtree(self.d, ignore_errors=True)
        with ca._CHRON_LOCK:
            ca._CHRON_JOB.update({"running": False, "phase": "idle", "result": None, "error": None})

    def _run(self, visits, timeout=20.0):
        with mock.patch.object(ca, "chronicle_visits", return_value={"visits": visits}):
            ca._CHRON_JOB.update({"running": False, "lanes": ["claude"]})
            ca.chronicle_sweep_start(visit=visits[0]["ts"] if visits else 1)
            deadline = time.time() + timeout
            while time.time() < deadline and ca.chronicle_sweep_state()["running"]:
                time.sleep(0.05)
        return ca.chronicle_sweep_state()

    def test_A_VISIT_WITH_NO_LEDGER_IS_REFUSED(self):
        # ★ THE dangerous shortcut. Reading an unknown ledger as "probably uniques" writes set pieces
        # into his grail, and there is no second chance on that. Refusing costs him one re-open.
        st = self._run([{"ts": 5, "ledger": "", "n": 3, "frames": ["reel_x/f1"]}])
        self.assertEqual(st["phase"], "error")
        self.assertIn("ledger was never read", st["error"])

    def test_a_visit_that_left_the_journal_says_so(self):
        st = self._run([])
        self.assertIn("no longer in the journal", st["error"])

    def test_frames_pruned_off_disk_say_so_rather_than_reading_nothing(self):
        # hist is pruned by the retention governor; "0 found" would be a lie about his chronicle
        os.environ["TV_HIST"] = self.d
        st = self._run([{"ts": 7, "ledger": "uniques", "n": 2, "frames": ["reel_gone/f1"]}])
        self.assertEqual(st["phase"], "error")
        self.assertIn("no longer on disk", st["error"])

    def test_a_real_visit_reads_its_pages_with_ZERO_classifies(self):
        try:
            from PIL import Image
        except Exception:
            self.skipTest("Pillow absent")
        rd = os.path.join(self.d, "reel_s_1")
        os.makedirs(rd)
        for n in range(5):
            _screenish((48, 32), 12).save(os.path.join(rd, "f%d.jpg" % n))
        man = os.path.join(self.d, "man.json")
        with open(man, "w", encoding="utf-8") as fh:
            json.dump({"*#chronicle": {"found": ["Windforce"], "notFound": [], "conf": 0.9}}, fh)
        os.environ.update({"TV_STUB": "1", "TV_STUB_MANIFEST": man, "TV_HIST": self.d})
        st = self._run([{"ts": 9, "ledger": "uniques", "n": 5,
                         "frames": ["reel_s_1/f%d" % n for n in range(5)]}])
        self.assertEqual(st["phase"], "done", st.get("error"))
        res = st["result"]
        self.assertEqual(res["totals"]["classified"], 0)      # ★ the visit already answered that
        self.assertEqual(res["totals"]["pagesRead"], 1)       # 5 identical frames = ONE page
        self.assertEqual(res["fromVisit"], 9)


class TestBothLanesShareOneNormalizer(unittest.TestCase):
    """v1519 — cross-lane agreement is only evidence if both lanes answer in the same UNITS."""

    def test_identical_raw_answers_normalize_identically(self):
        import chronicle_retro as cr
        import g5_grok_eyes as g5
        raw = {"found": ["Windforce"], "notFound": ["Shako"], "printedFound": 1,
               "printedTotal": 2, "conf": 0.8}
        with mock.patch.object(g5, "g5_vision_read", return_value=raw):
            grok = g5.g5_chronicle_read("/tmp/f.jpg", "chronicle-uniques")
        claude = cr.normalize_page(raw, "chronicle-uniques", "claude")
        for k in ("found", "notFound", "witness", "wholePage", "ledger", "read", "note"):
            self.assertEqual(grok[k], claude[k], k + " must mean the same thing in both lanes")
        self.assertNotEqual(grok["lane"], claude["lane"])   # only the byline differs






# v1456 — THE RUNNER LIVES AT THE BOTTOM. It used to sit mid-file (before TestFleetUnity, added
# v1418), and unittest.main() exits the interpreter — so every class defined below it was NEVER
# DEFINED, let alone run: silent zero coverage that still reported "OK". Keep this block last.

class TestChronicleAutoReadWatchdog(unittest.TestCase):
    """v1745 — THE WATCHDOG KONYO ASKED FOR, AND THE ONE PLACE IT MAY FIRE.

    Konyo: "where is the coded AI reader that retro analyzes this within the console like a
    watchdog.. i want it automatically synced." There was none, deliberately: chron_visit_flush's
    docstring sets the doctrine — "recording is FREE, reading is OFFERED... never spends a classify"
    — and chronicle_sweep_start was reachable only from the HTTP endpoint. So a session could end
    with a good Chronicle recording on disk and nothing would ever look at it. Measured on his
    session s_1786922954749_12579: visit journalled with ledger='uniques' and 4 frames, five deep
    reads naming 13 discovered uniques, and his count sat at 249/403 with the evidence right there.

    "Offered, not automatic" is a COST argument, and it stops applying when the read is free. v1528
    names exactly when that is: a visit whose LEDGER is known is "the cheapest read in the system...
    there is no classify stage to pay for". So the watchdog fires ONLY on those, and a visit with no
    ledger is refused with a NAMED reason rather than guessed at — guessing writes set pieces into
    his grail (v1528). It never applies; the review gate stays where v947 put it.
    """

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self._old_path = ca._CHRON_AUTOREAD_PATH
        # never his file — the state is redirected, not trusted to behave
        ca._CHRON_AUTOREAD_PATH = os.path.join(self.d, "autoread.json")
        ca._CHRON_AUTOREAD["done"] = None
        ca._CHRON_AUTOREAD["skipped"] = {}
        ca._CHRON_AUTOREAD["tries"] = {}      # shared module state — a leak here made one test's
                                              # refusal count carry into the next and retire early
        self._old = (ca.chronicle_sweep_start, ca._agent_alive, ca.chronicle_sweep_state, ca.chronicle_visits)
        self.calls = []
        # v1766 — THE STUB HAS TO FINISH THE JOB, because the real one does. Marking moved out of
        # the tick and into _chron_visit_run, which marks once the result is on disk; a stub that
        # only says {"ok": True} models a sweep that STARTED and never wrote anything, and under the
        # new rule that visit is correctly retried rather than spent. Tests that assert "once each"
        # therefore need a stub that completes — otherwise they assert the failure mode.
        def _start_and_finish(**kw):
            self.calls.append(kw)
            if kw.get("visit"):
                ca._chron_autoread_mark(int(kw["visit"]))
            return dict({"ok": True}, **kw)
        ca.chronicle_sweep_start = _start_and_finish
        ca._agent_alive = lambda: False
        ca.chronicle_sweep_state = lambda: {"running": False}
        ca.chronicle_visits = lambda *a, **k: {"visits": [
            {"ts": 3000, "ledger": "", "n": 9},                # no ledger — must be REFUSED
            {"ts": 2000, "ledger": "uniques", "n": 4},
            {"ts": 1000, "ledger": "sets", "n": 6},
        ]}

    def tearDown(self):
        ca._CHRON_AUTOREAD_PATH = self._old_path
        ca._CHRON_AUTOREAD["done"] = None
        (ca.chronicle_sweep_start, ca._agent_alive, ca.chronicle_sweep_state, ca.chronicle_visits) = self._old
        shutil.rmtree(self.d, ignore_errors=True)

    def test_reads_ledger_known_visits_once_each_and_never_guesses(self):
        a = ca.chronicle_autoread_tick()
        b = ca.chronicle_autoread_tick()
        c = ca.chronicle_autoread_tick()
        self.assertEqual(a.get("read"), 2000, a)          # newest ledger-known first
        self.assertEqual(b.get("read"), 1000, b)
        self.assertIsNone(c.get("read"), c)               # and then nothing left
        self.assertEqual([x.get("visit") for x in self.calls], [2000, 1000])
        # the ledger-less visit is REFUSED, and the refusal is recorded rather than silent
        self.assertIn("3000", ca._CHRON_AUTOREAD["skipped"])
        self.assertNotIn(3000, [x.get("visit") for x in self.calls])

    def test_never_fires_while_a_session_is_live(self):
        ca._agent_alive = lambda: True
        r = ca.chronicle_autoread_tick()
        self.assertFalse(r.get("ok"), r)
        self.assertIn("session is live", r.get("why", ""))
        self.assertEqual(self.calls, [])

    def test_never_fires_while_a_sweep_is_running(self):
        ca.chronicle_sweep_state = lambda: {"running": True}
        r = ca.chronicle_autoread_tick()
        self.assertFalse(r.get("ok"), r)
        self.assertEqual(self.calls, [])

    def test_a_refused_visit_is_retired_after_two_tries_not_retried_forever(self):
        """v1745.1 — Konyo: "i dont want it looping though the same video over and over.. it might
        loop and waste?" He was right about the one path that was open. A SUCCESSFUL read is already
        read-once (the ts is persisted). A REFUSED sweep marked nothing, so the same visit would be
        retried every 20s for as long as the console ran. Two tries, then retired WITH the reason —
        a third identical refusal teaches nothing and costs what the first did."""
        ca.chronicle_sweep_start = lambda **kw: {"ok": False, "why": "busy"}
        a = ca.chronicle_autoread_tick()
        b = ca.chronicle_autoread_tick()
        c = ca.chronicle_autoread_tick()
        self.assertFalse(a.get("ok"), a)
        self.assertEqual(b.get("retired"), 2000, b)          # retired on the second try
        self.assertIsNone(c.get("read"), c)                  # and never attempted again
        self.assertIn("2000", ca._CHRON_AUTOREAD["skipped"])
        self.assertIn("gave up", ca._CHRON_AUTOREAD["skipped"]["2000"])

    def test_a_visit_whose_sweep_DIED_is_retried_then_retired(self):
        """v1766 — THE HALF v1745 LEFT OPEN, described in its own comment and never closed: "a tick
        run from a throwaway process started a sweep, the process exited, and the visit was left
        flagged read with nothing to show for it." v1745 fixed the sweep that REFUSED; a sweep that
        TOOK the job and then died still burned the visit, because chronicle_sweep_start spawns a
        thread and returns immediately, and the mark fired on that return.

        The visit is now marked by the runner once its result is durable. This stub takes the job
        and never finishes — so the visit must come back, and then stop coming back."""
        ca.chronicle_sweep_start = lambda **kw: (self.calls.append(kw) or {"ok": True})
        a = ca.chronicle_autoread_tick()
        b = ca.chronicle_autoread_tick()
        c = ca.chronicle_autoread_tick()
        self.assertEqual(a.get("read"), 2000, a)
        self.assertEqual(b.get("read"), 2000, "a visit whose sweep died was never tried again: %s" % b)
        # ...and it does not retry forever - that would be the runaway on the other side
        self.assertEqual(c.get("retired"), 2000, "a dead sweep is retried without bound: %s" % c)
        self.assertIn("never wrote a result", ca._CHRON_AUTOREAD["skipped"].get("2000", ""))
        self.assertEqual([x.get("visit") for x in self.calls], [2000, 2000],
                         "it kept paying after giving up: %s" % self.calls)

    def test_a_refused_sweep_does_not_burn_the_visit(self):
        """Marking BEFORE the sweep took the job meant a refusal still spent the visit. Measured
        while building this: a tick from a throwaway process started a sweep, the process exited,
        and the visit was left flagged read with nothing to show for it."""
        ca.chronicle_sweep_start = lambda **kw: {"ok": False, "why": "busy"}
        r = ca.chronicle_autoread_tick()
        self.assertFalse(r.get("ok"), r)
        # ...and the next tick can still try it
        ca.chronicle_sweep_start = lambda **kw: (self.calls.append(kw) or dict({"ok": True}, **kw))
        self.assertEqual(ca.chronicle_autoread_tick().get("read"), 2000)

class TestOneGateRunPerTree(unittest.TestCase):
    """v1751 — REG-162: two gate runs in one tree make a THIRD, innocent gate fail.

    Reproduced, not theorised: two runs started at once failed DIFFERENT gates (robot_smoke in one,
    test_roundtrip_sim in the other) while a clean single run passed 30/30, and each of those gates
    passes alone. They share ports, reel directories and the journal, so whichever gate needs an
    exclusive one loses — and the verdict names the loser, never the collision. That is the worst
    kind of red: it sends you to debug working code.

    The lock is flock, so the kernel releases it when the holder dies. A pid file would need reaping
    logic, and reaping logic is how a lock starts lying — a stale lock that refuses every future run
    is a worse failure than the one being prevented. All three properties are asserted here, because
    a lock that only ever gets tested in the happy direction is a lock nobody has actually seen work.
    """

    def setUp(self):
        # A KEY OF THIS TEST'S OWN. test_control.py IS a gate, so under CI's `run_gates.py` the
        # outer run already holds the real tree lock — child runs here would be refused by the very
        # run they are testing, and this class would be red on CI and green on every laptop.
        self.env = dict(os.environ)
        self.env["D2R_GATE_LOCK_KEY"] = os.path.join(
            tempfile.gettempdir(), "d2r_gatelock_test_%d" % os.getpid())

    def _gates(self, *extra):
        return subprocess.run([sys.executable, os.path.join(HERE, "run_gates.py"),
                               "--only", "visual-lock"] + list(extra),
                              capture_output=True, text=True, timeout=180, env=self.env)

    def test_a_lone_run_is_never_blocked(self):
        r = self._gates()
        self.assertEqual(r.returncode, 0, "a single gate run was refused:\n%s" % r.stdout[-600:])

    def test_a_second_run_in_the_same_tree_is_refused_and_says_who_holds_it(self):
        holder = subprocess.Popen(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, %r); import run_gates as R; R._claim_the_tree();"
             "import time; time.sleep(30)" % HERE],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env)
        try:
            time.sleep(1.5)
            r = self._gates()
            self.assertEqual(r.returncode, 2,
                             "a concurrent gate run was ALLOWED — REG-162 can happen again")
            self.assertIn("REFUSED", r.stdout)
            # naming the holder is the point: "refused" with no address is a puzzle, not a message
            self.assertIn("pid %d" % holder.pid, r.stdout,
                          "the refusal does not say WHICH run holds the tree:\n%s" % r.stdout[:400])
        finally:
            holder.kill()
            holder.wait()

    def test_a_killed_run_does_not_leave_a_lock_that_refuses_everything_after_it(self):
        holder = subprocess.Popen(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, %r); import run_gates as R; R._claim_the_tree();"
             "import time; time.sleep(60)" % HERE],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env)
        time.sleep(1.5)
        holder.kill()          # SIGKILL — no chance to clean up after itself
        holder.wait()
        time.sleep(0.5)
        r = self._gates()
        self.assertEqual(r.returncode, 0,
                         "a kill -9'd run left a stale lock; every gate run after it is refused")


class TestTheSuiteNeverWritesHisConsoleState(unittest.TestCase):
    """FIXTURES NEVER TOUCH LIVE DATA — and this file was breaking that rule for months.

    The console's state lives beside control_app.py and belongs to the console RUNNING on his Mac.
    Two classes here (TestChronicleSweepJob, TestSweepOneVisit) and test_chronicle_chain drove the
    sweep with those paths still pointing at the real files, so every gate run overwrote
    tv/chron_last_result.json — his persisted sweep — with the fixture pair Harlequin Crest and
    Windforce, seen across reels s_100/200/300. Found by opening that file expecting his footage.

    IT WENT FROM COSMETIC TO DANGEROUS IN ONE DAY. v1765 wired his board to ADOPT a persisted sweep
    with no button press, and that fixture carries four witnesses, so it would have been applied
    rather than queued. Neither name is in his grail: two finds he never made, written into the one
    dataset that exists to be his own truth, by his own test suite.

    The real enforcement is in run_gates.py, which fingerprints the live files around the whole set
    so that a class nobody has written yet cannot quietly reintroduce this. These assertions cover
    the fingerprint's logic, because a guard whose comparison is wrong is worse than none."""

    def test_it_notices_every_shape_of_mutation(self):
        import run_gates as rg
        n = rg._LIVE_STATE[0]
        self.assertEqual(rg._live_state_diff({n: "aaa"}, {n: "aaa"}), [],
                         "an untouched file was reported as written")
        for before, after, what in (("aaa", "bbb", "modified"),
                                    (None, "bbb", "created"),
                                    ("aaa", None, "deleted")):
            d = rg._live_state_diff({n: before}, {n: after})
            self.assertTrue(d, "a %s live file was not flagged" % what)
            self.assertIn(n, d[0], "the report does not name the file: %s" % d)

    def test_the_live_paths_are_redirected_for_this_whole_module(self):
        """A per-class redirect is the wrong shape: the guarantee has to hold for classes nobody has
        written yet, and forgetting is silent. setUpModule points them at a temp dir."""
        for attr in ("_CHRON_RESULT_PATH", "_CHRON_AUTOREAD_PATH", "_CHRON_SWEPT_PATH"):
            if not hasattr(ca, attr):
                continue
            p = str(getattr(ca, attr))
            self.assertNotEqual(os.path.dirname(p), os.path.dirname(os.path.abspath(ca.__file__)),
                                "%s still points beside control_app.py — a test can write his "
                                "console's state: %s" % (attr, p))


class TestV1777EveryBlockerRefusesByName(unittest.TestCase):
    """v1777 — THE SUBSCRIPTION CAP ANSWERED LIKE DATA, AND THE WHOLE NIGHT WENT INTO IT.

    v1774 closed this for the throttle. The SAME defect had a second door: _sub_budget_check is a
    circuit breaker on his own subscription (60/hour, 250/day at the time), and when it fired
    _oneshot returned None — which the parse turned into {"scene": "gameplay", "names": [],
    "conf": None}. classify reads that as a confident "not a Chronicle page" and skips the run.

    MEASURED: the cap sat at 250/250, every read returned that dict in 0.0s, and a sweep "ran" for
    fifty minutes reading nothing while reporting success. One reel of his thorough scroll is ~290
    pages, so the first honest sweep could never have fitted inside a day's allowance anyway.

    The caps were sized for a live farm session sipping the odd frame, not for reading his footage
    back. Raised to 4000/hour and 20000/day - our own guard rails, not Anthropic's, and the real
    pace limit is the throttle detector, untouched.

    This pins the SHAPE of every refusal, because the shape is the bug: a blocker that answers like
    an empty page is indistinguishable from footage that holds nothing."""

    def setUp(self):
        sys.path.insert(0, HERE)
        import tv_diablo
        self.tv = tv_diablo
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir, True)
        self._keep = (tv_diablo._SUB_DAILY_MAX, tv_diablo._SUB_HOURLY_MAX,
                      list(tv_diablo._THROTTLED_UNTIL))

    def tearDown(self):
        self.tv._SUB_DAILY_MAX, self.tv._SUB_HOURLY_MAX = self._keep[0], self._keep[1]
        self.tv._THROTTLED_UNTIL[0] = self._keep[2][0]

    def _img(self):
        """A REAL image, because the cap guard sits after the file check on the Claude path — a
        directory returns early for the wrong reason and the test passes vacuously. Falls back to a
        tiny generated jpg so this never depends on his footage existing."""
        import glob
        hits = glob.glob(os.path.join(HERE, "frames", "hist", "*", "*.jpg"))
        if hits:
            return hits[0]
        p = os.path.join(self.tmpdir, "probe.jpg")
        try:
            from PIL import Image
            Image.new("RGB", (8, 8), (0, 0, 0)).save(p)
        except Exception:
            with open(p, "wb") as fh:
                fh.write(b"\xff\xd8\xff\xd9")
        return p

    def test_the_caps_are_big_enough_to_read_one_reel(self):
        """His thorough reel is ~290 pages. A cap below that cannot express "read my footage back",
        and the failure looked like empty footage rather than a full meter."""
        # v1778 — assert the DEFAULTS in source, not the live constants: those are initialised from
        # TV_VISION_*_MAX at import, so a legitimate operator override would fail this for a non-bug.
        import re as _re
        src = open(os.path.join(HERE, "tv_diablo.py"), encoding="utf-8").read()
        d = _re.search(r'TV_VISION_DAILY_MAX",\s*"(\d+)"', src)
        h = _re.search(r'TV_VISION_HOURLY_MAX",\s*"(\d+)"', src)
        self.assertTrue(d and h, "could not find the cap defaults")
        self.assertGreaterEqual(int(d.group(1)), 1000,
                                "the DEFAULT daily cap cannot fit a single ~290-page reel: %s" % d.group(1))
        self.assertGreaterEqual(int(h.group(1)), 300,
                                "the DEFAULT hourly cap throttles a catch-up sweep to a crawl")

    def _open_the_circuit(self, n=50):
        """v1778 — LOWERING THE MAX IS NOT ENOUGH, and the first version of these tests only ever
        passed on his Mac. The cap compares against .subscription_budget.json, which is GITIGNORED —
        so on CI the call list is EMPTY, len([]) >= 1 is False, and nothing is blocked. The test then
        fell through to a real read path and failed for the wrong reason. A fixture that depends on
        one machine's live state is the blind-fixture defect. Caught by code review.

        Patch the LOAD instead, so the circuit is genuinely open on any machine."""
        import time as _t
        now = _t.time()
        self._real_load = self.tv._sub_budget_load
        self.tv._sub_budget_load = lambda: {"calls": [now - 1] * n}
        self.addCleanup(lambda: setattr(self.tv, "_sub_budget_load", self._real_load))

    def test_a_capped_classify_says_NOTHING_not_gameplay(self):
        self.tv._SUB_DAILY_MAX = 1
        self._open_the_circuit()
        self.assertTrue(self.tv._sub_budget_check("oneshot"),
                        "the fixture did not actually open the circuit — the test would pass vacuously")
        r = self.tv.claude_read(self._img())
        self.assertIsNone(r, "a capped classify answered like a real read: %r" % (r,))

    def test_a_capped_page_read_names_the_refusal(self):
        self.tv._SUB_HOURLY_MAX = 1
        self._open_the_circuit()
        self.assertTrue(self.tv._sub_budget_check("oneshot"), "the circuit is not open")
        r = self.tv.claude_chronicle_read(self._img(), "chronicle-uniques")
        self.assertIsInstance(r, dict)
        self.assertIn("note", r, "a capped page read answered like an empty page: %r" % (r,))
        self.assertIn("cap", str(r["note"]).lower(),
                      "the refusal does not say it was the cap: %r" % r["note"])

    def test_both_doors_are_actually_wired(self):
        """The defect was a guard nobody downstream consulted. Assert the wiring, not just the
        behaviour - the tests above would also pass against a reader that fails on a bad path."""
        import inspect
        for fn in (self.tv.claude_read, self.tv.claude_chronicle_read):
            src = inspect.getsource(fn)
            self.assertIn("_sub_budget_check", src,
                          "%s does not consult the subscription cap" % fn.__name__)
            self.assertIn("_is_throttled", src,
                          "%s does not consult the throttle" % fn.__name__)


class TestV1785TheVaultReaderSeam(unittest.TestCase):
    """v1785 — THE SEAM THAT WAS NEVER BUILT, not one that was broken.

    vault_retro.sweep() reads resp["items"]. The vault sweep was wired to claude_chronicle_read,
    whose answer carries found/notFound/sets and no items key at all — and because `note` is None on
    a GOOD chronicle read it was not even treated as a refusal: the page counted as read, the reel
    was marked swept, and no row could ever be produced. `grep -rn "def claude_vault"` returned
    nothing. Found by an adversarial review of this lane.

    The guards are in it FROM BIRTH rather than retrofitted, because REG-180 and REG-181 were both
    exactly this: a blocked lane answering in the shape of an empty shelf."""

    def setUp(self):
        sys.path.insert(0, HERE)
        import tv_diablo
        self.tv = tv_diablo
        self._keep = (tv_diablo._SUB_DAILY_MAX, list(tv_diablo._THROTTLED_UNTIL))

    def tearDown(self):
        self.tv._SUB_DAILY_MAX = self._keep[0]
        self.tv._THROTTLED_UNTIL[0] = self._keep[1][0]

    def test_the_seam_exists_and_the_sweep_is_wired_to_it(self):
        self.assertTrue(hasattr(self.tv, "claude_vault_read"),
                        "the vault reader does not exist — vault_retro can never ground a row")
        # there are TWO _vr.sweep( call sites — the free-pass COST QUOTE and the real sweep — so
        # anchor on the reader definition itself, not on whichever sweep appears first
        src = open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        i = src.find("def _reader(p, surface):")
        self.assertGreater(i, 0, "the vault sweep's reader was renamed — this test is now blind")
        body = src[i:i + 900]
        self.assertIn("claude_vault_read", body,
                      "the vault sweep is still wired to a reader whose answer has no items key")
        # STRIP COMMENTS FIRST. The v1785 note inside this function explains the defect by naming
        # claude_chronicle_read, and the first version of this assertion matched that prose — the
        # documented scar of a comment blinding a grep-based guard, reproduced immediately.
        code = "\n".join(l for l in body.split("\n") if not l.strip().startswith("#"))
        self.assertNotIn("claude_chronicle_read", code,
                         "the vault sweep still CALLS the chronicle reader")

    def test_a_throttled_vault_read_refuses_instead_of_answering_an_empty_shelf(self):
        import time as _t
        self.tv._THROTTLED_UNTIL[0] = _t.time() + 60
        r = self.tv.claude_vault_read("/nonexistent.jpg", "stash")
        self.assertIsInstance(r, dict)
        self.assertIn("note", r, "a throttled vault read answered like a real one: %r" % (r,))
        self.assertFalse(r.get("items"), "a refusal must not carry rows")

    def test_a_capped_vault_read_names_the_refusal(self):
        import time as _t
        real = self.tv._sub_budget_load
        now = _t.time()
        self.tv._sub_budget_load = lambda: {"calls": [now - 1] * 50}
        self.tv._SUB_DAILY_MAX = 1
        try:
            r = self.tv.claude_vault_read("/nonexistent.jpg", "stash")
            self.assertIn("note", r, "a capped vault read answered like an empty shelf: %r" % (r,))
            self.assertIn("cap", str(r["note"]).lower())
        finally:
            self.tv._sub_budget_load = real

    def test_it_returns_the_shape_vault_retro_actually_reads(self):
        """The contract lives in vault_retro, not here: normalize_item refuses a nameless row, so an
        invented row is impossible by construction. This asserts the CARRIER — items must be a list
        the sweep can iterate, never a chronicle answer wearing the wrong keys."""
        os.environ["TV_STUB"] = "1"
        man = os.path.join(self.tmpdir(), "man.json")
        with open(man, "w", encoding="utf-8") as fh:
            json.dump({"*#vault": {"items": [{"name": "Ist Rune", "kind": "rune", "count": 2}],
                                   "conf": 0.9}}, fh)
        os.environ["TV_STUB_MANIFEST"] = man
        try:
            r = self.tv.claude_vault_read("whatever.jpg", "stash")
            self.assertIsInstance(r, dict)
            self.assertIsInstance(r.get("items"), list, "no items list — the old defect exactly")
            self.assertEqual(r["items"][0]["name"], "Ist Rune")
            self.assertNotIn("found", r, "this is the CHRONICLE shape, not the vault one")
        finally:
            os.environ.pop("TV_STUB", None)
            os.environ.pop("TV_STUB_MANIFEST", None)

    def tmpdir(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        return d


class TestV1784TheWatchdogSaysWhyItSkipped(unittest.TestCase):
    """v1784 — SIX SITES WROTE A REASON AND NOTHING READ ONE.

    Both tick docstrings promise "a silent skip is impossible to mistake for a clean run", and
    _CHRON_AUTOREAD["skipped"]/["reads"]/["tries"] are filled in at six places — then read by
    nothing: no route, no status payload, no print, never persisted. The only production caller
    made a skip exactly what the docstrings forbid, and after a restart a visit or reel retired for
    a NAMED reason was byte-identical to one genuinely swept.

    They now ride in chronicle_sweep_state() — the payload the console and the board already read —
    and survive a restart. BOTH writers of the mark file carry them, because v1762's scar in this
    same file was a writer that knew only its own key and wiped the other's."""

    def setUp(self):
        sys.path.insert(0, HERE)
        import control_app
        self.ca = control_app
        self._skipped = dict(control_app._CHRON_AUTOREAD.get("skipped") or {})

    def tearDown(self):
        self.ca._CHRON_AUTOREAD["skipped"] = self._skipped

    def test_a_named_refusal_reaches_the_state_everything_reads(self):
        self.ca._CHRON_AUTOREAD["skipped"]["4242"] = "no ledger — offered, never guessed"
        st = self.ca.chronicle_sweep_state()
        self.assertIn("autoreadSkipped", st,
                      "the watchdog's reasons are still write-only — a skip is invisible")
        self.assertEqual(st["autoreadSkipped"].get("4242"), "no ledger — offered, never guessed")
        self.assertIn("autoreadReads", st)

    def test_BOTH_writers_of_the_mark_file_keep_the_reasons(self):
        """v1762's scar, one file down: a writer that knows only its own key wipes the other's.
        Marking a VISIT and marking a REEL must each leave the reasons intact."""
        import json as _json
        self.ca._CHRON_AUTOREAD["skipped"]["7777"] = "gave up after 2 tries"
        self.ca._chron_autoread_mark(7777)
        after_visit = _json.load(open(self.ca._CHRON_AUTOREAD_PATH, encoding="utf-8"))
        self.assertIn("7777", (after_visit.get("skipped") or {}),
                      "the VISIT writer dropped the reasons: %s" % after_visit)
        self.ca._chron_reels_mark("reel_test_1784")
        after_reel = _json.load(open(self.ca._CHRON_AUTOREAD_PATH, encoding="utf-8"))
        self.assertIn("7777", (after_reel.get("skipped") or {}),
                      "the REEL writer dropped the reasons: %s" % after_reel)
        self.assertIn("reel_test_1784", (after_reel.get("reels") or []))
        self.assertIn(7777, (after_reel.get("done") or []))


class TestV1774AThrottledSweepSealsNothing(unittest.TestCase):
    """v1774 — A THROTTLED READER ANSWERED EMPTY AND EVERY LAYER BELIEVED IT.

    _note_slot_death() flips a throttle flag when 2+ readers die inside 60s, and its own docstring
    promises to "SAY SO instead of silent empties". Only the live heartbeat cap and a status chip
    ever read that flag. The retro sweep did not.

    MEASURED, by calling the reader directly on his 08-17 frames while the console was throttled:
    a page that had returned scene='chronicle', tab='uniques', 6 names came back scene='gameplay',
    conf=None, names=[] — and the console printed "throttle cascade detected". Three sweeps in a row
    returned 39, then 22, then 0 names as it deepened, and I spent that stretch blaming my own
    threshold changes for the drop.

    WHAT MADE IT EXPENSIVE RATHER THAN MERELY WRONG. The seal rule reasons that "classified > 0 with
    pages == 0 IS a legitimate seal: the cheap classifier looked at every frame and correctly found
    no Chronicle page". A throttle counterfeits exactly that shape — the classifier was never asked.
    So a throttled sweep finished clean, found nothing, sealed the reels, and since v1766 those
    reels are never read again. His footage is not re-creatable.

    Two guards, because either alone leaves a hole: the readers refuse out loud while throttled
    (tv_diablo returns a `note`, which chronicle_retro already counts as NOT read), and a run that
    touched the throttle seals nothing at all."""

    def setUp(self):
        sys.path.insert(0, HERE)
        import control_app, tv_diablo
        self.ca, self.tv = control_app, tv_diablo
        self._until = list(self.tv._THROTTLED_UNTIL)

    def tearDown(self):
        self.tv._THROTTLED_UNTIL[0] = self._until[0]

    def test_a_throttled_chronicle_read_refuses_instead_of_answering_empty(self):
        import time as _t
        self.tv._THROTTLED_UNTIL[0] = _t.time() + 60
        r = self.tv.claude_chronicle_read("/nonexistent.jpg", "chronicle-uniques")
        self.assertIsInstance(r, dict)
        # a `note` is the shape chronicle_retro counts as refused rather than as an empty page
        self.assertIn("note", r, "a throttled read answered like a real one: %s" % r)
        self.assertIn("throttl", str(r.get("note")).lower())
        self.assertFalse(r.get("found"), "a refusal must not carry findings")

    def test_a_throttled_classify_says_NOTHING_not_gameplay(self):
        import time as _t
        self.tv._THROTTLED_UNTIL[0] = _t.time() + 60
        # None is "no answer" to classifier(); a scene string would be a verdict, and a wrong
        # verdict here skips the run and then seals the reel behind it
        self.assertIsNone(self.tv.claude_read("/nonexistent.jpg"))

    def test_the_flag_is_actually_consulted_by_the_retro_readers(self):
        """The whole defect was a flag nobody downstream read. This asserts the wiring, because the
        two tests above would also pass against a reader that happens to fail on a bad path."""
        import inspect
        for fn in (self.tv.claude_chronicle_read, self.tv.claude_read):
            src = inspect.getsource(fn)
            self.assertIn("_is_throttled", src,
                          "%s does not consult the throttle — the v891 flag is unread again"
                          % fn.__name__)


class TestReelAutoSweepCannotSurpriseHim(unittest.TestCase):
    """v1762 — the reels sweep themselves, under a cap that makes the bill predictable.

    A VISIT is what the agent journalled; a REEL is the whole recording. His Aug 17 visit named FOUR
    frames while the reel of that same session holds FIFTY-FIVE screens, so every automatic sweep
    read the slice and reported the session as empty. Reels are the bigger object AND the bigger
    bill — 20-75 classifies against a visit's handful — so the automation has to be provably
    incapable of running away, not merely intended not to.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.state = os.path.join(self.tmp, "autoread.json")
        sys.path.insert(0, HERE)
        import control_app
        self.ca = control_app
        self._path0 = control_app._CHRON_AUTOREAD_PATH
        self._on0 = control_app._CHRON_AUTOREEL_ON
        self._alive0 = control_app._agent_alive
        self._state0 = control_app.chronicle_sweep_state
        self._start0 = control_app.chronicle_sweep_start
        control_app._CHRON_AUTOREAD_PATH = self.state
        control_app._CHRON_AUTOREAD["done"] = None
        control_app._CHRON_AUTOREAD["reels"] = None
        # v1766.1 — these are module globals and the retry counter is new; leaving them dirty made
        # one test retire a reel because an EARLIER test had already spent its attempts
        control_app._CHRON_AUTOREAD["tries"] = {}
        control_app._CHRON_AUTOREAD["skipped"] = {}
        control_app._agent_alive = lambda *a, **k: False
        control_app.chronicle_sweep_state = lambda *a, **k: {"running": False}
        self.started = []
        control_app.chronicle_sweep_start = lambda **kw: (self.started.append(kw) or {"ok": True})

    def tearDown(self):
        self.ca._CHRON_AUTOREAD_PATH = self._path0
        self.ca._CHRON_AUTOREEL_ON = self._on0
        self.ca._agent_alive = self._alive0
        self.ca.chronicle_sweep_state = self._state0
        self.ca.chronicle_sweep_start = self._start0
        self.ca._CHRON_AUTOREAD["done"] = None
        self.ca._CHRON_AUTOREAD["reels"] = None
        self.ca._CHRON_AUTOREAD["tries"] = {}
        self.ca._CHRON_AUTOREAD["skipped"] = {}
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_reel(self, rid):
        """A reel is only visible to reel_dirs when its index carries frames — a bare directory is
        invisible, and a test built on one would pass for the wrong reason (it would assert nothing
        was swept because there was nothing there)."""
        import json as _json
        hist = os.path.join(self.tmp, "hist")
        d = os.path.join(hist, rid)
        os.makedirs(d, exist_ok=True)
        for n in ("f0.jpg", "f1.jpg"):
            with open(os.path.join(d, n), "wb") as fh:
                fh.write(b"\xff\xd8\xff\xd9")
        with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
            _json.dump({"frames": [{"f": "f0.jpg", "ts": 1}, {"f": "f1.jpg", "ts": 2}]}, fh)
        return hist

    def test_a_live_session_is_never_swept(self):
        """A reel that is still growing is not a finished reel."""
        self.ca._agent_alive = lambda *a, **k: True
        r = self.ca.chronicle_autoreel_tick()
        self.assertFalse(r.get("ok"))
        self.assertIn("session is live", r.get("why", ""))
        self.assertEqual(self.started, [], "it started a sweep while a session was live")

    def test_it_never_runs_two_sweeps_at_once(self):
        self.ca.chronicle_sweep_state = lambda *a, **k: {"running": True}
        r = self.ca.chronicle_autoreel_tick()
        self.assertFalse(r.get("ok"))
        self.assertEqual(self.started, [], "it started a second concurrent sweep")

    def test_an_already_swept_reel_is_never_paid_for_twice(self):
        """The whole backlog was swept once, deliberately. The watchdog starts from that line."""
        self.ca._chron_reels_mark("reel_alpha")
        self.ca._chron_reels_mark("reel_beta")
        self.ca._CHRON_AUTOREAD["reels"] = None          # force a reload from disk
        seen = self.ca._chron_reels_seen()
        self.assertEqual(seen, {"reel_alpha", "reel_beta"},
                         "the reel marks did not survive a reload: %s" % seen)

    def test_a_visit_mark_does_not_wipe_the_reel_marks(self):
        """TWO WRITERS, ONE FILE. _chron_autoread_mark knew only about "done"; if it rewrites the
        file without "reels" every swept reel is silently un-marked and the whole backlog is paid
        for again on the next tick. Same shape as the whitelist that dropped gateHeld."""
        self.ca._chron_reels_mark("reel_alpha")
        self.ca._chron_autoread_mark(1111)
        self.ca._chron_reels_mark("reel_beta")
        self.ca._chron_autoread_mark(2222)
        with open(self.state, encoding="utf-8") as fh:
            payload = json.load(fh)
        self.assertEqual(sorted(payload.get("reels") or []), ["reel_alpha", "reel_beta"],
                         "a visit mark wiped the reel list: %s" % payload)
        self.assertEqual(sorted(payload.get("done") or []), [1111, 2222],
                         "a reel mark wiped the visit list: %s" % payload)

    def test_a_finished_sweep_survives_a_restart(self):
        """v1763 — A SWEEP THAT IS NOT WRITTEN DOWN DID NOT HAPPEN.

        _CHRON_JOB is a module global, so a completed sweep lived only in the memory of the process
        that ran it. Measured on his console: the retro sweep read 1070 frames and found 30 names;
        after a restart the state was {"phase": "idle"} and apply answered "no sweep result to apply
        — run a sweep first". Worse than not sweeping, because the SWEPT MARKER is durable while the
        result was not — the reel is recorded done, never read again, and its names are gone."""
        import json as _json
        res_path = os.path.join(self.tmp, "result.json")
        self.ca._CHRON_RESULT_PATH = res_path
        with self.ca._CHRON_LOCK:
            self.ca._CHRON_JOB["result"] = {"held": [{"name": "Bloodletter"}], "totals": {"reels": 1}}
        self.ca._chron_result_save()
        self.assertTrue(os.path.isfile(res_path), "the finished sweep was never written to disk")
        # now simulate the restart: memory empty, disk intact. NULLING `result` ALONE IS NOT A
        # RESTART — a new process starts from the module literal, with phase "idle" and startedTs 0,
        # and this test used to leave whatever phase an earlier test in the class had left behind.
        # v1765 scoped rehydration to processes that have never swept (so a REFUSED sweep can no
        # longer inherit an older proposal), which made that difference load-bearing and turned this
        # test red. The fix is a faithful restart, not a looser rule.
        with self.ca._CHRON_LOCK:
            self.ca._CHRON_JOB.update({"running": False, "startedTs": 0, "phase": "idle",
                                       "error": None, "result": None})
        self.assertTrue(self.ca._chron_result_load(), "the saved sweep did not reload")
        # setUp stubs chronicle_sweep_state to {"running": False} for the reel tests, so asking IT
        # here would measure the stub and not the reload — it answered {} and the first version of
        # this assertion read that as "the findings were lost". Use the real one.
        got = self._state0().get("result") or {}
        self.assertEqual([h["name"] for h in (got.get("held") or [])], ["Bloodletter"],
                         "the reloaded sweep lost its findings: %s" % _json.dumps(got)[:160])

    def test_a_sweep_that_ran_HERE_owns_its_own_empty_result(self):
        """v1765 — REHYDRATION IS FOR "THIS PROCESS NEVER SWEPT", NEVER "THIS SWEEP FOUND NOTHING".

        Caught by test_chronicle_chain on CI, on the ship that wired the board to adopt a persisted
        proposal automatically. _chron_result_load() refilled an empty result from disk whenever
        memory had none — including immediately after a sweep the console had REFUSED out loud, so
        a previous sweep's proposal was served under the current sweep's error. The gate's words:
        "a refused sweep must leave NO proposal behind". Once the board adopts automatically, that
        stale read stops being a confusing status and becomes a wrong write into his grail.

        The trap is that the OPPOSITE property is also load-bearing and one line away: v1763 exists
        so a restarted console still knows what it swept, and the auto-adopt depends on it. Fixing
        either of these by breaking the other is the two-fixes-broke-each-other class, so this pins
        BOTH directions in one test."""
        import json as _json
        res_path = os.path.join(self.tmp, "scoped.json")
        self.ca._CHRON_RESULT_PATH = res_path
        with open(res_path, "w", encoding="utf-8") as fh:
            _json.dump({"savedTs": "999", "result": {"totals": {"uniques": 1}}}, fh)

        def _job(**kw):
            base = {"running": False, "startedTs": 0, "phase": "idle", "error": None, "result": None}
            base.update(kw)
            with self.ca._CHRON_LOCK:
                self.ca._CHRON_JOB.update(base)

        # 1) v1763 still holds: a process that has never swept DOES pick up the last one
        _job()
        self.assertTrue(self.ca._chron_result_load(),
                        "a restarted console no longer recovers its last sweep — v1763 is undone")

        # 2) a sweep that ran here and was refused keeps its own emptiness
        _job(phase="error", error="the ledger was never read")
        self.assertFalse(self.ca._chron_result_load(),
                         "a REFUSED sweep inherited an older sweep's proposal")

        # 3) and so does one that ran fine and legitimately found nothing — the case with no error
        #    to give it away, where a stale proposal reads exactly like a real find
        _job(startedTs=12345, phase="done")
        self.assertFalse(self.ca._chron_result_load(),
                         "a sweep that found nothing was handed an older sweep's findings")

    def test_saving_the_result_does_not_deadlock_the_caller(self):
        """Both call sites hold _CHRON_LOCK when they save, and threading.Lock is NOT reentrant, so
        a save that acquires it self-deadlocks. It did: tv/test_control.py hung past 600s where it
        normally finishes in 24. This calls save WHILE HOLDING the lock, which is exactly how the
        sweep does it, and fails by hanging rather than by asserting — so the runner's own timeout
        is the assertion."""
        self.ca._CHRON_RESULT_PATH = os.path.join(self.tmp, "nodeadlock.json")
        done = []

        def _save_under_lock():
            with self.ca._CHRON_LOCK:
                self.ca._CHRON_JOB["result"] = {"totals": {"reels": 0}}
                self.ca._chron_result_save()
            done.append(True)

        t = threading.Thread(target=_save_under_lock, daemon=True)
        t.start()
        t.join(timeout=10)
        self.assertTrue(done, "_chron_result_save() deadlocked while the caller held _CHRON_LOCK")

    def test_a_reel_is_spent_only_once_its_findings_ARE_ON_DISK(self):
        """v1765 — THE COMMENT DESCRIBED A PROTECTION THAT WAS NOT THERE.

        The tick marked the reel the instant chronicle_sweep_start RETURNED. That call spawns a
        daemon thread and returns immediately, so the mark landed while the sweep had barely begun,
        and the note sitting directly above it — "the marker now waits for the result to exist on
        disk; if it does not, the reel stays unswept" — was false from the day it was written.

        The failure it described was therefore live the whole time: a console killed mid-sweep, or a
        sweep that threw, left the reel marked done FOREVER with its findings never written. His
        recordings are not re-creatable. A burned reel is a permanent loss of exactly the thing the
        automation exists to protect, and it is silent — the reel simply never comes up again.

        So: the tick must hand the reel to the sweep and mark NOTHING. Marking is the runner's job,
        after the result is durable."""
        reels = self._make_reel("reel_newone")
        self.ca._chron_reels_mark("reel_old")      # a reel already spent, to prove it is skipped
        old_hist = os.environ.get("TV_HIST")
        os.environ["TV_HIST"] = reels
        try:
            r = self.ca.chronicle_autoreel_tick()
        finally:
            if old_hist is None:
                os.environ.pop("TV_HIST", None)
            else:
                os.environ["TV_HIST"] = old_hist

        self.assertTrue(r.get("ok"), "the tick refused an unswept reel: %s" % r)
        self.assertEqual(r.get("swept"), "reel_newone", "it did not pick up the new reel: %s" % r)
        # the sweep was handed the reel by name, so the runner can mark it when the result lands
        self.assertEqual([k.get("reel_id") for k in self.started], ["reel_newone"],
                         "the sweep was not told which reel it is spending: %s" % self.started)
        # ...and NOTHING is marked yet. self.started's stub never finishes, which is exactly the
        # crash: if the mark had happened here, this reel would be gone for good.
        self.assertNotIn("reel_newone", self.ca._chron_reels_seen(),
                         "the reel was burned before its findings were ever written")

    def test_a_sweep_that_dies_leaves_the_reel_RETRYABLE(self):
        """The other half of the same rule, and the one that actually costs him film: if a dead
        sweep leaves no mark, the next tick must come back for the same reel rather than moving on.
        A retry costs one re-read; not retrying costs the recording."""
        reels = self._make_reel("reel_newone")
        old_hist = os.environ.get("TV_HIST")
        os.environ["TV_HIST"] = reels
        try:
            first = self.ca.chronicle_autoreel_tick()
            # the sweep "died": no result was ever saved, so no mark was ever made
            second = self.ca.chronicle_autoreel_tick()
        finally:
            if old_hist is None:
                os.environ.pop("TV_HIST", None)
            else:
                os.environ["TV_HIST"] = old_hist
        self.assertEqual(first.get("swept"), "reel_newone")
        self.assertEqual(second.get("swept"), "reel_newone",
                         "a reel whose sweep died was never tried again: %s" % second)

    def test_a_reel_that_never_finishes_is_RETIRED_not_retried_forever(self):
        """v1766.1 — THE OTHER EDGE OF THE SAME FIX, and one I walked straight into. Not marking a
        reel until its result is durable is right; on its own it also means a sweep that ALWAYS dies
        gets restarted on every tick, spending a sweep each time and never finishing. This class is
        named for the promise that the automation is "provably incapable of running away, not merely
        intended not to" — an unbounded retry is precisely that runaway, arrived at while fixing its
        opposite. Attempts are counted and the reel is retired with its reason kept, because a reel
        that stopped being tried must never look like one that was never tried."""
        self._make_reel("reel_cursed")
        old_hist = os.environ.get("TV_HIST")
        os.environ["TV_HIST"] = os.path.join(self.tmp, "hist")
        try:
            ticks = [self.ca.chronicle_autoreel_tick() for _ in range(4)]
        finally:
            if old_hist is None:
                os.environ.pop("TV_HIST", None)
            else:
                os.environ["TV_HIST"] = old_hist
        swept = [t.get("swept") for t in ticks]
        # it retries up to the bound...
        self.assertEqual(swept[:2], ["reel_cursed", "reel_cursed"],
                         "it did not retry a reel whose sweep died: %s" % swept)
        # ...and then stops, for good, with the reason on the record
        self.assertEqual(ticks[2].get("retired"), "reel_cursed",
                         "a reel that never finishes is retried forever: %s" % ticks[2])
        self.assertIn("never wrote a result", self.ca._CHRON_AUTOREAD["skipped"].get("reel_cursed", ""))
        self.assertEqual(len(self.started), 2,
                         "it kept paying for a sweep after giving up: %d starts" % len(self.started))
        # and the fourth tick is quiet — retired means retired
        self.assertIsNone(ticks[3].get("swept"), "a retired reel came back: %s" % ticks[3])

    def test_marking_a_reel_does_not_deadlock_the_sweep(self):
        """v1765 moved the reel mark INTO _chron_sweep_run, one line after _chron_result_save() —
        which runs while the caller holds _CHRON_LOCK. That is the precise shape of the bug that
        once took this file from 24s to past 600s: threading.Lock is not reentrant, so anything
        called from in there must not reach for it. _chron_reels_mark uses its own file and an
        atomic replace, and this pins that. It fails by HANGING, so the runner timeout is the
        assertion."""
        self.ca._CHRON_AUTOREAD_PATH = os.path.join(self.tmp, "nodeadlock_reels.json")
        done = []

        def _mark_under_lock():
            with self.ca._CHRON_LOCK:
                self.ca._chron_reels_mark("reel_under_lock")
            done.append(True)

        t = threading.Thread(target=_mark_under_lock, daemon=True)
        t.start()
        t.join(timeout=10)
        self.assertTrue(done, "_chron_reels_mark() deadlocked while the caller held _CHRON_LOCK")
        self.assertIn("reel_under_lock", self.ca._chron_reels_seen())

    def test_the_off_switch_actually_stops_it(self):
        self.ca._CHRON_AUTOREEL_ON = False
        r = self.ca.chronicle_autoreel_tick()
        self.assertFalse(r.get("ok"))
        self.assertIn("off", r.get("why", ""))
        self.assertEqual(self.started, [], "it swept with the switch off")


class TestV1789TheRosterIsTheAuthorityOnWhatIsOneItem(unittest.TestCase):
    """The fold that emptied 30 of 36 rows out of his inbox — and the crash that keeps it honest.

    His queue held 36 chronicle names awaiting a hand-tick. Six were unresolved uniques. Six were
    OCR slips of items ALREADY grounded ("Battlecage" for Rattlecage, "Naglring" for Nagelring),
    which asked him to adjudicate something the ledger had already answered. Twenty-four were
    reader debris: base names the Chronicle prints for an UNFOUND row, and tooltip truncations.

    The near-miss that shaped the design: "Latent Cold Rupture" looks like a quality prefix on
    "Cold Rupture", and the first cut stripped it. The roster carries BOTH forms as separate grail
    entries — six such pairs, twelve slots. Stripping would have credited him with items he had not
    found. So the roster, not a rule that reads plausibly, decides what is one item and what is two.
    """

    def _mod(self):
        import chronicle_resolve
        return chronicle_resolve

    def test_the_six_twin_pairs_stay_two_items(self):
        r = self._mod()
        roster = r.load_roster()
        pairs = [("Latent Black Cleft", "Black Cleft"), ("Latent Bone Break", "Bone Break"),
                 ("Latent Cold Rupture", "Cold Rupture"), ("Latent Flame Rift", "Flame Rift"),
                 ("Latent Rotting Fissure", "Rotting Fissure"),
                 ("Latent Crack of the Heavens", "Crack of the Heavens")]
        for latent, bare in pairs:
            self.assertEqual(r.canonical(latent, roster), latent,
                             "%s was folded away — that merges two of his grail slots" % latent)
            self.assertEqual(r.canonical(bare, roster), bare)

    def test_a_fold_rule_that_merges_two_roster_items_CRASHES(self):
        """The guard, seen RED for its own reason. A rule that collapses distinct items must never
        quietly pick a winner — picking one credits him with a find he never made."""
        r = self._mod()
        import json as _json
        import tempfile
        import os as _os
        fd, path = tempfile.mkstemp(suffix=".json")
        _os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                _json.dump({"names": ["Cold Rupture", "cold  rupture!"]}, fh)
            with self.assertRaises(ValueError) as ctx:
                r.load_roster(path)
            self.assertIn("collapses distinct roster items", str(ctx.exception))
        finally:
            _os.unlink(path)

    def test_an_empty_roster_is_refused_rather_than_retiring_his_whole_queue(self):
        r = self._mod()
        import json as _json
        import tempfile
        import os as _os
        fd, path = tempfile.mkstemp(suffix=".json")
        _os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                _json.dump({"names": []}, fh)
            with self.assertRaises(ValueError):
                r.load_roster(path)
        finally:
            _os.unlink(path)

    def test_the_real_ocr_slips_fold_and_the_debris_is_retired_with_a_reason(self):
        r = self._mod()
        roster = r.load_roster()
        prop = {"uniques": {
            "Battlecage": [{"reel": "a", "frame": "1", "conf": 0.75}],
            "Rattlecage": [{"reel": "a", "frame": "2", "conf": 0.75}],
            "Wrist Sword": [{"reel": "a", "frame": "3", "conf": 0.75}],
            "Firel...": [{"reel": "a", "frame": "4", "conf": 0.75}],
        }}
        folded, report = r.fold_proposal(prop, roster)
        self.assertIn("Rattlecage", folded["uniques"])
        self.assertNotIn("Battlecage", folded["uniques"])
        self.assertEqual(len(folded["uniques"]["Rattlecage"]), 2,
                         "the slip's sighting did not join the real item's — the whole point")
        retired = {x["name"]: x["why"] for x in report["retired"]}
        self.assertEqual(retired.get("Wrist Sword"), "debris")
        self.assertEqual(retired.get("Firel..."), "debris")

    def test_a_retired_name_is_recorded_never_silently_dropped(self):
        """'We looked and it was not a grail item' must not read the same as 'nobody looked'."""
        r = self._mod()
        roster = r.load_roster()
        _, report = r.fold_proposal({"uniques": {"Templar Coat": [{"conf": 0.9}]}}, roster)
        self.assertEqual([x["name"] for x in report["retired"]], ["Templar Coat"])

    def test_folding_never_invents_a_name_that_is_not_on_the_roster(self):
        r = self._mod()
        roster = r.load_roster()
        names = set(roster.values())
        prop = {"uniques": {n: [{"conf": 0.9}] for n in
                            ["Battlecage", "Naglring", "Heart Garver", "Twitchthrow",
                             "Gravepalms", "The Dragon Chang(?)", "Bloodfist Shard"]}}
        folded, _ = r.fold_proposal(prop, roster)
        for n in folded["uniques"]:
            self.assertIn(n, names, "%r reached the gate and is not a roster item" % n)

    def test_an_ambiguous_near_match_stays_unfolded(self):
        """A coin flip between two of his items is not a fold."""
        r = self._mod()
        roster = {"aaaaaaaaab": "Aaaaaaaaab", "aaaaaaaaac": "Aaaaaaaaac"}
        self.assertIsNone(r.canonical("aaaaaaaaad", roster))

    def test_the_generated_roster_is_in_sync_with_bible_html(self):
        """Cheap staleness guard — no browser. bible.html is the ONE source of the roster; this
        fails the moment its roster blocks move, instead of the fold quietly answering from a stale
        artifact. Regenerate with: python3 tv/roster_sync.py --write"""
        import roster_sync
        stale, why = roster_sync.is_stale()
        self.assertFalse(stale, why)


class TestV1789TheGateReadsTheBoardsNames(unittest.TestCase):
    """The gate counted witnesses on RAW strings, so two spellings of one item never combined."""

    def test_two_spellings_of_one_item_corroborate_each_other(self):
        import chronicle_resolve as res
        import chronicle_retro as cr
        roster = res.load_roster()
        # Two tags are needed to ground, and neither spelling reaches two ALONE: the straight-quote
        # reading has cross-frame (two frames in one reel) and the curly one has nothing. Folded,
        # they share cross-frame AND cross-reel. This is the exact shape that grounded Atma\u2019s
        # Scarab and Saracen\u2019s Chance on his real ledger.
        prop = {"uniques": {
            "Atma's Scarab": [{"reel": "r1", "frame": "f1", "conf": 0.8, "lane": "claude"},
                              {"reel": "r1", "frame": "f2", "conf": 0.8, "lane": "claude"}],
            "Atma\u2019s Scarab": [{"reel": "r2", "frame": "f9", "conf": 0.8, "lane": "claude"}],
        }}
        raw = cr.apply_proposal(prop, {"uniques": [], "sets": []}, gate=cr.strict_gate())
        self.assertEqual(raw["uniques"]["added"], [],
                         "raw gating grounded a one-witness name — this test's premise is wrong")
        folded, _ = res.fold_proposal(prop, roster)
        out = cr.apply_proposal(folded, {"uniques": [], "sets": []}, gate=cr.strict_gate())
        self.assertEqual(out["uniques"]["added"], ["Atma\u2019s Scarab"])

    def test_the_control_app_folds_before_it_gates(self):
        """The wiring, not the intent. A fold that exists and is never called is the unjoined end."""
        import re
        src = _read_control_source()
        body = re.sub(r"#.*", "", src)
        # match the CALL form, never the bare name: "def _chron_fold(prop):" contains
        # "_chron_fold(prop)" too, so the obvious assertion cannot go red (learned the hard way on
        # the hunt's twin of this test the same afternoon)
        self.assertIn("= _chron_fold(prop)", body,
                      "control_app gates raw reader names — the fold is not wired in")
        self.assertGreaterEqual(body.count("= _chron_fold("), 3,
                                "not every gate site folds; the tuner would preview a different "
                                "answer from the one the live gate gives")


def _read_control_source():
    import os as _os
    p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "control_app.py")
    with open(p, "r", encoding="utf-8") as fh:
        return fh.read()


class TestV1789TheHuntAimsWhereATagCanChange(unittest.TestCase):
    """The focused hunt, and the arithmetic that condemned its first design.

    The first cut re-read the frames NEIGHBOURING a known sighting. Then the six names his gate was
    actually holding were measured:

        Latent Cold Rupture 2 sightings / 1 reel / ['cross-frame']   Toothrow 4 / 1 / ['cross-frame']
        Latent Crack of the Heavens 3 / 1 / ['cross-frame']          Witherstring 3 / 1 / ['cross-frame']
        Latent Rotting Fissure 3 / 1 / ['cross-frame']               Thundergod's Vigor 2 / 1 / ['cross-frame']

    Every one ALREADY had cross-frame — one on four sightings. witnesses() returns a SET, so another
    frame in the same reel re-adds a tag that is already there and the name stays held forever. The
    hunt was not under-powered, it was aimed at pixels that could not change the answer: its best
    possible outcome was the current outcome. It ran for 325s against three names and returned
    nothing, and nothing was the only thing it could return.

    A hunt that cannot change a verdict must not be able to spend his subscription pretending to.
    """

    def _reel(self, root, name, frames):
        import json as _json
        import os as _os
        d = _os.path.join(root, name)
        _os.makedirs(d)
        with open(_os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
            _json.dump({"frames": [{"f": f} for f in frames]}, fh)
        return d

    def test_it_never_targets_the_reel_the_name_was_already_seen_in(self):
        import tempfile
        import chronicle_hunt as ch
        root = tempfile.mkdtemp()
        self._reel(root, "reel_a", ["f%02d.jpg" % i for i in range(20)])
        self._reel(root, "reel_b", ["g%02d.jpg" % i for i in range(20)])
        ev = {"uniques": {
            "Toothrow": [{"reel": "a", "frame": "f05.jpg"}],
            "Tooth Row Anchor Below": [{"reel": "b", "frame": "g04.jpg"}],
            "Zzz Anchor Above": [{"reel": "b", "frame": "g09.jpg"}],
        }}
        targets = ch.targets_for("Toothrow", ev, root)
        self.assertTrue(targets, "it found nowhere to look — the bracket logic is not working")
        self.assertEqual({t[0] for t in targets}, {"b"},
                         "it aimed at the reel the name was already seen in, where a hit adds "
                         "cross-frame — a tag every held name already has")

    def test_the_bracket_is_between_the_alphabetical_neighbours(self):
        """The Chronicle is sorted, so the row must lie between the names either side of it."""
        import tempfile
        import chronicle_hunt as ch
        root = tempfile.mkdtemp()
        self._reel(root, "reel_a", ["f%02d.jpg" % i for i in range(4)])
        self._reel(root, "reel_b", ["g%02d.jpg" % i for i in range(30)])
        ev = {"uniques": {
            "Mid Name": [{"reel": "a", "frame": "f00.jpg"}],
            "Aaa Before": [{"reel": "b", "frame": "g10.jpg"}],
            "Zzz After": [{"reel": "b", "frame": "g14.jpg"}],
        }}
        got = sorted(t[2] for t in ch.targets_for("Mid Name", ev, root))
        self.assertTrue(got, "no bracket was produced")
        idx = [int(f[1:3]) for f in got]
        self.assertGreaterEqual(min(idx), 8, "it reached far below the lower anchor")
        self.assertLessEqual(max(idx), 16, "it reached far above the upper anchor")

    def test_a_name_with_no_anchors_in_another_reel_is_left_alone(self):
        """No bracket means no informed place to look, and a blind sweep of a 400-frame reel is not
        a focused hunt — it is the ordinary sweep with a smaller budget and a better name."""
        import tempfile
        import chronicle_hunt as ch
        root = tempfile.mkdtemp()
        self._reel(root, "reel_a", ["f00.jpg", "f01.jpg"])
        ev = {"uniques": {"Lonely": [{"reel": "a", "frame": "f00.jpg"}]}}
        self.assertEqual(ch.targets_for("Lonely", ev, root), [])

    def test_a_reel_that_scrolled_out_of_order_still_gets_aimed_correctly(self):
        """The unit is the FRAME, not the reel — and this is the scar that forced it.

        The first design bracketed between the target's alphabetical neighbours using their POSITION
        IN THE REEL, which assumes the whole reel is one monotonic scroll. One of his reels is not:
        63 names across 39 frames, with "War Traveler" at position 2 and "Pelta Lunata" at position
        8, because he scrolled back up partway through. Bracketing between those positions aimed the
        hunt for Thundergod's Vigor at the W section (Winged Harpoon, Wire Fleece, Witchwild String).
        Every read there was a guaranteed miss delivered as a clean negative — and the code reads
        correctly either way. It was caught by rendering one target frame and LOOKING at it.

        A frame is always a contiguous alphabetical page — it is one screenshot of a sorted list — so
        scoring frames by alphabetical distance needs no assumption about the reel's order at all."""
        import tempfile
        import chronicle_hunt as ch
        root = tempfile.mkdtemp()
        self._reel(root, "reel_a", ["f00.jpg"])
        self._reel(root, "reel_b", ["g%02d.jpg" % i for i in range(12)])
        ev = {"uniques": {
            "Mid Name": [{"reel": "a", "frame": "f00.jpg"}],
            # the page that BRACKETS the target sits at g07, while the reel's alphabet runs
            # backwards across the reel as a whole — exactly his jumpy reel
            "Mica Thing": [{"reel": "b", "frame": "g07.jpg"}],
            "Mist Thing": [{"reel": "b", "frame": "g07.jpg"}],
            "Zzz After": [{"reel": "b", "frame": "g01.jpg"}],
            "Aaa Before": [{"reel": "b", "frame": "g11.jpg"}],
        }}
        got = sorted(t[2] for t in ch.targets_for("Mid Name", ev, root))
        self.assertIn("g07.jpg", got, "it did not read the page that brackets the name")
        self.assertNotIn("g01.jpg", got, "it read a page alphabetically far from the name")
        self.assertNotIn("g11.jpg", got, "it read a page alphabetically far from the name")

    def test_a_hit_is_recorded_with_its_reel_so_it_earns_cross_reel(self):
        import tempfile
        import chronicle_hunt as ch
        import chronicle_retro as cr
        root = tempfile.mkdtemp()
        self._reel(root, "reel_a", ["f00.jpg"])
        self._reel(root, "reel_b", ["g%02d.jpg" % i for i in range(12)])
        ev = {"uniques": {
            "Mid Name": [{"reel": "a", "frame": "f00.jpg", "conf": 0.8},
                         {"reel": "a", "frame": "f00.jpg", "conf": 0.8}],
            "Aaa Before": [{"reel": "b", "frame": "g04.jpg"}],
            "Zzz After": [{"reel": "b", "frame": "g06.jpg"}],
        }}
        seen = []

        def read_page(path, kind):
            seen.append(path)
            return {"items": [{"name": "Mid Name"}], "conf": 0.8}

        found = ch.hunt(["Mid Name"], ev, root, read_page)
        self.assertIn("Mid Name", found)
        self.assertEqual(found["Mid Name"][0]["reel"], "b")
        merged = ev["uniques"]["Mid Name"] + found["Mid Name"]
        self.assertIn("cross-reel", cr.witnesses(merged),
                      "the hit did not earn the tag the hunt exists to earn")

    def test_the_sweep_actually_CALLS_the_hunt(self):
        """THE JOIN. chronicle_hunt can target and read perfectly and change nothing at all while
        nothing calls it — built on both ends, never wired, and silent by construction. That failure
        has cost more time on this project than any other, so the wiring gets its own assertion and
        the comments are stripped first: a mention inside a comment must never satisfy it."""
        import re
        src = _read_control_source()
        body = re.sub(r"#.*", "", src)
        # v1789 — the FIRST version of this assertion looked for "_chron_hunt_held(prop", which the
        # DEFINITION line also contains ("def _chron_hunt_held(prop, applied, ...)"). Unwiring the
        # call left the test green, and a guard that cannot go red is not a guard. Matching the
        # assignment form is what separates "it is called" from "it exists".
        self.assertIn("= _chron_hunt_held(", body,
                      "the sweep never calls the hunt — held names will sit in his inbox forever")
        self.assertIn("def _chron_hunt_held", body)

    def test_a_broken_hunt_can_never_unground_what_the_sweep_earned(self):
        import control_app as ca
        prop = {"uniques": {"Windforce": [{"reel": "r", "frame": "f", "conf": 0.9}]}}
        applied = {"uniques": {"added": ["Windforce"]}, "sets": {"added": []},
                   "held": [{"ledger": "uniques", "name": "Toothrow", "sightings": []}]}
        p2, a2, rep = ca._chron_hunt_held(prop, applied, "/nonexistent/hist/dir", None)
        self.assertEqual(a2["uniques"]["added"], ["Windforce"])
        self.assertIs(p2, prop)

    def test_it_stops_reading_a_name_once_it_has_its_hit(self):
        """One other-reel hit IS the tag. A second costs his subscription and adds nothing."""
        import tempfile
        import chronicle_hunt as ch
        root = tempfile.mkdtemp()
        self._reel(root, "reel_a", ["f00.jpg"])
        self._reel(root, "reel_b", ["g%02d.jpg" % i for i in range(12)])
        ev = {"uniques": {
            "Mid Name": [{"reel": "a", "frame": "f00.jpg"}],
            "Aaa Before": [{"reel": "b", "frame": "g02.jpg"}],
            "Zzz After": [{"reel": "b", "frame": "g09.jpg"}],
        }}
        reads = []

        def read_page(path, kind):
            reads.append(path)
            return {"items": [{"name": "Mid Name"}], "conf": 0.8}

        ch.hunt(["Mid Name"], ev, root, read_page)
        self.assertEqual(len(reads), 1, "it kept reading after it already had the answer")


if __name__ == "__main__":
    unittest.main(verbosity=1)
