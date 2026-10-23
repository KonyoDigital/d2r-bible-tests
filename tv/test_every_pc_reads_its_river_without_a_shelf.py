# -*- coding: utf-8 -*-
"""REG-2641 - EVERY PC READS ITS RIVER ON THE FLEET WITHOUT ANYONE OPENING ITS SHELF.

His fleet, 2026-10-24 01:37, right after the Mac and Dean took v3792 and restarted: both rows read "river UNKNOWN" with
"this console has not computed its river since it started - nothing has asked for the river yet, and the beacon never
computes it itself". Only the SHELF view and the doctor asked /api/river, so a healthy PC nobody sat at (Dean mid
re-prove, the ALT, the box) read UNKNOWN after every restart until somebody opened its shelf - and its stuck reading was
never taken, because the beacon walks the stamp log only beside a river it already holds.

The river warmer (tvd-river-warm) computes the SAME lanes the route serves (_river_lanes_block) into the SAME cache
(_river_remember) a minute after start and whenever that cache is RIVER_WARM_EVERY_S old; a fresh read is left alone; a
failed read stays a failure, never an empty river. Driven in-process with the lanes block stood in; his tree is never
read. RED_PROOF below. [[unknown-stays-unknown]] [[the-unjoined-end]]
"""
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

import control_app as ca  # noqa: E402

NOW = 1792800000000
GOOD = {"ok": True, "shelf": 9, "unknown": 0,
        "lanes": [{"name": "INTAKE", "byStation": {"EMPTY": 2, "JOIN": 1}},
                  {"name": "TOMBSTONE", "byStation": {"ROUTED": 6}}]}

RED_PROOF = [
    {
        "why": "REG-2641 (r4) - a loaded machine does not hold a refresh",
        "file": "control_app.py",
        "find": "    if cpu >= _triage_max_cpu():\n        return \"the CPU is %.0f%% busy\" % cpu\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2641 (r4) - a failed boot fill is retried with no brake, beside his game",
        "file": "control_app.py",
        "find": "    if _RIVER_LAST.get(\"good\") is not None or _RIVER_LAST.get(\"fail\") is not None:\n",
        "replace": "    if _RIVER_LAST.get(\"good\") is not None:\n",
        "matches": 1,
    },
    {
        "why": "REG-2641 (r4) - an unmeasured CPU reads as an idle machine",
        "file": "control_app.py",
        "find": "    if cpu is None:\n        return \"this machine's CPU could not be measured\"\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2641 (r4) - a live capture does not hold a refresh",
        "file": "control_app.py",
        "find": "        if _capture_is_live() or _agent_alive():\n            return \"a capture is live on this machine\"\n",
        "replace": "        pass\n",
        "matches": 1,
    },
    {
        "why": "REG-2641 (r3) - a refresh walks the shelf twice beside his game and a live capture",
        "file": "control_app.py",
        "find": "        held = (_brake or _river_warm_brake)()\n        if held:\n",
        "replace": "        held = None\n        if held:\n",
        "matches": 1,
    },
    {
        "why": "REG-2641 (r3) - the first fill after a restart is braked too: a restart mid-session reads UNKNOWN all session",
        "file": "control_app.py",
        "find": "    if _RIVER_LAST.get(\"good\") is not None or _RIVER_LAST.get(\"fail\") is not None:\n        held = (_brake",
        "replace": "    if True:\n        held = (_brake",
        "matches": 1,
    },
    {
        "why": "REG-2641 (r3) - an older warm walk is stamped over a newer shelf read",
        "file": "control_app.py",
        "find": "    if (_RIVER_LAST.get(\"good\"), _RIVER_LAST.get(\"fail\")) != before:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-2641 (r3) - an UNKNOWN game probe reads as 'not playing'",
        "file": "control_app.py",
        "find": "    if _playing is not False:\n        return \"D2R is running here",
        "replace": "    if _playing is True:\n        return \"D2R is running here",
        "matches": 1,
    },
    {
        "why": "REG-2641 (r3) - the loop stamps its beat and never warms",
        "file": "control_app.py",
        "find": "            _lane_tick('tvd-river-warm', dead_after_s=RIVER_WARM_DEAD_AFTER_S)\n            _river_warm_once()\n",
        "replace": "            _lane_tick('tvd-river-warm', dead_after_s=RIVER_WARM_DEAD_AFTER_S)\n",
        "matches": 1,
    },
    {
        "why": "REG-2641 (r3) - a harness console starts the warmer and walks a shelf during a gate run",
        "file": "control_app.py",
        "find": "\"tvd-retro-triage\", \"tvd-orphan-fold\", \"tvd-river-warm\")",
        "replace": "\"tvd-retro-triage\", \"tvd-orphan-fold\")",
        "matches": 1,
    },
    {
        "why": "REG-2641 - the warmer is never started: every restarted PC reads 'river UNKNOWN' until its shelf is opened",
        "file": "control_app.py",
        "find": "        (\"tvd-river-warm\", _river_warm_loop),\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2641 - a console that never computed its river is not due a read",
        "file": "control_app.py",
        "find": "    if not newest:\n        return True, \"no river computed since this console started\"\n",
        "replace": "    if not newest:\n        return False, \"no river computed since this console started\"\n",
        "matches": 1,
    },
    {
        "why": "REG-2641 - a stale river is never read again: the fleet carries a river hours old as current",
        "file": "control_app.py",
        "find": "    if age >= RIVER_WARM_EVERY_S:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-2641 - the warmer says it computed and keeps nothing for the beacon",
        "file": "control_app.py",
        "find": "    if err is not None:\n        _river_remember(error=err)\n    else:\n        _river_remember(lanes)\n",
        "replace": "    pass\n",
        "matches": 1,
    },
    {
        "why": "REG-2641 - the route computes its own lanes again, so the warmer and the shelf can drift",
        "file": "control_app.py",
        "find": "                _lanes = _river_lanes_block()\n",
        "replace": "                _lanes = {\"ok\": False, \"why\": \"inline\"}\n",
        "matches": 1,
    },
]


