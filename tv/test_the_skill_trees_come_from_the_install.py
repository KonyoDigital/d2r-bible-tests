# -*- coding: utf-8 -*-
"""#174 — THE SKILL TREES COME FROM HIS INSTALL, AND A TREE THE TABLES DO NOT STATE IS UNKNOWN.

The mule/character window is being rebuilt to match the maxroll d2planner: three skill trees per
class, each skill an icon at a fixed row and column with arrows from its prerequisites. The repo
had no class, skill or tab data, and the easy way to get it — type the trees in from memory, or
from a fan site — is exactly how a planner ends up with a skill one row off, an arrow from the
wrong skill, or "Elemental" over the Druid's summons. `tv/skill_tables.py` pulls it from the CASC
of the install on this machine into a GENERATED, COMMITTED `tv/skill_tables.json`.

THE TRAPS THIS LAW PINS, each one a way the tree looks right and is not:
  · A KEY IS NOT A NAME. skills.txt calls Werewolf `Wearwolf` and Lycanthropy `Shape Shifting`;
    27 of 240 tree skills differ. A skill with no display string is unnamed, never its key.
  · A SKILLPAGE IS NOT A TAB POSITION. The Druid's page 3 is Elemental and sits LEFTMOST; the
    guess "tab i = page i+1" puts Tornado under Summoning. And the string keys cannot be read for
    the order either: the Warlock's leftmost tab is `SkillCategoryWa3`. The order is derived from
    the item-modifier strings charstats names per page, and a tie or a disagreement is UNKNOWN.
  · A JOIN BY ROW ORDER IS NOT A JOIN BY KEY. skilldesc is joined on the skills.txt `skilldesc`
    column; the fixture below stores skilldesc in a different order so a row-order join misplaces
    every skill, and SkillRow must agree with reqlevel (row 1..6 = level 1, 6, 12, 18, 24, 30).
  · A SKILLPAGE DOES NOT MAKE A TREE SKILL. Monster skills carry one too (DiabWall).
  · reqskill2 and reqskill3 are prerequisites too (Summon Dire Wolf needs Oak Sage AND Spirit Wolf).

  · DRIVEN: a small fake install (two classes, 16 skills, the layout's comments and trailing
    commas included) assembles into trees that satisfy every law — no install needed, so CI runs it.
  · MEASURED: the committed json — every class exactly 3 tabs, every skill inside the 6 x 3 grid
    the install's own layout declares, every prerequisite in the same class, the Druid's tabs
    Elemental / Shape Shifting / Summoning with Tornado, Hurricane, Werewolf and Summon Grizzly
    where the game puts them.
  · MEASURED when the install is present: the json's sourceHash, and its whole content, match a
    fresh build. UNMEASURED otherwise (CI has no install) — a skip, never a pass.
RED_PROOF below.
"""
import json
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

import skill_tables as ST  # noqa: E402

#: The level a skill in row r needs. Two tables state it (skilldesc SkillRow, skills.txt reqlevel);
#: they agree on all 240 tree skills of his install, so a disagreement is a broken join.
ROW_LEVEL = (1, 6, 12, 18, 24, 30)
CLASSIC = ("ama", "sor", "nec", "pal", "bar", "dru", "ass")


