# -*- coding: utf-8 -*-
"""REG-2855 (ACT-3, GrokBot's v3829 Vault pass) - AN ITEM IS SIZED BY ITS OWN BASE, AND A RUNE OR A GEM IS ONE CELL.

Measured on the whole page in node before the fix (window._itemCells, which vaultSize, the packer and every locker tile
read): Doom Eye, Raven Whorl, Wraith Scarab, Bone Eye and Brimstone Clasp were each a guessed 1x2; Ber, Perfect Amethyst,
Jah and Chipped Ruby 1x2 (marked approx) and Flawless Skull 2x2 (the helm rule's word 'skull').

  * his Magic & Rare register's base wins over a TV stub and over the name's grammar: Bone Eye (a magic Ring) 1x1, and
    Brimstone Clasp (a rare Plated Belt, where the grammar says amulet) 2x1;
  * with no keeper base, a rolled rare is sized by its slot when every slot its suffix names is one size (Doom Eye jewel,
    Raven Whorl ring / jewel, Wraith Scarab amulet / jewel: 1x1, stub or no stub); when the slots disagree (Doom Grip:
    gloves / ring) the name cannot say which, and the footprint stays the marked guess;
  * a keeper base recorded after a first ask is not answered by the guess cached before it;
  * runes and gems are 1x1;
  * a bare base name is its own base: every gear base the hand door takes (CB_DB, the table _cbFoot reads) is sized by
    its game footprint - 223 of 508 were the keyword table's guess (Ring Mail and Rune Sword a 1x1 ring and rune).

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
  'Brimstone Clasp': { q: 'rare', base: 'Plated Belt' }
}));
var stub = function(r, b){ return { rarity: r, base: b, cat: 'TV-vaulted', val: 'tv', desc: 'a law fixture' }; };
localStorage.setItem('d2r_tvExtraItems', JSON.stringify({
  'Doom Eye': stub('rare', 'Doom Eye'),
  'Bone Eye': stub('rare', 'Bone Eye'),
  'Brimstone Clasp': stub('rare', 'Brimstone Clasp')
}));
"""
BODY = r"""
(function(){
var W = window;
function sz(n){ var c = W._itemCells(n); return c ? [c.w, c.h, !!c.approx] : null; }
var names = ['Doom Eye', 'Raven Whorl', 'Wraith Scarab', 'Bone Eye', 'Brimstone Clasp', 'Doom Grip', 'Dread Grasp',
             'Ber', 'Ber Rune', 'Jah', 'Perfect Amethyst', 'Chipped Ruby', 'Flawless Skull', 'Rune Sword'];
OUT.cells = {};
names.forEach(function(n){ OUT.cells[n] = sz(n); });
OUT.vs = W.vaultSize ? W.vaultSize('Brimstone Clasp') : null;
/* every gear base the hand door takes, against its own game footprint */
var db = W._cbDb(), n = 0, diff = [];
Object.keys(db.b).forEach(function(k){
  var r = db.b[k];
  if (!r || !r[0] || r[21] === 'm' || r[1] === 'tpot' || r[20] === 0) return;
  n++;
  var c = W._itemCells(String(r[0])), f = W._cbFoot({ base: k });
  if (!f || !c || c.w !== f[0] || c.h !== f[1]) diff.push([String(r[0]), c && [c.w, c.h], f]);
});
OUT.bases = n; OUT.baseDiff = diff;
/* a keeper base recorded AFTER the first ask */
OUT.late0 = sz('Bitter Clasp');
magicFinds['Bitter Clasp'] = { q: 'rare', base: 'Heavy Belt' };
OUT.late1 = sz('Bitter Clasp');
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AnItemIsSizedByItsOwnBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=SEED, timeout=300)
        cls.c = cls.o["cells"]

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])

    def test_his_register_base_wins_over_the_stub_and_the_grammar(self):
        self.assertEqual(self.c["Bone Eye"], [1, 1, False], "a magic Ring in his register did not draw 1x1: %r" % self.c["Bone Eye"])
        self.assertEqual(self.c["Brimstone Clasp"], [2, 1, False],
                         "a rare Plated Belt in his register did not draw 2x1 (the grammar says amulet): %r" % self.c["Brimstone Clasp"])
        self.assertEqual(self.o["vs"], [2, 1], "the packer's vaultSize does not read the footprint the tile prints: %r" % self.o["vs"])

    def test_a_rolled_rare_is_sized_by_its_slot_when_its_slots_agree(self):
        for n in ("Doom Eye", "Raven Whorl", "Wraith Scarab"):
            self.assertEqual(self.c[n], [1, 1, False], "%s (ring / amulet / jewel slots) did not draw 1x1: %r" % (n, self.c[n]))

    def test_slots_that_disagree_stay_the_marked_guess(self):
        self.assertTrue(self.c["Doom Grip"][2], "Doom Grip (gloves / ring) was given one slot's size as fact: %r" % self.c["Doom Grip"])
        self.assertEqual(self.c["Dread Grasp"], [2, 2, False], "Dread Grasp's table answer moved: %r" % self.c["Dread Grasp"])

    def test_a_keeper_base_recorded_later_is_not_answered_by_the_old_guess(self):
        self.assertEqual(self.o["late0"], [1, 1, False], "PREMISE: Bitter Clasp (amulet grammar) did not first draw 1x1: %r" % self.o["late0"])
        self.assertEqual(self.o["late1"], [2, 1, False], "the keeper base recorded later was answered by the cached guess: %r" % self.o["late1"])

    def test_runes_and_gems_are_one_cell(self):
        for n in ("Ber", "Ber Rune", "Jah", "Perfect Amethyst", "Chipped Ruby", "Flawless Skull"):
            self.assertEqual(self.c[n], [1, 1, False], "%s did not draw 1x1: %r" % (n, self.c[n]))

    def test_a_bare_base_name_is_sized_by_its_own_game_footprint(self):
        self.assertGreater(self.o["bases"], 400, "PREMISE: the base table was not read (%r bases)" % self.o["bases"])
        self.assertEqual(self.o["baseDiff"], [], "%d bare bases are not sized by their own footprint: %r"
                         % (len(self.o["baseDiff"]), self.o["baseDiff"][:8]))
        self.assertEqual(self.c["Rune Sword"], [2, 3, False], "the base Rune Sword was not sized 2x3: %r" % self.c["Rune Sword"])


RED_PROOF = [
    {"why": "REG-2855 - his register's base is not read, so Brimstone Clasp is sized by the amulet grammar",
     "file": "bible.html",
     "find": "      _keeperBase = String(_mfBase(name) || '').trim();\n",
     "replace": "      _keeperBase = '';\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2855 - a TV stub's placeholder base outranks his register's base again",
     "file": "bible.html",
     "find": "        base = (c && c.base) || (t && t.b) || _keeperBase || (ex && ex.base) || '';\n",
     "replace": "        base = (c && c.base) || (t && t.b) || (ex && ex.base) || _keeperBase || '';\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2855 - the keeper base leaves the cache key, so a later record is answered by the old guess",
     "file": "bible.html",
     "find": " + (_keeperBase ? '\\nkeeper ' + _keeperBase : '');\n",
     "replace": ";\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2855 - runes and gems fall back to the keyword table (Ber 1x2, Flawless Skull 2x2)",
     "file": "bible.html",
     "find": "      if (_oneCell){ cells = {w:1, h:1}; _ITEM_CELLS_CACHE[_ck] = cells; return cells; }\n",
     "replace": "      if (false){ cells = {w:1, h:1}; _ITEM_CELLS_CACHE[_ck] = cells; return cells; }\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2855 - the rolled-rare grammar is not asked for a footprint (Doom Eye 1x2 again)",
     "file": "bible.html",
     "find": "      if ((!base || _stubOwn) && typeof _rolledQuality === 'function'){\n",
     "replace": "      if (false){\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2855 - a TV stub's own-name base blocks the grammar (Doom Eye with a stub 1x2 again)",
     "file": "bible.html",
     "find": "        _stubOwn = !!(!(c && c.base) && !(t && t.b) && !_keeperBase && ex && ex.val === 'tv' && String(ex.base || '') === String(name));\n",
     "replace": "        _stubOwn = false;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2855 - slots that disagree are not caught, so Doom Grip takes the gloves size as fact",
     "file": "bible.html",
     "find": "            else if (_rqSz.w !== z.w || _rqSz.h !== z.h) _rqOne = false;\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2855 - a bare base name is not looked up as its own base (Ring Mail a 1x1 ring again)",
     "file": "bible.html",
     "find": "            var _bCode = _cdbB._baseByName[String(base || name).toLowerCase()];   /* REG-2855 a bare base name */\n",
     "replace": "            var _bCode = _cdbB._baseByName[String(base).toLowerCase()];\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
