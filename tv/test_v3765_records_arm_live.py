# -*- coding: utf-8 -*-
"""#76 INC-3 live (v3765) — PAGE LOAD CALLS THE ARM ONCE.

v3764 left window._vaultRecordsArm dormant. This law is the one page-load call, from
_seedCleanseArm, and the reads that follow it. d2r_vaultRecords is the source for FIND,
GRAIL-DUPES and the vault header once the store is a real records array. A presence set
piece is one record at one location. The shelf card and the locker Items box print that
census. Undo is window._vaultRecordsMigrateUndo.

An unknown dock, an unreadable witness or a wrong store shape does not stamp. copies[] is
not rewritten. recId stays positional (REG-2272 item 4): a dropped copy reuses the prefix
id. That item stays open. The write door stays shut on sabotage alone.

The functions are extracted from bible.html and run in node on a seeded fixture, with an
in-memory window.LSR. A missing node raises. RED_PROOF below.
[[heart-first]] [[the-unjoined-end]] [[unknown-stays-unknown]] [[regression-guard]]
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

EXTRACT = [
    "_sharedNames", "_sharedCopyCount", "_sharedCappedCopies", "_vaultSharedOverflowCells",
    "_vaultSharedOverflowNames",
    "_vaultPresenceSpan", "_vaultRecords", "_vaultRecordsSource", "_vaultLockerItems",
    "_vaultRecordsHeader", "_vaultRecordsFind", "_vaultRecordsOverflow",
    "_vrRecLoadRaw", "_vrRecGuardedSet", "_vrLocForCopy", "_vaultRecordsLoad",
    "_vaultRecordsPersist", "_vaultRecordsMigrate", "_vaultRecordsMigrateUndo", "_vaultRecordsArm",
    "_shelfCopyCount", "_shelfDrawNames", "_muleLoad",
]

PREAMBLE = r"""
var window = globalThis;
window.D2R_PROFILE = 'main';
console.info = function(){ try { process.stderr.write('[info] ' + Array.prototype.join.call(arguments, ' ') + '\n'); } catch (e) {} };
console.log = console.info;
console.warn = function(){ try { process.stderr.write('[warn] ' + Array.prototype.join.call(arguments, ' ') + '\n'); } catch (e) {} };
var _LSRDATA = {};
window.LSR = {
  getItem: function(k){ return Object.prototype.hasOwnProperty.call(_LSRDATA, k) ? _LSRDATA[k] : null; },
  setItem: function(k, v){ _LSRDATA[k] = String(v); },
  removeItem: function(k){ delete _LSRDATA[k]; }
};
var _VR_STORE_KEY = 'd2r_vaultRecords';
var _VRM_KEY = 'd2r_vaultRecordsMigrate';
var _VRM_VER = 1;
var _vrRecUnread = {};
var NATALYA = "Natalya's Totem";
var TAL = "Tal Rasha's Guardianship";
var IK = "Immortal King's Soul Cage";
var ENIGMA = "Enigma";
var GRIFFON = "Griffon's Eye";
var assign = {};
assign[NATALYA] = 'mule-sets';
assign[TAL] = 'mule-sets';
assign[IK] = 'mule-sets';
assign[ENIGMA] = 'mule-sets';
assign[GRIFFON] = 'shared';
var copies = {};
copies[NATALYA] = 4;
copies[TAL] = 4;
copies[IK] = 3;
copies[ENIGMA] = 2;
copies[GRIFFON] = 4;
var OWNED = [NATALYA, TAL, IK, ENIGMA, GRIFFON];
var multiKeep = {};
var SET_PIECES = {};
SET_PIECES[NATALYA] = 1;
SET_PIECES[TAL] = 1;
SET_PIECES[IK] = 1;
window._vfIsSetPiece = function(n){ return !!SET_PIECES[n]; };
var _SHARED_COPY_CAP = 2, _MULE_COPY_CAP = 3;
function ownedPool(){ return OWNED.slice(); }
function copyCount(n){ var c = copies[n]; return (c && c > 0) ? c : (OWNED.indexOf(n) >= 0 ? 1 : 0); }
function isSharedStash(n){ return false; }
function muleById(id){ return (id === 'mule-sets' || id === 'mule-other') ? { id: id, name: id } : null; }
function _dockNames(){ return []; }
window._carriedNames = function(){ return []; };
var KEEP_IN_INVENTORY = /Annihilus|Hellfire Torch|Gheed/;
function _keepName(n){ return n; }
function _mpInvSeeds(){ return { hold: {}, at: {}, bad: [], n: 0 }; }
function vaultSize(){ return [1, 1]; }
function tipOf(){ return null; }
function _muleItemKey(n, ci){ return ci ? n + ' #' + (ci + 1) : n; }
function _mulePosAll(){ return {}; }
var MULE_STASH_W = 10, MULE_STASH_H = 10, MULE_INV_W = 10, MULE_INV_H = 4, MULE_CAP = 140;
var MULE_AREAS = {
  personal: [10, 10, 'Personal'], shared: [10, 10, 'Shared'], gems: [10, 10, 'Gems'],
  materials: [10, 10, 'Materials'], runes: [10, 10, 'Runes'], inv: [10, 4, 'Inventory']
};
function packGrid(items){
  var placed = (items || []).map(function(it, i){
    return { n: it.n, key: it.key, x: 0, y: i, w: it.w || 1, h: it.h || 1 };
  });
  return { placed: placed, left: [] };
}
"""


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


def _assigned_fn(src, name):
    m = re.search(r"window\.%s\s*=\s*function\s*\(" % re.escape(name), src)
    if not m:
        raise AssertionError("could not find window.%s" % name)
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
    raise AssertionError("unbalanced braces extracting window.%s" % name)


def _strip(src):
    return re.sub(r"/\*.{0,4000}?\*/", "", src, flags=re.S)


class TestV3765RecordsArmLive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not NODE:
            raise AssertionError("node is not on this machine — this law does not skip")
        with open(BIBLE, encoding="utf-8") as f:
            cls.src = f.read()
        cls.fns = "\n".join(_fn(cls.src, n) for n in EXTRACT)

    def _line(self, needle):
        hits = [ln.strip() for ln in self.src.splitlines() if needle in ln]
        if len(hits) != 1:
            raise AssertionError("%r matched %d lines" % (needle, len(hits)))
        return hits[0]

    def _run(self, scenario):
        prog = (PREAMBLE + self.fns +
                "\nwindow._vaultPresenceSpan = _vaultPresenceSpan;\nvar out = {};\n" +
                scenario + "\nprocess.stdout.write(JSON.stringify(out));\n")
        p = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, (p.stderr or p.stdout)[-2000:])
        return json.loads(p.stdout)

    def test_page_load_calls_the_arm_once(self):
        code = _strip(self.src)
        self.assertEqual(code.count("_vaultRecordsArm("), 2,
                         "arm sites drifted from the definition plus the one page-load call")
        self.assertEqual(code.count("_vaultRecordsMigrate("), 2,
                         "a second caller of the migrate function appeared")
        self.assertEqual(code.count("_vaultRecordsPersist("), 2,
                         "a second caller of persist appeared")
        body = _strip(_assigned_fn(self.src, "_seedCleanseArm"))
        self.assertEqual(body.count("_vaultRecordsArm("), 1,
                         "the page-load call is not the one inside _seedCleanseArm")
        self.assertIn("window._vaultRecordsMigrateUndo", code)

    def test_a_presence_set_piece_is_one_record_at_one_location(self):
        o = self._run(r"""
