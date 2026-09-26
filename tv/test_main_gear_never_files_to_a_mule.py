# -*- coding: utf-8 -*-
"""#246 L10 — WHAT HIS MAIN CARRIES IS NEVER FILED TO A MULE. One lock, joined from every source that knows it.

His words: the vault should keep "locking the items ... and the character name... so the MAIN character", and in
capitals, from PROJECT_VAULT_MANAGER.md: "inventory and main character equiment (SHOULD NEVER BE TOLD TO BE MOVED
its locked there)".

THE DEFECT: three sources each knew part of the lock and none reached the writer that files —
d2r_laneLock (vault_retro equipment/inventory rows, fed only by the sweep and ABSENT on his board), the furniture
law (tv/inventory_law.py — the board never consulted it), and the MAIN ledger (tv/main_character.py, a Wilson
ledger of what he wears — bible.html read it ZERO times). And the furniture law itself locked BLACKHAND KEY, a
unique wand filed to his UNI-WEAPONS mule, because "key" was a word-boundary match.

WHAT THIS LAW HOLDS, driven on the SHIPPED lock block and the SHIPPED door, cut from bible.html and run in node:
  · ONE PREDICATE, THREE SOURCES: a d2r_laneLock row with his 3 separate sessions locks (2 only WATCHES — his
    v1985 ruling); furniture locks by law (the Horadric Cube, a tome, the game's Key) while Blackhand Key does
    not; a row the console's MAIN ledger publishes locks, and a board name with a "(slot)" suffix matches it.
  · window.vaultFile REFUSES every locked name — a stash witness and his own hand alike (the panel offers the
    release) — and files Blackhand Key.
  · NOBODY ASKED IS NOT "NOTHING LOCKED": MAIN_LOCKS stays null until the console answers, a refusal leaves it
    null, and the other two sources still hold without it.
  · THE MAIN'S NAME is set only by his declaration or a .d2s he says is his: the tag reads "MAIN (name UNKNOWN)"
    until then; a .d2s is refused without his word (a planner export reads exactly like a save — the
    .d2s on his Desktop is a maxroll export); a name the game would not allow is refused.
  · THE PANEL SHOWS IT: a locked name still sitting in a mule is listed "filed in <mule>" beside the MAIN's tag.
  · A READER NEVER FILES A CONSUMABLE (measured on a copy of his store: a register filed two potions to
    UNI-WEAPONS); his own hand still may.
  · THE FURNITURE LIST IS ONE LIST: the board's words equal inventory_law.LOCKED / LOCKED_WHOLE /
    CONSUMABLE_WORDS, and the Python law answers Blackhand Key the same way the board does.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

NODE = shutil.which("node")
BIBLE = os.path.join(ROOT, "bible.html")
LOCK_FROM = "var _LANE_LOCK_KEY = 'd2r_laneLock';"
LOCK_TO = "window._laneLockSetWhere = function(name, where){"


def _src():
    with io.open(BIBLE, encoding="utf-8") as f:
        return f.read()


def _lock_block(s):
    assert s.count(LOCK_FROM) == 1 and s.count(LOCK_TO) == 1, "the lock block is not where this law cuts it"
    i = s.index(LOCK_FROM)
    return s[i:s.index(LOCK_TO, i)]


def _pieces(s):
    from test_every_mule_filing_carries_its_witness import _door, _say_line
    return _say_line(s) + _lock_block(s) + _door(s)


HARNESS = r"""
var window = globalThis, STORE = {};
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(STORE, k) ? STORE[k] : null; },
               setItem: function(k, v){ STORE[k] = String(v); }, removeItem: function(k){ delete STORE[k]; } };
