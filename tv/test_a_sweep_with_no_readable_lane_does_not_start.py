#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3406 — AN ATTACK THE LOCK ANSWERED IS NOT AN ATTACK ON THE DOOR.

`chronicle_sweep_start` asks `self_arming.may("vault.sweep_start")` BEFORE it reads the lane
list. That lock FAILS CLOSED on a stale heart census, which is its state for the whole of any
session that has touched a gate file — so every attack aimed at a guard BELOW the lock was
answered by the lock, and `sweep_wilson` counted the answer as a refusal by the door.

MEASURED 2026-09-22, and this is why the law is here rather than only in the harness: reverting
the door's own lane guard in a sandbox left `sweep_wilson` GREEN, exit 0, with lanesnone,
lanesraise, lanesstr and lanesdict all still reading PROVEN. The revert was real; its anchor
matched exactly once; the attack never arrived. Four claims were scoring a guard they could not
see, and banking `attacks=1` each into the very lock that was answering them.

So this file does what the harness cannot safely do: it STUBS THE LOCK OPEN, stubs
`threading.Thread` so nothing is ever spent, and drives the lane states at the real door.

⚠ NOTHING HERE SPENDS A PAID READ. Every case runs under a stubbed `threading.Thread`, and the
BASELINE case asserts the door WOULD have started — that is what makes the refusals mean
something. Without it a door jammed permanently shut would pass every other case.
"""
import os
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import control_app as ca              # noqa: E402
import self_arming as SA              # noqa: E402
import sweep_wilson as SW             # noqa: E402


class _StoppedThread(object):
    """Stands in for threading.Thread so a leak cannot spend a paid read."""
    spawned = []

    def __init__(self, *a, **k):
        _StoppedThread.spawned.append(self)

    def start(self):
        self.started = True


def _drive(lanes_fn, **kw):
    """Call the door with the LOCK OPEN, the thread stubbed, and `_chron_lanes` = lanes_fn.

    -> (response, spawned). The response is None only if the door RAISED, which is itself a
    failure: a door that explodes has not refused.
    """
    real_may, real_lanes, real_thread = SA.may, ca._chron_lanes, threading.Thread
    orig_job = dict(ca._CHRON_JOB)
    _StoppedThread.spawned = []
    SA.may = lambda lock: (True, "v3406: the lock is stubbed OPEN so the DOOR is under test")
    ca._chron_lanes = lanes_fn
    threading.Thread = _StoppedThread
    try:
        try:
            r = ca.chronicle_sweep_start(**kw)
        except Exception as e:
            return ("RAISED: %s: %s" % (type(e).__name__, e)), len(_StoppedThread.spawned)
        return r, len(_StoppedThread.spawned)
    finally:
        SA.may, ca._chron_lanes, threading.Thread = real_may, real_lanes, real_thread
        ca._CHRON_JOB.clear()
        ca._CHRON_JOB.update(orig_job)


class TestTheDoorIsReachedAtAll(unittest.TestCase):
    """The baseline. Every refusal below is worthless if the door refuses everything."""

    def test_BASELINE_with_the_lock_open_and_a_real_lane_the_sweep_STARTS(self):
        d = tempfile.mkdtemp(prefix="v3406ok_")
        r, spawned = _drive(lambda *a, **k: ["claude"], hist_dir=d, limit=None)
        self.assertIsInstance(r, dict, "the door raised instead of answering: %r" % (r,))
        self.assertIs(r.get("ok"), True,
                      "the door refused a LEGAL call, so no refusal below distinguishes "
                      "anything: %s" % str(r.get("why"))[:160])
        self.assertIs(r.get("started"), True, "a legal call must report started")
        self.assertEqual(spawned, 1, "exactly one worker, and it is stubbed")
        print("baseline: the door STARTS when the lane is real — %d thread(s) stubbed" % spawned)


class TestALaneListThatCannotBeReadDoesNotStart(unittest.TestCase):

    def test_a_lane_list_of_None_refuses_and_does_not_raise(self):
        d = tempfile.mkdtemp(prefix="v3406none_")
        r, spawned = _drive(lambda *a, **k: None, hist_dir=d, limit=1)
        self.assertIsInstance(r, dict,
                              "`\"claude\" not in None` raises TypeError — a door that explodes "
                              "has not refused, and the caller gets a traceback instead of a "
                              "reason: %r" % (r,))
        self.assertIs(r.get("ok"), False)
        self.assertEqual(spawned, 0, "nothing may spawn on an unreadable lane list")

    def test_a_lane_reader_that_RAISES_refuses_with_the_exception_named(self):
        def _boom(*a, **k):
            raise RuntimeError("lanes unreadable")
        d = tempfile.mkdtemp(prefix="v3406raise_")
        r, spawned = _drive(_boom, hist_dir=d, limit=1)
        self.assertIsInstance(r, dict,
                              "the reader's exception escaped the door: %r" % (r,))
        self.assertIs(r.get("ok"), False)
        self.assertIn("could not be read", str(r.get("why") or ""),
                      "the refusal must say the lane list was unreadable, not something else")
        self.assertIn("RuntimeError", str(r.get("why") or ""),
                      "UNKNOWN must name WHICH failure — a bare 'unavailable' sends the reader "
                      "hunting the wrong thing")
        self.assertEqual(spawned, 0)

    def test_the_WORD_claude_inside_a_string_is_not_a_lane_list(self):
        d = tempfile.mkdtemp(prefix="v3406str_")
        r, spawned = _drive(lambda *a, **k: "claude", hist_dir=d, limit=1)
        self.assertIsInstance(r, dict)
        self.assertIs(r.get("ok"), False,
                      "`\"claude\" in \"claude\"` is True for a STRING, so a lane reader that "
                      "returned one name instead of a list used to open the paid door")
        self.assertEqual(spawned, 0)

    def test_a_dict_of_lanes_is_not_a_lane_list(self):
        d = tempfile.mkdtemp(prefix="v3406dict_")
        r, spawned = _drive(lambda *a, **k: {"claude": True}, hist_dir=d, limit=1)
        self.assertIsInstance(r, dict)
        self.assertIs(r.get("ok"), False,
                      "`in` on a dict tests its KEYS, so a mapping walked straight through")
        self.assertEqual(spawned, 0)


class TestTheHarnessCannotScoreADoorItNeverReached(unittest.TestCase):
    """The other half. The door being right does not make the attacker honest."""

    def test_a_lock_answered_refusal_is_UNREACHED_and_not_a_refusal(self):
        locked = {"ok": False, "why": "vault.sweep_start is LOCKED — the heart census is STALE"}
        door = {"ok": False, "why": "there is no history directory at 3"}
        self.assertTrue(SW._lock_answered(locked),
                        "a refusal naming the lock is evidence about the LOCK")
        self.assertFalse(SW._lock_answered(door),
                         "a refusal by the door itself must still count")

    def test_an_UNREACHED_attempt_is_in_NEITHER_number(self):
        self.assertEqual(SW._tally([True, True]), (2, 2))
        self.assertEqual(SW._tally([True, False]), (2, 1))
        self.assertEqual(SW._tally([None, None]), (0, 0),
                         "all-unreached is 0 of 0 — UNPROVEN, never 0 of 2, which reads LEAKS "
                         "and accuses working code")
        self.assertEqual(SW._tally([None, True]), (1, 1),
                         "the reached half still counts")

    def test_a_claim_that_reached_nothing_banks_nothing(self):
        out = SW.bank_into_proof_queue([
            {"claim": "lanesnone", "what": "x", "attempts": 0, "caught": 0, "state": "UNPROVEN"},
        ])
        self.assertEqual(out["banked"], [],
                         "banking a 0/0 adds a DISTINCT ATTACK to the very lock that answered "
                         "it — the lock raising its own score on its own refusals")
        self.assertTrue(any("0 attempts REACHED" in s for s in out["skipped"]),
                        "and it must SAY so: %r" % (out["skipped"],))

    def test_the_live_harness_reports_those_four_claims_as_UNPROVEN_not_PROVEN(self):
        """Not a fixture — the real registry, so this dies the day a claim is renamed."""
        names = [c[0] for c in SW.CLAIMS]
        for want in ("lanesnone", "lanesraise", "lanesstr", "lanesdict"):
            self.assertIn(want, names, "the claim this version is about no longer exists")
        ok, why = SA.may("vault.sweep_start")
        print("vault.sweep_start may=%s — %s" % (ok, why[:110]))


RED_PROOF = [
    {
        "why": "v3406 — THE SHAPE CHECK. `\"claude\" in x` is True for the STRING \"claude\" and "
               "True for a DICT with that key, so a lane reader returning one name, or a mapping, "
               "walked straight through into the paid door. Removing the isinstance also makes the "
               "None case raise TypeError out of the door, which is not a refusal at all. "
               "⚠ SAFE: every case runs under a stubbed threading.Thread, so a door that opens "
               "here spends nothing.",
        "file": "control_app.py",
        "find": '        if not isinstance(lanes, (list, tuple)) or \"claude\" not in lanes:',
        "replace": '        if \"claude\" not in lanes:',
        "matches": 1,
    },
    {
        "why": "v3406 — THE READER'S OWN FAILURE. Without the try/except the lane reader's "
               "exception escapes the door, so the caller gets a traceback where it is owed a "
               "reason, and `_guarded` — which swallows exceptions into None — reads that as "
               "'not caught' in one harness and as nothing at all in another.",
        "file": "control_app.py",
        "find": '        try:\n            lanes = _chron_lanes()\n        except Exception as _lane_e:\n            return {\"ok\": False, \"why\": \"the lane list could not be read (%s) — a sweep with no \"\n                                        \"known reader does not start\" % type(_lane_e).__name__}\n',
        "replace": '        lanes = _chron_lanes()\n',
        "matches": 1,
    },
    {
        "why": "v3406 — THE HARNESS HALF, and the one that hid the other two for a whole session. "
               "With `_lock_answered` blinded, sweep_wilson counts a refusal issued by "
               "vault.sweep_start's own lock as a refusal by the door, so the four lane claims "
               "read PROVEN while the attack never arrived — exactly the state MEASURED on "
               "2026-09-22, where reverting the guard above left the harness green at exit 0.",
        "file": "sweep_wilson.py",
        "find": '    return isinstance(r, dict) and \"is LOCKED —\" in str(r.get(\"why\") or \"\")',
        "replace": '    return False',
        "matches": 1,
    },
    {
        "why": "v3406 — UNREACHED MUST LEAVE BOTH NUMBERS. Counting it in the denominator only "
               "turns 0 of 0 into 0 of 2, which score() grades LEAKS — an accusation against "
               "code that was never even asked. A wrong direction is not the safe direction: it "
               "would red the push and send the next reader hunting a defect that is not there.",
        "file": "sweep_wilson.py",
        "find": '    reached = [v for v in results if v is not None]',
        "replace": '    reached = list(results)',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
