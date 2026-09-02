"""v1511 — the retro sweep's laws, as tests.

Konyo's #1 priority in this arc is RETRO: the sealed reels already contain every Chronicle screen he
has opened on camera. What makes that safe to automate is not the reading — it is the three laws:
read-only until Apply, merge-max, and pay-for-runs. Each has a test here that fails loudly if it is
ever relaxed."""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import console_safe  # noqa: F401,E402  — non-ASCII in the failure messages must survive a
                     # non-UTF-8 console, or the suite crashes while REPORTING
import chronicle_retro as cr  # noqa: E402


def _sl():
    import shadow_ledger
    return shadow_ledger


def sig(v):
    """A fake fingerprint: 256 bytes all of value v. sig_diff(tol=28) then reads as |a-b|>28."""
    return bytes([v]) * 256


class TestStillRuns(unittest.TestCase):
    def test_a_held_screen_is_one_run_not_forty(self):
        # THE COST LAW: 40 frames of the same page must cost ONE classify, not 40 reads
        frames = [{"f": "f%d.jpg" % i, "ts": 1000 + i} for i in range(40)]
        runs = cr.still_runs(frames, lambda n: sig(100))
        self.assertEqual(len(runs), 1)
        self.assertEqual(len(runs[0]["frames"]), 40)

    def test_a_scene_change_starts_a_new_run(self):
        frames = [{"f": "a.jpg", "ts": 1}, {"f": "b.jpg", "ts": 2}, {"f": "c.jpg", "ts": 3}]
        vals = {"a.jpg": sig(10), "b.jpg": sig(10), "c.jpg": sig(220)}
        runs = cr.still_runs(frames, lambda n: vals[n])
        self.assertEqual([len(r["frames"]) for r in runs], [2, 1])

    def test_an_unreadable_frame_BREAKS_the_run(self):
        # ★ absorbing it would weld two different screens into one run, and the run is what we then
        # classify ONCE — the misgrouping would be invisible and wrong
        frames = [{"f": "a.jpg", "ts": 1}, {"f": "bad.jpg", "ts": 2}, {"f": "c.jpg", "ts": 3}]
        vals = {"a.jpg": sig(10), "bad.jpg": None, "c.jpg": sig(10)}
        runs = cr.still_runs(frames, lambda n: vals[n])
        self.assertEqual(len(runs), 2)
        self.assertNotIn("bad.jpg", runs[0]["frames"] + runs[1]["frames"])

    def test_runs_carry_their_time_span(self):
        frames = [{"f": "a.jpg", "ts": 500}, {"f": "b.jpg", "ts": 900}]
        r = cr.still_runs(frames, lambda n: sig(50))[0]
        self.assertEqual((r["start_ts"], r["end_ts"]), (500, 900))

    def test_a_glance_is_not_a_read(self):
        runs = [{"frames": ["a"]}, {"frames": ["a", "b"]}, {"frames": ["a", "b", "c"]}]
        self.assertEqual(len(cr.candidate_runs(runs)), 1)


class TestReadReel(unittest.TestCase):
    def setUp(self):
        # v1751 — THE DIRECTORY NAME IS A DELIBERATE TRAP. It carries "f2", one of the frame
        # tokens these tests classify on. That is not decoration: this class used to classify with
        # `"f2" in p` against the FULL path, and tempfile.mkdtemp() hands out names like
        # tmpf2i981c7 about 1.2% of the time — measured, and matching the 5/400 divergence the bug
        # actually produced. A 1.2% failure that only ever appeared inside the 30-gate run got
        # logged as ORDER-dependence for weeks.
        #
        # Naming the directory this way converts that coin flip into a certainty: revert any
        # classifier here to substring-matching the path and this class fails EVERY time, on the
        # first run, on any machine. A trap the fixture springs beats a comment asking people not
        # to. [[feedback_blind_fixture_green_gate]]
        self.d = tempfile.mkdtemp(prefix="f2trap_")
        frames = [{"f": "f%d.jpg" % i, "ts": 1000 + i} for i in range(12)]
        with open(os.path.join(self.d, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"sessionId": "s_test", "n": 12, "frames": frames}, fh)
        # frames 0-5 = one screen, 6-11 = another
        self.sigs = {"f%d.jpg" % i: sig(20 if i < 6 else 200) for i in range(12)}

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def _sweep(self, classify, read_page):
        return cr.read_reel(self.d, classify, read_page,
                            sig_of=lambda n: self.sigs.get(n))

    def test_ONE_classify_per_run_not_per_frame(self):
        # ★ THE COST LAW. 12 frames, 2 runs ⇒ 2 classifies. This is what makes the sweep affordable
        # across a whole hist directory instead of a one-off he never runs twice.
        calls = []
        r = self._sweep(lambda p: calls.append(p) or None, lambda p, k: {})
        self.assertEqual(r["runs"], 2)
        self.assertEqual(r["classified"], 2)
        self.assertEqual(len(calls), 2)

    def test_non_chronicle_runs_are_never_READ(self):
        # the expensive half must not fire for a town run
        reads = []
        self._sweep(lambda p: None, lambda p, k: reads.append(p) or {})
        self.assertEqual(reads, [])

    def test_a_chronicle_run_is_read_once_per_DISTINCT_page(self):
        # a held page is one page however many frames it spans; a scroll would be several
        reads = []

        def classify(p):
            # v1751 — MATCH THE FILENAME, NOT THE PATH. This read `"f2" in p` against the FULL
            # path, and the fixture's directory comes from tempfile.mkdtemp(), whose names look
            # like tmpf2i981c7. Measured: 1.2% of mkdtemp names contain f0, f2 or f3 — and when
            # one does, EVERY frame classifies as a chronicle, the second run gets read too, and
            # the test fails with "2 != 1". Measured divergence before the fix: 5/400 in a single
            # process, matching that 1.2% almost exactly.
            #
            # It was logged in BUGS.md as ORDER-dependent — "something earlier in the run leaves
            # frames or journal rows" — because it only ever showed up inside the 30-gate run and
            # passed 3/3 alone. It is neither order- nor concurrency-dependent: a long run simply
            # rolls the dice more times. read_reel is pure and takes no clock, which is what makes
            # a 1% failure look like contamination from a neighbour.
            #
            # The set is explicit rather than a substring test, so f1 can never match f10 or f11
            # either — the other trap in the original line. [[feedback_suspect_the_instrument]]
            return "chronicle-uniques" if os.path.basename(p) in {
                "f0.jpg", "f1.jpg", "f2.jpg", "f3.jpg"} else None

        r = self._sweep(classify, lambda p, k: reads.append(os.path.basename(p)) or {"found": []})
        self.assertGreaterEqual(len(r["pages"]), 1)
        self.assertEqual(len(reads), 1, "six identical frames of one page = ONE read")

    def test_every_page_keeps_the_frame_it_came_from(self):
        # provenance is load-bearing: "why does it think I have Windforce" must answer with a frame
        r = self._sweep(lambda p: "chronicle-uniques", lambda p, k: {"found": ["Windforce"]})
        self.assertTrue(r["pages"])
        for p in r["pages"]:
            self.assertTrue(p["frame"].endswith(".jpg"))
            self.assertEqual(p["reel"], "s_test")

    def test_a_missing_index_returns_evidence_of_nothing_not_a_crash(self):
        r = cr.read_reel(tempfile.mkdtemp(), lambda p: "chronicle-uniques", lambda p, k: {})
        self.assertEqual(r["pages"], [])
        self.assertEqual(r["note"], "no-index")


class TestClassifyAdapter(unittest.TestCase):
    """v1512 — the seam between the reader and the sweep."""

    def test_the_two_ledgers_map_to_their_own_kinds(self):
        self.assertEqual(cr.chronicle_kind({"scene": "chronicle", "chronicleTab": "uniques"}),
                         "chronicle-uniques")
        self.assertEqual(cr.chronicle_kind({"scene": "chronicle", "chronicleTab": "sets"}),
                         "chronicle-sets")

    def test_a_chronicle_page_with_an_UNKNOWN_ledger_is_not_read_at_all(self):
        # ★ the refusal that matters. Guessing "uniques" (bigger ledger, likelier screen) does not
        # cost a re-read — it writes set pieces into his grail.
        self.assertIsNone(cr.chronicle_kind({"scene": "chronicle", "chronicleTab": ""}))
        self.assertIsNone(cr.chronicle_kind({"scene": "chronicle"}))

    def test_every_other_scene_is_none(self):
        for sc in ("stash", "gameplay", "loot", "inventory", "transition", "town"):
            self.assertIsNone(cr.chronicle_kind({"scene": sc, "chronicleTab": "uniques"}),
                              sc + " must never classify as a chronicle")

    def test_junk_in_never_becomes_a_kind_out(self):
        for bad in (None, "chronicle", 42, [], {}):
            self.assertIsNone(cr.chronicle_kind(bad))

    def test_a_reader_that_throws_is_a_miss_not_a_crash(self):
        def boom(p):
            raise RuntimeError("model died")
        self.assertIsNone(cr.classifier(boom)("f.jpg"))

    def test_EVERY_probe_is_observable_including_the_misses(self):
        # "11 runs probed, 2 were Chronicle" is honest; reporting only the hits looks like the sweep
        # found everything there was to find
        seen = []
        c = cr.classifier(lambda p: {"scene": "gameplay"}, on_seen=lambda p, r: seen.append(p))
        self.assertIsNone(c("f1.jpg"))
        self.assertEqual(seen, ["f1.jpg"])


class TestSweepAKnownVisit(unittest.TestCase):
    """v1527 — what the live lane BUYS. A recorded visit already knows the two things a blind sweep
    pays a model to discover: that these frames are the Chronicle, and which ledger was open."""

    def test_a_known_visit_costs_ZERO_classifies(self):
        # ★ the whole point: the visit already answered the question the classify stage exists for
        reads = []
        r = cr.sweep_frames(["/x/reel_s1/f1.jpg", "/x/reel_s1/f2.jpg"], "chronicle-uniques",
                            lambda p, k: reads.append(p) or {"found": []},
                            sig_of=lambda p: sig(10 if p.endswith("f1.jpg") else 200))
        self.assertEqual(r["classified"], 0)
        self.assertEqual(r["pagesRead"], 2)

    def test_a_held_panel_is_ONE_read_not_forty(self):
        # he holds the panel still for seconds at 2fps; the same pixels must not cost 40 reads
        paths = ["/x/reel_s1/f%d.jpg" % i for i in range(40)]
        r = cr.sweep_frames(paths, "chronicle-sets", lambda p, k: {"found": []},
                            sig_of=lambda p: sig(60))
        self.assertEqual(r["framesGiven"], 40)
        self.assertEqual(r["pagesRead"], 1)

    def test_a_frame_WE_cannot_fingerprint_is_still_offered_to_the_model(self):
        # unreadable to our thumbnailer is not unreadable to the reader — dropping it would lose a page
        r = cr.sweep_frames(["/x/reel_s1/a.jpg", "/x/reel_s1/b.jpg"], "chronicle-uniques",
                            lambda p, k: {"found": []}, sig_of=lambda p: None)
        self.assertEqual(r["pagesRead"], 2)

    def test_pages_carry_their_reel_and_frame_so_the_evidence_still_works(self):
        r = cr.sweep_frames(["/x/reel_s_900/f7.jpg"], "chronicle-sets",
                            lambda p, k: {"ledger": "sets", "found": ["X"]}, sig_of=lambda p: sig(9))
        self.assertEqual(r["pages"][0]["reel"], "reel_s_900")
        self.assertEqual(r["pages"][0]["frame"], "f7.jpg")

    def test_the_visit_LEDGER_is_used_and_never_re_guessed(self):
        kinds = []
        cr.sweep_frames(["/x/reel_s1/a.jpg"], "chronicle-sets",
                        lambda p, k: kinds.append(k) or {}, sig_of=lambda p: sig(1))
        self.assertEqual(kinds, ["chronicle-sets"])

    def test_no_frames_reads_nothing(self):
        r = cr.sweep_frames([], "chronicle-uniques", lambda p, k: 1 / 0, sig_of=lambda p: sig(1))
        self.assertEqual(r["pagesRead"], 0)


class TestProposal(unittest.TestCase):
    def _pages(self, *resps):
        return [{"reel": "s1", "frame": "f%d.jpg" % i, "kind": "chronicle-uniques", "resp": r}
                for i, r in enumerate(resps)]

    def test_a_name_seen_twice_keeps_BOTH_sightings(self):
        # ★ the multi-witness signal the gate consumes — deduping the evidence would destroy it
        p = cr.proposal_from_pages(self._pages(
            {"ledger": "uniques", "found": ["Windforce"], "witness": "agree", "conf": 0.9},
            {"ledger": "uniques", "found": ["Windforce"], "witness": "none", "conf": 0.4},
        ))
        self.assertEqual(len(p["uniques"]["Windforce"]), 2)
        self.assertEqual({s["witness"] for s in p["uniques"]["Windforce"]}, {"agree", "none"})

    def test_a_REFUSED_page_contributes_nothing_but_is_counted(self):
        # "8 pages read, 3 refused" is the honest headline; "5 pages read" hides the refusals
        p = cr.proposal_from_pages(self._pages(
            {"ledger": "uniques", "found": ["Windforce"], "note": "no-found-state"},
            {"ledger": "uniques", "found": ["Stormshield"]},
        ))
        self.assertNotIn("Windforce", p["uniques"])
        self.assertEqual(p["pagesRead"], 1)
        self.assertEqual(len(p["refused"]), 1)
        self.assertEqual(p["refused"][0]["why"], "no-found-state")

    def test_sets_keep_their_grouping(self):
        p = cr.proposal_from_pages([{"reel": "s1", "frame": "f.jpg", "kind": "chronicle-sets", "resp": {
            "ledger": "sets", "found": ["Tal Rasha's Howling Wind"],
            "sets": [{"set": "Tal Rasha's Wrappings", "pieces": ["Tal Rasha's Howling Wind"]}]}}])
        self.assertIn("Tal Rasha's Wrappings", p["setGroups"])
        self.assertIn("Tal Rasha's Howling Wind", p["sets"])


class TestTwoLanes(unittest.TestCase):
    """v1514 — Konyo: "grok for me specifically i can use as a second pair of eyes and a different
    view for also these exact things! it must be also coded in so it is identically trying to read
    and retro chronicle these tallied in."

    Claude is primary; Grok is independent. The value is in the DISAGREEMENT being visible."""

    def claude(self, *found, **kw):
        return lambda p, k: dict({"ledger": "uniques", "found": list(found), "conf": 0.9}, **kw)

    def test_both_lanes_agreeing_reaches_the_gate_as_TWO_witnesses(self):
        # ★ the strongest signal in the system — folding the lanes into one row would discard it
        r = cr.two_lane_read("f.jpg", "chronicle-uniques",
                             self.claude("Windforce"), self.claude("Windforce"))
        self.assertEqual(r["lanes"]["Windforce"], ["claude", "grok"])
        prop = cr.proposal_from_pages([{"reel": "s1", "frame": "f.jpg", "resp": r}])
        self.assertIn("cross-lane", cr.gate_verdict("Windforce", prop["uniques"]["Windforce"])["witnesses"])

    def test_a_name_only_ONE_lane_saw_is_kept_but_still_needs_another_witness(self):
        r = cr.two_lane_read("f.jpg", "chronicle-uniques",
                             self.claude("Windforce", "Shako"), self.claude("Windforce"))
        self.assertIn("Shako", r["found"])                       # kept — not thrown away
        prop = cr.proposal_from_pages([{"reel": "s1", "frame": "f.jpg", "resp": r}])
        self.assertFalse(cr.gate_verdict("Shako", prop["uniques"]["Shako"])["pass"])   # but not grounded

    def test_the_DISAGREEMENT_is_reported_not_resolved(self):
        # ★ silently taking the bigger number leaves a system that LOOKS corroborated while being
        # exactly as wrong as its most confident lane
        r = cr.two_lane_read("f.jpg", "chronicle-uniques",
                             self.claude("Windforce", "Shako"), self.claude("Windforce", "Stormshield"))
        self.assertEqual(r["laneAgreement"]["both"], ["Windforce"])
        self.assertEqual(r["laneAgreement"]["claudeOnly"], ["Shako"])
        self.assertEqual(r["laneAgreement"]["grokOnly"], ["Stormshield"])
        self.assertIn("1 agreed", r["laneSummary"])

    def test_a_SILENT_grok_is_stated_never_implied(self):
        # "grok didn't run" and "grok agreed" are different facts; the gate must not confuse them
        r = cr.two_lane_read("f.jpg", "chronicle-uniques", self.claude("Windforce"), None)
        self.assertEqual(r["lanesRan"], ["claude"])
        self.assertEqual(r["laneNote"], "grok-silent")
        self.assertEqual(r["lanes"]["Windforce"], ["claude"])

    def test_a_grok_that_THROWS_never_breaks_the_read(self):
        def boom(p, k):
            raise RuntimeError("grok CLI died")
        r = cr.two_lane_read("f.jpg", "chronicle-uniques", self.claude("Windforce"), boom)
        self.assertEqual(r["found"], ["Windforce"])
        self.assertEqual(r["lanesRan"], ["claude"])

    def test_CLAUDE_IS_PRIMARY_a_refusal_ends_the_page(self):
        # if the primary lane refused the page, there is no page for a second opinion to be about
        called = []
        r = cr.two_lane_read("f.jpg", "chronicle-uniques",
                             self.claude("Windforce", note="no-found-state"),
                             lambda p, k: called.append(p) or {"found": ["Windforce"]})
        self.assertEqual(called, [], "grok must not be paid to second-guess a refusal")
        self.assertEqual(r["note"], "no-found-state")

    def test_the_reader_binds_into_the_sweep_seam(self):
        rp = cr.two_lane_reader(self.claude("Windforce"), self.claude("Windforce"))
        self.assertEqual(rp("f.jpg", "chronicle-uniques")["lanes"]["Windforce"], ["claude", "grok"])


