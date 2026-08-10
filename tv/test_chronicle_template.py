"""v1690 — the Chronicle TEMPLATE's laws, as tests.

Round 1 of this ship was discarded: its detector flagged 30 of 31 non-Chronicle controls AS
Chronicle, and its own gates never ran because the agent ceiling was hit before they could. This
file is the measured-first replacement's proof, built the way chronicle_retro's write-free law is
proven — structurally, from the source text — plus real pixel readings from real frames, graded
SEPARATELY from the sparse vision labels available for this footage (round-1 correction #3: one of
the eight vision reads is conf 0.60 with names == ['Amulet'] * 7 — not clean ground truth)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import console_safe  # noqa: F401,E402
import chronicle_template as ct  # noqa: E402

_FRAMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "frames", "hist", "reel_s_1786385768689_67392")


def _f(name):
    return os.path.join(_FRAMES_DIR, name)


def _pil_available():
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


class TestPureLaw(unittest.TestCase):
    """★ PURE, THE WHOLE DESIGN: no writes, no deletes/renames, no network, no model calls —
    proven structurally from the source text, the way chronicle_retro's read-only law is proven."""

    def test_never_writes_deletes_or_calls_out(self):
        src = open(ct.__file__, encoding="utf-8").read()
        # no write-mode open, no delete, no rename
        self.assertNotRegex(src, r'open\([^)]*["\'][wax]')
        for forbidden in ("os.remove(", "os.rename(", "os.unlink(", "shutil.", "json.dump(",
                           "requests.", "urllib.", "socket.", ".save(", "subprocess."):
            self.assertNotIn(forbidden, src, forbidden + " has no business in a pure template reader")
        # no model call of any kind
        for forbidden in ("anthropic", "openai", "grok", "claude_read", "vision_call"):
            self.assertNotIn(forbidden.lower(), src.lower(),
                              forbidden + " would make this a model caller, not a pure reader")


class TestGeometryIsLocked(unittest.TestCase):
    """The bands are non-degenerate, ordered, and inside [0,1] — the same sanity a locked
    _TALLY_CROPS-style dict needs before anyone trusts it."""

    def _assert_valid_box(self, box, name):
        x0, y0, x1, y1 = box
        for v in box:
            self.assertGreaterEqual(v, 0.0, name)
            self.assertLessEqual(v, 1.0, name)
        self.assertLess(x0, x1, name + " x0<x1")
        self.assertLess(y0, y1, name + " y0<y1")

    def test_named_bands_are_valid(self):
        for name, box in [("MODAL_BAND", ct.MODAL_BAND), ("TITLE_BAND", ct.TITLE_BAND),
                           ("CLOSE_X_BAND", ct.CLOSE_X_BAND), ("TAB_STRIP_BAND", ct.TAB_STRIP_BAND),
                           ("SEARCH_BAND", ct.SEARCH_BAND),
                           ("SECONDARY_STRIP_BAND", ct.SECONDARY_STRIP_BAND),
                           ("LEFT_RAIL_BAND", ct.LEFT_RAIL_BAND), ("LIST_BAND", ct.LIST_BAND)]:
            self._assert_valid_box(box, name)
        for tab, box in ct.TAB_BANDS.items():
            self._assert_valid_box(box, "TAB_BANDS[%s]" % tab)

    def test_three_tabs_are_ordered_left_to_right_and_disjoint(self):
        u = ct.TAB_BANDS["unique"]
        s = ct.TAB_BANDS["sets"]
        r = ct.TAB_BANDS["runewords"]
        self.assertLessEqual(u[2], s[0] + 1e-6, "unique must end before sets starts")
        self.assertLessEqual(s[2], r[0] + 1e-6, "sets must end before runewords starts")

    def test_search_band_sits_right_of_the_tabs(self):
        self.assertGreaterEqual(ct.SEARCH_BAND[0], ct.TAB_BANDS["runewords"][2] - 1e-6)

    def test_row_pitch_is_a_small_positive_fraction(self):
        self.assertGreater(ct.ROW_PITCH_FRAC, 0.0)
        self.assertLess(ct.ROW_PITCH_FRAC, 0.2)  # a row is not a fifth of the panel

    def test_runewords_has_no_ledger_path_and_says_so(self):
        # THE DEAD END, DOCUMENTED, NOT SILENTLY FOLDED
        self.assertIn("runewords", ct.NO_LEDGER_TABS)
        self.assertIsNone(ct.ledger_kind_for_tab("runewords"))
        self.assertEqual(ct.ledger_kind_for_tab("unique"), "chronicle-uniques")
        self.assertEqual(ct.ledger_kind_for_tab("sets"), "chronicle-sets")
        self.assertIsNone(ct.ledger_kind_for_tab(None))


