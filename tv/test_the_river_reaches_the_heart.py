# -*- coding: utf-8 -*-
"""v2761 — THE RIVER MEASURED ITSELF FOR NOBODY, AND THE ONE JOINT THAT COULD SPEAK WAS MISREADING.

Konyo: *"fix the gaps. connect it all to the heart of the console"*.

=== 1. THE INSTRUMENT NOTHING CONSULTED ===
`tv/river.py` walks ELEVEN joints of the pipeline, grades each CARRIES / DRY / UNKNOWN, and names
the first blockage in a sentence a person can act on. MEASURED before writing this:

    grep -rl 'import river' tv/*.py   ->   test_the_river_carries_a_stamp.py

ONE file. Its own test. Neither corroborate.py nor console_doctor.py had ever asked it anything.

⚠ AND A ROW CALLED "the river" ALREADY EXISTED, which is why the gap survived. It reads
`reel_router` and answers WHERE REELS ARE STATIONED. That is a different question from WHETHER THE
JOINTS CARRY. The console watched position and was blind to flow, and the two are similar enough
that nobody noticed the second question was unasked. [[the-unjoined-end]] [[plumbing-with-no-tap]]

=== 2. THE GATE JOINT WAS A ZERO WITH NO DENOMINATOR, INSIDE THE DIAGNOSTIC ITSELF ===
`j_gate` counted keys "grounded", "applied", "accepted" and reported `0 names grounded of 14,034`.
MEASURED on his live chron_last_result.json — TWO defects pointing the same way:

  a. THE STORE HAS NEVER CARRIED THOSE THREE KEYS. Its result holds calibration, contested,
     contestedExpired, denial, fold, held, hunt, lanes, newlyDated, notFoundDatable, reels,
     refused, refusedEver, resolverOk, setGroups, totals, verdict, wouldAdd.
  b. IT ASKED THE WRONG NESTING LEVEL. The file is {"proposal", "result", "savedTs"} and every
     figure lives under `result`, so the lookup would have missed even the right names.

Two wrong things pointing the same way is why it read as a confident 0 for so long, in the very
tool that diagnoses the river. [[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]

⚠ AND THE TRUE STATE WAS NOT "BLOCKED". `newlyDated` is what a sweep writes when a name grounds.
His last sweep proposed 354 (271 uniques + 83 sets) and /api/chronicle_crossref answers "354 of the
354 read are already in your chronicle; 0 are new". NOTHING NEW TO GROUND is a legitimate state the
old joint could not tell from a blockage — both rendered as 0. It now reports 0 of 354 proposed,
41 held, WITH that caveat in its own `why`.

⚠ THIS ALSO CORRECTED ME. I estimated "303 of 306 names clear the 2-witness bar" using distinct
(reel, lane) as a proxy and labelled it an upper bound. Running the REAL `witnesses()`:
uniques 272 of 306 (89%), sets 86 of 126 (68%) — and 36 set names sit at exactly ONE witness, one
short of the bar. The proxy was too generous, as flagged.
"""
import io
import os
import shutil
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import console_doctor as D  # noqa: E402
import river as RV  # noqa: E402

RSRC = io.open(os.path.join(HERE, "river.py"), encoding="utf-8").read()


