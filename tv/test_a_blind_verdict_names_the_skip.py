#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""♥🕳 A SKIPPED LAW IS NOT A WEAK LAW, AND THE BLIND LINE MUST SAY WHICH IT IS.

MEASURED 2026-09-09, on my own instrument. `python3 heart2.py --prove` reported

    test_the_lock_derives_from_the_heart[1]   BLIND ← stayed GREEN through its own defeat

and v2865 shipped a census carrying `blind: 1` on that name. The law was not weak. `.heart2.json`
is gitignored, so `safe_copy` never puts it in a sandbox, so the law called `self.skipTest()` and
the tampered run printed `OK (skipped=5)` — green because NOTHING RAN. The verdict line said
"stayed GREEN through its own defeat" about a law that never reached its defeat.

Those two states need opposite work: a real BLIND wants a stronger law; a skipped one wants the law
to stop opting out. The line reporting them said the same words about both, and the tail carrying
the answer (`OK (skipped=5)`) was already in the function's hands and thrown away.

⚠ THE DENOMINATOR RULE, ON A VERDICT INSTEAD OF A NUMBER. "Green" with nothing behind it is the
same defect as a `0` with no denominator. [[zero-needs-a-denominator]] [[unknown-stays-unknown]]

MEASURED after the fix:
    tail 'OK (skipped=5)' -> "⚠ but 5 law(s) SKIPPED in the sandbox … may never have been judged"
    tail 'OK'             -> the plain sentence, unchanged
    tail 'OK (skipped=0)' -> the plain sentence (zero skips is not a skip)
