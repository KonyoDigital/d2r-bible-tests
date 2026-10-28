# -*- coding: utf-8 -*-
"""v3767 — one cell is one record, a frame does not register while AUTO INTAKE is off.

Elad, 2026-10-18. A sighting is holder + location + cell. The same cell across reels is
one record and its sessions are the witnesses. A second cell is a second copy on the
same mule. Natalya, Tal Rasha's Guardianship and Immortal King's Soul Cage do not become
four and three records because a reel was read again.

15:20 IDT — the move is a record: from, to, status (to-move, moved-manual, verified,
moved-elsewhere) and the evidence frame ids. The list that paints it is the next version.

15:24 IDT — AUTO INTAKE is on or off, per world. Off, a frame does not register. The
existing + Add an item still places through the records seam, and the record says manual.

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

FNS = [
    "_vaultCellKey", "_vaultSightGroups", "_vaultRereadKind",
    "_vaultAutoIntakeRead", "_vaultAutoIntakePaint", "_vaultAutoIntakeSet",
    "_vaultAutoIntakeToggle", "_vaultFrameRefuse", "_vaultIntakeGate",
    "_vaultMovePlace", "_vaultMoveSamePlace", "_vaultMoveTask", "_vaultMoveQueue",
    "_vaultMoveTally", "_vaultMoveWitness", "_vaultPresenceSpan",
    "_vaultSeamHome", "_dockNames", "_vaultRecords",
]


def _fn(src, name):
    m = re.search(r"\bfunction %s\s*\(" % re.escape(name), src)
    if not m:
        raise AssertionError("could not find function %s" % name)
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
    raise AssertionError("unbalanced %s" % name)


def _assigned(src, pattern):
    m = re.search(pattern, src)
    if not m:
        raise AssertionError("could not find %s" % pattern)
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
    raise AssertionError("unbalanced %s" % pattern)


def _slice_fn(src, start, fn_anchor):
    i = src.index(start)
    m = src.index(fn_anchor, i)
    brace = src.index("{", m)
    depth, j = 0, brace
    while j < len(src):
        c = src[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[i:j + 1]
        j += 1
    raise AssertionError("unbalanced slice %s" % fn_anchor)


PREAMBLE = r"""
var window = globalThis;
var owned = new Set();
var assign = {};
var copies = {};
var multiKeep = {};
var PROV = {};
var magicFinds = {};
var ROUTES = {};
var SETS = {
  "Natalya's Totem": 1, "Tal Rasha's Guardianship": 1,
  "Immortal King's Soul Cage": 1, "Natalya's Soul": 1
};
var VAULT_AUTO_INTAKE_KEY = 'd2r_vaultAutoIntake';
var _ls = {};
window.LSR = {
  getItem: function(k){ return Object.prototype.hasOwnProperty.call(_ls, k) ? _ls[k] : null; },
  setItem: function(k, v){ _ls[k] = String(v); },
  removeItem: function(k){ delete _ls[k]; }
};
function ownedPool(){ return Array.from(owned).sort(); }
function copyCount(n){ return (copies[n] > 0) ? copies[n] : 1; }
function isSharedStash(){ return false; }
function _sharedNames(){ return []; }
function _inMagicRare(){ return false; }
function muleById(id){
  var known = { shared: 'SHARED', 'uni-weap': 'UNI-WEAPONS', 'uni-armor': 'UNI-ARMOR', 'uni-small': 'UNI-JEWELRY', runewords: 'RUNEWORDS' };
  return known[id] ? { id: id, name: known[id] } : null;
}
function suggestMule(name){
  if (Object.prototype.hasOwnProperty.call(ROUTES, name)) return ROUTES[name];
  return { id: null, unsorted: true, why: 'unknown' };
}
window._vfIsSetPiece = function(n){ return SETS[n] === 1; };
window._carriedNames = function(){ return []; };
window._furnitureLocked = function(){ return false; };
window._mainLockOf = function(){ return null; };
window._vaultLastSeenOnMain = function(){ return null; };
function _provAll(){ return PROV; }
function _isChronicleOnlyRow(){ return false; }
function _inner(){
  var nm = arguments[0];
  if (nm) owned.add(String(nm));
  return { ok: true, mode: 'new', name: nm };
}
function reset(){
  owned.clear();
  [assign, copies, multiKeep, PROV, ROUTES, _ls].forEach(function(o){
    Object.keys(o).forEach(function(k){ delete o[k]; });
  });
}
function L(holder, loc, cell, session, frame){
  return { holder: holder, loc: loc, cell: cell, id: session || null, frame: frame || null };
}
function see(name, looks, nCopies){
  owned.add(name);
  if (nCopies) copies[name] = nCopies;
  if (looks) PROV[name] = { looks: looks };
}
function rows(name){
  return _vaultRecords().records.filter(function(r){ return r.name === name; });
}
"""

TAIL = r"""
window._vaultFrameRefuse = _vaultFrameRefuse;
window._vaultIntakeGate = _vaultIntakeGate;
window._vaultAutoIntakePaint = _vaultAutoIntakePaint;
"""


def look_rule(src):
    """#201 (v3813) - THE ONE RULE FOR A LOOK THAT COUNTS, cut from bible.html with its floor. _vaultSightGroups,
    _vaultSightLooks and the register wrapper ask it through window.*, so a harness that cuts any of them carries it."""
    m = re.search(r"\n  var VAULT_WITNESS_FLOOR = [^;]+;", src)
    if not m:
        raise AssertionError("VAULT_WITNESS_FLOOR is gone from bible.html")
    return "\n".join([m.group(0).strip()] + [_fn(src, n) for n in ("_vaultLookConf", "_vaultLooksScored", "_vaultLookCounts")]
                     + ["globalThis._vaultLooksScored = _vaultLooksScored; globalThis._vaultLookCounts = _vaultLookCounts;"])


def witness_bundle(src):
    """The pure law, cut from bible.html. No browser."""
    lane = _slice_fn(src, "var _LANE_LOCK_KEY = 'd2r_laneLock';", "window._laneLockWhy = function(name){")
    looks = _assigned(src, r"window\._vaultEvidenceLooks\s*=\s*function\s*\(")
    doors = "\n".join(_assigned(src, p) for p in (
        r"window\.tvVaultRegister = function\(name\)\{",
        r"window\.vaultIntake = async function\(files, opts\)\{",
        r"window\.tvVaultAutoIntake = async function\(opts\)\{",
    ))
    return "\n".join([lane, looks, look_rule(src)] + [_fn(src, n) for n in FNS] + [doors, TAIL])


class TestV3767CopyWitness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not NODE:
            raise AssertionError("node is not on this machine — this law does not skip")
        with open(BIBLE, encoding="utf-8") as f:
            cls.src = f.read()
        cls.bundle = witness_bundle(cls.src)

    def _run(self, body):
        prog = PREAMBLE + "\n" + self.bundle + "\n" + body
        raw = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        self.assertEqual(raw.returncode, 0, (raw.stderr or "")[-2000:] + (raw.stdout or "")[-500:])
        line = [ln for ln in raw.stdout.splitlines() if ln.startswith("{") or ln.startswith("[")][-1]
        return json.loads(line)

    def test_same_cell_is_one_record_and_a_second_cell_is_another_copy(self):
        o = self._run(r"""
