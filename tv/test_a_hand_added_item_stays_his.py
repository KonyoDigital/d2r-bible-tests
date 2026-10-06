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
        self.assertEqual(out["m"], {"ok": True, "n": 2, "left": 0})
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
          OUT.same = STORE['d2r_vaultHand'] === raw;
          OUT.owned = Array.from(owned);
        """)
        self.assertEqual(kept["m"], {"ok": True, "n": 1, "left": 1})
        self.assertTrue(kept["same"], "a row the vault could not take was dropped or rewritten")
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

    def test_the_joins(self):
        s = _src()
        code = code_only(s)
        rv = _cut(code, "  function renderVault(){\n", "    renderMultiKeep();\n")
        self.assertEqual(rv.count("window._vaultHandMigrate();"), 1, "renderVault does not bring the second key home")
        self.assertLess(rv.index("window._vaultHandMigrate();"), rv.index("var poolAll=ownedPool();"),
                        "the migration runs after the pool was read")
        self.assertIn("return Array.from(owned).filter(_vaultKeeps).sort();", _cut(code, KEEPS_B, "  function art(n, glyph, size){"))
        hand = code_only(_cut(s, HAND_A, HAND_B))
        self.assertEqual(hand.count("var add = window._ownedAdd(nm, { source: 'hand',"), 1, "the door does not use the owned door")
        for banned in ("setItem(", "vaultFile(", "assign[", "suggestMule("):
            self.assertNotIn(banned, hand, "the hand door reaches %s" % banned)
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


RED_PROOF = [
    {
        "why": "only a name the vault draws is added; dropping the keep check files a crafted recipe that renders nowhere",
        "file": "bible.html",
        "find": "    if (!_vaultKeeps(nm))\n      return { ok: false, refused: 'not-drawn', name: nm,\n",
        "replace": "    if (false)\n      return { ok: false, refused: 'not-drawn', name: nm,\n",
        "matches": 1,
    },
    {
        "why": "the add must reach d2r_owned; without the persist it lives until the next reload",
        "file": "bible.html",
        "find": "    persistOwned();\n    return { ok: true, mode: 'added', name: nm,",
        "replace": "    return { ok: true, mode: 'added', name: nm,",
        "matches": 1,
    },
    {
        "why": "the pick is filed under the register's name; skipping the resolution makes a second tile for one item",
        "file": "bible.html",
        "find": "    try { if (typeof window._vaultResolveName === 'function') nm = String(window._vaultResolveName(nm) || nm); } catch (e) {}\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the second key is removed only when every row landed; removing it always loses what he typed",
        "file": "bible.html",
        "find": "    if (!left) window.LSR.removeItem(VAULT_HAND_LEGACY);\n",
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
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
