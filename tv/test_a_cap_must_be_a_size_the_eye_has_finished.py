# -*- coding: utf-8 -*-
"""v3418 — A CAP MAY ONLY BE A SIZE THE EYE HAS BEEN SEEN TO FINISH AT.

Konyo raised the second-eye cap 9,000 -> 26,000 on 2026-09-22 (*"raise the cap to 26000"*), the
call #143 had been waiting on since v3299 left the cost with him.

⚠ THE OLD NUMBER'S EVIDENCE HAD EXPIRED WITHOUT THE NUMBER MOVING. The comment above
`MAX_FENCE_CHARS` justified 9,000 with *"24,000 chars timed out at 240s"* — true when written, and
measured against an `EYE_TIMEOUT_S` that was later raised to 1200. So the ceiling it was protecting
against no longer existed, while the number it produced stayed. That is the shape this gate exists
to stop: a threshold whose justification is about a bound rather than about the instrument.
[[feedback-threshold-above-the-ceiling]] [[feedback-comments-vs-code]]

THE LAW, and it cuts both ways: a cap may not be raised to a size the eye has never finished at,
and it may not be quietly lowered to one the evidence does not support. It is checkable because
every row records what was actually sent.

⚠ AN EMPTY SEAT IS NOT A WITNESS. A row that was sent and never answered proves the payload left,
never that the eye could chew it — which is the entire question. Same for a row with no verdict.

⚠ THIS GATE OWNS ITS LEDGER. `tv/.second_eye.jsonl` is untracked, so a case reading it would
measure his machine and skip on a runner — a permanent skip that reads as a pass. Every case here
builds a temp ledger. The LIVE cap is watched by the doctor row instead, where it belongs.
[[feedback-fixtures-never-touch-live-data]] [[regression-guard]] §3
"""
import io
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


def _row(chars, verdict="clean", reached=True, model=XAI):
    r = {"version": "v9000", "model": model, "reached": reached, "verdict": verdict,
         "ts": time.time(), "findings": [], "sha": "deadbeef", "bytes": {"bible": 1},
         "answerFull": "an answer", "answerHead": "an answer"}
    if chars is not None:
        r["sentCode"] = {"chars": chars, "fences": 1, "unsent": []}
    return r


