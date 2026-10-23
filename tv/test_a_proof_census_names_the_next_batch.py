# -*- coding: utf-8 -*-
"""REG-2595 — THE 16-SHARD RUN IS A POST-PUSH CENSUS: IT NAMES THE LAWS THE NEXT BATCH FIXES.

⚠ WHAT IT IS FOR. Elad's ruling (2026-10-23 17:04): the 16-shard run no longer blocks a push. It runs AFTER the push,
on a ci/proof-keys-<sha12> branch at the pushed sha, as the census - and what it finds (a BLIND, a law already red
untampered, an INVALID) is the next version's work. So the run must SAY it, in one place a person reads: the job
summary and a `proof-census-<sha>` artifact, written by `proof_shard.py --census`.

⚠ THE RULE. The census reads whatever the shards left and never fails: every failure a kept-going shard owes
(REG-2591), or the one stop of a fail-fast shard, is listed with its law, proof, verdict, why and shard; the counts are
assigned / PROVEN / owed / unbanked; a dir with no store is named; a sha other than the pushed one is flagged; the
slowest and mean shard walls come from each shard's prove.log. The workflow runs it with `if: always()` - a census
that only runs on a green set would hide exactly the reds it is for.

⚠ THE DEFECTS THIS GUARDS: a census that drops the owed list or a fail-fast stop; counts that call every verdict
PROVEN; a census that exits red (a census never gates); walls not read; a foreign sha not flagged; the census step
skipped when the fan-in fails. Every store here is a temp dir; no law is run. RED_PROOF below.
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
import proof_shard   # noqa: E402

SHA = "a" * 40
WORKFLOW = os.path.join(os.path.dirname(HERE), ".github", "workflows", "proof-keys-shards.yml")


def _entry(gate, idx, verdict="PROVEN"):
    return {"gate": gate, "proof": idx, "verdict": verdict}


class TheCensusNamesTheNextBatch(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pkcensus.")
        self.addCleanup(shutil.rmtree, self.root, True)

    def shard(self, k, assigned, proven, owed=None, stopped=None, head=SHA, wall=None, store=True):
        d = os.path.join(self.root, "proof-shard-%d" % k)
        os.makedirs(d)
        if store:
            body = {"format": 1, "entries": dict(("k%d-%s-%d" % (k, g, i), _entry(g, i)) for g, i in proven),
                    "shard": {"k": k, "n": 2, "head": head, "assigned": [list(a) for a in assigned],
                              "owed": [list(f) for f in (owed or [])], "stopped": list(stopped) if stopped else None}}
            with open(os.path.join(d, proof_shard.STORE_NAME), "w", encoding="utf-8") as fh:
                json.dump(body, fh)
        if wall is not None:
            with open(os.path.join(d, "prove.log"), "w", encoding="utf-8") as fh:
                fh.write("  #42 something\nprove_seconds=%d rc=1\n" % wall)

    def test_every_owed_failure_of_a_kept_going_shard_is_listed(self):
        self.shard(1, [("a", 0), ("a", 1), ("b", 0)], [("a", 0)],
                   owed=[("a", 1, "BLIND", "the tamper ran and the law stayed GREEN"),
                         ("b", 0, "INVALID", "its anchor is gone")])
        text, tot = proof_shard.census(self.root, SHA)
        self.assertEqual([f[:3] + [f[4]] for f in tot["fix"]], [["a", 1, "BLIND", 1], ["b", 0, "INVALID", 1]])
        self.assertIn("| a | 1 | BLIND | the tamper ran and the law stayed GREEN | 1 |", text)
        self.assertIn("| b | 0 | INVALID |", text)

    def test_a_fail_fast_shard_names_its_stop(self):
        self.shard(2, [("c", 0), ("d", 0)], [], stopped=("c", 0, "UNPROVABLE", "the law is ALREADY RED untampered"))
        _text, tot = proof_shard.census(self.root, SHA)
        self.assertEqual([f[:3] for f in tot["fix"]], [["c", 0, "UNPROVABLE"]])

    def test_the_counts_split_proven_owed_and_unbanked(self):
        self.shard(1, [("a", 0), ("a", 1), ("b", 0)], [("a", 0)], owed=[("a", 1, "BLIND", "x")])
        self.shard(2, [("c", 0), ("c", 1)], [("c", 0)])
        text, tot = proof_shard.census(self.root, SHA)
        self.assertEqual((tot["assigned"], tot["proven"], tot["owed"], tot["unbanked"]), (5, 2, 1, 2))
        self.assertIn("Assigned 5 proof(s): PROVEN 2 · owed a fix 1 · unbanked 2", text)
        self.assertIn("- b: 1", text)

    def test_only_a_proven_entry_counts_as_proven(self):
        self.shard(1, [("a", 0), ("a", 1)], [("a", 0)])
        p = os.path.join(self.root, "proof-shard-1", proof_shard.STORE_NAME)
        with open(p, encoding="utf-8") as fh:
            body = json.load(fh)
        body["entries"]["odd"] = _entry("a", 1, "BLIND")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(body, fh)
        _text, tot = proof_shard.census(self.root, SHA)
        self.assertEqual(tot["proven"], 1)

    def test_a_dir_with_no_store_is_named_and_the_census_still_reads(self):
        self.shard(1, [("a", 0)], [("a", 0)])
        self.shard(2, [], [], store=False)
        text, tot = proof_shard.census(self.root, SHA)
        self.assertIn("1 dir(s) carry none: proof-shard-2", text)
        self.assertEqual(tot["proven"], 1)

    def test_the_shard_walls_come_from_prove_log(self):
        self.shard(1, [("a", 0)], [("a", 0)], wall=1200)
        self.shard(2, [("b", 0)], [("b", 0)], wall=800)
        text, _tot = proof_shard.census(self.root, SHA)
        self.assertIn("slowest 1200 s, mean 1000 s (1.20x)", text)

    def test_a_foreign_sha_is_flagged(self):
        self.shard(1, [("a", 0)], [("a", 0)], head="b" * 40)
        text, _tot = proof_shard.census(self.root, SHA)
        self.assertIn("not aaaaaaaaaaaa", text)

    def test_the_cli_writes_the_census_and_never_gates(self):
        self.shard(1, [("a", 0)], [], owed=[("a", 0, "BLIND", "x")])
        out = os.path.join(self.root, "census.md")
        with mock.patch("sys.stdout", io.StringIO()):
            rc = proof_shard.main(["--census", self.root, "--head", SHA, "--out", out])
        self.assertEqual(rc, 0)
        with open(out, encoding="utf-8") as fh:
            self.assertIn("laws owed a fix (1)", fh.read())

    def test_a_malformed_store_is_named_and_the_rest_still_counts(self):
        self.shard(1, [("a", 0)], [("a", 0)])
        self.shard(2, [("b", 0)], [])
        p = os.path.join(self.root, "proof-shard-2", proof_shard.STORE_NAME)
        with open(p, encoding="utf-8") as fh:
            body = json.load(fh)
        body["shard"]["assigned"] = [["b"]]
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(body, fh)
        text, tot = proof_shard.census(self.root, SHA)
        self.assertIn("proof-shard-2 (unreadable store)", text)
        self.assertEqual(tot["proven"], 1)
        self.assertIn("NOT a clean bill", text)

    def test_a_stop_is_listed_beside_the_owed(self):
        self.shard(1, [("a", 0), ("b", 0)], [], owed=[("a", 0, "BLIND", "x")], stopped=("b", 0, "INVALID", "y"))
        _text, tot = proof_shard.census(self.root, SHA)
        self.assertEqual([f[:3] for f in tot["fix"]], [["a", 0, "BLIND"], ["b", 0, "INVALID"]])

    def test_a_shard_that_left_nothing_is_unknown_not_green(self):
        self.shard(1, [("a", 0)], [("a", 0)])
        text, _tot = proof_shard.census(self.root, SHA, 3)
        self.assertIn("2 of 3 shard(s) left no readable store: 2, 3", text)
        self.assertIn("NOT a clean bill", text)
        self.assertNotIn("every assigned proof that ran is PROVEN", text)


class TheWorkflowRunsTheCensus(unittest.TestCase):

    def test_the_fan_in_runs_the_census_always_and_keeps_it(self):
        with open(WORKFLOW, encoding="utf-8") as fh:
            wf = fh.read()
        i = wf.index("The census - what this commit proved")
        step = wf[i:wf.index("- name: Every shard finished", i)]
        self.assertIn("if: ${{ always() }}", step.split("- name: Keep the census")[0])
        self.assertIn('--census shards --shards "$PROOF_SHARDS"', step)
        self.assertIn("GITHUB_STEP_SUMMARY", step)
        self.assertIn("name: proof-census-${{ github.sha }}", step)


RED_PROOF = [
    {"why": "REG-2595 - a kept-going shard's owed failures are dropped from the census",
     "file": "proof_shard.py",
     "find": "            bad = [list(f[:4]) for f in (sh.get(\"owed\") or [])]      # REG-2591",
     "replace": "            bad = []      # REG-2591",
     "matches": 1},
    {"why": "REG-2595 - a fail-fast shard's stop is not named",
     "file": "proof_shard.py",
     "find": "            if sh.get(\"stopped\") and list(sh[\"stopped\"][:2]) not in [f[:2] for f in bad]:\n",
     "replace": "            if sh.get(\"stopped\") and not bad:\n",
     "matches": 1},
    {"why": "REG-2595 - one malformed store ends the census (the law list is lost)",
     "file": "proof_shard.py",
     "find": "        except (TypeError, ValueError, KeyError, AttributeError):\n            missing.append(d + \" (unreadable store)\")\n            continue\n",
     "replace": "        except ZeroDivisionError:\n            continue\n",
     "matches": 1},
    {"why": "REG-2595 - a shard that left nothing reads green",
     "file": "proof_shard.py",
     "find": "    elif missing or lost or not rows:\n",
     "replace": "    elif False:\n",
     "matches": 1},
    {"why": "REG-2595 - every banked entry counts as PROVEN, whatever its verdict",
     "file": "proof_shard.py",
     "find": "                  if isinstance(e, dict) and e.get(\"verdict\") == \"PROVEN\")\n",
     "replace": "                  if isinstance(e, dict))\n",
     "matches": 1},
    {"why": "REG-2595 - the census gates (exits red)",
     "file": "proof_shard.py",
     "find": "        return 0                        # a census informs the next batch; it never gates a push\n",
     "replace": "        return 2 if _t[\"fix\"] else 0\n",
     "matches": 1},
    {"why": "REG-2595 - the shard walls are never read",
     "file": "proof_shard.py",
     "find": "            if m:\n                walls.append(int(m[-1]))\n",
     "replace": "            if m:\n                pass\n",
     "matches": 1},
    {"why": "REG-2595 - a census of another sha is not flagged",
     "file": "proof_shard.py",
     "find": "    if head and heads and heads != [str(head)[:12]]:\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-2595 - the census runs only when the fan-in is green",
     "file": "../.github/workflows/proof-keys-shards.yml",
     "find": "      - name: The census - what this commit proved, and the laws the next batch fixes (REG-2595)\n        if: ${{ always() }}\n",
     "replace": "      - name: The census - what this commit proved, and the laws the next batch fixes (REG-2595)\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
