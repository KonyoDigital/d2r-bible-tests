# -*- coding: utf-8 -*-
"""#234 step 5 — the Vault says where an item belongs, and does not move it.

The router's own sentence is painted on a hand-added row and on each witnessed
item still in the unsorted dock. A locked name stays, with the lock's reason.
Null is the shared stash. A missing reason names no mule. Nothing is stored
and nothing is assigned.
"""
import json
import os
import shutil
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
import sys as _sys  # noqa: E402
if HERE not in _sys.path:
    _sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402  - REG-1834: these print non-ASCII
_console_safe_enable()
BIBLE = os.path.join(HERE, "..", "bible.html")
NODE = shutil.which("node")

PARK = "nothing on the board recognises this name — parked in weapons, worth your eye"
LOCK = "seen in your equipment in 4 separate sessions"

HARNESS = r"""
var OUT = {};
var RAW = {};
var WRITES = 0;
var ELS = {};
var CALLS = [];
function El(){ this.id = ''; this.hidden = true; this._html = ''; this._attrs = {}; }
El.prototype.getAttribute = function(n){ return Object.prototype.hasOwnProperty.call(this._attrs, n) ? this._attrs[n] : null; };
El.prototype.setAttribute = function(n, v){ this._attrs[n] = String(v); };
Object.defineProperty(El.prototype, 'innerHTML', {
  set: function(h){
    this._html = String(h);
    var re = /id="([^"]+)"/g, m;
    while ((m = re.exec(this._html))){
      if (!ELS[m[1]]){ var c = new El(); c.id = m[1]; c.hidden = false; ELS[m[1]] = c; }
    }
  },
  get: function(){ return this._html; }
});
var document = {
  getElementById: function(id){ return ELS[id] || null; },
  createElement: function(){ return new El(); },
  body: { appendChild: function(c){ if (c.id) ELS[c.id] = c; } },
  documentElement: { classList: { contains: function(){ return false; } } }
};
var window = global;
window.LSR = {
  getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
  setItem: function(k, v){ WRITES++; RAW[k] = String(v); }
};
ELS['vault-hand'] = new El();
ELS['vault-hand'].id = 'vault-hand';
ELS['vault-organize'] = new El();
ELS['vault-organize'].id = 'vault-organize';
"""


def _bible():
    with open(BIBLE, encoding="utf-8") as fh:
        return fh.read()


def _between(src, a, b):
    i = src.find(a)
    if i < 0 or src.find(a, i + len(a)) >= 0:
        raise AssertionError("marker missing or not unique: %r" % a)
    start = src.find("\n", i)
    j = src.find(b, start + 1) if start >= 0 else -1
    if start < 0 or j < 0:
        raise AssertionError("markers missing: %r .. %r" % (a, b))
    return src[start + 1:j]


def _node(body):
    if not NODE:
        raise AssertionError("node is not on this machine — this gate does not skip")
    src = _bible()
    hand = _between(src, "/* ⟦VAULT HAND BEGIN⟧", "/* ⟦VAULT HAND END⟧")
    script = HARNESS + hand + "\n" + body + "\nconsole.log(JSON.stringify(OUT));\n"
    p = subprocess.run([NODE, "-e", script], capture_output=True, text=True, timeout=30)
    if p.returncode != 0:
        raise AssertionError((p.stderr or p.stdout)[-2000:])
    return json.loads(p.stdout)