class TestSweepEveryReel(unittest.TestCase):
    """v1515 — the whole hist directory in one pass.

    This is the shape Konyo actually asked for: "i want to save time manually trying to update and
    screenshot or manually tally each one" — everything at once, not a reel at a time.
    """

    def setUp(self):
        self.d = tempfile.mkdtemp()
        for i, sid in enumerate(("s_100", "s_200", "s_300")):
            rd = os.path.join(self.d, "reel_" + sid)
            os.makedirs(rd)
            with open(os.path.join(rd, "index.json"), "w", encoding="utf-8") as fh:
                json.dump({"sessionId": sid,
                           "frames": [{"f": "f%d.jpg" % k, "ts": k} for k in range(6)]}, fh)
        os.makedirs(os.path.join(self.d, "reel_broken"))     # no index.json
        self.sigs = lambda n: sig(30)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_newest_reels_are_swept_FIRST(self):
        # a sweep he interrupts should have covered his most recent play, not his oldest
        got = [os.path.basename(p) for p in cr.reel_dirs(self.d)]
        self.assertEqual(got, ["reel_s_300", "reel_s_200", "reel_s_100"])

    def test_a_reel_with_no_index_is_skipped_not_crashed_on(self):
        self.assertNotIn("reel_broken", [os.path.basename(p) for p in cr.reel_dirs(self.d)])

    def test_every_reel_folds_into_ONE_proposal(self):
        res = cr.sweep_hist(self.d, lambda p: "chronicle-uniques",
                            lambda p, k: {"ledger": "uniques", "found": ["Windforce"], "conf": 0.9},
                            sig_of=self.sigs)
        self.assertEqual(res["totals"]["reels"], 3)
        self.assertIn("Windforce", res["proposal"]["uniques"])
        # ★ seen in three separate SESSIONS — that is cross-reel corroboration, and it should pass
        self.assertTrue(cr.gate_verdict("Windforce", res["proposal"]["uniques"]["Windforce"])["pass"])

    def test_the_totals_let_him_CHECK_the_cost_claim_himself(self):
        res = cr.sweep_hist(self.d, lambda p: None, lambda p, k: {}, sig_of=self.sigs)
        self.assertEqual(res["totals"]["framesSeen"], 18)   # 3 reels × 6 frames
        self.assertEqual(res["totals"]["classified"], 3)    # 1 still run each
        self.assertEqual(res["totals"]["pagesRead"], 0)

    def test_progress_is_reported_per_reel(self):
        # a silent ten-minute sweep is one he kills halfway and never trusts again
        seen = []
        cr.sweep_hist(self.d, lambda p: None, lambda p, k: {}, sig_of=self.sigs,
                      on_reel=lambda st: seen.append(st["reel"]))
        self.assertEqual(len(seen), 3)

    def test_an_ALREADY_SWEPT_reel_is_not_paid_for_twice(self):
        # ★ v1524 — a sealed reel never changes, so re-reading one buys nothing and costs everything
        calls = []
        res = cr.sweep_hist(self.d, lambda p: calls.append(p) or None, lambda p, k: {},
                            sig_of=self.sigs, skip_reels={"reel_s_100", "reel_s_200"})
        self.assertEqual(len(calls), 1, "only the unswept reel should cost a classify")
        self.assertEqual(res["totals"]["skippedReels"], 2)

    def test_a_skipped_reel_is_REPORTED_not_silently_omitted(self):
        # "12 reels · 9 already swept" is honest; showing 3 makes his footage look thinner than it is
        res = cr.sweep_hist(self.d, lambda p: None, lambda p, k: {}, sig_of=self.sigs,
                            skip_reels={"reel_s_100"})
        self.assertEqual(len(res["reels"]), 3)
        notes = [r.get("note") for r in res["reels"]]
        # v2099 — PIN THE LAW, NOT THE WORD. This asserted the literal "already-swept", which v2098
        # narrowed to mean what it says: a reel the sweep MEMORY records. A reel skipped for any
        # other reason (the caller targeted a different one) now reports "not targeted this run".
        # The law here is v1524's and it is unchanged — a skipped reel must still be REPORTED, or
        # his footage looks thinner than it is. Assert that, and that the note SAYS SOMETHING.
        skipped = [r for r in res["reels"] if r.get("note")]
        self.assertEqual(len(skipped), 1, "the skipped reel vanished from the report: %s" % notes)
        self.assertTrue(str(skipped[0]["note"]).strip(),
                        "a skipped reel was reported with an empty reason")

    def test_progress_still_fires_for_a_skipped_reel(self):
        # otherwise a mostly-cached sweep looks stalled
        seen = []
        cr.sweep_hist(self.d, lambda p: None, lambda p, k: {}, sig_of=self.sigs,
                      skip_reels={"reel_s_100", "reel_s_200", "reel_s_300"},
                      on_reel=lambda st: seen.append(st["reel"]))
        self.assertEqual(len(seen), 3)

    def test_limit_takes_the_NEWEST_n(self):
        res = cr.sweep_hist(self.d, lambda p: None, lambda p, k: {}, limit=1, sig_of=self.sigs)
        self.assertEqual([r["reel"] for r in res["reels"]], ["s_300"])


class TestMergeLaw(unittest.TestCase):
    def test_merge_is_union_and_reports_only_the_gain(self):
        m = cr.merge_max(["Shako", "Windforce"], ["Windforce", "Stormshield"])
        self.assertEqual(m["merged"], ["Shako", "Stormshield", "Windforce"])
        self.assertEqual(m["added"], ["Stormshield"])
        self.assertEqual(m["already"], ["Windforce"])

    def test_a_sweep_can_never_UNFIND_anything(self):
        # a reel from March cannot un-find what was found in July, and a page that scrolled past a
        # row is not evidence the row is empty. There is no "unfind" in Diablo.
        m = cr.merge_max(["Shako", "Windforce", "Stormshield"], ["Shako"])
        self.assertEqual(m["merged"], ["Shako", "Stormshield", "Windforce"])
        self.assertEqual(m["added"], [])

    def test_notFound_is_carried_for_audit_and_subtracts_from_nothing(self):
        p = cr.proposal_from_pages([{"reel": "s1", "frame": "f.jpg", "kind": "chronicle-uniques",
                                     "resp": {"ledger": "uniques", "found": ["Shako"],
                                              "notFound": ["Windforce"]}}])
        self.assertEqual(p["notFound"]["uniques"], ["Windforce"])
        m = cr.merge_max(["Windforce"], list(p["uniques"]))
        self.assertIn("Windforce", m["merged"])   # ★ still found


class TestTheGate(unittest.TestCase):
    """v1513 — Konyo's multi-witness doctrine, as the rule that decides what touches his grail.

    The word doing the work is INDEPENDENT. Reading the same frame twice is not two witnesses, and
    one reader being confident twice is not two either."""

    def s(self, **kw):
        base = {"reel": "s1", "frame": "f1.jpg", "witness": "none", "conf": 0.9, "lane": "claude"}
        base.update(kw)
        return base

    def test_one_sighting_however_confident_is_NOT_enough(self):
        # ★ the doctrine in one test: confidence is not corroboration
        v = cr.gate_verdict("Windforce", [self.s(conf=0.99)])
        self.assertFalse(v["pass"])
        self.assertIn("independent witness", v["why"])

    def test_the_same_frame_read_twice_is_still_one_witness(self):
        # a repeated read of one frame shares every failure mode the first read had
        v = cr.gate_verdict("Windforce", [self.s(), self.s()])
        self.assertEqual(v["witnesses"], [])
        self.assertFalse(v["pass"])

    def test_ONE_sighting_in_each_of_two_reels_is_not_ALSO_cross_frame(self):
        # ★ v1519 — the same repetition must not be banked twice. Counting (reel, frame) pairs
        # globally let one sighting per session score cross-reel AND cross-frame, which is two
        # witnesses' worth of credit for one piece of evidence — enough to clear a two-witness gate
        # on its own. Independence has to be independent of itself.
        v = cr.gate_verdict("Windforce", [self.s(reel="s1", frame="a.jpg"),
                                          self.s(reel="s2", frame="b.jpg")])
        self.assertIn("cross-reel", v["witnesses"])
        self.assertNotIn("cross-frame", v["witnesses"])

    def test_TWO_sessions_alone_do_not_ground_a_name_but_THREE_do(self):
        # ★ two reads of one panel can share a systematic misread — same model, same font, same row —
        # even when the sessions are months apart. Three makes that much harder, so repetition alone
        # grounds a name only at three. Below that it is HELD, with the reason, for him to approve.
        two = cr.gate_verdict("Windforce", [self.s(reel="s1", frame="a.jpg"),
                                            self.s(reel="s2", frame="b.jpg")])
        self.assertFalse(two["pass"])
        three = cr.gate_verdict("Windforce", [self.s(reel="s1", frame="a.jpg"),
                                              self.s(reel="s2", frame="b.jpg"),
                                              self.s(reel="s3", frame="c.jpg")])
        self.assertTrue(three["pass"])
        self.assertIn("cross-reel-3+", three["witnesses"])

    def test_two_frames_inside_ONE_reel_is_cross_frame(self):
        v = cr.gate_verdict("Windforce", [self.s(reel="s1", frame="a.jpg"),
                                          self.s(reel="s1", frame="b.jpg")])
        self.assertIn("cross-frame", v["witnesses"])

    def test_two_frames_plus_the_panels_own_numbers_passes(self):
        v = cr.gate_verdict("Windforce", [
            self.s(frame="f1.jpg", witness="agree"),
            self.s(frame="f2.jpg"),
        ])
        self.assertEqual(v["witnesses"], ["cross-frame", "printed"])
        self.assertTrue(v["pass"])

    def test_two_INDEPENDENT_READERS_is_the_strongest_witness(self):
        # the lanes share no prompt, no model and no failure mode
        v = cr.gate_verdict("Windforce", [self.s(lane="claude"), self.s(lane="grok")])
        self.assertIn("cross-lane", v["witnesses"])

    def test_the_same_name_in_two_different_SESSIONS_counts(self):
        v = cr.gate_verdict("Windforce", [self.s(reel="s1", frame="a.jpg"),
                                          self.s(reel="s2", frame="b.jpg")])
        self.assertIn("cross-reel", v["witnesses"])

    def test_an_unsure_read_is_refused_before_witnesses_are_even_counted(self):
        # ★ unsure twice is still unsure — corroborating a guess with another guess is not evidence
        v = cr.gate_verdict("Windforce", [
            self.s(frame="a.jpg", conf=0.2, witness="agree"),
            self.s(frame="b.jpg", conf=0.3, lane="grok"),
        ])
        self.assertFalse(v["pass"])
        self.assertIn("unsure", v["why"])

    def test_every_verdict_EXPLAINS_itself_pass_or_fail(self):
        # when he asks why his grail did not move, the answer must be a sentence
        for sightings in ([], [self.s()], [self.s(frame="a.jpg"), self.s(frame="b.jpg", lane="grok")]):
            v = cr.gate_verdict("X", sightings)
            self.assertTrue(v["why"] and len(v["why"]) > 10, "a bare boolean is not an answer")

    def test_the_gate_keeps_its_reasoning_for_the_caller(self):
        g = cr.strict_gate()
        g("Windforce", [self.s()])
        self.assertIn("Windforce", g.verdicts)
        self.assertFalse(g.verdicts["Windforce"]["pass"])


class TestApplyIsSeparateAndGated(unittest.TestCase):
    def setUp(self):
        self.prop = cr.proposal_from_pages([{
            "reel": "s1", "frame": "f.jpg", "kind": "chronicle-uniques",
            "resp": {"ledger": "uniques", "found": ["Windforce", "Shako"], "witness": "agree"}}])

    def test_NO_GATE_MEANS_NOTHING_APPLIES(self):
        # an absent gate is "no policy stated" — applying a whole grail because nobody specified a
        # rule is precisely the failure this arc exists to avoid
        out = cr.apply_proposal(self.prop, {"uniques": []})
        self.assertEqual(out["uniques"]["added"], [])
        self.assertEqual(len(out["held"]), 2)

    def test_held_names_carry_their_evidence_so_a_refusal_is_reviewable(self):
        out = cr.apply_proposal(self.prop, {"uniques": []})
        h = out["held"][0]
        self.assertIn("sightings", h)
        self.assertEqual(h["sightings"][0]["frame"], "f.jpg")

    def test_a_gate_that_passes_lets_the_merge_law_do_the_rest(self):
        out = cr.apply_proposal(self.prop, {"uniques": ["Shako"]},
                                gate=lambda n, s: any(x["witness"] == "agree" for x in s))
        self.assertEqual(out["uniques"]["added"], ["Windforce"])   # Shako already had it
        self.assertEqual(out["uniques"]["merged"], ["Shako", "Windforce"])
        self.assertEqual(out["held"], [])

    def test_the_real_gate_applies_only_the_corroborated_name(self):
        # end to end: two names, one corroborated across frames+printed, one seen once
        prop = cr.proposal_from_pages([
            {"reel": "s1", "frame": "a.jpg", "kind": "chronicle-uniques", "resp": {
                "ledger": "uniques", "found": ["Windforce", "Shako"], "witness": "agree", "conf": 0.9}},
            {"reel": "s1", "frame": "b.jpg", "kind": "chronicle-uniques", "resp": {
                "ledger": "uniques", "found": ["Windforce"], "conf": 0.9}},
        ])
        g = cr.strict_gate()
        out = cr.apply_proposal(prop, {"uniques": []}, gate=g)
        self.assertEqual(out["uniques"]["added"], ["Windforce"])
        self.assertEqual([h["name"] for h in out["held"]], ["Shako"])
        self.assertIn("independent witness", g.verdicts["Shako"]["why"])

    def test_sweeping_writes_nothing_anywhere(self):
        # ★ READ-ONLY UNTIL APPLY, proven structurally: the module has no write/open-for-write path
        src = open(os.path.join(os.path.dirname(cr.__file__), "chronicle_retro.py"),
                   encoding="utf-8").read()
        # no write-mode open, no delete, no rename — the module can only ever READ
        self.assertNotRegex(src, r'open\([^)]*["\'][wax]')
        for forbidden in ("os.remove", "os.rename", "os.unlink", "shutil.", "json.dump("):
            self.assertNotIn(forbidden, src, forbidden + " has no business in a read-only sweep")



class TestSweepVerdict(unittest.TestCase):
    """v1541 — WHY AN EMPTY SWEEP IS EMPTY.

    Konyo ran the sweep on his Windows PC and reported it "didn't work properly". It may well have
    worked perfectly: a sweep over footage with no Chronicle in it correctly proposes nothing, and
    renders exactly like a broken one. There is more than one way to find nothing and they need
    different things done about them — only ONE of them is the reader's fault, and sending him to
    debug a prompt for any of the others wastes his evening on a machine that is working.
    """

    def v(self, **kw):
        t = {"reels": 1, "skippedReels": 0, "candidates": 5, "classified": 5,
             "pagesRead": 1, "uniques": 0, "sets": 0}
        t.update(kw)
        return cr.sweep_verdict(t)

    def test_names_found_is_not_a_complaint(self):
        v = self.v(uniques=7, pagesRead=3)
        self.assertEqual(v["state"], "found")
        self.assertTrue(v["ok"])

    def test_no_footage_at_all(self):
        self.assertEqual(self.v(reels=0, candidates=0, pagesRead=0)["state"], "no-footage")

    def test_everything_already_swept_is_the_memory_working(self):
        v = self.v(reels=4, skippedReels=4, candidates=0, pagesRead=0)
        self.assertEqual(v["state"], "all-swept")
        self.assertTrue(v["ok"], "a working cache must never read as a fault")

    def test_nothing_held_still_long_enough(self):
        self.assertEqual(self.v(candidates=0, pagesRead=0)["state"], "no-stills")

    def test_KONYO_CASE_screens_examined_but_no_chronicle_among_them(self):
        # his four Mac reels: 394 frames, 11 still screens, every one a lobby / stash / blank window
        v = self.v(reels=4, candidates=11, classified=11, pagesRead=0)
        self.assertEqual(v["state"], "no-chronicle")
        self.assertTrue(v["ok"], "footage without a Chronicle in it is not a reader failure")
        self.assertIn("NONE was a Chronicle", v["say"])
        self.assertIn("not a reader failure", v["say"])
        self.assertTrue(v["do"], "it must say what to DO, not just what happened")
        self.assertIn("Chronicle", v["do"])

    def test_the_ONE_case_that_really_is_the_reader(self):
        v = self.v(pagesRead=2, uniques=0, sets=0)
        self.assertEqual(v["state"], "read-nothing")
        self.assertFalse(v["ok"], "pages read that yield nothing IS the reader, and only this one is")

    def test_classified_counts_ATTEMPTS_not_chronicles(self):
        """read_reel() increments `classified` BEFORE it asks the classifier, so it counts calls.
        Reading it as "screens that came back Chronicle" put the no-chronicle case in the wrong
        branch and told him to hold the panel steadier when the panel was never opened."""
        no_chron = self.v(reels=4, candidates=11, classified=11, pagesRead=0)
        self.assertEqual(no_chron["state"], "no-chronicle")
        self.assertNotIn("hold it still", no_chron["say"])

    def test_every_verdict_says_something_and_stays_short(self):
        for kw in ({"uniques": 3}, {"reels": 0, "candidates": 0, "pagesRead": 0},
                   {"reels": 2, "skippedReels": 2, "candidates": 0, "pagesRead": 0},
                   {"candidates": 0, "pagesRead": 0}, {"candidates": 9, "pagesRead": 0},
                   {"pagesRead": 2}):
            v = self.v(**kw)
            self.assertTrue(v.get("say"), "every outcome needs a sentence")
            self.assertLess(len(v["say"]), 260)
            self.assertIn("state", v)
            self.assertIn("ok", v)

    def test_sweep_hist_carries_the_verdict(self):
        """The engine must hand it to the caller — a verdict the UI cannot reach is a comment."""
        with tempfile.TemporaryDirectory() as d:
            res = cr.sweep_hist(d, classify=lambda p: None, read_page=lambda p, k: {})
            self.assertIn("verdict", res)
            self.assertEqual(res["verdict"]["state"], "no-footage")
            self.assertIn("candidates", res["totals"], "the verdict's inputs travel with it")



