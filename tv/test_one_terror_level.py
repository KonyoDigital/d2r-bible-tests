# -*- coding: utf-8 -*-
"""v2716 — THE TERRORIZED MONSTER LEVEL WAS AN UNNAMED LITERAL PRINTED AS IF IT WERE DERIVED.

Konyo, 2026-09-06: *"96 terrorized is a hardcoded literal. sync them to really render the one
unified real calculation obviously :)"* — after a cold cross-family read flagged it TWICE, on two
different versions, with two different zone pairs:

    v2713   density 700 / alvl 82   and   density 880 / alvl 75   -> both "96 terrorized"
    v2714   Rocky Waste 880 / alvl 75  and  Stony Field 520 / alvl 68  -> both "96 terrorized"

Each time the reader was asked an OPEN question with a numbers focus and volunteered it unprompted.
Four earlier cold reads of the same console had been asked about VISUAL defects and all four missed
it — the question found it, not the pixels.

=== ⚠⚠ AND THE FIX IS **NOT** A FORMULA, WHICH IS THE WHOLE POINT ===
MEASURED BEFORE CHANGING ANYTHING:

    bible.html   "mlvl 96 terror"  x10 zones  — 96 is the ONLY value stated anywhere
                 "TC 87 max" x9 · "TC 85 max" x1 (Arcane Sanctuary)
    control_ui   TZ_INFO = 80 zones x [density, alvl, artKey], alvl spanning 67..85

Ten independently researched zones, alvl 67 to 85, ALL state 96. v1801 records why in his own
words: *"a terror zone lifts monster level to the player's own, so that base level is exactly the
thing the boost overrides"*. So it does not vary BY DESIGN, and inventing arithmetic that
reproduced 96 from alvl would be a fabricated calculation wearing a fix's clothes — it would look
unified and break the moment a zone disagreed. [[unknown-stays-unknown]]

What was actually wrong: an UNNAMED literal inside a template string, printed immediately right of
the zone's REAL per-zone alvl, so it read as derived from it. A constant that looks computed lies
about its own provenance even when the value is right. [[label-outlived-referent]]

⚠ NAMED, NOT FIXED: the figure that genuinely varies is the treasure-class ceiling (87, and 85 for
Arcane). TZ_INFO carries no TC at all, so the one per-zone number that DOES differ cannot be
rendered. That half needs his zone research and is not closed by this. [[the-unjoined-end]]
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

UI = os.path.join(HERE, "control_ui.html")
BIBLE = os.path.join(ROOT, "bible.html")


def _code_only(s):
    """-> s with comments blanked, so PROSE cannot satisfy or trip a CODE check.

    This file's own docstring quotes `96 terrorized` while forbidding it, and the console carries
    four CSS comments that quote the old markup verbatim. Grading those would make the gate report
    a defect that is only a description of one. [[source-reading-guard]]
    """
    s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    return re.sub(r"(?m)//.*$", " ", s)


class OneTerrorLevel(unittest.TestCase):

    def setUp(self):
        self.code = _code_only(io.open(UI, encoding="utf-8").read())

    def test_the_constant_is_named_exactly_once(self):
        n = len(re.findall(r"var\s+TZ_TERROR_MLVL\s*=", self.code))
        self.assertEqual(n, 1,
                         "TZ_TERROR_MLVL is declared %d times. Two declarations of one game "
                         "constant is the drift this gate exists to stop." % n)

    def test_no_bare_literal_survives_in_code(self):
        """The defect itself: a number printed as though the zone produced it."""
        hits = re.findall(r"\d+\s*terrorized", self.code)
        self.assertEqual(
            [], hits,
            "a bare '<number> terrorized' literal is back in the CODE: %r. It renders beside the "
            "zone's real per-zone alvl, so it reads as derived from it — which is exactly what two "
            "independent cold reads reported as a defect." % hits
        )

    def test_the_render_site_uses_the_constant(self):
        """⚠ A named constant nobody renders is the purest [[the-unjoined-end]]."""
        # ⚠ ANCHOR ON THE LINE THAT EMITS THE TEXT, not on the class name. The first cut used
        # `tzz-terr[^\n]*` and matched the CSS RULE — `.tzz-terr { color: ... }` — which of course
        # contains no constant, so the gate failed on a correct tree and named the wrong element.
        # A selector that matches the styling and the markup equally cannot tell them apart.
        lines = [l for l in self.code.splitlines()
                 if "tzz-terr" in l and "terrorized" in l]
        self.assertTrue(lines, "no line both names .tzz-terr AND emits 'terrorized' — the render "
                               "site is gone or renamed; fix this gate before trusting its verdict")
        self.assertTrue(
            all("TZ_TERROR_MLVL" in l for l in lines),
            "a terror line does not render from the constant: %r"
            % [l.strip()[:130] for l in lines if "TZ_TERROR_MLVL" not in l]
        )

    def test_it_is_still_HIS_number(self):
        """96 is a game constant he researched, not a value this repo may quietly drift."""
        m = re.search(r"var\s+TZ_TERROR_MLVL\s*=\s*(\d+)", self.code)
        self.assertIsNotNone(m, "TZ_TERROR_MLVL has no numeric value")
        self.assertEqual(m.group(1), "96",
                         "the terrorized level changed to %s. bible.html states 'mlvl 96 terror' "
                         "for TEN independently researched zones; if this moves it moves because "
                         "HE said so, not because a scan drifted." % m.group(1))

    def test_the_bible_still_agrees(self):
        """The corroboration this whole finding rests on — measured, not assumed."""
        b = io.open(BIBLE, encoding="utf-8").read()
        vals = set(re.findall(r"mlvl (\d+) terror\b", b))
        self.assertTrue(vals, "bible.html no longer states any 'mlvl N terror' — the evidence that "
                              "96 is a CONSTANT has gone, so this gate can no longer justify it")
        self.assertEqual(
            vals, {"96"},
            "the bible now states MORE THAN ONE terrorized level: %r. That breaks the premise of a "
            "single constant, and this must become per-zone data rather than one number." % sorted(vals)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
