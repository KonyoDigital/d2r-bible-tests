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
        "find": "KEEP_RECENT = 16           # never touch the newest SIXTEEN reels",
        "replace": "KEEP_RECENT = 5            # never touch the newest SIXTEEN reels",
        "matches": 1,
    },
    {
        "why": "putting the REEL floor back to the 5 he replaced. His instruction was 'okay make "
               "it last 8', and a floor that silently returns to its old value is the drift this "
               "gate exists to stop",
        "file": "reel_retention.py",
        "find": "KEEP_RECENT = 16         # never touch the newest SIXTEEN",
        "replace": "KEEP_RECENT = 8          # never touch the newest SIXTEEN",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the sixteen he asked for holds even when the disk is under the recording floor, "
               "so keeping the extra hours stops the next one from filming",
        "file": "reel_retention.py",
        "find": "            return KEEP_RECENT_UNDER_PRESSURE\n",
        "replace": "            return KEEP_RECENT\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the console's deleting pass never asks the disk, so the pressure rule is plumbing "
               "with no tap",
        "file": "control_app.py",
        "find": "    p = _rr.plan(hist, free_mb=None, keep_recent=_keep)\n",
        "replace": "    p = _rr.plan(hist, free_mb=None)\n",
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
        """★ 16, on his 2026-09-29 instruction (8 on 2026-09-10): *"if its less than 8 double the amount to
        16 reels.. FIFO same style just that instead of 8 last reels it reads 16"* - eight hourly reels
        measured ~3-4 GB on his Mac. A floor this repo lowers without being asked stopped being his."""
        self.assertEqual([16], _const("reel_retention.py", "KEEP_RECENT"),
                         "the reel floor is no longer the 16 he asked for")

    def test_under_the_recording_floor_the_extra_eight_go_first(self):
        """2026-09-29 — sixteen full hours is ~8 GB on his Mac (14 GB free that night), and below
        ON_AIR_FLOOR_GB the console refuses to film. So the deleting pass keeps the old eight while the disk
        is under the floor; an UNKNOWN disk keeps all sixteen."""
        import reel_retention as R
        self.assertEqual(R.keep_recent_for(20.0, 8.0), 16)
        self.assertEqual(R.keep_recent_for(8.0, 8.0), 16, "AT the floor is not below it")
        self.assertEqual(R.keep_recent_for(6.5, 8.0), 8,
                         "under the recording floor the extra hours still hold - the next one cannot film")
        self.assertEqual(R.keep_recent_for(None, 8.0), 16, "an unreadable disk was treated as a full one")
        self.assertEqual(R.KEEP_RECENT_UNDER_PRESSURE, 8)
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        i = src.index("def _retention_once(")
        body = src[i:src.index("\ndef ", i + 10)]
        self.assertIn("_rr.keep_recent_for(free_gb, ON_AIR_FLOOR_GB)", body,
                      "the deleting pass does not ask the disk - the pressure rule has no tap")
        # ⚠⚠ REG-1668 - ASK THE PLAN CALL ITSELF. `keep_recent=_keep` appears SEVEN times in this function now (every
        # drain call carries it too), so "the text is somewhere in the body" stayed true with the plan call stripped
        # of it. MEASURED: this proof went BLIND on his ALT first, and then on the Mac too once it was re-run - the
        # Mac's PROVEN was from before the drain calls existed. [[a-presence-law-is-not-a-reachability-law]]
        fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "_retention_once")
        plans = [c for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                 and c.func.attr == "plan" and isinstance(c.func.value, ast.Name) and c.func.value.id == "_rr"]
        self.assertEqual(len(plans), 1, "PREMISE: the deleting pass plans once - re-point this law")
        kw = {k.arg: k.value for k in plans[0].keywords}
        self.assertTrue(isinstance(kw.get("keep_recent"), ast.Name) and kw["keep_recent"].id == "_keep",
                        "the pass asks the disk and then plans without the answer")

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
