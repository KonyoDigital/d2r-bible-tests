# -*- coding: utf-8 -*-
"""#103 step B — A SESSION BELONGS TO THE CHARACTER HE ENTERED IT WITH, AND EVERYTHING AFTER IS ROUTED TO IT.

Konyo, 2026-09-30: "a sessions character selection then moving forward.. scenarios future wise are obviously linked to
that character meaning templates filters just like the printer.. same logic getting routed down".

What existed: tv/char_select.py learned WHO his characters are from the character-select screen, and
tv/equipped_ledger.py already split a reel at a login row and carried that character across the hourly rollover - but
its logins came from a reader field nobody asks for (REG-1522), so every reel read UNATTRIBUTED. The two halves were
built and never joined. [[the-unjoined-end]]

This law drives the joint:
  · THE READER IS ASKED WHICH ROW IS HIGHLIGHTED (the character the game enters with), and only a name from the rows
    that same read listed counts - a guessed character would file his gear under the wrong one.
  · THE VISIT'S LAST FRAME DECIDES. His first frames show the row the game highlights on arrival; he may move the
    cursor before pressing Play, so a visit that ran past its reads gets ONE closing read of its last frame, once the
    scan is past the visit (or the reel is walked and the visit is 90 s old) - never while he may still be on it, and
    within the same hourly cap as every read.
  · EACH LOGIN JOINS THE GEAR LEDGER as the row its reel splits at (the journal's own sessionId), so the gear after it -
    and the rollover reels the chain carries - is that character's.
  · THE PRINTER'S ORDER: a sealed reel the learner has not walked yet WAITS (bounded: 6 h, then filed without it), a reel
    whose frames are gone never waits, and a learner reading another world's reels is never asked. The doctor says a
    waiting reel is waiting, not late; the console's learner nudges the gear ledger when it has news.
Fixture reels, a stub reader, temp stores - his roster and his gear ledger are never touched. [[unknown-stays-unknown]]
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import char_select as CS  # noqa: E402
import equipped_ledger as E  # noqa: E402
from test_equipped_items_are_pixel_exact_per_character import _World, _row, _seal, _worn  # noqa: E402

T0 = 1790000000000
MEASURED = (0.03, 0.36, 0.1, 0.22)          # both stone panels, as char_select's own law measures them


def _rows(names):
    return [{"name": n, "key": CS._fold(n), "cls": "Paladin", "level": 80, "title": None} for n in names]


class TheHighlightedRowIsOneTheReadListed(unittest.TestCase):

    def test_only_a_listed_row_can_be_the_one_he_entered_with(self):
        rows = _rows(["Hammerdin", "Frostnova"])
        self.assertEqual(CS.selected_of({"selected": "HAMMERDIN"}, rows), ("Hammerdin", None))
        self.assertEqual(CS.selected_of('{"selected": "Frostnova"}', rows)[0], "Frostnova")
        name, why = CS.selected_of({"selected": "Nobody"}, rows)
        self.assertIsNone(name, "a highlighted name the list does not carry was taken as his character")
        self.assertIn("not one of the rows", why)
        for raw in ({"selected": None}, {"selected": ""}, {}, "not json", None):
            self.assertIsNone(CS.selected_of(raw, rows)[0], repr(raw))

    def test_the_reader_is_asked_for_it(self):
        import tv_diablo as T
        p = T.CHARSEL_READ_PROMPT.format(path="x")
        self.assertIn('"selected":null', p, "the reader's JSON shape does not carry the highlighted row")
        self.assertIn("HIGHLIGHTED", p)


class _Reels(unittest.TestCase):
    """A fixture reel store: frames are tiny files named by time; b"cs" is the character-select screen."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="cs_login_")
        self.hist = os.path.join(self.tmp, "hist")
        os.environ["TV_CHARS_LEARNED"] = os.path.join(self.tmp, "roster.json")
        self.reads = []
        self._orig = CS.panel_crop
        CS.panel_crop = lambda p, out: p

    def tearDown(self):
        CS.panel_crop = self._orig
        os.environ.pop("TV_CHARS_LEARNED", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def reel(self, name, frames):
        rd = os.path.join(self.hist, name)
        os.makedirs(rd, exist_ok=True)
        for ts, cs in frames:
            with open(os.path.join(rd, "f_%d.jpg" % ts), "wb") as f:
                f.write(b"cs" if cs else b"no")
        return rd

    def stats(self, p):
        with open(p, "rb") as f:
            return MEASURED if f.read() == b"cs" else (0.3, 0.2, 0.3, 0.2)

    def reader_for(self, pick):
        """a stub reader: `pick(frame_ts)` names the highlighted row on that frame"""
        def read(crop):
            ts = CS._frame_ts(crop)
            self.reads.append(ts)
            return {"screen": "character-select", "partial": False, "selected": pick(ts),
                    "chars": [{"name": "Hammerdin", "cls": "Paladin", "level": 80},
                              {"name": "Frostnova", "cls": "Sorceress", "level": 71}]}
        return read

    def tick(self, pick, now_ms):
        return CS.tick(root=self.hist, stats=self.stats, reader=self.reader_for(pick), now=now_ms / 1000.0)


class TheVisitsLastFrameDecides(_Reels):

    def test_each_read_names_the_highlighted_row_and_the_login_is_its_session(self):
        self.reel("reel_s_1", [(T0 + i * 1000, True) for i in range(2)] + [(T0 + 200000, False)])
        r = self.tick(lambda ts: "Hammerdin", T0 + 400000)
        self.assertTrue(r["ok"], r)
        L = CS.logins(CS.load())
        self.assertEqual([(x["character"], x["sessionId"], x["reel"]) for x in L], [("Hammerdin", "s_1", "reel_s_1")])
        self.assertTrue(CS.scanned_reel(CS.load(), "reel_s_1"))

    def test_a_visit_that_ran_on_is_decided_by_its_last_frame(self):
        # eleven seconds on the screen: he arrived on Hammerdin and moved to Frostnova before pressing Play
        self.reel("reel_s_2", [(T0 + i * 1000, True) for i in range(11)] + [(T0 + 20000 + i * 60000, False) for i in range(4)])
        r = self.tick(lambda ts: "Frostnova" if ts >= T0 + 10000 else "Hammerdin", T0 + 400000)
        self.assertEqual(r.get("closed"), 1, "the visit's last frame was never read: %r" % r)
        self.assertIn(T0 + 10000, self.reads, "the closing read did not read the LAST frame of the visit")
        L = CS.logins(CS.load())
        self.assertEqual([x["character"] for x in L], ["Frostnova"],
                         "the session went to the row highlighted on ARRIVAL, not the one he entered with")

    def test_a_visit_he_may_still_be_on_is_not_closed_and_not_a_login_yet(self):
        self.reel("reel_s_3", [(T0 + i * 1000, True) for i in range(8)])
        self.tick(lambda ts: "Frostnova" if ts >= T0 + 7000 else "Hammerdin", T0 + 30000)
        d = CS.load()
        self.assertEqual(CS.logins(d), [], "a visit that may still be on screen was already a login")
        self.assertFalse(CS.scanned_reel(d, "reel_s_3"), "a reel still owing a closing read was said to be walked")
        self.assertNotIn(T0 + 7000, self.reads, "the closing read ran while he could still be on the screen")
        r = self.tick(lambda ts: "Frostnova" if ts >= T0 + 7000 else "Hammerdin", T0 + 200000)
        self.assertEqual(r.get("closed"), 1)
        self.assertEqual([x["character"] for x in CS.logins(CS.load())], ["Frostnova"])
        self.assertTrue(CS.scanned_reel(CS.load(), "reel_s_3"))

    def test_the_closing_read_keeps_the_hourly_cap(self):
        self.reel("reel_s_4", [(T0 + i * 1000, True) for i in range(8)] + [(T0 + 300000, False)])
        now = T0 + 400000
        d = CS._empty()
        d["stats"]["readTs"] = [now / 1000.0 - 10] * (CS.READS_PER_HOUR - 2)     # room for the visit's two reads only
        CS.save(d)
        r = self.tick(lambda ts: "Hammerdin", now)
        self.assertEqual(r.get("closed"), 0, "the closing read spent past the hourly cap: %r" % r)
        self.assertIn("hourly read cap", r.get("why", ""))
        self.assertEqual(CS.logins(CS.load()), [], "a visit whose closing read is owed became a login")
        r2 = self.tick(lambda ts: "Hammerdin", now + 3700 * 1000)
        self.assertEqual(r2.get("closed"), 1, "the owed closing read never came back after the hour")


class AFailedCloseConfirmsNothing(_Reels):
    """#115 (REG-1619) - the #231 eye on v3529: "a failed close ends that wait". He arrived on Hammerdin and ran on past
    the reads; when the one read that could say otherwise names no row, the session is not his arrival highlight's."""

    LAST = T0 + 10000

    def _close(self, reel, how):
        self.reel(reel, [(T0 + i * 1000, True) for i in range(11)] + [(T0 + 20000 + i * 60000, False) for i in range(4)])
        base = self.reader_for(lambda ts: "Hammerdin")

        def read(crop):
            ts = CS._frame_ts(crop)
            if ts == self.LAST and how == "refused":
                self.reads.append(ts)
                return None
            if ts == self.LAST and how == "whole-empty":
                self.reads.append(ts)
                return {"screen": "character-select", "partial": False, "selected": None, "chars": []}
            if ts == self.LAST and how == "no-highlight":
                self.reads.append(ts)
                return {"screen": "character-select", "partial": False, "selected": None,
                        "chars": [{"name": "Hammerdin", "cls": "Paladin", "level": 80},
                                  {"name": "Frostnova", "cls": "Sorceress", "level": 71}]}
            return base(crop)
        if how == "unopenable":
            CS.panel_crop = lambda p, out: None if p.endswith("f_%d.jpg" % self.LAST) else p
        CS.tick(root=self.hist, stats=self.stats, reader=read, now=(T0 + 400000) / 1000.0)
        d = CS.load()
        return [x for x in CS.logins(d) if x["reel"] == reel], d

    def _unconfirmed(self, how):
        L, d = self._close("reel_f_" + how.replace("-", "_"), how)
        self.assertEqual(len(L), 1, L)
        self.assertIsNone(L[0]["character"], "a %s close filed the session under the ARRIVAL highlight: %r" % (how, L[0]))
        self.assertEqual(L[0].get("unconfirmed"), "Hammerdin")
        self.assertIn("named no row", L[0].get("why") or "")
        self.assertTrue(CS.scanned_reel(d, L[0]["reel"]), "the wait never ended: the reel could never be filed")
        self.assertEqual(E.login_rows(L), [], "the gear ledger filed gear under an unconfirmed character")

    def test_a_refused_close(self):
        self._unconfirmed("refused")

    def test_a_throttled_close_stays_owed_and_is_read_when_it_lifts(self):
        """REG-1945 (the #231 eye on v3574) - a closing read the reader could not make NOW (a throttle, a budget block)
        was closed 'refused' for good, so the session was filed under the arrival highlight. It stays owed."""
        reel = "reel_f_throttled"
        self.reel(reel, [(T0 + i * 1000, True) for i in range(11)] + [(T0 + 20000 + i * 60000, False) for i in range(4)])
        base = self.reader_for(lambda ts: "Frostnova" if ts == self.LAST else "Hammerdin")
        state = {"throttled": True}

        def read(crop):
            if CS._frame_ts(crop) == self.LAST and state["throttled"]:
                return {"note": "reader throttled - not read", "asked": False, "later": True}
            return base(crop)
        CS.tick(root=self.hist, stats=self.stats, reader=read, now=(T0 + 400000) / 1000.0)
        d = CS.load()
        vis = [v for vid, v in d["visits"].items() if str(vid).startswith(reel)]
        self.assertEqual(1, len(vis), "PREMISE: the visit was read on arrival")
        self.assertFalse(vis[0].get("closed"), "a throttled closing read closed the visit: %r" % vis[0].get("closed"))
        self.assertFalse(CS.scanned_reel(d, reel), "a reel whose closing read is still owed was called finished")
        state["throttled"] = False
        CS.tick(root=self.hist, stats=self.stats, reader=read, now=(T0 + 460000) / 1000.0)
        L = [x for x in CS.logins(CS.load()) if x["reel"] == reel]
        self.assertEqual(["Frostnova"], [x["character"] for x in L], "the close was not read once the throttle lifted")

    def test_a_close_whose_frame_would_not_open(self):
        self._unconfirmed("unopenable")

    def test_a_close_that_saw_no_highlighted_row(self):
        self._unconfirmed("no-highlight")

    def test_a_close_that_saw_a_whole_list_of_nobody(self):
        # the Grok CLI look at v3534: this path was untested. A whole list that shows nobody names no row - the session
        # stays unconfirmed (never filed under the arrival guess), and the close is a LOOK (REG-1620), so the wait ends
        self._unconfirmed("whole-empty")

    def test_a_close_that_named_the_row_still_decides(self):
        # the same visit, read to its end: the closing read's own name is the login (and agreeing with arrival is fine)
        L, _d = self._close("reel_f_read", "read")
        self.assertEqual([(x["character"], x.get("unconfirmed")) for x in L], [("Hammerdin", None)])


class AWholeListOfNobodyIsALook(_Reels):
    """#114 (REG-1620) - the #231 eye on v3528: a whole list that shows nobody was never stored (only `if rows:`
    recorded), so it could never count against the characters it stopped showing."""

    def _misses(self, how):
        self.reel("reel_e_1", [(T0 + i * 1000, True) for i in range(2)] + [(T0 + 200000, False)])
        self.reel("reel_e_2", [(T0 + 400000 + i * 1000, True) for i in range(2)] + [(T0 + 600000, False)])

        def read(crop):
            ts = CS._frame_ts(crop)
            self.reads.append(ts)
            if ts >= T0 + 300000:
                if how == "other":
                    return {"screen": "loading", "partial": False}
                return {"screen": "character-select", "partial": how != "whole", "selected": None, "chars": []}
            return {"screen": "character-select", "partial": False, "selected": "Hammerdin",
                    "chars": [{"name": "Hammerdin", "cls": "Paladin", "level": 80},
                              {"name": "Frostnova", "cls": "Sorceress", "level": 71}]}
        CS.tick(root=self.hist, stats=self.stats, reader=read, now=(T0 + 900000) / 1000.0)
        d = CS.load()
        self.assertEqual(sorted(c["name"] for c in d["chars"].values()), ["Frostnova", "Hammerdin"])
        return {c["name"]: CS.proof(d, c)["misses"] for c in d["chars"].values()}

    def test_a_whole_list_of_nobody_counts_against_everyone_it_stopped_showing(self):
        self.assertEqual(self._misses("whole"), {"Hammerdin": 1, "Frostnova": 1},
                         "a whole list that showed nobody was no evidence against the characters it stopped showing")

    def test_a_cut_off_empty_list_is_no_evidence(self):
        self.assertEqual(self._misses("cut-off"), {"Hammerdin": 0, "Frostnova": 0})

    def test_another_screen_is_no_list_at_all(self):
        self.assertEqual(self._misses("other"), {"Hammerdin": 0, "Frostnova": 0})


class TheGearAfterALoginIsThatCharacters(_World):

    LOGIN = {"reel": "reel_s_A", "sessionId": "s_A", "ts": T0 + 30000, "character": "Hammerdin",
             "visit": "reel_s_A#%d" % (T0 + 30000), "reader": "vision"}

    def rows(self):
        return [_row("s_A", T0 + 1000), _worn("s_A", T0 + 10000, "reel_s_A/f_1", "Shako"),
                _worn("s_A", T0 + 60000, "reel_s_A/f_2", "Enigma"), _seal("s_A", T0 + 3600000),
                _row("s_B", T0 + 3600000 + 30000), _worn("s_B", T0 + 3600000 + 40000, "reel_s_B/f_3", "Arachnid Mesh"),
                _seal("s_B", T0 + 7200000)]

    def test_the_gear_after_the_login_is_his_and_the_rollover_carries_it(self):
        r, d = self.ingest(self.rows(), now_ms=T0 + 8000000, logins=[self.LOGIN], cs=None)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["logins"], 1)
        ham = d["characters"].get("Hammerdin")
        self.assertIsNotNone(ham, "the login never reached the gear ledger: %r" % sorted(d["characters"]))
        names = json.dumps(ham)
        self.assertIn("Enigma", names, "the gear AFTER the login is not Hammerdin's")
        self.assertIn("Arachnid Mesh", names, "the rollover reel did not carry the character")
        self.assertNotIn("Shako", names, "gear worn BEFORE the login was filed under him")
        self.assertIn("Shako", json.dumps(d["unattributed"]))

    def test_a_reel_the_learner_has_not_walked_waits_then_files(self):
        os.makedirs(os.path.join(self.hist, "reel_s_A"), exist_ok=True)
        os.makedirs(os.path.join(self.hist, "reel_s_B"), exist_ok=True)
        cs = CS._empty()
        cs["reels"] = {"reel_s_A": {"pos": 10, "frames": 50}, "reel_s_B": {"pos": 50, "frames": 50}}
        r, _d = self.ingest(self.rows(), now_ms=T0 + 8000000, logins=[self.LOGIN], cs=cs)
        self.assertEqual(r["waiting"], ["s_A"], "a reel the learner had not walked was filed anyway: %r" % r)
        self.assertEqual(r["ingested"], ["s_B"])
        cs["reels"]["reel_s_A"]["pos"] = 50
        r2, d2 = self.ingest(self.rows(), now_ms=T0 + 8000000, logins=[self.LOGIN], cs=cs)
        self.assertEqual((r2["waiting"], r2["ingested"]), ([], ["s_A"]))
        self.assertIn("Enigma", json.dumps(d2["characters"].get("Hammerdin")))

    def test_a_reel_whose_frames_are_gone_does_not_wait(self):
        cs = CS._empty()
        cs["reels"] = {}
        r, _d = self.ingest(self.rows(), now_ms=T0 + 8000000, logins=[], cs=cs)
        self.assertEqual(r["waiting"], [], "a reel no learner can ever walk waited for it")

    def test_a_reel_that_waited_six_hours_is_filed_without_it(self):
        os.makedirs(os.path.join(self.hist, "reel_s_A"), exist_ok=True)
        cs = CS._empty()
        cs["reels"] = {"reel_s_A": {"pos": 0, "frames": 50}}
        r, _d = self.ingest(self.rows(), now_ms=T0 + 3600000 + E.CS_WAIT_MS + 60000, logins=[], cs=cs)
        self.assertNotIn("s_A", r["waiting"], "a learner that never speaks stopped the gear ledger for good")
        self.assertIn("s_A", r["ingested"])

    def test_another_worlds_learner_is_never_asked(self):
        cs, logins, why = E._char_select_view(self.hist)
        self.assertIsNone(cs, "the gear ledger asked a learner that reads another world's reels")
        self.assertEqual(logins, [])
        self.assertIn("another world", why)

    def _doctor_with(self, cs, now_ms):
        import console_doctor as CD
        self.write(self.rows())
        orig = E._char_select_view
        E._char_select_view = lambda hist, _cs=cs: (_cs, [], None)
        try:
            return CD, self.doctor([self.journal], now_ms=now_ms)
        finally:
            E._char_select_view = orig

    def test_a_waiting_reel_is_not_late_on_the_doctor(self):
        # s_A sealed 65 min ago and waits for the learner; s_B sealed 5 min ago, inside the grace
        os.makedirs(os.path.join(self.hist, "reel_s_A"), exist_ok=True)
        cs = CS._empty()
        cs["reels"] = {"reel_s_A": {"pos": 0, "frames": 50}}
        CD, (state, say) = self._doctor_with(cs, T0 + 7200000 + 5 * 60000)
        self.assertEqual(state, CD.OK, "a reel waiting for the character-select learner read as a stopped lane: %s" % say)
        self.assertIn("wait for the character-select learner", say)

    def test_when_every_owed_reel_waits_the_lane_is_not_late_and_not_unknown(self):
        for sid in ("s_A", "s_B"):
            os.makedirs(os.path.join(self.hist, "reel_" + sid), exist_ok=True)
        cs = CS._empty()
        cs["reels"] = {"reel_s_A": {"pos": 0, "frames": 50}, "reel_s_B": {"pos": 1, "frames": 50}}
        CD, (state, say) = self._doctor_with(cs, T0 + 7200000 + 30 * 60000)
        self.assertEqual(state, CD.OK, "every owed reel waits upstream, yet the row read %s: %s" % (state, say))
        self.assertIn("2 owed reel(s) wait for the character-select learner", say)

    def test_the_same_reel_not_waiting_is_late(self):
        # the premise the case above depends on: with the learner done with s_A, its 65-min-old seal IS late
        os.makedirs(os.path.join(self.hist, "reel_s_A"), exist_ok=True)
        cs = CS._empty()
        cs["reels"] = {"reel_s_A": {"pos": 50, "frames": 50}}
        CD, (state, say) = self._doctor_with(cs, T0 + 7200000 + 5 * 60000)
        self.assertEqual(state, CD.MISSING, "the late path never fires, so the case above proves nothing: %s" % say)


