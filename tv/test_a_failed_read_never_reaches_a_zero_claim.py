# -*- coding: utf-8 -*-
"""v3395 — A FAILED READ MUST NEVER REACH A SENTENCE THAT CLAIMS A MEASURED ZERO.

FOUND BY THE WIN-1 SEAT ON HIS WINDOWS BOX, 2026-09-20. It ran the queue drain as intended. The
reader thread died with UnicodeDecodeError ('charmap' codec, byte 0x9f - that console is cp1255),
and the tool then printed:

    0 new since ... nothing new. That is a measured zero, not a failure to look.

IT WAS EXACTLY A FAILURE TO LOOK, and the sentence ASSERTING otherwise is what makes this worse
than silence: a reassurance on the failure path disarms the suspicion that would have caught it.

TWO DEFECTS, and the second is the one that matters:
  · PROXIMATE - `subprocess.run(..., text=True)` decodes with the LOCALE CODE PAGE. The same file
    passes encoding="utf-8" correctly at three OTHER sites; the one call that talks to GitHub did
    not. [[copy-drift]]
  · CLASS - with capture_output, a dead reader thread hands back EMPTY stdout and returncode 0. The
    code then hit `if not body: return []` and produced a CONFIDENT EMPTY LIST. Fixing only the
    decode would leave every other reader failure landing in the same place.

⚠ THE DISTINCTION THAT MAKES THE CLASS FIX POSSIBLE: `gh api` prints `[]` for a query that matches
nothing. So an empty stdout from a SUCCESSFUL call is never "no rows" - it means the read failed.
[[zero-needs-a-denominator]] [[unknown-stays-unknown]] [[a-wrong-answer-skips-the-fallback]]

⚠ THIS FILE GRADES CODE, NOT PROSE. The comment explaining the fix necessarily contains the banned
string, and a raw count of it in this repo returns 1 while the code-only count returns 0. A guard
that reads its own explanation is the defect source-reading-guard exists to prevent.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ unittest -v prints the first docstring line and these carry a warning sign; cp1255 would crash.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

RAW = io.open(os.path.join(HERE, "handoff.py"), encoding="utf-8").read()
CODE = "\n".join(l.split("#", 1)[0] for l in RAW.split("\n"))


class AFailedReadNeverReachesAZeroClaim(unittest.TestCase):

    def test_the_github_read_decodes_as_utf8_not_the_locale(self):
        """The one call that talks to GitHub must not decode with the code page."""
        self.assertEqual(
            0, CODE.count("text=True"),
            "a subprocess read still decodes with the locale code page, so one non-ASCII byte "
            "kills the reader on a cp1255 console")
        self.assertIn('encoding="utf-8"', CODE)

    def test_the_decode_cannot_die_on_one_bad_byte(self):
        """errors='replace' - a single odd byte must not cost the whole read."""
        i = CODE.find("subprocess.run(cmd")
        self.assertGreater(i, 0, "the gh call is gone - this law cannot reach its subject")
        call = CODE[i:CODE.find(")", i) + 1]
        self.assertIn('errors="replace"', call,
                      "the decode has no replacement policy, so a bad byte still raises: %r" % call)

    def test_an_empty_stdout_from_a_SUCCESSFUL_read_raises(self):
        """gh prints [] for an empty result, so silence means the read failed."""
        self.assertNotIn("if not body:\n        return []", CODE,
                         "an empty stdout is still handed back as an empty result set")
        i = CODE.find("if not body:")
        self.assertGreater(i, 0)
        blk = CODE[i:i + 700]
        self.assertIn("raise RuntimeError", blk,
                      "a read that printed nothing no longer refuses - it returns a confident zero")

    def test_a_WRITE_may_still_legitimately_print_nothing(self):
        """⚠ THE BASELINE. If every empty raised, a POST/PATCH would break and the law would be
        measuring nothing but its own strictness. [[strictness-that-closes-the-lane]]"""
        i = CODE.find("if not body:")
        blk = CODE[i:i + 700]
        self.assertIn("if method:", blk,
                      "a write with an empty body now raises, which closes a lane that was working")

    def test_the_measured_zero_sentence_still_exists_and_is_now_TRUE(self):
        """The sentence is not the defect - being reachable on the failure path was."""
        self.assertIn("That is a measured zero, not a failure to look.", RAW,
                      "the claim was deleted rather than made honest; a drain that says nothing at "
                      "all is not an improvement on one that said something wrong")


RED_PROOF = [
    {
        "why": "restoring the locale decode is the original defect: on a cp1255 console one "
               "non-ASCII byte kills the reader and the drain reports a clean zero",
        "file": "tv/handoff.py",
        # v3463 — RE-ANCHORED: v3462 added `timeout=timeout` on a continuation line (the
        # unbounded-gh fix), and the one-line anchor then matched ZERO times. The tamper still
        # restores the locale decode and keeps the timeout, so it breaks the property it names.
        "find": '    p = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace",\n'
                '                       timeout=timeout)',
        "replace": '    p = subprocess.run(cmd, capture_output=True, text=True,\n'
                   '                       timeout=timeout)',
        "matches": 1,
    },
    {
        "why": "handing an empty stdout back as [] lets ANY reader failure - not just a decode - "
               "reach the sentence that asserts it is not a failure to look",
        "file": "tv/handoff.py",
        "find": '        raise RuntimeError(\n            "gh exited 0 but printed nothing for %s',
        "replace": '        return []  # noqa\n        _dead = (\n            "gh exited 0 but printed nothing for %s',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
