# -*- coding: utf-8 -*-
"""#174 v-B4 — THE MULE WINDOW'S SLOT PICKER OFFERS THE WHOLE ITEM DATABASE: ONE PICKER, TWO HOSTS.

His words (2026-09-26, on his ALT Windows PC, v3514): "i still cant see any items at all when i click on any body gear
within the mules ... all three pcs and users need visual verification and the logic needs to be individiually providing
the data and information we made it use". MEASURED on a copy of that PC's store: no d2r_muleAssign, no d2r_muleEquip,
d2r_owned = []. The mule window's picker listed only the locker's own routed rows, so every slot of every mule on that PC
said "Nothing in <mule> fits the Body Armor slot." It was the design, and it was wrong for him.

The fix: a slot of the mule window opens the Character Builder's picker modal in a MULE host - Select over the ENTIRE
database for the slot (CB_DB is on every PC's page, so every PC provides it itself), Base / Quality / Edit exactly as the
builder's, and an "In this locker" tab that IS the old list (its fit rules and footer), first and in front when the locker
has anything for the slot. This law drives the SHIPPED code in node - the vault span (the mule window), the ⟦CHARACTER
BUILDER JS⟧ block, the generated ⟦CB_DB⟧ block and the mule tooltip script, each cut from bible.html by the sibling laws'
own cutters (never re-typed), over a stand-in DOM:

  · THE ALT'S STORE (fresh, no muleAssign, no muleEquip): the Body Armor slot opens on Select, and its list is the
    database's body armors - every spawnable base of the slot's type (derived here from the CB_DB block) and every
    unique / set item on one; nothing of another slot (no Stone of Jordan). "Nothing in <mule> fits" never shows; the
    In this locker tab says the locker holds nothing on this PC and points at Select.
  · WITH LOCKER ITEMS the In this locker tab is in front and lists EXACTLY what the old picker listed: the same names, the
    same footer, word for word the same as the picker drawn without the builder's block on the page (the standalone
    path the other mule laws drive) - and a locker pick still writes {name, source, at} and nothing else.
  · A DATABASE PICK WRITES THE MULE, NEVER A BUILD: Enigma -> its Base tab -> Mage Plate writes the mule's equipment
    {name: 'Enigma', source: 'manual', id, base: 'xtp', q, sockets 3, fill: its runes}; Edit edits that record (item level
    80, the placement keeps its time); the doll wears it LIVE (never "no longer in this locker") and it frees no grid cell;
    the mule's hover is the builder's tooltip function over that entry (Enigma on Mage Plate); a unique goes straight on
    and Edit's Unequip takes it off; and d2r_charBuilds and d2r_cbSel are BYTE-IDENTICAL before and after.
  · Esc closes the host's top layer first (the Filters list), then the picker, then the window.
  · THE BUILDER HOST NEVER WRITES A MULE: a builder pick leaves d2r_muleEquip byte-identical.
  · #174 v-B4 review — THE PICKER IS ON THE HAND HE SEES. Swapping I / II with a hand's picker open re-aims it: Edit shows
    set II's Lightsabre and an item level typed there lands on set II (set I's Windforce untouched); a pick onto an empty
    set II lands on set II and the doll on screen wears it. (It read the set on screen and wrote the set it opened on:
    Windforce was silently replaced, and a pick onto set II vanished into set I.)
  · A PICK HIDES THE HOVERED ROW'S TOOLTIP in the mule host, as in the builder (a unique picked there left #cb-tip standing
    over Edit - on a phone over the whole sheet).
  · A LOCKER HAS NO CLASS, SO ITS LEFT HAND TAKES A SECOND WEAPON: Select over the database lists Lightsabre and Stormlash
    for it (In this locker already did), and the rail's tree carries Swords.

⚠ WHAT THIS LAW CANNOT SEE: pixels and a real pointer - the mule window's width law drives the picker with real input,
and the builder's report carries the 2000x1300 PNGs of a mule window on an empty store.
RED_PROOF below.
"""
import io
import json
import os
import re
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

import test_the_mule_window_equips_and_says_its_source as EQ  # noqa: E402  the mule harness, one cut
import test_the_character_builder_is_their_builder as CB  # noqa: E402  the builder's cutters
import test_the_character_builder_is_joined_to_the_engine_and_the_mule_window as JN  # noqa: E402  the tooltip script's cutter
from test_the_mule_window_is_the_planner_shell import _vault_span, _static_attrs  # noqa: E402

