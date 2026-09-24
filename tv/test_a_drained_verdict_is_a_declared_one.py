# -*- coding: utf-8 -*-
"""REG-1267 (#222) — A VERDICT DRAINED FROM A #231 FIELD IS A DECLARED VERDICT.

MEASURED on his console 2026-09-25: the row 'a verdict comes from a declared field' said "6 of the 6 most
recent look(s) carry NO declared verdict" - all six drained from #231, whose look format carries a required
`verdict:` line that second_eye_drain reads as a field. The check re-parsed the stored answer (the findings
paragraph only) for a VERDICT line, which could never be there. It had no law at all.

  · DRIVEN over a temp ledger: six drained rows (verdictFrom "gh#231 comment <id>") -> OK.
  · DRIVEN: schema rows -> OK; a row whose verdict came from PROSE with no VERDICT line -> MISSING (so the
    case can fail); a prose row whose answer DOES carry a VERDICT line -> declared.
  · DRIVEN: no stored answers -> UNMEASURED; an unreadable ledger -> UNKNOWN.
RED_PROOF below.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as cd  # noqa: E402
import second_eye_ledger as L  # noqa: E402


def _row(i, vf, answer="Two findings in the diff.", verdict="findings"):
    return {"ts": str(1790000000000 + i), "sha": "%040d" % i, "verdict": verdict, "verdictFrom": vf,
            "answerFull": answer, "answerHead": answer[:80], "model": "grok-4.7"}


class ADrainedVerdictIsADeclaredOne(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="declared-verdict-")
        self.path = os.path.join(self.d, "ledger.jsonl")
        self._path = L.LEDGER_PATH
        L.LEDGER_PATH = self.path

    def tearDown(self):
        L.LEDGER_PATH = self._path
        shutil.rmtree(self.d, ignore_errors=True)

    def _write(self, rows):
        with open(self.path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def test_drained_rows_are_declared(self):
        self._write([_row(i, "gh#231 comment %d" % (5820000000 + i)) for i in range(6)])
        state, why = cd._check_a_verdict_comes_from_a_declared_field()
        self.assertEqual(state, cd.OK, why)

    def test_schema_rows_are_declared(self):
        self._write([_row(i, "schema") for i in range(6)])
        self.assertEqual(cd._check_a_verdict_comes_from_a_declared_field()[0], cd.OK)

    def test_a_prose_verdict_with_no_line_is_missing(self):
        rows = [_row(i, "gh#231 comment %d" % i) for i in range(5)] + [_row(9, "prose")]
        self._write(rows)
        state, why = cd._check_a_verdict_comes_from_a_declared_field()
        self.assertEqual(state, cd.MISSING, "a verdict guessed from prose passed as declared: " + why)
        self.assertIn("1 of the 6", why)

    def test_a_prose_row_that_states_its_verdict_is_declared(self):
        self._write([_row(i, "prose", answer="Checked the diff.\nVERDICT: clean") for i in range(6)])
        self.assertEqual(cd._check_a_verdict_comes_from_a_declared_field()[0], cd.OK)

    def test_no_answers_is_unmeasured(self):
        self._write([dict(_row(i, "schema"), answerFull="", answerHead="") for i in range(3)])
        self.assertEqual(cd._check_a_verdict_comes_from_a_declared_field()[0], cd.UNMEASURED)

    def test_an_unreadable_ledger_is_unknown(self):
        L.LEDGER_PATH = os.path.join(self.d, "no-such-dir", "ledger.jsonl")
        self.assertEqual(cd._check_a_verdict_comes_from_a_declared_field()[0], cd.UNKNOWN)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1267 - drained #231 verdicts read as undeclared again: the row blames a parser that never guessed",
        "file": "console_doctor.py",
        "find": "        if vf == \"schema\" or vf.startswith(\"gh#231 comment\"):\n",
        "replace": "        if vf == \"schema\":\n",
        "matches": 1,
    },
]
