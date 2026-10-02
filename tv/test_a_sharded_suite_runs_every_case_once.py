# -*- coding: utf-8 -*-
"""#42 lever 4 — A SHARDED SUITE RUNS EVERY CASE ONCE, AND A SHARD THAT RAN LESS IS RED.

tv/shard_suite.py splits test_control (~10 of the push gate's 17 minutes, one process) into parallel shards by class. A
parallel run is only a faster verdict if it is the SAME verdict, so this law drives the real runner over a planted suite:

  · every class lands in exactly one shard, and the dealer balances by measured cost;
  · all green -> green, with the cases run equal to the cases the loader found;
  · one red class -> red; a shard that dies before it answers -> red (never "0 failures");
  · a shard that ran fewer cases than it was dealt -> red, even when every shard exited 0;
  · no two shards share a fixed port.
RED_PROOF below. [[regression-guard]] [[unknown-stays-unknown]]
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import shard_suite as SS  # noqa: E402

PLANT = '''
import os, unittest
class Alpha(unittest.TestCase):
    def test_a1(self): pass
    def test_a2(self): pass
class Beta(unittest.TestCase):
    def test_b1(self):
        with open(os.path.join(os.environ["PLANT_PORTS"], "beta"), "w") as fh: fh.write(os.environ["TV_PORT"])
class Gamma(unittest.TestCase):
    def test_g1(self):
        with open(os.path.join(os.environ["PLANT_PORTS"], "gamma"), "w") as fh: fh.write(os.environ["TV_PORT"])
    def test_g2(self):
        if os.environ.get("PLANT_RED") == "1": self.fail("planted red")
class Delta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("PLANT_DIE") == "1": os._exit(3)
    def test_d1(self): pass
class Zeta(unittest.TestCase):
    SHARD_ALONE = True
    def test_z1(self):
        import time
        with open(os.path.join(os.environ["PLANT_PORTS"], "zeta"), "w") as fh:
            fh.write("%s %f" % (os.environ["SHARD_INDEX"], time.time()))
class Eta(unittest.TestCase):
    def test_e1(self):
        import time
        time.sleep(0.5)
        with open(os.path.join(os.environ["PLANT_PORTS"], "eta"), "w") as fh:
            fh.write("%s %f" % (os.environ["SHARD_INDEX"], time.time()))
'''


class TheDealerPlacesEveryClassOnce(unittest.TestCase):

    def test_every_class_in_exactly_one_shard(self):
        names = ["C%02d" % i for i in range(23)]
        plan = SS.deal(names, 4, {})
        flat = [c for s in plan for c in s]
        self.assertEqual(sorted(flat), sorted(names), "a class was dropped or dealt twice")
        self.assertEqual(len(plan), 4)

    def test_the_heaviest_class_does_not_share_with_the_next_heaviest(self):
        plan = SS.deal(["big", "big2", "s1", "s2", "s3", "s4"], 2,
                       {"big": 100, "big2": 90, "s1": 1, "s2": 1, "s3": 1, "s4": 1})
        self.assertFalse(any("big" in s and "big2" in s for s in plan), "the two heaviest landed on one shard: %r" % plan)


class TheUnionIsTheVerdict(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="shard_law_")
        self.addCleanup(shutil.rmtree, self.d, True)
        with io.open(os.path.join(self.d, "plant_suite.py"), "w", encoding="utf-8") as fh:
            fh.write(PLANT)
        self.ports = os.path.join(self.d, "ports")
        os.makedirs(self.ports)
        self.cost = os.path.join(self.d, "cost.json")

    def _run(self, k=3, classes=None, **env):
        e = dict(os.environ, PLANT_PORTS=self.ports, **env)
        return SS.run("plant_suite", k, here=self.d, cost_path=self.cost, _classes=classes, _env=e)

    def test_all_green_is_green_and_counts_every_case(self):
        ok, rep = self._run()
        self.assertTrue(ok, rep)
        self.assertEqual((rep["ran"], rep["expected"]), (8, 8), rep)

    def test_one_red_class_is_red(self):
        ok, rep = self._run(PLANT_RED="1")
        self.assertFalse(ok, "a planted red case read green across shards")

    def test_a_shard_that_dies_before_answering_is_red(self):
        ok, rep = self._run(PLANT_DIE="1")
        self.assertFalse(ok, "a shard that exited in setUpClass read green")
        self.assertTrue(any(s["ran"] is None or s["rc"] != 0 for s in rep["shards"]), rep)

    def test_a_shard_that_ran_less_than_it_was_dealt_is_red(self):
        found = SS.classes_of("plant_suite", self.d)
        self.assertEqual(found, {"Alpha": 2, "Beta": 1, "Gamma": 2, "Delta": 1, "Zeta": 1, "Eta": 1},
                         "PREMISE: the loader count moved")
        ok, rep = self._run(classes=dict(found, Alpha=3))         # the loader said 3, the shard ran 2
        self.assertFalse(ok, "a shard that ran fewer cases than it was dealt read green: %r" % rep)

    def test_a_class_that_holds_a_budget_runs_alone_after_the_others(self):
        """v3562's push: a wall-clock budget measured beside three other shards measured the neighbours."""
        ok, rep = self._run(k=3)
        self.assertTrue(ok, rep)
        z_idx, z_start = io.open(os.path.join(self.ports, "zeta")).read().split()
        e_idx, e_end = io.open(os.path.join(self.ports, "eta")).read().split()
        z_shard = [s for s in rep["shards"] if s["shard"] == int(z_idx)][0]
        self.assertEqual(z_shard["classes"], 1, "the budget class shared its process: %r" % z_shard)
        self.assertGreaterEqual(float(z_start), float(e_end), "the budget class ran while another shard was running")

    def test_no_two_shards_share_a_port(self):
        ok, rep = self._run(k=4)
        self.assertTrue(ok, rep)
        b = io.open(os.path.join(self.ports, "beta")).read()
        g = io.open(os.path.join(self.ports, "gamma")).read()
        self.assertNotEqual(b, g, "two shards were handed the same fixed port")
        self.assertNotIn(b, ("17772", "17971", "17972"))


RED_PROOF = [
    {"why": "lever 4 - a class that holds a wall-clock budget is dealt beside the others again",
     "file": "shard_suite.py",
     "find": "    together = sorted(c for c in found if c not in alone)\n",
     "replace": "    together, alone = sorted(found), []\n",
     "matches": 1},
    {"why": "lever 4 - a shard's own exit code is the verdict again: one that ran fewer cases than dealt reads green",
     "file": "shard_suite.py",
     "find": "        sok = rc == 0 and bool(res) and res.get(\"ok\") is True and got == want\n",
     "replace": "        sok = rc == 0\n",
     "matches": 1},
    {"why": "lever 4 - every shard is handed the same fixed port again",
     "file": "shard_suite.py",
     "find": "                    \"TV_PORT\": str(PORT_BASE + 2 * i), \"TV_CONTROL_PORT\": str(PORT_BASE + 2 * i + 1),\n",
     "replace": "                    \"TV_PORT\": str(PORT_BASE), \"TV_CONTROL_PORT\": str(PORT_BASE + 1),\n",
     "matches": 1},
    {"why": "lever 4 - the dealer drops the last class",
     "file": "shard_suite.py",
     "find": "    for c in sorted(classes, key=lambda c: (-w[c], c)):\n",
     "replace": "    for c in sorted(classes, key=lambda c: (-w[c], c))[:-1]:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
