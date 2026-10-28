# -*- coding: utf-8 -*-
"""#145 (GrokBot ACT-A traps 7/8/12) - A WIPE, A RESET, A RECORDS CLEAR AND A HAND ADD CAN BE UNDONE, ONCE.

GrokBot's trap run: a mistaken Wipe items, Reset assignments or Reset vault had NO way back, and neither did a hand add
by mistake. Each door now snapshots the vault, stashes and characters (_vaultProfileBuild, the Save-profile file's own
text) in the page's memory after its confirm and before it changes anything; the ↶ chip names what it undoes and loads
the snapshot back through vaultProfileLoad (every store listed, Cancel-first, put back on a refused write, reload).
Memory only and one step - the conventional default for "memory or saved", and the profile file stays the durable copy.

THIS LAW cuts the SHIPPED doors, scope and profile/undo block from bible.html and drives them in node on the seeded
store of test_a_vault_reset_clears_only_the_mules (one copy of that harness, imported): a real wipe, then a real undo,
must leave every profile store byte-identical to before the wipe. A cancelled wipe leaves no undo; a refused undo is
kept; a snapshot that cannot be read gives no undo and the reset line says so; every reset door and the add-by-name
door record one. RED_PROOF below. [[unknown-stays-unknown]] [[the-unjoined-end]]
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except ImportError:
    _enable = None
import test_a_vault_reset_clears_only_the_mules as base  # noqa: E402

DOOR_WIPE = "  window.vaultWipeItems = async function(){\n"
DOOR_RECORDS = "  window.vaultClearRecords = async function(){\n"
DOOR_TAKE = "  window.vaultHandTake = function(id){\n"
PROFILE_FROM = "  var _PROFILE_KIND = 'd2r-vault-profile', _PROFILE_VERSION = 1;\n"
PROFILE_TO = "  /* Vault v3 — the locks chip reads the collapsed lock rows."

CHIPS = r"""
var CHIP = { hidden: true, title: '' }, CHIPW = { textContent: '' }, SAY = { textContent: '', attrs: {},
             setAttribute: function(k, v){ this.attrs[k] = v; } };
document.getElementById = function(id){
  return id === 'vault-intake-report' ? REPORT : id === 'vault-chip-undo' ? CHIP : id === 'vault-chip-undo-what' ? CHIPW
       : id === 'vault-hand-say' ? SAY : null; };
