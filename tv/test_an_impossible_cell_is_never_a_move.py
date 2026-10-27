# -*- coding: utf-8 -*-
"""#153.7 (GrokBot's vault sweep) - AN IMPOSSIBLE CELL IS NEVER A MOVE.

A sighting at stash:c99r99 returned applied:true and became a move's FROM - a cell no stash has. A grid cell must sit
inside its grid: the stash 10x10, the inventory 10x4 (the page's MULE_* constants, 0-based). A cell in another shape
(equipped:head) is not a grid cell and is left alone. Whether a second item may be read in an OCCUPIED cell is his
ruling to make, and is not decided here.

Driven on the whole page in node through window._vaultMoveApplySight with AUTO INTAKE on.
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
localStorage.setItem('d2r_owned', JSON.stringify(["The Gnasher", "Bloodfist"]));
localStorage.setItem('d2r_muleAssign', JSON.stringify({}));
"""

BODY = r"""
(function(){
var W = window;
W._vaultAutoIntakeSet(true);
function ap(nm, loc, cell){ var r = W._vaultMoveApplySight(nm, { holder: 'MAIN', location: loc, cell: cell, session: 's_1', frame: 'f_1' });
  return r ? { applied: !!r.applied, why: r.why || null } : null; }
OUT.ok = [W._vaultCellOk('stash:c9r9'), W._vaultCellOk('inventory:c9r3'), W._vaultCellOk('equipped:head'), W._vaultCellOk('stash:c0r0')];
OUT.bad = [W._vaultCellOk('stash:c99r99'), W._vaultCellOk('stash:c10r0'), W._vaultCellOk('inventory:c3r4'), W._vaultCellOk('inventory:c10r0')];
OUT.big = ap('The Gnasher', 'stash', 'stash:c99r99');
OUT.inv = ap('Bloodfist', 'inventory', 'inventory:c3r9');
OUT.real = ap('The Gnasher', 'stash', 'stash:c9r9');
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AnImpossibleCellIsNeverAMove(unittest.TestCase):

    def test_cells_inside_their_grid_and_out_of_it(self):
        o = VPN.run(BODY, prelude=SEED, timeout=300)
        self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
        self.assertEqual(o["ok"], [True, True, True, True], o["ok"])
        self.assertEqual(o["bad"], [False, False, False, False], o["bad"])
        self.assertEqual(o["big"], {"applied": False, "why": "impossible-cell"}, "stash:c99r99 was applied (#153.7): %r" % o)
        self.assertEqual(o["inv"], {"applied": False, "why": "impossible-cell"}, o)
        self.assertNotEqual(o["real"]["why"], "impossible-cell", "PREMISE: a real corner cell was refused: %r" % o)


RED_PROOF = [
    {"why": "#153.7 - a sighting at an impossible cell is applied as a move again",
     "file": "bible.html",
     "find": "    if (!_vaultCellOk(place.cell)) return { applied: false, task: null, why: 'impossible-cell' };   /* #153.7 */\n",
     "replace": "", "matches": 1, "needs": "node"},
    {"why": "#153.7 - the inventory is checked against the stash's 10x10 again",
     "file": "bible.html",
     "find": "    if (/inv/.test(cont)) { w = MULE_INV_W; h = MULE_INV_H; }\n",
     "replace": "", "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
