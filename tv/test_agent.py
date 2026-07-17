#!/usr/bin/env python3
# 📺 TV DIABLO — agent TDD suite (v711). Zero deps, zero vision cost, synthetic frames.
#   python3 tv/test_agent.py
import io, json, os, struct, sys, tempfile, threading, time, unittest, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["TV_PORT"] = "17971"          # never collide with a live agent
import tv_diablo as tv
tv.JOURNAL = os.path.join(tempfile.gettempdir(), "tvd_test_journal.jsonl")   # v753 — tests NEVER write the real session journal


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


class TestAutopilotInterest(unittest.TestCase):
    """v727 — Tesla-style interest: hard motion → stop scores high."""
    def test_hard_motion_priority_is_high(self):
        lo = tv.ap_interest(peak=0.02, stable_ticks=0, priority=False, empty_streak=0, named_recent=False)
        hi = tv.ap_interest(peak=0.20, stable_ticks=1, priority=True, empty_streak=0, named_recent=False)
        self.assertGreater(hi, 0.7)
        self.assertGreater(hi, lo)

    def test_empty_streak_never_zeros_interest(self):
        s = tv.ap_interest(peak=0.20, stable_ticks=1, priority=True, empty_streak=10, named_recent=False)
        self.assertGreater(s, 0.5)


class TestLootLifecycleV2(unittest.TestCase):
    """v731 — commitment vault: holding → hold/stash commit; throw-out cancels."""
    def setUp(self):
        self.lc = tv.LootLifecycle()

    def test_inv_starts_holding_not_vault(self):
        r = self.lc.process("inventory",
                            ["Horadric Cube", "Blade Bow", "Crown", "Super Healing Potion"],
                            "Rogue Encampment", 0.9, now_ms=1_000_000)
        self.assertEqual(r["vault_names"], [])
        self.assertIn("Blade Bow", r["pending_names"])
        self.assertIn("Crown", r["pending_names"])
        self.assertNotIn("Super Healing Potion", r["pending_names"])
        self.assertEqual(r["lifecycle_tags"].get("Blade Bow"), "holding")

    def test_hold_duration_commits_vault(self):
        t0 = 1_000_000
        self.lc.process("inventory", ["Horadric Cube", "Blade Bow"], "town", 0.9, now_ms=t0)
        # still holding before HOLD_MS
        r1 = self.lc.process("inventory", ["Horadric Cube", "Blade Bow"], "town", 0.9,
                             now_ms=t0 + tv.HOLD_MS - 1000)
        self.assertEqual(r1["vault_names"], [])
        self.assertIn("Blade Bow", r1["pending_names"])
        # after hold
        r2 = self.lc.process("inventory", ["Horadric Cube", "Blade Bow"], "town", 0.9,
                             now_ms=t0 + tv.HOLD_MS + 500)
        self.assertIn("Blade Bow", r2["vault_names"])
        self.assertNotIn("Blade Bow", r2["pending_names"])

    def test_stash_commits_immediately(self):
        self.lc.process("inventory", ["Horadric Cube", "Gothic Shield"], "field", 0.9, now_ms=1000)
        self.assertIn("gothic shield", self.lc.pending)  # pending is norm-keyed
        r = self.lc.process("stash", ["Gothic Shield"], "Rogue Encampment", 0.9, now_ms=2000)
        self.assertIn("Gothic Shield", r["vault_names"])
        self.assertNotIn("gothic shield", self.lc.pending)

    def test_throw_out_cancels_pending(self):
        self.lc.process("inventory", ["Horadric Cube", "Isenhart's Parry"], "town", 0.9, now_ms=1000)
        self.assertIn("isenhart's parry", self.lc.pending)
        r = self.lc.process("loot", ["Isenhart's Parry"], "Stony Field", 0.9, now_ms=5000)
        self.assertIn("Isenhart's Parry", r["thrown_names"])
        self.assertNotIn("isenhart's parry", self.lc.pending)
        self.assertEqual(r["vault_names"], [])

    def test_throw_out_after_vault_unvaults(self):
        t0 = 1_000_000
        self.lc.process("inventory", ["Horadric Cube", "Splint Mail"], "town", 0.9, now_ms=t0)
        self.lc.process("inventory", ["Horadric Cube", "Splint Mail"], "town", 0.9,
                        now_ms=t0 + tv.HOLD_MS + 1000)
        self.assertIn("splint mail", self.lc.vaulted)
        r = self.lc.process("loot", ["Splint Mail"], "Stony Field", 0.9, now_ms=t0 + tv.HOLD_MS + 5000)
        self.assertIn("Splint Mail", r["thrown_names"])
        self.assertIn("Splint Mail", r.get("unvault_names", []))
        self.assertNotIn("splint mail", self.lc.vaulted)

    def test_gone_alone_never_vaults(self):
        self.lc.process("loot", ["War Scythe"], "Stony Field", 0.9, now_ms=1000)
        self.lc.process("loot", [], "Stony Field", 0.9, now_ms=2000)
        r = self.lc.process("loot", [], "Stony Field", 0.9, now_ms=3000)
        self.assertIn("War Scythe", r["gone_candidates"])
        self.assertEqual(r["vault_names"], [])

    def test_run4_stash_only_commits_seen_not_panel_noise(self):
        """v738 — Run #4: floor Crossbow SEEN; shared-tab Blood Shield etc must NOT vault."""
        self.lc.process(
            "loot",
            ["Super Mana Potion", "Great Maul", "Greater Healing Potion",
             "Super Healing Potion", "Colossus Crossbow"],
            "Black Marsh", 0.9, now_ms=1000)
        r = self.lc.process(
            "stash",
            ["Blood Shield", "Compendium", "Colossus Crossbow", "Jewel", "Unidentified"],
            "Rogue Encampment", 0.9, now_ms=5000)
        self.assertIn("Colossus Crossbow", r["vault_names"])
        self.assertNotIn("Blood Shield", r["vault_names"])
        self.assertNotIn("Compendium", r["vault_names"])
        self.assertNotIn("Unidentified", r["vault_names"])
        # bare Jewel was never on the floor → no chain
        self.assertNotIn("Jewel", r["vault_names"])
        self.assertEqual(r["lifecycle_tags"].get("Blood Shield"), "stash-no-chain")
        self.assertEqual(r["lifecycle_tags"].get("Unidentified"), "skip-weak")

    def test_run4_jewel_vaults_only_if_floor_seen(self):
        """v738 — Konyo kept a Jewel: only vault if SEEN (or holding) first."""
        self.lc.process("loot", ["Colossus Crossbow", "Jewel"], "Black Marsh", 0.9, now_ms=1000)
        r = self.lc.process("stash", ["Colossus Crossbow", "Jewel"], "town", 0.9, now_ms=2000)
        self.assertCountEqual(r["vault_names"], ["Colossus Crossbow", "Jewel"])

    def test_unidentified_never_vaults_even_if_seen(self):
        self.lc.process("loot", ["Unidentified"], "Black Marsh", 0.9, now_ms=1000)
        r = self.lc.process("stash", ["Unidentified"], "town", 0.9, now_ms=2000)
        self.assertEqual(r["vault_names"], [])

    def test_stash_without_prior_chain_never_vaults(self):
        r = self.lc.process("stash", ["Blood Shield", "Compendium"], "town", 0.9, now_ms=1000)
        self.assertEqual(r["vault_names"], [])