class TheVaultProposesAHomeAndDoesNotMove(unittest.TestCase):

    def test_a_hand_row_shows_the_routers_own_reason(self):
        out = _node(r"""
          window.suggestMule = function(nm){
            CALLS.push(nm);
            if (nm === 'Battlecage') return { id: 'uni-weap', why: %s };
            if (nm === 'Harlequin Crest') return { id: 'uni-armor', why: 'armor slot — Shako' };
            return { id: 'uni-weap' };
          };
          var added = window.vaultHandAdd('Battlecage', '2026-10-05T12:00:00.000Z');
          window.vaultHandAdd('Harlequin Crest', '2026-10-05T12:00:01.000Z');
          var writes = WRITES;
          var raw = RAW['d2r_vaultHand'];
          OUT.propose = window.vaultPropose('Battlecage');
          OUT.paint = window.vaultHandPaint();
          OUT.section = ELS['vault-hand']._html;
          OUT.rows = JSON.parse(RAW['d2r_vaultHand']);
          OUT.same = RAW['d2r_vaultHand'] === raw;
          OUT.writes = WRITES - writes;
          OUT.assign = RAW['d2r_muleAssign'] || null;
          OUT.added = added.mode;
        """ % json.dumps(PARK))
        self.assertEqual(out["added"], "added")
        self.assertTrue(out["propose"]["ok"])
        self.assertFalse(out["propose"]["moved"])
        self.assertFalse(out["propose"]["stays"])
        self.assertEqual(out["propose"]["id"], "uni-weap")
        self.assertEqual(out["propose"]["why"], PARK)
        self.assertIn('data-home="uni-weap"', out["section"])
        self.assertIn('data-state="proposed"', out["section"])
        self.assertIn('data-moved="false"', out["section"])
        self.assertIn(PARK, out["section"])
        self.assertIn("armor slot — Shako", out["section"])
        self.assertIn('data-home="uni-armor"', out["section"])
        self.assertNotIn("weapon theme", out["section"])
        self.assertEqual(out["writes"], 0)
        self.assertTrue(out["same"])
        self.assertIsNone(out["assign"])
        for row in out["rows"]:
            self.assertEqual(sorted(row.keys()), ["at", "name", "seen", "source"])

    def test_a_missing_reason_names_no_mule(self):
        out = _node(r"""
          window.suggestMule = function(nm){
            if (nm === 'Nope') return { id: 'uni-weap' };
            if (nm === 'Ort') return null;
            if (nm === 'Boom') throw new Error('router down');
            return { id: 'uni-small', why: 'charm/skiller' };
          };
          OUT.nowhy = window.vaultProposeLine('Nope');
          OUT.shared = window.vaultProposeLine('Ort');
          OUT.boom = window.vaultProposeLine('Boom');
          delete window.suggestMule;
          OUT.gone = window.vaultProposeLine('Harlequin Crest');
          OUT.writes = WRITES;
        """)
        self.assertIn('data-state="unknown"', out["nowhy"])
        self.assertIn("the router gave no reason", out["nowhy"])
        self.assertNotIn("data-home", out["nowhy"])
        self.assertNotIn("uni-weap", out["nowhy"])
        self.assertIn('data-home="shared stash"', out["shared"])
        self.assertIn("shared stash — the router gave no reason", out["shared"])
        self.assertNotIn("high trade", out["shared"])
        self.assertNotIn("rare", out["shared"])
        self.assertIn('data-state="unknown"', out["boom"])
        self.assertIn("the router could not be asked", out["boom"])
        self.assertNotIn("data-home", out["boom"])
        self.assertNotIn("uni-weap", out["boom"])
        self.assertIn("the router is not on this page", out["gone"])
        self.assertNotIn("data-home", out["gone"])
        self.assertEqual(out["writes"], 0)

    def test_a_locked_name_is_not_offered_a_mule(self):
        out = _node(r"""
          window._laneLockWhy = function(nm){
            if (nm === 'Harlequin Crest') return { lane: 'equipment', why: %s };
            return null;
          };
          window.suggestMule = function(nm){
            CALLS.push(nm);
            return { id: 'uni-weap', why: 'weapon — base: Shako' };
          };
          OUT.line = window.vaultProposeLine('Harlequin Crest');
          OUT.calls = CALLS.slice();
          OUT.open = window.vaultProposeLine('Stone of Jordan');
          OUT.openCalls = CALLS.slice();
        """ % json.dumps(LOCK))
        self.assertIn('data-state="stays"', out["line"])
        self.assertIn(LOCK, out["line"])
        self.assertNotIn("data-home", out["line"])
        self.assertNotIn("uni-weap", out["line"])
        self.assertEqual(out["calls"], [])
        self.assertIn('data-home="uni-weap"', out["open"])
        self.assertEqual(out["openCalls"], ["Stone of Jordan"])

    def test_a_witnessed_item_gets_the_same_sentence_and_nothing_moves(self):
        src = _bible()
        propose = _between(src, "/* ⟦VAULT PROPOSE BEGIN⟧", "/* ⟦VAULT PROPOSE END⟧")
        self.assertNotIn("vaultAutoAssign", propose)
        self.assertNotIn("setItem", propose)
        self.assertNotIn("assign[", propose)
        self.assertNotIn("onclick", propose)
        self.assertEqual(src.count("window.vaultProposeLine(r.name)"), 1)
        self.assertEqual(src.count("window.vaultOrganizePaint(unsorted)"), 1)
        dock_at = src.find("dock.innerHTML = unsorted.map(function(n){")
        dock_end = src.find(".join('');", dock_at)
        self.assertGreater(dock_at, 0)
        self.assertNotIn("vaultPropose", src[dock_at:dock_end])
        self.assertEqual(src.count('id="vault-organize"'), 1)
        out = _node(r"""
          window.suggestMule = function(nm){
            if (nm === 'Battlecage') return { id: 'uni-weap', why: %s };
            if (nm === 'a < b') return { id: '__throwout', why: 'trade value TRASH — advice only' };
            return { id: 'uni-weap' };
          };
          OUT.empty = window.vaultOrganizePaint([]);
          OUT.hidden = ELS['vault-organize'].hidden;
          OUT.bad = window.vaultOrganizeLine ? null : window.vaultOrganizePaint(null);
          OUT.paint = window.vaultOrganizePaint(['Battlecage', 'a < b']);
          OUT.html = ELS['vault-organize']._html;
          OUT.writes = WRITES;
          OUT.hand = RAW['d2r_vaultHand'] || null;
          OUT.assign = RAW['d2r_muleAssign'] || null;
        """ % json.dumps(PARK))
        self.assertEqual(out["empty"]["n"], 0)
        self.assertTrue(out["hidden"])
        self.assertFalse(out["bad"]["ok"])
        self.assertIn("the organizer was not given a list", out["bad"]["why"])
        self.assertEqual(out["paint"]["n"], 2)
        self.assertIn('data-name="Battlecage"', out["html"])
        self.assertIn(PARK, out["html"])
        self.assertIn('data-home="__throwout"', out["html"])
        self.assertIn("trade value TRASH — advice only", out["html"])
        self.assertIn('data-name="a &lt; b"', out["html"])
        self.assertNotIn("onclick", out["html"])
        self.assertEqual(out["writes"], 0)
        self.assertIsNone(out["hand"])
        self.assertIsNone(out["assign"])


