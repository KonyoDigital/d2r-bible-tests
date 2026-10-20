# -*- coding: utf-8 -*-
"""v3775 review B2 (REG-2296) - A GATE KILLED BY ITS CLOCK IS NEVER STORED AS A RED.

A gate that timed out on a loaded box never reached a verdict. Storing it red sent it to the red-last
queue on the next --changed run, capped at red_cap (45 s) - so a 90 s gate that once ran slow could
never pass again on unchanged bytes. Now a timeout records nothing (trace=None), the next --changed
run gives it its full g.timeout, and red_cap is never below the gate's last measured runtime.
"""
import contextlib
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

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import test_a_gate_proven_on_these_bytes_is_carried as C  # noqa: E402

# First run: the box is "loaded" (sleeps past the clock). Every later run: needs 2 s - more than the
# red cap the test sets (1 s), well inside the gate's own timeout (5 s).
_SLOW_ONCE = ("import os, sys, time\n"
              "m = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'loaded.mark')\n"
              "if not os.path.exists(m):\n"
              "    open(m, 'w').close()\n"
              "    time.sleep(30)\n"
              "time.sleep(2)\n"
              "sys.exit(0)\n")


class ATimeoutIsNotARed(unittest.TestCase):
    def _two_runs(self):
        import run_gates as RG
        root, led = C._tree({"t_slow.py": _SLOW_ONCE})
        self.addCleanup(shutil.rmtree, root, True)
        g = C._gate(root, "t_slow.py", timeout=5)
        g.name = "slow-once-fixture"
        held = RG.GATES
        RG.GATES = [g]
        out = []
        try:
            with C._Env(GITHUB_ACTIONS=None, GATE_LEDGER=None, TV_GATE_LEDGER=led, TV_RED_CAP="1",
                        TV_SELF_ARMING_LEDGER=os.path.join(tempfile.mkdtemp(prefix="tmo-q."), "q.jsonl")):
                for _ in range(2):
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf):
                        res = RG.run(live_watch=False, ledger="changed")
                    out.append(([(s, d) for _g, s, _t, d, _b in res], buf.getvalue()))
                import gate_ledger as GL
                red, _m = GL.Ledger(path=led).lookup(g, want=False)
        finally:
            RG.GATES = held
        return out, red

    def test_a_gate_that_timed_out_once_passes_on_the_next_changed_run(self):
        out, _red = self._two_runs()
        first, second = out
        self.assertEqual(first[0][0][0], "FAIL", first)
        self.assertIn("timed out", first[0][0][1])
        self.assertEqual(second[0][0][0], "PASS", "the next --changed run did not give it its full timeout: %r" % (second,))
        self.assertNotIn("still red", second[1], "a timeout was carried as a red")

    def test_nothing_red_is_stored_for_a_timeout(self):
        import run_gates as RG
        root, led = C._tree({"t_hang.py": "import time\ntime.sleep(30)\n"})
        self.addCleanup(shutil.rmtree, root, True)
        g = C._gate(root, "t_hang.py", timeout=1)
        g.name = "hang-fixture"
        held = RG.GATES
        RG.GATES = [g]
        try:
            with C._Env(GITHUB_ACTIONS=None, GATE_LEDGER=None, TV_GATE_LEDGER=led,
                        TV_SELF_ARMING_LEDGER=os.path.join(tempfile.mkdtemp(prefix="tmo-q."), "q.jsonl")):
                with contextlib.redirect_stdout(io.StringIO()):
                    res = RG.run(live_watch=False, ledger="full")
                import gate_ledger as GL
                red, _m = GL.Ledger(path=led).lookup(g, want=False)
        finally:
            RG.GATES = held
        self.assertEqual(res[0][1], "FAIL", res)
        self.assertIsNone(red, "a timeout was stored as a red: %r" % (red,))

    def test_a_timeout_clears_an_old_red(self):
        import run_gates as RG
        script = ("import os, sys, time\n"
                  "m = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'red.mark')\n"
                  "if not os.path.exists(m):\n"
                  "    open(m, 'w').close()\n"
                  "    sys.exit(1)\n"
                  "time.sleep(30)\n")
        root, led = C._tree({"t_red_then_hang.py": script})
        self.addCleanup(shutil.rmtree, root, True)
        g = C._gate(root, "t_red_then_hang.py", timeout=2)
        g.name = "red-then-hang-fixture"
        held = RG.GATES
        RG.GATES = [g]
        reds = []
        try:
            with C._Env(GITHUB_ACTIONS=None, GATE_LEDGER=None, TV_GATE_LEDGER=led,
                        TV_SELF_ARMING_LEDGER=os.path.join(tempfile.mkdtemp(prefix="tmo-q."), "q.jsonl")):
                import gate_ledger as GL
                for _ in range(2):
                    with contextlib.redirect_stdout(io.StringIO()):
                        RG.run(live_watch=False, ledger="full")
                    reds.append(GL.Ledger(path=led).lookup(g, want=False)[0])
        finally:
            RG.GATES = held
        self.assertIsNotNone(reds[0], "fixture: a real FAIL should be stored red")
        self.assertIsNone(reds[1], "a timeout left the old red in place: %r" % (reds[1],))

    def test_the_red_cap_is_never_below_the_measured_runtime(self):
        import run_gates as RG
        held = dict(RG._COSTS)
        RG._COSTS["t"] = {"costs": {"slow-red": 90.2}}
        try:
            with C._Env(TV_RED_CAP="45"):
                self.assertEqual(RG.red_cap(C._G("slow-red", ["x"], timeout=300)), 91)
                self.assertEqual(RG.red_cap(C._G("slow-red", ["x"], timeout=60)), 60)
                self.assertEqual(RG.red_cap(C._G("unknown", ["x"], timeout=300)), 45)
        finally:
            RG._COSTS.clear()
            RG._COSTS.update(held)

    def test_the_real_cost_table_is_read(self):
        import run_gates as RG
        held = dict(RG._COSTS)
        RG._COSTS.clear()
        try:
            self.assertGreater(RG._measured_cost("blueprint-agrees"), 0, "gate_costs.json rows are not read")
        finally:
            RG._COSTS.clear()
            RG._COSTS.update(held)

    def test_wilson_of_these_attacks_meets_the_bar(self):
        import confidence
        self.assertGreaterEqual(len(RED_PROOF), 10)
        self.assertGreaterEqual(confidence.wilson_lower(len(RED_PROOF), len(RED_PROOF)), 0.722)


