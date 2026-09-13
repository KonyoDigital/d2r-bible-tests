# -*- coding: utf-8 -*-
"""THE EPOCH MAY NEVER DELETE, AND MAY NEVER REPORT A TERMINUS IT DID NOT REACH.

Konyo asked for real reels driven down the river and watched: *"keep yo-yoing it and looping it
through until it finally ends up where its suppose to ... then epoch it so its like it was an
isolated test demonstration.. but on real live and real reel sessions"*.

FIRST RUN, on his own footage:

    onDisk 24 · candidates to release: 0
    stations  releasable 16 · banked 8
    tags      recent 8 · panels-never-banked 8 · test-fixture 8
    cycle 1 moved=False · cycle 2 moved=False
    STOPPED: a fixed point — the river cannot advance these reels any further on its own
    STILL never fired (7): eligible, holds-proof, never-chronicle-swept, no-witness-index,
                           rows-not-banked, vault-owes, zero-pages

**`eligible` has never fired.** Not once has a reel been ruled safe to release. That is the
measurement behind "the vault hasnt worked yet", and it is why NOTHING may delete yet: a lane that
has never reached its own terminus has not been shown to work, and deleting on it would destroy
his footage on the strength of code nothing has exercised. [[regression-guard]]

This file refuses four rots:
  1. the harness gains the power to delete;
  2. `apply` stops defaulting to dry, so a caller changes state without asking;
  3. a fixed point is reported as success — "nothing moved" made to read like "everything done";
  4. the excluded rules are dropped silently instead of named with their reason.
"""
import ast
import io
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = io.open(os.path.join(HERE, "river_epoch.py"), encoding="utf-8").read()

#: anything that removes footage or rewrites a ledger. PARSED as calls, never grepped — the
#: module's own prose says the words "delete" and "retire" repeatedly. [[source-reading-guard]]
FORBIDDEN = ("unlink", "rmtree", "remove", "rmdir", "retire", "apply_plan", "prune")


