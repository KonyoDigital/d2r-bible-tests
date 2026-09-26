# -*- coding: utf-8 -*-
"""#174 v-B3 — THE CHARACTER SHEET SUMS THE AFFIXES HE PICKED, EXACTLY LIKE A UNIQUE'S PROPS, AND NOTHING ELSE MOVES.

His order (2026-09-26): "mods and buffs ranges of them all with manual additions to add so they sync to them item".
Before this a magic or rare item was one answer: UNKNOWN for every stat its affix pool could touch ("its affixes roll
from the affix tables and none was typed"). Now the Edit tab's ADD MOD stores the affixes on the entry
({affixes: [{id, rolls: {m1..m3}}]}) and window.D2R_CHAR_ENGINE sums each picked row of _CE_DATA.affixRows — which
tv/char_props.py generates from his install's magicprefix / magicsuffix / automagic / qualityitems — as it sums a
unique's lines: typed = EXACT (only inside its range), untouched = the RANGE, never averaged; an id the tables do not
have is an UNKNOWN row naming it, never a 0. With none picked it adds nothing and says so (the pool stays UNKNOWN).

THE GAME DATA (his install, 2026-09-26; the premise case re-reads each from the SHIPPED block):
    magicprefix.txt Chaotic   (p700)  skilltab par 23, 1..1 — +1 to Chaos Skills (Warlock Only), lcha
    magicsuffix.txt of Vita   (s338)  hp 36..40, lcha
    magicprefix.txt Devil's   (p712)  war 1..1 — +1 to Warlock Skills, amul / circ
    magicprefix.txt Ruby      (p374)  res-fire 31..40, circ
    magicsuffix.txt of the Magus (s175) cast3 20..20, circ
    qualityitems.txt row 2    (q2)    ac% 5..15 (armor, shield, boots, gloves, belt)
    magicprefix.txt Godly     (p150)  ac% 101..200 · Mnemonic (p540) mana/lvl 6 · printed "Mojo" (p464, table key Vodoun)
    magicsuffix.txt of Memory (s408)  mana/lvl 6 · of the Elephant (s409) hp/lvl 4 + mana/lvl 2
    magicsuffix.txt of Magic Arrows (s458) charged skill 6 (Magic Arrow), mod1min -30, mod1max -10 - NEGATIVE: set by the
                              item level in the game's code (every one of the 112 charged suffixes)
    armor.txt Diadem (ci3) 50..60 defense · misc.txt Grand Charm (cm3), type lcha, a charm
    difficultylevels.txt Hell -100 · Anya's scrolls +10 per difficulty completed (a rule, quests on) = +30 at Hell

THE HAND-WORKED ANSWERS (a Warlock, level 90, Hell, quests on):
  A  A MAGIC GRAND CHARM "Chaotic Grand Charm of Vita" in the inventory moves EXACTLY two rows against the same build
     without it: + Chaos Skills (tab:23) 0 -> 1 EXACT, Life (items) 0 -> 36..40 RANGE. Every other row is identical.
  B  typed of Vita 40 -> Life 40 EXACT; typed 41 (outside 36..40) -> REFUSED, a problem says so, Life stays 36..40.
  C  the same charm with NO affixes picked adds nothing and says so: Life is UNKNOWN naming "none was picked".
  D  on a Sorceress, Chaotic (+1 Chaos Skills, Warlock Only) is named under notApplied and summed nowhere.
  E  A RARE DIADEM with three mods (Devil's, Ruby, of the Magus): Class Skills 0 -> 1 EXACT; Fire Resistance -100 + 30
     + 31..40 = -39..-30 RANGE; FCR 20 EXACT; and its base's Defense 50..60 RANGE — those four rows and no other.
     Ruby typed 38 -> fire -32 EXACT.
  F  its base defense TYPED 55 (inside 50..60) -> Defense 55 EXACT; typed 99 -> refused, the range 50..60 stands.
  G  A SUPERIOR Diadem, qualityitems row 2 (ac% 5..15) typed 15 and base defense typed 60 -> it was BORN with Enhanced
     Defense, so its base is max + 1 = 61 whatever was typed: floor(61 x 115 / 100) = 70 (#174 v-B3 fix round; the
     first cut read 69 - a number the game never shows).
  H  A LOW-quality Diadem: its penalty is the game's code, so Defense is UNKNOWN naming it — never 50..60.
  I  an affix id the tables do not have (p99999) is an UNKNOWN row naming it; the rest still sums.
  #174 v-B3 FIX ROUND (the review's reproduced findings):
  J  A MAGIC Godly Diadem (+101..200% ED): typed 200 -> floor(61 x 300 / 100) = 183 EXACT (the base at max + 1, the rule
     uniques and sets already had - Blizzard's "Enhanced defense on armour" thread: superior / magic / rare / unique /
     set, runewords excepted); untouched -> floor(61 x 201 / 100) .. 183 = 122..183 RANGE, never 150..180.
  K  of Magic Arrows on a Short Bow: the proc row is UNKNOWN saying the item level sets it - never "-10 EXACT".
  L  Mnemonic + of Memory on a Circlet at level 90: ONE item stat, (6 + 6) x 90 >> 3 = 135 EXACT (line by line 134);
     Mnemonic + of the Elephant: (6 + 2) x 90 >> 3 = 90 mana and 4 x 90 >> 3 = 45 life.
  M  the sheet names an affix what the item shows: a Mojo Amulet's skill row says "Mojo", never "Vodoun".
And the block itself: tv/char_props.py --check where the install is (UNMEASURED elsewhere, never green), and every af
row of the builder's CB_DB block (tv/char_builder_db.py, the OTHER generator) names an affixRows id with the same codes.
RED_PROOF below.
"""
import json
import os
import shutil
import subprocess
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

