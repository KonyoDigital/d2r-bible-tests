# -*- coding: utf-8 -*-
"""REG-2521 (V1 round 3; the review of REG-2411, rv2) - WHILE THE VAULT IS HELD, EVERY DOOR THAT WOULD WRITE IT REFUSES IN
WORDS, AND NO DOOR THAT REFUSES IS WALKED AROUND.

Round 2 measured the hold refusing at two doors (+ Add an item, frame reads) while every other door answered ok over a
write the store door refused:
  * vaultFile asked only about the witness store: with d2r_copies, the roster or owned quarantined a move answered
    {ok, mode:'moved'} and a reader filing {ok, mode:'filed'} - the witness row was written, saveA() was refused, and the
    row said uni-armor while the saved map still said uni-weap;
  * vaultAutoAssign / Auto-Sort put "⚖️ filed 1 witnessed item" on the status line and the map did not change;
  * tvVaultRegister skipped the gate for a hand witness, so the Chronicle inbox's "Vault only" (kaiVaultFileOnly) was
    answered {ok, vault:'filed'} and DELETED HIS INBOX ROW while nothing about the item was saved - after a reload it was
    in no store, and the row he had to rule on was gone;
  * the removal door read a journal that would not read as [] (REG-2520), and toggleOwned / Delete unsorted / the TV
    unvault fell back to `owned.delete` whenever vaultRemove "took nothing" - a refusal looked exactly like that.

NOW the hold is asked at the one door: vaultFile's top check refuses on _vaultBasisHeld() (Magic & Rare joined the basis),
a refused saveA() is never answered ok, the sorter asks before it sorts, tvVaultRegister refuses for every witness (his
hand included) while any vault store is held, the removal door and its undo wait while a store they write is UNKNOWN or
held (window._vaultRemovalHeld) - and every caller keeps what it holds and says the refusal.

WHAT IS DRIVEN (store_door_harness.vault_page: the store door, the boot, the tab sync, the vault module's head and its
whole filing block), plus, cut whole from bible.html: the removal journal, vaultRemove and vaultRestoreLast, the sorter,
the register and its frame-gate wrapper, the shipped persistOwned and the Chronicle inbox's kaiVaultFileOnly; and
toggleOwned with the journal and the removal door. In node. RED_PROOF below. A missing node is the only skip.
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
except Exception:
    pass

import store_door_harness as D  # noqa: E402

PROV = json.dumps({"Grief": {"mule": "uni-weap", "holder": "UNI-WEAPONS", "source": "hand", "by": "hand", "at": "2026-10-01",
                             "where": "the vault manager", "sessions": [], "looks": []}})
INBOX = json.dumps([{"name": "Arachnid Mesh", "at": "2026-10-22T09:00:00Z", "kind": "vault"}])
L2 = "[{session:'s_a',frame:'f_a.jpg',conf:0.9},{session:'s_b',frame:'f_b.jpg',conf:0.85}]"
JOURNAL_CUT = ('[{"ts":1760000000000,"lane":"hand","names":["Shako"],"filed":{"Shako":"uni-armor"}},'
               '{"ts":1760000100000,"lane":"hand","names":["Enigma"],"filed":{"Enigma":"uni-armor"},"prov')
#: a store the vault stands on, made unreadable the ways GrokBot's sweep and the review wrote them
HELD = {
    "d2r_copies": '{"Grief":2',
    "d2r_muleRoster": "{}",
    "d2r_owned": '{"a":1}',
    "d2r_magicFinds": '{"Death Loop":{"q":"rare"',
    "d2r_muleAssign": '{"Grief":"uni-weap"',
}


def _seed(**more):
    out = {"d2r_owned": '["Grief","Enigma","Harlequin Crest (Shako)"]', "d2r_muleAssign": '{"Grief":"uni-weap"}',
           "d2r_vaultProv": PROV, "d2r_chronicleInbox": INBOX}
    out.update(more)
    return out


def _door(s, head):
    if s.count(head) != 1:
        raise AssertionError("%r matched %d times - re-point this law" % (head[:60], s.count(head)))
    i = s.index(head)
    return s[i:s.index("\n  };\n", i) + len("\n  };\n")]


def _pieces(s):
    wa = s.index("  (function(){\n    var _inner = window.tvVaultRegister;")
    extra = (D.fn(s, "persistOwned") + "\n"
             + "var _VR_LOG = 'd2r_vaultRemoved', _VR_RING = 20;\n"
             + D.between(s, "  function _vrRead(){", "  /* the heart and the console read the journal through here", keep_b=False)
             + D.between(s, "  window.vaultRemove = function(names, opts){", "  // v342.3 — throw out a Magic & Rare keeper", keep_b=False)
             + D.window_fn(s, "vaultAutoAssign") + "\n" + D.window_fn(s, "vaultUnown") + "\n"
             + D.start_to_close(s, s.index("  window.vaultDropMenuImport = async function(){"), "vaultDropMenuImport") + ";\n"
             + _door(s, "  window.tvVaultRegister = function(name, witness){\n")
             + D.start_to_close(s, wa + 2, "the register's frame gate") + ")();\n"
             + "window.__V = { assign: function(){ return assign; } };\n")
    pre = ("window._vaultResolveName = function(n){ return n; };\nvar EXTRA_ITEMS = {};\n"
           # REG-2663 (#209, v3813): the register head asks whether a name is an item at all - not this law's question
           "window._vaultNotAnItem = function(){ return null; };\n"
           "window._ownedAdd = function(n){ owned.add(n); return { ok: true }; };\n"
           "window._vaultRemovalNote = function(){ return { noted: 0 }; };\n")
    chron = (D.between(s, "  function _chLsGet(key, fallback){", "  function _chFoldApos(s){", keep_b=False)
             + "var _CH_INBOX_KEY = 'd2r_chronicleInbox'; function _chLogSetStatus(){}\n"
             + _door(s, "  window.kaiVaultFileOnly = function(name){\n"))
    return (D.stage(s) + D.boot(s) + D.tab_sync(s) + "\n" + D.VAULT_DOOR_STUBS + pre + "(function(){\n" + D.vault_head(s)
            + "\nfunction muleById(id){ return roster.find(function(m){ return m.id === id; }) || null; }\n"
            + D.say_line(s) + D.vault_door(s) + "\n" + extra + "\n})();\n" + chron)


WRITES = ("var WROTE = []; var _set = window.LSR.setItem; window.LSR.setItem = function(k, v){ WROTE.push(k);"
          " return _set.call(window.LSR, k, v); };\n")

DOORS = WRITES + r"""
OUT.held = window._vaultBasisHeld();
WROTE.length = 0;
OUT.move = window.vaultFile('Grief', null, { move: true, mule: 'uni-armor', by: 'hand' });
OUT.file = window.vaultFile('Enigma', { by: 'reader', lane: 'stash', sessions: %(l2)s }, { mule: 'uni-armor' });
OUT.sort = window.vaultAutoAssign();
OUT.reg = window.tvVaultRegister('Arachnid Mesh', { by: 'hand', at: '2026-10-22T10:00:00Z', where: 'the Chronicle inbox (Vault only)' });
OUT.inbox = window.kaiVaultFileOnly('Arachnid Mesh');
OUT.wrote = WROTE.filter(function(k){ return k !== 'd2r_chronicleLog'; });
OUT.raw = { map: RAW['d2r_muleAssign'], prov: RAW['d2r_vaultProv'], owned: RAW['d2r_owned'], inbox: RAW['d2r_chronicleInbox'] };
OUT.map = JSON.parse(JSON.stringify(window.__V.assign()));
OUT.status = STATUS.slice();
""" % {"l2": L2}


def _run(body, seed):
    s = D.src()
    return D.page(_pieces(s), body, seed=seed)


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED vault doors; UNMEASURED, not passing")
class TheVaultHoldRefusesAtTheOneDoor(unittest.TestCase):

    def test_with_every_store_readable_each_door_still_writes(self):
        """the premise: the doors this law holds shut do work, so the refusals below are the hold, not a dead harness"""
        o = _run(DOORS, _seed(**{"d2r_vaultProv": json.dumps({
            "Grief": json.loads(PROV)["Grief"],
            "Shako": {"mule": None, "source": "stash", "by": "reader", "sessions": ["s1", "s2"],
                      "looks": [{"id": "s1", "conf": 0.9}, {"id": "s2", "conf": 0.9}]}})}))
        self.assertIsNone(o["held"])
        self.assertEqual((o["move"]["ok"], o["move"]["mode"]), (True, "moved"), o["move"])
        self.assertTrue(o["file"]["ok"], o["file"])
        self.assertTrue(o["reg"]["ok"], o["reg"])
        self.assertTrue(o["inbox"]["ok"], o["inbox"])
        self.assertEqual(json.loads(o["raw"]["inbox"]), [], "PREMISE: 'Vault only' no longer clears the row it filed")
        self.assertIn("Arachnid Mesh", json.loads(o["raw"]["owned"]))
        self.assertEqual(json.loads(o["raw"]["map"]).get("Grief"), "uni-armor", "PREMISE: the move did not land")

    def test_while_a_store_the_vault_stands_on_will_not_read_every_door_refuses_in_words(self):
        for key, bad in HELD.items():
            with self.subTest(store=key):
                o = _run(DOORS, _seed(**{key: bad}))
                self.assertTrue(o["held"] and key in o["held"], "PREMISE: %s did not hold the vault: %r" % (key, o["held"]))
                for door in ("move", "file"):
                    r = o[door]
                    self.assertFalse(r["ok"], "%s held: vaultFile's %s answered ok over a refused write: %r" % (key, door, r))
                    self.assertEqual(r.get("refused"), "held", "%s held: the %s was not refused by the hold: %r" % (key, door, r))
                    self.assertIn(key, r.get("why", ""), "%s held: the %s refusal does not name the store" % (key, door))
                # the mule map itself unreadable is refused one step earlier, by its own words ('the mule map will not parse')
                self.assertEqual(o["sort"].get("refused"), "mule-map-unreadable" if key == "d2r_muleAssign" else "held",
                                 "%s held: the sorter sorted: %r" % (key, o["sort"]))
                self.assertEqual(o["sort"].get("filed"), 0)
                self.assertTrue(any("nothing was sorted" in m and (key in m or "the mule map" in m) for m in o["status"]),
                                "%s held: the sorter's refusal was not said: %r" % (key, o["status"]))
                self.assertFalse(o["reg"]["ok"], "%s held: his hand registered into a held vault: %r" % (key, o["reg"]))
                self.assertEqual(o["reg"].get("refused"), "held")
                self.assertFalse(o["inbox"]["ok"], "%s held: 'Vault only' answered ok with nothing saved" % key)
                self.assertEqual(o["raw"]["inbox"], INBOX, "%s held: his inbox row was deleted with nothing saved" % key)
                self.assertIn(key, o["inbox"].get("say", ""), "%s held: the inbox does not say which store holds it" % key)
                self.assertEqual(o["wrote"], [], "%s held: a door still tried to write %r" % (key, o["wrote"]))
                self.assertEqual(o["raw"]["prov"], PROV, "%s held: a witness row was written from a held vault" % key)
                # an unreadable mule map runs on its default ({}) in memory; nothing was filed into it either
                self.assertEqual(o["map"], {} if key == "d2r_muleAssign" else {"Grief": "uni-weap"},
                                 "%s held: the map moved in memory: %r" % (key, o["map"]))
                self.assertEqual(o["raw"]["map"], bad if key == "d2r_muleAssign" else '{"Grief":"uni-weap"}',
                                 "%s held: the saved mule map was written" % key)

    def test_the_removal_door_and_its_undo_wait_while_a_store_they_write_is_held(self):
        body = WRITES + r"""
