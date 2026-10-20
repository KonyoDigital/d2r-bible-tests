# -*- coding: utf-8 -*-
"""v3775 (REG-2296) — A RED GATE WHOSE INPUTS DID NOT MOVE IS STILL RED, AND IT IS NEVER A PASS.

Measured on a v3775 bump-only `--changed` run: 50 gates that failed in the `--full` baseline had no
stored row (a FAIL was dropped), so every one ran again at full length - 2647 of 4750 s, five of them
hanging to their 120-300 s timeouts. A bump cannot fix them.

A FAIL from a traced run is now kept in the ledger's own `reds` map, never in the PASS entries. On
`--changed`, a red gate whose inputs have not moved is announced as "still red, carried, unchanged",
sent to the back of the queue, and run once more under RED_CAP seconds. A cap hit or a failure is a
FAIL whose reason says "still red, carried, unchanged". A real pass inside the cap is a real pass,
recorded as one; nothing is ever carried green from a red row.
"""
import io
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import gate_ledger as GL  # noqa: E402
import test_a_gate_proven_on_these_bytes_is_carried as C  # noqa: E402  (its fixture tree, gate and trace helpers)

_RED = "import helper_gl\nimport sys\nprint('red')\nsys.exit(1)\n"
_SLOW_RED = "import helper_gl\nimport sys, time\ntime.sleep(20)\nsys.exit(1)\n"


def _fail(book, gate):
    """Store what one traced FAILING run of this fixture read."""
    _rc, trace = C._run_traced(gate)
    try:
        return book.record(gate, False, trace=trace)
    finally:
        os.remove(trace)


class ARedGateIsNeverCarriedAsAPass(unittest.TestCase):
    def setUp(self):
        self.held = C._Env(GITHUB_ACTIONS=None, GATE_LEDGER=None, TV_RED_CAP=None,
                           TV_SELF_ARMING_LEDGER=os.path.join(tempfile.mkdtemp(prefix="red-arm."), "arm.jsonl"))
        self.held.__enter__()
        self.addCleanup(self.held.__exit__, None, None, None)

    def _tree(self, files):
        base = {"helper_gl.py": "SALT = 1\n", "unrelated.py": "a\n"}
        base.update(files)
        root, led = C._tree(base)
        self.addCleanup(shutil.rmtree, root, True)
        return root, led

    def test_a_fail_is_kept_red_and_never_a_pass(self):
        root, led = self._tree({"t_red.py": _RED})
        gate = C._gate(root, "t_red.py")
        book = C._open(led)
        self.assertFalse(_fail(book, gate), "a FAIL reported as stored PASS")
        again = C._open(led)
        entry, why = again.lookup(gate)
        self.assertIsNone(entry, "a red row was carried as a pass")
        red, rwhy = again.lookup(gate, want=False)
        self.assertIsNotNone(red, rwhy)
        self.assertTrue(str(red.get("line") or "").startswith("red at "), red)
        self.assertNotIn("proven", str(red.get("line")))
        self.assertIs(red.get("ok"), False)

    def test_a_moved_input_is_not_an_unchanged_red(self):
        root, led = self._tree({"t_red.py": _RED})
        gate = C._gate(root, "t_red.py")
        _fail(C._open(led), gate)
        with io.open(os.path.join(root, "tv", "helper_gl.py"), "a", encoding="utf-8") as fh:
            fh.write("# moved\n")
        red, _why = C._open(led).lookup(gate, want=False)
        self.assertIsNone(red, "a red gate whose input moved was called unchanged")

    def test_an_unrelated_edit_keeps_it_red_and_unchanged(self):
        root, led = self._tree({"t_red.py": _RED})
        gate = C._gate(root, "t_red.py")
        _fail(C._open(led), gate)
        with io.open(os.path.join(root, "tv", "unrelated.py"), "a", encoding="utf-8") as fh:
            fh.write("b\n")
        red, why = C._open(led).lookup(gate, want=False)
        self.assertIsNotNone(red, why)

    def test_a_later_pass_clears_the_red(self):
        root, led = self._tree({"t_red.py": _RED, "t_ok.py": C._LAW})
        gate = C._gate(root, "t_red.py")
        _fail(C._open(led), gate)
        ok = C._gate(root, "t_ok.py")
        book = C._open(led)
        book.reds[gate.name] = dict(book.reds.get(gate.name) or {})
        self.assertTrue(C._prove(book, ok), book.last_why)  # same fixture name: the pass replaces the red
        red, _why = C._open(led).lookup(gate, want=False)
        self.assertIsNone(red, "a red row survived a pass of the same gate")

    def test_two_books_keep_each_others_reds(self):
        root, led = self._tree({"t_red.py": _RED, "t_ok.py": C._LAW})
        red_gate = C._gate(root, "t_red.py")
        red_gate.name = "red-one"
        ok_gate = C._gate(root, "t_ok.py")
        ok_gate.name = "green-two"
        first, second = C._open(led), C._open(led)
        second._ensure()
        _fail(first, red_gate)
        self.assertTrue(C._prove(second, ok_gate), second.last_why)
        red, why = C._open(led).lookup(red_gate, want=False)
        self.assertIsNotNone(red, "a second writer dropped the first writer's red: %s" % why)

    def test_the_cap_is_tight_and_never_longer_than_the_gate(self):
        import run_gates as RG
        g = C._G("x", [], timeout=300)
        self.assertEqual(RG.red_cap(g), RG.RED_CAP)
        self.assertLessEqual(RG.RED_CAP, 60)
        self.assertEqual(RG.red_cap(C._G("x", [], timeout=10)), 10)
        with C._Env(TV_RED_CAP="3"):
            self.assertEqual(RG.red_cap(g), 3)


