# -*- coding: utf-8 -*-
"""REG-1624 — A PROOF RUNS ONLY WHILE THE GAME IS OFF, AND YIELDS THE MOMENT IT STARTS.

His words, 2026-09-30, after closing Boosteroid on the ALT so it could prove: "future wise it needs to be working in
parallel somehow so when logging off and the game is off ... it can do whats needed but shadow reader when game start
should be triggered regardless. the shadow reader is always on when the game is on regardless of the console" - and
"everything should work smoothly regardless of each other with an intelligent architecture that makes it all work
consecutively".

MEASURED before the change, on the ALT with the game off and the console freshly relaunched: the prover's own probes
said playing False, 1,781 MB available - and its start bar was 2,048, so it could never start at all. And a proof that
did run was asked to stand aside only on the lane's 10-minute tick, so it could run beside his game for up to ten.

Driven, joint by joint:
  1. the loop - the rescue loop's one call (_self_prove_dispatch) runs the whole tick every 10 min and, between
     ticks, the cheap guard on every 10 s tick WHILE a proof runs (never while none does).
  2. the guard - asks only "is he playing" and "how much memory is left"; when stand_aside() says go it runs the
     whole tick at once, which kills, books the stand-aside and cools down through the one door it always had.
  3. the bar - with the game off, a proof starts at MIN_FREE_MB_TO_START (1,536), still never while he plays and never
     under the running floor.
Nothing here kills a process or starts a prover: every kill and every tick is a recorded fake. RED_PROOF below.
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

_WORLD = tempfile.mkdtemp(prefix="proof_yields_")
os.environ["TV_HIST"] = _WORLD
os.environ["TV_SESSIONS"] = os.path.join(_WORLD, "sessions.jsonl")

import self_prove as SP  # noqa: E402
import control_app as ca  # noqa: E402

RED_PROOF = [
    {"why": "REG-1624 - the guard never stands a running proof aside: it waits for the 10-minute tick",
     "file": "self_prove.py",
     "find": "        aside, _why = stand_aside(play_now, free_now)\n        if not aside:\n            return None\n",
     "replace": "        aside, _why = False, ''\n        if not aside:\n            return None\n", "matches": 1},
    {"why": "REG-1624 - the loop never asks the guard between ticks, so a proof runs beside his game for 10 minutes",
     "file": "control_app.py",
     "find": "    if isinstance(sp, dict) and (sp.get(\"running\") or sp.get(\"key\") in (\"running\", \"start\", \"aside-survived\")):\n        return \"guard\"\n",
     "replace": "    if False:\n        return \"guard\"\n", "matches": 1},
    {"why": "REG-1624 - the dispatch forgets to call the guard it chose",
     "file": "control_app.py",
     "find": "    elif step == \"guard\":\n        _self_prove_guard()",
     "replace": "    elif step == \"guard\":\n        pass", "matches": 1},
    {"why": "REG-1624 - the start bar is the stream-era 2048 again: an idle 8 GB ALT never starts a proof",
     "file": "self_prove.py",
     "find": "MIN_FREE_MB_TO_START = 1536\n",
     "replace": "MIN_FREE_MB_TO_START = 2048\n", "matches": 1},
    {"why": "REG-1624 - the guard runs a tick even when no proof is running (a 10 s full tick on an idle PC)",
     "file": "self_prove.py",
     "find": "        if not (mem.get(\"pid\") or _STARTED.get(\"pid\")):\n            return None\n",
     "replace": "        if False:\n            return None\n", "matches": 1},
]


class TheLoopAsksTheGuardOnlyWhileAProofRuns(unittest.TestCase):
    def test_the_step(self):
        first, every = ca.SELF_PROVE_FIRST_TICK, ca.SELF_PROVE_EVERY_TICKS
        self.assertEqual(ca._self_prove_step(first, {}), "tick")
        self.assertEqual(ca._self_prove_step(first + every, {"running": True}), "tick", "the whole tick keeps its slot")
        self.assertEqual(ca._self_prove_step(first + 1, {"running": True, "key": "running"}), "guard")
        self.assertEqual(ca._self_prove_step(first + 1, {"running": False, "key": "aside-survived"}), "guard",
                         "a prover that outlived its kill must keep being asked to end")
        self.assertIsNone(ca._self_prove_step(first + 1, {"running": False, "key": "current"}),
                          "the guard ran with no proof running")
        self.assertIsNone(ca._self_prove_step(first + 1, None))

    def test_the_dispatch_calls_what_it_chose(self):
        calls = []
        with mock.patch.object(ca, "_self_prove_tick", lambda: calls.append("tick")), \
                mock.patch.object(ca, "_self_prove_guard", lambda: calls.append("guard")), \
                mock.patch.dict(ca._SELF_PROVE, {"running": True, "key": "running"}, clear=True):
            ca._self_prove_dispatch(ca.SELF_PROVE_FIRST_TICK)
            ca._self_prove_dispatch(ca.SELF_PROVE_FIRST_TICK + 1)
            ca._self_prove_dispatch(ca.SELF_PROVE_FIRST_TICK + 2)
        self.assertEqual(calls, ["tick", "guard", "guard"])

    def test_the_rescue_loop_goes_through_the_dispatch(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        loop = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_console_rescue_loop")
        called = {c.func.id for c in ast.walk(loop) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
        self.assertIn("_self_prove_dispatch", called, "the rescue loop no longer reaches the self-prove lane")
        self.assertNotIn("_self_prove_tick", called, "a second, unguarded door into the lane from the loop")


class TheGuardStandsARunningProofAside(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="guard_store_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.store = os.path.join(self.d, ".self_prove.json")
        self.ticks = []
        self._started = dict(SP._STARTED)
        SP._STARTED.update(pid=None, birth=None)
        self.addCleanup(lambda: (SP._STARTED.clear(), SP._STARTED.update(self._started)))

    def _running(self):
        with io.open(self.store, "w", encoding="utf-8") as fh:
            json.dump({"pid": 4242, "pidBirth": 1234.5, "startedFor": "fp"}, fh)

    def _tick(self, **kw):
        self.ticks.append(kw)
        return {"key": "stood-aside", "running": False}

    def test_no_proof_running_asks_nothing(self):
        self.assertIsNone(SP.guard(path=self.store, playing=True, free=100, _tick=self._tick))
        self.assertEqual(self.ticks, [], "the guard ran the tick with no proof running")

    def test_a_proof_beside_nothing_keeps_running(self):
        self._running()
        self.assertIsNone(SP.guard(path=self.store, playing=False, free=3000, _tick=self._tick))
        self.assertEqual(self.ticks, [])

    def test_the_game_starting_stands_it_aside_at_once(self):
        self._running()
        r = SP.guard(path=self.store, playing=True, free=3000, _tick=self._tick)
        self.assertEqual(r["key"], "stood-aside")
        self.assertEqual(len(self.ticks), 1)
        self.assertIs(self.ticks[0]["playing"], True, "the tick was not told what the guard saw")

    def test_memory_under_the_running_floor_stands_it_aside(self):
        self._running()
        SP.guard(path=self.store, playing=False, free=SP.MIN_FREE_MB_WHILE_RUNNING - 100, _tick=self._tick)
        self.assertEqual(len(self.ticks), 1)

    def test_the_real_tick_kills_through_its_one_door_and_books_it(self):
        self._running()
        killed = []
        with mock.patch.object(SP, "is_ours", lambda pid, birth: True), \
                mock.patch.object(SP, "census_state", lambda: {"state": "missing", "why": "fixture"}), \
                mock.patch.object(SP, "tree_state", lambda: ("installed", "fixture")):
            r = SP.guard(now_s=5000.0, path=self.store, playing=True, free=3000,
                         kill_fn=lambda pid, birth: killed.append(pid) or True)
        self.assertEqual(killed, [4242], "the running proof was not ended when he started playing")
        self.assertEqual(r.get("key"), "stood-aside", r)
        mem = SP.load(self.store)
        self.assertEqual(mem.get("stoodAside"), 1, "the stand-aside was not booked (it would read as a failure)")
        self.assertIsNone(mem.get("pid"))


class AProofStartsWhenTheGameIsOffAndMemoryAllows(unittest.TestCase):
    def d(self, free, playing=False):
        return SP.decide({"state": "missing", "why": "fixture", "fingerprint": "fp"}, ("installed", "fixture"), None, 0,
                         {}, 100000.0, on=True, playing=playing, free=free)

    def test_the_idle_alt_can_start(self):
        self.assertTrue(self.d(1781)["start"], "the measured idle ALT (1,781 MB available) still cannot start a proof")

    def test_never_beside_his_game_and_never_near_the_floor(self):
        self.assertEqual(self.d(6000, playing=True)["key"], "playing")
        self.assertEqual(self.d(SP.MIN_FREE_MB_TO_START - 1)["key"], "low-memory")
        self.assertGreater(SP.MIN_FREE_MB_TO_START, SP.MIN_FREE_MB_WHILE_RUNNING + 256,
                           "a proof must start with room above the floor it stands aside at")


if __name__ == "__main__":
    unittest.main(verbosity=2)
