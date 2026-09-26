# -*- coding: utf-8 -*-
"""#174 v-B4 — THE TOOLTIP IS THE GAME'S TOOLTIP: THEIR LINES, FROM OUR TABLES, IN THE GAME'S ORDER.

His words (2026-09-26): "now for a warspike ranges and dmg is different ... relevant and accurate obviously and NOT
FABRICATED but we already have the data". Their planner's in-game tooltip was MEASURED (headless Chrome, real mouse) on
every base row of six runewords for a level 99 Sorceress, and its TEXT - the words and numbers only - is committed beside
this law (tv/the_tooltip_oracle.json: Breath of the Dying on 40 bases incl. the 7 of the base_dump, Grief 30, Spirit 24,
Insight 49, Call to Arms 48, Heart of the Oak 12 = 203 rows). Ours at v3514 on Breath of the Dying / Crowbill printed
Required Strength 94 / Dexterity 70 (Hel's -20% never applied - it sits in a socket), no rune string, no "Axe Class -
Very Fast Attack Speed", +125% and +75% Damage to Undead apart, four "+30 to <Attribute>", nothing in the game's order.

This law drives the SHIPPED tooltip - window._cbTipEntry + window.d2Tip, the ⟦CHARACTER BUILDER JS⟧ block and the
generated ⟦CB_DB⟧ block (tv/char_builder_db.py from his install), cut from bible.html and run in node over the builder
law's own DOM stand-in (tv/test_the_character_builder_is_their_builder.py's harness, imported, never re-typed) - on the
same runeword and base, and requires the line list to EQUAL theirs after only the en dash -> "-" and whitespace:
  · damage: the base's 1H / 2H columns with Enhanced Damage lo..hi floored, "(63-70) to (153-170)" (Ohm's +50% and Sol's
    +9 to Minimum Damage reach it); Durability (the base's, none on a bow or when Indestructible); requirements after
    item_req_percent: base + trunc(base x pct / 100) (94 -> 76, 70 -> 56, 133 -> 107, 54 -> 44), a zero one printed not;
    Required Level the highest of the base and the runes; the rune string 'VexHelElEldZodEth' (RuneQuote + r26L ...)
  · "<Class> Class - <Speed> Attack Speed": the game's strings; the speed word from the character's Attack1 frames
    (animdata.d2), the base's speed and the item's own IAS by the game's formula, and the frame bands measured here -
    10-13 Very Fast, 14-15 Fast, 16-19 Normal, 20-22 Slow - on every row that prints one
  · every property line of the runeword AND its runes merged where the game merges them (+125% + +75% = +200% Damage to
    Undead; str/dex/vit/enr as "+30 to all Attributes") and ordered by descpriority, ties by descfunc then stat id
  · their range form: a %+d range bare ("30-40% Increased Attack Speed"), a line standing for several stats signed ("All
    Resistances +30-40", "+350-400% Enhanced Damage")
THREE DIFFERENCES ARE DECLARED, each asserted exactly where its rule applies and nowhere else:
  (a) SWORD - theirs prints no class line on a sword (the table's key is spelled "WeaponDescSword - %s"; theirs asks for
      "WeaponDescSword" and finds nothing): ours prints the game's "Sword Class - ..." there, and only there.
  (b) BLUNT - theirs ends a blunt base with no undead stat of its own on "+50% Damage to Undead": that NUMBER is the game's
      code, no table holds it, so ours says "Damage to Undead: UNKNOWN ..." in the same place, never a typed 50.
  (c) AN UNTYPED ROLLED ATTACK SPEED whose two ends fall in two bands (Grief 30-40%): theirs prints the top roll's word,
      ours both, "(Fast-Very Fast) Attack Speed" - and with the roll typed at its top ours is theirs exactly.
Plus: Annihilus prints "Keep in Inventory to Gain Bonus" under its base and ONE "+10-20 to all Attributes" (one roll, p2);
a unique (Windforce) and a set item (Tal Rasha's Guardianship) print exactly their own lines, in the table's order, plus
only the new rows; a requirement is red only when the build is KNOWN to lack it; the speed word is UNKNOWN - never a
guess - for frames outside the measured bands, a class not set, a Barbarian's one-or-two-hander, a wand's class word.
⚠ WHAT THIS LAW CANNOT SEE: pixels - the tooltip was looked at on real pixels (headless Chrome, 2000x1300) when built.
RED_PROOF below: the requirement step, the merge, the order (and its tie rule), the speed rule (its bands and EIAS), the
range form, the rune string, the charm line, the durability rule.
"""
import io
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

