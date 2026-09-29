# -*- coding: utf-8 -*-
"""REG-1548 — THE SETS LEDGER KEEPS A DATED HISTORY, AND A STALE READING MAY ONLY REMOVE WHAT IT IS NEWER THAN.

2026-09-29 20:51, his Mac: the store came back without its one-shot flags (rewritten at 02:54), the Aug-21 boot
repair (`_SET_MISSING`, readAt 2026-08-21) ran again and took 16 set pieces he had found weeks after that
reading — 133 -> 118 — and nothing recorded when any piece had arrived, so nothing could say "newer than the
reading". Restored by hand from a copy of his 20:44 store (134/135). Konyo: "make sure the ledger is restoring
from the last and most recent refreshed and updated last read.. we should be having a history of this in ledger
to go by".

DRIVEN: the real `window.LSR` IIFE, cut from bible.html and run in node over an in-memory localStorage — the one
door LS/LSx/LSR all are. The repair's boot decision is driven on the real page by
tests/v1938_remaining_repair_outcome.spec.ts (CI); here its condition is pinned so a revert shows locally.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

NODE = shutil.which("node")

_DRIVER = r"""
const fs = require('fs');
const s = fs.readFileSync(process.argv[2], 'utf8');
const i = s.indexOf('window.LSR = (function(){'); const j = s.indexOf('})();', i) + 5;
const steps = JSON.parse(process.argv[3]);
const store = JSON.parse(process.argv[4] || '{}');
const LS = { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); },
             removeItem: k => { delete store[k]; } };
const owner = process.argv[5] !== 'guest';
global.window = { localStorage: LS, _D2R_OWNER: owner, D2R_PROFILE: 'main', _D2R_PFX: 'I·abcd1234·',
                  _D2R_LPFX: 'L·', _LP_FORKED: new Set(['d2r_setPieces']), _WP_FORKED: new Set(['d2r_setPieces']) };
