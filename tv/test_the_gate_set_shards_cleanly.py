# -*- coding: utf-8 -*-
"""v3472 (#184) — the gate set splits into slices that are DISJOINT, COMPLETE and the SAME everywhere.

⚠ WHY: the agent-suite ran 25m18s against its 25-minute ceiling on d9bdb682 and was CANCELLED — the
shipped version got no verdict. CI now runs `run_gates.py --shard K/N` as a matrix. A slice that
drops a gate is a gate that silently never runs; two slices sharing one is a ceiling paid twice; a
slice that differs between machines is a verdict nobody can reproduce. And an EMPTY slice is worse
than all three: `run()` treats `[]` as "every gate".

DRIVEN against the real registry; nothing here reads source text. RED_PROOF below.
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

import run_gates as RG  # noqa: E402


class TheGateSetShardsCleanly(unittest.TestCase):

    def test_every_gate_lands_in_exactly_one_slice(self):
        names = [g.name for g in RG.GATES]
        for n in (2, 3):
            slices = [RG.shard_names(k, n) for k in range(1, n + 1)]
            flat = [x for s in slices for x in s]
            self.assertEqual(sorted(flat), sorted(names),
                             "%d-way: a gate is missing from every slice, or sits in two" % n)
            self.assertTrue(all(slices), "%d-way: an EMPTY slice — run() would run EVERY gate" % n)

    def test_the_slices_are_the_same_on_every_run(self):
        self.assertEqual(RG.shard_names(1, 2), RG.shard_names(1, 2))
        self.assertEqual(RG.shard_names(1, 2, gates=list(reversed(RG.GATES))), RG.shard_names(1, 2),
                         "the slice depends on registry ORDER, so two machines can cut it differently")

    def test_the_slices_are_balanced_by_declared_cost(self):
        w = lambda names: sum(float(g.timeout or 0) for g in RG.GATES if g.name in set(names))
        a, b = w(RG.shard_names(1, 2)), w(RG.shard_names(2, 2))
        self.assertLess(abs(a - b), max(float(g.timeout or 0) for g in RG.GATES) + 1,
                        "slices differ by more than one gate's cost: %.0f vs %.0f" % (a, b))

    def test_a_slice_that_is_not_a_slice_is_refused(self):
        for k, n in ((0, 2), (3, 2), (1, 10 ** 6)):
            with self.assertRaises(ValueError, msg="shard %d/%d was accepted" % (k, n)):
                RG.shard_names(k, n)
        self.assertEqual(RG.main(["run_gates.py", "--shard", "3/2"]), 2,
                         "a malformed --shard did not answer exit 2 (NO GATE RAN)")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "every slice returns the WHOLE set: each shard re-runs everything and pays the ceiling",
        "file": "run_gates.py",
        "find": "    return sorted(bins[int(k) - 1][2])\n",
        "replace": "    return sorted(g.name for g in gates)\n",
        "matches": 1,
    },
    {
        "why": "ties broken by registry order instead of name: two machines cut different slices",
        "file": "run_gates.py",
        "find": "    for g in sorted(gates, key=lambda g: (-float(g.timeout or 0), g.name)):\n",
        "replace": "    for g in gates:\n",
        "matches": 1,
    },
    {
        "why": "the bounds check removed: shard 3/2 is 'accepted' and indexes past the slices",
        "file": "run_gates.py",
        "find": "    if not (1 <= int(k) <= int(n)) or int(n) > len(gates):\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
]