NODE = EQ.NODE


def _harness():
    """the mule law's own stand-in DOM, taught three more things the builder's block asks for: its database element,
    elements it creates, and appending them - each edit anchored once, so a moved harness fails loudly here"""
    h = EQ.HARNESS
    edits = [
        ("var box = mkEl(%(attrs)s), _html = '';",
         "var DBEL = { textContent: %(db)s }, MADE = {};\nvar box = mkEl(%(attrs)s), _html = '';"),
        ("  getElementById: function(id){ return id === 'vault-detail' ? box : null; },",
         "  getElementById: function(id){ if (id === 'cb-db') return DBEL; if (id === 'vault-detail') return box; return MADE[id] || null; },\n"
         "  createElement: function(){ var e = mkEl({}); e.style = {}; e.focus = function(){};\n"
         "    e.getBoundingClientRect = function(){ return { left: 0, top: 0, width: 100, height: 40, right: 100, bottom: 40 }; }; return e; },"),
        ("var body = { appendChild: function(el){ el.parentElement = body; } };",
         "var body = { appendChild: function(el){ el.parentElement = body; if (el.id) MADE[el.id] = el; return el; } };"),
    ]
    for a, b in edits:
        assert h.count(a) == 1, "the mule harness moved - this law's anchor %r matches %d times" % (a[:60], h.count(a))
        h = h.replace(a, b)
    return h


#: helpers the cases share, over the stand-in DOM's HTML
HELP = r"""
function st(){ return window._cbState(); }
function strip(h){ return unesc(String(h).replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim(); }
function modalHtml(){ var h = box.innerHTML, i = h.indexOf('id="cb-modal"'); return i < 0 ? null : h.slice(h.lastIndexOf('<div', i)); }
function hostTabs(){ var h = modalHtml() || '', re = /role="tab" class="cb-tab( cb-on)?"( disabled)? aria-selected="[a-z]+" onclick="window\._cbPickTab\('([a-z]+)'\)">([^<]*)</g, m, o = [];
  while ((m = re.exec(h))) o.push(m[4] + (m[1] ? '*' : '') + (m[2] ? '(off)' : '')); return o; }
function listIds(){ var h = modalHtml() || '', re = /class="cb-opt cb-c-[a-z]+" data-id="([^"]+)"/g, m, o = []; while ((m = re.exec(h))) o.push(unesc(m[1])); return o; }
function itemId(n, q){ var h = null; window._cbDb().it.forEach(function(x){ if (x[1] === n && (!q || x[2] === q)) h = x[0]; }); return h; }
function slotEl(slot, name){
  var art = { getAttribute: function(k){ return k === 'aria-label' ? name : null; } };
  var el = { nodeType: 1, getAttribute: function(k){ return k === 'data-slot' ? slot : null; }, hasAttribute: function(){ return false; },
    setAttribute: function(){}, removeAttribute: function(){}, contains: function(){ return false; },
    matches: function(sel){ return /\.mp-slot/.test(sel); },
    querySelector: function(sel){ return /d2art-wrap/.test(sel) ? art : null; },
    closest: function(sel){ return /\.mp-slot/.test(sel) ? el : null; },
    getBoundingClientRect: function(){ return { left: 0, top: 0, width: 60, height: 90, right: 60, bottom: 90 }; } };
  return el;
}
"""


