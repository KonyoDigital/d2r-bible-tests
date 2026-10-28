# -*- coding: utf-8 -*-
"""REG-2897 (GrokBot's v3829 fresh-add simulation, ACT-6) - THE NAME HE TYPES FINDS THE ITEM THE VAULT HOLDS.

+ Add an item owns "Harlequin Crest" as "Harlequin Crest (Shako)" and "Tal Rasha's Guardianship" as "... (armor)" - the
register's one name (_vaultResolveName) - and draws them there (the SHARED STASH, SETS-TAL-IK). Measured on the whole page
in node before the fix: vaultAssign('Harlequin Crest', ...) then refused 'not-owned', and FIND's where-is for the bare name
said only where it WOULD go, with no cell - GrokBot read both as "drawn on NO locker" and "no cell carries that name".
Now both doors ask the same resolver for a name he does not own, and act on the item it names. A name it cannot settle
is refused as before, and a bare "Shako" is still a question (REG-2858).

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
W._vaultAutoIntakeSet && W._vaultAutoIntakeSet(false);
OUT.add = [W.vaultHandAdd('Harlequin Crest', null, {}).name, W.vaultHandAdd("Tal Rasha's Guardianship", null, {}).name];
var w0 = W._vaultWhereIs("Tal Rasha's Guardianship");
OUT.whereTal = w0 && { mule: w0.mule, cell: w0.cell };
var a = W.vaultAssign('Harlequin Crest', 'uni-armor');
OUT.assign = JSON.parse(H.RAW.get('d2r_muleAssign') || '{}');
OUT.assignRet = a || null;
var w1 = W._vaultWhereIs('Harlequin Crest');
OUT.whereHC = w1 && { kind: w1.kind, mule: w1.mule, cell: w1.cell };
OUT.junk = W.vaultAssign('Stone of Nothing', 'uni-armor') || null;
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ATypedNameFindsTheItemTheVaultHolds(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=SEED, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(self.o["add"], ["Harlequin Crest (Shako)", "Tal Rasha's Guardianship (armor)"], "PREMISE: %r" % self.o["add"])

    def test_vault_assign_files_the_item_the_bare_name_names(self):
        self.assertEqual(self.o["assign"].get("Harlequin Crest (Shako)"), "uni-armor",
                         "vaultAssign('Harlequin Crest') did not file the item it names: %r / %r" % (self.o["assign"], self.o["assignRet"]))
        self.assertNotIn("Harlequin Crest", self.o["assign"], "a second name was filed beside the item")
        self.assertEqual(self.o["junk"], {"ok": False, "refused": "not-owned"}, "a name nothing settles was filed: %r" % self.o["junk"])

    def test_find_names_the_cell_for_the_bare_name(self):
        self.assertEqual(self.o["whereHC"]["mule"], "uni-armor", self.o["whereHC"])
        self.assertTrue(self.o["whereHC"]["cell"], "FIND gave no cell for the bare name: %r" % self.o["whereHC"])
        self.assertEqual(self.o["whereTal"]["mule"], "sets-major", self.o["whereTal"])
        self.assertTrue(self.o["whereTal"]["cell"], "FIND gave no cell for the bare set-piece name: %r" % self.o["whereTal"])


RED_PROOF = [
    {"why": "REG-2897 - vaultAssign refuses the bare name he typed again ('not-owned')",
     "file": "bible.html",
     "find": "            if (_cn && _cn !== name && owned.has(_cn)) name = _cn; } catch (eCn) {}\n",
     "replace": "            void _cn; } catch (eCn) {}\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2897 - FIND's where-is gives no cell for the bare name again",
     "file": "bible.html",
     "find": "            if (_cnW && _cnW !== nm && (owned.has(_cnW) || assign[_cnW] != null)){ nm = _cnW; mid = assign[nm]; } } catch (eCnW) {}\n",
     "replace": "            void _cnW; } catch (eCnW) {}\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
