# -*- coding: utf-8 -*-
"""v2711 — HIS RULING ON THE PRINTER PILLS SHIPPED WITH NOTHING WATCHING IT.

A17 #7, his words: *"this is a visual thing? make it symmetric then?"* — and he chose which of two
contradicting acceptance criteria wins: **equal pill widths**, with a taller rail accepted as the
cost. That shipped at v2686 ("his two rulings: contrast lifted to 4.86:1, and the printer pills
made symmetric") as a 2-column grid on `.mini-foc`.

⚠⚠ AND THEN NOTHING PINNED IT. Searched: `.mini-foc` appears three times in test_control.py and
every one is about the `--mini-focus` CLI FLAG, not the CSS. The ruling was implemented and left
unwatched.

That is the [[heartov2]] shape exactly, and heartov2 is the reason this file exists: a defect there
was fixed THREE TIMES and returned each time, because after every fix nothing was looking. The
fixes were not bad. Nobody was watching. A ruling he had to give once should not need giving twice.

=== WHAT THIS PINS, AND WHY IT IS THE LAW AND NOT THE STRING ===
`grid-template-columns: repeat(2, minmax(0, 1fr))` is today's implementation. The LAW is that every
column is the SAME width, so all six pills match whatever the longest label happens to be — and
that label moved this very session: v2709 made a chronicle reel resolve to `chronicle · uniques`,
which is longer than any stash label. A rule sized to content would have silently desynchronised
the pills the moment that label got longer.

So this accepts any equal-fraction column rule and REFUSES the content-sized keywords (`auto`,
`min-content`, `max-content`, `fit-content`), which are exactly the values that make a column as
wide as whatever is in it — the asymmetry he asked to be removed.
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

#: values that size a column to its CONTENT — the asymmetry his ruling removed
CONTENT_SIZED = ("auto", "min-content", "max-content", "fit-content")


def _rule():
    """The `.mini-foc` rule body, bound at BOTH ends.

    A fixed window past the brace reads as absent and would grade a truncated rule —
    [[source-window-shortcut]], which cost this repo four false readings in one day.
    """
    s = io.open(UI, encoding="utf-8").read()
    m = re.search(r"\.mini-foc\s*\{", s)
    if not m:
        raise AssertionError(
            "GUARD CANNOT GRADE: there is no `.mini-foc {` rule in control_ui.html. It was renamed "
            "or removed — fix this test before trusting any verdict it prints."
        )
    end = s.find("}", m.end())
    if end < 0:
        raise AssertionError("GUARD CANNOT GRADE: the `.mini-foc` rule is never closed")
    return s[m.end():end]


class MiniFocPillsAreSymmetric(unittest.TestCase):

    def setUp(self):
        self.rule = _rule()

    def test_it_is_a_grid(self):
        self.assertRegex(
            self.rule, r"display\s*:\s*grid",
            "`.mini-foc` is not a grid, so nothing makes the pills share a width. His ruling was "
            "'make it symmetric then?' and symmetry is what a grid with equal columns provides."
        )

    def test_the_columns_are_declared(self):
        self.assertIn("grid-template-columns", self.rule,
                      "the grid has no explicit columns, so the browser sizes them to content "
                      "and the pills go back to being as wide as their own labels")

    def test_every_column_is_an_EQUAL_FRACTION(self):
        """The law, not the string: equal columns, whatever the longest label turns out to be."""
        m = re.search(r"grid-template-columns\s*:\s*([^;]+)", self.rule)
        self.assertIsNotNone(m, "no grid-template-columns value to read")
        val = m.group(1).strip().lower()
        self.assertIn("fr", val,
                      "the columns are not fraction-sized (%r). Only `fr` units share the row "
                      "equally; anything else lets one column outgrow another." % val)
        for bad in CONTENT_SIZED:
            self.assertNotIn(
                bad, val,
                "the columns use `%s` (%r), which sizes a column to WHATEVER IS IN IT. That is "
                "the asymmetry he asked to be removed — and the longest label is not fixed: "
                "v2709 made a chronicle reel resolve to `chronicle · uniques`, longer than any "
                "stash label. A content-sized column would have desynchronised the pills the "
                "moment that happened." % (bad, val)
            )

    def test_the_pills_are_not_individually_widthed(self):
        """A per-pill width would defeat the grid without touching the grid rule."""
        s = io.open(UI, encoding="utf-8").read()
        m = re.search(r"\.mini-foc\s+\.mf\s*\{", s)
        if not m:
            self.skipTest("no `.mini-foc .mf` rule to check")
        end = s.find("}", m.end())
        body = s[m.end():end]
        # ⚠⚠ PARSE THE VALUE, DO NOT LOOKAHEAD PAST WHITESPACE. The first cut was
        #     assertNotRegex(body, r"\bwidth\s*:\s*(?!100%|auto)")
        # and it failed on the REAL file, which correctly declares `width: 100%`. `\s*` BACKTRACKS
        # to zero-width, so the negative lookahead then inspects " 100%" WITH the leading space,
        # does not see "100%", and the exclusion silently stops excluding. The control run is what
        # caught it — a sabotage suite whose CONTROL goes red is telling you about your guard, not
        # about the code. [[feedback-suspect-the-instrument]]
        # ⚠⚠ STRIP CSS COMMENTS FIRST, OR THIS LAW CHECKS NOTHING. Second fault in the same
        # assertion. The real rule reads `padding: 4px 9px; /* v2686 — fill the cell ... */
        # width: 100%;` — the declaration is preceded by a COMMENT, not by a `;`, so the
        # `(?:^|;)` anchor matched nothing, the loop body never ran, and the test passed having
        # examined ZERO declarations. Sabotaging it to `width: 120px` left it GREEN, which is how
        # it was caught. A loop over an empty match set is the [[zero-needs-a-denominator]] shape
        # in a guard: no failures, because no candidates.
        body = re.sub(r"/\*.*?\*/", ";", body, flags=re.S)
        decls = list(re.finditer(r"(?:^|;)\s*width\s*:\s*([^;]+)", body))
        self.assertTrue(
            decls,
            "no `width` declaration was found on the pill at all. The grid makes the CELLS equal; "
            "`width: 100%` is what makes the PILLS fill them, and v2686's own comment says so: "
            "'fill the cell and centre, otherwise the grid is equal but the PILLS are not'."
        )
        for decl in decls:
            val = decl.group(1).strip().lower()
            self.assertIn(
                val, ("100%", "auto"),
                "a pill sets `width: %s`, which overrides its grid cell and reintroduces the "
                "uneven widths his ruling removed. `100%%` is the CORRECT value here — it makes "
                "the pill fill the equal cell, which is what turns an equal GRID into equal "
                "PILLS." % val
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
