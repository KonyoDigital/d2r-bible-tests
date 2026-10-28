# -*- coding: utf-8 -*-
"""Front-run (REG-2837, REG-2838) - EVERY COPY HE ADDS GETS ITS MOVE ROW, AND A LATER SIGHTING JOINS THE RIGHT COPY.

His plan: hand-add his real items now, organise them in game by the MOVE tasks (mule + cell), and later let AUTO's
sightings JOIN those same records ("manually or automatic ... its the same items"). Measured on the whole page in node:
  * REG-2837 - 505 hand adds through the planner: all 60 perfect bases (the planner files them through vaultFile, never
    vaultHandAdd) and all 9 later copies of a filed name (the planner's copy count) had a record and NO MOVE task;
  * REG-2838 - two Stones of Jordan added by hand, AUTO on: the first sighting (stash c0r0) gave copy 0 its FROM cell, and
    the second (a new cell, c2r0) was read as copy 0 "moved-elsewhere" - copy 1 never got its sighting.
Now the planner writes each such copy's MOVE row (window._vaultMoveNoteAdded, the + Add an item door's own writer), and
a sighting at a new cell joins the first hand copy whose MANUAL row has no FROM cell yet. Driven here end to end: a 4os
Monarch and two Stones of Jordan through the planner, then reel sightings through tvVaultRegister. RED_PROOF below.
"""
import json
import os
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
import vault_page_node as VPN  # noqa: E402

PRELUDE = ("Object.defineProperty(navigator, 'webdriver', { get: function(){ return true; }, configurable: true });\n"
           "localStorage.setItem('d2r_ownerClaim', '*'); localStorage.setItem('d2r_vaultAutoIntake', 'on');\n")

BODY = r"""
(function(){
var W = window, DB = W._cbDb();
function code(n){ return Object.keys(DB.b).find(function(c){ return DB.b[c][0] === n; }); }
function rows(n){
  var raw = null; try { raw = JSON.parse(W.LSR.getItem('d2r_vaultRecords') || 'null'); } catch (e) {}
  return ((raw && raw.records) || []).filter(function(r){ return r.name === n; }).map(function(r){
    var m = r.move || null;
    return { ix: r.copyIx || 0, move: !!m, to: m && m.to ? (m.to.cell || null) : null, from: m && m.from ? (m.from.cell || null) : null,
             manual: !!(m && m.manual), status: m ? m.status : null, ev: m ? (m.evidence || []) : null };
  }).sort(function(a, b){ return a.ix - b.ix; });
}
function see(n, x, s1, s2){
  var cell = { x: x, y: 0, container: 'stash' };
  var r = W.tvVaultRegister(n, { by: 'tv-register', loc: 'stash', scene: 'stash', holder: 'MULE1', at: '2026-10-28T18:00:00.000Z', cell: cell,
                                 sessions: [{ session: s1, frame: s1 + '_f', cell: cell, holder: 'MULE1' }, { session: s2, frame: s2 + '_f', cell: cell, holder: 'MULE1' }] });
  H.flush(60, 3); try { W.renderVault(); } catch (e) {} H.flush(60, 3);
  return !!(r && r.ok);
}
/* a perfect base, through the planner */
W.vaultPlannerOpen(''); W._cbChoose('b:' + code('Monarch')); W._cbQuality('b'); W._cbEdit('sockets', '4'); W.vaultPlannerClose(); H.flush(60, 3);
OUT.base = rows('Monarch (4os)');
/* two Stones of Jordan, two opens - the second is a name he now holds, so the plate asks (REG-2841) and he answers "Another copy" */
var soj = DB.it.find(function(x){ return x[1] === 'The Stone of Jordan' && x[2] === 'u'; });
OUT.asked = [0, 1].map(function(){ W.vaultPlannerOpen(''); W._cbChoose(soj[0]); var asked = W.vaultPlannerClose() === false;
  if (asked){ W.vaultPlannerAnswer('copy'); W.vaultPlannerClose(); } H.flush(60, 3); return asked; });
var J = 'The Stone of Jordan';
OUT.copies = copyCount(J);
OUT.j0 = rows(J);
OUT.seen1 = see(J, 0, 'b1', 'b2'); OUT.j1 = rows(J);
OUT.seen2 = see(J, 2, 'b3', 'b4'); OUT.j2 = rows(J);
OUT.seen3 = see(J, 0, 'b5', 'b6'); OUT.j3 = rows(J); OUT.copies3 = copyCount(J);
OUT.errors = H.errors.slice();
})();
"""