RED_PROOF = [
    {
        "why": "a hand-added row must show the router's sentence; dropping the paint leaves the testimony with no destination",
        "file": "bible.html",
        "find": "          + window.vaultProposeLine(r.name) + '</li>';\n",
        "replace": "          + '</li>';\n",
        "matches": 1,
    },
    {
        "why": "a witnessed item in the dock must be asked too; dropping the call leaves that half unjoined",
        "file": "bible.html",
        "find": "    try { if (typeof window.vaultOrganizePaint === 'function') window.vaultOrganizePaint(unsorted); } catch (eO) {}\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "a router that throws must stay unknown; a weapon home in the catch fabricates a destination",
        "file": "bible.html",
        "find": "    catch (e) { return { ok: false, moved: false, home: null, id: null, stays: false, why: 'the router could not be asked' }; }\n",
        "replace": "    catch (e) { return { ok: true, moved: false, id: 'uni-weap', home: 'uni-weap', stays: false, why: 'weapon — base: Battlecage' }; }\n",
        "matches": 1,
    },
    {
        "why": "a locked name stays; deleting the lock return offers it a mule",
        "file": "bible.html",
        "find": "    if (held && held.why) return { ok: true, moved: false, id: null, home: null, stays: true, why: String(held.why) };\n",
        "replace": "",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
