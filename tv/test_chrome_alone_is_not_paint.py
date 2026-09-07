# -*- coding: utf-8 -*-
"""v2752 — HIS BLACK CONSOLE READ AS *PAINTED* BECAUSE OF TWO ROWS OF WINDOW CHROME.

Konyo, 2026-09-07, with a screenshot of a black console window: *"black screen again.. something
should be catching this"*. Something should have. Nothing did.

MEASURED ON THAT EXACT WINDOW while it was blank (pid 4333, 1120x660), sampling as measure() does:

    crop  modalShare  brightShare  p99   verdict
     30     0.1252      0.0159     255   PAINTED   <- the shipped CHROME_TOP_PX
     31     0.1192      0.0159     230   PAINTED
     32     0.1240      0.0000      27   BLANK
     36     0.1252      0.0000      27   BLANK

⚠⚠ EVERY ONE of the 63 bright samples sat at **y=30 exactly** — the title bar's bottom border, at
luminance 255. 63 of 3,969 samples is 1.59%, a hair over the 1.5% INK_SHARE_MAX bar, and the same
row dragged p99 to 255. A completely blank window cleared BOTH ink conditions on chrome alone.

=== WHY 30 WAS RIGHT WHEN IT WAS CHOSEN, AND STOPPED BEING RIGHT ===
The original note derived 30 against the MODAL test: "cropping 24px already clears the 0.98 bar
(0.9872), 30px gives 0.9966". Against a uniformity test, leftover chrome merely DILUTES — a couple
of bright rows cannot push modal share up. The INK test that arrived later asks a different
question: is ANY pixel bright? Two rows of luminance-255 answer yes, forever, on every window.
The threshold outlived the instrument it was measured against, and the note that justified it stayed
true and stopped being sufficient. [[label-outlived-referent]] [[feedback-threshold-above-the-ceiling]]

⚠ AND THE SECOND WITNESS DID NOT COVER FOR THE FIRST. region_witness saw it correctly — all six
cells blank, ink 0.0000 — but `half_blank` returns False for a FULLY blank window by design,
deferring to the whole-window witness. That witness was the blind one. Two instruments, one blind
and one deferring to it, and between them a black console reported no fault at all.
[[the-unjoined-end]]
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

import paint_witness as PW  # noqa: E402


def _shot(w, h, ground=8, chrome_rows=(30, 31), chrome_lum=255):
    """A blank window with a bright chrome border — his exact failing shape."""
    bpp, bpr = 4, w * 4
    buf = bytearray()
    for y in range(h):
        for x in range(w):
            if y < 28 or y in chrome_rows:
                v = chrome_lum                      # title bar + its bottom border
            else:
                v = ground + ((x + y) % 3)          # a dark, slightly textured page ground
            buf += bytes((v, v, v, 255))
    return {"w": w, "h": h, "buf": bytes(buf), "bpr": bpr, "bpp": bpp}


class ChromeAloneIsNotPaint(unittest.TestCase):

    def test_the_crop_clears_the_title_bar_AND_its_border(self):
        """⚠ THE FIX ITSELF. 30 leaves rows 30-31 in the sample; those two rows were the whole
        defect. This asserts the crop is past them, not merely 'bigger than before'."""
        self.assertGreaterEqual(PW.CHROME_TOP_PX, 32,
                                "CHROME_TOP_PX is back at or below 31, which leaves the title bar's "
                                "bottom border (measured at luminance 255 on rows 30-31 of his "
                                "1120x660 console) inside the sample. Two such rows are 1.59%% of "
                                "the frame and clear the 1.5%% ink bar on their own.")

    # ── ⚠⚠ THE LAW: a blank page under chrome must read BLANK ─────────────────────────────────
    def test_a_blank_window_with_a_bright_title_bar_reads_BLANK(self):
        shot = _shot(1120, 660)
        st, why = PW.verdict(PW.measure(shot))
        self.assertEqual(PW.BLANK, st,
                         "a window whose page drew NOTHING but whose chrome is bright still reads "
                         "as %s. That is exactly how his black console reported healthy. why=%r"
                         % (st, str(why)[:150]))

    def test_the_OLD_crop_would_have_missed_it(self):
        """⚠ PROVES THE FIX IS THE FIX rather than a coincidence: with the shipped-before value the
        same bitmap reads PAINTED, which is the defect reproduced on demand."""
        shot = _shot(1120, 660)
        real = PW.CHROME_TOP_PX
        try:
            PW.CHROME_TOP_PX = 30
            st, _ = PW.verdict(PW.measure(shot))
            self.assertEqual(PW.PAINTED, st,
                             "the old crop no longer reproduces the defect, so this fixture has "
                             "stopped standing for the thing it was built from")
        finally:
            PW.CHROME_TOP_PX = real

    # ── ⚠ THE OTHER DIRECTION — it must not start calling real pages blank ────────────────────
    def test_a_genuinely_PAINTED_page_still_reads_PAINTED(self):
        """A fix that reports every window blank would reload his console under him. His healthy
        console reads ~3.9% bright; this draws ink on the ground below the chrome."""
        shot = _shot(1120, 660)
        buf = bytearray(shot["buf"])
        # scatter ink across the PAGE area only, well below the crop
        for y in range(60, 640, 3):
            for x in range(0, 1120, 4):
                o = y * shot["bpr"] + x * shot["bpp"]
                buf[o] = buf[o+1] = buf[o+2] = 230
        shot["buf"] = bytes(buf)
        st, why = PW.verdict(PW.measure(shot))
        self.assertEqual(PW.PAINTED, st,
                         "a page with real ink below the chrome was called blank — that would "
                         "restart his console under him. why=%r" % str(why)[:150])

    def test_the_crop_does_not_eat_the_page(self):
        """⚠ THE COST HAS A CEILING. Cropping is not free: every row removed is page content the
        witness can no longer see. 36 of 660 is 5.5%; anything approaching a tenth of the window is
        no longer a chrome crop."""
        self.assertLess(PW.CHROME_TOP_PX, 66,
                        "the crop now eats more than a tenth of a 660px window, which stops being "
                        "chrome exclusion and starts being blindness to the top of the page")

    def test_it_is_the_INK_test_that_fires_not_the_modal_one(self):
        """His console's background is a GRADIENT — modal share is ~12%, structurally unable to
        reach 0.98 — so the single-colour test can never see this fault. If a future change makes
        the modal test the one that fires here, the reasoning above needs re-reading."""
        shot = _shot(1120, 660)
        m = PW.measure(shot)
        self.assertLess(m["modalShare"], PW.BLANK_MODAL_SHARE,
                        "the modal test now fires on this fixture, so it no longer stands for his "
                        "gradient-background console")
        self.assertLess(m["brightShare"], PW.INK_SHARE_MAX,
                        "the ink test is not what carries this verdict any more")


if __name__ == "__main__":
    unittest.main(verbosity=2)
