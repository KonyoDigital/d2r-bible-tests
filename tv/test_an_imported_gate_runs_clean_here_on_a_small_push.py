# -*- coding: utf-8 -*-
"""REG-2587 (#242 on a small push) - A GATE WHOSE PROOFS ANOTHER TREE PROVED RUNS CLEAN HERE, EVEN WITH NO WAVE.

#242 (REG-1996) let the cache serve a proof banked in another tree and kept one guard: the push's clean wave runs every
such gate untampered in THIS tree once, so a law red only here (live state only this tree holds) is never passed on
another tree's word. But the wave runs only when a push has more gates than lanes, and in the main pass a gate whose
every proof is served runs no law at all. MEASURED in the proof-keys e2e (2026-10-23): a push of 1 imported gate on 1
lane ran ZERO clean runs; 2 gates on 1 lane ran 2. With CI shards banking whole suites from another tree, the small push
is exactly the one that would trust them blind. Now the main pass asks that gate's clean run here, once:

  1. served from ANOTHER tree (or from none named) -> one clean run here; served from THIS tree -> none;
  2. GREEN keeps the served PROVENs; RED fails the push fast and keeps none; a run that cannot finish keeps none;
  3. a gate the wave already ran clean here is not asked twice.
Drives the REAL _prove_gate push path over a temp gate and a temp cache.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402  (its docstrings carry non-ASCII)
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

GATE = "no-such-registered-gate"
LINES = []


def _say(*a, **k):
    LINES.append(" ".join(str(x) for x in a))


class _Runs(object):
    """heart2._run_gate's stand-in: a tampered run is red; the Nth CLEAN run answers clean[N-1] (True / False / None)."""

    def __init__(self, tv, clean):
        self.tv, self.script, self.clean = tv, list(clean), 0

    def __call__(self, sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
        with io.open(os.path.join(self.tv, "subject.py"), encoding="utf-8") as fh:
            if "BAD" in fh.read():
                return False, "Ran 1 test | FAILED"
        self.clean += 1
        a = self.script[self.clean - 1] if self.clean <= len(self.script) else True
        return a, {True: "Ran 1 test | OK", False: "Ran 1 test | FAILED (red here)"}.get(a, "timed out after 120s")


class AnImportedGateRunsCleanHere(unittest.TestCase):

    def setUp(self):
        del LINES[:]
        self.root = tempfile.mkdtemp(prefix="h2cleanhere.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(self.tv)
        with io.open(os.path.join(self.tv, "subject.py"), "w", encoding="utf-8") as fh:
            fh.write('A = "GOOD"\nB = "GOOD"\n')
        with io.open(os.path.join(self.tv, "fake_gate.py"), "w", encoding="utf-8") as fh:
            fh.write("import sys\nsys.exit(0)\n")
        self.proofs = [{"file": "subject.py", "find": '%s = "GOOD"' % k, "replace": '%s = "BAD"' % k,
                        "matches": 1, "why": k} for k in ("A", "B")]
        for p in (mock.patch.object(H, "_run_gate", None),
                  mock.patch.dict(os.environ, {"HEART2_RED_MEMORY": "0"})):
            p.start()
            self.addCleanup(p.stop)
        self.assertIsNone(H._PUSH, "PREMISE: no push-time run is in progress")
        self.addCleanup(lambda: setattr(H, "_PUSH", None))
        self.cache = H._VerdictCache(path=os.path.join(self.root, ".heart2_cache.json"), say=_say)

    def push(self, tree, clean, wave=None):
        """Bank every proof as proved in `tree` (None: no tree named), then prove the gate at push time."""
        self.cache.entries, self.cache.hits = {}, 0
        for i, pr in enumerate(self.proofs):
            key, _rels, why = self.cache.key_for(self.tv, GATE, "fake_gate.py", pr)
            self.assertIsNotNone(key, "PREMISE: the fixture law cannot be keyed: %s" % why)
            e = {"verdict": H.PROVEN, "provedAt": 1, "gate": GATE, "proof": i}
            if tree is not None:
                e["tree"] = tree
            self.cache.entries[key] = e
        self.runs = _Runs(self.tv, clean)
        H._run_gate = self.runs
        H._PUSH = run = H._PushRun(order={}, browser=(), cache=self.cache)
        if wave:
            run.clean_wave.update(wave)
        try:
            verdict, per = H._prove_gate(self.tv, GATE, "fake_gate.py", self.proofs, _say)
        finally:
            H._PUSH = None
        self.assertEqual(self.cache.hits, 2, "PREMISE: both proofs were served by the cache")
        return run, per

    def test_served_from_this_tree_needs_no_clean_run(self):
        run, per = self.push(H.TREE_ID, [])
        self.assertEqual((per, self.runs.clean), ([H.PROVEN] * 2, 0), "a gate proved in THIS tree was run again")

    def test_served_from_another_tree_runs_clean_here_once(self):
        for tree in ("/some/other/worktree", None):
            run, per = self.push(tree, [True])
            self.assertEqual(self.runs.clean, 1, "banked in %r: %d clean run(s) here, want exactly 1 - the #242 guard "
                             "is skipped on a push with no wave" % (tree, self.runs.clean))
            self.assertEqual(per, [H.PROVEN] * 2, "a GREEN clean run here dropped the served proofs")
            self.assertIsNone(run.first)

    def test_red_here_keeps_nothing_and_fails_fast(self):
        run, per = self.push("/some/other/worktree", [False])
        self.assertEqual(per, [H.UNPROVABLE] * 2, "a law RED in this tree kept another tree's PROVENs")
        self.assertIsNotNone(run.first, "a law red here did not stop the push")
        self.assertEqual(run.first[0], GATE)
        self.assertTrue(any("REG-2587" in ln and "RED" in ln for ln in LINES), LINES)

    def test_a_clean_run_that_cannot_finish_keeps_nothing(self):
        run, per = self.push("/some/other/worktree", [None])
        self.assertEqual(per, [H.UNPROVABLE] * 2, "a clean run that never answered kept another tree's PROVENs")
        self.assertIsNone(run.first, "an unknown clean run was called RED")

    def test_a_gate_the_wave_ran_clean_here_is_not_asked_twice(self):
        run, per = self.push("/some/other/worktree", [False],
                             wave={("fake_gate.py", "()", "None", "", 180): (True, "Ran 1 test | OK")})
        self.assertEqual((per, self.runs.clean), ([H.PROVEN] * 2, 0), "the wave's green clean run was asked again")


    def test_the_failure_names_the_proof_whose_clean_run_was_red(self):
        """second eye - run.fail names the proof the clean run was asked for (the run's order), not the lowest index"""
        self.proofs[0]["widths"] = "not a width"        # unreadable: skipped, so proof 1 is the one asked
        run, per = self.push("/some/other/worktree", [False])
        self.assertEqual(run.first[:2], (GATE, 1), "the push names %r, not the proof whose clean run was red"
                         % (run.first,))

    def test_no_clean_run_that_could_be_asked_keeps_nothing(self):
        """second eye - every proof's declaration unreadable: nothing untampered ran here, so nothing is kept"""
        for pr in self.proofs:
            pr["widths"] = "not a width"
        run, per = self.push("/some/other/worktree", [True])
        self.assertEqual(self.runs.clean, 0)
        self.assertEqual(per, [H.UNPROVABLE] * 2, "a gate no clean run reached kept another tree's PROVENs")


RED_PROOF = [
    {"why": "REG-2587 - a gate served from another tree runs no clean run here when no wave runs (the e2e gap)",
     "file": "heart2.py",
     "find": "        per = _clean_here(sandbox, name, filename, proofs, per, say, run)   # REG-2587",
     "replace": "        pass  # ",
     "matches": 1},
    {"why": "REG-2587 - the tree a served proof was proved in is never noted, so no gate is ever asked",
     "file": "heart2.py",
     "find": "                    _srv.append((idx, hit.get(\"tree\")))",
     "replace": "                    pass",
     "matches": 1},
    {"why": "REG-2587 - a gate proved in THIS tree is run clean again on every push",
     "file": "heart2.py",
     "find": "    foreign = sorted(i for i, t in (getattr(_CLEAN, \"served\", None) or []) if t != TREE_ID)\n",
     "replace": "    foreign = sorted(i for i, t in (getattr(_CLEAN, \"served\", None) or []))\n",
     "matches": 1},
    {"why": "REG-2587 - a law RED here keeps another tree's PROVENs",
     "file": "heart2.py",
     "find": "    out = [UNPROVABLE if x == PROVEN else x for x in per]\n",
     "replace": "    out = list(per)\n",
     "matches": 1},
    {"why": "REG-2587 - a clean run that could not finish keeps another tree's PROVENs on a guess",
     "file": "heart2.py",
     "find": "    red = v == UNPROVABLE and bool(why.get(\"red\"))\n",
     "replace": "    red = v == UNPROVABLE and bool(why.get(\"red\"))\n    if not red:\n        return per\n",
     "matches": 1},
    {"why": "REG-2587 - a law red here is said but the push is not stopped",
     "file": "heart2.py",
     "find": "    if red and run.fail(name, asked, UNPROVABLE,",
     "replace": "    if False and run.fail(name, asked, UNPROVABLE,",
     "matches": 1},
    {"why": "REG-2587 - the push's failure names the lowest served proof, not the one whose clean run was red",
     "file": "heart2.py",
     "find": "    if red and run.fail(name, asked, UNPROVABLE,",
     "replace": "    if red and run.fail(name, foreign[0], UNPROVABLE,",
     "matches": 1},
    {"why": "REG-2587 - a gate no clean run could reach keeps another tree's PROVENs (an unreadable declaration hole)",
     "file": "heart2.py",
     "find": "        if skips == {ELSEWHERE}:\n",
     "replace": "        if True:\n",
     "matches": 1},
    {"why": "REG-2587 - a gate the wave already ran clean here is asked again",
     "file": "heart2.py",
     "find": "        return per                                       # the wave ran it clean here",
     "replace": "        pass                                             # the wave ran it clean here",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
