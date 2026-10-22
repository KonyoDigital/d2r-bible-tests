# -*- coding: utf-8 -*-
"""V1c (#152 item 4, #111 item 6; REG-2420..REG-2427) - A HAND ADD COSTS WORK IN PROPORTION TO THE VAULT, NOT ITS SQUARE.

GrokBot's measurement on v3784 (perf3.py, #230): a hand add took 30 ms at 50 items, 145 ms at 250, 0.9 s at 350,
2.0 s at 450 and 2.7 s at 600, so 600 adds took ~9.5 minutes and his 550-item test ~7.5. The page then did, for ONE
add at 300 items (measured on the shipped page in node, tv/vault_page_node.py): 4,595 router asks (15 per owned name),
861 fuzzy folds of runeword names against the 398-name roster, a catalogue walk of 867 names for every runeword ask,
a walk of every saved move for every war keeper, 5,400 ITEMS walks in ownedPool, and 1,341 reads of d2r_plannerMade
(_itemCells read it before its own cache - #111 item 6 - and artOr read it again for every picture). A paint rebuilt
every record three times per locker card: 36 rebuilds of the whole vault per paint with ten lockers.

The budget is a COUNT, never a clock (a loaded box moves a clock; it cannot move a count). Driven on the shipped page in
node through the real door (window.vaultHandAdd) with a planner record present, it counts one add at 40 owned names and
one at 160, one copy add, and one paint:
  * router asks (_vaultSeamAsk) per add stay under 4 per owned name, and grow linearly from 40 to 160 (x4, not x16);
  * fuzzy folds per add <= 2 (only a name never folded before), catalogue walks per add <= 4;
  * war-keeper walks of the saved moves per add <= 8 (one per bag), ITEMS walks per add <= 12;
  * set-piece folds (_etherNorm under _spNorm) per add <= 60 - never one per pool name per set piece;
  * planner-store parses per add <= 1 - the store did not change, so it is not parsed again;
  * records rebuilds per paint <= 8 and per add <= 4 (a copy add paints too: <= 12).
The clock is printed as a report beside the counts. RED_PROOF below: each entry turns one memo off, and its count
blows through its budget. The memos change no answer - tv/test_the_vault_memo_changes_no_answer.py proves that.
[[regression-guard]] [[heart-first]]
"""
import json
import os
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

import vault_page_node as VPN  # noqa: E402  (the whole page in node)

#: the counters each patch bumps; every anchor must match exactly once (vault_page_node refuses a moved one)
PATCHES = [
    ("      function _vaultSeamAsk(name){", "      function _vaultSeamAsk(name){ window.__C.ask++;"),
    ("  function _d2rItemLookupWalk(q){", "  function _d2rItemLookupWalk(q){ window.__C.lookupWalk++;"),
    ("    ix = new Map();\n    var map = bag.map || {};", "    ix = new Map(); window.__C.keeperWalk++;\n    var map = bag.map || {};"),
    ("    else Object.keys(bag.map || {}).forEach(function(k){",
     "    else (window.__C.keeperWalk++, Object.keys(bag.map || {})).forEach(function(k){"),
    ("    var out = { records: [], index: {}, byKind: {}, orphans: [], carUnknown: false, dockUnknown: false, assignUnknown: false, ok: true };",
     "    window.__C.recordsBuild++; var out = { records: [], index: {}, byKind: {}, orphans: [], carUnknown: false, dockUnknown: false, assignUnknown: false, ok: true };"),
]
PRELUDE = "window.__C = { ask: 0, lookupWalk: 0, keeperWalk: 0, recordsBuild: 0, fold: 0, plannerParse: 0, itemsWalk: 0, etherNorm: 0 };"