eval(s.slice(i, j));
let threw = null;
for (const st of steps) { try { window.LSR.setItem('d2r_setPieces', typeof st === 'string' ? st : JSON.stringify(st)); } catch (e) { threw = String(e); } }
process.stdout.write(JSON.stringify({ store, threw }));
"""


def _drive(steps, store=None, world="owner", src=None):
    import tempfile
    path = src or os.path.join(ROOT, "bible.html")
    d = tempfile.mkdtemp(prefix="sets_history_")
    drv = os.path.join(d, "driver.js")
    io.open(drv, "w", encoding="utf-8").write(_DRIVER)
    try:
        r = subprocess.run([NODE, drv, path, json.dumps(steps), json.dumps(store or {}), world],
                           capture_output=True, text=True, timeout=60)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if r.returncode != 0:
        raise AssertionError("node driver failed: %s" % r.stderr[-400:])
    return json.loads(r.stdout)


@unittest.skipIf(not NODE, "node is not installed here — the law cannot drive the page's storage door (NOT a pass)")
class TheSetsLedgerKeepsItsHistory(unittest.TestCase):

    def test_every_new_piece_is_stamped_the_first_time_it_appears(self):
        out = _drive([["A", "B"], ["A", "B", "C"]])["store"]
        since = json.loads(out["d2r_setPiecesSince"])
        self.assertEqual(sorted(since), ["A", "B", "C"])
        self.assertLessEqual(since["A"], since["C"])

    def test_a_piece_already_held_is_never_restamped_as_new(self):
        # a store that held pieces BEFORE stamping existed: their arrival is UNKNOWN and must stay unknown —
        # stamping them "now" would make an old piece look newer than any reading
        out = _drive([["A", "B", "C"]], store={"d2r_setPieces": json.dumps(["A", "B"])})["store"]
        self.assertEqual(sorted(json.loads(out["d2r_setPiecesSince"])), ["C"])

    def test_a_shrink_keeps_the_list_as_it_was_dated_with_what_left(self):
        out = _drive([["A", "B", "C", "D"], ["A", "D"]])["store"]
        h = json.loads(out["d2r_setPiecesHistory"])
        self.assertEqual(1, len(h))
        self.assertEqual(sorted(h[0]["removed"]), ["B", "C"])
        self.assertEqual(sorted(h[0]["pieces"]), ["A", "B", "C", "D"])
        self.assertEqual((h[0]["before"], h[0]["after"]), (4, 2))
        self.assertTrue(h[0]["at"].startswith("20"), "the row carries no readable date")

    def test_growth_writes_no_history_row(self):
        out = _drive([["A"], ["A", "B"]])["store"]
        self.assertNotIn("d2r_setPiecesHistory", out)

    def test_the_history_is_bounded_to_the_newest_twenty(self):
        steps = []
        for k in range(25):
            steps += [["A", "X%d" % k], ["A"]]
        h = json.loads(_drive(steps)["store"]["d2r_setPiecesHistory"])
        self.assertEqual(20, len(h))
        self.assertEqual(["X24"], h[-1]["removed"], "the newest shrink is not the last row")

    def test_the_history_lives_in_the_same_world_as_the_pieces(self):
        # a guest's history must never be read as his: it routes with d2r_setPieces' own prefix
        out = _drive([["A", "B"], ["A"]], world="guest")["store"]
        self.assertIn("I·abcd1234·d2r_setPiecesHistory", out)
        self.assertNotIn("d2r_setPiecesHistory", out)
        self.assertIn("I·abcd1234·d2r_setPieces", out)

    def test_a_bad_value_never_breaks_the_write_it_rides_on(self):
        res = _drive(["not json", ["A"]], store={"d2r_setPiecesSince": "{broken"})
        self.assertIsNone(res["threw"])
        self.assertEqual('["A"]', res["store"]["d2r_setPieces"])


class TheBootRepairAsksTheStamps(unittest.TestCase):
    """The page-level decision is DRIVEN on CI (v1938 spec, '★★★ v3525'); this pins its shape so a revert of the
    guard is seen on the Mac before a push rather than after."""

    def _repair_src(self):
        src = io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8").read()
        i = src.index("window._chRepairLedgers = function(opts){")
        return src[i:src.index("out.kept = keep.length;", i)]

    def test_the_auto_run_keeps_what_it_cannot_prove_is_older(self):
        seg = self._repair_src()
        self.assertIn("opts.auto", seg)
        self.assertIn("_spSince[n] && _readAtMs && _spSince[n] < _readAtMs", seg,
                      "the boot repair no longer asks whether a piece predates the reading")
        self.assertIn("window.LSR.spSide('d2r_setPiecesSince')", seg,
                      "the repair reads the stamps from a different world than the hook writes them")


RED_PROOF = [
    {
        "why": "2026-09-29 (REG-1548) - the storage door no longer records the sets ledger's history",
        "file": "bible.html",
        "find": "      if (k === 'd2r_setPieces'){ try { _spHistory(v); } catch(e){} }\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (REG-1548) - pieces already held are stamped 'now', so an old piece reads newer than a reading",
        "file": "bible.html",
        "find": "    next.forEach(function(n){ if (!inPrev[n] && !since[n]){ since[n] = now; stamped = true; } });\n",
        "replace": "    next.forEach(function(n){ if (!since[n]){ since[n] = now; stamped = true; } });\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (REG-1548) - the history lives in the bare world whatever world the pieces are in",
        "file": "bible.html",
        "find": "  function _spSide(name){ var kk = key('d2r_setPieces'); return kk.slice(0, kk.length - 'd2r_setPieces'.length) + name; }\n",
        "replace": "  function _spSide(name){ return name; }\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (REG-1548) - the boot repair removes on the stale reading again, whatever the stamps say",
        "file": "bible.html",
        "find": "          && !(_spSince[n] && _readAtMs && _spSince[n] < _readAtMs)){\n",
        "replace": "          && false){\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
