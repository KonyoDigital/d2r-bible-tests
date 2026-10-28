# -*- coding: utf-8 -*-
"""REG-2912 - A VAULT SIMULATION STOPS THE OCR WORKER IT STARTED, AND LEAVES ONE IT DID NOT START ALONE.

test_vault_lane's teardown found an `ocr_mac --worker` alive ("A TEST LEFT A CHILD PROCESS RUNNING"). Measured, class by
class, on this Mac: TestVaultDecisions alone reproduces it (6 passed, 1 error); the other four classes leave nothing. Its
cases run vault_simulate.run, and one run of the seen-once scenario over the synthetic reels took tv_diablo's warm workers
from none to one (_OCR): the sweep's own gate warms the OCR worker and nothing stopped it. So it was not a worker leaking
between laws of a sweep - the file leaked it alone - and the fix is the harness, not a tolerance: vault_simulate.run now
stops the warm workers its run started (exec_hygiene, the one door that knows them) and leaves one that was already warm.
This law looks for the leftover itself, so it fails under plain unittest (heart2, run_gates) as well as under pytest.
Two cases run on every venue with a stand-in worker (a live child in `.p` and a `.stop()`, all exec_hygiene asks of one);
the two that warm the real ocr_mac need macOS and say so off it rather than pass.
RED_PROOF below.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import exec_hygiene as EH  # noqa: E402
import vault_fixture_reels as VF  # noqa: E402
import vault_simulate as VS  # noqa: E402

OCR_HERE = sys.platform == "darwin" and os.access(os.path.join(HERE, "bin", "ocr_mac"), os.X_OK)


def _ocr_children():
    """This process's descendants that run ocr_mac. A ps that will not answer raises: an unread table is not a clean one."""
    out = subprocess.run(["ps", "-Ao", "pid=,ppid=,command="], capture_output=True, text=True, timeout=20, check=True).stdout
    kids, rows = {}, []
    for line in out.splitlines():
        p = line.strip().split(None, 2)
        if len(p) == 3 and p[0].isdigit() and p[1].isdigit():
            rows.append((int(p[0]), int(p[1]), p[2]))
            kids.setdefault(int(p[1]), []).append(int(p[0]))
    mine, stack = set(), [os.getpid()]
    while stack:
        for c in kids.get(stack.pop(), []):
            if c not in mine:
                mine.add(c)
                stack.append(c)
    return [cmd[:100] for pid, _pp, cmd in rows if pid in mine and "ocr_mac" in cmd]


class _Held(object):
    """A stand-in warm worker: a live child in `.p` and a `.stop()` - exactly what exec_hygiene.warm_workers looks for."""
    def __init__(self):
        self.p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])

    def alive(self):
        return self.p is not None and self.p.poll() is None

    def stop(self):
        p, self.p = self.p, None
        if p is not None and p.poll() is None:
            p.kill()
            p.wait(timeout=10)


class _Reels(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="vsim-worker-")
        cls.hist, why = VF.materialise(cls.root)
        if not cls.hist:
            raise AssertionError("PREMISE: the synthetic reels could not be built: %s" % why)

    @classmethod
    def tearDownClass(cls):
        EH.quiesce_before_exec()
        shutil.rmtree(cls.root, ignore_errors=True)

    def _scenario(self):
        scn = dict([s for s in VS.SCENARIOS if s["id"] == "seen-once"][0])
        scn["reels"] = list(VF.REELS)[:len(scn.get("reels") or [1])]
        return VS.build(scn, hist_dir=self.hist), scn


class AStandInWorkerOnEveryVenue(_Reels):
    """The rule itself, with no ocr_mac: a worker that appears during the run is stopped, one held before it is not."""

    def setUp(self):
        import tv_diablo as TD
        self.TD = TD
        self.held = []

    def tearDown(self):
        for w in self.held:
            w.stop()
        if hasattr(self.TD, "_REG2912_HELD"):
            delattr(self.TD, "_REG2912_HELD")

    def test_a_worker_that_appears_during_the_run_is_stopped(self):
        built, _ = self._scenario()
        orig = VS.vr.sweep

        def sweep(*a, **k):
            w = _Held()
            self.held.append(w)
            self.TD._REG2912_HELD = w          # a module the door watches now holds a worker it did not before
            return orig(*a, **k)
        VS.vr.sweep = sweep
        try:
            p = VS.run(built, hist_dir=self.hist)
        finally:
            VS.vr.sweep = orig
        self.assertTrue(p.get("ok") is not False, "PREMISE: the simulation did not run: %r" % p.get("why"))
        self.assertEqual(len(self.held), 1, "PREMISE: the sweep was not the run's own")
        self.assertFalse(self.held[0].alive(), "the run left a worker that appeared during it running")

    def test_a_worker_held_before_the_run_is_left_alone(self):
        built, _ = self._scenario()
        w = _Held()
        self.held.append(w)
        self.TD._REG2912_HELD = w
        self.assertIn(id(w), [id(o) for _m, _n, o in EH.warm_workers()], "PREMISE: the door cannot see the stand-in")
        VS.run(built, hist_dir=self.hist)
        self.assertTrue(w.alive(), "the run stopped a worker it did not start")


@unittest.skipUnless(OCR_HERE, "no executable ocr_mac on this machine (CI): the real OCR worker cannot be warmed here")
class ASimulationLeavesNoWorkerBehind(_Reels):

    def setUp(self):
        EH.quiesce_before_exec()
        self.assertEqual(_ocr_children(), [], "PREMISE: an OCR worker was already running before the case")

    def test_a_run_stops_the_worker_it_started(self):
        import tv_diablo as TD
        built, _ = self._scenario()
        spawned, orig = [], TD._OCR._spawn
        TD._OCR._spawn = lambda *a, **k: (spawned.append(1), orig(*a, **k))[1]
        try:
            p = VS.run(built, hist_dir=self.hist)
        finally:
            TD._OCR._spawn = orig
        self.assertTrue(p.get("ok") is not False, "PREMISE: the simulation did not run: %r" % p.get("why"))
        self.assertTrue(spawned, "PREMISE: the run started no OCR worker, so this case would be about nothing")
        self.assertEqual([n for _m, n, _o in EH.warm_workers()], [], "the run left a warm worker it started")
        self.assertEqual(_ocr_children(), [], "the run left an ocr_mac worker running")

    def test_a_worker_warm_before_the_run_is_left_alone(self):
        import tv_diablo as TD
        built, scn = self._scenario()
        frame = sorted(f for f in os.listdir(os.path.join(self.hist, scn["reels"][0])) if f.endswith(".jpg"))[0]
        TD._OCR.read(os.path.join(self.hist, scn["reels"][0], frame), timeout=10)   # someone else's warm worker
        before = [id(o) for _m, _n, o in EH.warm_workers()]
        self.assertTrue(before, "PREMISE: the sweep's gate did not warm a worker, so this case would be about nothing")
        VS.run(built, hist_dir=self.hist)
        self.assertEqual([id(o) for _m, _n, o in EH.warm_workers()], before, "the run stopped a worker it did not start")


RED_PROOF = [
    {"why": "REG-2912 - the simulation leaves the OCR worker it started running",
     "file": "vault_simulate.py",
     "find": "                        o.stop()                       # REG-2912 the run stops what it started\n",
     "replace": "                        pass\n",
     "matches": 1},
    {"why": "REG-2912 - the simulation stops every warm worker, its own or not",
     "file": "vault_simulate.py",
     "find": "                if id(o) not in _warm:\n",
     "replace": "                if True:\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
