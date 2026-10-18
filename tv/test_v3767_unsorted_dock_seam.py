# -*- coding: utf-8 -*-
"""v3767 — the unsorted dock keeps only a name with no home.

Elad, the v3766 console, 2026-10-18: "Still showing them unsorted though."
The Vault showed UNSORTED DOCK 7 (Arachnid Mesh, Dracul's Grasp, Eschuta's Temper,
Grief, Splendor, Taebaek's Glory, War Traveler). Each row already named a home
(shared stash, a weapons cell, a runeword mule) and Eschuta's Temper and Splendor
said they stay on his character, and the summary said 2 filed to a mule the board
can't find (unsorted and the mules disagree) beside 7 still loose.

The dock was the legacy assign==null list. The row text is the router, asked at
paint time and never written, so d2r_vaultRecords derived "loose" from that same
list and never consumed the home. A lane lock was not a dock exclusion. An assign
id no roster mule has was counted filed by subtraction and orphan by the records.

The seam files a resolved home onto the existing record. A MAIN lock is keep.
A missing mule with no router home is loose, in the dock, and not an orphan.
No record is added or dropped. assign is not written, so Auto-Sort and reset
are not required.

RED_PROOF below. [[heart-first]] [[the-unjoined-end]] [[unknown-stays-unknown]] [[regression-guard]]
"""
import json
import os
import re
import shutil
import subprocess
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
BIBLE = os.path.join(HERE, "..", "bible.html")
NODE = os.environ.get("NODE") or shutil.which("node")

FNS = ["_vaultSeamHome", "_dockNames", "_vaultRecords", "_vaultReconcileHomes", "_vaultRecordsLoad"]


