# -*- coding: utf-8 -*-
"""#76 REG-2272 item 6 — the records model classifies the shared LOCKER the way production does.

_sharedNames() is assign === 'shared': the shared locker, including war gear the never-muled regex
does not match. isSharedStash() is that regex (runes, shards, sunders). The INC-2/INC-3b fixtures
stubbed isSharedStash to mean assign === 'shared' and made muleById('shared') return null, so the
two never met. In production muleById('shared') is a real roster locker, and the filed branch then
called war gear a mule home: kind filed, mule 'shared', every copy loc the mule id, rule E skipped.
FIND was given a mule. An unassigned regex material is sharedStash by the header and is NOT in the
locker, but the persist overflow view walked kind, so a 4-copy shard read as trade-stock.

This law extracts the SHIPPED functions, including the real isSharedStash and SHARED_STASH_RE, and
gives muleById the shared locker. It does not stub the two shared notions into one.

  · a locker name the regex misses (Enigma, 4 copies) is sharedStash, mule null, copyIx 0..3,
    and the persisted loc is the rule-E split (shared, shared, dupes, dupes);
  · FIND does not give that name a mule home;
  · overflow membership is _sharedNames on the live view, the records view, and the loaded store.
    An unassigned Worldstone Shard with 4 copies is sharedStash and is NOT overflow;
  · a real mule filing stays filed;
  · carried still wins over the locker, in the header's order.

Copy-loss ids (REG-2272 item 4) are NOT this law. copies[name] is a count. Which physical copy
left is not in the source stores, and no note names the anchor. That stays open.

NOT wired: the migration stays dormant. A missing node raises. RED_PROOF below.
[[the-unjoined-end]] [[unknown-stays-unknown]] [[heart-first]] [[regression-guard]]
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
    "_vaultSharedOverflowNames", "isSharedStash",
    "_vaultRecords", "_vaultRecordsFind", "_vaultRecordsOverflow", "_vaultRecordsHeader",
    "_vrRecLoadRaw", "_vrRecGuardedSet", "_vrLocForCopy", "_vaultRecordsLoad", "_vaultRecordsPersist",
    "_vaultRecordsViewFind", "_vaultRecordsViewOverflow", "_vaultRecordsViewHeader",
]

PREAMBLE = r"""
var window = globalThis;
window.D2R_PROFILE = 'main';
console.info = function(){ try { process.stderr.write('[info] ' + Array.prototype.join.call(arguments, ' ') + '\n'); } catch(e){} };
console.log = console.info;
console.warn = function(){ try { process.stderr.write('[warn] ' + Array.prototype.join.call(arguments, ' ') + '\n'); } catch(e){} };
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
// Enigma is war gear filed to the shared locker and is NOT a never-muled regex name.
// Ist rune is in the locker AND matches the regex. Worldstone Shard matches the regex and is NOT filed.
// Shako is a real mule. Nagelring is loose. Grief is carried AND in the locker — carried wins.
var assign = { Enigma:'shared', 'Ist rune':'shared', Shako:'mule1', Grief:'shared' };
var copies = { Enigma:4, 'Worldstone Shard':4 };
var OWNED = ['Enigma', 'Ist rune', 'Worldstone Shard', 'Shako', 'Nagelring', 'Grief'];
var _SHARED_COPY_CAP = 2, _MULE_COPY_CAP = 3;
function ownedPool(){ return OWNED.slice(); }
function copyCount(n){ var c = copies[n]; return (c && c > 0) ? c : (OWNED.indexOf(n) >= 0 ? 1 : 0); }
function muleById(id){
  if (id === 'mule1') return { id:'mule1', name:'Mule One' };
  if (id === 'shared') return { id:'shared', name:'SHARED STASH' };
  return null;
}
function _dockNames(){ return ['Nagelring']; }
window._carriedNames = function(){ return [{ name:'Grief' }]; };
var KEEP_IN_INVENTORY = /Annihilus|Hellfire Torch|Gheed/;
function _keepName(n){ return n; }
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


def _var(src, name):
    m = re.search(r"^  var %s = .*;$" % re.escape(name), src, re.M)
    if not m:
        raise AssertionError("could not find var %s in bible.html" % name)
    return m.group(0)