@unittest.skipUnless(_pil_available(), "PIL not installed — pixel-path tests need it, like stash_eye")
class TestDetectOnRealFrames(unittest.TestCase):
    """VERIFY THE THING, NOT A PROXY: these are the real JPEGs from
    tv/frames/hist/reel_s_1786385768689_67392/, read with vision to confirm what they show, then
    read again here through detect() to prove the pixel path agrees with what a human saw."""

    def test_clean_unique_panel_is_chronicle_with_tab_unique(self):
        out = ct.detect(_f("f_1786385790530.jpg"))
        self.assertTrue(out["is_chronicle"])
        self.assertEqual(out["tab"], "unique")
        self.assertGreaterEqual(out["confidence"], 0.9)

    def test_scrolled_unique_panel_still_reads_unique(self):
        # a different scroll position (Amulet rows near the top of the ledger) — same template
        out = ct.detect(_f("f_1786385782444.jpg"))
        self.assertTrue(out["is_chronicle"])
        self.assertEqual(out["tab"], "unique")

    def test_another_scroll_position_still_reads_unique(self):
        out = ct.detect(_f("f_1786385807514.jpg"))
        self.assertTrue(out["is_chronicle"])
        self.assertEqual(out["tab"], "unique")

    def test_tooltip_over_panel_is_still_chronicle_but_refuses_the_tab(self):
        # ★ THE CASE THAT MOTIVATED THIS SHIP: a found-item tooltip (Cerebus' Bite) drawn OVER the
        # panel. is_chronicle must still be True (the modal chrome the tooltip doesn't cover is
        # still there) but tab MUST be None — guessing here writes a wrong count into his grail.
        out = ct.detect(_f("f_1786385826754.jpg"))
        self.assertTrue(out["is_chronicle"])
        self.assertIsNone(out["tab"])
        self.assertLess(out["confidence"], 0.9, "occlusion must cost confidence, not be invisible")
        self.assertIn("occlud", out["why"])

    def test_pure_gameplay_frame_is_not_chronicle(self):
        # the negative control: earliest frame in the same reel, before the panel ever opened
        out = ct.detect(_f("f_1786385773403.jpg"))
        self.assertFalse(out["is_chronicle"])
        self.assertIsNone(out["tab"])
        self.assertEqual(out["confidence"], 0.0)

    def test_missing_frame_never_raises_and_is_not_chronicle(self):
        out = ct.detect(_f("does_not_exist_anywhere.jpg"))
        self.assertFalse(out["is_chronicle"])
        self.assertIsNone(out["tab"])
        self.assertIn("unreadable", out["why"])

    def test_geometry_signals_available_for_a_real_frame(self):
        # geometry graded on its own terms (round-1 correction #3), independent of any label
        sig = ct.geometry_signals(_f("f_1786385790530.jpg"))
        self.assertIsNotNone(sig)
        self.assertEqual(sig["size"], (2940, 1912))
        self.assertAlmostEqual(sig["aspect"], 2940 / 1912.0, places=3)
        self.assertGreater(sig["close_x_red"], 0.03)

    def test_geometry_signals_none_for_unreadable_frame(self):
        self.assertIsNone(ct.geometry_signals(_f("nope.jpg")))
        self.assertIsNone(ct.geometry_signals(""))


class TestOcrLinesAreWeakSecondaryOnly(unittest.TestCase):
    """Round-1 correction #1: OCR lines are a weak secondary, never the production classify path.
    These tests only prove the helper is honest about that scope — they never assert it can carry
    a verdict on its own."""

    def test_no_lines_is_no_guess(self):
        self.assertIsNone(ct.detect_from_ocr_lines(None))
        self.assertIsNone(ct.detect_from_ocr_lines([]))

    def test_recognises_the_three_tab_words_loosely(self):
        self.assertEqual(ct.detect_from_ocr_lines(["UNIQUE", "Sword"]), "unique")
        self.assertEqual(ct.detect_from_ocr_lines(["Sets", "63%"]), "sets")
        self.assertEqual(ct.detect_from_ocr_lines(["Runewords"]), "runewords")

    def test_tooltip_garbage_yields_no_tab_guess(self):
        # exactly the round-1 failure mode: tooltip OCR text has none of the three words
        lines = ["Required Strength: 86", "Defense: (335-350)", "Cerebus' Bite"]
        self.assertIsNone(ct.detect_from_ocr_lines(lines))


class TestAspectScalingIsCenterPreserving(unittest.TestCase):
    """Round-1 correction #2: stash_eye's left-anchor law would drag a CENTERED modal sideways.
    This proves the replacement law actually preserves the center instead of assuming one more time."""

    def test_calibrated_aspect_is_untouched(self):
        box, branch = ct._scale_band_for_aspect(ct.TITLE_BAND, ct._CAL_ASPECT)
        self.assertEqual(box, ct.TITLE_BAND)
        self.assertEqual(branch, "measured-mac")

    def test_off_calibration_aspect_preserves_center(self):
        frac = (0.4, 0.1, 0.6, 0.2)  # centered at x=0.5
        box, branch = ct._scale_band_for_aspect(frac, 1.778)  # 16:9 windows monitor
        self.assertEqual(branch, "derived-not-measured")
        cx = (box[0] + box[2]) / 2.0
        self.assertAlmostEqual(cx, 0.5, places=3, msg="center must not drift under scaling")
        # y band must be untouched (D2R scales the UI by height, not width)
        self.assertEqual((box[1], box[3]), (frac[1], frac[3]))

    def test_zero_or_missing_aspect_is_refused_not_guessed(self):
        frac = (0.4, 0.1, 0.6, 0.2)
        box, branch = ct._scale_band_for_aspect(frac, 0)
        self.assertEqual(box, frac)
        self.assertEqual(branch, "no-aspect")


if __name__ == "__main__":
    unittest.main()
