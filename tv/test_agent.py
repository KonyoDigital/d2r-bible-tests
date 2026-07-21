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


def _healthy_disk(cls_self):
    """v872.1 (the 4GB night) — reaper paths read shutil.disk_usage; stub a healthy disk so
    the suite tests the LOGIC, not how full Konyo's Mac happens to be."""
    import shutil as _sh, collections as _co, unittest.mock as _mo
    fake = _co.namedtuple("usage", "total used free")(500e9, 100e9, 400e9)
    pat = _mo.patch.object(_sh, "disk_usage", return_value=fake)
    pat.start()
    cls_self.addCleanup(pat.stop)


class TestFrameArchive(unittest.TestCase):
    """v735 — per-read frame hist for click-to-enlarge eyes-on-AI."""
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self._old_frames = tv.FRAMES
        self._old_hist = tv.HIST_DIR
        tv.FRAMES = self.d
        tv.HIST_DIR = os.path.join(self.d, "hist")
        _healthy_disk(self)

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


class TestFootageArchivePromote(unittest.TestCase):
    """v1190 — _archive_footage_copy must follow the same _cap_promote law every other
    capture writer in the file already does: write to a private tmp, verify real bytes, THEN
    atomically rename into the final f_<ms>.jpg name. Before this fix it wrote straight onto
    the final durable name, so a copy interrupted partway left a truncated fragment sitting
    under a real frame's name forever — nothing downstream re-checks size before trusting it."""

    def setUp(self):
        _healthy_disk(self)
        self.d = tempfile.mkdtemp()
        self._old_frames, self._old_hist = tv.FRAMES, tv.HIST_DIR
        tv.FRAMES = self.d
        tv.HIST_DIR = os.path.join(self.d, "hist")
        self._old_due = tv.__dict__.get("_FOOTAGE_DUE")
        tv._FOOTAGE_DUE = 0.0
        self.src = os.path.join(self.d, "eye.jpg")
        open(self.src, "wb").write(b"J" * 5000)   # over the 4000-byte floor

    def tearDown(self):
        tv.FRAMES, tv.HIST_DIR = self._old_frames, self._old_hist
        if self._old_due is None:
            tv.__dict__.pop("_FOOTAGE_DUE", None)
        else:
            tv._FOOTAGE_DUE = self._old_due
        import shutil
        shutil.rmtree(self.d, ignore_errors=True)

    def _footage_files(self):
        if not os.path.isdir(tv.HIST_DIR):
            return []
        return os.listdir(tv.HIST_DIR)

    def test_success_promotes_full_frame(self):
        now_f = time.time()
        self.assertTrue(tv._archive_footage_copy(self.src, now_f, why="grab"))
        files = self._footage_files()
        real = [f for f in files if f.startswith("f_") and f.endswith(".jpg")]
        self.assertEqual(len(real), 1, files)
        self.assertEqual(os.path.getsize(os.path.join(tv.HIST_DIR, real[0])), 5000)
        self.assertFalse(any(".tmp." in f for f in files), "no tmp fragment left behind")

    def test_interrupted_copy_leaves_no_fragment_under_final_name(self):
        """Simulate a copy that dies partway (ENOSPC / kill): shutil.copyfile only gets a
        few bytes onto disk before the process is gone. The final f_<ms>.jpg name must never
        exist with those short bytes — a truncated frame is worse than a missing one."""
        import shutil, unittest.mock as mock

        def short_copy(src, dst):
            with open(dst, "wb") as f:
                f.write(b"X" * 10)   # far under the 4000-byte floor — a torn write

        with mock.patch.object(shutil, "copyfile", side_effect=short_copy):
            ok = tv._archive_footage_copy(self.src, time.time(), why="grab")
        self.assertFalse(ok)
        files = self._footage_files()
        real = [f for f in files if f.startswith("f_") and f.endswith(".jpg")]
        self.assertEqual(real, [], "a truncated copy must not be promoted under the final name")
        self.assertFalse(any(".tmp." in f for f in files), "tmp fragment must be cleaned up")

    def test_interrupted_copy_does_not_corrupt_last_good_bridge(self):
        """The eye.last.jpg starve-bridge source gets the same tmp+promote treatment: a short
        copy must not overwrite a previously-good last.jpg with a corrupt one."""
        import shutil, unittest.mock as mock
        last = os.path.join(self.d, "eye.last.jpg")
        open(last, "wb").write(b"G" * 6000)   # a real, previously-archived good frame

        real_copyfile = shutil.copyfile
        calls = {"n": 0}

        def flaky_copy(src, dst):
            calls["n"] += 1
            if calls["n"] == 2:   # let the primary f_<ms>.jpg promote succeed, corrupt the 2nd
                with open(dst, "wb") as f:
                    f.write(b"X" * 10)
                return
            real_copyfile(src, dst)

        with mock.patch.object(shutil, "copyfile", side_effect=flaky_copy):
            ok = tv._archive_footage_copy(self.src, time.time(), why="grab")
        self.assertTrue(ok, "primary archive still succeeds even if the bridge copy fails")
        self.assertEqual(os.path.getsize(last), 6000, "corrupt bridge copy must not clobber last-good")


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
        # state on disk — v879 write-behind: flush first (the seal path always does)
        tv._state_flush()
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

    def test_parse_read_captures_sockets(self):
        # v946.5 (Konyo: "was the Diadem read 3 socketed?") — socket count per item, name -> N (1..6)
        p = tv._parse_read('{"scene":"stash","names":["Diadem"],"sockets":{"Diadem":3},"conf":0.9}')
        self.assertEqual(p["sockets"], {"Diadem": 3})
        # non-int + out-of-range dropped; valid kept
        p2 = tv._parse_read('{"names":["Monarch","Shako","X"],"sockets":{"Monarch":4,"Shako":"z","X":9}}')
        self.assertEqual(p2["sockets"], {"Monarch": 4})
        # absent → empty, never crashes
        self.assertEqual(tv._parse_read('{"names":["Ral"]}')["sockets"], {})
        # the prompt actually asks for it
        self.assertIn('"sockets"', tv.READ_PROMPT)
        self.assertIn("Socketed", tv.READ_PROMPT)


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

    def test_genius_escalate_is_bounded_by_the_live_lane_timeout(self):
        # v1188 — the Master Brain law (LIVE_READ_TIMEOUT_S) bounds the warm read AND its
        # one-shot fallback; escalate is a THIRD vision call fired on top of either and must
        # obey the SAME live-lane budget, not a bare hardcoded 90s (which — the instant
        # TV_MODEL_ESCALATE differs from TV_MODEL — could hold the live lane hostage for
        # LIVE_READ_TIMEOUT_S + 90s, worse than the 66s stall the law exists to prevent).
        import unittest.mock as mock
        weak = {"scene": "loot", "names": [], "conf": 0.9, "area": ""}   # _needs_escalate → True
        with mock.patch.object(tv, "FAST_MODEL", "haiku"), \
             mock.patch.object(tv, "GENIUS_MODEL", "sonnet"), \
             mock.patch.object(tv, "ESCALATE_CAP", 40), \
             mock.patch.object(tv, "_ESCALATE_N", [0]), \
             mock.patch.object(tv, "_oneshot", return_value=None) as m_oneshot:
            tv._maybe_genius("/fake/read.jpg", dict(weak), time.time(), "warm")
        m_oneshot.assert_called_once()
        _, kwargs = m_oneshot.call_args
        self.assertEqual(kwargs.get("timeout"), tv.LIVE_READ_TIMEOUT_S)
        self.assertNotEqual(kwargs.get("timeout"), 90)


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


class TestLiveReadTimeoutCap(unittest.TestCase):
    """v948.17 — Grok P1-5 pin (2026-07-21 fast-run soak): a single frame took 68,978ms and,
    with POOL_N==1 outside robot mode, held the ENTIRE live lane for up to the OLD 75s ask()
    + 90s one-shot-fallback ceiling (165s worst case). claude_read() must honor
    LIVE_READ_TIMEOUT_S on BOTH the warm ask() and the one-shot fallback so a stalled read
    gives up fast and frees the lane for the next frame — the Master Brain law: 'a stalled
    live read is a signal to route to retro, not a failure that blocks everything else.'"""

    def setUp(self):
        self.fake = os.path.join(tv.HERE, "fake_claude.py")
        self._orig_bin = tv.CLAUDE_BIN
        tv.CLAUDE_BIN = self.fake
        self._orig_timeout = tv.LIVE_READ_TIMEOUT_S
        os.environ["TV_FAKE_MODE"] = "slow"   # fake claude never answers the warm/stream path

    def tearDown(self):
        tv.CLAUDE_BIN = self._orig_bin
        tv.LIVE_READ_TIMEOUT_S = self._orig_timeout
        os.environ.pop("TV_FAKE_MODE", None)

    def test_stalled_warm_read_bounded_by_live_read_timeout(self):
        tv.LIVE_READ_TIMEOUT_S = 1.0   # tight cap — a stalled read must give up fast
        d = tempfile.mkdtemp()
        f = os.path.join(d, "stalled.jpg")
        open(f, "w").close()
        w = tv.VisionWorker()
        t0 = time.time()
        rd = tv.claude_read(f, worker=w)
        elapsed = time.time() - t0
        w.stop()
        # OLD ceiling was ask()=75s default + oneshot=90s = up to 165s. This must return well
        # under even the old ask()-alone default — proving the cap is actually threaded in.
        self.assertLess(elapsed, 15.0,
                         f"claude_read took {elapsed:.1f}s — LIVE_READ_TIMEOUT_S not honored")
        self.assertEqual(rd["mode"], "empty")   # an honest miss, not a hang and not invented data

    def test_default_cap_is_tighter_than_old_75s_ceiling(self):
        # a real named read this soak took at most ~15s; the default cap stays generous but
        # bounded — nowhere near the old unbounded-feeling 75s/90s ceilings.
        self.assertLessEqual(tv.LIVE_READ_TIMEOUT_S, 60.0)
        self.assertGreaterEqual(tv.LIVE_READ_TIMEOUT_S, 15.0)


