# -*- coding: utf-8 -*-
"""#201 - A LOOK UNDER THE 0.55 FLOOR OPENS NO MOVE, THROUGH THE STORED RECORD TOO.

The v3808 cross-family look (MED): the rule "a look counts only with its own session, its own frame and, when scored,
conf >= VAULT_WITNESS_FLOOR" had three copies. The register wrapper and _vaultSightLooks' list branch applied it;
_vaultSightGroups did not - it counted any look with a session and a cell. A stored record's sight.witnesses is that
count, and _vaultSightLooks returns a number as it is, so a 0.40 look WITH a session reached _vaultMoveCollect as
witnesses 1 and opened a move the wrapper had scored 0 looks (the "Hellfire Torch under 0.55" case from #230).

Driven on the WHOLE page in node (tv/vault_page_node.py), through the real door (window.tvVaultRegister) with AUTO
INTAKE on, then the real persist and the real collector. One helper (window._vaultLookCounts) now answers for all three.
RED_PROOF below.
"""
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

SEED = r"""
localStorage.setItem('d2r_ownerClaim', '*');
/* #202 (his 2026-10-27 ruling): a FIRST read of a name he does not own is held until a second session. This law is about
   the floor on a look, so both items are already his - a re-read records its sight and asks the move rule. */
localStorage.setItem('d2r_owned', JSON.stringify(["Hellfire Torch", "Treachery"]));
localStorage.setItem('d2r_vaultProv', JSON.stringify({}));
localStorage.setItem('d2r_muleAssign', JSON.stringify({}));
"""

BODY = r"""
(function(){
var W = window, S1 = 's_1791232871109_10831';
function recs(){ try { return (JSON.parse(localStorage.getItem('d2r_vaultRecords') || '{}').records || []); } catch (e) { return []; } }
function movesOf(nm){ return recs().filter(function(r){ return r.name === nm && r.move; }).length; }
function sightOf(nm){ var r = recs().filter(function(r){ return r.name === nm; })[0]; return r && r.sight ? r.sight.witnesses : 'none'; }
function reg(nm, cell, conf){
  var r = W.tvVaultRegister(nm, { lane: 'shared', location: 'shared', cell: cell,
    witnesses: [{ session: S1, frame: 'f_1791548118549.jpg', lane: 'shared', conf: conf, cell: cell }] });
  return !!(r && r.ok);
}
function tasksOf(nm){
  W._movePaintBusy = false;
  try { W._vaultMovePaint(); } catch (e) { OUT.collectErr = String(e && e.message || e); }
  var m = W._moveModel;
  if (!m || !Array.isArray(m.tasks)) { OUT.collectErr = 'the move model did not build'; return null; }
  return m.tasks.filter(function(t){ return t && t.name === nm; }).length;
}
W._vaultAutoIntakeSet(true);
OUT.lowOk = reg('Hellfire Torch', 'shared:c9r6', 0.40);
OUT.lowMoves = movesOf('Hellfire Torch');
OUT.lowTasks = tasksOf('Hellfire Torch');
OUT.lowSight = sightOf('Hellfire Torch');
OUT.lowGroups = (W._vaultSightGroups('Hellfire Torch') || []).map(function(g){ return g.witnesses; });
OUT.highOk = reg('Treachery', 'shared:c3r4', 0.80);
OUT.highMoves = movesOf('Treachery');
OUT.highTasks = tasksOf('Treachery');
OUT.highGroups = (W._vaultSightGroups('Treachery') || []).map(function(g){ return g.witnesses; });
OUT.looks = [
  W._vaultSightLooks({ witnesses: [{ session: 's1', frame: 'f1', conf: 0.40 }] }),
  W._vaultSightLooks({ witnesses: [{ session: 's1', frame: 'f1', conf: 0.60 }] }),
  W._vaultSightLooks({ witnesses: [{ session: 's1', frame: 'f1' }] }),
  W._vaultSightLooks({ witnesses: [{ session: 's1', frame: 'f1' }, { session: 's2', frame: 'f2', conf: 0.9 }] }),
  W._vaultSightLooks({ witnesses: [{ session: 's1', conf: 0.9 }] })
];
OUT.floor = W.VAULT_WITNESS_FLOOR;
})();
"""
_RUNS = {}


def page():
    if "p" not in _RUNS:
        _RUNS["p"] = VPN.run(BODY, prelude=SEED, timeout=300)
    return _RUNS["p"]


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ALookUnderTheFloorOpensNoMove(unittest.TestCase):

    def test_the_page_booted(self):
        o = page()
        self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
        self.assertNotIn("collectErr", o, o)
        self.assertEqual(o["floor"], 0.55)

    def test_a_sub_floor_look_with_a_session_is_owned_with_no_move(self):
        o = page()
        self.assertTrue(o["lowOk"], o)
        self.assertIsNone(o["lowSight"], "a 0.40 look was stored as a witness: %r" % o)
        self.assertEqual(o["lowGroups"], [None], "the copy is kept, but a 0.40 look is not its witness: %r" % o)
        self.assertEqual(o["lowMoves"], 0, "a 0.40 look opened a move through the stored record (#201): %r" % o)
        self.assertEqual(o["lowTasks"], 0, "the move collector drew a task for a 0.40 look (#201): %r" % o)

    def test_a_look_over_the_floor_still_opens_its_move(self):
        o = page()
        self.assertTrue(o["highOk"], o)
        self.assertEqual(o["highGroups"], [1], o)
        self.assertEqual(o["highMoves"], 1, "PREMISE: a 0.80 look with its own session and frame opened no move: %r" % o)
        self.assertEqual(o["highTasks"], 1, "PREMISE: the collector drew no task for a 0.80 look: %r" % o)

    def test_one_rule_for_a_list_of_looks(self):
        o = page()
        self.assertEqual(o["looks"], [0, 1, 1, 1, 0], o["looks"])


RED_PROOF = [
    {"why": "#201 - the sight groups count any look with a session again, so a 0.40 look is stored as a witness",
     "file": "bible.html",
     "find": "      var sid = window._vaultLookCounts(k, _scored);   /* #201 - own session, own frame, over the floor when scored */\n",
     "replace": "      var sid = k.session || k.id || null;\n",
     "matches": 1, "needs": "node"},
    {"why": "#201 - the one rule drops its floor, so every scored look counts",
     "file": "bible.html",
     "find": "    if (c == null ? !!scored : c < VAULT_WITNESS_FLOOR) return null;\n",
     "replace": "    if (c == null && !!scored) return null;\n",
     "matches": 1, "needs": "node"},
    {"why": "#201 - the one rule drops the frame, so a look with no picture counts",
     "file": "bible.html",
     "find": "    if (!sid || !(look.frame || look.frameId)) return null;\n",
     "replace": "    if (!sid) return null;\n",
     "matches": 1, "needs": "node"},
    {"why": "#201 - an unscored look in a scored set counts again",
     "file": "bible.html",
     "find": "    if (c == null ? !!scored : c < VAULT_WITNESS_FLOOR) return null;\n",
     "replace": "    if (c != null && c < VAULT_WITNESS_FLOOR) return null;\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