import char_props as CP  # noqa: E402
import test_the_character_sheet_sums_the_game_data as SH  # noqa: E402  the engine's own cut (_src, _engine)

NODE = shutil.which("node")
HELL = {"difficulty": "Hell", "quests": True}
GC = "Chaotic Grand Charm of Vita"


def _gc(affixes=None, **kw):
    e = {"name": GC, "base": "cm3", "quality": "magic"}
    if affixes is not None:
        e["affixes"] = affixes
    e.update(kw)
    return e


def _diadem(quality, name="ci3", **kw):
    e = {"name": name, "base": "ci3", "quality": quality}
    e.update(kw)
    return e


def _build(cls="Warlock", slots=None, inv=None):
    return {"cls": cls, "level": 90, "sets": [{"name": "Set 1", "slots": slots or {}, "inv": inv or []}]}


PICK = [{"id": "p700", "rolls": {}}, {"id": "s338", "rolls": {}}]
RARE3 = [{"id": "p712", "rolls": {}}, {"id": "p374", "rolls": {}}, {"id": "s175", "rolls": {}}]
CASES = {
    "bare": (_build(), HELL),
    "A": (_build(inv=[_gc(PICK)]), HELL),
    "B-typed": (_build(inv=[_gc([{"id": "p700", "rolls": {}}, {"id": "s338", "rolls": {"m1": 40}}])]), HELL),
    "B-out": (_build(inv=[_gc([{"id": "p700", "rolls": {}}, {"id": "s338", "rolls": {"m1": 41}}])]), HELL),
    "C": (_build(inv=[_gc()]), HELL),
    "D": (_build(cls="Sorceress", inv=[_gc(PICK)]), HELL),
    "bareSorc": (_build(cls="Sorceress"), HELL),
    "E": (_build(slots={"head": _diadem("rare", "Beast Crest", affixes=RARE3)}), HELL),
    "E-typed": (_build(slots={"head": _diadem("rare", "Beast Crest", affixes=[
        {"id": "p712", "rolls": {}}, {"id": "p374", "rolls": {"m1": 38}}, {"id": "s175", "rolls": {}}])}), HELL),
    "F": (_build(slots={"head": _diadem("rare", "Beast Crest", affixes=RARE3, def_=None)}), HELL),
    "G": (_build(slots={"head": _diadem("superior", def_=None, affixes=[{"id": "q2", "rolls": {"m1": 15}}])}), HELL),
    "H": (_build(slots={"head": _diadem("low")}), HELL),
    "I": (_build(inv=[_gc([{"id": "p99999", "rolls": {}}, {"id": "s338", "rolls": {}}])]), HELL),
    "J": (_build(cls="Sorceress", slots={"head": _diadem("magic", "Godly Diadem", affixes=[{"id": "p150", "rolls": {"m1": 200}}])}), HELL),
    "J-range": (_build(cls="Sorceress", slots={"head": _diadem("magic", "Godly Diadem", affixes=[{"id": "p150", "rolls": {}}])}), HELL),
    "K": (_build(cls="Amazon", slots={"rarm": {"name": "Short Bow of Magic Arrow", "base": "sbw", "quality": "magic",
                                               "affixes": [{"id": "s458", "rolls": {}}]}}), HELL),
    "L": (_build(cls="Sorceress", slots={"head": {"name": "Mnemonic Circlet of Memory", "base": "ci0", "quality": "magic",
                                                  "affixes": [{"id": "p540", "rolls": {}}, {"id": "s408", "rolls": {}}]}}), HELL),
    "L-elephant": (_build(cls="Sorceress", slots={"head": {"name": "Mnemonic Circlet of the Elephant", "base": "ci0", "quality": "magic",
                                                           "affixes": [{"id": "p540", "rolls": {}}, {"id": "s409", "rolls": {}}]}}), HELL),
    "M": (_build(cls="Necromancer", slots={"neck": {"name": "Mojo Amulet", "base": "amu", "quality": "magic",
                                                    "affixes": [{"id": "p464", "rolls": {}}]}}), HELL),
}
# `def` is a keyword in python; the entry key the engine reads is "def"
CASES["F"][0]["sets"][0]["slots"]["head"].pop("def_")
CASES["F"][0]["sets"][0]["slots"]["head"]["def"] = 55
CASES["F-out"] = (json.loads(json.dumps(CASES["F"][0])), HELL)
CASES["F-out"][0]["sets"][0]["slots"]["head"]["def"] = 99
CASES["G"][0]["sets"][0]["slots"]["head"].pop("def_")
CASES["G"][0]["sets"][0]["slots"]["head"]["def"] = 60

