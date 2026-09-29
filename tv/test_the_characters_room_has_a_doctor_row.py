# -*- coding: utf-8 -*-
"""#41 ranks 12 + 13 (2026-09-29) — THE 👤 CHARACTERS ROOM HAS A DOCTOR ROW, AND ITS TWO MAINS ARE NAMED WHEN THEY DIFFER.

The heart audit (#256, ranked 26 gaps) found the Characters tab's heart was ONE proven law and nothing at runtime: no
doctor row named a broken link, nothing reached the eagle, no registry line said why there is no corroborator — while
he has a real build in the store (backup 2026-09-29 01:10). And its two MAINs collide under one word: ★ Set as MAIN
(d2r_cbMain, the room's) and the vault's MAIN (d2r_mainCharacter, what the #246 lock follows) can name different
characters, and marking a build ★ MAIN locks none of its gear. Nothing said so.

WHAT THIS LAW DRIVES (the real code, never a grep of it):
  · console_doctor.characters_room_verdict — pure, over fixtures: an absent store is MEASURED empty (OK, "0 builds"),
    an unparseable one is MISSING naming d2r_charBuilds and UNKNOWN (never "0 builds"), a store that is a list is
    MISSING, a d2r_cbMain naming no saved build is MISSING naming the id, a healthy store is OK with the count and the
    ★ MAIN; rank 13: ★ MAIN and the vault's MAIN naming different characters is SAID on the OK line naming BOTH and the
    door (REG-1553 - the planner names a build '<Class> build' and the vault's MAIN is a typed character name: two
    vocabularies, and a red he is told to leave carries nothing), the same name is OK saying "also", a vault MAIN with
    no name yet is OK (not a disagreement), and the name compare ignores case.
  · console_doctor._check_the_characters_room — the live row, with the shared board read stubbed: no console, a refused
    read and a read with no stores are each UNKNOWN (never "0 builds"); with stores it answers what the pure verdict
    answers over the SAME three keys (the join, driven).
  · the registries: the row is in CHECKS under its name, declared in WATCHES, and explained in corroborate.NO_JOINT_YET
    (coverage() files it as uncovered-with-a-reason, never as unexplained).
  · rank 13 on the page: the ★ Set as MAIN button the room RENDERS carries the sentence (its title), and the room's
    help copy says it too — driven through the room's own harness (test_the_characters_tab_is_manual_and_separate).
⚠ WHAT IT CANNOT SEE: whether #tab-chars is on the rendered board (the doctor reads stores, not the DOM), and pixels.
RED_PROOF below: every sabotage turns this law red for its own reason.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as CD  # noqa: E402
import corroborate as C  # noqa: E402

ROW = "characters room"
BUILDS = {"b1": {"name": "Konyoress", "cls": "Sorceress", "level": 80, "sets": [], "at": 1},
          "b2": {"name": "Hammerdin", "cls": "Paladin", "level": 91, "sets": [], "at": 5}}
VAULT_MAIN = {"name": "Konyoress", "class": "Sorceress", "level": 80, "source": "declared", "at": "2026-09-26T00:00:00Z"}


def _v(builds=BUILDS, main="b1", vault=VAULT_MAIN):
    """the verdict over stores as the board keeps them (JSON strings; None = the key is absent)"""
    b = builds if (builds is None or isinstance(builds, str)) else json.dumps(builds)
    v = vault if (vault is None or isinstance(vault, str)) else json.dumps(vault)
    return CD.characters_room_verdict(b, main, v)


class TheVerdictOverHisStores(unittest.TestCase):

    def test_an_absent_or_empty_store_is_measured_empty_never_unread(self):
        for raw in (None, ""):
            st, why = _v(builds=raw, main=None, vault=None)
            self.assertEqual(st, CD.OK, "an absent store read %s: %s" % (st, why))
            self.assertIn("0 builds", why)
            self.assertIn("empty, not unread", why)
            self.assertNotIn("UNKNOWN and refuses", why)

    def test_an_unparseable_store_is_missing_and_says_unknown_never_zero(self):
        st, why = _v(builds='{"b1": {"name": "Konyoress"', main=None, vault=None)
        self.assertEqual(st, CD.MISSING, "an unparseable store read %s: %s" % (st, why))
        self.assertIn("d2r_charBuilds", why)
        self.assertIn("UNKNOWN", why)
        self.assertIn("refuses every write", why)
        self.assertNotIn("0 build", why, "an unreadable store must never read as 0 builds: %s" % why)
        st2, why2 = _v(builds='["not", "a", "set"]', main=None, vault=None)
        self.assertEqual(st2, CD.MISSING, "a list read %s: %s" % (st2, why2))
        self.assertIn("not a set of builds", why2)

    def test_a_dangling_main_is_missing_and_names_the_id(self):
        st, why = _v(main="gone")
        self.assertEqual(st, CD.MISSING, "a dangling MAIN read %s: %s" % (st, why))
        self.assertIn("'gone'", why)
        self.assertIn("2 saved builds", why, "PRINT THE DENOMINATOR: %s" % why)
        self.assertIn("Set as MAIN", why)
        # an empty store with a pointer is dangling too
        st2, why2 = _v(builds=None, main="b1", vault=None)
        self.assertEqual(st2, CD.MISSING, "a pointer over an empty store read %s: %s" % (st2, why2))
        self.assertIn("0 saved builds", why2)

    def test_a_healthy_store_is_ok_with_its_count_and_main(self):
        st, why = _v(main=None, vault=None)
        self.assertEqual((st, "2 builds" in why, "none marked" in why), (CD.OK, True, True), why)
        self.assertIn("no name yet", why, "a vault MAIN with no name is said, never guessed: %s" % why)
        st1, why1 = _v(builds={"b1": BUILDS["b1"]}, main="b1", vault=None)
        self.assertEqual(st1, CD.OK, why1)
        self.assertIn("1 build ·", why1)
        self.assertIn("★ MAIN Konyoress", why1)

    def test_rank_13_two_mains_naming_different_characters_is_named_both_ways(self):
        """★ MAIN is the Hammerdin, the vault's MAIN is Konyoress: OK, both names, and what the lock follows.
        REG-1553 — never MISSING: a build is named '<Class> build' by the planner and the vault's MAIN is a typed
        character name, so the two differ on his first real use; a red he is told to leave carries nothing."""
        st, why = _v(main="b2")
        self.assertEqual(st, CD.OK, "two MAINs naming different characters went red (REG-1553): %s" % why)
        self.assertIn("Hammerdin", why)
        self.assertIn("Konyoress", why)
        self.assertIn("locks no gear", why)
        self.assertIn("d2r_mainCharacter", why)
        self.assertIn("lock panel", why, "the row must name the door that changes it: %s" % why)
        self.assertIn("two stores under one word", why, "the row does not say the two are different stores: %s" % why)
        self.assertNotIn("also the vault's MAIN", why, "two names read as one character: %s" % why)
        # the same character under both words is OK, and says so — the BASELINE that the two sentences differ
        st2, why2 = _v(main="b1")
        self.assertEqual(st2, CD.OK, why2)
        self.assertIn("also the vault's MAIN", why2)
        self.assertNotIn("two stores under one word", why2)
        # case never makes a disagreement
        st3, why3 = _v(main="b1", vault=dict(VAULT_MAIN, name="konyoress"))
        self.assertEqual(st3, CD.OK, "a case difference read as two characters: %s" % why3)
        # a vault MAIN that will not parse is no name, never a disagreement
        st4, why4 = _v(main="b2", vault="{bad")
        self.assertEqual(st4, CD.OK, why4)
        self.assertIn("no name yet", why4)


class TheLiveRowReadsTheBoardOnce(unittest.TestCase):

    def _with_board(self, got):
        real = CD._board_read
        CD._board_read = lambda: got
        try:
            return CD._check_the_characters_room()
        finally:
            CD._board_read = real

    def test_no_console_a_refusal_and_no_stores_are_each_unknown_never_zero(self):
        for got, tell in ((None, "did not answer"), ({"ok": False, "why": "closed"}, "refused"),
                          ({"ok": True}, "carried no stores")):
            st, why = self._with_board(got)
            self.assertEqual(st, CD.UNKNOWN, "board=%r read %s: %s" % (got, st, why))
            self.assertIn(tell, why)
            self.assertIn("UNKNOWN, not 0", why)

    def test_with_stores_the_row_answers_the_verdict_over_the_same_three_keys(self):
        fs = {"d2r_charBuilds": json.dumps(BUILDS), "d2r_cbMain": "b2", "d2r_mainCharacter": json.dumps(VAULT_MAIN),
              "d2r_muleAssign": "{}"}
        st, why = self._with_board({"ok": True, "fullStores": fs})
        self.assertEqual((st, why), CD.characters_room_verdict(fs["d2r_charBuilds"], fs["d2r_cbMain"], fs["d2r_mainCharacter"]))
        self.assertEqual(st, CD.OK, why)   # REG-1553 — two names are said, never red
        self.assertIn("Hammerdin", why)
        self.assertIn("Konyoress", why)
        ok, okwhy = self._with_board({"ok": True, "fullStores": {"d2r_charBuilds": json.dumps(BUILDS), "d2r_cbMain": "b1"}})
        self.assertEqual(ok, CD.OK, okwhy)
        self.assertIn("2 builds", okwhy)


class TheRowIsRegisteredAndExplained(unittest.TestCase):

    def test_the_row_is_in_checks_watches_and_the_corroborators_registry(self):
        names = [n for n, _fn in CD.CHECKS]
        self.assertIn(ROW, names, "the doctor never asks the row: CHECKS lacks %r" % ROW)
        fn = dict(CD.CHECKS)[ROW]
        self.assertIs(fn, CD._check_the_characters_room, "CHECKS names the row but runs another function")
        self.assertIn(ROW, CD.WATCHES, "the row is not declared in WATCHES (test_no_check_is_missing_from_WATCHES)")
        self.assertIn(ROW, C.NO_JOINT_YET, "no registry line says why the row has no corroborator")
        self.assertIn("hand", C.NO_JOINT_YET[ROW], "the stated reason must name his hand as the only witness")
        cov = C.coverage()
        self.assertTrue(cov.get("ok"), cov)
        self.assertIn(ROW, cov["uncovered"], "coverage() does not file the row as uncovered-with-a-reason")
        self.assertNotIn(ROW, cov["unexplained"], "coverage() files the row as UNEXPLAINED")


NODE = None
try:
    import test_the_characters_tab_is_manual_and_separate as ROOM  # noqa: E402
    NODE = ROOM.NODE
except Exception:
    ROOM = None


@unittest.skipIf(NODE is None, "node is absent - the rendered button was not driven; UNMEASURED, not passing")
class TheButtonSaysWhatItDoesNotDo(unittest.TestCase):

    def test_set_as_main_says_it_locks_no_gear_and_so_does_the_help(self):
        out = ROOM._run(r"""
          seed('bDRU'); window.renderCharsTab();
          var h = card('bHAM').html, m = /<button[^>]*data-act="main"[^>]*>/.exec(h);
          OUT.btn = m ? m[0] : null;
          OUT.title = m ? (/title="([^"]*)"/.exec(m[0]) || [])[1] || null : null;
          RAW['d2r_charBuilds'] = '{}'; delete RAW['d2r_cbMain']; window.renderCharsTab();
          OUT.help = ELS['chars-list']._html;
        """)
        self.assertIsNotNone(out["btn"], "the card renders no ★ Set as MAIN button")
        self.assertTrue(out["title"], "the ★ Set as MAIN button carries no sentence: %s" % out["btn"])
        for w in ("does not lock gear", "Vault", "lock panel"):
            self.assertIn(w, out["title"], "the button's sentence does not say what the lock follows: %r" % out["title"])
        self.assertIn("does not lock gear", out["help"], "the empty room's help copy does not say it")
        self.assertIn("lock panel", out["help"])


RED_PROOF = [
    {
        "why": "REG-1553 - two MAINs naming different characters go MISSING again (a red he is told to leave)",
        "file": "console_doctor.py",
        "find": "        return OK, (\"%d build%s · ★ MAIN %s · the vault's MAIN is %s — two stores under one word: ★ MAIN locks no gear, the \"\n",
        "replace": "        return MISSING, (\"%d build%s · ★ MAIN %s · the vault's MAIN is %s — two stores under one word: ★ MAIN locks no gear, the \"\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 12 - an unparseable d2r_charBuilds reads as a measured-empty store (0 builds)",
        "file": "console_doctor.py",
        "find": "        except Exception as e:\n            return MISSING, (\"d2r_charBuilds would not parse (%s) — the 👤 Characters room reads UNKNOWN and refuses every \"\n",
        "replace": "        except Exception as e:\n            builds = {}\n        if False:\n            return MISSING, (\"d2r_charBuilds would not parse (%s) — the 👤 Characters room reads UNKNOWN and refuses every \"\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 12 - a d2r_cbMain naming no saved build reads like no MAIN set",
        "file": "console_doctor.py",
        "find": "    if main_id is not None and main_id not in builds:\n",
        "replace": "    if main_id is not None and main_id not in builds:\n        main_id = None\n    if False:\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 13 - two MAINs naming different characters go unsaid",
        "file": "console_doctor.py",
        "find": "    if vault_name and main_name.lower() != vault_name.lower():\n",
        "replace": "    if vault_name and main_name.lower() != vault_name.lower() and False:\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 12 - the doctor never asks the row (dropped from CHECKS)",
        "file": "console_doctor.py",
        "find": "    (\"characters room\", _check_the_characters_room),\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#41 rank 12 - the live row answers 0 builds when the console did not answer",
        "file": "console_doctor.py",
        "find": "    if not got:\n        return UNKNOWN, \"the console did not answer — nobody asked the board, so his builds are UNKNOWN, not 0\"\n",
        "replace": "    if not got:\n        return OK, \"no builds yet (0 builds — the store is empty, not unread) · the vault's MAIN has no name yet\"\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 12 - the corroborator's registry no longer says why the row has no joint",
        "file": "corroborate.py",
        "find": "    'characters room': 'the row reads d2r_charBuilds and d2r_cbMain, which the 👤 room and the planner write from his '\n",
        "replace": "    'characters room ': 'the row reads d2r_charBuilds and d2r_cbMain, which the 👤 room and the planner write from his '\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 13 - the ★ Set as MAIN button loses its sentence",
        "file": "bible.html",
        "find": " title=\"' + SAY_MAIN + '\" onclick=\"window._charsSetMain(",
        "replace": " onclick=\"window._charsSetMain(",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
