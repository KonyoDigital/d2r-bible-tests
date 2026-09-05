#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REG-600 — TWO SABOTAGES THAT AIMED AT SOMETHING THAT COULD NOT REFUSE.

⚠⚠ WHAT WAS MEASURED, 2026-09-05, and it is arithmetic over a non-event.

`prune.reports` banked **24/24** and `reel.route` banked **2 of 7 axes** against code with no
refusal path in the direction being attacked:

  · `disk_report_wilson` handed `disk_history_append(pruned_mb=None)` three ways and asserted the
    row came back `prunedMb is None`. `disk_history_append` was a PURE PASSTHROUGH —
    `"prunedMb": pruned_mb`, no validation of any kind — so all 24 attempts recorded correct
    behaviour on a legal input as a guard refusing.
  · `reel_router_wilson._attempt_unknown_is_folded_into_a_total` ran
    `if RR.UNKNOWN not in RR.STATIONS: caught += 1` eight times. That compares two MODULE
    CONSTANTS and can never vary: one static fact, banked as eight refusals.
  · `reel_router_wilson._attempt_a_blind_walk_passes` called `_string_keys_read_by` on a decider
    that reads nothing and counted `== set()` as a catch — grading an OBSERVATION. Its own comment
    said *"the caller must refuse it"*, and the caller was never called.

⚠ THE TELL IS THE ONE REG-593 ALREADY NAMED: replace the code under attack with a stub hardwired
to accept everything, and an inert axis scores exactly the same. A guard that always agrees may be
perfect or dead, and those are indistinguishable until the instrument is shown to MOVE.

WHAT v2647 CHANGED, in three parts:
  1. `control_app.credible_pruned_mb` — a REAL refusal at the WRITE end. The screening used to sit
     in `disk_delta` at READ time (bool/NaN/inf, v2643), so an impossible claim was written into
     his durable series and filtered afterwards by ONE reader. [[unknown-stays-unknown]] §4.
  2. the attacks now hand it figures a reporter must throw out, and `_refused` requires the
     reporter's OWN sentence — a bare `None` is also what a row nobody offered a figure to looks
     like, which is how identity assertions passed for refusals in the first place.
  3. `self_arming.withdraw()` — because `_fold` keys on (lock, kind, src, REF), so rewriting the
     attacks retires the old evidence ONLY where the ref name is reused. It was not: the four new
     refs superseded nothing, and `prune.reports` read **n=56 — 32 real refusals plus the 24
     identity assertions the rewrite existed to remove**. A lock that looks repaired while
     three-eighths of its evidence cannot fail is worse than one that never claimed to be.

⚠ NOTHING IS DELETED. The ledger stays append-only; a withdrawal appends an `n=0, k=0` row that
supersedes the axis and states its reason. Both the original and the retraction stay readable.

