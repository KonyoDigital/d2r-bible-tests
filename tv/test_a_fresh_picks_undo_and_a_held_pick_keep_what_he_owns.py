# -*- coding: utf-8 -*-
"""REG-2560 / REG-2561 - A FRESH PLANNER PICK'S UNDO TAKES BACK ONLY ITS OWN ONE, AND A HELD VAULT SAVES NO PICK.

The V1 round-3 review 2 of track B (REG-2534, REG-2532/2533), reproduced on the merged A+B+C tree, the whole page in node:
  * REG-2560 (major): REG-2534 fixed a COPY pick's undo; a FRESH pick's undo (_vpDrop) still deleted the name outright -
    owned, filing, no journal row. A 4os Monarch filed by a fresh pick, then this tab's own reader counts a re-read one
    (the low-base register: copy 2), then the pick is cleared or re-rolled: BOTH Monarchs left d2r_owned and SOCKETED,
    and the d2r_copies key was orphaned. Now one copy comes off and the name stays owned and filed, said in words; only
    the pick's own single copy is removed, through the removal door (dated, journaled, undoable).
  * REG-2561 (major): with a store the vault stands on quarantined (d2r_copies cut short), a perfect-base pick of a
    filed label skipped vaultHandAdd and vaultFile and answered 'copy 2 filed to bases' (ok, filed) - nothing landed,
    and the 2 came from the empty default of a store that would not parse. Every pick that is not a clear now asks the
    hold first and refuses in its words, writing nothing.
Driven on the WHOLE page in node (tv/vault_page_node.py), real doors only.
RED_PROOF below: the one-copy-off arm removed (the name dropped outright again); the removal door bypassed (no journal
row for the take-back); the hold question removed from the planner door.
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

AUTOMATED = r"""
Object.defineProperty(navigator, 'webdriver', { get: function(){ return true; }, configurable: true });
location.protocol = 'file:'; location.href = 'file:///spec/bible.html'; location.origin = 'null'; location.host = ''; location.hostname = '';
"""

#: Monarch (4os) owned and filed to SOCKETED, and d2r_copies cut short: the vault is held
HELD_SEED = r"""
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify(['Monarch (4os)']));
localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'Monarch (4os)': 'bases' }));
localStorage.setItem('d2r_copies', '{"Monarch (4os)": 2, "Grief": 3');
"""

FRESH_BODY = r"""
(function(){
var W = window, L = 'Monarch (4os)', steps = [];
function disk(k){ try { return JSON.parse(W.LSR.getItem(k) || 'null'); } catch (e) { return 'UNREADABLE'; } }
function now(label, r){ var c = disk('d2r_copies') || {}, ow = disk('d2r_owned') || [];
  steps.push({ label: label, mode: (r && r.mode) || null, why: (r && r.why) || '', disk: (c[L] == null ? null : c[L]),
               mem: (copies[L] == null ? null : copies[L]), home: (disk('d2r_muleAssign') || {})[L] || null,
               ownedDisk: ow.indexOf(L) >= 0, ownedMem: owned.has(L) }); }
var d = W._cbDb(), code = Object.keys(d.b).find(function(c){ return d.b[c][0] === 'Monarch'; });
function ent(s){ var e = W._cbEntryFor(W._cbItem('b:' + code)); e.sockets = s; e.eth = false; return e; }
W._vaultPlannerOn = true;
var S = __S__;
OUT.forged = Object.keys(disk('d2r_rwMade') || {}).length;
now('pick', W.vaultPlannerFile(ent(4), 'vp-2560'));
if (S.door === 'reader'){ OUT.register = W._autoRegisterLowBase('Monarch (4os low base)', null); }
now('other door');
var end = (S.end === 'clear') ? W.vaultPlannerFile(null, 'vp-2560') : W.vaultPlannerFile(ent(3), 'vp-2560');
now(S.end, end);
var log = disk('d2r_vaultRemoved');
OUT.journal = Array.isArray(log) ? JSON.stringify(log) : String(log);
OUT.steps = steps;
})();
"""

HELD_BODY = r"""
(function(){
var W = window, L = 'Monarch (4os)';
var d = W._cbDb(), code = Object.keys(d.b).find(function(c){ return d.b[c][0] === 'Monarch'; });
function ent(s){ var e = W._cbEntryFor(W._cbItem('b:' + code)); e.sockets = s; e.eth = false; return e; }
OUT.held = W._vaultHeld();
OUT.rawBefore = H.RAW.get('d2r_copies');
W._vaultPlannerOn = true;
var r1 = W.vaultPlannerFile(ent(4), 'vp-2561');
var r2 = W.vaultPlannerFile(ent(5), 'vp-2561b');
OUT.r = [r1, r2].map(function(r){ return { ok: r && r.ok, filed: !!(r && r.filed), mode: (r && r.mode) || null,
                                            refused: (r && r.refused) || null, why: (r && r.why) || '' }; });
OUT.rawAfter = H.RAW.get('d2r_copies');
OUT.owned = Array.from(owned);
})();
"""

SCEN = {"reader-clear": {"door": "reader", "end": "clear"}, "reader-reroll": {"door": "reader", "end": "reroll"},
        "none-clear": {"door": "none", "end": "clear"}}
_RUNS = {}


def run(name):
    if name not in _RUNS:
        if name == "held":
            _RUNS[name] = VPN.run(HELD_BODY, prelude=AUTOMATED + HELD_SEED, timeout=300)
        else:
            _RUNS[name] = VPN.run(FRESH_BODY.replace("__S__", json.dumps(SCEN[name])), prelude="", timeout=300)
    return _RUNS[name]


def step(o, label):
    for s in o.get("steps") or []:
        if s.get("label") == label:
            return s
    raise AssertionError("no step %r in %r" % (label, o.get("steps")))


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AFreshPicksUndoAndAHeldPickKeepWhatHeOwns(unittest.TestCase):

    def test_0_premise(self):
        for name in SCEN:
            o = run(name)
            self.assertEqual(o["__boot"]["errors"], [], "%s: a page script did not run: %r" % (name, o["__boot"]))
            self.assertEqual(o.get("forged"), 0, "PREMISE: not a fresh install")
            p = step(o, "pick")
            self.assertEqual((p["mode"], p["home"], p["ownedDisk"]), ("filed", "bases", True), "%s PREMISE: the fresh pick did not file: %r" % (name, p))
        for name in ("reader-clear", "reader-reroll"):
            o = run(name)
            self.assertEqual((o.get("register") or {}).get("mode"), "copy", "PREMISE: the reader did not count copy 2: %r" % o.get("register"))
            self.assertEqual(step(o, "other door")["mem"], 2, "PREMISE: the re-read is not counted")

    def test_1_a_clear_keeps_the_one_this_tabs_reader_counted(self):
        c = step(run("reader-clear"), "clear")
        self.assertTrue(c["ownedDisk"] and c["ownedMem"], "the clear dropped the Monarch the reader counted: %r" % c)
        self.assertEqual(c["home"], "bases", "the clear unfiled the Monarch the reader counted: %r" % c)
        self.assertIsNone(c["mem"], "the pick's own copy was not taken off the live count: %r" % c)
        self.assertIsNone(c["disk"], "the pick's own copy was not taken off d2r_copies: %r" % c)
        self.assertIn("this pick added is taken back; 1 counted now, still filed", c["why"], c)

    def test_2_a_reroll_keeps_the_one_this_tabs_reader_counted(self):
        r = step(run("reader-reroll"), "reroll")
        self.assertTrue(r["ownedDisk"], "re-rolling the fresh pick dropped the Monarch the reader counted: %r" % r)
        self.assertEqual(r["home"], "bases", r)
        self.assertIn("this pick added is taken back; 1 counted now, still filed", r["why"], r)

    def test_3_the_control_takes_the_picks_own_one_back_through_the_removal_door(self):
        o = run("none-clear")
        c = step(o, "clear")
        self.assertFalse(c["ownedDisk"] or c["ownedMem"], "a clear with nothing else counted kept the pick: %r" % c)
        self.assertIsNone(c["home"], c)
        self.assertIn("planner-take-back", o.get("journal") or "", "the take-back left no row in the removal journal: %r" % o.get("journal"))
        self.assertIn("Monarch (4os) is taken back", c["why"], c)

    def test_4_a_held_vault_saves_no_pick(self):
        o = run("held")
        self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
        self.assertTrue(o.get("held"), "PREMISE: the cut-short d2r_copies did not hold the vault")
        for r in o["r"]:
            self.assertFalse(r["ok"], "a pick was answered ok while the vault is held: %r" % r)
            self.assertFalse(r["filed"], r)
            self.assertEqual(r["refused"], "held", r)
            self.assertNotEqual(r["mode"], "copy", r)
            self.assertIn("the vault is held", r["why"], r)
            self.assertIn("nothing was added", r["why"], r)
        self.assertEqual(o["rawAfter"], o["rawBefore"], "the held d2r_copies bytes changed")
        self.assertEqual(o["owned"], ["Monarch (4os)"], "a held pick changed what he owns: %r" % o["owned"])


RED_PROOF = [
    {"why": "REG-2560 - a fresh pick's undo drops the name outright again, taking the copy another door counted",
     "file": "bible.html",
     "find": "    if (cnt > 1 && typeof owned !== 'undefined' && owned && owned.has && owned.has(nm)){\n",
     "replace": "    if (false && cnt > 1 && typeof owned !== 'undefined' && owned && owned.has && owned.has(nm)){\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2560 - the take-back walks around the removal door again: no dated, journaled, undoable row",
     "file": "bible.html",
     "find": "    if (typeof window.vaultRemove === 'function' && typeof owned !== 'undefined' && owned && owned.has && owned.has(nm)){\n",
     "replace": "    if (false && typeof window.vaultRemove === 'function' && typeof owned !== 'undefined' && owned && owned.has && owned.has(nm)){\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2561 - the planner door no longer asks the hold, so a held vault answers 'copy 2 filed' over nothing",
     "file": "bible.html",
     "find": "    if (_hdP){\n",
     "replace": "    if (false && _hdP){\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
