# -*- coding: utf-8 -*-
"""v3394 — THE EYE IS ASKED FOR THE VERDICT FIELD THE PARSER READS.

v3376 built `_stated_verdict` so a DECLARED verdict line would be read first and prose would never
have to be matched. Its own comment says "the review prompt itself contains the line
1. VERDICT: clean / findings". IT DID NOT. `COLD_FRAMING` carried no such instruction, so the
reader had no writer and every answer fell through to the prose path. [[the-unjoined-end]]

MEASURED on the real ledger (906 rows, 659 verdict=findings): 35 rows from v2805 to v3391 are
answers that DECLARE the change clean - "No defects found.", "No concrete defects.", "The change is
correct." - and are filed as FINDINGS. agreement(), the eagle rows and the heart are wrong on every
one. Of the 8 rows that store a full answer, 6 are misfiled and only v3388 is genuine.

⚠⚠ THE PROSE FIX WAS REFUSED BY THIS FILE'S OWN RULING. A first-sentence matcher moved exactly
those 35 with 0 real findings eaten - but #76 measured that widening the prose matcher CANNOT BE
MADE SAFE, and second_eye_run.py says in as many words that prose is never consulted there. Asking
for the field is the fix the design already chose; a second mechanism would have overridden a
measured refusal by measuring something else.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ unittest -v prints the first docstring line and these carry a warning sign; on a cp1255 console
# that crashes WHILE REPORTING.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_run as SE  # noqa: E402

SRC = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8").read()


class TheEyeIsAskedForTheVerdictItIsReadFor(unittest.TestCase):

    def test_the_prompt_ASKS_for_the_field_the_parser_reads(self):
        """A reader with no writer is the defect this version exists to close."""
        self.assertIn("VERDICT:", SE.COLD_FRAMING,
                      "the prompt does not ask for a VERDICT line, so _stated_verdict can never "
                      "fire and every answer falls through to the prose path it was built to avoid")

    def test_the_instruction_is_not_itself_a_MENU(self):
        """⚠ _stated_verdict ignores any line naming 2+ verdict words, as a menu.

        An instruction written "VERDICT: clean / findings" would be ignored when echoed - the guard
        would eat the very field we just asked for.
        """
        for line in SE.COLD_FRAMING.splitlines():
            if "VERDICT:" not in line:
                continue
            words = [w.group(1).lower()
                     for w in SE._VERDICT_WORD_RX.finditer(line.split("VERDICT:", 1)[1])]
            self.assertLessEqual(
                len(set(words)), 1,
                "the instruction line names %d verdict words, so an eye echoing it is read as a "
                "MENU and ignored: %r" % (len(set(words)), line[:90]))

    def test_a_declared_verdict_is_read(self):
        self.assertEqual(SE._stated_verdict("looks fine\nVERDICT: clean"), "clean")
        self.assertEqual(SE._stated_verdict("1. a bug\nVERDICT: findings"), "findings")
        self.assertEqual(SE._stated_verdict("VERDICT: cannot-tell"), "cannot-tell")

    def test_a_menu_line_is_still_ignored(self):
        """⚠ THE BASELINE. If the guard stopped firing, an echoed instruction would read as a
        declaration and every look would come back clean."""
        self.assertIsNone(SE._stated_verdict("VERDICT: clean / findings"))
        self.assertIsNone(SE._stated_verdict("1. VERDICT: clean / findings / cannot-tell"))

    def test_an_undeclared_answer_still_falls_through_unchanged(self):
        """None means NOBODY DECLARED, which is not the same as declaring clean."""
        self.assertIsNone(SE._stated_verdict("The change is correct."))

    def test_a_declared_CLEAN_cannot_clear_a_real_claim(self):
        """v3376's rule survives: a declaration alone never clears a defect that is claimed."""
        self.assertIn("_claims_a_defect", SRC)
        i = SRC.find('if stated == "clean":')
        self.assertGreater(i, 0, "the stated-clean branch is gone")
        blk = SRC[i:i + 400]
        self.assertIn("_claims_a_defect", blk,
                      "a stated clean verdict no longer consults the defect claim, so an eye that "
                      "declares clean while listing a P1 would be filed clean")


RED_PROOF = [
    {
        "why": "without the instruction the parser's reader has no writer, and every clean answer "
               "falls through to the prose path - the 35 misfiled rows from v2805 to v3391",
        "file": "tv/second_eye_run.py",
        "find": '    "Then end your answer with a line naming only that one word, like  VERDICT: <your "',
        "replace": '    "Then end your answer with a plain summary. "  # noqa',
        "matches": 1,
    },
    {
        "why": "an instruction that lists the options is a MENU, and _stated_verdict ignores menus - "
               "so asking that way silently fails to produce the field",
        "file": "tv/second_eye_run.py",
        "find": '    "choice>  and put nothing else on that line.\\n"',
        "replace": '    "choice>  VERDICT: clean / findings / cannot-tell.\\n"',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
