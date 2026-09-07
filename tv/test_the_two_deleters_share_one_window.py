# -*- coding: utf-8 -*-
"""SWEPT AFTER v2752 (no version bump — this adds a law, it ships no behaviour change)

TWO DELETERS, TWO INDEPENDENT `KEEP_RECENT = 5`, AND NOTHING SAYS THEY MUST AGREE.

Found by sweeping for the shape of the v2752 defect (a constant that outlived the instrument it was
derived against). This is its cross-module twin: ONE rule, written down TWICE.

    frame_authority.py:52   KEEP_RECENT = 5   # never touch the newest five reels, whatever any ledger says
    reel_retention.py:47    KEEP_RECENT = 5   # never touch the newest five, whatever the ledgers say

Same rule, near-identical prose, two definitions, no link. They agree today by coincidence of
authorship, and `reel_retention` already imports `frame_authority` in three places — so the drift is
not prevented by any structural barrier, only by nobody having edited one of them yet.

=== ⚠⚠ WHY THIS IS NOT SYMMETRIC, WHICH IS THE WHOLE REASON IT IS WORTH A LAW ===
The two modules delete DIFFERENT THINGS:
    reel_retention.plan       -> removes whole REEL directories
    frame_authority.plan_frames -> strips FRAMES from reels it considers unprotected

Raise retention's window to 10 to be safer with his footage and leave frame_authority at 5, and
reels 6..10 survive as directories **while being gutted of their frames**. The reel list still shows
them. The disk figure still drops. Protection reads as INCREASED and is in fact partial — the worst
available outcome, because it is the one nobody goes looking for.

The other direction is merely wasteful: frames held inside reels that get deleted whole anyway.

⇒ The dangerous direction is retention > frame_authority, so this law demands EQUALITY rather than
an inequality that would quietly permit it.

=== WHY EQUALITY, AND NOT A REFACTOR TO ONE DEFINITION ===
The obvious fix is `from frame_authority import KEEP_RECENT`. Rejected: `reel_retention` imports
frame_authority LAZILY, inside three separate functions, and a module-level import would change that
module's load-time dependency graph to close a gap that a one-line assertion closes with no risk to
the deleter path. A law here costs nothing and cannot itself break a prune.
[[copy-drift]] [[the-unjoined-end]] [[label-outlived-referent]]
"""
import ast
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import frame_authority as FA  # noqa: E402
import reel_retention as RR  # noqa: E402


class TheTwoDeletersShareOneWindow(unittest.TestCase):

    # ── the law can find BOTH of its subjects ─────────────────────────────────────────────────
    def test_the_guard_can_find_both_constants_AT_ALL(self):
        """⚠ A law whose subject is gone passes having compared nothing — and this one compares two
        things, so it can go vacuous in two ways instead of one."""
        for mod, name in ((FA, "frame_authority"), (RR, "reel_retention")):
            self.assertTrue(hasattr(mod, "KEEP_RECENT"),
                            "%s.KEEP_RECENT is gone or renamed. Fix this guard before trusting a "
                            "green from it." % name)
            self.assertIsInstance(getattr(mod, "KEEP_RECENT"), int,
                                  "%s.KEEP_RECENT is not a number" % name)

    # ── ⚠⚠ THE LAW ────────────────────────────────────────────────────────────────────────────
    def test_the_two_deleters_protect_the_SAME_reels(self):
        self.assertEqual(
            FA.KEEP_RECENT, RR.KEEP_RECENT,
            "The two deleters disagree about how many recent reels are untouchable "
            "(frame_authority=%d, reel_retention=%d). If retention's window is the LARGER one, "
            "reels between the two figures survive as directories while frame_authority strips "
            "their frames: the reel list still shows them, the disk figure still drops, and the "
            "protection reads as increased while being partial."
            % (FA.KEEP_RECENT, RR.KEEP_RECENT))

    def test_the_window_is_not_zero(self):
        """A shared value of 0 would satisfy equality while removing the protection entirely — the
        one way this law could be 'satisfied' by deleting the thing it guards."""
        self.assertGreaterEqual(FA.KEEP_RECENT, 1,
                                "the recent-reel shield is zero, so the newest recording is "
                                "prunable the moment it exists")

    # ── the default is the DRIFT SURFACE, so pin it ───────────────────────────────────────────
    def test_neither_module_hardcodes_a_DIFFERENT_number_at_its_call_site(self):
        """Both expose `keep`/`keep_recent` parameters defaulting to the constant. A call site
        passing a literal instead would drift without either constant changing — the same defect
        one level down, and invisible to the assertion above."""
        for fname, params in (("frame_authority.py", ("keep=KEEP_RECENT",)),
                              ("reel_retention.py", ("keep_recent=KEEP_RECENT",))):
            src = io.open(os.path.join(HERE, fname), encoding="utf-8").read()
            for p in params:
                self.assertIn(p, src,
                              "%s no longer defaults its recent-window parameter to the constant, "
                              "so the constant can be correct while the running default is not"
                              % fname)

    # ── ⚠ BEHAVIOURAL, NOT MERELY TEXTUAL ─────────────────────────────────────────────────────
    def test_the_shield_actually_holds_the_newest_reels(self):
        """⚠ THE CONSTANT AGREEING IS NOT THE PROTECTION WORKING. `recent_reels` sorts on a
        timestamp parsed out of the directory NAME (`reel_s_<ts>_<n>` -> split("_")[2]); a rename
        or a reel whose name does not carry a parseable stamp sorts to infinity and would silently
        occupy a shield slot. This runs the real function over real directories.

        Host-independent on purpose: `recent_reels` only globs and sorts, so unlike
        `reel_retention.plan` (which reads a witness index from HERE, not from its hist_dir — the
        v2750 host-dependency) it cannot come out differently on CI than it does here."""
        tmp = tempfile.mkdtemp(prefix="keeprecent_")
        try:
            names = ["reel_s_17870000000%02d_100" % i for i in range(8)]
            for n in names:
                os.makedirs(os.path.join(tmp, n))
            held = FA.recent_reels(tmp)
            self.assertEqual(FA.KEEP_RECENT, len(held),
                             "the shield held %d reels, not KEEP_RECENT=%d"
                             % (len(held), FA.KEEP_RECENT))
            newest = {os.path.join(tmp, n) for n in names[-FA.KEEP_RECENT:]}
            self.assertEqual(newest, set(held),
                             "the shield held the wrong reels — it is not ordering by the "
                             "timestamp in the directory name")
            oldest = os.path.join(tmp, names[0])
            self.assertNotIn(oldest, held,
                             "the oldest reel is inside the shield, so nothing is ever prunable")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_an_empty_shelf_yields_an_empty_shield_not_a_crash(self):
        tmp = tempfile.mkdtemp(prefix="keeprecent_empty_")
        try:
            self.assertEqual(set(), FA.recent_reels(tmp))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_both_modules_still_parse(self):
        for f in ("frame_authority.py", "reel_retention.py"):
            ast.parse(io.open(os.path.join(HERE, f), encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main(verbosity=2)
