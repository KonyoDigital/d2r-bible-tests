# -*- coding: utf-8 -*-
"""#174 v-B3 — THE EDIT TAB BUILDS A MAGIC, RARE, SUPERIOR OR LOW ITEM THEIR WAY, OVER THE GAME'S OWN AFFIX TABLES.

His order (2026-09-26 ~02:30): "more items also i see need to be added to the itembase.. literally check and see how
its structured there ... charms too.. mods and buffs ranges of them all with manual additions to add so they sync to
them item within with those same buffs that were manually input there". Their flow, MEASURED (SPEC_174 §10, planner
PNGs 32 / 40-43 / 50-51): pick a BASE -> a Quality tab (Rare · Magic · Superior · Normal · Low, only what the base can
be) -> Edit with Item level · Quality ▾ · Name (a rare's two words + a dice) · Base ▾ · Defense · Sockets · Ethereal,
then REGULAR MODS and ADD MOD, a searchable list grouped PREFIXES / SUFFIXES with every option's range; a charm goes
straight to Edit as magic; a picked mod renames the item ("Grand Charm" -> "Chaotic Grand Charm").

This law drives the SHIPPED modal — the ⟦CHARACTER BUILDER JS⟧ block and the generated ⟦CB_DB⟧ block (af / rn / qm,
tv/char_builder_db.py from his install), cut from bible.html and run in node over the same DOM stand-in the builder's
own law uses (tv/test_the_character_builder_is_their_builder.py's harness, imported, never re-typed):

  · QUALITY IS THE DATA'S. A Diadem (itemtypes.txt circ: Rare 1, Magic blank) opens Quality with Rare · Magic ·
    Superior · Normal · Low, Edit greyed until one is chosen; a Ring (Magic 1, Rare 1) offers Rare · Magic only; a Grand
    Charm (lcha: Magic 1, Rare blank — its ancestor `misc` says Rare 1, which is NOT the charm's) goes straight to Edit
    as magic; a unique never sees the tab.
  · ADD MOD IS THE GAME'S RULE, EACH CLAUSE SEEN: by TYPE (a Grand Charm lists Chaotic, lcha, and never Sturdy, armo),
    by LEVEL (Chaotic is level 50: absent at item level 49, present at 50; Crimson p665 has maxlevel 4: present at 3,
    absent at 99), by GROUP (on a RARE Diadem, where three prefixes are allowed so the magic one-prefix cap cannot
    hide the rule: after Devil's, group 125, Arch-Devil's is gone and refused while Jagged, group 105, stays), by CLASS (an Eagle Orb is the Sorceress's: Expert's, tied to the Barbarian, is not offered; on a Crystal
    Sword it is), by the RARE flag (a rare Diadem never lists Bahamut's, rare 0; a magic one does), by the AUTOMOD group
    (an Eagle Orb's auto prefix 303 lists "of the Jackal" a9; a Diadem, auto prefix 0, lists no automod), and by the
    quality's LIMITS (magic: one prefix, then PREFIXES is full; rare: three; a rare jewel: four in all).
  · A ROLL OUTSIDE ITS RANGE IS REFUSED, the range shown: "of Vita" rolls 36-40 (magicsuffix.txt hp); 41 is not
    saved, 38 is saved EXACT under the mod's own key (m1) on the stored entry.
  · A PICKED MOD REACHES THE STORE AND THE TOOLTIP: d2r_charBuilds ...inv[i] = {q: 'm', affixes: [{id: 'p700',
    rolls: {}}, {id: 's338', rolls: {m1: 38}}]}; the in-game tooltip (window.d2Tip) prints "Chaotic Grand Charm of
    Vita" in the magic class with "+1 to Chaos Skills (Warlock Only)" and "+38 to Life"; the Edit tab's name is the
    same words in the same colour; a rare is its two words over its base.
  · IT REACHES THE SHEET: the builder hands the engine the picked affixes by id (the joined harness, engine included):
    STATS' Life row is 38 EXACT.
  · OLD BUILDS LOAD UNCHANGED: a build saved before this (a Diadem with q 'b', no affixes) opens on Edit as Normal and
    hands the engine a plain base.
  · Esc closes the ADD MOD list first, then the picker.
⚠ WHAT THIS LAW CANNOT SEE: pixels — tv/test_the_character_builder_fits_at_every_width.py measures the Edit tab with its
picked mods and the open ADD MOD list at 2000 / 1280 / 375 in a real browser.
RED_PROOF below.
"""
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

