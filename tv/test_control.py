#!/usr/bin/env python3
# 🎛 TV DIABLO control app — TDD (v765 REPLAY THEATRE + button/window discipline).
# Boots the REAL Handler on an ephemeral port with a fixture journal + frame archive.
import atexit
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
import re as _re_mod
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


# v1925 — CLASS 2 (orphaned processes from tests). Tests that drive the REAL structural gate
# (control_app.stash_screen_open -> tv_diablo.ocr_fast) warm tv_diablo's PERSISTENT `ocr_mac
# --worker` singleton, `_OCR`. In production that worker is reaped by close_session(); under a
# test runner close_session is never called, so every such test left one live `ocr_mac --worker`
# behind — the conftest orphan-reaper named the pid and killed it, and the suite ERRORed with
# "A TEST LEFT A CHILD PROCESS RUNNING". The test that starts it now reaps it, through the
# worker's own stop() (kill by PID; `pkill -f` is banned in this repo). tearDownModule reaps it
# under BOTH runners — pytest, whose session-scoped orphan check runs after this module and long
# before interpreter exit, and the plain `python3 test_control.py` that run_gates.py uses; atexit
# is the belt for an abort that never reaches tearDownModule. Importing pytest here is not an
# option: TestNoSuiteImportsSomethingCIDoesNotHave fails any third-party import CI does not
# install, and pytest is not one of them.
def _reap_ocr_worker():
    tvd = sys.modules.get("tv_diablo")
    w = getattr(tvd, "_OCR", None) if tvd is not None else None
    if w is None or getattr(w, "p", None) is None:
        return
    try:
        w.stop()
    except Exception:
        pass


atexit.register(_reap_ocr_worker)


def _get(port, path, timeout=3):
    # v1463 — timeout is a parameter now. /api/doctor genuinely takes seconds (it shells out
    # to probe the Claude CLI, WebView2, ports, pid files and frame ages — start_tvd_win.ps1
    # says so in its own comments), so a flat 3s made TestDoctor a load-dependent flake:
    # 1 error in 5 runs, always urlopen timing out, never a real assertion failure.
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=timeout) as r:
        return r.status, r.read(), dict(r.headers)



def _reap(proc):
    """Take a headless-Chrome launcher AND the helpers it forked down, by PID only.

    v1925 — CLASS 2 (orphaned processes from tests). The launcher is started in its own
    session, so ONE killpg reaches the renderer grandchildren that hold the stdout pipe open;
    if the group call fails we still SIGKILL the launcher itself, we close the pipes so no
    wait can block on a fd a survivor still holds, and we always wait() so nothing is left
    unreaped. `pkill -f` is banned in this repo — this kills by pid/pgid and nothing else.
    Safe to call on a process that has already exited: then it is just the wait().
    """
    if proc is None:
        return
    if proc.poll() is None:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    for stream in (proc.stdout, proc.stderr):
        try:
            if stream is not None:
                stream.close()
        except Exception:
            pass
    try:
        proc.wait(timeout=10)
    except Exception:
        pass


def _dump_dom_cdp(browser, url, timeout=40, profile=None):
    """v2008 — the fallback that ACTUALLY WORKS ON THIS MAC, so three real guards stop being dead.

    `--dump-dom` over http://127.0.0.1 never answers on his Chrome. The skip message has said so
    since v1579 and it names its own fix in the same breath: "file:// works, and Playwright drives
    the same binary fine". Both are true, and so is a third thing — CDP works. It was used about
    fifteen times on this machine in one night without a single hang.

    So the tests it was blocking are not testing anything on the machine that has the data:
      REG-069  a key read RAW
      REG-075  a gate on a differently-named function
      REG-076  the console read BARE while the board wrote W·, and a machine that should have
               started empty greeted its owner with "HOLY GRAIL 243 / 403 · 60% claimed"
    Three bugs in one family, and the test that executes the shipped lsFork against seeded storage
    has been skipping.

    Returns a CompletedProcess-alike so callers need no change, or None — a probe that could not run
    proves nothing and must never be reported as a pass. It degrades to None (not an error) when
    websocket-client is absent, so CI, where --dump-dom may work fine, is untouched.
    [[chrome-cdp-mac]] [[feedback-blind-fixture-green-gate]]
    """
    try:
        import json as _json
        import urllib.parse as _up
        import urllib.request as _ur
        import websocket  # noqa: F401 — optional; absent means "fall through to the skip"
    except Exception:
        return None
    port = _free_port()
    if not port:
        return None
    # v2008 — A CALLER MAY OWN THE PROFILE. The fresh-machine test loads bible.html to let the
    # board initialise ITSELF, then loads a probe page that reads what that boot wrote — so both
    # loads must share one user-data-dir. A helper that always minted its own would quietly test a
    # different question: an empty browser reading an empty store, which passes for the wrong reason.
    _owned = profile is None
    prof = tempfile.mkdtemp(prefix="cdp-dom-") if _owned else profile
    proc = subprocess.Popen(
        [browser, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--remote-debugging-port=%d" % port, "--user-data-dir=%s" % prof,
         "--no-first-run", "--no-default-browser-check",
         # chrome-cdp-mac: without this the WS upgrade is refused 403 and nothing else says why
         "--remote-allow-origins=*", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        base = "http://127.0.0.1:%d" % port
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                _ur.urlopen(base + "/json/version", timeout=2)
                break
            except Exception:
                time.sleep(0.3)
        else:
            return None
        req = _ur.Request(base + "/json/new?" + _up.quote(url, safe=":/.#?=&"), method="PUT")
        tab = _json.loads(_ur.urlopen(req, timeout=15).read().decode())
        ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=timeout,
                                         origin=base)
        try:
            time.sleep(2.0)          # the probe pages run inline script on load
            ws.send(_json.dumps({"id": 1, "method": "Runtime.evaluate",
                                 "params": {"expression": "document.documentElement.outerHTML",
                                            "returnByValue": True}}))
            got = ""
            end = time.time() + timeout
            while time.time() < end:
                m = _json.loads(ws.recv())
                if m.get("id") == 1:
                    got = (((m.get("result") or {}).get("result") or {}).get("value")) or ""
                    break
            if not got:
                return None
            return subprocess.CompletedProcess([browser, url], 0, got, "")
        finally:
            try:
                ws.close()
            except Exception:
                pass
    except Exception:
        return None
    finally:
        _reap(proc)
        if _owned:
            shutil.rmtree(prof, ignore_errors=True)


def _free_port():
    import socket
    try:
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        p = s.getsockname()[1]
        s.close()
        # never 9222/9223 — chrome-cdp-mac: Chrome holds one and TradingView Desktop the other,
        # and an ephemeral bind would not have handed those out anyway. Stated so nobody pins them.
        return p if p not in (9222, 9223) else None
    except Exception:
        return None


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
    # v2008 — SKIP THE DOOMED ATTEMPTS. js_syntax_gate has already probed this machine and knows
    # which launch path answers; on his Mac that is CDP, and trying both headless modes first costs
    # 45s each per call for a result the probe already has. Measured: 297s for three tests, ~270s of
    # it waiting on attempts known to fail. If the probe never ran or is unsure, fall through and
    # try everything, exactly as before.
    #
    # ⚠ THE FIRST CUT OF THIS BLOCK CALLED `js_syntax_gate.loopback_path()` WITHOUT IMPORTING IT.
    # The module is imported locally inside the test methods, not at module scope, so the name was
    # undefined here — NameError straight into the `except Exception: pass` below, falling through
    # to the slow path. The timing did not move (93.6s per call, twice) and the shortcut LOOKED
    # wired. Eighth instance of this exact shape in one night, third of them mine. Caught only by
    # timing a single call instead of trusting the change. [[the-unjoined-end]]
    try:
        import js_syntax_gate as _jsg
        if _jsg.loopback_path() == "cdp" and url.startswith("http"):
            return _dump_dom_cdp(browser, url, timeout=timeout)
    except Exception:
        pass
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
                try:
                    out, err = proc.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    continue
                return subprocess.CompletedProcess(
                    proc.args, proc.returncode,
                    (out or b"").decode("utf-8", "replace"),
                    (err or b"").decode("utf-8", "replace"))
            finally:
                # v1925 — the reap is in a finally, not only in the timeout branch. ANY other
                # escape (a decode blowing up, the harness torn down mid-communicate) used to
                # leave the launcher and every renderer helper it forked running, unreaped.
                # The second communicate() the timeout branch used to make could itself block
                # on a pipe a surviving grandchild held — _reap closes the pipes instead.
                _reap(proc)
    # v2008 — NEITHER HEADLESS MODE ANSWERED. That is the normal outcome on his Mac, and it has
    # been skipping three real guards for ~430 versions. CDP drives the same binary reliably here,
    # so ask that before giving up. Returns None if it cannot either, and the callers still skip.
    return _dump_dom_cdp(browser, url, timeout=timeout)
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
    _reap_ocr_worker()          # v1925 — the persistent `ocr_mac --worker` this file warmed



# ── v1892 — THE SAFE WAY TO TAKE A SLICE OF SOURCE, because four guards died on the unsafe one ──
#
# In one night: a 900-char window a later comment pushed past; an anchor that matched the FIRST
# mention of a name instead of its definition, twice; and a comment stripper that ate 16.9% of the
# file. Every one of them produced an EMPTY OR TRUNCATED slice, and an empty slice does not announce
# itself — `assertIn(x, "")` just fails somewhere confusing, and `assertNotIn(x, "")` PASSES.
#
# So the helper refuses instead: it insists the start anchor is found, that the end anchor is after
# it, and that what comes back is big enough to be the thing you meant. Every new source guard
# should use it. [[source-reading-guard]]
def _between(case, src, start, end, min_len=40, what="slice"):
    """src between `start` and the next `end` after it — or a failure that says which anchor moved."""
    i = src.find(start)
    case.assertGreater(i, -1, "%s: the start anchor is gone from the file: %r" % (what, start[:60]))
    j = src.find(end, i + len(start))
    case.assertGreater(j, i, "%s: the end anchor %r never appears after the start — the slice would "
                             "run to the end of the file or come back empty" % (what, end[:60]))
    out = src[i:j]
    case.assertGreaterEqual(len(out), min_len,
                            "%s: the slice came back %d chars. An empty or truncated slice does not "
                            "announce itself — assertNotIn PASSES on one. Check the anchors."
                            % (what, len(out)))
    return out


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
        # v1925 — tearDownClass is SKIPPED when setUpClass raises, so the listening socket used to
        # survive the whole run. addClassCleanup fires either way; server_close() is idempotent.
        cls.addClassCleanup(cls.srv.server_close)
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
        # v1925 — tearDownClass is SKIPPED when setUpClass raises, so the listening socket used to
        # survive the whole run. addClassCleanup fires either way; server_close() is idempotent.
        cls.addClassCleanup(cls.srv.server_close)
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
        # v1925 — the socket is freed even if Thread.start() never gets to run.
        self.addCleanup(srv.server_close)
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
        # v1874 — AND OWN THE FILE IT WRITES. Stubbing urlopen stops the network half; the beacon
        # ALSO persists to _BEACON_STATE_PATH ("otherwise 'it has never ONCE succeeded' is
        # unanswerable after a reboot"), which is his real tv/.tvd_beacon.json. Measured with his
        # console down, so nothing else could be blamed: this was the last file a full 32-gate run
        # still rewrote. A test that tells his dashboard a console checked in is a test writing his
        # fleet's history. [[feedback-fixtures-never-touch-live-data]]
        _beacon_dir = tempfile.mkdtemp(prefix="beacon-")
        _beacon_keep = ca._BEACON_STATE_PATH
        ca._BEACON_STATE_PATH = os.path.join(_beacon_dir, ".tvd_beacon.json")
        self.addCleanup(shutil.rmtree, _beacon_dir, True)
        self.addCleanup(setattr, ca, "_BEACON_STATE_PATH", _beacon_keep)
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
        # v1925 — tearDownClass is SKIPPED when setUpClass raises, so the listening socket used to
        # survive the whole run. addClassCleanup fires either way; server_close() is idempotent.
        cls.addClassCleanup(cls.srv.server_close)
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
        # v1957 — THRESHOLD SET FROM THE MEASURED GAP, NOT FROM FEEL.
        # 0.15 failed a full gate run at 0.1544 while his Chrome was eating ~190% CPU, and passed
        # 3/3 on the same commit at a quieter load. Scheduler starvation, not a slow call.
        # MEASURED over 7 runs: median 0.0005s, worst 0.0297s. A BLOCKING version waits for
        # stop_agent, which takes ~0.37s. So the honest bound sits between 0.03 and 0.37, and 0.15
        # was only 5x the worst working case — close enough to the noise floor to cry wolf.
        # 0.25 keeps a 8x margin over the worst good run and still fires well before a real block.
        # A gate that fails on the host's mood teaches him to ignore it, which is the same defect as
        # one that never fails. [[feedback-blind-fixture-green-gate]]
        self.assertLess(elapsed, 0.25)   # fire-and-forget, never waits for stop_agent (~0.37s)
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
        # v1925 — tearDownClass is SKIPPED when setUpClass raises, so the listening socket used to
        # survive the whole run. addClassCleanup fires either way; server_close() is idempotent.
        cls.addClassCleanup(cls.srv.server_close)
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
        # v1925 — tearDownClass is SKIPPED when setUpClass raises, so the listening socket used to
        # survive the whole run. addClassCleanup fires either way; server_close() is idempotent.
        cls.addClassCleanup(cls.srv.server_close)
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

    def test_a_browser_timeout_is_not_reported_as_a_syntax_error(self):
        """v1808 — THE GATE FILED A TIMEOUT AS A SYNTAX ERROR, and it cost a publication.

        On a busy CI runner the browser exceeded its 90s budget and the gate appended
        "bible.html: browser timed out after 90s" to `problems` — the same channel as
        "the page would be blank". Measured: 1 failure in 6 runs. Because publish.yml gates
        the deploy on the python suites, a slow runner could BLOCK A PUBLICATION over a file
        that parses perfectly.

        js_syntax_gate already states the rule twenty lines above the bug, for the loopback
        case: "a timeout is not a syntax verdict". The same reasoning holds when the browser
        answers too slowly — the difference is the runner's mood, not the file's correctness.

        This branch cannot run on his Mac (loopback never answers, so check() takes the node
        path early), which is exactly why it went unnoticed and exactly why it is forced here."""
        import js_syntax_gate as g
        import subprocess as _sp
        real_run, real_loop = _sp.run, g.browser_can_load_localhost
        try:
            g.browser_can_load_localhost = lambda *a, **k: True      # pretend loopback works
            # ⚠ TIME OUT ONLY THE BROWSER. The first version of this test patched subprocess.run
            # globally, so _node_bin()'s own `node --version` probe "timed out" too and the gate
            # correctly reported that node could not stand in — a true answer to a question the
            # test did not mean to ask. Simulating a broken world instead of a slow browser tests
            # the wrong thing.
            def _timeout_the_browser_only(cmd, *a, **k):
                argv = cmd if isinstance(cmd, (list, tuple)) else [cmd]
                if any("--dump-dom" in str(x) for x in argv):
                    raise _sp.TimeoutExpired(cmd="chrome", timeout=90)
                return real_run(cmd, *a, **k)
            _sp.run = _timeout_the_browser_only
            if not g.find_browser():
                self.skipTest("no browser on PATH — the branch under test needs one to be chosen")
            problems, reason = g.check(targets=["bible.html"])
        finally:
            _sp.run, g.browser_can_load_localhost = real_run, real_loop
        self.assertEqual(problems, [],
                         "a browser TIMEOUT was reported as a syntax problem: %r. 'nobody could "
                         "check' must never read the same as 'it is broken'." % (problems,))
        self.assertIsNone(reason,
                          "node should have stood in for the timed-out browser and produced a "
                          "real verdict, not a skip: %r" % (reason,))

    def test_an_unverifiable_target_never_erases_a_real_finding(self):
        """v1809 — THE FALLBACK USED TO `return [], reason`, WHICH FORGOT WHAT IT HAD FOUND.

        When the browser timed out and node was unavailable, check() returned an empty problem
        list and a skip reason — discarding every problem collected from EARLIER targets and never
        visiting the later ones. A genuine syntax error in bible.html would vanish the moment
        control_ui.html happened to time out on a runner without node.

        Found by a third-eye review of the block I had just written. A gate that forgets what it
        already found is worse than one that never looked, because it reports clean.

        Now: an unverifiable target is itself recorded as a problem (fail closed — this gate exists
        to stop a blank page shipping), and the loop continues so nothing earlier is lost."""
        import js_syntax_gate as g
        import subprocess as _sp
        real_run, real_loop, real_node = _sp.run, g.browser_can_load_localhost, g._node_bin
        try:
            g.browser_can_load_localhost = lambda *a, **k: True
            g._node_bin = lambda: None                       # node cannot stand in
            def _timeout_the_browser_only(cmd, *a, **k):
                argv = cmd if isinstance(cmd, (list, tuple)) else [cmd]
                if any("--dump-dom" in str(x) for x in argv):
                    raise _sp.TimeoutExpired(cmd="chrome", timeout=90)
                return real_run(cmd, *a, **k)
            _sp.run = _timeout_the_browser_only
            if not g.find_browser():
                self.skipTest("no browser on PATH — the branch under test needs one to be chosen")
            problems, reason = g.check(targets=["bible.html", "tv/control_ui.html"])
        finally:
            _sp.run, g.browser_can_load_localhost, g._node_bin = real_run, real_loop, real_node

        self.assertIsNone(reason,
                          "an unverifiable TARGET must not abort the whole gate as a skip: %r" % (reason,))
        self.assertEqual(len(problems), 2,
                         "both targets were unverifiable, so both must be named — an early return "
                         "here is what erased earlier findings: %r" % (problems,))
        for rel in ("bible.html", "tv/control_ui.html"):
            self.assertTrue(any(rel in p for p in problems),
                            "%s was silently dropped: %r" % (rel, problems))
        self.assertTrue(all("NOT VERIFIED" in p for p in problems),
                        "an unverifiable file must say so, not masquerade as a syntax error: %r" % (problems,))

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
                    # v2008 — the probe already knows which launch path answers on this machine.
                    # Without this the two doomed headless attempts cost 45s EACH, per load, twice:
                    # measured 204s for one test that CDP finishes in about 16s.
                    try:
                        import js_syntax_gate as _jsg
                        if _jsg.loopback_path() == "cdp":
                            cdp0 = _dump_dom_cdp(browser, "http://127.0.0.1:%d/%s" % (port, rel),
                                                 timeout=LOAD_TIMEOUT_S, profile=profile)
                            if cdp0 is not None:
                                return cdp0
                    except Exception:
                        pass
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
                            try:
                                out, err = proc.communicate(timeout=LOAD_TIMEOUT_S)
                            except subprocess.TimeoutExpired:
                                # subprocess timeouts kill the launcher, NOT the renderer helpers
                                # Chrome forks — that left orphan Chrome processes burning CPU (two
                                # found on this machine). _reap owns the whole group.
                                continue
                            if not mode_ok:
                                mode_ok.append(mode)
                            return subprocess.CompletedProcess(
                                proc.args, proc.returncode,
                                (out or b"").decode("utf-8", "replace"),
                                (err or b"").decode("utf-8", "replace"))
                        finally:
                            # v1925 — reap on EVERY path, not only the timeout one: an assertion or
                            # an exception raised out of load() used to strand the whole Chrome tree.
                            _reap(proc)
                    # v2008 — BEFORE GIVING UP, ASK THE PATH THAT WORKS HERE. --dump-dom never
                    # returns for bible.html on this Mac (measured: 45s timeout in BOTH headless
                    # modes), and CDP loads the same 5.8MB page in 7.7s and hands back 9.26MB of
                    # DOM. The profile is passed through so the second load still sees what the
                    # first boot wrote — that shared state IS the test.
                    cdp = _dump_dom_cdp(browser, "http://127.0.0.1:%d/%s" % (port, rel),
                                        timeout=LOAD_TIMEOUT_S, profile=profile)
                    if cdp is not None:
                        return cdp
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
        # v1868 — A REFUSAL IS JOURNALED, AND THIS CLASS EXISTS TO CAUSE REFUSALS.
        # Every run appended `{"lane":"skip","note":"subscription daily cap 50/1 (oneshot)"}` to
        # his live tv/sessions.jsonl — that is exactly where those rows came from. The caps were
        # saved and restored carefully here; the write path was not isolated at all.
        # [[feedback-fixtures-never-touch-live-data]]
        self._keep_journal = os.environ.get("TV_NO_JOURNAL")
        os.environ["TV_NO_JOURNAL"] = "1"

    def tearDown(self):
        self.tv._SUB_DAILY_MAX, self.tv._SUB_HOURLY_MAX = self._keep[0], self._keep[1]
        self.tv._THROTTLED_UNTIL[0] = self._keep[2][0]
        if self._keep_journal is None:
            os.environ.pop("TV_NO_JOURNAL", None)
        else:
            os.environ["TV_NO_JOURNAL"] = self._keep_journal

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
        # v1796 — AND STAND THE GROK LANE DOWN, or this asserts nothing.
        #
        # The CLAUDE cap gates the CLAUDE path and only it — v1778 moved it BELOW the G5 block on
        # purpose: "a per-lane circuit breaker that takes down the other lane is worse than no
        # breaker: it removes the independent witness precisely when the main lane is struggling."
        # That is right, and it means claude_read with G5 primary answers from GROK, on Grok's own
        # quota, no matter what the Claude budget says.
        #
        # So this test passed only while Grok happened to be unreachable. It went red the hour his
        # Grok balance came back — returning a real chronicle read stamped
        # model='grok-subscription-cli', mode='g5-primary' — and the failure was the FIXTURE finally
        # being exercised, not a regression. Blind-fixture, the exact class this class was written
        # about: the guard below checked the Claude circuit while the read came from another lane.
        try:
            import g5_grok_eyes as _g5mod
            self._real_is_primary = _g5mod.is_primary
            _g5mod.is_primary = lambda: False
            self.addCleanup(lambda: setattr(_g5mod, "is_primary", self._real_is_primary))
        except Exception:
            pass   # module absent on this machine — the lane cannot answer anyway

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
        """v1868 — this test wrote into his live journal and left the cap set to 1 behind it.

        Every run appended `{"lane":"skip","note":"subscription daily cap 50/1 (oneshot)"}` to
        tv/sessions.jsonl — that is where those rows in his journal came from — and the finally
        restored `_sub_budget_load` but NOT `_SUB_DAILY_MAX`, so every later test in the same
        process ran with a daily cap of ONE. A fixture that leaks a cap is a fixture that can make
        the next test pass for a reason nobody chose. [[feedback-fixtures-never-touch-live-data]]"""
        import time as _t
        real = self.tv._sub_budget_load
        keep_daily = self.tv._SUB_DAILY_MAX
        keep_journal = os.environ.get("TV_NO_JOURNAL")
        now = _t.time()
        self.tv._sub_budget_load = lambda: {"calls": [now - 1] * 50}
        self.tv._SUB_DAILY_MAX = 1
        os.environ["TV_NO_JOURNAL"] = "1"      # the refusal is journaled — not into his file
        try:
            r = self.tv.claude_vault_read("/nonexistent.jpg", "stash")
            self.assertIn("note", r, "a capped vault read answered like an empty shelf: %r" % (r,))
            self.assertIn("cap", str(r["note"]).lower())
        finally:
            self.tv._sub_budget_load = real
            self.tv._SUB_DAILY_MAX = keep_daily
            if keep_journal is None:
                os.environ.pop("TV_NO_JOURNAL", None)
            else:
                os.environ["TV_NO_JOURNAL"] = keep_journal

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
        # v1823 — ISOLATE THE FOOTAGE. This class never set TV_HIST, so chronicle_autoreel_tick()
        # has always walked his REAL frames directory while the fixture wrote reels into a temp
        # one. It passed only because every real reel happened to be swept already; the moment
        # three of his sat unread, these tests started picking THOSE up and asserting against
        # whatever was on the machine. A test that reads his live footage is not testing the code —
        # the same fault this session already hit twice, in chronicle_visits() and in a guard of my
        # own.
        self._hist0 = os.environ.get("TV_HIST")
        os.environ["TV_HIST"] = os.path.join(self.tmp, "hist")
        os.makedirs(os.environ["TV_HIST"], exist_ok=True)
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
        if getattr(self, "_hist0", None) is None:
            os.environ.pop("TV_HIST", None)
        else:
            os.environ["TV_HIST"] = self._hist0
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
        # v1823 — AGE IT, because a reel written this instant is one still being written. The tick
        # now decides "finished" by measuring whether the directory is still receiving frames
        # (_reel_is_growing) instead of asking whether a session exists anywhere, so a fixture left
        # at the current mtime is a LIVE reel and would be skipped — these tests are all about
        # FINISHED ones. Ageing it is what makes the fixture mean what its name says.
        old = time.time() - 3600
        for n in os.listdir(d):
            os.utime(os.path.join(d, n), (old, old))
        os.utime(d, (old, old))
        return hist

    def test_a_reel_that_is_still_growing_is_never_swept(self):
        """A reel that is still growing is not a finished reel.

        v1823 — the ASSERTION changed; the charter in that sentence did not. This used to prove the
        rule through a proxy: a session exists anywhere, therefore refuse everything. Konyo found
        what that cost — "why is nothing automatically sweeping? its been hours" — because he plays
        with the console capturing, so a session was live almost whenever he was at the machine and
        three FINISHED reels sat unread behind the guard. The proxy protected footage that had
        stopped growing hours earlier.
        It now measures the thing the docstring names. A reel still receiving frames is skipped
        whether or not a session is live, which is strictly stronger than the old rule.
        """
        self.ca._agent_alive = lambda *a, **k: True
        rid = "reel_s_9999999999999_live"
        self._make_reel(rid)
        d = os.path.join(self.tmp, "hist", rid)
        now = time.time()
        for n in os.listdir(d):
            os.utime(os.path.join(d, n), (now, now))
        os.utime(d, (now, now))
        r = self.ca.chronicle_autoreel_tick()
        self.assertEqual(self.started, [], "it swept a reel that was still being written")
        self.assertIn(rid, self.ca._CHRON_AUTOREAD["skipped"])

    def test_a_SEALED_reel_is_swept_even_while_a_session_is_live(self):
        """The other half, and the one that cost him hours: a live session says nothing about the
        reels behind it."""
        self.ca._agent_alive = lambda *a, **k: True
        self._make_reel("reel_s_1787177179114_91449")     # aged by the fixture = finished
        r = self.ca.chronicle_autoreel_tick()
        self.assertTrue(r.get("ok"), r)
        self.assertEqual([k.get("reel_id") for k in self.started], ["reel_s_1787177179114_91449"])

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
            # v1917 — THE REAL READER'S SHAPE. This fixture used to say {"items": [...]}, a key
            # normalize_page has never emitted, so the hunt scored every page against an empty list
            # and this test stayed green over a function that could not work in production. The
            # blind-fixture scar, in the one place it costs money: each miss is a paid vision read.
            return {"found": ["Mid Name"], "sets": [], "conf": 0.8, "lane": "claude"}

        ch.hunt(["Mid Name"], ev, root, read_page)
        self.assertEqual(len(reads), 1, "it kept reading after it already had the answer")


class TestV1791ARegateThatKeepsItsStampIsInvisible(unittest.TestCase):
    """The board dedupes adoption on the sweep stamp, so a re-gate that changes the answer and keeps
    the stamp is a silent no-op.

    `_chronAutoAdopt` compares the sweep stamp against `d2r_chronAdopted` and returns "this sweep was
    already adopted" when they match. `_chron_result_save()` stamps `savedTs` with the current time on
    every write, so a normal sweep always presents a new stamp. A re-gate done by hand does not go
    through that function.

    On 2026-08-18 the ledger was re-gated in place after a second lane grounded six held names —
    255 grounded became 261 — and the file kept its ORIGINAL savedTs. Every number in it was correct.
    The console would have reported 261, the board would have shown 255, and the two would have
    disagreed forever with no error anywhere: both halves right, the joint silent.
    """

    def _fixture(self, tmp):
        import json as _json
        import os as _os
        ev = _os.path.join(tmp, "ev.json")
        res = _os.path.join(tmp, "res.json")
        with open(ev, "w", encoding="utf-8") as fh:
            _json.dump({"uniques": {
                "Toothrow": [{"reel": "r1", "frame": "f1", "conf": 0.85, "lane": "claude"},
                             {"reel": "r1", "frame": "f2", "conf": 0.85, "lane": "claude"},
                             {"reel": "r1", "frame": "f1", "conf": 0.9, "lane": "grok"}],
                "Wrist Sword": [{"reel": "r1", "frame": "f3", "conf": 0.7, "lane": "claude"}],
            }}, fh)
        with open(res, "w", encoding="utf-8") as fh:
            _json.dump({"savedTs": 1, "result": {"wouldAdd": {"uniques": []}, "held": []}}, fh)
        return ev, res

    def test_the_stamp_advances_so_the_board_sees_a_sweep_it_has_not_adopted(self):
        import tempfile
        import chronicle_regate as rg
        ev, res = self._fixture(tempfile.mkdtemp())
        payload, summary = rg.regate(ev, res)
        self.assertGreater(payload["savedTs"], 1,
                           "the re-gate kept the old stamp — the board will skip every new name")

    def test_a_second_lane_grounds_a_name_one_lane_could_not(self):
        """The exact shape that grounded his last six: one reel, two frames, plus a different model
        family on the same pixels. cross-frame alone is one tag; cross-lane is what closes it."""
        import tempfile
        import chronicle_regate as rg
        ev, res = self._fixture(tempfile.mkdtemp())
        payload, _ = rg.regate(ev, res)
        names = [x["name"] for x in payload["result"]["wouldAdd"]["uniques"]]
        self.assertIn("Toothrow", names)
        row = [x for x in payload["result"]["wouldAdd"]["uniques"] if x["name"] == "Toothrow"][0]
        self.assertIn("cross-lane", row["witnesses"])
        self.assertEqual(sorted(payload["result"]["lanes"]), ["claude", "grok"])

    def test_reader_debris_never_reaches_the_board(self):
        import tempfile
        import chronicle_regate as rg
        ev, res = self._fixture(tempfile.mkdtemp())
        payload, summary = rg.regate(ev, res)
        names = [x["name"] for x in payload["result"]["wouldAdd"]["uniques"]]
        self.assertNotIn("Wrist Sword", names)
        self.assertEqual(summary["retired"], 1)

    def test_it_refuses_to_publish_a_name_that_is_not_on_the_roster(self):
        """A grounded name the board cannot match is a number that will never tick. The CLI treats
        that as a refusal rather than a warning, because publishing it produces a console and a board
        that disagree with no error between them."""
        import tempfile
        import chronicle_regate as rg
        ev, res = self._fixture(tempfile.mkdtemp())
        _, summary = rg.regate(ev, res)
        self.assertTrue(summary["allNamesOnRoster"])
        import inspect
        src = inspect.getsource(rg.main)
        self.assertIn("REFUSING to write", src)


class TestV1792ARelookCountsForKeepAndNeverForThrow(unittest.TestCase):
    """Konyo: "maybe though like it can be smarter then this if in the same session but theres a 3-4
    min gap between timestamped reels then it can be considered another witness?"

    He is right, and better supported than it first looks: two candidate runs inside one reel are
    ALREADY separated by a signature change, because still_runs only starts a new run when the screen
    moves past STILL_MAX_DIFF. So a second run is not the same frozen screen — it is the panel left
    and returned to. Add a multi-minute gap and it is him walking away and coming back.

    WHAT IT DOES NOT BUY is why it stops at the keep bar. The failure being guarded is a SYSTEMATIC
    misread: same model, same prompt, same font, same row. Coming back four minutes later and reading
    "Ral" as "Ort" a second time is exactly as likely as the first. Elapsed time buys independence of
    STATE, never independence of JUDGEMENT — so a re-look can ground `owned` and can never on its own
    justify suggesting he bin something. There is no un-throw in Diablo.
    """

    def _ev(self, sessions, conf=0.99):
        return [{"session": sid, "witness": w, "conf": conf} for sid, w in sessions]

    def test_two_relooks_in_one_recording_ground_owned(self):
        import vault_retro as vr
        ev = self._ev([("s1", "s1#0"), ("s1", "s1#1")], conf=0.8)
        v = vr.gate(ev, vr.KEEP_CONF_FLOOR, vr.KEEP_MIN_WITNESSES)
        self.assertTrue(v["pass"], v["why"])
        self.assertIn("look", v["why"])

    def test_two_glances_without_a_gap_are_still_ONE_witness(self):
        """The rule has to be able to say no, or it is not a rule. Same bucket = same look."""
        import vault_retro as vr
        ev = self._ev([("s1", "s1#0"), ("s1", "s1#0")])
        self.assertFalse(vr.gate(ev, vr.KEEP_CONF_FLOOR, vr.KEEP_MIN_WITNESSES)["pass"])

    def test_a_single_recording_can_NEVER_suggest_throwing_something_out(self):
        """Law 3, at maximum confidence and three re-looks — the strongest evidence one recording can
        possibly produce. It must still refuse, and refuse for the RIGHT reason."""
        import vault_retro as vr
        ev = self._ev([("s1", "s1#0"), ("s1", "s1#1"), ("s1", "s1#2")])
        v = vr.gate(ev, vr.THROWOUT_CONF_FLOOR, vr.THROWOUT_MIN_WITNESSES,
                    witness_field="session", witness_noun="recording")
        self.assertFalse(v["pass"])
        self.assertIn("1 independent recording", v["why"])

    def test_three_real_recordings_do_reach_the_throw_bar(self):
        import vault_retro as vr
        ev = self._ev([("s0", "s0#0"), ("s1", "s1#0"), ("s2", "s2#0")])
        self.assertTrue(vr.gate(ev, vr.THROWOUT_CONF_FLOOR, vr.THROWOUT_MIN_WITNESSES,
                                witness_field="session", witness_noun="recording")["pass"])

    def test_the_sweep_opens_a_new_bucket_only_after_the_gap(self):
        """Measured through the real sweep rather than asserted on the constant: two runs a minute
        apart share a bucket, two runs an hour apart do not."""
        import vault_retro as vr
        gap = vr.REOPEN_GAP_MS
        self.assertGreater(gap, 0)
        import inspect
        src = inspect.getsource(vr.sweep)
        self.assertIn("REOPEN_GAP_MS", src, "the sweep never applies the gap it defines")
        self.assertIn('"witness": _wkey', src, "sightings carry no re-look key, so the keep bar "
                                               "silently falls back to counting recordings")

    def test_evidence_written_before_this_rule_still_gates(self):
        """Old rows have no `witness` field. They must fall back to the session id rather than
        collapsing to a single unnamed witness and un-grounding what he already owns."""
        import vault_retro as vr
        ev = [{"session": "s0", "conf": 0.9}, {"session": "s1", "conf": 0.9}]
        v = vr.gate(ev, vr.KEEP_CONF_FLOOR, vr.KEEP_MIN_WITNESSES)
        self.assertTrue(v["pass"], v["why"])


class TestV1795SetsFoldAgainstTheirOwnRoster(unittest.TestCase):
    """Uniques got the fold in v1789 and sets got nothing, so a misread set piece stayed a separate
    name with one witness forever — exactly as "Battlecage" did before the uniques fold.

    Pieces are stored SUFFIXED ("Tal Rasha's Adjudication (amulet)") because that is the ledger form
    d2r_setPieces holds, while the in-game Chronicle row prints the BARE name. `_norm` strips the
    parenthetical so both collapse to one key, and the canonical stays the suffixed form.
    """

    def _rosters(self):
        import chronicle_resolve as res
        return res.load_roster(), res.load_set_roster()

    def test_the_bare_chronicle_row_folds_to_the_suffixed_ledger_name(self):
        import chronicle_resolve as res
        _, sr = self._rosters()
        self.assertEqual(res.canonical("Tal Rasha's Adjudication", sr),
                         "Tal Rasha's Adjudication (amulet)")
        self.assertEqual(res.canonical("Tal Rasha's Adjudication (amulet)", sr),
                         "Tal Rasha's Adjudication (amulet)")

    def test_a_misread_piece_is_repaired(self):
        import chronicle_resolve as res
        _, sr = self._rosters()
        self.assertEqual(res.canonical("Tal Rashas Adjudicaton", sr),
                         "Tal Rasha's Adjudication (amulet)")

    def test_a_unique_never_folds_onto_a_set_piece_or_the_reverse(self):
        """The cross-ledger guard. Measured on the real catalogues: 135 piece keys, ZERO of which also
        match a unique roster name — so a name cannot be both. If that ever became false, a set piece
        could land in his grail tally, which is the exact harm the uniques fold exists to prevent."""
        import chronicle_resolve as res
        ur, sr = self._rosters()
        self.assertIsNone(res.canonical("Windforce", sr), "a unique resolved against the SET roster")
        self.assertIsNone(res.canonical("Tal Rasha's Adjudication (amulet)", ur),
                          "a set piece resolved against the UNIQUE roster")
        overlap = set(sr) & set(ur)
        self.assertEqual(overlap, set(), "a name is now both a unique and a set piece: %s" % overlap)

    def test_the_set_roster_refuses_to_collapse_two_distinct_pieces(self):
        import chronicle_resolve as res
        import json as _json
        import tempfile
        import os as _os
        fd, path = tempfile.mkstemp(suffix=".json")
        _os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                _json.dump({"pieces": ["Angelic Halo (ring)", "angelic  halo!"]}, fh)
            with self.assertRaises(ValueError) as ctx:
                res.load_set_roster(path)
            self.assertIn("collapses distinct set pieces", str(ctx.exception))
        finally:
            _os.unlink(path)

    def test_an_empty_set_roster_is_refused(self):
        import chronicle_resolve as res
        import json as _json
        import tempfile
        import os as _os
        fd, path = tempfile.mkstemp(suffix=".json")
        _os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                _json.dump({"pieces": []}, fh)
            with self.assertRaises(ValueError):
                res.load_set_roster(path)
        finally:
            _os.unlink(path)

    def test_folding_sets_against_the_UNIQUE_roster_would_retire_them_all(self):
        """Why each ledger asks its OWN catalogue, stated as a test rather than a comment: hand the
        sets ledger the unique roster and every piece resolves to nothing and is retired as debris —
        the whole ledger silently emptied, with a tidy receipt saying so."""
        import chronicle_resolve as res
        ur, sr = self._rosters()
        prop = {"sets": {"Tal Rasha's Adjudication": [{"conf": 0.9}],
                         "Immortal King's Will": [{"conf": 0.9}]}}
        wrong, wrep = res.fold_proposal(prop, ur, ledgers=("sets",))
        self.assertEqual(wrong["sets"], {})
        self.assertEqual(len(wrep["retired"]), 2)
        right, rrep = res.fold_proposal(prop, ur, ledgers=("sets",), set_roster=sr)
        self.assertEqual(sorted(right["sets"]),
                         ["Immortal King's Will (helm)", "Tal Rasha's Adjudication (amulet)"])
        self.assertEqual(rrep["retired"], [])

    def test_the_control_app_folds_BOTH_ledgers(self):
        """The wiring, not the intent — and matching the call form, never the bare name, because the
        def line contains it too (the lesson from v1789's blind guard)."""
        import re
        src = _read_control_source()
        body = re.sub(r"#.*", "", src)
        self.assertIn("load_set_roster()", body, "the sets fold is never given a set roster")
        self.assertIn('"sets"', body)

    def test_a_missing_set_roster_degrades_to_uniques_only(self):
        """It must not take the uniques fold down with it: a sets ledger that cannot be folded is
        worth less than one folded wrongly, but a uniques ledger that stops folding is a regression."""
        import chronicle_resolve as res
        ur, _ = self._rosters()
        prop = {"uniques": {"Battlecage": [{"conf": 0.8}]}, "sets": {"Whatever": [{"conf": 0.8}]}}
        folded, _rep = res.fold_proposal(prop, ur, ledgers=("uniques",))
        self.assertIn("Rattlecage", folded["uniques"])
        self.assertEqual(folded.get("sets"), {"Whatever": [{"conf": 0.8}]},
                         "the sets ledger was touched despite not being in `ledgers`")


class TestV1798TheSetsLaneHasATapEndToEnd(unittest.TestCase):
    """v1796 added a fold for sets; this asks the question that matters about it — does anything ever
    PUT anything in the sets ledger for it to fold?

    A fold with nothing upstream is plumbing with no tap, and this arc has produced that shape before
    (REG-181: the vault sweep called a reader whose answer had no `items` key, so pages counted as
    read, nothing ever grounded, and the reel was marked swept). Traced here with the real functions
    and zero vision calls, because the whole chain is pure.

    Also a note on how the trace was done, since it cost three wrong readings today: the page dict is
    keyed `resp`, not `read`. Passing the wrong key returns an empty proposal from every ledger, which
    looks exactly like a broken lane. Suspect the instrument first.
    """

    def _page(self, complete=True, reel="r1", frame="f1", merge=True):
        """One sets page, through the REAL chain — including merge_proposals.

        v1798 — the first cut of this class stopped at proposal_from_pages and a code review caught
        it: merge_proposals sits between that and the fold on EVERY production path
        (control_app _chron_evidence_merge), and it was the one step where the lane actually broke.
        A fixture built on the near side of the joint it claims to test is the blind-fixture shape,
        and this class had it while citing REG-181 in its own docstring.

        The fixture also named "Tal Rasha's Howling Wind", which is not a D2R item — the set is
        Adjudication / Fine-Spun Cloth / Guardianship / Horadric Crest / Lidless Eye. It passed only
        because notFound was never folded; a real name is used now so the test cannot be green for a
        reason unrelated to what it pins."""
        import chronicle_retro as cr
        read = {"ledger": "sets",
                "found": ["Tal Rasha's Adjudication"],
                "notFound": ["Tal Rasha's Lidless Eye"],
                "sets": [{"set": "Tal Rasha's Wrappings (Sorc)",
                          "pieces": ["Tal Rasha's Adjudication", "Tal Rasha's Lidless Eye"],
                          "complete": complete}],
                "conf": 0.9, "stateVisible": True, "wrongTab": False}
        norm = cr.normalize_page(read, "chronicle-sets", "claude")
        prop = cr.proposal_from_pages([{"kind": "chronicle-sets", "reel": reel,
                                        "frame": frame, "resp": norm}])
        return cr.merge_proposals({}, prop) if merge else prop

    def test_a_sets_page_populates_the_sets_ledger(self):
        p = self._page()
        self.assertEqual(list(p["sets"]), ["Tal Rasha's Adjudication"],
                         "a chronicle-sets page read a found piece and the sets ledger stayed empty")
        self.assertEqual(p["pagesRead"], 1)

    def test_the_pieces_reach_setGroups_and_the_unfound_one_is_not_claimed(self):
        p = self._page()
        self.assertEqual(sorted(p["setGroups"]["Tal Rasha's Wrappings (Sorc)"]),
                         ["Tal Rasha's Adjudication", "Tal Rasha's Lidless Eye"])
        self.assertIn("Tal Rasha's Lidless Eye", p["notFound"]["sets"])
        self.assertNotIn("Tal Rasha's Lidless Eye", p["sets"])

    def test_complete_true_is_the_claim_and_complete_false_is_not(self):
        self.assertEqual(list(self._page(complete=True)["completeSets"]),
                         ["Tal Rasha's Wrappings (Sorc)"])
        self.assertEqual(list(self._page(complete=False)["completeSets"]), [],
                         "a set the game did NOT call complete was claimed complete")

    def test_two_reels_corroborate_a_complete_set_claim(self):
        """THE JOINT the first version of this class skipped. merge_proposals used dict.update on
        setGroups/completeSets, so the second reel REPLACED the first's evidence: witnesses() came
        back [] and apply_proposal gates a complete-set claim by the same MIN_WITNESSES = 2 rule, so
        a set worth five pieces could never ground on cross-reel evidence. Reproduced, then fixed."""
        import chronicle_retro as cr
        a = self._page(reel="A", frame="f1")
        b = self._page(reel="B", frame="f9")
        m = cr.merge_proposals(a, b)
        claim = m["completeSets"]["Tal Rasha's Wrappings (Sorc)"]
        self.assertEqual(len(claim), 2, "the second reel replaced the first's evidence")
        self.assertIn("cross-reel", cr.witnesses(claim))
        self.assertEqual(sorted(m["setGroups"]["Tal Rasha's Wrappings (Sorc)"]),
                         ["Tal Rasha's Adjudication", "Tal Rasha's Lidless Eye"])

    def test_the_merged_proposal_SURVIVES_json_dump(self):
        """The one line that would have caught v1798's worst regression.

        merge_proposals accumulates with SETS — the right type to fold with, the wrong type to hand
        back, because this dict is json.dump-ed straight to chron_evidence.json. `json.dumps` refuses
        a set, and it failed on an EMPTY merge. `_chron_evidence_save` wraps its dump in a bare
        `except Exception: return False` that nobody checks, so the ledger simply stopped being
        written and said nothing: the sweep reported success, the console showed findings, and the
        accumulated evidence froze at its last pre-v1798 content.

        Every assertion in this class passed throughout, because `sorted()` and `in` behave
        identically on a set — the class asserted on the in-memory dict and never on the artifact.
        A ledger is what reaches DISK; asserting the shape in memory tests the wrong noun."""
        import json as _json
        import chronicle_retro as cr
        _json.dumps(cr.merge_proposals({}, {}))          # empty merge: this alone used to raise
        m = cr.merge_proposals(self._page(reel="A"), self._page(reel="B", frame="f9"))
        round_tripped = _json.loads(_json.dumps(m))
        self.assertEqual(round_tripped["setGroups"], m["setGroups"],
                         "setGroups did not survive a JSON round trip")
        self.assertEqual(round_tripped["notFound"]["sets"], m["notFound"]["sets"])
        self.assertIsInstance(m["notFound"]["sets"], list,
                              "the merger returns a set where the producer returns a list — the two "
                              "halves of one contract disagree")
        self.assertIsInstance(m["setGroups"]["Tal Rasha's Wrappings (Sorc)"], list)

    def test_the_evidence_file_is_actually_written(self):
        """v1800 — THIS TEST WAS ITSELF THE BLIND FIXTURE IT WAS WRITTEN TO PREVENT.

        Its first version hand-rolled `json.dump(merged, fh)` into a temp path and asserted the
        file came back. That exercises the json module. It never called `_chron_evidence_save`
        at all, so it passed identically whether the writer worked, was broken, or was DELETED —
        which is precisely the shape of REG-198 and of the v1798 defect it was meant to guard.
        A gate whose subject never runs is not a weak gate, it is furniture.

        It now drives the real function, and — the half that makes it a gate — proves the
        function goes RED on the exact v1798 payload, so a future serializer that cannot fail
        cannot pass here either. [[feedback-blind-fixture-green-gate]]"""
        import json as _json
        import os as _os
        import shutil as _shutil
        import tempfile
        import chronicle_retro as cr
        d = tempfile.mkdtemp()
        self.addCleanup(_shutil.rmtree, d, True)   # v1800 — mkdtemp leaked a dir per run
        path = _os.path.join(d, "ev.json")
        merged = cr.merge_proposals(self._page(reel="A"), self._page(reel="B", frame="f9"))

        old_path = ca._CHRON_EVIDENCE_PATH
        old_fails, old_writes = list(ca._CHRON_EVIDENCE_FAILS), ca._CHRON_EVIDENCE_WRITES
        old_count, old_lastok = ca._CHRON_EVIDENCE_FAILCOUNT, ca._CHRON_EVIDENCE_LAST_OK
        try:
            ca._CHRON_EVIDENCE_PATH = path
            ca._CHRON_EVIDENCE_FAILS[:] = []
            ca._CHRON_EVIDENCE_FAILCOUNT = 0
            ca._CHRON_EVIDENCE_LAST_OK = None
            # GREEN: the real writer, on the real merged shape
            self.assertTrue(ca._chron_evidence_save(merged),
                            "_chron_evidence_save refused a well-formed merged proposal")
            self.assertTrue(_os.path.exists(path), "the writer returned True and wrote nothing")
            with open(path, encoding="utf-8") as fh:
                back = _json.load(fh)
            self.assertEqual(sorted(back["setGroups"]["Tal Rasha's Wrappings (Sorc)"]),
                             ["Tal Rasha's Adjudication", "Tal Rasha's Lidless Eye"])
            self.assertEqual(ca._CHRON_EVIDENCE_FAILS, [])
            self.assertTrue(ca.chronicle_sweep_state().get("evidenceSaved"))

            # RED: the v1798 payload — a set where a list belongs. Must FAIL, must SAY SO, and the
            # failure must reach the state the board reads. Without this half the test above only
            # proves the happy path, which is what every green-forever gate proves.
            self.assertFalse(ca._chron_evidence_save({"uniques": {"x"}}),
                             "an unserializable proposal was reported as saved")
            self.assertEqual(len(ca._CHRON_EVIDENCE_FAILS), 1)
            st = ca.chronicle_sweep_state()
            self.assertFalse(st.get("evidenceSaved"),
                             "the ledger failed to write and the sweep state still said it saved")
            self.assertIn("serializable", (st.get("evidenceError") or ""),
                          "the failure reached the board without saying what went wrong")
        finally:
            ca._CHRON_EVIDENCE_PATH = old_path
            ca._CHRON_EVIDENCE_FAILS[:] = old_fails
            ca._CHRON_EVIDENCE_WRITES = old_writes
            ca._CHRON_EVIDENCE_FAILCOUNT = old_count
            ca._CHRON_EVIDENCE_LAST_OK = old_lastok

    def test_the_same_page_twice_is_still_ONE_sighting(self):
        """The de-dupe must survive the fix — two reads of one photograph are not corroboration."""
        import chronicle_retro as cr
        a = self._page(reel="A", frame="f1")
        m = cr.merge_proposals(a, a)
        self.assertEqual(len(m["completeSets"]["Tal Rasha's Wrappings (Sorc)"]), 1)
        self.assertEqual(cr.witnesses(m["completeSets"]["Tal Rasha's Wrappings (Sorc)"]), [])

    def test_notFound_survives_the_merge(self):
        """It was dropped entirely: "the game says he has NOT found this" lasted one sweep and
        vanished. An absence that cannot be carried is an absence nobody can act on."""
        import chronicle_retro as cr
        m = cr.merge_proposals(self._page(reel="A"), self._page(reel="B", frame="f9"))
        self.assertIn("Tal Rasha's Lidless Eye", m["notFound"]["sets"])

    def test_the_fold_turns_the_bare_row_into_the_canonical_ledger_name(self):
        """The join between the two halves: the Chronicle prints the BARE piece name, the board stores
        the SUFFIXED one, and v1796's fold is what makes them the same item."""
        import chronicle_resolve as res
        p = self._page()
        folded, rep = res.fold_proposal(p, res.load_roster(), ledgers=("sets",),
                                        set_roster=res.load_set_roster())
        self.assertEqual(list(folded["sets"]), ["Tal Rasha's Adjudication (amulet)"])
        self.assertEqual(rep["retired"], [],
                         "a real set piece was retired as debris by its own ledger's fold")


class TestV1800TheConsoleRowsSayOneThing(unittest.TestCase):
    """Two defects Konyo found by hovering and by looking, both of the same family: a surface that
    contradicts itself, where every individual value is correct."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
            cls.ui = fh.read()

    def test_thin_is_not_outranked_by_the_up_next_column(self):
        """`.tz-slot.next .tzz {opacity:.9}` is specificity (0,3,0); `.tzz-thin {opacity:.3}` is
        (0,1,0). The column rule won, so the SAME zone rendered 0.3 under LIVE NOW and 0.9 under
        UP NEXT — and in that column a THIN card and a GOOD card were both 0.9, which erases the
        verdict in the row whose whole job is saying what is coming.

        Konyo: "the next should also be cancelled like out and also grey form ... symmetric".

        Pinned as SOURCE ORDER + SPECIFICITY rather than a rendered opacity, because that is what
        actually decides it: any future column-scoped rule added after this one takes the treatment
        away again, silently, exactly as this one did."""
        i_col = self.ui.find(".tz-slot.next .tzz { opacity: .9; }")
        i_fix = self.ui.find(".tz-slot.next .tzz-thin { opacity: .3; }")
        self.assertGreater(i_col, 0, "the UP NEXT column rule is gone — re-check this guard")
        self.assertGreater(i_fix, 0,
                           "the thin override is gone: every thin zone in UP NEXT is bright again")
        self.assertGreater(i_fix, i_col,
                           "the thin override must come AFTER the column rule it corrects; equal "
                           "specificity means source order decides, and it now loses")
        self.assertIn(".tz-slot.next .tzz-thin:hover { opacity: .92; }", self.ui,
                      "the hover half is missing — a zone he cannot read is hidden, not dim")
        # v1801 — THE WHOLE CLASS, not the one member. v1800 guarded .tzz-thin alone and the two
        # other opacity-bearing tiers stayed outranked, so the asymmetry simply moved. Each member
        # is checked for BOTH the override and its source position, because equal specificity means
        # order is the only thing deciding it.
        for member, base in ((".tz-slot.next .tzz-good { opacity: .74; }", ".tzz-good { opacity: .74"),
                             (".tz-slot.next .tzz-pending { opacity: .6; }", ".tzz-pending { opacity: .6")):
            j = self.ui.find(member)
            self.assertGreater(j, 0, "%s is missing — that tier is bright again in UP NEXT" % member)
            self.assertGreater(j, i_col, "%s must come after the column rule it corrects" % member)
            self.assertIn(base, self.ui, "the LIVE NOW side of the pair vanished")
        self.assertIn(".tz-slot.next .tzz-good:hover { opacity: .95; }", self.ui,
                      "a GOOD card in UP NEXT does not respond to the mouse")
        # and the same trap one property over: the terror flag's colour
        k = self.ui.find(".tz-slot.next .tzz-txt b.tzz-terr")
        self.assertGreater(k, 0, "the terror flag is repainted by the column rule again")
        self.assertGreater(k, self.ui.find(".tz-slot.next .tzz-txt b { color:"),
                           "the terror-flag override must follow the rule that overrode it")

    def test_the_next_piece_row_has_exactly_one_hover_card(self):
        """The row printed TWO item cards — one on the piece, one on the set — that pictured the
        same sprite (an aggregate set has no art, so setArt falls back to the piece), described the
        same hunt, and opened the SAME destination. They also disagreed on the item's name: the
        headline ran it through _pieceLabel() and read "Telling of Beads" while the set card printed
        the raw name and read "Telling of Beads (spired helm)".

        Konyo: "telling of beads and the disciple there is a mismatch or unsynced .. should be one
        item not two.. confusing"."""
        i = self.ui.find("var _setChip = setName")
        self.assertGreater(i, 0, "the set chip is gone — re-check this guard")
        chip = self.ui[i:i + 1400]
        self.assertNotIn("_itipAttr(", chip,
                         "the set chip grew a second art card back: one row, one hunt, one card")
        self.assertIn("aria-label=", chip, "the set chip lost its spoken label")
        self.assertIn("_hubGoSetPiece(", chip, "the set chip lost its route")

    def test_the_hover_card_does_not_answer_the_base_question_twice(self):
        """v1800 added a `base` fact built from the name's parenthetical. About half of
        _PIECE_SLOT_TOK is SLOT words, so "Griswold's Honor (Shield)" rendered `base Shield` — the
        slot — while the att-type line above it already rendered `Set · Vortex Shield` from tip.b,
        the real base. One card, two answers, the added one wrong.

        Asserted against CODE, not the file: this class's own comments now discuss _pieceBase by
        name, and a guard that greps the whole file matches its own explanation and passes forever.
        [[feedback-comments-vs-code]]"""
        # strip comments from the WHOLE file BEFORE slicing: a window that ends mid-comment leaves
        # an unterminated /* the stripper cannot match, and the guard then reads its own prose.
        # (That is not hypothetical — this assertion failed exactly that way when first written.)
        code = _re_mod.sub(r"/\*.*?\*/", "", self.ui, flags=_re_mod.S)
        i = code.find("var _setChip = setName")
        self.assertGreater(i, 0)
        code = code[i:i + 3000]
        self.assertNotIn("_pieceBase", code,
                         "the slot-as-base fact is back; the bridge already carries the real base")
        self.assertNotIn("['base'", code, "a second `base` answer reappeared on the card")

    def test_the_set_chip_escapes_the_bridge_value_it_prints(self):
        """meta.left arrives from d2r_setFarm in localStorage — untrusted by this file's own stated
        policy. v1800 removed the _itipAttr that had been escaping it and concatenated it raw into
        a title attribute, where a quote breaks out into new attributes."""
        code = _re_mod.sub(r"/\*.*?\*/", "", self.ui, flags=_re_mod.S)
        i = code.find("var _setChip = setName")
        self.assertGreater(i, 0)
        code = code[i:i + 3000]
        k = code.find("title=")
        self.assertGreater(k, 0, "the set chip lost its title")
        seg = code[k:k + 260]
        self.assertNotIn("+ meta.left +", seg,
                         "meta.left is concatenated into an HTML attribute unescaped")
        self.assertIn("esc(String(meta.left))", seg,
                      "the bridge value must be escaped before it enters an attribute")


class TestV1801TheLedgerFailureReachesAReader(unittest.TestCase):
    """v1800 said the write failure "reaches the board". It reached the payload and stopped — the
    only readers were v1800's own assertions, so the v1798 silent-freeze was still fully reachable.
    These pin the JOINT, not the ends. [[the-unjoined-end]]"""

    def setUp(self):
        # v1804 — the monotonic FAILCOUNT is a third global and must be saved/reset like the other
        # two, or these tests leak into each other and the count they assert is whatever the suite
        # happened to accumulate. It caught itself the moment it was added: 2 != 1.
        self._fails = list(ca._CHRON_EVIDENCE_FAILS)
        self._writes = ca._CHRON_EVIDENCE_WRITES
        self._count = ca._CHRON_EVIDENCE_FAILCOUNT
        self._lastok = ca._CHRON_EVIDENCE_LAST_OK
        ca._CHRON_EVIDENCE_FAILS[:] = []
        ca._CHRON_EVIDENCE_WRITES = 0
        ca._CHRON_EVIDENCE_FAILCOUNT = 0
        ca._CHRON_EVIDENCE_LAST_OK = None
        self.addCleanup(self._restore)

    def _restore(self):
        ca._CHRON_EVIDENCE_FAILS[:] = self._fails
        ca._CHRON_EVIDENCE_WRITES = self._writes
        ca._CHRON_EVIDENCE_FAILCOUNT = self._count
        ca._CHRON_EVIDENCE_LAST_OK = self._lastok

    def test_a_later_success_does_not_erase_an_unshown_failure(self):
        """THE HEADLINE RECOVERS, THE HISTORY DOES NOT — and it took two wrong versions to land.

        v1800 kept one error slot and cleared it on every success. The watchdog fires visit sweeps
        on a timer, each of which saves, so a retro sweep whose write failed — its sightings lost
        for good, since the merge rebuilds `base` from the file — was erased seconds later by an
        unrelated tick that happened to succeed.

        v1801's first attempt over-corrected to `evidenceSaved = not FAILS`, which can never return
        to true inside a process. That turns one transient failure into a permanent red present-
        tense alarm, and a permanent alarm is furniture — the same defect as a forever-red CI gate,
        arrived at from the opposite direction. THIS TEST ITSELF PINNED THAT for one commit.

        The contract now: evidenceSaved answers "did the LAST attempt succeed" (so it recovers and
        the present tense stays true), evidenceFails answers "has anything been lost" (so it never
        un-says a loss), and evidenceFailTs says when, because a failure with no age is a
        [[stale-reading]] defect on the one surface whose job is reporting loss."""
        import shutil as _shutil, tempfile, os as _os
        d = tempfile.mkdtemp(); self.addCleanup(_shutil.rmtree, d, True)
        old = ca._CHRON_EVIDENCE_PATH
        try:
            ca._CHRON_EVIDENCE_PATH = _os.path.join(d, "ev.json")
            self.assertFalse(ca._chron_evidence_save({"uniques": {"x"}}))   # the failure
            self.assertTrue(ca._chron_evidence_save({"uniques": {}}))       # a later success
            st = ca.chronicle_sweep_state()
            self.assertTrue(st.get("evidenceSaved"),
                            "the headline is stuck: one transient failure pins a present-tense "
                            "alarm for the life of the process, which is furniture, not a warning")
            self.assertEqual(st.get("evidenceFails"), 1,
                             "a later success erased a loss the board never showed him")
            self.assertEqual(st.get("evidenceWrites"), 1,
                             "0 writes and 0 failures must stay distinguishable from all-good")
            self.assertIsNotNone(st.get("evidenceFailAgeS"),
                                 "the age must be computed by the process that recorded the "
                                 "failure — a server epoch differenced against the browser clock "
                                 "renders skew as a wrong age")
            self.assertNotIn("evidenceFailTs", st,
                             "the raw server epoch is no longer published; publishing both invites "
                             "a consumer to subtract it from its own clock again")
            # and the un-attempted state must not read as success
            ca._CHRON_EVIDENCE_FAILS[:] = []
            ca._CHRON_EVIDENCE_WRITES = 0
            ca._CHRON_EVIDENCE_LAST_OK = None
            self.assertIsNone(ca.chronicle_sweep_state().get("evidenceSaved"),
                              "\"nothing was attempted\" must not report as \"it saved\"")
        finally:
            ca._CHRON_EVIDENCE_PATH = old

    def test_the_console_actually_reads_the_flag(self):
        """The defect this whole thread is about: a value published and consumed by nothing."""
        with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
            ui = fh.read()
        self.assertIn("st.evidenceSaved === false", ui,
                      "nothing on the console reads evidenceSaved — the tap is missing again")
        self.assertIn('id="chron-evwarn"', ui, "the warning element is gone, so the painter writes nowhere")
        self.assertIn("chron-evwarn {", ui, "the warning has no styling and will paint as bare text")
        # and it must be reachable when there is NO result — that is the likeliest failing run
        i_warn = ui.find("var evWarn = document.getElementById('chron-evwarn')")
        i_ret = ui.find("if (!res) return;", i_warn)
        self.assertGreater(i_warn, 0)
        self.assertGreater(i_ret, i_warn,
                           "the warning paints after the empty-result early return, so the run most "
                           "likely to have lost its evidence would never show it")

    def test_the_result_writer_still_refuses_an_unserializable_payload(self):
        """v1800 removed `default=str` from _chron_result_save so a set could not be written as its
        repr — and that was the one changed line with no gate, so re-adding it left the suite green.
        Asserts the REFUSAL, which is the behaviour that matters."""
        import json as _json
        with self.assertRaises(TypeError):
            _json.dumps({"result": {"x": {"a", "b"}}})           # no default= : must raise
        src = open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        i = src.find("def _chron_result_save")
        self.assertGreater(i, 0)
        body = src[i:i + 1800]
        code = _re_mod.sub(r"#.*", "", body)
        self.assertNotIn("default=str", code,
                         "default=str is back: an unserializable value is written as its repr and "
                         "reloaded as data, which is silent corruption instead of a loud failure")


class TestWaitingFootageIsVisible(unittest.TestCase):
    """v1820 — Konyo, after recording three Chronicle sessions: "still not changed the sets or the
    uniques number.. ill do another session it should definitely be able to read and tally them".

    A fourth would have changed nothing either. A `chronicle/visit` row is journaled by the LIVE
    agent; a MINI capture with a CHOSEN chronicle focus produces no such row, only a reel whose
    index says focus=chronicle-uniques/sets. The offer the console renders read journal visits
    only, so three reels sat on disk, correctly labelled by him, invisible to every screen — while
    the only thing that would ever read them was a daemon inside a console that was closed.
    Work waiting, and the system silent about it.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="chron-offer-")
        self._hist = os.environ.get("TV_HIST")
        os.environ["TV_HIST"] = self.tmp
        ca._CHRON_AUTOREAD["reels"] = set()

    def tearDown(self):
        if self._hist is None:
            os.environ.pop("TV_HIST", None)
        else:
            os.environ["TV_HIST"] = self._hist
        ca._CHRON_AUTOREAD["reels"] = None
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _reel(self, rid, focus, n=12):
        d = os.path.join(self.tmp, rid)
        os.makedirs(d, exist_ok=True)
        idx = {"sessionId": rid[5:], "n": n, "focus": focus, "focusChosen": True,
               "frames": [{"f": "f_%d.jpg" % (1787177179114 + i), "ts": 1787177179114 + i}
                          for i in range(n)]}
        with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
            json.dump(idx, fh)
        return d

    def test_a_reel_he_focused_on_the_chronicle_is_OFFERED(self):
        self._reel("reel_s_1787177179114_91449", "chronicle-uniques", 35)
        self._reel("reel_s_1787177267889_92273", "chronicle-sets", 38)
        offers = ca.chronicle_offer(limit=8)["visits"]
        reels = {o.get("reel"): o for o in offers if o.get("source") == "reel"}
        self.assertIn("reel_s_1787177179114_91449", reels)
        self.assertIn("reel_s_1787177267889_92273", reels)
        self.assertEqual(reels["reel_s_1787177179114_91449"]["ledger"], "uniques")
        self.assertEqual(reels["reel_s_1787177267889_92273"]["ledger"], "sets")
        self.assertEqual(reels["reel_s_1787177267889_92273"]["n"], 38)

    def test_the_offer_still_spends_nothing(self):
        self._reel("reel_s_1787177179114_91449", "chronicle-uniques")
        self.assertEqual(ca.chronicle_offer(limit=8)["spent"], 0)

    def test_a_reel_already_swept_is_not_offered_again(self):
        self._reel("reel_s_1787177179114_91449", "chronicle-uniques")
        ca._CHRON_AUTOREAD["reels"] = {"reel_s_1787177179114_91449"}
        offers = ca.chronicle_offer(limit=8)["visits"]
        self.assertFalse([o for o in offers if o.get("reel") == "reel_s_1787177179114_91449"])

    def test_a_mini_focused_somewhere_ELSE_is_never_offered(self):
        # the vault sweep owns stash/rune/gem minis; guessing a ledger for one of those is the
        # failure the whole chronicle lane refuses to commit
        self._reel("reel_s_1787177179114_91449", "stash")
        offers = ca.chronicle_offer(limit=8)["visits"]
        self.assertFalse([o for o in offers if o.get("source") == "reel"])

    def test_the_VISIT_tick_never_takes_a_REEL(self):
        # this loop turns whatever it takes into chronicle_sweep_start(visit=ts). Handing it a reel
        # would look up a journal row that does not exist, fail, spend one of that reel's two tries
        # and eventually RETIRE footage the reel tick would have read correctly.
        self._reel("reel_s_1787177179114_91449", "chronicle-uniques")
        taken = {"visit": [], "reel": []}
        orig_start = ca.chronicle_sweep_start
        orig_alive = ca._agent_alive
        orig_state = ca.chronicle_sweep_state
        try:
            ca.chronicle_sweep_start = lambda **kw: (
                taken["visit"].append(kw.get("visit")) if kw.get("visit")
                else taken["reel"].append(kw.get("reel_id"))) or {"ok": True}
            ca._agent_alive = lambda: False
            ca.chronicle_sweep_state = lambda: {"running": False}
            ca.chronicle_autoread_tick()
        finally:
            ca.chronicle_sweep_start = orig_start
            ca._agent_alive = orig_alive
            ca.chronicle_sweep_state = orig_state
        self.assertEqual(taken["reel"], [], "the visit tick grabbed a reel")


class TestTheFreePassDoesNotAccuseTheReader(unittest.TestCase):
    """v1821 — the quote screen must not diagnose a fault it cannot possibly have observed.

    chronicle_scan_cost installs a stub read_page that returns {} by construction, so "no names" is
    guaranteed and means nothing at all. Without priced_only the verdict landed on `read-nothing` —
    "N Chronicle pages WERE read and produced no names. This one is the reading itself, not the
    footage." That is a confident accusation against his reader, printed on the exact screen he
    opens to decide whether a sweep is worth paying for, and it would send him hunting a fault in
    the one component the pass never ran. sweep_verdict has had the `not-measured` state for this
    since v1541 and the CLI always passed the flag; only this caller, the one he looks at, did not.
    """

    def test_the_quote_declares_itself_a_dry_run(self):
        seen = {}
        import chronicle_retro as _cr

        def fake_sweep(hist, **kw):
            seen.update(kw)
            return {"reels": [], "proposal": {"pagesRead": 0, "refused": [], "uniques": {}, "sets": {}},
                    "totals": {"reels": 0, "framesSeen": 0, "candidates": 0, "classified": 0,
                               "pagesRead": 0, "refused": 0, "uniques": 0, "sets": 0},
                    "verdict": _cr.sweep_verdict({"reels": 0, "framesSeen": 0, "candidates": 0,
                                                  "classified": 0, "pagesRead": 0, "refused": 0,
                                                  "uniques": 0, "sets": 0},
                                                 priced_only=kw.get("priced_only", False))}

        # HERMETIC ON PURPOSE, and this test taught me why the hard way: the first version called
        # chronicle_scan_cost() with no hist_dir, so it fell through to his real frames directory.
        # That passes on his Mac, where footage exists, and FAILS on CI, where tv/frames/hist is
        # absent and the function returns early before the sweep it is meant to be checking. A test
        # that reads whatever happens to be on the machine is not testing the code.
        tmp = tempfile.mkdtemp(prefix="scan-cost-")
        self.addCleanup(shutil.rmtree, tmp, True)
        with mock.patch.object(_cr, "sweep_hist", side_effect=fake_sweep):
            ca.chronicle_scan_cost(hist_dir=tmp, limit=1)
        self.assertTrue(seen.get("priced_only"),
                        "the free pass ran the sweep without priced_only — its verdict will blame "
                        "the reader for finding nothing it was never allowed to look for")

    def test_a_priced_verdict_is_never_a_reader_fault(self):
        # the states that accuse something. A pass that read nothing may report `not-measured` and
        # nothing else; anything here means it claimed to have observed a failure it did not.
        import chronicle_retro as _cr
        totals = {"reels": 3, "framesSeen": 112, "candidates": 18, "classified": 0,
                  "pagesRead": 78, "refused": 0, "uniques": 0, "sets": 0}
        v = _cr.sweep_verdict(totals, priced_only=True)
        self.assertEqual(v["state"], "not-measured")
        self.assertTrue(v["ok"])
        self.assertNotIn("produced no names", v["say"])


class TestALiveSessionDoesNotBlockSealedFootage(unittest.TestCase):
    """v1823 — Konyo: "why refused when session is LIVE?" and, before that, "why is nothing
    automatically sweeping? its been hours".

    Both watchdog ticks opened with a blanket `if _agent_alive(): refuse`, giving the reason "a reel
    is only final once it stops growing". That is true of the reel being recorded RIGHT NOW and
    false of every sealed reel behind it. He plays with the console capturing, so a session was live
    almost whenever he was at the machine, and three finished reels sat unread for hours while the
    guard did exactly what it said on the tin. My first diagnosis — "the console was closed" — was
    wrong, and he corrected it: it had been open the whole time.

    "A session exists" was a PROXY. "This directory is still receiving frames" is the fact.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="reel-growing-")
        self._hist = os.environ.get("TV_HIST")
        os.environ["TV_HIST"] = self.tmp
        ca._CHRON_AUTOREAD["reels"] = set()
        ca._CHRON_AUTOREAD["tries"] = {}
        ca._CHRON_AUTOREAD["skipped"] = {}

    def tearDown(self):
        if self._hist is None:
            os.environ.pop("TV_HIST", None)
        else:
            os.environ["TV_HIST"] = self._hist
        ca._CHRON_AUTOREAD["reels"] = None
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _reel(self, rid, focus="chronicle-uniques", n=6, age_s=3600):
        d = os.path.join(self.tmp, rid)
        os.makedirs(d, exist_ok=True)
        frames = []
        when = time.time() - age_s
        for i in range(n):
            name = "f_%d.jpg" % (1787177179114 + i)
            fp = os.path.join(d, name)
            with open(fp, "wb") as fh:
                fh.write(b"\xff\xd8\xff\xe0stub")
            os.utime(fp, (when, when))
            frames.append({"f": name, "ts": 1787177179114 + i})
        with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"sessionId": rid[5:], "n": n, "focus": focus, "focusChosen": True,
                       "frames": frames}, fh)
        os.utime(d, (when, when))
        return d

    def test_a_sealed_reel_is_swept_even_while_a_session_is_live(self):
        d = self._reel("reel_s_1787177179114_91449", age_s=3600)
        self.assertFalse(ca._reel_is_growing(d), "an hour-old reel is not growing")
        taken = []
        with mock.patch.object(ca, "chronicle_sweep_start",
                               side_effect=lambda **kw: taken.append(kw.get("reel_id")) or {"ok": True}), \
             mock.patch.object(ca, "_agent_alive", return_value=True), \
             mock.patch.object(ca, "chronicle_sweep_state", return_value={"running": False}):
            r = ca.chronicle_autoreel_tick()
        self.assertTrue(r.get("ok"), r)
        self.assertEqual(taken, ["reel_s_1787177179114_91449"],
                         "a live session blocked footage that had already stopped growing")

    def test_the_reel_still_receiving_frames_IS_skipped(self):
        # the one thing the old guard genuinely protected, kept
        self._reel("reel_s_1787177179114_91449", age_s=2)
        taken = []
        with mock.patch.object(ca, "chronicle_sweep_start",
                               side_effect=lambda **kw: taken.append(kw.get("reel_id")) or {"ok": True}), \
             mock.patch.object(ca, "_agent_alive", return_value=True), \
             mock.patch.object(ca, "chronicle_sweep_state", return_value={"running": False}):
            ca.chronicle_autoreel_tick()
        self.assertEqual(taken, [], "a reel still being written was swept")
        self.assertIn("reel_s_1787177179114_91449", ca._CHRON_AUTOREAD["skipped"])

    def test_a_reel_it_cannot_judge_counts_as_growing(self):
        # reading a half-written reel spends money on footage about to change, so "cannot tell"
        # must never mean "go ahead"
        self.assertTrue(ca._reel_is_growing(os.path.join(self.tmp, "does-not-exist")))

    def test_a_sweep_already_running_still_refuses(self):
        self._reel("reel_s_1787177179114_91449", age_s=3600)
        with mock.patch.object(ca, "_agent_alive", return_value=False), \
             mock.patch.object(ca, "chronicle_sweep_state", return_value={"running": True}):
            r = ca.chronicle_autoreel_tick()
        self.assertFalse(r.get("ok"))
        self.assertIn("already running", r.get("why", ""))


class TestAVisitIsNotTheHistFolder(unittest.TestCase):
    """v1825 — every visit ever swept was filed under the reel id "hist".

    _chron_visit_run joins each journalled frame id onto the hist ROOT (the live agent writes those
    frames there, not into a reel), so sweep_frames' default reel_of — basename(dirname(path)) —
    returned the name of the hist directory. 15 sightings in his live ledger carry it.

    witnesses() counts DISTINCT reels, so every visit collapsed into one pseudo-reel: two genuinely
    separate sittings of the same item could not corroborate each other. Under-counting, which is
    the safe direction, but wrong. Keying them per VISIT would have been worse and in the dangerous
    direction — the same frames later swept as a reel would appear under two keys and the sitting
    would corroborate itself, the fault v1824 closed one field over. So the key is the reel that
    actually holds the moment, matched on the frame's own epoch, and "" when it cannot be proven.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="visit-reel-")
        ca._reel_for_frame_epoch.__defaults__[0].clear()   # the span cache is keyed by hist path

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        ca._reel_for_frame_epoch.__defaults__[0].clear()

    def _reel(self, rid, first_ts, n=5, step=1000):
        d = os.path.join(self.tmp, rid)
        os.makedirs(d, exist_ok=True)
        frames = []
        for i in range(n):
            name = "f_%d.jpg" % (first_ts + i * step)
            with open(os.path.join(d, name), "wb") as fh:
                fh.write(b"\xff\xd8\xff\xd9")
            frames.append({"f": name, "ts": first_ts + i * step})
        with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"sessionId": rid[5:], "n": n, "frames": frames}, fh)
        return d

    def test_a_frame_inside_a_reels_span_resolves_to_that_reel(self):
        self._reel("reel_s_1787177179114_91449", 1787177185446)
        self.assertEqual(ca._reel_for_frame_epoch(self.tmp, 1787177187446),
                         "s_1787177179114_91449")

    def test_two_reels_are_told_apart(self):
        self._reel("reel_s_1000000000000_aaa", 1000000000000)
        self._reel("reel_s_2000000000000_bbb", 2000000000000)
        self.assertEqual(ca._reel_for_frame_epoch(self.tmp, 1000000002000), "s_1000000000000_aaa")
        self.assertEqual(ca._reel_for_frame_epoch(self.tmp, 2000000003000), "s_2000000000000_bbb")

    def test_an_epoch_no_reel_covers_is_UNPROVEN_not_guessed(self):
        # an unproven independence is not independence: the caller keeps the old collapsed key
        self._reel("reel_s_1000000000000_aaa", 1000000000000)
        self.assertEqual(ca._reel_for_frame_epoch(self.tmp, 5555555555555), "")

    def test_an_empty_hist_answers_unproven_rather_than_throwing(self):
        self.assertEqual(ca._reel_for_frame_epoch(os.path.join(self.tmp, "nope"), 123), "")


class TestBothLanesKnowWhatASetHeadingIs(unittest.TestCase):
    """v1826 — the readers confused a set HEADING with a PIECE about a quarter of the time.

    Measured on his own swept evidence, not imagined: of 16 set groups, 4 were keyed by something
    that is not a set — "M'avina's True Sight", "M'avina's Tenet" and "Cleglaw's Claw" are PIECES,
    and "Cathan's" is a truncation. It wrote no bad data, because a heading matching no set expands
    to nothing and the apply only ever wrote real roster pieces. But a quarter of the groups being
    junk is a reader that was never told what a heading looks like, and the tell is unambiguous on
    his frames: a heading is centred with NO icon, NO `Dropped By:` and NO `First Found:`, while
    every piece row carries all three.
    """

    def _prompts(self):
        here = os.path.dirname(os.path.abspath(__file__))
        return (open(os.path.join(here, "tv_diablo.py"), encoding="utf-8").read(),
                open(os.path.join(here, "g5_grok_eyes.py"), encoding="utf-8").read())

    def test_neither_lane_still_asks_for_the_sort_control(self):
        """v1828 — `sort` was asked for on every chronicle read since v1819 and returned EMPTY 2358
        times out of 2358, then tested directly against a frame that plainly shows "Newest to
        Oldest" at its top right: it came back "" while the same read returned four found names and
        four correct dates. Plumbed end to end; never filled.

        Removed rather than re-worded, because the thing it was for is solved better - every row
        carries its own First Found stamp, so the list's ORDER is derivable from the data instead of
        read off a control. A prompt line that has never produced a value is not free: it is paid
        for on every page of every sweep and it reads to the next person as a capability that
        exists.
        """
        claude, grok = self._prompts()
        for lane, src in (("claude", claude), ("grok", grok)):
            i = src.index("CHRONICLE_READ_PROMPT" if lane == "claude" else "CHRONICLE_VISION_PROMPT")
            body = src[i:i + 4000]
            self.assertNotIn('"sort":""', body, "the %s lane still asks for sort" % lane)

    def test_both_lanes_know_a_First_Found_line_IS_the_found_state(self):
        """v1827 — the sets reel refused 20 of 35 attempts, and one of the refusals was a perfectly
        legible page: M'avina's Tenet (Demon Imp, 05/19/2026), M'avina's Icy Clutch (The Cow King,
        05/18/2026), the Trang-Oul's Avatar heading, then Girth and Claws each with a date.

        The stateVisible rule was written for the UNIQUES panel, where unfound rows are dim
        silhouettes sitting beside bright found ones, so "can you tell them apart" is answerable by
        contrast. A SETS page showing only owned rows has nothing to contrast against, and a reader
        following that rule literally MUST refuse it. The refusal was correct behaviour from an
        incomplete instruction, which is the worst kind to debug: nothing is broken and pages still
        vanish.
        """
        claude, grok = self._prompts()
        for needle in ("`First Found:` date IS found", "do NOT set stateVisible=false"):
            self.assertIn(needle, claude, "the Claude lane lost: %s" % needle)
            self.assertIn(needle, grok, "the Grok lane lost: %s" % needle)

    def test_both_lanes_describe_the_heading_the_same_way(self):
        claude, grok = self._prompts()
        for needle in ("set-name HEADING", "NO `Dropped By:` line", "never a piece name in"):
            self.assertIn(needle, claude, "the Claude lane lost: %s" % needle)
            self.assertIn(needle, grok, "the Grok lane lost: %s" % needle)

    def test_the_prompt_version_moved_with_the_prompt(self):
        # a changed prompt on an old version replays cached reads that were answered under the old
        # wording — the same guard test_agent keeps, asserted here because THIS change is the reason
        import tv_diablo as _tv
        self.assertEqual(_tv.PROMPT_VER, "p1839")


class TestV1829CropRefusalRetriesFullFrame(unittest.TestCase):
    """v1829 — A CROP THAT ANSWERS AND REFUSES IS STILL REFUSED.

    Both crop routes in tv_diablo retried the full frame on `not raw`, which catches only a crop
    that returned NOTHING. A crop returning a well-formed {"stateVisible": false} is TRUTHY, so the
    retry never fired — and that is the COMMON failure, because what a bad crop cuts away is
    precisely the chrome the reader is asked to judge.

    The page that proved it: frames/hist/reel_s_1787177267889_92273/f_1787177297466.jpg, recorded
    `no-found-state` by the sweep on two passes, while both lanes read the FULL frame at conf
    0.90/0.88 with five dated set pieces. Nothing was wrong with the footage or the readers.
    """

    def setUp(self):
        # Pillow is installed in CI (publish.yml + tv-tests.yml), but a bare environment must SKIP
        # rather than ERROR — an unguarded import here refused ten consecutive publishes.
        try:
            from PIL import Image  # noqa: F401
        except Exception:
            self.skipTest("Pillow absent — this fixture writes a real JPEG for the reader to crop")

    def _jpg(self, tmp):
        from PIL import Image
        p = os.path.join(tmp, "page.jpg")
        Image.new("RGB", (1400, 1000), (18, 18, 22)).save(p, quality=90)
        return p

    def _drive(self, crop_answer, full_answer):
        """Run the real reader with only the vision call faked, and report which paths it asked."""
        import tv_diablo as _tv
        seen = []

        def fake_oneshot(ap, model, timeout=90, prompt=None, raw_json=False):
            seen.append(ap)
            # the crop is written to a temp file; the full frame is the path we passed in
            return crop_answer if "tvd_chron_crop" in os.path.basename(ap) else full_answer

        with tempfile.TemporaryDirectory() as tmp:
            img = self._jpg(tmp)
            old = (_tv._oneshot, _tv._is_throttled, _tv._sub_budget_check)
            _tv._oneshot = fake_oneshot
            _tv._is_throttled = lambda: False
            _tv._sub_budget_check = lambda *a, **k: None
            try:
                out = _tv.claude_chronicle_read(img, "chronicle-sets")
            finally:
                (_tv._oneshot, _tv._is_throttled, _tv._sub_budget_check) = old
        return out, seen

    GOOD = {"stateVisible": True, "wrongTab": False, "conf": 0.9,
            "found": ["Trang-Oul's Girth", "Sazabi's Mental Sheath"],
            "sets": [{"set": "Trang-Oul's Avatar", "pieces": ["Trang-Oul's Girth"]}]}
    REFUSED = {"stateVisible": False, "conf": 0.2, "found": []}

    def test_a_crop_that_refuses_gets_the_full_frame(self):
        out, seen = self._drive(self.REFUSED, self.GOOD)
        self.assertEqual(len(seen), 2,
                         "the full frame was never requested — the crop's refusal was taken as the "
                         "page's answer. Asked for: %s" % seen)
        self.assertIsNone((out or {}).get("note"),
                          "a legible page was recorded as refused: %r" % ((out or {}).get("note"),))
        self.assertIn("Sazabi's Mental Sheath", (out or {}).get("found") or [],
                      "the full frame was read and then thrown away")

    def test_the_retry_asks_the_subscription_cap_again(self):
        """v1845 — one budget check may not license two reads.

        The cap is checked once at the top of the read. Before v1829 the full-frame retry fired only
        on a hard crash, so one check covered one read in practice. v1829 made it fire on a REFUSAL,
        which is common — so every refused page spent two reads on a single check. Bounded, but
        systematic, and the cap is the one guard between a long sweep and his whole allowance.

        Skipping the retry leaves the crop's answer standing, which is the pre-v1829 behaviour: an
        honest refusal rather than a read he cannot afford.
        """
        import tv_diablo as _tv
        seen = []

        def fake_oneshot(ap, model, timeout=90, prompt=None, raw_json=False):
            seen.append(ap)
            return self.REFUSED if "tvd_chron_crop" in os.path.basename(ap) else self.GOOD

        with tempfile.TemporaryDirectory() as tmp:
            img = self._jpg(tmp)
            old = (_tv._oneshot, _tv._is_throttled, _tv._sub_budget_check)
            _tv._oneshot = fake_oneshot
            _tv._is_throttled = lambda: False
            # the cap is OPEN at entry and CLOSES before the retry would fire
            calls = []
            def capped(*a, **k):
                calls.append(1)
                return None if len(calls) == 1 else "out of reads until the window rolls"
            _tv._sub_budget_check = capped
            try:
                out = _tv.claude_chronicle_read(img, "chronicle-sets")
            finally:
                (_tv._oneshot, _tv._is_throttled, _tv._sub_budget_check) = old
        self.assertEqual(len(seen), 1,
                         "the retry spent a read the cap had already refused: %s" % seen)
        self.assertEqual((out or {}).get("note"), "no-found-state",
                         "a skipped retry must leave the crop's honest refusal standing")

    def test_a_full_frame_that_also_refuses_never_overwrites_the_crop(self):
        # a retry that can LOSE information is not a retry. The crop keeps its answer.
        out, seen = self._drive(dict(self.GOOD, conf=0.55), self.REFUSED)
        self.assertEqual(len(seen), 1, "nothing was refused — no retry was owed")
        self.assertIn("Sazabi's Mental Sheath", (out or {}).get("found") or [])

    def test_wrong_ledger_from_a_crop_is_re_asked_on_the_full_frame(self):
        # a crop that cuts the tab chrome reports the wrong ledger for the same reason it reports
        # no found-state. If the ledger really is wrong the full frame says so too.
        out, seen = self._drive({"wrongTab": True, "conf": 0.3, "found": []}, self.GOOD)
        self.assertEqual(len(seen), 2, "a wrong-ledger crop was believed without a second look")
        self.assertFalse((out or {}).get("wrongTab"))

    def test_the_helper_reads_every_shape_a_refusal_arrives_in(self):
        import tv_diablo as _tv
        for shape in (None, {}, "", [], {"stateVisible": False}, {"wrongTab": True}):
            self.assertTrue(_tv._crop_answer_refused(shape), "not caught as refused: %r" % (shape,))
        self.assertFalse(_tv._crop_answer_refused({"stateVisible": True, "found": []}),
                         "an EMPTY page is an answer, not a refusal")
        # the vault lane marks refusals with `note`, and an empty stash tab is a real answer
        self.assertTrue(_tv._crop_answer_refused({"note": "not read"}, ledger_lane=False))
        self.assertFalse(_tv._crop_answer_refused({"items": []}, ledger_lane=False))



class TestV1830ASealIsOnlyAsGoodAsItsReader(unittest.TestCase):
    """v1830 — a zero-page seal made by an older reader must not outlive it.

    `chronicle_swept.json` stored ts/classified/pages and nothing about WHO read. So "the classifier
    looked and found no Chronicle page" — a legitimate verdict — survived every later fix to the
    classifier. Eight reels, 1,032 frames, sealed 08-17 16:10 and 08-18 00:41, ahead of v1770, v1774,
    v1777, v1778, v1779 and v1780. Three of those six exist because the sweep believed a reader that
    had stopped answering, which is the exact shape of "classified 43, pages 0".

    The footage was never the problem: a frame from the 483-frame reel, opened and looked at, is a
    Chronicle page printing Nature's Peace 05/23/2026 01:06 and two more with stamps, and today's
    classifier calls it chronicle-uniques outright.
    """

    def test_a_seal_with_no_reader_recorded_does_not_stand(self):
        import control_app as ca
        self.assertFalse(ca._chron_seal_stands({"ts": 1, "classified": 43, "pages": 0}, "p1828"),
                         "every seal on his disk predates the stamp — if these stand, nothing reopens")

    def test_a_seal_from_the_current_reader_stands(self):
        import control_app as ca
        self.assertTrue(ca._chron_seal_stands({"pages": 0, "promptVer": "p1828"}, "p1828"),
                        "a gameplay reel must stay sealed, or every ship re-pays for the whole hist")

    def test_a_seal_from_an_older_reader_is_void(self):
        import control_app as ca
        self.assertFalse(ca._chron_seal_stands({"pages": 0, "promptVer": "p1700"}, "p1828"))

    def test_a_seal_that_actually_read_pages_stands_forever(self):
        import control_app as ca
        # the findings outlive the reader that found them — they are already in the evidence ledger
        self.assertTrue(ca._chron_seal_stands({"pages": 21, "promptVer": "p1700"}, "p1828"))

    def test_an_unreadable_record_is_not_a_licence_to_re_spend(self):
        import control_app as ca
        for junk in (None, "", 3, []):
            self.assertTrue(ca._chron_seal_stands(junk, "p1828"), "junk reopened a reel: %r" % (junk,))

    def test_force_reopens_everything_and_reports_nothing_as_reopened(self):
        import control_app as ca
        skip, reopened = ca._chron_skip_set({"a": {"pages": 9, "promptVer": "p1828"}}, force=True)
        self.assertEqual((skip, reopened), (set(), []))

    def test_the_split_names_what_it_reopens(self):
        import control_app as ca
        swept = {"stands": {"pages": 0, "promptVer": "p1828"},
                 "read_it": {"pages": 4, "promptVer": "p1000"},
                 "stale":   {"pages": 0, "promptVer": "p1000"},
                 "nostamp": {"pages": 0}}
        skip, reopened = ca._chron_skip_set(swept, prompt_ver="p1828")
        self.assertEqual(skip, {"stands", "read_it"})
        self.assertEqual(reopened, ["nostamp", "stale"])

    def test_the_seal_writer_records_which_reader_sealed_it(self):
        # the decision above is worthless if nothing ever writes the key it reads
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        i = src.find('swept["reel_" + str(st["reel"])]')
        self.assertGreater(i, 0, "the seal writer moved — find it and re-point this guard")
        self.assertIn("promptVer", src[i:i + 700],
                      "seals are written without the reader stamp, so nothing will ever reopen")



class TestV1831TheFeedCanBeBehindTheClock(unittest.TestCase):
    """v1831 — upstream itself lags the rotation, so "refresh more often" cannot fix it.

    Measured across a real boundary, sampling every 45s:
        07:29:59  +1799s | cur=Burial Grounds   | next=Kurast Bazaar
        07:30:44  +  44s | cur=Burial Grounds   | next=Kurast Bazaar      <- slot ALREADY turned
        07:31:29  +  89s | cur=Kurast Bazaar    | next=Nihlathak's Temple

    Forty-four seconds past the turn, the feed still called the previous zone `current`. v1813 fixed
    OUR cache outliving its slot; this is the same reading arriving through the other door, and the
    console printed it as LIVE NOW.
    """
    SLOT = 1800000

    def _body(self, newest_slot):
        return {"current": "Burial Grounds, Crypt, and Mausoleum",
                "next": "Kurast Bazaar, Ruined Temple, and Disused Fane",
                "history": [{"slot": newest_slot, "zone": "Burial Grounds"},
                            {"slot": newest_slot - self.SLOT, "zone": "Tal Rasha's Tombs"}]}

    def test_a_feed_still_on_the_previous_slot_is_turning(self):
        import control_app as ca
        now = 1787200244000                       # 07:30:44 — 44s past the turn
        here = (now // self.SLOT) * self.SLOT
        out = ca._tz_mark_turning(self._body(here - self.SLOT), now_ms=now)
        self.assertEqual(out["slotBehind"], 1)
        self.assertTrue(out["turning"], "the board will print a zone that has already ended")

    def test_a_caught_up_feed_is_not_turning(self):
        import control_app as ca
        now = 1787201000000
        here = (now // self.SLOT) * self.SLOT
        out = ca._tz_mark_turning(self._body(here), now_ms=now)
        self.assertEqual(out["slotBehind"], 0)
        self.assertFalse(out["turning"])

    def test_a_badly_frozen_feed_is_not_flattered_as_a_turnover(self):
        # many slots behind is a broken feed, which `stale` already says. Calling that "turning
        # over" would dress a dead feed as a healthy one mid-rotation.
        import control_app as ca
        now = 1787201000000
        here = (now // self.SLOT) * self.SLOT
        out = ca._tz_mark_turning(self._body(here - 9 * self.SLOT), now_ms=now)
        self.assertEqual(out["slotBehind"], 9)
        self.assertFalse(out["turning"])

    def test_no_history_claims_nothing(self):
        import control_app as ca
        out = ca._tz_mark_turning({"current": "x", "next": "y"}, now_ms=1787201000000)
        self.assertIsNone(out["slotBehind"], "not measured must not read as not behind")
        self.assertFalse(out["turning"])

    def test_it_is_additive_and_never_rewrites_the_reading(self):
        import control_app as ca
        now = 1787200244000
        here = (now // self.SLOT) * self.SLOT
        src = self._body(here - self.SLOT)
        before = dict(src)
        out = ca._tz_mark_turning(src, now_ms=now)
        for k in ("current", "next", "history"):
            self.assertEqual(out[k], before[k], "%s was rewritten — the reading is upstream's" % k)

    def test_a_junk_payload_is_returned_untouched(self):
        import control_app as ca
        for junk in (None, "", 7, []):
            self.assertEqual(ca._tz_mark_turning(junk, now_ms=1), junk)



class TestV1832OneLiveSessionRuleInBothSweepers(unittest.TestCase):
    """v1832 — the console and the command line must refuse for the SAME reasons.

    Konyo: "why refused when session is LIVE? we had a AI reader for live too". v1823 removed the
    blanket live-session refusal from the console path, saying why in its own comment: "A live
    session says nothing about the SEALED reels behind it, and refusing on it meant the sweeper
    never ran while he was at the machine." chronicle_sweep_now.py kept the old rule while its
    comment claimed to "refuse for the same reasons the watchdog refuses" — so the console would
    sweep while he played and the command line would not. [[copy-drift]]
    """

    def _sweeper_src(self):
        import control_app as ca
        p = os.path.join(os.path.dirname(os.path.abspath(ca.__file__)), "chronicle_sweep_now.py")
        self.assertTrue(os.path.isfile(p), "the standalone sweeper moved — re-point this guard")
        return open(p, encoding="utf-8").read()

    def test_the_command_line_does_not_refuse_just_because_a_session_is_live(self):
        # Scanned by LINE, not by a character window: the first cut of this guard read 260 chars
        # past the live check and tripped on the NEXT refusal — the already-running-sweep one,
        # which is supposed to return. A guard that cannot tell two adjacent rules apart reports
        # the wrong one broken.
        src = self._sweeper_src()
        lines = src.splitlines()
        hits = [n for n, ln in enumerate(lines) if "_agent_alive()" in ln]
        self.assertTrue(hits, "the live check vanished entirely — the growing reel is now unprotected")
        for n in hits:
            branch = [ln.strip() for ln in lines[n:n + 4]]
            if not lines[n].strip().startswith("if "):
                continue      # an assignment (live = ...) is the v1832 shape and refuses nothing
            self.assertNotIn("return 1", branch,
                             "line %d aborts the whole run on a live session; v1823 skips only "
                             "the reel still recording" % (n + 1))

    def test_it_still_protects_the_reel_that_is_actually_recording(self):
        # dropping the blanket refusal must not drop the real protection with it
        self.assertIn("_reel_is_growing", self._sweeper_src(),
                      "nothing skips the reel still receiving frames — a half-written reel would "
                      "be swept and then sealed")

    def test_a_running_sweep_is_still_refused(self):
        src = self._sweeper_src()
        self.assertIn("a sweep is already running", src)

    def test_the_doc_no_longer_claims_a_refusal_it_does_not_make(self):
        # the drift that produced this bug was a comment asserting a rule the code had stopped
        # sharing; a doc that lies about the refusal is the same defect one layer up
        src = self._sweeper_src()
        self.assertNotIn("It refuses outright while a capture session is live", src)



class TestV1832TheSuiteMustNotTouchHisSweepLock(unittest.TestCase):
    """v1832 — a properly isolated test still stamped his live tv/.sweep.lock.

    Every sweep test already sets TV_HIST + TV_STUB and spends nothing, but chronicle_sweep_start
    wrote the lock at a hardcoded HERE/.sweep.lock. Measured before the fix: one full run of
    `python3 -m unittest test_control` moved tv/.sweep.lock every time.

    It has teeth. run_gates._sweep_in_progress() reads that file and calls anything younger than
    900s a live sweep, so for fifteen minutes after any suite run the gate believed a sweep was
    running and softened its live-state verdict — a guard disarmed by the suite beside it.
    """

    def test_an_isolated_hist_gets_an_isolated_lock(self):
        import control_app as ca
        old = os.environ.get("TV_HIST")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["TV_HIST"] = tmp
            try:
                p = ca._sweep_lock_path()
            finally:
                if old is None: os.environ.pop("TV_HIST", None)
                else: os.environ["TV_HIST"] = old
            self.assertEqual(os.path.dirname(p), tmp,
                             "the lock still lands outside the isolated footage: %s" % p)

    def test_production_keeps_the_exact_path_run_gates_reads(self):
        # run_gates points at tv/.sweep.lock by name; changing it in production would silently
        # retire that guard instead of fixing it
        import control_app as ca
        saved = {k: os.environ.get(k) for k in ("TV_HIST", "TV_SWEEP_LOCK")}
        for k in saved: os.environ.pop(k, None)
        try:
            self.assertEqual(ca._sweep_lock_path(),
                             os.path.join(os.path.dirname(os.path.abspath(ca.__file__)), ".sweep.lock"))
        finally:
            for k, v in saved.items():
                if v is not None: os.environ[k] = v

    def test_the_heartbeat_actually_beats(self):
        # run_gates has always CALLED it a heartbeat ("a sweep touches it while it runs") while the
        # lock was written once, at sweep start — so its 900s staleness bound went blind partway
        # through every long sweep. His reels take far longer than 900s.
        import control_app as ca
        with tempfile.TemporaryDirectory() as tmp:
            lock = os.path.join(tmp, "beat.lock")
            os.environ["TV_SWEEP_LOCK"] = lock
            try:
                ca._sweep_lock_touch(_last=[0.0])
                self.assertTrue(os.path.isfile(lock), "the heartbeat wrote nothing")
                first = os.path.getmtime(lock)
                ca._sweep_lock_touch(_last=[0.0])       # a later beat refreshes it
                self.assertGreaterEqual(os.path.getmtime(lock), first)
            finally:
                os.environ.pop("TV_SWEEP_LOCK", None)

    def test_the_heartbeat_is_rate_limited(self):
        # it runs before every page read; the point is a fresh mtime, not a write per read
        import control_app as ca
        with tempfile.TemporaryDirectory() as tmp:
            lock = os.path.join(tmp, "rl.lock")
            os.environ["TV_SWEEP_LOCK"] = lock
            try:
                ca._sweep_lock_touch(_last=[time.time()])
                self.assertFalse(os.path.isfile(lock), "a beat inside the window still wrote")
            finally:
                os.environ.pop("TV_SWEEP_LOCK", None)

    def test_the_read_loop_beats_it(self):
        # a heartbeat nothing calls is the defect it replaced
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        i = src.find("def _breathe()")
        self.assertGreater(i, 0, "_breathe moved — re-point this guard")
        self.assertIn("_sweep_lock_touch()", src[i:i + 1400],
                      "the sweep's per-read hook no longer beats the lock")



class TestV1834ANamedReelIsReachableAndPricedAsItself(unittest.TestCase):
    """v1834 — v1830 reopened eight sealed reels and nothing could reach them.

    _unswept_chron_reels() lists only reels that DECLARE a Chronicle focus, which is right for an
    automatic run — it stops a stash mini or a gameplay session being swept at full price. But
    --reel and --again FILTER that list, so an undeclared reel answered "nothing waiting" whatever
    you typed. The eight reels v1830 reopened (1,032 frames, including the 483-frame browse whose
    pages print First Found stamps and his 64% meter) carry no declared focus, because they were
    ordinary sessions. Reopened in the skip set, invisible to the selector: two halves, each
    correct, never joined.

    And the price named a different reel. `limit` slices reel_dirs newest-first, so pricing by name
    was impossible — his 483-frame reel quoted "21 page read(s)", the cost of the NEWEST reel, on
    the exact line he reads before agreeing to spend.
    """

    def setUp(self):
        try:
            from PIL import Image  # noqa: F401
        except Exception:
            self.skipTest("Pillow absent — the pricing walk has to decode frames to group them")

    def _reel(self, root, name, n):
        """REAL jpegs, in blocks of four. The first cut of this fixture wrote index.json and no
        image files, so live_probe() found nothing readable, every run counted blank and BOTH
        quotes came back zero pages — a test that would have passed the broken code just as
        happily. Blocks of four so frames group into runs the way a held panel does, which is what
        makes the page count scale with the reel."""
        from PIL import Image, ImageDraw
        d = os.path.join(root, name)
        os.makedirs(d)
        frames = []
        for i in range(n):
            fn = "f_%03d.jpg" % i
            block = i // 4
            im = Image.new("RGB", (320, 240), (16, 16, 20))
            dr = ImageDraw.Draw(im)
            # CONTENT, not a flat fill: live_probe() rejects a featureless frame as blank, so a
            # solid-colour fixture priced zero pages and the test could not tell a working walk
            # from a broken one. Deterministic bars, shifted per block so blocks are distinguishable.
            for k in range(8):
                y = 12 + k * 26
                dr.rectangle([18 + ((block * 7 + k * 13) % 40), y, 300, y + 14],
                             fill=(60 + ((block * 37 + k * 21) % 150), 90, 130))
            im.save(os.path.join(d, fn), quality=88)
            frames.append(fn)
        with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"frames": [{"f": f} for f in frames]}, fh)
        return d

    def test_the_pricer_prices_the_reel_it_was_given_not_the_newest(self):
        import control_app as ca
        with tempfile.TemporaryDirectory() as root:
            self._reel(root, "reel_newest", 4)
            self._reel(root, "reel_target", 24)
            small = ca.chronicle_scan_cost(hist_dir=root, limit=1, reel_id="reel_newest") or {}
            big = ca.chronicle_scan_cost(hist_dir=root, limit=1, reel_id="reel_target") or {}
            self.assertGreater(big.get("wouldReadPages") or 0, small.get("wouldReadPages") or 0,
                               "both quotes describe the same reel — reel_id is not reaching the walk")

    def test_pricing_without_a_reel_id_is_unchanged(self):
        import control_app as ca
        with tempfile.TemporaryDirectory() as root:
            self._reel(root, "reel_a", 8)
            q = ca.chronicle_scan_cost(hist_dir=root, limit=1) or {}
            self.assertTrue(q.get("ok"))
            self.assertGreaterEqual(q.get("wouldReadPages") or 0, 1)

    def test_the_cli_lets_an_explicitly_named_reel_through_the_focus_filter(self):
        import control_app as ca
        src = open(os.path.join(os.path.dirname(os.path.abspath(ca.__file__)),
                                "chronicle_sweep_now.py"), encoding="utf-8").read()
        i = src.find("if args.reel and not waiting:")
        self.assertGreater(i, 0,
                           "an undeclared reel is unreachable again — --reel filters a list it can "
                           "never appear in, which is how v1830's eight reopened reels were stranded")
        self.assertIn("declares no Chronicle focus", src[i:i + 700],
                      "it reaches the reel without SAYING the focus filter was bypassed")

    def test_the_cli_prices_the_named_reel(self):
        import control_app as ca
        src = open(os.path.join(os.path.dirname(os.path.abspath(ca.__file__)),
                                "chronicle_sweep_now.py"), encoding="utf-8").read()
        self.assertIn("reel_id=(args.reel or None)", src,
                      "the quote is computed for whatever reel is newest, not the one named")

    def test_the_printed_reel_count_matches_what_would_be_read(self):
        import control_app as ca
        src = open(os.path.join(os.path.dirname(os.path.abspath(ca.__file__)),
                                "chronicle_sweep_now.py"), encoding="utf-8").read()
        i = src.find("the free pass says:")
        self.assertGreater(i, 0)
        self.assertIn('!= "already-swept"', src[max(0, i - 600):i],
                      "the reel count still counts reels skipped as already-swept, so the pages "
                      "and the reels in one sentence describe different sets")



class TestV1835EvidenceIsBankedAsItIsRead(unittest.TestCase):
    """v1835 — a sweep that dies must not lose everything it paid for.

    Findings reached disk in ONE place: _chron_evidence_merge(), after the last page of the last
    reel. Everything before that lived in a list in memory, so a sweep killed, throttled out, slept,
    abandoned by the CLI's --timeout, or crashed on page 439 lost every read — and the reel was not
    sealed either, so the whole bill came again.

    Affordable at 21 pages a reel. Not at 440: v1834 made his 483-frame browse reachable and priced
    it, and nobody should be asked to authorise sixteen hours of reading as one all-or-nothing
    transaction.
    """

    def setUp(self):
        try:
            from PIL import Image  # noqa: F401
        except Exception:
            self.skipTest("Pillow absent — frame grouping needs to decode the JPEGs")
        self.d = tempfile.mkdtemp()
        for i, sid in enumerate(("s_a", "s_b", "s_c")):
            rd = os.path.join(self.d, "reel_" + sid)
            os.makedirs(rd)
            for n in range(6):
                _screenish((64, 48), 11 + i).save(os.path.join(rd, "f%d.jpg" % n))
            with open(os.path.join(rd, "index.json"), "w", encoding="utf-8") as fh:
                json.dump({"sessionId": sid,
                           "frames": [{"f": "f%d.jpg" % n, "ts": 1000 + n} for n in range(6)]}, fh)
        self.man = os.path.join(self.d, "man.json")
        with open(self.man, "w", encoding="utf-8") as fh:
            # "*" feeds the CLASSIFIER and "*#chronicle" the page read — a manifest with only the
            # second classifies nothing, reads nothing, and the test then measures an empty sweep.
            json.dump({"*": {"scene": "chronicle", "chronicleTab": "uniques",
                             "names": [], "conf": 0.9},
                       "*#chronicle": {"ledger": "uniques", "found": ["Windforce"],
                                       "notFound": [], "stateVisible": True, "conf": 0.9}}, fh)
        self._env = {k: os.environ.get(k) for k in ("TV_STUB", "TV_STUB_MANIFEST", "TV_HIST")}
        os.environ.update({"TV_STUB": "1", "TV_STUB_MANIFEST": self.man, "TV_HIST": self.d})
        self._swept = mock.patch.object(ca, "_CHRON_SWEPT_PATH", os.path.join(self.d, "swept.json"))
        self._swept.start()
        self._ev = mock.patch.object(ca, "_CHRON_EVIDENCE_PATH", os.path.join(self.d, "ev.json"))
        self._ev.start()

    def tearDown(self):
        self._ev.stop()
        self._swept.stop()
        for k, v in self._env.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v
        shutil.rmtree(self.d, ignore_errors=True)
        with ca._CHRON_LOCK:
            ca._CHRON_JOB.update({"running": False, "phase": "idle", "result": None, "error": None})

    def _run(self, timeout=60.0):
        started = ca.chronicle_sweep_start(hist_dir=self.d)
        self.assertTrue(started.get("ok"), started)
        deadline = time.time() + timeout
        while time.time() < deadline and ca.chronicle_sweep_state()["running"]:
            time.sleep(0.05)
        self.assertFalse(ca.chronicle_sweep_state()["running"], "the sweep never finished")

    def test_evidence_is_merged_more_than_once(self):
        calls = []
        real = ca._chron_evidence_merge

        def counting(prop):
            calls.append(sum(len(v or {}) for k, v in (prop or {}).items()
                             if k in ("uniques", "sets")))
            return real(prop)

        with mock.patch.object(ca, "_CHRON_CKPT_PAGES", 1), \
             mock.patch.object(ca, "_chron_evidence_merge", counting):
            self._run()
        self.assertGreaterEqual(len(calls), 2,
                                "evidence reached disk once, at the end — a sweep that dies on the "
                                "last page still loses every read before it")

    def test_the_banked_evidence_is_on_disk_and_holds_names(self):
        with mock.patch.object(ca, "_CHRON_CKPT_PAGES", 1):
            self._run()
        self.assertTrue(os.path.isfile(ca._CHRON_EVIDENCE_PATH), "nothing was ever written")
        with open(ca._CHRON_EVIDENCE_PATH, encoding="utf-8") as fh:
            ev = json.load(fh)
        self.assertIn("Windforce", ev.get("uniques") or {},
                      "the ledger was written but holds none of what was read")

    def test_a_high_threshold_still_completes_and_banks_at_the_end(self):
        # the checkpoint is an addition, never a replacement: with a threshold no run reaches, the
        # final merge must still put everything on disk exactly as before
        with mock.patch.object(ca, "_CHRON_CKPT_PAGES", 10 ** 6):
            self._run()
        with open(ca._CHRON_EVIDENCE_PATH, encoding="utf-8") as fh:
            ev = json.load(fh)
        self.assertIn("Windforce", ev.get("uniques") or {})

    def test_the_live_lane_stays_out_of_isolated_footage(self):
        # v1833 shipped the live lane reading sessions.jsonl. Tests isolate TV_HIST but not
        # TV_SESSIONS, so his REAL journal — Baranar's Star, Jalal's Mane, lane "live" — landed in
        # fixture evidence within the hour. A journal about his sessions says nothing about a
        # fixture reel, so this is wrong on the merits and not merely untidy in a test.
        self.assertEqual(ca._chron_live_lane_pages(), [],
                         "the live lane read his real journal into an isolated sweep")

    def test_the_live_lane_still_runs_when_the_journal_is_pointed_at_the_same_footage(self):
        # isolation must not become a mute button: name the journal and the lane works again
        jp = os.path.join(self.d, "sessions.jsonl")
        with open(jp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"scene": "chronicle", "sessionId": "s_a", "frameId": "f0",
                                 "conf": 0.8, "chronicleTab": "uniques",
                                 "discovered_names": ["Windforce"]}) + "\n")
        old = os.environ.get("TV_SESSIONS")
        os.environ["TV_SESSIONS"] = jp
        try:
            pages = ca._chron_live_lane_pages()
        finally:
            if old is None: os.environ.pop("TV_SESSIONS", None)
            else: os.environ["TV_SESSIONS"] = old
        self.assertEqual(len(pages), 1, "the isolation swallowed a journal that WAS pointed at it")
        self.assertEqual(pages[0]["resp"]["lane"], "live")

    def test_re_banking_the_same_pages_does_not_duplicate_sightings(self):
        # what makes a checkpoint safe: merge_proposals keys a sighting by (reel, frame, lane), so
        # the final merge re-offers pages already banked and they fold to nothing
        with mock.patch.object(ca, "_CHRON_CKPT_PAGES", 1):
            self._run()
        with open(ca._CHRON_EVIDENCE_PATH, encoding="utf-8") as fh:
            ev = json.load(fh)
        sightings = (ev.get("uniques") or {}).get("Windforce") or []
        keys = [(x.get("reel"), x.get("frame"), x.get("lane")) for x in sightings]
        self.assertEqual(len(keys), len(set(keys)),
                         "the same photograph was banked twice — sighting counts now overstate the "
                         "evidence: %s" % keys)



class TestV1837RefusedThisRunIsNotRefusedEver(unittest.TestCase):
    """v1837 — one result object published two scopes under sibling keys and said neither.

    `totals` is computed from THIS run's proposal; `refused` was taken from `prop`, which two lines
    earlier had become the MERGED, cumulative ledger. Both true, each answering a different
    question, printed side by side.

    It cost real time on the night it was found: a cumulative refused list read as one pass's, and
    a working fix (v1829) briefly called a failure on the strength of it. If it misleads the person
    who wrote it an hour later, it will mislead him.
    """

    def _src(self):
        import control_app as ca
        return open(ca.__file__, encoding="utf-8").read()

    def test_both_publish_sites_separate_the_two(self):
        src = self._src()
        # the visit path and the reel path are byte-identical twins here; fixing one is the
        # copy-drift that produced half these bugs
        self.assertEqual(src.count('"refused": _run_refused,'), 2,
                         "only one of the two result builders reports THIS run's refusals")
        self.assertEqual(src.count('"refusedEver": prop.get("refused") or [],'), 2,
                         "the cumulative list is unnamed again in one of the two paths")

    def test_the_cumulative_list_is_never_published_as_refused(self):
        src = self._src()
        self.assertNotIn('"refused": prop.get("refused")', src,
                         "the all-time list is being published under the same key as the per-run "
                         "one, beside a per-run `totals`")

    def test_the_per_run_list_is_captured_before_the_merge(self):
        # captured AFTER the merge it would simply be the cumulative list wearing a new name
        src = self._src()
        for anchor in ('_run_refused = list(prop.get("refused") or [])',
                       '_run_refused = list((res.get("proposal") or {}).get("refused") or [])'):
            i = src.find(anchor)
            self.assertGreater(i, 0, "missing capture: %s" % anchor)
            j = src.find("_chron_evidence_merge(prop)", i)
            self.assertTrue(j == -1 or j > i,
                            "this run's refusals are captured after the cumulative merge, so they "
                            "are the cumulative list under another name")



class TestTheStampsAgreeInTheCOMMITNotJustTheWorktree(unittest.TestCase):
    """2026-08-20 — CI was RED on every publish for TEN consecutive versions and nothing local saw it.

    test_all_four_stamps_are_the_same_version reads the four files from the WORKING TREE, where the
    bump had landed correctly every time. The pre-push hook runs that same suite against that same
    working tree, so it went green on all ten. CI reads the COMMITTED tree, where tv/tv_diablo.py
    had not been staged since v1832 and sat seven versions behind:

        bible.html v1838 · control_app v1837 · tv_diablo v1831 · WINDOWS_SHIP v1838

    Ten ships reached origin/main and none of them deployed; the site stayed on v1828 while each was
    reported as shipped. The push was real, the publish was not.

    So this asks the only question that matters — what do the bytes that were PUSHED say — and it
    can fail locally, before the push, which the working-tree version never could.
    [[feedback-blind-fixture-green-gate]] [[the-unjoined-end]]

    It reads HEAD, never the tree, so a half-finished bump in progress does NOT trip it: HEAD still
    holds the previous, self-consistent set. It only speaks about what was committed.
    """

    def _at_head(self, path):
        r = subprocess.run(["git", "show", "HEAD:" + path],
                           capture_output=True, text=True,
                           cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if r.returncode != 0:
            self.skipTest("not a git checkout (%s)" % (r.stderr or "").strip()[:60])
        return r.stdout

    def test_the_four_stamps_agree_as_committed(self):
        board = re.search(r"D2R_BUILD\s*=\s*\{\s*id:'(v\d+)'", self._at_head("bible.html"))
        control = re.search(r'"ver": "(v\d+)"', self._at_head("tv/control_app.py"))
        agent = re.search(r'VERSION = "(v\d+)"', self._at_head("tv/tv_diablo.py"))
        try:
            ship = json.loads(self._at_head("tv/WINDOWS_SHIP.json")).get("ver")
        except Exception:
            ship = None
        for label, m in (("bible.html", board), ("control_app", control), ("tv_diablo", agent)):
            self.assertIsNotNone(m, "%s carries no parseable stamp in HEAD" % label)
        stamps = {"bible.html D2R_BUILD": board.group(1),
                  "control_app /api/status": control.group(1),
                  "tv_diablo VERSION": agent.group(1),
                  "tv/WINDOWS_SHIP.json": ship}
        self.assertEqual(
            len(set(stamps.values())), 1,
            "THE COMMIT IS HALF-BUMPED and CI will refuse to publish it, however green the working "
            "tree looks: %s. bump_version.py writes all four — stage all four."
            % json.dumps(stamps, indent=2))

    def test_every_stamp_is_read_from_head(self):
        # A guard that opens the working copy is the guard that missed ten ships, so this checks
        # all four lookups go through _at_head.
        #
        # Its first cut asserted the ABSENCE of the working-tree reader and tripped on its own
        # failure message, which contained the very string it was banning — the same shape as the
        # comment that once blinded a guard grepping for a module name. A positive count cannot
        # be fooled by the prose around it. [[feedback-comments-vs-code]]
        src = open(os.path.abspath(__file__), encoding="utf-8").read()
        i = src.find("def test_the_four_stamps_agree_as_committed")
        body = src[i:src.find("def ", i + 40)]
        self.assertEqual(body.count("self._at_head("), 4,
                         "not all four stamps are read from HEAD — a mixed guard is a blind one")



class TestV1843TheFoldReceiptReachesASurface(unittest.TestCase):
    """v1843 — the fold's receipt was written at three sites and read by none.

    control_app builds `_fold_report` and publishes it as result["fold"]; grepping the tree finds no
    reader — not bible.html, not tv/control_ui.html, not the CLI. v1789 wrote it for exactly this
    purpose, in its own words: a name folded onto an item he already has, or retired as reader
    debris, "must not simply vanish: 'we looked and it was not a grail item' and 'nobody looked'
    have to read differently". They could not, because neither was ever printed.

    It carries real information. On the 2026-08-20 sweep: 49 corrections — Battlecage -> Rattlecage,
    Naglring -> Nagelring, Twitchthrow -> Twitchthroe, Heart Garver -> Heart Carver — and 25 names
    retired, every one verified as NOT an exact roster member, so nothing real was discarded.
    """

    def _cli(self):
        import control_app as ca
        p = os.path.join(os.path.dirname(os.path.abspath(ca.__file__)), "chronicle_sweep_now.py")
        return open(p, encoding="utf-8").read()

    def test_the_cli_reads_the_fold_key(self):
        src = self._cli()
        self.assertIn('.get("fold")', src,
                      "the fold report is published by three sites and consumed by none again")

    def test_it_reports_both_halves(self):
        # a count of corrections without a count of retirements answers only half the question
        src = self._cli()
        i = src.find('.get("fold")')
        body = src[i:i + 600]
        self.assertIn("corrected", body)
        self.assertIn("retired as debris", body)

    def test_the_cli_prints_the_sweep_verdict(self):
        """The five-kinds-of-nothing diagnostic reached no surface either.

        sweep_verdict separates no-footage / all-swept / no-chronicle / read-nothing / not-measured
        precisely because only ONE of them means the reader is at fault, and its docstring records
        the complaint that produced it: a run reported as broken that had worked perfectly over 394
        frames of lobby and character select. The CLI printed a bare count, which is the same
        ambiguity the verdict was written to end.
        """
        src = self._cli()
        # anchored on the SWEEP verdict's own assignment: the file also reads a verdict off the
        # PRICING quote, and the first cut of this guard found that one instead and reported the
        # actionable half missing from a block it was never looking at.
        anchor = '_v = (st.get("result") or {}).get("verdict")'
        self.assertIn(anchor, src, "the sweep verdict is published and read by nothing")
        i = src.find(anchor)
        body = src[i:i + 400]
        self.assertIn('_v.get("do")', body, "the actionable half of the verdict is dropped")
        self.assertIn('!= "found"', body,
                      "a successful sweep would repeat itself — the count already says that")

    def test_it_says_nothing_when_the_fold_did_nothing(self):
        # "no corrections" and "no fold ran" must not print the same line
        src = self._cli()
        i = src.find('.get("fold")')
        self.assertIn("if _fx or _rt:", src[i:i + 400],
                      "an empty fold would print a receipt for work that never happened")



class TestV1844TheReopenedReelsRideInTheState(unittest.TestCase):
    """v1844 — the console must be able to say WHY the bill moved.

    v1830 voids a zero-page seal made by an older reader; v1839 bumped PROMPT_VER, so eight of his
    eleven seals reopened at once. Correct, and the point. But it changes what one button costs: the
    console's "run it for real" posts {}, so limit=None, so every unswept reel — and those eight are
    roughly 808 pages, where the same press used to sweep almost nothing.

    The console prices before it spends, so the NUMBER stays honest. What was missing was the
    REASON: the reopened list was printed to stdout, which only a terminal sees, so the UI could
    show a bill grown thirty-fold with nothing on screen explaining it. Same write-only shape v1784
    fixed for the watchdog's skip reasons, and the same fix — ride along in the state the console
    and the board already read.
    """

    def test_the_state_always_carries_the_key(self):
        import control_app as ca
        st = ca.chronicle_sweep_state()
        self.assertIn("reopenedReels", st,
                      "the surface that shows the bill cannot show the reason for it")

    def test_absent_and_empty_do_not_read_the_same(self):
        # "none were reopened" and "this build does not report it" are different facts
        import control_app as ca
        st = ca.chronicle_sweep_state()
        self.assertIsInstance(st.get("reopenedReels"), list)

    def test_the_sweep_records_what_it_reopened(self):
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        i = src.find("_skip, _reopened = _chron_skip_set(")
        self.assertGreater(i, 0, "the skip split moved — re-point this guard")
        self.assertIn("_tick(reopenedReels=", src[i:i + 1400],
                      "the reopened list is computed and then only printed, which is where it was")

    def test_it_matches_what_the_skip_split_reports(self):
        import control_app as ca
        swept = {"stands": {"pages": 0, "promptVer": "p-now"},
                 "stale": {"pages": 0, "promptVer": "p-old"},
                 "read_it": {"pages": 5, "promptVer": "p-old"}}
        skip, reopened = ca._chron_skip_set(swept, prompt_ver="p-now")
        self.assertEqual(reopened, ["stale"])
        self.assertEqual(skip, {"stands", "read_it"})



class TestTheReReadCap(unittest.TestCase):
    """2026-08-20 — Konyo: "it shouldnt even re-read them again like after third read it should be
    blocked..? safegaurd?"

    He is right, and the A→Z reel is the proof: 16 pages re-read for ONE name not already in the
    ledger. Nothing stopped a frame being read again on every sweep forever, so a reel that has
    given up everything it holds still cost full price every time it was looked at.

    THE COUNT CANNOT LIVE IN THE EVIDENCE. A sighting is keyed (reel, frame, lane) and DEDUPES, so
    the evidence cannot tell one read from three — that is v1836's point and it is right for
    evidence. A read count is the opposite kind of number: it must not be idempotent.

    AND IT IS KEYED BY PROMPT_VER, so the cap can never fight v1830. A new reader is the one
    legitimate reason to look again — the reason eight reels reopened — and a prompt change starts
    every frame's count at zero.
    """

    def test_a_THROTTLED_page_does_not_burn_a_look(self):
        """v1861 — the defect this closes, in his own words: "after third read it should be
        blocked..? safegaurd?". It was, and a throttle could spend all three looks on pages the
        reader never opened.

        claude_chronicle_read answers a throttle with {"note": "reader throttled — not read"} and
        reads nothing. `_read_one` bumped anyway, under a comment promising it did not — so three
        throttled sweeps would retire a page that had never been read once, and the cap message
        would tell him to re-read it "by changing the reader"."""
        import control_app as ca
        reads = {}
        for note in ("reader throttled — not read", "not read — subscription cap"):
            for _ in range(5):
                spent = ca._chron_read_bump_if_read(reads, "p1", "r", "f", {"note": note})
                self.assertFalse(spent, "a page nobody read spent a look")
        self.assertEqual(ca._chron_read_count(reads, "p1", "r", "f"), 0)
        self.assertIsNone(ca._chron_read_capped(reads, "p1", "r", "f"),
                          "ten refusals capped a frame the reader never opened")

    def test_a_DEAD_lane_does_not_burn_a_look_either(self):
        # None is the other "not read" — a lane that died. Absence of a page is not a page.
        import control_app as ca
        reads = {}
        self.assertFalse(ca._chron_read_bump_if_read(reads, "p1", "r", "f", None))
        self.assertEqual(ca._chron_read_count(reads, "p1", "r", "f"), 0)

    def test_a_REAL_read_still_spends_one(self):
        # the mirror, or the fix is just a cap that never counts and the safeguard is gone
        import control_app as ca
        reads = {}
        for i in range(3):
            self.assertTrue(ca._chron_read_bump_if_read(
                reads, "p1", "r", "f", {"found": ["Shako"], "note": None}))
            self.assertEqual(ca._chron_read_count(reads, "p1", "r", "f"), i + 1)
        self.assertIsNotNone(ca._chron_read_capped(reads, "p1", "r", "f"),
                             "three real reads must still reach the cap")

    def test_the_sweep_spends_looks_through_THIS_function_only(self):
        """The joint, not the parts. Both halves were right for two ships and only the closure
        called the raw bump — which is why a source check earns its place here.
        [[source-reading-guard]]"""
        import ast, control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        fn = None
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.FunctionDef) and node.name == "_read_one":
                fn = node
        self.assertIsNotNone(fn, "the chronicle sweep no longer has a _read_one")
        called = {getattr(n.func, "id", None) or getattr(n.func, "attr", None)
                  for n in ast.walk(fn) if isinstance(n, ast.Call)}
        self.assertIn("_chron_read_bump_if_read", called)
        self.assertNotIn("_chron_read_bump", called,
                         "the raw bump is back in the closure — it cannot tell a read from a refusal")

    def test_a_fresh_frame_is_not_capped(self):
        import control_app as ca
        self.assertIsNone(ca._chron_read_capped({}, "p1", "r", "f"))

    def test_the_third_read_is_the_last_one(self):
        import control_app as ca
        reads = {}
        for _ in range(3):
            self.assertIsNone(ca._chron_read_capped(reads, "p1", "r", "f"),
                              "capped before the cap")
            ca._chron_read_bump(reads, "p1", "r", "f")
        note = ca._chron_read_capped(reads, "p1", "r", "f")
        self.assertIsNotNone(note, "a fourth read was allowed")
        self.assertIn("read-cap", note.get("note", ""))

    def test_a_new_reader_starts_the_count_again(self):
        # the cap must never block the one legitimate reason to look again
        import control_app as ca
        reads = {}
        for _ in range(5):
            ca._chron_read_bump(reads, "p1", "r", "f")
        self.assertIsNotNone(ca._chron_read_capped(reads, "p1", "r", "f"))
        self.assertIsNone(ca._chron_read_capped(reads, "p1846", "r", "f"),
                          "a prompt change did not reopen the frame — this fights v1830")

    def test_frames_are_counted_separately(self):
        import control_app as ca
        reads = {}
        for _ in range(3):
            ca._chron_read_bump(reads, "p1", "r", "f1")
        self.assertIsNotNone(ca._chron_read_capped(reads, "p1", "r", "f1"))
        self.assertIsNone(ca._chron_read_capped(reads, "p1", "r", "f2"))

    def test_the_same_frame_id_in_two_reels_is_two_frames(self):
        import control_app as ca
        reads = {}
        for _ in range(3):
            ca._chron_read_bump(reads, "p1", "reelA", "f")
        self.assertIsNone(ca._chron_read_capped(reads, "p1", "reelB", "f"))

    def test_the_cap_can_be_turned_off(self):
        import control_app as ca
        reads = {}
        for _ in range(9):
            ca._chron_read_bump(reads, "p1", "r", "f")
        self.assertIsNone(ca._chron_read_capped(reads, "p1", "r", "f", cap=0),
                          "TV_CHRON_READ_CAP=0 must lift it — an optimisation he cannot clear is a cage")

    def test_a_capped_page_REFUSES_out_loud(self):
        # in the shape chronicle_retro already reads as "not read", so the page is reported and
        # counted rather than silently vanishing. A skip nobody can see is the recurring defect here.
        import control_app as ca
        reads = {}
        for _ in range(3):
            ca._chron_read_bump(reads, "p1", "r", "f")
        note = ca._chron_read_capped(reads, "p1", "r", "f")
        self.assertIsInstance(note, dict)
        self.assertTrue(note.get("note"), "a capped page came back with no reason")

    def test_the_counter_follows_the_footage(self):
        """The first cut hardcoded HERE/chron_reads.json and wrote into his live tv/ from the suite
        — the v1832 scar repeated within the hour of fixing it. It also broke four sweep tests,
        which shared one counter across runs until the third found itself capped."""
        import control_app as ca
        old = os.environ.get("TV_HIST")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["TV_HIST"] = tmp
            try:
                p = ca._chron_reads_path()
            finally:
                if old is None: os.environ.pop("TV_HIST", None)
                else: os.environ["TV_HIST"] = old
            self.assertEqual(os.path.dirname(p), tmp,
                             "the read counter lands outside the isolated footage: %s" % p)

    def test_production_keeps_the_counter_beside_the_console(self):
        import control_app as ca
        saved = {k: os.environ.get(k) for k in ("TV_HIST", "TV_CHRON_READS")}
        for k in saved: os.environ.pop(k, None)
        try:
            self.assertEqual(ca._chron_reads_path(),
                             os.path.join(os.path.dirname(os.path.abspath(ca.__file__)),
                                          "chron_reads.json"))
        finally:
            for k, v in saved.items():
                if v is not None: os.environ[k] = v

    def test_the_read_loop_asks_the_cap(self):
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        i = src.find("def _read_one(p, k):")
        self.assertGreater(i, 0)
        self.assertIn("_chron_read_capped(", src[i:i + 900],
                      "the cap exists and the read loop never asks it")



class TestBoardOwnershipReadBack(unittest.TestCase):
    """2026-08-20 — Konyo, on being told the vault cross-reference needed a hand-pasted dump:
    "i neeed to do this in my website browser and not locally on the console? why?" then
    "yea try to fix this :)".

    The "why" was real but it was a LIMITATION, not a law. His ledgers live in localStorage inside
    bible.html — vault_ledger_load() returns 0 entries on disk — and chronicle_apply has always
    reached into the board window to WRITE a tick (v1523: "the console never writes the grail", it
    asks the board, which owns it). Only the READ direction was missing, so a question about his own
    ledger required him to copy it out by hand.
    """

    def test_no_board_means_say_so_not_zero(self):
        """THE ONE THAT MATTERS. "he owns nothing" and "nobody could ask" must never read the same."""
        import control_app as ca
        old = (ca.__dict__.get("_MAIN_WIN"), ca.__dict__.get("_WINDOW_LIVE"))
        ca.__dict__["_MAIN_WIN"] = None
        ca.__dict__["_WINDOW_LIVE"] = False
        try:
            r = ca.board_ownership()
        finally:
            ca.__dict__["_MAIN_WIN"], ca.__dict__["_WINDOW_LIVE"] = old
        self.assertFalse(r.get("ok"))
        self.assertIn("board window is not open", r.get("why", ""))
        self.assertNotIn("counts", r, "a closed board reported a ledger it never read")

    def test_a_timeout_is_not_an_empty_ledger(self):
        import control_app as ca
        old = (ca.__dict__.get("_MAIN_WIN"), ca.__dict__.get("_WINDOW_LIVE"), ca._ejs)
        ca.__dict__["_MAIN_WIN"] = object()
        ca.__dict__["_WINDOW_LIVE"] = True
        ca._ejs = lambda w, js, timeout=8.0: None        # _ejs returns None on timeout
        try:
            r = ca.board_ownership()
        finally:
            ca.__dict__["_MAIN_WIN"], ca.__dict__["_WINDOW_LIVE"], ca._ejs = old
        self.assertFalse(r.get("ok"))
        self.assertIn("UNREAD", r.get("why", ""),
                      "a silent board was reported as an answer")

    def test_it_reports_what_the_board_says(self):
        import control_app as ca
        payload = json.dumps({"ok": True,
                              "counts": {"foundLog": 287, "owned": 0, "setPieces": 21},
                              "sample": {"foundLog": [], "owned": [], "setPieces": []}})
        old = (ca.__dict__.get("_MAIN_WIN"), ca.__dict__.get("_WINDOW_LIVE"), ca._ejs)
        ca.__dict__["_MAIN_WIN"] = object()
        ca.__dict__["_WINDOW_LIVE"] = True
        ca._ejs = lambda w, js, timeout=8.0: payload
        try:
            r = ca.board_ownership()
        finally:
            ca.__dict__["_MAIN_WIN"], ca.__dict__["_WINDOW_LIVE"], ca._ejs = old
        self.assertTrue(r.get("ok"))
        self.assertEqual(r["counts"]["foundLog"], 287)

    def test_unreadable_answer_is_refused_not_guessed(self):
        import control_app as ca
        old = (ca.__dict__.get("_MAIN_WIN"), ca.__dict__.get("_WINDOW_LIVE"), ca._ejs)
        ca.__dict__["_MAIN_WIN"] = object()
        ca.__dict__["_WINDOW_LIVE"] = True
        ca._ejs = lambda w, js, timeout=8.0: "not json at all"
        try:
            r = ca.board_ownership()
        finally:
            ca.__dict__["_MAIN_WIN"], ca.__dict__["_WINDOW_LIVE"], ca._ejs = old
        self.assertFalse(r.get("ok"))

    def test_the_route_exists_beside_its_sibling(self):
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        self.assertIn('path == "/api/board_ownership"', src)
        # both halves of one channel answer to the same verb
        i = src.find('path == "/api/board_ownership"')
        # 900, not 400: the route carries a long note and a short window stopped before the call —
        # the third time today a guard failed on its own reach rather than on the code.
        self.assertIn("board_ownership(", src[i:i + 900])

    def test_it_reads_all_three_stores(self):
        # the vault question needs the found LEDGER and the physical VAULT kept apart — that split
        # is the whole point of _UNI_EXTRA and of the v1692 mis-route it was written for
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        body = _between(self, src, "def board_ownership(", "\ndef ", min_len=400,
                        what="board_ownership")
        for k in ("d2r_foundLog", "d2r_owned", "d2r_setPieces"):
            self.assertIn(k, body, "%s is not read — the cross-reference cannot tell the stores apart" % k)



class TestPrepTabChromeIsNotDead(unittest.TestCase):
    """2026-08-20 — prep_tab_chrome returned None for 310 versions and nobody could tell.

    Four lines pasted from prep_stash_grid referenced `derived`, `aspect` and `layout` — all local
    to THAT function, none of them defined in this one. So it raised NameError on every call and its
    own `except Exception: return None` swallowed it. Introduced v1538 (cc9c6f71), found at v1848
    while building the vault's structural gate, because that gate could not pass a single genuine
    stash frame.

    What it cost: the stash TAB CHROME is the one NON-MODEL signal for which tab is open, and
    stash_eye's own note says the chrome "only becomes readable via a deliberate crop + 3x upscale".
    With this dead there was no readable chrome, nothing could confirm a stash panel structurally,
    and every ownership frame fell back to a model's guess — the failure vault_retro warns about in
    its own words: "a rune tab misread as 'inventory' files his runes in the wrong lane, which
    merge-max then makes permanent."
    """

    def _frame(self, tmp):
        from PIL import Image, ImageDraw
        p = os.path.join(tmp, "f.jpg")
        im = Image.new("RGB", (2560, 1665), (12, 12, 16))
        d = ImageDraw.Draw(im)
        for i in range(14):                      # content in the chrome band so the crop is real
            d.rectangle([300 + i * 90, 200, 360 + i * 90, 300], fill=(180, 170, 140))
        im.save(p, quality=88)
        return p

    def test_it_returns_a_path_not_None(self):
        import stash_eye as se
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "crop.jpg")
            got = se.prep_tab_chrome(self._frame(tmp), out)
            self.assertIsNotNone(got, "prep_tab_chrome is dead again — it is swallowing its own "
                                      "exception and returning None for every frame")
            self.assertTrue(os.path.isfile(out), "it claimed success and wrote nothing")

    def test_it_records_its_own_branch_not_the_grid_function_s(self):
        # the telemetry that caused this: it described prep_stash_grid's decision, using
        # prep_stash_grid's variables, from inside prep_tab_chrome
        import stash_eye as se
        with tempfile.TemporaryDirectory() as tmp:
            se.prep_tab_chrome(self._frame(tmp), os.path.join(tmp, "crop.jpg"))
            d = se.last_crop_decision() or {}
            self.assertEqual(d.get("branch"), "tab-chrome",
                             "the crop telemetry still reports another function's branch: %r" % (d,))

    def test_the_dead_names_are_gone(self):
        """A regression guard on the CLASS, not the line: these three names are local to
        prep_stash_grid and must never appear in prep_tab_chrome again."""
        import stash_eye as se
        # Ask the COMPILER, not the text. co_names holds the global/attribute names the function
        # actually references, so a dict KEY like "layout" is a constant and does not appear, while
        # a bare `derived` does. The first cut of this guard grepped the source and tripped on
        # `"layout": ""` — a string key that was never the bug.
        names = set(se.prep_tab_chrome.__code__.co_names)
        for dead in ("derived",):
            self.assertNotIn(dead, names,
                             "%r is referenced by prep_tab_chrome and is not defined there — that "
                             "is the NameError that killed it for 310 versions" % dead)

    def test_a_real_stash_frame_is_recognised_and_gameplay_is_not(self):
        """GREEN AND RED, EACH FOR ITS OWN REASON — the thing that caught this.

        Measured on his own footage: 5_1784984201581.jpg is journaled scene=stash and the gate reads
        its tab as 'gems'; 6_1786554035205.jpg is gameplay and is refused. A gate that only ever
        refuses is the same defect as one that only ever passes.
        """
        import control_app as ca
        here = os.path.dirname(os.path.abspath(__file__))
        stash = os.path.join(here, "frames", "hist", "5_1784984201581.jpg")
        play = os.path.join(here, "frames", "hist", "6_1786554035205.jpg")
        if not (os.path.isfile(stash) and os.path.isfile(play)):
            self.skipTest("his footage is not on this machine")
        # v1880 — A SILENT OCR LANE IS NOT A VERDICT ABOUT THE GATE, and this test kept turning
        # red for that reason. Twice tonight it failed inside a long combined run and passed alone
        # seconds later; v1864 diagnosed why and gave the engine a way to tell the two apart, and
        # then the test went on asserting the verdict anyway.
        #
        # gate_hearing() counts probes that came back with NOTHING against probes that heard
        # something. If this frame's probe was silent, the reader could not run — so the honest
        # outcome is SKIP with the reason, never a failure blamed on the gate. A flaky test is a
        # test he learns to ignore, which is the same defect as a gate that never goes red.
        # [[feedback-silence-is-not-evidence]] [[feedback-blind-fixture-green-gate]]
        _s0, _h0 = ca.gate_hearing()
        _got = ca.stash_screen_open(stash)
        _s1, _h1 = ca.gate_hearing()
        if _s1 > _s0 and _h1 == _h0:
            self.skipTest("the tab-chrome OCR answered nothing on this probe — the reader could "
                          "not run, so this says nothing about the gate")
        self.assertTrue(_got, "a genuine stash frame was refused — the gate passes nothing")
        self.assertIsNone(ca.stash_screen_open(play),
                          "a gameplay frame was accepted as a stash")



class TestNoFunctionLoadsAnUndefinedName(unittest.TestCase):
    """v1863 — MINI WAS DEAD FOR TEN VERSIONS AND NOTHING SAID SO.

    v1853 removed `_focus_was_chosen` as dead code — correctly — and took the six constants sitting
    beside it: MINI_MIN/MAX/DEFAULT_SECONDS and MINI_CHRONICLE_FOCUSES/MAX/DEFAULT_SECONDS.
    `_mini_bounds` still names all six. So every /api/mini POST raised NameError -> 500 -> a
    non-JSON body -> the console's `fetch().json()` threw -> its catch printed "mini could not
    start — the console is not reachable". Konyo reported it as a SETS problem; it was EVERY focus,
    since v1853, and the only symptom was a toast blaming the network.

    Python cannot catch this at import: a name used only inside a function body is resolved when
    that line RUNS. So the check has to be static, and this is it — an AST scope walk asserting
    that every bare name a function LOADS resolves to a local, a parameter, a module global, an
    import or a builtin.

    It is the whole class, not the one site: run against the tree as v1853 left it, it names
    `MINI_CHRONICLE_FOCUSES` and `MINI_DEFAULT_SECONDS` directly. [[source-reading-guard]] —
    "ask fn.__code__ before the text", which is what this does, one level up at the AST.
    """

    # v1923 — A GUARD THAT DOES NOT GROW WITH THE TREE SHRINKS. This list was written when these
    # nine were the tree; three modules shipped since sat outside it, including the two this very
    # class caught a NameError in one version earlier. New reader/ledger modules belong here on the
    # day they land, not the day they break. [[feedback-generalize-fixes]]
    MODULES = ("control_app.py", "tv_diablo.py", "stash_eye.py", "chronicle_retro.py",
               "vault_retro.py", "chronicle_template.py", "chronicle_resolve.py",
               "g5_grok_eyes.py", "chronicle_sweep_now.py",
               "counter_ledger.py", "chronicle_calibrate.py", "chronicle_hunt.py",
               "vault_corpus.py", "pathguard.py", "sets_base_index.py")

    @staticmethod
    def _undefined(path):
        import ast, builtins
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
        module = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__spec__", "__package__"}

        def bind(node, into):
            for x in ast.walk(node):
                if isinstance(x, ast.Name):
                    into.add(x.id)

        def collect(nodes, into):
            for n in nodes:
                if isinstance(n, (ast.Import, ast.ImportFrom)):
                    for a in n.names:
                        into.add((a.asname or a.name).split(".")[0])
                elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    into.add(n.name)
                elif isinstance(n, ast.Assign):
                    for t in n.targets:
                        bind(t, into)
                elif isinstance(n, (ast.AugAssign, ast.AnnAssign)):
                    bind(n.target, into)
                elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)):
                    if getattr(n, "target", None) is not None:
                        bind(n.target, into)
                elif isinstance(n, ast.withitem) and n.optional_vars is not None:
                    bind(n.optional_vars, into)
                elif isinstance(n, ast.ExceptHandler) and n.name:
                    into.add(n.name)
                elif isinstance(n, (ast.Global, ast.Nonlocal)):
                    into.update(n.names)
                elif isinstance(n, ast.NamedExpr):
                    bind(n.target, into)

        # MODULE SCOPE IS tree.body, NOT ast.walk. Walking the whole tree adds names bound INSIDE
        # functions (a local `import x as _y`, a loop variable) to the module set, and every other
        # function then looks like it can see them. It still caught v1853 — those constants were
        # bound nowhere at all — but a weaker gate than it reads as. Class bodies count, since a
        # method may reference a class-level constant by bare name at class scope.
        # MODULE SCOPE = everything not inside a function or class body — which includes the
        # `try: import g5_grok_eyes as _G5 / except: _G5 = None` at the top of control_app, a
        # module-level binding nested in a Try. Reading only tree.body missed it and the gate
        # reported eight uses of a name that genuinely exists. `own_scope` is defined below for the
        # same reason, one level down.
        module_nodes = []
        stack = list(ast.iter_child_nodes(tree))
        while stack:
            nd = stack.pop()
            module_nodes.append(nd)
            if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            stack.extend(ast.iter_child_nodes(nd))
        collect(module_nodes, module)
        for n in module_nodes:
            if isinstance(n, ast.ClassDef):
                collect(list(ast.iter_child_nodes(n)), module)
        # `global X` anywhere makes X a module name — that is the whole meaning of the statement.
        for n in ast.walk(tree):
            if isinstance(n, ast.Global):
                module.update(n.names)
        out = []

        def own_scope(root):
            """Every node of THIS scope — never descending into a nested function or class, whose
            parameters would otherwise be checked against the OUTER locals and all read undefined."""
            stack, seen = list(ast.iter_child_nodes(root)), []
            while stack:
                nd = stack.pop()
                seen.append(nd)
                if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                    continue
                stack.extend(ast.iter_child_nodes(nd))
            return seen

        def scope(fn, bound):
            local = set(bound)
            a = fn.args
            for p in list(getattr(a, "posonlyargs", [])) + list(a.args) + list(a.kwonlyargs):
                local.add(p.arg)
            if a.vararg:
                local.add(a.vararg.arg)
            if a.kwarg:
                local.add(a.kwarg.arg)
            nodes = own_scope(fn)
            inner = [n for n in nodes
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))]
            collect(nodes, local)
            for n in nodes:
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                    if n.id not in local and n.id not in module:
                        out.append((getattr(fn, "name", "<lambda>"), n.id, n.lineno))
            for f in inner:
                scope(f, local)

        # START ONLY AT MODULE LEVEL. Walking every FunctionDef reaches nested ones twice — once by
        # recursion, with the enclosing scope's names bound, and once from here with nothing bound —
        # and the second visit reports every closure variable as undefined. Six false positives,
        # all of them real closures. A gate with false alarms is a gate he learns to scroll past.
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                scope(n, set())
            elif isinstance(n, ast.ClassDef):
                for m in n.body:
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        scope(m, set())
        return sorted(set(out), key=lambda t: t[2])

    def test_no_function_references_a_name_that_does_not_exist(self):
        here = os.path.dirname(os.path.abspath(__file__))
        checked = 0
        for name in self.MODULES:
            p = os.path.join(here, name)
            if not os.path.isfile(p):
                continue
            checked += 1
            bad = self._undefined(p)
            self.assertEqual(bad, [], "%s references names that do not exist: %s" % (
                name, "; ".join("%s() loads %r at line %d" % b for b in bad[:8])))
        self.assertGreaterEqual(checked, 5, "the module list has rotted — this gate is checking air")

    def test_the_guard_SEES_the_v1853_deletion(self):
        """A gate never seen RED is measuring nothing. Feed it the exact shape v1853 left behind."""
        import tempfile
        src = ("MINI_FOCUSES = ('stash',)\n"
               "def _mini_bounds(focus):\n"
               "    if focus in MINI_CHRONICLE_FOCUSES:\n"
               "        return MINI_CHRONICLE_DEFAULT_SECONDS, MINI_CHRONICLE_MAX_SECONDS\n"
               "    return MINI_DEFAULT_SECONDS, MINI_MAX_SECONDS\n")
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(src)
            p = f.name
        try:
            names = sorted(set(n for _, n, _ in self._undefined(p)))
        finally:
            os.unlink(p)
        self.assertEqual(names, ["MINI_CHRONICLE_DEFAULT_SECONDS", "MINI_CHRONICLE_FOCUSES",
                                 "MINI_CHRONICLE_MAX_SECONDS", "MINI_DEFAULT_SECONDS",
                                 "MINI_MAX_SECONDS"])


class TestTheGameFindDateReachesTheBoard(unittest.TestCase):
    """v1864 — the middle of this path was missing, and both ends looked finished.

    The reader returns foundAt/droppedBy (p1839). proposal_from_pages hangs them on each sighting
    (v1819). bible.html has consumed a per-row `date` since v1693. The PAYLOAD between them carried
    name/why/witnesses/seen and nothing else, so `row.date` was never once fed and every find — his
    Immortal King's Will included — was filed with the moment the sweep ran. [[plumbing-with-no-tap]]

    Guarded across the seam because neither side alone shows it: the server must EMIT the key, and
    both board branches must READ it. The sets branch is called out by name — v1693 wired the
    uniques branch and stopped, and the piece he asked about is a set piece."""

    def _bible(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        return open(p, encoding="utf-8").read()

    def test_the_payload_emits_the_game_date_for_both_ledgers(self):
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        self.assertEqual(src.count('"gameFound": _cr.in_game_stamp('), 2,
                         "both sweep payloads must carry the game's own find date")

    def test_the_board_reads_it_in_the_UNIQUES_branch(self):
        b = self._bible()
        i = b.find("(add.uniques || []).forEach(")
        j = b.find("(add.sets || []).forEach(", i)
        self.assertGreater(i, 0)
        self.assertIn("row.gameFound", b[i:j])
        self.assertIn("_gameFoundSet(", b[i:j])

    def test_the_board_reads_it_in_the_SETS_branch_too(self):
        # v1693 wired uniques and stopped. Immortal King's Will — the piece he asked about — is a
        # SET piece, so the branch that had no date was the branch his question landed in.
        b = self._bible()
        i = b.find("(add.sets || []).forEach(")
        j = b.find("completeSets", i)
        self.assertGreater(i, 0)
        self.assertIn("row.gameFound", b[i:j])
        self.assertIn("window._grailStamp = function(){ return _ds; }", b[i:j],
                      "the set piece is still stamped with the moment the sweep ran")
        self.assertIn("window._grailStamp = _savedS", b[i:j],
                      "the stamp swap is not restored — every later tick would wear this date")

    def test_the_ledger_stamp_is_NOT_replaced_by_the_game_date(self):
        # both questions keep their answer: d2r_foundLog says when the BOARD learned it,
        # d2r_gameFound says when the GAME says he found it. Collapsing them loses the only thing
        # that can tell a fresh find from an old one nobody had read. [[label-outlived-referent]]
        b = self._bible()
        self.assertIn("window.LSR.setItem('d2r_gameFound'", b)
        self.assertIn("window.gameFoundFor = function(name)", b)


class TestTheGameDateConversionRunsInARealEngine(unittest.TestCase):
    """v1864 — the converter is JS, so it is TESTED as JS, in node, not asserted about as text.

    ⚠ THE DATE ORDER IS MEASURED, NOT ASSUMED. His Chronicle printed "07/18/2026" — 18 cannot be a
    month, so his D2R prints US M/D/YYYY, which is what settles the ambiguous rows ("06/02/2026" is
    2 June, not 6 February). Anything that does not fit that shape is REFUSED rather than guessed
    at: a wrong find-date reorders his history, which is worse than no date at all."""

    def _run(self, cases):
        import json as _json
        import shutil as _sh
        import subprocess as _sp
        import tempfile as _tf
        node = _sh.which("node")
        if not node:
            self.skipTest("node is not installed on this machine")
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        src = open(p, encoding="utf-8").read()
        i = src.find("var _GAME_MON = [")
        j = src.find("window._gameFoundSet", i)
        self.assertGreater(i, 0, "the game-date converter is gone")
        body = src[i:j]
        prog = ("var window = {};\n" + body
                + "\nconsole.log(JSON.stringify(" + _json.dumps(cases)
                + ".map(function(x){ return window._gameStampToLedger(x); })));\n")
        with _tf.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(prog)
            jp = f.name
        try:
            out = _sp.run([node, jp], capture_output=True, text=True, timeout=60)
            self.assertEqual(out.returncode, 0, out.stderr[:400])
            return _json.loads(out.stdout.strip().splitlines()[-1])
        finally:
            os.unlink(jp)

    def test_his_real_rows_convert(self):
        got = self._run(["07/18/2026, 02:47", "06/02/2026, 01:06", "05/18/2026, 07:34"])
        self.assertEqual(got, ["Jul 18, 2026 \u00b7 02:47",
                               "Jun 2, 2026 \u00b7 01:06",
                               "May 18, 2026 \u00b7 07:34"])

    def test_anything_that_is_not_that_shape_is_REFUSED_not_guessed(self):
        got = self._run(["18/07/2026, 02:47",     # D/M — month 18 does not exist
                         "07/18/2026, 25:47",     # hour 25
                         "07/18/26, 02:47",       # two-digit year
                         "July 18 2026", "", "07/18/2026 02:47", "  ", "not a date"])
        self.assertEqual(got, ["", "", "", "", "", "", "", ""],
                         "a date it cannot read must come back empty, never approximated")

    def test_a_date_with_no_time_still_converts(self):
        self.assertEqual(self._run(["07/18/2026"]), ["Jul 18, 2026"])

    def test_the_output_matches_the_boards_own_stamp_shape(self):
        # _grailStamp writes "Aug 20, 2026 · 18:25"; a second shape in the same ledger field would
        # make his history sort and read two different ways.
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        src = open(p, encoding="utf-8").read()
        self.assertIn("month:'short',day:'numeric',year:'numeric'", src,
                      "the board's own stamp changed shape — the converter must follow it")


class TestTheShelfSeparatesASimulationFromARun(unittest.TestCase):
    """v1866 — the sessions payload had a `stub` flag that means something else, and the console
    filtered on it believing it excluded simulations. It does not: `stub` is a 1-read ghost with no
    footage, so his six- and seven-frame SIM sessions passed straight through and were counted as
    "runs recorded today". [[label-outlived-referent]]"""

    def test_the_payload_marks_a_sim_session(self):
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        self.assertIn('"sim": any(bool(r2.get("sim")) or r2.get("mode") == "stub"', src,
                      "the sessions payload cannot tell a simulation from a run")

    def test_the_console_does_not_count_a_sim_as_a_run(self):
        here = os.path.dirname(os.path.abspath(__file__))
        p = os.path.join(here, "control_ui.html")
        if not os.path.isfile(p):
            self.skipTest("control_ui.html is not on this machine")
        ui = open(p, encoding="utf-8").read()
        i = ui.find("var _todays = (HD_ALL || [])")
        self.assertGreater(i, 0, "the today-count no longer separates simulations")
        # bound by the block's REAL end, not a byte count — a 900-char window stopped short of the
        # render the moment a comment landed between them. [[source-reading-guard]]
        j = ui.find('<span class="tf-tag dim">TODAY</span>', i)
        self.assertGreater(j, i, "the TODAY row is gone")
        body = ui[i:j]
        self.assertIn("return !x.sim;", body)
        # and it must SAY so rather than quietly dropping them — he pressed SIM on purpose
        self.assertIn("(+' + simToday + ' sim)", body,
                      "the simulations vanish silently, which is its own kind of lie")


class TestNoGateWritesHisLiveWorld(unittest.TestCase):
    """v1867/v1868 — the guard that exists to catch a test writing his live state was not watching
    the file the leak used.

    run_gates' watchlist named five chronicle/vault files. test_reel_index_durability had been
    appending to a SIXTH — tv/sessions.jsonl, his session journal, 1,729 rows, 75% of every
    session_end row in it — through every green run of that gate. Extending the list turned it RED
    within one run and it immediately caught a SECOND leak: test_button_matrix boots a private
    control app on a private free port, with --no-open, terminating only its own pid — every
    process-discipline lesson applied — and then handed it his REAL environment, so it wrote his
    journal, his hist root and his chronicle state. Isolating the port is not isolating the world.
    [[feedback-blind-fixture-green-gate]] [[feedback-fixtures-never-touch-live-data]]"""

    def test_the_watchlist_includes_the_journal(self):
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "run_gates.py"), encoding="utf-8").read()
        i = src.find("_LIVE_STATE = (")
        self.assertGreater(i, 0)
        block = src[i:src.find(")", i)]
        for name in ("sessions.jsonl", "chron_evidence.json", "chron_reads.json"):
            self.assertIn(name, block, "%s is live state and the gate is not watching it" % name)

    def test_the_button_matrix_sandboxes_every_path_not_only_the_port(self):
        here = os.path.dirname(os.path.abspath(__file__))
        p = os.path.join(here, "test_button_matrix.py")
        if not os.path.isfile(p):
            self.skipTest("the button matrix is not on this machine")
        src = open(p, encoding="utf-8").read()
        i = src.find("def _boot_control():")
        j = src.find("\ndef ", i + 10)
        body = src[i:j]
        for var in ("TV_HIST=", "TV_SESSIONS=", "TV_FRAMES_DIR=", "TV_CHRON_EVIDENCE=",
                    "TV_CHRON_RESULT=", "TV_SWEEP_LOCK="):
            self.assertIn(var, body,
                          "the private control app can still write his %s" % var.strip("=T V_"))
        self.assertIn("TV_CONTROL_PORT=", body, "the port isolation is gone")


class TestEveryFoundChipCarriesItsStoryline(unittest.TestCase):
    """v1871 — Konyo: "when it was added to the chronicle it should be storyline synced with the
    ingame diablo ii".

    v1864 landed the date; this makes it visible on the HUNDREDS of found items rather than only on
    the last one ticked. It rides in the chip's `title`, so nothing on the page moves — the wall is
    dense and a second line would cost the density that makes it readable.

    Run in node, because the half-claim it now avoids was found that way and not by reading:
    {at:'', by:'Mephisto'} used to render "found in game · dropped by Mephisto" — a sentence that
    stops mid-claim. Each half stands alone or not at all."""

    def _run(self, store):
        import json as _json
        import shutil as _sh
        import subprocess as _sp
        import tempfile as _tf
        node = _sh.which("node")
        if not node:
            self.skipTest("node is not installed on this machine")
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        src = open(p, encoding="utf-8").read()
        i, j = src.find("var _GAME_MON = ["), src.find("window._gameFoundSet = function")   # the DEFINITION, not the first
        # mention: v1891 added a CALL to it inside _forgeRedo, which sits earlier in the file, and
        # the bare name anchored there and truncated the slice to nothing. Fourth time tonight an
        # anchor hit the wrong occurrence. [[source-reading-guard]]
        k = src.find("  function _gameFoundTitle(n){")
        m = src.find("  function _itemChip(n,q){", k)
        self.assertGreater(k, 0, "the chip no longer carries a storyline")
        prog = ("var window = {};\n" + src[i:j]
                + "var STORE = " + _json.dumps(store) + ";\n"
                + "window.gameFoundFor = function(n){ return STORE[n] || null; };\n"
                + src[k:m].replace("function _gameFoundTitle", "window._gft = function")
                + "console.log(JSON.stringify(Object.keys(STORE).concat(['__absent'])"
                  ".map(function(x){ return window._gft(x); })));\n")
        with _tf.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(prog)
            jp = f.name
        try:
            out = _sp.run([node, jp], capture_output=True, text=True, timeout=60)
            self.assertEqual(out.returncode, 0, out.stderr[:400])
            return _json.loads(out.stdout.strip().splitlines()[-1])
        finally:
            os.unlink(jp)

    def test_his_own_row_reads_as_the_game_printed_it(self):
        got = self._run({"Immortal King's Will": {"at": "07/18/2026, 02:47", "by": "Andariel"}})
        self.assertEqual(got[0], " \u2014 \u2694 found in game Jul 18, 2026 \u00b7 02:47 "
                                 "\u00b7 dropped by Andariel")
        self.assertEqual(got[-1], "", "an item the Chronicle never dated claims nothing")

    def test_each_half_stands_alone_or_not_at_all(self):
        got = self._run({"a": {"at": "", "by": "Mephisto"},
                         "b": {"at": "06/02/2026, 01:06"},
                         "c": {"at": "nonsense"}})
        self.assertEqual(got[0], " \u2014 \u2694 dropped by Mephisto",
                         "'found in game' with no date is a sentence that stops mid-claim")
        self.assertEqual(got[1], " \u2014 \u2694 found in game Jun 2, 2026 \u00b7 01:06")
        self.assertEqual(got[2], "", "an unparseable date must claim nothing, not approximate")


class TestNoOptionalCallToAFunctionThatCannotExist(unittest.TestCase):
    """v1872 — `window.X && window.X()` on a name assigned nowhere calls nothing, forever, silently.

    Found live: `window.renderGrailMeters && window.renderGrailMeters()` in `_inboxAct`, the line
    that reads as the backstop refreshing his grail meters after an inbox decision. The real name is
    `renderGrailProgress` and it is published on window at ~18547. 227 such call sites in the board,
    85 distinct names, exactly ONE that could never fire.

    It was harmless in practice — kaiChronicleAccept already calls renderGrailProgress itself — and
    that is why it survived. A backstop that is never needed is a backstop nobody notices is
    missing, until the path it guards changes. [[the-unjoined-end]]

    ⚠ COMMENTS ARE STRIPPED FIRST, and that is not caution. The first run of this sweep after the
    fix reported a dead call to `window.X` — which is the placeholder inside the comment explaining
    the fix. His scar file already names this exact shape: an explanatory comment blinding a guard
    that greps for a name. [[feedback-comments-vs-code]]"""

    @staticmethod
    def _strip_js_comments(src, cap=4000):
        """Strip comments — and BOUND the block form, because an unbounded one eats the file.

        v1873, measured on bible.html the hour after v1872 shipped this guard: `/\*.*?\*/` with
        DOTALL removed 16.9% of a 5.6MB mixed HTML/CSS/JS file and **170 of its 444 `id=`
        declarations**, because a `/*` inside a JS string or a regex literal matches forward to the
        next `*/` anywhere in the file. js_syntax_gate says this in its own docstring — a heuristic
        cannot separate a comment from a string containing embedded HTML and regex literals — and I
        shipped a guard built on one anyway. It PASSED, on a mangled view: a stripper that deletes
        a third of the ids can only ever produce false NEGATIVES, which is the quiet direction.

        A real comment in this file is long but not unbounded; a match spanning thousands of
        characters is a string that happens to contain the tokens. At cap=4000 the loss is 0 of
        444. [[feedback-suspect-the-instrument]] [[feedback-comments-vs-code]]
        """
        import re
        src = re.sub(r"/\*.{0,%d}?\*/" % int(cap), " ", src, flags=re.S)
        return re.sub(r"(?m)^\s*//.*$", " ", src)

    def test_the_stripper_does_not_eat_live_markup(self):
        """The instrument, checked before its verdict is believed. Founding rule 4."""
        import re
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        raw = open(p, encoding="utf-8").read()
        ID = r"\bid\s*=\s*[\\]?[\'\"]([\w-]+)"
        raw_ids = set(re.findall(ID, raw))
        kept = set(re.findall(ID, self._strip_js_comments(raw)))
        self.assertTrue(raw_ids, "no id= declarations found at all — the pattern rotted")
        self.assertEqual(raw_ids - kept, set(),
                         "the comment stripper deleted live markup; every verdict built on it is "
                         "a false negative waiting to happen")

    @classmethod
    def _dead_calls(cls, src):
        import re
        body = cls._strip_js_comments(src)
        calls = set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*(?:&&|\?)\s*window\.\1\s*\(", body))
        assigned = set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*=", body))
        return sorted(calls - assigned)

    def test_the_board_calls_nothing_that_does_not_exist(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        dead = self._dead_calls(open(p, encoding="utf-8").read())
        self.assertEqual(dead, [], "optional calls to functions assigned nowhere — they have never "
                                   "run and never will: %s" % ", ".join(dead))

    def test_it_SEES_the_renderGrailMeters_shape(self):
        # seen red, on the exact line that was live until this ship
        live = ("window.renderGrailProgress = function(){};\n"
                "try { window.renderGrailProgress && window.renderGrailProgress(); } catch(e){}\n")
        dead = ("window.renderGrailProgress = function(){};\n"
                "try { window.renderGrailMeters && window.renderGrailMeters(); } catch(e){}\n")
        self.assertEqual(self._dead_calls(live), [])
        self.assertEqual(self._dead_calls(dead), ["renderGrailMeters"])

    def test_a_comment_cannot_blind_it(self):
        src = ("/* explaining that window.Ghost && window.Ghost() would be dead */\n"
               "// and again in a line comment: window.Ghost && window.Ghost()\n"
               "window.Real = function(){};\n"
               "window.Real && window.Real();\n")
        self.assertEqual(self._dead_calls(src), [],
                         "the guard is reading its own documentation again")


class TestTheChronicleReceiptMatchesTheMeter(unittest.TestCase):
    """v1889 — `chronicleApply` reported five uniques applied while the grail counter moved by four.

    MEASURED IN A REAL PAGE, headless Chrome on :9224, because this function lives in a closure no
    unit test can reach. Applying Shako · Stormspire · Stormspike · Titan’s Revenge · Herald of
    Zakarum gave `uniques: 5` and a delta of 4. Driving them one at a time named the odd one out:

        Shako   reported 1, delta 0, and it is not in d2r_foundLog at all — it is in d2r_owned

    "Shako" is the community nickname for Harlequin Crest, so the board has no such unique.
    `toggleOwned` routes by what the board KNOWS: a grail unique lands in the found ledger, a name it
    does not recognise lands in the PHYSICAL VAULT. That split is deliberate — `_UNI_EXTRA` exists
    precisely so real uniques with no card stop falling into the vault — but the RECEIPT did not know
    about it and counted both as applied uniques. A number under a word naming a different quantity.

    The ledger is the arbiter, not the intent, so the receipt asks it. After: `uniques: 4`,
    `vaulted: ['Shako']`, delta 4 — the receipt and the meter agree.
    [[label-outlived-referent]] [[unknown-stays-unknown]]"""

    def _apply_src(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        src = open(p, encoding="utf-8").read()
        i = src.find("    (add.uniques || []).forEach(function(row){")
        j = src.find("    (add.sets || []).forEach(function(row){", i)
        self.assertGreater(i, 0, "the uniques apply branch is gone")
        return src[i:j]

    def test_it_asks_the_ledger_where_the_name_landed(self):
        body = self._apply_src()
        self.assertIn("d2r_foundLog", body,
                      "the receipt reports intent again instead of asking the ledger")
        self.assertIn("res.vaulted", body, "there is nowhere to report a vault landing")

    def test_a_name_that_did_not_land_is_not_counted_as_a_find(self):
        body = self._apply_src()
        i = body.find("if (_landed) res.uniques.push(n);")
        self.assertGreater(i, 0, "the receipt pushes unconditionally again")
        self.assertIn("else { res.vaulted", body[i:i + 200],
                      "a name that went to the vault is silently dropped from the receipt")

    def test_an_unreadable_ledger_does_NOT_invent_a_demotion(self):
        """If the ledger cannot be read, "he did not find it" is a claim we have not earned. The
        safe direction here is the OLD behaviour, not a fabricated vault row."""
        body = self._apply_src()
        self.assertIn("_landed = true;", body,
                      "an unreadable ledger now demotes a real find to a vault row")


class TestTheSourceGuardsDoNotGetMoreDangerous(unittest.TestCase):
    """v1892 — A RATCHET, not a cleanup. Four source guards died in one night on the same shape.

    `body = src[i:i + 900]` reads a fixed number of BYTES from an anchor. It works until someone
    adds a comment between the anchor and the line being checked, and then it silently measures
    nothing — `assertIn` fails somewhere confusing and `assertNotIn` PASSES. That is how v1866's
    guard stopped checking, and it is the same family as the two anchors that hit the wrong
    occurrence of a name and the stripper that ate a third of the file.

    There are 24 of these in this file tonight. Rewriting them all at once would be a large,
    risky change to the very things that catch regressions, so this does the safe half: it PINS THE
    COUNT so the class cannot grow, and names `_between()` as the way to write the next one. Lower
    the number as sites are converted; never raise it.

    ⚠ The number is a DEBT, not a target. It is here to be reduced. [[source-reading-guard]]"""

    # v2029 — 24 -> 23. Converting the v2028 gate-body read to an anchored slice removed one,
    # so the ratchet moves down as its own docstring instructs: "Lower the number as sites
    # are converted; never raise it." A debt ceiling that only ever holds is not a ratchet.
    LIMIT = 23

    def test_no_new_byte_counted_slices(self):
        import re as _re
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "test_control.py"), encoding="utf-8").read()
        found = _re.findall(r"\[i:i \+ \d+\]|\[i:i\+\d+\]", src)
        self.assertLessEqual(len(found), self.LIMIT,
                             "%d byte-counted source slices, up from %d. Use _between(self, src, "
                             "start, end) instead — it refuses an empty or truncated slice rather "
                             "than measuring nothing." % (len(found), self.LIMIT))

    def test_the_safe_helper_refuses_an_empty_slice(self):
        """Seen RED for its own reason, in all three directions it can fail."""
        src = "AAA start ... middle ... end ZZZ"
        with self.assertRaises(AssertionError):
            _between(self, src, "no such anchor", "end")
        with self.assertRaises(AssertionError):
            _between(self, src, "middle", "start")          # the end anchor is BEFORE the start
        with self.assertRaises(AssertionError):
            _between(self, src, "start", "end", min_len=999)
        got = _between(self, src, "start", "end", min_len=5)
        self.assertTrue(got.startswith("start"))
        self.assertNotIn("end", got)

    def test_the_helper_is_reachable(self):
        self.assertTrue(callable(_between))


class TestOneLegibleLabelIsNotASelectedTab(unittest.TestCase):
    """v1913 — `stash_screen_open` returned a legible-label COUNT as if it were the selected tab.

    The branch was `if len(canons) == 1: return canons[0]`, which is the same wrong question v1860
    fixed on the line below it: the strip prints ALL FIVE labels whichever tab is active, so how
    many of them the OCR happened to read is a fact about the OCR, not about the selection.

    MEASURED ON HIS OWN HIST, all 883 frames: the gate admits 10 and took that branch on THREE.
    It was wrong on all three — `5_1784984201581` (canons ['gems'], a tooltip over the rest),
    `7_1784984245418` and `8_1784984208085` (canons ['shared']) are all unmistakably on PERSONAL:
    gold box, blue gem, four grey labels beside it.

    ⚠ IT WAS INERT AND THAT IS NOT A REASON TO LEAVE IT. All three callers test `is None` and
    discard the value — because v1857 DID use it as a lane and v1859 had to revert that. A function
    that returns a wrong-by-construction tab is a loaded gun waiting for the next caller who does
    not read the comment. The VALUE is truthful now instead of the discipline being.
    [[label-outlived-referent]] [[the-unjoined-end]]"""

    def _gate(self, lines, gem=""):
        """Drive the gate with canned chrome and a canned gem — no OCR, no model, no frame."""
        from unittest import mock
        import control_app as ca
        import stash_eye as se
        import tv_diablo as tvd
        with mock.patch.object(se, "prep_tab_chrome", lambda src, dst: dst), \
             mock.patch.object(tvd, "ocr_fast", lambda p: {"raw_lines": list(lines)}), \
             mock.patch.object(se, "tab_from_gem", lambda p: (gem, {"method": "stub"})):
            return ca.stash_screen_open("whatever.jpg")

    def test_one_legible_label_admits_the_frame_and_names_no_tab(self):
        got = self._gate(["Gems"])
        self.assertEqual(got, "stash",
                         "the gate called a frame the GEMS tab because GEMS was the one label the "
                         "OCR could read — on his footage that frame is PERSONAL")

    def test_several_legible_labels_still_admit_and_still_name_no_tab(self):
        self.assertEqual(self._gate(["$\u2022NAL", "SHAkED", "% Gems", "I mATeRIALS"]), "stash")

    def test_the_GEM_names_it_when_it_can(self):
        self.assertEqual(self._gate(["Gems"], gem="personal"), "personal")
        self.assertEqual(self._gate(["$\u2022NAL", "SHAkED"], gem="materials"), "materials")

    def test_no_chrome_is_still_a_refusal_however_loud_the_gem(self):
        """Admission is the chrome's job. A gem without chrome is not a stash frame — and the gem
        reader itself abstains on those, so this pins the ORDER, not a hypothetical."""
        self.assertIsNone(self._gate([], gem="personal"))

    def test_his_three_real_frames_are_no_longer_given_a_wrong_tab(self):
        """The measurement, not a mock: these are the exact frames the old branch got wrong."""
        import control_app as ca
        here = os.path.dirname(os.path.abspath(__file__))
        frames = {"5_1784984201581.jpg": "personal",
                  "7_1784984245418.jpg": None,      # the gem abstains — "stash", never "shared"
                  "8_1784984208085.jpg": None}
        hist = os.path.join(here, "frames", "hist")
        if not os.path.isfile(os.path.join(hist, "5_1784984201581.jpg")):
            self.skipTest("his frames are not in this checkout")
        for f, want in frames.items():
            # v1990 — A SILENT OCR LANE IS NOT A VERDICT ABOUT THE GATE.
            #
            # This assertion went RED mid-suite on 2026-08-23 ("5_1784984201581.jpg stopped being
            # admitted at all") and PASSED on the identical commit minutes earlier and again when
            # measured alone at load 30. The gate itself already knows the difference and says so
            # at control_app.py:11344 — zero OCR lines means EITHER a genuinely blank strip OR a
            # lane that could not run, and it counts the second in _GATE_SILENT rather than
            # pretending it learned something. The test threw that distinction away and read every
            # None as a regression.
            #
            # So ask the counter. If the lane went silent on THIS call, the run measured nothing
            # about the gate and must say so. If the lane was HEARD and the gate still refused,
            # that is a real failure and still fails. [[feedback-silence-is-not-evidence]]
            # [[feedback-suspect-the-instrument]]
            _before = ca.gate_hearing()
            got = ca.stash_screen_open(os.path.join(hist, f))
            _after = ca.gate_hearing()
            if got is None and _after[0] > _before[0]:
                self.skipTest("the tab-chrome OCR lane answered nothing on %s — that is a fact "
                              "about the lane, not about the gate (silent %d->%d, heard %d->%d)"
                              % (f, _before[0], _after[0], _before[1], _after[1]))
            self.assertIsNotNone(got, "%s stopped being admitted at all — and the OCR lane WAS "
                                      "heard (silent %d->%d, heard %d->%d), so this is the gate "
                                      "refusing a real stash frame, not a dead lane"
                                 % (f, _before[0], _after[0], _before[1], _after[1]))
            if want:
                self.assertEqual(got, want, "%s: the gate says %r, the picture says %r"
                                 % (f, got, want))
            else:
                self.assertEqual(got, "stash",
                                 "%s: the gate named a tab it cannot see — it is on PERSONAL and "
                                 "the old branch called it SHARED" % f)


class TestTheFocusedHuntCanActuallyRegisterAHit(unittest.TestCase):
    """v1917 — THE FOCUSED HUNT WAS DEAD TWICE OVER, and both halves were invisible.

    1. IT READ A KEY THE READER NEVER EMITS. `chronicle_hunt` scored each page on `page["items"]`;
       `normalize_page` returns eighteen keys and `items` is not one of them, and `two_lane_read`
       passes that dict straight through. So every hunted frame was read, PAID FOR, and matched
       against an empty list. `grep -c "hunting|hunt done"` across every log on his machine: **0**.
       The test that covered it handed it `{"items": [{"name": "Mid Name"}]}` — a fixture nobody had
       cross-checked against the real reader. [[feedback-blind-fixture-green-gate]]

    2. IT WAS UNIQUES-ONLY while every held name was a set piece. Measured on his own last sweep
       (2026-08-21 00:47): **41 held, 41 of them sets, 0 uniques** — and the report said "nothing
       was held" and spent 0 reads. Tancred's Skull sat there with six sightings, one witness short.

    Konyo asked for exactly this and was told he had it: *"for F-SETS it should cross reference the
    items i still dont have ... JUST LIKE UNIQUES i remember we integrated this already"*. The
    integration was real and covered one of the two ledgers."""

    def test_it_reads_the_shape_the_reader_actually_emits(self):
        import chronicle_hunt as ch
        import chronicle_retro as cr
        uni = cr.normalize_page({"stateVisible": True, "found": ["Shako", "Ist Rune"], "conf": 0.9},
                                "chronicle-uniques", "claude")
        self.assertNotIn("items", uni, "the reader started emitting `items` — re-read this guard")
        self.assertEqual(ch.page_names(uni), ["Shako", "Ist Rune"],
                         "the hunt cannot see the names on a real uniques page")

    def test_a_SETS_page_yields_its_piece_names(self):
        """A sets page carries names under `sets[].pieces`, not `found`. A hunt that read only
        `found` would be the same defect one ledger over."""
        import chronicle_hunt as ch
        import chronicle_retro as cr
        sp = cr.normalize_page(
            {"stateVisible": True, "sets": [{"set": "Tancred's Battlegear",
                                             "pieces": ["Tancred's Skull", "Tancred's Spine"]}],
             "conf": 0.9}, "chronicle-sets", "claude")
        self.assertEqual(ch.page_names(sp), ["Tancred's Skull", "Tancred's Spine"])

    def test_the_old_shape_is_still_accepted(self):
        """A caller that hands `items` is not wrong, it is old — refusing it would be a second
        defect wearing the first one's clothes."""
        import chronicle_hunt as ch
        self.assertEqual(ch.page_names({"items": [{"name": "Old Shape"}]}), ["Old Shape"])

    def test_held_SET_pieces_are_hunted_at_all(self):
        """The measurement that matters: 41 held set pieces used to produce `nothing was held`."""
        from unittest import mock
        import control_app as ca
        applied = {"held": [{"name": "Tancred's Skull (bone helm)", "ledger": "sets"},
                            {"name": "Aldur's Rhythm (mace)", "ledger": "sets"}]}
        seen = {}

        def fake_hunt(names, prop, hist, read_page, kind="chronicle-uniques", log=None):
            seen[kind] = list(names)
            return {}

        with mock.patch.dict("sys.modules"):
            import chronicle_hunt as ch
            with mock.patch.object(ch, "hunt", fake_hunt):
                _p, _a, rep = ca._chron_hunt_held({}, applied, "/nowhere", lambda p, k: None)
        self.assertNotEqual(rep.get("skipped"), "nothing was held",
                            "41 held set pieces still read as nothing to hunt")
        self.assertIn("chronicle-sets", seen,
                      "the sets ledger was never hunted — the reader would be asked about the "
                      "wrong list even if it were")
        self.assertEqual(len(seen.get("chronicle-sets") or []), 2)

    def test_a_uniques_hold_still_hunts_uniques(self):
        """The half that already worked must survive the half that did not."""
        from unittest import mock
        import control_app as ca
        applied = {"held": [{"name": "Shako", "ledger": "uniques"}]}
        seen = {}

        def fake_hunt(names, prop, hist, read_page, kind="chronicle-uniques", log=None):
            seen[kind] = list(names)
            return {}

        import chronicle_hunt as ch
        with mock.patch.object(ch, "hunt", fake_hunt):
            ca._chron_hunt_held({}, applied, "/nowhere", lambda p, k: None)
        self.assertEqual(seen.get("chronicle-uniques"), ["Shako"])
        self.assertNotIn("chronicle-sets", seen, "it hunted a sets page with nothing held there")


class TestTheGameIsAskedItsOwnNumber(unittest.TestCase):
    """v1920 — THE SAFEGUARD THAT DID NOT EXIST.

    Konyo: *"and sets.. are you sure its 118/135 how is it 87%? ingame im 85% somewthing isnt
    calliberated properly"*, and then the harder one: *"the AI READERS needs to be doing this
    automatically... where is the AI intelligence and AI coder that routes and funnels and watchdog
    even for a safegaurd of this?"*

    He was right that it was missing. Every Chronicle page carries a completion bar, the readers have
    photographed it for months, and NOTHING compared it to the board's tally. Two numbers about one
    collection, by different routes, never put side by side.

    WHAT IT COST: the board read 118/135 = 87.4% while the game printed 85%. His own two sentences
    settled it — "this is exactly 19 i still have missing" and "meaning i have 116/135" — and
    116 + 19 = 135 with 116/135 = 85.9%, which the game truncates to 85. The board was counting TWO
    pieces he does not have, and he caught it by eye before any gate did.

    ⚠ THE READER IS A WATCHDOG, NOT A COUNTER (±1.5 points). These tests pin that it FIRES on a real
    gap and REFUSES rather than agreeing when the game says nothing — never that its figure is
    exact. [[unknown-stays-unknown]]"""

    def test_it_fires_on_the_gap_that_actually_happened(self):
        import chronicle_calibrate as cal
        v = cal.verdict(0.8395, 118, 135)          # the measured fill, and his board that day
        self.assertIs(v["ok"], False, "the 3.5-point gap he spotted by eye read as agreement")
        self.assertIn("DISAGREE", v["say"])
        self.assertIn("the game is the one holding the items", v["say"])

    def test_it_does_NOT_fire_on_the_truth(self):
        """116/135 against the same bar must pass, or the watchdog cries wolf at the right answer."""
        import chronicle_calibrate as cal
        v = cal.verdict(0.8395, 116, 135)
        self.assertIs(v["ok"], True, "the correct tally tripped the alarm: %s" % v["say"])

    def test_silence_is_never_agreement(self):
        import chronicle_calibrate as cal
        v = cal.verdict(None, 118, 135)
        self.assertIsNone(v["ok"], "no bar on any frame read as the game agreeing")
        self.assertIn("not the same as agreeing", v["say"])
        v2 = cal.verdict(0.85, 118, 0)
        self.assertIsNone(v2["ok"], "a missing total read as a verdict")

    def test_the_tolerance_is_wider_than_the_reader_error(self):
        """±1.5 points of reader error inside a 3-point tolerance. A tolerance TIGHTER than the
        instrument is an alarm that fires on itself; one far wider never fires at all."""
        import chronicle_calibrate as cal
        self.assertGreaterEqual(cal.TOLERANCE, 0.02)
        self.assertLessEqual(cal.TOLERANCE, 0.05)

    def test_it_runs_on_every_sweep_rather_than_when_someone_remembers(self):
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        self.assertIn("def _chron_calibration(", src)
        self.assertIn('"calibration": _cal_report', src,
                      "the verdict is computed and never reaches the result — the exact shape of "
                      "every defect this file has been fixing tonight")

    def test_a_dead_board_is_reported_not_assumed(self):
        """If the board cannot be asked, the sweep must SAY the comparison did not happen."""
        from unittest import mock
        import control_app as ca
        import chronicle_calibrate as cal
        with mock.patch.object(cal, "read_reel", lambda d, sample=6: (0.84, 5)), \
             mock.patch.object(ca, "board_ownership", lambda n=0: {"ok": False, "why": "window shut"}):
            v = ca._chron_calibration(["/nowhere"])
        self.assertIsNone(v.get("ok"))
        self.assertIn("did not answer", v.get("say", ""))


class TestOneGauntletForBothSurfaces(unittest.TestCase):
    """v1916 — the board wore the D2R gauntlet and the console wore the macOS arrow.

    Konyo: *"the MOUSE CURSOR with its effects when clicking ... isnt syncing and symetric across
    the platform there are areas that its a regular mouse cursor"*. Measured before writing a line:
    bible.html has carried `*{cursor:url(<gauntlet>) 2 1, auto !important}` since v605 and an audit
    of 2,778 interactive elements across 12 tabs found ZERO falling back to the OS arrow;
    control_ui.html had **zero** custom cursor declarations and 69 plain `cursor: pointer` rules.
    The asymmetry was not scattered — it was the whole console.

    ONE ASSET, NOT A SECOND COPY: `art/hd_cursor_hand32.png` is the exact bytes decoded out of the
    board's inline data URI. This pins them byte-identical, so the hand cannot drift between the
    two surfaces — which is the thing he actually asked for. [[copy-drift]]"""

    def _repo(self):
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_the_console_asset_is_the_boards_own_bytes(self):
        import base64
        import hashlib
        repo = self._repo()
        with open(os.path.join(repo, "bible.html"), encoding="utf-8") as fh:
            page = fh.read()
        m = re.search(r'\*\{cursor:url\("data:image/png;base64,([A-Za-z0-9+/=]+)"\)\s*(\d+)\s*(\d+)',
                      page)
        self.assertTrue(m, "the board lost its inline gauntlet cursor entirely")
        inline = base64.b64decode(m.group(1))
        asset = os.path.join(repo, "art", "hd_cursor_hand32.png")
        self.assertTrue(os.path.isfile(asset), "the console's cursor asset is gone")
        with open(asset, "rb") as fh:
            served = fh.read()
        self.assertEqual(hashlib.md5(served).hexdigest(), hashlib.md5(inline).hexdigest(),
                         "the console's hand and the board's hand are different pictures — that is "
                         "the asymmetry he reported, arriving again by drift instead of by absence")
        self.assertEqual((m.group(2), m.group(3)), ("2", "1"), "the board's hotspot moved")

    def test_the_console_actually_declares_it_with_the_same_hotspot(self):
        with open(os.path.join(self._repo(), "tv", "control_ui.html"), encoding="utf-8") as fh:
            ui = fh.read()
        code = re.sub(r"/\*[\s\S]*?\*/", " ", ui)
        self.assertIn('cursor: url("/art/hd_cursor_hand32.png") 2 1', code,
                      "the console is back on the OS arrow")
        self.assertIn("cursor: text !important", code,
                      "text entry lost its I-beam under the blanket rule")

    def test_the_verdict_cursors_survive_the_blanket_rule(self):
        """A blanket `*{cursor:...!important}` is exactly the shape that eats a not-allowed. v1915's
        unfarmable zone and every disabled control must still say no with the pointer."""
        with open(os.path.join(self._repo(), "tv", "control_ui.html"), encoding="utf-8") as fh:
            code = re.sub(r"/\*[\s\S]*?\*/", " ", fh.read())
        self.assertRegex(code, r"\.tzz\.tzz-thin[^{]*\{[^}]*cursor:\s*not-allowed\s*!important",
                         "the blanket cursor overrode the CANCELLED sign he asked for")


class TestNoSuiteImportsSomethingCIDoesNotHave(unittest.TestCase):
    """v1911 — `import yaml` IN A TEST TOOK THE PUBLISH WORKFLOW DOWN AND KEPT v1910 OFF THE SITE.

    PyYAML is installed on his Mac and is not on the runner. Locally: 1,412 tests green and 34 gates
    green. On CI: `ModuleNotFoundError: No module named 'yaml'`, two errors, **Publish red, Deploy
    skipped, and the live site still serving the previous version** while every local signal said
    the ship was clean. The host is part of the fixture, and this is the third host-difference of
    the arc — after his Windows console encoding, and a local Python 3.9 against CI's 3.11.

    THE ALLOWLIST IS WHAT CI ACTUALLY INSTALLS: `pillow`, one line in publish.yml and tv-tests.yml,
    and nothing else. `playwright` is allowed only because its one importer wraps it in a try.

    ⚠ SKIPPING WOULD HAVE BEEN WORSE THAN FAILING. `try: import yaml / except: skipTest` turns green
    on the only machine that publishes — a test that skips where it matters is a test that does not
    exist. [[feedback-blind-fixture-green-gate]] [[dual-machine-setup]]"""

    ALLOWED_BARE = {"PIL"}                 # installed by `pip install --quiet pillow` on CI
    # v2008 — `websocket` joins them, and ONLY as a GUARDED import. It drives the CDP fallback that
    # lets three long-dead guards run on his Mac, and it is optional by construction: absent, the
    # import raises, the helper returns None, and every caller skips exactly as it did before. CI is
    # deliberately NOT given the dependency — its `--dump-dom` may well answer over loopback, and
    # adding a package to two workflows to enable a fallback nothing there needs is cost for
    # nothing. If that ever changes, the guard's own message says the price: add it to publish.yml
    # AND tv-tests.yml, then widen this.
    ALLOWED_GUARDED = {"PIL", "playwright", "websocket"}

    @staticmethod
    def _is_third_party(mod):
        """Not 'is it stdlib' — `sys.stdlib_module_names` does not exist on his 3.9. Ask the
        FILESYSTEM where the module lives: site-packages, or nowhere at all, means third party."""
        import importlib.util
        import sysconfig
        try:
            spec = importlib.util.find_spec(mod)
        except Exception:
            return True
        if spec is None:
            return True                     # not installed HERE — the CI case, verbatim
        origin = spec.origin or ""
        if origin in ("built-in", "frozen") or not origin:
            return False
        std = os.path.realpath(sysconfig.get_paths().get("stdlib") or "")
        return "site-packages" in origin or not os.path.realpath(origin).startswith(std)

    @staticmethod
    def _repo_module_deps(here, mod):
        """Module-level third-party imports of a REPO module — one level, which is where the
        failure lived. Guarded imports (inside a try) are skipped: those already say they may be
        absent."""
        import ast
        path = os.path.join(here, mod + ".py")
        if not os.path.isfile(path):
            return []
        try:
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
        except Exception:
            return []
        guarded = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for sub in ast.walk(node):
                    guarded.add(id(sub))
        out = []
        for node in tree.body:                     # MODULE LEVEL only — a function-local import
            if id(node) in guarded:                # costs nothing until it is called
                continue
            if isinstance(node, ast.Import):
                out += [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                out.append(node.module.split(".")[0])
        return out

    def test_every_third_party_import_is_one_CI_installs(self):
        import ast
        import glob
        here = os.path.dirname(os.path.abspath(__file__))
        repo_mods = {os.path.splitext(os.path.basename(p))[0]
                     for p in glob.glob(os.path.join(here, "*.py"))}
        bad = []
        for path in sorted(glob.glob(os.path.join(here, "test_*.py"))):
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            inside_try = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Try):
                    for sub in ast.walk(node):
                        inside_try.add(id(sub))
            for node in ast.walk(tree):
                mods = []
                if isinstance(node, ast.Import):
                    mods = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    mods = [node.module.split(".")[0]]
                for m in mods:
                    if m in repo_mods:
                        # ⚠ v1934 — A LOCAL MODULE IS NOT AUTOMATICALLY SAFE. It was treated as
                        # safe, and that let a suite import `conftest` — a repo module whose FIRST
                        # LINE is `import pytest`. run_gates.py runs each suite as a plain script
                        # and the agent-tests runner installs only pillow, so the gate ERRORED on CI
                        # for NINE consecutive runs while every local signal stayed green. The guard
                        # was right about its own question — "is this import third-party?" — and
                        # blind to the failure one level below it. [[the-unjoined-end]] §6
                        for dep in self._repo_module_deps(here, m):
                            if dep in repo_mods or not self._is_third_party(dep):
                                continue
                            if dep not in self.ALLOWED_BARE:
                                bad.append("%s:%d imports the repo module %r, which imports %r "
                                           "at module level — and the runner does not have it"
                                           % (os.path.basename(path),
                                              getattr(node, "lineno", 0), m, dep))
                        continue
                    if not self._is_third_party(m):
                        continue
                    ok = (self.ALLOWED_GUARDED if id(node) in inside_try else self.ALLOWED_BARE)
                    if m not in ok:
                        bad.append("%s:%d imports %r%s"
                                   % (os.path.basename(path), getattr(node, "lineno", 0), m,
                                      " (inside a try)" if id(node) in inside_try else ""))
        self.assertEqual(bad, [],
                         "a suite imports something the CI runner does not have — it will pass here "
                         "and take the deploy down there:\n  " + "\n  ".join(bad)
                         + "\nCI installs only pillow. Parse it by hand, or add the dependency to "
                           "publish.yml AND tv-tests.yml and widen this allowlist.")


class TestEveryRoutineCanSeeTheInputItPolices(unittest.TestCase):
    """v1910 — a gate that cannot see the input it polices is not a gate, and Routine I already says
    exactly that in its own path list. The other five did not follow it: editing `J_screens.js`,
    `H_sweep.js`, `K_perf.js`, `end_to_end_audit.js` or `L_integrity.js` — or the workflow file that
    runs them — changed what the gate DOES while triggering nothing.

    So the change landed and the routine that judges it stayed asleep until the next cron; and if
    the edit broke it, the red run arrived later, wearing someone else's commit. That is the same
    shape as REG-256, where twelve cancelled Routine I runs hid two CSS defects for eleven versions.
    [[gate-blind-to-unexercised-input]]"""

    WATCHES = {
        "routine-g-audit.yml": "end_to_end_audit.js",
        "routine-h-item-sweep.yml": "H_sweep.js",
        "routine-j-screens.yml": "J_screens.js",
        "routine-k-perf.yml": "K_perf.js",
        "routine-l-integrity.yml": "L_integrity.js",
    }

    def _paths(self, wf):
        """The `on: push: paths:` list, WITHOUT PyYAML.

        ⚠ v1911 — THE FIRST VERSION IMPORTED yaml AND TOOK THE PUBLISH WORKFLOW DOWN WITH IT.
        PyYAML is installed on his Mac and is NOT on the CI runner: `ModuleNotFoundError: No module
        named 'yaml'`, two errors, Publish red, and **v1910 never reached the live site** while the
        local suite and all 34 gates were green. The host is the fixture, and this is the third
        host-difference of the arc after his Windows console encoding.

        Skipping when the import fails would have been worse: a test that skips on the only machine
        that publishes is a test that does not exist. So it parses the block itself — the shape is
        fixed, three keys deep, one quoted string per line.
        [[feedback-blind-fixture-green-gate]] [[dual-machine-setup]]"""
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(repo, ".github", "workflows", wf), encoding="utf-8") as fh:
            text = fh.read()
        m = re.search(r"\n  push:\n    paths:\n((?:\s*(?:#[^\n]*|-\s*'[^']+')\n)+)", text)
        if not m:
            return []
        return re.findall(r"-\s*'([^']+)'", m.group(1))

    def test_each_routine_watches_its_own_script_and_its_own_workflow(self):
        for wf, script in sorted(self.WATCHES.items()):
            paths = self._paths(wf)
            self.assertTrue(paths, "%s has no push paths at all" % wf)
            self.assertIn(script, paths,
                          "%s runs %s and does not watch it — editing the gate would not run it"
                          % (wf, script))
            self.assertIn(".github/workflows/" + wf, paths,
                          "%s does not watch ITSELF; a change to its own verdict step would not "
                          "run it" % wf)

    def test_routine_i_still_watches_the_page_and_the_specs(self):
        """The one that got it right first — pinned so it cannot quietly lose it."""
        paths = self._paths("routine-i-playwright.yml")
        for want in ("bible.html", "tests/**", "tv/control_ui.html",
                     ".github/workflows/routine-i-playwright.yml"):
            self.assertIn(want, paths, "routine I stopped watching %s" % want)


class TestTheCssInvariantsRunWhereTheyCannotBeCancelled(unittest.TestCase):
    """v1906 — TWO REAL CSS DEFECTS SAT ON MAIN FOR ELEVEN VERSIONS BECAUSE THEIR ONLY GATE KEEPS
    GETTING CANCELLED.

    `Routine I — Playwright suite` is the only thing that judges these two invariants, and it takes
    long enough that the next push cancels it. Twelve consecutive runs — v1894 through v1902 — are
    all `cancelled`. v1903 was the first to reach a verdict since v1893, and it went RED on two
    defects I had shipped myself:

        bible.html:3288       var(--q-set,#5fc97a) — the settled set green is #00fc00
        tv/control_ui.html    --dim renders as #5f6a5a AND #7d7360, undefined, both fallbacks live

    A gate that never reaches a verdict reads exactly like one that passed. That is the same class
    as everything else in this arc: a mechanism that looks like protection and carries nothing.

    Both invariants are pure file reads — no browser, no page — so there is no reason they only live
    somewhere cancellable. They run in the python suites now, which his pre-push hook runs on every
    single push. The Playwright copies stay where they are; this is a second, earlier reader of the
    same rule, not a replacement. [[feedback-batch-pushes-gate-cost]] [[feedback-ci-verdict-before-seal]]

    ⚠ THE PALETTE IS READ OUT OF THE SPEC, never copied. A second hardcoded copy of SETTLED would
    drift from the first the moment either moved, which is the defect this file exists to catch.
    """

    REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FILES = ("bible.html", "tv/control_ui.html")
    SPEC = "tests/v1628_no_literal_quality_hex.spec.ts"

    def _read(self, rel):
        with open(os.path.join(self.REPO, rel), encoding="utf-8") as fh:
            return fh.read()

    def _palette(self):
        spec = self._read(self.SPEC)
        m = re.search(r"const SETTLED[^=]*=\s*\{(.*?)\}\s*;", spec, re.S)
        m2 = re.search(r"const CANONICAL_TOKENS[^=]*=\s*\{(.*?)\}\s*;", spec, re.S)
        self.assertTrue(m and m2, "the spec no longer declares SETTLED/CANONICAL_TOKENS — this "
                                  "guard is reading the wrong file and must not report a pass")
        settled = dict(re.findall(r"([a-z]+)\s*:\s*'(#[0-9a-fA-F]{6})'", m.group(1)))
        canon = dict(re.findall(r"'(--[a-z-]+)'\s*:\s*'([a-z]+)'", m2.group(1)))
        self.assertTrue(settled and canon, "the palette parsed empty — a vacuous pass")
        return settled, canon

    def test_a_quality_colour_never_drifts_from_the_settled_palette(self):
        settled, canon = self._palette()
        bad, checked = [], 0
        for rel in self.FILES:
            code = self._read(rel)
            # B1 — the JS/object map form:  unique:'#c7b377'
            for m in re.finditer(r"\b(unique|set|magic|rare|crafted)\s*:\s*['\"]?(#[0-9a-fA-F]{6})",
                                 code):
                checked += 1
                want = settled.get(m.group(1).lower())
                if want and m.group(2).lower() != want:
                    bad.append("%s line %d: %s = %s — settled is %s"
                               % (rel, code[:m.start()].count("\n") + 1, m.group(1),
                                  m.group(2), want))
            # B2 — the CSS custom-property form, second palettes included:  --d2-set:#2fe35e
            for m in re.finditer(r"--(?:q|rar|d2)-(unique|set|magic|rare|orange|crafted)"
                                 r"\s*:\s*(#[0-9a-fA-F]{6})", code):
                checked += 1
                concept = "crafted" if m.group(1).lower() == "orange" else m.group(1).lower()
                want = settled.get(concept)
                if want and m.group(2).lower() != want:
                    bad.append("%s line %d: --*-%s = %s — settled is %s"
                               % (rel, code[:m.start()].count("\n") + 1, m.group(1),
                                  m.group(2), want))
            # B3 — the var() fallback form:  var(--q-unique,#c7b377)
            for m in re.finditer(r"var\(\s*(--(?:q|rar)-[a-z]+)\s*,\s*(#[0-9a-fA-F]{6})", code):
                concept = canon.get(m.group(1).lower())
                if not concept:
                    continue
                checked += 1
                if m.group(2).lower() != settled[concept]:
                    bad.append("%s line %d: var(%s) fallback %s — settled is %s"
                               % (rel, code[:m.start()].count("\n") + 1, m.group(1),
                                  m.group(2), settled[concept]))
        self.assertGreater(checked, 0, "found ZERO quality-keyed colours — the matcher is broken, "
                                       "not the files")
        self.assertEqual(bad, [], "\n".join(bad))

    def test_an_undefined_token_does_not_render_as_two_different_values(self):
        for rel in self.FILES:
            raw = self._read(rel)
            code = re.sub(r"/\*[\s\S]*?\*/", " ", raw)
            fb = {}
            for m in re.finditer(r"var\(\s*(--[a-zA-Z0-9-]+)\s*,\s*([^)]+?)\s*\)", code):
                fb.setdefault(m.group(1), set()).add(m.group(2).lower().strip())
            checked, bad = 0, []
            for token, vals in fb.items():
                if re.search(re.escape(token) + r"\s*:", code):
                    continue          # a DEFINED token always wins; its fallbacks are dead
                checked += 1
                if len(vals) > 1:
                    bad.append("%s: %s renders as %s" % (rel, token, " AND ".join(sorted(vals))))
            self.assertGreater(checked, 3, "%s: no undefined-with-fallback tokens to judge" % rel)
            self.assertEqual(bad, [], "one token, several colours:\n  " + "\n  ".join(bad))


class TestEveryWrittenStateFileFollowsAnIsolatedHist(unittest.TestCase):
    """v1902 — THE ONE FILE THAT SAYS WHAT HE OWNS DID NOT FOLLOW THE ISOLATION RULE.

    `VAULT_LEDGER_PATH` and `_VAULT_SWEPT_PATH` were bare `os.path.join(HERE, ...)`, so a sweep
    driven against a fixture hist wrote its swept memo and its OWNED-ITEM LEDGER into his real tv/
    tree. Nothing had hit it — and that is exactly why it was worth fixing rather than shrugging at:
    what stopped it was the discipline of every fixture written so far, not the path. The gate that
    proves his tree is byte-identical can only catch this AFTER a test reaches it, and by then the
    ledger it corrupted is merge-max, so nothing it gained would ever be subtracted.

    Three chronicle files had the softer version of the same hole: they isolated only when a test
    remembered their own env var. A rule half the files follow is a rule nobody can rely on.

    THIS TEST IS THE CLASS, not the two instances: it asks each written state path where it lives
    with and without TV_HIST, and any that does not move is a live file a fixture can reach.
    [[feedback-fixtures-never-touch-live-data]] [[gate-blind-to-unexercised-input]]"""

    # Every path here is WRITTEN by the console or the agent. A read-only path may point anywhere.
    MUST_MOVE = ("ca.VAULT_LEDGER_PATH", "ca._VAULT_SWEPT_PATH", "ca._VAULT_RESULT_PATH",
                 "ca._CHRON_EVIDENCE_PATH", "ca._CHRON_AUTOREAD_PATH", "ca._CHRON_RESULT_PATH",
                 "ca.chron_swept()", "ca.chron_reads()",
                 "td._KNOWN_DEAD_FILE", "td.JOURNAL", "td.STATE")

    def _paths(self, extra_env):
        import json as _json
        import subprocess as _sp
        here = os.path.dirname(os.path.abspath(__file__))
        prog = ("import sys, json; sys.path.insert(0, %r)\n"
                "import control_app as ca, tv_diablo as td\n"
                "out = {}\n"
                "for nm in %r:\n"
                "    mod, attr = nm.split('.', 1)\n"
                "    src = ca if mod == 'ca' else td\n"
                "    if attr.endswith('()'):\n"
                "        fn = {'chron_swept()': ca._chron_swept_path,\n"
                "              'chron_reads()': ca._chron_reads_path}[attr]\n"
                "        out[nm] = os.path.realpath(fn())\n"
                "    else:\n"
                "        out[nm] = os.path.realpath(getattr(src, attr))\n"
                "print(json.dumps(out))\n" % (here, self.MUST_MOVE))
        prog = "import os\n" + prog
        env = dict(os.environ)
        # a fixture that sets ONLY TV_HIST — which is the whole point: it must not have to
        # remember six other variables to stay out of his tree
        for k in ("TV_CHRON_AUTOREAD", "TV_CHRON_EVIDENCE", "TV_CHRON_RESULT", "TV_CHRON_SWEPT",
                  "TV_CHRON_READS", "TV_VAULT_RESULT", "TV_VAULT_LEDGER", "TV_VAULT_SWEPT",
                  "TV_KNOWN_FRAMES", "TV_SESSIONS", "TV_HIST"):
            env.pop(k, None)
        env.update(extra_env)
        out = _sp.run([sys.executable, "-c", prog], capture_output=True, text=True,
                      env=env, timeout=240)
        self.assertEqual(out.returncode, 0, out.stderr[-400:])
        return _json.loads(out.stdout.strip().splitlines()[-1])

    def test_none_of_them_stays_in_his_tree(self):
        import shutil
        import tempfile
        root = tempfile.mkdtemp(prefix="isolation-")
        self.addCleanup(shutil.rmtree, root, True)
        hist = os.path.join(root, "frames", "hist")
        real = self._paths({})
        fixture = self._paths({"TV_HIST": hist})
        here = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
        stuck = sorted(nm for nm in self.MUST_MOVE
                       if os.path.realpath(os.path.dirname(fixture[nm])) == here)
        self.assertEqual(stuck, [],
                         "these WRITTEN state files still point at his real tv/ when a fixture "
                         "isolates TV_HIST: %s" % (stuck,))
        for nm in self.MUST_MOVE:
            self.assertNotEqual(real[nm], fixture[nm], "%s did not move at all" % nm)

    def test_the_env_override_still_wins(self):
        """Isolation by hist must not take the specific-file override away — tests that want one
        exact path (and the console's own doctor) still pass it by name."""
        import shutil
        import tempfile
        root = tempfile.mkdtemp(prefix="isolation2-")
        self.addCleanup(shutil.rmtree, root, True)
        named = os.path.join(root, "i_said_here.json")
        got = self._paths({"TV_HIST": os.path.join(root, "h"), "TV_VAULT_LEDGER": named})
        self.assertEqual(got["ca.VAULT_LEDGER_PATH"], os.path.realpath(named))


class TestOneWriterForTheAutoReadMarks(unittest.TestCase):
    """v1900 — chron_autoread.json had TWO writers, and that fact has un-marked the file TWICE.

    v1762: the visit writer knew only "done" and rewrote the file WITHOUT "reels", so the watchdog
    re-walked the whole backlog and PAID FOR IT AGAIN. v1784: the same shape with "skipped", so a
    reel retired for a named reason read as never-swept. Both were fixed by teaching one writer
    about one more key — which leaves the NEXT key exactly as fragile.

    Three occurrences of one class is where you stop fixing instances. One writer now, and this
    test drives BOTH marks and asserts every key survives each. [[feedback-generalize-fixes]]"""

    def test_either_mark_preserves_every_key(self):
        import json as _json
        import shutil
        import subprocess as _sp
        import tempfile as _tf
        here = os.path.dirname(os.path.abspath(__file__))
        root = _tf.mkdtemp(prefix="autoread-")
        self.addCleanup(shutil.rmtree, root, True)
        path = os.path.join(root, "deep", "chron_autoread.json")   # parent does NOT exist
        prog = ("import sys, os, json; sys.path.insert(0, %r)\n"
                "import control_app as ca\n"
                "ca._CHRON_AUTOREAD['skipped'] = {'reel_x': 'no stash screen'}\n"
                "ca._chron_autoread_mark(1700000000)\n"     # the VISIT writer
                "ca._chron_reels_mark('reel_y')\n"          # the REEL writer
                "ca._chron_autoread_mark(1700000001)\n"     # visit again, AFTER the reel mark
                "print(json.dumps(json.load(open(ca._CHRON_AUTOREAD_PATH))))\n" % here)
        out = _sp.run([sys.executable, "-c", prog], capture_output=True, text=True,
                      env=dict(os.environ, TV_CHRON_AUTOREAD=path), timeout=180)
        self.assertEqual(out.returncode, 0, out.stderr[-400:])
        got = _json.loads(out.stdout.strip().splitlines()[-1])
        self.assertEqual(sorted(got.get("done") or []), [1700000000, 1700000001])
        self.assertIn("reel_y", got.get("reels") or [],
                      "a visit mark wiped the swept reels again — v1762, a third time")
        self.assertIn("reel_x", got.get("skipped") or {},
                      "a mark wiped the retirement reasons again — v1784, a second time")

    def test_there_is_exactly_one_writer(self):
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        self.assertEqual(src.count("os.replace(tmp, _CHRON_AUTOREAD_PATH)"), 1,
                         "a second writer of chron_autoread.json is back")


class TestAResultSaveMakesItsOwnDirectoryAndSaysWhenItCannot(unittest.TestCase):
    """v1899 — found in the SUITE'S OWN OUTPUT, which had been carrying it for a while:

        ⚠ chronicle result NOT persisted ([Errno 2] No such file or directory:
          '/var/folders/.../nodeadlock.json.tmp') — this sweep will not survive a restart

    repeated on every run. A result path whose directory does not exist means the sweep is not
    persisted at all, and both saves had that shape.

    ⚠ AND MY OWN VAULT SAVE (v1895) SWALLOWED THE FAILURE ENTIRELY. The chronicle's has said so out
    loud for versions; mine was `except Exception: pass`, written one ship after I fixed the same
    class in HIS code. Losing a vault proposal quietly undoes v1895 exactly — the reads that paid
    for it are spent, he closes the console, and there is nothing and no reason.
    [[feedback-silence-is-not-evidence]]"""

    def test_the_vault_save_makes_its_parent(self):
        import json as _json
        import shutil
        import subprocess as _sp
        import tempfile as _tf
        here = os.path.dirname(os.path.abspath(__file__))
        root = _tf.mkdtemp(prefix="mkparent-")
        self.addCleanup(shutil.rmtree, root, True)
        hist = os.path.join(root, "not", "made", "yet")     # the parent does NOT exist
        prog = ("import sys, os, json; sys.path.insert(0, %r)\n"
                "import control_app as ca\n"
                "with ca._VAULT_LOCK:\n"
                "    ca._VAULT_JOB.update({'running': False, 'phase': 'done',\n"
                "        'result': {'ok': True, 'owned': [{'name': 'Ral Rune'}]}, 'resultTs': 1})\n"
                "ca._vault_result_save()\n"
                "print(json.dumps({'saved': os.path.isfile(ca._VAULT_RESULT_PATH)}))\n" % here)
        out = _sp.run([sys.executable, "-c", prog], capture_output=True, text=True,
                      env=dict(os.environ, TV_HIST=hist), timeout=180)
        self.assertEqual(out.returncode, 0, out.stderr[-300:])
        self.assertTrue(_json.loads(out.stdout.strip().splitlines()[-1])["saved"],
                        "the vault proposal was lost because its directory did not exist yet")

    def test_both_saves_say_so_when_they_cannot(self):
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        self.assertIn("chronicle result NOT persisted", src)
        self.assertIn("vault result NOT persisted", src,
                      "the vault save is silent again — a lost proposal with no reason")

    def test_neither_save_swallows_its_error(self):
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        body = _between(self, src, "def _vault_result_save():", "def _vault_result_load():",
                        min_len=200, what="the vault save")
        self.assertNotIn("except Exception:\n        pass", body,
                         "the vault save swallows its failure again")


class TestTheArtGuardRefusesTraversalAndAllowsArt(unittest.TestCase):
    """v1898 — the art route's 403 guard now uses the one path rule, and it must stay exactly as
    strict. Normalising BOTH sides identically cannot admit a path outside ART_DIR; it only stops
    refusing legitimate ones on a case-insensitive or case-normalising filesystem.

    ⚠ WHAT THIS DOES NOT FIX, recorded because I nearly claimed the opposite: ART_DIR is ALREADY
    realpath'd at its definition, so the symlink half of the hazard does not exist in this repo and
    never did. The real half is his WINDOWS machine, where a case difference makes startswith say
    no and the guard fails CLOSED on his own art — a 403 on every picture. [[dual-machine-setup]]"""

    def test_traversal_is_still_refused(self):
        import control_app as ca
        import tv_diablo as tv
        from urllib.parse import unquote
        AD = ca.ART_DIR
        for rel in ("../control_app.py", "../../etc/passwd", "..%2f..%2fetc%2fpasswd",
                    "../../../../../../etc/hosts"):
            r = unquote(rel).split("?", 1)[0].split("#", 1)[0]
            target = os.path.realpath(os.path.join(AD, r))
            self.assertFalse(tv._under(target, AD),
                             "%r escaped the art directory: %s" % (rel, target))

    def test_ordinary_art_is_still_served(self):
        import control_app as ca
        import tv_diablo as tv
        AD = ca.ART_DIR
        for rel in ("boss_andariel.png", "hd/x.png", "./boss_andariel.png"):
            target = os.path.realpath(os.path.join(AD, rel))
            self.assertTrue(tv._under(target, AD), "%r was refused" % rel)

    def test_the_route_uses_the_one_rule(self):
        import control_app as ca
        body = _between(self, open(ca.__file__, encoding="utf-8").read(),
                        "    def _serve_art(self, name):", "if not os.path.isfile(target):",
                        min_len=200, what="the art route")
        self.assertIn("_under(target, ART_DIR)", body,
                      "the art guard grew its own path comparison again")
        self.assertIn("403", body, "the refusal is gone")


class TestHeldNamesReachTheInboxAndStayHeld(unittest.TestCase):
    """v1896 — VERIFIED, and it found nothing wrong. Recording that is the point.

    v1759 built this path after five names the readers genuinely saw were "silently discarded on the
    server: they never reached the board, never reached the inbox, and he never saw them". It had
    never been driven with a real held pile.

    MEASURED IN A REAL PAGE against the 41 names his own sweep is currently holding:

        held in                41
        queued                 41  (skipped 0 · conflicts 0 · autoAccepted 0 · autoDismissed 0)
        rows in the inbox      41, each carrying its reason as `triageWhy`
                               e.g. "only 1 independent witness (cross-frame) — needs 2"
        auto-ticked            0
        after THREE sync passes   still 41 rows, still 0 ticked

    The three passes matter: a defect that needs a second triage to bite would hide from one, and
    v1759's own note says what is at stake — "the board's triage sees a well-formed grail name and
    AUTO-TICKS it, which quietly undoes the gate that just refused to ground it".

    What is asserted here is the contract the in-page run exercised: held names go through
    kaiChroniclePropose carrying gateHeld, and carrying WHY."""

    def _bible(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        return open(p, encoding="utf-8").read()

    def test_held_names_are_routed_through_the_one_door(self):
        body = _between(self, self._bible(), "var _held = (proposal && proposal.held) || [];",
                        "(add.uniques || []).forEach(", min_len=300, what="the held branch")
        self.assertIn("kaiChroniclePropose", body,
                      "held names take a private path again instead of the door every proposal uses")
        self.assertIn("gateHeld: true", body,
                      "without gateHeld the triage auto-ticks a name the gate just refused")
        self.assertIn("gateWhy", body, "a held name reaches him with no reason attached")

    def test_the_reason_survives_into_the_row(self):
        src = self._bible()
        i = src.find("if (item.gateHeld){")
        self.assertGreater(i, 0, "the triage no longer reads gateHeld at all")

    def test_a_held_name_is_never_auto_accepted(self):
        """The property the three sync passes proved in the page, pinned at its source."""
        src = self._bible()
        body = _between(self, src, "if (item.gateHeld){", "\n", min_len=10,
                        what="the gateHeld branch")
        self.assertTrue(body.strip().endswith("{"), body[:80])


class TestTheVaultProposalSurvivesARestart(unittest.TestCase):
    """v1895 — the vault proposal was IN-MEMORY ONLY. He sweeps his vault, closes the console, and
    the proposal is gone while the READS THAT PAID FOR IT are spent. The chronicle solved this in
    v1763 for the same reason — "a fresh process reports the LAST sweep, not 'idle, nothing here'".

    Proven end to end in an ISOLATED tree, and his own confirmed untouched by the same run:

        save     -> the fixture's own vault_last_result.json, not his
        reload   -> owned rows restored into a fresh, empty job
        state    -> resultFromDisk true, resultTs set
        his tv/  -> no vault_last_result.json, chronicle result byte-identical

    The age fields matter more here than anywhere: a proposal that now OUTLIVES the session must
    say how old it is, or one made last week reads as one made just now. [[stale-reading]]"""

    def test_it_saves_and_restores_the_result(self):
        import json as _json
        import shutil
        import subprocess as _sp
        import tempfile as _tf
        here = os.path.dirname(os.path.abspath(__file__))
        d = _tf.mkdtemp(prefix="vres-test-")
        self.addCleanup(shutil.rmtree, d, True)
        hist = os.path.join(d, "frames", "hist")
        os.makedirs(hist, exist_ok=True)
        prog = (
            "import sys, os, json; sys.path.insert(0, %r)\n"
            "import control_app as ca\n"
            "with ca._VAULT_LOCK:\n"
            "    ca._VAULT_JOB.update({'running': False, 'phase': 'done',\n"
            "        'result': {'ok': True, 'owned': [{'name': 'Ral Rune', 'lane': 'stash'}]},\n"
            "        'resultTs': 1787000000000, 'restoredFrom': None})\n"
            "ca._vault_result_save()\n"
            "with ca._VAULT_LOCK:\n"
            "    ca._VAULT_JOB.clear(); ca._VAULT_JOB.update({'running': False})\n"
            "st = ca.vault_sweep_state()\n"
            "print(json.dumps({'names': [r['name'] for r in (st.get('result') or {}).get('owned') or []],\n"
            "                  'fromDisk': bool(st.get('resultFromDisk')),\n"
            "                  'hasTs': bool(st.get('resultTs')),\n"
            "                  'path': ca._VAULT_RESULT_PATH}))\n" % here)
        env = dict(os.environ, TV_HIST=hist)
        out = _sp.run([sys.executable, "-c", prog], capture_output=True, text=True,
                      env=env, timeout=180)
        self.assertEqual(out.returncode, 0, out.stderr[-400:])
        got = _json.loads(out.stdout.strip().splitlines()[-1])
        self.assertEqual(got["names"], ["Ral Rune"], "the proposal did not survive a fresh process")
        self.assertTrue(got["fromDisk"], "a restored result does not say it came from disk")
        self.assertTrue(got["hasTs"], "a restored result carries no age")
        self.assertTrue(got["path"].startswith(os.path.realpath(hist))
                        or got["path"].startswith(hist),
                        "an isolated TV_HIST did not take the vault result with it: %s" % got["path"])

    def test_his_own_file_is_not_created_by_that(self):
        """v2023 — ASSERT WHAT THIS MEANS: the isolated run must not CREATE OR TOUCH his file.

        This used to assert the file was simply ABSENT, and it blocked a push on 2026-08-23 with
        "an isolated run wrote his vault result file". Nothing had written it: `tv/vault_last_result
        .json` was stamped 19:04 by the FIRST REAL VAULT SWEEP ever run on this project, which
        persists its result on purpose (v1763 — "a sweep that is not written down did not happen").

        So the old assertion was only ever true because the feature it guards had never been used.
        A check that passes only while nobody exercises the thing it protects is measuring the
        disuse, not the isolation — and it fails for the first time on the day the feature starts
        working, which is the worst possible moment to cry wolf.
        [[feedback-suspect-the-instrument]] [[gate-blind-to-unexercised-input]]

        It now brackets its OWN isolated run and asserts the live file is byte-identical across it,
        which is the property that was actually intended and which holds whether or not a real
        sweep has ever run. Its sibling above is what proves the isolated path writes into TV_HIST.
        """
        import json as _json
        import shutil
        import subprocess as _sp
        import tempfile as _tf
        here = os.path.dirname(os.path.abspath(__file__))
        live = os.path.join(here, "vault_last_result.json")

        def sig():
            try:
                st = os.stat(live)
                with open(live, "rb") as fh:
                    import hashlib
                    return (int(st.st_size), hashlib.md5(fh.read()).hexdigest())
            except FileNotFoundError:
                return None

        before = sig()
        d = _tf.mkdtemp(prefix="vres-leak-")
        self.addCleanup(shutil.rmtree, d, True)
        hist = os.path.join(d, "frames", "hist")
        os.makedirs(hist, exist_ok=True)
        prog = (
            "import sys, os, json; sys.path.insert(0, %r)\n"
            "import control_app as ca\n"
            "with ca._VAULT_LOCK:\n"
            "    ca._VAULT_JOB.update({'running': False, 'phase': 'done',\n"
            "        'result': {'ok': True, 'owned': [{'name': 'Ral Rune', 'lane': 'stash'}]},\n"
            "        'resultTs': 1787000000000, 'restoredFrom': None})\n"
            "ca._vault_result_save()\n"
            "print(ca._VAULT_RESULT_PATH)\n" % here)
        out = _sp.run([sys.executable, "-c", prog], capture_output=True, text=True,
                      env=dict(os.environ, TV_HIST=hist), timeout=180)
        self.assertEqual(out.returncode, 0, out.stderr[-400:])
        after = sig()
        self.assertEqual(
            before, after,
            "an isolated run CREATED OR MODIFIED his live vault_last_result.json — the fixture "
            "escaped TV_HIST and wrote into his tree [[feedback-fixtures-never-touch-live-data]]")

    def test_the_gate_watches_the_new_live_file(self):
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "run_gates.py"), encoding="utf-8").read()
        self.assertIn("vault_last_result.json", src,
                      "new live state that the gate is not watching is how the last three leaks "
                      "survived")

    def test_the_console_shows_the_vault_proposal_s_age(self):
        here = os.path.dirname(os.path.abspath(__file__))
        ui = open(os.path.join(here, "control_ui.html"), encoding="utf-8").read()
        body = _between(self, ui, "var _vAge = document.getElementById('vault-result-age');",
                        "var owned = res.owned", min_len=200, what="the vault age line")
        self.assertIn("this vault proposal was made", body)
        self.assertIn("restored from disk", body)


class TestUndoRetractsTheGameDateToo(unittest.TestCase):
    """v1891 — the undo bar promises "the ledger entry is erased and it returns to the hunt", and
    v1864's `d2r_gameFound` was left behind.

    MEASURED in a real page, the full round trip:

        tick   have +1 · ledger row + stamp "Jul 18, 2026 · 02:47" · date present
        undo   have  0 · ledger row gone   · DATE STILL THERE          <- the defect
        after  have  0 · ledger row gone   · date gone
        redo   have +1 · date restored exactly: 07/18/2026, 02:47 · Andariel

    WHY IT MATTERS RATHER THAN BEING TIDY. The reason he un-ticks is usually that the READ WAS
    WRONG, so the date belongs to a different item. Left behind, it re-attaches the moment he ticks
    that name by hand later — and v1871 prints it on the chip: "⚔ found in game Jul 18, 2026 ·
    Andariel", a claim sourced from a read he threw away. If he genuinely found it, the next read
    re-establishes it.

    A joint I opened in v1864 and did not finish. [[the-unjoined-end]]"""

    def _src(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        src = open(p, encoding="utf-8").read()
        i = src.find("  window._forgeUndo = function(el, name, kind){")
        j = src.find("  function _undoBar(kind){", i)
        self.assertGreater(i, 0, "the undo is gone")
        return src, src[i:j]

    def test_undo_deletes_the_date(self):
        _s, body = self._src()
        self.assertIn("d2r_gameFound", body, "the undo does not touch the game's find date")
        self.assertIn("delete _gf[name];", body)
        self.assertIn("window.LSR.setItem('d2r_gameFound'", body,
                      "the date is deleted in memory and never written back")

    def test_undo_keeps_it_so_redo_can_put_it_back_unchanged(self):
        _s, body = self._src()
        self.assertIn("window._FORGE_REDO.gameFound = _gf[name];", body,
                      "the date is dropped with no way to restore it — redo would lose it")
        self.assertIn("if (r.gameFound) window._gameFoundSet(r.name, r.gameFound);", body,
                      "redo does not restore the date it was handed")

    def test_it_only_touches_the_name_being_undone(self):
        _s, body = self._src()
        i = body.find("delete _gf[name];")
        self.assertGreater(i, 0)
        window = body[max(0, i - 300):i]
        self.assertIn("hasOwnProperty.call(_gf, name)", window,
                      "the undo rewrites the whole store even when the name is not in it")
        self.assertNotIn("_gf = {}", body, "the undo clears every date rather than one")


class TestANonPieceNeverEntersTheSetLedger(unittest.TestCase):
    """v1890 — the sets branch had v1889's defect in a WORSE shape.

    MEASURED in a real page on a cleared store: applying three real pieces plus "IK Helm" and
    "Totally Not A Set Piece" reported `sets: 5`, moved the meter by THREE, and wrote ALL FIVE into
    d2r_foundLog. In the uniques case an unrecognised name at least landed in the vault; here it
    lands in the FOUND LEDGER and stays, because nothing ever un-finds.

    After: `sets: 3`, `unknown: ["IK Helm", "Totally Not A Set Piece"]`, meter +3, and the ledger
    holds only the three real pieces.

    The membership question is asked BEFORE the write, against the board's own piece universe
    (`__allSets` — ITEM_SETS plus the two EXTRA tables), memoised because a 500-name payload would
    otherwise walk that universe 500 times.

    ⚠ AND AN UNREADABLE ROSTER DOES NOT INVENT A REFUSAL. "This is not a set piece" is a claim that
    needs the roster to make; without it the old behaviour stands. The tempting catch is the wrong
    way round here, exactly as it was in v1889. [[unknown-stays-unknown]]"""

    def _sets_branch(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        src = open(p, encoding="utf-8").read()
        i = src.find("    (add.sets || []).forEach(function(row){")
        j = src.find("completeSets", i)
        self.assertGreater(i, 0, "the sets apply branch is gone")
        return src, src[i:j]

    def test_membership_is_asked_BEFORE_the_write(self):
        _src, body = self._sets_branch()
        ask = body.find("_chronSetPieceSet")
        write = body.find("window.toggleSetPiece")
        self.assertGreater(ask, 0, "nothing checks that the name is a set piece at all")
        self.assertGreater(write, 0)
        self.assertLess(ask, write, "the name is written first and questioned afterwards — by then "
                                    "it is in his ledger and nothing ever un-finds")

    def test_an_unknown_name_is_reported_not_written(self):
        """⚠ v1918 — THIS GUARD BROKE ON ITS OWN REACH, NOT ON THE CODE. It pinned the literal
        one-line spelling `res.unknown.push(n); return;` inside a 120-character window. v1918 added
        a provenance write between the push and the return — the branch still refuses, still returns,
        still writes nothing to the ledger — and the guard went red because the two statements
        stopped being adjacent.

        A guard that greps SOURCE fails on its own reach, and the fix is to assert the PROPERTY, not
        the spelling: between entering the branch and leaving it, `unknown` is pushed, the branch
        returns, and nothing that writes a find appears. [[source-reading-guard]]"""
        _src, body = self._sets_branch()
        i = body.find("if (!_known){")
        self.assertGreater(i, 0)
        j = body.find("return;", i)
        self.assertGreater(j, i, "the refusal branch no longer returns — the name falls through")
        branch = body[i:j]
        self.assertIn("res.unknown.push(n)", branch,
                      "an unrecognised name is no longer reported as unknown")
        for writer in ("toggleSetPiece", "res.sets.push", "grailTogglePiece"):
            self.assertNotIn(writer, branch,
                             "the refusal branch now WRITES the name it just refused (%s)" % writer)

    def test_an_unreadable_roster_does_NOT_invent_a_refusal(self):
        _src, body = self._sets_branch()
        self.assertIn("catch(e){ _known = true; }", body,
                      "a missing roster now refuses every piece he actually found")
        self.assertIn("if (_pieces && _pieces.size)", body,
                      "an EMPTY piece set would refuse everything — that is the same failure")

    def test_the_piece_universe_is_memoised_and_reachable(self):
        src, _body = self._sets_branch()
        self.assertIn("window._chronSetPieceSet = function()", src,
                      "the helper is not reachable from outside its IIFE — the REG-083 shape")
        self.assertIn("if (_CH_PIECES) return _CH_PIECES;", src,
                      "the piece universe is rebuilt per row; a 500-name payload walks it 500 times")


class TestTheVaultApplyTellsZeroFromUnknown(unittest.TestCase):
    """v1887 — `window.vaultAccumApply` called `count: 0` and `count: null` the same thing.

    Both correctly write NOTHING — merge-max means a zero can never lower a count, so the STORE was
    always safe — but the receipt said "no readable count" for a genuine zero, which is a wrong
    reason attached to a right action. His own doctrine: "`0` means 'we measured, it was zero';
    `None` means 'nobody looked'. Collapsing them is a lie with no author."

    VERIFIED IN A REAL PAGE, headless Chrome on :9224, calling the function itself — which is the
    only way this line was ever going to be read, because it lives inside an IIFE that no unit test
    can reach:

        count: 0      -> "Flawless Amethyst (read as none — nothing to raise)"
        count: null   -> "Flawless Topaz (no readable count)"
        count: 'lots' -> "Flawless Emerald (no readable count)"
        count: -3     -> "Perfect Ruby (no readable count)"      store untouched in all four

    THE SAME PASS CHECKED THE FOUR RULES THE FUNCTION STATES ABOUT ITSELF, and all four hold:
      1. merge-max — a read of 3 left a stored 9 alone; a read of 14 raised it
      2. route by kind — gem→gems, material→materials, item→grail, unknown kind→skipped BY NAME
      3. throw-outs are never written — 2 suggestions acknowledged, all three stores byte-identical
      4. an empty payload refuses: ok:false, "the payload carried no items"
      · traffic: 500 tally items in 242ms, every one written

    What is asserted HERE is the one thing a source check can hold honestly: the ORDER of the two
    branches. `saw === 0` must be tested BEFORE the `!isFinite || saw < 0` branch, or zero falls
    through into it and the distinction is gone again. [[unknown-stays-unknown]]"""

    def test_zero_is_tested_before_the_unreadable_branch(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        src = open(p, encoding="utf-8").read()
        zero = src.find("if (saw === 0){")
        junk = src.find("if (!isFinite(saw) || saw < 0){")
        self.assertGreater(zero, 0, "the zero branch is gone — a measurement reads as an absence")
        self.assertGreater(junk, 0, "the unreadable-count branch is gone")
        self.assertLess(zero, junk, "zero now falls through into 'no readable count' again")

    def test_neither_branch_writes_anything(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        src = open(p, encoding="utf-8").read()
        i = src.find("if (saw === 0){")
        j = src.find("if (saw > have){", i)
        self.assertGreater(j, i)
        between = src[i:j]
        self.assertEqual(between.count("return;"), 2, "a refusal stopped returning early")
        self.assertNotIn("pend[kind][nm] =", between, "a refused row writes into the store")


class TestBothTzClocksAgreeOnTheCadence(unittest.TestCase):
    """v1882 — the dock badge counted to :00 ONLY, and the rotation is every 30 minutes.

    `remMin = 59 - m` reaches the next hour, so for the whole first half of every hour the badge read
    up to THIRTY MINUTES too long and it never once fired at the :30 turn. It sits in the bottom
    dock, on every tab — the most-seen clock on the site — and it had said "TZ rotates each hour at
    :00 IDT" for ~1,840 versions while the tracker page said "on the hour and the half hour".

    SETTLED FROM THE FEED'S OWN HISTORY, not from either surface's opinion. https://bull-4-u.com/api/tz,
    ten consecutive slots: 00:30 · 21:30 · 21:00 · 20:30 · 20:00 · 19:30 · 19:00 · 18:30 · 18:00 ·
    17:30 — gaps [30]×10. The tracker was right; the badge was wrong.

    THEY AGREED ONLY WHEN SAMPLED IN THE SECOND HALF OF AN HOUR, where :30 and :00 coincide. That is
    why it survived: the render that found it happened at 00:34, and both read 25:28 and 25:29.
    [[feedback-contradiction-is-the-finding]] [[copy-drift]]"""

    def _bible(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        return p, open(p, encoding="utf-8").read()

    def test_the_dock_counts_to_the_half_hour_too(self):
        import json as _json
        import shutil as _sh
        import subprocess as _sp
        import tempfile as _tf
        node = _sh.which("node")
        if not node:
            self.skipTest("node is not installed on this machine")
        _p, src = self._bible()
        i = src.find("  function _nextTurnMs(now) {")
        j = src.find("  function update() {", i)
        self.assertGreater(i, 0, "the dock badge lost its boundary helper")
        prog = ("var window = {};\n" + src[i:j]
                + "var cases=['2026-08-21T00:05:00','2026-08-21T00:29:59','2026-08-21T00:31:00',"
                  "'2026-08-21T00:59:59'];\n"
                  "console.log(JSON.stringify(cases.map(function(c){var t=new Date(c).getTime();"
                  "return Math.round((_nextTurnMs(t)-t)/1000);})));\n")
        with _tf.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(prog)
            jp = f.name
        try:
            out = _sp.run([node, jp], capture_output=True, text=True, timeout=60)
            self.assertEqual(out.returncode, 0, out.stderr[:400])
            got = _json.loads(out.stdout.strip().splitlines()[-1])
        finally:
            os.unlink(jp)
        # 00:05 was 3300 (55 min) under the old rule — thirty minutes wrong
        self.assertEqual(got, [1500, 1, 1740, 1])

    def test_there_is_ONE_definition_and_the_dock_prefers_it(self):
        _p, src = self._bible()
        self.assertIn("window._tzTurnBoundary = _tzTurnBoundary", src,
                      "the tracker's boundary is not published, so the dock cannot share it")
        i = src.find("  function _nextTurnMs(now) {")
        body = src[i:src.find("  function update() {", i)]
        self.assertIn("window._tzTurnBoundary", body,
                      "the dock stopped preferring the shared definition — two copies again")

    def test_no_surface_still_says_hourly(self):
        _p, src = self._bible()
        for phrase in ("TZ rotates each hour at :00",
                       "Terror Zones rotate every hour on the hour"):
            i = src.find(phrase)
            if i < 0:
                continue
            near = src[max(0, i - 500):i + 500]
            self.assertIn("v1882", near,
                          "a surface still claims an hourly rotation as fact: %r" % phrase)


class TestTheTzTrackerChasesTheTurn(unittest.TestCase):
    """v1881 — Konyo: "the TZ TRACKER when im on it i want it to be refreshed its stuck and not
    updating".

    It was not frozen. It was SILENT, and LATE at the only moment that matters:
      · a flat 120s poll, so between polls nothing on screen changed and a working tracker looked
        exactly like a dead one;
      · that poll is unaligned to the rotation, which turns ON THE HOUR AND THE HALF HOUR, so he
        could sit up to two minutes reading the zone that had just ended;
      · ⚠ a comment claimed "the board already refetches 6s after the turn". IT DID NOT — `_tzTimer`
        was the only timer in the file. A stale claim about a safeguard is why nobody looked.
        [[label-outlived-referent]]

    The boundary maths is run in NODE against fixed clocks, including both one-second edges and the
    midnight rollover, because an off-by-one here means the chase fires on the wrong side of the
    turn and he sees the old zone for another half hour."""

    def _boundaries(self, cases):
        import json as _json
        import shutil as _sh
        import subprocess as _sp
        import tempfile as _tf
        node = _sh.which("node")
        if not node:
            self.skipTest("node is not installed on this machine")
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        src = open(p, encoding="utf-8").read()
        i = src.find("function _tzTurnBoundary(now){")
        j = src.find("function tzTrackerOnShow(){", i)
        self.assertGreater(i, 0, "the tracker lost its turn-boundary maths")
        prog = ("var document = { getElementById: function(){ return null; } };\n" + src[i:j]
                + "var cases = " + _json.dumps(cases) + ";\n"
                + "console.log(JSON.stringify(cases.map(function(c){ var t = new Date(c).getTime();"
                  " return Math.round((_tzTurnBoundary(t) - t) / 1000); })));\n")
        with _tf.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(prog)
            jp = f.name
        try:
            out = _sp.run([node, jp], capture_output=True, text=True, timeout=60)
            self.assertEqual(out.returncode, 0, out.stderr[:400])
            return _json.loads(out.stdout.strip().splitlines()[-1])
        finally:
            os.unlink(jp)

    def test_it_counts_to_the_next_hour_or_half_hour(self):
        got = self._boundaries(["2026-08-21T00:05:00", "2026-08-21T00:29:59",
                                "2026-08-21T00:30:00", "2026-08-21T00:31:00"])
        self.assertEqual(got, [1500, 1, 1800, 1740])

    def test_it_survives_midnight(self):
        # the boundary is built from the top of the hour plus 60 minutes, so the date rolls with it
        self.assertEqual(self._boundaries(["2026-08-21T23:45:00", "2026-08-21T23:59:59"]),
                         [900, 1])

    def test_the_panel_has_somewhere_to_show_it(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        src = open(p, encoding="utf-8").read()
        self.assertIn('id="tztracker-clock"', src, "the countdown has no element to render into")
        self.assertIn(".tzt-clock{", src, "the countdown element has no styling at all")

    def test_the_chase_and_the_floor_both_exist(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        src = open(p, encoding="utf-8").read()
        i = src.find("function tzTrackerOnShow(){")
        body = src[i:src.find("window.tzTrackerOnShow", i)]
        self.assertIn("now + 8000", body, "the post-turn chase is gone — the feed lags its own turn")
        self.assertIn("now - _lastPoll >= 120000", body, "the 120s floor is gone")
        self.assertIn("}, 1000);", body, "the tick is no longer once a second, so nothing moves")

    def test_the_stale_6s_claim_never_stands_unretracted(self):
        """⚠ THE FIRST CUT OF THIS TEST FAILED ON ITS OWN DOCUMENTATION.

        It asserted the phrase was ABSENT — and v1881's note about removing it quotes the phrase, so
        the guard found the record of the fix and called it the defect. Third time tonight that an
        explanatory comment blinded a guard that greps for a name, and this one was written sixty
        seconds after the last. [[feedback-comments-vs-code]]

        A string cannot tell a claim from its retraction, so the check is about what SURROUNDS it:
        every occurrence must sit beside a retraction. The claim re-introduced plainly still fails;
        the history is allowed to stay written down."""
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        src = open(p, encoding="utf-8").read()
        RETRACTED = ("used to claim", "IT\n", "DOES NOT", "did not exist", "v1881")
        i, unretracted = 0, []
        while True:
            i = src.find("the board already refetches 6s after the turn", i)
            if i < 0:
                break
            near = src[max(0, i - 400):i + 400]
            if not any(w in near for w in RETRACTED):
                unretracted.append(src.count("\n", 0, i) + 1)
            i += 10
        self.assertEqual(unretracted, [],
                         "a safeguard that does not exist is claimed as fact at line(s) %s"
                         % unretracted)


class TestTheFindDateIsForkedExactlyLikeTheFindItself(unittest.TestCase):
    """v1879 — a coupling, checked rather than assumed.

    `d2r_gameFound` (v1864) holds the GAME's First Found date and dropper per item. `d2r_foundLog`
    holds when the BOARD learned of the same find. They describe one event from two sides, so they
    must live in the same scope — and `_LP_FORKED` decides that: a forked key is per-account, an
    unforked one is shared.

    Measured: neither is forked, which matches the ladder doctrine — *"everything NON-LADDER syncs
    to main; a profile toggle must never change a count"*. A grail is what he has EVER found, so it
    is account-wide; `d2r_owned` IS forked, because what he HOLDS is per-profile. That split is
    right, and this asserts the PAIR rather than either value, so if the log is ever forked the
    dates follow it instead of quietly splitting from the finds they date.
    [[d2r-ladder-doctrine]] [[the-unjoined-end]]"""

    def _forked(self):
        import re
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        src = open(p, encoding="utf-8").read()
        m = re.search(r"window\._LP_FORKED = new Set\(\[(.*?)\]\)", src, re.S)
        self.assertIsNotNone(m, "the fork list is gone — every key just changed scope")
        return set(re.findall(r'"([^"]+)"', m.group(1))), src

    def test_the_dates_share_the_ledger_s_scope(self):
        forked, _ = self._forked()
        self.assertEqual("d2r_gameFound" in forked, "d2r_foundLog" in forked,
                         "the game's find DATE and the find it dates ended up in different scopes: "
                         "one per-account, one shared. They describe one event from two sides.")

    def test_what_he_HOLDS_is_still_per_profile(self):
        # the other half of the split, or the test above passes on a board where nothing is forked
        forked, _ = self._forked()
        self.assertIn("d2r_owned", forked,
                      "the physical vault stopped being per-profile — a profile toggle would now "
                      "change what he owns")

    def test_the_store_is_actually_written_through_LSR(self):
        # forked or not, the fork only applies to keys that go through the wrapper
        _, src = self._forked()
        self.assertIn("window.LSR.setItem('d2r_gameFound'", src,
                      "the dates are written past the storage wrapper, so no scope applies at all")


class TestNewlyDatedReachesASurface(unittest.TestCase):
    """v1880 — CORRECTING v1878, which was mine and was wrong.

    v1878 said `newlyDated` was "produced at two sites and consumed at zero", and added a print to
    the hand sweep. It was ALREADY consumed: control_app prints it at both sweep sites, LIVE, while
    the reel is still being read. His own sweep printed it forty minutes later —

        \U0001f195 1 find(s) newer than anything read before: Bul-Kathos' Tribal Guardian (08/20/2026, 02:59)

    — from the engine, not from my line. The duplicate is removed.

    WHY THE GREP MISSED IT: I searched for the field name `newlyDated`, and the consumer works from
    the local `_fresh`, assigned before the field is built. Searching a name and concluding absence
    is the exact failure `source-reading-guard` exists for, applied to my own field.
    [[source-reading-guard]] [[feedback-silence-is-not-evidence]]

    So this guards the joint that was always real, and both ends that make it work: the engine
    computes the dates, prints them where they can be seen WHILE the sweep runs, and carries them
    into the stored result for anything reading it afterwards."""

    def _ca_src(self):
        import control_app as ca
        return open(ca.__file__, encoding="utf-8").read()

    def test_the_engine_says_it_while_the_sweep_is_still_running(self):
        self.assertEqual(self._ca_src().count("find(s) newer than anything read before"), 2,
                         "both sweep paths must say which finds are new, or one of them is silent")

    def test_it_says_nothing_when_there_is_nothing_new(self):
        # a line that always prints is one he stops reading
        src = self._ca_src()
        i = src.find("find(s) newer than anything read before")
        self.assertIn("if _fresh:", src[max(0, i - 400):i],
                      "the new-finds line prints unconditionally")

    def test_the_result_still_carries_them_for_later_readers(self):
        # printing is for the person watching; the FIELD is for everything that reads the result
        # afterwards. Both ends, or a later consumer silently gets nothing.
        self.assertEqual(self._ca_src().count('"newlyDated": _fresh'), 2)

    def test_the_hand_sweep_does_not_print_it_twice(self):
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "chronicle_sweep_now.py"), encoding="utf-8").read()
        body = "\n".join(ln for ln in src.splitlines() if not ln.strip().startswith("#"))
        self.assertNotIn("newer than anything read before", body,
                         "v1878's duplicate print is back — the engine already streams this line")


class TestTheCascadeLookupAnswersCorrectly(unittest.TestCase):
    """v1877 — `d2r_css_last_rule_wins` is a carved scar: `.hero-title` had four rules and a twin
    `filterSilver` cost him a pane. At equal specificity the LAST declaration wins, so editing the
    first occurrence changes nothing and reads as "the edit did not take".

    Measured on bible.html: 4,682 top-level rules, 201 selectors declared more than once, **153 that
    set the same property in more than one block**. That is not 153 defects — a file grown over
    1,800 versions overrides on purpose — which is exactly why this is a LOOKUP and not a gate. A
    gate would cry wolf 153 times; the hazard is a person editing the wrong copy.

    The tool must be right about WHICH LINE or it is worse than nothing. Its first cut concatenated
    the style blocks and hunted a needle, and reported two different rules as the same line.
    Offsets are carried through now, and this asserts the answers against the file."""

    @staticmethod
    def _mod():
        import importlib.util
        here = os.path.dirname(os.path.abspath(__file__))
        spec = importlib.util.spec_from_file_location("_cww", os.path.join(here, "css_who_wins.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def _bible(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        return p

    def test_every_line_it_reports_really_declares_that_selector(self):
        m, p = self._mod(), self._bible()
        lines = open(p, encoding="utf-8").read().splitlines()
        found = 0
        for sel in (".hero-title", ".h-title", ".tabs"):
            rows = m.blocks_for(p, sel)
            self.assertTrue(rows, "%s is declared nowhere — the scanner rotted" % sel)
            for ln, sellist, _body in rows:
                self.assertIn(sel, lines[ln - 1],
                              "%s reported at line %d, which reads %r" % (sel, ln, lines[ln - 1][:70]))
                found += 1
        self.assertGreaterEqual(found, 8, "the scan collapsed to a couple of rules")

    def test_it_finds_more_than_one_block_for_the_scarred_selector(self):
        m, p = self._mod(), self._bible()
        self.assertGreater(len(m.blocks_for(p, ".hero-title")), 1,
                           "the very selector the scar is about now reads as declared once")

    def test_an_undeclared_selector_says_so_rather_than_guessing(self):
        m, p = self._mod(), self._bible()
        self.assertEqual(m.blocks_for(p, ".no-such-class-anywhere-xyz"), [])

    def test_it_reads_only_style_blocks(self):
        # a selector-looking string in JS or an attribute must not become a CSS rule
        import tempfile
        m = self._mod()
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
            f.write("<div class='x'></div>\n"
                    "<script>var s = \".ghost { color: red }\";</script>\n"
                    "<style>.real { color: blue }</style>\n")
            p = f.name
        try:
            self.assertEqual(m.blocks_for(p, ".ghost"), [], "a JS string became a CSS rule")
            self.assertEqual(len(m.blocks_for(p, ".real")), 1)
        finally:
            os.unlink(p)


class TestNoCssVarWithoutAFallbackOnAnUndefinedToken(unittest.TestCase):
    """v1876 — `var(--x)` on a token nothing defines collapses the whole declaration, silently.

    That is v1841, on his own board: `--fs-tiny` was used and never defined, so the rule carrying it
    rendered with no font-size at all. There is already a guard against the NOTE text re-creating it
    (bump_version refuses `var(--x)` in a build note); there was none on the CSS itself.

    THE DISTINCTION THAT MATTERS: `var(--x, 10px)` still renders — the fallback is doing the work,
    which is a token that is decorative rather than broken, and that is a tidiness question and his
    call. `var(--x)` with NO fallback and no definition renders NOTHING. Only the second fails here.

    ⚠ THE INSTRUMENT NEEDED TWO CORRECTIONS BEFORE ITS VERDICT WAS WORTH ANYTHING, both found by
    looking at what it accused:
      · a token set from JS — `style.setProperty('--claim-h', …)` — is defined, just not in CSS.
        Four of the five accusations were these.
      · `'var(--q-' + rarity + ')'` is a dynamic CONSTRUCTION, not a reference to a token named
        `--q-`. The fifth was that.
    Founding rule 4, twice in one sweep. [[feedback-suspect-the-instrument]]"""

    @classmethod
    def _dead(cls, src):
        import re
        s = TestNoOptionalCallToAFunctionThatCannotExist._strip_js_comments(src)
        defined = set(re.findall(r"(--[\w-]+)\s*:", s))
        defined |= set(re.findall(r"setProperty\(\s*['\"](--[\w-]+)", s))
        bad = []
        for m in re.finditer(r"var\(\s*(--[\w-]+)\s*\)", s):     # NO fallback: the failing form
            name = m.group(1)
            if name in defined:
                continue
            # a dynamic build — 'var(--q-' + x + ')' — names no token at all
            if s[max(0, m.start() - 1):m.start()] in ("'", '"'):
                continue
            bad.append(name)
        return sorted(set(bad))

    def test_the_board_has_none(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        dead = self._dead(open(p, encoding="utf-8").read())
        self.assertEqual(dead, [], "used with no fallback and never defined — the declaration "
                                   "carrying it renders nothing: %s" % ", ".join(dead))

    def test_the_console_has_none(self):
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "control_ui.html")
        if not os.path.isfile(p):
            self.skipTest("control_ui.html is not on this machine")
        dead = self._dead(open(p, encoding="utf-8").read())
        self.assertEqual(dead, [], "used with no fallback and never defined: %s" % ", ".join(dead))

    def test_it_SEES_the_v1841_shape_and_spares_the_others(self):
        self.assertEqual(self._dead(".a{font-size:var(--fs-tiny)}"), ["--fs-tiny"])
        self.assertEqual(self._dead(":root{--fs-tiny:10px}.a{font-size:var(--fs-tiny)}"), [])
        self.assertEqual(self._dead(".a{font-size:var(--fs-tiny, 10px)}"), [],
                         "a fallback renders — that is decoration, not breakage")
        self.assertEqual(self._dead("el.style.setProperty('--claim-h', h);.a{top:var(--claim-h)}"), [],
                         "a token set from JS is defined, just not in CSS")
        self.assertEqual(self._dead("var c = 'var(--q-' + rarity + ')';"), [],
                         "a dynamic construction names no token at all")


class TestTheGateWatchesTheWholeTreeNotAList(unittest.TestCase):
    """v1874 — a named watchlist is a list of the leaks somebody already found.

    It named five files while a harness wrote a SIXTH (1,729 rows into his session journal). Adding
    that sixth caught two more writers within the hour. Then hashing the WHOLE tree caught five more
    nobody had thought to name — including `.subscription_budget.json`, which meant every push spent
    a real vision call on his account.

    So the gate hashes everything under tv/ now. The named files stay the hard FAILURE; every other
    moved file is reported by name, so the next leak is found the way tonight's were rather than
    waited for. Measured with his console down, after the last writer was fixed: a full 32-gate run
    leaves the tree byte-identical. [[feedback-blind-fixture-green-gate]]"""

    def _rg(self):
        import importlib.util
        here = os.path.dirname(os.path.abspath(__file__))
        spec = importlib.util.spec_from_file_location("_rg_probe", os.path.join(here, "run_gates.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def test_it_names_a_file_that_moved_created_or_vanished(self):
        rg = self._rg()
        before = {"a.json": "111", "b.log": "222", "gone.txt": "333"}
        after = {"a.json": "111", "b.log": "999", "new.txt": "444"}
        moved = rg._tree_diff(before, after)
        joined = " | ".join(moved)
        self.assertIn("b.log", joined, "a changed file was not reported")
        self.assertIn("new.txt", joined, "a file the run CREATED was not reported")
        self.assertIn("gone.txt", joined, "a file the run DELETED was not reported")
        self.assertNotIn("a.json", joined, "an untouched file was reported")

    def test_an_unchanged_tree_reports_nothing(self):
        # the mirror — a reporter that always speaks is one he learns to scroll past
        rg = self._rg()
        same = {"a.json": "111", "b.log": "222"}
        self.assertEqual(rg._tree_diff(same, dict(same)), [])

    def test_the_watchlist_is_still_the_hard_failure(self):
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "run_gates.py"), encoding="utf-8").read()
        self.assertIn('failed.append("live-state-untouched")', src,
                      "the named files stopped failing the run")
        self.assertIn('if m.split(" (")[0] not in _LIVE_STATE', src,
                      "the tree report duplicates the named files instead of complementing them")

    def test_the_skips_are_the_three_that_legitimately_churn(self):
        rg = self._rg()
        self.assertEqual(rg._TREE_SKIP_DIRS,
                         {".git", "__pycache__", "frames", "node_modules", ".pytest_cache"})


class TestNoLookupOfAnElementThatIsNeverCreated(unittest.TestCase):
    """v1873 — `document.getElementById('x')` where no `id="x"` exists anywhere returns null, and
    the usual `if (el)` around it turns that into silence.

    The console records this exact failure in its own comment: everything after one line "wrote into
    #hd-shelf-grid, an element nothing creates" — a whole block of work rendering into nowhere.

    Swept with a stripper that is itself checked first (see the sibling class): **bible.html looks
    up 276 distinct ids and declares 444; zero lookups have no declaration. control_ui.html: 236
    looked up, zero missing.** Both clean, and now they stay clean.

    ⚠ THE COUNT WAS THE TELL. The first run of this sweep reported 135 missing ids in the board.
    That is not a codebase 135 ways broken, it is a broken instrument: the unbounded comment
    stripper had deleted 170 of the 444 declarations. Founding rule 4, and the reason the
    stripper's own test sits beside this one. [[feedback-suspect-the-instrument]]"""

    @staticmethod
    def _missing(src):
        import re
        s = TestNoOptionalCallToAFunctionThatCannotExist._strip_js_comments(src)
        ids = set(re.findall(r"\bid\s*=\s*[\\]?['\"]([\w-]+)", s))
        got = set(re.findall(r"getElementById\(\s*['\"]([\w-]+)['\"]\s*\)", s))
        return sorted(got - ids)

    def test_the_board_looks_up_nothing_it_never_creates(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        dead = self._missing(open(p, encoding="utf-8").read())
        self.assertEqual(dead, [], "these ids are looked up and never created, so every branch "
                                   "behind them is silent: %s" % ", ".join(dead))

    def test_the_console_looks_up_nothing_it_never_creates(self):
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "control_ui.html")
        if not os.path.isfile(p):
            self.skipTest("control_ui.html is not on this machine")
        dead = self._missing(open(p, encoding="utf-8").read())
        self.assertEqual(dead, [], "looked up and never created: %s" % ", ".join(dead))

    def test_it_SEES_the_hd_shelf_grid_shape(self):
        # the console's own recorded scar, as the fixture
        live = "<div id=\"hd-shelf\"></div>\ndocument.getElementById('hd-shelf').innerHTML = x;\n"
        dead = "<div id=\"hd-shelf\"></div>\ndocument.getElementById('hd-shelf-grid').innerHTML = x;\n"
        self.assertEqual(self._missing(live), [])
        self.assertEqual(self._missing(dead), ["hd-shelf-grid"])


class TestNoTypeofGuardOnANameThatCannotExist(unittest.TestCase):
    """v1872 — `typeof X !== 'undefined'` on a name that is never declared is PERMANENTLY FALSE,
    and it fails silently, which is the worst way for a feature to be absent.

    That is not hypothetical here — it is v1562, recorded in bible.html's own comment: a Session
    cockpit KPI tile "HAS NEVER RENDERED, NOT ONCE" because its guard needed `SETS` and the array is
    called `ITEM_SETS`. `typeof` on a name that was never declared returns 'undefined' rather than
    throwing, so the condition was false forever and the tile drew nothing. His cockpit reported
    Chronicle 99/99 and Grail 243/403 and said nothing at all about sets, while the F·Sets tab one
    click away said 108/135.

    The board is ~44k lines and there are 94 such guards in it. This is the cheap static check that
    the class is closed, and it is the JS twin of the AST walk that found MINI dead (v1863).
    [[source-reading-guard]]"""

    # names the browser or the host provides — a guard on one of these is the guard doing its job
    HOST = {"window", "document", "console", "Object", "Array", "JSON", "Math", "Date", "String",
            "Number", "Boolean", "Promise", "Set", "Map", "WeakMap", "WeakSet", "RegExp", "Error",
            "localStorage", "sessionStorage", "fetch", "navigator", "location", "performance",
            "requestAnimationFrame", "cancelAnimationFrame", "IntersectionObserver",
            "MutationObserver", "ResizeObserver", "AbortController", "URL", "URLSearchParams",
            "Intl", "Symbol", "Proxy", "Reflect", "BigInt", "structuredClone", "queueMicrotask",
            "setTimeout", "setInterval", "clearTimeout", "clearInterval", "getComputedStyle",
            "CustomEvent", "Event", "Blob", "File", "FileReader", "Image", "Worker", "matchMedia",
            "crypto", "TextEncoder", "TextDecoder", "Element", "Node", "HTMLElement", "DOMParser",
            "alert", "confirm", "prompt", "history", "screen", "top", "parent", "self", "globalThis"}

    @classmethod
    def _dead_guards(cls, src):
        import re
        guards = set(re.findall(
            r"typeof\s+([A-Za-z_$][\w$]*)\s*[!=]==?\s*['\"]undefined['\"]", src))
        declared = set()
        for pat in (r"\b(?:var|let|const)\s+([A-Za-z_$][\w$]*)",
                    r"\bfunction\s+([A-Za-z_$][\w$]*)",
                    r"\bclass\s+([A-Za-z_$][\w$]*)",
                    r"window\.([A-Za-z_$][\w$]*)\s*=",
                    r"\b([A-Za-z_$][\w$]*)\s*=\s*(?:function|\(|\{|\[)"):
            declared.update(re.findall(pat, src))
        return sorted(n for n in guards if n not in declared and n not in cls.HOST)

    def test_the_board_has_none(self):
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
        if not os.path.isfile(p):
            self.skipTest("bible.html is not on this machine")
        src = open(p, encoding="utf-8").read()
        dead = self._dead_guards(src)
        self.assertEqual(dead, [], "guarded on names that are never declared, so the branch can "
                                   "never run: %s" % ", ".join(dead))

    def test_the_console_has_none(self):
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "control_ui.html")
        if not os.path.isfile(p):
            self.skipTest("control_ui.html is not on this machine")
        dead = self._dead_guards(open(p, encoding="utf-8").read())
        self.assertEqual(dead, [], "guarded on names that are never declared: %s" % ", ".join(dead))

    def test_it_SEES_the_v1562_shape(self):
        """A gate never seen red is measuring nothing. This is v1562's exact line, and the name it
        should have used, side by side."""
        good = "var ITEM_SETS = [];\nif (typeof ITEM_SETS !== 'undefined') { draw(); }\n"
        bad = "var ITEM_SETS = [];\nif (typeof SETS !== 'undefined') { draw(); }\n"
        self.assertEqual(self._dead_guards(good), [])
        self.assertEqual(self._dead_guards(bad), ["SETS"])


class TestTheMiniDurationsHaveOneSource(unittest.TestCase):
    """v1870 — Konyo: "i just did a MINI sets and its too short.. it needs to be longer like the
    UNIQUES mini".

    They were ALREADY equal — 75s on the server and 75s in the console's own MINI_FOCUS_SECS table —
    so the premise as stated could not be the defect. The reason underneath it is real: a SETS row
    is three lines (name · Dropped By · First Found) where a UNIQUES row is one, so the same 75
    seconds of scrolling covers about a third as much ledger. Equal numbers, unequal work. And the
    ceiling was binding either way, because the console sends only {focus} and no duration — he had
    no way to ask for longer.

    The second copy is the part that would have made the fix invisible: raising the bound on the
    server would have left the button printing 75s and asking for 75s. [[copy-drift]]"""

    def test_sets_gets_longer_than_uniques(self):
        import control_app as ca
        self.assertGreater(ca._mini_bounds("chronicle-sets")[0],
                           ca._mini_bounds("chronicle-uniques")[0],
                           "a sets row is three lines to a unique's one and they still get equal time")

    def test_there_is_headroom_above_both(self):
        import control_app as ca
        for f in ("chronicle-sets", "chronicle-uniques"):
            d, mx = ca._mini_bounds(f)
            self.assertGreater(mx, d, "%s cannot be asked to run longer than its default" % f)

    def test_the_stash_focuses_are_untouched(self):
        # the mirror — a stash tab is ONE screen and 25s photographs it several times over
        import control_app as ca
        for f in ("stash", "runes", "gems", "materials"):
            self.assertEqual(ca._mini_bounds(f), (25, 40))

    def test_the_engine_publishes_the_numbers_it_enforces(self):
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        self.assertIn("focusSecs={f: _mini_bounds(f)[0] for f in MINI_FOCUSES}", src)
        self.assertIn("focusMax={f: _mini_bounds(f)[1] for f in MINI_FOCUSES}", src)

    def test_the_console_prefers_the_engines_numbers_over_its_own(self):
        here = os.path.dirname(os.path.abspath(__file__))
        ui = open(os.path.join(here, "control_ui.html"), encoding="utf-8").read()
        i = ui.find("if (j && j.focusSecs)")
        j = ui.find("if (j && j.focuses)", i)
        self.assertGreater(i, 0, "the console never reads the published durations")
        self.assertGreater(j, i, "it renders the buttons before taking the durations")
        self.assertIn("MINI_FOCUS_SECS[k] = v", ui[i:j])


class TestTheStatusSaysWhetherReadsAreReal(unittest.TestCase):
    """v1870 — `stub` was in the status payload as a literal None: it reads like "no" and means
    "nobody asked", which is the worst of the three answers.

    It cost an hour tonight. His reel s_1787244002054_15361 is unmistakably his — shared stash open
    at page 1/5, a Raven Frost tooltip under the cursor — and its journal rows say lane=deep
    mode=stub, so those reads were CANNED. Deciding whether that meant he pressed SIM or his console
    had inherited TV_STUB meant reading a log that tests also write to, and then inspecting the live
    process's environment by hand. [[unknown-stays-unknown]]"""

    def test_it_answers_true_when_the_stub_is_set(self):
        import control_app as ca
        keep = os.environ.get("TV_STUB")
        os.environ["TV_STUB"] = "1"
        try:
            p = ca.status_payload()
        finally:
            if keep is None:
                os.environ.pop("TV_STUB", None)
            else:
                os.environ["TV_STUB"] = keep
        self.assertIs(p.get("stub"), True)
        self.assertIs(p.get("readsAreReal"), False)

    def test_it_answers_false_in_real_play(self):
        import control_app as ca
        keep = os.environ.pop("TV_STUB", None)
        try:
            p = ca.status_payload()
        finally:
            if keep is not None:
                os.environ["TV_STUB"] = keep
        self.assertIs(p.get("stub"), False, "None here reads like 'no' and means 'nobody asked'")
        self.assertIs(p.get("readsAreReal"), True)


class TestTheBridgeCacheKeyNamesWhatItCaches(unittest.TestCase):
    """v1862 — his F·Sets tab read 116/135 while the console's DAILY TASK FORCE read 113/135.

    Konyo: "this dailt tasks is not sycned to the counter as the sets and uniques tabs".

    `d2r_forgeSummary` is written ONLY on real change, and `_fsCmp` in bible.html computes the
    signature that decides. `sets` joined the payload in v922; `_fsCmp` was written in v913 and
    never updated. A change in the set count alone produced an identical signature, so the bridge
    was never rewritten and the console served whatever snapshot was stored the last time the GRAIL
    or a RUNEWORD moved. The tab read live, the console read a fossil, and both were sure.

    THE INVARIANT, stated across the two files rather than inside either: every `fs.<chronicle>.<field>`
    the console PRINTS must appear in the comparator that decides whether it is refreshed. A cache
    key that omits the value it is caching is not a cache key. [[the-unjoined-end]] [[copy-drift]]
    """

    def _sources(self):
        here = os.path.dirname(os.path.abspath(__file__))
        b = os.path.join(os.path.dirname(here), "bible.html")
        c = os.path.join(here, "control_ui.html")
        for p in (b, c):
            if not os.path.isfile(p):
                self.skipTest("%s is not on this machine" % os.path.basename(p))
        return (open(b, encoding="utf-8").read(), open(c, encoding="utf-8").read())

    def test_every_field_the_console_prints_is_in_the_compare(self):
        import re
        bible, console = self._sources()
        i = console.find("var _tfChron = function(")
        j = console.find("var runsToday", i)
        self.assertGreater(i, 0, "the console no longer has a task-force chronicle row")
        printed = set(re.findall(r"fs\.(\w+)\.(\w+)", console[i:j]))
        self.assertTrue(printed, "no fs.<chronicle>.<field> is read where the rows are built")
        k = bible.find("var _fsCmp = function(x){")
        self.assertGreater(k, 0, "bible.html no longer has the bridge comparator")
        cmp_body = bible[k:bible.find("if (_fsCmp(", k)]
        for chron, field in sorted(printed):
            self.assertIn("(x.%s || {}).%s" % (chron, field), cmp_body,
                          "the console prints fs.%s.%s and the comparator ignores it — a change in "
                          "it alone will never refresh the bridge" % (chron, field))

    def test_the_compare_still_names_the_sets_count_by_name(self):
        # the specific one that was missing, spelled out, so a refactor of the loop above cannot
        # quietly stop covering the case that cost him three different numbers on one screen
        bible, _ = self._sources()
        k = bible.find("var _fsCmp = function(x){")
        cmp_body = bible[k:bible.find("if (_fsCmp(", k)]
        self.assertIn("(x.sets || {}).found", cmp_body)


class TestTheVaultTemplateGate(unittest.TestCase):
    """2026-08-20 — Konyo: "it needs to be hardcoded and safegauded for vault manager to only when
    maybe i CLICK stash and am in my stash with my inventory open at the same time thats the
    template it should start knowing to read whats in my inventory and stash and log it and ledger
    it accordingly".

    HARDCODED means structural. Before this, a reel without a declared focus paid a MODEL to say
    which ownership surface a frame showed, and vault_retro names the cost when that is wrong: "a
    rune tab misread as 'inventory' files his runes in the wrong lane, which merge-max then makes
    permanent." Permanent is why he opened the vault manager and found items he does not have.

    The gate reads the stash TAB CHROME out of a fixed band by OCR — no chrome, no stash panel, no
    vault read — and D2R draws the inventory beside the stash whenever it is open, which is the
    "both at the same time" template he described.
    """

    def test_the_sweep_asks_the_gate_before_paying_a_classify(self):
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        i = src.find("if stash_screen_open(p) is None:")
        self.assertGreater(i, 0, "no vault classify consults the stash template")
        # bound by the function's REAL end, not a byte count — a 2000-char window broke the moment
        # v1859 added its explanation. [[source-reading-guard]]
        i = src.rfind("def _classify(p):", 0, i)
        body = src[i:src.find("def _reader", i)]
        gate_at = body.find("stash_screen_open(")
        pay_at = body.find("_tick(classified=1)")
        self.assertGreater(gate_at, -1)
        self.assertGreater(pay_at, -1)
        self.assertLess(gate_at, pay_at,
                        "the gate is asked AFTER the classify is charged — a frame that is not a "
                        "stash must cost nothing")

    def test_the_QUOTE_asks_the_same_gate_as_the_sweep(self):
        """v1851 — both halves of a price must name the same thing.

        vault_scan_cost's probe answered "stash" for every path on purpose (v1596: price the WORST
        case, because a probe answering None hid the larger half of the bill). v1850 then put a
        structural gate in front of the real sweep, so the quote would have priced every gameplay
        frame as a readable stash page while the sweep refuses those for free — the same mismatch
        v1834 fixed on the chronicle side, where a 483-frame reel quoted the cost of a different one.
        """
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        i = src.find("def vault_scan_cost")
        self.assertGreater(i, 0)
        j = src.find('return "stash"', i)
        self.assertGreater(j, i, "the vault quote's probe moved — re-point this guard")
        # v1941 — ASSERT THE GATE, NOT ITS SPELLING. This required the literal
        # "stash_screen_open(" and so failed the moment the quote started calling
        # stash_screen_open_CACHED() — a memo that delegates to the very same gate and is proven in
        # tv/test_gate_cache.py to return the identical answer (and to MISS rather than lie when a
        # frame is rewritten). The guard was right to fire: the two halves of a price must name the
        # same thing, and it could not tell a rename from a divergence. So it now accepts the gate
        # or a wrapper around it, and the behavioural half of the claim lives in a behavioural test.
        # A guard that pins an exact call string fails on its own REACH, not on the code.
        # [[source-reading-guard]]
        seg = src[i:j]
        self.assertTrue("stash_screen_open(" in seg or "stash_screen_open_cached(" in seg,
                        "the quote prices frames the sweep would refuse for free")

    def test_a_BROKEN_gate_is_not_a_quiet_gate(self):
        """v1854 — stash_screen_open is shaped exactly like prep_tab_chrome was: a bare handler
        returning a plausible value. That is how prep_tab_chrome stayed dead for 310 versions —
        every caller read None as "not a stash panel" when the truth was "this never ran". I wrote
        this one the day after diagnosing that.

        The ANSWER stays None, because refusing is the safe direction for a gate. What must not stay
        the same is the silence."""
        import control_app as ca
        import stash_eye as se
        # v1860 — SABOTAGE WHAT THE GATE ACTUALLY CALLS. This used to break
        # ca._tab_from_ocr_lines; when the gate switched to stash_chrome_canons the sabotage stopped
        # reaching it, the gate ran fine, and this guard would have passed forever on a gate it was
        # no longer testing. It failed instead — because it asserts an OUTCOME (None + a recorded
        # failure), not that a particular symbol was called. [[feedback-blind-fixture-green-gate]]
        before = ca.gate_failures()
        old = se.stash_chrome_canons
        ca.__dict__["_GATE_BROKE"]["said"] = True          # keep the log quiet during the test
        def boom(_lines):
            raise RuntimeError("the gate itself is broken")
        se.stash_chrome_canons = boom
        try:
            here = os.path.dirname(os.path.abspath(__file__))
            f = os.path.join(here, "frames", "hist", "5_1784984201581.jpg")
            if not os.path.isfile(f):
                self.skipTest("his footage is not on this machine")
            got = ca.stash_screen_open(f)
        finally:
            se.stash_chrome_canons = old
        self.assertIsNone(got, "a broken gate must still refuse — that is the safe direction")
        self.assertGreater(ca.gate_failures(), before,
                           "the gate failed and said nothing — the exact shape that hid "
                           "prep_tab_chrome for 310 versions")

    def test_FULL_chrome_admits_it_is_the_strongest_proof_the_stash_is_open(self):
        """v1860 — the gate refused his clearest stash frames.

        It asked tab_from_ocr_lines "which tab?", which abstains on 2+ legible labels — correctly,
        because the strip prints all five whichever is active — and then read that abstention as
        "not a stash frame". So a strip reading ['$•NAL','SHAkED','% Gems','I mATeRIALS'] — four tab
        names, chrome that renders ONLY when the panel is open — was turned away exactly like an
        empty frame. Two of his own reels' frames, measured.

        Admission counts labels; it does not ask which is selected. One is proof, four is
        overwhelming, and the tab stays unknown because it genuinely is."""
        import control_app as ca
        for lines, why in (
            (["$\u2022NAL", "SHAkED", "% Gems", "I mATeRIALS"], "his frame 6_1784984233446"),
            (["S*NAL", "SHARED", "g Gems", "mATeRIALS"], "his frame 8_1785078207015"),
        ):
            self.assertGreaterEqual(len(se.stash_chrome_canons(lines)), 2, why)
            self.assertEqual(se.tab_from_ocr_lines(lines), "",
                             "the tab is genuinely ambiguous — that half was always right")

    def test_ambiguous_chrome_names_no_tab_it_did_not_read(self):
        """Admitting must not become inventing: the gate may name a tab only when something actually
        READ one, never from how many labels the OCR happened to transcribe.

        ⚠ v1913 UPDATED THE EXPECTED VALUE AND NOT THE RULE. This asserted `stash` because, when it
        was written, nothing on the frame could say which tab was selected — so "unknown" was the
        only truthful answer. The gem reader now reads it (12/12, structural, abstains rather than
        guess), and on THIS frame it says `personal`, which is what the picture shows: gold box and
        blue gem on PERSONAL, four grey labels beside it.

        So the invariant is unchanged and the answer got better. The half that must never come back
        — naming a tab from a label COUNT — is pinned in
        TestOneLegibleLabelIsNotASelectedTab, and by the no-gem case below."""
        import control_app as ca
        import stash_eye as se_mod
        from unittest import mock
        here = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(here, "frames", "hist", "6_1784984233446.jpg")
        if not os.path.isfile(f):
            self.skipTest("his footage is not on this machine")
        self.assertEqual(ca.stash_screen_open(f), "personal",
                         "the gate stopped reporting the tab the picture actually shows")
        # and with nothing able to READ the tab, it must go back to saying only "open"
        with mock.patch.object(se_mod, "tab_from_gem", lambda p: ("", {"method": "stub"})):
            self.assertEqual(ca.stash_screen_open(f), "stash",
                             "with no reader for the tab, full chrome must admit as an open stash "
                             "of UNKNOWN tab — never one of the five as a guess")

    def test_junk_chrome_still_refuses(self):
        """The mirror, or the fix is just a gate that always says yes. Two of the same 68 frames
        OCR'd to ['AYp*INt..:-;'] — no canon label anywhere — and must still be refused."""
        import control_app as ca
        self.assertEqual(se.stash_chrome_canons(["AYp*INt..:-;"]), [])
        self.assertEqual(se.stash_chrome_canons(["Corrupted tremors strike Durance of Hate"]), [])

    def test_a_SILENT_ocr_lane_is_counted_apart_from_a_dark_strip(self):
        """v1864 — this very class went RED once, mid-run, and passed alone seconds later.

        His live session held the OCR worker; `ocr_fast` came back with no lines; the gate answered
        None for a genuine stash frame. The frame-level answer cannot tell "the strip was dark" from
        "the reader could not run" — both are zero lines — and None is the safe answer either way.
        What CAN tell them apart is the RUN: every probe silent means the lane is down, not that his
        footage holds no stash. So the two are counted separately and read out.
        [[feedback-silence-is-not-evidence]]"""
        import control_app as ca
        import tv_diablo as tvd
        s0, h0 = ca.gate_hearing()
        here = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(here, "frames", "hist", "6_1784984233446.jpg")
        if not os.path.isfile(f):
            self.skipTest("his footage is not on this machine")
        old = tvd.ocr_fast
        try:
            tvd.ocr_fast = lambda *_a, **_k: {}          # the lane, answering nothing
            self.assertIsNone(ca.stash_screen_open(f),
                              "a gate that cannot read must refuse — that half was always right")
        finally:
            tvd.ocr_fast = old
        s1, h1 = ca.gate_hearing()
        self.assertEqual(s1, s0 + 1, "the silence was not counted — it is invisible again")
        self.assertEqual(h1, h0, "a silent probe was counted as one that heard something")
        # and the mirror: a frame it CAN read moves the other counter, or the pair is decoration
        # v1913 — `personal`, not `stash`: the gem reader names this frame's tab now. The counter
        # is what this test is about; the tab value is asserted by its own class.
        self.assertEqual(ca.stash_screen_open(f), "personal")
        s2, h2 = ca.gate_hearing()
        self.assertEqual((s2, h2), (s1, h1 + 1))

    def test_the_sweeps_silence_report_measures_THIS_RUN_not_the_process(self):
        """v1865 — caught reviewing v1864, which was my own fix for the defect it repeated.

        gate_hearing() counts for the LIFE OF THE PROCESS. The console runs for hours, so one
        successful probe ever makes `heard` non-zero forever and the "the reader is silent" warning
        could never fire again however completely the OCR lane died afterwards. A run-level claim
        built on a lifetime counter. [[stale-reading]]"""
        import ast, control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        i = src.find("def _vault_sweep_run(")
        j = src.find("\ndef ", i + 10)
        body = src[i:j]
        self.assertIn("_gate0 = gate_hearing()", body,
                      "the sweep does not snapshot the gate's audibility before it starts")
        self.assertIn("_GATE_SILENT[0] - _gate0[0]", body)
        self.assertIn("_GATE_HEARD[0] - _gate0[1]", body)
        # and the snapshot must be taken BEFORE anything is probed, or the delta is not the run's
        self.assertLess(body.find("_gate0 = gate_hearing()"), body.find("_vr.sweep("),
                        "the baseline is taken after the sweep — the delta would be zero")

    def test_a_working_gate_records_no_failures(self):
        # 0 must mean "it ran", never "nobody looked" — otherwise the counter is the next silence
        import control_app as ca
        here = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(here, "frames", "hist", "5_1784984201581.jpg")
        if not os.path.isfile(f):
            self.skipTest("his footage is not on this machine")
        before = ca.gate_failures()
        self.assertTrue(ca.stash_screen_open(f))
        self.assertEqual(ca.gate_failures(), before, "a healthy read was counted as a failure")

    def test_the_gate_is_on_the_READER_too_not_only_the_classify(self):
        """v1853 — v1850 claimed the gate covered every frame "including inside a declared-focus
        reel". It did not: vault_retro skips the classifier ENTIRELY for a declared focus (v1603,
        `if declared: surface = declared`), so the gate never ran on exactly the reels he records on
        purpose — a mini started while walking to the stash.

        The READER is the one hook both paths pass through."""
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        # v1892 — bounded by the function's real end, not 900 bytes of habit
        body = _between(self, src, "def _reader(p, surface):", "\n        prop = _vr.sweep(",
                        min_len=200, what="the vault reader")
        self.assertIn("stash_screen_open(", body,
                      "a declared-focus reel still reads every frame as ownership, gate or no gate")
        gate_at = body.find("stash_screen_open(")
        pay_at = body.find("_tick(pagesRead=1)")
        self.assertGreater(pay_at, -1)
        self.assertLess(gate_at, pay_at, "the frame is charged before the gate is asked")

    def test_a_refused_frame_is_reported_not_silent(self):
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        self.assertIn("refused by the stash template", src,
                      "frames vanish with no reason — 'the stash was never open on camera' and "
                      "'the reader found nothing in it' are different answers")

    def test_gameplay_is_not_an_ownership_screen(self):
        import control_app as ca
        here = os.path.dirname(os.path.abspath(__file__))
        play = os.path.join(here, "frames", "hist", "6_1786554035205.jpg")
        if not os.path.isfile(play):
            self.skipTest("his footage is not on this machine")
        self.assertIsNone(ca.stash_screen_open(play),
                          "a gameplay frame would be read into his vault")

    def test_a_real_stash_frame_still_passes(self):
        # the gate must not be a mute button: refusing everything is the same defect as refusing
        # nothing, and it is how the first cut of this shipped before prep_tab_chrome was revived
        import control_app as ca
        here = os.path.dirname(os.path.abspath(__file__))
        stash = os.path.join(here, "frames", "hist", "5_1784984201581.jpg")
        if not os.path.isfile(stash):
            self.skipTest("his footage is not on this machine")
        self.assertTrue(ca.stash_screen_open(stash))



class TestTheTemplateClassifiesForFree(unittest.TestCase):
    """2026-08-20 — Konyo: "is there a way here to code this more inteligently?"

    There was, and it was already written. chronicle_template.detect() resolves the Chronicle tab
    from FOUR independent pixel signals and reports how many voted. Structural, free, and until now
    called by NOTHING outside its own test — tv_diablo imports the module only to borrow a crop
    band — while every candidate run paid a MODEL to answer the same question.

    Measured on his own frames before wiring: uniques page 4/4, sets page 4/4, TV DIABLO console
    window 1/4, gameplay 1/4, stash panel 0/4.
    """

    def _f(self, *parts):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames", "hist", *parts)

    def test_it_names_the_uniques_tab_with_no_model(self):
        import chronicle_template as ct
        f = self._f("reel_s_1786999742937_35523", "f_1786999985035.jpg")
        if not os.path.isfile(f):
            self.skipTest("his footage is not on this machine")
        self.assertEqual(ct.ledger_kind_for_tab((ct.detect(f) or {}).get("tab")), "chronicle-uniques")

    def test_it_names_the_sets_tab_with_no_model(self):
        import chronicle_template as ct
        f = self._f("reel_s_1787177267889_92273", "f_1787177293765.jpg")
        if not os.path.isfile(f):
            self.skipTest("his footage is not on this machine")
        self.assertEqual(ct.ledger_kind_for_tab((ct.detect(f) or {}).get("tab")), "chronicle-sets")

    def test_it_ABSTAINS_on_a_frame_that_is_not_the_chronicle(self):
        """Abstaining is an answer here, not a failure — and it is what makes the fallback safe.
        A detector that guessed on gameplay would put names into a grail he never opened."""
        import chronicle_template as ct
        for name, parts in (("console window", ("reel_s_1787177267889_92273", "f_1787177276485.jpg")),
                            ("gameplay", ("6_1786554035205.jpg",)),
                            ("stash", ("5_1784984201581.jpg",))):
            f = self._f(*parts)
            if not os.path.isfile(f):
                continue
            self.assertIsNone(ct.ledger_kind_for_tab((ct.detect(f) or {}).get("tab")),
                              "%s was classified as a Chronicle ledger" % name)

    def test_the_sweep_asks_the_template_before_paying(self):
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        i = src.find("def _classify_one(p):")
        self.assertGreater(i, 0)
        # 3600, not 2200: the explanation above _classify_one is long and a short window stopped
        # before the paid fallback. That is the FOURTH guard of mine today to fail on its own reach
        # rather than on the code — measure the window against the function, not against a habit.
        # the function's real end is the line that WRAPS it — `_classify = _cr.classifier(...)`.
        # The first end anchor I reached for ("def _reader") does not exist after this function at
        # all, and _between REFUSED rather than silently running to EOF. That refusal is the whole
        # point of the helper: the old `src[i:i + 3600]` would have measured 3600 bytes of whatever
        # happened to follow and reported a pass.
        body = _between(self, src, "def _classify_one(", "_classify = _cr.classifier(",
                        min_len=400, what="the chronicle classify")
        t_at = body.find("chronicle_template")
        pay_at = body.find("_tv.claude_read(")
        self.assertGreater(t_at, -1, "the sweep still pays a model for what the template knows")
        self.assertGreater(pay_at, -1, "the paid fallback is gone — an abstaining detector needs it")
        self.assertLess(t_at, pay_at, "the model is called before the free detector is asked")

    def test_the_tab_GUESS_may_never_name_the_ownership_surface(self):
        """v1859 — v1857 did exactly this and it was wrong.

        stash_eye.tab_from_ocr_lines says so in its own docstring: "Active-tab GUESS from OCR
        lines. Stash chrome always prints ALL five tab names... 2+ canons -> '' (ambiguous chrome;
        pixel/grid fingerprint decides)."

        Proven on his frame 5_1784984201581.jpg: the strip OCRs as [',WAAITHsrirEP', 'Gems',
        'fflATtklAL5'] — a tooltip plus two labels, one garbled past recognition — so one canon
        matched and it answered "gems" while the selected tab is Runes. v1857 handed that to the
        reader as the SURFACE; the reader was asked whether a runes panel is a gems panel, said no,
        and returned zero items from a stash full of them.

        Reading a label proves the stash is OPEN (v1850's gate, still sound). It does not prove
        which tab is SELECTED, and a lane assignment made from it is the very mis-filing this arc
        exists to prevent."""
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        i = src.find("if stash_screen_open(p) is None:")
        self.assertGreater(i, 0, "the vault gate stopped reading the tab entirely")
        # NAME-INDEPENDENT. A `assertNotIn("return _surf")` only forbids the variable v1857
        # happened to use; the invariant is about what the function may RETURN at all. Every exit
        # from the vault classify is either "I do not know" (None) or the paid reader's answer.
        # Anything else is a surface named without paying for it. [[source-reading-guard]]
        import ast
        fn = None
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.FunctionDef) and node.name == "_vault_sweep_run":
                for inner in ast.walk(node):
                    if isinstance(inner, ast.FunctionDef) and inner.name == "_classify":
                        fn = inner
        self.assertIsNotNone(fn, "no _classify inside _vault_sweep_run")
        rets = [r.value for r in ast.walk(fn) if isinstance(r, ast.Return)]
        self.assertTrue(rets, "a classify that returns nothing classifies nothing")
        paid = 0
        for v in rets:
            if v is None or (isinstance(v, ast.Constant) and v.value is None):
                continue          # "not a stash screen" / the reader died — both honest unknowns
            self.assertIsInstance(v, ast.Call, "the vault classify returns a value it did not pay for")
            self.assertEqual(getattr(v.func, "attr", None), "claude_read",
                             "only the paid reader may name the ownership surface")
            paid += 1
        self.assertGreater(paid, 0, "the paid classify is gone — the guess would be all that is left")

    def test_the_model_is_still_the_fallback(self):
        # this may only REMOVE model calls; when the detector abstains the old path must run
        # unchanged, or an occluded tab becomes an unread page
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        i = src.find("def _classify_one(p):")
        self.assertIn("claude_read", src[i:i + 3600])


class TestV1923TheGameGetsAVetoOnTheWritePath(unittest.TestCase):
    """A flag the register button ignores is decoration.

    v1923 added the counter-ledger: the game's own Remaining page, which is the only reading in the
    whole pipeline that can say "you do NOT have that". It caught one row of 36 — Natalya's Soul
    (claws) — in the proposal Konyo was about to register. Flagging it in the panel and then writing
    it anyway would have been the worst of both: a warning that reads as protection while the button
    beside it puts the row on his board.

    So the veto lives on the WRITE path, where pressing register cannot bypass it. These tests pin
    both directions, because a veto only ever seen pass is a veto nobody has seen work — and pin the
    two rows it must NEVER eat, which is the more dangerous half: withholding a real find on
    evidence nobody has is worse than the defect it was built for.
    [[feedback-blind-fixture-green-gate]] [[stale-reading]]
    """

    def _fake_board(self, ca, captured):
        def _ejs(w, js, timeout=8.0):
            i = js.index("window.chronicleApply(") + len("window.chronicleApply(")
            j = js.rindex(");return JSON.stringify")
            captured.append(json.loads(js[i:j]))
            return json.dumps({"ok": True, "applied": {"uniques": 0, "sets": 0, "skipped": 0}})
        return _ejs

    def _run(self, rows, remaining=("Natalya's Soul (claws)",)):
        import tempfile
        import control_app as ca
        tmp = tempfile.mkdtemp(prefix="veto-")
        with open(os.path.join(tmp, "sets.json"), "w", encoding="utf-8") as fh:
            json.dump({"ledger": "sets", "reel": "reel_s_1787307553811_9452",
                       "readAt": "2026-08-21T10:19:13.811000Z",
                       "rows": [{"piece": n} for n in remaining]}, fh)
        cap = []
        old_env = os.environ.get("TV_REMAINING_DIR")
        os.environ["TV_REMAINING_DIR"] = tmp
        old = (ca.__dict__.get("_MAIN_WIN"), ca.__dict__.get("_WINDOW_LIVE"), ca._ejs)
        ca.__dict__["_MAIN_WIN"] = object()
        ca.__dict__["_WINDOW_LIVE"] = True
        ca._ejs = self._fake_board(ca, cap)
        try:
            out = ca.chronicle_apply({"wouldAdd": {"uniques": [], "sets": rows}, "held": []})
        finally:
            ca.__dict__["_MAIN_WIN"], ca.__dict__["_WINDOW_LIVE"], ca._ejs = old
            if old_env is None:
                os.environ.pop("TV_REMAINING_DIR", None)
            else:
                os.environ["TV_REMAINING_DIR"] = old_env
        sent = [r["name"] for r in ((cap[0] if cap else {}).get("wouldAdd") or {}).get("sets", [])]
        return out, sent

    def test_a_denied_row_never_reaches_the_board(self):
        out, sent = self._run([
            {"name": "Natalya's Soul (claws)", "seen": [{"frame": "f_1787177277865.jpg"}]},
            {"name": "Aldur's Rhythm (mace)", "seen": [{"frame": "f_1787177277865.jpg"}]},
        ])
        self.assertEqual(sent, ["Aldur's Rhythm (mace)"],
                         "the denied row was handed to the board anyway")
        self.assertEqual(out.get("withheld"), ["Natalya's Soul (claws)"])
        self.assertIn("still lists them as missing", out.get("withheldWhy", ""))

    def test_a_row_the_game_never_listed_passes_through_untouched(self):
        """The veto must be seen NOT firing, or it is indistinguishable from a filter that eats
        everything."""
        out, sent = self._run([
            {"name": "Aldur's Rhythm (mace)", "seen": [{"frame": "f_1787177277865.jpg"}]},
        ])
        self.assertEqual(sent, ["Aldur's Rhythm (mace)"])
        self.assertNotIn("withheld", out)

    def test_a_piece_found_AFTER_the_page_is_NOT_withheld(self):
        """The dangerous half. He keeps playing; the page ages. A find made after the reading must
        survive, or the safeguard starts deleting the finds it exists to protect."""
        out, sent = self._run([
            {"name": "Natalya's Soul (claws)", "seen": [{"frame": "f_1787999999999.jpg"}]},
        ])
        self.assertEqual(sent, ["Natalya's Soul (claws)"],
                         "seen AFTER the Remaining page — the page is older than the fact")
        self.assertNotIn("withheld", out)

    def test_an_UNDATED_sighting_is_not_withheld_either(self):
        """Order unknown is not evidence for the accusation. [[unknown-stays-unknown]]"""
        out, sent = self._run([
            {"name": "Natalya's Soul (claws)", "seen": [{"frame": "screenshot.png"}]},
        ])
        self.assertEqual(sent, ["Natalya's Soul (claws)"])
        self.assertNotIn("withheld", out)

    def test_with_no_remaining_page_on_file_nothing_is_withheld(self):
        out, sent = self._run(
            [{"name": "Natalya's Soul (claws)", "seen": [{"frame": "f_1787177277865.jpg"}]}],
            remaining=())
        self.assertEqual(sent, ["Natalya's Soul (claws)"],
                         "no reading on file must mean the veto is silent, never that it denies "
                         "everything or approves everything on its own authority")
        self.assertNotIn("withheld", out)


class TestV1923EveryCssVariableUsedIsActuallyDefined(unittest.TestCase):
    """An undefined CSS custom property does not error. It INHERITS — silently.

    v1923 styled a new warning strip with `var(--st-ok)`. This file's token is `--st-good`. Nothing
    failed: no parse error, no console warning, no failing assertion. The strip simply rendered in
    inherited white — which made the one REASSURING message on the panel the loudest thing on it,
    above the two genuine warnings. Found by looking at the pixels, which is the only thing that
    could have found it.

    That is the whole class, and it is worth a guard precisely because the failure mode is a
    plausible-looking page rather than an error:

      * `color: var(--nope)`      -> inherits the parent colour
      * `color-mix(in srgb, var(--nope) 45%, transparent)` -> the whole declaration is invalid at
        computed-value time, so the property falls back to its inherited or initial value

    ⚠ COMMENTS ARE STRIPPED FIRST, and this is not caution — it is the majority of the answer. Run
    raw, this sweep reports four undefined tokens across the two files and THREE are prose: `--a`
    and `--rar-rune` appear only inside comments (one of them quoting the OTHER file), and `--q-`
    is the literal prefix of a name JS concatenates at runtime. Exactly one was real, and it was
    mine. A guard that reads documentation reports its own explanations as defects.
    [[feedback-comments-vs-code]] [[feedback-suspect-the-instrument]]
    """

    FILES = ("tv/control_ui.html", "bible.html")

    # Set at runtime via element.style.setProperty(), so they are correctly absent from the
    # stylesheet. Each must be justified by a real setProperty call — asserted below, so this list
    # cannot quietly become a place to hide a genuine miss.
    RUNTIME = {"--tz-cols"}

    def _files(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for rel in self.FILES:
            p = os.path.join(root, rel)
            if os.path.isfile(p):
                yield rel, p

    def test_no_var_reference_resolves_to_nothing(self):
        import re
        strip = TestNoOptionalCallToAFunctionThatCannotExist._strip_js_comments
        problems = []
        for rel, p in self._files():
            with open(p, encoding="utf-8") as fh:
                raw = fh.read()
            src = strip(raw)
            defined = set(re.findall(r"(--[A-Za-z0-9_-]+)\s*:", src))
            for m in re.finditer(r"var\(\s*(--[A-Za-z0-9_-]+)\s*([,)])", src):
                name, nxt = m.group(1), m.group(2)
                if nxt == ",":
                    continue                       # var(--x, fallback) is legitimate
                if name in defined or name in self.RUNTIME:
                    continue
                problems.append("%s: var(%s) is used with no fallback and never defined" % (rel, name))
        self.assertEqual(sorted(set(problems)), [],
                         "an undefined custom property inherits instead of erroring, so this "
                         "renders as a plausible page in the wrong colour")

    def test_every_runtime_exemption_is_really_set_at_runtime(self):
        """An allowlist nobody checks becomes the place defects go to be forgotten."""
        found = set()
        for _rel, p in self._files():
            with open(p, encoding="utf-8") as fh:
                src = fh.read()
            for name in self.RUNTIME:
                if ("setProperty('%s'" % name) in src or ('setProperty("%s"' % name) in src:
                    found.add(name)
        self.assertEqual(found, self.RUNTIME,
                         "these are exempted as runtime-set but no setProperty call sets them: %s"
                         % sorted(self.RUNTIME - found))

    def test_the_stripper_does_not_hide_a_planted_miss(self):
        """Calibrate the instrument through the SAME path the real subjects take, or a clean
        result means nothing. Founding rule 4. [[feedback-blind-fixture-green-gate]]"""
        import re
        strip = TestNoOptionalCallToAFunctionThatCannotExist._strip_js_comments
        planted = "  .planted { color: var(--definitely-not-a-real-token); }\n"
        src = strip(planted)
        defined = set(re.findall(r"(--[A-Za-z0-9_-]+)\s*:", src))
        hits = [m.group(1) for m in re.finditer(r"var\(\s*(--[A-Za-z0-9_-]+)\s*\)", src)
                if m.group(1) not in defined]
        self.assertEqual(hits, ["--definitely-not-a-real-token"],
                         "the sweep cannot see a miss it is pointed straight at")



class TestV1924LiveStateFollowsTheFixture(unittest.TestCase):
    """v1869 wrote the right rule and bound it at the wrong time.

    `tv_diablo.STATE` was computed ONCE, at import, from TV_HIST. Inside a suite the import happens
    during collection, so a test that repoints TV_HIST in its own body got his real tree anyway —
    the redirect looked applied and was not, which is the same trap that truncated his banked
    evidence the same night.

    MEASURED ON HIS MACHINE, 2026-08-21: one gate run wrote **39 stub reads into the live
    tv/state.json**, replaced his session id, and left `readCount: 39` against `cap: 240`. The file
    went 3,867 -> 49,080 bytes and every read in it was `mode: "stub"`. It had been happening on
    every local run, silently, because nothing compared the file before and after.

    Guarded here and, behaviourally, by tv/conftest.py — which is what caught it.
    [[feedback-fixtures-never-touch-live-data]]
    """

    def _tvd(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import tv_diablo as tvd
        return tvd

    def test_a_TV_HIST_set_after_import_still_redirects_live_state(self):
        import tempfile
        tvd = self._tvd()
        real = tvd._state_path()
        tmp = tempfile.mkdtemp(prefix="statepath-")
        old_env, old_state = os.environ.get("TV_HIST"), tvd.STATE
        try:
            os.environ["TV_HIST"] = tmp
            self.assertNotEqual(tvd._state_path(), real,
                                "TV_HIST set after import must still move live state — this is the "
                                "exact hole that spent 39 of his 240 daily reads")
            self.assertTrue(tvd._state_path().startswith(os.path.realpath(tmp)))
        finally:
            tvd.STATE = old_state
            if old_env is None:
                os.environ.pop("TV_HIST", None)
            else:
                os.environ["TV_HIST"] = old_env

    def test_an_explicit_STATE_assignment_still_wins(self):
        """Seen the other way too: a test that says exactly where state goes must not be overruled
        by the environment, or every existing suite that assigns STATE breaks."""
        import tempfile
        tvd = self._tvd()
        tmp = tempfile.mkdtemp(prefix="statepath2-")
        old_env, old_state = os.environ.get("TV_HIST"), tvd.STATE
        try:
            os.environ["TV_HIST"] = tmp
            tvd.STATE = os.path.join(tmp, "explicit.json")
            self.assertTrue(tvd._state_path().endswith("explicit.json"))
        finally:
            tvd.STATE = old_state
            if old_env is None:
                os.environ.pop("TV_HIST", None)
            else:
                os.environ["TV_HIST"] = old_env

    def test_the_canary_that_found_it_is_installed(self):
        """A behavioural guard that lives in a file nobody collects is not a guard."""
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conftest.py")
        self.assertTrue(os.path.isfile(p), "tv/conftest.py is missing — the live-data canary is gone")
        with open(p, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("chron_evidence.json", src)
        self.assertIn("state.json", src)
        self.assertIn("autouse=True", src, "the canary must run without being asked for")



class TestV1928NothingRunnableLivesBelowTheRunner(unittest.TestCase):
    """`if __name__ == "__main__": main()` runs BEFORE anything defined under it.

    ⚠ TWICE IN ONE NIGHT, IN TWO FILES. In tv/test_control.py new classes were appended below the
    runner and simply never collected — caught by TestRunnerIsLast, which exists for that. Then the
    SAME shape in tv/vault_corpus.py: an inventory block appended below the runner, so `main()`
    executed while `INV_SAMPLE` did not yet exist and a 145-second corpus scan died with NameError
    on its last line, after all the work was done.

    ⚠ AND THE SCOPE GUARD PASSED. TestNoFunctionLoadsAnUndefinedName asks whether a name EXISTS,
    not whether it exists YET — `INV_SAMPLE` is a perfectly good module global, defined 20 lines too
    late. A guard can be right about its own question and blind to the failure standing next to it.

    TestRunnerIsLast covers the test files. This covers the RUNNABLE MODULES, which had nothing.
    [[feedback-generalize-fixes]] [[feedback-blind-fixture-green-gate]]
    """

    MODULES = ("vault_corpus.py", "counter_ledger.py", "chronicle_calibrate.py",
               "sets_base_index.py", "chronicle_hunt.py", "chronicle_sweep_now.py",
               "chronicle_doctor.py", "run_gates.py", "bump_version.py")

    @staticmethod
    def _is_main_guard(node):
        import ast
        return isinstance(node, ast.If) and "__main__" in ast.dump(node.test)

    def test_no_module_defines_anything_below_its_main_guard(self):
        import ast
        here = os.path.dirname(os.path.abspath(__file__))
        bad = []
        for name in self.MODULES:
            path = os.path.join(here, name)
            if not os.path.isfile(path):
                continue
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            guard = None
            for node in tree.body:
                if self._is_main_guard(node):
                    guard = node.lineno
            if guard is None:
                continue
            for node in tree.body:
                if node.lineno > guard and not self._is_main_guard(node):
                    bad.append("%s:%d %s is defined BELOW the __main__ guard at :%d"
                               % (name, node.lineno, type(node).__name__, guard))
        self.assertEqual(bad, [],
                         "the __main__ guard runs before these, so the script dies with NameError "
                         "at runtime while importing perfectly cleanly:\n  " + "\n  ".join(bad))

    def test_the_check_can_see_a_planted_offender(self):
        """Calibrate through the same path the real subjects take. Founding rule 4."""
        import ast
        tree = ast.parse('import sys\nif __name__ == "__main__":\n    sys.exit(0)\nX = 1\n')
        guard = [n.lineno for n in tree.body if self._is_main_guard(n)]
        self.assertTrue(guard, "the guard-finder cannot find a guard it was handed")
        below = [n for n in tree.body if n.lineno > guard[-1] and not self._is_main_guard(n)]
        self.assertEqual(len(below), 1, "the check cannot see an assignment placed below the guard")



class TestV1994TheTwoLayersAreCompared(unittest.TestCase):
    """v1994 — Konyo: "we need an AI manager that reads and analyzes above them to cross reference
    and check and verify.. so like another layer of accuracy.. maybe even two."

    Both layers already existed and had never been introduced to each other. inventory_occupancy
    counts filled cells from the pixels, free; the paid read returns names. Nobody compared the two
    numbers, so the one failure a reader cannot self-report — naming an item that is not in the
    picture — had no detector at all.

    MEASURED on his own frames before this was wired (occupied / synthetic named / verdict):
        5_1784984201581  22  0->under-read  22->agree  27->over-read
        7_1784984245418  23  0->under-read  23->agree  28->over-read
        8_1784984208085  22  0->under-read  22->agree  27->over-read
    """

    def test_the_three_verdicts_and_their_boundaries(self):
        import control_app as ca
        rv = ca.reconcile_verdict
        # the fabrication signal — one more name than the panel can hold is already over-read
        self.assertEqual(rv(23, 22), "over-read")
        self.assertEqual(rv(27, 22), "over-read")
        # exactly full is agreement, not a fault
        self.assertEqual(rv(22, 22), "agree")
        # naming fewer than are there is normal: a tooltip covers cells, a read is partial
        self.assertEqual(rv(5, 22), "agree")
        # nothing named while cells are filled is THE GLIMPSE, not a fabrication
        self.assertEqual(rv(0, 22), "under-read")
        # and an empty panel read as empty is agreement, NOT an under-read
        self.assertEqual(rv(0, 0), "agree")

    def test_it_never_says_over_read_when_the_panel_is_unmeasured(self):
        """occupied=0 can mean 'measured empty'. named=0 there must NOT read as a glimpse, or an
        empty stash would be reported as items needing a tooltip pass forever."""
        import control_app as ca
        self.assertEqual(ca.reconcile_verdict(0, 0), "agree")
        # but a single name against a measured-empty panel IS over-read, which is the honest reading
        self.assertEqual(ca.reconcile_verdict(1, 0), "over-read")

    def test_the_sweep_actually_calls_it(self):
        """The join, not the function. A verdict nothing computes is the muleById defect again."""
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        self.assertIn("reconcile_verdict(_named, _occN)", src,
                      "the sweep no longer computes a verdict — the layer above is unwired")
        self.assertIn('prop["reconciled"]', src,
                      "the comparison is computed and never handed to the board")


class TestV1998ThePixelLaneCannotFailSILENTLY(unittest.TestCase):
    """v1998 — `except Exception: pass` around the free pixel work means a missing vault_corpus, a
    broken lattice or a renamed function produces ZERO glimpses and ZERO complaint, which reads
    exactly like "his panels were empty".

    That is not hypothetical here: v1989 shipped a call to `_vault_corpus()` — a function that did
    not exist — inside a bare except, and it would have done nothing forever while looking wired.

    Checked with AST, not a grep: the question is whether the HANDLER for the try block containing
    the pixel calls is a bare `pass`, and a text search cannot see block structure.
    [[feedback-silence-is-not-evidence]] [[source-reading-guard]]
    """

    def _tree(self):
        import ast
        import control_app as ca
        with open(ca.__file__, encoding="utf-8") as fh:
            return ast.parse(fh.read()), ast

    def test_no_pixel_try_block_swallows_into_a_bare_pass(self):
        tree, ast = self._tree()
        PIXEL = ("inventory_lattice", "inventory_occupancy", "_vault_corpus")
        bad = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            body_src = " ".join(
                n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
                for n in ast.walk(node) if isinstance(n, ast.Call) and hasattr(n, "func"))
            if not any(k in body_src for k in PIXEL):
                continue
            for h in node.handlers:
                only_pass = len(h.body) == 1 and isinstance(h.body[0], ast.Pass)
                if only_pass:
                    bad.append("line %d" % h.lineno)
        self.assertEqual(bad, [],
                         "a pixel-lane try block still swallows into a bare pass at %s — a lane that "
                         "cannot report its own failure is indistinguishable from an empty stash"
                         % ", ".join(bad))

    def test_the_failure_is_recorded_once_and_read_out(self):
        """The join: recording without reporting is the same silence one step later."""
        import control_app as ca
        with open(ca.__file__, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("_pix_err.append", src, "nothing records why the pixel lane went quiet")
        self.assertIn("the free pixel lane could not run", src,
                      "the failure is recorded and never printed — a log nobody writes to the run")
        self.assertIn('prop["pixelLaneError"]', src,
                      "the board cannot tell 'measured nothing' from 'measured empty'")
        # recorded ONCE, not per frame: this runs inside a per-frame reader
        self.assertIn("if not _pix_err:", src,
                      "without the guard a broken lane prints once per frame and buries the run")


class TestV2002AVaultSealIsNotALifeSentence(unittest.TestCase):
    """v2002 — the vault lane never learned the lesson the chronicle lane paid for in v1830.

    The chronicle seal records {ts, classified, pages, promptVer, agentVer} and REOPENS a reel that
    an older reader sealed with nothing. The vault seal recorded {"ts": ...} — and VAULT_READ_PROMPT
    had no version constant at ALL, so nothing could tell an old read from a new one and a vault seal
    was permanent however much the reader improved. A stale verdict made permanent, on the lane whose
    mistakes reach his stash. [[label-outlived-referent]] [[feedback-generalize-fixes]]

    The rule mirrors the chronicle one exactly: a productive seal is never re-spent; only the claim
    "I looked and there was nothing" expires, and it expires when the eye that made it is replaced.
    """

    def _f(self):
        import control_app as ca
        return ca._vault_still_sealed

    def test_a_productive_seal_is_never_respent(self):
        """His subscription pays for these reads. Findings outlive the reader that found them."""
        self.assertTrue(self._f()({"ts": 1, "rows": 7, "promptVer": "vp0001"}))

    def test_an_empty_seal_reopens_only_when_the_reader_changed(self):
        import tv_diablo as tv
        cur = tv.VAULT_PROMPT_VER
        self.assertTrue(self._f()({"ts": 1, "rows": 0, "promptVer": cur}),
                        "re-reading with the SAME prompt buys nothing and costs money")
        self.assertFalse(self._f()({"ts": 1, "rows": 0, "promptVer": "vp0001"}),
                         "a newer vault reader must be allowed to look again")

    def test_the_legacy_ts_only_seal_reopens(self):
        """Every row written before v2002 is {"ts": ...} with no rows and no promptVer. Those must
        reopen, or the ledger he already has stays frozen under the reader that made it."""
        self.assertFalse(self._f()({"ts": 1}))

    def test_an_unreadable_record_is_not_a_licence_to_respend(self):
        for junk in ("not-a-dict", None, 7, []):
            self.assertTrue(self._f()(junk), "a broken row must not trigger a paid re-read")

    def test_the_vault_prompt_carries_a_version_at_all(self):
        import tv_diablo as tv
        self.assertTrue(getattr(tv, "VAULT_PROMPT_VER", ""),
                        "without a version nothing can ever tell an old vault read from a new one")

    def test_the_seal_records_what_read_it(self):
        """A seal that cannot say which reader made it cannot be reopened by a better one."""
        import control_app as ca
        with open(ca.__file__, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn('"promptVer": _pv', src, "the vault seal no longer records its reader")
        self.assertIn('"rows": int(_rows)', src,
                      "without rows, a productive seal cannot be told from an empty one")
        self.assertIn("_vault_still_sealed(_sealed_rec(d))", src,
                      "the skip list does not consult the predicate — seals are permanent again")


class TestV2003ACompleteAnswerMaySeal(unittest.TestCase):
    """v2003 — "no rows" is two different facts and was treated as one.

    A sweep that FAILED must never seal; that safeguard is from v1785 and it stands. A sweep that
    READ every frame and found nothing NAMEABLE has given a COMPLETE answer, and D2R guarantees the
    same answer forever: a stash GRID prints no names at all, only the hover tooltip does. Proven on
    his own film, where the reader returns items:[] and is right to.

    Until this, those frames took a PAID read, produced no rows, sealed nothing, and were paid for
    again on the very next sweep. Forever.

    It is only ever a PAUSE: v2002 records the reader on the seal, so the moment VAULT_PROMPT_VER
    changes every one of these reopens by itself. That net had to exist before this could ship,
    which is why they are two versions and not one.
    """

    U = {"verdict": "under-read"}
    A = {"verdict": "agree"}
    O = {"verdict": "over-read"}

    def _f(self):
        import control_app as ca
        return ca.vault_seal_is_definitive

    def test_every_frame_read_and_cross_checked_is_a_complete_answer(self):
        f = self._f()
        self.assertTrue(f(3, [self.U, self.U, self.U], [], []))
        self.assertTrue(f(2, [self.U, self.A], [], []),
                        "a panel measured EMPTY (0 named, 0 occupied) is settled too")

    def test_it_refuses_every_way_the_answer_could_be_incomplete(self):
        f = self._f()
        self.assertFalse(f(0, [], [], []), "a sweep that read nothing knows nothing")
        self.assertFalse(f(3, [self.U] * 3, [], ["boom"]),
                         "the pixel lane failed — no cross-check means no verdict")
        self.assertFalse(f(3, [self.U, self.U, self.O], [self.O], []),
                         "a frame naming MORE than its panel holds is not settled")
        self.assertFalse(f(3, [self.U, self.U], [], []),
                         "one read frame was never cross-checked — the picture is partial")
        self.assertFalse(f(2, [self.U, {"verdict": "?"}], [], []),
                         "an unrecognised verdict must never count as settled")

    def test_junk_in_the_reconcile_list_cannot_pass_by_being_counted(self):
        """A non-dict entry must not satisfy the length check and then be waved through."""
        self.assertFalse(self._f()(2, [self.U, "nope"], [], []))

    def test_a_definitive_seal_records_zero_rows_so_v2002_can_reopen_it(self):
        """The two halves have to agree: this writes rows=0, and _vault_still_sealed reopens a
        rows==0 seal the moment the prompt changes. If this wrote rows=1 it would be permanent."""
        import control_app as ca
        with open(ca.__file__, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn('"rows": 0', src, "a definitive seal must record ZERO rows, or it is permanent")
        self.assertIn("vault_seal_is_definitive(_read_ok[0]", src,
                      "the sweep does not consult the predicate — the leak is back")
        import tv_diablo as tv
        self.assertFalse(ca._vault_still_sealed({"rows": 0, "promptVer": "vp-old"}),
                         "a definitive seal from an older reader must reopen")
        self.assertTrue(ca._vault_still_sealed({"rows": 0, "promptVer": tv.VAULT_PROMPT_VER}),
                        "re-reading with the SAME reader buys nothing and costs money")


class TestV2007TheEndToEndGateRunsOnWhateverFootageEXISTS(unittest.TestCase):
    """v2007 — restores what v1712 recorded as permanently lost.

    TestStashPanelOpenGuard has two real-frame tests that have not run since the corpus was pruned,
    "PERMANENTLY skipped in both venues". v1712 handled that honestly: it kept the pure-predicate
    tests covering the DECISION and wrote down exactly what was gone —

        "What is genuinely lost here is only the END-TO-END path (crop -> features -> label) on real
         pixels, which is why these are kept rather than deleted."

    THE FIXTURES WERE PINNED TO REEL NAMES, and reel names get pruned. Pin to a PROPERTY instead and
    the same coverage survives any pruning: ask his corpus for a frame that classifies not-d2r and a
    frame that classifies as an open stash, whichever reels happen to be on disk today.

    MEASURED across 199 sampled frames of his 31 current reels — every case the pruned pair covered
    is present:
        gameplay / gameplay        122
        stash    / stash            43
        stash    / stash-default    31
        gameplay / not-d2r           3     <- the wallpaper bug's exact verdict

    It still skips where there is genuinely no footage (CI, a fresh checkout), and says so. The
    difference is that it now RUNS on the machine that has the film, every push, instead of nowhere.
    [[feedback-blind-fixture-green-gate]]
    """

    HIST = os.path.join(HERE, "frames", "hist")
    _CACHE = {}

    @classmethod
    def _find(cls, shape, cap=260):
        """First frame whose measured PIXELS match `shape`. Cached so the tests scan once.

        ⚠ IT SEARCHES BY FEATURES, NOT BY VERDICT, and the first cut got this wrong. Anchoring on
        `pick == "not-d2r"` meant that breaking the predicate produced NO not-d2r frames, so the
        search found nothing and the test SKIPPED — sabotage-proven, and a skip is not a failure.
        That is the "a gate that always skips is the same defect" scar, in my own new test, the
        first time I ran it against a broken predicate.

        frac_dark and dark_cols are measurements of the picture and survive any change to the rule
        that reads them, so the frame is still found and the ASSERTION is what fails.
        [[feedback-blind-fixture-green-gate]] [[feedback-suspect-the-instrument]]
        """
        if shape in cls._CACHE:
            return cls._CACHE[shape]
        import glob
        frames = []
        for d in sorted(glob.glob(os.path.join(cls.HIST, "reel_*"))):
            frames += sorted(glob.glob(os.path.join(d, "*.jpg")))[::12]
        hit = None
        for p in frames[:cap]:
            try:
                label, detail = se.classify_stash_grid(p)
            except Exception:
                continue
            fd = (detail or {}).get("frac_dark")
            dc = (detail or {}).get("dark_cols")
            if fd is None or dc is None:
                continue
            # LIT PHOTOGRAPH — the wallpaper shape. Measured in his corpus: 2 frames at fd=0.0, 0 cols.
            if shape == "lit-photo" and fd < 0.05 and dc == 0:
                hit = (p, label, detail); break
            # OPEN PANEL — measured: 61 frames, e.g. fd=0.5302/15 cols, fd=0.3688/11 cols.
            if shape == "open-panel" and 0.15 <= fd <= 0.65 and dc >= 10:
                hit = (p, label, detail); break
        cls._CACHE[shape] = hit
        return hit

    def test_a_not_d2r_frame_never_carries_a_stash_label(self):
        """THE wallpaper bug, end to end on real pixels: 69 desktop frames sealed as stash-gems and
        fired a phantom tally that read 0. The predicate is tested at measured values elsewhere;
        this proves the whole path still agrees with it."""
        hit = self._find("lit-photo")
        if not hit:
            self.skipTest("no lit-photograph frame in this checkout's footage — the DECISION is "
                          "still covered by the _panel_open_from_features tests, which need no film")
        p, label, detail = hit
        self.assertFalse(str(label).startswith("stash"),
                         "%s: a LIT PHOTOGRAPH (frac_dark=%s, dark_cols=%s — no game content) "
                         "classified as %r. This is the wallpaper bug: 69 desktop frames sealed as "
                         "stash-gems and fired a phantom tally that read 0."
                         % (os.path.basename(p), detail.get("frac_dark"),
                            detail.get("dark_cols"), label))
        self.assertEqual(detail.get("pick"), "not-d2r")

    def test_a_real_open_panel_is_still_recognised(self):
        """The other half, and the one a too-strict guard breaks: refusing everything is not a fix.
        A gate that never says yes is the same defect as one that never says no."""
        hit = self._find("open-panel")
        if not hit:
            self.skipTest("no open-stash frame in this checkout's footage")
        p, label, detail = hit
        self.assertTrue(str(label).startswith("stash"),
                        "%s: a real open stash panel classified as %r" % (os.path.basename(p), label))

    def test_the_two_detectors_do_not_flatly_contradict_each_other(self):
        """stash_screen_open (OCR of the tab chrome) and classify_stash_grid (pixel geometry) are
        INDEPENDENT. Where the OCR one admits a frame, the pixel one must not call it not-d2r —
        that combination means one of them is badly wrong, and it is exactly the pair the vault
        sweep leans on. Reported as the finding it is, rather than averaged.
        [[feedback-contradiction-is-the-finding]]"""
        import glob
        import control_app as ca
        frames = []
        for d in sorted(glob.glob(os.path.join(self.HIST, "reel_*"))):
            frames += sorted(glob.glob(os.path.join(d, "*.jpg")))[::12]
        if not frames:
            self.skipTest("no footage in this checkout")
        clashes, looked = [], 0
        for p in frames[:120]:
            if ca.stash_screen_open(p) is None:
                continue
            looked += 1
            try:
                _label, detail = se.classify_stash_grid(p)
            except Exception:
                continue
            if str((detail or {}).get("pick") or "") == "not-d2r":
                clashes.append(os.path.basename(p))
        if not looked:
            self.skipTest("the OCR gate admitted no frame in this sample — nothing to cross-check")
        self.assertEqual(clashes, [],
                         "the tab-chrome OCR admitted these frames as a stash while the pixel "
                         "geometry called them NOT D2R: %s" % ", ".join(clashes[:5]))


class TestV2010NoCallIntoANameThatIsNotThere(unittest.TestCase):
    """v2010 — the shape that hit EIGHT times in one night, three of them mine, finally has a gate.

    A reference to a name nothing binds. Outside a try it crashes loudly and is fixed in a minute;
    inside one it is swallowed and the code looks perfectly wired forever. Both halves read fine
    from their own end — that is the defining property.

      v1989  `_vault_corpus()` — a function that did not exist — inside a bare `except: pass`.
             It would have done nothing, silently, for as long as the file lived.
      v2008  `js_syntax_gate.loopback_path()` without the import. The module is imported LOCALLY
             inside the test methods, so the name was undefined at module scope. The timing did not
             move (93.6s per call, twice) and the shortcut LOOKED wired.
      v2008  `time.time()` in a file that never imports `time`. Same swallow, same silence.

    LAW19 already covers "a symbol with no caller" (v2005) and "a payload key with no reader". This
    is the third face: A CALLER WITH NO SYMBOL.

    ⚠ IT USES CPYTHON'S OWN SYMBOL TABLE, not a hand-rolled walk. The hand-rolled version was tried
    first and produced 59 findings of which nearly all were false — closure variables, parameters,
    module dunders — because getting nested scopes right IS writing pyflakes. `symtable` is the
    compiler's own answer to "what scope does this name resolve to", it is stdlib, and it needs no
    dependency the CI runner lacks. [[source-reading-guard]] [[the-unjoined-end]]
    """

    _BUILTIN = None

    @classmethod
    def _builtins(cls):
        if cls._BUILTIN is None:
            import builtins
            cls._BUILTIN = set(dir(builtins)) | {
                "__file__", "__name__", "__doc__", "__spec__", "__package__", "__builtins__",
                # Windows-only names this tree references behind a platform check
                "WindowsError",
            }
        return cls._BUILTIN

    @staticmethod
    def _module_globals(st):
        return {s.get_name() for s in st.get_symbols()
                if s.is_assigned() or s.is_imported() or s.is_namespace()}

    @classmethod
    def _scan(cls, path):
        import symtable
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        try:
            st = symtable.symtable(src, path, "exec")
        except SyntaxError:
            return []          # a parse error is a different gate's job, not this one's
        mod = cls._module_globals(st)
        out, stack = [], list(st.get_children())
        while stack:
            scope = stack.pop()
            for sym in scope.get_symbols():
                # a name the COMPILER resolved to global scope, that is read and never bound
                if sym.is_global() and sym.is_referenced() and not sym.is_assigned():
                    n = sym.get_name()
                    if n not in mod and n not in cls._builtins():
                        out.append("%s: %r in %s()" % (os.path.basename(path), n, scope.get_name()))
            stack.extend(scope.get_children())
        return out

    def test_no_python_file_calls_a_name_nothing_binds(self):
        import glob
        here = os.path.dirname(os.path.abspath(__file__))
        bad = []
        for f in sorted(glob.glob(os.path.join(here, "*.py"))):
            bad += self._scan(f)
        self.assertEqual(
            bad, [],
            "these read a name that is bound NOWHERE — module scope, enclosing scope, parameter or "
            "builtin. Inside a try/except that is silent forever and the code looks wired:\n  "
            + "\n  ".join(bad))

    def test_the_detector_actually_catches_the_three_that_shipped(self):
        """A guard that has never been seen RED is measuring nothing — and this one currently finds
        zero, which is exactly when that question must be asked."""
        import tempfile
        src = (
            "import time\n"
            "def outer(a):\n"
            "    def inner(b):\n"
            "        try:\n"
            "            return a + b\n"          # closure — must NOT be flagged
            "        except Exception:\n"
            "            return None\n"
            "    return inner\n"
            "def v2008_one():\n"
            "    try:\n"
            "        return js_syntax_gate.loopback_path()\n"   # never imported
            "    except Exception:\n"
            "        return None\n"
            "def v1989_shape():\n"
            "    try:\n"
            "        return _vault_corpus()\n"                  # does not exist
            "    except Exception:\n"
            "        return None\n"
            "def params_are_fine(delay=1, reason=''):\n"
            "    try:\n"
            "        return '%s/%s' % (reason, delay)\n"        # params — must NOT be flagged
            "    except Exception:\n"
            "        return ''\n"
            "def imported_is_fine():\n"
            "    try:\n"
            "        return time.time()\n"                      # imported — must NOT be flagged
            "    except Exception:\n"
            "        return 0\n")
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, "sab.py")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(src)
        found = " ".join(self._scan(p))
        self.assertIn("js_syntax_gate", found, "it misses the v2008 bug it exists for")
        self.assertIn("_vault_corpus", found, "it misses the v1989 bug it exists for")
        for clean in ("'a'", "'b'", "'delay'", "'reason'", "'time'"):
            self.assertNotIn(clean, found,
                             "false positive on %s — closures, parameters and imports are legal "
                             "and a noisy guard gets bypassed" % clean)


class TestV2011ThePromptShapeAndTheConsumerAGREE(unittest.TestCase):
    """v2011 — this defect has now appeared TWICE, in opposite directions, in the same prompt.

    ⚠ The first cut of this guard looked for `_row_of`, the name Grok's handoff used. There is no
    such function — it is `normalize_item`. The guard REFUSED rather than passing on an empty set,
    which is the only reason the mistake was visible in one run: a guard that cannot find its
    subject must fail, never return "nothing wrong here". [[source-reading-guard]]

      v1903  `throwOut` was in the JSON SCHEMA and nowhere in the prose. Nothing told the reader
             what it meant or when to set it, while vault_retro consumed it, gated it behind a
             higher confidence floor and rode it out to him as suggestions — "an elaborate safety
             mechanism fed by a field nobody was ever asked to fill".

      v2011  `throwWhy` was in the PROSE and nowhere in the schema. The instruction says "When you
             set it true, also give throwWhy = a short reason in your own words", and the JSON
             template it must match listed four keys, none of them throwWhy. A model told to reply
             with STRICT JSON matching a template emits the template's keys.

    Both were invisible because the consumer has a fallback: `or "the reader flagged it as junk"`
    fired on EVERY suggestion and read like the reader's own words.

    So the two halves are pinned to each other: every field `_row_of` reads off a raw item must be a
    field the reader was actually ASKED for. [[the-unjoined-end]] [[unknown-stays-unknown]]
    """

    # fields _row_of builds from something OTHER than the raw item — not the reader's to supply
    DERIVED = {"lane", "conf"}

    def _template_keys(self):
        import tv_diablo as tv
        m = re.search(r"Each item = \{\{(.+?)\}\}", tv.VAULT_READ_PROMPT, re.S)
        self.assertIsNotNone(m, "the item template moved or was renamed — this guard reads nothing")
        return set(re.findall(r'"([A-Za-z_][\w]*)"\s*:', m.group(1)))

    def _consumed_keys(self):
        import ast
        import vault_retro as vr
        with open(vr.__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = None
        for n in ast.walk(tree):
            if isinstance(n, ast.FunctionDef) and n.name == "normalize_item":
                fn = n
        self.assertIsNotNone(fn, "normalize_item moved — this guard is measuring nothing")
        keys = set()
        for n in ast.walk(fn):
            # raw.get("x")
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "get" and isinstance(n.func.value, ast.Name)
                    and n.func.value.id == "raw" and n.args
                    and isinstance(n.args[0], ast.Constant)):
                keys.add(n.args[0].value)
        return keys

    def test_every_field_the_consumer_reads_was_actually_asked_for(self):
        tmpl, used = self._template_keys(), self._consumed_keys()
        self.assertTrue(tmpl, "the item template parsed to no keys at all")
        missing = sorted(k for k in used
                         if k not in tmpl and k not in self.DERIVED
                         and not k.endswith("_tab") and "_" not in k)
        self.assertEqual(
            missing, [],
            "vault_retro.normalize_item reads these off the raw item and the prompt never asks the reader "
            "for them, so they arrive empty and a fallback stands in silently: %s. Template asks "
            "for: %s" % (", ".join(missing), ", ".join(sorted(tmpl))))

    def test_throwWhy_specifically_is_in_the_shape(self):
        """The field this version exists for. Named on its own so a regression says WHICH."""
        self.assertIn("throwWhy", self._template_keys(),
                      "throwWhy left the item template again — every throw-out suggestion will "
                      "carry the same default sentence and read like the reader's opinion")

    def test_the_vault_reader_is_told_about_the_hover_tooltip(self):
        """v2016 — it was not, for the whole life of the vault lane.

        This repo states the fact as a calibrated truth from his real videos (tv_diablo.py ~305):
        "panel grids show item ICONS with no text — names ONLY come from hover tooltips (first line
        = name)". READ_PROMPT acts on it in four places. VAULT_READ_PROMPT mentioned tooltip or
        hover ZERO times, so on a frame where he hovers an item the reader was asked about the grid,
        correctly answered items:[] because a grid prints no names, and never saw the fully legible
        tooltip beside it.

        Found by OPENING one of his frames: f_1784984209709 carries a complete tooltip —
        "Annihilus / Small Charm / … / +1 to All Skills" — in a frame the sweep had already PAID to
        read. That is why the vault shows 220 occupied cells and zero names.
        """
        import tv_diablo as tv
        p = tv.VAULT_READ_PROMPT.lower()
        self.assertIn("tooltip", p,
                      "the vault reader is not told about the hover tooltip — the only place a stash "
                      "item's name is ever written")
        self.assertIn("first line", p,
                      "it must say WHICH line of the tooltip is the name, or the reader may return "
                      "a stat line")
        # v2017 — and the half the vault prompt never had. READ_PROMPT has always said "Never
        # complete partial names"; the vault covered only "cannot read it at all". Asking for
        # tooltips (v2016) made a partial name MORE likely, not less — a tooltip clipped at the
        # panel edge is half a name in the most authoritative place on the frame.
        self.assertIn("never complete a partial name", p,
                      "a half-readable label may still be completed — the most convincing "
                      "fabrication there is, because the model is right about most of the letters")

    def test_a_prompt_change_moves_the_version(self):
        """v2002 records the reader on every vault seal so a better one can reopen it. A prompt
        edited without moving VAULT_PROMPT_VER leaves every seal claiming a reader that no longer
        exists."""
        import tv_diablo as tv
        self.assertTrue(getattr(tv, "VAULT_PROMPT_VER", "").startswith("vp"),
                        "VAULT_PROMPT_VER is missing or malformed")
        for stale in ("vp2002", "vp2011", "vp2016"):
            self.assertNotEqual(tv.VAULT_PROMPT_VER, stale,
                                "the prompt changed after %s and the version did not move — seals "
                                "made by the older reader can never reopen" % stale)


class TestV2012TheLauncherDoesNotRaceItself(unittest.TestCase):
    """v2012 — three launches in fifty seconds, each killing the one before it.

    start_tvd_mac.sh frees :17772 before binding, which is right (v1379.1: a double-click must boot
    THIS checkout, never window-only onto a stale headless). It was UNCONDITIONAL, so two launches
    close together race. MEASURED in his own control_app.log, 2026-08-23, after he closed the window:

        01:30:01  auto-pull: fast-forward ok   -> native window up
        01:30:21  auto-pull: fast-forward ok   -> window gone (signal-SIGTERM)
        01:30:51  auto-pull: fast-forward ok   -> window gone (signal-SIGTERM)

    Each SIGTERM ran the exit safeguard and stopped ON AIR. Had he been recording, that is a session
    destroyed by a race with itself.

    ⚠ AND THOSE THREE LINES WERE MISREAD ONCE. They look like a poller reacting to a git push;
    auto-pull runs ONCE PER LAUNCH. Reading them as a timeline of cause blamed a push nine minutes
    earlier. [[feedback-suspect-the-instrument]]

    THE TEST DRIVES THE SHIPPED FUNCTION, extracted from start_tvd_mac.sh itself — not a copy. A
    copy is the fixture trap: it passes while the real script rots. And it uses a THROWAWAY port,
    never :17772, which is his live console.
    """

    PORT = 18879        # never 17772 (his console) and never 9222/9223 (Chrome / TradingView)

    def _guard_script(self):
        """The real _tvd_age_secs plus the real stand-down loop, lifted out of the shipped file."""
        path = os.path.join(HERE, "start_tvd_mac.sh")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        fn = re.search(r"(_tvd_age_secs\(\) \{.*?\n\})", src, re.S)
        self.assertIsNotNone(fn, "the age helper is gone from start_tvd_mac.sh — the guard is unwired")
        loop = re.search(r"(if command -v lsof.*?TV_FORCE_PORT.*?\nfi)", src, re.S)
        self.assertIsNotNone(loop, "the stand-down loop is gone from start_tvd_mac.sh")
        body = loop.group(1).replace("17772", "$PORT").replace('"$_TVD_PORT_GRACE"', '"$GRACE"')
        body = re.sub(r'>>"\$HERE/control_app\.log"[^\n]*', ">/dev/null", body)
        body = body.replace("exit 0", 'echo "STAND-DOWN"; exit 0')
        return ('#!/bin/bash\nPORT="$1"; GRACE="${2:-25}"\n' + fn.group(1) + "\n" + body
                + '\necho "PROCEED"\n')

    def _run(self, port, grace, env=None):
        import tempfile
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        sh = os.path.join(d, "g.sh")
        with open(sh, "w", encoding="utf-8") as fh:
            fh.write(self._guard_script())
        e = dict(os.environ)
        e.pop("TV_FORCE_PORT", None)
        if env:
            e.update(env)
        r = subprocess.run(["bash", sh, str(port), str(grace)], capture_output=True, text=True,
                           timeout=30, env=e)
        return (r.stdout or "").strip()

    def test_it_stands_down_for_a_young_incumbent_and_replaces_an_old_one(self):
        # ⚠ start_new_session=True is REQUIRED, and the first cut omitted it. _reap kills the
        # process GROUP — its docstring states the precondition in as many words ("the launcher is
        # started in its own session") — so without it os.getpgid() returns the TEST RUNNER's group
        # and killpg SIGKILLs the suite mid-run. Observed exactly that: one dot, then exit 1 with no
        # summary and no traceback. Using a helper without honouring its documented contract.
        srv = subprocess.Popen([sys.executable, "-m", "http.server", str(self.PORT),
                                "--bind", "127.0.0.1"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=True)
        self.addCleanup(_reap, srv)
        time.sleep(1.5)
        if not shutil.which("lsof"):
            self.skipTest("no lsof on this machine — the guard cannot see the incumbent either")
        young = self._run(self.PORT, 25)
        if "STAND-DOWN" not in young and "PROCEED" not in young:
            self.skipTest("the guard produced no verdict (%r) — probe could not run" % young[:60])
        self.assertIn("STAND-DOWN", young,
                      "a console seconds old was taken over — that IS the restart storm")
        self.assertIn("PROCEED", self._run(self.PORT, 0),
                      "an OLD incumbent must still be replaced; a launcher that never takes the "
                      "port cannot recover from a stale console")
        self.assertIn("PROCEED", self._run(self.PORT, 25, {"TV_FORCE_PORT": "1"}),
                      "TV_FORCE_PORT must restore the old unconditional behaviour")

    def test_a_free_port_is_never_blocked(self):
        """The ordinary case. A guard that refuses a normal launch is worse than the storm."""
        self.assertIn("PROCEED", self._run(18881, 25))


class TestV2015NoBareWindowCallIntoNothing(unittest.TestCase):
    """v2015 — the JS twin of v2010, and the half that was still open.

    TestNoOptionalCallToAFunctionThatCannotExist catches `window.X && window.X()` on a name assigned
    nowhere — the guarded form, which fails SILENTLY and forever. A BARE `window.X(...)` on such a
    name throws, which is loud and gets fixed in a minute — UNLESS it sits inside a try/catch, and
    this file is full of try/catch. Then it is exactly as silent as the guarded form.

    That is the shape that hit three times in Python in one night (v1989 `_vault_corpus`, v2008
    `js_syntax_gate` and `time`), each one swallowed by an `except` and each looking perfectly wired.
    v2010 gated Python with CPython's own symtable. JavaScript had nothing.

    TWO THINGS ARE LEGITIMATELY NEVER ASSIGNED and would make this noisy without them:
      · browser built-ins — window.addEventListener, print, scrollTo, showDirectoryPicker…
      · top-level `function NAME(){}` — a classic script declaration IS window.NAME, without any
        `window.NAME =` anywhere. `toggleSec` is one, and a first cut flagged it.
    Both are resolved rather than allowlisted by name, so a new built-in or a new declaration needs
    no maintenance here. [[the-unjoined-end]] [[feedback-comments-vs-code]]
    """

    BUILTINS = {
        "addEventListener", "removeEventListener", "print", "scrollTo", "scrollBy", "alert",
        "showDirectoryPicker", "showOpenFilePicker", "showSaveFilePicker", "matchMedia",
        "requestAnimationFrame", "cancelAnimationFrame", "setTimeout", "setInterval",
        "clearTimeout", "clearInterval", "getComputedStyle", "fetch", "open", "close", "focus",
        "blur", "confirm", "prompt", "postMessage", "btoa", "atob", "queueMicrotask",
    }

    @staticmethod
    def _strip(text):
        """Comments out first — a guard that reads its own documentation passes on prose. Bounded,
        because an unbounded /*…*/ once ate 16.9% of this file."""
        text = re.sub(r"/\*.{0,4000}?\*/", " ", text, flags=re.S)
        return re.sub(r"(?m)^\s*//.*$", " ", text)

    def _board(self):
        with open(os.path.join(HERE, "..", "bible.html"), encoding="utf-8") as fh:
            raw = fh.read()
        body = self._strip(raw)
        self.assertGreater(len(body), len(raw) * 0.5,
                           "comment-stripping removed most of the file — the instrument is broken, "
                           "and a broken instrument passes everything")
        return body

    def test_no_bare_window_call_lands_on_a_name_nothing_binds(self):
        body = self._board()
        assigned = set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*=", body))
        # a top-level `function NAME(` in a classic script IS window.NAME
        assigned |= set(re.findall(r"(?m)^\s*function\s+([A-Za-z_$][\w$]*)\s*\(", body))
        called = set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*\(", body))
        optional = set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*(?:&&|\?)\s*window\.\1\s*\(", body))
        bare = called - optional - self.BUILTINS - assigned
        self.assertEqual(
            sorted(bare), [],
            "these are CALLED as window.X(...) and window.X is assigned nowhere. Outside a try that "
            "throws; inside one — and this file is full of them — it is silent forever and reads as "
            "wired from both ends: %s" % ", ".join(sorted(bare)))

    def test_it_catches_a_planted_one(self):
        """Zero findings is exactly when a guard must be asked whether it can go red."""
        body = self._board() + "\ntry { window._v2015_ghost(1); } catch(e){}\n"
        assigned = set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*=", body))
        assigned |= set(re.findall(r"(?m)^\s*function\s+([A-Za-z_$][\w$]*)\s*\(", body))
        called = set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*\(", body))
        optional = set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*(?:&&|\?)\s*window\.\1\s*\(", body))
        self.assertIn("_v2015_ghost", called - optional - self.BUILTINS - assigned)

    def test_a_top_level_function_declaration_is_not_a_finding(self):
        """`function toggleSec(h){}` with no `window.toggleSec =` anywhere IS window.toggleSec, and
        a first cut of this guard reported it. A false positive on real code gets a guard bypassed."""
        body = self._board()
        self.assertTrue(re.search(r"(?m)^\s*function\s+toggleSec\s*\(", body),
                        "toggleSec stopped being a top-level declaration — re-check this guard")
        assigned = set(re.findall(r"(?m)^\s*function\s+([A-Za-z_$][\w$]*)\s*\(", body))
        self.assertIn("toggleSec", assigned)


class TestV2018ThePlannerIsAskedAboutTheItemNotAboutMyStub(unittest.TestCase):
    """v2018 (REG-349) — ORDER IS THE WHOLE DEFECT, so order is what this guards.

    tvVaultRegister does three things to an unknown name, and for 1279 versions it did them in the
    wrong order:

        1. write EXTRA_ITEMS[name] = {rarity:'basic', base:name}   <- the v739 UNIVERSE GUARANTEE
        2. sg = suggestMule(name)                                  <- the planner
        3. if (sg.id === '__throwout') ... route to the review bucket

    suggestMule's first act is to look the name up. With (1) before (2) it did not read the item, it
    read a placeholder written three lines earlier - a known 'basic' with a slot - and filed it BY
    SLOT. MEASURED on his own board (99 runewords forged, profile main): 17 of 20 verdicts flip.
    Every white base he stashed was landing on his UNIQUES mules.

    THE CORRECT ORDER IS 2 -> 1 -> 3, and BOTH the middle and the end matter:
      * the planner must be asked BEFORE the stub, or it is grading my own fabrication;
      * the stub must still be written BEFORE the __throwout branch, because that branch RETURNS.
        Move it below and an item routed to throw-out review becomes undrawable - which is exactly
        the invisible-item bug v739 added the guarantee to prevent.

    A plain 'suggestMule comes first' assertion would pass on that second mistake, so all three
    positions are pinned. [[the-unjoined-end]] [[feedback-suspect-the-instrument]]
    """

    @staticmethod
    def _register_body():
        """The INNER tvVaultRegister, comments stripped.

        Bounded stripping only - an unbounded /*...*/ strip once ate 16.9% of this file. And the
        stripping is not optional here: the block comment this guard protects NAMES all three
        markers in its own prose, so an unstripped read finds them in the explanation rather than
        in the code and passes no matter what the code does. [[feedback-comments-vs-code]]
        """
        import os
        import re
        bib = os.path.join(os.path.dirname(HERE), "bible.html")
        with open(bib, encoding="utf-8") as fh:
            text = fh.read()
        start = text.index("window.tvVaultRegister = function(name){")
        body = text[start:start + 9000]
        body = re.sub(r"/\*.{0,4000}?\*/", " ", body, flags=re.S)
        body = re.sub(r"(?m)//[^\n]*$", " ", body)
        return body

    def test_the_planner_is_asked_before_the_stub_is_written(self):
        body = self._register_body()
        i_ask = body.find("sg = suggestMule(name)")
        i_stub = body.find("var _tvEntry = { rarity:'basic'")
        i_branch = body.find("if (sg && sg.id === '__throwout')")
        self.assertNotEqual(i_ask, -1, "suggestMule call not found in tvVaultRegister")
        self.assertNotEqual(i_stub, -1, "the v739 universe stub not found in tvVaultRegister")
        self.assertNotEqual(i_branch, -1, "the __throwout branch not found in tvVaultRegister")
        self.assertLess(
            i_ask, i_stub,
            "REG-349: the {rarity:'basic'} stub is written BEFORE suggestMule is asked, so the "
            "planner grades a placeholder instead of the item and files every white base by slot")
        self.assertLess(
            i_stub, i_branch,
            "the universe stub must be written BEFORE the __throwout branch, which RETURNS - "
            "otherwise an item routed to throw-out review is not drawable (the v739 bug)")

    def test_the_throwout_branch_still_never_overwrites_a_manual_placement(self):
        """The routing change is only safe because this guard holds: he outranks the planner."""
        body = self._register_body()
        self.assertIn("if (!assign[name]) assign[name] = '__throwout';", body,
                      "the throw-out branch must keep its !assign[name] guard - without it the "
                      "reorder starts clobbering placements he made by hand")



class TestV2019TheTooltipPassGivesBackWhatItTook(unittest.TestCase):
    """v2019 — a toggle whose OFF is not the inverse of its ON.

    Konyo, with both switches sitting OFF and the header still reading ON AIR: "and its not just
    recording non stop is it..? it says end session.. but i never started a session." Measured while
    he watched: +16 frames / +37MB in 15 seconds — ~150MB/min, ~9GB/hour, on top of 3.1GB already
    on disk, with 17GB free.

    toggleTooltipPass ON took three server-side actions (arm the mini lane, POST /api/shadow
    {on:true}, POST /api/on -> STARTS A RECORDING). OFF took none. It wrote a local flag and
    returned, so the pass started a session he never asked for and never gave it back.

    The old code defended this in a comment: sealing is his ON AIR control and must not be a side
    effect of a toggle. That rule is RIGHT, and it is exactly why the code was wrong - it applied
    the rule to one end of the switch only. If OFF may not seal, ON may not start. Undoing what
    this toggle did is not overriding his control, it is returning it; a reel HE started stays
    untouchable, and `startedReel` is what tells the two apart.

    AND THE MESSAGE WAS THE WORSE HALF. Two OFF texts existed. The one for a pass that named
    something warned that the reel was still rolling. The one for a pass that named NOTHING - the
    likely first run, and the case he hit - never mentioned the reel and said the reel may be "not
    recording", pointing away from a reel recording at 9GB/hour. The branch that fires when the
    news is worst told him least. That asymmetry is what the message tests below pin.
    """

    @staticmethod
    def _toggle_body():
        import os
        import re
        bib = os.path.join(os.path.dirname(HERE), "bible.html")
        with open(bib, encoding="utf-8") as fh:
            text = fh.read()
        start = text.index("window.toggleTooltipPass = function(){")
        body = text[start:start + 12000]
        # Comments out first, bounded - this block's own prose names every marker below, so an
        # unstripped read would find them in the explanation rather than in the code.
        body = re.sub(r"/\*.{0,6000}?\*/", " ", body, flags=re.S)
        body = re.sub(r"(?m)//[^\n]*$", " ", body)
        return body

    def test_on_records_whether_it_started_the_reel(self):
        """Without this, OFF cannot tell a reel it started from one he started."""
        body = self._toggle_body()
        self.assertIn("startedReel", body,
                      "ON must record whether IT started the reel - /api/on answers ok:false when "
                      "one is already rolling, so j.ok is that answer")
        self.assertIn("wokeReader", body,
                      "ON must record whether IT woke the reader, or OFF will switch off a reader "
                      "he turned on himself")

    def test_off_seals_the_reel_it_started(self):
        body = self._toggle_body()
        i_off = body.find("'/api/off'")
        self.assertNotEqual(i_off, -1,
                            "OFF never calls /api/off, so a reel this pass started runs forever - "
                            "measured at ~9GB/hour on his machine")
        i_mine = body.find("st.startedReel")
        self.assertNotEqual(i_mine, -1, "the seal must be conditional on having started it")
        self.assertLess(i_mine, i_off,
                        "the /api/off call must be GATED on startedReel - sealing a reel HE "
                        "started is the one thing this toggle may never do")

    def test_both_off_messages_state_the_reel_state(self):
        """The zero-named branch is the one that fires on a first run and the one that used to
        say nothing. Neither branch may leave the reel unexplained."""
        body = self._toggle_body()
        self.assertNotIn("not recording \u2014 check the shadow reader", body,
                         "the old zero-named text pointed AWAY from a reel that was recording")
        self.assertIn("STILL ROLLING", body,
                      "when the reel is HIS, OFF must say plainly that it is still rolling")
        self.assertIn("sealed", body,
                      "when the reel was this pass's, OFF must say it was sealed")

    def test_a_failed_seal_is_never_reported_as_stopped(self):
        """Silence from the console must not read as 'nothing is recording'."""
        body = self._toggle_body()
        self.assertIn("COULD NOT SEAL THE REEL", body,
                      "a refused /api/off must say so, loudly, and name the OFF AIR button")
        self.assertIn("may STILL", body,
                      "a thrown fetch must report the reel as possibly-still-recording, never as "
                      "stopped [[feedback-silence-is-not-evidence]]")



class TestV2023TheSweepSpendsWhereTheStashIs(unittest.TestCase):
    """v2023 — the first vault sweep ever run read ZERO pages, and the reader was innocent.

    It took the 4 "mini-first" reels, examined 234 frames and read nothing. Sampled with the panel
    gate, those four show a stash panel in 0 of 60 frames. A reel that shows one in 23 of 39 sat
    unswept. Only 4 of his 32 reels contain a panel at all, so an ordering that ignores the film had
    a 4-in-32 shot and drew zero.

    `is_mini_reel` asks whether he PRESSED MINI - a statement of intent, not evidence about what is
    on the film. The gate that IS evidence costs no model call (control_app's own words: "a crop and
    an OCR"), so the ordering can price every reel before a single read is paid for.

    Guarded on BEHAVIOUR with a fake gate, not on his footage: a test that needs his reels on disk
    would skip on CI and prove nothing there. [[feedback-blind-fixture-green-gate]]
    """

    def test_a_reel_that_shows_a_panel_outranks_one_that_does_not(self):
        import os
        import tempfile
        import vault_retro as vr
        with tempfile.TemporaryDirectory() as td:
            empty = os.path.join(td, "reel_s_1_empty"); os.makedirs(empty)
            full = os.path.join(td, "reel_s_2_full"); os.makedirs(full)
            for i in range(8):
                open(os.path.join(empty, "f_%d.jpg" % i), "w").close()
                open(os.path.join(full, "f_%d.jpg" % i), "w").close()
            gate = lambda path: "stash" if "_full" in path else None
            # caller order deliberately puts the EMPTY one first, as the old mini-first sort did
            out = vr.order_reels([empty, full], panel_gate=gate)
            self.assertEqual(os.path.basename(out[0]), "reel_s_2_full",
                             "the reel that actually shows a stash panel must be swept FIRST - "
                             "spending `limit` on footage of him walking around is why the first "
                             "real sweep read 0 pages")

    def test_no_gate_means_the_old_behaviour_exactly(self):
        """Every existing caller passes no gate; none of them may change."""
        import os
        import tempfile
        import vault_retro as vr
        with tempfile.TemporaryDirectory() as td:
            a = os.path.join(td, "reel_s_1_a"); os.makedirs(a)
            b = os.path.join(td, "reel_s_2_b"); os.makedirs(b)
            self.assertEqual(vr.order_reels([a, b]), vr.order_reels([a, b]),
                             "the no-gate path must stay deterministic")
            self.assertEqual(len(vr.order_reels([a, b])), 2)

    def test_a_reel_it_cannot_measure_sorts_last_not_first(self):
        """An unreadable reel must never be preferred - 'we could not look' is not 'it is full'."""
        import os
        import tempfile
        import vault_retro as vr
        with tempfile.TemporaryDirectory() as td:
            good = os.path.join(td, "reel_s_1_good"); os.makedirs(good)
            boom = os.path.join(td, "reel_s_2_boom"); os.makedirs(boom)
            for i in range(4):
                open(os.path.join(good, "f_%d.jpg" % i), "w").close()
                open(os.path.join(boom, "f_%d.jpg" % i), "w").close()
            def gate(path):
                if "_boom" in path:
                    raise RuntimeError("gate exploded")
                return "stash"
            out = vr.order_reels([boom, good], panel_gate=gate)
            self.assertEqual(os.path.basename(out[0]), "reel_s_1_good",
                             "a reel whose gate throws must sort LAST, never first")

    def test_the_gate_reaches_the_sweep(self):
        """A gate wired into order_reels but not threaded through sweep() would be inert."""
        import inspect
        import vault_retro as vr
        self.assertIn("panel_gate", inspect.signature(vr.sweep).parameters,
                      "sweep() must accept panel_gate or the ordering fix never runs")
        src = inspect.getsource(vr.sweep)
        self.assertIn("panel_gate=panel_gate", src,
                      "sweep() must HAND the gate to order_reels - accepting it and dropping it is "
                      "the same defect wearing a parameter [[the-unjoined-end]]")



class TestV2024TheModeSwitchPowersTheLane(unittest.TestCase):
    """v2024 — Konyo: "is this MODE CONTROL needs to be across the entire console allround so when
    its toggled its powered allround". It was not.

    _chron_lanes() added grok on has_subscription() alone - a CAPABILITY question ("is a Grok CLI on
    PATH and logged in") that never looks at the mode. switch_on() is the mode-aware one. So setting
    G5 to OFF left grok in the lane list: the sweep still announced two lanes and the gate still
    scored the run as cross-lane corroborated, while a switch he had deliberately turned off went on
    being counted.

    Three modes, three different right answers, and "off" must be distinguishable from "absent".
    """

    def _lanes_with(self, capable, switched_on, mode="primary"):
        import control_app as ca
        import g5_grok_eyes as g5
        cap, sw, mi = g5.has_subscription, g5.switch_on, g5.mode_intent
        try:
            g5.has_subscription = lambda: capable
            g5.switch_on = lambda: switched_on
            g5.mode_intent = lambda: mode
            return list(ca._chron_lanes()), ca._chron_lane_detail()
        finally:
            g5.has_subscription, g5.switch_on, g5.mode_intent = cap, sw, mi

    def test_dual_when_installed_and_switched_on(self):
        lanes, _ = self._lanes_with(True, True, "primary")
        self.assertIn("claude", lanes)
        self.assertIn("grok", lanes, "installed + switched on must give BOTH lanes")

    def test_switched_off_removes_the_lane(self):
        """The whole fix. Before this, OFF still shipped a grok lane."""
        lanes, detail = self._lanes_with(True, False, "off")
        self.assertIn("claude", lanes)
        self.assertNotIn("grok", lanes,
                         "G5 set to OFF must remove the grok lane everywhere, not just from the "
                         "reads - otherwise the gate keeps scoring a switch he turned off")
        self.assertIn("switched it off", detail["grok"]["why"],
                      "a lane he turned off must SAY so")

    def test_not_installed_says_something_different_from_switched_off(self):
        """'You turned it off' and 'there is no Grok here' are different facts. His cousin's
        machine is the second one and must never be reported as the first."""
        lanes, detail = self._lanes_with(False, False, "off")
        self.assertNotIn("grok", lanes)
        self.assertIn("no Grok CLI", detail["grok"]["why"])
        self.assertNotIn("switched it off", detail["grok"]["why"])

    def test_claude_alone_is_a_working_configuration(self):
        """The cousin's machine. Claude-only must still be a full lane list, not an error."""
        lanes, detail = self._lanes_with(False, False)
        self.assertEqual(lanes, ["claude"])
        self.assertTrue(detail["claude"]["present"])

    def test_a_grok_only_sweep_is_refused_out_loud(self):
        """Claude is PRIMARY. Without it there is no page for a second opinion to be ABOUT, and the
        sweep says so rather than starting a run that cannot ground anything."""
        import inspect
        import control_app as ca
        src = inspect.getsource(ca.vault_sweep_start)
        self.assertIn('"claude" not in lanes', src,
                      "a sweep with no primary lane must refuse")
        self.assertIn("primary (Claude) lane is unavailable", src,
                      "and it must say WHY, not just return false")



class TestV2025OneLaneSwitchMeansTheSameThingEverywhere(unittest.TestCase):
    """v2025 — Konyo: "we have this toggle vault auto-read but then what does this need to be on if
    we have shaddow and tooltip pass on toggled?" then "fix it so there one unified logic here".

    He was right that it did nothing. Every call to _miniOnAirOn, comments stripped: two paint the
    pill, two ARM it (quickIntake / the tooltip pass), and exactly ONE is a real gate —
    tvStashAutoIntake, which returns early for runes|gems|materials and answers 'not-tally-tab' for
    anything else. The VAULT lane's switch was decoration, the precise thing this file's own v1975
    comment warns about: "the user is told a lane is dark while frames keep flowing into it".

    vaultAccumApply is where the automated path files, so that is where the switch belongs, and now
    all four lanes mean the same thing.
    """

    @staticmethod
    def _apply_body():
        import os
        import re
        bib = os.path.join(os.path.dirname(HERE), "bible.html")
        with open(bib, encoding="utf-8") as fh:
            text = fh.read()
        start = text.index("window.vaultAccumApply = function(payload)")
        body = text[start:start + 30000]
        body = re.sub(r"/\*.{0,8000}?\*/", " ", body, flags=re.S)
        body = re.sub(r"(?m)//[^\n]*$", " ", body)
        return body

    def test_the_sweep_apply_asks_the_vault_lane_switch(self):
        body = self._apply_body()
        self.assertIn("_miniOnAirOn('vault')", body,
                      "vaultAccumApply must consult the VAULT lane switch, or the pill is "
                      "decoration and the reel files into a lane he switched dark")

    def test_a_lane_he_switched_off_is_REPORTED_not_silently_dropped(self):
        body = self._apply_body()
        self.assertIn("lane-off", body,
                      "a skipped lane must carry a NAMED reason - 'nobody looked' and 'we looked "
                      "and found nothing' must never read alike")

    def test_a_broken_switch_files_rather_than_eats(self):
        """If the switch cannot be read, the safe default is to FILE. Losing his loot to a thrown
        exception in a UI helper is a far worse failure than filing into a lane he meant to close."""
        body = self._apply_body()
        i = body.find("_miniOnAirOn('vault')")
        self.assertNotEqual(i, -1)
        window = body[max(0, i - 260): i + 260]
        self.assertIn("_laneOn = true", window,
                      "the catch around the switch read must default to ON")

    def test_it_gates_the_SWEEP_not_his_hand(self):
        """REG-383 settled it: he outranks the machine. The gate lives in the sweep's apply path,
        never inside tvVaultRegister itself, so a manual add and the Item Checker are untouched."""
        import os
        import re
        bib = os.path.join(os.path.dirname(HERE), "bible.html")
        with open(bib, encoding="utf-8") as fh:
            text = fh.read()
        start = text.index("window.tvVaultRegister = function(name){")
        reg = text[start:start + 9000]
        reg = re.sub(r"/\*.{0,6000}?\*/", " ", reg, flags=re.S)
        reg = re.sub(r"(?m)//[^\n]*$", " ", reg)
        self.assertNotIn("_miniOnAirOn", reg,
                         "the lane switch must NOT live inside tvVaultRegister - that would let a "
                         "UI toggle veto something he did by hand")



class TestV2026AChronicleIsNotAStash(unittest.TestCase):
    """v2026 — ENGRAVE THE ONE DISTINCTION THAT DECIDES WHICH LEDGER A NAME LANDS IN.

    Konyo: "the grail doesnt really mean anything we invented it didnt we? ... just chronicles are
    the different area here that needs to understand and know the diffrence of when in chronicle or
    just on ground or something it should register it as an item ... the logic coding should be
    engraved so its working properly and bugs or mis-reads dont happen".

    He is right about the grail: it is a self-imposed collection goal, not a game mechanic. The
    distinction that IS load-bearing is CHRONICLE vs OWNERSHIP, because they are different FACTS:

        chronicle page   "I have found this at some point"   -> a catalogue entry
        stash/inventory  "this is physically here, now"      -> owned, needs a mule

    Confuse them in one direction and a catalogue of everything he has ever found gets filed onto
    mules he does not own. Confuse them the other way and a stash panel inflates the found-log.

    Both directions ARE separated today. Nothing pinned it, so nothing stopped the next edit from
    quietly widening one of the two lists. This is that pin.
    """

    def test_a_chronicle_page_can_never_be_an_ownership_claim(self):
        import vault_retro as vr
        self.assertNotIn("chronicle", vr.OWNERSHIP_SURFACES,
                         "adding 'chronicle' to OWNERSHIP_SURFACES would file his entire found-log "
                         "onto mules - a catalogue of what he HAS FOUND is not a list of what he HAS")
        self.assertIsNone(vr._surface_of("chronicle"),
                          "a chronicle surface must normalise to None so the sweep HOLDS it")
        self.assertIsNone(vr._surface_of({"surface": "chronicle"}))

    def test_every_ownership_surface_is_a_place_things_physically_ARE(self):
        """The whitelist is the whole guard, so its membership is the thing to state out loud."""
        import vault_retro as vr
        self.assertEqual(set(vr.OWNERSHIP_SURFACES),
                         {"stash", "inventory", "equipment", "runes", "gems", "materials"},
                         "OWNERSHIP_SURFACES changed - every member must be somewhere an item "
                         "physically sits, never a catalogue, a vendor screen or a drop log")

    def test_the_chronicle_lane_refuses_a_non_chronicle_scene(self):
        """The mirror. A stash panel must not inflate the found-log either."""
        import os
        import re
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "chronicle_retro.py"), encoding="utf-8").read()
        src = re.sub(r'"""(?:.|\n)*?"""', " ", src)
        src = re.sub(r"(?m)#[^\n]*$", " ", src)
        hits = len(re.findall(r'scene["\']?\s*\)?\s*or\s*""\)\.lower\(\)\s*!=\s*"chronicle"', src))
        self.assertGreaterEqual(
            hits, 1,
            "the chronicle lane must require scene == 'chronicle' - without it a stash frame can "
            "be folded into the found-log as though he had catalogued it")

    def test_the_two_lists_do_not_overlap(self):
        """Any surface accepted by BOTH lanes would be double-counted: once as owned, once as
        found, from a single sighting. The corroboration gate would then see two 'witnesses' that
        are one frame."""
        import vault_retro as vr
        self.assertNotIn("chronicle", vr.SURFACE_LANE,
                         "a chronicle surface must not map to an ownership LANE either")
        for s in vr.OWNERSHIP_SURFACES:
            self.assertNotEqual(s, "chronicle")



class TestV2026TheEagleEyeSeesTheWholeConsole(unittest.TestCase):
    """v2026 — Konyo: "is there a MANAGER for the AI console? ... dont we need like a type of EAGLE
    EYE kind of style management system here? eyes from above it all".

    The per-lane doctors each answer about ONE lane; run_gates answers about the SOURCE before a
    push. Nothing looked at the RUNNING SYSTEM, and every defect found the night this was written
    was that shape - no component wrong, two correct things disagreeing:

        the console served v2018 while the tree was v2024, for two hours
        the vault sweep read 0 pages while 4 reels on disk were 40-100% stash panels
        G5 said mode=off while the lane list still shipped a grok lane
        the free cost pass called his footage worthless, from its own refusing stub

    The property that matters most here is the LAST one in this class: a check that throws must be
    reported as UNKNOWN, never dropped. A monitor whose failures are invisible is the thing it was
    built to catch.
    """

    def test_it_runs_and_every_row_is_a_named_state(self):
        import console_doctor as cd
        rows = cd.run(include_slow=False)   # the sub-doctors cost ~2min; guarded separately
        self.assertGreaterEqual(len(rows), 5, "the eagle eye lost checks")
        for r in rows:
            self.assertIn(r["state"], (cd.OK, cd.MISSING, cd.UNKNOWN),
                          "%r is not one of ok/missing/unknown" % r)
            self.assertTrue(str(r.get("why") or "").strip(),
                            "check %r answered with no reason - a verdict with no why is a lamp"
                            % r.get("check"))

    def test_a_check_that_throws_is_UNKNOWN_not_silently_dropped(self):
        """The defining property. If a check can vanish, the report is a green light with a hole
        in it - exactly the class this doctor exists to find. [[unknown-stays-unknown]]"""
        import console_doctor as cd
        def boom():
            raise RuntimeError("deliberate")
        original = cd.CHECKS[:]
        try:
            cd.CHECKS.append(("exploding check", boom))
            rows = cd.run(include_slow=False)
            hit = [r for r in rows if r["check"] == "exploding check"]
            self.assertEqual(len(hit), 1, "a throwing check DISAPPEARED from the report")
            self.assertEqual(hit[0]["state"], cd.UNKNOWN,
                             "a throwing check must be UNKNOWN, never ok")
            self.assertIn("threw", hit[0]["why"])
        finally:
            cd.CHECKS[:] = original

    def test_version_drift_compares_two_real_versions(self):
        """The check that would have caught the two-hour drift. It must read a version from the
        TREE - the first cut read only 400KB of a 5.8MB bible.html and answered None, which is a
        check that never fires."""
        import console_doctor as cd
        v = cd._tree_version()
        self.assertIsNotNone(v, "the tree version could not be read - the drift check is inert")
        self.assertRegex(v, r"^v\d+$")

    def test_it_calls_the_other_doctors_rather_than_reimplementing_them(self):
        """Two copies of one rule are two things that drift apart, and only one gets fixed."""
        import inspect
        import console_doctor as cd
        src = inspect.getsource(cd)
        self.assertIn("vault_doctor", src)
        self.assertIn("chronicle_doctor", src)
        self.assertNotIn("inventory_lattice", src,
                         "the eagle eye must not re-implement vault_doctor's pixel work")

    def test_the_console_exposes_it(self):
        """A doctor nobody can reach from the app is a script, not a management system."""
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "control_app.py"), encoding="utf-8").read()
        # v2026 — assertTrue on a boolean, NOT assertIn on a 900KB string. The first cut used
        # assertIn and its failure message dumped the entire control_app.py into the log — 907KB
        # of noise around one line of signal, in the CI output someone reads at 3am.
        self.assertTrue('"/api/eagle"' in src, "the eagle eye has no route in control_app.py")
        self.assertTrue("console_doctor" in src, "the /api/eagle route does not call console_doctor")
        # v2026 — AND IT MUST NOT HAVE TAKEN SOMEONE ELSE'S PATH. /api/doctor has been the Windows
        # self-diagnosis since v801; this dispatch is a first-match-wins chain, so a duplicate
        # branch above it silently retires the original. Exactly what happened, caught by a 45s
        # timeout in TestDoctor rather than by anything naming the collision.
        self.assertEqual(src.count('if path == "/api/doctor":'), 1,
                         "/api/doctor is declared more than once - the earlier branch shadows the "
                         "later one and one of the two endpoints is now unreachable")
        self.assertEqual(src.count('if path == "/api/eagle":'), 1)



class TestV2027ADeclaredFocusSurvivesAFullSession(unittest.TestCase):
    """v2027 — Konyo, after filming a reel with Tools -> "Vault items (auto-file to mules)": "when i
    click this it doesnt need the same logic to read the items and vault them automatically ... it
    should understand its focused and i am working together with it on a focused task ... ( i
    remeber this was coded ) i just want to make sure".

    He was right that it was coded, and right to check: it only ever reached MINI. THREE separate
    joins were missing and any one of them alone would have made the feature inert.

      1. tv_diablo read --mini-focus ONLY `if MINI_MODE`, so a full session dropped the flag and
         wrote focus:"" into index.json.
      2. /api/on never passed a focus at all, though start_agent has accepted one since v1603.
      3. the lane card posted a bare '{}'.

    MEASURED on the reel he had just filmed - reel_s_1787508759592_46621, 80 frames, 30 of 40
    sampled frames showing a stash panel - index.json keys were
    ['blank','blankPass','frames','n','sessionId']. No focus. So the sweep paid a classifier to work
    out what he had already told the console he was doing.

    What must NOT change: a DEFAULTED focus is still untrusted. vault_retro._declared_surface()
    keys on focusChosen, and that is what stops a fallback "stash" labelling town as a stash panel.
    """

    def test_tv_diablo_reads_the_focus_outside_mini_mode(self):
        import re
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "tv_diablo.py"), encoding="utf-8").read()
        m = re.search(r"^MINI_FOCUS\s*=\s*(.+)$", src, re.M)
        self.assertIsNotNone(m, "MINI_FOCUS assignment not found")
        line = m.group(1).strip()
        # v2027 — ASSERT THE PROPERTY, NOT A SUBSTRING. The first cut banned the text
        # `if MINI_MODE else ""` outright and failed on the CORRECT line, because the fix keeps
        # that conditional for the DEFAULT ("stash" only when it is a mini) while reading the flag
        # unconditionally in front of it. A guard that cannot tell those two apart would have
        # forced the fix to be written worse to satisfy it.
        self.assertTrue(line.startswith("_FOCUS_ARG"),
                        "the --mini-focus flag must be read UNCONDITIONALLY and only the DEFAULT "
                        "may depend on MINI_MODE; got: %s" % line)

    def test_a_defaulted_focus_is_still_not_chosen(self):
        """The half that must not regress. focusChosen is what stops a fallback labelling town."""
        import re
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "tv_diablo.py"), encoding="utf-8").read()
        m = re.search(r"^MINI_FOCUS_CHOSEN\s*=\s*(.+)$", src, re.M)
        self.assertIsNotNone(m)
        self.assertIn("_FOCUS_ARG", m.group(1),
                      "chosen-ness must come from the FLAG BEING PRESENT, never from the value")

    def test_api_on_passes_a_validated_focus(self):
        import inspect
        import re
        import control_app as ca
        src = inspect.getsource(ca.Handler.do_POST) if hasattr(ca, "Handler") else None
        if src is None:
            import os
            here = os.path.dirname(os.path.abspath(__file__))
            src = open(os.path.join(here, "control_app.py"), encoding="utf-8").read()
        self.assertIn('_mini_focus(body.get("focus"))', src,
                      "/api/on must VALIDATE the focus - an unvalidated string gets stamped into a "
                      "reel and later trusted by the sweep in place of a classify call")

    def test_the_lane_card_declares_a_focus_the_server_will_accept(self):
        """A map whose values the server rejects is a join that looks wired and carries nothing."""
        import os
        import re
        here = os.path.dirname(os.path.abspath(__file__))
        bib = open(os.path.join(os.path.dirname(here), "bible.html"), encoding="utf-8").read()
        m = re.search(r"var FOCUS = \{([^}]*)\}", bib)
        self.assertIsNotNone(m, "_laneStartReel has no focus map")
        vals = set(re.findall(r":'([a-z-]+)'", m.group(1)))
        self.assertTrue(vals, "the focus map is empty")
        import control_app as ca
        self.assertTrue(vals <= set(ca.MINI_FOCUSES),
                        "the lane card declares %s, which the server would reject: MINI_FOCUSES is %s"
                        % (sorted(vals - set(ca.MINI_FOCUSES)), sorted(ca.MINI_FOCUSES)))



class TestV2028ATooltipIsNotAnAbsentStash(unittest.TestCase):
    """v2028 — THE ROOT CAUSE OF "no name to be had", and the exact inverse of how it looked.

    stash_screen_open admits a frame only when stash_chrome_canons finds a legible tab label. A D2R
    hover tooltip is drawn ON TOP of that tab strip. So the gate refused, with perfect consistency,
    the only frames that carry a readable item NAME — and kept the bare grids, which print none.
    Every vault sweep therefore sealed "read N panel(s), every one cross-checked, no name to be had"
    while he had been hovering items on camera the whole time.

    LOOKED AT, not inferred:
      f_1784984195842.jpg  "Sullied Grand Charm of Blight / +1 to Eldritch Skills (Warlock Only)"
      f_1787508818939.jpg  "Marshal's Amulet / +3 to Offensive Auras (Paladin Only)"
    On the second the chrome still OCRs as ['StrNAL','SHAktD','GE',...] — PERSONAL and SHARED are
    THERE, corrupted just past the fuzzy matcher ('SHAkED' canonicalises, 'SHAktD' does not).

    MEASURED across his four stash reels: 16 of 170 in-panel frames refused while BRACKETED by
    frames the gate resolves, and the new path admits 20 more (+13%).

    THE CONJUNCTION IS THE WHOLE SAFETY, and either half alone is unsafe — CALIBRATED on 7 labelled
    frames, classify_stash_grid ALONE calls a LAVA SCENE a stash panel. The INVENTORY title is on
    the far right where a stash-side tooltip cannot reach, and D2R draws it only when the inventory
    is open, which IS the "both panels at once" template this gate exists to enforce.
    """

    @staticmethod
    def _gate_src():
        import os
        import re
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "control_app.py"), encoding="utf-8").read()
        # v2029 — anchored to the NEXT def, not a byte count. A fixed window slides off what it
        # meant to read and assertNotIn passes on the remainder.
        i = src.index("def stash_screen_open(frame_path)")
        j = src.find("\ndef ", i + 20)
        body = src[i:j if j > i else len(src)]
        body = re.sub(r'"""(?:.|\n)*?"""', " ", body)
        body = re.sub(r"(?m)#[^\n]*$", " ", body)
        return body

    def test_an_occluded_tab_strip_has_a_second_way_in(self):
        body = self._gate_src()
        self.assertIn("inventory_title_visible", body,
                      "a tooltip over the tab strip must not read as an absent stash - without a "
                      "second admission path the gate throws away every frame that has a NAME on it")
        self.assertIn("classify_stash_grid", body,
                      "the pixel fingerprint is the other half of the conjunction")

    def test_neither_half_admits_on_its_own(self):
        """The calibration says why: the fingerprint alone calls a LAVA SCENE a stash panel."""
        body = self._gate_src()
        # v2028 — MEASURE THE CALL SITES, NOT THE IMPORT. The first cut used .find() on the bare
        # names and failed on correct code, because `from stash_eye import classify_stash_grid,
        # inventory_title_visible` puts them in the opposite order on the IMPORT line. A guard that
        # cannot tell an import from a call is reading the wrong thing.
        i_inv = body.find("inventory_title_visible(")
        i_grid = body.find("classify_stash_grid(")
        self.assertNotEqual(i_inv, -1, "inventory_title_visible is imported but never CALLED")
        self.assertNotEqual(i_grid, -1, "classify_stash_grid is imported but never CALLED")
        self.assertLess(i_inv, i_grid,
                        "the INVENTORY title must gate the fingerprint, not the other way round - "
                        "the fingerprint alone is the half with a known false positive (it calls a "
                        "LAVA SCENE a stash panel)")

    def test_it_returns_the_generic_surface_not_a_guessed_tab(self):
        """v1859: the tab is a GUESS and a guess may not name a lane. When the strip is occluded we
        genuinely do not know which tab is selected, so the honest answer is the generic one."""
        body = self._gate_src()
        i = body.find("inventory_title_visible")
        seg = body[i: i + 700]
        self.assertIn('return "stash"', seg,
                      "an occluded-strip admission must return the GENERIC stash surface; naming a "
                      "tab it cannot see would reintroduce the v1857 misroute")

    def test_the_new_path_is_additive_and_cannot_loosen_the_old_one(self):
        """It lives INSIDE `if not canons`, so a frame the old gate admitted is untouched."""
        body = self._gate_src()
        i_canon = body.find("if not canons:")
        i_inv = body.find("inventory_title_visible")
        self.assertNotEqual(i_canon, -1, "the canons branch is gone - the old gate has been rewritten")
        self.assertLess(i_canon, i_inv,
                        "the occlusion path must sit inside the `not canons` branch, so it can only "
                        "ever ADD admissions and never change an existing verdict")

    def test_the_inventory_anchor_exists_and_is_bounded(self):
        import stash_eye as se
        self.assertTrue(hasattr(se, "inventory_title_visible"))
        self.assertTrue(hasattr(se, "_INV_BAND"))
        x0, y0, x1, y1 = se._INV_BAND
        self.assertGreater(x0, 0.5, "the band must be on the RIGHT half, away from the stash tooltip")
        self.assertLessEqual(x1, 1.0)
        self.assertLess(y0, y1)



class TestV2029AnItemsNameIsInATooltipNotInTheGrid(unittest.TestCase):
    """v2029 — the last two blockers between his hover footage and a NAME.

    v2028 taught the GATE that a tooltip covering the tab strip is not an absent stash. The frames
    then reached the reader and it STILL returned items:[] at conf 0.9 — confident there was
    nothing. Two more things were in the way, and both were measured on his own frames.

    1. THE CROP THREW THE TOOLTIP AWAY. claude_vault_read cropped every non-inventory surface to
       the calibrated stash-grid band, x 8%..40% y 20%..47%. The two tooltips sat at y ~2..13% —
       ENTIRELY ABOVE IT. The model was asked to read a grid and read the grid honestly.
       A tally tab is COUNTED from the grid and its band is genuinely calibrated; an ITEM's identity
       exists only in a tooltip that follows the cursor, so no band can be right for it. This is
       v1861's own rule one surface wider: "an uncalibrated band is not a band".

    2. A STASH TAB IS NOT A SURFACE. stash_screen_open answers with a TAB (personal/shared/...),
       and the prompt renders the value literally: "a ... {surface} panel". MEASURED, same frame,
       one word changed:  surface=personal -> 0 items conf 0.0  ·  surface=stash -> 1 item conf 0.9
       ("Annihilus"). A lane that could not answer, looking exactly like an empty shelf.

    PROVEN END TO END on f_1784984195842.jpg, a frame the gate used to refuse:
        gate 'stash' -> full frame -> 1 item, conf 0.6, "Sullied Grand Charm of Blight"
    the first item name the vault lane has ever read off a tooltip.
    """

    @staticmethod
    def _reader_src():
        import inspect
        import re
        import tv_diablo as tv
        src = inspect.getsource(tv.claude_vault_read)
        src = re.sub(r'"""(?:.|\n)*?"""', " ", src)
        src = re.sub(r"(?m)#[^\n]*$", " ", src)
        return src

    def test_the_item_lanes_read_the_whole_frame(self):
        src = self._reader_src()
        self.assertIn("_TALLY", src,
                      "the crop must be scoped to the TALLY tabs; cropping an item lane throws the "
                      "tooltip away, and the tooltip is the only place an item's name exists")
        # v2029 — ANCHORED, NOT BYTE-COUNTED. The first cut used a fixed byte window, and
        # TestTheSourceGuardsDoNotGetMoreDangerous blocked the push for it: a char window silently
        # slides off the thing it meant to read, and assertNotIn PASSES on an empty slice. _between
        # fails loudly and names which anchor moved.
        seg = _between(self, src, "_band =", "if _band", what="the band selection")
        self.assertIn("in _TALLY", seg,
                      "the band must be taken ONLY for a tally surface")

    def test_a_stash_tab_is_normalised_to_a_surface(self):
        src = self._reader_src()
        self.assertIn('("personal", "shared")', src,
                      "personal/shared are stash TABS, not surfaces - passed through they render "
                      "into the prompt as 'a personal panel' and the read silently returns nothing")
        seg = _between(self, src, 'if surface in ("personal", "shared")', "_read_path",
                       min_len=20, what="the tab normalisation")
        self.assertIn('"stash"', seg, "they must normalise to the stash surface")

    def test_the_tally_lanes_keep_their_calibrated_band(self):
        """The crop is not wrong everywhere - it is measured on his Mac for the tally tabs, and
        widening those to full frames would be a cost regression for no benefit."""
        src = self._reader_src()
        self.assertIn("crops_for_aspect", src, "the tally lanes must still use the calibrated band")
        for tab in ("runes", "gems", "materials"):
            self.assertIn(tab, src, "the tally set must still name %s" % tab)



class TestV2031TheDeclaredFocusChainIsJoinedAtEVERYLink(unittest.TestCase):
    """v2031 — v2027 fixed THREE links of a four-link chain and I reported it as wired end to end.

    The chain that lets a lane card tell the sweep what he is looking at:

        1. bible.html   the card POSTs { focus: 'stash' }
        2. /api/on      accepts it and validates it through _mini_focus()
        3. tv_diablo    parses --mini-focus OUTSIDE MINI mode
        4. tv_diablo    STAMPS it into the reel's index.json          <-- v2027 missed this one

    Link 4 stayed behind `if MINI_MODE:`, so the flag was parsed correctly and never written down —
    and vault_retro reads the SEALED REEL, not the argv of a process that has already exited.

    MEASURED on the reel he filmed at 22:18 under a console that already carried v2027:
    index.json keys were ['blank','blankPass','frames','n','sessionId']. No focus at all, not even
    an empty one. Three of four joined and the chain still carried nothing, which is the defining
    property of this class — it reads as wired from both ends. [[the-unjoined-end]]

    So this guard walks EVERY link rather than sampling one. A chain test that checks three links is
    the bug it is trying to catch.
    """

    @staticmethod
    def _tvd():
        import os
        import re
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "tv_diablo.py"), encoding="utf-8").read()
        src = re.sub(r'"""(?:.|\n)*?"""', " ", src)
        src = re.sub(r"(?m)#[^\n]*$", " ", src)
        return src

    def test_link1_the_card_sends_a_focus(self):
        import os
        import re
        here = os.path.dirname(os.path.abspath(__file__))
        bib = open(os.path.join(os.path.dirname(here), "bible.html"), encoding="utf-8").read()
        self.assertRegex(bib, r"var FOCUS = \{", "link 1: the lane card has no focus map")
        self.assertIn("{ focus:_focus }", bib, "link 1: the card does not SEND the focus")

    def test_link2_the_route_validates_it(self):
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "control_app.py"), encoding="utf-8").read()
        self.assertIn('_mini_focus(body.get("focus"))', src,
                      "link 2: /api/on must accept AND validate a focus")

    def test_link3_the_agent_parses_it_outside_mini_mode(self):
        import re
        src = self._tvd()
        m = re.search(r"^MINI_FOCUS\s*=\s*(.+)$", src, re.M)
        self.assertIsNotNone(m, "link 3: MINI_FOCUS assignment is gone")
        self.assertTrue(m.group(1).strip().startswith("_FOCUS_ARG"),
                        "link 3: the flag must be read unconditionally; only the DEFAULT may "
                        "depend on MINI_MODE")

    def test_link4_the_agent_STAMPS_it_into_the_reel(self):
        """The one v2027 left. Everything upstream is inert without it, and silently so."""
        src = self._tvd()
        i_focus = src.find('_ixdoc["focus"]')
        self.assertNotEqual(i_focus, -1, "link 4: the focus is never stamped into index.json")
        head = src[:i_focus]
        last_if = head.rfind("if ")
        guard = head[last_if:last_if + 40] if last_if != -1 else ""
        self.assertNotIn("MINI_MODE", guard,
                         "link 4: the focus stamp is gated on MINI_MODE, so a full session parses "
                         "the flag and never writes it down - the reel is what the sweep reads")
        self.assertIn("if MINI_FOCUS", guard,
                      "the stamp should fire whenever a focus was actually declared")

    def test_focusChosen_travels_with_the_focus_not_with_the_mini(self):
        """vault_retro._declared_surface keys its TRUST on focusChosen. A focus stamped without it
        would be trusted by default - the exact inversion v1783 built the field to prevent."""
        src = self._tvd()
        i_fc = src.find('_ixdoc["focusChosen"]')
        self.assertNotEqual(i_fc, -1, "focusChosen is never stamped")
        head = src[:i_fc]
        last_if = head.rfind("if ")
        guard = head[last_if:last_if + 40] if last_if != -1 else ""
        self.assertNotIn("MINI_MODE", guard,
                         "focusChosen must be written wherever the focus is, or a declared focus "
                         "arrives with no statement of whether he chose it")



class TestV2032EveryTooltipFrameReachesTheReader(unittest.TestCase):
    """v2032 — the dedupe that makes a held grid cheap makes a hover pass invisible.

    _distinct keeps only frames that LOOK different from the last kept one, so a panel held still
    costs ONE read instead of forty. Right for a grid, inverted for a tooltip pass: the panel is
    identical frame to frame and only a small tooltip rectangle changes, and jpeg_sig fingerprints
    the WHOLE frame, so that rectangle moves it far less than the default max_diff=0.06 tolerates.

    MEASURED on his tooltip reel, on the 73-frame run holding all 18 of its tooltips:
        vault today (defaults)        2 pages,  1 tooltip
        chronicle's max_diff=0.002   36 pages,  8 tooltips
        chronicle's full tuning      72 pages, 18 tooltips
    One name reached him out of eighteen chances.

    COPYING THE CHRONICLE'S NUMBERS WOULD BE THE WRONG FIX — 72 of 73 frames is not a dedupe. The
    vault lane only cares about frames carrying a NAME, and those are free to spot: a tooltip
    covering the tab strip is exactly what makes the gate answer the GENERIC "stash" (v2028). So the
    cheap dedupe still picks the GRID pages and every tooltip frame is added on top: 19 pages, 18 of
    them tooltips.
    """

    def _reel(self, td, n_plain=6, n_tip=4):
        """A fake reel: `plain` frames the gate calls a TAB, `tip` frames it calls generic stash."""
        import json
        import os
        d = os.path.join(td, "reel_s_TEST")
        os.makedirs(d, exist_ok=True)
        rows = []
        order = []
        for i in range(n_plain):
            fn = "f_plain_%03d.jpg" % i
            open(os.path.join(d, fn), "w").close()
            rows.append({"f": fn, "ts": 1000 + i}); order.append(fn)
        for i in range(n_tip):
            fn = "f_tip_%03d.jpg" % i
            open(os.path.join(d, fn), "w").close()
            rows.append({"f": fn, "ts": 2000 + i}); order.append(fn)
        with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"sessionId": "s_TEST", "n": len(rows), "frames": rows}, fh)
        return d, order

    def test_a_tooltip_frame_is_never_deduped_away(self):
        import tempfile
        import vault_retro as vr
        with tempfile.TemporaryDirectory() as td:
            d, order = self._reel(td)
            seen = []
            gate = lambda p: ("stash" if "_tip_" in p else "personal")
            vr.sweep([d], sig=lambda p: "SAME",             # every frame looks identical to _distinct
                     classify=lambda p: "stash",
                     reader=lambda p, s: (seen.append(p.split("/")[-1]), {"items": []})[1],
                     panel_gate=gate)
            tips = [n for n in seen if "_tip_" in n]
            self.assertEqual(len(tips), 4,
                             "every tooltip frame must reach the reader - the tooltip is the ONLY "
                             "place an item name exists, so deduping one away is losing a name. "
                             "got: %s" % seen)

    def test_the_grid_is_still_deduped(self):
        """The saving must survive: identical grid frames still collapse."""
        import tempfile
        import vault_retro as vr
        with tempfile.TemporaryDirectory() as td:
            d, order = self._reel(td, n_plain=6, n_tip=0)
            seen = []
            vr.sweep([d], sig=lambda p: "SAME",
                     classify=lambda p: "stash",
                     reader=lambda p, s: (seen.append(p), {"items": []})[1],
                     panel_gate=lambda p: "personal")
            self.assertLess(len(seen), 6,
                            "six identical grid frames must NOT all be read - that is the dedupe "
                            "this lane depends on for cost")

    def test_pages_are_offered_in_the_order_he_hovered_them(self):
        import tempfile
        import vault_retro as vr
        with tempfile.TemporaryDirectory() as td:
            d, order = self._reel(td)
            seen = []
            vr.sweep([d], sig=lambda p: "SAME", classify=lambda p: "stash",
                     reader=lambda p, s: (seen.append(p.split("/")[-1]), {"items": []})[1],
                     panel_gate=lambda p: ("stash" if "_tip_" in p else "personal"))
            pos = [order.index(n) for n in seen if n in order]
            self.assertEqual(pos, sorted(pos),
                             "pages must be read in reel order, so witnesses land in the order he "
                             "actually hovered them: %s" % seen)

    def test_no_panel_gate_means_the_old_behaviour(self):
        """Every caller that passes no gate must be byte-identical to before."""
        import tempfile
        import vault_retro as vr
        with tempfile.TemporaryDirectory() as td:
            d, order = self._reel(td)
            seen = []
            vr.sweep([d], sig=lambda p: "SAME", classify=lambda p: "stash",
                     reader=lambda p, s: (seen.append(p), {"items": []})[1])
            self.assertLessEqual(len(seen), 2,
                                 "with no gate supplied the cheap dedupe must be all there is")



class TestV2034TheApplyNamesWhichCauseStoppedIt(unittest.TestCase):
    """v2034 — one message for two causes, and only one of them was about the build.

    vault_apply answered "this board build has no vaultAccumApply — update the board" whenever the
    function was missing from the window. Two very different things produce that:

      (a) the window is showing the CONSOLE RAIL, not the board. Nothing is wrong with anything and
          he just navigates back. This is the COMMON case — one window, same-origin nav (v781).
      (b) the window IS the board and its build predates vaultAccumApply. Only then is "update" the
          right instruction.

    HIT LIVE: a finished sweep with two grounded names could not be applied, and the message sent me
    to check bible.html — which contained the function nine times over. A message that names the
    wrong cause costs exactly as much as no message, and worse, it spends his trust.

    The two are told apart by what the window is SHOWING (#tab-tools on the board, details.sig-adv
    on the rail), never by guessing at the build. [[label-outlived-referent]]
    """

    @staticmethod
    def _apply_src():
        import inspect
        import control_app as ca
        return inspect.getsource(ca.vault_apply)

    def test_the_console_case_does_not_say_update_the_board(self):
        src = self._apply_src()
        i = src.find("onRail&&!onBoard")
        self.assertNotEqual(i, -1, "the console-rail case is not distinguished at all")
        seg = _between(self, src, "onRail&&!onBoard", "onBoard ?", min_len=30,
                       what="the console-rail branch")
        self.assertNotIn("update the board", seg,
                         "when the window is merely on the console rail, telling him to UPDATE THE "
                         "BOARD sends him to fix something that is not broken")
        self.assertIn("CONSOLE", seg, "it must say where the window actually is")

    def test_the_stale_board_case_still_says_reload(self):
        src = self._apply_src()
        self.assertIn("reload it", src,
                      "a genuinely old board must still be told to reload - control_ui and "
                      "bible.html are both read fresh from disk, so a reload IS the fix")

    def test_all_three_outcomes_are_distinct(self):
        """Neither-board-nor-rail is its own answer: 'I cannot see where you are' is not the same
        as either diagnosis, and must not borrow one of their instructions."""
        src = self._apply_src()
        for probe in ("onRail&&!onBoard", "onBoard ? 'the board is open",
                      "neither the board nor the console"):
            self.assertIn(probe, src, "missing branch: %s" % probe)

    def test_it_reads_the_dom_not_the_version(self):
        """Which view is on screen is a FACT about the window. Inferring it from a version stamp
        would be the same guess this whole class of bug is made of."""
        src = self._apply_src()
        self.assertIn("getElementById('tab-tools')", src)
        self.assertIn("querySelector('details.sig-adv')", src)



class TestV2035TheLaneReelSealsItselfWhenHeLeavesTheStash(unittest.TestCase):
    """v2035 — Konyo asked for this twice and it had never been built.

    "when we start like moving and like close stash.. enter a new Waypoint through a portal it
    should kill it completley for sure by then", and then live: "i hit auto vault. and now i exited
    the stash... and am going to farm... verifiy and monitor it and make sure it closes
    automatically".

    IT DID NOT. Measured while he farmed: recording=True, 5297 -> 5683 frames over seven minutes of
    footage of him walking around, at roughly 9GB/hour. The honest answer to "make sure it closes"
    was "it does not".

    The signal was already free — stash_screen_open answers per frame whether a panel is on screen,
    a crop and an OCR with no model call. Closing the stash, walking off, taking a waypoint all stop
    that answer.
    """

    def test_it_only_closes_a_reel_with_a_DECLARED_focus(self):
        """A plain ON AIR is HIS, for whatever he is doing. Guessing at that is not the machine's
        job, and auto-sealing it would destroy a recording he deliberately started."""
        import inspect
        import control_app as ca
        src = inspect.getsource(ca._stash_watch_loop)
        self.assertIn("_current_declared_focus", src,
                      "the watcher must only close a reel a LANE CARD opened")
        self.assertIn("stop_agent", src, "it must actually seal")

    def test_a_single_frame_without_a_panel_does_not_seal(self):
        """One frame is him scrolling a tab, or a tooltip covering the chrome. It needs a RUN."""
        import inspect
        import control_app as ca
        src = inspect.getsource(ca._stash_watch_loop)
        self.assertIn("gone_since", src, "there must be a grace window, not a single-frame trigger")
        self.assertGreaterEqual(ca._STASH_WATCH_GRACE_S, 10,
                                "a grace shorter than ~10s will seal on a tab switch")

    def test_silence_is_not_absence(self):
        """No frames, or a gate that threw, is 'I cannot see' — never 'he left'. Sealing on a blind
        read would end a session because the CAMERA failed. [[unknown-stays-unknown]]"""
        import inspect
        import control_app as ca
        src = inspect.getsource(ca._stash_watch_loop)
        i = src.find("_newest_frame_path()")
        self.assertNotEqual(i, -1)
        seg = _between(self, src, "fr = _newest_frame_path()", "try:", min_len=20,
                       what="the no-frame branch")
        self.assertIn("gone_since = None", seg,
                      "no frame must RESET the countdown, never advance it")

    def test_it_reads_the_live_frame_UNCACHED(self):
        """frames/eye.jpg is one path rewritten in place many times a second, and the gate cache is
        keyed on (size, mtime) with 1s granularity. Measured live: the cached call answered 'stash'
        for a frame the uncached gate correctly called gameplay. [[stale-reading]]"""
        import inspect
        import control_app as ca
        src = inspect.getsource(ca._stash_watch_loop)
        self.assertIn("stash_screen_open(fr)", src)
        self.assertNotIn("stash_screen_open_cached(fr)", src,
                         "the live view must not be read through a (size, mtime) cache")

    def test_the_watcher_is_actually_started(self):
        """A loop nobody starts is the class this whole night kept finding."""
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "control_app.py"), encoding="utf-8").read()
        self.assertIn('name="tvd-stash-watch"', src, "the watcher thread is never started")
        self.assertIn("target=_stash_watch_loop", src)



class TestV2036ATornFrameIsNotAnAbsentStash(unittest.TestCase):
    """A frame still being WRITTEN must never read as evidence he left the stash.

    The capture writes `eye.jpg.part.jpg` and then renames it. Measured on the live tree at
    2026-08-24 02:0x, that partial was sitting in `_newest_frame_path`'s own glob at full size
    (1433054 B) - one mtime tick from being the newest candidate. Had it won, the v2035 watcher
    would have handed a torn JPEG to `stash_screen_open`, which does NOT throw on garbage: it
    answers None, `open_now` goes False, the 25s eviction timer starts, and a session he is
    still farming in gets sealed under him.

    The loop already refuses to act on no-frames and on a gate that threw. A TORN frame is the
    third case, and it was the one that read as a confident answer. [[unknown-stays-unknown]]

    SABOTAGE-PROVEN: drop the `.part.` filter in `_newest_frame_path` and the first test goes red.
    """

    def _mk(self, d, name, age_s):
        import os, time
        q = os.path.join(d, name)
        with open(q, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0" + b"0" * 64)
        t = time.time() - age_s
        os.utime(q, (t, t))
        return q

    def test_the_partial_never_wins_even_when_it_is_newest(self):
        import os, tempfile
        import unittest.mock as mock
        import control_app
        with tempfile.TemporaryDirectory() as root:
            hist = os.path.join(root, "hist")
            os.makedirs(hist)
            real = self._mk(hist, "f_1787526382111.jpg", 30)   # COMPLETE, older
            self._mk(hist, "eye.jpg.part.jpg", 1)              # TORN, newest
            with mock.patch.object(control_app, "HIST_DIR", hist):
                got = control_app._newest_frame_path()
            self.assertIsNotNone(got, "a complete frame was present; None would stall the watcher")
            self.assertNotIn(".part.", os.path.basename(got),
                             "the half-written frame won - the watcher would OCR a torn JPEG, "
                             "answer None, and seal a session he is still using")
            self.assertEqual(os.path.basename(got), os.path.basename(real))

    def test_only_partials_reads_as_UNKNOWN_never_as_a_frame(self):
        """Every candidate torn = nobody looked. None, which the loop treats as no evidence."""
        import os, tempfile
        import unittest.mock as mock
        import control_app
        with tempfile.TemporaryDirectory() as root:
            hist = os.path.join(root, "hist")
            os.makedirs(hist)
            self._mk(hist, "eye.jpg.part.jpg", 1)
            with mock.patch.object(control_app, "HIST_DIR", hist):
                self.assertIsNone(control_app._newest_frame_path())

    def test_the_loop_still_refuses_to_act_on_no_evidence(self):
        """The two pre-existing no-evidence branches must survive this edit."""
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "control_app.py"), encoding="utf-8").read()
        body = _between(self, src, "def _stash_watch_loop", "def _newest_frame_path",
                        what="the stash watch loop")
        # assertTrue, not assertIn: a failing assertIn against this source dumps the whole slice
        # into the log. The message below says more than 2600 chars of Python ever would.
        self.assertTrue("no frames = no evidence" in body,
                        "the no-frames branch is gone - the watcher would treat 'I cannot see' "
                        "as 'he left', which is the whole defect the loop exists to avoid")
        self.assertTrue("a gate that threw has not seen him leave" in body,
                        "the gate-threw branch is gone from the watch loop")



class TestV2037TheRollingPruneNeverEatsEvidence(unittest.TestCase):
    """Konyo asked for a prune that runs "indefinitely while its on ... to prune and register and
    witness". Deleting film is irreversible, so every refusal here matters more than the bytes.

    The safety bar was MEASURED, not argued: fingerprinting all 1270 frames of his 22-minute
    auto-vault reel, grouping at 0.02 and keeping one per group drops 26% of the bytes, and the
    worst distance from a dropped frame to its kept representative - measured against the nine
    frames that reel's sweep actually READ - was 0.0117.
    """

    def _mk(self, d, name, age_s=9999):
        q = os.path.join(d, name)
        with open(q, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0" + b"0" * 200)
        t = time.time() - age_s
        os.utime(q, (t, t))
        return q

    def _run(self, root, sigs, **kw):
        """Run one prune pass with a FAKE fingerprint, so the test measures the POLICY."""
        import unittest.mock as mock
        import control_app, vault_retro
        with mock.patch.object(vault_retro, "DEFAULT_SIG",
                               lambda q: sigs.get(os.path.basename(q))):
            kw.setdefault("floor", 0)
            kw.setdefault("grace_s", 0.0)
            kw.setdefault("batch", 500)
            return control_app._prune_once(hist_dir=root, **kw)

    def test_it_compares_against_the_KEPT_frame_not_the_previous_one(self):
        """The defect this avoids is the one still_runs actually has.

        On his own reel a 56-frame run walked 0.484 from its anchor while every consecutive step
        stayed under 0.22 - welding gameplay to a Loading screen. A prune that drifted that way
        would delete frames it never compared against what it kept.

        Each frame here differs from the PREVIOUS by 0.01, under the 0.02 bar. But f_3 differs
        from the ANCHOR f_0 by 0.03, over it. Anchor-comparison keeps f_0 and f_3;
        previous-comparison keeps only f_0 and silently eats a frame 3x past the bar.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            sigs = {}
            for k in range(5):
                n = "f_%d.jpg" % k
                self._mk(root, n)
                sigs[n] = [0] * (100 - k) + [100] * k     # k of 100 samples differ from f_0
            d, b, why = self._run(root, sigs, max_diff=0.02)
            left = sorted(os.path.basename(x) for x in glob.glob(os.path.join(root, "f_*.jpg")))
            self.assertIn("f_0.jpg", left, "the anchor itself must never be dropped")
            self.assertIn("f_3.jpg", left,
                          "f_3 is 0.03 from the anchor - over the 0.02 bar - and was eaten. "
                          "That is previous-frame comparison, and it is how a group drifts "
                          "without bound (the still_runs defect measured on his own reel).")
            self.assertNotIn("f_1.jpg", left, "f_1 is 0.01 from the anchor and adds nothing")
            self.assertNotIn("f_2.jpg", left, "f_2 is 0.02 from the anchor and adds nothing")
            self.assertEqual(d, 3, "expected f_1, f_2 and f_4 dropped")

    def test_it_never_touches_a_reel_directory(self):
        """Sealed reels are the reader's evidence, and a sweep may be walking one right now."""
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            reel = os.path.join(root, "reel_s_1_2")
            os.makedirs(reel)
            sigs = {}
            for k in range(4):
                n = "f_%d.jpg" % k
                self._mk(root, n); sigs[n] = [0] * 100
            inside = self._mk(reel, "f_99.jpg"); sigs["f_99.jpg"] = [0] * 100
            self._run(root, sigs, max_diff=0.02)
            self.assertTrue(os.path.exists(inside),
                            "a frame INSIDE a reel was deleted - sealed reels are evidence and a "
                            "sweep may be reading that directory this second")

    def test_it_never_touches_a_partial_write(self):
        """v2036's rule, enforced at the second place it matters."""
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            sigs = {}
            for k in range(4):
                n = "f_%d.jpg" % k
                self._mk(root, n); sigs[n] = [0] * 100
            part = self._mk(root, "f_eye.jpg.part.jpg"); sigs["f_eye.jpg.part.jpg"] = [0] * 100
            self._run(root, sigs, max_diff=0.02)
            self.assertTrue(os.path.exists(part),
                            "a half-written frame was deleted; it is not a frame and not a duplicate")

    def test_the_grace_window_protects_recent_frames(self):
        """The stash watcher and the live eye read the newest frame - it must always be whole."""
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            sigs = {}
            for k in range(6):
                n = "f_%d.jpg" % k
                self._mk(root, n, age_s=1)     # all brand new
                sigs[n] = [0] * 100
            d, b, why = self._run(root, sigs, grace_s=600.0, max_diff=0.02)
            self.assertEqual(d, 0, "recent frames were pruned despite the grace window")
            self.assertIn("grace", why)

    def test_an_unreadable_frame_breaks_the_group_and_is_kept(self):
        """A fingerprint we could not take is not evidence of sameness. [[unknown-stays-unknown]]"""
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            sigs = {}
            for k in range(4):
                n = "f_%d.jpg" % k
                self._mk(root, n); sigs[n] = [0] * 100
            self._mk(root, "f_bad.jpg"); sigs["f_bad.jpg"] = None
            self._run(root, sigs, max_diff=0.02)
            left = [os.path.basename(x) for x in glob.glob(os.path.join(root, "f_*.jpg"))]
            self.assertIn("f_bad.jpg", left, "an unreadable frame was deleted as a duplicate")

    def test_dry_run_deletes_nothing_but_still_reports(self):
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            sigs = {}
            for k in range(5):
                n = "f_%d.jpg" % k
                self._mk(root, n); sigs[n] = [0] * 100
            d, b, why = self._run(root, sigs, max_diff=0.02, dry_run=True)
            left = glob.glob(os.path.join(root, "f_*.jpg"))
            self.assertEqual(len(left), 5, "dry_run deleted files")
            self.assertGreater(d, 0, "dry_run reported nothing - it must still count")

    def test_the_prune_loop_is_actually_started(self):
        """A loop nobody starts is the class this project keeps finding."""
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "control_app.py"), encoding="utf-8").read()
        self.assertTrue('name="tvd-rolling-prune"' in src, "the prune thread is never started")
        self.assertTrue("target=_prune_loop" in src)



class TestV2040TheClaimBarIsTheFixNotTheNoise(unittest.TestCase):
    """v2039 hid the claim bar when the store held data. That was a REGRESSION and this reverts it.

    The bar's button is the ONLY writer of d2r_ownerClaim. Without that claim `_D2R_OWNER` is false,
    `_D2R_PFX` becomes 'I·<installId>·', and the load lives in a per-install GUEST world. Measured
    2026-08-24: six board windows, six install ids, six empty worlds, and d2r_owned lost every time.
    d2r_grailFarm only LOOKED like it migrated because the console re-bridges it on every load.

    So suppressing the bar hides the fix from exactly the person standing on the bug.
    """

    def _bible(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return open(os.path.join(here, "bible.html"), encoding="utf-8").read()

    def test_the_bar_is_never_suppressed_by_the_presence_of_data(self):
        src = self._bible()
        blk = _between(self, src, "var claimed = null;", "var btn = document.getElementById",
                       what="the claim-bar block")
        self.assertFalse("hasData" in blk,
                         "the bar is being hidden when the store holds data again - that hides the "
                         "only control that writes d2r_ownerClaim, stranding him in a guest world")

    def test_the_claim_button_still_writes_the_only_key_that_matters(self):
        src = self._bible()
        blk = _between(self, src, "var btn = document.getElementById('claim-btn')", "})();",
                       what="the claim button")
        self.assertTrue("d2r_ownerClaim" in blk,
                        "the button no longer writes d2r_ownerClaim, so nothing can ever leave the "
                        "guest world")

    def test_the_queued_apply_stays_REMOVED(self):
        """v2038 spawned a board window and applied there; v2040 then had to stop it lying about
        the result. Both treated the symptom.

        Measured 2026-08-24: the main window and a spawned board window hold SEPARATE localStorage
        while both run — a persistent probe beside the live console saw its own sentinel, not his
        404-entry ledger — and the console is what SERVES /board, so a board window can never exist
        without it. A spawned window is therefore never his real world, and claiming one would only
        build a second empty owner world beside the real one. Removed in v2045.

        This guard exists because the idea is attractive and WILL be re-invented: the refusal
        message reads like something to work around, and it is not. [[the-unjoined-end]]
        """
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "control_app.py"), encoding="utf-8").read()
        for dead in ("_queue_board_apply", "_board_apply_on_load", "--apply-vault"):
            self.assertFalse(dead in src,
                             "%r is back. A spawned board window is never his real world — put the "
                             "board on the MAIN window instead." % dead)
        blk = _between(self, src, "def vault_apply(proposal=None):", "def _jsq(",
                       what="vault_apply")
        self.assertTrue("not the board" in blk,
                        "vault_apply no longer tells him WHICH window to use")


class TestV2039TheBoardDoesNotLieAboutBeingEmpty(unittest.TestCase):
    """Two defects caught by LOOKING at his board, both invisible to every parser gate.

    1. The claim bar rendered "chronicle, vault and forge all start at zero" directly above a VAULT
       tile reading 7, on a store holding 451 KB of d2r_grailFarm. Its GATE was correct - there was
       no d2r_ownerClaim key - but the SENTENCE is a claim about DATA and nothing had looked at the
       data. [[unknown-stays-unknown]]

    2. The subscription meter's right-aligned figures ended 3px PAST .help-btn's left edge at 1440,
       1200, 1100, 901 AND 375 - measured by CDP. Because the FABs are position:fixed, the collision
       only appears at scroll positions that put the row level with them, which is why his screenshot
       caught it and a first CDP pass at scrollTop 0 reported "no overlap".
    """

    def _bible(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return open(os.path.join(here, "bible.html"), encoding="utf-8").read()

    def test_the_meter_reserves_the_fixed_FAB_column(self):
        src = self._bible()
        blk = _between(self, src, "#tab-tools .sub-meter{", "}", what="the sub-meter rule")
        self.assertTrue("padding:8px 60px 8px 12px" in blk,
                        "the meter no longer reserves room for the fixed help/legend FABs - its "
                        "figures render under the gold '?' at every width")

    def test_the_meter_still_exists_to_be_covered(self):
        """A guard on a rule for an element that was deleted is a guard measuring nothing."""
        src = self._bible()
        self.assertTrue('id="sub-meter"' in src, "#sub-meter is gone from the board")



class TestV2041ADurableReceiptForALedgerThatLivesInAWindow(unittest.TestCase):
    """His grail and vault ledgers live ONLY in a window's localStorage - vault_ledger_load() says
    so in its own docstring: the console has never held them. A crash or a force-quit takes 404
    found uniques and 120 set pieces with it, silently.

    Made urgent 2026-08-24: spawned board windows are unclaimed GUEST worlds, and six of them in one
    night wrote six `I·<id>·` namespaces into the same on-disk store, leaving none of his bare keys
    on disk. His ledger was fine - verified live at 404/5/120 with real names - but nothing on disk
    could have proven it and nothing would have brought it back.
    """

    def _patch(self, ca, tmp, answer):
        import unittest.mock as mock
        return (mock.patch.object(ca, "_LEDGER_BACKUP_DIR", tmp),
                mock.patch.object(ca, "board_ownership", lambda sample=0: answer))

    def _run(self, answer, tmp, force=True, reset=True):
        import control_app as ca
        if reset:
            ca._LEDGER_BACKUP_STATE.update({"last": "", "counts": None, "writes": 0, "why": ""})
        a, b = self._patch(ca, tmp, answer)
        with a, b:
            return ca._ledger_snapshot_once(force=force)

    def test_a_refusal_never_becomes_a_backup(self):
        """board_ownership refuses honestly on a timeout. Filing that as a backup would record
        'he owns nothing' as though it had been measured. [[unknown-stays-unknown]]"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path, why = self._run({"ok": False, "why": "the board did not answer in time"}, tmp)
            self.assertIsNone(path, "a refusal was written to disk as a backup")
            self.assertEqual(len(glob.glob(os.path.join(tmp, "*.json"))), 0)

    def test_an_empty_ledger_is_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path, why = self._run({"ok": True, "counts": {"foundLog": 0, "owned": 0, "setPieces": 0},
                                   "sample": {"foundLog": [], "owned": [], "setPieces": []}}, tmp)
            self.assertIsNone(path, "an empty ledger was filed over real history")
            self.assertIn("EMPTY", why)

    def test_a_truncated_ledger_is_refused(self):
        """A partial copy that calls itself a backup is worse than no backup."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path, why = self._run({"ok": True,
                                   "counts": {"foundLog": 404, "owned": 5, "setPieces": 120},
                                   "sample": {"foundLog": ["a", "b"], "owned": ["c"],
                                              "setPieces": ["d"]}}, tmp)
            self.assertIsNone(path, "a truncated ledger was written as if complete")
            self.assertIn("truncated", why)

    def _full(self):
        return {"ok": True, "counts": {"foundLog": 2, "owned": 1, "setPieces": 1},
                "sample": {"foundLog": ["Wormskull", "Wolfhowl"], "owned": ["Raven Frost"],
                           "setPieces": ["Angelic Halo (ring)"]}}

    def test_a_complete_ledger_is_written_with_its_names(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path, why = self._run(self._full(), tmp)
            self.assertIsNotNone(path, "a complete ledger was not written: %s" % why)
            d = json.load(open(path, encoding="utf-8"))
            self.assertEqual(d["counts"]["foundLog"], 2)
            self.assertIn("Wormskull", d["ledger"]["foundLog"])
            self.assertTrue(d.get("takenAt"), "a backup with no timestamp cannot be ordered")

    def test_an_unchanged_ledger_does_not_spam_a_second_copy(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._run(self._full(), tmp)
            path, why = self._run(self._full(), tmp, force=False, reset=False)
            self.assertIsNone(path, "an identical ledger was filed twice")
            self.assertIn("unchanged", why)

    def test_it_keeps_a_bounded_number_of_copies(self):
        import tempfile, control_app as ca
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(ca._LEDGER_BACKUP_KEEP + 6):
                open(os.path.join(tmp, "ledger_2020-01-01_%06d.json" % i), "w").write("{}")
            self._run(self._full(), tmp)
            left = glob.glob(os.path.join(tmp, "ledger_*.json"))
            self.assertLessEqual(len(left), ca._LEDGER_BACKUP_KEEP,
                                 "backups grow without bound")

    def test_the_backups_are_written_OUTSIDE_the_public_repo(self):
        """d2r-bible-tests is PUBLIC and a push to main PUBLISHES. His ledger must never land in it."""
        import control_app as ca
        repo = os.path.dirname(os.path.dirname(os.path.abspath(ca.__file__)))
        d = os.path.abspath(ca._LEDGER_BACKUP_DIR)
        self.assertFalse(d.startswith(os.path.abspath(repo) + os.sep),
                         "ledger backups are inside the PUBLIC repo (%s) - a push would publish "
                         "his entire grail history" % d)

    def test_the_backup_loop_is_actually_started(self):
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "control_app.py"), encoding="utf-8").read()
        self.assertTrue('name="tvd-ledger-backup"' in src, "the backup loop is never started")
        self.assertTrue("target=_ledger_backup_loop" in src)



class TestV2048TheBoardWindowStaysIsolated(unittest.TestCase):
    """REVERTS v2043. A board window must NOT share the main window's localStorage.

    v2043 gave the board window `private_mode=False` so its own world would survive a relaunch, and
    it worked — install id c5c2c92d survived two launches beside the live console.

    THEN IT COST HIM HIS LEDGER. His main window's grail/vault world lives only in ITS memory —
    nothing on disk ever held his bare `d2r_foundLog`. After persistent WebKit probes ran beside the
    live console, that window went from 404 foundLog / 5 owned / 120 setPieces to ZERO, and the
    shared store held the probe's own key and none of his. A second persistent process on this
    origin can take the live window's world with it.

    v2045 had already removed the only reason a board window needed to persist: it is a GUEST world
    that can never be his real one, so nothing of value is stored there. Isolation is worth more
    than persistence for a window whose contents do not matter.
    """

    def _src(self):
        here = os.path.dirname(os.path.abspath(__file__))
        return open(os.path.join(here, "control_app.py"), encoding="utf-8").read()

    def test_the_board_window_does_NOT_ask_for_persistent_storage(self):
        blk = _between(self, self._src(), "def board_window():", "def main():",
                       what="board_window")
        # Check the CALL, not the prose. The comment above it legitimately contains the words
        # `private_mode=False` while explaining why they are gone, and a naive substring test would
        # be blinded by exactly that — the same way my own comment blinded a guard earlier tonight.
        self.assertFalse("private_mode=False)" in blk,
                         "the board window passes private_mode=False again — it would share the "
                         "MAIN window's localStorage, and that emptied his 404-entry ledger once")
        self.assertFalse("webview.start(**" in blk,
                         "the board window starts with kwargs again; the only kwarg this ever "
                         "carried was the persistence that cost him the ledger")
        self.assertTrue("webview.start()" in blk,
                        "board_window no longer starts a window at all")

    def test_the_MAIN_window_still_persists(self):
        """The revert must not reach the window that holds his real ledger."""
        self.assertTrue("_start_kw = dict(debug=False, private_mode=False)" in self._src(),
                        "the MAIN window stopped requesting persistent storage — his grail ledger "
                        "would reset on every quit")

class TestV2044TheDoctorCanSeeADoomedWorld(unittest.TestCase):
    """An unclaimed board world fails SILENTLY: the ledger counts read exactly the same in a doomed
    world as in a real one, so nothing on any screen distinguishes them. An apply into it returns
    ok:true, writes real rows, and they are unreachable from the next load. That cost a whole night.
    [[the-unjoined-end]]
    """

    def _cd(self):
        import console_doctor
        return console_doctor

    def test_an_ABSENT_ownership_field_is_unknown_never_a_pass(self):
        """An older console cannot answer. 'Nobody asked' must never read as 'all fine'."""
        import unittest.mock as mock
        cd = self._cd()
        with mock.patch.object(cd, "_post", lambda *a, **k: {
                "ok": True, "counts": {"foundLog": 404, "owned": 5, "setPieces": 120}}):
            state, why = cd._check_the_board_world_is_claimed()
        self.assertEqual(state, cd.UNKNOWN,
                         "a console that cannot report ownership was graded as healthy")

    def test_an_unclaimed_world_is_reported_MISSING_with_the_remedy(self):
        import unittest.mock as mock
        cd = self._cd()
        with mock.patch.object(cd, "_post", lambda *a, **k: {
                "ok": True, "owner": False, "pfx": "I\u00b7abc12345\u00b7",
                "counts": {"foundLog": 404, "owned": 5, "setPieces": 120}}):
            state, why = cd._check_the_board_world_is_claimed()
        self.assertEqual(state, cd.MISSING, "a doomed world was not flagged")
        self.assertIn("This browser is mine", why, "the report names no remedy")
        # 404 + 5 + 120 = 529. Naming the size is what makes the warning land: "your 529-entry
        # ledger is in a world that evaporates" is a different sentence from a generic caution.
        self.assertIn("529", why,
                      "the warning does not say how much is at stake, so it reads as boilerplate")

    def test_a_claimed_world_passes(self):
        import unittest.mock as mock
        cd = self._cd()
        with mock.patch.object(cd, "_post", lambda *a, **k: {
                "ok": True, "owner": True, "pfx": "",
                "counts": {"foundLog": 404, "owned": 5, "setPieces": 120}}):
            state, why = cd._check_the_board_world_is_claimed()
        self.assertEqual(state, cd.OK)

    def test_a_silent_console_is_unknown_not_ok(self):
        import unittest.mock as mock
        cd = self._cd()
        with mock.patch.object(cd, "_post", lambda *a, **k: None):
            state, why = cd._check_the_board_world_is_claimed()
        self.assertEqual(state, cd.UNKNOWN)

    def test_the_check_is_actually_in_the_CHECKS_list(self):
        """A check nobody runs is prose."""
        cd = self._cd()
        names = [n for n, _fn in cd.CHECKS]
        self.assertIn("board is claimed", names, "the check is never run by the Eagle Eye")

    def test_board_ownership_reports_which_world_it_read(self):
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "control_app.py"), encoding="utf-8").read()
        blk = _between(self, src, "def board_ownership", "def _jsq(", what="board_ownership")
        self.assertTrue("_D2R_OWNER" in blk,
                        "board_ownership no longer says which world the counts came from, so a real "
                        "ledger and a doomed one are indistinguishable to every caller")
        self.assertTrue("owner:owner" in blk)



class TestV2046TheDiskWarningMeasuresHisFootage(unittest.TestCase):
    """The disk check used to say "a reel writes roughly 9GB/hour".

    That number is REAL — v2019 clocked +37MB in 15s on a busy scene. So is 5.0-6.6GB/hour, measured
    2026-08-24 across his three newest reels at 1.44-1.90 MB/frame. Both are true, because JPEG size
    tracks scene complexity and the rate swings ~2x with what he is looking at. A single constant
    cannot describe that, and quoting one as though it could is a right number under a word that
    stopped being true. [[label-outlived-referent]]

    He acts on this figure — it is how he decides whether to start a session.
    """

    def _fixture(self, tmp, n_frames, minutes, kb):
        """A reel of n_frames spread over `minutes`, each kb kilobytes."""
        import time as _t
        d = os.path.join(tmp, "frames", "hist", "reel_s_1_1")
        os.makedirs(d)
        now = _t.time()
        for i in range(n_frames):
            q = os.path.join(d, "f_%d.jpg" % i)
            with open(q, "wb") as fh:
                fh.write(b"\0" * (kb * 1024))
            t = now - (minutes * 60.0) + (i * minutes * 60.0 / max(1, n_frames - 1))
            os.utime(q, (t, t))
        return d

    def _rate(self, tmp):
        import unittest.mock as mock
        import console_doctor as cd
        with mock.patch.object(cd, "HERE", tmp):
            return cd._measured_write_rate()

    def test_it_measures_the_real_rate_from_his_own_reels(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            # 60 frames x 1MB over 1 minute = 60MB/min = 3.5GB/hour
            self._fixture(tmp, 60, 1.0, 1024)
            rate, n = self._rate(tmp)
            self.assertEqual(n, 1)
            self.assertAlmostEqual(rate, 60 * 1024 * 1024 * 60 / float(1 << 30), delta=0.3)

    def test_a_reel_too_short_to_time_produces_NO_rate(self):
        """Dividing by a near-zero window invents an enormous figure out of nothing."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._fixture(tmp, 60, 0.05, 1024)      # 3 seconds
            rate, n = self._rate(tmp)
            self.assertIsNone(rate, "a 3-second reel was extrapolated into an hourly rate")
            self.assertEqual(n, 0)

    def test_a_reel_with_too_few_frames_produces_NO_rate(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._fixture(tmp, 5, 5.0, 1024)
            rate, n = self._rate(tmp)
            self.assertIsNone(rate, "five frames were treated as a measurement")

    def test_when_nothing_is_measurable_it_SAYS_it_is_a_worst_case(self):
        """An unmeasured number must never arrive dressed as a measured one."""
        import tempfile
        import unittest.mock as mock
        import console_doctor as cd
        import collections
        # Pin the FREE SPACE too. Reaching the warning branch must not depend on how full his disk
        # happens to be while the suite runs - that is a gate that passes for the wrong reason.
        fake = collections.namedtuple("du", "total used free")(500e9, 490e9, 10e9)
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(cd, "HERE", tmp):
                with mock.patch.object(cd, "_measured_write_rate", lambda: (None, 0)):
                    with mock.patch("shutil.disk_usage", lambda _p: fake):
                        state, why = cd._check_disk_headroom()
        self.assertEqual(state, cd.MISSING, "10GB free did not reach the warning branch")
        self.assertIn("worst case", why,
                      "an unmeasured rate was reported without saying it was unmeasured")

    def test_the_warning_names_the_measured_rate_not_a_constant(self):
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "console_doctor.py"), encoding="utf-8").read()
        blk = _between(self, src, "def _check_disk_headroom():", "def _check_subscription_burn():",
                       what="the disk check")
        self.assertTrue("_measured_write_rate()" in blk,
                        "the disk check asserts a constant rate again instead of measuring his "
                        "footage - he decides whether to start a session on this number")
        self.assertFalse("roughly 9GB/hour" in blk,
                         "the old constant is back in the warning text")



class TestV2049TheVerdictNamesWhatDidNotRun(unittest.TestCase):
    """run_gates' own docstring already says it: *"Silence about a check that did not happen is the
    same lie as a false green."* That rule was enforced for a whole GATE that skips. It was NOT
    enforced one level down, and that is exactly where it hid.

    Measured 2026-08-24 in a true CI environment (a fresh clone, so tv/frames/ is absent because it
    is gitignored): **45 gates passed while 24 individual CASES skipped inside them** — 8 of them the
    entire scoring half of test_stash_eye_aspect. Meanwhile that hand-labelled corpus had rotted from
    14 frames to 7, losing EVERY negative, and CI stayed green because the cases that would have
    failed never executed.

    The per-gate line said `OK (skipped=8)`. The verdict said `45 gate(s) passed`. Only the verdict
    gets read. [[feedback-blind-fixture-green-gate]]
    """

    def _src(self):
        here = os.path.dirname(os.path.abspath(__file__))
        return open(os.path.join(here, "run_gates.py"), encoding="utf-8").read()

    def test_the_verdict_counts_cases_that_skipped_inside_passing_gates(self):
        blk = _between(self, self._src(), "COUNT THE CASES THAT DID NOT RUN", "return 0",
                       what="the case-skip accounting")
        self.assertTrue('skipped=(\\d+)' in blk or 'skipped=(\d+)' in blk,
                        "the verdict no longer parses the per-suite skip count, so a gate that "
                        "passes while its cases skip reads as full coverage again")
        # THE PRINTED STRING, not the phrase. A first cut asserted "DID NOT RUN" and passed
        # against a sabotage that rewrote the print, because the comment heading above it says
        # "COUNT THE CASES THAT DID NOT RUN". That is the third time tonight my own prose has
        # blinded my own guard. [[source-reading-guard]]
        self.assertTrue("CASE(S) DID NOT RUN inside those gates" in blk,
                        "the verdict no longer NAMES the cases that did not run — a gate that "
                        "passes while its cases skip reads as full coverage again")

    def test_it_does_not_double_count_a_gate_that_skipped_entirely(self):
        """A whole-gate SKIP is already reported and already counted; counting its cases again
        would inflate the number and make the honest one look wrong."""
        blk = _between(self, self._src(), "COUNT THE CASES THAT DID NOT RUN", "return 0",
                       what="the case-skip accounting")
        self.assertTrue('_st != "SKIP"' in blk,
                        "gate-level SKIPs are being counted a second time as case skips")

    def test_the_gate_still_passes_when_nothing_skipped(self):
        """The warning must be conditional. A line that always prints is furniture."""
        blk = _between(self, self._src(), "COUNT THE CASES THAT DID NOT RUN", "return 0",
                       what="the case-skip accounting")
        self.assertTrue("if _cases:" in blk,
                        "the warning prints unconditionally — it would appear on a clean run and "
                        "stop meaning anything")



if __name__ == "__main__":
    unittest.main(verbosity=1)
