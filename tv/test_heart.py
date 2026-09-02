#!/usr/bin/env python3
"""Guards for THE HEART. Every case defends a distinction that, if it collapsed, would let the
heart report green over something nobody is watching."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import heart as H  # noqa: E402


class _Fake(object):
    """A stand-in for lane_census, so these cases never depend on his real console."""
    def __init__(self, rows):
        self._rows = rows

    def census(self, src=None):
        return self._rows


class _Swap(unittest.TestCase):
    def use(self, rows):
        sys.modules["lane_census"] = _Fake(rows)
        self.addCleanup(sys.modules.pop, "lane_census", None)

    def states(self, rep):
        return dict((v["name"], v["state"]) for v in rep["vessels"])


class TestDarkIsNotUnknownAndNeitherIsHarmless(_Swap):
    """★ THE DISTINCTION THE WHOLE FILE EXISTS FOR. A16: the heart "can only supervise what it
    knows exists — and it does not." Measured 2026-09-02: 30 targets, 11 supervised, 8 unwatched.
    Two of those eight had a real defect the same day. If DARK and UNKNOWN collapse, or if either
    is allowed to read as fine, the heart reports green over exactly those eight."""

    def test_a_loop_nobody_watches_is_DARK(self):
        self.use([{"fn": "_rogue_loop", "kind": "LOOP", "lane": None, "supervised": False}])
        rep = H.vessels()
        self.assertEqual(self.states(rep)["_rogue_loop"], H.DARK)
        self.assertIn("NOTHING watches it", rep["vessels"][0]["why"])

    def test_an_unclassifiable_target_is_UNKNOWN_not_DARK(self):
        """Dark means measured-and-nothing-watches. Unknown means the census could not tell. The
        remedies differ, so folding them together hides one of the two."""
        self.use([{"fn": "serve_forever", "kind": "UNKNOWN", "lane": None, "supervised": False}])
        self.assertEqual(self.states(H.vessels())["serve_forever"], H.UNKNOWN)

    def test_DARK_sorts_ABOVE_everything_else(self):
        """A vessel nobody watches must not be findable only by scrolling."""
        self.use([
            {"fn": "_aaa_watched", "kind": "LOOP", "lane": "tvd-aaa", "supervised": True},
            {"fn": "_zzz_dark", "kind": "LOOP", "lane": None, "supervised": False},
        ])
        self.assertEqual(H.vessels()["vessels"][0]["name"], "_zzz_dark",
                         "the unwatched lane sorted below a watched one — the thing nobody is "
                         "looking at must be the first thing on the surface")


class TestWatchedIsWorkOwedNotAFault(_Swap):
    """[[heart-first]] §5 — UNPROVEN must not read as FAILING. A heart that turned its own newest
    vessels red would be ignored inside a week, and then the real red goes with it."""

    def test_a_watched_lane_with_no_score_is_WATCHED_not_DARK(self):
        self.use([{"fn": "_lane", "kind": "LOOP", "lane": "tvd-lane", "supervised": True}])
        rep = H.vessels()
        self.assertEqual(self.states(rep)["_lane"], H.WATCHED)
        self.assertIn("work owed, not a fault", rep["vessels"][0]["why"])

    def test_WATCHED_carries_no_score_rather_than_a_zero(self):
        """`score: None` means nobody tested it; `0.0` would mean it was tested and never refused.
        Those are opposite facts and the second is the dangerous one."""
        self.use([{"fn": "_lane", "kind": "LOOP", "lane": "tvd-lane", "supervised": True}])
        self.assertIsNone(H.vessels()["vessels"][0]["score"])


class TestFlowingHasToBeEARNED(_Swap):
    """FLOWING is the only word that claims something was proven, so it is the only one that can
    lie in the expensive direction."""

    def test_a_watcher_that_was_tested_and_NEVER_REFUSED_is_not_FLOWING(self):
        """score 0.0 is the INERT watcher — tested, and it could not say no. It must never be
        mistaken for a proven one, and `if score:` would do exactly that."""
        self.use([{"fn": "_lane", "kind": "LOOP", "lane": "tvd-lane", "supervised": True}])

        class _HE(object):
            OK = "ok"
            @staticmethod
            def report():
                return {"rows": [{"id": "tvd-lane", "state": "ok", "score": 0.0}]}
        sys.modules["health_engine"] = _HE
        self.addCleanup(sys.modules.pop, "health_engine", None)
        self.assertEqual(self.states(H.vessels())["_lane"], H.WATCHED,
                         "a watcher that was sabotaged and never refused was reported as FLOWING. "
                         "An invariant that always agrees may be perfect or inert, and this is the "
                         "inert one.")

    def test_a_real_score_DOES_make_it_flowing(self):
        """The mirror: without this the first case could pass by nothing ever being FLOWING."""
        self.use([{"fn": "_lane", "kind": "LOOP", "lane": "tvd-lane", "supervised": True}])

        class _HE(object):
            OK = "ok"
            @staticmethod
            def report():
                return {"rows": [{"id": "tvd-lane", "state": "ok", "score": 0.84}]}
        sys.modules["health_engine"] = _HE
        self.addCleanup(sys.modules.pop, "health_engine", None)
        rep = H.vessels()
        self.assertEqual(self.states(rep)["_lane"], H.FLOWING)
        self.assertEqual(rep["vessels"][0]["score"], 0.84)


class TestTasksAreNotVessels(_Swap):
    """lane_census marks them itself: "a roster entry would be a lie". They are one-shot work kicked
    off by something else and they inherit their caller's vessel. Counting them would make the
    roster claim more things run without him than actually do."""

    def test_a_TASK_is_excluded_and_COUNTED_SEPARATELY(self):
        self.use([
            {"fn": "_reap", "kind": "TASK", "lane": None, "supervised": False},
            {"fn": "_lane", "kind": "LOOP", "lane": "tvd-lane", "supervised": True},
        ])
        rep = H.vessels()
        self.assertNotIn("_reap", self.states(rep))
        self.assertEqual(rep["notVessels"], 1,
                         "tasks were dropped without being counted — silently excluding them is "
                         "indistinguishable from never having seen them")


class TestItRefusesRatherThanRemembers(_Swap):
    """A16: "The 21 / 11 that stood here was from a classifier later proven wrong; do not quote
    it." So an unavailable census must produce UNKNOWN, never a remembered number."""

    def test_no_census_figure_is_hardcoded_anywhere_in_the_module(self):
        import inspect, re
        src = inspect.getsource(H)
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        # the counts live in the docstring as EVIDENCE; they must not appear in executable code
        for n in ("30", "11", "8"):
            self.assertNotRegex(
                code, r"counts\s*\[[^\]]*\]\s*=\s*%s\b" % n,
                "a census count is written into the code. It must be ASKED every call — A16 says "
                "a hardcoded figure here was already proven wrong once")

    def test_a_census_that_cannot_be_taken_is_ok_False_with_NO_counts(self):
        class _Broken(object):
            @staticmethod
            def census(src=None):
                raise RuntimeError("boom")
        sys.modules["lane_census"] = _Broken
        self.addCleanup(sys.modules.pop, "lane_census", None)
        rep = H.vessels()
        self.assertFalse(rep["ok"])
        self.assertIsNone(rep["counts"][H.FLOWING],
                          "an unreadable census produced a NUMBER. Zero vessels and 'nobody could "
                          "look' are different facts and only one of them is safe to act on")

    def test_a_shape_change_is_UNKNOWN_not_a_reclassification(self):
        """If census() disappears, the shape changed. Guessing at a replacement name would silently
        reclassify every lane, which is worse than refusing."""
        class _NoCensus(object):
            pass
        sys.modules["lane_census"] = _NoCensus
        self.addCleanup(sys.modules.pop, "lane_census", None)
        rep = H.vessels()
        self.assertFalse(rep["ok"])
        self.assertIn("shape changed", rep["why"])


class TestItDerivesAndNeverWrites(unittest.TestCase):
    """A hand-maintained diagram is a map that drifts from the territory. This repo paid for that
    on 2026-09-02 when BLUEPRINT.md — a GENERATED artifact — went stale and a gate graded the last
    build. The heart must have no stored copy to go stale."""

    def test_the_module_writes_nothing(self):
        import ast, inspect
        tree = ast.parse(inspect.getsource(H))
        bad = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                nm = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                if nm in ("remove", "unlink", "rmtree", "replace", "mkdir", "makedirs"):
                    bad.append("%s() at line %d" % (nm, node.lineno))
                if nm == "open":
                    bad.append("open() at line %d" % node.lineno)
        self.assertEqual(bad, [],
                         "the heart writes or caches: %s. It DERIVES and REPORTS; a stored picture "
                         "is a map that drifts from the territory." % "; ".join(bad))


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
