# -*- coding: utf-8 -*-
"""REG-1711 - A REAL READ OF A GAME SCENE WITH NOTHING ON IT TO NAME IS THE GAME, NOT THE LAUNCHER.

His ALT, 2026-10-02 10:42 and 10:50, while he played on Boosteroid: the launcher judge sealed two live reels as "the
launcher" with "judged 4 reads of this reel: gameplay 4". The frame was the Rogue Encampment - Deckard Cain, both orbs,
the belt. The reader had filed every read as gameplay (conf 0.85) and named nothing, because nothing on screen carried a
zone or an item name, and the judge counted only a zone, a panel or an item. MEASURED over three days of his ALT's
shadow_seals.jsonl: 65 launcher seals - 39 fed "transition" x3 (Boosteroid's own "Session has been terminated due to no
activity" screen, opened and looked at), 24 recorded nothing, and exactly 2 fed "gameplay" x3: those two.

What this law drives - the REAL read_shows_the_game / first_reads_show_d2r_hud and the REAL door verdict
(control_app._bare_hud_verdict) with his reads as they were journalled:
  * his 10:42 reads show the game, and the door keeps the reel open
  * the launcher stays the launcher: read as transition, or as gameplay naming its own words (Play, Library, Boosteroid)
  * a read that did not happen never counts (conf None - every fallback row carries it), nor a doubtful one (conf 0.4),
    nor one whose area names something that is not a zone
  * REG-1716 (the v3555 eye): nor an answer the PARSE made into that shape - a string of names, an unknown, spaced or
    absent scene, a JSON true for conf - through the real _parse_read, and on GROK ONLY through Grok's own
    _loose_parse first; the journal row's parse audit is what says the reader said it
RED_PROOF below.
"""
import os
import sys
import tempfile
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

_WORLD = tempfile.mkdtemp(prefix="game_nothing_")
os.environ["TV_HIST"] = _WORLD
os.environ["TV_SESSIONS"] = os.path.join(_WORLD, "sessions.jsonl")

import control_app as ca  # noqa: E402
import tv_diablo as tv  # noqa: E402

#: his ALT's journal rows for reel_s_1790926370987_13672 (sealed 10:42:37 "judged 4 reads of this reel: gameplay 4")
HIS_GAME = {"lane": "deep", "sessionId": "s_g", "scene": "gameplay", "mode": "warm", "model": "sonnet", "area": "",
            "names": [], "tz": [], "conf": 0.85,
            # the parse audit every journalled read carries (REG-1716) - his Mac's five such rows, as written
            "parse": {"ok": True, "strategy": "first-last", "rawLen": 136, "dropped": [], "normalized": []}}
#: the launcher read as he saw it on 39 seals: Boosteroid's own idle-terminate screen
LAUNCHER_TRANSITION = {"lane": "deep", "sessionId": "s_l", "scene": "transition", "mode": "warm", "model": "sonnet",
                       "area": "", "names": [], "tz": [], "conf": 0.9}


def _words():
    return set(ca._AREA_ACT)


def _launch(word):
    return {"lane": "deep", "sessionId": "s_l", "scene": "gameplay", "mode": "warm", "model": "sonnet", "area": "",
            "names": [word], "tz": [], "conf": 0.9,
            # a clean audit, as a real journalled read carries: only the NAME may refuse it (REG-1716 must not mask it)
            "parse": dict(HIS_GAME["parse"])}


class AGameReadWithNothingToName(unittest.TestCase):

    def test_his_1042_reads_show_the_game(self):
        why = tv.read_shows_the_game(dict(HIS_GAME), _words(), frozenset())
        self.assertIn("gameplay", why)
        self.assertIs(tv.first_reads_show_d2r_hud([dict(HIS_GAME)] * 3, words=_words(), items=frozenset()), True)
        self.assertIs(tv.reads_show_the_game([dict(HIS_GAME)] * 4, words=_words(), items=frozenset()), True)

    def test_the_launcher_read_as_transition_is_still_the_launcher(self):
        self.assertIs(tv.first_reads_show_d2r_hud([dict(LAUNCHER_TRANSITION)] * 3, words=_words(), items=frozenset()),
                      False)

    def test_the_launcher_naming_its_own_words_is_still_the_launcher(self):
        reads = [_launch("Play"), _launch("Library"), _launch("Boosteroid")]
        self.assertIs(tv.first_reads_show_d2r_hud(reads, words=_words(), items=frozenset()), False,
                      "a gameplay read naming the launcher's own words was called the game")

    def test_a_read_that_did_not_happen_never_counts(self):
        ghost = dict(HIS_GAME, conf=None, mode="warm")
        self.assertEqual(tv.read_shows_the_game(ghost, _words(), frozenset()), "",
                         "a gameplay row with no confidence of its own - every fallback's shape - was called the game")

    def test_a_doubtful_read_never_counts(self):
        self.assertEqual(tv.read_shows_the_game(dict(HIS_GAME, conf=0.4), _words(), frozenset()), "")

    def test_an_area_that_is_not_a_zone_never_counts(self):
        self.assertEqual(tv.read_shows_the_game(dict(HIS_GAME, area="Boosteroid"), _words(), frozenset()), "")