var before = JSON.stringify(copies);
var a = _vaultRecordsArm();
var loaded = _vaultRecordsLoad();
function pack(name){
  return loaded.records.filter(function(r){ return r.name === name; }).map(function(r){
    return r.loc;
  });
}
out.stamped = !!(a && a.stamped);
out.seam = a && a.seam;
out.copyIdentity = a && a.copyIdentity;
out.nat = pack(NATALYA);
out.tal = pack(TAL);
out.ik = pack(IK);
out.enigma = pack(ENIGMA);
out.griffon = pack(GRIFFON);
out.copiesSame = JSON.stringify(copies) === before;
out.shelfNat = _shelfDrawNames([NATALYA], 'mule-sets').length;
out.shelfTal = _shelfDrawNames([TAL], 'mule-sets').length;
out.shelfIk = _shelfDrawNames([IK], 'mule-sets').length;
out.shelfEnigma = _shelfDrawNames([ENIGMA], 'mule-sets').length;
out.physNat = _muleLoad([NATALYA], null, 'mule-sets', {}).phys;
out.physTal = _muleLoad([TAL], null, 'mule-sets', {}).phys;
out.physIk = _muleLoad([IK], null, 'mule-sets', {}).phys;
out.physEnigma = _muleLoad([ENIGMA], null, 'mule-sets', {}).phys;
out.storedCopies = copies[NATALYA];
""")
        self.assertTrue(o["stamped"], o)
        self.assertEqual(o["seam"], "page-load")
        self.assertEqual(o["copyIdentity"], "positional")
        self.assertEqual(o["nat"], ["mule-sets"], "Natalya x4 stayed more than one record: %r" % o["nat"])
        self.assertEqual(o["tal"], ["mule-sets"], "Tal Guardianship x4 stayed more than one record: %r" % o["tal"])
        self.assertEqual(o["ik"], ["mule-sets"], "IK Soul Cage x3 stayed more than one record: %r" % o["ik"])
        self.assertEqual(o["enigma"], ["mule-sets", "mule-sets"],
                         "a non-set spare was collapsed: %r" % o["enigma"])
        self.assertEqual(len(o["griffon"]), 4, "a non-set shared name was collapsed: %r" % o["griffon"])
        self.assertTrue(o["copiesSame"], "the span rewrote copies[]")
        self.assertEqual(o["storedCopies"], 4)
        self.assertEqual(o["shelfNat"], 1, o)
        self.assertEqual(o["shelfTal"], 1, o)
        self.assertEqual(o["shelfIk"], 1, o)
        self.assertEqual(o["shelfEnigma"], 2, o)
        self.assertEqual(o["physNat"], 1, o)
        self.assertEqual(o["physTal"], 1, o)
        self.assertEqual(o["physIk"], 1, o)
        self.assertEqual(o["physEnigma"], 2, o)

    def test_an_explicit_multi_keep_keeps_the_spare(self):
        o = self._run(r"""
