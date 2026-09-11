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
import reel_retention as rr  # noqa: E402

#: the two invariants that read plan_frames' prunable list
BUILDERS = ("_inv_the_deleter_is_never_looser_than_the_planner",
            "_inv_the_two_deleters_stay_at_their_own_granularity")


class _Base(unittest.TestCase):

    def _stub(self, plan, offered=()):
        """Both engines, because the corrected left operand is a JOIN of the two.

        ⚠⚠ v2905 — THE SECOND HALF IS NOT OPTIONAL. This fed only frame_authority, which is exactly
        how the left side came to be measured in a unit reel_retention does not speak: FRAME FILES
        against the planner's CHRONICLE PAGES. A stub that still fed one engine would let that
        return without a single test going red.
        ⚠ EVERY CANDIDATE BELOW CARRIES pages=0 ON PURPOSE. `pages` is no longer an operand; if a
        future edit reintroduces it, these fixtures give it nothing to read and the tests go red.
        """
        real_fa, real_rr = fa.plan_frames, rr.plan
        fa.plan_frames = lambda *a, **k: plan
        rr.plan = lambda *a, **k: {"ok": True,
                                   "candidates": [{"reel": r, "pages": 0} for r in offered]}
        self.addCleanup(setattr, fa, "plan_frames", real_fa)
        self.addCleanup(setattr, rr, "plan", real_rr)

    def _frames(self, **per_reel):
        """`reel_a=5` -> five frame paths inside reel_a. The count of PATHS and the count of REELS
        are deliberately different in every fixture, so a test cannot pass under both units."""
        out = []
        for reel, n in per_reel.items():
            out += [os.path.join("/hist", reel, "f_%d.jpg" % i) for i in range(n)]
        return out

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

    def test_it_counts_REELS_OUTSIDE_THE_OFFER_and_not_frames(self):
        """★ THE OPERAND SHAPE, PINNED — not the number. Nine frame files across two reels, neither
        offered: the answer must be 2. If it is ever 9 again, the left side has gone back to
        counting FRAMES and the relation is comparing units.

        MEASURED on his tree 2026-09-10, which is why the SHAPE is the subject: frames exceeded
        chronicle pages on 24 of 24 reels (3,151 vs 676), so a frame-count left side sat above the
        page-count right side's own CEILING and the relation could not hold in any world. The old
        assertion pinned 3 == 3 and would have passed forever under either unit.
        [[label-outlived-referent]]
        """
        for b in BUILDERS:
            self._stub({"prunable": self._frames(reel_a=5, reel_b=4)}, offered=())
            left = self._left(b)
            self.assertEqual(left, 2, "%s did not count REELS outside the offer" % b)
            self.assertNotEqual(left, 9,
                                "%s is counting FRAME FILES again — that is the units error this "
                                "file exists to keep out" % b)

    def test_the_planners_PAGE_COUNT_is_no_longer_an_operand(self):
        """★★ THE UNITS ERROR ITSELF, RED. The right side used to be sum(candidate["pages"]) —
        chronicle pages, the READER's output, a quantity the frame deleter never produces. Here 400
        frames sit inside the one reel the planner offered, at pages=0. The answer must move with
        the OFFER and never with the pages."""
        for b in BUILDERS:
            self._stub({"prunable": self._frames(reel_a=400)}, offered=("reel_a",))
            self.assertEqual(self._left(b), 0,
                             "%s: 400 frames inside the ONE reel the planner offered is not a "
                             "violation at any page count" % b)

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

    # ── v2943 (#63) — the pair that was permanently red ────────────────────────────────────────
    def _eagle_expectation(self, eagle):
        """The `eagle-ran-every-check` right() operand under a given _EAGLE state. -> int|None"""
        import control_app as ca, corroborate as CO
        inv = None
        for b in CO.BUILDERS:
            try:
                t = b()
            except Exception:
                continue
            if isinstance(t, tuple) and t and t[0] == "eagle-ran-every-check":
                inv = t
                break
        self.assertIsNotNone(inv, "the eagle-ran-every-check invariant is gone — re-derive this law")
        right = [x for x in inv if callable(x)][-1]
        was = getattr(ca, "_EAGLE", None)
        ca._EAGLE = eagle
        try:
            return right()
        finally:
            ca._EAGLE = was

    def test_a_pass_that_SKIPPED_periodic_is_not_expected_to_have_run_it(self):
        """⚠⚠ A PERMANENTLY-RED PAIR CANNOT REPORT A DROPPED CHECK. The unattended eagle tick skips
        PERIODIC on 5 of every 6 passes, and this expectation counted the roster minus SLOW only —
        so it was one too high almost always. MEASURED on his tree before the fix: "rows in the
        last eagle pass says 53 and rows that pass was expected to cover says 54". That is the
        cry-wolf shape: a finding he learns to skip is worse than no finding.
        [[feedback-threshold-above-the-ceiling]]"""
        import console_doctor as cd
        cheap = len([c for c in cd.CHECKS if c[0] not in cd.SLOW])
        per = len([c for c in cd.CHECKS if c[0] in getattr(cd, "PERIODIC", ()) and c[0] not in cd.SLOW])
        self.assertGreater(per, 0, "no PERIODIC check is also cheap — re-derive this law")
        skipped = self._eagle_expectation({"checked": 1, "slow": False, "periodic": False})
        included = self._eagle_expectation({"checked": 1, "slow": False, "periodic": True})
        self.assertEqual(cheap - per, skipped,
                         "a pass that skipped PERIODIC is still expected to have run it: %r" % skipped)
        self.assertEqual(cheap, included,
                         "a pass that INCLUDED periodic is under-expected: %r" % included)
        self.assertNotEqual(skipped, included,
                            "the expectation does not depend on `periodic` at all, so the pair is "
                            "back to disagreeing on 5 of every 6 passes")

    def test_a_LEGACY_record_stays_GRADEABLE(self):
        """⚠⚠ THE RULE I GOT WRONG, AND THE GATE CAUGHT IT. v2943 returned UNKNOWN for a record
        with no `periodic`, on the "absent is not False" principle — and five tests in
        `TestV2394TheEagleCanBeGradedFromOUTSIDEItsOwnProcess` went red, including
        `test_a_PRE_v2409_record_with_no_primary_key_is_still_read`, whose own message reads
        *"refused for lacking a key it COULD NOT HAVE HAD"*.

        Backward compatibility with an older console's record is a DELIBERATE contract and it
        outranks the newer principle. A legacy record keeps the pre-v2943 expectation; the cost is
        that it can still read red on a pass that skipped PERIODIC — the state it was already in —
        and it self-corrects the moment the console writes one record carrying the key."""
        import console_doctor as cd
        cheap = len([c for c in cd.CHECKS if c[0] not in cd.SLOW])
        got = self._eagle_expectation({"checked": 1, "slow": False})
        self.assertEqual(cheap, got,
                         "a legacy record without `periodic` is no longer gradeable (%r) — that "
                         "refuses a record for lacking a key it could not have had" % (got,))

    def test_the_DURABLE_record_persists_what_the_reader_needs(self):
        """⚠⚠ THE UNJOINED END. `periodic` was computed and stored into the in-memory _EAGLE and
        then DROPPED by the disk write — and that file is the ONLY thing an out-of-process reader
        (this module, the gates, CI) can see. PARSED, not grepped. [[the-unjoined-end]]"""
        import ast as _ast, io as _io, os as _os
        here = _os.path.dirname(_os.path.abspath(__file__))
        src = _io.open(_os.path.join(here, "control_app.py"), encoding="utf-8").read()
        found = False
        for node in _ast.walk(_ast.parse(src)):
            if not isinstance(node, _ast.Dict):
                continue
            keys = {k.value for k in node.keys
                    if isinstance(k, _ast.Constant) and isinstance(k.value, str)}
            if {"checked", "rows", "slow", "needsYou"}.issubset(keys):
                found = True
                self.assertIn("periodic", keys,
                              "the eagle's durable record drops `periodic` (%s) — the reader "
                              "cannot then say which roster the pass was measured against"
                              % sorted(keys))
        self.assertTrue(found, "the eagle's durable dict literal is gone — re-derive this law")

    def test_the_durable_read_hands_back_ONE_shape(self):
        """⚠ ONE READ, ONE POLICY — this module's own rule. Every return of `_durable_pass` must
        have the same arity, or a caller unpacking it gets `tuple index out of range` on one path
        only. MEASURED during this fix: widening six returns and missing the seventh produced
        exactly that, and the pair reported 'cannot be asked' for the wrong reason."""
        import ast as _ast, io as _io, os as _os
        here = _os.path.dirname(_os.path.abspath(__file__))
        src = _io.open(_os.path.join(here, "corroborate.py"), encoding="utf-8").read()
        fn = [n for n in _ast.walk(_ast.parse(src))
              if isinstance(n, _ast.FunctionDef) and n.name == "_durable_pass"][0]
        arities = {len(r.value.elts) for r in _ast.walk(fn)
                   if isinstance(r, _ast.Return) and isinstance(r.value, _ast.Tuple)}
        self.assertEqual(1, len(arities),
                         "_durable_pass returns tuples of differing length %s — one caller path "
                         "raises where the others do not" % sorted(arities))

    def test_a_deleter_freeing_from_a_reel_the_planner_HOLDS_breaks_the_relation(self):
        """★★★ THE INVERSION, IN THE UNIT THE LAW IS ACTUALLY WRITTEN IN. The reel-set equivalent of
        "the deleter frees more than the planner offers" is: it frees a frame from a reel that is
        NOT in the offer. The planner offers reel_a; the deleter reaches into reel_b and reel_c as
        well, so two reels are freed outside the offer and `left <= right` must be FALSE.

        ⚠ THIS IS NOT THE OLD TEST WITH NEW NUMBERS. The old one asserted 9 <= 2 was false, which is
        true of any two integers in that order and never once looked at WHICH reels — a deleter
        taking 1 frame from a held reel while the planner offered 50 pages passed it clean.
        MEASURED on his tree today the corrected operand reads 3: three reels the frame deleter
        would free from that the planner is still holding.
        """
        for b in BUILDERS:
            self._stub({"prunable": self._frames(reel_a=3, reel_b=1, reel_c=1)},
                       offered=("reel_a",))
            left, right = self._left(b), 0
            self.assertEqual(left, 2,
                             "%s did not name the two reels freed outside the offer" % b)
            self.assertFalse(left <= right,
                             "%s: the deleter reaching into two reels the planner is still holding "
                             "still reads as agreement — the invariant cannot invert" % b)

    def test_an_UNREADABLE_PLANNER_is_UNKNOWN_never_zero(self):
        """★★ THE NEW HALF. The corrected left operand needs BOTH engines, so there is now a second
        unanswerable question: the planner's offer. Subtracting an unknown set would silently answer
        "nothing is outside the offer" — a confident zero produced by a question nobody answered,
        the exact defect this file was written for. [[unknown-stays-unknown]]"""
        for b in BUILDERS:
            self._stub({"prunable": self._frames(reel_a=3)})
            rr.plan = lambda *a, **k: {"ok": False, "why": "the shelf would not read"}
            self.assertIsNone(self._left(b),
                              "%s reported a number while the planner's offer was unreadable" % b)
        for b in BUILDERS:
            self._stub({"prunable": self._frames(reel_a=3)})
            rr.plan = lambda *a, **k: {"ok": True, "candidates": None}
            self.assertIsNone(self._left(b),
                              "%s treated a MISSING candidate list as an empty offer" % b)

    def test_and_the_healthy_direction_still_holds(self):
        """⚠ THE BASELINE. A guard that fails on everything is not a guard. The invariant must
        still agree when the deleter is the stricter of the two, which is the normal state."""
        for b in BUILDERS:
            self._stub({"prunable": self._frames(reel_a=6, reel_b=2)},
                       offered=("reel_a", "reel_b", "reel_c"))
            self.assertEqual(self._left(b), 0)
            self.assertTrue(self._left(b) <= 0)

    def test_before_the_fix_this_relation_was_UNREACHABLE(self):
        """The old expression, run against the same sabotage, to show what was actually being
        graded: a constant that no state could move."""
        plan = {"prunable": ["f%d" % i for i in range(9)]}
        old = len(plan.get("free") or plan.get("freeable") or [])
        self.assertEqual(old, 0, "the old expression is not the constant this file claims")
        self.assertTrue(old <= 2, "the old left side could not violate `<= 2` at any shelf state")


