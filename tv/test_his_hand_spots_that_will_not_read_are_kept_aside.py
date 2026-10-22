# -*- coding: utf-8 -*-
"""REG-2416 (review of REG-2410, r2 reproduced) — HIS HAND SPOTS THAT WILL NOT READ ARE KEPT ASIDE, NEVER DROPPED.

d2r_mulePos is where he put each item on a mule's grids by hand ("i can move them and unlock them to lock them in a
different cube in the order i choose"). The mule window read it through `JSON.parse(raw || '{}')` with `catch -> {}`,
so a store cut short mid-write read as EMPTY and the next drop wrote {its own spot} over it: the review drove
window._mpPlace on such a store - ok:true, the stored value only {uni-armor:{Enigma:...}}, Shako's hand spot gone,
nothing quarantined, nothing kept aside, nothing said.

THE FIX, driven here on the SHIPPED code (the store door window.LSR, the boot and its notice, ⟦TAB SYNC⟧, the vault
module's head, and the mule window's _mulePosAll / _mulePosWrite / _mpFind / window._mpPlace / _mpUnlock / _mpMoveTo /
the packer's spot read, each cut from bible.html), in node, with the packer itself stood in:
  · bytes that will not parse, or are not a map, are UNKNOWN (null) and QUARANTINED at the door: kept aside byte for
    byte, every write refused, the notice names the store in his words;
  · a drop, an unlock and a move refuse in their own words, and every spot he placed stays;
  · the writer throws (every caller's catch says it) on UNKNOWN and on a key the door holds - nothing is written;
  · the packer lays every item itself while the spots are UNKNOWN, and never throws on them;
  · another tab's spots that read lift the quarantine; nothing saved yet places as it always did.
The packing itself is test_the_mule_window_places_by_hand's; the pixels are the browser's, on CI.
RED_PROOF below; prove with `HEART2_PROVE_WORKERS=1 python3 tv/heart2.py --prove test_his_hand_spots_that_will_not_read_are_kept_aside`.
"""
import json
import os
import re
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

import store_door_harness as D  # noqa: E402

POS = "d2r_mulePos"
#: his spots, cut short mid-write (the review's r2): Shako's whole, Arkaine's Valor half-written
CORRUPT = ('{"uni-armor":{"Harlequin Crest (Shako)":{"tab":"personal","page":0,"x":3,"y":2,"at":"2026-10-01"},'
           '"Arkaine\'s Valor":{"tab":"personal","page":0,"x":0,"y":0')
GOOD = '{"uni-armor":{"Harlequin Crest (Shako)":{"tab":"personal","page":0,"x":3,"y":2,"at":"2026-10-01"}}}'
SPOT = "{ tab: 'personal', page: 0, x: 6, y: 0 }"

#: the packer stood in: one 2x3 item in the locker, one mule, nothing in the way, no conflicts
PACKER = r"""
function _mpLoadNow(muleId, posAll){
  return { mules: [{ stash: [], inv: [], tabs: {} }], sized: [{ key: 'Enigma', n: 'Enigma', w: 2, h: 3 }], conflicts: [] };
}
"""


def _line(s, start):
    n = s.count("\n" + start)
    if n != 1:
        raise AssertionError("the line %r matched %d times - the anchor moved" % (start[:60], n))
    i = s.index("\n" + start) + 1
    return s[i:s.index("\n", i) + 1]


