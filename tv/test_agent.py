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
        try:
            man = {"pit.jpg": {"area": "The Pit Level 1", "scene": "loot", "names": ["Ist Rune"], "tz": ["Spider Forest"]},
                   "*": {"scene": "gameplay", "names": []}}
            mp = os.path.join(tv.HERE, "stub_manifest.json")
            with open(mp, "w", encoding="utf-8") as f: json.dump(man, f)
            r = tv.claude_read("/anywhere/pit.jpg")
            self.assertEqual(r["area"], "The Pit Level 1")
            self.assertEqual(r["names"], ["Ist Rune"])
            self.assertEqual(r["tz"], ["Spider Forest"])
            r2 = tv.claude_read("/anywhere/unknown.jpg")
            self.assertEqual(r2["scene"], "gameplay")
            self.assertEqual(r2["names"], [])
            os.remove(mp)
        finally:
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