class TestBlankCaptures(unittest.TestCase):
    """v1543 — DO NOT PAY TO CLASSIFY A PHOTOGRAPH OF NOTHING.

    Three of the eleven still screens in Konyo's reels are blank captures: a white window, a black
    one, and a black one with a title bar. The sweep paid a classify for each and the reader
    dutifully answered "not a chronicle" about a picture of nothing.

    Measured on that footage: the dead frames sit at 95.0% and 99.4% single-tone, and the busiest
    legitimately-dark real frame — the D2R title screen — at 82.7%. The threshold has room on both
    sides, and the numbers are in the source so the next person can re-derive them.
    """

    def _png(self, dirpath, name, shade):
        from PIL import Image
        p = os.path.join(dirpath, name)
        Image.new("L", (120, 90), shade).save(p)
        return p

    def _busy(self, dirpath, name):
        from PIL import Image
        import random
        im = Image.new("L", (120, 90))
        rnd = random.Random(7)
        im.putdata([rnd.randrange(256) for _ in range(120 * 90)])
        p = os.path.join(dirpath, name)
        im.save(p)
        return p

    def test_a_flat_white_or_black_frame_is_dead(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(cr.is_dead_frame(self._png(d, "w.png", 255)))
            self.assertTrue(cr.is_dead_frame(self._png(d, "b.png", 0)))
            self.assertTrue(cr.is_dead_frame(self._png(d, "g.png", 128)))

    def test_a_frame_with_a_screen_on_it_is_not(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(cr.is_dead_frame(self._busy(d, "busy.png")))

    def test_an_unmeasurable_frame_is_READ_not_skipped(self):
        """"I could not look" must never be spent as "nothing there". Skipping what we could not
        judge is exactly how a real Chronicle page would go missing."""
        self.assertFalse(cr.is_dead_frame("/nope/does/not/exist.jpg"))
        self.assertIsNone(cr.frame_flatness("/nope/does/not/exist.jpg"))

    def test_live_probe_prefers_the_middle_frame(self):
        with tempfile.TemporaryDirectory() as d:
            names = [os.path.basename(self._busy(d, "f%d.png" % i)) for i in range(5)]
            got, dead = cr.live_probe(names, lambda n: os.path.join(d, n))
            self.assertEqual(got, names[2], "the middle frame is the most settled one")
            self.assertEqual(dead, 0)

    def test_a_blank_middle_does_not_condemn_the_whole_run(self):
        """A window that blanked for a moment mid-visit is exactly when the rest of the run is
        still a real screen — so it steps outward rather than giving up."""
        with tempfile.TemporaryDirectory() as d:
            names = []
            for i in range(5):
                names.append(os.path.basename(
                    self._png(d, "f%d.png" % i, 0) if i == 2 else self._busy(d, "f%d.png" % i)))
            got, dead = cr.live_probe(names, lambda n: os.path.join(d, n))
            self.assertIsNotNone(got)
            self.assertNotEqual(got, names[2])
            self.assertEqual(dead, 1, "it reports the blank it stepped over")

    def test_an_all_blank_run_is_refused_and_COUNTED(self):
        with tempfile.TemporaryDirectory() as d:
            names = [os.path.basename(self._png(d, "f%d.png" % i, 255)) for i in range(4)]
            got, dead = cr.live_probe(names, lambda n: os.path.join(d, n))
            self.assertIsNone(got, "there is nothing in this run worth paying for")
            self.assertEqual(dead, 4)

    def test_the_verdict_names_blank_captures_rather_than_hiding_the_saving(self):
        """A silent skip would turn a capture fault into a smaller invoice and nothing else. He needs
        to know the difference between 'your Chronicle was not on camera' and 'your camera was off'."""
        t = {"reels": 3, "skippedReels": 0, "candidates": 8, "classified": 5,
             "blankRuns": 3, "pagesRead": 0, "uniques": 0, "sets": 0}
        v = cr.sweep_verdict(t)
        self.assertEqual(v["state"], "no-chronicle")
        self.assertIn("BLANK CAPTURES", v["say"])
        self.assertIn("3 run(s)", v["say"])

    def test_no_blanks_means_no_noise_about_blanks(self):
        t = {"reels": 3, "skippedReels": 0, "candidates": 8, "classified": 8,
             "blankRuns": 0, "pagesRead": 0, "uniques": 0, "sets": 0}
        self.assertNotIn("BLANK", cr.sweep_verdict(t)["say"])

    def test_blankRuns_reaches_the_totals(self):
        with tempfile.TemporaryDirectory() as d:
            res = cr.sweep_hist(d, classify=lambda p: None, read_page=lambda p, k: {})
            self.assertIn("blankRuns", res["totals"], "a count the UI cannot reach is a comment")



class TestBlankMarkedAtSeal(unittest.TestCase):
    """v1545 — the seal marks blank captures, and grouping skips them.

    16 of the 17 blanks in his worst reel land in the first NINETEEN SECONDS — capture starts while
    D2R is launching, so the window exists and is blank until the title paints. v1543 stopped paying
    for them; this stops them costing anything at all, and says so at the moment they are created.
    """

    def test_a_blank_marked_frame_is_skipped_by_grouping(self):
        frames = [{"f": "a", "ts": 1}, {"f": "b", "ts": 2, "blank": True}, {"f": "c", "ts": 3}]
        sigs = {"a": b"\x01" * 16, "b": b"\xff" * 16, "c": b"\x01" * 16}
        runs = cr.still_runs(frames, lambda n: sigs[n])
        self.assertEqual(len(runs), 1, "a one-frame flicker must not split a visit into two runs")
        self.assertEqual(runs[0]["frames"], ["a", "c"])

    def test_a_blank_frame_is_NOT_treated_as_unreadable(self):
        """An unreadable frame BREAKS the run — we cannot tell what it was, so welding across it
        would be a guess. A blank one is different: we know it carried no screen."""
        sigs = {"a": b"\x01" * 16, "b": None, "c": b"\x01" * 16}
        runs = cr.still_runs([{"f": "a"}, {"f": "b"}, {"f": "c"}], lambda n: sigs[n])
        self.assertEqual(len(runs), 2, "an UNREADABLE frame must still break the run")

    def test_an_unmarked_index_still_works(self):
        """Reels sealed before v1545 carry no `blank` key at all. They must group exactly as before —
        v1543's live_probe is what protects those."""
        frames = [{"f": "a"}, {"f": "b"}, {"f": "c"}]
        sigs = {"a": b"\x01" * 16, "b": b"\x01" * 16, "c": b"\x01" * 16}
        runs = cr.still_runs(frames, lambda n: sigs[n])
        self.assertEqual(len(runs), 1)
        self.assertEqual(len(runs[0]["frames"]), 3)

    def test_marking_never_removes_the_footage(self):
        """The mark is a flag on the index row, not a deletion. That footage is real, the SIM replays
        it, and discarding evidence to tidy a count is the wrong trade."""
        frames = [{"f": "a", "blank": True}, {"f": "b"}]
        self.assertIn("f", frames[0], "the frame is still named in the index")
        runs = cr.still_runs(frames, lambda n: b"\x01" * 16)
        self.assertEqual(runs[0]["frames"], ["b"])



# v1601 — REAL, DECODABLE FRAMES. The fixture below used to write four magic bytes and 64 zeros as
# a ".jpg". Pillow cannot decode that, so jpeg_sig() returned None for every frame; still_runs()
# treats an unreadable frame as a run BREAK (deliberately — one unreadable frame must never weld two
# screens into one run), so no run ever reached MIN_RUN_FRAMES and the classifier was never called
# even once. `classified` was 0, which is why "the throwing probe" never threw.
#
# The frames must therefore be (a) decodable and (b) NOT blank — live_probe() skips a run that is
# dead all the way through, which would silence the classifier a second way. Identical frames per
# reel is the point: four identical frames are ONE held screen, which is exactly one classify.
try:
    from PIL import Image as _PILImage
except Exception:                                   # pragma: no cover
    _PILImage = None


def _write_frame(path):
    """One small, decodable, visibly-non-blank JPEG."""
    im = _PILImage.new("RGB", (48, 48))
    px = im.load()
    for y in range(48):
        for x in range(48):
            px[x, y] = ((x * 5) % 256, (y * 7) % 256, ((x + y) * 3) % 256)
    im.save(path, "JPEG", quality=90)


@unittest.skipIf(_PILImage is None, "Pillow absent — the sweep cannot group frames without it")
class TestV1577ClassifyIsolation(unittest.TestCase):
    """v1577 — a sweep must survive ONE bad frame, and production must actually use the thing that
    makes it survive.

    read_reel() calls classify() bare and sweep_hist() calls read_reel() bare, so an exception raised
    while probing a single frame propagated all the way out and abandoned every reel after it. The
    probe is a MODEL CALL over the network, so "it threw once" is not exotic — it is Tuesday.

    cr.classifier() was written to isolate exactly that, was covered by its own tests, and had no
    production caller at all: control_app had re-implemented it inline WITHOUT the try. That is the
    v1576 defect class (plumbing with no tap) in its most expensive form — the dead code was the
    SAFE version, and the live code was the unsafe copy.
    """

    def _reels(self, root, n=3, frames=4):
        """A minimal hist dir: n reels, each with an index.json in the REAL reel shape.

        v1601 — THIS FIXTURE WAS WRONG FROM THE DAY IT WAS WRITTEN, and it took both tests in this
        class down with it. It wrote `frames` as a list of bare STRINGS, but a sealed reel's
        index.json holds ROWS — `{"f": "f_1784984130673.jpg", "ts": 1784984130673}` — which is what
        the agent writes and what every real reel on disk contains. still_runs() reads `fr.get("f")`,
        so both tests died on `AttributeError: 'str' object has no attribute 'get'` INSIDE the
        fixture's own sweep, before reaching the isolation they exist to pin.

        So from v1577 until now, the two tests guarding "one bad frame must not abandon the whole
        sweep" have never once exercised it, and tv/test_chronicle_retro.py has been a red gate
        nobody chased. That is precisely LAW19's clause about proving added tests actually RAN: a
        test that errors in its setup is not a weaker test, it is no test at all.
        """
        for i in range(n):
            d = os.path.join(root, "reel_s_%d_%05d" % (1700000000000 + i, i))
            os.makedirs(d, exist_ok=True)
            rows = []
            for f in range(frames):
                nm = "f%03d.jpg" % f
                _write_frame(os.path.join(d, nm))
                rows.append({"f": nm, "ts": 1700000000000 + i * 10000 + f * 500})
            with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
                json.dump({"sessionId": "s_%05d" % i, "frames": rows}, fh)
        return root

    def test_a_throwing_probe_aborts_the_bare_sweep(self):
        """The bug, pinned. If this ever stops raising, the isolation moved and the test below is
        no longer measuring anything."""
        with tempfile.TemporaryDirectory() as td:
            hist = self._reels(td)
            calls = {"n": 0}

            def flaky(path):
                calls["n"] += 1
                if calls["n"] == 2:
                    raise RuntimeError("transient model failure on one frame")
                return {"scene": "gameplay"}

            with self.assertRaises(RuntimeError):
                cr.sweep_hist(hist, lambda p: cr.chronicle_kind(flaky(p)), lambda p, k: {})

    def test_classifier_keeps_sweeping_past_it(self):
        with tempfile.TemporaryDirectory() as td:
            hist = self._reels(td)
            calls = {"n": 0}

            def flaky(path):
                calls["n"] += 1
                if calls["n"] == 2:
                    raise RuntimeError("transient model failure on one frame")
                return {"scene": "gameplay"}

            res = cr.sweep_hist(hist, cr.classifier(flaky), lambda p, k: {})
            self.assertEqual(len(res["reels"]), 3,
                             "one bad frame must cost ONE run, not every reel after it")
            self.assertGreaterEqual(sum(r.get("classified") or 0 for r in res["reels"]), 3)

    def test_the_console_retro_sweep_actually_goes_through_classifier(self):
        """The isolation is worth nothing if production keeps its own unguarded copy — which is
        precisely what happened between v1527 and v1577."""
        import control_app as ca
        src = open(ca.__file__, encoding="utf-8").read()
        self.assertIn("_cr.classifier(", src,
                      "the retro sweep must build its classify through cr.classifier()")
        self.assertNotIn("return _cr.chronicle_kind(_tv.claude_read(path))", src,
                         "the unguarded inline classify is back — one bad frame will abandon the sweep")


@unittest.skipIf(_PILImage is None, "Pillow absent — the sweep cannot group frames without it")
class TestV1689CostPassMeasuresNothing(unittest.TestCase):
    """v1689 — A STUB READER MAY REPORT COST. IT MAY NOT REPORT WHAT THE FOOTAGE CONTAINS.

    `--cost` installs a classify that always returns None and a read_page that returns {}, so
    pagesRead is 0 BY CONSTRUCTION and sweep_verdict() always landed on `no-chronicle`: "…NONE was a
    Chronicle page — so there was nothing to read. This is not a reader failure." It printed exactly
    that over a reel that provably holds 8 Chronicle pages. The sentence outlived what it described,
    and no test asserted on a word — which is how it survived four ships.
    """

    def _reel(self, root, n_frames=5):
        d = os.path.join(root, "reel_s_1786385768689_67392")
        os.makedirs(d, exist_ok=True)
        rows = []
        for f in range(n_frames):
            nm = "f%03d.jpg" % f
            _write_frame(os.path.join(d, nm))       # identical frames ⇒ ONE still run ⇒ 1 candidate
            rows.append({"f": nm, "ts": 1786385768689 + f * 500})
        with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"sessionId": "s_1786385768689_67392", "frames": rows}, fh)
        return root

    def _cost_run(self, hist):
        import subprocess
        return subprocess.run([sys.executable, cr.__file__, "--cost", "--hist", hist],
                              cwd=os.path.dirname(os.path.abspath(cr.__file__)),
                              capture_output=True, text=True, timeout=120)

    def test_the_cost_pass_has_candidates_to_be_wrong_about(self):
        """NON-VACUOUS FIRST: if the fixture produced 0 candidates the verdict below would be
        `no-stills` and the real defect would go unmeasured."""
        with tempfile.TemporaryDirectory() as td:
            out = self._cost_run(self._reel(td))
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("1 runs", out.stdout, "the fixture must group into a candidate run")

    def test_cost_does_NOT_claim_the_footage_holds_no_chronicle(self):
        with tempfile.TemporaryDirectory() as td:
            out = self._cost_run(self._reel(td))
            self.assertNotIn("NONE was a Chronicle", out.stdout,
                             "a stub reader read nothing — it cannot say what the frames were")
            self.assertNotIn("not a reader failure", out.stdout,
                             "no reader ran, so there is no reader verdict to give")

    def test_cost_says_plainly_that_nothing_was_read(self):
        with tempfile.TemporaryDirectory() as td:
            out = self._cost_run(self._reel(td))
            self.assertIn("No reader ran", out.stdout)
            self.assertIn("prices frames", out.stdout)

    def test_the_not_measured_verdict_is_its_own_state(self):
        v = cr.sweep_verdict({"reels": 1, "candidates": 11, "classified": 11, "pagesRead": 0,
                              "uniques": 0, "sets": 0}, priced_only=True)
        self.assertEqual(v["state"], "not-measured")
        self.assertTrue(v["ok"], "pricing a pass is not a fault")
        self.assertLess(len(v["say"]), 260)
        self.assertNotIn("NONE was a Chronicle", v["say"])
        self.assertTrue(v.get("do"))

    def test_every_genuine_verdict_is_byte_identical(self):
        """★ THE BLAST RADIUS. A real sweep's verdicts must not move by one character."""
        for kw in ({"uniques": 3}, {"reels": 0, "candidates": 0, "pagesRead": 0},
                   {"reels": 2, "skippedReels": 2, "candidates": 0, "pagesRead": 0},
                   {"candidates": 0, "pagesRead": 0}, {"candidates": 9, "pagesRead": 0},
                   {"pagesRead": 2}):
            t = {"reels": 1, "skippedReels": 0, "candidates": 5, "classified": 5,
                 "pagesRead": 1, "uniques": 0, "sets": 0}
            t.update(kw)
            self.assertEqual(cr.sweep_verdict(t), cr.sweep_verdict(t, priced_only=False))


class TestV1770ASlowScrollIsNotWalkingThroughTown(unittest.TestCase):
    """v1770 — MIN_RUN_FRAMES=3 DISCARDED MOST OF A DELIBERATE SCROLL.

    The floor exists so a sweep does not pay to classify somebody walking through town, and for that
    job 3 frames is right. It is the wrong judge of a Chronicle read: Konyo went through the list
    slowly, and each page still only held for a frame or two before he moved on.

    MEASURED ON HIS 08-17 REEL: 339 frames group into 55 distinct screens, and min_frames=3 keeps 24.
    THIRTY-ONE SCREENS — 56% of what he filmed — were dropped before anything looked at them, which
    at ~6 found rows per screen is roughly 180 item rows the sweep never read. That is why his tally
    sat ~9 short of the game's own 64% however often he re-swept, and why he said "i literally did it
    slow and went through the uniques and scrolled slowly".

    v1689 found this defect from the other side and rescued journal-marked frames. That fix was real
    and starved: it can only rescue frames the journal marked, and the journal had marked 13.

    THE DISCRIMINATOR IS THE REEL ITSELF. Once a run here comes back chronicle-*, the
    walking-through-town rationale cannot apply to this reel — it IS a recording of the Chronicle —
    so the floor drops to 1 for the rest of that reel and nowhere else."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        # a 3-frame HELD page (clears the floor), then 10 single-frame screens: a scroll
        rows = [{"f": "h%d.jpg" % i, "ts": 1000 + i} for i in range(3)]
        rows += [{"f": "s%d.jpg" % i, "ts": 2000 + i * 10} for i in range(8)]
        self.rows = rows
        with open(os.path.join(self.d, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"sessionId": "s_scrolltest", "frames": rows}, fh)
        self.sigs = {"h%d.jpg" % i: sig(250) for i in range(3)}
        # a fake fingerprint is ONE byte, so the whole ladder has to fit in 0-255: 8 rungs of 29
        # (> tol 28, so each is its own screen) is the most the range allows
        for i in range(8):
            self.sigs["s%d.jpg" % i] = sig(i * 29)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def _run(self, kind="chronicle-uniques"):
        self.classified = []

        def classify(path):
            self.classified.append(os.path.basename(path))
            return kind

        def read_page(path, k):
            return {"found": [], "notFound": []}

        return cr.read_reel(self.d, classify, read_page,
                            sig_of=lambda n: self.sigs.get(os.path.basename(n)))

    def test_the_short_screens_are_read_once_the_reel_proves_itself(self):
        r = self._run()
        self.assertEqual(r["runs"], 9, "fixture is not 1 held page + 8 scrolled screens")
        self.assertEqual(r.get("rescuedShortRuns"), 8,
                         "the scrolled screens were discarded: %s" % r.get("rescuedShortRuns"))
        # every screen he filmed is read, not 1 of 9
        self.assertEqual(len(r["pages"]), 9,
                         "only %d of 9 screens were read" % len(r["pages"]))

    def test_a_reel_that_is_NOT_a_chronicle_pays_nothing_extra(self):
        """The floor still does its original job. A reel whose runs come back as anything else must
        not have its short runs swept — that is the walking-through-town bill this constant exists
        to refuse, and the fix must not quietly hand it back."""
        r = self._run(kind=None)
        self.assertEqual(r.get("rescuedShortRuns"), 0,
                         "a non-chronicle reel paid for its short runs anyway")
        self.assertEqual(len(r["pages"]), 0)
        self.assertEqual(len(self.classified), 1,
                         "it classified more than the one candidate: %s" % self.classified)


class TestV1781LimitCountsReelsItCanRead(unittest.TestCase):
    """v1781 — THE WATCHDOG COULD NOT READ ANYTHING ONCE THE NEWEST REEL WAS SWEPT.

    sweep_hist sliced reel_dirs(hist)[:limit] BEFORE testing skip_reels. The reel watchdog passes
    limit=1 on every tick, so as soon as the newest reel was in the swept memory the sweep took that
    one reel, reported "already-swept", and stopped — never reaching the reel it had been asked for.
    Every 20 seconds, for as long as the console ran.

    Demonstrated in isolation before the fix: tick 1 targeted reel_s_2000_newest and read it; tick 2
    targeted reel_s_1000_older and read_reel was called only for reel_s_2000_newest. It also hid
    v1779's fix, which narrows skip_reels to the targeted reel and could not work while the slice
    ran first.

    Skipped reels are still REPORTED — "12 reels · 9 already swept" stays honest — they just do not
    consume the budget."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        for rid, ts in (("reel_s_2000_newest", 2000), ("reel_s_1000_older", 1000)):
            p = os.path.join(self.d, rid)
            os.makedirs(p)
            for i in range(3):
                with open(os.path.join(p, "f%d.jpg" % i), "wb") as fh:
                    fh.write(b"\xff\xd8\xff\xd9")
            with open(os.path.join(p, "index.json"), "w", encoding="utf-8") as fh:
                json.dump({"frames": [{"f": "f%d.jpg" % i, "ts": ts + i} for i in range(3)]}, fh)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def _read(self, skip, limit=1):
        seen = []
        real = cr.read_reel
        cr.read_reel = lambda d, *a, **k: (seen.append(os.path.basename(d)) or
            {"reel": os.path.basename(d), "runs": 0, "candidates": 0, "classified": 0, "pages": []})
        try:
            cr.sweep_hist(self.d, lambda p: None, lambda p, k: {}, limit=limit, skip_reels=skip)
        finally:
            cr.read_reel = real
        return seen

    def test_a_swept_newest_reel_does_not_consume_the_budget(self):
        seen = self._read({"reel_s_2000_newest"})
        self.assertEqual(seen, ["reel_s_1000_older"],
                         "limit=1 was spent walking past a reel it could not read: %s" % seen)

    def test_the_skipped_reel_is_still_REPORTED(self):
        """Honesty is not the thing being traded away: '9 already swept' must still appear, or his
        footage looks thinner than it is (v1524's rule)."""
        res = cr.sweep_hist(self.d, lambda p: None, lambda p, k: {}, limit=1,
                            skip_reels={"reel_s_2000_newest"})
        notes = [st.get("note") for st in res["reels"]]
        # v2099 — same law, not the same word. See the note in TestSweepEveryReel above: v2098 made
        # "already-swept" mean only what the memory records, so a reel skipped because the caller
        # targeted another one says "not targeted this run" instead. What v1524 protects is that it
        # is REPORTED at all.
        self.assertTrue([n for n in notes if n], "the skipped reel vanished from the report: %s" % notes)
        self.assertEqual(res["totals"].get("skippedReels"), 1)


