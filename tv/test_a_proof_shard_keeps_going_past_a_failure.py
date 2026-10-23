# -*- coding: utf-8 -*-
"""REG-2591 — A CI PROOF SHARD KEEPS GOING PAST A FAILURE: IT IS OWED, NEVER A STRAND.

⚠ WHAT IT IS FOR. `heart2 --prove --push` fails fast on the Mac: the first BLIND / INVALID / clean-run red stops the run
and refuses the push, because a push is one yes-or-no. A CI proof shard (`--proof-shard K/N`, REG-2585) is not a push:
it is one sixteenth of the set, and the run at dcff7160 showed what fail-fast costs there - 7 of 16 shards stopped on
their first red, and about 300 proofs each were never run, banked nothing, and had to be proved again on the Mac.

⚠ THE RULE. In shard mode every failure is RECORDED and the shard KEEPS GOING: only the failed gate's own remaining
proofs are NOT RUN, every other gate still runs and banks, the manifest lists every failure as `owed`, and the shard
still exits red. The fan-in names what each shard owes and stays green (the set is whole; what it banks is the Mac's
count, REG-2594). Off a shard (the Mac's push) the first failure still stops the run.

⚠ THE DEFECTS THIS GUARDS:
  · a shard that stops at its first red (strands its other gates);
  · a shard that keeps going but forgets the earlier failures (only the first is owed, the rest read green);
  · a kept-going shard that exits 0 (a red law ships as a green shard);
  · a gate whose clean wave run was red is proved again proof by proof (minutes for nothing);
  · the manifest drops the owed list, or the fan-in refuses a whole set that merely owes;
  · fail-fast lost on the Mac's push.
Every store here is a temp file; no law is run. RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402  (it prints non-ASCII)
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2        # noqa: E402
import proof_shard   # noqa: E402

BLIND = heart2.BLIND
PROVEN = heart2.PROVEN


class ThePushRunsOneRule(unittest.TestCase):

    def test_off_a_shard_the_first_failure_stops_the_run(self):
        run = heart2._PushRun()
        self.assertTrue(run.fail("a", 0, BLIND, "why"))
        self.assertTrue(run.stop.is_set(), "the Mac's push no longer fails fast")
        self.assertFalse(run.fail("b", 1, BLIND, "why"), "a second failure announced as the one that stopped it")
        self.assertEqual(run.first, ("a", 0, BLIND, "why"))

    def test_a_shard_records_every_failure_and_never_stops(self):
        run = heart2._PushRun(keep_going=True)
        self.assertTrue(run.fail("a", 0, BLIND, "x"))
        self.assertTrue(run.fail("b", 2, BLIND, "y"), "a later failure in a kept-going shard was never announced")
        self.assertFalse(run.stop.is_set(), "a shard stopped at a failure and stranded its other proofs")
        self.assertEqual([f[:2] for f in run.failures], [("a", 0), ("b", 2)])
        self.assertTrue(run.failed("a") and run.failed("b"))
        self.assertFalse(run.failed("c"))


class AGateInAShard(unittest.TestCase):
    """_prove_gate_push with the law never run: each proof's verdict is scripted."""

    PROOFS = [{"file": "x"}, {"file": "x"}, {"file": "x"}]

    def prove(self, run, name, script, ran):
        def one(sandbox, n, filename, proof, i, say, why):
            ran.append((n, i))
            return script.get((n, i), PROVEN)
        with mock.patch.object(heart2, "_prove_push_one", one), \
                mock.patch.object(heart2, "_clean_here", lambda *a: a[4]), \
                mock.patch.object(heart2, "_closing_clean", lambda name, per, say: per):
            return heart2._prove_gate_push(None, name, name + ".py", self.PROOFS, lambda *a, **k: None, run)

    def test_after_a_blind_the_next_gate_still_runs_in_a_shard(self):
        run, ran = heart2._PushRun(keep_going=True), []
        _v, per = self.prove(run, "a", {("a", 1): BLIND}, ran)
        self.assertEqual(per, [PROVEN, BLIND, None], "the failed gate's own later proofs are NOT RUN")
        _v, per = self.prove(run, "b", {}, ran)
        self.assertEqual(per, [PROVEN, PROVEN, PROVEN], "a shard stranded the gates after its first failure")
        self.assertEqual(ran, [("a", 0), ("a", 1), ("b", 0), ("b", 1), ("b", 2)])

    def test_off_a_shard_the_next_gate_is_not_run(self):
        run, ran = heart2._PushRun(), []
        self.prove(run, "a", {("a", 1): BLIND}, ran)
        _v, per = self.prove(run, "b", {}, ran)
        self.assertEqual(per, [None, None, None])

    def test_a_gate_whose_clean_run_was_red_is_not_proved_again(self):
        run, ran = heart2._PushRun(keep_going=True), []
        run.fail("a", 0, heart2.UNPROVABLE, "the law is ALREADY RED untampered")
        v, per = self.prove(run, "a", {}, ran)
        self.assertEqual((v, per, ran), (heart2.NOT_RUN, [None, None, None], []))