"""
import ast
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: E402  — this file prints ♥ 🕳 ⚠ ★
console_safe.enable()

import heart2 as H  # noqa: E402


RED_PROOF = [
    {
        "why": "switching off the skip branch returns the BLIND line to one sentence for opposite "
               "states — a law that was never run reads exactly like a law that was run and "
               "survived, which is how v2865 shipped blind:1 without anyone knowing why",
        "file": "heart2.py",
        "find": "    if not n_skipped:\n        return _base",
        "replace": "    if True:\n        return _base",
        "matches": 1,
    },
    {
        "why": "un-joining the helper from the only place it is called: the reason text can be "
               "perfect and the prover still print the old sentence. Plumbing with no tap",
        "file": "heart2.py",
        "find": 'say("     %-52s %s ← %s" % (label, BLIND, blind_reason(pr.get("why"), got, tail2)))',
        "replace": 'say("     %-52s %s ← stayed GREEN" % (label, BLIND))',
        "matches": 1,
    },
    {
        "why": "v2870's defect: collapsing a MIXED run into a total one. Five laws skipping while "
               "three run and stay green is a WEAK LAW, and this branch would send the reader to "
               "delete skips while the three that judged the tamper stay blind",
        "file": "heart2.py",
        "find": "    if n_skipped >= n_ran:",
        "replace": "    if True:",
        "matches": 1,
    },
    {
        "why": "throwing away the DENOMINATOR at the source: without unittest's `Ran N tests` line "
               "the helper cannot tell a whole-file skip from a partial one, and every skip reads "
               "as 'never judged'",
        "file": "heart2.py",
        "find": '        if _l.startswith("Ran ") and " test" in _l:',
        "replace": '        if False and _l.startswith("Ran ") and " test" in _l:',
        "matches": 1,
    },
]


def _prove_one_src():
    """The source of _prove_one, sliced by AST so no fixed-size window can read past it.
    [[source-reading-guard]] [[source-window-shortcut]]"""
    src = io.open(os.path.join(HERE, "heart2.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_prove_one":
            return ast.get_source_segment(src, node) or ""
    return ""


class ABlindVerdictNamesTheSkip(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_a_tampered_run_that_SKIPPED_says_so(self):
        """★★ The whole finding. 5 skips must reach the person reading the verdict."""
        out = H.blind_reason("some why", 2, "OK (skipped=5)")
        self.assertIn("SKIP", out.upper(),
                      "a tampered run that skipped its laws reads exactly like one that ran them "
                      "and survived — the two need opposite fixes")
        self.assertIn("5", out, "the skip COUNT is the measurement; a word without it is prose")

    def test_a_run_with_NO_skips_does_not_claim_any(self):
        """★★ The other half: unconditional prose would be a label that is always true."""
        out = H.blind_reason("some why", 2, "OK")
        self.assertNotIn("SKIP", out.upper(),
                         "the warning fires on a run with no skips at all, so it says nothing "
                         "about any particular run [[label-outlived-referent]]")

    def test_skipped_ZERO_is_not_a_skip(self):
        """★ unittest prints `skipped=0` on some paths; zero skipped laws is a full run."""
        out = H.blind_reason("some why", 2, "OK (skipped=0)")
        self.assertNotIn("SKIP", out.upper(),
                         "`skipped=0` was read as evidence of skipping — a truthy-string bug in "
                         "the very check written to stop a green from lying")

    def test_the_plain_sentence_survives(self):
        """★ The old text still carries the match count and the why; the warning is an addition."""
        out = H.blind_reason("the why text", 3, "OK")
        self.assertIn("3 match(es)", out)
        self.assertIn("the why text", out)

    def test_a_TOTAL_skip_says_the_tamper_was_never_judged(self):
        """★★ skipped == ran: nothing judged anything. The skip is the whole job."""
        out = H.blind_reason("some why", 2, "Ran 5 tests in 0.1s | OK (skipped=5)")
        self.assertIn("ALL 5", out)
        self.assertIn("never judged", out)

    def test_a_MIXED_run_says_the_law_is_WEAK_TOO(self):
        """★★ v2870 — THE DENOMINATOR. A cross-family review of v2868: five laws skipping while
        three RUN and stay green is a weak law, and the old sentence — 'the tamper may never have
        been judged at all, fix the SKIP before calling the law weak' — sent the reader to delete
        skips while the three laws that actually judged the tamper stayed blind. A numerator with
        no denominator, shipped inside the fix for exactly that scar.
        [[zero-needs-a-denominator]]"""
        out = H.blind_reason("some why", 2, "Ran 8 tests in 0.1s | OK (skipped=5)")
        self.assertIn("5 of 8", out, "the skip count is printed without the total that makes it "
                                     "mean anything")
        self.assertIn("3 DID run", out,
                      "a mixed run does not say that laws ran and survived — so it reads as "
                      "'nothing was judged' when the law is genuinely weak")
        self.assertNotIn("never judged", out,
                         "a mixed run is told the tamper was never judged, which is false for the "
                         "laws that ran")

    def test_a_tail_with_NO_denominator_says_UNKNOWN(self):
        """★ No `Ran N` line: whether the tamper was judged is UNKNOWN, not 'never'."""
        out = H.blind_reason("some why", 2, "OK (skipped=5)")
        self.assertIn("UNKNOWN", out)
        self.assertNotIn("ALL 5", out)

    def test_the_RUNNER_actually_carries_the_denominator(self):
        """★★ [[the-unjoined-end]] — behavioural, not a string check: run a real gate file through
        `_run_gate` and require unittest's `Ran N tests` line to survive into the tail. The helper
        can divide perfectly and still be handed nothing to divide by."""
        d = tempfile.mkdtemp(prefix="ranline-")
        try:
            io.open(os.path.join(d, "t_x.py"), "w", encoding="utf-8").write(
                "import unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_a(self): pass\n"
                "    def test_b(self): self.skipTest('deliberate')\n"
                "unittest.main()\n")
            ok, tail = H._run_gate(d, "t_x.py", timeout=60)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        self.assertTrue(ok, "the fixture gate did not pass: %r" % tail)
        self.assertRegex(tail, r"Ran \d+ test",
                         "_run_gate discarded unittest's `Ran N tests` line, so blind_reason has "
                         "no denominator however well it divides: %r" % tail)
        self.assertIn("skipped=1", tail, "the skip count did not survive either: %r" % tail)

    # ── the join: a reason nobody prints is not a reason ─────────────────────────────────────
    def test_the_PROVER_actually_calls_it(self):
        """★★ [[the-unjoined-end]] — parsed, not grepped: _prove_one must CALL blind_reason."""
        seg = _prove_one_src()
        self.assertTrue(seg, "_prove_one could not be located in heart2.py by AST")
        calls = [n.func.id for n in ast.walk(ast.parse(seg))
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        self.assertIn("blind_reason", calls,
                      "_prove_one never calls blind_reason — the helper is correct and unreachable, "
                      "which is the shape of every unjoined end this repo has shipped")

    def test_the_old_inline_sentence_is_GONE_from_the_prover(self):
        """★ Two texts for one verdict is how a fix stops taking without anything going red."""
        seg = _prove_one_src()
        self.assertNotIn("stayed GREEN through its own defeat", seg,
                         "_prove_one still holds its own copy of the BLIND sentence, so the "
                         "helper can be improved for ever and the prover keep printing the old "
                         "one [[copy-drift]]")


if __name__ == "__main__":
    unittest.main(verbosity=2)
