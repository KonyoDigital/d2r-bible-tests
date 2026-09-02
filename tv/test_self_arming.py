#!/usr/bin/env python3
"""Guards for the self-arming lock. Every case asserts a REFUSAL as well as a pass.

The thing being replaced is a human flipping `_PRUNE_SAFE_TO_RUN` by hand, so the failure that
matters is not "it refused when it should have opened" — it is "IT OPENED WITHOUT EARNING IT".
Every test here is pointed at that direction.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import self_arming as SA


class _Ledger(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="arm-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.p = os.path.join(self.root, "proofs.jsonl")
        self._old = SA.LEDGER
        SA.LEDGER = self.p
        self.addCleanup(setattr, SA, "LEDGER", self._old)

    def put(self, lock, kind, refused, n=1):
        with io.open(self.p, "a", encoding="utf-8") as fh:
            for _ in range(n):
                fh.write(json.dumps({"lock": lock, "kind": kind,
                                     "refused": bool(refused), "ts": 0}) + "\n")


class TestUnprovenIsNotFailing(_Ledger):
    """The distinction the whole mechanism rests on. If these two collapse, a lock either opens on
    silence or paints its own newest surfaces red — and both get the mechanism ignored."""

    def test_no_proofs_is_UNPROVEN_and_carries_NO_score(self):
        s = SA.score("vault.apply")
        self.assertEqual(s["state"], SA.UNPROVEN)
        self.assertIsNone(s["wilson"],
                          "n=0 rendered as a NUMBER. 'nobody looked' would then be indistinguishable "
                          "from 'it scored zero', and a surface could be reported as failing when "
                          "it has simply never been tested. [[unknown-stays-unknown]]")
        self.assertIn("not a failure", s["why"])

    def test_UNPROVEN_still_does_not_permit_the_action(self):
        ok, why = SA.may("vault.apply")
        self.assertFalse(ok, "an untested surface was permitted to act")


class TestTheDenominatorIsSABOTAGES(_Ledger):
    """★ THE ONE THING THAT WOULD MAKE THIS A LIE. [[heart-first]] §5 — an invariant that always
    agrees may be perfect or INERT, and those are indistinguishable. A lock fed by an agreement
    rate opens BECAUSE nobody tested it, which is the exact failure it exists to prevent."""

    def test_a_wall_of_agreements_with_no_refusal_NEVER_opens(self):
        # 40 sabotages, and the guard failed to refuse every single time
        self.put("vault.sweep_start", "sabotage", False, n=40)
        s = SA.score("vault.sweep_start")
        self.assertEqual(s["state"], SA.LOCKED)
        self.assertEqual(s["k"], 0)
        self.assertEqual(s["n"], 40)
        self.assertEqual(s["wilson"], 0.0,
                         "40 attempts and 0 refusals must score 0.0 — this is the INERT guard, and "
                         "it must never be mistaken for an untested one")

    def test_a_refusal_is_what_counts_as_success(self):
        self.put("vault.sweep_start", "sabotage", True, n=10)
        s = SA.score("vault.sweep_start")
        self.assertEqual(s["k"], 10)
        self.assertGreater(s["wilson"], 0.72,
                           "10/10 refusals should reach the published 0.722 reference")


class TestWilsonAndConfluenceBOTH(_Ledger):
    """confidence.py's own words: 'The two run TOGETHER or neither means anything.' Wilson counts
    how many looks agreed, never whether they were INDEPENDENT — four re-runs of one sabotage by
    one harness is one proof wearing four hats."""

    def test_a_perfect_score_from_ONE_kind_is_still_LOCKED(self):
        self.put("vault.apply", "sabotage", True, n=30)      # wilson ~0.88, one kind = 1.0
        self.put("vault.sweep_start", "sabotage", True, n=30)
        s = SA.score("vault.apply")
        self.assertGreater(s["wilson"], s["bar"], "precondition: the score itself must clear")
        self.assertEqual(s["state"], SA.LOCKED,
                         "30 identical proofs opened the lock. Evidence that is all one kind is "
                         "one look wearing thirty hats.")
        self.assertIn("too alike", s["why"])

    def test_two_INDEPENDENT_kinds_open_it(self):
        self.put("vault.sweep_start", "sabotage", True, n=20)
        self.put("vault.apply", "sabotage", True, n=15)
        self.put("vault.apply", "cross-family", True, n=5)
        s = SA.score("vault.apply")
        self.assertEqual(s["state"], SA.OPEN, s["why"])
        ok, why = SA.may("vault.apply")
        self.assertTrue(ok, why)

    def test_an_UNWEIGHTED_kind_is_worth_zero_not_a_default(self):
        """A kind nobody has weighted is a kind nobody has thought about."""
        self.put("vault.sweep_start", "sabotage", True, n=20)
        self.put("vault.apply", "sabotage", True, n=20)
        self.put("vault.apply", "vibes", True, n=20)
        s = SA.score("vault.apply")
        self.assertEqual(s["state"], SA.LOCKED,
                         "an unrecognised proof kind paid as if someone had weighted it")


class TestHisOrderIsEnforced(_Ledger):
    """He gave a chain: printer+reels -> theatre+shelf -> routing -> the deleter. Proving the
    deleter in isolation proves nothing about the river feeding it."""

    def test_the_deleter_cannot_open_before_its_prerequisites(self):
        # a flawless record for the prune itself, and NOTHING upstream
        self.put("prune.arm", "sabotage", True, n=60)
        self.put("prune.arm", "cross-family", True, n=20)
        self.put("prune.arm", "live", True, n=20)
        ok, why = SA.may("prune.arm")
        self.assertFalse(ok, "the deleter armed itself with no proof of the lanes that feed it")
        self.assertIn("blocked upstream", why)
        self.assertIn("vault.sweep_start", why,
                      "the refusal must NAME the unmet prerequisite, or a high score reads as "
                      "'nearly there' when the real blocker is somewhere else entirely")


class TestItFailsCLOSED(_Ledger):
    """An unreadable proof queue is UNKNOWN, and UNKNOWN is never permission."""

    def test_an_unparseable_row_is_UNKNOWN_not_empty(self):
        self.put("vault.sweep_start", "sabotage", True, n=5)
        with io.open(self.p, "a", encoding="utf-8") as fh:
            fh.write("{not json\n")
        s = SA.score("vault.sweep_start")
        self.assertEqual(s["state"], SA.UNKNOWN,
                         "a hole in the evidence was read as a blank one — the 5 good rows would "
                         "then be the whole record, which is a smaller claim than the truth")
        ok, why = SA.may("vault.sweep_start")
        self.assertFalse(ok)
        self.assertIn("fails CLOSED", why)

    def test_an_undeclared_lock_is_never_permitted(self):
        ok, why = SA.may("something.nobody.declared")
        self.assertFalse(ok)
        self.assertIn("never permitted", why)


class TestThereIsNoHandOverride(unittest.TestCase):
    """The whole point is that Konyo stops being the arming mechanism. A `force` parameter would
    quietly restore the thing this replaces."""

    def test_may_takes_exactly_one_argument(self):
        import inspect
        sig = inspect.signature(SA.may)
        self.assertEqual(list(sig.parameters), ["lock"],
                         "may() grew a parameter. If one of them is an override, the lock is "
                         "decorative and the hand-arming is back.")

    def test_the_module_never_writes_an_unlock_flag(self):
        """⚠ THIS GUARD FAILED ON PROSE FIRST, AND THE LAW WAS NEVER WRONG.

        The first cut stripped `#` comments and asserted `_PRUNE_SAFE_TO_RUN` was absent. The
        module's own DOCSTRING says "This replaces `_PRUNE_SAFE_TO_RUN`" — so the guard went red
        on the sentence explaining the fix, which is [[source-reading-guard]] §4 exactly, and the
        third time that class has cost a wrong reading today. A `#`-stripper does not strip
        docstrings.

        Ask the COMPILER, not the text (§1): a name in a docstring is not in the AST. This also
        makes the guard STRONGER — it now catches `setattr(m, "_PRUNE_SAFE_TO_RUN", True)`-shaped
        writes that a substring search would miss entirely.
        """
        import ast, inspect
        tree = ast.parse(inspect.getsource(SA))

        FORBIDDEN_NAMES = {"_PRUNE_SAFE_TO_RUN", "SAFE_TO_RUN"}
        FORBIDDEN_CALLS = {"remove", "unlink", "rmtree", "replace", "setattr"}
        bad = []
        for node in ast.walk(tree):
            # writing a flag — assignment, augmented assignment, or an attribute set
            if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                tgts = node.targets if isinstance(node, ast.Assign) else [node.target]
                for t in tgts:
                    nm = getattr(t, "id", None) or getattr(t, "attr", None)
                    if nm in FORBIDDEN_NAMES:
                        bad.append("writes %s at line %d" % (nm, node.lineno))
            # destructive or reflective calls
            if isinstance(node, ast.Call):
                fn = node.func
                nm = getattr(fn, "attr", None) or getattr(fn, "id", None)
                if nm in FORBIDDEN_CALLS:
                    bad.append("calls %s() at line %d" % (nm, node.lineno))
        self.assertEqual(bad, [],
                         "the lock module ACTS instead of only deciding: %s. It DECIDES and "
                         "REPORTS; anything that flips a flag or deletes is a second arming path "
                         "and restores the hand-arming this replaces." % "; ".join(bad))

    def test_it_calls_confidence_rather_than_restating_the_maths(self):
        import inspect
        src = inspect.getsource(SA)
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertIn("from confidence import", code)
        self.assertNotIn("def wilson_lower", code,
                         "a second copy of the Wilson maths. [[copy-drift]] — two copies of one "
                         "safety routine diverge, and only one of them gets tuned.")


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
