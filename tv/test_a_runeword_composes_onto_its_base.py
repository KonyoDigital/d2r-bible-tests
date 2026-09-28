# -*- coding: utf-8 -*-
"""Wave 2 — A RUNEWORD COMPOSES ONTO THE BASE ALREADY IN THE CELL.

GrokBot ACT 5855268494: the base comes first. Sacred Armor looks like Sacred Armor, white
name, its own defense, durability and requirements. Then Runewords, Chains of Honor, composes
onto that base. The picture stays Sacred Armor. The name, the rune string and the mods are
the runeword's, through the builder's one box. The first base of that word is Ancient Armor;
this law fails if the picture becomes that.

An empty cell still waits on the Base tab. Breath of the Dying cannot be made in Sacred
Armor, so the armor stays. A magic Sacred Armor is not a runeword base, so it stays too.
The door files the runeword once, not the generic base.

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

BASE_ROWS = [
    ("d2t-b", "Sacred Armor"),
    ("d2t-w", "Defense: (487-600)"),
    ("d2t-w", "Durability: 60 of 60"),
    ("d2t-w", "Required Strength: 232"),
    ("d2t-w", "Required Level: 66"),
]
ROWS = [
    ("d2t-r", "Chains of Honor"),
    ("d2t-g", "Sacred Armor"),
    ("d2t-r", "'DolUmBerIst'"),
    ("d2t-w", "Defense: (827-1020)"),
    ("d2t-w", "Durability: 60 of 60"),
    ("d2t-w", "Required Strength: 232"),
    ("d2t-w", "Required Level: 66"),
    ("d2t-p", "+2 to All Skills"),
    ("d2t-p", "+200% Damage to Demons"),
    ("d2t-p", "+100% Damage to Undead"),
    ("d2t-p", "8% Life stolen per hit"),
    ("d2t-p", "+70% Enhanced Defense"),
    ("d2t-p", "+20 to Strength"),
    ("d2t-p", "Replenish Life +7"),
    ("d2t-p", "All Resistances +65"),
    ("d2t-p", "Physical Damage Received Reduced by 8%"),
    ("d2t-p", "25% Better Chance of Getting Magic Items"),
    ("d2t-p", "Socketed (4)"),
]

SCENARIO = r"""
door();
window.openMuleCard('uni-armor');
var beforeBuilds = STORE['d2r_charBuilds'], beforeSel = STORE['d2r_cbSel'];
window._mpInvCell(0, 0);
out.placed = window._cbChoose('b:uar') && window._cbQuality('b');
var white = invList()[0];
out.white = { name: white.name, id: white.id, base: white.base, q: invStore()[white.key].q,
              x: white.x, y: white.y, w: white.w, h: white.h };
out.whiteArt = artOf(white.key);
out.whiteN = (dbTiles().filter(function(t){ return t.key === white.key; })[0] || {}).n;
function rowsOf(key){
  var seen = null, real = window.d2Tip.show;
  window.d2Tip.show = function(e){ seen = e; };
  fire('mouseover', { target: tileEl(key), buttons: 0 });
  window.d2Tip.show = real;
  if (!seen) return null;
  var html = window.d2Tip(seen), rows = [], re = /<div class="([^"]+)">([\s\S]*?)<\/div>/g, m;
  while ((m = re.exec(html))) rows.push({ c: m[1], t: unesc(m[2].replace(/<[^>]+>/g, '')),
    num: m[2].indexOf('class="d2t-num"') >= 0 });
  return rows.filter(function(r){ return r.c !== 'd2t-note'; });
}
out.whiteRows = rowsOf(white.key);
window._cbPickTab('select');
window._cbQt('r');
out.botd = window._cbChoose('r11');
out.botdTab = st().pick && st().pick.tab;
out.botdStill = invList().map(function(e){ return e.name + '@' + e.base; });
window._cbPickTab('select');
out.first = window._cbBasesOf(window._cbItem('r14'))[0];
out.chose = window._cbChoose('r14');
out.tab = st().pick && st().pick.tab;
var made = invList()[0], rec = invStore()[made.key];
out.made = { name: made.name, id: made.id, base: made.base, q: rec.q, sockets: rec.sockets,
             x: made.x, y: made.y, w: made.w, h: made.h, same: made.key === white.key };
