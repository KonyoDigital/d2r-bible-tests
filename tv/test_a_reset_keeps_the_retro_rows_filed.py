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


def _served_plan(path):
    """The body POST /api/vault_rebuild_plan answers, from the real handler, as JSON bytes."""
    import control_app as CA
    got = {}
    h = CA.Handler.__new__(CA.Handler)
    h.path = "/api/vault_rebuild_plan"
    h.headers = {"Content-Length": "2"}
    h.rfile = io.BytesIO(b"{}")
    h._json = lambda code, obj: got.update(code=code, body=json.dumps(obj))
    with mock.patch.object(CA, "VAULT_LEDGER_PATH", path):
        h.do_POST()
    return got


BODY = r"""
var PLAN = __PLAN__;
var location = { hostname: '127.0.0.1' };
var FETCHES = [], ASKED = [], RESULT = {};
globalThis.fetch = function(url){
  FETCHES.push(String(url));
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
              rebuiltFailed: (window._vaultLastReset && window._vaultLastReset.rebuiltFailed) || null };
  FETCHES.length = 0; ASKED.length = 0; RESULT = {};
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


RED_PROOF = [
    {
        "why": "a retro row is held like any WATCHED row, so the reset un-files Radiance and the Cube",
        "file": "vault_evidence.py",
        "find": "        elif got[\"tier\"] == WATCHED and not kept and not retro:\n",
        "replace": "        elif got[\"tier\"] == WATCHED and not kept:\n",
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
        "why": "the filing drops the retro flag, so the board files it without saying why",
        "file": "../bible.html",
        "find": "      if (retroN) { rowF.flag = retroN; rowF.keepFiled = true; }\n",
        "replace": "",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
