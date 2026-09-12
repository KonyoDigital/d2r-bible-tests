#!/usr/bin/env python3
"""v3011 (#80) — THE OUTLET'S CORROBORATOR: his rule, re-derived from the reels' own evidence.

"make sure that stamps/verification is happening obviously before they go to tombstone and then
deleted." The route lane checks this before acting — the actor grading itself. The pair counts,
from the evidence walk alone, reels that were MEASURED worth reading and closed out unsealed.

⚠⚠ THE FIRST PREDICATE WENT RED ON HIS LIVE DATA WITHIN A MINUTE, AND THE RED WAS WRONG. `sealed
is False` alone counted 4 — all four `worthReading=False, surveyed=True, names=0`: reels judged
EMPTY OF VALUE, where nothing was ever sealed because there was nothing to seal, and routing them
is exactly right. The violation is the CONJUNCTION. These laws pin both halves so neither can be
quietly dropped. [[sabotage-is-usually-the-wrong-one]] [[unknown-stays-unknown]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import corroborate as CO  # noqa: E402
import reel_router as RR  # noqa: E402


class TheOutletPairRederivesHisRule(unittest.TestCase):

    def _left(self, routed, ev):
        real_r, real_e = RR._routed_by_a_lane, RR._evidence
        RR._routed_by_a_lane = lambda *a, **k: (routed, "")
        RR._evidence = lambda *a, **k: (ev, "")
        try:
            _key, _what, _prove, _ln, left, _rn, right, rel = \
                CO._inv_a_tombstone_is_never_ahead_of_extraction()
            return left()
        finally:
            RR._routed_by_a_lane, RR._evidence = real_r, real_e

    def test_a_worth_reading_reel_closed_out_unsealed_is_the_violation(self):
        got = self._left({"r1": {"station": "ROUTED"}},
                         {"r1": {"sealed": False, "worthReading": True, "names": 3}})
        self.assertEqual(got, 1,
                         "worth reading + unsealed + routed is exactly the tombstone-ahead-of-"
                         "extraction his rule forbids")

    def test_a_judged_empty_reel_routes_freely(self):
        """The false red the first predicate produced, pinned so it cannot return."""
        got = self._left({"r1": {"station": "ROUTED"}},
                         {"r1": {"sealed": False, "worthReading": False, "names": 0,
                                 "surveyed": True}})
        self.assertEqual(got, 0,
                         "a reel surveyed and judged empty of value satisfies the extraction "
                         "contract vacuously — counting it is the false red measured live on "
                         "4 of his 20 routed reels")

    def test_an_unmeasured_half_counts_neither_way(self):
        self.assertEqual(self._left({"r1": {}}, {"r1": {"sealed": None, "worthReading": True}}), 0)
        self.assertEqual(self._left({"r1": {}}, {"r1": {"sealed": False, "worthReading": None}}), 0)

    def test_a_sealed_reel_is_clean(self):
        self.assertEqual(self._left({"r1": {}},
                                    {"r1": {"sealed": True, "worthReading": True, "names": 9}}), 0)

    def test_a_deleted_reel_absent_from_evidence_is_the_deleters_wake(self):
        self.assertEqual(self._left({"gone": {}}, {}), 0,
                         "tombstoned reels leave the evidence walk entirely — absence there is "
                         "the deleter's documented shape, not silence")

    def test_unreadable_stores_are_unmeasured_never_zero(self):
        self.assertIsNone(self._left(None, {}),
                          "no stamp store means nothing was measured")
        real_r, real_e = RR._routed_by_a_lane, RR._evidence
        RR._routed_by_a_lane = lambda *a, **k: ({"r1": {}}, "")
        RR._evidence = lambda *a, **k: (None, "boom")
        try:
            _k, _w, _p, _l, left, _rn, _r, _rel = \
                CO._inv_a_tombstone_is_never_ahead_of_extraction()
            self.assertIsNone(left(), "no evidence walk means nothing was measured")
        finally:
            RR._routed_by_a_lane, RR._evidence = real_r, real_e

    def test_the_pair_is_registered_so_it_actually_runs(self):
        """An invariant not in BUILDERS has never run — corroborate's own v2434 scar."""
        names = [getattr(b, "__name__", "") for b in CO.BUILDERS]
        self.assertIn("_inv_a_tombstone_is_never_ahead_of_extraction", names)


RED_PROOF = [
    {
        "why": "dropping the conjunction to a constant means no violation can ever be counted — "
               "the pair reports agreement whatever the reels' evidence says",
        "file": "corroborate.py",
        "find": "            if e.get(\"sealed\") is False and e.get(\"worthReading\") is True:",
        "replace": "            if False:",
        "matches": 1,
    },
    {
        "why": "narrowing back to sealed-only restores the false red measured live on 4 of his "
               "20 routed reels — judged-empty reels counted as contract breaches",
        "file": "corroborate.py",
        "find": "and e.get(\"worthReading\") is True:",
        "replace": "and True:",
        "matches": 1,
    },
]

if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
