# -*- coding: utf-8 -*-
"""#174 v-B4 — A RUNEWORD OPENS ITS BASE TAB, AND THE TAB IS THEIRS: THE GROUPS, THE ROWS, THE ORDER, THE HOVER, THE CLICK.

His words (2026-09-26): "after i clicked within the tabs for weapons and click runewords and then it gives me this list of
base items to represent it in within the character ... see its like SELECT tab and then BASE TAB that way it continues to
stay organzied". Their planner, measured the same hour with a real mouse (a Sorceress, level 99): picking Breath of the
Dying turns the modal into Select | Base | Edit on Base - every base the runeword can be made in AND can hold its runes,
grouped "Elite Axes" / "Exceptional Axes" / "Normal Axes", the categories A-Z, each group's rows by the base's qlvl high to
low; a class-only base of another class is not listed; hovering a row is the runeword ON THAT BASE; clicking it wears it
there. Ours, before this: no Base tab - the runeword went on the first base (Crystal Sword) and the base was a <select>.

This law drives the SHIPPED builder in node (the builder law's own harness: the ⟦CHARACTER BUILDER JS⟧ block and the
generated ⟦CB_DB⟧ block cut from bible.html, never re-typed), and reads the modal the builder DREW:

  · THE GROUPS, ROWS AND ORDER ARE THEIRS. Breath of the Dying: all 48 rows (the first 40 read row by row off their list,
    the last 8 off 80_breath_of_the_dying_base scrolled to its end); Grief 30, Spirit 24 and Heart of the Oak 12 (their
    whole lists); Insight and Call to Arms as far as their virtualised list drew (49 and 48 rows - a prefix, said so).
    Spirit on the weapon slot is its 24 SWORDS and no shield - the weapon hand lists the runeword's weapon bases.
  · A CLASS'S BASES: for a Sorceress no Amazon spear; for an Amazon the Matriarchal Pike under "Elite Amazon Spears" - and
    exactly as many more rows as the block holds Amazon bases that carry six runes (derived here from CB_DB).
  · THE ITEM LEVEL HOLDS THE SOCKETS: at item level 20 no base carries six runes and the tab says so; at 99 all 48.
  · HOVER = the runeword on THAT base, drawn by the builder's own tooltip component (window.d2Tip's box names Crowbill).
  · CLICK = worn on that base (the slot's base is 9mp, its six runes socketed) and Edit opens; Edit's Base control goes
    back to the Base tab; a base the runeword cannot take is refused and nothing moves.
  · THE SEARCH MATCH IS UNDERLINED (Base and Select lists), the Filters narrow the bases (Elite only).
  · THE WEAPON RAIL IS THE GAME'S TYPE TREE from CB_DB ty[code][4]: Weapons and Shields > Shields (Auric Shields, Voodoo
    Heads, Grimoires) > Melee Weapons (their twelve, their order) > Missile Weapons (Bows, Crossbows) > Orbs > Thrown
    Weapons (Throwing Axes, Throwing Knives, Javelins - and our data's own Missile Potions, a type theirs does not draw);
    Axes > Throwing Axes, Daggers > Throwing Knives, Spears > Amazon Spears + Javelins, Bows > Amazon Bows, Javelins >
    Amazon Javelins; the first level open, deeper ones folded; a node lists its type and below (Axes lists a Throwing
    Axe, never a sword); and the weapon slot's list carries shields, as theirs does (Aegis, Ancient Shield).
  · #174 v-B4 review — THE LEFT HAND KEEPS ITS SECOND WEAPONS ROW. The flat rail had "Second Weapons (Barbarian)" for every
    class; the tree dropped it. A Sorceress's left-hand tree ends with that row (marked Barbarian), it lists exactly the
    one-handed weapon bases the block holds with no class lock (derived here from CB_DB) and never a shield, her whole list
    still holds none of them, and her Base tab does not draw it; a Barbarian's tree carries the weapon types instead.

⚠ WHAT THIS LAW CANNOT SEE: pixels and a real pointer - the PNGs of the shipped modal (2000x1300) are the builder's report;
the tooltip's own LINES (merged, in the game's order) are the tooltip rewrite's law, not this one - this law asks only
that the hover box is the runeword on the hovered base.
RED_PROOF below.
"""
import json
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

