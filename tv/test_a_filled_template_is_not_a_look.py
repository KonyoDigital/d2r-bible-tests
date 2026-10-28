# -*- coding: utf-8 -*-
"""REG-2740 - A SCHEMA ANSWER OF "findings" THAT LISTS NONE IS NOT A LOOK, ON THE GATE AND ON THE AUDIT ALIKE.

MEASURED on v3820's row, the whole answer: {"verdict":"findings","findings":[],"unseen":"placeholder"}. The eye was held
to the verdict schema and filled it in: findings with no finding, and the word "placeholder" where its reach note goes.
second_eye_run files the unseen note among the findings, so the row carried exactly one line - the eye's own NOT SHOWN
note - and `_has_evidence` read that line as a finding. The runner printed "LOOKED - 1 finding(s) recorded", the push
gate counted it, and v3821 shipped past a seat nobody sat in.

A schema verdict of findings with nothing but the eye's own NOT SHOWN note contradicts itself; it is now read as NOT a
look by looked_at, by owes_a_look, by audit() and by the gate's refusal message - one predicate, row_is_not_a_look, so
no surface reads the row another way (v3415, test_the_audit_and_the_gate_read_one_row_one_way).

⚠ ONLY SCHEMA ROWS. 92 rows in the real ledger were drained from public #231 comments and also say findings with none
listed; each is bound to the comment that carries its findings (verdictFrom "gh#231 comment <id>"), and each still
counts. A clean schema look with a NOT SHOWN note is a clean look, and a real finding beside the note is a look.

Every case builds its own temp ledger (the live one is per machine). RED_PROOF below.
"""
import json
import os
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_ledger as L  # noqa: E402

XAI = "grok-4-1-fast-reasoning"
NOTE = L.NOT_SHOWN_PREFIX + "placeholder"


def _row(version, **kw):
    r = {"version": version, "model": XAI, "verdict": "findings", "reached": True, "ts": time.time(),
         "findings": [], "sha": "deadbeef", "answerHead": '{"verdict":"findings","findings":[],"unseen":"placeholder"}',
         "verdictFrom": "schema"}
    r.update(kw)
    return r


class AFilledTemplateIsNotALook(unittest.TestCase):

    def setUp(self):
        self._paths = []

    def tearDown(self):
        for p in self._paths:
            try:
                os.remove(p)
            except Exception:
                pass

    def _ledger(self, rows):
        fd, p = tempfile.mkstemp(suffix=".jsonl", prefix="eye_template_")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        self._paths.append(p)
        return p

    def _read(self, row):
        """-> (looked_at count, owes_a_look, audit looks) for one row in its own ledger"""
        p = self._ledger([row])
        v = row["version"]
        got = [s for s in L.audit(path=p) if s["version"] == v]
        self.assertEqual(len(got), 1, "audit() did not produce exactly one row for %s" % v)
        return len(L.looked_at(v, path=p)), L.owes_a_look(v, path=p), got[0]["looks"]

    def test_BASELINE_a_real_finding_beside_the_note_is_a_look(self):
        self.assertEqual(self._read(_row("v9201", findings=["a real defect at x.py:12", NOTE])), (1, False, 1),
                         "a schema look with a real finding no longer counts - every case below would agree for the wrong reason")

    def test_BASELINE_a_clean_schema_look_with_its_note_is_a_look(self):
        self.assertEqual(self._read(_row("v9202", verdict="clean", findings=[NOTE])), (1, False, 1))

    def test_BASELINE_a_drained_comment_row_listing_none_is_still_a_look(self):
        self.assertEqual(self._read(_row("v9203", verdictFrom="gh#231 comment 5868503290", answerHead="")), (1, False, 1),
                         "a row bound to a public #231 comment stopped counting (92 such rows in the real ledger)")

    def test_v3820s_row_is_not_a_look_on_any_surface(self):
        self.assertEqual(self._read(_row("v9204", findings=[NOTE])), (0, True, 0),
                         "a schema 'findings' with only the eye's own NOT SHOWN note still counts as a look")

    def test_findings_with_nothing_at_all_is_not_a_look(self):
        self.assertEqual(self._read(_row("v9205", findings=[])), (0, True, 0))

    def test_the_runner_files_the_note_under_the_ledgers_one_prefix(self):
        src = open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8").read()
        self.assertEqual(src.count("findings = findings + [SEL.NOT_SHOWN_PREFIX + _unseen]"), 1,
                         "the runner spells the NOT SHOWN prefix itself again - two spellings, and the rule reads one")


RED_PROOF = [
    {"why": "REG-2740 - a filled-in template counts as a look again",
     "file": "second_eye_ledger.py",
     "find": "    return is_not_a_look((row or {}).get(\"verdict\")) or a_template_not_a_look(row)\n",
     "replace": "    return is_not_a_look((row or {}).get(\"verdict\"))\n",
     "matches": 1},
    {"why": "REG-2740 - every schema 'findings' row is refused, real findings or not",
     "file": "second_eye_ledger.py",
     "find": "    return all(f.startswith(NOT_SHOWN_PREFIX) for f in lines)\n",
     "replace": "    return True\n",
     "matches": 1},
    {"why": "REG-2740 - drained #231 comment rows are refused too (92 real looks lost)",
     "file": "second_eye_ledger.py",
     "find": "    if not isinstance(row, dict) or str(row.get(\"verdictFrom\") or \"\").strip() != \"schema\":\n",
     "replace": "    if not isinstance(row, dict):\n",
     "matches": 1},
    {"why": "REG-2740 - the audit reads the template one way and the gate another (v3415 again)",
     "file": "second_eye_ledger.py",
     "find": "        elif fam and _has_evidence(r) and row_is_not_a_look(r):",
     "replace": "        elif fam and _has_evidence(r) and is_not_a_look(r.get(\"verdict\")):",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
