# -*- coding: utf-8 -*-
"""v2779 — FOUR "COLD CODE REVIEWS" WERE RECORDED AS LOOKS AND THE CODE WAS NEVER SENT.

2026-09-08. The second-eye lane recorded `reached=True` rows for v2772, v2774 and v2776 whose
prompts contained, inside the code fence, the LITERAL TEXT

    \"\"\" + open('/tmp/eye_cold.txt').read() + \"\"\"

because the prompt was assembled as an ordinary string and the concatenation was never evaluated.
The other family received a fence full of Python source-expression — plus several paragraphs of
careful, accurate prose context describing what the code did — and answered CONFIDENTLY in
specific-sounding language:

    "The inference is unsound under the documented threading model; the failure mode is the
     dangerous one. Thread A reads counter (value N), thread B increments it..."

That is a review of code it had never seen. A sentinel probe settled it: asked to quote the
snippet's first line, the model answered **"NO CODE RECEIVED"**.

=== ⚠ THE PART THAT MAKES THIS A GATE AND NOT A NOTE ===
Nothing in the lane could have caught it, because the ledger recorded the CLAIM that a look
happened and never the TRANSMISSION. Every field it stored — model, family, verdict, findings, the
head of the raw answer, even a hash of the bytes I *said* were photographed — describes the ANSWER.
Not one described the QUESTION. So a fluent answer to a prompt containing no code was indistinguish-
able from a real review, and stayed that way for four versions. [[the-unjoined-end]]

=== ⚠⚠ AND IT WAS NOT ALL OF THEM — the count is the tell ===
I first told Konyo that EVERY cold review this session had gone out empty. Measured against the
stored Grok-MCP prompts, that was wrong: **v2775 carried its diff intact** (0 literals, 0 seams),
and its finding — a redundant `max-width: 100%` on `.fleet-box` — was real and was acted on. A
blanket retraction would have been exactly as unmeasured as the original overclaim, in the other
direction. Grep the prompts, count, let the count decide.
[[inherited-claim-is-not-evidence]] [[feedback-suspect-the-instrument]]

=== WHAT IS PINNED HERE ===
`code_was_transmitted()` reads the FENCES ONLY — never the whole prompt — because a prompt may
legitimately discuss `open().read()` in its prose, and a whole-text search would go red on this very
docstring. [[source-reading-guard]]
"""
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import second_eye_ledger as L  # noqa: E402

# The exact shape that shipped, built at runtime so this file never contains it as one literal
# string — otherwise the module's own source would trip a future whole-file search.
_Q3 = '"' * 3
LITERAL_FENCE = "context\n```python\n%s + open('/tmp/eye_cold.txt').read() + %s\n```\nnow answer" % (_Q3, _Q3)
REAL_FENCE = "context\n```javascript\nvar _n = 0;\nif (Array.isArray(_p)) { _n++; }\n```\nnow answer"


