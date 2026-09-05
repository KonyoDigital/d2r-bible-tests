#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""154's REAL SUBJECT — A FREED-SPACE FIGURE THAT WAS NEVER MEASURED.

⚠⚠ TWO FABRICATIONS, both found 2026-09-05 by an adversarial workflow and both REPRODUCED before
being believed. Task 154 said *"the prune field can never report anything"*. The truth was worse:
it could report, and what it reported was a hope.

**ONE — `reel_retention.apply_plan` returned the PLAN'S figure as the MEASUREMENT.**

    return {"ok": not failed, "removed": removed, "failed": failed,
            "freedMb": p.get("freeMb", 0),          # <- the plan's hope
            ...}

`freedMb` sat in the same dict literal as its own `removed` and `failed` lists and never consulted
either. Reproduced against a plan whose candidate did not exist, so every rmtree raised:

    ok=False   removed=[]   failed=1   freedMb=512.0

and `control_app.py:16348` — which copies this with **no read of `r["ok"]`** — would have printed:

    "freed 512 MB by removing 0 reel(s)"

The megabytes came from the plan and the reel count from the measurement. Two sources, one fiction.

**TWO — a BOOLEAN counted as MEGABYTES.** `bool` subclasses `int`, so
`isinstance(True, (int, float))` is True and `sum([True, True])` is 2. A history whose two
in-window rows carried `prunedMb: true` produced `prunedMbInWindow = 2` and the sentence
*"— 2 MB of that was our pruning"*. A caller one refactor from `pruned_mb=bool(freed)` turns
"yes, we pruned" into a quantity with no author.
⚠ `math.isfinite` does not cover it — `isfinite(True)` is True.

⚠ THE PRUNE STAYS OFF, so neither is firing today. Both were armed and latent, which is exactly
what `vault-owes` was called while it starved 29 reels.

⚠ NOTHING HERE TOUCHES HIS STORES. Every case builds a temp shelf or a throwaway JSONL, and the
apply_plan cases assert the tombstone path resolves INSIDE the fixture before calling — because
`_tombstone_path` falls back to his live `reel_tombstones.json` when it cannot resolve, and the
tombstone is written BEFORE the first removal. [[feedback-fixtures-never-touch-live-data]]
"""
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import control_app as ca  # noqa: E402
import reel_retention as rr  # noqa: E402


class AFreedFigureNamesWhatWasActuallyRemoved(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="freed_")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def _contained(self, d):
        """⚠ REFUSE TO RUN unless the tombstone lands inside the fixture."""
        tp = os.path.realpath(rr._tombstone_path(d))
        self.assertTrue(tp.startswith(os.path.realpath(d) + os.sep),
                        "the tombstone would land outside the fixture, at %s" % tp)

    def _reel(self, name, n=1):
        p = os.path.join(self.dir, name)
        os.makedirs(p, exist_ok=True)
        for i in range(n):
            io.open(os.path.join(p, "f_%d.jpg" % i), "w").close()
        return name

    def test_NOTHING_removed_reports_ZERO_not_the_plans_hope(self):
        """★ THE FABRICATION. Every removal fails; the report must not name the plan's number."""
        self._contained(self.dir)
        r = rr.apply_plan({"hist": self.dir, "freeMb": 512.0,
                           "candidates": [{"reel": "reel_absent_fixture", "mb": 512.0}]}, yes=True)
        self.assertEqual(r.get("removed"), [])
        self.assertTrue(r.get("failed"), "no removal was attempted, so nothing had to decide")
        self.assertEqual(r.get("freedMb"), 0,
                         "it still names %s MB with an empty `removed` list" % r.get("freedMb"))

    def test_it_sums_ONLY_the_reels_that_actually_went(self):
        """⚠ THE BASELINE. A figure that is always 0 is as useless as one that is always the plan."""
        self._contained(self.dir)
        self._reel("reel_real", 2)
        r = rr.apply_plan({"hist": self.dir, "freeMb": 907.5,
                           "candidates": [{"reel": "reel_real", "mb": 7.5},
                                          {"reel": "reel_gone", "mb": 900.0}]}, yes=True)
        self.assertEqual(r.get("removed"), ["reel_real"])
        self.assertEqual(r.get("freedMb"), 7.5,
                         "it counted a candidate that was never removed")

    def test_the_PLAN_figure_is_kept_under_its_own_name(self):
        """Nothing is lost: the hope is still reportable, it just stops wearing the word `freed`.
        [[label-outlived-referent]]"""
        self._contained(self.dir)
        r = rr.apply_plan({"hist": self.dir, "freeMb": 512.0,
                           "candidates": [{"reel": "reel_absent_fixture", "mb": 512.0}]}, yes=True)
        self.assertEqual(r.get("freedMbPlanned"), 512.0)

    def test_a_candidate_with_no_mb_adds_NOTHING_rather_than_defaulting(self):
        self._contained(self.dir)
        self._reel("reel_nomb")
        r = rr.apply_plan({"hist": self.dir, "freeMb": 99.0,
                           "candidates": [{"reel": "reel_nomb"}]}, yes=True)
        self.assertEqual(r.get("removed"), ["reel_nomb"])
        self.assertEqual(r.get("freedMb"), 0)

    def test_the_sentence_his_console_prints_can_no_longer_disagree_with_itself(self):
        """★ The end-to-end shape: MB from the plan, count from the measurement."""
        self._contained(self.dir)
        r = rr.apply_plan({"hist": self.dir, "freeMb": 512.0,
                           "candidates": [{"reel": "reel_absent_fixture", "mb": 512.0}]}, yes=True)
        said = "freed %.0f MB by removing %d reel(s)" % (r.get("freedMb") or 0,
                                                         len(r.get("removed") or []))
        self.assertEqual(said, "freed 0 MB by removing 0 reel(s)")
        self.assertNotIn("512", said)