class TheRunnerRunsAnUnchangedRedLastAndKeepsItRed(unittest.TestCase):
    def setUp(self):
        self.held = C._Env(GITHUB_ACTIONS=None, GATE_LEDGER=None, TV_RED_CAP="2", TV_SELF_ARMING_DEFER=None,
                           TV_SELF_ARMING_LEDGER=os.path.join(tempfile.mkdtemp(prefix="red-arm."), "arm.jsonl"))
        self.held.__enter__()
        self.addCleanup(self.held.__exit__, None, None, None)

    def _run(self, files, names):
        import run_gates as RG
        base = {"helper_gl.py": "SALT = 1\n"}
        base.update(files)
        root, led = C._tree(base)
        self.addCleanup(shutil.rmtree, root, True)
        gates = []
        for fname, gname in names:
            g = C._gate(root, fname, timeout=60)
            g.name = gname
            gates.append(g)
        held = RG.GATES
        RG.GATES = gates
        try:
            with C._Env(TV_GATE_LEDGER=led):
                book = GL.Ledger(path=led)  # the real tool probes, as run() takes them
                for g in gates:
                    if g.name.startswith("red"):
                        _fail(book, g)
                    else:
                        C._prove(book, g)
                C._write(root, "tv/unrelated.py", "a\n")
                C._commit(root, "an unrelated commit")
                t0 = time.time()
                res = RG.run(live_watch=False, ledger="changed")
                return res, time.time() - t0
        finally:
            RG.GATES = held

    def test_a_hung_red_is_capped_last_and_stays_red(self):
        res, dt = self._run({"t_slow.py": _SLOW_RED, "t_ok.py": C._LAW},
                            [("t_slow.py", "red-slow"), ("t_ok.py", "green")])
        names = [(g.name, s) for g, s, _dt, _d, _b in res]
        self.assertIn(("red-slow", "FAIL"), names, names)
        self.assertNotIn(("red-slow", "PASS"), names)
        self.assertNotIn(("red-slow", "CARRY"), names)
        self.assertEqual(names[-1][0], "red-slow", "the unchanged red did not run last: %s" % names)
        detail = [d for g, s, _dt, d, _b in res if g.name == "red-slow"][0]
        self.assertIn("still red, carried, unchanged", detail)
        self.assertLess(dt, 15, "the red ran its full 20 s instead of the cap")

    def test_a_fast_red_says_still_red(self):
        res, _dt = self._run({"t_red.py": _RED}, [("t_red.py", "red-fast")])
        rows = [(s, d) for g, s, _dt, d, _b in res if g.name == "red-fast"]
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual(rows[0][0], "FAIL")
        self.assertTrue(rows[0][1].startswith("still red, carried, unchanged"), rows)

    def test_wilson_of_these_attacks_meets_the_bar(self):
        import confidence
        self.assertGreaterEqual(len(RED_PROOF), 10)
        self.assertGreaterEqual(confidence.wilson_lower(len(RED_PROOF), len(RED_PROOF)), 0.722)


