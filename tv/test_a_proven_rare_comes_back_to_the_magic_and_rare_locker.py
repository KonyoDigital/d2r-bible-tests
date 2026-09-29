# -*- coding: utf-8 -*-
"""A PROVEN RARE (gold) OR MAGIC (blue) COMES BACK FROM A RESET INTO THE MAGIC & RARE LOCKER, PAINTED, AND TALLIED.

His ask 2026-09-28 (#51): magic and rare items get the same evidence chain as uniques — a rebuild
after a reset, the board line, the tallies.

MEASURED before the change (the shipped door, driven in node over a plan the real route served):
  · a plan row for a rolled name reached vaultFile's rebuild branch with no home, so the door asked
    suggestMule — whose last line routes a name nothing recognises to the weapons mule. A rare ring
    twelve visits had proven was filed under UNI-ARMOR (the law's stub; UNI-WEAPONS on his board);
  · the witness row it wrote carried no rarity, so _artRarity — the ONE name-colour resolver — had
    nothing to paint a rolled name with; the locker cell fell to _qStyle's 'unique' fallback: a rare
    in unique gold, the exact colour defect test_a_name_takes_its_colour_from_its_rarity exists for;
  · the receipt said "rebuilt 4" and nothing about what the four were.

WHAT THIS LAW DRIVES, end to end, no browser:
  1. the plan THE ROUTE SERVES — control_app.Handler.do_POST for /api/vault_rebuild_plan over a temp
     ledger (his vault_accum.json is never opened; the fixture is byte-identical after);
  2. the SHIPPED reset, door and colour resolver — cut from bible.html by the anchors the sibling
     reset laws use (never re-typed) and run in node over that served plan: a rare and a magic land in
     'magic-rare', their witness rows carry their rarity, _artRarity paints them (and its cache lets
     go of the '' it held before the filing), a row of UNKNOWN rarity routes exactly as before, the
     status line and the persisted receipt tally the rebuild by rarity — and the SAME receipt read by
     vault_evidence.reset_receipt says the same tally on the heart;
  3. a roster with no MAGIC & RARE locker: the door refuses the rare in words (no-home) and never
     guesses a mule, and the refusal is on the receipt.
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
from console_safe import enable; enable()

import test_a_vault_reset_clears_only_the_mules as RESET
import test_every_mule_filing_carries_its_witness as FILE
import test_a_reset_refiles_only_what_the_plan_says as REFILE
import test_a_reset_keeps_the_retro_rows_filed as RETRO
import vault_evidence as VE

NODE = shutil.which("node")
BIBLE = os.path.join(ROOT, "bible.html")
ART_FROM = "var _ARTRARITY_CACHE = {};\nfunction _artRarity(name){\n"
ART_TO = "\nwindow._artRarity = _artRarity;\n"
RARE, MAGIC, UNIQUE, BLANK, WATCHED = "Doom Grip", "Jade Ring of Frost", "Harlequin Crest", "Sad Thing", "Storm Loop"


def _looks(stem, n, quality=None):
    out = []
    for i in range(n):
        row = {"session": "s_%s_%02d" % (stem, i), "witness": "s_%s_%02d#0" % (stem, i),
               "frame": "%s_%02d.jpg" % (stem, i), "conf": 0.92, "lane": "stash"}
        if quality is not None:
            row["quality"] = quality
        out.append(row)
    return out


def _ledger():
    return {"owned": [
        {"name": UNIQUE, "lane": "stash", "kind": "item", "witnesses": _looks("crest", 12)},
        {"name": RARE, "lane": "stash", "kind": "item", "witnesses": _looks("doom", 12, "rare")},
        {"name": MAGIC, "lane": "stash", "kind": "item", "witnesses": _looks("jade", 12, "magic")},
        {"name": BLANK, "lane": "stash", "kind": "item", "witnesses": _looks("sad", 12)},
        {"name": WATCHED, "lane": "stash", "kind": "item", "witnesses": _looks("cg", 2, "rare")},
    ]}


def _art(s):
    """The ONE name-colour resolver, cut whole: its cache line through its window export."""
    assert s.count(ART_FROM) == 1 and s.count(ART_TO) == 1, "the _artRarity anchors are not unique (%d, %d)" % (
        s.count(ART_FROM), s.count(ART_TO))
    i = s.index(ART_FROM)
    return s[i:s.index(ART_TO, i) + len(ART_TO)]


# the stubs the refile law ships, with a roster that also knows the MAGIC & RARE locker (its id is what the
# door asks for); the second scenario takes the locker away. `function` declarations hoist, last wins.
LOCKER = r"""
var HAS_MAGIC_RARE = true;
function muleById(id){
  if (id === 'uni-armor') return { id: 'uni-armor', name: 'UNI-ARMOR' };
  if (id === 'magic-rare' && HAS_MAGIC_RARE) return { id: 'magic-rare', name: 'MAGIC & RARE' };
  return null;
}
"""

BODY = r"""
var PLAN = __PLAN__;
var location = { hostname: '127.0.0.1' };
var RESULT = {};
globalThis.fetch = function(url, opt){
  return Promise.resolve({ ok: true, json: function(){ return Promise.resolve(PLAN); } });
};
var _doorFile = window.vaultFile;
window.vaultFile = function(name, w, o){
  var r = _doorFile(name, w, o);
  RESULT[String(name)] = r ? { ok: !!r.ok, refused: r.refused || null, why: r.why || null, mule: r.mule || null } : null;
  return r;
};
function seed(){
  Object.keys(STORE).forEach(function(k){ delete STORE[k]; });
  Object.keys(_ARTRARITY_CACHE).forEach(function(k){ delete _ARTRARITY_CACHE[k]; });
  assign = {}; owned = new Set(); setPieces = new Set(); unknownReads = new Set();
  magicFinds = {}; copies = {}; multiKeep = {}; rwMade = {};
  STORE['d2r_muleAssign'] = '{}'; STORE['d2r_vaultProv'] = '{}'; STORE['d2r_owned'] = '[]'; STORE['d2r_setPieces'] = '[]';
  IDB['d2r_vault_fs/shotdir'] = { fake: true };
  UNLINKS = 0; CONFIRMS.length = 0; STATUS.length = 0; RESULT = {};
  window._vaultLastReset = undefined; ANSWER = true;
}
function take(){
  var prov = {}, receipt = null;
  try { prov = JSON.parse(STORE['d2r_vaultProv'] || '{}'); } catch (e) { prov = {}; }
  try { receipt = JSON.parse(STORE['d2r_vaultLastReset'] || 'null'); } catch (e) { receipt = null; }
  return { result: JSON.parse(JSON.stringify(RESULT)), assign: JSON.parse(JSON.stringify(assign)), prov: prov,
           status: STATUS.length ? STATUS[STATUS.length - 1] : '', receipt: receipt,
           paint: { rare: window._artRarity('__RARE__'), magic: window._artRarity('__MAGIC__'),
                    blank: window._artRarity('__BLANK__'), unique: window._artRarity('__UNIQUE__') } };
}
(async function(){
  var OUT = {};
  seed();
  // the resolver is asked BEFORE the reset, so its per-name cache holds '' for the rare — the filing must let go of it
  OUT.before = { rare: window._artRarity('__RARE__'), cached: Object.prototype.hasOwnProperty.call(_ARTRARITY_CACHE, '__RARE__') };
  await window.vaultClearHistory();
  OUT.withLocker = take();
  seed();
  HAS_MAGIC_RARE = false;
  await window.vaultClearHistory();
  OUT.noLocker = take();
  HAS_MAGIC_RARE = true;
  process.stdout.write(JSON.stringify(OUT));
})().catch(function(e){ process.stderr.write(String((e && e.stack) || e)); process.exit(3); });
"""


def _drive(plan_json):
    with io.open(BIBLE, encoding="utf-8") as fh:
        src = fh.read()
    body = (BODY.replace("__PLAN__", plan_json).replace("__RARE__", RARE).replace("__MAGIC__", MAGIC)
            .replace("__BLANK__", BLANK).replace("__UNIQUE__", UNIQUE))
    prog = RESET.HARNESS + REFILE.EXTRA + LOCKER + FILE._door(src) + RESET._pieces(src) + _art(src) + body
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("the shipped reset would not execute — UNKNOWN, not passing: %s"
                             % (r.stderr or r.stdout)[-900:])
    return json.loads(r.stdout)


class TheRouteServesTheRarityTheDoorFilesOn(unittest.TestCase):
    """No node needed: the plan the board receives carries what each rebuilt row IS."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="magic-rare-plan-")
        cls.path = os.path.join(cls.tmp, "vault_accum.json")
        cls.blob = json.dumps(_ledger()).encode("utf-8")
        with io.open(cls.path, "wb") as fh:
            fh.write(cls.blob)
        cls.served = RETRO._served_plan(cls.path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_served_plan_carries_rarity_on_every_row_and_writes_nothing(self):
        self.assertEqual(200, self.served.get("code"), self.served)
        plan = json.loads(self.served["body"])
        self.assertTrue(plan["ok"], plan.get("why"))
        rows = dict((r["name"], r) for r in plan["rebuilt"] + plan["held"])
        self.assertEqual("gold", rows[RARE].get("rarity"), rows[RARE])
        self.assertEqual("blue", rows[MAGIC].get("rarity"), rows[MAGIC])
        self.assertEqual("unique", rows[UNIQUE].get("rarity"), rows[UNIQUE])
        self.assertIsNone(rows[BLANK].get("rarity"), "a row with no quality was given a rarity")
        self.assertEqual([WATCHED], [r["name"] for r in plan["held"]])
        self.assertEqual("gold", rows[WATCHED].get("rarity"), "a HELD rare does not say what it is")
        with io.open(self.path, "rb") as fh:
            self.assertEqual(self.blob, fh.read(), "serving the plan wrote the witness ledger")


@unittest.skipIf(NODE is None, "node is absent — the shipped door was not driven, so this is not a pass")
class TheShippedResetFilesARareIntoTheMagicAndRareLocker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="magic-rare-node-")
        cls.path = os.path.join(cls.tmp, "vault_accum.json")
        with io.open(cls.path, "wb") as fh:
            fh.write(json.dumps(_ledger()).encode("utf-8"))
        cls.plan = RETRO._served_plan(cls.path)["body"]
        cls.out = _drive(cls.plan)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_a_proven_rare_and_magic_land_in_the_magic_and_rare_locker(self):
        got = self.out["withLocker"]
        for name in (RARE, MAGIC):
            res = got["result"].get(name)
            self.assertIsNotNone(res, "the reset never asked the door to file %s" % name)
            self.assertEqual({"ok": True, "refused": None}, {k: res[k] for k in ("ok", "refused")}, res)
            self.assertEqual("magic-rare", got["assign"].get(name),
                             "%s was filed to %r, not the MAGIC & RARE locker" % (name, got["assign"].get(name)))
        self.assertEqual("uni-armor", got["assign"].get(UNIQUE), "a unique stopped going where suggestMule sends it")
        self.assertEqual("uni-armor", got["assign"].get(BLANK), "a row of UNKNOWN rarity was routed differently")
        self.assertNotIn(WATCHED, got["assign"], "a WATCHED rare was filed back")
        self.assertEqual([], got["receipt"]["rebuiltFailed"], "the door refused a row the plan rebuilt")

    def test_the_witness_row_carries_the_rarity_and_the_resolver_paints_it(self):
        got = self.out["withLocker"]
        self.assertEqual(("gold", "PROVEN"), (got["prov"][RARE].get("rarity"), got["prov"][RARE].get("tier")), got["prov"][RARE])
        self.assertEqual("blue", got["prov"][MAGIC].get("rarity"))
        self.assertIsNone(got["prov"][BLANK].get("rarity"), "a row of UNKNOWN rarity was written with one")
        self.assertEqual({"rare": "rare", "magic": "magic", "blank": ""},
                         {k: got["paint"][k] for k in ("rare", "magic", "blank")},
                         "_artRarity does not paint a rebuilt rare/magic from its witness row (a blank stays uncoloured): %r"
                         % got["paint"])
        # the cache: '' was held for the rare BEFORE the filing and must not outlive it
        self.assertEqual({"rare": "", "cached": True}, self.out["before"],
                         "PREMISE: the resolver had cached '' for the rare before the reset")

    def test_the_status_line_and_the_receipt_tally_the_rebuild_by_rarity_and_the_heart_reads_it(self):
        got = self.out["withLocker"]
        self.assertIn("rebuilt 4 (1 unique · 1 rare (gold) · 1 magic (blue) · 1 rarity UNKNOWN)", got["status"],
                      "the status line does not tally by rarity: %s" % got["status"])
        tally = got["receipt"].get("rebuiltByRarity")
        self.assertEqual({"unique": 1, "gold": 1, "blue": 1, "unknown": 1}, tally, got["receipt"])
        # the SAME receipt, read by the heart's reader
        read = VE.reset_receipt(got["receipt"], got["receipt"]["keepsBefore"], got["receipt"]["keepsAfter"])
        self.assertEqual(tally, read["byRarity"])
        self.assertIn("rebuilt by rarity: 1 unique · 1 rare (gold) · 1 magic (blue) · 1 rarity UNKNOWN", read["why"])

    def test_without_a_magic_and_rare_locker_the_door_refuses_in_words_and_never_guesses(self):
        got = self.out["noLocker"]
        for name in (RARE, MAGIC):
            res = got["result"].get(name)
            self.assertEqual("no-home", res and res.get("refused"), "%s was not refused for lack of a locker: %r" % (name, res))
            self.assertIn("no MAGIC & RARE locker", res["why"])
            self.assertNotIn(name, got["assign"], "%s was guessed into %r" % (name, got["assign"].get(name)))
        self.assertEqual("uni-armor", got["assign"].get(UNIQUE))
        refused = [r["name"] for r in got["receipt"]["rebuiltFailed"]]
        self.assertEqual(sorted([RARE, MAGIC]), sorted(refused), "the refusals are not on the receipt")
        self.assertEqual({"unique": 1, "unknown": 1}, got["receipt"].get("rebuiltByRarity"))
        self.assertIn("could not be re-filed", got["status"])


