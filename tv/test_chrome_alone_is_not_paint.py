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

    # ── v2944 — the cross-family attack that landed, and the real frames that must not move ─────
    def test_the_INK_test_declines_on_an_obviously_PAINTED_window(self):
        """⚠⚠ A CROSS-FAMILY ATTACK, DESIGNED COLD, THAT LANDED. GB-L-PIXEL-3's `A3_dim_ink_theme`
        handed a window with **distinct 140, modalShare 0.071** — arithmetically IDENTICAL to his
        HEALTHY console (140, 0.069) — and the ink test declared it BLANK because its p99 sat at
        78, ONE POINT under the 80 bar. 140 different shades is not a dead renderer under any theme,
        and a false BLANK is the worse direction: it fires a rescue on a working console.

        ⚠ The guard is on the INK test ALONE. Conjoining `distinct` with the MODAL test is what
        failed on 2026-09-04 — his blank-white console draws NINE distinct luminances from chrome
        by itself and read PAINTED — so that path is deliberately untouched."""
        a3 = {"samples": 3969, "distinct": 140, "modalShare": 0.071, "modalLuminance": 12,
              "meanLuminance": 18.0, "p99Luminance": 78, "brightShare": 0.0}
        st, why = PW.verdict(a3)
        self.assertEqual(PW.PAINTED, st,
                         "a window with 140 distinct luminances was called BLANK: %s" % why)
        self.assertIn("distinct", why, "the refusal does not say which test declined: %r" % why)
        # and the same frame WITH few shades is still blank — the guard must not disarm the test
        dead = dict(a3, distinct=3)
        self.assertEqual(PW.BLANK, PW.verdict(dead)[0],
                         "the ink test no longer fires on a genuinely featureless dim window — the "
                         "guard disarmed the test instead of narrowing it")

    def test_the_guard_must_sit_ABOVE_what_CHROME_ALONE_DRAWS(self):
        """⚠⚠ THE BAR IS A FLOOR, AND THIS IS THE FLOOR. Measured 2026-09-04 on his own machine:
        his blank console's window CHROME — traffic lights, the "TV DIABLO" title, the 1px rule
        under it — contributes **9 distinct luminances all by itself**, and "a real blank window is
        never chrome-free". So a dim blank arrives at the ink test carrying chrome's shades, and a
        guard set at or below 9 declines exactly the case the ink test exists for.

        ⚠ The drill taught me this law. `INK_MAX_DISTINCT = 4` came back BLIND — nothing I had
        written could tell a sane bar from one below what chrome draws, because every fixture I
        had built was chrome-free. That is the SAME mistake as 2026-09-04, one test over.
        [[feedback-blind-fixture-green-gate]]"""
        chrome_dim_blank = {"samples": 3969, "distinct": 9, "modalShare": 0.124,
                            "modalLuminance": 20, "meanLuminance": 22.0,
                            "p99Luminance": 33, "brightShare": 0.0041}
        st, why = PW.verdict(chrome_dim_blank)
        self.assertEqual(PW.BLANK, st,
                         "a DIM BLANK window carrying only chrome's 9 luminances was not caught "
                         "(%s) — the guard sits at or below what chrome alone draws, which is the "
                         "2026-09-04 defect arriving through the ink test" % why)
        self.assertGreater(PW.INK_MAX_DISTINCT, 9,
                           "INK_MAX_DISTINCT is %d, at or below the 9 luminances his chrome draws "
                           "by itself" % PW.INK_MAX_DISTINCT)

    def test_the_MODAL_test_is_NOT_guarded_by_distinct(self):
        """⚠⚠ THE 2026-09-04 REGRESSION, PINNED SO IT CANNOT RETURN. `distinct <= 4` was once a
        second bar on the MODAL test, and his blank-white console read PAINTED because chrome alone
        contributes NINE luminances — the conjunct failed on the only case that mattered. Any future
        tightening must leave this path alone."""
        chrome_blank = {"samples": 3969, "distinct": 9, "modalShare": 0.9963, "modalLuminance": 255,
                        "meanLuminance": 250.0, "p99Luminance": 255, "brightShare": 0.99}
        self.assertEqual(PW.BLANK, PW.verdict(chrome_blank)[0],
                         "a 99.6%-one-colour window with chrome was not called BLANK — the modal "
                         "test has been conjoined with `distinct` again")
        many = dict(chrome_blank, distinct=200)
        self.assertEqual(PW.BLANK, PW.verdict(many)[0],
                         "the modal test now depends on `distinct` — that is the 2026-09-04 defect")

    #: MEASURED FROM HIS OWN CAPTURES, and RECORDED rather than re-measured. Reading the PNGs
    #: needs the macOS graphics bindings, and the suite may not pull in anything CI does not
    #: install — a guarded import of them was the FIRST cut, and the CI-imports law refused it
    #: refused it. That refusal is right: on CI the check would SKIP, and a skip is not a pass.
    #: Each row is one FROZEN CLASS on his shelf - N byte-identical captures, which cannot happen
    #: on a live console since the clock alone changes. Border excluded (inset 80).
    REAL_FRAMES = [
        {'identical': 34, 'file': 'HEART2-LOOK-103.png', 'samples': 3720, 'distinct': 1, 'modalShare': 1.0, 'modalLuminance': 30, 'meanLuminance': 30.0, 'p99Luminance': 30, 'brightShare': 0.0, 'verdict': 'BLANK'},
        {'identical': 18, 'file': 'heart2-241-20260910T060700Z.png', 'samples': 3720, 'distinct': 1, 'modalShare': 1.0, 'modalLuminance': 255, 'meanLuminance': 255.0, 'p99Luminance': 255, 'brightShare': 1.0, 'verdict': 'BLANK'},
        {'identical': 16, 'file': 'heart2-20260910-065806-w47306.png', 'samples': 3720, 'distinct': 1, 'modalShare': 1.0, 'modalLuminance': 255, 'meanLuminance': 255.0, 'p99Luminance': 255, 'brightShare': 1.0, 'verdict': 'BLANK'},
        {'identical': 3, 'file': 'HEART2-LOOK-139-146-20260910-011122-quartz.png', 'samples': 3782, 'distinct': 1, 'modalShare': 1.0, 'modalLuminance': 30, 'meanLuminance': 30.0, 'p99Luminance': 30, 'brightShare': 0.0, 'verdict': 'BLANK'},
        {'identical': 3, 'file': 'heart2-20260910-063201-w47001.png', 'samples': 3720, 'distinct': 1, 'modalShare': 1.0, 'modalLuminance': 255, 'meanLuminance': 255.0, 'p99Luminance': 255, 'brightShare': 1.0, 'verdict': 'BLANK'},
        {'identical': 3, 'file': 'heart2-278-20260910-122047-IDT.png', 'samples': 3782, 'distinct': 152, 'modalShare': 0.1126, 'modalLuminance': 5, 'meanLuminance': 20.8, 'p99Luminance': 192, 'brightShare': 0.0489, 'verdict': 'PAINTED'},
    ]

    def test_every_REAL_captured_frame_keeps_its_verdict(self):
        """THE REGRESSION CHECK THAT MATTERS. A threshold change that moved ANY of these would be
        trading a synthetic attack for a real failure. Five frozen-BLANK classes on his shelf all
        measure distinct 1; the painted class measures 152. These are his own console's frames,
        including the 18-identical class whose titlebar-and-nothing-else was confirmed by eye."""
        for r in self.REAL_FRAMES:
            m = dict((k, r[k]) for k in ("samples", "distinct", "modalShare", "modalLuminance",
                                         "meanLuminance", "p99Luminance", "brightShare"))
            st, why = PW.verdict(m)
            self.assertEqual(r["verdict"], st,
                             "a REAL captured frame changed verdict: " + str(r["identical"])
                             + "x identical, " + str(r["file"]) + ", distinct=" + str(r["distinct"])
                             + " modalShare=" + str(r["modalShare"]) + " -> " + str(st)
                             + ", was " + str(r["verdict"]) + ". " + str(why))
        blanks = [r for r in self.REAL_FRAMES if r["verdict"] == PW.BLANK]
        painted = [r for r in self.REAL_FRAMES if r["verdict"] == PW.PAINTED]
        self.assertGreaterEqual(len(blanks), 3, "too few real BLANK frames recorded to call this "
                                                "a regression check")
        self.assertTrue(painted, "no real PAINTED frame recorded, so this cannot catch a change "
                                 "that calls everything blank")

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