class TestV1776EvidenceOutlivesTheSweep(unittest.TestCase):
    """v1776 — A SWEEP MUST ONLY EVER ADD. Konyo, after watching a five-reel run get wiped by the
    watchdog's own tick: "we need a safegaurd to this.. this cant happen.. like why cant after it
    reads .. it locks it somehow like the progress is going up and then reversing."

    _CHRON_JOB["result"] was ONE slot, so every sweep REPLACED the last one's findings. Two costs,
    and the second is the expensive one:

      1. what a sweep found vanished the moment anything else swept - including the watchdog, which
         is meant to be helping;
      2. sightings could only corroborate INSIDE a single run, so `cross-reel` could not fire unless
         both recordings happened to be in the SAME sweep. Read one reel tonight and another
         tomorrow and the gate sees two lonely single sightings. That is most of why nothing could
         ground without Grok - the witness Claude can supply alone was unreachable by construction.

    The vault path has accumulated since v1533 ("merge-max only"); the chronicle path never did."""

    def test_a_later_sweep_never_erases_an_earlier_one(self):
        # v1836 — the fixture now carries WHICH pages, not just a count. It used to declare
        # pagesRead:4 beside a single sighting, which no real proposal looks like, and the counter
        # is derived from page identity since v1835's checkpointing made a summed count double
        # itself on re-merge. The claim under test is unchanged: two sweeps ADD, never replace.
        first = {"uniques": {"Gore Rider": [{"reel": "A", "frame": "f1", "lane": "claude"}]},
                 "pageKeys": ["A|f1", "A|f2", "A|f3", "A|f4"], "pagesRead": 4}
        second = {"uniques": {"Bonesnap": [{"reel": "B", "frame": "f7", "lane": "claude"}]},
                  "pageKeys": ["B|f5", "B|f6", "B|f7", "B|f8", "B|f9", "B|f10"], "pagesRead": 6}
        m = cr.merge_proposals(first, second)
        self.assertIn("Gore Rider", m["uniques"], "the second sweep wiped the first one's finding")
        self.assertIn("Bonesnap", m["uniques"])
        self.assertEqual(m["pagesRead"], 10, "the page count reversed instead of adding")
        # and merging the same two again must not make it twenty
        again = cr.merge_proposals(m, second)
        self.assertEqual(again["pagesRead"], 10, "the count grew on a re-merge of the same pages")

    def test_cross_reel_can_finally_fire_ACROSS_two_sweeps(self):
        """The whole point. One name, two recordings, read on two different days — that is exactly
        the corroboration his footage can supply without a second model lane."""
        # conf matters: the gate has a confidence FLOOR as well as a witness count, and a fixture
        # without it proves the floor rather than the merge
        tonight = {"uniques": {"Gore Rider": [{"reel": "A", "frame": "f1", "lane": "claude", "conf": 0.9}]}}
        tomorrow = {"uniques": {"Gore Rider": [{"reel": "B", "frame": "f9", "lane": "claude", "conf": 0.9}]}}
        m = cr.merge_proposals(tonight, tomorrow)
        tags = cr.witnesses(m["uniques"]["Gore Rider"])
        self.assertIn("cross-reel", tags,
                      "two recordings of the same name still do not corroborate: %s" % tags)
        # and with a third recording it clears the gate on its own, no Grok anywhere
        third = cr.merge_proposals(m, {"uniques": {"Gore Rider": [
            {"reel": "C", "frame": "f3", "lane": "claude", "conf": 0.9}]}})
        v = cr.gate_verdict("Gore Rider", third["uniques"]["Gore Rider"])
        self.assertTrue(v["pass"],
                        "three recordings by ONE lane still cannot ground a name: %s" % v.get("why"))
        self.assertNotIn("cross-lane", v["witnesses"], "this must not depend on the second eye")

    def test_the_same_photograph_twice_is_still_ONE_sighting(self):
        """v1689's rule survives accumulation: re-reading a frame is not corroboration, and merging
        must not turn a repeated sweep into a fake second witness."""
        a = {"uniques": {"Gore Rider": [{"reel": "A", "frame": "f1", "lane": "claude"}]}}
        m = cr.merge_proposals(a, a)
        self.assertEqual(len(m["uniques"]["Gore Rider"]), 1,
                         "sweeping the same reel twice invented a witness")
        self.assertEqual(cr.witnesses(m["uniques"]["Gore Rider"]), [],
                         "one photograph read twice must carry no witness tag")


class TestV1775ARunIsNotOnePage(unittest.TestCase):
    """v1775 — A SCROLLED RUN MUST YIELD MORE THAN ONE PAGE, or Claude can never corroborate itself.

    _distinct() compared frames at the DEFAULT tol=28, and v1758 had already measured what that does
    to a Chronicle: two COMPLETELY different pages differ by at most one gray level in one of
    jpeg_sig's 256 cells, so nothing clears 28 and every frame in a run looks identical to the first.
    Measured on his 08-17 reel: runs of 43 and 44 distinct scroll positions each yielded ONE page.

    THAT IS WHAT MADE THE SECOND EYE LOOK MANDATORY. The gate takes five witness kinds and only
    cross-lane needs Grok; cross-frame — two frames within ONE reel — is the one Claude supplies
    alone, and it cannot fire when a run is collapsed to a single frame. Konyo: "why is grok a
    mandatory thing? we made it that i can toggle grok for extra pair of eyes."

    v1772 reverted this on evidence that REG-180 later traced to a THROTTLED reader answering empty;
    the same frames read chronicle/uniques with 6 names before the throttle and nothing during it."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        rows = [{"f": "f%d.jpg" % i, "ts": 1000 + i} for i in range(6)]
        with open(os.path.join(self.d, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"sessionId": "s_scroll", "frames": rows}, fh)
        # ONE still-run (they group together), but each frame is its own PAGE — a slow scroll.
        # Steps of 5 are invisible at tol=28 and plain at tol=4, which is the whole defect.
        self.sigs = {"f%d.jpg" % i: sig(100 + i * 5) for i in range(6)}

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_every_page_of_a_scroll_is_read_not_just_the_first(self):
        reads = []
        r = cr.read_reel(self.d, lambda p: "chronicle-uniques",
                         lambda p, k: reads.append(os.path.basename(p)) or {},
                         sig_of=lambda n: self.sigs.get(os.path.basename(n)))
        self.assertEqual(r["runs"], 1, "fixture is not one still-run: %s" % r["runs"])
        self.assertGreater(len(reads), 1,
                           "the whole scrolled run collapsed to %d page(s) — cross-frame can never "
                           "fire, so nothing grounds without a second lane" % len(reads))
        self.assertEqual(len(reads), len(self.sigs),
                         "some pages of the scroll were dropped: %s" % reads)

    def test_a_genuinely_held_page_is_still_read_once(self):
        """The other direction, and the reason the threshold sits mid-gap: a page he simply left on
        screen is ONE page however many frames photographed it. Reading it forty times would be
        money for nothing AND would hand witnesses() forty sightings of one photograph."""
        held = {"f%d.jpg" % i: sig(100) for i in range(6)}
        reads = []
        cr.read_reel(self.d, lambda p: "chronicle-uniques",
                     lambda p, k: reads.append(os.path.basename(p)) or {},
                     sig_of=lambda n: held.get(os.path.basename(n)))
        self.assertEqual(len(reads), 1, "a held page was read %d times" % len(reads))


class TestV1773OneBadProbeMustNotDiscardARun(unittest.TestCase):
    """v1773 — A CONFIDENT WRONG ANSWER IS THE SAME DEFECT v1577 FIXED, IN BETTER CLOTHES.

    classify() runs ONCE per run, on its middle frame, and a "no" throws away every frame behind it.
    Measured on his 08-17 reel with the REAL reader: a frame where his cursor rested on an item — so
    the game painted a large stat tooltip over the list — came back scene='transition', conf 0.85,
    names 0. Two clean frames from the same reel came back chronicle/uniques with 6 names each. The
    panel had not gone anywhere; a popup had covered it, and the run behind that probe was up to 44
    Chronicle pages discarded on one frame's bad luck. That is why his tally would not move.

    v1577 fixed this when the probe THREW. Nothing looked broken here, which is why it lasted.

    THE LIMIT, STATED RATHER THAN HIDDEN: the proof has to come from the same judge, so a reel whose
    ONLY run gets a bad probe is still lost. That is deliberate — "ONE classify per run, not per
    frame" is a real constraint with its own test, and a reel of town must not become expensive to
    rule out. His 08-17 reel has 55 runs and the clean ones classify positive, which is what pays
    for the rest."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        # TWO runs, which is what a real reel looks like: a clean stretch that classifies as a
        # Chronicle, and a second stretch whose middle frame happens to carry his item tooltip.
        rows = [{"f": "a%d.jpg" % i, "ts": 1000 + i} for i in range(4)]
        rows += [{"f": "f%d.jpg" % i, "ts": 2000 + i} for i in range(6)]
        with open(os.path.join(self.d, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"sessionId": "s_probe", "frames": rows}, fh)
        self.sigs = {"a%d.jpg" % i: sig(20) for i in range(4)}
        self.sigs.update({"f%d.jpg" % i: sig(90) for i in range(6)})   # |Δ|=70 > tol ⇒ two runs

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_a_tooltip_on_the_probe_frame_does_not_lose_the_run(self):
        seen = []

        def classify(path):
            n = os.path.basename(path)
            seen.append(n)
            # the second run's middle frame is the one with his cursor on an item
            return None if n == "f3.jpg" else "chronicle-uniques"

        reads = []
        r = cr.read_reel(self.d, classify,
                         lambda p, k: reads.append(os.path.basename(p)) or {},
                         sig_of=lambda n: self.sigs.get(os.path.basename(n)))
        self.assertGreaterEqual(len(seen), 2, "it never asked a second frame: %s" % seen)
        self.assertEqual(r.get("rescuedProbes"), 1,
                         "the run was discarded on one bad probe: %s" % r.get("rescuedProbes"))
        self.assertTrue(reads, "no page was read from a run that IS a Chronicle")

    def test_a_reel_of_gameplay_still_costs_ONE_classify_per_run(self):
        """The bill is the reason this runs last and behind a proof gate. "ONE classify per run, not
        per frame" is a real constraint with its own test, and a reel of town must not become
        expensive to rule out — so a second opinion is only sought once a PAID classify has already
        said chronicle on THIS reel."""
        seen = []

        def classify(path):
            seen.append(os.path.basename(path))
            return None            # nothing here is a Chronicle, and nothing ever proves otherwise

        r = cr.read_reel(self.d, classify, lambda p, k: {},
                         sig_of=lambda n: self.sigs.get(os.path.basename(n)))
        self.assertEqual(len(seen), 2, "it paid for extra probes on a reel of gameplay: %s" % seen)
        self.assertEqual(r.get("rescuedProbes"), 0)


class TestV1689JournalMarkedChronicleFrames(unittest.TestCase):
    """v1689 — READING A CHRONICLE MEANS SCROLLING IT, AND A SCROLL IS NEVER STILL.

    Measured on reel_s_1786385768689_67392: 217 frames → 1 candidate run, and 0 of the 8 frames the
    vision lane had already marked scene='chronicle' were among them (the single candidate sits 30s
    after the scrolling stopped). The still-run selection cannot see the one screen the whole module
    exists to find. The journal already answered the classify stage's question for those frames, so
    they cost ZERO classifies here.
    """

    def setUp(self):
        # 8 consecutive frames, each a full STILL_MAX_DIFF apart — a scrolled list, not a held page
        self.d = tempfile.mkdtemp()
        self.rows = [{"f": "f%d.jpg" % i, "ts": 1786385778600 + i * 1000} for i in range(8)]
        with open(os.path.join(self.d, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"sessionId": "s_1786385768689_67392", "frames": self.rows}, fh)
        self.sigs = {"f%d.jpg" % i: sig(10 + i * 30) for i in range(8)}   # |Δ|=30 > tol 28 ⇒ diff 1.0

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def _sweep(self, **kw):
        return cr.read_reel(self.d, lambda p: "chronicle-uniques", lambda p, k: {"found": ["Windforce"]},
                            sig_of=lambda n: self.sigs.get(n), **kw)

    def test_a_scrolled_chronicle_is_INVISIBLE_to_the_still_selection(self):
        """NON-VACUOUS BASELINE: this is the bug, pinned. 8 real Chronicle frames, 8 runs of one
        frame each, ZERO candidates — nothing is classified and nothing is read."""
        r = self._sweep()
        self.assertEqual(r["runs"], 8)
        self.assertEqual(r["candidates"], 0)
        self.assertEqual(r["pages"], [])

    def test_journal_marked_frames_become_candidates_anyway(self):
        r = self._sweep(known_chronicle={row["f"]: "uniques" for row in self.rows})
        # `candidates` counts RUNS, and 8 consecutive marked frames are ONE visit — 0 → 1
        self.assertEqual(r["candidates"], 1, "the marked visit must become a candidate")
        self.assertEqual(r["journalRuns"], 1)
        self.assertEqual(len(r["pages"]), 8, "a scrolled page is a DIFFERENT page — read each one")

    def test_they_cost_ZERO_classifies(self):
        calls = []
        r = cr.read_reel(self.d, lambda p: calls.append(p) or "chronicle-uniques",
                         lambda p, k: {"found": []}, sig_of=lambda n: self.sigs.get(n),
                         known_chronicle={row["f"]: "uniques" for row in self.rows})
        self.assertEqual(calls, [], "the journal already answered 'is this a Chronicle'")
        self.assertEqual(r["classified"], 0)

    def test_the_tab_the_journal_recorded_is_the_ledger_that_is_read(self):
        r = self._sweep(known_chronicle={row["f"]: {"scene": "chronicle", "chronicleTab": "sets"}
                                         for row in self.rows})
        self.assertTrue(r["pages"])
        self.assertEqual({p["kind"] for p in r["pages"]}, {"chronicle-sets"})

    def test_a_marked_frame_with_no_readable_tab_is_not_guessed(self):
        """chronicle_kind()'s refusal stands: an unreadable tab must not become 'uniques', because a
        wrong guess writes set pieces into his grail. It falls back to a paid classify."""
        calls = []
        cr.read_reel(self.d, lambda p: calls.append(p) or None, lambda p, k: {},
                     sig_of=lambda n: self.sigs.get(n),
                     known_chronicle={row["f"]: "" for row in self.rows})
        self.assertEqual(len(calls), 1, "one unknown-tab visit costs one classify, not eight")

    def test_sweep_hist_carries_the_journal_map_down(self):
        with tempfile.TemporaryDirectory() as root:
            shutil.copytree(self.d, os.path.join(root, "reel_s_1786385768689_67392"))
            res = cr.sweep_hist(root, classify=lambda p: None, read_page=lambda p, k: {"found": ["Shako"]},
                                sig_of=lambda n: self.sigs.get(n),
                                known_chronicle={row["f"]: "uniques" for row in self.rows})
            self.assertEqual(res["totals"]["journalRuns"], 1)
            self.assertEqual(res["totals"]["pagesRead"], 8)
            self.assertEqual(res["totals"]["classified"], 0)
            self.assertEqual(res["verdict"]["state"], "found")

    def test_a_deep_lane_frameId_finds_its_reel_frame_by_TIME(self):
        """★ MEASURED ON HIS OWN FOOTAGE. The journal's frameIds are '2_1786385782689' — a DIFFERENT
        capture of the same moment — and the reel names its frames 'f_<ms>.jpg' from its own grab.
        String matching finds ZERO of the 8; the nearest reel frame was 55-432ms away every time."""
        marks = {"%d_%d" % (i + 2, row["ts"] + 300): "uniques" for i, row in enumerate(self.rows)}
        r = self._sweep(known_chronicle=marks)
        self.assertEqual(len(r["pages"]), 8, "a mark must reach its frame across the capture gap")

    def test_a_mark_too_far_from_any_frame_is_dropped_not_stretched(self):
        far = {"2_%d" % (self.rows[0]["ts"] + 9000): "uniques"}
        r = self._sweep(known_chronicle=far)
        self.assertEqual(r["pages"], [], "a mark welded onto the wrong frame is worse than no mark")

    def test_a_mark_does_not_relabel_the_still_run_that_covers_it(self):
        """★ THE WELD THIS ALMOST SHIPPED. On his real reel the stillness pass produced ONE run
        spanning all 217 frames; lending that run a mark's ledger would declare a whole session of
        town and stash a Chronicle page. One frame speaks for itself and nothing beside it."""
        d = tempfile.mkdtemp()
        try:
            rows = [{"f": "g%d.jpg" % i, "ts": 1000 + i * 500} for i in range(9)]
            with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
                json.dump({"sessionId": "s_weld", "frames": rows}, fh)
            sigs = {row["f"]: sig(80) for row in rows}          # one held screen ⇒ ONE still run
            reads = []
            r = cr.read_reel(d, lambda p: None, lambda p, k: reads.append(os.path.basename(p)) or {},
                             sig_of=lambda n: sigs.get(n), known_chronicle={"g4.jpg": "uniques"})
            self.assertEqual(r["candidates"], 2, "the still run plus the marked frame's own run")
            self.assertEqual(reads, ["g4.jpg"], "only the MARKED frame is read as a Chronicle")
            self.assertEqual(r["classified"], 1, "the still run is still classified on its own merits")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_a_frame_is_never_read_TWICE(self):
        """Two sightings of one photograph is not corroboration — it would let a single frame pass a
        gate that asks for two independent witnesses."""
        d = tempfile.mkdtemp()
        try:
            rows = [{"f": "h%d.jpg" % i, "ts": 1000 + i * 500} for i in range(5)]
            with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
                json.dump({"sessionId": "s_dup", "frames": rows}, fh)
            sigs = {row["f"]: sig(80) for row in rows}
            reads = []
            cr.read_reel(d, lambda p: "chronicle-uniques",
                         lambda p, k: reads.append(os.path.basename(p)) or {},
                         # h0 is the frame _distinct keeps for the still run too — the overlap the
                         # guard exists for. Marking a frame the still run would NOT have read makes
                         # this test pass with no guard at all, which is no test.
                         sig_of=lambda n: sigs.get(n), known_chronicle={"h0.jpg": "uniques"})
            self.assertEqual(reads, ["h0.jpg"], "same frame read twice: %r" % (reads,))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_an_unmarked_reel_sweeps_exactly_as_before(self):
        """The blast radius: no journal map, no behaviour change."""
        self.assertEqual(self._sweep(known_chronicle=None), self._sweep())


