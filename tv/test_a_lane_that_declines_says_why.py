#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2806 — THREE KNOWABLE FACTS WERE REPORTED AS ONE UNKNOWN.

Measured on his console 2026-09-08. Of the eight DARK supervisors, three reported
`live: UNKNOWN, tickAgeS: None` — which reads as *"nobody can tell whether this is alive"*:

    _mini_watchdog      UNKNOWN   None
    _orphan_exit_loop   UNKNOWN   None
    _orphan_watch       UNKNOWN   None

Every one of those reasons was knowable, and they are three DIFFERENT facts:

| lane | why it does not stamp |
|---|---|
| `_mini_watchdog` | EPISODIC — spawned per MINI session with `(token, ends_ts)`; it lives only as long as that session, and none had run since boot |
| `_orphan_watch` | ANOTHER PROCESS — started inside the board window, so its stamps go to that process's store and can never reach this reader |
| `_orphan_exit_loop` | DECLINES BY DESIGN — `if not ppid: return` before its first tick, because a console nobody claimed must never self-exit, and his primary console never has a TV_PARENT_PID |

★ AND THE COST IS NOT ONLY A VAGUE REPORT. Collapsed into UNKNOWN they send a reader hunting a
fault that is not there — and they HIDE the one case that is a fault. A scratch console started
*with* `TV_PARENT_PID` that still declines at that return is a genuine defect, and it currently
renders identically to the healthy primary-console case. An unknown that swallows a known reason
costs exactly what a zero with no denominator costs. [[unknown-stays-unknown]]

This is the same split v2610 made one level up, where DARK stopped meaning both "nothing watches
this worker" and "nothing watches the watchman" — because those need different answers.

⚠ THE PERIODS WERE DELIBERATELY NOT FORCED. Three lanes read UNTIMED (`_bridge_prober`,
`_engine_driver`, `_kai_closer_loop`) because their sleeps are computed or branch several ways —
`_engine_driver` has four. lane_liveness's own docstring names that case and calls UNTIMED "a third
answer and not a soft version of either other one". Declaring a period they do not have would have
manufactured false LATEs, which is the mirror of the defect this file exists to prevent.
"""
import os
import ast
import io
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import lane_liveness as LL  # noqa: E402

APP = os.path.join(HERE, "control_app.py")


class TestALaneThatDeclinesSaysWhy(unittest.TestCase):

    def setUp(self):
        LL.forget_all_for_tests()

    def tearDown(self):
        LL.forget_all_for_tests()

    def test_dormant_is_its_own_state_not_a_flavour_of_unknown(self):
        LL.dormant("sleeper", "no MINI session has run since boot")
        rows = {r["lane"]: r for r in LL.report()["rows"]}
        self.assertIn("sleeper", rows,
                      "a declared-dormant lane produced NO ROW — the declaration would be "
                      "recorded and no reader could ever see it")
        self.assertEqual(rows["sleeper"]["state"], LL.DORMANT)
        self.assertNotEqual(LL.DORMANT, LL.UNKNOWN,
                            "DORMANT and UNKNOWN are the same string — the split is cosmetic")
        self.assertIn("no MINI session", rows["sleeper"]["why"],
                      "the row does not carry the reason it was given")

    def test_a_dormancy_without_a_reason_is_refused(self):
        """A reason-less dormancy IS an unknown, and must not be dressed in a calmer word."""
        for bad in ("", "   ", None):
            with self.assertRaises(ValueError):
                LL.dormant("x", bad)

    def test_a_lane_that_ticks_is_never_reported_dormant(self):
        """Declaring dormancy must not outrank evidence: a lane that stamps is alive, whatever
        anyone declared about it earlier."""
        LL.dormant("waker", "not started yet")
        LL.tick("waker", 5.0)
        rows = {r["lane"]: r for r in LL.report()["rows"]}
        self.assertEqual(rows["waker"]["state"], LL.FLOWING,
                         "a lane that has stamped a tick was still reported DORMANT — a "
                         "declaration outranking a measurement is exactly backwards")

    def test_waking_clears_it(self):
        LL.dormant("w", "episodic")
        LL.waking("w")
        self.assertNotIn("w", {r["lane"] for r in LL.report()["rows"]})

    def test_unknown_still_exists_for_the_genuinely_unexplained(self):
        """The floor must survive. If everything absent became DORMANT, the honest 'nobody
        looked' answer would be gone and this whole split would be a downgrade."""
        LL.tick("other", 1.0)
        LL._TICKS["never"] = {"ticks": 0, "everyS": None, "last": None}
        rows = {r["lane"]: r for r in LL.report()["rows"]}
        self.assertEqual(rows["never"]["state"], LL.UNKNOWN)
        self.assertIn("Nobody looked", rows["never"]["why"])

    def test_the_three_known_lanes_declare_their_reason_in_the_console(self):
        """PARSED, not grepped: the declarations must be real calls, and each must carry a
        non-empty reason string."""
        with io.open(APP, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        declared = {}
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
               and n.func.id == "_lane_dormant" and n.args:
                a0 = n.args[0]
                if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                    why = ""
                    if len(n.args) > 1:
                        w = n.args[1]
                        if isinstance(w, ast.Constant):
                            why = str(w.value)
                        elif isinstance(w, ast.JoinedStr) or isinstance(w, ast.BinOp):
                            why = "<computed>"
                    declared[a0.value] = why
        for lane in ("_mini_watchdog", "_orphan_watch", "_orphan_exit_loop"):
            self.assertIn(lane, declared,
                          "%s does not declare why it is not stamping, so it still reports as "
                          "UNKNOWN and is indistinguishable from a supervisor that died" % lane)
            self.assertTrue(str(declared[lane]).strip(),
                            "%s declares dormancy with an empty reason" % lane)
        print("\n   lanes declaring a reason: %s" % sorted(declared))


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
# Dropping one declaration returns that lane to the undifferentiated UNKNOWN it came from — which
# is the whole defect, and the reason a decline that IS a fault would be invisible again.
RED_PROOF = [{
    "why": "a lane with no declared reason falls back to UNKNOWN, indistinguishable from a dead one",
    "file": "control_app.py",
    "find": "    _lane_dormant('_orphan_watch',",
    "replace": "    _lane_dormant('_orphan_watch_RENAMED',",
    "matches": 1,
}]


if __name__ == "__main__":
    unittest.main(verbosity=2)
