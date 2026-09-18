# -*- coding: utf-8 -*-
"""v3292 — A RED-PROOF THAT PROVED NOTHING MUST NOT REPORT SUCCESS.

Tonight a red-proof came back **BLIND**: it matched its anchor exactly once, deleted the clause it
targeted, and the law stayed GREEN. It was asserting two phrases against a whole file, and both
occur three times because neighbouring panels share the idiom — so unrelated sites satisfied it
and it had never pinned its own branch. I caught that only because I happened to run
`heart2.py --prove` by hand.

BLIND already returned 1, and that was right. **INVALID did not**, and INVALID is the verdict that
says the sabotage MATCHED NOTHING — the proof changed no byte, so the gate has no working
red-proof at all while reporting that it has one.

MEASURED 2026-09-18 with a throwaway gate whose `find` was deliberately absent from the file:

    "INVALID — the tamper matched 0 time(s)"   ->   exit 0

Twice in one session a REAL proof went INVALID because its anchor had **rotted** — once on a line
my own refactor had deleted. Both printed the word and exited 0, so any hook or CI step calling
this would have recorded success. That is how inert proofs accumulate exactly where the static law
cannot see them. [[matches-once-can-still-prove-nothing]] [[exit-status-of-the-block]]

⚠ **UNPROVABLE is named and deliberately NOT failed.** It means the law was already red before the
tamper — a fact about the working tree, which the test suite is the organ to report. Failing it
here would make this tool red for something it did not find, and a tool that is red for somebody
else's reason is one you learn to ignore.

⚠ The decision lives in `prove_exit_code()` rather than inline in `main()` for one reason: a
decision you can only reach by building a sandbox is a decision nothing will ever test. This file
calls it with fixtures.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import heart2  # noqa: E402


class TestAnInertProofDoesNotExitZero(unittest.TestCase):
    def test_a_clean_set_still_succeeds(self):
        code, broken, idle = heart2.prove_exit_code({"a": heart2.PROVEN, "b": heart2.PROVEN})
        self.assertEqual(code, 0, "every proof demonstrated its law and this must not fail")
        self.assertEqual((broken, idle), ([], []))

    def test_a_blind_proof_fails(self):
        """The law stayed green through its own defeat. It is not a law."""
        code, broken, _ = heart2.prove_exit_code({"a": heart2.PROVEN, "b": heart2.BLIND})
        self.assertEqual(code, 1, "a BLIND proof reported success")
        self.assertEqual(broken, ["b"], "the failing gate must be NAMED, not merely counted")

    def test_an_INVALID_proof_fails(self):
        """The one that exited 0 until v3292, measured with a throwaway gate."""
        code, broken, _ = heart2.prove_exit_code({"a": heart2.PROVEN, "b": heart2.INVALID})
        self.assertEqual(code, 1,
                         "an INVALID proof matched nothing, changed no byte and demonstrated "
                         "nothing - reporting success for it is how inert proofs pile up")
        self.assertEqual(broken, ["b"])

    def test_UNPROVABLE_is_named_but_not_failed(self):
        """Deliberate: that is the suite's finding, not this tool's."""
        code, broken, idle = heart2.prove_exit_code({"a": heart2.PROVEN, "b": heart2.UNPROVABLE})
        self.assertEqual(code, 0,
                         "UNPROVABLE means the tree was already red; failing here makes this tool "
                         "red for a reason it did not find, which teaches people to ignore it")
        self.assertEqual(broken, [], "UNPROVABLE must not be counted as a broken proof")
        self.assertEqual(idle, ["b"], "but it must still be NAMED - silence would hide it")

    def test_a_mixed_set_separates_the_two(self):
        code, broken, idle = heart2.prove_exit_code({"a": heart2.INVALID, "b": heart2.UNPROVABLE})
        self.assertEqual(code, 1)
        self.assertEqual(broken, ["a"], "the inert proof is the failure")
        self.assertEqual(idle, ["b"], "the already-red law is reported separately")

    def test_an_empty_run_is_not_a_pass_or_a_failure(self):
        """prove() returns {} when nothing declared a proof - that is the BACKLOG, and this
        function must not invent a verdict about it either way."""
        code, broken, idle = heart2.prove_exit_code({})
        self.assertEqual((code, broken, idle), (0, [], []))


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "dropping INVALID restores the exit-0 that let an inert proof read as success",
        "file": "tv/heart2.py",
        "find": "    broken = sorted(n for n, v in (results or {}).items() if v in (BLIND, INVALID))",
        "replace": "    broken = sorted(n for n, v in (results or {}).items() if v in (BLIND,))",
        "matches": 1,
    },
    {
        "why": "failing UNPROVABLE makes the tool red for the suite's reason, not its own",
        "file": "tv/heart2.py",
        "find": "    idle = sorted(n for n, v in (results or {}).items() if v == UNPROVABLE)",
        "replace": "    idle = []",
        "matches": 1,
    },
    {
        "why": "an exit code that is always 0 is the defect this whole file exists to remove",
        "file": "tv/heart2.py",
        "find": "    return (1 if broken else 0), broken, idle",
        "replace": "    return 0, broken, idle",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