class TestChronicleDatesReachTheEvidence(unittest.TestCase):
    """v1819 — Konyo: "date and timestamp related coding so they know what they registered
    yesterday and whats new today".

    Checked against his own 20-Aug frames before any of it was written: every Chronicle row prints
    its own `First Found:` stamp and a `Dropped By:` line, and the sort control reads
    "Newest to Oldest" at the top right. The sweep was reading those pages and keeping only the
    names, so nothing downstream could separate a find made TODAY from one that had simply never
    been read before — which is the only question he is asking.
    """

    UNIQUES = {
        "ledger": "uniques", "found": ["Razorswitch", "Greyform"], "notFound": [],
        "sort": "Newest to Oldest",
        "foundAt": {"Razorswitch": "08/20/2026, 00:49", "Greyform": "08/16/2026, 02:18"},
        "droppedBy": {"Razorswitch": "Infector of Souls", "Greyform": "Andariel"},
        "printedFound": 2, "printedTotal": 2, "stateVisible": True, "wrongTab": False, "conf": 0.9,
    }

    def test_a_page_keeps_its_stamps_and_its_sort(self):
        r = cr.normalize_page(dict(self.UNIQUES), "chronicle-uniques", "claude")
        self.assertEqual(r["sort"], "Newest to Oldest")
        self.assertEqual(r["foundAt"]["Razorswitch"], "08/20/2026, 00:49")
        self.assertEqual(r["droppedBy"]["Greyform"], "Andariel")

    def test_a_SWAPPED_read_never_reaches_the_ledger(self):
        # The two tabs print `First Found:` and `Dropped By:` in OPPOSITE orders, so a reader going
        # by position puts a monster where the date belongs. A wrong find-date outlives every later
        # correction, because nothing downstream re-reads a date it already has.
        r = cr.normalize_page({
            "ledger": "sets", "found": ["M'avina's True Sight"], "notFound": [],
            "sort": "Newest to Oldest",
            "foundAt": {"M'avina's True Sight": "Doom Knight"},
            "droppedBy": {"M'avina's True Sight": "08/17/2026, 00:10"},
            "printedFound": 1, "printedTotal": 1, "stateVisible": True, "wrongTab": False,
            "conf": 0.9}, "chronicle-sets", "claude")
        self.assertEqual(r["foundAt"], {}, "a monster name was stored as a find date")
        self.assertEqual(r["droppedBy"], {}, "a timestamp was stored as a monster")

    def test_the_stamp_travels_all_the_way_into_the_sighting(self):
        # a date sitting in normalize_page's output and not in the proposal would be plumbing with
        # no tap: the gate and every consumer downstream read sightings, not pages.
        resp = cr.normalize_page(dict(self.UNIQUES), "chronicle-uniques", "claude")
        prop = cr.proposal_from_pages(
            [{"reel": "reel_A", "frame": "f1", "kind": "chronicle-uniques", "resp": resp}])
        sighting = prop["uniques"]["Razorswitch"][0]
        self.assertEqual(sighting["foundAt"], "08/20/2026, 00:49")
        self.assertEqual(sighting["droppedBy"], "Infector of Souls")
        self.assertEqual(sighting["sort"], "Newest to Oldest")

    def test_a_page_that_prints_no_dates_still_reads_exactly_as_before(self):
        # additive or nothing: every page read before v1819 carries no stamps, and must keep
        # producing the same sightings it always did.
        bare = dict(self.UNIQUES)
        for k in ("sort", "foundAt", "droppedBy"):
            bare.pop(k)
        resp = cr.normalize_page(bare, "chronicle-uniques", "claude")
        self.assertEqual(resp["foundAt"], {})
        self.assertEqual(resp["sort"], "")
        prop = cr.proposal_from_pages(
            [{"reel": "reel_A", "frame": "f1", "kind": "chronicle-uniques", "resp": resp}])
        sighting = prop["uniques"]["Razorswitch"][0]
        self.assertNotIn("foundAt", sighting, "an absent stamp must not become an empty one")
        self.assertEqual(sighting["lane"], "claude")

    def test_both_reader_lanes_ask_for_the_same_three_fields(self):
        # the second eye must speak the same shape as the first, or a cross-lane agreement on a
        # find DATE is impossible by construction — the same reason `complete` was mirrored in v1566
        here = os.path.dirname(os.path.abspath(__file__))
        claude = open(os.path.join(here, "tv_diablo.py"), encoding="utf-8").read()
        grok = open(os.path.join(here, "g5_grok_eyes.py"), encoding="utf-8").read()
        for field in ('"foundAt":{{}}', '"droppedBy":{{}}'):
            self.assertIn(field, claude, "the Claude lane stopped asking for %s" % field)
            self.assertIn(field, grok, "the Grok lane stopped asking for %s" % field)
        # v1829 — `sort` IS DELIBERATELY ABSENT FROM BOTH, and this test asserted the retired
        # contract for a version after it was retired. v1828 dropped it because it returned empty
        # 2358 times out of 2358, including on a frame that plainly prints "Newest to Oldest" while
        # correctly returning four names and four dates from the same picture. The ordering it was
        # for is derivable from the per-row `First Found:` stamps instead.
        # SYMMETRY IS STILL THE POINT: one lane quietly re-adding it would put the lanes back in
        # different units, which is the whole reason this test exists.
        for lane_name, src in (("claude", claude), ("grok", grok)):
            self.assertNotIn('"sort":""', src,
                             "the %s lane is asking for `sort` again — v1828 retired it as a field "
                             "no reader has ever once filled; re-adding it on one lane only puts "
                             "the two eyes back in different units" % lane_name)


class TestOneReelCannotWitnessItselfTwice(unittest.TestCase):
    """v1824 — a reel is written into the evidence under TWO different names.

    read_reel takes `sid = idx.get("sessionId") or os.path.basename(reel_dir)`, so a reel whose
    index carries a sessionId lands as "s_1787177267889_92273" while one without it falls back to
    the directory name, "reel_s_1787177267889_92273". BOTH spellings are already in his live
    ledger — found while watching a real sweep write one of them.

    witnesses() counts DISTINCT reels, so one reel read once under each spelling would score
    `cross-reel`: two sessions' worth of independence conjured out of one recording. The function's
    own cross-frame rule states the principle — "Independence has to be independent of itself."
    """

    def test_the_same_reel_under_both_spellings_is_ONE_reel(self):
        sightings = [
            {"reel": "s_1787177267889_92273", "frame": "f1", "lane": "claude", "conf": 0.9},
            {"reel": "reel_s_1787177267889_92273", "frame": "f2", "lane": "claude", "conf": 0.9},
        ]
        w = cr.witnesses(sightings)
        self.assertNotIn("cross-reel", w,
                         "one recording claimed to be two independent sessions")
        self.assertIn("cross-frame", w, "two frames of one reel is still cross-frame")

    def test_two_genuinely_different_reels_still_corroborate(self):
        sightings = [
            {"reel": "s_1787177267889_92273", "frame": "f1", "lane": "claude", "conf": 0.9},
            {"reel": "reel_s_1786999742937_35523", "frame": "f2", "lane": "claude", "conf": 0.9},
        ]
        self.assertIn("cross-reel", cr.witnesses(sightings),
                      "normalising the key must not cost a real witness")

    def test_normalising_can_only_REMOVE_a_witness(self):
        # the safe direction: this may only ever shrink the evidence for a name, never inflate it,
        # so it cannot ground something that would not have grounded before.
        sightings = [
            {"reel": "reel_A", "frame": "f1", "lane": "claude", "conf": 0.9},
            {"reel": "A", "frame": "f2", "lane": "grok", "conf": 0.9},
        ]
        w = cr.witnesses(sightings)
        self.assertIn("cross-lane", w, "a second LANE is independent of how the reel is spelled")
        self.assertNotIn("cross-reel", w)


class TestV1833TheLiveLaneIsAWitness(unittest.TestCase):
    """v1833 — the live agent's Chronicle sightings become evidence.

    Konyo: "we had a AI reader for live too just its probably not gonna catch it... but if it does
    why not? make it an extra layer of accuracy its the first eyes". His journal already held them
    — 13 chronicle rows, 10 carrying `discovered_names` at conf 0.75 — and v1695 wired the live
    lane's FRAME IDENTITY into the sweep while the names it had paid for went nowhere.
    """

    def _led(self, name):
        return {"Windforce": "uniques", "Bul-Kathos' Sacred Charge": "uniques",
                "Tal Rasha's Adjudicator": "sets"}.get(name)

    ROW = {"scene": "chronicle", "sessionId": "s_100_1", "frameId": "f_9",
           "conf": 0.75, "discovered_names": ["Windforce"]}

    def test_a_live_row_becomes_a_page_on_its_own_lane(self):
        pages = cr.live_pages([dict(self.ROW)], self._led)
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["resp"]["lane"], "live")
        self.assertEqual(pages[0]["kind"], "chronicle-uniques")
        self.assertEqual(pages[0]["resp"]["found"], ["Windforce"])

    def test_the_ledger_is_derived_from_the_names_when_the_tab_is_unknown(self):
        # his real rows carry chronicleTab:null — that is the case this exists for
        pages = cr.live_pages([dict(self.ROW, chronicleTab=None)], self._led)
        self.assertEqual(pages[0]["kind"], "chronicle-uniques")

    def test_a_stated_tab_beats_the_derivation(self):
        pages = cr.live_pages([dict(self.ROW, chronicleTab="sets",
                                    discovered_names=["Tal Rasha's Adjudicator"])], self._led)
        self.assertEqual(pages[0]["kind"], "chronicle-sets")

    def test_a_row_whose_names_disagree_is_dropped_not_guessed(self):
        # guessing here does not cost a re-read, it writes a set piece into his unique grail
        row = dict(self.ROW, discovered_names=["Windforce", "Tal Rasha's Adjudicator"])
        self.assertEqual(cr.live_pages([row], self._led), [])

    def test_a_row_nothing_resolves_is_dropped(self):
        row = dict(self.ROW, discovered_names=["Battlecage", "Nonesuch"])
        self.assertEqual(cr.live_pages([row], self._led), [])

    def test_a_row_with_no_discoveries_contributes_nothing(self):
        self.assertEqual(cr.live_pages([dict(self.ROW, discovered_names=[])], self._led), [])

    def test_gameplay_rows_are_ignored(self):
        self.assertEqual(cr.live_pages([dict(self.ROW, scene="gameplay")], self._led), [])

    def test_live_plus_retro_on_one_session_is_cross_lane_and_not_cross_reel(self):
        # THE POINT OF THE WHOLE FEATURE, and its honest limit. The live sighting keys to its
        # sessionId, which _reel_key normalises to the retro reel's key — so the same footage read
        # twice by two different readers is ONE reel and TWO lanes.
        live = cr.live_pages([dict(self.ROW)], self._led)
        retro = {"reel": "reel_s_100_1", "frame": "f_42", "kind": "chronicle-uniques",
                 "resp": cr.normalize_page({"ledger": "uniques", "found": ["Windforce"],
                                            "stateVisible": True, "conf": 0.9},
                                           "chronicle-uniques", "claude")}
        prop = cr.proposal_from_pages(live + [retro])
        w = cr.witnesses(prop["uniques"]["Windforce"])
        self.assertIn("cross-lane", w)
        self.assertNotIn("cross-reel", w,
                         "one session's footage was counted as two — independence must be "
                         "independent of itself")

    def test_a_live_only_name_still_cannot_ground(self):
        live = cr.live_pages([dict(self.ROW)], self._led)
        prop = cr.proposal_from_pages(live)
        self.assertFalse(cr.gate_verdict("Windforce", prop["uniques"]["Windforce"])["pass"],
                         "the first eyes are an extra witness, never a shortcut past the gate")



class TestV1836TheCountersSurviveARemerge(unittest.TestCase):
    """v1836 — v1835 banks evidence mid-sweep, and the counters could not take it.

    A sighting has always been keyed by (reel, frame, lane), so NAMES fold correctly no matter how
    often a proposal is re-offered. The counters did not: `pagesRead` and `pagesRefused` were summed
    and `refused` was a bare extend. So the checkpointing shipped an hour earlier made a long sweep
    report roughly twice the pages it read, and repeated every refusal once per bank.

    That is the headline he reads. I misread this list myself tonight — took a cumulative `refused`
    for one pass's and briefly called a working fix a failure.
    """

    def _pages(self, reel, found_frames, refused_frames=()):
        out = []
        for f in found_frames:
            out.append({"reel": reel, "frame": f, "kind": "chronicle-uniques",
                        "resp": cr.normalize_page({"ledger": "uniques", "found": ["Windforce"],
                                                   "stateVisible": True, "conf": 0.9},
                                                  "chronicle-uniques", "claude")})
        for f in refused_frames:
            out.append({"reel": reel, "frame": f, "kind": "chronicle-uniques",
                        "resp": cr.normalize_page({"ledger": "uniques", "found": [],
                                                   "stateVisible": False, "conf": 0.2},
                                                  "chronicle-uniques", "claude")})
        return out

    def test_re_merging_the_same_proposal_changes_nothing(self):
        p = cr.proposal_from_pages(self._pages("r1", ["f1", "f2"], ["f3"]))
        m = cr.merge_proposals({}, p)
        first = (m["pagesRead"], m["pagesRefused"], len(m["refused"]))
        for _ in range(5):
            m = cr.merge_proposals(m, p)
        self.assertEqual((m["pagesRead"], m["pagesRefused"], len(m["refused"])), first,
                         "the counters grew on a re-merge — a banked sweep now overstates itself")

    def test_two_different_reels_still_add(self):
        a = cr.proposal_from_pages(self._pages("r1", ["f1", "f2"]))
        b = cr.proposal_from_pages(self._pages("r2", ["f1", "f2", "f3"]))
        m = cr.merge_proposals(a, b)
        self.assertEqual(m["pagesRead"], 5, "accumulation across sweeps was the point of v1776")

    def test_the_same_frame_in_two_reels_is_two_pages(self):
        # frame ids repeat across reels; the key has to be the pair
        a = cr.proposal_from_pages(self._pages("r1", ["f1"]))
        b = cr.proposal_from_pages(self._pages("r2", ["f1"]))
        self.assertEqual(cr.merge_proposals(a, b)["pagesRead"], 2)

    def test_a_refusal_is_not_counted_as_a_page_read(self):
        p = cr.proposal_from_pages(self._pages("r1", ["f1"], ["f2", "f3"]))
        m = cr.merge_proposals({}, p)
        self.assertEqual(m["pagesRead"], 1)
        self.assertEqual(m["pagesRefused"], 2)

    def test_a_legacy_ledger_without_page_keys_is_reconstructed(self):
        # his chron_evidence.json predates pageKeys; its pages are recoverable from the (reel,
        # frame) its own sightings already carry
        p = cr.proposal_from_pages(self._pages("r1", ["f1", "f2"]))
        p.pop("pageKeys")
        self.assertEqual(cr.merge_proposals({}, p)["pagesRead"], 2)

    def test_the_same_refusal_seen_twice_is_listed_once(self):
        p = cr.proposal_from_pages(self._pages("r1", [], ["f9"]))
        m = cr.merge_proposals(cr.merge_proposals({}, p), p)
        self.assertEqual(len(m["refused"]), 1,
                         "one refused frame, listed twice — this is what made me misread the list")



class TestV1838TheAuditTrailReachesASurface(unittest.TestCase):
    """v1838 — notFound is carried for audit and reached no surface a person reads.

    Absence stays inert: it subtracts from nothing, and the guard that says so
    (test_notFound_is_carried_for_audit_and_subtracts_from_nothing) is untouched. What changes is
    that the count is now reported, because an audit nobody can see is not an audit.

    It is also the cheapest instrument check available. A Chronicle page that yields eight found
    names and ZERO not-found rows means the reader saw the ticks and missed the list — the exact
    failure v1758 spent a version on, where a scrolled panel collapsed into one frame and reported
    the top of the list as the whole ledger. Zero here is a smell, not a clean bill.
    """

    def _page(self, reel, frame, found, not_found):
        return {"reel": reel, "frame": frame, "kind": "chronicle-uniques",
                "resp": cr.normalize_page({"ledger": "uniques", "found": found,
                                           "notFound": not_found, "stateVisible": True,
                                           "conf": 0.9}, "chronicle-uniques", "claude")}

    def test_the_count_is_reported_in_the_totals(self):
        res = cr.sweep_frames.__doc__ is not None   # module sanity, cheap
        self.assertTrue(res)
        prop = cr.proposal_from_pages([self._page("r1", "f1", ["Windforce"],
                                                  ["Stormshield", "Gore Rider"])])
        self.assertEqual(sorted(prop["notFound"]["uniques"]), ["Gore Rider", "Stormshield"])

    def test_absence_still_subtracts_from_nothing(self):
        # the rule this must not break: a name read as not-found does not remove or block a find
        # THREE reels, so the find genuinely grounds (cross-reel + cross-reel-3+ = two witnesses).
        # The first cut of this test used two and failed on the WITNESS COUNT while accusing the
        # not-found row of vetoing it — a fixture proving the gate's floor, not the claim.
        pages = [self._page("r1", "f1", ["Windforce"], []),
                 self._page("r2", "f2", ["Windforce"], ["Windforce"]),
                 self._page("r3", "f3", ["Windforce"], ["Windforce"])]
        prop = cr.proposal_from_pages(pages)
        self.assertIn("Windforce", prop["uniques"])
        self.assertIn("Windforce", prop["notFound"]["uniques"])
        v = cr.gate_verdict("Windforce", prop["uniques"]["Windforce"])
        self.assertTrue(v["pass"],
                        "a not-found sighting vetoed a find that its own witnesses ground: %s" % v)
        # and the SAME evidence without the not-found rows grounds identically — absence changed
        # nothing either way, which is the actual claim
        clean = cr.proposal_from_pages([self._page("r%d" % i, "f%d" % i, ["Windforce"], [])
                                        for i in (1, 2, 3)])
        self.assertEqual(cr.witnesses(prop["uniques"]["Windforce"]),
                         cr.witnesses(clean["uniques"]["Windforce"]))

    def test_a_page_with_no_not_found_rows_still_reports_zero_rather_than_nothing(self):
        # zero must be a MEASURED zero — "nobody looked" and "there were none" cannot look alike
        prop = cr.proposal_from_pages([self._page("r1", "f1", ["Windforce"], [])])
        self.assertEqual(prop["notFound"]["uniques"], [])

    def test_the_cli_prints_it(self):
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "chronicle_sweep_now.py"), encoding="utf-8").read()
        self.assertIn("not-found (audit only)", src,
                      "the audit count is computed and again reaches no surface")



class TestV1839ThreeRefusalsThreeNames(unittest.TestCase):
    """v1839 — "this is not the Chronicle" and "I cannot judge these rows" were the same word.

    A reel is a screen recording: it opens and closes on his TV DIABLO console window and on
    ordinary gameplay. Refusing those frames is CORRECT. But they came back stateVisible=false — the
    same answer as a legible Chronicle page whose rows could not be judged — so `refused 7` mixed
    healthy refusals with lost pages and could be read as neither.

    Settled by opening six of his refused frames rather than reasoning about them: three were the
    console window or gameplay (right to refuse), three were legible sets pages carrying First Found
    dates (lost). One number, two opposite meanings.
    """

    def _norm(self, **raw):
        base = {"ledger": "sets", "found": ["M'avina's Tenet (belt)"], "conf": 0.8,
                "stateVisible": True, "wrongTab": False}
        base.update(raw)
        return cr.normalize_page(base, "chronicle-sets", "claude")

    def test_a_non_chronicle_frame_says_so(self):
        self.assertEqual(self._norm(notChronicle=True)["note"], "not-a-chronicle-page")

    def test_a_chronicle_page_that_cannot_be_judged_still_says_no_found_state(self):
        self.assertEqual(self._norm(stateVisible=False)["note"], "no-found-state")

    def test_the_wrong_ledger_is_still_its_own_answer(self):
        self.assertEqual(self._norm(wrongTab=True)["note"], "wrong-ledger")

    def test_not_a_chronicle_page_outranks_the_other_two(self):
        # gameplay cannot be "the wrong tab" or "rows I could not judge" — there is no panel
        self.assertEqual(self._norm(notChronicle=True, wrongTab=True, stateVisible=False)["note"],
                         "not-a-chronicle-page")

    def test_it_contributes_no_names(self):
        r = self._norm(notChronicle=True)
        self.assertEqual(r["found"], [], "a gameplay frame handed names to the grail")

    def test_a_clean_page_is_unaffected(self):
        r = self._norm()
        self.assertIsNone(r["note"])
        self.assertEqual(r["found"], ["M'avina's Tenet (belt)"])

    def test_absent_means_not_claimed(self):
        # a reader that never heard of the field must not be read as asserting either way
        r = self._norm()
        self.assertIsNone(r["note"])

    def test_both_lanes_ask_for_it(self):
        here = os.path.dirname(os.path.abspath(__file__))
        claude = open(os.path.join(here, "tv_diablo.py"), encoding="utf-8").read()
        grok = open(os.path.join(here, "g5_grok_eyes.py"), encoding="utf-8").read()
        for lane, src in (("claude", claude), ("grok", grok)):
            self.assertIn('"notChronicle":false', src,
                          "the %s lane does not ask for notChronicle — cross-lane agreement is "
                          "only evidence if both lanes answer the same question" % lane)
            self.assertIn("notChronicle = true when the picture is not a Chronicle panel", src,
                          "the %s lane asks for the field without saying what it means" % lane)