reset();
see("Natalya's Totem", null, 4);
see("Tal Rasha's Guardianship", null, 4);
see("Immortal King's Soul Cage", null, 3);
see("Natalya's Soul", [L('Mule','stash','stash:c1r1','s1','a'), L('Mule','stash','stash:c4r4','s1','b')], 4);
see("Harlequin Crest", [L('Mule','stash','stash:c3r3','s1','a'), L('Mule','stash','stash:c3r3','s2','b'), L('Mule','stash','stash:c3r3','s3','c')], 4);
see("Griffon's Eye", [L('Mule','stash','stash:c1r1','s1','a'), L('Mule','stash','stash:c2r2','s2','b')], 1);
ROUTES["Griffon's Eye"] = { id: 'uni-armor', why: 'helm' };
ROUTES["Natalya's Soul"] = { id: 'uni-armor', why: 'armor' };
see("Enigma", [L('Mule','stash','stash:c5r5','e1','a'), L('Mule','stash','stash:c5r5','e2','b'), L('Mule','stash','stash:c5r5','e3','c')], 1);
see("Grief", [L('Mule','stash','stash:c1r2','g1','a'), L('Mule','stash','stash:c8r2','g1','b')], 1);
ROUTES["Grief"] = { id: 'uni-weap', why: 'weapon' };
see("Annihilus", [L('MAIN','inventory','inventory:c1r1','c1','a'), L('MAIN','inventory','inventory:c1r1','c2','b'), L('MAIN','inventory','inventory:c1r1','c3','c')], 1);
see("Hellfire Torch", [L('MAIN','inventory','inventory:c2r1','h1','a'), L('MAIN','inventory','inventory:c3r1','h1','b')], 1);
see("Archon Plate", [L('Mule','stash','stash:c6r6','b1','a'), L('Mule','stash','stash:c6r6','b1','b')], 3);
see("Colossus Blade", [L('Mule','stash','stash:c1r8','d1','a'), L('Mule','stash','stash:c2r8','d1','b')], 1);
ROUTES["Colossus Blade"] = { id: 'uni-weap', why: 'blade' };
see("Magefist", [L('MAIN','equipment','equipped:gloves','m1','a'), L('Mule','stash','equipped:gloves','m2','b')], 1);
see("Shako Bare", null, 4);
see("One Session Three Frames", [L('Mule','stash','stash:c9r9','only','f1'), L('Mule','stash','stash:c9r9','only','f2'), L('Mule','stash','stash:c9r9','only','f3')], 1);
see("No Session", [L('Mule','stash','stash:c9r8', null, null)], 1);
multiKeep["Archon Plate"] = 2;
var arch = rows("Archon Plate");
var grief = rows("Grief");
var soul = rows("Natalya's Soul");
var mage = rows("Magefist");
console.log(JSON.stringify({
  natalya: rows("Natalya's Totem").length,
  tal: rows("Tal Rasha's Guardianship").length,
  ik: rows("Immortal King's Soul Cage").length,
  soul: soul.length, soulMule: soul.map(function(r){ return r.mule; }),
  shako: rows("Harlequin Crest").length,
  shakoW: rows("Harlequin Crest")[0].sight.witnesses,
  griff: rows("Griffon's Eye").length,
  griffMule: rows("Griffon's Eye").map(function(r){ return r.mule; }),
  enigma: rows("Enigma").length, enigmaW: rows("Enigma")[0].sight.witnesses,
  grief: grief.length, griefMule: grief.map(function(r){ return r.mule; }),
  anni: rows("Annihilus").length, anniW: rows("Annihilus")[0].sight.witnesses,
  torch: rows("Hellfire Torch").length,
  arch: arch.length,
  blade: rows("Colossus Blade").length,
  bladeMule: rows("Colossus Blade").map(function(r){ return r.mule; }),
  mage: mage.length,
  mageHolders: mage.map(function(r){ return r.sight.holder; }).sort(),
  bare: rows("Shako Bare").length,
  frames: rows("One Session Three Frames")[0].sight.witnesses,
  nosess: rows("No Session")[0].sight.witnesses
}));
""")
        self.assertEqual(o["natalya"], 1)
        self.assertEqual(o["tal"], 1)
        self.assertEqual(o["ik"], 1)
        self.assertEqual(o["soul"], 2)
        self.assertEqual(o["soulMule"], ["uni-armor", "uni-armor"])
        self.assertEqual(o["shako"], 1)
        self.assertEqual(o["shakoW"], 3)
        self.assertEqual(o["griff"], 2)
        self.assertEqual(o["griffMule"], ["uni-armor", "uni-armor"])
        self.assertEqual(o["enigma"], 1)
        self.assertEqual(o["enigmaW"], 3)
        self.assertEqual(o["grief"], 2)
        self.assertEqual(o["griefMule"], ["uni-weap", "uni-weap"])
        self.assertEqual(o["anni"], 1)
        self.assertEqual(o["anniW"], 3)
        self.assertEqual(o["torch"], 2)
        self.assertEqual(o["arch"], 2, "a multi-keep above the cells is a spare he asked for")
        self.assertEqual(o["blade"], 2)
        self.assertEqual(o["bladeMule"], ["uni-weap", "uni-weap"])
        self.assertEqual(o["mage"], 2)
        self.assertEqual(o["mageHolders"], ["MAIN", "Mule"])
        self.assertEqual(o["bare"], 4, "no cell on a unique is not a measured one")
        self.assertEqual(o["frames"], 1, "three frames of one session are one witness")
        self.assertIsNone(o["nosess"], "a look with no session does not invent one")

    def test_two_sessions_watch_and_the_third_locks(self):
        o = self._run(r"""