def _fn(src, name):
    m = re.search(r"\bfunction %s\s*\(" % re.escape(name), src)
    if not m:
        raise AssertionError("could not find function %s in bible.html" % name)
    i = src.index("{", m.start())
    depth, j = 0, i
    while j < len(src):
        c = src[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[m.start():j + 1]
        j += 1
    raise AssertionError("unbalanced braces extracting %s" % name)


PREAMBLE = r"""
var window = globalThis;
var owned = new Set();
var assign = {};
var magicFinds = {};
function ownedPool(){ return Array.from(owned).filter(function(n){ return !_inMagicRare(n); }).sort(); }
function copyCount(n){ return n === 'Grief' ? 2 : 1; }
function isSharedStash(){ return false; }
function _inMagicRare(){ return false; }
function muleById(id){
  var known = { shared: 'SHARED STASH', 'uni-weap': 'UNI-WEAPONS', runewords: 'RUNEWORDS', 'uni-small': 'UNI-JEWELRY', 'uni-armor': 'UNI-ARMOR' };
  return known[id] ? { id: id, name: known[id] } : null;
}
function suggestMule(name){
  if (name === 'Grief') return { id: 'uni-weap', why: 'war weapon' };
  if (name === 'Splendor') return { id: 'runewords', why: 'runeword' };
  if (name === 'Stone of Jordan') return { id: 'uni-small', why: 'ring' };
  if (name === 'Raven Frost') return { id: null, unsorted: true, why: 'the board cannot name it' };
  if (name === 'Rare Junk') return { id: null, unsorted: true, why: 'unknown' };
  if (name === "Sigon's Guard") return { id: '__throwout', why: 'low set piece' };
  if (name === 'Ghost Drawer') return { id: 'not-a-mule', why: 'guessed drawer' };
  if (name === 'Enigma' || name === 'Chronicle Raven') return { id: 'shared', why: 'war gear' };
  if (name === "Eschuta's Temper" || name === 'Arachnid Mesh' || name === "Dracul's Grasp" || name === "Taebaek's Glory" || name === 'War Traveler')
    return { id: 'shared', why: 'war gear' };
  return { id: null, unsorted: true, why: 'unknown' };
}
window._laneLockWhy = function(name){
  if (name === "Eschuta's Temper" || name === 'Splendor')
    return { lane: 'equipment', why: 'his gear, seen on his character' };
  return null;
};
window._carriedNames = function(){ return []; };
window._vaultLastSeenOnMain = function(name){ return name === 'Enigma' ? 'equipped' : null; };
var PROV = { 'Chronicle Raven': { looks: [{ loc: 'chronicle', scene: 'chronicle', frame: '9' }] } };
function _provAll(){ return PROV; }
function _isChronicleOnlyRow(row){
  var looks = (row && row.looks) || [];
  if (!looks.length) return false;
  return looks.every(function(e){
    return String((e && e.loc) || '').toLowerCase() === 'chronicle'
        || String((e && e.scene) || '').toLowerCase() === 'chronicle';
  });
}
var STORE = null;
function _vrRecLoadRaw(){ return STORE; }
function world(){
  owned.clear();
  Object.keys(assign).forEach(function(k){ delete assign[k]; });
  ['Arachnid Mesh', "Dracul's Grasp", "Eschuta's Temper", 'Grief', 'Splendor', "Taebaek's Glory", 'War Traveler',
   'Stone of Jordan', 'Raven Frost', 'Rare Junk', "Sigon's Guard", 'Ghost Drawer', 'Enigma', 'Chronicle Raven', 'Shako'].forEach(function(n){ owned.add(n); });
  assign['Stone of Jordan'] = 'no-such-mule';
  assign['Raven Frost'] = 'no-such-mule-2';
  assign['Shako'] = 'uni-armor';
}
function kindOf(rec, name){
  var rows = rec.records.filter(function(r){ return r.name === name; });
  return rows.map(function(r){ return { recId: r.recId, kind: r.kind, mule: r.mule }; });
}
"""


class TestV3767UnsortedDockSeam(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not NODE:
            raise AssertionError("node is not on this machine — this law does not skip")
        with open(BIBLE, encoding="utf-8") as f:
            cls.src = f.read()
        cls.bundle = "\n".join(_fn(cls.src, n) for n in FNS)

    def test_a_resolved_home_leaves_the_dock_and_the_record_keeps_one_location(self):
        prog = PREAMBLE + "\n" + self.bundle + r"""
world();
var before = Array.from(owned).length;
var rec = _vaultRecords();
var rec2 = _vaultRecords();
var ids = rec.records.map(function(r){ return r.recId; }).sort();
var ids2 = rec2.records.map(function(r){ return r.recId; }).sort();
STORE = { records: [
  { recId: 'Grief#0', name: 'Grief', copyIx: 0, kind: 'loose', mule: null, loc: 'loose' },
  { recId: 'Grief#1', name: 'Grief', copyIx: 1, kind: 'loose', mule: null, loc: 'loose' },
  { recId: "Eschuta's Temper#0", name: "Eschuta's Temper", copyIx: 0, kind: 'orphan', mule: null, loc: null },
  { recId: 'Stone of Jordan#0', name: 'Stone of Jordan', copyIx: 0, kind: 'orphan', mule: 'no-such-mule', loc: null },
  { recId: 'Raven Frost#0', name: 'Raven Frost', copyIx: 0, kind: 'orphan', mule: 'no-such-mule-2', loc: null },
  { recId: 'Shako#0', name: 'Shako', copyIx: 0, kind: 'filed', mule: 'uni-armor', loc: 'uni-armor' }
] };
var loaded = _vaultRecordsLoad();
var out = {
  dock: _dockNames(),
  owned: before,
  count: rec.records.length,
  ids: ids,
  idsSame: JSON.stringify(ids) === JSON.stringify(ids2),
  orphans: rec.orphans.map(function(o){ return o.name; }).sort(),
  grief: kindOf(rec, 'Grief'),
  mesh: kindOf(rec, 'Arachnid Mesh'),
  dracul: kindOf(rec, "Dracul's Grasp"),
  tae: kindOf(rec, "Taebaek's Glory"),
  trav: kindOf(rec, 'War Traveler'),
  eschuta: kindOf(rec, "Eschuta's Temper"),
  splendor: kindOf(rec, 'Splendor'),
  soj: kindOf(rec, 'Stone of Jordan'),
  raven: kindOf(rec, 'Raven Frost'),
  junk: kindOf(rec, 'Rare Junk'),
  sigon: kindOf(rec, "Sigon's Guard"),
  ghost: kindOf(rec, 'Ghost Drawer'),
  enigma: kindOf(rec, 'Enigma'),
  chron: kindOf(rec, 'Chronicle Raven'),
  shako: kindOf(rec, 'Shako'),
  assignGrief: Object.prototype.hasOwnProperty.call(assign, 'Grief'),
  assignSoj: assign['Stone of Jordan'],
  loadedN: loaded.records.length,
  loadedIds: loaded.records.map(function(r){ return r.recId; }).sort(),
  loadedGrief: kindOf(loaded, 'Grief'),
  loadedEschuta: kindOf(loaded, "Eschuta's Temper"),
  loadedSoj: kindOf(loaded, 'Stone of Jordan'),
  loadedRaven: kindOf(loaded, 'Raven Frost'),
  loadedShako: kindOf(loaded, 'Shako'),
  loadedOrphans: (loaded.orphans || []).map(function(o){ return o.name; })
};
console.log(JSON.stringify(out));
"""
        raw = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        self.assertEqual(raw.returncode, 0, raw.stderr[-2000:] + raw.stdout[-500:])
        o = json.loads(raw.stdout)
        dock = o["dock"]
        for gone in ["Arachnid Mesh", "Dracul's Grasp", "Eschuta's Temper", "Grief",
                     "Splendor", "Taebaek's Glory", "War Traveler", "Stone of Jordan", "Shako", "Enigma"]:
            self.assertNotIn(gone, dock, "%s still sits in the dock: %r" % (gone, dock))
        for stay in ["Raven Frost", "Rare Junk", "Sigon's Guard", "Ghost Drawer", "Chronicle Raven"]:
            self.assertIn(stay, dock, "%s left the dock and it has no home: %r" % (stay, dock))
        self.assertEqual(o["count"], 16, "a copy was dropped or duplicated: %s" % o["count"])
        self.assertEqual(o["owned"], 15)
        self.assertTrue(o["idsSame"])
        self.assertEqual(o["orphans"], [], "unsorted and the mules still disagree: %r" % o["orphans"])
        self.assertEqual(o["grief"], [
            {"recId": "Grief#0", "kind": "filed", "mule": "uni-weap"},
            {"recId": "Grief#1", "kind": "filed", "mule": "uni-weap"},
        ])
        for row in (o["mesh"], o["dracul"], o["tae"], o["trav"]):
            self.assertEqual(len(row), 1)
            self.assertEqual(row[0]["kind"], "sharedStash")
            self.assertIsNone(row[0]["mule"])
        self.assertEqual(o["eschuta"][0]["kind"], "keep")
        self.assertEqual(o["splendor"][0]["kind"], "keep")
        self.assertEqual(o["soj"], [{"recId": "Stone of Jordan#0", "kind": "filed", "mule": "uni-small"}])
        self.assertNotEqual(o["soj"][0]["mule"], "no-such-mule")
        self.assertEqual(o["raven"][0]["kind"], "loose")
        self.assertEqual(o["junk"][0]["kind"], "loose")
        self.assertEqual(o["sigon"][0]["kind"], "loose")
        self.assertEqual(o["ghost"][0]["kind"], "loose")
        self.assertIsNone(o["ghost"][0]["mule"])
        self.assertEqual(o["enigma"][0]["kind"], "keep")
        self.assertEqual(o["chron"][0]["kind"], "loose")
        self.assertEqual(o["shako"], [{"recId": "Shako#0", "kind": "filed", "mule": "uni-armor"}])
        self.assertFalse(o["assignGrief"], "the seam wrote assign and became an Auto-Sort")
        self.assertEqual(o["assignSoj"], "no-such-mule")
        self.assertEqual(o["loadedN"], 6)
        self.assertEqual(o["loadedIds"], [
            "Eschuta's Temper#0", "Grief#0", "Grief#1", "Raven Frost#0", "Shako#0", "Stone of Jordan#0",
        ])
        self.assertEqual(o["loadedGrief"], [
            {"recId": "Grief#0", "kind": "filed", "mule": "uni-weap"},
            {"recId": "Grief#1", "kind": "filed", "mule": "uni-weap"},
        ])
        self.assertEqual(o["loadedEschuta"][0]["kind"], "keep")
        self.assertEqual(o["loadedSoj"][0]["mule"], "uni-small")
        self.assertEqual(o["loadedRaven"][0]["kind"], "loose")
        self.assertEqual(o["loadedShako"][0]["mule"], "uni-armor")
        self.assertEqual(o["loadedOrphans"], [])

    def test_distinct_attacks_clear_the_vault_apply_wilson_bar(self):
        from confidence import confluence, wilson_lower
        import self_arming as SA
        bar = SA.LOCKS["vault.apply"]["bar"]
        kinds_bar = SA.LOCKS["vault.apply"]["kinds_bar"]
        n = len(RED_PROOF)
        w = wilson_lower(n, n)
        conf = confluence(["sabotage"], SA.KINDS)
        msg = ("unsorted dock seam: %d distinct attacks, wilson %.4f vs vault.apply bar %.3f; "
               "kinds sabotage %.2f vs %.2f" % (n, w, bar, conf, kinds_bar))
        print(msg)
        self.assertGreaterEqual(n, 12, msg)
        self.assertGreaterEqual(w, bar, msg)
        self.assertLess(conf, kinds_bar,
                        "one sabotage family must not read as enough to open the write door")


RED_PROOF = [
    {
        "why": "The dock still reads assign==null. A resolved home stays in the unsorted dock.",
        "file": "bible.html",
        "find": "var _seamD = (typeof _vaultSeamHome === 'function') ? _vaultSeamHome(n) : null; /* v3767 dock seam */",
        "replace": "var _seamD = null; /* v3767 dock seam */",
        "matches": 1,
    },
    {
        "why": "The records still derive loose from the legacy dock. A resolved home is an orphan.",
        "file": "bible.html",
        "find": "var _seamR = (typeof _vaultSeamHome === 'function') ? _vaultSeamHome(name) : null; /* v3767 records seam */",
        "replace": "var _seamR = null; /* v3767 records seam */",
        "matches": 1,
    },
    {
        "why": "A reload keeps the stored loose row. The home is never consumed.",
        "file": "bible.html",
        "find": "if (typeof _vaultReconcileHomes === 'function') recs = _vaultReconcileHomes(recs); /* v3767 dock reconcile */",
        "replace": "if (false && typeof _vaultReconcileHomes === 'function') recs = _vaultReconcileHomes(recs); /* v3767 dock reconcile */",
        "matches": 1,
    },
    {
        "why": "A MAIN-worn item stays in the dock. The lane lock is not a home.",
        "file": "bible.html",
        "find": "if (stayed && stayed.why) return { loc: 'keep', mule: null }; /* v3767 seam main */",
        "replace": "if (stayed && stayed.why) return { loc: 'loose', mule: null }; /* v3767 seam main */",
        "matches": 1,
    },
    {
        "why": "War gear the router already sent to the shared stash stays unsorted.",
        "file": "bible.html",
        "find": "if (sg.id === 'shared') return { loc: 'shared', mule: null }; /* v3767 seam shared */",
        "replace": "if (sg.id === 'shared') return { loc: 'loose', mule: null }; /* v3767 seam shared */",
        "matches": 1,
    },
    {
        "why": "A real mule id from the router stays unsorted. Grief sits in the dock.",
        "file": "bible.html",
        "find": "if (typeof muleById === 'function' && muleById(sg.id)) return { loc: 'filed', mule: sg.id }; /* v3767 seam route */",
        "replace": "if (typeof muleById === 'function' && muleById(sg.id)) return { loc: 'loose', mule: null }; /* v3767 seam route */",
        "matches": 1,
    },
    {
        "why": "A missing mule with no router home is filed and orphan at once. Unsorted and the mules disagree.",
        "file": "bible.html",
        "find": "return { loc: 'loose', mule: null }; /* v3767 seam ghost */",
        "replace": "return { loc: 'orphan', mule: mid }; /* v3767 seam ghost */",
        "matches": 1,
    },
    {
        "why": "The record keeps the ghost mule. The router home is not the location.",
        "file": "bible.html",
        "find": "else if (_seamR && _seamR.loc === 'filed' && _seamR.mule) { kind = 'filed'; mid = _seamR.mule; } /* v3767 records home */",
        "replace": "else if (false && _seamR && _seamR.loc === 'filed' && _seamR.mule) { kind = 'filed'; mid = _seamR.mule; } /* v3767 records home */",
        "matches": 1,
    },
    {
        "why": "A MAIN lock is not keep on the record, so the worn item is an orphan.",
        "file": "bible.html",
        "find": "else if (_seamR && _seamR.loc === 'keep') kind = 'keep'; /* v3767 records keep */",
        "replace": "else if (false && _seamR && _seamR.loc === 'keep') kind = 'keep'; /* v3767 records keep */",
        "matches": 1,
    },
    {
        "why": "Reconcile skips every stored row. A loose Grief stays loose on reload.",
        "file": "bible.html",
        "find": "if (r.kind !== 'loose' && r.kind !== 'orphan') return; /* v3767 reconcile kind */",
        "replace": "if (true) return; /* v3767 reconcile kind */",
        "matches": 1,
    },
    {
        "why": "Reconcile drops the records it was given.",
        "file": "bible.html",
        "find": "return records; /* v3767 reconcile return */",
        "replace": "return []; /* v3767 reconcile return */",
        "matches": 1,
    },
    {
        "why": "Throw-out advice becomes a home, so a discard leaves the dock.",
        "file": "bible.html",
        "find": "if (sg.id === '__throwout') return { loc: 'loose', mule: null }; /* v3767 seam discard */",
        "replace": "if (sg.id === '__throwout') return { loc: 'shared', mule: null }; /* v3767 seam discard */",
        "matches": 1,
    },
    {
        "why": "A name last seen on his MAIN is loose in the dock. Worn gear is given a mule.",
        "file": "bible.html",
        "find": "if (onMain) return { loc: 'keep', mule: null }; /* v3767 seam worn */",
        "replace": "if (false && onMain) return { loc: 'keep', mule: null }; /* v3767 seam worn */",
        "matches": 1,
    },
    {
        "why": "A chronicle-only tick is homed as a held copy. Found-ever is not a location.",
        "file": "bible.html",
        "find": "if (chron) return { loc: 'loose', mule: null }; /* v3767 seam chronicle */",
        "replace": "if (false && chron) return { loc: 'loose', mule: null }; /* v3767 seam chronicle */",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
