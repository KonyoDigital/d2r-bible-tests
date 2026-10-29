# -*- coding: utf-8 -*-
"""REG-3085 - A SHARD THE RUNNER KILLED IS PROVED AGAIN ONCE, FROM EVIDENCE; A RED IS NEVER TRIED TWICE.

MEASURED on Publish 40812615686 attempt 1 (v3838): shard 7's prove step ended "Process completed with exit code 143", its
own log reads "##[error]The runner has received a shutdown signal. ...", its upload step was skipped, the fan-in refused
the set (exit 2) and the deploy was skipped - over a runner GitHub took away, not over a law. A synthetic kill cannot be
made on CI, so this law holds tv/proof_triage.py's decision on job-API JSON shaped as that run recorded it:
  * a shutdown line in the job's own log + no finished manifest -> proved again, once;
  * a timeout, a law red, a crash with no runner-loss line -> refused (never proved twice);
  * the jobs API or a job log that will not read -> UNKNOWN, refused - never a guess toward a deploy;
  * a shard proved again already ("shard <k> again") -> refused: exactly one retry;
  * a finished manifest that did arrive -> nothing to prove again.
And proof-keys-shards.yml as it is built around it: `triage` (actions: read, no write anywhere) after the shards,
`shard-again` proving exactly the triaged list through the SAME composite action with the SAME inputs (so the same
manifest), the fan-in waiting for both and refusing a set the retry did not complete. RED_PROOF below.
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
from console_safe import enable as _enable  # noqa: E402
_enable()

import proof_shard as PS  # noqa: E402
import proof_triage as T  # noqa: E402

WF = os.path.join(ROOT, ".github", "workflows", "proof-keys-shards.yml")
ACT = os.path.join(ROOT, ".github", "actions", "prove-shard", "action.yml")
HEAD = "a" * 40

# the measured run's own lines (Publish 40812615686, shard 7)
KILLED_LOG = ("2026-10-29T04:17:15.5421260Z   · a proving lane is working - 13 line(s) of its gate held until the gate ends\n"
              "2026-10-29T04:17:30.0705463Z ##[error]Process completed with exit code 143.\n"
              "2026-10-29T04:17:30.0774612Z ##[error]The runner has received a shutdown signal. This can happen when the "
              "runner service is stopped, or a manually started runner is canceled.\n"
              "2026-10-29T04:17:30.4205618Z Cleaning up orphan processes\n")
RED_LOG = ("     test_x[0]  RED (a proof did not go red)\n"
           "2026-10-29T04:17:30.0705463Z ##[error]Process completed with exit code 1.\n")
TIMEOUT_LOG = ("the prove ran past 160 minutes and was stopped\n"
               "2026-10-29T04:17:30.0705463Z ##[error]Process completed with exit code 124.\n")


def _job(k, conclusion="failure", status="completed", again=False, reusable=True, jid=None):
    name = ("Prove the laws (16 runners) / " if reusable else "") + ("shard %d again" % k if again else "shard %d" % k)
    return {"id": jid or (123246235526 + k), "name": name, "status": status, "conclusion": conclusion}


def _run(jobs, logs, root, n=2):
    return T.triage(n, jobs, lambda j: logs.get(j["id"]), root)


def _code(path):
    with io.open(path, encoding="utf-8") as fh:
        return "\n".join(l for l in fh.read().split("\n") if not l.lstrip().startswith("#"))


def _job_text(code, name):
    m = re.search(r"\n  %s:\n(.*?)(?=\n  [A-Za-z][\w-]*:\n|\Z)" % re.escape(name), "\n" + code.split("\njobs:\n", 1)[-1] + "\n",
                  re.S)
    return m.group(1) if m else ""


def _manifest(root, k, n=2, finished=True):
    d = os.path.join(root, "proof-shard-%d" % k)
    os.makedirs(d, exist_ok=True)
    m = PS.manifest(k, n, HEAD, False, "p1", {"g%d" % k: {0}}, None, None, 1761200000000)
    m["finished"] = finished
    with io.open(os.path.join(d, PS.STORE_NAME), "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"format": 2, "shard": m,
                             "entries": {"e%d" % k: {"verdict": "PROVEN", "gate": "g%d" % k, "proof": 0, "provedAt": 1,
                                                     "tree": "/home/runner/work/x/x"}}}))


class TriageDecidesFromEvidence(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        _manifest(self.root, 1)

    def test_a_runner_shutdown_with_no_manifest_is_proved_again(self):
        jobs = [_job(1, "success"), _job(2)]
        dead, why = _run(jobs, {jobs[1]["id"]: KILLED_LOG}, self.root)
        self.assertEqual(dead, [2], why)
        self.assertIn("proved again once", why[1])

    def test_the_same_kill_in_a_run_of_its_own_names_is_seen(self):
        jobs = [_job(1, "success", reusable=False), _job(2, reusable=False)]
        self.assertEqual(_run(jobs, {jobs[1]["id"]: KILLED_LOG}, self.root)[0], [2])

    def test_a_law_red_is_never_proved_twice(self):
        jobs = [_job(1, "success"), _job(2)]
        dead, why = _run(jobs, {jobs[1]["id"]: RED_LOG}, self.root)
        self.assertEqual(dead, [], "a red was re-run - a flaky red would be laundered into a deploy")
        self.assertIn("never proved twice", why[1])

    def test_a_timeout_is_not_a_kill(self):
        jobs = [_job(1, "success"), _job(2)]
        self.assertEqual(_run(jobs, {jobs[1]["id"]: TIMEOUT_LOG}, self.root)[0], [])

    def test_an_unreadable_log_or_job_list_is_unknown_never_a_kill(self):
        jobs = [_job(1, "success"), _job(2)]
        dead, why = _run(jobs, {}, self.root)
        self.assertEqual(dead, [], "a log nobody read was taken as a runner kill")
        self.assertIn("could not be read", why[1])
        dead, why = _run(None, {}, self.root)
        self.assertEqual(dead, [], "a job list nobody read re-proved shards")
        self.assertIn("could not be read", why[0])

    def test_a_second_kill_is_never_proved_a_third_time(self):
        jobs = [_job(1, "success"), _job(2), _job(2, again=True, jid=99)]
        dead, why = _run(jobs, {jobs[1]["id"]: KILLED_LOG, 99: KILLED_LOG}, self.root)
        self.assertEqual(dead, [], "a shard already proved again was proved again")
        self.assertIn("one retry", why[1])

    def test_a_finished_manifest_is_nothing_to_prove_again(self):
        _manifest(self.root, 2)
        jobs = [_job(1, "success"), _job(2)]
        self.assertEqual(_run(jobs, {jobs[1]["id"]: KILLED_LOG}, self.root)[0], [])

    def test_two_jobs_of_one_name_or_none_at_all_are_unknown(self):
        jobs = [_job(1, "success"), _job(2), _job(2, jid=77)]
        self.assertEqual(_run(jobs, {jobs[1]["id"]: KILLED_LOG, 77: KILLED_LOG}, self.root)[0], [])
        self.assertEqual(_run([_job(1, "success")], {}, self.root)[0], [])

    def test_the_infra_lines_are_the_runners_own(self):
        for ln in T.INFRA_LINES:
            self.assertNotIn(ln, RED_LOG + TIMEOUT_LOG)
        self.assertIn("The runner has received a shutdown signal.", T.INFRA_LINES)


class TheWorkflowRetriesOnceThroughTheSameProve(unittest.TestCase):

    def setUp(self):
        self.code = _code(WF)

    def test_triage_reads_only_and_runs_after_every_shard(self):
        t = _job_text(self.code, "triage")
        self.assertIn("    needs: [shard]\n    if: ${{ always() }}\n", t)
        self.assertRegex(t, r"\n    permissions:\n      contents: read\n      actions: read\n")
        self.assertIn("dead: ${{ steps.triage.outputs.dead }}", t)
        self.assertIn('python3 tv/proof_triage.py --shards "$PROOF_SHARDS"', t)
        self.assertIn('--run "$GITHUB_RUN_ID"', t)
        self.assertIn('--attempt "$GITHUB_RUN_ATTEMPT" --root shards --out "$GITHUB_OUTPUT"', t)
        self.assertNotRegex(self.code, r":\s*write\b", "the shard workflow asks for a write scope")

    def test_shard_again_proves_exactly_the_triaged_list_through_the_same_action(self):
        a = _job_text(self.code, "shard-again")
        s = _job_text(self.code, "shard")
        self.assertIn("    needs: [triage]\n", a)
        self.assertIn("shard: ${{ fromJSON(needs.triage.outputs.dead) }}", a)
        self.assertIn("needs.triage.outputs.dead != '[]'", a, "an empty list still starts a retry job")
        self.assertIn("    name: shard ${{ matrix.shard }} again\n", a)
        self.assertTrue(T._AGAIN.search("Prove the laws (16 runners) / shard 7 again"))
        with_s = s[s.find("uses: ./.github/actions/prove-shard"):]
        with_a = a[a.find("uses: ./.github/actions/prove-shard"):]
        self.assertTrue(with_s and with_a, "a prove job does not use the shared action")
        self.assertEqual(with_a.strip(), with_s.strip(), "the retry proves with other inputs than the shard did")
        for k in ("timeout-minutes: 180", 'D2R_NO_CLAUDE: "1"', 'HEART2_PROVE_WORKERS: "2"', "fetch-depth: 200"):
            self.assertIn(k, a, "the retry runs under other conditions than the shard: %s" % k)

    def test_exactly_one_retry_and_the_fan_in_waits_for_it(self):
        self.assertEqual(re.findall(r"needs: \[[^\]]*shard-again[^\]]*\]", self.code), ["needs: [shard, triage, shard-again]"],
                         "something besides the fan-in waits for the retry, or the fan-in does not")
        self.assertNotIn("shard-again", _job_text(self.code, "triage"), "the retry is triaged again")
        f = _job_text(self.code, "fan-in")
        self.assertIn("    if: ${{ always() }}\n", f)
        self.assertIn("pattern: proof-shard-*", f)
        act = _code(ACT)
        self.assertIn("name: proof-shard-${{ inputs.shard }}", act, "the retry uploads where the fan-in does not look")
        self.assertIn("overwrite: true", act)


class TheFanInRefusesASetTheRetryDidNotComplete(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_a_retried_shard_completes_the_set_and_a_failed_retry_refuses_it(self):
        _manifest(self.root, 1)
        said = []
        self.assertEqual(PS.fan_in(self.root, 2, HEAD, say=said.append), 2, "a set with the killed shard missing passed")
        _manifest(self.root, 2)          # shard-again's upload: the same manifest shape the shard writes
        said = []
        self.assertEqual(PS.fan_in(self.root, 2, HEAD, say=said.append), 0, said)
        shutil.rmtree(os.path.join(self.root, "proof-shard-2"))
        _manifest(self.root, 2, finished=False)          # the retry was killed too
        self.assertEqual(PS.fan_in(self.root, 2, HEAD, say=lambda *a: None), 2, "an unfinished retry passed the fan-in")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {"why": "REG-3085 - any failed shard is proved again: a flaky red is laundered into a deploy",
     "file": "tv/proof_triage.py",
     "find": "    if not hit:\n        return False, (",
     "replace": "    if False:\n        return False, (",
     "matches": 1},
    {"why": "REG-3085 - a log nobody read is taken as a runner kill",
     "file": "tv/proof_triage.py",
     "find": "    if log_text is None:\n        return False,",
     "replace": "    if log_text is None:\n        return True,",
     "matches": 1},
    {"why": "REG-3085 - a job list nobody read re-proves every shard",
     "file": "tv/proof_triage.py",
     "find": "    if jobs is None:\n        return [], [",
     "replace": "    if jobs is None:\n        return list(range(1, int(n) + 1)), [",
     "matches": 1},
    {"why": "REG-3085 - a shard proved again is proved again a second time",
     "file": "tv/proof_triage.py",
     "find": "    if again:\n        return False,",
     "replace": "    if False:\n        return False,",
     "matches": 1},
    {"why": "REG-3085 - a shard whose finished manifest arrived is proved again",
     "file": "tv/proof_triage.py",
     "find": "    if have_manifest:\n        return False,",
     "replace": "    if False:\n        return False,",
     "matches": 1},
    {"why": "REG-3085 - the fan-in does not wait for the retry, so the killed shard's absence is judged before it lands",
     "file": ".github/workflows/proof-keys-shards.yml",
     "find": "    needs: [shard, triage, shard-again]\n",
     "replace": "    needs: [shard, triage]\n",
     "matches": 1},
    {"why": "REG-3085 - the retry proves through another step than the shard, so its manifest may differ",
     "file": ".github/workflows/proof-keys-shards.yml",
     "find": "      - name: Prove shard ${{ matrix.shard }} again\n        uses: ./.github/actions/prove-shard\n        with:\n          shard: ${{ matrix.shard }}\n",
     "replace": "      - name: Prove shard ${{ matrix.shard }} again\n        uses: ./.github/actions/prove-shard\n        with:\n          shard: ${{ matrix.shard }}\n          gate: deploy\n",
     "matches": 1},
    {"why": "REG-3085 - triage asks for a write scope it does not need",
     "file": ".github/workflows/proof-keys-shards.yml",
     "find": "    permissions:\n      contents: read\n      actions: read\n    outputs:\n",
     "replace": "    permissions:\n      contents: read\n      actions: write\n    outputs:\n",
     "matches": 1},
]
