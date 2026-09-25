# -*- coding: utf-8 -*-
"""#174 v-B2 — THE CHARACTER SHEET SUMS THE GAME'S OWN PROPERTY DATA, AND EVERY NUMBER SAYS WHERE IT CAME FROM.

HIS ORDER, 2026-09-25 ~18:25: "link the data to the character like physical damage percentage and fire absorb cold
absorb magic dmg % add all the information and data based on the items buffs that it gives it should calculate the
total sum of it all correctly. based on HELL and its data like the resistances starting with -100%".

THE DEFECT THIS LAW EXISTS FOR: a sheet that reads a confident number it did not earn — an untouched roll averaged or
pushed to its max, a Hell penalty missing, a cap that never binds, a property it could not read summed as 0 or dropped.
So every case below is DRIVEN on the SHIPPED engine (the <script id="v174-char-engine-js"> element of bible.html, cut
out whole and run in node over the SHIPPED CHAR_PROPS block), and every expected number is worked BY HAND from the
game's tables, never read back from the engine.

THE GAME DATA THE ANSWERS COME FROM (his install, 2026-09-25; the premise case re-reads each line from the shipped
block, so a patch that moves one fails as "the premise moved", not as an engine bug):
    difficultylevels.txt ResistPenalty       Normal 0 · Nightmare -40 · Hell -100
    properties.txt res-all                   func 1 fireresist, func 3 lightresist / coldresist / poisonresist
    properties.txt red-dmg%                  func 1 damageresist
    uniqueitems.txt Crown of Ages (Corona, armor.txt 111-165)      res-all 20..30 · ac 100..150 · ac% 50 · red-dmg% 10..15
    uniqueitems.txt Skin of the Vipermagi (Serpentskin 111-126)    res-all 20..35 · ac% 120 · cast3 30
    uniqueitems.txt Mara's Kaleidoscope (Amulet)                   res-all 20..30
    uniqueitems.txt The Oculus (Swirling Crystal)                  res-all 20 · sor 3 (class id 1) · cast2 30
    uniqueitems.txt Stormshield (Monarch 133-148)                  red-dmg% 35 · ac/lvl par 30
    uniqueitems.txt Verdungo's Hearty Cord (Mithril Coil 58-65)    red-dmg% 10..15 · ac% 90..140
    uniqueitems.txt Guardian Angel (Templar Coat)                  res-all-max 15
    uniqueitems.txt Wraithstep                                     skilltab-war 1 — a code properties.txt DOES NOT HAVE
    runes.txt Enigma                                               mag%/lvl par 8 (itemstatcost op param 3 = /8)
    Anya's scroll: +10 all resistances per difficulty completed — a quest reward no table holds, applied as a rule

THE HAND-WORKED ANSWERS:
  A  Hell, quests on (3 scrolls = +30); Crown of Ages TYPED 30, Vipermagi, Mara's and The Oculus untouched:
       fire = -100 + 30 + 30 + (20..35) + (20..30) + 20 = 20..45, cap 75 -> 20..45 RANGE (all four resistances).
       ⚠ The brief wrote "Crown of Ages 30"; the table says 20..30, so the brief's figure is a TYPED roll. Untouched:
  B  the same with Crown of Ages untouched: -100 + 30 + (20..30) + (20..35) + (20..30) + 20 = 10..45.
  C  Vipermagi TYPED 35 narrows A: -100 + 30 + 30 + 35 + (20..30) + 20 = 35..45.
  D  Crown of Ages alone, quests OFF: Normal 0 + 20..30 = 20..30 · Nightmare -40 -> -20..-10 · Hell -100 -> -80..-70.
  E  quests off at Hell is exactly 30 lower than on: B's ... Crown alone, on = -100 + 30 + 20..30 = -50..-40.
  F  PDR: Stormshield 35 + Verdungo's 10..15 = 45..50, cap 50 -> 45..50. Add Crown of Ages 10..15 -> raw 55..65,
       shown 50..50 with the raw beside it.
  G  the 75 cap binds: Normal, quests on (+10), Crown 30 + Vipermagi 35 + Mara's 30 typed + Oculus 20 = raw 125 -> 75.
  H  max resistance lifts it: Normal, quests on, Guardian Angel (+15 max all) + Crown 30 + Mara's 30 typed + Oculus 20
       + Annihilus 20 typed = raw 10 + 30 + 30 + 20 + 20 = 110, cap 75 + 15 = 90 -> 90.
  I  an unmapped prop -> UNKNOWN naming the item: Wraithstep's skilltab-war is a row of its own, value null, and the
       rest still sums (its move1 30 -> FRW 30 EXACT). An item the data does not name makes every item row UNKNOWN
       naming it — never a 0.
  J  class skills add to ONE class: The Oculus sor 3 -> +3 on a Sorceress, 0 on a Paladin with the reason kept.
  K  defense: Crown of Ages = floor(166 x 150 / 100) + 100..150 = 349..399 (a unique carrying +%ED spawns at the base's
       max + 1 — the in-game 349-399); Stormshield at level 90 = 133..148 + floor(30 x 90 / 8) = 470..485.
  L  per level: Enigma's MF at level 88 = floor(8 x 88 / 8) = 88.
  M  a typed roll outside its range (Crown res-all 40) is REFUSED: the range stands and a problem says why.

AND THE BLOCK'S OWN FRESHNESS (python, no browser): tv/char_props.py --check on a FAKE install — fresh 0, a moved
table 1, a hand-edited block 1, no install 77 (UNKNOWN, never green), a corrupt string table 77; the doctor row
"character sheet data" OK / MISSING / UNKNOWN and registered; and a CROSS-GENERATOR case: every unique and set item in
the block names the same base code tv/item_tables.json (a different generator over the same install) names.
The real install's --check runs where the install is, and says UNMEASURED elsewhere.
RED_PROOF below.
"""
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import char_props as CP  # noqa: E402

