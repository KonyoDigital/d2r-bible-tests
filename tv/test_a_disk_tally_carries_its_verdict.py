# -*- coding: utf-8 -*-
"""REG-1907 - A TALLY READ OFF DISK IS STILL ASKED OF THE LEDGER AUTHORITY.

The testing-phase pre-run (FLEET-01, 2026-10-07) read live /api/fleet: the ALT ("Konyo ALT TEST", v3600, on air)
sent tally.measured null, measuredBy null and NO ledgerVerdict, while GrokBot on the same build sent a full verdict -
so the card's never-synced RUNEWORDS 0 printed as "0 / 99", the doc's listed fail. Two halves, never joined:

  * the board persists its tally without the one flag the authority classifies by (onOwnerSeed - the live read
    sends window._seedsBelongHere, the persisted copy did not), and the POST route whitelists fields, so even a
    board that sent it would have had it dropped;
  * _tally_from_board_store sealed without a world, so classify_row was never asked at all.

The law: a disk tally carrying onOwnerSeed False is classified per ledger (a 0 is UNSYNCED, a count is SYNCED, and
measuredBy says so for the card); a record written before the fix still carries a verdict, which says UNKNOWN per
ledger - never a cheerful default; the route banks a bool and drops anything else; the board writes the flag.
Fixtures only: board_tally_load and the WebKit store list are stubbed, nothing reads his stores.
"""
import io
import json
import os
import sys
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as CA  # noqa: E402

WHO = {"id": "fixture-install-1", "p": "main", "pfx": ""}


def _banked(onOwnerSeed="absent"):
    t = {"v": 1, "who": dict(WHO), "route": dict(WHO), "at": 1790000000000,
         "sets": {"have": 2, "total": 135}, "uniques": {"have": 4, "total": 403},
         "runewords": {"have": 0, "total": 99}}
    if onOwnerSeed != "absent":
        t["onOwnerSeed"] = onOwnerSeed
    return t


def _read(banked):
    with mock.patch.object(CA, "board_tally_load", lambda: banked), \
         mock.patch.object(CA, "_webkit_localstorage_dbs", lambda: []):
        return CA._tally_from_board_store()


def _prov(out):
    return dict((r.get("ledger"), r.get("provenance")) for r in (out.get("ledgerVerdict") or {}).get("ledgers") or [])


class ADiskTallyCarriesItsVerdict(unittest.TestCase):

    def test_a_never_synced_zero_read_off_disk_is_UNSYNCED_not_a_count(self):
        out = _read(_banked(onOwnerSeed=False))
        self.assertIsNotNone(out, "the banked tally was not read at all - the case reached nothing")
        self.assertIn("ledgerVerdict", out, "a tally read off disk carries no verdict (REG-1907): %s" % out)
        p = _prov(out)
        self.assertEqual(p.get("runewords"), "UNSYNCED", p)
        self.assertEqual(p.get("sets"), "SYNCED", p)
        self.assertEqual(p.get("uniques"), "SYNCED", p)
        self.assertIs((out.get("measuredBy") or {}).get("runewords"), False,
                      "the card is not told the runewords 0 is no count: %s" % out.get("measuredBy"))
        self.assertIs((out.get("measuredBy") or {}).get("sets"), True)
        self.assertEqual(out["runewords"]["have"], 0, "the figure itself was altered")

    def test_a_record_from_before_the_fix_says_UNKNOWN_never_a_default(self):
        out = _read(_banked())
        self.assertIn("ledgerVerdict", out)
        self.assertIsNone(out.get("onOwnerSeed"))
        for k, v in _prov(out).items():
            self.assertNotIn(v, ("SYNCED", "SEEDED", "MANUAL"),
                             "an old disk record with no seed flag was called %s for %s" % (v, k))

    def test_a_junk_seed_flag_is_not_believed(self):
        out = _read(_banked(onOwnerSeed="false"))
        self.assertIsNone(out.get("onOwnerSeed"), "a string was taken as the seed flag")


class TheRouteAndTheBoardCarryTheFlag(unittest.TestCase):

    def setUp(self):
        self.src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.page = io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8").read()

    def test_the_route_banks_a_bool_and_nothing_else(self):
        line = ('"onOwnerSeed": body.get("onOwnerSeed") if isinstance(body.get("onOwnerSeed"), bool) else None,')
        self.assertEqual(self.src.count(line), 1, "the tally POST route does not bank the seed flag, so a board that "
                                                  "sends it still reaches the disk without it")

    def test_the_board_persists_the_same_flag_the_live_read_sends(self):
        expr = "onOwnerSeed: (typeof window._seedsBelongHere === 'boolean' ? window._seedsBelongHere : null),"
        self.assertEqual(self.page.count(expr), 1, "bible.html's persisted tally does not carry onOwnerSeed")
        live = "onOwnerSeed:(typeof window._seedsBelongHere==='boolean'?window._seedsBelongHere:null)"
        self.assertEqual(self.src.count(live), 1, "the live read's expression moved - the two must stay one rule")


RED_PROOF = [
    {
        "why": "REG-1907 - the disk tally is sealed without a world again: no verdict travels and the ALT's "
               "never-synced 0 prints as a count",
        "file": "tv/control_app.py",
        "find": "            out, \"the board has written a tally but it carries no counts\", world=route)",
        "replace": "            out, \"the board has written a tally but it carries no counts\")",
        "matches": 1,
    },
    {
        "why": "REG-1907 - the disk tally drops the seed flag it carries, so every ledger reads UNKNOWN and the 0 is "
               "still a count",
        "file": "tv/control_app.py",
        "find": "        out[\"onOwnerSeed\"] = _oos if isinstance(_oos, bool) else None\n",
        "replace": "        out[\"onOwnerSeed\"] = None\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
