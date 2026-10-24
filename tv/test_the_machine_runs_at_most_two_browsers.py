# -*- coding: utf-8 -*-
"""#160 (REG-2439) - ACROSS EVERY PROVER ON THIS MACHINE, AT MOST TWO BROWSER GATES RUN AT ONCE.

His ruling: at most two headless Chromes at once on his Mac (four parallel Chrome lanes drove it to load 100 on
2026-09-28). MEASURED at 7285e7efc: _PushRun.browser_lock was a threading.Lock - one per PROCESS - and the census held no
browser lock at all, so his self-prover's lanes plus any push (or a worktree's pre-flight) ran as many Chromes as they
had lanes. heart2 now proves a browser gate - push or census - under one of the machine's K browser slots
(lane_ports.BrowserSemaphore, K = min(HEART2_BROWSER_SLOTS, 2)).

Driven with THREE real prover processes sharing one slot directory (this law's own, named with use_law_slots): a push over two
browser gates in two lanes, a push over one, and a census over one - each through the REAL _PushRun / _CensusRun,
_prove_gates, _prove_lane, take() and _browser_slot; only the sandbox build and the gate itself are stand-ins (a gate
records when it starts and ends and holds for a while). Released together; the most gates running at one moment, across
all three, is two - and it IS two (the cap is reached, not just respected).
RED_PROOF below.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable; enable()  # noqa: E402
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

#: one prover: argv = role, gate names...; it waits for the "go" file, then proves its browser gates in its own lanes
_PROVER = r'''
import io, os, sys, tempfile, time
tv, role, names = sys.argv[1], sys.argv[2], sys.argv[3:]
sys.path.insert(0, tv)
import heart2 as H
H.use_law_slots(os.environ["HEART2_LANES_DIR"])          # this law's slot dir - a prover script opts in, never by env alone
log, go = os.environ["BROWSER_LOG"], os.environ["BROWSER_GO"]


def gate(sandbox, name, filename, proofs, say):
    with io.open(log, "a", encoding="utf-8") as fh:
        fh.write("start %s %.4f\n" % (name, time.time()))
    time.sleep(1.5)
    with io.open(log, "a", encoding="utf-8") as fh:
        fh.write("end %s %.4f\n" % (name, time.time()))
    return H.PROVEN, [H.PROVEN] * len(proofs)


def sandbox(say=print):
    d = tempfile.mkdtemp(prefix="browserlane.")
    os.makedirs(os.path.join(d, "tv"))
    return os.path.join(d, "tv"), d


H.make_sandbox, H._prove_gate = sandbox, gate
have = [(n, n + ".py", [{"file": "x.py", "find": "a", "replace": "b", "matches": 1}]) for n in names]
if role == "census":
    run = H._CensusRun(cache=None, red=False)
    run.browser, run.browser_lock = set(names), H._machine_browser_lock(lambda *a, **k: None)
    H._CENSUS = run
else:
    H._PUSH = H._PushRun(order={}, browser=set(names))
with io.open(os.path.join(os.path.dirname(go), "ready." + role), "w") as fh:
    fh.write("ready")
while not os.path.exists(go):
    time.sleep(0.05)
H._prove_gates(have, say=lambda *a, **k: None, workers=len(names))
'''


class AtMostTwoBrowsersAcrossProvers(unittest.TestCase):

    def test_three_provers_never_hold_more_than_two_browsers(self):
        d = tempfile.mkdtemp(prefix="browsers_")
        self.addCleanup(shutil.rmtree, d, True)
        script = os.path.join(d, "prover.py")
        with io.open(script, "w", encoding="utf-8") as fh:
            fh.write(_PROVER)
        log, go = os.path.join(d, "spans.log"), os.path.join(d, "go")
        env = dict((k, v) for k, v in os.environ.items() if not k.upper().startswith(("GIT_", "HEART2_")))
        env.update(HEART2_LANES_DIR=os.path.join(d, "lanes"), BROWSER_LOG=log, BROWSER_GO=go, PYTHONDONTWRITEBYTECODE="1")
        roles = (("push2", ["g1", "g2"]), ("push1", ["g3"]), ("census", ["g4"]))
        procs = [subprocess.Popen([sys.executable, script, HERE, role] + names, env=env, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT) for role, names in roles]
        try:
            deadline = time.time() + 60
            while time.time() < deadline and not all(os.path.exists(os.path.join(d, "ready." + r)) for r, _n in roles):
                time.sleep(0.05)
            self.assertTrue(all(os.path.exists(os.path.join(d, "ready." + r)) for r, _n in roles),
                            "PREMISE: the three provers never became ready")
            with io.open(go, "w") as fh:
                fh.write("go")
            outs = [p.communicate(timeout=120)[0].decode("utf-8", "replace") for p in procs]
        finally:
            for p in procs:
                if p.poll() is None:
                    p.kill()
        self.assertEqual([p.returncode for p in procs], [0, 0, 0], "a prover failed:\n%s" % "\n".join(outs))
        with io.open(log, encoding="utf-8") as fh:
            ev = [l.split() for l in fh if l.strip()]
        starts = [e for e in ev if e[0] == "start"]
        self.assertEqual(sorted(e[1] for e in starts), ["g1", "g2", "g3", "g4"], "PREMISE: not every gate ran: %s" % ev)
        timeline = sorted((float(t), 1 if k == "start" else -1) for k, _g, t in ev)
        now = peak = 0
        for _t, step in sorted(timeline, key=lambda x: (x[0], x[1])):
            now += step
            peak = max(peak, now)
        self.assertLessEqual(peak, 2, "%d browser gates ran at once across three provers - his ruling is two: %s"
                             % (peak, ev))
        self.assertEqual(peak, 2, "PREMISE: the provers never overlapped - the cap was never reached, so never tested: "
                                  "%s" % ev)


class ASeamedProverNeverFlipsTheLawsItProves(unittest.TestCase):

    def setUp(self):
        import heart2 as H
        self.H = H
        self.d = tempfile.mkdtemp(prefix="seamed_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.old_env, self.old_law = os.environ.get("HEART2_LANES_DIR"), dict(H._SLOTS_LAW)
        self.addCleanup(self._restore)

    def _restore(self):
        self.H._SLOTS_LAW.clear()
        self.H._SLOTS_LAW.update(self.old_law)
        if self.old_env is None:
            os.environ.pop("HEART2_LANES_DIR", None)
        else:
            os.environ["HEART2_LANES_DIR"] = self.old_env

    def test_an_inherited_slot_dir_opts_nothing_in_and_never_reaches_a_law_run(self):
        """★ every law run inherits its prover's environment. MEASURED: a prover seamed with HEART2_LANES_DIR flipped the
        laws it proved onto that dir - test_a_lane_never_waits_on_the_browser_while_work_waits read ALREADY RED
        untampered in its sandbox. A process that only INHERITED the variable has no slots in play (a push's browser lock
        is its own process's), heart2 hands no law run the prover's slot dir, and a law that opts in with its own dir
        does get slots"""
        H = self.H
        lanes = os.path.join(self.d, "lanes")
        self.H._SLOTS_LAW["dir"] = None
        os.environ["HEART2_LANES_DIR"] = lanes
        self.assertFalse(H._slots_in_play(), "an INHERITED HEART2_LANES_DIR put the machine's slots in play in a law's "
                                             "process - a seamed prover flips every law it proves")
        import lane_ports as LP
        self.assertNotIsInstance(H._PushRun(order={}, browser={"b"}).browser_lock, LP.BrowserSemaphore,
                                 "a law's in-process push took the machine's browser slots from an inherited variable")
        tv = os.path.join(self.d, "box", "repo", "tv")
        os.makedirs(tv)
        open(os.path.join(tv, "seam_probe.py"), "w").close()
        ok, tail = H._run_gate(tv, "seam_probe.py", timeout=60,
                               script="import os\nprint('LANES=[%s]' % os.environ.get('HEART2_LANES_DIR', ''))\n")
        self.assertTrue(ok, "PREMISE: the probe did not run: %r" % tail)
        self.assertIn("LANES=[]", tail, "a law run inherited the prover's slot dir - a prover it starts counts this "
                                        "one as a sibling: %r" % tail)
        H.use_law_slots(lanes)
        self.assertTrue(H._slots_in_play(), "a law that named its own slot dir got no slots - the opt-in is dead")
        self.assertIsInstance(H._PushRun(order={}, browser={"b"}).browser_lock, LP.BrowserSemaphore,
                              "PREMISE: an opted-in push does not take the machine's browser slots")


RED_PROOF = [
    {"why": "#160 - each prover counts only its own Chromes again (a per-process lock): three provers run three",
     "file": "heart2.py",
     "find": "    if _slots_in_play():\n        try:\n            import lane_ports as _lp\n            return "
             "_lp.BrowserSemaphore(say=say)\n",
     "replace": "    if False:\n        try:\n            import lane_ports as _lp\n            return "
                "_lp.BrowserSemaphore(say=say)\n",
     "matches": 1},
    {"why": "#160 - the census's browser gates run free beside a push's Chromes",
     "file": "heart2.py",
     "find": "        return _CENSUS.browser_lock                          # CENSUS-BROWSER-SLOT\n",
     "replace": "        return contextlib.nullcontext()                      # CENSUS-BROWSER-SLOT\n",
     "matches": 1},
    {"why": "#160 - the machine's cap is three Chromes, not his two",
     "file": "lane_ports.py",
     "find": "BROWSER_CAP = 2 ",
     "replace": "BROWSER_CAP = 3 ",
     "matches": 1},
    {"why": "#160 - an inherited HEART2_LANES_DIR opts a law's process into the machine's slots again: a seamed prover "
            "flips every law it proves",
     "file": "heart2.py",
     "find": "    return bool(d) and os.environ.get(\"HEART2_LANES_DIR\") == d               # LAW-OPTS-IN\n",
     "replace": "    return bool(os.environ.get(\"HEART2_LANES_DIR\"))               # LAW-OPTS-IN\n",
     "matches": 1},
    {"why": "#160 - a law run inherits the prover's slot dir again",
     "file": "heart2.py",
     "find": "    env.pop(\"HEART2_LANES_DIR\", None)                                        # NO-INHERITED-SLOTS\n",
     "replace": "    pass                                        # NO-INHERITED-SLOTS\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
