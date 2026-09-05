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
import json
import os
import shutil
import sys
import tempfile
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

    def test_an_unreadable_store_is_UNKNOWN_not_an_empty_corpus(self):
        """⚠⚠ REG-543 — THIS TEST'S NAME WAS ALWAYS RIGHT AND ITS ASSERTION PINNED THE COLLAPSE.
        It exists to stop *"I could not read the store"* being confused with a verdict, and it
        asserted `UNREACHABLE` — because until now that was the only word available, and the SAME
        word carried the real finding *"I measured, and the contradiction is structurally
        impossible on this corpus"*. So a store that failed to open was indistinguishable from the
        measured result to anything branching on `state`; only the `why` told them apart.

        UNKNOWN is its own state now, and this asserts the rule the name always described. The
        assertion moved; the intent did not.
        """
        real = PR._triage
        try:
            PR._triage = lambda: (None, "the store could not be read")
            r = PR.report()
        finally:
            PR._triage = real
        self.assertEqual(r["state"], PR.UNKNOWN,
                         "nothing was established and it did not say UNKNOWN: %s" % r.get("why"))
        self.assertNotEqual(r["state"], PR.UNREACHABLE,
                            "an unreadable store still wears the word that carries the MEASURED "
                            "finding — that is the collapse this split removed")
        self.assertIn("could not be read", r["why"])

    def test_UNREACHABLE_still_means_the_MEASURED_finding(self):
        """⚠ BASELINE for the split: if UNREACHABLE stopped being reachable, the fix would have
        traded one collapse for a lost verdict.

        ⚠⚠ IT USED TO CALL `PR.report()` BARE, WHICH MADE IT A TEST ABOUT HIS FOOTAGE. Both stores
        it reaches are gitignored — `.gitignore:147` for `tv/retro_triage.json`, and
        `tv/vault_swept.json` is simply untracked — so `git ls-files` measures 0 tracked bytes of
        either and the runner has neither. `_triage()` then cannot open the file and answers
        UNKNOWN, which is the correct answer to a store that is not there. MEASURED on a
        `git archive HEAD` export of this tree: `AssertionError: 'UNKNOWN' != 'UNREACHABLE'`,
        byte-identical to CI run 33951643518. Nothing was lost; the runner has none of his reels.

        ⚠ AND IT WAS PINNED TO A DATUM, NOT A LAW. His corpus reports UNREACHABLE only while no
        seal names `location` — the day the sweep starts recording it, his corpus earns CLEAN and
        this goes red with nothing broken. A baseline must assert what must always be true of
        `report()`, not what happens to be true of one shelf.
        [[regression-guard]] [[feedback-blind-fixture-green-gate]]

        So the corpus is CONSTRUCTED — and, unlike the two stubbed cases above, it is constructed
        ON DISK and read by the module's OWN readers. That distinction is the whole baseline after
        REG-543: `report()` can only reach UNKNOWN when a reader fails, and a stubbed reader can
        never fail, so only a real read off a real file proves UNREACHABLE is still reachable end
        to end rather than merely reachable in a harness.
        """
        tmp = tempfile.mkdtemp(prefix="printer-reach-fixture-")
        real_triage_path, real_seals = PR.TRIAGE, FA.sealed_sessions
        try:
            # a readable reel survey, and a readable seal store whose one seal names no `extracted`
            # — the live shape, written out rather than stubbed so `_triage` and `sealed_sessions`
            # both do their real work. `_load` joins root with SEAL_STORE, so the fixture is a
            # DIRECTORY and `sealed_sessions` is asked for it by its own documented `root=` seam.
            triage = json.dumps({"reel_s_1": {"panels": 9, "frames": 100}})
            seals = json.dumps({"s_1": {"ts": 1, "rows": 1, "promptVer": "vpX"}})
            with open(os.path.join(tmp, "retro_triage.json"), "w", encoding="utf-8") as fh:
                fh.write(triage)
            with open(os.path.join(tmp, FA.SEAL_STORE), "w", encoding="utf-8") as fh:
                fh.write(seals)
            PR.TRIAGE = os.path.join(tmp, "retro_triage.json")
            FA.sealed_sessions = lambda root=None: real_seals(tmp)
            r = PR.report()
        finally:
            PR.TRIAGE, FA.sealed_sessions = real_triage_path, real_seals
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertNotEqual(
            r["state"], PR.UNKNOWN,
            "both stores were written to disk and read back, so nothing failed to open — reading "
            "UNKNOWN here means a reader broke, not that the corpus said nothing: %s" % r.get("why"))
        self.assertEqual(
            r["state"], PR.UNREACHABLE,
            "the module's own readers, on a store that IS readable and whose seals certify no "
            "extraction, no longer report the measured UNREACHABLE (%r). That is the verdict the "
            "UNKNOWN split existed to keep." % r["state"])
        self.assertIn("REFUSING EVERY SEAL", r["why"],
                      "it is the OTHER UNREACHABLE — the join, not the contract. This baseline "
                      "must pin the measured finding, not whichever one is easiest to reach")

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
