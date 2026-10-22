# -*- coding: utf-8 -*-
"""REG-2417 (review of REG-2410, the same shape as r2) — WHAT A MULE WEARS AND CARRIES THAT WILL NOT READ IS KEPT ASIDE.

d2r_muleEquip is each mule's doll and inventory as he set them in the mule window (his picks from the database, his
imports). It was read exactly as his spots were: `JSON.parse(raw || '{}')` with `catch -> {}`, so a store cut short
mid-write read as EMPTY, and the next pick, removal or drag wrote {its own entry} over every doll and inventory he had.
Not quarantined, not kept aside, not said.

THE FIX, driven here on the SHIPPED code (the store door window.LSR, the boot and its notice, ⟦TAB SYNC⟧, the vault
module's head, and the mule window's _mpEqAll / _mpEqWrite / _mpEqPlace / _mpEqRemove / _mpEqAt / _mpCbEntryAt /
_mpHostWrite / window._mpUnequip, each cut from bible.html), in node, with the filing door stood in:
  · bytes that will not parse, or are not a map, are UNKNOWN (null) and QUARANTINED at the door: kept aside byte for
    byte, every write refused, the notice names the store in his words;
  · the store's one writer throws on UNKNOWN and on a key the door holds - nothing is written and nothing is filed -
    so every picker door says "the equipment could not be saved (why)";
  · a pick over it is refused in the picker's own words; the doll shows nothing from it and never throws;
  · another tab's store that reads lifts the quarantine; nothing saved yet still files a new manual pick.
The mule window's pixels are the browser's, on CI.
RED_PROOF below; prove with `HEART2_PROVE_WORKERS=1 python3 tv/heart2.py --prove test_what_a_mule_wears_that_will_not_read_is_kept_aside`.
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

EQ = "d2r_muleEquip"
#: his dolls, cut short mid-write: UNI-ARMOR wears Shako, its inventory half-written
CORRUPT = ('{"uni-armor":{"setI":{"head":{"name":"Harlequin Crest (Shako)","source":"manual","at":"2026-10-01"}},'
           '"inv":{"k1":{"name":"Annihilus","source":"manual","page":0,"x":0,"y":0')
GOOD = '{"uni-armor":{"setI":{"head":{"name":"Harlequin Crest (Shako)","source":"manual","at":"2026-10-01"}}}}'
SHAKO_PICK = ("{ name: 'Harlequin Crest (Shako)', id: 'u:shako', base: 'Shako', q: 'u', rolls: {}, sockets: 0,"
              " affixes: [], eth: false, ilvl: 99, socketed: [] }")
NEW_PICK = ("{ 'uni-armor': { setI: { head: { name: 'Harlequin Crest (Shako)', source: 'manual', at: '2026-10-01' },"
            " tors: { name: 'Arkaine\\'s Valor', source: 'manual', at: '2026-10-22T10:00:00Z' } } } }")


def _block(s, start, end_line):
    """from a unique start line to the end of the line holding `end_line` after it"""
    if s.count(start) != 1:
        raise AssertionError("%r matched %d times - the anchor moved" % (start[:60], s.count(start)))
    i = s.index(start)
    j = s.index(end_line, i)
    return s[i:s.index("\n", j) + 1]


def _pieces(s):
    inner = ("function muleById(id){ return roster.find(function(m){ return m.id === id; }) || null; }\n"
             "var FILED = []; window.vaultFile = function(n, w, o){ FILED.push({ n: n, by: w && w.by, mule: o && o.mule });"
             " return { ok: true, mode: 'filed', mule: o && o.mule }; };\n"
             "var openMuleId = 'uni-armor', _mpPickAt = { slot: 'head', set: 'setI' }, _mpPickErr = '', _mpSwap = 1,"
             " _mpFocusNext = null, OPENED = 0;\n"
             "function _mpHostSync(){} function _mpRefresh(){} window.openMuleCard = function(){ OPENED++; };\n"
             + _block(s, "  var MP_SLOT_WEARS = { head: ['helm']", "  var MP_CB_FIELDS = [")
             + D.fn(s, "_mpEqAll") + "\n" + D.fn(s, "_mpEqHeldWhy") + "\n" + D.fn(s, "_mpEqWrite") + "\n"
             + D.fn(s, "_mpIsGenericCopy") + "\n" + D.fn(s, "_mpSetOf") + "\n" + D.fn(s, "_mpEqPlace") + "\n"
             + D.fn(s, "_mpEqRemove") + "\n" + D.fn(s, "_mpLockRefusal") + "\n" + D.fn(s, "_mpCbEntry") + "\n"
             + D.fn(s, "_mpEqAt") + "\n" + D.window_fn(s, "_mpCbEntryAt") + "\n" + D.fn(s, "_mpHostWrite") + "\n"
             + D.window_fn(s, "_mpUnequip") + "\n"
             + "window.__E = { all: _mpEqAll, write: _mpEqWrite, at: _mpEqAt, host: _mpHostWrite,"
             " err: function(){ return _mpPickErr; }, filed: function(){ return FILED; }, opened: function(){ return OPENED; } };\n")
    return (D.stage(s) + D.boot(s) + D.tab_sync(s) + "\nvar renderVault = function(){};\n(function(){\n" + D.vault_head(s)
            + "\n" + inner + "})();\n")


OTHER = ("function other(k, nv){ var ov = RAW[k] == null ? null : RAW[k]; if (nv == null) delete RAW[k]; else RAW[k] = String(nv);"
         " fire(k, ov, nv == null ? null : String(nv)); }\n")


def _run(body, eq):
    seed = {} if eq is None else {EQ: eq}
    return D.page(_pieces(D.src()), OTHER + body, seed=seed)


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED mule window doors; UNMEASURED, not passing")
class WhatAMuleWearsThatWillNotReadIsKeptAside(unittest.TestCase):

    def test_a_store_that_will_not_parse_is_quarantined_never_read_as_empty(self):
        o = _run("OUT.read = window.__E.all(); var q = window.LSR.quarantined('d2r_muleEquip');"
                 "OUT.q = q ? { kind: q.kind, reason: q.reason, asideOk: q.asideOk } : null; OUT.aside = aside();"
                 "OUT.notice = (document.getElementById('store-quarantine') || {}).innerHTML || '';", CORRUPT)
        self.assertIsNone(o["read"], "a mule store that will not parse was read as empty")
        self.assertEqual(o["q"], {"kind": "quarantine", "reason": "will not parse", "asideOk": True})
        self.assertEqual(list(o["aside"].values()), [CORRUPT], "the exact bytes must be kept aside")
        self.assertIn('data-store="d2r_muleEquip"', o["notice"])
        self.assertIn("what each mule wears and carries", o["notice"], "the notice must say what the store is, in his words")

    def test_a_pick_over_it_is_refused_in_the_pickers_words_and_every_entry_stays(self):
        o = _run("try { OUT.r = window.__E.host(" + SHAKO_PICK + "); } catch (e) { OUT.r = 'threw: ' + e.message; }"
                 "OUT.err = window.__E.err(); OUT.filed = window.__E.filed().length; OUT.raw = RAW['d2r_muleEquip'];", CORRUPT)
        self.assertIsInstance(o["r"], dict, "the picker threw on a store that will not read: %r" % (o["r"],))
        self.assertFalse(o["r"]["ok"])
        self.assertIn("the equipment could not be saved", o["err"])
        self.assertIn("d2r_muleEquip", o["err"], "the picker must name the store")
        self.assertEqual(o["filed"], 0)
        self.assertEqual(o["raw"], CORRUPT, "a pick wrote over every doll and inventory it could not read")

    def test_the_writer_throws_on_unknown_and_on_a_held_key_and_files_nothing(self):
        o = _run("try { window.__E.write(" + NEW_PICK + "); OUT.unknown = 'wrote'; } catch (e) { OUT.unknown = e.message; }"
                 "OUT.raw = RAW['d2r_muleEquip']; OUT.filed = window.__E.filed().length;", CORRUPT)
        self.assertIn("d2r_muleEquip", o["unknown"], "the writer wrote over a store it could not read")
        self.assertEqual((o["raw"], o["filed"]), (CORRUPT, 0))
        o = _run("window.LSR.hold('d2r_muleEquip', 'another tab cleared this browser’s saved data');"
                 "try { window.__E.write(" + NEW_PICK + "); OUT.held = 'wrote'; } catch (e) { OUT.held = e.message; }"
                 "OUT.raw = RAW['d2r_muleEquip']; OUT.filed = window.__E.filed().length;", GOOD)
        self.assertIn("changed in another tab", o["held"], "a write the door held was answered as written")
        self.assertEqual((o["raw"], o["filed"]), (GOOD, 0), "a placement the door refused was filed to the mule anyway")
        o = _run("try { window.__E.write(null); OUT.bare = 'wrote'; } catch (e) { OUT.bare = e.message; }"
                 "OUT.has = Object.prototype.hasOwnProperty.call(RAW, 'd2r_muleEquip');", None)
        self.assertNotEqual(o["bare"], "wrote")
        self.assertFalse(o["has"], "UNKNOWN was written as the mule store")

    def test_unequip_says_it_and_writes_nothing(self):
        o = _run("OUT.r = window._mpUnequip('head'); OUT.err = window.__E.err(); OUT.opened = window.__E.opened();"
                 "OUT.raw = RAW['d2r_muleEquip'];", CORRUPT)
        self.assertFalse(o["r"])
        self.assertIn("the equipment could not be saved", o["err"])
        self.assertEqual(o["opened"], 1, "the window must repaint to say it")
        self.assertEqual(o["raw"], CORRUPT)

    def test_the_doll_shows_nothing_from_it_and_never_throws(self):
        o = _run("try { OUT.at = window.__E.at('head'); OUT.cb = window._mpCbEntryAt('head', 'setI');"
                 " OUT.cb2 = window._mpCbEntryAt('head'); OUT.ok = true; } catch (e) { OUT.ok = 'threw: ' + e.message; }", CORRUPT)
        self.assertIs(o["ok"], True, o["ok"])
        self.assertEqual((o["at"], o["cb"], o["cb2"]), (None, None, None))

    def test_a_store_of_the_wrong_shape_is_unknown_too(self):
        for raw in ("[]", "null", '"text"'):
            o = _run("OUT.read = window.__E.all(); var q = window.LSR.quarantined('d2r_muleEquip'); OUT.reason = q && q.reason;", raw)
            self.assertIsNone(o["read"], "%s was read as the mule store" % raw)
            self.assertEqual(o["reason"], "is not a map of mules to what they wear and carry")

    def test_nothing_saved_yet_still_files_a_new_manual_pick(self):
        o = _run("OUT.read = window.__E.all(); window.__E.write(" + NEW_PICK + ");"
                 "OUT.stored = JSON.parse(RAW['d2r_muleEquip']); OUT.filed = window.__E.filed();", None)
        self.assertEqual(o["read"], {})
        self.assertEqual(sorted(o["stored"]["uni-armor"]["setI"]), ["head", "tors"])
        self.assertEqual(sorted(f["n"] for f in o["filed"]), ["Arkaine's Valor", "Harlequin Crest (Shako)"],
                         "a new manual pick must still be filed to that mule through the door")
        self.assertEqual({f["by"] for f in o["filed"]}, {"hand"})

    def test_another_tab_writing_one_that_reads_lifts_the_quarantine(self):
        o = _run("OUT.before = (window.__E.all() === null) && !!window.LSR.quarantined('d2r_muleEquip');"
                 "other('d2r_muleEquip', " + json.dumps(GOOD) + "); OUT.q = window.LSR.quarantined('d2r_muleEquip');"
                 "OUT.at = (window.__E.at('head') || {}).name || null;", CORRUPT)
        self.assertTrue(o["before"], "the setup must start with the mule store quarantined here")
        self.assertIsNone(o["q"], "another tab's store that reads must lift the quarantine here")
        self.assertEqual(o["at"], "Harlequin Crest (Shako)")


RED_PROOF = [
    {"why": "REG-2417 - a mule store that will not parse is read as empty again",
     "file": "bible.html", "matches": 1,
     "find": "    try { if (window.LSR && typeof window.LSR.quarantine === 'function') window.LSR.quarantine('d2r_muleEquip', why); } catch (eQ) {}\n    return null;\n",
     "replace": "    try { if (window.LSR && typeof window.LSR.quarantine === 'function') window.LSR.quarantine('d2r_muleEquip', why); } catch (eQ) {}\n    return {};\n"},
    {"why": "REG-2417 - a mule store that will not read is not quarantined (not kept aside, not said)",
     "file": "bible.html", "matches": 1,
     "find": "    try { if (window.LSR && typeof window.LSR.quarantine === 'function') window.LSR.quarantine('d2r_muleEquip', why); } catch (eQ) {}\n",
     "replace": ""},
    {"why": "REG-2417 - the writer writes UNKNOWN, or over a store it could not read",
     "file": "bible.html", "matches": 1,
     "find": "    if (_prev === null || !all || typeof all !== 'object' || Array.isArray(all)) throw new Error(_mpEqHeldWhy());\n",
     "replace": ""},
    {"why": "REG-2417 - a write the door refused is answered as written, and its placement filed to the mule",
     "file": "bible.html", "matches": 1,
     "find": "    if (window.LSR.setItem('d2r_muleEquip', JSON.stringify(all)) === false) throw new Error(_mpEqHeldWhy());\n",
     "replace": "    window.LSR.setItem('d2r_muleEquip', JSON.stringify(all));\n"},
    {"why": "REG-2417 - the picker indexes a store that will not read and throws",
     "file": "bible.html", "matches": 1,
     "find": "    if (all === null){ _mpPickErr = 'the equipment could not be saved (' + _mpEqHeldWhy() + ')'; return { ok: false, why: _mpPickErr }; }\n",
     "replace": ""},
    {"why": "REG-2417 - the doll's slot read throws on a store that will not read",
     "file": "bible.html", "matches": 1,
     "find": "  function _mpEqAt(slot){ var m = (_mpEqAll() || {})[openMuleId] || {};",
     "replace": "  function _mpEqAt(slot){ var m = _mpEqAll()[openMuleId] || {};"},
    {"why": "REG-2417 - the builder entry read throws on a store that will not read",
     "file": "bible.html", "matches": 1,
     "find": "    var m = (_mpEqAll() || {})[openMuleId] || {};   /* REG-2417 — UNKNOWN shows no entry */\n",
     "replace": "    var m = _mpEqAll()[openMuleId] || {};\n"},
    {"why": "REG-2417 - the notice names the mule store with no words he knows",
     "file": "bible.html", "matches": 1,
     "find": "  d2r_muleEquip: 'what each mule wears and carries'\n",
     "replace": "  d2r_muleEquipOff: ''\n"},
    {"why": "REG-2417 - the mule store is left out of the tab sync: another tab's good store never lifts the quarantine",
     "file": "bible.html", "matches": 1,
     "find": "    ['d2r_vaultProv', 'd2r_mulePos', 'd2r_muleEquip'].forEach(function(k){\n",
     "replace": "    ['d2r_vaultProv', 'd2r_mulePos'].forEach(function(k){\n"},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
