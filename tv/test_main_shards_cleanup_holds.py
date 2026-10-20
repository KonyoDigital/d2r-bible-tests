# -*- coding: utf-8 -*-
"""REG-2320 - THREE APP FIXES BEHIND MAIN'S RED PLAYWRIGHT SHARDS, PINNED IN NODE.

Main 4f487af9 had 28 red Playwright tests across 8 of 10 shards. Most were stale specs (his rulings moved
the routes: REG-2241 Anni/Torch shared + Gheed's muled, the 2026-10-19 war-stash list, v3766 per-copy cells,
v3767 witness intake, REG-2267 planner swap). Three were real app defects, and this law drives each one:

  1. A PERFECT BASE IS A KEEPER EVEN WHEN ITS RUNEWORDS ARE ALL FORGED (REG-2250 ruling, 2026-10-13).
     vaultPlannerFile proved a 4os Monarch perfect, then asked _vpRoute, whose suggestMule said "nothing left
     for it -> vendor it" (__throwout), so the pick came back "stays unfiled". _vpRoute(nm, keeperWhy) re-homes a
     vendor verdict to the socketed base mule ONLY when the caller proved the pick a keeper; every other route,
     an Unsorted verdict, and a board with no base mule are untouched.
  2. A SCROLL DURING THE STYLED TIP'S COLD-START WAIT DROPPED THE TIP (tv/control_ui.html, REG-2252 lane).
     say() waits ~380 ms before painting; reglue() saw #itip not yet .tip-say and took the item-card branch,
     hide(), so the pending row tip never opened. reglue() now leaves a pending tip alone (a disconnected host
     still hides), and the timer clears sayTimer when it fires so "pending" is readable.
  3. renderMultiKeep IS REACHABLE FROM THE PAGE (window.renderMultiKeep), the recount panel the v3753 spec drives.

Each function is cut out of the shipped file and run in node with stubs. A missing node raises. RED_PROOF below.
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
UI = os.path.join(HERE, "control_ui.html")
NODE = os.environ.get("NODE") or shutil.which("node")


def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def _cut(src, start, end):
    i = src.find(start)
    if i < 0:
        raise AssertionError("not found in the shipped file: %r" % start)
    j = src.find(end, i)
    if j < 0:
        raise AssertionError("end marker not found after %r" % start)
    return src[i:j]


def _node(prog):
    if not NODE:
        raise RuntimeError("node is required for this law (it does not skip)")
    p = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise AssertionError("node failed: " + (p.stderr or p.stdout)[-2000:])
    return json.loads(p.stdout.strip().splitlines()[-1])


VP_HARNESS = r"""
var window = {}, assign = {}, magicFinds = {}, VP_WHERE = 'the Vault planner', FILED = [];
var SG = null, MULES = { 'bases': { id: 'bases', name: 'SOCKETED' }, 'uni-weap': { id: 'uni-weap', name: 'UNI-WEAPONS' } };
function suggestMule(n){ return SG; }
function muleById(id){ return MULES[id] || null; }
function isSharedStash(n){ return false; }
window.vaultFile = function(nm, w, o){ FILED.push([nm, o.mule]); return { ok: true, mode: 'filed' }; };
%s
function run(sg, why, mules){ SG = sg; FILED = []; assign = {}; MULES = mules || { 'bases': { id: 'bases', name: 'SOCKETED' }, 'uni-weap': { id: 'uni-weap', name: 'UNI-WEAPONS' } };
  var r = _vpRoute('Monarch (4os)', why); return { r: r, filed: FILED }; }