NODE = shutil.which("node")
OPEN = '<script id="v174-char-engine-js">'


def _src():
    with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as f:
        return f.read()


def _engine(src):
    """the whole shipped engine element, from its own opening tag to its own closing tag"""
    assert src.count(OPEN) == 1, "the engine's script element is not there exactly once (%d)" % src.count(OPEN)
    i = src.index(OPEN) + len(OPEN)
    return src[i:src.index("</script>", i)]


def _slot(name, **kw):
    d = {"name": name}
    d.update(kw)
    return d


CROWN, VIPER, MARA, OCULUS = "Crown of Ages", "Skin of the Vipermagi", "Mara's Kaleidoscope", "The Oculus"

#: name -> (build, opts). Run once, in one node process, over the SHIPPED engine.
CASES = {
    "A": ({"cls": "Sorceress", "level": 88, "sets": [{"name": "Set 1", "slots": {
        "head": _slot(CROWN, rolls={"res-all": 30}), "tors": _slot(VIPER), "neck": _slot(MARA), "rarm": _slot(OCULUS)}}]},
        {"difficulty": "Hell", "quests": True}),
    "B": ({"cls": "Sorceress", "level": 88, "sets": [{"slots": {
        "head": _slot(CROWN), "tors": _slot(VIPER), "neck": _slot(MARA), "rarm": _slot(OCULUS)}}]},
        {"difficulty": "Hell", "quests": True}),
    "C": ({"cls": "Sorceress", "level": 88, "sets": [{"slots": {
        "head": _slot(CROWN, rolls={"res-all": 30}), "tors": _slot(VIPER, rolls={"res-all": 35}), "neck": _slot(MARA),
        "rarm": _slot(OCULUS)}}]}, {"difficulty": "Hell", "quests": True}),
    "D-normal": ({"cls": "Sorceress", "level": 88, "sets": [{"slots": {"head": _slot(CROWN)}}]},
                 {"difficulty": "Normal", "quests": False}),
    "D-nightmare": ({"cls": "Sorceress", "level": 88, "sets": [{"slots": {"head": _slot(CROWN)}}]},
                    {"difficulty": "Nightmare", "quests": False}),
    "D-hell": ({"cls": "Sorceress", "level": 88, "sets": [{"slots": {"head": _slot(CROWN)}}]},
               {"difficulty": "Hell", "quests": False}),
    "E-hell-on": ({"cls": "Sorceress", "level": 88, "sets": [{"slots": {"head": _slot(CROWN)}}]},
                  {"difficulty": "Hell", "quests": True}),
    "F": ({"cls": "Paladin", "level": 90, "sets": [{"slots": {
        "larm": _slot("Stormshield"), "belt": _slot("Verdungo's Hearty Cord")}}]}, {"difficulty": "Hell", "quests": True}),
    "F-over": ({"cls": "Paladin", "level": 90, "sets": [{"slots": {
        "larm": _slot("Stormshield"), "belt": _slot("Verdungo's Hearty Cord"), "head": _slot(CROWN)}}]},
        {"difficulty": "Hell", "quests": True}),
    "G": ({"cls": "Sorceress", "level": 88, "sets": [{"slots": {
        "head": _slot(CROWN, rolls={"res-all": 30}), "tors": _slot(VIPER, rolls={"res-all": 35}),
        "neck": _slot(MARA, rolls={"res-all": 30}), "rarm": _slot(OCULUS)}}]}, {"difficulty": "Normal", "quests": True}),
    "H": ({"cls": "Sorceress", "level": 88, "sets": [{"slots": {
        "head": _slot(CROWN, rolls={"res-all": 30}), "tors": _slot("Guardian Angel"),
        "neck": _slot(MARA, rolls={"res-all": 30}), "rarm": _slot(OCULUS),
        "inv0": _slot("Annihilus", rolls={"res-all": 20})}}]}, {"difficulty": "Normal", "quests": True}),
    "I-unmapped": ({"cls": "Warlock", "level": 88, "sets": [{"slots": {"feet": _slot("Wraithstep")}}]},
                   {"difficulty": "Hell", "quests": True}),
    "I-unknown": ({"cls": "Sorceress", "level": 88, "sets": [{"slots": {
        "head": _slot(CROWN), "rrin": _slot("Dread Loop")}}]}, {"difficulty": "Hell", "quests": True}),
    "J-sorc": ({"cls": "Sorceress", "level": 88, "sets": [{"slots": {"rarm": _slot(OCULUS)}}]},
               {"difficulty": "Hell", "quests": True}),
    "J-pala": ({"cls": "Paladin", "level": 88, "sets": [{"slots": {"rarm": _slot(OCULUS)}}]},
               {"difficulty": "Hell", "quests": True}),
    "K-crown": ({"cls": "Sorceress", "level": 88, "sets": [{"slots": {"head": _slot(CROWN)}}]},
                {"difficulty": "Hell", "quests": True}),
    "K-storm": ({"cls": "Paladin", "level": 90, "sets": [{"slots": {"larm": _slot("Stormshield")}}]},
                {"difficulty": "Hell", "quests": True}),
    "L": ({"cls": "Warlock", "level": 88, "sets": [{"slots": {"tors": _slot("Enigma", base="Mage Plate")}}]},
          {"difficulty": "Hell", "quests": True}),
    "M": ({"cls": "Sorceress", "level": 88, "sets": [{"slots": {"head": _slot(CROWN, rolls={"res-all": 40})}}]},
          {"difficulty": "Hell", "quests": True}),
}

