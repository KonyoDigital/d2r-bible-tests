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

    def test_sweeping_writes_nothing_anywhere(self):
        # ★ READ-ONLY UNTIL APPLY, proven structurally: the module has no write/open-for-write path
        src = open(os.path.join(os.path.dirname(cr.__file__), "chronicle_retro.py"),
                   encoding="utf-8").read()
        # no write-mode open, no delete, no rename — the module can only ever READ
        self.assertNotRegex(src, r'open\([^)]*["\'][wax]')
        for forbidden in ("os.remove", "os.rename", "os.unlink", "shutil.", "json.dump("):
            self.assertNotIn(forbidden, src, forbidden + " has no business in a read-only sweep")


if __name__ == "__main__":
    unittest.main(verbosity=2)
