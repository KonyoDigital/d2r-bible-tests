# -*- coding: utf-8 -*-
"""v3848 SPEED - `run_gates.py --rerun-failed` RUNS ONLY WHAT THE LAST RUN LEFT RED.

v3847 spent 5+ h re-running full sets after a red. The rule (FAST_GATE.md) is: after a red run, rerun ONLY the
failed gates plus the gates the fix touches. This law pins the mechanism: a run records its red names in this
worktree's git dir; --rerun-failed reads them back (a suffix like '(undeclared SKIP)' is the same gate), adds any
--only names, refuses when nothing is recorded, and refuses to combine with a set-picking flag.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_gates as R  # noqa: E402


class ARerunRunsOnlyTheLastReds(unittest.TestCase):
    def setUp(self):
        fd, self.p = tempfile.mkstemp(prefix="tvd-lastfailed-", suffix=".json")
        os.close(fd)
        os.unlink(self.p)
        self.addCleanup(lambda: os.path.exists(self.p) and os.unlink(self.p))
        m = mock.patch.object(R, "_last_failed_path", lambda: self.p)
        m.start()
        self.addCleanup(m.stop)

    def test_the_recorded_reds_come_back_as_gate_names(self):
        R._write_last_failed(["visual-lock", "visual-lock (undeclared SKIP)", "test_control"], "abc")
        names, why = R._read_last_failed()
        self.assertEqual(names, ["visual-lock", "test_control"], why)

    def test_nothing_recorded_refuses(self):
        names, why = R._read_last_failed()
        self.assertIsNone(names, "a rerun with no recorded run must refuse, never run every gate")

    def test_rerun_runs_exactly_the_reds_plus_the_named(self):
        R._write_last_failed(["visual-lock"], "abc")
        seen = {}

        def fake_run(only, **kw):
            seen["only"] = list(only or [])
            raise SystemExit(0)
        with mock.patch.object(R, "run", fake_run), mock.patch.object(R, "_claim_the_tree", lambda: None), \
                mock.patch.object(R, "_parallel_light", lambda a, o: (None, None)):
            with self.assertRaises(SystemExit):
                R.main(["run_gates.py", "--rerun-failed", "--only", "test_control"])
        self.assertEqual(seen.get("only"), ["visual-lock", "test_control"])

    def test_it_does_not_combine_with_a_set_picking_flag(self):
        R._write_last_failed(["visual-lock"], "abc")
        for flag in ("--full", "--fast"):
            self.assertEqual(R.main(["run_gates.py", "--rerun-failed", flag]), 2, flag)

    def test_the_cli_refuses_with_nothing_recorded(self):
        env = dict(os.environ, GIT_DIR=tempfile.mkdtemp(prefix="tvd-nogit-"))
        p = subprocess.run([sys.executable, os.path.join(HERE, "run_gates.py"), "--rerun-failed"],
                           cwd=os.path.dirname(HERE), env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 2, (p.stdout + p.stderr)[-800:])
        self.assertIn("NO gate ran", p.stdout)


RED_PROOF = [
    {"why": "v3848 - a '(undeclared SKIP)' red is read as an unknown gate name",
     "file": "run_gates.py",
     "find": "        n = n.split(\" (\")[0]\n",
     "replace": "",
     "matches": 1},
    {"why": "v3848 - --rerun-failed ignores the recorded reds",
     "file": "run_gates.py",
     "find": "        only = a.only = _rf\n",
     "replace": "        only = a.only = [n for n in (a.only or [])]\n",
     "matches": 1},
    {"why": "v3848 - --rerun-failed combines with --full",
     "file": "run_gates.py",
     "find": "        if a.shard or a.full or a.fast:\n",
     "replace": "        if a.shard:\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
