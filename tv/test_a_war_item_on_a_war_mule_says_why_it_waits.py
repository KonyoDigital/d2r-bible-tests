# -*- coding: utf-8 -*-
"""#148.1 (REG-2761, his ruling 2026-10-28) - A WAR ITEM HE FILED ON A WAR MULE SAYS WHY ITS TASK GOES TO THE SHARED STASH.

GrokBot (#230 c6319274564): vaultAssign('Grief', WAR1) wrote the filing, and both Grief tasks still targeted SHARED STASH
through a reload - it read as his hand being ignored. His ruling: war items go to the Shared stash (the war stash), and
the WAR mules only when its 5 pages are full. That is L1 and BY DESIGN; the move task should say why. So the target
stays (_vaultMoveHome honours a hand filing only on a NORMAL mule) and the row carries "war stash first", its title the
whole reason (_vaultMoveL1Why). Nothing is said when the item is not filed on a WAR mule, or its task goes elsewhere.

Driven on the whole page in node (vault_page_node - never a browser on his Mac), the WAR mule seeded into the roster
store the way his saved roster holds it, beside the page's own default lockers read in a first pass. RED_PROOF below.
"""
import io
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
import json  # noqa: E402
import vault_page_node as VPN  # noqa: E402

WAR = "Arachnid Mesh"          # war-stash gear (a belt files to SHARED STASH - test_vault_l1_a_hand_add_routes_by_type)
CLAIM = "localStorage.setItem('d2r_ownerClaim', '*');\n"


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AWarItemOnAWarMuleSaysWhyItWaits(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        base = VPN.run("OUT.r = JSON.parse(window.LSR.getItem('d2r_muleRoster') || 'null') || "
                       "(window._vaultRosterNow && window._vaultRosterNow());", prelude=CLAIM, timeout=300).get("r")
        if not isinstance(base, list) or not base:
            raise AssertionError("PREMISE: the page has no default roster to extend: %r" % (base,))
        roster = [m for m in base if not str(m.get("id", "")).startswith("war-law-")] + [{"id": "war-law-0", "name": "WAR1"}]
        cls.o = VPN.run(r"""
window._vaultAutoIntakeSet(false);
var a = window.vaultHandAdd(%(war)r);
OUT.add = a && a.ok;
OUT.before = window._vaultMoveL1Why(%(war)r, (window._vaultMoveEnsure(%(war)r, 0) || {}).task);
window.vaultAssign(%(war)r, 'war-law-0');
var t = (window._vaultMoveEnsure(%(war)r, 0) || {}).task;
OUT.to = t && t.to ? { id: t.to.id, location: t.to.location, holder: t.to.holder } : null;
OUT.why = window._vaultMoveL1Why(%(war)r, t);
OUT.notShared = window._vaultMoveL1Why(%(war)r, { to: { id: 'uni-weap', location: 'stash' } });
window.vaultAssign(%(war)r, 'uni-armor');
var tn = (window._vaultMoveEnsure(%(war)r, 0) || {}).task;
OUT.normalTo = tn && tn.to ? { id: tn.to.id, location: tn.to.location } : null;
OUT.normal = window._vaultMoveL1Why(%(war)r, tn);
""" % {"war": WAR}, prelude=CLAIM + "localStorage.setItem('d2r_muleRoster', %s);\n" % json.dumps(json.dumps(roster)),
                        timeout=300)

    def test_the_target_stays_on_the_shared_stash(self):
        self.assertTrue(self.o.get("add"), "PREMISE: the hand add did not land: %r" % self.o)
        to = self.o.get("to") or {}
        self.assertTrue(to.get("id") == "shared" or to.get("location") == "shared",
                        "PREMISE: L1 moved the task off the shared stash: %r" % to)

    def test_the_task_says_why(self):
        why = self.o.get("why") or ""
        self.assertIn("SHARED stash first (L1)", why, "the task does not say why his WAR-mule filing waits: %r" % why)
        self.assertIn("WAR1", why, "the reason does not name the mule he filed it on: %r" % why)
        self.assertIn("5 pages are full", why)

    def test_nothing_is_said_when_his_hand_is_not_on_a_war_mule(self):
        self.assertEqual(self.o.get("before"), "", "a reason was given before he filed it anywhere")
        self.assertEqual(self.o.get("notShared"), "", "a reason was given for a task that does not go to the shared stash")
        nt = self.o.get("normalTo") or {}
        self.assertTrue(nt.get("id") == "shared" or nt.get("location") == "shared",
                        "PREMISE: the keeper copy of a war item filed on a normal mule left the shared stash: %r" % nt)
        self.assertEqual(self.o.get("normal"), "", "a filing on a NORMAL mule was explained as a WAR-mule wait")


class TheRowCarriesIt(unittest.TestCase):

    def test_the_move_row_shows_the_reason(self):
        page = io.open(os.path.join(os.path.dirname(HERE), "bible.html"), encoding="utf-8").read()
        self.assertEqual(page.count("var l1 = (!thr && typeof window._vaultMoveL1Why === 'function') ? window._vaultMoveL1Why(row.name, t) : '';"), 1,
                         "the move row does not ask why")
        self.assertEqual(page.count("+ (l1 ? '<b class=\"vmv-l1\" title=\"' + esc(l1) + '\">war stash first</b>' : '')"), 1,
                         "the move row does not show the reason")


RED_PROOF = [
    {"why": "REG-2761 - the task never says why his WAR-mule filing waits",
     "file": "bible.html",
     "find": "      if (!m || !_vaultWarRole(m)) return '';\n      return 'war gear lives on the SHARED stash first (L1): '",
     "replace": "      return '';\n      return 'war gear lives on the SHARED stash first (L1): '",
     "matches": 1},
    {"why": "REG-2761 - the reason is given for any filing, a normal mule's included",
     "file": "bible.html",
     "find": "      if (!m || !_vaultWarRole(m)) return '';\n",
     "replace": "      if (!m) return '';\n",
     "matches": 1},
    {"why": "REG-2761 - the reason is given for a task that does not go to the shared stash",
     "file": "bible.html",
     "find": "      if (!to || !(to.id === 'shared' || to.location === 'shared')) return '';\n",
     "replace": "      if (!to) return '';\n",
     "matches": 1},
    {"why": "REG-2761 - the row drops the reason",
     "file": "bible.html",
     "find": "        + (l1 ? '<b class=\"vmv-l1\" title=\"' + esc(l1) + '\">war stash first</b>' : '')",
     "replace": "        + ''",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