class WhatTheShardWritesAndSays(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="keepgoing-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.addCleanup(heart2._SHARD.update, {"spec": None, "manifest": None, "plan": None, "own": None})

    def test_the_manifest_lists_every_failure_owed_and_no_stop(self):
        path = os.path.join(self.tmp, os.path.basename(heart2.CACHE))

        class _Cache(object):
            file = heart2._StoreFile(path, lambda *a, **k: None)

            def flush(self):
                return False
        heart2._SHARD.update(spec=(1, 1), plan="p", own={"a": {0, 1}, "b": {0}})
        owed = [("a", 1, BLIND, "x"), ("b", 0, BLIND, "y")]
        with mock.patch.object(heart2, "_git", side_effect=lambda *a: (True, "abc\n") if a[0] == "rev-parse"
                               else (True, "")):
            heart2._shard_finish(_Cache(), None, owed, lambda *a, **k: None)
        with io.open(path, encoding="utf-8") as fh:
            m = json.load(fh)["shard"]
        self.assertEqual([f[:2] for f in m["owed"]], [["a", 1], ["b", 0]])
        self.assertIsNone(m["stopped"], "a kept-going shard wrote that it stopped")
        self.assertIs(m["finished"], True)

    def test_the_fan_in_names_what_each_shard_owes_and_takes_the_set(self):
        head = "c" * 40
        for k, own, ent, owed in ((1, {"a": {0, 1}}, {"k1": {"gate": "a", "proof": 0, "verdict": PROVEN, "provedAt": 1,
                                                               "tree": "t"}}, [["a", 1, BLIND, "x"]]),
                                  (2, {"b": {0}}, {}, [])):
            d = os.path.join(self.tmp, "proof-shard-%d" % k)
            os.makedirs(d)
            body = {"format": 2, "entries": ent,
                    "shard": proof_shard.manifest(k, 2, head, False, "p", own, None, None, 1, owed=owed)}
            with io.open(os.path.join(d, proof_shard.STORE_NAME), "w", encoding="utf-8") as fh:
                json.dump(body, fh)
        said = []
        rc = proof_shard.fan_in(self.tmp, 2, head, say=said.append)
        text = "\n".join(said)
        self.assertEqual(rc, 0, text)
        self.assertIn("OWES a[1] BLIND", text)
        self.assertIn("REG-2591: 1 failure(s) OWED a fix in 1 shard(s)", text)
        self.assertIn("REG-2594: 2 of 3 assigned proof(s) bank nothing", text)

    def test_every_failure_is_handed_on_not_only_the_first(self):
        run = heart2._PushRun(keep_going=True)
        run.fail("a", 1, BLIND, "x")
        run.fail("b", 0, heart2.INVALID, "y")
        said, stopped = [], []
        heart2._owe_all(run, {"a": [PROVEN, BLIND, None], "b": [heart2.INVALID]}, said.append, stopped)
        self.assertEqual([f[:2] for f in stopped], [("a", 1), ("b", 0)])
        text = "\n".join(said)
        self.assertIn("2 failure(s) in 2 gate(s) are OWED a fix; 1 proof(s) NOT RUN", text)
        self.assertIn("OWED b[0] INVALID", text)

    def test_a_shard_that_owes_exits_red(self):
        p = os.path.join(self.tmp, os.path.basename(heart2.CACHE))

        def prove(only=None, push=False, stopped=None, **_k):
            stopped.append(("a", 1, BLIND, "the tamper ran and the law stayed GREEN"))
            return {}
        out = io.StringIO()
        with mock.patch.object(heart2, "CACHE", p), \
                mock.patch.dict(os.environ, {"HEART2_CACHE_PATH": p}), mock.patch("sys.stdout", out), \
                mock.patch.object(heart2, "install_sandbox_cleanup", lambda: None), \
                mock.patch.object(heart2, "sweep_stale_sandboxes", lambda: []), \
                mock.patch.object(heart2, "prove", prove):
            code = heart2.main(["--prove", "a", "--push", "--proof-shard", "1/2"])
        self.assertEqual(code, 1, out.getvalue()[-600:])
        self.assertIn("REG-2591 this proof shard OWES 1 failure(s) (a[1] BLIND)", out.getvalue())


    def _push(self, spec):
        """_prove_push itself, with the proving faked: gate a goes BLIND at [1], gate b runs after it."""
        have = [("a", "test_a.py", [{}, {}]), ("b", "test_b.py", [{}])]
        seen = []

        def gates(items, say, blank=None):
            run = heart2._PUSH
            seen.append(bool(run.keep_going))
            res, per = {}, {}
            for n, _f, p in items:
                if run.stop.is_set():
                    res[n], per[n] = heart2.NOT_RUN, [None] * len(p)
                    continue
                if n == "a":
                    run.fail("a", 1, BLIND, "the tamper ran and the law stayed GREEN")
                    res[n], per[n] = BLIND, [PROVEN, BLIND]
                else:
                    res[n], per[n] = PROVEN, [PROVEN]
            return res, per
        said, stopped = [], []
        with mock.patch.dict(heart2._SHARD, {"spec": spec} if spec else {}, clear=True), \
                mock.patch.object(heart2, "_heart2_seams", lambda: {}), \
                mock.patch.object(heart2, "_push_facts", lambda h, say: (
                    None, {"a": [1, 0], "b": [0]}, ["a", "b"], {"anchor": 0, "entry": 0, "target": 0})), \
                mock.patch.object(heart2, "_shard_cut", lambda h, o, g, say: (o, g)), \
                mock.patch.object(heart2, "_push_browser", lambda h, unk: set()), \
                mock.patch.object(heart2, "prove_workers", lambda n: 8), \
                mock.patch.object(heart2, "_push_record", lambda *a: None), \
                mock.patch.object(heart2, "_prove_gates", gates):
            results, _per = heart2._prove_push(have, said.append, stopped)
        return results, stopped, "\n".join(said), seen

    def test_a_shard_push_keeps_going_and_hands_on_every_failure(self):
        results, stopped, text, seen = self._push((1, 2))
        self.assertEqual(seen, [True], "a CI shard's push run was not told to keep going")
        self.assertEqual(results.get("b"), PROVEN, "the gate after the BLIND was stranded: " + text[-400:])
        self.assertEqual([f[:2] for f in stopped], [("a", 1)])
        self.assertIn("are OWED a fix", text)
        self.assertNotIn("STOPPED at the first failure", text)

    def test_the_macs_push_still_stops_at_the_first_failure(self):
        results, stopped, text, seen = self._push(None)
        self.assertEqual(seen, [False])
        self.assertNotIn("b", results, "off a shard the gate after the failure ran")
        self.assertEqual([f[:2] for f in stopped], [("a", 1)])
        self.assertIn("STOPPED at the first failure", text)

RED_PROOF = [
    {"why": "REG-2591 - a shard stops at its first failure: the gates after it are stranded",
     "file": "heart2.py",
     "find": "        if self.keep_going:\n            return True\n        self.stop.set()\n",
     "replace": "        self.stop.set()\n        if self.keep_going:\n            return True\n",
     "matches": 1},
    {"why": "REG-2591 - only the first failure is kept: the rest of a kept-going shard's reds read green",
     "file": "heart2.py",
     "find": "            self.failures.append((name, idx, verdict, reason))\n",
     "replace": "            if first:\n                self.failures.append((name, idx, verdict, reason))\n",
     "matches": 1},
    {"why": "REG-2591 - the Mac's push no longer fails fast",
     "file": "heart2.py",
     "find": "        self.stop.set()\n        return first\n",
     "replace": "        return True\n",
     "matches": 1},
    {"why": "REG-2591 - a gate whose clean run was red is proved again, proof by proof",
     "file": "heart2.py",
     "find": "    if getattr(run, \"keep_going\", False) and run.failed(name):\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-2591 - a kept-going shard's failures never reach the manifest or main",
     "file": "heart2.py",
     "find": "    if stopped is not None:\n        stopped.extend(run.failures)\n",
     "replace": "    if stopped is not None:\n        stopped.extend(run.failures[:1])\n",
     "matches": 1},
    {"why": "REG-2591 - the manifest drops the owed list",
     "file": "proof_shard.py",
     "find": "            \"owed\": [list(f) for f in (owed or [])],\n",
     "replace": "            \"owed\": [],\n",
     "matches": 1},
    {"why": "REG-2591 - _shard_finish writes no owed",
     "file": "heart2.py",
     "find": "int(time.time() * 1000), owed=stopped)\n",
     "replace": "int(time.time() * 1000), owed=None)\n",
     "matches": 1},
    {"why": "REG-2591 - a shard that owes exits 0",
     "file": "heart2.py",
     "find": "                                               + (\" …\" if len(_stopped) > 4 else \"\")))\n        return _done(1)\n",
     "replace": "                                               + (\" …\" if len(_stopped) > 4 else \"\")))\n        return _done(0)\n",
     "matches": 1},
    {"why": "REG-2591 - the fan-in never says what a shard owes",
     "file": "proof_shard.py",
     "find": "    fails = dict((b[\"shard\"][\"k\"], b[\"shard\"].get(\"owed\")) for _l, b, _w in bodies if b[\"shard\"].get(\"owed\"))\n",
     "replace": "    fails = {}\n",
     "matches": 1},
    {"why": "REG-2591 - _prove_push never turns keep-going on: a CI shard still stops at its first failure",
     "file": "heart2.py",
     "find": "    _keep = bool(_SHARD.get(\"spec\"))",
     "replace": "    _keep = False",
     "matches": 1},
    {"why": "REG-2591 - _prove_push never hands a kept-going shard's failures on (no _owe_all)",
     "file": "heart2.py",
     "find": "    if run.keep_going and run.failures:\n        _owe_all(run, per_proof, say, stopped)\n",
     "replace": "    if False:\n        pass\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
