# -*- coding: utf-8 -*-
"""REG-1989 - A PROVING LANE NEVER PARKS BEHIND THE ONE BROWSER WHILE OTHER WORK WAITS, AND THE BROWSER CHAIN GOES FIRST.

MEASURED on the v3602 push (131 gates, 11 of them reach a browser through their imports and are proved one at a time):
the lanes took gates in queue order, so the serial browser chain started wherever fail-fast happened to rank its first
gate, and a lane that took a browser gate while another lane held the browser WAITED, holding that gate. For the tail of
the run one law was running and three lanes sat idle behind it. _PushRun.take() now hands a lane the free browser first
(the serial chain is the critical path), the next gate that needs no browser when it is busy, and makes a lane wait only
when nothing else is left.

#160 (REG-2439) - "the one browser" is a law's own process. heart2's own process proves browser gates under the
machine's K browser slots (lane_ports.BrowserSemaphore, K = min(HEART2_BROWSER_SLOTS, 2), counted across every prover on
the machine): take() hands a browser gate to each lane while a slot is free, a lane that finds all K busy takes the next
gate that needs none, and only with nothing else left does it wait. Driven through the real semaphore over this law's own
slot dir (use_law_slots), never the machine's.

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
from console_safe import enable; enable()  # noqa: E402
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


class _Lane(object):
    """One lane thread: it calls take() and HOLDS what it was handed (a browser slot is held by the thread that took
    it) until released - then leaves the gate's context in that same thread."""

    def __init__(self, run, work):
        self.got, self.took, self.go = None, threading.Event(), threading.Event()
        self.t = threading.Thread(target=self._body, args=(run, work))
        self.t.daemon = True
        self.t.start()
        self.took.wait(10)

    def _body(self, run, work):
        self.got = run.take(work)
        self.took.set()
        self.go.wait(10)
        if self.got is not None and isinstance(self.got[1], H._HeldLock):
            with self.got[1]:
                pass

    def release(self):
        self.go.set()
        self.t.join(10)


class TakeOrderUnderTheMachinesSlots(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="h2slots.")
        self.addCleanup(shutil.rmtree, self.d, True)
        saved = (os.environ.get("HEART2_LANES_DIR"), os.environ.get("HEART2_BROWSER_SLOTS"), dict(H._SLOTS_LAW))

        def restore():
            for k, v in (("HEART2_LANES_DIR", saved[0]), ("HEART2_BROWSER_SLOTS", saved[1])):
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            H._SLOTS_LAW.clear()
            H._SLOTS_LAW.update(saved[2])
        self.addCleanup(restore)
        os.environ.pop("HEART2_BROWSER_SLOTS", None)
        H.use_law_slots(os.path.join(self.d, "lanes"))

    def test_two_lanes_take_the_two_free_slots_and_a_third_takes_other_work(self):
        """★ K = 2: two lanes are each handed a browser gate (each holding one of the machine's slots), a third lane -
        both slots busy - is handed the gates that need no browser, and with only browser work left it waits; when the
        slots come back a lane that waits gets one"""
        import lane_ports as LP
        run = H._PushRun(order={}, browser={"b1", "b2", "b3"})
        self.assertIsInstance(run.browser_lock, LP.BrowserSemaphore, "a push in heart2's process counts only its own "
                                                                      "browser, not the machine's K slots")
        work = _q(["n1", "b1", "b2", "n2", "b3"])
        one, two = _Lane(run, work), _Lane(run, work)
        try:
            self.assertEqual((one.got[0][0], two.got[0][0]), ("b1", "b2"),
                             "two lanes were not each handed a browser gate while a slot was free")
            self.assertTrue(isinstance(one.got[1], H._HeldLock) and isinstance(two.got[1], H._HeldLock),
                            "a lane was handed a browser gate without holding a slot")
            got = []
            for _ in range(2):
                three = _Lane(run, work)
                got.append((three.got[0][0], three.got[1] is run.browser_lock))
                three.release()
            self.assertEqual(got, [("n1", False), ("n2", False)],
                             "with both slots busy a lane did not take the next gate that needs no browser: %s" % got)
            last = _Lane(run, work)
            self.assertEqual((last.got[0][0], last.got[1] is run.browser_lock), ("b3", True),
                             "with only browser work left and both slots busy, a lane must wait for one")
            last.release()
        finally:
            one.release()
            two.release()
        ok = run.browser_lock.acquire(False)
        self.assertTrue(ok, "the slots were never given back")
        run.browser_lock.release()


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
    {"why": "#160 - take() counts this process's one browser again, not the machine's K slots: a second lane never "
            "gets the second slot",
     "file": "heart2.py",
     "find": "        self.browser_lock = _machine_browser_lock()   # #160 (REG-2439) - the machine's K browser slots, not "
             "this process's\n",
     "replace": "        self.browser_lock = threading.Lock()   # #160 (REG-2439) - the machine's K browser slots, not "
                "this process's\n",
     "matches": 1},
    {"why": "REG-1989 - the lanes take gates in queue order again and never ask take()",
     "file": "heart2.py",
     "find": "            if _PUSH is not None and _PUSH.browser:\n                _got = _PUSH.take(work)",
     "replace": "            if False:\n                _got = _PUSH.take(work)",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
