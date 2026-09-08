#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2800 — HALF HIS PROOF PHOTOS WERE REPORTED MISSING BECAUSE THE ID WAS SPELLED THE OTHER WAY.

⚠⚠ MEASURED 2026-09-08, and the split is almost exactly even:

    chron_evidence.json witness rows   `reel_`-prefixed  4,106
                                        BARE             4,411
    directories under frames/hist      BARE                623
                                        `reel_`-prefixed     40

Two conventions in one field, and the on-disk convention is the OPPOSITE of what most ids suggest.
`_hist_frame_paths` only ever tried the id exactly as given, so every lookup whose spelling did not
match its directory reported the photo as ABSENT.

    _hist_has_frame over 300 sampled witnesses     29%
    ...also trying the other spelling              56%
    recovered by one change                        82 of 300

★ WHY THIS IS NOT COSMETIC. Those photos are the `provenance` leg of the extraction contract — the
picture behind a banked name — and he is deciding which footage to delete. **A photo that is merely
looked up wrongly is indistinguishable from one that is gone**, and once the footage is pruned the
difference stops being recoverable. He was told 41% were already lost; the true figure was measured
only after this, and the gap between "missing" and "misfiled" was 27 points of it.
[[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]

⚠ THE LOOKUP IS WIDENED, THE ID IS NOT REWRITTEN. Nothing downstream starts seeing a spelling it
did not ask for — the same discipline `artUrl`'s apostrophe fold follows. [[copy-drift]]
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import control_app as CA  # noqa: E402


class TheProofPhotoIsFoundUnderEitherSpelling(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self._hist = CA.HIST_DIR
        CA.HIST_DIR = self.d

    def tearDown(self):
        CA.HIST_DIR = self._hist
        shutil.rmtree(self.d, ignore_errors=True)

    def _put(self, reel_dir, frame="f_123.jpg"):
        os.makedirs(os.path.join(self.d, reel_dir), exist_ok=True)
        io.open(os.path.join(self.d, reel_dir, frame), "wb").write(b"\xff\xd8jpeg")
        return frame

    # ── ⚠⚠ THE LAW, BOTH DIRECTIONS ─────────────────────────────────────────────────────────
    def test_a_BARE_directory_is_found_by_a_PREFIXED_id(self):
        """★★★ The common case: 623 of 663 directories are bare, and 4,106 rows ask with a
        `reel_` prefix."""
        fr = self._put("s_999_1")
        self.assertTrue(
            CA._hist_has_frame("reel_s_999_1/%s" % fr),
            "a photo in a BARE directory was reported missing when asked for by its `reel_`-"
            "prefixed id. 4,106 witness rows spell it that way and 623 of 663 directories do not.")

    def test_a_PREFIXED_directory_is_found_by_a_BARE_id(self):
        """⚠ The other 40 directories, and the 4,411 rows that ask bare. Fixing only one direction
        would move the loss rather than remove it."""
        fr = self._put("reel_s_888_2")
        self.assertTrue(
            CA._hist_has_frame("s_888_2/%s" % fr),
            "a photo in a `reel_`-prefixed directory was reported missing when asked for bare")

    def test_the_relative_path_it_returns_actually_EXISTS(self):
        """⛔ Finding it is not enough — the UI builds `/hist/<rel>` from this, so a rel that does
        not resolve renders a broken image, which reads as 'the evidence is gone'."""
        fr = self._put("s_777_3")
        rel = CA._hist_frame_rel("reel_s_777_3/%s" % fr)
        self.assertTrue(rel, "no relative path returned for a photo that is on disk")
        self.assertTrue(os.path.isfile(os.path.join(self.d, rel)),
                        "the returned rel %r does not point at a real file" % rel)

    def test_a_GENUINELY_absent_photo_is_still_absent(self):
        """⚠ THE OTHER DIRECTION, and it matters most here: widening a lookup until everything is
        'found' would make the 41%-already-gone figure disappear without a single file coming back.
        A law that only checks the permissive side invites exactly that."""
        self._put("s_666_4")
        self.assertFalse(CA._hist_has_frame("s_666_4/f_nope.jpg"),
                         "a frame that does not exist was reported present")
        self.assertFalse(CA._hist_has_frame("s_nosuchreel/f_123.jpg"),
                         "a reel that does not exist was reported present")
        self.assertEqual(CA._hist_frame_rel("s_nosuchreel/f_123.jpg"), "",
                         "an absent photo returned a path instead of an empty string")


if __name__ == "__main__":
    unittest.main(verbosity=2)
