# -*- coding: utf-8 -*-
"""v3830 second eye (REG-2842) - A CLEARED PLANNER PICK PUTS BACK THE KEEPER TARGET IT RAISED, WHATEVER THE COUNT IS NOW.

A planner pick of a name he holds, seen in fewer cells than copies, raises copies[] and the keeper target with it
(REG-2786), so the copy is drawn. Its clear put the target back only on the branch that also took the copy off - the one
where the live count is still above the count the pick started from. With the count lowered elsewhere first (another tab's
merge, a removal), the clear said "nothing more ... was taken back" and left the target the pick had raised: a later
re-read was then drawn as a copy the clear had put back. Now the clear restores the target it set whatever the live count
is, unless something else has set the target since, and its sentence says so. Driven on the whole page in node on the
REG-2786 Obedience scenario. RED_PROOF below.
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

OBED = "Obedience"
LOOK = {"id": "s_law_10", "frame": "10_100", "conf": None, "at": "2026-10-22T08:00:00.000Z", "loc": "stash", "scene": "stash",
        "holder": "MULE1", "cell": {"x": 5, "y": 0, "container": "stash"}}
PRELUDE = ("localStorage.setItem('d2r_ownerClaim', '*');\n"
           "localStorage.setItem('d2r_owned', %s);\n" % json.dumps(json.dumps([OBED]))
           + "localStorage.setItem('d2r_copies', '{}');\n"
           + "localStorage.setItem('d2r_muleAssign', %s);\n" % json.dumps(json.dumps({OBED: "runewords"}))
           + "localStorage.setItem('d2r_vaultProv', %s);\n" % json.dumps(json.dumps(
               {OBED: {"mule": "runewords", "source": "tv", "by": "tv", "at": "2026-10-20T08:00:00.000Z", "looks": [LOOK],
                       "kind": "filing"}})))

BODY = r"""
(function(){
var W = window, N = %s;
function paint(){ try { W.renderVault(); } catch (e) { OUT.renderErr = String(e && e.message || e); } H.flush(60, 3); }
function mk(){ return Object.prototype.hasOwnProperty.call(multiKeep, N) ? _mkWant(N) : null; }   /* the want, through REG-2900's one accessor: a target is {want, dest} */
function stored(){ try { var m = JSON.parse(W.LSR.getItem('d2r_multiKeep') || '{}'); return (N in m) ? m[N] : null; } catch (e) { return 'UNREADABLE'; } }
paint();
var it = W._cbItem('r92'), b = (W._cbBasesOf(it) || [])[0];
OUT.before = { copies: copyCount(N), mk: mk() };
var p = W.vaultPlannerFile({ id: 'r92', base: b, affixes: [], sockets: 0 }, 'law-copy');
OUT.pick = { mode: p && p.mode, copies: copyCount(N), mk: mk() };
/* something else lowers the live count back to 1 before the clear (a removal, another tab's merge) */
delete copies[N]; try { persistOwned(); } catch (e) {}
OUT.lowered = { copies: copyCount(N), mk: mk() };
var cl = W.vaultPlannerFile(null, 'law-copy'); paint();
OUT.clear = { mode: cl && cl.mode, why: cl && cl.why, copies: copyCount(N), mk: mk(), stored: stored() };
OUT.errors = H.errors.slice();
})();
""" % json.dumps(OBED)


class AClearedPickPutsBackItsKeeperTarget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not VPN.NODE:
            raise AssertionError("node is not on this machine - this law does not skip")
        cls.o = VPN.run(BODY, prelude=PRELUDE, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(self.o["errors"], [])

    def test_the_pick_raised_the_target_and_the_count_was_lowered_elsewhere(self):
        b, p, lo = self.o["before"], self.o["pick"], self.o["lowered"]
        self.assertEqual((b["copies"], b["mk"]), (1, None), "PREMISE: %r" % b)
        self.assertEqual((p["copies"], p["mk"]), (2, 2), "PREMISE: the pick did not raise the copy and its target: %r" % p)
        self.assertEqual((lo["copies"], lo["mk"]), (1, 2), "PREMISE: the count was not lowered before the clear: %r" % lo)

    def test_the_clear_puts_back_the_target_it_raised(self):
        c = self.o["clear"]
        self.assertEqual(c["mode"], "cleared", c)
        self.assertEqual(c["copies"], 1, c)
        self.assertIsNone(c["mk"], "the clear left the keeper target its pick raised: %r" % c)
        self.assertIsNone(c["stored"], "the target the clear put back is still on disk: %r" % c)
        self.assertIn("the keeper target this pick raised is put back", c["why"] or "", c)


RED_PROOF = [
    {"why": "REG-2842 - the clear puts the target back only when it also takes the copy off",
     "file": "bible.html",
     "find": "      if (b.keepSet != null && typeof multiKeep !== 'undefined' && multiKeep && _mkWant(b.name) === b.keepSet){\n",
     "replace": "      if (_vpCopyUndone.took && b.keepSet != null && typeof multiKeep !== 'undefined' && multiKeep && _mkWant(b.name) === b.keepSet){\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
