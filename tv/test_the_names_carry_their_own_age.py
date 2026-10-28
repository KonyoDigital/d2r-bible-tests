# -*- coding: utf-8 -*-
"""#200 (REG-2745) - THE CHRONICLE'S NAMES CARRY THEIR OWN AGE, AND THAT AGE IS NEVER A HASH INPUT.

A PC's chronicle section has one asOf: when its counts were BANKED (the board tally). Its name rows are read fresh from
the found stores at publish. So a viewer dated fresh names by old counts. The section now carries rowsAsOf (when the rows
were read) beside its rows, both shapers keep it (roster_publish.section_of on the PC, roster.js shapeSection on the
worker), and both hashes leave it out exactly as they leave asOf out - so a publish is never triggered by the stamp
alone, and an older worker that drops the key computes the same hash. The reader dates it (rowsAge) and the shadow's
chronicle line says it: "names read 5 min ago".

Driven on the real functions: roster_publish in Python, roster.js's shapeSection/forHash in node, and the console's
_chronicleCounts cut out of control_ui.html and run in node with a fixed clock. RED_PROOF below.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
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
import roster_publish as RP  # noqa: E402

NODE = shutil.which("node")
T_COUNTS = 1790000000000
T_NOW = T_COUNTS + 3 * 3600 * 1000
TALLY = {"at": T_COUNTS, "uniques": {"have": 3, "total": 400}, "sets": {"have": 1, "total": 120}}
LISTS = {"uniques": {"Harlequin Crest": "", "The Stone of Jordan": "", "Windforce": ""}, "sets": {"Tal Rasha's Guardianship": ""}}


def _node(script, cfg):
    d = tempfile.mkdtemp(prefix="tvd_rows_age_")
    try:
        h, c = os.path.join(d, "h.mjs"), os.path.join(d, "cfg.json")
        io.open(h, "w", encoding="utf-8").write(script)
        io.open(c, "w", encoding="utf-8").write(json.dumps(cfg))
        r = subprocess.run([NODE, h, c], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    finally:
        shutil.rmtree(d, True)
    if r.returncode != 0:
        raise AssertionError("node failed rc=%s\n%s" % (r.returncode, r.stderr[-1500:]))
    return json.loads(r.stdout)


class ThePcStampsAndKeepsIt(unittest.TestCase):

    def test_the_chronicle_rows_carry_when_they_were_read(self):
        sec = RP.chronicle_read(TALLY, T_NOW, lists=LISTS)
        self.assertEqual(sec["asOf"], T_COUNTS, "PREMISE: the counts are dated by the bank")
        self.assertTrue(sec.get("rows"), "PREMISE: no name rows were read")
        self.assertEqual(sec.get("rowsAsOf"), T_NOW, "the names are dated by the banked counts: %r" % sorted(sec))

    def test_no_rows_no_stamp(self):
        sec = RP.chronicle_read(TALLY, T_NOW, lists=None)
        self.assertNotIn("rowsAsOf", sec, "a section with no names still says when its names were read")

    def test_the_shaper_keeps_it_beside_the_rows(self):
        shaped = RP.section_of(RP.chronicle_read(TALLY, T_NOW, lists=LISTS), T_NOW)
        self.assertEqual(shaped.get("rowsAsOf"), T_NOW)

    def test_the_stamp_never_changes_the_hash(self):
        a = RP.section_of(RP.chronicle_read(TALLY, T_NOW, lists=LISTS), T_NOW)
        b = dict(a, rowsAsOf=T_NOW + 999999)
        self.assertEqual(RP.packed(RP.for_hash({"chronicle": a})), RP.packed(RP.for_hash({"chronicle": b})),
                         "a new names stamp alone changes the hash, so every pass would publish")

    def test_the_reader_dates_the_names(self):
        sec = RP.section_of(RP.chronicle_read(TALLY, T_NOW, lists=LISTS), T_NOW)
        owner = "Konyo · ALT"
        row = {"owner": owner, "published": True, "t": T_NOW, "sections": {"chronicle": sec},
               "hash": RP.hash_of(RP.packed(RP.for_hash({"chronicle": sec})))}
        v = RP.view_one(owner, row, T_NOW + 60000)
        self.assertFalse(v.get("corrupt"), "a row carrying the names stamp failed its own hash check: %r" % v)
        ch = (v.get("sections") or {}).get("chronicle") or {}
        self.assertEqual((ch.get("age"), ch.get("rowsAge")), ("stale", "current"),
                         "the reader does not date the names apart from the banked counts: %r" % ch)


@unittest.skipUnless(NODE, "node is absent - roster.js and the console line are UNMEASURED here, never a pass")
class TheWorkerAndTheLineAgree(unittest.TestCase):

    def test_the_worker_keeps_it_and_leaves_it_out_of_the_hash(self):
        sec = RP.section_of(RP.chronicle_read(TALLY, T_NOW, lists=LISTS), T_NOW)
        script = r"""
