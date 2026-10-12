# -*- coding: utf-8 -*-
"""#146 step 4 (REG-1821) — AN ITEM HE ADDS IN THE VAULT IS HIS, THROUGH THE ONE `owned` DOOR.

His ask (2026-10-01): a Vault '+ Add an item' that uses the planner's item list, source manual, his testimony. The
first cut wrote each pick to a NEW key, d2r_vaultHand, beside the hand ledger the board already keeps: a pick never
reached `owned` — not the dock, not a mule, not the grail count — and every visitor's Vault said "Nothing added by
hand." under a list nothing else read. This law drives the SHIPPED door end to end over the SHIPPED owned door:

  · A PICK IS OWNED, WITH HIS HAND AS ITS RECEIPT. vaultHandTake -> vaultHandAdd -> the board's name resolution
    (_vaultResolveName: "Harlequin Crest" lands on the tile the readers file, "Harlequin Crest (Shako)") ->
    window._ownedAdd(source 'hand'): the name is in `owned` and in d2r_owned, d2r_vaultProv holds a kind:'owned'
    receipt whose source is 'hand' and whose time is the pick's. Nothing is filed: d2r_muleAssign is never written
    (he files it, as every manual filing goes through vaultFile). No d2r_vaultHand key is written.
  · ONLY A NAME THE VAULT DRAWS. The list offers only what ownedPool's own rule (_vaultKeeps) keeps, SAYS how many
    matching planner rows it left out, and the door refuses a crafted recipe / a white base in words — such a name
    would sit in d2r_owned and render nowhere.
  · A SECOND ADD CHANGES NOTHING: an owned name answers 'already' and writes no store.
  · THE SECOND KEY COMES HOME ONCE: every d2r_vaultHand row is added at the time he typed it, the key is removed only
    when every row landed (a row the vault cannot take keeps the key, untouched), an unreadable list is never written
    over, and the migration runs once a page.
  · THE JOINS: renderVault asks the migration before it reads the pool; ownedPool filters by _vaultKeeps; the door
    names no mule and writes no store of its own; the side list's section is gone from the page.
  · THE PLANNER SEARCH is a second door, outside that block. It opens the character-builder picker (search, quality,
    mods) and files a pick only when suggestMule names a mule on this board: a catalogue piece through vaultHandAdd,
    a magic / rare / crafted piece through magicFinds with the real base and the mod lines. Throw-out, keep-on-MAIN,
    a rune answered as the shared stash with no locker id, a name nothing knows, and a white base stay unfiled.
    War gear names the shared locker and is filed there; a missing locker is the same SHARED STASH the load migration
    adds, put back, then the pick is filed. A runeword keeps the base he chose. The old door still does not file, and the
    migration still does not file a row he typed before.

Drives the shipped ⟦OWNED PROV⟧ door, _vaultKeeps, _vaultResolveName and the ⟦VAULT HAND⟧ block in node, the program
on stdin. A missing node raises — this law does not skip. RED_PROOF below.
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
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_every_owned_door_writes_provenance as OWN  # noqa: E402  the ⟦OWNED PROV⟧ cut and the vault predicate

BIBLE = os.path.join(HERE, "..", "bible.html")
NODE = os.environ.get("NODE") or shutil.which("node")

HAND_A, HAND_B = "  /* ⟦VAULT HAND BEGIN⟧ */\n", "  /* ⟦VAULT HAND END⟧ */\n"
KEEPS_A, KEEPS_B = "  function _vaultKeeps(n){\n", "  function ownedPool(){\n"
RESOLVE_A, RESOLVE_B = "  window._vaultResolveName = function(name){\n", "  window.tvVaultRegister = function(name, witness){\n"
SHARED_A, SHARED_B = "  var SHARED_STASH_RE = ", "  try { window.isSharedStash = isSharedStash; }"
AGG = "  function isAggregate(n){ return /\\((any piece|any|set)\\)\\s*$/i.test(n); }\n"

HARNESS = r"""
var window = globalThis, STORE = {}, WRITES = [], ELS = {}, RENDERS = 0;
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(STORE, k) ? STORE[k] : null; },
               setItem: function(k, v){ WRITES.push(k); STORE[k] = String(v); },
               removeItem: function(k){ WRITES.push('-' + k); delete STORE[k]; } };
window.localStorage = { getItem: function(){ return null; }, setItem: function(){}, removeItem: function(){} };
window.D2R_BUILD = { id: 'vTEST' }; window.D2R_PROFILE = 'main';
function El(id){ this.id = id || ''; this.hidden = true; this._html = ''; this.textContent = ''; this.value = ''; this._attrs = {}; }
El.prototype.setAttribute = function(n, v){ this._attrs[n] = String(v); };
El.prototype.getAttribute = function(n){ return Object.prototype.hasOwnProperty.call(this._attrs, n) ? this._attrs[n] : null; };
Object.defineProperty(El.prototype, 'innerHTML', {
  set: function(h){ this._html = String(h); var re = /id="([^"]+)"/g, m;
    while ((m = re.exec(this._html))){ ELS[m[1]] = new El(m[1]); ELS[m[1]].hidden = false; } },
  get: function(){ return this._html; } });
var document = { getElementById: function(id){ return ELS[id] || null; }, createElement: function(){ return new El(); },
                 body: { appendChild: function(c){ if (c.id) ELS[c.id] = c; } },
                 documentElement: { classList: { contains: function(){ return false; } } } };
var owned = new Set([]);
function persistOwned(){ STORE['d2r_owned'] = JSON.stringify(Array.from(owned)); WRITES.push('d2r_owned'); }
function renderVault(){ RENDERS++; }
var ITEMS = [{ n: 'Harlequin Crest (Shako)' }, { n: 'Stone of Jordan' }, { n: "Arachnid Mesh" }];
var EXTRA_ITEMS = {};
window.findRuneword = function(n){ return n === 'Enigma' ? { n: 'Enigma' } : null; };
window.findSetPiece = function(){ return null; };
%(lanes)s
%(region)s
%(shared)s
%(agg)s
%(keeps)s
%(resolve)s
%(hand)s
var CAT = [{ id: 'u:shako', name: 'Harlequin Crest', q: 'u' }, { id: 'u:soj', name: 'Stone of Jordan', q: 'u' },
           { id: 'r:enigma', name: 'Enigma', q: 'r' }, { id: 'c88', name: 'Caster Amulet', q: 'c' },
           { id: 'b:amu', name: 'Amulet', q: 'm' }];
window._cbHandCatalog = function(q){ q = String(q || '').toLowerCase();
  return { ok: true, rows: CAT.filter(function(r){ return !q || r.name.toLowerCase().indexOf(q) >= 0; }) }; };
function prov(){ return JSON.parse(STORE['d2r_vaultProv'] || '{}'); }
var OUT = {};
%(body)s
process.stdout.write(JSON.stringify(OUT));
"""


def _src():
    with io.open(BIBLE, encoding="utf-8") as fh:
        return fh.read()


def _cut(s, a, b, keep_b=False):
    if s.count(a) != 1:
        raise AssertionError("anchor %r matched %d times" % (a[:60], s.count(a)))
    i = s.index(a)
    j = s.index(b, i + len(a))
    return s[i:j + (len(b) if keep_b else 0)]


def code_only(text):
    """`text` with its /* */ and // comments blanked — a guard grades CODE, never the prose that explains it."""
    text = re.sub(r"/\*.{0,6000}?\*/", " ", text, flags=re.S)
    return "\n".join(re.sub(r"(^|\s)//.*$", r"\1", ln) for ln in text.split("\n"))


