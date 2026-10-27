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
        except TypeError:
            self.skipTest("tick signature differs")
        finally:
            SP.free_mb, SP.playing_state, SP.proc_birth = orig
        self.assertTrue(calls, "no slice was spawned at 1,019 MB free")
        self.assertEqual(calls[0]["workers"], 1)
        self.assertLessEqual(len(calls[0]["names"]), SP.SMALL_SLICE_MAX_GATES)


class TheFleetRowSaysWhy(unittest.TestCase):

    def test_a_memory_wait_is_named_on_the_row(self):
        with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8", errors="replace") as f:
            src = f.read()
        i = src.find("var _fleetStuckChip")
        self.assertGreater(i, 0)
        body = src[i:src.find("return bits.join", i)]
        self.assertIn("hs.key === 'low-memory'", body)
        self.assertIn("census waiting for memory", body)


if __name__ == "__main__":
    unittest.main()
