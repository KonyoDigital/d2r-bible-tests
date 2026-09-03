"""v2469 — the probe primitives must keep the corrections that five scars bought.

Every one of these five was a probe of mine that measured something adjacent to the question and
produced a confident sentence. None was a wrong answer about the page; each was a right answer to a
question I had not meant to ask. [[feedback-suspect-the-instrument]]

⚠ This reads the JS SOURCE STRINGS the probes actually inject — not the module docstring, which
names every one of these mistakes while explaining them and would satisfy a lazier check.
[[source-reading-guard]]
"""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dom_probe as DP


class TheCorrectionsSurvive(unittest.TestCase):

    def test_leaf_text_skips_source_bearing_tags(self):
        """SCAR 1: `body *` includes SCRIPT, and its textContent is source code. Two probes read a
        JS comment and a build-stamp script tag as if they were on screen. Measured on his page:
        a naive walk matches 21 script nodes."""
        for tag in ("script", "style", "noscript", "template"):
            self.assertIn(tag, DP.SKIP_TAGS, "%r is not skipped — its text is source, not screen" % tag)
        self.assertIn("SKIP", DP.LEAF_TEXT.upper().replace("__LEAFTEXT", "SKIP"),
                      "the leaf walker no longer filters by tag at all")
        self.assertRegex(DP.LEAF_TEXT, r"getBoundingClientRect|clientWidth|width<2",
                         "the leaf walker no longer checks that the element has a box")

    def test_the_clip_test_knows_inline_from_block(self):
        """SCAR 2: an inline box reports clientWidth 0, so scrollWidth > clientWidth is false
        however long the text is. I nearly published 'this cannot clip' off exactly that."""
        # ⚠ ASSERT THE MECHANISM, NOT THE WORD. My first version checked `"inline" in
        # DP.CLIPPED` — satisfied by the word appearing in a comment, so removing the branch
        # entirely left it GREEN. The same "a window is not a scope" mistake I made an hour
        # earlier on a different guard. This requires the branch to actually READ cs.display.
        self.assertRegex(DP.CLIPPED, r"inline[^\n]*\.test\(\s*cs\.display",
                         "the clip test no longer branches on the computed DISPLAY, so it will "
                         "answer 'not clipped' for every inline element regardless of the text — "
                         "inline boxes report clientWidth 0")
        self.assertIn("parentElement", DP.CLIPPED,
                      "the inline branch no longer compares against the parent content edge, "
                      "which is the only thing that can answer for an inline box")

    def test_the_clip_test_says_when_overflow_is_visible(self):
        """An element with overflow:visible wraps; it cannot clip ITSELF. Saying so is the
        difference between a measurement and a guess."""
        self.assertIn("visible", DP.CLIPPED)
        self.assertIn("why", DP.CLIPPED, "a clip verdict with no reason is a number to argue with")

    def test_occlusion_samples_the_TARGET_not_the_coverer(self):
        """SCAR 3: sampling an element's own centre asks what covers IT. I used that twice to
        'refute' a claim that it covered something else."""
        self.assertRegex(DP.COVERS, r"function\s+__covers\s*\(\s*a\s*,\s*b\s*\)",
                         "the occlusion helper no longer takes both elements, so it cannot know "
                         "which direction it is measuring")
        self.assertIn("b.getBoundingClientRect", DP.COVERS,
                      "it no longer samples the TARGET's rect — sampling the coverer's own box is "
                      "the exact error this exists to prevent")
        self.assertIn("scroll fold", DP.COVERS,
                      "it no longer warns that a target below its own scroll fold looks identical "
                      "to an occluded one — that confusion cost an hour and a wrong bug report")

    def test_colour_is_measured_not_inferred(self):
        """SCAR 5: I checked for a `q-*` class, found zero, and nearly reported 'no item names are
        coloured'. Measured on his page, the element's class is `gp-nm` — which says nothing about
        rarity — and it paints rgb(199,179,119), D2's unique gold."""
        self.assertIn("getComputedStyle", DP.PAINTED)
        self.assertIn("color", DP.PAINTED, "the paint helper no longer reports the painted colour")

    def test_a_quoted_claim_can_be_checked_against_the_page(self):
        """SCAR 7: a cold read quoted a line as clipped. The item names in it were real and on
        screen; the connecting phrases were NOT IN THE DOM; the page had ZERO clipped nodes. It
        stitched a sentence out of words it could see.

        Every cold-read prompt says 'quote exact strings', on the assumption that a quote
        disciplines a claim. It only does if something checks it."""
        self.assertIn("__quoted", DP.QUOTED, "the quote checker is gone")
        self.assertIn("innerText", DP.QUOTED,
                      "it no longer reads the RENDERED text — checking a quote against innerHTML "
                      "would find markup and attributes the reader never saw")

    def test_a_stitched_quote_is_distinguished_from_an_absent_one(self):
        """The interesting case is not 'absent'. It is 'nearly every word is here and the sentence
        is not' — measured on the real confabulation, 5 of 6 words present. A checker that only
        answered yes/no would call that identical to a typo."""
        self.assertRegex(DP.QUOTED, r"fragmentsPresent",
                         "it no longer counts how many words of the quote appear separately, so a "
                         "stitched sentence is indistinguishable from a wrong one")
        self.assertIn("stitched", DP.QUOTED,
                      "it no longer NAMES the stitched-sentence case, which is the whole finding")

    def test_an_empty_quote_is_UNKNOWN_not_false(self):
        """Nothing to check is not the same as checked-and-absent."""
        self.assertRegex(DP.QUOTED, r"exists\s*:\s*null",
                         "an empty quote must answer UNKNOWN, never 'does not exist'")

    def test_the_prelude_carries_all_four(self):
        p = DP.prelude()
        for fn in ("__leafText", "__clipped", "__covers", "__painted", "__quoted"):
            self.assertIn(fn, p, "%s is missing from the prelude, so probes will hand-roll it "
                                 "again — which is how all five scars happened" % fn)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