multiKeep[IK] = 2;
var before = copies[IK];
_vaultRecordsArm();
var loaded = _vaultRecordsLoad();
out.ik = loaded.records.filter(function(r){ return r.name === IK; }).length;
out.nat = loaded.records.filter(function(r){ return r.name === NATALYA; }).length;
out.copies = copies[IK];
out.before = before;
""")
        self.assertEqual(o["ik"], 3, "a multi-keep above 1 was collapsed: %r" % o)
        self.assertEqual(o["nat"], 1, o)
        self.assertEqual(o["copies"], o["before"])

    def test_the_card_and_the_items_box_print_one_census(self):
        card = self._line("var _ci76 = _vaultLockerItems(m.id)")
        locker = self._line("var _li76 = _vaultLockerItems(muleId)")
        o = self._run(r"""
_vaultRecordsArm();
assign.Shako = 'mule-sets';
OWNED.push('Shako');
var liveNames = [NATALYA, TAL, IK, ENIGMA, 'Shako'];
var drawn = _shelfDrawNames(liveNames, 'mule-sets');
var _itemN = (new Set(drawn)).size;
var muleId = 'mule-sets';
var m = { id: muleId };
var _physN = _muleLoad(liveNames, null, muleId, {}).phys;
var _namesN = liveNames.length;
out.fallback = _itemN;
""" + "\n" + card + "\n" + locker + r"""
out.itemN = _itemN;
out.namesN = _namesN;
out.physN = _physN;
out.census = _vaultLockerItems(muleId);
""")
        self.assertEqual(o["fallback"], 5, "the live card list did not pick up the later name: %r" % o)
        self.assertEqual(o["census"], 4, "the stored census moved with the later edit: %r" % o)
        self.assertEqual(o["itemN"], o["census"], "the card did not print the census: %r" % o)
        self.assertEqual(o["namesN"], o["census"], "the Items box did not print the census: %r" % o)
        self.assertEqual(o["itemN"], o["namesN"], "card and Items diverged: %r" % o)
        self.assertGreater(o["physN"], o["itemN"],
                           "the shared count was the physical copy total: %r" % o)

    def test_find_and_dupes_read_the_persisted_store(self):
        o = self._run(r"""
