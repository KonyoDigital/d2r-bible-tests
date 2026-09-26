# -*- coding: utf-8 -*-
"""#174 v-B3 — THE AFFIX ROWS THE BUILDER OFFERS ARE HIS INSTALL'S: EVERY SPAWNABLE ROW, ITS OWN NUMBERS, ITS OWN WORDS.

The Edit tab's ADD MOD lists affixes, and the sheet sums them; both read the ⟦CB_DB⟧ block's af / rn / qm rows that
tv/char_builder_db.py writes from his install (magicprefix / magicsuffix / automagic / rareprefix / raresuffix /
qualityitems / lowqualityitems .txt and item-nameaffixes.json). A picker that invents a range, drops a row or renames
a word is a picker that lies about the game, so this law holds the block to the tables:

  · THE ROWS ARE THE SPAWNABLE ONES, COUNTED: counts.affixes = every af row = prefixes + suffixes + automods; each row
    is [id, kind, name, level, maxlevel, levelreq, rare, group, class, itypes, etypes, lines, frequency, class level
    requirement] with its id's first letter its kind; the rare words and the superior rows are counted the same way.
  · A NAMED SAMPLE, HAND-READ FROM HIS TABLES (2026-09-26): Chaotic (magicprefix row 700) level 50, no maxlevel,
    levelreq 42, rare 1, group 125, the Warlock's, itypes [lcha], one line "+1 to Chaos Skills (Warlock Only)" 1..1 on
    skilltab, frequency 1 · of Vita (magicsuffix row 338) level 77, levelreq 69, rare 0, group 26, hp 36..40 · Ruby
    (magicprefix 374) res-fire 31..40 on rod / boot / amul / orb / circ · Crimson (magicprefix 665) maxlevel 4 · the
    classic duplicate Sturdy (magicprefix 1, frequency 0) is kept in the data and marked 0, never offered.
  · THE RARE WORDS ARE THE SAME WORDS tv/affix_lexicon.json (a DIFFERENT generator over the same tables) resolved, AND
    THE SIX IT LEAVES UNRESOLVED: the lexicon reads two string tables and records GhoulRI, Wraithra, Fiendra · crusher,
    strap, scarab as unresolved; the game asks every table, and his install names all six - monsters.json GhoulRI
    "Ghoul", Wraithra "Wraith", Fiendra "Fiend", crusher "Crusher", scarab "Scarab"; ui.json strap "Strap" (#174 v-B3
    fix round: the builder offered 6 of the game's words never). So the builder's named words = the lexicon's + these
    six, and none is left unnamed. Where the install is, each is re-read from monsters.json / ui.json.
  · #174 v-B3 FIX ROUND, ALSO FROM THE TABLES: a base's `magic lvl` is its b[23] (Diadem 18, Circlet 3, Small Charm 0)
    beside its qlvl b[18] (Diadem 85, Small Charm 28) - the page's affix level is worked from them; an affix's [13] is
    magicsuffix.txt `class` / `classlevelreq` (of Magic Arrow: levelreq 11, [Amazon, 1]); and a charged skill the table
    gives as NEGATIVE (all 112 "of <Skill>" suffixes: of Magic Arrows mod1min -30, mod1max -10) is ONE UNKNOWN line
    ("Level ? Magic Arrow (?/? Charges) - set by the item level ...") - no charged line anywhere carries a negative.
  · QUALITY IS itemtypes.txt's OWN FLAG PER TYPE, NEVER INHERITED: a Circlet may be Rare · Magic · Superior · Normal ·
    Low, a Ring / a Jewel Rare · Magic, a Grand Charm Magic only (its ancestor `misc` says Rare 1 — not the charm's), a
    quiver Normal only; qualityitems row 2 (ac% 5..15) applies to armor / shield / boots / gloves / belt; the low words
    are Crude · Cracked · Damaged · Low Quality; a base's automod group is its `auto prefix` (Stag Bow 300, Eagle Orb 303).
  · WHERE THE INSTALL IS, EVERY ROW IS RE-READ FROM THE RAW TABLE (no generator code in between): each spawnable,
    named row with a mod is one af row with the table's level / maxlevel / levelreq / rare / group / itypes / etypes /
    frequency and the table's mod codes; and tv/char_builder_db.py --check is 0. With no install both say UNMEASURED
    (a skip), never pass.
RED_PROOF below.
"""
import io
import json
import os
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

import char_builder_db as CBDB  # noqa: E402


def _db():
    with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as f:
        d = CBDB.embedded(f.read())
    assert d is not None, "bible.html carries no parseable CB_DB block"
    return d


