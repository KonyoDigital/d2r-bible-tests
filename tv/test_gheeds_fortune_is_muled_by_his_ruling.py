# -*- coding: utf-8 -*-
"""REG-2859 (router probe, GrokBot's v3829 Vault pass) - GHEED'S FORTUNE IS MULED ON UNI-SMALL BY HIS RULING, AND SAYS SO.

His ruling 2026-10-15: "torches and anni stay in shared. gheeds gets muled." Measured on the whole page in node before the
fix: suggestMule("Gheed's Fortune") answered UNI-SMALL with "jewelry/charm - base: Grand Charm" - it reached the charm mule
only by falling through to the jewelry word table - while the code's comments called its home "its charm mule", which
GrokBot read as a mule of its own beside the UNI-SMALL the router gave: two answers for one item.

  * the ruling itself answers: UNI-SMALL, the charm mule, citing the ruling - for the catalogue's curly spelling, a
    straight one and a bare "Gheeds";
  * his per-item switch still wins: forced 'shared' is the shared stash, forced 'mule' is UNI-SMALL;
  * Annihilus and Hellfire Torch keep the shared stash (the ruling's other half, unchanged).
Where charms belong in general is his ACT-4 ruling and is not decided here.

Driven on the whole page in node (vault_page_node), fixtures only. RED_PROOF below.
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

SEED = "localStorage.setItem('d2r_ownerClaim', '*');\n"
BODY = r"""
(function(){
var W = window;
function ask(n, o){ var s = W.suggestMule(n, o); return s ? { id: s.id, why: s.why || '' } : null; }
OUT.r = {
  straight: ask("Gheed's Fortune"), curly: ask('Gheed’s Fortune'), bare: ask('Gheeds Fortune'),
  forcedMule: ask("Gheed's Fortune", { _shareForceOut: true }), forcedShared: ask("Gheed's Fortune", { _shareForceIn: true }),
  anni: ask('Annihilus'), torch: ask('Hellfire Torch')
};
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class GheedsFortuneIsMuledByHisRuling(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=SEED, timeout=300)
        cls.r = cls.o["r"]

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])

    def test_the_ruling_mules_it_on_uni_small_and_says_so(self):
        for k in ("straight", "curly", "bare", "forcedMule"):
            r = self.r[k]
            self.assertEqual(r["id"], "uni-small", "%s: Gheed's Fortune was not muled on UNI-SMALL: %r" % (k, r))
            self.assertIn("2026-10-15 ruling", r["why"], "%s: the answer does not come from his ruling: %r" % (k, r))
            self.assertIn("UNI-SMALL, the charm mule", r["why"], r)

    def test_his_switch_and_the_rulings_other_half_hold(self):
        self.assertEqual(self.r["forcedShared"]["id"], "shared", self.r["forcedShared"])
        for k in ("anni", "torch"):
            self.assertEqual(self.r[k]["id"], "shared", "%s left the shared stash: %r" % (k, self.r[k]))


RED_PROOF = [
    {"why": "REG-2859 - Gheed's reaches UNI-SMALL only through the jewelry word table again",
     "file": "bible.html",
     "find": "    if (/^Gheed'?s Fortune$/i.test(_keepName(name)) && muleById('uni-small'))\n",
     "replace": "    if (false)\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2859 - the ruling's answer names a different home than the charm mule",
     "file": "bible.html",
     "find": "      return {id:'uni-small', why:'Gheed\\u2019s Fortune is muled",
     "replace": "      return {id:'magic-rare', why:'Gheed\\u2019s Fortune is muled",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