window.D2R_BUILD = { id: 'vLAW' };
window.location = { host: '' };
window.addEventListener = function(){};
var EL = { hidden: true, innerHTML: '' };
var document = { getElementById: function(id){ return id === 'vault-lane-locks' ? EL : null; }, hidden: false };
window.document = document;
var assign = {}, owned = new Set();
function saveA(){ window.LSR.setItem('d2r_muleAssign', JSON.stringify(assign)); }
function persistOwned(){}
var ROSTER = { 'uni-armor': { id: 'uni-armor', name: 'UNI-ARMOR' }, 'uni-weap': { id: 'uni-weap', name: 'UNI-WEAPONS' } };
function muleById(id){ return ROSTER[id] || null; }
function suggestMule(n){ return { id: /Key|Rider/.test(n) ? (/Key/.test(n) ? 'uni-weap' : 'uni-armor') : 'uni-armor', why: 'law' }; }
function isSharedStash(n){ return false; }
function ownedPool(){ return Array.from(owned); }
"""

BODY = r"""
var OUT = {};
var L2 = [{ session: 's_a', frame: 'f_a.jpg', conf: 0.9 }, { session: 's_b', frame: 'f_b.jpg', conf: 0.85 }];
var HAND = { by: 'hand', at: '2026-09-26T00:00:00Z', where: 'the vault manager' };
function lk(n){ return window._laneLocked(n); }
OUT.mainBefore = window.MAIN_LOCKS;
OUT.furn = { cube: lk('Horadric Cube'), tome: lk('Tome of Town Portal'), key: lk('Key'), keys: lk('12 Keys'),
             bhk: lk('Blackhand Key'), sword: lk('Crystal Sword') };
window.LSR.setItem('d2r_laneLock', JSON.stringify({
  'War Traveler': { lane: 'equipment', sessions: ['s1', 's2', 's3'] },
  'Dwarf Star':   { lane: 'inventory', sessions: ['s1', 's2'] } }));
OUT.lane = { three: lk('War Traveler'), two: lk('Dwarf Star') };
OUT.grBefore = lk('Gore Rider');
OUT.refusedApply = window._mainLocksApply({ ok: false, why: 'unreadable', locked: null });
OUT.mainAfterRefusal = window.MAIN_LOCKS;
OUT.applied = window._mainLocksApply({ ok: true, locked: [{ name: 'Gore Rider', why: 'his gear — seen on his character 3 of 3 times', wilson: 0.438 }] });
OUT.gr = { bare: lk('Gore Rider'), suffixed: lk('Gore Rider (boots)'), why: (window._laneLockWhy('Gore Rider') || {}).source };
OUT.file = {
  cube: window.vaultFile('Horadric Cube', { lane: 'stash', sessions: L2 }),
  gr: window.vaultFile('Gore Rider', { lane: 'stash', sessions: L2 }),
  grHand: window.vaultFile('Gore Rider', HAND, { mule: 'uni-armor' }),
  wt: window.vaultFile('War Traveler', HAND, { mule: 'uni-armor' }),
  ds: window.vaultFile('Dwarf Star', { lane: 'stash', sessions: L2 }),
  bhk: window.vaultFile('Blackhand Key', { lane: 'stash', sessions: L2 }),
  potion: window.vaultFile('Super Mana Potion', { lane: 'stash', sessions: L2 }),
  potionHand: window.vaultFile('Full Rejuvenation Potion', HAND, { mule: 'uni-armor' })
};
OUT.cons = { tome: window._consumable('Tome of Town Portal'), scroll: window._consumable('Scroll of Town Portal'),
             gold: window._consumable('1,240 Gold'), ring: window._consumable('Nagelring') };
