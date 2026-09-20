#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3386 (#129) — THE ROW KEPT THE VERDICT AND THREW AWAY THE EVIDENCE.

MEASURED on the live ledger before this version: 898 rows, 876 with an answer, median head 400
chars, max 600 — the cap. `answerHead` is a PREFIX and the text past it was stored NOWHERE.

⚠⚠ THAT MAKES A RE-JUDGE IMPOSSIBLE BY CONSTRUCTION, NOT BY ACCIDENT. Every proposed change to
the findings parser — and there have been five, three of them refused after measurement (#76,
#117, #127) — could only ever be argued about, never validated against what the eyes actually
said. The store could not answer the one question the next stage needed to ask.

⚠ AND THE ANSWER WAS ALREADY IN HAND. v3339 moved the truncation out of the runner into
`record()`, so the caller passes the COMPLETE text and this function was discarding it. Nothing
new had to be fetched; what was missing was keeping it. [[heart-first]] section 6 — persist what
you knew, not a summary of it.

⚠ THE STORE IS GITIGNORED AND LOCAL (2.7 MB over 898 rows), so keeping the evidence costs a few
megabytes. Losing it cost every re-judge, permanently.

WHAT THIS FILE PINS:
  * a long answer is stored WHOLE, tail and all
  * `answerChars` is the TRUE length, so neither stored field can claim to be complete when it is not
  * `answerHead` still behaves exactly as before — this adds evidence, it does not move the cap
  * a row written BEFORE this version reads as UNKNOWN, never as "the head was everything"
  * a row whose full text was itself cut reports complete=False rather than passing as whole
"""

import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    import console_safe
    console_safe.enable()
except Exception:
    pass

import second_eye_ledger as L


class ALookKeepsItsEvidence(unittest.TestCase):

    def setUp(self):
        self._real = L.LEDGER_PATH
        self._tmp = tempfile.mkdtemp()
        L.LEDGER_PATH = os.path.join(self._tmp, "ledger.jsonl")

    def tearDown(self):
        L.LEDGER_PATH = self._real

    def _write(self, answer, head_cap=400):
        return L.record("v9999", "grok-test", "clean", answer_head=answer,
                        head_cap=head_cap, sha="deadbeef")

    # ---------- the evidence survives ----------

    def test_a_long_answer_is_stored_whole(self):
        """THE WHOLE POINT — the tail past the head cap used to be lost for ever."""
        tail = " ...and the tail that used to be lost."
        answer = ("A" * 5000) + tail
        row = self._write(answer)
        self.assertEqual(row.get("answerFull"), answer,
                         "the full answer is not stored, so no parser change can ever be "
                         "validated against what the eye actually said")
        self.assertTrue(str(row.get("answerFull") or "").endswith(tail),
                        "the tail was cut — storing a longer prefix is not storing the answer")

    def test_answerChars_is_the_true_length(self):
        answer = "B" * 7321
        row = self._write(answer)
        self.assertEqual(row.get("answerChars"), 7321,
                         "answerChars is not the true length, so a cut row could read as whole")

    def test_the_head_still_behaves_exactly_as_before(self):
        """NO REGRESSION. This version adds evidence; it must not move the cap or the head."""
        answer = "C" * 5000
        row = self._write(answer, head_cap=400)
        self.assertEqual(len(row.get("answerHead") or ""), 400)
        self.assertEqual(row.get("headCap"), 400)
        row600 = self._write(answer, head_cap=600)
        self.assertEqual(len(row600.get("answerHead") or ""), 600)
        self.assertEqual(row600.get("headCap"), 600)

    def test_a_short_answer_is_not_padded_or_marked_cut(self):
        answer = "No defects found."
        row = self._write(answer)
        self.assertEqual(row.get("answerFull"), answer)
        self.assertEqual(row.get("answerChars"), len(answer))
        txt, complete = L.answer_for_rejudge(row)
        self.assertTrue(complete, "a short answer that fit is being reported as cut")

    # ---------- the reader refuses to guess ----------

    def test_a_row_written_before_this_version_is_UNKNOWN(self):
        """⚠ ALL 898 EXISTING ROWS ARE THIS CASE. Handing back `answerHead` here would let a
        re-judge read a 400-character prefix and report a verdict as if it had read the answer."""
        old = {"answerHead": "prefix only, the rest was never stored", "headCap": 600,
               "verdict": "findings", "version": "v2807"}
        txt, complete = L.answer_for_rejudge(old)
        self.assertIsNone(txt, "a pre-v3386 row handed back text it does not have")
        self.assertFalse(complete)

    def test_a_full_field_that_was_itself_cut_is_not_called_whole(self):
        """zero-needs-a-denominator: a cut that is not declared is a cut that lies."""
        row = {"answerFull": "D" * 100, "answerChars": 250}
        txt, complete = L.answer_for_rejudge(row)
        self.assertEqual(txt, "D" * 100, "usable text must still be handed back")
        self.assertFalse(complete,
                         "answerFull is shorter than answerChars, so it was cut and must not "
                         "report as the whole answer")

    def test_a_missing_answerChars_is_not_complete(self):
        row = {"answerFull": "E" * 40}
        self.assertEqual(L.answer_for_rejudge(row), ("E" * 40, False),
                         "a row with no true length is UNKNOWN about completeness, not complete")

    def test_garbage_in_is_UNKNOWN_not_a_crash(self):
        for bad in (None, "", 7, [], {"answerFull": None}, {"answerFull": ""}):
            self.assertEqual(L.answer_for_rejudge(bad), (None, False),
                             "%r was not treated as UNKNOWN" % (bad,))

    # ---------- the round trip ----------

    def test_the_row_survives_json_and_is_still_re_judgeable(self):
        """A field that does not survive the file is a field nobody has."""
        answer = ("F" * 3000) + " END"
        self._write(answer)
        rows = [json.loads(l) for l in io.open(L.LEDGER_PATH, encoding="utf-8") if l.strip()]
        self.assertTrue(rows, "nothing was written to the ledger at all")
        txt, complete = L.answer_for_rejudge(rows[-1])
        self.assertEqual(txt, answer, "the answer did not survive the round trip to disk")
        self.assertTrue(complete)


RED_PROOF = [
    {
        "why": "storing the head again instead of the full text is the exact defect: the tail is "
               "lost and a re-judge is impossible by construction",
        "file": "second_eye_ledger.py",
        "find": '        "answerFull": (_raw[:FULL_ANSWER_CAP]) or None,',
        "replace": '        "answerFull": (_raw[:_cap]) or None,',
        "matches": 1,
    },
    {
        "why": "an answerChars measured on the CUT text makes a truncated row read as whole, "
               "which is the confident-zero this field exists to prevent",
        "file": "second_eye_ledger.py",
        "find": '        "answerChars": len(_raw),',
        "replace": '        "answerChars": len(_raw[:_cap]),',
        "matches": 1,
    },
    {
        "why": "handing back answerHead for a pre-v3386 row lets a re-judge read a 400-character "
               "prefix and report a verdict as though it had read the answer",
        "file": "second_eye_ledger.py",
        "find": "    full = row.get(\"answerFull\")\n    if not isinstance(full, str) or not full:\n        return None, False",
        "replace": "    full = row.get(\"answerFull\")\n    if not isinstance(full, str) or not full:\n        return row.get(\"answerHead\"), True",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