import { pathToFileURL } from 'node:url';
import { readFileSync } from 'node:fs';
const CFG = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const m = await import(pathToFileURL(CFG.file).href);
const a = m.shapeSection(CFG.sec);
const b = m.shapeSection(Object.assign({}, CFG.sec, { rowsAsOf: CFG.sec.rowsAsOf + 999999 }));
process.stdout.write(JSON.stringify({ kept: a && a.rowsAsOf, same: m.forHash({ chronicle: a }) === m.forHash({ chronicle: b }) }));
"""
        o = _node(script, {"file": os.path.join(ROOT, "functions", "api", "roster.js"), "sec": sec})
        self.assertEqual(o["kept"], T_NOW, "the worker drops when the names were read")
        self.assertTrue(o["same"], "the worker hashes the names stamp, so the PC and the worker disagree on every pass")

    def test_the_shadow_line_says_when_the_names_were_read(self):
        ui = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
        start = ui.find("  function _chronicleCounts(summary, progress, lists) {")
        self.assertEqual(ui.count("  function _chronicleCounts(summary, progress, lists) {"), 1)
        end = ui.find("\n  }\n", start)
        fn = ui[start:end + 4]
        script = r"""
import { readFileSync } from 'node:fs';
const CFG = JSON.parse(readFileSync(process.argv[2], 'utf8'));
Date.now = () => CFG.now;
const f = new Function(CFG.fn + '\nreturn _chronicleCounts;')();
const prog = (at) => ({ uniques: { have: 3, total: 400, listed: true, rowsAsOf: at } });
process.stdout.write(JSON.stringify({
  five: f(null, prog(CFG.now - 5 * 60000), null),
  ahead: f(null, prog(CFG.now + 10 * 60000), null),
  none: f(null, { uniques: { have: 3, total: 400, listed: true } }, null)
}));
"""
        o = _node(script, {"fn": fn, "now": T_NOW})
        self.assertIn("names read 5 min ago", o["five"], "the shadow line does not say when the names were read: %r" % o)
        self.assertNotIn("names read", o["ahead"], "a clock ahead of now was said as an age: %r" % o["ahead"])
        self.assertNotIn("names read", o["none"], "a section with no stamp invented one: %r" % o["none"])


RED_PROOF = [
    {"why": "REG-2745 - the names are dated by the banked counts again",
     "file": "roster_publish.py",
     "find": "            out[\"rowsAsOf\"] = now_ms\n",
     "replace": "            pass\n",
     "matches": 1},
    {"why": "REG-2745 - the PC's hash takes the names stamp",
     "file": "roster_publish.py",
     "find": "if k not in (\"asOf\", \"rowsAsOf\", \"hash\", \"allow\")}",
     "replace": "if k not in (\"asOf\", \"hash\", \"allow\")}",
     "matches": 1},
    {"why": "REG-2745 - the worker's hash takes the names stamp",
     "file": "functions/api/roster.js",
     "find": "      if (k === \"asOf\" || k === \"rowsAsOf\" || k === \"hash\") continue;",
     "replace": "      if (k === \"asOf\" || k === \"hash\") continue;",
     "matches": 1, "needs": "node"},
    {"why": "REG-2745 - the reader never dates the names",
     "file": "roster_publish.py",
     "find": "                one[\"rowsAge\"] = _age_state(sec.get(\"rowsAsOf\"), now_ms)",
     "replace": "                pass",
     "matches": 1},
    {"why": "REG-2745 - the shadow line says nothing about the names' age",
     "file": "control_ui.html",
     "find": "    if (namesAt && line) {",
     "replace": "    if (false) {",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
