# -*- coding: utf-8 -*-
"""A15 clause 3 — the routes separate PER REEL, BY WHAT THE REEL HOLDS.

⚠⚠ THE QUESTION IS NOT "DO REELS DIFFER". They obviously do. It is whether the difference is EARNED
BY THE CONTENT — a shelf where every route is decided by age, or by whether the suite opens the
reel, has divergence in it and none of it is the divergence A15 asks for. Measured on his shelf the
two columns are the same 28 and the same 12: **every reel that reached the far end got there by
POLICY**, and every content-routed reel is parked under one tag at one rung.

⚠⚠ AND THAT IS NOT A DEFECT. `zero-pages` means *swept, and the sweep found nothing to read* — a
deliberate hold, because the engine reopens those when the prompt improves. A probe reporting it as
a routing failure would cry wolf on a shelf behaving exactly as designed. UNEXERCISED is a third
state, distinct from broken AND from working, and these pin that it stays distinct.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import per_reel_routes as PRR   # noqa: E402


class ARouteCountsOnlyWhenTheCONTENTEarnedIt(unittest.TestCase):

    def _r(self, reel, tag, stage):
        return {"reel": reel, "tag": tag, "stage": stage}

    def test_a_POLICY_hold_is_never_counted_as_a_content_earned_route(self):
        """⚠⚠ THE WHOLE POINT. `recent` and `test-fixture` are age and the suite — not content."""
        r = PRR.routes([self._r("reel_a", "recent", "releasable"),
                        self._r("reel_b", "test-fixture", "releasable")])
        self.assertEqual(r["byDecider"].get("content", 0), 0,
                         "a policy hold was attributed to the reel's content: %s" % r["rows"])
        self.assertEqual(
            r["state"], "POLICY_ONLY",
            "two reels took two different routes and the probe called that content-earned "
            "divergence. Neither route has anything to do with what the reel HOLDS — one is age, "
            "one is the test suite opening it. %s" % r["why"])

    def test_ONE_content_route_across_many_reels_is_UNEXERCISED_not_earned(self):
        """One route is a queue, not a divergence. 28 of his reels sit on exactly this shape."""
        rows = [self._r("reel_%d" % i, "zero-pages", "swept") for i in range(5)]
        r = PRR.routes(rows)
        self.assertEqual(r["byDecider"].get("content"), 5)
        self.assertEqual(
            r["state"], "UNEXERCISED",
            "five reels routed by their content all took the SAME route and the probe reported "
            "the clause as satisfied: %s" % r["why"])
        self.assertIn("not a defect", r["why"],
                      "the report does not say UNEXERCISED is distinct from broken, so a reader "
                      "takes it as a routing failure on a shelf behaving as designed: %s" % r["why"])

    def test_TWO_distinct_content_routes_reach_EARNED(self):
        """⚠ BASELINE: if nothing could ever reach EARNED, UNEXERCISED is not a measurement."""
        r = PRR.routes([self._r("reel_a", "zero-pages", "swept"),
                        self._r("reel_b", "vault-owes", "vault-done")])
        self.assertEqual(r["distinctContentRoutes"], 2, r["contentRoutes"])
        self.assertEqual(r["state"], "EARNED",
                         "two reels took different paths because of what they hold and the probe "
                         "would not say so: %s" % r["why"])

    def test_an_UNTAUGHT_tag_is_not_rounded_into_the_content_bucket(self):
        """⚠ It would inflate the exact count this module exists to report honestly."""
        r = PRR.routes([self._r("reel_a", "some-tag-nobody-taught", "swept")])
        self.assertEqual(r["byDecider"].get("unknown"), 1,
                         "a tag reel_story's own map has never seen was attributed anyway: %s"
                         % r["rows"])
        self.assertEqual(r["byDecider"].get("content", 0), 0)

    def test_a_GLOBAL_hold_is_identical_for_every_reel_so_it_is_not_per_reel(self):
        r = PRR.routes([self._r("reel_a", "ledger-unreadable", "triaged"),
                        self._r("reel_b", "ledger-unreadable", "triaged")])
        self.assertEqual(r["byDecider"].get("global"), 2,
                         "a hold about the WHOLE tree was read as a per-reel decision: %s" % r["rows"])
        self.assertEqual(r["state"], "POLICY_ONLY")

    def test_the_split_is_QUOTED_from_reel_story_never_restated_here(self):
        """⚠ A second copy of POLICY_HOLDS is a rename away from filing a policy hold as content.
        [[copy-drift]] §1"""
        import reel_story as RS
        real = RS.POLICY_HOLDS
        try:
            RS.POLICY_HOLDS = frozenset(("zero-pages",))     # move a tag across the line
            r = PRR.routes([self._r("reel_a", "zero-pages", "swept")])
            self.assertEqual(
                r["byDecider"].get("policy"), 1,
                "moving a tag in reel_story.POLICY_HOLDS did not move it here, so this module "
                "keeps its own copy of the split: %s" % r["rows"])
        finally:
            RS.POLICY_HOLDS = real

    def test_an_EMPTY_shelf_is_UNKNOWN_not_POLICY_ONLY(self):
        r = PRR.routes([])
        self.assertEqual(r["state"], "UNKNOWN", r["why"])
        self.assertFalse(r["ok"], "nothing to read answered ok=True: %s" % r["why"])


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