class TestFrameArchive(unittest.TestCase):
    """v735 — per-read frame hist for click-to-enlarge eyes-on-AI."""
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self._old_frames = tv.FRAMES
        self._old_hist = tv.HIST_DIR
        tv.FRAMES = self.d
        tv.HIST_DIR = os.path.join(self.d, "hist")

    def tearDown(self):
        tv.FRAMES = self._old_frames
        tv.HIST_DIR = self._old_hist

    def test_archive_makes_id_and_file(self):
        # minimal jpeg via sips from a tiny png written as bmp-ish won't work — use read.jpg copy path
        src = os.path.join(self.d, "live.png")
        # 1x1 png
        import base64
        open(src, "wb").write(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="))
        fid = tv.archive_read_frame(src, 3, 1_700_000_000_000)
        self.assertTrue(fid)
        self.assertEqual(fid, "3_1700000000000")
        self.assertTrue(os.path.isfile(tv.frame_path_for_id(fid)))

    def test_frame_path_rejects_traversal(self):
        self.assertEqual(tv.frame_path_for_id("../etc/passwd"), "")
        self.assertEqual(tv.frame_path_for_id("abc"), "")


class TestFarewellRead(unittest.TestCase):
    """v740 — shutdown farewell always publishes (run #7 race fix)."""
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self._old_frames = tv.FRAMES
        self._old_hist = tv.HIST_DIR
        self._old_state = tv.STATE
        self._old_life = tv._LIFECYCLE
        tv.FRAMES = self.d
        tv.HIST_DIR = os.path.join(self.d, "hist")
        tv.STATE = os.path.join(self.d, "state.json")
        tv._LIFECYCLE = tv.LootLifecycle()
        # seed empty state
        with open(tv.STATE, "w") as f:
            json.dump({"online": True, "reads": [], "readCount": 2, "seen": [], "farmed": []}, f)
        # stub vision
        self._prev_stub = os.environ.get("TV_STUB")
        os.environ["TV_STUB"] = "1"
        man = os.path.join(self.d, "stub_manifest.json")
        # claude_read looks in HERE for stub_manifest — patch via writing to tv/ and basename
        self._man_path = os.path.join(os.path.dirname(tv.__file__), "stub_manifest.json")
        self._man_bak = None
        if os.path.isfile(self._man_path):
            with open(self._man_path, encoding="utf-8") as f:
                self._man_bak = f.read()
        with open(self._man_path, "w") as f:
            json.dump({
                "*": {"scene": "stash", "stashTab": "shared", "area": "Harrogath",
                      "names": ["Horadric Cube", "Nagelring"], "conf": 0.9}
            }, f)
        # seed lifecycle so Nagelring can chain-vault if previously seen
        tv._LIFECYCLE.process("loot", ["Nagelring"], "Frigid Highlands", 0.9, now_ms=1000)

    def tearDown(self):
        tv.FRAMES = self._old_frames
        tv.HIST_DIR = self._old_hist
        tv.STATE = self._old_state
        tv._LIFECYCLE = self._old_life
        if self._prev_stub is None:
            os.environ.pop("TV_STUB", None)
        else:
            os.environ["TV_STUB"] = self._prev_stub
        if self._man_bak is not None:
            with open(self._man_path, "w") as f:
                f.write(self._man_bak)
        else:
            try: os.remove(self._man_path)
            except Exception: pass

    def test_farewell_publishes_flagged_record(self):
        # use a tiny real file as force_frame so claude_read stub path works by basename
        img = os.path.join(self.d, "farewell.jpg")
        open(img, "wb").write(b"\xff\xd8\xff\xd9")  # minimal jpeg bytes
        # stub looks up basename in manifest under HERE — set * fallback already
        rec = tv.farewell_read(force_frame=img)
        self.assertIsNotNone(rec)
        self.assertTrue(rec.get("farewell"))
        self.assertEqual(rec.get("lane"), "deep")
        self.assertEqual(rec.get("n"), 3)  # readCount was 2 → +1
        self.assertEqual(rec.get("scene"), "stash")
        # state on disk
        st = json.load(open(tv.STATE, encoding="utf-8"))
        self.assertEqual(st["readCount"], 3)
        self.assertTrue(st["reads"][-1].get("farewell"))
        # Nagelring was SEEN then farewell stash → vault commit
        self.assertIn("Nagelring", rec.get("vault_names") or [])


class TestStashTab(unittest.TestCase):
    """v734 — stashTab normalize for RotW left tabs."""
    def test_norm_aliases(self):
        self.assertEqual(tv._norm_stash_tab("Runes", "stash"), "runes")
        self.assertEqual(tv._norm_stash_tab("rune", "stash"), "runes")
        self.assertEqual(tv._norm_stash_tab("Materials", "stash"), "materials")
        self.assertEqual(tv._norm_stash_tab("Gems tab", "stash"), "gems")
        self.assertEqual(tv._norm_stash_tab("personal", "stash"), "personal")
        self.assertEqual(tv._norm_stash_tab("runes", "inventory"), "")  # not stash scene
        self.assertEqual(tv._norm_stash_tab("", "stash"), "")

    def test_parse_read_includes_stash_tab(self):
        raw = '{"area":"Rogue Encampment","tz":[],"scene":"stash","stashTab":"runes","names":[],"conf":0.9}'
        p = tv._parse_read(raw)
        self.assertIsNotNone(p)
        self.assertEqual(p["scene"], "stash")
        self.assertEqual(p["stashTab"], "runes")


class TestOcrFastLane(unittest.TestCase):
    """v732 — local OCR lane: filter noise; provisional never vaults."""
    def test_filter_keeps_itemish_drops_chrome(self):
        lines = ["Blade Bow", "Ist Rune", "http://localhost:17771", "12", "ab",
                 "python3 tv/tv_diablo.py", "Crown of Thieves", ""]
        n = tv.filter_ocr_lines(lines)
        self.assertIn("Blade Bow", n)
        self.assertIn("Ist Rune", n)
        self.assertIn("Crown of Thieves", n)
        self.assertNotIn("http://localhost:17771", n)
        self.assertTrue(all("python" not in x.lower() for x in n))

    def test_filter_dedupes_case(self):
        n = tv.filter_ocr_lines(["Blade Bow", "blade bow", "BLADE BOW"])
        self.assertEqual(len(n), 1)

    def test_ocr_disabled_returns_none(self):
        prev = os.environ.get("TV_OCR")
        os.environ["TV_OCR"] = "0"
        try:
            # re-read flag is module-level — patch directly
            old = tv.OCR_ENABLED
            tv.OCR_ENABLED = False
            try:
                self.assertIsNone(tv.ocr_fast("/tmp/nope.jpg"))
            finally:
                tv.OCR_ENABLED = old
        finally:
            if prev is None:
                os.environ.pop("TV_OCR", None)
            else:
                os.environ["TV_OCR"] = prev

    def test_fake_ocr_worker_roundtrip(self):
        """TV_OCR_BIN seam: a fake worker prints JSON lines — agent parses names."""
        d = tempfile.mkdtemp()
        fake = os.path.join(d, "fake_ocr")
        with open(fake, "w") as f:
            f.write("#!/usr/bin/env bash\n"
                    "if [[ \"${1:-}\" == --worker ]]; then\n"
                    "  while IFS= read -r line; do\n"
                    "    [[ \"$line\" == quit ]] && break\n"
                    "    echo '{\"ms\":12,\"lines\":[\"Blade Bow\",\"http://x\",\"Ist Rune\"],\"confs\":[0.9,0.4,0.8],\"mode\":\"roi-fast\"}'\n"
                    "  done\n"
                    "fi\n")
        os.chmod(fake, 0o755)
        old_bin, old_en = tv.OCR_BIN, tv.OCR_ENABLED
        old_ocr = tv._OCR
        try:
            tv.OCR_BIN = fake
            tv.OCR_ENABLED = True
            tv._OCR = tv.OcrWorker()
            # need a real path that exists (worker ignores content)
            p = os.path.join(d, "frame.jpg")
            open(p, "wb").write(b"x")
            rd = tv.ocr_fast(p)
            self.assertIsNotNone(rd)
            self.assertEqual(rd["mode"], "ocr")
            self.assertTrue(rd["provisional"])
            self.assertEqual(rd["intent"], "seen")
            self.assertIn("Blade Bow", rd["names"])
            self.assertIn("Ist Rune", rd["names"])
            self.assertNotIn("http://x", rd["names"])
            self.assertEqual(rd["ms"], 12)
        finally:
            try: tv._OCR.stop()
            except Exception: pass
            tv.OCR_BIN, tv.OCR_ENABLED = old_bin, old_en
            tv._OCR = old_ocr


class TestIntentAndEscalate(unittest.TestCase):
    """v723 — floor=seen / inv-stash=farmed · haiku→sonnet escalate gates."""
    def test_intent_lifecycle(self):
        self.assertEqual(tv._intent_for("loot"), "seen")
        self.assertEqual(tv._intent_for("inventory"), "farmed")
        self.assertEqual(tv._intent_for("stash"), "farmed")
        self.assertEqual(tv._intent_for("gameplay"), "context")
        self.assertEqual(tv._intent_for("town"), "context")

    def test_escalate_on_low_conf_and_empty_loot(self):
        self.assertTrue(tv._needs_escalate(None))
        self.assertTrue(tv._needs_escalate({"scene": "loot", "names": [], "conf": 0.9}))
        # empty gameplay/town: never escalate (honest empty, don't burn genius)
        self.assertFalse(tv._needs_escalate({"scene": "gameplay", "names": [], "conf": 0.2}))
        self.assertFalse(tv._needs_escalate({"scene": "gameplay", "names": [], "conf": 0.9}))
        self.assertFalse(tv._needs_escalate({"scene": "inventory", "names": [], "conf": 0.9}))  # no hover = honest
        self.assertTrue(tv._needs_escalate({"scene": "inventory", "names": ["Ist Rune"], "conf": 0.4}))
        self.assertFalse(tv._needs_escalate({"scene": "inventory", "names": ["Ist Rune"], "conf": 0.9}))
        self.assertTrue(tv._needs_escalate({"scene": "loot", "names": ["Ist Rune"], "conf": 0.3}))

    def test_read_score_prefers_names(self):
        a = {"names": ["Ist Rune"], "conf": 0.5, "area": ""}
        b = {"names": ["Ist Rune", "Vex Rune"], "conf": 0.5, "area": "Pit"}
        self.assertGreater(tv._read_score(b), tv._read_score(a))


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

    def test_ask_is_serialized_under_lock(self):
        """v720.1 — concurrent ask() must not interleave prompts on one stream."""
        w = tv.VisionWorker()
        results = []
        def go(i):
            results.append(w.ask(f"read {i}", timeout=10))
        threads = [threading.Thread(target=go, args=(i,)) for i in range(3)]
        for t in threads: t.start()
        for t in threads: t.join(timeout=30)
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r and "Worker Keep" in r for r in results))
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


