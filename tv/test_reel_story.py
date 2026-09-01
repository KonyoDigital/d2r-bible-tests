"""The pipeline board must not invent a stage, and must not hide that it could not measure one.

Konyo asked for the shelf to show "whats happening and needs to happen storyline synced to the
process, visually and the backend of it" — which only works if the picture is the backend's
answer and not a second opinion about it. These guards pin exactly that.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# These docstrings carry ★ and ⚠, and unittest PRINTS them. On a non-UTF-8 console that is a
# UnicodeEncodeError instead of a test report — a suite that cannot report its own verdict.
try:
    import console_safe
    console_safe.enable()
except Exception:
    pass

import reel_story as RS


class TestUnknownIsNotZero(unittest.TestCase):
    """★ The single rule this whole board turns on: a reel nobody surveyed and a reel that was
    surveyed and carried nothing are OPPOSITE FACTS, and only one of them is a reason to delete
    footage that has no un-delete. [[unknown-stays-unknown]]"""

    def test_a_reel_absent_from_the_triage_store_yields_None_not_zero(self):
        p, f, r = RS._yield_of({}, "reel_nobody_looked_at")
        self.assertIsNone(r, "an unsurveyed reel reported a ratio — that is a measurement nobody "
                             "made, and it would rank the reel as pure waste")
        self.assertIsNone(p)
        self.assertIsNone(f)

    def test_a_SURVEYED_reel_that_carried_nothing_yields_0_not_None(self):
        p, f, r = RS._yield_of({"reel_x": {"panels": 0, "frames": 40}}, "reel_x")
        self.assertEqual(r, 0.0, "a surveyed-and-empty reel must report 0.0 — reporting None "
                                 "would hide the very footage the prune exists to find")
        self.assertEqual((p, f), (0, 40))

    def test_a_store_that_could_not_be_READ_is_unknown_for_every_reel(self):
        """`story()` passes None for the store when retro_triage.load() said not-ok. A reel then
        reads UNKNOWN rather than inheriting a zero from a file nobody could parse."""
        self.assertEqual(RS._yield_of(None, "anything"), (None, None, None))

    def test_zero_frames_is_not_a_division(self):
        p, f, r = RS._yield_of({"r": {"panels": 3, "frames": 0}}, "r")
        self.assertIsNone(r, "frames=0 must not produce a ratio")
        self.assertEqual((p, f), (3, 0))


class TestAnUnknownVerdictRefusesRatherThanGuesses(unittest.TestCase):
    """★ A retention verdict this board has never been taught must not be silently bucketed.

    Defaulting to the FIRST stage draws a finished reel as untouched; defaulting to the LAST
    draws a held reel as ready to delete. Both are confident pictures of something nobody
    established, and the second one deletes his footage."""

    def test_an_unmapped_tag_gets_no_stage(self):
        stage, idx = RS._stage_of("a-rule-invented-next-year")
        self.assertIsNone(stage)
        self.assertEqual(idx, -1)

    def test_it_does_not_quietly_become_the_first_stage(self):
        self.assertNotEqual(RS._stage_of("a-rule-invented-next-year")[0], RS.STAGES[0])

    def test_it_does_not_quietly_become_RELEASABLE(self):
        """The dangerous direction: 'releasable' is the stage the prune acts on."""
        self.assertNotEqual(RS._stage_of("a-rule-invented-next-year")[0], "releasable")

    def test_every_rule_reel_retention_can_EMIT_has_a_stage(self):
        """⚠ THE PREMISE, AND IT IS THE POINT OF THIS FILE. If reel_retention grows a rule and
        nobody teaches TAG_STAGE, the board silently shows a reel as 'unmapped' forever. Better
        to go red here, next to the map, than to be discovered on his screen."""
        import reel_retention as RR
        missing = [r for r in RR.RULES if r not in RS.TAG_STAGE]
        self.assertEqual(missing, [],
                         "reel_retention can emit %s, which reel_story.TAG_STAGE has no stage "
                         "for — teach the map" % missing)

    def test_the_map_does_not_name_a_rule_that_no_longer_EXISTS(self):
        """The mirror, and the one that rots quietly: a stage kept for a rule that was deleted
        reads as coverage this board does not have. [[label-outlived-referent]]"""
        import reel_retention as RR
        stale = [t for t in RS.TAG_STAGE if t not in RR.RULES]
        self.assertEqual(stale, [],
                         "reel_story.TAG_STAGE still maps %s, which reel_retention no longer "
                         "emits" % stale)


class TestTheBoardNeverDECIDES(unittest.TestCase):
    """★ reel_story reads verdicts; it must never compute one. Two authorities over footage that
    has no un-delete is the worst outcome available here."""

    def test_it_does_not_write(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "reel_story.py"),
                   encoding="utf-8").read()
        # assembled, not written, so this guard does not match its own assertion text
        for bad in ("os." + "remove", "shutil." + "rmtree", "os." + "unlink",
                    "apply_" + "plan", ".write("):
            self.assertNotIn(bad, src,
                             "reel_story must stay read-only; found %r" % bad)

    def test_a_plan_that_failed_is_reported_not_swallowed(self):
        """An unbuildable board and an empty shelf are opposite facts."""
        import reel_retention as RR
        real = RR.plan
        try:
            RR.plan = lambda **kw: {"ok": False, "why": "the disk is on fire"}
            out = RS.story()
        finally:
            RR.plan = real
        self.assertFalse(out["ok"])
        self.assertIn("disk is on fire", out["why"])
        self.assertEqual(out["reels"], [])


class TestTheAggregateSaysWhatItCovers(unittest.TestCase):
    """★ A percentage with no stated population is a number that claims more than it earned."""

    def _story_over(self, kept, triage, t_ok=True):
        import reel_retention as RR
        import retro_triage as RT
        rp, rl = RR.plan, RT.load
        try:
            RR.plan = lambda **kw: {"ok": True, "hist": "/x", "onDisk": len(kept),
                                    "candidates": [], "kept": kept, "unreadable": [], "freeMb": 0}
            RT.load = lambda *a, **k: (triage, t_ok)
            return RS.story()
        finally:
            RR.plan, RT.load = rp, rl

    def test_unsurveyed_reels_are_EXCLUDED_and_COUNTED(self):
        out = self._story_over(
            [{"reel": "a", "mb": 10, "pages": 1, "tag": "eligible", "why": ""},
             {"reel": "b", "mb": 10, "pages": 1, "tag": "eligible", "why": ""}],
            {"a": {"panels": 5, "frames": 10}})           # b was never surveyed
        y = out["yield"]
        self.assertEqual(y["usefulPct"], 50.0, "b's absence must not drag the percentage down — "
                                               "it was never measured")
        self.assertEqual(y["reelsMeasured"], 1)
        self.assertEqual(y["reelsUnmeasured"], 1,
                         "the excluded reel must be COUNTED on the payload, or the percentage "
                         "reads as covering the whole shelf")

    def test_an_unreadable_store_is_declared_on_the_payload(self):
        out = self._story_over(
            [{"reel": "a", "mb": 10, "pages": 1, "tag": "eligible", "why": ""}],
            {}, t_ok=False)
        self.assertIsNone(out["yield"],
                          "with an unreadable store nothing was surveyed, so there is no yield — "
                          "not a yield of zero")

    def test_no_surveyed_reel_at_all_gives_None_not_a_tidy_zero(self):
        out = self._story_over(
            [{"reel": "a", "mb": 10, "pages": 1, "tag": "eligible", "why": ""}], {})
        self.assertIsNone(out["yield"])

    def test_hold_kind_separates_a_DELIBERATE_hold_from_a_STUCK_one(self):
        """On screen these are different colours, because painting them alike is how a real
        blocker gets scrolled past and a deliberate fixture reads as waste."""
        out = self._story_over(
            [{"reel": "a", "mb": 1, "pages": 0, "tag": "test-fixture", "why": ""},
             {"reel": "b", "mb": 1, "pages": 0, "tag": "zero-pages", "why": ""},
             {"reel": "c", "mb": 1, "pages": 9, "tag": "eligible", "why": ""},
             {"reel": "d", "mb": 1, "pages": 0, "tag": "ledger-unreadable", "why": ""}],
            {})
        kind = {r["reel"]: r["holdKind"] for r in out["reels"]}
        self.assertEqual(kind["a"], "policy")
        self.assertEqual(kind["b"], "evidence")
        self.assertIsNone(kind["c"], "an eligible reel is not held at all")
        self.assertEqual(kind["d"], "global")


if __name__ == "__main__":
    unittest.main(verbosity=2)