def _laws(tc, t, where):
    """Every law a skill tree must satisfy, whoever built it."""
    g = t.get("grid") or {}
    tc.assertEqual((g.get("rows"), g.get("cols")), (6, 3),
                   "%s: the install's layout no longer declares a 6 x 3 tree grid: %r" % (where, g))
    tc.assertTrue(t.get("classes"), "%s: no classes at all" % where)
    for code, c in sorted(t["classes"].items()):
        tabs = c.get("tabs") or []
        tc.assertEqual(len(tabs), 3, "%s: %s has %d tabs" % (where, code, len(tabs)))
        tc.assertEqual(sorted(x["page"] for x in tabs), [1, 2, 3], "%s: %s pages" % (where, code))
        tc.assertEqual([x["index"] for x in tabs], [0, 1, 2],
                       "%s: %s tabs are not in panel order 0,1,2: %r" % (where, code, [x["index"] for x in tabs]))
        ids = {s["id"]: (x["page"], s) for x in tabs for s in x["skills"]}
        tc.assertNotIn(None, ids, "%s: %s has a skill with no id" % (where, code))
        for x in tabs:
            cells = set()
            for s in x["skills"]:
                who = "%s: %s %s" % (where, code, s["key"])
                tc.assertTrue(1 <= (s["row"] or 0) <= g["rows"], "%s row %r outside 1..%d" % (who, s["row"], g["rows"]))
                tc.assertTrue(1 <= (s["col"] or 0) <= g["cols"], "%s col %r outside 1..%d" % (who, s["col"], g["cols"]))
                tc.assertNotIn((s["row"], s["col"]), cells, "%s shares a cell" % who)
                cells.add((s["row"], s["col"]))
                tc.assertEqual(s["reqlevel"], ROW_LEVEL[s["row"] - 1],
                               "%s: row %d says level %d, reqlevel says %r — the skilldesc join is wrong"
                               % (who, s["row"], ROW_LEVEL[s["row"] - 1], s["reqlevel"]))
                tc.assertEqual(len(s["prereqs"]), len(s["prereqKeys"]), "%s: a prerequisite was dropped" % who)
                for q in s["prereqs"]:
                    tc.assertIn(q, ids, "%s: prerequisite %r is not a %s skill" % (who, q, code))
                    qpage, qs = ids[q]
                    tc.assertEqual(qpage, x["page"], "%s: prerequisite %s is in another tab" % (who, qs["key"]))
                    tc.assertLessEqual(qs["row"], s["row"], "%s: prerequisite %s sits BELOW it" % (who, qs["key"]))


def _tab(t, code, name):
    for x in t["classes"][code]["tabs"]:
        if x["name"] == name:
            return x
    raise AssertionError("%s has no tab named %r: %r" % (code, name, [x["name"] for x in t["classes"][code]["tabs"]]))


def _skill(tab, name):
    for s in tab["skills"]:
        if s["name"] == name:
            return s
    raise AssertionError("tab %r has no skill named %r" % (tab["name"], name))


# ── the fake install ────────────────────────────────────────────────────────────────────────
# Written here, independently of the builder: its own TSV and JSON, real column names, and the
# measured Druid/Warlock values. skilldesc is stored in REVERSE order on purpose.

def _tsv(header, rows):
    return ("\t".join(header) + "\r\n" + "".join("\t".join(str(c) for c in r) + "\r\n" for r in rows)).encode("utf-8")


def _strs(pairs):
    return json.dumps([{"id": i + 1, "Key": k, "enUS": v} for i, (k, v) in enumerate(pairs)]).encode("utf-8-sig")