DRIVER = r"""
var window = {};
%(engine)s
var E = window.D2R_CHAR_ENGINE, C = %(cases)s, out = {};
Object.keys(C).forEach(function(k){ out[k] = E.sheet(C[k][0], C[k][1]); });
process.stdout.write(JSON.stringify(out));
"""
_RUN = {}


def _run():
    if "out" not in _RUN:
        js = DRIVER % {"engine": SH._engine(SH._src()), "cases": json.dumps(CASES)}
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=90)
        if r.returncode != 0:
            raise AssertionError("the shipped stats engine would not run - UNKNOWN, not passing: %s" % r.stderr[:900])
        _RUN["out"] = json.loads(r.stdout)
    return _RUN["out"]


def _rows(case):
    return dict((r["key"], r) for r in _run()[case]["rows"])


def _val(case, key):
    r = _rows(case)[key]
    return (None if r["value"] is None else (r["value"]["min"], r["value"]["max"])), r["source"]


def _moved(a, b):
    ra, rb = _rows(a), _rows(b)
    return sorted(k for k in set(ra) | set(rb)
                  if (ra.get(k) or {}).get("value") != (rb.get(k) or {}).get("value")
                  or (ra.get(k) or {}).get("source") != (rb.get(k) or {}).get("source"))


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheSheetSumsPickedAffixes(unittest.TestCase):

    def test_premise_the_shipped_block_carries_the_rows_the_answers_were_worked_from(self):
        d = CP.embedded(SH._src())
        self.assertIsNotNone(d, "bible.html carries no parseable CHAR_PROPS block")
        rows = d.get("affixRows") or {}
        want = {"p700": ["Chaotic", [["m1", "skilltab", "23", 1, 1]]], "s338": ["of Vita", [["m1", "hp", "", 36, 40]]],
                "p712": ["Devil's", [["m1", "war", "", 1, 1]]], "p374": ["Ruby", [["m1", "res-fire", "", 31, 40]]],
                "s175": ["of the Magus", [["m1", "cast3", "", 20, 20]]], "q2": ["superior", [["m1", "ac%", "0", 5, 15]]],
                "p150": ["Godly", [["m1", "ac%", "", 101, 200]]], "p540": ["Mnemonic", [["m1", "mana/lvl", "6", None, None]]],
                "s408": ["of Memory", [["m1", "mana/lvl", "6", None, None]]],
                "s409": ["of the Elephant", [["m1", "hp/lvl", "4", None, None], ["m2", "mana/lvl", "2", None, None]]],
                "s458": ["of Magic Arrow", [["m1", "charged", "6", -30, -10]]], "p464": ["Mojo", [["m1", "skilltab", "8", 2, 2]]]}
        for k, v in want.items():
            self.assertEqual(rows.get(k), v, "the premise moved: affixRows %s" % k)
        self.assertNotIn("p99999", rows)
        self.assertEqual(d["bases"]["ci3"][2:4], [50, 60])
        self.assertEqual((d["bases"]["cm3"][5], d["bases"]["cm3"][6]), ("lcha", 1))

    def test_A_a_magic_grand_charm_moves_exactly_its_two_rows(self):
        self.assertEqual(_moved("bare", "A"), ["life", "tab:23"], "the charm moved rows its two affixes never touch")
        self.assertEqual(_val("bare", "tab:23"), ((0, 0), "EXACT"))
        self.assertEqual(_val("A", "tab:23"), ((1, 1), "EXACT"))
        self.assertEqual(_val("A", "life"), ((36, 40), "RANGE"), "an untouched roll is its whole range, never averaged")
        why = _rows("A")["life"]["why"]
        self.assertIn(GC, why)
        self.assertIn("of Vita", why, "the life row does not say which affix it came from")

    def test_B_typed_is_exact_and_outside_is_refused(self):
        self.assertEqual(_val("B-typed", "life"), ((40, 40), "EXACT"))
        self.assertEqual(_val("B-out", "life"), ((36, 40), "RANGE"), "a typed 41 outside 36..40 moved the sum")
        self.assertTrue(any("41" in p and "36..40" in p for p in _run()["B-out"]["problems"]),
                        "the refused roll is not said: %s" % _run()["B-out"]["problems"])

    def test_C_none_picked_adds_nothing_and_says_so(self):
        v, src = _val("C", "life")
        self.assertEqual((v, src), (None, "UNKNOWN"))
        self.assertIn("none was picked", _rows("C")["life"]["why"])

    def test_D_a_class_tied_affix_on_another_class_is_not_applied(self):
        self.assertEqual(_moved("bareSorc", "D"), ["life"], "Chaotic moved a Sorceress's sheet")
        self.assertTrue(any("Chaos Skills" in (n.get("why") or "") for n in _run()["D"]["notApplied"]),
                        "Chaotic on a Sorceress is not named under notApplied")

    def test_E_a_rare_with_three_mods_sums_them(self):
        self.assertEqual(_moved("bare", "E"), ["class-skills", "defense", "fcr", "res-fire"])
        self.assertEqual(_val("E", "class-skills"), ((1, 1), "EXACT"))
        self.assertEqual(_val("E", "res-fire"), ((-39, -30), "RANGE"))
        self.assertEqual(_val("E", "fcr"), ((20, 20), "EXACT"))
        self.assertEqual(_val("E", "defense"), ((50, 60), "RANGE"))
        self.assertEqual(_val("E-typed", "res-fire"), ((-32, -32), "EXACT"))

    def test_F_a_typed_base_defense_is_exact_and_outside_is_refused(self):
        self.assertEqual(_val("F", "defense"), ((55, 55), "EXACT"))
        self.assertEqual(_val("F-out", "defense"), ((50, 60), "RANGE"))
        self.assertTrue(any("99" in p and "50-60" in p for p in _run()["F-out"]["problems"]))

    def test_G_a_superior_row_raises_its_own_items_defense(self):
        self.assertEqual(_val("G", "defense"), ((70, 70), "EXACT"), "born with ED: max + 1 = 61, floor(61 x 115 / 100) = 70")
        self.assertIn("max+1 = 61", _rows("G")["defense"]["why"])
        self.assertIn("typed 60 is set aside", _rows("G")["defense"]["why"])

    def test_J_a_magic_item_born_with_enhanced_defense_sits_at_max_plus_one(self):
        self.assertEqual(_val("J", "defense"), ((183, 183), "EXACT"), "Godly +200% on a Diadem: floor(61 x 300 / 100) = 183")
        self.assertEqual(_val("J-range", "defense"), ((122, 183), "RANGE"), "untouched: floor(61 x 201 / 100) .. 183")

    def test_K_a_negative_charged_level_is_unknown_never_a_number(self):
        procs = [r for r in _run()["K"]["rows"] if r["key"].startswith("proc:") and ":charged:" in r["key"]]
        self.assertEqual(len(procs), 1, "PRINT THE DENOMINATOR: %d charged proc rows" % len(procs))
        self.assertEqual((procs[0]["value"], procs[0]["source"]), (None, "UNKNOWN"), "of Magic Arrows read %s" % procs[0])
        self.assertIn("set by the item level", procs[0]["why"])
        self.assertNotIn("-10", procs[0]["label"] + procs[0]["why"], "a negative skill level is still printed")

    def test_L_two_affixes_of_one_per_level_stat_are_one_stat(self):
        self.assertEqual(_val("L", "mana"), ((135, 135), "EXACT"), "(6 + 6) x 90 >> 3 = 135, not 67 + 67")
        self.assertEqual(_val("L-elephant", "mana"), ((90, 90), "EXACT"), "(6 + 2) x 90 >> 3 = 90, not 67 + 22")
        self.assertEqual(_val("L-elephant", "life"), ((45, 45), "EXACT"), "of the Elephant's life per level alone: 4 x 90 >> 3")

    def test_M_the_sheet_names_the_affix_the_item_shows(self):
        tab = _rows("M")["tab:8"]
        self.assertEqual((tab["value"], tab["source"]), ({"min": 2, "max": 2}, "EXACT"))
        self.assertIn("(Mojo)", tab["why"])
        self.assertNotIn("Vodoun", tab["why"], "the sheet names the table key, not the affix the item shows")

    def test_H_a_low_quality_base_has_unknown_defense(self):
        v, src = _val("H", "defense")
        self.assertEqual((v, src), (None, "UNKNOWN"))
        self.assertIn("low quality", _rows("H")["defense"]["why"])

    def test_I_an_affix_the_tables_do_not_have_is_unknown_naming_it(self):
        bad = [r for r in _run()["I"]["rows"] if r["source"] == "UNKNOWN" and "p99999" in (r.get("why") or "")]
        self.assertEqual(len(bad), 1, "p99999 is not ONE UNKNOWN row naming it")
        self.assertEqual(_val("I", "life"), ((36, 40), "RANGE"), "the known affix beside it stopped summing")

    def test_the_two_generators_name_the_same_affixes(self):
        """every af row of the builder has an engine row with its codes AND its printed name (fix round: M)"""
        import char_builder_db as CBDB
        src = SH._src()
        cb, cp = CBDB.embedded(src), CP.embedded(src)
        rows = cp["affixRows"]
        bad = []
        for a in cb["af"]:
            r = rows.get(a[0])
            if not r:
                bad.append("%s %s has no engine row" % (a[0], a[2]))
                continue
            codes = set(x[1] for x in r[1])
            for l in a[11]:
                for c in str(l[3]).split("+"):
                    if c and c not in codes:
                        bad.append("%s %s: the builder line %s is not an engine code %s" % (a[0], a[2], c, sorted(codes)))
            # #174 v-B3 fix round: and ONE name - the sheet's row says the affix the item shows (116 said the table key)
            if r[0] != a[2]:
                bad.append("%s: the builder names it %r, the engine %r" % (a[0], a[2], r[0]))
        for r in cb["qm"]["sup"]:
            if r[0] not in rows:
                bad.append("superior %s has no engine row" % r[0])
        self.assertGreater(len(cb["af"]), 1000, "PRINT THE DENOMINATOR: %d af rows" % len(cb["af"]))
        self.assertEqual(bad, [], "\n  ".join(bad[:20]))

    def test_the_shipped_block_matches_his_install_where_there_is_one(self):
        code, say = CP.check()
        if code == CP.SKIP:
            self.skipTest("UNMEASURED here, not passed: " + say)
        self.assertEqual(code, 0, say)