import test_the_character_builder_is_their_builder as CB  # noqa: E402  the builder's own harness, one cut

#: THEIR Base tab, a Sorceress at level 99, measured with a real mouse (2026-09-26). The game's own words only.
THEIRS = {
    "Breath of the Dying": [
        ("Elite Axes", ["Berserker Axe", "Glorious Axe", "Champion Axe", "War Spike"]),
        ("Exceptional Axes", ["Ancient Axe", "Naga", "Gothic Axe", "Crowbill"]),
        ("Normal Axes", ["Giant Axe", "War Axe", "Great Axe", "Military Pick"]),
        ("Elite Bows", ["Hydra Bow", "Crusader Bow"]), ("Exceptional Bows", ["Gothic Bow", "Large Siege Bow"]),
        ("Normal Bows", ["Long War Bow", "Long Battle Bow"]),
        ("Elite Crossbows", ["Colossus Crossbow"]), ("Exceptional Crossbows", ["Ballista"]), ("Normal Crossbows", ["Heavy Crossbow"]),
        ("Elite Hammers", ["Thunder Maul", "Ogre Maul"]), ("Exceptional Hammers", ["Martel de Fer", "War Club"]),
        ("Normal Hammers", ["Great Maul", "Maul"]),
        ("Elite Polearms", ["Giant Thresher", "Great Poleaxe"]), ("Exceptional Polearms", ["Grim Scythe", "Bec-de-Corbin"]),
        ("Normal Polearms", ["War Scythe", "Halberd"]),
        ("Elite Spears", ["War Pike", "Ghost Spear"]), ("Exceptional Spears", ["Lance", "Yari"]), ("Normal Spears", ["Pike", "Spetum"]),
        # rows 41-48, off their list scrolled to its end (80_breath_of_the_dying_base)
        ("Elite Staves", ["Archon Staff"]), ("Exceptional Staves", ["Rune Staff"]), ("Normal Staves", ["War Staff"]),
        ("Elite Swords", ["Colossus Blade", "Phase Blade"]), ("Exceptional Swords", ["Executioner Sword", "Dimensional Blade"]),
        ("Normal Swords", ["Great Sword", "Crystal Sword"]),
    ],
    "Grief": [
        ("Elite Axes", ["Berserker Axe", "Glorious Axe", "Champion Axe", "War Spike", "Decapitator", "Ettin Axe", "Silver-edged Axe"]),
        ("Exceptional Axes", ["Ancient Axe", "Naga", "Gothic Axe", "Crowbill", "Tabar", "Twin Axe", "Bearded Axe"]),
        ("Normal Axes", ["Giant Axe", "War Axe", "Great Axe", "Military Pick", "Battle Axe", "Double Axe", "Broad Axe"]),
        ("Elite Swords", ["Colossus Blade", "Colossus Sword", "Phase Blade"]),
        ("Exceptional Swords", ["Executioner Sword", "Zweihander", "Dimensional Blade"]),
        ("Normal Swords", ["Great Sword", "Flamberge", "Crystal Sword"]),
    ],
    "Spirit": [
        ("Elite Swords", ["Colossus Blade", "Cryptic Sword", "Colossus Sword", "Conquest Sword", "Champion Sword", "Phase Blade",
                          "Balrog Blade", "Highland Blade"]),
        ("Exceptional Swords", ["Executioner Sword", "Zweihander", "Gothic Sword", "Tusk Sword", "Rune Sword", "Dacian Falx",
                                "Battle Sword", "Dimensional Blade"]),
        ("Normal Swords", ["Great Sword", "Flamberge", "Bastard Sword", "Giant Sword", "Long Sword", "Claymore", "Broad Sword",
                           "Crystal Sword"]),
    ],
    "Heart of the Oak": [
        ("Elite Maces", ["Scourge"]), ("Exceptional Maces", ["Knout"]), ("Normal Maces", ["Flail"]),
        ("Elite Staves", ["Archon Staff", "Shillelagh", "Elder Staff"]), ("Exceptional Staves", ["Rune Staff", "Gothic Staff", "Cedar Staff"]),
        ("Normal Staves", ["War Staff", "Battle Staff", "Gnarled Staff"]),
    ],
    # their list is virtualised: these are the rows it DREW, a prefix of the whole - compared as a prefix, said so
    "Insight": [
        ("Elite Bows", ["Hydra Bow", "Ward Bow", "Crusader Bow", "Diamond Bow", "Great Bow", "Shadow Bow", "Blade Bow"]),
        ("Exceptional Bows", ["Gothic Bow", "Rune Bow", "Large Siege Bow", "Short Siege Bow", "Double Bow", "Cedar Bow", "Razor Bow"]),
        ("Normal Bows", ["Long War Bow", "Short War Bow", "Long Battle Bow", "Short Battle Bow", "Composite Bow", "Long Bow", "Hunter's Bow"]),
        ("Elite Crossbows", ["Demon Crossbow", "Colossus Crossbow", "Gorgon Crossbow"]),
        ("Exceptional Crossbows", ["Chu-Ko-Nu", "Ballista", "Siege Crossbow"]),
        ("Normal Crossbows", ["Repeating Crossbow", "Heavy Crossbow", "Crossbow"]),
        ("Elite Polearms", ["Giant Thresher", "Great Poleaxe", "Cryptic Axe", "Thresher", "Colossus Voulge"]),
        ("Exceptional Polearms", ["Grim Scythe", "Bec-de-Corbin", "Battle Scythe", "Bill", "Partizan"]),
        ("Normal Polearms", ["War Scythe", "Halberd", "Poleaxe", "Scythe", "Voulge"]),
        ("Elite Staves", ["Archon Staff", "Shillelagh", "Elder Staff"]), ("Exceptional Staves", ["Rune Staff"]),
    ],
    "Call to Arms": [
        ("Elite Axes", ["Berserker Axe", "Glorious Axe", "Champion Axe", "War Spike", "Decapitator", "Ettin Axe", "Silver-edged Axe"]),
        ("Exceptional Axes", ["Ancient Axe", "Naga", "Gothic Axe", "Crowbill", "Tabar", "Twin Axe", "Bearded Axe"]),
        ("Normal Axes", ["Giant Axe", "War Axe", "Great Axe", "Military Pick", "Battle Axe", "Double Axe", "Broad Axe"]),
        ("Elite Bows", ["Hydra Bow", "Ward Bow", "Crusader Bow", "Diamond Bow", "Shadow Bow"]),
        ("Exceptional Bows", ["Gothic Bow", "Rune Bow", "Large Siege Bow", "Short Siege Bow", "Cedar Bow"]),
        ("Normal Bows", ["Long War Bow", "Short War Bow", "Long Battle Bow", "Short Battle Bow", "Long Bow"]),
        ("Elite Crossbows", ["Demon Crossbow", "Colossus Crossbow"]), ("Exceptional Crossbows", ["Chu-Ko-Nu", "Ballista"]),
        ("Normal Crossbows", ["Repeating Crossbow", "Heavy Crossbow"]),
        ("Elite Hammers", ["Thunder Maul", "Ogre Maul"]), ("Exceptional Hammers", ["Martel de Fer", "War Club"]),
        ("Normal Hammers", ["Great Maul", "Maul"]),
    ],
}
PREFIX_ONLY = {"Insight", "Call to Arms"}

