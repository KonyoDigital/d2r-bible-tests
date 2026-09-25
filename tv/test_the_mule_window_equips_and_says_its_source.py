# -*- coding: utf-8 -*-
"""#174 v-B — THE MULE WINDOW EQUIPS FROM ITS OWN LOCKER, AND EVERY STAT SAYS WHERE ITS NUMBER CAME FROM.

His words: click a doll slot and pick from this mule's items; hover is the board's own item card; the stats are
computed from what is worn. Spec §6 decides how honest each number may be, and this law holds each rule to the
SHIPPED code, driven in node (the vault span of bible.html, the board's own ITEM_CODEX / ITEM_TIP / tipOf, its set
and runeword tables with findSetPiece / _codexSetMember / findRuneword, the routed store and the Backup exporter —
each cut out of bible.html and run, never re-typed here):

  · THE STORE. d2r_muleEquip = {muleId: {setI: {slot: {name, source, at}}, setII: {rarm, larm}}}; only the hands
    swap. A MANUAL placement always wins: an analyzer route (v-E) can never replace what his hand put there, and an
    import cannot either — his hand is testimony, not state.
  · FIT IS DATA. A slot is offered only what this locker holds AND fits it — a ring is never offered for the helm.
    An item whose slot cannot be established is never offered; the picker COUNTS it and says why.
  · EACH NUMBER SAYS ITS SOURCE. Exact (a .d2s import's rolled props) · a RANGE from the item's own text, placed
    by name, drawn as a range and never averaged · UNKNOWN with the reason · and a mix reads "≥ exact + range".
    A measured zero beside an UNKNOWN part is still UNKNOWN. [[unknown-stays-unknown]]
  · THE STORE IS ACCOUNT STATE: it forks per world like d2r_muleAssign and rides Backup & Share.
  · Esc closes the PICKER first, the window on the second Esc. A worn copy leaves the stash (the window promises
    "pack in-game EXACTLY like this"), and the shelf card packs with the same worn map. An equipped slot carries
    no native title, so the board's one hover card is not covered by an OS box (v2119). NOTES is an editor over
    the locker's own note, saved on Enter/blur through the routed store, and a draft survives a re-render.
  · THE SLOT TABLE IS THE GAME'S. MULE_BASE_SLOT is generated from his install's armor/weapons/misc `type` column
    (tv/mule_slot_map.py): here every name in it is checked against the committed tv/item_tables.json kinds, and
    MULE_NAMED_BASE is re-derived from item_tables.json and compared exactly. Only the SUBTYPE (helm vs torso)
    needs the install — that case runs where the install is, and says UNMEASURED where it is not.

#174 v-B REVIEW — what three independent seats found in the shipped build, each reproduced before it was fixed:
  · CLASS SKILLS ADD TO ONE CLASS. The Oculus (+3 Sorceress) and Homunculus (+2 Necromancer) read "+ Class Skills
    5 TEXT" — a number no character ever gets; the .d2s path threw the class param away and did the same.
  · A GHOST IS NOT WORN. An item reassigned to another locker stayed on the first doll, still summed, and the one
    copy could then be worn on the second locker's doll too. Only a LIVE entry counts (_mpLive).
  · THE HANDS HOLD WHAT THE GAME ALLOWS. Windforce (a Hydra Bow — weapons.txt `2handed`) sat beside Stormshield and
    both were summed; a two-handed spear and a Sorceress-only orb were offered for the left hand; an orb and a
    Necromancer's head were worn together. The rules are the install's (weapons.txt, itemtypes.txt), generated.
  · AN IMPORT CARRIES WHAT ITS SAVE CARRIES. The store's only writer dropped runewordProps and socketed children,
    so an imported Enigma read FRW "0% EXACT". A part the store did not carry makes the number UNKNOWN (≥).
  · A NAME FINDS ITS TEXT THE WAY IT FINDS ITS SLOT ("Stone of Jordan", "Harlequin Crest", runewords, the codex's
    own set-piece spellings), and an UNKNOWN names the keys it tried. Two texts that disagree (Arioc's Needle: 2 vs
    2–4) print their union and say so. +Vitality / +Energy are UNKNOWN parts of Life / Mana, never a silent 0.
  · THE HARNESS REACHES EVERY BRANCH. The runeword-base fit, the set-piece text and the set-piece slot fit were
    typeof-skipped here, so a sabotage of any of them stayed green.

⚠ WHAT THIS LAW CANNOT SEE: pixels. That the picker, the worn art and the stat tags fit at every width is
test_the_mule_window_fits_at_every_width.py's second pass, in a real browser.
RED_PROOF below.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

from test_the_mule_window_is_the_planner_shell import _vault_span, _static_attrs  # noqa: E402  ONE cut
import mule_slot_map as MSM  # noqa: E402

NODE = shutil.which("node")
MULE = "uni-armor"
#: the board's own spellings — what tvVaultRegister stores ("Harlequin Crest" registers as "Harlequin Crest (Shako)").
#: Beast Bite Ring is a rolled rare: it fits a ring slot by its own name and has no text anywhere, the honest UNKNOWN.
LOCKER = ["Harlequin Crest (Shako)", "The Stone of Jordan", "Mara's Kaleidoscope", "Arachnid Mesh", "The Oculus",
          "Annihilus", "Mystery Relic", "Nagelring", "Magefist", "Beast Bite Ring"]
#: a weapons locker for the two-hands rules: a bow, its two quivers, a shield, a two-handed spear, a one-handed sword
#: and flail (a Barbarian holds both), two claws (an Assassin holds both), an orb and a Voodoo head (two classes)
HANDS = ["Windforce", "Arrows", "Bolts", "Stormshield", "Arioc's Needle", "Lightsabre", "Stormlash",
         "Bartuc's Cut-Throat", "Jade Talon", "The Oculus", "Homunculus"]


def _src():
    with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as f:
        return f.read()


def _between(s, start, end):
    assert s.count(start) == 1, "the cut start %r is not unique (%d) — the anchor moved" % (start[:60], s.count(start))
    i = s.index(start)
    j = s.index(end, i + len(start))
    return s[i:j]


def _line(s, start):
    assert s.count(start) == 1, "the line %r is not unique (%d)" % (start[:60], s.count(start))
    i = s.index(start)
    return s[i:s.index("\n", i) + 1]


def _block(s, start):
    """a top-level `const X = [ ... ];` table, up to its own closing line"""
    return _between(s, start, "\n];\n") + "\n];\n"


def _sets_and_runewords(s):
    """#174 v-B review — the set and runeword tables the fit and the text read, and the finders over them. Without
    these the harness typeof-skipped three shipped branches, and a sabotage of any of them stayed green."""
    return (_line(s, "function _norm(s){") + _block(s, "const ITEM_SETS = [") + _block(s, "const SET_PIECES_EXTRA = [")
            + _block(s, "const SET_PIECES_EXTRA2 = [") + _line(s, "function __allSets(){")
            + _line(s, "function __pieceBase(pc){") + _line(s, "function __pieceSlot(pc){")
            + _between(s, "function findSetPiece(name){", "window.findSetPiece = findSetPiece;")
            + _between(s, "function _codexSetMember(name){", "function _setPieceTipHtml(sp){")
            + _block(s, "const RUNEWORDS = [") + _line(s, "const RUNEWORD_TIP = {") + _line(s, "function _rwNorm(s){")
            + _line(s, "const _RW_TIP_INDEX = ")
            + _between(s, "function findRuneword(name){", "window.findRuneword = findRuneword;"))


HARNESS = r"""
var STORE = %(store)s, LISTEN = {}, WLISTEN = {}, switched = [], renders = 0;
function mkEl(attrs){
  var cls = {}, a = {};
  Object.keys(attrs || {}).forEach(function(k){ a[k] = attrs[k]; });
  return { hidden: Object.prototype.hasOwnProperty.call(a, 'hidden'), innerHTML: '', scrollTop: 0, parentElement: null,
    classList: { add: function(c){ cls[c] = 1; }, remove: function(c){ delete cls[c]; }, contains: function(c){ return !!cls[c]; } },
    setAttribute: function(k, v){ a[k] = String(v); }, getAttribute: function(k){ return Object.prototype.hasOwnProperty.call(a, k) ? a[k] : null; },
    removeAttribute: function(k){ delete a[k]; }, querySelector: function(){ return null; } };
}
var box = mkEl(%(attrs)s), _html = '';
Object.defineProperty(box, 'innerHTML', { get: function(){ return _html; }, set: function(v){ _html = v; } });
box.querySelector = function(sel){
  if (sel !== '.mp') return null;
  var m = /data-sig="([^"]*)"/.exec(_html);
  return m ? { getAttribute: function(k){ return k === 'data-sig' ? m[1] : null; } } : null;
};
box.contains = function(){ return false; };
var body = { appendChild: function(el){ el.parentElement = body; } };
var document = { body: body, documentElement: mkEl({}), activeElement: null,
  getElementById: function(id){ return id === 'vault-detail' ? box : null; },
  querySelector: function(sel){ return sel === '.tab.active' ? { dataset: { tab: 'vault' } } : null; },
  querySelectorAll: function(){ return []; },
  addEventListener: function(n, f, cap){ (LISTEN[n] = LISTEN[n] || []).push({ f: f, cap: !!cap }); } };
var window = { innerWidth: 2000, innerHeight: 1300, switchTab: function(t){ switched.push(t); },
  addEventListener: function(n, f){ (WLISTEN[n] = WLISTEN[n] || []).push(f); },
  LSR: { getItem: function(k){ return Object.prototype.hasOwnProperty.call(STORE, k) ? STORE[k] : null; },
         setItem: function(k, v){ STORE[k] = String(v); } } };
function setTimeout(f){ f(); } function clearTimeout(){}
var roster = [{ id: 'uni-armor', name: 'UNI-ARMOR', icon: 'A', note: 'body armor · helms · shields' },
              { id: 'uni-weap', name: 'UNI-WEAPONS', icon: 'W', note: '' }];
