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
FIX ROUND (the #174 v-B4 review, four defects, each reproduced before it was fixed):
  · ONE FILLED SOCKET ON A PLAIN BASE: the joined list was used only for two sources, and a plain base has no lines of
    its own - a Shako with one Um printed no resist line while STATS counted it (+15), a Crowbill with one Hel kept 94 / 70
    and no "Requirements -20%", a Monarch with one Um lost "All Resistances +22". The joined list is now always the list.
  · THE GAME'S STAT GROUPS (itemstatcost dgrp): the group's one line only when every member is on the item and all are
    equal, else each member in its own words - Duress printed "Cold Resist +30%" beside "All Resistances +15" (the page's
    own RUNEWORD_TIP, the game's text: Cold +45%, Lightning / Fire / Poison +15%), Rift typed 7 "+7 to all Attributes"
    beside "+10 to Dexterity", a Monarch holding Ral Ort Tal Thul four "+35%" where the game prints one line.
  · ONE ORDER: a lone Death's Web kept the table's order (Life after each Kill, then Mana) and flipped when a Tir was
    socketed; the game has one stat list, so every item takes the tie rule (Grief, measured: Mana first).
  · POISON FROM TWO SOURCES: Venom on an Axe printed "+213 ... over 7 seconds" and its Tal's "+75 ... over 5 seconds"
    apart; the game prints ONE line, its number the game's code over per-frame values no line carries - said UNKNOWN,
    naming both sources, never two lines and never a guessed sum.
⚠ WHAT THIS LAW CANNOT SEE: pixels - the tooltip was looked at on real pixels (headless Chrome, 2000x1300) when built.
RED_PROOF below: the requirement step, the merge, the order (and its tie rule), the speed rule (its bands and EIAS), the
range form, the rune string, the charm line, the durability rule; and the fix round's four: the join for one socket,
the stat groups (off, equality ignored, four equal members never collapsed), one order for every item, the poison line.
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
import test_the_character_builder_is_joined_to_the_engine_and_the_mule_window as J  # noqa: E402  its picker + STATS

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

    # ── the fix round (the #174 v-B4 review) ────────────────────────────────────────────────────────────────────────
    def test_one_filled_socket_on_a_plain_base_joins_the_tooltip_and_agrees_with_stats(self):
        """A plain base has no lines of its own, so ONE rune was one source and the joined list was thrown away."""
        out = _run(r"""
          function rune(n){ var h = null; Object.keys(d.rwRunes).forEach(function(c){ if (!h && d.rwRunes[c][1] === n + ' Rune') h = c; }); return h; }
          function plain(bn, socks, slot, n){ var it = window._cbItem('b:' + baseCode(bn)), e = window._cbEntryFor(it);
            e.sockets = n || socks.length; e.socketed = socks;
            return rows(window.d2Tip(window._cbTipEntry(e, it, 99, slot, 'Sorceress'))).filter(function(r){ return r[0] !== 'd2t-note'; }).map(function(r){ return r[1]; }); }
          function word(code, sc){ return d.rwRunes[code][sc].map(function(l){ return window._cbLineHtml(l, {}, 99, 'tip'); }); }
          var um = rune('Um'), hel = rune('Hel');
          OUT.shako = plain('Shako', [um], 'head'); OUT.umHelm = word(um, 5);
          OUT.crow = plain('Crowbill', [hel], 'rarm'); OUT.helWeapon = word(hel, 4);
          OUT.crowReq = d.b[baseCode('Crowbill')].slice(6, 8); OUT.helPct = d.rwRunes[hel][4][0][1][0][0];
          OUT.mon = plain('Monarch', [um], 'larm', 4); OUT.umShield = word(um, 6);
          OUT.jewel = plain('Crowbill', ['b:' + baseCode('Jewel'), hel], 'rarm');
        """)
        self.assertEqual(len(out["umHelm"]), 1)
        self.assertIn(out["umHelm"][0], out["shako"], "a Shako with ONE Um must print the Um's helm line: %s" % out["shako"])
        self.assertIn(out["umShield"][0], out["mon"], "a Monarch with ONE Um must print the Um's shield line: %s" % out["mon"])
        rs, rd = out["crowReq"]
        pct = out["helPct"]
        want = ["Required Dexterity: %d" % (rd + int(rd * pct / 100.0)), "Required Strength: %d" % (rs + int(rs * pct / 100.0))]
        self.assertEqual(want, ["Required Dexterity: 56", "Required Strength: 76"], "the Crowbill's own requirement step")
        for c in (out["crow"], out["jewel"]):
            self.assertEqual([t for t in c if t.startswith("Required ") and "Level" not in t], want,
                             "ONE Hel in a plain Crowbill must lower its requirements: %s" % c)
            self.assertIn(out["helWeapon"][0], c, "the Hel's own line")
        self.assertTrue([t for t in out["jewel"] if "a magic Jewel" in t], "the magic jewel is still said UNKNOWN")
        # driven through the builder's own picker: the tooltip and the STATS sheet read the same socket
        ui = J._run(r"""
          mk('Sorceress', 90);
          var d = window._cbDb(), code = null; Object.keys(d.b).forEach(function(c){ if (!code && d.b[c][0] === 'Shako' && d.b[c][20]) code = c; });
          var um = null; Object.keys(d.rwRunes).forEach(function(c){ if (!um && d.rwRunes[c][1] === 'Um Rune') um = c; });
          window._cbOpenPick('slot', 'head'); window._cbChoose('b:' + code); window._cbQuality('b');
          window._cbEdit('sockets', '1'); window._cbSocket(0, um); window._cbClosePick();
          OUT.tip = tipOf('head').lines; OUT.fire = rowOf(eng(), 'res-fire');
          OUT.word = window._cbLineHtml(d.rwRunes[um][5][0], {}, 90, 'tip'); OUT.v = d.rwRunes[um][5][0][1][0][0];
        """)
        self.assertEqual(ui["tip"], [ui["word"]], "the picked Shako + Um: the tooltip must print the Um's line")
        self.assertIn("Shako (Um Rune) +%d" % ui["v"], ui["fire"][2], "STATS counts the same Um: %s" % ui["fire"])

    def test_a_stat_group_prints_as_the_game_prints_it(self):
        """itemstatcost dgrp: the group's one line only when every member is on the item and all are equal."""
        src = CB._src()
        m = re.search(r"^const RUNEWORD_TIP = (\{.*\});\s*$", src, re.M)
        self.assertIsNotNone(m, "the page's RUNEWORD_TIP is gone")
        tipd = {}
        for n in ("Duress", "Ancients' Pledge"):
            k = m.group(1).find(json.dumps(n) + ":{l:")
            self.assertGreater(k, 0, "RUNEWORD_TIP has no %s" % n)
            a = m.group(1).index("[", k)
            tipd[n] = json.JSONDecoder().raw_decode(m.group(1), a)[0]
        out = _run(r"""
          function rune(n){ var h = null; Object.keys(d.rwRunes).forEach(function(c){ if (!h && d.rwRunes[c][1] === n + ' Rune') h = c; }); return h; }
          function plain(bn, socks, slot){ var it = window._cbItem('b:' + baseCode(bn)), e = window._cbEntryFor(it);
            e.sockets = socks.length; e.socketed = socks;
            return rows(window.d2Tip(window._cbTipEntry(e, it, 99, slot, 'Sorceress'))).map(function(r){ return r[1]; }); }
          OUT.duress = tip('Duress', 'Ancient Armor', { slot: 'tors' });
          OUT.ap = tip("Ancients' Pledge", 'Gothic Shield', { slot: 'larm' });
          var four = ['Ral', 'Ort', 'Tal', 'Thul'].map(rune);
          OUT.mon = plain('Monarch', four, 'larm');
          OUT.monV = four.map(function(c){ return d.rwRunes[c][6][0][1][0][0]; });
          var rift = d.byName['rift'], ak = null;
          rift[6].forEach(function(l){ if (d.T[l[0]] === '{+0} to all Attributes') ak = l[1][0]; });
          OUT.ak = ak; var ro = {}; if (ak) ro[ak[2]] = ak[0];
          OUT.rift = tip('Rift', 'Halberd', { rolls: ro });
          OUT.koDex = d.rwRunes[rune('Ko')][4][0][1][0][0];
          OUT.lh = tip('Lionheart', 'Ancient Armor', { slot: 'tors' });
          OUT.anni = tip('Annihilus', null, { slot: 'inv' });
        """)
        res = re.compile(r"^(Fire|Cold|Lightning|Poison) Resist ([+-]\d+)%$")
        for key, n in (("duress", "Duress"), ("ap", "Ancients' Pledge")):
            ours = [t for c, t in out[key] if res.match(t)]
            self.assertFalse([t for c, t in out[key] if t.startswith("All Resistances")],
                             "%s: a group line beside its members: %s" % (n, out[key]))
            game = dict(res.match(t).groups() for t in tipd[n] if res.match(t))
            self.assertEqual(len(game), 4, "RUNEWORD_TIP's %s lost its four resist lines" % n)
            self.assertEqual(dict(res.match(t).groups() for t in ours), game, "%s: ours %s, the game %s" % (n, ours, tipd[n]))
            self.assertEqual([res.match(t).group(1) for t in ours], ["Cold", "Lightning", "Fire", "Poison"],
                             "%s: the members in descpriority order (40, 38, 36, 34)" % n)
        v = out["monV"]
        self.assertEqual(len(set(v)), 1, "Ral / Ort / Tal / Thul give one shield value each: %s" % v)
        self.assertEqual([t for t in out["mon"] if "Resist" in t], ["All Resistances +%d" % v[0]],
                         "four equal members are the group's ONE line: %s" % out["mon"])
        self.assertIsNotNone(out["ak"], "Rift carries no all-Attributes line")
        a, dx = out["ak"][0], out["koDex"]
        self.assertEqual([t for c, t in out["rift"] if re.search(r"to (all Attributes|Strength|Dexterity|Vitality|Energy)$", t)],
                         ["+%d to Strength" % a, "+%d to Dexterity" % (a + dx), "+%d to Vitality" % a, "+%d to Energy" % a],
                         "Rift typed at %d with Ko's +%d Dexterity: four members apart, in descpriority order" % (a, dx))
        self.assertFalse([t for c, t in out["lh"] if t.endswith("to all Attributes")], "Lionheart's members are unequal")
        self.assertIn("+10-20 to all Attributes", [t for c, t in out["anni"]], "ONE roll feeding all four stays the group")

    def test_one_order_for_every_item_socketed_or_not(self):
        """The game has one stat list: a lone Death's Web and one holding a Tir put Mana after each Kill first, as the
        measured Grief does - and every unique / set item with a descpriority tie follows the one tie rule."""
        out = _run(r"""
          var kill = function(r){ return /after each Kill$/.test(r[1]); };
          OUT.dw = tip("Death's Web", null, { cls: 'Necromancer' }).filter(kill).map(function(r){ return r[1]; });
          var x = entry("Death's Web", null, { cls: 'Necromancer' }), tir = null;
          Object.keys(d.rwRunes).forEach(function(c){ if (!tir && d.rwRunes[c][1] === 'Tir Rune') tir = c; });
          x.e.sockets = 1; x.e.socketed = [tir];
          OUT.dwSock = rows(window.d2Tip(window._cbTipEntry(x.e, x.it, 99, 'rarm', 'Necromancer'))).filter(kill).map(function(r){ return r[1]; });
          OUT.grief = tip('Grief', 'Phase Blade').filter(kill).map(function(r){ return r[1]; });
          /* every unique / set item: its own lines (text, sort key) in the table's order, and its tooltip's rows */
          OUT.all = [];
          d.it.forEach(function(it){
            if (it[2] !== 'u' && it[2] !== 's') return;
            var ls = (it[6] || []).filter(function(l){ return !l[2]; });
            OUT.all.push({ n: it[1], own: ls.map(function(l){ return [window._cbLineHtml(l, {}, 99, 'tip'), d.TK[l[0]]]; }),
                           rows: rows(window.d2Tip(window._cbTipEntry(window._cbEntryFor(it), it, 99, 'inv', 'Sorceress'))).map(function(r){ return r[1]; }) });
          });
        """)
        self.assertEqual(len(out["grief"]), 2)
        self.assertIn("Mana", out["grief"][0], "the measured Grief: Mana after each Kill first")
        self.assertEqual(len(out["dw"]), 2)
        self.assertIn("Mana", out["dw"][0], "a lone Death's Web: Mana after each Kill first, as the game's one list: %s" % out["dw"])
        self.assertIn("Mana", out["dwSock"][0], "Death's Web with a Tir: the same order: %s" % out["dwSock"])
        # the tie rule over every tie the tables hold where it differs from the table's order
        flips, bad = 0, []
        for x in out["all"]:
            own = x["own"]
            for i in range(len(own)):
                for j in range(i + 1, len(own)):
                    (ta, ka), (tb, kb) = own[i], own[j]
                    if ka[0] != kb[0] or (ka[1], ka[2]) >= (kb[1], kb[2]) or ta == tb:
                        continue
                    if ta not in x["rows"] or tb not in x["rows"]:
                        continue
                    flips += 1
                    if x["rows"].index(tb) > x["rows"].index(ta):
                        bad.append("%s: %r (descfunc %d, stat %d) must print before %r (descfunc %d, stat %d)"
                                   % (x["n"], tb, kb[1], kb[2], ta, ka[1], ka[2]))
        self.assertGreater(flips, 0, "no unique or set item has a tie the table orders the other way - the case measures nothing")
        self.assertEqual(bad, [], "\n  ".join(bad[:10]))

    def test_poison_from_two_sources_is_one_line_said_unknown(self):
        out = _run(r"""
          var tal = null; Object.keys(d.rwRunes).forEach(function(c){ if (!tal && d.rwRunes[c][1] === 'Tal Rune') tal = c; });
          var sid = d.tip.st.poisonmindam, v = d.byName['venom'];
          OUT.own = v[6].filter(function(l){ return d.TK[l[0]][2] === sid; }).map(function(l){ return window._cbLineHtml(l, {}, 99, 'tip'); });
          OUT.tal = d.rwRunes[tal][4].filter(function(l){ return d.TK[l[0]][2] === sid; }).map(function(l){ return window._cbLineHtml(l, {}, 99, 'tip'); });
          OUT.venom = tip('Venom', 'Axe');
          OUT.insight = tip('Insight', 'Hydra Bow');
        """)
        self.assertEqual((len(out["own"]), len(out["tal"])), (1, 1), "Venom's and Tal's own poison lines")
        pois = [(c, t) for c, t in out["venom"] if "poison damage" in t.lower()]
        self.assertEqual(len(pois), 1, "Venom must print ONE poison line: %s" % pois)
        c, t = pois[0]
        self.assertEqual(c, "d2t-unk", "the combined number is the game's code - said UNKNOWN")
        self.assertTrue(t.startswith("Poison damage: UNKNOWN"), t)
        for part in out["own"] + out["tal"]:
            self.assertIn(part, t, "the UNKNOWN line names what it combines")
        self.assertIn(out["tal"][0], [t for c, t in out["insight"]], "ONE poison source keeps its own line")


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
        "find": "    if (J.s > 0) L = _cbTipMerge(L, rolls);\n",
        "replace": "",
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
    {
        "why": "#174 v-B4 fix round - the joined list is used only for two sources again (a Shako with ONE Um prints no Um)",
        "file": "bible.html",
        "find": "    var J = _cbTipJoin(it, e, slot), L = _cbTipGroups(_cbTipPoison(J.lines, rolls), rolls);\n",
        "replace": "    var J = _cbTipJoin(it, e, slot), L = _cbTipGroups(_cbTipPoison(J.n > 1 ? J.lines : (it[6] || []).slice(), rolls), rolls);\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 fix round - the stat groups are off (Duress: 'Cold Resist +30%' beside 'All Resistances +15')",
        "file": "bible.html",
        "find": "      if (all.length < 2 || (!gi.length && have < ms.length)) return;\n",
        "replace": "      return;\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 fix round - a group collapses without its members being equal (Duress reads one 'All Resistances')",
        "file": "bible.html",
        "find": "      var eq = on.length === ms.length && on.every(function(v){ return v.sig === on[0].sig; });\n",
        "replace": "      var eq = on.length === ms.length;\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 fix round - four equal members never become the group's line (a Monarch with Ral Ort Tal Thul: four +35%)",
        "file": "bible.html",
        "find": "(!gi.length && have < ms.length)) return;",
        "replace": "!gi.length) return;",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 fix round - an item with no filled socket keeps the table's order (a lone Death's Web: Life before Mana)",
        "file": "bible.html",
        "find": "    it = it.slice(); it[6] = _cbTipOrder(L);\n",
        "replace": "    it = it.slice(); it[6] = J.s > 0 ? _cbTipOrder(L) : L;\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 fix round - poison from two sources prints two lines again (Venom + its Tal)",
        "file": "bible.html",
        "find": "    if (at.length < 2) return lines;\n    var c = lines[at[0]].slice();\n",
        "replace": "    return lines;\n    var c = lines[at[0]].slice();\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if CB.NODE is None:
        sys.stderr.write("⚪ SKIP — node is not on this machine, so the tooltip was not driven. UNMEASURED, declared (77).\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