RED_PROOF = [
    {
        "why": 'a blank console window whose only bright pixels are two rows of OS title-bar chrome must read BLANK — crop below 32 leaves rows 30-31 at luminance 255 in the sample, which alone clears the 1.5% ink bar and reported his black screen as PAINTED  MEASURED: untampered OK — Ran 6 tests in 0.446s, all 6 pass (python3 tv/test_chrome_alone_is_not_paint.py, exit; tampered (all 1) FAILED (failures=3) — Ran 6 tests in 0.592s, exit 1. Red laws: test_a_blank_window_with_a_; reddened law test_chrome_alone_is_not_paint.ChromeAloneIsNotPaint.test_a_blank_wind; ALONE RED ALONE — `python3 -m unittest test_chrome_alone_is_not_paint.ChromeAloneIsNotPaint.test_a_blank_window_with.',
        "file": 'paint_witness.py',
        "find": 'CHROME_TOP_PX = 36',
        "replace": 'CHROME_TOP_PX = 30',
        "matches": 1,
    },
    {
        "why": 'v2944/A — removes the distinct guard from the INK test, so a window with 140 distinct luminances — arithmetically identical to his HEALTHY console (140, 0.069) — is declared BLANK because its p99 sits one point under the bar. A false BLANK is the worse direction: it fires a rescue on a working console. Designed cold by a different model family as A3_dim_ink_theme, and it LANDED.',
        "file": 'paint_witness.py',
        "find": '            and d is not None and d <= INK_MAX_DISTINCT\n',
        "replace": '',
        "matches": 1,
    },
    {
        "why": 'v2944/B — drops the bar to the old report-only value, which is BELOW what real chrome draws (his blank-white console contributes NINE luminances from chrome alone). The ink test then declines on genuinely blank windows and the detector loses the case it exists for — the 2026-09-04 defect arriving through the other test.',
        "file": 'paint_witness.py',
        "find": 'INK_MAX_DISTINCT = 64\n',
        "replace": 'INK_MAX_DISTINCT = 4\n',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