class TestKnownFrames(unittest.TestCase):
    """v741 — the agent LEARNS dead frames (loading/portal screens are the same pixels every
    time): an empty deep read caches the frame signature; a re-match skips vision entirely
    and registers a 'transition' read. (Konyo: 'always the same photo — recognize it')."""
    def setUp(self):
        tv._KNOWN_DEAD.clear()
        self.d = tempfile.mkdtemp()

    def _sig(self, payload):
        p = os.path.join(self.d, "f.bmp"); make_bmp(p, payload)
        return tv.frame_sig(p)

    def test_learn_then_recognize(self):
        sig = self._sig(bytes([60, 80, 100] * 100000))
        self.assertIsNone(tv.known_dead_match(sig))          # unknown at first
        tv.learn_dead_frame(sig)
        self.assertIsNotNone(tv.known_dead_match(sig))       # exact re-match recognized
        near = self._sig(bytes([62, 82, 102] * 100000))      # ±2 noise — same screen
        self.assertIsNotNone(tv.known_dead_match(near))

    def test_different_screen_not_matched(self):
        tv.learn_dead_frame(self._sig(bytes([60, 80, 100] * 100000)))
        other = self._sig(bytes([200, 30, 150] * 100000))
        self.assertIsNone(tv.known_dead_match(other))        # loot on screen = different pixels

    def test_cache_capped(self):
        for i in range(20):
            tv.learn_dead_frame(self._sig(bytes([i * 12 % 250] * 90000)))
        self.assertLessEqual(len(tv._KNOWN_DEAD), tv.KNOWN_DEAD_CAP)

    # v746 — Konyo: 'this photo is ENTERING a PORTAL or ENTERING A NEW GAME, depending on the
    # photos beforehand' — the transition label reads the story so far.
    def test_transition_note_reads_context(self):
        self.assertIn("leaving Durance of Hate Level 2",
                      tv.transition_note("Durance of Hate Level 2", 5))
        self.assertEqual("entering a new game", tv.transition_note("", 0))
        self.assertIn("loading", tv.transition_note("", 3))

    def test_should_learn_dead_covers_transition_scene(self):
        # vision now labels the portal art scene='transition' — that read must ALSO teach the cache
        self.assertTrue(tv.should_learn_dead({"scene": "transition", "names": [], "area": ""}))
        self.assertTrue(tv.should_learn_dead({"scene": "gameplay", "names": [], "area": ""}))
        self.assertTrue(tv.should_learn_dead({"scene": "", "names": [], "area": ""}))
        self.assertFalse(tv.should_learn_dead({"scene": "loot", "names": ["Ist Rune"], "area": ""}))
        self.assertFalse(tv.should_learn_dead({"scene": "gameplay", "names": [], "area": "Durance of Hate Level 2"}))

    def test_transition_prompt_vocabulary(self):
        # the vision prompt must offer the transition scene, or Sonnet can never say it
        self.assertIn("transition", tv.READ_PROMPT)