def _node(body):
    if not NODE:
        raise AssertionError("node is not on this machine — this law does not skip")
    s = _src()
    prog = HARNESS % {"lanes": OWN._lanes(s), "region": OWN.owned_prov_region(s), "shared": _cut(s, SHARED_A, SHARED_B),
                      "agg": AGG if s.count(AGG) == 1 else "/* isAggregate MISSING */",
                      "keeps": _cut(s, KEEPS_A, KEEPS_B), "resolve": _cut(s, RESOLVE_A, RESOLVE_B),
                      "hand": _cut(s, HAND_A, HAND_B), "body": body}
    p = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise AssertionError("the hand harness would not run — UNKNOWN, not passing: " + (p.stderr or p.stdout)[-2000:])
    return json.loads(p.stdout)


class AHandAddedItemStaysHis(unittest.TestCase):

    def test_a_pick_is_owned_with_his_hand_as_its_receipt(self):
        out = _node(r"""
          OUT.open = window.vaultHandOpen();
          OUT.list = ELS['vault-hand-list']._html;
          OUT.take = window.vaultHandTake('u:shako');
          OUT.say = ELS['vault-hand-say'].textContent;
          OUT.sayState = ELS['vault-hand-say'].getAttribute('data-state');
          OUT.owned = Array.from(owned);
          OUT.stored = JSON.parse(STORE['d2r_owned'] || '[]');
          OUT.row = prov()['Harlequin Crest (Shako)'] || null;
          OUT.keys = Object.keys(STORE).sort();
          OUT.renders = RENDERS;
          OUT.after = ELS['vault-hand-list']._html;
        """)
        self.assertTrue(out["open"]["ok"])
        self.assertEqual(out["open"]["n"], 3, "the list did not offer exactly the three names the vault draws")
        self.assertEqual(out["open"]["left"], 2)
        self.assertIn('data-id="u:shako"', out["list"])
        self.assertIn('data-id="r:enigma"', out["list"])
        self.assertNotIn('data-id="c88"', out["list"], "a crafted recipe the vault cannot draw was offered")
        self.assertNotIn('data-id="b:amu"', out["list"], "a white base the vault cannot draw was offered")
        self.assertIn("2 matching planner items are not listed", out["list"])
        self.assertEqual(out["take"]["mode"], "added")
        self.assertEqual(out["take"]["name"], "Harlequin Crest (Shako)", "the pick was not filed under the register's name")
        self.assertEqual(out["owned"], ["Harlequin Crest (Shako)"])
        self.assertEqual(out["stored"], ["Harlequin Crest (Shako)"], "the add never reached d2r_owned")
        row = out["row"]
        self.assertIsNotNone(row, "no receipt in d2r_vaultProv — the pick did not go through the owned door")
        self.assertEqual(row["kind"], "owned")
        self.assertEqual(row["source"], "hand")
        self.assertEqual(row["where"], "the Vault (+ Add an item)")
        self.assertTrue(row["tsMeasured"])
        self.assertEqual(out["keys"], ["d2r_owned", "d2r_vaultProv"], "the add wrote a store beyond owned + its receipt")
        self.assertIn("is yours — it waits in Unsorted", out["say"])
        self.assertEqual(out["sayState"], "added")
        self.assertEqual(out["renders"], 1, "the vault was not repainted after the add")
        self.assertIn("already yours", out["after"])

    def test_a_name_the_vault_cannot_draw_is_refused_and_a_second_add_changes_nothing(self):
        out = _node(r"""
          OUT.craft = window.vaultHandAdd('Caster Amulet', '2026-10-05T12:00:00.000Z');
          OUT.base = window.vaultHandAdd('Amulet', '2026-10-05T12:00:00.000Z');
          OUT.blank = window.vaultHandAdd('  ', null);
          OUT.badTime = window.vaultHandAdd('Stone of Jordan', 'not a date');
          OUT.writes0 = WRITES.slice();
          OUT.first = window.vaultHandAdd('Stone of Jordan', '2026-10-05T12:00:00.000Z');
          var raw = STORE['d2r_vaultProv'], n = WRITES.length;
          OUT.second = window.vaultHandAdd('stone of jordan', '2026-10-06T12:00:00.000Z');
          OUT.same = STORE['d2r_vaultProv'] === raw;
          OUT.writes2 = WRITES.length - n;
          OUT.at = prov()['Stone of Jordan'].at;
        """)
        self.assertEqual(out["craft"]["refused"], "not-drawn")
        self.assertIn("not an item the vault draws", out["craft"]["why"])
        self.assertEqual(out["base"]["refused"], "not-drawn")
        self.assertEqual(out["blank"]["refused"], "no-name")
        self.assertEqual(out["badTime"]["refused"], "no-time")
        self.assertEqual(out["writes0"], [], "a refused add wrote a store")
        self.assertEqual(out["first"]["mode"], "added")
        self.assertEqual(out["second"]["mode"], "already")
        self.assertTrue(out["same"])
        self.assertEqual(out["writes2"], 0, "a second add of an owned name wrote a store")
        self.assertEqual(out["at"], "2026-10-05T12:00:00.000Z", "the receipt is not the time of the first add")

    def test_the_second_key_comes_home_once_and_nothing_he_typed_is_lost(self):
        out = _node(r"""
          STORE['d2r_vaultHand'] = JSON.stringify([
            { name: 'Stone of Jordan', source: 'manual', at: '2026-10-05T12:00:00.000Z', seen: null },
            { name: 'Harlequin Crest', source: 'manual', at: '2026-10-05T13:00:00.000Z', seen: { source: 'stash', at: null } }]);
          OUT.m = window._vaultHandMigrate();
          OUT.again = window._vaultHandMigrate();
          OUT.gone = !Object.prototype.hasOwnProperty.call(STORE, 'd2r_vaultHand');
          OUT.owned = Array.from(owned).sort();
          OUT.at = [prov()['Stone of Jordan'].at, prov()['Harlequin Crest (Shako)'].at];
          OUT.src = prov()['Stone of Jordan'].source;
        """)
        self.assertEqual(out["m"], {"ok": True, "n": 2, "left": 0, "rows": []})
        self.assertIsNone(out["again"], "the migration ran twice in one page")
        self.assertTrue(out["gone"], "every row landed and the second key stayed")
        self.assertEqual(out["owned"], ["Harlequin Crest (Shako)", "Stone of Jordan"])
        self.assertEqual(out["at"], ["2026-10-05T12:00:00.000Z", "2026-10-05T13:00:00.000Z"],
                         "a migrated row was not dated when he typed it")
        self.assertEqual(out["src"], "hand")

        kept = _node(r"""
          var raw = JSON.stringify([{ name: 'Stone of Jordan', source: 'manual', at: '2026-10-05T12:00:00.000Z' },
                                    { name: 'Caster Amulet', source: 'manual', at: '2026-10-05T12:01:00.000Z' }]);
          STORE['d2r_vaultHand'] = raw;
          OUT.m = window._vaultHandMigrate();
          OUT.key = STORE['d2r_vaultHand'];
          OUT.owned = Array.from(owned);
        """)
        self.assertEqual((kept["m"]["n"], kept["m"]["left"]), (1, 1))
        self.assertEqual(kept["key"], '[{"name":"Caster Amulet","source":"manual","at":"2026-10-05T12:01:00.000Z"}]',
                         "the key does not hold exactly the row left, verbatim")
        self.assertEqual(kept["owned"], ["Stone of Jordan"])

        bad = _node(r"""
          STORE['d2r_vaultHand'] = '{';
          OUT.m = window._vaultHandMigrate();
          OUT.raw = STORE['d2r_vaultHand'];
          OUT.writes = WRITES.slice();
        """)
        self.assertFalse(bad["m"]["ok"])
        self.assertEqual(bad["raw"], "{", "an unreadable list was written over")
        self.assertEqual(bad["writes"], [])

    def test_a_row_already_owned_keeps_his_hand_and_one_owned_elsewhere_stays_said(self):
        """REG-1848 — a legacy row whose name is already owned is not landed by being owned."""
        out = _node(r"""
          ELS['vault-hand-left'] = new El('vault-hand-left');
          ['Stone of Jordan', 'Arachnid Mesh', 'Enigma'].forEach(function(n){ owned.add(n); });
          STORE['d2r_vaultProv'] = JSON.stringify({
            'Stone of Jordan': { kind: 'owned', source: 'kai-register', by: 'x', ts: 5, at: '2026-09-01T00:00:00.000Z' },
            'Enigma': { mule: 'runewords', source: 'stash', at: '2026-09-02T00:00:00.000Z' } });
          var raw = JSON.stringify([{ name: 'Stone of Jordan', source: 'manual', at: '2026-10-05T12:00:00.000Z' },
                                    { name: 'Arachnid Mesh', source: 'manual', at: '2026-10-05T12:01:00.000Z' },
                                    { name: 'Enigma', source: 'manual', at: '2026-10-05T12:02:00.000Z' }]);
          STORE['d2r_vaultHand'] = raw;
          OUT.m = window._vaultHandMigrate();
          OUT.paint = window._vaultHandLeftPaint();
          OUT.left = ELS['vault-hand-left']._html; OUT.hidden = ELS['vault-hand-left'].hidden;
          OUT.key = JSON.parse(STORE['d2r_vaultHand'] || 'null');
          OUT.prov = prov();
        """)
        self.assertEqual((out["m"]["n"], out["m"]["left"]), (2, 1))
        self.assertEqual(out["key"], [{"name": "Stone of Jordan", "source": "manual", "at": "2026-10-05T12:00:00.000Z"}],
                         "the key went while a row he typed had not joined the ledger, or kept rows that landed")
        sj = out["prov"]["Stone of Jordan"]
        self.assertEqual(sj["source"], "kai-register", "another door's receipt was overwritten")
        self.assertNotIn("where", sj, "his hand was smeared into another door's receipt")
        mesh = out["prov"]["Arachnid Mesh"]
        self.assertEqual((mesh["kind"], mesh["source"], mesh["at"]), ("owned", "hand", "2026-10-05T12:01:00.000Z"),
                         "an owned name with no receipt did not take his hand as its receipt")
        en = out["prov"]["Enigma"]
        self.assertEqual(en["source"], "stash")
        self.assertEqual((en["ownedBy"]["source"], en["ownedBy"]["at"]), ("hand", "2026-10-05T12:02:00.000Z"),
                         "a filing with no ownedBy did not take his hand")
        self.assertFalse(out["hidden"], "a row left behind is not said on the Vault")
        self.assertIn("1 item you added by hand before this version could not join the vault", out["left"])
        self.assertIn('data-name="Stone of Jordan"', out["left"])
        self.assertIn("already yours through the live reader (KAI register)", out["left"])
        quiet = _node(r"""
          ELS['vault-hand-left'] = new El('vault-hand-left'); ELS['vault-hand-left'].hidden = false;
          window._vaultHandMigrate(); window._vaultHandLeftPaint();
          OUT.hidden = ELS['vault-hand-left'].hidden; OUT.html = ELS['vault-hand-left']._html;
        """)
        self.assertTrue(quiet["hidden"], "a board with no old key shows the left-behind line")
        self.assertEqual(quiet["html"], "")

    def test_the_next_page_load_counts_the_same(self):
        """REG-1866 — two passes over two page loads: a row that joined stays landed, the banner count is stable, and a
        landed row leaves the key."""
        first = _node(r"""
          ELS['vault-hand-left'] = new El('vault-hand-left');
          ['Stone of Jordan', 'Enigma'].forEach(function(n){ owned.add(n); }); persistOwned();
          STORE['d2r_vaultProv'] = JSON.stringify({
            'Stone of Jordan': { kind: 'owned', source: 'kai-register', by: 'x', ts: 5, at: '2026-09-01T00:00:00.000Z' },
            'Enigma': { mule: 'runewords', source: 'stash', at: '2026-09-02T00:00:00.000Z' } });
          STORE['d2r_vaultHand'] = JSON.stringify([{ name: 'Stone of Jordan', source: 'manual', at: '2026-10-05T12:00:00.000Z' },
                                                   { name: 'Enigma', source: 'manual', at: '2026-10-05T12:02:00.000Z' }]);
          OUT.m = window._vaultHandMigrate(); window._vaultHandLeftPaint();
          OUT.banner = (ELS['vault-hand-left']._html.match(/<p class="vault-org-h">([^<]*)/) || [])[1] || null;
          OUT.STORE = STORE;
        """)
        second = _node(r"""
          ELS['vault-hand-left'] = new El('vault-hand-left');
          var S = %s; Object.keys(S).forEach(function(k){ STORE[k] = S[k]; });
          JSON.parse(STORE['d2r_owned']).forEach(function(n){ owned.add(n); });
          var keyBefore = STORE['d2r_vaultHand'], provBefore = STORE['d2r_vaultProv'];
          OUT.m = window._vaultHandMigrate(); window._vaultHandLeftPaint();
          OUT.banner = (ELS['vault-hand-left']._html.match(/<p class="vault-org-h">([^<]*)/) || [])[1] || null;
          OUT.keySame = STORE['d2r_vaultHand'] === keyBefore; OUT.provSame = STORE['d2r_vaultProv'] === provBefore;
          OUT.key = JSON.parse(STORE['d2r_vaultHand'] || 'null');
        """ % json.dumps(first["STORE"]))
        self.assertEqual((first["m"]["n"], first["m"]["left"]), (1, 1))
        self.assertEqual([r["name"] for r in json.loads(first["STORE"]["d2r_vaultHand"])], ["Stone of Jordan"],
                         "a row that landed stayed in the key")
        self.assertEqual(second["m"]["left"], 1, "the next page counted a landed row as left")
        self.assertEqual(second["banner"], first["banner"], "the left-behind banner grew on the next page load")
        self.assertIn("1 item you added by hand", second["banner"])
        self.assertTrue(second["keySame"] and second["provSame"], "a pass that landed nothing wrote a store")
        self.assertEqual([r["name"] for r in second["key"]], ["Stone of Jordan"])

        # and a row the pass joined, still in the key (a page that stopped between the join and the key write), is landed
        joined = _node(r"""
          ['Enigma'].forEach(function(n){ owned.add(n); });
          STORE['d2r_vaultProv'] = JSON.stringify({ 'Enigma': { mule: 'runewords', source: 'stash', at: '2026-09-02T00:00:00.000Z',
            ownedBy: { kind: 'owned', source: 'hand', at: '2026-10-05T12:02:00.000Z' } } });
          STORE['d2r_vaultHand'] = JSON.stringify([{ name: 'Enigma', source: 'manual', at: '2026-10-05T12:02:00.000Z' }]);
          OUT.m = window._vaultHandMigrate();
          OUT.gone = !Object.prototype.hasOwnProperty.call(STORE, 'd2r_vaultHand');
        """)
        self.assertEqual((joined["m"]["n"], joined["m"]["left"]), (1, 0), "a filing that carries his hand was counted left")
        self.assertTrue(joined["gone"])

    def test_a_pass_that_did_not_finish_is_asked_again(self):
        """REG-1849 — the latch closes on a finished pass, not on an attempt."""
        out = _node(r"""
          var real = window.LSR.getItem, n = 0;
          window.LSR.getItem = function(k){ if (k === 'd2r_vaultHand' && n++ === 0) throw new Error('transient'); return real(k); };
          STORE['d2r_vaultHand'] = JSON.stringify([{ name: 'Stone of Jordan', source: 'manual', at: '2026-10-05T12:00:00.000Z' }]);
          OUT.first = window._vaultHandMigrate();
          OUT.second = window._vaultHandMigrate();
          OUT.third = window._vaultHandMigrate();
          OUT.owned = Array.from(owned);
        """)
        self.assertFalse(out["first"]["ok"])
        self.assertIn("asked again on the next paint", out["first"]["why"])
        self.assertEqual((out["second"]["n"], out["second"]["left"]), (1, 0), "a failed read stopped the next paint from trying")
        self.assertIsNone(out["third"], "a finished pass ran again")
        self.assertEqual(out["owned"], ["Stone of Jordan"])

    def test_the_door_says_what_its_door_said(self):
        """REG-1847 — the owned door's answer, and a check that could not be asked, decide what is said."""
        out = _node(r"""
          STORE['d2r_vaultProv'] = '{';
          OUT.noReceipt = window.vaultHandAdd('Stone of Jordan', '2026-10-05T12:00:00.000Z');
          OUT.provRaw = STORE['d2r_vaultProv'];
        """)
        r = out["noReceipt"]
        self.assertEqual((r["mode"], r["receipt"]), ("added", False))
        self.assertIn("its receipt was not written: d2r_vaultProv would not parse", r["why"])
        self.assertEqual(out["provRaw"], "{")
        gone = _node(r"""
          window._ownedAdd = undefined;
          OUT.r = window.vaultHandAdd('Stone of Jordan', '2026-10-05T12:00:00.000Z');
          OUT.owned = Array.from(owned); OUT.keys = Object.keys(STORE);
        """)
        self.assertEqual(gone["r"]["refused"], "no-door")
        self.assertEqual((gone["owned"], gone["keys"]), ([], []))
        amb = _node(r"""
          window._vaultNameAmbiguity = function(){ throw new Error('the known list would not read'); };
          OUT.r = window.vaultHandAdd('Stone of Jordan', '2026-10-05T12:00:00.000Z');
          OUT.owned = Array.from(owned);
        """)
        self.assertEqual(amb["r"]["refused"], "unknown", "a check that raised was read as a yes")
        self.assertIn("could not be asked", amb["r"]["why"])
        self.assertEqual(amb["owned"], [])

    def test_an_unsettled_name_is_its_own_count(self):
        """REG-1850 — a planner row whose item could not be settled is not "a name the vault does not draw"."""
        out = _node(r"""
          window._vaultNameAmbiguity = function(x){ return x === 'Crescent Moon'
            ? { name: x, among: ['Crescent Moon', 'Crescent Moon (amulet)'], why: '"Crescent Moon" names 2 known items' } : null; };
          CAT.push({ id: 'u:cm', name: 'Crescent Moon', q: '' });
          OUT.open = window.vaultHandOpen();
          OUT.list = ELS['vault-hand-list']._html;
        """)
        self.assertEqual((out["open"]["left"], out["open"]["unsettled"]), (2, 1))
        self.assertIn("2 matching planner items are not listed — the vault does not draw them", out["list"])
        self.assertIn("1 matching planner item is not listed — which vault item it names could not be settled", out["list"])

    def test_the_joins(self):
        s = _src()
        code = code_only(s)
        rv = _cut(code, "  function renderVault(){\n", "    renderMultiKeep();\n")
        self.assertEqual(rv.count("window._vaultHandMigrate();"), 1, "renderVault does not bring the second key home")
        self.assertEqual(rv.count("window._vaultHandLeftPaint();"), 1, "renderVault never says what the pass left")
        self.assertEqual(s.count('id="vault-hand-left"'), 1)
        self.assertLess(rv.index("window._vaultHandMigrate();"), rv.index("var poolAll=ownedPool();"),
                        "the migration runs after the pool was read")
        self.assertIn("return Array.from(owned).filter(_vaultKeeps).sort();", _cut(code, KEEPS_B, "  function art(n, glyph, size){"))
        hand = code_only(_cut(s, HAND_A, HAND_B))
        self.assertEqual(hand.count("try { add = window._ownedAdd(nm, { source: 'hand',"), 1, "the door does not use the owned door")
        for banned in ("vaultFile(", "assign[", "suggestMule("):
            self.assertNotIn(banned, hand, "the hand door reaches %s" % banned)
        self.assertEqual(hand.count("setItem("), 1, "the hand door writes a store of its own")
        self.assertEqual(hand.count("window.LSR.setItem(VAULT_HAND_LEGACY, JSON.stringify(kept.map(function(k){ return k.row; })));"), 1,
                         "the hand door's one write is not the legacy key keeping only what is left")
        self.assertEqual(code.count("window.LSR.removeItem(VAULT_HAND_LEGACY)"), 1)
        self.assertNotIn('id="vault-hand"', s, "the side list's section is still on the page")
        self.assertNotIn("vaultHandPaint", code)
        self.assertEqual(s.count('onclick="window.vaultHandOpen()"'), 1)
        self.assertIn('id="tab-vault"', s[:s.find('onclick="window.vaultHandOpen()"')])
        self.assertIn('"d2r_vaultHand"', s[s.find("window._LP_FORKED"):s.find("window._WP_FORKED")],
                      "the legacy key left the fork set — a ladder migration would read Main's rows")

    def test_the_door_asks_the_planner_list_with_the_class_filter_off(self):
        s = _src()
        self.assertEqual(s.count("else rows = _cbForSlot(slot, p.rail, p.host === 'hand');"), 1)
        catalog = _cut(s, "  /* ⟦VAULT HAND CATALOG BEGIN⟧ */\n", "  /* ⟦VAULT HAND CATALOG END⟧ */")
        prog = ("var window = globalThis, ASKED = null, CB_MINV = 'minv';\n"
                "function _cbRowsFor(p){ ASKED = p; return [['u:shako', 'Harlequin Crest', 'u']]; }\n" + catalog
                + "\nvar OUT = window._cbHandCatalog('crest'); OUT.asked = ASKED; process.stdout.write(JSON.stringify(OUT));\n")
        if not NODE:
            raise AssertionError("node is not on this machine — this law does not skip")
        p = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr[-1500:])
        cat = json.loads(p.stdout)
        self.assertTrue(cat["ok"])
        self.assertEqual(cat["rows"], [{"id": "u:shako", "name": "Harlequin Crest", "q": "u"}])
        self.assertEqual(cat["asked"]["host"], "hand")
        self.assertEqual(cat["asked"]["slot"], "minv")

    def test_the_planner_search_opens_the_picker_and_the_hand_door_still_does_not_file(self):
        """The vault search is the character-builder picker. The old + Add an item door still files nothing."""
        s = _src()
        self.assertEqual(s.count('id="vault-planner-q"'), 1)
        self.assertEqual(s.count('onclick="window.vaultHandOpen()"'), 1)
        add_at = s.find('id="vault-planner-q"')
        find_at = s.find('id="vault-find-input"')
        self.assertGreater(add_at, 0)
        self.assertIn('id="tab-vault"', s[:add_at])
        self.assertLess(add_at, find_at, "the add search was put after the finder, or the finder is gone")
        self.assertIn("window.vaultPlannerOpen(this.value)", s)
        self.assertIn("window.vaultFind&&window.vaultFind(this.value)", s)
        opened = _cut(s, "  /* ⟦VAULT PLANNER OPEN BEGIN⟧ */\n", "  /* ⟦VAULT PLANNER OPEN END⟧ */\n")
        filed = _cut(s, "  /* ⟦VAULT PLANNER FILE BEGIN⟧ */\n", "  /* ⟦VAULT PLANNER FILE END⟧ */\n")
        self.assertEqual(opened.count("window._cbHostOpen("), 1)
        self.assertIn("kind: 'inv'", opened)
        self.assertIn("planner: true", opened)
        self.assertIn("fits: function(){ return true; }", opened)
        self.assertIn("window.vaultPlannerFile(entry, token)", opened)
        self.assertLess(s.find("  /* ⟦VAULT HAND END⟧ */\n"), s.find("  /* ⟦VAULT PLANNER FILE BEGIN⟧ */\n"))
        where = "the Vault planner — your search filed it where a reel of it would go"
        self.assertEqual(s.count(where), 1, "the reel-route witness is missing or was copied into a second door")
        hand = _cut(s, HAND_A, HAND_B)
        self.assertNotIn(where, hand)
        self.assertNotIn("vaultFile(", code_only(hand))
        self.assertNotIn("vaultPlannerFile", hand)
        if not NODE:
            raise AssertionError("node is not on this machine — this law does not skip")
        prog = "new Function(%s); new Function(%s);" % (json.dumps(opened), json.dumps(filed))
        p = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr[-1500:])

    def test_a_planner_pick_files_where_a_reel_of_it_would_go(self):
        """A manual pick takes the reel road. A mule answer files it. Every other answer is said and left alone."""
        if not NODE:
            raise AssertionError("node is not on this machine — this law does not skip")
        s = _src()
        block = _cut(s, "  /* ⟦VAULT PLANNER FILE BEGIN⟧ */\n", "  /* ⟦VAULT PLANNER FILE END⟧ */\n")
        prog = r"""
var window = globalThis, CALLS = [], SAID = [], magicFinds = {}, assign = {}, owned = new Set(), copies = {};
function copyCount(n){ var c = copies && copies[n]; return (c && c > 0) ? c : (owned.has(n) ? 1 : 0); }
function status(m){ SAID.push(String(m)); }
function renderVault(){ CALLS.push('render'); }
function persistOwned(){ CALLS.push('persist'); }
function saveA(){ CALLS.push('save'); }
var SHARED_ON = false;
function muleById(id){
  var names = { 'uni-armor': 'UNI-ARMOR', 'magic-rare': 'MAGIC & RARE' };
  if (id === 'shared' && SHARED_ON) return { id: id, name: 'SHARED STASH' };
  return names[id] ? { id: id, name: names[id] } : null;
}
function isSharedStash(nm){ return nm === 'El Rune'; }
function _vaultKeeps(nm){ return nm === 'Monarch'; }
function suggestMule(nm){
  var rec = magicFinds[nm];
  CALLS.push('route:' + nm + ':' + ((rec && rec.q) || '') + ':' + ((rec && rec.base) || '') + ':' + ((rec && rec.mods) ? rec.mods.join('|') : ''));
  return Object.prototype.hasOwnProperty.call(ROUTES, nm) ? ROUTES[nm] : { id: null, unsorted: true, why: 'nothing on the board recognises this name' };
}
var MADESTORE = {};
var LS = {
  getItem: function(k){ return Object.prototype.hasOwnProperty.call(MADESTORE, k) ? MADESTORE[k] : null; },
  setItem: function(k, v){ CALLS.push('ls:' + k); MADESTORE[k] = String(v); }
};
var ROUTES = {};
window.vaultHandAdd = function(nm, at, opts){
  CALLS.push('own:' + nm + ':' + ((opts && opts.kind) || ''));
  if (!owned.has(nm)) owned.add(nm);
  return { ok: true, mode: 'added', name: nm };
};
window.vaultFile = function(nm, wit, opts){
  CALLS.push('file:' + nm + ':' + opts.mule + ':' + wit.where);
  assign[nm] = opts.mule;
  if (!owned.has(nm)) owned.add(nm);
  return { ok: true, mode: 'filed', mule: opts.mule };
};
window.vaultUnassign = function(nm){ CALLS.push('unfile:' + nm); delete assign[nm]; return { ok: true }; };
window._cbItem = function(id){ return { id: id }; };
window._cbShown = function(e, it){
  return { name: e._name, q: e._q, base: e._base || '' };
};
window._cbDb = function(){ return { b: { cm: ['Grand Charm'], mon: ['Monarch'], '7cr': ['Phase Blade'] } }; };
window._cbAf = function(id){ return id === 'vita' ? { _text: '+36 to Life' } : null; };
window._cbAfText = function(a){ return a._text || ''; };
""" + block + r"""
function files(nm){ return CALLS.filter(function(c){ return c.indexOf('file:' + nm + ':') === 0; }); }
var WHERE = 'the Vault planner — your search filed it where a reel of it would go';
ROUTES['Harlequin Crest'] = { id: 'uni-armor', why: 'armor slot' };
var u1 = window.vaultPlannerFile({ id: 'shako', _name: 'Harlequin Crest', _q: 'u' }, 't-u');
var u2 = window.vaultPlannerFile({ id: 'shako', _name: 'Harlequin Crest', _q: 'u' }, 't-u');
var crestSame = copies['Harlequin Crest'] || 0;
var crestAgain = window.vaultPlannerFile({ id: 'shako', _name: 'Harlequin Crest', _q: 'u' }, 't-u2');
ROUTES['Shimmering Grand Charm of Vita'] = { id: 'magic-rare', why: 'registered in Magic and Rare' };
var m1 = window.vaultPlannerFile({ id: 'charm', base: 'cm', _name: 'Shimmering Grand Charm of Vita', _q: 'm', affixes: [{ id: 'vita' }] }, 't-m');
var m2 = window.vaultPlannerFile({ id: 'charm', base: 'cm', _name: 'Shimmering Grand Charm of Vita', _q: 'm', affixes: [{ id: 'vita' }] }, 't-m');
ROUTES['Junk Charm'] = { id: '__throwout', why: 'the planner would vendor it' };
var toss = window.vaultPlannerFile({ id: 'junk', base: 'cm', _name: 'Junk Charm', _q: 'm' }, 't-toss');
ROUTES['Keep Helm'] = { id: '__keep', why: 'your MAIN wears it' };
var keep = window.vaultPlannerFile({ id: 'keep', _name: 'Keep Helm', _q: 'u' }, 't-keep');
ROUTES['El Rune'] = null;
var shared = window.vaultPlannerFile({ id: 'el', _name: 'El Rune', _q: 'u' }, 't-el');
ROUTES['Bone Visor'] = { id: null, unsorted: true, why: 'nothing on the board recognises this name' };
var loose = window.vaultPlannerFile({ id: 'bone', _name: 'Bone Visor', _q: 'u' }, 't-bone');
var white = window.vaultPlannerFile({ id: 'amu', _name: 'Amulet', _q: 'b' }, 't-white');
ROUTES['Monarch'] = { id: 'uni-armor', why: 'armor slot' };
var base = window.vaultPlannerFile({ id: 'mon', base: 'mon', _name: 'Monarch', _q: 'b' }, 't-mon');
ROUTES['Alpha Charm'] = { id: 'magic-rare', why: 'registered in Magic and Rare' };
ROUTES['Beta Charm'] = { id: 'magic-rare', why: 'registered in Magic and Rare' };
window.vaultPlannerFile({ id: 'cm', base: 'cm', _name: 'Alpha Charm', _q: 'm' }, 'same');
var moved = window.vaultPlannerFile({ id: 'cm', base: 'cm', _name: 'Beta Charm', _q: 'm' }, 'same');
var snap = { alpha: magicFinds['Alpha Charm'] || null, alphaHome: assign['Alpha Charm'] || null,
             beta: magicFinds['Beta Charm'] || null, betaHome: assign['Beta Charm'] || null };
ROUTES['Gamma Charm'] = { id: 'magic-rare', why: 'registered in Magic and Rare' };
ROUTES['Delta Charm'] = { id: 'magic-rare', why: 'registered in Magic and Rare' };
window.vaultPlannerFile({ id: 'g', base: 'cm', _name: 'Gamma Charm', _q: 'm' }, 'both');
window.vaultPlannerFile({ id: 'd', base: 'cm', _name: 'Delta Charm', _q: 'm' }, 'both');
ROUTES['Epsilon Charm'] = { id: 'magic-rare', why: 'registered in Magic and Rare' };
ROUTES['Epsilon Two'] = { id: 'magic-rare', why: 'registered in Magic and Rare' };
window.vaultPlannerFile({ id: 'eps', base: 'cm', _name: 'Epsilon Charm', _q: 'm' }, 'tok-a');
window.vaultPlannerFile({ id: 'eps', base: 'cm', _name: 'Epsilon Two', _q: 'm' }, 'tok-b');
assign['Stone of Jordan'] = 'uni-small';
owned.add('Stone of Jordan');
ROUTES['Stone of Jordan'] = { id: 'uni-armor', why: 'armor slot' };
var already = window.vaultPlannerFile({ id: 'soj', _name: 'Stone of Jordan', _q: 'u' }, 't-soj');
var sojSame = copies['Stone of Jordan'] || 0;
var sojTwo = window.vaultPlannerFile({ id: 'soj', _name: 'Stone of Jordan', _q: 'u' }, 't-soj2');
ROUTES['Clear Charm'] = { id: 'magic-rare', why: 'registered in Magic and Rare' };
window.vaultPlannerFile({ id: 'clr', base: 'cm', _name: 'Clear Charm', _q: 'm' }, 'clr');
var cleared = window.vaultPlannerFile(null, 'clr');
ROUTES['Grief'] = { id: 'shared', why: 'war gear: flat damage war weapon - in the shared stash, where every character can reach it' };
var griefNo = window.vaultPlannerFile({ id: 'grief', base: '7cr', _name: 'Grief', _q: 'r', affixes: [{ id: 'ias', rolls: { a: 31 } }], rolls: { ias: 31 } }, 't-g1');
var griefRec = window._vpMadeOf('Grief');
var griefBase = window._vpMadeBase('Grief');
var clearedG = window.vaultPlannerFile(null, 't-g1');
var griefGone = window._vpMadeOf('Grief');
window._vaultEnsureSharedLocker = function(){ CALLS.push('ensure-shared'); SHARED_ON = true; return { id: 'shared', name: 'SHARED STASH' }; };
var griefYes = window.vaultPlannerFile({ id: 'grief', base: '7cr', _name: 'Grief', _q: 'r', affixes: [{ id: 'ias', rolls: { a: 31 } }], rolls: { ias: 31 } }, 't-g2');
ROUTES['Grief Bare'] = { id: 'shared', why: 'war gear: flat damage war weapon - in the shared stash, where every character can reach it' };
var griefBare = window.vaultPlannerFile({ id: 'griefb', _name: 'Grief Bare', _q: 'r' }, 't-gb');
var griefTwo = window.vaultPlannerFile({ id: 'grief', base: '7cr', _name: 'Grief', _q: 'r', affixes: [{ id: 'ias', rolls: { a: 31 } }], rolls: { ias: 31 } }, 't-g3');
var griefSame = window.vaultPlannerFile({ id: 'grief', base: '7cr', _name: 'Grief', _q: 'r', affixes: [{ id: 'ias', rolls: { a: 31 } }], rolls: { ias: 31 } }, 't-g3');
var griefCopies = copies['Grief'] || 0;
ROUTES['Swap Helm'] = { id: 'uni-armor', why: 'armor slot' };
var swapped = window.vaultPlannerFile({ id: 'swap', _name: 'Swap Helm', _q: 'u' }, 't-g3');
var griefAfterSwap = copies['Grief'] || 0;
var griefStill = assign['Grief'] || null;
var griefOwned = owned.has('Grief');
var griefThree = window.vaultPlannerFile({ id: 'grief', base: '7cr', _name: 'Grief', _q: 'r', affixes: [{ id: 'ias', rolls: { a: 31 } }], rolls: { ias: 31 } }, 't-g4');
var OUT = {
  u1: u1, u2: u2, uFiles: files('Harlequin Crest'), ownedU: owned.has('Harlequin Crest'),
  m1: m1, m2: m2, mf: magicFinds['Shimmering Grand Charm of Vita'] || null, mFiles: files('Shimmering Grand Charm of Vita'),
  routeM: CALLS.filter(function(c){ return c.indexOf('route:Shimmering Grand Charm of Vita:') === 0; })[0] || '',
  toss: toss, tossMf: magicFinds['Junk Charm'] || null, tossFiles: files('Junk Charm'),
  keep: keep, keepFiles: files('Keep Helm'),
  shared: shared, sharedFiles: files('El Rune'),
  loose: loose, looseFiles: files('Bone Visor'),
  white: white, whiteOwn: CALLS.filter(function(c){ return c.indexOf('own:Amulet:') === 0; }), whiteFiles: files('Amulet'),
  base: base, baseOwn: CALLS.filter(function(c){ return c === 'own:Monarch:'; }), baseFiles: files('Monarch'),
  moved: moved, alpha: snap.alpha, alphaHome: snap.alphaHome, beta: snap.beta, betaHome: snap.betaHome,
  gamma: magicFinds['Gamma Charm'] || null, delta: magicFinds['Delta Charm'] || null,
  epsilon: magicFinds['Epsilon Charm'] || null, epsilonTwo: magicFinds['Epsilon Two'] || null,
  already: already, sojFiles: files('Stone of Jordan'), sojHome: assign['Stone of Jordan'] || null,
  cleared: cleared, clearMf: magicFinds['Clear Charm'] || null, clearHome: assign['Clear Charm'] || null,
  griefNo: griefNo, griefRec: griefRec, griefBase: griefBase, griefMf: magicFinds['Grief'] || null,
  clearedG: clearedG, griefGone: griefGone, griefYes: griefYes, griefFiles: files('Grief'),
  griefBare: griefBare, bareRec: window._vpMadeOf('Grief Bare'), bareBase: window._vpMadeBase('Grief Bare'),
  ensured: CALLS.filter(function(c){ return c === 'ensure-shared'; }),
  crestSame: crestSame, crestAgain: crestAgain, crestCopies: copies['Harlequin Crest'] || 0,
  sojSame: sojSame, sojTwo: sojTwo, sojCopies: copies['Stone of Jordan'] || 0,
  griefTwo: griefTwo, griefSame: griefSame, griefCopies: griefCopies,
  swapped: swapped, griefAfterSwap: griefAfterSwap, griefStill: griefStill, griefOwned: griefOwned,
  griefThree: griefThree, griefEnd: copies['Grief'] || 0,
  where: WHERE
};
process.stdout.write(JSON.stringify(OUT));
"""
        p = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, (p.stderr or p.stdout)[-2000:])
        o = json.loads(p.stdout)
        self.assertTrue(o["u1"]["filed"], o["u1"])
        self.assertEqual(o["u1"]["mule"], "uni-armor")
        self.assertIn(o["where"], o["uFiles"][0])
        self.assertEqual(o["u2"]["mode"], "already")
        self.assertEqual(len(o["uFiles"]), 1, "a second look at the same pick rewrote the filing")
        self.assertTrue(o["ownedU"])
        self.assertEqual(o["mf"]["q"], "magic")
        self.assertEqual(o["mf"]["base"], "Grand Charm", "the magic record stored the shown name instead of the base")
        self.assertEqual(o["mf"]["mods"], ["+36 to Life"])
        self.assertIn(":magic:Grand Charm:+36 to Life", o["routeM"])
        self.assertLess(o["routeM"].find("route:"), 1)
        self.assertTrue(o["m1"]["filed"], o["m1"])
        self.assertEqual(o["m2"]["mode"], "already")
        self.assertEqual(len(o["mFiles"]), 1)
        self.assertIn("throw-out", o["toss"]["why"])
        self.assertFalse(o["toss"]["filed"])
        self.assertIsNone(o["tossMf"], "a throw-out pick was left in Magic and Rare")
        self.assertEqual(o["tossFiles"], [])
        self.assertIn("MAIN", o["keep"]["why"])
        self.assertEqual(o["keepFiles"], [])
        self.assertIn("shared stash", o["shared"]["why"])
        self.assertEqual(o["sharedFiles"], [])
        self.assertIn("nothing on the board recognises this name", o["loose"]["why"])
        self.assertEqual(o["looseFiles"], [])
        self.assertIn("white, superior or low base", o["white"]["why"])
        self.assertEqual(o["whiteOwn"], [])
        self.assertEqual(o["whiteFiles"], [])
        self.assertEqual(o["baseOwn"], ["own:Monarch:"])
        self.assertTrue(o["base"]["filed"], o["base"])
        self.assertIsNone(o["alpha"], "the old composed name was left beside the new one")
        self.assertIsNone(o["alphaHome"])
        self.assertEqual(o["beta"]["q"], "magic")
        self.assertEqual(o["betaHome"], "magic-rare")
        self.assertTrue(o["moved"]["filed"], o["moved"])
        self.assertIsNotNone(o["gamma"], "a second pick in the same search was removed")
        self.assertIsNotNone(o["delta"])
        self.assertEqual(o["epsilon"]["q"], "magic", "a later search removed a pick from an earlier one")
        self.assertEqual(o["epsilonTwo"]["q"], "magic")
        self.assertEqual(o["already"]["mode"], "already")
        self.assertEqual(o["sojFiles"], [])
        self.assertEqual(o["sojHome"], "uni-small")
        self.assertEqual(o["cleared"]["mode"], "cleared")
        self.assertIsNone(o["clearMf"])
        self.assertIsNone(o["clearHome"])
        self.assertFalse(o["griefNo"]["filed"], o["griefNo"])
        self.assertIn("no mule on this board has id shared", o["griefNo"]["why"])
        self.assertEqual(o["griefRec"]["base"], "7cr")
        self.assertEqual(o["griefRec"]["baseName"], "Phase Blade")
        self.assertEqual(o["griefRec"]["q"], "r")
        self.assertEqual(o["griefRec"]["affixes"][0]["rolls"]["a"], 31)
        self.assertEqual(o["griefBase"], "Phase Blade")
        self.assertIsNone(o["griefMf"], "a runeword was stored as a magic find")
        self.assertEqual(o["clearedG"]["mode"], "cleared")
        self.assertIsNone(o["griefGone"], "clearing the pick left the Phase Blade record behind")
        self.assertTrue(o["griefYes"]["filed"], o["griefYes"])
        self.assertEqual(o["griefYes"]["mule"], "shared")
        self.assertIn("SHARED STASH", o["griefYes"]["why"])
        self.assertEqual(o["ensured"], ["ensure-shared"])
        self.assertEqual(len(o["griefFiles"]), 1)
        self.assertIn(o["where"], o["griefFiles"][0])
        self.assertTrue(o["griefBare"]["filed"], o["griefBare"])
        self.assertIsNone(o["bareRec"], "a runeword with no chosen base was given one")
        self.assertEqual(o["bareBase"], "")
        self.assertEqual(o["crestSame"], 0, "a second look at the same open counted a new copy")
        self.assertEqual(o["crestAgain"]["mode"], "copy", o["crestAgain"])
        self.assertEqual(o["crestCopies"], 2, o["crestAgain"])
        self.assertEqual(len(o["uFiles"]), 1, "a second copy rewrote the filing")
        self.assertEqual(o["sojSame"], 0, "opening a pick that was already filed counted a new copy")
        self.assertEqual(o["sojTwo"]["mode"], "copy", o["sojTwo"])
        self.assertEqual(o["sojCopies"], 2)
        self.assertEqual(o["sojFiles"], [])
        self.assertEqual(o["sojHome"], "uni-small")
        self.assertEqual(o["griefTwo"]["mode"], "copy", o["griefTwo"])
        self.assertTrue(o["griefTwo"]["filed"], o["griefTwo"])
        self.assertEqual(o["griefTwo"]["mule"], "shared")
        self.assertIn("copy 2", o["griefTwo"]["why"])
        self.assertIn("filed to", o["griefTwo"]["why"], "the Saved plate lights only when the sentence says filed to")
        self.assertEqual(o["griefSame"]["mode"], "already", "saving the same open again counted a third copy")
        self.assertEqual(o["griefCopies"], 2)
        self.assertEqual(len(o["griefFiles"]), 1, "the second Grief rewrote the filing")
        self.assertEqual(o["griefAfterSwap"], 0, "leaving that open left the extra Grief behind")
        self.assertEqual(o["griefStill"], "shared", "leaving that open unfiled the first Grief")
        self.assertTrue(o["griefOwned"])
        self.assertTrue(o["swapped"]["filed"], o["swapped"])
        self.assertEqual(o["swapped"]["mule"], "uni-armor")
        self.assertEqual(o["griefThree"]["mode"], "copy", o["griefThree"])
        self.assertEqual(o["griefEnd"], 2)

    def test_a_vault_item_click_keeps_the_floating_card(self):
        """A locker cell, a shared-stash tile, and the other vault item chips stay on the vault.
        The floating card is the click. The runeword page is not."""
        s = _src()
        a = s.find("function renderMultiKeep(){")
        b = s.find("\nfunction renderJournal(){")
        self.assertGreater(a, 0)
        self.assertGreater(b, a)
        self.assertNotIn("window.openDrop", s[a:b], "a vault item click still leaves the vault")
        journal = s[b:s.find("\n  function persistOwned(){", b)]
        self.assertNotIn("window.openDrop", journal, "a journal chip still leaves the vault")
        self.assertNotIn(
            "onclick=\"window.openDrop&&window.openDrop('\"+jsArg(p.n)+\"')\"",
            s, "the shared-stash tile still opens the item page")
        dismiss = s.find("a click can re-render")
        self.assertGreater(dismiss, 0)
        prose = s.find("THE PROSE LANE, PURELY ADDITIVE", dismiss)
        self.assertGreater(prose, dismiss, "the click guard has no end anchor")
        keep = s[dismiss:prose]
        self.assertIn(".vd-item, .vm-cell, .vrg-row, .vmk-name, .to-name, .vj-chip", keep)
        self.assertIn("!t.closest('button, a, input, textarea, select')", keep)
        self.assertIn("!chip.classList.contains('vd-db')", keep)
        self.assertNotIn("the item's card opens as always", s)

    def test_the_planner_card_and_the_sort_click_meet_the_stored_base(self):
        """The hover prefers the stored Phase Blade, and his Auto-Sort click can file that pick.
        The picture gate stays the one line it was, so a found-ever receipt with no picture still stops."""
        s = _src()
        self.assertEqual(s.count("      if (!_hasPicture(row)){ out.noPicture.push(name); return; }\n"), 1)
        pic = s.find("      if (!_hasPicture(row)){ out.noPicture.push(name); return; }\n")
        hand = s.find("  function _plannerHandRow(name, row){")
        self.assertGreater(hand, 0)
        self.assertLess(hand, pic, "the planner-hand branch was placed after the picture gate")
        self.assertEqual(s.count("    var filed = window.vaultFile(nm, { by: 'hand', at: at, where: VP_WHERE }, { mule: id });\n"), 1)
        self.assertIn('"d2r_plannerMade"', s[s.find("window._LP_FORKED"):s.find("window._WP_FORKED")])
        self.assertEqual(s.count("var sh={id:'shared', name:'SHARED STASH', icon:'📦', note:SHARED_NOTE};"), 1)
        self.assertIn("Add an item", s)
        self.assertIn("Find on a mule", s)
        self.assertIn("Saved into the vault", s)
        self.assertLess(s.find('id="vault-planner-q"'), s.find('id="vault-find-input"'))
        tip = s.find("function _arttipResolve(nm){")
        built = s.find("_plannerBuiltTip(nm)", tip)
        word = s.find("findRuneword(nm)", tip)
        self.assertGreater(built, tip)
        self.assertLess(built, word, "the catalogue runeword card still wins over the stored base")
        self.assertEqual(s.count("artUrl(nm) || artUrl(r.artName)"), 1)
        self.assertIn("r.builtBase && artUrl(r.artName)", s)
        self.assertIn("window._vpMadeBase", s)
        opened = _cut(s, "  /* ⟦VAULT PLANNER OPEN BEGIN⟧ */\n", "  /* ⟦VAULT PLANNER OPEN END⟧ */\n")
        self.assertIn("planner: true", opened)
        self.assertNotIn("vaultFile(", opened)


