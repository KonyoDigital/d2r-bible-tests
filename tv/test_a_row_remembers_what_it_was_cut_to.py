# -*- coding: utf-8 -*-
"""v3339 (#77) — A ROW REMEMBERS WHAT IT WAS CUT TO, AND ONE PLACE DOES THE CUTTING.

The second-eye ledger stores the HEAD of each answer so a plausible summary cannot stand in for a
look. Judging whether a stored verdict still means what it says requires knowing whether the whole
answer is there — and the cap was written in FOUR places:

    second_eye_run.py   answer_head=_reply[:200]          (reached=False)
    second_eye_run.py   answer_head=answer[:400]          (the main, reached path)
    second_eye_run.py   answer_head=(answer or "")[:200]  (reached=False)
    second_eye_ledger.py  str(answer_head or "")[:ANSWER_HEAD_CAP]   (600)

The RUNNER cut first, so a row capped at 400 never reached 600 and the re-judger treated it as a
whole answer. MEASURED on 843 rows: 381 sat at exactly 400 while `prefixOnly` reported 98. The
census, counting only the writer's 600, reported 91 — two readings disagreeing because one number
lived in four places. After the fix, on 847 rows: prefixOnly 478, and `agree` fell 554 -> 192.
THREE HUNDRED AND SIXTY-TWO ROWS LEFT "AGREEMENT" FOR UNKNOWN, which is the only honest direction.

⚠ A LEGACY ROW CARRIES NO headCap AND THAT IS UNKNOWN, NOT WHOLE. Rows written before this sat on
either 200, 400 or 600 and nothing on disk says which, so all three lengths are treated as
prefix-only. That can only REMOVE claimed agreement, never manufacture it.
[[copy-drift]] [[heart-first]] §6 — persist what you knew, not a summary of it.
[[unknown-stays-unknown]]
"""
import io
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_ledger as L  # noqa: E402


class TestARowRemembersWhatItWasCutTo(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hcap_")
        self.path = os.path.join(self.tmp, "rows.jsonl")

    def test_the_row_records_the_cap_that_was_applied(self):
        """BEHAVIOURAL. A cap that is not written down has to be guessed by every later reader."""
        r = L.record("vTEST", "m", "clean", answer_head="x" * 5000, head_cap=400, path=self.path)
        self.assertEqual(
            len(r["answerHead"]), 400,
            "the writer did not apply the cap it was given; the head is %d chars."
            % len(r["answerHead"]))
        self.assertEqual(
            r.get("headCap"), 400,
            "the row does not record headCap, so a reader must guess which of 200/400/600 cut it "
            "— which is the guess that made prefixOnly report 98 where the truth was 478.")

    def test_the_default_cap_is_resolved_at_call_time(self):
        """⚠ ANSWER_HEAD_CAP is defined BELOW record() in that file. A default evaluated in the
        signature would freeze whatever the bar was the day the line was written — and here it
        would not even import. [[regression-guard]] §4"""
        r = L.record("vTEST", "m", "clean", answer_head="y" * 5000, path=self.path)
        self.assertEqual(r.get("headCap"), L.ANSWER_HEAD_CAP,
                         "the default cap did not follow ANSWER_HEAD_CAP")
        self.assertEqual(len(r["answerHead"]), L.ANSWER_HEAD_CAP)

    def test_the_runner_does_not_cut_before_the_writer(self):
        """ONE DEFINITION. A second cut upstream is how the two numbers drifted apart."""
        with io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8") as fh:
            code = "\n".join(l.split("#", 1)[0] for l in fh.read().split("\n"))
        hits = re.findall(r"answer_head\s*=\s*[^,\n]*\[:\s*\d+\s*\]", code)
        self.assertEqual(
            hits, [],
            "%d site(s) in the runner still truncate before the writer: %s. The runner must pass "
            "the FULL answer and DECLARE its cap with head_cap=, so exactly one place cuts and the "
            "row can say what it was cut to." % (len(hits), ", ".join(hits)))
        self.assertGreaterEqual(
            len(re.findall(r"head_cap\s*=\s*\d+", code)), 3,
            "the runner no longer declares head_cap at its call sites, so every row falls back to "
            "the writer's default and an unreached 200-char stub is judged as a whole answer.")

    def test_a_legacy_row_without_a_cap_is_UNKNOWN_not_whole(self):
        """⚠ THE ONE THAT MATTERS. 824 rows predate headCap; treating them as whole is the
        confident-zero this fix exists to remove."""
        import json
        with io.open(self.path, "a", encoding="utf-8") as fh:
            for n in (200, 400, L.ANSWER_HEAD_CAP):
                fh.write(json.dumps({"version": "vOLD", "model": "m", "verdict": "clean",
                                     "answerHead": "z" * n, "reached": True}) + "\n")
        out = L.verdict_provenance(self.path)
        self.assertGreaterEqual(
            out["prefixOnly"], 3,
            "a legacy row at 200/400/%d was re-judged as a whole answer. Nothing on disk says "
            "which cap applied, so all three are UNKNOWN — and UNKNOWN may never be counted as "
            "agreement. Got prefixOnly=%d." % (L.ANSWER_HEAD_CAP, out["prefixOnly"]))
        self.assertEqual(
            out["agree"], 0,
            "a legacy row with an unknown cap landed in `agree` (%d). That is the exact inflation "
            "this law removes." % out["agree"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "reading a hardcoded cap instead of the row's own puts 362 prefix rows back into agreement",
        "file": "tv/second_eye_ledger.py",
        "find": '        _cap = r.get("headCap")',
        "replace": '        _cap = ANSWER_HEAD_CAP',
        "matches": 1,
    },
    {
        "why": "dropping headCap from the row leaves every later reader guessing which cap applied",
        "file": "tv/second_eye_ledger.py",
        "find": '        "headCap": _cap,',
        "replace": '        "headCapX": _cap,',
        "matches": 1,
    },
    {
        "why": "putting the cut back in the runner recreates the two-numbers-one-cap drift",
        "file": "tv/second_eye_run.py",
        "find": "answer_head=answer, head_cap=400, reached=True,",
        "replace": "answer_head=answer[:400], reached=True,",
        "matches": 1,
    },
]
