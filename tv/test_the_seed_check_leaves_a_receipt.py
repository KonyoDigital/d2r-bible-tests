# -*- coding: utf-8 -*-
"""#159 — the seed's check against his board leaves a dated receipt, and a row reads its age.

⚠⚠ WHAT IT COST BEFORE THIS EXISTED: bake_seed.py answered "no drift — the shipped seed already
matches his board" to stdout and left nothing behind, so nothing on his console could say WHEN the
seed was last checked, and a heart row had nothing to read. [[stale-reading]] §4.
Every case points TV_BAKE_RECEIPT at a temp file — never his live receipt. RED_PROOF below.
"""
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

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as cd   # noqa: E402

NAME = "the seed was checked against his board"


class TheSeedCheckLeavesAReceipt(unittest.TestCase):

    def setUp(self):
        self._d = tempfile.mkdtemp(prefix="seed-receipt-")
        self._p = os.path.join(self._d, "receipt.json")
        self._env = os.environ.get("TV_BAKE_RECEIPT")
        os.environ["TV_BAKE_RECEIPT"] = self._p

    def tearDown(self):
        if self._env is None:
            os.environ.pop("TV_BAKE_RECEIPT", None)
        else:
            os.environ["TV_BAKE_RECEIPT"] = self._env
        shutil.rmtree(self._d, ignore_errors=True)

    def _row(self, rec=None, days_ago=0.0):
        if rec is not None:
            rec = dict(rec, ts=int((time.time() - days_ago * 86400) * 1000))
            io.open(self._p, "w", encoding="utf-8").write(json.dumps(rec))
        return dict(cd.CHECKS)[NAME]()

    def test_no_receipt_is_UNKNOWN_never_fine(self):
        st, why = self._row()
        self.assertEqual(st, cd.UNKNOWN, why)

    def test_a_fresh_no_drift_check_is_OK_and_says_how_old(self):
        st, why = self._row({"outcome": "no-drift", "boardSetPieces": 133, "boardFoundLog": 445})
        self.assertEqual(st, cd.OK, why)
        self.assertIn("day(s) ago", why)

    def test_drift_is_MISSING_and_names_the_bake(self):
        st, why = self._row({"outcome": "drift", "drift": 4, "mode": "report"})
        self.assertEqual(st, cd.MISSING, why)
        self.assertIn("bake", why)

    def test_an_old_check_no_longer_speaks_for_now(self):
        st, why = self._row({"outcome": "no-drift"}, days_ago=cd._SEED_CHECK_STALE_DAYS + 1)
        self.assertEqual(st, cd.UNMEASURED, why)

    def test_a_check_that_could_not_read_his_board_is_UNKNOWN(self):
        st, why = self._row({"outcome": "no-store"})
        self.assertEqual(st, cd.UNKNOWN, why)

    def test_the_baker_writes_a_receipt_even_when_it_cannot_read_the_board(self):
        import bake_seed as B
        empty = tempfile.mkdtemp(prefix="no-webkit-")
        try:
            rc = B.bake(write=False, root=empty)
        finally:
            shutil.rmtree(empty, ignore_errors=True)
        self.assertEqual(rc, 2)
        self.assertTrue(os.path.exists(self._p), "the baker ran and left NO receipt")
        self.assertEqual(json.load(io.open(self._p))["outcome"], "no-store")

    def test_a_no_drift_check_leaves_a_no_drift_receipt(self):
        """DRIVEN down the path the BLIND proof named: a board whose ledger holds only a name the
        shipped seed already carries is zero drift — report mode, nothing written to bible.html."""
        import sqlite3
        import bake_seed as B
        src = io.open(B.BIBLE, encoding="utf-8").read()
        grail, _m = B._lit(src, "_GRAIL_SEED")
        self.assertTrue(grail, "the shipped grail seed is empty, so no-drift cannot be staged")
        name, date = sorted(grail.items())[0]
        root = tempfile.mkdtemp(prefix="nodrift-")
        try:
            d = os.path.join(root, "o" * 8, "o" * 8, "LocalStorage")
            os.makedirs(d)
            con = sqlite3.connect(os.path.join(d, "localstorage.sqlite3"))
            con.execute("CREATE TABLE ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB)")
            for k, v in (("d2r_foundLog", json.dumps({name: date or "Jan 1, 2026"})),
                         ("d2r_setPieces", json.dumps([]))):
                con.execute("INSERT INTO ItemTable VALUES (?,?)", (k, v.encode("utf-16-le")))
            con.commit(); con.close()
            before = io.open(B.BIBLE, encoding="utf-8").read()
            rc = B.bake(write=False, root=root)
            self.assertEqual(io.open(B.BIBLE, encoding="utf-8").read(), before, "a REPORT wrote bible.html")
        finally:
            shutil.rmtree(root, ignore_errors=True)
        self.assertEqual(rc, 0, "a ledger of already-seeded names was not zero drift")
        self.assertEqual(json.load(io.open(self._p))["outcome"], "no-drift",
                         "the no-drift run left no no-drift receipt")

    def test_it_is_registered_where_the_console_reads_it(self):
        import corroborate as C
        import run_gates as RG
        self.assertIn(NAME, dict(cd.CHECKS))
        self.assertIn(NAME, cd.WATCHES)
        self.assertIn(NAME, cd.MINE)
        self.assertIn(NAME, cd.PERIODIC)
        self.assertIn(NAME, C.NO_JOINT_YET)
        self.assertIn(".bake_seed_receipt.json", RG._LIVE_STATE)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the no-drift receipt no longer written: the verdict is printed and gone again",
        "file": "bake_seed.py",
        "find": "        write_receipt(\"no-drift\", **_facts)\n",
        "replace": "        pass\n",
        "matches": 1,
    },
    {
        "why": "the no-store path leaves nothing: a run that could not read his board is invisible",
        "file": "bake_seed.py",
        "find": "        write_receipt(\"no-store\", mode=(\"write\" if write else \"report\"))\n",
        "replace": "        pass\n",
        "matches": 1,
    },
    {
        "why": "drift read as fine: a bake that is owed never reaches anyone",
        "file": "console_doctor.py",
        "find": "    if out == \"drift\":\n        return MISSING, (",
        "replace": "    if out == \"drift\":\n        return OK, (",
        "matches": 1,
    },
    {
        "why": "an old check read as current: a verdict with no expiry",
        "file": "console_doctor.py",
        "find": "    if age > _SEED_CHECK_STALE_DAYS:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
]