var _VH_KIND = {};
"""

BODY = base.BODY.split("(async function(){")[0] + r"""
function last(){ return STATUS.length ? STATUS[STATUS.length - 1] : null; }
function copyStore(){ return JSON.parse(JSON.stringify(STORE)); }
(async function(){
  var OUT = {};
  window._vaultPlanFromEvidence = async function(){ return { ok: true, rebuilt: [], held: [] }; };
  seed(); ANSWER = false; window._vaultUndo = null;
  await window.vaultWipeItems();
  OUT.cancel = { undo: !!window._vaultUndo, chipHidden: CHIP.hidden };
  seed(); ANSWER = true; window._vaultUndo = null;
  var before = copyStore();
  await window.vaultWipeItems();
  var afterWipe = copyStore();
  OUT.wipe = { what: window._vaultUndo && window._vaultUndo.what, note: window._vaultUndo && window._vaultUndo.note,
               chipHidden: CHIP.hidden, chipWhat: CHIPW.textContent, chipTitle: CHIP.title, status: last(),
               emptied: ['d2r_owned', 'd2r_muleAssign', 'd2r_magicFinds', 'd2r_copies'].filter(function(k){ return afterWipe[k] !== before[k]; }) };
  var LEADS = [];
  var r1 = await window.vaultUndoLast({ confirm: function(m){ LEADS.push(m); return false; }, noReload: true });
  OUT.refused = { ok: r1 && r1.ok, kept: !!window._vaultUndo, untouched: JSON.stringify(STORE) === JSON.stringify(afterWipe) };
  var r2 = await window.vaultUndoLast({ confirm: function(m){ LEADS.push(m); return true; }, noReload: true });
  var keys = []; Object.keys(window._PROFILE_STORES).forEach(function(g){ keys = keys.concat(window._PROFILE_STORES[g]); });
  function at(o, k){ return Object.prototype.hasOwnProperty.call(o, k) ? o[k] : null; }
  OUT.undo = { ok: r2 && r2.ok, wrote: r2 && r2.wrote, spent: !window._vaultUndo, chipHidden: CHIP.hidden, lead: LEADS[0] || '',
               differ: keys.filter(function(k){ return at(STORE, k) !== at(before, k); }) };
  var r3 = await window.vaultUndoLast({ noReload: true });
  OUT.nothing = { ok: r3 && r3.ok, status: last() };
  seed(); ANSWER = true; window._vaultUndo = null;
  var _pb = window._vaultProfileBuild; window._vaultProfileBuild = function(){ throw new Error('a store would not read'); };
  await window.vaultWipeItems();
  window._vaultProfileBuild = _pb;
  OUT.nosnap = { undo: !!window._vaultUndo, chipHidden: CHIP.hidden, status: last() };
  OUT.doors = {};
  var doors = [['vaultReset', 'Reset assignments'], ['vaultClearHistory', 'Reset vault'], ['vaultClearRecords', 'Clear records history']];
  for (var i = 0; i < doors.length; i++){
    seed(); ANSWER = true; window._vaultUndo = null;
    await window[doors[i][0]]();
    OUT.doors[doors[i][0]] = { what: window._vaultUndo && window._vaultUndo.what, status: last() };
  }
  var ADDS = [];
  window._vhCat = { ok: true, rows: [{ id: 'r1', name: 'Harlequin Crest', q: 'unique' }, { id: 'r2', name: 'Shako', q: 'unique' }] };
  window.vaultHandSearch = function(){};
  window.vaultHandAdd = function(name){ ADDS.push(name);
    return name === 'Harlequin Crest' ? { ok: true, mode: 'added', name: name, why: name + ' added' }
                                      : { ok: true, mode: 'already', name: name, why: name + ' is already yours' }; };
  seed(); window._vaultUndo = null;
  window.vaultHandTake('r2');
  OUT.addAlready = { undo: !!window._vaultUndo, say: SAY.textContent };
  window.vaultHandTake('r1');
  OUT.addNew = { what: window._vaultUndo && window._vaultUndo.what, hasText: !!(window._vaultUndo && window._vaultUndo.text),
                 say: SAY.textContent, adds: ADDS };
  process.stdout.write(JSON.stringify(OUT));
})().catch(function(e){ process.stderr.write(String((e && e.stack) || e)); process.exit(3); });
"""


def _drive(src=None):
    s = src if src is not None else base._src()
    prog = (base.HARNESS + CHIPS + base._pieces(s) + base._door(s, DOOR_WIPE) + base._door(s, DOOR_RECORDS)
            + base._door(s, DOOR_TAKE) + base._between(s, PROFILE_FROM, PROFILE_TO) + BODY)
    r = subprocess.run([base.NODE, "-"], input=prog, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise AssertionError("the shipped doors would not execute - UNKNOWN, not passing: %s" % (r.stderr or r.stdout)[-900:])
    return json.loads(r.stdout)


@unittest.skipIf(base.NODE is None, "node is not on this machine - UNMEASURED here, not passing")
class AVaultChangeCanBeUndone(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = _drive()

    def test_a_cancelled_wipe_leaves_no_undo(self):
        self.assertEqual(self.o["cancel"], {"undo": False, "chipHidden": True}, self.o["cancel"])

    def test_a_wipe_offers_its_undo_on_the_chip_and_says_so(self):
        w = self.o["wipe"]
        self.assertEqual(sorted(w["emptied"]), ["d2r_copies", "d2r_magicFinds", "d2r_muleAssign", "d2r_owned"],
                         "PREMISE: the wipe emptied the item stores: %s" % w)
        self.assertEqual((w["what"], w["chipHidden"], w["chipWhat"]), ("Wipe items", False, "Wipe items"), w)
        self.assertIn("link it again", w["note"], "the wipe's undo does not say the folder link is not part of it")
        self.assertIn("Only the newest change can be undone", w["chipTitle"])
        self.assertIn("↶ Undo is in the toolbar", w["status"], "the reset line does not say where the undo is")

    def test_a_refused_undo_changes_nothing_and_keeps_the_undo(self):
        self.assertEqual(self.o["refused"], {"ok": False, "kept": True, "untouched": True}, self.o["refused"])

    def test_an_undo_puts_every_profile_store_back_byte_identical(self):
        u = self.o["undo"]
        self.assertTrue(u["ok"] and u["wrote"], "the undo did not load: %s" % u)
        self.assertEqual(u["differ"], [], "after the undo these stores still differ from before the wipe: %s" % u["differ"])
        self.assertTrue(u["spent"] and u["chipHidden"], "a loaded undo is still offered: %s" % u)
        self.assertTrue(u["lead"].startswith("Undo Wipe items?"), "the confirm does not say what it undoes: %r" % u["lead"][:80])

    def test_nothing_to_undo_is_said(self):
        self.assertEqual(self.o["nothing"]["ok"], False)
        self.assertIn("Nothing to undo", self.o["nothing"]["status"])

    def test_an_unreadable_snapshot_gives_no_undo_and_says_so(self):
        n = self.o["nosnap"]
        self.assertEqual((n["undo"], n["chipHidden"]), (False, True), "an undo was offered over nothing: %s" % n)
        self.assertIn("no undo: the stores could not be read", n["status"])

    def test_every_reset_door_records_its_undo(self):
        want = {"vaultReset": "Reset assignments", "vaultClearHistory": "Reset vault",
                "vaultClearRecords": "Clear records history"}
        for door, what in want.items():
            self.assertEqual(self.o["doors"][door]["what"], what, "%s records no undo: %s" % (door, self.o["doors"][door]))
            self.assertIn("↶ Undo is in the toolbar", self.o["doors"][door]["status"] or "", door)

    def test_a_hand_add_that_added_records_its_undo_and_one_that_did_not_does_not(self):
        self.assertEqual(self.o["addAlready"]["undo"], False, "an add that changed nothing offered an undo")
        a = self.o["addNew"]
        self.assertEqual((a["what"], a["hasText"]), ("the add of Harlequin Crest", True), a)
        self.assertIn("↶ Undo is in the toolbar", a["say"], "the add-by-name door does not say where the undo is")

    def test_the_chip_is_in_the_toolbar(self):
        s = base._src()
        chip = ('<button type="button" class="vault-chip" id="vault-chip-undo" data-state="undo" hidden '
                'onclick="window.vaultUndoLast()">↶ Undo <span id="vault-chip-undo-what"></span></button>')
        self.assertEqual(s.count(chip), 1, "the undo chip is not on the page (or not once)")
        i = s.index('<div class="vault-tb-grp vault-tb-chips">')
        self.assertTrue(i < s.index(chip) < s.index("</div>", i), "the undo chip is not in the toolbar's chip group")


RED_PROOF = [
    {"why": "#145 - a snapshot that could not be read still offers an undo (over nothing)",
     "file": "bible.html",
     "find": "    window._vaultUndo = t ? { what: String(what || 'the last change')",
     "replace": "    window._vaultUndo = true ? { what: String(what || 'the last change')",
     "matches": 1, "needs": "node"},
    {"why": "#145 - an undo he refused is spent anyway",
     "file": "bible.html",
     "find": "    if (r && r.ok && r.wrote){ window._vaultUndo = null; window._vaultUndoPaint(); }\n",
     "replace": "    window._vaultUndo = null; window._vaultUndoPaint();\n",
     "matches": 1, "needs": "node"},
    {"why": "#145 - the undo's confirm reads 'Load this profile', not what it undoes",
     "file": "bible.html",
     "find": "Object.assign({ lead: 'Undo ' + u.what }, opts || {})",
     "replace": "Object.assign({}, opts || {})",
     "matches": 1, "needs": "node"},
    {"why": "#145 - Wipe items takes no snapshot: a mistaken wipe has no way back",
     "file": "bible.html",
     "find": "    var _undoOk = window._vaultUndoTry ? window._vaultUndoTry('Wipe items',",
     "replace": "    var _undoOk = false ? window._vaultUndoTry('Wipe items',",
     "matches": 1, "needs": "node"},
    {"why": "#145 - Reset assignments takes no snapshot",
     "file": "bible.html",
     "find": "    var _undoOk = window._vaultUndoTry ? window._vaultUndoTry('Reset assignments') : null;",
     "replace": "    var _undoOk = null;",
     "matches": 1, "needs": "node"},
    {"why": "#145 - a hand add that changed nothing offers an undo",
     "file": "bible.html",
     "find": "    var _undoHas = !!(res && res.ok && (res.mode === 'added' || res.mode === 'copy') && _undoText\n",
     "replace": "    var _undoHas = !!(res && res.ok && _undoText\n",
     "matches": 1, "needs": "node"},
    {"why": "#145 - a cancelled wipe leaves an undo (the snapshot is taken before the confirm)",
     "file": "bible.html",
     "find": "  window.vaultWipeItems = async function(){\n    if (!(await uiConfirm(",
     "replace": "  window.vaultWipeItems = async function(){\n    if (window._vaultUndoTry) window._vaultUndoTry('Wipe items');\n    if (!(await uiConfirm(",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