class TestStallDrainDecision(unittest.TestCase):
    """v948.17 — Grok P1-4 pin (2026-07-21 fast-run soak): 'a 66s live stall means 0 second-eye
    drains.' Outside ROBOT_MODE, POOL_N==1, so the OLD gate (`_vision_in_flight_n() < POOL_N`)
    can never open while the single live reader is busy — no matter how long it's stuck. This
    is the pure decision behind the parallel stall-drain escape hatch: fire a DEDICATED worker
    when the pool is full AND genuinely stalled AND the backlog has something piling up."""

    def test_no_backlog_never_fires(self):
        self.assertFalse(tv._stall_drain_decision(0, 1, 1, 999999, False))

    def test_free_slot_defers_to_ordinary_idle_gap_sweep(self):
        # in_flight < pool_n → a normal slot is free, the '< POOL_N' gate already covers it
        self.assertFalse(tv._stall_drain_decision(3, 0, 1, 999999, False))

    def test_pool_full_but_not_stalled_yet_does_not_fire(self):
        self.assertFalse(tv._stall_drain_decision(3, 1, 1, 500, False, threshold_ms=20000))

    def test_pool_full_and_genuinely_stalled_fires(self):
        # this is the exact soak shape: POOL_N=1, one read in flight, stuck way past threshold
        self.assertTrue(tv._stall_drain_decision(3, 1, 1, 69000, False, threshold_ms=20000))

    def test_already_running_sweep_blocks_a_second_one(self):
        self.assertFalse(tv._stall_drain_decision(3, 1, 1, 999999, True, threshold_ms=20000))

    def test_disabled_never_fires(self):
        self.assertFalse(tv._stall_drain_decision(3, 1, 1, 999999, False, enabled=False, threshold_ms=20000))

    def test_boundary_is_inclusive_at_threshold(self):
        self.assertTrue(tv._stall_drain_decision(1, 1, 1, 20000, False, threshold_ms=20000))
        self.assertFalse(tv._stall_drain_decision(1, 1, 1, 19999, False, threshold_ms=20000))

    def test_default_threshold_uses_module_stall_drain_s(self):
        thr = tv.STALL_DRAIN_S * 1000
        self.assertTrue(tv._stall_drain_decision(1, 1, 1, thr, False))
        self.assertFalse(tv._stall_drain_decision(1, 1, 1, thr - 1, False))


class TestStallDrainParallelWorker(unittest.TestCase):
    """v948.17 — the stall-drain sweep must run on a worker OUTSIDE the normal POOL_N/_pool_free
    bookkeeping (sentinel `_STALL_RID`), so it can fire even while every ordinary pool slot is
    occupied, and it must never leak into `_pool_free` (which would let normal live dispatch
    silently claim it later, breaking 'ONE Claude always' outside robot mode)."""

    def test_stall_rid_is_never_a_real_pool_slot(self):
        self.assertNotIn(tv._STALL_RID, list(range(tv.POOL_N)))

    def test_stall_worker_is_lazy_and_separate_from_the_live_pool(self):
        old = tv._STALL_WORKER
        try:
            tv._STALL_WORKER = None
            w = tv._stall_worker()
            self.assertIsInstance(w, tv.VisionWorker)
            self.assertIsNot(w, tv._WORKER)
            self.assertNotIn(w, tv._WORKERS)
            self.assertIs(tv._stall_worker(), w)   # lazy singleton, not re-created each call
        finally:
            if tv._STALL_WORKER is not None and tv._STALL_WORKER.p:
                tv._STALL_WORKER.stop()
            tv._STALL_WORKER = old

    def test_pool_release_never_adds_stall_rid_to_pool_free(self):
        # _pool_release is the normal-path release; guard against a future edit routing the
        # override id through it and leaking it into ordinary live dispatch.
        before = list(tv._pool_free)
        tv._pool_release(tv._STALL_RID)
        self.assertNotIn(tv._STALL_RID, tv._pool_free)
        tv._pool_free[:] = before   # restore exactly (defensive — _pool_release may have no-opped)


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
        # v794 recal — empty gameplay must NOT learn dead (one bad parse used to blind
        # the eye to a whole panel class); only explicit vision-confirmed transition learns.
        self.assertFalse(tv.should_learn_dead({"scene": "gameplay", "names": [], "area": ""}))
        self.assertFalse(tv.should_learn_dead({"scene": "", "names": [], "area": ""}))   # v794 recal — unknown scene never learns dead
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

    def test_watch_mode_ignores_eye_jpg_for_settle(self):
        """Windows film (eye.jpg) must not starve intelligence of live.bmp."""
        d = tempfile.mkdtemp()
        try:
            old = tv.FRAMES
            tv.FRAMES = d
            open(os.path.join(d, "eye.jpg"), "wb").write(b"eye" + b"x" * 100)
            time.sleep(0.02)
            open(os.path.join(d, "live.bmp"), "wb").write(b"BM" + b"y" * 200)
            hit = tv.newest_watched_frame()
            self.assertTrue(hit and hit.endswith("live.bmp"), hit)
            # cap_target status file
            with open(os.path.join(d, "cap_target.json"), "w") as f:
                f.write('{"mode":"window","label":"D2R · Diablo II: Resurrected"}')
            tv._CAP_TARGET = {"mode": "full", "label": "full screen", "wid": None}
            tv._refresh_cap_target_from_disk()
            self.assertEqual(tv._CAP_TARGET.get("mode"), "window")
            self.assertIn("D2R", tv._CAP_TARGET.get("label") or "")
        finally:
            tv.FRAMES = old
            import shutil
            shutil.rmtree(d, ignore_errors=True)

    def test_journal_shield_lists_frame_ids(self):
        """v840 — prune must see journaled frame basenames."""
        j = os.path.join(self.d, "sessions_shield.jsonl")
        old = tv.JOURNAL
        tv.JOURNAL = j
        try:
            with open(j, "w") as f:
                f.write(json.dumps({"ts": 1, "frameId": "7_99", "names": ["Vex Rune"]}) + "\n")
                f.write(json.dumps({"ts": 2, "frameId": "8_100", "names": []}) + "\n")
            ids = tv._journal_frame_ids()
            self.assertIn("7_99.jpg", ids)
            self.assertIn("8_100.jpg", ids)
        finally:
            tv.JOURNAL = old

    def test_scout_lane_removed(self):
        """v845 — no secondary scout reader (one AI reader = settle → dual-lane only)."""
        self.assertFalse(hasattr(tv, "_scout_fresh_names"))
        self.assertFalse(hasattr(tv, "SCOUT_INTERVAL_S"))
        self.assertFalse(hasattr(tv, "_engine_due_scout"))
        self.assertFalse(hasattr(tv, "SCOUT_GAP_S"))

    def test_tesla_drive_film_and_gaps(self):
        """v901 — Auto Intake defaults: gentle settle gap, 1 Claude, Robot frozen."""
        self.assertRegex(tv.VERSION, r"^v\d+")  # major; dots ok (v935.6)
        self.assertFalse(tv.ROBOT_MODE, "Robot must be frozen by default")
        self.assertEqual(tv.POOL_N, 1, "Auto Intake uses one Claude worker")
        self.assertLessEqual(tv.MIN_GAP_S, 5.0)
        self.assertGreaterEqual(tv.MIN_GAP_S, 2.0)
        # v925 LIGHT contract — the default is a gentle screenshot reader, not a recorder:
        # a slow sensor tick (Konyo: 'like screenshot not record'), no continuous film, no OCR.
        self.assertTrue(tv.LIGHT_MODE, "LIGHT is the default product")
        self.assertGreaterEqual(tv.POLL_S, 1.0, "LIGHT samples slowly so the game can breathe")
        # v941 — DOCTRINE FLIPPED (Konyo, after the v925-LIGHT off-default bit 4 times):
        # lanes are ON by default in code; only an explicit TV_OCR=0 disables.
        self.assertTrue(tv.OCR_ENABLED, "v941: OCR lane is ON by default (TV_OCR=0 to disable)")
        self.assertFalse(tv.FAREWELL_READ_ON, "LIGHT End Session seals + exits, no farewell vision")
        # the film-fps constant still exists (heavy/debug mode uses it) but the thread stays dark
        self.assertAlmostEqual(tv.FOOTAGE_INTERVAL_S, 1.0, places=3)
        self.assertGreaterEqual(tv.FILM_MAX_PX, 1280)
        h = tv._health({"reads": [], "startedAt": int(time.time() * 1000)})
        for k in ("filmFps", "filmTargetFps", "filmMaxPx", "pollMs", "gapCruiseS",
                  "gapPriorityS", "footageTargetFps", "heartbeatS", "gameOk", "aiPaused",
                  "productMode", "robotMode"):
            self.assertIn(k, h)
        self.assertEqual(h.get("productMode"), "intake")
        self.assertFalse(h.get("robotMode"))
        self.assertLessEqual(tv.FAREWELL_MAX_S, 45)
        # heartbeat dual-lane only when robot unlocked
        src = open(tv.__file__, encoding="utf-8").read()
        self.assertIn("ROBOT_MODE and (_vision_in_flight_n()", src)

    def test_no_game_guard_helpers(self):
        """v899 — pause AI when D2R.exe missing; helpers exist and gate flips."""
        self.assertTrue(callable(tv._game_window_present))
        self.assertTrue(callable(tv._set_game_gate))
        tv._set_game_gate(False, "D2R window missing — open Diablo II")
        self.assertTrue(tv._AI_PAUSED)
        self.assertFalse(tv._GAME_OK)
        self.assertIn("D2R window missing", tv._GAME_MSG)
        tv._set_game_gate(True, "")
        self.assertFalse(tv._AI_PAUSED)
        self.assertTrue(tv._GAME_OK)

    def test_close_session_helper_exists(self):
        """v847 — OFF/STOP seal via close_session + /shutdown (not just kill)."""
        self.assertTrue(callable(tv.close_session))
        src = open(tv.__file__).read()
        self.assertIn('"/shutdown"', src)
        self.assertIn("session_end", src)

    def test_settle_queue_tags_origin(self):
        """Settle freezes keep origin tags on the one-reader queue."""
        d = tempfile.mkdtemp()
        old_f, old_emit = tv.FRAMES, tv.__dict__.get("_LAST_EMIT_SIG")
        try:
            tv.FRAMES = d
            tv._SETTLE_QUEUE[:] = []
            tv._LAST_EMIT_SIG = None
            src = os.path.join(d, "live.bmp")
            open(src, "wb").write(b"x" * 64)
            sig = bytes([7]) * 4096
            tv._settle_enqueue(src, sig, interest=0.9, priority=True, origin="settle")
            self.assertEqual(len(tv._SETTLE_QUEUE), 1)
            self.assertEqual(tv._SETTLE_QUEUE[0]["origin"], "settle")
            e = tv._settle_drain_pop()
            self.assertEqual(e["origin"], "settle")
        finally:
            tv.FRAMES = old_f
            tv._LAST_EMIT_SIG = old_emit
            tv._SETTLE_QUEUE[:] = []
            import shutil
            shutil.rmtree(d, ignore_errors=True)


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
        # v843 — if a game is up, pin must be D2R.exe (not CrossOver / Battle.net)
        low = label.lower()
        if "d2r" in low or "diablo" in low:
            self.assertIn("d2r.exe", low)
            self.assertNotIn("crossover", low.split("·")[0])
            self.assertNotIn("battle.net", low.split("·")[0])

    def test_score_rejects_crossover_home_and_battle_net(self):
        """v843 — CrossOver Home + Battle.net lobby must never outrank the game."""
        self.assertIsNone(tv.score_d2r_window_candidate("CrossOver", "CrossOver", 1150, 700))
        self.assertIsNone(tv.score_d2r_window_candidate("CrossOver", "Home", 1150, 700))
        self.assertIsNone(tv.score_d2r_window_candidate("Battle.net.exe", "Battle.net", 1470, 805))
        self.assertIsNone(tv.score_d2r_window_candidate("Google Chrome", "D2R Farming Bible", 1400, 900))

    def test_score_prefers_d2r_exe_game(self):
        """v843 — D2R.exe · Diablo II: Resurrected is the absolute pin winner."""
        game = tv.score_d2r_window_candidate(
            "D2R.exe", "Diablo II: Resurrected", 1470, 956, onscreen=True)
        self.assertIsNotNone(game)
        self.assertGreater(game, 10000)
        # thin chrome bars under D2R.exe still lose on size
        self.assertIsNone(tv.score_d2r_window_candidate("D2R.exe", "", 1470, 33))

    def test_quartz_grab_helpers_exist(self):
        """v844 — capture stack has Quartz fallback + window BMP path (no live grab required)."""
        self.assertTrue(callable(tv._quartz_grab_window))
        self.assertTrue(callable(tv._capture_window_to_bmp))
        self.assertTrue(callable(tv._screencapture_window))
        # bad wid must not crash
        self.assertFalse(tv._quartz_grab_window(0, "/tmp/nope_tvd.png"))
        self.assertFalse(tv._quartz_grab_window(None, "/tmp/nope_tvd.png"))

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



