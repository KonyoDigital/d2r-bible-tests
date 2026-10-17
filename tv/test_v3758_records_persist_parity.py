# -*- coding: utf-8 -*-
"""#76 INC-3b (v-foundation, DORMANT) — THE PERSISTED d2r_vaultRecords STORE IS AT PARITY WITH THE IN-MEMORY MODEL.

The design doc PHASE-2 foundation. INC-1/INC-2 derive the one-record model on demand from the already-forked
name-homed stores (owned/copies/assign). This law proves that _vaultRecordsPersist() writes a d2r_vaultRecords store
whose records, re-derived into the header / find / overflow views, EQUAL the live in-memory _vaultRecords()-derived
views — so PHASE 2 (gated, his confirm) can flip the live views to read the store with NO behaviour change.

It extracts the SHIPPED functions out of bible.html and runs them in node on a seeded fixture, with an in-memory
fake window.LSR (NEVER his real disk):

  · the migration writes BOTH keys (store + stamp), is version-gated (a 2nd run is `already`), and is UNKNOWN-safe
    (an unreadable stamp persists NOTHING);
  · persisted header / find / overflow EQUAL the in-memory _vaultRecordsHeader / _vaultRecordsFind /
    _vaultRecordsOverflow AND the live _vaultSharedOverflowNames — including the SHARED-NAME-AT-CAP boundary (F has
    exactly _SHARED_COPY_CAP copies, so a `>= cap` bug would wrongly flag it as overflow);
  · each persisted record carries a STABLE OPAQUE recId (rec_<n>, not name+'#'+i) that SURVIVES a rename;
  · each record carries its OWN per-copy loc (rule E: a shared name's 3rd+ copy -> 'dupes');
  · a CORRUPT/unreadable d2r_vaultRecords is NEVER overwritten (the _muleUnread/_guardedSet guard);
  · the undo clears d2r_vaultRecords + the stamp and leaves owned/copies/assign UNTOUCHED;
  · DORMANCY: the migration/persist have NO caller in bible.html's live flow — only this law calls them.

NOT vacuous: the persisted views are derived from the stored records, so a parity miss means the PERSIST drifted
from the model it snapshots — exactly what must hold before phase 2 swaps the source. A missing node raises — this
law does not skip. RED_PROOF below. [[the-unjoined-end]] [[unknown-stays-unknown]] [[heart-first]] [[regression-guard]]
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

# the shipped functions under test + the live overflow chain they are proven against
EXTRACT = [
    "_sharedNames", "_sharedCopyCount", "_sharedCappedCopies", "_vaultSharedOverflowCells",
    "_vaultSharedOverflowNames", "_vaultRecords", "_vaultRecordsFind", "_vaultRecordsOverflow",
    "_vaultRecordsHeader",
    # INC-3b: persist / load / migrate / undo / rename + the model-in parity views
    "_vrRecLoadRaw", "_vrRecGuardedSet", "_vrLocForCopy", "_vaultRecordsLoad", "_vaultRecordsPersist",
    "_vaultRecordsMigrate", "_vaultRecordsMigrateUndo", "_vaultRecordsRename",
    "_vaultRecordsViewFind", "_vaultRecordsViewOverflow", "_vaultRecordsViewHeader",
]

# ── the fixture: A filed to mule1; B shared(1); C shared(4 -> overflow 2); E shared(3 -> overflow 1);
#    F shared(2 == cap, the BOUNDARY -> NO overflow, so a `>= cap` bug would wrongly fill dupes); D loose ──
PREAMBLE = r"""
var window = globalThis;
window.D2R_PROFILE = 'main';
// keep stdout clean for the result JSON — the shipped code's console.info/.log/.warn go to stderr here
console.info = function(){ try { process.stderr.write('[info] ' + Array.prototype.join.call(arguments, ' ') + '\n'); } catch(e){} };
console.log  = console.info;
console.warn = function(){ try { process.stderr.write('[warn] ' + Array.prototype.join.call(arguments, ' ') + '\n'); } catch(e){} };
// ── in-memory fake localStorage (NEVER his real disk) ──
var _LSRDATA = {};
window.LSR = {
  getItem: function(k){ return Object.prototype.hasOwnProperty.call(_LSRDATA, k) ? _LSRDATA[k] : null; },
  setItem: function(k, v){ _LSRDATA[k] = String(v); },
  removeItem: function(k){ delete _LSRDATA[k]; }
};
// ── the INC-3b module-level vars that _fn does not extract (they are `var`, not `function`) ──
var _VR_STORE_KEY = 'd2r_vaultRecords';
var _VRM_KEY = 'd2r_vaultRecordsMigrate';
var _VRM_VER = 1;
var _vrRecUnread = {};
// ── fixture stores + deps (kept consistent with the fixture) ──
var assign = { A:'mule1', B:'shared', C:'shared', E:'shared', F:'shared' };   // D unassigned -> loose
var copies = { C:4, E:3, F:2 };                                    // A,B default 1
var OWNED  = ['A','B','C','D','E','F'];
var _SHARED_COPY_CAP = 2, _MULE_COPY_CAP = 3;
function ownedPool(){ return OWNED.slice(); }
function copyCount(n){ var c = copies[n]; return (c && c > 0) ? c : (OWNED.indexOf(n) >= 0 ? 1 : 0); }
function isSharedStash(n){ return assign[n] === 'shared'; }         // fixture: shared-assigned == shared-stash
function muleById(id){ return (id === 'mule1') ? { id:'mule1', name:'Mule One' } : null; }
function _dockNames(){ return ['D']; }                             // D is loose
window._carriedNames = function(){ return []; };                   // nothing carried
var KEEP_IN_INVENTORY = /Annihilus|Hellfire Torch|Gheed/;
function _keepName(n){ return n; }
"""


def _fn(src, name):
    """Extract `function NAME(...){ ...balanced... }` by brace-balancing from the first match."""
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


class TestV3758RecordsPersistParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not NODE:
            raise AssertionError("node is not on this machine — this law does not skip")
        with open(BIBLE, encoding="utf-8") as f:
            cls.src = f.read()
        cls.fns = "\n".join(_fn(cls.src, n) for n in EXTRACT)

    def _run(self, scenario):
        prog = PREAMBLE + self.fns + "\nvar out = {};\n" + scenario + "\nprocess.stdout.write(JSON.stringify(out));\n"
        p = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, (p.stderr or p.stdout)[-2000:])
        return json.loads(p.stdout)

    # ───────────────────────────────────────────────────────────────────────────────────────────
    def test_persisted_views_equal_the_in_memory_model_at_parity(self):
        o = self._run(r"""
