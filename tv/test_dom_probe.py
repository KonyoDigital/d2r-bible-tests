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


def _run_quoted(pairs):
    """EXECUTE the helper in a real JS engine and return its answers. -> [dict]

    Reading the source cannot tell which branch a ternary takes, which is exactly how the previous
    version of this test stayed green. `node` is required; without it the answer is UNKNOWN and the
    test SKIPS loudly rather than passing on no evidence. [[feedback-blind-fixture-green-gate]]
    """
    import json as _json
    import shutil as _shutil
    import subprocess as _subprocess
    import tempfile as _tempfile
    node = _shutil.which("node")
    if not node:
        raise unittest.SkipTest("node is not installed, so the helper could not be RUN — that is "
                                "UNKNOWN, not a pass")
    calls = ",".join("__quotedIn(%s, %s)" % (_json.dumps(q), _json.dumps(b)) for q, b in pairs)
    src = ("var document={body:{innerText:''}};\n" + DP.prelude()
           + "\nconsole.log(JSON.stringify([" + calls + "]))")
    with _tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(src)
        path = fh.name
    try:
        out = _subprocess.check_output([node, path], stderr=_subprocess.STDOUT, timeout=60)
        return _json.loads(out.decode("utf-8", "replace"))
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


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
        """The interesting case is not 'absent'. It is 'every word is here and the sentence is not'.

        ⚠⚠ THIS TEST USED TO GREP AND IT STAYED GREEN OVER THE EXACT DEFECT IT NAMES. It asserted
        that the source CONTAINS "fragmentsPresent" and "stitched" — both of which remained true
        while the helper answered "NOT on the page at all" about a quote whose every word was on
        the page. A guard that reads for a WORD cannot see a wrong BRANCH; the words were there
        and the ternary sent the strongest case to the weakest label. Caught by the v2471
        review-after-ship pass, not by this file. It now RUNS the helper. [[source-reading-guard]]
        """
        got = _run_quoted([
            ("Fleshrender mighty", "the mighty Fleshrender item"),   # every word present
            ("mighty Fleshrender sword", "the mighty Fleshrender item"),  # 2 of 3
            ("Fleshrender absent", "nothing similar here at all"),    # none present
            ("of the", "the top of it"),                              # nothing testable
            ("best expected yield", "best expected yield is shown"),  # really there
        ])
        self.assertEqual(
            got[0]["verdict"], "stitched",
            "a quote whose EVERY word is on the page and whose phrase is not was reported as %r. "
            "That is the strongest form of the confabulation this helper exists to name, and it "
            "was wearing the label for total absence: %s"
            % (got[0].get("verdict"), str(got[0].get("why"))[:110]))
        self.assertEqual(got[0]["fragmentsPresent"], got[0]["fragmentsTotal"],
                         "the 100%-present case no longer reports all words present")
        self.assertEqual(got[1]["verdict"], "partly", "a partly-present quote lost its own name")
        self.assertEqual(got[2]["verdict"], "absent", "a genuinely absent quote lost its own name")
        self.assertEqual(
            got[3]["verdict"], "untestable",
            "a quote with no word over three characters was judged %r. Nothing in it could be "
            "checked, so the honest answer is UNKNOWN rather than a verdict about the page."
            % got[3].get("verdict"))
        self.assertTrue(got[4]["exists"], "a quote that IS on the page was not found")

    def test_the_verdicts_are_all_different_words(self):
        """Four outcomes collapsing into one label is the defect; pin that they stay four."""
        got = _run_quoted([
            ("Fleshrender mighty", "the mighty Fleshrender item"),
            ("mighty Fleshrender sword", "the mighty Fleshrender item"),
            ("Fleshrender absent", "nothing similar here at all"),
            ("of the", "the top of it"),
        ])
        verdicts = [g["verdict"] for g in got]
        self.assertEqual(len(set(verdicts)), 4,
                         "two of the four outcomes now answer with the same word: %s" % verdicts)

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