RED_PROOF = [
    {"why": "a FAIL is stored as a PASS", "file": "gate_ledger.py",
     "find": "        red = ok is not True\n", "replace": "        red = False\n", "matches": 1},
    {"why": "a FAIL is not kept in the red map", "file": "gate_ledger.py",
     "find": "        if red:  # LEDGER-RED-STORE", "replace": "        if False:  # LEDGER-RED-STORE", "matches": 1},
    {"why": "a red line says proven", "file": "gate_ledger.py",
     "find": "            line = \"red\" + line[len(\"proven\"):]  # LEDGER-RED-LINE",
     "replace": "            pass  # LEDGER-RED-LINE", "matches": 1},
    {"why": "the red lookup reads the PASS book", "file": "gate_ledger.py",
     "find": "        book = self.entries if want is True else self.reds\n",
     "replace": "        book = self.entries\n", "matches": 1},
    {"why": "reds are not loaded back", "file": "gate_ledger.py",
     "find": "                self.reds = dict(reds) if isinstance(reds, dict) else {}  # LEDGER-REDS-LOAD",
     "replace": "                self.reds = {}  # LEDGER-REDS-LOAD", "matches": 1},
    {"why": "reds are not written", "file": "gate_ledger.py",
     "find": "\"entries\": self.entries, \"reds\": self.reds}", "replace": "\"entries\": self.entries}",
     "matches": 1},
    {"why": "a pass leaves the red row", "file": "gate_ledger.py",
     "find": "        self._drop_red(name, write=False)\n", "replace": "        pass\n", "matches": 1},
    {"why": "a second writer drops the first writer's reds", "file": "gate_ledger.py",
     "find": "                if isinstance(entry, dict) and entry.get(\"ok\") is False and entry.get(\"gate\") == name:\n",
     "replace": "                if False:\n", "matches": 1},
    {"why": "an unchanged red is never queued again", "file": "run_gates.py",
     "find": "                    _queue.append(g)\n", "replace": "                    pass\n", "matches": 1},
    {"why": "the capped rerun gets the gate's full timeout", "file": "run_gates.py",
     "find": "                               timeout=red_cap(g) if _capped else g.timeout,  # GATES-RED-CAP\n",
     "replace": "                               timeout=g.timeout,  # GATES-RED-CAP\n", "matches": 1},
    {"why": "a cap hit does not say still red", "file": "run_gates.py",
     "find": "            if _capped:  # GATES-RED-STAYS-RED\n", "replace": "            if False:  # GATES-RED-STAYS-RED\n",
     "matches": 1},
    {"why": "the cap is not bounded", "file": "run_gates.py",
     "find": "    return max(1, min(int(g.timeout or cap), cap))\n", "replace": "    return int(g.timeout or cap)\n",
     "matches": 1},
    {"why": "a fast red does not say still red", "file": "run_gates.py",
     "find": "            if _capped and status == \"FAIL\":\n", "replace": "            if False:\n", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=1)