DRIVER = r"""
var window = {};
%(engine)s
var E = window.D2R_CHAR_ENGINE, C = %(cases)s, out = {};
Object.keys(C).forEach(function(k){ out[k] = E.sheet(C[k][0], C[k][1]); });
out.__lines = E.lines({ name: 'Crown of Ages' });
out.__api = Object.keys(E).sort();
process.stdout.write(JSON.stringify(out));
"""

_RUN = {}


def _run():
    if "out" not in _RUN:
        js = DRIVER % {"engine": _engine(_src()), "cases": json.dumps(CASES)}
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=90)
        if r.returncode != 0:
            raise AssertionError("the shipped stats engine would not run - UNKNOWN, not passing: %s" % r.stderr[:900])
        _RUN["out"] = json.loads(r.stdout)
    return _RUN["out"]


def _row(case, key):
    rows = [r for r in _run()[case]["rows"] if r["key"] == key]
    assert len(rows) == 1, "case %s has %d rows keyed %r" % (case, len(rows), key)
    return rows[0]


def _val(case, key):
    v = _row(case, key)["value"]
    return None if v is None else (v["min"], v["max"])


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheSheetSumsTheGameData(unittest.TestCase):

    def test_premise_the_shipped_block_carries_the_lines_the_answers_were_worked_from(self):
        d = CP.embedded(_src())
        self.assertIsNotNone(d, "bible.html carries no parseable CHAR_PROPS block")
        self.assertEqual(d["diff"], [["Normal", 0], ["Nightmare", -40], ["Hell", -100]])
        self.assertEqual(d["props"]["res-all"], [[1, "fireresist", None], [3, "lightresist", None],
                                                 [3, "coldresist", None], [3, "poisonresist", None]])
        u = dict((x[0], x) for x in d["uniques"] if x[5] == 1)
        want = {CROWN: ["res-all", "", 20, 30], VIPER: ["res-all", "", 20, 35], MARA: ["res-all", "", 20, 30],
                OCULUS: ["res-all", "", 20, 20], "Stormshield": ["red-dmg%", "", 35, 35],
                "Verdungo's Hearty Cord": ["red-dmg%", "", 10, 15], "Guardian Angel": ["res-all-max", "", 15, 15]}
        for name, line in want.items():
            self.assertIn(line, u[name][6], "the premise moved: %s no longer carries %s" % (name, line))
        self.assertIn(["ac/lvl", "30", None, None], u["Stormshield"][6])
        self.assertEqual(d["bases"]["urn"][2:4], [111, 165])
        self.assertEqual(d["bases"]["uit"][2:4], [133, 148])
        self.assertIn("skilltab-war", [l[0] for l in u["Wraithstep"][6]])
        self.assertNotIn("skilltab-war", d["props"], "the premise moved: properties.txt now HAS skilltab-war")
        self.assertEqual(d["perlvl"]["item_find_magic_perlevel"], ["item_magicbonus", 3, 2])

    def test_the_engine_is_exposed_whole(self):
        self.assertEqual(_run()["__api"], ["classes", "dataHash", "difficulties", "lines", "resolve", "sheet"])

    def test_A_hell_with_quests_is_the_brief_sum_with_the_crown_typed(self):
        for k in ("res-fire", "res-cold", "res-ltng", "res-pois"):
            r = _row("A", k)
            self.assertEqual((r["value"]["min"], r["value"]["max"]), (20, 45), "%s: %s" % (k, r["why"]))
            self.assertEqual(r["source"], "RANGE")
            self.assertEqual(r["cap"], {"min": 75, "max": 75})
        why = _row("A", "res-fire")["why"]
        for part in ("Hell", "-100", "Anya", "+30", "Crown of Ages +30 typed", "Skin of the Vipermagi +20..35 untouched roll"):
            self.assertIn(part, why, "the row does not say its source: %s" % why)

    def test_B_an_untouched_roll_is_its_whole_range_never_averaged_or_maxed(self):
        self.assertEqual(_val("B", "res-fire"), (10, 45))

    def test_C_a_typed_roll_narrows_the_range(self):
        self.assertEqual(_val("C", "res-fire"), (35, 45))

    def test_D_the_difficulty_penalty_is_the_tables(self):
        self.assertEqual(_val("D-normal", "res-fire"), (20, 30))
        self.assertEqual(_val("D-nightmare", "res-fire"), (-20, -10))
        self.assertEqual(_val("D-hell", "res-fire"), (-80, -70))

    def test_E_quests_off_is_thirty_lower_at_hell(self):
        on, off = _val("E-hell-on", "res-fire"), _val("D-hell", "res-fire")
        self.assertEqual(on, (-50, -40))
        self.assertEqual((on[0] - off[0], on[1] - off[1]), (30, 30))
        self.assertNotIn("Anya", _row("D-hell", "res-fire")["why"])

    def test_F_pdr_sums_and_caps_at_fifty_with_the_raw_beside_it(self):
        r = _row("F", "pdr")
        self.assertEqual((r["value"]["min"], r["value"]["max"]), (45, 50))
        self.assertEqual(r["cap"], {"min": 50, "max": 50})
        o = _row("F-over", "pdr")
        self.assertEqual((o["value"]["min"], o["value"]["max"]), (50, 50), o["why"])
        self.assertEqual((o["raw"]["min"], o["raw"]["max"]), (55, 65))
        self.assertIn("raw +55..65", o["why"])

    def test_G_the_resistance_cap_binds_at_75(self):
        r = _row("G", "res-fire")
        self.assertEqual((r["value"]["min"], r["value"]["max"]), (75, 75))
        self.assertEqual((r["raw"]["min"], r["raw"]["max"]), (125, 125))
        self.assertEqual(r["source"], "EXACT")

    def test_H_max_resistance_lifts_the_cap(self):
        r = _row("H", "res-fire")
        self.assertEqual(r["cap"], {"min": 90, "max": 90})
        self.assertEqual((r["value"]["min"], r["value"]["max"]), (90, 90))
        self.assertEqual((r["raw"]["min"], r["raw"]["max"]), (110, 110))

    def test_I_an_unmapped_prop_is_UNKNOWN_naming_the_item_and_the_rest_still_sums(self):
        un = [r for r in _run()["I-unmapped"]["rows"] if r["group"] == "unmapped"]
        self.assertEqual(len(un), 1, [r["key"] for r in un])
        self.assertIsNone(un[0]["value"])
        self.assertEqual(un[0]["source"], "UNKNOWN")
        self.assertIn("Wraithstep", un[0]["why"])
        self.assertIn("skilltab-war", un[0]["why"])
        self.assertEqual(_val("I-unmapped", "frw"), (30, 30))

    def test_I_an_item_the_data_does_not_name_makes_rows_UNKNOWN_never_zero(self):
        for k in ("res-fire", "fcr", "mf"):
            r = _row("I-unknown", k)
            self.assertIsNone(r["value"], "%s read %s beside an item nobody can name" % (k, r["value"]))
            self.assertEqual(r["source"], "UNKNOWN")
            self.assertIn("Dread Loop", r["why"])

    def test_J_class_skills_add_to_one_class(self):
        self.assertEqual(_val("J-sorc", "class-skills"), (3, 3))
        self.assertEqual(_val("J-pala", "class-skills"), (0, 0))
        na = " ".join(x["why"] for x in _run()["J-pala"]["notApplied"])
        self.assertIn("Sorceress", na, "a class skill that does not apply was dropped without a word")

    def test_K_defense_from_the_base_table(self):
        self.assertEqual(_val("K-crown", "defense"), (349, 399))
        self.assertEqual(_val("K-storm", "defense"), (470, 485))

    def test_L_a_per_level_stat_scales_by_the_tables_shift(self):
        self.assertEqual(_val("L", "mf"), (88, 88))

    def test_M_a_typed_roll_outside_its_range_is_refused(self):
        self.assertEqual(_val("M", "res-fire"), (-50, -40))
        self.assertTrue(any("refused" in p and "40" in p for p in _run()["M"]["problems"]), _run()["M"]["problems"])

    def test_the_edit_tab_reads_its_roll_keys_from_the_engine(self):
        ls = dict((l["code"], l) for l in _run()["__lines"]["lines"])
        self.assertEqual(ls["res-all"]["k"], "res-all")
        self.assertTrue(ls["res-all"]["rolled"])
        self.assertFalse(ls["balance2"]["rolled"])
        self.assertEqual((ls["res-all"]["min"], ls["res-all"]["max"]), (20, 30))


