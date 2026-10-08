# -*- coding: utf-8 -*-
"""REG-1997 - EVERY LAW THE PROVER RUNS IS TOLD HOW MANY PROVING LANES RUN BESIDE IT.

MEASURED: the v3603 push #8 clean wave ran test_control in one of 4 lanes beside three other law runs, and its
cheap-subset CPU budget went red; alone in main minutes later it read 6,607 ms CPU on a fast core against 9,000 ms. A law
that judges its own cost cannot tell the prover's self-inflicted load from its code unless it is told, so the prover hands
every run HEART2_LANES (the lanes running right now, 1 outside a parallel run), and test_control's cheap-subset case
prints its readings and leaves the budget UNMEASURED when it is above 1 - the push's suite stage and CI judge it with no
lanes.

Drives the REAL heart2._run_gate on a probe script that writes back what it was handed, and anchors test_control's
branch (code only, exactly once).
"""
import io
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

BRANCH = "        if _lanes > 1:\n"


class ALawIsToldHowManyLanesRun(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="h2lanes.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(self.tv)
        with io.open(os.path.join(self.tv, "probe_gate.py"), "w", encoding="utf-8") as fh:
            fh.write("import os, io\nio.open('lanes.txt', 'w').write(str(os.environ.get('HEART2_LANES')))\n")
        self._prev = H.LANES_NOW
        self.addCleanup(lambda: setattr(H, "LANES_NOW", self._prev))

    def _told(self, lanes):
        H.LANES_NOW = lanes
        ok, tail = H._run_gate(self.tv, "probe_gate.py", timeout=60)
        with io.open(os.path.join(self.tv, "lanes.txt"), encoding="utf-8") as fh:
            return fh.read().strip()

    def test_a_run_inside_four_lanes_is_told_four(self):
        self.assertEqual(self._told(4), "4", "a law run inside 4 parallel lanes was not told so")

    def test_a_run_outside_a_parallel_run_is_told_one(self):
        self.assertEqual(self._told(1), "1")

    def test_the_real_lanes_set_the_count_while_they_run(self):
        """Drives the REAL _prove_gates with 2 lanes: each gate sees LANES_NOW = 2 while it runs, and 1 afterwards."""
        seen = []

        def _sandbox(say=print):
            d = tempfile.mkdtemp(prefix="lane.", dir=self.root)
            os.makedirs(os.path.join(d, "tv"))
            return os.path.join(d, "tv"), d

        def _gate(sandbox, name, filename, proofs, say):
            seen.append(H.LANES_NOW)
            return H.PROVEN, [H.PROVEN] * len(proofs)

        sb, pg = H.make_sandbox, H._prove_gate
        self.addCleanup(lambda: (setattr(H, "make_sandbox", sb), setattr(H, "_prove_gate", pg)))
        H.make_sandbox, H._prove_gate = _sandbox, _gate
        have = [(n, n + ".py", [{"file": "x.py", "find": "a", "replace": "b", "matches": 1}]) for n in ("g1", "g2", "g3")]
        H.LANES_NOW = 1
        H._prove_gates(have, say=lambda *a, **k: None, workers=2)
        self.assertEqual(seen, [2, 2, 2], "the lanes did not set the count their laws are told: %s" % seen)
        self.assertEqual(H.LANES_NOW, 1, "the count outlived the lanes")

    def test_the_cheap_subset_withholds_its_verdict_only_above_one_lane(self):
        with io.open(os.path.join(HERE, "test_control.py"), encoding="utf-8") as fh:
            src = fh.read()
        code = "\n".join(l for l in src.split("\n") if not l.lstrip().startswith("#"))
        i = code.find("def test_the_cheap_subset_is_actually_CHEAP")
        self.assertGreater(i, 0)
        blk = code[i:code.find("\n    def ", i + 10)]
        self.assertEqual(blk.count(BRANCH), 1, "the cheap-subset case lost its lanes branch, or it now fires at 1 lane")
        self.assertEqual(blk.count('_lanes = int(os.environ.get("HEART2_LANES") or 1)'), 1)

    def test_the_button_matrix_waits_longer_only_beside_other_lanes(self):
        """REG-2122 - the v3631 push proved test_button_matrix beside four lanes and its fixed 20 s 'STOP -> dark' wait timed
        out (already red untampered). Its waits now double with the prover's deadline when HEART2_LANES > 1, and never alone."""
        import subprocess, sys
        got = {}
        for lanes in ("4", "1", ""):
            env = dict(os.environ)
            env["HEART2_LANES"] = lanes
            r = subprocess.run([sys.executable, "-c", "import test_button_matrix as M; print(M._WAIT_SCALE)"],
                               cwd=HERE, env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr[-400:])
            got[lanes] = r.stdout.strip().splitlines()[-1]
        self.assertEqual(got, {"4": "2", "1": "1", "": "1"}, "the matrix's waits do not follow the lanes beside it: %r" % got)


RED_PROOF = [
    {"why": "REG-1997 - the prover stops telling a law how many lanes run beside it, so a cost law judges the prover's load",
     "file": "heart2.py",
     "find": '    env["HEART2_LANES"] = str(int(LANES_NOW or 1))   # REG-1997 - the lanes running beside this law right now\n',
     "replace": "",
     "matches": 1},
    {"why": "REG-1997 - the lane count is never set while lanes run",
     "file": "heart2.py",
     "find": "    LANES_NOW = n\n",
     "replace": "    LANES_NOW = 1\n",
     "matches": 1},
    {"why": "REG-1997 - the cheap-subset case withholds its verdict even with one lane (it would never judge again)",
     "file": "tv/test_control.py",
     "find": "        if _lanes > 1:\n",
     "replace": "        if _lanes > 0:\n",
     "matches": 1},
    {"why": "REG-2122 - the button matrix's waits stay fixed beside four proving lanes (STOP -> dark timed out on the v3631 push)",
     "file": "tv/test_button_matrix.py",
     "find": "_WAIT_SCALE = 2 if _LANES > 1 else 1\n",
     "replace": "_WAIT_SCALE = 1\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
