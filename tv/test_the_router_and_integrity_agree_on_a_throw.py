# -*- coding: utf-8 -*-
"""#158.5 (REG-2813, GrokBot on his real frames) - THE ROUTER AND VAULT INTEGRITY AGREE ON WHAT IS THROWN OUT.

GrokBot: the auto door threw Blackbog's Sharp out as trade value TRASH (suggestMule, v2200), and VAULT INTEGRITY flagged
the same read "wrongly thrown - a chronicle unique, Rescue it" with Fix all - so it was rescued and thrown again, for ever.
MEASURED on the whole page in node: 254 of the 555 catalogue names route to throw-out (v2200 trash, v394 low set pieces),
and integrity called every one of them wrongly thrown. One rule now, _vaultRouterThrows: the auto door throws a read out
when it says so, and integrity never rescues a read it throws; a thrown read the router would keep (a grail unique, a
runeword, a keeper) is still rescued.

Driven on the whole page in node (vault_page_node, fresh empty storage): every router-thrown catalogue name sits in the
thrown store at once and the audit runs; Blackbog's Sharp goes through Fix all twice and settles; a keeper in the thrown
store is still rescued, and the router keeps what integrity rescues. The auto door's throw is read at its one-line site.
RED_PROOF below.
"""
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
import vault_page_node as VPN  # noqa: E402

BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")

BODY = r"""
(function(){
var N = "Blackbog's Sharp", KEEP = "Harlequin Crest";
function thrownKinds(name){ return (window._vaultAudit().findings || []).filter(function(f){
  return f.item === name && f.kind === 'wrongly-thrown'; }).length; }
var reg = (typeof ITEM_REGISTRY !== 'undefined') ? ITEM_REGISTRY : {};
var names = {}; Object.keys(reg).concat(Object.keys(window._UNI_EXTRA || {})).forEach(function(n){ names[n] = 1; });
var routerThrows = Object.keys(names).filter(function(n){
  try { var s = suggestMule(n); return !!(s && s.id === '__throwout'); } catch (e) { return false; } });
OUT.routerThrowsN = routerThrows.length;
OUT.helper = typeof window._vaultRouterThrows;
OUT.blackbogRoute = (function(){ var s = suggestMule(N); return s && s.id; })();
// 1) everything the router throws, in the thrown store at once: integrity rescues none of it
routerThrows.forEach(function(n){ unknownReads.add(n); });
var F = (window._vaultAudit().findings || []).filter(function(f){ return f.kind === 'wrongly-thrown'; });
OUT.rescuedAgainstRouter = F.filter(function(f){ return routerThrows.indexOf(f.item) >= 0; }).map(function(f){ return f.item; }).slice(0, 8);
OUT.rescuedAgainstRouterN = F.filter(function(f){ return routerThrows.indexOf(f.item) >= 0; }).length;
// 2) Blackbog's Sharp: one load, the router's throw, then integrity's Fix all twice - it settles where the router put it
OUT.bb = [];
for (var k = 0; k < 2; k++){
  window._vaultAuditFixAll();
  OUT.bb.push({ thrown: unknownReads.has(N), owned: owned.has(N), flagged: thrownKinds(N) });
}
// 3) the other way: a keeper the router would mule, thrown by mistake, is still rescued - and the router keeps it
OUT.keepRoute = (function(){ var s = suggestMule(KEEP); return s && s.id; })();
unknownReads.add(KEEP);
OUT.keepFlagged = thrownKinds(KEEP);
window._vaultAuditFixAll();
OUT.keepAfter = { thrown: unknownReads.has(KEEP), owned: owned.has(KEEP), routerThrows: window._vaultRouterThrows(KEEP) };
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class TheRouterAndIntegrityAgree(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, timeout=400)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(self.o["helper"], "function", "the one rule is not on the page")

    def test_premise_the_router_throws_blackbog_and_many_more(self):
        self.assertEqual(self.o["blackbogRoute"], "__throwout")
        self.assertGreater(self.o["routerThrowsN"], 100, "PREMISE: the router throws few catalogue names - re-measure")

    def test_integrity_never_rescues_what_the_router_throws(self):
        self.assertEqual(self.o["rescuedAgainstRouterN"], 0,
                         "VAULT INTEGRITY calls router-thrown reads wrongly thrown (the rescue/re-throw loop): %r"
                         % self.o["rescuedAgainstRouter"])

    def test_blackbogs_sharp_settles(self):
        self.assertEqual(self.o["bb"], [{"thrown": True, "owned": False, "flagged": 0}] * 2,
                         "Blackbog's Sharp did not settle after the router's throw and integrity's Fix all: %r" % self.o["bb"])

    def test_a_keeper_thrown_by_mistake_is_still_rescued(self):
        self.assertNotEqual(self.o["keepRoute"], "__throwout", "PREMISE: the keeper fixture is one the router keeps")
        self.assertEqual(self.o["keepFlagged"], 1, "a keeper in the thrown store is no longer rescued")
        self.assertEqual(self.o["keepAfter"], {"thrown": False, "owned": True, "routerThrows": False})

    def test_the_auto_door_throws_by_the_same_rule(self):
        with open(BIBLE, encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count("            if (window._vaultRouterThrows(n)){   /* REG-2813 - the same rule VAULT INTEGRITY asks, "
                                   "so it never rescues this read */\n"), 1,
                         "the auto door's throw-out no longer asks the one rule integrity asks")


RED_PROOF = [
    {"why": "REG-2813 - integrity rescues router-thrown reads again (the Blackbog's Sharp loop)",
     "file": "bible.html",
     "find": "      if (_vaultRouterThrows(n)) return;   /* REG-2813 - the router threw it: one rule, never rescued against it */\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2813 - the one rule stops answering for a throw-out route, so integrity rescues a keeper it should not",
     "file": "bible.html",
     "find": "  function _vaultRouterThrows(n){ try { var sg = suggestMule(n); return !!(sg && sg.id === '__throwout'); } catch (e) { return false; } }\n",
     "replace": "  function _vaultRouterThrows(n){ return true; }\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2813 - the auto door throws by its own copy of the rule again",
     "file": "bible.html",
     "find": "            if (window._vaultRouterThrows(n)){   /* REG-2813 - the same rule VAULT INTEGRITY asks, so it never rescues this read */\n",
     "replace": "            var _lsm = suggestMule(n);\n            if (_lsm && _lsm.id === '__throwout'){\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
