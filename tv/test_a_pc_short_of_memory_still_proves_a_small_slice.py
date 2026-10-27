# -*- coding: utf-8 -*-
"""GBL census-lowmem - A PC THAT NEVER HAS 1,536 MB FREE STILL MAKES ITS CENSUS PROGRESS.

His ALT (7.9 GB), 2026-10-27 on v3806: 1,019 MB free with the window already sent away, "low-memory" on 69 ticks,
143 gates owed, census stale -> every river lock shut, and the Fleet row said only "locks shut" for ever. Under the
full start, a MEASURED-idle PC with a sliceable owed list now starts a SMALL slice (one lane, a few gates). Never
beside his game, never on an unknown 'is he playing', never under MIN_FREE_MB_TO_START_SMALL, and never with nothing
to slice. Fixtures only: low free memory is simulated; nothing is spawned for real.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import self_prove as SP  # noqa: E402
import fixture_tmp  # noqa: E402

fixture_tmp.contain()

OWED = [("test_a", 10.0), ("test_b", 10.0), ("test_c", 10.0), ("test_d", 10.0), ("test_e", 10.0),
        ("test_f", 10.0), ("test_g", 10.0), ("test_h", 10.0)]


def _census(owed=True):
    c = {"state": "stale", "why": "fixture", "fingerprint": "fp"}
    if owed:
        c["owedGates"] = list(OWED)
    return c


def d(free, playing=False, owed=True):
    return SP.decide(_census(owed), ("installed", "fixture"), None, 0, {}, 100000.0, on=True, playing=playing,
                     free=free)


class TheSmallStart(unittest.TestCase):

    def test_the_measured_alt_starts_a_small_slice(self):
        r = d(1019)
        self.assertTrue(r["start"], "the ALT at 1,019 MB free stays refused for ever: %s" % r)
        self.assertTrue(r.get("small"))
        self.assertEqual(r["key"], "start-small")

    def test_a_full_start_is_unchanged(self):
        r = d(SP.MIN_FREE_MB_TO_START + 1)
        self.assertTrue(r["start"])
        self.assertFalse(r.get("small"))

    def test_never_beside_his_game_or_on_a_guess(self):
        self.assertEqual(d(1019, playing=True)["key"], "playing")
        self.assertEqual(d(1019, playing=None)["key"], "play-unknown")

    def test_never_under_the_small_floor_or_with_nothing_to_slice(self):
        self.assertEqual(d(SP.MIN_FREE_MB_TO_START_SMALL - 1)["key"], "low-memory")
        self.assertEqual(d(1019, owed=False)["key"], "low-memory")

    def test_the_small_floor_leaves_room_over_the_idle_running_floor(self):
        self.assertGreater(SP.MIN_FREE_MB_TO_START_SMALL, SP.MIN_FREE_MB_WHILE_RUNNING_IDLE + 256)


class TheTickSpawnsTheSmallSlice(unittest.TestCase):

    def test_a_small_start_spawns_one_lane_and_few_gates(self):
        calls = []

        def spawn(log_path, names=None, workers=None):
            calls.append({"names": names, "workers": workers})
            return 4242

        import tempfile
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "sp.json")
        orig = (SP.free_mb, SP.playing_state, SP.proc_birth)
        SP.free_mb = lambda: 1019
        SP.playing_state = lambda *a, **k: False
        SP.proc_birth = lambda pid: 1.0
        try:
            SP.tick(now_s=100000.0, busy=0, tree=("installed", "fixture"), census=_census(), path=path,
                    spawn_fn=spawn, env={"TV_SELF_PROVE": "1"})
        finally:
            SP.free_mb, SP.playing_state, SP.proc_birth = orig
        self.assertTrue(calls, "no slice was spawned at 1,019 MB free")
        self.assertEqual(calls[0]["workers"], 1)
        self.assertLessEqual(len(calls[0]["names"]), SP.SMALL_SLICE_MAX_GATES)


class ABusyPcNeverStarvesIntoASmallSlice(unittest.TestCase):

    def test_busy_past_the_starve_window_stays_busy_under_the_full_floor(self):
        r = SP.decide(_census(), ("installed", "fixture"), None, 99.0,
                      {"busySince": 1.0}, 10 * SP.BUSY_STARVE_S, playing=False, free=1019)
        self.assertFalse(r["start"], r)
        self.assertEqual(r["key"], "busy")


class TheFleetRowSaysWhy(unittest.TestCase):

    def test_a_memory_wait_is_named_on_the_row(self):
        with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8", errors="replace") as f:
            src = f.read()
        i = src.find("var _fleetStuckChip")
        self.assertGreater(i, 0)
        body = src[i:src.find("return bits.join", i)]
        self.assertIn("hs.key === 'low-memory'", body)
        self.assertIn("census waiting for memory", body)


class AMemoryStandAsideNamesItsGates(unittest.TestCase):
    """#193 - his ALT, 2026-10-27: 23 stand-asides in a row, each on the same BLIND gate the planner put first and alone
    (REG-1673); the stand-aside forgot the slice, so the next slice picked that gate again and 139 others never ran.
    A MEMORY stand-aside now names its gates for this census; one because he is playing names none."""

    def setUp(self):
        import tempfile
        import shutil
        self.d = tempfile.mkdtemp(prefix="memstall_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.store = os.path.join(self.d, ".self_prove.json")
        self._started = dict(SP._STARTED)
        SP._STARTED.update(pid=None, birth=None)
        self.addCleanup(lambda: (SP._STARTED.clear(), SP._STARTED.update(self._started)))

    CENSUS = {"state": "stale", "why": "fixture", "fingerprint": "fp", "blind": ["test_heavy"],
              "owedGates": [["test_heavy", 5], ["test_a", 1], ["test_b", 1]]}

    def _write(self, rec):
        import io
        import json
        with io.open(self.store, "w", encoding="utf-8") as fh:
            json.dump(rec, fh)

    def _stand_aside(self, playing, free, prior=None):
        from unittest import mock
        rec = {"pid": 4242, "pidBirth": 1234.5, "startedFor": "fp", "sliceGates": ["test_heavy"]}
        rec.update(prior or {})
        self._write(rec)
        killed = []
        with mock.patch.object(SP, "pid_alive", lambda pid: True), \
                mock.patch.object(SP, "proc_birth", lambda pid: 1234.5 if pid == 4242 else None), \
                mock.patch.object(SP, "is_ours", lambda pid, birth: True), \
                mock.patch.object(SP, "census_state", lambda: dict(self.CENSUS)), \
                mock.patch.object(SP, "tree_state", lambda: ("installed", "fixture")):
            SP.guard(now_s=5000.0, path=self.store, playing=playing, free=free,
                     kill_fn=lambda pid, birth: killed.append(pid) or True)
        self.assertEqual(killed, [4242], "PREMISE: the running slice was not stood aside")
        return SP.load(self.store)

    def test_a_memory_stand_aside_names_the_gates_it_could_not_finish(self):
        mem = self._stand_aside(playing=False, free=SP.MIN_FREE_MB_WHILE_RUNNING_IDLE - 100)
        self.assertEqual(mem.get("stalledGates"), ["test_heavy"], mem)
        self.assertEqual(mem.get("stalledFor"), "fp", mem)
        self.assertIsNone(mem.get("standingAsideForMemory"), "the slice's memory flag outlived the slice: %r" % mem)

    def test_a_stand_aside_for_his_game_names_no_gate(self):
        mem = self._stand_aside(playing=True, free=3000)
        self.assertFalse(mem.get("stalledGates"), "his game was booked as the gate's fault: %r" % mem)

    def test_stalled_gates_add_up_within_one_census_and_restart_with_a_new_one(self):
        same = self._stand_aside(playing=False, free=600, prior={"stalledGates": ["test_a"], "stalledFor": "fp"})
        self.assertEqual(same.get("stalledGates"), ["test_a", "test_heavy"], same)
        other = self._stand_aside(playing=False, free=600, prior={"stalledGates": ["test_old"], "stalledFor": "older"})
        self.assertEqual(other.get("stalledGates"), ["test_heavy"], other)

    def test_the_next_slice_proves_the_others_first(self):
        self._write({"stalledGates": ["test_heavy"], "stalledFor": "fp"})
        calls = []

        def spawn(log_path, names=None, workers=None):
            calls.append({"names": names, "workers": workers})
            return 4343
        orig = (SP.free_mb, SP.playing_state, SP.proc_birth)
        SP.free_mb = lambda: 1019
        SP.playing_state = lambda *a, **k: False
        SP.proc_birth = lambda pid: 1.0
        try:
            SP.tick(now_s=100000.0, busy=0, tree=("installed", "fixture"), census=dict(self.CENSUS), path=self.store,
                    spawn_fn=spawn, env={"TV_SELF_PROVE": "1"})
        finally:
            SP.free_mb, SP.playing_state, SP.proc_birth = orig
        self.assertTrue(calls, "no slice started beside a stalled gate")
        self.assertNotIn("test_heavy", calls[0]["names"], "the stalled BLIND gate went first again: %r" % calls)
        self.assertTrue(set(calls[0]["names"]) <= {"test_a", "test_b"}, calls)


RED_PROOF = [
    {"why": "#193 - a memory stand-aside forgets its slice again, so the same heavy gate is planned first every 30 min",
     "file": "tv/self_prove.py",
     "find": "            _memory_stall(mem, census, play_now)               # #193 - before _forget drops the slice's gates\n",
     "replace": "            pass\n",
     "matches": 1},
    {"why": "#193 - a stand-aside because he is playing books the gates as the cause",
     "file": "tv/self_prove.py",
     "find": "    if playing is True:\n        return\n    gates = [str(g) for g in (mem.get(\"sliceGates\") or []) if g]\n",
     "replace": "    gates = [str(g) for g in (mem.get(\"sliceGates\") or []) if g]\n",
     "matches": 1},
    {"why": "#193 - a second memory stand-aside drops the gates the first one named",
     "file": "tv/self_prove.py",
     "find": "    prior = [str(g) for g in (mem.get(\"stalledGates\") or []) if g] if mem.get(\"stalledFor\") == fp else []\n",
     "replace": "    prior = []\n",
     "matches": 1},
    {"why": "#193 - the planner ignores stalled gates, so a stalled BLIND gate is put first and alone again",
     "file": "tv/self_prove.py",
     "find": "            _stuck = (set(mem.get(\"stalledGates\") or []) if mem.get(\"stalledFor\") == census.get(\"fingerprint\")\n                      else set())\n",
     "replace": "            _stuck = set()\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main()
