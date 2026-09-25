# -*- coding: utf-8 -*-
"""REG-1283 — A SCRATCH CONSOLE LEAVES NO LANE TRACE IN HIS WORLD.

lane_trace.DIR was always his live tv/.lane_trace, so every scratch console - the render gate's on each push,
any probe's - stamped HIS lane traces, and those files are the corroborator's second witness that his own
loops ran. MEASURED 2026-09-25: a scratch console booted at 06:07:12 wrote .lane_trace/_orphan_exit_loop.json
at 06:07:18. loop_corroborate read the same hard-coded path, so a fixture world also READ his traces.

  · DRIVEN (a fresh interpreter, TV_HIST = a fixture world outside the tree): lane_trace.note() writes
    into the fixture's .lane_trace and his live trace for that lane is untouched; every loop_corroborate
    trace path resolves inside the fixture world.
  · PREMISE: with no TV_HIST the directory is his tree's, as his console needs.
RED_PROOF below.
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

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

LANE = "reg1283-law-probe"


def _child(code, hist=None):
    env = dict(os.environ)
    env.pop("TV_HIST", None)
    if hist:
        env["TV_HIST"] = hist
    r = subprocess.run([sys.executable, "-c", code], cwd=HERE, capture_output=True, text=True, timeout=120, env=env)
    if r.returncode != 0:
        raise AssertionError("the child did not run - UNKNOWN, not passing: %s" % r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AScratchConsoleLeavesNoTraceInHisWorld(unittest.TestCase):

    def setUp(self):
        self.world = tempfile.mkdtemp(prefix="trace-world-")
        self.live = os.path.join(HERE, ".lane_trace", LANE + ".json")

    def tearDown(self):
        shutil.rmtree(self.world, ignore_errors=True)
        if os.path.exists(self.live):          # only ever this law's own probe lane, never one of his
            os.remove(self.live)

    def test_a_fixture_world_writes_and_reads_its_own_traces(self):
        got = _child(
            "import json, lane_trace as lt, loop_corroborate as lc\n"
            "lt.note(%r, verdict='probe')\n"
            "print(json.dumps({'dir': lt.DIR, 'written': lt.path_of(%r),"
            " 'reads': [v[1] for v in lc.LOOPS.values() if '.lane_trace' in v[1]]}))" % (LANE, LANE),
            hist=self.world)
        world = os.path.realpath(self.world)
        self.assertTrue(os.path.realpath(got["dir"]).startswith(world), "a fixture world's traces went to %r" % got["dir"])
        self.assertTrue(os.path.isfile(got["written"]), "the probe trace was not written where lane_trace says")
        self.assertFalse(os.path.exists(self.live), "a fixture world wrote a trace into HIS .lane_trace")
        self.assertTrue(got["reads"], "premise: the corroborator reads lane traces")
        bad = [p for p in got["reads"] if not os.path.realpath(p).startswith(world)]
        self.assertEqual(bad, [], "the corroborator in a fixture world reads HIS traces: %r" % bad)

    def test_premise_no_fixture_means_his_tree(self):
        got = _child("import json, lane_trace as lt\nprint(json.dumps({'dir': lt.DIR}))")
        self.assertEqual(os.path.realpath(got["dir"]), os.path.realpath(os.path.join(HERE, ".lane_trace")))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1283 - lane traces go to his tree whatever the world: scratch consoles stamp his loops' witnesses",
        "file": "lane_trace.py",
        "find": "DIR = os.path.join(_world(), \".lane_trace\")\n",
        "replace": "DIR = os.path.join(HERE, \".lane_trace\")\n",
        "matches": 1,
    },
    {
        "why": "REG-1283 - the corroborator reads a hard-coded live trace again, whatever world it is in",
        "file": "loop_corroborate.py",
        "find": "_lt.path_of(\"_orphan_watch\")",
        "replace": "os.path.join(HERE, \".lane_trace\", \"_orphan_watch.json\")",
        "matches": 1,
    },
]