reset();
owned.add("Eschuta's Temper");
ROUTES["Eschuta's Temper"] = { id: 'shared', why: 'war' };
window._laneLockNote("Eschuta's Temper", 'equipment', 's1');
window._laneLockNote("Eschuta's Temper", 'equipment', 's2');
var mid = rows("Eschuta's Temper")[0];
var nMid = window._laneLockSessions("Eschuta's Temper");
var whyMid = window._laneLockWhy("Eschuta's Temper");
window._laneLockNote("Eschuta's Temper", 'equipment', 's3');
var end = rows("Eschuta's Temper")[0];
console.log(JSON.stringify({
  watch: !!mid.watching, lockedMid: !!mid.locked, nMid: nMid, whyMid: whyMid,
  watchEnd: !!end.watching, locked: !!end.locked, kind: end.kind,
  dock: _dockNames().indexOf("Eschuta's Temper")
}));
""")
        self.assertTrue(o["watch"], o)
        self.assertFalse(o["lockedMid"], o)
        self.assertEqual(o["nMid"], 2, o)
        self.assertIsNone(o["whyMid"], o)
        self.assertTrue(o["locked"], o)
        self.assertFalse(o["watchEnd"], o)
        self.assertEqual(o["kind"], "keep", o)
        self.assertEqual(o["dock"], -1, o)

    def test_reread_kinds_and_the_intake_button(self):
        o = self._run(r"""
