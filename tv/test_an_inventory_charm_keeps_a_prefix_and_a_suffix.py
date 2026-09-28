# -*- coding: utf-8 -*-
"""Wave 2 — AN INVENTORY CHARM KEEPS A PREFIX AND A SUFFIX.

GrokBot ACT 5855237740: a Small Charm in the mule 10x4 takes Add Mod, and Fine plus of Balance
is max damage, attack rating, and 5% faster hit recovery. The builder's Add Mod already does
that. This law does not add a second picker. It drives that same _cbAddMod on a charm the mule
window placed, then the hover the window already draws.

The store keeps the base name, so the charm stays a generic copy and the door does not file the
composed name. The tile and its spoken name say what the tooltip says. The inventory list asks
the same composer when that list is drawn.
A charm with no mods still says its base. A move keeps the mods. An armour prefix and a second
prefix are refused by the same Add Mod.

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

import test_the_mule_inventory_takes_items_like_the_doll as INV  # noqa: E402

NODE = INV.NODE
NAME = "Fine Small Charm of Balance"
LINES = ["+5% Faster Hit Recovery", "1-3 to Maximum Damage", "10-20 to Attack Rating"]

SCENARIO = r"""
door();
window.openMuleCard('uni-armor');
var beforeBuilds = STORE['d2r_charBuilds'], beforeSel = STORE['d2r_cbSel'];
out.placed = place(0, 0, 'b:cm1');
out.tab = st().pick && st().pick.tab;
out.addBtn = (modalHtml() || '').indexOf('window._cbModOpen(true)') >= 0;
var k = keyOf('Small Charm');
out.addFine = window._cbAddMod('p256');
out.addBal = window._cbAddMod('s267');
out.addSturdy = window._cbAddMod('p1');
out.addSecond = window._cbAddMod('p322');
var rec = invStore()[k];
out.stored = { name: rec.name, q: rec.q, id: rec.id, base: rec.base, w: rec.w, h: rec.h,
               ids: (rec.affixes || []).map(function(a){ return a.id; }) };
var tile = dbTiles().filter(function(t){ return t.key === k; })[0] || null;
out.tile = tile;
out.aria = (function(){ var tag = tileTag(k) || ''; var m = /aria-label="([^"]*)"/.exec(tag); return m ? unesc(m[1]) : ''; })();
out.art = artOf(k);
var seen = null;
window.d2Tip.show = function(e){ seen = { name: e && e.name, q: e && e.q,
  lines: (e && e.lines || []).map(function(l){ return String(l.html || l.t || ''); }) }; };
fire('mouseover', { target: tileEl(k), buttons: 0 });
out.hover = seen;
out.moved = window._mpInvMove(k, 5, 2);
var rec2 = invStore()[k];
out.after = { x: rec2.x, y: rec2.y, ids: (rec2.affixes || []).map(function(a){ return a.id; }),
              n: (dbTiles().filter(function(t){ return t.key === k; })[0] || {}).n };