class TestV1846WhatWasRegisteredYesterdayAndWhatIsNewToday(unittest.TestCase):
    """v1846 — the stamps were captured and never once COMPARED.

    Konyo: "maybe try to code and focus the AI readers to understand this logic too as an addition
    to the cross reference maybe date and timestamp related coding so they know what they registered
    yesterday and whats new today".

    v1819 taught both readers to capture each row's `First Found:` stamp, and the ledger has held
    them ever since — as TEXT. Read as text, stored as text, printed as text, and never compared.
    So the system knew every find-date in his grail and could not answer the one question he asked
    of them. This is the missing arithmetic.

    Measured on his real ledger: newest stamp 08/20/2026 02:10 (Hellclap), and six finds dated after
    08/17 — Hellclap, Rainbow Facet, Blood Raven's Charge, Rixot's Keen, Razorswitch and M'avina's
    Embrace, all in the early hours of the 20th.
    """

    def _prop(self, pairs):
        return {"uniques": {n: [{"reel": "r", "frame": "f", "lane": "claude", "foundAt": d}]
                            for n, d in pairs}, "sets": {}}

    def test_a_printed_stamp_sorts_by_time_not_by_text(self):
        # MM/DD/YYYY sorts alphabetically into nonsense: "01/02/2027" < "12/31/2026" as text
        early, late = cr.stamp_key("12/31/2026, 23:59"), cr.stamp_key("01/02/2027, 00:01")
        self.assertIsNotNone(early)
        self.assertLess(early, late, "the new year sorted before December")

    def test_a_monster_name_is_not_a_stamp(self):
        for junk in ("Hell Bovine", "", None, "Dropped By: Baal", "08/2026"):
            self.assertIsNone(cr.stamp_key(junk), "parsed a non-stamp: %r" % (junk,))

    def test_the_newest_stamp_is_found_across_both_ledgers(self):
        p = self._prop([("A", "05/10/2026, 23:22"), ("B", "08/20/2026, 02:10")])
        self.assertEqual(cr.newest_stamp(p), (2026, 8, 20, 2, 10))

    def test_a_ledger_with_no_stamps_has_no_newest(self):
        # None is not a date and must never compare as one
        self.assertIsNone(cr.newest_stamp({"uniques": {"A": [{"reel": "r", "frame": "f"}]}}))

    def test_only_finds_newer_than_the_mark_are_reported(self):
        p = self._prop([("old", "05/10/2026, 23:22"), ("new", "08/20/2026, 02:10")])
        got = cr.newly_dated(p, (2026, 8, 17, 23, 59))
        self.assertEqual([r["name"] for r in got], ["new"])

    def test_it_reports_newest_first(self):
        p = self._prop([("mid", "08/19/2026, 10:00"), ("newest", "08/20/2026, 02:10"),
                        ("older", "08/18/2026, 09:00")])
        got = cr.newly_dated(p, (2026, 8, 17, 0, 0))
        self.assertEqual([r["name"] for r in got], ["newest", "mid", "older"])

    def test_no_prior_mark_reports_NOTHING_rather_than_everything(self):
        """THE ONE THAT MATTERS. A ledger that has never held a stamp cannot tell new from old.
        Answering "everything is new" would flood the first sweep after this ships with his entire
        grail dressed as today's finds. [[unknown-stays-unknown]]"""
        p = self._prop([("A", "08/20/2026, 02:10")])
        self.assertEqual(cr.newly_dated(p, None), [])

    def test_a_name_keeps_its_newest_sighting(self):
        # one name seen in two reels keeps the later date, not whichever was merged last
        p = {"uniques": {"A": [{"reel": "r1", "frame": "f1", "foundAt": "05/10/2026, 23:22"},
                               {"reel": "r2", "frame": "f2", "foundAt": "08/20/2026, 02:10"}]},
             "sets": {}}
        got = cr.newly_dated(p, (2026, 8, 1, 0, 0))
        self.assertEqual(got, [{"name": "A", "foundAt": "08/20/2026, 02:10"}])




class TestTheGamesOwnFindDate(unittest.TestCase):
    """v1864 — Konyo: "i want the console also updateing me on when it was found timestamped in the
    game..(not when the AI READ IT) ... storyline synced with the ingame diablo ii".

    His Chronicle prints it per row and the reader has returned it since p1839. Measured live on
    his frame f_1787177298256.jpg, which is his own Sets page:

        foundAt   {"Immortal King's Will": "07/18/2026, 02:47",
                   "Immortal King's Pillar": "06/02/2026, 01:06"}
        droppedBy {"Immortal King's Will": "Andariel", "Immortal King's Pillar": "Andariel"}

    — matching the pixels exactly. What was missing was every step after: 0 of 339 names in his
    stored proposal carried a date, because nothing read it back off the sightings."""

    def test_two_lanes_agreeing_on_a_date_is_the_date(self):
        got = cr.in_game_stamp([
            {"lane": "claude", "foundAt": "07/18/2026, 02:47", "droppedBy": "Andariel"},
            {"lane": "grok", "foundAt": "07/18/2026, 02:47"},
            {"lane": "claude"}])
        self.assertEqual(got.get("at"), "07/18/2026, 02:47")
        self.assertEqual(got.get("by"), "Andariel")
        self.assertEqual(got.get("n"), 2)

    def test_a_TIE_between_two_dates_returns_nothing(self):
        # a First Found date is a FIXED fact — two equally-supported answers means it was misread,
        # and a wrong find-date reorders his history. Unknown stays unknown.
        self.assertEqual(cr.in_game_stamp([{"foundAt": "07/18/2026, 02:47"},
                                           {"foundAt": "06/02/2026, 01:06"}]), {})

    def test_a_majority_still_wins(self):
        got = cr.in_game_stamp([{"foundAt": "07/18/2026, 02:47"},
                                {"foundAt": "07/18/2026, 02:47"},
                                {"foundAt": "06/02/2026, 01:06"}])
        self.assertEqual(got.get("at"), "07/18/2026, 02:47")

    def test_the_date_and_the_dropper_are_decided_separately(self):
        # a page can print a legible dropper beside an illegible date, and vice versa
        got = cr.in_game_stamp([{"droppedBy": "Andariel"}, {"droppedBy": "Andariel"}])
        self.assertEqual(got.get("by"), "Andariel")
        self.assertNotIn("at", got)

    def test_no_sighting_carries_one_is_an_empty_answer_not_a_blank_date(self):
        self.assertEqual(cr.in_game_stamp([{"lane": "claude", "conf": 0.9}]), {})
        self.assertEqual(cr.in_game_stamp([]), {})
        self.assertEqual(cr.in_game_stamp(None), {})


class TestTheGameDateSurvivesTheWholeChain(unittest.TestCase):
    """v1871 — the END-TO-END proof, on his own reader output rather than an invented fixture.

    The `resp` below is MEASURED: it is what claude_chronicle_read returned when asked directly for
    frame f_1787177298256.jpg of his Set-pieces reel, and it matches his pixels — the row reads
    "IMMORTAL KING'S WILL · Dropped By: Andariel · First Found: 07/18/2026, 02:47".

    Each earlier guard covers one link. This one asserts the whole run: two frames × two lanes ->
    proposal_from_pages -> gate_verdict -> the exact wouldAdd row control_app ships to the board.
    v1864's defect was that every link was sound and the chain carried nothing."""

    RESP = {"kind": "chronicle", "ledger": "sets", "conf": 0.9, "stateVisible": True,
            "found": ["Immortal King's Will"], "notFound": [], "sets": [],
            "foundAt": {"Immortal King's Will": "07/18/2026, 02:47"},
            "droppedBy": {"Immortal King's Will": "Andariel"}}

    def _prop(self):
        pages = []
        for frame in ("f_1787177298256.jpg", "f_1787177300387.jpg"):
            for lane in ("claude", "grok"):
                pages.append({"reel": "s_1787177267889_92273", "frame": frame,
                              "resp": dict(self.RESP, lane=lane, witness="cross-frame")})
        return cr.proposal_from_pages(pages)

    def test_the_gate_grounds_it_and_the_row_carries_the_game_date(self):
        name = "Immortal King's Will"
        sights = self._prop()["sets"][name]
        v = cr.gate_verdict(name, sights)
        self.assertTrue(v.get("pass"), "his own two frames and two lanes did not corroborate: %r" % v)
        self.assertIn("cross-lane", v.get("witnesses") or [])
        stamp = cr.in_game_stamp(sights)
        self.assertEqual(stamp.get("at"), "07/18/2026, 02:47")
        self.assertEqual(stamp.get("by"), "Andariel")
        # the row control_app builds, assembled the same way
        row = dict({"name": name, "why": v.get("why", "")},
                   **({"gameFound": stamp} if stamp else {}))
        self.assertIn("gameFound", row,
                      "the row reaching the board carries no date — v1864's defect, returned")

    def test_a_page_that_prints_no_date_ships_NO_key_rather_than_an_empty_one(self):
        """Absent, never blank: the board has to be able to tell "found on this date" from
        "found, date unknown". [[unknown-stays-unknown]]"""
        bare = dict(self.RESP)
        bare.pop("foundAt"); bare.pop("droppedBy")
        pages = [{"reel": "r", "frame": "f.jpg", "resp": dict(bare, lane=l, witness="cross-frame")}
                 for l in ("claude", "grok")]
        sights = cr.proposal_from_pages(pages)["sets"]["Immortal King's Will"]
        stamp = cr.in_game_stamp(sights)
        self.assertEqual(stamp, {})
        row = dict({"name": "x"}, **({"gameFound": stamp} if stamp else {}))
        self.assertNotIn("gameFound", row)


class TestTheSortControlReachesThePage(unittest.TestCase):
    """v1907 — TWO HALVES EACH BUILT RIGHT, NEVER JOINED.

    The live prompt has asked for `chronicleSort` since v1818 — *"the sort control at the TOP RIGHT
    of the panel, read literally"* — and `tv_diablo` writes the answer into every chronicle journal
    row. `normalize_page` reads `sort`, and `proposal_from_pages` copies it onto every sighting.

    `live_pages` built its `raw` dict WITHOUT it. So the field was empty on every page ever produced:
    a question asked, an answer stored, and a reader looking at a different key.
    [[plumbing-with-no-tap]] [[the-unjoined-end]]"""

    def _row(self, **kw):
        row = {"scene": "chronicle", "chronicleTab": "uniques",
               "discovered_names": ["Harlequin Crest"], "conf": 0.9,
               "sessionId": "s_1", "frameId": "f_1", "ts": 1}
        row.update(kw)
        return row

    def test_a_live_row_carries_its_sort_onto_the_page(self):
        pages = cr.live_pages([self._row(chronicleSort="Newest to Oldest")])
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["resp"]["sort"], "Newest to Oldest",
                         "the sort control the live reader was asked for never reached the page")

    def test_the_snake_case_spelling_is_accepted_too(self):
        """tv_diablo accepts `chronicleTab` or `chronicle_tab` from the reader; the same defensive
        pair has to survive the whole way, or the tolerant half is decorative."""
        pages = cr.live_pages([self._row(chronicle_sort="Oldest to Newest")])
        self.assertEqual(pages[0]["resp"]["sort"], "Oldest to Newest")

    def test_a_row_with_no_sort_is_empty_not_invented(self):
        pages = cr.live_pages([self._row()])
        self.assertEqual(pages[0]["resp"]["sort"], "")

    def test_it_reaches_the_SIGHTING_not_just_the_page(self):
        """proposal_from_pages is where it has to land — a page nobody folds is not evidence."""
        pages = cr.live_pages([self._row(chronicleSort="Newest to Oldest")])
        prop = cr.proposal_from_pages(pages)
        sights = (prop.get("uniques") or {}).get("Harlequin Crest") or []
        self.assertTrue(sights, "the name never became a sighting")
        self.assertEqual(sights[0].get("sort"), "Newest to Oldest")

    def test_the_retro_prompts_deliberately_do_NOT_ask_for_it(self):
        """So a blank `sort` on a retro page is an absence of a QUESTION, and on a live page an
        absence of an ANSWER. v1828 settled that the printed `First Found:` stamps decide order,
        never a label — this pins that decision so the blank is explained, not accidental."""
        import g5_grok_eyes as g5
        import tv_diablo as td
        for name, prompt in (("claude", td.CHRONICLE_READ_PROMPT),
                             ("grok", g5.CHRONICLE_VISION_PROMPT)):
            self.assertNotIn("sort", prompt,
                             "the %s retro prompt now asks for a sort control — if that is "
                             "deliberate, v1828's reasoning has to be revisited, not quietly "
                             "reversed" % name)
        self.assertIn("chronicleSort", td.READ_PROMPT,
                      "the LIVE prompt stopped asking for it, which makes the join dead again")


class TestANotFoundReadingCarriesItsPage(unittest.TestCase):
    """v1921 — `notFound` was a bare set of NAMES: no reel, no frame, no lane, no moment.

    So when the same piece is read FOUND on one page and NOT FOUND on another — which happens
    constantly, because he keeps finding things — nothing could say which photographs disagreed, and
    nothing computed that they disagreed at all.

    ⚠ IT COST A WRONG ANSWER TO HIM DIRECTLY. Told that 12 of his 36 proposed set pieces were ones
    "the game says you do not have", the truth was that three of them — Natalya's Totem, Hsarus'
    Iron Fist, Hsarus' Iron Heel — carry First Found dates on his newest reel. The not-found
    readings were simply OLD. A claim built on evidence that cannot be dated cannot be checked.

    Measured over his banked evidence the day this shipped: **26 contested names**, 13 uniques and
    13 sets, including Immortal King's Will — the very item he had told me he does not have.

    ⚠ THIS MAKES THE CONTRADICTION VISIBLE, NOT RESOLVABLE. Resolving by recency needs a timestamp
    on the sighting, which these do not carry. Saying which is newer would be an invention, so it is
    reported and left to him. [[unknown-stays-unknown]]"""

    def _pages(self):
        return [
            {"reel": "r1", "frame": "f1.jpg", "kind": "chronicle-sets",
             "resp": cr.normalize_page({"stateVisible": True, "found": ["Tancred's Skull"],
                                        "notFound": ["Milabrega's Diadem"], "conf": 0.9},
                                       "chronicle-sets", "claude")},
            {"reel": "r2", "frame": "f2.jpg", "kind": "chronicle-sets",
             "resp": cr.normalize_page({"stateVisible": True, "found": ["Milabrega's Diadem"],
                                        "conf": 0.9}, "chronicle-sets", "grok")},
        ]

    def test_the_not_found_reading_names_its_page_and_its_eye(self):
        p = cr.proposal_from_pages(self._pages())
        seen = (p.get("notFoundSeen") or {}).get("sets", {}).get("Milabrega's Diadem") or []
        self.assertTrue(seen, "a not-found reading still carries no receipt")
        self.assertEqual(seen[0]["reel"], "r1")
        self.assertEqual(seen[0]["frame"], "f1.jpg")
        self.assertEqual(seen[0]["lane"], "claude")

    def test_the_contradiction_is_NAMED(self):
        p = cr.proposal_from_pages(self._pages())
        self.assertEqual((p.get("contested") or {}).get("sets"), ["Milabrega's Diadem"],
                         "a name read both ways is still averaged into silence")

    def test_an_uncontested_name_is_not_listed(self):
        """The mirror, or `contested` is just a copy of the proposal."""
        p = cr.proposal_from_pages(self._pages())
        self.assertNotIn("Tancred's Skull", (p.get("contested") or {}).get("sets") or [])

    def test_the_old_shape_still_stands_untouched(self):
        """Every existing reader and gate consumes `notFound` as a sorted list of names. The receipt
        is added BESIDE it; changing the old field would have been a second defect."""
        p = cr.proposal_from_pages(self._pages())
        self.assertEqual(p["notFound"]["sets"], ["Milabrega's Diadem"])
        self.assertIsInstance(p["notFound"]["uniques"], list)

    def test_a_merge_carries_the_receipts_and_recomputes_the_contradiction(self):
        """merge_proposals is what makes evidence ACCUMULATE; a field it does not know about is a
        field that quietly resets after one sweep."""
        a = cr.proposal_from_pages(self._pages()[:1])       # only the not-found page
        b = cr.proposal_from_pages(self._pages()[1:])       # only the found page
        m = cr.merge_proposals(a, b)
        self.assertEqual((m.get("contested") or {}).get("sets"), ["Milabrega's Diadem"],
                         "the contradiction vanished across a merge")
        seen = (m.get("notFoundSeen") or {}).get("sets", {}).get("Milabrega's Diadem") or []
        self.assertTrue(seen, "the receipt did not survive the merge")


class TestV1932APieceIsNotASet(unittest.TestCase):
    """A set the panel calls complete is ONE ROW WORTH FIVE PIECES. A piece accepted as a set there
    would tick pieces he does not own, from a single misread heading.

    MEASURED ON HIS BANKED EVIDENCE, not supposed: 5 of 38 setGroups keys are PIECE names —
    "M'avina's True Sight" (a helm) keyed as a set carrying M'avina's Icy Clutch and M'avina's
    Tenet; "Cleglaw's Claw" (a shield) carrying Cleglaw's Pincers and Tooth. The reader grouped
    rows under a row instead of under the heading.

    ⚠ The comparison is on the BARE name, because the readers print "M'avina's Tenet" while the
    roster stores "M'avina's Tenet (belt)" — the same two-conventions gap that once let a guard pass
    cleanly on 86 names none of which could ever have matched. [[source-reading-guard]]
    """

    def test_a_real_set_name_is_accepted(self):
        for good in ("M'avina's Battle Hymn", "Trang-Oul's Avatar", "Immortal King",
                     "Natalya's Odium"):
            self.assertFalse(cr._is_piece_not_set(good), "%s is a real set" % good)

    def test_a_piece_name_is_refused(self):
        for bad in ("M'avina's True Sight", "M'avina's Tenet", "Cleglaw's Claw",
                    "M'avina's Caster", "M'avina's Embrace"):
            self.assertTrue(cr._is_piece_not_set(bad), "%s is a PIECE, not a set" % bad)

    def test_the_suffixed_spelling_is_caught_too(self):
        self.assertTrue(cr._is_piece_not_set("M'avina's Tenet (belt)"))

    def test_with_no_roster_it_refuses_to_JUDGE_rather_than_refusing_the_data(self):
        """An unavailable roster must not turn every group into a refusal."""
        old = cr._PIECE_BARE
        try:
            cr._PIECE_BARE = set()
            self.assertFalse(cr._is_piece_not_set("M'avina's Tenet"))
        finally:
            cr._PIECE_BARE = old

    def test_the_refusal_is_recorded_not_dropped(self):
        pages = [{"reel": "s_1787177267889_92273", "frame": "f_1787177277865.jpg",
                  "resp": {"ledger": "sets", "lane": "claude", "sets": [
                      {"set": "M'avina's True Sight", "pieces": ["M'avina's Tenet"]},
                      {"set": "Trang-Oul's Avatar", "pieces": ["Trang-Oul's Claws"]}]}}]
        prop = cr.proposal_from_pages(pages)
        self.assertIn("Trang-Oul's Avatar", prop["setGroups"], "a real set must still be collected")
        self.assertNotIn("M'avina's True Sight", prop["setGroups"], "a piece must not become a set")
        rg = prop.get("refusedGroups") or []
        self.assertEqual([x["set"] for x in rg], ["M'avina's True Sight"],
                         "the refusal must be RECORDED — a silently dropped group is "
                         "indistinguishable from a page that held none")
        self.assertTrue(rg[0].get("frame"), "the refusal must carry its receipt")


