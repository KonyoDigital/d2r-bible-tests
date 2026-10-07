# -*- coding: utf-8 -*-
"""REG-1941 - A READ THAT DID NOT HAPPEN IS BOUNDED, SAID, AND NEVER AN EXCEPTION OUT OF THE TICK.

The #231 cross-family eye (Claude CLI) on v3574 and v3575, char_select's paid lobby reads. MEASURED against the
shipped tick before this fix, on a fake reel of one four-frame lobby visit:
  · one frame that always came back with a note (a stub with no answer, a reader that returns nothing) held its reel
    for ever: 12 ticks asked the SAME frame 12 times, pos stayed 0 of 4, owed() stayed 4 - _rewind_unread had no limit;
  · under BOTH, Claude's call timed out and the Grok backup failed, so tv_diablo.surface_read's note was the backup's own
    words ("backup: claude timed out - Grok is not installed on this PC"), not "the reader returned nothing": 20 ticks
    made 20 paid Claude calls and spent 0 hourly slots - the spend was decided by matching one string across modules;
  · the gate staying busy for the whole wait made NO call and still read as spent;
  · a reader that raised subprocess.TimeoutExpired escaped tick() (try/finally only): no ledger was written at all;
  · a lobby stop broke one reel's loop and the scan went on into the next reel with the reason already set.

Now: the reader says whether it was asked (`asked`) and whether it simply cannot be asked now (`later`); a lobby frame
that fails LOBBY_TRIES_PER_FRAME times for a reason that is not "later" is passed and said; the reader door (_ask)
turns a raise into a read that did not happen; any stop ends the whole scan. DRIVEN: char_select.tick on throwaway
reels, and tv_diablo.surface_read through the real _oneshot with only the CLI calls patched. RED_PROOF below.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

_WORLD = tempfile.mkdtemp(prefix="read_bounded_")
os.environ["TV_HIST"] = _WORLD
os.environ["TV_SESSIONS"] = os.path.join(_WORLD, "sessions.jsonl")
os.environ["G5_STATS_PATH"] = os.path.join(_WORLD, "g5_stats.json")   # a backup count never reaches his file
os.environ.pop("TV_STUB", None)

import char_select as C  # noqa: E402

LOBBY = (0.158, 0.192, 0.183, 0.083)     # the measured lobby tuple (test_the_lobby_names_the_character)
PLAQUE = {"screen": "lobby", "name": "KONYOSSIN", "cls": "Assassin", "level": 90}
REEL = "reel_s_1500000000001_12001"
BASE = 1790978100063


class _Ticks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="read_bounded_tick_")
        self.hist = os.path.join(self.tmp, "hist")
        os.environ["TV_CHARS_LEARNED"] = os.path.join(self.tmp, "roster.json")
        self.asked = []

    def tearDown(self):
        os.environ.pop("TV_CHARS_LEARNED", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _reel(self, name=REEL, frames=(BASE, BASE + 1000, BASE + 2000, BASE + 3000)):
        rd = os.path.join(self.hist, name)
        os.makedirs(rd, exist_ok=True)
        for ts in frames:
            with open(os.path.join(rd, "f_%d.jpg" % ts), "wb") as fh:
                fh.write(b"no")
        return rd

    def _tick(self, surface_reader, k=0, stats=None, reader=None, surface_stats=None, step=45):
        return C.tick(root=self.hist, stats=stats or (lambda p: (0.9, 0.1, 0.9, 0.1)),
                      reader=reader or (lambda crop: {"screen": "other"}),
                      surface_stats=surface_stats or (lambda p: LOBBY), surface_reader=surface_reader,
                      now=1000000.0 + step * k)

    def _noting(self, note):
        def reader(p):
            self.asked.append(os.path.basename(p))
            return dict(note)
        return reader


class AFrameThatKeepsFailingIsPassed(_Ticks):

    def test_a_frame_note_is_tried_a_bounded_number_of_times_then_passed_and_said(self):
        self._reel()
        first = "f_%d.jpg" % BASE
        reader = self._noting({"note": "stub has no #surface answer", "asked": False, "later": False})
        for k in range(C.LOBBY_TRIES_PER_FRAME):
            self._tick(reader, k)
        self.assertEqual([first] * C.LOBBY_TRIES_PER_FRAME, self.asked[:C.LOBBY_TRIES_PER_FRAME],
                         "the frame was not the one retried")
        d = C.load()
        self.assertGreater(int(d["reels"][REEL]["pos"]), 0, "one bad frame still holds its reel")
        self.assertEqual(1, d["stats"].get("lobbyPassed"), "the passed frame was not counted")
        said = d["stats"].get("lobbyPassedLast") or {}
        self.assertEqual(first, said.get("frame"), "the passed frame is not named")
        self.assertEqual(REEL, said.get("reel"))
        self.assertIn("stub has no #surface answer", said.get("why") or "", "the pass does not say why")
        s = C.status(self.hist)
        self.assertEqual(1, s.get("lobbyPassed"), "the lane's status does not say a frame was passed")
        self.assertIn("f_%d.jpg" % (BASE + 1000), self.asked, "the next frame of the same visit was never asked")
        self.assertEqual(0, d["reels"][REEL]["lobby"]["reads"], "a passed frame was counted as the visit's read")

    def test_a_reel_whose_every_frame_keeps_failing_still_finishes(self):
        self._reel()
        reader = self._noting({"note": "the reader returned nothing", "asked": True, "later": False})
        for k in range(12):
            self._tick(reader, k, step=3601)      # a fresh hour each tick: the cap is not what moves the reel
        d = C.load()
        self.assertEqual(4, int(d["reels"][REEL]["pos"]), "the reel never finished")
        self.assertEqual(0, C.owed(d, self.hist))
        self.assertEqual(4 * C.LOBBY_TRIES_PER_FRAME, len(self.asked), "a frame was asked past (or short of) its bound")
        self.assertEqual(4, d["stats"].get("lobbyPassed"))

    def test_the_hourly_cap_still_holds_while_frames_are_passed(self):
        self._reel()
        reader = self._noting({"note": "the reader returned nothing", "asked": True, "later": False})
        for k in range(12):
            self._tick(reader, k)
        d = C.load()
        self.assertEqual(C.READS_PER_HOUR, len(self.asked), "passing a frame bought paid calls past the hourly cap")
        self.assertEqual(C.READS_PER_HOUR, len(d["stats"]["readTs"]))

    def test_a_good_answer_after_a_miss_starts_the_count_again(self):
        self._reel(frames=(BASE,))
        answers = [{"note": "the reader returned nothing", "asked": True}, dict(PLAQUE)]
        r1 = self._tick(lambda p: answers.pop(0), 0)
        self.assertIn("surface not read", r1["why"])
        self._tick(lambda p: dict(PLAQUE), 1)
        d = C.load()
        self.assertNotIn("lobbyTry", d["reels"][REEL], "a frame that was read kept its miss count")
        self.assertEqual("Konyossin", C.surface_witnesses(d)[0]["name"])

    def test_a_throttle_never_passes_a_frame(self):
        self._reel(frames=(BASE,))
        reader = self._noting({"note": "reader throttled - not read", "asked": False, "later": True})
        for k in range(C.LOBBY_TRIES_PER_FRAME * 3):
            self._tick(reader, k)
        d = C.load()
        self.assertEqual(0, int(d["reels"][REEL]["pos"]), "a throttle walked the cursor past a lobby frame it never read")
        self.assertFalse(d["stats"].get("lobbyPassed"), "a throttle passed a frame")
        self.assertEqual([], d["stats"]["readTs"], "a throttle spent an hourly slot")

    def test_premise_an_old_reader_that_does_not_say_later_is_judged_by_its_words(self):
        self.assertTrue(C._surface_later({"note": "reader throttled - not read"}))
        self.assertTrue(C._surface_later({"note": "not read - 250/250 this hour"}))
        self.assertFalse(C._surface_later({"note": "no such frame"}))


class TheSpendIsWhatTheReaderSays(unittest.TestCase):

    def test_asked_decides_the_spend_whatever_the_note_says(self):
        self.assertTrue(C._surface_call_was_spent(
            {"note": "backup: claude timed out - Grok is not installed on this PC", "asked": True}),
            "a Claude call that ran under BOTH was not counted (its note is the backup's words)")
        self.assertFalse(C._surface_call_was_spent({"note": "the reader returned nothing", "asked": False}),
                         "a read that was never asked spent an hourly slot")
        self.assertTrue(C._surface_call_was_spent({"note": "the reader returned nothing"}),
                        "the fallback for a reader that does not say was lost")


class TheReaderDoorNeverRaises(_Ticks):

    def test_a_lobby_reader_that_times_out_is_a_spent_read_that_did_not_happen_and_the_ledger_is_saved(self):
        self._reel(frames=(BASE,))

        def raises(p):
            self.asked.append(p)
            raise subprocess.TimeoutExpired(["claude"], 120)
        r = self._tick(raises)
        self.assertTrue(r["ok"], r)
        self.assertIn("TimeoutExpired", r["why"])
        d = C.load()
        self.assertIsNotNone(d, "the tick wrote no ledger")
        self.assertEqual(1, d["stats"]["ticks"])
        self.assertEqual(1, len(d["stats"]["readTs"]), "a call that ran until its timeout spent no slot")
        self.assertEqual(0, int(d["reels"][REEL]["pos"]), "the frame the timeout did not read was walked past")

    def test_a_reader_that_cannot_start_spends_nothing(self):
        self._reel(frames=(BASE,))

        def missing(p):
            raise FileNotFoundError("claude")
        r = self._tick(missing)
        self.assertTrue(r["ok"], r)
        self.assertEqual([], C.load()["stats"]["readTs"])

    def test_a_list_reader_that_raises_is_a_refusal_and_the_ledger_is_saved(self):
        self._reel(frames=(BASE,))

        def raises(crop):
            raise subprocess.TimeoutExpired(["claude"], 120)
        with mock.patch.object(C, "panel_crop", lambda p, work: p):
            r = self._tick(lambda p: dict(PLAQUE), stats=lambda p: (0.05, 0.35, 0.10, 0.20), reader=raises)
        self.assertTrue(r["ok"], r)
        d = C.load()
        self.assertEqual(1, d["stats"]["refused"], "a list read that raised was not counted as refused")
        self.assertIn("TimeoutExpired", d["stats"]["lastWhy"])

    def test_premise_the_list_band_is_what_the_stats_above_say(self):
        self.assertTrue(C.looks_like_char_select((0.05, 0.35, 0.10, 0.20))[0])


class AStopEndsTheWholeScan(_Ticks):

    def test_a_lobby_read_that_did_not_happen_does_not_go_on_into_the_next_reel(self):
        self._reel(name="reel_s_1500000000002_12002", frames=(BASE + 10 ** 7,))   # newest: scanned first
        self._reel(name=REEL, frames=(BASE,))
        listed = []

        def list_reader(crop):
            listed.append(crop)
            return {"note": "reader throttled - not read"}

        def stats(p):
            return (0.9, 0.1, 0.9, 0.1) if "12002" in p else (0.05, 0.35, 0.10, 0.20)
        with mock.patch.object(C, "panel_crop", lambda p, work: p):
            r = self._tick(lambda p: {"note": "reader throttled - not read", "later": True}, stats=stats,
                           reader=list_reader)
        self.assertIn("surface not read", r["why"], "the first failure's reason was overwritten")
        self.assertEqual([], listed, "the scan went on into the next reel after the lobby read did not happen")
        self.assertEqual(0, int(C.load()["reels"].get(REEL, {}).get("pos") or 0))


import tv_diablo as tv  # noqa: E402
import g5_grok_eyes as g5  # noqa: E402


class TheNoteSaysWhetherTheReaderWasAsked(unittest.TestCase):
    """tv_diablo.surface_read through the real _oneshot; only the CLI calls are patched."""

    def setUp(self):
        self.pic = os.path.join(_WORLD, "f_1790978100063.jpg")
        with open(self.pic, "wb") as fh:
            fh.write(b"x")

    def _common(self, choice):
        return [mock.patch.object(tv, "_reader_choice", lambda: choice),
                mock.patch.object(tv, "_is_throttled", lambda: False),
                mock.patch.object(tv, "_sub_budget_check", lambda kind="vision": None),
                mock.patch.object(tv, "_claude_lane_skip_why", lambda: None),
                mock.patch.object(tv, "journal_skip", lambda *a, **k: None),
                mock.patch.object(tv, "ev", lambda *a, **k: None)]

    def _run(self, choice, *extra):
        ps = self._common(choice) + list(extra)
        for p in ps:
            p.start()
        try:
            return tv.surface_read(self.pic, timeout=1)
        finally:
            for p in reversed(ps):
                p.stop()

    def test_both_with_a_claude_timeout_and_no_grok_is_asked(self):
        def inner(*a, **k):
            raise subprocess.TimeoutExpired(["claude"], 1)
        raw = self._run("both", mock.patch.object(tv, "_oneshot_inner", inner),
                        mock.patch.object(g5, "_grok_bin", lambda: None),
                        mock.patch.object(g5, "note_backup", lambda why: None))
        self.assertNotEqual("the reader returned nothing", raw.get("note"), "premise: the BOTH note is the backup's")
        self.assertTrue(raw.get("asked"), raw)
        self.assertTrue(C._surface_call_was_spent(raw))

    def test_a_gate_that_stayed_busy_asked_nobody(self):
        raw = self._run("claude", mock.patch.object(tv._ONESHOT_GATE, "acquire", lambda timeout=None: False))
        self.assertEqual("the reader returned nothing", raw.get("note"))
        self.assertFalse(raw.get("asked"), "a read nobody was asked for spent an hourly slot")
        self.assertFalse(C._surface_call_was_spent(raw))

    def test_claude_called_and_empty_is_asked(self):
        raw = self._run("claude", mock.patch.object(tv, "_oneshot_inner", lambda *a, **k: None))
        self.assertTrue(raw.get("asked"), raw)

    def test_grok_only_blocked_asked_nobody(self):
        raw = self._run("grok", mock.patch.object(g5, "grok_only_blocked_why", lambda: "Grok is signed out"))
        self.assertFalse(raw.get("asked"), raw)

    def test_a_throttle_is_later_and_not_asked(self):
        ps = self._common("claude")
        for p in ps:
            p.start()
        try:
            with mock.patch.object(tv, "_is_throttled", lambda: True):
                raw = tv.surface_read(self.pic, timeout=1)
        finally:
            for p in reversed(ps):
                p.stop()
        self.assertTrue(raw.get("later"), raw)
        self.assertFalse(raw.get("asked"), raw)


def tearDownModule():
    shutil.rmtree(_WORLD, ignore_errors=True)


RED_PROOF = [
    {
        "why": "REG-1941 - one lobby frame that keeps failing holds its reel for ever again (no per-frame bound)",
        "file": "tv/char_select.py",
        "find": "                if not _surface_later(raw) and _lobby_tries(rs, p) >= LOBBY_TRIES_PER_FRAME:\n",
        "replace": "                if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-1941 - a throttle counts toward passing a frame, so a long throttle walks past lobby frames unread",
        "file": "tv/char_select.py",
        "find": "    if \"later\" in raw:\n        return bool(raw.get(\"later\"))\n",
        "replace": "    if \"later\" in raw:\n        return False\n",
        "matches": 1,
    },
    {
        "why": "REG-1941 - the spend is a string match again: a BOTH timeout is re-asked, paid, on every tick",
        "file": "tv/char_select.py",
        "find": "    if isinstance(raw, dict) and \"asked\" in raw:\n        return bool(raw.get(\"asked\"))\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1941 - a lobby reader that raises escapes the tick and no ledger is written",
        "file": "tv/char_select.py",
        "find": "            raw = _ask(surface_reader, p)\n",
        "replace": "            raw = surface_reader(p)\n",
        "matches": 1,
    },
    {
        "why": "REG-1941 - a list reader that raises escapes the tick and no ledger is written",
        "file": "tv/char_select.py",
        "find": "                raw = _ask(reader, crop)\n",
        "replace": "                raw = reader(crop)\n",
        "matches": 1,
    },
    {
        "why": "REG-1941 - only the budget and the cap end the scan; a lobby stop goes on into the next reel",
        "file": "tv/char_select.py",
        "find": "            if why:\n                break\n",
        "replace": "            if why == \"tick budget spent\" or why.startswith(\"hourly read cap\"):\n                break\n",
        "matches": 1,
    },
    {
        "why": "REG-1941 - a Claude call that ran is not marked asked, so its empty answer spends nothing",
        "file": "tv/tv_diablo.py",
        "find": "                backed[\"asked\"] = \"claude\"\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1941 - a timed-out reader door is not a spent call",
        "file": "tv/char_select.py",
        "find": "                \"asked\": isinstance(e, _sp.TimeoutExpired), \"later\": False}\n",
        "replace": "                \"asked\": False, \"later\": False}\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