#: (skill key, charclass, skilldesc, reqlevel, reqskills, (page, row, col, icon), str name)
SKILLS = [
    ("Attack",             "",    "attack",             1,  (),                                  (0, 0, 0, 0),  "SkAttack"),
    ("DiabWall",           "",    "diabwall",           1,  (),                                  (3, 1, 1, 0),  "SkDiabWall"),
    ("Raven",              "dru", "raven",              1,  (),                                  (1, 1, 2, 0),  "SkRaven"),
    ("Wearwolf",           "dru", "wearwolf",           1,  (),                                  (2, 1, 1, 20), "SkWearwolf"),
    ("Shape Shifting",     "dru", "shape shifting",     1,  ("Wearwolf",),                       (2, 1, 2, 52), "SkShapeShifting"),
    ("Firestorm",          "dru", "firestorm",          1,  (),                                  (3, 1, 1, 32), "SkFirestormHasNoString"),
    ("Oak Sage",           "dru", "oak sage",           6,  (),                                  (1, 2, 1, 16), "SkOakSage"),
    ("Summon Spirit Wolf", "dru", "summon spirit wolf", 6,  ("Raven",),                          (1, 2, 2, 6),  "SkSpiritWolf"),
    ("Twister",            "dru", "twister",            18, (),                                  (3, 4, 2, 42), "SkTwister"),
    ("Summon Fenris",      "dru", "summon fenris",      18, ("Oak Sage", "Summon Spirit Wolf"),  (1, 4, 2, 12), "SkFenris"),
    ("Tornado",            "dru", "tornado",            24, ("Twister",),                        (3, 5, 2, 46), "SkTornado"),
    ("Summon Grizzly",     "dru", "summon grizzly",     30, ("Summon Fenris",),                  (1, 6, 2, 18), "SkGrizzly"),
    ("Hurricane",          "dru", "hurricane",          30, ("Tornado",),                        (3, 6, 2, 48), "SkHurricane"),
    ("Summon Goatman",     "war", "summon goatman",     1,  (),                                  (1, 1, 3, 2),  "SkGoatman"),
    ("Levitate",           "war", "levitate",           1,  (),                                  (2, 1, 1, 20), "SkLevitate"),
    ("Miasma Bolt",        "war", "miasma bolt",        1,  (),                                  (3, 1, 3, 46), "SkMiasmaBolt"),
]
NAMES = [("SkAttack", "Attack"), ("SkDiabWall", "Diablo's Wall"), ("SkRaven", "Raven"),
         ("SkWearwolf", "Werewolf"), ("SkShapeShifting", "Lycanthropy"), ("SkOakSage", "Oak Sage"),
         ("SkSpiritWolf", "Summon Spirit Wolf"), ("SkTwister", "Twister"), ("SkFenris", "Summon Dire Wolf"),
         ("SkTornado", "Tornado"), ("SkGrizzly", "Summon Grizzly"), ("SkHurricane", "Hurricane"),
         ("SkGoatman", "Summon Goatman"), ("SkLevitate", "Levitation Mastery"), ("SkMiasmaBolt", "Miasma Bolt"),
         ("SkillCategoryDr1", "Elemental"), ("SkillCategoryDr2", "Shape Shifting"), ("SkillCategoryDr3", "Summoning"),
         ("SkillCategoryWa1", "Demon"), ("SkillCategoryWa2", "Eldritch"), ("SkillCategoryWa3", "Chaos")]
LAYOUT = r'''{
    "type": "SkillsTreePanel", "name": "SkillsTreePanel",
    "fields": {
        "skillRow": [ 296, 478, 654, 834, 1014, 1190 ],
        "skillColumn": [ 253, 515, 775 ],
        // Amazon, Sorceress, Necromancer, Palladin, Barbarian, Druid, Assassin
        "skillButtonFile": [
             "Spells\\amazon\\AmSkillicon", "Spells\\Sorceress\\SoSkillicon", "Spells\\Necromancer\\NeSkillicon",
             "Spells\\paladin\\PaSkillicon", "Spells\\Barbarian\\BaSkillicon", "Spells\\Druid\\DrSkillicon",
             "Spells\\Assassin\\AsSkillicon", "Spells\\Warlock\\WaSkillicon",
        ],
        "textTab0": [ "@SkillCategoryAm1", "@SkillCategorySo1", "@SkillCategoryNe1", "@SkillCategoryPa1",
                      "@SkillCategoryBa1", "@SkillCategoryDr1", "@SkillCategoryAs1", "@SkillCategoryWa3", ],
        "textTab1": [ "@SkillCategoryAm2", "@SkillCategorySo2", "@SkillCategoryNe2", "@SkillCategoryPa2",
                      "@SkillCategoryBa2", "@SkillCategoryDr2", "@SkillCategoryAs2", "@SkillCategoryWa2", ],
        "textTab2": [ "@SkillCategoryAm3", "@SkillCategorySo3", "@SkillCategoryNe3", "@SkillCategoryPa3",
                      "@SkillCategoryBa3", "@SkillCategoryDr3", "@SkillCategoryAs3", "@SkillCategoryWa1", ],
    },
    "children": [ { "type": "TabWidget", "name": "Tab0", "fields": { "rect": "http://not-a-comment" } }, ],
}'''