var mem = _vaultRecords();
var m = _vaultRecordsMigrate();
var m2 = _vaultRecordsMigrate();          // version gate: a 2nd run is `already`, nothing re-persisted
var loaded = _vaultRecordsLoad();
var names = ['A','B','C','D','E','F','ZZ'];
out.migrate = m;
out.migrate2already = !!(m2 && m2.already && m2.ran === false);
out.storeWritten = (window.LSR.getItem('d2r_vaultRecords') != null);
out.stampWritten = (window.LSR.getItem('d2r_vaultRecordsMigrate') != null);
out.loadedIdxLen = (function(){ var q={}; ['A','B','C','D','E','F'].forEach(function(n){ q[n]=(loaded.index[n]||[]).length; }); return q; })();
// view helpers pinned to the SHIPPED in-memory functions (so the helpers cannot drift)
out.memViewHeader = _vaultRecordsViewHeader(mem);
out.shippedHeader = _vaultRecordsHeader();
out.memViewOverflow = _vaultRecordsViewOverflow(mem);
out.shippedOverflow = _vaultRecordsOverflow();
out.liveOverflow = _vaultSharedOverflowNames();
out.memFind = {}; out.shippedFind = {};
names.forEach(function(n){ out.memFind[n] = _vaultRecordsViewFind(mem, n); out.shippedFind[n] = _vaultRecordsFind(n); });
// PERSISTED parity: the SAME views derived from the LOADED store
out.loadedViewHeader = _vaultRecordsViewHeader(loaded);
out.loadedViewOverflow = _vaultRecordsViewOverflow(loaded);
out.loadedFind = {};
names.forEach(function(n){ out.loadedFind[n] = _vaultRecordsViewFind(loaded, n); });
""")
        # the migration wrote both keys, derived a faithful model, and is version-gated
        self.assertTrue(o["migrate"]["ran"], "the migration did not run: %r" % o["migrate"])
        self.assertTrue(o["migrate"]["stamped"], "the migration did not stamp: %r" % o["migrate"])
        self.assertTrue(o["storeWritten"], "d2r_vaultRecords was not written")
        self.assertTrue(o["stampWritten"], "the migrate stamp was not written")
        self.assertTrue(o["migrate2already"], "a 2nd migrate was not version-gated to `already`: %r" % o)
        # FIDELITY: the persisted index carries copyCount(name) records per name
        self.assertEqual(o["loadedIdxLen"], {"A": 1, "B": 1, "C": 4, "D": 1, "E": 3, "F": 2},
                         "persisted index miscounts copies: %r" % o["loadedIdxLen"])
        # the view helpers equal the SHIPPED functions on the in-memory model (no drift)
        self.assertEqual(o["memViewHeader"], o["shippedHeader"], "view header drifted from _vaultRecordsHeader")
        self.assertEqual(o["memViewOverflow"], o["shippedOverflow"], "view overflow drifted from _vaultRecordsOverflow")
        self.assertEqual(o["memFind"], o["shippedFind"], "view find drifted from _vaultRecordsFind")
        # PERSISTED == IN-MEMORY: header, find, overflow
        self.assertEqual(o["loadedViewHeader"], o["shippedHeader"],
                         "persisted header != in-memory header: %r vs %r" % (o["loadedViewHeader"], o["shippedHeader"]))
        self.assertEqual(o["loadedFind"], o["shippedFind"],
                         "persisted find != in-memory find: %r vs %r" % (o["loadedFind"], o["shippedFind"]))
        self.assertEqual(o["loadedViewOverflow"], o["shippedOverflow"],
                         "persisted overflow != in-memory overflow: %r vs %r" % (o["loadedViewOverflow"], o["shippedOverflow"]))
        # the BOUNDARY: F has exactly _SHARED_COPY_CAP copies -> NOT overflow; C, E are
        self.assertEqual(o["loadedViewOverflow"], ["C", "E"],
                         "overflow boundary wrong (F at cap must be excluded): %r" % o["loadedViewOverflow"])
        self.assertEqual(o["loadedViewOverflow"], o["liveOverflow"],
                         "persisted overflow != live _vaultSharedOverflowNames: %r vs %r" % (o["loadedViewOverflow"], o["liveOverflow"]))
        # a filed name resolves to its mule via the persisted store; non-filed / unknown invent no home
        self.assertEqual(o["loadedFind"]["A"], "mule1", "a filed name did not resolve to its mule via the store")
        self.assertIsNone(o["loadedFind"]["B"], "a SHARED name was given a mule home")
        self.assertIsNone(o["loadedFind"]["D"], "a LOOSE name was given a mule home")
        self.assertIsNone(o["loadedFind"]["ZZ"], "an unknown name was given a home")

    def test_recId_is_opaque_and_survives_a_rename(self):
        o = self._run(r"""
