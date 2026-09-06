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


def _eyebrow_literals():
    """Every JS string literal that builds an `.hh-eye` line, bound at BOTH ends.

    ⚠ Anchored on the opening `<div class="hh-eye"` and closed at the `</div>` that ends it, so
    this never reads a fixed window past the region — [[source-reading-guard]], which cost this
    repo four false readings in one day. A concatenation is followed across `+` joins because the
    eyebrow is assembled from three or four pieces and the separator lives in the middle piece.
    """
    src = io.open(UI, encoding="utf-8").read()
    out = []
    for m in re.finditer(r'<div class="hh-eye">', src):
        end = src.find("</div>", m.end())
        if end < 0:
            raise AssertionError("GUARD CANNOT GRADE: an .hh-eye div is never closed at char %d"
                                 % m.start())
        out.append(src[m.start():end])
    return out


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
