# -*- coding: utf-8 -*-
"""REG-1992 - A LAW ALREADY RED UNTAMPERED REFUSES THE PUSH BEFORE ANY TAMPERED RUN (THE CLEAN WAVE).

MEASURED: the v3601 push was refused at minute 39 and the v3602 push at minute 80, both on a law ALREADY RED untampered -
the cheapest verdict the prover makes (one run per gate), scheduled gate by gate among the expensive tampered ones. Every
gate's untampered run now goes first; a red stops the run before a single tamper, and the main pass reuses each green
(its closing run asks it again in that pass's own sandbox).

Driven through the REAL _prove_push, _prove_gates, _prove_lane, _wave_gate and _prove_one; only git's facts, the sandbox
build and the law RUN are stand-ins (a run answers from the subject file's actual bytes: green while it reads GOOD, red
once a tamper wrote BAD - and red untampered for the one gate a case names).
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
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

GATES = ["wave-g1", "wave-g2", "wave-g3", "wave-g4"]


def _quiet(*a, **k):
    pass


class _Runs(object):
    """A stand-in for heart2._run_gate. `red_gate` is red untampered; every gate is red once its tamper wrote BAD."""

    def __init__(self, red_gate=None):
        self.red_gate, self.clean, self.tampered = red_gate, 0, 0

    def __call__(self, sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
        with io.open(os.path.join(sandbox_tv, "subject.py"), encoding="utf-8") as fh:
            src = fh.read()
        if "BAD" in src:
            self.tampered += 1
            return False, "Ran 1 test | FAILED"
        self.clean += 1
        if filename == "%s.py" % self.red_gate:
            return False, "Ran 1 test | FAILED (red untampered)"
        return True, "Ran 1 test | OK"


class ARedLawRefusesBeforeAnyTamper(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="h2wave.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.proofs = [{"file": "subject.py", "find": '%s = "GOOD"' % k, "replace": '%s = "BAD"' % k,
                        "matches": 1, "why": k} for k in ("A", "B")]

        def _sandbox(say=print):
            d = tempfile.mkdtemp(prefix="lane.", dir=self.root)
            tv = os.path.join(d, "tv")
            os.makedirs(tv)
            with io.open(os.path.join(tv, "subject.py"), "w", encoding="utf-8") as fh:
                fh.write('A = "GOOD"\nB = "GOOD"\n')
            for g in GATES:
                with io.open(os.path.join(tv, g + ".py"), "w", encoding="utf-8") as fh:
                    fh.write("import sys\nsys.exit(0)\n")
            return tv, d

        names = list(GATES)
        for target, value in (
                ("make_sandbox", _sandbox),
                ("_push_facts", lambda have, say: (None, {}, names, {"anchor": 0, "entry": 0, "target": 0})),
                ("browser_gates", lambda gates, unclassified=None: set())):
            p = mock.patch.object(H, target, value)
            p.start()
            self.addCleanup(p.stop)
        for env in ({"HEART2_PROVE_WORKERS": "1", "HEART2_RED_MEMORY": "0"},):
            p = mock.patch.dict(os.environ, env)
            p.start()
            self.addCleanup(p.stop)
        self.assertIsNone(H._PUSH, "PREMISE: no push-time run is in progress")

    def _push(self, runs):
        have = [(g, g + ".py", list(self.proofs)) for g in GATES]
        stopped = []
        with mock.patch.object(H, "_run_gate", runs):
            results, per = H._prove_push(have, _quiet, stopped=stopped, cache=None)
        return results, per, stopped

    def test_the_last_gate_red_untampered_refuses_before_a_single_tamper(self):
        runs = _Runs(red_gate="wave-g4")          # queued LAST: the old schedule tampered every gate ahead of it first
        results, per, stopped = self._push(runs)
        self.assertTrue(stopped, "a law already red untampered did not refuse the push")
        self.assertEqual(stopped[0][0], "wave-g4")
        self.assertEqual(runs.tampered, 0, "%d tampered run(s) ran before the red clean run was found" % runs.tampered)
        self.assertEqual(results, {}, "a stopped wave still handed back verdicts: %s" % results)

    def test_a_green_wave_is_reused_and_every_gate_still_asks_its_closing_run(self):
        runs = _Runs()
        results, per, stopped = self._push(runs)
        self.assertEqual(stopped, [])
        self.assertEqual(results, dict((g, H.PROVEN) for g in GATES))
        self.assertEqual(runs.tampered, 2 * len(GATES))
        self.assertEqual(runs.clean, 2 * len(GATES),
                         "the main pass did not reuse the wave's clean run (or skipped its closing run): %d clean runs "
                         "for %d gates" % (runs.clean, len(GATES)))


RED_PROOF = [
    {"why": "REG-1992 - no clean wave: a law red untampered is found only when its turn comes, after every tamper ahead",
     "file": "heart2.py",
     "find": "            run.wave = True\n",
     "replace": "            run.wave = False\n",
     "matches": 1},
    {"why": "REG-1992 - the main pass ignores the wave and pays a second clean run for every gate",
     "file": "heart2.py",
     "find": "        if _wv is not None and _wv[0] is True:\n",
     "replace": "        if False:\n",
     "matches": 1},
    {"why": "REG-1992 - a red in the wave is said but never stops the run: every tamper ahead of it runs anyway",
     "file": "heart2.py",
     "find": "                if run.fail(name, i, UNPROVABLE, \"the law is ALREADY RED untampered, so no proof of it can be judged\"):\n",
     "replace": "                if (lambda *a: False)(name, i, UNPROVABLE, \"the law is ALREADY RED untampered, so no proof of it can be judged\"):\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
