# -*- coding: utf-8 -*-
"""REG-3085 - A SHARD THE RUNNER KILLED IS PROVED AGAIN ONCE; A SHARD THAT FAILED IS NEVER TRIED TWICE.

MEASURED on Publish 40812615686, attempt 1 (v3838, 2026-10-29): shard 7's prove step ended with exit 143 and its own log
reads "##[error]The runner has received a shutdown signal. This can happen when the runner service is stopped, or a
manually started runner is canceled." Its upload step was skipped, so no manifest reached the fan-in, the fan-in refused
the set (exit 2) and the deploy was skipped: the site stayed on v3836 over a runner GitHub took away, not over a law.

proof-keys-shards.yml now runs `triage` after the 16 shards. It names the shards to prove once more (`shard-again`), and
the fan-in waits for both. A shard is re-proved ONLY when all three hold, read from evidence:
  1. its job (this run attempt, named "shard <k>") concluded failure or cancelled;
  2. its OWN log carries a runner-loss line (INFRA_LINES) - the job API's log, not a guess from the exit code;
  3. no FINISHED shard manifest of it reached this job (its store under <root>/proof-shard-<k>/).
Everything else is not re-proved, and the fan-in then refuses the set exactly as before:
  * a job that succeeded (its manifest decides at the fan-in);
  * a failure with no runner-loss line - a law red on a ci/proof-keys push, a crash, a 160-minute timeout;
  * a job or a log that could not be read - UNKNOWN is never a kill, and never guessed toward a deploy;
  * a shard proved again already ("shard <k> again" in this attempt): one retry, never a second.
In Publish's deploy gate a law red never fails its job (it is named in the manifest), so this cannot launder a red: the
retry needs the runner-loss line, and a red never writes one.
    python3 tv/proof_triage.py --shards N --repo OWNER/NAME --run ID --attempt K --root DIR [--out FILE] [--summary FILE]
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import proof_shard as PS  # noqa: E402

#: the lines GitHub writes into a job's own log when the runner, not the job, went away. Exact text, never a pattern
#: loose enough to match a law's output.
INFRA_LINES = (
    "The runner has received a shutdown signal.",                  # Publish 40812615686, shard 7 (measured)
    "lost communication with the server.",                         # GitHub-hosted runner lost mid-job
)
_SHARD = re.compile(r"(?:^|/ )shard (\d+)$")
_AGAIN = re.compile(r"(?:^|/ )shard (\d+) again\b")


def shard_jobs(jobs):
    """-> ({k: job}, {k: [again jobs]}) from one run attempt's job list. Two jobs named "shard <k>" is UNKNOWN: None."""
    first, again = {}, {}
    for j in jobs or []:
        name = str((j or {}).get("name") or "")
        m = _SHARD.search(name)
        if m:
            k = int(m.group(1))
            if k in first:
                first[k] = None
            else:
                first[k] = j
            continue
        m = _AGAIN.search(name)
        if m:
            again.setdefault(int(m.group(1)), []).append(j)
    return first, again


def finished_manifest(root, k):
    """Did a FINISHED manifest of shard k reach this job? -> True | False (absent, unreadable or unfinished)"""
    p = os.path.join(root, "proof-shard-%d" % k, PS.STORE_NAME)
    try:
        with io.open(p, encoding="utf-8") as fh:
            m = (json.load(fh) or {}).get("shard")
    except FileNotFoundError:
        return False
    except Exception:
        return False
    return isinstance(m, dict) and m.get("v") == PS.MANIFEST_V and m.get("k") == k and m.get("finished") is True


def decide(k, job, log_text, have_manifest, again=None):
    """REG-3085 - prove shard k once more? -> (bool, why). log_text None means its log could not be read."""
    if again:
        return False, "shard %d: proved again already in this attempt - one retry, never a second" % k
    if job is None:
        return False, "shard %d: no single job of this attempt is named 'shard %d' - UNKNOWN, not re-proved" % (k, k)
    if job.get("status") != "completed":
        return False, "shard %d: its job is %s, not completed - UNKNOWN, not re-proved" % (k, job.get("status"))
    concl = job.get("conclusion")
    if concl == "success":
        return False, "shard %d: finished - its manifest decides at the fan-in" % k
    if concl not in ("failure", "cancelled"):
        return False, "shard %d: concluded %s - not a kill, not re-proved" % (k, concl)
    if log_text is None:
        return False, "shard %d: %s, and its log could not be read - UNKNOWN is not a kill, the deploy refuses" % (k, concl)
    hit = [ln for ln in INFRA_LINES if ln in log_text]
    if not hit:
        return False, ("shard %d: %s with no runner-loss line in its own log - a red, a crash or a timeout is never "
                       "proved twice" % (k, concl))
    if have_manifest:
        return False, "shard %d: a finished manifest reached the fan-in - nothing to prove again" % k
    return True, "shard %d: the runner went away under it (%r) and it left no finished manifest - proved again once" % (
        k, hit[0])


def triage(n, jobs, log_of, root):
    """-> (dead [k], reasons [str]). jobs None = the job list could not be read: nothing is re-proved."""
    if jobs is None:
        return [], ["the run's job list could not be read - UNKNOWN, so no shard is proved again and the fan-in "
                    "refuses any missing one"]
    first, again = shard_jobs(jobs)
    dead, why = [], []
    for k in range(1, int(n) + 1):
        job = first.get(k)
        log = None
        if job and job.get("status") == "completed" and job.get("conclusion") in ("failure", "cancelled") \
                and not again.get(k):
            log = log_of(job)
        ok, w = decide(k, job, log, finished_manifest(root, k), again.get(k))
        why.append(w)
        if ok:
            dead.append(k)
    return dead, why


def _gh(args, timeout=60):
    """`gh api` -> stdout text, or None when it could not answer (UNKNOWN)."""
    try:
        r = subprocess.run(["gh", "api"] + list(args), capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None
    return r.stdout if r.returncode == 0 else None


def jobs_of(repo, run, attempt):
    out, page = [], 1
    while True:
        txt = _gh(["repos/%s/actions/runs/%s/attempts/%s/jobs?per_page=100&page=%d" % (repo, run, attempt, page)])
        if txt is None:
            return None
        try:
            got = json.loads(txt).get("jobs")
        except Exception:
            return None
        if not isinstance(got, list):
            return None
        out += got
        if len(got) < 100:
            return out
        page += 1


def main(argv):
    def arg(name, default=None):
        return argv[argv.index(name) + 1] if name in argv else default
    n, repo, run, attempt, root = arg("--shards"), arg("--repo"), arg("--run"), arg("--attempt"), arg("--root", "shards")
    if not (n and repo and run and attempt):
        print(__doc__)
        return 2
    jobs = jobs_of(repo, run, attempt)
    dead, why = triage(int(n), jobs, lambda j: _gh(["repos/%s/actions/jobs/%s/logs" % (repo, j.get("id"))], 120), root)
    for w in why:
        print(w)
    print("dead=%s" % json.dumps(dead))
    out = arg("--out")
    if out:
        with io.open(out, "a", encoding="utf-8") as fh:
            fh.write("dead=%s\n" % json.dumps(dead, separators=(",", ":")))
    summ = arg("--summary")
    if summ:
        with io.open(summ, "a", encoding="utf-8") as fh:
            fh.write("## Shard triage (REG-3085)\n\n" + ("Proved again once: %s\n\n" % dead if dead else
                     "No shard is proved again.\n\n") + "\n".join("- " + w for w in why) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
