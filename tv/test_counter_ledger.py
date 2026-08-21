#!/usr/bin/env python3
"""The counter-ledger — the game's own list of what he does NOT have.

Every test here exists because the same check, written the obvious way, PASSED while being blind.
The first cut of `denied()` compared proposal names to roster names directly and reported "no
proposed name appears on the game's missing list (86 checked)". Zero of those 86 were roster
strings: the pipeline carries `M'avina's Caster`, the roster carries `M'avina's Caster (helm)`. A
comparison between two naming conventions agrees no matter what is in it.

So these tests pin the REACH of the guard, not just its verdict — and every branch is forced,
because a branch that has never run is a branch that is not there. [[feedback-blind-fixture-green-gate]]
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

import counter_ledger as cl  # noqa: E402
import chronicle_resolve as _res  # noqa: E402


def _reading(tmp, names, ms=1787307553811, name="sets_test.json"):
    os.makedirs(tmp, exist_ok=True)
    with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
        json.dump({"ledger": "sets", "reel": "reel_s_%d_9452" % ms,
                   "readAt": "2026-08-21T10:19:13.811000Z",
                   "rows": [{"piece": n} for n in names]}, fh)


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="counterledger-")
        self._old = os.environ.get("TV_REMAINING_DIR")
        os.environ["TV_REMAINING_DIR"] = self._tmp

    def tearDown(self):
        if self._old is None:
            os.environ.pop("TV_REMAINING_DIR", None)
        else:
            os.environ["TV_REMAINING_DIR"] = self._old


class TestTheGuardCanActuallyReachTheNames(TempDirCase):
    """THE DEFECT THAT MADE THIS FILE. Raw pipeline names vs suffixed roster names."""

    def test_a_bare_pipeline_name_is_folded_onto_its_suffixed_roster_piece(self):
        _reading(self._tmp, ["Natalya's Soul (claws)"])
        # exactly how the pipeline spells it in chron_evidence.json — no suffix
        out = cl.denied({"Natalya's Soul": [{"frame": "f_1787177277865.jpg"}]})
        self.assertEqual([d["name"] for d in out["denied"]], ["Natalya's Soul (claws)"],
                         "a bare name must fold onto its roster piece — comparing the two "
                         "conventions directly is what made the first cut always agree")

    def test_the_unfolded_comparison_would_have_missed_it(self):
        """Pin the failure itself, so the fix cannot be quietly undone."""
        ro = _res.load_set_roster()
        self.assertIsNone(_res.canonical("Natalya's Soul", ro) and None,
                          "sanity: canonical() resolves it")  # resolves, so `and None` -> None
        self.assertNotIn("Natalya's Soul", set(ro.values()),
                         "the bare name is NOT a roster string — which is exactly why a direct "
                         "set-membership test on it can never match")


class TestTimeOrderingProtectsARealFind(TempDirCase):
    """A Remaining page is one moment. He keeps playing. A denial must be ordered or it destroys
    the finds it exists to protect."""

    def test_a_sighting_older_than_the_page_is_denied(self):
        _reading(self._tmp, ["Natalya's Soul (claws)"], ms=1787307553811)
        out = cl.denied({"Natalya's Soul (claws)": [{"frame": "f_1787177277865.jpg"}]})
        self.assertEqual(len(out["denied"]), 1)
        self.assertEqual(out["superseded"], [])
        self.assertFalse(out["ok"])

    def test_a_sighting_NEWER_than_the_page_is_superseded_not_denied(self):
        _reading(self._tmp, ["Natalya's Soul (claws)"], ms=1787307553811)
        out = cl.denied({"Natalya's Soul (claws)": [{"frame": "f_1787999999999.jpg"}]})
        self.assertEqual(out["denied"], [],
                         "he found it AFTER the page was shot — denying it would delete a real find")
        self.assertEqual([d["name"] for d in out["superseded"]], ["Natalya's Soul (claws)"])
        self.assertTrue(out["ok"])
        self.assertIn("older than the fact", out["say"])

    def test_the_newest_sighting_decides_not_the_oldest(self):
        _reading(self._tmp, ["Natalya's Soul (claws)"], ms=1787307553811)
        out = cl.denied({"Natalya's Soul (claws)": [
            {"frame": "f_1787177277865.jpg"}, {"frame": "f_1787999999999.jpg"}]})
        self.assertEqual(out["denied"], [],
                         "one look after the page is enough — a stale sighting alongside a fresh "
                         "one must not drag the row back into a denial")

    def test_the_frame_beats_the_reel_because_a_reel_is_a_whole_session(self):
        # reel STARTED before the page, but this frame was captured after it.
        _reading(self._tmp, ["Natalya's Soul (claws)"], ms=1787307553811)
        out = cl.denied({"Natalya's Soul (claws)": [
            {"reel": "s_1787177267889_92273", "frame": "f_1787999999999.jpg"}]})
        self.assertEqual(out["denied"], [],
                         "a reel id is when the session STARTED; the frame is when the item was "
                         "actually on screen, and it is the frame that orders the evidence")


class TestUnknownStaysUnknown(TempDirCase):
    def test_no_reading_is_not_agreement(self):
        out = cl.denied({"Anything": [{"frame": "f_1787177277865.jpg"}]})
        self.assertIsNone(out["ok"], "no page on file must be UNKNOWN, never a pass")
        self.assertIn("not the same as", out["say"])
        self.assertIsNone(cl.load("sets"))
        self.assertIsNone(cl.missing_names("sets"))

    def test_a_sighting_with_no_readable_time_is_flagged_not_denied(self):
        _reading(self._tmp, ["Natalya's Soul (claws)"])
        out = cl.denied({"Natalya's Soul (claws)": [{"frame": "screenshot.png"}]})
        self.assertEqual(out["denied"], [])
        self.assertEqual([d["name"] for d in out["undated"]], ["Natalya's Soul (claws)"])
        self.assertIn("not evidence", out["say"])

    def test_an_empty_rows_file_is_a_failed_recording_not_a_finished_grail(self):
        os.makedirs(self._tmp, exist_ok=True)
        with open(os.path.join(self._tmp, "sets_empty.json"), "w", encoding="utf-8") as fh:
            json.dump({"ledger": "sets", "reel": "reel_s_1787307553811_9452", "rows": []}, fh)
        self.assertIsNone(cl.load("sets"),
                         "zero rows would mean 'he is missing nothing' — a huge claim. A recording "
                         "that produced no rows is a recording that failed.")

    def test_an_unparseable_stamp_gives_age_None_never_zero(self):
        self.assertIsNone(cl._age_days("not a date"))
        self.assertIsNone(cl._age_days(None))


class TestTheArithmeticThatStartedIt(TempDirCase):
    def test_118_plus_19_overshoots_135_by_exactly_two(self):
        _reading(self._tmp, ["p%d" % i for i in range(19)])
        a = cl.arithmetic(118, 135)
        self.assertEqual(a["surplus"], 2)
        self.assertEqual(a["impliedFound"], 116)
        self.assertFalse(a["ok"])
        self.assertIn("2 row(s)", a["say"])

    def test_116_plus_19_closes_the_account(self):
        _reading(self._tmp, ["p%d" % i for i in range(19)])
        a = cl.arithmetic(116, 135)
        self.assertTrue(a["ok"])
        self.assertEqual(a["surplus"], 0)

    def test_a_SHORTFALL_reads_as_unaccounted_not_double_counted(self):
        _reading(self._tmp, ["p%d" % i for i in range(19)])
        a = cl.arithmetic(110, 135)
        self.assertFalse(a["ok"])
        self.assertIn("SHORT", a["say"])
        self.assertIn("unaccounted", a["say"])

    def test_no_reading_refuses_the_arithmetic_rather_than_passing_it(self):
        a = cl.arithmetic(118, 135)
        self.assertIsNone(a["ok"])


class TestAgainstTheRealRosterAndTheRealReading(unittest.TestCase):
    """No fixture — his actual files. A guard proven only on invented data is proven on invented
    data. [[feedback-blind-fixture-green-gate]]"""

    def test_the_roster_is_135_and_the_recorded_page_is_19_and_they_subtract_to_116(self):
        ro = _res.load_set_roster()
        self.assertEqual(len(ro), 135, "his total, from the data rather than from a claim")
        r = cl.load("sets")
        self.assertIsNotNone(r, "the 2026-08-21 Remaining reading must be on file")
        self.assertEqual(r["count"], 19)
        owned, meta = cl.owned_by_subtraction(ro)
        self.assertTrue(meta["exact"], "unresolved rows make the subtraction inexact: %s"
                        % meta["unresolved"])
        self.assertEqual(len(owned), 116)

    def test_every_recorded_missing_row_is_a_real_roster_piece(self):
        ro = _res.load_set_roster()
        r = cl.load("sets")
        bad = [n for n in r["names"] if _res.canonical(n, ro) is None]
        self.assertEqual(bad, [], "a missing row that is not a roster piece would silently shrink "
                                  "the subtraction and inflate the owned count")

    def test_the_live_evidence_denies_exactly_the_row_found_by_hand(self):
        ev_path = os.path.join(HERE, "chron_evidence.json")
        if not os.path.isfile(ev_path):
            self.skipTest("no chron_evidence.json on this machine")
        with open(ev_path, encoding="utf-8") as fh:
            ev = json.load(fh)
        out = cl.denied(ev.get("sets") or {})
        self.assertEqual([d["name"] for d in out["denied"]], ["Natalya's Soul (claws)"],
                         "this is the row found by eye on 2026-08-21; the guard must find it "
                         "without a hand")


class TestANotFoundReadingExpires(unittest.TestCase):
    """THE ONE THAT COST A WRONG ANSWER TO HIS FACE.

    2026-08-21: I told Konyo that **12 of his 36 proposed set pieces were ones the game shows as
    not-found**. Three of them carried First Found dates on his newest reel — those readings were
    simply OLD, describing a moment before he owned the item. The real number was one.

    A not-found reading is not a fact about an item. It is a fact about an item AT ONE MOMENT, and
    it expires the instant a later look disagrees. The code already SAID this, in a comment, right
    above the line that compared the two as flat membership anyway.
    """

    F_OLD = {"frame": "f_1787177277865.jpg"}
    F_NEW = {"frame": "f_1787999999999.jpg"}

    def test_an_older_not_found_does_not_contradict_a_newer_find(self):
        r = cl.resolve_contested([self.F_NEW], [self.F_OLD])
        self.assertEqual(r["verdict"], "found")
        self.assertIn("expired", r["say"])

    def test_a_newer_not_found_IS_a_real_contradiction(self):
        r = cl.resolve_contested([self.F_OLD], [self.F_NEW])
        self.assertEqual(r["verdict"], "not-found")

    def test_the_same_frame_read_both_ways_cannot_be_ordered_away(self):
        r = cl.resolve_contested([self.F_OLD], [self.F_OLD])
        self.assertEqual(r["verdict"], "same-moment")

    def test_an_undatable_side_is_never_resolved_by_guess(self):
        self.assertEqual(cl.resolve_contested([{"frame": "x.png"}], [self.F_OLD])["verdict"],
                         "undatable")
        self.assertEqual(cl.resolve_contested([self.F_OLD], [{"frame": "x.png"}])["verdict"],
                         "undatable")
        self.assertEqual(cl.resolve_contested([self.F_OLD], [])["verdict"], "undatable")

    def test_resolve_all_drops_the_expired_ones_from_a_contested_count(self):
        """The padding is the defect. A contested list swollen with expired readings is exactly how
        a wrong number gets stated with a straight face."""
        prop = {"sets": {"A": [self.F_NEW], "B": [self.F_OLD]},
                "notFound": {"sets": ["A", "B"]},
                "notFoundSeen": {"sets": {"A": [self.F_OLD], "B": [self.F_NEW]}}}
        r = cl.resolve_all(prop)["sets"]
        self.assertEqual(r["A"]["verdict"], "found", "A was found AFTER the not-found look")
        self.assertEqual(r["B"]["verdict"], "not-found")
        real = [n for n, v in r.items() if v["verdict"] != "found"]
        self.assertEqual(real, ["B"],
                         "one real contradiction, not two — this is the 1-vs-12 defect in miniature")

    def test_his_real_banked_evidence_is_reported_UNDATABLE_not_quoted(self):
        """No fixture. The actual file my wrong claim was made from."""
        ev_path = os.path.join(HERE, "chron_evidence.json")
        if not os.path.isfile(ev_path):
            self.skipTest("no chron_evidence.json on this machine")
        with open(ev_path, encoding="utf-8") as fh:
            ev = json.load(fh)
        res = cl.resolve_all(ev)
        verdicts = {v["verdict"] for led in res.values() for v in led.values()}
        self.assertEqual(verdicts, {"undatable"},
                         "this evidence was banked before not-found receipts existed, so NOTHING "
                         "in it can be ordered — and the engine must say so rather than produce a "
                         "confident number from it")


if __name__ == "__main__":
    unittest.main(verbosity=2)
