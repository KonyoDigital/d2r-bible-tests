# -*- coding: utf-8 -*-
"""#183 (REG-2530) - A SECOND, DIFFERENT PLANNER PICK NEVER TAKES BACK THE COPY THE FIRST PICK FILED.

GrokBot's V0 triage (2026-10-22, run 39726369389 on v3784, 2/2 headless): v3740:63 and v3742r:72 - Grief is already
filed, a planner pick of it files copy 2, then a pick of a DIFFERENT item in the same open (same token, a different
builder id) and d2r_copies has no Grief at all: expected 2, actual undefined. REG-2227 (v3740) had put the id check on
the name-change undo, and REG-2240 (v3742) scoped _vpCopyUndo to the bump's own name; REG-2267 (v3753) then dropped the
id check to undo a "swap", and the name check could not hold, because the name it compares IS the first pick's.

The planner rule is one rule for both halves of a pick: a different item in the same open is a SECOND ADD (the fresh
record of the first pick already survives it - _vpDrop has always required the same id), and only a RE-ROLL of the same
pick (same id, a new composed name) or a clear of the held pick takes back what that pick made. Taking back a copy on a
different pick dropped a real item from his count without a word, and the sentence he had just read ("Grief - copy 2
filed to uni-weap") stayed on screen as a lie. [[unknown-stays-unknown]] [[the-unjoined-end]]

And what an undo takes back reaches DISK: the undo changed only the live count, so after a clear (or a re-roll whose
new pick stopped early) d2r_copies still said copy 2 and the next load put the taken-back copy back.

Driven on the WHOLE page in node (tv/vault_page_node.py), in the world a Playwright file:// page is (navigator.webdriver,
file:), with each spec's own seed and stubs, reading d2r_copies from storage as the specs do:
  * v3740:63  - Grief (copy 2), then Spirit in the same open: Grief stays 2 (the spec's stubs exactly: the real
                _vaultNameAmbiguity);
  * v3742r:72 - and a re-roll of that second pick (same id, new name): Grief stays 2, the Spirit record moves;
  * a clear of the held second pick takes back only that pick: Grief stays 2, the fresh Spirit filing goes;
  * a RE-ROLL of the copy pick itself (same id, a new name) still takes its copy back, and so does a clear of it -
    on disk, and the open planner is told to draw it;
  * a re-roll of the copy pick whose new pick stops at the white-base sentence takes the copy back ON DISK too;
  * the same open counts once, and a later open of Grief files the next copy (3) beside the first two.
RED_PROOF below: the id check removed from the name-change undo turns every "stays 2" red; the undo's write removed
turns the on-disk half red.
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

#: the world a Playwright spec runs in: navigator.webdriver on a file:// page (the owner world, his seeded Chronicle)
AUTOMATED = r"""
Object.defineProperty(navigator, 'webdriver', { get: function(){ return true; }, configurable: true });
location.protocol = 'file:'; location.href = 'file:///spec/bible.html'; location.origin = 'null'; location.host = ''; location.hostname = '';
"""

#: the seed both specs write before the page loads: Grief owned once, no copies, already filed to uni-weap
SEED = r"""
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify(['Grief']));
localStorage.setItem('d2r_copies', JSON.stringify({}));
localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'Grief': 'uni-weap' }));
"""

BODY = r"""
(function(){
var W = window;
function disk(k){ try { return JSON.parse(W.LSR.getItem(k) || 'null'); } catch (e) { return 'UNREADABLE'; } }
function copiesNow(){ var c = disk('d2r_copies'); return (c && typeof c === 'object') ? c : {}; }
var S_ = __SCENARIO__;
/* the specs' stubs: each pick resolves to its own name (a runeword unless the pick says otherwise); suggestMule,
   muleById, vaultFile, copies and assign stay the page's own, so the copy bump and its undo run against the real
   stores. v3740 leaves _vaultNameAmbiguity real; v3742r stubs it - each scenario keeps its spec's choice. */
W._cbItem = function(id){ return { id: id }; };
W._cbShown = function(entry){ return { name: entry && entry.name, q: (entry && entry.q) || 'r', base: (entry && entry.base) || '' }; };
W._vaultResolveName = function(n){ return n; };
if (S_ !== 'second') W._vaultNameAmbiguity = function(){ return null; };
W.vaultHandAdd = function(){ return { ok: true }; };
W._vaultPlannerOn = true;
var G = { id: 'ENTRY-GRIEF', name: 'Grief', base: 'Phase Blade' };
var S = { id: 'ENTRY-SECOND', name: 'Spirit', base: 'Monarch' };
var steps = [];
function pick(e, tok, label){
  W._vaultPlannerDirty = false;
  var r = W.vaultPlannerFile(e, tok);
  var c = copiesNow(), a = disk('d2r_muleAssign') || {};
  steps.push({ label: label, mode: (r && r.mode) || null, filed: !!(r && r.filed), why: (r && r.why) || '',
               grief: (c.Grief == null ? null : c.Grief), griefMem: (copies.Grief == null ? null : copies.Grief),
               griefHome: a.Grief || null, spirit: a.Spirit || null, reroll: a['Spirit (vp-reroll)'] || null,
               dirty: W._vaultPlannerDirty === true });
}
if (S_ === 'second'){
  pick(G, 'vp-183', 'grief'); pick(S, 'vp-183', 'second');
} else if (S_ === 'reroll'){
  pick(G, 'vp-183', 'grief'); pick(S, 'vp-183', 'second');
  pick({ id: 'ENTRY-SECOND', name: 'Spirit (vp-reroll)', base: 'Archon Plate' }, 'vp-183', 'reroll-second');
} else if (S_ === 'clear-second'){
  pick(G, 'vp-183', 'grief'); pick(S, 'vp-183', 'second'); pick(null, 'vp-183', 'clear');
} else if (S_ === 'reroll-first'){
  pick(G, 'vp-183', 'grief'); pick({ id: 'ENTRY-GRIEF', name: 'Grief of the Re-roll', base: 'Phase Blade' }, 'vp-183', 'reroll-grief');
} else if (S_ === 'clear-first'){
  pick(G, 'vp-183', 'grief'); pick(null, 'vp-183', 'clear');
} else if (S_ === 'reroll-first-stops'){
  /* the same pick re-rolled into a plain white base: its new answer is the white-base sentence, an early return */
  pick(G, 'vp-183', 'grief'); pick({ id: 'ENTRY-GRIEF', name: 'Plain Phase Blade', base: 'Phase Blade', q: 'b' }, 'vp-183', 'reroll-white');
} else if (S_ === 'later-open'){
  pick(G, 'vp-183', 'grief'); pick(G, 'vp-183', 'grief-again'); pick(S, 'vp-183', 'second');
  pick(G, 'vp-183-later', 'grief-later-open');
}
OUT.steps = steps;
})();
"""

_RUNS = {}


def run(scenario):
    if scenario not in _RUNS:
        _RUNS[scenario] = VPN.run(BODY.replace("__SCENARIO__", json.dumps(scenario)), prelude=AUTOMATED + SEED, timeout=300)
    return _RUNS[scenario]


def step(o, label):
    for s in o.get("steps") or []:
        if s.get("label") == label:
            return s
    raise AssertionError("no step %r in %r" % (label, o.get("steps")))


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ASecondPlannerPickKeepsTheFirstPicksCopy(unittest.TestCase):

    def test_0_the_page_boots_and_the_first_pick_files_copy_two(self):
        for scenario in ("second", "reroll"):
            o = run(scenario)
            self.assertEqual(o["__boot"]["errors"], [], "a page script did not run in node: %r" % o["__boot"])
            g = step(o, "grief")
            self.assertEqual(g.get("mode"), "copy", "PREMISE: the already-filed Grief pick did not take the copy path: %r" % g)
            self.assertEqual(g.get("grief"), 2, "PREMISE: Grief is not copy 2 on disk after the first pick: %r" % g)
            self.assertIn("copy 2", g.get("why", ""))

    def test_1_a_different_second_pick_keeps_the_first_picks_copy(self):
        """v3740:63 - the spec's own scenario"""
        s = step(run("second"), "second")
        self.assertTrue(s.get("filed"), "PREMISE: the second, different pick did not file: %r" % s)
        self.assertEqual(s.get("grief"), 2, "a later, different pick took back Grief's copy (d2r_copies on disk): %r" % s)
        self.assertEqual(s.get("griefMem"), 2, "a later, different pick took back Grief's copy (the live count): %r" % s)
        self.assertEqual(s.get("griefHome"), "uni-weap", "the second pick unfiled Grief: %r" % s)

    def test_2_a_reroll_of_the_second_pick_keeps_the_first_picks_copy(self):
        """v3742r:72 - the bump still sits on Grief; the re-roll is the second pick's own"""
        o = run("reroll")
        r = step(o, "reroll-second")
        self.assertEqual(step(o, "second").get("grief"), 2, "the second pick already took back Grief's copy: %r" % o["steps"])
        self.assertEqual(r.get("grief"), 2, "re-rolling the second pick took back the FIRST pick's copy: %r" % r)
        self.assertIsNone(r.get("spirit"), "the re-roll left the old composed name filed beside the new one: %r" % r)
        self.assertIsNotNone(r.get("reroll"), "the re-rolled second pick was not filed under its new name: %r" % r)

    def test_3_a_clear_takes_back_only_the_held_pick(self):
        o = run("clear-second")
        c = step(o, "clear")
        self.assertEqual(c.get("mode"), "cleared")
        self.assertEqual(c.get("grief"), 2, "clearing the second pick took back the FIRST pick's copy: %r" % c)
        self.assertEqual(c.get("griefMem"), 2, c)
        self.assertIsNone(c.get("spirit"), "the clear left the second pick's own fresh filing behind: %r" % c)

    def test_4_a_reroll_or_clear_of_the_copy_pick_itself_takes_its_copy_back(self):
        """the half of REG-2267 that is right: the pick that made the copy, re-rolled or cleared, takes it back"""
        r = step(run("reroll-first"), "reroll-grief")
        self.assertIsNone(r.get("grief"), "re-rolling the copy pick itself left its copy behind (a copy with no pick): %r" % r)
        self.assertIsNone(r.get("griefMem"), r)
        self.assertEqual(r.get("griefHome"), "uni-weap", "the re-roll unfiled the Grief he already had: %r" % r)
        c = step(run("clear-first"), "clear")
        self.assertIsNone(c.get("griefMem"), "clearing the copy pick itself left its copy in the live count: %r" % c)
        self.assertIsNone(c.get("grief"), "the clear took the copy back in the live count only - d2r_copies still holds it "
                                          "and the next load puts it back: %r" % c)
        self.assertEqual(c.get("griefHome"), "uni-weap", "the clear unfiled the Grief he already had: %r" % c)
        self.assertTrue(c.get("dirty"), "the open planner was not told to draw the taken-back copy on close: %r" % c)

    def test_5_a_reroll_that_stops_early_still_takes_the_copy_back_on_disk(self):
        """the re-roll's new pick ends at the white-base sentence, before the pick's own write - the undo writes itself"""
        r = step(run("reroll-first-stops"), "reroll-white")
        self.assertIn("white, superior or low base", r.get("why", ""), "PREMISE: the re-rolled pick did not stop early: %r" % r)
        self.assertIsNone(r.get("griefMem"), r)
        self.assertIsNone(r.get("grief"), "the re-roll took the copy back in the live count only - d2r_copies still holds "
                                          "it and the next load puts it back: %r" % r)
        self.assertEqual(r.get("griefHome"), "uni-weap", r)

    def test_6_the_same_open_counts_once_and_a_later_open_counts_the_next(self):
        o = run("later-open")
        self.assertEqual(step(o, "grief-again").get("mode"), "already", "saving the same open again counted another copy")
        self.assertEqual(step(o, "grief-again").get("grief"), 2)
        self.assertEqual(step(o, "second").get("grief"), 2, "a different pick took back the copy: %r" % o["steps"])
        later = step(o, "grief-later-open")
        self.assertEqual(later.get("mode"), "copy", later)
        self.assertEqual(later.get("grief"), 3, "a later open of Grief did not file the next copy beside the first two: %r" % later)
        self.assertIn("copy 3", later.get("why", ""))


RED_PROOF = [
    {"why": "#183 (REG-2530) - the name-change undo fires on a DIFFERENT pick again, taking back the first pick's copy",
     "file": "bible.html",
     "find": "    if (_vpMade && _vpMade.token === token && _vpMade.id === entry.id && _vpMade.name && _vpMade.name !== nm) _vpCopyUndo(token, _vpMade.name);",
     "replace": "    if (_vpMade && _vpMade.token === token && _vpMade.name && _vpMade.name !== nm) _vpCopyUndo(token, _vpMade.name);",
     "matches": 1, "needs": "node"},
    {"why": "REG-2530 - an undo takes the copy back in the live count only; d2r_copies keeps it and the next load restores it",
     "file": "bible.html",
     "find": "    try { persistOwned(); } catch (eCp) {}\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
