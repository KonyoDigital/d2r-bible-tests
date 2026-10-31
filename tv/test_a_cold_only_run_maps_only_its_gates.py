# -*- coding: utf-8 -*-
"""v3847 - A COLD `--only` RUN MAPS ONLY ITS OWN GATES.

The scoped prove of v3847 read test_control ALREADY RED untampered (REG-1877's killed-lock case) and the push would
have been refused. Not the lock: the child `run_gates.py --only visual-lock` ran in a fresh heart2 sandbox with no
input map, and the ledger declared the inputs of EVERY registered gate (~1300 parses) before running its one gate -
measured >200 s, past the law's 180 s timeout. A run maps the gates it runs, and keeps the rows its key already has.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
GATE = "visual-lock"


class AColdOnlyRunMapsOnlyItsGates(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="tvd-coldmap-")
        self.led = os.path.join(self.d, ".gate_ledger.json")
        self.addCleanup(shutil.rmtree, self.d, True)

    def _map(self):
        import gate_ledger as L
        with open(os.path.join(self.d, L.MAP_NAME)) as f:
            return json.load(f).get("gates") or {}

    def test_a_cold_only_run_declares_only_the_gate_it_runs(self):
        env = dict(os.environ, TV_GATE_LEDGER=self.led, D2R_GATE_LOCK_KEY=self.led)
        env.pop("CI", None); env.pop("GITHUB_ACTIONS", None); env.pop("GATE_LEDGER", None)
        p = subprocess.run([sys.executable, os.path.join(HERE, "run_gates.py"), "--only", GATE],
                           cwd=os.path.dirname(HERE), env=env, capture_output=True, text=True, timeout=170)
        self.assertEqual(p.returncode, 0, (p.stdout + p.stderr)[-1500:])
        self.assertEqual(sorted(self._map()), [GATE],
                         "a cold --only run mapped gates it never ran - the whole-registry parse is back")

    def test_a_partial_map_keeps_its_rows_and_adds_the_missing_one(self):
        import gate_ledger as L
        import run_gates as R
        by = {g.name: g for g in R.GATES}
        other = "test_a_plain_gate_run_banks_its_passes"
        L.Ledger(path=self.led).prepare([by[GATE]])
        L.Ledger(path=self.led).prepare([by[other]])
        self.assertEqual(sorted(self._map()), sorted([GATE, other]),
                         "a second run threw away the rows its key already had")


    def test_the_self_arming_defer_holds_on_ci_too(self):
        import re
        src = open(os.path.join(HERE, "run_gates.py"), encoding="utf-8").read()
        m = re.search(r"\n    if (led is not None[^\n]*\n[^\n]*TV_SELF_ARMING_DEFER[^\n]*)", src)
        self.assertIsNotNone(m, "the self-arming defer is gone")
        self.assertNotIn("ci_blocks", m.group(1),
                         "CI skips the defer again: a Wilson gate dirties tv/.self_arming.jsonl mid-run on CI")


RED_PROOF = [
    {"why": "a cold --only run maps every registered gate again (>200 s in a prove sandbox; test_control timed out)",
     "file": "tv/run_gates.py",
     "find": "led.prepare([x for x in GATES if not only or x.name in only])  # ONLY-PREPARES-ITS-OWN",
     "replace": "led.prepare(GATES)  # ONLY-PREPARES-ITS-OWN", "matches": 1},
    {"why": "a run throws away the map rows its key already has",
     "file": "tv/gate_ledger.py",
     "find": '        rows = dict(self.map.get("gates") or {}) if self.map.get("key") == map_key(root) else {}\n',
     "replace": "        rows = {}\n", "matches": 1},
    {"why": "CI skips the self-arming defer, so a Wilson gate dirties the checkout mid-run (CI g red)",
     "file": "tv/run_gates.py",
     "find": "    if led is not None and not _GL.reuse_closed() \\\n",
     "replace": "    if led is not None and not _GL.ci_blocks() and not _GL.reuse_closed() \\\n", "matches": 1},
]

if __name__ == "__main__":
    unittest.main()
