# -*- coding: utf-8 -*-
"""REG-2534 - A HELD PLANNER PICK'S UNDO TAKES BACK THE ONE COPY THAT PICK COUNTED, NEVER A COPY ANYTHING ELSE COUNTED.

The V1 round-3 review of REG-2530 (reproduced on ed832f3d9, the whole page in node, real doors): Grief is filed, a
planner pick counts copy 2, another tab of the board counts a third Grief and writes d2r_copies {Grief: 3}, and this tab
merges it through its own window._tabSyncMerge (what the 'storage' listener calls) - live and disk read 3. Then the held
pick is cleared, or re-rolled: _vpCopyUndo put back the count it had SEEN AT PICK TIME (1), so Grief was gone from the
live count AND from disk - the other tab's copy went with the pick's, and REG-2530's own write put the loss on disk at
once. Expected 2. The same can happen in one tab: the folder poll and the low-base register count a re-read socketed
base while a pick of it is held. Nothing was said. [[unknown-stays-unknown]]

THE RULE: an undo takes ONE copy off the count as it is now, and only while that count is above the one the pick started
from. At or below it the count was already lowered elsewhere (his HAVE stepper walked it down, another tab lowered it):
nothing more is taken, and the answer says so in words.

Driven on the WHOLE page in node (tv/vault_page_node.py), the world a Playwright file:// page is, real doors only:
  * another tab's +1, merged by _tabSyncMerge, then a CLEAR of the held pick: 2 on disk and live (the review's repro);
  * the same, then a RE-ROLL of the held pick (same id, a new name): 2 on disk and live;
  * this tab's own HAVE stepper (+1 under a keep-target of 4) while the pick is held, then a clear: 2;
  * this tab's own reader: the low-base register counts a re-read 4os Monarch while a pick of it is held, then a
    clear: 2 (a fresh install, where the router keeps it in SOCKETED);
  * the control: no other door, a clear takes the pick's copy back (Grief back to one);
  * his HAVE stepper walks the count DOWN while the pick is held (copy 4 -> 3, the count it started from), then a
    clear and, separately, a re-roll: 3 stays on disk and live, and the answer says nothing more was taken back.
RED_PROOF below: the absolute restore put back (b.prev) turns the foreign-copy cases red; the guard removed (one off
whatever the count is) turns the walk-down cases red.
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

#: Grief owned and filed to uni-weap; the copy count and the keep-targets are each scenario's own
SEED = r"""
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify(['Grief']));
localStorage.setItem('d2r_copies', JSON.stringify(__COPIES__));
localStorage.setItem('d2r_multiKeep', JSON.stringify(__WANT__));
localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'Grief': 'uni-weap' }));
"""

BODY = r"""
(function(){
var W = window;
function disk(k){ try { return JSON.parse(W.LSR.getItem(k) || 'null'); } catch (e) { return 'UNREADABLE'; } }
function now(label, r){
  var c = disk('d2r_copies') || {};
  steps.push({ label: label, mode: (r && r.mode) || null, why: (r && r.why) || '',
               disk: (c.Grief == null ? null : c.Grief), mem: (copies.Grief == null ? null : copies.Grief),
               home: (disk('d2r_muleAssign') || {}).Grief || null });
}
/* the specs' stubs (v3740/v3742r): each pick resolves to its own name; the stores, the router and the doors are the page's */
W._cbItem = function(id){ return { id: id }; };
W._cbShown = function(entry){ return { name: entry && entry.name, q: 'r', base: '' }; };
W._vaultResolveName = function(n){ return n; };
W._vaultNameAmbiguity = function(){ return null; };
W.vaultHandAdd = function(){ return { ok: true }; };
W._vaultPlannerOn = true;
var S = __S__, steps = [];
var G = { id: 'ENTRY-GRIEF', name: 'Grief' };
now('pick', W.vaultPlannerFile(G, 'vp-2534'));
if (S.door === 'tab'){
  /* another tab of this board counts one more Grief and writes the store; this tab merges it through its own door */
  var oldRaw = W.LSR.getItem('d2r_copies');
  var theirs = JSON.parse(oldRaw || '{}'); theirs.Grief = (theirs.Grief || 1) + 1;
  var newRaw = JSON.stringify(theirs);
  H.RAW.set('d2r_copies', newRaw);
  OUT.merge = W._tabSyncMerge('d2r_copies', oldRaw, newRaw);
  now('other door');
} else if (S.door === 'have-up' || S.door === 'have-down'){
  /* his own HAVE stepper on the multi-copy panel, while the pick is held */
  W.vaultCopyAdjust('Grief', S.door === 'have-up' ? 1 : -1);
  now('other door');
}
var end = (S.end === 'clear') ? W.vaultPlannerFile(null, 'vp-2534')
        : W.vaultPlannerFile({ id: 'ENTRY-GRIEF', name: 'Grief of the Re-roll' }, 'vp-2534');
now(S.end, end);
OUT.steps = steps;
})();
"""

SCENARIOS = {
    "tab-clear":       {"door": "tab", "end": "clear", "copies": {}, "want": {}},
    "tab-reroll":      {"door": "tab", "end": "reroll", "copies": {}, "want": {}},
    "have-up-clear":   {"door": "have-up", "end": "clear", "copies": {}, "want": {"Grief": 4}},
    "none-clear":      {"door": "none", "end": "clear", "copies": {}, "want": {}},
    "have-down-clear":  {"door": "have-down", "end": "clear", "copies": {"Grief": 3}, "want": {}},
    "have-down-reroll": {"door": "have-down", "end": "reroll", "copies": {"Grief": 3}, "want": {}},
}

#: the same tab's own reader, as the review named it: a socketed base re-read while a planner pick of it is held. A fresh
#: install (nothing forged - a board seeded with data is claimed as his and gets his Chronicle, where the router would
#: vendor the base and the register would not count it), so the first open files the 4os Monarch through the planner's
#: own door, and the router keeps it in SOCKETED for the register.
LOWBASE_SEED = ""

LOWBASE_BODY = r"""
(function(){
var W = window, L = 'Monarch (4os)', steps = [];
function disk(k){ try { return JSON.parse(W.LSR.getItem(k) || 'null'); } catch (e) { return 'UNREADABLE'; } }
function now(label, r){ var c = disk('d2r_copies') || {};
  steps.push({ label: label, mode: (r && r.mode) || null, why: (r && r.why) || '', disk: (c[L] == null ? null : c[L]),
               mem: (copies[L] == null ? null : copies[L]), home: (disk('d2r_muleAssign') || {})[L] || null }); }
var d = W._cbDb(), code = Object.keys(d.b).find(function(c){ return d.b[c][0] === 'Monarch'; });
var e = W._cbEntryFor(W._cbItem('b:' + code)); e.sockets = 4; e.eth = false;
W._vaultPlannerOn = true;
OUT.forged = Object.keys(disk('d2r_rwMade') || {}).length;
now('first open', W.vaultPlannerFile(e, 'vp-2534-first'));
now('pick', W.vaultPlannerFile(e, 'vp-2534-lowbase'));
OUT.register = W._autoRegisterLowBase('Monarch (4os low base)', null);
now('other door');
now('clear', W.vaultPlannerFile(null, 'vp-2534-lowbase'));
OUT.steps = steps;
})();
"""

_RUNS = {}


def run(name):
    if name == "lowbase-clear":
        if name not in _RUNS:
            _RUNS[name] = VPN.run(LOWBASE_BODY, prelude=LOWBASE_SEED, timeout=300)
        return _RUNS[name]
    if name not in _RUNS:
        sc = SCENARIOS[name]
        seed = SEED.replace("__COPIES__", json.dumps(sc["copies"])).replace("__WANT__", json.dumps(sc["want"]))
        body = BODY.replace("__S__", json.dumps({"door": sc["door"], "end": sc["end"]}))
        _RUNS[name] = VPN.run(body, prelude=AUTOMATED + seed, timeout=300)
    return _RUNS[name]


def step(o, label):
    for s in o.get("steps") or []:
        if s.get("label") == label:
            return s
    raise AssertionError("no step %r in %r" % (label, o.get("steps")))


NOTHING_MORE = "nothing more of Grief was taken back"


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AHeldPicksUndoTakesBackOnlyItsOwnCopy(unittest.TestCase):

    def test_0_premise_the_pick_counts_a_copy_and_the_other_door_lands(self):
        for name, sc in SCENARIOS.items():
            o = run(name)
            self.assertEqual(o["__boot"]["errors"], [], "%s: a page script did not run in node: %r" % (name, o["__boot"]))
            p = step(o, "pick")
            want = (sc["copies"].get("Grief") or 1) + 1
            self.assertEqual((p["mode"], p["disk"], p["mem"]), ("copy", want, want),
                             "%s - PREMISE: the planner pick did not count copy %d: %r" % (name, want, p))
        t = run("tab-clear")
        self.assertTrue((t.get("merge") or {}).get("merged"), "PREMISE: this tab did not merge the other tab's write: %r" % t.get("merge"))
        for name, n in (("tab-clear", 3), ("tab-reroll", 3), ("have-up-clear", 3), ("have-down-clear", 3), ("have-down-reroll", 3)):
            d = step(run(name), "other door")
            self.assertEqual((d["disk"], d["mem"]), (n, n), "%s - PREMISE: the other door did not move the count to %d: %r" % (name, n, d))

    def test_1_a_clear_keeps_the_copy_another_tab_counted(self):
        """the review's repro: pick (2), another tab's +1 merged (3), clear -> 2, not gone"""
        c = step(run("tab-clear"), "clear")
        self.assertEqual(c["mode"], "cleared", c)
        self.assertEqual(c["mem"], 2, "the clear took the other tab's copy with the pick's (live count): %r" % c)
        self.assertEqual(c["disk"], 2, "the clear wrote the other tab's copy away on disk: %r" % c)
        self.assertIn("the copy of Grief this pick counted is taken back (2 counted now)", c["why"], c)
        self.assertEqual(c["home"], "uni-weap", c)

    def test_2_a_reroll_keeps_the_copy_another_tab_counted(self):
        r = step(run("tab-reroll"), "reroll")
        self.assertEqual(r["mem"], 2, "re-rolling the held pick took the other tab's copy with it (live count): %r" % r)
        self.assertEqual(r["disk"], 2, "re-rolling the held pick wrote the other tab's copy away on disk: %r" % r)
        self.assertEqual(r["home"], "uni-weap", r)

    def test_3_a_clear_keeps_the_copy_his_own_have_stepper_counted(self):
        c = step(run("have-up-clear"), "clear")
        self.assertEqual((c["disk"], c["mem"]), (2, 2), "the clear took the copy his HAVE stepper counted: %r" % c)

    def test_3b_a_clear_keeps_the_copy_this_tabs_own_reader_counted(self):
        """the same-tab shape the review read in the code: the low-base register counts a re-read socketed base"""
        o = run("lowbase-clear")
        self.assertEqual(o["__boot"]["errors"], [], "a page script did not run in node: %r" % o["__boot"])
        self.assertEqual(o.get("forged"), 0, "PREMISE: this is not a fresh install - the router would vendor the base")
        f = step(o, "first open")
        self.assertEqual((f["mode"], f["home"]), ("filed", "bases"), "PREMISE: the first open did not file the 4os Monarch: %r" % f)
        p, d, c = step(o, "pick"), step(o, "other door"), step(o, "clear")
        self.assertEqual((p["mode"], p["disk"]), ("copy", 2), "PREMISE: the planner pick of the filed 4os Monarch did not count copy 2: %r" % p)
        self.assertEqual((o.get("register") or {}).get("mode"), "copy", "PREMISE: the low-base register did not count the re-read: %r" % o.get("register"))
        self.assertEqual((d["disk"], d["mem"]), (3, 3), "PREMISE: the re-read did not reach 3: %r" % d)
        self.assertEqual((c["disk"], c["mem"]), (2, 2), "the clear took the copy this tab's reader counted with the pick's: %r" % c)
        self.assertEqual(c["home"], "bases", c)

    def test_4_the_control_a_clear_still_takes_the_picks_own_copy(self):
        c = step(run("none-clear"), "clear")
        self.assertIsNone(c["mem"], "a clear with nothing else counted left the pick's copy in the live count: %r" % c)
        self.assertIsNone(c["disk"], "a clear with nothing else counted left the pick's copy on disk: %r" % c)
        self.assertIn("taken back (1 counted now)", c["why"], c)
        self.assertNotIn(NOTHING_MORE, c["why"], c)

    def test_5_a_count_already_walked_down_is_left_alone_and_said(self):
        """copy 4 counted by the pick, his HAVE stepper walks it to 3 (where the pick started): nothing more is taken"""
        for name, label in (("have-down-clear", "clear"), ("have-down-reroll", "reroll")):
            e = step(run(name), label)
            self.assertEqual(e["mem"], 3, "%s took a second copy off a count he had already walked down (live): %r" % (name, e))
            self.assertEqual(e["disk"], 3, "%s took a second copy off a count he had already walked down (disk): %r" % (name, e))
            self.assertIn(NOTHING_MORE, e["why"], "%s left the count alone without saying so: %r" % (name, e))
            self.assertIn("3 counted now, not above the 3 there were before this pick", e["why"], e)


RED_PROOF = [
    {"why": "REG-2534 - the undo puts back the count it saw at pick time again, so a copy another tab or door counted "
            "while the pick was held is taken with it, on disk",
     "file": "bible.html",
     "find": "      var cur = (copies[b.name] > 0) ? copies[b.name] : 1;\n      if (cur > b.prev){\n"
             "        if (cur - 1 > 1) copies[b.name] = cur - 1;\n",
     "replace": "      var cur = b.prev + 1;\n      if (cur > b.prev){\n"
                "        if (b.prev > 1) copies[b.name] = b.prev;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2534 - the undo takes one off whatever the count is, so a count he already walked down loses a second copy",
     "file": "bible.html",
     "find": "      var cur = (copies[b.name] > 0) ? copies[b.name] : 1;\n      if (cur > b.prev){\n",
     "replace": "      var cur = (copies[b.name] > 0) ? copies[b.name] : 1;\n      if (true){\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