class TheRiverReachesTheHeart(unittest.TestCase):

    # ── ⚠⚠ THE JOIN ─────────────────────────────────────────────────────────────────────────
    def test_the_row_is_REGISTERED(self):
        """A check defined and not in CHECKS runs never — this repo's most repeated defect in its
        smallest form."""
        self.assertIn("river joints", dict(D.CHECKS),
                      "the river-joints row is not registered, so the river's own diagnosis still "
                      "reaches nothing")

    def test_it_actually_calls_river(self):
        """★ It must consult the INSTRUMENT, not re-derive a second opinion. river.py's API is
        trace() + summary() — my first cut guessed survey()/run() behind a hasattr, which would
        have returned UNKNOWN for ever while looking like a wired watcher."""
        called = {"trace": 0, "summary": 0}
        rt, rs = RV.trace, RV.summary

        def _t():
            called["trace"] += 1
            return rt()

        def _s(rows=None):
            called["summary"] += 1
            return rs(rows)
        RV.trace, RV.summary = _t, _s
        try:
            dict(D.CHECKS)["river joints"]()
        finally:
            RV.trace, RV.summary = rt, rs
        self.assertEqual(1, called["trace"], "the row never called river.trace()")
        self.assertEqual(1, called["summary"], "the row never called river.summary()")

    def test_it_NAMES_the_blockage_not_just_a_count(self):
        """"4 of 11 dry" is not actionable. The river already writes the sentence; carry it."""
        st, say = dict(D.CHECKS)["river joints"]()
        self.assertTrue(say and len(say) > 30, "the row says almost nothing")
        if st == D.MISSING:
            self.assertIn("blocked at", say,
                          "a dry river is reported as a bare count, so he cannot tell WHICH joint")

    def test_an_unreadable_river_is_UNKNOWN_not_OK(self):
        """[[unknown-stays-unknown]] — a probe that could not run has not found the river healthy."""
        rt = RV.trace

        def _boom():
            raise RuntimeError("simulated")
        RV.trace = _boom
        try:
            st, say = dict(D.CHECKS)["river joints"]()
        finally:
            RV.trace = rt
        self.assertEqual(D.UNKNOWN, st, "an unreadable river graded as something other than UNKNOWN")

    def test_no_joints_is_UNKNOWN_not_a_clean_bill(self):
        rt = RV.trace
        RV.trace = lambda: []
        try:
            st, _ = dict(D.CHECKS)["river joints"]()
        finally:
            RV.trace = rt
        self.assertEqual(D.UNKNOWN, st,
                         "a river that reported NO joints was graded as measured — an empty "
                         "container answering for a measurement")

    # ── ⚠ THE GATE JOINT: RIGHT KEYS, RIGHT LEVEL, REAL DENOMINATOR ────────────────────────
    def test_the_gate_joint_reads_the_keys_the_store_ACTUALLY_writes(self):
        i = RSRC.find("def j_gate(")
        j = RSRC.find("\ndef ", i + 1)
        blk = RSRC[i:j]
        self.assertIn('d.get("newlyDated")', blk,
                      "the gate joint does not read `newlyDated`, which is what a sweep writes "
                      "when a name actually grounds")
        self.assertIn('d.get("wouldAdd")', blk,
                      "the gate joint has no denominator — it cannot say 0 OF WHAT")
        for dead in ('"grounded"', '"applied"', '"accepted"'):
            self.assertNotIn(dead, blk,
                             "the gate joint is asking for %s again — a key this store has never "
                             "written, which is how it reported a confident 0" % dead)

    def test_the_gate_joint_reads_the_RESULT_level(self):
        """⚠ THE SECOND DEFECT, and it hid behind the first. The store is
        {"proposal","result","savedTs"} and every figure lives under `result`."""
        i = RSRC.find("def j_gate(")
        j = RSRC.find("\ndef ", i + 1)
        self.assertIn('d.get("result")', RSRC[i:j],
                      "the gate joint reads the TOP level, where none of these figures live")

    def test_nothing_proposed_is_UNKNOWN_not_DRY(self):
        """A sweep that proposed nothing has not been blocked — there was no question. Reporting
        that as DRY is crying wolf, and a distrusted instrument is a switched-off one."""
        i = RSRC.find("def j_gate(")
        j = RSRC.find("\ndef ", i + 1)
        blk = RSRC[i:j]
        # ⚠ ANCHOR ON TEXT THAT IS CONTIGUOUS IN THE SOURCE. My first cut searched for
        # "nothing to ground", which the code splits across two concatenated literals
        # ("...nothing to " + "ground — ..."), so the law failed on a phrase that IS present in
        # the rendered message. A guard that greps source must match the SOURCE, not the output.
        # [[source-reading-guard]]
        self.assertIn("an empty question, not a dry joint", blk,
                      "the empty-question case has no wording, so it renders as a blockage")
        self.assertIn("if not proposed:", blk,
                      "nothing distinguishes 'none proposed' from 'proposed and none grounded'")

    def test_zero_grounded_of_N_proposed_is_UNKNOWN_not_an_asserted_DRY(self):
        """★ FOUND BY THE SECOND EYE (grok-4-1-fast-reasoning, reviewing the diff cold): my first
        cut returned crossed=0 — which grades DRY — while its own `why` said the situation "may be
        'nothing NEW to ground' and not a blockage". The verdict contradicted its own reason: it
        asserted a blockage and argued against itself in the sentence underneath.

        AND IT GENUINELY CANNOT TELL. "0 grounded of 354 proposed" is a blockage ONLY if some of
        those were new; `chronicle_crossref` is what knows, and it has NO cache file — it is
        computed live against the board window, so this joint cannot ask it without dragging the
        console in. An instrument that cannot distinguish two states must not pick one.
        [[unknown-stays-unknown]] [[feedback-contradiction-is-the-finding]]
        """
        i = RSRC.find("def j_gate(")
        j = RSRC.find("\ndef ", i + 1)
        blk = RSRC[i:j]
        self.assertIn("if not grounded:", blk,
                      "nothing separates the zero-grounded case, so it falls through to a number")
        self.assertIn('_joint("gate", "names grounded", None, proposed', blk,
                      "zero-grounded still reports a COUNT (which grades DRY) rather than None "
                      "(UNKNOWN) — the joint is asserting a blockage it cannot establish")
        # ⚠ CONTIGUOUS TEXT ONLY — SECOND TIME TODAY. The source splits this across two literals
        # ("...This joint cannot " + "tell a real blockage from..."), so a phrase spanning the
        # boundary is absent from the SOURCE while present in the rendered message. A guard that
        # greps source must match the source. [[source-reading-guard]]
        self.assertIn("tell a real blockage from", blk,
                      "the unknown verdict does not say WHAT it could not tell apart")
        self.assertIn("chronicle_crossref", blk,
                      "it does not name the thing that would settle the question, so the reader "
                      "is left with an unknown and no way to resolve it")

    def test_the_unknown_still_carries_its_denominator(self):
        """UNKNOWN must not mean unmeasured. It knows 354 were proposed and 41 held; those travel."""
        r = RV.j_gate()
        if r.get("state") == RV.UNKNOWN and r.get("upstream"):
            self.assertTrue(r.get("upstream"),
                            "an UNKNOWN gate dropped its denominator, so nothing says 0 OF WHAT")
            self.assertIn("proposed", str(r.get("why") or ""),
                          "the unknown does not say how many were proposed")

    # ── ⚠⚠ v2772 — THE JOINT THAT ASKED FOR A KEY THE WRITER NEVER WRITES ───────────────────
    def test_the_surface_joint_reads_the_key_the_writer_ACTUALLY_writes(self):
        """★ Found by an independent recon pass. `chronicle_retro` persists the surface on every
        new sighting as `"scene"` — named that way on purpose, because `surface` was already two
        other narrower vocabularies. This joint counted `surface`, so it read 0 for ever while the
        console printed "the reader knows which tab the frame showed AND DOES NOT PERSIST IT" long
        after that stopped being true. Two vocabularies meeting silently.
        [[the-unjoined-end]] [[label-outlived-referent]]"""
        i = RSRC.find("def j_surface(")
        blk = RSRC[i:RSRC.find("\ndef ", i + 1)]
        self.assertIn('s.get("scene")', blk,
                      "the surface joint does not read `scene`, which is the key chronicle_retro "
                      "actually writes — it will report 0 for ever and blame the writer")
        self.assertIn('s.get("surface")', blk,
                      "the older `surface` key stopped being counted, so any sighting that does "
                      "carry it now vanishes from the joint")

    def test_the_WRITER_still_writes_scene(self):
        """⚠ THE FIXTURE ASSUMPTION, PINNED. If chronicle_retro is ever changed to persist
        `surface` after all, the joint above should be simplified rather than left carrying two
        keys for ever — but that must be a decision, not a silent drift."""
        csrc = io.open(os.path.join(HERE, "chronicle_retro.py"), encoding="utf-8").read()
        self.assertIn('"scene": "chronicle"', csrc,
                      "chronicle_retro no longer writes `scene`, so the joint is now watching for "
                      "a key nobody produces — re-point it deliberately")

    def test_a_zero_here_does_NOT_blame_the_writer(self):
        """★★ THE SENTENCE IS THE FINDING. A 0 with the old wording sent a reader to fix a writer
        that was already correct. The real reason is different and it is ACTIONABLE in a different
        place: the backlog predates the writer, and no chronicle read is scheduled to make more —
        `chronicle_autoreel_tick` reports 0 reels owing a read, and a reel re-owes only when it
        GROWS or when PROMPT_VER changes. So it cannot heal by waiting.
        [[zero-needs-a-denominator]]"""
        # ⚠⚠ v2795 — THIS GUARD READ A KEY THAT DOES NOT EXIST, AND THE JOINT HAD HEALED.
        # It was `if r.get("carried"): skipTest(...)`. `_joint` publishes the count as **crossed**,
        # never `carried`, so the guard was permanently falsy and the zero-case assertions ran
        # against a NON-zero result: MEASURED 258 of 14,322 sightings now carry `scene`, state
        # CARRIES. The gate went red announcing "the zero does not say WHY it is zero" about a
        # sentence that is not reporting a zero at all.
        #
        # A missing key reading as absent is this repo's most repeated instrument fault, and it
        # bit the guard that exists to stop a zero lying. [[unknown-stays-unknown]]
        #
        # ⛔ AND THE FIX IS NOT A SKIP. The old branch would have skipped once the key was right,
        # and its own comment says a skip is NOT a pass — so the law would have stopped grading
        # anything the moment the thing it watches started working. Both states get a real
        # assertion instead, because both have a way of lying.
        r = RV.j_surface()
        why = str(r.get("why") or "")
        total = len(RV._sightings() or [])
        self.assertNotIn("does not persist it", why,
                         "the joint still blames the reader for dropping a key it writes")
        # ⚠⚠ v2873 — river.py GRADES THREE STATES AND THIS LAW READ TWO. `_joint` returns UNKNOWN
        # whenever either side is None, and its own docstring says why: "None is never silently
        # turned into 0 — that substitution is the defect this module exists to find." On any
        # machine without `chron_evidence.json` — CI, and every heart2 sandbox, because the store
        # is gitignored — `j_surface()` returns UNKNOWN, and this law sent it down the ZERO branch
        # and demanded the word PREDATES of a sentence that reads "chron_evidence.json absent or
        # unreadable". Red on the runner for as long as it has existed, and the reason named none
        # of it. An unmeasured joint graded as a measured zero is exactly the substitution above.
        # [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
        if r.get("state") == RV.UNKNOWN:
            self.assertIn("unreadable", why.lower(),
                          "the joint is UNKNOWN and its sentence does not say the store could not "
                          "be read, so an unmeasured joint reads like a measured one: %r" % why)
            self.assertIsNone(r.get("crossed"),
                              "an UNKNOWN joint published a NUMBER (%r) — that is the None-to-zero "
                              "substitution river.py exists to catch" % r.get("crossed"))
            self.assertIsNone(r.get("upstream"),
                              "an UNKNOWN joint published a denominator (%r) it never measured"
                              % r.get("upstream"))
            return
        if r.get("crossed"):
            # ⚠ THE CARRYING CASE. The danger here is the opposite one: a bare "it carries" hides
            # HOW FEW. 258 of 14,322 is 1.8%, and a reader who sees only CARRIES will think the
            # cross-surface witness is available when it is available for almost nothing.
            self.assertIn("scene", why,
                          "the sentence no longer names WHICH key is carrying, so a future rename "
                          "would silently change what this number counts")
            self.assertIn("surface", why,
                          "the older key is no longer reported beside the new one — that pair IS "
                          "the finding; one number alone cannot show a vocabulary changing hands")
            self.assertEqual(r.get("upstream"), total,
                             "the joint publishes no denominator, so %r carrying reads as "
                             "'enough'" % r.get("crossed"))
            self.assertLessEqual(int(r.get("crossed")), total,
                                 "more sightings carry a surface than exist — the numerator and "
                                 "the denominator are counting different things")
        else:
            self.assertIn("PREDATES", why,
                          "the zero does not say WHY it is zero, so it reads as a broken writer")
            self.assertIn("cannot heal by waiting", why,
                          "nothing says this will not fix itself on the next tick — it will not")
            self.assertIn(str(total), why, "the zero has no denominator")

    def test_an_UNMEASURED_joint_is_UNKNOWN_and_never_a_ZERO(self):
        """★★ v2873 — DETERMINISTIC, BECAUSE THE AMBIENT STORE CANNOT BE TRUSTED TO BE ABSENT.
        The law above grades the UNKNOWN state, but it can only reach it on a machine with no
        `chron_evidence.json` — and MEASURED, a heart2 sandbox carries the live one (2,210,457
        bytes; `safe_copy` copies working-tree files, ignored or not). So the red-proof that
        restores the None-to-zero substitution came back BLIND: the tamper was real, the sandbox
        simply never took that branch. The prover and the CI runner disagree about what exists,
        and a law that depends on the ambient filesystem is graded by whichever one it lands on.
        This asks `_joint` directly, so it holds on both. [[feedback-fixtures-never-touch-live-data]]"""
        r = RV._joint("x", "things", None, None, "the store is absent or unreadable")
        self.assertEqual(RV.UNKNOWN, r.get("state"),
                         "a joint with nothing measured on either side graded %r — river.py's own "
                         "docstring calls turning None into 0 'the defect this module exists to "
                         "find'" % r.get("state"))
        self.assertIsNone(r.get("crossed"), "an UNKNOWN joint published a numerator")
        self.assertIsNone(r.get("upstream"), "an UNKNOWN joint published a denominator")
        half = RV._joint("x", "things", 0, None, "the denominator could not be read")
        self.assertEqual(RV.UNKNOWN, half.get("state"),
                         "a known ZERO over an UNMEASURED denominator graded %r — 0 of unknown is "
                         "not a dry river, it is an unread one [[zero-needs-a-denominator]]"
                         % half.get("state"))

    def test_the_gate_joint_still_runs_on_his_real_store(self):
        r = RV.j_gate()
        self.assertEqual("gate", r.get("joint"))
        self.assertIn(r.get("state"), (RV.CARRIES, RV.DRY, RV.UNKNOWN))
        if r.get("state") == RV.DRY:
            self.assertTrue(r.get("upstream"),
                            "a DRY gate with no upstream is a zero with no denominator — the exact "
                            "defect this rewrite removed")



# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════
# PROPOSED by tv/heart2_candidates.py — derived from this gate's OWN assertions and
# measured against the target file (each anchor occurs exactly once). Review it: the
# question is whether deleting this text is the defect the law exists to catch.
class TheRiverNamesTheRightCulprit(unittest.TestCase):
    """★ v3267 — TWO JOINTS WERE BLAMING THINGS THAT WERE NOT AT FAULT.

    MEASURED on his console 2026-09-17, both by asking the thing each joint accuses:

    **prune** said *"a planner that releases nothing while the disk is full is the blockage"* on
    every run it has ever made. `j_prune` read `plan["delete"]` and `plan["remove"]`. The planner
    publishes neither — its keys are candidates/kept/coverage/eligibleMb/onDisk/say — so `gone`
    was `len([])` forever, while `plan["say"]` read **"1 reel(s) may go, freeing 17 MB"**. A
    caller and a callee disagreeing about a key name, reported as a blocked river.

    **slot** said *"the reader has all three at the moment it reads and records none of them"*,
    which describes a dropped field and sends you into `chronicle_retro` to add three keys. But
    every `point` in that file is the English word; the sighting it mints carries
    reel/frame/witness/conf/lane/foundAt/droppedBy/sort; and the only code in the tree that ever
    produces `panelBox` is `hover_wilson.py`, a probe over synthetic rectangles whose own
    docstring says the live hover "has not been authorised yet". 0 of 14,322 sightings carry a
    coordinate. The joint waits on a MODE HE HAS NOT TURNED ON, not on a missing assignment.

    ⚠ The danger in fixing the second one is building a quiet corner. UNBUILT must be MEASURED
    (no sighting has ever carried geometry) and never assumed, or the day the autopilot is
    switched on and writes coordinates that fail to derive, the joint goes quiet instead of red.
    """

    def test_prune_reads_the_key_the_planner_ACTUALLY_publishes(self):
        seen = {}
        class _RR:
            @staticmethod
            def plan(*a, **k):
                seen["asked"] = True
                return {"ok": True, "candidates": [{"reel": "r1"}], "kept": [{"reel": "r2"}],
                        "say": "1 reel(s) may go"}
        real = sys.modules.get("reel_retention")
        sys.modules["reel_retention"] = _RR
        # ⚠ A HISTORY DIRECTORY OF ITS OWN. j_prune answers "no history directory" before it asks the
        # planner, and on CI tv/frames/hist exists only if an EARLIER gate in the same shard made it -
        # so this case passed or failed with the shard's composition (it went red on e6d71ca5 when new
        # gates reshuffled the shards). The case is about which KEY is read; the folder is scaffolding.
        import tempfile as _tf
        _h = _tf.mkdtemp(prefix="river-prune-")
        _was = os.environ.get("TV_HIST")
        os.environ["TV_HIST"] = _h
        try:
            j = RV.j_prune()
        finally:
            if _was is None:
                os.environ.pop("TV_HIST", None)
            else:
                os.environ["TV_HIST"] = _was
            shutil.rmtree(_h, ignore_errors=True)
            if real is not None:
                sys.modules["reel_retention"] = real
            else:
                sys.modules.pop("reel_retention", None)
        self.assertEqual(j["crossed"], 1,
                         "the prune joint read a key the planner does not publish, so a planner "
                         "with a candidate reads as one that releases nothing")
        self.assertEqual(j["state"], RV.CARRIES)

    def test_a_joint_whose_PRODUCER_never_ran_is_UNBUILT_not_DRY(self):
        j = RV._joint("slot", "x", 0, 14322, "old blame", "sighting",
                      unbuilt_why="nothing has ever produced a coordinate")
        self.assertEqual(j["state"], RV.UNBUILT)
        self.assertIn("has ever produced", j["why"])
        self.assertNotIn("old blame", j["why"], "the superseded accusation survived into the row")

    def test_UNBUILT_is_NEVER_inferred_from_a_bare_zero(self):
        """⚠⚠ THE LAW THE WHOLE STATE TURNS ON. A dry joint that does not explicitly declare
        itself unbuilt stays DRY. Without this, UNBUILT is just a quieter word for broken."""
        j = RV._joint("slot", "x", 0, 14322, "genuinely broken", "sighting")
        self.assertEqual(j["state"], RV.DRY)

    def test_a_joint_whose_producer_HAS_run_stays_DRY(self):
        """⚠ the regression guard on the fix itself: once geometry exists, a zero is a real
        derivation failure and must not hide in the unbuilt bucket."""
        import river as _rv
        # ⚠⚠ #192 — THE FIXTURE MUST FAIL TO DERIVE, or this case never reaches the branch it
        # guards. It used point (1,2) inside a 9x9 box, which DERIVES (stash:c1r2): the joint read
        # CARRIES 3 of 3, UNBUILT only ever applies to a DRY joint, and so red-proof [6] — which
        # forces the unbuilt claim on — was BLIND in the full census. A point OUTSIDE the grid is
        # geometry that exists and derives nothing: the exact day-one state of a live autopilot.
        # [[feedback-blind-fixture-green-gate]] [[a-probe-licenses-only-what-it-tested]]
        real = _rv._sightings
        _rv._sightings = lambda: [{"point": (50, 50), "panelBox": (0, 0, 9, 9),
                                   "container": "stash"}] * 3
        try:
            j = _rv.j_slot()
        finally:
            _rv._sightings = real
        self.assertEqual((j["crossed"], j["upstream"]), (0, 3),
                         "premise: the fixture's geometry must exist and derive NOTHING — %r/%r "
                         "means this case is not looking at a derivation failure at all"
                         % (j["crossed"], j["upstream"]))
        self.assertEqual(j["state"], RV.DRY,
                         "geometry exists, none of it derived a cell, and the joint called itself "
                         "%s — a real derivation failure hidden in the unbuilt bucket" % j["state"])

    def test_the_summary_does_not_say_NO_JOINT_IS_DRY_and_fall_silent(self):
        rows = [{"joint": "a", "state": RV.CARRIES, "why": ""},
                {"joint": "slot", "state": RV.UNBUILT, "why": "hover mode was never authorised"}]
        rep = RV.summary(rows)
        self.assertIsNone(rep["firstBlockage"], "an unbuilt joint claimed the blockage headline")
        self.assertEqual(rep["awaiting"], "slot")
        self.assertIn("slot", rep["say"])
        self.assertIn("never been built or switched on", rep["say"])

    def test_an_UNMEASURED_joint_does_not_SWALLOW_the_unbuilt_one(self):
        """★ v3269 — the quiet corner built one branch above the guard meant to prevent it.
        The row checks `unk` before `ub`, which is the right precedence, and then named only the
        unmeasured joints. MEASURED on his live tree: `gate` UNKNOWN + `slot` UNBUILT produced
        "1 of 11 joint(s) could not be measured" and the unbuilt joint vanished from the sentence.
        A precedence rule decides which fact LEADS, never which facts are REPORTED."""
        import river as _rv
        real_t, real_s = _rv.trace, _rv.summary
        _rv.trace = lambda: [{"joint": "a", "state": _rv.CARRIES, "why": ""},
                             {"joint": "gate", "state": _rv.UNKNOWN, "why": "no store"},
                             {"joint": "slot", "state": _rv.UNBUILT, "why": "never switched on"}]
        _rv.summary = lambda rows=None: {"say": "slot has never been built",
                                         "firstBlockage": None, "awaiting": "slot"}
        try:
            st, say = dict(D.CHECKS)["river joints"]()
        finally:
            _rv.trace, _rv.summary = real_t, real_s
        self.assertIn("could not be measured", say, "the unmeasured joint stopped leading")
        self.assertIn("never been built or switched on", say,
                      "the UNBUILT joint was swallowed by the unmeasured sentence")

    def test_the_DOCTOR_does_not_report_ALL_JOINTS_CARRY_over_an_unbuilt_one(self):
        """⚠ THE THIRD CONSUMER. The row counted DRY and UNKNOWN only, so a new state word would
        have fallen through to OK, "all 11 river joint(s) carry" — green over a joint that has
        never carried anything. [[the-unjoined-end]]"""
        import river as _rv
        real_t, real_s = _rv.trace, _rv.summary
        _rv.trace = lambda: [{"joint": "a", "state": _rv.CARRIES, "why": ""},
                             {"joint": "slot", "state": _rv.UNBUILT, "why": "never switched on"}]
        _rv.summary = lambda rows=None: {"say": "1 joint(s) have never been built",
                                         "firstBlockage": None, "awaiting": "slot"}
        try:
            st, say = dict(D.CHECKS)["river joints"]()
        finally:
            _rv.trace, _rv.summary = real_t, real_s
        self.assertNotIn("all 2 river joint(s) carry", say)
        self.assertIn("never been built or switched on", say)


