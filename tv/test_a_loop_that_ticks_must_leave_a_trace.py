# -*- coding: utf-8 -*-
"""A LOOP THAT CLAIMS TO RUN MUST HAVE LEFT SOMETHING BEHIND — and an unreadable tick is UNKNOWN.

MEASURED 2026-09-13: ten surfaces sat at 3 of 4 organs and every one was missing the SAME organ.
A corroborator needs TWO INDEPENDENT witnesses; for a loop that is (a) its tick and (b) the trace
it leaves. Six of the eight loops leave nothing an outside reader can date, so there was nothing
to build one FROM. Two do, and this covers exactly those two.

⚠ THE SIX STAY ABSENT ON PURPOSE. Declaring a trace they do not produce is the coverage v3055
deleted — a resolver that matched on name tails and invented eight cells. An honest hole beats a
filled one. [[unknown-stays-unknown]]

⚠ AND A MISSING TICK IS NOT A DEAD LOOP. `lane_liveness._TICKS` is an in-process dict on a
`time.monotonic()` clock; a separate process sees it EMPTY. Measured: `rows()` returned 0 lanes
here while his console was healthy, and every vessel read live=UNKNOWN. Reporting that as "the
loops are dead" would be a fabricated alarm about a working machine.
[[feedback-suspect-the-instrument]]
"""
import io
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


class TestALoopThatTicksMustLeaveATrace(unittest.TestCase):

    def test_only_loops_with_a_real_trace_are_declared(self):
        import loop_corroborate as LC
        print("declared loops: %s" % sorted(LC.LOOPS))
        self.assertEqual(sorted(LC.LOOPS), sorted(LC.SURFACES),
                         "every declared surface must have a trace entry, and vice versa")
        for vessel, (lane, pattern, every) in LC.LOOPS.items():
            self.assertTrue(lane and isinstance(lane, str), "%s: no lane name" % vessel)
            self.assertNotEqual(lane, vessel,
                                "%s: the tick is stamped under a LANE name, not the vessel name — "
                                "if these ever match, re-derive it rather than assuming" % vessel)
            self.assertTrue(pattern and isinstance(pattern, str), "%s: no trace pattern" % vessel)
            self.assertTrue(isinstance(every, (int, float)) and every > 0,
                            "%s: a period is needed or 'stale' means nothing" % vessel)

    def test_a_fresh_tick_with_a_stale_trace_is_a_contradiction(self):
        """The finding this organ exists for: running, and producing nothing."""
        import loop_corroborate as LC
        real_tick, real_trace = LC._tick_age, LC._trace_age
        try:
            LC._tick_age = lambda lane: 5.0                      # ticked seconds ago
            LC._trace_age = lambda pat: (999999.0, 3)            # produced nothing for ages
            c = LC.corroborate({"x": ("lane-x", "/nope/*", 60.0)})
        finally:
            LC._tick_age, LC._trace_age = real_tick, real_trace
        print("fresh tick + ancient trace -> %s" % c["rows"][0]["verdict"])
        self.assertEqual(1, c["disagreed"], "a loop that ticks and produces nothing must refuse")
        self.assertEqual("DISAGREE", c["rows"][0]["verdict"])

    def test_a_fresh_tick_with_a_fresh_trace_agrees(self):
        """The positive half — it must not simply refuse everything."""
        import loop_corroborate as LC
        real_tick, real_trace = LC._tick_age, LC._trace_age
        try:
            LC._tick_age = lambda lane: 5.0
            LC._trace_age = lambda pat: (30.0, 3)
            c = LC.corroborate({"x": ("lane-x", "/nope/*", 60.0)})
        finally:
            LC._tick_age, LC._trace_age = real_tick, real_trace
        print("fresh tick + fresh trace -> %s" % c["rows"][0]["verdict"])
        self.assertEqual(0, c["disagreed"])
        self.assertEqual("AGREE", c["rows"][0]["verdict"])

    def test_an_unreadable_tick_is_unknown_never_a_failure(self):
        """One witness corroborates nothing, and out-of-process the tick is invisible."""
        import loop_corroborate as LC
        real_tick, real_trace = LC._tick_age, LC._trace_age
        try:
            LC._tick_age = lambda lane: None                     # the normal out-of-process case
            LC._trace_age = lambda pat: (999999.0, 3)            # even with an ancient trace
            c = LC.corroborate({"x": ("lane-x", "/nope/*", 60.0)})
        finally:
            LC._tick_age, LC._trace_age = real_tick, real_trace
        print("unreadable tick + ancient trace -> %s (disagreed=%d)"
              % (c["rows"][0]["verdict"], c["disagreed"]))
        self.assertEqual("UNKNOWN", c["rows"][0]["verdict"],
                         "a tick this process cannot see must never be read as a dead loop")
        self.assertEqual(0, c["disagreed"], "and it must not be counted as a contradiction")
        self.assertIn("UNMEASURED", c["say"].upper())

    def test_a_missing_trace_is_unknown_not_agreement(self):
        import loop_corroborate as LC
        real_tick, real_trace = LC._tick_age, LC._trace_age
        try:
            LC._tick_age = lambda lane: 5.0
            LC._trace_age = lambda pat: (None, 0)
            c = LC.corroborate({"x": ("lane-x", "/nope/*", 60.0)})
        finally:
            LC._tick_age, LC._trace_age = real_tick, real_trace
        print("no trace at all -> %s" % c["rows"][0]["verdict"])
        self.assertEqual("UNKNOWN", c["rows"][0]["verdict"],
                         "nothing to corroborate against is unmeasured, never a clean bill")

    def test_the_six_traceless_loops_are_not_declared(self):
        """The honest hole. If one of these ever gains a trace, ADD it — do not invent one."""
        import loop_corroborate as LC
        for absent in ("_drift_loop", "_orphan_watch", "_orphan_exit_loop",
                       "_shadow_watch_loop", "_prune_loop", "_retention_loop"):
            self.assertNotIn(absent, LC.LOOPS,
                             "%s leaves nothing datable; declaring it would manufacture the "
                             "coverage v3055 deleted" % absent)
        print("trace-less loops correctly left ABSENT: 6")


RED_PROOF = [
    {
        "why": "a fresh tick with an ancient trace stops being a contradiction, so a loop that "
               "runs and produces nothing reads exactly like a healthy one",
        "file": "loop_corroborate.py",
        "find": "        elif t_age > every * STALE_PERIODS:",
        "replace": "        elif False:",
        "matches": 1,
    },
    {
        "why": "an unreadable tick stops being UNKNOWN, so a process that simply cannot see "
               "_TICKS starts reporting his healthy loops as broken",
        "file": "loop_corroborate.py",
        "find": "        elif k_age is None:",
        "replace": "        elif False:",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
