# -*- coding: utf-8 -*-
"""#41 rank 20 (REG-1534, 2026-09-29) — THE CHARACTERS TAB SAYS UNKNOWN, NEVER "NO MAIN" OR "0 WORN".

The heart audit (verified list, rank 20): "A dangling d2r_cbMain shows exactly like 'no MAIN set', and a set missing
its slots counts as 0 worn." `_mainOf` returned null for a dangling id, so the room drew no badge and nothing else -
the same picture as a MAIN never set; `_count` added nothing for a set without a slots object and still returned a
number, so a build whose set could not be counted read "0 items · 0 worn".

WHAT THIS LAW DRIVES, in the SHIPPED room (the ⟦chars-tab-js⟧ block cut from bible.html, run in node over the same
DOM stand-in test_the_characters_tab_is_manual_and_separate uses — never re-typed here):
  · A MAIN THAT NAMES NO SAVED BUILD IS SAID: the list opens with a note (data-state="main-dangling") naming the
    dangling id and calling the MAIN UNKNOWN; no card wears the badge; the cards still render; and the room's own
    reader (window._charsList, what the mule window asks) carries `mainDangling` = that id.
  · THE TWO HONEST STATES STAY QUIET: a MAIN that names a build wears the badge and draws no note; no MAIN at all
    draws no note; both read `mainDangling: null`.
  · A SET WITH NO SLOTS OBJECT IS UNKNOWN: its card says "items UNKNOWN" and never "0 items"; a set with an EMPTY
    slots object is a real 0; a set missing only its swap/inv still counts what its slots hold.
  · A read never writes: no localStorage write happens for any of it.
RED_PROOF below.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable; enable()

from test_the_characters_tab_is_manual_and_separate import NODE, _run   # the shipped harness, one copy

NOTE = 'data-state="main-dangling"'


def _drive(main, extra_builds=""):
    body = r"""
var all = { bHAM: HAMMER, bSORC: SORC, bDRU: DRUID };
""" + extra_builds + r"""
window.LSR.setItem('d2r_charBuilds', JSON.stringify(all, null, 1));
if (__MAIN__ !== null) window.LSR.setItem('d2r_cbMain', __MAIN__);
WRITES.length = 0;
window.renderCharsTab();
OUT.html = ELS['chars-list']._html;
OUT.ids = ids();
OUT.badges = cards().filter(function(c){ return c.badge; }).map(function(c){ return c.id; });
OUT.list = window._charsList();
OUT.cards = {}; cards().forEach(function(c){ OUT.cards[c.id] = c.html; });
OUT.writes = WRITES.slice();
""".replace("__MAIN__", "null" if main is None else repr(main))
    return _run(body)


@unittest.skipIf(NODE is None, "node is not on this machine")
class ADanglingMainAndASetWithoutSlotsReadUnknown(unittest.TestCase):

    def test_a_main_that_names_no_saved_build_is_said_and_marks_nothing(self):
        out = _drive("bGONE")
        self.assertIn(NOTE, out["html"], "a dangling MAIN draws the same as no MAIN")
        self.assertIn("bGONE", out["html"], "the note does not name the dangling id")
        self.assertIn("UNKNOWN", out["html"])
        self.assertEqual([], out["badges"], "a dangling MAIN put the badge on a card")
        self.assertEqual(3, len(out["ids"]), "the cards stopped rendering under a dangling MAIN")
        self.assertEqual("bGONE", out["list"]["mainDangling"], "the room's reader does not carry the dangling id")
        self.assertEqual([False, False, False], [r["main"] for r in out["list"]["rows"]])
        self.assertEqual([], out["writes"], "a read wrote the store")

    def test_a_main_that_names_a_build_and_no_main_at_all_stay_quiet(self):
        out = _drive("bSORC")
        self.assertNotIn(NOTE, out["html"])
        self.assertEqual(["bSORC"], out["badges"])
        self.assertIsNone(out["list"]["mainDangling"])
        self.assertEqual("bSORC", out["ids"][0], "the MAIN does not lead")
        out = _drive(None)
        self.assertNotIn(NOTE, out["html"], "no MAIN at all is not a dangling MAIN")
        self.assertEqual([], out["badges"])
        self.assertIsNone(out["list"]["mainDangling"])

    def test_a_set_without_a_slots_object_is_unknown_not_zero_worn(self):
        out = _drive("bHAM", extra_builds=r"""
all.bBARE = b('Bare', 'Druid', 5, NOW - 60000, [{ name: 'Set 1', inv: [], swap: {}, ws: 1 }]);          // no slots object
all.bEMPTY = b('Empty', 'Druid', 5, NOW - 70000, [set1({}, [], {})]);                                    // a real empty set
all.bOLD = b('Old', 'Druid', 5, NOW - 80000, [{ name: 'Set 1', slots: { head: { name: 'Shako' } }, ws: 1 }]);   // slots only
""")
        bare, empty, old = out["cards"]["bBARE"], out["cards"]["bEMPTY"], out["cards"]["bOLD"]
        self.assertIn("items UNKNOWN", bare, "a set with no slots object was counted")
        self.assertNotIn("<b>0</b> item", bare)
        self.assertNotIn("0 worn", bare)
        self.assertIn("<b>0</b> items", empty, "an empty slots object is a measured zero")
        self.assertIn("0 worn", empty)
        self.assertIn("<b>1</b> item", old, "a set missing only swap/inv lost the slot it holds")
        self.assertIn("1 worn", old)


RED_PROOF = [
    {
        "why": "#41 rank 20 - a set with no slots object counts as 0 worn again",
        "file": "../bible.html",
        "find": "      if (!s.slots || typeof s.slots !== 'object') return null;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#41 rank 20 - the dangling-MAIN note is never drawn: a dangling MAIN reads like no MAIN",
        "file": "../bible.html",
        "find": "    list.innerHTML = _mainNote(_mainDangling(r.all))\n      + ",
        "replace": "    list.innerHTML = ",
        "matches": 1,
    },
    {
        "why": "#41 rank 20 - the room's reader stops carrying mainDangling, so the mule window cannot say UNKNOWN",
        "file": "../bible.html",
        "find": "    return { ok: true, mainDangling: _mainDangling(r.all), rows: _order(r.all, mainId).map(function(id){",
        "replace": "    return { ok: true, mainDangling: null, rows: _order(r.all, mainId).map(function(id){",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("⚪ SKIP — node is not on this machine, so the Characters tab was not driven. UNMEASURED, declared (77).\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
