#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE BLANK TEST THAT COULD NEVER FIRE ON HIS CONSOLE.

⚠⚠ THE DEFECT. `paint_witness.verdict()` declared BLANK only when one colour covered >= 98% of the
window. MEASURED 2026-09-05 through that same instrument, on his window in BOTH states, with a
known-painted window as a same-instrument reference:

    window                        modalShare    p99    brightShare
    his console, BLANK to him        0.124       33      0.0041
    his console, HEALTHY             0.069      177      0.0394
    Terminal, full of text           0.628      254      0.0581

**READ THE MODAL COLUMN.** The PAINTED window scores 0.628 and the blank one 0.124 — his blank
window is FURTHER from the 0.98 bar than a healthy one. A text window has a dominant background
colour; this console's background is a dark GRADIENT that never collapses to one flat colour. So
`share >= 0.98` was not a high bar here, it was **structurally unreachable**, and the check has
never once been able to report the fault he keeps hitting.

⚠ WHY THE OBVIOUS ALTERNATIVES WERE REJECTED, each refuted by measurement rather than by taste:
  · `distinct <= 4` — the module already dropped it: a healthy console swings 156 -> 34 between
    consecutive looks, so 28 proves nothing. Its own docstring records this.
  · mean luminance — refuted earlier: healthy renders measured 11.3 / 23.9 / 20.8 against a black
    window at 12.2. The ranges overlap.

p99 and brightShare separate the two states with no overlap (33 vs 177, 0.41% vs 3.94%), and the
HEALTHY console sits beside Terminal rather than beside its own blank state — so this is not the
dark theme being mistaken for emptiness.

⚠ NOTHING HERE TOUCHES HIS WINDOW. Every case drives `verdict()` on a measurement dict.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import paint_witness as PW  # noqa: E402


def _m(modal, p99, bright, distinct=40, mean=12.0):
    return {"samples": 4620, "distinct": distinct, "modalShare": modal, "modalLuminance": 7,
            "meanLuminance": mean, "p99Luminance": p99, "brightShare": bright, "why": ""}


#: the three real readings, taken through this instrument on 2026-09-05
HIS_BLANK = _m(0.124, 33, 0.0041, distinct=46, mean=11.6)
HIS_HEALTHY = _m(0.069, 177, 0.0394, distinct=164, mean=22.8)
TERMINAL = _m(0.628, 254, 0.0581, distinct=110, mean=39.8)


class ItSeesTheFaultHeKeepsHitting(unittest.TestCase):

    def test_his_REAL_blank_window_reads_BLANK(self):
        """★ THE WHOLE POINT. These are his actual numbers, not a synthetic worst case."""
        state, why = PW.verdict(HIS_BLANK)
        self.assertEqual(state, PW.BLANK, "his real blank window still reads as painted")
        self.assertIn("nothing is DRAWN", why)

    def test_the_reason_does_NOT_claim_one_colour_covers_the_window(self):
        """⚠ A WRONG REASON IS HOW THE LAST THREE ATTEMPTS AT THIS BUG WENT. The single-colour
        sentence would be false here — the commonest colour covers 12.4%."""
        _s, why = PW.verdict(HIS_BLANK)
        self.assertNotIn("SINGLE colour", why)
        self.assertIn("gradient", why)

    def test_his_REAL_healthy_window_still_reads_PAINTED(self):
        """⚠⚠ THE BASELINE, and without it this file proves nothing. A detector that calls
        everything blank would reload his console forever."""
        state, _why = PW.verdict(HIS_HEALTHY)
        self.assertEqual(state, PW.PAINTED, "a healthy console was called blank")

    def test_a_text_window_with_a_DOMINANT_BACKGROUND_is_not_blank(self):
        """★ Terminal's modalShare is 0.628 — five times his blank window's. If the ink test were
        wrong about what modal share means, this is where it would misfire."""
        state, _why = PW.verdict(TERMINAL)
        self.assertEqual(state, PW.PAINTED)