RED_PROOF = [
    {
        "why": "#51 - the door no longer reads the plan row's rarity, so a proven rare is filed where suggestMule guesses",
        "file": "bible.html",
        "find": "      var rarR = (pr.rarity === 'blue' || pr.rarity === 'gold') ? String(pr.rarity) : '';\n",
        "replace": "      var rarR = '';\n",
        "matches": 1,
    },
    {
        "why": "#51 - with no MAGIC & RARE locker the rare falls through to suggestMule instead of a no-home refusal",
        "file": "bible.html",
        "find": "        if (!home && rarR) return { ok: false, refused: 'no-home',\n",
        "replace": "        if (false && rarR) return { ok: false, refused: 'no-home',\n",
        "matches": 1,
    },
    {
        "why": "#51 - the witness row drops the rarity, so nothing on the board can paint a rebuilt rare",
        "file": "bible.html",
        "find": "        rarity: (typeof pr.rarity === 'string' && pr.rarity) ? pr.rarity : null,\n",
        "replace": "        rarity: null,\n",
        "matches": 1,
    },
    {
        "why": "#51 - the name colour resolver stops asking the witness row, so a rebuilt rare paints as unique gold again",
        "file": "bible.html",
        "find": "        r = ({ blue: 'magic', gold: 'rare', unique: 'unique', set: 'set', white: 'basic' })[_pq] || '';\n",
        "replace": "        r = '';\n",
        "matches": 1,
    },
    {
        "why": "#51 - a witness write no longer empties the resolver's cache, so the '' cached before the filing paints for ever",
        "file": "bible.html",
        "find": "    try { if (typeof _ARTRARITY_CACHE === 'object' && _ARTRARITY_CACHE) Object.keys(_ARTRARITY_CACHE).forEach(function(k){ delete _ARTRARITY_CACHE[k]; }); } catch (e) {}\n",
        "replace": "    /* cache kept */\n",
        "matches": 1,
    },
    {
        "why": "#51 - the rebuild stops tallying by rarity, so the status line and the receipt say nothing about what came back",
        "file": "bible.html",
        "find": "        byRar[rk] = (byRar[rk] || 0) + 1;\n",
        "replace": "        byRar[rk] = 0;\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
