# -*- coding: utf-8 -*-
"""REG-2858 (router probe, GrokBot's v3829 Vault pass) - A BARE "SHAKO" THROUGH THE HAND DOOR IS ASKED, NEVER GUESSED.

"Shako" is a white base, and it is also the name the board files Harlequin Crest under ("Harlequin Crest (Shako)").
Measured on the whole page in node before the fix: vaultHandAdd('Shako') owned a white Shako base (the router then sends it
to SOCKETED, "white base - still needed for Lore, Nadir") without a word, when he may mean his Harlequin Crest. His rule: a
doubt becomes a question, never a guess.

  * a bare base the board also files a unique under is refused 'ambiguous', naming both, and nothing is added;
  * the planner row's kind answers it: 'unique' owns Harlequin Crest (Shako), 'base' owns the white Shako;
  * an Eth / Superior word settles it as the base, and a base no unique is filed under (Monarch, Archon Plate; Dagger,
    whose "Gull (dagger)" bracket is a slot note) is added
    as before - so the hand door's base adds (test_vault_l1_a_hand_add_routes_by_type) keep working;
  * the pairs are read from the catalogue: on v3833 there is exactly one, Shako.

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
function add(n, o){ var a = W.vaultHandAdd(n, null, o || {}); return a && { ok: a.ok, refused: a.refused || null, mode: a.mode || null,
                                                                           name: a.name || null, among: a.among || null, why: a.why || '' }; }
OUT.pairs = [];
ITEMS.forEach(function(i){
  var p = /^(.+) \(([^()]+)\)$/.exec(String((i && i.n) || ''));
  if (p && W._vaultHandBase(p[2]) === p[2]) OUT.pairs.push(i.n);
});
OUT.bare = add('Shako');
OUT.lower = add('shako');
OUT.ownedAfterAsk = Array.from(owned).filter(function(n){ return /shako/i.test(n); });
OUT.superior = add('Superior Shako');
OUT.monarch = add('Monarch');
OUT.archon = add('Archon Plate');
OUT.dagger = add('Dagger');
OUT.unique = add('Shako', { kind: 'unique' });
OUT.base = add('Shako', { kind: 'base' });
OUT.owned = Array.from(owned).sort();
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ABareShakoIsAskedNotGuessed(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=SEED, timeout=300)

    def test_the_page_booted_and_the_catalogue_names_the_pair(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(self.o["pairs"], ["Harlequin Crest (Shako)"],
                         "PREMISE: the uniques filed under a hand-door base changed: %r" % self.o["pairs"])

    def test_a_bare_shako_is_asked_and_nothing_is_added(self):
        for k in ("bare", "lower"):
            r = self.o[k]
            self.assertFalse(r["ok"], "a bare Shako was owned without asking (%s): %r" % (k, r))
            self.assertEqual(r["refused"], "ambiguous", r)
            self.assertEqual(r["among"], ["Harlequin Crest (Shako)", "Shako"], r)
            self.assertIn("Which one?", r["why"], r)
            self.assertIn("Nothing was added", r["why"], r)
        self.assertEqual(self.o["ownedAfterAsk"], [], "a question still added something: %r" % self.o["ownedAfterAsk"])

    def test_the_kind_answers_the_question(self):
        self.assertTrue(self.o["unique"]["ok"], self.o["unique"])
        self.assertEqual(self.o["unique"]["name"], "Harlequin Crest (Shako)", self.o["unique"])
        self.assertTrue(self.o["base"]["ok"], self.o["base"])
        self.assertEqual(self.o["base"]["name"], "Shako", self.o["base"])
        self.assertIn("Harlequin Crest (Shako)", self.o["owned"])
        self.assertIn("Shako", self.o["owned"])

    def test_a_base_no_unique_is_filed_under_is_added_as_before(self):
        for k, nm in (("superior", "Superior Shako"), ("monarch", "Monarch"), ("archon", "Archon Plate"), ("dagger", "Dagger")):
            self.assertTrue(self.o[k]["ok"], "%s was refused: %r" % (nm, self.o[k]))
            self.assertEqual(self.o[k]["name"], nm, self.o[k])


RED_PROOF = [
    {"why": "REG-2858 - a bare Shako is owned as a white base again, never asked",
     "file": "bible.html",
     "find": "      else if (_tw.length && _kd !== 'base')\n",
     "replace": "      else if (false)\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2858 - the planner's 'unique' kind does not answer the question (the unique cannot be added by its base)",
     "file": "bible.html",
     "find": "      if (_tw.length === 1 && _kd === 'unique') r = { ok: true, name: _tw[0] };\n",
     "replace": "      if (false) r = { ok: true, name: _tw[0] };\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2858 - the pair is read off any bracket, so a lowercase slot note asks too (Dagger)",
     "file": "bible.html",
     "find": "          if (p && _vaultHandBase(p[2]) === p[2] && _vaultKeeps(i.n)) (m[p[2]] = m[p[2]] || []).push(String(i.n));\n",
     "replace": "          if (p && _vaultHandBase(p[2]) && _vaultKeeps(i.n)) (m[_vaultHandBase(p[2])] = m[_vaultHandBase(p[2])] || []).push(String(i.n));\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
