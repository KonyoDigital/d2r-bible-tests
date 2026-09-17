# -*- coding: utf-8 -*-
"""v3286 — THE VAULT MUST ACCOUNT FOR EVERY ITEM IT HOLDS.

Konyo, 2026-09-17, at a screenshot of the Vault: *"this is still here 200+ items that should not
be"*. The vault drew lockers and a dock and never once said how many things it holds, so "200+"
had no referent on screen — he and I could not point at the same number, and the measurement that
settled it had to come off `/api/vault_population` rather than off the surface he was looking at.

MEASURED on his board, 2026-09-18: **222 owned = 173 filed + 49 loose**, and the 49 split
**31 set pieces / 18 other**. The locker counts sum exactly (68+64+10+9+9+7+5+1 = 173).

⚠ THE GUARD THAT MATTERS IS THE THIRD ONE. The line is only worth having if its parts cannot
drift from its whole, and the way that is guaranteed is that **every figure is derived by
SUBTRACTION from the two pools renderVault already built** — never counted independently. An
independent tally is free to disagree with the thing it describes, which is the exact defect
class this panel exists to end. filed + loose == pool and pool + shared == owned, by
construction rather than by luck.

⚠ It deliberately does NOT restate why the loose items are loose. v3250 already put the sorter's
own verdict on the dock bar ("every one is a discard suggestion — Auto-Sort will not throw items
away for you"), and a second sentence saying the same thing is how two sentences begin to
disagree. [[copy-drift]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# non-ASCII in the docstring and in the failure messages below is PRINTED on a failure; on a
# cp1255 console that crashes while REPORTING, so a clean tree would exit non-zero for a reason
# unrelated to the law. test_control's encoding gate catches this and caught it once already.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

from frame_authority import _executable_only  # noqa: E402

BIBLE = os.path.join(ROOT, "bible.html")


def _between(src, start, end, what):
    """Slice anchored on real bytes at BOTH ends — never a fixed-size window."""
    i = src.find(start)
    if i < 0:
        raise AssertionError("anchor START vanished for %s: %r" % (what, start[:70]))
    j = src.find(end, i + len(start))
    if j < 0:
        raise AssertionError("anchor END vanished for %s: %r" % (what, end[:70]))
    return src[i:j]


class TestTheVaultSaysItsOwnPopulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = io.open(BIBLE, encoding="utf-8").read()
        # ".js", not the real path: _executable_only dispatches on EXTENSION and an .html path
        # falls through to the python branch, where ast.parse throws and the source comes back
        # UNSTRIPPED. Do not "fix" that dispatch — frame_authority:738 uses the same helper to
        # decide which reels are referenced, and teaching it .html would make every reel id named
        # in a bible.html comment newly eligible for deletion.
        cls.code = _executable_only(cls.raw, ".js")

    def test_the_vault_has_a_place_to_say_its_population(self):
        self.assertIn('id="vault-pop"', self.raw,
                      "the population line has no element, so nothing can render it")

    def test_render_vault_actually_fills_it(self):
        blk = self._fill_block()
        self.assertIn("getElementById('vault-pop')", blk,
                      "renderVault does not reach the population element, so the markup is inert "
                      "— present on the page and never written to")

    def test_every_figure_is_derived_from_the_pools_not_counted_again(self):
        """The one that stops the parts drifting from the whole."""
        blk = self._fill_block()
        self.assertIn("poolAll.length - pool.length", blk,
                      "the shared-stash figure is not derived from the two pools, so it is free "
                      "to disagree with them")
        self.assertIn("pool.length - unsorted.length", blk,
                      "the FILED figure is counted independently instead of being the remainder, "
                      "so filed + loose is no longer guaranteed to equal the pool — which is the "
                      "whole reason this line is trustworthy")

    def _fill_block(self):
        # both anchors are EXECUTABLE: a comment anchor cannot survive _executable_only
        return _between(
            self.code,
            "var unsorted = pool.filter(function(n){ return !assign[n] && !isSharedStash(n); });",
            "window._menuAscendingFraction",
            "the v3286 population fill")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "renaming the element leaves the line with nowhere to render",
        "file": "bible.html",
        "find": '      <div id="vault-pop" class="vault-pop"></div>',
        "replace": '      <div id="vault-pop-GONE" class="vault-pop"></div>',
        "matches": 1,
    },
    {
        "why": "pointing the fill at another id makes the markup inert — there, and never written",
        "file": "bible.html",
        "find": "      var _pEl = document.getElementById('vault-pop');",
        "replace": "      var _pEl = document.getElementById('vault-pop-GONE');",
        "matches": 1,
    },
    {
        "why": "counting FILED independently lets the parts stop summing to the whole",
        "file": "bible.html",
        "find": "        var _filed  = pool.length - unsorted.length;",
        "replace": "        var _filed  = Object.keys(assign).length;",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
