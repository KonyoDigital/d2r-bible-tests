# -*- coding: utf-8 -*-
"""#270 (REG-2032) - A TOOLTIP-JUDGE READ SAYS ITS PLACE IS UNKNOWN; IT NEVER CLAIMS HE DOES NOT HOLD THE ITEM.

His question, 2026-10-08 (Session 1, the Highlord's Wrath tooltip open on screen): "did any retro analyzer read these
reels ... this highlords amulet was easily seen it was registered to the vault? to my equipment lock". MEASURED on his frame
(read-only): the tooltip hangs off his EQUIPPED amulet slot - he was wearing it. The KAI tooltip judge registered it with
no place and the lane name 'kai' as its scene, and the board's holding route said "read during kai, which does not show
that you hold it" - a claim the frame contradicts. The judge records the item and never where it sat, so the honest
sentence is that the place is UNKNOWN and this read alone files nothing. The route itself is unchanged (a placing look
decides; worn gear is locked to his MAIN, never a mule).

Driven on the SHIPPED page in a scratch Chrome. NO CHROME AT ALL = a declared skip, never a pass.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_a_sweep_never_reticks_what_he_unticked as H  # noqa: E402  (its Board drives the shipped page)

_B = {}


def board():
    if "b" not in _B:
        _B["b"] = H.Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class ATooltipJudgeReadNeverClaimsHeDoesNotHoldIt(unittest.TestCase):

    def test_a_kai_read_with_no_place_says_the_place_is_unknown(self):
        o = board().run("var R = window._vaultHoldingRoute;"
                        "OUT.kai = R(null, 'kai', \"Highlord's Wrath\");"
                        "OUT.gameplay = R(null, 'gameplay', \"Highlord's Wrath\");"
                        "OUT.worn = R('equipped', 'kai', \"Highlord's Wrath\");")
        k = o["kai"]
        self.assertEqual(k.get("route"), "not-held", "a tooltip-judge read alone started filing: %r" % k)
        self.assertNotIn("does not show that you hold it", k.get("why", ""), "the board still claims he does not hold it: %r" % k)
        self.assertIn("not where it sat", k.get("why", ""), k)
        # the control: a real scene keeps its own sentence, and a placed read is decided by its place
        self.assertIn("does not show that you hold it", o["gameplay"].get("why", ""), o["gameplay"])
        self.assertEqual(o["worn"].get("route"), "vault", o["worn"])


RED_PROOF = [
    {"why": "REG-2032 - a tooltip-judge read claims again that it shows he does not hold the item",
     "file": "bible.html",
     "find": "    if (s === 'kai')\n      return { route: 'not-held', why: 'read by the tooltip judge,",
     "replace": "    if (false)\n      return { route: 'not-held', why: 'read by the tooltip judge,",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