class ABooleanIsNotAQuantity(unittest.TestCase):
    """`bool` subclasses `int`. Every type filter written as `isinstance(x, (int, float))` lets a
    flag through, and `sum` turns flags into a total."""

    def _hist(self, vals):
        d = tempfile.mkdtemp(prefix="dd_")
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, "h.jsonl")
        now = int(time.time() * 1000)
        rows = [{"at": now - 48 * 3600000, "freeGb": 40.0, "prunedMb": None}]
        for i, v in enumerate(vals):
            rows.append({"at": now - 3600000 + i, "freeGb": 39.0, "prunedMb": v})
        with io.open(p, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        return p

    def _win(self, vals):
        out = ca.disk_delta(hours=24, path=self._hist(vals))
        self.assertIsNotNone(out.get("deltaGb"),
                             "the reader returned early, so the filter never ran and a pass here "
                             "would be a refusal that never happened")
        return out.get("prunedMbInWindow")

    def test_two_TRUE_flags_do_not_become_2_MB(self):
        self.assertIsNone(self._win([True, True]),
                          "a boolean was totalled as megabytes")

    def test_a_bool_mixed_with_a_real_number_contributes_nothing(self):
        self.assertEqual(self._win([True, 40.0]), 40.0)

    def test_real_numbers_still_sum(self):
        """⚠ BASELINE — a filter that drops everything is not a filter."""
        self.assertEqual(self._win([12.5, 7.5]), 20.0)

    def test_a_genuine_ZERO_survives_as_a_measurement(self):
        """0 means measured-and-freed-nothing. Turning it into None would trade one blindness for
        another, and 154's own rule says a numeric sample is never UNKNOWN."""
        self.assertEqual(self._win([0]), 0)

    def test_NaN_is_refused_and_isfinite_would_not_have_saved_us(self):
        self.assertIsNone(self._win([float("nan")]))
        import math
        self.assertTrue(math.isfinite(True),
                        "isfinite(True) is False here, so the bool clause could have been dropped")

    def test_infinity_is_refused(self):
        self.assertIsNone(self._win([float("inf")]))


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
