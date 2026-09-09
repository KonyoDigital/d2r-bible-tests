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


class ARealDiffMustNotRetractItsOwnReview(unittest.TestCase):
    """v2824 — THE FALSE POSITIVE THAT WOULD HAVE DEADLOCKED THE REPO SHUT, TWICE.

    `_UNSENT_MARKERS` matched a class of ANY three quote CHARACTERS, so ordinary JavaScript
    concatenating a quote — `esc(call) + '"'` — read as a Python triple-quote seam. A non-empty
    `unsent` RETRACTS the row to `reached=False`, and a version may not ship while the previous one
    has never been looked at. So every review of a diff touching control_ui.html or bible.html —
    which is most of them — would have filed as an EMPTY SEAT and nothing could ever ship again.

    MEASURED on the real v2821 review payload: exactly ONE hit, in a bible.html hunk.

    THIS IS THE SAME DEADLOCK v2808 FIXED, IN A DIFFERENT SPELLING. That fix narrowed WHERE the
    pattern may match — not across a newline, not on a diff marker — and never WHAT a triple quote
    actually is. A guard hardened against one spelling of its own false positive is hardened
    against that spelling only. [[feedback-suspect-the-instrument]]
    """

    JS_CASES = (
        ("a double quote in JS", "out = esc(call) + " + chr(39) + chr(34) + chr(39) + " + tail;"),
        ("a single quote in JS", "out = a + " + chr(34) + chr(39) + chr(34) + " + b;"),
        ("a quote before the +", "out = " + chr(39) + chr(34) + chr(39) + " + tail;"),
    )

    def test_javascript_concatenating_a_quote_is_not_a_python_seam(self):
        for label, body in self.JS_CASES:
            got = L.code_was_transmitted("```js\n%s\n```" % body)
            self.assertEqual([], got["unsent"],
                             "%s retracts a review row — the ledger would refuse every diff that "
                             "touches a JS surface, and nothing could ship: %s"
                             % (label, got["unsent"]))
            self.assertGreater(got["chars"], 0, "the fence was not even counted as code")

    def test_a_real_python_seam_is_still_caught(self):
        """[[feedback-blind-fixture-green-gate]] — a guard that can only pass measures nothing."""
        _d, _s = chr(34) * 3, chr(39) * 3
        cases = (
            ("triple-quote then +", "print(" + _d + "head" + _d + " + body)"),
            ("+ then triple-quote", "msg = head + " + _d + "tail" + _d),
            ("single-quoted triple", "msg = head + " + _s + "tail" + _s),
            ("an un-evaluated read", "prompt = open(" + chr(34) + "f.py" + chr(34) + ").read()"),
        )
        for label, body in cases:
            got = L.code_was_transmitted("```python\n%s\n```" % body)
            self.assertTrue(got["unsent"],
                            "%s is a REAL un-evaluated seam and the guard let it through — a "
                            "review of a promise would file as a review of the code" % label)

    def test_a_comment_describing_the_pattern_is_not_the_pattern(self):
        """v2825 — THE GUARD MATCHED ITS OWN DOCUMENTATION, INSIDE A DIFF OF ITSELF.

        second_eye_ledger's comment beside _UNSENT_MARKERS spells out what a real seam looks like.
        When a review diff includes that file, the sentence is inside the fence and BOTH markers
        fire on it, so the row is retracted, the look files as an empty seat, and the next push is
        refused. Measured on the v2824 payload: two hits, both on that one comment line, zero real
        seams.

        The docstring of code_was_transmitted already names this defect one level up — prose may
        legitimately DISCUSS the expression, which is why it searches fences and not the whole
        prompt. When the fence holds a real file whose PROSE discusses the pattern, the same
        problem returns inside it. [[feedback-comments-vs-code]]
        """
        _d = chr(34) * 3
        cases = (
            ("a bare comment", "# A REAL seam is " + _d + " + x or x + " + _d + " on ONE line."),
            ("an added diff line", "+    # the seam is " + _d + " + x here"),
            ("a context diff line", "     # or x + " + _d + " on one line"),
        )
        for label, body in cases:
            got = L.code_was_transmitted("```python\n%s\n```" % body)
            self.assertEqual([], got["unsent"],
                             "%s retracts a review row — a sentence describing the rule is not "
                             "the rule, and a diff of this very file would deadlock the ledger: %s"
                             % (label, got["unsent"]))

    def test_a_seam_on_a_real_code_line_survives_the_comment_skip(self):
        """The skip must be LINE-scoped, not fence-scoped.

        v2826 — THE FIRST VERSION OF THIS TEST WAS VACUOUS AND A CROSS-FAMILY REVIEW SAID SO. It
        asserted only that a body of `comment + code-with-seam` still fires — which is true whether
        the scan skips comment lines or reads the whole fence, so it passed identically before and
        after the change it was written to guard. REPRODUCED by running the pre-fix code path
        beside the post-fix one: both returned the same finding.

        The discriminating shape is the PAIR. Only a line-scoped skip can make the comment-only
        body clean AND the comment+code body fire; a fence-scoped skip clears both, and no skip at
        all fires on both. [[feedback-blind-fixture-green-gate]]
        """
        _d = chr(34) * 3
        seam = "msg = head + " + _d + "tail" + _d
        note = "# describing it here: " + _d + " + x"
        only_comment = L.code_was_transmitted("```python\n%s\n```" % note)
        with_code = L.code_was_transmitted("```python\n%s\n%s\n```" % (note, seam))
        self.assertEqual([], only_comment["unsent"],
                         "a fence holding ONLY a comment about the pattern fires — the deadlock is "
                         "back: %s" % only_comment["unsent"])
        self.assertTrue(with_code["unsent"],
                        "a real seam on a code line beneath that same comment did NOT fire, so the "
                        "skip is fence-scoped rather than line-scoped and swallowed the law")

    def test_the_limit_of_the_comment_skip_is_stated_not_hidden(self):
        """A seam written INSIDE a comment is not detected, and that is the accepted trade.

        Raised by the cross-family review with a concrete string. It is real: the scan drops
        comment lines, so a marker sitting on one is invisible. It is not fixed, because fixing it
        is what caused the deadlock this whole change undoes — and it costs little, since the guard
        exists to catch a prompt that carries a PROMISE INSTEAD OF the code. A seam quoted inside a
        comment means a real fence was transmitted around it.

        A stated limit is not a defect; an unstated one is. This test exists so the limit cannot
        quietly change without somebody reading this paragraph. [[unknown-stays-unknown]]
        """
        _d = chr(34) * 3
        hidden = "+    # msg = head + " + _d + " + tail" + _d
        got = L.code_was_transmitted("```python\n%s\n```" % hidden)
        self.assertEqual([], got["unsent"],
                         "the comment skip no longer covers this shape. That may be an improvement "
                         "— but re-read the deadlock note in second_eye_ledger before keeping it, "
                         "because the last time this scan reached into prose the ledger refused "
                         "every push: %s" % got["unsent"])

