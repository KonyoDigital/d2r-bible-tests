# -*- coding: utf-8 -*-
"""REG-2533 (the #183 sweep) - A PLANNER PICK OF AN ITEM HE HAS FILED IS ANOTHER COPY, WHATEVER THE ROUTER NOW SAYS.

Found sweeping #183's class (a copy that never reaches d2r_copies): _vpRoute answered "already filed" only AFTER its
advice checks, so a pick of an item he had filed by hand, whose router verdict had since become throw-out advice,
answered "<name> stays unfiled - throw-out advice - ..." about an item sitting in his mule, and a later open counted no
copy. Measured on the shipped page in node: Axe of Fechmar, owned and filed by hand to UNI-WEAPONS, is "trade value
TRASH" to the router; a later planner open of it said it stays unfiled, d2r_copies never moved, and his second Axe was
lost without a word. The planner's own rule is that a later open of a filed name files another copy beside it.

A filed name now answers 'already' before the router is even asked, so the copy is counted and the sentence says where
it went; the filing is not moved and nothing is re-filed, and a router that cannot answer at all (it throws) no longer
turns a filed pick into "nothing was filed". The router's disagreement is still the vault audit's to show.
Driven on the WHOLE page in node (tv/vault_page_node.py), in the owner world a spec runs in, through the real doors; the
router is taken down by a patch to the page's own suggestMule (a closure of the vault script, out of a stub's reach).
RED_PROOF below: the early 'already' answer removed; the router asked before it again.
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

BODY = r"""
(function(){
var W = window;
function disk(k){ try { return JSON.parse(W.LSR.getItem(k) || 'null'); } catch (e) { return 'UNREADABLE'; } }
var row = W._cbHandCatalog('Axe of Fechmar').rows.filter(function(r){ return r.name === 'Axe of Fechmar' && r.q === 'u'; })[0];
OUT.row = row || null;
if (!row) return;
var add = W.vaultHandAdd('Axe of Fechmar', null, { kind: 'unique' });
var nm = add && add.name;
OUT.add = add ? { ok: add.ok, mode: add.mode || null, name: add.name || null } : null;
OUT.advice = W.suggestMule(nm);
var put = W.vaultFile(nm, { by: 'hand', at: new Date().toISOString(), where: 'his hand, in the law' }, { mule: 'uni-weap' });
OUT.put = put ? { ok: put.ok, mode: put.mode || null, mule: put.mule || null } : null;
W._vaultPlannerOn = true;
var e = W._cbEntryFor(W._cbItem(row.id));
var r1 = W.vaultPlannerFile(e, 'tok-later-open');
var a1 = disk('d2r_muleAssign') || {}, c1 = disk('d2r_copies') || {};
OUT.later = { mode: (r1 && r1.mode) || null, filed: !!(r1 && r1.filed), why: (r1 && r1.why) || '', home: a1[nm] || null,
              copies: c1[nm] == null ? null : c1[nm] };
var r2 = W.vaultPlannerFile(e, 'tok-later-open');
var c2 = disk('d2r_copies') || {};
OUT.same = { mode: (r2 && r2.mode) || null, copies: c2[nm] == null ? null : c2[nm] };
var r3 = W.vaultPlannerFile(e, 'tok-third-open');
var a3 = disk('d2r_muleAssign') || {}, c3 = disk('d2r_copies') || {};
OUT.third = { mode: (r3 && r3.mode) || null, why: (r3 && r3.why) || '', home: a3[nm] || null, copies: c3[nm] == null ? null : c3[nm] };
/* a router that cannot be asked at all (it throws - ROUTER_DOWN below): a filed name is still filed, and the copy is
   still counted. suggestMule is a closure of the vault script, so a window stub would never reach the planner's call. */
W.__lawRouterAsked = 0;
W.__lawRouterDown = true;
var r4 = W.vaultPlannerFile(e, 'tok-router-down');
W.__lawRouterDown = false;
var a4 = disk('d2r_muleAssign') || {}, c4 = disk('d2r_copies') || {};
OUT.down = { mode: (r4 && r4.mode) || null, ok: !!(r4 && r4.ok), why: (r4 && r4.why) || '', home: a4[nm] || null,
             copies: c4[nm] == null ? null : c4[nm], asked: W.__lawRouterAsked };
W.__lawRouterDown = true;
var probe = null;
try { W.suggestMule(nm); probe = 'answered'; } catch (eP) { probe = String(eP && eP.message || eP); }
W.__lawRouterDown = false;
OUT.downProbe = probe;
OUT.nm = nm;
})();
"""

#: the router taken down for one pick: the page's own suggestMule throws while the body sets __lawRouterDown
ROUTER_DOWN = ("  function suggestMule(name, opts){\n",
               "  function suggestMule(name, opts){\n"
               "    if (window.__lawRouterDown){ window.__lawRouterAsked = (window.__lawRouterAsked || 0) + 1;"
               " throw new Error('the router is down in this law'); }\n", 1)

_OUT = {}


def measured():
    if "o" not in _OUT:
        _OUT["o"] = VPN.run(BODY, prelude=AUTOMATED, patches=[ROUTER_DOWN], timeout=300)
    return _OUT["o"]


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AFiledPickCountsACopyWhateverTheRouterSays(unittest.TestCase):

    def test_0_premise_he_filed_it_and_the_router_would_throw_it_out(self):
        o = measured()
        self.assertEqual(o["__boot"]["errors"], [], "a page script did not run in node: %r" % o["__boot"])
        self.assertIsNotNone(o["row"], "PREMISE: Axe of Fechmar is not a unique in the planner's catalogue")
        self.assertTrue(o["add"]["ok"], "PREMISE: the hand door did not add it: %r" % o["add"])
        self.assertTrue(o["put"]["ok"], "PREMISE: his hand filing did not land: %r" % o["put"])
        self.assertEqual(o["advice"]["id"], "__throwout", "PREMISE: the router no longer advises throwing it out: %r" % o["advice"])

    def test_1_a_later_open_counts_copy_two_and_leaves_the_filing_where_he_put_it(self):
        o = measured()
        r = o["later"]
        self.assertEqual(r["mode"], "copy", "a later open of a filed item counted no copy: %r" % r)
        self.assertEqual(r["copies"], 2, "d2r_copies did not reach 2: %r" % r)
        self.assertIn("copy 2 filed to uni-weap", r["why"], r)
        self.assertNotIn("stays unfiled", r["why"], "a filed item was called unfiled: %r" % r)
        self.assertEqual(r["home"], "uni-weap", "the pick moved or unfiled his filing: %r" % r)

    def test_2_the_same_open_counts_once_and_the_next_open_counts_three(self):
        o = measured()
        self.assertEqual(o["same"]["mode"], "already", o["same"])
        self.assertEqual(o["same"]["copies"], 2, "saving the same open again counted another copy: %r" % o["same"])
        self.assertEqual(o["third"]["mode"], "copy", o["third"])
        self.assertEqual(o["third"]["copies"], 3, o["third"])
        self.assertEqual(o["third"]["home"], "uni-weap", o["third"])

    def test_3_a_router_that_cannot_be_asked_does_not_unfile_a_filed_pick(self):
        """the filing stands whether or not the router answers: it is never asked about a name already filed"""
        o = measured()
        d = o["down"]
        self.assertEqual(o.get("downProbe"), "the router is down in this law",
                         "PREMISE: the router could not be taken down - this case would grade nothing: %r" % o.get("downProbe"))
        self.assertEqual(d["asked"], 0, "the router was asked about a name already filed: %r" % d)
        self.assertTrue(d["ok"], "a filed item was refused because the router could not be asked: %r" % d)
        self.assertEqual(d["mode"], "copy", "a later open with the router down counted no copy: %r" % d)
        self.assertEqual(d["copies"], 4, d)
        self.assertEqual(d["home"], "uni-weap", d)


RED_PROOF = [
    {"why": "REG-2533 - a filed item whose router now advises throw-out is called unfiled, and its next copy is lost",
     "file": "bible.html",
     "find": "    if (assign[nm] != null) return { ok: true, filed: false, mode: 'already', mule: assign[nm], why: nm + ' is already filed' };\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2533 - the router is asked first again, so a router that cannot answer refuses a filed item and loses its copy",
     "file": "bible.html",
     "find": "    if (assign[nm] != null) return { ok: true, filed: false, mode: 'already', mule: assign[nm], why: nm + ' is already filed' };\n"
             "    var sg, asked = false;\n"
             "    try { sg = suggestMule(nm); asked = true; } catch (e) { sg = null; }\n"
             "    if (!asked) return { ok: false, filed: false, why: nm + ' — the router could not be asked, so nothing was filed' };\n",
     "replace": "    var sg, asked = false;\n"
                "    try { sg = suggestMule(nm); asked = true; } catch (e) { sg = null; }\n"
                "    if (!asked) return { ok: false, filed: false, why: nm + ' — the router could not be asked, so nothing was filed' };\n"
                "    if (assign[nm] != null) return { ok: true, filed: false, mode: 'already', mule: assign[nm], why: nm + ' is already filed' };\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