function muleById(id){ for (var i = 0; i < roster.length; i++) if (roster[i].id === id) return roster[i]; return null; }
var assign = %(assign)s, COPIES = %(copies)s;
function vaultSize(n){ return [1, 1]; }
function copyCount(n){ return COPIES[n] || 1; }
function artOr(n, g, size){ return '<span class="d2art-wrap ' + (size || 'lg') + '" role="img" aria-label="' + esc(n) + '">' + g + '</span>'; }
function _renderSharedStash(){}
function _itemValue(){ return ''; }
function renderVault(){ renders++; }
%(tables)s
%(helpers)s
%(span)s
function fire(type, ev){
  var stop = false;
  ev.stopImmediatePropagation = function(){ stop = true; }; ev.stopPropagation = ev.stopImmediatePropagation;
  ev.preventDefault = ev.preventDefault || function(){};
  var ls = LISTEN[type] || [];
  ls.filter(function(l){ return l.cap; }).concat(ls.filter(function(l){ return !l.cap; })).forEach(function(l){ if (!stop) l.f(ev); });
}
function unesc(t){ return String(t).replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&amp;/g, '&'); }
function options(){ var re = /data-fk="opt-(\d+)"[^>]*aria-label="(?:equip |worn here now: )([^"]*)"/g, m, out = [];
  while ((m = re.exec(box.innerHTML))) out.push(unesc(m[2])); return out; }
function choose(name){ var o = options(), i = o.indexOf(name); return i < 0 ? 'NOT OFFERED' : window._mpChoose(i); }
function footer(){ var i = box.innerHTML.indexOf('<div class="mp-pick-f">'); return i < 0 ? null : unesc(box.innerHTML.slice(i, box.innerHTML.indexOf('</div></div>', i))).replace(/<[^>]+>/g, ''); }
function row(label){ var re = new RegExp('<div class="mp-st-r[^"]*" data-k="' + label.toLowerCase().replace(/[+]/g, '\\+') + '"[^>]*><span>[^<]*</span>(.*?)</div>'), m = re.exec(box.innerHTML);
  if (!m) return null; var c = m[1], v = /<b>([^<]*)<\/b><i>([^<]*)<\/i>/.exec(c), t = /title="([^"]*)"/.exec(c);
  return v ? { value: unesc(v[1]), tag: v[2], title: unesc(t ? t[1] : '') } : { value: /UNKNOWN/.test(c) ? 'UNKNOWN' : c, tag: null, title: unesc(t ? t[1] : '') }; }
