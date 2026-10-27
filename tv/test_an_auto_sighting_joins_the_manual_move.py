# -*- coding: utf-8 -*-
"""An AUTO INTAKE sighting files through the same move the hand add already uses.

Elad, 2026-10-27. The toolbar chip and the Advanced switch are one control.
The chip only opens the panel. On Air's subtitle says auto intake and it
starts a recording. A reel sighting carries lane and cell. With the switch on,
that sighting is one look, a vault record, and a to-move whose FROM is the
cell that was seen and whose TO is the organizer's cell. A MAIN lane and a
name with no home do not get a move row. Two frames of one session are still
one look. The bar stays two sessions.

RED_PROOF below. [[the-unjoined-end]] [[unknown-stays-unknown]] [[regression-guard]]
"""
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
UI = os.path.join(HERE, "control_ui.html")
NODE = os.environ.get("NODE") or shutil.which("node")


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


def _var(src, name):
    m = re.search(r"^  var %s = [^;]*;" % re.escape(name), src, re.M)
    if not m:
        raise AssertionError("could not find var %s" % name)
    return m.group(0)


class AutoSightingJoinsTheManualMove(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not NODE:
            raise AssertionError("node is not on this machine — this law does not skip")
        with open(BIBLE, encoding="utf-8") as f:
            cls.src = f.read()
        with open(UI, encoding="utf-8") as f:
            cls.ui = f.read()

    def _run(self, prog):
        raw = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        self.assertEqual(raw.returncode, 0, (raw.stderr or "")[-2000:])
        line = [ln for ln in raw.stdout.splitlines() if ln.startswith("{") or ln.startswith("[")][-1]
        import json
        return json.loads(line)

    def test_the_top_chip_is_gone_and_the_advanced_switch_remains(self):
        self.assertNotIn('id="vault-chip-intake"', self.src)
        self.assertNotIn('id="vault-chip-intake-s"', self.src)
        self.assertEqual(self.src.count('id="vault-auto-intake"'), 1)
        self.assertEqual(self.src.count('onclick="window._vaultAutoIntakeToggle()"'), 1)
        self.assertNotIn("getElementById('vault-chip-intake'", self.src)

    def test_on_air_says_capture_and_not_auto_intake(self):
        self.assertNotIn("auto intake · pause on stash", self.ui)
        self.assertEqual(self.ui.count("capture · pause on stash"), 2)

    def test_a_lane_sighting_with_no_from_cell_is_a_to_move(self):
        prog = "\n".join([
            "var window = globalThis;",
            _fn(self.src, "_vaultMovePlace"),
            _fn(self.src, "_vaultMoveSamePlace"),
            _fn(self.src, "_vaultMoveTask"),
            _fn(self.src, "_vaultMoveWitness"),
            r"""
function muleById(id){ return id === 'magic' ? { id: 'magic', name: 'NEW NAME' } : null; }
var task = _vaultMoveTask({
  name: 'Thresher', manual: false, status: 'to-move',
  from: { holder: null, location: null, cell: null },
  to: { holder: 'UNI-WEAPONS', location: 'stash', cell: 'stash:c0r0' }
});
var seen = _vaultMoveWitness(task, { lane: 'stash', cell: 'stash:c7r1', frame: 'f1' });
var third = _vaultMoveWitness(_vaultMoveTask({
  name: 'Thresher', manual: false, status: 'to-move',
  from: { holder: 'MAIN', location: 'stash', cell: 'stash:c7r1' },
  to: { holder: 'UNI-WEAPONS', location: 'stash', cell: 'stash:c0r0' }
}), { holder: 'Other', lane: 'inventory', cell: 'inventory:c2r2', frame: 'else' });
var blank = _vaultMoveWitness(_vaultMoveTask({
  name: 'Thresher', manual: false, status: 'to-move',
  from: { holder: 'MAIN', location: 'stash', cell: 'stash:c7r1' },
  to: { holder: 'UNI-WEAPONS', location: 'stash', cell: 'stash:c0r0' }
}), { lane: 'stash', cell: null, frame: 'nope' });
var there = _vaultMoveWitness(_vaultMoveTask({
  name: 'Charm', manual: false, status: 'to-move',
  from: { holder: null, location: null, cell: null },
  to: { holder: 'MAGIC', location: 'stash', cell: 'stash:c0r0' }
}), { holder: 'MAGIC', lane: 'stash', cell: 'stash:c2r1', frame: 'f2' });
var home = _vaultMoveWitness(_vaultMoveTask({
  name: 'Charm', manual: false, status: 'to-move',
  from: { holder: null, location: null, cell: null },
  to: { holder: 'MAGIC', location: 'stash', cell: 'stash:c0r0' }
}), { holder: 'MAGIC', lane: 'stash', cell: 'stash:c0r0', frame: 'f3' });
var renamed = _vaultMoveWitness(_vaultMoveTask({
  name: 'Charm', manual: false, status: 'to-move',
  from: { holder: null, location: null, cell: null },
  to: { id: 'magic', holder: 'OLD NAME', location: 'stash', cell: 'stash:c0r0' }
}), { holder: 'NEW NAME', lane: 'stash', cell: 'stash:c0r0', frame: 'f4' });
var queued = _vaultMoveWitness(_vaultMoveTask({
  name: 'Harlequin Crest', manual: true, status: 'to-move',
  from: { holder: 'MAIN', location: 'stash', cell: 'stash:c1r1' },
  to: { holder: 'Mule', location: 'stash', cell: 'stash:c8r8' }
}), { holder: 'Other', location: 'inventory', cell: 'inventory:c2r2', frame: 'else' });
console.log(JSON.stringify({
  status: seen.status, fromCell: seen.from.cell, fromLoc: seen.from.location, toCell: seen.to.cell,
  third: third.status, blank: blank.status, there: there.status, home: home.status, renamed: renamed.status, queued: queued.status
}));
""",
        ])
        o = self._run(prog)
        self.assertEqual(o["status"], "to-move")
        self.assertEqual(o["fromCell"], "stash:c7r1")
        self.assertEqual(o["fromLoc"], "stash")
        self.assertEqual(o["toCell"], "stash:c0r0")
        self.assertEqual(o["third"], "moved-elsewhere")
        self.assertEqual(o["blank"], "to-move")
        self.assertEqual(o["there"], "to-move")
        self.assertEqual(o["home"], "verified")
        self.assertEqual(o["renamed"], "verified")
        self.assertEqual(o["queued"], "moved-elsewhere")

    def test_shared_is_a_container_and_a_bare_frame_is_one_look(self):
        prog = "\n".join([
            "var window = globalThis;",
            _var(self.src, "_WIT_STASH"),
            _var(self.src, "_WIT_MAIN"),
            _var(self.src, "VAULT_WITNESS_FLOOR"),
            _var(self.src, "VAULT_WITNESS_MIN"),
            _var(self.src, "VAULT_RETRO_KEEP_MIN"),
            _fn(self.src, "_lookConf"),
            _assigned(self.src, r"window\._vaultWitnessCheck\s*=\s*function\s*\("),
            _fn(self.src, "_vaultIntakeLook"),
            r"""
var one = window._vaultWitnessCheck({ lane: 'shared', sessions: [
  { session: 's1', frame: 'f1' }, { session: 's2', frame: 'f2' }
]});
var bare = _vaultIntakeLook({ lane: 'stash', cell: 'stash:c7r1', frame: 'f9', session: 's9' });
var again = _vaultIntakeLook(bare);
var two = _vaultIntakeLook({ lane: 'stash', cell: 'stash:c7r1', frame: 'f10', session: 's10', sessions: bare.sessions });
var judged = window._vaultWitnessCheck(two);
var same = _vaultIntakeLook({ lane: 'stash', cell: 'stash:c7r1', frame: 'f11', session: 's9', sessions: bare.sessions });
var oneSess = window._vaultWitnessCheck(same);
console.log(JSON.stringify({
  sharedOk: one.ok, sharedWhy: one.why || null,
  frame: bare.sessions[0].frame, cell: bare.sessions[0].cell, lane: bare.sessions[0].lane,
  again: again.sessions.length,
  looks: judged.ok ? judged.sessions.length : judged.looks,
  judgedOk: judged.ok,
  sameOk: oneSess.ok, sameLooks: oneSess.looks
}));
""",
        ])
        o = self._run(prog)
        self.assertTrue(o["sharedOk"], o["sharedWhy"])
        self.assertEqual(o["frame"], "f9")
        self.assertEqual(o["cell"], "stash:c7r1")
        self.assertEqual(o["lane"], "stash")
        self.assertEqual(o["again"], 1)
        self.assertTrue(o["judgedOk"], o)
        self.assertEqual(o["looks"], 2)
        self.assertFalse(o["sameOk"])
        self.assertEqual(o["sameLooks"], 1)

    def test_a_main_lane_and_an_unknown_name_do_not_get_a_move_row(self):
        prog = "\n".join([
            "var window = globalThis;",
            _fn(self.src, "_vaultMoveAutoRow"),
            r"""
function _vaultMoveHome(name){
  var homes = {
    'Thresher': { id: 'uni-weap', holder: 'UNI-WEAPONS', location: 'stash' },
    'Treachery': { id: 'shared', holder: 'SHARED STASH', location: 'shared' },
    'Tome of Town Portal': { id: 'main', holder: 'MAIN', location: 'inventory' },
    'Zzyzx Blade of Nothing': { id: null, holder: null, location: null }
  };
  return homes[name] || { id: null, holder: null, location: null };
}
var tome = _vaultMoveAutoRow('Tome of Town Portal', { lane: 'inventory', cell: 'inventory:c0r2' });
var worn = _vaultMoveAutoRow('Thresher', { lane: 'equipped', cell: 'equipped:weapon' });
var unk = _vaultMoveAutoRow('Zzyzx Blade of Nothing', { lane: 'stash', cell: 'stash:c1r1' });
var uni = _vaultMoveAutoRow('Thresher', { lane: 'stash', cell: 'stash:c7r1' });
var rw = _vaultMoveAutoRow('Treachery', { lane: 'stash', cell: 'stash:c3r4' });
console.log(JSON.stringify({
  tome: tome.why, worn: worn.why, unk: unk.why,
  uni: uni.row, rw: rw.row
}));
""",
        ])
        o = self._run(prog)
        self.assertEqual(o["tome"], "main")
        self.assertEqual(o["worn"], "main")
        self.assertEqual(o["unk"], "no-home")
        self.assertTrue(o["uni"])
        self.assertTrue(o["rw"])

    def test_the_register_records_the_look_then_persists_then_moves(self):
        wrap = _assigned(self.src, r"window\.tvVaultRegister = function\(name\)\{")
        prog = "\n".join([
            "var window = globalThis;",
            "var owned = new Set();",
            _fn(self.src, "_vaultIntakeLook"),
            r"""
function _inner(name, wit){
  window._lastWit = wit;
  var had = owned.has(name);
  owned.add(name);
  return { ok: true, mode: had ? 'already' : 'new', label: name, filed: false, refused: null };
}
window._vaultIntakeLook = _vaultIntakeLook;
window._vaultIntakeGate = function(){ return null; };
window._vaultRecordsPersist = function(){ window._persisted = (window._persisted || 0) + 1; return { ok: true }; };
window._vaultMoveApplySight = function(n, w){ window._applied = { n: n, cell: w && w.cell, lane: w && w.lane }; return { applied: true }; };
window._vaultMoveAutoRow = function(n, w){
  var lane = String((w && (w.lane || w.loc || w.location)) || '');
  if (lane === 'inventory' || lane === 'equipped' || lane === 'equipment') return { row: false, why: 'main' };
  if (n === 'Zzyzx Blade of Nothing') return { row: false, why: 'no-home' };
  return { row: true, why: null };
};
""",
            wrap,
            r"""
window.LSR = { getItem: function(){ return 'on'; }, setItem: function(){} };
var a = window.tvVaultRegister('Thresher', { lane: 'stash', cell: 'stash:c7r1', frame: 'f1', session: 's1', by: 'tv-live' });
var wit = window._lastWit;
var b = window.tvVaultRegister('Tome of Town Portal', { lane: 'inventory', cell: 'inventory:c0r2', frame: 'f2', session: 's1', by: 'tv-live' });
console.log(JSON.stringify({
  mode: a.mode,
  frame: wit && wit.sessions && wit.sessions[0] && wit.sessions[0].frame,
  cell: wit && wit.sessions && wit.sessions[0] && wit.sessions[0].cell,
  persisted: window._persisted || 0,
  moved: window._applied && window._applied.n,
  movedCell: window._applied && window._applied.cell,
  tome: b && b.label
}));
""",
        ])
        o = self._run(prog)
        self.assertEqual(o["mode"], "new")
        self.assertEqual(o["frame"], "f1")
        self.assertEqual(o["cell"], "stash:c7r1")
        self.assertGreaterEqual(o["persisted"], 1)
        self.assertEqual(o["moved"], "Thresher")
        self.assertEqual(o["movedCell"], "stash:c7r1")
        self.assertEqual(o["tome"], "Tome of Town Portal")
        self.assertIn("window._vaultIntakeLook", wrap)
        self.assertIn("window._vaultRecordsPersist", wrap)
        self.assertIn("window._vaultMoveAutoRow", wrap)

    def test_a_zero_look_witness_does_not_open_a_move(self):
        wrap = _assigned(self.src, r"window\.tvVaultRegister = function\(name\)\{")
        prog = "\n".join([
            "var window = globalThis;",
            "var owned = new Set();",
            _fn(self.src, "_vaultIntakeLook"),
            r"""
function _inner(name, wit){
  owned.add(name);
  return { ok: true, mode: 'new', label: name, filed: false, refused: null };
}
window._vaultIntakeLook = _vaultIntakeLook;
window._vaultIntakeGate = function(){ return null; };
window._vaultRecordsPersist = function(){ return { ok: true }; };
window._vaultMoveApplySight = function(n, w){ window._applied = n; return { applied: true }; };
window._vaultMoveAutoRow = function(){ return { row: true, why: null }; };
""",
            wrap,
            r"""
window.LSR = { getItem: function(){ return 'on'; }, setItem: function(){} };
function took(name, wit){
  window._applied = null;
  window.tvVaultRegister(name, wit);
  return window._applied;
}
var treachery = took('Treachery', { lane: 'stash', cell: 'stash:c1r1', frame: 'made-up-frame', by: 'tv-live' });
var charm = took('Small Charm', { lane: 'stash', cell: 'stash:c0r1', frame: 'f-charm', session: '   ', by: 'tv-live' });
var torch = took('Hellfire Torch', { lane: 'stash', cell: 'stash:c3r1', frame: 'f-torch', session: 's-torch', conf: 0.40, by: 'tv-live' });
var one = took('Thresher', { lane: 'stash', cell: 'stash:c7r1', frame: 'f1', session: 's1', by: 'tv-live' });
console.log(JSON.stringify({ treachery: treachery, charm: charm, torch: torch, one: one }));
""",
        ])
        o = self._run(prog)
        self.assertIsNone(o["treachery"])
        self.assertIsNone(o["charm"])
        self.assertIsNone(o["torch"])
        self.assertEqual(o["one"], "Thresher")

    def test_a_live_frame_counts_and_two_sessions_file(self):
        """The read's score is the frame's, copied onto every name. It is not a look's confidence.

        Two sessions with that score file. One session stays owned and unfiled. An empty
        session is not a look. A look that itself carries a confidence under the floor still fails.
        """
        self.assertEqual(self.src.count("/* live witness frame */"), 1)
        self.assertEqual(self.src.count(
            "var _liveW = (typeof window._vaultLiveWitness === 'function') ? window._vaultLiveWitness(rd)"), 1)
        self.assertEqual(self.src.count(
            "sessions: [{ session: _liveSid || null, frame: _liveFid || null, conf: null }]"), 1)
        prog = "\n".join([
            "var window = globalThis;",
            "var PROV_KEY = 'd2r_vaultProv';",
            "var assign = {};",
            "var owned = new Set();",
            "var store = {};",
            "function _provAll(){ return store; }",
            "function _provWrite(all){ store = all; }",
            "function _vHomeOk(id){ return id === 'uni-weap'; }",
            "function _vHomeName(id){ return 'UNI-WEAPONS'; }",
            "function _vMainName(){ return 'MAIN'; }",
            "function _vNoHomeWhy(nm){ return nm + ' has no mule'; }",
            "function saveA(){ return true; }",
            "function persistOwned(){}",
            "window._consumable = function(){ return false; };",
            "window.LSR = {};",
            "window.D2R_BUILD = { id: 'law' };",
            _fn(self.src, "_str"),
            _fn(self.src, "_num"),
            _fn(self.src, "_iso"),
            _fn(self.src, "_receipt"),
            _fn(self.src, "_lookConf"),
            _var(self.src, "_WIT_STASH"),
            _var(self.src, "_WIT_MAIN"),
            _var(self.src, "VAULT_WITNESS_FLOOR"),
            _var(self.src, "VAULT_WITNESS_MIN"),
            _var(self.src, "VAULT_RETRO_KEEP_MIN"),
            _assigned(self.src, r"window\._vaultWitnessCheck\s*=\s*function\s*\("),
            _fn(self.src, "_vaultLiveWitness"),
            _fn(self.src, "_vaultIntakeLook"),
            _fn(self.src, "_receiptStashWitness"),
            _assigned(self.src, r"window\.vaultFile = function\(name, witness, opts\)\{"),
            r"""
function live(rd){
  return _vaultIntakeLook(_vaultLiveWitness(rd));
}
function keep(name, wit){
  var look = wit.sessions[0];
  store[name] = _receipt({
    source: 'tv-live', by: 'tvVaultRegister', loc: 'stash',
    sessionId: look.session || null, frameId: look.frame || null, conf: look.conf
  }, 1700000000000, true);
}
var first = live({ conf: 0.45, sessionId: 'sess-a', frameId: 'frame-a' });
var second = live({ conf: 0.45, sessionId: 'sess-b', frameId: 'frame-b' });
keep('Thresher', first);
var gathered = _receiptStashWitness('Thresher', second);
var judged = window._vaultWitnessCheck(gathered);
var oneCheck = window._vaultWitnessCheck(first);
var oneFile = window.vaultFile('Spirit', first, { mule: 'uni-weap' });
var filed = window.vaultFile('Thresher', gathered, { mule: 'uni-weap' });
keep('Treachery', first);
var again = live({ conf: 0.45, sessionId: 'sess-a', frameId: 'frame-c' });
var sameG = _receiptStashWitness('Treachery', again);
var same = window._vaultWitnessCheck(sameG);
var sameFile = window.vaultFile('Treachery', sameG, { mule: 'uni-weap' });
var empty = live({ conf: 0.45, sessionId: '   ', frameId: 'frame-a' });
var emptyJ = window._vaultWitnessCheck(empty);
var low = window._vaultWitnessCheck({ lane: 'stash', by: 'reader', sessions: [
  { session: 'sess-a', frame: 'frame-a', conf: 0.40 },
  { session: 'sess-b', frame: 'frame-b', conf: 0.40 }
]});
var copied = window._vaultWitnessCheck({ lane: 'stash', by: 'reader', sessions: [
  { session: 'sess-a', frame: 'frame-a', conf: 0.45 },
  { session: 'sess-b', frame: 'frame-b', conf: 0.45 }
]});
console.log(JSON.stringify({
  conf: first.sessions[0].conf,
  session: first.sessions[0].session,
  frame: first.sessions[0].frame,
  judgedOk: judged.ok,
  looks: judged.ok ? judged.sessions.length : judged.looks,
  filed: !!(filed && filed.ok),
  filedMode: filed && filed.mode,
  mule: assign.Thresher || null,
  oneOk: oneCheck.ok,
  oneLooks: oneCheck.looks,
  oneRefused: oneFile && oneFile.refused,
  spirit: assign.Spirit || null,
  sameOk: same.ok,
  sameLooks: same.looks,
  treachery: assign.Treachery || null,
  emptySession: empty.sessions[0].session || null,
  emptyLooks: emptyJ.looks,
  emptyOk: emptyJ.ok,
  lowLooks: low.looks,
  lowOk: low.ok,
  copiedLooks: copied.looks,
  copiedOk: copied.ok,
  min: VAULT_WITNESS_MIN
}));
""",
        ])
        # The receipt written for Thresher is replaced when the filing succeeds. Read it before that
        # by asking the program for the look it stored. The print above lost that row, so judge the
        # stored confidence from a second, smaller run that stops before vaultFile.
        o = self._run(prog)
        self.assertIsNone(o["conf"])
        self.assertEqual(o["session"], "sess-a")
        self.assertEqual(o["frame"], "frame-a")
        self.assertTrue(o["judgedOk"], o)
        self.assertEqual(o["looks"], 2)
        self.assertTrue(o["filed"], o)
        self.assertEqual(o["filedMode"], "filed")
        self.assertEqual(o["mule"], "uni-weap")
        self.assertFalse(o["oneOk"])
        self.assertEqual(o["oneLooks"], 1)
        self.assertEqual(o["oneRefused"], "witness")
        self.assertIsNone(o["spirit"])
        self.assertFalse(o["sameOk"])
        self.assertEqual(o["sameLooks"], 1)
        self.assertIsNone(o["treachery"])
        self.assertIsNone(o["emptySession"])
        self.assertEqual(o["emptyLooks"], 0)
        self.assertFalse(o["emptyOk"])
        self.assertEqual(o["lowLooks"], 0)
        self.assertFalse(o["lowOk"])
        self.assertEqual(o["copiedLooks"], 0)
        self.assertFalse(o["copiedOk"])
        self.assertEqual(o["min"], 2)
        receipt = self._run("\n".join([
            "var window = globalThis;",
            "window.D2R_BUILD = { id: 'law' };",
            _fn(self.src, "_str"),
            _fn(self.src, "_num"),
            _fn(self.src, "_iso"),
            _fn(self.src, "_receipt"),
            _fn(self.src, "_vaultLiveWitness"),
            r"""
var w = _vaultLiveWitness({ conf: 0.45, sessionId: 'sess-a', frameId: 'frame-a' });
var look = w.sessions[0];
var row = _receipt({
  source: 'tv-live', by: 'tvVaultRegister', loc: 'stash',
  sessionId: look.session, frameId: look.frame, conf: look.conf
}, 1700000000000, true);
console.log(JSON.stringify({ conf: row.looks[0].conf, id: row.looks[0].id, frame: row.looks[0].frame, kind: row.kind }));
""",
        ]))
        self.assertIsNone(receipt["conf"])
        self.assertEqual(receipt["id"], "sess-a")
        self.assertEqual(receipt["frame"], "frame-a")
        self.assertEqual(receipt["kind"], "owned")

    def test_inventory_and_an_unknown_name_are_not_move_rows(self):
        prog = "\n".join([
            "var window = globalThis;",
            "var assign = {};",
            "var homes = {",
            "  'Thresher': { id: 'uni-weap', holder: 'UNI-WEAPONS', location: 'stash' },",
            "  'Treachery': { id: 'shared', holder: 'SHARED STASH', location: 'shared' }",
            "};",
            "function _vaultMoveHome(name){ return homes[name] || { id: null, holder: null, location: null }; }",
            "function muleById(){ return null; }",
            "function _vaultSeamHome(){ return window._seam || null; }",
            "function suggestMule(){ return null; }",
            "function _vaultMisfiled(){ return false; }",
            "function _vaultMoveBag(){ return { map: {}, prior: { records: [] }, unread: false }; }",
            "function _vaultRecords(){ return { records: window._recs || [] }; }",
            "function _vaultMoveCommit(list){ window._committed = (window._committed || []).concat(list || []); return { ok: true, wrote: true }; }",
            "function _vaultMoveGroup(rows){ return rows || []; }",
            "function _vaultMoveLocks(){ return []; }",
            "function _vaultMoveEnsure(name){",
            "  var fromLoc = window._ensFrom || 'stash';",
            "  var home = _vaultMoveHome(name);",
            "  return { fresh: true, task: _vaultMoveTask({",
            "    name: name, status: 'to-move', manual: false,",
            "    from: { holder: 'MAIN', location: fromLoc, cell: fromLoc + ':c1r1' },",
            "    to: { holder: home.holder || 'UNI-WEAPONS', location: home.location || 'stash', cell: 'stash:c0r0', id: home.id }",
            "  }) };",
            "}",
            _fn(self.src, "_vaultMovePlace"),
            _fn(self.src, "_vaultMoveSamePlace"),
            _fn(self.src, "_vaultMoveTask"),
            _fn(self.src, "_vaultMoveWorn"),
            _fn(self.src, "_vaultMoveOnKeep"),
            _fn(self.src, "_vaultMoveMainLane"),
            _fn(self.src, "_vaultMoveAutoRow"),
            _fn(self.src, "_vaultMoveShown"),
            _fn(self.src, "_vaultThrowReason"),
            _fn(self.src, "_vaultThrowRoute"),
            _fn(self.src, "_vaultThrowTask"),
            _fn(self.src, "_vaultSightLooks"),
            _fn(self.src, "_vaultMoveCollect"),
            r"""
function task(spec){ return _vaultMoveTask(spec); }
var invThrow = _vaultMoveShown(task({
  name: 'Thresher', kind: 'throw', status: 'to-move',
  from: { holder: 'MAIN', location: 'inventory', cell: 'inventory:c0r0' }, to: {}
}));
var equipped = _vaultMoveShown(task({
  name: 'Thresher', status: 'to-move',
  from: { holder: 'MAIN', location: 'equipped', cell: 'equipped:weapon' },
  to: { holder: 'UNI-WEAPONS', location: 'stash', cell: 'stash:c0r0', id: 'uni-weap' }
}));
var invFilled = _vaultMoveShown(task({
  name: 'Thresher', status: 'to-move',
  from: { holder: 'MAIN', location: 'inventory', cell: 'inventory:c1r1' },
  to: { holder: 'UNI-WEAPONS', location: 'stash', cell: 'stash:c0r0', id: 'uni-weap' }
}));
var unknown = _vaultMoveShown(task({
  name: 'Zzyzx Blade of Nothing', kind: 'throw', status: 'to-move',
  from: { holder: null, location: 'stash', cell: 'stash:c1r1' }, to: {}
}));
var ruledOff = _vaultMoveShown(task({
  name: 'Zzyzx Blade of Nothing', kind: 'throw', status: 'to-move',
  from: { holder: null, location: 'stash', cell: 'stash:c1r1' }, to: {}
}));
assign['Zzyzx Blade of Nothing'] = '__throwout';
var ruled = _vaultMoveShown(task({
  name: 'Zzyzx Blade of Nothing', kind: 'throw', status: 'to-move',
  from: { holder: null, location: 'stash', cell: 'stash:c1r1' }, to: {}
}));
var stash = _vaultMoveShown(task({
  name: 'Thresher', status: 'to-move', manual: false,
  from: { holder: 'MAIN', location: 'stash', cell: 'stash:c7r1' },
  to: { holder: 'UNI-WEAPONS', location: 'stash', cell: 'stash:c0r0', id: 'uni-weap' }
}));
var shared = _vaultMoveShown(task({
  name: 'Treachery', status: 'to-move', manual: false,
  from: { holder: null, location: 'shared', cell: 'shared:c3r4' },
  to: { holder: 'SHARED STASH', location: 'shared', cell: 'shared:c0r0', id: 'shared' }
}));
function collect(records){
  window._recs = records;
  window._committed = [];
  var pack = _vaultMoveCollect();
  pack.committed = (window._committed || []).map(function(x){ return x.name; });
  return pack;
}
delete assign['Zzyzx Blade of Nothing'];
var fromInv = collect([{ name: 'Thresher', copyIx: 0, sight: { location: 'inventory', cell: 'inventory:c0r2' } }]);
var fromEquip = collect([{ name: 'Thresher', copyIx: 0, sight: { location: 'equipped', cell: 'equipped:weapon' } }]);
var fromUnknown = collect([{ name: 'Zzyzx Blade of Nothing', copyIx: 0, sight: { location: 'stash', cell: 'stash:c1r1' } }]);
var fromUnknownPlain = collect([{ name: 'Mystery Blade', copyIx: 0, sight: { location: 'stash', cell: 'stash:c2r2' } }]);
assign['Zzyzx Blade of Nothing'] = '__throwout';
window._seam = { loc: 'loose' };
var fromRuled = collect([{ name: 'Zzyzx Blade of Nothing', copyIx: 0, sight: { location: 'stash', cell: 'stash:c1r1' } }]);
window._seam = null;
var fromStash = collect([{ name: 'Thresher', copyIx: 0, sight: { location: 'stash', cell: 'stash:c7r1', witnesses: 1 } }]);
var fromShared = collect([{ name: 'Treachery', copyIx: 0, sight: { location: 'shared', cell: 'shared:c3r4', witnesses: 1 } }]);
window._ensFrom = 'inventory';
/* #230 review: the sight may carry its LIST of looks; one real session in it is one look */
window._ensFrom = 'stash';
var listLook = collect([{ name: 'Thresher', copyIx: 0, sight: { location: 'stash', cell: 'stash:c7r1', witnesses: [
  { session: 's_1791356557071_58418', frame: 'f_1791358157119.jpg', conf: 0.85, cell: 'stash:c7r1' }] } }]);
var listNoSession = collect([{ name: 'Thresher', copyIx: 0, sight: { location: 'stash', cell: 'stash:c7r1', witnesses: [
  { frame: 'f_1791358157119.jpg', conf: 0.85, cell: 'stash:c7r1' }] } }]);
/* #230 v3806: a cell with no session behind it (witnesses null) is zero looks and opens no move */
window._ensFrom = 'inventory';
var zeroLook = collect([{ name: 'Thresher', copyIx: 0, sight: { location: 'stash', cell: 'stash:c7r1', witnesses: null } }]);
var storedInv = collect([{ name: 'Thresher', copyIx: 0, sight: { location: '', cell: null } }]);
function names(pack){ return (pack.tasks || []).map(function(r){ return r.name; }); }
console.log(JSON.stringify({
  invThrow: invThrow, equipped: equipped, invFilled: invFilled, unknown: unknown, ruledOff: ruledOff, ruled: ruled,
  stash: stash, shared: shared,
  fromInv: names(fromInv), fromEquip: names(fromEquip),
  fromUnknown: names(fromUnknown), fromUnknownPlain: names(fromUnknownPlain),
  fromRuled: names(fromRuled), fromStash: names(fromStash), fromShared: names(fromShared),
  storedInv: names(storedInv), zeroLook: names(zeroLook), listLook: names(listLook), listNoSession: names(listNoSession),
  committedUnknown: fromUnknownPlain.committed || []
}));
""",
        ])
        o = self._run(prog)
        self.assertFalse(o["invThrow"])
        self.assertFalse(o["equipped"])
        self.assertFalse(o["invFilled"])
        self.assertFalse(o["unknown"])
        self.assertFalse(o["ruledOff"])
        self.assertTrue(o["ruled"])
        self.assertTrue(o["stash"])
        self.assertTrue(o["shared"])
        self.assertEqual(o["fromInv"], [])
        self.assertEqual(o["fromEquip"], [])
        self.assertEqual(o["fromUnknown"], [])
        self.assertEqual(o["fromUnknownPlain"], [])
        self.assertEqual(o["fromRuled"], ["Zzyzx Blade of Nothing"])
        self.assertEqual(o["fromStash"], ["Thresher"])
        self.assertEqual(o["fromShared"], ["Treachery"])
        self.assertEqual(o["storedInv"], [])
        self.assertEqual(o["zeroLook"], [])
        self.assertEqual(o["listLook"], ["Thresher"])
        self.assertEqual(o["listNoSession"], [])
        self.assertEqual(o["committedUnknown"], [])


    def test_the_intake_owned_stamp_never_throws_on_a_bad_prov_row(self):
        prog = "\n".join([_fn(self.src, "_vaultIntakeOwned"), _fn(self.src, "_vaultSightLooks"), r"""
var boom = {}; Object.defineProperty(boom, 'ownedBy', { get: function(){ throw new Error('bad row'); } });
var S = { by: 'tvVaultRegister', kind: 'owned' };
console.log(JSON.stringify({
  direct: _vaultIntakeOwned(S), filed: _vaultIntakeOwned({ mule: 'bases', ownedBy: S }),
  boom: _vaultIntakeOwned(boom), str: _vaultIntakeOwned({ ownedBy: 'owned' }), arr: _vaultIntakeOwned({ ownedBy: [S] }),
  nul: _vaultIntakeOwned(null), hand: _vaultIntakeOwned({ kind: 'owned', by: 'hand' }),
  n2: _vaultSightLooks({ witnesses: 2 }), nNull: _vaultSightLooks({ witnesses: null }),
  lst: _vaultSightLooks({ witnesses: [
    { session: 's_1', frame: 'f_1.jpg', conf: 0.9 }, { session: 's_1', frame: 'f_2.jpg', conf: 0.9 },
    { session: 's_2', frame: 'f_3.jpg', conf: 0.4 }, { session: 's_3', frame: null, conf: 0.9 }, { session: 's_4', frame: 'f_4.jpg', conf: 0.7 }] })
}));
"""])
        o = self._run(prog)
        self.assertEqual(o, {"direct": True, "filed": True, "boom": False, "str": False, "arr": False,
                             "nul": False, "hand": False, "n2": 2, "nNull": 0, "lst": 2})


RED_PROOF = [
    {"why": "An auto sighting with no from-cell is marked moved elsewhere again.",
     "file": "bible.html",
     "find": "if ((t.from == null || t.from.cell == null) && !t.manual) { /* auto intake from */",
     "replace": "if (false && (t.from == null || t.from.cell == null) && !t.manual) { /* auto intake from */",
     "matches": 1},
    {"why": "The move reader ignores lane, so a reel sighting has no place.",
     "file": "bible.html",
     "find": "sighting.location || sighting.loc || sighting.lane",
     "replace": "sighting.location || sighting.loc",
     "matches": 2},
    {"why": "A shared-stash sighting is refused as not a container.",
     "file": "bible.html",
     "find": "  var _WIT_STASH = { stash: 1, mule: 1, locker: 1, tomb: 1, tombs: 1, shared: 1, 'shared stash': 1 };",
     "replace": "  var _WIT_STASH = { stash: 1, mule: 1, locker: 1, tomb: 1, tombs: 1 };",
     "matches": 1},
    {"why": "A frame is not recorded as a look, so two sessions still say zero looks.",
     "file": "bible.html",
     "find": "if (!_byHand && _witIn && typeof window._vaultIntakeLook === 'function') _witIn = window._vaultIntakeLook(_witIn); /* auto intake look */",
     "replace": "/* auto intake look */",
     "matches": 1},
    {"why": "The live read's score is copied onto every item, so two sessions count as zero looks.",
     "file": "bible.html",
     "find": "    var one = { conf: null };",
     "replace": "    var one = { conf: rd.conf };",
     "matches": 1},
    {"why": "Inventory and equipped gear still get a move row.",
     "file": "bible.html",
     "find": "    if (_vaultMoveMainLane(t.from && t.from.location)) return false; /* inventory and equipped stay locked */",
     "replace": "    if (false && _vaultMoveMainLane(t.from && t.from.location)) return false; /* inventory and equipped stay locked */",
     "matches": 1},
    {"why": "An unknown name with no home still gets a move row.",
     "file": "bible.html",
     "find": "        if (!_ruledJunk) return; /* main lane or no home: no move row */",
     "replace": "        if (false && !_ruledJunk) return; /* main lane or no home: no move row */",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
