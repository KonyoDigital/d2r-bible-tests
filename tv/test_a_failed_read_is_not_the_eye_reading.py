# -*- coding: utf-8 -*-
"""REG-1935 - A READ THAT FAILED IS NOT THE EYE READING.

GrokBot (#230 tick 375): Dean's fleet row said "the reader . reading now" on the same row as "Claude signed
out" - and Dean has no Grok. Measured off the live /api/fleet the same morning (GET only): Dean's beacon
carries readers.claude off/needsLogin and grok off, while its eye is the one the wire derives from
_eyes_pulse().liveTs - the newest journal row in lane "deep", ANY deep row. A signed-out reader journals a
readFailed row for every attempt, so every failure refreshed liveTs and the wire said live. The engines
panel's "Live Eye . reading" reads the same number.

The law: liveTs counts only reads that did not fail, by the readers lamp's own rule (readFailed, or a read
that came back empty); a failure newer than a good read leaves the good read's time; nothing but failures
is 0, and the wire then says not live; the verify and kai lanes are untouched.
Fixtures only: the journal rows are handed in, the cache is cleared and restored.
"""
import os
import sys
import time
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as CA  # noqa: E402

_MISSING = object()


def _pulse(rows):
    saved = CA.__dict__.get("_EYES_CACHE", _MISSING)
    CA.__dict__.pop("_EYES_CACHE", None)
    try:
        with mock.patch.object(CA, "_kai_journal_rows", return_value=(rows, None)):
            return CA._eyes_pulse()
    finally:
        CA.__dict__.pop("_EYES_CACHE", None)
        if saved is not _MISSING:
            CA._EYES_CACHE = saved


def _deep(ts, **k):
    return dict({"lane": "deep", "ts": ts, "completedTs": ts}, **k)


class AFailedReadIsNotTheEyeReading(unittest.TestCase):

    def test_a_good_read_is_the_eye(self):
        self.assertEqual(_pulse([_deep(1000)])["liveTs"], 1000, "the baseline good read was not counted")

    def test_a_failed_read_is_not(self):
        self.assertEqual(_pulse([_deep(2000, readFailed=True, readErr="signed out")])["liveTs"], 0,
                         "a signed-out reader's failed attempt counted as the eye reading (REG-1935)")

    def test_an_empty_read_is_not(self):
        self.assertEqual(_pulse([_deep(2000, mode="empty")])["liveTs"], 0)

    def test_a_newer_failure_keeps_the_good_reads_time(self):
        out = _pulse([_deep(1000), _deep(5000, readFailed=True)])
        self.assertEqual(out["liveTs"], 1000, "a failure after a good read moved the eye's last read to it")

    def test_the_other_lanes_are_untouched(self):
        out = _pulse([{"lane": "verify", "ts": 3000, "readFailed": True}, {"lane": "kai", "ts": 4000}])
        self.assertEqual((out["verifyTs"], out["kaiTs"]), (3000, 4000))

    def test_the_wire_says_not_live_over_only_failures(self):
        now = int(time.time() * 1000)
        pulse = _pulse([_deep(now - 1000, readFailed=True)])
        with mock.patch.object(CA, "_eyes_pulse", lambda: pulse), \
             mock.patch.object(CA, "_second_eye_lane_state", lambda: {"state": "absent", "provider": "grok"}):
            eye = CA._eye_for_wire()
        self.assertIsNotNone(eye)
        self.assertIs(eye["live"], False, "the fleet wire said 'reading now' over nothing but failed reads: %s" % eye)


RED_PROOF = [
    {
        "why": "REG-1935 - the pulse counts failed reads again: a signed-out PC's card says 'reading now'",
        "file": "tv/control_app.py",
        "find": "                if r.get(\"readFailed\") or r.get(\"mode\") == \"empty\":\n                    continue\n"
                "                out[\"liveTs\"]",
        "replace": "                if False:\n                    continue\n                out[\"liveTs\"]",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