#: answers a reader could give that the parse turns into a bare, confident gameplay row (the v3555 eye's list)
GARBAGE = ('{"names": "Play", "scene": null, "conf": true}',          # a launcher word sent as a string
           '{"names": [], "scene": "menu", "conf": 0.9}',              # a scene word D2R has no template for
           '{"names": [], "scene": "transition ", "conf": 0.9}',       # the launcher's own scene, with a space
           '{"names": [], "conf": 0.9}',                               # no scene at all
           '{"names": [], "scene": "gameplay", "conf": true}')         # a JSON true is not a confidence


def _row(parsed):
    """the journal row emit_deep_read writes from a parse, in the fields the judge reads"""
    return {"lane": "deep", "sessionId": "s_x", "mode": "warm", "model": "sonnet", "tz": [],
            "scene": parsed["scene"], "names": parsed["names"], "area": parsed["area"], "conf": parsed.get("conf"),
            "parse": parsed.get("_parse_audit") or {}}


class AReadTheParseMadeIsNotTheGame(unittest.TestCase):
    """REG-1716 - the v3555 eye: _parse_read clamps, so a garbage answer arrives as REG-1711's exact shape"""

    def test_premise_his_real_read_through_the_real_parse_is_the_game(self):
        got = tv._parse_read('{"area": "", "names": [], "scene": "gameplay", "conf": 0.85}')
        self.assertIn("gameplay", tv.read_shows_the_game(_row(got), _words(), frozenset()))

    def test_every_answer_the_parse_rewrote_is_not_the_game(self):
        for raw in GARBAGE:
            got = tv._parse_read(raw)
            self.assertEqual(got["scene"], "gameplay", raw)          # the shape REG-1711 counts - it is the premise
            self.assertEqual(tv.read_shows_the_game(_row(got), _words(), frozenset()), "",
                             "an answer the parse rewrote into gameplay was called the game: %s" % raw)

    def test_a_row_with_no_audit_cannot_show_the_words_were_the_readers(self):
        bare = dict(HIS_GAME)
        del bare["parse"]
        self.assertEqual(tv.read_shows_the_game(bare, _words(), frozenset()), "")


class GrokOnlyCarriesWhatItsOwnParseRewrote(unittest.TestCase):
    """REG-1716 - on his GROK ONLY ALT the answer is cleaned by g5_grok_eyes._loose_parse BEFORE _parse_read sees it"""

    def _read(self, raw):
        import g5_grok_eyes as g5
        saved = (g5.grok_only_blocked_why, g5.g5_vision_read)
        self.addCleanup(lambda: (setattr(g5, "grok_only_blocked_why", saved[0]), setattr(g5, "g5_vision_read", saved[1])))
        g5.grok_only_blocked_why = lambda: None
        g5.g5_vision_read = lambda ap, prompt=None, **k: g5._loose_parse(raw)
        got = tv._grok_oneshot("/nonexistent/f_1.jpg", timeout=5)
        self.assertIsNotNone(got, raw)
        return got

    def test_REG1721_a_refused_true_stays_unknown_not_zero(self):
        import g5_grok_eyes as g5
        j = g5._loose_parse('{"names": [], "scene": "gameplay", "conf": true}')
        self.assertIsNone(j["conf"], "a JSON true for conf became %r - a confidence the reader never gave" % j["conf"])
        self.assertIn("a-bool-is-not-a-confidence", [f.get("why") for f in j.get("_g5_fixed") or []])
        self.assertEqual(g5._loose_parse('{"names": [], "scene": "gameplay"}')["conf"], 0.0,
                         "premise: an ABSENT conf keeps its old 0.0 default (only the refused bool changed)")

    def test_premise_a_real_grok_read_is_the_game(self):
        got = self._read('{"area": "", "names": [], "scene": "gameplay", "conf": 0.85}')
        self.assertIn("gameplay", tv.read_shows_the_game(_row(got), _words(), frozenset()))

    def test_a_grok_answer_its_own_parse_rewrote_is_not_the_game(self):
        for raw in ('{"names": "Play", "scene": "gameplay", "conf": 0.9}', '{"names": [], "conf": 0.9}',
                    '{"names": [], "scene": "gameplay", "conf": true}'):
            got = self._read(raw)
            self.assertEqual(got["scene"], "gameplay", raw)
            self.assertEqual(tv.read_shows_the_game(_row(got), _words(), frozenset()), "",
                             "Grok's own parse cleaned this into a bare gameplay row and it was called the game: %s" % raw)


