#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2808 — THREE WAYS THE SECOND-EYE LEDGER MISREPORTED ITS OWN LOOKS.

This ledger exists for one reason: so a thin look can never be filed as a thorough one. Measured
tonight, it was failing at that in three independent ways at once, and each hid the next.

1. THE CALLER AND THE LEDGER DISAGREED ABOUT `sent`. `second_eye_run` computes
   `sent = code_was_transmitted(prompt)` — already a measurement — and `record()` re-measured that
   DICT, which carries no code fence, producing {"chars": 0, "fences": 0}. That is BYTE-IDENTICAL
   to what `sent=None` produces, and `sent=None` is defined by the docstring as "NOBODY CHECKED".
   So "the whole diff was transmitted" and "nobody passed the prompt in" became the same row.
   Ledger census: 417 rows, 20 with a sentCode, 9 of them zero — every look taken through the real
   path — and the 11 healthy ones ALL written by the test, which passes a raw fence. The gate was
   green because it exercised a shape production never used.

2. THE UNSENT DETECTOR FIRED ON EVERY DIFF. Its seam patterns let `\\s*` cross a newline, and in a
   unified diff every added line begins with `+`. So an added docstring reads as `+\"\"\"` and a
   docstring above an added line reads as `\"\"\"\\n+import os`. Measured on the v2807 payload: 24
   hits, ALL ordinary Python docstrings beside a diff marker, ZERO genuine seams. A non-empty
   `unsent` RETRACTS the row, and a version cannot ship while the previous one has never been
   looked at — so this would have deadlocked the repo shut. It was invisible only because defect 1
   was reporting zero fences; fixing that fired it immediately.

3. A CLEAN LOOK WAS FILED AS ONE THAT FOUND DEFECTS. `_findings_from` folds an unenumerated answer
   into a single block, so "No defects found." was recorded as findings=[<the whole answer>] with
   verdict="findings" — the ledger reporting the opposite of what the other family concluded.