out.art = artOf(made.key);
out.n = (dbTiles().filter(function(t){ return t.key === made.key; })[0] || {}).n;
out.rows = rowsOf(made.key);
out.defNum = (out.rows || []).filter(function(r){ return r.t.indexOf('Defense:') === 0; })[0] || null;
window._mpInvCell(null);
window._mpInvCell(4, 0);
out.empty = window._cbChoose('r14');
out.emptyTab = st().pick && st().pick.tab;
out.afterEmpty = invList().length;
window._mpInvCell(null);
window._mpInvCell(4, 0);
out.magic = window._cbChoose('b:uar') && window._cbQuality('m');
var mag = invList().filter(function(e){ return e.x === 4; })[0];
window._cbPickTab('select');
out.magicChose = window._cbChoose('r14');
out.magicTab = st().pick && st().pick.tab;
out.magicStill = { name: mag.name, id: invStore()[mag.key].id, q: invStore()[mag.key].q, base: mag.base };
out.magicArt = artOf(mag.key);
out.builds = STORE['d2r_charBuilds'] === beforeBuilds;
out.sel = STORE['d2r_cbSel'] === beforeSel;
out.filed = FILED.map(function(f){ return f.n; });
out.hostErr = st().hostErr || '';
"""


def _pairs(rows):
    return [(r["c"], r["t"]) for r in rows or []]


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class ARunewordComposesOntoItsBase(unittest.TestCase):

    def test_chains_of_honor_keeps_the_sacred_armor_picture(self):
        out = INV._drive(SCENARIO, store={"d2r_charBuilds": INV.BUILDS, "d2r_cbSel": "b1"})
        self.assertIs(out["placed"], True, "Sacred Armor was not placed: %r" % out.get("hostErr"))
        self.assertEqual(out["white"], {"name": "Sacred Armor", "id": "b:uar", "base": "uar", "q": "b",
                                         "x": 0, "y": 0, "w": 2, "h": 3})
        self.assertEqual(out["whiteArt"], "Sacred Armor", "the base's picture is not Sacred Armor")
        self.assertEqual(out["whiteN"], "Sacred Armor")
        self.assertEqual(_pairs(out["whiteRows"]), BASE_ROWS,
                         "the base hover is not Sacred Armor's own lines: %r" % out["whiteRows"])
        self.assertIs(out["botd"], True)
        self.assertEqual(out["botdTab"], "base", "a weapon runeword composed onto Sacred Armor")
        self.assertEqual(out["botdStill"], ["Sacred Armor@uar"])
        first = INV._db()["b"][out["first"]][0]
        self.assertNotEqual(first, "Sacred Armor",
                            "Chains of Honor's first base is Sacred Armor, so this law cannot tell a swap")
        self.assertIs(out["chose"], True, "Chains of Honor was not composed: %r" % out.get("hostErr"))
        self.assertEqual(out["tab"], "edit", "choosing the runeword opened the Base tab instead of composing")
        self.assertEqual(out["made"], {"name": "Chains of Honor", "id": "r14", "base": "uar", "q": "r",
                                        "sockets": 4, "x": 0, "y": 0, "w": 2, "h": 3, "same": True},
                         "the cell is not Chains of Honor on Sacred Armor: %r" % out["made"])
        self.assertEqual(out["art"], "Sacred Armor", "the picture left Sacred Armor for %r (first base %s)"
                         % (out["art"], first))
        self.assertEqual(out["n"], "Chains of Honor", "the tile does not say the runeword")
        self.assertEqual(_pairs(out["rows"]), ROWS, "the hover is not the runeword on that base: %r" % out["rows"])
        self.assertTrue(out["defNum"] and out["defNum"]["num"], "the defense number is not the blue number")
        self.assertIs(out["empty"], True)
        self.assertEqual(out["emptyTab"], "base", "an empty cell no longer waits on the Base tab")
        self.assertEqual(out["afterEmpty"], 1, "choosing a runeword on an empty cell placed it")
        self.assertIs(out["magic"], True, "a magic Sacred Armor was not placed")
        self.assertIs(out["magicChose"], True)
        self.assertEqual(out["magicTab"], "base", "a magic base took a runeword")
        self.assertEqual(out["magicStill"], {"name": "Sacred Armor", "id": "b:uar", "q": "m", "base": "uar"})
        self.assertEqual(out["magicArt"], "Sacred Armor")
        self.assertTrue(out["builds"], "the compose wrote d2r_charBuilds")
        self.assertTrue(out["sel"], "the compose wrote d2r_cbSel")
        self.assertEqual(out["filed"], ["Chains of Honor"], "the door did not file the runeword once: %r" % out["filed"])
        self.assertEqual(out["hostErr"], "")


RED_PROOF = [
    {
        "why": "a runeword chosen onto a white base opens the Base tab instead of composing",
        "file": "bible.html",
        "find": "    if (it[2] === 'r' && it[7] && it[7].runes){\n"
                "      var held = _cbCurEntry(), hq = held && (held.q || 'b');\n",
        "replace": "    if (false && it[2] === 'r' && it[7] && it[7].runes){\n"
                   "      var held = _cbCurEntry(), hq = held && (held.q || 'b');\n",
        "matches": 1,
    },
    {
        "why": "the composed runeword takes its first base and the picture leaves Sacred Armor",
        "file": "bible.html",
        "find": "        eC.base = held.base;\n",
        "replace": "        eC.base = eC.base;\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("SKIP — node is not on this machine, so the compose was not driven. UNMEASURED.\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