class TestV3764RecordsClassificationParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not NODE:
            raise AssertionError("node is not on this machine — this law does not skip")
        with open(BIBLE, encoding="utf-8") as f:
            cls.src = f.read()
        cls.fns = _var(cls.src, "SHARED_STASH_RE") + "\n" + "\n".join(_fn(cls.src, n) for n in EXTRACT)

    def _run(self, scenario):
        prog = PREAMBLE + self.fns + "\nvar out = {};\n" + scenario + "\nprocess.stdout.write(JSON.stringify(out));\n"
        p = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, (p.stderr or p.stdout)[-2000:])
        return json.loads(p.stdout)

    def test_the_shared_locker_matches_production_names_and_copy_locations(self):
        o = self._run(r"""
var mem = _vaultRecords();
function pack(name){
  return mem.records.filter(function(r){ return r.name === name; }).map(function(r){
    return { copyIx: r.copyIx, kind: r.kind, mule: r.mule };
  });
}
out.war = pack('Enigma');
out.rune = pack('Ist rune');
out.shard = pack('Worldstone Shard');
out.filed = pack('Shako');
out.carried = pack('Grief');
out.findWar = _vaultRecordsFind('Enigma');
out.findFiled = _vaultRecordsFind('Shako');
out.findShard = _vaultRecordsFind('Worldstone Shard');
out.sharedNames = _sharedNames();
out.liveOverflow = _vaultSharedOverflowNames();
out.recOverflow = _vaultRecordsOverflow();
out.memOverflow = _vaultRecordsViewOverflow(mem);
var pr = _vaultRecordsPersist();
var loaded = _vaultRecordsLoad();
out.persistOk = !!pr.ok;
out.locWar = loaded.records.filter(function(r){ return r.name === 'Enigma'; }).map(function(r){ return r.loc; });
out.loadedOverflow = _vaultRecordsViewOverflow(loaded);
out.regexMissesWar = !isSharedStash('Enigma');
out.regexHitsShard = !!isSharedStash('Worldstone Shard');
""")
        self.assertTrue(o["regexMissesWar"], "Enigma must stay outside the never-muled regex or this law is vacuous")
        self.assertTrue(o["regexHitsShard"], "Worldstone Shard must match the never-muled regex")
        self.assertEqual(o["sharedNames"], ["Enigma", "Grief", "Ist rune"],
                         "production _sharedNames drifted: %r" % o["sharedNames"])
        self.assertEqual(o["war"], [
            {"copyIx": 0, "kind": "sharedStash", "mule": None},
            {"copyIx": 1, "kind": "sharedStash", "mule": None},
            {"copyIx": 2, "kind": "sharedStash", "mule": None},
            {"copyIx": 3, "kind": "sharedStash", "mule": None},
        ], "a shared-locker name the regex misses was not classified as the locker: %r" % o["war"])
        self.assertIsNone(o["findWar"], "FIND gave the shared locker a mule home: %r" % o["findWar"])
        self.assertTrue(o["persistOk"], "persist refused a readable store: %r" % o)
        self.assertEqual(o["locWar"], ["shared", "shared", "dupes", "dupes"],
                         "rule E did not split the locker's copies: %r" % o["locWar"])
        self.assertEqual(o["rune"], [{"copyIx": 0, "kind": "sharedStash", "mule": None}], o["rune"])
        self.assertEqual(o["shard"], [
            {"copyIx": i, "kind": "sharedStash", "mule": None} for i in range(4)
        ], "an unassigned regex material left sharedStash: %r" % o["shard"])
        self.assertIsNone(o["findShard"], o["findShard"])
        self.assertEqual(o["filed"], [{"copyIx": 0, "kind": "filed", "mule": "mule1"}],
                         "a real mule filing was reclassified: %r" % o["filed"])
        self.assertEqual(o["findFiled"], "mule1", o["findFiled"])
        self.assertEqual(o["carried"], [{"copyIx": 0, "kind": "carried", "mule": None}],
                         "carried must still win over the locker: %r" % o["carried"])
        self.assertEqual(o["liveOverflow"], ["Enigma"], o["liveOverflow"])
        self.assertEqual(o["recOverflow"], ["Enigma"], o["recOverflow"])
        self.assertEqual(o["memOverflow"], ["Enigma"],
                         "the in-memory overflow view left _sharedNames: %r" % o["memOverflow"])
        self.assertEqual(o["loadedOverflow"], ["Enigma"],
                         "the loaded store's overflow view left _sharedNames: %r" % o["loadedOverflow"])


RED_PROOF = [
    {
        "why": "REG-2272 item 6 — a name in the shared locker (assign === shared) that the never-muled "
               "regex misses must be sharedStash. Dropping that branch lets muleById('shared') file Enigma "
               "as a mule, FIND returns shared, and the 3rd copy never becomes dupes.",
        "file": "bible.html",
        "find": "        else if (sharedSet[name]) kind = 'sharedStash';\n",
        "replace": "        else if (false && sharedSet[name]) kind = 'sharedStash';\n",
        "matches": 1,
    },
    {
        "why": "REG-2272 item 6 — overflow membership is production _sharedNames, not kind === sharedStash. "
               "A kind walk calls an unassigned 4-copy Worldstone Shard trade-stock. The live overflow does not.",
        "file": "bible.html",
        "find": "      (_sharedNames() || []).forEach(function(n){\n        var ids = model.index[n] || [];\n",
        "replace": "      (function(){ var s=[]; (model.records||[]).forEach(function(r){ if(r && r.kind==='sharedStash' && s.indexOf(r.name)<0) s.push(r.name); }); return s; })().forEach(function(n){\n        var ids = model.index[n] || [];\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