def _blobs(**override):
    skills = _tsv(["skill", "*Id", "charclass", "skilldesc", "reqlevel", "maxlvl", "reqskill1", "reqskill2", "reqskill3"],
                  [[k, i, c, d, lv, 20] + list(req) + [""] * (3 - len(req))
                   for i, (k, c, d, lv, req, _pos, _sn) in enumerate(SKILLS)])
    desc = _tsv(["skilldesc", "SkillPage", "SkillRow", "SkillColumn", "ListRow", "IconCel", "str name"],
                [[d, p, r, c, 0, ic, sn] for (_k, _c, d, _lv, _req, (p, r, c, ic), sn) in reversed(SKILLS)])
    b = {
        "skills": skills,
        "skilldesc": desc,
        "playerclass": _tsv(["Player Class", "Code"],
                            [["Amazon", "ama"], ["Sorceress", "sor"], ["Necromancer", "nec"], ["Paladin", "pal"],
                             ["Barbarian", "bar"], ["Expansion", ""], ["Druid", "dru"], ["Assassin", "ass"],
                             ["Warlock", "war"]]),
        "charstats": _tsv(["class", "StrSkillTab1", "StrSkillTab2", "StrSkillTab3"],
                          [["Druid", "StrSklTabItem16", "StrSklTabItem17", "StrSklTabItem18"],
                           ["Expansion", "", "", ""],
                           ["Warlock", "StrSklTabItem24", "StrSklTabItem22", "StrSklTabItem23"]]),
        "treelayout": LAYOUT.encode("utf-8"),
        "skillnames": _strs(NAMES),
        "uinames": _strs([("Druid", "Druid"), ("Warlock", "Warlock")]),
        "itemmods": _strs([("StrSklTabItem16", "%+d to Summoning Skills"),
                           ("StrSklTabItem17", "%+d to Shape Shifting Skills"),
                           ("StrSklTabItem18", "%+d to Elemental Skills"),
                           ("StrSklTabItem22", "+%d to Eldritch Skills"),
                           ("StrSklTabItem23", "+%d to Chaos Skills"),
                           ("StrSklTabItem24", "+%d to Demon Skills")]),
    }
    b.update(override)
    return b


def _fixture_ids():
    return {k: i for i, (k, *_r) in enumerate(SKILLS)}


