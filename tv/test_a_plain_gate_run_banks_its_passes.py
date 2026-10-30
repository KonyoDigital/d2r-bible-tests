# -*- coding: utf-8 -*-
"""v3846 - A PLAIN GATE RUN BANKS ITS PASSES.

v3845: two `run_gates.py` runs with no flag passed 1312 gates and recorded none (no flag left the ledger
closed), so the bump-only carry had nothing to inherit and the bump commit reran every gate. A run with no
flag now records each PASS; only --changed carries.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = "test_a_bump_only_commit_inherits_its_parents_passes"


def _run(args, led):
    env = dict(os.environ, TV_GATE_LEDGER=led)
    env.pop("CI", None); env.pop("GITHUB_ACTIONS", None); env.pop("GATE_LEDGER", None)
    p = subprocess.run([sys.executable, os.path.join(HERE, "run_gates.py")] + args, cwd=os.path.dirname(HERE),
                       env=env, capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout + p.stderr


def _stored(led):
    if not os.path.exists(led):
        return {}
    with open(led) as f:
        d = json.load(f)
    return d.get("entries", d) if isinstance(d, dict) else {}


class APlainRunBanks(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="tvd-plainrun-")
        self.led = os.path.join(self.d, ".gate_ledger.json")

    def test_a_plain_run_records_the_pass(self):
        rc, out = _run(["--only", GATE], self.led)
        self.assertEqual(rc, 0, out[-1500:])
        self.assertIn(GATE, json.dumps(_stored(self.led)), "a plain run passed the gate and banked nothing:\n" + out[-1500:])


RED_PROOF = [
    {"why": "no flag leaves the ledger closed again, so a green run banks nothing for a bump to inherit",
     "file": "tv/run_gates.py",
     "find": '("record" if not a.shard else None))  # RUN-RECORDS-BY-DEFAULT',
     "replace": '(None if not a.shard else None))  # RUN-RECORDS-BY-DEFAULT', "matches": 1},
]

if __name__ == "__main__":
    unittest.main()