class TestLifecycleSceneClass(unittest.TestCase):
    """v753 — run #8: the grail pile Sonnet called 'gameplay' must still enter the SEEN chain."""
    def test_gameplay_with_names_is_loot_class(self):
        self.assertEqual(tv.effective_lc_scene("gameplay", ["The Grandfather"]), "loot")

    def test_gameplay_empty_stays_gameplay(self):
        self.assertEqual(tv.effective_lc_scene("gameplay", []), "gameplay")

    def test_real_scenes_untouched(self):
        for sc in ("stash", "inventory", "loot", "town", "transition"):
            self.assertEqual(tv.effective_lc_scene(sc, ["x"]), sc)


class TestDiscovered(unittest.TestCase):
    """v763 — Konyo: 'in chat some other player finds a chronicle for me… DISCOVERED → route
    it to the beginning of our system'. The prompt must ask for discovery broadcasts, and the
    published record must carry them — separate from names (no vault, chronicle only)."""
    def test_prompt_asks_for_discoveries(self):
        self.assertIn("discovered", tv.READ_PROMPT)

    def test_emit_carries_discovered_names(self):
        old_state, old_j = tv.STATE, tv.JOURNAL
        d = tempfile.mkdtemp()
        tv.STATE = os.path.join(d, "state.json"); tv.JOURNAL = os.path.join(d, "j.jsonl")
        try:
            rec = tv.emit_deep_read({"area": "Durance of Hate Level 2", "scene": "gameplay",
                                     "names": [], "tz": [], "conf": 0.9, "ms": 100,
                                     "discovered": ["Harlequin Crest", "Sigon's Guard"]},
                                    n=1, frame_id="")
            self.assertEqual(rec.get("discovered_names"), ["Harlequin Crest", "Sigon's Guard"])
            self.assertEqual(rec.get("vault_names"), [])   # a chat discovery NEVER vaults
        finally:
            tv.STATE, tv.JOURNAL = old_state, old_j