class TheFakeInstallAssembles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.t, cls.why = ST.assemble(_blobs())

    def test_it_assembles_and_every_law_holds(self):
        self.assertIsNotNone(self.t, self.why)
        self.assertEqual(self.t["classOrder"], ["dru", "war"])
        self.assertEqual(self.t["classesWithoutSkills"], ["ama", "sor", "nec", "pal", "bar", "ass"])
        _laws(self, self.t, "fixture")

    def test_the_druid_reads_elemental_shape_shifting_summoning(self):
        dru = self.t["classes"]["dru"]
        self.assertEqual((dru["id"], dru["name"]), (5, "Druid"))
        self.assertEqual([(x["name"], x["page"]) for x in dru["tabs"]],
                         [("Elemental", 3), ("Shape Shifting", 2), ("Summoning", 1)])
        el = _tab(self.t, "dru", "Elemental")
        tor, hur = _skill(el, "Tornado"), _skill(el, "Hurricane")
        self.assertEqual((tor["row"], tor["col"], hur["row"], hur["col"]), (5, 2, 6, 2))
        self.assertEqual(hur["prereqs"], [tor["id"]])
        self.assertEqual((hur["iconIndex"], hur["maxlvl"]), (48, 20))
        self.assertEqual(_skill(_tab(self.t, "dru", "Summoning"), "Summon Grizzly")["row"], 6)

    def test_a_key_is_not_a_display_name(self):
        ss = _tab(self.t, "dru", "Shape Shifting")
        self.assertEqual(_skill(ss, "Werewolf")["key"], "Wearwolf")
        self.assertEqual(_skill(ss, "Lycanthropy")["key"], "Shape Shifting")

    def test_a_skill_with_no_display_string_is_unnamed_never_its_key(self):
        fs = [s for s in _tab(self.t, "dru", "Elemental")["skills"] if s["key"] == "Firestorm"]
        self.assertEqual(len(fs), 1)
        self.assertIsNone(fs[0]["name"], "Firestorm has no display string here, and its KEY was printed as its name")
        self.assertEqual(self.t["counts"]["unnamedSkills"], 1)

    def test_all_three_prerequisite_columns_are_read(self):
        ids = _fixture_ids()
        wolf = _skill(_tab(self.t, "dru", "Summoning"), "Summon Dire Wolf")
        self.assertEqual(wolf["prereqs"], [ids["Oak Sage"], ids["Summon Spirit Wolf"]])
        self.assertEqual(wolf["prereqKeys"], ["Oak Sage", "Summon Spirit Wolf"])

    def test_the_warlocks_keys_run_backwards_and_its_tabs_do_not(self):
        war = self.t["classes"]["war"]
        self.assertEqual([(x["name"], x["nameKey"], x["page"]) for x in war["tabs"]],
                         [("Chaos", "SkillCategoryWa3", 3), ("Eldritch", "SkillCategoryWa2", 2),
                          ("Demon", "SkillCategoryWa1", 1)])
        self.assertEqual(_skill(_tab(self.t, "war", "Demon"), "Summon Goatman")["col"], 3)

    def test_a_monster_skill_with_a_page_is_in_no_tree(self):
        keys = {s["key"] for c in self.t["classes"].values() for x in c["tabs"] for s in x["skills"]}
        self.assertNotIn("DiabWall", keys)
        self.assertNotIn("Attack", keys)
        self.assertEqual(self.t["counts"]["skills"], 14)

    def test_ids_are_skills_txt_row_ids_not_class_positions(self):
        ids = _fixture_ids()
        el = _tab(self.t, "dru", "Elemental")
        self.assertEqual(_skill(el, "Hurricane")["id"], ids["Hurricane"])
        self.assertEqual(_skill(_tab(self.t, "war", "Chaos"), "Miasma Bolt")["id"], ids["Miasma Bolt"])

    def test_an_id_the_star_column_contradicts_is_unknown(self):
        bad = _blobs(skills=_blobs()["skills"].replace(b"Miasma Bolt\t15\t", b"Miasma Bolt\t99\t"))
        t, why = ST.assemble(bad)
        self.assertIsNotNone(t, why)
        self.assertIsNone(_skill(_tab(t, "war", "Chaos"), "Miasma Bolt")["id"],
                          "row 15 and *Id 99 disagree, and one of them was picked")


