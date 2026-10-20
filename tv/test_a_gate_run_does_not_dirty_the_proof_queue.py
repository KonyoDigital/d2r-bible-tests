# -*- coding: utf-8 -*-
"""v3775 (REG-2296) — A GATE RUN DOES NOT DIRTY THE TRACKED PROOF QUEUE WHILE OTHER GATES ARE PROVED.

The Wilson gates bank into tv/.self_arming.jsonl. Mid-run that made a tracked input of 147 gates
dirty, so each of those passes was refused ("proved on uncommitted tv/.self_arming.jsonl, not on the
commit") and ran again on the next bump - 599 s of a 4750 s bump-only run.

While run_gates records proofs it points TV_SELF_ARMING_DEFER at a scratch file outside the checkout.
self_arming._bank_path sends a row bound for the DEFAULT queue there (a fixture that redirected the
queue still writes where it pointed), and run_gates folds the scratch rows into the queue after the
last gate, then removes the scratch file. Nothing banked is lost; it lands after the proofs.
"""
import io
import json
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

import gate_ledger as GL  # noqa: E402
import self_arming as SA  # noqa: E402
import test_a_gate_proven_on_these_bytes_is_carried as C  # noqa: E402

_BANKER = ("import os, sys\n"
           "p = os.environ.get('TV_SELF_ARMING_DEFER') or ''\n"
           "print('DEFER=' + p)\n"
           "if p:\n"
           "    open(p, 'a').write('{\"lock\": \"x\", \"src\": \"fixture\"}\\n')\n"
           "sys.exit(0)\n")


class TheBankIsDeferredOnlyForTheDefaultQueue(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="arm-defer.")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_a_default_queue_row_goes_to_the_scratch_file(self):
        d = os.path.join(self.tmp, "defer.jsonl")
        with C._Env(TV_SELF_ARMING_LEDGER=None, TV_SELF_ARMING_DEFER=d):
            self.assertEqual(SA._bank_path(), d)

    def test_without_a_defer_the_queue_is_the_queue(self):
        with C._Env(TV_SELF_ARMING_LEDGER=None, TV_SELF_ARMING_DEFER=None):
            self.assertEqual(os.path.abspath(SA._bank_path()), os.path.abspath(SA.LEDGER))

    def test_a_redirected_fixture_queue_is_never_deferred(self):
        mine = os.path.join(self.tmp, "mine.jsonl")
        with C._Env(TV_SELF_ARMING_LEDGER=mine, TV_SELF_ARMING_DEFER=os.path.join(self.tmp, "d.jsonl")):
            self.assertEqual(SA._bank_path(), mine)

    def test_both_writers_append_through_the_bank_path(self):
        import inspect
        for writer in ("bank", "record"):
            body = inspect.getsource(getattr(SA, writer))
            self.assertIn("io.open(_bank_path(), \"a\"", body, "%s() appends to the queue directly" % writer)
            self.assertNotIn("io.open(_ledger_path(), \"a\"", body)

    def test_fold_appends_rows_and_refuses_what_is_not_a_row(self):
        q = os.path.join(self.tmp, "queue.jsonl")
        d = os.path.join(self.tmp, "defer.jsonl")
        with io.open(q, "w", encoding="utf-8") as fh:
            fh.write('{"old": 1}\n')
        with io.open(d, "w", encoding="utf-8") as fh:
            fh.write('{"new": 2}\n[1]\nnot json\n{"new": 3}\n')
        with C._Env(TV_SELF_ARMING_LEDGER=q, TV_SELF_ARMING_DEFER=None):
            n, bad = SA.fold_deferred(d)
        self.assertEqual((n, bad), (2, 2))
        with io.open(q, encoding="utf-8") as fh:
            rows = [json.loads(x) for x in fh.read().splitlines() if x.strip()]
        self.assertEqual(rows, [{"old": 1}, {"new": 2}, {"new": 3}])

    def test_fold_of_nothing_is_nothing(self):
        with C._Env(TV_SELF_ARMING_LEDGER=os.path.join(self.tmp, "q.jsonl")):
            self.assertEqual(SA.fold_deferred(os.path.join(self.tmp, "absent.jsonl")), (0, 0))