class TestACapMustBeASizeTheEyeHasFinished(unittest.TestCase):

    def setUp(self):
        self._paths = []

    def tearDown(self):
        for p in self._paths:
            try:
                os.remove(p)
            except Exception:
                pass

    def _ledger(self, rows):
        fd, p = tempfile.mkstemp(suffix=".jsonl", prefix="cap_gate_")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        self._paths.append(p)
        return p

    # ---- the baseline: a real finished look DOES witness a cap ----------------------------

    def test_BASELINE_a_finished_look_witnesses_a_smaller_cap(self):
        p = self._ledger([_row(30000)])
        self.assertTrue(L.cap_is_witnessed(26000, path=p),
                        "a finished 30,000-char look does not witness a 26,000 cap — every case "
                        "below would then pass for the wrong reason")
        self.assertEqual(L.largest_finished_look(path=p), 30000)

    def test_a_cap_above_every_finished_look_is_NOT_witnessed(self):
        p = self._ledger([_row(9000), _row(12000)])
        self.assertFalse(L.cap_is_witnessed(26000, path=p),
                         "a cap larger than anything the eye has ever finished was called "
                         "witnessed — that is a threshold above the ceiling")

    # ---- what does NOT count as a witness ---------------------------------------------------

    def test_an_EMPTY_SEAT_does_not_witness_a_cap(self):
        """It proves the payload was SENT, never that the eye could chew it."""
        p = self._ledger([_row(30000, reached=False)])
        self.assertFalse(L.cap_is_witnessed(26000, path=p),
                         "a seat that never answered was counted as proof the eye can finish that "
                         "size — which is exactly backwards: it is the evidence it CANNOT")
        self.assertIsNone(L.largest_finished_look(path=p))

    def test_a_row_with_no_verdict_does_not_witness_a_cap(self):
        p = self._ledger([_row(30000, verdict="")])
        self.assertFalse(L.cap_is_witnessed(26000, path=p))

    def test_a_row_with_no_sentCode_is_ignored_not_guessed(self):
        p = self._ledger([_row(None), _row(27000)])
        self.assertEqual(L.largest_finished_look(path=p), 27000)

    def test_a_non_numeric_char_count_is_ignored(self):
        bad = _row(30000)
        bad["sentCode"]["chars"] = "lots"
        p = self._ledger([bad, _row(27000)])
        self.assertEqual(L.largest_finished_look(path=p), 27000)

    # ---- UNKNOWN is a third state, not a False ----------------------------------------------

    def test_an_empty_ledger_witnesses_NOTHING_and_says_so(self):
        """None, never False and never True — nobody has looked, so nothing is known."""
        p = self._ledger([])
        self.assertIsNone(L.largest_finished_look(path=p))
        self.assertIsNone(L.cap_is_witnessed(26000, path=p),
                          "an empty ledger answered a definite verdict about a cap it has no "
                          "evidence for")

    def test_a_ledger_of_only_empty_seats_is_UNKNOWN_not_a_refusal(self):
        p = self._ledger([_row(30000, reached=False), _row(9000, reached=False)])
        self.assertIsNone(L.largest_finished_look(path=p))

    # ---- it takes the LARGEST, not the newest ----------------------------------------------

    def test_the_largest_finished_look_is_the_max_not_the_last(self):
        p = self._ledger([_row(31000), _row(12000), _row(8000)])
        self.assertEqual(L.largest_finished_look(path=p), 31000)

    # ---- and the shipped cap itself ---------------------------------------------------------

    def test_the_SHIPPED_cap_is_not_contradicted_by_this_machine(self):
        """⚠ REACH STATED: on a runner the ledger is absent, so this answers UNKNOWN and proves
        nothing there — that is why the LIVE cap is watched by the doctor row and not only here.
        What this case can do everywhere is refuse a cap the local evidence positively DENIES."""
        import second_eye_run as R
        got = L.cap_is_witnessed(R.MAX_FENCE_CHARS)
        self.assertIsNot(got, False,
                         "the shipped cap %r is LARGER than anything the eye has been seen to "
                         "finish on this machine — raise the evidence or lower the cap"
                         % (R.MAX_FENCE_CHARS,))


RED_PROOF = [
    {
        "why": "v3418 - AN EMPTY SEAT COUNTED AS A WITNESS. Dropping the reached check makes a "
               "payload that was SENT and never answered vouch for a cap, which is the exact "
               "inversion: a timeout at that size is evidence the eye CANNOT chew it.",
        "file": "second_eye_ledger.py",
        "find": "        if r.get(\"reached\") is not True:\n            continue\n        if not str(r.get(\"verdict\") or \"\").strip():",
        "replace": "        if False:\n            continue\n        if not str(r.get(\"verdict\") or \"\").strip():",
        "matches": 1,
    },
    {
        "why": "v3418 - A ROW WITH NO VERDICT COUNTED. A row carrying no answer is not a finished "
               "look, and letting it witness a cap means the ledger vouches for sizes nothing ever "
               "came back from.",
        "file": "second_eye_ledger.py",
        "find": "        if not str(r.get(\"verdict\") or \"\").strip():\n            continue\n        sc = r.get(\"sentCode\")",
        "replace": "        if False:\n            continue\n        sc = r.get(\"sentCode\")",
        "matches": 1,
    },
    {
        "why": "v3418 - AN EMPTY LEDGER VOUCHING FOR EVERYTHING. Answering True when nothing has "
               "ever been measured is the collapse of UNKNOWN into fine - a fresh machine would "
               "certify any cap at all.",
        "file": "second_eye_ledger.py",
        "find": "    big = largest_finished_look(path)\n    if big is None:\n        return None",
        "replace": "    big = largest_finished_look(path)\n    if big is None:\n        return True",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
