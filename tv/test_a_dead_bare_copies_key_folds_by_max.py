# -*- coding: utf-8 -*-
"""#184 (REG-2531) - THE SET-PIECE RECONCILE FOLDS EVERY COPY COUNT BY MAX, AND THE SPEC THAT SAID IT DID NOT ASKED IT
SOMETHING ELSE.

GrokBot's V0 triage (2026-10-22, v3784, 2/2 headless) filed v3753:95 as REAL data loss: after folding a dead bare
copies key the slotted keeper read 3, not MAX(1,4) = 4. MEASURED on the shipped page in node, the fold is right: a lone
dead "Natalya's Totem": 4 beside an owned "Natalya's Totem (helm)" folds to 4. The 3 is the spec's FIRST seed. Its
second seedLoad registers a second init script on the same page; on the next load both run, navigator.webdriver is by
then the page's own non-configurable property, the second Object.defineProperty threw, the single catch swallowed it,
and every storage write after it was skipped - so the "MAX(1,4)" load ran on {helm: 3, bare: 2} and answered
MAX(3,2) = 3, correctly. The CI retry failed differently (no dead key at all): the page's own load-time pass, 1.5 s
after load, had already swept it. The spec now seeds before it flags webdriver, in its own step, and tells the
load-time pass it already ran.

This law pins both halves:
  * the fold, on the WHOLE page in node (tv/vault_page_node.py) in the owner world a spec runs in: a dead bare key
    above, below and beside an absent keeper, and an owned bare/slotted pair, each fold to the MAX of the two counts,
    on disk and in the live count, and the receipt keeps every prior count;
  * the spec's seed: its init-script body, cut from the spec file and run twice over a navigator whose webdriver is a
    prototype getter (as Chromium's is), lands the SECOND seed.
RED_PROOF below: each MAX turned into "keep the keeper's", and the spec's seed put back behind the flag.
"""
import io
import json
import os
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

import vault_page_node as VPN  # noqa: E402  (the whole page in node)

SPEC = os.path.join(ROOT, "tests", "v3753_set_piece_recount_and_sweep.spec.ts")
SEED_A = "  await page.addInitScript(({ owned, assign, copies, multiKeep, stamp }: any) => {\n"
SEED_B = "  }, { owned, assign, copies, multiKeep, stamp: !!stamp });\n"

BARE, HELM = "Natalya's Totem", "Natalya's Totem (helm)"

AUTOMATED = r"""
Object.defineProperty(navigator, 'webdriver', { get: function(){ return true; }, configurable: true });
location.protocol = 'file:'; location.href = 'file:///spec/bible.html'; location.origin = 'null'; location.host = ''; location.hostname = '';
"""


def _seed(owned, assign, copies):
    return ("localStorage.setItem('d2r_ownerClaim', '*');\n"
            "localStorage.setItem('d2r_owned', %s);\n"
            "localStorage.setItem('d2r_muleAssign', %s);\n"
            "localStorage.setItem('d2r_copies', %s);\n"
            "localStorage.setItem('d2r_multiKeep', '{}');\n"
            "localStorage.setItem('d2r_setPieceReconcile', JSON.stringify({ ver: 1e9, by: 'law' }));\n"
            % (json.dumps(json.dumps(owned)), json.dumps(json.dumps(assign)), json.dumps(json.dumps(copies))))


BODY = r"""
(function(){
var K = { helm: "Natalya's Totem (helm)", bare: "Natalya's Totem" };
function disk(k){ try { return JSON.parse(window.LSR.getItem(k) || 'null'); } catch (e) { return 'UNREADABLE'; } }
__AFTER_LOAD__
var before = disk('d2r_copies');
var res = window._setPieceReconcile({ force: true });
var c = disk('d2r_copies') || {}, ow = disk('d2r_owned') || [];
var rc = (res && res.receipt) || {};
OUT.r = { before: before, ran: !!(res && res.ran), stamped: !!(res && res.stamped), dead: rc.copiesDeadKeys || [],
          folded: (res && res.folded) || [], prior: rc.copiesPrior || {},
          helm: c[K.helm] == null ? null : c[K.helm], bare: c[K.bare] == null ? null : c[K.bare],
          helmMem: copies[K.helm] == null ? null : copies[K.helm], bareMem: copies[K.bare] == null ? null : copies[K.bare],
          ownedBare: ow.indexOf(K.bare) >= 0, ownedHelm: ow.indexOf(K.helm) >= 0 };
})();
"""

