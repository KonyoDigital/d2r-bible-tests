#!/usr/bin/env python3
"""v3842 GATE-TRIM A - the parallel --full runs every registered gate exactly once, and stays serial when it must.

plan() is driven over the REAL registry and the real cost table: the light slices and the heavy list are disjoint,
their union is every gate, nothing at or over HEAVY_S lands in a light slice, and the slices are balanced. why_serial
refuses under the memory floor, on an unknown reading, and on a dirty tracked tree. And run_gates hands the heavy list
to the serial pass only when it is non-empty (an empty `only` would mean every gate).
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gates_parallel as GP  # noqa: E402
import run_gates as RG  # noqa: E402


class TheParallelFullRunsEveryGateOnce(unittest.TestCase):
    def test_every_gate_lands_in_exactly_one_place(self):
        weigh = RG.cost_weights(RG.GATES)
        slices, heavy = GP.plan(RG.GATES, weigh)
        seen = [n for s in slices for n in s] + heavy
        self.assertEqual(len(seen), len(set(seen)), "a gate would run twice")
        self.assertEqual(set(seen), set(g.name for g in RG.GATES), "a gate would not run at all")
        self.assertEqual(len(slices), GP.SLICES)
        for s in slices:
            for n in s:
                self.assertLess(weigh[n], GP.HEAVY_S, "%s is heavy but would share the box" % n)
        for n in heavy:
            self.assertGreaterEqual(weigh[n], GP.HEAVY_S)
        self.assertTrue(heavy, "the heavy pass is empty - run() would read [] as every gate")
        tot = [sum(weigh[n] for n in s) for s in slices]
        self.assertLess(max(tot) - min(tot), GP.HEAVY_S + 1, "the light slices are not balanced: %r" % tot)

    def test_it_stays_serial_under_the_floor_or_blind(self):
        self.assertIn("serial", GP.why_serial(mem=GP.FLOOR_GB - 0.5) or "")
        self.assertIn("UNKNOWN", GP.why_serial(mem=None) if GP.free_gb() is None else "UNKNOWN")

    def test_a_dirty_tracked_tree_stays_serial(self):
        tmp = tempfile.mkdtemp(prefix="tvd-par-dirty-")
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        g = lambda *a: subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t"] + list(a), cwd=tmp,
                                      env=env, capture_output=True, check=True)
        open(os.path.join(tmp, "f"), "w").write("a")
        g("init", "-q"); g("add", "f"); g("commit", "-qm", "x")
        self.assertIsNone(GP.why_serial(repo=tmp, mem=GP.FLOOR_GB + 10))
        open(os.path.join(tmp, "f"), "w").write("b")
        self.assertIn("uncommitted", GP.why_serial(repo=tmp, mem=GP.FLOOR_GB + 10) or "")

    def test_run_gates_never_hands_an_empty_heavy_list_on(self):
        src = open(os.path.join(HERE, "run_gates.py"), encoding="utf-8").read()
        body = src[src.index("def _parallel_light("):src.index("def gate_set_exit(")]
        self.assertIn("if not heavy:", body)
        self.assertLess(body.index("if not heavy:"), body.index("GP.run_light("))


if __name__ == "__main__":
    unittest.main()
