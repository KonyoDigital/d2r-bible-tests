# -*- coding: utf-8 -*-
"""A window titled only Boosteroid must show D2R HUD words in the first reads.

Boosteroid's own app titles the stream and the launcher with nothing but "Boosteroid"
(measured 2026-09-27). Both still pin — that pin is the windows-door law, and this one
does not build a second. The shadow door may call the window the game only when the
first reads show a zone name the HUD prints. Three reads with none is the launcher.
Fewer than that, or no reads at all, is UNKNOWN: a loading frame has no zone yet, and
an unread window is not called the launcher. A reel he opened is never sealed for this.

#167 - the one-frame relook after a launcher verdict has a camera only on the Mac. A Windows
console films only inside a reel, so there the wait ends and the reel's reads judge. On a Mac a
frame that will not come holds the door one more wait, never for ever. These cases run the real
_launcher_picture on the platform they name, so a Mac-only grabber on Windows turns them red.

RED_PROOF below.
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

_WORLD = tempfile.mkdtemp(prefix="bare_hud_")
os.environ["TV_HIST"] = _WORLD
os.environ["TV_SESSIONS"] = os.path.join(_WORLD, "sessions.jsonl")

import control_app as ca  # noqa: E402
import tv_diablo as tv  # noqa: E402
import window_visibility as WV  # noqa: E402

BARE = (2002, "Boosteroid · Boosteroid")
GAME = (4004, "Diablo II: Resurrected")
ZONE = [{"area": "Cold Plains", "scene": "gameplay", "names": []}]
LAUNCH = [
    {"area": "", "scene": "gameplay", "names": ["Play"]},
    {"area": "", "scene": "gameplay", "names": ["Library"]},
    {"area": "", "scene": "gameplay", "names": ["Boosteroid"]},
]


def _words():
    return set(ca._AREA_ACT)


class TheRelookComparesPictures(unittest.TestCase):

    def test_a_quiet_difference_is_the_same_picture(self):
        n = ca._RELOOK_EDGE * ca._RELOOK_EDGE * 3
        a = bytes([80] * n)
        b = bytes([80 + ca._RELOOK_SAME_TOL] * n)
        self.assertIs(ca._pictures_same(a.hex(), b.hex()), True)

    def test_a_different_screen_is_not_the_same_picture(self):
        n = ca._RELOOK_EDGE * ca._RELOOK_EDGE * 3
        self.assertIs(ca._pictures_same(bytes([0] * n).hex(), bytes([200] * n).hex()), False)

    def test_a_missing_side_is_unknown(self):
        n = ca._RELOOK_EDGE * ca._RELOOK_EDGE * 3
        self.assertIsNone(ca._pictures_same(None, bytes([1] * n).hex()))
        self.assertIsNone(ca._pictures_same("zz", bytes([1] * n).hex()))


class TheFirstReadsCarryTheHud(unittest.TestCase):

    def test_a_zone_name_in_the_first_read_is_the_game(self):
        self.assertIs(tv.first_reads_show_d2r_hud(ZONE, words=_words()), True)
        self.assertIs(tv.first_reads_show_d2r_hud(
            [{"area": "Rogue Encampment", "scene": "town"}], words=_words()), True)

    def test_three_launcher_reads_are_not_the_game(self):
        self.assertIs(tv.first_reads_show_d2r_hud(LAUNCH, words=_words()), False)

    def test_one_launcher_read_is_still_unknown(self):
        self.assertIsNone(tv.first_reads_show_d2r_hud(LAUNCH[:1], words=_words()))

    def test_no_reads_is_unknown(self):
        self.assertIsNone(tv.first_reads_show_d2r_hud(None, words=_words()))
        self.assertIsNone(tv.first_reads_show_d2r_hud([], words=_words()))
        self.assertIsNone(tv.first_reads_show_d2r_hud(LAUNCH, words=set()))

    def test_the_fourth_read_cannot_rescue_three_without_a_hud_word(self):
        rows = list(LAUNCH) + [{"area": "Cold Plains", "scene": "gameplay"}]
        self.assertIs(tv.first_reads_show_d2r_hud(rows, words=_words()), False)

    def test_a_zone_word_inside_another_word_is_not_the_zone(self):
        self.assertFalse(tv.text_has_d2r_hud_word("the capital pitfall", {"pit"}))
        self.assertTrue(tv.text_has_d2r_hud_word("the pit", {"pit"}))
        self.assertTrue(tv.text_has_d2r_hud_word("Cold Plains", _words()))

    def test_a_kai_or_intake_row_is_not_one_of_the_first_reads(self):
        # measured: those rows are written first, with an empty area, and are not the HUD
        rows = [
            {"lane": "kai", "scene": "kai", "names": ["Play"]},
            {"lane": "intake", "scene": "intake", "names": ["Library"]},
            {"lane": "kai", "scene": "kai", "names": ["Boosteroid"]},
            {"lane": "deep", "scene": "town", "area": "Cold Plains"},
        ]
        self.assertIs(tv.first_reads_show_d2r_hud(rows, words=_words()), True)
        self.assertIsNone(tv.first_reads_show_d2r_hud(rows[:3], words=_words()))

    # REG-1603 - MEASURED 2026-09-30 on his ALT: Claude signed out, every read failed and was journalled as the
    # fallback row; a black loading frame sat between them. Three of those sealed every shadow reel as "the
    # launcher" for a day (2-4-min reels, 2-min holes). These are the rows, as his journal holds them.
    ALT_FAILED = {"lane": "deep", "scene": "gameplay", "mode": "empty", "names": [], "area": "", "conf": None,
                  "model": "sonnet", "raw": "Failed to authenticate: OAuth session expired and could not be refreshed"}
    ALT_BLACK = {"lane": "known", "scene": "transition", "mode": "near-black", "names": [], "area": "",
                 "note": "loading \u2014 next area coming"}

    def test_a_read_that_did_not_happen_is_not_a_look(self):
        rows = [self.ALT_FAILED, self.ALT_BLACK, self.ALT_FAILED, self.ALT_FAILED]
        self.assertIsNone(tv.first_reads_show_d2r_hud(rows, words=_words()),
                          "failed reads and a black loading frame were taken as three looks that saw no HUD - "
                          "the launcher verdict that sealed every ALT reel")
        flagged = dict(self.ALT_FAILED, mode="vision", readFailed=True)
        self.assertIsNone(tv.first_reads_show_d2r_hud([flagged] * 3, words=_words()))

    def test_real_launcher_reads_still_decide_around_a_failed_one(self):
        rows = [LAUNCH[0], self.ALT_FAILED, LAUNCH[1], self.ALT_BLACK, LAUNCH[2]]
        self.assertIs(tv.first_reads_show_d2r_hud(rows, words=_words()), False,
                      "three REAL launcher reads stopped being the launcher because a failed one sat between them")
        self.assertIsNone(tv.first_reads_show_d2r_hud([LAUNCH[0], self.ALT_BLACK, LAUNCH[1]], words=_words()),
                          "a black loading frame was counted as the third look - two reads are not yet the launcher")

    def test_the_failed_read_row_says_it_failed_and_why(self):
        """the deep-read row the ALT journalled for a failed read now carries readFailed + the reader's words"""
        src = io.open(os.path.join(HERE, "tv_diablo.py"), encoding="utf-8").read()
        # the whole function, by its own boundaries - a fixed-size window measures a guess about its length
        fn = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "emit_deep_read"]
        self.assertEqual(len(fn), 1, "emit_deep_read is not one function any more")
        blk = ast.get_source_segment(src, fn[0])
        self.assertIn('{"readFailed": True, "readErr": _first_line(', blk)
        self.assertEqual(tv._first_line("\n  Failed to authenticate: OAuth session expired\nmore"),
                         "Failed to authenticate: OAuth session expired")

    def test_only_boosteroid_is_the_bare_label(self):
        self.assertTrue(tv.label_is_bare_boosteroid("Boosteroid · Boosteroid"))
        self.assertTrue(tv.label_is_bare_boosteroid("Boosteroid · Boosteroid · Boosteroid"))
        self.assertFalse(tv.label_is_bare_boosteroid("Diablo II: Resurrected"))
        self.assertFalse(tv.label_is_bare_boosteroid("Boosteroid · Diablo II: Resurrected"))
        self.assertFalse(tv.label_is_bare_boosteroid(""))