class TheTabOrderIsNeverGuessed(unittest.TestCase):

    def test_no_layout_leaves_every_tab_unknown(self):
        t, why = ST.assemble(_blobs(treelayout=None))
        self.assertIsNotNone(t, why)
        for code, c in t["classes"].items():
            self.assertEqual(len(c["tabs"]), 3)
            for x in c["tabs"]:
                self.assertIsNone(x["index"], "%s page %s was given a tab position with no layout" % (code, x["page"]))
                self.assertIsNone(x["name"], "%s page %s was given a tab name with no layout" % (code, x["page"]))
                self.assertIn("layout", x["tabWhy"])
        self.assertEqual((t["grid"]["rows"], t["grid"]["cols"]), (None, None))
        self.assertEqual(t["counts"]["untitledTabs"], 6)

    def test_no_item_modifiers_leaves_the_order_unknown(self):
        t, why = ST.assemble(_blobs(itemmods=None))
        self.assertIsNotNone(t, why)
        self.assertEqual({x["index"] for c in t["classes"].values() for x in c["tabs"]}, {None})

    def test_a_layout_slot_that_names_another_class_is_not_trusted(self):
        swapped = LAYOUT.replace(r'"Spells\\Druid\\DrSkillicon"', r'"Spells\\Assassin\\AsSkillicon"', 1)
        t, why = ST.assemble(_blobs(treelayout=swapped.encode("utf-8")))
        self.assertIsNotNone(t, why)
        self.assertEqual({x["name"] for x in t["classes"]["dru"]["tabs"]}, {None})
        self.assertEqual([x["name"] for x in t["classes"]["war"]["tabs"]], ["Chaos", "Eldritch", "Demon"])

    def test_a_tie_between_two_orders_is_unknown(self):
        order, why = ST._tab_positions({1: {"auras"}, 2: {"auras"}, 3: {"combat"}},
                                       {0: {"auras"}, 1: {"auras"}, 2: {"combat"}})
        self.assertIsNone(order, "two assignments agree equally and one was picked")
        self.assertIn("tie", why)

    def test_the_best_order_wins_over_a_merely_possible_one(self):
        # the Paladin's shape: 'auras' fits both aura tabs, the full words fit only one way
        order, why = ST._tab_positions({1: {"combat"}, 2: {"offensive", "auras"}, 3: {"defensive", "auras"}},
                                       {0: {"defensive", "auras"}, 1: {"offensive", "auras"}, 2: {"combat"}})
        self.assertEqual(order, {1: 2, 2: 1, 3: 0}, why)


class ABrokenSourceIsRefused(unittest.TestCase):

    def test_a_corrupt_layout_is_not_an_absent_one(self):
        t, why = ST.assemble(_blobs(treelayout=b"{ this is not json"))
        self.assertIsNone(t)
        self.assertIn("treelayout", why)

    def test_a_corrupt_string_table_is_not_an_empty_one(self):
        t, why = ST.assemble(_blobs(skillnames=b"[{broken"))
        self.assertIsNone(t)
        self.assertIn("skillnames", why)

    def test_no_skills_table_is_no_tree(self):
        t, why = ST.assemble(_blobs(skills=None))
        self.assertIsNone(t)
        self.assertIn("skills", why)


class TheCommittedTables(unittest.TestCase):
    """tv/skill_tables.json is GENERATED and COMMITTED: absent is a broken checkout, so it FAILS."""

    @classmethod
    def setUpClass(cls):
        cls.t = ST.load(ST.STORE)

    def setUp(self):
        self.assertIsNotNone(self.t, "tv/skill_tables.json is missing or unreadable — run: python3 tv/skill_tables.py --write")

    def test_every_law_holds_on_his_install_s_trees(self):
        _laws(self, self.t, "committed")

    def test_every_class_of_the_game_is_there(self):
        self.assertEqual(self.t["classesWithoutSkills"], [])
        for code in CLASSIC:
            self.assertIn(code, self.t["classes"])
        extra = [c for c in self.t["classOrder"] if c not in CLASSIC]
        print("   %d classes: %s (beyond the classic seven: %s)"
              % (len(self.t["classOrder"]), " ".join(self.t["classOrder"]), " ".join(extra) or "none"))

    def test_every_skill_is_named_placed_and_has_an_icon(self):
        for code, c in self.t["classes"].items():
            self.assertTrue(c["name"] and c["iconFile"], "%s: class name / icon sheet UNKNOWN" % code)
            for x in c["tabs"]:
                self.assertTrue(x["name"], "%s page %s has no tab name: %s" % (code, x["page"], x["tabWhy"]))
                for s in x["skills"]:
                    for f in ("name", "iconIndex", "maxlvl"):
                        self.assertIsNotNone(s[f], "%s %s: %s is UNKNOWN" % (code, s["key"], f))

    def test_the_druid_tree_is_the_druid_tree(self):
        self.assertEqual([x["name"] for x in self.t["classes"]["dru"]["tabs"]],
                         ["Elemental", "Shape Shifting", "Summoning"])
        el = _tab(self.t, "dru", "Elemental")
        tor, hur = _skill(el, "Tornado"), _skill(el, "Hurricane")
        self.assertEqual((hur["col"], hur["row"]), (tor["col"], tor["row"] + 1), "Hurricane is not right below Tornado")
        self.assertIn(tor["id"], hur["prereqs"])
        self.assertEqual(hur["row"], 6, "Hurricane is a level-30 skill and must sit in the bottom row")
        wolf = _skill(_tab(self.t, "dru", "Shape Shifting"), "Werewolf")
        self.assertEqual((wolf["row"], wolf["prereqs"]), (1, []), "Werewolf is a top-row skill with no prerequisite")
        griz = _skill(_tab(self.t, "dru", "Summoning"), "Summon Grizzly")
        dire = _skill(_tab(self.t, "dru", "Summoning"), "Summon Dire Wolf")
        self.assertEqual(griz["row"], 6)
        self.assertEqual(griz["prereqs"], [dire["id"]])
        for name, home in (("Tornado", "Elemental"), ("Hurricane", "Elemental"),
                           ("Werewolf", "Shape Shifting"), ("Summon Grizzly", "Summoning")):
            where = [x["name"] for x in self.t["classes"]["dru"]["tabs"]
                     if any(s["name"] == name for s in x["skills"])]
            self.assertEqual(where, [home], "%s is in %r" % (name, where))