# ── the block's freshness: a FAKE install, so these run on every machine ──────────────────────────────────────────
def _tsv(*rows):
    return ("\n".join("\t".join(str(c) for c in r) for r in rows) + "\n").encode("utf-8")


def _strs(pairs):
    return json.dumps([{"Key": k, "enUS": v} for k, v in pairs]).encode("utf-8")


def _fake(**over):
    t = {
        "uniqueitems": _tsv(["index", "*ID", "code", "lvl req", "spawnable", "prop1", "par1", "min1", "max1"],
                            ["Crown of Ages", 1, "urn", 82, 1, "res-all", "", 20, 30]),
        "setitems": _tsv(["index", "*ID", "set", "item", "lvl req", "add func", "prop1", "par1", "min1", "max1"],
                         ["Tal Crest", 1, "TalSet", "urn", 66, 0, "res-all", "", 15, 15]),
        "sets": _tsv(["index", "name", "PCode2a", "PParam2a", "PMin2a", "PMax2a", "FCode1", "FParam1", "FMin1", "FMax1"],
                     ["TalSet", "TalSet", "mag%", "", 65, 65, "res-all", "", 50, 50]),
        "runes": _tsv(["Name", "*Rune Name", "complete", "Rune1", "T1Code1", "T1Param1", "T1Min1", "T1Max1"],
                      ["Runeword1", "Stealth", 1, "r01", "cast3", "", 25, 25]),
        "gems": _tsv(["name", "code", "weaponMod1Code", "weaponMod1Param", "weaponMod1Min", "weaponMod1Max",
                      "helmMod1Code", "helmMod1Param", "helmMod1Min", "helmMod1Max",
                      "shieldMod1Code", "shieldMod1Param", "shieldMod1Min", "shieldMod1Max"],
                     ["El Rune", "r01", "att", "", 50, 50, "ac", "", 15, 15, "ac", "", 15, 15]),
        "properties": _tsv(["code", "func1", "stat1", "set1", "val1", "func2", "stat2", "set2", "val2"],
                           ["res-all", 1, "fireresist", "", "", 3, "lightresist", "", ""],
                           ["ama", 21, "item_addclassskills", "", 0, "", "", "", ""],
                           ["sor", 21, "item_addclassskills", "", 1, "", "", "", ""],
                           ["cast3", 8, "item_fastercastrate", "", "", "", "", "", ""],
                           ["mag%", 1, "item_magicbonus", "", "", "", "", "", ""],
                           ["att", 1, "tohit", "", "", "", "", "", ""],
                           ["ac", 1, "armorclass", "", "", "", "", "", ""]),
        "itemstatcost": _tsv(["Stat", "*ID", "op", "op param", "op base", "op stat1", "descstrpos", "dgrp", "dgrpstrpos"],
                             ["fireresist", 39, "", "", "", "", "ModFire", 1, "ModAll"],
                             ["item_find_magic_perlevel", 240, 2, 3, "level", "item_magicbonus", "", "", ""]),
        "difficultylevels": _tsv(["Name", "ResistPenalty"], ["Normal", 0], ["Nightmare", -40], ["Hell", -100]),
        "armor": _tsv(["name", "code", "namestr", "minac", "maxac", "gemsockets", "levelreq", "type"],
                      ["Corona", "urn", "urn", 111, 165, 3, 66, "helm"]),
        "weapons": _tsv(["name", "code", "namestr", "minac", "maxac", "gemsockets", "levelreq", "type"],
                        ["Crystal Sword", "crs", "crs", 0, 0, 6, 0, "swor"]),
        "misc": _tsv(["name", "code", "namestr", "minac", "maxac", "gemsockets", "levelreq", "type"],
                     ["El Rune", "r01", "r01", 0, 0, 0, 11, "rune"], ["Elixir", "elx", "elx", 0, 0, 0, 0, "elix"]),
        "itemtypes": _tsv(["ItemType", "Code", "Equiv1", "Equiv2"], ["Helm", "helm", "armo", ""], ["Any Armor", "armo", "", ""],
                          ["Weapon", "weap", "", ""], ["Sword", "swor", "weap", ""], ["Rune", "rune", "misc", ""],
                          ["Elixir", "elix", "misc", ""], ["Misc", "misc", "", ""], ["Charm", "char", "misc", ""]),
        "skills": _tsv(["skill", "*Id", "charclass", "skilldesc"], ["Teleport", 54, "sor", "teleport"]),
        "skilldesc": _tsv(["skilldesc", "str name"], ["teleport", "skillname54"]),
        "charstats": _tsv(["class", "StrAllSkills", "StrClassOnly", "StrSkillTab1", "StrSkillTab2", "StrSkillTab3"],
                          ["Amazon", "AmaAll", "AmaOnly", "AmaT1", "AmaT2", "AmaT3"],
                          ["Expansion", "", "", "", "", ""],
                          ["Sorceress", "SorAll", "SorOnly", "SorT1", "SorT2", "SorT3"]),
        "itemnames": _strs([("urn", "Corona"), ("crs", "Crystal Sword"), ("r01", "El Rune"), ("Crown of Ages", "Crown of Ages")]),
        "itemrunes": _strs([("Runeword1", "Stealth")]),
        "itemmodifiers": _strs([("ModFire", "Fire Resist %+d%%"), ("ModAll", "All Resistances %+d"),
                                ("AmaAll", "%+d to Amazon Skill Levels"), ("SorAll", "%+d to Sorceress Skill Levels")]),
        "skillstrings": _strs([("skillname54", "Teleport")]),
    }
    t.update(over)
    by_path = dict((path, t[label]) for label, path in CP.SOURCES)
    return lambda p: by_path.get(p)