class TheOldTestCouldNotHaveCaughtIt(unittest.TestCase):
    """RED for the original defect: not 'it was hard to catch' but 'it was unreachable'."""

    def test_his_blank_window_never_approached_the_modal_bar(self):
        self.assertLess(HIS_BLANK["modalShare"], PW.BLANK_MODAL_SHARE)
        self.assertLess(HIS_BLANK["modalShare"], TERMINAL["modalShare"],
                        "his BLANK window has a HIGHER modal share than a painted one — if that "
                        "inverts, the single-colour test might have been reachable after all")

    def test_the_modal_test_still_fires_for_a_genuinely_flat_window(self):
        """⚠ The old rule is kept, not replaced. A window that really is one colour must still be
        caught by the sentence written for it."""
        state, why = PW.verdict(_m(0.995, 12, 0.0, distinct=3))
        self.assertEqual(state, PW.BLANK)
        self.assertIn("SINGLE colour", why)


class BothBarsMustAgree(unittest.TestCase):
    """⚠ The bars sit in the empty middle of a 5x gap, and BLANK needs BOTH. Either alone would be
    a hair-trigger on a console whose theme is legitimately dark."""

    def test_dark_p99_but_plenty_of_ink_is_NOT_blank(self):
        state, _ = PW.verdict(_m(0.10, 40, 0.20))
        self.assertEqual(state, PW.PAINTED, "it fired on p99 alone")

    def test_little_ink_but_a_BRIGHT_tail_is_NOT_blank(self):
        state, _ = PW.verdict(_m(0.10, 200, 0.004))
        self.assertEqual(state, PW.PAINTED, "it fired on brightShare alone")

    def test_the_bars_are_not_adjacent_to_either_real_reading(self):
        """A threshold sitting on top of a real measurement is one noisy sample from flipping."""
        self.assertGreater(PW.INK_P99_MAX, HIS_BLANK["p99Luminance"] * 2)
        self.assertLess(PW.INK_P99_MAX, HIS_HEALTHY["p99Luminance"] * 0.5)
        self.assertGreater(PW.INK_SHARE_MAX, HIS_BLANK["brightShare"] * 2)
        self.assertLess(PW.INK_SHARE_MAX, HIS_HEALTHY["brightShare"] * 0.5)


class AnUnmeasuredWindowStaysUnknown(unittest.TestCase):
    """[[unknown-stays-unknown]] — a reading that could not be taken is not a blank window."""

    def test_no_measurement_is_UNKNOWN(self):
        self.assertEqual(PW.verdict(None)[0], PW.UNKNOWN)
        self.assertEqual(PW.verdict({"distinct": None, "why": "no pixels"})[0], PW.UNKNOWN)

    def test_a_measurement_with_NO_ink_fields_falls_back_to_the_modal_test(self):
        """⚠ Backwards compatibility is not politeness here: a stored reading from before this
        change must not be re-judged by bars it never carried. Absent ink fields mean the ink test
        does not apply, NOT that the window was blank."""
        old = {"samples": 100, "distinct": 40, "modalShare": 0.10, "modalLuminance": 7,
               "meanLuminance": 12.0, "why": ""}
        self.assertEqual(PW.verdict(old)[0], PW.PAINTED)
        old_flat = dict(old, modalShare=0.99)
        self.assertEqual(PW.verdict(old_flat)[0], PW.BLANK)


class TheMeasurementActuallyProducesTheFields(unittest.TestCase):
    """⚠ A verdict reading keys the measurer never writes is the defect this whole file is about,
    one layer up. [[the-unjoined-end]]"""

    def test_measure_emits_p99_and_brightShare(self):
        import inspect
        src = inspect.getsource(PW)
        self.assertIn('"p99Luminance"', src)
        self.assertIn('"brightShare"', src)

    def test_the_live_console_reading_carries_them(self):
        """Drives the real instrument. Skips honestly if no console is up — a skip is not a pass."""
        import subprocess
        try:
            out = subprocess.run(["lsof", "-nP", "-iTCP:17772", "-sTCP:LISTEN", "-t"],
                                 capture_output=True, timeout=10).stdout.decode().split()
        except Exception:
            out = []
        if not out:
            self.skipTest("no console on :17772 — nothing to look at, and that is not a pass")
        r = PW.look(int(out[0]))
        m = r.get("measure") or {}
        if m.get("distinct") is None:
            self.skipTest("the window could not be sampled: %s" % r.get("why"))
        self.assertIsNotNone(m.get("p99Luminance"))
        self.assertIsNotNone(m.get("brightShare"))


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