def _drive(scenario, assign=None, store=None, builder=True):
    """the shipped mule window (+ the builder's block and the mule tooltip script when `builder`), one node program"""
    s = EQ._src()
    tables = EQ._line(s, "const ITEM_CODEX = {") + EQ._line(s, "const ITEM_TIP = {") + EQ._sets_and_runewords(s)
    helpers = (EQ._line(s, "  var RK='d2r_muleRoster', AK='d2r_muleAssign';")
               + EQ._line(s, "  function saveR(){ window.LSR.setItem(RK, JSON.stringify(roster)); }")
               + EQ._line(s, "  function art(n, glyph, size){")
               + EQ._line(s, "  function esc(t){ return String(t)")
               + EQ._line(s, "  function jsArg(t){")
               + EQ._between(s, "  function tipOf(n){", "  // RoW shared-stash items never get a mule"))
    extra = (CB._builder_js(s) + "\n" + JN._tip_js(s) + "\n") if builder else ""
    js = _harness() % {
        "store": json.dumps(store or {}), "attrs": json.dumps(_static_attrs()), "db": json.dumps(CB._db_json(s)),
        "assign": json.dumps(assign if assign is not None else {}), "copies": json.dumps({}),
        "tables": tables, "helpers": helpers, "span": _vault_span(), "scenario": extra + HELP + scenario,
    }
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise AssertionError("the shipped mule window + picker would not run - UNKNOWN, not passing: %s" % r.stderr[-1500:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def _db():
    return CB._db()


#: a build he already has, which a mule pick must never touch (and its selection key)
BUILDS = json.dumps({"b1": {"name": "Konyoress", "cls": "Sorceress", "level": 80, "sets": [{"name": "Set 1", "slots": {},
                     "inv": [], "swap": {}, "ws": 1}], "active": 0, "notes": "mine", "stash": [], "from": None, "at": 1}})


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheAltsEmptyStoreGetsTheWholeDatabase(unittest.TestCase):

    def test_body_armor_on_an_empty_store_lists_the_databases_body_armors(self):
        out = _drive("""
          window.openMuleCard('uni-armor'); window._mpPick('tors');
          out.host = st().pick && st().pick.host; out.tab = st().pick && st().pick.tab; out.tabs = hostTabs();
          out.ids = listIds(); out.nothing = /Nothing in [^<]* fits the /.test(box.innerHTML); out.names = window._cbPickRows().length;
          window._cbPickTab('locker'); out.lockerSays = strip((modalHtml() || '').replace(/[\\s\\S]*?<div class="cb-mb cb-mb-locker">/, ''));
          out.lockerNothing = /Nothing in [^<]* fits the /.test(box.innerHTML);
          out.store = [STORE['d2r_muleAssign'] || null, STORE['d2r_muleEquip'] || null];""")
        self.assertEqual(out["store"], [None, None], "the fixture is not the ALT's store (no muleAssign, no muleEquip)")
        self.assertEqual((out["host"], out["tab"]), ("mule", "select"),
                         "an empty locker's Body Armor did not open the builder's picker on the whole database")
        self.assertEqual(out["tabs"], ["In this locker", "Select*", "Edit(off)"])
        self.assertFalse(out["nothing"], "an empty store still says 'Nothing in <mule> fits'")
        db = _db()
        types = set(t for row in db["rail"]["tors"] for t in row[1])
        bases = set("b:" + c for c, b in db["b"].items() if b[20] and b[1] in types)
        uni = set(x[0] for x in db["it"] if x[2] in ("u", "s") and db["b"].get(x[3], [None, None])[1] in types)
        self.assertGreaterEqual(len(bases), 40, "PRINT THE DENOMINATOR: the block holds only %d body-armor bases" % len(bases))
        self.assertGreaterEqual(len(uni), 30, "PRINT THE DENOMINATOR: the block holds only %d body-armor uniques/sets" % len(uni))
        ids = set(out["ids"])
        self.assertEqual(sorted(i for i in ids if i.startswith("b:")), sorted(bases),
                         "the Body Armor list's bases are not every spawnable body armor in the database")
        self.assertEqual(sorted(uni - ids), [], "body-armor uniques / set items missing from the list")
        soj = [x[0] for x in db["it"] if x[1] == "The Stone of Jordan"]
        self.assertTrue(soj and soj[0] not in ids, "a ring was offered for the Body Armor")
        self.assertEqual(len(out["ids"]), out["names"], "the drawn list is not the picker's rows")
        self.assertIn("UNI-ARMOR holds no items in this PC’s store", out["lockerSays"])
        self.assertIn("Select lists every item in the database for the body armor slot", out["lockerSays"])
        self.assertFalse(out["lockerNothing"], "the In this locker tab of an EMPTY store still says 'Nothing in ... fits'")


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class InThisLockerIsTheOldList(unittest.TestCase):

    SCENARIO = """
      window.openMuleCard('uni-armor');
      window._mpPick('head'); out.headTab = window._cbState ? (st().pick || {}).tab : null; out.head = options(); out.headFoot = footer();
      window._mpPick('rrin'); out.rrin = options(); out.chose = choose('The Stone of Jordan');
      window._mpPick('lrin'); out.lrin = options(); out.lrinFoot = footer();
      window._mpPick('feet'); out.feetTab = window._cbState ? (st().pick || {}).tab : null;
      if (window._cbPickTab) window._cbPickTab('locker'); out.feet = options(); out.feetFoot = footer();
      out.feetSays = /Nothing in UNI-ARMOR fits the boots slot\\./.test(box.innerHTML);
      out.soj = eq()['uni-armor'].setI.rrin;"""

    def test_the_locker_tab_lists_exactly_what_the_old_picker_listed(self):
        assign = dict((n, EQ.MULE) for n in EQ.LOCKER)
        hosted = _drive(self.SCENARIO, assign=assign)
        alone = _drive(self.SCENARIO, assign=assign, builder=False)
        self.assertEqual(hosted["headTab"], "locker", "a locker with a helm did not open on In this locker")
        self.assertEqual(hosted["head"], ["Harlequin Crest (Shako)"])
        self.assertIn("Left out: 9 of 10", hosted["headFoot"])
        self.assertEqual(sorted(hosted["rrin"]), ["Beast Bite Ring", "Nagelring", "The Stone of Jordan"])
        self.assertIs(hosted["chose"], True)
        self.assertEqual(sorted(hosted["lrin"]), ["Beast Bite Ring", "Nagelring"])
        self.assertIn("1 is already worn in another slot: The Stone of Jordan", hosted["lrinFoot"])
        self.assertEqual(hosted["feetTab"], "select", "a locker with nothing for the boots opened on its empty list, not Select")
        self.assertTrue(hosted["feetSays"], "the boots' In this locker tab lost the old picker's words")
        for k in ("head", "headFoot", "rrin", "lrin", "lrinFoot", "feet", "feetFoot"):
            self.assertEqual(hosted[k], alone[k], "In this locker's %s is not what the old picker drew: %r vs %r" % (k, hosted[k], alone[k]))
        self.assertEqual(sorted(hosted["soj"]), ["at", "name", "source"], "a locker pick carries more than {name, source, at}")
        self.assertEqual(hosted["soj"]["source"], "manual")


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class ADatabasePickWritesTheMuleNeverABuild(unittest.TestCase):

    def test_a_pick_is_manual_on_the_mules_doll_and_the_builds_are_byte_identical(self):
        out = _drive("""
          var before = STORE['d2r_charBuilds'], beforeSel = STORE['d2r_cbSel'];
          window.openMuleCard('uni-armor'); window._mpPick('tors');
          window._cbQt('r'); window._cbChoose(itemId('Enigma', 'r')); out.baseTab = st().pick.tab;
          out.picked = window._cbPickBase('xtp'); out.afterPick = st().pick && st().pick.tab;
          out.rec = eq()['uni-armor'].setI.tors;
          window._cbEdit('ilvl', 80); out.rec2 = eq()['uni-armor'].setI.tors;
          var L = window._mpLive('uni-armor', eq()); out.live = !!L.at.setI.tors; out.dead = L.dead;
          out.worn = window._mpWornFor('uni-armor', eq()); out.slotSay = slotSay('tors');
          var got = null; window.d2Tip.show = function(e){ got = e; };
          window._mpPick(null); fire('mouseover', { target: slotEl('tors', 'Enigma') });
          out.tip = got && { name: got.name, base: got.base };
          window._mpPick('head'); window._cbChoose(itemId('Harlequin Crest', 'u')); out.head = eq()['uni-armor'].setI.head; out.headTab = st().pick && st().pick.tab;
          window._cbUnequip(); out.headGone = !eq()['uni-armor'].setI.head;
          out.buildsSame = STORE['d2r_charBuilds'] === before; out.selSame = STORE['d2r_cbSel'] === beforeSel;""",
                     store={"d2r_charBuilds": BUILDS, "d2r_cbSel": "b1"})
        self.assertEqual(out["baseTab"], "base", "a runeword picked in the mule host did not wait on its Base tab")
        self.assertIs(out["picked"], True)
        self.assertEqual(out["afterPick"], "edit")
        r = out["rec"]
        self.assertEqual((r["name"], r["source"], r["id"], r["base"], r["q"], r["sockets"], len(r["fill"])),
                         ("Enigma", "manual", r["id"], "xtp", "r", 3, 3), "the mule's record is not the builder's entry, placed by hand")
        self.assertTrue(r["id"].startswith("r"))
        self.assertEqual((out["rec2"]["ilvl"], out["rec2"]["at"]), (80, r["at"]), "Edit did not edit the mule's record in place")
        self.assertTrue(out["live"], "the database pick is not worn: %s" % out["dead"])
        self.assertEqual(out["worn"], {}, "a database pick freed a grid cell it never held")
        self.assertIn("from the item database", out["slotSay"]["say"])
        self.assertEqual(out["tip"], {"name": "Enigma", "base": "Mage Plate"},
                         "the mule's hover is not the builder's tooltip over the stored entry")
        self.assertEqual((out["head"]["name"], out["head"]["source"], out["headTab"]), ("Harlequin Crest", "manual", "edit"))
        self.assertTrue(out["headGone"], "Edit's Unequip did not take the unique off the mule")
        self.assertTrue(out["buildsSame"], "a mule pick touched d2r_charBuilds")
        self.assertTrue(out["selSame"], "a mule pick touched d2r_cbSel")

    def test_esc_closes_the_hosts_top_layer_then_the_picker_then_the_window(self):
        out = _drive("""
          window.openMuleCard('uni-armor'); window._mpPick('tors'); window._cbFiltToggle();
          fire('keydown', { key: 'Escape' }); out.e1 = [st().filtOpen, !!st().pick, !!modalHtml()];
          fire('keydown', { key: 'Escape' }); out.e2 = [!!st().pick, !!modalHtml(), box.hidden];
          fire('keydown', { key: 'Escape' }); out.e3 = box.hidden;""")
        self.assertEqual(out["e1"], [False, True, True], "the first Esc did not close the Filters list alone")
        self.assertEqual(out["e2"], [False, False, False], "the second Esc did not close the picker (and only it)")
        self.assertIs(out["e3"], True, "the third Esc did not close the window")

    def test_the_builder_host_never_writes_a_mule(self):
        mine = json.dumps({"uni-armor": {"setI": {"head": {"name": "Shako", "source": "manual", "at": "2026-09-26T00:00:00Z"}}}})
        out = _drive("""
          var before = STORE['d2r_muleEquip'];
          window.openCharBuilder(); window._cbOpenPick('slot', 'tors'); out.ok = window._cbChoose(itemId("Tyrael's Might", 'u'));
          var b = JSON.parse(STORE['d2r_charBuilds'] || '{}'), k = Object.keys(b)[0];
          out.built = k ? b[k].sets[0].slots.tors.name : null; out.same = STORE['d2r_muleEquip'] === before;""",
                     store={"d2r_muleEquip": mine})
        self.assertEqual(out["built"], "Tyrael's Might", "the builder host's pick did not land in the build")
        self.assertTrue(out["same"], "a builder pick wrote d2r_muleEquip")



#: set I's right hand holds Windforce and set II's Lightsabre - both database picks, as the mule host writes them
def _two_sets(ids):
    rec = lambda name, at: {"name": name, "source": "manual", "id": ids[name], "base": ids[name + " base"], "q": "u",
                               "rolls": {}, "sockets": 0, "eth": False, "ilvl": 99, "fill": [], "at": at}
    return json.dumps({"uni-weap": {"setI": {"rarm": rec("Windforce", "2026-09-26T10:00:00.000Z")},
                                    "setII": {"rarm": rec("Lightsabre", "2026-09-26T10:00:01.000Z")}}})


def _ids():
    db = _db()
    out = {}
    for n in ("Windforce", "Lightsabre"):
        hit = [x for x in db["it"] if x[1] == n and x[2] == "u"]
        assert len(hit) == 1, "PRINT THE DENOMINATOR: the block holds %d uniques named %s" % (len(hit), n)
        out[n], out[n + " base"] = hit[0][0], hit[0][3]
    return out


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheHostKeepsToTheHandHeSees(unittest.TestCase):
    """#174 v-B4 review - three defects the review reproduced with a real mouse on the shipped modal"""

    def test_a_swap_with_the_picker_open_moves_it_to_the_set_on_screen(self):
        ids = _ids()
        out = _drive("""
          window.openMuleCard('uni-weap'); window._mpPick('rarm');
          out.editI = (st().host.cur() || {}).name;
          window._mpSet('swap', 2); out.editII = (st().host.cur() || {}).name; out.tabII = st().pick && st().pick.tab;
          window._cbEdit('ilvl', 80);
          var e = eq()['uni-weap']; out.I = [e.setI.rarm.name, e.setI.rarm.ilvl]; out.II = [e.setII.rarm.name, e.setII.rarm.ilvl];""",
                     assign=EQ._hands_locker(), store={"d2r_muleEquip": _two_sets(ids)})
        self.assertEqual(out["editI"], "Windforce", "the fixture's set I is not on screen when the mule opens")
        self.assertEqual((out["editII"], out["tabII"]), ("Lightsabre", "edit"),
                         "after I -> II with the picker open, Edit does not show the hand on screen")
        self.assertEqual(out["I"], ["Windforce", 99], "an edit made on set II's hand changed set I (Windforce replaced)")
        self.assertEqual(out["II"], ["Lightsabre", 80], "the item level typed on set II's Lightsabre did not land on it")
        # the second shape: set II empty - a pick after the swap lands on set II and the doll on screen wears it
        out = _drive("""
          window.openMuleCard('uni-weap'); window._mpPick('rarm'); window._cbQt('u'); window._cbChoose(itemId('Windforce', 'u'));
          window._mpSet('swap', 2); out.tab = st().pick && st().pick.tab;
          window._cbPickTab('select'); window._cbQt('u'); out.ok = window._cbChoose(itemId('Lightsabre', 'u'));
          var e = eq()['uni-weap']; out.I = e.setI && e.setI.rarm && e.setI.rarm.name; out.II = e.setII && e.setII.rarm && e.setII.rarm.name;
          out.doll = slotSay('rarm').say;""", assign=EQ._hands_locker())
        self.assertIs(out["ok"], True)
        self.assertEqual((out["I"], out["II"]), ("Windforce", "Lightsabre"),
                         "a pick made after I -> II did not land on set II (the set on screen)")
        self.assertIn("Lightsabre", out["doll"], "the doll on screen (set II) does not wear the pick: %r" % out["doll"])

    def test_a_pick_hides_the_hovered_rows_tooltip(self):
        out = _drive("""
          window.openMuleCard('uni-armor'); window._mpPick('head'); window._cbPickTab('select'); window._cbQt('u');
          var id = itemId('Harlequin Crest', 'u');
          window._cbTipRow({ getAttribute: function(k){ return k === 'data-id' ? id : null; },
                             getBoundingClientRect: function(){ return { left: 0, top: 0, width: 90, height: 18, right: 90, bottom: 18 }; } });
          out.shown = window.d2Tip.shown(); out.ok = window._cbChoose(id); out.after = window.d2Tip.shown(); out.tab = st().pick.tab;""")
        self.assertIs(out["shown"], True, "the hovered row drew no tooltip - this case cannot bite")
        self.assertEqual((out["ok"], out["tab"]), (True, "edit"))
        self.assertIs(out["after"], False, "a unique picked in the mule host left the hovered row's tooltip over Edit")

    def test_a_lockers_left_hand_lists_the_second_weapons(self):
        out = _drive("""
          window.openMuleCard('uni-weap'); window._mpPick('larm'); out.first = st().pick.tab; out.locker = options();
          window._cbPickTab('select'); var names = window._cbPickRows().map(function(x){ return x[1]; });
          out.has = ['Lightsabre', 'Stormlash', 'Stormshield'].filter(function(n){ return names.indexOf(n) >= 0; });
          out.tree = window._cbTree('larm').map(function(r){ return r[1]; });""", assign=EQ._hands_locker())
        self.assertIn("Lightsabre", out["locker"], "the fixture's In this locker no longer offers Lightsabre for the left hand")
        self.assertEqual(out["has"], ["Lightsabre", "Stormlash", "Stormshield"],
                         "Select over the database lists no second weapon for a locker's left hand (a locker has no class)")
        self.assertIn("Swords", out["tree"], "the left hand's tree has no weapon types for a locker")
        self.assertNotIn("Second Weapons (Barbarian)", out["tree"], "a locker was given the non-Barbarian's marked row")


RED_PROOF = [
    {
        "why": "#174 v-B4 - the mule's slot opens the locker-only picker again (his ALT: 'Nothing in <mule> fits' everywhere)",
        "file": "bible.html",
        "find": "      var _hosted = typeof window._cbHostHtml === 'function';\n",
        "replace": "      var _hosted = false;\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - an empty locker opens on its empty list instead of the database",
        "file": "bible.html",
        "find": "    if (p.tab === 'auto') p.tab = (st.host.locker.n > 0) ? 'locker' : 'select';\n",
        "replace": "    if (p.tab === 'auto') p.tab = 'locker';\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the In this locker tab no longer draws the old list",
        "file": "bible.html",
        "find": "return head + '<div class=\"cb-mb cb-mb-locker\">' + ((st.host && st.host.locker && st.host.locker.html) || '') + '</div>';",
        "replace": "return head + '<div class=\"cb-mb cb-mb-locker\"></div>';",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the empty store's locker tab says 'Nothing in <mule> fits' again",
        "file": "bible.html",
        "find": "      var _none = names.length ? 'Nothing in '",
        "replace": "      var _none = true ? 'Nothing in '",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - a mule pick leaks into d2r_charBuilds (the #245/#246 separation)",
        "file": "bible.html",
        "find": "      var mb = _cbMuleBuild(); mut(mb);\n",
        "replace": "      var mb = _cbMuleBuild(); mut(mb); window.LSR.setItem('d2r_charBuilds', JSON.stringify({ leak: mb }));\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the mule's record drops the builder's entry (no id / base: the hover and Edit lose the item)",
        "file": "bible.html",
        "find": "      MP_CB_FIELDS.forEach(function(k){ if (entry[k] !== undefined",
        "replace": "      [].forEach(function(k){ if (entry[k] !== undefined",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - a database pick reads 'no longer in this locker' and is not worn",
        "file": "bible.html",
        "find": "        if (e.source !== 'import' && !e.id && assign[e.name] !== muleId){",
        "replace": "        if (e.source !== 'import' && assign[e.name] !== muleId){",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - a database pick frees a grid cell it never held",
        "file": "bible.html",
        "find": "        if (e.source !== 'import' && !e.id) out[e.name] = (out[e.name] || 0) + 1;",
        "replace": "        if (e.source !== 'import') out[e.name] = (out[e.name] || 0) + 1;",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the mule's hover re-reads a database pick by its name (Enigma with no base)",
        "file": "bible.html",
        "find": "    var entry = (_ce && _cit && typeof window._cbTipEntry === 'function') ? window._cbTipEntry(_ce, _cit, null, slot) : entryFor(n, slot), t = el.getAttribute('title');\n",
        "replace": "    var entry = entryFor(n, slot), t = el.getAttribute('title');\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - Esc closes the picker while its Filters list is open (the top layer is skipped)",
        "file": "bible.html",
        "find": "    if (typeof window._cbHostEsc === 'function' && window._cbHostEsc()) return;",
        "replace": "    if (false) return;",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 review - the picker keeps the set it opened on after I / II: Edit shows set II, the write goes to set I",
        "file": "bible.html",
        "find": "      if (MP_WEAPON_SLOT[_mpPickAt.slot] && _mpPickAt.set !== _mpSetOf(_mpPickAt.slot, _mpSwap)){\n",
        "replace": "      if (false){\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 review - the mule host returns before the tooltip is hidden: a picked unique leaves it over Edit",
        "file": "bible.html",
        "find": "    try { window.d2Tip.hide(); } catch (e) {}\n    if (st.pick && st.pick.host === 'mule'){ if (st.host) st.host.render(); return; }",
        "replace": "    if (st.pick && st.pick.host === 'mule'){ if (st.host) st.host.render(); return; }\n    try { window.d2Tip.hide(); } catch (e) {}",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 review - a locker (no class) is read as a non-Barbarian: its left hand lists no second weapon",
        "file": "bible.html",
        "find": "  function _cbOffOk(){ var bb = _cbBuild(); return !(bb && bb.cls) || bb.cls === 'Barbarian'; }",
        "replace": "  function _cbOffOk(){ var bb = _cbBuild(); return !!(bb && bb.cls === 'Barbarian'); }",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("⚪ SKIP — node is not on this machine, so the mule picker was not driven. UNMEASURED, declared (77).\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
