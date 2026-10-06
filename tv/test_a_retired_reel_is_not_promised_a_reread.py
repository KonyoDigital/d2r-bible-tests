# -*- coding: utf-8 -*-
"""#86 gap audit 36 (REG-1780) — A RETIRED REEL IS NOT PROMISED A RE-READ.

The above-floor sentence took the chronicle owed count, subtracted the waiting list, and
said that many were sealed by an older reader and will be re-read. A reel retired after a
refusal is inside that owed count. The tick names it and does not start it. Promising it
a re-read was the lie.

  · DRIVEN: two reels owe, one of them retired -> one will be re-read, one will not.
  · DRIVEN: a retirement that does not still owe is not named. None retired keeps the old
    sentence. A waiting list that already covers them says nothing more.
  · DRIVEN: an owed count that was not taken says nothing. A retirement record that will
    not read promises none. A waiting count that will not parse promises none.
  · DRIVEN: the floor sentence he is served asks this clause. It does not keep a second one.
Nothing here deletes a reel, starts a sweep, or reads his shelf. RED_PROOF below.
[[unknown-stays-unknown]]
"""
import copy
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca  # noqa: E402


class ARetiredReelIsNotPromisedAReread(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="reread-promise-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self._hist = os.environ.get("TV_HIST")
        self._swept = os.environ.get("TV_CHRON_SWEPT")
        self._path = ca._CHRON_AUTOREAD_PATH
        self._auto = copy.deepcopy(dict(ca._CHRON_AUTOREAD))
        self._ruled = ca._TRIAGE_RULED_EMPTY.get("chronicle")
        self._owes = ca._chron_reel_owes_a_read
        os.environ["TV_HIST"] = self.tmp
        os.environ["TV_CHRON_SWEPT"] = os.path.join(self.tmp, "chronicle_swept.json")
        ca._CHRON_AUTOREAD_PATH = os.path.join(self.tmp, "chron_autoread.json")
        ca._CHRON_AUTOREAD["retired"] = {}
        self.owing = set()
        ca._chron_reel_owes_a_read = lambda rid, mem=None, prompt_ver=None: rid in self.owing
        self.addCleanup(self._restore)

    def _restore(self):
        ca._CHRON_AUTOREAD_PATH = self._path
        ca._chron_reel_owes_a_read = self._owes
        ca._CHRON_AUTOREAD.clear()
        ca._CHRON_AUTOREAD.update(self._auto)
        ca._TRIAGE_RULED_EMPTY["chronicle"] = self._ruled
        if self._hist is None:
            os.environ.pop("TV_HIST", None)
        else:
            os.environ["TV_HIST"] = self._hist
        if self._swept is None:
            os.environ.pop("TV_CHRON_SWEPT", None)
        else:
            os.environ["TV_CHRON_SWEPT"] = self._swept

    def _reel(self, name):
        d = os.path.join(self.tmp, name)
        os.makedirs(d)
        frame = os.path.join(d, "f_1.jpg")
        with open(frame, "wb") as fh:
            fh.write(b"\xff\xd8\xff\xd9")
        return name

    def test_one_retired_reel_is_not_the_ones_that_will_be_reread(self):
        a = self._reel("reel_s_1780000000001_a")
        b = self._reel("reel_s_1780000000002_b")
        self.owing.update((a, b))
        ca._CHRON_AUTOREAD["retired"] = {a: {"why": "the sweep door was locked", "tries": 2}}
        tail = ca._chron_older_seal_tail(0, ca._chron_owed_count())
        self.assertIn("1 more were sealed by an older reader and will be re-read", tail)
        self.assertIn("1 retired after a refusal and will not be re-read", tail)
        self.assertIn("proved false", tail)
        self.assertNotIn("2 more were sealed", tail)

    def test_a_retirement_that_does_not_still_owe_is_not_named(self):
        a = self._reel("reel_s_1780000000001_a")
        b = self._reel("reel_s_1780000000002_b")
        c = self._reel("reel_s_1780000000003_c")
        self.owing.update((a, b))
        ca._CHRON_AUTOREAD["retired"] = {c: {"why": "done", "tries": 2}}
        tail = ca._chron_older_seal_tail(0, ca._chron_owed_count())
        self.assertEqual(
            tail, " 2 more were sealed by an older reader and will be re-read.")
        self.assertNotIn("will not be re-read", tail)

    def test_none_retired_keeps_the_old_sentence_and_a_covered_list_says_nothing(self):
        a = self._reel("reel_s_1780000000001_a")
        b = self._reel("reel_s_1780000000002_b")
        self.owing.update((a, b))
        owed = ca._chron_owed_count()
        self.assertEqual(
            ca._chron_older_seal_tail(0, owed),
            " 2 more were sealed by an older reader and will be re-read.")
        self.assertEqual(ca._chron_older_seal_tail(owed, owed), "")
        self.assertEqual(ca._chron_older_seal_tail(0, None), "")
        self.assertEqual(ca._chron_older_seal_tail("nope", owed), "")

    def test_an_unreadable_retirement_record_promises_none(self):
        a = self._reel("reel_s_1780000000001_a")
        self.owing.add(a)
        ca._CHRON_AUTOREAD["retired"] = None
        with open(ca._CHRON_AUTOREAD_PATH, "w", encoding="utf-8") as fh:
            fh.write("{")
        tail = ca._chron_older_seal_tail(0, ca._chron_owed_count())
        self.assertIn("could not be read", tail)
        self.assertIn("none are promised a re-read", tail)
        self.assertNotIn("will be re-read", tail)
        self.assertIsNone(ca._CHRON_AUTOREAD.get("retired"))

    def test_the_floor_sentence_asks_this_clause(self):
        """The helper is not a second sentence. The pass he is served asks it."""
        a = self._reel("reel_s_1780000000001_a")
        b = self._reel("reel_s_1780000000002_b")
        self.owing.update((a, b))
        ca._CHRON_AUTOREAD["retired"] = {b: {"why": "locked", "tries": 2}}
        saved = copy.deepcopy(ca._RETENTION)
        self.addCleanup(self._put_back, saved)

        def _usage(_path):
            return type("U", (), {"free": 50 * 10 ** 9})()

        with mock.patch("shutil.disk_usage", _usage), \
                mock.patch("reel_retention.plan", return_value={
                    "ok": True, "kept": [], "candidates": [], "freeMb": 0, "unreadable": []}), \
                mock.patch.object(ca, "disk_history_append", lambda *a, **k: {"at": 1}), \
                mock.patch.object(ca, "_retention_drain", lambda **k: {"state": "CLEAR"}), \
                mock.patch.object(ca, "_vault_positions_and_seals", lambda: ({}, {})), \
                mock.patch.object(ca, "_vault_swept_load", lambda: {}):
            ca._retention_once()
        say = ca._RETENTION.get("say") or ""
        self.assertIn("1 more were sealed by an older reader and will be re-read", say)
        self.assertIn("1 retired after a refusal and will not be re-read", say)
        self.assertNotIn("2 more were sealed", say)
        self.assertEqual(ca._RETENTION.get("owedARead"), 2)

    def _put_back(self, saved):
        ca._RETENTION.clear()
        ca._RETENTION.update(saved)


RED_PROOF = [
    {"why": "REG-1780 - a retired reel that still owes is promised a re-read with the rest",
     "file": "control_app.py",
     "find": "    retired = _chron_retired_still_owing()\n",
     "replace": "    retired = 0\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
