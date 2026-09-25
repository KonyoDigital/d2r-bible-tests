# -*- coding: utf-8 -*-
"""#174 v-B2 — THE CHARACTER BUILDER IS THEIR BUILDER: THE ENTIRE DATABASE, THEIR PICKER, EVERY ROLL HONEST.

His words (2026-09-25): "if i click on helmet lets say.. it shold give me the options from the entire database to
put as a helmet or runeword and based on the base item.. exactly like the d2r one to one", and "the mules are mules
and continue to be so the items coming in dont mix up this... this is just a simple tool for character building".

This law drives the SHIPPED builder — the ⟦CHARACTER BUILDER JS⟧ block, the ⟦CB_DB⟧ block tv/char_builder_db.py
generated from his install, the board's own CHARS, LSR and fork sets, and the Backup exporter, each CUT from
bible.html between two real boundaries and run in node over a small DOM stand-in (never re-typed here):

  · THE RAIL AND THE TABS ARE THE DATA'S, PER SLOT. The helm's rail is their Helmets · Circlets · Pelts (Druid) ·
    Primal Helms (Barbarian), from itemtypes.txt's own UI categories and class locks; every base the game wears on
    the head sits under one of them. A quality tab shows only when the data holds something for it: gloves have NO
    Runewords tab (no runeword names a glove type), exactly as theirs (06_gloves_filters). The list is the ENTIRE
    database for the slot: every unique, set item, runeword and base the tables put there, not a sample.
  · A RUNEWORD'S BASES CARRY THE SOCKET COUNT. Enigma (Jah Ith Ber) is offered only on body armor that can hold 3
    sockets — Mage Plate yes (3), Quilted Armor no (2) — and Spirit (4 runes, swords and shields) on a Crystal Sword
    and a Monarch, never a Short Sword (2 sockets) and never an axe. The runeword's sockets are its runes, locked.
  · A ROLL IS A BOX CLAMPED TO ITS RANGE. Crown of Ages rolls All Resistances 20-30 (uniqueitems.txt res-all 20 30):
    typed 28 is stored EXACT under the game's own key (p2 = prop2), 35 is REFUSED and nothing is saved, a blank box
    is the range again. Hand-checked Defense: Corona's max defense is 165 (armor.txt), an item with Enhanced
    Defense rolls its base at max + 1 = 166, x 1.5 (its +50% ED) = 249, + its 100-150 flat => untouched 349-399
    (a RANGE, never averaged), typed 150 => exactly 399 — their tooltip's number (05_hover_equipped).
  · THE STORE IS THE BRIEF'S SHAPE, FORKED PER ACCOUNT, IN BACKUP & SHARE: d2r_charBuilds {buildId: {name, cls,
    level, sets: [{name: 'Set 1', slots: {slot: {name, base, sockets, eth, rolls, socketed}}}]}} through LSR; on the
    ladder profile it is L·d2r_charBuilds; _collectProgress exports it.
  · Esc CLOSES THE TOP LAYER FIRST: the picker, then the builder — through the document's capture-phase listener,
    the same way the console's Esc probe arrives.
  · IT READS NO VAULT STORE. A whole session — open, pick, roll, an inventory charm, the stash, close — reads only
    d2r_charBuilds and its own selection key, and calls no vault or mule function (his rule: the items coming in
    do not mix with this).
  · THE TOOLTIP'S COLOUR MAP IS SPEC §8. unique rgb(199,179,119) · set rgb(0,255,0) · crafted rgb(255,168,0) ·
    base white · magic and every property rgb(105,105,255) · a failed requirement rgb(255,77,77) on rgba(8,8,8,.95)
    with 6px 9px padding — read out of the SHIPPED stylesheet — and a requirement is red only when the character is
    KNOWN to fail it: the level is the build's, strength and dexterity are UNKNOWN and never red on a guess.
  · CRAFTED IS THE GAME'S CUBE, WITNESSED BY THE BOARD: every craft the board's CRAFTS names (Caster / Blood / Safety
    / Hit Power x its nine slots) is a crafted recipe in the database, by the game's own name.
  · THE BLOCK IS THE COMMITTED TABLES' WORDS: every base, unique, set item and runeword name in ⟦CB_DB⟧ is the name
    tv/item_tables.json carries for the same code / id / key — checked here without an install. Whether the block
    is what the install says TODAY is tv/char_builder_db.py's --check (UNKNOWN, never green, without an install).

⚠ WHAT THIS LAW CANNOT SEE: pixels — that is test_the_character_builder_fits_at_every_width.py, in a real browser.
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

NODE = shutil.which("node")
BIBLE = os.path.join(ROOT, "bible.html")


def _src():
    with io.open(BIBLE, encoding="utf-8") as f:
        return f.read()


def _between(s, start, end):
    assert s.count(start) == 1, "the cut start %r is not unique (%d) — the anchor moved" % (start[:60], s.count(start))
    i = s.index(start) + len(start)
    j = s.index(end, i)
    return s[i:j]


def _builder_js(s):
    return _between(s, '<script id="cb-builder-js">', "\n</script>")


def _builder_css(s):
    return _between(s, '<style id="cb-builder-css">', "\n</style>")


def _db_json(s):
    return _between(s, '<script type="application/json" id="cb-db">', "</script>")


def _stage(s):
    """the board pieces the builder stands on, each cut between its own boundaries"""
    lp = "window._LP_FORKED = new Set([" + _between(s, "window._LP_FORKED = new Set([", "]);") + "]);\n"
    wp = "window._WP_FORKED = new Set(" + _between(s, "window._WP_FORKED = new Set(", ");\n") + ");\n"
    lsr = "window.LSR = (function(){" + _between(s, "window.LSR = (function(){", "\n})();") + "\n})();\n"
    chars = "const CHARS = {" + _between(s, "const CHARS = {", "\n};\n") + "\n};\n"
    backup = "function _collectProgress(){" + _between(s, "function _collectProgress(){", "\nfunction _progressSnapshot(){") + "\n"
    return lp, wp, lsr, chars, backup


HARNESS = r"""
var RAW = {}, READS = [], CALLS = [], LISTEN = [];
var localStorage = {
  getItem: function(k){ READS.push(k); return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
  setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; },
  key: function(i){ return Object.keys(RAW)[i] == null ? null : Object.keys(RAW)[i]; }
};
Object.defineProperty(localStorage, 'length', { get: function(){ return Object.keys(RAW).length; } });
var window = globalThis;
window.localStorage = localStorage;
window._D2R_OWNER = true; window.D2R_PROFILE = 'main'; window._D2R_LPFX = 'L·'; window._D2R_PFX = 'W·';
window._D2R_INSTALL = 'test';
/* the vault and the mules, as spies: the builder must never touch them */
['vaultAssign', 'openMuleCard', 'tvVaultRegister', '_muleLoad', 'vaultCloseCard', 'muleById'].forEach(function(n){
  window[n] = function(){ CALLS.push(n); };
});
/* his real stores are there, full: reading any of them is the defect */
RAW['d2r_muleAssign'] = '{"Harlequin Crest (Shako)":"m1"}'; RAW['d2r_owned'] = '["Harlequin Crest"]';
RAW['d2r_muleEquip'] = '{}'; RAW['d2r_muleRoster'] = '[]'; RAW['d2r_foundLog'] = '[]';
function Cls(){ var c = {}; return { add: function(x){ c[x] = 1; }, remove: function(x){ delete c[x]; },
  contains: function(x){ return !!c[x]; }, toggle: function(x, on){ if (on === undefined) on = !c[x]; if (on) c[x] = 1; else delete c[x]; return on; } }; }
