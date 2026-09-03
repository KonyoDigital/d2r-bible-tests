# -*- coding: utf-8 -*-
"""A10 — a disagreement between two DIFFERENT questions is not a gap, and counting it teaches him to skip the row.

⚠⚠ THIS GUARD EXISTS BECAUSE THE MEASUREMENT MISLED ITS OWN AUTHOR. Walking the river I found
12 reels reporting RELEASABLE — "both lanes done; it may be pruned" — while `frame_authority`
refused every seal on the tree. Twelve reels cleared to go and the deletion authority saying no to
all of them reads exactly like the defect this repo keeps producing.

It is not one. `reel_retention` settled it in v2314, in a comment I had not read when I took the
measurement: *"frame_authority is stricter because it answers a DIFFERENT question — may this
FRAME go, protecting the witness frames behind his vault rows — not may this REEL go. Two
authorities at two granularities is correct; collapsing them was my error."* The v2312 attempt to
collapse them was WITHDRAWN, because it would have stopped the prune firing on every existing reel.

So the law: **a gap is two deciders answering the SAME question differently.** A probe that counts
the reel/frame split reports 12 gaps on a healthy tree, and a row that cries wolf is a row he
learns to skip — the exact defect CF-10 records three instances of.
[[measured-true-read-wrong]] [[the-unjoined-end]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import reel_river as RR   # noqa: E402


class AGapIsOnlyASameQuestionDisagreement(unittest.TestCase):

    def _run(self, story_rows, seals, covers=None):
        """Drive river() over constructed stages and seals."""
        import frame_authority as FA
        real_story, real_seals, real_cov = RR._story, FA.sealed_sessions, FA.seal_covers_extraction
        try:
            RR._story = lambda: (story_rows, "")
            FA.sealed_sessions = lambda root=None: (seals, True)
            if covers is not None:
                FA.seal_covers_extraction = covers
            return RR.river()
        finally:
            RR._story, FA.sealed_sessions, FA.seal_covers_extraction = real_story, real_seals, real_cov

    def test_the_reel_door_and_the_frame_door_disagreeing_is_NOT_a_gap(self):
        """The live shape, constructed: releasable at reel granularity, refused at frame granularity."""
        r = self._run([{"reel": "reel_s_1", "stage": "releasable"}],
                      {"s_1": {"ts": 1, "promptVer": "vpX"}})     # no `extracted` -> frame says no
        row = r["rows"][0]
        self.assertTrue(row["reelAnswer"], "BASELINE: the reel door did not say yes, so the two "
                                           "doors do not actually disagree here and this test is "
                                           "not exercising its own subject")
        self.assertIs(row["frameAnswer"], False,
                      "BASELINE: the frame door did not say no, same problem")
        self.assertEqual(
            r["gaps"], [],
            "the reel door and the frame door disagreed and it was counted as a GAP. They answer "
            "different questions — may this REEL go, versus may this FRAME go — and on his tree "
            "that would report 12 gaps on a healthy shelf. A row that cries wolf is a row he "
            "learns to skip; v2312 tried collapsing these and was withdrawn.")

    def test_the_two_questions_are_stated_on_the_row_itself(self):
        """A reader cannot tell two questions apart if only one of them is named."""
        r = self._run([{"reel": "reel_s_1", "stage": "releasable"}], {"s_1": {"ts": 1}})
        row = r["rows"][0]
        self.assertIn("REEL", row["question"] + row["frameQuestion"])
        self.assertIn("FRAME", row["frameQuestion"])
        self.assertNotEqual(
            row["decider"], row["frameDecider"],
            "both answers are attributed to the same decider, so the row cannot show that two "
            "different authorities answered two different questions")

    def test_a_reel_with_no_seal_is_UNASKED_not_refused(self):
        """8 of his 12 releasable reels have no seal at all. 'No seal' is a question never put."""
        r = self._run([{"reel": "reel_s_ZZZ", "stage": "releasable"}], {"s_other": {"ts": 1}})
        row = r["rows"][0]
        self.assertIsNone(
            row["frameAnswer"],
            "a reel with no seal reports frameAnswer=%r. Nobody asked the frame question about it; "
            "recording that as a refusal invents an answer." % (row["frameAnswer"],))
        self.assertIn("UNASKED", row["frameWhy"])

    def test_a_stage_with_no_declared_decider_IS_a_gap(self):
        """⚠ BASELINE for the whole file: `gaps` must be reachable, or the assertions above are
        just describing a function that can never report anything."""
        r = self._run([{"reel": "reel_s_1", "stage": "teleported"}], {})
        self.assertTrue(
            r["gaps"],
            "a stage nothing is declared to decide produced no gap. Then `gaps` is empty for every "
            "possible input and the emptiness above proves nothing.")
        self.assertIn("teleported", r["gaps"][0]["gap"])

    def test_an_unreadable_shelf_is_UNKNOWN_not_an_empty_river(self):
        real = RR._story
        try:
            RR._story = lambda: ([], "reel_story would not answer")
            r = RR.river()
        finally:
            RR._story = real
        self.assertFalse(r["ok"])
        self.assertIn("UNKNOWN", r["why"])

    def test_every_stage_reel_story_can_emit_has_a_declared_question(self):
        """If reel_story grows a stage and this map does not, every reel at that stage is a gap —
        which is honest, but it should be caught here rather than on his screen."""
        import reel_story as RS
        missing = [s for s in RS.STAGES if s not in RR.QUESTIONS]
        self.assertFalse(
            missing,
            "reel_story can report stage(s) %s that reel_river has no declared decider for. Every "
            "reel there would render as a gap." % missing)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