HELP = r"""
function mk(cls, lvl){ window.openCharBuilder(); window._cbOpenNew(); window._cbNewCls(cls); window._cbNewLvl(lvl); window._cbNewGo(); }
function cur(){ return window._cbAll()[window._cbState().bid]; }
function unesc(t){ return String(t).replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&'); }
function rwId(n){ var h = null; window._cbDb().it.forEach(function(x){ if (x[1] === n && x[2] === 'r') h = x[0]; }); return h; }
/* the Base tab's list as the builder DREW it: [name, its group, base code] in order */
function baseRows(){
  var re = /<div class="cb-bgrp"[^>]*>([^<]*)<\/div>|<button type="button" class="cb-opt cb-bopt[^"]*"[^>]*data-base="([^"]+)"[^>]*>(.*?)<\/button>/g, m, g = null, out = [];
  while ((m = re.exec(MODAL._html))){ if (m[1] != null) g = unesc(m[1]); else out.push([unesc(m[3].replace(/<[^>]+>/g, '')), g, m[2]]); }
  return out;
}
function tabs(){ var re = /role="tab" class="cb-tab( cb-on)?"( disabled)? aria-selected="[a-z]+" onclick="window\._cbPickTab\('([a-z]+)'\)">([^<]*)</g, m, o = [];
  while ((m = re.exec(MODAL._html))) o.push(m[4] + (m[1] ? '*' : '') + (m[2] ? '(off)' : '')); return o; }
function pickRw(slot, name){ window._cbOpenPick('slot', slot); window._cbQt('r'); return window._cbChoose(rwId(name)); }
function fakeEl(code){ return { getAttribute: function(k){ return k === 'data-base' ? code : null; }, getBoundingClientRect: El.prototype.getBoundingClientRect }; }
function tipHtml(){ var t = ELS['cb-tip']; return t && !t.hidden ? t._html : null; }
"""