class AHandCopyGetsItsMoveAndItsSighting(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not VPN.NODE:
            raise AssertionError("node is not on this machine - this law does not skip")
        cls.o = VPN.run(BODY, prelude=PRELUDE, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(self.o["errors"], [])
        self.assertEqual(self.o["asked"], [False, True], "PREMISE: the second Stone was not asked 'same item or another copy'")

    def test_a_perfect_base_from_the_planner_gets_its_move(self):
        b = self.o["base"]
        self.assertEqual(len(b), 1, "PREMISE: the 4os Monarch has no record: %r" % b)
        self.assertTrue(b[0]["move"] and b[0]["to"] and b[0]["manual"], "the perfect base has no MOVE task with a cell: %r" % b)

    def test_each_planner_copy_gets_its_own_move(self):
        j = self.o["j0"]
        self.assertEqual(self.o["copies"], 2, "PREMISE: the second open did not count a second copy")
        self.assertEqual([r["ix"] for r in j], [0, 1], j)
        self.assertTrue(all(r["move"] and r["to"] and r["manual"] for r in j), "a copy has no MOVE task with a cell: %r" % j)
        self.assertNotEqual(j[0]["to"], j[1]["to"], "two copies share one target cell: %r" % j)

    def test_a_sighting_at_a_new_cell_joins_the_unseen_copy(self):
        self.assertTrue(self.o["seen1"] and self.o["seen2"], "PREMISE: a sighting did not register")
        j1, j2 = self.o["j1"], self.o["j2"]
        self.assertEqual((j1[0]["from"], j1[1]["from"]), ("stash:c0r0", None), "the first sighting did not join copy 0: %r" % j1)
        self.assertEqual(j2[1]["from"], "stash:c2r0", "the second cell did not join the unseen copy: %r" % j2)
        self.assertEqual((j2[0]["from"], j2[0]["status"]), ("stash:c0r0", "to-move"),
                         "copy 0 was read as moved elsewhere by the second copy's sighting: %r" % j2)
        self.assertEqual((j2[0]["ev"], j2[1]["ev"]), (["b1_f"], ["b3_f"]), "a sighting's frame went to the wrong copy: %r" % j2)

    def test_a_re_read_of_a_seen_cell_adds_no_copy(self):
        self.assertEqual(self.o["copies3"], 2, "a re-read made a third copy")
        self.assertEqual(self.o["j3"][1]["from"], "stash:c2r0", self.o["j3"])


RED_PROOF = [
    {"why": "REG-2837 - the planner's later copy gets no MOVE row again",
     "file": "bible.html",
     "find": "          _vpMoveAt = { name: nm, copyIx: copies[nm] - 1 };   /* REG-2837 - this copy's own MOVE row, written once saved */\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2837 - a perfect base from the planner gets no MOVE row again",
     "file": "bible.html",
     "find": "    if (_pb && !beforeOwned && routed && (routed.mode === 'filed' || routed.mode === 'confirmed')) _vpMoveAt = { name: nm, copyIx: 0 };\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2838 - a new cell goes to copy 0 again, which reads it as moved elsewhere",
     "file": "bible.html",
     "find": "      if (tW && tW.manual && (!tW.from || tW.from.cell == null)) hit = ensW;   /* REG-2838 the unseen hand copy */\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
