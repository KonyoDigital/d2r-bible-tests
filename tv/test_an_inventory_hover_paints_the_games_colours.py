# -*- coding: utf-8 -*-
"""Wave 2 — A MULE HOVER PAINTS THE GAME'S TOOLTIP COLOURS.

GrokBot ACT 5855265931: the hover on an inventory item is the game's box, and each line has a
colour role. The builder's one box (window.d2Tip) already paints them. This law does not add a
second map. It drives the mule window's own hover, the same mouseover the footprint law fires,
and reads the HTML that box returns.

Measured on the Chains of Honor frame (maxroll, 2026-09-27): the runeword name is gold, the base
under it is grey rgb(121, 121, 121), the rune string is gold again, a defense label is white and
its number is blue, a met requirement is white, and the property lines are blue. Andariel's
Visage on the same planner keeps its base in the name's gold, not that grey. A mule has no
character level, so a requirement stays white: never red on a guess.

Annihilus: gold name, gold base, white charm line, blue properties. Fine Small Charm of Balance:
blue name, no second base line, blue properties. Enigma on Mage Plate: gold name, grey base, gold
rune string, a white defense label with a blue number, a white durability line.
RED_PROOF below.
"""
import json
import os
import re
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

import test_the_character_builder_is_their_builder as CB  # noqa: E402
import test_the_mule_inventory_takes_items_like_the_doll as INV  # noqa: E402

NODE = INV.NODE

SCENARIO = r"""
var I = %s;
door();
window.openMuleCard('uni-armor');
out.anni = place(4, 0, I.Annihilus);
out.fine = place(5, 0, 'b:cm1');
out.addFine = window._cbAddMod('p256');
out.addBal = window._cbAddMod('s267');
window._mpInvCell(null);
window._mpInvCell(0, 0);
out.chose = window._cbChoose(I.Enigma);
out.tab = st().pick && st().pick.tab;
out.baseOk = window._cbPickBase('xtp');
window._mpInvCell(null);
function rowsOf(key){
  var seen = null, real = window.d2Tip.show;
  window.d2Tip.show = function(e){ seen = e; };
  fire('mouseover', { target: tileEl(key), buttons: 0 });
  window.d2Tip.show = real;
  if (!seen) return null;
  var html = window.d2Tip(seen), rows = [], re = /<div class="([^"]+)">([\s\S]*?)<\/div>/g, m;
  while ((m = re.exec(html))) rows.push({ c: m[1], t: unesc(m[2].replace(/<[^>]+>/g, '')),
    num: m[2].indexOf('class="d2t-num"') >= 0 });
  return rows;
}
out.anniRows = rowsOf(keyOf('Annihilus'));
out.fineRows = rowsOf(keyOf('Small Charm'));
out.enigmaRows = rowsOf(keyOf('Enigma'));
out.hostErr = st().hostErr || '';
"""


def _grey():
    css = CB._builder_css(CB._src())
    m = re.search(r"\.d2tip \.d2t-g\{color:([^;}]+)", css)
    return m.group(1).strip() if m else None


