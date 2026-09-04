# -*- coding: utf-8 -*-
"""A5 — the surface was known at capture, computed on every read, and never once written down.

His words: *"the fact was in hand at intake, discarded, and the re-derivation needs footage that no
longer exists."*

⚠⚠ `_sighting_loc` (v2353) ALREADY ANSWERS THE QUESTION AND NOTHING KEPT THE ANSWER. It asks the
reel timeline where the cursor was when a name was read, and the report renders it — recomputed
from scratch on every read, from footage that is mostly gone.

MEASURED on the live store before building anything:

    evidence rows                     14,034
    rows carrying a persisted `loc`         0
    distinct reels named                  39
    reels still on disk                    3   —  92% GONE
    rows whose frame could be re-read   3,446   —  only 25%

Computed, rendered, and thrown away. [[the-unjoined-end]]

⚠ THIS CANNOT RECOVER THE PAST and must not pretend to. A row whose reel is gone stays without a
loc for ever — that is the 75%. It stops future loss only.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import control_app as CA   # noqa: E402


class TheAnswerIsKeptWhileTheReelIsStillHere(unittest.TestCase):

    def _run(self, merged, resolver):
        real = CA._sighting_loc
        try:
            CA._sighting_loc = resolver
            return CA._stamp_sighting_locs(merged)
        finally:
            CA._sighting_loc = real

    def test_a_known_surface_is_written_onto_the_sighting(self):
        merged = {"uniques": {"X": [{"reel": "r1", "frame": "f_1.jpg"}]}}
        n = self._run(merged, lambda sg, _s=None: "stash")
        self.assertEqual(n, 1, "nothing was stamped even though the surface was answerable")
        self.assertEqual(
            merged["uniques"]["X"][0].get("loc"), "stash",
            "the surface was computed and not written down — which is the whole defect: it is "
            "re-derived on every read from footage that is 92% gone")

    def test_an_UNKNOWN_surface_is_never_stamped(self):
        """⚠ A stored 'unknown' is indistinguishable from a stored FACT once the reel is pruned.

        `_sighting_loc` returns None for "not established" — no segments for that reel, or an
        unparseable frame name. Writing that down would end exactly the confusion this task
        exists to end.
        """
        merged = {"uniques": {"X": [{"reel": "gone", "frame": "f_1.jpg"}]}}
        n = self._run(merged, lambda sg, _s=None: None)
        self.assertEqual(n, 0)
        self.assertNotIn(
            "loc", merged["uniques"]["X"][0],
            "a sighting whose surface could NOT be established was stamped anyway: %r"
            % (merged["uniques"]["X"][0],))

    def test_an_existing_loc_is_never_overwritten(self):
        """The earlier answer was taken closer to the capture, when more footage existed."""
        merged = {"uniques": {"X": [{"reel": "r1", "frame": "f_1.jpg", "loc": "personal"}]}}
        n = self._run(merged, lambda sg, _s=None: "stash")
        self.assertEqual(n, 0)
        self.assertEqual(merged["uniques"]["X"][0]["loc"], "personal",
                         "a stored surface was overwritten by a later, weaker re-derivation")

    def test_a_resolver_that_raises_does_not_lose_the_sweep(self):
        """⚠ This runs INSIDE the evidence merge. An exception here must not cost the sweep —
        control_app's own history has a case where an AttributeError inside a job literal
        discarded uniques, sets, held and evidence together, on the run that found the row
        worth five."""
        merged = {"uniques": {"X": [{"reel": "r1", "frame": "f_1.jpg"}]}}
        def boom(sg, _s=None):
            raise RuntimeError("the timeline blew up")
        n = self._run(merged, boom)
        self.assertEqual(n, 0)
        self.assertEqual(merged["uniques"]["X"], [{"reel": "r1", "frame": "f_1.jpg"}],
                         "the sighting was damaged by a resolver failure")

    def test_ONE_bad_sighting_does_not_skip_every_sighting_after_it(self):
        """⚠ THE OUTER `except` ALREADY SAVES THE SWEEP — this is what the INNER one is for.

        Removing the per-sighting handler left the previous test GREEN, because the outer handler
        catches the raise and the sweep survives either way. What changes is REACH: with only the
        outer handler the first bad sighting ABORTS THE WHOLE LOOP, so every stampable sighting
        after it silently keeps nothing. One unparseable frame name would cost the surface of
        every name behind it in the same sweep.
        """
        merged = {"uniques": {"X": [
            {"reel": "bad", "frame": "f_1.jpg"},
            {"reel": "good", "frame": "f_2.jpg"},
        ]}}

        def one_bad(sg, _s=None):
            if sg["reel"] == "bad":
                raise RuntimeError("unparseable frame name")
            return "stash"

        n = self._run(merged, one_bad)
        self.assertEqual(
            merged["uniques"]["X"][1].get("loc"), "stash",
            "a sighting AFTER a failing one kept no surface — one bad frame name costs the "
            "provenance of every name behind it in the sweep")
        self.assertEqual(n, 1)
        self.assertNotIn("loc", merged["uniques"]["X"][0])

    def test_a_malformed_store_does_not_raise(self):
        for junk in (None, {}, {"uniques": None}, {"uniques": {"X": None}},
                     {"uniques": {"X": ["not-a-dict"]}}):
            self.assertEqual(self._run(junk, lambda sg, _s=None: "stash"), 0,
                             "a malformed evidence store %r was not survived" % (junk,))

    def test_the_merge_actually_calls_it(self):
        """⚠ COMPUTED AND NOT CALLED IS THE DEFECT THIS FIXES — it must not be reintroduced one
        level up. The stamp is worthless if the merge does not run it."""
        import inspect
        src = inspect.getsource(CA._chron_evidence_merge)
        self.assertIn(
            "_stamp_sighting_locs(", src,
            "the evidence merge does not call the stamper, so the surface is computed for the "
            "report and still never written down")
        self.assertLess(
            src.index("_stamp_sighting_locs("), src.index("_chron_evidence_save("),
            "the stamp runs AFTER the save, so what gets persisted is the unstamped view")


class TheWalkReachesEverySightingHoweverItNESTS(unittest.TestCase):
    """⚠⚠ REG-574 — 3,689 SIGHTINGS WERE NEVER WALKED, AND NOTHING SAID SO.

    `_stamp_sighting_locs` walked `lane -> name -> [sightings]`, and any value that was not a list
    hit a bare `continue`. Measured on his real `chron_evidence.json`: `notFoundSeen` nests THREE
    deep — `notFoundSeen -> "sets"/"uniques" -> name -> [sightings]` — so **3,689 sightings, every
    one carrying both `reel` and `frame`, were structurally unreachable**. Reach measured 10,809
    before and 13,790 after.

    ⚠ AND THE HEADLINE NUMBER IS NOT A WIN, WHICH IS WHY IT IS WRITTEN DOWN HERE. On his store the
    widened walk derives **zero** new locs, because 92% of the reels are pruned and a loc needs the
    reel's segments (see this module's header). The fix changes what is REACHABLE, not what is
    recovered — it stops future loss on the deep lanes exactly as the shallow ones already had.
    Claiming 2,981 rows "gained" a loc would have been a number measuring my own reach.
    [[plumbing-with-no-tap]] [[unknown-stays-unknown]]

    These tests stub `_sighting_loc`, because the WALK is what changed; loc-derivation did not.
    """

    def _run(self, merged):
        import control_app as C
        real = C._sighting_loc
        C._sighting_loc = lambda sg, _segments=None: "stash" if sg.get("frame") else None
        try:
            return C._stamp_sighting_locs(merged)
        finally:
            C._sighting_loc = real

    def test_a_sighting_nested_three_deep_is_reached(self):
        m = {"notFoundSeen": {"sets": {"Tal Rasha's Guardianship":
                                       [{"reel": "r1", "frame": "f_1.jpg", "lane": "claude"}]}}}
        n = self._run(m)
        self.assertEqual(n, 1, "the three-deep sighting was not reached at all — this is the "
                               "shape 3,689 of his rows are in")
        self.assertEqual(m["notFoundSeen"]["sets"]["Tal Rasha's Guardianship"][0].get("loc"),
                         "stash", "reached but not stamped")

    def test_a_VERDICT_record_at_the_same_depth_is_NOT_stamped(self):
        """⚠ BASELINE — `contestedResolved` nests identically and its leaves are resolutions, not
        sightings. Stamping one would invent a provenance nobody observed. Excluded BY SHAPE (the
        leaf is a dict, not a list), so a renamed or newly-added lane cannot slip past."""
        m = {"contestedResolved": {"uniques": {"Atma's Wail":
                                               {"foundMs": 1, "notFoundMs": 2, "verdict": "found"}}}}
        n = self._run(m)
        self.assertEqual(n, 0, "a verdict record was stamped with a location it never carried")
        self.assertNotIn("loc", m["contestedResolved"]["uniques"]["Atma's Wail"])

    def test_the_ordinary_two_deep_shape_still_works(self):
        """⚠ BASELINE — or the widening could pass by having broken the path that already worked."""
        m = {"claude": {"Shako": [{"reel": "r1", "frame": "f_2.jpg"}]}}
        self.assertEqual(self._run(m), 1, "the shallow walk regressed")

    def test_a_sighting_that_already_has_a_loc_is_left_alone_at_depth(self):
        m = {"notFoundSeen": {"uniques": {"Shako": [{"reel": "r1", "frame": "f_3.jpg",
                                                     "loc": "inventory"}]}}}
        self.assertEqual(self._run(m), 0, "an existing loc was recomputed and overwritten")
        self.assertEqual(m["notFoundSeen"]["uniques"]["Shako"][0]["loc"], "inventory")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