class TheMeasuredWindowIsTheBareOne(unittest.TestCase):

    def test_the_finder_label_is_bare_boosteroid(self):
        row = WV._win_row(20, "Boosteroid", (0, 0, 1920, 1040), 0, False, 0)
        row["hwnd"] = 2002

        class _Walk(object):
            def rows(self):
                return [row]

        hit = tv.find_d2r_window_win(win=_Walk(), procs={20: "Boosteroid.exe"})
        self.assertIsNotNone(hit, tv._PICK_WHY)
        self.assertTrue(tv.label_is_bare_boosteroid(hit[1]), hit)


class _Proc(object):
    pid = 4242

    def poll(self):
        return None


class TheDoorAsksTheFirstReads(unittest.TestCase):

    STUBS = ("_shadow_state", "_agent_alive", "mini_state", "start_agent", "stop_agent",
             "_force_kill_all_agents", "_mini_sid", "_shadow_now_ms", "_screen_recording_ok_quick",
             "ON_AIR_FLOOR_GB", "_agent_proc", "_agent_origin", "_agent_since_ms", "_stop_inflight",
             "bare_content_reads", "reel_content_reads", "_launcher_picture")

    def setUp(self):
        self.world = tempfile.mkdtemp(prefix="bare_hud_case_")
        self.addCleanup(shutil.rmtree, self.world, True)
        self.journal = os.path.join(self.world, "sessions.jsonl")
        self._env = {k: os.environ.get(k) for k in ("TV_HIST", "TV_SESSIONS", "TV_CAPTURE")}
        os.environ["TV_HIST"] = self.world
        os.environ["TV_SESSIONS"] = self.journal
        os.environ["TV_CAPTURE"] = "auto"
        self._saved = {k: getattr(ca, k) for k in self.STUBS}
        self._finders = (tv.find_d2r_window_mac, tv.find_d2r_window_win)
        self._grab = tv._capture_window_to_file
        self._real_reads = ca.bare_content_reads
        self.addCleanup(self._restore)
        self.now = int(time.time() * 1000)
        self.alive = False
        self.window = BARE
        self.reads = None
        self.starts, self.stops = [], []
        ca._shadow_state = lambda: {"on": True, "available": True, "recording": self.alive}
        ca._agent_alive = lambda: self.alive
        ca.mini_state = lambda: {"running": False}
        ca._shadow_now_ms = lambda: self.now
        ca._screen_recording_ok_quick = lambda: True
        ca.ON_AIR_FLOOR_GB = 0
        ca._mini_sid = lambda: "s_hud"
        ca._stop_inflight = False
        ca._agent_proc, ca._agent_origin, ca._agent_since_ms = None, "hand", None
        ca.start_agent = self._start
        ca.stop_agent = self._stop
        ca._force_kill_all_agents = lambda *a, **k: {"ok": True}
        ca.bare_content_reads = lambda: self.reads
        self.picture = None
        ca._launcher_picture = lambda pre: self.picture
        # REG-1704 - the whole reel's reads come from the same journal as its first reads, so they hold them. Left
        # unstubbed, the real reader answered [] for this fixture's reel while its first reads said "launcher" - a pair
        # the console can never see, which every launcher case here leaned on (the collapse the v3550 eye found).
        ca.reel_content_reads = lambda: self.reads
        tv.find_d2r_window_mac = lambda *a, **k: self.window
        tv.find_d2r_window_win = lambda *a, **k: self.window
        self.path = ca._shadow_watch_path()
        self.assertTrue(os.path.realpath(self.path).startswith(os.path.realpath(self.world) + os.sep),
                        "TV_HIST was not honoured (%s)" % self.path)
        self.assertEqual(os.path.realpath(ca._journal_path()), os.path.realpath(self.journal))

    def _restore(self):
        for k, v in self._saved.items():
            setattr(ca, k, v)
        tv.find_d2r_window_mac, tv.find_d2r_window_win = self._finders
        tv._capture_window_to_file = self._grab
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _start(self, *a, **k):
        self.starts.append(dict(k))
        ca._agent_proc = _Proc()
        ca._agent_origin = k.get("origin", "hand")
        ca._agent_since_ms = self.now
        self.alive = True
        return {"ok": True, "msg": "started", "origin": k.get("origin", "hand")}

    def _stop(self, *a, **k):
        self.stops.append(dict(k))
        self.alive = False
        return {"ok": True, "msg": "session saved · off"}

    def begin(self, origin):
        ca._agent_proc = _Proc()
        ca._agent_origin = origin
        ca._agent_since_ms = self.now
        self.alive = True

    def test_the_door_does_not_start_on_launcher_reads(self):
        self.reads = LAUNCH
        r = ca.shadow_watch_tick()
        self.assertFalse(r.get("started"), r)
        self.assertEqual(self.starts, [])
        self.assertIn("launcher", (r.get("why") or "").lower())
        self.assertIn("HUD", r.get("why") or "")

    def test_the_door_starts_when_the_first_reads_name_a_zone(self):
        self.reads = ZONE
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("started"), r)
        self.assertEqual(self.starts, [{"sim": False, "origin": "shadow"}])
        self.assertIn("D2R HUD word", r.get("why") or "")

    def test_no_reads_yet_still_starts_and_does_not_say_launcher(self):
        self.reads = None
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("started"), r)
        self.assertIn("not in yet", r.get("why") or "")
        self.assertNotIn("launcher", (r.get("why") or "").lower())

    def test_a_refused_launcher_waits_and_a_hud_read_opens_it(self):
        self.reads = LAUNCH
        ca.shadow_watch_tick()
        self.reads = None
        self.now += 1000
        r = ca.shadow_watch_tick()
        self.assertFalse(r.get("started"), r)
        self.assertEqual(self.starts, [])
        self.reads = ZONE
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("started"), r)
        self.assertIn("D2R HUD word", r.get("why") or "")

    def _sample(self, n):
        return bytes([n] * (ca._RELOOK_EDGE * ca._RELOOK_EDGE * 3)).hex()

    def on(self, plat):
        """#167 - this case is a console on `plat`: the real platform branch, never a faked picture."""
        saved = (sys.platform, ca.IS_WIN)

        def _back():
            sys.platform, ca.IS_WIN = saved
        self.addCleanup(_back)
        sys.platform, ca.IS_WIN = plat, plat.startswith("win")

    def _no_frame(self):
        """The real _launcher_picture over the grabber's answer on Windows (no Quartz, no sips, no screencapture)."""
        asked = []

        def _grab(wid, path, timeout=12):
            asked.append(wid)
            return False
        tv._capture_window_to_file = _grab
        ca._launcher_picture = self._saved["_launcher_picture"]
        return asked

    def _mac_camera(self):
        """The real _launcher_picture over a grabber that writes the grey this case shows."""
        from PIL import Image
        shots = []

        def _grab(wid, path, timeout=12):
            shots.append(wid)
            Image.new("RGB", (64, 40), (self.grey,) * 3).save(path, "JPEG")
            return True
        tv._capture_window_to_file = _grab
        ca._launcher_picture = self._saved["_launcher_picture"]
        return shots

    def test_the_wait_ends_without_a_frame_and_no_reel_opens(self):
        self.on("darwin")
        self.reads = LAUNCH
        ca.shadow_watch_tick()
        self.reads = None
        self.picture = None
        self.starts = []
        self.now += ca._BARE_HUD_RELOOK_S * 1000
        r = ca.shadow_watch_tick()
        self.assertFalse(r.get("started"), r)
        self.assertEqual(self.starts, [])
        self.assertIn("UNKNOWN", r.get("why") or "")

    def test_a_matching_relook_does_not_open_a_reel(self):
        self.on("darwin")
        self.picture = self._sample(40)
        self.reads = LAUNCH
        ca.shadow_watch_tick()
        self.reads = None
        self.starts = []
        self.now += ca._BARE_HUD_RELOOK_S * 1000
        r = ca.shadow_watch_tick()
        self.assertFalse(r.get("started"), r)
        self.assertEqual(self.starts, [])
        self.assertIn("matches the sealed launcher", r.get("why") or "")
        self.assertIn(str(ca._BARE_HUD_RELOOK_S), r.get("why") or "")
        stored = ca._shadow_watch_stored()
        self.assertGreaterEqual(stored.get("launcherUntil"), self.now + ca._BARE_HUD_RELOOK_S * 1000 - 1)

    def test_a_changed_picture_opens_one_reel(self):
        self.on("darwin")
        self.picture = self._sample(40)
        self.reads = LAUNCH
        ca.shadow_watch_tick()
        self.picture = self._sample(220)
        self.reads = None
        self.starts = []
        self.now += ca._BARE_HUD_RELOOK_S * 1000
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("started"), r)
        self.assertEqual(len(self.starts), 1)
        self.assertIn("differs from the sealed launcher", r.get("why") or "")

    def test_a_windows_pc_is_filmed_again_after_a_launcher_seal(self):
        # #167 - the ALT (Boosteroid) and Dean's PC (GeForce NOW). The relook waited for a frame only the Mac can take,
        # so after the first launcher seal no reel ever opened on either PC.
        self.on("win32")
        asked = self._no_frame()
        self.begin("shadow")
        self.reads = LAUNCH
        ca.shadow_watch_tick()
        self.now += (ca._SHADOW_AWAY_GRACE_S + 1) * 1000
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("cut"), r)
        self.reads = None            # no reel rolls now, so there are no reads
        self.now += 20 * 1000
        r = ca.shadow_watch_tick()
        self.assertFalse(r.get("started"), "the launcher wait opened a reel early: %r" % r)
        self.now += ca._BARE_HUD_RELOOK_S * 1000
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("started"), "after the launcher wait this Windows PC opened no reel: %r" % r)
        self.assertEqual(self.starts, [{"sim": False, "origin": "shadow"}])
        self.assertIn("films only inside a reel", r.get("why") or "")
        self.assertEqual(asked, [], "the Mac-only grabber was asked for a frame on Windows")
        self.assertIsNone(ca._shadow_watch_stored().get("launcherUntil"))

    def test_a_windows_launcher_verdict_keeps_no_picture_and_the_wait_still_ends(self):
        self.on("win32")
        asked = self._no_frame()
        self.reads = LAUNCH
        r = ca.shadow_watch_tick()
        self.assertFalse(r.get("started"), r)
        self.assertNotIn("launcherFrame", ca._shadow_watch_stored())
        self.reads = None
        self.now += ca._BARE_HUD_RELOOK_S * 1000
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("started"), r)
        self.assertEqual(asked, [], "the Mac-only grabber was asked for a frame on Windows")

    def test_a_mac_relook_takes_its_frame_through_the_real_picture(self):
        # the real _launcher_picture, so a name it cannot reach (the tempfile NameError) is a red here
        self.on("darwin")
        shots = self._mac_camera()
        self.grey = 40
        self.reads = LAUNCH
        ca.shadow_watch_tick()
        self.assertIsInstance(ca._shadow_watch_stored().get("launcherFrame"), str, "the launcher verdict kept no picture")
        self.reads = None
        self.now += ca._BARE_HUD_RELOOK_S * 1000
        r = ca.shadow_watch_tick()
        self.assertFalse(r.get("started"), r)
        self.assertIn("matches the sealed launcher", r.get("why") or "")
        self.grey = 220
        self.now += ca._BARE_HUD_RELOOK_S * 1000
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("started"), r)
        self.assertIn("differs from the sealed launcher", r.get("why") or "")
        self.assertEqual(shots, [BARE[0]] * 3)

    def test_a_frame_that_will_not_come_holds_the_door_one_wait_not_for_ever(self):
        self.on("darwin")
        asked = self._no_frame()
        self.reads = LAUNCH
        ca.shadow_watch_tick()
        self.reads = None
        self.now += ca._BARE_HUD_RELOOK_S * 1000
        r = ca.shadow_watch_tick()
        self.assertFalse(r.get("started"), r)
        self.assertIn("UNKNOWN", r.get("why") or "")
        self.now += (ca._BARE_HUD_RELOOK_S - 1) * 1000
        r = ca.shadow_watch_tick()
        self.assertFalse(r.get("started"), r)
        self.now += 1000
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("started"), "a frame that never comes held the door for ever: %r" % r)
        self.assertIn("could not be taken for another %d s" % ca._BARE_HUD_RELOOK_S, r.get("why") or "")
        self.assertEqual(len(self.starts), 1)
        self.assertEqual(len(asked), 4, "the Mac grabber was not asked on every look: %r" % asked)
        self.assertIsNone(ca._shadow_watch_stored().get("launcherUntil"))

    def test_a_look_that_raises_says_so_and_dates_no_look(self):
        # #167 - the relook's NameError was swallowed by the watch loop every 20 s, so the record said nothing
        class _Stop(BaseException):
            pass

        slept = []

        class _Clock(object):
            def __getattr__(self, n):
                return getattr(time, n)

            def sleep(self, s):
                slept.append(s)
                if len(slept) > 1:
                    raise _Stop()

        def _boom():
            raise NameError("name 'tempfile' is not defined")
        ca._shadow_watch_note(lookedAt=self.now - 5000, why="an earlier look")
        saved = (ca.time, ca.shadow_watch_tick, ca._lane_tick)
        ca.time, ca.shadow_watch_tick, ca._lane_tick = _Clock(), _boom, (lambda *a, **k: None)
        try:
            with self.assertRaises(_Stop):
                ca._shadow_watch_loop()
        finally:
            ca.time, ca.shadow_watch_tick, ca._lane_tick = saved
        st = ca._shadow_watch_stored()
        self.assertIn("raised NameError", st.get("why") or "", st)
        self.assertIn("UNKNOWN", st.get("why") or "")
        self.assertEqual(st.get("raisedAt"), self.now)
        self.assertEqual(st.get("lookedAt"), self.now - 5000, "a look that raised was dated as a look")

    def test_a_rolling_shadow_reel_seals_when_the_first_reads_lack_the_hud(self):
        # #148 HIS RULE: the launcher verdict waits the same 3 minutes as a gone game before it seals
        self.begin("shadow")
        self.reads = LAUNCH
        r = ca.shadow_watch_tick()
        self.assertFalse(r.get("cut"), "sealed on the first launcher look - his rule gives it %d s" % ca._SHADOW_AWAY_GRACE_S)
        self.assertTrue(r.get("launcher"), r)
        self.now += (ca._SHADOW_AWAY_GRACE_S - 1) * 1000
        r = ca.shadow_watch_tick()
        self.assertFalse(r.get("cut"), r)
        self.assertEqual(self.stops, [])
        self.now += 2000
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("cut"), r)
        self.assertEqual(self.stops, [{"farewell": False}])
        self.assertIn("no D2R zone, panel or item", r.get("why") or "")
        self.assertFalse(self.alive)

    def test_his_own_session_is_not_sealed_for_this(self):
        self.begin("hand")
        self.reads = LAUNCH
        r = ca.shadow_watch_tick()
        self.assertFalse(r.get("cut"), r)
        self.assertEqual(self.stops, [])
        self.assertTrue(self.alive)

    def test_a_window_that_names_the_game_does_not_need_the_check(self):
        self.window = GAME
        self.reads = LAUNCH
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("started"), r)
        self.assertIn("Diablo is on screen", r.get("why") or "")

    def test_the_journal_reader_keeps_this_sessions_first_reads(self):
        self.alive = True
        ca.bare_content_reads = self._real_reads
        rows = [
            {"sessionId": "s_other", "area": "Cold Plains", "scene": "town"},
            {"sessionId": "s_hud", "kind": "skip", "why": "boot"},
            {"sessionId": "s_hud", "area": "", "scene": "gameplay", "names": ["Play"]},
            {"sessionId": "s_hud", "area": "", "scene": "gameplay", "names": ["Library"]},
            {"sessionId": "s_hud", "area": "", "scene": "gameplay", "names": ["Boosteroid"]},
            {"sessionId": "s_hud", "area": "Cold Plains", "scene": "gameplay"},
        ]
        with io.open(self.journal, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
        got = ca.bare_content_reads()
        self.assertEqual([r.get("names") for r in got], [["Play"], ["Library"], ["Boosteroid"]])
        self.assertIs(tv.first_reads_show_d2r_hud(got, words=_words()), False)
        self.alive = False
        self.assertIsNone(ca.bare_content_reads())


RED_PROOF = [
    {
        "why": "REG-1603 - a read that failed (the ALT's signed-out Claude) counts as a look that saw no HUD again",
        "file": "tv_diablo.py",
        "find": '    if row.get("readFailed") or row.get("mode") in ("empty", "near-black"):\n        return False\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1603 - a near-black loading frame counts as a look again",
        "file": "tv_diablo.py",
        "find": '    if row.get("readFailed") or row.get("mode") in ("empty", "near-black"):\n',
        "replace": '    if row.get("readFailed") or row.get("mode") in ("empty",):\n',
        "matches": 1,
    },
    {
        "why": "a bare Boosteroid window starts a shadow reel when the first reads show no D2R HUD word",
        "file": "control_app.py",
        "find": "    if hud is False:   # bare Boosteroid, first reads have no D2R HUD word\n",
        "replace": "    if False:   # bare Boosteroid, first reads have no D2R HUD word\n",
        "matches": 1,
    },
    {
        "why": "a rolling shadow reel on the launcher is left filming",
        "file": "control_app.py",
        "find": "                if hud is False:   # a rolling shadow reel on the launcher\n",
        "replace": "                if False:   # a rolling shadow reel on the launcher\n",
        "matches": 1,
    },
    {
        "why": "the door judges the bare window with no zone names, so launcher reads read as unknown and it starts",
        "file": "control_app.py",
        "find": "    first = _tv.first_reads_show_d2r_hud(reads, words=set(_AREA_ACT), items=_game_items())\n",
        "replace": "    first = _tv.first_reads_show_d2r_hud(reads, words=set(), items=None)\n",
        "matches": 1,
    },
    {
        "why": "a zone name in the first read is no longer a HUD word, so the door never confirms the game",
        "file": "tv_diablo.py",
        "find": "        if needle and (\" \" + needle + \" \") in hay:\n",
        "replace": "        if False and (\" \" + needle + \" \") in hay:\n",
        "matches": 1,
    },
    {
        "why": "every window is put through the Boosteroid content check, so a titled game with launcher reads does not start",
        "file": "control_app.py",
        "find": "    if not _tv.label_is_bare_cloud(pre.get(\"windowLabel\") or \"\"):\n",
        "replace": "    if False and _tv.label_is_bare_cloud(pre.get(\"windowLabel\") or \"\"):\n",
        "matches": 1,
    },
    {
        "why": "a changed picture after the launcher wait opens no reel",
        "file": "control_app.py",
        "find": "    if same is False:\n",
        "replace": "    if False and same is False:\n",
        "matches": 1,
    },
    {
        "why": "a refused launcher opens another reel on the next look instead of waiting",
        "file": "control_app.py",
        "find": "    if hud is None and tv_label_is_bare(pre) and not _bare_relook_open(now):\n",
        "replace": "    if False and tv_label_is_bare(pre) and not _bare_relook_open(now):\n",
        "matches": 1,
    },
    {
        "why": "kai and intake rows count as the first reads, so a live game whose journal opens with them is called the launcher",
        "file": "tv_diablo.py",
        "find": "    return str(row.get(\"scene\") or \"\") in _HUD_SCENES\n",
        "replace": "    return bool(row.get(\"scene\"))\n",
        "matches": 1,
    },
    {
        "why": "#167 - every PC is said to have the Mac's camera, so a Windows relook asks the Mac-only grabber and waits",
        "file": "control_app.py",
        "find": "    return sys.platform == \"darwin\"\n",
        "replace": "    return True\n",
        "matches": 1,
    },
    {
        "why": "#167 - a Windows relook waits for a frame it can never take, so after a launcher seal no reel opens",
        "file": "control_app.py",
        "find": "    if not _launcher_camera_here():\n        # #167 \u2014 on Windows there is no camera outside a reel",
        "replace": "    if False:\n        # #167 \u2014 on Windows there is no camera outside a reel",
        "matches": 1,
    },
    {
        "why": "#167 - tempfile is a bare name again, so the Mac relook never takes its frame",
        "file": "control_app.py",
        "find": "        import tempfile as _tf\n        fd, path = _tf.mkstemp(",
        "replace": "        fd, path = tempfile.mkstemp(",
        "matches": 1,
    },
    {
        "why": "#167 - a frame that will not come holds the door for ever",
        "file": "control_app.py",
        "find": "    if isinstance(until, (int, float)) and now >= float(until) + _BARE_HUD_RELOOK_S * 1000:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "#167 - the watch loop swallows a look that raised, so the record keeps its last why",
        "file": "control_app.py",
        "find": "                _shadow_watch_note(raisedAt=_shadow_now_ms(),",
        "replace": "                (lambda **k: None)(raisedAt=_shadow_now_ms(),",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