#: helpers every case shares: a build of a class, the current build, the stripped tooltip
HELP = r"""
function mk(cls, lvl){ window.openCharBuilder(); window._cbOpenNew(); window._cbNewCls(cls); window._cbNewLvl(lvl); window._cbNewGo(); }
function cur(){ return window._cbAll()[window._cbState().bid]; }
function strip(h){ return String(h).replace(/<[^>]+>/g, '|').replace(/&#39;/g, "'").replace(/\|+/g, '|'); }
function ids(e){ var P = window._cbAffixPool(e), o = {}; ['p', 's', 'a', 'q'].forEach(function(k){ o[k] = P.rows[k].map(function(a){ return a[0]; }); }); o.full = P.full; return o; }
function has(e, id){ var P = window._cbAffixPool(e); return ['p', 's', 'a', 'q'].some(function(k){ return P.rows[k].some(function(a){ return a[0] === id; }); }); }
function box(ax, key, lo, hi, v){ var at = { 'data-key': key, 'data-lo': String(lo), 'data-hi': String(hi), 'data-ax': String(ax) };
  return { target: { value: String(v), classList: { contains: function(c){ return c === 'cb-roll'; }, add: function(){}, remove: function(){}, toggle: function(){} },
           getAttribute: function(a){ return Object.prototype.hasOwnProperty.call(at, a) ? at[a] : null; } } }; }
function inv(){ var s = cur().sets[0].inv; return s[s.length - 1]; }
"""


def _run(body):
    return CB._run(HELP + body)