def _raw(label):
    """the install's raw table rows, or None (no install here). Read with the tables' own parser only."""
    import item_tables as IT
    for lab, path in CBDB.SOURCES:
        if lab == label:
            return IT._rows(IT._pull(path))
    return None


class TheAffixRowsAreTheInstalls(unittest.TestCase):

    def test_the_rows_are_counted_and_shaped(self):
        d = _db()
        c, af = d["counts"], d["af"]
        self.assertGreater(len(af), 1000, "PRINT THE DENOMINATOR: %d af rows" % len(af))
        self.assertEqual(c["affixes"], len(af))
        self.assertEqual(c["prefixes"] + c["suffixes"] + c["automods"], len(af))
        self.assertEqual([c["prefixes"], c["suffixes"], c["automods"]],
                         [sum(1 for a in af if a[1] == k) for k in "psa"])
        self.assertEqual(c["rareWords"], [len(d["rn"][0]), len(d["rn"][1])])
        self.assertEqual(c["superior"], len(d["qm"]["sup"]))
        bad = [a[0] for a in af if len(a) != 14 or a[0][0] != a[1] or a[1] not in "psa" or not a[11]
               or not isinstance(a[3], int) or (a[4] is not None and not isinstance(a[4], int))
               or not (a[13] is None or (isinstance(a[13], list) and len(a[13]) == 2 and all(isinstance(x, int) for x in a[13])))]
        self.assertEqual(bad, [], "af rows off their shape: %s" % bad[:10])
        self.assertEqual(len(set(a[0] for a in af)), len(af), "two af rows share an id")

    def test_a_named_sample_is_the_tables(self):
        d = _db()
        by, T = dict((a[0], a) for a in d["af"]), d["T"]
        war = [c["n"] for c in d["cls"]].index("Warlock")
        ch = by["p700"]
        self.assertEqual(ch[:11], ["p700", "p", "Chaotic", 50, None, 42, 1, 125, war, ["lcha"], []])
        self.assertEqual(ch[12], 1)
        self.assertEqual([(T[l[0]], l[1], l[3]) for l in ch[11]],
                         [("+{0} to Chaos Skills (Warlock Only)", [[1, 1, "m1"]], "skilltab")])
        vi = by["s338"]
        self.assertEqual(vi[:11], ["s338", "s", "of Vita", 77, None, 69, 0, 26, -1, ["lcha"], []])
        self.assertEqual([(T[l[0]], l[1], l[3]) for l in vi[11]], [("{+0} to Life", [[36, 40, "m1"]], "hp")])
        ru = by["p374"]
        self.assertEqual((ru[2], ru[9], [l[1] for l in ru[11]]), ("Ruby", ["rod", "boot", "amul", "orb", "circ"], [[[31, 40, "m1"]]]))
        self.assertEqual((by["p665"][2], by["p665"][3], by["p665"][4]), ("Crimson", 1, 4))
        st = by["p1"]
        self.assertEqual((st[2], st[12], [l[1] for l in st[11]]), ("Sturdy", 0, [[[20, 30, "m1"]]]),
                         "the classic Sturdy (frequency 0) is not kept as the table has it")
        # #174 v-B3 fix round: of Magic Arrow - its class level requirement, and its charges UNKNOWN, never -10 / -30
        ama = [c["n"] for c in d["cls"]].index("Amazon")
        ma = by["s458"]
        self.assertEqual((ma[2], ma[3], ma[5], ma[13]), ("of Magic Arrow", 12, 11, [ama, 1]))
        self.assertEqual([(T[l[0]], l[1], l[2], l[3]) for l in ma[11]],
                         [("Level ? Magic Arrow (?/? Charges) - set by the item level (the game's code, not a table value)", [], 2, "charged")])
        charged = [a for a in d["af"] if any(l[3] == "charged" for l in a[11])]
        neg = [a[0] for a in charged if any(r and not isinstance(r[0], str) and (r[0] < 0 or r[1] < 0)
                                            for l in a[11] if l[3] == "charged" for r in l[1])]
        self.assertEqual((len(charged), neg), (112, []), "PRINT THE DENOMINATOR: %d charged affix rows, negative: %s" % (len(charged), neg[:5]))
        self.assertEqual(sum(1 for a in d["af"] if a[13]), 112, "the 112 class level requirements of magicsuffix.txt")
        self.assertEqual([(d["b"][c][18], d["b"][c][23]) for c in ("ci3", "ci0", "cm1", "rin")], [(85, 18), (24, 3), (28, 0), (1, 0)],
                         "qlvl / magic lvl of Diadem, Circlet, Small Charm, Ring")

    #: the six rare keys the item string tables do not name, and what his install's other tables print for them
    SIX = {"rarePrefix": {"GhoulRI": "Ghoul", "Wraithra": "Wraith", "Fiendra": "Fiend"},
           "rareSuffix": {"crusher": "Crusher", "scarab": "Scarab", "strap": "Strap"}}

    def test_the_rare_words_are_the_lexicons(self):
        d = _db()
        with io.open(os.path.join(HERE, "affix_lexicon.json"), encoding="utf-8") as f:
            lex = json.load(f)
        for i, key in ((0, "rarePrefix"), (1, "rareSuffix")):
            named = sorted(set(w[0] for w in d["rn"][i] if w[3] == 1))
            unnamed = sorted(set(w[0] for w in d["rn"][i] if w[3] == 0))
            self.assertEqual(sorted(lex["unresolvedKeys"][key]), sorted(self.SIX[key]), "the premise moved: %s unresolved" % key)
            self.assertEqual(named, sorted(set(lex[key]) | set(self.SIX[key].values())),
                             "%s: the named words are not the lexicon's plus the six his other string tables name" % key)
            self.assertEqual(unnamed, [], "%s: a word no string table names is left: %s" % (key, unnamed))
        ghoul = [w for w in d["rn"][0] if w[0] == "Ghoul"]
        self.assertEqual(ghoul, [["Ghoul", ["armo", "weap", "misc"], [], 1]])
        beast = [w for w in d["rn"][0] if w[0] == "Beast"]
        self.assertEqual(beast, [["Beast", ["armo", "weap", "misc"], [], 1]])

    def test_quality_superior_low_and_automod_are_the_tables(self):
        d = _db()
        q = d["qm"]
        self.assertEqual(q["can"]["circ"], ["rare", "m", "sup", "b", "low"])
        self.assertEqual((q["can"]["ring"], q["can"]["jewl"], q["can"]["lcha"], q["can"]["bowq"]),
                         (["rare", "m"], ["rare", "m"], ["m"], ["b"]))
        self.assertEqual((q["cat"]["circ"], q["cat"]["orb"], q["cat"]["abow"], q["cat"]["ashd"], q["cat"].get("lcha")),
                         ("armor", "weapon", "bow", "shield", None))
        sup = dict((r[0], r) for r in q["sup"])
        self.assertEqual((sup["q2"][1][0][1], sup["q2"][1][0][3], sorted(sup["q2"][2])),
                         ([[5, 15, "m1"]], "ac%", ["armor", "belt", "boots", "gloves", "shield"]))
        self.assertEqual(q["low"], ["Crude", "Cracked", "Damaged", "Low Quality"])
        self.assertEqual((d["b"]["am1"][22], d["b"]["ob1"][22], d["b"]["ci3"][22]), (300, 303, 0))

    def test_every_row_is_the_raw_tables_where_the_install_is(self):
        raws = dict((lab, _raw(lab)) for lab in ("magicprefix", "magicsuffix", "automagic"))
        if any(v is None for v in raws.values()):
            self.skipTest("no install here: the raw affix tables could not be read - UNMEASURED, not passed")
        by = dict((a[0], a) for a in _db()["af"])
        seen, bad = 0, []
        for lab, kind in (("magicprefix", "p"), ("magicsuffix", "s"), ("automagic", "a")):
            for i, r in enumerate(raws[lab]):
                mods = [(r.get("mod%dcode" % j) or "").strip() for j in (1, 2, 3)]
                if r.get("spawnable") != "1" or not (r.get("Name") or "").strip() or not any(mods):
                    if (kind + str(i)) in by:
                        bad.append("%s%d is in the block and the table does not spawn it" % (kind, i))
                    continue
                seen += 1
                a = by.get(kind + str(i))
                if not a:
                    bad.append("%s%d %s is missing from the block" % (kind, i, r.get("Name")))
                    continue
                mx = (r.get("maxlevel") or "").strip()
                want = [CBDB._int(r.get("level")), int(mx) if mx else None, CBDB._int(r.get("levelreq")),
                        1 if r.get("rare") == "1" else 0, CBDB._int(r.get("group")),
                        [r.get("itype%d" % j) for j in range(1, 8) if r.get("itype%d" % j)],
                        [r.get("etype%d" % j) for j in range(1, 6) if r.get("etype%d" % j)], CBDB._int(r.get("frequency"))]
                cl = (r.get("class") or "").strip()
                want.append([[c["c"] for c in _db()["cls"]].index(cl), CBDB._int(r.get("classlevelreq"))]
                            if cl and str(r.get("classlevelreq") or "").strip() else None)
                got = [a[3], a[4], a[5], a[6], a[7], a[9], a[10], a[12], a[13]]
                if got != want:
                    bad.append("%s%d %s: block %s, table %s" % (kind, i, r.get("Name"), got, want))
                codes = set(c for l in a[11] for c in str(l[3]).split("+"))
                missing = [c for c in mods if c and c not in codes and c not in ("fire-max", "cold-max", "ltng-max", "pois-max", "cold-len", "pois-len")]
                if missing:
                    bad.append("%s%d %s: the table's %s drew no line" % (kind, i, r.get("Name"), missing))
        self.assertEqual(seen, len(by), "the block holds %d af rows and the tables spawn %d" % (len(by), seen))
        self.assertEqual(bad, [], "\n  ".join(bad[:20]))

    def test_the_six_words_are_his_installs_where_the_install_is(self):
        import item_tables as IT
        got = {}
        for lab in ("monsters", "ui"):
            path = dict(CBDB.SOURCES).get(lab)
            m = IT._strings(IT._pull(path)) if path else None
            if m is None:
                self.skipTest("no install here: %s could not be read - UNMEASURED, not passed" % lab)
            got.update(m)
        for key in ("rarePrefix", "rareSuffix"):
            for k, w in self.SIX[key].items():
                self.assertEqual(got.get(k), w, "his install's string for %s" % k)

    def test_the_generator_writes_the_shipped_block_where_the_install_is(self):
        code, say = CBDB.check()
        if code == CBDB.SKIP:
            self.skipTest("UNMEASURED here, not passed: " + say)
        self.assertEqual(code, 0, say)


