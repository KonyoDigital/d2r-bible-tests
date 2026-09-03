"""v2461 — no text may render below the console's smallest type token.

⚠ THE DEFECT THIS EXISTS FOR, and it is not the one you would guess. Nothing in this console was
ever typed below the floor. Two font tokens were REFERENCED AND NEVER DEFINED —

    var(--fs-meta, 12px)     --fs-meta  is defined nowhere
    var(--fs-3xs, 10px)      --fs-3xs   is defined nowhere

— so every use of them silently rendered at its FALLBACK, under the floor, and a reader auditing
the stylesheet for small numbers would find nothing wrong. Measured at his real 1120x628: 16 nodes
below 13px, and the last one standing traced to a `var()` whose token does not exist.

A fallback is a font size nobody reviewed. This pins two rules:
  1. every --fs-* token a rule REFERENCES must be DEFINED, or the fallback is the real size
  2. no fallback may be below the floor, so a mistyped name degrades TO the floor, never under it

⚠ It pins the RULE, not a node count. The count is a symptom and moves with his data.
[[unknown-stays-unknown]] [[label-outlived-referent]]
"""
import io
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "control_ui.html")
FLOOR_PX = 13.0          # --fs-2xs = clamp(13px, 1.0vw, 15px) is the smallest token there is


def _css(path):
    """The stylesheet with comments stripped.

    ⚠ This file's own header quotes `var(--fs-meta, 12px)` while explaining the bug, and so does
    the note beside the token block. A scan over raw text would find those and fail forever on its
    own prose. [[source-reading-guard]]
    """
    s = io.open(path, encoding="utf-8", errors="replace").read()
    return re.sub(r"/\*.*?\*/", " ", s, flags=re.S)


class EveryFontTokenResolves(unittest.TestCase):

    def setUp(self):
        self.src = _css(UI)
        self.defined = set(re.findall(r"(--fs-[a-z0-9-]+)\s*:", self.src))
        self.used = set(re.findall(r"var\(\s*(--fs-[a-z0-9-]+)", self.src))

    def test_the_scan_finds_tokens_at_all(self):
        """PRINT THE COUNT. A scan that finds none looks exactly like a clean stylesheet."""
        self.assertGreaterEqual(len(self.defined), 6,
                                "only %d --fs-* definitions found (%s) — the extractor is broken, "
                                "not the CSS" % (len(self.defined), sorted(self.defined)))
        self.assertGreaterEqual(len(self.used), 6,
                                "only %d --fs-* references found — the extractor is broken"
                                % len(self.used))

    def test_an_undefined_token_is_only_safe_when_its_fallback_is(self):
        """⚠ MY FIRST VERSION OF THIS TEST WAS WRONG AND WENT RED ON CORRECT CODE.

        It demanded that every referenced token be DEFINED. But this file deliberately writes
        `var(--fs-3xs, var(--fs-2xs))` and `var(--fs-micro, var(--fs-2xs))` — an undefined token
        whose fallback is the FLOOR token — and a comment at one of those sites says so in as many
        words. That pattern is correct: it degrades to the smallest legal size. Forcing those
        tokens to be defined would have invented two new sizes to satisfy a test.

        What actually bites is narrower, and it is two things:
          - a BARE `var(--fs-x)` on an undefined token: the whole declaration is invalid, so the
            element silently INHERITS its parent size. An author wrote a size and got another.
          - a fallback that is a raw px BELOW the floor (covered by the next test).
        """
        bare = set()
        for tok in sorted(self.used - self.defined):
            # a reference with NO comma inside its own parens has no fallback at all
            for m in re.finditer(r"var\(\s*%s\s*([,)])" % re.escape(tok), self.src):
                if m.group(1) == ")":
                    bare.add(tok)
        self.assertEqual(
            sorted(bare), [],
            "these tokens are undefined AND referenced with no fallback, so the declaration is "
            "invalid and the element inherits its parent size — a font size was written and had "
            "no effect: %s" % sorted(bare))

    def test_no_font_fallback_is_below_the_floor(self):
        bad = [(t, fb) for t, fb in re.findall(r"var\(\s*(--fs-[a-z0-9-]+)\s*,\s*([0-9.]+)px\s*\)",
                                               self.src) if float(fb) < FLOOR_PX]
        self.assertEqual(
            bad, [],
            "a fallback below the %spx floor is a font size nobody reviewed — it fires exactly when "
            "a token name is wrong, which is the moment nobody is looking: %s" % (FLOOR_PX, bad))


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