RED_PROOF = [
    {
        "why": "REG-1866 - a filing that carries his hand as ownedBy is landed on every pass; without it the next load counts it left",
        "file": "bible.html",
        "find": "    if (cur && (cur.source === 'hand' || (cur.ownedBy && cur.ownedBy.source === 'hand'))) return { ok: true, mode: 'already', name: pre.name };\n",
        "replace": "    if (cur && cur.source === 'hand') return { ok: true, mode: 'already', name: pre.name };\n",
        "matches": 1,
    },
    {
        "why": "REG-1866 - a row that landed leaves the key; without the rewrite it stays there for ever beside the row left",
        "file": "bible.html",
        "find": "    else if (n) window.LSR.setItem(VAULT_HAND_LEGACY, JSON.stringify(kept.map(function(k){ return k.row; })));\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1848 - an owned name is not landed by being owned; counting it landed deletes the hand row he typed",
        "file": "bible.html",
        "find": "    if (!owned.has(pre.name)){\n      var res = _vhCommit(pre, VH_MIGRATE);\n",
        "replace": "    if (owned.has(pre.name)) return { ok: true, mode: 'already', name: pre.name };\n    if (!owned.has(pre.name)){\n      var res = _vhCommit(pre, VH_MIGRATE);\n",
        "matches": 1,
    },
    {
        "why": "REG-1849 - the latch set before the read stops every later paint from trying again",
        "file": "bible.html",
        "find": "    if (_vhMigrated) return null;\n    var raw = null, rows = null;\n",
        "replace": "    if (_vhMigrated) return null;\n    _vhMigrated = true;\n    var raw = null, rows = null;\n",
        "matches": 1,
    },
    {
        "why": "REG-1847 - a receipt the door could not write must be said, not folded into a plain 'added'",
        "file": "bible.html",
        "find": "    var prov = (add && add.prov) || null, receipt = !!(prov && prov.ok === true);\n",
        "replace": "    var prov = (add && add.prov) || null, receipt = true;\n",
        "matches": 1,
    },
    {
        "why": "REG-1847 - an ambiguity check that raised is UNKNOWN; reading it as 'not ambiguous' adds the raw name",
        "file": "bible.html",
        "find": "    catch (e) { return { ok: false, refused: 'unknown', why: 'whether \"' + raw + '\" names one item could not be asked — nothing was added' }; }\n",
        "replace": "    catch (e) { amb = null; }\n",
        "matches": 1,
    },
    {
        "why": "REG-1850 - an unsettled name counted as 'the vault does not draw it' is a wrong reason",
        "file": "bible.html",
        "find": "      if (!c.name){ unsettled++; return; }\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1848 - a row left behind must be said on the Vault; without the paint it is invisible",
        "file": "bible.html",
        "find": "    try { if (typeof window._vaultHandLeftPaint === 'function') window._vaultHandLeftPaint(); } catch (eL) {}\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "only a name the vault draws is added; dropping the keep check files a crafted recipe that renders nowhere",
        "file": "bible.html",
        "find": "    if (!_vaultKeeps(r.name))\n      return { ok: false, refused: 'not-drawn', name: r.name,\n",
        "replace": "    if (false)\n      return { ok: false, refused: 'not-drawn', name: r.name,\n",
        "matches": 1,
    },
    {
        "why": "the add must reach d2r_owned; without the persist it lives until the next reload",
        "file": "bible.html",
        "find": "    persistOwned();\n    var prov = (add && add.prov) || null, receipt = !!(prov && prov.ok === true);\n",
        "replace": "    var prov = (add && add.prov) || null, receipt = !!(prov && prov.ok === true);\n",
        "matches": 1,
    },
    {
        "why": "the pick is filed under the register's name; skipping the resolution makes a second tile for one item",
        "file": "bible.html",
        "find": "nm = String(window._vaultResolveName(nm) || nm); }\n",
        "replace": "nm = nm; }\n",
        "matches": 1,
    },
    {
        "why": "the second key is removed only when every row landed; removing it always loses what he typed",
        "file": "bible.html",
        "find": "    if (!kept.length) window.LSR.removeItem(VAULT_HAND_LEGACY);\n",
        "replace": "    window.LSR.removeItem(VAULT_HAND_LEGACY);\n",
        "matches": 1,
    },
    {
        "why": "renderVault must bring the second key home; without the call its rows never reach owned",
        "file": "bible.html",
        "find": "    try { if (typeof window._vaultHandMigrate === 'function') window._vaultHandMigrate(); } catch (eH) {}\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "a planner pick must be filed by the reel door; skipping that call leaves the catalogue pick unfiled",
        "file": "bible.html",
        "find": "    var filed = window.vaultFile(nm, { by: 'hand', at: at, where: VP_WHERE }, { mule: id });\n",
        "replace": "    var filed = { ok: true, mode: 'skipped' };\n",
        "matches": 1,
    },
    {
        "why": "a later open of a filed name must count another copy; without the token check the second Grief stays one",
        "file": "bible.html",
        "find": "      if (routed.mode === 'already' && assign[nm] != null && _vpCopySeen[nm] && _vpCopySeen[nm] !== token){\n",
        "replace": "      if (false && routed.mode === 'already' && assign[nm] != null && _vpCopySeen[nm] && _vpCopySeen[nm] !== token){\n",
        "matches": 1,
    },
    {
        "why": "a vault item click must keep the floating card; dropping the keep returns the page route",
        "file": "bible.html",
        "find": "        if (chip && !chip.classList.contains('vd-db') && !t.closest('button, a, input, textarea, select')) return;\n",
        "replace": "        if (false) return;\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
