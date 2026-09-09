#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""♥🔒 A SURFACE MAY NOT ARM ITSELF WHILE ITS INSTRUMENTS ARE BLIND.

Konyo, 2026-09-09: *"the lock and everything still derives from the heart and visually seen"*.
MEASURED when he asked: `self_arming.py` and `hover_wilson.py` held ZERO references to heart2. The
Wilson lock and the heart were two systems that never spoke, so a surface could reach its bar and
ARM ITSELF while the gates that would catch its failure were dark — the lock proving the surface
works, with nothing left able to prove the PROOF works.

A Wilson score says "this refused every attack we made". It cannot say "and we would have noticed
if it had not". That second question is the heart's, and it belongs in the same precondition chain
as the upstream check `may()` already runs: proving a surface in isolation proves nothing about what
feeds it, and an instrument that cannot go red is exactly that kind of missing prerequisite.
[[the-unjoined-end]] [[join-gate-heart]]

MEASURED after the join, on the real lock:
    1 BLIND instrument   -> may(printer.stream) False
    unreadable census    -> False   ("UNKNOWN fails CLOSED")
    absent census        -> False
    restored             -> True    (so it is a gate, not furniture)
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: E402  — this file prints ♥ 🔒 ⚠ ★
console_safe.enable()

import self_arming as SA  # noqa: E402
import heart2 as H  # noqa: E402

STATE = os.path.join(H.HERE, ".heart2.json")


class _Census(object):
    """Swap the heart's census for the duration of one law, and always put it back."""

    def __init__(self, payload):
        self.payload = payload
        self.bak = None

    def __enter__(self):
        if os.path.exists(STATE):
            self.bak = STATE + ".lawtest"
            shutil.copy(STATE, self.bak)
        if self.payload is None:
            if os.path.exists(STATE):
                os.unlink(STATE)
        else:
            io.open(STATE, "w", encoding="utf-8").write(self.payload)
        return self

    def __exit__(self, *a):
        if self.bak and os.path.exists(self.bak):
            shutil.move(self.bak, STATE)
        elif os.path.exists(STATE) and not self.bak:
            os.unlink(STATE)
        return False


def _real_census():
    return io.open(STATE, encoding="utf-8").read() if os.path.exists(STATE) else None


RED_PROOF = [
    {
        "why": "un-asking the heart returns the lock to what it was — a surface that can arm itself "
               "while the gates that would catch its failure are blind",
        "file": "self_arming.py",
        "find": "    _hok, _hwhy = _heart_says_watched()\n    if not _hok:\n        return False, _hwhy",
        "replace": "    _hok, _hwhy = _heart_says_watched()",
        "matches": 1,
    },
    {
        "why": "letting a BLIND instrument pass is the defect itself: the lock arming on a Wilson "
               "score while nothing can prove the proof still works",
        "file": "self_arming.py",
        "find": "    if _blind:",
        "replace": "    if False and _blind:",
        "matches": 1,
    },
]


class TheLockDerivesFromTheHeart(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_a_BLIND_instrument_closes_the_lock(self):
        """★★ The whole join. A dark gate is a missing prerequisite, not a detail."""
        real = _real_census()
        if real is None:
            self.skipTest("no census on this machine — UNMEASURED, not a failure")
        st = json.loads(real)
        st["blind"] = ["test_an_instrument_that_cannot_go_red"]
        with _Census(json.dumps(st)):
            ok, why = SA.may("printer.stream")
        self.assertFalse(ok, "a lock armed itself while an instrument was BLIND — the Wilson score "
                             "proved the surface and nothing was left to prove the proof")
        self.assertIn("BLIND", why)

    def test_an_UNREADABLE_census_fails_CLOSED(self):
        """★★ Matching _rows(): UNKNOWN never arms anything."""
        if _real_census() is None:
            self.skipTest("no census on this machine")
        with _Census("{ this is not json"):
            ok, why = SA.may("printer.stream")
        self.assertFalse(ok, "an unreadable heart census permitted a lock to act")
        self.assertIn("CLOSED", why)

    def test_an_ABSENT_census_fails_CLOSED(self):
        """★ Never run here is not the same as nothing wrong here."""
        if _real_census() is None:
            self.skipTest("no census on this machine")
        with _Census(None):
            ok, why = SA.may("printer.stream")
        self.assertFalse(ok, "a missing heart census permitted a lock to act")
        self.assertIn("CLOSED", why)

    def test_it_is_a_GATE_not_furniture(self):
        """★★ A check that can only say no would be switched off within a week.
        With the real census — 0 blind today — at least one declared lock must still be able to
        act, or this law has proved nothing except that it can refuse. [[feedback-blind-fixture-green-gate]]"""
        if _real_census() is None:
            self.skipTest("no census on this machine")
        opened = [k for k in list(SA.LOCKS) + list(SA.ROUTES) if SA.may(k)[0]]
        self.assertTrue(
            opened,
            "with a healthy heart NOT ONE surface may act. Either every lock is genuinely shut, or "
            "this join refuses unconditionally — and a gate that can only say no is furniture.")

    def test_the_heart_check_runs_BEFORE_the_score(self):
        """★ Order matters: a blind instrument must be reported as the reason, not a Wilson number."""
        real = _real_census()
        if real is None:
            self.skipTest("no census on this machine")
        st = json.loads(real)
        st["blind"] = ["test_dark"]
        with _Census(json.dumps(st)):
            _, why = SA.may("vault.apply")          # a lock that is ALSO blocked upstream
        self.assertIn("BLIND", why,
                      "a blind heart was masked by another refusal — he would read the downstream "
                      "reason and never learn the instruments were dark: %r" % why)


if __name__ == "__main__":
    unittest.main(verbosity=2)