⚠ NOTHING IS ARMED. `may()` is still never called, the prune is still OFF, and no button is
blocked. `credible_pruned_mb` only ever makes the reporter say LESS.
"""
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import control_app as CA  # noqa: E402
import disk_report_wilson as DRW  # noqa: E402
import reel_router as RR  # noqa: E402
import reel_router_wilson as RRW  # noqa: E402
import self_arming as SA  # noqa: E402


class TheDiskRowNowHasARefusalPath(unittest.TestCase):
    """★ Part 1. The thing `prune.reports` was always supposed to be about."""

    CORPUS = 9_000_000_000                     # 9 GB in bytes

    def test_a_bool_is_not_one_megabyte(self):
        """⚠ `control_app.disk_delta` carries the scar: a history whose rows held `prunedMb: true`
        produced `prunedMbInWindow = 2` and the sentence *"2 MB of that was our pruning"*. That was
        screened at READ time; the `true` still went to disk."""
        for bad in (True, False):
            v, why = CA.credible_pruned_mb(bad, self.CORPUS)
            self.assertIsNone(v, "%r was accepted as a megabyte figure" % (bad,))
            self.assertTrue(why, "it was thrown out with no reason, which is unreadable")

    def test_a_string_is_not_a_measurement(self):
        for bad in ("12", "", [], {}, object()):
            v, _ = CA.credible_pruned_mb(bad, self.CORPUS)
            self.assertIsNone(v, "%r was accepted" % (type(bad).__name__,))

    def test_NaN_and_infinity_are_refused(self):
        for bad in (float("nan"), float("inf"), float("-inf")):
            v, _ = CA.credible_pruned_mb(bad, self.CORPUS)
            self.assertIsNone(v, "%r was accepted" % (bad,))

    def test_a_NEGATIVE_freed_figure_is_refused(self):
        v, why = CA.credible_pruned_mb(-5.0, self.CORPUS)
        self.assertIsNone(v, "pruning was reported as consuming space")
        self.assertIn("negative", why)

    def test_more_than_the_measured_corpus_is_refused(self):
        """★★ HIS OWN QUESTION, v2229: *"how come i have 15 gigabytes more today than yesterday?
        is the pruning working?"* — against a reel store measuring 8.9 GB. A figure larger than the
        thing it was freed from is impossible whatever the disk says."""
        v, why = CA.credible_pruned_mb(15_000.0, 8_900_000_000)
        self.assertIsNone(v)
        self.assertIn("corpus", why)

    def test_ZERO_IS_KEPT_because_measured_and_zero_is_a_real_answer(self):
        """⚠⚠ THE BASELINE, and the most important case in this file. `0` means "we measured and
        freed nothing"; `None` means nobody looked. Refusing 0 would be the same fabrication
        pointing the other way, and would make every refusal above prove a jammed door.
        [[unknown-stays-unknown]]"""
        for good in (0, 0.0, 12.5, 1000.0):
            v, why = CA.credible_pruned_mb(good, self.CORPUS)
            self.assertEqual(v, good, "a legitimate figure %r was thrown out (%s)" % (good, why))
            self.assertIsNone(why)

    def test_an_UNREADABLE_corpus_does_not_refuse_a_real_figure(self):
        """⚠ Refusing a measurement because a DIFFERENT field was not sampled trades a fabrication
        for a blindness. The bound cannot be applied; that is not a reason to reject the number."""
        for h in (None, "big", float("nan"), True):
            v, _ = CA.credible_pruned_mb(500.0, h)
            self.assertEqual(v, 500.0, "hist_bytes=%r caused a legitimate figure to be refused"
                                       % (h,))

    def test_None_stays_None_and_carries_NO_reason(self):
        """Three states, not two: nobody-measured must stay distinguishable from we-threw-it-out."""
        v, why = CA.credible_pruned_mb(None, self.CORPUS)
        self.assertIsNone(v)
        self.assertIsNone(why, "a row nobody offered a figure to now looks like a refusal")

    def test_the_WRITER_applies_it_and_records_the_reason(self):
        """⚠ The validator existing is not the same as the writer using it. [[the-unjoined-end]]"""
        import json
        import shutil
        import tempfile
        d = tempfile.mkdtemp(prefix="reg600_")
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, "h.jsonl")
        CA.disk_history_append(40.0, 8, hist_bytes=self.CORPUS, pruned_mb=True, path=p)
        row = json.loads(open(p, encoding="utf-8").read().strip().splitlines()[-1])
        self.assertIsNone(row.get("prunedMb"), "`True` reached his durable series")
        self.assertTrue(row.get("prunedWhy"), "the row cannot say it threw anything out")


class TheAttacksNowAimAtSomethingThatCanRefuse(unittest.TestCase):
    """★★ THE REG-593 CONTROL, applied to both harnesses. An axis that scores the same against a
    stub hardwired OPEN is measuring nothing, and that is the only check that separates a working
    guard from an inert one."""

    def test_the_disk_axes_COLLAPSE_against_a_validator_that_accepts_anything(self):
        real = CA.credible_pruned_mb
        try:
            CA.credible_pruned_mb = lambda v, h=None: (v, None)
            rep = DRW.prove()
        finally:
            CA.credible_pruned_mb = real
        self.assertEqual(rep["k"], 0,
                         "the disk axes still score %d/%d against a validator that refuses "
                         "NOTHING — they are not testing the validator" % (rep["k"], rep["n"]))
        self.assertNotEqual(rep["state"], "PROVEN")

    def test_a_validator_hardwired_SHUT_withdraws_the_claim_instead_of_acing_it(self):
        """⚠ The other direction, and it is the one REG-593 was written for: a guard that refuses
        EVERYTHING scores 32/32 and has proven nothing. The baseline must catch it."""
        real = CA.credible_pruned_mb
        try:
            CA.credible_pruned_mb = lambda v, h=None: (None, "no")
            rep = DRW.prove()
        finally:
            CA.credible_pruned_mb = real
        self.assertEqual(rep["k"], rep["n"], "the fixture no longer reproduces a jammed door")
        self.assertFalse(rep["baseline"], "a door jammed shut passed the baseline")
        self.assertEqual(rep["state"], "WITHDRAWN")
        self.assertEqual(DRW.bank_into_proof_queue(rep)[0][:8], "REFUSED ",
                         "a run the harness disowned still banked into the lock")

    def test_the_BLIND_axis_asks_the_real_assertion_to_refuse(self):
        """It used to grade `_string_keys_read_by(...) == set()` — an observation. It must now
        blind the real walker and require `assert_independent_of_retention` to FAIL."""
        real = RR.assert_independent_of_retention
        try:
            RR.assert_independent_of_retention = lambda: (True, [])
            n, k = RRW._attempt_a_blind_walk_passes()
        finally:
            RR.assert_independent_of_retention = real
        self.assertEqual(k, 0, "the blind axis scores %d/%d even when the assertion it drives has "
                               "been made tolerant of a dead instrument" % (k, n))
        n2, k2 = RRW._attempt_a_blind_walk_passes()
        self.assertEqual(k2, n2, "the blind axis does not pass against the real assertion")

    def test_the_UNKNOWN_axis_drives_route_instead_of_comparing_constants(self):
        """It used to run `if RR.UNKNOWN not in RR.STATIONS` — two module constants. It must now
        make `route()` keep the unmeasured reels OUT of the station totals."""
        real = RR.route

        def _folding(hist=None):
            rep = real(hist)
            if rep.get("ok"):
                rep["counts"]["INTAKE"] = rep["counts"].get("INTAKE", 0) + rep.get("unknown", 0)
                rep["unknown"] = 0
            return rep
        try:
            RR.route = _folding
            n, k = RRW._attempt_unknown_is_folded_into_a_total()
        finally:
            RR.route = real
        self.assertEqual(k, 0, "the unknown axis scores %d/%d even when UNKNOWN really is folded "
                               "into the station totals — the defect it names" % (k, n))
        n2, k2 = RRW._attempt_unknown_is_folded_into_a_total()
        self.assertEqual(k2, n2, "the unknown axis does not pass against the real router")


class RouteSurvivesAReelThePrinterNeverAnsweredFor(unittest.TestCase):
    """⚠⚠ FOUND BY THE REPLACEMENT AXIS ON ITS FIRST RUN, and the old one could never have.

    `_station_of` opens with `if ev is None: return UNKNOWN, "the printer did not answer for this
    reel"` — a branch written on purpose and documented. Its ONLY caller then went straight to
    `e.get("sealed")` and raised AttributeError, so the module's whole UNKNOWN story ended in a
    traceback the moment a reel actually went unanswered. [[the-unjoined-end]]
    """

    def _shelf(self):
        return {"r_a": {"sealed": True, "names": 3, "surveyed": True, "worthReading": True},
                "r_b": {"sealed": False, "names": 0, "surveyed": True, "worthReading": False},
                "r_c": {"sealed": None, "names": None, "surveyed": True},
                "r_d": None}

    def _route(self):
        real = RR._evidence
        try:
            RR._evidence = lambda h=None, _m=self._shelf(): (_m, "")
            return RR.route()
        finally:
            RR._evidence = real

    def test_a_None_evidence_row_does_not_raise(self):
        rep = self._route()
        self.assertTrue(rep.get("ok"), "route refused a shelf containing an unanswered reel")

    def test_it_lands_at_UNKNOWN_with_the_printer_sentence(self):
        rep = self._route()
        row = [r for r in rep["reels"] if r["reel"] == "r_d"][0]
        self.assertEqual(row["station"], RR.UNKNOWN)
        self.assertIn("did not answer", row["why"])

    def test_the_unmeasured_stay_OUT_of_the_station_totals(self):
        rep = self._route()
        self.assertEqual(rep["unknown"], 2)
        self.assertEqual(sum(rep["counts"].values()), 2)
        self.assertNotEqual(sum(rep["counts"].values()), rep["shelf"],
                            "the totals already contain the reels nobody could place")
        self.assertTrue(rep["reconciles"], "the shelf does not reconcile once UNKNOWN is added")


class AWithdrawalIsNotADeletionAndNotAnUnrunAxis(unittest.TestCase):
    """★ Part 3. `_fold` keys on ref, so a rewrite retires nothing unless the ref name is reused."""

    def test_a_withdrawal_needs_a_REASON(self):
        with self.assertRaises(ValueError):
            SA.withdraw("prune.reports", "sabotage", "disk_report_wilson", "x", "")

    def test_a_withdrawal_needs_the_REF_it_retires(self):
        """Without it this appends a new empty axis instead of superseding one — which would make
        the lock INCOMPLETE rather than clean."""
        with self.assertRaises(ValueError):
            SA.withdraw("prune.reports", "sabotage", "disk_report_wilson", "", "because")

    def test_it_cannot_RAISE_a_score(self):
        """⚠ A retirement that could add evidence would be a way to launder a weak lock upward."""
        import inspect
        src = inspect.getsource(SA.withdraw)
        self.assertIn("n=0, k=0", src, "withdraw banks something other than an empty axis")

    def test_the_allow_list_still_binds_a_withdrawal(self):
        """It goes through `bank`, so an undeclared source cannot retire somebody else's axis."""
        with self.assertRaises(ValueError):
            SA.withdraw("prune.reports", "sabotage", "not_a_declared_source", "x", "because")

    def test_a_withdrawn_axis_does_NOT_read_as_never_exercised(self):
        """★★ Both bank n == 0. Reporting a deliberate retirement as *"declared but never
        exercised"* puts a true sentence under the wrong word. [[label-outlived-referent]]"""
        rows = [r for r in (SA.report().get("locks") or [])
                if r.get("lock") == "prune.reports"]
        if not rows:
            self.skipTest("prune.reports is not in the table on this tree — not a pass")
        row = rows[0]
        self.assertIn("withdrawnClaims", row, "the report cannot say an axis was retired")
        for ref in ("noprune", "unreadable", "shrank"):
            self.assertNotIn(ref, row.get("blindClaims") or [],
                             "%r reads as never-exercised when it was withdrawn" % ref)

    def test_the_RETIRED_evidence_is_no_longer_counted(self):
        """★★ THE WHOLE POINT. 24 identity assertions must not still be inside the total."""
        rows = [r for r in (SA.report().get("locks") or [])
                if r.get("lock") == "prune.reports"]
        if not rows:
            self.skipTest("prune.reports is not in the table on this tree — not a pass")
        n = int(rows[0].get("n") or 0)
        self.assertNotEqual(n, 56, "the lock still reads 32 real refusals PLUS the 24 identity "
                                   "assertions the rewrite existed to remove")
        self.assertLessEqual(n, 32, "prune.reports counts more than its four attacks can produce")

    def test_the_ledger_is_still_APPEND_ONLY(self):
        """⚠ Nothing of his is pruned, and a withdrawal you cannot read is a deletion with a nicer
        name — the original row and the retraction must both survive."""
        import io
        import json
        rows = [json.loads(l) for l in io.open(SA._ledger_path(), encoding="utf-8") if l.strip()]
        old = [r for r in rows if r.get("ref") == "noprune" and int(r.get("n") or 0) > 0]
        new = [r for r in rows if r.get("ref") == "noprune" and r.get("withdrawn")]
        self.assertTrue(old, "the original banked axis was removed rather than superseded")
        self.assertTrue(new, "no withdrawal row was written for it")


