# -*- coding: utf-8 -*-
"""v2743 — 8,790 DISK-HISTORY ROWS AND NOT ONE HAS EVER CARRIED A FREED FIGURE.

MEASURED on his live `tv/disk_history.jsonl`:

    8,790 rows total
      8,270 carry prunedMb exactly 0
        520 carry null
          0 have EVER carried a nonzero value

⚠⚠ AND THE ROW'S STATED BLOCKER WAS FALSE. t154 said "nothing can pass until a prune actually
runs". That is not it. `disk_history_append` has ONE production call site and it passes
`pruned_mb=None` **hardcoded**, ~85 lines ABOVE `apply_plan` — so it fires BEFORE any deletion and
a prune running changed nothing about what got written. `credible_pruned_mb` is correct and always
has been; it has simply never been handed a real figure.
⚠ NOT BLOCKED ON `prune.arm` EITHER. That lock governs whether a prune may ACT, not what the writer
may carry. The row conflated the two, and that conflation is why this sat behind a Wilson score it
never depended on.

=== THE TRAP THIS FIX HAD TO AVOID, AND IT IS NOT OBVIOUS ===
`credible_pruned_mb(pruned_mb, hist_bytes)` REFUSES a figure larger than the measured corpus —
verified against the real function:

    credible_pruned_mb(12.5, 100MB) -> (12.5, None)
    credible_pruned_mb(9e9,  100MB) -> (None, 'prunedMb ... exceeds the whole measured corpus ...
                                              a figure larger than the thing it was freed from is
                                              not a measurement')

`_hist_bytes` is computed from kept+candidates BEFORE the reels are removed. So a second write that
RE-MEASURED the corpus after deletion would compare the freed figure against a shrunken corpus and
get every legitimate prune refused as impossible. The pre-prune corpus is reused deliberately: the
corpus and the freed figure must come from the SAME MOMENT.

⚠ A SECOND ROW, NOT A REWRITE. The log is append-only, so the "before" row stays as the honest
record of what was known at that time.
"""
import ast
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

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()


def _fn(name):
    """The source of one function, bounded by the next def at column 0."""
    i = SRC.find("def %s(" % name)
    if i < 0:
        return None
    j = SRC.find("\ndef ", i + 1)
    return SRC[i:j if j > i else len(SRC)]