RED_PROOF = [
    {"why": "a timeout is stored as a red", "file": "run_gates.py",
     "find": "                        led.record(g, False, trace=None)\n", "replace": "                        led.record(g, False, trace=_trace)\n", "matches": 1},
    {"why": "every run is capped at red_cap, not the gate's own timeout", "file": "run_gates.py",
     "find": "                                   timeout=red_cap(g) if _capped else g.timeout,  # GATES-RED-CAP\n",
     "replace": "                                   timeout=red_cap(g),  # GATES-RED-CAP\n", "matches": 1},
    {"why": "the timeout branch keeps an old red", "file": "run_gates.py",
     "find": "                        led.record(g, False, trace=None)\n", "replace": "                        pass\n", "matches": 1},
    {"why": "the cap ignores the measured runtime", "file": "run_gates.py",
     "find": "    cap = max(cap, _measured_cost(getattr(g, \"name\", \"\")))  # GATES-RED-CAP-MEASURED\n", "replace": "    pass\n", "matches": 1},
    {"why": "the cap takes the smaller of the two", "file": "run_gates.py",
     "find": "    cap = max(cap, _measured_cost(getattr(g, \"name\", \"\")))  # GATES-RED-CAP-MEASURED\n", "replace": "    cap = min(cap, _measured_cost(getattr(g, \"name\", \"\")) or cap)  # GATES-RED-CAP-MEASURED\n",
     "matches": 1},
    {"why": "the cost rows are read from the wrong level", "file": "run_gates.py",
     "find": "        v = float(((_COSTS[\"t\"] or {}).get(\"costs\") or {}).get(name) or 0)  # GATES-COST-ROWS\n",
     "replace": "        v = float((_COSTS[\"t\"] or {}).get(name) or 0)  # GATES-COST-ROWS\n", "matches": 1},
    {"why": "the measured cost is rounded down", "file": "run_gates.py",
     "find": "    return int(v + 0.999) if v > 0 else 0\n", "replace": "    return int(v) if v > 0 else 0\n", "matches": 1},
    {"why": "the cap ignores the gate's own timeout", "file": "run_gates.py",
     "find": "    return max(1, min(int(g.timeout or cap), cap))\n", "replace": "    return max(1, cap)\n", "matches": 1},
    {"why": "the cost table is never read", "file": "run_gates.py",
     "find": "            with open(os.path.join(HERE, \"gate_costs.json\"), encoding=\"utf-8\") as fh:\n",
     "replace": "            with open(os.devnull, encoding=\"utf-8\") as fh:\n", "matches": 1},
    {"why": "an unchanged red is never deferred, so nothing is capped", "file": "run_gates.py",
     "find": "                    if _red is not None:  # GATES-RED-DEFER\n",
     "replace": "                    if _red is not None or True:  # GATES-RED-DEFER\n", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=1)
