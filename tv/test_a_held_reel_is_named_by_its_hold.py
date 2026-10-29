# -*- coding: utf-8 -*-
"""#193 (REG-3053, measured on his Mac 2026-10-29) - A REEL THE DRAIN HOLDS IS NAMED BY THE DRAIN'S HOLD, NEVER AS ITS DEBT.

After REG-3052 the Mac's river still showed 12 reels "older than the newest 16 - the drain owes them a tombstone". The drain's
own plan() owed none of them: it HELD all 12 (8 panels-never-banked, 4 zero-pages) by rules that wait for his ruling. The
sentence named a debt the drain does not have. The retention pass now keeps the drain's own reason for every reel it holds
(_retention_holds, beside its other words in _RETENTION), and the stuck reader names a held reel with that tag and reason and
when the drain last said so; a reel nobody holds still reads as owed. Measured on his river, read only: every one of the 12
now reads "held by the drain, not owed: N <tag> (<the drain's reason>) - the drain's pass N min ago". Wording only - nothing
here releases a reel.

Driven: _river_stuck_for_wire through its seams with _RETENTION standing in for a pass, _retention_holds on a plan-shaped
fixture, and the pass's own line read from control_app.py - never his river. RED_PROOF below.
"""
import io
import os
import sys
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx  # noqa: E402
_fx.contain()
import control_app as CA  # noqa: E402
import reel_retention as RR  # noqa: E402

T = 1793000000000
DAY = 86400000
NOW = T + 2 * DAY
NEW = ["reel_s_%d_%d" % (T + i * 60000, i) for i in range(1, 17)]
A, B, C = ("reel_s_%d_%d" % (T - n * DAY, 900 + n) for n in (7, 8, 9))
PANELS = "a FULL survey found panel frames here and the vault ledger holds NO row from this reel"
ZERO = "sealed with 0 pages - that is 'this reader found nothing', not 'done'"


def _rows(reels, station):
    return [{"reel": r, "station": station, "at": RR._reel_ts(r)} for r in reels]


def _pass(holds, mins_ago=7):
    return {"holds": holds, "checked": int(time.time() * 1000) - mins_ago * 60000, "say": "nothing is eligible"}


class AHeldReelIsNamedByItsHold(unittest.TestCase):

    def _stuck(self, rows, retention):
        with mock.patch.dict(CA._RETENTION, retention, clear=True):
            return CA._river_stuck_for_wire(NOW, _rows=rows, _shelf=NEW + [A, B, C], _fixtures=(), _remnants=())

    def test_every_reel_held_reads_as_held_with_the_drains_reason_and_its_age(self):
        holds = {A: {"tag": "panels-never-banked", "why": PANELS}, B: {"tag": "panels-never-banked", "why": PANELS},
                 C: {"tag": "zero-pages", "why": ZERO}}
        out = self._stuck(_rows([A, B, C], "ROUTED") + _rows(NEW, "CAPTURE"), _pass(holds))
        self.assertEqual(len(out), 1, out)
        why = out[0]["why"]
        self.assertTrue(why.startswith("older than the newest 16 - held by the drain, not owed: 2 panels-never-banked ("), why)
        self.assertIn("; 1 zero-pages (", why)
        self.assertTrue(why.endswith(" - the drain's pass 7 min ago"), why)
        self.assertNotIn("owes them a tombstone", why, "a held reel was called the drain's debt")
        self.assertNotIn("_reels", out[0], "the reader's working list leaked onto the wire")

    def test_a_row_part_held_says_both(self):
        out = self._stuck(_rows([A, B], "ROUTED") + _rows(NEW, "CAPTURE"),
                          _pass({A: {"tag": "zero-pages", "why": ZERO}}))
        why = out[0]["why"]
        self.assertIn("the drain owes them a tombstone (1 of them; the rest held by the drain, not owed: 1 zero-pages (", why)

    def test_with_no_pass_on_record_the_sentence_is_unchanged(self):
        out = self._stuck(_rows([A], "ROUTED") + _rows(NEW, "CAPTURE"), {})
        self.assertEqual(out[0]["why"], "older than the newest 16 - the drain owes them a tombstone")

    def test_a_lane_station_held_by_the_drain_says_the_drains_hold(self):
        out = self._stuck(_rows([A], "PRINTER") + _rows(NEW, "CAPTURE"),
                          _pass({A: {"tag": "panels-never-banked", "why": PANELS}}))
        self.assertIn("held by the drain, not owed: 1 panels-never-banked", out[0]["why"])

    def test_the_pass_keeps_the_drains_holds_and_not_its_window(self):
        p = {"kept": [{"reel": A, "tag": "panels-never-banked", "why": PANELS}, {"reel": NEW[0], "tag": "recent", "why": "x"},
                      {"reel": C, "tag": "zero-pages", "why": ZERO}]}
        self.assertEqual(sorted(CA._retention_holds(p)), sorted([A, C]))
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        once = src[src.index("\ndef _retention_once("):]
        once = once[:once.index("\ndef ", 10)]
        self.assertIn('"holds": _retention_holds(p),', once, "the retention pass does not keep the drain's holds")


RED_PROOF = [
    {"why": "REG-3053 - a reel the drain holds is called its debt again",
     "file": "tv/control_app.py",
     "find": "    if held and n_held >= len(reels or ()):\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-3053 - a row part held names only the debt",
     "file": "tv/control_app.py",
     "find": "    if held:\n        why += \" (%d of them; the rest %s)\" % (len(reels) - n_held, held)\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-3053 - the retention pass stops keeping the drain's holds",
     "file": "tv/control_app.py",
     "find": "            \"holds\": _retention_holds(p),   # REG-3053 - the drain's own reason for each reel it holds\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-3053 - the newest window's 'recent' is kept as a hold",
     "file": "tv/control_app.py",
     "find": "k.get(\"tag\") not in (None, \"recent\"):\n",
     "replace": "k.get(\"tag\") is not None:\n",
     "matches": 1},
    {"why": "REG-3053 - the reader never hands its reels to the sentence",
     "file": "tv/control_app.py",
     "find": "_river_owed_why(e[\"station\"], _keep, _rs), 320))\n",
     "replace": "_river_owed_why(e[\"station\"], _keep), 320))\n",
     "matches": 1},
    {"why": "REG-3053 - the hold loses the age of the drain's pass",
     "file": "tv/control_app.py",
     "find": "    return \"held by the drain, not owed: \" + \"; \".join(parts) + when, sum(n for n, _w in by.values())\n",
     "replace": "    return \"held by the drain, not owed: \" + \"; \".join(parts), sum(n for n, _w in by.values())\n",
     "matches": 1},
    {"why": "REG-3053 - the reader's working list leaks onto the wire",
     "file": "tv/control_app.py",
     "find": "        _rs = e.pop(\"_reels\", [])\n",
     "replace": "        _rs = e.get(\"_reels\", [])\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
