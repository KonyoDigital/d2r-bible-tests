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
    # v1919 — BACK TO 1, AND THE ONE IS REAL THIS TIME. Widening the corpus into the reels added a
    # genuine RUNES panel (f_1784984269782) that the grid fingerprint calls plain `stash`. It is a
    # MISS, not a false tally, and it is contained: the gem reader names that frame `runes`
    # correctly, so fuse_tab_signals still answers ('runes', ['gem']) — the fingerprint being blind
    # to a tab no longer decides anything on its own. Widening a corpus is supposed to surface
    # exactly this; a number that only ever goes down is a number nobody is testing.
    MISSED_TALLIES = 1

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
        # v2047 — 10, not 14. Rotation ate 7 entries that named frames in the ROTATING archive; the
        # survivors are now copied to tv/frames/corpus/ where nothing prunes them, and three fresh
        # negatives were labelled by opening them. The 7 are recorded under `_lost` rather than
        # deleted, because a corpus that quietly shrinks scores BETTER every time it loses a hard
        # case. Raise this number when frames are added; never lower it to make a red run green.
        self.assertEqual(len(rows), 10, "the corpus lost frames — the survivors live in "
                                        "tv/frames/corpus/ precisely so this cannot happen again")

    def test_the_corpus_still_contains_cases_that_could_FAIL(self):
        """THE EROSION GUARD, and it is the one that was missing.

        By 2026-08-24 all 7 `panel: false` entries had been eaten by archive rotation, leaving 7
        positives and nothing else. The ratchet FALSE_TALLIES = 0 was then being measured against
        ZERO cases that could ever produce a false tally — a perfect score from an empty exam.

        A corpus of positives cannot catch the expensive error, which is claiming a panel that was
        never open (REG-203: a fire-lit fight read as `stash-gems`). The replacements are deliberately
        the HARD kind: dark_cols 47, 38 and 33, and 47 is higher than the real SHARED-tab panel's 40.
        [[gate-blind-to-unexercised-input]] [[feedback-blind-fixture-green-gate]]
        """
        import stash_grid_score as sgs
        truth = sgs.load_truth()
        negatives = [n for n, t in truth.items() if not t.get("panel")]
        positives = [n for n, t in truth.items() if t.get("panel")]
        self.assertGreaterEqual(len(negatives), 3,
                                "the corpus has %d negative(s) — it can no longer catch a FALSE "
                                "tally, which is the expensive error" % len(negatives))
        self.assertGreaterEqual(len(positives), 5,
                                "the corpus has %d positive(s) — it can no longer catch a MISS"
                                % len(positives))

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


