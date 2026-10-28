# -*- coding: utf-8 -*-
"""#158.4 (GrokBot, the vault on his real frames) - A MATERIAL IS NOT A VAULT ITEM.

"Key of Destruction" was registered into the vault and routed to a WEAPON mule. Uber keys, organs, essences and the Token
of Absolution are materials: the Materials stash counts them (SPECIAL_DROPS - the groups the uber/Token planner reads) and
the vault never files them. The read door refuses them with that sentence; a Sunder charm - a real unique the Renewed
recipe also counts - still registers, and so does an ordinary unique.

Driven on the whole page in node through the real door (window.tvVaultRegister). RED_PROOF below.
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

SEED = r"""
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify([]));
localStorage.setItem('d2r_vaultProv', JSON.stringify({}));
localStorage.setItem('d2r_muleAssign', JSON.stringify({}));
"""
BODY = r"""
(function(){
var W = window;
W._vaultAutoIntakeSet && W._vaultAutoIntakeSet(true);
function reg(n){ var r = W.tvVaultRegister(n, { by: 'hand', at: new Date().toISOString(), where: 'the law' });
  return r ? { ok: !!r.ok, refused: r.refused || null, why: r.why || '' } : null; }
OUT.key = reg('Key of Destruction');
OUT.horn = reg('Diablo’s Horn');
OUT.token = reg('Token of Absolution');
OUT.essence = reg('Essence of Hatred');
OUT.sunder = reg('Bone Break');
OUT.unique = reg('Harlequin Crest');
OUT.owned = Array.from(owned).sort();
OUT.groups = Object.keys(W.vaultMaterialNames()).length;
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AMaterialIsNotAVaultItem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=SEED, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])

    def test_a_material_is_refused_and_says_where_it_is_counted(self):
        for k in ("key", "horn", "token", "essence"):
            r = self.o[k]
            self.assertFalse(r["ok"], "%s was registered into the vault (#158.4): %r" % (k, r))
            self.assertEqual(r["refused"], "not-an-item", r)
            self.assertIn("Materials stash counts it", r["why"])
        for n in ("Key of Destruction", "Token of Absolution", "Essence of Hatred"):
            self.assertNotIn(n, self.o["owned"])
        self.assertGreaterEqual(self.o["groups"], 10, "PREMISE: the material groups were not read from SPECIAL_DROPS")

    def test_a_sunder_charm_and_a_unique_still_register(self):
        self.assertTrue(self.o["sunder"]["ok"], "a Sunder charm (a real unique) was refused as a material: %r" % self.o["sunder"])
        self.assertTrue(self.o["unique"]["ok"], self.o["unique"])
        self.assertIn("Bone Break", self.o["owned"])


RED_PROOF = [
    {"why": "#158.4 - a material is registered into the vault again",
     "file": "bible.html",
     "find": "    if (Object.prototype.hasOwnProperty.call(mat, f))\n",
     "replace": "    if (false)\n",
     "matches": 1, "needs": "node"},
    {"why": "#158.4 - Sunder charms are refused as materials too",
     "file": "bible.html",
     "find": "      ['key', 'organ', 'essence', 'token'].forEach(function(c){\n",
     "replace": "      ['key', 'organ', 'essence', 'token', 'sunder'].forEach(function(c){\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