class TestV1936ACalibrationTableCannotOutliveItsConstant(unittest.TestCase):
    """A comment that says "← chosen" about a value the code no longer uses.

    v1712 calibrated CHRON_STILL_MAX_DIFF and its table marked `0.005 ← chosen`. v1758 then moved
    the constant to **0.002** — correctly, and with its evidence immediately BELOW the constant —
    and nobody updated the table above it. Two statements about one number, three lines apart,
    disagreeing.

    Nothing was broken: the CODE is right. What is broken is the instruction to the next reader,
    who sees "0.005 ← chosen" beside `= 0.002` and helpfully "fixes" a deliberate decision back to
    the comment. I nearly did exactly that on 2026-08-21, which is why this exists.
    [[label-outlived-referent]] [[feedback-comments-vs-code]]
    """

    def _src(self):
        # plain open(), not io.open — `io` is not imported in this suite, and only THIS class
        # needed it. The guard about stale comments failed on its own missing import.
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "chronicle_retro.py"), encoding="utf-8") as fh:
            return fh.read()

    def test_no_chosen_marker_names_a_value_the_constant_does_not_use(self):
        import re
        s = self._src()
        m = re.search(r"^CHRON_STILL_MAX_DIFF\s*=\s*([0-9.]+)", s, re.M)
        self.assertIsNotNone(m, "the constant is gone — this guard has lost its subject")
        live = m.group(1)
        for line in s.split("\n"):
            if "chosen" not in line or not line.strip().startswith("#"):
                continue
            nums = re.findall(r"0\.\d+", line)
            if not nums:
                continue
            # a table row that still says "chosen" must either name the live value or say it is old
            if live in nums:
                continue
            self.assertTrue(
                "SUPERSEDED" in line.upper() or "AT THE TIME" in line.upper(),
                "this line marks %s as chosen while the constant is %s, and does not say it is "
                "history: %s" % (nums, live, line.strip()[:90]))

    def test_the_superseding_decision_is_recorded_beside_the_constant(self):
        s = self._src()
        i = s.index("CHRON_STILL_MAX_DIFF = ")
        self.assertIn("v1758", s[i:i + 400],
                      "the reason the constant holds its current value must live next to it, or "
                      "the older table upstream is the only story a reader finds")


class TestV2210AMachineWithoutGrokStillReadsAndRegisters(unittest.TestCase):
    """Konyo, mid-arc: "dont forget my cuzin doesnt have grok eyes.. it needs to read and register
    by default on CLAUDE".

    HE IS POINTING AT A SCAR THIS PROJECT HAS ALREADY PAID FOR TWICE. The third eye was hardwired to
    Grok, ON by default, and therefore PERMANENTLY EMPTY on every machine but his — every lamp
    green. And G5 sat `mode=primary` on this console for weeks with `calls: 0`, because a lane that
    never ATTEMPTS never records a failure.

    So this class asks the question from the COUSIN'S side, in three parts, and each one is a
    different way the same wrong answer could arrive:

      1. does a read still happen?           (two_lane_read with no Grok lane)
      2. is the absent lane STATED?          ("grok didn't run" must never read as "grok agreed")
      3. can a name still GROUND?            (the tier floors must be reachable on Claude alone)

    Part 3 is the one nothing else guards, and it is the one that could break silently: raise
    CONFLUENCE_FLOOR above what Claude-only evidence can reach, and his cousin's vault quietly stops
    registering while his own keeps working. Nobody would see it here.
    """

    def _claude(self, found):
        def _lane(path, kind):
            return {"ledger": "uniques", "found": list(found), "notFound": [], "kind": kind}
        return _lane

    def test_the_read_happens_with_no_grok_lane_at_all(self):
        out = cr.two_lane_read("p.png", "uniques", self._claude(["Shako", "Occulus"]), None)
        self.assertEqual(sorted(out.get("found") or []), ["Occulus", "Shako"],
                         "a machine with no Grok read NOTHING — Claude is the primary lane and "
                         "must not depend on a second eye existing")
        self.assertEqual(out.get("lanesRan"), ["claude"])

    def test_an_absent_second_eye_is_STATED_never_implied(self):
        out = cr.two_lane_read("p.png", "uniques", self._claude(["Shako"]), None)
        self.assertEqual(out.get("laneNote"), "grok-silent",
                         "the payload does not say the second eye was absent. 'grok did not run' "
                         "and 'grok agreed' are different facts, and only one of them means the "
                         "name has a second witness")
        self.assertNotIn("cross-lane", (out.get("lanes") or {}).get("Shako") or [],
                         "a missing lane was credited as agreement — the exact shape of the "
                         "empty-seat scar")
        # and a lane that RAISES must not be mistaken for one that disagreed
        def _boom(path, kind):
            raise RuntimeError("grok CLI not on PATH")
        out = cr.two_lane_read("p.png", "uniques", self._claude(["Shako"]), _boom)
        self.assertEqual(out.get("lanesRan"), ["claude"])
        self.assertEqual(out.get("laneNote"), "grok-silent")

    def test_claude_only_evidence_can_still_reach_every_floor(self):
        """⚠ THE ONE THAT COULD BREAK SILENTLY. `cross-lane` needs two DIFFERENT model families and
        is therefore unreachable on a machine with one. If a floor is ever set above what the
        remaining tiers can reach, his cousin's vault stops grounding anything and his own keeps
        working — and the difference is invisible from here.

        Measured today: three cross-reel sightings score 1.65 against a 1.00 floor, and the game's
        own printed date scores 1.00 on its own. Cross-lane is a BONUS. This test is what keeps it
        one.
        """
        reachable_without_grok = [t for t in cr.WITNESS_TIER if t != "cross-lane"]
        self.assertIn("printed", reachable_without_grok)

        # the strongest thing a one-lane machine can present: three reels, and the game's own date
        best_one_lane = cr.confluence(["cross-reel", "cross-reel-3+", "printed"])
        self.assertGreaterEqual(
            best_one_lane, cr.CONFLUENCE_FLOOR,
            "a machine with only Claude can reach at most %.2f confluence and the floor is %.2f — "
            "his cousin's vault would refuse every item while his own registers normally, and "
            "nothing on this machine would show it" % (best_one_lane, cr.CONFLUENCE_FLOOR))

        # and REPETITION ALONE, with no printed date, must still be enough — most items never carry
        # an in-game date at all
        repetition_only = cr.confluence(["cross-reel", "cross-reel-3+"])
        self.assertGreaterEqual(
            repetition_only, cr.CONFLUENCE_FLOOR,
            "three separate sessions seeing the same item score %.2f against a %.2f floor, so on a "
            "one-lane machine only items carrying an in-game Chronicle date could ever ground. "
            "Most items do not carry one." % (repetition_only, cr.CONFLUENCE_FLOOR))

    def test_switching_grok_ON_only_ADDS_and_never_weakens_the_claude_verdict(self):
        """Konyo: "make sure witnesses are claude only based by default and when switched on".

        The default half is the three tests above. THIS is the other half, and it is the one a
        second eye can quietly break: turning Grok on must never REMOVE a name Claude found, never
        lower a witness count, and never make an item that grounded stop grounding. A second opinion
        that can subtract is not a second opinion, it is a veto nobody asked for.
        """
        claude = self._claude(["Shako", "Occulus", "Skin of the Vipermagi"])

        def grok_sees_less(path, kind):
            return {"ledger": "uniques", "found": ["Shako"], "notFound": [], "kind": kind}

        def grok_sees_other(path, kind):
            return {"ledger": "uniques", "found": ["Gheed's Fortune"], "notFound": [], "kind": kind}

        alone = cr.two_lane_read("p.png", "uniques", claude, None)
        less = cr.two_lane_read("p.png", "uniques", claude, grok_sees_less)
        other = cr.two_lane_read("p.png", "uniques", claude, grok_sees_other)

        for name in (alone.get("found") or []):
            self.assertIn(name, less.get("found") or [],
                          "%r was found by Claude and DISAPPEARED once Grok was switched on. The "
                          "second lane is a union, never an intersection -- a name only one lane "
                          "saw is kept as a one-lane sighting for the gate to judge." % (name,))
            self.assertIn(name, other.get("found") or [],
                          "%r vanished when Grok reported a different name entirely" % (name,))

        # a name only Grok saw is ADDED, and marked as Grok-only rather than merged into agreement
        self.assertIn("Gheed's Fortune", other.get("found") or [],
                      "a name only the second eye saw was discarded -- then switching Grok on buys "
                      "nothing, which is worse than not having it")
        self.assertEqual((other.get("laneAgreement") or {}).get("grokOnly"), ["Gheed's Fortune"])
        self.assertEqual(sorted((other.get("laneAgreement") or {}).get("claudeOnly") or []),
                         ["Occulus", "Shako", "Skin of the Vipermagi"],
                         "a Claude-only name was silently upgraded to agreed")

        # and the witness count for a Claude-only name must not FALL when Grok joins
        w_alone = cr.witnesses([{"lane": "claude", "reel": "rA"}, {"lane": "claude", "reel": "rB"}])
        w_both = cr.witnesses([{"lane": "claude", "reel": "rA"}, {"lane": "claude", "reel": "rB"},
                              {"lane": "grok", "reel": "rA"}])
        self.assertTrue(set(w_alone) <= set(w_both),
                        "turning Grok on REMOVED a witness tag: %s -> %s. Adding evidence must "
                        "never subtract from what was already established."
                        % (sorted(w_alone), sorted(w_both)))
        self.assertIn("cross-lane", w_both, "the second lane contributed no cross-lane tag at all")
        self.assertGreaterEqual(cr.confluence(w_both), cr.confluence(w_alone),
                                "switching the second eye on LOWERED the confluence score")

    def test_cross_lane_is_worth_less_than_the_evidence_a_lone_machine_can_gather(self):
        """A second eye must be a BONUS, not the top of the scale, or the machine that has one is
        playing a different game from the machine that does not."""
        self.assertLess(cr.WITNESS_TIER["cross-lane"], cr.WITNESS_TIER["printed"],
                        "cross-lane outranks the GAME'S OWN printed date. A second model agreeing "
                        "is weaker evidence than the game saying so, always")
        self.assertLess(cr.WITNESS_TIER["cross-lane"], cr.WITNESS_TIER["cross-reel-3+"],
                        "cross-lane outranks three independent sessions. It must not, or the "
                        "machine with Grok grounds on less evidence than the machine without")



class TestV2217TheShadowLaneLearnsAndNeverPromotesItself(unittest.TestCase):
    """Konyo: "make it self improving and really accurate so its locked and locks in the console."

    The Wilson lane was implemented and agreed with the live gate on every name it had ever scored.
    That sounds like a result and is not one — it is a statement about how little evidence his tree
    holds (23 names), not about the two rules. So the lane ACCUMULATES: every sweep adds its scored
    names and its disagreements to one durable record, and the console reports the record.

    ⚠ IT NEVER PROMOTES ITSELF. Reaching the threshold means the record is worth HIS decision. A
    gate that switched on its own agreement statistics is marking its own homework, and the failure
    lands as a wrong verdict in his grail, where a wrong answer is invisible.
    """

    def setUp(self):
        import shutil
        import tempfile
        self.d = tempfile.mkdtemp()
        self.led = os.path.join(self.d, "shadow_ledger.json")
        self.addCleanup(shutil.rmtree, self.d, True)

    def _agree(self):
        """3 reels x 1 frame — both rules ground it. Measured."""
        return [{"lane": "claude", "reel": r, "frame": "f1.png", "conf": 0.97}
                for r in ("rA", "rB", "rC")]

    def _disagree(self):
        """2 reels x 3 frames — the live gate grounds it on two witness KINDS; the shadow holds it
        at confluence 0.85 because the evidence is repetitive. Measured, and it is the shape a MINI
        capture produces, so it WILL occur in his data."""
        return ([{"lane": "claude", "reel": "rA", "frame": "f%d.png" % i, "conf": 0.97}
                 for i in range(3)]
                + [{"lane": "claude", "reel": "rB", "frame": "f%d.png" % i, "conf": 0.97}
                   for i in range(3)])

    def test_the_disagreeing_shape_really_does_disagree(self):
        """⚠ THE FIXTURE CHECK FIRST. Every assertion below about disagreements is vacuous if this
        shape does not actually split the two rules."""
        v = cr.gate_verdict("X", self._disagree())
        self.assertTrue(v["pass"], "the live gate no longer grounds this shape")
        self.assertFalse((v.get("shadow") or {}).get("wouldPass"),
                         "the shadow no longer holds this shape — the fixture stopped separating "
                         "the two rules and every disagreement test below proves nothing")
        a = cr.gate_verdict("X", self._agree())
        self.assertTrue(a["pass"])
        self.assertTrue((a.get("shadow") or {}).get("wouldPass"))

    def test_it_counts_DISTINCT_names_not_repeat_scorings(self):
        """⚠⚠ v2225 — THIS TEST USED TO ENCODE THE DEFECT AS CORRECT.

        It observed the SAME single name three times and asserted (names, sweeps) == (3, 3), then
        called the result "thin" only because 3 < 500. So the guard blessed counting one name three
        times as three names, and stayed green while the field called `names` filled with repeats.

        On his live tree that ran to names=1263 across 717 sweeps — while chron_evidence.json holds
        417 distinct names and bible.html pins the uniques universe at 403. 1263 DISTINCT was
        arithmetically impossible. It crossed ENOUGH_SWEEPS=20 in about 222 seconds, so state()
        returned "agrees" — the branch whose sentence is "The record is worth a decision" — and
        console_doctor rendered it OK, on one small slice re-read every eleven seconds.

        The lane exists to argue for changing the gate that writes his grail. It was arguing from
        repetition. [[unknown-stays-unknown]] [[regression-guard]]"""
        for i in range(3):
            r = _sl().observe(cr.shadow_scores({"Shako": self._agree()}), at=1000 + i, path=self.led)
            self.assertTrue(r["ok"], r)
        st = _sl().state(path=self.led)
        self.assertEqual(st["names"], 1,
                         "one name scored three times is ONE name; %r says otherwise" % st["names"])
        self.assertEqual(st["sweeps"], 3, "three sweeps did happen and that number is honest")
        self.assertEqual(st["scorings"], 3,
                         "the old inflated total must survive under its true label, so the "
                         "ratio scorings/names makes re-reading visible instead of silent")
        self.assertEqual(st["disagree"], 0)
        self.assertEqual(st["state"], "thin",
                         "one name is not enough to be worth a decision and must not read as if "
                         "it were")

    def test_the_DISAGREE_counter_has_the_SAME_defect_v2225_fixed_for_names(self):
        """★★ B-65 — v2225 FIXED `names` WITH A SET AND LEFT ITS TWIN COUNTING EVENTS.

        Twelve lines below that fix, `disagree` still did `+= len(dis)` on every sweep. So it is an
        EVENT count whose denominator is `scorings`, while state() divided it by `names`. MEASURED
        on his live ledger 2026-09-02:

            sweeps 17,579 · names 414 (distinct, correct) · scorings 343,515
            agree 311,851 · disagree 31,664      <- agree + disagree == scorings, NOT names

        and the console printed "disagreed on 31,664 of 414 names" — a numerator 76x its
        denominator. THE COUNT WAS THE TELL, which is the same sentence v2225 wrote about the same
        defect one field over, and nobody read it again. [[sweep-dont-ask]]

        This pins BOTH halves: the event count keeps growing honestly, and the DISTINCT count —
        the number he would actually act on — is tracked separately instead of not at all."""
        for i in range(4):
            r = _sl().observe(cr.shadow_scores({"Shako": self._disagree()}), at=2000 + i,
                              path=self.led)
            self.assertTrue(r["ok"], r)
        st = _sl().state(path=self.led)
        self.assertEqual(st["state"], "disagrees", "fixture check: this shape must split the rules")
        self.assertEqual(st["disagree"], 4,
                         "the EVENT count must keep counting events — it is true and other readers "
                         "use it; renaming its meaning would be a second defect")
        self.assertEqual(st["disagreeNames"], 1,
                         "one name that disagrees on four sweeps is ONE disagreeing name. %r says "
                         "otherwise, which is exactly the shape that produced '31,664 of 414'"
                         % st.get("disagreeNames"))

    def test_the_sentence_divides_by_the_denominator_it_actually_HAS(self):
        """The arithmetic must be sayable out loud without being impossible."""
        for i in range(4):
            _sl().observe(cr.shadow_scores({"Shako": self._disagree()}), at=3000 + i, path=self.led)
        st = _sl().state(path=self.led)
        say = st["say"]
        # ⚠ THE FIRST CUT OF THIS TEST WAS TOO WEAK AND A SABOTAGE PROVED IT. Asserting that the
        # word "scorings" appears, and that the old phrasing does not, both survived swapping
        # "across N sweeps" for "across N names" — the word was still there and the old phrasing
        # still absent, while the sentence had gone wrong again. A guard that names a WORD instead
        # of a RELATIONSHIP measures the vocabulary, not the arithmetic.
        # [[regression-guard]] §5a — when a sabotage stays green, suspect the sabotage first, and
        # when the sabotage turns out to be real, the test is what has to get stronger.
        # So: assert the actual NUMBERS land beside the actual WORDS.
        import re as _re
        m = _re.search(r"disagreed (\d+) times out of (\d+) scorings across (\d+) sweeps", say)
        self.assertIsNotNone(
            m, "the sentence no longer states <disagree> out of <scorings> across <sweeps>. Each "
               "number must sit beside the unit it is actually counted in — pairing the event "
               "count with `names` is exactly how it read as 76x its own denominator.\n%s" % say)
        self.assertEqual(int(m.group(1)), st["disagree"], "the printed count is not `disagree`")
        self.assertEqual(int(m.group(2)), st["scorings"],
                         "the DENOMINATOR printed is not `scorings`. agree + disagree == scorings, "
                         "so that is the only denominator this numerator has")
        self.assertEqual(int(m.group(3)), st["sweeps"], "the printed sweeps figure is not `sweeps`")
        self.assertNotRegex(say, r"disagreed on \d+ of \d+ names",
                            "the impossible phrasing is back")

    def test_a_ledger_from_BEFORE_this_ship_says_UNKNOWN_not_zero(self):
        """His real ledger has 17,579 sweeps banked with no disagreeSet. It CANNOT answer the
        distinct question, and answering 0 would be a measurement nobody took — the same lie as
        collapsing None into 0. [[unknown-stays-unknown]]"""
        import json
        with io.open(self.led, "w", encoding="utf-8") as fh:
            json.dump({"v": 1, "sweeps": 900, "names": 400, "scorings": 9000,
                       "agree": 8000, "disagree": 1000, "nameSet": ["n%d" % i for i in range(400)],
                       "recent": [{"name": "Shako"}]}, fh)
        st = _sl().state(path=self.led)
        self.assertIsNone(st["disagreeNames"],
                          "a ledger with no disagreeSet reported a NUMBER for distinct names. It "
                          "has never counted them; 0 would be a measurement nobody took")
        self.assertIn("unknown rather than none", st["say"])

    def test_two_DIFFERENT_names_do_accumulate(self):
        """The other half, or the fix could pass by always answering 1."""
        _sl().observe(cr.shadow_scores({"Shako": self._agree()}), at=1, path=self.led)
        _sl().observe(cr.shadow_scores({"Windforce": self._agree()}), at=2, path=self.led)
        st = _sl().state(path=self.led)
        self.assertEqual(st["names"], 2, "distinct names must still accumulate")

    def test_a_disagreement_is_kept_BY_NAME_not_counted(self):
        _sl().observe(cr.shadow_scores({"Windforce": self._disagree()}), at=1, path=self.led)
        st = _sl().state(path=self.led)
        self.assertEqual(st["state"], "disagrees")
        self.assertEqual(st["disagree"], 1)
        row = st["recent"][-1]
        self.assertEqual(row["name"], "Windforce")
        self.assertTrue(row["live"], "the row does not record what the LIVE gate said")
        self.assertFalse(row["shadowPass"], "the row does not record what the SHADOW said")
        self.assertIsNotNone(row.get("wilson"))
        self.assertIsNotNone(row.get("confluence"))
        self.assertIn("Windforce", st["say"],
                      "the summary counts disagreements without naming them — a count is not "
                      "actionable and is where a real divergence hides")

    def test_the_thin_state_says_HOW_FAR_OFF(self):
        _sl().observe(cr.shadow_scores({"Shako": self._agree()}), at=1, path=self.led)
        say = _sl().state(path=self.led)["say"]
        self.assertIn("SMALL SAMPLE", say,
                      "agreement on a tiny sample is being presented as evidence the rules are "
                      "equivalent")
        self.assertIn("more names", say)

    def test_an_unreadable_ledger_never_reads_as_agreement(self):
        with io.open(self.led, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        st = _sl().state(path=self.led)
        self.assertFalse(st["ok"])
        self.assertEqual(st["state"], "unreadable")
        self.assertIn("not the same as", st["say"])
        # and observing over it must REFUSE rather than silently start a new count
        r = _sl().observe(cr.shadow_scores({"Shako": self._agree()}), at=1, path=self.led)
        self.assertFalse(r["ok"], "a new count was started over an unreadable ledger, erasing the "
                                  "history the record exists to build")

    def test_the_sweep_door_SCORES_and_the_ledger_PERSISTS(self):
        """THE JOINT, in the shape the architecture actually has.

        chronicle_retro cannot write — law 1 of that file, proven from its source text by
        test_sweeping_writes_nothing_anywhere, which caught my first cut opening a file inside it.
        So apply_proposal attaches SCORES and shadow_ledger persists them.

        ⚠ AND THE SCAR THIS GUARDS, which happened while writing this feature: the first cut called
        time.time() in a module that did not import `time`; the NameError went into a bare
        `except: pass`, nothing was written, and apply_proposal returned normally. The lane looked
        installed and would have reported "agrees so far" forever while learning nothing. So this
        asserts the FILE, never the call. [[paid-work-with-no-memory]]
        """
        prop = {"uniques": {"Windforce": self._disagree()}, "sets": {}}
        out = cr.apply_proposal(prop, {"uniques": [], "sets": []}, gate=cr.strict_gate())
        sc = out.get("shadow")
        self.assertIsInstance(sc, dict, "the sweep door attached no shadow scores at all")
        self.assertEqual(sc["scored"], 1)
        self.assertEqual(len(sc["disagreements"]), 1,
                         "the disagreeing shape scored as agreement — the fixture or the rule moved")
        self.assertNotIn("ok", sc, "apply_proposal is reporting a WRITE outcome; this module must "
                                   "not write at all")
        self.assertFalse(os.path.exists(self.led),
                         "scoring wrote a file — chronicle_retro must stay read-only")

        r = _sl().observe(sc, at=1, path=self.led)
        self.assertTrue(r["ok"], r)
        self.assertTrue(os.path.exists(self.led),
                        "observe() returned ok and the ledger was NEVER WRITTEN")
        st = _sl().state(path=self.led)
        self.assertEqual(st["disagree"], 1)
        self.assertIn("Windforce", st["say"])

    def test_the_console_joins_the_two_halves(self):
        """⚠ SCORING AND PERSISTING ARE BOTH USELESS UNJOINED. control_app._shadow_bank is the
        joint; if it stops being called after a sweep the lane silently stops learning and still
        reports whatever it last knew. [[the-unjoined-end]]"""
        src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "control_app.py"), encoding="utf-8").read()
        self.assertIn("def _shadow_bank(", src, "the joint is gone")
        # ⚠ COUNT CALLS, NOT THE DEFINITION. `def _shadow_bank(applied):` contains the very
        # string a naive count matches, so removing EVERY call site still left the assertion
        # satisfied by the def line — measured: 4 call sites deleted, count still 1, test green.
        # A guard that counts its own subject is the shape this repo keeps paying for.
        # [[feedback-comments-vs-code]] [[feedback-suspect-the-instrument]]
        calls = [ln for ln in src.split("\n")
                 if "_shadow_bank(applied)" in ln and not ln.lstrip().startswith("def ")]
        self.assertGreaterEqual(len(calls), 1,
                                "nothing calls _shadow_bank after a sweep — the lane scores and "
                                "nothing ever records it, silently")
        body = src[src.index("def _shadow_bank("):src.index("def _console_beacon(")]
        self.assertIn("shadow_ledger", body, "the joint no longer reaches the writer")
        self.assertNotIn("except Exception:\n        pass", body,
                         "the joint swallows its failure silently — the exact defect that made the "
                         "first version of this lane learn nothing forever")

    def test_observing_NEVER_changes_what_the_sweep_applied(self):
        """A shadow that can alter the answer is not a shadow."""
        prop = {"uniques": {"Shako": self._agree()}, "sets": {}}
        with_lane = cr.apply_proposal(prop, {"uniques": [], "sets": []}, gate=cr.strict_gate())
        without = cr.apply_proposal(prop, {"uniques": [], "sets": []}, gate=cr.strict_gate())
        self.assertEqual(with_lane.get("uniques"), without.get("uniques"),
                         "the applied result changed depending on whether the shadow could record")
        self.assertEqual(with_lane.get("held"), without.get("held"))