out.large = place(2, 0, 'b:cm2');
out.largeN = (dbTiles().filter(function(t){ return t.n === 'Large Charm'; }).length);
out.builds = STORE['d2r_charBuilds'] === beforeBuilds;
out.sel = STORE['d2r_cbSel'] === beforeSel;
out.filed = FILED.map(function(f){ return f.n; });
out.hostErr = st().hostErr || '';
"""


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class AnInventoryCharmKeepsAPrefixAndASuffix(unittest.TestCase):

    def test_fine_and_of_balance_name_the_tile_and_the_hover(self):
        out = INV._drive(SCENARIO, store={"d2r_charBuilds": INV.BUILDS, "d2r_cbSel": "b1"})
        self.assertIs(out["placed"], True, "the small charm was not placed: %r" % out.get("hostErr"))
        self.assertEqual(out["tab"], "edit", "a charm did not open on Edit, so Add Mod is not the one on screen")
        self.assertTrue(out["addBtn"], "Edit does not offer the builder's Add Mod")
        self.assertIs(out["addFine"], True, "Fine was not added")
        self.assertIs(out["addBal"], True, "of Balance was not added")
        self.assertIs(out["addSturdy"], False, "an armour prefix was added to a charm")
        self.assertIs(out["addSecond"], False, "a second prefix was added to a magic charm")
        self.assertEqual(out["stored"], {"name": "Small Charm", "q": "m", "id": "b:cm1", "base": "cm1",
                                         "w": 1, "h": 1, "ids": ["p256", "s267"]},
                         "the store is not the base plus those two mods: %r" % out["stored"])
        self.assertIsNotNone(out["tile"], "the charm was not drawn")
        self.assertEqual({k: out["tile"][k] for k in ("n", "x", "y", "w", "h")},
                         {"n": NAME, "x": 0, "y": 0, "w": 1, "h": 1},
                         "the tile still says the base: %r" % out["tile"])
        self.assertTrue(out["aria"].startswith(NAME), "the spoken name is not the composed one: %r" % out["aria"])
        self.assertEqual(out["art"], "Small Charm", "the charm's picture is no longer its base")
        self.assertEqual(out["hover"], {"name": NAME, "q": "m", "lines": LINES},
                         "the hover is not Fine Small Charm of Balance with those three lines: %r" % out["hover"])
        self.assertIs(out["moved"]["ok"], True, "the charm could not be moved: %r" % out["moved"])
        self.assertEqual(out["after"], {"x": 5, "y": 2, "ids": ["p256", "s267"], "n": NAME},
                         "a move dropped the mods or the name: %r" % out["after"])
        self.assertIs(out["large"], True, "an unmodified large charm was not placed")
        self.assertEqual(out["largeN"], 1, "a charm with no mods was renamed")
        self.assertTrue(out["builds"], "Add Mod wrote d2r_charBuilds")
        self.assertTrue(out["sel"], "Add Mod wrote d2r_cbSel")
        self.assertEqual(out["filed"], [], "the composed name was filed: %r" % out["filed"])
        self.assertEqual(out["hostErr"], "")


RED_PROOF = [
    {
        "why": "the mule inventory write drops the charm's affixes",
        "file": "bible.html",
        "find": "                  affixes: e.affixes, eth: e.eth, ilvl: e.ilvl, rn: e.rn, lq: e.lq, def: e.def, fill: e.socketed,\n"
                "                  w: ft ? ft[0] : null, h: ft ? ft[1] : null };\n",
        "replace": "                  affixes: null, eth: e.eth, ilvl: e.ilvl, rn: e.rn, lq: e.lq, def: e.def, fill: e.socketed,\n"
                   "                  w: ft ? ft[0] : null, h: ft ? ft[1] : null };\n",
        "matches": 1,
    },
    {
        "why": "the tile and the list keep the base name after a prefix and a suffix",
        "file": "bible.html",
        "find": "      if (p && p.db && p.dbkey && typeof window._mpInvCbEntry === 'function' && typeof window._cbShown === 'function' && typeof window._cbItem === 'function'){\n",
        "replace": "      if (false && p && p.db && p.dbkey && typeof window._mpInvCbEntry === 'function' && typeof window._cbShown === 'function' && typeof window._cbItem === 'function'){\n",
        "matches": 1,
    },
    {
        "why": "the hover reads the art's name and not the stored mods",
        "file": "bible.html",
        "find": "    if (_ie && _iit && typeof window._cbTipEntry === 'function') entry = window._cbTipEntry(_ie, _iit, null, 'inv');\n",
        "replace": "    if (false && _ie && _iit && typeof window._cbTipEntry === 'function') entry = window._cbTipEntry(_ie, _iit, null, 'inv');\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("SKIP — node is not on this machine, so the charm mods were not driven. UNMEASURED.\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