class TheInstallAgrees(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.have = ST.load(ST.STORE)
        cls.fresh, cls.why = ST.build()

    def setUp(self):
        if self.fresh is None:
            self.skipTest("UNMEASURED: no install to re-derive from here (%s) — the committed json's "
                          "freshness is not known, which is not the same as fresh" % self.why)
        self.assertIsNotNone(self.have, "tv/skill_tables.json is missing or unreadable")

    def test_the_source_hash_matches_a_fresh_build(self):
        self.assertEqual(self.fresh["sourceHash"], self.have["sourceHash"],
                         "the install has changed since tv/skill_tables.json was generated — run --write")

    def test_the_committed_json_is_what_the_builder_writes_now(self):
        self.assertEqual(json.loads(ST.serialise(self.fresh)), self.have,
                         "same install, different trees: skill_tables.py changed and --write was not re-run")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the tab position is assumed to be page - 1 instead of derived: the Druid's Tornado and "
               "Hurricane land under 'Summoning' and the Warlock reads Demon / Eldritch / Chaos",
        "file": "tv/skill_tables.py",
        "find": "            index = order.get(page) if order else None\n",
        "replace": "            index = page - 1 if page else None\n",
        "matches": 1,
    },
    {
        "why": "skilldesc is joined by ROW ORDER instead of by the skills.txt `skilldesc` key: every "
               "skill takes another skill's row, column, page and name",
        "file": "tv/skill_tables.py",
        "find": "            d = descs.get(r.get(\"skilldesc\") or \"\")\n",
        "replace": "            d = desc_rows[n] if n < len(desc_rows) else None\n",
        "matches": 1,
    },
    {
        "why": "a skill with no display string is printed under its table KEY (Wearwolf, Plague Poppy) "
               "instead of reading UNKNOWN",
        "file": "tv/skill_tables.py",
        "find": "                \"name\": skill_names.get((d or {}).get(\"str name\") or \"\") or None,\n",
        "replace": "                \"name\": skill_names.get((d or {}).get(\"str name\") or \"\") or r.get(\"skill\"),\n",
        "matches": 1,
    },
    {
        "why": "only reqskill1 is read: Summon Dire Wolf loses Summon Spirit Wolf, Bind Demon loses Summon Defiler",
        "file": "tv/skill_tables.py",
        "find": "for k in (\"reqskill1\", \"reqskill2\", \"reqskill3\") if r.get(k)]",
        "replace": "for k in (\"reqskill1\",) if r.get(k)]",
        "matches": 1,
    },
    {
        "why": "a tie between two tab orders is settled by taking the first instead of reading UNKNOWN",
        "file": "tv/skill_tables.py",
        "find": "    if len(scored) > 1 and scored[0][0] == scored[1][0]:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
]