_vaultRecordsArm();
out.overflowAtArm = _vaultRecordsOverflow();
out.liveAtArm = _vaultSharedOverflowNames();
out.findAtArm = _vaultRecordsFind(NATALYA);
copies[GRIFFON] = 1;
assign[NATALYA] = 'mule-other';
out.overflowAfter = _vaultRecordsOverflow();
out.liveAfter = _vaultSharedOverflowNames();
out.findAfter = _vaultRecordsFind(NATALYA);
var live = _vaultRecords();
var rec = null;
for (var i = 0; i < live.records.length; i++){
  if (live.records[i].name === NATALYA){ rec = live.records[i]; break; }
}
out.liveFind = rec && rec.kind === 'filed' ? rec.mule : null;
""")
        self.assertEqual(o["overflowAtArm"], ["Griffon's Eye"], o)
        self.assertEqual(o["overflowAtArm"], o["liveAtArm"], o)
        self.assertEqual(o["findAtArm"], "mule-sets", o)
        self.assertEqual(o["overflowAfter"], ["Griffon's Eye"],
                         "GRAIL-DUPES left the persisted store: %r" % o)
        self.assertEqual(o["liveAfter"], [], o)
        self.assertEqual(o["findAfter"], "mule-sets", "FIND left the persisted store: %r" % o)
        self.assertEqual(o["liveFind"], "mule-other", o)

    def test_an_unknown_dock_does_not_stamp(self):
        o = self._run(r"""
function probe(mode){
  _vrRecUnread = {};
  window.LSR.removeItem('d2r_vaultRecords');
  window.LSR.removeItem('d2r_vaultRecordsMigrate');
  if (OWNED.indexOf('Nagelring') < 0) OWNED.push('Nagelring');
  if (mode === 'missing') _dockNames = null;
  if (mode === 'null') _dockNames = function(){ return null; };
  var a = _vaultRecordsArm();
  return {
    stamped: !!(a && a.stamped),
    unknown: !!(a && a.unknown),
    store: window.LSR.getItem('d2r_vaultRecords') != null,
    stamp: window.LSR.getItem('d2r_vaultRecordsMigrate') != null
  };
}
out.missing = probe('missing');
out.nullDock = probe('null');
""")
        for which in ("missing", "nullDock"):
            row = o[which]
            self.assertFalse(row["stamped"], which + " stamped: %r" % row)
            self.assertTrue(row["unknown"], which + " was not UNKNOWN: %r" % row)
            self.assertFalse(row["store"], which)
            self.assertFalse(row["stamp"], which)

    def test_a_wrong_shape_store_does_not_stamp(self):
        o = self._run(r"""
function probe(raw){
  _vrRecUnread = {};
  window.LSR.setItem('d2r_vaultRecords', raw);
  window.LSR.removeItem('d2r_vaultRecordsMigrate');
  var a = _vaultRecordsArm();
  return {
    stamped: !!(a && a.stamped),
    bytes: window.LSR.getItem('d2r_vaultRecords'),
    stamp: window.LSR.getItem('d2r_vaultRecordsMigrate') != null
  };
}
out.arr = probe('[]');
out.obj = probe('{"v":1}');
out.badRec = probe('{"records":{}}');
""")
        for key, raw in (("arr", "[]"), ("obj", '{"v":1}'), ("badRec", '{"records":{}}')):
            row = o[key]
            self.assertFalse(row["stamped"], key + " stamped: %r" % row)
            self.assertEqual(row["bytes"], raw, key + " was overwritten: %r" % row)
            self.assertFalse(row["stamp"], key)

    def test_an_unreadable_witness_does_not_stamp(self):
        o = self._run(r"""
window.LSR.setItem('d2r_vaultProv', '{bad');
var a = _vaultRecordsArm();
var loaded = _vaultRecordsLoad();
out.stamped = !!(a && a.stamped);
out.unknown = !!(a && a.unknown);
out.store = window.LSR.getItem('d2r_vaultRecords') != null;
out.stamp = window.LSR.getItem('d2r_vaultRecordsMigrate') != null;
out.marked = !!(loaded && loaded.records.length && loaded.records.every(function(r){
  return r.provUnknown === true && !('prov' in r);
}));
""")
        self.assertFalse(o["stamped"], "an unreadable witness stamped: %r" % o)
        self.assertTrue(o["unknown"], o)
        self.assertTrue(o["store"], "persist did not leave the marker store: %r" % o)
        self.assertFalse(o["stamp"], o)
        self.assertTrue(o["marked"], "the marker was stored as a null witness: %r" % o)

    def test_undo_clears_both_keys_and_a_stamp_throw_leaves_the_store(self):
        o = self._run(r"""