reset();
function kind(opts){ return _vaultRereadKind('x', opts); }
console.log(JSON.stringify({
  set: kind({ tgt: 1, cur: 4, qtyBase: false }),
  unique: kind({ tgt: 1, cur: 1, qtyBase: false }),
  spare: kind({ tgt: 3, cur: 1, qtyBase: false }),
  base: kind({ tgt: 1, cur: 1, qtyBase: true, cap: 3 }),
  cap: kind({ tgt: 1, cur: 3, qtyBase: true, cap: 3 })
}));
""")
        self.assertEqual(o["set"], "witness")
        self.assertEqual(o["unique"], "witness")
        self.assertEqual(o["spare"], "copy")
        self.assertEqual(o["base"], "copy")
        self.assertEqual(o["cap"], "over-cap")
        self.assertEqual(self.src.count(
            '''onclick="window._vaultEvidenceOpen(\\'' + jsArg(n) + '\\')"'''), 1)
        self.assertIn("if (_rk === 'witness' && _tgt <= 1 && _ownedAtStart.has(n)) { /* v3767 intake witness */", self.src)

    def test_move_record_checks_itself_off(self):
        o = self._run(r"""
reset();
var from = { holder: 'MAIN', location: 'stash', cell: 'stash:c1r1' };
var to = { holder: 'Mule', location: 'stash', cell: 'stash:c8r8' };
var task = _vaultMoveQueue("Harlequin Crest", from, to);
var still = _vaultMoveWitness(task, { holder: 'MAIN', location: 'stash', cell: 'stash:c1r1', frame: 'leave' });
var tally = _vaultMoveTally(still);
var verified = _vaultMoveWitness(tally, { holder: 'Mule', location: 'stash', cell: 'stash:c8r8', frame: 'arrive' });
var third = _vaultMoveWitness(task, { holder: 'Other', location: 'inventory', cell: 'inventory:c2r2', frame: 'else' });
var blank = _vaultMoveWitness(task, { holder: 'Other', location: 'stash', cell: null, frame: 'nope' });
var again = _vaultMoveWitness(verified, { holder: 'Mule', location: 'stash', cell: 'stash:c8r8', frame: 'arrive' });
console.log(JSON.stringify({
  queued: task.status, manual: task.manual, assign: assign["Harlequin Crest"] || null,
  still: still.status, stillEv: still.evidence,
  tally: tally.status, tallyManual: tally.manual,
  verified: verified.status, verifiedManual: verified.manual, ev: verified.evidence,
  third: third.status, thirdEv: third.evidence,
  blank: blank.status, blankEv: blank.evidence,
  again: again.evidence
}));
""")
        self.assertEqual(o["queued"], "to-move")
        self.assertTrue(o["manual"])
        self.assertIsNone(o["assign"])
        self.assertEqual(o["still"], "to-move")
        self.assertEqual(o["stillEv"], ["leave"])
        self.assertEqual(o["tally"], "moved-manual")
        self.assertTrue(o["tallyManual"])
        self.assertEqual(o["verified"], "verified")
        self.assertTrue(o["verifiedManual"])
        self.assertEqual(o["ev"], ["leave", "arrive"])
        self.assertEqual(o["third"], "moved-elsewhere")
        self.assertEqual(o["thirdEv"], ["else"])
        self.assertEqual(o["blank"], "to-move")
        self.assertEqual(o["blankEv"], [])
        self.assertEqual(o["again"], ["leave", "arrive"])

    def test_auto_intake_off_refuses_a_frame_and_a_typed_item_places(self):
        o = self._run(r"""
