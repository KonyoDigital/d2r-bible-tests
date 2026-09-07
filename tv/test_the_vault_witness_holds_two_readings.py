# -*- coding: utf-8 -*-
"""I TOLD HIM THE VAULT'S WRITE PATH RE-GATES. ON THE BUTTON HE ACTUALLY PRESSES, IT DOES NOT.

Konyo: *"the vault accumalator that should be connected to the heart of the console with the vault
and joined obivously too"*.

`control_app.vault_apply`:
    caller_supplied = proposal is not None
    prop = proposal or (st.get("result") if isinstance(st.get("result"), dict) else None)
    if caller_supplied and isinstance(prop, dict):     <- the re-gate lives INSIDE this
and the console's button posts `body: '{}'`, deliberately — its own comment: *"NO BODY. Posting the
proposal back would hand the server a client-editable payload; the engine already holds the gated
result, and v1595 re-gates anything supplied from outside precisely because that door existed."*

The design is coherent — trust your own engine, guard the untrusted door — resting on ONE buried
assumption: **that the engine's stored result was gated under the law in force NOW.** It was not.
`vault_retro.merge_vault`/`_absorb` merge-max accumulated rows forever and never call `gate()`
again, so a row keeps whatever verdict it won under whatever bar was live the day it entered.

MEASURED on his own store, 2026-09-07: **6 of 7 stored OWNED rows could not clear the bar they were
displayed under.** Pressing "register 7" would have applied all seven. I had told him it would
refuse them. [[inherited_claim_is_not_evidence]] [[feedback-verify-not-proxy]]

His ruling unified the bar back to 2 the same day, so those seven are legitimate now — but the
STRUCTURAL hole is untouched: the next bar change recreates it exactly and nothing would say so.

⇒ THE PAIR, and it never averages them: [[feedback-contradiction-is-the-finding]]
    A  the stored claim — vault_accum.json's owned rows as they sit on disk
    B  the re-gate      — those rows' OWN witnesses through the REAL vault_retro.gate() at TODAY's
                          live constants
PROVEN AGAINST REALITY, not a fixture: at today's bar of 2 it reads AGREE (7/7); with the bar set
back to 3 it reads CONTRADICTION and names exactly the six rows that were wrong.

⛔ AGE IS CONTEXT, NEVER A VERDICT. His proposal lives on disk across restarts by design; 23 or 25
hours old is normal. A row that reddens on age is ignored within a week. [[stale-reading]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import vault_retro as VR  # noqa: E402
import vault_witness as VW  # noqa: E402

SRC = io.open(os.path.join(HERE, "vault_witness.py"), encoding="utf-8").read()


def _code_only(src):
    """Docstrings and comments stripped — written in from the start.
    Five laws this session were fooled by the prose explaining their own rule."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            b = getattr(node, "body", None) or []
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                b[0].value.value = ""
    import re
    out = ast.unparse(tree) if hasattr(ast, "unparse") else src
    return re.sub(r"(?m)#[^\n]*", "", out)


CODE = _code_only(SRC)


def _rows(*specs):
    """owned rows with N distinct sessions each."""
    return [{"name": nm, "witnesses": [{"session": "s%d" % i, "conf": 0.9} for i in range(n)]}
            for nm, n in specs]


