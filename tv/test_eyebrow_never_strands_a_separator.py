# -*- coding: utf-8 -*-
"""v2728 — A WRAPPED LINE MUST NEVER BEGIN WITH A SEPARATOR.

TWO INDEPENDENT COLD READS flagged this, on different versions, neither knowing the other had:
    v2719  "'· OF 383' sits on its own line ... reads as broken"
    v2722  "'· OF 383' on its own line"
Two readers with no memory of each other reporting the same thing is the signal that made the
terror-level defect worth chasing, and that one was real too.

MEASURED on his live console at five widths before the fix:
    >=1000px  box 527  natural 516   fits
      901px   box 440  natural 516   WRAPS      <- the sighting
      375px   box 302  natural 516   WRAPS
The eyebrow is uppercase mono at .28em tracking, so the text node wraps inside the flex item and
the break lands BEFORE the '·', leaving a separator alone at the start of the continuation line.

=== WHY THE FIX IS A NON-BREAKING SPACE AND NOT ANY OF THE FOUR OPTIONS THE ROW LISTED ===
The row ruled out four and left the item filed-not-fixed. Each is still ruled out, and one is now
ruled out by MEASUREMENT rather than by argument:
  · white-space:nowrap        -> stops wrapping and CLIPS instead. Clipped is destroyed; wrapped is
                                 merely ugly. Strictly worse.
  · smaller font / tracking   -> MEASURED 2026-09-06 and it is INSUFFICIENT, which nobody had
                                 checked: .14em gives 434 against a 440 box at 901 (it would work
                                 there), but at 375 the box is 302 and even .06em is 387. Forty-five
                                 uppercase mono characters do not fit 302px at any legible tracking.
                                 A fix that works at one width and not the other is a narrower bug.
  · suppress a leading '·' in CSS -> correct that CSS cannot detect a line start.
  · restructure into nowrap segments -> the segments already travel together.

THE FIFTH OPTION: the separators are plain ' · ' in a text node, so the browser has a break
opportunity on BOTH sides of the dot and takes the left one. Binding the dot to the word BEFORE it
with U+00A0 DELETES that opportunity. CSS cannot detect a line start — but the markup can remove
the place a line could start. It changes no font, no tracking, no layout and no width, so it cannot
clip: wrapping still happens, one break opportunity later.

PROVEN RED THEN GREEN IN THE SAME PAGE, by cloning the live element and replacing U+00A0 with a
plain space in the clone — same box, same styles, same fonts, measured with Range rects per glyph:
    901px  OLD 't·' STRANDS  ->  NEW 'th' clean
    375px  OLD 'tf' clean    ->  NEW 'tf' clean
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

UI = os.path.join(HERE, "control_ui.html")
NBSP = u" "


def _eyebrow_spans(src):
    """(start, end) of every `.hh-eye` builder in `src` — the ONE place the region is bounded.

    ⚠ Anchored on the opening `<div class="hh-eye"` and closed at the `</div>` that ends it, so
    this never reads a fixed window past the region — [[source-reading-guard]], which cost this
    repo four false readings in one day. A concatenation is followed across `+` joins because the
    eyebrow is assembled from three or four pieces and the separator lives in the middle piece.
    Shared by the law and by the red-proof scope check below, so the two can never disagree about
    where an eyebrow ends. [[copy-drift]]
    """
    out = []
    for m in re.finditer(r'<div class="hh-eye">', src):
        end = src.find("</div>", m.end())
        if end < 0:
            raise AssertionError("GUARD CANNOT GRADE: an .hh-eye div is never closed at char %d"
                                 % m.start())
        out.append((m.start(), end))
    return out


def _eyebrow_literals():
    """Every JS string literal that builds an `.hh-eye` line, bound at BOTH ends."""
    src = io.open(UI, encoding="utf-8").read()
    return [src[a:b] for a, b in _eyebrow_spans(src)]


class EyebrowNeverStrandsASeparator(unittest.TestCase):

    def setUp(self):
        self.blocks = _eyebrow_literals()

    def test_the_guard_can_actually_see_the_eyebrows(self):
        """⚠ A law that found nothing to grade passed by examining ZERO candidates.

        This repo has shipped exactly that: a loop over an empty match set, green because there
        were no cases rather than because the cases were right. [[zero-needs-a-denominator]]
        """
        self.assertTrue(
            self.blocks,
            "no `<div class=\"hh-eye\">` was found in control_ui.html at all. The eyebrow was "
            "renamed or removed — fix this guard before trusting any verdict it prints."
        )
        with_sep = [b for b in self.blocks if u"·" in b]
        self.assertTrue(
            with_sep,
            "%d eyebrow(s) found and NOT ONE contains a '·' separator, so this law is grading "
            "nothing. Either the separators are gone (delete this file) or the reader is broken."
            % len(self.blocks)
        )

    def test_no_separator_can_begin_a_wrapped_line(self):
        """THE LAW: every '·' in an eyebrow is bound to the text BEFORE it by a non-breaking space.

        ⚠⚠ IT MUST ACCEPT BOTH SPELLINGS, AND THE FIRST CUT DID NOT — it read the SOURCE and
        demanded a literal U+00A0 one character back, which is wrong for the form actually shipped.
        These are JS string literals inside an HTML file, so `\u00a0` is a six-character ESCAPE in
        the source that the engine turns into one NBSP in the DOM. The law rejected the working fix
        and reported that the separator was preceded by `'0'` — the last digit of the escape.
        Verified independently on real pixels: the rendered text node contains U+00A0 (`nbsp=True`)
        and no wrapped line begins with a separator. A guard that grades the source must know which
        of the two layers it is looking at. [[source-reading-guard]] [[feedback-suspect-the-instrument]]
        """
        ESCAPES = ("\\u00a0", "\\u00A0", "\\xa0", "\\xA0", "&nbsp;")
        # REG-1893 - no eyebrow, or no separator in any of them, and the loop below grades nothing
        self.assertTrue(any(u"·" in b for b in self.blocks),
                        "%d eyebrow(s) read and not one '·' among them, so no separator was graded"
                        % len(self.blocks))
        for block in self.blocks:
            for m in re.finditer(u"·", block):
                i = m.start()
                head = block[:i]
                ok = head.endswith(NBSP) or any(head.endswith(e) for e in ESCAPES)
                self.assertTrue(
                    ok,
                    "a '·' in an eyebrow is not bound to the word before it (source ends %r). The "
                    "browser can then break BEFORE the separator and the wrapped line begins with "
                    "a bare '·' — exactly what two independent cold readers reported on two "
                    "different versions. Accepted bindings: a literal U+00A0, a \\u00a0 / \\xa0 "
                    "escape, or &nbsp;. Context: ...%s..."
                    % (head[-8:], block[max(0, i - 40):i + 12].replace("\n", " "))
                )

    def test_a_COUNT_is_never_stranded_from_the_word_that_names_it(self):
        """v2733 — THE SIBLING MY OWN FIX MISSED, AND A CROSS-FAMILY EYE FOUND IT.

        REG-689 bound the SEPARATOR to the word before it. It did not bind `of` to its NUMBER, and
        the eyebrow builds `'fastest in hell\u00a0· of ' + count` — an ordinary space between the
        word and the figure. Asked cold about a console capture, a different model family reported:
        *"the line 'OF 34' wraps so the number '34' sits alone on its own line directly above the
        item name"*.

        ⚠⚠ A STRANDED NUMBER IS WORSE THAN A STRANDED SEPARATOR. A lone '·' reads as broken and is
        ignored; a lone '34' reads as a QUANTITY OF THE THING BELOW IT. This repo has the scar
        already — a cold eye once read "1.00 of 1.80" as "1.00 of 1.00" and inverted what a bar
        meant. [[unknown-stays-unknown]] [[label-outlived-referent]]

        ⚠ AND THIS IS A [[sweep-dont-ask]] MISS ON MY PART: I fixed one break opportunity in this
        exact string and did not sweep the string for its siblings. The separator and the count are
        the same defect one word apart.
        """
        src = io.open(UI, encoding="utf-8").read()
        for m in re.finditer(r"'[^']*\bof '\s*\+", src):
            frag = src[max(0, m.start() - 70):m.end()]
            if "hh-eye" not in frag and "fastest" not in frag:
                continue          # only the eyebrow strings are in scope here
            self.fail(
                "an eyebrow builds \"... of \" + <count> with an ordinary space, so the line can "
                "break between the word and its number and leave the figure alone at the start of "
                "a line, reading as a quantity of whatever follows it. Bind it: 'of\\u00a0'. "
                "Context: ...%s..." % frag[-58:].replace("\n", " ")
            )

    def test_nowrap_was_NOT_used_because_it_clips(self):
        """⚠ The rejected option must stay rejected. Clipped is destroyed; wrapped is merely ugly.

        If a later edit reaches for `white-space: nowrap` on the eyebrow to 'fix' this, the
        stranded separator disappears and the END OF THE SENTENCE disappears with it — a strictly
        worse defect that looks tidier, which is how it would survive review.
        """
        src = io.open(UI, encoding="utf-8").read()
        m = re.search(r"\.hh-eye\s*\{", src)
        self.assertIsNotNone(m, "GUARD CANNOT GRADE: no `.hh-eye {` rule in control_ui.html")
        end = src.find("}", m.end())
        rule = src[m.end():end]
        self.assertNotRegex(
            rule, r"white-space\s*:\s*nowrap",
            "`.hh-eye` sets white-space:nowrap. That does not fix the stranded separator, it "
            "CLIPS the line instead — measured: the string is 516px against a 440px box at 901 "
            "and a 302px box at 375, so nowrap loses the end of the sentence at both."
        )

    def test_its_red_proof_tampers_the_eyebrows_and_nothing_else(self):
        """REG-1513 — THE PROOF'S ANCHOR WAS A SPELLING, NOT A PLACE, AND ANOTHER BRANCH SPELLED IT TOO.

        MEASURED on v3524: the proof below anchored on the bare escape-then-dot and declared 4
        matches — the two sites in each of the two `.hh-eye` builders. river-alarm's REG-1462 fleet
        compare footer (bb31d730) then glued ITS dots on both sides with the same escape, and the
        anchor count went 4 -> 7 with the extra 3 at the footer. The census refused the push on the
        count (7 vs 4), which is the loud half. The quiet half is the tempting repair — declare 7 —
        after which the census is green and the tamper also rewrites three separators this law does
        not grade: a proof whose sabotage reaches past its law's subject can go red for a reason
        that is not the law's. [[sabotage-is-usually-the-wrong-one]] [[source-reading-guard]]

        So this DRIVES the real declaration over the real file: every occurrence of each proof's
        `find` in control_ui.html must lie inside an eyebrow span from `_eyebrow_spans` (the same
        bounds the law grades). The declared count is the anchor census's job, not this test's.
        """
        src = io.open(UI, encoding="utf-8").read()
        spans = _eyebrow_spans(src)
        graded = 0
        for i, pr in enumerate(RED_PROOF):
            if os.path.basename(str(pr.get("file") or "")) != os.path.basename(UI):
                continue          # a proof on this law's own file is scoped by its own find
            graded += 1
            find = str(pr.get("find") or "")
            hits = [m.start() for m in re.finditer(re.escape(find), src)]
            outside = [src.count("\n", 0, h) + 1 for h in hits
                       if not any(a <= h < b for a, b in spans)]
            self.assertEqual(
                outside, [],
                "RED_PROOF[%d]'s find %r also matches control_ui.html OUTSIDE every .hh-eye builder, "
                "at line(s) %s. Its tamper would rewrite code this law does not grade, so a red run "
                "is no longer evidence about the eyebrow. Narrow the anchor to the eyebrow's own "
                "form; do not raise `matches` to swallow the new sites." % (i, find, outside))
            # ⚠ NO COUNT ASSERTION HERE (the skeptic on fix24-merge): proof [0]'s tamper DELETES its own find, so a
            # count check would go red under that tamper whatever the eyebrow law does - and heart2 reads any non-zero
            # exit as PROVEN, so the proof would measure its own anchor, not the law. The anchor census already holds
            # every declared `matches` to the real count; this only asks WHERE the hits are.
        # DENOMINATOR — a loop over zero proofs would pass by grading nothing.
        # [[zero-needs-a-denominator]]
        self.assertGreater(graded, 0, "no RED_PROOF targets control_ui.html, so this checked nothing")


RED_PROOF = [
    {
        'why': 'The gate\'s whole reason for existing is that the eyebrow separators must be bound to the word BEFORE them so the browser has no break opportunity there — two independent cold reads reported "· OF 383" alone on a line. The fix as shipped is the six-character JS escape \xa0 immediately before each \'·\' inside the two `<div class="hh-eye">` builders in tv/control_ui.html. This tamper turns that escape into   (a plain space) at all four sites, which is exactly the pre-fix defect: the DOM gets an ordinary space, the break opportunity comes back, and a wrapped line can begin with a bare separator. It deletes the REAL THING — not a comment, not a message string, not a constant shared with the law: the ESCAPES tuple lives in the test file and is untouched, and the sibling law\'s `of\xa0` bindings are untouched, so exactly one law moves. The anchor deliberately omits the leading backslash so it survives JSON escaping literally, and   is still valid JS, so the tamper reproduces the bug rather than breaking the syntax.  MEASURED: untampered OK — Ran 4 tests in 0.038s, 0 failures (test_the_guard_can_actually_see_the_eyebrows, test; tampered (all 4) FAILED (failures=1) — Ran 4 tests; test_no_separator_can_begin_a_wrapped_line raised Asser; reddened law test_eyebrow_never_strands_a_separator.EyebrowNeverStrandsASeparator.t; ALONE FAILS ALONE — fresh process, `python3 -m unittest test_eyebrow_never_strands_a_separator.EyebrowNeverStrandsAS.'
               ' REG-1513 (review of v3524): THE TRAILING SPACE IS THE SCOPE. The eyebrow binds each dot to the word BEFORE it and '
               'leaves an ordinary space after it (escape, dot, space); river-alarm\'s REG-1462 fleet compare footer glues its dots '
               'on BOTH sides (escape, dot, escape). The bare escape-then-dot anchor matched both - 4 on main, 7 after bb31d730 - so '
               'the census refused the push, and declaring 7 would have tampered three separators this law does not grade. With the '
               'space it matches the four eyebrow sites exactly (control_ui.html 23639/23641/23871/23872) and none of the footer\'s; '
               'test_its_red_proof_tampers_the_eyebrows_and_nothing_else pins that every match lies inside an .hh-eye span.',
        'file': 'control_ui.html',
        'find': 'u00a0· ',
        'replace': 'u0020· ',
        'matches': 4,
    },
    {
        'why': 'REG-1513 - the proof above goes back to the bare escape-then-dot anchor that also matched the REG-1462 fleet '
               'footer (7 sites where 4 are the law\'s): its tamper reaches code the eyebrow law does not grade. The find is '
               'written with a \\u00b7 escape so this declaration is not a second occurrence of its own anchor.',
        'file': 'test_eyebrow_never_strands_a_separator.py',
        'find': "'find': 'u00a0\u00b7 ',",
        'replace': "'find': 'u00a0\u00b7',",
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