_vaultRecordsMigrate();
var loaded = _vaultRecordsLoad();
out.allIds = loaded.records.map(function(r){ return r.recId; });
out.idShapeOk = loaded.records.every(function(r){ return /^rec_\d+$/.test(r.recId); });
out.idNotNameDerived = loaded.records.every(function(r){ return r.recId !== (r.name + '#' + r.copyIx); });
// per-copy loc (rule E): C -> [shared,shared,dupes,dupes]; F -> [shared,shared] (boundary, NO dupes)
out.locByName = (function(){ var q={}; loaded.records.forEach(function(r){ (q[r.name]=q[r.name]||[]).push(r.loc); }); return q; })();
// rename A -> A2: the record's name field changes, the recId does NOT
out.aIdsBefore = (loaded.index['A'] || []).slice();
out.rename = _vaultRecordsRename('A', 'A2');
var loaded2 = _vaultRecordsLoad();
out.a2IdsAfter = (loaded2.index['A2'] || []).slice();
out.aGoneAfter = (loaded2.index['A'] || []).length;
out.a2IdNotNameDerived = (out.a2IdsAfter.length === 1 && out.a2IdsAfter[0] !== 'A2#0');
""")
        self.assertTrue(o["idShapeOk"], "a recId is not an opaque rec_<n> token: %r" % o["allIds"])
        self.assertTrue(o["idNotNameDerived"], "a recId is name+'#'+i derived: %r" % o["allIds"])
        # rule E per-copy location is persisted (phase-2 routing data), boundary respected
        self.assertEqual(o["locByName"]["C"], ["shared", "shared", "dupes", "dupes"],
                         "rule-E per-copy loc wrong for C: %r" % o["locByName"].get("C"))
        self.assertEqual(o["locByName"]["F"], ["shared", "shared"],
                         "F at cap must be two shared copies, no dupes: %r" % o["locByName"].get("F"))
        self.assertEqual(o["locByName"]["A"], ["mule1"], "a filed copy's loc must be its mule: %r" % o["locByName"].get("A"))
        self.assertEqual(o["locByName"]["D"], ["loose"], "a loose copy's loc must be loose: %r" % o["locByName"].get("D"))
        # the id SURVIVED the rename, unchanged, and is not the new name's positional id
        self.assertEqual(o["rename"]["moved"], 1, "the rename moved the wrong number of records: %r" % o["rename"])
        self.assertEqual(o["aIdsBefore"], o["a2IdsAfter"],
                         "the recId changed across a rename (it must be opaque): %r -> %r" % (o["aIdsBefore"], o["a2IdsAfter"]))
        self.assertEqual(o["aGoneAfter"], 0, "the old name still indexes records after the rename")
        self.assertTrue(o["a2IdNotNameDerived"], "the renamed record's id is name-derived: %r" % o["a2IdsAfter"])

    def test_rename_then_persist_reuses_the_recId(self):
        """REG-2272 item 1. Rename alone keeps the id. The next persist used to look the id up under the
        renamed spelling, miss the live name, re-mint, and overwrite the store."""
        o = self._run(r"""
