# -*- coding: utf-8 -*-
"""v3392 — THE CROSS-REFERENCE PANEL ASKS THE SAME THREE QUESTIONS FOR EVERY USER.

HIS RULING, 2026-09-20, from his Windows ALT console:
    "the first column is what DEAN NEEDs.. any for every user same unified logic... and the second
     is what they have that i dont.. so i need compared to the user related. and the third is what
     we both need combined... what user sti has that I DONT HAVE and the second row is what i have
     that they dont. and the third is what we both need.. hardcode that join it and fix it like it
     already was... something changed last coupleships when we tocuheed it."

WHAT CHANGED, AND WHEN. v3176 ("A PANEL OF DIFFERENCES MUST NOT LIST THE WHOLE LEDGER") replaced
column 1 with `you still need` whenever the peer cannot publish names, and v3178 kept it. Its
reasoning was honest - "what he can ACT on is what he still needs" - but the effect is that ONE
COLUMN HEADER ANSWERS TWO DIFFERENT QUESTIONS depending on a condition he cannot see from the
screen. He photographed it reading YOU STILL NEED 86 and said it "cant be logical".

THE LAW: the three labels are INVARIANT across both arms of the ok/not-ok ternary. A column whose
names are unknown is REFUSED - col() renders names===null as an em-dash plus its reason - and is
NEVER swapped for an easier question.

⚠ THIS GRADES CODE, NOT PROSE. Every assertion anchors on `col('<label>'` - a call - rather than on
the label text, which necessarily appears in this docstring and in the panel's own comments.
[[source-reading-guard]] section 4b
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ THIS FILE PRINTS THE COLUMN LABELS, AND THEY CONTAIN A MIDDLE DOT. On a cp1255 console
# that crashes WHILE REPORTING, so a clean tree would exit non-zero for a reason unrelated
# to the check — and his Windows box is exactly such a console. The pre-push gate refused
# this file for precisely that, which is the gate doing its job.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()

# The three questions, in his order. These strings are the LAW.
LABELS = ("they have · you do not", "you have · they do not", "you both need")


def _code_only(src):
    """Block and line comments removed, line count preserved.

    ⚠ THE BLOCK FORM IS BOUNDED. An unbounded /\\*.*?\\*/ with DOTALL over this mixed HTML/CSS/JS
    file removes 16.9% of it and 170 of its 444 id= declarations, because a `/*` inside a string
    or a regex matches forward to the next `*/` anywhere in the file - and a stripper that eats a
    third of the file can only produce false NEGATIVES. [[source-reading-guard]]
    """
    def _blank(m):
        return "\n" * m.group(0).count("\n")
    out = re.sub(r"/\*.{0,4000}?\*/", _blank, src, flags=re.S)
    return "\n".join(l.split("//", 1)[0] if l.strip().startswith("//") else l
                     for l in out.split("\n"))


CODE = _code_only(UI)


class TheCompareColumnsAskOneQuestion(unittest.TestCase):

    def test_every_column_label_appears_in_BOTH_arms(self):
        """The ok arm and the refused arm must ask the SAME three questions."""
        for lab in LABELS:
            n = CODE.count("col('" + lab + "'")
            self.assertGreaterEqual(
                n, 2,
                "the column %r is drawn %d time(s) - it must appear in BOTH the ok arm and the "
                "refused arm, or the panel means different things in different states" % (lab, n))

    def test_the_refused_arm_substitutes_no_other_question(self):
        """v3176's `you still need` is his own gap list, not a comparison. It must not return."""
        self.assertNotIn(
            "col('you still need'", CODE,
            "column 1 was replaced by a DIFFERENT QUESTION (his own missing list) when the peer "
            "cannot publish names - that is the v3176 regression he reported")

    def test_a_column_with_unknown_names_is_REFUSED_not_filled(self):
        """names===null reaches col() and renders an em-dash with its reason."""
        i = CODE.find("+ (!j.ok")
        self.assertGreater(i, 0, "the ok/not-ok ternary is gone - this law cannot reach its subject")
        arm = CODE[i:CODE.find("+ (j.ok ?", i)]
        self.assertGreater(len(arm), 40, "the refused arm could not be bounded")
        for lab in LABELS:
            self.assertIn(
                "col('" + lab + "', null", arm,
                "in the refused arm %r must pass null (refuse with a reason), never a list" % lab)

    def test_the_three_questions_are_his_words(self):
        """A label is a claim. These are the three he dictated; renaming one is a ruling."""
        for lab in LABELS:
            self.assertIn("col('" + lab + "'", CODE, "the panel no longer asks %r" % lab)

    def test_neitherHas_still_passes_without_a_coalesce(self):
        """⚠ v3022 - `j.neitherHas` must NOT get `|| []`.

        The server answers null when the roster is not known to be the whole universe, and `|| []`
        would turn that refusal into a confident "0 items you both need". [[unknown-stays-unknown]]
        """
        self.assertIn("col('you both need', j.neitherHas,", CODE,
                      "neitherHas gained a coalesce - a refusal would render as a confident zero")


RED_PROOF = [
    {
        "why": "restoring v3176's substitution makes column 1 answer a different question than it "
               "does in the ok arm - the exact regression he photographed",
        "file": "tv/control_ui.html",
        "find": "          ? (col('they have · you do not', null, 'no names published', 'theirs')",
        "replace": "          ? (col('you still need', j.mineMissingNames || [], 'x', 'need-only')",
        "matches": 1,
    },
    {
        "why": "a refused column that is handed a list instead of null stops being a refusal and "
               "renders a confident answer the peer never published",
        "file": "tv/control_ui.html",
        "find": "             + col('you both need', null, 'no names published', 'neither'))",
        "replace": "             + col('you both need', [], 'no names published', 'neither'))",
        "matches": 1,
    },
    {
        "why": "v3022 - coalescing neitherHas turns the server's refusal into a confident zero",
        "file": "tv/control_ui.html",
        "find": "col('you both need', j.neitherHas,",
        "replace": "col('you both need', j.neitherHas || [],",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
