# -*- coding: utf-8 -*-
"""v3848 - A FRESH WORKTREE RENDERS THE STORED HALF OF THE HEART.

v3847 push #1 went red on `heart-stored` (11 nodes against a floor of 18): the worktree had no tv/.heart2.json
(gitignored), so the panel read "never measured here". The fix copied a file by hand. Now the render sandbox writes
a SYNTHETIC census into the sandbox only when the tree has none, and the private console reads it through
TV_HEART2_STATE. The tree's own census always wins, and nothing is written into the tree.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


class AFreshTreeRendersTheStoredHeart(unittest.TestCase):
    def setUp(self):
        self.sand = tempfile.mkdtemp(prefix="tvd-h2seed-")
        self.addCleanup(shutil.rmtree, self.sand, True)
        import render_check
        self.R = render_check

    def test_a_tree_without_a_census_gets_a_synthetic_one_in_the_sandbox(self):
        real = os.path.isfile
        with mock.patch("os.path.isfile", lambda p: False if p.endswith(os.sep + ".heart2.json") else real(p)):
            p = self.R._seed_heart2_census(self.sand)
        self.assertTrue(p and p.startswith(self.sand), "a fresh tree got no census - heart-stored reads UNKNOWN")
        env = dict(os.environ, TV_HEART2_STATE=p)
        out = subprocess.run([sys.executable, "-c", "import control_app as c, json; print(json.dumps(c._heart2_census().get('state')))"],
                             cwd=HERE, env=env, capture_output=True, text=True, timeout=60)
        self.assertNotEqual(out.stdout.strip().splitlines()[-1], '"UNKNOWN"', out.stdout[-500:] + out.stderr[-500:])

    def test_the_trees_own_census_wins(self):
        real = os.path.isfile
        with mock.patch("os.path.isfile", lambda p: True if p.endswith(os.sep + ".heart2.json") else real(p)):
            self.assertIsNone(self.R._seed_heart2_census(self.sand))
        self.assertFalse(os.path.exists(os.path.join(self.sand, "heart2_fixture.json")), "the tree has its own census, yet a fixture was seeded")

    def test_heart2_reads_the_state_it_is_pointed_at(self):
        out = subprocess.run([sys.executable, "-c", "import heart2; print(heart2.STATE)"], cwd=HERE,
                             env=dict(os.environ, TV_HEART2_STATE="/nowhere/h2.json"),
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(out.stdout.strip().splitlines()[-1], "/nowhere/h2.json")


RED_PROOF = [
    {"why": "v3848 - heart2 ignores TV_HEART2_STATE",
     "file": "heart2.py",
     "find": 'STATE = os.environ.get("TV_HEART2_STATE") or os.path.join(HERE, ".heart2.json")\n',
     "replace": 'STATE = os.path.join(HERE, ".heart2.json")\n',
     "matches": 1},
    {"why": "v3848 - a fresh tree gets no synthetic census",
     "file": "render_check.py",
     "find": '    p = os.path.join(sand, "heart2_fixture.json")\n',
     "replace": '    return None\n    p = os.path.join(sand, "heart2_fixture.json")\n',
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