var copiesBefore = JSON.stringify(copies);
var assignBefore = JSON.stringify(assign);
_vaultRecordsArm();
var u = _vaultRecordsMigrateUndo();
out.undone = !!(u && u.undone);
out.store = window.LSR.getItem('d2r_vaultRecords') != null;
out.stamp = window.LSR.getItem('d2r_vaultRecordsMigrate') != null;
out.copiesSame = JSON.stringify(copies) === copiesBefore;
out.assignSame = JSON.stringify(assign) === assignBefore;
var again = _vaultRecordsArm();
out.rearmed = !!(again && again.stamped);
var realRemove = window.LSR.removeItem.bind(window.LSR);
window.LSR.removeItem = function(k){
  if (k === 'd2r_vaultRecordsMigrate') throw new Error('stamp disk');
  return realRemove(k);
};
var u2 = _vaultRecordsMigrateUndo();
out.throwUndone = !!(u2 && u2.undone);
out.throwStore = window.LSR.getItem('d2r_vaultRecords') != null;
out.throwStamp = window.LSR.getItem('d2r_vaultRecordsMigrate') != null;
""")
        self.assertTrue(o["undone"], o)
        self.assertFalse(o["store"], o)
        self.assertFalse(o["stamp"], o)
        self.assertTrue(o["copiesSame"], o)
        self.assertTrue(o["assignSame"], o)
        self.assertTrue(o["rearmed"], o)
        self.assertFalse(o["throwUndone"], "a stamp remove that threw reported undone: %r" % o)
        self.assertTrue(o["throwStore"], "a stamp remove that threw dropped the store: %r" % o)
        self.assertTrue(o["throwStamp"], o)

    def test_a_dropped_copy_reuses_the_prefix_id(self):
        """REG-2272 item 4 stays open. The survivor takes the lower positional id.

        No cell, witness or frame was named as the per-copy anchor, so this law does not
        invent one. The arm keeps reporting copyIdentity positional."""
        o = self._run(r"""
