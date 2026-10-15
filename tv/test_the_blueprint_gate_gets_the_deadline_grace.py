# -*- coding: utf-8 -*-
"""REG-2235 (#120) - THE BLUEPRINT AND HEART GATES GET THE DEADLINE GRACE, SO A BUSY MACHINE IS NOT A STALE MAP.

blueprint.py --check and heart_map.py --check both REGENERATE a map in memory (blueprint walks the tree's AST, heart
maps every instrument) and diff it against the committed file, so their wall time tracks CPU contention rather than the
code. MEASURED 2026-10-13 on a89e0700: blueprint --check exited 0 in 115 s under D2R load (1-min load 17-29) and the
fixed 60 s bound in hooks/pre-push killed it and called a BUSY machine a stale map. Same class as test-venue's "the
suite measured my CPU, not his code".

The fix marks BOTH back-to-back 60 s gates with GATE_LOAD_GRACE (the render gate's REG-1995 mechanism), which gives a
gate busy AT ITS DEADLINE one load-measured extension (base x load/5, capped 2.5x -> 60 s becomes up to 150 s) and
STILL kills a gate quiet at its deadline at 60 s, so the hang detector is intact and the gate is not weakened. This is
a SOURCE guard (like test_a_gate_busy_at_its_deadline_gets_one_extension.test_only_the_render_gate_is_marked): it pins
the CALL SITE - the two gates sit inside one GATE_LOAD_GRACE region that is released before the next gate, and nothing
wider is marked. The grace MECHANISM itself is proved behaviourally in that sibling file. Reads hooks/pre-push, asserts
on structure, runs nothing.
"""
import io
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

HOOK = os.path.join(os.path.dirname(HERE), "hooks", "pre-push")


def _hook_lines():
    with io.open(HOOK, encoding="utf-8") as fh:
        return fh.read().split("\n")


def _is_gate_run(line):
    """True for a gate_run CALL SITE (gate_run "<name>" ...), never a comment or the function definition."""
    return ('gate_run "' in line) and not line.lstrip().startswith("#")


def _gate_line(lines, name):
    """Index of the `gate_run "<name>"` call, or -1. The call site, never a comment that mentions it."""
    needle = 'gate_run "%s"' % name
    for i, line in enumerate(lines):
        if needle in line and not line.lstrip().startswith("#"):
            return i
    return -1