class AColdReviewMustCarryTheCode(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_an_UNEVALUATED_file_read_is_detected(self):
        """★★ The exact text that shipped, four times."""
        r = L.code_was_transmitted(LITERAL_FENCE)
        self.assertTrue(r["unsent"],
                        "the un-evaluated open(...).read() in the code fence is no longer detected, "
                        "so a review of code that was never sent records as a real look again")

    def test_REAL_code_in_a_fence_is_NOT_flagged(self):
        """⛔ THE FALSE-POSITIVE HALF. A detector that flags real reviews is worse than none — it
        would make the lane refuse every genuine second eye and there would be no way to ship."""
        r = L.code_was_transmitted(REAL_FENCE)
        self.assertEqual(r["unsent"], [],
                         "a fence holding real code was flagged as un-transmitted")
        self.assertGreater(r["chars"], 0, "real code measured as 0 characters")

    def test_it_reads_the_FENCES_and_not_the_PROSE(self):
        """⚠ [[source-reading-guard]]. Prose ABOUT `open(...).read()` is not a fence full of it, and
        this file's own module docstring is the proof: a whole-text search would go red on the very
        explanation of the defect. Sixth-plus time in this repo that a guard read prose as code."""
        prose = ("I once shipped a prompt whose fence held %s + open('/x').read() + %s and nobody "
                 "noticed.\n```javascript\nvar a = 1;\n```" % (_Q3, _Q3))
        self.assertEqual(L.code_was_transmitted(prose)["unsent"], [],
                         "the detector searched the whole prompt instead of the fences, so writing "
                         "about the defect is now indistinguishable from committing it")

    def test_NO_FENCE_is_UNKNOWN_and_not_a_failure(self):
        """⚠ [[unknown-stays-unknown]]. A pixel look carries an image, not a fence. Zero code chars
        with zero markers is 'no code here', which is a different fact from 'code was promised and
        did not arrive' — and only the second one is a defect."""
        r = L.code_was_transmitted("just a question about a screenshot")
        self.assertEqual(r["chars"], 0)
        self.assertEqual(r["fences"], 0)
        self.assertEqual(r["unsent"], [], "an ordinary question was recorded as a failed send")

    # ── ⚠ THE JOIN — the detector must actually REACH the ledger ────────────────────────────
    def test_record_REFUSES_to_call_it_a_look(self):
        """★★ [[plumbing-with-no-tap]]. A detector nothing calls is the same defect one layer up.
        `record()` must force the row to an EMPTY SEAT, not merely annotate it."""
        d = tempfile.mkdtemp()
        p = os.path.join(d, "t.jsonl")
        row = L.record("v9999", "grok-4", "clean", answer_head="looks fine",
                       sent=LITERAL_FENCE, path=p)
        self.assertFalse(row["reached"],
                         "a review whose prompt carried no code still recorded as REACHED, so the "
                         "gate would let the next version ship on it")
        self.assertEqual(row["verdict"], "cannot-tell")
        self.assertTrue(row.get("retracted"), "the row does not say why it was refused")
        self.assertTrue(L.owes_a_look("v9999", path=p),
                        "an empty-seat row satisfied the ship gate")

    def test_record_ACCEPTS_a_real_one(self):
        """⛔ The other half — proving the refusal above is not simply 'refuse everything'."""
        d = tempfile.mkdtemp()
        p = os.path.join(d, "t.jsonl")
        row = L.record("v9999", "grok-4", "findings", findings=["a real one"],
                       answer_head="Array.isArray is the fix", sent=REAL_FENCE, path=p)
        self.assertTrue(row["reached"], "a genuine review with its code attached was refused")
        self.assertFalse(L.owes_a_look("v9999", path=p))

    def test_an_UNPASSED_prompt_records_UNKNOWN_never_a_pass(self):
        """⚠ [[unknown-stays-unknown]]. Callers that never pass `sent` must leave a NULL behind, so
        'nobody checked' is visible as itself. Writing `{"unsent": []}` there would be a measurement
        nobody took, and every one of the 397 rows predating this field would silently acquire it."""
        d = tempfile.mkdtemp()
        p = os.path.join(d, "t.jsonl")
        row = L.record("v9999", "grok-4", "clean", answer_head="fine", path=p)
        self.assertIsNone(row["sentCode"],
                          "a row whose prompt was never inspected claims to have been inspected")

    # ── ⚠ THE HISTORICAL RECORD ─────────────────────────────────────────────────────────────
    def test_the_retracted_rows_stay_retracted(self):
        """⚠ The three shipped rows were corrected in place rather than deleted: a deleted row reads
        as 'never happened', and what happened is that a look was CLAIMED. If the live ledger is
        present, they must still carry their retraction and must not count as looks."""
        p = L.LEDGER_PATH
        if not os.path.exists(p):
            self.skipTest("no live ledger on this machine — UNMEASURED, not a pass")
        rows = [json.loads(l) for l in io.open(p, encoding="utf-8") if l.strip()]
        bad = [r for r in rows
               if r.get("version") in ("v2772", "v2774", "v2776")
               and r.get("reached") and not r.get("retracted")]
        self.assertEqual(bad, [],
                         "a retracted prose-only review is claiming to be a look again")


if __name__ == "__main__":
    unittest.main(verbosity=2)
