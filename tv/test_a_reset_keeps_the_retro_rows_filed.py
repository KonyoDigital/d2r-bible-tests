# -*- coding: utf-8 -*-
"""A full vault reset keeps a retro-flagged item FILED, at its true tier, on every reset.

HIS RULING 2026-09-28 (§34.2), his words: "Keep filed, flag 'retro: WATCHED'".

THE DEFECT (Ledger P0 review, finding 1, reproduced): the P0 build computed the retro flags and
served them on POST /api/vault_rebuild_plan as `plan.retro` — a field the board's reset never
reads. bible.html's _vaultRefileFromPlan files `plan.rebuilt` and nothing else, and Radiance and
the Horadric Cube (2 visits each, WATCHED under the visit math) sat in `plan.held`. So his next
"Reset vault" would have UN-FILED both, which is the one thing his ruling forbids. Two halves each
correct, never joined. [[the-unjoined-end]]

WHAT THIS LAW DRIVES, end to end, with no browser:
  1. the plan THE ROUTE SERVES — control_app.Handler.do_POST for /api/vault_rebuild_plan, called
     in-process with VAULT_LEDGER_PATH pointed at a seeded fixture, JSON round-tripped the way the
     board receives it;
  2. the SHIPPED reset and the SHIPPED door — cut from bible.html by the same anchors the reset
     law uses (never re-typed) and run in node over that served plan, TWICE, because "keep filed"
     has to survive the next reset as well as this one.

2026-09-28 (Ledger fix round 2, finding B, reproduced): the plan promised keepFiled for EVERY
retro-flagged row, but the door still asked two qualifying looks — so a retro item with ONE visit
was refused and un-filed with no message, and R.rebuiltFailed was written and read by nothing. HIS
RULING §34.2: "Keep filed, flag 'retro: WATCHED'". Now the door keeps a keepFiled retro row on ONE
qualifying look; a flagged row NO visit saw is held by the plan with its why and never promised
keepFiled; and every door refusal is SAID — in the status sentence, in the receipt as
{name, refused, why}, and on the doctor's reset row, which reads that receipt.

Fixtures only. His vault_accum.json is never opened; the fixture ledger is byte-identical after.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except ImportError:
    _enable = None

import test_a_vault_reset_clears_only_the_mules as RESET
import test_every_mule_filing_carries_its_witness as FILE
import test_a_reset_refiles_only_what_the_plan_says as REFILE
import vault_evidence as VE

NODE = shutil.which("node")
FLAGGED = ["Radiance", "Horadric Cube"]


def _still(session, bucket, n, prefix, conf=0.92):
    """n frames of ONE held screen: one session, one re-look bucket."""
    return [{"session": session, "witness": "%s#%d" % (session, bucket),
             "frame": "%s_%03d.jpg" % (prefix, i), "conf": conf, "lane": "stash"}
            for i in range(n)]


def _ledger():
    shako = []
    for i in range(12):
        shako += _still("s_shako_%02d" % i, 0, 1, "shako%02d" % i)
    return {"owned": [
        # his real shapes, measured read-only 2026-09-28: 103 frames from 2 visits, 21 from 2
        {"name": "Radiance", "lane": "stash", "kind": "item",
         "witnesses": _still("s_rad_A", 0, 1, "radA") + _still("s_rad_B", 0, 102, "radB")},
        {"name": "Horadric Cube", "lane": "stash", "kind": "item",
         "witnesses": _still("s_cube_A", 0, 20, "cubeA") + _still("s_cube_B", 0, 1, "cubeB")},
        {"name": "Shako", "lane": "stash", "kind": "item", "witnesses": shako},
        # 2 visits, 2 frames: WATCHED by BOTH maths, so never flagged — and never filed back
        {"name": "Chance Guards", "lane": "stash", "kind": "item",
         "witnesses": _still("s_cg_A", 0, 1, "cgA") + _still("s_cg_B", 0, 1, "cgB")},
    ]}


def _served_plan(path, body=b"{}"):
    """The body POST /api/vault_rebuild_plan answers, from the real handler, as JSON bytes.
    `body` is what the board POSTs — since #41 rank 1 the reset sends {recorded: its own filings}."""
    import control_app as CA
    got = {}
    h = CA.Handler.__new__(CA.Handler)
    h.path = "/api/vault_rebuild_plan"
    h.headers = {"Content-Length": str(len(body))}
    h.rfile = io.BytesIO(body)
    h._json = lambda code, obj: got.update(code=code, body=json.dumps(obj))
    with mock.patch.object(CA, "VAULT_LEDGER_PATH", path):
        h.do_POST()
    return got