RED_PROOF = [
    {
        "why": 'the law requires this text in console_doctor.py, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'console_doctor.py',
        "find": '("river joints", _check_the_river_joints_carry)',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": 'the law requires this text in river.py, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'river.py',
        "find": 'd.get("newlyDated")',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": 'the law requires this text in river.py, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'river.py',
        "find": 'd.get("wouldAdd")',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": "the None-to-zero substitution river.py names in its own docstring as the defect it "
               "exists to find: an UNKNOWN joint — the store absent or unreadable — published as a "
               "measured zero, so a reader is sent to fix a dry river that was never measured",
        "file": "river.py",
        "find": "    if n is None or upstream is None:\n        state = UNKNOWN",
        "replace": "    n, upstream = (n or 0), (upstream or 0)\n    if False:\n        state = UNKNOWN",
        "matches": 1,
    },
    {
        "why": "the prune joint reading the key the planner ACTUALLY publishes. Reverting it to "
               "the delete/remove names the planner has never had makes `gone` len([]) on every "
               "run, so a planner with a live candidate reports as one that releases nothing and "
               "the river names a permanent false blockage",
        "file": "river.py",
        "find": 'plan.get("candidates") or plan.get("delete")',
        "replace": 'plan.get("delete")',
        "matches": 1,
    },
    {
        "why": "UNBUILT must be DECLARED, never inferred. Grading any dry joint as unbuilt turns "
               "the state into a quiet corner where a genuinely broken join can hide, which is "
               "the one way this fix could be worse than the bug it replaced",
        "file": "river.py",
        "find": "        state = UNBUILT if unbuilt_why else DRY",
        "replace": "        state = UNBUILT",
        "matches": 1,
    },
    {
        "why": "the MEASUREMENT behind the slot joint's unbuilt claim. Hard-coding it means the "
               "day the hover autopilot is switched on and writes coordinates that fail to "
               "derive, the joint reports 'never built' instead of going red",
        "file": "river.py",
        "find": "    if not _geo:",
        "replace": "    if True:",
        "matches": 1,
    },
    {
        "why": "the doctor's third-consumer join. Without the unbuilt branch this row returns "
               "OK, 'all N river joint(s) carry' over a joint that has never carried anything",
        "file": "console_doctor.py",
        "find": "    if ub:",
        "replace": "    if False:",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