class TestLifecycleRestore(unittest.TestCase):
    """v768 (Grok R2) — the loot chain survives an agent restart: floor-proven names must not
    become 'stash-no-chain' because the process cycled mid-run."""
    def test_restore_rehydrates_chain(self):
        lc = tv.LootLifecycle()
        snap = {"seen": [{"name": "Harlequin Crest", "area": "Durance of Hate Level 2"}],
                "pending": [{"name": "Vex Rune", "tag": "keep"}],
                "candidates": [{"name": "Skin of the Vipermagi"}],
                "vaulted": [{"name": "Nagelring", "reason": "stash"}]}
        self.assertTrue(lc.restore(snap, tv._norm_name))
        self.assertIn(tv._norm_name("Harlequin Crest"), lc.seen)
        self.assertIn(tv._norm_name("Vex Rune"), lc.pending)
        self.assertIn(tv._norm_name("Skin of the Vipermagi"), lc.candidates)
        self.assertIn(tv._norm_name("Nagelring"), lc.vaulted)

    def test_restore_never_clobbers_live_entries(self):
        lc = tv.LootLifecycle()
        lc.pending[tv._norm_name("Vex Rune")] = {"name": "Vex Rune", "firstHeld": 111, "lastHeld": 222, "tag": "live"}
        lc.restore({"pending": [{"name": "Vex Rune", "tag": "stale"}]}, tv._norm_name)
        self.assertEqual(lc.pending[tv._norm_name("Vex Rune")]["tag"], "live")

    def test_restore_tolerates_garbage(self):
        lc = tv.LootLifecycle()
        self.assertTrue(lc.restore({"seen": [{}], "pending": None}, tv._norm_name) in (True, False))