BODY = r"""
var PLAN = __PLAN__;
var location = { hostname: '127.0.0.1' };
var FETCHES = [], ASKED = [], RESULT = {}, BODIES = [];
globalThis.fetch = function(url, opt){
  FETCHES.push(String(url));
  BODIES.push(opt && opt.body ? JSON.parse(opt.body) : null);
  return Promise.resolve({ ok: true, json: function(){ return Promise.resolve(PLAN); } });
};
var _doorFile = window.vaultFile;
window.vaultFile = function(name, w, o){
  ASKED.push(String(name));
  var r = _doorFile(name, w, o);
  RESULT[String(name)] = r ? { ok: !!r.ok, refused: r.refused || null, why: r.why || null } : null;
  return r;
};
function seed(){
  Object.keys(STORE).forEach(function(k){ delete STORE[k]; });
  assign = { 'Radiance': 'uni-armor', 'Horadric Cube': 'uni-armor' };
  owned = new Set(['Radiance', 'Horadric Cube']);
  setPieces = new Set(); unknownReads = new Set();
  magicFinds = {}; copies = {}; multiKeep = {}; rwMade = {};
  STORE['d2r_muleAssign'] = JSON.stringify(assign);
  STORE['d2r_vaultProv'] = JSON.stringify({ 'Radiance': { mule: 'uni-armor', source: 'stash', by: 'evidence', tier: 'HARDENED' },
                                            'Horadric Cube': { mule: 'uni-armor', source: 'stash', by: 'evidence', tier: 'HARDENED' } });
  STORE['d2r_owned'] = JSON.stringify(Array.from(owned));
  STORE['d2r_setPieces'] = '[]';
  IDB['d2r_vault_fs/shotdir'] = { fake: true };
  UNLINKS = 0; CONFIRMS.length = 0; STATUS.length = 0;
  window._vaultLastReset = undefined;
  ANSWER = true;
}
function take(){
  var prov = {};
  try { prov = JSON.parse(STORE['d2r_vaultProv'] || '{}'); } catch (e) { prov = {}; }
  var out = { fetches: FETCHES.slice(), asked: ASKED.slice(), result: JSON.parse(JSON.stringify(RESULT)),
              assign: JSON.parse(JSON.stringify(assign)), owned: Array.from(owned), prov: prov,
              status: STATUS.length ? STATUS[STATUS.length - 1] : '',
              rebuiltFailed: (window._vaultLastReset && window._vaultLastReset.rebuiltFailed) || null,
              bodies: BODIES.slice(), recorded: (window._vaultLastReset && window._vaultLastReset.recorded) || null };
  FETCHES.length = 0; ASKED.length = 0; RESULT = {}; BODIES.length = 0;
  return out;
}
(async function(){
  var OUT = {};
  seed();
  await window.vaultClearHistory();
  OUT.first = take();
  await window.vaultClearHistory();       // the NEXT reset, on the board the first one left
  OUT.second = take();
  process.stdout.write(JSON.stringify(OUT));
})().catch(function(e){ process.stderr.write(String((e && e.stack) || e)); process.exit(3); });
"""


def _drive(plan_json):
    with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
        src = fh.read()
    prog = (RESET.HARNESS + REFILE.EXTRA + FILE._door(src) + RESET._pieces(src)
            + BODY.replace("__PLAN__", plan_json))
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("the shipped reset would not execute — UNKNOWN, not passing: %s"
                             % (r.stderr or r.stdout)[-900:])
    return json.loads(r.stdout)