CASES = {
    # a lone dead bare key ABOVE an absent keeper (1): the spec's MAX(1,4)
    "above-absent": ([HELM], {HELM: "sets-rest"}, {BARE: 4}),
    # BELOW a present keeper: the keeper is not over-raised
    "below": ([HELM], {HELM: "sets-rest"}, {HELM: 3, BARE: 2}),
    # ABOVE a present keeper: the larger count is never lost
    "above-present": ([HELM], {HELM: "sets-rest"}, {HELM: 3, BARE: 4}),
    # an owned bare/slotted PAIR: the name folds, the count follows by MAX. Seeded AFTER the load, because the boot's own
    # owned-name pass already folds a pair it is handed (by MAX too) and the reconcile would then have nothing to fold.
    "pair": ([HELM], {HELM: "sets-rest"}, {HELM: 2}),
}

#: what a case does on the loaded page before the fold is asked
AFTER_LOAD = {
    "pair": "owned.add(K.bare); copies[K.bare] = 4; persistOwned();",
}

_RUNS = {}


def fold(case):
    if case not in _RUNS:
        owned, assign, copies = CASES[case]
        body = BODY.replace("__AFTER_LOAD__", AFTER_LOAD.get(case, ""))
        _RUNS[case] = VPN.run(body, prelude=AUTOMATED + _seed(owned, assign, copies), timeout=300)
    return _RUNS[case]


def _spec_seed_body():
    with io.open(SPEC, encoding="utf-8") as fh:
        s = fh.read()
    if s.count(SEED_A) != 1 or s.count(SEED_B) != 1:
        raise AssertionError("the spec's seedLoad anchors moved (%d, %d) - this law cannot find the seed it guards"
                             % (s.count(SEED_A), s.count(SEED_B)))
    i = s.index(SEED_A) + len(SEED_A)
    return s[i:s.index(SEED_B, i)]


