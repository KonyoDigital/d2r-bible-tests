# -*- coding: utf-8 -*-
"""REG-1760 — the create-game lobby names the character, citing the frame.

Measured 2026-10-03, draft decode at 1/4, on reel_s_1790978096994 (Session 3, 3 Oct 00:55-01:00):
  lobby  f_1790978100063  full sat 0.158 val 0.192, bot val 0.183, right sat 0.083
  loading f_1790978357205 full sat 0.094 val 0.085, bot val 0.000, right sat 0.014
  skill   f_1790978399206 full sat 0.177 val 0.255, bot val 0.229, right sat 0.116
  play    f_1790978250101 full sat 0.596 val 0.156, bot val 0.170, right sat 0.556
The other dark runs in that reel are loading cards. No character-panel frame was filmed, so this law
pins no pixel band for it. A reader that says c-panel still banks. The jpegs are not on CI; the tuples
are. Accuracy is the joiner against a reader answer, not a name written into the detector.

One lobby read per visit, on the same hourly cap as the character-select list, and the cap rewinds
onto the frame it did not read. The row is served on /api/chars_learned and painted in the in-game
section. One lobby frame does not teach the character.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable
enable()

import char_select as C  # noqa: E402

NODE = shutil.which("node")
LOBBY = (0.158, 0.192, 0.183, 0.083)
LOADING = (0.094, 0.085, 0.0, 0.014)
SKILL = (0.177, 0.255, 0.229, 0.116)
PLAY = (0.596, 0.156, 0.170, 0.556)
PROOF = "f_1790978100063.jpg"
# A reader of that plaque. The detector never sees this. _clean_name titles an all-caps name.
PLAQUE = {"screen": "lobby", "name": "KONYOSSIN", "cls": "Assassin", "level": 90}


def _js_fn(src, sig):
    """The function whose header is the one occurrence of sig, bounded by its own braces."""
    n = src.count(sig)
    if n != 1:
        raise AssertionError("%r occurs %d times" % (sig, n))
    i = src.index(sig)
    b = src.index("{", i)
    depth = 0
    j = b
    while j < len(src):
        c = src[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[i:j + 1]
        j += 1
    raise AssertionError("could not bound %r" % sig)


class TheLobbyBands(unittest.TestCase):
    def test_the_measured_lobby_passes_and_the_screens_beside_it_do_not(self):
        ok, why = C.looks_like_lobby(LOBBY)
        self.assertTrue(ok, why)
        for tag, st in (("loading", LOADING), ("skill tree", SKILL), ("play", PLAY)):
            ok, why = C.looks_like_lobby(st)
            self.assertFalse(ok, "%s passed: %s" % (tag, why))
        self.assertEqual(C.looks_like_lobby(None), (False, "frame unreadable"))

    def test_there_is_no_character_panel_pixel_band(self):
        self.assertFalse(hasattr(C, "looks_like_c_panel"),
                         "a character-panel detector was added without a measured frame")

    def test_a_flat_plaque_passes_and_a_saturated_frame_does_not_and_garbage_is_unreadable(self):
        from PIL import Image
        d = tempfile.mkdtemp(prefix="lobby_px_")
        try:
            def flat(name, s, v):
                im = Image.new("HSV", (320, 200), (0, int(s * 255), int(v * 255)))
                p = os.path.join(d, name)
                im.convert("RGB").save(p, quality=95)
                return p
            yes = C.lobby_stats(flat("f_yes.jpg", 0.05, 0.19))
            no = C.lobby_stats(flat("f_no.jpg", 0.80, 0.50))
            self.assertTrue(C.looks_like_lobby(yes)[0], yes)
            self.assertFalse(C.looks_like_lobby(no)[0], no)
            junk = os.path.join(d, "f_junk.jpg")
            with open(junk, "wb") as fh:
                fh.write(b"no")
            self.assertIsNone(C.lobby_stats(junk))
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TheSurfaceAnswer(unittest.TestCase):
    def test_the_plaque_answer_is_the_character_and_another_screen_banks_nothing(self):
        row, why = C.surface_of(PLAQUE)
        self.assertEqual(why, "one witness")
        self.assertEqual((row["name"], row["key"], row["cls"], row["level"], row["kind"]),
                         ("Konyossin", "konyossin", "Assassin", 90, "lobby"))
        other, owhy = C.surface_of({"screen": "other", "name": "KONYOSSIN", "cls": "Assassin", "level": 90})
        self.assertIsNone(other, "a gameplay misread was banked")
        self.assertEqual(owhy, "other screen")
        panel, _pwhy = C.surface_of({"screen": "c-panel", "name": "KONYOSSIN", "cls": "Assassin", "level": 90})
        self.assertEqual(panel["kind"], "c-panel")
        self.assertIsNone(C.surface_of({"note": "not read - subscription cap"})[0])
        self.assertIsNone(C.surface_of(None)[0])

    def test_one_image_is_one_row_and_the_two_kinds_add(self):
        d = C._empty()
        lobby, _w = C.surface_of(PLAQUE)
        C.bank_surface(d, lobby, PROOF, 1790978100063)
        C.bank_surface(d, lobby, PROOF, 1790978100063)
        ws = C.surface_witnesses(d)
        self.assertEqual(len(ws), 1, ws)
        self.assertEqual((ws[0]["image"], ws[0]["confluence"], ws[0]["name"]), (PROOF, 1.0, "Konyossin"))
        panel, _p = C.surface_of({"screen": "c-panel", "name": "KONYOSSIN", "cls": "Assassin", "level": 90})
        C.bank_surface(d, panel, "f_panel.jpg", 1790978200000)
        both = C.surface_witnesses(d)
        self.assertEqual(sorted(w["kind"] for w in both), ["c-panel", "lobby"])
        self.assertEqual({w["confluence"] for w in both}, {2.0})
        self.assertEqual(C.surface_confluence([{"kind": "lobby"}, {"kind": "snow"}]), 1.0)
        self.assertEqual(C.learned(d), [], "a surface witness taught a character")

    def test_a_witness_does_not_move_a_level_the_list_already_taught(self):
        d = C._empty()
        row = {"name": "Konyossin", "key": "konyossin", "cls": "Assassin", "level": 90, "title": None}
        C.record(d, "v1", [row], {"ts": 1})
        C.record(d, "v2", [row], {"ts": 2})
        lobby, _w = C.surface_of(PLAQUE)
        C.bank_surface(d, lobby, PROOF, 5)
        got = C.learned(d)[0]
        self.assertEqual((got["level"], got["visits"]), (90, 2))
        self.assertEqual(d["chars"]["konyossin"]["visitLevel"], {"v1": 90, "v2": 90})


class _Reel(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="lobby_tick_")
        self.hist = os.path.join(self.tmp, "hist")
        self.store = os.path.join(self.tmp, "roster.json")
        os.environ["TV_CHARS_LEARNED"] = self.store
        self.called = []

    def tearDown(self):
        os.environ.pop("TV_CHARS_LEARNED", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _reel(self, frames):
        rd = os.path.join(self.hist, "reel_s_1500000000001_12001")
        os.makedirs(rd, exist_ok=True)
        for ts in frames:
            with open(os.path.join(rd, "f_%d.jpg" % ts), "wb") as fh:
                fh.write(b"no")
        return rd

    def _tick(self, stats_of, reader, **kw):
        return C.tick(root=self.hist, stats=lambda p: (0.9, 0.1, 0.9, 0.1),
                      reader=lambda crop: {"screen": "other"},
                      surface_stats=stats_of, surface_reader=reader,
                      now=kw.pop("now", 1000000.0), **kw)

    def test_one_lobby_visit_is_one_read_and_it_cites_the_frame(self):
        base = 1790978100063
        self._reel([base, base + 1000, base + 2000])

        def reader(p):
            self.called.append(os.path.basename(p))
            return dict(PLAQUE)

        r = self._tick(lambda p: LOBBY, reader)
        self.assertTrue(r["ok"], r)
        self.assertEqual(self.called, [PROOF])
        self.assertEqual(r["surfaces"], 1)
        ws = C.surface_witnesses(C.load())
        self.assertEqual([(w["name"], w["cls"], w["level"], w["image"], w["kind"]) for w in ws],
                         [("Konyossin", "Assassin", 90, PROOF, "lobby")])
        self.assertEqual(C.learned(C.load()), [])
        again = self._tick(lambda p: LOBBY, reader)
        self.assertEqual(again["reads"], 0, "the same lobby visit was read again")

    def test_a_frame_that_is_not_the_lobby_is_not_read(self):
        self._reel([1790978250101])

        def reader(p):
            self.called.append(p)
            return dict(PLAQUE)

        r = self._tick(lambda p: PLAY, reader)
        self.assertEqual(self.called, [])
        self.assertEqual(r["reads"], 0)
        self.assertEqual(C.surface_witnesses(C.load()), [])

    def test_another_screen_spends_the_read_and_banks_nothing(self):
        self._reel([1790978100063])
        r = self._tick(lambda p: LOBBY, lambda p: {"screen": "other", "name": "KONYOSSIN"})
        self.assertEqual(r["reads"], 1)
        self.assertEqual(r["surfaces"], 0)
        self.assertEqual(C.surface_witnesses(C.load()), [])
        self.assertEqual(C.load()["stats"]["refused"], 0)

    def test_a_read_that_did_not_happen_is_tried_on_the_next_pass(self):
        self._reel([1790978100063])
        answers = [{"note": "the reader returned nothing"}, dict(PLAQUE)]

        def reader(p):
            self.called.append(os.path.basename(p))
            return answers.pop(0)

        r = self._tick(lambda p: LOBBY, reader)
        self.assertEqual(r["reads"], 0)
        self.assertEqual(r["surfaces"], 0)
        self.assertIn("surface not read", r["why"])
        d = C.load()
        self.assertEqual(d["stats"]["refused"], 0)
        self.assertEqual(d["stats"]["reads"], 0)
        self.assertEqual(d["reels"]["reel_s_1500000000001_12001"]["lobby"]["reads"], 0)
        self.assertGreater(C.owed(d, self.hist), 0)
        self.assertEqual(C.surface_witnesses(d), [])
        again = self._tick(lambda p: LOBBY, reader)
        self.assertEqual(again["surfaces"], 1)
        self.assertEqual(self.called, [PROOF, PROOF])
        self.assertEqual(C.surface_witnesses(C.load())[0]["name"], "Konyossin")

    def test_a_timeout_spends_the_hourly_cap_and_a_throttle_does_not(self):
        self._reel([1790978100063])
        name = "reel_s_1500000000001_12001"

        def nothing(p):
            self.called.append(os.path.basename(p))
            return {"note": "the reader returned nothing"}

        for _ in range(C.READS_PER_HOUR):
            self._tick(lambda p: LOBBY, nothing)
        self.assertEqual(len(self.called), C.READS_PER_HOUR)
        d = C.load()
        self.assertEqual(len(d["stats"]["readTs"]), C.READS_PER_HOUR)
        self.assertEqual(d["stats"]["reads"], 0)
        self.assertEqual(d["reels"][name]["lobby"]["reads"], 0)
        stopped = self._tick(lambda p: LOBBY, nothing)
        self.assertIn("hourly read cap", stopped["why"])
        self.assertEqual(len(self.called), C.READS_PER_HOUR, "the cap asked the reader again")
        self.assertGreater(C.owed(C.load(), self.hist), 0)

        self.called = []
        os.environ["TV_CHARS_LEARNED"] = os.path.join(self.tmp, "throttle.json")

        def throttled(p):
            self.called.append(os.path.basename(p))
            return {"note": "reader throttled - not read"}

        for _ in range(3):
            self._tick(lambda p: LOBBY, throttled)
        t = C.load()
        self.assertEqual(t["stats"]["readTs"], [])
        self.assertEqual(t["reels"][name]["lobby"]["reads"], 0)
        self.assertEqual(len(self.called), 3)

    def test_an_answer_that_cannot_be_used_is_refused_and_not_retried(self):
        self._reel([1790978100063])

        def reader(p):
            self.called.append(os.path.basename(p))
            return [1, 2]

        r = self._tick(lambda p: LOBBY, reader)
        self.assertEqual(r["reads"], 0)
        self.assertEqual(C.load()["stats"]["refused"], 1)
        self.assertEqual(C.load()["reels"]["reel_s_1500000000001_12001"]["lobby"]["reads"], 1)
        self._tick(lambda p: LOBBY, reader)
        self.assertEqual(self.called, [PROOF])

    def test_the_hourly_cap_leaves_the_unread_lobby_frame_owed(self):
        base = 1790978100000
        # nine lobby visits, a hundred seconds apart: the ninth meets the cap
        self._reel([base + n * 100000 for n in range(C.READS_PER_HOUR + 1)])

        def reader(p):
            self.called.append(os.path.basename(p))
            return dict(PLAQUE)

        r = self._tick(lambda p: LOBBY, reader)
        self.assertEqual(r["reads"], C.READS_PER_HOUR)
        self.assertIn("hourly read cap", r["why"])
        d = C.load()
        name = "reel_s_1500000000001_12001"
        self.assertLess(d["reels"][name]["pos"], C.READS_PER_HOUR + 1,
                        "the cap walked past the lobby frame it did not read")
        self.assertGreater(C.owed(d, self.hist), 0)
        self.assertEqual(len(C.surface_witnesses(d)), C.READS_PER_HOUR)
        later = self._tick(lambda p: LOBBY, reader, now=1000000.0 + 3601)
        self.assertGreater(later["reads"], 0, "the next hour did not read the lobby frame the cap held")
        self.assertEqual(len(C.surface_witnesses(C.load())), C.READS_PER_HOUR + 1)


class TheRoutePaintsTheRow(unittest.TestCase):
    def test_the_chars_route_returns_the_rows_and_the_in_game_section_paints_them(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            app = fh.read()
        self.assertEqual(app.count('"surfaceWitnesses": _cs.surface_witnesses(_d)'), 1)
        self.assertEqual(app.count('"gear": _gear, "gearWhy": _gwhy})'), 1,
                         "the gear line the card test reads was moved")
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            page = fh.read()
        self.assertEqual(page.count("function _surfaceWitnessHtml()"), 1)
        ing = page.index('data-sec="ingame"')
        sim = page.index('data-sec="sim"', ing)
        call = page.index("_surfaceWitnessHtml()", ing)
        self.assertLess(call, sim, "the in-game section does not paint the witness rows")
        fn = _js_fn(page, "function _surfaceWitnessHtml()")
        self.assertIn("surfaceWitnesses", fn)
        if not NODE:
            self.skipTest("node is required to run the page function")
        learned = {"ok": True, "surfaceWitnesses": [{
            "name": "Konyossin", "cls": "Assassin", "level": 90, "kind": "lobby",
            "image": PROOF, "confluence": 1.0}]}
        out = _paint(fn, learned)
        self.assertIn('data-kind="lobby"', out)
        self.assertIn('data-image="%s"' % PROOF, out)
        self.assertIn("Konyossin", out)
        self.assertIn("confluence 1", out)
        self.assertEqual(_paint(fn, {"ok": True, "surfaceWitnesses": []}), "")
        self.assertEqual(_paint(fn, {"ok": True, "chars": []}), "")
        self.assertEqual(_paint(fn, {"ok": False, "surfaceWitnesses": None}), "")
        self.assertEqual(_paint(fn, {"ok": True, "surfaceWitnesses": [
            {"name": "Konyossin", "kind": "lobby"}]}), "")

    def test_the_list_prompt_still_refuses_a_frame_that_is_not_the_list(self):
        with io.open(os.path.join(HERE, "tv_diablo.py"), encoding="utf-8") as fh:
            src = fh.read()
        a = src.index("CHARSEL_READ_PROMPT = (")
        b = src.index("SURFACE_READ_PROMPT = (", a)
        c = src.index("def surface_read(", b)
        charsel = src[a:b]
        surface = src[b:c]
        self.assertIn('{"screen":"other","chars":[]}', charsel)
        self.assertNotIn("c-panel", charsel)
        self.assertIn('{"screen":"lobby"', surface)
        self.assertIn('{"screen":"c-panel"', surface)
        self.assertIn('{"screen":"other"}', surface)


def _paint(fn, learned):
    drv = (
        "function esc(s){ return String(s == null ? '' : s); }\n"
        "var window = { _cbLearnedNow: function(){ return LEARNED; } };\n"
        "var LEARNED = %s;\n"
        "%s\n"
        "process.stdout.write(_surfaceWitnessHtml());\n"
    ) % (json.dumps(learned), fn)
    r = subprocess.run([NODE, "-"], input=drv, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError(r.stderr[-500:] or r.stdout[-500:])
    return r.stdout


RED_PROOF = [
    {
        "why": "REG-1760 - the loading card passes the lobby bands once val and the bottom strip are not required",
        "file": "tv/char_select.py",
        "find": "    ok = (fs < LOBBY_FULL_SAT_MAX and LOBBY_FULL_VAL[0] < fv < LOBBY_FULL_VAL[1]\n"
                "          and bv > LOBBY_BOT_VAL_MIN and rs < LOBBY_RIGHT_SAT_MAX)\n",
        "replace": "    ok = (fs < LOBBY_FULL_SAT_MAX and rs < LOBBY_RIGHT_SAT_MAX)\n",
        "matches": 1,
    },
    {
        "why": "REG-1760 - a frame the reader called another screen is banked as the lobby",
        "file": "tv/char_select.py",
        "find": "    if not kind:\n        return None, \"other screen\"\n",
        "replace": "    if not kind:\n        kind = \"lobby\"\n",
        "matches": 1,
    },
    {
        "why": "REG-1760 - banking the same frame twice stores two rows",
        "file": "tv/char_select.py",
        "find": "        if isinstance(w, dict) and w.get(\"kind\") == kind and w.get(\"image\") == image:\n"
                "            return w\n",
        "replace": "        if False and isinstance(w, dict) and w.get(\"kind\") == kind and w.get(\"image\") == image:\n"
                   "            return w\n",
        "matches": 1,
    },
    {
        "why": "REG-1760 - the hourly cap walks the cursor past the lobby frame it did not read",
        "file": "tv/char_select.py",
        "find": "def _rewind_unread(rs, i):\n"
                "    \"\"\"The frame was not read. The cursor waits on it.\"\"\"\n"
                "    rs[\"pos\"] = i - SAMPLE_EVERY\n",
        "replace": "def _rewind_unread(rs, i):\n"
                   "    \"\"\"The frame was not read. The cursor waits on it.\"\"\"\n"
                   "    return\n",
        "matches": 1,
    },
    {
        "why": "REG-1761 - a lobby read that did not happen is kept and never retried",
        "file": "tv/char_select.py",
        "find": "                            if _surface_unread(raw):\n"
                "                                if _surface_call_was_spent(raw):\n"
                "                                    st[\"readTs\"].append(now_s)\n"
                "                                _rewind_unread(rs, i)\n"
                "                                why = \"surface not read: \" + rwhy\n"
                "                                break\n",
        "replace": "                            if False and _surface_unread(raw):\n"
                   "                                if _surface_call_was_spent(raw):\n"
                   "                                    st[\"readTs\"].append(now_s)\n"
                   "                                _rewind_unread(rs, i)\n"
                   "                                why = \"surface not read: \" + rwhy\n"
                   "                                break\n",
        "matches": 1,
    },
    {
        "why": "REG-1762 - a lobby timeout retries forever and never spends the hourly cap",
        "file": "tv/char_select.py",
        "find": "                            if _surface_unread(raw):\n"
                "                                if _surface_call_was_spent(raw):\n"
                "                                    st[\"readTs\"].append(now_s)\n"
                "                                _rewind_unread(rs, i)\n",
        "replace": "                            if _surface_unread(raw):\n"
                   "                                if False and _surface_call_was_spent(raw):\n"
                   "                                    st[\"readTs\"].append(now_s)\n"
                   "                                _rewind_unread(rs, i)\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
