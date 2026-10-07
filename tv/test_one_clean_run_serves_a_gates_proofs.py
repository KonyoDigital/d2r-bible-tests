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


class AReusedCleanRunNeverBanksAFalseBlind(unittest.TestCase):
    """REG-1677 (the v3543 cross-family eye) - proof 0's runs leave the sandbox changed (other.py drifts), so proof 1,
    judged on the CACHED green, misses its anchor: INVALID, which the census files as BLIND and which shuts every lock.
    Its own fresh clean run would have gone red first (UNPROVABLE). The closing run must catch it."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="h2drift.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(self.tv)
        for fn, body in (("subject.py", 'A = "GOOD"\n'), ("other.py", 'B = "GOOD"\n'),
                         ("fake_gate.py", "import sys\nsys.exit(0)\n")):
            with io.open(os.path.join(self.tv, fn), "w", encoding="utf-8") as fh:
                fh.write(body)
        self.proofs = [{"file": "subject.py", "find": 'A = "GOOD"', "replace": 'A = "BAD"', "matches": 1, "why": "A"},
                       {"file": "other.py", "find": 'B = "GOOD"', "replace": 'B = "BAD"', "matches": 1, "why": "B"}]
        self._real = H._run_gate
        self.addCleanup(lambda: setattr(H, "_run_gate", self._real))

    def _read(self, fn):
        with io.open(os.path.join(self.tv, fn), encoding="utf-8") as fh:
            return fh.read()

    def _drifting_run(self, sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
        """A law that is red on a tamper - and whose tampered run leaves other.py changed (state the law wrote)."""
        a, b = self._read("subject.py"), self._read("other.py")
        if "BAD" in a:
            with io.open(os.path.join(self.tv, "other.py"), "w", encoding="utf-8") as fh:
                fh.write('B = "DRIFTED"\n')
            return False, "Ran 1 test | FAILED"
        if "GOOD" not in b:
            return False, "Ran 1 test | FAILED (the sandbox drifted)"
        return True, "Ran 1 test | OK"

    def test_a_drifted_sandbox_is_unprovable_never_blind(self):
        H._run_gate = self._drifting_run
        verdict, per = H._prove_gate(self.tv, GATE, "fake_gate.py", self.proofs, _quiet)
        self.assertNotIn(H.INVALID, per, "a proof judged on a reused clean run in a drifted sandbox was banked INVALID "
                                          "(the census files that BLIND, and one BLIND shuts every lock): %r" % per)
        self.assertNotIn(verdict, (H.BLIND, H.INVALID), per)
        self.assertEqual(verdict, H.UNPROVABLE, per)

    def test_a_reused_invalid_is_caught_even_when_nothing_was_proven(self):
        """The finding's own scenario: no proof PROVEN, so the old closing check never ran. Proof 0 is a genuine BLIND
        (its tamper stays green on its OWN fresh clean run) whose run drifts other.py; proof 1, judged on the reused
        green, misses its anchor. Proof 0's BLIND stands; proof 1 is UNPROVABLE, never INVALID."""
        def run(sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
            if "BAD" in self._read("subject.py"):
                with io.open(os.path.join(self.tv, "other.py"), "w", encoding="utf-8") as fh:
                    fh.write('B = "DRIFTED"\n')
                return True, "Ran 1 test | OK"                    # the law misses this tamper: a real BLIND
            if "GOOD" not in self._read("other.py"):
                return False, "Ran 1 test | FAILED (the sandbox drifted)"
            return True, "Ran 1 test | OK"
        H._run_gate = run
        verdict, per = H._prove_gate(self.tv, GATE, "fake_gate.py", self.proofs, _quiet)
        self.assertEqual(per, [H.BLIND, H.UNPROVABLE],
                         "a reused clean run banked an INVALID when nothing was PROVEN, or a genuine BLIND was hidden: %r"
                         % per)

    def test_a_closing_run_that_raises_keeps_the_gate_honest(self):
        state = {"n": 0}

        def run(sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
            if "BAD" in self._read("subject.py") or "BAD" in self._read("other.py"):
                return False, "Ran 1 test | FAILED"
            state["n"] += 1
            if state["n"] >= 2:
                raise OSError("the sandbox file is locked")
            return True, "Ran 1 test | OK"
        H._run_gate = run
        verdict, per = H._prove_gate(self.tv, GATE, "fake_gate.py", self.proofs, _quiet)
        self.assertEqual(per, [H.UNPROVABLE, H.UNPROVABLE],
                         "a closing run that raised turned the gate's judged proofs into something else: %r" % per)
        self.assertEqual(verdict, H.UNPROVABLE)


class ThePushPathSharesItsCleanRunToo(OneCleanRunServesAGate):
    """REG-1988 - _prove_gate handed a push-time gate to _prove_gate_push BEFORE it set _CLEAN.runs, so the run the hook
    pays on every push still ran the untampered law before each proof: 2N runs where N+2 do. The same cases as above,
    driven through the REAL push path (H._PUSH set, as `--prove --push` sets it), plus what the verdict cache banks."""

    def setUp(self):
        super(ThePushPathSharesItsCleanRunToo, self).setUp()
        from unittest import mock
        p = mock.patch.dict(os.environ, {"HEART2_RED_MEMORY": "0"})   # the sabotage memory is neither read nor written
        p.start()
        self.addCleanup(p.stop)
        self.cache = H._VerdictCache(path=os.path.join(self.root, ".heart2_cache.json"), say=_quiet)
        self.addCleanup(lambda: setattr(H, "_PUSH", None))

    def _gate(self, runs, proofs=None):
        H._run_gate = runs
        H._PUSH = self.run = H._PushRun(order={}, browser=(), cache=self.cache)
        try:
            return H._prove_gate(self.tv, GATE, "fake_gate.py", self.proofs if proofs is None else proofs, _quiet)
        finally:
            H._PUSH = None

    def test_a_proven_push_gate_banks_every_proof_after_its_closing_run(self):
        verdict, per = self._gate(_Runs(self.tv))
        self.assertEqual((verdict, per), (H.PROVEN, [H.PROVEN] * 3))
        self.assertEqual(len(self.cache.entries), 3, "a PROVEN push gate banked %d of its 3 proofs" % len(self.cache.entries))

    def test_a_red_closing_run_banks_nothing(self):
        verdict, per = self._gate(_Runs(self.tv, red_clean_at=2))
        self.assertEqual(per, [H.UNPROVABLE] * 3)
        self.assertEqual(self.cache.entries, {}, "a PROVEN the closing clean run took away was still banked")

    def test_a_law_already_red_untampered_is_judged_once(self):
        runs = _Runs(self.tv, red_clean_at=1)
        verdict, per = self._gate(runs)
        self.assertEqual((runs.clean, runs.tampered), (1, 0), "a red clean run was re-run at push time")
        self.assertEqual(self.run.first[3], "the law is ALREADY RED untampered, so no proof of it can be judged",
                         "the push no longer stops on a law already red untampered")
        self.assertEqual(per[0], H.UNPROVABLE)

    def test_the_share_ends_with_the_gate(self):
        self._gate(_Runs(self.tv))
        self.assertIsNone(getattr(H._CLEAN, "runs", None), "a push gate's clean run outlived it into the next gate")
        self.assertIsNone(getattr(H._CLEAN, "pending", None), "a push gate's unbanked proofs outlived it")


RED_PROOF = [
    {"why": "REG-1988 - the push path pays its own clean run per proof again (2N runs on every push)",
     "file": "heart2.py",
     "find": "    _CLEAN.runs = {}\n    _CLEAN.pending = []",
     "replace": "    _CLEAN.runs = None\n    _CLEAN.pending = []",
     "matches": 1},
    {"why": "REG-1988 - the push path asks no closing clean run, so a drifted sandbox's PROVEN is banked",
     "file": "heart2.py",
     "find": "        per = _closing_clean(name, per, say)             # REG-1988",
     "replace": "        per = per                                        # REG-1988",
     "matches": 1},
    {"why": "REG-1988 - a push-time PROVEN is banked before the closing run can take it away",
     "file": "heart2.py",
     "find": "                if isinstance(_pend, list):\n",
     "replace": "                if False:\n",
     "matches": 1},
    {"why": "REG-1677 - the closing run is skipped when nothing was PROVEN, so a reused clean run banks a false BLIND",
     "file": "heart2.py",
     "find": "    if not shared or not any(v in (PROVEN, BLIND, INVALID) for v in verdicts):\n",
     "replace": "    if not shared or PROVEN not in verdicts:\n",
     "matches": 1},
    {"why": "REG-1677 - a red closing run downgrades only PROVEN: a reused INVALID / BLIND is banked as blind",
     "file": "heart2.py",
     "find": "            return [UNPROVABLE if (v == PROVEN or (j in _reused and v in (BLIND, INVALID))) else v\n",
     "replace": "            return [UNPROVABLE if v == PROVEN else v\n",
     "matches": 1},
    {"why": "REG-1677 - a closing run that raises escapes and the whole gate is written BLIND and unmeasured",
     "file": "heart2.py",
     "find": "        except Exception as _ce:                         # REG-1677",
     "replace": "        except ZeroDivisionError as _ce:                 # REG-1677",
     "matches": 1},
    {"why": "REG-1669 - every proof pays its own clean run again (the 82-minute ALT slice)",
     "file": "heart2.py",
     "find": "    _hit = _runs.get(_ck) if isinstance(_runs, dict) else None\n",
     "replace": "    _hit = None\n",
     "matches": 1},
    {"why": "REG-1669 - no closing clean run: a gate whose state drifted across its proofs is credited PROVEN",
     "file": "heart2.py",
     "find": "    if not shared or not any(v in (PROVEN, BLIND, INVALID) for v in verdicts):\n        return verdicts\n",  # REG-1677 re-anchor
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
