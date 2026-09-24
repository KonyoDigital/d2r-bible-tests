# -*- coding: utf-8 -*-
"""#237 — A SLOW CENSUS IS STILL REMEMBERED.

MEASURED 2026-09-24, inside a push at load ~7: /api/heart took 48.3 s. The memo was stamped with the
moment the derivation STARTED and aged against a 45 s TTL from there, so it was born expired — the
panel's own fetch one click later walked the source again, and the render gate refused the heart
panel ("could not be ACTIVATED after 12.1s"). The next target read the same route in 0.0 s.

  · DRIVEN: heart_state() serves a memo whose reading began 60 s ago but LANDED 10 s ago, and never
    touches the census (a stub `heart` module records every call).
  · DRIVEN: the age it reports is still the age of the READING (60 s), not of the landing.
  · DRIVEN: _heart_memo_store stamps `done` from the clock at store time, not from `started`.
  · PREMISE: a memo that landed longer ago than the TTL IS derived again, so the first case can fail.
RED_PROOF below.
"""
import os
import sys
import time
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as C  # noqa: E402

_SENTINEL = {"ok": True, "counts": {"FLOWING": 7}, "vessels": ["v"], "locks": [], "ageMs": 0}


class ASlowCensusIsStillRemembered(unittest.TestCase):

    def setUp(self):
        self._memo = dict(C._HEART_MEMO)
        self._heart = sys.modules.get("heart")
        self.census_calls = []
        fake = types.ModuleType("heart")

        def _vessels():
            self.census_calls.append(1)
            raise RuntimeError("stub census: the test must not reach the walk")
        fake.vessels = _vessels
        sys.modules["heart"] = fake

    def tearDown(self):
        C._HEART_MEMO.clear()
        C._HEART_MEMO.update(self._memo)
        if self._heart is None:
            sys.modules.pop("heart", None)
        else:
            sys.modules["heart"] = self._heart

    def _seed(self, began_ago, landed_ago):
        now = time.time()
        C._HEART_MEMO.update({"t": now - began_ago, "done": now - landed_ago, "v": dict(_SENTINEL)})

    def test_a_census_that_took_longer_than_the_ttl_is_served_from_the_memo(self):
        self._seed(began_ago=60.0, landed_ago=10.0)      # a 50 s census, landed 10 s ago
        out = C.heart_state()
        self.assertEqual(self.census_calls, [], "a census slower than its TTL was walked again on the next open")
        self.assertEqual(out.get("counts"), _SENTINEL["counts"])

    def test_the_age_shown_is_the_age_of_the_reading(self):
        self._seed(began_ago=60.0, landed_ago=10.0)
        out = C.heart_state()
        self.assertGreaterEqual(out.get("ageMs"), 59000, "the shown age dropped the time the reading took: %r" % out.get("ageMs"))

    def test_premise_a_memo_that_landed_past_the_ttl_is_derived_again(self):
        self._seed(began_ago=C._HEART_TTL + 60.0, landed_ago=C._HEART_TTL + 5.0)
        out = C.heart_state()
        self.assertEqual(self.census_calls, [1], "premise: an expired memo must reach the census")
        self.assertIs(out.get("ok"), False)

    def test_force_skips_even_a_fresh_memo(self):
        self._seed(began_ago=1.0, landed_ago=1.0)
        C.heart_state(force=True)
        self.assertEqual(self.census_calls, [1])


class TheStoreStampsTheLanding(unittest.TestCase):

    def setUp(self):
        self._memo = dict(C._HEART_MEMO)

    def tearDown(self):
        C._HEART_MEMO.clear()
        C._HEART_MEMO.update(self._memo)

    def test_done_is_the_clock_at_store_time_not_the_start(self):
        started = time.time() - 50.0
        C._heart_memo_store(started, dict(_SENTINEL))
        self.assertEqual(C._HEART_MEMO["t"], started)
        self.assertGreater(C._HEART_MEMO["done"], started + 49.0, "the landing was stamped with the start again")
        self.assertIsNotNone(C._heart_memo_hit(time.time()), "a 50 s census was stored already expired")

    def test_heart_state_stores_through_the_helper(self):
        # compiler-level, not text: the derivation's one store goes through the two-clock helper
        self.assertIn("_heart_memo_store", C.heart_state.__code__.co_names)
        self.assertIn("_heart_memo_hit", C.heart_state.__code__.co_names)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#237 - the reuse window counts from the START of the census again: a 48 s census is born expired and every open re-walks the source",
        "file": "control_app.py",
        "find": "    if (now - (_HEART_MEMO.get(\"done\") or _HEART_MEMO[\"t\"])) >= _HEART_TTL:\n",
        "replace": "    if (now - _HEART_MEMO[\"t\"]) >= _HEART_TTL:\n",
        "matches": 1,
    },
    {
        "why": "#237 - the store stamps the landing with the start time again",
        "file": "control_app.py",
        "find": "    _HEART_MEMO[\"done\"] = _t.time()\n",
        "replace": "    _HEART_MEMO[\"done\"] = started\n",
        "matches": 1,
    },
    {
        "why": "#237 - the shown age is the age of the landing, hiding the 48 s the reading took",
        "file": "control_app.py",
        "find": "    out[\"ageMs\"] = int((now - _HEART_MEMO[\"t\"]) * 1000)\n    return out\n",
        "replace": "    out[\"ageMs\"] = int((now - _HEART_MEMO[\"done\"]) * 1000)\n    return out\n",
        "matches": 1,
    },
]