★ THE ORDER MATTERS AND IS THE LESSON. Defect 1 masked defect 2 completely. A fix that "worked"
would have shipped a repo that could never ship again. [[two-fixes-broke-each-other]]
[[feedback-suspect-the-instrument]] [[feedback-blind-fixture-green-gate]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_ledger as L  # noqa: E402
import second_eye_run as R  # noqa: E402

# ⚠⚠ THE LEDGER PATH IS REDIRECTED BEFORE ANY TEST RUNS, AND THIS IS NOT OPTIONAL.
# `record()` APPENDS. The first run of this file wrote three v0000 rows straight into the real
# `.second_eye.jsonl` — a fixture writing into live evidence, inside the gate written to make that
# evidence trustworthy. Caught by counting the rows afterwards, which is the only reason it did not
# ship. Guard the FIXTURE, not the call site. [[feedback-fixtures-never-touch-live-data]]
import tempfile  # noqa: E402

_TMP = tempfile.mkdtemp(prefix="second_eye_gate.")
L.LEDGER_PATH = os.path.join(_TMP, "ledger.jsonl")
assert not os.path.exists(L.LEDGER_PATH), "the scratch ledger already exists"

# A real unified-diff fence: added lines carry '+', docstrings are ordinary Python.
DIFF_FENCE = (
    "review this\n```diff\n"
    '+"""v2807 - a module docstring on an added line.\n'
    '+"""\n'
    "+import os\n"
    "+\n"
    "+def f():\n"
    '+    """-> [(file, line)] every call in production code."""\n'
    "+    return []\n"
    "```\n"
)

# The defect the detector exists for: a fence holding the EXPRESSION, not the file.
REAL_SEAM = (
    "review this\n```python\n"
    'PROMPT = """header\n""" + open("control_app.py").read() + """footer"""\n'
    "```\n"
)


class TestTheLedgerCannotLieAboutWhatItSaw(unittest.TestCase):

    # ── 1. the contract ──────────────────────────────────────────────────────────────────────
    def test_a_measured_dict_is_not_the_same_as_nobody_checking(self):
        measured = L.code_was_transmitted(DIFF_FENCE)
        self.assertGreater(measured["chars"], 0, "the fixture carries no code")
        row = L.record(version="v0000", model="t", verdict="clean", findings=[],
                       asked="x", answer_head="y", sent=measured)
        self.assertIsNotNone(row.get("sentCode"),
                             "a measured dict recorded as None — indistinguishable from unchecked")
        self.assertEqual(row["sentCode"]["chars"], measured["chars"],
                         "the ledger re-measured the dict instead of trusting it: %r"
                         % (row["sentCode"],))

    def test_raw_text_still_works(self):
        row = L.record(version="v0000", model="t", verdict="clean", findings=[],
                       asked="x", answer_head="y", sent=DIFF_FENCE)
        self.assertGreater(row["sentCode"]["chars"], 0,
                           "passing the prompt TEXT no longer measures it")

    def test_an_unrecognised_type_is_none_not_zero(self):
        row = L.record(version="v0000", model="t", verdict="clean", findings=[],
                       asked="x", answer_head="y", sent=12345)
        self.assertIsNone(row.get("sentCode"),
                          "an unmeasurable value recorded as a number — a zero with no denominator")

    # ── 2. the detector ──────────────────────────────────────────────────────────────────────
    def test_a_unified_diff_is_not_an_unsent_seam(self):
        m = L.code_was_transmitted(DIFF_FENCE)
        self.assertEqual(m["unsent"], [],
                         "a plain diff trips the unsent detector %r — every code review would be "
                         "RETRACTED, and no version could ship while the previous one is retracted"
                         % (m["unsent"],))

    def test_the_genuine_seam_is_still_caught(self):
        m = L.code_was_transmitted(REAL_SEAM)
        self.assertGreaterEqual(len(m["unsent"]), 2,
                                "the real un-evaluated seam is no longer detected — the fix for "
                                "the false positives went too far and disarmed the check")

    # ── 3. the verdict ───────────────────────────────────────────────────────────────────────
    def test_a_declared_clean_answer_is_recorded_clean(self):
        v, f = R._verdict_for("**No defects found.** Reviewed for races and leaks. Nothing real.",
                              ["one folded block"])
        self.assertEqual(v, "clean", "a 'no defects found' answer filed as findings")
        self.assertEqual(f, [], "a clean answer still carries findings")

    def test_a_declaration_can_never_bury_an_enumerated_list(self):
        v, f = R._verdict_for("No defects found.\n1. a race in x\n2. a leak in y\n3. bad state",
                              ["1. a race in x", "2. a leak in y", "3. bad state"])
        self.assertEqual(v, "findings",
                         "a model that says 'no defects' and then lists three was recorded clean "
                         "— that is a hole a real finding falls through")
        self.assertEqual(len(f), 3, "the enumerated findings were dropped")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "restoring the re-measure makes a full diff and an unchecked look identical again",
        "file": "second_eye_ledger.py",
        "find": "    elif isinstance(sent, dict):",
        "replace": "    elif isinstance(sent, dict) and False:",
        "matches": 1,
    },
    {
        "why": "letting the seam pattern cross a newline re-arms the diff false positive",
        "file": "second_eye_ledger.py",
        "find": '    (re.compile(r"\\S[ \\t]*\\+[ \\t]*[\\"\']{3}"), "a +/triple-quote concatenation seam reached the prompt as text"),',
        "replace": '    (re.compile(r"\\+\\s*[\\"\']{3}"), "a +/triple-quote concatenation seam reached the prompt as text"),',
        "matches": 1,
    },
    {
        "why": "without the declaration check a clean look is filed as one that found defects",
        "file": "second_eye_run.py",
        "find": "    if not enumerated and _NO_DEFECT_RX.search(answer or \"\"):",
        "replace": "    if False:",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
