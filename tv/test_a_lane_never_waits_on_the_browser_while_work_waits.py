# -*- coding: utf-8 -*-
"""REG-1989 - A PROVING LANE NEVER PARKS BEHIND THE ONE BROWSER WHILE OTHER WORK WAITS, AND THE BROWSER CHAIN GOES FIRST.

MEASURED on the v3602 push (131 gates, 11 of them reach a browser through their imports and are proved one at a time):
the lanes took gates in queue order, so the serial browser chain started wherever fail-fast happened to rank its first
gate, and a lane that took a browser gate while another lane held the browser WAITED, holding that gate. For the tail of
the run one law was running and three lanes sat idle behind it. _PushRun.take() now hands a lane the free browser first
(the serial chain is the critical path), the next gate that needs no browser when it is busy, and makes a lane wait only
when nothing else is left.

Driven through the REAL _PushRun.take and the REAL _prove_gates / _prove_lane; only the sandbox build and the gate itself
are stand-ins (a gate records when it started and sleeps briefly).
"""
import os
import queue
import shutil
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402


def _quiet(*a, **k):
    pass


def _q(names):
    w = queue.Queue()
    for n in names:
        w.put((n, n + ".py", [{"file": "x.py", "find": "a", "replace": "b", "matches": 1}]))
    return w


class TakeOrder(unittest.TestCase):

    def test_the_free_browser_is_taken_first_and_a_busy_one_never_parks_a_lane(self):
        run = H._PushRun(order={}, browser={"b1", "b2"})
        work = _q(["n1", "b1", "n2", "b2", "n3"])
        first, ctx1 = run.take(work)
        self.assertEqual(first[0], "b1", "the free browser was not taken first - the serial chain starts late")
        self.assertFalse(run.browser_lock.acquire(False), "take() handed a browser gate without holding the browser")
        got = []
        for _ in range(3):
            it, ctx = run.take(work)
            got.append(it[0])
            self.assertNotEqual(ctx, run.browser_lock, "a lane was told to wait on the browser while %s waits" % got)
        self.assertEqual(got, ["n1", "n2", "n3"], "a lane that found the browser busy did not take the next free gate")
        last, ctx5 = run.take(work)
        self.assertEqual((last[0], ctx5), ("b2", run.browser_lock), "with only browser work left a lane must wait for it")
        with ctx1:
            pass                                          # leaving the first gate releases the browser
        self.assertTrue(run.browser_lock.acquire(False), "the browser was never given back")
        run.browser_lock.release()
        self.assertIsNone(run.take(work), "an empty queue handed out a gate")


class TheLanesStartTheBrowserChainFirst(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="h2lane.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self._sb, self._pg = H.make_sandbox, H._prove_gate
        self.addCleanup(lambda: (setattr(H, "make_sandbox", self._sb), setattr(H, "_prove_gate", self._pg),
                                 setattr(H, "_PUSH", None)))
        self.starts, self.lock = [], threading.Lock()

        def _sandbox(say=print):
            d = tempfile.mkdtemp(prefix="lane.", dir=self.root)
            os.makedirs(os.path.join(d, "tv"))
            return os.path.join(d, "tv"), d

        def _gate(sandbox, name, filename, proofs, say):
            with self.lock:
                self.starts.append(name)
            time.sleep(0.05)
            return H.PROVEN, [H.PROVEN] * len(proofs)

        H.make_sandbox, H._prove_gate = _sandbox, _gate

    def test_browser_gates_queued_last_still_start_at_once(self):
        have = [(n, n + ".py", [{"file": "x.py", "find": "a", "replace": "b", "matches": 1}])
                for n in ("n1", "n2", "n3", "n4", "b1", "b2")]
        H._PUSH = H._PushRun(order={}, browser={"b1", "b2"})
        results, _per = H._prove_gates(have, say=_quiet, workers=2)
        self.assertEqual(sorted(results), sorted(n for n, _f, _p in have), "a gate came back with no row")
        self.assertIn("b1", self.starts[:2], "the browser chain waited for the gates queued ahead of it: %s" % self.starts)


RED_PROOF = [
    {"why": "REG-1989 - the free browser is never taken first: the serial chain starts wherever fail-fast ranked it",
     "file": "heart2.py",
     "find": "            if self.browser_lock.acquire(False):\n",
     "replace": "            if False:\n",
     "matches": 1},
    {"why": "REG-1989 - a lane that finds the browser busy parks behind it while gates that need no browser wait",
     "file": "heart2.py",
     "find": "                if it[0] not in self.browser:\n",
     "replace": "                if False:\n",
     "matches": 1},
    {"why": "REG-1989 - the lanes take gates in queue order again and never ask take()",
     "file": "heart2.py",
     "find": "            if _PUSH is not None and _PUSH.browser:\n                _got = _PUSH.take(work)",
     "replace": "            if False:\n                _got = _PUSH.take(work)",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