class TestV2370TheSurfaceShadowIsJOINED(unittest.TestCase):
    """It was computed on every verdict since v2357 and read by NOBODY.

    The only two references to `surfaceShadow` in the whole tree were its own two assignments in
    gate_verdict. The Wilson shadow beside it runs a complete rail — shadow_scores ->
    shadow_ledger.observe -> state() -> console_doctor / control_app / corroborate — so the fix
    was to put the surface rule ON that rail, not to build a second one. [[the-unjoined-end]]"""

    def _by_name(self):
        # two sightings of one name, so the live gate has something to judge
        return {"Shadow Dancer": [{"reel": "r1", "frame": "f_1.jpg", "kind": "panel"},
                                  {"reel": "r2", "frame": "f_2.jpg", "kind": "panel"}]}

    def test_the_scorer_returns_the_surface_rule_at_all(self):
        out = cr.shadow_scores(self._by_name())
        self.assertIn("surfaceScored", out,
                      "shadow_scores dropped the surface shadow again — it is computed on every "
                      "verdict and this is the only thing that carries it anywhere")
        self.assertIn("surfaceDisagreements", out)
        self.assertIsInstance(out["surfaceDisagreements"], list)

    def test_the_ledger_folds_it_and_state_reports_it(self):
        import shadow_ledger as sl
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "ledger.json")
            row = {"name": "X", "live": True, "shadowPass": False, "rule": "surface",
                   "direction": "live-grounds-surface-holds"}
            r = sl.observe({"scored": 1, "disagreements": [], "names": ["X"],
                            "surfaceScored": 1, "surfaceDisagreements": [row]}, path=p)
            self.assertTrue(r.get("ok"), r)
            doc = json.load(io.open(p, encoding="utf-8"))
            self.assertEqual(doc["surface"]["scored"], 1, "the surface score was not folded")
            self.assertEqual(doc["surface"]["wouldHold"], 1)
            self.assertEqual(doc["surface"]["wouldGround"], 0)
            st = sl.state(path=p)
            self.assertIn("surface", st,
                          "state() dropped it, which just moves the unjoined end one file along")
            self.assertEqual(st["surface"]["wouldHold"], 1)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_a_ledger_written_before_this_still_reads(self):
        """An older ledger has no surface sub-document; it must gain an empty one, not crash."""
        import shadow_ledger as sl
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "ledger.json")
            io.open(p, "w", encoding="utf-8").write(json.dumps(
                {"v": 1, "sweeps": 3, "names": 2, "byDirection": {}, "recent": [], "nameSet": ["A", "B"]}))
            r = sl.observe({"scored": 1, "disagreements": [], "names": ["C"],
                            "surfaceScored": 2, "surfaceDisagreements": []}, path=p)
            self.assertTrue(r.get("ok"), r)
            self.assertEqual(json.load(io.open(p, encoding="utf-8"))["surface"]["scored"], 2)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_the_surface_rule_can_HOLD_but_never_GROUND(self):
        """`would = live_pass and meets_surface`, so one direction is structurally impossible.

        An earlier cut of the surface rule DID drop the confidence floor and would have grounded
        33 names the live gate refuses — OCR garbles whose repeated misreads looked like
        witnesses. This pins the law, not the number: if surface_shadow ever passes where the
        live verdict failed, the shadow has become a WEAKER gate wearing a stricter name."""
        for live in (True, False):
            v = {"pass": live}
            ss = cr.surface_shadow(
                [{"reel": "r%d" % i, "frame": "f_%d.jpg" % i, "kind": "panel"} for i in range(6)],
                surface_of=None, live_verdict=v)
            if "wouldPass" in ss and not live:
                self.assertFalse(ss["wouldPass"],
                                 "the surface shadow GROUNDED a name the live gate holds — it is "
                                 "built so that cannot happen; a weaker gate in stricter clothing")


class TestV2379TarnhelmRoutesITSELFOnTheSecondWitness(unittest.TestCase):
    """The one item that went right, turned into a guard — on HIS OWN reels.

    Konyo, 2026-09-01: "i just saw tarnhelm in my inbox and it correctly registered it hile in
    shadow mode.. the extraction and everything and read correctly.. i just tallied it to my
    chronicle(NOT MY VAULT)" — and then the ask this case exists for: "i did it.. so that next
    step if i had not have tallied it manually i want the enxt parrt automated too.. like lets say
    for example it did get that second witness run tests and simulation and demonstrations using
    that exact example wit hthose exact reels images."

    TRACED FROM HIS LIVE BOARD STORE:
        session   s_1788213593006_73234        shadow reel, unattended
        frame     f_1788213611266.jpg
        loc       null            <- no container evidence, so it may never claim the vault
        gate      HELD "only 1 independent witness (cross-frame) — needs 2"

    A WITNESS IS A KIND OF INDEPENDENCE, NOT A SIGHTING. cross-lane · cross-reel · cross-reel-3+ ·
    cross-frame (two frames inside ONE reel) · printed. Two sightings in two reels is ONE witness
    (cross-reel), which is why his 58 sightings still read as one — and this case pins that,
    because it looks like a contradiction on screen and is not."""

    REEL_A = "reel_s_1788213593006_73234"      # his Tarnhelm reel
    REEL_B = "reel_s_1788210216752_34991"      # a different real session of his
    FRAME_A1 = "f_1788213611266.jpg"           # the frame that actually read it
    FRAME_A2 = "f_1788213640000.jpg"
    FRAME_B1 = "f_1788210260510.jpg"

    def _s(self, reel, frame, lane="claude"):
        return {"reel": reel, "frame": frame, "lane": lane, "conf": 0.9,
                "loc": None, "witness": "none"}

    def _today(self):
        return [self._s(self.REEL_A, self.FRAME_A1), self._s(self.REEL_A, self.FRAME_A2)]

    def test_his_ACTUAL_state_is_held_for_him(self):
        """Reproduces the sentence on his screen, from his own reel."""
        sg = self._today()
        self.assertEqual(cr.witnesses(sg), ["cross-frame"])
        v = cr.gate_verdict("Tarnhelm", sg)
        self.assertFalse(v["pass"])
        self.assertIn("needs 2", v["why"])

    def test_a_second_SESSION_lets_it_register_ITSELF(self):
        sg = self._today() + [self._s(self.REEL_B, self.FRAME_B1)]
        self.assertEqual(cr.witnesses(sg), ["cross-frame", "cross-reel"])
        v = cr.gate_verdict("Tarnhelm", sg)
        self.assertTrue(v["pass"], v.get("why"))
        out = cr.apply_proposal({"uniques": {"Tarnhelm": sg}}, existing={}, gate=cr.strict_gate())
        self.assertEqual([h.get("name") for h in (out.get("held") or [])], [],
                         "with two witnesses it still waits for him — the automatic half is dead")

    def test_a_second_LANE_does_it_too(self):
        """Different reader, same reel. Independence does not have to mean a new session."""
        sg = [self._s(self.REEL_A, self.FRAME_A1),
              self._s(self.REEL_A, self.FRAME_A2, lane="live")]
        self.assertEqual(cr.witnesses(sg), ["cross-frame", "cross-lane"])
        self.assertTrue(cr.gate_verdict("Tarnhelm", sg)["pass"])

    def test_it_can_NEVER_route_to_the_vault_however_many_witnesses(self):
        """The half he cares most about: loc is null, so it proves he FOUND it, never that he
        HOLDS it. apply_proposal has no vault path at all — this pins that it stays that way."""
        sg = self._today() + [self._s(self.REEL_B, self.FRAME_B1)]
        out = cr.apply_proposal({"uniques": {"Tarnhelm": sg}}, existing={}, gate=cr.strict_gate())
        self.assertNotIn("vault", " ".join(out.keys()).lower(),
                         "apply_proposal grew a vault channel — a chronicle sighting with no "
                         "container must never become a claim that he HOLDS the item")
        self.assertIn("uniques", out)

    def test_two_reels_is_ONE_witness_not_two(self):
        """Why his 58 sightings still read as a single witness. Counting sightings instead of
        KINDS would let one repeated misread ground a name on its own."""
        sg = [self._s(self.REEL_A, self.FRAME_A1), self._s(self.REEL_B, self.FRAME_B1)]
        self.assertEqual(cr.witnesses(sg), ["cross-reel"])
        self.assertFalse(cr.gate_verdict("Tarnhelm", sg)["pass"])


class TestV2380TheSameItemOnTwoPanelsIsAWitness(unittest.TestCase):
    """Konyo named the lifecycle this exists for: "i find it on the floor from farming.. and then
    its in my inventory and then its identified and then its seen and registerd also as a
    chronicle... so thats two witnesses in the same session with two diffrent reels and
    templates... so understand that too also as a scenario".

    MEASURED BEFORE THE CHANGE: floor -> inventory -> chronicle inside ONE session scored
    ['cross-frame'] and was HELD. witnesses() read lane, reel and frame and never surface.

    WHY IT IS A WITNESS: cross-frame is the SAME panel photographed twice, discounted precisely
    because one systematic misread repeats. The floor label, the inventory grid and the Chronicle
    list are three different layouts — a misread does not survive being re-rendered in a different
    template."""

    REEL = "reel_s_777_1"

    def _s(self, frame, loc):
        return {"reel": self.REEL, "frame": frame, "lane": "claude",
                "conf": 0.9, "loc": loc, "witness": "none"}

    def _loc_of(self, sg):
        return sg.get("loc")

    def _life(self):
        return [self._s("f_floor", "floor"), self._s("f_inv", "inventory"),
                self._s("f_chron", "chronicle")]

    def test_his_lifecycle_now_earns_a_second_witness(self):
        w = cr.witnesses(self._life(), surface_of=self._loc_of)
        self.assertIn("cross-surface", w)
        self.assertTrue(cr._gate_verdict_live("X", self._life(), surface_of=self._loc_of)["pass"])

    def test_the_SAME_surface_twice_is_still_one_witness(self):
        """The whole point of discounting repetition. Two looks at the stash are not two panels."""
        sg = [self._s("f1", "stash"), self._s("f2", "stash")]
        self.assertNotIn("cross-surface", cr.witnesses(sg, surface_of=self._loc_of))
        self.assertFalse(cr._gate_verdict_live("X", sg, surface_of=self._loc_of)["pass"])

    def test_an_UNKNOWN_surface_never_manufactures_a_witness(self):
        """The judge lane legitimately does not know where it looked — 84 names, zero locations.
        Unknown must not become evidence. [[unknown-stays-unknown]]"""
        sg = [self._s("f1", None), self._s("f2", None)]
        self.assertNotIn("cross-surface", cr.witnesses(sg, surface_of=self._loc_of))
        self.assertFalse(cr._gate_verdict_live("X", sg, surface_of=self._loc_of)["pass"])

    def test_ONE_known_surface_plus_ONE_unknown_is_still_one_witness(self):
        """The case that CAUGHT a bad sabotage. Two unknowns collapse to str(None)=='none' and
        look safe by accident; a known surface beside an unknown is where 'count it anyway'
        actually manufactures the second witness. Half-knowing where you looked is not two
        panels. [[unknown-stays-unknown]]"""
        sg = [self._s("f1", "stash"), self._s("f2", None)]
        self.assertNotIn("cross-surface", cr.witnesses(sg, surface_of=self._loc_of))
        self.assertFalse(cr._gate_verdict_live("X", sg, surface_of=self._loc_of)["pass"])

    def test_an_EMPTY_STRING_surface_is_not_a_surface(self):
        """A resolver that returns '' for 'I could not tell' must read as unknown, not as a
        distinct panel named nothing."""
        sg = [self._s("f1", "stash"), self._s("f2", "   ")]
        self.assertNotIn("cross-surface", cr.witnesses(sg, surface_of=self._loc_of))

    def test_with_NO_resolver_nothing_changes(self):
        """No caller is forced to change, and nothing silently starts passing."""
        self.assertEqual(cr.witnesses(self._life()), ["cross-frame"])
        self.assertFalse(cr._gate_verdict_live("X", self._life())["pass"])

    def test_a_resolver_that_THROWS_does_not_take_the_gate_with_it(self):
        def boom(_sg):
            raise RuntimeError("the timeline is unreadable")
        self.assertEqual(cr.witnesses(self._life(), surface_of=boom), ["cross-frame"])

    def test_it_reaches_the_gate_through_strict_gate(self):
        """The plumbing: control_app passes surface_of=_sighting_loc, and it must arrive."""
        gate = cr.strict_gate(surface_of=self._loc_of)
        self.assertTrue(gate("X", self._life()),
                        "surface_of does not reach witnesses() through strict_gate")


if __name__ == "__main__":
    unittest.main(verbosity=2)