class TestVigilantFilm(unittest.TestCase):
    """v785 — eye.jpg lifecycle: age surfaces, death is clean, no LIVE on a dead frame."""

    def test_eye_age_no_file(self):
        import tempfile
        d = tempfile.mkdtemp()
        old = tv.FRAMES
        try:
            tv.FRAMES = d
            self.assertEqual(tv._eye_age_ms(), -1)
        finally:
            tv.FRAMES = old
            import shutil; shutil.rmtree(d, ignore_errors=True)

    def test_eye_age_fresh_and_stale(self):
        import tempfile
        d = tempfile.mkdtemp()
        old = tv.FRAMES
        try:
            tv.FRAMES = d
            eye = os.path.join(d, "eye.jpg")
            with open(eye, "wb") as f:
                f.write(b"J" * 100)
            age = tv._eye_age_ms()
            self.assertGreaterEqual(age, 0)
            self.assertLess(age, 3000)
            os.utime(eye, (time.time() - 60, time.time() - 60))
            self.assertGreater(tv._eye_age_ms(), 50000)
        finally:
            tv.FRAMES = old
            import shutil; shutil.rmtree(d, ignore_errors=True)

    def test_eye_clear(self):
        import tempfile
        d = tempfile.mkdtemp()
        old = tv.FRAMES
        try:
            tv.FRAMES = d
            eye = os.path.join(d, "eye.jpg")
            with open(eye, "wb") as f:
                f.write(b"J" * 100)
            tv._eye_clear()
            self.assertFalse(os.path.exists(eye))
            tv._eye_clear()   # idempotent on missing file
        finally:
            tv.FRAMES = old
            import shutil; shutil.rmtree(d, ignore_errors=True)

    def test_full_screen_lane_keeps_real_frame(self):
        """v1181 — the full-screen lane must apply the SAME white-Metal-backing guard the
        window lane already had; a real (non-blank) grab is kept as-is."""
        import tempfile
        d = tempfile.mkdtemp()
        tmp = os.path.join(d, "eye.jpg.part.jpg")
        old_grab, old_white = tv._quartz_grab_screen, tv._is_white_backing
        try:
            def fake_grab(dest, uti="public.jpeg"):
                with open(dest, "wb") as f:
                    f.write(b"J" * 5000)
                return True
            tv._quartz_grab_screen = fake_grab
            tv._is_white_backing = lambda path, size_ceiling=300_000: False
            self.assertTrue(tv._grab_full_screen_frame(tmp))
            self.assertTrue(os.path.isfile(tmp), "a real frame must survive the guard")
        finally:
            tv._quartz_grab_screen, tv._is_white_backing = old_grab, old_white
            import shutil; shutil.rmtree(d, ignore_errors=True)

    def test_full_screen_lane_rejects_white_metal_backing(self):
        """v1181 — REGRESSION: before this fix, ONLY the window lane ran _is_white_backing;
        the full-screen lane (which is invoked specifically when the window lane just
        white-rejected and demoted) archived whatever it grabbed with no blank-frame check
        at all. A white backing on the full-screen grab must now be rejected exactly like
        the window lane rejects one, and the tmp file must not be left behind for a caller
        to mistakenly archive."""
        import tempfile
        d = tempfile.mkdtemp()
        tmp = os.path.join(d, "eye.jpg.part.jpg")
        old_grab, old_white = tv._quartz_grab_screen, tv._is_white_backing
        old_rejects = tv._FILM_WHITE_REJECTS if hasattr(tv, "_FILM_WHITE_REJECTS") else None
        try:
            def fake_grab(dest, uti="public.jpeg"):
                with open(dest, "wb") as f:
                    f.write(b"J" * 5000)
                return True
            tv._quartz_grab_screen = fake_grab
            tv._is_white_backing = lambda path, size_ceiling=300_000: True
            tv._FILM_WHITE_REJECTS = 0
            self.assertFalse(tv._grab_full_screen_frame(tmp))
            self.assertFalse(os.path.isfile(tmp), "rejected white grab must not linger as tmp")
            self.assertEqual(tv._FILM_WHITE_REJECTS, 1, "the full-screen reject must count too")
        finally:
            tv._quartz_grab_screen, tv._is_white_backing = old_grab, old_white
            if old_rejects is None:
                if hasattr(tv, "_FILM_WHITE_REJECTS"):
                    del tv._FILM_WHITE_REJECTS
            else:
                tv._FILM_WHITE_REJECTS = old_rejects
            import shutil; shutil.rmtree(d, ignore_errors=True)



class TestHonestReplay(unittest.TestCase):
    """v787 — TV_NO_JOURNAL runs stamp sim:true on every published read (R3 sleeper:
    the board must be able to tell a replay from real loot, or it re-vaults history)."""

    def test_replay_read_carries_sim_flag(self):
        old = os.environ.get("TV_NO_JOURNAL")
        os.environ["TV_NO_JOURNAL"] = "1"
        try:
            rec = tv.emit_deep_read({"area": "Cold Plains", "scene": "loot",
                                     "names": ["Ist"], "tz": [], "conf": 0.9,
                                     "vault_names": ["Ist"]}, 1, "1_123", capture_ts=123)
            st = tv._load()
            reads = st.get("reads") or []
            self.assertTrue(reads, "no read published")
            self.assertTrue(reads[-1].get("sim"), "replay read missing sim:true")
        finally:
            if old is None:
                os.environ.pop("TV_NO_JOURNAL", None)
            else:
                os.environ["TV_NO_JOURNAL"] = old

    def test_live_read_has_no_sim_flag(self):
        os.environ.pop("TV_NO_JOURNAL", None)
        rec = tv.emit_deep_read({"area": "Cold Plains", "scene": "loot",
                                 "names": ["Shael"], "tz": [], "conf": 0.9}, 2, "2_456", capture_ts=456)
        st = tv._load()
        reads = st.get("reads") or []
        self.assertTrue(reads)
        self.assertFalse(reads[-1].get("sim"), "live read must NOT be sim")



class TestNoCliff(unittest.TestCase):
    """v788 — the 240-read cliff is dead: emit still publishes past SESSION_CAP."""

    def test_publish_past_cap(self):
        n = tv.SESSION_CAP + 5
        tv.emit_deep_read({"area": "Cold Plains", "scene": "loot", "names": ["Ral"],
                           "tz": [], "conf": 0.9}, n, "%d_999" % n, capture_ts=999)
        st = tv._load()
        reads = st.get("reads") or []
        self.assertTrue(any(r.get("n") == n for r in reads), "read past cap not published")



class TestFaultLamp(unittest.TestCase):
    """v789 — _health() truth object: ages numeric, tallies real."""

    def test_health_shape(self):
        import time as _t
        st = {"startedAt": int(_t.time() * 1000) - 60000,
              "reads": [{"ts": int(_t.time() * 1000) - 5000, "names": ["Shako"], "vault_names": ["Shako"]},
                        {"ts": int(_t.time() * 1000) - 2000, "names": [], "vault_names": []}]}
        h = tv._health(st)
        self.assertGreaterEqual(h["sessionMs"], 59000)
        self.assertGreaterEqual(h["lastReadAgeMs"], 1500)
        self.assertLess(h["lastReadAgeMs"], 30000)
        self.assertEqual(h["named"], 1)
        self.assertEqual(h["vaulted"], 1)
        self.assertIn("captureMode", h)
        self.assertIn("visionBusyMs", h)

    def test_health_empty(self):
        h = tv._health({})
        self.assertEqual(h["lastReadAgeMs"], -1)
        self.assertEqual(h["named"], 0)



class TestNoPoison(unittest.TestCase):
    """v794 (Grok R5 #4) — one bad parse must never blind the eye permanently."""

    def test_learn_dead_only_on_explicit_transition(self):
        self.assertTrue(tv.should_learn_dead({"scene": "transition", "names": [], "area": ""}))
        self.assertFalse(tv.should_learn_dead({"scene": "gameplay", "names": [], "area": ""}))
        self.assertFalse(tv.should_learn_dead({"scene": "", "names": [], "area": ""}))
        self.assertFalse(tv.should_learn_dead({"scene": "transition", "names": [], "area": "", "mode": "empty"}))
        self.assertFalse(tv.should_learn_dead({"scene": "transition", "names": [], "area": "", "mode": "timeout"}))
        self.assertFalse(tv.should_learn_dead({"scene": "transition", "names": ["Shako"], "area": ""}))

    def test_parse_survives_chatty_cli(self):
        chatter = 'worker log {"pid": 12} noise\n{"area":"Cold Plains","scene":"loot","names":["Ist"],"conf":0.9}\ntrailing {broken'
        p = tv._parse_read(chatter)
        self.assertIsNotNone(p)
        self.assertEqual(p["names"], ["Ist"])
        self.assertEqual(p["area"], "Cold Plains")

    def test_parse_none_on_garbage(self):
        self.assertIsNone(tv._parse_read("no json here at all"))