def _run(body):
    return CB._run(HELP + body)


def _flat(groups):
    return [[n, g] for g, names in groups for n in names]


def _band(ty, ilvl):
    m = ty[3]
    return m[0] if ilvl <= m[1] else (m[2] if ilvl <= m[3] else m[4])


@unittest.skipIf(CB.NODE is None, "node is not on this machine")
class TheBaseTabIsTheirs(unittest.TestCase):

    def test_a_runeword_opens_its_base_tab_with_their_groups_rows_and_order(self):
        names = list(THEIRS)
        out = _run(r"""
          mk('Sorceress', 99);
          OUT.picked = pickRw('rarm', 'Breath of the Dying');
          OUT.tab = window._cbState().pick.tab; OUT.rw = window._cbState().pick.rw; OUT.worn = !!cur().sets[0].slots.rarm;
          OUT.tabs = tabs(); OUT.id = rwId('Breath of the Dying');
          OUT.rows = {};
          %s.forEach(function(n){ window._cbClosePick(); pickRw('rarm', n); OUT.rows[n] = baseRows().map(function(r){ return [r[0], r[1]]; }); });
        """ % json.dumps(names))
        self.assertIs(out["picked"], True)
        self.assertEqual((out["tab"], out["rw"], out["worn"]), ("base", out["id"], False),
                         "picking Breath of the Dying did not wait on its Base tab (or it was worn on a first base anyway)")
        self.assertEqual(out["tabs"], ["Select", "Base*", "Edit(off)"], "the modal is not their Select | Base | Edit, Edit greyed")
        for n in names:
            want, got = _flat(THEIRS[n]), out["rows"][n]
            self.assertGreaterEqual(len(got), len(want), "%s: %d rows drawn, theirs has at least %d" % (n, len(got), len(want)))
            if n in PREFIX_ONLY:
                self.assertEqual(got[:len(want)], want, "%s: the rows their list drew are not ours, in order" % n)
            else:
                self.assertEqual(got, want, "%s: the Base tab is not theirs (group / row / order):\n%s" % (n, "\n".join(
                    "%-3d ours %-40s theirs %s" % (i, got[i] if i < len(got) else None, want[i] if i < len(want) else None)
                    for i in range(max(len(got), len(want))) if (got[i:i + 1] != want[i:i + 1]))))
        self.assertFalse(any("Shield" in g for _, g in out["rows"]["Spirit"]), "Spirit on the weapon slot listed shields")

    def test_another_classes_base_is_absent_and_its_own_class_sees_it(self):
        out = _run(r"""
          mk('Sorceress', 99); pickRw('rarm', 'Breath of the Dying'); OUT.sorc = baseRows();
          mk('Amazon', 99); pickRw('rarm', 'Breath of the Dying'); OUT.ama = baseRows();
        """)
        db = CB._db()
        amazon = [c for c, b in db["b"].items() if b[20] and b[1] in db["ty"] and db["ty"][b[1]][2] == 0
                  and b[21] == "w" and min(b[4], _band(db["ty"][b[1]], 99)) >= 6]
        self.assertGreaterEqual(len(amazon), 1, "PRINT THE DENOMINATOR: the block holds no Amazon base that carries six runes")
        sorc = [r[0] for r in out["sorc"]]
        self.assertEqual(len(sorc), 48)
        self.assertNotIn("Matriarchal Pike", sorc, "a Sorceress is offered an Amazon-only spear")
        self.assertIn(["Matriarchal Pike", "Elite Amazon Spears"], [r[:2] for r in out["ama"]], "an Amazon is not offered her own spear")
        self.assertEqual(len(out["ama"]) - len(out["sorc"]), len(amazon),
                         "an Amazon's list is not the Sorceress's plus the block's %d six-rune Amazon bases" % len(amazon))

    def test_the_item_level_holds_the_socket_count(self):
        out = _run(r"""
          mk('Sorceress', 99); pickRw('rarm', 'Breath of the Dying'); window._cbPickBase('9mp');
          window._cbEdit('ilvl', 20); window._cbPickTab('base');
          OUT.low = baseRows(); OUT.say = /No base this slot holds can carry Breath of the Dying/.test(MODAL._html);
          window._cbPickTab('edit'); window._cbEdit('ilvl', 99); window._cbPickTab('base'); OUT.high = baseRows().length;
        """)
        db = CB._db()
        names = [n for _, ns in THEIRS["Breath of the Dying"] for n in ns]
        by = dict((b[0], c) for c, b in db["b"].items() if b[20])
        at20 = [n for n in names if min(db["b"][by[n]][4], _band(db["ty"][db["b"][by[n]][1]], 20)) >= 6]
        self.assertEqual([r[0] for r in out["low"]], at20, "at item level 20 the bases that carry six runes are not the tables'")
        self.assertEqual(at20, [], "the tables let an item-level-20 base carry six runes - this case no longer bites")
        self.assertTrue(out["say"], "an empty Base tab does not say why")
        self.assertEqual(out["high"], 48)

    def test_hover_is_the_runeword_on_that_base(self):
        out = _run(r"""
          mk('Sorceress', 99); pickRw('rarm', 'Breath of the Dying');
          window._cbTipBase(fakeEl('9mp')); OUT.crow = tipHtml();
          window._cbTipBase(fakeEl('7wa')); OUT.bers = tipHtml();
          OUT.entry = window._cbBaseEntry('9mp');
        """)
        for key, base in (("crow", "Crowbill"), ("bers", "Berserker Axe")):
            h = out[key] or ""
            self.assertIn(base, h, "hovering %s did not draw the runeword on it" % base)
            self.assertIn("Breath of the Dying", h)
            self.assertNotIn("Crystal Sword", h, "the hover box shows the runeword on its first base, not the hovered one")
        self.assertEqual((out["entry"]["base"], out["entry"]["ilvl"]), ("9mp", 99))

    def test_a_click_wears_it_on_that_base_and_edit_goes_back_to_base(self):
        out = _run(r"""
          mk('Sorceress', 99); pickRw('rarm', 'Breath of the Dying');
          OUT.click = window._cbPickBase('9mp');
          var s = cur().sets[0].slots.rarm; OUT.worn = s && [s.id, s.base, s.sockets, s.socketed.length];
          OUT.tab = window._cbState().pick.tab; OUT.tabs = tabs();
          var m = /id="cb-base" onclick="([^"]*)"[^>]*>([^<]*)</.exec(MODAL._html); OUT.ctl = m && [unesc(m[1]), unesc(m[2])];
          if (m) new Function(unesc(m[1]))();
          OUT.back = [window._cbState().pick.tab, baseRows().length];
          OUT.refused = window._cbPickBase('ssd'); OUT.still = cur().sets[0].slots.rarm.base;
          OUT.change = window._cbPickBase('7wa'); OUT.now = [cur().sets[0].slots.rarm.id, cur().sets[0].slots.rarm.base, window._cbState().pick.tab];
        """)
        self.assertIs(out["click"], True)
        self.assertEqual(out["worn"][1:], ["9mp", 6, 6], "clicking Crowbill did not wear Breath of the Dying on it, six runes in")
        self.assertEqual((out["tab"], out["tabs"]), ("edit", ["Select", "Base", "Edit*"]))
        self.assertIsNotNone(out["ctl"], "Edit has no Base control")
        self.assertIn("Crowbill", out["ctl"][1])
        self.assertEqual(out["back"], ["base", 48], "Edit's Base control did not go back to the Base tab")
        self.assertIs(out["refused"], False, "a Short Sword (two sockets) was taken for six runes")
        self.assertEqual(out["still"], "9mp")
        self.assertIs(out["change"], True)
        self.assertEqual(out["now"], [out["worn"][0], "7wa", "edit"], "a new base on the worn runeword did not stick")

    def test_the_search_match_is_underlined_and_the_filters_narrow(self):
        out = _run(r"""
          mk('Sorceress', 99); pickRw('rarm', 'Breath of the Dying');
          window._cbBaseSearch('axe'); OUT.axe = baseRows().map(function(r){ return r[0]; }); OUT.u = /Giant <u>Axe<\/u>/.test(MODAL._html);
          window._cbBaseSearch(''); window._cbFiltToggle(); window._cbBaseFilt('e');
          OUT.elite = baseRows().map(function(r){ return r[1]; });
          window._cbClosePick(); window._cbOpenPick('slot', 'head'); window._cbPickSearch('crown'); window._cbModal();
          OUT.sel = /<u>Crown<\/u> of Ages/.test(MODAL._html);
        """)
        want = [n for _, ns in THEIRS["Breath of the Dying"] for n in ns if "axe" in n.lower()]
        self.assertGreaterEqual(len(want), 5, "PRINT THE DENOMINATOR: only %d of their rows say 'axe'" % len(want))
        self.assertEqual(out["axe"], want, "the search did not keep exactly the bases that say 'axe', in their order")
        self.assertTrue(out["u"], "the Base tab's search match is not underlined")
        self.assertTrue(out["elite"] and all(g.startswith("Elite ") for g in out["elite"]), "the Elite filter let another tier in")
        self.assertTrue(out["sel"], "the Select list's search match is not underlined")