_vaultRecordsMigrate();
var before = (_vaultRecordsLoad().index['A'] || []).slice();
out.rename = _vaultRecordsRename('A', 'A2');
var again = _vaultRecordsPersist();
var loaded = _vaultRecordsLoad();
out.ok = !!again.ok;
out.aIds = (loaded.index['A'] || []).slice();
out.a2Ids = (loaded.index['A2'] || []).slice();
out.same = (out.aIds.length === 1 && out.aIds[0] === before[0]);
""")
        self.assertTrue(o["ok"], "the persist after a rename refused: %r" % o)
        self.assertEqual(o["rename"]["moved"], 1, o["rename"])
        self.assertEqual(o["a2Ids"], [], "the live name is still A, so the snapshot must not keep the renamed spelling: %r" % o)
        self.assertTrue(o["same"], "rename-then-persist re-minted the id: %r" % o)

    def test_a_wrong_shape_store_is_unknown_and_not_overwritten(self):
        """REG-2272 item 2. Parse-OK but not {records: array} is UNKNOWN, not absent."""
        o = self._run(r"""
window.LSR.setItem('d2r_vaultRecords', JSON.stringify({ v: 1 }));
var before = window.LSR.getItem('d2r_vaultRecords');
var pr = _vaultRecordsPersist();
var m = _vaultRecordsMigrate();
out.unknown = !!pr.unknown;
out.ok = pr.ok;
out.unchanged = (window.LSR.getItem('d2r_vaultRecords') === before);
out.stamped = (window.LSR.getItem('d2r_vaultRecordsMigrate') != null);
out.migrateRan = m.ran;
""")
        self.assertTrue(o["unknown"], "a wrong-shape store was not UNKNOWN: %r" % o)
        self.assertFalse(o["ok"], "persist wrote over a wrong-shape store")
        self.assertTrue(o["unchanged"], "the wrong-shape bytes were overwritten")
        self.assertFalse(o["stamped"], "the migrate stamp latched over a wrong-shape store")
        self.assertFalse(o["migrateRan"], "the migration ran over a wrong-shape store")

    def test_an_unreadable_witness_store_is_not_a_null_witness(self):
        """REG-2272 item 3. Absent prov is null. Unreadable prov is a marker, not null."""
        o = self._run(r"""
