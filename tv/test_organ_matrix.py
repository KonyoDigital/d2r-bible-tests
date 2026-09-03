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
        self.assertTrue(
            should,
            "no surface is named differently by any organ — if the vocabularies really did "
            "align, this test has lost its subject and should be retired deliberately, not left "
            "passing on an empty set")
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

    def test_it_reports_how_many_organs_could_not_be_asked(self):
        """Silence about a missing instrument reads as a clean bill of health."""
        _rows, why = OM.matrix()
        cov = OM.organ_coverage()
        unaskable = [o for o, (n, _w) in cov.items() if n is None]
        self.assertEqual(
            sorted(why), sorted(unaskable),
            "the matrix does not report every organ it could not ask: unaskable=%s reported=%s"
            % (unaskable, sorted(why)))

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
