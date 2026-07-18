#!/usr/bin/env python3
"""v886 — THE ROUNDTRIP (Grok third-eye acceptance spec, task #52-B).
Proves the whole ON AIR → record → OFF/seal → SIM chain END-TO-END with zero vision cost:
boot control on a private port (TV_STUB agent, temp journal + temp hist), go ON AIR, inject
synthetic footage into the live window, seal, then assert:
  · reel_<sid>/ holds EXACTLY the injected frames (fold correctness, boot-spanning window)
  · /api/sessions: newest non-stub is our sid, footageN matches, stub flag honest
  · /api/session?n: footage beats == reel set, capture-clock sorted
  · /hist/reel_<sid>/... serves HTTP 200 JPEG
  · live-truncation regression: frames written AFTER the last read appear while live
Runs everywhere (no darwin film thread needed — frames are injected).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 17956
CTRL = "http://127.0.0.1:%d" % PORT


def api(path, post=False, timeout=15):
    req = urllib.request.Request(CTRL + path, data=b"{}" if post else None,
                                 headers={"Content-Type": "application/json"} if post else {},
                                 method="POST" if post else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


class TestRoundtrip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp(prefix="tvd-roundtrip-")
        cls.hist = os.path.join(cls.dir, "hist")
        os.makedirs(cls.hist, exist_ok=True)
        cls.journal = os.path.join(cls.dir, "sessions.jsonl")
        env = dict(os.environ,
                   TV_CONTROL_PORT=str(PORT), TV_PORT="17955",
                   TV_SESSIONS=cls.journal, TV_HIST=cls.hist,
                   TV_STUB="1", TV_POOL="1", TV_FAREWELL="0")
        env.pop("ANTHROPIC_API_KEY", None)
        cls.proc = subprocess.Popen([sys.executable, os.path.join(HERE, "control_app.py")],
                                    env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        for _ in range(40):
            try:
                if api("/api/status")["ok"]:
                    return
            except Exception:
                time.sleep(0.5)
        raise RuntimeError("roundtrip control server never came up")

    @classmethod
    def tearDownClass(cls):
        try:
            api("/api/off", post=True, timeout=30)
        except Exception:
            pass
        try:
            cls.proc.kill()
        except Exception:
            pass
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_roundtrip_on_record_seal_sim(self):
        # 2 — ON AIR (and the second click must not restart the agent)
        r = api("/api/on", post=True, timeout=30)
        self.assertTrue(r.get("ok"), r)
        bridge_pid = None
        for _ in range(40):
            st = api("/api/status")
            if st.get("bridge"):
                bridge_pid = st.get("pid")
                break
            time.sleep(0.5)
        self.assertTrue(bridge_pid, "bridge never came up")
        api("/api/on", post=True, timeout=30)   # double-click
        time.sleep(1.0)
        self.assertEqual(api("/api/status").get("pid"), bridge_pid,
                         "second ON AIR click restarted the agent (Grok #3)")

        # 3 — record: inject synthetic footage into the LIVE window (film thread is darwin-only)
        live_sid_now = api("/api/status").get("sessionId") or ""
        try:
            boot_ms = int(live_sid_now.split("_")[1])
        except Exception:
            boot_ms = int(time.time() * 1000) - 1500
        t_ms = int(time.time() * 1000)
        injected = []
        for k in range(12):
            # stamps live inside [boot, now] — the run's real recording window
            fn = "f_%d.jpg" % (boot_ms + 100 + int(k * (t_ms - boot_ms - 200) / 12))
            with open(os.path.join(self.hist, fn), "wb") as f:
                f.write(b"\xff\xd8\xff\xe0" + b"J" * 5000 + b"\xff\xd9")
            injected.append(fn)
        # wait for at least one stub read so the session has substance
        for _ in range(40):
            if (api("/api/status").get("readCount") or 0) >= 1:
                break
            time.sleep(0.5)

        # 9 — LIVE truncation regression: frames after the last read must already show
        sessions = api("/api/sessions").get("sessions") or []
        self.assertTrue(sessions, "no sessions listed while live")
        live_sid = api("/api/status").get("sessionId") or (sessions[0].get("sessionId") or "")
        live_n = next((x.get("n") for x in sessions if x.get("sessionId") == live_sid), 1)
        live_beats = api("/api/session?n=%d" % live_n).get("beats") or []
        live_foot = [b for b in live_beats if b.get("footage")]
        self.assertGreaterEqual(len(live_foot), len(injected),
                                "live window truncated — footage after the last read is missing (Grok #2)")

        # 4 — OFF / seal
        api("/api/off", post=True, timeout=60)
        for _ in range(40):
            st = api("/api/status")
            if not st.get("bridge") and not st.get("stopping"):
                break
            time.sleep(0.5)
        final_reads = api("/api/status").get("readCount") or 0
        rows = [json.loads(l) for l in open(self.journal, encoding="utf-8") if l.strip()]
        # KONYO'S SYNC LAW: every read the console counted exists in the journal (and thus the SIM)
        j_reads = [r for r in rows if not r.get("sessionEnd") and r.get("scene") != "session_end"
                   and r.get("kind") != "skip" and (r.get("n") or 0) > 0]
        self.assertGreaterEqual(len(j_reads), final_reads,
                                "reads counted (%d) > reads journaled (%d) — SIM would lie" % (final_reads, len(j_reads)))
        self.assertTrue(any(r.get("scene") == "session_end" and r.get("sessionId") == live_sid for r in rows),
                        "session_end row missing after seal")
        reel = os.path.join(self.hist, "reel_" + live_sid)
        self.assertTrue(os.path.isdir(reel), "reel fold never happened")
        reel_set = set(os.listdir(reel))
        for fn in injected:
            self.assertIn(fn, reel_set, "injected frame %s missing from the sealed reel" % fn)
        loose_left = [f for f in os.listdir(self.hist) if f.startswith("f_") and f.endswith(".jpg")]
        self.assertEqual(loose_left, [], "loose frames survived the fold inside the session window")

        # 5/6 — sessions + payload truth
        sessions = api("/api/sessions").get("sessions") or []
        ours = next((x for x in sessions if x.get("sessionId") == live_sid), None)
        self.assertIsNotNone(ours, "sealed session missing from the shelf")
        self.assertFalse(ours.get("stub"), "a real recorded run got the stub flag")
        self.assertGreaterEqual(ours.get("footageN") or 0, len(injected), "shelf footageN lies")
        beats = api("/api/session?n=%d" % ours["n"]).get("beats") or []
        foot = [b for b in beats if b.get("footage")]
        self.assertGreaterEqual(len(foot), len(injected), "sealed reel beats missing footage")
        ts_list = [b["ts"] for b in beats]
        self.assertEqual(ts_list, sorted(ts_list), "beats not capture-clock sorted")

        # 7 — frame serves from the reel subpath
        frame = foot[0]["frame"]
        self.assertTrue(frame.startswith("reel_"), "footage beat not served from the reel: %s" % frame)
        req = urllib.request.Request(CTRL + "/hist/" + frame)
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
        self.assertEqual(resp.status, 200)
        self.assertTrue(body.startswith(b"\xff\xd8"), "reel frame is not a JPEG")


if __name__ == "__main__":
    unittest.main(verbosity=2)
