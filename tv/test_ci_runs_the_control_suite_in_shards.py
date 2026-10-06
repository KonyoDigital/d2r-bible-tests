# -*- coding: utf-8 -*-
"""#160 — CI runs the control suite through the shard door. The law file stays put.

A push already starts test_control through tv/shard_suite.py. The agent workflow still
asks run_gates for that gate as one process, and that process is the long one inside its
shard. The heart maps a law by the first .py in Gate.argv, so the registered list stays
test_control.py. Only the command CI actually runs changes, and only for this gate.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
import sys as _sys  # noqa: E402
if HERE not in _sys.path:
    _sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402  - REG-1834: these print non-ASCII
_console_safe_enable()
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import run_gates as RG  # noqa: E402


def _gate(name):
    for g in RG.GATES:
        if g.name == name:
            return g
    raise AssertionError("no gate named %s" % name)


class TestCiRunsTheControlSuiteInShards(unittest.TestCase):

    def test_the_registered_law_is_still_the_control_file(self):
        g = _gate("test_control")
        pys = [os.path.basename(p) for p in g.argv if str(p).endswith(".py")]
        self.assertEqual(pys, ["test_control.py"], pys)

    def test_actions_starts_that_gate_through_the_shard_door(self):
        got = RG.gate_argv(_gate("test_control"), {"GITHUB_ACTIONS": "true"})
        self.assertEqual(os.path.basename(got[1]), "shard_suite.py", got)
        self.assertEqual(got[2:], ["test_control"], got)
        self.assertFalse(any(str(a).endswith("test_control.py") for a in got), got)

    def test_his_machine_runs_the_file(self):
        got = RG.gate_argv(_gate("test_control"), {})
        self.assertEqual(os.path.basename(got[-2]), "test_control.py", got)
        self.assertEqual(got[-1], "-v")

    def test_a_false_actions_flag_is_not_the_runner(self):
        got = RG.gate_argv(_gate("test_control"), {"GITHUB_ACTIONS": "false"})
        self.assertEqual(os.path.basename(got[-2]), "test_control.py", got)

    def test_another_suite_stays_one_process_on_actions(self):
        got = RG.gate_argv(_gate("test_agent"), {"GITHUB_ACTIONS": "true"})
        self.assertEqual(os.path.basename(got[-2]), "test_agent.py", got)
        self.assertEqual(got[-1], "-v")
        self.assertNotIn("shard_suite.py", " ".join(os.path.basename(str(a)) for a in got))


RED_PROOF = [
    {
        "why": "CI still runs the control suite as one process, so that shard stays the floor",
        "file": "run_gates.py",
        "find": "            and str((env if env is not None else os.environ).get(\"GITHUB_ACTIONS\") or \"\") == \"true\"):\n",
        "replace": "            and False):\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
