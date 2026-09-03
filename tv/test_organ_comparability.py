# -*- coding: utf-8 -*-
"""A cell may say ABSENT only when the organ's vocabulary actually reaches this list.

⚠⚠ THE DEFECT THIS EXISTS FOR SHIPPED FOR ABOUT TEN MINUTES INSIDE ONE SESSION AND LOOKED LIKE
PROGRESS THE WHOLE TIME. `console_doctor.report()` was added so the doctor's column would stop
being UNKNOWN — and the column immediately filled with 44 confident ABSENT cells, because the
doctor names CONCERNS ('armed migration', 'art corpus', 'board join') and the surfaces are CODE
OBJECTS ('_bridge_prober', '_chron_autoread_loop', 'vault.apply'). Zero of 34 names resolved to
any of 44 surfaces. Nothing errored. The table simply went from honestly unknown to confidently
wrong, and the summary went on counting those cells as holes.

The law, in one sentence: **an organ that names a different KIND of thing has not been shown to
miss anything.** [[unknown-stays-unknown]] [[the-unjoined-end]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import organ_matrix as OM          # noqa: E402
import console_doctor as CD        # noqa: E402


class TheDoctorAnswersWithoutTouchingHisWindow(unittest.TestCase):

    def test_report_exists_and_names_its_checks(self):
        self.assertTrue(hasattr(CD, "report"),
                        "console_doctor has no report(), so organ_matrix cannot ask it anything "
                        "and a whole column of that table is unanswerable")
        rep = CD.report()
        rows = rep.get("rows") or []
        self.assertTrue(rows, "report() named nothing — an organ that lists no subjects cannot be "
                              "distinguished from one that is broken")
        self.assertEqual(len(rows), len(CD.CHECKS),
                         "report() and CHECKS disagree on how many things this doctor watches")

    def test_report_does_not_reach_his_console(self):
        """⚠ /api/board_ownership EVALUATES JAVASCRIPT IN THE WINDOW HE IS LOOKING AT.

        An organ asked "what do you watch?" must answer from its own table. If this ever starts
        calling run(), every consumer of the coverage question — the matrix, the heart, a status
        poll — begins reaching into his screen to answer a question about names.
        [[borrowed-surface]]
        """
        def boom(*a, **k):
            raise AssertionError("report() reached the network")
        get, post = CD._get, CD._post
        CD._get, CD._post = boom, boom
        try:
            rep = CD.report()
        finally:
            CD._get, CD._post = get, post
        self.assertTrue(rep.get("rows"))
        for r in rep["rows"]:
            self.assertEqual(
                r["state"], CD.UNMEASURED,
                "a row that was never run reports %r. A check that did not run is UNMEASURED, "
                "never OK — that gap is the whole reason this module has a fourth state."
                % r["state"])

    def test_the_matrix_can_read_the_doctors_vocabulary(self):
        """The doctor names things under `check`; a reader missing that synonym reports emptiness
        rather than failing, which is why this is asserted rather than assumed."""
        got = OM._names_from([{"check": "armed migration"}])
        self.assertIn("armed migration", got,
                      "_names_from cannot read `check`, so console_doctor.report() would hand the "
                      "matrix an EMPTY name set and the column would read 'watches nothing'")


class AbsentRequiresAComparableVocabulary(unittest.TestCase):

    def test_an_incomparable_organ_never_produces_a_verdict(self):
        rows, _why = OM.matrix()

        # ⚠⚠ THE FIRST VERSION OF THIS TEST ASKED THE MODULE WHETHER THE MODULE WAS RIGHT, and a
        # sabotage proved it worthless: forcing `hits = 1` inside comparability() — which is the
        # exact defect, doctor and watchdog declared comparable and handing down 88 verdicts they
        # had not earned — left this file GREEN. It iterated over the organs the code had ALREADY
        # labelled incomparable, so disabling the label removed the organs from the test's own
        # scope. A guard that reads the system's classification cannot detect a wrong
        # classification. [[source-reading-guard]]
        #
        # So the overlap is counted HERE, from the organ's names and the surface list, using the
        # shared resolver directly rather than the matrix's wrapper — a sabotage of either one is
        # then visible from the other side.
        cov = OM.organ_coverage()
        surf = OM.surfaces()
        try:
            import one_name as _on
            _same = _on.same_thing
        except Exception:                                   # pragma: no cover
            _same = lambda a, b: str(a).lower() == str(b).lower()

        def _overlap(names):
            return sum(1 for s in surf
                       if s in names or any(_same(s, n) for n in names))

        incomparable, comparable = [], []
        for o in OM.ORGANS:
            names, _w = cov.get(o, (None, ""))
            (comparable if (names and _overlap(names)) else incomparable).append(o)
        comp = {o: (o in comparable,
                    "" if o in comparable else "no name resolves to any surface")
                for o in OM.ORGANS}

        # BASELINE — the case must be distinguishable, or a green here means nothing.
        # There must be at least one organ of each kind in play; otherwise this test would pass
        # on a matrix where the question never arises. [[regression-guard]] §5
        self.assertTrue(incomparable,
                        "BASELINE: no organ is incomparable right now, so this test cannot "
                        "distinguish a matrix that honours the law from one that ignores it. That "
                        "is an UNKNOWN result, not a pass.")
        self.assertTrue(comparable,
                        "BASELINE: no organ is comparable, so every cell is UNKNOWN and the law "
                        "would hold vacuously.")

        for o in incomparable:
            verdicts = [r["surface"] for r in rows if r["cells"][o] != OM.UNKNOWN]
            self.assertEqual(
                verdicts, [],
                "%r names a different KIND of thing (%s) and yet delivered a verdict on %d "
                "surface(s), e.g. %s. Nothing about those cells was measured."
                % (o, comp[o][1][:70], len(verdicts), verdicts[:3]))

        # and the comparable organ must still be able to say something, or the fix has simply
        # turned the whole table off
        said = sum(1 for r in rows for o in comparable if r["cells"][o] != OM.UNKNOWN)
        self.assertTrue(said, "no comparable organ produced a single verdict — the table has been "
                              "silenced rather than corrected")

    def test_the_summary_does_not_count_unmeasured_cells_as_holes(self):
        """Run main() and read what it actually prints. A count that ignores a state is that state
        deleted, and this line has now been wrong twice for exactly that reason."""
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            OM.main([])
        out = buf.getvalue()
        # independently again, for the same reason as above
        cov, surf = OM.organ_coverage(), OM.surfaces()
        try:
            import one_name as _on
            _same = _on.same_thing
        except Exception:                                   # pragma: no cover
            _same = lambda a, b: str(a).lower() == str(b).lower()
        ncomp = 0
        for o in OM.ORGANS:
            names, _w = cov.get(o, (None, ""))
            if names and any(s in names or any(_same(s, n) for n in names) for s in surf):
                ncomp += 1
        if ncomp < len(OM.ORGANS):
            self.assertIn(
                "only %d of the %d organs" % (ncomp, len(OM.ORGANS)), out,
                "the summary reports a hole count without saying how many organs that verdict "
                "rests on. With %d of %d organs incomparable, '%d have none' reads as 'nobody is "
                "watching these' — a far larger claim than the evidence."
                % (len(OM.ORGANS) - ncomp, len(OM.ORGANS), len(OM.ORGANS)))
            self.assertNotIn(
                "have none at all", out,
                "the summary still says 'have none at all' while %d organ(s) were never compared"
                % (len(OM.ORGANS) - ncomp))


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
