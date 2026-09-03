# -*- coding: utf-8 -*-
"""A zero taken through a filter that rejects every input measures the filter.

⚠⚠ THIS IS THE THIRD TIME THIS WEEK, WHICH IS WHY IT IS A GUARD AND NOT A COMMENT. v2493 read 0
joinable pairs as "different kinds of thing" (wrong — the resolver's reach). v2495 read a fallback
list I had typed as a fact about his console. Here the contradiction A4 was born from returns 0 —
and the cause is that NOT ONE of the 30 seals satisfies the extraction contract, so no reel can be
judged disposable and the contradiction cannot arise at all.

Reported as CLEAN, that zero would say "the printer's routing is sound". It says nothing of the
kind. [[unknown-stays-unknown]]

⚠ The subjects here are CONSTRUCTED. A guard that can only fire while his stores happen to contain
an example is blind the moment they do not — and "there are no contradictions" is exactly when that
blindness arrives. [[gate-blind-to-unexercised-input]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import frame_authority as FA   # noqa: E402
import printer_reach as PR     # noqa: E402


def _full_seal(**kw):
    """A seal that DOES satisfy the contract, built from the contract itself, never typed."""
    row = {"ts": 1, "rows": 1, "promptVer": "vpX", "extracted": list(FA.EXTRACTION_CONTRACT)}
    row.update(kw)
    return row


class AZeroMustEarnTheWordClean(unittest.TestCase):

    def _run(self, triage, seals):
        real_t, real_s = PR._triage, FA.sealed_sessions
        try:
            PR._triage = lambda: (triage, "")
            FA.sealed_sessions = lambda root=None: (seals, True)
            return PR.report()
        finally:
            PR._triage, FA.sealed_sessions = real_t, real_s

    def test_no_seal_satisfying_the_contract_is_UNREACHABLE_not_CLEAN(self):
        """The live case, constructed: seals exist, none of them certifies full extraction."""
        r = self._run({"reel_s_1": {"panels": 9, "frames": 100}},
                      {"s_1": {"ts": 1, "promptVer": "vpX"}})     # no `extracted` -> refused
        self.assertEqual(
            r["state"], PR.UNREACHABLE,
            "with NOT ONE seal satisfying the extraction contract, the report says %r. No reel can "
            "be judged disposable, so the contradiction cannot arise — calling that CLEAN reports "
            "a filter that rejected every input as a pipeline shown healthy." % r["state"])
        self.assertIn("REFUSING EVERY SEAL", r["why"],
                      "it reached the right state without saying why, which is the half a reader "
                      "would have to re-derive")

    def test_nothing_joining_is_UNREACHABLE_not_CLEAN(self):
        """A seal that satisfies the contract but joins no reel proves nothing either."""
        r = self._run({"reel_s_ZZZ": {"panels": 4, "frames": 10}}, {"s_1": _full_seal()})
        self.assertEqual(r["state"], PR.UNREACHABLE,
                         "nothing joined and it reported %r. A zero over an empty join measures "
                         "the join." % r["state"])

    def test_a_real_contradiction_is_reported_as_one(self):
        """⚠ BASELINE: without this the two UNREACHABLE tests could both pass on a report() that
        can only ever say UNREACHABLE, which would be a guard that cannot distinguish anything."""
        r = self._run({"reel_s_1": {"panels": 12, "frames": 80}}, {"s_1": _full_seal()})
        self.assertEqual(
            r["state"], PR.CONTRADICTION,
            "a seal certifying FULL extraction sits on a reel the survey says held 12 panels, and "
            "the report says %r. That is the exact case A4 was born from." % r["state"])
        self.assertEqual([x["reel"] for x in r["rows"]], ["reel_s_1"])

    def test_CLEAN_is_reachable_when_it_is_actually_earned(self):
        """And the other baseline: the word CLEAN must be attainable, or the two UNREACHABLE
        assertions above are just describing a function that never says anything else."""
        r = self._run({"reel_s_1": {"panels": 0, "frames": 80}}, {"s_1": _full_seal()})
        self.assertEqual(
            r["state"], PR.CLEAN,
            "a joined seal that satisfies the contract, on a reel the survey says held NOTHING, is "
            "the one shape that earns CLEAN — and it reported %r instead." % r["state"])

    def test_an_unreadable_store_is_UNREACHABLE_not_an_empty_corpus(self):
        real = PR._triage
        try:
            PR._triage = lambda: (None, "the store could not be read")
            r = PR.report()
        finally:
            PR._triage = real
        self.assertEqual(r["state"], PR.UNREACHABLE)
        self.assertIn("could not be read", r["why"])

    def test_the_contract_is_read_from_frame_authority_not_copied(self):
        """[[copy-drift]] §1 — if this module ever hardcodes the three facts, the contract can
        change next door and this acceptance test goes on grading against the old one."""
        import io as _io
        src = _io.open(os.path.join(HERE, "printer_reach.py"), encoding="utf-8").read()
        body = src.split('"""', 2)[-1]          # skip the module docstring, which names them
        for fact in FA.EXTRACTION_CONTRACT:
            self.assertNotIn(
                '"%s"' % fact, body,
                "printer_reach hardcodes the contract fact %r instead of asking frame_authority. "
                "The contract would then be able to change without this test noticing." % fact)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