BODY = r"""
(function(){
var C = window.__C;
function reset(){ for (var k in C) C[k] = 0; }
function snapC(){ var o = {}; for (var k in C) o[k] = C[k]; return o; }
var realEngine = window.d2rInboxEngine;
window.d2rInboxEngine = function(){ C.fold++; return realEngine.apply(this, arguments); };
var realEther = window._etherNorm;
window._etherNorm = function(){ C.etherNorm++; return realEther.apply(this, arguments); };
Object.defineProperty(ITEMS, 'some', { value: function(){ C.itemsWalk++; return Array.prototype.some.apply(this, arguments); },
                                       configurable: true, writable: true, enumerable: false });
window._vaultAutoIntakeSet(false);
LSR.setItem('d2r_plannerMade', JSON.stringify({ Grief: { id: 'grief', base: '7cr', baseName: 'Phase Blade', q: 'r', affixes: [], eth: false, sockets: 5, rolls: null } }));
var pmKey = null; H.RAW.forEach(function(v, k){ if (/d2r_plannerMade$/.test(k)) pmKey = k; });
var realParse = JSON.parse;
JSON.parse = function(s){ if (pmKey && typeof s === 'string' && s === H.RAW.get(pmKey)) C.plannerParse++; return realParse.apply(JSON, arguments); };
var KIND = { u: 'unique', s: 'set', r: 'runeword' };
var rows = window._cbHandCatalog('').rows.filter(function(r){ return r.q === 'u' || r.q === 's' || r.q === 'r'; });
var at = 0, added = [];
function addNext(){
  while (at < rows.length){
    var r = rows[at++];
    var res = window.vaultHandAdd(r.name, null, { kind: KIND[r.q] });
    H.flush(60, 3);
    if (res && res.ok && res.mode === 'added'){ added.push(res.name); return res; }
  }
  throw new Error('the catalogue ran out at ' + added.length + ' names');
}
function addUntil(n){ while (owned.size < n) addNext(); }
function one(){ reset(); var t0 = H.now(); var res = addNext(); var ms = H.now() - t0; var c = snapC(); c.ms = Math.round(ms * 10) / 10; c.owned = owned.size; c.name = res.name; return c; }
addUntil(39); OUT.at40 = one();
addUntil(159); OUT.at160 = one();
reset(); var t1 = H.now(); renderVault(); H.flush(60, 3); OUT.paint = snapC(); OUT.paint.ms = Math.round((H.now() - t1) * 10) / 10;
reset(); var t2 = H.now(); var cp = window.vaultHandAdd(added[3]); H.flush(60, 3); OUT.copy = snapC(); OUT.copy.ms = Math.round((H.now() - t2) * 10) / 10; OUT.copy.mode = cp && cp.mode;
OUT.grief = window._itemCells('Grief');
})();
"""

_OUT = {}


def measured():
    if "o" not in _OUT:
        _OUT["o"] = VPN.run(BODY, patches=PATCHES, prelude=PRELUDE, timeout=900)
    return _OUT["o"]


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AHandAddIsNotQuadratic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        o = measured()
        print("V1c hand add (node, counts are the verdict, ms is a report): at 40 %s | at 160 %s | paint %s | copy %s"
              % (json.dumps(o["at40"]), json.dumps(o["at160"]), json.dumps(o["paint"]), json.dumps(o["copy"])))

    def test_1_the_page_boots_and_the_door_adds(self):
        o = measured()
        self.assertEqual(o["__boot"]["errors"], [], "a page script did not run in node: %r" % o["__boot"])
        self.assertEqual((o["at40"]["owned"], o["at160"]["owned"]), (40, 160), "the door did not add one name each time")
        self.assertEqual(o["copy"]["mode"], "copy", "the copy add did not take the copy path: %r" % o["copy"])
        self.assertEqual((o["grief"]["w"], o["grief"]["h"]), (2, 3), "the planner record was not read: %r" % o["grief"])

    def test_2_router_asks_grow_with_the_vault_not_its_square(self):
        o = measured()
        a40, a160 = o["at40"]["ask"], o["at160"]["ask"]
        self.assertGreater(a40, 0, "PREMISE: the router counter never moved - the anchor counts nothing")
        self.assertLessEqual(a160, 4 * 160, "one add at 160 names asked the router %d times (budget 640, v3784: ~15 per name)" % a160)
        self.assertLessEqual(a40, 4 * 40, "one add at 40 names asked the router %d times (budget 160)" % a40)
        self.assertLessEqual(a160, 5 * a40, "router asks grew %.1fx from 40 to 160 names - linear is 4x" % (a160 / float(a40)))
        self.assertLessEqual(o["paint"]["ask"], 2 * 160, "one paint at 160 names asked the router %d times (budget 320)" % o["paint"]["ask"])
        self.assertLessEqual(o["copy"]["ask"], 6 * 160, "a copy add with its paint asked the router %d times (budget 960)" % o["copy"]["ask"])

    def test_3_a_name_is_folded_and_walked_once(self):
        o = measured()
        for k in ("at40", "at160", "copy"):
            self.assertLessEqual(o[k]["fold"], 2, "%s: %d fuzzy folds in one add (budget 2)" % (k, o[k]["fold"]))
            self.assertLessEqual(o[k]["lookupWalk"], 4, "%s: %d catalogue walks in one add (budget 4)" % (k, o[k]["lookupWalk"]))
            self.assertLessEqual(o[k]["itemsWalk"], 12, "%s: %d ITEMS walks in one add (budget 12)" % (k, o[k]["itemsWalk"]))
            self.assertLessEqual(o[k]["etherNorm"], 60, "%s: %d set-piece folds in one add (budget 60)" % (k, o[k]["etherNorm"]))

    def test_4_the_war_keeper_walks_each_bag_once(self):
        o = measured()
        for k in ("at40", "at160", "copy"):
            self.assertLessEqual(o[k]["keeperWalk"], 8, "%s: %d walks of the saved moves in one add (budget 8)" % (k, o[k]["keeperWalk"]))

    def test_5_the_planner_store_is_parsed_once_per_change(self):
        o = measured()
        for k in ("at40", "at160", "paint", "copy"):
            self.assertLessEqual(o[k]["plannerParse"], 1, "%s: d2r_plannerMade was parsed %d times though it did not change"
                                 % (k, o[k]["plannerParse"]))

    def test_6_a_paint_builds_the_records_a_few_times_not_per_locker(self):
        o = measured()
        self.assertGreater(o["paint"]["recordsBuild"], 0, "PREMISE: the records counter never moved")
        self.assertLessEqual(o["paint"]["recordsBuild"], 8, "one paint rebuilt the records %d times (budget 8)" % o["paint"]["recordsBuild"])
        for k in ("at40", "at160"):
            self.assertLessEqual(o[k]["recordsBuild"], 4, "%s: one add rebuilt the records %d times (budget 4)" % (k, o[k]["recordsBuild"]))
        # a copy add paints the vault itself (vaultHandAdd's copy path calls renderVault): the add's 4 and the paint's 8
        self.assertLessEqual(o["copy"]["recordsBuild"], 12, "a copy add with its paint rebuilt the records %d times (budget 12)"
                             % o["copy"]["recordsBuild"])


