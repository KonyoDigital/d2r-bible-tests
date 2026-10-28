# -*- coding: utf-8 -*-
"""REG-2856 (GrokBot's v3829 Vault pass, the router probe) - HIS MAGIC & RARE REGISTER ANSWERS BEFORE A TV STUB AND BEFORE
THE NAME'S GRAMMAR, SO ONE ITEM GETS ONE ANSWER.

Measured on the whole page in node before the fix (window.suggestMule, which the proposal, the filing and the audit ask):
  * Bone Eye - a magic Ring in d2r_magicFinds - routed as "a rare's rolled name (Bone + Eye: jewel)";
  * Brimstone Clasp - a rare Plated Belt there - as "(Brimstone + Clasp: amulet)";
  * Lion Branded Grand Charm - magic there, with a TV stub - to UNI-SMALL as "charm/skiller", while MAGIC & RARE counted the
    same name from the same register: two answers for one item.
Now the register's answer (REG-2093) is asked first by the stub path and by the no-base path, and names his record's base.
A rolled name the register does not hold keeps the grammar's answer. Since his 2026-10-28 charm ruling (REG-2895) a
charm is answered by the one charm rule before either: Lion Branded Grand Charm is a skiller, so the CHARMS mule - one
answer at the router and the proposal, which is what this law holds it to.

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

SEED = r"""
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_magicFinds', JSON.stringify({
  'Bone Eye': { q: 'magic', base: 'Ring' },
  'Brimstone Clasp': { q: 'rare', base: 'Plated Belt' },
  'Lion Branded Grand Charm': { q: 'magic', base: 'Grand Charm' }
}));
var stub = function(r, b){ return { rarity: r, base: b, cat: 'TV-vaulted', val: 'tv', desc: 'a law fixture' }; };
localStorage.setItem('d2r_tvExtraItems', JSON.stringify({
  'Bone Eye': stub('rare', 'Bone Eye'),
  'Lion Branded Grand Charm': stub('basic', 'Lion Branded Grand Charm'),
  'Doom Eye': stub('rare', 'Doom Eye')
}));
"""
BODY = r"""
(function(){
var W = window;
OUT.r = {};
['Bone Eye', 'Brimstone Clasp', 'Lion Branded Grand Charm', 'Doom Eye', 'Raven Whorl'].forEach(function(n){
  var s = W.suggestMule(n), p = W.vaultPropose(n);
  OUT.r[n] = { id: s && s.id, why: s && s.why, home: p && p.home };
});
OUT.stubs = ['Bone Eye', 'Lion Branded Grand Charm', 'Doom Eye'].map(function(n){ return !!(EXTRA_ITEMS[n] && EXTRA_ITEMS[n].val === 'tv'); });
OUT.noStub = !EXTRA_ITEMS['Brimstone Clasp'];
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class HisRegisterAnswersBeforeAStubOrTheGrammar(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=SEED, timeout=300)
        cls.r = cls.o["r"]

    def test_the_page_booted_with_the_fixture(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(self.o["stubs"], [True, True, True], "PREMISE: the TV stubs were not seeded")
        self.assertTrue(self.o["noStub"], "PREMISE: Brimstone Clasp must reach the no-stub path")

    def test_a_stubbed_registered_name_takes_the_registers_answer(self):
        b = self.r["Bone Eye"]
        self.assertEqual(b["id"], "magic-rare", b)
        self.assertIn("(magic Ring)", b["why"], "a magic Ring in his register was routed by its name's grammar: %r" % b)
        self.assertNotIn("jewel", b["why"], b)
        lb = self.r["Lion Branded Grand Charm"]
        self.assertEqual(lb["id"], "charms",
                         "a registered skiller grand charm with a TV stub was not given the charm rule's one home: %r" % lb)
        self.assertEqual(lb["home"], "CHARMS", "the proposal gives a second answer: %r" % lb)

    def test_an_unstubbed_registered_name_takes_the_registers_answer_before_the_grammar(self):
        c = self.r["Brimstone Clasp"]
        self.assertEqual(c["id"], "magic-rare", c)
        self.assertIn("(rare Plated Belt)", c["why"], "a rare Plated Belt in his register was routed as an amulet: %r" % c)

    def test_a_rolled_name_the_register_does_not_hold_keeps_the_grammar(self):
        self.assertIn("Doom + Eye: jewel", self.r["Doom Eye"]["why"], self.r["Doom Eye"])
        self.assertIn("Raven + Whorl", self.r["Raven Whorl"]["why"], self.r["Raven Whorl"])
        self.assertEqual(self.r["Doom Eye"]["id"], "magic-rare")


RED_PROOF = [
    {"why": "REG-2856 - a TV stub answers before his register again (Lion Branded Grand Charm -> UNI-SMALL, Bone Eye a jewel)",
     "file": "bible.html",
     "find": "{ var _mfS = _mfRoute(); if (_mfS) return _mfS; }   /* REG-2856 his register before a stub */",
     "replace": "{}   /* REG-2856 his register before a stub */",
     "matches": 1, "needs": "node"},
    {"why": "REG-2856 - the name's grammar answers before his register again (Brimstone Clasp an amulet)",
     "file": "bible.html",
     "find": "      var _mfA = _mfRoute(); if (_mfA) return _mfA;\n",
     "replace": "\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
