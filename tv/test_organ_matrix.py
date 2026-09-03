"""A3 — the surface × organ matrix may report what it measured, and nothing else.

⚠⚠ THE TABLE HE WAS SHOWN WAS MOSTLY EMPTY, and the empty cells were not all the same thing. His
ask was to fix the gaps "or honestly mark them as not having them" — so the danger here is not an
incomplete matrix, it is a matrix that FILLS ITSELF IN. A cell claiming coverage nobody
demonstrated is worse than the blank he was already looking at, because the blank told the truth.

Three states must stay apart, and each was a real mistake before it was a rule:
  COVERED   the organ's own output NAMES this surface
  MISNAMED  the organ IS watching it under a different string — `runeword` against
            `chronicle.runeword`. Reporting these as ABSENT is HOW the table came to look empty:
            9 of them, measured. Not holes; a join nobody made.
  ABSENT    the organ ran, answered, and does not name it
  UNKNOWN   the organ could not be asked AT ALL — console_doctor has no report(). An organ nobody
            can ask has not been shown to miss anything, and has not been shown to do anything.

These assert the LAWS, never the counts: coverage must be demonstrable, the states must not
collapse, and an unaskable organ must never read as an absence.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable  # noqa: E402

enable()

import organ_matrix as OM  # noqa: E402


class ItNeverInventsCoverage(unittest.TestCase):

    def test_every_COVERED_cell_is_backed_by_the_organ_naming_it(self):
        """The one claim that must never be free. Re-derive each COVERED cell from the organ."""
        cov = OM.organ_coverage()
        rows, _why = OM.matrix()
        for r in rows:
            for organ, cell in r["cells"].items():
                if cell != OM.COVERED:
                    continue
                names, _w = cov.get(organ, (None, ""))
                self.assertIsNotNone(
                    names, "%s is COVERED by %s, but that organ could not be asked at all"
                    % (r["surface"], organ))
                self.assertIn(
                    r["surface"], names,
                    "%s is reported COVERED by %s and that organ does not name it. A matrix that "
                    "fills itself in is worse than the empty one he was shown."
                    % (r["surface"], organ))

    def test_an_unaskable_organ_is_UNKNOWN_everywhere_and_never_ABSENT(self):
        cov = OM.organ_coverage()
        rows, _why = OM.matrix()
        for organ, (names, _w) in cov.items():
            if names is not None:
                continue
            for r in rows:
                self.assertEqual(
                    r["cells"][organ], OM.UNKNOWN,
                    "%s could not be asked, yet %s reads %s for it. Nobody-could-ask and "
                    "it-does-not-cover-this are different facts, and collapsing them accuses an "
                    "organ of a gap that was never measured."
                    % (organ, r["surface"], r["cells"][organ]))

    def test_MISNAMED_is_kept_apart_from_ABSENT(self):
        """⚠ WITHOUT THIS THE MATRIX LIES BY OMISSION. 9 cells are a join nobody made."""
        rows, _why = OM.matrix()
        states = {c for r in rows for c in r["cells"].values()}
        self.assertTrue(
            states <= {OM.COVERED, OM.ABSENT, OM.UNKNOWN, OM.MISNAMED},
            "an unexpected cell state appeared: %s" % (states,))
        # ⚠⚠ AND IT MUST ASSERT THEY EXIST WHEN THEY SHOULD. The first version only validated
        # cells ALREADY marked MISNAMED, so collapsing every one of them into ABSENT passed
        # vacuously — proven by sabotage, which went GREEN. A guard that checks the label it is
        # given, and never that the label was applied, cannot fail in the direction that matters.
        # This re-derives the pairs from the organs and demands each one be MISNAMED, not ABSENT.
        cov = OM.organ_coverage()
        should = []
        for r in rows:
            for organ, cell in r["cells"].items():
                names, _w = cov.get(organ, (None, ""))
                if names is None:
                    continue
                if r["surface"] in names:
                    continue
                if OM._same_thing(r["surface"], names):
                    should.append((r["surface"], organ, cell))
        # ⚠⚠ THIS ASSERTION FIRED, AND IT WAS RIGHT TO. v2496 made the corroborator keep the lane
        # it learned each name in, which turned all nine live MISNAMED cells into COVERED — so the
        # live world stopped containing an example and this test lost its subject, exactly as its
        # own message predicted. The message said RETIRE IT DELIBERATELY rather than let it pass
        # on an empty set, and neither of those is right here: the classification law still has to
        # hold the next time two vocabularies drift apart.
        #
        # So the subject is CONSTRUCTED instead of borrowed from live data. A guard that can only
        # fire while his console happens to contain an instance is blind the moment it does not —
        # and "the bug is fixed" is precisely when that blindness arrives.
        # [[gate-blind-to-unexercised-input]]
        self.assertEqual(
            OM._same_thing("chronicle.runeword", {"runewords"}), True,
            "the resolver no longer sees a lane-qualified surface and a bare plural as the same "
            "thing, so nothing in this table could ever be classified MISNAMED again")
        self.assertEqual(
            OM._same_thing("chronicle.runeword", {"orphans", "board_join"}), False,
            "the resolver matches names that have nothing to do with each other, which would turn "
            "ABSENT into MISNAMED everywhere and hide real holes")
        if not should:
            # not a failure — a state worth printing, so a future reader knows the live count is
            # zero because the join was MADE, not because the check stopped looking
            print("\n    (no live MISNAMED cells: the nine route surfaces were joined in v2496; "
                  "the classification law above is checked on constructed input)")
        wrong = [(s, o, c) for s, o, c in should if c != OM.MISNAMED]
        self.assertFalse(
            wrong,
            "%d cell(s) where the organ IS watching the thing under another name are reported as "
            "ABSENT: %s. That is precisely how the table he was shown filled with holes that were "
            "not holes." % (len(wrong), wrong[:4]))
        for r in rows:
            for organ, cell in r["cells"].items():
                if cell != OM.MISNAMED:
                    continue
                names, _w = cov.get(organ, (None, ""))
                self.assertTrue(
                    names and OM._same_thing(r["surface"], names),
                    "%s/%s is MISNAMED but the organ names nothing resembling it"
                    % (r["surface"], organ))

    def test_every_dark_column_says_why_it_is_dark(self):
        """Silence about a missing instrument reads as a clean bill of health.

        ⚠ THIS TEST CAUGHT A CONTRACT CHANGE AND WAS RIGHT TO. It asserted `why` held exactly the
        UNASKABLE organs — true while that was the only way a column could go dark. v2496 added
        two more ways: an organ that answers with nothing at all, and an organ whose names are a
        different KIND of thing from the surfaces (console_doctor names 34 concerns, none of which
        resolves to any of the 44 code objects). Both leave a column entirely UNKNOWN.

        The law it was really protecting is unchanged and is now stated directly: **a column that
        is UNKNOWN everywhere must say why, and an organ that produced any verdict must not claim
        it could not.** Widening the set of reasons must not widen the set of silences.
        """
        rows, why = OM.matrix()
        dark, speaking = [], []
        for o in OM.ORGANS:
            if all(r["cells"][o] == OM.UNKNOWN for r in rows):
                dark.append(o)
            else:
                speaking.append(o)
        self.assertEqual(
            sorted(why), sorted(dark),
            "every column that is UNKNOWN everywhere must carry its reason, and only those: "
            "dark=%s reported=%s" % (sorted(dark), sorted(why)))
        for o in dark:
            self.assertTrue(
                str(why.get(o) or "").strip(),
                "%r is dark and gives no reason — 'UNKNOWN' with no cause is indistinguishable "
                "from a bug in this table" % o)
        for o in speaking:
            self.assertNotIn(
                o, why,
                "%r delivered verdicts AND is listed as unanswerable. One of the two is wrong, "
                "and a reader has no way to tell which." % o)

    def test_the_corroborator_keeps_the_lane_it_learned_the_name_in(self):
        """The nine MISNAMED cells were one dropped qualifier, not nine naming problems.

        `_corr()` merged three route modules into one set of bare names, so `chronicle.runeword`,
        `fleet.sets` and `roster.unique` — 100% of the MISNAMED cells in this table — could never
        resolve to anything but a near-match. WHICH LANE a name came from is known at the call
        site and was discarded one line later.

        ⚠ And the fix must not over-reach: publishing lane-qualified names is only correct while
        it covers the surfaces of THAT lane and no others.
        """
        cov = OM.organ_coverage()
        names, why = cov["corroborator"]
        self.assertTrue(names, "the corroborator named nothing: %s" % why)

        lanes = ("chronicle", "fleet", "roster")
        qualified = {n for n in names if "." in n}
        self.assertTrue(qualified,
                        "no lane-qualified name at all — the corroborator is back to publishing "
                        "bare concept names, and every route surface will read MISNAMED")
        stray = {n for n in qualified if n.split(".")[0] not in lanes}
        self.assertFalse(stray, "the corroborator invented lane(s) that do not exist: %s" % stray)

        rows, _w = OM.matrix()
        route_rows = [r for r in rows if r["origin"] == "route"]
        self.assertTrue(route_rows, "BASELINE: no route surfaces, so this law is vacuous")
        bad = [(r["surface"], r["cells"]["corroborator"]) for r in route_rows
               if r["cells"]["corroborator"] != OM.COVERED]
        self.assertFalse(
            bad,
            "%d route surface(s) are still not COVERED by the corroborator: %s. The route sets "
            "ARE watching these; a cell that says otherwise is the dropped qualifier, back."
            % (len(bad), bad[:4]))

        # OVER-REACH — a lane-qualified name must not cover a surface belonging to no lane.
        over = [r["surface"] for r in rows
                if r["origin"] != "route" and r["cells"]["corroborator"] == OM.COVERED]
        self.assertFalse(
            over,
            "%d non-route surface(s) became COVERED by the corroborator: %s. Qualifying names by "
            "lane must widen the join, never the claim." % (len(over), over[:4]))

    def test_a_surface_with_no_organs_is_not_silently_dropped(self):
        """The whole point is that the holes stay visible."""
        rows, _why = OM.matrix()
        self.assertTrue(rows, "no surfaces derived at all")
        surfaces = OM.surfaces()
        self.assertEqual(
            len(rows), len(surfaces),
            "%d surfaces exist but only %d reached the matrix — one that produced no row is "
            "invisible, which is the defect A17 taught in v2490" % (len(surfaces), len(rows)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
