# -*- coding: utf-8 -*-
"""REG-2585 — ONE PROVE ACROSS MANY RUNNERS: EVERY PROOF IN EXACTLY ONE SHARD, AND A SHARD IS NOT A CENSUS.

⚠ WHAT IT IS FOR. A full `heart2 --prove` is ~3.5 h on his Mac and ~3 h on the box (2 lanes, 3,057 verdicts in
3h01m, 2026-10-23). Keys cannot cut the count (proof-keys Phase 0/0b), so the same proofs go to N CI runners at once:
`heart2 --prove [names] --push --proof-shard K/N`, each banking into a fresh cache file of its own, brought home by
`--import-shards` (REG-2586, test_an_imported_shard_keeps_its_tree).

⚠ THE DEFECTS THIS GUARDS, each one a silent loss:
  · a proof in NO shard is never proven, and the set still reads as "all shards green";
  · a proof in TWO shards is paid twice; a plan two shards compute differently does both at once;
  · a gate is not split - a 41-proof browser gate (the character builder, ~113 s a run on CI) keeps one runner busy
    for over an hour while the others wait;
  · a shard proves its whole gate list after all (the cut never reaches the run), so N runners do N full proves;
  · a shard writes the census as if its slice of each gate were the gate;
  · a shard banks into this machine's store, or into a file that already held entries it then serves as its own;
  · a shard proved from a tree that is not its HEAD calls itself clean.
Nothing here proves anything for real: the run's own seams are replaced by recorders, and every file is a temp one.
[[zero-needs-a-denominator]] [[feedback-fixtures-never-touch-live-data]] RED_PROOF below.
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
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2        # noqa: E402
import proof_shard   # noqa: E402

RED_PROOF = [
    {
        "why": "REG-2585 - every chunk goes to shard 1, so shards 2..N prove nothing while their runners report green",
        "file": "proof_shard.py",
        "find": "        k = min(range(n), key=lambda s: (load[s], s))\n",
        "replace": "        k = 0\n",
        "matches": 1,
    },
    {
        "why": "REG-2585 - a gate is never cut into chunks: the 41-proof browser gate holds one runner for over an hour",
        "file": "proof_shard.py",
        "find": "        k = max(1, min(p, int(math.ceil((c + oh) * p / target)) if target > 0 else 1))\n",
        "replace": "        k = 1\n",
        "matches": 1,
    },
    {
        "why": "REG-2585 - a proof is priced at its gate's run alone, so a shard of many cheap laws runs far longer",
        "file": "proof_shard.py",
        "find": "PROOF_OVERHEAD_S = 1.5\n",
        "replace": "PROOF_OVERHEAD_S = 0\n",
        "matches": 1,
    },
    {
        "why": "REG-2585 - the run's order keeps every proof of a gate, so a shard proves proofs another shard owns",
        "file": "proof_shard.py",
        "find": "[i for i in (order.get(g) or []) if i in own.get(g, ())]",
        "replace": "list(order.get(g) or [])",
        "matches": 1,
    },
    {
        "why": "REG-2585 - the cut never reaches the push run: every shard proves the whole list, N full proves",
        "file": "heart2.py",
        "find": "    order, gates = _shard_cut(have, order, gates, say)                 # REG-2585 - only this shard's proofs\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2585 - a shard falls through to _write_state and files its slice of each gate as the gate's census",
        "file": "heart2.py",
        "find": "            return dict((n, v) for n, v in (results or {}).items())\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2585 - a shard with no HEART2_CACHE_PATH banks into this machine's shared store",
        "file": "heart2.py",
        "find": "        if _sw is None and not os.environ.get(\"HEART2_CACHE_PATH\"):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-2585 - a shard proved from a tree whose tracked files differ from HEAD writes dirty=False",
        "file": "heart2.py",
        "find": "(bool(dirty.strip()) if ok_d else True)",
        "replace": "False",
        "matches": 1,
    },
]


def _have(spec):
    """[(name, file, proofs)] from {name: n proofs}; each proof a distinct entry."""
    return [(n, n + ".py", [{"file": n + ".py", "find": "x%d" % i, "replace": "", "why": "w%d" % i}
                            for i in range(p)]) for n, p in spec]


FIX = [("g_big", 40), ("g_a", 5), ("g_b", 3), ("g_c", 7), ("g_d", 1), ("g_e", 12), ("g_f", 2)]
COSTS = {"g_big": 110.0, "g_a": 2.0, "g_b": 0.2, "g_c": 3.0, "g_d": 0.3, "g_e": 8.0, "g_f": 1.0}


class TheShardSpec(unittest.TestCase):
    def test_reads_k_of_n(self):
        self.assertEqual(proof_shard.parse_spec(" 3 / 16 "), (3, 16))
        self.assertEqual(proof_shard.parse_spec("1/1"), (1, 1))

    def test_refuses_what_names_no_shard(self):
        for bad in ("0/2", "3/2", "2", "a/b", "", None, "-1/4"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                proof_shard.parse_spec(bad)


class ThePlan(unittest.TestCase):
    def test_every_proof_is_in_exactly_one_shard_and_every_shard_works(self):
        have = _have(FIX)
        every = set((n, i) for n, _f, p in have for i in range(len(p)))
        for n in range(1, 9):
            a = proof_shard.plan(have, n, COSTS)
            self.assertEqual(set(a), every, "N=%d: a proof is in no shard" % n)
            self.assertTrue(all(1 <= k <= n for k in a.values()), "N=%d: a shard number outside 1..N" % n)
            self.assertEqual(set(a.values()), set(range(1, n + 1)), "N=%d: a shard was given nothing" % n)
            self.assertEqual(a, proof_shard.plan(have, n, COSTS), "N=%d: two shards would compute two plans" % n)

    def test_the_big_gate_is_split_and_the_load_is_level(self):
        have = _have(FIX)
        a = proof_shard.plan(have, 8, COSTS)
        self.assertGreaterEqual(len(set(k for (g, _i), k in a.items() if g == "g_big")), 4,
                                "the 40-proof gate stayed on too few shards")
        load = dict((k, 0.0) for k in range(1, 9))
        for k in range(1, 9):
            own = proof_shard.mine(a, k)
            load[k] = sum((COSTS[g] + proof_shard.PROOF_OVERHEAD_S) * len(ix) + COSTS[g] for g, ix in own.items())
        mean = sum(load.values()) / 8.0
        self.assertLessEqual(max(load.values()), 1.5 * mean, "one shard carries far more than its share: %r" % load)

    def test_many_cheap_laws_are_priced_by_their_proofs_too(self):
        """MEASURED on the box (2026-10-23): a tampered run costs ~1.5 s beyond the gate's own run - 24 proofs of
        sub-second laws took 64 s on one lane. Priced at the gate's run alone, 60 proofs of two 0.1 s laws weighed
        less than nine proofs of three 4 s laws, and one shard ran 3.5x the other."""
        have = _have([("c1", 30), ("c2", 30), ("d1", 3), ("d2", 3), ("d3", 3)])
        costs = {"c1": 0.1, "c2": 0.1, "d1": 4.0, "d2": 4.0, "d3": 4.0}
        for n in (2, 3):
            a = proof_shard.plan(have, n, costs)
            ran = [sum((costs[g] + 1.5) * len(ix) + costs[g] for g, ix in proof_shard.mine(a, k).items())
                   for k in range(1, n + 1)]
            self.assertLessEqual(max(ran), 1.3 * min(ran), "N=%d: the shards run %r seconds" % (n, ran))

    def test_the_digest_names_n_and_every_entry(self):
        have = _have(FIX)
        a4 = proof_shard.plan(have, 4, COSTS)
        d = proof_shard.plan_digest(have, 4, a4)
        self.assertEqual(d, proof_shard.plan_digest(_have(FIX), 4, proof_shard.plan(_have(FIX), 4, COSTS)))
        self.assertNotEqual(d, proof_shard.plan_digest(have, 5, proof_shard.plan(have, 5, COSTS)))
        moved = _have(FIX)
        moved[1][2][0]["find"] = "moved"
        self.assertNotEqual(d, proof_shard.plan_digest(moved, 4, proof_shard.plan(moved, 4, COSTS)))

    def test_the_order_keeps_only_this_shards_proofs_in_run_order(self):
        order = {"g1": [3, 0, 2, 1], "g2": [0, 1], "g3": [0]}
        own = {"g1": {0, 3}, "g3": {0}}
        o2, g2 = proof_shard.restrict_order(order, ["g2", "g1", "g3"], own)
        self.assertEqual(g2, ["g1", "g3"])
        self.assertEqual(o2, {"g1": [3, 0], "g3": [0]})


class TheShardRun(unittest.TestCase):
    """The push run itself, with its seams replaced by recorders: what reaches the lanes, and what is written."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="shardrun-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.addCleanup(heart2._SHARD.update, {"spec": None, "manifest": None})

    def test_only_this_shards_gates_and_proofs_reach_the_lanes(self):
        have = _have([("g1", 6), ("g2", 1), ("g3", 4)])
        seen = []

        def fake_gates(items, say, blank=None, workers=None):
            seen.append(([n for n, _f, _p in items], dict(heart2._PUSH.order) if heart2._PUSH else None))
            return (dict((n, heart2.PROVEN) for n, _f, _p in items),
                    dict((n, [heart2.PROVEN] * len(p)) for n, _f, p in items))
        facts = (None, {"g1": list(range(6)), "g2": [0], "g3": list(range(4))}, ["g1", "g2", "g3"],
                 {"anchor": 0, "entry": 0, "target": 0})
        costs = {"g1": 50.0, "g2": 1.0, "g3": 5.0}
        a = proof_shard.plan(have, 3, costs)
        heart2._SHARD["spec"] = (2, 3)
        with mock.patch.object(heart2, "_push_facts", return_value=facts), \
                mock.patch.object(heart2, "browser_gates", return_value=set()), \
                mock.patch.object(heart2, "_prove_gates", side_effect=fake_gates), \
                mock.patch.object(proof_shard, "gate_costs", return_value=costs):
            heart2._prove_push(have, lambda *x, **k: None, stopped=[], cache=None, blank=set())
        own = proof_shard.mine(a, 2)
        self.assertTrue(seen, "nothing reached the lanes")
        names, order = seen[-1]
        self.assertEqual(sorted(names), sorted(own), "the lanes were handed gates this shard does not own")
        for g, ix in order.items():
            self.assertEqual(set(ix), own[g], "%s: the run's order holds proofs another shard owns" % g)

    def test_a_shard_writes_its_manifest_and_never_the_census(self):
        path = os.path.join(self.tmp, os.path.basename(heart2.CACHE))

        class _Cache(object):
            file = heart2._StoreFile(path, lambda *a, **k: None)
            measured = {}

            def flush(self):
                return False
        wrote = []
        heart2._SHARD["spec"] = (1, 2)
        heart2._SHARD["plan"], heart2._SHARD["own"] = "p" * 64, {"g1": {0, 2}}
        with mock.patch.object(heart2, "gate_files", return_value=[("g1", "g1.py")]), \
                mock.patch.object(heart2, "red_proofs_in", return_value=[{"file": "g1.py"}] * 3), \
                mock.patch.object(heart2, "red_proof_unreadable", return_value=False), \
                mock.patch.object(heart2, "open_cache", return_value=_Cache()), \
                mock.patch.object(heart2, "_prove_push", return_value=({"g1": heart2.PROVEN}, {"g1": [heart2.PROVEN, None, None]})), \
                mock.patch.object(heart2, "_write_state", side_effect=lambda *a, **k: wrote.append(a)), \
                mock.patch.object(heart2, "_git", side_effect=lambda *a: (True, "abc123\n") if a[0] == "rev-parse"
                                  else (True, "")):
            heart2.prove(only={"g1"}, say=lambda *a, **k: None, push=True, stopped=[])
        self.assertEqual(wrote, [], "a shard wrote the census as if its slice were the gate")
        with io.open(path, encoding="utf-8") as fh:
            m = json.load(fh)["shard"]
        self.assertEqual((m["k"], m["n"], m["head"], m["dirty"], m["finished"]), (1, 2, "abc123", False, True))
        self.assertEqual(m["assigned"], [["g1", 0], ["g1", 2]])

    def test_a_tree_that_differs_from_head_is_written_dirty(self):
        path = os.path.join(self.tmp, os.path.basename(heart2.CACHE))

        class _Cache(object):
            file = heart2._StoreFile(path, lambda *a, **k: None)

            def flush(self):
                return False
        heart2._SHARD.update(spec=(1, 1), plan="p", own={"g": {0}})
        with mock.patch.object(heart2, "_git", side_effect=lambda *a: (True, "abc\n") if a[0] == "rev-parse"
                               else (True, " M tv/heart2.py\n")):
            heart2._shard_finish(_Cache(), None, [], lambda *a, **k: None)
        with io.open(path, encoding="utf-8") as fh:
            self.assertIs(json.load(fh)["shard"]["dirty"], True)


