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
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: E402  — this file prints ♥ 🕳 ⚠ ★
console_safe.enable()

import heart2 as H  # noqa: E402


RED_PROOF = [
    {
        "why": "switching off the skip branch returns the BLIND line to one sentence for two "
               "opposite states — a law that was never run reads exactly like a law that was run "
               "and survived, which is how v2865 shipped blind:1 without anyone knowing why",
        "file": "heart2.py",
        "find": "    if _m and int(_m.group(1)):",
        "replace": "    if False and _m and int(_m.group(1)):",
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