@unittest.skipIf(CB.NODE is None, "node is not on this machine")
class TheWeaponRailIsTheGamesTypeTree(unittest.TestCase):

    def test_the_tree_is_their_tree_from_the_types_ancestors(self):
        out = _run(r"""
          mk('Sorceress', 99);
          OUT.tree = window._cbTree('rarm');
          window._cbOpenPick('slot', 'rarm');
          OUT.head = /class="cb-rail-b cb-tree-h cb-on"[^>]*>Weapons and Shields</.test(MODAL._html);
          OUT.melee = /aria-expanded="true" data-node="mele"/.test(MODAL._html); OUT.axes = /aria-expanded="false" data-node="axe"/.test(MODAL._html);
          OUT.taxeDrawn = (MODAL._html.match(/data-node="taxe"/g) || []).length;
          window._cbRailNode('axe'); var d = window._cbDb();
          OUT.axeRows = window._cbPickRows().map(function(x){ return [x[0], window._cbBasesOf(window._cbItem(x[0])).some(function(c){ var b = d.b[c]; return b && (b[1] === 'axe' || (d.anc[b[1]] || {}).axe); })]; });
          OUT.list = window._cbForSlot('rarm').map(function(x){ return x[1]; });
        """)
        tree = out["tree"]
        kids = {}
        stack = []
        for t, label, depth, _ in tree:
            del stack[depth:]
            if stack and label not in kids.setdefault(stack[-1], []):   # a type under two parents is drawn under each
                kids[stack[-1]].append(label)
            stack.append(label)
        self.assertEqual([r[1] for r in tree if r[2] == 0], ["Shields", "Melee Weapons", "Missile Weapons", "Orbs", "Thrown Weapons"])
        self.assertEqual(kids["Shields"], ["Auric Shields", "Voodoo Heads", "Grimoires"])
        self.assertEqual(kids["Melee Weapons"], ["Axes", "Swords", "Daggers", "Spears", "Polearms", "Clubs", "Hammers", "Maces",
                                                 "Scepters", "Wands", "Staves", "Claws"])
        self.assertEqual(kids["Missile Weapons"], ["Bows", "Crossbows"])
        self.assertEqual(kids["Thrown Weapons"][:3], ["Throwing Axes", "Throwing Knives", "Javelins"])
        self.assertEqual(kids["Thrown Weapons"][3:], ["Missile Potions"], "Thrown Weapons holds a type the data does not put there")
        for parent, want in (("Axes", ["Throwing Axes"]), ("Daggers", ["Throwing Knives"]), ("Spears", ["Amazon Spears", "Javelins"]),
                             ("Bows", ["Amazon Bows"]), ("Javelins", ["Amazon Javelins"])):
            self.assertEqual(kids.get(parent), want, "%s's children are not the Equiv tree's" % parent)
        self.assertNotIn("Claws", kids, "Hand to Hand 2 was drawn as its own Claws under Claws")
        self.assertTrue(out["head"], "the rail's header is not 'Weapons and Shields', selected")
        self.assertTrue(out["melee"] and out["axes"], "the first level is not open / the second not folded, as theirs")
        self.assertEqual(out["taxeDrawn"], 1, "Throwing Axes is drawn %d times with Axes folded (their tree: once, under "
                                              "Thrown Weapons)" % out["taxeDrawn"])
        rows = out["axeRows"]
        self.assertGreaterEqual(len(rows), 40, "PRINT THE DENOMINATOR: the Axes node listed only %d items" % len(rows))
        self.assertEqual([r[0] for r in rows if not r[1]], [], "the Axes node listed items with no axe base")
        ids = [r[0] for r in rows]
        self.assertIn("b:tax", ids, "the Axes node does not list a Throwing Axe (a type below it)")
        self.assertNotIn("b:ssd", ids, "the Axes node lists a Short Sword")
        for n in ("Aegis", "Ancient Shield", "Stormshield"):
            self.assertIn(n, out["list"], "the weapon slot's list does not carry %s (theirs lists shields there)" % n)


    def test_a_non_barbarians_left_hand_keeps_the_second_weapons_row(self):
        out = _run(r"""
          mk('Sorceress', 99);
          OUT.tree = window._cbTree('larm');
          window._cbOpenPick('slot', 'larm');
          OUT.drawn = /data-node="@offhand"[^>]*>Second Weapons \(Barbarian\)</.test(MODAL._html);
          OUT.whole = window._cbPickRows().map(function(x){ return x[0]; });
          window._cbRailNode('@offhand'); OUT.node = window._cbPickRows().map(function(x){ return x[0]; });
          window._cbRailNode(''); window._cbQt('r'); window._cbChoose(rwId('Spirit'));
          OUT.baseTab = window._cbState().pick.tab; OUT.baseDrawn = /data-node="@offhand"/.test(MODAL._html);
          mk('Barbarian', 99); OUT.barb = window._cbTree('larm');
          OUT.barbWhole = window._cbForSlot('larm').map(function(x){ return x[0]; });
        """)
        db = CB._db()
        off = sorted("b:" + c for c, b in db["b"].items()
                     if b[20] and b[21] == "w" and b[14] in (1, 12) and (db["ty"].get(b[1]) or [None, None, None])[2] == -1)
        self.assertGreaterEqual(len(off), 40, "PRINT THE DENOMINATOR: the block holds only %d one-handed classless weapon bases" % len(off))
        last = out["tree"][-1]
        self.assertEqual((last[0], last[1], last[2]), ("@offhand", "Second Weapons (Barbarian)", 0),
                         "a Sorceress's left-hand rail lost the Second Weapons (Barbarian) row the flat rail had")
        self.assertTrue(out["drawn"], "the row is in the tree but not drawn on the rail")
        self.assertEqual(sorted(i for i in out["node"] if i.startswith("b:")), off,
                         "the Second Weapons row does not list exactly the block's one-handed classless weapon bases")
        lsab = [x[0] for x in db["it"] if x[1] == "Lightsabre" and x[2] == "u"]
        self.assertTrue(lsab and lsab[0] in out["node"], "the Second Weapons row does not list Lightsabre")
        self.assertFalse(any(i.startswith("b:") and db["b"][i[2:]][1] in ("shie", "ashd") for i in out["node"]), "the row lists a shield")
        self.assertEqual([i for i in out["whole"] if i in set(off)], [], "a Sorceress's whole left-hand list holds second weapons")
        self.assertEqual(out["baseTab"], "base")
        self.assertFalse(out["baseDrawn"], "the Base tab of a Sorceress's left hand draws the Second Weapons row (it holds none)")
        self.assertNotIn("@offhand", [r[0] for r in out["barb"]], "a Barbarian got the marked row as well as the weapon types")
        self.assertIn("Swords", [r[1] for r in out["barb"]])
        self.assertTrue(lsab[0] in out["barbWhole"], "a Barbarian's whole left-hand list holds no Lightsabre")