class TheShardFlag(unittest.TestCase):
    """main() refuses a shard it could not bank honestly - before any sandbox is built."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="shardflag-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.addCleanup(heart2._SHARD.update, {"spec": None, "manifest": None})

    def _main(self, argv, env):
        out = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=False), mock.patch("sys.stdout", out), \
                mock.patch.object(heart2, "install_sandbox_cleanup", side_effect=AssertionError("it began to prove")):
            code = heart2.main(argv)
        return code, out.getvalue()

    def test_without_push(self):
        code, out = self._main(["--prove", "g", "--proof-shard", "1/2"], {"HEART2_CACHE_PATH": "x"})
        self.assertEqual(code, 2)
        self.assertIn("--push", out)

    def test_without_a_cache_file_of_its_own(self):
        env = dict(os.environ)
        env.pop("HEART2_CACHE_PATH", None)
        with mock.patch.dict(os.environ, env, clear=True):
            code, out = self._main(["--prove", "g", "--push", "--proof-shard", "1/2"], {})
        self.assertEqual(code, 2)
        self.assertIn("HEART2_CACHE_PATH", out)

    def test_into_a_file_that_already_holds_entries(self):
        p = os.path.join(self.tmp, os.path.basename(heart2.CACHE))
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(u'{"format": 2, "entries": {}}')
        with mock.patch.object(heart2, "CACHE", p):
            code, out = self._main(["--prove", "g", "--push", "--proof-shard", "1/2"], {"HEART2_CACHE_PATH": p})
        self.assertEqual(code, 2)
        self.assertIn("already exists", out)

    def test_a_spec_nobody_can_read(self):
        code, out = self._main(["--prove", "g", "--push", "--proof-shard", "5/4"], {"HEART2_CACHE_PATH": "x"})
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
