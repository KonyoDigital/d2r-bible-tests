# -*- coding: utf-8 -*-
"""v2749 — ZERO CONTRADICTIONS, BECAUSE THE CONTRACT REFUSES EVERY SEAL. Nothing said so.

His ask, 2026-09-03: *"i want this related to the 3/4D printer it should be in the same zone. that
unified printer needs to be built, that processing system for the reels all need a unified logic
coming in and out"*. `printer_reach` answers the question that opens — how much of the corpus the
pipeline can act on at all — and `grep -c printer_reach` was **0** across control_app.py,
console_doctor.py, corroborate.py and control_ui.html. The third module in three versions found
built, correct, and read by nothing. [[the-unjoined-end]] [[sweep-dont-ask]]

MEASURED on his tree: reels 437 · seals 31 · joined 21 · **sealsSatisfyingContract 0**, with name,
location AND provenance missing on all 31.

⚠⚠ WHY IT IS WORTH A ROW RATHER THAN A NUMBER: a downstream reader sees ZERO CONTRADICTIONS and
concludes the pipeline is healthy. It is not — the contract refuses every seal, so the contradiction
CANNOT ARISE. A zero meaning "nothing qualified" wearing the clothes of a zero meaning "nothing
wrong" is the exact confusion this repo has paid for repeatedly. [[zero-needs-a-denominator]]

⚠ AND THE MISSING FACTS MUST BE NAMED, because they imply DIFFERENT WORK. A missing `name` is a
reader change; a missing `location` is a CAPTURE question — 0 of 1,065 deep rows carry a cell — and
that is HIS ruling, not something code decides. The module itself once collapsed all three into one
by keying its tally on `str(cwhy)[:70]`, which lands mid-explanation; the truncated read implied a
reader fix, the true read implies a question for him.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import console_doctor as D  # noqa: E402


def _verdict(payload):
    import printer_reach as PR
    fn = dict(D.CHECKS)["printer reach"]
    real = PR.report
    PR.report = lambda *a, **k: payload
    try:
        return fn()
    finally:
        PR.report = real


def _rep(seals=31, ok=0, facts=None, reels=437, joined=21):
    return {"state": "UNREACHABLE", "rows": [], "why": "forced",
            "counts": {"reels": reels, "seals": seals, "joined": joined,
                       "sealsSatisfyingContract": ok},
            "missingByFact": facts if facts is not None else
                             {"name": 31, "location": 31, "provenance": 31}}


class ThePrinterReachIsWatched(unittest.TestCase):

    def test_the_row_is_REGISTERED(self):
        """A check defined and not in CHECKS runs NEVER."""
        self.assertIn("printer reach", dict(D.CHECKS),
                      "the printer-reach row is not registered, so it never runs")

    def test_the_console_actually_READS_the_module(self):
        doc = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()
        self.assertIn("import printer_reach", doc,
                      "console_doctor no longer reads printer_reach, so it is back to being built "
                      "and unread")

    # ── ⚠⚠ THE LAW ────────────────────────────────────────────────────────────────────────────
    def test_a_contract_that_refuses_EVERY_seal_is_MISSING(self):
        st, say = _verdict(_rep(seals=31, ok=0))
        self.assertEqual(D.MISSING, st, "a contract refusing every seal was graded as fine")
        self.assertIn("NOT ONE of 31", say)

    def test_the_message_says_the_zero_means_REFUSED_not_CLEAN(self):
        """⚠ THE WHOLE POINT. Without this sentence the row publishes a zero a reader will take for
        health. [[zero-needs-a-denominator]]"""
        _, say = _verdict(_rep(ok=0))
        self.assertTrue("refused everything" in say or "cannot arise" in say,
                        "the message no longer explains that zero here means the contract refused "
                        "everything rather than that nothing is wrong: %r" % str(say)[:160])

    def test_the_missing_FACTS_are_named_not_just_counted(self):
        """A missing `name` is a reader change; a missing `location` is a CAPTURE question and his
        ruling. A bare count cannot tell them apart."""
        _, say = _verdict(_rep(ok=0, facts={"name": 31, "location": 31, "provenance": 31}))
        for f in ("name", "location", "provenance"):
            self.assertIn(f, say, "the message no longer names the missing fact %r" % f)

    def test_a_satisfied_contract_is_OK(self):
        """The other direction — a row that can only be red is as useless as one that can only be
        green."""
        st, _ = _verdict(_rep(seals=31, ok=7))
        self.assertEqual(D.OK, st, "seals that DO satisfy the contract were still graded as stuck")

    # ── UNKNOWN is never collapsed into OK ────────────────────────────────────────────────────
    def test_an_unreadable_report_is_UNKNOWN(self):
        for bad in (None, {}, {"why": "no counts"}, "nonsense"):
            st, _ = _verdict(bad)
            self.assertEqual(D.UNKNOWN, st,
                             "a report of %r was treated as a measurement" % (bad,))

    def test_a_MISSING_count_is_UNKNOWN_not_zero(self):
        """`sealsSatisfyingContract: None` means nobody counted. Reading it as 0 would publish the
        alarming version of this row over a corpus nobody measured."""
        st, _ = _verdict({"counts": {"reels": 437, "seals": None,
                                     "sealsSatisfyingContract": None}, "why": ""})
        self.assertEqual(D.UNKNOWN, st, "an uncounted corpus was graded %r instead of UNKNOWN" % st)

    def test_no_wilson_lock_was_invented(self):
        try:
            import self_arming as SA
        except Exception:
            self.skipTest("self_arming unavailable")
        proves = getattr(SA, "PROVES", {}) or {}
        for bad in ("printer.reach", "printer_reach", "reach.corpus"):
            self.assertNotIn(bad, proves,
                             "%s was declared as a lock. Reachability is a READING." % bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