reset();
var absent = _vaultIntakeGate();
var reg = window.tvVaultRegister('Stone of Jordan', { by: 'tv-photo' });
var intakeP = window.vaultIntake([{ name: 'shot.jpg' }]);
var tvP = window.tvVaultAutoIntake({});
_vaultAutoIntakeSet(true);
var on = _vaultIntakeGate();
_vaultAutoIntakeSet(false);
var off = _vaultFrameRefuse();
window.LSR.setItem(VAULT_AUTO_INTAKE_KEY, 'maybe');
var unk = _vaultAutoIntakeRead();
var unkGate = _vaultFrameRefuse();
var unkToggle = _vaultAutoIntakeToggle();
PROV['Grief'] = { source: 'hand' };
owned.add('Grief');
ROUTES['Grief'] = { id: 'uni-weap', why: 'war weapon' };
var grew = rows('Grief')[0];
var dock = _dockNames();
function pack(p){
  return p.then(function(r){ return { refused: r && r.refused || null, err: null }; },
                 function(e){ return { refused: null, err: String(e && e.message || e) }; });
}
Promise.all([pack(intakeP), pack(tvP)]).then(function(both){
  console.log(JSON.stringify({
    absent: absent && absent.refused, reg: reg && reg.refused,
    ownedSoj: owned.has('Stone of Jordan'),
    intake: both[0], tv: both[1],
    on: on, off: off && off.refused,
    unk: unk, unkGate: unkGate && unkGate.refused, toggleKnown: unkToggle.known,
    store: window.LSR.getItem(VAULT_AUTO_INTAKE_KEY),
    source: grew.source, mule: grew.mule, kind: grew.kind,
    assign: Object.prototype.hasOwnProperty.call(assign, 'Grief'),
    dockGrief: dock.indexOf('Grief'),
    dockJunk: null
  }));
});
""")
        self.assertEqual(o["absent"], "auto-intake-off")
        self.assertEqual(o["reg"], "auto-intake-off")
        self.assertFalse(o["ownedSoj"])
        self.assertEqual(o["intake"]["refused"], "auto-intake-off")
        self.assertEqual(o["tv"]["refused"], "auto-intake-off")
        self.assertIsNone(o["on"])
        self.assertEqual(o["off"], "auto-intake-off")
        self.assertFalse(o["unk"]["known"])
        self.assertEqual(o["unkGate"], "auto-intake-off")
        self.assertFalse(o["toggleKnown"])
        self.assertEqual(o["store"], "maybe", "an unreadable choice was written over")
        self.assertEqual(o["source"], "manual")
        self.assertEqual(o["mule"], "uni-weap")
        self.assertEqual(o["kind"], "filed")
        self.assertFalse(o["assign"])
        self.assertEqual(o["dockGrief"], -1)
        self.assertIn("source: 'hand', by: String((opts && opts.by) || '+ Add an item')", self.src)

    def test_the_frame_doors_and_the_button_are_the_gate(self):
        for line in (
            "if (_stopped) return _stopped; /* v3767 intake stop */",
            "if (_stopped) return _stopped; /* v3767 register stop */",
            "if (_stopped) return _stopped; /* v3767 tv intake stop */",
            'onclick="window._vaultAutoIntakeToggle()"',
            '"d2r_vaultAutoIntake"',
        ):
            self.assertEqual(self.src.count(line), 1, line)

    def test_a_charm_and_a_runeword_witness_and_sit_beside_the_original(self):
        """A charm and a runeword. The same cell is one record and another witness.
        A second cell is a second copy on that item's own mule, beside the original."""
        o = self._run(r"""
reset();
ROUTES["Gheed's Fortune"] = { id: 'uni-small', why: 'grand charm' };
ROUTES['Obedience'] = { id: 'runewords', why: 'runeword' };
see("Gheed's Fortune", [
  L('Mule','stash','stash:c1r1','c1','a'),
  L('Mule','stash','stash:c1r1','c2','b'),
  L('Mule','stash','stash:c2r1','c2','c')
], 4);
see('Obedience', [
  L('Mule','stash','stash:c4r4','r1','a'),
  L('Mule','stash','stash:c4r4','r2','b'),
  L('Mule','stash','stash:c8r4','r2','c')
], 4);
var g = rows("Gheed's Fortune");
var rw = rows('Obedience');
console.log(JSON.stringify({
  gN: g.length,
  gMule: g.map(function(r){ return r.mule; }),
  gW: g[0] && g[0].sight ? g[0].sight.witnesses : null,
  gCell: g.map(function(r){ return r.sight && r.sight.cell; }),
  rwN: rw.length,
  rwMule: rw.map(function(r){ return r.mule; }),
  rwW: rw[0] && rw[0].sight ? rw[0].sight.witnesses : null,
  rwCell: rw.map(function(r){ return r.sight && r.sight.cell; })
}));
""")
        self.assertEqual(o["gN"], 2, "a re-read of the same charm cell is not a second row")
        self.assertEqual(o["gMule"], ["uni-small", "uni-small"])
        self.assertEqual(o["gW"], 2)
        self.assertEqual(o["gCell"], ["stash:c1r1", "stash:c2r1"])
        self.assertEqual(o["rwN"], 2, "a re-read of the same runeword cell is not a second row")
        self.assertEqual(o["rwMule"], ["runewords", "runewords"])
        self.assertEqual(o["rwW"], 2)
        self.assertEqual(o["rwCell"], ["stash:c4r4", "stash:c8r4"])

    def test_distinct_attacks_clear_the_vault_apply_wilson_bar(self):
        from confidence import confluence, wilson_lower
        import self_arming as SA
        bar = SA.LOCKS["vault.apply"]["bar"]
        kinds_bar = SA.LOCKS["vault.apply"]["kinds_bar"]
        n = len(RED_PROOF)
        w = wilson_lower(n, n)
        conf = confluence(["sabotage"], SA.KINDS)
        msg = ("copy witness: %d distinct attacks, wilson %.4f vs vault.apply bar %.3f; "
               "kinds sabotage %.2f vs %.2f" % (n, w, bar, conf, kinds_bar))
        print(msg)
        self.assertGreaterEqual(n, 12, msg)
        self.assertGreaterEqual(w, bar, msg)
        self.assertLess(conf, kinds_bar, msg)