import test_the_character_builder_is_their_builder as CB  # noqa: E402  the builder's own harness

ORACLE = os.path.join(HERE, "the_tooltip_oracle.json")
#: base_dump's seven, the rows the brief measured first - they must be theirs with NO declared difference
SEVEN = ("Crowbill", "War Spike", "Berserker Axe", "Giant Axe", "Military Pick", "Hydra Bow", "Long War Bow")


def _oracle():
    with io.open(ORACLE, encoding="utf-8") as f:
        return json.load(f)


def _rows(fx):
    """[(runeword, base, their lines)] - head + the runeword's props, or the base's own props"""
    out = []
    for rw, v in fx["runewords"].items():
        for base, e in v["bases"].items():
            out.append((rw, base, list(e["head"]) + list(e.get("props") or v["props"])))
    return out


def _norm(s):
    return re.sub(r"\s+", " ", s.replace(u"\u2013", "-")).strip()


#: helpers every case shares: the tooltip of a named item on a named base, as [class, text] rows
HELP = r"""
window.openCharBuilder();
var d = window._cbDb();
function baseCode(n){ var h = null; Object.keys(d.b).forEach(function(c){ if (!h && d.b[c][0] === n && d.b[c][20]) h = c; }); return h; }
function rows(h){ var out = [], re = /<div class="([^"]+)"[^>]*>([\s\S]*?)<\/div>/g, m;
  while ((m = re.exec(h))) out.push([m[1], m[2].replace(/<[^>]+>/g, '').replace(/&#39;/g, "'").replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>')]);
  return out; }
function entry(name, base, o){
  o = o || {}; var it = d.byName[name.toLowerCase()]; if (!it) return null;
  var e = window._cbEntryFor(it); if (base){ var bc = baseCode(base); if (!bc) return null; e.base = bc; }
  if (o.rolls) e.rolls = o.rolls;
  var t = window._cbTipEntry(e, it, o.lvl == null ? 99 : o.lvl, o.slot || 'rarm', o.cls === undefined ? 'Sorceress' : o.cls);
  if (o.attrs) t.attrs = o.attrs;
  return { it: it, e: e, t: t };
}
function tip(name, base, o){ var x = entry(name, base, o); return x ? rows(window.d2Tip(x.t)) : null; }
/* the roll key and the top of the item's own Increased Attack Speed line, when it is a range */
function iasRoll(name){ var it = d.byName[name.toLowerCase()], sid = d.tip.st.item_fasterattackrate, hit = null;
  (it[6] || []).forEach(function(l){ var r = l[1] && l[1][0]; if (!hit && d.TK[l[0]][2] === sid && r && r[0] !== r[1]) hit = [r[2], Math.max(r[0], r[1])]; });
  return hit; }
"""


def _run(body):
    return CB._run(HELP + body)