RED_PROOF = [
    {
        "why": "The tamper deletes the refusal at the top of BOTH cross-engine invariants' left operands in corroborate.py — `_inv_the_deleter_is_never_looser_than_the_planner` and `_inv_the_two_deleters_stay_at_their_own_granularity`. Each wraps its `fa.plan_frames(hist)` call in a try/except that returns None when the shelf cannot be read; the tamper turns that into `return 0`. That is the exact defect class the whole gate exists to catch: an unanswerable question rendered as a confident measured zero. Because the relation both invariants publish is `left <= right`, a constant 0 on the left can never invert, so an unreadable shelf would silently report AGREEMENT on the one direction with no undo (the thing that can delete his footage). The anchor is executable code inside the two `left()` closures — not a comment, not a message string, not a shared constant — and it is the only site the raising-plan law reads: the two left() try/except blocks are the only `fa.plan_frames` call sites in the file (2 occurrences, both replaced), while the `rr.plan` except blocks have different text and are untouched. Measured: untampered the gate printed OK (9 tests); with all 2 occurrences replaced it printed FAILED (failures=1) with exactly one law red, and that law failed ALONE under `python3 -m unittest test_corroborate_operands.AMissingKeyIsUNKNOWNNeverZero.test_a_RAISING_plan_is_None_not_zero` with `AssertionError: 0 is not None`, so the red is not leftover state from a sibling test. `git checkout -- corroborate.py` restored the file (clean `git status`) and the gate printed OK again.  MEASURED: untampered OK; tampered (all 2 match(es)) FAILED (failures=1); reddened law AMissingKeyIsUNKNOWNNeverZero.test_a_RAISING_plan_is_None_not_zero; that law ALONE FAILED (failures=1) — FAIL: test_a_RAISING_plan_is_None_not_zero (test_corroborate_operands.AMissingKeyIsUNKNOWNNeverZer.",
        "file": 'corroborate.py',
        "find": '            plan = fa.plan_frames(hist)\n        except Exception:\n            return None\n',
        "replace": '            plan = fa.plan_frames(hist)\n        except Exception:\n            return 0\n',
        "matches": 2,
    },
    {
        "why": "v2943/A — drops `periodic` from the eagle's durable record, the ONLY thing an out-of-process reader can see. The corroborator then cannot say which roster a pass was measured against and the pair goes permanently UNKNOWN — an alarm that can never report a genuinely dropped check.",
        "file": 'control_app.py',
        "find": '                       "periodic": _EAGLE.get("periodic"),\n',
        "replace": '',
        "matches": 1,
    },
    {
        "why": "v2943/B — stops subtracting PERIODIC, so a pass that skipped it is still expected to have run it. MEASURED on his tree before the fix: 'rows says 53 and expected 54' on 5 of every 6 passes — a permanently-red pair, which is the cry-wolf shape.",
        "file": 'corroborate.py',
        "find": '            return _base - len([c for c in cd.CHECKS\n                                if c[0] in getattr(cd, "PERIODIC", ()) and c[0] not in cd.SLOW])\n',
        "replace": '            return _base\n',
        "matches": 1,
    },
    {
        "why": "v2943/C — makes a LEGACY record (one with no `periodic`, written by an older console) ungradeable. That refuses a record for lacking a key it could not have had, and it is the exact regression the gate caught: five tests in TestV2394TheEagleCanBeGradedFromOUTSIDEItsOwnProcess went red, plus test_an_eagle_that_flew_EVERY_check_agrees reading 'unknown' != 'agree'. Backward compatibility here is a deliberate contract.",
        "file": 'corroborate.py',
        "find": '            if periodic is None:\n                # ⚠⚠ v2944 — BACKWARD COMPATIBILITY OUTRANKS THE NEW RULE, AND THE GATE TAUGHT ME\n                # THAT. v2943 returned UNKNOWN here on the "absent is not False" principle, and\n                # test_control\'s TestV2394TheEagleCanBeGradedFromOUTSIDEItsOwnProcess went RED in\n                # five places — including `test_a_PRE_v2409_record_with_no_primary_key_is_still_read`,\n                # whose own message is "refused for lacking a key it COULD NOT HAVE HAD". That is a\n                # deliberate contract: a record written by an older console must still be gradeable.\n                # So a record with no `periodic` keeps the PRE-v2943 expectation. The cost is\n                # stated rather than hidden: such a record can still read red on a pass that\n                # skipped PERIODIC — which is the state it was already in — and it corrects itself\n                # the moment the console writes one record carrying the key.\n                # [[feedback-blind-fixture-green-gate]] [[copy-drift]]\n                return _base\n',
        "replace": '            if periodic is None:\n                return None\n',
        "matches": 1,
    },
]


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