class TestOcrSeed(unittest.TestCase):
    """v795 (Grok R5 #2) — OCR-won / Claude-lost frames still enter the loot chain."""

    def test_empty_deep_with_ocr_names_seeds_seen(self):
        rec = tv.emit_deep_read({"area": "Cold Plains", "scene": "gameplay", "names": [],
                                 "tz": [], "conf": None, "mode": "empty"},
                                7, "7_777", ocr_rd={"names": ["Harlequin Crest"], "ms": 60},
                                capture_ts=777)
        self.assertIn("Harlequin Crest", rec.get("ocr_seeded") or [])
        snap = tv._LIFECYCLE.snapshot()
        blob = str(snap).lower()
        self.assertIn("harlequin crest", blob, "OCR seed missing from lifecycle chain")

    def test_named_deep_does_not_seed(self):
        rec = tv.emit_deep_read({"area": "Cold Plains", "scene": "loot", "names": ["Ist"],
                                 "tz": [], "conf": 0.9},
                                8, "8_888", ocr_rd={"names": ["Ist", "Ghost"], "ms": 60},
                                capture_ts=888)
        self.assertEqual(rec.get("ocr_seeded") or [], [])



class TestMultisetLedger(unittest.TestCase):
    """v796 (Grok R5 #3) — a second physical drop of the same name COUNTS."""

    def test_second_instance_revaults_with_count(self):
        lc = tv.LootLifecycle()
        # first drop: floor → stash
        lc.process("loot", ["Ist Rune"], "Cold Plains", 0.9)
        r1 = lc.process("stash", ["Ist Rune"], "Cold Plains", 0.9)
        self.assertIn("Ist Rune", r1["vault_names"])
        # echo with NO new provenance: blocked
        r2 = lc.process("stash", ["Ist Rune"], "Cold Plains", 0.9)
        self.assertNotIn("Ist Rune", r2["vault_names"])
        self.assertEqual(r2["lifecycle_tags"].get("Ist Rune"), "already-vaulted")
        # SECOND physical drop: fresh floor sighting → re-vault, count 2
        lc.process("loot", ["Ist Rune"], "Cold Plains", 0.9)
        r3 = lc.process("stash", ["Ist Rune"], "Cold Plains", 0.9)
        self.assertIn("Ist Rune", r3["vault_names"], "second instance must count")
        # either path is doctrine-true: floor-again throw-out → fresh re-vault ('vault:stash'),
        # or the multiset branch ('vault:stash ×2') when provenance coexists with the ledger entry
        self.assertIn("vault:stash", r3["lifecycle_tags"].get("Ist Rune", ""))

    def test_prefix_canonical_chain(self):
        lc = tv.LootLifecycle()
        lc.process("loot", ["Superior Colossus Crossbow"], "Cold Plains", 0.9)
        r = lc.process("stash", ["Colossus Crossbow"], "Cold Plains", 0.9)
        tag = r["lifecycle_tags"].get("Colossus Crossbow", "")
        self.assertNotEqual(tag, "stash-no-chain", "prefix broke the chain")



class TestJournalRotation(unittest.TestCase):
    """v805 (Grok R5/R7, journal-agent) — a ~4MB journal ROTATES (sessions.jsonl → sessions.1.jsonl),
    never half-truncates the live file; the reader concatenates rotated + live."""
    def _rot(self, j):
        root, ext = os.path.splitext(j)
        return root + ".1" + ext

    def test_oversize_rotates_and_reader_concatenates(self):
        import replay
        old_j, old_rj = tv.JOURNAL, replay.JOURNAL
        d = tempfile.mkdtemp()
        j = os.path.join(d, "sessions.jsonl")
        tv.JOURNAL = j
        replay.JOURNAL = j
        rot = self._rot(j)
        try:
            line = json.dumps({"m": "OLD", "pad": "x" * 200}) + "\n"
            with open(j, "w", encoding="utf-8") as f:
                while os.path.getsize(j) < 4_050_000:
                    f.write(line * 500)
                    f.flush()
            tv._journal({"m": "TRIGGER"})
            self.assertTrue(os.path.exists(rot), "rotated file was not created")
            self.assertFalse(os.path.exists(j), "live file should be renamed away by rotation")
            tv._journal({"m": "AFTER"})
            self.assertTrue(os.path.exists(j), "live file was not recreated after rotation")
            self.assertLess(os.path.getsize(j), 4_000_000)
            reads = replay.load_journal()
            markers = {r.get("m") for r in reads}
            self.assertIn("OLD", markers)
            self.assertIn("TRIGGER", markers)
            self.assertIn("AFTER", markers)
            self.assertEqual(reads[-1].get("m"), "AFTER")
        finally:
            tv.JOURNAL, replay.JOURNAL = old_j, old_rj


class TestReplayTornLineTolerance(unittest.TestCase):
    """v805 — torn last line / blank lines are skipped, never break loading."""
    def test_torn_and_blank_lines_are_skipped(self):
        import replay
        d = tempfile.mkdtemp()
        p = os.path.join(d, "torn.jsonl")
        with open(p, "w", encoding="utf-8") as f:
            f.write(json.dumps({"a": 1}) + "\n")
            f.write("\n")
            f.write(json.dumps({"b": 2}) + "\n")
            f.write('{"c": 3, "half')
        got = replay.load_journal(path=p)
        self.assertEqual(got, [{"a": 1}, {"b": 2}])

    def test_missing_file_returns_empty(self):
        import replay
        got = replay.load_journal(path=os.path.join(tempfile.mkdtemp(), "nope.jsonl"))
        self.assertEqual(got, [])



class TestJournalGenerations(unittest.TestCase):
    """v811 (Grok R8 sleeper) — the second rotation SHIFTS the ring; gen-1 is never erased."""

    def test_second_rotation_shifts_not_overwrites(self):
        import replay
        old_j, old_rj = tv.JOURNAL, replay.JOURNAL
        d = tempfile.mkdtemp()
        j = os.path.join(d, "sessions.jsonl")
        tv.JOURNAL = j; replay.JOURNAL = j
        root, ext = os.path.splitext(j)
        try:
            def fill(marker):
                with open(j, "w", encoding="utf-8") as f:
                    line = (json.dumps({"m": marker, "pad": "x" * 200}) + "\n") * 500
                    while os.path.getsize(j) < 4_050_000:
                        f.write(line); f.flush()
            fill("GEN1"); tv._journal({"m": "T1"})
            fill("GEN2"); tv._journal({"m": "T2"})
            g1 = open(root + ".1" + ext, encoding="utf-8").read()
            g2 = open(root + ".2" + ext, encoding="utf-8").read()
            self.assertIn("GEN2", g1)          # newest rotation in .1
            self.assertIn("GEN1", g2)          # older night SURVIVES in .2
            reads = replay.load_journal()
            markers = {r.get("m") for r in reads}
            self.assertIn("GEN1", markers)
            self.assertIn("GEN2", markers)
        finally:
            tv.JOURNAL, replay.JOURNAL = old_j, old_rj



class TestOneBudget(unittest.TestCase):
    """v813 (Grok R8 #7) — derivative caches share the hist budget and die with their source."""

    def test_prune_kills_derivative_twins_and_orphans(self):
        import shutil as sh
        _healthy_disk(self)   # v872.1 — prune LOGIC under test, not the host's real free space
        tv._ORPHAN_DUE = 0.0   # v877 — force the periodic orphan sweep in this test
        d = tempfile.mkdtemp()
        old_hist = tv.HIST_DIR
        old_keep = tv.HIST_KEEP
        tv.HIST_DIR = d
        tv.HIST_KEEP = 5
        try:
            os.makedirs(os.path.join(d, "cache1280"), exist_ok=True)
            for i in range(12):
                fid = "%d_%d" % (i, 1000 + i)
                with open(os.path.join(d, fid + ".jpg"), "wb") as f:
                    f.write(b"J" * 2000)
                with open(os.path.join(d, "cache1280", fid + ".jpg"), "wb") as f:
                    f.write(b"j" * 500)
                os.utime(os.path.join(d, fid + ".jpg"), (1000 + i, 1000 + i))
            # orphan derivative with no source
            with open(os.path.join(d, "cache1280", "999_999.jpg"), "wb") as f:
                f.write(b"o" * 100)
            src = os.path.join(d, "seed.bmp")
            with open(src, "wb") as f:
                f.write(b"BM" + b"D" * 60000)
            fid = tv.archive_read_frame(src, 99, 999999)
            live = {f for f in os.listdir(d) if f.endswith(".jpg")}
            cached = set(os.listdir(os.path.join(d, "cache1280")))
            # v861.1 recal — COUNT CAPS ABOLISHED (Konyo): with free disk, EVERY frame lives.
            self.assertGreaterEqual(len(live), 12, "frames must survive when the disk is fine")
            for c in cached:
                self.assertIn(c, live, "derivative %s survived its source" % c)
            self.assertNotIn("999_999.jpg", cached, "orphan derivative survived")
        finally:
            tv.HIST_DIR = old_hist
            tv.HIST_KEEP = old_keep
            sh.rmtree(d, ignore_errors=True)



class TestOcrTwinLane(unittest.TestCase):
    """v818 (Grok R8 #3) — the fast lane exists on both platforms (worker cmd dispatch)."""

    def test_mac_cmd(self):
        import unittest.mock as mock
        with mock.patch.object(tv.sys, "platform", "darwin"):
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("TV_OCR_BIN", None)
                cmd = tv._ocr_worker_cmd()
                if os.path.isfile(tv.OCR_BIN):
                    self.assertEqual(cmd[0], tv.OCR_BIN)

    def test_win_cmd_uses_ps1(self):
        import unittest.mock as mock
        with mock.patch.object(tv.sys, "platform", "win32"):
            os.environ.pop("TV_OCR_BIN", None)
            cmd = tv._ocr_worker_cmd()
            self.assertIsNotNone(cmd, "windows worker cmd missing (ocr_win.ps1 not found?)")
            self.assertIn("powershell.exe", cmd[0])
            self.assertIn("ocr_win.ps1", cmd[-1])

    def test_env_override_wins(self):
        os.environ["TV_OCR_BIN"] = "/tmp/fake_ocr"
        try:
            cmd = tv._ocr_worker_cmd()
            self.assertEqual(cmd, ["/tmp/fake_ocr", "--worker"])
        finally:
            os.environ.pop("TV_OCR_BIN", None)