@unittest.skipIf(CB.NODE is None, "node is not on this machine")
class TheEditTabBuildsTheirItems(unittest.TestCase):

    def test_quality_is_offered_only_where_the_base_can_be_more_than_one(self):
        out = _run(r"""
          mk('Warlock', 90);
          window._cbOpenPick('slot', 'head'); window._cbChoose('b:ci3');
          OUT.diadem = { tab: window._cbState().pick.tab, pending: window._cbState().pick.pending, stored: !!cur().sets[0].slots.head,
            opts: (MODAL._html.match(/data-q="[a-z]+"/g) || []).map(function(x){ return x.slice(8, -1); }),
            rareCls: /class="cb-opt cb-c-rare" role="option" data-q="rare"[^>]*>Rare</.test(MODAL._html),
            magicCls: /class="cb-opt cb-c-m" role="option" data-q="m"[^>]*>Magic</.test(MODAL._html),
            editGrey: /role="tab" class="cb-tab" disabled aria-selected="false" onclick="window._cbPickTab\('edit'\)">Edit/.test(MODAL._html) };
          window._cbQuality('m'); OUT.afterQ = [window._cbState().pick.tab, cur().sets[0].slots.head.q, /id="cb-qual"/.test(MODAL._html)];
          window._cbClosePick();
          window._cbOpenPick('slot', 'rrin'); window._cbChoose('b:rin');
          OUT.ring = (MODAL._html.match(/data-q="[a-z]+"/g) || []).map(function(x){ return x.slice(8, -1); }); window._cbClosePick();
          window._cbOpenPick('inv', null, [0, 0]); window._cbChoose('b:cm3');
          OUT.gc = [window._cbState().pick.tab, inv().q, /data-q=/.test(MODAL._html)]; window._cbClosePick();
          var coa = null; window._cbDb().it.forEach(function(x){ if (x[1] === 'Crown of Ages') coa = x[0]; });
          window._cbOpenPick('slot', 'head'); window._cbChoose(coa); OUT.unique = [window._cbState().pick.tab, /Quality</.test(MODAL._html)];
        """)
        d = out["diadem"]
        self.assertEqual((d["tab"], d["pending"], d["stored"]), ("quality", "b:ci3", False),
                         "a Diadem did not wait on its Quality tab (or was equipped before a quality was chosen): %s" % d)
        self.assertEqual(d["opts"], ["rare", "m", "sup", "b", "low"], "the Diadem's qualities are not theirs in their order")
        self.assertTrue(d["rareCls"] and d["magicCls"], "Rare / Magic are not drawn in their colours")
        self.assertTrue(d["editGrey"], "Edit is not greyed while the quality is pending")
        self.assertEqual(out["afterQ"], ["edit", "m", True], "choosing Magic did not equip it and flip to Edit with a Quality box")
        self.assertEqual(out["ring"], ["rare", "m"], "a ring can be only rare or magic (itemtypes.txt ring: Magic 1, Rare 1)")
        self.assertEqual(out["gc"], ["edit", "m", False], "a Grand Charm is always magic and goes straight to Edit")
        self.assertEqual(out["unique"], ["edit", False], "a unique must never see a Quality tab")

    def test_add_mod_lists_by_type_level_and_maxlevel(self):
        out = _run(r"""
          mk('Warlock', 90);
          window._cbOpenPick('inv', null, [0, 0]); window._cbChoose('b:cm3');
          var e = inv(); OUT.gc99 = [has(e, 'p700'), has(e, 's338'), has(e, 'p143')];
          e.ilvl = 49; OUT.gc49 = has(e, 'p700'); e.ilvl = 50; OUT.gc50 = has(e, 'p700'); e.ilvl = 76; OUT.vita76 = has(e, 's338');
          var dm = { id: 'b:ci3', base: 'ci3', q: 'm', ilvl: 3 }; OUT.crimson3 = has(dm, 'p665'); dm.ilvl = 99; OUT.crimson99 = has(dm, 'p665');
          OUT.diademNoChaotic = !has(dm, 'p700') && has(dm, 'p712');
          OUT.firstRow = window._cbDb().af.filter(function(a){ return a[0] === 'p700'; })[0];
        """)
        self.assertEqual(out["firstRow"][:9], ["p700", "p", "Chaotic", 50, None, 42, 1, 125, 7], "the premise moved: Chaotic")
        self.assertEqual(out["gc99"], [True, True, False], "a Grand Charm's list: Chaotic and of Vita yes (lcha), Sturdy never (armo)")
        self.assertEqual((out["gc49"], out["gc50"], out["vita76"]), (False, True, False), "the affix level vs the item level")
        self.assertEqual((out["crimson3"], out["crimson99"]), (True, False), "maxlevel 4: Crimson p665 only at item level <= 4")
        self.assertTrue(out["diademNoChaotic"], "a Diadem lists its own affixes (Devil's) and never a charm's (Chaotic)")

    def test_add_mod_lists_by_group_class_rare_flag_and_automod(self):
        out = _run(r"""
          mk('Warlock', 90);
          window._cbOpenPick('inv', null, [0, 0]); window._cbChoose('b:cm3');
          OUT.added = window._cbAddMod('p700');
          OUT.stored = inv().affixes;
          window._cbClosePick();
          /* the GROUP on a RARE (three prefixes allowed, so the magic item's one-prefix cap cannot hide the rule): after
             Devil's (group 125) its sibling Arch-Devil's is gone while Jagged (group 105) is still offered */
          window._cbOpenPick('slot', 'head'); window._cbChoose('b:ci3'); window._cbQuality('rare');
          var h0 = cur().sets[0].slots.head; OUT.before = [has(h0, 'p713'), has(h0, 'p186')];
          window._cbAddMod('p712');
          var h = cur().sets[0].slots.head; OUT.sibs = [has(h, 'p713'), has(h, 'p186')];
          OUT.refused = window._cbAddMod('p713'); OUT.say = window._cbState().modSay;
          OUT.rareStored = cur().sets[0].slots.head.affixes;
          OUT.orb = has({ id: 'b:ob1', base: 'ob1', q: 'm', ilvl: 99 }, 'p481');
          OUT.sword = has({ id: 'b:crs', base: 'crs', q: 'm', ilvl: 99 }, 'p481');
          OUT.rareDiadem = has({ id: 'b:ci3', base: 'ci3', q: 'rare', ilvl: 99 }, 'p313');
          OUT.magicDiadem = has({ id: 'b:ci3', base: 'ci3', q: 'm', ilvl: 99 }, 'p313');
          OUT.orbAuto = has({ id: 'b:ob1', base: 'ob1', q: 'm', ilvl: 99 }, 'a9');
          OUT.diademAuto = ids({ id: 'b:ci3', base: 'ci3', q: 'm', ilvl: 99 }).a.length;
          OUT.bowAuto = has({ id: 'b:am1', base: 'am1', q: 'm', ilvl: 99 }, 'a9');
        """)
        self.assertTrue(out["added"], "Chaotic could not be added to a Grand Charm")
        self.assertEqual(out["stored"], [{"id": "p700", "rolls": {}}])
        self.assertEqual(out["before"], [True, True], "the premise moved: Arch-Devil's and Jagged on an empty rare Diadem")
        self.assertEqual(out["sibs"], [False, True], "after Devil's (group 125): Arch-Devil's (125) gone, Jagged (105) still offered")
        self.assertFalse(out["refused"], "a second affix of group 125 was added")
        self.assertIn("not added", out["say"])
        self.assertEqual(out["rareStored"], [{"id": "p712", "rolls": {}}])
        self.assertEqual((out["orb"], out["sword"]), (False, True),
                         "Expert's (tied to the Barbarian) on a Sorceress's orb / on a Crystal Sword anyone holds")
        self.assertEqual((out["rareDiadem"], out["magicDiadem"]), (False, True), "Bahamut's (rare 0) on a rare / a magic Diadem")
        self.assertEqual((out["orbAuto"], out["diademAuto"], out["bowAuto"]), (True, 0, False),
                         "an automod is the base's own automagic group (Eagle Orb 303; a Diadem none; an Amazon bow 300)")

    def test_the_qualitys_limits_hold(self):
        out = _run(r"""
          mk('Warlock', 90);
          window._cbOpenPick('inv', null, [0, 0]); window._cbChoose('b:cm3'); window._cbAddMod('p700');
          var P = window._cbAffixPool(inv()); OUT.magic = [P.full.p, P.rows.p.length, P.full.s, P.rows.s.length > 0];
          OUT.magicHtml = /Prefixes <small>full · 1 of 1<\/small>/.test((function(){ window._cbModOpen(true); return MODAL._html; })());
          window._cbClosePick();
          window._cbOpenPick('slot', 'head'); window._cbChoose('b:ci3'); window._cbQuality('rare');
          ['p712', 'p374', 'p309'].forEach(function(id){ window._cbAddMod(id); });
          var h = cur().sets[0].slots.head, Q = window._cbAffixPool(h); OUT.rare = [h.affixes.length, Q.full.p, Q.rows.p.length, Q.full.s];
          OUT.fourthOk = has({ id: 'b:ci3', base: 'ci3', q: 'rare', ilvl: 99 }, 'p186');
          OUT.fourth = window._cbAddMod('p186');
          window._cbClosePick();
          window._cbOpenPick('inv', null, [5, 0]); window._cbChoose('b:jew'); OUT.jewTab = window._cbState().pick.tab; window._cbQuality('rare');
          var got = [];
          ['p', 'p', 's', 's'].forEach(function(k){ var J0 = window._cbAffixPool(inv()); got.push(J0.rows[k].length ? window._cbAddMod(J0.rows[k][0][0]) : 'none'); });
          var J = window._cbAffixPool(inv()); OUT.jewel = [got, inv().affixes.length, J.full.p, J.full.s];
        """)
        self.assertEqual(out["magic"], [True, 0, False, True], "a magic item holds one prefix, and still takes a suffix")
        self.assertTrue(out["magicHtml"], "ADD MOD does not say PREFIXES is full (1 of 1)")
        self.assertEqual(out["rare"], [3, True, 0, False], "a rare holds three prefixes, and still takes suffixes")
        self.assertTrue(out["fourthOk"], "the premise moved: Jagged p186 is not a prefix an empty rare Diadem may carry")
        self.assertFalse(out["fourth"], "a fourth prefix went onto a rare")
        self.assertEqual(out["jewTab"], "quality", "a jewel can be magic or rare: it waits on Quality")
        self.assertEqual(out["jewel"], [[True, True, True, True], 4, True, True], "a rare jewel holds four affixes in all")

    def test_a_roll_outside_its_range_is_refused_and_a_picked_mod_reaches_the_store_and_the_tooltip(self):
        out = _run(r"""
          mk('Warlock', 90);
          window._cbOpenPick('inv', null, [0, 0]); window._cbChoose('b:cm3');
          window._cbAddMod('p700'); window._cbAddMod('s338');
          OUT.boxes = (MODAL._html.match(/data-ax="1" class="cb-roll[^"]*"[^>]*data-key="m1" data-lo="36"[^>]*data-hi="40"/g) || []).length;
          window._cbRollInput(box(1, 'm1', 36, 40, 41)); OUT.bad = [JSON.stringify(inv().affixes[1].rolls), window._cbState().modSay, window._cbState().modBad];
          window._cbRollInput(box(1, 'm1', 36, 40, 38)); OUT.good = inv().affixes;
          window._cbPickTab('edit');
          OUT.name = (MODAL._html.match(/<div class="cb-ed-n (cb-c-[a-z]+)" id="cb-ed-name">([^<]*)</) || []).slice(1);
          var s = inv(), t = window._cbTipEntry(s, window._cbItem(s.id), 90, 'inv', 'Warlock'); OUT.tipQ = t.q; OUT.tip = strip(window.d2Tip(t));
          OUT.tipHead = (window.d2Tip(t).match(/^<div class="(d2t-[a-z]+)">([^<]*)<\/div>/) || []).slice(1);
          OUT.stored = JSON.parse(window.LSR.getItem('d2r_charBuilds'))[window._cbState().bid].sets[0].inv[0];
          window._cbClosePick();
          window._cbOpenPick('slot', 'head'); window._cbChoose('b:ci3'); window._cbQuality('rare');
          var h = cur().sets[0].slots.head; OUT.rn = h.rn; OUT.rareName = (MODAL._html.match(/<div class="cb-ed-n (cb-c-[a-z]+)" id="cb-ed-name">([^<]*) <span/) || []).slice(1);
          var rt = window._cbTipEntry(h, window._cbItem(h.id), 90, 'head', 'Warlock'); OUT.rareTip = [rt.name, rt.base, rt.q];
        """)
        self.assertEqual(out["boxes"], 1, "of Vita's picked row has no roll box keyed m1 inside 36-40")
        self.assertEqual(out["bad"][0], "{}", "41 (outside 36-40) was saved")
        self.assertIn("36–40", out["bad"][1], "the refusal does not show the range")
        self.assertTrue(out["bad"][2], "the refusal is not said as a refusal")
        self.assertEqual(out["good"], [{"id": "p700", "rolls": {}}, {"id": "s338", "rolls": {"m1": 38}}])
        self.assertEqual(out["stored"]["q"], "m")
        self.assertEqual(out["stored"]["affixes"], [{"id": "p700", "rolls": {}}, {"id": "s338", "rolls": {"m1": 38}}],
                         "the picked mods are not on the stored entry (d2r_charBuilds)")
        self.assertEqual(out["name"], ["cb-c-m", "Chaotic Grand Charm of Vita"], "the magic name is not composed prefix + base + suffix, in blue")
        self.assertEqual(out["tipHead"], ["d2t-m", "Chaotic Grand Charm of Vita"])
        self.assertIn("|+1 to Chaos Skills (Warlock Only)|", out["tip"])
        self.assertIn("|+38 to Life|", out["tip"], "the typed roll is not what the tooltip prints")
        self.assertIn("Required Level: 69", out["tip"], "of Vita's own level requirement (69) is not the item's")
        self.assertEqual(len(out["rn"]), 2)
        self.assertTrue(all(out["rn"]), "a rare did not get its two words from the dice")
        self.assertEqual(out["rareName"], ["cb-c-rare", " ".join(out["rn"])], "a rare's Edit name is not its two words in rare yellow")
        self.assertEqual(out["rareTip"], [" ".join(out["rn"]), "Diadem", "rare"])

    def test_the_picked_mods_reach_the_sheet_and_old_builds_load_unchanged(self):
        import test_the_character_builder_is_joined_to_the_engine_and_the_mule_window as J
        out = J._run(HELP + r"""
          mk('Warlock', 90);
          window._cbOpenPick('inv', null, [0, 0]); window._cbChoose('b:cm3'); window._cbAddMod('p700'); window._cbAddMod('s338');
          window._cbRollInput(box(1, 'm1', 36, 40, 38)); window._cbClosePick();
          OUT.life = rowOf(eng(), 'life'); OUT.tab = rowOf(eng(), 'tab:23');
          OUT.ent = window._cbEngineBuild(cur()).build.inv[0];
          var all = window._cbAll(), id = window._cbState().bid;
          all[id].sets[0].inv = []; all[id].sets[0].slots.head = { id: 'b:ci3', name: 'Diadem', q: 'b', base: 'ci3', sockets: 0, eth: false, rolls: {}, socketed: [], ilvl: 99 };
          window.LSR.setItem('d2r_charBuilds', JSON.stringify(all));
          window.closeCharBuilder(); window.openCharBuilder(id);
          window._cbOpenPick('slot', 'head');
          OUT.old = [window._cbState().pick.tab, (MODAL._html.match(/<option value="([a-z]+)" class="cb-c-[a-z]+" selected>/) || [])[1], /Regular Mods/.test(MODAL._html)];
          OUT.oldEnt = window._cbEngineBuild(cur()).build.slots.head;
        """)
        self.assertEqual(out["life"][:2], [{"min": 38, "max": 38}, "EXACT"], "the typed of Vita did not reach STATS' Life: %s" % out["life"])
        self.assertEqual(out["tab"][:2], [{"min": 1, "max": 1}, "EXACT"], "Chaotic did not reach the Chaos Skills row: %s" % out["tab"])
        self.assertEqual(out["ent"]["affixes"], [{"id": "p700", "rolls": {}}, {"id": "s338", "rolls": {"m1": 38}}])
        self.assertEqual(out["ent"]["quality"], "magic")
        self.assertEqual(out["old"], ["edit", "b", True], "a build saved before v-B3 does not open as a Normal Diadem")
        self.assertEqual((out["oldEnt"]["name"], out["oldEnt"]["quality"], "affixes" in out["oldEnt"]), ("ci3", "base", False),
                         "an old build's base is not handed to the engine exactly as before")

    def test_esc_closes_the_add_mod_list_before_the_picker(self):
        out = _run(r"""
          mk('Warlock', 90);
          window._cbOpenPick('inv', null, [0, 0]); window._cbChoose('b:cm3'); window._cbModOpen(true);
          OUT.open = /id="cb-add-list"/.test(MODAL._html);
          OUT.first = window._cbEsc(); OUT.closed = !/id="cb-add-list"/.test(MODAL._html) && !!window._cbState().pick;
          OUT.second = window._cbEsc();
        """)
        self.assertTrue(out["open"])
        self.assertEqual((out["first"], out["closed"], out["second"]), ("addmod", True, "picker"))


