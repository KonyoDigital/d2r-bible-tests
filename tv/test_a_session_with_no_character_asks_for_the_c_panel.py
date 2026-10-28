# -*- coding: utf-8 -*-
"""#36 (REG-2909) - A SESSION THE BOARD CANNOT NAME ASKS HIM, IN HIS WORDS: "session N: character UNKNOWN - open the C panel once".

His rule: a doubt becomes a guided ask. REG-2906 gives each session the character its own screens named (character
select, the lobby, the C panel); a session none of them named is UNKNOWN, and every look in it reads holder UNKNOWN on
the vault (REG-2908). Nothing said so: the doctor had no row. Now 'which character each session is on' reads the newest
session on this PC: OK naming its character, how it is known and how many of the last sessions are named; MISSING with
the ask when the newest session names nobody - and the ask says what is true today: no pixel band finds the C panel yet
(no C-panel frame was ever filmed), so picking the character at character select names the session too; UNKNOWN when the
ledger or the reel folder cannot be read - never "0 sessions". The rule is pure (session_character_verdict) and the live
row drives it over a fixture ledger and reel tree; the registries carry the row. RED_PROOF below.
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import console_doctor as CD  # noqa: E402
import corroborate as C  # noqa: E402
import char_select as CS  # noqa: E402

ROW = "which character each session is on"
T0 = 1792800000000
R = ["reel_s_%d" % (T0 + i * 3600000) for i in range(4)]


def _sid(r):
    return r[5:]


class TheVerdict(unittest.TestCase):

    def test_an_unreadable_ledger_is_unknown_never_none(self):
        st, say = CD.session_character_verdict(None, R)
        self.assertEqual(st, CD.UNKNOWN, say)

    def test_no_reel_is_measured_empty(self):
        st, say = CD.session_character_verdict({}, [])
        self.assertEqual(st, CD.OK, say)
        self.assertIn("0 reels", say)

    def test_the_newest_session_with_no_character_asks_in_his_words(self):
        s = {_sid(R[0]): [{"from": T0, "character": "Konyolock", "via": "char-select"}]}
        st, say = CD.session_character_verdict(s, R)
        self.assertEqual(st, CD.MISSING, say)
        self.assertTrue(say.startswith("session %s: character UNKNOWN - open the C panel once" % _sid(R[3])), say)
        self.assertIn("1 of the last 4 sessions name their character", say)
        self.assertIn("character select", say, "the ask hides that no pixel band finds the C panel yet")

    def test_a_span_two_screens_disagreed_on_is_unknown_too(self):
        s = {_sid(R[3]): [{"from": None, "why": "two screens in one span named different characters"}]}
        st, say = CD.session_character_verdict(s, R)
        self.assertEqual(st, CD.MISSING, say)

    def test_a_named_newest_session_is_ok_and_says_how(self):
        s = {_sid(R[3]): [{"from": None, "character": "Konyolock", "via": "lobby"},
                          {"from": T0 + 3 * 3600000 + 9, "character": "Konyodin", "via": "char-select"}],
             _sid(R[2]): [{"from": None, "character": "Konyolock", "via": "carried"}]}
        st, say = CD.session_character_verdict(s, R)
        self.assertEqual(st, CD.OK, say)
        self.assertIn("session %s: Konyodin (char-select)" % _sid(R[3]), say, "the row names the span before the newest")
        self.assertIn("2 of the last 4", say)


class TheLiveRow(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="sess-doc-")
        for r in R:
            os.makedirs(os.path.join(self.root, r))
        self.orig = (CS.load, CS.hist_root)

    def tearDown(self):
        CS.load, CS.hist_root = self.orig
        shutil.rmtree(self.root, ignore_errors=True)

    def _led(self, newest_named):
        visits = {"L": {"reel": R[3 if newest_named else 1], "ts": T0 + 5,
                        "sel": [{"name": "Konyolock", "ts": T0 + 3 * 3600000 + 5, "reader": "vision"}]}}
        return {"visits": visits, "chars": {}}

    def test_the_row_asks_when_the_newest_session_names_nobody(self):
        CS.load, CS.hist_root = (lambda: self._led(False)), (lambda: self.root)
        st, say = CD._check_which_character_each_session_is_on()
        self.assertEqual(st, CD.MISSING, say)
        self.assertIn("open the C panel once", say)

    def test_the_row_names_the_character_it_read(self):
        CS.load, CS.hist_root = (lambda: self._led(True)), (lambda: self.root)
        st, say = CD._check_which_character_each_session_is_on()
        self.assertEqual(st, CD.OK, say)
        self.assertIn("Konyolock", say)

    def test_an_unreadable_ledger_or_reel_folder_is_unknown(self):
        CS.load, CS.hist_root = (lambda: None), (lambda: self.root)
        self.assertEqual(CD._check_which_character_each_session_is_on()[0], CD.UNKNOWN)
        CS.load, CS.hist_root = (lambda: self._led(True)), (lambda: os.path.join(self.root, "gone"))
        self.assertEqual(CD._check_which_character_each_session_is_on()[0], CD.UNKNOWN)


class TheRegistries(unittest.TestCase):

    def test_the_row_is_asked_declared_and_explained(self):
        self.assertIn(ROW, [n for n, _ in CD.CHECKS])
        self.assertIn(ROW, CD.WATCHES)
        self.assertIn(ROW, C.NO_JOINT_YET)
        self.assertNotIn(ROW, CD.MINE, "the ask is his to act on, so the row counts as his")
        self.assertNotIn(ROW, CD.BY_DESIGN)


RED_PROOF = [
    {"why": "REG-2909 - an unreadable ledger reads as no session to name",
     "file": "console_doctor.py",
     "find": "    if sessions is None:\n        return UNKNOWN, (\"which character each session is on is UNKNOWN",
     "replace": "    if sessions is None:\n        sessions = {}\n    if False:\n        return UNKNOWN, (\"which character each session is on is UNKNOWN",
     "matches": 1},
    {"why": "REG-2909 - a session nobody named is OK (no ask)",
     "file": "console_doctor.py",
     "find": "        return MISSING, (\"session %s: character UNKNOWN - %s (%s; \"\n",
     "replace": "        return OK, (\"session %s: character UNKNOWN - %s (%s; \"\n",
     "matches": 1},
    {"why": "REG-2909 - the ask hides that no pixel band finds the C panel",
     "file": "console_doctor.py",
     "find": "SESSION_ASK_TAIL = ",
     "replace": "SESSION_ASK_TAIL_X = \"\"\nSESSION_ASK_TAIL = \"\" and ",
     "matches": 1},
    {"why": "REG-2909 - the row names the first span, not the one he is on now",
     "file": "console_doctor.py",
     "find": "        return sp[-1].get(\"character\"), sp[-1].get(\"via\")\n",
     "replace": "        return sp[0].get(\"character\"), sp[0].get(\"via\")\n",
     "matches": 1},
    {"why": "REG-2909 - the doctor never asks the row",
     "file": "console_doctor.py",
     "find": "    (\"which character each session is on\", _check_which_character_each_session_is_on),\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2909 - an unlisted reel folder reads as no session",
     "file": "console_doctor.py",
     "find": "        return UNKNOWN, \"this PC's reel folder could not be listed - which sessions exist is UNKNOWN, not 0\"\n",
     "replace": "        return session_character_verdict(sessions, [])\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
