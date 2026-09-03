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

    def test_CLEAN_reports_both_doors_and_chooses_neither(self):
        """A15: *every one comes out clean at the far end* — and it does not say WHICH DOOR decides.

        ⚠ The two candidates disagree on his shelf: 12 finished by the reel door, 0 satisfying
        the frame contract. Conjoining them is exactly the collapse v2312 attempted and WITHDREW,
        because they answer different questions at different granularities (v2314). So both are
        reported and neither is called *the* answer — choosing is a decision about what
        "finished" means, and it gates the prune.
        """
        rows = [{"reel": "reel_s_1", "stage": "releasable"},
                {"reel": "reel_s_2", "stage": "swept"}]
        r = self._run(rows, {"s_1": {"ts": 1, "promptVer": "v"}})   # seal exists, contract unmet
        c = r.get("clean")
        self.assertTrue(c, "the report carries no `clean` reading at all")
        self.assertEqual(c["byReelDoor"], 1, "the reel-door count is wrong: %s" % c)
        self.assertEqual(c["byFrameContract"], 0, "the frame-contract count is wrong: %s" % c)
        self.assertEqual(
            c["byBoth"], 0,
            "byBoth is not the conjunction it claims to be: %s" % c)
        self.assertIn("Reported, not chosen", c["why"],
                      "the report does not say it is declining to choose between the two doors, "
                      "so a reader will take whichever number they saw first as the answer")

    def test_the_two_CLEAN_readings_are_counted_separately_not_merged(self):
        """⚠ BASELINE: if the two counts could never differ, reporting both would be theatre."""
        rows = [{"reel": "reel_s_1", "stage": "releasable"}]
        seal = {"s_1": {"ts": 1, "extracted": ["name", "location", "provenance"]}}
        r = self._run(rows, seal)
        c = r["clean"]
        self.assertEqual((c["byReelDoor"], c["byFrameContract"], c["byBoth"]), (1, 1, 1),
                         "a reel that satisfies BOTH doors was not counted by both: %s" % c)

    def test_CLEAN_does_not_bury_the_UNASKED_reels_inside_its_zero(self):
        """⚠⚠ REG-532. The rows keep a TRI-STATE and the first summary flattened it.

        Measured on his shelf: frame UNASKED 25, frame no 15, frame yes 0 — published as a bare
        `byFrameContract: 0`, which reads as a door refusing all forty. Fifteen of those are
        refusals; twenty-five are questions NOBODY PUT, because no seal exists for them. Every row
        already says so in `frameWhy`; the aggregate threw it away one layer above where this
        repo usually catches it. A count is only comparable next to its own denominator.
        [[unknown-stays-unknown]] §1
        """
        rows = [{"reel": "reel_s_1", "stage": "releasable"},     # sealed, contract unmet -> refused
                {"reel": "reel_s_2", "stage": "releasable"},     # no seal at all       -> UNASKED
                {"reel": "reel_s_3", "stage": "swept"}]          # mid-river at the reel door
        r = self._run(rows, {"s_1": {"ts": 1, "promptVer": "v"}})
        c = r["clean"]
        self.assertEqual(
            (c["byFrameRefused"], c["byFrameUnasked"]), (1, 2),
            "the frame door's zero does not separate refusals from questions never put: %s. One "
            "reel was refused and two were never asked — publishing them as one flat zero says "
            "the door turned away three reels it never saw." % c)
        self.assertEqual(
            (c["byReelDoor"], c["walked"], c["notYetAtReelDoor"]), (2, 3, 1),
            "the reel door's numerator arrives without its denominator: %s. `swept` is mid-river, "
            "not a refusal, so 2-of-3 is the honest reading and a bare 2 is not." % c)
        self.assertIn(
            "never asked", c["why"],
            "the `why` does not warn that the two counts have DIFFERENT denominators, so a reader "
            "comparing them directly is misled by the very block that promised not to choose")

    def test_BASELINE_the_unasked_count_can_be_zero(self):
        """⚠ Or the assertion above passes on a constant. Every reel sealed -> nothing unasked."""
        rows = [{"reel": "reel_s_1", "stage": "releasable"}]
        r = self._run(rows, {"s_1": {"ts": 1, "promptVer": "v"}})
        c = r["clean"]
        self.assertEqual(c["byFrameUnasked"], 0,
                         "a fully-sealed shelf still reports unasked reels, so the count is not "
                         "measuring what it names: %s" % c)
        self.assertEqual(c["byFrameRefused"], 1, "and the refusal was not counted either: %s" % c)

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