class TheRouteServesTheFlaggedRowsWhereTheResetReads(unittest.TestCase):
    """No node needed: the field the reset reads is `rebuilt`, and it must carry both."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="retro-kept-")
        cls.path = os.path.join(cls.tmp, "vault_accum.json")
        cls.blob = json.dumps(_ledger()).encode("utf-8")
        with io.open(cls.path, "wb") as fh:
            fh.write(cls.blob)
        cls.served = _served_plan(cls.path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_route_answers_and_writes_nothing(self):
        self.assertEqual(200, self.served.get("code"), self.served)
        with io.open(self.path, "rb") as fh:
            self.assertEqual(self.blob, fh.read(), "serving the plan wrote the witness ledger")

    def test_rebuilt_carries_both_flagged_items_at_their_true_tier(self):
        plan = json.loads(self.served["body"])
        self.assertTrue(plan["ok"], plan.get("why"))
        by = dict((r["name"], r) for r in plan["rebuilt"])
        for name in FLAGGED:
            self.assertIn(name, by, "%s is flagged retro but not in `rebuilt` — the field the "
                                    "board's reset files from — so a reset UN-FILES it" % name)
            row = by[name]
            self.assertEqual(VE.WATCHED, row["tier"], "a retro row must come back at its TRUE tier")
            self.assertIs(False, row["locked"])
            self.assertEqual("retro: WATCHED", row["flag"])
            self.assertIs(True, row["keepFiled"])
            self.assertEqual("kept filed by his ruling (§34.2)", row["why"])
            self.assertEqual({"successes": 2, "trials": 2},
                             {"successes": row["successes"], "trials": row["trials"]})
        self.assertEqual(set(FLAGGED), set(plan["retro"]["names"]),
                         "the summary and the rows disagree about which items are flagged")
        held = [r["name"] for r in plan["held"]]
        self.assertEqual(["Chance Guards"], held,
                         "an unflagged WATCHED item came back, or a flagged one stayed held")
        self.assertNotIn("flag", by["Shako"], "an honestly PROVEN item carries a retro flag")


@unittest.skipIf(NODE is None, "node is absent — the shipped door was not driven, so this is not a pass")
class TheShippedResetKeepsThemFiled(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="retro-kept-node-")
        cls.path = os.path.join(cls.tmp, "vault_accum.json")
        with io.open(cls.path, "wb") as fh:
            fh.write(json.dumps(_ledger()).encode("utf-8"))
        served = _served_plan(cls.path)
        cls.out = _drive(served["body"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _filed(self, run):
        got = self.out[run]
        for name in FLAGGED:
            res = got["result"].get(name)
            self.assertIsNotNone(res, "the %s reset never asked the door to file %s — it was not in "
                                      "the plan's `rebuilt`, so it is UN-FILED" % (run, name))
            self.assertEqual({"ok": True, "refused": None}, {k: res[k] for k in ("ok", "refused")},
                             "the board's door refused %s on the %s reset: %r" % (name, run, res))
            self.assertEqual("uni-armor", got["assign"].get(name),
                             "%s was UN-FILED by the %s reset, against his ruling" % (name, run))
            self.assertIn(name, got["owned"])
            prov = got["prov"][name]
            self.assertEqual("WATCHED", prov["tier"], "the filing claims a tier its visits never earned")
            self.assertEqual("retro: WATCHED", prov.get("flag"),
                             "the filing lost the retro flag, so the board cannot show it")
            self.assertIs(True, prov.get("keepFiled"))
            self.assertIs(False, prov["locked"])
            self.assertEqual("evidence", prov["by"])
        self.assertNotIn("Chance Guards", got["assign"], "an unflagged WATCHED item was filed back")
        self.assertEqual("uni-armor", got["assign"].get("Shako"))
        self.assertEqual([], got["rebuiltFailed"] or [], "the door refused a row the plan rebuilt")

    def test_the_first_reset_files_both_back_through_the_door(self):
        self._filed("first")
        self.assertIn("rebuilt 3", self.out["first"]["status"])

    def test_the_next_reset_keeps_them_filed_too(self):
        self._filed("second")

    def test_the_reset_asks_the_plan_with_the_filings_the_board_held_before_its_clears(self):
        """#41 rank 1: the ask carried '{}', so the plan derived 'filed before' from surplus frames. The reset now reads
        its own filings BEFORE the clears (the mule map's names, the witness rows' tiers) and POSTs them as `recorded`."""
        first = self.out["first"]
        self.assertEqual(1, len(first["bodies"]), first["bodies"])
        rec = (first["bodies"][0] or {}).get("recorded")
        self.assertEqual({"Radiance": "HARDENED", "Horadric Cube": "HARDENED"}, rec,
                         "the ask does not carry the board's own filings (read before the clears): %r" % (rec,))
        self.assertEqual(rec, first["recorded"], "the receipt does not keep what was posted")
        second = self.out["second"]
        rec2 = (second["bodies"][0] or {}).get("recorded")
        self.assertEqual({"Radiance": "WATCHED", "Horadric Cube": "WATCHED", "Shako": "PROVEN"}, rec2,
                         "the second reset did not post what the first one filed back")


class TheKeepIsPromisedOnlyToARowTheBoardHeld(unittest.TestCase):
    """#41 rank 1 (2026-09-29): with the board's filings in hand, the plan keeps a retro row filed only where the board
    had filed it. His board has held nothing since his 09-27 reset — a plan asked by that board holds Radiance and the
    Cube like any WATCHED row instead of promising keepFiled on the 1-look bar. Without `recorded` the frame math still
    decides, as before, and the plan says which."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="retro-recorded-")
        cls.path = os.path.join(cls.tmp, "vault_accum.json")
        cls.blob = json.dumps(_ledger()).encode("utf-8")
        with io.open(cls.path, "wb") as fh:
            fh.write(cls.blob)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _plan(self, body):
        got = _served_plan(self.path, body=json.dumps(body).encode("utf-8"))
        self.assertEqual(200, got.get("code"), got)
        return json.loads(got["body"])

    def test_an_empty_board_holds_the_retro_rows_and_files_only_what_is_proven(self):
        plan = self._plan({"recorded": {}})
        self.assertTrue(plan["ok"], plan.get("why"))
        self.assertEqual("board", plan["recordedBy"])
        self.assertEqual(["Shako"], [r["name"] for r in plan["rebuilt"]], "a board that holds nothing was promised keepFiled retro rows")
        held = dict((r["name"], r) for r in plan["held"])
        for name in FLAGGED:
            self.assertIn(name, held, "%s was rebuilt for a board that never filed it" % name)
            self.assertEqual("below the proven bar", held[name]["why"])
            self.assertNotIn("flag", held[name])
        self.assertEqual([], plan["retro"]["names"])

    def test_a_board_that_filed_them_keeps_them_and_the_recorded_tier_is_the_one_compared(self):
        plan = self._plan({"recorded": {"Radiance": "HARDENED", "Horadric Cube": "filed"}})
        by = dict((r["name"], r) for r in plan["rebuilt"])
        for name in FLAGGED:
            self.assertIn(name, by, "%s was filed on this board and is no longer kept" % name)
            self.assertIs(True, by[name]["keepFiled"])
            self.assertEqual("retro: WATCHED", by[name]["flag"])
        rows = dict((r["name"], r) for r in plan["retro"]["rows"])
        self.assertEqual(("HARDENED", "board"), (rows["Radiance"]["recordedTier"], rows["Radiance"]["recordedBy"]),
                         "the board's own recorded tier is not the one compared")
        self.assertEqual("frames", rows["Horadric Cube"]["recordedBy"], "a filing with no tier falls back to the frame math for its recorded tier")

    def test_without_recorded_the_frame_math_still_decides_and_says_so(self):
        plan = self._plan({})
        self.assertEqual("frames", plan["recordedBy"])
        self.assertEqual(set(FLAGGED), set(plan["retro"]["names"]))
        unread = self._plan({"recorded": "not a map"})
        self.assertFalse(unread["ok"], "an unreadable `recorded` was read as an empty board")
        self.assertIn("UNKNOWN", unread["why"])
        self.assertEqual([], unread["rebuilt"])

    def test_the_route_wrote_nothing(self):
        with io.open(self.path, "rb") as fh:
            self.assertEqual(self.blob, fh.read(), "serving the plan wrote the witness ledger")