window.LSR.setItem('d2r_vaultProv', '{bad');
var pr = _vaultRecordsPersist();
var loaded = _vaultRecordsLoad();
out.ok = !!pr.ok;
out.marked = loaded.records.every(function(r){ return r.provUnknown === true && !('prov' in r); });
out.n = loaded.records.length;
""")
        self.assertTrue(o["ok"], "persist refused a readable records store: %r" % o)
        self.assertGreater(o["n"], 0)
        self.assertTrue(o["marked"], "an unreadable witness store was stored as a null witness: %r" % o)

    def test_an_undo_that_throws_does_not_say_it_rearmed(self):
        """REG-2272 item 5. undone:true while removeItem threw left the stamp gating."""
        o = self._run(r"""
_vaultRecordsMigrate();
window.LSR.removeItem = function(){ throw new Error('disk'); };
var undo = _vaultRecordsMigrateUndo();
out.undone = undo.undone;
out.why = undo.why || '';
out.storeStill = (window.LSR.getItem('d2r_vaultRecords') != null);
out.stampStill = (window.LSR.getItem('d2r_vaultRecordsMigrate') != null);
""")
        self.assertFalse(o["undone"], "undo reported re-armed after a throw: %r" % o)
        self.assertIn("threw", o["why"], o["why"])
        self.assertTrue(o["storeStill"], "a thrown remove still cleared the store")
        self.assertTrue(o["stampStill"], "a thrown remove still cleared the stamp")

    def test_a_corrupt_store_is_never_overwritten(self):
        o = self._run(r"""
window.LSR.setItem('d2r_vaultRecords', '{this is : not valid json');   // corrupt bytes
var before = window.LSR.getItem('d2r_vaultRecords');
var pr = _vaultRecordsPersist();                 // marks the key UNREAD, refuses to write
var guardedSetRefused = (_vrRecGuardedSet({ v:1, records:[] }) === false);
var m = _vaultRecordsMigrate();                  // the migration refuses on the same UNKNOWN store
out.persistOk = pr.ok;
out.persistUnknown = !!pr.unknown;
out.guardedSetRefused = guardedSetRefused;
out.migrateRan = m.ran;
out.storeUnchanged = (window.LSR.getItem('d2r_vaultRecords') === before);
out.stampWritten = (window.LSR.getItem('d2r_vaultRecordsMigrate') != null);
""")
        self.assertFalse(o["persistOk"], "persist claimed success over a corrupt store")
        self.assertTrue(o["persistUnknown"], "a corrupt store was not reported UNKNOWN")
        self.assertTrue(o["guardedSetRefused"], "_vrRecGuardedSet overwrote a corrupt store")
        self.assertTrue(o["storeUnchanged"], "the corrupt d2r_vaultRecords bytes were overwritten — DATA LOSS")
        self.assertFalse(o["migrateRan"], "the migration ran over a corrupt store")
        self.assertFalse(o["stampWritten"], "the migration stamped over a corrupt store")

    def test_an_unreadable_stamp_persists_nothing(self):
        o = self._run(r"""
window.LSR.setItem('d2r_vaultRecordsMigrate', '{bad stamp');   // the stamp will not parse -> UNKNOWN
var m = _vaultRecordsMigrate();
out.ran = m.ran;
out.why = m.why || '';
out.storeWritten = (window.LSR.getItem('d2r_vaultRecords') != null);
""")
        self.assertFalse(o["ran"], "the migration acted on an unreadable stamp")
        self.assertIn("UNKNOWN", o["why"], "the refusal did not name UNKNOWN: %r" % o["why"])
        self.assertFalse(o["storeWritten"], "an unreadable stamp still let the store be written")

    def test_the_undo_clears_both_keys_and_leaves_the_source_stores_untouched(self):
        o = self._run(r"""
