#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The pixel witness must call his BLANK console blank, and never call a healthy one blank.

⚠⚠ EVERY CASE HERE IS SYNTHETIC OR A RECORDED MEASUREMENT. Not one test captures a window, asks
Quartz, or touches his running console — the fake below answers instead. A suite that reads his
live screen would pass or fail on what he happened to have open.
[[feedback-fixtures-never-touch-live-data]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import paint_witness as PW  # noqa: E402


def _m(share, distinct, mean=128.0, samples=3780, modal=255):
    """A measurement, as `measure()` would return it."""
    return {"samples": samples, "distinct": distinct, "modalShare": share,
            "modalLuminance": modal, "meanLuminance": mean, "why": ""}


class TheBarIsCalibratedAgainstHisREALSymptom(unittest.TestCase):
    """★ THE REGRESSION THAT PRODUCED THIS FILE. The module first shipped with a second bar,
    `distinct <= 4`, calibrated against healthy windows and synthetic all-black buffers. Pointed at
    his running console it found the thing it was built for — blank white, only the titlebar drawn
    — and said **PAINTED**, because window CHROME contributes 8-9 distinct luminances by itself.

    Every fixture behind that bar was chrome-free, and no real window ever is."""

    def test_his_console_BLANK_WITH_CHROME_is_called_blank(self):
        """The exact reading taken off his window at 15:3x on 2026-09-04."""
        state, why = PW.verdict(_m(0.9963, 9, mean=254.7))
        self.assertEqual(state, PW.BLANK,
                         "the live blank console reads as %s — this is the one case the witness "
                         "exists for, and chrome must not rescue the verdict: %s" % (state, why))

    def test_his_console_HEALTHY_is_never_called_blank(self):
        """⚠ BASELINE, and the more expensive direction to get wrong: a false blank reloads a
        window he is working in. Both readings taken off his healthy console."""
        for share, distinct in ((0.069, 156), (0.122, 34)):
            state, _ = PW.verdict(_m(share, distinct, mean=34.2, modal=6))
            self.assertEqual(state, PW.PAINTED,
                             "a healthy console (modalShare %.3f) was called blank" % share)

    def test_ordinary_busy_windows_are_never_called_blank(self):
        """Measured the same minute, so the margin is real and not assumed."""
        for label, share, distinct in (("Terminal", 0.6628, 117), ("Safari", 0.4892, 125)):
            state, _ = PW.verdict(_m(share, distinct))
            self.assertEqual(state, PW.PAINTED, "%s was called blank" % label)

    def test_a_solid_window_with_ONE_stray_pixel_is_still_blank(self):
        """His first report was a black console showing only the tooltip cursor. One drawn thing
        must not buy the window a clean bill."""
        state, _ = PW.verdict(_m(0.9995, 2, mean=1.0, modal=0))
        self.assertEqual(state, PW.BLANK)

    def test_the_distinct_count_is_REPORTED_and_not_REQUIRED(self):
        """⚠ Pins the fix itself. If someone re-adds `distinct` to the verdict, the live case
        above breaks again — so assert directly that a high distinct count cannot save a window
        that is 99% one colour."""
        state, _ = PW.verdict(_m(0.99, 40))
        self.assertEqual(state, PW.BLANK,
                         "a 99%-uniform window was called painted because it had many distinct "
                         "luminances — that is the chrome bug returning")


class NothingMeasuredIsNeverGOOD_NEWS(unittest.TestCase):
    """[[unknown-stays-unknown]] — the witness must never let an absent look read as a healthy one."""

    def test_an_unmeasurable_frame_is_UNKNOWN(self):
        state, why = PW.verdict({"distinct": None, "modalShare": None, "why": "no pixel sampled"})
        self.assertEqual(state, PW.UNKNOWN)
        self.assertIn("no pixel", why)

    def test_a_missing_measurement_is_UNKNOWN_not_painted(self):
        self.assertEqual(PW.verdict(None)[0], PW.UNKNOWN)

    def test_rescue_worked_is_NONE_when_the_pixels_cannot_be_read(self):
        """⚠ THE SHARP ONE. A rescue whose result cannot be measured must not count as a cure."""
        real = PW.look
        PW.look = lambda pid, **k: {"state": PW.UNKNOWN, "why": "no image"}
        try:
            r = PW.rescue_worked(1)
        finally:
            PW.look = real
        self.assertIsNone(r["worked"], "an unreadable window was reported as a working cure")
        self.assertIn("not success", r["why"])

    def test_rescue_worked_is_FALSE_when_the_window_is_still_blank(self):
        """The measured case: rescues=1 and the window still white. It must say so."""
        real = PW.look
        PW.look = lambda pid, **k: {"state": PW.BLANK, "why": "99.6% one colour"}
        try:
            r = PW.rescue_worked(1)
        finally:
            PW.look = real
        self.assertIs(r["worked"], False)
        self.assertIn("DID NOT RESTORE PAINTING", r["why"])

    def test_rescue_worked_is_TRUE_only_when_paint_returned(self):
        real = PW.look
        PW.look = lambda pid, **k: {"state": PW.PAINTED, "why": "content"}
        try:
            r = PW.rescue_worked(1)
        finally:
            PW.look = real
        self.assertIs(r["worked"], True)


class _FakeQuartz(object):
    """Answers the three calls the module makes, with no window server anywhere."""
    kCGWindowListOptionOnScreenOnly = 1
    kCGWindowListExcludeDesktopElements = 2
    kCGWindowListOptionIncludingWindow = 4
    kCGWindowImageBoundsIgnoreFraming = 8
    kCGWindowImageNominalResolution = 16
    kCGNullWindowID = 0
    CGRectNull = None

    def __init__(self, rows):
        self._rows = rows

    def CGWindowListCopyWindowInfo(self, opts, wid):
        return self._rows


class ItPicksHisCONSOLEAndSaysSoWhenItCannot(unittest.TestCase):

    def _row(self, pid, w, h, num):
        return {"kCGWindowOwnerPID": pid, "kCGWindowNumber": num,
                "kCGWindowBounds": {"Width": w, "Height": h}}

    def test_it_picks_the_BIGGEST_window_that_pid_owns(self):
        q = _FakeQuartz([self._row(7, 60, 60, 100), self._row(7, 1120, 660, 200),
                         self._row(9, 2000, 2000, 300)])
        wid, why = PW.window_for(7, quartz=q)
        self.assertEqual(wid, 200, "it did not pick his console-sized window: %s" % why)

    def test_a_tiny_helper_window_is_not_his_console(self):
        """⚠ A 1x1 helper window exists and would otherwise be captured and read as blank —
        which is how a witness invents a fault. Same threshold as window_visibility, imported
        from it rather than re-typed."""
        q = _FakeQuartz([self._row(7, 1, 1, 100)])
        wid, why = PW.window_for(7, quartz=q)
        self.assertIsNone(wid)
        self.assertIn("not the same as a blank one", why)

    def test_no_window_at_all_is_UNKNOWN_not_blank(self):
        wid, why = PW.window_for(7, quartz=_FakeQuartz([]))
        self.assertIsNone(wid)
        self.assertTrue(why)

    def test_no_quartz_is_UNKNOWN_with_its_reason(self):
        r = PW.look(7, quartz=None) if PW._quartz() is None else None
        if r is not None:
            self.assertEqual(r["state"], PW.UNKNOWN)
            self.assertIn("Quartz", r["why"])


class StrikesAreConsecutiveAndAnUnknownEndsIt(unittest.TestCase):

    def _looks(self, states):
        it = iter(states)
        return lambda pid, **k: {"state": next(it), "why": "fixture"}

    def test_three_blanks_running_is_BLANK(self):
        real = PW.look
        PW.look = self._looks([PW.BLANK, PW.BLANK, PW.BLANK])
        try:
            r = PW.blank_strikes(1)
        finally:
            PW.look = real
        self.assertEqual(r["state"], PW.BLANK)
        self.assertEqual(r["strikes"], 3)

    def test_one_painted_look_ENDS_it_immediately(self):
        """A window that draws even once in three looks is not the fault this catches."""
        real = PW.look
        PW.look = self._looks([PW.BLANK, PW.PAINTED, PW.BLANK])
        try:
            r = PW.blank_strikes(1)
        finally:
            PW.look = real
        self.assertEqual(r["state"], PW.PAINTED)

    def test_an_UNKNOWN_look_makes_the_RUN_unknown(self):
        """⚠ NOT 'fewer strikes than needed', which would read as healthier than the truth."""
        real = PW.look
        PW.look = self._looks([PW.BLANK, PW.UNKNOWN, PW.BLANK])
        try:
            r = PW.blank_strikes(1)
        finally:
            PW.look = real
        self.assertEqual(r["state"], PW.UNKNOWN)
        self.assertIn("nothing is established", r["why"])


class ItNeverACTS(unittest.TestCase):
    """⚠⚠ A WITNESS, NOT A TRIGGER. Asserted against the source by AST rather than by reading the
    docstring that promises it — a comment is not a guard. [[source-reading-guard]]"""

    FORBIDDEN = ("load_url", "reload", "os.remove", "unlink", "rmtree", "terminate", "kill")

    def test_the_module_cannot_reload_delete_or_kill_anything(self):
        import ast
        import io as _io
        src = _io.open(os.path.join(HERE, "paint_witness.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        # strip docstrings so the module's own prose about NOT doing these cannot satisfy it
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                names.append(node.attr)
            elif isinstance(node, ast.Name):
                names.append(node.id)
        for bad in self.FORBIDDEN:
            leaf = bad.split(".")[-1]
            self.assertNotIn(leaf, names,
                             "paint_witness references %r — it is a witness and must not act" % bad)



class TestV2626TheTitleBarHidBlankness(unittest.TestCase):
    """★★ HIS "USUAL SUSPECT BUG", MEASURED AT LAST — and the reason it was never caught is that
    the blank test was diluted by the OS title bar.

    Captured his actual window while he was reporting it black (`CGWindowListCreateImage`, window
    15475, 1120x660). It is a title bar reading "TV DIABLO" over a completely empty body:

        whole window            modalShare 0.9513  -> PAINTED   (wrong)
        excluding the top 30px  modalShare 0.9966  -> BLANK     (correct)

    A blank body plus three traffic lights and a title is ~5% of the pixels and NEVER uniform, so
    the chrome alone held a genuinely blank window three points under a 0.98 bar. ⚠ The module
    already knew chrome was the problem — its own note says *"window CHROME draws 8-9 distinct
    luminances"* — and answered it by dropping the DISTINCT conjunct, which left the modal-share
    bar just as diluted. **The chrome is not evidence about whether the page drew anything; the
    window server draws it either way.** [[feedback-threshold-above-the-ceiling]]

    ⚠ NOTHING HERE SHIPS A PICTURE OF HIS SCREEN. The windows are synthesised in memory — the repo
    is public, and a capture of his desktop is not a test fixture.
    """

    BODY = 30           # the uniform body luminance of a blank console
    CHROME = (200, 90, 160, 70, 210, 120)   # traffic lights + title text: never uniform

    def _shot(self, w=1120, h=660, body=None, chrome=True, content=False):
        """A window bitmap in the shape `measure()` reads: BGRA rows."""
        body = self.BODY if body is None else body
        bpp, bpr = 4, w * 4
        buf = bytearray(bpr * h)
        for y in range(h):
            for x in range(w):
                o = y * bpr + x * bpp
                if chrome and y < 28:
                    v = self.CHROME[(x // 7 + y) % len(self.CHROME)]
                elif content and (y % 11 == 0):
                    v = 120 + (x % 90)      # text-ish rows, genuinely varied
                else:
                    v = body
                buf[o] = buf[o + 1] = buf[o + 2] = v
                buf[o + 3] = 255
        return {"w": w, "h": h, "buf": bytes(buf), "bpr": bpr, "bpp": bpp}

    def test_a_blank_body_under_a_title_bar_reads_BLANK(self):
        """★ HIS WINDOW. Before this it read PAINTED, because the chrome carried the variance."""
        m = PW.measure(self._shot(chrome=True, content=False))
        self.assertGreaterEqual(
            m["modalShare"], PW.BLANK_MODAL_SHARE,
            "a blank body under a title bar still reads as painted (%.4f < %.2f) — the chrome is "
            "diluting the measurement, which is exactly the bug"
            % (m["modalShare"], PW.BLANK_MODAL_SHARE))

    def test_the_SAME_window_read_WITH_the_chrome_would_have_passed(self):
        """⚠ THE CONTROL, and it is what makes this case mean anything: it shows the old behaviour
        on the same bitmap. Without it, a bar that happens to pass proves nothing about the fix."""
        shot = self._shot(chrome=True, content=False)
        real = PW.CHROME_TOP_PX
        try:
            PW.CHROME_TOP_PX = 0
            with_chrome = PW.measure(shot)
        finally:
            PW.CHROME_TOP_PX = real
        without = PW.measure(shot)
        self.assertLess(with_chrome["modalShare"], PW.BLANK_MODAL_SHARE,
                        "the control does not reproduce the old behaviour, so this suite is not "
                        "grading the fix")
        self.assertGreater(without["modalShare"], with_chrome["modalShare"])

    def test_a_window_WITH_CONTENT_is_still_PAINTED(self):
        """⚠⚠ THE BASELINE THAT MATTERS. Cropping the chrome must not make every window look blank
        — a bar nothing can fail is not a bar."""
        m = PW.measure(self._shot(chrome=True, content=True))
        self.assertLess(m["modalShare"], PW.BLANK_MODAL_SHARE,
                        "a window with real content read as blank (%.4f)" % m["modalShare"])

    def test_a_SMALL_window_is_not_measured_down_to_nothing(self):
        """A helper window shorter than a few title bars must not have most of itself cropped."""
        m = PW.measure(self._shot(w=120, h=90, chrome=True, content=False))
        self.assertIsNotNone(m["modalShare"])
        self.assertGreater(m["samples"], 0)

    def test_the_crop_is_a_FLOOR_not_a_guess(self):
        """⚠ Measured on his 1120x660: 24px already clears (0.9872), 30px gives 0.9966. The value
        must stay at least the height of a real title bar or it stops removing the chrome."""
        self.assertGreaterEqual(PW.CHROME_TOP_PX, 24)
        self.assertLessEqual(PW.CHROME_TOP_PX, 44,
                             "cropping this much starts eating page content, not chrome")



if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