ONE_VISIT = "Arkaine's Valor"
NO_VISIT = "Ghost Charm"


def _unplaced(n, prefix, conf=0.92):
    """n frames that each saw the item but name NO visit (no session, no witness id)."""
    return [{"frame": "%s_%03d.jpg" % (prefix, i), "conf": conf, "lane": "stash"} for i in range(n)]


def _ledger_b():
    doc = _ledger()
    doc["owned"] += [
        # ONE visit held still for 25 frames: HARDENED by frames, WATCHED 1/1 by visits
        {"name": ONE_VISIT, "lane": "stash", "kind": "item",
         "witnesses": _still("s_av_A", 0, 25, "avA")},
        # 15 frames that saw it and name no visit: PROVEN by frames, 0 qualifying visits
        {"name": NO_VISIT, "lane": "stash", "kind": "item", "witnesses": _unplaced(15, "gc")},
    ]
    return doc


BODY_B = r"""
var PLAN = __PLAN__;
var location = { hostname: '127.0.0.1' };
globalThis.fetch = function(url){
  return Promise.resolve({ ok: true, json: function(){ return Promise.resolve(PLAN); } });
};
var KEEPS = ['d2r_setPieces', 'd2r_foundLog', 'd2r_rwMade'];
function seed(){
  Object.keys(STORE).forEach(function(k){ delete STORE[k]; });
  var was = ['Radiance', 'Horadric Cube', "Arkaine's Valor", 'Ghost Charm'];
  assign = {}; was.forEach(function(n){ assign[n] = 'uni-armor'; });
  owned = new Set(was);
  setPieces = new Set(['Tal Rasha Armor']); unknownReads = new Set();
  magicFinds = {}; copies = {}; multiKeep = {}; rwMade = { Spirit: 1 };
  STORE['d2r_muleAssign'] = JSON.stringify(assign);
  var pv = {}; was.forEach(function(n){ pv[n] = { mule: 'uni-armor', source: 'stash', by: 'evidence', tier: 'HARDENED' }; });
  STORE['d2r_vaultProv'] = JSON.stringify(pv);
  STORE['d2r_owned'] = JSON.stringify(was);
  STORE['d2r_setPieces'] = JSON.stringify(['Tal Rasha Armor']);
  STORE['d2r_foundLog'] = JSON.stringify({ 'Radiance': '2026-09-01' });
  STORE['d2r_rwMade'] = JSON.stringify(rwMade);
  IDB['d2r_vault_fs/shotdir'] = { fake: true };
  UNLINKS = 0; CONFIRMS.length = 0; STATUS.length = 0;
  window._vaultLastReset = undefined;
  ANSWER = true;
}
function keeps(){ var o = {}; KEEPS.forEach(function(k){ o[k] = STORE[k] === undefined ? null : STORE[k]; }); return o; }
async function run(lock){
  seed();
  Object.keys(LOCKS).forEach(function(k){ delete LOCKS[k]; });
  if (lock) LOCKS[lock] = 'equipment';
  var before = keeps();
  await window.vaultClearHistory();
  var prov = {};
  try { prov = JSON.parse(STORE['d2r_vaultProv'] || '{}'); } catch (e) { prov = {}; }
  return { assign: JSON.parse(JSON.stringify(assign)), prov: prov,
           status: STATUS.length ? STATUS[STATUS.length - 1] : '',
           receipt: JSON.parse(JSON.stringify(window._vaultLastReset || null)),
           before: before, after: keeps() };
}
(async function(){
  var OUT = {};
  OUT.plain = await run(null);
  OUT.locked = await run('Shako');     // his MAIN carries Shako: the door must refuse to put it on a mule
  process.stdout.write(JSON.stringify(OUT));
})().catch(function(e){ process.stderr.write(String((e && e.stack) || e)); process.exit(3); });
"""