var assignBefore = JSON.stringify(assign), copiesBefore = JSON.stringify(copies), ownedBefore = OWNED.join(',');
_vaultRecordsMigrate();
// the migration must NEVER write the source stores
out.wroteOwned  = (window.LSR.getItem('d2r_owned') != null);
out.wroteCopies = (window.LSR.getItem('d2r_copies') != null);
out.wroteAssign = (window.LSR.getItem('d2r_muleAssign') != null);
var undo = _vaultRecordsMigrateUndo();
out.undo = undo;
out.storeAfter = (window.LSR.getItem('d2r_vaultRecords') != null);
out.stampAfter = (window.LSR.getItem('d2r_vaultRecordsMigrate') != null);
out.assignUnchanged = (JSON.stringify(assign) === assignBefore);
out.copiesUnchanged = (JSON.stringify(copies) === copiesBefore);
out.ownedUnchanged  = (OWNED.join(',') === ownedBefore);
// after the undo the migration RE-ARMS (a clean re-run persists again)
var again = _vaultRecordsMigrate();
out.reArmed = !!(again && again.ran && again.stamped);
""")
        self.assertFalse(o["wroteOwned"], "the migration wrote d2r_owned")
        self.assertFalse(o["wroteCopies"], "the migration wrote d2r_copies")
        self.assertFalse(o["wroteAssign"], "the migration wrote d2r_muleAssign")
        self.assertTrue(o["undo"]["clearedStore"], "the undo did not clear the store")
        self.assertTrue(o["undo"]["clearedStamp"], "the undo did not clear the stamp")
        self.assertFalse(o["storeAfter"], "d2r_vaultRecords survived the undo")
        self.assertFalse(o["stampAfter"], "the migrate stamp survived the undo")
        self.assertTrue(o["assignUnchanged"], "the undo altered assign")
        self.assertTrue(o["copiesUnchanged"], "the undo altered copies")
        self.assertTrue(o["ownedUnchanged"], "the undo altered owned")
        self.assertTrue(o["reArmed"], "the migration did not re-arm after the undo")

    def test_the_migration_is_dormant_no_live_caller(self):
        """DORMANCY (task step 4): nothing in bible.html's live flow calls the migration/persist — only this law.
        Proven by counting call sites with /* */ comments stripped (bounded form, source-reading-guard): the
        migration appears ONCE (its definition, no caller) and persist TWICE (its definition + the migration's
        single call). The window-exports `= _vaultRecordsMigrate;` carry no '(' and do not count as calls."""
        code = re.sub(r"/\*.{0,4000}?\*/", "", self.src, flags=re.S)
        self.assertEqual(code.count("_vaultRecordsMigrate("), 1,
                         "the migration has a caller in bible.html — it must stay DORMANT (phase-2 arms it)")
        self.assertEqual(code.count("_vaultRecordsPersist("), 2,
                         "_vaultRecordsPersist has a caller other than the migration — it must stay DORMANT")


# ── RED_PROOF: each tamper matches EXACTLY ONCE and turns THIS law RED; heart2 reverts byte-identical. ──
RED_PROOF = [
    {
        "why": "#76 INC-3b - the records-overflow view must EXCLUDE a shared name AT the cap (F, 2 copies). A `>= cap` "
               "bug fills GRAIL-DUPES with every shared name at or over the cap and breaks parity with the live "
               "trade-stock view and the in-memory overflow (F and B would wrongly appear).",
        "file": "bible.html",
        "find": "if (ids.length - cap > 0) out.push(n);",
        "replace": "if (ids.length - cap >= 0) out.push(n);",
        "matches": 1,
    },
    {
        "why": "#76 INC-3b - a persisted record must carry its name's assign-derived mule home, or _vaultRecordsFind "
               "re-derived from the store stops resolving a filed name to its mule (findA would go null) and the "
               "persisted FIND view drifts from the in-memory one.",
        "file": "bible.html",
        "find": "kind: r.kind, mule: r.mule,",
        "replace": "kind: r.kind, mule: null,",
        "matches": 1,
    },
    {
        "why": "#76 INC-3b - the recId must be a STABLE OPAQUE token, never name+'#'+i. A name-derived id re-mints on "
               "every rename/copy-count change (the defect recIdStability describes); the opaque-id + rename-stability "
               "assertions catch it.",
        "file": "bible.html",
        "find": "if (!recId) { seq += 1; recId = 'rec_' + seq; }",
        "replace": "if (!recId) { seq += 1; recId = r.name + '#' + r.copyIx; }",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