RED_PROOF = [
    {"why": "REG-2420 - the fuzzy fold is asked again for every runeword on every router ask",
     "file": "bible.html",
     "find": "    var memo = typeof name === 'string' && name !== '' && name === name.trim() && window._vaultMemoOff !== true",
     "replace": "    var memo = false && typeof name === 'string' && name !== '' && name === name.trim() && window._vaultMemoOff !== true",
     "matches": 1, "needs": "node"},
    {"why": "REG-2423 - d2rItemLookup walks the whole catalogue on every call again",
     "file": "bible.html",
     "find": "    if (window._vaultMemoOff === true || typeof Map !== 'function' || typeof ITEMS === 'undefined' || !ITEMS) return null;",
     "replace": "    if (true) return null;",
     "matches": 1, "needs": "node"},
    {"why": "REG-2421 - the war keeper walks every saved move for every item again",
     "file": "bible.html",
     "find": "    if (!_vaultWarKeeperIxOf || !bag || typeof bag !== 'object' || window._vaultMemoOff === true) return null;",
     "replace": "    if (true) return null;",
     "matches": 1, "needs": "node"},
    {"why": "REG-2424 - a read phase opens no memo: the router is asked ~15 times per owned name per add again",
     "file": "bible.html",
     "find": "    if (window._seamPaint || window._vaultMemoOff === true) return fn();",
     "replace": "    if (true) return fn();",
     "matches": 1, "needs": "node"},
    {"why": "REG-2426 - the shelf opens no records pass: every locker card rebuilds the whole vault three times again",
     "file": "bible.html",
     "find": "    if (window._vaultMemoOff !== true) window._vrFindPass = _vrShelfOuter || {};",
     "replace": "    if (false) window._vrFindPass = _vrShelfOuter || {};",
     "matches": 1, "needs": "node"},
    {"why": "#111 item 6 (REG-2422) - _itemCells asks _vpMadeOf again, which parses d2r_plannerMade before its cache",
     "file": "bible.html",
     "find": "    if (typeof window !== 'undefined' && window && typeof window._vpMadeBaseCode === 'function'){",
     "replace": "    if (false){",
     "matches": 1, "needs": "node"},
    {"why": "#111 item 6 (REG-2422) - the planner read parses d2r_plannerMade on every footprint and picture again",
     "file": "bible.html",
     "find": "      if (!(_vpMadeRO.ok && _vpMadeRO.raw === raw)){",
     "replace": "      if (true){",
     "matches": 1, "needs": "node"},
    {"why": "REG-2427 - _vaultKeeps walks all of ITEMS for every owned name again",
     "file": "bible.html",
     "find": "    if (window._vaultMemoOff === true || typeof Set !== 'function') return ITEMS.some(function(i){return i.n===n;});",
     "replace": "    if (true) return ITEMS.some(function(i){return i.n===n;});",
     "matches": 1, "needs": "node"},
    {"why": "REG-2425 - the set-piece fold runs for every pool name for every set piece again",
     "file": "bible.html",
     "find": "    var memo = !!_spNormMemo && typeof s === 'string' && window._vaultMemoOff !== true;",
     "replace": "    var memo = false;",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
