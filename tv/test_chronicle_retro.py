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
        self.d = tempfile.mkdtemp()
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
            return "chronicle-uniques" if "f0" in p or "f1.jpg" in p or "f2" in p or "f3" in p else None

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