# ══ THE EXECUTABLE RED-PROOF ═══════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "removing the comment skip makes the guard match its own documentation, so a\n               review diff that touches this very file retracts its own row and the next push\n               is refused",
        "file": "second_eye_ledger.py",
        "find": '        _code = "\\n".join(ln for ln in body.split("\\n")\n                          if not _COMMENT_LINE.match(ln))',
        "replace": '        _code = body',
        "matches": 1,
    },
    {
        "why": "restoring the any-three-quotes class is the deadlock verbatim: JS concatenating a "
               "quote reads as a Python triple-quote seam and retracts every review of a diff "
               "carrying a JS surface",
        "file": "second_eye_ledger.py",
        "find": '(re.compile(r"\\S[ \\t]*\\+[ \\t]*(?:\\\'{3}|\\"{3})")',
        "replace": '(re.compile(r"\\S[ \\t]*\\+[ \\t]*[\\"\']{3}")',
        "matches": 1,
    },
    {
        "why": "dropping the seam markers entirely lets a review of a PROMISE file as a review of "
               "the code — the defect the whole transmission check exists for",
        "file": "second_eye_ledger.py",
        # ⚠ RE-ANCHORED at v2825: the comment-skip change moved this line (body -> _code).
        # heart2 said so at once — INVALID, the tamper matched 0 times — which is the
        # correct diagnosis and the second time tonight a refactor of mine moved a proof's
        # target. The LAW is unchanged. [[sabotage-is-usually-the-wrong-one]]
        "find": '            if rx.search(_code) and msg not in why:',
        "replace": "            if False:",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