class TheBlueprintGateGetsTheDeadlineGrace(unittest.TestCase):

    def setUp(self):
        self.lines = _hook_lines()
        self.bp = _gate_line(self.lines, "blueprint")
        self.ht = _gate_line(self.lines, "heart")
        self.rn = _gate_line(self.lines, "render")
        self.assertGreaterEqual(self.bp, 0, "the blueprint gate_run is gone from hooks/pre-push")
        self.assertGreaterEqual(self.ht, 0, "the heart gate_run is gone from hooks/pre-push")
        self.assertGreaterEqual(self.rn, 0, "the render gate_run (the region boundary) is gone from hooks/pre-push")
        self.assertLess(self.bp, self.ht, "blueprint no longer runs before heart")
        self.assertLess(self.ht, self.rn, "the render gate no longer runs after blueprint/heart")

    def _export_above(self, idx):
        """Nearest `export ... GATE_LOAD_GRACE` strictly above idx, stopping at the previous gate_run; -1 if none.

        Stopping at the previous gate_run is the point: an export that applies to blueprint must sit between it and
        the gate before it, not be inherited from some earlier gate's leaked mark.
        """
        for i in range(idx - 1, -1, -1):
            line = self.lines[i]
            if _is_gate_run(line):
                return -1
            if line.lstrip().startswith("export ") and "GATE_LOAD_GRACE" in line:
                return i
        return -1

    def _unset_below(self, idx, stop):
        """Nearest `unset ... GATE_LOAD_GRACE` below idx and before line `stop`; -1 if a gate_run is hit first."""
        for i in range(idx + 1, stop):
            line = self.lines[i]
            if _is_gate_run(line):
                return -1
            if line.lstrip().startswith("unset ") and "GATE_LOAD_GRACE" in line:
                return i
        return -1

    def test_the_blueprint_gate_is_inside_a_grace_region(self):
        exp = self._export_above(self.bp)
        uns = self._unset_below(self.ht, self.rn)
        self.assertGreaterEqual(
            exp, 0,
            "the blueprint gate_run is not preceded by `export ... GATE_LOAD_GRACE` (no gate between): the fixed "
            "60 s bound kills a busy-but-correct --check again and reports a stale map (REG-2235)")
        self.assertGreaterEqual(uns, 0, "the grace region never closes before the next gate (REG-2235)")
        self.assertTrue(exp < self.bp < uns,
                        "the blueprint gate is not inside the GATE_LOAD_GRACE region (REG-2235)")

    def test_the_heart_gate_is_covered_by_the_same_region(self):
        # heart is blueprint's identical 60 s back-to-back sibling; a blueprint-only fix still refuses at heart,
        # so the push stays blocked while he is gaming. The grace must cover both.
        exp = self._export_above(self.bp)
        uns = self._unset_below(self.ht, self.rn)
        self.assertGreaterEqual(exp, 0, "no grace region opens before the blueprint gate (REG-2235)")
        self.assertGreaterEqual(uns, 0, "the grace region never closes before the next gate (REG-2235)")
        self.assertTrue(exp < self.ht < uns,
                        "the heart gate is not inside the blueprint grace region, so the push is still refused at "
                        "heart while he is gaming (REG-2235)")

    def test_the_region_is_released_before_the_next_gate(self):
        # the mark must not outlive heart: a leak would silently hand the render/crest gates an extension they were
        # never sized for. REG-1995 carved exactly this shape ("the grace mark outlives the gate").
        uns = self._unset_below(self.ht, self.rn)
        self.assertGreaterEqual(
            uns, 0,
            "no `unset ... GATE_LOAD_GRACE` between the heart gate and the next gate: the grace leaks and silently "
            "weakens every gate after it (REG-2235)")

    def test_exactly_the_blueprint_and_heart_gates_are_marked(self):
        exp = self._export_above(self.bp)
        uns = self._unset_below(self.ht, self.rn)
        self.assertGreaterEqual(exp, 0, "no grace region opens before the blueprint gate (REG-2235)")
        self.assertGreaterEqual(uns, 0, "the grace region never closes before the next gate (REG-2235)")
        inside = [line for line in self.lines[exp + 1:uns] if _is_gate_run(line)]
        covered = [n for n in ("blueprint", "heart") if any('gate_run "%s"' % n in line for line in inside)]
        self.assertEqual(covered, ["blueprint", "heart"],
                         "the grace region must cover the blueprint and heart gates")
        self.assertEqual(
            len(inside), 2,
            "the GATE_LOAD_GRACE region covers a gate other than blueprint/heart - it must be scoped to exactly "
            "those two, or another gate silently gets an extension nobody asked for (REG-2235)")


# A sabotage of the FIX that this guard must catch (applied to the post-fix tree, then reverted).
RED_PROOF = [
    {"why": "REG-2235 - the blueprint/heart gates lose the deadline grace; the fixed 60 s bound kills a "
            "busy-but-correct --check again and reports a stale map",
     "file": "hooks/pre-push",
     "find": "  export GATE_LOAD_GRACE=1\n",
     "replace": "  : # grace mark removed\n",
     "matches": 1},
    {"why": "REG-2235 - the grace mark is never released, so it leaks past heart and silently widens the render "
            "and crest gates' bounds",
     "file": "hooks/pre-push",
     "find": "  unset GATE_LOAD_GRACE   # REG-2235 (#120) - release the deadline grace so no later gate inherits it\n",
     "replace": "  : # unset removed\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)