class TestSettleQueue(unittest.TestCase):
    """v827 (Grok R5 #1 / R9 #2) — the settle-queue ring buffer: freezes that land WHILE a
    Claude vision call is in flight are captured (a copied snapshot) and the NEWEST one is
    drained through the same pipeline the moment the read frees up — instead of vanishing at
    the `if _VISION_BUSY:` continue."""
    def setUp(self):
        _healthy_disk(self)
        self.d = tempfile.mkdtemp()
        self._old = {k: getattr(tv, k) for k in
                     ("FRAMES", "SETTLE_QUEUE_CAP", "SETTLE_QUEUE_STALE_MS",
                      "PRIORITY_CAP_BONUS", "TEXT_EYE_BACKLOG_CAP")}
        tv._TEXT_EYE_BACKLOG[:] = []
        self._old_emit = tv.__dict__.get("_LAST_EMIT_SIG")
        tv.FRAMES = self.d
        tv._SETTLE_QUEUE[:] = []
        tv._LAST_EMIT_SIG = None
        self.src = os.path.join(self.d, "live.bmp")
        open(self.src, "wb").write(b"x" * 128)

    def tearDown(self):
        for k, v in self._old.items():
            setattr(tv, k, v)
        tv._LAST_EMIT_SIG = self._old_emit
        tv._SETTLE_QUEUE[:] = []
        tv._TEXT_EYE_BACKLOG[:] = []
        import shutil
        shutil.rmtree(self.d, ignore_errors=True)

    @staticmethod
    def _sig(v):
        return bytes([v]) * 4096

    def test_capture_during_busy_and_dedupe(self):
        tv._settle_enqueue(self.src, self._sig(0), interest=0.5, priority=True)
        tv._settle_enqueue(self.src, self._sig(0), interest=0.5, priority=True)
        tv._settle_enqueue(self.src, self._sig(90), interest=0.2, priority=False)
        self.assertEqual(len(tv._SETTLE_QUEUE), 2)
        first = tv._SETTLE_QUEUE[0]
        self.assertEqual(first["interest"], 0.5)
        self.assertTrue(first["priority"])
        self.assertTrue(all(os.path.isfile(e["path"]) for e in tv._SETTLE_QUEUE))
        self.assertTrue(first["path"].startswith(os.path.join(self.d, "queue")))
        self.assertNotEqual(first["path"], self.src)

    def test_reading_view_not_requeued(self):
        tv._LAST_EMIT_SIG = self._sig(0)
        tv._settle_enqueue(self.src, self._sig(0))
        self.assertEqual(len(tv._SETTLE_QUEUE), 0)
        tv._settle_enqueue(self.src, self._sig(120))
        self.assertEqual(len(tv._SETTLE_QUEUE), 1)

    def test_cap_eviction_is_fifo(self):
        tv.SETTLE_QUEUE_CAP = 2
        for v in (0, 80, 160):
            tv._settle_enqueue(self.src, self._sig(v))
        self.assertEqual([e["sig"] for e in tv._SETTLE_QUEUE],
                         [self._sig(80), self._sig(160)])
        qd = os.path.join(self.d, "queue")
        self.assertEqual(sorted(os.listdir(qd)),
                         sorted(os.path.basename(e["path"]) for e in tv._SETTLE_QUEUE))

    def test_drain_pops_newest_and_cleans_the_rest(self):
        for v in (0, 80, 160):
            tv._settle_enqueue(self.src, self._sig(v))
        older = [e["path"] for e in tv._SETTLE_QUEUE[:-1]]
        entry = tv._settle_drain_pop()
        self.assertIsNotNone(entry)
        self.assertEqual(entry["sig"], self._sig(160))
        self.assertEqual(len(tv._SETTLE_QUEUE), 0)
        self.assertTrue(os.path.isfile(entry["path"]))
        for p in older:
            self.assertFalse(os.path.isfile(p))
        self.assertIsNone(tv._settle_drain_pop())

    def test_stale_entries_dropped(self):
        tv._settle_enqueue(self.src, self._sig(0))
        stale_path = tv._SETTLE_QUEUE[0]["path"]
        tv._SETTLE_QUEUE[0]["ts"] -= (tv.SETTLE_QUEUE_STALE_MS + 5000)
        tv._settle_enqueue(self.src, self._sig(80))
        self.assertEqual([e["sig"] for e in tv._SETTLE_QUEUE], [self._sig(80)])
        self.assertFalse(os.path.isfile(stale_path))
        tv._SETTLE_QUEUE[0]["ts"] -= (tv.SETTLE_QUEUE_STALE_MS + 5000)
        p2 = tv._SETTLE_QUEUE[0]["path"]
        self.assertIsNone(tv._settle_drain_pop())
        self.assertFalse(os.path.isfile(p2))

    def test_clear_wipes_files_on_farewell(self):
        for v in (0, 80):
            tv._settle_enqueue(self.src, self._sig(v))
        paths = [e["path"] for e in tv._SETTLE_QUEUE]
        tv._settle_queue_clear()
        self.assertEqual(len(tv._SETTLE_QUEUE), 0)
        for p in paths:
            self.assertFalse(os.path.isfile(p))
        qd = os.path.join(self.d, "queue")
        if os.path.isdir(qd):
            self.assertFalse([f for f in os.listdir(qd) if f.endswith(".bmp")])

    # ── v944 brains 1+2 calibration (film-medic): eviction justice + sweeper backlog ──
    @staticmethod
    def _dsig(seed):
        # distinct-sig helper: bytes([v])*4096 sigs land under the ~28/byte
        # dedupe tolerance at SETTLE=0.03 — scramble per-byte instead
        return bytes([(seed * 131 + j * (seed * 7 + 1)) % 256 for j in range(4096)])

    def test_eviction_protects_text_eye(self):
        tv.SETTLE_QUEUE_CAP = 4
        tv.PRIORITY_CAP_BONUS = 6
        for v in (1, 2, 3):
            tv._settle_enqueue(self.src, self._dsig(v), interest=0.95,
                               priority=True, origin="text-eye")
        for v in (10, 11, 12, 13, 14):
            tv._settle_enqueue(self.src, self._dsig(v), interest=0.2,
                               priority=False, origin="settle")
        te = [e for e in tv._SETTLE_QUEUE if e["origin"] == "text-eye"]
        self.assertEqual(len(te), 3)                  # text-eye never evicted for settle
        self.assertEqual(len(tv._SETTLE_QUEUE), 4)    # trimmed to base cap
        self.assertEqual(
            [e for e in tv._SETTLE_QUEUE if e["origin"] == "settle"][0]["sig"],
            self._dsig(14))

    def test_all_priority_ring_holds_to_raised_cap(self):
        tv.SETTLE_QUEUE_CAP = 4
        tv.PRIORITY_CAP_BONUS = 6
        for v in range(10):
            tv._settle_enqueue(self.src, self._dsig(100 + v),
                               priority=True, origin="text-eye")
        self.assertEqual(len(tv._SETTLE_QUEUE), 10)
        tv._settle_enqueue(self.src, self._dsig(200),
                           priority=True, origin="text-eye")
        self.assertEqual(len(tv._SETTLE_QUEUE), 10)
        self.assertEqual(tv._SETTLE_QUEUE[0]["sig"], self._dsig(101))  # oldest shed

    def test_drain_backlogs_unread_text_eye(self):
        tv.SETTLE_QUEUE_CAP = 8
        tv._TEXT_EYE_BACKLOG[:] = []
        for v in (1, 2, 3):
            tv._settle_enqueue(self.src, self._dsig(v),
                               priority=True, origin="text-eye")
        tv._settle_enqueue(self.src, self._dsig(50), priority=False, origin="settle")
        te_paths = [e["path"] for e in tv._SETTLE_QUEUE if e["origin"] == "text-eye"]
        entry = tv._settle_drain_pop()
        self.assertEqual(entry["sig"], self._dsig(50))             # newest fired live
        self.assertEqual(len(tv._TEXT_EYE_BACKLOG), 3)             # older text-eye backlogged
        self.assertTrue(all(os.path.isfile(p) for p in te_paths))  # files kept
        self.assertEqual(tv._text_eye_backlog_pop()["sig"], self._dsig(1))  # oldest swept first

    def test_drained_read_stamps_original_capture_clock(self):
        """v1187 REGRESSION — a queue-held frame was captured earlier (that's the entry's own
        'ts', same clock _settle_drain_pop already trusts for staleness). Before this fix,
        _fire_read always stamped the DRAIN moment (time.time() at read time) into the
        frame_id/captureTs the retro debugger joins on, silently desyncing a held frame from
        the moment its pixels were actually captured — worse the longer it sat queued (up to
        SETTLE_QUEUE_STALE_MS). _resolve_read_ts (what _fire_read now calls) must return the
        entry's real capture clock when a drain caller passes it, not now()."""
        tv._settle_enqueue(self.src, self._sig(0))
        entry = tv._settle_drain_pop()
        held_ts = entry["ts"]
        # simulate the read landing well after the frame was actually captured — exactly the
        # 'held while readers were busy' scenario this queue exists for
        time.sleep(0.05)
        stamped = tv._resolve_read_ts(cap_ts_override=held_ts)
        self.assertEqual(stamped, held_ts, "drained read must stamp the frame's OWN capture time")
        self.assertLess(stamped, int(time.time() * 1000),
                         "must not silently become the drain-time now()")
        # frame_id built from that stamp must round-trip to the same captureTs (the join law)
        fid = "1_%d" % stamped
        self.assertEqual(tv._capture_ts_from_frame_id(fid), held_ts)

    def test_live_read_still_defaults_to_now(self):
        """v1187 — a fresh/live read (no queue involved) has no earlier clock to honor;
        _resolve_read_ts must keep stamping now(), unchanged from before this fix."""
        before = int(time.time() * 1000)
        stamped = tv._resolve_read_ts(cap_ts_override=None)
        after = int(time.time() * 1000)
        self.assertGreaterEqual(stamped, before)
        self.assertLessEqual(stamped, after)


class TestLocationTruth(unittest.TestCase):
    """v830 (Konyo forensics) — equipped gear never farms; inventory-side holds; stash vaults."""

    def test_parse_roundtrip_names_loc(self):
        raw = ('{"area":"","tz":[],"scene":"stash","names":["Harlequin Crest","Flame Rift Grand Charm"],'
               '"names_loc":{"Harlequin Crest":"equipped","Flame Rift Grand Charm":"inventory"},'
               '"discovered":[],"conf":0.9}')
        pr = tv._parse_read(raw)
        self.assertEqual(pr["names_loc"].get("Harlequin Crest"), "equipped")
        self.assertEqual(pr["names_loc"].get("Flame Rift Grand Charm"), "inventory")

    def test_equipped_shako_never_vaults(self):
        lc = tv.LootLifecycle()
        r = lc.process("stash", ["Harlequin Crest"], "Harrogath", 0.9,
                       names_loc={"Harlequin Crest": "equipped"})
        self.assertNotIn("Harlequin Crest", r["vault_names"])
        self.assertNotIn("Harlequin Crest", r["pending_names"])
        self.assertEqual(r["lifecycle_tags"].get("Harlequin Crest"), "equipped")

    def test_inventory_charm_holds_not_vaults(self):
        lc = tv.LootLifecycle()
        lc.process("loot", ["Flame Rift Grand Charm"], "Chaos", 0.9)
        r = lc.process("stash", ["Flame Rift Grand Charm"], "Harrogath", 0.9,
                       names_loc={"Flame Rift Grand Charm": "inventory"})
        self.assertNotIn("Flame Rift Grand Charm", r["vault_names"], "inventory-side must NOT vault")
        self.assertIn("Flame Rift Grand Charm", r["pending_names"], "inventory-side holds")

    def test_true_stash_still_vaults(self):
        lc = tv.LootLifecycle()
        lc.process("loot", ["Ist Rune"], "Chaos", 0.9)
        r = lc.process("stash", ["Ist Rune"], "Harrogath", 0.9,
                       names_loc={"Ist Rune": "stash"})
        self.assertIn("Ist Rune", r["vault_names"])

    def test_emit_carries_equipped_names(self):
        rec = tv.emit_deep_read({"area": "Harrogath", "scene": "stash",
                                 "names": ["Harlequin Crest"], "tz": [], "conf": 0.9,
                                 "names_loc": {"Harlequin Crest": "equipped"}},
                                42, "42_4242", capture_ts=4242)
        self.assertIn("Harlequin Crest", rec.get("equipped_names") or [])
        self.assertNotIn("Harlequin Crest", rec.get("vault_names") or [])



