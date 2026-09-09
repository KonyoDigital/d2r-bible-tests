#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎞🔒 THE REEL FLOOR AND THE FRAME FLOOR ARE ONE NUMBER, WRITTEN TWICE.

Konyo, 2026-09-10, after asking whether the prune was working: *"okay make it last 8"* — and, on
the rule itself, *"reswept and then delete and retired"*, so the extraction precondition STAYS. The
floor widened; it did not loosen.

⚠⚠ THE NUMBER LIVES IN TWO FILES AND GUARDS TWO DIFFERENT THINGS.

    reel_retention.KEEP_RECENT    the newest N REELS are never deleted
    frame_authority.KEEP_RECENT   the newest N reels never have FRAMES pruned out of them

They are the same promise at two depths. If the frame floor is the lower of the two, a reel the
retention rule swore never to touch can be quietly emptied of its frames — still on disk, still
listed, and worth nothing. A floor that only holds at one depth is not a floor.

MEASURED when this was written: both 8, and `plan()` still refuses to delete anything, because 38
of 41 reels on disk are sealed with 0 pages and the extraction precondition is deliberately kept.

[[copy-drift]] [[the-unjoined-end]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: E402  — this file prints 🎞 🔒 ⚠ ★
console_safe.enable()


RED_PROOF = [
    {
        "why": "drifting the FRAME floor below the REEL floor: the newest reels stay on disk, as "
               "promised, and are emptied of their frames anyway — the promise kept at one depth "
               "and broken at the other",
        "file": "frame_authority.py",
        "find": "KEEP_RECENT = 8            # never touch the newest EIGHT reels",
        "replace": "KEEP_RECENT = 5            # never touch the newest EIGHT reels",
        "matches": 1,
    },
    {
        "why": "putting the REEL floor back to the 5 he replaced. His instruction was 'okay make "
               "it last 8', and a floor that silently returns to its old value is the drift this "
               "gate exists to stop",
        "file": "reel_retention.py",
        "find": "KEEP_RECENT = 8          # never touch the newest EIGHT",
        "replace": "KEEP_RECENT = 5          # never touch the newest EIGHT",
        "matches": 1,
    },
]


def _const(filename, name):
    """The module-level int a file assigns to `name`, read by AST — never imported, never grepped.
    [[source-reading-guard]]"""
    src = io.open(os.path.join(HERE, filename), encoding="utf-8").read()
    found = [n.value.value for n in ast.walk(ast.parse(src))
             if isinstance(n, ast.Assign)
             and any(getattr(t, "id", "") == name for t in n.targets)
             and isinstance(n.value, ast.Constant) and isinstance(n.value.value, int)]
    return found


class TheTwoKeepFloorsAgree(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_the_frame_floor_is_never_below_the_reel_floor(self):
        """★★ The whole point. A reel kept but emptied is worth nothing."""
        reels = _const("reel_retention.py", "KEEP_RECENT")
        frames = _const("frame_authority.py", "KEEP_RECENT")
        self.assertEqual(1, len(reels), "reel_retention assigns KEEP_RECENT %d times" % len(reels))
        self.assertEqual(1, len(frames), "frame_authority assigns KEEP_RECENT %d times" % len(frames))
        self.assertGreaterEqual(
            frames[0], reels[0],
            "the FRAME floor is %d while the REEL floor is %d, so the newest %d reel(s) survive "
            "deletion and are stripped of their frames anyway — the promise kept at one depth and "
            "broken at the other" % (frames[0], reels[0], reels[0] - frames[0]))

    def test_they_are_the_SAME_number(self):
        """★★ Not merely ordered — one promise, so one value. Two numbers that happen to satisfy
        the inequality today will drift apart the next time one of them is edited alone."""
        self.assertEqual(_const("reel_retention.py", "KEEP_RECENT"),
                         _const("frame_authority.py", "KEEP_RECENT"),
                         "the two floors have drifted apart; they are one promise written twice")

    def test_it_is_HIS_number(self):
        """★ 8, on his 2026-09-10 instruction. A floor this repo lowers without being asked is a
        floor that stopped being his."""
        self.assertEqual([8], _const("reel_retention.py", "KEEP_RECENT"),
                         "the reel floor is no longer the 8 he asked for")

    def test_the_modules_AGREE_at_runtime_too(self):
        """★ Source and import must say the same thing — a constant can be reassigned below its
        declaration and the AST read would never know. [[the-unjoined-end]]"""
        import reel_retention as R
        import frame_authority as F
        self.assertEqual(R.KEEP_RECENT, F.KEEP_RECENT,
                         "imported: reel_retention says %r, frame_authority says %r"
                         % (R.KEEP_RECENT, F.KEEP_RECENT))
        self.assertEqual(R.KEEP_RECENT, _const("reel_retention.py", "KEEP_RECENT")[0],
                         "the source declares one value and the module carries another")


if __name__ == "__main__":
    unittest.main(verbosity=2)
