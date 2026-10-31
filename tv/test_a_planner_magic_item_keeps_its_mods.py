# -*- coding: utf-8 -*-
"""#154 front-run (REG-2835) - A MAGIC OR RARE ITEM ADDED FROM THE PLANNER KEEPS ITS MODS, AND IS KEPT.

His plan: hand-add 300-500 real items, with their exact mods, through the Vault's ✚ Add an item (the planner). The planner
turns each picked affix into its line (_vpMods) through window._cbAfText, and the d2jsp desk's gear lines do the same -
and the page never published window._cbAfText (every law that drives them stubs its own). Measured on the whole page in
node, through the planner's own UI path (choose, quality, ADD MOD, Done):
  * a magic Grand Charm with a prefix and a suffix was kept as "Stout Grand Charm of Dexterity" with mods [];
  * a rare Diadem with three picked mods was judged "RARE circlet with no stats read ... it needs a tooltip look" by the
    router, which then saw no lines, and the planner deleted it - his hand-added rare vanished.
Now the formatter is published beside window._cbAf: the charm keeps its two lines, the Diadem is kept in Magic & Rare with
its three, and the desk's post carries the affix line. RED_PROOF below.
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
import vault_page_node as VPN  # noqa: E402

PRELUDE = ("Object.defineProperty(navigator, 'webdriver', { get: function(){ return true; }, configurable: true });\n"
           "localStorage.setItem('d2r_ownerClaim', '*');\n")

BODY = r"""
(function(){
var W = window, DB = W._cbDb();
function code(n){ return Object.keys(DB.b).find(function(c){ return DB.b[c][0] === n; }); }
function cur(){ var s = W._cbState(); return s && s.host && s.host.cur ? s.host.cur() : null; }
function add(base, q, pre, suf, rn){
  W.vaultPlannerOpen(''); W._cbChoose('b:' + code(base)); W._cbQuality(q);
  if (rn){ W._cbRareName(0, rn[0]); W._cbRareName(1, rn[1]); }
  var picked = [];
  for (var k = 0; k < pre; k++){ var r = (W._cbAffixPool(cur()).rows.p || [])[k * 3]; if (r){ W._cbAddMod(r[0]); picked.push(r[0]); } }
  for (var j = 0; j < suf; j++){ var r2 = (W._cbAffixPool(cur()).rows.s || [])[j * 5]; if (r2){ W._cbAddMod(r2[0]); picked.push(r2[0]); } }
  var e = cur(), sh = W._cbShown(e, W._cbItem(e.id));
  W.vaultPlannerClose(); H.flush(60, 3);
  return { name: sh && sh.name, picked: picked.length, want: (typeof W._cbAfText === 'function') ? picked.map(function(id){ return W._cbAfText(W._cbAf(id), {}, null, 'text'); }) : null };
}
OUT.charm = add('Grand Charm', 'm', 1, 1);
OUT.diadem = add('Diadem', 'rare', 2, 1);
/* REG-3101 - the dice can name a rare after a unique it is not (Blood Crest / Blood Crescent): CI k drew it */
OUT.crest = add('Diadem', 'rare', 2, 1, ['Blood', 'Crest']);
OUT.mf = JSON.parse(W.LSR.getItem('d2r_magicFinds') || '{}');
OUT.owned = JSON.parse(W.LSR.getItem('d2r_owned') || '[]');
var gcId = 'b:' + code('Grand Charm');
var pa = (W._cbAffixPool({ id: gcId, base: code('Grand Charm'), q: 'm', ilvl: 99, affixes: [] }).rows.p || [])[0];
OUT.desk = pa ? W._d2jspGearLines({ id: gcId, base: code('Grand Charm'), q: 'm', affixes: [{ id: pa[0], rolls: {} }], rolls: {} }) : null;
OUT.deskWant = pa ? String(pa[2] || '') : null;   /* the affix's own words (its name column), whatever the export */
OUT.deskN = OUT.desk ? OUT.desk.length : null;
OUT.errors = H.errors.slice();
})();
"""


class APlannerMagicItemKeepsItsMods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not VPN.NODE:
            raise AssertionError("node is not on this machine - this law does not skip")
        cls.o = VPN.run(BODY, prelude=PRELUDE, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(self.o["errors"], [])

    def test_a_magic_charm_keeps_each_picked_mod(self):
        c = self.o["charm"]
        self.assertEqual(c["picked"], 2, "PREMISE: two mods were not picked: %r" % c)
        rec = self.o["mf"].get(c["name"])
        self.assertIsNotNone(rec, "the magic charm was not kept: %r" % (c, ))
        self.assertEqual(len(rec["mods"]), 2, "the charm's mods were not stored: %r" % rec)
        self.assertTrue(all(rec["mods"]), rec)
        if c["want"] is not None:
            self.assertEqual(rec["mods"], c["want"], rec)

    def test_a_rare_circlet_with_its_mods_is_kept_not_dropped(self):
        d = self.o["diadem"]
        self.assertEqual(d["picked"], 3, "PREMISE: three mods were not picked: %r" % d)
        rec = self.o["mf"].get(d["name"])
        self.assertIsNotNone(rec, "his hand-added rare vanished: %r not in %r" % (d["name"], sorted(self.o["mf"])))
        self.assertEqual((rec["q"], rec["base"], len(rec["mods"])), ("rare", "Diadem", 3), "the rare kept no mods: %r" % rec)
        if d["want"] is not None:
            self.assertEqual(rec["mods"], d["want"], rec)
        self.assertIn(d["name"], self.o["owned"], "the kept rare is not owned")

    def test_a_rare_named_like_a_unique_is_kept_as_his_rare(self):
        # REG-3101 (CI on ci/claude-v3847k) - "Blood Crest" was folded as a misread of the unique Blood Crescent, routed
        # TRASH, and the planner dropped the rare it had just filed
        c = self.o["crest"]
        self.assertEqual((c["name"], c["picked"]), ("Blood Crest", 3), "PREMISE: the rare was not named Blood Crest with three mods: %r" % c)
        rec = self.o["mf"].get(c["name"])
        self.assertIsNotNone(rec, "his rare named like a unique vanished: %r not in %r" % (c["name"], sorted(self.o["mf"])))
        self.assertEqual((rec["q"], rec["base"], len(rec["mods"])), ("rare", "Diadem", 3), rec)
        self.assertIn(c["name"], self.o["owned"], "the kept rare is not owned")

    def test_the_trade_desk_lists_the_affix_line(self):
        self.assertTrue(self.o["deskWant"] is not None, "PREMISE: no affix to list")
        self.assertGreaterEqual(self.o["deskN"] or 0, 1, "the d2jsp post drops the affix line: %r" % self.o["desk"])


RED_PROOF = [
    {"why": "REG-2835 - the affix text is not published again, so every planner magic or rare item loses its mods",
     "file": "bible.html",
     "find": "  window._cbAfText = _cbAfText;\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-3101 - a rare he owns is folded like a misread, so a rare named after a unique is dropped",
     "file": "bible.html",
     "find": "      if (!_sugFolding && !_sugHisMr && typeof window.d2rResolveItem === 'function'\n",
     "replace": "      if (!_sugFolding && typeof window.d2rResolveItem === 'function'\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