RED_PROOF = [
    {
        "why": "#174 v-B3 - a hand edit of the shipped block moves Chaotic's level requirement",
        "file": "bible.html",
        "find": "[\"p700\",\"p\",\"Chaotic\",50,null,42,1,125,",
        "replace": "[\"p700\",\"p\",\"Chaotic\",50,null,1,1,125,",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - a rare word his install names (monsters.json GhoulRI \"Ghoul\") is back to an unnamed key",
        "file": "bible.html",
        "find": "[\"Ghoul\",[\"armo\",\"weap\",\"misc\"],[],1]",
        "replace": "[\"GhoulRI\",[\"armo\",\"weap\",\"misc\"],[],0]",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - a hand edit puts of Magic Arrow's charges back as the table's negative numbers",
        "file": "bible.html",
        "find": "[\"s458\",\"s\",\"of Magic Arrow\",12,null,11,1,44,-1,[\"miss\",\"abow\"],[],[[510,[],2,\"charged\"]],1,[0,1]]",
        "replace": "[\"s458\",\"s\",\"of Magic Arrow\",12,null,11,1,44,-1,[\"miss\",\"abow\"],[],[[510,[[-10,-10,\"m1\"],[-30,-30,\"m1\"]],0,\"charged\"]],1,[0,1]]",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - the generator asks only the item string tables for a rare word (six left unnamed)",
        "file": "char_builder_db.py",
        "find": "        for src in (self.NA or {}, self.S, self.OS or {}):\n",
        "replace": "        for src in (self.NA or {}, self.S):\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - the generator prints a charged skill's negative table values as its level and charges",
        "file": "char_builder_db.py",
        "find": "                if _int(lo) < 0 or _int(hi) < 0:\n",
        "replace": "                if False:\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - the generator drops an affix's class level requirement",
        "file": "char_builder_db.py",
        "find": "        return [ci, _int(r.get(\"classlevelreq\"))] if ci >= 0 else None\n",
        "replace": "        return None\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - the generator drops a base's magic lvl (a Diadem's affix level is its item level again)",
        "file": "char_builder_db.py",
        "find": "                           _int(r.get(\"magic lvl\"))]\n",
        "replace": "                           0]\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - the generator writes the game's non-spawnable affix rows too",
        "file": "char_builder_db.py",
        "find": "                if r.get(\"spawnable\") != \"1\" or not (r.get(\"Name\") or \"\").strip():\n",
        "replace": "                if not (r.get(\"Name\") or \"\").strip():\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - the generator inherits the quality flags, so a Grand Charm could be rare",
        "file": "char_builder_db.py",
        "find": "            rare = [\"rare\"] if own.get(\"Rare\") == \"1\" else []\n",
        "replace": "            rare = [\"rare\"] if self.walk(t, \"Rare\") == \"1\" else []\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - the generator drops an affix's maxlevel",
        "file": "char_builder_db.py",
        "find": "                           _int(mx) if mx else None, _int(r.get(\"levelreq\")), 1 if r.get(\"rare\") == \"1\" else 0,\n",
        "replace": "                           None, _int(r.get(\"levelreq\")), 1 if r.get(\"rare\") == \"1\" else 0,\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
