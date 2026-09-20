# -*- coding: utf-8 -*-
"""v3404c — THE DOCTOR MUST SAY HOW LONG EACH CHECK TOOK.

RESUME_HERE named the unfinished thread: `cd.run(include_slow=False)` > 8 min on an idle
machine, while the same 93 checks timed standalone summed to ~24s. The decomposition is
wrong somewhere, and without a duration ON THE ROW the next hang cannot name which check
sat — so the 1500s bound takes the blame, exactly as the heart row predicted for the
syntax gate.

This does not claim to have found the 8 minutes. It pins that `run()` persists `ms` so
the next measurement is a row, not a session note. None is not-asked; 0 is asked and
instant. Collapsing those is the defect. [[heart-first]] [[unknown-stays-unknown]]

Does not hit his live console: tick_caches is replaced, CHECKS is a stub.
"""
from __future__ import annotations

import contextlib
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import console_doctor as cd  # noqa: E402


@contextlib.contextmanager
def _quiet_tick():
    """Production tick_caches POSTs /api/board_ownership into HIS window. Not here."""
    yield


class TestTheDoctorTimesEachCheck(unittest.TestCase):

    def setUp(self):
        self._checks = cd.CHECKS[:]
        self._tick = cd.tick_caches
        cd.tick_caches = _quiet_tick

    def tearDown(self):
        cd.CHECKS[:] = self._checks
        cd.tick_caches = self._tick

    def test_an_executed_check_carries_ms(self):
        def slow():
            time.sleep(0.05)
            return cd.OK, "deliberate"
        cd.CHECKS[:] = [("timed check", slow)]
        rows = cd.run(include_slow=False)
        hit = [r for r in rows if r.get("check") == "timed check"]
        self.assertEqual(len(hit), 1, "the stubbed check disappeared from run()")
        self.assertIn("ms", hit[0], "an executed check dropped the ms key")
        ms = hit[0]["ms"]
        self.assertIsNotNone(ms, "an executed check carried no ms — the next hang cannot name it")
        self.assertGreaterEqual(ms, 40, "ms=%r did not cover a 50ms sleep" % ms)
        self.assertLess(ms, 5000, "ms=%r looks like a hang, not a 50ms sleep" % ms)

    def test_a_skipped_periodic_check_is_None_not_zero(self):
        def never():
            return cd.OK, "should not run"
        cd.CHECKS[:] = [("periodic stub", never)]
        periodic = getattr(cd, "PERIODIC", ())
        # PERIODIC is a tuple of names; temporarily include our stub.
        orig = cd.PERIODIC
        try:
            cd.PERIODIC = ("periodic stub",)
            rows = cd.run(include_slow=False, include_periodic=False)
        finally:
            cd.PERIODIC = orig
        hit = [r for r in rows if r.get("check") == "periodic stub"]
        self.assertEqual(len(hit), 1, "a skipped PERIODIC check vanished instead of emitting UNMEASURED")
        self.assertTrue(hit[0].get("notAsked"))
        self.assertIn("ms", hit[0],
                      "a skipped PERIODIC check dropped the ms key; absence and None then read "
                      "the same, which is how a sabotage that deletes the stamp stays green")
        self.assertIsNone(hit[0]["ms"],
                          "not-asked collapsed to %r; 0 would read as instant" % (hit[0]["ms"],))


RED_PROOF = [
    {
        "why": "dropping ms from the executed append leaves the next hang unnamed, which is "
               "how the 1500s bound took the blame",
        "file": "console_doctor.py",
        "find": '                         "ms": _ms})',
        "replace": "})",
        "matches": 1,
    },
    {
        "why": "a skipped PERIODIC check carrying ms=0 would read as asked-and-instant",
        "file": "console_doctor.py",
        "find": '                             "ms": None})',
        "replace": "})",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
