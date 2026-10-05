# -*- coding: utf-8 -*-
"""#234 step 4 — an item he adds in the Vault is his testimony, and a reader does not replace it.

+ Add an item opens the planner's own list. A pick is one ledger row, source manual.
A second add leaves that row. A reader that later agrees is written beside it.
The manual fact stays. A name he did not pick is not filed. Nothing is assigned to a mule.
"""
import json
import os
import shutil
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BIBLE = os.path.join(HERE, "..", "bible.html")
NODE = shutil.which("node")

HARNESS = r"""
var OUT = {};
var RAW = {};
var WRITES = 0;
var ELS = {};
var OPENED = [];
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
  documentElement: { classList: { contains: function(c){ return c === 'cb-lock' && global.__cbLock === true; } } }
};
var window = global;
window.openCharBuilder = function(){ OPENED.push('plan'); };
window.LSR = {
  getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
  setItem: function(k, v){ WRITES++; RAW[k] = String(v); }
};
ELS['vault-hand'] = new El();
ELS['vault-hand'].id = 'vault-hand';
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


class AHandAddedItemStaysHis(unittest.TestCase):

    def test_a_pick_from_the_planner_list_files_one_manual_row(self):
        out = _node(r"""
          window._cbHandCatalog = function(){ return { ok: true, rows: [
            { id: 'u:shako', name: 'Harlequin Crest', q: 'u' },
            { id: 'u:soj', name: 'Stone of Jordan', q: 'u' } ] }; };
          OUT.open = window.vaultHandOpen();
          OUT.list = ELS['vault-hand-list']._html;
          OUT.take = window.vaultHandTake('u:shako');
          OUT.foreign = window.vaultHandTake('not-a-real-id');
          OUT.rows = JSON.parse(RAW['d2r_vaultHand']);
          OUT.opened = OPENED.slice();
          OUT.section = ELS['vault-hand']._html;
          OUT.assign = RAW['d2r_muleAssign'] || null;
          OUT.builds = RAW['d2r_charBuilds'] || null;
        """)
        self.assertTrue(out["open"]["ok"])
        self.assertIn('data-id="u:shako"', out["list"])
        self.assertIn("Harlequin Crest", out["list"])
        self.assertEqual(out["take"]["mode"], "added")
        self.assertEqual(out["take"]["row"]["source"], "manual")
        self.assertIsNone(out["take"]["row"]["seen"])
        self.assertEqual(out["foreign"]["refused"], "not-listed")
        self.assertEqual(len(out["rows"]), 1)
        self.assertEqual(out["rows"][0]["name"], "Harlequin Crest")
        self.assertEqual(out["rows"][0]["source"], "manual")
        self.assertEqual(out["opened"], [])
        self.assertIsNone(out["assign"])
        self.assertIsNone(out["builds"])
        self.assertIn('data-source="manual"', out["section"])
        self.assertIn("by hand", out["section"])
        self.assertNotIn("also seen", out["section"])

    def test_a_second_add_does_not_replace_the_row(self):
        out = _node(r"""
          OUT.first = window.vaultHandAdd('Harlequin Crest', '2026-10-05T12:00:00.000Z');
          OUT.second = window.vaultHandAdd('harlequin crest', '2026-10-06T12:00:00.000Z');
          OUT.rows = JSON.parse(RAW['d2r_vaultHand']);
        """)
        self.assertEqual(out["first"]["mode"], "added")
        self.assertEqual(out["second"]["mode"], "already")
        self.assertEqual(len(out["rows"]), 1)
        self.assertEqual(out["rows"][0]["name"], "Harlequin Crest")
        self.assertEqual(out["rows"][0]["source"], "manual")
        self.assertEqual(out["rows"][0]["at"], "2026-10-05T12:00:00.000Z")
        self.assertIsNone(out["rows"][0]["seen"])

    def test_a_reader_sits_beside_the_manual_row(self):
        out = _node(r"""
          window.vaultHandAdd('Harlequin Crest', '2026-10-05T12:00:00.000Z');
          OUT.miss = window.vaultHandAgree('Stone of Jordan', { source: 'stash', at: '2026-10-05T13:00:00.000Z' });
          OUT.hand = window.vaultHandAgree('Harlequin Crest', { source: 'hand', at: '2026-10-05T13:00:00.000Z' });
          OUT.afterHand = JSON.parse(RAW['d2r_vaultHand'])[0].seen;
          OUT.seen = window.vaultHandAgree('Harlequin Crest', { source: 'stash', at: '2026-10-05T13:00:00.000Z' });
          OUT.later = window.vaultHandAgree('Harlequin Crest', { source: 'inventory', at: '2026-10-05T14:00:00.000Z' });
          OUT.rows = JSON.parse(RAW['d2r_vaultHand']);
          window.vaultHandPaint();
          OUT.section = ELS['vault-hand']._html;
        """)
        self.assertFalse(out["miss"]["noted"])
        self.assertEqual(len(out["rows"]), 1, "a reader created a row he never added")
        self.assertFalse(out["hand"]["noted"])
        self.assertIsNone(out["afterHand"], "his own hand was recorded as a reader")
        self.assertTrue(out["seen"]["noted"])
        self.assertEqual(out["rows"][0]["source"], "manual")
        self.assertEqual(out["rows"][0]["at"], "2026-10-05T12:00:00.000Z")
        self.assertEqual(out["rows"][0]["seen"]["source"], "stash")
        self.assertEqual(out["rows"][0]["seen"]["at"], "2026-10-05T13:00:00.000Z")
        self.assertFalse(out["later"]["noted"])
        self.assertEqual(out["rows"][0]["seen"]["source"], "stash", "a later read replaced the first witness")
        self.assertIn('data-source="manual"', out["section"])
        self.assertIn('data-seen="stash"', out["section"])
        self.assertIn("also seen in stash", out["section"])

    def test_an_unreadable_ledger_is_not_an_empty_one(self):
        out = _node(r"""
          RAW['d2r_vaultHand'] = '{';
          OUT.add = window.vaultHandAdd('Harlequin Crest', '2026-10-05T12:00:00.000Z');
          OUT.agree = window.vaultHandAgree('Harlequin Crest', { source: 'stash', at: '2026-10-05T13:00:00.000Z' });
          OUT.writes = WRITES;
          window.vaultHandPaint();
          OUT.section = ELS['vault-hand']._html;
          delete RAW['d2r_vaultHand'];
          window.vaultHandPaint();
          OUT.empty = ELS['vault-hand']._html;
          window._cbHandCatalog = function(){ return { ok: false, why: 'the planner list could not be read', rows: null }; };
          window.vaultHandOpen();
          OUT.list = ELS['vault-hand-list']._html;
        """)
        self.assertEqual(out["add"]["refused"], "unreadable")
        self.assertEqual(out["agree"]["refused"], "unreadable")
        self.assertEqual(out["writes"], 0, "an unreadable ledger was written over")
        self.assertIn('data-state="unknown"', out["section"])
        self.assertNotIn("Nothing added by hand", out["section"])
        self.assertIn('data-state="empty"', out["empty"])
        self.assertIn("Nothing added by hand.", out["empty"])
        self.assertIn('data-state="unknown"', out["list"])
        self.assertNotIn("No item in the planner list matches", out["list"])

    def test_the_door_uses_the_planner_list_and_the_reader_notes_it(self):
        src = _bible()
        self.assertEqual(src.count('onclick="window.vaultHandOpen()"'), 1)
        self.assertIn('id="tab-vault"', src[:src.find('onclick="window.vaultHandOpen()"')])
        self.assertEqual(src.count("else rows = _cbForSlot(slot, p.rail, p.host === 'hand');"), 1)
        catalog = _between(src, "/* ⟦VAULT HAND CATALOG BEGIN⟧", "/* ⟦VAULT HAND CATALOG END⟧")
        self.assertIn("host: 'hand'", catalog)
        self.assertIn("_cbRowsFor(", catalog)
        self.assertEqual(src.count("_noteHand(nm, row.source, row.at);"), 1)
        self.assertEqual(src.count("_noteHand(nm, (wc.kind === 'lane') ? wc.lane : wc.kind, null);"), 3)
        door = _between(src, "window.vaultFile = function(name, witness, opts){", "function _provAsWitness")
        self.assertNotIn("vaultHandAdd", door, "the mule door creates a hand row")
        hand = _between(src, "/* ⟦VAULT HAND BEGIN⟧", "/* ⟦VAULT HAND END⟧")
        self.assertNotIn("vaultFile", hand, "adding by hand files to a mule")
        self.assertIn('"d2r_vaultHand"', src[src.find("window._LP_FORKED"):src.find("window._WP_FORKED")])
        cat = _node_catalog()
        self.assertTrue(cat["ok"])
        self.assertEqual(cat["rows"], [{"id": "u:shako", "name": "Harlequin Crest", "q": "u"}])
        self.assertEqual(cat["asked"]["host"], "hand")
        self.assertEqual(cat["asked"]["slot"], "minv")
        self.assertTrue(cat["noCls"])


def _node_catalog():
    if not NODE:
        raise AssertionError("node is not on this machine — this gate does not skip")
    src = _bible()
    catalog = _between(src, "/* ⟦VAULT HAND CATALOG BEGIN⟧", "/* ⟦VAULT HAND CATALOG END⟧")
    script = r"""
