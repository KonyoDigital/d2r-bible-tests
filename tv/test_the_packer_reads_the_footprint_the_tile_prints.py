# -*- coding: utf-8 -*-
"""#275 (REG-2051) - THE MULE PACKER READS THE FOOTPRINT EVERY LOCKER TILE PRINTS; A GUESSED SIZE SAYS SO ON THE CHIP.

GrokBot ticks 416-417 on #230 (v3621): UNI-WEAPONS read "3 items · 12 cells" over three tiles that each said "default
1x2" (6), and UNI-ARMOR "24 cells" over tiles summing to 22 - "the chip looks like items x 4". MEASURED at HEAD: the
packer (vaultSize, behind the chip, the gauge and the mule window) carried its OWN keyword table whose unknown-base
default was [2,2], while the tile prints _itemCells (unknown base -> a 1x2 marked approx; EXTRA_ITEMS.cells honoured;
the v2240 plural and v2242 claw fixes). Two copies of one rule, and they disagreed.

  * vaultSize answers exactly what _itemCells answers - an unknown base, an explicit EXTRA_ITEMS size, a known base;
  * the locker chip says how many of its items are of unknown size, counted at the default.
Drives the SHIPPED vaultSize and _itemCells, cut from bible.html and run in node with the catalogues stubbed. A missing
node raises; this law does not skip.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
from cb_node_harness import NODE  # noqa: E402

PAGE = os.path.join(os.path.dirname(HERE), "bible.html")
CELLS_START = "var _ITEM_CELLS_CACHE = {};\nfunction _itemCells(name){\n"
CELLS_END = "\n  return cells;\n}\n"
SIZE_START = "  function vaultSize(name){\n"
SIZE_END = "\n  }\n"
CHIP = "(_approxN ? ' (' + _approxN + ' of unknown size, counted at the default 1x2)' : '')"


def _src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


def _cut(s, start, end):
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start[:40], s.count(start)))
    i = s.index(start)
    return s[i:s.index(end, i) + len(end)]


def _sizes(names):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    js = """
var EXTRA_ITEMS = { "Odd Trophy": { base: "Mystery Base", cells: { w: 2, h: 4 } } };
var ITEM_CODEX = { "Rainbow Facet": { rarity: "unique", base: "Jewels" }, "Bartuc's Cut-Throat": { base: "Greater Talons" },
                   "Shaftstop": { base: "Mesh Armor" }, "Nosferatu's Coil": { base: "Vampirefang Belt" } };
var ITEM_TIP = {};
var RUNEWORD_TIP = { "Enigma": { t: "Runeword", b: "3 socket Body Armor" }, "Spirit": { t: "Runeword", b: "4 socket Swords or Shields" },
                     "Hand of Justice": { t: "Runeword", b: "4 socket Weapons" }, "Delirium": { t: "Runeword", b: "3 socket Helms" } };
function findRuneword(n){ return RUNEWORD_TIP[n] ? n : null; }
%s
%s
var OUT = {};
%s.forEach(function(n){ var c = _itemCells(n); OUT[n] = { pack: vaultSize(n), tile: [c.w, c.h], approx: !!c.approx }; });
console.log(JSON.stringify(OUT));
""" % (_cut(s, CELLS_START, CELLS_END), _cut(s, SIZE_START, SIZE_END), json.dumps(names))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut functions did not run in node: %s" % r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class ThePackerReadsTheFootprintTheTilePrints(unittest.TestCase):

    NAMES = ["Some Unheard-Of Thing", "Odd Trophy", "Rainbow Facet", "Bartuc's Cut-Throat", "Shaftstop",
             "Nosferatu's Coil", "Annihilus", "Gheed's Fortune"]

    def test_the_packer_and_the_tile_agree_on_every_kind_of_name(self):
        got = _sizes(self.NAMES)
        for n in self.NAMES:
            self.assertEqual(got[n]["pack"], got[n]["tile"],
                             "%s: the packer packs %r while its tile prints %r" % (n, got[n]["pack"], got[n]["tile"]))

    def test_an_unknown_base_packs_at_the_default_the_tile_names(self):
        got = _sizes(["Some Unheard-Of Thing"])["Some Unheard-Of Thing"]
        self.assertTrue(got["approx"], "premise: an unheard-of base is a guessed size")
        self.assertEqual(got["pack"], [1, 2], "an unknown base packs at a size its tile does not print: %r" % got)

    def test_an_explicit_size_is_honoured_by_the_packer(self):
        self.assertEqual(_sizes(["Odd Trophy"])["Odd Trophy"]["pack"], [2, 4])

    def test_a_runeword_is_sized_by_its_base_never_by_its_name(self):
        got = _sizes(["Enigma", "Delirium", "Spirit", "Hand of Justice"])
        self.assertEqual((got["Enigma"]["tile"], got["Enigma"]["approx"]), ([2, 3], False),
                         "Enigma (3 socket Body Armor) is not drawn as the body armour it always is: %r" % got["Enigma"])
        self.assertEqual((got["Delirium"]["tile"], got["Delirium"]["approx"]), ([2, 2], False), got["Delirium"])
        self.assertTrue(got["Spirit"]["approx"], "a runeword whose base names two classes was given a size: %r" % got["Spirit"])
        self.assertTrue(got["Hand of Justice"]["approx"],
                        "a runeword was sized by a keyword in its NAME (Hand -> gloves): %r" % got["Hand of Justice"])
        for n in got:
            self.assertEqual(got[n]["pack"], got[n]["tile"], n)

    def test_the_chip_says_how_many_sizes_are_guessed(self):
        s = _src()
        self.assertEqual(s.count(CHIP), 1, "the locker chip no longer says how many of its sizes are guessed")
        self.assertEqual(s.count("var _approxN = items.filter(function(n){ var c = (typeof _itemCells === 'function')"
                                 " ? _itemCells(n) : null; return !!(c && c.approx); }).length;"), 1,
                         "the chip's guessed-size count is no longer asked of _itemCells")


RED_PROOF = [
    {"why": "REG-2051 - a runeword falls to the default again although its base settles its size (Enigma 1x2)",
     "file": "bible.html",
     "find": "        if (/^\\d+\\s+socket\\s+body armou?r$/.test(_rwb)) cells = {w:2,h:3};\n",
     "replace": "        if (false) cells = {w:2,h:3};\n",
     "matches": 1},
    {"why": "REG-2051 - a runeword is sized by a keyword in its name again (Hand of Justice read as gloves)",
     "file": "bible.html",
     "find": "        _ITEM_CELLS_CACHE[name] = cells;\n        return cells;\n      }\n",
     "replace": "      }\n",
     "matches": 1},
    {"why": "REG-2051 - the packer answers with its own default again (a second copy of the footprint rule)",
     "file": "bible.html",
     "find": "    return c ? [c.w || 1, c.h || 1] : [1, 2];\n",
     "replace": "    return (c && !c.approx) ? [c.w || 1, c.h || 1] : [2, 2];\n",
     "matches": 1},
    {"why": "REG-2051 - the chip stops saying how many sizes are guessed",
     "file": "bible.html",
     "find": "(_approxN ? ' (' + _approxN + ' of unknown size, counted at the default 1x2)' : '')",
     "replace": "''",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