class TheVaultWitnessHoldsTwoReadings(unittest.TestCase):

    # ── ⛔ IT READS ONLY ──────────────────────────────────────────────────────────────────────
    def test_it_never_sweeps_applies_or_prunes(self):
        """A witness that can act is not a witness. Checked in CODE, not prose."""
        for bad in ("vault_apply", "apply_plan", "sweep(", "_tombstone(", "prune"):
            self.assertNotIn(bad, CODE,
                             "vault_witness reaches for %r in code — it must only read" % bad)

    def test_it_uses_the_REAL_gate_and_the_REAL_bars(self):
        """A private copy of the witness rule would drift from the rule the write path enforces,
        and then this compares the ledger against a copy of the law rather than the law."""
        self.assertIn("VR.gate(", CODE, "it no longer calls vault_retro.gate")
        self.assertIn("VR.KEEP_CONF_FLOOR", CODE, "it no longer reads the live conf floor")
        self.assertIn("VR.KEEP_MIN_WITNESSES", CODE, "it no longer reads the live witness bar")

    # ── ⚠⚠ THE LAW: THE DISAGREEMENT IS THE FINDING ──────────────────────────────────────────
    def test_rows_that_fail_TODAYS_bar_are_a_CONTRADICTION(self):
        real = VW.stored
        VW.stored = lambda *a, **k: (_rows(("A", 2), ("B", 2), ("C", 9)), "")
        old = VR.KEEP_MIN_WITNESSES
        VR.KEEP_MIN_WITNESSES = 3
        try:
            v = VW.verdict()
            self.assertEqual("CONTRADICTION", v.get("state"))
            self.assertEqual(2, v.get("disagree"), "wrong count of failing rows")
            self.assertEqual(1, v.get("agree"))
            self.assertIn("applied AS-IS", v.get("why"),
                          "the message does not say the stored result is what actually lands, "
                          "which is the whole reason this matters")
        finally:
            VW.stored = real
            VR.KEEP_MIN_WITNESSES = old

    def test_rows_that_all_clear_are_AGREE(self):
        """The other direction. A row that can only go red is as useless as one that can only be
        green."""
        real = VW.stored
        VW.stored = lambda *a, **k: (_rows(("A", 4), ("B", 3)), "")
        try:
            self.assertEqual("AGREE", VW.verdict().get("state"))
        finally:
            VW.stored = real

    # ── ⛔ AGE MUST NOT BE THE VERDICT ────────────────────────────────────────────────────────
    def test_an_OLD_ledger_whose_rows_still_clear_is_AGREE(self):
        """His proposal lives on disk across restarts BY DESIGN. Reddening on age is the cry-wolf
        that gets the row ignored."""
        real = VW.stored
        VW.stored = lambda *a, **k: (_rows(("A", 5)), "")
        try:
            v = VW.verdict()
            self.assertEqual("AGREE", v.get("state"),
                             "age alone produced a fault verdict")
        finally:
            VW.stored = real
        self.assertNotIn("ageS >", CODE, "age is being compared to a threshold — it is context")

    # ── ⚠ UNKNOWN IS NEVER A CLEAN ZERO ──────────────────────────────────────────────────────
    def test_a_missing_ledger_is_UNKNOWN_not_zero_owned(self):
        rows, why = VW.stored(path=os.path.join(HERE, "__no_such_vault_accum__.json"))
        self.assertIsNone(rows, "a missing ledger returned a row list")
        self.assertIn("NOT the same", why,
                      "the reason does not distinguish 'no sweep here' from 'a sweep found nothing'")

    def test_an_EMPTY_ledger_is_measured_AGREE_not_unknown(self):
        """The other half: a ledger that IS present and holds no owned rows is a measurement."""
        real = VW.stored
        VW.stored = lambda *a, **k: ([], "")
        try:
            v = VW.verdict()
            self.assertEqual("AGREE", v.get("state"))
            self.assertEqual(0, v.get("n"))
            self.assertIn("measured, not unknown", v.get("why"))
        finally:
            VW.stored = real

    def test_a_gate_that_RAISES_is_UNKNOWN_never_a_failure(self):
        """A crashing check is not a verdict about his data."""
        real = VR.gate
        VR.gate = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("simulated"))
        rs = VW.stored
        VW.stored = lambda *a, **k: (_rows(("A", 2)), "")
        try:
            v = VW.verdict()
            self.assertEqual("UNKNOWN", v.get("state"),
                             "a raising gate was reported as a finding about his vault")
        finally:
            VR.gate = real
            VW.stored = rs

    def test_it_still_parses(self):
        ast.parse(SRC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
