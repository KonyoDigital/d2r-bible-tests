# -*- coding: utf-8 -*-
"""#160 (REG-2452) - TWO PROVERS ON ONE MACHINE NEVER SHARE A LANE PORT, AND NEVER RUN MORE THAN TWO CHROMES.

MEASURED at HEAD 7285e7efc: lane_ports.base_for_lane(n) was BASE0 + (n-1)*STRIDE in EVERY process, so the census and a
push (or a worktree's pre-flight) proving at once bound the SAME ports - and a request from one sandbox on a listener the
other holds is how a tracked file was deleted (test_a_prove_lane_keeps_its_own_port). stamp() never set TV_RENDER_PORT,
so every lane inherited the hook's one render port; nothing capped Chrome machine-wide. Driven here with REAL processes
and a slot directory in this law's own scratch (HEART2_LANES_DIR):

  1. two prover processes claim two different slots, and every port either one's 16 lanes could bind (agent, control,
     law, render) is disjoint from the other's, clear of his reserved ports and of shard_suite's range; slot 0 is the
     numbering every caller had before;
  2. a holder that DIES (killed, no clean-up) frees its slot;
  3. never more than two browser slots are held machine-wide - three processes asking at once, even with
     HEART2_BROWSER_SLOTS=3, get two; one given back is taken again; the waiting form waits and then gets it;
  4. stamp() gives each lane its own TV_RENDER_PORT (its spare, base+3), over the one the hook exports.
RED_PROOF below.
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402  (the docstrings carry non-ASCII)
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import lane_ports as LP  # noqa: E402

_PROVER = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
import lane_ports as LP
kind = sys.argv[2]
if kind == "prover":
    n = LP.claim_slot(wait_s=0)
    ports = [LP.base_for_lane(l, n) + i for l in range(1, LP.LANES_PER_SLOT + 1) for i in range(LP.STRIDE)]
    out = {"slot": n, "ports": ports}
else:
    s = LP.try_browser_slot()
    out = {"held": s is not None, "index": s.index if s is not None else None}
sys.stdout.write("READY " + json.dumps(out) + "\n")
sys.stdout.flush()
sys.stdin.read()                      # held until the law closes stdin (or kills this process)
'''


class TwoProversNeverShareALanePort(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="lanes-")
        env = mock.patch.dict(os.environ, {LP.ENV_LANES_DIR: self.dir})
        env.start()
        self.addCleanup(env.stop)
        self.procs = []
        self.addCleanup(self._reap)

    def _reap(self):
        for p in self.procs:
            if p.poll() is None:
                p.kill()
            try:
                p.wait(timeout=10)
            except Exception:
                pass
            for f in (p.stdin, p.stdout):
                try:
                    f.close()
                except Exception:
                    pass

    def _spawn(self, kind, **extra):
        env = dict((k, v) for k, v in os.environ.items() if not k.startswith("GIT_"))
        env.update(extra)
        env["PYTHONIOENCODING"] = "utf-8"
        p = subprocess.Popen([sys.executable, "-c", _PROVER, HERE, kind], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env, text=True,
                             encoding="utf-8", errors="replace")
        self.procs.append(p)
        line = p.stdout.readline()
        self.assertTrue(line.startswith("READY "), "a %s process never reported: %r" % (kind, line))
        return p, json.loads(line[len("READY "):])

    # 1 ---------------------------------------------------------------------------------------------------------------
    def test_two_provers_hold_two_slots_and_disjoint_ports(self):
        _a, ra = self._spawn("prover")
        _b, rb = self._spawn("prover")
        self.assertNotEqual(ra["slot"], rb["slot"], "two live provers were handed ONE slot: %r %r" % (ra, rb))
        shared = set(ra["ports"]) & set(rb["ports"])
        self.assertEqual(shared, set(), "two provers' lanes share %d port(s), e.g. %s - the listener one sandbox's "
                                        "request reaches in the other" % (len(shared), sorted(shared)[:4]))
        for r in (ra, rb):
            self.assertEqual(len(set(r["ports"])), len(r["ports"]), "one prover's own lanes overlap")
            for port in r["ports"]:
                self.assertNotIn(port, LP.FORBIDDEN, "lane port %d is one of his reserved ports" % port)
                self.assertFalse(LP.SHARD_PORTS[0] <= port < LP.SHARD_PORTS[1], "lane port %d is shard_suite's" % port)
        import shard_suite
        self.assertTrue(LP.SHARD_PORTS[0] <= shard_suite.PORT_BASE < LP.SHARD_PORTS[1],
                        "shard_suite moved its ports (%d) out of the range lane_ports keeps clear" % shard_suite.PORT_BASE)
        for n in range(1, LP.LANES_PER_SLOT + 1):
            self.assertEqual(LP.base_for_lane(n), LP.BASE0 + (n - 1) * LP.STRIDE,
                             "slot 0 is no longer the numbering every caller had before #160")
            self.assertEqual(LP.base_for_lane(n, 0), LP.base_for_lane(n))

    # 2 ---------------------------------------------------------------------------------------------------------------
    def test_a_dead_holders_slot_is_free_again(self):
        a, ra = self._spawn("prover")
        path = os.path.join(self.dir, "slot-%d.lock" % ra["slot"])
        fh, how = LP._try_lock(path)
        if how is None:
            self.skipTest("no file lock on this machine - the slot cannot be held, which claim_slot says")
        self.assertIsNone(fh, "a live prover's slot could be taken by another process")
        a.kill()
        a.wait(timeout=10)
        deadline, fh = time.time() + 15, None
        while fh is None and time.time() < deadline:
            fh, _how = LP._try_lock(path)
            if fh is None:
                time.sleep(0.1)
        self.assertIsNotNone(fh, "slot %d stayed held after its prover was killed" % ra["slot"])
        fh.close()
        _b, rb = self._spawn("prover")
        self.assertEqual(rb["slot"], ra["slot"], "the next prover did not get the freed slot back: %r" % rb)

    # 3 ---------------------------------------------------------------------------------------------------------------
    def test_never_more_than_two_browser_slots_machine_wide(self):
        got = [self._spawn("browser", **{LP.ENV_BROWSER_SLOTS: "3"})[1] for _ in range(3)]
        held = [g for g in got if g["held"]]
        self.assertEqual(len(held), 2, "%d headless Chromes were allowed at once across this machine (his ruling: "
                                       "two): %r" % (len(held), got))
        self.assertEqual(sorted(g["index"] for g in held), [0, 1])
        self.assertIsNone(LP.try_browser_slot(), "this process took a third browser slot while two were held")
        self.assertIsNone(LP.browser_slot(timeout=0.3), "the waiting form handed out a third slot")
        holder = self.procs[[g["held"] for g in got].index(True)]
        holder.kill()
        holder.wait(timeout=10)
        s = LP.browser_slot(timeout=15)
        self.assertIsNotNone(s, "a browser slot its holder gave up (by dying) was never handed out again")
        s.release()
        sem = LP.BrowserSemaphore()
        self.assertTrue(sem.acquire(False))
        other = []
        t = threading.Thread(target=lambda: other.append(sem.acquire(False)))
        t.start()
        t.join()
        self.assertEqual(other, [False], "a second thread took a slot while every one was held")
        sem.release()

    # 4 ---------------------------------------------------------------------------------------------------------------
    def test_each_lane_renders_on_its_own_port(self):
        seen = {}
        for slot in (0, 1, LP.SLOTS - 1):
            for lane in (1, 2, LP.LANES_PER_SLOT):
                env = LP.stamp({"TV_RENDER_PORT": "9224"}, lane, slot)   # the one port the hook exports to everyone
                b = LP.base_for_lane(lane, slot)
                self.assertEqual(env["TV_RENDER_PORT"], str(b + 3),
                                 "lane %d of slot %d renders on %r, not its own spare" % (lane, slot,
                                                                                      env.get("TV_RENDER_PORT")))
                self.assertNotIn(env["TV_RENDER_PORT"], seen, "two lanes render on one port")
                seen[env["TV_RENDER_PORT"]] = (slot, lane)
        self.assertEqual(LP.stamp({}, 3)["TV_LAW_PORT"], str(LP.base_for_lane(3) + 2), "the law port moved")


RED_PROOF = [
    {"why": "#160 - the base comes from the lane number alone again: the census and a push bind the same ports",
     "file": "lane_ports.py",
     "find": "    b += _slot(slot) * SLOT_SPAN\n",
     "replace": "    pass\n",
     "matches": 1},
    {"why": "#160 - three headless Chromes at once on his Mac (his ruling is two)",
     "file": "lane_ports.py",
     "find": "    return max(1, min(k, BROWSER_CAP))\n",
     "replace": "    return max(1, min(k, 3))\n",
     "matches": 1},
    {"why": "#160 - stamp() leaves TV_RENDER_PORT alone: every lane renders on the one port the hook exported",
     "file": "lane_ports.py",
     "find": "    env[\"TV_RENDER_PORT\"] = str(b + 3)\n",
     "replace": "    pass\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