RED_PROOF = [
    {
        "why": "#174 v-B3 - the picked affixes are never summed (the sheet ignores ADD MOD)",
        "file": "bible.html",
        "find": "      picked.forEach(function(a){\n        var row = Object.prototype.hasOwnProperty.call(D.affixRows || {}, a.id)",
        "replace": "      [].forEach(function(a){\n        var row = Object.prototype.hasOwnProperty.call(D.affixRows || {}, a.id)",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - an item with picked affixes still blanks its whole affix pool as UNKNOWN",
        "file": "bible.html",
        "find": "      if (it.kind === 'affixed' && !picked.length){\n",
        "replace": "      if (it.kind === 'affixed'){\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - a typed affix roll is ignored, so it stays a range",
        "file": "bible.html",
        "find": "via: row[0] || a.id, typed: Object.prototype.hasOwnProperty.call(ar, l[0]) ? ar[l[0]] : undefined };\n",
        "replace": "via: row[0] || a.id, typed: undefined };\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - a low-quality base reads its full defense (a number nobody measured)",
        "file": "bible.html",
        "find": "          if (it.low){ ex.unknown = (ex.unknown || []).concat([",
        "replace": "          if (false){ ex.unknown = (ex.unknown || []).concat([",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - a typed base defense is ignored",
        "file": "bible.html",
        "find": "          if (tdef !== null && tdef >= b[2] && tdef <= b[3]){ bmin = bmax = tdef; why = 'base typed ' + tdef; }\n",
        "replace": "          if (false){ bmin = bmax = tdef; why = 'base typed ' + tdef; }\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - an affix id the tables do not have is dropped silently (a 0 nobody measured)",
        "file": "bible.html",
        "find": "        if (!row){ unmap({ src: src, slot: it.slot }, 'affix ' + a.id,",
        "replace": "        if (!row){ return; unmap({ src: src, slot: it.slot }, 'affix ' + a.id,",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - the generator writes non-spawnable affix rows the game never rolls",
        "file": "char_props.py",
        "find": "            if kind != \"q\" and r.get(\"spawnable\") != \"1\":\n",
        "replace": "            if False:\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - a magic / rare / superior item born with Enhanced Defense reads its base's min..max",
        "file": "bible.html",
        "find": "          else if (it.pickEd && it.kind !== 'runeword'){ bmin = bmax = b[3] + 1;",
        "replace": "          else if (false){ bmin = bmax = b[3] + 1;",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - an affix table's negative charged level is summed as a level (-10 EXACT)",
        "file": "bible.html",
        "find": "          if (func === 19 && ((mn !== null && mn < 0) || (mx !== null && mx < 0))){\n",
        "replace": "          if (false){\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - two affixes of one per-level stat are scaled and floored apart (134, not 135)",
        "file": "bible.html",
        "find": "        if (g.length === 1){ plain.push(g[0]); return; }\n",
        "replace": "        if (true){ g.forEach(function(o){ plain.push(o); }); return; }\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - the engine names an affix by its table key (Vodoun), not what the item shows (Mojo)",
        "file": "bible.html",
        "find": "    \"p464\":[\"Mojo\",",
        "replace": "    \"p464\":[\"Vodoun\",",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - the generator names the affix rows by the table key again",
        "file": "char_props.py",
        "find": "rows_of[kind + str(i)] = [(naff.get(nk) or names.get(nk) or nk) if nk else",
        "replace": "rows_of[kind + str(i)] = [nk if nk else",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("⚪ SKIP — node is not on this machine, so the stats engine was not driven. UNMEASURED, declared (77).\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
