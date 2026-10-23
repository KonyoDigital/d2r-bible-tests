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
        "find": "        _river_remember(_river_lanes_block())\n    except Exception as e:\n        _river_remember(error=e)\n",
        "replace": "        _river_lanes_block()\n    except Exception as e:\n        pass\n",
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


class AWarmerReadsTheRiver(_Cache):

    def test_a_restarted_console_reads_its_river_without_a_shelf(self):
        before = ca._river_for_wire(NOW)
        self.assertIsNone(before["lanes"], "PREMISE: a fresh console already holds a river")
        self.assertIsNone(before["stuck"], "PREMISE: a fresh console already has a stuck reading")
        calls = []
        with mock.patch.object(ca, "_river_lanes_block", lambda: calls.append(1) or GOOD), \
                mock.patch("time.time", lambda: NOW / 1000.0):
            why = ca._river_warm_once(NOW)
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
            ca._river_warm_once(NOW)
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
        # and a failure is itself a read: no retry storm every minute
        with mock.patch.object(ca, "_river_lanes_block", lambda: self.fail("a fresh failure was retried at once")):
            ca._river_warm_once(NOW + 60 * 1000)


class TheWarmerIsWired(unittest.TestCase):

    def test_the_roster_starts_it_and_the_route_shares_its_block(self):
        import inspect
        src = inspect.getsource(ca.start_background_watchers)
        self.assertIn('("tvd-river-warm", _river_warm_loop)', src, "the warmer is not in the watcher roster")
        self.assertIn("_lane_tick('tvd-river-warm'", inspect.getsource(ca._river_warm_loop),
                      "the warmer stamps no beat, so a dead warmer is invisible")
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
