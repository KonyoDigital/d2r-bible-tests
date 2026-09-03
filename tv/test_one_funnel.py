# -*- coding: utf-8 -*-
"""A15 clause 2 — ONE FUNNEL, and the way half an answer becomes a whole claim.

The clause holds two questions. One is answerable today and one is not:

    THE LADDER   is there ONE stage vocabulary?              ANSWERABLE — and the answer is yes
    THE PASSAGE  did each reel actually FLOW down it?        PARTIAL — 2 of 6 rungs are dated

⚠⚠ Answering the easy half and marking the clause done is exactly how a task gets called shipped
while the thing he asked for is unbuilt. So the two readings are separate fields, and a probe that
merges them — or that lets a ONE_LADDER verdict imply the passage is known — fails here.

⚠ AND OCCUPANCY IS NOT A ROUTE. `reel_story._stage_of` maps a reel's current HOLD TAG to the rung
it is stuck BEFORE. An empty rung means nobody is stuck there; it does NOT mean nobody passed. That
misreading is the one that opened A10 — 12 RELEASABLE beside a refusing frame authority, read as a
contradiction it was not.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import one_funnel as OF   # noqa: E402


class TheLadderAndThePassageAreTwoAnswers(unittest.TestCase):

    def _run(self, rows, rungs=("filmed", "triaged", "swept", "banked", "vault-done", "releasable"),
             cover=None):
        import reel_story as RS
        real_stages, real_story = RS.STAGES, RS.story
        real_cov = OF._waypoint_cover
        try:
            RS.STAGES = rungs
            RS.story = lambda *a, **k: {"reels": rows}
            if cover is not None:
                OF._waypoint_cover = lambda sids: cover
            return OF.funnel()
        finally:
            RS.STAGES, RS.story = real_stages, real_story
            OF._waypoint_cover = real_cov

    def _cov(self, dated):
        out = {}
        for r in ("filmed", "triaged", "swept", "banked", "vault-done", "releasable"):
            out[r] = ({"store": "x.json", "covered": 3, "why": "dated"} if r in dated
                      else {"store": None, "covered": None, "why": "no store records this rung"})
        return out

    def test_ONE_LADDER_does_not_imply_the_passage_is_known(self):
        """⚠⚠ THE WHOLE POINT. A single stage vocabulary is evidence about NAMES, not about flow."""
        rows = [{"reel": "reel_s_1", "stage": "swept", "stageIdx": 2, "stageKnown": True},
                {"reel": "reel_s_2", "stage": "releasable", "stageIdx": 5, "stageKnown": True}]
        r = self._run(rows, cover=self._cov(("triaged", "swept")))
        self.assertEqual(r["ladder"], "ONE_LADDER", r["why"])
        self.assertEqual(
            r["passage"], "PARTIAL",
            "the ladder verdict was allowed to speak for the passage. Two of six rungs leave a "
            "dated waypoint; calling that RECORDED marks A15 clause 2 done on evidence that does "
            "not exist. %s" % r["why"])
        self.assertIn("PASSAGE IS PARTIAL", r["why"],
                      "the summary does not warn that the passage is only partly recorded, so a "
                      "reader takes ONE_LADDER as the whole answer: %s" % r["why"])

    def test_a_rung_naming_two_stages_is_a_SPLIT_ladder(self):
        """⚠ BASELINE: if nothing could ever reach SPLIT_LADDER, ONE_LADDER is not a measurement."""
        rows = [{"reel": "reel_s_1", "stage": "swept", "stageIdx": 2, "stageKnown": True},
                {"reel": "reel_s_2", "stage": "banked", "stageIdx": 2, "stageKnown": True}]
        r = self._run(rows, cover=self._cov(("triaged",)))
        self.assertEqual(r["ladder"], "SPLIT_LADDER",
                         "index 2 named two different stages and the probe still called it one "
                         "ladder: %s" % r["why"])
        self.assertTrue(r["collisions"], "the collision was not reported at all: %s" % r)

    def test_a_reel_at_an_UNTAUGHT_stage_breaks_the_ladder_rather_than_being_dropped(self):
        rows = [{"reel": "reel_s_1", "stage": "teleported", "stageIdx": 9, "stageKnown": False}]
        r = self._run(rows, cover=self._cov(("triaged",)))
        self.assertEqual(r["unknownStage"], 1, "the untaught stage was silently skipped: %s" % r)
        self.assertEqual(r["ladder"], "SPLIT_LADDER",
                         "a reel at a stage the ladder does not know was folded into ONE_LADDER, "
                         "which is a lane with its own rungs going unreported: %s" % r["why"])

    def test_NO_dated_rung_reads_UNRECORDED_not_partial(self):
        rows = [{"reel": "reel_s_1", "stage": "swept", "stageIdx": 2, "stageKnown": True}]
        r = self._run(rows, cover=self._cov(()))
        self.assertEqual(r["passage"], "UNRECORDED",
                         "no rung leaves a waypoint and the passage did not say so: %s" % r["why"])

    def test_an_UNREADABLE_store_is_not_counted_as_zero_coverage(self):
        """⚠ A store nobody could open says nothing about how many reels it holds. Counting it as
        0 turns an unread file into evidence that the rung is undated. [[unknown-stays-unknown]]"""
        cov = self._cov(("triaged",))
        cov["swept"] = {"store": "vault_swept.json", "covered": None,
                        "why": "the store would not read (boom)"}
        rows = [{"reel": "reel_s_1", "stage": "swept", "stageIdx": 2, "stageKnown": True}]
        r = self._run(rows, cover=cov)
        self.assertNotIn("swept", r["datedRungs"],
                         "an unreadable store was counted as a dated rung: %s" % r["datedRungs"])
        self.assertEqual(r["waypoints"]["swept"]["covered"], None,
                         "an unreadable store was flattened to a number: %s" % r["waypoints"])

    def test_an_EMPTY_shelf_is_UNKNOWN_on_both_readings(self):
        r = self._run([])
        self.assertEqual((r["ladder"], r["passage"]), ("UNKNOWN", "UNKNOWN"), r["why"])
        self.assertFalse(r["ok"])

    def test_occupancy_is_reported_but_never_used_as_the_passage(self):
        """An empty rung means nobody is STUCK there. The probe must not read that as unused."""
        rows = [{"reel": "reel_s_1", "stage": "releasable", "stageIdx": 5, "stageKnown": True}]
        r = self._run(rows, cover=self._cov(("triaged", "swept")))
        self.assertEqual(r["occupancy"].get("banked", 0), 0)
        self.assertIn("swept", r["datedRungs"],
                      "an unoccupied rung lost its dated waypoint, so occupancy decided the "
                      "passage after all: %s" % r["datedRungs"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