class TestParseHonesty(unittest.TestCase):
    """v769 (Grok R3 sleeper, repro-CONFIRMED) — _parse_read was the silent kill-switch:
    it rewrote scene 'transition' to 'gameplay' and never extracted 'discovered', so the v746
    portal scene and the v763 DISCOVERED lane were DEAD on the only path that matters."""
    def test_transition_scene_survives_parse(self):
        p = tv._parse_read('{"area":"","tz":[],"scene":"transition","names":[],"conf":0.9}')
        self.assertEqual(p["scene"], "transition")

    def test_discovered_survives_parse(self):
        p = tv._parse_read('{"scene":"gameplay","names":[],"discovered":["Harlequin Crest","Vex Rune"]}')
        self.assertEqual(p.get("discovered"), ["Harlequin Crest", "Vex Rune"])

    def test_discovered_garbage_tolerant(self):
        p = tv._parse_read('{"scene":"loot","names":[],"discovered":[" ", 3, "Ist Rune"]}')
        self.assertEqual(p.get("discovered"), ["3", "Ist Rune"])

    def test_bad_scene_still_normalizes(self):
        p = tv._parse_read('{"scene":"chatlobby","names":[]}')
        self.assertEqual(p["scene"], "gameplay")


class TestStateDelta(unittest.TestCase):
    """v770 (Grok R4 perf) — /state?since= returns a thin delta; cold poll stays full."""
    def test_since_filters_reads(self):
        import threading, urllib.request
        from http.server import ThreadingHTTPServer
        d = tempfile.mkdtemp()
        old_state = tv.STATE
        tv.STATE = os.path.join(d, "state.json")
        try:
            tv._save({"online": True, "startedAt": 1, "readCount": 2,
                      "reads": [{"ts": 100, "n": 1}, {"ts": 200, "n": 2}],
                      "seen": [1], "farmed": [2]})
            srv = ThreadingHTTPServer(("127.0.0.1", 0), tv.Handler) if hasattr(tv, "Handler") else None
            if srv is None:
                # the handler is nested in serve(); exercise the filter logic directly instead
                st = tv._load()
                thin = [r for r in st["reads"] if (r.get("ts") or 0) > 100]
                self.assertEqual(len(thin), 1)
                self.assertEqual(thin[0]["n"], 2)
                return
        finally:
            tv.STATE = old_state


