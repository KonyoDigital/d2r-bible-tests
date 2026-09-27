# -*- coding: utf-8 -*-
"""The full vault reset files back only what the evidence plan names.

His ruling 2026-09-27: a reset clears the marks, never the witness ledger, and then rebuilds what
that ledger proved. The bar is vault_evidence.rebuild_plan — one table. The filing is
window.vaultFile — one door. This law drives both on a seeded ledger, not his.

A 12-look item comes back proven. A 21-look item comes back locked. Twelve looks with five misses
stay cleared, and so does a 2-look item. An equipped item and a sunder come back below the bar.
An unreadable count is not rebuilt. The ledger file is byte-identical afterwards. When the plan
cannot be read, the status says UNKNOWN and does not say the vault was empty.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_a_vault_reset_clears_only_the_mules as RESET
import test_every_mule_filing_carries_its_witness as FILE
import vault_evidence as VE

NODE = shutil.which("node")
PLAN_URL = "http://127.0.0.1:17772/api/vault_rebuild_plan"
CELL = {"tab": "personal", "x": 3, "y": 4}
BACK = ["Shako", "Arachnid Mesh", "Harlequin Crest", "Lightning Sunder Charm"]
HELD = ["War Traveler", "Chance Guards", "Unread Thing"]

EXTRA = r"""
function muleById(id){ return id === 'uni-armor' ? { id: 'uni-armor', name: 'UNI-ARMOR' } : null; }
function suggestMule(n){ return { id: 'uni-armor', why: 'the law routes a proven stash item to UNI-ARMOR' }; }
function isSharedStash(n){ return false; }
function ownedPool(){ return Array.from(owned); }
var LOCKS = {};
window._laneLocked = function(n){ return LOCKS[n] || ''; };
window._mainTag = function(){ return 'MAIN'; };
window._consumable = function(){ return false; };
window.D2R_BUILD = window.D2R_BUILD || { id: 'vLAW' };
"""

BODY = r"""
var PLAN = __PLAN__;
var FETCH_MODE = 'plan';
var location = { hostname: '127.0.0.1' };
var FETCHES = [], ASKED = [];
globalThis.fetch = function(url){
  FETCHES.push(String(url));
  var body = FETCH_MODE === 'plan' ? PLAN : { ok: false, why: 'the witness ledger could not be read' };
  return Promise.resolve({ ok: FETCH_MODE === 'plan', json: function(){ return Promise.resolve(body); } });
};
var _doorFile = window.vaultFile;
window.vaultFile = function(name, w, o){ ASKED.push(String(name)); return _doorFile(name, w, o); };
function seed(){
  Object.keys(STORE).forEach(function(k){ delete STORE[k]; });
  assign = { 'Decoy Item': 'uni-armor' };
  owned = new Set(['Decoy Item']);
  setPieces = new Set(['Tal Rasha Armor']);
  unknownReads = new Set();
  magicFinds = { 'A Magic': { at: '2026-09-20' } };
  copies = {}; multiKeep = {}; rwMade = { Spirit: 1 };
  STORE['d2r_muleAssign'] = JSON.stringify(assign);
  STORE['d2r_vaultProv'] = JSON.stringify({ 'Decoy Item': { mule: 'uni-armor', source: 'hand', by: 'hand' } });
  STORE['d2r_intakeLog'] = JSON.stringify([{ ts: 1, items: ['Decoy Item'] }]);
  STORE['d2r_intakeSeen'] = JSON.stringify({ 'shot.png': 1 });
  STORE['d2r_owned'] = JSON.stringify(['Decoy Item']);
  STORE['d2r_setPieces'] = JSON.stringify(['Tal Rasha Armor']);
  STORE['d2r_magicFinds'] = JSON.stringify(magicFinds);
  STORE['d2r_copies'] = '{}';
  STORE['d2r_multiKeep'] = '{}';
  STORE['d2r_unknownReads'] = '[]';
  STORE['d2r_foundLog'] = JSON.stringify({ 'Decoy Item': '2026-09-01' });
  STORE['d2r_rwMade'] = JSON.stringify(rwMade);
  STORE['d2r_runeStash'] = JSON.stringify({ Ber: 1 });
  IDB['d2r_vault_fs/shotdir'] = { fake: true };
  UNLINKS = 0; CONFIRMS.length = 0; STATUS.length = 0; ASKED.length = 0; FETCHES.length = 0;
  window._vaultLastReset = undefined;
  ANSWER = true;
}
function snap(){ return JSON.parse(JSON.stringify(STORE)); }
(async function(){
  var OUT = {};
  seed();
  var keeps = snap();
  await window.vaultReset();
  OUT.assignDoor = { fetches: FETCHES.slice(), asked: ASKED.slice(),
                     assign: JSON.parse(JSON.stringify(assign)),
                     owned: Array.from(owned), confirm: CONFIRMS[0] || '' };
  seed();
  var before = snap();
  await window.vaultClearHistory();
  var prov = {};
  try { prov = JSON.parse(STORE['d2r_vaultProv'] || '{}'); } catch (e) { prov = {}; }
  OUT.full = { fetches: FETCHES.slice(), asked: ASKED.slice(),
               assign: JSON.parse(JSON.stringify(assign)), owned: Array.from(owned),
               prov: prov, status: STATUS.length ? STATUS[STATUS.length - 1] : '',
               confirm: CONFIRMS[0] || '',
               receipt: window._vaultLastReset || null,
               keptSame: before['d2r_setPieces'] === STORE['d2r_setPieces']
                      && before['d2r_foundLog'] === STORE['d2r_foundLog']
                      && before['d2r_rwMade'] === STORE['d2r_rwMade']
                      && before['d2r_runeStash'] === STORE['d2r_runeStash']
                      && before['d2r_magicFinds'] === STORE['d2r_magicFinds'],
               journalGone: !Object.prototype.hasOwnProperty.call(STORE, 'd2r_intakeLog') };
  seed();
  FETCH_MODE = 'unread';
  await window.vaultClearHistory();
  OUT.unread = { asked: ASKED.slice(), owned: Array.from(owned),
                 assign: JSON.parse(JSON.stringify(assign)),
                 status: STATUS.length ? STATUS[STATUS.length - 1] : '',
                 receipt: window._vaultLastReset || null,
                 sets: STORE['d2r_setPieces'] };
  process.stdout.write(JSON.stringify(OUT));
})().catch(function(e){ process.stderr.write(String((e && e.stack) || e)); process.exit(3); });
"""


def _looks(n, misses=0, cell=None):
    rows = []
    for i in range(n):
        row = {"session": "s%02d" % i, "frame": "f%02d.jpg" % i, "conf": 0.91, "lane": "stash"}
        if cell:
            row["cell"] = dict(cell)
        if misses and i >= n - misses:
            row["saw"] = "empty"
        rows.append(row)
    return rows


def _ledger():
    return {"owned": [
        {"name": "Shako", "lane": "stash", "kind": "item",
         "witnesses": _looks(12, cell=CELL)},
        {"name": "Arachnid Mesh", "lane": "stash", "kind": "item", "witnesses": _looks(21)},
        {"name": "War Traveler", "lane": "stash", "kind": "item", "witnesses": _looks(12, misses=5)},
        {"name": "Chance Guards", "lane": "stash", "kind": "item", "witnesses": _looks(2)},
        {"name": "Harlequin Crest", "lane": "equipment", "equipped": True, "kind": "item",
         "witnesses": _looks(2)},
        {"name": "Lightning Sunder Charm", "lane": "stash", "kind": "sunder", "witnesses": []},
        {"name": "Unread Thing", "lane": "stash", "witnesses": 4},
    ]}


def _drive(plan):
    with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
        src = fh.read()
    body = BODY.replace("__PLAN__", json.dumps(plan))
    prog = RESET.HARNESS + EXTRA + FILE._door(src) + RESET._pieces(src) + body
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("the shipped reset would not execute — UNKNOWN, not passing: %s"
                             % (r.stderr or r.stdout)[-900:])
    return json.loads(r.stdout)


@unittest.skipIf(NODE is None, "node is absent — the shipped door was not driven, so this is not a pass")
class AResetRefilesOnlyWhatThePlanSays(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="vault-evidence-law-")
        cls.path = os.path.join(cls.tmp, "witness.json")
        blob = json.dumps(_ledger()).encode("utf-8")
        with io.open(cls.path, "wb") as fh:
            fh.write(blob)
        cls.before = blob
        cls.plan = VE.plan_from_ledger(cls.path)
        with io.open(cls.path, "rb") as fh:
            cls.same = fh.read()
        cls.out = _drive(cls.plan)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_ledger_is_not_written(self):
        self.assertEqual(self.before, self.same, "plan_from_ledger wrote the witness ledger")
        with io.open(self.path, "rb") as fh:
            self.assertEqual(self.before, fh.read())
        missing = VE.plan_from_ledger(self.path + ".absent")
        self.assertFalse(missing["ok"])
        self.assertEqual([], missing["rebuilt"])
        self.assertIn("could not be read", missing["why"])
        self.assertIn("nothing is called empty", missing["why"])

    def test_the_plan_is_the_only_bar(self):
        plan = self.plan
        self.assertTrue(plan["ok"], plan.get("why"))
        self.assertEqual(BACK, [r["name"] for r in plan["rebuilt"]])
        self.assertEqual(HELD, [r["name"] for r in plan["held"]])
        by = dict((r["name"], r) for r in plan["rebuilt"])
        self.assertEqual("PROVEN", by["Shako"]["tier"])
        self.assertFalse(by["Shako"]["locked"])
        self.assertIsNone(by["Shako"]["home"])
        self.assertEqual(12, by["Shako"]["successes"])
        self.assertEqual(12, by["Shako"]["trials"])
        self.assertEqual([CELL], by["Shako"]["cells"])
        self.assertEqual(12, len(by["Shako"]["sessions"]))
        self.assertEqual("HARDENED", by["Arachnid Mesh"]["tier"])
        self.assertTrue(by["Arachnid Mesh"]["locked"])
        self.assertEqual("__keep", by["Harlequin Crest"]["home"])
        self.assertEqual("kept kind", by["Harlequin Crest"]["why"])
        self.assertEqual("__keep", by["Lightning Sunder Charm"]["home"])
        self.assertEqual("kept kind", by["Lightning Sunder Charm"]["why"])
        self.assertIn("UNKNOWN", plan["held"][-1]["why"])

    def test_the_console_hands_that_ledger_to_the_plan(self):
        import control_app as CA
        got = CA.vault_rebuild_plan(self.path)
        self.assertEqual(BACK, [r["name"] for r in got["rebuilt"]])
        self.assertEqual(HELD, [r["name"] for r in got["held"]])
        with io.open(self.path, "rb") as fh:
            self.assertEqual(self.before, fh.read(), "the console route wrote the witness ledger")

    def test_assignments_reset_does_not_refile(self):
        door = self.out["assignDoor"]
        self.assertEqual([], door["fetches"], "Reset assignments asked the evidence plan")
        self.assertEqual([], door["asked"])
        self.assertNotIn("Shako", door["assign"])
        self.assertEqual(["Decoy Item"], door["owned"])
        self.assertNotIn("evidence plan", door["confirm"])

    def test_the_full_reset_refiles_only_the_plan_through_the_door(self):
        full = self.out["full"]
        self.assertEqual([PLAN_URL], full["fetches"])
        self.assertEqual(BACK, full["asked"], "the reset filed a name the plan did not rebuild")
        self.assertEqual(BACK, full["owned"])
        self.assertNotIn("Decoy Item", full["owned"])
        self.assertNotIn("War Traveler", full["assign"])
        self.assertNotIn("Chance Guards", full["assign"])
        self.assertNotIn("Unread Thing", full["assign"])
        self.assertEqual("uni-armor", full["assign"]["Shako"])
        self.assertEqual("uni-armor", full["assign"]["Arachnid Mesh"])
        self.assertEqual("__keep", full["assign"]["Harlequin Crest"])
        self.assertEqual("__keep", full["assign"]["Lightning Sunder Charm"])
        shako = full["prov"]["Shako"]
        self.assertEqual("evidence", shako["by"])
        self.assertEqual("PROVEN", shako["tier"])
        self.assertEqual(12, shako["successes"])
        self.assertEqual(12, shako["trials"])
        self.assertFalse(shako["locked"])
        self.assertEqual(CELL["x"], shako["cells"][0]["x"])
        self.assertEqual(12, len(shako["sessions"]))
        self.assertEqual(12, len(shako["looks"]))
        self.assertTrue(full["prov"]["Arachnid Mesh"]["locked"])
        self.assertEqual("HARDENED", full["prov"]["Arachnid Mesh"]["tier"])
        self.assertEqual("kept kind", full["prov"]["Harlequin Crest"]["evidence"])
        self.assertEqual("kept", full["prov"]["Lightning Sunder Charm"]["source"])
        self.assertNotIn("War Traveler", full["prov"])
        self.assertTrue(full["keptSame"], "a kept store moved during the rebuild")
        self.assertTrue(full["journalGone"])
        self.assertIn("rebuilt 4", full["status"])
        self.assertIn("held 3", full["status"])
        self.assertIn("witness ledger is not cleared", full["confirm"])
        with io.open(self.path, "rb") as fh:
            self.assertEqual(self.before, fh.read())

    def test_an_unreadable_plan_is_unknown_and_files_nothing(self):
        bad = self.out["unread"]
        self.assertEqual([], bad["asked"])
        self.assertEqual([], bad["owned"])
        self.assertEqual({}, bad["assign"])
        self.assertIsNone(bad["receipt"].get("rebuilt"), bad["receipt"])
        self.assertIn("rebuilt UNKNOWN", bad["status"])
        self.assertNotIn("rebuilt 0", bad["status"])
        self.assertEqual(json.dumps(["Tal Rasha Armor"]), bad["sets"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the full reset asks a different plan than the evidence ledger",
        "file": "bible.html",
        "find": "http://127.0.0.1:17772/api/vault_rebuild_plan",
        "replace": "http://127.0.0.1:17772/api/vault_rebuild_plan_other",
        "matches": 1,
    },
    {
        "why": "the reset files the held rows too, so a watched item comes back",
        "file": "bible.html",
        "find": "    var names = [], failed = [], rows = plan.rebuilt;\n",
        "replace": "    var names = [], failed = [], rows = plan.rebuilt.concat(plan.held || []);\n",
        "matches": 1,
    },
    {
        "why": "the ledger reader stops asking rebuild_plan and calls every row proven",
        "file": "vault_evidence.py",
        "find": "    plan = rebuild_plan(items)\n",
        "replace": (
            "    plan = {\"ok\": True, \"rebuilt\": [{\"name\": it[\"name\"], \"tier\": \"PROVEN\", "
            "\"bound\": 1.0, \"successes\": it.get(\"successes\"), \"trials\": it.get(\"trials\"), "
            "\"locked\": False, \"why\": \"PROVEN\"} for it in items], \"held\": [], \"why\": \"\"}\n"
        ),
        "matches": 1,
    },
    {
        "why": "reading the witness ledger appends to it",
        "file": "vault_evidence.py",
        "find": "            blob = fh.read()\n    except Exception:\n        return _unread()\n",
        "replace": "            blob = fh.read(); io.open(path, \"ab\").write(b\"x\")\n    except Exception:\n        return _unread()\n",
        "matches": 1,
    },
    {
        "why": "the console route answers a private list instead of the evidence plan",
        "file": "control_app.py",
        "find": "    return VE.plan_from_ledger(p)\n",
        "replace": (
            "    return {\"ok\": True, \"rebuilt\": [{\"name\": \"War Traveler\", \"tier\": \"PROVEN\", "
            "\"why\": \"PROVEN\", \"locked\": False, \"bound\": 1, \"successes\": 12, \"trials\": 12}], "
            "\"held\": [], \"why\": \"\"}\n"
        ),
        "matches": 1,
    },
]
