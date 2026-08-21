#!/usr/bin/env python3
"""v1536 — THE CROPS WERE CALIBRATED ON KONYO'S MACBOOK, and only his MacBook got them.

Konyo: *"THE AI READERS arent working properly my cuzin just did a ON AIR and it didnt read his
runestash"* … *"there might be something to do with resolution for MACBOOK/WINDOWS?"*

He was right. Every crop band in stash_eye.py was measured on 2940×1912 (aspect 1.538) and the
caller applied them only for 1.45 <= aspect <= 1.62. A normal Windows monitor is 16:9 = 1.778 —
outside that gate — so every one of his cousin's frames fell to the "foreign/windowed" fallback:
the whole left 46% of the screen. On 1920×1080 that is a 954k-pixel slab where the Mac gets a
177k-pixel band, so the grid arrived 5.4× more diluted and both the tab OCR and the grid
fingerprint were reading a much emptier picture.

The first test here is the one that matters most: KONYO'S OWN MACHINE MUST NOT CHANGE. A fix for
the cousin that moves the Mac would trade one broken machine for another.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: F401,E402
import stash_eye as se  # noqa: E402


class TestKonyosMacIsUntouched(unittest.TestCase):
    def test_the_locked_band_comes_back_BYTE_IDENTICAL_on_his_film(self):
        # ★ 2940×1912 is the actual film every band was measured on
        for layout in ("runes", "gems", "materials", "shared", "personal"):
            self.assertEqual(se.crops_for_aspect(layout, 2940 / 1912.0),
                             se._TALLY_CROPS[layout],
                             layout + " moved on Konyo's own machine")

    def test_every_aspect_inside_the_calibrated_gate_is_untouched(self):
        for a in (1.45, 1.50, 1.538, 1.60, 1.62):
            self.assertEqual(se.crops_for_aspect("runes", a), se._TALLY_CROPS["runes"])


class TestTheCousinGetsARealBand(unittest.TestCase):
    def test_16_9_no_longer_falls_off_the_calibrated_gate(self):
        band = se.crops_for_aspect("runes", 16 / 9.0)
        self.assertIsNotNone(band, "16:9 must get a band, not the 46% slab")
        self.assertNotEqual(band, se._TALLY_CROPS["runes"])

    def test_the_derived_band_keeps_the_PANEL_the_same_physical_size(self):
        # the derivation's whole claim: D2R scales its UI with HEIGHT and anchors the panel left, so
        # the panel's WIDTH IN PIXELS should barely move between a Mac and a Windows box of the same
        # height. If this drifts, the derivation is wrong.
        mac_w, mac_h = 2940, 1912
        win_w, win_h = 1920, 1080
        mb = se.crops_for_aspect("runes", mac_w / float(mac_h))
        wb = se.crops_for_aspect("runes", win_w / float(win_h))
        mac_px_per_h = (mb[2] - mb[0]) * mac_w / mac_h      # panel width, in units of frame height
        win_px_per_h = (wb[2] - wb[0]) * win_w / win_h
        self.assertAlmostEqual(mac_px_per_h, win_px_per_h, places=6)

    def test_the_vertical_band_does_NOT_move(self):
        # the panel is anchored vertically the same way; only the horizontal fraction changes
        mb = se._TALLY_CROPS["runes"]
        wb = se.crops_for_aspect("runes", 16 / 9.0)
        self.assertEqual((mb[1], mb[3]), (wb[1], wb[3]))

    def test_it_stays_inside_the_frame_at_absurd_aspects(self):
        for a in (2.37, 3.55, 8.0):          # ultrawide, super-ultrawide, nonsense
            b = se.crops_for_aspect("runes", a)
            self.assertGreaterEqual(b[0], 0.0)
            self.assertLessEqual(b[2], 1.0)
            self.assertLess(b[0], b[2])

    def test_a_WINDOWED_frame_still_refuses_a_band(self):
        # ★ the derivation only holds for a fullscreen game. A windowed or letterboxed frame has the
        # panel somewhere else entirely, and inventing a band there would be worse than the slab.
        for a in (1.29, 1.0, 0.75, 0):
            self.assertIsNone(se.crops_for_aspect("runes", a))

    def test_an_unknown_layout_falls_back_to_the_generic_left_panel(self):
        self.assertEqual(se.crops_for_aspect("wat", 1.538), se._TALLY_CROPS["runes"])


class TestTheFixIsHonestlyLabelled(unittest.TestCase):
    def test_the_source_says_it_is_DERIVED_and_not_yet_measured(self):
        # this band has never been checked against a real 16:9 stash frame. Saying so in the file is
        # the difference between a fix and a claim.
        src = open(os.path.join(HERE, "stash_eye.py"), encoding="utf-8").read()
        self.assertIn("DERIVED, NOT YET MEASURED", src)


class TestAGuessNeverOutranksADifferentAnswer(unittest.TestCase):
    """v1907 — REG-204, filed OPEN on 2026-08-20 and closed here.

    `fuse_tab_signals` rule 1 — *"OCR tally wins over vague vault labels"* — returned the OCR tab
    before grid or model were consulted at all. The intent is sound: a specific tally word should
    beat a vague `shared`/`vault`/`stash` label. The implementation also beat a SPECIFIC AND
    DIFFERENT tally, so one witness — one that names itself a GUESS in its own docstring —
    overruled two that disagreed, and reported `sources: ['ocr']` while doing it.

    ⚠ THE REASON IT SAT OPEN IS THE REASON IT NEEDS THESE TESTS: the disagreement occurs in ZERO of
    the 68 stash-panel frames in his corpus, so his data cannot exercise the branch either way. A
    fix shipped on his frames alone would be untested; these drive it synthetically.
    [[gate-blind-to-unexercised-input]] [[d2r-multiwitness-corroboration]]"""

    def test_a_disagreeing_grid_stops_the_ocr_guess(self):
        tab, sources = se.fuse_tab_signals(ocr_tab="gems", grid_label="stash-runes")
        self.assertEqual(tab, "stash", "the OCR guess still overruled a grid that said otherwise")
        self.assertEqual(sources, ["tab-conflict"],
                         "a refusal has to carry its named reason, not an empty list")

    def test_a_disagreeing_model_stops_it_too(self):
        tab, sources = se.fuse_tab_signals(ocr_tab="gems", grid_label="stash", model_tab="runes")
        self.assertEqual((tab, sources), ("stash", ["tab-conflict"]))

    def test_the_frame_is_KEPT_as_a_stash_panel_not_dropped(self):
        """Both witnesses agree the panel IS a stash and disagree only about WHICH tally. Returning
        "" would send class_from_tab down the else branch and the frame would be dropped as
        `gameplay` — losing a real stash panel is a worse answer than declining to name its tab."""
        tab, _ = se.fuse_tab_signals(ocr_tab="gems", grid_label="stash-runes")
        self.assertEqual(se.class_from_tab(tab), "stash")
        self.assertNotEqual(se.class_from_tab(tab), "",
                            "a contradiction now throws the frame away entirely")

    def test_a_LAGGING_sticky_is_not_a_disagreeing_witness(self):
        """⚠ v1907 SHIPPED THIS WRONG AND THE REVIEW PASS CAUGHT IT 20 MINUTES LATER.

        The first version put `journal_tab` in the conflict set. `_kai_sticky_tab` says what it is
        in its own docstring: *"last deep tab with st<=ts+1.5s, HELD until the next deep tab (or
        25s)"*. So for up to 25 seconds after he clicks from Runes to Gems the sticky still says
        runes while the OCR correctly reads gems — and treating that as a contradiction demotes an
        ORDINARY TAB SWITCH to a generic stash with no tally.

        That trades a regression on something he does constantly against a contradiction measured
        at zero of 68 frames. REG-204's measurement named grid and model, and it named them for a
        reason. [[feedback-suspect-the-instrument]]"""
        tab, sources = se.fuse_tab_signals(ocr_tab="gems", journal_tab="runes")
        self.assertEqual(tab, "gems",
                         "a stale sticky from before a tab switch now cancels a correct OCR read")
        self.assertEqual(sources, ["ocr"])

    def test_a_VAGUE_label_is_still_beaten_by_the_tally(self):
        """The rule's real intent must survive the fix — this is the half that was right."""
        self.assertEqual(se.fuse_tab_signals(ocr_tab="gems", grid_label="stash",
                                             model_tab="shared")[0], "gems")
        self.assertEqual(se.fuse_tab_signals(ocr_tab="gems", journal_tab="personal")[0], "gems")

    def test_the_conflict_marker_is_not_mistaken_for_an_OCR_WITNESS(self):
        """`sources` is read downstream as a list of witnesses — `control_app` has two sites that do
        `owner = "ocr" if row.get("sources") else None`. A non-witness token in that list could
        therefore claim OCR ownership of a frame no reader vouched for.

        It cannot, and this pins WHY rather than leaving it to be re-reasoned: the conflict returns
        the tab `"stash"`, so `class_from_tab` yields the label `stash` and never `stash-*` — and
        the branch that turns a truthy `sources` into `owner="ocr"` is guarded by
        `label.startswith("stash-")`. The precedent for a named non-witness token is already in this
        file: the boot-screen guard returns `["boot-screen-guard"]`."""
        tab, sources = se.fuse_tab_signals(ocr_tab="gems", grid_label="stash-runes")
        self.assertEqual(sources, ["tab-conflict"])
        self.assertFalse(se.class_from_tab(tab).startswith("stash-"),
                         "a tab-conflict now produces a stash-* label, and the downstream branch "
                         "that reads a truthy `sources` as an OCR witness would fire on it")

    def test_agreement_still_gathers_its_witnesses(self):
        tab, sources = se.fuse_tab_signals(ocr_tab="gems", grid_label="stash-gems")
        self.assertEqual(tab, "gems")
        self.assertIn("grid", sources, "an agreeing witness stopped being counted")