SEED_RUNNER = r"""
var STORE = {};
var localStorage = { setItem: function(k, v){ STORE[k] = String(v); }, getItem: function(k){ return Object.prototype.hasOwnProperty.call(STORE, k) ? STORE[k] : null; },
                     removeItem: function(k){ delete STORE[k]; } };
/* Chromium's navigator under Playwright: webdriver is a getter on the prototype (answering true), so an init script's
   defineProperty makes an OWN, non-configurable property on the instance - and a second one with another getter throws */
function Navigator(){}
Object.defineProperty(Navigator.prototype, 'webdriver', { get: function(){ return true; }, configurable: true });
var navigator = new Navigator();
function seedLoad(args){ (function(__a){ var owned = __a.owned, assign = __a.assign, copies = __a.copies, multiKeep = __a.multiKeep, stamp = __a.stamp;
__BODY__
})(args); }
seedLoad({ owned: ["H"], assign: { H: 'sets-rest' }, copies: { H: 3, B: 2 }, multiKeep: {}, stamp: true });
seedLoad({ owned: ["H"], assign: { H: 'sets-rest' }, copies: { B: 4 }, multiKeep: {}, stamp: true });
process.stdout.write(JSON.stringify({ copies: JSON.parse(STORE.d2r_copies || 'null'), webdriver: navigator.webdriver,
                                      stamp: JSON.parse(STORE.d2r_setPieceReconcile || 'null') }));
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ADeadBareCopiesKeyFoldsByMax(unittest.TestCase):

    def test_0_the_page_boots_and_the_fold_runs_on_the_seed(self):
        o = fold("above-absent")
        self.assertEqual(o["__boot"]["errors"], [], "a page script did not run in node: %r" % o["__boot"])
        r = o["r"]
        self.assertEqual(r["before"], {BARE: 4}, "PREMISE: the load changed the seed before the fold: %r" % r)
        self.assertTrue(r["ran"] and r["stamped"], r)

    def test_1_a_dead_bare_key_above_an_absent_keeper_moves_onto_it(self):
        """v3753:95 - MAX(1,4) = 4, the spec's own question"""
        r = fold("above-absent")["r"]
        self.assertEqual(r["dead"], [BARE], r)
        self.assertEqual((r["helm"], r["helmMem"]), (4, 4), "a copy was lost folding the dead bare key: %r" % r)
        self.assertEqual((r["bare"], r["bareMem"]), (None, None), "the dead bare key was not swept: %r" % r)
        self.assertEqual(r["prior"], {BARE: 4, HELM: None}, "the receipt lost a prior count: %r" % r)

    def test_2_below_a_present_keeper_the_keeper_is_not_raised(self):
        r = fold("below")["r"]
        self.assertEqual(r["dead"], [BARE], r)
        self.assertEqual((r["helm"], r["helmMem"]), (3, 3), r)
        self.assertIsNone(r["bare"], r)

    def test_3_above_a_present_keeper_the_larger_count_is_kept(self):
        r = fold("above-present")["r"]
        self.assertEqual(r["dead"], [BARE], r)
        self.assertEqual((r["helm"], r["helmMem"]), (4, 4), "a count above the keeper's was dropped: %r" % r)
        self.assertEqual(r["prior"].get(HELM), 3, r)

    def test_4_an_owned_pair_folds_its_name_and_keeps_the_larger_count(self):
        r = fold("pair")["r"]
        self.assertEqual(r["before"], {BARE: 4, HELM: 2}, "PREMISE: the pair was not on disk when the fold ran: %r" % r)
        self.assertEqual(r["folded"], [BARE], "the owned bare/slotted pair did not fold: %r" % r)
        self.assertFalse(r["ownedBare"], r)
        self.assertTrue(r["ownedHelm"], r)
        self.assertEqual((r["helm"], r["helmMem"]), (4, 4), "the pair fold lost the larger count: %r" % r)
        self.assertIsNone(r["bare"], r)

    def test_5_the_specs_second_seed_lands(self):
        """the cause of the 3: the spec's init script, registered twice on one page, must land its second seed"""
        body = _spec_seed_body()
        prog = SEED_RUNNER.replace("__BODY__", body)
        p = subprocess.run([VPN.NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, (p.stderr or p.stdout)[-1500:])
        o = json.loads(p.stdout)
        self.assertEqual(o["copies"], {"B": 4}, "the spec's second seedLoad did not land - the load runs on the first "
                                                "seed, and the fold is asked a different question: %r" % o)
        self.assertTrue(o["webdriver"], "the page would not resolve the owner world (navigator.webdriver): %r" % o)
        self.assertEqual((o["stamp"] or {}).get("by"), "spec", "the load-time pass is not told it already ran: %r" % o)


RED_PROOF = [
    {"why": "#184 (REG-2531) - a dead bare copies key is folded by 'keep the keeper's', losing a count above it",
     "file": "bible.html",
     "find": "_mm = (_dk > _kk) ? _dk : _kk;",
     "replace": "_mm = _kk;",
     "matches": 1, "needs": "node"},
    {"why": "#184 (REG-2531) - an owned bare/slotted pair folds its count by 'keep the keeper's', losing the larger one",
     "file": "bible.html",
     "find": "          var merged = (bc > kc) ? bc : kc;\n",
     "replace": "          var merged = kc;\n",
     "matches": 1, "needs": "node"},
    {"why": "#184 (REG-2531) - the spec flags webdriver inside its seed again: a second seedLoad throws and lands nothing",
     "file": "tests/v3753_set_piece_recount_and_sweep.spec.ts",
     "find": "      localStorage.setItem('d2r_ownerClaim', '*');\n      localStorage.setItem('d2r_owned', JSON.stringify(owned));\n",
     "replace": "      localStorage.setItem('d2r_ownerClaim', '*');\n      Object.defineProperty(navigator, 'webdriver', { get: () => true });\n      localStorage.setItem('d2r_owned', JSON.stringify(owned));\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