function El(id){ this.id = id || ''; this.hidden = false; this.attrs = {}; this._html = ''; this.style = {}; this.classList = Cls();
  this.scrollTop = 0; this.children = []; this.textContent = ''; }
El.prototype.setAttribute = function(k, v){ this.attrs[k] = String(v); if (k === 'id') this.id = String(v); };
El.prototype.getAttribute = function(k){ return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null; };
El.prototype.querySelector = function(){ return null; };
El.prototype.querySelectorAll = function(){ return []; };
El.prototype.getBoundingClientRect = function(){ return { left: 0, top: 0, width: 100, height: 40, right: 100, bottom: 40 }; };
El.prototype.appendChild = function(c){ this.children.push(c); if (c.id) ELS[c.id] = c; return c; };
El.prototype.focus = function(){};
Object.defineProperty(El.prototype, 'innerHTML', { get: function(){ return this._html; }, set: function(v){ this._html = String(v); } });
var ELS = {}, MODAL = new El('cb-modal');
var DBEL = new El('cb-db'); DBEL.textContent = __DB__;
var document = {
  body: new El('body'), documentElement: new El('html'), activeElement: null,
  getElementById: function(id){
    if (id === 'cb-db') return DBEL;
    if (id === 'cb-modal') return (ELS['cb-win'] && ELS['cb-win']._html.indexOf('id="cb-modal"') >= 0) ? MODAL : null;
    return ELS[id] || null;
  },
  createElement: function(){ return new El(''); },
  querySelector: function(){ return null; }, querySelectorAll: function(){ return []; },
  addEventListener: function(t, f, cap){ LISTEN.push([t, f, !!cap]); }
};
document.body.appendChild = function(c){ if (c.id) ELS[c.id] = c; return c; };
window.document = document;
window.addEventListener = function(){};
window.innerWidth = 2000; window.innerHeight = 1300;
function artOr(n){ return '<span class="d2art-wrap">' + n + '</span>'; }
function key(k){ var fired = []; LISTEN.forEach(function(l){ if (l[0] === 'keydown' && l[2]) l[1]({ key: k, preventDefault: function(){}, stopImmediatePropagation: function(){ fired.push('stopped'); } }); }); return fired; }
function slots(){ var b = JSON.parse(RAW['d2r_charBuilds'] || '{}'); var k = Object.keys(b)[0]; return k ? b[k] : null; }
"""


def _run(body, db=None):
    s = _src()
    lp, wp, lsr, chars, backup = _stage(s)
    prog = (HARNESS.replace("__DB__", json.dumps(db if db is not None else _db_json(s)))
            + lp + wp + lsr + chars + backup + _builder_js(s) + "\n;(function(){ var OUT = {};\n" + body
            + "\nprocess.stdout.write(JSON.stringify(OUT)); })();\n")
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise AssertionError("node failed: " + (r.stderr or r.stdout)[-2000:])
    return json.loads(r.stdout)


def _db():
    return json.loads(_db_json(_src()))


@unittest.skipIf(NODE is None, "node is not on this machine")
class TheBuilderIsTheirBuilder(unittest.TestCase):

    def test_the_rail_and_the_tabs_come_from_the_data_per_slot(self):
        out = _run(r"""
          window.openCharBuilder();
          OUT.head = window._cbRailOf('head').map(function(r){ return [r[0], r[1], r[2] >= 0 ? window._cbDb().cls[r[2]].n : null]; });
          OUT.headTabs = window._cbQTabs('head').map(function(t){ return t[0]; });
          OUT.glovTabs = window._cbQTabs('glov').map(function(t){ return t[0]; });
          OUT.invRail = window._cbRailOf('inv').map(function(r){ return r[0]; });
          OUT.invTabs = window._cbQTabs('inv').map(function(t){ return t[0]; });
          OUT.headN = window._cbForSlot('head').length;
          OUT.headQ = {}; window._cbForSlot('head').forEach(function(x){ OUT.headQ[x[2]] = (OUT.headQ[x[2]] || 0) + 1; });
          OUT.headNames = window._cbForSlot('head').map(function(x){ return x[1]; });
          OUT.glovNames = window._cbForSlot('glov').map(function(x){ return x[1]; });
          OUT.rwForGloves = window._cbForSlot('glov').filter(function(x){ return x[2] === 'r'; }).length;
        """)
        self.assertEqual(out["head"], [["Helmets", -1, None], ["Circlets", 1, None], ["Pelts", 2, "Druid"],
                                       ["Primal Helms", 3, "Barbarian"]],
                         "the helm's rail is not their Helmets / Circlets / Pelts (Druid) / Primal Helms: %s" % out["head"])
        self.assertEqual(out["headTabs"], ["all", "r", "u", "b", "c", "s", "ex"])
        self.assertEqual(out["glovTabs"], ["all", "u", "b", "c", "s", "ex"],
                         "gloves show a Runewords tab although no runeword names a glove type")
        self.assertEqual(out["rwForGloves"], 0)
        self.assertEqual(out["invRail"], ["Inventory", "Small Charms", "Large Charms", "Grand Charms",
                                          "Crafted Sunder Charms"])
        self.assertEqual(out["invTabs"], ["all", "u", "b", "m", "ex"])
        # THE ENTIRE DATABASE: every head base the block holds (spawnable), every unique / set on one, every crafted
        # helm and every runeword a helm can carry — derived here from the block's own tables, not a hand list
        db = _db()
        head_types = set()
        for row in db["rail"]["head"]:
            head_types |= set(row[1])
        want = set(b[0] for c, b in db["b"].items() if b[20] and b[1] in head_types)
        want |= set(x[1] for x in db["it"] if x[2] in ("u", "s") and db["b"].get(x[3], [None, None])[1] in head_types)
        self.assertEqual(set(out["headNames"]) & want, want, "the helm list is missing: %s" % sorted(want - set(out["headNames"]))[:10])
        for n in ("Crown of Ages", "Harlequin Crest", "Arreat's Face", "Jalal's Mane", "Tal Rasha's Horadric Crest",
                  "Corona", "Circlet", "Caster Helm", "Lore", "Dream"):
            self.assertIn(n, out["headNames"], "%s is not offered for the helm" % n)
        for n in ("The Stone of Jordan", "Windforce", "Enigma", "Stormshield"):
            self.assertNotIn(n, out["headNames"], "%s is offered for the helm" % n)
        self.assertGreater(out["headQ"].get("r", 0), 5, "helm runewords (Lore, Dream, ...) are missing: %s" % out["headQ"])
        self.assertIn("Magefist", out["glovNames"])

    def test_a_runewords_bases_carry_its_socket_count(self):
        out = _run(r"""
          window.openCharBuilder();
          var d = window._cbDb(), byName = function(n){ var h = null; d.it.forEach(function(x){ if (x[1] === n) h = x; }); return h; };
          var names = function(it){ return window._cbBasesOf(it).map(function(c){ return d.b[c][0]; }); };
          var en = byName('Enigma'), sp = byName('Spirit');
          OUT.enigma = names(en); OUT.spirit = names(sp);
          OUT.enigmaRunes = en[7].runes.length; OUT.spiritRunes = sp[7].runes.length;
          OUT.minSockEnigma = Math.min.apply(null, window._cbBasesOf(en).map(function(c){ return window._cbMaxSock(c, 99); }));
          OUT.minSockSpirit = Math.min.apply(null, window._cbBasesOf(sp).map(function(c){ return window._cbMaxSock(c, 99); }));
          OUT.entry = window._cbEntryFor(en);
          OUT.quilted = window._cbMaxSock('qui', 99); OUT.mage = window._cbMaxSock('xtp', 99);
        """)
        self.assertEqual((out["enigmaRunes"], out["spiritRunes"]), (3, 4))
        self.assertIn("Mage Plate", out["enigma"])
        self.assertIn("Archon Plate", out["enigma"])
        self.assertNotIn("Quilted Armor", out["enigma"], "Enigma offered on a 2-socket Quilted Armor")
        self.assertEqual((out["quilted"], out["mage"]), (2, 3), "armor.txt's socket counts moved")
        self.assertGreaterEqual(out["minSockEnigma"], 3)
        self.assertIn("Crystal Sword", out["spirit"])
        self.assertIn("Monarch", out["spirit"])
        self.assertNotIn("Short Sword", out["spirit"], "Spirit offered on a 2-socket Short Sword")
        self.assertFalse(any("Axe" in n for n in out["spirit"]), "Spirit offered on an axe: %s" % out["spirit"])
        self.assertGreaterEqual(out["minSockSpirit"], 4)
        self.assertEqual((out["entry"]["sockets"], len(out["entry"]["socketed"])), (3, 3), out["entry"])

    def test_a_roll_is_clamped_to_its_range_and_typed_is_exact(self):
        out = _run(r"""
          window.openCharBuilder();
          window._cbOpenPick('slot', 'head');
          var d = window._cbDb(), coa = null; d.it.forEach(function(x){ if (x[1] === 'Crown of Ages') coa = x; });
          window._cbChoose(coa[0]);
          OUT.pure = [window._cbRoll([20, 30], '25'), window._cbRoll([20, 30], '35'), window._cbRoll([20, 30], ''), window._cbRoll([20, 30], 'x2')];
          var box = function(k, lo, hi, v){ var cls = {}; return { value: v, classList: { contains: function(c){ return c === 'cb-roll' || !!cls[c]; }, add: function(c){ cls[c] = 1; }, remove: function(c){ delete cls[c]; }, toggle: function(c, on){ if (on) cls[c] = 1; else delete cls[c]; } },
            getAttribute: function(a){ return { 'data-key': k, 'data-lo': String(lo), 'data-hi': String(hi) }[a]; }, bad: function(){ return !!cls['cb-bad']; } }; };
          var tip = function(){ var e = slots().sets[0].slots.head; return window._cbTipEntry(e, window._cbItem(e.id), 88, 'head'); };
          OUT.untouched = tip().defense;
          var b1 = box('p2', 20, 30, '35'); window._cbRollInput({ target: b1 }); OUT.refused = [b1.bad(), JSON.stringify(slots().sets[0].slots.head.rolls)];
          var b2 = box('p2', 20, 30, '28'); window._cbRollInput({ target: b2 }); OUT.typed = slots().sets[0].slots.head.rolls;
          var b3 = box('p4', 100, 150, '150'); window._cbRollInput({ target: b3 }); OUT.defense = tip().defense;
          OUT.resLine = tip().lines.map(function(l){ return l.html; }).filter(function(h){ return /All Resistances/.test(h); })[0];
          var b4 = box('p2', 20, 30, ''); window._cbRollInput({ target: b4 }); OUT.cleared = slots().sets[0].slots.head.rolls;
          OUT.resAfter = tip().lines.map(function(l){ return l.html; }).filter(function(h){ return /All Resistances/.test(h); })[0];
        """)
        ok, bad, blank, junk = out["pure"]
        self.assertEqual(ok, {"ok": True, "v": 25})
        self.assertFalse(bad["ok"])
        self.assertIn("20–30", bad["why"])
        self.assertEqual(blank, {"ok": True, "v": None})
        self.assertFalse(junk["ok"])
        # hand-checked: Corona max 165 -> ED base 166 -> x1.5 = 249 -> + 100..150
        self.assertEqual(out["untouched"], [349, 399], "an untouched Crown of Ages must read the RANGE 349-399")
        self.assertEqual(out["refused"], [True, "{}"], "a roll outside 20-30 was saved: %s" % out["refused"])
        self.assertEqual(out["typed"], {"p2": 28})
        self.assertEqual(out["defense"], [399, 399], "typed 150 must make Defense exactly 399 (their tooltip)")
        self.assertEqual(out["resLine"], "All Resistances +28")
        self.assertEqual(out["cleared"], {"p4": 150})
        self.assertEqual(out["resAfter"], "All Resistances +20-30", "a cleared box must be the range again, never a default")

    def test_the_store_is_the_brief_shape_forked_and_backed_up(self):
        out = _run(r"""
          window.openCharBuilder();
          window._cbOpenPick('slot', 'head');
          var d = window._cbDb(), pick = function(n){ var h = null; d.it.forEach(function(x){ if (x[1] === n) h = x; }); return h[0]; };
          window._cbChoose(pick('Crown of Ages'));
          window._cbOpenPick('inv', null, [0, 0]); window._cbChoose(pick('Annihilus'));
          OUT.main = Object.keys(RAW).filter(function(k){ return /charBuilds/.test(k); });
          OUT.build = slots();
          OUT.backup = Object.keys(_collectProgress()).filter(function(k){ return /charBuilds/.test(k); });
          OUT.forked = window._LP_FORKED.has('d2r_charBuilds');
          var mainBefore = RAW['d2r_charBuilds'];
          window.D2R_PROFILE = 'ladder';
          OUT.ladderSees = Object.keys(window._cbAll()).length;
          window._cbOpenNew(); window._cbNewCls('Sorceress'); window._cbNewGo();
          OUT.ladder = Object.keys(RAW).filter(function(k){ return /charBuilds/.test(k); }).sort();
          OUT.mainUntouched = RAW['d2r_charBuilds'] === mainBefore;
          OUT.ladderBackup = Object.keys(_collectProgress()).filter(function(k){ return /charBuilds/.test(k); });
          OUT.ladderBackupIsLadder = JSON.parse(_collectProgress()['d2r_charBuilds'] || '{}');
        """)
        self.assertTrue(out["forked"], "d2r_charBuilds is not in _LP_FORKED")
        self.assertEqual(out["main"], ["d2r_charBuilds"])
        b = out["build"]
        for k, t in (("name", str), ("cls", str), ("level", int), ("sets", list)):
            self.assertIsInstance(b.get(k), t, "build.%s: %r" % (k, b.get(k)))
        self.assertEqual((b["cls"], b["level"]), ("Warlock", 88), "the first template is konyolock, Warlock 88")
        self.assertEqual(b["sets"][0]["name"], "Set 1")
        e = b["sets"][0]["slots"]["head"]
        for k, t in (("name", str), ("base", str), ("sockets", int), ("eth", bool), ("rolls", dict), ("socketed", list)):
            self.assertIsInstance(e.get(k), t, "slot.%s: %r" % (k, e.get(k)))
        self.assertEqual((e["name"], e["base"]), ("Crown of Ages", "urn"))
        inv = b["sets"][0]["inv"]
        self.assertEqual([(i["name"], i["x"], i["y"], i["w"], i["h"]) for i in inv], [("Annihilus", 0, 0, 1, 1)])
        self.assertEqual(out["backup"], ["d2r_charBuilds"], "Backup & Share does not carry the builds")
        self.assertEqual(out["ladderSees"], 0, "the ladder world sees the main world's builds")
        self.assertEqual(out["ladder"], ["L·d2r_charBuilds", "d2r_charBuilds"],
                         "on the ladder profile the builds did not fork: %s" % out["ladder"])
        self.assertTrue(out["mainUntouched"], "a ladder build changed the main world's builds")
        self.assertEqual(out["ladderBackup"], ["d2r_charBuilds"], "the ladder export must name the key bare")
        self.assertEqual([v["cls"] for v in out["ladderBackupIsLadder"].values()], ["Sorceress"],
                         "the ladder export must carry the ladder world's builds, not main's")

    def test_esc_closes_the_top_layer_first_then_the_builder(self):
        out = _run(r"""
          window.openCharBuilder();
          window._cbOpenPick('slot', 'head');
          OUT.before = [!!window._cbState().pick, window._cbState().open];
          OUT.stop1 = key('Escape');
          OUT.after1 = [!!window._cbState().pick, window._cbState().open];
          window._cbOpenStash();
          key('Escape');
          OUT.after2 = [!!window._cbState().stash, window._cbState().open];
          OUT.stop3 = key('Escape');
          OUT.after3 = [window._cbState().open, document.documentElement.classList.contains('cb-lock')];
          OUT.role = ELS['cb-win'].getAttribute('role');
        """)
        self.assertEqual(out["before"], [True, True])
        self.assertEqual(out["after1"], [False, True], "the first Esc must close the picker and leave the builder up")
        self.assertIn("stopped", out["stop1"], "the Esc reached other listeners on the board")
        self.assertEqual(out["after2"], [False, True], "Esc must close the stash before the builder")
        self.assertEqual(out["after3"], [False, False], "the last Esc must close the builder")
        self.assertEqual(out["role"], "dialog", "the console forwards Esc only into a [role=dialog]")

    def test_it_reads_no_vault_store_and_calls_no_mule(self):
        out = _run(r"""
          READS.length = 0;
          window.openCharBuilder();
          var d = window._cbDb(), pick = function(n){ var h = null; d.it.forEach(function(x){ if (x[1] === n) h = x; }); return h[0]; };
          window._cbOpenPick('slot', 'head'); window._cbChoose(pick('Crown of Ages'));
          window._cbOpenPick('slot', 'tors'); window._cbQt('ex'); window._cbQt('r'); window._cbChoose(pick('Enigma'));
          window._cbOpenPick('inv', null, [2, 1]); window._cbChoose(pick('Annihilus'));
          window._cbMove(0, 5, 2);
          window._cbOpenStash(); window._cbStashTab('create'); window._cbStashCat(1); window._cbStashAdd(pick('Harlequin Crest'));
          window._cbStashTab('stash'); window._cbStashCat(0);
          window._cbOpenNew(); window._cbNewCls('Sorceress'); window._cbNewGo();
          window._cbTipSlot({ getBoundingClientRect: El.prototype.getBoundingClientRect }, 'head');
          window.closeCharBuilder();
          OUT.reads = READS.filter(function(k, i){ return READS.indexOf(k) === i; });
          OUT.calls = CALLS;
          OUT.moved = slots() ? null : null;
          var all = JSON.parse(RAW['d2r_charBuilds']); OUT.nBuilds = Object.keys(all).length;
          OUT.anyInv = Object.keys(all).map(function(k){ return (all[k].sets[0].inv || []).map(function(e){ return [e.name, e.x, e.y]; }); });
          OUT.stash = Object.keys(all).map(function(k){ return (all[k].stash || []).map(function(e){ return e.name; }); });
        """)
        self.assertEqual(sorted(out["reads"]), ["d2r_cbSel", "d2r_charBuilds"],
                         "the builder read a store that is not its own: %s" % out["reads"])
        self.assertEqual(out["calls"], [], "the builder called the vault / the mules: %s" % out["calls"])
        self.assertEqual(out["nBuilds"], 2)
        self.assertIn([["Annihilus", 5, 2]], out["anyInv"], "the inventory move did not stay: %s" % out["anyInv"])
        self.assertIn(["Harlequin Crest"], out["stash"])
        # and in the SOURCE: no vault store key, no mule function, anywhere in the block's code (comments stripped)
        js = _builder_js(_src())
        code = re.sub(r"/\*.{0,4000}?\*/", " ", js, flags=re.S)
        code = "\n".join(re.sub(r"(^|[^:'\"])//.*$", r"\1", l) for l in code.split("\n"))
        for bad in ("d2r_muleAssign", "d2r_muleRoster", "d2r_muleEquip", "d2r_owned", "d2r_foundLog", "d2r_vault",
                    "vaultAssign(", "openMuleCard(", "_muleLoad(", "tvVaultRegister("):
            self.assertNotIn(bad, code, "the builder's code names %s" % bad)

    def test_the_tooltip_colour_map_is_spec_8(self):
        css = _builder_css(_src())
        rules = {}
        for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", re.sub(r"/\*.{0,4000}?\*/", " ", css, flags=re.S)):
            for sel in m.group(1).split(","):
                rules.setdefault(sel.strip(), []).append(m.group(2))

        def prop(sel, name):
            for body in rules.get(sel, []):
                mm = re.search(r"(?:^|;)\s*%s\s*:\s*([^;]+)" % re.escape(name), body)
                if mm:
                    return mm.group(1).strip()
            return None
        want = {".d2tip .d2t-u": "rgb(199,179,119)", ".d2tip .d2t-r": "rgb(199,179,119)", ".d2tip .d2t-s": "rgb(0,255,0)",
                ".d2tip .d2t-c": "rgb(255,168,0)", ".d2tip .d2t-b": "rgb(255,255,255)", ".d2tip .d2t-m": "rgb(105,105,255)",
                ".d2tip .d2t-rare": "rgb(255,255,100)", ".d2tip .d2t-p": "rgb(105,105,255)",
                ".d2tip .d2t-num": "rgb(105,105,255)", ".d2tip .d2t-w": "rgb(255,255,255)",
                ".d2tip .d2t-red": "rgb(255,77,77)"}
        got = dict((s, prop(s, "color")) for s in want)
        self.assertEqual(got, want)
        self.assertEqual(prop(".d2tip", "background"), "rgba(8,8,8,.95)")
        self.assertEqual(prop(".d2tip", "padding"), "6px 9px")
        # the picker's names: the same six quality colours, as custom properties of the window
        for k, v in (("--cb-q-unique", "rgb(199,179,119)"), ("--cb-q-set", "rgb(0,255,0)"), ("--cb-q-crafted", "rgb(255,168,0)"),
                     ("--cb-q-base", "rgb(255,255,255)"), ("--cb-q-magic", "rgb(105,105,255)"), ("--cb-q-rare", "rgb(255,255,100)")):
            self.assertEqual(prop(".cb-win", k), v, "%s is not %s" % (k, v))
        out = _run(r"""
          var e = function(q, lvl, clvl, str, attrs){ return window.d2Tip({ name: 'X', base: 'Y', q: q, reqs: { lvl: lvl, str: str }, clvl: clvl, attrs: attrs, lines: [{ t: 'a property' }] }); };
          OUT.q = ['u', 's', 'c', 'b', 'm', 'rare', 'r', 'unique', 'set'].map(function(q){ return /class="(d2t-[a-z]+)"/.exec(e(q, 1, 10))[1]; });
          OUT.lvlFail = /class="d2t-red">Required Level: 82/.test(e('u', 82, 80, 174, null));
          OUT.lvlOk = /class="d2t-w">Required Level: 82/.test(e('u', 82, 88, 174, null));
          OUT.strUnknown = /class="d2t-w">Required Strength: 174/.test(e('u', 82, 88, 174, null));
          OUT.strKnownFail = /class="d2t-red">Required Strength: 174/.test(e('u', 82, 88, 174, { str: 100 }));
          OUT.prop = /class="d2t-p">a property/.test(e('u', 1, 10));
        """)
        self.assertEqual(out["q"], ["d2t-u", "d2t-s", "d2t-c", "d2t-b", "d2t-m", "d2t-rare", "d2t-r", "d2t-u", "d2t-s"])
        self.assertTrue(out["lvlFail"], "a level-80 character is not told it fails a level-82 requirement in red")
        self.assertTrue(out["lvlOk"])
        self.assertTrue(out["strUnknown"], "strength is UNKNOWN, so its requirement must never be red on a guess")
        self.assertTrue(out["strKnownFail"], "a KNOWN strength below the requirement must be red")
        self.assertTrue(out["prop"])

    def test_stats_are_the_engines_with_their_source_or_all_unknown(self):
        """STATS draws window.D2R_CHAR_ENGINE.sheet(build, {difficulty, quests}) when it is loaded — each number with
        its source, a range as a range — and when it is not, every row is UNKNOWN and no number is drawn at all."""
        out = _run(r"""
          window.openCharBuilder();
          var stats = function(){ var h = ELS['cb-win']._html; return h.slice(h.indexOf('id="cb-stats"'), h.indexOf('id="cb-modal"')); };
          var none = stats();
          OUT.noneSays = /the stats engine is not loaded/.test(none);
          OUT.noneNumbers = (none.match(/<b>[^<]*\d[^<]*<\/b>/g) || []);
          OUT.noneUnknown = (none.match(/<b>UNKNOWN<\/b>/g) || []).length;
          var seen = null;
          window.D2R_CHAR_ENGINE = { sheet: function(b, o){ seen = { cls: b.cls, level: b.level, head: b.slots && b.slots.head && b.slots.head.name, o: o };
            return { rows: [
              { key: 'res_fire', label: 'Fire Resistance', group: 'Resistances', value: { min: 20, max: 45 }, cap: 75, raw: { min: 20, max: 45 }, source: 'RANGE', why: 'rolls untouched' },
              { key: 'fhr', label: 'Faster Hit Recovery', group: 'Speed', value: { min: 30, max: 30 }, cap: null, raw: 30, source: 'EXACT', why: 'fixed' },
              { key: 'res_cold', label: 'Cold Resistance', group: 'Resistances', value: { min: 75, max: 75 }, cap: 75, raw: { min: 91, max: 91 }, source: 'EXACT', why: 'capped' },
              { key: 'str', label: 'Strength', group: 'Attributes', value: null, cap: null, raw: null, source: 'UNKNOWN', why: 'no attributes until a save is imported' } ] }; } };
          window._cbOpenPick('slot', 'head');
          var d = window._cbDb(), coa = null; d.it.forEach(function(x){ if (x[1] === 'Crown of Ages') coa = x; });
          window._cbChoose(coa[0]); window._cbClosePick();
          window._cbStatsOpt('diff', 'nightmare');
          var h = stats();
          OUT.seen = seen;
          OUT.range = /Fire Resistance<\/span><span class="cb-sv cb-sv-RANGE"[^>]*><b>20–45<\/b><i>RANGE<\/i>/.test(h);
          OUT.exact = /Faster Hit Recovery<\/span><span class="cb-sv cb-sv-EXACT"[^>]*><b>30<\/b><i>EXACT<\/i>/.test(h);
          OUT.capped = /Cold Resistance<\/span><span class="cb-sv cb-sv-EXACT"[^>]*><b>75 \(raw 91\)<\/b>/.test(h);
          OUT.unknown = /Strength<\/span><span class="cb-sv cb-sv-UNKNOWN" title="no attributes until a save is imported"><b>UNKNOWN<\/b>/.test(h);
          window.D2R_CHAR_ENGINE = { sheet: function(){ throw new Error('boom'); } };
          window._cbRender();
          OUT.threw = /the stats engine failed \(boom\)/.test(stats()) && !(stats().match(/<b>[^<]*\d[^<]*<\/b>/g) || []).length;
        """)
        self.assertTrue(out["noneSays"], "with no engine STATS does not say the engine is not loaded")
        self.assertEqual(out["noneNumbers"], [], "with no engine STATS drew a number: %s" % out["noneNumbers"])
        self.assertGreaterEqual(out["noneUnknown"], 20)
        self.assertEqual(out["seen"], {"cls": "Warlock", "level": 88, "head": "Crown of Ages",
                                       "o": {"difficulty": "nightmare", "quests": True}},
                         "the engine was not handed the build, its worn slots and the sheet's options: %s" % out["seen"])
        self.assertTrue(out["range"], "a RANGE row is not drawn as its range with its source")
        self.assertTrue(out["exact"], "an EXACT row is not drawn as its number with its source")
        self.assertTrue(out["unknown"], "an UNKNOWN row does not say UNKNOWN with its reason")
        self.assertTrue(out["capped"], "a capped row must show the raw sum the cap moved (75 (raw 91))")
        self.assertTrue(out["threw"], "an engine that throws must leave every row UNKNOWN, saying why")

    def test_crafted_is_the_games_cube_witnessed_by_the_boards_crafts(self):
        s = _src()
        crafts = _between(s, "const CRAFTS = [", "\n];")
        keys = re.findall(r"key:'([^']+)'", crafts)
        self.assertGreaterEqual(len(keys), 4, "the board's CRAFTS did not parse: %s" % keys)
        names = set(x[1] for x in _db()["it"] if x[2] == "c")
        missing = []
        for m in re.finditer(r"key:'([^']+)'.*?slots:\{(.*?)\}\s*\}", crafts, re.S):
            for q, w in re.findall(r"(?:'([^']+)'|\b([A-Z][a-z]+)\b):\{rune", m.group(2)):
                slot = q or w
                n = "%s %s" % (m.group(1), "Body" if slot == "Body Armor" else slot)
                if n not in names:
                    missing.append(n)
        self.assertEqual(missing, [], "the board names crafts the game's cube table does not hold: %s" % missing)
        self.assertEqual(len(names), 36)

    def test_the_block_speaks_the_committed_tables_words(self):
        import item_tables as IT
        t = IT.load()
        self.assertTrue(t, "tv/item_tables.json is missing")
        db = _db()
        self.assertEqual(len(db.get("sourceHash") or ""), 64, "the block carries no sourceHash")
        bad = []
        for code, b in db["b"].items():
            it = (t["items"].get(code) or {}).get("name")
            if it != b[0] and b[20]:
                # a spawnable base renamed apart from a twin (the Colossal Jewel prints "Jewel") is the one exception
                if not (it and it != b[0] and sum(1 for x in t["items"].values() if x.get("name") == it) > 1):
                    bad.append("base %s: block %r, item_tables %r" % (code, b[0], it))
        uq = dict((v.get("name"), 1) for v in t["uniques"].values())
        st = dict((v.get("name"), 1) for v in t["setItems"].values())
        rw = dict((v.get("key"), v.get("name")) for v in t["runewords"].values())
        for x in db["it"]:
            base_name = re.sub(r" \((?:[^)]*)\)$", "", x[1])
            if x[2] == "u" and base_name not in uq and x[1] not in uq:
                bad.append("unique %r is not in item_tables.json" % x[1])
            if x[2] == "s" and x[1] not in st:
                bad.append("set item %r is not in item_tables.json" % x[1])
            if x[2] == "r" and rw.get("Runeword" + x[0][1:]) != x[1]:
                bad.append("runeword %s %r vs item_tables %r" % (x[0], x[1], rw.get("Runeword" + x[0][1:])))
        self.assertEqual(bad, [], "\n  ".join(bad[:20]))
        c = db["counts"]
        self.assertGreaterEqual((c["uniques"], c["sets"], c["runewords"], c["crafted"]), (400, 140, 90, 36), c)


RED_PROOF = [
    {
        "why": "#174 v-B2 - with no stats engine STATS draws a number (a 0) where nothing was measured",
        "file": "bible.html",
        "find": "+ esc(why) + '\"><b>UNKNOWN</b></span></div>'; });\n",
        "replace": "+ esc(why) + '\"><b>0</b></span></div>'; });\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - the helm's rail loses its parent entry, so Helmets stops listing circlets and the rail is no longer theirs",
        "file": "bible.html",
        "find": "    return [[cats[0][0], -1, cats.length === 1 ? cats[0][2] : -1]].concat(kids(1));\n",
        "replace": "    return kids(0);\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - a runeword is offered on a base that cannot hold its runes (Enigma on a 2-socket Quilted Armor)",
        "file": "bible.html",
        "find": "        if (_cbMaxSock(c, 99) < n) return;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - a roll outside the item's range is accepted and saved as if it were his",
        "file": "bible.html",
        "find": "    if (v < lo || v > hi) return { ok: false, why: 'this roll is ' + lo + '–' + hi + ' on this item; ' + v + ' is outside it' };\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - a typed roll never reaches the numbers, so Defense stays a range after he typed his roll",
        "file": "bible.html",
        "find": "    if (t != null && t >= Math.min(r[0], r[1]) && t <= Math.max(r[0], r[1])) return [t, t, true];\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - the builds stop forking per account: a ladder build lands in the main world's key",
        "file": "bible.html",
        "find": "  \"d2r_charBuilds\",\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - Esc skips the picker and closes the whole builder on the first press",
        "file": "bible.html",
        "find": "    if (st.pick){ window._cbClosePick(); return 'picker'; }\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - the builder reads his vault (the items coming in mix with the tool)",
        "file": "bible.html",
        "find": "    _cbDb();\n    var all = _cbAll(), sel = buildId || null;\n",
        "replace": "    _cbDb(); try { window.LSR.getItem('d2r_muleAssign'); } catch (e) {}\n    var all = _cbAll(), sel = buildId || null;\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - the tooltip's properties are no longer the game's blue",
        "file": "bible.html",
        "find": ".d2tip .d2t-num,.d2tip .d2t-p{color:rgb(105,105,255)}",
        "replace": ".d2tip .d2t-num,.d2tip .d2t-p{color:rgb(232,232,232)}",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - an UNKNOWN strength paints the requirement red on a guess",
        "file": "bible.html",
        "find": "    var red = function(need, have){ return (have != null && need != null && have < need) ? 'd2t-red' : 'd2t-w'; };\n",
        "replace": "    var red = function(need, have){ return (need != null && !(have >= need)) ? 'd2t-red' : 'd2t-w'; };\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("⚪ SKIP — node is not on this machine, so the builder was not driven. UNMEASURED, declared (77).\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