class TheDoorKeepsHisSessionOpen(unittest.TestCase):

    def setUp(self):
        saved = (ca.bare_content_reads, ca.reel_content_reads, ca._game_items)
        self.addCleanup(lambda: (setattr(ca, "bare_content_reads", saved[0]),
                                 setattr(ca, "reel_content_reads", saved[1]), setattr(ca, "_game_items", saved[2])))
        ca._game_items = lambda: frozenset()
        self.pre = {"windowLabel": "Boosteroid"}
        self.assertTrue(tv.label_is_bare_cloud("Boosteroid"), "premise: a bare Boosteroid window is the judged one")

    def _verdict(self, reads):
        ca.bare_content_reads = lambda: list(reads)
        ca.reel_content_reads = lambda: list(reads)
        return ca._bare_hud_verdict(self.pre)

    def test_his_live_game_is_not_sealed(self):
        self.assertIs(self._verdict([dict(HIS_GAME)] * 4), True,
                      "his live game, read as gameplay with nothing to name, was judged the launcher")

    def test_the_launcher_is_still_sealed(self):
        self.assertIs(self._verdict([dict(LAUNCHER_TRANSITION)] * 4), False)


RED_PROOF = [
    {
        "why": "REG-1711 - a real gameplay read with nothing to name is not the game: his live reel seals as the launcher",
        "file": "tv_diablo.py",
        "find": "    if (sc == \"gameplay\" and not (row.get(\"names\") or []) and not str(row.get(\"area\") or \"\").strip()\n",
        "replace": "    if (False and not (row.get(\"names\") or []) and not str(row.get(\"area\") or \"\").strip()\n",
        "matches": 1,
    },
    {
        "why": "REG-1711 - a gameplay read naming the launcher's own words (Play, Library) is called the game",
        "file": "tv_diablo.py",
        "find": "    if (sc == \"gameplay\" and not (row.get(\"names\") or []) and not str(row.get(\"area\") or \"\").strip()\n",
        "replace": "    if (sc == \"gameplay\" and not str(row.get(\"area\") or \"\").strip()\n",
        "matches": 1,
    },
    {
        "why": "REG-1711 - a read with no confidence of its own (every fallback row) is called the game",
        "file": "tv_diablo.py",
        "find": "            and isinstance(_c, (int, float)) and not isinstance(_c, bool) and _c >= _GAMEPLAY_CONF_MIN\n",
        "replace": "            and True\n",
        "matches": 1,
    },
    {
        "why": "REG-1711 - an area that is not a zone stops disqualifying a gameplay read",
        "file": "tv_diablo.py",
        "find": " and not (row.get(\"names\") or []) and not str(row.get(\"area\") or \"\").strip()\n",
        "replace": " and not (row.get(\"names\") or [])\n",
        "matches": 1,
    },
    {
        "why": "REG-1711 - the confidence bar falls to nothing: a doubtful read keeps a launcher reel open",
        "file": "tv_diablo.py",
        "find": "_GAMEPLAY_CONF_MIN = 0.7\n",
        "replace": "_GAMEPLAY_CONF_MIN = 0.0\n",
        "matches": 1,
    },
    {
        "why": "REG-1716 - the judge stops asking whether the reader said it: a garbage answer the parse rewrote is the game",
        "file": "tv_diablo.py",
        "find": "            and _the_reader_said_it(row)):\n",
        "replace": "            and True):\n",
        "matches": 1,
    },
    {
        "why": "REG-1716 - an absent scene goes back to a silent default: a read with no scene is gameplay the reader said",
        "file": "tv_diablo.py",
        "find": "        _audit[\"normalized\"].append({\"field\": \"scene\", \"from\": \"(absent)\", \"to\": \"gameplay\", \"why\": \"absent-scene-default\"})\n",
        "replace": "        pass\n",
        "matches": 1,
    },
    {
        "why": "REG-1721 - a refused JSON true for conf becomes 0.0 again, a confidence the reader never gave",
        "file": "g5_grok_eyes.py",
        "find": "            j[\"conf\"] = None\n        else:\n",
        "replace": "            j[\"conf\"] = None\n        if True:\n",
        "matches": 1,
    },
    {
        "why": "REG-1716 - Grok's own parse rewrites in silence again: on GROK ONLY a string of names becomes the game",
        "file": "g5_grok_eyes.py",
        "find": "        if _fixed:\n            j[\"_g5_fixed\"] = _fixed\n",
        "replace": "        if False:\n            j[\"_g5_fixed\"] = _fixed\n",
        "matches": 1,
    },
    {
        "why": "REG-1716 - the GROK ONLY path drops what Grok's parse rewrote before the journal's audit sees it",
        "file": "tv_diablo.py",
        "find": "        if _gfix and isinstance(pr.get(\"_parse_audit\"), dict):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