WROTE.length = 0;
OUT.rm = window.vaultRemove(['Grief'], { lane: 'hand' });
OUT.undo = window.vaultRestoreLast();
OUT.wrote = WROTE.slice(); OUT.journal = RAW['d2r_vaultRemoved'] == null ? null : RAW['d2r_vaultRemoved'];
OUT.ownedHas = owned.has('Grief'); OUT.status = STATUS.slice();
"""
        for label, seed, key in (("journal cut short", _seed(d2r_vaultRemoved=JOURNAL_CUT), "d2r_vaultRemoved"),
                                 ("owned quarantined", _seed(d2r_owned='{"a":1}'), "d2r_owned")):
            with self.subTest(held=label):
                o = _run(body, seed)
                self.assertEqual(o["rm"].get("refused"), "held", "%s: the removal went through: %r" % (label, o["rm"]))
                self.assertEqual(o["rm"].get("removed"), [])
                self.assertIn(key, o["rm"].get("why", ""), "%s: the refusal does not name %s" % (label, key))
                self.assertEqual(o["undo"].get("refused"), "held", "%s: the undo ran: %r" % (label, o["undo"]))
                self.assertEqual(o["wrote"], [], "%s: the removal door still wrote %r" % (label, o["wrote"]))
                self.assertEqual(o["journal"], JOURNAL_CUT if key == "d2r_vaultRemoved" else None,
                                 "%s: the journal was written" % label)
                self.assertTrue(any("nothing removed" in m for m in o["status"]), "%s: not said: %r" % (label, o["status"]))
                self.assertTrue(any("nothing was undone" in m for m in o["status"]), "%s: the undo's refusal was not said" % label)


class TheCallersOfTheRemovalDoorKeepItsWords(unittest.TestCase):

    @unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED doors; UNMEASURED, not passing")
    def test_a_refused_removal_is_never_reported_as_not_owned_or_as_zero_removed(self):
        body = (WRITES + "window.__ASYNC = true; window.uiConfirm = function(){ return Promise.resolve(true); };\n"
                "(async function(){\n"
                "OUT.unown = window.vaultUnown('Grief'); OUT.unownSaid = STATUS.slice(); STATUS.length = 0;\n"
                "window._menuRunVerdict = { isMenu: true, armed: true, names: ['Enigma'], why: 'alphabetical' };\n"
                "await window.vaultDropMenuImport(); OUT.menuSaid = STATUS.slice();\n"
                "OUT.owned = Array.from(owned).sort(); OUT.wrote = WROTE.slice();\n"
                "})().then(done).catch(function(e){ process.stderr.write(String(e && e.stack || e)); process.exit(3); });")
        o = _run(body, _seed(d2r_vaultRemoved=JOURNAL_CUT))
        self.assertEqual(o["unown"].get("refused"), "held", "PREMISE: the removal door did not refuse: %r" % o["unown"])
        self.assertTrue(o["unownSaid"] and "nothing removed" in o["unownSaid"][-1],
                        "the card's un-own buried the door's refusal: %r" % o["unownSaid"])
        self.assertFalse(any("was not in owned" in m for m in o["unownSaid"]), "a held removal was reported as 'not in owned'")
        self.assertTrue(o["menuSaid"] and "nothing removed" in o["menuSaid"][-1],
                        "the menu import buried the door's refusal under its own line: %r" % o["menuSaid"])
        self.assertFalse(any("removed 0" in m for m in o["menuSaid"]))
        self.assertEqual(o["owned"], ["Enigma", "Grief", "Harlequin Crest (Shako)"], "a name left owned")


TOGGLE_PROGRAM = r"""
var window = globalThis;
var RAW = %(seed)s;
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
               setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; } };
