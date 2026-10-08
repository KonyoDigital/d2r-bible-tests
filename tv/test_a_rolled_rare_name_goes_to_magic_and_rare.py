# -*- coding: utf-8 -*-
"""REG-2024 - A RARE'S ROLLED NAME GOES TO MAGIC & RARE, NEVER TO A SLOT DRAWER BY ONE WORD. #269, GrokBot ticks 411/412.

GrokBot on his v3616 board: Dread Grasp in UNI-ARMOR and Storm Scarab in UNI-WEAPONS, each tipped "Base item · TV-vaulted
· Not a grail item". MEASURED on the shipped page: Dread Grasp -> uni-armor ("armor slot — base: name match"); Storm
Scarab, Death Loop, Viper Eye, Bitter Spiral, Doom Spiral -> uni-weap ("nothing on the board recognises this name"). They
are rares - one RarePrefix word + one RareSuffix word (RARE_NAME_PREFIXES / RARE_NAME_POOLS, the board's own v332 tables) -
and rolled-name keepers live in MAGIC & RARE. The rule asks only when NO catalogue knows the name, so a real item (Raven
Frost: "Raven" is a rare prefix too) keeps its own route, and a white base keeps its throw-out advice.
⚠ The catalogue check has NO live subject today: measured over ITEM_REGISTRY + ITEMS, the one catalogued name in the rare
shape is Rune Master, and the router files it by its base (BASE_DB) before this rule. A sabotage of the check cannot go red,
so it is not declared as a red-proof - it stays as a guard for a future catalogue name, said here rather than counted.
NO CHROME AT ALL = a declared skip, never a pass.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_a_sweep_never_reticks_what_he_unticked as H  # noqa: E402  (its Board drives the shipped page)

_B = {}
ROLLED = ("Dread Grasp", "Storm Scarab", "Death Loop", "Viper Eye", "Bitter Spiral", "Doom Spiral")
MAGIC = ("Chaotic Grand Charm of Greed", "Grand Charm of Inertia", "Steel Grand Charm of Balance")


def board():
    if "b" not in _B:
        _B["b"] = H.Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class ARolledRareNameGoesToMagicAndRare(unittest.TestCase):

    def test_the_rolled_names_go_to_magic_and_rare_and_real_items_keep_their_route(self):
        o = board().run("OUT.r = {}; %s.forEach(function(n){ var s = window.suggestMule(n); OUT.r[n] = s ? s.id : null; });"
                        % repr(list(ROLLED) + list(MAGIC) + ["Raven Frost", "Heavy Belt", "Nokozan Relic"]).replace("'", '"'))["r"]
        for n in ROLLED:
            self.assertEqual(o[n], "magic-rare", "%s - a rare's rolled name - was filed into %r by one word" % (n, o[n]))
        for n in MAGIC:   # REG-2054 (#269, tick 416 K05) - a magic charm is a rolled-name keeper too
            self.assertEqual(o[n], "magic-rare", "%s - a magic grand charm - was filed into %r" % (n, o[n]))
        self.assertEqual(o["Raven Frost"], "shared", "a real item that shares a rare prefix lost its own route")
        self.assertEqual(o["Heavy Belt"], "__throwout", "a white base lost its throw-out advice")
        self.assertEqual(o["Nokozan Relic"], "uni-small", "the control: a catalogued unique amulet moved")


    def test_a_name_tv_already_registered_routes_the_same(self):
        # REG-2054 (GrokBot tick 419 K10) - HIS board, not a fresh one: every one of these was registered by TV first, as a
        # stub whose base is its own name. The rule asked `!base`, the stub answered with the name, and nothing moved.
        names = list(ROLLED) + list(MAGIC)
        o = board().run("OUT.r = {}; %s.forEach(function(n){ window._tvExtraRemember(n, { rarity: 'basic', base: n, "
                        "cat: 'TV-vaulted', val: 'tv' }); var s = window.suggestMule(n); OUT.r[n] = s ? s.id : null; });"
                        % repr(names).replace("'", '"'))["r"]
        for n in names:
            self.assertEqual(o[n], "magic-rare", "%s - registered by TV as a stub - was filed into %r" % (n, o[n]))


RED_PROOF = [
    {"why": "REG-2054 - a TV stub answers through the curated-EXTRA branch again (a magic grand charm -> UNI-SMALL)",
     "file": "bible.html",
     "find": "      if (ex && ex.val === 'tv' && !((_itip0 && _itip0.b) || (tip && tip.base)) && typeof _rolledQuality === 'function'){\n",
     "replace": "      if (false){\n",
     "matches": 1},
    {"why": "REG-2054 - a TV stub's own name counts as its base again, so a registered rare never routes",
     "file": "bible.html",
     "find": "      var _catBase = (itip && itip.b) || (tip && tip.base) || '';\n",
     "replace": "      var _catBase = base;\n",
     "matches": 1},
    {"why": "REG-2024 - a rare's rolled name is filed into a slot drawer by one word again",
     "file": "bible.html",
     "find": "  if (w.length === 2 && RARE_NAME_PREFIXES.indexOf(w[0]) >= 0){\n",
     "replace": "        if (false){\n",
     "matches": 1},
    {"why": "REG-2054 - a magic grand charm is filed into UNI-SMALL again",
     "file": "bible.html",
     "find": "      if (_rq && _rq.q === 'magic' && muleById('magic-rare'))\n",
     "replace": "      if (false)\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
