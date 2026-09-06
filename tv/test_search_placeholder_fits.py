# -*- coding: utf-8 -*-
"""v2697 — A PLACEHOLDER WRITTEN FOR A DESKTOP INPUT, SHOWN IN A 375px ONE.

The global search field carried a 70-character sentence — "Search a boss, act, zone, super-unique,
or item — jump straight to it". At 1440 it reads as a helpful hint. At 375 the box is roughly 285px
of usable width, so the browser cut it mid-word and it rendered as "...super-uniq", which reads as
BROKEN TEXT rather than as a hint.

⚠ HOW IT WAS FOUND, AND WHY THAT MATTERS. Not by a gate — every geometry gate was green, correctly,
because nothing was clipped: an input truncating its own placeholder is normal rendering, not
overflow. It was found by the SECOND EYE, cold, on the pixels, unprompted, answering "is any text
cut off mid-word". That is [[grok-second-eye]] earning its seat: the defect was invisible to every
measurement we had and obvious to something that simply looked.

THE LAW THIS PINS, which is not the number. CSS cannot reach a placeholder, so the narrow-width text
must exist as its own string and something must swap it. Three ways that goes wrong, one test each:

  1. The short string drifts back toward prose until it no longer fits. Pinned as a BUDGET derived
     from the box, not as the current length — a future edit may rewrite the words freely, it may
     not spend more than the 375px box can show.
  2. The swap runs at load only. Then a rotate or a window resize strands the wrong one, and the
     desktop sentence reappears in the narrow box with no reload to fix it. Pinned by requiring a
     `change` listener on the MediaQueryList, not just an initial call.
  3. The swap sits ABOVE the input it mutates. `getElementById` during parse returns null for an
     element the parser has not reached, the IIFE returns silently, and the page looks fine at
     desktop width forever — this repo has paid for that exact shape four times
     ([[console-ui-two-script-blocks]]). Pinned by BYTE ORDER in the file.

⚠ THIS GUARD READS SOURCE TEXT, so it obeys [[source-reading-guard]]: every anchor is matched with
both ends bound, the match COUNT is asserted rather than the truthiness of a find, and a count that
is not exactly 1 fails LOUDLY as a broken guard instead of quietly as a passing one. A test that
cannot find what it grades must not report green.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

BIBLE = os.path.join(ROOT, "bible.html")

# The narrow viewport the swap is for, and what the input can actually show there.
# 375px viewport, less the page gutters, the leading magnifier and the field's own padding,
# measured at ~90px total -> ~285px of text. At the field's ~13px font an average glyph runs
# ~7.2px, so the budget is 285/7.2 ~= 39 characters. Rounded DOWN to 40 as a ceiling with no
# slack for a descender-heavy string.
NARROW_PX = 640          # the breakpoint the swap keys on
SHORT_BUDGET_CHARS = 40  # what fits the 375px box, derived above


def _src():
    return io.open(BIBLE, encoding="utf-8").read()


def _one(src, pattern, what):
    """Return the single match for `pattern`, or raise with the COUNT that was actually found.

    A guard that greps must fail on its own reach. `re.search` returning None and returning a
    match are two different worlds, and a test that treats "not found" as "nothing to check"
    is the [[feedback-blind-fixture-green-gate]] defect with a regex in it.
    """
    hits = re.findall(pattern, src, re.S)
    if len(hits) != 1:
        raise AssertionError(
            "GUARD CANNOT GRADE: expected exactly 1 %s, found %d. The anchor moved or the "
            "element was renamed — fix this test before trusting any verdict it prints." %
            (what, len(hits))
        )
    return hits[0]


class SearchPlaceholderFits(unittest.TestCase):

    def setUp(self):
        self.src = _src()
        # Bind BOTH ends of the input tag. An open-ended window would happily read the next
        # element's attributes as this one's -- [[source-window-shortcut]], 4x in one session.
        self.tag = _one(self.src, r'(<input id="gsearch-input"[^>]*>)', "gsearch-input tag")

    # ---- 1. both strings exist, and the short one fits the box -----------------------------

    def test_both_placeholders_are_declared(self):
        for attr in ("data-ph-full", "data-ph-short"):
            self.assertIn(attr, self.tag,
                          "%s is missing from the search input -- the narrow-width text has no "
                          "source to come from, so the desktop sentence is all there is." % attr)

    def test_short_placeholder_fits_the_narrow_box(self):
        brief = _one(self.tag, r'data-ph-short="([^"]*)"', "data-ph-short value")
        self.assertTrue(brief.strip(), "data-ph-short is empty -- an empty hint is not a hint.")
        self.assertLessEqual(
            len(brief), SHORT_BUDGET_CHARS,
            "data-ph-short is %d chars; the 375px field shows about %d. At %d it truncates "
            "mid-word again, which is the exact defect this test exists for. Rewrite the words "
            "shorter -- do NOT raise the budget, it is derived from the box." %
            (len(brief), SHORT_BUDGET_CHARS, len(brief))
        )

    def test_short_is_materially_shorter_than_full(self):
        brief = _one(self.tag, r'data-ph-short="([^"]*)"', "data-ph-short value")
        full = _one(self.tag, r'data-ph-full="([^"]*)"', "data-ph-full value")
        self.assertLess(
            len(brief), len(full),
            "data-ph-short (%d) is not shorter than data-ph-full (%d) -- the swap would show the "
            "same overflowing string under a different name." % (len(brief), len(full))
        )

    # ---- 2. the swap reacts to a resize, not only to a load --------------------------------

    def test_swap_keys_on_the_narrow_breakpoint(self):
        """⚠ v2698 — THIS ASSERTION USED TO BE VACUOUS, and a code review caught it.

        It read `assertIn("max-width: 640px", self.src)` against the WHOLE 6MB file. That string
        already appeared TWICE in the stylesheet before this feature existed (measured:
        `git show 707c2e6c:bible.html | grep -c "max-width: 640px"` -> 2), so deleting the entire
        swap script left it green. It pinned nothing, while REG-663 claimed it pinned a law.
        Bind it to the swap block instead, which is the only place the breakpoint means anything.
        """
        block = self._swap_block()
        self.assertIn(
            "max-width: %dpx" % NARROW_PX, block,
            "the swap does not key on the %dpx breakpoint. NOTE: this now greps the swap BLOCK, "
            "not the whole file -- the file has unrelated CSS media queries at this width and "
            "matching those proved nothing." % NARROW_PX
        )

    def test_swap_listens_for_change_not_just_load(self):
        block = self._swap_block()
        self.assertTrue(
            "addEventListener" in block or "addListener" in block,
            "the placeholder swap runs at load only. A rotate or a resize then strands the "
            "desktop sentence in the narrow box, with no reload to correct it."
        )

    # ---- 3. the swap runs AFTER the element it mutates -------------------------------------

    def test_swap_sits_below_the_input_it_mutates(self):
        """⚠ v2698 — THIS ASSERTION COULD NOT FAIL, and a code review caught it.

        It compared the SECOND occurrence of "data-ph-short" against the START of the input tag.
        Occurrence #1 is the input's own attribute, which sits INSIDE the tag and is therefore
        always greater than the tag's start; occurrence #2 is later still. Move the script above
        the input -- the exact shape this test exists for -- and occurrence #2 becomes the input's
        attribute, which is STILL inside the tag and still greater. Green in both worlds.

        The fix is to compare the two things the law is actually about: where the SCRIPT BLOCK
        begins, and where the input tag ENDS. Nothing else settles parse order.
        """
        i_input_end = self.src.index(">", self.src.index('<input id="gsearch-input"'))
        i_block = self._swap_block_start()
        self.assertGreater(
            i_block, i_input_end,
            "the placeholder swap block begins at %d, BEFORE the input tag closes at %d. "
            "getElementById returns null during parse for an element the parser has not reached, "
            "the handler returns silently, and the page looks correct at desktop width forever. "
            "This repo has shipped that shape four times -- see console-ui-two-script-blocks."
            % (i_block, i_input_end)
        )

    def _swap_block_start(self):
        """Byte offset of the <script> that performs the swap.

        Located by CONTENT, not by counting occurrences: the block is the one that both reads
        `data-ph-short` and calls `matchMedia`. Counting occurrences is what made the order test
        vacuous, so this deliberately does not do that.
        """
        hits = []
        pos = 0
        while True:
            st = self.src.find("<script", pos)
            if st < 0:
                break
            en = self.src.find("</script>", st)
            if en < 0:
                break
            body = self.src[st:en]
            if "data-ph-short" in body and "matchMedia" in body:
                hits.append(st)
            pos = en + 1
        if len(hits) != 1:
            raise AssertionError(
                "GUARD CANNOT GRADE: expected exactly 1 <script> block containing both "
                "`data-ph-short` and `matchMedia`, found %d. The swap was removed, split, or "
                "duplicated -- fix this test before trusting any verdict it prints." % len(hits)
            )
        return hits[0]

    def _swap_block(self):
        """The swap script's source, bound at both ends."""
        st = self._swap_block_start()
        en = self.src.find("</script>", st)
        return self.src[st:en]


if __name__ == "__main__":
    unittest.main(verbosity=2)