class TheBlockKnowsWhenItIsStale(unittest.TestCase):

    def _page(self, pull):
        data, why = CP.build(pull)
        self.assertIsNone(why, why)
        return "<p>before</p>\n  " + CP.render(data) + "\n<p>after</p>", data

    def test_premise_the_fake_install_builds_a_real_block(self):
        src, data = self._page(_fake())
        self.assertEqual(CP.embedded(src), data, "the block does not read back as what was written")
        self.assertEqual(data["diff"], [["Normal", 0], ["Nightmare", -40], ["Hell", -100]])
        self.assertEqual([c[1] for c in data["classes"]], ["Amazon", "Sorceress"])
        self.assertNotIn("elx", data["bases"], "a misc base nothing can hold was written into the page")

    def test_fresh_is_0(self):
        src, _ = self._page(_fake())
        code, say = CP.check(src, _fake())
        self.assertEqual(code, 0, say)

    def test_a_moved_table_is_1_stale(self):
        src, _ = self._page(_fake())
        moved = _fake(difficultylevels=_tsv(["Name", "ResistPenalty"], ["Normal", 0], ["Nightmare", -40], ["Hell", -95]))
        code, say = CP.check(src, moved)
        self.assertEqual(code, 1, say)
        self.assertIn("install has changed", say)

    def test_a_hand_edited_block_is_1_stale(self):
        src, data = self._page(_fake())
        edited = copy.deepcopy(data)
        edited["diff"][2][1] = -90
        src2 = src.replace(CP.render(data), CP.render(edited))
        code, say = CP.check(src2, _fake())
        self.assertEqual(code, 1, say)
        self.assertIn("diff", say)

    def test_no_install_is_77_unknown_never_green(self):
        src, _ = self._page(_fake())
        code, say = CP.check(src, lambda p: None)
        self.assertEqual(code, CP.SKIP, say)
        self.assertIn("UNKNOWN", say)

    def test_a_corrupt_string_table_is_77_not_an_empty_one(self):
        src, _ = self._page(_fake())
        code, say = CP.check(src, _fake(itemmodifiers=b"{not json"))
        self.assertEqual(code, CP.SKIP, say)
        self.assertIn("would not parse", say)

    def test_a_page_without_the_block_is_1(self):
        code, say = CP.check("<p>no block here</p>", _fake())
        self.assertEqual(code, 1, say)

    def test_the_shipped_block_matches_his_install_where_there_is_one(self):
        code, say = CP.check()
        if code == CP.SKIP:
            self.skipTest("UNMEASURED here, not passed: " + say)
        self.assertEqual(code, 0, say)

    def test_two_generators_name_the_same_bases(self):
        """the block against tv/item_tables.json — a different generator over the same install tables"""
        import item_tables as IT
        t = IT.load()
        if t is None:
            self.skipTest("tv/item_tables.json is absent - UNMEASURED, not passed")
        d = CP.embedded(_src())
        bad = []
        for u in d["uniques"]:
            row = t["uniques"].get(str(u[2]))
            if not row or row["code"] != u[3] or row["name"] != u[0]:
                bad.append(("unique", u[2], u[0], u[3], row))
        for s in d["sets"]:
            row = t["setItems"].get(str(s[2]))
            if not row or row["code"] != s[3] or row["name"] != s[0]:
                bad.append(("set", s[2], s[0], s[3], row))
        self.assertFalse(bad, "%d item(s) where the two generators disagree: %s" % (len(bad), bad[:4]))


