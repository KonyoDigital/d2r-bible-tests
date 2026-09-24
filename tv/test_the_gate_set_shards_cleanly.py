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

    def test_the_slices_are_balanced_by_MEASURED_cost(self):
        """v3477 — balanced on declared timeout, the first sharded run came back 8m41s / 17m25s."""
        w = RG.cost_weights()
        a = sum(w[x] for x in RG.shard_names(1, 2))
        b = sum(w[x] for x in RG.shard_names(2, 2))
        self.assertLess(abs(a - b), max(w.values()) + 1,
                        "slices differ by more than one gate's MEASURED cost: %.0f vs %.0f" % (a, b))

    def test_the_cost_table_is_a_measurement_that_covers_the_registry(self):
        import gate_costs as GC
        table = GC.load()
        self.assertTrue(table, "tv/gate_costs.json is missing or empty — the shards fall back to "
                               "declared timeout, which the first sharded run proved lopsided")
        names = {g.name for g in RG.GATES}
        covered = len(names & set(table)) / float(len(names))
        self.assertGreaterEqual(covered, 0.95, "the cost table covers only %.0f%% of the gate set — "
                                "refresh it: python3 tv/gate_costs.py <ci-job-logs>" % (covered * 100))
        w = RG.cost_weights()
        unseen = sorted(names - set(table))
        if unseen:
            med = sorted(table.values())[len(table) // 2]
            self.assertEqual(w[unseen[0]], med, "an unmeasured gate did not weigh the median")

    def test_the_banner_names_the_basis_the_weights_actually_used(self):
        """#219 follow-up — the second eye on ea3f05da: every --shard run printed "balanced by
        declared timeout" while cost_weights() balanced on the measured table. One decision
        (_cost_table), two readers; DRIVEN through all three states, and the banner and the weights
        are both pinned to it."""
        import ast
        import inspect
        import gate_costs as _gc
        real = _gc.load
        try:
            for table, word in (({"a": 1.0}, "measured"), ({}, "no measured cost table"),
                                (None, "UNREADABLE")):
                _gc.load = lambda *a, _t=table, **k: _t
                got, basis = RG._cost_table()
                self.assertEqual(got, table)
                self.assertIn(word, basis, "a %r table was described as %r" % (table, basis))
        finally:
            _gc.load = real
        self.assertIn("measured", RG._cost_table()[1],
                      "premise: the committed table is readable, so the basis must say measured")
        tree = ast.parse(inspect.getsource(RG))
        banner = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                  and getattr(n.func, "id", "") == "print" and n.args
                  and isinstance(n.args[0], ast.BinOp)
                  and isinstance(n.args[0].left, ast.Constant)
                  and "SHARD %d/%d" in str(n.args[0].left.value)]
        self.assertEqual(len(banner), 1, "the shard banner moved — this law is judging nothing")
        self.assertNotIn("declared timeout", banner[0].args[0].left.value,
                         "the banner hard-codes a basis again instead of asking _cost_table()")
        self.assertIn("_cost_table", ast.dump(banner[0]),
                      "the banner does not ask _cost_table() which basis the weights used")
        self.assertIn("_cost_table", inspect.getsource(RG.cost_weights),
                      "cost_weights() decides its basis somewhere the banner cannot see")

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
        "why": "v3477 — the measured table ignored: back to declared timeout, the lopsided 8m41s / 17m25s split",
        "file": "run_gates.py",
        "find": "    weigh = cost_weights(gates)\n",
        "replace": "    weigh = dict((g.name, float(g.timeout or 0)) for g in gates)\n",
        "matches": 1,
    },
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
        # v3477 — RE-ANCHORED (REG-1163, my own proof): v3477 weighs by measured cost now.
        # Same property: ties must break by NAME, never by registry order.
        "find": "    for g in sorted(gates, key=lambda g: (-weigh[g.name], g.name)):\n",
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
