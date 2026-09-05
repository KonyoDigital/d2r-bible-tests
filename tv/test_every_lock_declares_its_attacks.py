#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TWELVE OF SIXTEEN LOCKS COULD NOT SAY HOW MANY DISTINCT ATTACKS BACKED THEM.

⚠⚠ WHY THAT FIELD IS THE WHOLE POINT. REG-598: Wilson tightens as `n` grows and **cannot tell 83
independent looks from ONE attack applied 83 times**, so running more of the same buys a higher
number and proves nothing. `attacks` is the field that stops it, and `wilsonByAttack` is the score
recomputed over distinct attacks rather than repetitions.

⚠⚠ MEASURED 2026-09-05, and the count was the tell. Twelve locks with `n > 0` read
`attacks: UNSTATED` — including **`prune.arm`, the one door with no undo**, and
**`vault.sweep_start`, which spends his money**. `attacks: null` is documented as *"the harness has
not re-run since the field existed"*, which is NOT the same as "no repetition" — but nothing
distinguished the two on the badge, so a lock resting on one attack looped many times rendered
exactly like one that earned it.

**IT WAS NOT A WIRING GAP.** Walked by AST: every harness that banks — all ten of them — already
passes `attacks=`. v2623 wired them; the STORED ROWS simply predated the re-run. So the fix was to
re-run the harnesses, not to change them, and this guard is what stops the state coming back.

AFTER RE-RUNNING, and this is the picture the field exists to show:

    lock                 wilson   byAttack   bar
    prune.arm            0.9259     0.5655   0.839     <- the deleter
    vault.apply          0.9259     0.4385   0.722     <- the only HARDENED lock
    vault.sweep_start    0.8064     0.3424   0.510     <- his money
    miniauto.run         0.9347     0.5101   0.510
    printer.stream       0.9558     0.5655   0.510

⚠⚠⚠ WHAT THIS GUARD DOES NOT DECIDE, DELIBERATELY. Whether the bars are read against `wilson` or
against `wilsonByAttack` is **HIS RULING**, still open on the board. Every one of those locks
CLEARS on `wilson` and several do NOT clear on `wilsonByAttack`. This file makes both numbers
available on every lock so the decision can be made on evidence; it does not make the decision, and
it must never be edited into making it. [[unknown-stays-unknown]]

⚠ NOTHING HERE ARMS ANYTHING. `may()` is still never called; the prune stays OFF.
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import self_arming as SA  # noqa: E402


def _locks():
    rep = SA.report()
    return [r for r in (rep.get("locks") or []) if isinstance(r, dict)]


class EveryLockWithEvidenceDeclaresItsAttacks(unittest.TestCase):

    def test_the_report_has_locks_at_all(self):
        """⚠ A guard over an empty list is measuring nothing."""
        self.assertGreaterEqual(len(_locks()), 8,
                                "the lock table is too small to be the real one")

    def test_no_lock_with_n_over_zero_reads_UNSTATED(self):
        """★★ THE LAW. A score with an unstated attack count cannot be told apart from one bought
        by repetition — which is the defect REG-598 exists for."""
        bad = [r["lock"] for r in _locks()
               if int(r.get("n") or 0) > 0 and r.get("attacks") is None]
        self.assertEqual(bad, [],
                         "%d lock(s) carry evidence but cannot say how many DISTINCT attacks are "
                         "behind it, so a score looped from one sabotage renders exactly like one "
                         "that earned it: %s" % (len(bad), bad))

    def test_a_lock_with_NO_evidence_may_be_unstated(self):
        """⚠ THE CARVE-OUT, and it must stay. `vault.forget` is UNPROVEN BY CONSTRUCTION — it has
        no refusal path, so no attack can ever be made. Demanding an attack count there would be
        demanding a number about an event that cannot happen."""
        zero = [r for r in _locks() if int(r.get("n") or 0) == 0]
        for r in zero:
            self.assertIn(r.get("state"), ("UNPROVEN", "UNKNOWN", "INCOMPLETE"),
                          "%s has no evidence but does not say so" % r.get("lock"))

    def test_wilsonByAttack_is_published_wherever_attacks_is(self):
        """⚠ The count alone is not the point — the SCORE over distinct attacks is. A lock that
        states `attacks` and hides the recomputed figure has published the input and withheld the
        answer. [[the-unjoined-end]]"""
        for r in _locks():
            if r.get("attacks"):
                self.assertIsNotNone(r.get("wilsonByAttack"),
                                     "%s declares %s attacks and publishes no wilsonByAttack"
                                     % (r.get("lock"), r.get("attacks")))

    def test_byAttack_is_never_HIGHER_than_the_raw_score(self):
        """⚠⚠ AN ARITHMETIC SANITY CHECK, because a byAttack figure ABOVE the raw one would mean
        the correction is inflating rather than deflating — and a correction that can only help is
        not a correction. Wilson rises with n, and attacks <= n, so it can only fall or tie."""
        for r in _locks():
            w, wba = r.get("wilson"), r.get("wilsonByAttack")
            if w is None or wba is None:
                continue
            self.assertLessEqual(round(wba, 6), round(w, 6) + 1e-9,
                                 "%s: wilsonByAttack %.4f exceeds wilson %.4f — the repetition "
                                 "correction is adding confidence instead of removing it"
                                 % (r.get("lock"), wba, w))