class TheRunnerDefersAndFolds(unittest.TestCase):
    def _run(self, preset=None):
        import run_gates as RG
        root, led = C._tree({"t_bank.py": _BANKER})
        self.addCleanup(shutil.rmtree, root, True)
        q = os.path.join(tempfile.mkdtemp(prefix="arm-q."), "queue.jsonl")
        g = C._gate(root, "t_bank.py")
        g.name = "banker"
        held = RG.GATES
        RG.GATES = [g]
        try:
            with C._Env(GITHUB_ACTIONS=None, GATE_LEDGER=None, TV_GATE_LEDGER=led,
                        TV_SELF_ARMING_LEDGER=q, TV_SELF_ARMING_DEFER=preset):
                res = RG.run(live_watch=False, ledger="full")
                after = os.environ.get("TV_SELF_ARMING_DEFER")
        finally:
            RG.GATES = held
        return res, q, after

    def test_the_gate_sees_a_scratch_file_outside_the_checkout_and_it_is_folded(self):
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res, q, after = self._run()
        self.assertEqual([s for _g, s, _t, _d, _b in res], ["PASS"], res)
        self.assertIsNone(after, "the runner left TV_SELF_ARMING_DEFER set")
        with io.open(q, encoding="utf-8") as fh:
            self.assertIn('"src": "fixture"', fh.read(), "the deferred row was not folded into the queue")

    def test_the_scratch_file_is_removed(self):
        import run_gates as RG
        seen = []
        real = RG.subprocess.run

        def spy(*a, **kw):
            env = kw.get("env") or {}
            if env.get("TV_SELF_ARMING_DEFER"):
                seen.append(env["TV_SELF_ARMING_DEFER"])
            return real(*a, **kw)
        RG.subprocess.run = spy
        try:
            self._run()
        finally:
            RG.subprocess.run = real
        self.assertTrue(seen, "no gate was handed a scratch file")
        self.assertFalse(os.path.exists(seen[0]), "the scratch file was left behind")
        self.assertFalse(seen[0].startswith(os.path.dirname(HERE) + os.sep), "the scratch file is in the checkout")

    def test_an_outer_defer_is_kept(self):
        outer = os.path.join(tempfile.mkdtemp(prefix="arm-outer."), "outer.jsonl")
        _res, _q, after = self._run(preset=outer)
        self.assertEqual(after, outer, "a nested run replaced or dropped the outer scratch file")

    def test_wilson_of_these_attacks_meets_the_bar(self):
        import confidence
        self.assertGreaterEqual(len(RED_PROOF), 10)
        self.assertGreaterEqual(confidence.wilson_lower(len(RED_PROOF), len(RED_PROOF)), 0.722)


RED_PROOF = [
    {"why": "nothing is deferred", "file": "self_arming.py",
     "find": "    if d and os.path.abspath(p) == os.path.abspath(os.path.join(HERE, \".self_arming.jsonl\")):  # ARMING-DEFER\n",
     "replace": "    if False:  # ARMING-DEFER\n", "matches": 1},
    {"why": "a redirected fixture queue is deferred too", "file": "self_arming.py",
     "find": "    if d and os.path.abspath(p) == os.path.abspath(os.path.join(HERE, \".self_arming.jsonl\")):  # ARMING-DEFER\n",
     "replace": "    if d:  # ARMING-DEFER\n", "matches": 1},
    {"why": "bank() appends to the queue directly", "file": "self_arming.py",
     "find": "    with io.open(_bank_path(), \"a\", encoding=\"utf-8\") as fh:\n",
     "replace": "    with io.open(_ledger_path(), \"a\", encoding=\"utf-8\") as fh:\n", "matches": 2},
    {"why": "a non-object line is folded", "file": "self_arming.py",
     "find": "            if isinstance(json.loads(ln), dict):\n", "replace": "            if json.loads(ln) is not None:\n",
     "matches": 1},
    {"why": "the fold writes nowhere", "file": "self_arming.py",
     "find": "        with io.open(_ledger_path(), \"a\", encoding=\"utf-8\") as fh:  # ARMING-FOLD\n",
     "replace": "        with io.open(os.devnull, \"a\", encoding=\"utf-8\") as fh:  # ARMING-FOLD\n", "matches": 1},
    {"why": "the fold hides what it refused", "file": "self_arming.py",
     "find": "    return len(good), len(lines) - len(good)  # the caller removes its own scratch file\n",
     "replace": "    return len(good), 0  # the caller removes its own scratch file\n", "matches": 1},
    {"why": "the runner never hands gates a scratch file", "file": "run_gates.py",
     "find": "        os.environ[\"TV_SELF_ARMING_DEFER\"] = _defer\n", "replace": "        pass\n", "matches": 1},
    {"why": "a nested run replaces an outer scratch file", "file": "run_gates.py",
     "find": "            and not os.environ.get(\"TV_SELF_ARMING_DEFER\"):\n", "replace": "            and True:\n",
     "matches": 1},
    {"why": "the runner leaves the defer set", "file": "run_gates.py",
     "find": "        os.environ.pop(\"TV_SELF_ARMING_DEFER\", None)\n", "replace": "        pass\n", "matches": 1},
    {"why": "the deferred rows are dropped", "file": "run_gates.py",
     "find": "        _nf, _nr = _SA.fold_deferred(path)\n", "replace": "        _nf, _nr = 0, 0\n", "matches": 1},
    {"why": "the scratch file is left behind", "file": "run_gates.py",
     "find": "        os.remove(path)\n", "replace": "        pass\n", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=1)