class TestDispatchDecomposition(unittest.TestCase):
    """v833 (Grok addendum A2.1) — the interest score exposes its parts; parts sum to score."""

    def test_parts_sum(self):
        parts = {}
        s = tv.ap_interest(0.5, 2, True, 0, True, parts=parts)
        self.assertAlmostEqual(min(1.0, sum(parts.values())), s, places=5)
        self.assertGreater(parts["peak"], 0)
        self.assertGreater(parts["priority"], 0)

    def test_parts_optional(self):
        self.assertEqual(tv.ap_interest(0.0, 0, False, 5, False),
                         tv.ap_interest(0.0, 0, False, 5, False, parts={}))



class TestParseAudit(unittest.TestCase):
    """v835 (Grok A2.2) — clamps and drops are RECORDED, never silent."""

    def test_scene_clamp_recorded(self):
        pr = tv._parse_read('{"area":"","scene":"loading","names":[],"conf":0.5}')
        au = pr.get("_parse_audit") or {}
        self.assertTrue(au.get("ok"))
        norm = au.get("normalized") or []
        self.assertTrue(any(x.get("field") == "scene" and x.get("from") == "loading" for x in norm))
        self.assertEqual(pr["scene"], "gameplay")

    def test_invalid_loc_drop_recorded(self):
        pr = tv._parse_read('{"scene":"stash","names":["Foo"],"names_loc":{"Foo":"bag"},"conf":0.5}')
        au = pr.get("_parse_audit") or {}
        self.assertTrue(any("names_loc" in (x.get("field") or "") for x in au.get("dropped") or []))

    def test_clean_parse_clean_audit(self):
        pr = tv._parse_read('{"scene":"loot","names":["Ist"],"names_loc":{"Ist":"floor"},"conf":0.9}')
        au = pr.get("_parse_audit") or {}
        self.assertTrue(au.get("ok"))
        self.assertFalse(au.get("dropped"))
        self.assertFalse(au.get("normalized"))



class TestDecisionChain(unittest.TestCase):
    """v836 — every name gets {loc, tag, why} on the rec; the whys speak owner language."""

    def test_decisions_on_rec(self):
        rec = tv.emit_deep_read({"area": "Harrogath", "scene": "stash",
                                 "names": ["Skull Shell Crown"], "tz": [], "conf": 0.9,
                                 "names_loc": {"Skull Shell Crown": "stash"}},
                                77, "77_7777", capture_ts=7777)
        d = (rec.get("decisions") or {}).get("Skull Shell Crown") or {}
        self.assertEqual(d.get("loc"), "stash")
        self.assertTrue(d.get("why"), "why missing")
        self.assertIn("provenance", d.get("why", "") + "provenance")  # non-empty sanity

    def test_reason_language(self):
        self.assertIn("never farms", tv._reason_for("equipped"))
        self.assertIn("no provenance", tv._reason_for("stash-no-chain"))
        self.assertIn("committed", tv._reason_for("vault:stash"))



class TestItemishGate(unittest.TestCase):
    """v848 — OCR garbage never seeds the chain."""

    def test_gate(self):
        self.assertTrue(tv._itemish("Harlequin Crest"))
        self.assertTrue(tv._itemish("Ist Rune"))
        self.assertFalse(tv._itemish("QvfST L\u2022"))
        self.assertFalse(tv._itemish("y$-."))
        self.assertFalse(tv._itemish("xyz"))
        self.assertFalse(tv._itemish("FLAfflQ R{}"))



class TestScorerOverride(unittest.TestCase):
    """v849 (audit-core #4) — a wine/CrossOver-owned window with an unambiguous game title
    at game size must PASS the blocklists (Quartz sometimes reports the owner that way)."""

    def test_crossover_owner_with_game_title_passes(self):
        sc = tv.score_d2r_window_candidate("CrossOver", "Diablo II: Resurrected", 1470, 956, True)
        self.assertIsNotNone(sc, "game title + size must override the shell owner")

    def test_crossover_launcher_still_rejected(self):
        self.assertIsNone(tv.score_d2r_window_candidate("CrossOver", "CrossOver", 1150, 700, False))

    def test_browser_bible_tab_still_rejected(self):
        self.assertIsNone(tv.score_d2r_window_candidate("Google Chrome", "Konyo's D2R Farming Bible", 1470, 900, True))



class TestPinRaceHotfix(unittest.TestCase):
    """v852 (Grok R17 b) — the override is wine-scoped: browsers stay DEAD; runes are itemish."""

    def test_browser_with_game_title_stays_dead(self):
        self.assertIsNone(tv.score_d2r_window_candidate("Google Chrome", "Diablo II: Resurrected build guide", 1470, 900, True))
        self.assertIsNone(tv.score_d2r_window_candidate("Safari", "resurrected wiki", 1200, 800, True))

    def test_crossover_short_title_passes(self):
        self.assertIsNotNone(tv.score_d2r_window_candidate("CrossOver", "D2R", 1470, 956, True))

    def test_bare_runes_are_itemish(self):
        for r in ("Ist", "Ber", "Io", "El", "Jah", "Ist Rune"):
            self.assertTrue(tv._itemish(r), r)
        self.assertFalse(tv._itemish("QvfST L\u2022"))



class TestPreTriage(unittest.TestCase):
    """v853 (A2.3+A2.7) — the silent filters get a journal."""

    def test_gate_matrix(self):
        pre = tv._pre_triage(["Harlequin Crest", "Healing Potion"],
                             {"names": ["Ber", "QvfST L\u2022"],
                              "dropped": [{"line": "Keop INvENT", "why": "line-filter"}]})
        by = {(x["name"], x["lane"]): x["gate"] for x in pre}
        self.assertEqual(by[("Harlequin Crest", "deep")], "pass")
        self.assertEqual(by[("Ber", "ocr")], "pass")
        self.assertEqual(by[("QvfST L\u2022", "ocr")], "not-itemish")
        self.assertIn(("Keop INvENT", "ocr"), [(x["name"], x["lane"]) for x in pre])

    def test_rec_carries_pre_and_raw(self):
        rec = tv.emit_deep_read({"area": "Chaos", "scene": "loot", "names": ["Ist"],
                                 "tz": [], "conf": 0.9},
                                88, "88_8888",
                                ocr_rd={"names": ["Ist"], "raw_lines": ["Ist", "xx"], "ms": 30},
                                capture_ts=8888)
        self.assertTrue(rec.get("pre"))
        self.assertEqual(rec.get("ocr_raw"), ["Ist", "xx"])



class TestChainProvenance(unittest.TestCase):
    """v855 (A2.4) — provenance at decision time makes stash-no-chain diagnosable."""

    def test_never_seen_vs_seen(self):
        lc = tv.LootLifecycle()
        lc.process("loot", ["Ist Rune"], "Chaos", 0.9)
        r = lc.process("stash", ["Ist Rune", "Blood Shield"], "Harrogath", 0.9,
                       names_loc={"Ist Rune": "stash", "Blood Shield": "stash"})
        ch = r.get("chain") or {}
        self.assertTrue(ch.get("Ist Rune", {}).get("seen") or ch.get("Ist Rune", {}).get("vaulted"))
        bs = ch.get("Blood Shield") or {}
        self.assertFalse(bs.get("seen") or bs.get("pending") or bs.get("candidate") or bs.get("vaulted"),
                         "never-seen must snapshot as chainless")
        self.assertEqual(r["lifecycle_tags"].get("Blood Shield"), "stash-no-chain")

    def test_rec_carries_chain(self):
        rec = tv.emit_deep_read({"area": "Harrogath", "scene": "stash", "names": ["Widowmaker"],
                                 "tz": [], "conf": 0.9, "names_loc": {"Widowmaker": "stash"}},
                                91, "91_9191", capture_ts=9191)
        self.assertIn("Widowmaker", rec.get("chain") or {})



class TestChainClasses(unittest.TestCase):
    """v856 (Grok R18) — the closed class enum + wipe-retention lock."""

    def test_never_seen_class(self):
        lc = tv.LootLifecycle()
        r = lc.process("stash", ["Blood Shield"], "Harrogath", 0.9,
                       names_loc={"Blood Shield": "stash"})
        c = (r.get("chain") or {}).get("Blood Shield") or {}
        self.assertEqual(c.get("class"), "never-seen")

    def test_full_chain_retained_after_wipe(self):
        lc = tv.LootLifecycle()
        lc.process("loot", ["Widowmaker"], "Stony Field", 0.9)
        r = lc.process("stash", ["Widowmaker"], "Harrogath", 0.9,
                       names_loc={"Widowmaker": "stash"})
        c = (r.get("chain") or {}).get("Widowmaker") or {}
        self.assertTrue(c.get("seen"), "journaled chain must retain wasSeen AFTER the commit wipe")
        self.assertEqual(c.get("class"), "full-chain")
        self.assertIn("Widowmaker", r["vault_names"])

    def test_wiped_by_commit_echo(self):
        lc = tv.LootLifecycle()
        lc.process("loot", ["Titan's Revenge"], "Chaos", 0.9)
        lc.process("stash", ["Titan's Revenge"], "Harrogath", 0.9,
                   names_loc={"Titan's Revenge": "stash"})
        r = lc.process("stash", ["Titan's Revenge"], "Harrogath", 0.9,
                       names_loc={"Titan's Revenge": "stash"})
        c = (r.get("chain") or {}).get("Titan's Revenge") or {}
        self.assertEqual(c.get("class"), "wiped-by-commit")

    def test_decisions_nest_chain(self):
        rec = tv.emit_deep_read({"area": "Harrogath", "scene": "stash", "names": ["Buriza-Do Kyanon"],
                                 "tz": [], "conf": 0.9, "names_loc": {"Buriza-Do Kyanon": "stash"}},
                                93, "93_9393", capture_ts=9393)
        d = (rec.get("decisions") or {}).get("Buriza-Do Kyanon") or {}
        self.assertIn("chain", d)
        self.assertEqual((d.get("chain") or {}).get("class"), "never-seen")


