# -*- coding: utf-8 -*-
"""v3420 — A VERDICT THE MODEL WAS CONSTRAINED TO EMIT IS NOT ONE A REGEX GUESSED.

`_verdict_for` and the machinery under it are a long line of patches on reading prose, and their
own docstrings in second_eye_run.py are the receipts:

  · v2808 — a CLEAN look filed as `findings`
  · v3198 — that fix was "wrong in BOTH directions"; a declaration followed by exactly ONE listed
            P1 produced len(findings)==1, which is not >1, so the declaration cleared it and a real
            P1 was filed as a clean look
  · a review saying NO DEFECTS filed `findings` because the word after `defects` was `meeting`
  · an answer ending "VERDICT: clean" filed `findings`

Every patch was right about the case in front of it and wrong about the next, because PROSE IS NOT
A FIELD. MEASURED 2026-09-23: `grok --json-schema` answers with an envelope carrying `text`,
`thought`, `usage` and `structuredOutput`, and the model cannot emit a verdict outside the enum.

⚠ THE PROSE PATH IS NOT DELETED. The MCP transport cannot constrain, and a look taken through it
must still be recordable. What this law pins is that the ROW SAYS WHICH ROUTE PRODUCED IT — a
verdict forced into an enum and a verdict inferred from sentences are different evidential objects,
and collapsing them is how this ledger came to assert things the eye never said.
[[unknown-stays-unknown]] [[label-outlived-referent]]

⚠ THIS GATE NEVER TOUCHES THE LIVE LEDGER. `record_answer` writes through `SEL.record(path=None)`,
which resolves to the real `tv/.second_eye.jsonl`; every case here repoints `SEL.LEDGER_PATH` at a
temp file and restores it. [[feedback-fixtures-never-touch-live-data]]
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

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_ledger as SEL  # noqa: E402
import second_eye_run as R  # noqa: E402

ANSWER = ("A long enough reply to count as a look at all, describing the diff and what it does, "
          "with more than forty characters so no emptiness guard fires on it.")


class TestAConstrainedVerdictIsNotAParsedOne(unittest.TestCase):

    def setUp(self):
        fd, self._p = tempfile.mkstemp(suffix=".jsonl", prefix="verdict_gate_")
        os.close(fd)
        self._real = SEL.LEDGER_PATH
        SEL.LEDGER_PATH = self._p

    def tearDown(self):
        SEL.LEDGER_PATH = self._real
        try:
            os.remove(self._p)
        except Exception:
            pass

    def _row(self, structured=None, answer=ANSWER):
        R.record_answer("v9900", answer, {"chars": 500, "fences": 1, "unsent": []},
                        prompt_text="", answer_model="grok-4-1-fast-reasoning",
                        sha="deadbeef", structured=structured)
        rows = [json.loads(l) for l in io.open(self._p, encoding="utf-8") if l.strip()]
        self.assertTrue(rows, "record_answer wrote nothing at all")
        return rows[-1]

    # ---- the baseline: the prose path must still work, or every case below is vacuous ----

    def test_BASELINE_the_prose_path_still_records_a_look(self):
        row = self._row(structured=None)
        self.assertTrue(row.get("reached"), "the prose path stopped recording a look")
        self.assertEqual(row.get("verdictFrom"), "prose",
                         "an unconstrained answer must say so — every case below compares against "
                         "this")

    # ---- the law ------------------------------------------------------------------------

    def test_a_constrained_verdict_is_READ_not_inferred(self):
        row = self._row({"verdict": "clean", "findings": [], "unseen": ""})
        self.assertEqual(row.get("verdict"), "clean")
        self.assertEqual(row.get("verdictFrom"), "schema",
                         "a verdict the model was constrained to emit was filed as if a regex had "
                         "guessed it")

    def test_the_two_routes_are_DISTINGUISHABLE_in_the_row(self):
        a = self._row({"verdict": "clean", "findings": [], "unseen": ""})
        b = self._row(None)
        self.assertNotEqual(a.get("verdictFrom"), b.get("verdictFrom"),
                            "a constrained verdict and a parsed one are recorded identically — the "
                            "reader cannot weight them apart")

    def test_the_constrained_findings_are_the_ones_recorded(self):
        row = self._row({"verdict": "findings",
                         "findings": ["the count is compared against nothing"],
                         "unseen": ""})
        self.assertEqual(row.get("verdict"), "findings")
        self.assertIn("compared against nothing", json.dumps(row.get("findings")))

    def test_what_the_eye_was_NOT_shown_is_recorded_as_part_of_the_look(self):
        """A clean verdict taken through a keyhole is not a clean verdict."""
        row = self._row({"verdict": "clean", "findings": [],
                         "unseen": "bible.html never reached me"})
        self.assertIn("NOT SHOWN", json.dumps(row.get("findings")),
                      "the eye said what it could not see and the row dropped it")
        self.assertIn("bible.html", json.dumps(row.get("findings")))

    # ---- what must NOT be accepted --------------------------------------------------------

    def test_a_verdict_OUTSIDE_the_enum_is_not_accepted_as_schema(self):
        """A transport that returns junk in the field must fall back, not be believed."""
        row = self._row({"verdict": "looks fine to me", "findings": [], "unseen": ""})
        self.assertEqual(row.get("verdictFrom"), "prose",
                         "an out-of-enum string was accepted as a constrained verdict")

    def test_an_empty_structured_object_falls_back(self):
        row = self._row({})
        self.assertEqual(row.get("verdictFrom"), "prose")

    def test_a_non_dict_structured_falls_back(self):
        row = self._row("clean")
        self.assertEqual(row.get("verdictFrom"), "prose")

    def test_cannot_tell_survives_the_schema_path(self):
        """The verdict the whole ledger exists to keep apart from clean."""
        row = self._row({"verdict": "cannot-tell", "findings": [],
                         "unseen": "4 of 5 changed files never arrived"})
        self.assertEqual(row.get("verdict"), "cannot-tell")
        self.assertEqual(row.get("verdictFrom"), "schema")

    # ---- the schema itself ----------------------------------------------------------------

    def test_the_schema_constrains_the_verdict_to_three_words(self):
        s = json.loads(R.EYE_VERDICT_SCHEMA)
        self.assertEqual(sorted(s["properties"]["verdict"]["enum"]),
                         ["cannot-tell", "clean", "findings"])
        self.assertIn("unseen", s["required"],
                      "the eye is not required to say what it was NOT shown")

    def test_the_eye_is_denied_every_write_tool(self):
        """⚠ v3408: a CLI eye is an AGENT with tools and CAN edit this checkout — Grok was caught
        writing to tv/ mid-ship on 2026-09-22. An empty cwd is a hiding place, not a guard."""
        src = io.open(os.path.join(HERE, "second_eye_run.py"),
                      encoding="utf-8", errors="replace").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        for tool in ("Edit", "Write", "MultiEdit"):
            self.assertIn('"--deny", "%s"' % tool, code,
                          "the eye is not denied the %s tool" % tool)


RED_PROOF = [
    {
        "why": "v3420 - THE ENUM CHECK REMOVED. Accepting whatever string the field holds means a "
               "transport that returns prose, junk or a fourth verdict word is recorded as a "
               "CONSTRAINED answer, which is the entire property this law buys.",
        "file": "second_eye_run.py",
        "find": '        if _v in ("clean", "findings", "cannot-tell"):',
        "replace": '        if True:',
        "matches": 1,
    },
    {
        "why": "v3420 - THE ROUTE ERASED. With verdictFrom never written, a verdict forced into an "
               "enum and one a regex guessed from sentences become the same row, and no reader can "
               "weight them apart - the collapse this ledger has already been burned by.",
        "file": "second_eye_ledger.py",
        "find": '        "verdictFrom": (str(verdict_from).strip() or None) if verdict_from else None,\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "v3420 - THE CONSTRAINT IGNORED. Running the prose parser even when the model was "
               "constrained throws the field away and reinstates every defect the parser's own "
               "docstrings record.",
        "file": "second_eye_run.py",
        "find": '    if _verdict_from == "prose":',
        "replace": '    if True:',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
