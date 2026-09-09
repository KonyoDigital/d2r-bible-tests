# -*- coding: utf-8 -*-
"""v2771 — THE `locked lanes` ROW WAS CRYING WOLF ABOUT HIS OWN RULING.

Found by running every doctor row at once: 50 rows, 31 ok, 17 flagged — and one of the 17 was
reporting a decision Konyo made on purpose as a fault.

    [missing] locked lanes — "the throw bar (2) is no longer STRICTLY above the keep bar (2)
                             — there is no un-throw in Diablo"

HIS RULING, 2026-09-07, quoted in vault_retro beside the constant itself:

    *"make it two also.. its fine.. i will review what i throw regardless.. as long as it in that
     bin"* · *"i will decide if to throw it out or not to"*

=== ⚠⚠ THE DANGER IS REAL; THE ROW WAS MEASURING THE WRONG AXIS ===
"There is no un-throw in Diablo" is exactly right, and the protection has not gone anywhere — it
simply is not carried by the witness count:

    keep    2 witnesses  ·  conf 0.55
    throw   2 witnesses  ·  conf 0.85     <- STRICTLY above, on confidence

and `gate()` is called for the throw bar with `witness_field="session"`, so the throw bar counts
independent RECORDINGS where the keep bar counts LOOKS. Two bars, still ordered, ordered on a
different axis than the row was checking.

⇒ The invariant this file pins is the true one: **strictly above on AT LEAST ONE axis, and never
below on either.** A real inversion — throwing becoming easier than keeping — still goes red, and so
does the degenerate case where the two bars become identical on both axes.

=== ⚠ WHY THIS IS WORTH A GATE AND NOT JUST AN EDIT ===
A doctor row that reports his own deliberate choice as a fault is a row he learns to scroll past —
and then it is not believed on the day something IS wrong. That is the same failure as a gate never
seen red, arriving from the other direction. [[feedback-suspect-the-instrument]]

⛔ AND THE FIX WAS TO THE ROW, NEVER TO THE BARS. Moving a bar to make a check green is repairing
the measurement to fit the data, on the one gate in the tree that owns an irreversible act.
"""
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
import vault_retro as VR  # noqa: E402


class _Bars(object):
    """Set both bars, always restoring the real ones."""

    def __init__(self, tw, kw, tc, kc):
        self.v = (tw, kw, tc, kc)

    def __enter__(self):
        self.real = (VR.THROWOUT_MIN_WITNESSES, VR.KEEP_MIN_WITNESSES,
                     VR.THROWOUT_CONF_FLOOR, VR.KEEP_CONF_FLOOR)
        (VR.THROWOUT_MIN_WITNESSES, VR.KEEP_MIN_WITNESSES,
         VR.THROWOUT_CONF_FLOOR, VR.KEEP_CONF_FLOOR) = self.v
        return self

    def __exit__(self, *a):
        (VR.THROWOUT_MIN_WITNESSES, VR.KEEP_MIN_WITNESSES,
         VR.THROWOUT_CONF_FLOOR, VR.KEEP_CONF_FLOOR) = self.real


def _row():
    return dict(D.CHECKS)["locked lanes"]()