class APruneRecordsWhatItFreed(unittest.TestCase):

    def test_the_guard_can_find_the_retention_pass_AT_ALL(self):
        """⚠ A law that cannot find its subject passes having examined nothing."""
        blk = _fn("_retention_once")
        self.assertIsNotNone(blk, "_retention_once is gone or renamed")
        self.assertIn("apply_plan", blk, "the retention pass no longer applies a plan")

    # ── ⚠⚠ THE LAW ────────────────────────────────────────────────────────────────────────────
    def test_the_freed_figure_REACHES_the_history(self):
        blk = _fn("_retention_once")
        self.assertIn('pruned_mb=round(float(_freed), 1)', blk,
                      "the freed figure never reaches disk_history_append. 8,790 rows carried 0 or "
                      "null and not one a real number, because the only write fires before the "
                      "prune with pruned_mb hardcoded to None.")
        self.assertIn('_freed = r.get("freedMb")', blk,
                      "the figure is no longer taken from apply_plan's own result")

    def test_the_ORIGINAL_write_still_passes_None(self):
        """The pre-prune row is honest: at that moment nothing had been freed. Changing it to guess
        would replace one wrong number with another."""
        blk = _fn("_retention_once")
        self.assertIn("eligible_mb=round(p.get(\"freeMb\") or 0, 1), pruned_mb=None)", blk,
                      "the pre-prune write no longer records None. It runs BEFORE any deletion, so "
                      "None is the true answer there and anything else is invented.")

    # ── ⚠ THE TRAP: THE CORPUS MUST COME FROM THE SAME MOMENT ─────────────────────────────────
    def test_the_second_write_REUSES_the_pre_prune_corpus(self):
        """`credible_pruned_mb` refuses a figure larger than the corpus. `_hist_bytes` is measured
        from kept+candidates BEFORE deletion, so re-measuring after would make every legitimate
        prune look impossible and be silently refused."""
        blk = _fn("_retention_once")
        i = blk.find("_freed = r.get")
        self.assertGreater(i, 0, "the second write is gone")
        tail = blk[i:i + 900]
        self.assertIn("hist_bytes=_hist_bytes", tail,
                      "the second write does not reuse the PRE-PRUNE corpus. Measured after the "
                      "reels are gone, a real freed figure exceeds the shrunken corpus and "
                      "credible_pruned_mb refuses it — the fix would silently do nothing.")
        for bad in ("_corpus_mb =", "sum((k.get(\"mb\")"):
            self.assertNotIn(bad, tail,
                             "the corpus appears to be RE-MEASURED after the prune (%r)" % bad)

    def test_the_guard_it_feeds_actually_refuses_an_impossible_figure(self):
        """⚠ Proven against the real function, not assumed — this is the whole reason the corpus
        moment matters."""
        import control_app as CA
        ok, why = CA.credible_pruned_mb(12.5, 100 * 1024 * 1024)
        self.assertEqual(12.5, ok, "a plausible figure was refused")
        bad, why2 = CA.credible_pruned_mb(9e9, 100 * 1024 * 1024)
        self.assertIsNone(bad, "a figure larger than the whole corpus was published")
        self.assertIn("exceeds the whole measured corpus", str(why2))

    def test_it_APPENDS_rather_than_rewriting(self):
        """The log is append-only. The before-row must survive as the record of what was known
        then; two rows telling one story is honest, one row rewritten is not."""
        blk = _fn("_retention_once")
        self.assertEqual(2, blk.count("disk_history_append("),
                         "expected exactly two history writes in a retention pass (before, and "
                         "after with the freed figure); found %d"
                         % blk.count("disk_history_append("))

    # ── ⚠⚠ THE WRITE MUST BE REACHABLE, NOT MERELY PRESENT ────────────────────────────────────
    def test_the_second_write_is_guarded_on_the_FIGURE_not_a_constant(self):
        """⚠ THIS LAW EXISTS BECAUSE SABOTAGE FOUND THE OTHERS VACUOUS. Replacing
        `if _freed is not None:` with `if False:` left every string the laws above look for exactly
        where it was — two `disk_history_append(` calls, the rounded `pruned_mb`, the reused
        corpus — and they passed 7/7 over a write that could never execute.

        Checking text presence is not checking reachability. This walks the AST instead and
        requires the branch to be guarded on the freed value itself.
        [[sabotage-is-usually-the-wrong-one]] [[feedback-suspect-the-instrument]]
        """
        tree = ast.parse(SRC)
        fn = [n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_retention_once"]
        self.assertTrue(fn, "_retention_once is gone")
        found = []
        for node in ast.walk(fn[0]):
            if not isinstance(node, ast.If):
                continue
            calls = {c.func.id for c in ast.walk(node)
                     if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
            if "disk_history_append" not in calls:
                continue
            found.append(node)
        self.assertTrue(found,
                        "no conditional guards a disk_history_append call — the freed write is "
                        "either gone or unconditional")
        for node in found:
            self.assertNotIsInstance(
                node.test, ast.Constant,
                "the freed write is guarded by a CONSTANT (%r), so it is unreachable while every "
                "text-matching law above still passes. That is exactly how a disabled write hides."
                % getattr(node.test, "value", "?"))
            names = {n.id for n in ast.walk(node.test) if isinstance(n, ast.Name)}
            self.assertIn("_freed", names,
                          "the write is guarded on something other than the freed figure")

    def test_it_still_parses(self):
        ast.parse(SRC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
