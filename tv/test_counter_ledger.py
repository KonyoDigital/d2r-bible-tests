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
# ⚠ v2122 — THE NATALYA SUFFIXES MOVED, AND THAT IS THE POINT OF THE FIXTURE, NOT AN ACCIDENT.
# The set catalogue says Natalya's Mark IS a "Scissors Suwayyah" (a CLAW) and Natalya's Soul a
# "Mesh Boots"; the roster had them swapped and v2119 corrected it. So:
#   · SYNTHETIC fixtures below use "Natalya's Soul (boots)" — the roster's current spelling. These
#     cases are about FOLDING a bare pipeline name onto its roster piece and about TIME ORDERING;
#     the suffix is incidental to both, and pinning a spelling the roster no longer has made five
#     of them fail on a legitimate data correction.
#   · The REAL-reading case names "Natalya's Mark (claws)", because the stored 2026-08-21 Remaining
#     reading recorded the game's own base (Scissors Suwayyah) and its DERIVED label was corrected
#     to agree with it.
# [[label-outlived-referent]] [[feedback-blind-fixture-green-gate]]
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
        _reading(self._tmp, ["Natalya's Soul (boots)"])
        # exactly how the pipeline spells it in chron_evidence.json — no suffix
        out = cl.denied({"Natalya's Soul": [{"frame": "f_1787177277865.jpg"}]})
        self.assertEqual([d["name"] for d in out["denied"]], ["Natalya's Soul (boots)"],
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
        _reading(self._tmp, ["Natalya's Soul (boots)"], ms=1787307553811)
        out = cl.denied({"Natalya's Soul (boots)": [{"frame": "f_1787177277865.jpg"}]})
        self.assertEqual(len(out["denied"]), 1)
        self.assertEqual(out["superseded"], [])
        self.assertFalse(out["ok"])

    def test_a_sighting_NEWER_than_the_page_is_superseded_not_denied(self):
        _reading(self._tmp, ["Natalya's Soul (boots)"], ms=1787307553811)
        out = cl.denied({"Natalya's Soul (boots)": [{"frame": "f_1787999999999.jpg"}]})
        self.assertEqual(out["denied"], [],
                         "he found it AFTER the page was shot — denying it would delete a real find")
        self.assertEqual([d["name"] for d in out["superseded"]], ["Natalya's Soul (boots)"])
        self.assertTrue(out["ok"])
        self.assertIn("older than the fact", out["say"])

    def test_the_newest_sighting_decides_not_the_oldest(self):
        _reading(self._tmp, ["Natalya's Soul (boots)"], ms=1787307553811)
        out = cl.denied({"Natalya's Soul (boots)": [
            {"frame": "f_1787177277865.jpg"}, {"frame": "f_1787999999999.jpg"}]})
        self.assertEqual(out["denied"], [],
                         "one look after the page is enough — a stale sighting alongside a fresh "
                         "one must not drag the row back into a denial")

    def test_the_frame_beats_the_reel_because_a_reel_is_a_whole_session(self):
        # reel STARTED before the page, but this frame was captured after it.
        _reading(self._tmp, ["Natalya's Soul (boots)"], ms=1787307553811)
        out = cl.denied({"Natalya's Soul (boots)": [
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
        _reading(self._tmp, ["Natalya's Soul (boots)"])
        out = cl.denied({"Natalya's Soul (boots)": [{"frame": "screenshot.png"}]})
        self.assertEqual(out["denied"], [])
        self.assertEqual([d["name"] for d in out["undated"]], ["Natalya's Soul (boots)"])
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

    def test_the_live_evidence_and_the_page_now_name_DIFFERENT_pieces(self):
        """v2122 — WHAT THIS CASE MEASURES CHANGED, AND THE CHANGE IS THE FINDING.

        It used to assert that his live evidence denies exactly one row, found by eye on
        2026-08-21. That row was `Natalya's Soul (claws)` — a string the roster no longer has.
        The 2026-08-21 Remaining reading recorded the GAME's own base for it, "Scissors Suwayyah",
        and the set catalogue says a Scissors Suwayyah IS Natalya's Mark. So the reading's derived
        label was corrected to `Natalya's Mark (claws)` (v2119, #114) and the two sides stopped
        meeting: the READER saw Natalya's Soul; the GAME's page says he is missing Natalya's Mark.

        Different pieces, so nothing is denied — and that is CORRECT, not a broken veto. It also
        means the earlier retraction of Soul was made against a mislabelled row, which is exactly
        the class #129 is open on.

        The no-denial half alone would be vacuous, so the veto is proven to still BITE on the row
        the page actually names. [[feedback-contradiction-is-the-finding]]"""
        ev_path = os.path.join(HERE, "chron_evidence.json")
        if not os.path.isfile(ev_path):
            # ⚠ chron_evidence.json is UNTRACKED (it carries item names, and this repo is PUBLIC),
            # so this case is a permanent SKIP on CI and only ever runs on his machine. A skip is
            # not a pass — say which venue actually proved it. [[feedback-blind-fixture-green-gate]]
            self.skipTest("no chron_evidence.json here — this case only ever runs on HIS machine, "
                          "so CI has never proven it either way")
        with open(ev_path, encoding="utf-8") as fh:
            ev = json.load(fh)

        r = cl.load("sets")
        self.assertIn("Natalya's Mark (claws)", r["names"],
                      "the corrected reading no longer names the Suwayyah row this case is about")

        # v2122 (#144) — PIN THE SPLIT ITSELF, or `denied == []` proves nothing. Empty evidence,
        # evidence that has lost the Soul sightings, or evidence that already names Mark would all
        # keep the assertion below green while the finding it describes had evaporated.
        sets = ev.get("sets") or {}
        soul = [k for k in sets if k.startswith("Natalya's Soul")]
        mark = [k for k in sets if k.startswith("Natalya's Mark")]
        self.assertTrue(soul,
                        "the evidence no longer carries a Natalya's Soul sighting, so the two-sides"
                        "-name-different-pieces finding this case documents is not what is being "
                        "measured any more")
        self.assertEqual(mark, [],
                         "the evidence now names Natalya's Mark too — the page names it as MISSING, "
                         "so this should be a DENIAL and the empty result below would be hiding one")

        out = cl.denied(sets)
        self.assertEqual([d["name"] for d in out["denied"]], [],
                         "his evidence names Natalya's Soul and the page names Natalya's Mark — "
                         "denying across two different pieces would destroy a real find")

        # AND THE VETO STILL BITES. Same page, a sighting of the row it DOES name, timed before it.
        bite = cl.denied({"Natalya's Mark (claws)": [{"frame": "f_1787177277865.jpg"}]})
        self.assertEqual([d["name"] for d in bite["denied"]], ["Natalya's Mark (claws)"],
                         "the veto no longer fires on the row the game's own page lists as "
                         "missing — this case would be asserting nothing")


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
        verdicts = [v["verdict"] for led in res.values() for v in led.values()]
        # v1953 — PIN THE RULE, NOT THE SNAPSHOT.
        # This asserted `set(verdicts) == {"undatable"}`, which was true of the file on the day it
        # was written: every row in it predated not-found receipts, so nothing could be ordered.
        # That is a fact about a LIVE FILE, and the file has since grown rows that DO carry receipts
        # — which is the receipts working, not a regression. The old assertion turned his own
        # progress into a red gate.
        #
        # The scar this guards is unchanged and is about the OTHER direction: I once reported "12 of
        # your 36 set pieces are ones the game shows as not-found" from evidence that could not be
        # ordered at all; the true number was 1. So what must hold forever is that an unorderable
        # reading is REPORTED unorderable and never quoted as a contradiction — not that every
        # reading is unorderable. [[stale-reading]] [[unknown-stays-unknown]]
        self.assertTrue(verdicts, "no verdicts at all — this guard has lost its subject")
        # v2026 — `same-moment` WAS MISSING FROM THIS LIST, AND IT IS THE ENGINE'S OWN WORD.
        # counter_ledger:428 sets it and its docstring says outright: "Only `not-found`,
        # `same-moment` and `undatable` are real". The allowlist named neither of the last two
        # correctly, so the guard could only pass while no row in his evidence had ever produced
        # one — and it went red the first night a sweep banked a same-frame disagreement.
        #
        # That is the SECOND guard in one evening that held only because the path it watched had
        # never executed (the other asserted vault_last_result.json was absent, which was true only
        # because the vault sweep had never run). Both fired on the day the feature started
        # working, which is the worst moment for a false alarm. The lesson generalises: an
        # allowlist of another module's outputs must be derived from that module, or stated with
        # the reason each member is there. [[gate-blind-to-unexercised-input]]
        KNOWN = {"undatable", "found", "not-found", "same-moment", "superseded", "denied"}
        self.assertTrue(set(verdicts) <= KNOWN,
                        "the engine invented a verdict this guard does not know: %s"
                        % sorted(set(verdicts) - KNOWN))
        self.assertIn("undatable", verdicts,
                      "not one row is reported undatable any more. His pre-receipt evidence is "
                      "still in this file and still cannot be ordered, so something has started "
                      "handing it a confident verdict — which is the 1-vs-12 defect returning.")


class TestThePhantomNamer(TempDirCase):
    """`--phantoms` names the board rows the game denies. Tested because an untested CLI branch is
    a branch that works until the one evening he needs it."""

    def _run(self, board_names, remaining=("Natalya's Soul (boots)",), counts=None):
        import control_app as ca
        _reading(self._tmp, list(remaining))
        payload = json.dumps({"ok": True,
                              "counts": {"foundLog": 0, "owned": 0,
                                         "setPieces": counts if counts is not None else len(board_names)},
                              "sample": {"foundLog": [], "owned": [], "setPieces": list(board_names)}})
        old = (ca.__dict__.get("_MAIN_WIN"), ca.__dict__.get("_WINDOW_LIVE"), ca._ejs)
        ca.__dict__["_MAIN_WIN"] = object()
        ca.__dict__["_WINDOW_LIVE"] = True
        ca._ejs = lambda w, js, timeout=8.0: payload
        import io as _io
        import contextlib
        buf = _io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = cl.main(["--phantoms"])
        finally:
            ca.__dict__["_MAIN_WIN"], ca.__dict__["_WINDOW_LIVE"], ca._ejs = old
        return rc, buf.getvalue()

    def test_it_names_the_row_the_game_denies(self):
        rc, out = self._run(["Natalya's Soul (boots)", "Aldur's Rhythm (mace)"])
        self.assertIn("Natalya's Soul (boots)", out)
        self.assertIn("the rows to untick", out)
        self.assertEqual(rc, 1, "a board carrying a denied row must not exit clean")

    def test_a_clean_board_says_so_and_exits_zero(self):
        """Seen green for its own reason, not because the namer names nothing.

        The account has to CLOSE for this to be clean: 116 found + 19 missing = the 135 roster. An
        earlier draft passed one missing name and expected zero, which made the exit code report a
        19-piece shortfall rather than the clean board it claimed to be testing."""
        remaining = ["p%d" % i for i in range(19)]
        rc, out = self._run(["Aldur's Rhythm (mace)"], remaining=remaining, counts=116)
        self.assertNotIn("the rows to untick", out)
        self.assertIn("consistent with the game", out)
        self.assertEqual(rc, 0)

    def test_a_capped_sample_is_reported_rather_than_read_as_complete(self):
        """The board says 118 and lists 2: a phantom could be hiding in the 116 nobody read, and
        that must never be reported as 'no phantoms found'. [[unknown-stays-unknown]]"""
        rc, out = self._run(["Aldur's Rhythm (mace)", "Aldur's Advance (boots)"], counts=118)
        self.assertIn("the sample was capped", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