function slotSay(slot){ var h = box.innerHTML, i = h.indexOf('data-slot="' + slot + '"'); if (i < 0) return null;
  var b = h.slice(h.lastIndexOf('<button', i), h.indexOf('>', i) + 1), c = /class="([^"]*)"/.exec(b), a = /aria-label="([^"]*)"/.exec(b);
  return { cls: c ? c[1] : '', say: unesc(a ? a[1] : '') }; }
function eq(){ return JSON.parse(STORE['d2r_muleEquip'] || '{}'); }
function liveCount(name){ var n = 0; roster.forEach(function(r){ var L = window._mpLive(r.id, eq());
  ['setI', 'setII'].forEach(function(s){ Object.keys(L.at[s]).forEach(function(k){ if (L.at[s][k].name === name) n++; }); }); }); return n; }
var out = {};
%(scenario)s
console.log(JSON.stringify(out));
"""


def _drive(scenario, assign=None, copies=None, store=None):
    s = _src()
    tables = _line(s, "const ITEM_CODEX = {") + _line(s, "const ITEM_TIP = {") + _sets_and_runewords(s)
    helpers = (_line(s, "  var RK='d2r_muleRoster', AK='d2r_muleAssign';")
               + _line(s, "  function saveR(){ window.LSR.setItem(RK, JSON.stringify(roster)); }")
               + _line(s, "  function art(n, glyph, size){")
               + _line(s, "  function esc(t){ return String(t)")
               + _line(s, "  function jsArg(t){")
               + _between(s, "  function tipOf(n){", "  // RoW shared-stash items never get a mule"))
    js = HARNESS % {
        "store": json.dumps(store or {}), "attrs": json.dumps(_static_attrs()),
        "assign": json.dumps(assign if assign is not None else dict((n, MULE) for n in LOCKER)),
        "copies": json.dumps(copies or {}), "tables": tables, "helpers": helpers, "span": _vault_span(),
        "scenario": scenario,
    }
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, timeout=90)
    if r.returncode != 0:
        raise AssertionError("the shipped mule window would not run - UNKNOWN, not passing: %s" % r.stderr[:900])
    return json.loads(r.stdout.strip().splitlines()[-1])


def _hands_locker():
    a = dict((n, MULE) for n in LOCKER)
    a.update((n, "uni-weap") for n in HANDS)
    return a


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheStoreAndItsPrecedence(unittest.TestCase):

    def test_choosing_writes_the_store_in_its_shape(self):
        out = _drive("""
          window.openMuleCard('uni-armor'); window._mpPick('head'); out.chose = choose('Harlequin Crest (Shako)');
          out.eq = eq(); out.pickOpen = box.innerHTML.indexOf('class="mp-pick"') >= 0;
          window._mpSet('swap', 2); window._mpPick('rarm'); out.chose2 = choose('The Oculus'); out.eq2 = eq();
          window._mpPick('neck'); out.chose3 = choose("Mara's Kaleidoscope"); out.eq3 = eq();""")
        self.assertIs(out["chose"], True)
        self.assertFalse(out["pickOpen"], "choosing an item left the picker open")
        e = out["eq"][MULE]["setI"]["head"]
        self.assertEqual(sorted(e), ["at", "name", "source"])
        self.assertEqual((e["name"], e["source"]), ("Harlequin Crest (Shako)", "manual"))
        datetime.strptime(e["at"][:19], "%Y-%m-%dT%H:%M:%S")
        self.assertEqual(out["eq2"][MULE]["setII"]["rarm"]["name"], "The Oculus", "weapon set II did not keep its own hand")
        self.assertNotIn("rarm", out["eq2"][MULE]["setI"], "a set-II weapon landed in set I")
        self.assertEqual(sorted(out["eq3"][MULE]["setII"]), ["rarm"], "only the hands swap; the amulet went to set II")
        self.assertEqual(out["eq3"][MULE]["setI"]["neck"]["name"], "Mara's Kaleidoscope")

    def test_a_manual_placement_always_wins(self):
        out = _drive("""
          var P = window._mpEqPlace, a = P({}, 'm', 'setI', 'head', { name: 'Shako', source: 'manual' }).all;
          out.analyzer_over_manual = P(a, 'm', 'setI', 'head', { name: 'Vampire Gaze', source: 'analyzer' });
          out.import_over_manual = P(a, 'm', 'setI', 'head', { name: 'Vampire Gaze', source: 'import', props: [] });
          out.manual_over_manual = P(a, 'm', 'setI', 'head', { name: 'Crown of Ages', source: 'manual' }).ok;
          var r = P({}, 'm', 'setI', 'head', { name: 'Vampire Gaze', source: 'analyzer' }).all;
          out.manual_over_analyzer = P(r, 'm', 'setI', 'head', { name: 'Shako', source: 'manual' }).ok;
          out.import_over_analyzer = P(r, 'm', 'setI', 'head', { name: 'Shako', source: 'import', props: [] }).ok;
          var i = P({}, 'm', 'setI', 'head', { name: 'Shako', source: 'import', props: [] }).all;
          out.analyzer_over_import = P(i, 'm', 'setI', 'head', { name: 'Vampire Gaze', source: 'analyzer' }).ok;
          out.no_source = P({}, 'm', 'setI', 'head', { name: 'Shako' }).ok;
          out.shared_slot_in_set2 = Object.keys(P({}, 'm', 'setII', 'glov', { name: 'Magefist', source: 'manual' }).all.m);""")
        self.assertFalse(out["analyzer_over_manual"]["ok"])
        self.assertIn("a manual placement always wins", out["analyzer_over_manual"]["why"])
        self.assertEqual(out["analyzer_over_manual"]["all"]["m"]["setI"]["head"]["name"], "Shako", "the refused route moved it")
        self.assertFalse(out["import_over_manual"]["ok"])
        self.assertTrue(out["manual_over_manual"], "his hand could not change his own placement")
        self.assertTrue(out["manual_over_analyzer"] and out["import_over_analyzer"])
        self.assertFalse(out["analyzer_over_import"])
        self.assertFalse(out["no_source"], "a placement with no source was stored")
        self.assertEqual(out["shared_slot_in_set2"], ["setI"], "a shared slot was filed under weapon set II")


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class OnlyWhatFitsIsOffered(unittest.TestCase):

    def test_a_ring_is_never_offered_for_the_helm_and_the_left_out_are_counted(self):
        out = _drive("""
          window.openMuleCard('uni-armor');
          window._mpPick('head'); out.head = options(); out.headFoot = footer();
          window._mpPick('rrin'); out.rrin = options(); out.chose = choose('The Stone of Jordan');
          window._mpPick('lrin'); out.lrin = options(); out.lrinFoot = footer();
          window._mpPick('rarm'); out.rarm = options();
          window._mpPick('neck'); out.neck = options();""")
        self.assertEqual(out["head"], ["Harlequin Crest (Shako)"], "the helm picker offered something that is not a helm")
        foot = out["headFoot"]
        self.assertIn("Left out: 9 of 10", foot)
        self.assertIn("7 fit other slots:", foot)
        self.assertIn("Nagelring (ring)", foot, "a ring left out of the helm picker is not named with its slot")
        self.assertIn("1 is carried, never worn: Annihilus", foot)
        self.assertIn("1 has no slot on record, so it is not offered: Mystery Relic (no base type is on record for it)", foot)
        self.assertEqual(sorted(out["rrin"]), ["Beast Bite Ring", "Nagelring", "The Stone of Jordan"])
        self.assertIs(out["chose"], True)
        self.assertEqual(sorted(out["lrin"]), ["Beast Bite Ring", "Nagelring"], "the one Stone of Jordan, already worn, was offered again")
        self.assertIn("1 is already worn in another slot: The Stone of Jordan", out["lrinFoot"])
        self.assertEqual(out["rarm"], ["The Oculus"])
        self.assertEqual(out["neck"], ["Mara's Kaleidoscope"])

    def test_the_slot_of_a_base_is_read_never_guessed(self):
        out = _drive("""
          var K = window._mpSlotKind, F = window._mpFit;
          out.k = ['Shako', 'ring', 'Monarch (4os)', 'Superior Archon Plate', '3-sock body armor', 'helm or shield',
                   'Grand Charm', 'Event / RotW Item', ''].map(function(b){ var r = K(b); return r ? (r.kind || ('AMBIGUOUS ' + r.ambiguous.join('/'))) : null; });
          out.f = ['Stone of Jordan', 'Harlequin Crest', 'Laying of Hands (bramble mitts)', 'Beast Bite Ring', 'Mystery Relic', 'Annihilus']
                  .map(function(n){ var r = F(n); return [r.kind, r.from || r.why]; });""")
        self.assertEqual(out["k"], ["helm", "ring", "shield", "armor", "armor", "AMBIGUOUS helm/shield", "none", None, None])
        self.assertEqual([f[0] for f in out["f"]], ["ring", "helm", "gloves", "ring", None, "none"])
        self.assertEqual(out["f"][0][1], "the game's unique / set table", "SoJ's slot did not come from the game's table")
        self.assertEqual(out["f"][4][1], "no base type is on record for it")


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheHarnessReachesEveryBranch(unittest.TestCase):
    """#174 v-B review — the runeword-base fit, the set-piece text and the set-piece slot fit, each on the SHIPPED
    tables. Before, the harness never loaded them and the typeof guards skipped all three in silence."""

    def test_a_runeword_fits_by_its_base_and_a_set_piece_reads_its_own_affixes(self):
        out = _drive("""
          out.reach = [typeof RUNEWORDS, typeof findSetPiece, typeof _codexSetMember, typeof findRuneword, typeof ITEM_SETS];
          var e = window._mpFit('Enigma'); out.enigma = [e.kind, e.from, e.base];
          var c = window._mpContrib({ name: "Tal Rasha's Horadric Crest", source: 'manual' });
          out.tal = { src: c.src, from: c.from, fire: c.per.fire, life: c.per.life, mana: c.per.mana };
          SET_PIECES_EXTRA.push({ name: 'Planted Kit (set)', pieces: ['Planted Visor (war hat)'] });
          var p = window._mpFit('Planted Visor'); out.planted = [p.kind, p.from, p.base];""")
        self.assertEqual(out["reach"], ["object", "function", "function", "function", "object"],
                         "the harness no longer carries the set / runeword tables the shipped fit and text read")
        self.assertEqual(out["enigma"], ["armor", "runeword base", "3-sock body armor"])
        tal = out["tal"]
        self.assertEqual((tal["src"], tal["from"]), ("range", "ITEM_CODEX set piece text"))
        self.assertEqual((tal["fire"]["lo"], tal["fire"]["hi"]), (15, 15), "Horadric Crest's All Resistances +15 was not read")
        self.assertEqual((tal["life"]["lo"], tal["mana"]["lo"]), (60, 30))
        # no set piece on today's tables reaches findSetPiece (the game table answers first), so this branch is
        # driven with a planted piece — a working finder would otherwise be indistinguishable from a broken one
        self.assertEqual(out["planted"], ["helm", "set piece slot", "war hat"])


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class EachNumberSaysItsSource(unittest.TestCase):

    def test_the_text_parser_reads_ranges_and_refuses_what_needs_a_character(self):
        lines = ["+[20-30]% Faster Cast Rate", "+20% Faster Cast Rate", "All Resistances +15", "Fire Resist +30%",
                 "Fire Resist +-30%", "+2 To All Skills", "+1 to Sorceress Skill Levels", "15-30% Better Chance of Getting Magic Items",
                 "+[1-99] To Life (Based On Character Level)", "Increase Maximum Life 5%", "+5% to Maximum Fire Resist",
                 "-25% To Enemy Fire Resistance", "Replenish Life +10", "+40 To Mana", "+10 to Mana after each Kill",
                 "25% Faster Run/Walk", "+30% Faster Hit Recovery", "20% Increased Attack Speed",
                 "+20 to Vitality", "+[10-20] To Energy", "+5 To All Attributes", "+2 to Str/Vit/Energy",
                 "+[1-99] To Vitality (Based On Character Level)", "+1 Energy Shield (Sorceress Only)"]
        out = _drive("out.p = %s.map(function(l){ return window._mpParseProp(l); });" % json.dumps(lines))
        p = dict(zip(lines, out["p"]))
        self.assertEqual(p["+[20-30]% Faster Cast Rate"], [{"k": "fcr", "lo": 20, "hi": 30}])
        self.assertEqual(p["+20% Faster Cast Rate"], [{"k": "fcr", "lo": 20, "hi": 20}])
        self.assertEqual([c["k"] for c in p["All Resistances +15"]], ["fire", "cold", "light", "poison"])
        self.assertEqual(p["Fire Resist +30%"], [{"k": "fire", "lo": 30, "hi": 30}])
        self.assertEqual(p["Fire Resist +-30%"], [{"k": "fire", "lo": -30, "hi": -30}])
        self.assertEqual(p["+2 To All Skills"], [{"k": "allsk", "lo": 2, "hi": 2}])
        self.assertEqual(p["+1 to Sorceress Skill Levels"], [{"k": "clsk", "lo": 1, "hi": 1, "cls": "Sorceress"}],
                         "a class-skill line lost the class it adds to")
        self.assertEqual(p["15-30% Better Chance of Getting Magic Items"], [{"k": "mf", "lo": 15, "hi": 30}])
        self.assertEqual([sorted(c) for c in p["+[1-99] To Life (Based On Character Level)"]], [["k", "why"]])
        self.assertEqual(p["Increase Maximum Life 5%"][0]["k"], "life")
        self.assertIn("why", p["Increase Maximum Life 5%"][0])
        for none in ("+5% to Maximum Fire Resist", "-25% To Enemy Fire Resistance", "Replenish Life +10",
                     "+10 to Mana after each Kill", "+1 Energy Shield (Sorceress Only)"):
            self.assertEqual(p[none], [], "%r is not the stat it names" % none)
        self.assertEqual(p["+40 To Mana"], [{"k": "mana", "lo": 40, "hi": 40}])
        self.assertEqual(p["25% Faster Run/Walk"][0]["k"], "frw")
        self.assertEqual(p["+30% Faster Hit Recovery"][0]["k"], "fhr")
        self.assertEqual(p["20% Increased Attack Speed"][0]["k"], "ias")
        # #174 v-B review — +Vitality / +Energy add life / mana by the character's class: an UNKNOWN part, never nothing
        self.assertEqual([(c["k"], "why" in c) for c in p["+20 to Vitality"]], [("life", True)])
        self.assertEqual([(c["k"], "why" in c) for c in p["+[10-20] To Energy"]], [("mana", True)])
        for both in ("+5 To All Attributes", "+2 to Str/Vit/Energy"):
            self.assertEqual([(c["k"], "why" in c) for c in p[both]], [("life", True), ("mana", True)], both)
        self.assertEqual([(c["k"], "why" in c) for c in p["+[1-99] To Vitality (Based On Character Level)"]], [("life", True)])

    def test_exact_range_unknown_and_mixed_sum(self):
        out = _drive("""
          var S = window._mpSumStat, ex = { name: 'SoJ', src: 'exact', from: 'its .d2s', per: { fire: { lo: 35, hi: 35, unk: [] } } },
              rg = { name: 'Mara', src: 'range', from: 'ITEM_CODEX text', per: { fire: { lo: 20, hi: 30, unk: [] } } },
              uk = { name: 'Relic', src: 'unknown', from: '', per: {}, why: 'no property text is on record for it' },
              lv = { name: 'Forge', src: 'range', from: 'ITEM_TIP text', per: { fire: { lo: 0, hi: 0, unk: ['scales with character level'] } } };
          out.exact = S([ex], 'fire'); out.range = S([rg], 'fire'); out.mixed = S([ex, rg], 'fire'); out.unknown = S([uk], 'fire');
          out.rangeUnk = S([rg, uk], 'fire'); out.none = S([], 'fire'); out.zeroButUnknown = S([lv], 'fire');
          out.zero = S([{ name: 'Belt', src: 'range', from: 'ITEM_CODEX text', per: {} }], 'fire');""")
        self.assertEqual((out["exact"]["kind"], out["exact"]["text"], out["exact"]["tag"]), ("exact", "35%", "EXACT"))
        self.assertEqual((out["range"]["kind"], out["range"]["text"], out["range"]["tag"]), ("range", "20\u201330%", "TEXT"))
        self.assertEqual((out["mixed"]["kind"], out["mixed"]["text"], out["mixed"]["tag"]), ("mixed", "\u2265 35% + 20\u201330%", "MIXED"))
        self.assertEqual(out["unknown"]["kind"], "unknown")
        self.assertIn("Relic: no property text is on record for it", out["unknown"]["why"])
        self.assertEqual(out["rangeUnk"]["text"], "\u2265 20\u201330%", "a range beside an UNKNOWN part is not a floor")
        self.assertEqual(out["none"], {"kind": "unknown", "why": "nothing is equipped on this doll"})
        self.assertEqual(out["zeroButUnknown"]["kind"], "unknown", "a part that needs the character read as a 0")
        self.assertEqual((out["zero"]["kind"], out["zero"]["text"]), ("zero", "0%"))
        for k in ("range", "mixed", "rangeUnk"):
            self.assertNotIn("25", out[k]["text"], "a range was averaged")

    def test_the_window_prints_each_stat_with_its_source(self):
        out = _drive("""
          window.openMuleCard('uni-armor');
          window._mpPick('neck'); choose("Mara's Kaleidoscope");
          window._mpPick('belt'); choose('Arachnid Mesh');
          var a = window._mpEqPlace(eq(), 'uni-armor', 'setI', 'rrin', { name: 'The Stone of Jordan', source: 'import',
                    props: [{ stat: 'item_allskills', value: 1 }, { stat: 'maxmana', value: 20 }, { stat: 'item_maxmana_percent', value: 25 }] });
          window.LSR.setItem('d2r_muleEquip', JSON.stringify(a.all));
          window.openMuleCard('uni-armor');
          out.A = { skills: row('+ All Skills'), fcr: row('Faster Cast Rate'), fire: row('Fire Resistance'), mana: row('Mana'),
                    mf: row('Magic Find'), str: row('Strength'), src: box.innerHTML.indexOf('class="mp-st-src"') >= 0 };
          window._mpPick('head'); choose('Harlequin Crest (Shako)');
          out.B = { skills: row('+ All Skills'), mf: row('Magic Find') };
          window._mpPick('lrin'); choose('Beast Bite Ring');
          out.C = { mf: row('Magic Find'), frw: row('Faster Run/Walk') };""")
        A, B, C = out["A"], out["B"], out["C"]
        self.assertEqual((A["skills"]["value"], A["skills"]["tag"]), ("\u2265 1 + 3", "MIXED"))
        self.assertIn("The Stone of Jordan \u2014 EXACT from its .d2s: 1", A["skills"]["title"])
        self.assertIn("Mara's Kaleidoscope \u2014 by name, ITEM_CODEX text: 2", A["skills"]["title"])
        self.assertEqual((A["fcr"]["value"], A["fcr"]["tag"]), ("20%", "TEXT"))
        self.assertEqual((A["fire"]["value"], A["fire"]["tag"]), ("20\u201330%", "TEXT"), "the rolled range was not kept a range")
        self.assertEqual((A["mana"]["value"], A["mana"]["tag"]), ("\u2265 20", "MIXED"),
                         "a % of the character's own mana was folded into the exact +20")
        self.assertEqual((A["mf"]["value"], A["mf"]["tag"]), ("0%", "MIXED"))
        self.assertEqual(A["str"]["value"], "UNKNOWN", "a row the gear is not read for printed a number")
        self.assertTrue(A["src"], "the stats no longer say what EXACT / TEXT / MIXED mean")
        # the board's own spelling of the Shako carries its text: +2 skills and 50% magic find, by name
        self.assertEqual((B["skills"]["value"], B["skills"]["tag"]), ("\u2265 1 + 5", "MIXED"))
        self.assertEqual((B["mf"]["value"], B["mf"]["tag"]), ("50%", "TEXT"))
        self.assertIn("Harlequin Crest (Shako) \u2014 by name, ITEM_CODEX text: 50%", B["mf"]["title"])
        # a rolled rare with no text anywhere: a known part becomes a floor, known zeros become UNKNOWN, and the
        # reason names the keys it tried
        self.assertEqual((C["mf"]["value"], C["mf"]["tag"]), ("\u2265 50%", "MIXED"), "the no-text ring's part was read as nothing")
        self.assertEqual(C["frw"]["value"], "UNKNOWN", "an item with no text on record let the others' zero stand as measured")
        self.assertIn('Beast Bite Ring: no property text is on record under "Beast Bite Ring", "The Beast Bite Ring"',
                      C["frw"]["title"])


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class ClassSkillsAddToOneClass(unittest.TestCase):
    """#174 v-B review — "+3 to Sorceress Skill Levels" and "+2 to Necromancer Skill Levels" read "+ Class Skills 5".
    No character gets that. Lines of two classes are UNKNOWN, each class's part named; one class prints its name."""

    def test_two_classes_are_never_one_number_by_name_or_from_a_save(self):
        out = _drive("""
          var S = window._mpSumStat, C = window._mpContrib;
          var imp = function(n, param, v){ return C({ name: n, source: 'import', props: [{ stat: 'item_addclassskills', param: param, value: v }] }); };
          out.text = S([C({ name: 'The Oculus', source: 'manual' }), C({ name: 'Homunculus', source: 'manual' })], 'clsk');
          out.exact = S([imp('A', 1, 3), imp('B', 2, 2)], 'clsk');
          out.one = S([C({ name: 'The Oculus', source: 'manual' })], 'clsk');
          out.sameTwo = S([imp('A', 1, 3), imp('B', 1, 1)], 'clsk');
          out.noClass = S([imp('X', 9, 1)], 'clsk');
          out.ids = MP_CLASS_BY_ID;""")
        self.assertEqual(out["text"]["kind"], "unknown", "two classes' skill lines were summed into one number")
        self.assertIn("Necromancer: Homunculus 2", out["text"]["why"])
        self.assertIn("Sorceress: The Oculus 3", out["text"]["why"])
        self.assertEqual(out["exact"]["kind"], "unknown", "the .d2s path summed two classes (the class param was thrown away)")
        self.assertIn("Necromancer: B 2", out["exact"]["why"])
        self.assertEqual((out["one"]["text"], out["one"]["tag"]), ("3 Sorceress", "TEXT"))
        self.assertEqual((out["sameTwo"]["text"], out["sameTwo"]["tag"]), ("4 Sorceress", "EXACT"))
        self.assertEqual(out["noClass"]["kind"], "unknown")
        self.assertIn("(id 9) is not on record", out["noClass"]["why"])
        import d2s_read
        self.assertEqual(out["ids"], [d2s_read.CLASSES[i] for i in range(len(d2s_read.CLASSES))],
                         "the page's class ids are not the .d2s reader's")

    def test_the_window_row_names_each_class_and_sums_none(self):
        items = ["Wormskull", "Visceratuant"]
        out = _drive("""
          window.openMuleCard('uni-armor'); window._mpPick('head'); choose('Wormskull');
          out.one = row('+ Class Skills');
          window._mpPick('larm'); choose('Visceratuant');
          out.two = row('+ Class Skills');""", assign=dict((n, MULE) for n in items))
        self.assertEqual((out["one"]["value"], out["one"]["tag"]), ("1 Necromancer", "TEXT"))
        self.assertEqual(out["two"]["value"], "UNKNOWN", "the window summed two classes' skill lines")
        self.assertIn("different classes", out["two"]["title"])


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class AGhostIsNotWorn(unittest.TestCase):
    """#174 v-B review — an item reassigned to another locker stayed on the first doll, still summed, and the one copy
    could then be worn on the second locker's doll as well."""

    def test_a_reassigned_item_is_not_counted_and_is_worn_once(self):
        a = dict((n, MULE) for n in LOCKER)
        out = _drive("""
          window.openMuleCard('uni-armor');
          window._mpPick('neck'); choose("Mara's Kaleidoscope");
          window._mpPick('rrin'); out.chose = choose('The Stone of Jordan');
          out.before = row('+ All Skills');
          assign['The Stone of Jordan'] = 'uni-weap';
          window.openMuleCard('uni-armor');
          out.slot = slotSay('rrin'); out.after = row('+ All Skills');
          out.dead = /<div class="mp-st-src mp-st-dead">([^<]*<b>[^<]*<\\/b>[^<]*)<\\/div>/.exec(box.innerHTML);
          out.dead = out.dead ? unesc(out.dead[1].replace(/<[^>]+>/g, '')) : null;
          out.wornArmor = window._mpWornFor('uni-armor');
          window.openMuleCard('uni-weap'); window._mpPick('lrin'); out.offer = options();
          out.chose2 = choose('The Stone of Jordan');
          out.live = liveCount('The Stone of Jordan');""", assign=a)
        self.assertIs(out["chose"], True)
        self.assertEqual((out["before"]["value"], out["before"]["tag"]), ("3", "TEXT"))
        self.assertIn("mp-gone", out["slot"]["cls"])
        self.assertIn("NOT WORN, NOT COUNTED: no longer in this locker", out["slot"]["say"])
        self.assertEqual((out["after"]["value"], out["after"]["tag"]), ("2", "TEXT"), "the ghost's +1 is still summed")
        self.assertNotIn("The Stone of Jordan", out["after"]["title"])
        self.assertIn("The Stone of Jordan (no longer in this locker)", out["dead"] or "",
                      "the stats do not say which slot they left out")
        self.assertNotIn("The Stone of Jordan", out["wornArmor"])
        self.assertIn("The Stone of Jordan", out["offer"])
        self.assertIs(out["chose2"], True)
        self.assertEqual(out["live"], 1, "the one Stone of Jordan is worn on two dolls")


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheHandsHoldWhatTheGameAllows(unittest.TestCase):
    """#174 v-B review — Windforce (two-handed) beside Stormshield, a two-handed spear or an orb in the left hand, an
    orb beside a Necromancer's head: none of these is a loadout any class can wear, and the doll summed them."""

    def _run(self, scenario):
        return _drive("window.openMuleCard('uni-weap');\n" + scenario, assign=_hands_locker())

    def test_a_two_hander_leaves_the_left_hand_only_its_quiver(self):
        out = self._run("""
          window._mpPick('rarm'); out.rarm = options(); choose('Windforce');
          window._mpPick('larm'); out.larm = options(); out.foot = footer();
          out.shield = window._mpHandsWhy(window._mpGear('Windforce'), window._mpGear('Stormshield'));
          out.staff = window._mpHandsWhy(window._mpGear("Arioc's Needle"), window._mpGear('Stormshield'));""")
        self.assertIn("Windforce", out["rarm"])
        self.assertEqual(out["larm"], ["Arrows"], "the left hand beside a two-handed bow offered more than its quiver")
        self.assertIn("Bartuc's Cut-Throat, Homunculus, Jade Talon, Lightsabre, Stormlash, Stormshield \u2014 Windforce is a two-handed "
                      "Hydra Bow: the left hand holds only its Arrows", out["foot"], "one reason is not said once for every item it keeps out")
        self.assertIn("Bolts \u2014 Windforce shoots Arrows, not Bolts", out["foot"])
        self.assertEqual(out["shield"], "Windforce is a two-handed Hydra Bow: the left hand holds only its Arrows")
        self.assertEqual(out["staff"], "Arioc's Needle is a two-handed Hyperion Spear: the left hand holds nothing")

    def test_the_left_hand_never_takes_a_two_hander_or_a_class_weapon(self):
        out = self._run("window._mpPick('larm'); out.larm = options(); out.foot = footer();")
        self.assertNotIn("Arioc's Needle", out["larm"], "a two-handed spear was offered for the left hand")
        self.assertNotIn("The Oculus", out["larm"], "a Sorceress-only orb was offered as a second weapon")
        for n in ("Stormshield", "Homunculus", "Lightsabre", "Stormlash", "Bartuc's Cut-Throat", "Arrows", "Bolts"):
            self.assertIn(n, out["larm"])
        self.assertIn("Arioc's Needle \u2014 a two-handed Hyperion Spear is held in the right hand", out["foot"])
        self.assertIn("The Oculus \u2014 a Sorceress-only weapon, and a Sorceress never holds a second weapon", out["foot"])

    def test_a_shield_keeps_two_handers_out_of_the_right_hand(self):
        out = self._run("""
          window._mpPick('larm'); choose('Stormshield');
          window._mpPick('rarm'); out.rarm = options(); out.foot = footer();""")
        self.assertNotIn("Windforce", out["rarm"])
        self.assertNotIn("Arioc's Needle", out["rarm"])
        self.assertIn("Lightsabre", out["rarm"])
        self.assertIn("Windforce is a two-handed Hydra Bow: the left hand holds only its Arrows, and it holds Stormshield", out["foot"])

    def test_two_weapons_only_as_a_barbarian_or_two_claws(self):
        out = self._run("""
          window._mpPick('rarm'); choose('Lightsabre');
          window._mpPick('larm'); out.sword = options(); out.swordFoot = footer();
          window._mpPick('rarm'); choose("Bartuc's Cut-Throat");
          window._mpPick('larm'); out.claw = options();""")
        self.assertIn("Stormlash", out["sword"], "a Barbarian's second one-handed weapon was refused")
        self.assertNotIn("Bartuc's Cut-Throat", out["sword"])
        self.assertIn("Bartuc's Cut-Throat \u2014 no class holds Lightsabre and Bartuc's Cut-Throat together", out["swordFoot"])
        self.assertIn("Jade Talon", out["claw"], "an Assassin's second claw was refused")
        self.assertNotIn("Stormlash", out["claw"])

    def test_one_class_per_doll(self):
        out = self._run("""
          window._mpPick('rarm'); choose('The Oculus');
          window._mpPick('larm'); out.larm = options(); out.foot = footer();""")
        self.assertNotIn("Homunculus", out["larm"], "a Necromancer's head was offered beside a Sorceress's orb")
        self.assertIn("Homunculus \u2014 Necromancer-only, and The Oculus (Sorceress-only) is worn", out["foot"])

    def test_a_stored_impossible_loadout_is_drawn_and_never_summed(self):
        store = {"d2r_muleEquip": json.dumps({"uni-weap": {
            "setI": {"rarm": {"name": "The Oculus", "source": "manual", "at": "2026-09-25T10:00:00.000Z"},
                     "larm": {"name": "Homunculus", "source": "manual", "at": "2026-09-25T10:00:01.000Z"}},
            "setII": {"rarm": {"name": "Windforce", "source": "manual", "at": "2026-09-25T10:00:02.000Z"},
                      "larm": {"name": "Stormshield", "source": "manual", "at": "2026-09-25T10:00:03.000Z"}}}})}
        out = _drive("""
          window.openMuleCard('uni-weap');
          out.I = { larm: slotSay('larm'), clsk: row('+ Class Skills') };
          window._mpSet('swap', 2);
          out.II = { larm: slotSay('larm'), cold: row('Cold Resistance'), ias: row('Increased Attack Speed') };
          out.worn = window._mpWornFor('uni-weap');""", assign=_hands_locker(), store=store)
        self.assertIn("mp-gone", out["I"]["larm"]["cls"])
        self.assertIn("NOT WORN, NOT COUNTED: Necromancer-only, and The Oculus (Sorceress-only) was worn first", out["I"]["larm"]["say"])
        self.assertEqual((out["I"]["clsk"]["value"], out["I"]["clsk"]["tag"]), ("3 Sorceress", "TEXT"))
        self.assertIn("mp-gone", out["II"]["larm"]["cls"])
        self.assertIn("NOT WORN, NOT COUNTED: Windforce is a two-handed Hydra Bow: the left hand holds only its Arrows",
                      out["II"]["larm"]["say"])
        self.assertNotIn("Stormshield", out["II"]["cold"]["title"], "a shield beside a two-handed bow was summed")
        self.assertEqual(out["II"]["ias"]["value"], "20%")
        self.assertEqual(out["worn"], {"The Oculus": 1, "Windforce": 1}, "an unwearable piece left the grid")


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class AnImportCarriesWhatItsSaveCarries(unittest.TestCase):
    """#174 v-B review — the store's only writer kept props alone; the EXACT reader wanted runewordProps too."""

    def test_the_runeword_list_and_the_sockets_reach_the_sum(self):
        out = _drive("""
          var P = window._mpEqPlace, S = window._mpSumStat, C = window._mpContrib;
          var put = function(slot, e){ var r = P({}, 'm', 'setI', slot, e); return r.all.m.setI[slot]; };
          var rw = { name: 'Enigma', source: 'import', isRuneword: true, props: [{ stat: 'armorclass', value: 750 }],
                     runewordProps: [{ stat: 'item_fastermovevelocity', value: 45 }, { stat: 'item_allskills', value: 2 }],
                     socketedCount: 0, socketed: [] };
          var e1 = put('tors', rw); out.keys = Object.keys(e1).sort();
          out.frw = S([C(e1)], 'frw'); out.allsk = S([C(e1)], 'allsk');
          var jw = put('head', { name: 'Harlequin Crest (Shako)', source: 'import', props: [{ stat: 'item_allskills', value: 2 }], socketedCount: 1,
                     socketed: [{ name: 'Jewel', code: 'jew', simple: false, props: [{ stat: 'fireresist', value: 19 }, { stat: 'coldresist', value: 19 }] }] });
          out.fire = S([C(jw)], 'fire');
          var runes = JSON.parse(JSON.stringify(rw)); runes.socketedCount = 1; runes.socketed = [{ name: 'Jah Rune', code: 'r31', simple: true, props: [] }];
          out.runes = S([C(put('tors', runes))], 'frw');
          var bare = { name: 'Enigma', source: 'import', isRuneword: true, props: [] };
          out.bare = S([C(put('tors', bare))], 'frw');
          var holes = { name: 'Shako', source: 'import', props: [], socketedCount: 2, socketed: [] };
          out.holes = S([C(put('head', holes))], 'fire');""")
        self.assertEqual(out["keys"], ["at", "isRuneword", "name", "props", "runewordProps", "socketed", "socketedCount", "source"])
        self.assertEqual((out["frw"]["text"], out["frw"]["tag"]), ("45%", "EXACT"), "the runeword's own list did not reach the sum")
        self.assertEqual(out["allsk"]["text"], "2")
        self.assertEqual((out["fire"]["text"], out["fire"]["tag"]), ("19%", "EXACT"), "a socketed jewel's resist was dropped")
        self.assertEqual((out["runes"]["text"], out["runes"]["tag"]), ("\u2265 45%", "MIXED"),
                         "a socketed rune's bonus (unread) let the number stand as EXACT")
        self.assertIn("its socketed Jah Rune adds by the item type", out["runes"]["say"])
        self.assertEqual(out["bare"]["kind"], "unknown", "a runeword without its own list read as an EXACT number")
        self.assertIn("the runeword's own properties were not carried", out["bare"]["why"])
        self.assertEqual(out["holes"]["kind"], "unknown")
        self.assertIn("2 socketed items were not carried", out["holes"]["why"])


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class ANameFindsItsText(unittest.TestCase):
    """#174 v-B review — a name finds its text the way it finds its slot; an UNKNOWN names the keys it tried."""

    def test_the_boards_own_spellings_runewords_and_the_codex_set_names(self):
        names = ["Stone of Jordan", "Harlequin Crest", "Enigma", "Cow King's Hooves (heavy boots)", "Whitstan's Guard",
                 "Griswold's Redemption", "Beast Bite Ring"]
        out = _drive("""out.c = %s.map(function(n){ var c = window._mpContrib({ name: n, source: 'manual' });
          return { src: c.src, from: c.from, why: c.why || null, allsk: c.per.allsk || null, mf: c.per.mf || null, frw: c.per.frw || null }; });"""
                     % json.dumps(names))
        c = dict(zip(names, out["c"]))
        self.assertEqual((c["Stone of Jordan"]["from"], c["Stone of Jordan"]["allsk"]["lo"]), ("ITEM_CODEX text", 1))
        self.assertEqual((c["Harlequin Crest"]["allsk"]["lo"], c["Harlequin Crest"]["mf"]["lo"]), (2, 50))
        self.assertEqual((c["Enigma"]["from"], c["Enigma"]["frw"]["lo"]), ("RUNEWORD_TIP text", 45))
        ck = c["Cow King's Hooves (heavy boots)"]
        self.assertEqual((ck["from"], ck["frw"]["lo"], ck["mf"]["lo"]), ("ITEM_CODEX set piece text", 30, 25))
        for n in ("Whitstan's Guard", "Griswold's Redemption"):
            self.assertEqual((c[n]["src"], c[n]["from"]), ("range", "ITEM_CODEX set piece text"), n)
        bb = c["Beast Bite Ring"]
        self.assertEqual(bb["src"], "unknown")
        self.assertEqual(bb["why"], 'no property text is on record under "Beast Bite Ring", "The Beast Bite Ring" '
                                    '(ITEM_CODEX, its set pieces, RUNEWORD_TIP, ITEM_TIP)')

    def test_the_codex_spelling_table_is_what_the_tables_say(self):
        """MP_TEXT_ALIAS is re-derived here from the page's own tables: every game unique / set name that no folded
        key reaches, paired with the one codex set-piece name within two letters of it. Exactly, both ways."""
        out = _drive("""
          out.alias = MP_TEXT_ALIAS; out.keys = Object.keys(ITEM_CODEX).concat(Object.keys(ITEM_TIP));
          out.mem = []; Object.keys(ITEM_CODEX).forEach(function(k){ (ITEM_CODEX[k].setMembers || []).forEach(function(m){ out.mem.push(m.name); }); });""")
        _, named, _ = MSM.embedded()

        def fold(x):
            x = re.sub(r"\s*\([^)]*\)\s*$", "", x.lower().replace("\u2019", "'"))
            return re.sub(r"\s+", " ", re.sub(r"^the\s+", "", x)).strip()

        def lev(a, b):
            prev = list(range(len(b) + 1))
            for i, ca in enumerate(a, 1):
                cur = [i]
                for j, cb in enumerate(b, 1):
                    cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
                prev = cur
            return prev[-1]
        reached = set(fold(k) for k in out["keys"] + out["mem"])
        game = set(fold(n) for n in named)
        mem = dict((fold(m), m) for m in out["mem"] if fold(m) not in game)
        derived = {}
        for n in named:
            f = fold(n)
            if f in reached:
                continue
            near = [m for g, m in mem.items() if abs(len(g) - len(f)) <= 2 and lev(f, g) <= 2]
            if len(near) == 1:
                derived[f] = near[0]
        self.assertEqual(out["alias"], derived, "MP_TEXT_ALIAS is not what the page's own tables say")
        self.assertGreater(len(derived), 0)

    def test_two_texts_that_disagree_print_their_union_and_say_so(self):
        out = _drive("""
          var c = window._mpContrib({ name: "Arioc's Needle", source: 'manual' });
          out.c = { from: c.from, allsk: c.per.allsk, note: c.note };
          out.s = window._mpSumStat([c], 'allsk');""")
        self.assertEqual((out["c"]["allsk"]["lo"], out["c"]["allsk"]["hi"]), (2, 4),
                         "one text's reading was taken over the other's without a word")
        self.assertEqual(out["c"]["note"]["allsk"], "ITEM_CODEX says 2, ITEM_TIP says 2\u20134")
        self.assertEqual((out["s"]["text"], out["s"]["tag"]), ("2\u20134", "TEXT"))
        self.assertIn("(ITEM_CODEX says 2, ITEM_TIP says 2\u20134)", out["s"]["say"])

    def test_vitality_and_energy_leave_life_and_mana_unknown(self):
        out = _drive("""
          var C = window._mpContrib, S = window._mpSumStat;
          out.oc = { life: S([C({ name: 'The Oculus', source: 'manual' })], 'life'), mana: S([C({ name: 'The Oculus', source: 'manual' })], 'mana') };
          out.imp = S([C({ name: 'X', source: 'import', props: [{ stat: 'vitality', value: 20 }, { stat: 'maxhp', value: 30 }] })], 'life');""")
        self.assertEqual(out["oc"]["life"]["kind"], "unknown", "The Oculus's +20 Vitality left Life a complete-looking 0")
        self.assertIn("+Vitality adds life by the character's class", out["oc"]["life"]["why"])
        self.assertEqual(out["oc"]["mana"]["kind"], "unknown")
        self.assertEqual((out["imp"]["text"], out["imp"]["tag"]), ("\u2265 30", "MIXED"))


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheStoreIsAccountStateAndTravels(unittest.TestCase):

    def _run(self, scenario):
        s = _src()
        router = _between(s, "window._LP_FORKED = new Set([", "// v1478 — THE ROUTE, PUBLISHED.")
        backup = _between(s, "function _collectProgress(){", "function _progressSnapshot(){")
        js = r"""
          var RAWD = {}, RAW = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAWD, k) ? RAWD[k] : null; },
            setItem: function(k, v){ RAWD[k] = String(v); }, removeItem: function(k){ delete RAWD[k]; },
            key: function(i){ return Object.keys(RAWD)[i]; } };
          Object.defineProperty(RAW, 'length', { get: function(){ return Object.keys(RAWD).length; } });
          var window = { localStorage: RAW, D2R_PROFILE: 'main' };
          %s
          %s
          var out = {};
          %s
          console.log(JSON.stringify(out));""" % (router, backup, scenario)
        r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise AssertionError("the shipped router / exporter would not run - UNKNOWN: %s" % r.stderr[:600])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_the_store_forks_per_world_like_the_assignments(self):
        out = self._run("""
          window._D2R_OWNER = false; window._D2R_PFX = 'I\u00b7abcd1234\u00b7'; window._D2R_LPFX = 'IL\u00b7abcd1234\u00b7';
          out.guest = [window.LSR.key('d2r_muleEquip'), window.LSR.key('d2r_muleAssign')];
          window._D2R_OWNER = true; window._D2R_LPFX = 'L\u00b7'; window.D2R_PROFILE = 'ladder';
          out.ladder = [window.LSR.key('d2r_muleEquip'), window.LSR.key('d2r_muleAssign')];""")
        self.assertEqual(out["guest"], ["I\u00b7abcd1234\u00b7d2r_muleEquip", "I\u00b7abcd1234\u00b7d2r_muleAssign"],
                         "a guest's doll would land in the owner's store")
        self.assertEqual(out["ladder"], ["L\u00b7d2r_muleEquip", "L\u00b7d2r_muleAssign"], "ladder and main share one doll")

    def test_the_store_rides_backup_and_share(self):
        out = self._run("""
          window._D2R_OWNER = false; window._D2R_PFX = 'I\u00b7abcd1234\u00b7'; window._D2R_LPFX = 'IL\u00b7abcd1234\u00b7';
          window.LSR.setItem('d2r_muleEquip', '{"uni-armor":{"setI":{"head":{"name":"Shako","source":"manual","at":"x"}}}}');
          window.LSR.setItem('d2r_muleAssign', '{"Shako":"uni-armor"}');
          out.snap = _collectProgress();""")
        self.assertEqual(out["snap"].get("d2r_muleEquip"),
                         '{"uni-armor":{"setI":{"head":{"name":"Shako","source":"manual","at":"x"}}}}',
                         "Backup & Share does not carry the doll, so a restore brings every locker back naked")
        self.assertIn("d2r_muleAssign", out["snap"])


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheWindowAroundThePicker(unittest.TestCase):

    def test_esc_closes_the_picker_first_then_the_window(self):
        out = _drive("""
          window.openMuleCard('uni-armor'); window._mpPick('glov');
          out.open = box.innerHTML.indexOf('class="mp-pick"') >= 0;
          fire('keydown', { key: 'Escape', target: null });
          out.afterOne = { pick: box.innerHTML.indexOf('class="mp-pick"') >= 0, hidden: box.hidden };
          fire('keydown', { key: 'Escape', target: null });
          out.afterTwo = { hidden: box.hidden, switched: switched };""")
        self.assertTrue(out["open"])
        self.assertEqual(out["afterOne"], {"pick": False, "hidden": False}, "the first Esc did not close ONLY the picker")
        self.assertEqual(out["afterTwo"], {"hidden": True, "switched": ["vault"]}, "the second Esc did not close the window")

    def test_a_worn_copy_leaves_the_stash_on_both_surfaces(self):
        out = _drive("""
          window.openMuleCard('uni-armor');
          var cnt = function(){ var h = box.innerHTML, i = h.indexOf('<div class="mp-view mp-v-stash"'), j = h.indexOf('<div class="mp-view mp-v-tree"');
                                return (h.slice(i, j).match(/class="vd-item/g) || []).length; };
          out.before = cnt();
          window._mpPick('rarm'); choose('The Oculus');
          out.after = cnt();
          var g = /<div class="vd-goldbox"( title="[^"]*")?>([^<]*)<\\/div>/.exec(box.innerHTML);
          out.gold = g[2]; out.goldTitle = g[1] || '';
          out.items = /<span class="mp-box-k">Items<\\/span><span class="mp-box-v">(\\d+)<\\/span>/.exec(box.innerHTML)[1];
          out.load = window._muleLoad(%s, window._mpWornFor('uni-armor'));
          out.load = { phys: out.load.phys, worn: out.load.worn, sized: out.load.sized.length };
          out.renders = renders;""" % json.dumps(sorted(LOCKER)))
        self.assertEqual(out["after"], out["before"] - 1, "the worn copy is still drawn in the stash")
        # #174 v-B review — the worn count keeps the gold box on one line; the title carries the whole sentence
        self.assertTrue(out["gold"].endswith(" · 1 worn"), out["gold"])
        self.assertIn("+ 1 worn on the doll = %d on this mule" % len(LOCKER), out["goldTitle"])
        self.assertEqual(out["items"], str(len(LOCKER)), "a worn item stopped counting as one of this locker's items")
        self.assertEqual(out["load"], {"phys": len(LOCKER), "worn": 1, "sized": len(LOCKER) - 1})
        self.assertGreater(out["renders"], 0, "equipping did not refresh the shelf, whose gauge the worn copy frees")
        # the shelf card is the other surface (v2211): its _muleLoad call carries the same worn map — the SHIPPED line
        s = _src()
        shelf = (_line(s, "      try { if (_isMule && typeof _muleLoad === 'function') _ld = _muleLoad(items.concat(magicItems)")
                 + _line(s, "      catch(e){ _ld = null; }"))
        js = ("var got = null, _isMule = true, items = ['A'], magicItems = [], m = { id: 'uni-armor' }, _ld = null;"
              "function _muleLoad(n, w){ got = w; return {}; } function _mpWornFor(id){ return { mule: id }; }\n"
              + shelf + "\nconsole.log(JSON.stringify(got));")
        r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr[:400])
        self.assertEqual(json.loads(r.stdout.strip()), {"mule": "uni-armor"},
                         "the shelf card packs without the doll's worn map, so its gauge and the window disagree")

    def test_an_equipped_slot_shows_its_art_under_one_tooltip(self):
        out = _drive("""
          window.openMuleCard('uni-armor'); window._mpPick('neck'); choose("Mara's Kaleidoscope");
          var h = box.innerHTML, i = h.indexOf('data-slot="neck"'); out.neck = h.slice(h.lastIndexOf('<button', i), h.indexOf('</button>', i) + 9);
          out.unq = /<button type="button" class="mp-unq" data-fk="unq-neck"[^>]*onclick="window._mpUnequip\\('neck'\\)"/.test(h);
          var j = h.indexOf('data-slot="head"'); out.head = h.slice(h.lastIndexOf('<button', j), h.indexOf('>', j) + 1);
          out.ctxEmpty = window._mpCtx({ preventDefault: function(){} }, 'head');
          var prevented = 0; out.ctxFull = window._mpCtx({ preventDefault: function(){ prevented++; } }, 'neck');
          out.prevented = prevented; out.afterCtx = (eq()['uni-armor'].setI || {}).neck || null;""")
        self.assertIn(' mp-has"', out["neck"])
        self.assertIn('<span class="d2art-wrap lg" role="img" aria-label="Mara&#39;s Kaleidoscope">', out["neck"],
                      "the equipped slot does not show the item's art (the board's hover anchor)")
        self.assertNotIn(' title="', out["neck"], "an equipped slot carries a native title — an OS box over the hover card")
        self.assertTrue(out["unq"], "the equipped slot has no small ✕ to unequip it")
        self.assertIn(' title="helm — empty.', out["head"])
        self.assertIn('onclick="window._mpPick(\'head\')"', out["head"])
        self.assertIs(out["ctxEmpty"], True, "right-click on an empty slot swallowed the browser's own menu")
        self.assertIs(out["ctxFull"], False)
        self.assertEqual((out["prevented"], out["afterCtx"]), (1, None), "right-click did not unequip")

    def test_notes_is_an_editor_saved_through_the_routed_store(self):
        out = _drive("""
          window.openMuleCard('uni-armor');
          out.editor = /<textarea class="mp-note-ed" data-fk="note"[^>]*>body armor · helms · shields<\\/textarea>/.test(box.innerHTML);
          window._mpNoteInput('half typed'); window.openMuleCard('uni-armor');
          out.draft = /<textarea class="mp-note-ed"[^>]*>half typed<\\/textarea>/.test(box.innerHTML);
          window.vaultCloseCard(); out.closed = roster[0].note; out.stored = JSON.parse(STORE['d2r_muleRoster'] || '[]')[0];
          window.openMuleCard('uni-armor');
          var blurred = 0, el = { value: 'keeps the good rings', blur: function(){ blurred++; } };
          window._mpNoteKey({ key: 'Enter', shiftKey: true, preventDefault: function(){} }, el); out.shift = roster[0].note;
          window._mpNoteKey({ key: 'Enter', shiftKey: false, preventDefault: function(){} }, el);
          out.enter = [roster[0].note, JSON.parse(STORE['d2r_muleRoster'])[0].note, blurred];""")
        self.assertTrue(out["editor"], "NOTES is not an editor over the locker's own note")
        self.assertTrue(out["draft"], "a re-render underneath him threw away the note he was typing")
        self.assertEqual(out["closed"], "half typed", "closing the window dropped the note he was typing")
        self.assertEqual((out["stored"] or {}).get("note"), "half typed", "the note did not reach d2r_muleRoster")
        self.assertEqual(out["shift"], "half typed", "Shift+Enter saved instead of starting a new line")
        self.assertEqual(out["enter"], ["keeps the good rings", "keeps the good rings", 1])


