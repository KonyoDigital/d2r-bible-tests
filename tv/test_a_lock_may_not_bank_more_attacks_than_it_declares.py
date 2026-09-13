# -*- coding: utf-8 -*-
"""A SOURCE MAY NOT BANK MORE ATTACKS THAN IT DECLARES — the arithmetic his vault rests on.

`self_arming.score()` clears a bar on `wilson_lower(min(k, attacks), attacks)`. The bound is
computed on DISTINCT ATTACKS, never on raw attempts, because Wilson tightens with n and cannot
tell 83 independent looks from one attack applied 83 times. A row that overstates `attacks` buys
a lock open on refusals nobody earned — and on 2026-09-13 exactly that arithmetic took
`vault.apply` from locked to OPEN at 10 of 10.

⚠⚠ PER SOURCE, NEVER PER LOCK, and that distinction cost three wrong measurements. MEASURED:
`reel.route` carries 34 banked sabotage attacks against a harness declaring 7 — apparent 5x
inflation in a HARDENED lock. It is not:

    reel.route = 7 from reel_router_wilson (one per CLAIM) + 27 from rung_accounting_wilson

Two harnesses bank for one lock. A per-lock comparison would have flagged healthy locks as
fraudulent, which is the most damaging false alarm available here.
[[feedback-suspect-the-instrument]]

⚠ AN UNREADABLE DECLARATION IS UNKNOWN, NEVER A VIOLATION. Some harnesses declare their attacks in
a shape this reader cannot count; "I cannot check" must never render as "it cheated".
[[unknown-stays-unknown]]
"""
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


class TestALockMayNotBankMoreAttacksThanItDeclares(unittest.TestCase):

    def test_no_source_overclaims_on_the_live_queue(self):
        import lock_evidence_corroborate as LE
        c = LE.corroborate()
        over = [r for r in c["rows"] if r["verdict"] == "OVERCLAIM"]
        print("sources checked: %d · AGREE %d · UNKNOWN %d · OVERCLAIM %d"
              % (c["checked"], c["checked"] - c["unknown"] - c["overclaimed"],
                 c["unknown"], c["overclaimed"]))
        self.assertGreater(c["checked"], 0,
                           "0 sources checked is UNMEASURED, not clean — the queue was unreadable "
                           "or no lock in scope carries evidence")
        self.assertEqual([], [(r["src"], r["lock"], r["banked"], r["declared"]) for r in over],
                         "a source banking more attacks than it declares buys its lock open")

    def test_an_overclaim_is_caught(self):
        """The refusal, on a fixture — a green organ nobody has seen refuse measures nothing."""
        import lock_evidence_corroborate as LE
        real = LE._declared
        try:
            LE._declared = lambda src: 2            # every harness declares only 2
            c = LE.corroborate()
        finally:
            LE._declared = real
        print("with every declaration forced to 2 -> overclaimed=%d of %d"
              % (c["overclaimed"], c["checked"]))
        self.assertGreater(c["overclaimed"], 0,
                           "forcing declarations below the banked counts MUST produce refusals")

    def test_an_unreadable_declaration_is_unknown_not_a_violation(self):
        import lock_evidence_corroborate as LE
        real = LE._declared
        try:
            LE._declared = lambda src: None
            c = LE.corroborate()
        finally:
            LE._declared = real
        print("with no declaration readable -> unknown=%d overclaimed=%d"
              % (c["unknown"], c["overclaimed"]))
        self.assertEqual(0, c["overclaimed"],
                         "a harness this reader cannot count must never be called a cheat")
        self.assertEqual(c["checked"], c["unknown"])

    def test_the_comparison_is_per_source(self):
        """The bug this law was nearly built with: two harnesses bank for one lock."""
        import lock_evidence_corroborate as LE
        c = LE.corroborate({"reel.route"})
        srcs = sorted({r["src"] for r in c["rows"]})
        print("sources banking for reel.route: %d -> %s" % (len(srcs), srcs))
        self.assertGreater(len(srcs), 1,
                           "reel.route is fed by MORE THAN ONE harness; if that ever stops being "
                           "true, re-derive this law rather than assuming a per-lock total is safe")
        for r in c["rows"]:
            self.assertIn("src", r, "every row must name WHICH harness banked it")

    def test_folded_evidence_not_raw_history(self):
        """Raw _rows() double-counts a harness's own history and makes every lock 'disagree'."""
        import io
        src = io.open(os.path.join(HERE, "lock_evidence_corroborate.py"), encoding="utf-8").read()
        import re
        code = re.sub(r"#[^\n]*", "", src)
        self.assertIn("_fold(", code,
                      "the comparison must run on FOLDED evidence, as score() does — summing raw "
                      "rows counts history twice")
        print("uses _fold(): yes")


RED_PROOF = [
    {
        "why": "an overclaiming source stops being caught, so a lock can be bought open on more "
               "distinct attacks than any harness ever ran",
        "file": "lock_evidence_corroborate.py",
        "find": "        elif n > dec:",
        "replace": "        elif False:",
        "matches": 1,
    },
    {
        "why": "an unreadable declaration is treated as zero rather than UNKNOWN, so every "
               "harness this reader cannot count is reported as a cheat",
        "file": "lock_evidence_corroborate.py",
        "find": "        if dec is None:",
        "replace": "        if False:",
        "matches": 1,
    },
    {
        "why": "the comparison runs on raw history instead of folded evidence, double-counting "
               "every harness's own past and making healthy locks read as inflated",
        "file": "lock_evidence_corroborate.py",
        "find": "        for r in SA._fold([x for x in rows if x.get(\"lock\") == lock]):",
        "replace": "        for r in [x for x in rows if x.get(\"lock\") == lock]:",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
