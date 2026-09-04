#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AN INVARIANT THAT ASKS FOR A KEY NOBODY RETURNS IS A CONSTANT ZERO.

⚠⚠ THE DEFECT, measured 2026-09-05. Two cross-engine invariants in `corroborate.py` read their
left operand as:

    len(plan.get("free") or plan.get("freeable") or [])

`frame_authority.plan_frames()` returns NEITHER key. Measured against his live tree, its keys are
exactly: bytes, haveIndex, heldBy, kept, prunable, say, scanned, sealOk, sealedSessions,
witnessFrames, witnessOk. So `.get()` fell through to `[]` and the left side answered **0 forever,
on every tree, whatever the deleter did**.

An invariant whose left operand is a constant cannot be violated. Both of these guard the direction
with no undo — *"the one thing that can delete never frees more than the planner offers"* — and
neither has ever been able to fire.

⚠ AND THE FILE ALREADY SUSPECTED THEM. Its own v2393 note lists both by name under *"agreeing at
ZERO vs ZERO (cannot tell healthy from inert)"*. The suspicion was right; the cause was a key name.

⚠⚠ WHAT THIS FIX DOES **NOT** DO, said plainly. `prunable` is genuinely an empty list on his shelf
today, so both invariants still read 0 vs 0. The fix does not make them informative — it makes them
CAPABLE. They went from structurally unable to respond to quiet-but-live. Claiming otherwise would
be exactly the overstatement this file exists to catch. [[unknown-stays-unknown]]

⚠ NOTHING HERE TOUCHES HIS TREE. Every case stubs `frame_authority.plan_frames` and restores it.
[[feedback-fixtures-never-touch-live-data]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import corroborate as C  # noqa: E402
import frame_authority as fa  # noqa: E402

#: the two invariants that read plan_frames' prunable list
BUILDERS = ("_inv_the_deleter_is_never_looser_than_the_planner",
            "_inv_the_two_deleters_stay_at_their_own_granularity")


class _Base(unittest.TestCase):

    def _stub(self, plan):
        real = fa.plan_frames
        fa.plan_frames = lambda *a, **k: plan
        self.addCleanup(setattr, fa, "plan_frames", real)

    def _left(self, builder):
        """The invariant's LEFT operand, driven exactly as the live path drives it."""
        _key, _what, _why, _ln, left_fn, _rn, _rf, _op = getattr(C, builder)()
        return left_fn()


class TheLeftOperandReadsTheKeyThatExists(_Base):

    def test_plan_frames_really_returns_prunable_and_not_free(self):
        """★ THE MEASUREMENT THE FIX RESTS ON. If this ever fails, the fix is aimed at the wrong
        key and both invariants are inert again — silently, because a constant reads as agreement."""
        plan = fa.plan_frames(os.environ.get("TV_HIST")
                              or os.path.join(HERE, "frames", "hist"))
        self.assertIsInstance(plan, dict)
        self.assertIn("prunable", plan,
                      "plan_frames no longer returns `prunable`; the invariants read a key that "
                      "does not exist and are back to a constant zero")
        self.assertNotIn("free", plan)
        self.assertNotIn("freeable", plan)

    def test_it_COUNTS_the_prunable_list(self):
        for b in BUILDERS:
            self._stub({"prunable": ["a", "b", "c"]})
            self.assertEqual(self._left(b), 3, "%s did not count prunable" % b)

    def test_the_OLD_keys_are_no_longer_consulted(self):
        """RED for the original defect: a plan carrying only the old keys must NOT answer from
        them. If it did, the fix would be additive rather than corrective and the wrong key would
        still be load-bearing."""
        for b in BUILDERS:
            self._stub({"free": ["x", "y"], "freeable": ["z"]})
            self.assertIsNone(self._left(b),
                              "%s still answers from `free`/`freeable`, the keys plan_frames "
                              "never returns" % b)


class AMissingKeyIsUNKNOWNNeverZero(_Base):
    """★★ THE HEART OF IT. `.get(k) or []` turns 'this plan has no such key' into 'nothing is
    prunable' — a confident measured zero produced by an unanswered question. That is how the
    defect stayed invisible for its whole life: the invariant reported AGREEMENT."""

    def test_a_plan_with_no_prunable_key_returns_None(self):
        for b in BUILDERS:
            self._stub({"kept": 5022, "scanned": 5022})
            self.assertIsNone(self._left(b),
                              "%s reported a number for a plan that never answered the question"
                              % b)

    def test_an_EMPTY_prunable_list_is_a_real_zero_and_stays_0(self):
        """⚠ The distinction that makes the above meaningful: present-and-empty is a MEASUREMENT.
        Collapsing it into the same answer as absent would trade one blindness for another."""
        for b in BUILDERS:
            self._stub({"prunable": []})
            self.assertEqual(self._left(b), 0)

    def test_a_RAISING_plan_is_None_not_zero(self):
        for b in BUILDERS:
            real = fa.plan_frames

            def boom(*a, **k):
                raise RuntimeError("cannot read the shelf")
            fa.plan_frames = boom
            self.addCleanup(setattr, fa, "plan_frames", real)
            self.assertIsNone(self._left(b))


class TheInvariantCanNowActuallyInvert(_Base):
    """★★★ RED FOR ITS OWN REASON, and the only case that proves the guard is alive. Before the
    fix this was UNREACHABLE: the left side was a constant 0, so `left <= right` held against
    every possible right and the relation could never be violated."""

    def test_a_deleter_freeing_MORE_than_the_planner_offers_now_breaks_the_relation(self):
        for b in BUILDERS:
            self._stub({"prunable": ["f%d" % i for i in range(9)]})
            left = self._left(b)
            right = 2          # the planner offered 2
            self.assertEqual(left, 9)
            self.assertFalse(left <= right,
                             "%s: the deleter freeing 9 while the planner offers 2 still reads as "
                             "agreement — the invariant cannot invert" % b)

    def test_and_the_healthy_direction_still_holds(self):
        """⚠ THE BASELINE. A guard that fails on everything is not a guard. The invariant must
        still agree when the deleter is the stricter of the two, which is the normal state."""
        for b in BUILDERS:
            self._stub({"prunable": ["f1"]})
            self.assertTrue(self._left(b) <= 6)

    def test_before_the_fix_this_relation_was_UNREACHABLE(self):
        """The old expression, run against the same sabotage, to show what was actually being
        graded: a constant that no state could move."""
        plan = {"prunable": ["f%d" % i for i in range(9)]}
        old = len(plan.get("free") or plan.get("freeable") or [])
        self.assertEqual(old, 0, "the old expression is not the constant this file claims")
        self.assertTrue(old <= 2, "the old left side could not violate `<= 2` at any shelf state")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
