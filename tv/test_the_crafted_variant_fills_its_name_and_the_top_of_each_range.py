# -*- coding: utf-8 -*-
"""#95 — A CRAFTED AMULET FILLS ITS NAME AND THE TOP OF EACH RANGE.

Add Mod stays the planner's list for that item. Magic and rare still store a blank roll
(typed = exact, blank = the range). A crafted variant is offered only on a wearable amulet.
Choosing it fills the rare name — Grim and Noose when the tables offer them, otherwise the
first legal word of each list — and the shown name is those words plus the base name in one
string (Grim Noose Amulet). A pick on that quality stores the high end of each numeric range
under the affix's own key. A class choice stays blank. A ring and a diadem keep the quality
lists they already had. Nothing is written to the vault stores.

Drives the shipped builder through tv/test_the_character_builder_is_their_builder.py's harness.
A missing node raises. This law does not skip.
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

import test_the_character_builder_is_their_builder as CB  # noqa: E402

HELP = r"""
function mk(cls, lvl){ window.openCharBuilder(); window._cbOpenNew(); window._cbNewCls(cls); window._cbNewLvl(lvl); window._cbNewGo(); }
function cur(){ return window._cbAll()[window._cbState().bid]; }
function opts(){ return (MODAL._html.match(/data-q="[a-z]+"/g) || []).map(function(x){ return x.slice(8, -1); }); }
function vaultSnap(){ var o = {}; ['d2r_muleAssign','d2r_owned','d2r_muleEquip','d2r_muleRoster','d2r_foundLog'].forEach(function(k){ o[k] = RAW[k]; }); return o; }
function vaultSame(b){ return ['d2r_muleAssign','d2r_owned','d2r_muleEquip','d2r_muleRoster','d2r_foundLog'].every(function(k){ return RAW[k] === b[k]; }); }
"""


def _run(body):
    if CB.NODE is None:
        raise AssertionError("node is not on this machine — this gate does not skip")
    return CB._run(HELP + body)


class TheCraftedVariantFillsItsNameAndTheTopOfEachRange(unittest.TestCase):

    def test_an_amulet_fills_its_crafted_name(self):
        out = _run(r"""
          mk('Warlock', 90);
          var before = vaultSnap();
          window._cbOpenPick('slot', 'neck'); window._cbChoose('b:amu');
          OUT.opts = opts();
          OUT.craftBtn = /class="cb-opt cb-c-c" role="option" data-q="c"[^>]*>Crafted</.test(MODAL._html);
          OUT.words0 = window._cbRareWords('amu', 0);
          OUT.words1 = window._cbRareWords('amu', 1);
          window._cbQuality('rare');
          window._cbRareName(0, 'Beast');
          window._cbRareName(1, 'Wing');
          OUT.wasRare = cur().sets[0].slots.neck.rn.slice();
          OUT.chose = window._cbQuality('c');
          var e = cur().sets[0].slots.neck, it = window._cbItem(e.id), sh = window._cbShown(e, it);
          OUT.entry = { q: e.q, rn: e.rn, name: sh.name, base: sh.base, qShown: sh.q };
          OUT.nameSpan = /id="cb-ed-name"[^>]*>[^<]*<span/.test(MODAL._html);
          OUT.vip = window._cbCanQ('vip');
          OUT.vaultSame = vaultSame(before);
        """)
        words0, words1 = out["words0"], out["words1"]
        self.assertIn("Grim", words0)
        self.assertIn("Noose", words1)
        w0 = "Grim" if "Grim" in words0 else words0[0]
        w1 = "Noose" if "Noose" in words1 else words1[0]
        self.assertEqual(out["opts"], ["rare", "m", "c"], "a wearable amulet offers crafted after the qualities it can drop")
        self.assertTrue(out["craftBtn"], "the crafted button is not the crafted colour")
        self.assertEqual(out["wasRare"], ["Beast", "Wing"])
        self.assertTrue(out["chose"], "choosing crafted on an amulet did not take")
        self.assertEqual(out["entry"]["q"], "c")
        self.assertEqual(out["entry"]["rn"], [w0, w1], "a crafted amulet did not replace the rare name it already had")
        self.assertEqual(out["entry"]["name"], w0 + " " + w1 + " Amulet")
        self.assertEqual(out["entry"]["base"], "")
        self.assertEqual(out["entry"]["qShown"], "c")
        self.assertFalse(out["nameSpan"], "the base name is a second span instead of part of the crafted name")
        self.assertNotIn("c", out["vip"], "the Horadric staff top is not a wearable amulet")
        self.assertTrue(out["vaultSame"], "the crafted edit wrote a vault store")

    def test_a_ring_and_a_diadem_keep_their_own_qualities(self):
        out = _run(r"""
          mk('Warlock', 90);
          window._cbOpenPick('slot', 'head'); window._cbChoose('b:ci3');
          OUT.diadem = opts();
          window._cbClosePick();
          window._cbOpenPick('slot', 'rrin'); window._cbChoose('b:rin');
          OUT.ring = opts();
          window._cbQuality('m');
          OUT.stuck = window._cbQuality('c');
          OUT.ringQ = cur().sets[0].slots.rrin.q;
        """)
        self.assertEqual(out["diadem"], ["rare", "m", "sup", "b", "low"])
        self.assertEqual(out["ring"], ["rare", "m"])
        self.assertFalse(out["stuck"], "crafted stuck on a ring")
        self.assertEqual(out["ringQ"], "m")

    def test_a_crafted_pick_stores_the_top_and_a_magic_pick_stays_blank(self):
        out = _run(r"""
          mk('Warlock', 90);
          var before = vaultSnap();
          window._cbOpenPick('slot', 'neck'); window._cbChoose('b:amu'); window._cbQuality('c');
          var e = cur().sets[0].slots.neck, P = window._cbAffixPool(e);
          var pick = null, key = null, hi = null;
          P.rows.p.some(function(a){
            var hit = null;
            (a[11] || []).forEach(function(ln){
              (ln[1] || []).forEach(function(r){
                if (r && typeof r[0] === 'number' && typeof r[1] === 'number' && r[0] !== r[1])
                  hit = { key: r[2], hi: Math.max(r[0], r[1]) };
              });
            });
            if (!hit) return false;
            pick = a[0]; key = hit.key; hi = hit.hi; return true;
          });
          OUT.pick = { id: pick, key: key, hi: hi };
          OUT.added = pick ? window._cbAddMod(pick) : false;
          OUT.stored = cur().sets[0].slots.neck.affixes;
          OUT.say = window._cbState().modSay;
          OUT.fortuitous = ['p', 's', 'a'].some(function(k){ return P.rows[k].some(function(a){ return a[0] === 'p282'; }); });
          OUT.refused = window._cbAddMod('p282');
          OUT.after = cur().sets[0].slots.neck.affixes;
          window._cbClosePick();
          window._cbOpenPick('inv', null, [0, 0]); window._cbChoose('b:cm3');
          OUT.magicFixed = window._cbAddMod('p700');
          OUT.magicAdded = window._cbAddMod('s338');
          var inv = cur().sets[0].inv; OUT.magicStored = inv[inv.length - 1].affixes;
          OUT.magicSay = window._cbState().modSay;
          OUT.vaultSame = vaultSame(before);
        """)
        pick = out["pick"]
        self.assertTrue(pick["id"] and pick["key"] and pick["hi"] is not None, "no ranged prefix on a crafted amulet: %s" % pick)
        self.assertTrue(out["added"])
        stored = out["stored"]
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["id"], pick["id"])
        self.assertEqual(stored[0]["rolls"].get(pick["key"]), pick["hi"])
        self.assertIn("top of its range", out["say"])
        self.assertIn(str(pick["hi"]), out["say"])
        self.assertFalse(out["fortuitous"], "Fortuitous (rare flag 0) is offered on a crafted amulet")
        self.assertFalse(out["refused"], "a mod the pool does not offer was added")
        self.assertEqual(out["after"], stored)
        self.assertTrue(out["magicFixed"] and out["magicAdded"])
        self.assertEqual(out["magicStored"], [{"id": "p700", "rolls": {}}, {"id": "s338", "rolls": {}}])
        self.assertIn("leave it blank", out["magicSay"])
        self.assertTrue(out["vaultSame"], "the crafted edit wrote a vault store")


if __name__ == "__main__":
    unittest.main(verbosity=2)