class TheConsoleRunsTheNextStation(unittest.TestCase):

    def test_the_learner_nudges_the_gear_ledger_when_it_has_news(self):
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        # from the tick to the END OF THE FUNCTION holding it - both ends anchored to the code, never a length guessed
        at = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "_csr"
              for t in n.targets) and "_cs.tick()" in (ast.get_source_segment(src, n.value) or "")]
        self.assertEqual(len(at), 1, "the learner's tick is not one assignment any more")
        fns = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.lineno <= at[0] <= n.end_lineno]
        inner = min(fns, key=lambda n: n.end_lineno - n.lineno)
        blk = "\n".join(src.splitlines()[at[0] - 1:inner.end_lineno])
        self.assertIn('elif _csr.get("finished") or _csr.get("reads") or _csr.get("closed"):', blk)
        self.assertIn("_equipped_ledger_nudge()", blk, "the learner never hands its news to the next station")
        self.assertTrue(any(isinstance(n, ast.FunctionDef) and n.name == "_equipped_ledger_nudge" for n in ast.walk(tree)))


RED_PROOF = [
    {"why": "REG-1945 - a throttled closing read closes the visit 'refused' for good",
     "file": "tv/char_select.py",
     "find": "        raw = _ask(reader, crop)\n        if _surface_later(raw):\n",
     "replace": "        raw = _ask(reader, crop)\n        if False:\n", "matches": 1},
    {"why": "#114 (REG-1620) - a whole list that shows nobody is never stored, so it counts against no one",
     "file": "tv/char_select.py",
     "find": "                elif _whole_and_empty(raw, rwhy):\n",
     "replace": "                elif False:\n", "matches": 1},
    {"why": "#114 (REG-1620) - another screen or a cut-off list is stored as a whole list of nobody",
     "file": "tv/char_select.py",
     "find": "    return rwhy != \"other screen\" and partial_of(raw) is False\n",
     "replace": "    return True\n", "matches": 1},
    {"why": "#115 (REG-1619) - a close that was refused or named no row files the session under the ARRIVAL highlight",
     "file": "tv/char_select.py",
     "find": "        if v.get(\"closed\") and best.get(\"reader\") != \"vision-close\":\n",
     "replace": "        if False:\n", "matches": 1},
    {"why": "#115 (REG-1619) - every closed visit reads unconfirmed, even one whose closing read named the row",
     "file": "tv/char_select.py",
     "find": "        if v.get(\"closed\") and best.get(\"reader\") != \"vision-close\":\n",
     "replace": "        if v.get(\"closed\"):\n", "matches": 1},
    {"why": "#103B - a highlighted name the list does not carry is taken as his character",
     "file": "tv/char_select.py",
     "find": "    for r in rows or []:\n        if r.get(\"key\") == _fold(name):\n            return r[\"name\"], None\n    return None, \"the highlighted name %r is not one of the rows this read listed\" % name\n",
     "replace": "    return name, None\n", "matches": 1},
    {"why": "#103B - the reads stop saying which row is highlighted",
     "file": "tv/char_select.py",
     "find": "                                               \"selected\": sel})\n",
     "replace": "                                               \"selected\": None})\n", "matches": 1},
    {"why": "#103B - no visit ever owes a closing read: the row highlighted on ARRIVAL wins",
     "file": "tv/char_select.py",
     "find": "    return int(lf.get(\"ts\") or 0) - int(v.get(\"ts\") or 0) >= CLOSE_READ_GAP_MS\n",
     "replace": "    return False\n", "matches": 1},
    {"why": "#103B - a visit he may still be on is closed at once",
     "file": "tv/char_select.py",
     "find": "        over = (int(rs.get(\"scannedTs\") or 0) - lts > VISIT_GAP_S * 1000\n",
     "replace": "        over = True or (int(rs.get(\"scannedTs\") or 0) - lts > VISIT_GAP_S * 1000\n", "matches": 1},
    {"why": "#103B - a visit whose closing read is owed already counts as a login",
     "file": "tv/char_select.py",
     "find": "        if not isinstance(v, dict) or _close_owed(vid, v):\n            continue\n        sel = ",
     "replace": "        if not isinstance(v, dict):\n            continue\n        sel = ", "matches": 1},
    {"why": "#103B - the closing read spends past the hourly cap",
     "file": "tv/char_select.py",
     "find": "        if len(st[\"readTs\"]) >= READS_PER_HOUR:\n            return n, \"hourly read cap (%d) reached\" % READS_PER_HOUR\n",
     "replace": "", "matches": 1},
    {"why": "#103B - the logins never reach the gear ledger (the unjoined end)",
     "file": "tv/equipped_ledger.py",
     "find": "    reels = reels_from_rows(rows + lrows)\n",
     "replace": "    reels = reels_from_rows(rows)\n", "matches": 1},
    {"why": "#103B - the printer's order goes: a reel the learner has not walked is filed anyway",
     "file": "tv/equipped_ledger.py",
     "find": "        if cs_waits(cs, reel, hist_dir, now):\n",
     "replace": "        if False:\n", "matches": 1},
    {"why": "#103B - a reel whose frames are gone waits for a walk that can never come",
     "file": "tv/equipped_ledger.py",
     "find": "    if not os.path.isdir(os.path.join(str(hist_dir), name)):\n        return None\n",
     "replace": "", "matches": 1},
    {"why": "#103B - a learner that never speaks stops the gear ledger for good",
     "file": "tv/equipped_ledger.py",
     "find": "    if isinstance(seal, (int, float)) and now_ms - int(seal) > CS_WAIT_MS:\n        return None\n",
     "replace": "", "matches": 1},
    {"why": "#103B - his learner is asked about a fixture world's reels (the REG-1583 leak shape)",
     "file": "tv/equipped_ledger.py",
     "find": "        if os.path.realpath(str(_cs.hist_root())) != os.path.realpath(str(hist_dir)):\n",
     "replace": "        if False:\n", "matches": 1},
    {"why": "#103B - the doctor dates a waiting reel's seal as the lane being late",
     "file": "tv/console_doctor.py",
     "find": "        oldest = c.get(\"oldestNotWaitingSealTs\") if _waiting else c.get(\"oldestOwedSealTs\")\n",
     "replace": "        oldest = c.get(\"oldestOwedSealTs\")\n", "matches": 1},
    {"why": "#103B - with every owed reel waiting upstream, the doctor still grades the lane (and reads UNKNOWN)",
     "file": "tv/console_doctor.py",
     "find": "    if c[\"owed\"] > len(_waiting):\n",
     "replace": "    if c[\"owed\"] > 0:\n", "matches": 1},
    {"why": "#103B - the contract's late age counts the reels that wait upstream",
     "file": "tv/equipped_ledger.py",
     "find": "        _free = [(sid, t) for sid, t in owed if sid not in set(out[\"waitingOnCharSelect\"])]\n",
     "replace": "        _free = list(owed)\n", "matches": 1},
    {"why": "#103B - the learner never hands its news to the next station",
     "file": "tv/control_app.py",
     "find": "                    _eqr = _equipped_ledger_nudge()\n",
     "replace": "                    _eqr = None\n", "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