RED_PROOF = [
    {"why": "Distinct cells collapse back to the inflated copies[]. Natalya's second helm disappears into the count.",
     "file": "bible.html", "find": "return _nSg; /* v3767 distinct cells */",
     "replace": "return have; /* v3767 distinct cells */", "matches": 1},
    {"why": "The same cell across reels becomes another copy.",
     "file": "bible.html", "find": "} else g = by[key]; /* v3767 same cell */",
     "replace": "} else { g = { holder: holder, location: location, cell: cell, sessions: {} }; order.push(g); } /* v3767 same cell */",
     "matches": 1},
    {"why": "Three frames of one session count as three witnesses, and a look with no session invents one.",
     "file": "bible.html", "find": "if (sid) g.sessions[String(sid)] = 1; /* v3767 session witness */",
     "replace": "if (true) g.sessions[String(sid || k.frame || 'invented')] = 1; /* v3767 session witness */",
     "matches": 1},
    {"why": "The same cell string on two holders is one copy.",
     "file": "bible.html",
     "find": "var key = holderKey + '\\u0000' + String(location || '') + '\\u0000' + cell; /* v3767 copy key */",
     "replace": "var key = cell; /* v3767 copy key */", "matches": 1},
    {"why": "The evidence look drops the holder, so two mules share one record.",
     "file": "bible.html",
     "find": "cell: k.cell || null, loc: k.loc || null, holder: k.holder || k.character || null, /* v3767 look place */",
     "replace": "cell: k.cell || null, /* v3767 look place */", "matches": 1},
    {"why": "The record no longer carries the sight the cell was counted from.",
     "file": "bible.html",
     "find": "if (g) rec.sight = { holder: g.holder, location: g.location, cell: g.cell, witnesses: g.witnesses }; /* v3767 sight */",
     "replace": "if (false && g) rec.sight = { holder: g.holder, location: g.location, cell: g.cell, witnesses: g.witnesses }; /* v3767 sight */",
     "matches": 1},
    {"why": "Two sessions no longer read as WATCHING.",
     "file": "bible.html",
     "find": "if (watchN > 0 && watchN < mins && !lockedWhy) rec.watching = true; /* v3767 watching */",
     "replace": "if (false) rec.watching = true; /* v3767 watching */", "matches": 1},
    {"why": "Three sessions never lock.",
     "file": "bible.html",
     "find": "else if (lockedWhy) rec.locked = true; /* v3767 locked */",
     "replace": "else if (false && lockedWhy) rec.locked = true; /* v3767 locked */", "matches": 1},
    {"why": "A presence re-read climbs a copy instead of a witness.",
     "file": "bible.html", "find": "return 'witness'; /* v3767 reread witness */",
     "replace": "return 'copy'; /* v3767 reread witness */", "matches": 1},
    {"why": "A multi-keep still under its target is called a witness, so the spare is not kept.",
     "file": "bible.html", "find": "if (tgt > 1 && cur < tgt) return 'copy'; /* v3767 reread spare */",
     "replace": "if (tgt > 1 && cur < tgt) return 'witness'; /* v3767 reread spare */", "matches": 1},
    {"why": "A socketed base under the cap is called a witness, so the extra base is dropped.",
     "file": "bible.html", "find": "if (opts.qtyBase && cur < cap) return 'copy'; /* v3767 reread base */",
     "replace": "if (opts.qtyBase && cur < cap) return 'witness'; /* v3767 reread base */", "matches": 1},
    {"why": "A multi-keep above the witnessed cells is ignored.",
     "file": "bible.html",
     "find": "if (typeof multiKeep !== 'undefined' && multiKeep && multiKeep[name] > _nSg)\n          return Math.max(_nSg,",
     "replace": "if (typeof multiKeep !== 'undefined' && multiKeep && multiKeep[name] > 999)\n          return Math.max(_nSg,",
     "matches": 1},
    {"why": "A hand-typed item is not marked manual.",
     "file": "bible.html", "find": "if (_ps === 'hand') rec.source = 'manual'; /* v3767 manual source */",
     "replace": "if (_ps === 'hand') rec.source = null; /* v3767 manual source */", "matches": 1},
    {"why": "A sighting at the planned TO stays to-move, so the task never ticks off.",
     "file": "bible.html", "find": "t.status = 'verified'; /* v3767 move verified */",
     "replace": "t.status = 'to-move'; /* v3767 move verified */", "matches": 1},
    {"why": "A sighting still at FROM is called verified.",
     "file": "bible.html", "find": "t.status = 'to-move'; /* v3767 move still */",
     "replace": "t.status = 'verified'; /* v3767 move still */", "matches": 1},
    {"why": "A third spot is called verified instead of moved elsewhere.",
     "file": "bible.html", "find": "t.status = 'moved-elsewhere'; /* v3767 move elsewhere */",
     "replace": "t.status = 'verified'; /* v3767 move elsewhere */", "matches": 1},
    {"why": "A hand tally is stored as verified before any witness.",
     "file": "bible.html", "find": "t.status = 'moved-manual'; /* v3767 move tally */",
     "replace": "t.status = 'verified'; /* v3767 move tally */", "matches": 1},
    {"why": "A sighting with no cell is a third spot. Unknown is treated as elsewhere.",
     "file": "bible.html", "find": "if (place.cell == null) return t; /* v3767 move unknown */",
     "replace": "if (false && place.cell == null) return t; /* v3767 move unknown */", "matches": 1},
    {"why": "The witness frame is not kept on the task.",
     "file": "bible.html",
     "find": "if (frame != null && frame !== '' && t.evidence.indexOf(String(frame)) < 0) t.evidence.push(String(frame)); /* v3767 move proof */",
     "replace": "void frame; /* v3767 move proof */", "matches": 1},
    {"why": "Queuing a move writes assign. The hand door files the item.",
     "file": "bible.html",
     "find": "return _vaultMoveTask({ name: name, from: from, to: to, status: 'to-move', evidence: [], manual: true }); /* v3767 move queue */",
     "replace": "try { assign[name] = 'wrote'; } catch (eQ) {}\n    return _vaultMoveTask({ name: name, from: from, to: to, status: 'to-move', evidence: [], manual: true }); /* v3767 move queue */",
     "matches": 1},
    {"why": "An absent AUTO INTAKE choice reads as on, so a frame registers.",
     "file": "bible.html",
     "find": "if (raw == null || raw === '') return { on: false, known: true }; /* v3767 intake absent */",
     "replace": "if (raw == null || raw === '') return { on: true, known: true }; /* v3767 intake absent */",
     "matches": 1},
    {"why": "A value that is not on or off reads as on.",
     "file": "bible.html",
     "find": "return { on: false, known: false }; /* v3767 intake unknown */",
     "replace": "return { on: true, known: true }; /* v3767 intake unknown */",
     "matches": 1},
    {"why": "The switch writes off no matter which way he sets it.",
     "file": "bible.html",
     "find": "window.LSR.setItem(VAULT_AUTO_INTAKE_KEY, on ? 'on' : 'off'); /* v3767 intake write */",
     "replace": "window.LSR.setItem(VAULT_AUTO_INTAKE_KEY, 'off'); /* v3767 intake write */",
     "matches": 1},
    {"why": "The frame gate never refuses, so AUTO INTAKE off still registers.",
     "file": "bible.html", "find": "if (_aiOff) return _aiOff; /* v3767 frame gate */",
     "replace": "if (false && _aiOff) return _aiOff; /* v3767 frame gate */", "matches": 1},
    {"why": "Screenshot intake ignores the switch.",
     "file": "bible.html", "find": "if (_stopped) return _stopped; /* v3767 intake stop */",
     "replace": "if (false && _stopped) return _stopped; /* v3767 intake stop */", "matches": 1},
    {"why": "The TV register ignores the switch and owns the name.",
     "file": "bible.html", "find": "if (_stopped) return _stopped; /* v3767 register stop */",
     "replace": "if (false && _stopped) return _stopped; /* v3767 register stop */", "matches": 1},
    {"why": "TV auto-intake ignores the switch and pulls a frame.",
     "file": "bible.html", "find": "if (_stopped) return _stopped; /* v3767 tv intake stop */",
     "replace": "if (false && _stopped) return _stopped; /* v3767 tv intake stop */", "matches": 1},
    {"why": "The AUTO INTAKE button no longer calls the switch.",
     "file": "bible.html", "find": 'onclick="window._vaultAutoIntakeToggle()"',
     "replace": 'onclick="void(0)"', "matches": 1},
    {"why": "A charm or a runeword's second copy leaves its mule, so the duplicate does not sit next to the original.",
     "file": "bible.html",
     "find": "else if (_seamR && _seamR.loc === 'filed' && _seamR.mule) { kind = 'filed'; mid = _seamR.mule; } /* v3767 records home */",
     "replace": "else if (false && _seamR && _seamR.loc === 'filed' && _seamR.mule) { kind = 'filed'; mid = _seamR.mule; } /* v3767 records home */",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