class _Cache(unittest.TestCase):
    def setUp(self):
        saved = dict(ca._RIVER_LAST)
        self.addCleanup(lambda: (ca._RIVER_LAST.clear(), ca._RIVER_LAST.update(saved)))
        ca._RIVER_LAST.clear()
        ca._RIVER_LAST.update({"good": None, "fail": None})
        p = mock.patch.object(ca, "_river_stuck_for_wire", lambda now=None, **k: [])
        p.start()
        self.addCleanup(p.stop)
        t = mock.patch.object(ca, "_triage_for_wire", lambda: {"ok": True})
        t.start()
        self.addCleanup(t.stop)
        self.clock = [NOW / 1000.0]
        c = mock.patch("time.time", lambda: self.clock[0])
        c.start()
        self.addCleanup(c.stop)


class AWarmerReadsTheRiver(_Cache):

    def test_a_restarted_console_reads_its_river_without_a_shelf(self):
        before = ca._river_for_wire(NOW)
        self.assertIsNone(before["lanes"], "PREMISE: a fresh console already holds a river")
        self.assertIsNone(before["stuck"], "PREMISE: a fresh console already has a stuck reading")
        calls = []
        with mock.patch.object(ca, "_river_lanes_block", lambda: calls.append(1) or GOOD):
            why = ca._river_warm_once(NOW, _brake=lambda: "playing")
            after = ca._river_for_wire(NOW)
        self.assertEqual(calls, [1], "the warmer did not compute the river of a console that has none: %s" % why)
        self.assertEqual(after["lanes"], {"EMPTY": 2, "JOIN": 1, "ROUTED": 6},
                         "the beacon still carries no river after the warmer ran: %r" % after)
        self.assertEqual(after["stuck"], [], "a healthy PC's stuck reading is not 'flowing' ([]): %r" % after["stuck"])
        self.assertEqual(after.get("shelf"), 9)

    def test_a_fresh_river_is_left_alone(self):
        ca._RIVER_LAST["good"] = {"ts": NOW - 30 * 1000, "n": 1, "stations": {"EMPTY": 1}}
        with mock.patch.object(ca, "_river_lanes_block", lambda: self.fail("a fresh river was walked again")):
            why = ca._river_warm_once(NOW)
        self.assertTrue(why.startswith("fresh"), why)

    def test_a_stale_river_is_read_again(self):
        ca._RIVER_LAST["good"] = {"ts": NOW - (ca.RIVER_WARM_EVERY_S + 5) * 1000, "n": 1, "stations": {"EMPTY": 1}}
        calls = []
        with mock.patch.object(ca, "_river_lanes_block", lambda: calls.append(1) or GOOD):
            ca._river_warm_once(NOW, _brake=lambda: None)
        self.assertEqual(calls, [1], "a river %d s old was not read again" % (ca.RIVER_WARM_EVERY_S + 5))

    def test_a_failed_read_stays_a_failure_never_an_empty_river(self):
        def _boom():
            raise RuntimeError("router down")
        with mock.patch.object(ca, "_river_lanes_block", _boom):
            ca._river_warm_once(NOW)
        out = ca._river_for_wire(NOW)
        self.assertIsNone(out["lanes"], "a failed read became a river: %r" % out)
        self.assertIsNone(out["stuck"], "a failed read became a stuck reading: %r" % out)
        self.assertIn("could not be read", out["why"])
        # and a failure is itself a read: no retry storm every minute (one clock: the cache's stamp and the tick's)
        walked = []
        with mock.patch.object(ca, "_river_lanes_block", lambda: walked.append(1) or GOOD):
            self.clock[0] = NOW / 1000.0 + 60
            why = ca._river_warm_once(NOW + 60 * 1000, _brake=lambda: None)
            self.assertEqual(walked, [], "a failure 60 s old was retried at once: %s" % why)
            self.clock[0] = NOW / 1000.0 + ca.RIVER_WARM_EVERY_S
            why = ca._river_warm_once(NOW + ca.RIVER_WARM_EVERY_S * 1000, _brake=lambda: "playing")
            self.assertEqual(walked, [], "a failed boot fill was retried beside his game: %s" % why)
            ca._river_warm_once(NOW + ca.RIVER_WARM_EVERY_S * 1000, _brake=lambda: None)
        self.assertEqual(walked, [1], "a failure RIVER_WARM_EVERY_S old was never read again")

    def test_a_refresh_stands_down_beside_his_game_and_the_first_fill_does_not(self):
        ca._RIVER_LAST["good"] = {"ts": NOW - (ca.RIVER_WARM_EVERY_S + 5) * 1000, "n": 1, "stations": {"EMPTY": 1}}
        with mock.patch.object(ca, "_river_lanes_block", lambda: self.fail("a refresh walked the shelf beside his game")):
            why = ca._river_warm_once(NOW, _brake=lambda: "D2R is running here")
        self.assertTrue(why.startswith("held"), why)
        with mock.patch.object(ca, "_d2r_running_here", lambda: (None, "probe")):
            self.assertIn("cannot be ruled out", ca._river_warm_brake() or "", "an UNKNOWN game probe did not refuse")
        clear = dict(_d2r_running_here=lambda: (False, "probe"), _capture_is_live=lambda: False,
                     _agent_alive=lambda: False, _cpu_busy_pct=lambda sample_s=None: 5.0)
        with mock.patch.multiple(ca, **clear):
            self.assertIsNone(ca._river_warm_brake(), "PREMISE: a quiet machine is braked")
        for k, v, said in (("_capture_is_live", lambda: True, "capture"), ("_cpu_busy_pct", lambda sample_s=None: None,
                           "could not be measured"), ("_cpu_busy_pct", lambda sample_s=None: 100.0, "busy")):
            with mock.patch.multiple(ca, **dict(clear, **{k: v})):
                self.assertIn(said, ca._river_warm_brake() or "", "%s did not hold a refresh" % k)

    def test_a_newer_read_is_never_overwritten_by_the_warm(self):
        newer = {"ts": NOW, "n": 99, "stations": {"PRINTER": 4}}

        def _walk():
            ca._RIVER_LAST["good"] = newer          # the shelf published while the warm walked
            return GOOD
        with mock.patch.object(ca, "_river_lanes_block", _walk):
            why = ca._river_warm_once(NOW)
        self.assertIs(ca._RIVER_LAST["good"], newer, "the warm stamped its older walk over a newer shelf read: %s" % why)


class TheWarmerIsWired(unittest.TestCase):

    def test_the_roster_starts_it_and_the_route_shares_its_block(self):
        import inspect
        src = inspect.getsource(ca.start_background_watchers)
        self.assertIn('("tvd-river-warm", _river_warm_loop)', src, "the warmer is not in the watcher roster")
        loop = inspect.getsource(ca._river_warm_loop)
        self.assertIn("_lane_tick('tvd-river-warm'", loop, "the warmer stamps no beat, so a dead warmer is invisible")
        self.assertIn("            _river_warm_once()\n", loop, "the warmer ticks and never warms")
        self.assertIn("tvd-river-warm", ca._HARNESS_ONLY_SKIP, "a harness console walks a shelf beside the gate run")
        import auto_scope
        self.assertEqual(auto_scope.LANE_FN.get("tvd-river-warm"), "_river_warm_loop", "the warmer declares no scope")
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            text = fh.read()
        route = text[text.index('if path == "/api/river":'):]
        route = route[:route.index("_river_remember(_lanes)")]
        self.assertIn("_lanes = _river_lanes_block()", route,
                      "/api/river computes its own lanes - the warmer's river and the shelf's can drift")


if __name__ == "__main__":
    unittest.main(verbosity=2)