@unittest.skipIf(CB.NODE is None, "node is not on this machine")
class TheTooltipIsTheGamesTooltip(unittest.TestCase):

    def test_the_fixture_is_their_text_and_holds_what_the_brief_measured(self):
        fx = _oracle()
        rows = _rows(fx)
        self.assertGreaterEqual(len(rows), 7 + 2, "the oracle fixture lost its rows: %d" % len(rows))
        rw = fx["runewords"]
        for b in SEVEN:
            self.assertIn(b, rw["Breath of the Dying"]["bases"], "the measured Breath of the Dying base %s is gone" % b)
        self.assertEqual(list(fx["measured7"]), list(SEVEN))
        self.assertIn("Grief", rw)
        self.assertIn("Spirit", rw)
        for n in ("Grief", "Spirit"):
            self.assertIn("Crystal Sword", rw[n]["bases"], "%s on a sword is not in the fixture" % n)
        blob = json.dumps(fx, ensure_ascii=False)
        for bad in ("<", "http", "/Users", "maxroll", "class=", "function"):
            self.assertNotIn(bad, blob, "the fixture must be their tooltip TEXT only - it carries %r" % bad)
        for r, b, lines in rows:
            self.assertEqual(lines[0], r, "%s / %s: the first line is not the runeword's name" % (r, b))
            self.assertEqual(lines[1], b, "%s / %s: the second line is not the base" % (r, b))
            self.assertTrue(all(isinstance(x, str) and x.strip() for x in lines))

    def test_every_oracle_row_is_the_shipped_tooltip(self):
        fx = _oracle()
        rows = _rows(fx)
        out = _run(r"""
          var CASES = %s, B = CASES.map(function(c){ return c[1]; });
          OUT.r = CASES.map(function(c){
            var x = entry(c[0], c[1]);
            if (!x) return { err: 'no item or base ' + c[0] + ' / ' + c[1] };
            var bt = d.b[x.e.base][1], anc = d.anc[bt] || {};
            return { rows: rows(window.d2Tip(x.t)), sword: !!anc.swor, blunt: !!anc.blun };
          });
        """ % json.dumps([[r, b] for r, b, _ in rows]))
        bad, kinds, equal = [], {"sword": 0, "blunt": 0, "speed": 0}, 0
        for (rw, base, theirs), got in zip(rows, out["r"]):
            if "err" in got:
                bad.append(got["err"])
                continue
            notes = [t for c, t in got["rows"] if c == "d2t-note"]
            for n in notes:
                if not n.startswith("strength / dexterity: UNKNOWN until the character has attributes"):
                    bad.append("%s / %s: an unexpected note %r" % (rw, base, n))
            ours = [(c, _norm(t)) for c, t in got["rows"] if c != "d2t-note"]
            th = [_norm(x) for x in theirs]
            ot = [t for _, t in ours]
            if ot == th:
                equal += 1
                continue
            # (a) SWORD: ours has the game's sword class line where theirs has none - on a sword, and only there
            if got["sword"]:
                k = [i for i, t in enumerate(ot) if t.startswith("Sword Class - ")]
                if len(k) != 1 or [t for t in th if " Class - " in t]:
                    bad.append("%s / %s: a sword must print exactly one 'Sword Class - ' line (theirs none): %s" % (rw, base, k))
                    continue
                if not (ot[k[0] - 1].startswith("Required Level: ") and (re.search(r" Attack Speed$", ot[k[0]])
                                                                         or "attack speed UNKNOWN" in ot[k[0]])):
                    bad.append("%s / %s: the sword's class line is out of place or not the game's form: %r" % (rw, base, ot[k[0]]))
                    continue
                del ot[k[0]]
                del ours[k[0]]
                kinds["sword"] += 1
            # (b) BLUNT: theirs "+50% Damage to Undead" before Socketed; ours the UNKNOWN in the same place
            if got["blunt"] and "+50% Damage to Undead" in th:
                i = th.index("+50% Damage to Undead")
                if i >= len(ours) or ours[i][0] != "d2t-unk" or not ours[i][1].startswith("Damage to Undead: UNKNOWN"):
                    bad.append("%s / %s: the blunt bonus is not said UNKNOWN in its place: %r" % (rw, base, ours[i:i + 1]))
                    continue
                if any("Damage to Undead" in t and not t.startswith("Damage to Undead: UNKNOWN") for t in ot):
                    bad.append("%s / %s: a blunt base with its own undead stat must not say the bonus" % (rw, base))
                    continue
                ot[i] = th[i]
                kinds["blunt"] += 1
            # (c) an untyped rolled IAS whose ends fall in two bands: ours "(A-B) Attack Speed", theirs B (the top roll)
            for i, (a, b) in enumerate(zip(th, ot)):
                m = re.match(r"^(\w+ Class - )\((.+)-(.+)\) Attack Speed$", b)
                if a != b and m and a == m.group(1) + m.group(3) + " Attack Speed":
                    ot[i] = a
                    kinds["speed"] += 1
            if ot != th:
                bad.append("%s / %s:\n      theirs %s\n      ours   %s" % (rw, base, th, ot))
        self.assertEqual(bad, [], "\n  ".join(bad[:12]) + ("\n  ... %d rows in all" % len(bad) if len(bad) > 12 else ""))
        # the declared differences stayed where their rules put them (each one exercised, so none absorbs a defect
        # unseen), and most rows are theirs line for line with nothing declared at all
        self.assertGreater(equal, len(rows) // 2, "only %d of %d rows are theirs exactly" % (equal, len(rows)))
        for k in ("sword", "blunt", "speed"):
            self.assertGreater(kinds[k], 0, "the declared difference %r was never met - the fixture lost its rows" % k)

    def test_the_seven_measured_rows_are_theirs_with_nothing_declared(self):
        fx = _oracle()
        v = fx["runewords"]["Breath of the Dying"]
        out = _run(r"""
          OUT.r = %s.map(function(b){ return tip('Breath of the Dying', b); });
        """ % json.dumps(list(SEVEN)))
        for b, got in zip(SEVEN, out["r"]):
            e = v["bases"][b]
            theirs = [_norm(x) for x in list(e["head"]) + list(e.get("props") or v["props"])]
            self.assertEqual([_norm(t) for c, t in got if c != "d2t-note"], theirs, "Breath of the Dying on %s" % b)
        crow = dict((t, c) for c, t in out["r"][0])
        self.assertEqual(crow.get("Crowbill"), "d2t-g", "the base under a runeword is their grey")
        self.assertEqual(crow.get("'VexHelElEldZodEth'"), "d2t-r", "the rune string is the runeword's gold")

    def test_a_rolled_attack_speed_typed_at_its_top_is_their_word(self):
        fx = _oracle()
        g = fx["runewords"]["Grief"]
        bases = [b for b, e in g["bases"].items() if any(" Class - " in x for x in e["head"])]
        out = _run(r"""
          var k = iasRoll('Grief'), roll = {}; roll[k[0]] = k[1]; OUT.k = k;
          OUT.r = %s.map(function(b){ return [tip('Grief', b), tip('Grief', b, { rolls: roll })]; });
        """ % json.dumps(bases))
        self.assertEqual(out["k"][1], 40, "Grief's Increased Attack Speed tops at 40 (runes.txt swing3 30-40)")
        ranged = 0
        for b, (untyped, typed) in zip(bases, out["r"]):
            theirs = [x for x in g["bases"][b]["head"] if " Class - " in x][0]
            mine = [t for c, t in typed if " Class - " in t]
            self.assertEqual(mine, [theirs], "Grief on %s at 40%% IAS" % b)
            if [t for c, t in untyped if " Class - " in t] != [theirs]:
                ranged += 1
        self.assertGreater(ranged, 0, "no Grief base put its two ends in two bands - the case measures nothing")

    def test_requirements_are_red_only_when_the_build_is_known_to_lack_them(self):
        out = _run(r"""
          OUT.lack = tip('Breath of the Dying', 'Crowbill', { attrs: { str: 75, dex: 56 } });
          OUT.none = tip('Breath of the Dying', 'Crowbill');
          OUT.lvl = tip('Breath of the Dying', 'Crowbill', { lvl: 68 });
        """)
        lack = dict((t, c) for c, t in out["lack"])
        self.assertEqual(lack.get("Required Strength: 76"), "d2t-red", "strength 75 lacks 76: red")
        self.assertEqual(lack.get("Required Dexterity: 56"), "d2t-w", "dexterity 56 meets 56: never red")
        none = dict((t, c) for c, t in out["none"])
        self.assertEqual((none.get("Required Strength: 76"), none.get("Required Dexterity: 56")), ("d2t-w", "d2t-w"),
                         "a build with no attributes is never red on a guess")
        self.assertTrue(any(c == "d2t-note" for c, t in out["none"]), "the UNKNOWN attributes are not said")
        self.assertEqual(dict((t, c) for c, t in out["lvl"]).get("Required Level: 69"), "d2t-red")

    def test_annihilus_keeps_in_inventory_and_rolls_all_attributes_once(self):
        out = _run(r"""
          OUT.anni = tip('Annihilus', null, { slot: 'inv' });
          OUT.typed = tip('Annihilus', null, { slot: 'inv', rolls: { p2: 20 } });
          var it = d.byName['annihilus'];
          OUT.lines = it[6].map(function(l){ return [d.T[l[0]], l[1], l[3]]; });
        """)
        self.assertEqual([t for c, t in out["anni"]],
                         ["Annihilus", "Small Charm", "Keep in Inventory to Gain Bonus", "Required Level: 70",
                          "+1 to All Skills", "+10-20 to all Attributes", "All Resistances +10-20",
                          "5-10% to Experience Gained"])
        self.assertEqual(out["anni"][2][0], "d2t-w", "the charm line is the game's white")
        self.assertIn("+20 to all Attributes", [t for c, t in out["typed"]], "a typed p2 is one value for all four")
        allattr = [l for l in out["lines"] if l[0] == "{+0} to all Attributes"]
        self.assertEqual(len(allattr), 1, "Annihilus must carry ONE all-Attributes line: %s" % out["lines"])
        self.assertEqual(allattr[0][1], [[10, 20, "p2"]], "its one roll is uniqueitems.txt prop2, 10-20")
        self.assertFalse([l for l in out["lines"] if re.match(r"^\{\+0\} to (Strength|Dexterity|Vitality|Energy)$", l[0])])

    def test_a_unique_and_a_set_item_are_their_own_lines_plus_only_the_new_rows(self):
        out = _run(r"""
          var own = function(n){ return d.byName[n.toLowerCase()][6].filter(function(l){ return l[2] !== 3; }).map(function(l){ return window._cbLineHtml(l, {}, 99, 'tip'); }); };
          OUT.wf = tip('Windforce'); OUT.wfOwn = own('Windforce');
          OUT.tr = tip("Tal Rasha's Guardianship", null, { slot: 'tors' }); OUT.trOwn = own("Tal Rasha's Guardianship");
          var t = entry("Tal Rasha's Guardianship", null, { slot: 'tors' }).t; OUT.trSet = t.set.map(function(l){ return l.html; });
        """)
        wf = out["wf"]
        self.assertEqual([t for c, t in wf if c == "d2t-p"], out["wfOwn"], "Windforce's own lines, in the table's order")
        self.assertEqual([t for c, t in wf if c not in ("d2t-p", "d2t-note")],
                         ["Windforce", "Hydra Bow", "Two-Hand Damage: 35 to 547", "Required Dexterity: 167",
                          "Required Strength: 134", "Required Level: 73", "Bow Class - Fast Attack Speed"],
                         "a unique bow gains only its class line (a Hydra Bow has no durability)")
        tr = out["tr"]
        self.assertEqual([t for c, t in tr if c == "d2t-p"], out["trOwn"], "the set piece's own lines, in the table's order")
        head = [t for c, t in tr if c in ("d2t-s", "d2t-w")]
        self.assertEqual(head[:2], ["Tal Rasha's Guardianship", "Lacquered Plate"])
        self.assertIn("Durability: 55 of 55", head, "the new Durability row (armor.txt Lacquered Plate)")
        self.assertIn("Required Strength: 84", head, "208 + trunc(208 x -60 / 100) = 84")
        self.assertEqual(out["trSet"], ["+10% Faster Cast Rate (2 items)"], "the set bonus is unchanged")

    def test_the_speed_word_is_the_frames_band_or_unknown(self):
        out = _run(r"""
          OUT.fpa = [window._cbFpa(20, 256, 60, -10), window._cbFpa(20, 256, 60, 0), window._cbFpa(18, 256, 60, 10),
                     window._cbFpa(20, 256, 40, 10), window._cbFpa(18, 256, 0, 20)];
          OUT.keys = [9, 10, 13, 14, 15, 16, 19, 20, 22, 23].map(window._cbSpeedKey);
          OUT.noCls = tip('Breath of the Dying', 'Crowbill', { cls: null });
          OUT.barb = tip('Grief', 'Colossus Blade', { cls: 'Barbarian' });
          var wand = null; d.it.forEach(function(x){ if (!wand && x[2] === 'u' && d.b[x[3]] && d.b[x[3]][1] === 'wand') wand = x[1]; });
          OUT.wandName = wand; OUT.wand = tip(wand, null, { cls: 'Necromancer' });
        """)
        self.assertEqual(out["fpa"], [13, 14, 13, 16, 22], "the game's formula over Sorceress frames")
        self.assertEqual(out["keys"], [None, "WeaponAttackVeryFast", "WeaponAttackVeryFast", "WeaponAttackFast",
                                       "WeaponAttackFast", "WeaponAttackNormal", "WeaponAttackNormal",
                                       "WeaponAttackSlow", "WeaponAttackSlow", None],
                         "the measured bands, UNKNOWN outside 10-22")
        cl = [t for c, t in out["noCls"] if " Class - " in t]
        self.assertEqual(cl, ["Axe Class - attack speed UNKNOWN — the character's class is not set"])
        self.assertTrue([t for c, t in out["barb"] if t.startswith("Sword Class - attack speed UNKNOWN")],
                        "a Barbarian's one-or-two-handed sword must be UNKNOWN: %s" % out["barb"])
        self.assertTrue(out["wandName"], "no unique wand in the block")
        self.assertTrue([t for c, t in out["wand"] if c == "d2t-unk" and "class word" in t],
                        "a wand's class word is in no table - it must say so: %s" % out["wand"])


RED_PROOF = [
    {
        "why": "#174 v-B4 - the requirement percent is floored off the whole again (Crowbill with Hel reads 75, theirs 76)",
        "file": "bible.html",
        "find": "        var a = v + Math.trunc(v * ease[0] / 100), z = v + Math.trunc(v * ease[1] / 100);\n",
        "replace": "        var a = Math.floor(v * (100 + ease[0]) / 100), z = Math.floor(v * (100 + ease[1]) / 100);\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the runeword's and its runes' lines are no longer merged (+125% and +75% Damage to Undead apart)",
        "file": "bible.html",
        "find": "it[6] = _cbTipOrder(_cbTipMerge(J.lines, rolls)); }\n",
        "replace": "it[6] = _cbTipOrder(J.lines); }\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the joined lines keep the runeword-then-runes order, not the game's descpriority",
        "file": "bible.html",
        "find": "    rest.sort(function(a, b){ var x = _cbTk(a[0]), y = _cbTk(b[0]); return (y[0] - x[0]) || (y[1] - x[1]) || (y[2] - x[2]) || (a[1] - b[1]); });\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - a descpriority tie keeps the list's order (Grief's own life after each kill before Tir's mana)",
        "file": "bible.html",
        "find": "return (y[0] - x[0]) || (y[1] - x[1]) || (y[2] - x[2]) || (a[1] - b[1]); });",
        "replace": "return (y[0] - x[0]) || (a[1] - b[1]); });",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the speed bands drift by one frame (Berserker Axe's Fast reads Very Fast)",
        "file": "bible.html",
        "find": "  var CB_SPEED_BANDS = [[10, 13, 'WeaponAttackVeryFast'], [14, 15, 'WeaponAttackFast'], [16, 19, 'WeaponAttackNormal'], [20, 22, 'WeaponAttackSlow']];\n",
        "replace": "  var CB_SPEED_BANDS = [[10, 14, 'WeaponAttackVeryFast'], [15, 16, 'WeaponAttackFast'], [17, 19, 'WeaponAttackNormal'], [20, 22, 'WeaponAttackSlow']];\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the item's IAS is used raw, not the game's diminishing EIAS",
        "file": "bible.html",
        "find": "    var eias = ias > 0 ? Math.floor(120 * ias / (120 + ias)) : ias, sp",
        "replace": "    var eias = ias, sp",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - a %+d range keeps its sign in the tooltip again ('+30-40% Increased Attack Speed', theirs '30-40%')",
        "file": "bible.html",
        "find": "      if (mode === 'tip' && !v[2] && !_cbTipGroup(line)) return v[0] + '-' + v[1];\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - a runeword prints no rune string",
        "file": "bible.html",
        "find": "      out.runes = _cbUi('RuneQuote', \"'\") + it[7].runes.map(",
        "replace": "      out.runesX = _cbUi('RuneQuote', \"'\") + it[7].runes.map(",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - a charm loses 'Keep in Inventory to Gain Bonus'",
        "file": "bible.html",
        "find": "    if (anc.char) out.charm = _cbUi('Charmdes', 'Keep in Inventory to Gain Bonus');\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - an Indestructible item prints the base's durability anyway",
        "file": "bible.html",
        "find": "      if ((b[25] | 0) > 0 && !indes) out.dur = (e.eth || it[8]) ? null : [b[25], b[25]];\n",
        "replace": "      if ((b[25] | 0) > 0) out.dur = (e.eth || it[8]) ? null : [b[25], b[25]];\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if CB.NODE is None:
        sys.stderr.write("⚪ SKIP — node is not on this machine, so the tooltip was not driven. UNMEASURED, declared (77).\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