def _pieces(s):
    areas = re.search(r"^  var MULE_AREAS = \{.*?\};$", s, re.M | re.S)
    if not areas:
        raise AssertionError("MULE_AREAS moved")
    load = (_line(s, "    if (muleId != null && !posAll) posAll = _mulePosAll() || {};")
            + _line(s, "    var _pos = (muleId != null) ? ((posAll || _mulePosAll())[muleId] || {}) : {};"))
    inner = ("var MULE_STASH_W = 10, MULE_STASH_H = 10, MULE_INV_W = 10, MULE_INV_H = 4;\n"
             + "function muleById(id){ return roster.find(function(m){ return m.id === id; }) || null; }\n"
             + areas.group(0) + "\n" + _line(s, "  var MP_POS_KEY = 'd2r_mulePos';") + PACKER
             + D.fn(s, "_mulePosAll") + "\n" + D.fn(s, "_mulePosHeldWhy") + "\n" + D.fn(s, "_mulePosWrite") + "\n"
             + D.fn(s, "_mpFind") + "\n" + D.window_fn(s, "_mpPlace") + "\n" + D.window_fn(s, "_mpUnlock") + "\n"
             + D.window_fn(s, "_mpMoveTo") + "\n"
             + "window.__pos = function(muleId, posAll){\n" + load + "    return _pos;\n};\n"
             + "window.__M = { all: _mulePosAll, write: _mulePosWrite };\n")
    return (D.stage(s) + D.boot(s) + D.tab_sync(s) + "\nvar renderVault = function(){};\n(function(){\n" + D.vault_head(s)
            + "\n" + inner + "})();\n")


OTHER = ("function other(k, nv){ var ov = RAW[k] == null ? null : RAW[k]; if (nv == null) delete RAW[k]; else RAW[k] = String(nv);"
         " fire(k, ov, nv == null ? null : String(nv)); }\n")


