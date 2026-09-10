"""CSS `content:` PAINTS TEXT THE RENDER HARNESS CANNOT READ, SO ITS ESCAPES MUST BE CSS ESCAPES.

⚠⚠ MEASURED 2026-09-10 (v2894, #58). A separator was added to the river strip as
`content: " \\u00b7"` — the JAVASCRIPT escape. CSS reads `\\u` as an escaped letter `u` followed by
the literal characters `00b7`, and `text-transform: uppercase` then served him:

    7 CLOSED OUT U00B7 23 LIFETIMES

⚠ AND THE RENDER HARNESS CALLED THAT TARGET GREEN — twice, at five widths. Generated content is not
in `textContent`, so `render_check`'s extracted text read "7 closed out 23 lifetimes", perfectly
correct, while the pixels carried a stray token. Every automatic check agreed with the code and
disagreed with the screen; only LOOKING at the image found it. That is precisely the shape
[[feedback-blind-fixture-green-gate]] names — an instrument that cannot see the thing it is trusted
to watch — so the check belongs in the SOURCE, where it is decidable, rather than in a harness that
is structurally blind to it. [[visual-regression-detector]] [[unknown-stays-unknown]]

⚠ THE VALID CSS FORMS ARE `\\00b7` / `\\2014` (hex, no `u`) or the literal character itself. Anything
matching `\\u` inside a `content:` value is the JS habit leaking into a stylesheet, and it is silent:
no parse error, no console warning, just the wrong glyphs on his screen.
"""
import io
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))

#: Every file in tv/ that carries a stylesheet the console actually paints from.
STYLED = ("control_ui.html",)

#: A `content:` declaration and its value, up to the terminating `;` or `}`.
_CONTENT = re.compile(r"\bcontent\s*:\s*([^;}]*)")

#: The JS escape, which CSS does not have. `\\u` in a css value is always this mistake.
_JS_ESCAPE = re.compile(r"\\u[0-9a-fA-F]{4}")


def _strip_comments(css):
    """/* … */ removed, so a comment DESCRIBING the mistake is not read as making it.

    ⚠ This law was written the same day a comment satisfied its own guard — the fourth time in
    this repo a check has read prose as code. The comment above `.shr-life::after` quotes the bad
    escape on purpose, so a version of this law that did not strip comments would fail forever on
    its own documentation. [[source-reading-guard]] [[feedback-comments-vs-code]]
    """
    return re.sub(r"/\*.*?\*/", " ", css, flags=re.S)


class CssGeneratedTextIsNotAJsEscape(unittest.TestCase):

    def test_no_content_value_carries_a_javascript_escape(self):
        checked, decls = 0, 0
        for name in STYLED:
            p = os.path.join(HERE, name)
            if not os.path.exists(p):
                continue
            checked += 1
            with io.open(p, encoding="utf-8") as fh:
                src = _strip_comments(fh.read())
            for m in _CONTENT.finditer(src):
                decls += 1
                val = m.group(1)
                bad = _JS_ESCAPE.findall(val)
                if bad:
                    line = src[:m.start()].count("\n") + 1
                    self.fail(
                        "%s:%d — `content: %s` carries the JAVASCRIPT escape %s. CSS paints that "
                        "as the literal text 'u%s', and no harness can see it: generated content "
                        "is not in textContent. Use the CSS form (\\%s) or the character itself."
                        % (name, line, val.strip()[:60], bad[0], bad[0][2:], bad[0][2:]))
        # ⚠ A ZERO NEEDS A DENOMINATOR. "no bad escapes" over zero files read is not a pass — it is
        # a law that measured nothing, which is how a guard quietly stops guarding.
        self.assertTrue(checked, "no styled file was read, so this law measured NOTHING")
        self.assertGreater(decls, 10,
                           "only %d `content:` declaration(s) found across %d file(s) — the "
                           "scanner stopped matching the stylesheet it is pointed at, so a green "
                           "here says nothing about the CSS" % (decls, checked))


RED_PROOF = [
    {
        "why": "putting the JS escape back into a real `content:` value must turn this red — it is "
               "the exact byte sequence that painted 'U00B7' on his river strip",
        "file": "control_ui.html",
        "find": '#th-shelfov .shr-life:not(:last-child)::after { content: " ·"; opacity: .45; }',
        "replace": '#th-shelfov .shr-life:not(:last-child)::after { content: " \\u00b7"; opacity: .45; }',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