class NothingHereArmsAnything(unittest.TestCase):
    """⚠ The standing constraint, checked rather than promised."""

    def test_credible_pruned_mb_can_only_make_the_reporter_say_LESS(self):
        """It returns the value or None. There is no path on which it invents a figure."""
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(CA.credible_pruned_mb).lstrip())
        for node in ast.walk(tree):
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Tuple):
                first = node.value.elts[0]
                ok = (isinstance(first, ast.Constant) and first.value is None) or \
                     (isinstance(first, ast.Name) and first.id in ("pruned_mb", "v"))
                self.assertTrue(ok, "a return path yields a figure that was not the one handed in")

    def test_may_is_still_never_called(self):
        """⚠⚠ AST, NOT A REGEX — and my first cut of THIS CASE proved why, going red on

            run_gates.py:1158  "... and that may() never grows an override "

        which is PROSE inside a string literal, describing the very rule being checked. That is the
        sixth guard in this repo defeated by its own documentation. A `Call` node is a call; text
        that looks like one is not. [[source-reading-guard]]
        """
        import ast
        import io
        hits = []
        for f in sorted(os.listdir(HERE)):
            if not f.endswith(".py") or f.startswith("test_") or f == "self_arming.py":
                continue
            try:
                tree = ast.parse(io.open(os.path.join(HERE, f), encoding="utf-8",
                                         errors="replace").read())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    fn = node.func
                    name = getattr(fn, "id", None) or getattr(fn, "attr", None)
                    if name == "may":
                        hits.append("%s:%d" % (f, node.lineno))
        self.assertEqual(hits, [], "something now CALLS may() — a badge became a gate: %s" % hits)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