def _run(body, pos):
    seed = {} if pos is None else {POS: pos}
    return D.page(_pieces(D.src()), OTHER + body, seed=seed)


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED mule window doors; UNMEASURED, not passing")
class HisHandSpotsThatWillNotReadAreKeptAside(unittest.TestCase):

    def test_spots_that_will_not_parse_are_quarantined_never_read_as_empty(self):
        o = _run("OUT.read = window.__M.all(); var q = window.LSR.quarantined('d2r_mulePos');"
                 "OUT.q = q ? { kind: q.kind, reason: q.reason, asideOk: q.asideOk } : null; OUT.aside = aside();"
                 "OUT.notice = (document.getElementById('store-quarantine') || {}).innerHTML || '';", CORRUPT)
        self.assertIsNone(o["read"], "spots that will not parse were read as an empty store")
        self.assertEqual(o["q"], {"kind": "quarantine", "reason": "will not parse", "asideOk": True})
        self.assertEqual(list(o["aside"].values()), [CORRUPT], "the exact bytes must be kept aside")
        self.assertIn('data-store="d2r_mulePos"', o["notice"])
        self.assertIn("your hand spots on the mule grids", o["notice"], "the notice must say what the store is, in his words")

    def test_a_drop_over_them_is_refused_and_every_spot_stays(self):
        """The review's r2: a drop of Enigma onto the personal stash of UNI-ARMOR."""
        o = _run("OUT.r = window._mpPlace('uni-armor', 'Enigma', " + SPOT + "); OUT.raw = RAW['d2r_mulePos'];", CORRUPT)
        self.assertFalse(o["r"]["ok"], o["r"])
        self.assertEqual(o["r"]["refused"], "held")
        self.assertIn("d2r_mulePos", o["r"]["why"], "the refusal must name the store")
        self.assertEqual(o["raw"], CORRUPT, "a drop wrote over the spots it could not read - Shako's spot gone")

    def test_the_unlock_and_the_move_refuse_in_their_own_words(self):
        o = _run("OUT.unlock = window._mpUnlock('uni-armor', 'Harlequin Crest (Shako)');"
                 "OUT.move = window._mpMoveTo('uni-armor', 'Enigma', 0, 'personal'); OUT.raw = RAW['d2r_mulePos'];", CORRUPT)
        self.assertEqual((o["unlock"]["ok"], o["unlock"].get("refused")), (False, "held"))
        self.assertIn("nothing was unlocked", o["unlock"]["why"])
        self.assertEqual((o["move"]["ok"], o["move"].get("refused")), (False, "held"))
        self.assertIn("will not parse", o["move"]["why"], "the move must say the spots will not read, not that the mule has no room")
        self.assertNotIn("no room", o["move"]["why"])
        self.assertEqual(o["raw"], CORRUPT)

    def test_a_store_of_the_wrong_shape_is_unknown_too(self):
        for raw in ("[]", "null", "7"):
            o = _run("OUT.read = window.__M.all(); var q = window.LSR.quarantined('d2r_mulePos'); OUT.reason = q && q.reason;", raw)
            self.assertIsNone(o["read"], "%s was read as his spots" % raw)
            self.assertEqual(o["reason"], "is not a map of mules to hand spots")

    def test_nothing_saved_yet_places_as_it_always_did(self):
        o = _run("OUT.read = window.__M.all(); OUT.q = window.LSR.quarantined('d2r_mulePos');"
                 "OUT.r = window._mpPlace('uni-armor', 'Enigma', " + SPOT + ");"
                 "OUT.stored = JSON.parse(RAW['d2r_mulePos'] || 'null');", None)
        self.assertEqual(o["read"], {})
        self.assertIsNone(o["q"])
        self.assertTrue(o["r"]["ok"], o["r"])
        spot = o["stored"]["uni-armor"]["Enigma"]
        self.assertEqual((spot["tab"], spot["page"], spot["x"], spot["y"]), ("personal", 0, 6, 0))

    def test_the_writer_throws_on_unknown_and_on_a_held_key_and_writes_nothing(self):
        o = _run("try { window.__M.write(null); OUT.bare = 'wrote'; } catch (e) { OUT.bare = String(e.message); }"
                 "OUT.afterBare = RAW['d2r_mulePos'];"
                 "window.LSR.hold('d2r_mulePos', 'another tab cleared this browser’s saved data');"
                 "try { window.__M.write({ 'uni-armor': {} }); OUT.held = 'wrote'; } catch (e) { OUT.held = String(e.message); }"
                 "OUT.place = window._mpPlace('uni-armor', 'Enigma', " + SPOT + ");"
                 "OUT.raw = RAW['d2r_mulePos'];", GOOD)
        self.assertIn("d2r_mulePos", o["bare"], "UNKNOWN was written as his spots")
        self.assertEqual(o["afterBare"], GOOD)
        self.assertIn("changed in another tab", o["held"], "a write the door held was not refused in words")
        self.assertEqual((o["place"]["ok"], o["place"].get("refused")), (False, "held"))
        self.assertEqual(o["raw"], GOOD)

    def test_the_packer_lays_every_item_itself_while_the_spots_will_not_read(self):
        bad = _run("try { OUT.pos = window.__pos('uni-armor'); } catch (e) { OUT.pos = 'threw: ' + e.message; }", CORRUPT)
        good = _run("OUT.pos = window.__pos('uni-armor');", GOOD)
        self.assertEqual(bad["pos"], {}, "the packer threw on, or read, spots that will not parse")
        self.assertEqual(sorted(good["pos"]), ["Harlequin Crest (Shako)"], "the packer must still read spots that do")

    def test_another_tab_writing_spots_that_read_lifts_the_quarantine(self):
        o = _run("OUT.before = (window.__M.all() === null) && !!window.LSR.quarantined('d2r_mulePos');"
                 "other('d2r_mulePos', " + json.dumps(GOOD) + "); OUT.q = window.LSR.quarantined('d2r_mulePos');"
                 "OUT.r = window._mpPlace('uni-armor', 'Enigma', " + SPOT + ").ok;"
                 "OUT.keys = Object.keys(JSON.parse(RAW['d2r_mulePos'])['uni-armor']).sort();", CORRUPT)
        self.assertTrue(o["before"], "the setup must start with his spots quarantined here")
        self.assertIsNone(o["q"], "another tab's spots that read must lift the quarantine here")
        self.assertTrue(o["r"])
        self.assertEqual(o["keys"], ["Enigma", "Harlequin Crest (Shako)"])