class TheThrowBarStaysStricter(unittest.TestCase):

    # ── ⚠⚠ THE THREE DANGEROUS STATES ───────────────────────────────────────────────────────
    def test_throw_EASIER_on_witnesses_is_RED(self):
        with _Bars(1, 2, 0.85, 0.55):
            st, say = _row()
        self.assertEqual(D.MISSING, st,
                         "throwing needs FEWER witnesses than keeping and the console says fine — "
                         "an item could be thrown on evidence that would not have kept it")
        self.assertIn("EASIER", say)

    def test_throw_EASIER_on_confidence_is_RED(self):
        """★ The axis the old row could not see. It compared witnesses only, so a confidence
        inversion — the very thing now carrying the whole protection — would have passed green."""
        with _Bars(2, 2, 0.40, 0.55):
            st, say = _row()
        self.assertEqual(D.MISSING, st,
                         "throwing needs LESS confidence than keeping and the console says fine")
        self.assertIn("EASIER", say)

    def test_IDENTICAL_on_both_axes_is_RED(self):
        """★ The degenerate case. If the bars match on witnesses AND confidence, nothing anywhere
        makes throwing harder than keeping, and the ordering he relies on is gone entirely."""
        with _Bars(2, 2, 0.55, 0.55):
            st, say = _row()
        self.assertEqual(D.MISSING, st,
                         "the two bars are identical on both axes and the console reports the "
                         "lanes as safely ordered")
        self.assertIn("IDENTICAL", say)

    # ── ⚠ HIS RULING IS NOT A FAULT ─────────────────────────────────────────────────────────
    def test_his_actual_2026_09_07_configuration_reads_OK(self):
        """His ruling levelled the WITNESS bars and left the CONFIDENCE bars ordered. That is a
        decision, not a defect, and the row must say so or he will learn to ignore it."""
        with _Bars(2, 2, 0.85, 0.55):
            st, say = _row()
        self.assertEqual(D.OK, st,
                         "his own 2026-09-07 ruling is being reported as a fault: %s" % say)
        self.assertIn("stricter on confidence", say,
                      "the row does not say WHICH axis still carries the ordering, so a reader "
                      "cannot tell a safe configuration from a lucky one")

    def test_stricter_on_BOTH_still_reads_OK(self):
        with _Bars(3, 2, 0.85, 0.55):
            st, say = _row()
        self.assertEqual(D.OK, st)
        self.assertIn("witnesses and confidence", say)

    # ── ⛔ THE BARS THEMSELVES ───────────────────────────────────────────────────────────────
    def test_the_LIVE_bars_are_still_ordered_on_at_least_one_axis(self):
        """⛔ Pinned separately from the row, because the cheapest way to make any of this green is
        to move the thing it measures. This is the one gate in the tree that owns an irreversible
        act — there is no un-throw in Diablo."""
        self.assertGreaterEqual(VR.THROWOUT_MIN_WITNESSES, VR.KEEP_MIN_WITNESSES,
                                "the live throw bar needs FEWER witnesses than the keep bar")
        self.assertGreaterEqual(VR.THROWOUT_CONF_FLOOR, VR.KEEP_CONF_FLOOR,
                                "the live throw bar needs LESS confidence than the keep bar")
        self.assertTrue(VR.THROWOUT_MIN_WITNESSES > VR.KEEP_MIN_WITNESSES
                        or VR.THROWOUT_CONF_FLOOR > VR.KEEP_CONF_FLOOR,
                        "the live bars are identical on both axes — nothing makes throwing harder "
                        "than keeping")

    def test_the_row_did_not_become_unable_to_fail(self):
        """⚠ A row rewritten to stop crying wolf is exactly where a green-forever check gets born.
        If NONE of the dangerous configurations can turn it red, the rewrite went too far."""
        reds = 0
        for bars in ((1, 2, 0.85, 0.55), (2, 2, 0.40, 0.55), (2, 2, 0.55, 0.55)):
            with _Bars(*bars):
                if _row()[0] == D.MISSING:
                    reds += 1
        self.assertEqual(3, reds,
                         "only %d of the 3 dangerous bar configurations turn this row red — it has "
                         "been softened into a check that cannot fail" % reds)



# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════
# PROPOSED by tv/heart2_candidates.py — derived from this gate's OWN assertions and
# measured against the target file (each anchor occurs exactly once). Review it: the
# question is whether deleting this text is the defect the law exists to catch.
RED_PROOF = [
    {
        "why": 'the law requires this text in console_doctor.py, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'console_doctor.py',
        "find": 'IDENTICAL',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": 'the law requires this text in console_doctor.py, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'console_doctor.py',
        "find": 'witnesses and confidence',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
