#!/usr/bin/env python3
"""Guards for lane health. Every one asserts a REFUSAL as well as a pass — the thing being replaced
is a watchdog that stayed silent for five days, so silence must never be a pass here."""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lane_health as LH

HOUR = 3600000.0


class _Tree(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="lane-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self._here = LH.HERE
        LH.HERE = self.root
        self.addCleanup(setattr, LH, "HERE", self._here)
        self.now = 1_000_000 * HOUR

    def _write(self, name, blob):
        with io.open(os.path.join(self.root, name), "w", encoding="utf-8") as fh:
            json.dump(blob, fh)

    def _seal(self, n, hours_ago):
        return {"s_%d" % i: {"ts": self.now - hours_ago * HOUR, "rows": 1} for i in range(n)}


class TestFreshness(_Tree):
    def test_a_lane_that_worked_recently_is_FRESH(self):
        self._write("chronicle_swept.json", self._seal(3, 2))
        self.assertEqual(LH.lane("chronicle", self.now)["state"], "fresh")

    def test_a_lane_past_its_threshold_is_STALLED_and_says_how_long(self):
        self._write("vault_swept.json", self._seal(8, 136.7))
        r = LH.lane("vault", self.now)
        self.assertEqual(r["state"], "stalled")
        self.assertAlmostEqual(r["ageHours"], 136.7, places=0)
        self.assertIn("STOPPED", r["why"])

    def test_an_UNREADABLE_store_is_UNKNOWN_never_healthy(self):
        # ⚠ the whole point: "cannot tell" must not read the same as "fine"
        with io.open(os.path.join(self.root, "vault_swept.json"), "w", encoding="utf-8") as fh:
            fh.write("{not json")
        r = LH.lane("vault", self.now)
        self.assertEqual(r["state"], "unknown")
        self.assertIn("never healthy", r["why"])

    def test_a_MISSING_store_is_UNKNOWN_not_fresh(self):
        self.assertEqual(LH.lane("vault", self.now)["state"], "unknown")

    def test_seals_with_NO_TIMESTAMP_are_UNKNOWN_not_fresh(self):
        # a lane with 40 sealed rows and no clock cannot answer "how long ago"
        self._write("vault_swept.json", {"s_%d" % i: {"rows": 1} for i in range(40)})
        r = LH.lane("vault", self.now)
        self.assertEqual(r["state"], "unknown")
        self.assertIn("unanswerable", r["why"])


class TestDivergenceIsTheCorroborator(_Tree):
    def test_one_lane_ahead_of_the_other_is_DIVERGED_and_names_the_deleter(self):
        self._write("chronicle_swept.json", self._seal(36, 49))
        self._write("vault_swept.json", {"s_0": {"ts": self.now, "rows": 1}})
        d = LH.divergence("chronicle", "vault")
        self.assertEqual(d["state"], "diverged")
        self.assertEqual(d["onlyInFirst"], 35)
        self.assertIn("frame deleter", d["why"])

    def test_lanes_covering_the_same_sessions_are_ALIGNED(self):
        same = self._seal(5, 1)
        self._write("chronicle_swept.json", same)
        self._write("vault_swept.json", same)
        self.assertEqual(LH.divergence("chronicle", "vault")["state"], "aligned")

    def test_divergence_with_an_unreadable_side_is_UNKNOWN(self):
        self._write("chronicle_swept.json", self._seal(3, 1))
        self.assertEqual(LH.divergence("chronicle", "vault")["state"], "unknown")

    def test_divergence_is_DIRECTIONAL(self):
        # vault ahead of chronicle is a different fact and must not read as the same defect
        self._write("chronicle_swept.json", {"s_0": {"ts": self.now, "rows": 1}})
        self._write("vault_swept.json", self._seal(9, 1))
        self.assertEqual(LH.divergence("chronicle", "vault")["state"], "aligned")
        self.assertEqual(LH.divergence("vault", "chronicle")["state"], "diverged")


class TestTheReportRefusesToBeGreenOnAnyProblem(_Tree):
    def test_everything_fresh_and_aligned_is_ok(self):
        same = self._seal(4, 1)
        self._write("chronicle_swept.json", same)
        self._write("vault_swept.json", same)
        self.assertTrue(LH.report(self.now)["ok"])

    def test_ONE_stalled_lane_makes_the_whole_report_not_ok(self):
        self._write("chronicle_swept.json", self._seal(4, 1))
        self._write("vault_swept.json", self._seal(4, 200))
        # v2308 — say what this fixture owes, or report() asks the real machine and a
        # deliberately stalled lane reads as idle on a tree where nothing is owed.
        self.assertFalse(LH.report(self.now, owed={"chronicle": 2, "vault": 2})["ok"])

    def test_a_DIVERGENCE_ALONE_makes_it_not_ok_even_when_both_lanes_are_fresh(self):
        # ⚠ this is the exact shape that hid the five-day stall: each lane correct on its own
        self._write("chronicle_swept.json", self._seal(9, 1))
        self._write("vault_swept.json", {"s_0": {"ts": self.now, "rows": 1}})
        rep = LH.report(self.now)
        self.assertTrue(all(l["state"] == "fresh" for l in rep["lanes"].values()))
        self.assertFalse(rep["ok"], "both lanes fresh but diverged, and the report called it ok")

    def test_it_writes_nothing(self):
        import inspect
        src = inspect.getsource(LH)
        for forbidden in ('open(', "os.remove", "unlink", "rmtree"):
            if forbidden == 'open(' and 'io.open' in src:
                continue          # io.open for READING is the module's whole job
            self.assertNotIn(forbidden, src, "lane_health must stay a reader; found %r" % forbidden)
        self.assertNotIn('"w"', src, "lane_health opened something for writing")



class TestIdleIsNotStopped(_Tree):
    """★ A LANE WITH NOTHING TO DO IS NOT A LANE THAT STOPPED.

    lane() measured ONE thing — how long since work last happened — so a lane that had swept
    everything reported the same "STOPPED" as a broken one. MEASURED on his console 2026-08-30,
    two checks of the same doctor contradicting each other in the same breath:
        reel extract      ok       all 28 reel(s) have been read
        extraction lanes  missing  chronicle: last did work 63.5 h ago -- this lane has STOPPED
    And it mattered the moment it was fixed: with owed counted, the chronicle lane is IDLE (0 owed)
    while the VAULT lane is genuinely STALLED with 2 reels and 452 MB it has never read. Those two
    had been telling the same story.
    """

    def test_stale_with_nothing_owed_is_IDLE(self):
        self._write("chronicle_swept.json", self._seal(36, 64.0))
        r = LH.lane("chronicle", self.now, owed=0)
        self.assertEqual(r["state"], "idle")
        self.assertIn("IDLE, not stopped", r["why"])
        self.assertNotIn("STOPPED", r["why"])

    def test_stale_with_work_owed_is_still_STALLED(self):
        self._write("vault_swept.json", self._seal(8, 151.5))
        r = LH.lane("vault", self.now, owed=2)
        self.assertEqual(r["state"], "stalled")
        self.assertIn("STOPPED", r["why"])

    def test_an_UNCOUNTED_lane_is_STALLED_and_says_idle_could_not_be_ruled_in(self):
        """⚠ THE LAW THIS WHOLE CHANGE TURNS ON. "nothing was owed" and "nobody counted" must never
        reach the same box, and the cheap wrong version of this fix — treat missing as zero — would
        have silenced every genuinely stalled lane on any venue that cannot count."""
        self._write("vault_swept.json", self._seal(8, 151.5))
        r = LH.lane("vault", self.now, owed=None)
        self.assertEqual(r["state"], "stalled")
        self.assertIn("IDLE cannot be ruled in", r["why"])

    def test_a_FRESH_lane_is_never_relabelled_by_the_owed_count(self):
        self._write("chronicle_swept.json", self._seal(3, 2))
        for owed in (0, 2, None):
            self.assertEqual(LH.lane("chronicle", self.now, owed=owed)["state"], "fresh")

    def test_the_report_is_not_red_merely_because_a_lane_is_idle(self):
        self._write("chronicle_swept.json", self._seal(36, 64.0))
        self._write("vault_swept.json", self._seal(8, 2.0))
        rep = LH.report(self.now)
        ch = rep["lanes"]["chronicle"]
        # ⚠ assert on the LANE'S OWN sentence, never on the word "chronicle" anywhere in why:
        # the first cut did that and caught the DIVERGENCE line ("28 session(s) the chronicle lane
        # covered that vault never did"), which is a different and entirely real problem. A guard
        # that matches a substring of an unrelated finding is measuring the wrong thing.
        if ch["state"] == "idle":
            self.assertNotIn(ch["why"], rep["why"],
                             "an idle lane is healthy and must not be listed as a problem")
            self.assertIn("IDLE, not stopped", ch["why"])




class TestTheCorroboratorCanSayALIGNED(_Tree):
    """★ A DIVERGENCE CHECK THAT HAS NEVER BEEN SEEN SAY "ALIGNED" HAS NEVER BEEN PROVEN ABLE TO.

    MEASURED on his tree 2026-08-30: chronicle_swept.json keys carry a `reel_` prefix and
    vault_swept.json keys do not, and divergence() differenced them raw. It reported 36 diverged
    where the truth was 20 — and 8 reels covered by BOTH lanes were counted as diverged purely
    because of the spelling. Being wrong by 16 was the small half. The large half: the difference
    was non-empty BY CONSTRUCTION, so this check could never report agreement on any tree, which
    makes its red mean nothing at all. [[feedback-blind-fixture-green-gate]]
    """

    def _ids(self, ids):
        """A sealed store keyed by EXACTLY these ids — the point of these tests is the spelling,
        so the fixture may not go through a helper that invents its own keys."""
        return {i: {"ts": self.now - HOUR, "rows": 1} for i in ids}

    def test_the_same_sessions_in_BOTH_dialects_read_as_aligned(self):
        self._write("chronicle_swept.json", self._ids(["reel_s_1_a", "reel_s_2_b"]))
        self._write("vault_swept.json", self._ids(["s_1_a", "s_2_b"]))
        d = LH.divergence("chronicle", "vault")
        self.assertEqual(d["state"], "aligned",
                         "the same two sessions, spelled the two ways the real stores spell them, "
                         "must not read as diverged: %s" % d.get("why"))

    def test_a_REAL_gap_still_diverges(self):
        self._write("chronicle_swept.json", self._ids(["reel_s_1_a", "reel_s_2_b"]))
        self._write("vault_swept.json", self._ids(["s_1_a"]))
        d = LH.divergence("chronicle", "vault")
        self.assertEqual(d["state"], "diverged")
        self.assertIn("1 session", d["why"])

    def test_the_normaliser_is_idempotent_and_leaves_bare_ids_alone(self):
        self.assertEqual(LH._sid("reel_s_1_a"), "s_1_a")
        self.assertEqual(LH._sid("s_1_a"), "s_1_a")
        self.assertEqual(LH._sid(LH._sid("reel_s_1_a")), "s_1_a")



if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