RED_PROOF = [
    {
        "why": "#174 v-B3 - a base skips its Quality tab (their Select -> Quality -> Edit is gone)",
        "file": "bible.html",
        "find": "      if (qs.length > 1){ p.pending = id; p.tab = 'quality'; _cbModal(); return true; }\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - ADD MOD stops filtering by item type: a charm lists armour affixes",
        "file": "bible.html",
        "find": "      if (!a[9].some(function(t){ return anc[t]; })) return;\n      if (a[10].some(function(t){ return anc[t]; })) return;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - ADD MOD ignores the affix level and maxlevel",
        "file": "bible.html",
        "find": "      if (a[3] > ilvl || (a[4] != null && ilvl > a[4])) return;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - two affixes of one group go on one item",
        "file": "bible.html",
        "find": "      if (used[a[7]]) return;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - a rare lists affixes that never spawn on a rare (the rare flag)",
        "file": "bible.html",
        "find": "      if (q === 'rare' && !a[6]) return;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - a class item lists another class's tied affixes",
        "file": "bible.html",
        "find": "      if (a[8] >= 0 && tcls != null && tcls >= 0 && a[8] !== tcls) return;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - a magic item takes two prefixes",
        "file": "bible.html",
        "find": "    if (q === 'm') return { p: 1, s: 1, a: 1, q: 0, total: null };\n",
        "replace": "    if (q === 'm') return { p: 2, s: 1, a: 1, q: 0, total: null };\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - a typed roll of a picked mod never reaches the store",
        "file": "bible.html",
        "find": "x.rolls = x.rolls || {}; if (r.v == null) delete x.rolls[key]; else x.rolls[key] = r.v; okAx = true; });",
        "replace": "x.rolls = x.rolls || {}; okAx = true; });",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - the tooltip never prints the picked mods",
        "file": "bible.html",
        "find": "    if (it && e.affixes && e.affixes.length){ var W = _cbWithAffixes(it, e); it = W[0]; rolls = W[1]; }\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - a magic item keeps its base's name (Grand Charm, never Chaotic Grand Charm of Vita)",
        "file": "bible.html",
        "find": "    if (q === 'm') return { name: pre.concat([bn], suf).join(' '), base: '', q: 'm' };\n",
        "replace": "    if (q === 'm') return { name: bn, base: '', q: 'm' };\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - ADD MOD adds any id it is handed, whatever the list offers",
        "file": "bible.html",
        "find": "    if (!a || !(P.rows[a[1]] || []).some(function(r){ return r[0] === id; })){\n",
        "replace": "    if (!a){\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - a charm's quality flags are inherited again and a Grand Charm offers Rare",
        "file": "bible.html",
        "find": "\"lcha\":[\"m\"]",
        "replace": "\"lcha\":[\"rare\",\"m\"]",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if CB.NODE is None:
        sys.stderr.write("⚪ SKIP — node is not on this machine, so the Edit tab was not driven. UNMEASURED, declared (77).\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