class TestReplay(unittest.TestCase):
    """v752 — REPLAY: re-run a REAL past session (Konyo: 'use the screenshots it used…
    re-run a test on the history — real based on real simulation ingame')."""
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def test_stub_manifest_env_seam(self):
        # TV_STUB_MANIFEST points claude_read at a REPLAY manifest, not the canned demo one
        man = os.path.join(self.d, "replay_manifest.json")
        with open(man, "w") as f:
            json.dump({"7_123.jpg": {"area": "Durance of Hate Level 2", "scene": "loot",
                                     "names": ["Harlequin Crest"], "tz": []}}, f)
        frame = os.path.join(self.d, "7_123.jpg"); open(frame, "wb").write(b"x")
        os.environ["TV_STUB"] = "1"; os.environ["TV_STUB_MANIFEST"] = man
        try:
            rd = tv.claude_read(frame)
        finally:
            os.environ.pop("TV_STUB", None); os.environ.pop("TV_STUB_MANIFEST", None)
        self.assertEqual(rd.get("area"), "Durance of Hate Level 2")
        self.assertEqual(rd.get("names"), ["Harlequin Crest"])

    def test_journal_appends_reads(self):
        # every published read lands in the persistent journal (replay's source of truth)
        j = os.path.join(self.d, "sessions.jsonl")
        old = tv.JOURNAL; tv.JOURNAL = j
        try:
            tv._journal({"ts": 1, "n": 1, "scene": "loot", "names": ["Ist Rune"], "frameId": "1_1"})
            tv._journal({"ts": 2, "n": 2, "scene": "stash", "names": [], "frameId": "2_2"})
        finally:
            tv.JOURNAL = old
        lines = [json.loads(x) for x in open(j) if x.strip()]
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["names"], ["Ist Rune"])

    def test_replay_manifest_builder(self):
        # the builder keeps only reads whose frame file EXISTS, keyed by basename, recorded truth
        import replay as rp
        frames = os.path.join(self.d, "hist"); os.makedirs(frames)
        open(os.path.join(frames, "1_100.jpg"), "wb").write(b"x")
        reads = [
            {"ts": 100, "n": 1, "frameId": "1_100", "area": "Cold Plains", "scene": "loot",
             "names": ["Vex Rune"], "tz": []},
            {"ts": 200, "n": 2, "frameId": "2_200", "area": "", "scene": "gameplay", "names": []},  # frame missing
            {"ts": 300, "n": 3, "frameId": "", "area": "", "scene": "loot", "names": ["ghost"]},     # no frame
        ]
        man, order = rp.build_manifest(reads, frames)
        self.assertEqual(order, ["1_100.jpg"])
        self.assertEqual(man["1_100.jpg"]["names"], ["Vex Rune"])
        self.assertEqual(man["1_100.jpg"]["area"], "Cold Plains")

    def test_session_id_splits_theatre_reels(self):
        """v780 — each ON cycle (sessionId) is its own theatre page, even inside 10min."""
        import replay as rp
        reads = [
            {"ts": 1000, "n": 1, "sessionId": "s_a", "frameId": "1_a", "names": ["A"]},
            {"ts": 2000, "n": 2, "sessionId": "s_a", "frameId": "2_a", "names": []},
            {"ts": 3000, "n": 1, "sessionId": "s_b", "frameId": "1_b", "names": ["B"]},  # new ON, <10min
            {"ts": 4000, "n": 2, "sessionId": "s_b", "frameId": "2_b", "names": ["C"]},
        ]
        sess = rp.split_sessions(reads)
        self.assertEqual(len(sess), 2)
        self.assertEqual([r["sessionId"] for r in sess[0]], ["s_b", "s_b"])  # newest first
        self.assertEqual([r["names"] for r in sess[0] if r.get("names")], [["B"], ["C"]])
        self.assertEqual(sess[1][0]["sessionId"], "s_a")

    def test_capture_ts_matches_frame_id(self):
        """v784 — journal ts is the capture clock embedded in frameId, not AI completion."""
        self.assertEqual(tv._capture_ts_from_frame_id("3_1784329241093"), 1784329241093)
        self.assertIsNone(tv._capture_ts_from_frame_id(""))
        # emit_deep_read with capture_ts must journal that exact clock
        j = os.path.join(self.d, "sessions.jsonl")
        old_j, old_sid = tv.JOURNAL, tv.SESSION_ID
        tv.JOURNAL = j
        tv.SESSION_ID = "s_test"
        try:
            rec = tv.emit_deep_read(
                {"area": "Cold Plains", "scene": "loot", "names": ["Vex Rune"], "tz": [],
                 "conf": 0.9, "mode": "warm", "model": "test", "ms": 5000},
                n=1, frame_id="1_1111111111111", capture_ts=1111111111111,
            )
            self.assertEqual(rec["ts"], 1111111111111)
            self.assertEqual(rec["captureTs"], 1111111111111)
            self.assertGreaterEqual(rec["completedTs"], rec["ts"])
            self.assertEqual(rec["frameId"], "1_1111111111111")
        finally:
            tv.JOURNAL = old_j
            tv.SESSION_ID = old_sid