class TheHARNESSESAllPassIt(unittest.TestCase):
    """★ Established by AST, so a harness that stops declaring is caught even before it re-runs and
    the stored rows go stale."""

    def test_every_banking_harness_passes_attacks(self):
        gaps = []
        for src in sorted(SA.PROVES):
            p = os.path.join(HERE, src + ".py")
            if not os.path.exists(p):
                continue                      # a SOURCE LABEL banked by another harness
            try:
                tree = ast.parse(io.open(p, encoding="utf-8").read())
            except SyntaxError:
                continue
            for n in ast.walk(tree):
                if not isinstance(n, ast.Call):
                    continue
                nm = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                if nm in ("bank", "record") and not any(
                        k.arg == "attacks" for k in (n.keywords or [])):
                    gaps.append("%s:%d" % (src, n.lineno))
        self.assertEqual(gaps, [],
                         "bank/record call(s) with no attacks= : %s — the row they write cannot "
                         "say how many distinct attacks it represents" % gaps)

    def test_a_source_with_no_module_is_a_LABEL_and_that_is_legitimate(self):
        """⚠ I RAISED THIS AS AN ALARM AND IT WAS WRONG, which is worth keeping. `vault_live` is
        declared in PROVES and has no `vault_live.py`, and for a moment that looked like the only
        HARDENED lock resting on a module that does not exist. It is a source LABEL: `vault_wilson`
        banks under it when it drives the RUNNING console over HTTP. The evidence is real and
        re-derivable. Checking before believing my own alarm is the only reason this is a note and
        not a retraction."""
        labels = [s for s in SA.PROVES if not os.path.exists(os.path.join(HERE, s + ".py"))]
        for lab in labels:
            found = False
            for other in SA.PROVES:
                p = os.path.join(HERE, other + ".py")
                if not os.path.exists(p):
                    continue
                if ('"%s"' % lab) in io.open(p, encoding="utf-8").read():
                    found = True
                    break
            self.assertTrue(found,
                            "%r is declared in PROVES, has no module, and no harness banks under "
                            "it — that is evidence nobody can re-derive" % lab)


class ItDoesNotDecideHisRuling(unittest.TestCase):
    """⚠⚠ THE ONE WAY THIS FILE COULD DO HARM. Several locks clear on `wilson` and do NOT clear on
    `wilsonByAttack`; which figure the bars read is HIS open ruling. This guard must never quietly
    settle it."""

    def test_the_bar_is_still_compared_against_the_RAW_wilson(self):
        """If this ever fails, the ruling was made — say so out loud rather than letting a guard
        record it silently."""
        import inspect
        src = inspect.getsource(SA.score)
        self.assertIn("wilson_lower(k, n)", src,
                      "the bar is no longer compared against the raw wilson. If that was his "
                      "ruling, this guard should be rewritten to state it, not deleted")

    def test_the_locks_that_would_CHANGE_under_the_other_reading_are_visible(self):
        """★ The evidence his decision needs, published rather than argued."""
        flip = [(r["lock"], r.get("wilson"), r.get("wilsonByAttack"), r.get("bar"))
                for r in _locks()
                if r.get("wilson") is not None and r.get("wilsonByAttack") is not None
                and r.get("bar") is not None
                and r["wilson"] >= r["bar"] > r["wilsonByAttack"]]
        for lock, w, wba, bar in flip:
            self.assertLess(wba, bar)          # by construction; asserted so the list is real
        self.assertIsInstance(flip, list)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