class TestTheEpochNeverDeletes(unittest.TestCase):

    def test_the_harness_calls_nothing_that_can_destroy(self):
        tree = ast.parse(SRC)
        called = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                f = n.func
                nm = getattr(f, "attr", None) or getattr(f, "id", None)
                if nm:
                    called.append(nm)
        bad = sorted(set(c for c in called if c in FORBIDDEN))
        print("distinct calls parsed: %d · destructive among them: %d" % (len(set(called)), len(bad)))
        self.assertEqual([], bad,
                         "the epoch reads, re-admits and records. It may never delete: %r" % (bad,))

    def test_apply_defaults_to_dry_everywhere(self):
        tree = ast.parse(SRC)
        checked = 0
        for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            names = [a.arg for a in fn.args.args]
            if "apply" not in names:
                continue
            idx = names.index("apply")
            pad = len(names) - len(fn.args.defaults)
            self.assertGreaterEqual(idx, pad, "%s: apply has no default at all" % fn.name)
            d = fn.args.defaults[idx - pad]
            checked += 1
            self.assertIsInstance(d, ast.Constant, "%s: apply's default is not a literal" % fn.name)
            self.assertIs(d.value, False,
                          "%s: apply must default to FALSE — a caller changes state only by "
                          "asking" % fn.name)
        print("functions taking `apply`, all defaulting False: %d" % checked)
        self.assertGreaterEqual(checked, 2, "expected the pass and the runner to both take apply")

    def test_a_fixed_point_is_never_reported_as_success(self):
        """PARSED OUT OF run(), NOT GREPPED OUT OF THE FILE.

        ⚠⚠ THE FIRST CUT OF THIS LAW WAS BLIND AND heart2 CAUGHT IT. It asserted both phrases
        existed ANYWHERE in the source; the sabotage swapped the fixed-point sentence for the
        success one in the CODE, and the words "fixed point" still sat in this module's own
        DOCSTRING, so the law stayed green through its own defeat. A guard that reads prose cannot
        tell a live branch from a paragraph about it. [[source-reading-guard]]
        [[feedback-blind-fixture-green-gate]]

        So: find the quiet-cycle branch inside run() and read the string IT assigns.
        """
        tree = ast.parse(SRC)
        run = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "run"]
        self.assertEqual(1, len(run), "run() could not be located")
        # every string literal assigned to ep["stoppedBecause"] inside run(), in source order
        assigned = []
        for n in ast.walk(run[0]):
            if not isinstance(n, ast.Assign):
                continue
            t = n.targets[0]
            if not (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                    and t.value.id == "ep"):
                continue
            k = t.slice.value if isinstance(t.slice, ast.Constant) else None
            if k != "stoppedBecause":
                continue
            txt = " ".join(c.value for c in ast.walk(n.value)
                           if isinstance(c, ast.Constant) and isinstance(c.value, str))
            assigned.append(txt)
        print("stoppedBecause sentences assigned inside run(): %d" % len(assigned))
        for a in assigned:
            print("   %s" % a[:90])
        fixed = [a for a in assigned if "fixed point" in a]
        done = [a for a in assigned if "every gap rule fired" in a]
        self.assertEqual(1, len(fixed),
                         "exactly one branch may say a fixed point was reached, and it must be "
                         "the quiet-cycle branch")
        self.assertEqual(1, len(done), "exactly one branch may report success")
        self.assertNotEqual(fixed[0], done[0],
                            "'nothing moved' and 'every rule fired' are opposite facts and must "
                            "never render as the same sentence")

    def test_the_excluded_rules_are_named_with_their_reason(self):
        import river_epoch as RE
        print("excluded: %s" % (list(RE.EXCLUDED),))
        print("reason   : %s" % RE.EXCLUDED_WHY)
        self.assertEqual(2, len(RE.EXCLUDED),
                         "exactly two rules cannot fire without a free_mb target")
        self.assertTrue(RE.EXCLUDED_WHY and len(RE.EXCLUDED_WHY) > 20,
                        "an exclusion with no stated reason is a silent cap, which is how a "
                        "partial run reads as a complete one")
        for r in RE.EXCLUDED:
            self.assertNotIn(r, RE.never_fired({r: 0, "eligible": 0}),
                             "%s must be excluded from the gap list, not counted as a gap" % r)
        self.assertIn("eligible", RE.never_fired({"eligible": 0, "recent": 3}),
                      "a real gap rule must still be reported")

    def test_never_fired_reads_zero_as_a_gap_and_a_count_as_fired(self):
        import river_epoch as RE
        self.assertEqual(["zero-pages"], RE.never_fired({"zero-pages": 0, "recent": 8}))
        self.assertEqual([], RE.never_fired({"zero-pages": 1, "recent": 8}))
        print("never_fired: 0 -> gap, non-zero -> fired  (both asserted)")


RED_PROOF = [
    {
        "why": "the runner's `apply` stops defaulting to dry, so any caller that forgets the "
               "keyword changes his river instead of reading it",
        "file": "river_epoch.py",
        "find": "def run(cycles=10, quiet_for=2, apply=False):",
        "replace": "def run(cycles=10, quiet_for=2, apply=True):",
        "matches": 1,
    },
    {
        "why": "the two excluded rules stop being named, so a partial rule set reads as the whole "
               "one and a silent cap becomes a clean bill",
        "file": "river_epoch.py",
        "find": 'EXCLUDED = ("ledger-unreadable", "target-met")',
        "replace": 'EXCLUDED = ("ledger-unreadable", "target-met", "eligible")',
        "matches": 1,
    },
    {
        "why": "a fixed point reports as success, so 'the river cannot advance these reels' reads "
               "exactly like 'every reel finished'",
        "file": "river_epoch.py",
        "find": '            ep["stoppedBecause"] = ("nothing moved for %d consecutive cycle(s) — a fixed point. "',
        "replace": '            ep["stoppedBecause"] = ("every gap rule fired after %d quiet cycle(s). "',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
