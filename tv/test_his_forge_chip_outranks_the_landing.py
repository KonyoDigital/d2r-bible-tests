# -*- coding: utf-8 -*-
"""REG-3056 (GrokBot #230 6486545342, 04:30-04:58, a shadow of the Mac -> Runewords -> Crafts) - HIS CHIP OUTRANKS THE
AUTO-LANDING.

On a sealed chronicle (every runeword made) with a craft ready, the crafts room's v1411 auto-land and the chronicle's v2094
landing ran on EVERY render, so a click on ALL or COMPLETED snapped straight back to MAKE NOW: the room could not be read
past its landing. A landing now chooses the FIRST view only; once he picks a chip in a room, that room keeps his pick.
Driven on the whole page in node (vault_page_node - never a browser on his Mac): every runeword marked made, one craft's
rune and gem added through the Tools tab's own tally doors. RED_PROOF below.
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

CLAIM = "localStorage.setItem('d2r_ownerClaim', '*');\n"

BODY = r"""
var W = window, made = {};
Object.keys(RUNEWORD_TIP).forEach(function(n){ made[n] = 'Oct 1, 2026 · 10:00'; });
W.LSR.setItem('d2r_rwMade', JSON.stringify(made));
try { if (typeof rwMade !== 'undefined') { for (var k in made) rwMade[k] = made[k]; } } catch (e) {}
var c0 = CRAFTS[0], rec = c0.slots[Object.keys(c0.slots)[0]];
W.adjustRuneStash(rec.rune, 1); W.adjustGemStash(c0.gem, 1);
OUT.crafts = (W.forgeScan().crafts || []).length;
W.renderCrafts(); H.flush(60, 2); OUT.first = W._FORGE_VIEW;
W.forgeSetFilter('all', 'crafts'); H.flush(60, 2); OUT.all = W._FORGE_VIEW;
W.renderCrafts(); H.flush(60, 2); OUT.allAgain = W._FORGE_VIEW;
W.forgeSetFilter('completed', 'crafts'); H.flush(60, 2); W.renderCrafts(); H.flush(60, 2); OUT.completed = W._FORGE_VIEW;
W.renderForge(); H.flush(60, 2); OUT.chronFirst = W._FORGE_VIEW;
W.forgeSetFilter('all'); H.flush(60, 2); W.renderForge(); H.flush(60, 2); OUT.chronAfterAll = W._FORGE_VIEW;
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class HisForgeChipOutranksTheLanding(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.r = VPN.run(BODY, prelude=CLAIM, timeout=300)

    def test_the_landing_still_chooses_the_first_view(self):
        r = self.r
        self.assertEqual(r["__boot"]["errors"], [], r["__boot"])
        self.assertGreaterEqual(r["crafts"], 1, "PREMISE: no craft is ready, so the landing can never fire: %r" % r)
        self.assertEqual(r["first"], "now", "a sealed board with a ready craft no longer lands on MAKE NOW first: %r" % r)

    def test_his_all_and_completed_survive_a_render(self):
        r = self.r
        self.assertEqual((r["all"], r["allAgain"]), ("all", "all"), "his ALL in Crafts snapped back: %r" % r)
        self.assertEqual(r["completed"], "completed", "his COMPLETED in Crafts snapped back: %r" % r)


    def test_a_sealed_chronicle_still_lands_on_completed(self):
        """REG-3084 - REG-3056 stood the chronicle's v2094 landing aside too: v1630's sealed-card specs went red on CI (a click
        on Completed toggles to ALL, and the empty ALL of a sealed chronicle no longer landed back on Completed)."""
        r = self.r
        self.assertEqual(r["chronFirst"], "completed", "PREMISE: a sealed chronicle does not land on Completed: %r" % r)
        self.assertEqual(r["chronAfterAll"], "completed", "a sealed chronicle's empty ALL stayed ALL after his chip: %r" % r)


RED_PROOF = [
    {"why": "REG-3084 - his chip stands the CHRONICLE's sealed landing aside too, so a sealed chronicle's empty ALL never lands on Completed",
     "file": "bible.html",
     "find": "    if (!_isCrafts && _F==='all' && !total",
     "replace": "    if (!_forgeByHand.forge && !_isCrafts && _F==='all' && !total",
     "matches": 1, "needs": "node"},
    {"why": "REG-3056 - the crafts auto-land ignores his chip again, so ALL snaps back to MAKE NOW on a sealed board",
     "file": "bible.html",
     "find": "    if (!_byHand && (s.crafts||[]).length > 0 && _sealed691 && (_F==='all' || _F==='completed')){",
     "replace": "    if ((s.crafts||[]).length > 0 && _sealed691 && (_F==='all' || _F==='completed')){",
     "matches": 1, "needs": "node"},
    {"why": "REG-3056 - his chip is never recorded as his, so every render lands again",
     "file": "bible.html",
     "find": "    if (scope === 'crafts'){ _forgeByHand.crafts = true; ",
     "replace": "    if (scope === 'crafts'){ ",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
