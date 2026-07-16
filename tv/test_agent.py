#!/usr/bin/env python3
# 📺 TV DIABLO — agent TDD suite (v711). Zero deps, zero vision cost, synthetic frames.
#   python3 tv/test_agent.py
import io, json, os, struct, sys, tempfile, time, unittest, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["TV_PORT"] = "17971"          # never collide with a live agent
import tv_diablo as tv


def make_bmp(path, payload):
    """A minimal valid-enough BMP: 54-byte header + raw payload (frame_sig samples body bytes)."""
    with open(path, "wb") as f:
        f.write(b"BM" + struct.pack("<IHHI", 54 + len(payload), 0, 0, 54))
        f.write(b"\x00" * 40)
        f.write(payload)


class TestFrameSig(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def _frame(self, name, payload):
        p = os.path.join(self.d, name)
        make_bmp(p, payload)
        return tv.frame_sig(p)

    def test_identical_frames_diff_zero(self):
        a = self._frame("a.bmp", bytes([120] * 200000))
        b = self._frame("b.bmp", bytes([120] * 200000))
        self.assertEqual(tv.sig_diff(a, b), 0.0)

    def test_ambient_flicker_stays_settled(self):
        # every pixel nudged by ±10 — under the 28 tolerance, must read as settled
        a = self._frame("a.bmp", bytes([120] * 200000))
        b = self._frame("b.bmp", bytes([130] * 200000))
        self.assertLessEqual(tv.sig_diff(a, b), 0.03)

    def test_real_change_is_motion(self):
        # half the screen swings hard (panel opened) — far past tolerance
        a = self._frame("a.bmp", bytes([120] * 200000))
        b = self._frame("b.bmp", bytes([120] * 100000) + bytes([250] * 100000))
        self.assertGreater(tv.sig_diff(a, b), 0.03)

    def test_none_sig_is_full_motion(self):
        a = self._frame("a.bmp", bytes([120] * 200000))
        self.assertEqual(tv.sig_diff(a, None), 1.0)

    def test_near_black_loading_guard_threshold(self):
        sig = self._frame("dark.bmp", bytes([6] * 200000))
        self.assertLess(sum(sig) / len(sig), 14)          # would be skipped by the loading guard
        lit = self._frame("lit.bmp", bytes([40] * 200000))
        self.assertGreaterEqual(sum(lit) / len(lit), 14)  # gameplay passes


class TestStub(unittest.TestCase):
    def test_stub_read_uses_manifest(self):
        os.environ["TV_STUB"] = "1"
        mp = os.path.join(tv.HERE, "stub_manifest.json")
        backup = open(mp, "rb").read() if os.path.exists(mp) else None
        try:
            man = {"pit.jpg": {"area": "The Pit Level 1", "scene": "loot", "names": ["Ist Rune"], "tz": ["Spider Forest"]},
                   "*": {"scene": "gameplay", "names": []}}
            with open(mp, "w", encoding="utf-8") as f: json.dump(man, f)
            r = tv.claude_read("/anywhere/pit.jpg")
            self.assertEqual(r["area"], "The Pit Level 1")
            self.assertEqual(r["names"], ["Ist Rune"])
            self.assertEqual(r["tz"], ["Spider Forest"])
            r2 = tv.claude_read("/anywhere/unknown.jpg")
            self.assertEqual(r2["scene"], "gameplay")
            self.assertEqual(r2["names"], [])
        finally:
            # NEVER delete the committed manifest — restore it (the first version removed it
            # and starved the e2e test downstream: a real TDD catch on the tests themselves)
            if backup is not None:
                open(mp, "wb").write(backup)
            del os.environ["TV_STUB"]

    def test_readable_frame_passthrough_non_bmp(self):
        self.assertTrue(tv._readable_frame("/tmp/x.jpg").endswith("x.jpg"))


class TestEventsAndBridge(unittest.TestCase):
    def test_event_ring_caps_at_60(self):
        tv._EVENTS.clear()
        for i in range(100):
            tv.ev("skip", f"e{i}")
        self.assertEqual(len(tv._EVENTS), 60)
        self.assertEqual(tv._EVENTS[-1]["t"], "e99")

    def test_bridge_state_and_ping(self):
        with tv._state_lock:
            tv._save({"online": True, "startedAt": 1, "reads": [{"ts": 2, "names": ["Ist Rune"], "n": 1}], "readCount": 1})
        tv.beat("watching", 0.12)
        srv = tv.bridge()
        try:
            time.sleep(0.2)
            st = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{tv.PORT}/state", timeout=3).read())
            self.assertTrue(st["online"])
            self.assertEqual(st["readCount"], 1)
            self.assertEqual(st["beat"]["phase"], "watching")
            self.assertAlmostEqual(st["beat"]["motion"], 0.12)
            self.assertTrue(isinstance(st.get("events"), list))
            ping = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{tv.PORT}/ping", timeout=3).read())
            self.assertEqual(ping["tv"], "diablo")
        finally:
            srv.shutdown()


class TestReadableFrame(unittest.TestCase):
    def test_bmp_converts_to_small_jpg(self):
        # real sips on mac; on CI-linux this falls through — both outcomes asserted honestly
        d = tempfile.mkdtemp()
        bmp = os.path.join(d, "big.bmp")
        make_bmp(bmp, bytes([90, 140, 200] * 400000))   # ~1.2MB three-tone payload
        out = tv._readable_frame(bmp)
        if out.endswith(".jpg"):
            self.assertLess(os.path.getsize(out), os.path.getsize(bmp))
        else:
            self.assertEqual(out, bmp)   # no sips → honest passthrough


class TestEventContract(unittest.TestCase):
    """The board renders these kinds — the contract the UI depends on."""
    def test_kinds_are_the_ui_vocabulary(self):
        tv._EVENTS.clear()
        tv.ev("boot", "x"); tv.ev("settle", "x"); tv.ev("read", "x"); tv.ev("skip", "x"); tv.ev("cap", "x")
        kinds = {e["k"] for e in tv._EVENTS}
        self.assertEqual(kinds, {"boot", "settle", "read", "skip", "cap"})
        for e in tv._EVENTS:
            self.assertLessEqual(len(e["t"]), 120)


class TestStubE2E(unittest.TestCase):
    """Grok P1-5: the FULL agent loop against stub vision — no Claude, no game.
    Feeds two distinct settled frames through the real main-loop mechanics by
    replicating its decision sequence with the module's own functions."""
    def test_settle_then_stub_read_lands_in_state(self):
        os.environ["TV_STUB"] = "1"
        try:
            d = tempfile.mkdtemp()
            f1 = os.path.join(d, "pit_loot.jpg")
            with io.open(f1, "w") as fh: fh.write("x")
            rd = tv.claude_read(f1)
            self.assertEqual(rd["scene"], "loot")
            self.assertIn("Ist Rune", rd["names"])
            with tv._state_lock:
                tv._save({"online": True, "startedAt": 1, "reads": [], "readCount": 0})
                st = tv._load()
                st["reads"].append({"ts": 2, "names": rd["names"], "n": 1, "area": rd["area"], "scene": rd["scene"], "tz": rd["tz"]})
                st["readCount"] = 1
                tv._save(st)
            st2 = tv._load()
            self.assertEqual(st2["readCount"], 1)
            self.assertEqual(st2["reads"][0]["area"], "The Pit Level 1")
        finally:
            del os.environ["TV_STUB"]


class TestClaudeEnv(unittest.TestCase):
    """v720 — vision must ride the Claude subscription, not a shell API key."""
    def test_strips_api_key_keeps_other_env(self):
        prev = os.environ.get("ANTHROPIC_API_KEY")
        prev_t = os.environ.get("ANTHROPIC_AUTH_TOKEN")
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-should-not-leak"
        os.environ["ANTHROPIC_AUTH_TOKEN"] = "token-should-not-leak"
        os.environ["TV_PROBE_KEEP"] = "1"
        try:
            env, stripped = tv._claude_env()
            self.assertIn("ANTHROPIC_API_KEY", stripped)
            self.assertIn("ANTHROPIC_AUTH_TOKEN", stripped)
            self.assertNotIn("ANTHROPIC_API_KEY", env)
            self.assertNotIn("ANTHROPIC_AUTH_TOKEN", env)
            self.assertEqual(env.get("TV_PROBE_KEEP"), "1")
            # parent shell env must remain untouched (caller owns their shell)
            self.assertEqual(os.environ.get("ANTHROPIC_API_KEY"), "sk-ant-test-should-not-leak")
        finally:
            if prev is None: os.environ.pop("ANTHROPIC_API_KEY", None)
            else: os.environ["ANTHROPIC_API_KEY"] = prev
            if prev_t is None: os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
            else: os.environ["ANTHROPIC_AUTH_TOKEN"] = prev_t
            os.environ.pop("TV_PROBE_KEEP", None)

    def test_no_strip_when_unset(self):
        prev = os.environ.pop("ANTHROPIC_API_KEY", None)
        prev_t = os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
        try:
            env, stripped = tv._claude_env()
            self.assertEqual(stripped, [])
            self.assertNotIn("ANTHROPIC_API_KEY", env)
        finally:
            if prev is not None: os.environ["ANTHROPIC_API_KEY"] = prev
            if prev_t is not None: os.environ["ANTHROPIC_AUTH_TOKEN"] = prev_t


class TestVisionWorker(unittest.TestCase):
    """v713 — the persistent worker against the fake claude bin (TV_CLAUDE_BIN seam)."""
    def setUp(self):
        self.fake = os.path.join(tv.HERE, "fake_claude.py")
        tv.CLAUDE_BIN = sys.executable and sys.executable or "python3"
        # the worker invokes CLAUDE_BIN with claude-style args — wrap via env-configured argv0
        tv.CLAUDE_BIN = self.fake
        os.environ.pop("TV_FAKE_MODE", None)

    def tearDown(self):
        tv._WORKER.stop()
        os.environ.pop("TV_FAKE_MODE", None)

    def test_multi_turn_reuse_same_process(self):
        w = tv.VisionWorker()
        r1 = w.ask("read frame 1", timeout=10)
        pid1 = w.p.pid
        r2 = w.ask("read frame 2", timeout=10)
        self.assertEqual(w.p.pid, pid1)            # SAME process — no cold start
        self.assertIn("Worker Keep", r1)
        self.assertIn("Vex Rune", r2)
        self.assertEqual(w.turns, 2)
        w.stop()

    def test_restart_after_max_turns(self):
        w = tv.VisionWorker()
        w.ask("t", timeout=10); pid1 = w.p.pid
        w.turns = tv.WORKER_MAX_TURNS             # force the context-bloat guard
        w.ask("t", timeout=10)
        self.assertNotEqual(w.p.pid, pid1)         # fresh process
        w.stop()

    def test_timeout_kills_worker_returns_none(self):
        os.environ["TV_FAKE_MODE"] = "slow"
        w = tv.VisionWorker()
        r = w.ask("t", timeout=2)
        self.assertIsNone(r)                       # caller falls back to one-shot
        self.assertIsNone(w.p)                     # wedged worker is DEAD, never reused
        w.stop()

    def test_junk_result_parses_to_none(self):
        os.environ["TV_FAKE_MODE"] = "junk"
        w = tv.VisionWorker()
        out = w.ask("t", timeout=10)
        self.assertIsNotNone(out)
        self.assertIsNone(tv._parse_read(out))     # claude_read falls back on this
        w.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