RED_PROOF = [
    {"why": "REG-2416 - spots that will not parse are read as an empty store again",
     "file": "bible.html", "matches": 1,
     "find": "    try { if (window.LSR && typeof window.LSR.quarantine === 'function') window.LSR.quarantine(MP_POS_KEY, why); } catch (eQ) {}\n    return null;\n",
     "replace": "    try { if (window.LSR && typeof window.LSR.quarantine === 'function') window.LSR.quarantine(MP_POS_KEY, why); } catch (eQ) {}\n    return {};\n"},
    {"why": "REG-2416 - spots that will not read are not quarantined (not kept aside, not said)",
     "file": "bible.html", "matches": 1,
     "find": "    try { if (window.LSR && typeof window.LSR.quarantine === 'function') window.LSR.quarantine(MP_POS_KEY, why); } catch (eQ) {}\n",
     "replace": ""},
    {"why": "REG-2416 - a drop writes over spots it could not read (the review's r2)",
     "file": "bible.html", "matches": 1,
     "find": "    if (_mulePosAll() === null || (window.LSR && typeof window.LSR.quarantined === 'function' && window.LSR.quarantined(MP_POS_KEY)))\n",
     "replace": "    if (false)\n"},
    {"why": "REG-2416 - a drop onto spots the door holds is tried, and refused only as 'could not be saved'",
     "file": "bible.html", "matches": 1,
     "find": "    if (_mulePosAll() === null || (window.LSR && typeof window.LSR.quarantined === 'function' && window.LSR.quarantined(MP_POS_KEY)))\n",
     "replace": "    if (_mulePosAll() === null)\n"},
    {"why": "REG-2416 - the unlock indexes spots that will not read",
     "file": "bible.html", "matches": 1,
     "find": "    if (all === null) return { ok: false, refused: 'held', why: 'nothing was unlocked - ' + _mulePosHeldWhy() };\n",
     "replace": ""},
    {"why": "REG-2416 - the move says 'no room' after every cell's refusal, never why",
     "file": "bible.html", "matches": 1,
     "find": "    if (_mulePosAll() === null) return { ok: false, refused: 'held', why: 'nothing was moved - ' + _mulePosHeldWhy() };\n",
     "replace": ""},
    {"why": "REG-2416 - UNKNOWN is written as his spots",
     "file": "bible.html", "matches": 1,
     "find": "    if (!all || typeof all !== 'object' || Array.isArray(all)) throw new Error(_mulePosHeldWhy());\n",
     "replace": ""},
    {"why": "REG-2416 - a write the door refused is answered as written",
     "file": "bible.html", "matches": 1,
     "find": "    if (window.LSR.setItem(MP_POS_KEY, JSON.stringify(all)) === false) throw new Error(_mulePosHeldWhy());\n",
     "replace": "    window.LSR.setItem(MP_POS_KEY, JSON.stringify(all));\n"},
    {"why": "REG-2416 - the packer indexes spots that will not read and throws",
     "file": "bible.html", "matches": 1,
     "find": "    if (muleId != null && !posAll) posAll = _mulePosAll() || {};\n",
     "replace": ""},
    {"why": "REG-2416 - the notice names the spot store with no words he knows",
     "file": "bible.html", "matches": 1,
     "find": " d2r_mulePos: 'your hand spots on the mule grids',\n",
     "replace": "\n"},
    {"why": "REG-2416 - the spot store is left out of the tab sync: another tab's good spots never lift the quarantine",
     "file": "bible.html", "matches": 1,
     "find": "    ['d2r_vaultProv', 'd2r_mulePos', 'd2r_muleEquip'].forEach(function(k){\n",
     "replace": "    ['d2r_vaultProv', 'd2r_muleEquip'].forEach(function(k){\n"},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
