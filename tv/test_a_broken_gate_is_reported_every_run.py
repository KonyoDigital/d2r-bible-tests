# -*- coding: utf-8 -*-
"""THE STASH GATE'S BREAKAGES REACH A HUMAN — EVERY RUN, NOT JUST THE FIRST.

`gate_failures()` was one of the 26 verdict-shaped functions with no caller. Its own docstring
promises *"the count is kept so a status surface can report it"* — and no surface ever did. The
only human channel was a ONE-SHOT print at the first break, so every breakage after the first was
invisible for the lifetime of the process. A counter with a stated consumer and no consumer is
[[plumbing-with-no-tap]].

⚠⚠ AND THE OBVIOUS JOIN IS THE WRONG JOIN, WHICH IS WHY THIS PINS A DELTA.
`_GATE_BROKE` is a module global and the console runs chronicle and vault sweeps on OTHER THREADS
that move it. Its own comment records the trap: *"every reader of them asks the same question the
same wrong way: snapshot before the call, snapshot after, treat any movement as 'this frame was
blind'. That works alone and is false in the console."* So this may only ever be a RUN-level fact,
never a per-frame one.

⚠ AND IT MAY NOT BE THE LIFETIME VALUE EITHER. The sibling report beside it carries the scar in
its own words: *"a run-level claim built on a lifetime counter — the same defect this whole arc
keeps finding, written by me into the fix for it. Deltas now."* A lifetime count printed as a run
claim reads as "it broke 14 times during this sweep" when 13 of those were yesterday.
[[unknown-stays-unknown]] [[label-outlived-referent]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

SRC = os.path.join(HERE, "control_app.py")


def _code():
    with io.open(SRC, encoding="utf-8") as fh:
        s = fh.read()
    s = re.sub(r"(?m)^\s*#.*$", " ", s)          # prose is not evidence about code
    return s


class ABrokenGateIsReportedEveryRun(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.code = _code()

    def test_the_run_snapshots_the_break_count(self):
        self.assertIn("_gbroke0 = gate_failures()", self.code,
                      "the run no longer snapshots gate_failures() at its start, so it cannot "
                      "report a delta and the counter goes back to having no consumer")

    def test_it_reports_a_DELTA_not_the_lifetime_count(self):
        """the scar the sibling report already carries."""
        self.assertIn("_gb = gate_failures() - _gbroke0", self.code,
                      "the break count is being reported without subtracting the run's start — a "
                      "run-level claim built on a lifetime counter, which is the defect this whole "
                      "arc keeps finding")

    def test_the_delta_is_what_gates_the_message(self):
        i = self.code.find("_gb = gate_failures() - _gbroke0")
        self.assertGreater(i, 0)
        window = self.code[i:i + 400]
        self.assertIn("if _gb:", window,
                      "the message is not gated on the delta, so a quiet run would print a "
                      "breakage line about breakages that happened before it started")

    def test_it_says_a_THROW_is_not_a_VERDICT(self):
        """[[zero-needs-a-denominator]] — a frame the gate threw on was NOT judged, and reporting
        it as a refusal would turn an absence of measurement into a negative verdict."""
        i = self.code.find("the stash gate BROKE")
        self.assertGreater(i, 0, "the breakage line is gone")
        window = self.code[i:i + 320]
        self.assertIn("not judged", window,
                      "the line reports a count without saying those frames were NOT JUDGED — a "
                      "gate that threw is not a gate that said no")

    def test_it_still_offers_the_lifetime_number(self):
        """the run figure answers 'now'; the lifetime answers 'is this chronic'. Both, or the
        reader cannot tell one bad sweep from a dying lane."""
        i = self.code.find("the stash gate BROKE")
        window = self.code[i:i + 400]
        # ⚠ the phrase is SPLIT across two string literals by line-wrapping ("The lifetime " +
        # "count is %d."), so a contiguous search for it fails on correct code. Anchor on the
        # word that survives the wrap. [[source-reading-guard]]
        self.assertIn("lifetime", window,
                      "the run delta is printed with no lifetime figure beside it, so a single "
                      "bad run and a chronically broken gate read identically")

    def test_gate_failures_still_refuses_to_mean_unknown(self):
        """its docstring's own promise: '0 means it ran; it never means unknown'."""
        with io.open(SRC, encoding="utf-8") as fh:
            raw = fh.read()
        i = raw.find("def gate_failures():")
        self.assertGreater(i, 0)
        self.assertIn("never means", raw[i:i + 260],
                      "gate_failures lost the docstring line separating a measured zero from an "
                      "unasked question")


RED_PROOF = [
    ("control_app.py", "_gb = gate_failures() - _gbroke0", "_gb = gate_failures()",
     "test_it_reports_a_DELTA_not_the_lifetime_count"),
    ("control_app.py", "        _gbroke0 = gate_failures()", "        _gbroke0X = gate_failures()",
     "test_the_run_snapshots_the_break_count"),
    ("control_app.py", "not judged, and a gate that threw", "counted, and a gate that threw",
     "test_it_says_a_THROW_is_not_a_VERDICT"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
