# -*- coding: utf-8 -*-
"""REG-2537 - WANT NEVER WRITES HAVE: A KEEP-TARGET MOVES OR GOES AND THE COPIES HE HAS STAY COUNTED.

The V1 round-3 review (reproduced on ed832f3d9, the whole page in node): the Multi-copy Keepers panel's WANT controls
were d2r_copies writers. Harlequin Crest at copies 3, want 3: vaultTargetBump(-1) clamped the copy count down to the new
target (copies 2), and vaultMultiKeepRemove deleted the count outright (copies gone = 1). Copies counted by intake, the
planner (REG-2530..2534) or his own HAVE stepper were dropped by a control about what he WANTS, and nothing asked or said
so. Pre-existing; found by the review because d2r_copies is this track's store. [[unknown-stays-unknown]]

THE RULE: WANT is the target, HAVE is the count. A target moves or goes and the count stays. The one control that lowers
a count is HAVE, in his hands: the ✕ on a row with NO target resets an inflated count to one (#76 v3753) - and it asks
first, in words, naming how many are counted; an answer of no changes nothing and says so.

Driven on the WHOLE page in node (tv/vault_page_node.py), the panel's own functions, reading d2r_copies on disk and the
live count:
  * WANT 3 -> 2 below a HAVE of 3: the count stays 3; WANT 2 -> 1 (the target goes): the count stays 3; a WANT step on a
    name with no target never reaches the reset (nothing asked, the count stays);
  * the ✕ on a target row: the target goes, the count stays 3;
  * the ✕ on an inflated set piece with no target: it asks ("... 3 are counted now ..."); a no keeps 3 and the status
    line says nothing was reset; a yes resets it to one.
RED_PROOF below: the WANT clamp put back; the target ✕ deleting the count again; the reset done without asking; a WANT
step sent through the ✕ again.
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

SEED = r"""
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify(['Harlequin Crest', 'Gore Rider', "Natalya's Totem (helm)"]));
localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'Harlequin Crest': 'uni-armor', 'Gore Rider': 'uni-armor', "Natalya's Totem (helm)": 'sets-rest' }));
localStorage.setItem('d2r_copies', JSON.stringify({ 'Harlequin Crest': 3, 'Gore Rider': 3, "Natalya's Totem (helm)": 3 }));
localStorage.setItem('d2r_multiKeep', JSON.stringify({ 'Harlequin Crest': 3, 'Gore Rider': 2 }));
"""

BODY = r"""
(function(){
var W = window;
function disk(k){ try { return JSON.parse(W.LSR.getItem(k) || 'null'); } catch (e) { return 'UNREADABLE'; } }
function look(label, n, r){
  var c = disk('d2r_copies') || {}, mk = disk('d2r_multiKeep') || {};
  var st = document.getElementById('vault-status');
  steps.push({ label: label, name: n, disk: (c[n] == null ? null : c[n]), mem: (copies[n] == null ? null : copies[n]),
               /* REG-2900 - a keeper is stored {want, dest}: the target is its want */
               want: (mk[n] == null ? null : ((typeof mk[n] === 'object') ? mk[n].want : mk[n])), result: r || null, status: st ? String(st.textContent || '') : null });
}
var steps = [], ASKED = [], ANSWER = false;
W.confirm = function(q){ ASKED.push(String(q)); return ANSWER; };
var HC = 'Harlequin Crest', GR = 'Gore Rider', NT = "Natalya's Totem (helm)";
OUT.canon = { hc: W._vfCanon ? W._vfCanon(HC) : HC, gr: W._vfCanon ? W._vfCanon(GR) : GR, nt: W._vfCanon ? W._vfCanon(NT) : NT };
look('seed hc', HC); look('seed gr', GR); look('seed nt', NT);
W.vaultTargetBump(HC, -1); look('want 3 to 2', HC);
W.vaultTargetBump(HC, -1); look('want 2 to 1', HC);
W.vaultMultiKeepRemove(GR); look('target row removed', GR);
/* a WANT step on a name with no target (the panel draws no WANT stepper there; a caller still may): never a HAVE reset */
W.vaultTargetBump(NT, -1); look('want down with no target', NT);
OUT.askedByWant = ASKED.slice();
ANSWER = false; var no = W.vaultMultiKeepRemove(NT); look('reset answered no', NT, no);
OUT.askedNo = ASKED.slice();
ANSWER = true; var yes = W.vaultMultiKeepRemove(NT); look('reset answered yes', NT, yes);
OUT.asked = ASKED.slice();
OUT.steps = steps;
})();
"""

_OUT = {}


def measured():
    if "o" not in _OUT:
        _OUT["o"] = VPN.run(BODY, prelude=SEED, timeout=300)
    return _OUT["o"]


def step(o, label):
    for s in o.get("steps") or []:
        if s.get("label") == label:
            return s
    raise AssertionError("no step %r in %r" % (label, o.get("steps")))


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class WantNeverWritesHave(unittest.TestCase):

    def test_0_premise_the_seed_is_what_the_panel_reads(self):
        o = measured()
        self.assertEqual(o["__boot"]["errors"], [], "a page script did not run in node: %r" % o["__boot"])
        self.assertEqual(o["canon"], {"hc": "Harlequin Crest", "gr": "Gore Rider", "nt": "Natalya's Totem (helm)"},
                         "PREMISE: the panel's canon moved one of the seeded names - this law would read a dead key")
        self.assertEqual((step(o, "seed hc")["disk"], step(o, "seed hc")["mem"], step(o, "seed hc")["want"]), (3, 3, 3))
        self.assertEqual((step(o, "seed gr")["mem"], step(o, "seed gr")["want"]), (3, 2))
        self.assertEqual((step(o, "seed nt")["mem"], step(o, "seed nt")["want"]), (3, None))

    def test_1_a_lowered_target_keeps_the_count(self):
        o = measured()
        a = step(o, "want 3 to 2")
        self.assertEqual(a["want"], 2, "PREMISE: the WANT stepper did not move the target: %r" % a)
        self.assertEqual((a["disk"], a["mem"]), (3, 3), "lowering WANT clamped the copies he has: %r" % a)
        b = step(o, "want 2 to 1")
        self.assertIsNone(b["want"], "PREMISE: WANT 2 -> 1 did not remove the target: %r" % b)
        self.assertEqual((b["disk"], b["mem"]), (3, 3), "the target going took the count with it: %r" % b)

    def test_2_removing_a_target_row_keeps_the_count(self):
        r = step(measured(), "target row removed")
        self.assertIsNone(r["want"], "PREMISE: the ✕ did not remove the keep-target: %r" % r)
        self.assertEqual((r["disk"], r["mem"]), (3, 3), "removing a keep-target deleted the copies he has: %r" % r)

    def test_2b_a_want_step_never_reaches_the_reset(self):
        o = measured()
        w = step(o, "want down with no target")
        self.assertEqual(o["askedByWant"], [], "a WANT step asked to reset the count he has: %r" % o["askedByWant"])
        self.assertEqual((w["disk"], w["mem"], w["want"]), (3, 3, None), "a WANT step on a name with no target moved its count: %r" % w)

    def test_3_the_inflated_count_reset_asks_first_and_a_no_changes_nothing(self):
        o = measured()
        self.assertEqual(len(o["askedNo"]), 1, "the reset of an inflated count did not ask first: %r" % o["askedNo"])
        self.assertIn("3 are counted now", o["askedNo"][0], "the question does not say how many are counted: %r" % o["askedNo"])
        n = step(o, "reset answered no")
        self.assertEqual((n["disk"], n["mem"]), (3, 3), "a no to the reset still dropped copies: %r" % n)
        self.assertEqual((n["result"] or {}).get("refused"), "not-confirmed", n)
        self.assertIn("nothing was reset", n["status"] or "", "a no to the reset was not said on the board: %r" % n)

    def test_4_a_yes_resets_the_inflated_count_to_one(self):
        y = step(measured(), "reset answered yes")
        self.assertTrue((y["result"] or {}).get("ok"), y)
        self.assertIsNone(y["mem"], "a yes to the reset left the inflated count: %r" % y)
        self.assertIsNone(y["disk"], "a yes to the reset did not reach d2r_copies: %r" % y)


RED_PROOF = [
    {"why": "REG-2537 - lowering a keep-target clamps the copies he has down to it again",
     "file": "bible.html",
     "find": "_mkSetWant(n,nt); try{ (typeof persist==='function')?persist():persistOwned(); }catch(e){} renderMultiKeep(); renderVaultRegistered(); };\n",
     "replace": "_mkSetWant(n,nt); if(copies[n]&&copies[n]>nt) copies[n]=nt; try{ (typeof persist==='function')?persist():persistOwned(); }catch(e){} renderMultiKeep(); renderVaultRegistered(); };\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2537 - removing a keep-target deletes the copy count again",
     "file": "bible.html",
     "find": "    if (_mkWant(n) > 1) delete multiKeep[n];\n",
     "replace": "    if (_mkWant(n) > 1){ delete multiKeep[n]; delete copies[n]; }\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2537 - the inflated-count reset drops copies without asking",
     "file": "bible.html",
     "find": "        try { yes = !!window.confirm(ask); } catch (eAsk) { yes = false; }\n",
     "replace": "        yes = true;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2537 - a WANT step below two goes through the ✕ again, so lowering a target can reach the HAVE reset",
     "file": "bible.html",
     "find": "var nt=multiTarget(n)+d; if(nt<2) delete multiKeep[n]; else _mkSetWant(n,nt);",
     "replace": "var nt=multiTarget(n)+d; if(nt<2){ window.vaultMultiKeepRemove(n); return; } _mkSetWant(n,nt);",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