var TH = { id: '__throwout', why: 'socketed Monarch - nothing left for it -> vendor it' };
var out = {
  keeper: run(TH, 'Monarch at 4 of 4 sockets - a perfect socketable base is a keeper, not vendor'),
  plain: run(TH, undefined),
  unsorted: run({ id: '__throwout', unsorted: true, why: 'x' }, 'keeper'),
  nobases: run(TH, 'keeper', { 'uni-weap': { id: 'uni-weap', name: 'UNI-WEAPONS' } }),
  other: run({ id: 'uni-weap', why: 'weapon slot' }, 'keeper')
};
console.log(JSON.stringify(out));
"""

RG_HARNESS = r"""
function make(state){
  var calls = [];
  var sayHost = state.host, el = state.el, sayTimer = state.timer;
  var o = { hide: function(){ calls.push('hide'); }, anchor: function(){ calls.push('anchor'); },
            reglue: %s };
  o.reglue();
  return calls;
}
function host(conn){ return { isConnected: conn, offsetParent: conn ? {} : null, getBoundingClientRect: function(){ return { width: 10, height: 10 }; } }; }
function tip(cls){ return { classList: { contains: function(c){ return c === cls; } } }; }
console.log(JSON.stringify({
  pending: make({ host: host(true), el: tip(''), timer: 7 }),
  pendingGone: make({ host: host(false), el: tip(''), timer: 7 }),
  open: make({ host: host(true), el: tip('tip-say'), timer: null }),
  card: make({ host: host(true), el: tip(''), timer: null }),
  none: make({ host: null, el: tip(''), timer: null })
}));
"""


class APerfectBaseIsFiled(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src = _read(BIBLE)
        cls.src = src
        fn = _cut(src, "  function _vpRoute(nm, keeperWhy){", "\n  function _vpCopyUndo(")
        cls.o = _node(VP_HARNESS % fn)

    def test_a_proven_keeper_vendor_verdict_files_to_the_base_mule(self):
        k = self.o["keeper"]
        self.assertTrue(k["r"]["filed"], k)
        self.assertEqual(k["filed"], [["Monarch (4os)", "bases"]])
        self.assertIn("perfect socketable base", k["r"]["why"], "the keeper reason is what he reads")

    def test_without_the_keeper_proof_a_vendor_verdict_stays_unfiled(self):
        p = self.o["plain"]
        self.assertFalse(p["r"]["filed"], p)
        self.assertEqual(p["filed"], [])
        self.assertIn("throw-out advice", p["r"]["why"])

    def test_an_unsorted_verdict_is_never_re_homed(self):
        self.assertEqual(self.o["unsorted"]["filed"], [])

    def test_no_base_mule_on_the_board_files_nothing(self):
        n = self.o["nobases"]
        self.assertEqual(n["filed"], [])
        self.assertIn("throw-out advice", n["r"]["why"], "with no base mule the vendor verdict stands as it was")

    def test_a_real_route_is_untouched_by_the_keeper_reason(self):
        self.assertEqual(self.o["other"]["filed"], [["Monarch (4os)", "uni-weap"]])

    def test_the_planner_hands_its_keeper_reason_to_the_router(self):
        self.assertEqual(self.src.count("var _pbRouted = _vpRoute(_pb.name, _pb.why);"), 1)

    def test_the_recount_painter_is_on_the_page(self):
        self.assertEqual(self.src.count("window.renderMultiKeep = renderMultiKeep;"), 1)


class APendingTipSurvivesAScroll(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ui = _read(UI)
        cls.ui = ui
        body = _cut(ui, "      reglue: function(){", "\n      /* ELEMENT-ANCHORED, not cursor-following.")
        body = body[len("      reglue: "):].rstrip().rstrip(",")
        cls.o = _node(RG_HARNESS % body)

    def test_a_pending_tip_is_left_alone(self):
        self.assertEqual(self.o["pending"], [], "a scroll in the cold-start wait must not hide or move the tip")

    def test_a_pending_tip_whose_host_left_is_hidden(self):
        self.assertEqual(self.o["pendingGone"], ["hide"])

    def test_an_open_tip_re_glues(self):
        self.assertEqual(self.o["open"], ["anchor"])

    def test_the_item_card_still_hides_on_scroll(self):
        self.assertEqual(self.o["card"], ["hide"])

    def test_no_host_hides(self):
        self.assertEqual(self.o["none"], ["hide"])

    def test_the_timer_says_when_it_has_fired(self):
        self.assertRegex(self.ui, r"sayTimer = setTimeout\(function\(\)\{\n\s+sayTimer = null;")


RED_PROOF = [
    {"why": "REG-2320 - without the re-home a proven perfect base is vendored and stays unfiled",
     "file": "bible.html",
     "find": "    if (keeperWhy && sg && sg.id === '__throwout' && !sg.unsorted){\n",
     "replace": "    if (false){\n", "matches": 1},
    {"why": "REG-2320 - an Unsorted verdict re-homed would file a name nothing knows",
     "file": "bible.html",
     "find": "    if (keeperWhy && sg && sg.id === '__throwout' && !sg.unsorted){\n",
     "replace": "    if (keeperWhy && sg && sg.id === '__throwout'){\n", "matches": 1},
    {"why": "REG-2320 - re-homing every route would move a weapon off its slot mule",
     "file": "bible.html",
     "find": "    if (keeperWhy && sg && sg.id === '__throwout' && !sg.unsorted){\n",
     "replace": "    if (keeperWhy && sg && !sg.unsorted){\n", "matches": 1},
    {"why": "REG-2320 - with no keeper proof the vendor verdict must stand",
     "file": "bible.html",
     "find": "    if (keeperWhy && sg && sg.id === '__throwout' && !sg.unsorted){\n",
     "replace": "    if (sg && sg.id === '__throwout' && !sg.unsorted){\n", "matches": 1},
    {"why": "REG-2320 - a board with no base mule must not get a filing to a missing locker",
     "file": "bible.html",
     "find": "      if (_kb) sg = { id: 'bases', why: String(keeperWhy) };\n",
     "replace": "      sg = { id: 'bases', why: String(keeperWhy) };\n", "matches": 1},
    {"why": "REG-2320 - the keeper reason is what he reads on the filing",
     "file": "bible.html",
     "find": "      if (_kb) sg = { id: 'bases', why: String(keeperWhy) };\n",
     "replace": "      if (_kb) sg = { id: 'bases', why: '' };\n", "matches": 1},
    {"why": "REG-2320 - the planner must hand the router its keeper proof",
     "file": "bible.html",
     "find": "        var _pbRouted = _vpRoute(_pb.name, _pb.why);\n",
     "replace": "        var _pbRouted = _vpRoute(_pb.name);\n", "matches": 1},
    {"why": "REG-2320 - the recount painter must be reachable from the page",
     "file": "bible.html",
     "find": "  try { window.renderMultiKeep = renderMultiKeep; } catch (eRmk) {}",
     "replace": "  try { } catch (eRmk) {}", "matches": 1},
    {"why": "REG-2320 - a scroll in the cold-start wait killed every pending row tip",
     "file": "control_ui.html",
     "find": "        if (sayTimer){\n          if (!sayHost.isConnected) return this.hide();\n          return;\n        }",
     "replace": "", "matches": 1},
    {"why": "REG-2320 - a pending tip whose host was removed must still clear",
     "file": "control_ui.html",
     "find": "        if (sayTimer){\n          if (!sayHost.isConnected) return this.hide();\n          return;\n        }",
     "replace": "        if (sayTimer){\n          return;\n        }", "matches": 1},
    {"why": "REG-2320 - an open tip must still re-glue, not be treated as pending",
     "file": "control_ui.html",
     "find": "        if (sayTimer){\n          if (!sayHost.isConnected) return this.hide();\n          return;\n        }",
     "replace": "        if (!sayTimer){\n          if (!sayHost.isConnected) return this.hide();\n          return;\n        }", "matches": 1},
    {"why": "REG-2320 - a timer that never clears itself leaves every later scroll reading pending",
     "file": "control_ui.html",
     "find": "          sayTimer = null;   /* REG-2320 — the cold-start wait is over; reglue() reads this to tell \"pending\" from \"open\" */\n",
     "replace": "", "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
