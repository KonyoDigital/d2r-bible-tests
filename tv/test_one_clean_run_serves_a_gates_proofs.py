# -*- coding: utf-8 -*-
"""REG-1669 (#42) - one clean run serves a gate's proofs, and a closing clean run must still be green.

MEASURED on his ALT 2026-10-01: a 40-gate census slice took 82 minutes, because every proof ran the untampered law
before its tampered run - a gate with N proofs paid 2N runs. Now the proofs of one gate share the first clean run
(N + 1), and one CLOSING clean run after the last proof (N + 2) must still be green: a law whose state drifted across
its proofs could otherwise go red for the drift and be credited with catching the tamper - then no PROVEN of that
gate is kept. A direct _prove_one call outside a gate still runs its own clean run, as it always has.

Driven through the REAL _prove_gate and _prove_one against a real directory; only the law RUN is a stand-in, which
answers from the subject file's actual bytes (green while it reads GOOD, red once a tamper wrote BAD).

RED_PROOF below.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

GATE = "no-such-registered-gate"


def _quiet(*a, **k):
    pass


class _Runs(object):
    """A stand-in for heart2._run_gate: reads the subject's real bytes. `closing_red` turns the Nth clean run red."""

    def __init__(self, tv, red_clean_at=None):
        self.tv, self.red_clean_at = tv, red_clean_at
        self.clean, self.tampered = 0, 0

    def __call__(self, sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
        with io.open(os.path.join(self.tv, "subject.py"), encoding="utf-8") as fh:
            src = fh.read()
        if "BAD" in src:
            self.tampered += 1
            return False, "Ran 1 test | FAILED"
        self.clean += 1
        if self.red_clean_at is not None and self.clean == self.red_clean_at:
            return False, "Ran 1 test | FAILED (drifted state)"
        return True, "Ran 1 test | OK"


class OneCleanRunServesAGate(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="h2clean.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(self.tv)
        with io.open(os.path.join(self.tv, "subject.py"), "w", encoding="utf-8") as fh:
            fh.write('A = "GOOD"\nB = "GOOD"\nC = "GOOD"\n')
        with io.open(os.path.join(self.tv, "fake_gate.py"), "w", encoding="utf-8") as fh:
            fh.write("import sys\nsys.exit(0)\n")
        self.proofs = [{"file": "subject.py", "find": '%s = "GOOD"' % k, "replace": '%s = "BAD"' % k,
                        "matches": 1, "why": k} for k in ("A", "B", "C")]
        self._real = H._run_gate
        self.addCleanup(lambda: setattr(H, "_run_gate", self._real))
        self.assertIsNone(H._PUSH, "PREMISE: no push-time run is in progress")

    def _gate(self, runs, proofs=None):
        H._run_gate = runs
        return H._prove_gate(self.tv, GATE, "fake_gate.py", self.proofs if proofs is None else proofs, _quiet)

    def test_three_proofs_pay_one_clean_run_and_one_closing_run(self):
        runs = _Runs(self.tv)
        verdict, per = self._gate(runs)
        self.assertEqual((verdict, per), (H.PROVEN, [H.PROVEN] * 3))
        self.assertEqual((runs.clean, runs.tampered), (2, 3),
                         "a gate's proofs did not share their clean run (%d clean runs for 3 proofs - every proof "
                         "paid its own, the 82-minute ALT slice)" % runs.clean)

    def test_a_closing_run_that_is_red_keeps_no_proven(self):
        runs = _Runs(self.tv, red_clean_at=2)            # the first clean run green, the closing one red
        verdict, per = self._gate(runs)
        self.assertEqual(per, [H.UNPROVABLE] * 3,
                         "a gate whose sandbox did not stay clean across its proofs was still credited PROVEN")
        self.assertEqual(verdict, H.UNPROVABLE)

    def test_one_proof_needs_no_closing_run(self):
        runs = _Runs(self.tv)
        verdict, per = self._gate(runs, proofs=self.proofs[:1])
        self.assertEqual((verdict, runs.clean, runs.tampered), (H.PROVEN, 1, 1),
                         "a one-proof gate paid a closing run it never needed")

    def test_a_law_already_red_untampered_is_judged_once(self):
        runs = _Runs(self.tv, red_clean_at=1)
        verdict, per = self._gate(runs)
        self.assertEqual(per, [H.UNPROVABLE] * 3)
        self.assertEqual((runs.clean, runs.tampered), (1, 0), "a red clean run was re-run for every proof")

    def test_the_share_ends_with_the_gate(self):
        self._gate(_Runs(self.tv))
        self.assertIsNone(getattr(H._CLEAN, "runs", None), "a gate's clean run outlived it into the next gate")
        runs = _Runs(self.tv)
        H._run_gate = runs
        H._prove_one(self.tv, GATE, "fake_gate.py", self.proofs[0], 0, _quiet)
        self.assertEqual((runs.clean, runs.tampered), (1, 1), "a direct _prove_one call no longer runs its own clean run")


RED_PROOF = [
    {"why": "REG-1669 - every proof pays its own clean run again (the 82-minute ALT slice)",
     "file": "heart2.py",
     "find": "    _hit = _runs.get(_ck) if isinstance(_runs, dict) else None\n",
     "replace": "    _hit = None\n",
     "matches": 1},
    {"why": "REG-1669 - no closing clean run: a gate whose state drifted across its proofs is credited PROVEN",
     "file": "heart2.py",
     "find": "    if not shared or PROVEN not in verdicts:\n        return verdicts\n",
     "replace": "    return verdicts\n",
     "matches": 1},
    {"why": "REG-1669 - a gate's clean run outlives it into the next gate",
     "file": "heart2.py",
     "find": "    finally:\n        _CLEAN.runs = None\n",
     "replace": "    finally:\n        pass\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