def _drive_b(plan_json):
    with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
        src = fh.read()
    prog = (RESET.HARNESS + REFILE.EXTRA + FILE._door(src) + RESET._pieces(src)
            + BODY_B.replace("__PLAN__", plan_json))
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("the shipped reset would not execute — UNKNOWN, not passing: %s"
                             % (r.stderr or r.stdout)[-900:])
    return json.loads(r.stdout)


class TheKeepPromiseIsOneTheDoorCanKeep(unittest.TestCase):
    """Finding B, plan half: a retro row one visit saw is kept filed; one NO visit saw is held."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="retro-keep-b-")
        cls.path = os.path.join(cls.tmp, "vault_accum.json")
        cls.blob = json.dumps(_ledger_b()).encode("utf-8")
        with io.open(cls.path, "wb") as fh:
            fh.write(cls.blob)
        cls.plan = json.loads(_served_plan(cls.path)["body"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_a_retro_row_with_one_visit_is_promised_keep_filed(self):
        by = dict((r["name"], r) for r in self.plan["rebuilt"])
        self.assertIn(ONE_VISIT, by, "a retro row one visit saw was not rebuilt")
        row = by[ONE_VISIT]
        self.assertEqual(("WATCHED", 1, 1, True, "retro: WATCHED"),
                         (row["tier"], row["successes"], row["trials"], row["keepFiled"], row["flag"]))
        self.assertEqual(1, len(row["witness"]["sessions"]),
                         "baseline: the door is handed exactly ONE qualifying look for this row")

    def test_a_retro_row_no_visit_saw_is_held_with_its_why_never_promised(self):
        rebuilt = [r["name"] for r in self.plan["rebuilt"]]
        self.assertNotIn(NO_VISIT, rebuilt,
                         "a flagged row with ZERO qualifying looks was promised keepFiled — a promise "
                         "the door cannot keep, so the reset un-files it with no message")
        held = dict((r["name"], r) for r in self.plan["held"])
        self.assertIn(NO_VISIT, held)
        row = held[NO_VISIT]
        self.assertEqual(VE.RETRO_NO_LOOK_WHY, row["why"])
        self.assertEqual("retro: WATCHED", row.get("flag"), "the held row lost the flag that explains it")
        self.assertIs(False, row.get("keepFiled"))
        summary = dict((r["name"], r) for r in self.plan["retro"]["rows"])
        self.assertIs(False, summary[NO_VISIT]["keepFiled"],
                      "the retro summary still promises keepFiled for a row no visit saw")
        self.assertIs(True, summary[ONE_VISIT]["keepFiled"])
        self.assertEqual([NO_VISIT], self.plan["retro"]["heldNames"])
        self.assertIn("held — no visit saw it: %s" % NO_VISIT, self.plan["retro"]["why"])

    def test_the_plan_wrote_nothing(self):
        with io.open(self.path, "rb") as fh:
            self.assertEqual(self.blob, fh.read(), "serving the plan wrote the witness ledger")


@unittest.skipIf(NODE is None, "node is absent — the shipped door was not driven, so this is not a pass")
class EveryDoorRefusalIsSaid(unittest.TestCase):
    """Finding B, door half: the one-visit row is filed; a refusal is named in the sentence,
    in the receipt, and on the doctor's reset row, which reads that receipt."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="retro-keep-b-node-")
        cls.path = os.path.join(cls.tmp, "vault_accum.json")
        with io.open(cls.path, "wb") as fh:
            fh.write(json.dumps(_ledger_b()).encode("utf-8"))
        cls.out = _drive_b(_served_plan(cls.path)["body"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_door_keeps_a_retro_row_on_one_look(self):
        got = self.out["plain"]
        failed = got["receipt"]["rebuiltFailed"]
        self.assertEqual([], failed, "the door refused a row the plan rebuilt: %r" % (failed,))
        self.assertEqual("uni-armor", got["assign"].get(ONE_VISIT),
                         "%s (one visit, retro: WATCHED, keepFiled) was UN-FILED by the reset" % ONE_VISIT)
        prov = got["prov"][ONE_VISIT]
        self.assertEqual(("WATCHED", "retro: WATCHED", True),
                         (prov["tier"], prov.get("flag"), prov.get("keepFiled")))
        self.assertEqual(1, len(prov["looks"]), "the filing does not carry the one look it stands on")
        for name in FLAGGED:
            self.assertEqual("uni-armor", got["assign"].get(name))
        self.assertNotIn(NO_VISIT, got["assign"], "a row no visit saw was filed with no look to stand on")
        self.assertNotIn("could not be re-filed", got["status"])

    def test_an_unflagged_row_still_needs_two_looks(self):
        # the lowered bar is ONLY for a keepFiled retro row: the same one look without the flag is refused
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            src = fh.read()
        prog = (FILE.HARNESS + REFILE.EXTRA + FILE._door(src) + r"""
var one = { lane: 'stash', sessions: [{ witness: 's#0', session: 's', frame: 'f.jpg', conf: 0.9 }] };
var row = { name: 'X', tier: 'WATCHED', why: 'kept filed by his ruling (§34.2)', successes: 1, trials: 1 };
var proven = window.vaultFile('X', one, { rebuild: true, plan: Object.assign({}, row, { tier: 'PROVEN', why: 'PROVEN' }), mule: 'uni-armor' });
var plain = window.vaultFile('X', one, { rebuild: true, plan: row, mule: 'uni-armor' });
var forged = window.vaultFile('X', one, { rebuild: true, plan: Object.assign({}, row, { flag: 'retro: WATCHED' }), mule: 'uni-armor' });
var direct = window._vaultWitnessCheck(one, 0);
var retroBar = window._vaultWitnessCheck(one, 1);
process.stdout.write(JSON.stringify({ proven: proven, plain: plain, forged: forged, direct: direct, retroBar: retroBar }));
""")
        r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
        self.assertEqual(0, r.returncode, r.stderr[-600:])
        got = json.loads(r.stdout)
        self.assertIs(True, got["retroBar"]["ok"], "baseline: the retro keep bar admits this one look")
        self.assertEqual("witness", got["proven"].get("refused"),
                         "an unflagged PROVEN row was filed on ONE look — the two-look rule was lowered "
                         "for every rebuild, not only for his keep-filed retro rows: %r" % (got["proven"],))
        self.assertIn("needs 2", got["proven"].get("why") or "")
        self.assertEqual("plan", got["plain"].get("refused"), "a WATCHED row with no retro flag was filed")
        self.assertEqual("plan", got["forged"].get("refused"),
                         "a flag without keepFiled lowered the bar — only the plan's own promise may")
        self.assertIs(False, got["direct"]["ok"], "a caller lowered the witness bar to a number of its own")

    def test_a_refused_rebuild_is_named_in_the_sentence(self):
        got = self.out["locked"]
        self.assertNotIn("Shako", got["assign"], "baseline: the door refused Shako (his MAIN carries it)")
        self.assertIn("1 could not be re-filed: Shako (", got["status"],
                      "the door refused a plan row and the status line said nothing: %s" % got["status"])
        self.assertIn("locked to your MAIN", got["status"], "the door's own reason was not said")

    def test_a_refused_rebuild_is_carried_by_the_receipt_the_doctor_reads(self):
        import console_doctor as CD
        got = self.out["locked"]
        failed = got["receipt"]["rebuiltFailed"]
        self.assertEqual(1, len(failed))
        self.assertEqual(("Shako", "locked"), (failed[0]["name"], failed[0]["refused"]),
                         "the receipt carries a bare name with no code: %r" % (failed,))
        self.assertIn("locked to your MAIN", failed[0]["why"])
        # the JOIN: the receipt the SHIPPED reset wrote, read by the doctor's own reset row
        st, why = CD._check_the_vault_reset(got["receipt"], got["before"], got["after"])
        self.assertEqual(CD.MISSING, st, "a refused rebuild read %s on the heart: %s" % (st, why))
        self.assertIn("Shako", why)
        self.assertIn("locked to your MAIN", why)
        st0, why0 = CD._check_the_vault_reset(self.out["plain"]["receipt"], self.out["plain"]["before"],
                                              self.out["plain"]["after"])
        self.assertEqual(CD.OK, st0, why0)
        self.assertIn("refused 0", why0)


RED_PROOF = [
    {
        "why": "a retro row is held like any WATCHED row, so the reset un-files Radiance and the Cube",
        "file": "vault_evidence.py",
        "find": "        elif got[\"tier\"] == WATCHED and not kept and not retro:\n",
        "replace": "        elif got[\"tier\"] == WATCHED and not kept:\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 1 - the plan flags a retro row the board never filed, so an empty board is promised keepFiled again",
        "file": "vault_evidence.py",
        "find": "            flagged = (_retro_row(name, measured, held_tiers.get(name))\n                       if (held_names is None or name in held_names) else None)\n",
        "replace": "            flagged = _retro_row(name, measured)\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 1 - the reset stops reading its own filings before the clears, so the ask carries nothing",
        "file": "../bible.html",
        "find": "    R.recorded = _vaultRecordedFilings();\n",
        "replace": "    R.recorded = null;\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 1 - the route drops the board's filings from the ask, so the frame math decides for every board",
        "file": "control_app.py",
        "find": "            self._json(200, vault_rebuild_plan(recorded=body.get(\"recorded\") if isinstance(body, dict) else None))\n",
        "replace": "            self._json(200, vault_rebuild_plan())\n",
        "matches": 1,
    },
    {
        "why": "the flag never reaches `rebuilt`, only the summary the board never reads",
        "file": "vault_evidence.py",
        "find": "                item[\"retro\"] = flagged[\"flag\"]\n",
        "replace": "                item[\"retro\"] = \"\"\n",
        "matches": 1,
    },
    {
        "why": "the board's door refuses a WATCHED plan row even when it carries his keep-filed flag",
        "file": "../bible.html",
        "find": "      if (tierN !== 'PROVEN' && tierN !== 'HARDENED' && whyN !== 'kept kind' && !retroN)\n",
        "replace": "      if (tierN !== 'PROVEN' && tierN !== 'HARDENED' && whyN !== 'kept kind')\n",
        "matches": 1,
    },
    {
        "why": "the door asks two looks of a keepFiled retro row again, so a one-visit retro item is refused and un-filed (finding B)",
        "file": "../bible.html",
        "find": "        var wcR = window._vaultWitnessCheck(w, retroN ? VAULT_RETRO_KEEP_MIN : VAULT_WITNESS_MIN);\n",
        "replace": "        var wcR = window._vaultWitnessCheck(w);\n",
        "matches": 1,
    },
    {
        "why": "the witness check takes any bar a caller names, so the two-look rule can be lowered by anyone (finding B)",
        "file": "../bible.html",
        "find": "    var need = (minLooks === VAULT_RETRO_KEEP_MIN) ? VAULT_RETRO_KEEP_MIN : VAULT_WITNESS_MIN;\n",
        "replace": "    var need = (typeof minLooks === 'number') ? minLooks : VAULT_WITNESS_MIN;\n",
        "matches": 1,
    },
    {
        "why": "the door lowers the bar for EVERY rebuild row, not only a keepFiled retro row (finding B)",
        "file": "../bible.html",
        "find": "        var wcR = window._vaultWitnessCheck(w, retroN ? VAULT_RETRO_KEEP_MIN : VAULT_WITNESS_MIN);\n",
        "replace": "        var wcR = window._vaultWitnessCheck(w, VAULT_RETRO_KEEP_MIN);\n",
        "matches": 1,
    },
    {
        "why": "the plan promises keepFiled to a retro row no visit saw, a promise the door cannot keep (finding B)",
        "file": "vault_evidence.py",
        "find": "        elif got[\"tier\"] == WATCHED and not kept and got[\"successes\"] < RETRO_KEEP_MIN_LOOKS:\n",
        "replace": "        elif False:\n",
        "matches": 1,
    },
    {
        "why": "the retro summary promises keepFiled to every flagged row again (finding B)",
        "file": "vault_evidence.py",
        "find": "    keep = honest[\"successes\"] >= RETRO_KEEP_MIN_LOOKS\n",
        "replace": "    keep = True\n",
        "matches": 1,
    },
    {
        "why": "a refused rebuild is a bare name again, with no code and no reason for anyone to read (finding B)",
        "file": "../bible.html",
        "find": "      else failed.push({ name: String(row.name), refused: (filed && filed.refused)",
        "replace": "      else failed.push(String(row.name)); if (0) failed.push({ name: String(row.name), refused: (filed && filed.refused)",
        "matches": 1,
    },
    {
        "why": "the status sentence stops naming the rows the door refused (finding B)",
        "file": "../bible.html",
        "find": "      if (rf.length) bits.push('⚠ ' + rf.length + ' could not be re-filed: '",
        "replace": "      if (false) bits.push('⚠ ' + rf.length + ' could not be re-filed: '",
        "matches": 1,
    },
    {
        "why": "the filing drops the retro flag, so the board files it without saying why",
        "file": "../bible.html",
        "find": "      if (retroN) { rowF.flag = retroN; rowF.keepFiled = true; }\n",
        "replace": "",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
