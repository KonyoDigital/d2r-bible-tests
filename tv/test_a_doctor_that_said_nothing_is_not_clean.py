# -*- coding: utf-8 -*-
"""#86 gap audit 24 (REG-1726) — A DOCTOR THAT SAID NOTHING IS NOT A CLEAN REPORT.

The console doctor's "the other doctors" row runs vault_doctor and chronicle_doctor and counts their marks. The count
WAS the verdict: a sub-doctor that crashed - a traceback, exit 1, no marks - read "vault 0 green / 0 needs-you" and the
row was OK. Found by the 09-29 gap audit, driven then; still open on 10-02.

  · DRIVEN: a sub-doctor that prints a traceback and exits 1 -> UNKNOWN, saying it gave no verdict and its exit code.
  · DRIVEN: one that exits 0 with no marks -> UNKNOWN too (zero needs a denominator).
  · DRIVEN: a real report (green and needs-you marks) still reads as it did - OK when all green, MISSING when not.
Nothing here starts a process: the run is a seam. RED_PROOF below. [[unknown-stays-unknown]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import console_doctor as CD  # noqa: E402


class _R(object):
    def __init__(self, out, rc):
        self.stdout, self.stderr, self.returncode = out, "", rc


def _runner(out, rc):
    seen = []

    def run(argv, **kw):
        seen.append(os.path.basename(argv[-1]))
        return _R(out, rc)
    return run, seen


class ADoctorThatSaidNothing(unittest.TestCase):

    def test_a_crashed_doctor_is_unknown_and_says_so(self):
        run, seen = _runner("Traceback (most recent call last):\n  ...\nImportError: boom\n", 1)
        state, line = CD._check_the_other_doctors(_run=run)
        self.assertEqual(seen, ["vault_doctor.py", "chronicle_doctor.py"], "PREMISE: both doctors were not asked")
        self.assertEqual(state, CD.UNKNOWN, "a doctor that crashed was read as a clean report: %r" % line)
        self.assertIn("gave no verdict", line)
        self.assertIn("exited 1", line)

    def test_a_silent_exit_zero_is_unknown_too(self):
        run, _ = _runner("", 0)
        state, line = CD._check_the_other_doctors(_run=run)
        self.assertEqual(state, CD.UNKNOWN, line)

    def test_a_real_report_still_reads_as_before(self):
        run, _ = _runner("🟢 a\n🟢 b\n", 0)
        state, line = CD._check_the_other_doctors(_run=run)
        self.assertEqual(state, CD.OK, line)
        self.assertIn("vault 2 green / 0 needs-you", line)
        run, _ = _runner("🟢 a\n🔴 b\n", 1)
        state, line = CD._check_the_other_doctors(_run=run)
        self.assertEqual(state, CD.MISSING, line)


RED_PROOF = [
    {"why": "REG-1726 - a doctor with no marks is counted again: a crashed sub-doctor reads 0 green / 0 needs-you, OK",
     "file": "console_doctor.py",
     "find": "            if not (good or bad):\n",
     "replace": "            if False:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