RED_PROOF = [
    {
        "why": "#174 v-B4 - a runeword is worn on its first base again, no Base tab (ours before: Crystal Sword)",
        "file": "bible.html",
        "find": "    if (it[2] === 'r' && p.kind === 'slot'){ p.rw = id; p.tab = 'base';",
        "replace": "    if (false){ p.rw = id; p.tab = 'base';",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the tiers run Normal first (theirs: Elite, Exceptional, Normal)",
        "file": "bible.html",
        "find": "(y.tier - x.tier) || (y.q - x.q) || (x.rq - y.rq)",
        "replace": "(x.tier - y.tier) || (y.q - x.q) || (x.rq - y.rq)",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - a Sorceress is offered the Amazon's spears (their Sorceress list holds none)",
        "file": "bible.html",
        "find": "return !!b && _cbMaxSock(c, lv) >= n && !(ci >= 0 && t && t[2] >= 0 && t[2] !== ci); });",
        "replace": "return !!b && _cbMaxSock(c, lv) >= n; });",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the item level no longer holds the socket count (every base at 99)",
        "file": "bible.html",
        "find": "return !!b && _cbMaxSock(c, lv) >= n && !(ci",
        "replace": "return !!b && _cbMaxSock(c, 99) >= n && !(ci",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the weapon hand lists a sword-and-shield runeword's shields (their Spirit: 24 swords)",
        "file": "bible.html",
        "find": "    var rows = inCats(own); if (!rows.length) rows = inCats(every);\n",
        "replace": "    var rows = inCats(every);\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - hovering a base shows the runeword on its first base",
        "file": "bible.html",
        "find": "    e.base = code; e.ilvl = c0.ilvl;\n",
        "replace": "    e.ilvl = c0.ilvl;\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - clicking a base wears the runeword on its first base",
        "file": "bible.html",
        "find": "    if (p.rw){ var e = _cbEntryFor(c0.it); e.base = code; p.rw = null; return _cbEquip(c0.it, e); }\n",
        "replace": "    if (p.rw){ var e = _cbEntryFor(c0.it); p.rw = null; return _cbEquip(c0.it, e); }\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - Edit's Base control no longer goes back to the Base tab",
        "file": "bible.html",
        "find": "id=\"cb-base\" onclick=\"window._cbPickTab(\\'base\\')\"",
        "replace": "id=\"cb-base\" onclick=\"window._cbPickTab(\\'select\\')\"",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the Base tab's search match is not underlined",
        "file": "bible.html",
        "find": "+ _cbUnderline(esc(d.b[r[0]][0]), q) + '</button>';",
        "replace": "+ esc(d.b[r[0]][0]) + '</button>';",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the tree hangs a type under every ancestor (Throwing Axes under Melee Weapons too)",
        "file": "bible.html",
        "find": "      parents[n] = cand.filter(function(p){ return !cand.some(function(q){ return q !== p && anc[q][p]; }); });\n",
        "replace": "      parents[n] = cand;\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - a tree node lists everything in the hand, not its type and below",
        "file": "bible.html",
        "find": "    if (p.node && CB_HANDS[slot]){ var nc = _cbSlotCats(slot); rows = rows.filter(function(x){ return _cbNodeHas(x, nc, p.node); }); }",
        "replace": "    if (false){ var nc = _cbSlotCats(slot); rows = rows.filter(function(x){ return _cbNodeHas(x, nc, p.node); }); }",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the weapon slot drops the shields their weapon list carries (Aegis, Ancient Shield)",
        "file": "bible.html",
        "find": "    if (slot === 'rarm' && d) cats = cats.concat(",
        "replace": "    if (false) cats = cats.concat(",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 review - the tree drops the flat rail's Second Weapons (Barbarian) row for every other class",
        "file": "bible.html",
        "find": "    if (oc) list.push({ t: CB_OFF_NODE,",
        "replace": "    if (false) list.push({ t: CB_OFF_NODE,",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if CB.NODE is None:
        sys.stderr.write("⚪ SKIP — node is not on this machine, so the Base tab was not driven. UNMEASURED, declared (77).\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