class TestTheGridAgainstHandLabelledFrames(unittest.TestCase):
    """v1909 — THE CORPUS REG-205 SAID WAS MISSING, in its own words: *"Three hand-labelled frames is
    not a corpus."* This is twelve, labelled by OPENING the images.

    REG-203 (a fire-lit fight called `stash-gems`) and REG-205 (the tab is in the pixels, reading it
    is not solved) were both filed OPEN with the same reason — *retuning a pixel fingerprint needs
    its own before/after sweep over the whole corpus* — and there was nothing to sweep against.
    Now there is, and `tv/stash_grid_score.py` prints the before/after.

    ⚠ THE REFUTATION IS PINNED HERE SO IT IS NOT RE-DERIVED A THIRD TIME. `dark_cols` looks like the
    obvious separator: the real panels measured 7, 11, 14 and the fire-lit frames 31, 31, 39, 40, so
    an upper bound seems to cut cleanly. It does not. A REAL stash panel on the SHARED tab reads
    **40** — the same as the fire. Every bound that drops the false positives throws real stash
    panels away with them. I proposed exactly that bound, and his own frames refused it.
    [[feedback-suspect-the-instrument]] [[gate-blind-to-unexercised-input]]

    THE RATCHET: the disagreement count may go DOWN and may never go up, and every real panel must
    stay claimed — because the cheap way to "fix" the false positives is to stop admitting panels.
    """

    FALSE_TALLIES = 0    # v1909: was 3 here (8 across his whole hist) before the ceiling landed
    MISSED_TALLIES = 1   # 5_1784984201581 is a RUNES tab the grid calls plain `stash` — REG-205

    def _rows(self):
        import stash_grid_score as sgs
        rows, missing = sgs.score()
        if not rows:
            self.skipTest("his labelled frames are not in this checkout")
        return rows, missing

    def test_the_corpus_is_actually_present(self):
        """A missing frame must never read as a pass — an empty corpus scores perfectly."""
        rows, missing = self._rows()
        self.assertEqual(missing, [], "labelled frames vanished from the checkout: %s" % (missing,))
        self.assertEqual(len(rows), 12)

    def test_no_frame_without_a_panel_is_given_a_TALLY(self):
        """THE EXPENSIVE ERROR. A false tally writes a tally count for a panel that was never open;
        a missed one costs another look and the funnel rechecks. REG-203's fire-lit fight lived
        here — three of these frames, eight across his whole hist."""
        import stash_grid_score as sgs
        rows, _ = self._rows()
        false_t, _missed = sgs.tally_score(rows)
        self.assertLessEqual(len(false_t), self.FALSE_TALLIES,
                             "the grid names a tally on a frame that has no panel:\n  "
                             + "\n  ".join(false_t))

    def test_the_MISSED_tallies_do_not_grow_either(self):
        """The cheap way to kill false tallies is to stop naming any. This is the half that keeps
        the other test honest."""
        import stash_grid_score as sgs
        rows, _ = self._rows()
        _false, missed = sgs.tally_score(rows)
        self.assertLessEqual(len(missed), self.MISSED_TALLIES,
                             "the grid stopped naming tallies it used to get right:\n  "
                             + "\n  ".join(missed))

    def test_every_real_stash_panel_is_still_claimed(self):
        """The ceiling gates the TALLY branches only — the plain-stash path never needed
        panel_open, which is exactly why a real SHARED-tab panel at dark_cols=40 survives it. That
        is the fact I got wrong by reading the feature table instead of running it."""
        rows, _ = self._rows()
        lost = [r[0] for r in rows if r[1] and not r[5]]
        self.assertEqual(lost, [], "a retune stopped seeing REAL stash panels: %s" % (lost,))

    def test_the_ceiling_is_a_threshold_the_signal_can_CROSS(self):
        """A bound outside the signal's range is an absent bound wearing a tuned face. Real tally
        panels read 7 and 14 here, the false ones 31-39, and dark_cols spans 0-71 across his hist —
        so 24 sits inside a 17-column gap rather than on either knife-edge.
        [[feedback-threshold-above-the-ceiling]]"""
        import stash_eye as se
        rows, _ = self._rows()
        dcs = [r[4] for r in rows if r[4] is not None]
        self.assertLess(min(dcs), se._PANEL_MAX_DARKCOLS, "nothing is below the ceiling")
        self.assertGreater(max(dcs), se._PANEL_MAX_DARKCOLS, "nothing is above it — it never fires")
        self.assertGreater(se._PANEL_MAX_DARKCOLS, se._PANEL_MIN_DARKCOLS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