OUT.consWords = window._CONSUMABLE_WORDS;
OUT.map = JSON.parse(JSON.stringify(assign));
OUT.tag0 = window._mainTag();
OUT.badName = window.mainCharacterDeclare({ name: 'no spaces allowed' });
OUT.d2sNotHis = window.mainCharacterFromD2s({ ok: true, verify: { checksumOk: true }, header: { name: 'Export', className: 'Druid', level: 85 }, path: '/x/Export.d2s' });
OUT.declared = window.mainCharacterDeclare({ name: 'Testhero', level: 85, cls: 'Druid' });
OUT.tag1 = window._mainTag();
OUT.store = JSON.parse(window.LSR.getItem('d2r_mainCharacter') || 'null');
OUT.d2sHis = window.mainCharacterFromD2s({ ok: true, verify: { checksumOk: true }, header: { name: 'Savedhero', className: 'Sorceress', level: 90 }, path: '/x/Savedhero.d2s' }, { his: true });
OUT.store2 = JSON.parse(window.LSR.getItem('d2r_mainCharacter') || 'null');
assign['Gore Rider'] = 'uni-armor';
window.renderLaneLocks();
OUT.panel = { hidden: EL.hidden, html: EL.innerHTML };
OUT.words = window._FURNITURE_WORDS; OUT.whole = window._FURNITURE_WHOLE;
process.stdout.write(JSON.stringify(OUT));
"""


def _drive():
    prog = HARNESS + _pieces(_src()) + BODY
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise AssertionError("the shipped lock would not execute — UNKNOWN, not passing: %s" % (r.stderr or r.stdout)[-800:])
    return json.loads(r.stdout)


@unittest.skipIf(NODE is None, "node is absent — this law runs the SHIPPED lock; UNMEASURED, not passing")
class MainGearNeverFilesToAMule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = _drive()

    def test_furniture_locks_by_law_and_blackhand_key_does_not(self):
        f = self.o["furn"]
        for k in ("cube", "tome", "key", "keys"):
            self.assertEqual("inventory", f[k], "furniture %s is not locked: %r" % (k, f))
        self.assertEqual("", f["bhk"], "Blackhand Key — a unique wand — is locked as a key again")
        self.assertEqual("", f["sword"])

    def test_his_three_session_bar_holds_for_the_lane_lock(self):
        self.assertEqual("equipment", self.o["lane"]["three"])
        self.assertEqual("", self.o["lane"]["two"], "two sessions LOCKED — he overruled the eager lock (v1985)")

    def test_the_main_ledger_joins_and_nobody_asked_is_not_nothing_locked(self):
        self.assertIsNone(self.o["mainBefore"], "MAIN_LOCKS claims an answer nobody gave")
        self.assertEqual("", self.o["grBefore"])
        self.assertFalse(self.o["refusedApply"])
        self.assertIsNone(self.o["mainAfterRefusal"], "a refused read was stored as an (empty) answer")
        self.assertTrue(self.o["applied"])
        self.assertEqual("equipment", self.o["gr"]["bare"], "a MAIN-ledger lock does not reach the board's predicate")
        self.assertEqual("equipment", self.o["gr"]["suffixed"], "the board's slot-suffixed name escapes the lock")
        self.assertEqual("main-ledger", self.o["gr"]["why"])

    def test_the_door_refuses_every_locked_name_and_files_the_rest(self):
        fl = self.o["file"]
        for k in ("cube", "gr", "grHand", "wt"):
            self.assertFalse(fl[k]["ok"], "%s was filed although locked to the MAIN: %r" % (k, fl[k]))
            self.assertEqual("locked", fl[k]["refused"], fl[k])
        self.assertTrue(fl["ds"]["ok"], "a WATCHED (2-session) name was refused as locked: %r" % fl["ds"])
        self.assertTrue(fl["bhk"]["ok"], "Blackhand Key could not be filed: %r" % fl["bhk"])
        self.assertEqual("uni-weap", self.o["map"].get("Blackhand Key"))
        for k in ("Horadric Cube", "Gore Rider", "War Traveler"):
            self.assertNotIn(k, self.o["map"], "%s reached a mule" % k)

    def test_a_reader_never_files_a_consumable_and_his_hand_still_may(self):
        """MEASURED on a copy of his store: a register of his real stash rows filed a Full Rejuvenation Potion
        and a Super Mana Potion to UNI-WEAPONS. His ruling: consumables are used or thrown out, never worth a
        register. The door refuses them from a reader; a filing by his own hand stands."""
        fl = self.o["file"]
        self.assertFalse(fl["potion"]["ok"], "a reader filed a potion to a mule: %r" % fl["potion"])
        self.assertEqual("consumable", fl["potion"]["refused"])
        self.assertTrue(fl["potionHand"]["ok"], "his own hand was refused a potion: %r" % fl["potionHand"])
        c = self.o["cons"]
        self.assertEqual((False, True, True, False), (c["tome"], c["scroll"], c["gold"], c["ring"]),
                         "the consumable rule answers differently from inventory_law: %r" % c)

    def test_the_mains_name_comes_only_from_him(self):
        self.assertEqual("MAIN (name UNKNOWN)", self.o["tag0"])
        self.assertFalse(self.o["badName"]["ok"], "a name the game would not allow was stored")
        self.assertFalse(self.o["d2sNotHis"]["ok"], "a .d2s was taken as the MAIN without his word")
        self.assertIn("planner export", self.o["d2sNotHis"]["why"])
        self.assertTrue(self.o["declared"]["ok"])
        self.assertEqual("MAIN · Testhero · L85 Druid", self.o["tag1"])
        self.assertEqual("declared", self.o["store"]["source"])
        self.assertTrue(self.o["d2sHis"]["ok"], self.o["d2sHis"])
        self.assertEqual(("Savedhero", "d2s", "Savedhero.d2s"),
                         (self.o["store2"]["name"], self.o["store2"]["source"], self.o["store2"]["file"]))

    def test_the_panel_shows_a_main_item_sitting_in_a_mule(self):
        p = self.o["panel"]
        self.assertFalse(p["hidden"], "the lock panel stayed hidden with a MAIN item in a mule")
        self.assertIn("filed in UNI-ARMOR", p["html"], "the MAIN item in a mule is not called out")
        self.assertIn("MAIN · Savedhero", p["html"], "the panel does not carry the MAIN's tag")

    def test_the_furniture_list_is_one_list(self):
        import inventory_law as IL
        self.assertEqual(list(IL.LOCKED), self.o["words"], "the board's furniture words drifted from inventory_law")
        self.assertEqual(list(IL.LOCKED_WHOLE), self.o["whole"], "the whole-name words drifted from inventory_law")
        self.assertEqual(list(IL.CONSUMABLE_WORDS), self.o["consWords"], "the consumable words drifted from inventory_law")
        self.assertFalse(IL.is_locked("Blackhand Key"), "inventory_law locks Blackhand Key as a key again")
        self.assertTrue(IL.is_locked("Key") and IL.is_locked("12 Keys"))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#246 W4 - the door files a name locked to his MAIN",
        "file": "bible.html",
        "find": "    if (lk) return { ok: false, refused: 'locked', lock: lk,\n      why: nm + ' is locked to your MAIN (' + lk + ') — ' + ((window._mainTag",
        "replace": "    if (false) return { ok: false, refused: 'locked', lock: lk,\n      why: nm + ' is locked to your MAIN (' + lk + ') — ' + ((window._mainTag",
        "matches": 1,
    },
    {
        "why": "#246 W4 - the MAIN ledger the console publishes is not joined to the lock",
        "file": "bible.html",
        "find": "  var ml = window._mainLockOf(nm);\n",
        "replace": "  var ml = null;\n",
        "matches": 1,
    },
    {
        "why": "#246 W4 - a reader files a consumable to a mule again (two potions landed in UNI-WEAPONS on his data)",
        "file": "bible.html",
        "find": "    if (wc.kind !== 'hand' && window._consumable && window._consumable(nm))\n",
        "replace": "    if (false && window._consumable && window._consumable(nm))\n",
        "matches": 1,
    },
    {
        "why": "#246 W4 - the furniture law locks Blackhand Key as a 'key' again",
        "file": "inventory_law.py",
        "find": "    \"wirts leg\",\n)",
        "replace": "    \"wirts leg\",\n    \"key\",\n)",
        "matches": 1,
    },
]
