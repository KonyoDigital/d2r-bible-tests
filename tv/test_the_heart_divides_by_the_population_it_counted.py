# -*- coding: utf-8 -*-
"""v3318 — THE HEART DIVIDES BY THE POPULATION ITS NUMERATOR CAME FROM.

`self_arming._heart_says_watched()` printed *"instruments watched: 394 of 457 gates proved"*.
`proved` counts gates that DECLARE a red-proof and were proven; `total` counts every registered
gate, including those that declare none. One numerator, a different denominator.

MEASURED 2026-09-18, counted independently from `run_gates.GATES` and the test files themselves:

    gates registered                     457    == the store's `total`
    gates whose file declares RED_PROOF  417    == the store's `declared`
    gates PROVEN                         394    == the store's `proved`

        394 / 457 = 86.2%   what it printed
        394 / 417 = 94.5%   what is true of the population 394 came from

⚠ IT UNDER-STATED, which is the safe direction and exactly why it would have survived: a number
that looks worse than reality never gets challenged.

⚠⚠ AND THE REAL LOSS WAS THE 40. Forty registered gates declare NO red-proof at all — gates that
have never been SEEN to refuse, which is the one thing this repo treats as measuring nothing.
Folding them into a denominator turns "we have not proven these" into "we proved a smaller
fraction", a far less actionable sentence. They now get their own clause.

⚠ ONE FACT, TWO READERS, AND ONLY ONE WAS WRONG. `control_app.py:19460` has printed it correctly
all along — *"N of <declared> gate(s) can still go red; M carry no executable proof and are
UNKNOWN"*. The store already persisted `declared`, `total` and `unproven`; nothing new had to be
computed. Only the consumer was wrong. [[copy-drift]] [[zero-needs-a-denominator]]

⚠ THE NO-PROOF COUNT IS OMITTED, NEVER ZEROED, when either figure is missing. A census that
cannot say how many gates exist must not be made to say "0 declare no proof" — that is a
manufactured clean. [[unknown-stays-unknown]]
"""
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Its docstrings and failure messages carry non-ASCII, and a unittest failure PRINTS them. On a
# cp1255 console that crash happens while REPORTING, so a clean tree exits non-zero for a reason
# that has nothing to do with the law. Caught by test_control's encoding-safety gate.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import heart2 as H            # noqa: E402
import self_arming as SA      # noqa: E402


def _census(**over):
    """A census the staleness check will accept, so the sentence below is actually reached.

    The fingerprint must be the LIVE one: `_heart_says_watched` refuses a stale census before it
    ever composes its sentence, so a fixture with a stale print would test the refusal path and
    silently prove nothing about the arithmetic. [[matches-once-can-still-prove-nothing]]
    """
    d = {"proved": 394, "declared": 417, "total": 457, "blind": [],
         "gatesFingerprint": H.gates_fingerprint(), "partial": True}
    d.update(over)
    return d


def _say(**over):
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with io.open(path, "w", encoding="utf-8") as _fh:
        _fh.write(json.dumps(_census(**over)))
    old = os.environ.get("TV_HEART_CENSUS")
    try:
        os.environ["TV_HEART_CENSUS"] = path
        return SA._heart_says_watched()
    finally:
        if old is None:
            os.environ.pop("TV_HEART_CENSUS", None)
        else:
            os.environ["TV_HEART_CENSUS"] = old
        os.unlink(path)


class TestTheHeartDividesByThePopulationItCounted(unittest.TestCase):

    def test_the_denominator_is_the_population_the_numerator_came_from(self):
        ok, why = _say()
        self.assertTrue(ok, "the fixture census was refused before the sentence was composed, so "
                            "this case proves nothing about the arithmetic: %s" % why)
        self.assertIn(
            "394 of 417", why,
            "the heart still divides the proved-count by a different population. 394 counts gates "
            "that DECLARE a proof and were proven; 457 counts every gate. Said:\n  %s" % why)
        self.assertNotIn(
            "394 of 457", why,
            "the all-gates denominator is still being printed (86.2%% where 94.5%% is true of the "
            "population 394 came from). Said:\n  %s" % why)

    def test_the_gates_that_declare_no_proof_are_NAMED_not_absorbed(self):
        ok, why = _say()
        self.assertIn(
            "40 of 457", why,
            "the 40 gates that declare no executable proof are not named — they are still hidden "
            "inside a denominator. A gate never seen red is measuring nothing, and that is the "
            "actionable half of this sentence. Said:\n  %s" % why)
        self.assertIn(
            "never been seen to refuse", why,
            "the count is there but not what it MEANS. A bare number nobody can act on is the "
            "thing this repo keeps re-learning to avoid. Said:\n  %s" % why)

    def test_a_census_that_cannot_say_omits_the_clause_rather_than_zeroing_it(self):
        """⚠ UNKNOWN, never a manufactured clean."""
        ok, why = _say(declared=None)
        self.assertNotIn(
            "declare NO executable proof", why,
            "with `declared` missing, the heart still published a no-proof count. It cannot know "
            "one — and '0 declare no proof' is the most reassuring possible lie. Said:\n  %s" % why)

    def test_the_two_sentences_agree_when_every_gate_declares_a_proof(self):
        """BASELINE. Without it, a hardcoded '394 of 417' would pass the first case."""
        ok, why = _say(proved=457, declared=457, total=457)
        self.assertIn(
            "457 of 457", why,
            "with every gate declaring a proof the two populations coincide and the sentence must "
            "say so; it did not, so the first case may be reading a constant. Said:\n  %s" % why)
        self.assertIn(
            "0 of 457", why,
            "with declared == total, exactly 0 gates declare no proof, and the clause must say "
            "that MEASURED zero rather than vanishing. Said:\n  %s" % why)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "dividing by every gate puts a numerator over a population it did not come from",
        "file": "tv/self_arming.py",
        "find": '                  % (_proved, _decl,',
        "replace": '                  % (_proved, _tot,',
        "matches": 1,
    },
    {
        "why": "dropping the clause hides the 40 gates that have never been seen to refuse",
        "file": "tv/self_arming.py",
        "find": '                     ("" if _noproof is None else',
        "replace": '                     ("" if True else',
        "matches": 1,
    },
    {
        "why": "a census that cannot say how many gates exist must not publish a reassuring zero",
        "file": "tv/self_arming.py",
        "find": '    _noproof = ((_tot - _decl) if isinstance(_tot, int) and isinstance(_decl, int) else None)',
        "replace": '    _noproof = ((_tot - _decl) if isinstance(_tot, int) and isinstance(_decl, int) else 0)',
        "matches": 1,
    },
]