var LS = window.LSR;
var _cnV = function(x){ return String(x||'').replace(/[‘’`]/g, "'").toLowerCase().trim(); };
var owned = new Set(['Enigma', 'Harlequin Crest']), magicFinds = {}, assign = { 'Enigma': 'runewords' }, copies = {};
var unknownReads = new Set(), etherealItems = new Set(), superiorBases = new Set(), PROV = {};
function _provAll(){ return PROV; } function _provDrop(){} function _provAsWitness(r){ return r; }
function persistOwned(){ LS.setItem('d2r_owned', JSON.stringify(Array.from(owned))); }
function persist(){ persistOwned(); }
function saveA(){} function renderVault(){} function refreshOpenCard(){}
var SAID = []; function status(m){ SAID.push(String(m)); }
window._repaintOwned = function(){}; window._D2R_LEDGER = null; window.D2R_PROFILE = 'main';
window._ownedAdd = function(n){ owned.add(n); return { added: true }; };
window._ownedProvForget = function(){ return false; };
window._vaultRemovalNote = function(){ return { noted: 0 }; };
function muleById(id){ return { id: id, name: id }; } function suggestMule(){ return null; }
window.vaultFile = function(){ return { ok: true }; };
%(journal)s
%(door)s
var ITEMS = [{ n: 'Harlequin Crest', tier: 'grail' }];
window._gUniqueRoster = function(){ return ['Harlequin Crest']; };
window._UNI_EXTRA = {}; window._GRAIL_SEED = {};
function _gFound(){ return true; } function _gFoundDirty(){}
function renderHero(){} function renderBossCards(){} function renderCalc(){} function renderGrailProgress(){}
function showCelebrate(){} function ownedPool(){ return Array.from(owned); }
var document = { getElementById: function(){ return null; } };
var TOASTS = []; window._grailToast = function(i, m, s){ TOASTS.push(String(m) + ' | ' + String(s)); };
%(say)s
%(toggle)s
var OUT = {};
toggleOwned('Enigma');                      /* his un-tick on a runeword's card (the non-grail branch) */
toggleOwned('Harlequin Crest');             /* and on a grail unique's card (the grail branch) */
OUT.owned = Array.from(owned).sort(); OUT.journal = RAW['d2r_vaultRemoved']; OUT.storedOwned = RAW['d2r_owned'] || null;
OUT.toasts = TOASTS.slice(); OUT.said = SAID.slice();
process.stdout.write(JSON.stringify(OUT));
"""


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED toggleOwned; UNMEASURED, not passing")
class AnUntickTheDoorRefusedIsNeverWalkedAround(unittest.TestCase):

    def test_both_untick_branches_keep_the_name_and_say_why_when_the_removal_door_refuses(self):
        s = D.src()
        prog = TOGGLE_PROGRAM % {
            "seed": json.dumps({"d2r_vaultRemoved": JOURNAL_CUT, "d2r_owned": '["Enigma","Harlequin Crest"]',
                                "d2r_foundLog": '{"Harlequin Crest":"2026-10-01"}'}),
            "journal": "", "door": "var _VR_LOG = 'd2r_vaultRemoved', _VR_RING = 20;\n"
            + D.between(s, "  function _vrRead(){", "  /* the heart and the console read the journal through here", keep_b=False)
            + D.between(s, "  window.vaultRemove = function(names, opts){", "  /* The reverse of exactly one batch", keep_b=False),
            "say": D.fn(s, "_vrRefusedSay") + "\nwindow._vrRefusedSay = _vrRefusedSay;\n",
            "toggle": D.fn(s, "toggleOwned")}
        r = subprocess.run([D.NODE, "-"], input=prog, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=60)
        if r.returncode != 0:
            raise AssertionError("the shipped toggleOwned would not run in node: %s" % (r.stderr or r.stdout)[-1500:])
        o = json.loads(r.stdout)
        self.assertEqual(o["owned"], ["Enigma", "Harlequin Crest"],
                         "an un-tick walked around the removal door's refusal - the name left owned with no journal row")
        self.assertEqual(o["journal"], JOURNAL_CUT, "the journal that would not read was written over")
        self.assertNotEqual(o["storedOwned"], '["Harlequin Crest"]', "the walked-around removal was persisted")
        self.assertEqual(len(o["toasts"]), 2, "the refusal was not said where he clicked: %r" % o["toasts"])
        self.assertTrue(all("stays in your vault" in t and "nothing was removed" in t for t in o["toasts"]), o["toasts"])
        self.assertTrue(any("d2r_vaultRemoved" in m for m in o["said"]), "the removal door did not say why: %r" % o["said"])


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED backfill; UNMEASURED, not passing")
class AOneTimeReplayWaitsForAHeldVault(unittest.TestCase):

    def test_the_provenance_backfill_does_not_stamp_itself_done_over_refusals(self):
        """the one-time backfill replays his reads through the register - which refuses while the vault is held - and
        stamps itself done: run while held, it would never run again. It waits, said, and asks again next load."""
        s = D.src()
        prog = (r"""
var window = globalThis, RAW = {};
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
               setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; } };
RAW['d2r_chronicleInboxLog'] = JSON.stringify([{ name: 'Grief', loc: 'stash', sessionId: 's_1', firstSeenTs: 1 }]);
function _bfRead(){ return null; } function _read(){ return {}; }
var REG = []; window.tvVaultRegister = function(n){ REG.push(n); return { ok: false, refused: 'held' }; };
window._vaultMayClaim = function(){ return true; };
var HELD = null; window._vaultHeld = function(){ return HELD; };
/* past the hold the replay reads his removals first: a recorder that answers UNKNOWN, so a run that got past the hold
   stops there and says so - never a crash on a helper this cut does not carry */
var RM_ASKED = 0, _RM_AT_KEY = 'd2r_vaultRemovedAt'; function _rmRead(){ RM_ASKED++; return null; }
""" + D.window_fn(s, "_ownedProvBackfill") + r"""
HELD = { keys: ['d2r_intakeLog'], why: 'the vault is held - d2r_intakeLog will not parse' };
var OUT = { r: window._ownedProvBackfill(), reg: REG.slice(), stamp: RAW['d2r_ownedProvBackfill'] || null, rm: RM_ASKED };
process.stdout.write(JSON.stringify(OUT));
""")
        r = subprocess.run([D.NODE, "-"], input=prog, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=60)
        if r.returncode != 0:
            raise AssertionError("the shipped backfill would not run in node: %s" % (r.stderr or r.stdout)[-1500:])
        o = json.loads(r.stdout)
        self.assertFalse(o["r"].get("ran"), "the backfill ran while the vault is held: %r" % o["r"])
        self.assertIn("the vault is held", o["r"].get("why", ""), "the wait was not said")
        self.assertIn("asks again next load", o["r"].get("why", ""))
        self.assertEqual(o["reg"], [], "the backfill replayed reads into a held vault")
        self.assertIsNone(o["stamp"], "the backfill stamped itself done while the vault is held")
        self.assertEqual(o["rm"], 0, "the backfill went past the hold (it read his removals to replay over a held vault)")


RED_PROOF = [
    {"why": "REG-2521 - the card's un-own reports a held removal as 'was not in owned'",
     "file": "bible.html", "matches": 1,
     "find": "    if (r && r.refused) return r;\n    if (r && r.removed.length) {\n",
     "replace": "    if (r && r.removed.length) {\n"},
    {"why": "REG-2521 - the menu import buries a held removal under 'removed 0 menu-read name(s)'",
     "file": "bible.html", "matches": 1,
     "find": "    if (vrM && vrM.refused) return;   /* REG-2521",
     "replace": "    if (false) return;   /* REG-2521"},
    {"why": "REG-2521 - the one-time provenance backfill runs while the vault is held and stamps itself done over refusals",
     "file": "bible.html", "matches": 1,
     "find": "    if (_bfHeld) return { ran: false, why: _bfHeld.why + ' — nothing was backfilled; it asks again next load' };\n",
     "replace": ""},
    {"why": "REG-2521 - vaultFile no longer asks the hold at its door (a move / filing answered ok over a refused write)",
     "file": "bible.html", "matches": 1,
     "find": "    if (_bh0) return { ok: false, refused: 'held', why: nm + ' was not filed - ' + _bh0 + ' (see the notice at the top)' };\n",
     "replace": ""},
    {"why": "REG-2521 - the sorter sorts while the vault is held ('filed 1 witnessed item' with nothing saved)",
     "file": "bible.html", "matches": 1,
     "find": "    if (_bhS){ status('⚠ nothing was sorted - ' + _bhS + ' (see the notice at the top)'); return { filed: 0, refused: 'held', why: _bhS }; }\n",
     "replace": ""},
    {"why": "REG-2521 - a hand witness registers into a held vault ('Vault only' deletes his inbox row with nothing saved)",
     "file": "bible.html", "matches": 1,
     "find": "      if (_vhR) return { ok:false, refused:'held', registered:false, held:_vhR.keys,\n",
     "replace": "      if (false) return { ok:false, refused:'held', registered:false, held:_vhR.keys,\n"},
    {"why": "REG-2521 - Magic & Rare is not in the basis (the prune and the filing doors judge against a default pool)",
     "file": "bible.html", "matches": 1,
     "find": "d2r_copies: 1, d2r_vaultProv: 1, d2r_magicFinds: 1 });\n",
     "replace": "d2r_copies: 1, d2r_vaultProv: 1 });\n"},
    {"why": "REG-2521 - the removal door does not ask the hold (removes while owned is quarantined)",
     "file": "bible.html", "matches": 1,
     "find": "    var _hRm = (typeof window._vaultRemovalHeld === 'function') ? window._vaultRemovalHeld(!opts.keepFiling) : null;\n",
     "replace": "    var _hRm = null;\n"},
    {"why": "REG-2521 - the undo runs while a store it writes is held",
     "file": "bible.html", "matches": 1,
     "find": "    if (_hU){ status('⚠ nothing was undone - ' + _hU.why + ' (see the notice at the top)'); return { restored: 0, kept: 0, refused: 'held', why: _hU.why }; }\n",
     "replace": ""},
    {"why": "REG-2521 - the non-grail un-tick walks around the removal door's refusal again",
     "file": "bible.html", "matches": 1,
     "find": "      if (_vrNG && _vrNG.refused){ try { window._vrRefusedSay(name, _vrNG); } catch(eRs2){} }\n      else {",
     "replace": "      if (false){}\n      else {"},
    {"why": "REG-2521 - the grail un-tick walks around the removal door's refusal again",
     "file": "bible.html", "matches": 1,
     "find": "          if (_vrUT && _vrUT.refused){ try { window._vrRefusedSay(name, _vrUT); } catch(eRs){} } else if (",
     "replace": "          if (false){} else if ("},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
