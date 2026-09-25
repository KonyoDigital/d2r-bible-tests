# -*- coding: utf-8 -*-
"""#174 — THE SAVE READER SHIPS WITH ITS DOCTOR: STALE TABLES READ MISSING, NO INSTALL READS UNKNOWN.

tv/d2s_read.py decodes a .d2s against tv/item_tables.json, generated once from his install. A game patch that moves a
stat's Save Bits makes every later import decode WRONG while each row still looks like an item. The doctor row
"save reader tables" re-derives the tables' sourceHash and compares - built WITH the reader (heart-first), not after.

  · DRIVEN: the real row, with the verifier made to answer fresh / stale / cannot-tell: OK / MISSING / UNKNOWN.
  · JOINED: the row is registered, periodic (it re-derives from a 28 GB install), and declared in WATCHES.
RED_PROOF below.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as D  # noqa: E402
import item_tables as IT  # noqa: E402


class TheSaveReaderWatchesItsTables(unittest.TestCase):

    def _run(self, answer):
        real = IT.verify
        IT.verify = lambda: answer
        try:
            return D._check_the_save_reader_matches_the_install()
        finally:
            IT.verify = real

    def test_fresh_tables_are_ok(self):
        self.assertEqual(self._run((0, "item tables match the install"))[0], D.OK)

    def test_stale_tables_are_missing(self):
        st, why = self._run((1, "the install has changed since the item tables were generated"))
        self.assertEqual(st, D.MISSING, "a patched install still reads as a working save reader")
        self.assertIn("last patch", why)

    def test_no_install_is_unknown_never_ok(self):
        self.assertEqual(self._run((getattr(IT, "SKIP", 77), "cannot re-derive here"))[0], D.UNKNOWN)

    def test_the_row_is_registered_periodic_and_declared(self):
        self.assertIn("save reader tables", dict(D.CHECKS))
        self.assertIn("save reader tables", D.PERIODIC)
        self.assertIn("save reader tables", D.WATCHES)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#174 - stale item tables read as a healthy save reader; every import decodes against old bit widths",
        "file": "console_doctor.py",
        "find": "        return MISSING, say + \" - every .d2s import would decode against last patch's bit widths\"\n",
        "replace": "        return OK, say\n",
        "matches": 1,
    },
]