_vaultRecordsPersist();
var loaded = _vaultRecordsLoad();
var ids = loaded.records.filter(function(r){ return r.name === ENIGMA; }).map(function(r){ return r.recId; });
copies[ENIGMA] = 1;
_vaultRecordsPersist();
var loaded2 = _vaultRecordsLoad();
var ids2 = loaded2.records.filter(function(r){ return r.name === ENIGMA; }).map(function(r){ return r.recId; });
var a = _vaultRecordsArm();
out.ids = ids;
out.ids2 = ids2;
out.copyIdentity = a && a.copyIdentity;
""")
        self.assertEqual(len(o["ids"]), 2, o)
        self.assertEqual(o["ids2"], [o["ids"][0]],
                         "a dropped copy did not keep the positional prefix id: %r" % o)
        self.assertEqual(o["copyIdentity"], "positional", o)

    def test_distinct_attacks_clear_the_write_door_wilson_bar(self):
        """vault.apply bar. One RED_PROOF is one attack. Sabotage does not open the door."""
        from confidence import confluence, wilson_lower
        import self_arming as SA
        bar = SA.LOCKS["vault.apply"]["bar"]
        kinds_bar = SA.LOCKS["vault.apply"]["kinds_bar"]
        n = len(RED_PROOF)
        w = wilson_lower(n, n)
        conf = confluence(["sabotage"], SA.KINDS)
        msg = ("vault-records arm: %d distinct attacks, wilson %.4f vs write-door bar %.3f; "
               "kinds sabotage %.2f vs %.2f" % (n, w, bar, conf, kinds_bar))
        print(msg)
        self.assertGreaterEqual(n, 10, msg)
        self.assertGreaterEqual(w, bar, msg)
        self.assertLess(conf, kinds_bar,
                        "one sabotage family must not read as enough to open the write door")


RED_PROOF = [
    {
        "why": "Page load must call the arm once. Removing that call leaves d2r_vaultRecords unwired.",
        "file": "bible.html",
        "find": "          try { window._vaultRecordsArm(); } catch (eArm) {}   /* #76 INC-3 v3765 — the one page-load call, after the set-piece fold */",
        "replace": "          /* page-load call removed */",
        "matches": 1,
    },
    {
        "why": "A second page-load call is another door. The arm count leaves two.",
        "file": "bible.html",
        "find": "          try { window._vaultRecordsArm(); } catch (eArm) {}   /* #76 INC-3 v3765 — the one page-load call, after the set-piece fold */",
        "replace": "          try { window._vaultRecordsArm(); } catch (eArm) {}\n          try { window._vaultRecordsArm(); } catch (eArm) {}",
        "matches": 1,
    },
    {
        "why": "A presence set piece is one record. Returning the raw count puts Natalya x4, Tal x4 and Soul Cage x3 back.",
        "file": "bible.html",
        "find": "      if (!(typeof multiKeep !== 'undefined' && multiKeep && multiKeep[name] > 1)) return 1;",
        "replace": "      if (!(typeof multiKeep !== 'undefined' && multiKeep && multiKeep[name] > 1)) return have;",
        "matches": 1,
    },
    {
        "why": "The record model has to use the presence span. Without it the store keeps copyCount records.",
        "file": "bible.html",
        "find": "        if (typeof _vaultPresenceSpan === 'function') { var _psRec = _vaultPresenceSpan(name, cc); if (_psRec != null) cc = _psRec; }",
        "replace": "        /* presence span removed from the record model */",
        "matches": 1,
    },
    {
        "why": "The shelf card draws one tile for a presence set piece. Without the span a x4 name draws the capped copies.",
        "file": "bible.html",
        "find": "    if (typeof _vaultPresenceSpan === 'function') { var _psShelf = _vaultPresenceSpan(n, c); if (_psShelf != null) c = _psShelf; }",
        "replace": "    /* presence span removed from the shelf */",
        "matches": 1,
    },
    {
        "why": "The locker packs one copy of a presence set piece. Without the span it packs the capped copy count.",
        "file": "bible.html",
        "find": "      if (typeof _vaultPresenceSpan === 'function') { var _psMule = _vaultPresenceSpan(n, cc); if (_psMule != null) cc = Math.max(1, Math.min(_psMule, _MULE_COPY_CAP)); }",
        "replace": "      /* presence span removed from the locker pack */",
        "matches": 1,
    },
    {
        "why": "The Items box prints the one-record census. Putting the physical copy total back makes the card come out lower.",
        "file": "bible.html",
        "find": "if (typeof _li76 === 'number') _namesN = _li76;",
        "replace": "if (typeof _li76 === 'number') _namesN = _physN;",
        "matches": 1,
    },
    {
        "why": "The shelf card prints the same census. A null census leaves the live name list, which a later edit moves.",
        "file": "bible.html",
        "find": "var _ci76 = _vaultLockerItems(m.id);",
        "replace": "var _ci76 = null;",
        "matches": 1,
    },
    {
        "why": "An unreadable witness must not stamp. Skipping the marker check latches the migration over UNKNOWN.",
        "file": "bible.html",
        "find": "    if (back.records.some(function(row){ return row && row.provUnknown === true; }))",
        "replace": "    if (false && back.records.some(function(row){ return row && row.provUnknown === true; }))",
        "matches": 1,
    },
    {
        "why": "An unknown dock must not stamp. Dropping the guard persists the guess.",
        "file": "bible.html",
        "find": "if (rec.carUnknown || rec.dockUnknown) return { ok: false, wrote: false, unknown: true, why: 'carried or dock is UNKNOWN - nothing persisted' };",
        "replace": "if (false && (rec.carUnknown || rec.dockUnknown)) return { ok: false, wrote: false, unknown: true, why: 'carried or dock is UNKNOWN - nothing persisted' };",
        "matches": 1,
    },
    {
        "why": "A wrong-shape store is UNKNOWN. Returning null treats it as absent, so the arm overwrites it and stamps.",
        "file": "bible.html",
        "find": "        _vrRecUnread[_VR_STORE_KEY] = 'wrong shape';\n        return undefined;\n",
        "replace": "        return null;\n",
        "matches": 1,
    },
    {
        "why": "FIND and GRAIL-DUPES read the persisted store. Falling through to the live model drops the snapshot.",
        "file": "bible.html",
        "find": "        if (loaded && loaded.ok && Array.isArray(loaded.records)) return loaded;",
        "replace": "        return _vaultRecords();",
        "matches": 1,
    },
    {
        "why": "The arm is the migration. Cutting that call leaves the page-load seam as a no-op.",
        "file": "bible.html",
        "find": "    var r = _vaultRecordsMigrate();\n",
        "replace": "    var r = { ran: false, stamped: false, why: 'seam cut' };\n",
        "matches": 1,
    },
    {
        "why": "Undo removes the stamp before the store. Removing the store first, then throwing on the stamp, leaves the gate with nothing behind it.",
        "file": "bible.html",
        "find": "    try { window.LSR.removeItem(_VRM_KEY); }\n",
        "replace": "    try { window.LSR.removeItem(_VR_STORE_KEY); }\n",
        "matches": 1,
    },
    {
        "why": "recId stays positional. Reporting another identity would close REG-2272 item 4 without an anchor.",
        "file": "bible.html",
        "find": "    r.copyIdentity = 'positional';",
        "replace": "    r.copyIdentity = 'cell';",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