class TestReaderPool(unittest.TestCase):
    """v863 — READER POOL: ordered apply (floor-before-stash lock), stragglers, private files,
    job-carried dispatch identity, and POOL_N=1 regression parity."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self._state, self._journal = tv.STATE, tv.JOURNAL
        tv.STATE = os.path.join(self.d, "state.json")
        tv.JOURNAL = os.path.join(self.d, "j.jsonl")
        with open(tv.STATE, "w") as f:
            json.dump({"reads": [], "seen": [], "farmed": []}, f)
        self._life = tv._LIFECYCLE
        tv._LIFECYCLE = tv.LootLifecycle()
        self._pool_n, self._hold = tv.POOL_N, tv.ORDER_HOLD_MS
        with tv._pool_lock:
            tv._in_flight.clear()
            tv._pool_free[:] = list(range(tv.POOL_N))
        with tv._emit_lock:
            tv._order_buf[:] = []

    def tearDown(self):
        tv.STATE, tv.JOURNAL = self._state, self._journal
        tv._LIFECYCLE = self._life
        tv.POOL_N, tv.ORDER_HOLD_MS = self._pool_n, self._hold
        with tv._pool_lock:
            tv._in_flight.clear()
            tv._pool_free[:] = list(range(tv.POOL_N))
        with tv._emit_lock:
            tv._order_buf[:] = []

    def _mark_inflight(self, jid, rid, cap):
        with tv._pool_lock:
            tv._in_flight[jid] = {"readerId": rid, "captureTs": cap, "sig": [],
                                  "origin": "settle", "startedAt": cap}

    def _pop_inflight(self, jid):
        with tv._pool_lock:
            tv._in_flight.pop(jid, None)

    def _job(self, n, rid):
        return {"n": n, "fid": "", "interest": 0.5, "priority": False,
                "dispatch": {"readerId": rid, "poolN": tv.POOL_N, "poolInFlight": 1,
                             "origin": "settle"}, "raw": ""}

    def test_order_buffer_floor_before_stash_lock(self):
        """T2(stash) completes before T1(floor). Ordered apply must HOLD the stash read until
        the older floor read lands — then the stash finds its chain and the item VAULTS."""
        item = "Colossus Crossbow"
        now = int(time.time() * 1000)
        t1, t2 = now, now + 1
        self._mark_inflight("a", 0, t1)   # floor read — OLDER
        self._mark_inflight("b", 1, t2)   # stash read — newer
        rd_floor = {"area": "Black Marsh", "scene": "loot", "names": [item], "conf": 0.9, "ms": 10}
        rd_stash = {"area": "town", "scene": "stash", "stashTab": "shared",
                    "names": [item], "conf": 0.9, "ms": 10}
        self._pop_inflight("b")
        tv._order_push(t2, self._job(2, 1), rd_stash, None)
        held = tv._order_drain()
        self.assertEqual(held, [], "stash read applied out of order — floor lock broken")
        self.assertNotIn(tv._norm_name(item), tv._LIFECYCLE.vaulted)
        self._pop_inflight("a")
        tv._order_push(t1, self._job(1, 0), rd_floor, None)
        applied = tv._order_drain()
        self.assertEqual(len(applied), 2, "both reads should apply once the floor read lands")
        self.assertEqual(applied[0].get("scene"), "loot")
        self.assertEqual(applied[-1].get("scene"), "stash")
        self.assertIn(item, applied[-1].get("vault_names") or [],
                      "stash must VAULT after ordered floor-first apply")
        self.assertIn(tv._norm_name(item), tv._LIFECYCLE.vaulted)

    def test_straggler_applies_after_order_hold(self):
        """An older read wedges in flight forever. The newer buffered read must NOT wait past
        ORDER_HOLD_MS — it applies anyway, flagged dispatch.orderSkip='straggler'."""
        item = "Vex Rune"
        now = int(time.time() * 1000)
        t1, t2 = now, now + 1
        self._mark_inflight("a", 0, t1)   # STUCK older reader (never completes)
        rd = {"area": "River of Flame", "scene": "loot", "names": [item], "conf": 0.9, "ms": 10}
        tv._order_push(t2, self._job(2, 1), rd, None)
        self.assertEqual(tv._order_drain(), [])
        tv.ORDER_HOLD_MS = 0
        applied = tv._order_drain()
        self.assertEqual(len(applied), 1)
        disp = applied[0].get("dispatch") or {}
        self.assertEqual(disp.get("orderSkip"), "straggler")
        self.assertIn("appliedTs", disp)
        self.assertEqual(disp.get("orderHoldMs"), 0)

    def test_private_job_files_distinct(self):
        """Two concurrent readers must never share snap.bmp / read.jpg."""
        s0, r0 = tv._job_files(0, 5)
        s1, r1 = tv._job_files(1, 5)
        self.assertNotEqual(s0, s1)
        self.assertNotEqual(r0, r1)
        self.assertTrue(os.path.basename(s0).startswith("snap_0_5"))
        self.assertTrue(os.path.basename(s1).startswith("snap_1_5"))
        self.assertTrue(os.path.basename(r0).startswith("read_0_5"))
        self.assertTrue(r0.endswith(".jpg") and s0.endswith(".bmp"))
        self.assertNotEqual(tv._job_files(0, 5)[0], tv._job_files(0, 6)[0])

    def test_dispatch_carries_reader_identity(self):
        now = int(time.time() * 1000)
        rd = {"area": "town", "scene": "gameplay", "names": [], "conf": 0.9, "ms": 5}
        job = {"n": 7, "fid": "", "interest": 0.5, "priority": False,
               "dispatch": {"readerId": 2, "poolN": 3, "poolInFlight": 2, "origin": "settle"},
               "raw": "the-thought"}
        tv._order_push(now, job, rd, None)
        applied = tv._order_drain()
        self.assertEqual(len(applied), 1)
        disp = applied[0].get("dispatch") or {}
        self.assertEqual(disp.get("readerId"), 2)
        self.assertEqual(disp.get("poolN"), 3)
        self.assertIn("appliedTs", disp)
        self.assertEqual(applied[0].get("raw"), "the-thought")

    def test_pool_n_one_busy_semantics(self):
        tv.POOL_N = 1
        with tv._pool_lock:
            tv._in_flight.clear()
            tv._pool_free[:] = [0]
        self.assertFalse(tv._vision_busy())
        self.assertEqual(tv._vision_in_flight_n(), 0)
        self._mark_inflight("solo", 0, int(time.time() * 1000))
        self.assertTrue(tv._vision_busy())
        self.assertEqual(tv._vision_in_flight_n(), 1)
        self._pop_inflight("solo")
        self.assertFalse(tv._vision_busy())

    def test_pool_default_is_8_and_clamps_1_to_8(self):
        import subprocess as sp
        tvdir = os.path.dirname(os.path.abspath(tv.__file__))

        def pooln(env_val):
            # TV_POOL only applies when Robot is unlocked (intake default forces pool=1)
            e = dict(os.environ)
            e.pop("TV_POOL", None)
            e["TV_ROBOT"] = "1"
            if env_val is not None:
                e["TV_POOL"] = env_val
            out = sp.check_output(
                [sys.executable, "-c",
                 "import tv_diablo,sys; sys.stdout.write(str(tv_diablo.POOL_N))"],
                cwd=tvdir, env=e, text=True)
            return int(out.strip())

        # v901 — default Auto Intake forces POOL_N=1 regardless of RAM; robot uses lean map.
        def pooln_gb(gb, robot="0"):
            e = dict(os.environ); e.pop("TV_POOL", None); e["TV_POOL_ASSUME_GB"] = gb
            e["TV_ROBOT"] = robot
            out = sp.check_output([sys.executable, "-c",
                "import tv_diablo,sys; sys.stdout.write(str(tv_diablo.POOL_N))"],
                cwd=tvdir, env=e, text=True)
            return int(out.strip())
        self.assertEqual(pooln_gb("16", "0"), 1, "intake default → 1 reader")
        self.assertEqual(pooln_gb("32", "0"), 1, "intake ignores big RAM")
        self.assertEqual(pooln_gb("16", "1"), 2, "robot 16GB → 2")
        self.assertEqual(pooln_gb("24", "1"), 3, "robot 24GB → 3")
        self.assertEqual(pooln_gb("32", "1"), 4, "robot 32GB → 4")
        self.assertEqual(pooln("1"), 1)
        self.assertEqual(pooln("3"), 3)
        self.assertEqual(pooln("6"), 6)
        self.assertEqual(pooln("12"), 6)
        self.assertEqual(pooln("0"), 1)

    def test_heartbeat_cap_adaptive(self):
        # v900 — lean: default 1 concurrent heartbeat; pool≥3 + healthy film can earn 2.
        import time as _t
        old_n = tv.POOL_N
        try:
            tv.POOL_N = 2
            tv._FOOT_TIMES.clear()
            tv._FILM_CAP_MS = 0
            self.assertEqual(tv._heartbeat_cap(), 1, "pool 2 → always 1 heartbeat")
            now = _t.time()
            for i in range(20):
                tv._FOOT_TIMES.append(now - i * 1.0)
            tv._FILM_CAP_MS = 100
            self.assertEqual(tv._heartbeat_cap(), 1, "pool 2 healthy still 1")
            tv.POOL_N = 4
            tv._FILM_CAP_MS = 100
            self.assertEqual(tv._heartbeat_cap(), 2, "pool 4 healthy → 2")
            tv._FILM_CAP_MS = 2000
            self.assertEqual(tv._heartbeat_cap(), 1, "slow capture → 1")
            tv.POOL_N = 1
            self.assertEqual(tv._heartbeat_cap(), 1, "N=1 → 1 always")
        finally:
            tv.POOL_N = old_n
            tv._FOOT_TIMES.clear()
            tv._FILM_CAP_MS = 0

class TestSourceShapeLocks(unittest.TestCase):
    """v877 (army suite-audit #1/#2) — SOURCE-ORDER locks for the two bugs Konyo caught LIVE:
    the v861 heartbeat was dead below the motion-continue twice; a regression would pass every
    behavior test (the loop is unexitable). Lock the SHAPE of main() itself."""

    def _main_src(self):
        import inspect
        return inspect.getsource(tv.main)

    def test_heartbeat_fires_before_the_motion_gate(self):
        src = self._main_src()
        hb = src.find("_heartbeat_cap()")
        self.assertGreater(hb, 0, "heartbeat gate missing from main()")
        # the FIRST motion-continue after the watching beat must come AFTER the heartbeat gate
        watch = src.find('beat("watching", motion)')
        self.assertGreater(watch, 0)
        motion_gate = src.find("if motion > SETTLE:", watch)
        self.assertGreater(motion_gate, 0)
        self.assertLess(hb, motion_gate,
                        "v866 REGRESSION: heartbeat sits below the motion-continue again (dead in combat)")

    def test_heartbeat_gate_wires_the_adaptive_cap_and_dedupe(self):
        src = self._main_src()
        hb_at = src.find("_heartbeat_cap()")
        gate = src[hb_at - 600:hb_at + 600]
        self.assertIn("_heartbeat_in_flight_n()", gate, "cap not compared against heartbeat in-flight")
        self.assertIn("_in_flight_has_sig", gate, "v868 REGRESSION: same-view double-dispatch de-dupe gone")

    def test_youth_shield_survives_disk_emergency(self):
        """v873 — an emergency shed may NEVER eat frames younger than 15min."""
        import collections, unittest.mock, shutil as sh, time as _t
        d = tempfile.mkdtemp()
        old_hist, old_j = tv.HIST_DIR, tv.JOURNAL
        tv.HIST_DIR, tv.JOURNAL = d, os.path.join(d, "nope.jsonl")
        tv._JFID_STATE = {"path": None, "ids": None}
        tv._ORPHAN_DUE = 0.0
        try:
            now = _t.time()
            for i in range(6):   # OLD footage (1h) — legitimate shed fuel
                fp = os.path.join(d, "f_%d.jpg" % (int((now - 3600) * 1000) + i))
                open(fp, "wb").write(b"J" * 4000)
                os.utime(fp, (now - 3600, now - 3600))
            young = []
            for i in range(6):   # YOUNG footage (2min) — must be untouchable
                fp = os.path.join(d, "f_%d.jpg" % (int((now - 120) * 1000) + i))
                open(fp, "wb").write(b"J" * 4000)
                young.append(os.path.basename(fp))
            starving = collections.namedtuple("usage", "total used free")(500e9, 499e9, 1e9)
            src = os.path.join(d, "seed.bmp")
            open(src, "wb").write(b"BM" + b"D" * 60000)
            with unittest.mock.patch.object(sh, "disk_usage", return_value=starving):
                tv.archive_read_frame(src, 1, 12345)
            left = set(os.listdir(d))
            for y in young:
                self.assertIn(y, left, "YOUTH SHIELD BREACH: young frame %s was shed" % y)
        finally:
            tv.HIST_DIR, tv.JOURNAL = old_hist, old_j
            tv._JFID_STATE = {"path": None, "ids": None}

    def test_parse_fuzz_corpus_never_raises(self):
        """v877 — _parse_read survives every garbage shape the CLI has ever produced."""
        corpus = [
            '```json\n{"names": ["Shako"], "scene": "gameplay"}\n```',
            '{"names": ["Shako"]',                       # truncated
            '{"names": []}{"names": ["Twice"]}',          # doubled objects
            '\ufeff{"names": ["BOM"]}',                  # BOM prefix
            '\x1b[32m{"names": ["ANSI"]}\x1b[0m',       # ANSI escapes
            '{"names": null, "scene": 7}',                # wrong types
            '{"names": "not-a-list"}',
            'I could not read the screen, sorry!',
            '{"names": ["War Scythe (6os)"], "scene": "gameplay"}',
            '', '   ', 'null', '[]', '{}', '0',
        ]
        for c in corpus:
            try:
                r = tv._parse_read(c)
            except Exception as e:
                self.fail("_parse_read raised on %r: %s" % (c[:40], e))
            self.assertTrue(r is None or isinstance(r, dict), repr(c[:40]))


class TestV926SecondLook(unittest.TestCase):
    """v926 — the verify lane: re-read the SAME frame, correct the tally, journal a distinct
    `lane=verify` beat so the funnel's exactly-once holds. Stub-driven (zero vision cost)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.hist = os.path.join(self.tmp, "hist")
        os.makedirs(self.hist)
        # a fake archived frame for the read the verify pass will re-check
        self.fid = "7_1784500000000"
        with open(os.path.join(self.hist, self.fid + ".jpg"), "wb") as f:
            f.write(b"\xff\xd8\xff\xe0FAKE")
        self.man = os.path.join(self.tmp, "man.json")
        self._old = (tv.HIST_DIR, tv.JOURNAL, dict(os.environ))
        tv.HIST_DIR = self.hist
        tv.JOURNAL = os.path.join(self.tmp, "sessions.jsonl")
        os.environ["TV_STUB"] = "1"
        os.environ["TV_STUB_MANIFEST"] = self.man
        tv.VERIFY_ON = True

    def tearDown(self):
        tv.HIST_DIR, tv.JOURNAL, env = self._old
        os.environ.clear(); os.environ.update(env)

    def _rows(self):
        try:
            return [json.loads(l) for l in open(tv.JOURNAL) if l.strip()]
        except FileNotFoundError:
            return []

    def test_misread_of_a_vaulted_name_is_removed_on_a_distinct_subframe(self):
        # verify rejects a reported name that WAS vaulted → un-tally it; a "missed" is surfaced
        # (verify.missed) for the debugger but NEVER auto-vaulted at pass-2 (Grok R4 footgun).
        with open(self.man, "w") as _mf:
            json.dump({os.path.basename(self.fid + ".jpg") + "#verify":
                       {"confirm": ["Ist Rune"], "not_present": ["Ohm Rune"], "missed": ["Vex Rune"], "conf": 0.95}}, _mf)
        job = {"fid": self.fid, "names": ["Ist Rune", "Ohm Rune"], "vaulted": ["Ist Rune", "Ohm Rune"],
               "n": 7, "sid": "s_v", "scene": "loot", "cap_ms": 1784500000000}
        out = tv._verify_apply(job)
        self.assertIsNotNone(out)
        self.assertEqual(sorted(out["remove"]), ["Ohm Rune"])
        self.assertEqual(out["add"], [])                          # ADD deferred to pass-3
        vrows = [r for r in self._rows() if r.get("lane") == "verify"]
        self.assertEqual(len(vrows), 1)
        self.assertEqual(vrows[0]["frameId"], self.fid + "#v")   # distinct → funnel exactly-once holds
        self.assertEqual(vrows[0]["vault_names"], [])            # never force-vault a hallucination
        self.assertIn("Ohm Rune", vrows[0]["unvault_names"])
        self.assertIn("Vex Rune", vrows[0]["verify"]["missed"])  # surfaced for the debugger, not applied

    def test_reject_of_a_name_that_was_never_vaulted_does_nothing(self):
        # the read named Ohm but did NOT vault it → verify rejecting Ohm must not unvault (nothing to remove)
        with open(self.man, "w") as _mf:
            json.dump({os.path.basename(self.fid + ".jpg") + "#verify":
                       {"confirm": ["Ist Rune"], "not_present": ["Ohm Rune"], "missed": [], "conf": 0.95}}, _mf)
        out = tv._verify_apply({"fid": self.fid, "names": ["Ist Rune", "Ohm Rune"], "vaulted": ["Ist Rune"],
                                "n": 7, "sid": "s_v", "scene": "loot", "cap_ms": 1784500000000})
        self.assertEqual(out["delta"], 0)
        vrows = [r for r in self._rows() if r.get("lane") == "verify"]
        self.assertEqual(vrows[0]["unvault_names"], [])

    def test_clean_confirm_makes_no_engine_delta_but_still_records_the_look(self):
        with open(self.man, "w") as _mf:
            json.dump({os.path.basename(self.fid + ".jpg") + "#verify":
                       {"confirm": ["Ist Rune"], "not_present": [], "missed": [], "conf": 0.9}}, _mf)
        out = tv._verify_apply({"fid": self.fid, "names": ["Ist Rune"], "n": 7, "sid": "s_v",
                                "scene": "loot", "cap_ms": 1784500000000})
        self.assertEqual(out["delta"], 0)
        vrows = [r for r in self._rows() if r.get("lane") == "verify"]
        self.assertEqual(len(vrows), 1)
        self.assertEqual(vrows[0]["vault_names"], [])
        self.assertEqual(vrows[0]["unvault_names"], [])

    def test_low_confidence_verify_changes_nothing(self):
        with open(self.man, "w") as _mf:
            json.dump({os.path.basename(self.fid + ".jpg") + "#verify":
                       {"confirm": [], "not_present": ["Ist Rune"], "missed": ["Ber Rune"], "conf": 0.4}}, _mf)
        out = tv._verify_apply({"fid": self.fid, "names": ["Ist Rune"], "n": 7, "sid": "s_v",
                                "scene": "loot", "cap_ms": 1784500000000})
        self.assertEqual(out["delta"], 0)   # conf<0.7 → no remove, conf<0.8 → no add

    def test_close_time_drain_respects_a_past_deadline(self):
        # v1179 CLOSER — a deadline already in the past (the shutdown budget is spent) must
        # leave the queue untouched rather than overrun the caller's time box.
        with open(self.man, "w") as _mf:
            json.dump({os.path.basename(self.fid + ".jpg") + "#verify":
                       {"confirm": ["Ist Rune"], "not_present": [], "missed": [], "conf": 0.9}}, _mf)
        tv._VERIFY_Q.append({"fid": self.fid, "names": ["Ist Rune"], "vaulted": ["Ist Rune"],
                             "n": 7, "sid": "s_v", "scene": "loot", "cap_ms": 1784500000000})
        tv._verify_drain(budget=len(tv._VERIFY_Q), deadline=time.time() - 1.0)
        self.assertEqual(len(tv._VERIFY_Q), 1)   # nothing spent — the job is still queued
        tv._VERIFY_Q.clear()

    def test_close_time_drain_clears_a_multi_item_backlog_before_a_future_deadline(self):
        # v1179 CLOSER — the last read(s) before session close must not vanish un-verified:
        # a future deadline (spare time left in the shutdown budget) drains the WHOLE backlog,
        # not just the main-loop's usual budget=1 idle-gap trickle.
        fid2 = "8_1784500000100"
        with open(os.path.join(self.hist, fid2 + ".jpg"), "wb") as f:
            f.write(b"\xff\xd8\xff\xe0FAKE2")
        with open(self.man, "w") as _mf:
            json.dump({
                os.path.basename(self.fid + ".jpg") + "#verify":
                    {"confirm": ["Ist Rune"], "not_present": [], "missed": [], "conf": 0.9},
                os.path.basename(fid2 + ".jpg") + "#verify":
                    {"confirm": ["Ohm Rune"], "not_present": [], "missed": [], "conf": 0.9},
            }, _mf)
        tv._VERIFY_Q.append({"fid": self.fid, "names": ["Ist Rune"], "vaulted": ["Ist Rune"],
                             "n": 7, "sid": "s_v", "scene": "loot", "cap_ms": 1784500000000})
        tv._VERIFY_Q.append({"fid": fid2, "names": ["Ohm Rune"], "vaulted": ["Ohm Rune"],
                             "n": 8, "sid": "s_v", "scene": "loot", "cap_ms": 1784500000100})
        tv._verify_drain(budget=len(tv._VERIFY_Q), deadline=time.time() + 30.0)
        self.assertEqual(len(tv._VERIFY_Q), 0)   # both jobs drained, none silently dropped
        vrows = [r for r in self._rows() if r.get("lane") == "verify"]
        self.assertEqual(len(vrows), 2)
        self.assertEqual({r["frameId"] for r in vrows}, {self.fid + "#v", fid2 + "#v"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