class TestTheActiveTabGem(unittest.TestCase):
    """v1912 — REG-205 said *"the selected stash tab IS visible in the pixels; reading it is not
    solved."* It is solved: the marker is the GEM, not the brightness.

    REG-205 tried the obvious thing — split the chrome into five equal cells, take the argmax mean
    luminance — and got **1 of 3 on margins of 1-5 grey levels**, because the labels are not equal
    width and a cell straddles two of them. The obvious thing was the wrong FEATURE. D2R draws a
    gold box around the active tab AND sets a small blue gem on the underline beneath it: tiny,
    saturated, at a position no other chrome occupies.

    **12 of 12 on the hand-labelled corpus, zero false tabs on the seven non-panels**, and 8 named
    frames across his whole 883-frame hist.

    ⚠ AND IT CAUGHT A WRONG LABEL. On `5_1784984201581` the detector said PERSONAL where REG-205's
    hand label said RUNES. The disagreement WAS the finding: zoomed to 2.6x, the gold box and the
    gem are both on PERSONAL, a WRAITHSTEP tooltip covers its text, RUNES is grey with no border,
    and the grid below holds gear. The detector was right and the label was wrong.
    [[feedback-contradiction-is-the-finding]]

    ⚠ THE FALSE POSITIVE THAT ALMOST SHIPPED: without its guards this named a tab on 131 of 883
    frames, 125 of them "personal" — and five of six I opened were SOLID BLUE capture failures,
    where every pixel qualifies as blue. Same shape as this file's oldest scar, "69 wallpaper frames
    sealed as stash-gems". Both guards sit in enormous measured gaps: qualifying blue px real 2-18
    against 1025, strip luminance sd real 32.7-35.2 against 0.00."""

    def _frames(self):
        import json
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "stash_grid_truth.json"), encoding="utf-8") as fh:
            return json.load(fh)["_frames"], os.path.join(here, "frames", "hist")

    def test_it_reads_every_labelled_panel_and_invents_none(self):
        frames, hist = self._frames()
        if not os.path.isfile(os.path.join(hist, list(frames)[0])):
            self.skipTest("his labelled frames are not in this checkout")
        wrong = []
        for f, t in sorted(frames.items()):
            got, _d = se.tab_from_gem(os.path.join(hist, f))
            want = t.get("tab") if t.get("panel") else None
            if (got or None) != want:
                wrong.append("%s: said %r, truth %r" % (f, got or None, want))
        self.assertEqual(wrong, [], "\n  ".join(wrong))

    def test_a_solid_blue_capture_never_names_a_tab(self):
        """The failure that almost shipped, driven directly rather than described."""
        import shutil
        import tempfile
        from PIL import Image
        root = tempfile.mkdtemp(prefix="bluefail-")
        self.addCleanup(shutil.rmtree, root, True)
        p = os.path.join(root, "blue.jpg")
        Image.new("RGB", (1280, 800), (0, 0, 255)).save(p, quality=90)
        tab, detail = se.tab_from_gem(p)
        self.assertEqual(tab, "", "a solid blue frame was given a stash tab: %r" % (detail,))
        self.assertIn("why", detail, "it refused without saying why")

    def test_a_BLUE_WASH_over_real_chrome_is_refused_too(self):
        """The stddev guard catches a flat blue SCREEN. This is the other half — a frame with real
        chrome structure and far too much blue in the gem band, which is what `_GEM_MAX_PX` is for.
        Without it the "centre of the strongest blue" is arithmetic on a wash, and it lands
        somewhere, and somewhere is always one of five tabs."""
        import shutil
        import tempfile
        from PIL import Image, ImageDraw
        frames, hist = self._frames()
        real = os.path.join(hist, "8_1785078207015.jpg")
        if not os.path.isfile(real):
            self.skipTest("his labelled frames are not in this checkout")
        base = Image.open(real).convert("RGB")
        w, h = base.size
        b = se._TAB_CHROME
        d = ImageDraw.Draw(base)
        y0 = h * b[1] + (h * (b[3] - b[1])) * se._GEM_BAND[0]
        y1 = h * b[1] + (h * (b[3] - b[1])) * se._GEM_BAND[1]
        d.rectangle([w * b[0], y0, w * b[2], y1], fill=(20, 40, 230))
        root = tempfile.mkdtemp(prefix="bluewash-")
        self.addCleanup(shutil.rmtree, root, True)
        p = os.path.join(root, "wash.jpg")
        base.save(p, quality=92)
        tab, detail = se.tab_from_gem(p)
        self.assertGreater(detail.get("stripSd", 0), se._GEM_MIN_STRIP_SD,
                           "the fixture lost its chrome structure, so this proves nothing")
        self.assertEqual(tab, "", "a blue wash over the gem band still named a tab: %r" % (detail,))
        self.assertIn("too much blue", detail.get("why", ""))

    def test_the_pitch_predicted_the_two_tabs_it_had_never_seen(self):
        """personal 0.141, shared 0.324, materials 0.691 — one and two pitches apart. That fixes
        gems at 0.508 and runes at 0.875, and when v1912 shipped, NEITHER had a frame in his corpus;
        both were recorded UNVERIFIED rather than counted as covered.

        ✅ v1919 — vault_corpus.py found them in the REELS, a half of the archive no stash
        measurement had touched, and the prediction landed on the nose:
            f_1784984269782  RUNES  x=0.874  vs 0.875 predicted   (off by 0.001)
            f_1784984271825  GEMS   x=0.506  vs 0.508 predicted   (off by 0.002)
        A pitch derived from three tabs placed the other two to within two thousandths of the strip.
        This pins the arithmetic AND the two frames, so a retune has to keep both."""
        self.assertAlmostEqual(se._GEM_FIRST + se._GEM_PITCH * 1, 0.3245, places=3)
        self.assertAlmostEqual(se._GEM_FIRST + se._GEM_PITCH * 2, 0.5080, places=3)
        self.assertAlmostEqual(se._GEM_FIRST + se._GEM_PITCH * 3, 0.6915, places=3)
        self.assertAlmostEqual(se._GEM_FIRST + se._GEM_PITCH * 4, 0.8750, places=3)
        here = os.path.dirname(os.path.abspath(__file__))
        for frame, want, x in (("reel_s_1784984019250_95276/f_1784984269782.jpg", "runes", 0.874),
                               ("reel_s_1784984019250_95276/f_1784984271825.jpg", "gems", 0.506)):
            p = os.path.join(here, "frames", "hist", frame)
            if not os.path.isfile(p):
                self.skipTest("his reels are not in this checkout")
            got, d = se.tab_from_gem(p)
            self.assertEqual(got, want, "%s: the reader stopped seeing the %s tab" % (frame, want))
            self.assertAlmostEqual(d.get("gemX", 0), x, places=2,
                                   msg="the gem moved on a frame the geometry was verified against")

    def test_the_gem_is_a_witness_in_the_fusion_and_never_outranks_the_WORDS(self):
        self.assertEqual(se.fuse_tab_signals(gem_tab="materials"), ("materials", ["gem"]))
        self.assertEqual(se.fuse_tab_signals(ocr_tab="gems", gem_tab="gems"), ("gems", ["ocr", "gem"]))
        self.assertEqual(se.fuse_tab_signals(ocr_tab="gems", gem_tab="runes"),
                         ("stash", ["tab-conflict"]))
        self.assertEqual(se.fuse_tab_signals(gem_tab="nonsense"), ("", []))


if __name__ == "__main__":
    unittest.main(verbosity=2)