var window = global;
var ASKED = null;
var CB_MINV = 'minv';
function _cbRowsFor(p){ ASKED = p; return [['u:shako', 'Harlequin Crest', 'u']]; }
""" + catalog + r"""
var OUT = window._cbHandCatalog('crest');
OUT.asked = ASKED;
console.log(JSON.stringify(OUT));
"""
    p = subprocess.run([NODE, "-e", script], capture_output=True, text=True, timeout=30)
    if p.returncode != 0:
        raise AssertionError((p.stderr or p.stdout)[-2000:])
    out = json.loads(p.stdout)
    out["noCls"] = "else rows = _cbForSlot(slot, p.rail, p.host === 'hand');" in src
    return out


RED_PROOF = [
    {
        "why": "a second add must leave the first manual row; deleting the already-return files him twice",
        "file": "bible.html",
        "find": "    if (hit) return { ok: true, mode: 'already', row: hit };\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "a landed witness has to note the hand row; dropping the call leaves the reader and the testimony unjoined",
        "file": "bible.html",
        "find": "    _noteHand(nm, row.source, row.at);\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the vault list is the planner list with the class filter off; dropping that argument hides items behind whatever build is open",
        "file": "bible.html",
        "find": "    else rows = _cbForSlot(slot, p.rail, p.host === 'hand');\n",
        "replace": "    else rows = _cbForSlot(slot, p.rail);\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
