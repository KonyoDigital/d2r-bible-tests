"""v1511 — the retro sweep's laws, as tests.

Konyo's #1 priority in this arc is RETRO: the sealed reels already contain every Chronicle screen he
has opened on camera. What makes that safe to automate is not the reading — it is the three laws:
read-only until Apply, merge-max, and pay-for-runs. Each has a test here that fails loudly if it is
ever relaxed."""

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
        self.assertIn("already-swept", notes)

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
        self.assertIn("already-swept", notes, "the skipped reel vanished from the report: %s" % notes)
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



if __name__ == "__main__":
    unittest.main(verbosity=2)
