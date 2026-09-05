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

    def test_the_store_names_are_QUOTED_from_their_owners_never_retyped(self):
        """⚠⚠ REG-534, and the consequence was REPRODUCED before it was believed. The first cut
        hardcoded "retro_triage.json" and "vault_swept.json". Rename the store in its owning module
        and this probe does not follow: `triaged` — 40 of 40 reels covered — silently vanishes from
        the dated rungs while the verdict stays PARTIAL and nothing looks wrong. A wrong answer
        wearing a measurement's clothes. [[copy-drift]] §1: name ONE source, everything else quotes
        it. This is the check that a second name never appears here again.
        """
        import frame_authority as FA
        import retro_triage as RT
        self.assertEqual(
            OF._store_of("triaged")[0], RT.STORE,
            "the funnel names a different triage store than retro_triage declares. It must QUOTE "
            "the owner's constant — a second copy of a filename is a rename away from silently "
            "reporting a covered rung as undated.")
        self.assertEqual(
            OF._store_of("swept")[0], FA.SEAL_STORE,
            "the funnel names a different seal store than frame_authority declares — same defect, "
            "other rung.")

    def test_the_waypoint_VIEW_cannot_go_stale_behind_the_resolver(self):
        """⚠⚠ REG-537. The fix for REG-534 re-created the defect ONE LINE BELOW ITSELF: a frozen
        `WAYPOINTS = {rung: _store_of(rung)[0] ...}` evaluated once at import, so the moment an
        owner renamed its store the snapshot disagreed with the resolver three lines above it.
        Reproduced — `_store_of('triaged')` followed the rename, `WAYPOINTS['triaged']` did not.
        And its own comment claimed a reader and a guard that a grep found do not exist.
        [[plumbing-with-no-tap]] A view that is a function cannot go stale.
        """
        import retro_triage as RT
        real = RT.STORE
        try:
            RT.STORE = "retro_triage_RENAMED.json"
            self.assertEqual(
                OF.waypoints()["triaged"], "retro_triage_RENAMED.json",
                "the waypoint view did not follow the owner's rename, so it is a snapshot again "
                "and will disagree with _store_of the moment anything moves")
        finally:
            RT.STORE = real
        self.assertEqual(OF.waypoints()["triaged"], RT.STORE,
                         "and it does not agree with the owner once restored either")

    def test_a_renamed_store_is_named_UNKNOWN_not_guessed(self):
        """⚠ BASELINE: the resolver must actually be able to fail, or the equality above is two
        constants agreeing with themselves."""
        import retro_triage as RT
        real = RT.STORE
        try:
            RT.STORE = ""
            name, why = OF._store_of("triaged")
            self.assertIsNone(name, "an owner that stopped declaring its store still yielded a "
                                    "filename, which is a guess: %r" % (name,))
            self.assertIn("STORE", why, "the reason does not name what went missing: %r" % why)
        finally:
            RT.STORE = real

    def test_an_unreadable_store_names_the_FILE_in_its_reason(self):
        """⚠ The first cut printed str(e)[:60], which on a real path cut off mid-directory —
        `/Users/konyo/d2r_bible` — hiding the one word that would diagnose it."""
        import retro_triage as RT
        real = RT.STORE
        try:
            RT.STORE = "no_such_store_ever.json"
            cov = OF._waypoint_cover({"s_1"})
            w = cov["triaged"]
            self.assertIsNone(w["covered"], "a missing store was counted as coverage: %s" % w)
            self.assertIn("no_such_store_ever.json", w["why"],
                          "the reason does not name the file that would not read, so a reader "
                          "cannot tell WHICH store is missing: %r" % w["why"])
        finally:
            RT.STORE = real

    def test_an_UNREADABLE_store_makes_the_passage_UNKNOWN_not_UNRECORDED(self):
        """⚠⚠ REG-555. `UNRECORDED` says *no rung leaves a dated waypoint* — a finding about his
        PIPELINE. Measured with both waypoint stores pointed at a directory: `dated` came back
        empty and the passage reported UNRECORDED, **asserting that finding over evidence that was
        never gathered**. *No store records this rung* and *the store could not be read* are
        opposite facts and both produced an empty `dated`.

        ⚠ Found by asking what the three probes the per-probe law did NOT cover do with a real
        broken source — the law covered 3 of 6 and nothing said so.
        """
        import os
        import shutil
        import tempfile
        import frame_authority as FA
        import retro_triage as RT
        d = tempfile.mkdtemp(prefix="funnel_trap_")
        self.addCleanup(shutil.rmtree, d, True)
        trap = os.path.join(d, "trap.json")
        os.makedirs(trap)                      # a DIRECTORY where a file is expected
        rt, fa = RT.STORE, FA.SEAL_STORE
        try:
            # ⚠ THE ABSOLUTE PATH, NOT ITS BASENAME. `_waypoint_cover` resolves a store as
            # os.path.join(HERE, store), so "trap.json" pointed at tv/trap.json — a file that has
            # never existed — and the directory built two lines up was never opened. MEASURED: the
            # reason came back "No such file or directory", never "Is a directory", so the REG-555
            # scenario this test NAMES was passing on a different failure. os.path.join keeps an
            # absolute second argument, so this one actually reaches the trap.
            RT.STORE = FA.SEAL_STORE = trap
            # ⚠⚠ AND THE SHELF IS PLANTED, NOT BORROWED. This called OF.funnel() bare, which walks
            # the REAL tv/frames/hist — 639 reels on his Mac, ABSENT on a runner (gitignored, 0
            # tracked bytes). one_funnel.py:172 then takes its `if not rows` exit into _unknown(),
            # which hardcodes unreadableRungs=[], and CI read "[] != ['swept', 'triaged']" for four
            # pushes. The law was never measured there. `_run` plants the shelf the class already
            # owns, so the reading is about the STORES, which is what this test is for.
            r = self._run([{"reel": "reel_s_1", "stage": "swept", "stageIdx": 2,
                            "stageKnown": True}])
        finally:
            RT.STORE, FA.SEAL_STORE = rt, fa
        self.assertEqual(
            r["passage"], "UNKNOWN",
            "both waypoint stores were unreadable and the passage still reported %r — a claim "
            "about the pipeline made over evidence nobody gathered" % r["passage"])
        self.assertEqual(sorted(r["unreadableRungs"]), ["swept", "triaged"], r["unreadableRungs"])
        self.assertIn("COULD NOT BE READ", r["why"], r["why"])

    def test_the_unreadable_warning_survives_BOTH_ladder_branches(self):
        """⚠⚠ REG-558 — AN OPERATOR-PRECEDENCE BUG THAT SILENCED A REAL WARNING. The reason was
        built as `prefix + A if cond else B`, and `+` binds tighter than the conditional, so it
        parsed as `(prefix + A) if cond else B` — the unreadable-stores warning reached ONLY the
        ONE_LADDER text. Measured with both stores unreadable AND a stage collision: `passage` said
        UNKNOWN, `unreadableRungs` held two entries, **and the sentence a reader sees said nothing
        about either.** The numbers were right and the prose was silent.

        Both branches are asserted here, because a fix verified on one branch is how this happened.
        """
        import shutil
        import tempfile
        import frame_authority as FA
        import reel_story as RS
        import retro_triage as RT
        d = tempfile.mkdtemp(prefix="funnel_split_")
        self.addCleanup(shutil.rmtree, d, True)
        trap = os.path.join(d, "trap.json")
        os.makedirs(trap)
        rt, fa, story = RT.STORE, FA.SEAL_STORE, RS.story
        try:
            # ⚠ ABSOLUTE, not a basename: `_waypoint_cover` joins the store onto HERE, so
            # "trap.json" resolved to tv/trap.json and the directory above was never opened —
            # the rungs read unreadable on a FileNotFoundError instead. Same fix as REG-555's test.
            RT.STORE = FA.SEAL_STORE = trap
            # SPLIT branch: two reels claiming one rung with different stages
            RS.story = lambda *a, **k: {"reels": [
                {"reel": "r1", "stage": "swept", "stageIdx": 2, "stageKnown": True},
                {"reel": "r2", "stage": "banked", "stageIdx": 2, "stageKnown": True}]}
            split = OF.funnel()
            # ONE_LADDER branch, same unreadable stores
            RS.story = lambda *a, **k: {"reels": [
                {"reel": "r1", "stage": "swept", "stageIdx": 2, "stageKnown": True}]}
            one = OF.funnel()
        finally:
            RT.STORE, FA.SEAL_STORE, RS.story = rt, fa, story
        self.assertEqual(split["ladder"], "SPLIT_LADDER", "BASELINE: the split branch was not "
                                                          "reached, so this proves nothing: %s"
                         % split["ladder"])
        self.assertEqual(one["ladder"], "ONE_LADDER", one["ladder"])
        for label, r in (("SPLIT_LADDER", split), ("ONE_LADDER", one)):
            self.assertEqual(r["passage"], "UNKNOWN", "%s: %s" % (label, r["passage"]))
            self.assertIn("COULD NOT BE READ", r["why"],
                          "%s branch drops the unreadable-stores warning: %r" % (label, r["why"]))

    def test_a_row_that_names_NO_reel_is_not_asked_about_as_a_session(self):
        """⚠⚠ REG-559 — A PHANTOM SESSION ID, and the SAME class as the printer's phantom reel
        (REG-550) in a different module. Any row naming no reel added `""` to the session set, and
        every store was then asked whether it held a dated row for the empty string.

        ⚠ I swept that class when I found it in `printer.py` and this survived, because **a sweep
        of a class is only as wide as the modules you looked in.**
        """
        import reel_story as RS
        real = RS.story
        try:
            RS.story = lambda *a, **k: {"reels": [
                {"reel": "reel_s_1", "stage": "swept", "stageIdx": 2, "stageKnown": True},
                {"stage": "swept", "stageIdx": 2, "stageKnown": True},     # no `reel` key
                None]}                                                      # not a dict at all
            r = OF.funnel()
        finally:
            RS.story = real
        self.assertEqual(r["namelessRows"], 2,
                         "rows naming no reel were not counted: %s" % r["namelessRows"])

    def test_a_store_READ_AND_EMPTY_is_not_invisible(self):
        """⚠⚠ REG-559 — THREE FACTS, TWO LISTS. A rung's store can be ABSENT, UNREADABLE, or READ
        AND EMPTY. `covered == 0` fell out of `dated` AND out of `unreadable`, so a rung that was
        checked and found empty read exactly like a rung nobody records — different facts about
        his pipeline, sharing one silence."""
        cover = {"triaged": {"store": "x.json", "covered": 0, "why": "read, 0 dated"},
                 "swept": {"store": None, "covered": None, "why": "no store"},
                 "banked": {"store": "y.json", "covered": None, "why": "would not read"}}
        # ⚠⚠ `_run` PLANTS BOTH HALVES — this cover AND a reel on the shelf. Patching the cover
        # alone and calling OF.funnel() bare walked the real tv/frames/hist, which is gitignored
        # and absent on a runner, so one_funnel.py:172 returned _unknown() with emptyStoreRungs=[]
        # hardcoded and CI failed "[] != ['triaged']" — the cover was never consulted at all. A
        # fixture that only exists on his Mac is not a fixture. [[regression-guard]]
        r = self._run([{"reel": "reel_s_1", "stage": "swept", "stageIdx": 2, "stageKnown": True}],
                      cover=cover)
        self.assertEqual(r["emptyStoreRungs"], ["triaged"],
                         "a store that was READ and covered zero reels is in neither list: %s" % r)
        self.assertEqual(r["unreadableRungs"], ["banked"], r["unreadableRungs"])
        self.assertEqual(r["datedRungs"], [], r["datedRungs"])

    def test_BASELINE_UNRECORDED_is_still_reachable(self):
        """⚠ Or the fix traded one wrong verdict for an unreachable one: a rung with NO STORE AT
        ALL is genuinely undated, and that must still read UNRECORDED rather than UNKNOWN."""
        real = OF.WAYPOINT_SOURCES
        try:
            OF.WAYPOINT_SOURCES = {k: None for k in real}
            # ⚠ Same absent-shelf trap as the two above: a bare OF.funnel() read the real
            # tv/frames/hist, so on a runner this got UNKNOWN out of the empty-shelf exit and
            # NEVER out of the no-store-at-all path the baseline exists to reach — the reachability
            # it claims to prove was the one thing it stopped proving. `_run` plants the shelf.
            r = self._run([{"reel": "reel_s_1", "stage": "swept", "stageIdx": 2,
                            "stageKnown": True}])
        finally:
            OF.WAYPOINT_SOURCES = real
        self.assertEqual(r["passage"], "UNRECORDED",
                         "with no rung having a store at all the passage is genuinely UNRECORDED, "
                         "and it said %r" % r["passage"])
        self.assertEqual(r["unreadableRungs"], [], r["unreadableRungs"])

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
    # ⚠ HIS WINDOWS PC PRINTS STDOUT AS cp1255, AND EVERY ⚠ IN THIS FILE IS UNPRINTABLE THERE.
    # Without this the suite crashes while REPORTING — a clean tree exits non-zero and the failure
    # is in the messenger, not the subject. tv/test_control.py asserts every non-ASCII CLI enables
    # it, and it caught these two at the gate.
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