class TheSlotTableIsTheGames(unittest.TestCase):

    def setUp(self):
        import item_tables as IT
        self.T = IT.load()
        self.assertIsNotNone(self.T, "tv/item_tables.json is missing — UNKNOWN, not passing")
        self.slots, self.named, self.rules = MSM.embedded()

    def test_every_name_in_the_block_is_a_base_of_the_kind_it_claims(self):
        by_kind = {}
        for v in self.T["items"].values():
            by_kind.setdefault(v["kind"], set()).add(v["name"])
        armourish = set()
        for k in ("helm", "armor", "shield", "gloves", "belt", "boots"):
            armourish |= set(self.slots[k])
        self.assertEqual(armourish, by_kind["armor"], "the worn-armour slots are not exactly the game's armour bases")
        self.assertEqual(set(self.slots["weapon"]), by_kind["weapon"], "the weapon slot is not exactly the game's weapons")
        carried = set()
        for k in ("ring", "amulet", "quiver", "none"):
            carried |= set(self.slots[k])
        self.assertEqual(carried, by_kind["misc"], "rings, amulets and carried things are not exactly the game's misc")
        self.assertEqual(self.slots["ring"], ["Ring"])
        self.assertIn("Amulet", self.slots["amulet"])

    def test_the_hand_and_class_rules_name_real_bases(self):
        """#174 v-B review — the hands and ammo rules name only weapons; each ammo is a quiver base; the class
        rule names weapons and armour. Which base is which is the install's to say (test_the_subtypes_...)."""
        weapons, quivers = set(self.slots["weapon"]), set(self.slots["quiver"])
        worn = weapons | set().union(*(set(self.slots[k]) for k in ("helm", "armor", "shield", "gloves", "belt", "boots")))
        self.assertEqual(sorted(self.rules["hands"]), ["12", "2"])
        for v, ns in self.rules["hands"].items():
            self.assertTrue(ns and set(ns) <= weapons, "hands %s names a non-weapon" % v)
        self.assertEqual(set(self.rules["ammo"]), quivers, "a bow shoots something that is not a quiver base")
        for v, ns in self.rules["ammo"].items():
            self.assertTrue(set(ns) <= set(self.rules["hands"]["2"]), "something that shoots %s is not two-handed" % v)
        for v, ns in self.rules["class"].items():
            self.assertIn(v, MSM.CLASS_NAME.values())
            self.assertTrue(ns and set(ns) <= worn, "the %s class rule names a base that is not worn" % v)
        self.assertIn("Hydra Bow", self.rules["ammo"]["Arrows"])
        self.assertIn("Swirling Crystal", self.rules["class"]["Sorceress"])

    def test_the_named_bases_are_derived_from_the_game_tables(self):
        nb, dropped = MSM.named(self.T, self.slots)
        self.assertEqual(self.named, nb, "MULE_NAMED_BASE is not what tv/item_tables.json says — re-run the generator")
        self.assertEqual(self.named.get("The Stone of Jordan"), "Ring")
        self.assertEqual(self.named.get("Harlequin Crest"), "Shako")
        self.assertGreater(len(self.named), 500)

    def test_the_subtypes_are_what_the_install_says(self):
        code, say = MSM.check()
        if code == MSM.SKIP:
            self.skipTest("UNMEASURED here, not passing: %s" % say)
        self.assertEqual(code, 0, say)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#174 v-B - an analyzer route replaces what his hand placed (a manual placement must always win)",
        "file": "bible.html",
        "find": "    if (cur && rn < rc) return { ok: false, all: all, why: cur.name + ' was ' + MP_SRC_SAY[cur.source]\n",
        "replace": "    if (false) return { ok: false, all: all, why: cur.name + ' was ' + MP_SRC_SAY[cur.source]\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B - a ring is offered for the helm (fit is ignored)",
        "file": "bible.html",
        "find": "        if (_wears.indexOf(f.kind) < 0){ _other.push(",
        "replace": "        if (false){ _other.push(",
        "matches": 1,
    },
    {
        "why": "#174 v-B - an item whose slot cannot be established is offered anyway, and not counted",
        "file": "bible.html",
        "find": "        if (!f.kind){ _unknown.push(n + ' (' + f.why + ')'); return; }\n",
        "replace": "        if (!f.kind){ f.kind = MP_SLOT_WEARS[_ps][0]; }\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B - a rolled range is averaged into one number",
        "file": "bible.html",
        "find": "      var lo = Math.min(a, b), hi = Math.max(a, b);\n",
        "replace": "      var lo = (a + b) / 2, hi = (a + b) / 2;\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B - a mixed sum reads as one number instead of >= exact + range",
        "file": "bible.html",
        "find": "    if (mixed) return { kind: 'mixed', text: '≥ ' + parts",
        "replace": "    if (mixed) return { kind: 'mixed', text: parts",
        "matches": 1,
    },
    {
        "why": "#174 v-B - known zeros beside an UNKNOWN part print a measured-looking 0",
        "file": "bible.html",
        "find": "      if (unk.length) return { kind: 'unknown', why: unk.join('; ') };\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B - a line that needs the character (per level) is read as nothing instead of UNKNOWN",
        "file": "bible.html",
        "find": "      return lk.map(function(k){ return { k: k, why: 'scales with character level, and a locker has none' }; });\n",
        "replace": "      return [];\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B - an imported item's rolled props stop saying EXACT",
        "file": "bible.html",
        "find": "      return { name: name, src: 'exact', from: 'its .d2s', per: per };\n",
        "replace": "      return { name: name, src: 'range', from: 'its .d2s', per: per };\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B - d2r_muleEquip leaves the fork list, so a guest's doll lands in the owner's store",
        "file": "bible.html",
        "find": "\"d2r_muleRoster\", \"d2r_muleEquip\", \"d2r_vaultRerouteDone\"",
        "replace": "\"d2r_muleRoster\", \"d2r_vaultRerouteDone\"",
        "matches": 1,
    },
    {
        "why": "#174 v-B - Backup & Share stops carrying the doll (filed as a pointer that never travels)",
        "file": "bible.html",
        "find": "                 'd2r_ownerClaim':1, 'd2r_installIdCache':1, 'd2r_installId':1 };",
        "replace": "                 'd2r_ownerClaim':1, 'd2r_installIdCache':1, 'd2r_installId':1, 'd2r_muleEquip':1 };",
        "matches": 1,
    },
    {
        "why": "#174 v-B - Esc closes the whole window while the picker is open (the picker must close first)",
        "file": "bible.html",
        "find": "    if (e.key !== 'Escape' || !openMuleId || !_mpPickAt) return;\n",
        "replace": "    if (e.key !== 'Escape' || !openMuleId || !_mpPickAt || true) return;\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B - a worn copy is still drawn in the stash",
        "file": "bible.html",
        "find": "      for (var _ci = 0; _ci < cc - _w; _ci++){\n",
        "replace": "      for (var _ci = 0; _ci < cc; _ci++){\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B - the shelf card packs without the doll's worn map (its gauge and the window disagree)",
        "file": "bible.html",
        "find": "_ld = _muleLoad(items.concat(magicItems), (typeof _mpWornFor === 'function') ? _mpWornFor(m.id) : null); }",
        "replace": "_ld = _muleLoad(items.concat(magicItems)); }",
        "matches": 1,
    },
    {
        "why": "#174 v-B - an equipped slot keeps a native title, drawing an OS box over the board's hover card",
        "file": "bible.html",
        "find": "        + (e ? '' : ' title=\"'+esc(say)+'\"') + ' aria-label=\"'+esc(say)+'\">'\n",
        "replace": "        + ' title=\"'+esc(say)+'\"' + ' aria-label=\"'+esc(say)+'\">'\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B - the note is not saved through the routed store",
        "file": "bible.html",
        "find": "    try { saveR(); }\n    catch (e){ m.note = old;",
        "replace": "    try { void 0; }\n    catch (e){ m.note = old;",
        "matches": 1,
    },
    {
        "why": "#174 v-B - a re-render underneath him throws away the note he is typing",
        "file": "bible.html",
        "find": "      +     esc((_mpNoteDraft && _mpNoteDraft.id === muleId) ? _mpNoteDraft.v : (m.note || '')) + '</textarea>'\n",
        "replace": "      +     esc(m.note || '') + '</textarea>'\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B - the game's unique table stops naming a base, so Stone of Jordan has no slot",
        "file": "bible.html",
        "find": "    if (_nb) add(\"the game's unique / set table\", _nb);\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B - the generated slot map loses the ring (the install table is no longer what the page reads)",
        "file": "bible.html",
        "find": "    \"ring\": \"Ring\",\n",
        "replace": "    \"ring\": \"\",\n",
        "matches": 1,
    },
    # ── #174 v-B review ──
    {
        "why": "#174 v-B review - two classes' skill lines are summed into one number no character gets",
        "file": "bible.html",
        "find": "    if (nCls > 1) return { kind: 'unknown', why: 'the worn lines add to different classes — '",
        "replace": "    if (false) return { kind: 'unknown', why: 'the worn lines add to different classes — '",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - the .d2s path throws item_addclassskills' class param away again",
        "file": "bible.html",
        "find": "          var cn = MP_CLASS_BY_ID[p.param], c = at('clsk');",
        "replace": "          var cn = MP_CLASS_BY_ID[1], c = at('clsk');",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - a class-skill text line loses the class it adds to",
        "file": "bible.html",
        "find": "      var cls = (MP_PROP_RULES[i][1][0] === 'clsk' && m[3]) ?",
        "replace": "      var cls = (false && m[3]) ?",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - an item reassigned to another locker stays live on the first doll (summed, and worn twice)",
        "file": "bible.html",
        "find": "        if (e.source !== 'import' && assign[e.name] !== muleId){ dead[set + '.' + slot] = 'no longer in this locker'; return; }",
        "replace": "        if (false){ dead[set + '.' + slot] = 'no longer in this locker'; return; }",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - the stats stop saying which slots they left out",
        "file": "bible.html",
        "find": "      + (_unworn.length ? '<div class=\"mp-st-src mp-st-dead\">",
        "replace": "      + (false ? '<div class=\"mp-st-src mp-st-dead\">",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - a two-hander leaves the left hand free for a shield (Windforce beside Stormshield)",
        "file": "bible.html",
        "find": "    if (R.hands === 2){\n",
        "replace": "    if (false){\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - a two-handed weapon is offered for the left hand",
        "file": "bible.html",
        "find": "      if (L.hands === 2) return 'a two-handed '",
        "replace": "      if (false) return 'a two-handed '",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - a class weapon that class never dual-wields (an orb) is offered as a second weapon",
        "file": "bible.html",
        "find": "      if (L.cls && L.cls !== 'Assassin') return",
        "replace": "      if (false) return",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - two weapons are offered together that no class holds (a sword beside a claw)",
        "file": "bible.html",
        "find": "      if (!R.cls && !L.cls) return null;\n",
        "replace": "      return null;\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - the picker offers a piece of another class than the one already worn",
        "file": "bible.html",
        "find": "          if (g.cls && _clsOn[ci].cls !== g.cls) why =",
        "replace": "          if (false) why =",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - a stored doll of two classes is summed as if one character wore it",
        "file": "bible.html",
        "find": "      if (x.g.cls !== first.g.cls)\n",
        "replace": "      if (false)\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - a stored shield beside a two-hander is summed and taken off the grid",
        "file": "bible.html",
        "find": "      if (why){ dead[set + '.larm'] = why; delete seen[set].larm; }",
        "replace": "      if (false){ dead[set + '.larm'] = why; delete seen[set].larm; }",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - the generated rules lose every two-hander (the install's weapons.txt is no longer read)",
        "file": "bible.html",
        "find": ", \"2\": \"",
        "replace": ", \"22\": \"",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - the store drops an import's runeword list again (Enigma reads FRW 0% EXACT)",
        "file": "bible.html",
        "find": "    if (Array.isArray(entry.runewordProps)) e.runewordProps = entry.runewordProps;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - a socketed jewel's properties never reach the EXACT sum",
        "file": "bible.html",
        "find": "      (Array.isArray(e.socketed) ? e.socketed : []).forEach(function(k){ if (k && Array.isArray(k.props)) lists.push(k.props); });\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - a runeword whose own list was not carried still reads as an EXACT number",
        "file": "bible.html",
        "find": "      if (e.isRuneword && !Array.isArray(e.runewordProps)) gap.push(",
        "replace": "      if (false) gap.push(",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - a name whose text sits under a folded key (Harlequin Crest -> (Shako)) reads UNKNOWN",
        "file": "bible.html",
        "find": "      return (ix[id] && ix[id][f]) || null;\n",
        "replace": "      return null;\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - a runeword's text in RUNEWORD_TIP is never read",
        "file": "bible.html",
        "find": "        if (rw && rw.l && rw.l.length) got.push({ lines: rw.l, from: 'RUNEWORD_TIP', key: rk });",
        "replace": "        if (false) got.push({ lines: rw.l, from: 'RUNEWORD_TIP', key: rk });",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - the codex's own set-piece spellings are not asked (Cow King's Hooves reads UNKNOWN)",
        "file": "bible.html",
        "find": "    if (MP_TEXT_ALIAS[_mpFold(bare)]) add(MP_TEXT_ALIAS[_mpFold(bare)]);\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - an UNKNOWN stops naming the keys it tried (a false 'nothing on record')",
        "file": "bible.html",
        "find": "'no property text is on record under ' + t.tried.map(function(k){ return '\"' + k + '\"'; }).join(', ')",
        "replace": "'no property text is on record for it' + t.tried.slice(0, 0).join('')",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - two texts that disagree: the first source's reading is taken without a word",
        "file": "bible.html",
        "find": "          a.lo = Math.min(a.lo, b.lo); a.hi = Math.max(a.hi, b.hi);\n        } else if",
        "replace": "          void 0;\n        } else if",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - +Vitality / +Energy are read as nothing, so Life and Mana print a complete-looking 0",
        "file": "bible.html",
        "find": "    if (_vit || _ene){\n",
        "replace": "    if (false){\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - the runeword-base fit is wrong (Enigma offered as a ring) and the harness must see it",
        "file": "bible.html",
        "find": "        if (_rw.length === 1) add('runeword base', _rw[0].base);\n",
        "replace": "        if (_rw.length === 1) add('runeword base', 'Ring');\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - a set piece's own affixes are replaced, and the harness must see it",
        "file": "bible.html",
        "find": "          if (cm && cm.affixes && cm.affixes.length) got.push({ lines: cm.affixes, from: 'ITEM_CODEX set piece', key: cm.name });",
        "replace": "          if (cm && cm.affixes && cm.affixes.length) got.push({ lines: ['+99 to All Skills'], from: 'ITEM_CODEX set piece', key: cm.name });",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - findSetPiece's slot is ignored (a set piece fits the ring), and the harness must see it",
        "file": "bible.html",
        "find": "if (_sp) add('set piece slot', _sp.slot); } catch (e) {}",
        "replace": "if (_sp) add('set piece slot', 'ring'); } catch (e) {}",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - the gold box says the worn copies in a sentence that wraps it to two lines",
        "file": "bible.html",
        "find": "+ ' in inventory · ' + _wornHere + ' worn</div>'",
        "replace": "+ ' in inventory · ' + _wornHere + ' worn on the doll · ' + (_thisMuleN + _wornHere) + ' on this mule</div>'",
        "matches": 1,
    },
]
