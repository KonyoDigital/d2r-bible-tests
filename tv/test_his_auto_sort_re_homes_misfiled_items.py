# -*- coding: utf-8 -*-
"""REG-2023 - HIS AUTO-SORT CLICK ALSO RE-HOMES WHAT THE ROUTER NOW PLACES ELSEWHERE, AND THE EMPTY DOCK NEVER SAYS
"PERFECT ORDER" OVER A MISFILED LOCKER. #269, GrokBot ticks 411 and 412 on v3616.

GrokBot, on his v3616 board: VAULT INTEGRITY "3 issues · 3 auto-fixable" - Dwarf Star, Enigma, Raven Frost "belongs in
SHARED STASH" (each filed in an old drawer before the war rule) - sitting directly ABOVE the empty dock's "every owned
item has a home - the vault is in perfect order", with SHARED STASH reading "empty locker". His ask was one click that
leaves the vault "assembled correctly and organized within the mules". Now:
  - the click MOVES the audit's own misroute rows through the door's move (which refuses a HARDENED row);
  - a home his OWN hand chose stays his (a hand row this button did not make);
  - the empty dock asks the integrity check before it claims perfect order.
Driven on the SHIPPED page in a scratch Chrome. NO CHROME AT ALL = a declared skip, never a pass.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_a_sweep_never_reticks_what_he_unticked as H  # noqa: E402  (its Board drives the shipped page)

_B = {}


def board():
    if "b" not in _B:
        _B["b"] = H.Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


def _filed(mule, source, where=None):
    row = {"mule": mule, "holder": mule, "source": source, "at": "2026-10-07T08:00:00.000Z", "by": "reader",
           "sessions": [], "looks": [{"id": "s_1", "frame": "1_1", "conf": 0.9}, {"id": "s_2", "frame": "2_1", "conf": 0.9}],
           "ver": "law"}
    if source == "hand":
        row.update({"by": "hand", "where": where or "the mule window"})
    return row


def _seed():
    board().seed({
        "d2r_owned": ["Enigma", "Raven Frost", "Nokozan Relic"],
        "d2r_muleAssign": {"Enigma": "runewords", "Raven Frost": "uni-small", "Nokozan Relic": "uni-small"},
        "d2r_vaultProv": {"Enigma": _filed("runewords", "stash"),
                          "Raven Frost": _filed("uni-small", "hand", "the mule window"),
                          "Nokozan Relic": _filed("uni-small", "stash")},
    })


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class HisAutoSortReHomesMisfiledItems(unittest.TestCase):

    def test_the_click_moves_a_misfiled_item_and_leaves_his_own_placement(self):
        _seed()
        o = board().run("try { window.switchTab('vault'); } catch(e){}"
                        "OUT.mis0 = window._vaultAudit().findings.filter(function(f){ return f.kind === 'misroute'; }).map(function(f){ return f.item; }).sort();"
                        "OUT.dock0 = (document.querySelector('.vault-dock') || {getAttribute: function(){ return null; }}).getAttribute('data-misfiled');"
                        "OUT.r = window.vaultAutoSortByHand();"
                        "OUT.a = JSON.parse(window.LSR.getItem('d2r_muleAssign') || '{}');")
        self.assertEqual(o["mis0"], ["Enigma", "Raven Frost"], "premise: the audit does not see the two misfiled war items %r" % o["mis0"])
        self.assertEqual(o["dock0"], "1", "the empty dock was not told some filed items sit in the wrong locker")
        self.assertEqual(o["a"].get("Enigma"), "shared", "his click left Enigma in the wrong locker: %r" % o["a"])
        self.assertEqual(o["a"].get("Raven Frost"), "uni-small", "his click moved an item HIS hand placed")
        self.assertIn("Raven Frost", o["r"]["keptHand"], o["r"])
        self.assertEqual(o["a"].get("Nokozan Relic"), "uni-small", "the control: a correctly filed item moved")

    def test_the_empty_dock_says_perfect_order_only_when_nothing_is_misfiled(self):
        board().seed({"d2r_owned": ["Nokozan Relic"], "d2r_muleAssign": {"Nokozan Relic": "uni-small"},
                      "d2r_vaultProv": {"Nokozan Relic": _filed("uni-small", "stash")}})
        o = board().run("try { window.switchTab('vault'); } catch(e){} window.renderVault && window.renderVault();"
                        "OUT.m = (document.querySelector('.vault-dock') || {getAttribute: function(){ return null; }}).getAttribute('data-misfiled');")
        self.assertEqual(o["m"], "0", "a vault with nothing misfiled was told it has misfiled items")


RED_PROOF = [
    {"why": "REG-2023 - his click leaves an item the router now places elsewhere in its old locker",
     "file": "bible.html",
     "find": "        var mv = window.vaultFile(f.item, null, { move: true, mule: f.to, by: 'Auto-Sort (his click)' });\n",
     "replace": "        var mv = { ok: false, why: 'sabotaged' };\n",
     "matches": 1},
    {"why": "REG-2023 - his click moves a home his own hand chose",
     "file": "bible.html",
     "find": "        if (pr && pr.kind !== 'owned' && pr.source === 'hand' && !/Auto-Sort/.test(String(pr.where || ''))){ out.keptHand.push(f.item); return; }\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2023 - the empty dock claims perfect order over a misfiled locker again",
     "file": "bible.html",
     "find": "      dock.setAttribute('data-misfiled', _misN ? '1' : '0');\n",
     "replace": "      dock.setAttribute('data-misfiled', '0');\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
