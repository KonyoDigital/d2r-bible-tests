# -*- coding: utf-8 -*-
"""REG-2898 (GrokBot's v3829 fresh-add simulation, ACT-7) - + ADD AN ITEM TAKES A SOCKETED BASE, AND IT LANDS WHERE THE
ROUTER SAYS.

Measured on the whole page in node before the fix: vaultHandAdd('Monarch (4os)') answered "not an item the vault draws (a
unique, a set piece, a runeword or a socketed base it carries)" while the router sends a 4os Monarch to SOCKETED: the door
contradicted its own sentence. A socketed label's entry was made only when a reader registered it (tvVaultRegister asks
_ensureSocketBaseEntry); the hand door never asked. It asks now, the same way: a Monarch (4os) is owned and homed on
SOCKETED, while a base that can hold no runeword (a Circlet) is still not made a socketed keeper - that function's own
rule - and is refused. Runes and gems name their stash (REG-2857).

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
function add(n){ var a = W.vaultHandAdd(n, null, {}); return a && { ok: a.ok, name: a.name || null, refused: a.refused || null, why: a.why || '' }; }
OUT.mon = add('Monarch (4os)');
OUT.circ = add('Circlet (2os)');
OUT.route = (W.suggestMule('Monarch (4os)') || {}).id || null;
OUT.owned = Array.from(owned).sort();
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class TheHandDoorTakesASocketedBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=SEED, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])

    def test_a_socketed_base_is_taken_and_homed_where_the_router_says(self):
        self.assertTrue(self.o["mon"]["ok"], "the hand door refused a 4os Monarch: %r" % self.o["mon"])
        self.assertIn("Monarch (4os)", self.o["owned"])
        self.assertEqual(self.o["route"], "bases", self.o["route"])

    def test_a_base_that_holds_no_runeword_is_still_refused(self):
        self.assertFalse(self.o["circ"]["ok"], "a socketed circlet was made a keeper: %r" % self.o["circ"])
        self.assertNotIn("Circlet (2os)", self.o["owned"])


RED_PROOF = [
    {"why": "REG-2898 - the hand door never asks for the socketed base's entry, so a 4os Monarch is refused again",
     "file": "bible.html",
     "find": "      try { if (typeof window._ensureSocketBaseEntry === 'function') window._ensureSocketBaseEntry(r.name); } catch (eSb) {}\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
