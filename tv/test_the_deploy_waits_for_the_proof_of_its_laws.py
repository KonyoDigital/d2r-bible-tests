# -*- coding: utf-8 -*-
"""REG-2962 (#161 stage 2, his go 2026-10-21: "do whatever is recommended") - NOTHING A PUSH CHANGED PUBLISHES UNPROVEN.

Before: publish.yml's deploy needed [smoke, suites, review]; no proof ran on main, so the laws' red-proofs (heart2
--prove) were proved only by hooks/pre-push on his Mac - browser laws one at a time (the v3833 push spent ~30 min there).
Now Publish CALLS proof-keys-shards.yml (job `proof`, gate deploy) and the deploy needs it:

  * the 16 shards prove (from the last main run's seed, REG-2961) and, in the deploy gate, never fail the run themselves:
    each failure is named in its shard's manifest (owed, REG-2591);
  * the fan-in's verdict (tv/proof_shard.py --deploy-verdict) passes only when the proof set is WHOLE and no law this push
    changed since the last commit Publish published is owed a fix - a law only the Mac can prove is left to the hook,
    which proved it; with no last publish, or a diff git cannot take, EVERY law is this push's;
  * a law owed a fix that the push did NOT change is said and never holds the deploy: the hook never proved unchanged
    laws either, so a red already standing on CI cannot stop his site forever.

Fixtures only: shard stores built here; the verdict's gate and Mac-only lookups injected. RED_PROOF below.
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import proof_shard as PS  # noqa: E402

PUB = os.path.join(ROOT, ".github", "workflows", "publish.yml")
WF = os.path.join(ROOT, ".github", "workflows", "proof-keys-shards.yml")
#: REG-3085 - the shard's prove steps, shared by `shard` and `shard-again`
ACT = os.path.join(ROOT, ".github", "actions", "prove-shard", "action.yml")
HEAD, BASE = "a" * 40, "b" * 40


def _read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def _code(text):
    return "\n".join(l for l in text.split("\n") if not l.lstrip().startswith("#"))


class TheVerdict(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="deployverdict-")
        self.addCleanup(shutil.rmtree, self.root, True)

    def _shard(self, k, assigned, owed=(), n=2):
        d = os.path.join(self.root, "proof-shard-%d" % k)
        os.makedirs(d)
        m = {"v": PS.MANIFEST_V, "k": k, "n": n, "head": HEAD, "dirty": False, "plan": "p1", "finished": True,
             "names": None, "stopped": None, "at": 1, "owed": [list(f) for f in owed],
             "assigned": [list(a) for a in assigned]}
        ent = dict(("k%d%s%d" % (k, g, i), {"verdict": "PROVEN", "provedAt": 1, "gate": g, "proof": i, "kind": "static"})
                   for g, i in assigned if (g, i) not in [(f[0], f[1]) for f in owed])
        with io.open(os.path.join(d, PS.STORE_NAME), "w", encoding="utf-8") as fh:
            json.dump({"format": 2, "entries": ent, "shard": m}, fh)

    def _set(self):
        self._shard(1, [("g_changed_ok", 0), ("g_owed", 0)], owed=[("g_owed", 0, "BLIND", "the law stayed green")])
        self._shard(2, [("g_changed_ok", 1), ("g_mac", 0)], owed=[("g_mac", 0, "BLIND", "needs his footage")])

    def _verdict(self, gates, changed=(), mac=()):
        said = []
        rc = PS.deploy_verdict(self.root, 2, HEAD, BASE, say=said.append, changed=set(changed),
                               gates_of=lambda paths: list(gates), mac_only=lambda names: set(mac) & set(names))
        return rc, "\n".join(said)

    def test_a_changed_law_owed_a_fix_holds_the_deploy_and_is_named(self):
        self._set()
        rc, said = self._verdict(["g_changed_ok", "g_owed"])
        self.assertEqual(rc, 1, said)
        self.assertIn("DEPLOY HELD", said)
        self.assertIn("g_owed[0] BLIND", said)

    def test_a_push_whose_laws_are_proven_publishes_and_says_what_else_is_owed(self):
        self._set()
        rc, said = self._verdict(["g_changed_ok"])
        self.assertEqual(rc, 0, said)
        self.assertIn("did NOT change are owed a fix", said)
        self.assertIn("g_owed", said)

    def test_a_law_only_the_mac_can_prove_is_the_hooks(self):
        self._set()
        rc, said = self._verdict(["g_mac", "g_changed_ok"], mac=["g_mac"])
        self.assertEqual(rc, 0, "a Mac-only law the hook proved held the CI deploy: %s" % said)
        self.assertIn("only the Mac can prove", said)

    def test_unknown_changes_are_every_law(self):
        self._set()
        said = []
        rc = PS.deploy_verdict(self.root, 2, HEAD, None, say=said.append, changed=None,
                               gates_of=lambda paths: ["g_changed_ok", "g_owed"] if paths is None else [],
                               mac_only=lambda names: set())
        self.assertEqual(rc, 1, "with no last publish the push's laws were read as none: %s" % said)
        self.assertIn("EVERY law", "\n".join(said))

    def test_a_set_that_is_not_whole_is_refused(self):
        self._shard(1, [("g_changed_ok", 0)])
        rc, said = self._verdict(["g_changed_ok"])
        self.assertEqual(rc, 2, said)
        self.assertIn("not whole", said)


class TheVerdictReadsTheHooksOwnRule(unittest.TestCase):
    """the gates a push's paths name are heart2.gates_for_tests' (the hook's own rule, pinned beside the hook's script by
    its own law); UNKNOWN paths are every registered gate"""

    def test_paths_name_the_hooks_gates_and_unknown_is_every_gate(self):
        self.assertEqual(PS._gates_of({"tv/test_the_vault_find_ranks_matches.py", "bible.html"}),
                         ["test_the_vault_find_ranks_matches"])
        every = PS._gates_of(None)
        self.assertIn("test_the_vault_find_ranks_matches", every)
        self.assertGreater(len(every), 300, "UNKNOWN changes read as a handful of laws: %d" % len(every))


class PublishWaitsForIt(unittest.TestCase):

    def test_the_deploy_needs_the_proof_job_and_the_shards_take_the_call(self):
        pub = _code(_read(PUB))
        self.assertIn("    needs: [smoke, suites, review, proof]\n", pub, "the deploy no longer waits for every gate")
        job = pub[pub.find("\n  proof:\n"):pub.find("\n  deploy:\n")]
        self.assertIn("uses: ./.github/workflows/proof-keys-shards.yml", job)
        self.assertIn("actions: read", job, "the verdict cannot ask which commit Publish last published")
        self.assertIn("      gate: deploy\n", job, "Publish calls the shards without its gate")
        self.assertIn("\n  workflow_call:\n", _code(_read(WF)), "the shard workflow cannot be called")

    def test_in_the_deploy_gate_a_shard_leaves_the_verdict_to_the_fan_in(self):
        # REG-3085 - the prove step is the shared action's; the shard job hands it the workflow's own gate input
        self.assertIn("gate: ${{ inputs.gate }}", _code(_read(WF)), "the shard does not hand Publish's gate to its prove")
        code = _code(_read(ACT))
        prove = code[code.find("python3 -u tv/heart2.py --prove --push --proof-shard"):]
        prove = prove[:prove.find("\n    - ")]
        g = prove.find('if [ "${{ inputs.gate }}" = "deploy" ]; then')
        self.assertGreater(g, 0, "a shard fails Publish's run on any law, changed by this push or not")
        self.assertLess(g, prove.find("exit $rc"), "the deploy-gate exit comes after the shard's own")
        self.assertIn("exit 0", prove[g:prove.find("exit $rc")])

    def test_the_fan_in_judges_this_push_from_the_last_publish(self):
        code = _code(_read(WF))
        step = code[code.find("May this commit publish?"):]
        self.assertIn("if: ${{ inputs.gate == 'deploy' }}", step)
        self.assertIn("--workflow publish.yml --branch main --status success", step)
        self.assertIn('python3 tv/proof_shard.py --deploy-verdict shards --shards "$PROOF_SHARDS" --head "$GITHUB_SHA" '
                      '--base "$BASE"', step)
        fan = code[code.find("\n  fan-in:\n"):]
        self.assertTrue(re.search(r"\n    permissions:\n      contents: read\n      actions: read\n", fan),
                        "the fan-in cannot read Publish's runs")


RED_PROOF = [
    {"why": "REG-2962 - the verdict never holds a deploy over a law the push changed",
     "file": "tv/proof_shard.py",
     "find": "    held = [g for g in mine if g in owed]\n",
     "replace": "    held = []\n",
     "matches": 1},
    {"why": "REG-2962 - a Mac-only law the hook proved holds the CI deploy",
     "file": "tv/proof_shard.py",
     "find": "    mine = sorted(set(names) - set(local))\n",
     "replace": "    mine = sorted(set(names))\n",
     "matches": 1},
    {"why": "REG-2962 - a red already standing on CI holds every deploy, changed or not",
     "file": "tv/proof_shard.py",
     "find": "    held = [g for g in mine if g in owed]\n",
     "replace": "    held = sorted(owed)\n",
     "matches": 1},
    {"why": "REG-2962 - a set that is not whole passes the verdict",
     "file": "tv/proof_shard.py",
     "find": "    if ok and len(shards) != int(n):\n        ok, why = False, \"%d of %d shards\" % (len(shards), int(n))\n    if not ok:\n        say(\"  ✗ REG-2962 DEPLOY HELD: the proof set is not whole",
     "replace": "    ok = True\n    if not ok:\n        say(\"  ✗ REG-2962 DEPLOY HELD: the proof set is not whole",
     "matches": 1},
    {"why": "REG-2962 - with no last publish the push's laws are none",
     "file": "tv/proof_shard.py",
     "find": "        return sorted(set(n for n, _f in _H.gate_files(say=lambda *a, **k: None)))\n",
     "replace": "        return []\n",
     "matches": 1},
    {"why": "REG-2962 - the deploy publishes without waiting for the proof job",
     "file": ".github/workflows/publish.yml",
     "find": "    needs: [smoke, suites, review, proof]\n",
     "replace": "    needs: [smoke, suites, review]\n",
     "matches": 1},
    {"why": "REG-2962 - in Publish's gate a shard fails the run on any law, so a red standing on CI stops every deploy",
     "file": ".github/actions/prove-shard/action.yml",
     "find": "          echo \"deploy gate: rc=$rc is the fan-in verdict's to judge\"\n          exit 0\n",
     "replace": "          echo \"deploy gate: rc=$rc is the fan-in verdict's to judge\"\n          exit $rc\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main()
