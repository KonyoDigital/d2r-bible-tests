# -*- coding: utf-8 -*-
"""#238 (REG-2038) - A RETIRED REEL IS COUNTED ONCE, IS NOT "WAITING", AND AN UNREADABLE RECORD STARTS NOTHING.

The #231 eye on 00e3efbe (v3595) named three things about the chronicle's older-seal tail; reproduced against the
shipped functions on 2026-10-08:
  1. a retired never-swept reel is on the retention plan's never-chronicle-swept list AND in
     _chron_retired_still_owing, so `owed - waiting - retired` subtracted it twice and the clamp at 0 dropped real reels
     from the "will be re-read" promise - and the waiting count passed in also held VAULT-lane reels, which are not in
     the chronicle's owed count at all;
  2. that reel read "waiting on a sweep" while the tick skips it;
  3. an unreadable retirement record made _chron_reels_retired() answer {} (uncached), so the next tick could restart a
     reel the v1766.1 bound gave up on, while the tail said "none are promised a re-read".
Nothing here deletes a reel, starts a sweep, or reads his shelf.
"""
import copy
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

import control_app as ca  # noqa: E402


class ARetiredReelIsCountedOnce(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="retired-once-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self._hist = os.environ.get("TV_HIST")
        self._swept = os.environ.get("TV_CHRON_SWEPT")
        self._path = ca._CHRON_AUTOREAD_PATH
        self._auto = copy.deepcopy(dict(ca._CHRON_AUTOREAD))
        self._owes = ca._chron_reel_owes_a_read
        self._state = ca.chronicle_sweep_state
        os.environ["TV_HIST"] = self.tmp
        os.environ["TV_CHRON_SWEPT"] = os.path.join(self.tmp, "chronicle_swept.json")
        ca._CHRON_AUTOREAD_PATH = os.path.join(self.tmp, "chron_autoread.json")
        ca._CHRON_AUTOREAD["retired"] = {}
        self.owing = set()
        ca._chron_reel_owes_a_read = lambda rid, mem=None, prompt_ver=None: rid in self.owing
        ca.chronicle_sweep_state = lambda *a, **k: {"running": False}
        self.addCleanup(self._restore)

    def _restore(self):
        ca._CHRON_AUTOREAD_PATH = self._path
        ca._chron_reel_owes_a_read = self._owes
        ca.chronicle_sweep_state = self._state
        ca._CHRON_AUTOREAD.clear()
        ca._CHRON_AUTOREAD.update(self._auto)
        for k, v in (("TV_HIST", self._hist), ("TV_CHRON_SWEPT", self._swept)):
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _reel(self, name):
        d = os.path.join(self.tmp, name)
        os.makedirs(d)
        with open(os.path.join(d, "f_1.jpg"), "wb") as fh:
            fh.write(b"\xff\xd8\xff\xd9")
        return name

    def test_the_retired_reels_are_named_by_id(self):
        a = self._reel("reel_s_1780000000001_a")
        b = self._reel("reel_s_1780000000002_b")
        c = self._reel("reel_s_1780000000003_c")
        self.owing = {a, b}
        ca._CHRON_AUTOREAD["retired"] = {a: {"why": "gave up", "tries": 2}, c: {"why": "gave up", "tries": 2}}
        self.assertEqual(ca._chron_retired_owing_ids(), {a}, "only a retired reel that still owes is named")
        self.assertEqual(ca._chron_retired_still_owing(), 1)

    def test_a_retired_reel_is_not_waiting_and_the_tail_counts_it_once(self):
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertEqual(src.count('        _w_chron = [k for k in _w_chron if str(k.get("reel") or "") not in _ret_ids]\n'),
                         1, "a retired reel is still listed as waiting on a sweep")
        self.assertEqual(src.count("            _tail = _chron_older_seal_tail(len(_w_chron), _owed)\n"), 1,
                         "the tail is handed a waiting count that is not the chronicle's")
        # the arithmetic, on disjoint inputs: 1 waiting + 1 retired + 1 older seal = 3 owed
        a = self._reel("reel_s_1780000000001_a")
        self._reel("reel_s_1780000000002_b")
        self.owing = {a, "reel_s_1780000000002_b"}
        ca._CHRON_AUTOREAD["retired"] = {a: {"why": "gave up", "tries": 2}}
        tail = ca._chron_older_seal_tail(1, 3)
        self.assertIn("1 more were sealed by an older reader and will be re-read", tail, tail)
        self.assertIn("1 retired after a refusal", tail, tail)

    def test_an_unreadable_retirement_record_starts_no_reel(self):
        a = self._reel("reel_s_1780000000001_a")
        self.owing = {a}
        with open(ca._CHRON_AUTOREAD_PATH, "w") as fh:
            fh.write("{ not json")
        ca._CHRON_AUTOREAD["retired"] = None
        out = ca.chronicle_autoreel_tick()
        self.assertFalse(out.get("ok"), out)
        self.assertIn("retirement record could not be read", str(out.get("why")), out)
        self.assertNotIn(a, (ca._CHRON_AUTOREAD.get("tries") or {}), "a try was spent on a reel while the record was unreadable")


RED_PROOF = [
    {"why": "REG-2038 - a retired reel is listed as waiting on a sweep again",
     "file": "control_app.py",
     "find": "    if _ret_ids:\n        _w_chron = [k for k in _w_chron if str(k.get(\"reel\") or \"\") not in _ret_ids]\n",
     "replace": "    if False:\n        _w_chron = [k for k in _w_chron if str(k.get(\"reel\") or \"\") not in _ret_ids]\n",
     "matches": 1},
    {"why": "REG-2038 - an unreadable retirement record lets the tick start a reel again",
     "file": "control_app.py",
     "find": "    if _chron_retirement_map() is None:\n        return {\"ok\": False, \"why\": \"the retirement record could not be read",
     "replace": "    if False:\n        return {\"ok\": False, \"why\": \"the retirement record could not be read",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