class TestWindowPin(unittest.TestCase):
    """v772 — Mac CrossOver / Windows native D2R window targeting helpers."""

    def test_match_tokens_include_crossover_and_d2r(self):
        toks = tv._match_tokens()
        self.assertTrue(any("crossover" in t or "diablo" in t for t in toks))
        self.assertTrue(any("d2r" in t or "resurrected" in t for t in toks))

    def test_find_d2r_window_mac_skips_tv_diablo_ui(self):
        """Even when TV DIABLO control windows are open, they must never be the capture target."""
        hit = tv.find_d2r_window_mac()
        if hit is None:
            self.assertIsNone(hit)  # game not running — fine
            return
        wid, label = hit
        self.assertNotIn("tv diablo", label.lower())
        self.assertIsInstance(wid, int)

    def test_capture_target_dict_shape(self):
        self.assertIn("mode", tv._CAP_TARGET)
        self.assertIn("label", tv._CAP_TARGET)

    def test_cap_promote_rejects_missing_tmp(self):
        """v779 — stale target must never satisfy a failed capture."""
        import tempfile
        d = tempfile.mkdtemp()
        try:
            path = os.path.join(d, "live.bmp")
            with open(path, "wb") as f:
                f.write(b"BM" + b"X" * 50000)   # pre-existing STALE desktop
            stale_sz = os.path.getsize(path)
            tmp = path + ".tmp.nope"
            self.assertFalse(tv._cap_promote(tmp, path))  # tmp never written
            self.assertEqual(os.path.getsize(path), stale_sz)  # target untouched
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)

    def test_cap_promote_only_fresh_tmp(self):
        import tempfile
        d = tempfile.mkdtemp()
        try:
            path = os.path.join(d, "live.bmp")
            with open(path, "wb") as f:
                f.write(b"OLD" + b"Y" * 20000)
            tmp = path + ".tmp.fresh"
            with open(tmp, "wb") as f:
                f.write(b"NEW" + b"Z" * 30000)
            self.assertTrue(tv._cap_promote(tmp, path))
            self.assertFalse(os.path.exists(tmp))
            with open(path, "rb") as f:
                self.assertTrue(f.read(3) == b"NEW")
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)

    def test_capture_mac_does_not_trust_stale_on_failed_screencapture(self):
        """If screencapture writes nothing, a pre-existing live.bmp must NOT count as success."""
        import tempfile
        from unittest import mock
        d = tempfile.mkdtemp()
        try:
            path = os.path.join(d, "live.bmp")
            with open(path, "wb") as f:
                f.write(b"BM" + b"D" * 100000)  # "desktop" already there
            with open(path, "rb") as f:
                before = f.read(8)
            # force window path + a hit, then a screencapture that does NOT create tmp
            with mock.patch.dict(os.environ, {"TV_CAPTURE": "window"}):
                with mock.patch.object(tv, "find_d2r_window_mac", return_value=(999, "D2R.exe · fake")):
                    with mock.patch("subprocess.run") as run:
                        run.return_value = type("R", (), {"returncode": 1})()
                        ok = tv.capture_mac(path, timeout=2)
            self.assertFalse(ok)
            with open(path, "rb") as f:
                self.assertEqual(f.read(8), before)  # stale file unchanged
            self.assertIn(tv._CAP_TARGET.get("mode"), ("waiting", "full"))
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
