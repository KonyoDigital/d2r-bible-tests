#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A FIELD THAT NEVER ONCE CARRIED A VALUE, AND IT WAS THE DENOMINATOR OF HIS OWN QUESTION.

⚠⚠ MEASURED ON HIS LIVE SERIES, 2026-09-05:

    rows: 8588
      histBytes    non-null     0 / 8588
      reels        non-null  8588 / 8588
      eligibleMb   non-null  8588 / 8588
      freeGb       non-null  8588 / 8588

**`histBytes` has never once carried a value**, while every sibling field on the same row is
populated on all 8,588. That is REG-598's `startedTs` shape verbatim — *"a field that never once
carried a value is not a field, it is a typo with a comma after it."*

⚠⚠ AND IT IS NOT A FIELD NOBODY WANTED. It is the CORPUS: the denominator of the one question he
actually asked (v2229 — *"how come i have 15 gigabytes more today than yesterday? is the pruning
working?"*). `credible_pruned_mb` refuses a freed figure larger than the corpus, and **with
`hist_bytes` null that bound has never once been applicable on his machine.** The whole cold-read
hardening of v2648 sat behind a `None` that the only caller passed as a literal.

**THE VALUE WAS IN THE SAME DICT THE WHOLE TIME.** The call site already computes `reels` and
`eligibleMb` from the retention plan; the per-reel `mb` figures are right beside them. Measured on
his shelf: 40 reels, **5,463.4 MB**. Now passed, and the bound refuses his exact v2229 case —
15,000 MB against a 5,463 MB corpus.

⚠ THE PRE-PRUNE SIDE, DELIBERATELY. The write banks before anything branches, so the corpus is
what existed BEFORE any deletion — the right denominator, since a figure freed cannot exceed what
was there to free. Sampling after a prune would refuse a large legitimate one by its own bound
(freed 6 GB, 4 GB remains).

⚠ `pruned_mb` STAYS None, and that is correct rather than unfinished. The prune is OFF, so nothing
measured a freed figure. `None` means nobody looked; `0` would claim a measurement nobody took.

⚠ NOTHING HERE TOUCHES HIS STORES. Every write goes to a temp file; the live series is read
COUNT-ONLY, and only to assert the historical shape this file is about.
"""
import ast
import inspect
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import control_app as CA  # noqa: E402


def _the_call():
    """The `disk_history_append(...)` call inside the retention pass. -> ast.Call | None

    ⚠ FOUND BY WALKING THE AST, not by slicing source text. A fixed window past the region reads as
    ABSENT and would make this guard skip instead of fail. [[source-reading-guard]]
    """
    src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
    for node in ast.walk(ast.parse(src)):
        if (isinstance(node, ast.Call)
                and getattr(node.func, "id", None) == "disk_history_append"
                and any(k.arg == "hist_bytes" for k in node.keywords)):
            return node
    return None


def _kw(call, name):
    for k in (call.keywords or []):
        if k.arg == name:
            return k.value
    return None


class TheCorpusIsACTUALLYPASSED(unittest.TestCase):

    def test_the_call_site_exists_at_all(self):
        self.assertIsNotNone(_the_call(),
                             "no `disk_history_append` call with a `hist_bytes` keyword was found "
                             "— the anchor moved, and a guard that cannot find its subject must "
                             "REFUSE rather than pass")

    def test_hist_bytes_is_NOT_a_hardcoded_None(self):
        """★ THE DEFECT. `hist_bytes=None` written as a literal is what made 8,588 rows dead."""
        v = _kw(_the_call(), "hist_bytes")
        self.assertFalse(isinstance(v, ast.Constant) and v.value is None,
                         "hist_bytes is passed as a literal None again, so every row this writes "
                         "carries a dead field and the corpus bound can never apply")

    def test_pruned_mb_IS_still_a_deliberate_None(self):
        """⚠ THE OTHER HALF, and it must NOT be 'fixed'. The prune is OFF; nothing measured a
        freed figure. `None` means nobody looked. Writing `0` would claim a measurement nobody
        took — the exact fabrication `credible_pruned_mb` exists to refuse."""
        v = _kw(_the_call(), "pruned_mb")
        self.assertTrue(isinstance(v, ast.Constant) and v.value is None,
                        "pruned_mb is no longer a deliberate None — if a real counter now feeds "
                        "it, this guard should be re-read rather than deleted")


class TheBoundIsNowAPPLICABLE(unittest.TestCase):
    """★★ The point of passing it. A validator nothing can reach is not a validator."""

    CORPUS = int(5463.4 * 1024 * 1024)          # his shelf, measured 2026-09-05

    def _row(self, pruned_mb, hist_bytes):
        d = tempfile.mkdtemp(prefix="histb_")
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, "h.jsonl")
        CA.disk_history_append(40.0, 8, hist_bytes=hist_bytes, reels=40,
                               eligible_mb=0.0, pruned_mb=pruned_mb, path=p)
        with io.open(p, encoding="utf-8") as fh:
            return json.loads(fh.read().strip().splitlines()[-1])

    def test_his_v2229_case_is_REFUSED_once_the_corpus_is_known(self):
        """15 GB claimed against a 5.3 GB shelf — the question that produced this whole field."""
        row = self._row(15000.0, self.CORPUS)
        self.assertIsNone(row.get("prunedMb"), "a 15 GB claim passed against a 5.3 GB corpus")
        self.assertIn("corpus", row.get("prunedWhy") or "")

    def test_the_same_case_is_PUBLISHED_when_the_corpus_is_unknown(self):
        """⚠⚠ THE BASELINE, and it is what makes the fix worth anything. With `hist_bytes=None`
        the identical claim sails through — which is precisely the state his 8,588 rows were in."""
        row = self._row(15000.0, None)
        self.assertEqual(row.get("prunedMb"), 15000.0,
                         "the fixture no longer reproduces the unbounded state, so the test above "
                         "proves nothing about what changed")

    def test_a_PLAUSIBLE_figure_still_passes_with_the_corpus_known(self):
        """A bound that refuses everything is not a bound."""
        row = self._row(100.0, self.CORPUS)
        self.assertEqual(row.get("prunedMb"), 100.0)
        self.assertIsNone(row.get("prunedWhy"))

    def test_the_row_carries_the_corpus_it_was_judged_against(self):
        """⚠ A refusal a reader cannot re-derive is an assertion. The byte count goes on the row."""
        row = self._row(None, self.CORPUS)
        self.assertEqual(row.get("histBytes"), self.CORPUS,
                         "the corpus is used for the bound and then dropped from the row")


class TheHistoricalShapeIsWHYThisExists(unittest.TestCase):
    """⚠ Read-only, count-only, on the live series. It asserts the DEFECT this file records, so if
    the store is ever rewritten this stops claiming a history it no longer has."""

    def test_the_live_series_shows_the_dead_field(self):
        p = os.path.join(HERE, "disk_history.jsonl")
        if not os.path.exists(p):
            self.skipTest("no live disk history on this tree — not a pass")
        rows = []
        with io.open(p, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                if ln.strip():
                    try:
                        rows.append(json.loads(ln))
                    except Exception:
                        pass
        if len(rows) < 100:
            self.skipTest("only %d rows — too young to call a column dead" % len(rows))
        old = [r for r in rows if r.get("histBytes") is None]
        self.assertGreater(len(old), 1000,
                           "the historical dead column is gone, so this file's premise no longer "
                           "matches the store — re-read it rather than trusting the number")
        # every sibling on the same rows WAS populated: that is what makes it dead, not young
        live_siblings = [r for r in rows if r.get("reels") is not None]
        self.assertGreater(len(live_siblings), len(rows) // 2,
                           "the sibling fields are null too, so the store was simply not being "
                           "written — a different defect from a dead column")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