class TheDoctorWatchesTheBlock(unittest.TestCase):

    def _run(self, answer):
        import console_doctor as D
        real = CP.check
        CP.check = lambda *a, **k: answer
        try:
            return D._check_the_character_sheet_data_matches_the_install()
        finally:
            CP.check = real

    def test_fresh_is_ok(self):
        import console_doctor as D
        self.assertEqual(self._run((0, "matches the install"))[0], D.OK)

    def test_stale_is_missing(self):
        import console_doctor as D
        st, why = self._run((1, "the install has changed since the CHAR_PROPS block was generated"))
        self.assertEqual(st, D.MISSING, "a patched install still reads as a healthy character sheet")
        self.assertIn("last patch", why)

    def test_no_install_is_unknown_never_ok(self):
        import console_doctor as D
        self.assertEqual(self._run((CP.SKIP, "cannot re-derive here"))[0], D.UNKNOWN)

    def test_the_row_is_registered_periodic_declared_and_explained(self):
        import console_doctor as D
        import corroborate as C
        self.assertIn("character sheet data", dict(D.CHECKS))
        self.assertIn("character sheet data", D.PERIODIC)
        self.assertIn("character sheet data", D.WATCHES)
        self.assertIn("character sheet data", D.MINE)
        self.assertIn("character sheet data", C.NO_JOINT_YET)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#174 v-B2 - the Hell penalty dropped: a bare Hell sheet reads the items alone, 100 points too kind",
        "file": "bible.html",
        "find": "else pen.push({ src: dif.name, via: 'difficultylevels.txt ResistPenalty', how: 'rule', lo: dif.penalty, hi: dif.penalty });",
        "replace": "else pen.push({ src: dif.name, via: 'difficultylevels.txt ResistPenalty', how: 'rule', lo: 0, hi: 0 });",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - Anya's scrolls counted once whatever the difficulty (maxroll's -70 is THREE scrolls)",
        "file": "bible.html",
        "find": "how: 'rule', lo: 10 * (dif.i + 1), hi: 10 * (dif.i + 1) });",
        "replace": "how: 'rule', lo: 10, hi: 10 });",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - a typed roll ignored: his real roll never narrows the range",
        "file": "bible.html",
        "find": "else { lo = hi = tv; how = 'typed'; }",
        "replace": "else { how = 'typed'; }",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - the 75 resistance cap never binds: 125% of fire resistance read as 125",
        "file": "bible.html",
        "find": "r.cap = { min: Math.min(95, 75 + m.value.min), max: Math.min(95, 75 + m.value.max) };",
        "replace": "r.cap = { min: 999, max: 999 };",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - PDR uncapped: three damage-reduction items read 55-65% where the game allows 50",
        "file": "bible.html",
        "find": "if (R[0] === 'pdr'){ ex.cap = { min: 50, max: 50 };",
        "replace": "if (R[0] === 'pdr'){ ex.cap = { min: 999, max: 999 };",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - a property code the game data does not have is DROPPED silently instead of said UNKNOWN",
        "file": "bible.html",
        "find": "      if (!fs){\n        unmap(ctx, code, src + (ctx.via ? ' (' + ctx.via + ')' : '') + ' carries \"' + code + '\"'",
        "replace": "      if (!fs){ return;\n        unmap(ctx, code, src + (ctx.via ? ' (' + ctx.via + ')' : '') + ' carries \"' + code + '\"'",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - an item nobody can name leaves every total reading a confident number (0 beside UNKNOWN)",
        "file": "bible.html",
        "find": "if (!ex.itemOnly && unkAll.length) bad = bad.concat(unkAll);",
        "replace": "if (false) bad = bad.concat(unkAll);",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - +3 Sorceress skills summed on a Paladin (the v-B review's class-skill defect, again)",
        "file": "bible.html",
        "find": "if (val !== cls.id){ res.notApplied.push({ item: src, code: code, why: _ceFmt((D.classes[val] || [])[2]",
        "replace": "if (false){ res.notApplied.push({ item: src, code: code, why: _ceFmt((D.classes[val] || [])[2]",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - a unique carrying +%ED read at the base's max, not max + 1 (Crown of Ages 347-397, the game 349-399)",
        "file": "bible.html",
        "find": "if ((it.kind === 'unique' || it.kind === 'set') && it.ownEd){ bmin = bmax = b[3] + 1;",
        "replace": "if ((it.kind === 'unique' || it.kind === 'set') && it.ownEd){ bmin = bmax = b[3];",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - a per-level stat without the table's shift: Enigma's MF read 704 at level 88",
        "file": "bible.html",
        "find": "a = Math.floor(a * lvl / sh); b = Math.floor(b * lvl / sh);",
        "replace": "a = Math.floor(a * lvl); b = Math.floor(b * lvl);",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - a stale CHAR_PROPS block reads fresh: the sheet sums last patch's ranges and says OK",
        "file": "char_props.py",
        "find": "    if fresh == have:\n",
        "replace": "    if True:\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - no install reads as fresh: a CI runner's 'I could not look' becomes 'all is well'",
        "file": "char_props.py",
        "find": "        return SKIP, \"cannot re-derive here (%s), so whether the block matches the install is UNKNOWN\" % why\n",
        "replace": "        return 0, \"cannot re-derive here (%s), so whether the block matches the install is UNKNOWN\" % why\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - the doctor row reads a stale block as OK",
        "file": "console_doctor.py",
        "find": "        return MISSING, say + \" - every character sheet sums last patch's ranges\"\n",
        "replace": "        return OK, say\n",
        "matches": 1,
    },
]