def _row(rows, text):
    hit = [r for r in rows if r["t"] == text or r["t"].startswith(text)]
    return hit[0] if hit else None


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class AnInventoryHoverPaintsTheGamesColours(unittest.TestCase):

    def test_the_hover_uses_the_games_colour_roles(self):
        ids = INV._ids(("Annihilus", "u"), ("Enigma", "r"))
        out = INV._drive(SCENARIO % json.dumps(ids),
                         store={"d2r_charBuilds": INV.BUILDS, "d2r_cbSel": "b1"})
        self.assertIs(out["anni"], True, "Annihilus was not placed")
        self.assertIs(out["fine"], True, "the small charm was not placed")
        self.assertIs(out["addFine"], True, "Fine was not added")
        self.assertIs(out["addBal"], True, "of Balance was not added")
        self.assertEqual(out["tab"], "base", "Enigma did not open on its Base tab")
        self.assertIs(out["chose"], True)
        self.assertIs(out["baseOk"], True, "Mage Plate was not the base: %r" % out.get("hostErr"))
        self.assertEqual(out["hostErr"], "")
        self.assertEqual(_grey(), "rgb(121,121,121)",
                         "the runeword base is not the measured grey")

        anni = out["anniRows"]
        self.assertIsNotNone(anni, "the Annihilus hover painted no box")
        self.assertEqual(_row(anni, "Annihilus")["c"], "d2t-u", "the unique name is not gold")
        self.assertEqual(_row(anni, "Small Charm")["c"], "d2t-u",
                         "a unique's base is not the name's gold")
        self.assertEqual(_row(anni, "Keep in Inventory to Gain Bonus")["c"], "d2t-w")
        self.assertEqual(_row(anni, "Required Level: 70")["c"], "d2t-w",
                         "a mule with no character level painted a requirement red")
        self.assertEqual(_row(anni, "+1 to All Skills")["c"], "d2t-p")

        fine = out["fineRows"]
        self.assertEqual(_row(fine, "Fine Small Charm of Balance")["c"], "d2t-m",
                         "the magic name is not blue")
        self.assertIsNone(_row(fine, "Small Charm"), "a magic charm drew a second base line")
        self.assertEqual(_row(fine, "+5% Faster Hit Recovery")["c"], "d2t-p")
        self.assertEqual(_row(fine, "1-3 to Maximum Damage")["c"], "d2t-p")
        self.assertEqual(_row(fine, "10-20 to Attack Rating")["c"], "d2t-p")

        en = out["enigmaRows"]
        self.assertEqual(_row(en, "Enigma")["c"], "d2t-r", "the runeword name is not gold")
        self.assertEqual(_row(en, "Mage Plate")["c"], "d2t-g", "the base under a runeword is not grey")
        rune = _row(en, "'JahIthBer'")
        self.assertIsNotNone(rune, "the rune string is missing: %r" % en)
        self.assertEqual(rune["c"], "d2t-r", "the rune string is not the runeword's gold")
        defense = _row(en, "Defense:")
        self.assertEqual(defense["c"], "d2t-w", "the defense label is not white")
        self.assertTrue(defense["num"], "the defense number is not blue")
        dura = _row(en, "Durability:")
        self.assertEqual(dura["c"], "d2t-w")
        self.assertFalse(dura["num"], "durability's numbers left the white line")
        self.assertEqual(_row(en, "+2 to All Skills")["c"], "d2t-p")


RED_PROOF = [
    {
        "why": "the name line loses the quality colour",
        "file": "bible.html",
        "find": "    var h = '<div class=\"' + qc + '\">' + esc(entry.name || '') + '</div>';\n",
        "replace": "    var h = '<div class=\"d2t-w\">' + esc(entry.name || '') + '</div>';\n",
        "matches": 1,
    },
    {
        "why": "a runeword base is painted in the name colour instead of the measured grey",
        "file": "bible.html",
        "find": "    if (entry.base && entry.base !== entry.name) h += '<div class=\"' + (entry.baseUnknown ? 'd2t-unk' : (entry.baseGrey ? 'd2t-g' : qc)) + '\">' + esc(entry.base) + '</div>';\n",
        "replace": "    if (entry.base && entry.base !== entry.name) h += '<div class=\"' + (entry.baseUnknown ? 'd2t-unk' : qc) + '\">' + esc(entry.base) + '</div>';\n",
        "matches": 1,
    },
    {
        "why": "the defense number leaves the blue role",
        "file": "bible.html",
        "find": "    return '<div class=\"' + (cls || 'd2t-w') + '\">' + (k < 0 ? esc(s) : esc(s.slice(0, k)) + '<span class=\"d2t-num\">' + esc(_d2tFill(s.slice(k), vals)) + '</span>') + '</div>';\n",
        "replace": "    return '<div class=\"' + (cls || 'd2t-w') + '\">' + (k < 0 ? esc(s) : esc(s.slice(0, k)) + esc(_d2tFill(s.slice(k), vals))) + '</div>';\n",
        "matches": 1,
    },
    {
        "why": "the measured grey of a runeword base is no longer that grey",
        "file": "bible.html",
        "find": ".d2tip .d2t-g{color:rgb(121,121,121)}\n",
        "replace": ".d2tip .d2t-g{color:rgb(80,80,80)}\n",
        "matches": 1,
    },
    {
        "why": "the mule hover stops using the stored entry and paints the art's name",
        "file": "bible.html",
        "find": "    if (_ie && _iit && typeof window._cbTipEntry === 'function') entry = window._cbTipEntry(_ie, _iit, null, 'inv');\n",
        "replace": "    if (false && _ie && _iit && typeof window._cbTipEntry === 'function') entry = window._cbTipEntry(_ie, _iit, null, 'inv');\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("SKIP — node is not on this machine, so the hover colours were not driven. UNMEASURED.\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
