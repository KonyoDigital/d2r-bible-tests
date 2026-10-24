# -*- coding: utf-8 -*-
"""REG-2633 - A COMMIT'S PROOF BANK IS PUBLISHED TO origin/proof-bank, OR THE RUN THAT OWED IT IS RED.

Linux bank only (owner ruling 2026-10-24): the Linux census (proof-keys-shards.yml, job `bank`) is the one live
producer. The Windows census (proof-bank-windows.yml, job `win-bank`) is kept but OFF - manual dispatch only, and every
Windows job starts only on a ci/proof-keys-* ref. This law reads both workflows - every publish step can only fail its
job, never shrug, never be skipped - and DRIVES the publisher over a temp bare remote: a bank lands and reads back where self_prove looks for
it; every bad export (missing, empty, other commit, dirty, other class, a machine path) and an unreachable remote is
exit 1 with "PROOF BANK REFUSED"; a linux and a windows bank racing both land (the publisher keeps that path); old banks are pruned to KEEP.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import proof_bank as PB  # noqa: E402
import self_prove as SP  # noqa: E402

LINUX_WF = os.path.join(ROOT, ".github", "workflows", "proof-keys-shards.yml")
WIN_WF = os.path.join(ROOT, ".github", "workflows", "proof-bank-windows.yml")
H1, H2, H3 = "a" * 40, "b" * 40, "c" * 40

RED_PROOF = [
    {"why": "REG-2633 - an empty export is published as a bank that serves nothing",
     "file": "proof_bank.py",
     "find": '    if len(ent) < 1 or m.get("entries") != len(ent):\n',
     "replace": "    if False:\n", "matches": 1},
    {"why": "REG-2633 - another commit's export is published under this commit's name",
     "file": "proof_bank.py",
     "find": '    if m.get("head") != head:\n',
     "replace": "    if False:\n", "matches": 1},
    {"why": "REG-2633 - a Linux runner publishes a .windows bank (its keys never meet a Windows PC's)",
     "file": "proof_bank.py",
     "find": "    if platform_class != cls:\n",
     "replace": "    if False:\n", "matches": 1},
    {"why": "REG-2633 - a bank carrying a machine path is published",
     "file": "proof_bank.py",
     "find": "    for rx in PRIVATE:\n",
     "replace": "    for rx in ():\n", "matches": 1},
    {"why": "REG-2633 - a dirty tree's export is published",
     "file": "proof_bank.py",
     "find": '    if m.get("dirty") is not False:\n',
     "replace": "    if False:\n", "matches": 1},
    {"why": "REG-2633 - old banks are never pruned (the branch grows without bound)",
     "file": "proof_bank.py",
     "find": "            for old in prune(order, keep):\n",
     "replace": "            for old in []:\n", "matches": 1},
    {"why": "REG-2633 - the Linux publish step shrugs off a failed publish",
     "file": ".github/workflows/proof-keys-shards.yml",
     "find": '          python3 tv/proof_bank.py --publish "$RUNNER_TEMP/out/.heart2_cache.json" --head "$GITHUB_SHA" --class linux\n',
     "replace": '          python3 tv/proof_bank.py --publish "$RUNNER_TEMP/out/.heart2_cache.json" --head "$GITHUB_SHA" --class linux || true\n',
     "matches": 1},
    {"why": "REG-2633 - the Windows bank job runs whatever the fan-in said",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": '        run: python tv/proof_shard.py --fan-in shards --shards "$WIN_PROOF_SHARDS" --head "$GITHUB_SHA"\n',
     "replace": '        run: python tv/proof_shard.py --fan-in shards --shards "$WIN_PROOF_SHARDS" --head "$GITHUB_SHA" || true\n',
     "matches": 1},
    {"why": "REG-2633 - the Windows producer no longer insists on the PCs' eol conversion",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": '          test "$v" = "true" || {',
     "replace": '          true || {', "matches": 2},
    {"why": "REG-2633 - the scratch repo pushes without the checkout's token header (anonymous push, never lands)",
     "file": "proof_bank.py",
     "find": '        for line in (hdrs.splitlines() if rc == 0 else []):\n',
     "replace": '        for line in []:\n', "matches": 1},
    {"why": "REG-2633 - a failed first push onto a new branch aborts the retries (orphan refused)",
     "file": "proof_bank.py",
     "find": '                _must(work, "symbolic-ref", "HEAD", "refs/heads/%s" % branch)\n',
     "replace": '                _must(work, "checkout", "-q", "--orphan", branch)\n', "matches": 1},
    {"why": "REG-2633 - a retried orphan keeps the rejected commit as its parent",
     "file": "proof_bank.py",
     "find": '                _must(work, "update-ref", "-d", "refs/heads/%s" % branch)\n',
     "replace": '', "matches": 1},
    {"why": "REG-2633 - the publisher never compares what origin serves back",
     "file": "proof_bank.py",
     "find": "        if rc != 0 or back != text:\n",
     "replace": "        if False:\n", "matches": 1},
    {"why": "REG-2633 - the Windows bank job keys whatever bytes its checkout holds",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": "sys.exit(0 if b'\\r\\n' in b else",
     "replace": "sys.exit(0 if True else", "matches": 2},
    {"why": "REG-2633 - the Windows CRLF probe is shrugged off",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": "not the bytes a Windows PC keys')\"\n",
     "replace": "not the bytes a Windows PC keys')\" || true\n", "matches": 2},
    {"why": "REG-2633 - the Windows dirty-checkout check is shrugged off",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": '          test -z "$(git status --porcelain)" || {',
     "replace": '          test -z "$(git status --porcelain)" || true # {', "matches": 2},
    {"why": "REG-2633 - a public why quoting a user folder refuses the whole bank",
     "file": "proof_bank.py",
     "find": 'if f != "why") if',
     "replace": 'if f != "why_") if', "matches": 1},
    {"why": "REG-2633 - the publisher stamps an LF tree as a .windows bank",
     "file": "proof_bank.py",
     "find": '    if b"\\r\\n" not in b:\n',
     "replace": '    if False:\n', "matches": 1},
    {"why": "REG-2633 - the publisher accepts any autocrlf for a .windows bank",
     "file": "proof_bank.py",
     "find": '    if v.strip() != "true":\n',
     "replace": '    if False:\n', "matches": 1},
    {"why": "REG-2633 - a .windows bank skips the bytes check",
     "file": "proof_bank.py",
     "find": '    if cls == "windows":\n        windows_bytes(repo)\n',
     "replace": '', "matches": 1},
    {"why": "REG-2633 - a dispatch from main publishes the Linux bank",
     "file": ".github/workflows/proof-keys-shards.yml",
     "find": "    if: ${{ startsWith(github.ref, 'refs/heads/ci/proof-keys-') }}\n",
     "replace": "", "matches": 1},
    {"why": "REG-2633 - the disabled Windows producer triggers on every ci/proof-keys-* push again",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": "on:\n  workflow_dispatch:\n",
     "replace": "on:\n  push:\n    branches:\n      - 'ci/proof-keys-*'\n  workflow_dispatch:\n", "matches": 1},
    {"why": "REG-2633 - the disabled Windows producer runs on a schedule",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": "on:\n  workflow_dispatch:\n",
     "replace": "on:\n  schedule:\n    - cron: '0 3 * * *'\n  workflow_dispatch:\n", "matches": 1},
    {"why": "REG-2633 - the disabled Windows producer is turned on with a spaced YAML key (push :)",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": "on:\n  workflow_dispatch:\n",
     "replace": "on:\n  push :\n    branches: ['ci/proof-keys-*']\n  workflow_dispatch:\n", "matches": 1},
    {"why": "REG-2633 - a dispatch from main starts 16 billed Windows shard runners",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": "    # billing guard: a dispatch from main (or any non-ci ref) starts no Windows runner at all\n    if: ${{ startsWith(github.ref, 'refs/heads/ci/proof-keys-') }}\n",
     "replace": "", "matches": 1},
    {"why": "REG-2633 - `&& false` on win-bank's guard skips the bank and the job is green",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": "    if: ${{ always() && startsWith(github.ref, 'refs/heads/ci/proof-keys-') }}\n",
     "replace": "    if: ${{ always() && startsWith(github.ref, 'refs/heads/ci/proof-keys-') && false }}\n", "matches": 1},
    {"why": "REG-2633 - a step-level if skips the Linux publish",
     "file": ".github/workflows/proof-keys-shards.yml",
     "find": "      - name: Import the set, export what this tree keys, publish it\n",
     "replace": "      - name: Import the set, export what this tree keys, publish it\n        if: false\n", "matches": 1},
    {"why": "REG-2633 - the Linux publish step turns errexit back off",
     "file": ".github/workflows/proof-keys-shards.yml",
     "find": '          set -euo pipefail\n          export HEART2_CACHE_PATH="$RUNNER_TEMP/bank/.heart2_cache.json"\n',
     "replace": '          set -euo pipefail\n          set +e\n          export HEART2_CACHE_PATH="$RUNNER_TEMP/bank/.heart2_cache.json"\n',
     "matches": 1},
    {"why": "REG-2633 r16 - push hides in an on: [...] list that wraps across lines",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": "on:\n  workflow_dispatch:\n",
     "replace": "on: [workflow_dispatch,\n  push]\n", "matches": 1},
    {"why": "REG-2633 r16 - exit 0 above the Linux publish command: the publish never runs and the step is green",
     "file": ".github/workflows/proof-keys-shards.yml",
     "find": '          python3 tv/heart2.py --export-proved "$RUNNER_TEMP/out"\n',
     "replace": '          python3 tv/heart2.py --export-proved "$RUNNER_TEMP/out"\n          exit 0\n', "matches": 1},
    {"why": "REG-2633 r16 - a quoted \"if\": false skips the Linux publish step",
     "file": ".github/workflows/proof-keys-shards.yml",
     "find": "      - name: Import the set, export what this tree keys, publish it\n",
     "replace": "      - name: Import the set, export what this tree keys, publish it\n        \"if\": false\n", "matches": 1},
    {"why": "REG-2633 r16 - a new Windows job with no ref guard bills a runner on a dispatch from main",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": "jobs:\n  win-shard:\n",
     "replace": "jobs:\n  extra-win:\n    runs-on: windows-latest\n    steps:\n      - run: echo hi\n  win-shard:\n", "matches": 1},
    {"why": "REG-2633 r16 - proof_bank.py's docstring describes a live Windows writer again",
     "file": "proof_bank.py",
     "find": "Linux bank only",
     "replace": "Two CI producers", "matches": 1},
    {"why": "REG-2633 r17 - { exit 0; } above the Linux publish: the shell leaves green before publishing",
     "file": ".github/workflows/proof-keys-shards.yml",
     "find": '          python3 tv/heart2.py --export-proved "$RUNNER_TEMP/out"\n',
     "replace": '          python3 tv/heart2.py --export-proved "$RUNNER_TEMP/out"\n          { exit 0; }\n', "matches": 1},
    {"why": "REG-2633 r17 - `true ||` in front of the Linux publish command",
     "file": ".github/workflows/proof-keys-shards.yml",
     "find": '          python3 tv/proof_bank.py --publish "$RUNNER_TEMP/out/.heart2_cache.json" --head "$GITHUB_SHA" --class linux\n',
     "replace": '          true || python3 tv/proof_bank.py --publish "$RUNNER_TEMP/out/.heart2_cache.json" --head "$GITHUB_SHA" --class linux\n',
     "matches": 1},
    {"why": "REG-2633 r17 - an escaped \"\\u0069f\": false skips the Linux publish step",
     "file": ".github/workflows/proof-keys-shards.yml",
     "find": "      - name: Import the set, export what this tree keys, publish it\n",
     "replace": "      - name: Import the set, export what this tree keys, publish it\n        \"\\u0069f\": false\n", "matches": 1},
    {"why": "REG-2633 r17 - win-shard's guard continued with || true on the next line (always true on GitHub)",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": "    if: ${{ startsWith(github.ref, 'refs/heads/ci/proof-keys-') }}\n    runs-on: windows-latest\n",
     "replace": "    if: ${{ startsWith(github.ref, 'refs/heads/ci/proof-keys-') }}\n      || true\n    runs-on: windows-latest\n",
     "matches": 1},
    {"why": "REG-2633 r17 - a second trigger key spelled !!str on turns push on",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": "on:\n  workflow_dispatch:\n",
     "replace": "on:\n  workflow_dispatch:\n!!str on:\n  push:\n", "matches": 1},
    {"why": "REG-2633 r17 - an explicit-key (? extra-win) Windows job hides from the billing scan",
     "file": ".github/workflows/proof-keys-shards.yml",
     "find": "jobs:\n  shard:\n",
     "replace": "jobs:\n  ? extra-win\n  :\n    runs-on: windows-latest\n    steps:\n      - run: echo hi\n  shard:\n", "matches": 1},
    {"why": "REG-2633 r17 - an escaped continue-on-error on the Windows bank job",
     "file": ".github/workflows/proof-bank-windows.yml",
     "find": "    timeout-minutes: 30\n",
     "replace": "    timeout-minutes: 30\n    \"continue-on-\\u0065rror\": true\n", "matches": 1},
]


def _read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def _job(text, name):
    m = re.search(r"\n  %s:\n(.*?)(?=\n  [A-Za-z][\w-]*:\n|\Z)" % re.escape(name),
                  "\n" + text.split("\njobs:\n", 1)[-1] + "\n", re.S)
    return m.group(1) if m else ""


_KEY = re.compile(r"""^(?P<ind> *)(?:"(?P<dq>[^"]*)"|'(?P<sq>[^']*)'|(?P<bare>[^\s:#'"\-][^:#]*?))\s*:(?:\s+(?P<val>.*?))?\s*$""")


def _uncomment(line):
    if line.lstrip().startswith("#"):
        return ""
    return re.sub(r"\s+#.*$", "", line).rstrip()


def _keyname(m):
    if m.group("dq") is not None:
        # a double-quoted YAML key reads its escapes: "\u006fn" is the key on
        try:
            return m.group("dq").encode("latin-1", "backslashreplace").decode("unicode_escape").strip()
        except (UnicodeDecodeError, UnicodeEncodeError):
            return m.group("dq").strip()
    return (m.group("sq") if m.group("sq") is not None else m.group("bare") or "").strip()


def triggers(text):
    """The events a workflow file starts on, read the way YAML reads keys (NO `import yaml` - CI bans it): a top-level
    key spelled on / "on" / 'on' / `on :` (YAML 1.1 also reads true/yes/y as that key), every child key at the next
    indent in any quoting or spacing, a `- event` list, and the flow forms `on: push` / `on: [push, schedule]`. More
    than one top-level trigger key is refused (a YAML parser keeps the last). -> [event]; raises AssertionError"""
    lines = [_uncomment(l) for l in text.splitlines()]
    heads = []
    for i, l in enumerate(lines):
        m = _KEY.match(l)
        if m and not m.group("ind") and _keyname(m).lower() in ("on", "true", "yes", "y"):
            heads.append((i, m.group("val")))
    assert len(heads) == 1, "%d top-level trigger keys" % len(heads)
    i, val = heads[0]
    if val and val.strip()[:1] in "[{":
        # a flow sequence/map may span lines: read on to its closing bracket
        close, j = {"[": "]", "{": "}"}[val.strip()[0]], i + 1
        while close not in val:
            assert j < len(lines), "an unclosed flow trigger list"
            val, j = val + " " + lines[j].strip(), j + 1
    if val:
        return [v.strip().strip("'\"") for v in val.strip().strip("[]{}").split(",") if v.strip()]
    out, ind = [], None
    for l in lines[i + 1:]:
        if not l.strip():
            continue
        assert "\t" not in l[:len(l) - len(l.lstrip())], "a tab-indented trigger line"
        lead = len(l) - len(l.lstrip(" "))
        if lead == 0:
            break
        ind = lead if ind is None else ind
        if lead != ind:
            continue
        if l.lstrip().startswith("-"):
            out.append(l.lstrip()[1:].strip().strip("'\""))
            continue
        m = _KEY.match(l)
        assert m, "an unreadable trigger line %r" % l
        out.append(_keyname(m))
    return out


GUARD = "startsWith(github.ref, 'refs/heads/ci/proof-keys-')"


def job_if(text, job):
    """The one job-level `if:` of a job, exactly as written. -> str or None"""
    ifs = re.findall(r"^    if\s*:\s*(.*?)\s*$", _job(text, job), re.M)
    assert len(ifs) <= 1, "%s has %d job-level ifs" % (job, len(ifs))
    return ifs[0] if ifs else None


def job_names(text):
    """Every job key directly under top-level `jobs:` (any quoting). -> [name]"""
    text = "\n" + text
    body = text.split("\njobs:\n", 1)[-1] if "\njobs:\n" in text else ""
    out = []
    for l in body.splitlines():
        l = _uncomment(l)
        if l and not l.startswith(" "):
            break
        m = _KEY.match(l)
        if m and m.group("ind") == "  ":
            out.append(_keyname(m))
    return out


def windows_jobs(text):
    """Jobs whose runs-on (inline, a list, a matrix expression or a following block) could be a Windows runner: any
    runs-on that is not plainly ubuntu-*. -> [name]"""
    out = []
    for name in job_names(text):
        m = re.search(r"\n  (?:\"%s\"|'%s'|%s)\s*:\n(.*?)(?=\n  \S|\Z)" % ((re.escape(name),) * 3),
                      "\n" + ("\n" + text).split("\njobs:\n", 1)[-1] + "\n", re.S)
        job = m.group(1) if m else ""
        r = re.search(r"(?m)^    (?:\"runs-on\"|'runs-on'|runs-on)\s*:(.*(?:\n      .*)*)", job)
        val = r.group(1).strip() if r else ""
        if not re.fullmatch(r"ubuntu-[\w.-]+", val):
            out.append(name)
    return out


#: the publish steps, byte for byte. A deny-list of shell/YAML tricks never ends ({ exit 0; }, `true ||`, "\u0069f",
#: an escaped continue-on-error ...); any added line, key or prefix in these steps is red.
PUBLISH_STEP = {
    "linux": ('name: Import the set, export what this tree keys, publish it\n'
              '        run: |\n'
              '          set -euo pipefail\n'
              '          export HEART2_CACHE_PATH="$RUNNER_TEMP/bank/.heart2_cache.json"\n'
              '          mkdir -p "$RUNNER_TEMP/bank"\n'
              '          python3 tv/heart2.py --import-shards shards/*/.heart2_cache.json\n'
              '          python3 tv/heart2.py --export-proved "$RUNNER_TEMP/out"\n'
              '          python3 tv/proof_bank.py --publish "$RUNNER_TEMP/out/.heart2_cache.json" --head "$GITHUB_SHA"'
              ' --class linux'),
    "windows": ('name: Import the set, export what this tree keys, publish it\n'
                '        run: |\n'
                '          set -euo pipefail\n'
                '          export HEART2_CACHE_PATH="$RUNNER_TEMP/bank/.heart2_cache.json"\n'
                '          mkdir -p "$RUNNER_TEMP/bank"\n'
                '          python tv/heart2.py --import-shards shards/*/.heart2_cache.json\n'
                '          python tv/heart2.py --export-proved "$RUNNER_TEMP/out"\n'
                '          python tv/proof_bank.py --publish "$RUNNER_TEMP/out/.heart2_cache.json" --head "$GITHUB_SHA"'
                ' --class windows'),
}
WIN_FAN_IN_STEP = ('name: Every shard finished, on this commit, on one plan\n'
                   '        run: python tv/proof_shard.py --fan-in shards --shards "$WIN_PROOF_SHARDS" --head "$GITHUB_SHA"')
TOP_KEYS = ("name", "on", "permissions", "concurrency", "env", "jobs")
JOBS = {"proof-keys-shards.yml": ["shard", "fan-in", "bank"], "proof-bank-windows.yml": ["win-shard", "win-bank"]}


def shape_errors(text):
    """What a plain line reader cannot vouch for, so it is refused outright: a top-level key that is not one bare
    known key exactly once (`!!str on`, `? on`, `"\u006fn"`, a second `jobs:`), a job key that is not bare at indent 2
    (`? extra-win`), a job-level key that is not bare at indent 4 (`"\u0069f"`, an escaped continue-on-error, a
    duplicate), and a job-level `if:` continued on the next line (`|| true` makes GitHub's if always true). -> [str]"""
    errs, top, lines = [], [], text.splitlines()
    in_jobs, job_keys = False, None
    for n, raw in enumerate(lines):
        l = _uncomment(raw)
        if not l.strip():
            continue
        lead = len(l) - len(l.lstrip(" "))
        if lead == 0:
            m = re.match(r"^([a-z]+):(?: .*)?$", l)
            if not m or m.group(1) not in TOP_KEYS:
                errs.append("top-level line %r" % l)
                continue
            top.append(m.group(1))
            in_jobs = m.group(1) == "jobs"
            continue
        if not in_jobs:
            continue
        if lead == 2:
            if not re.match(r"^  [a-z][a-z-]*:$", l):
                errs.append("job key %r" % l)
            job_keys = []
            continue
        if lead == 4:
            m = re.match(r"^    ([a-z][a-z-]*):(?: .*)?$", l)
            if not m:
                errs.append("job-level line %r" % l)
                continue
            if job_keys is not None and m.group(1) in job_keys:
                errs.append("duplicate job key %r" % l)
            if job_keys is not None:
                job_keys.append(m.group(1))
            if m.group(1) == "if":
                nxt = [x for x in (_uncomment(y) for y in lines[n + 1:]) if x.strip()][:1]
                if nxt and len(nxt[0]) - len(nxt[0].lstrip(" ")) > 4:
                    errs.append("a job if continued on the next line %r" % nxt[0])
        elif lead in (1, 3):
            errs.append("odd indent %r" % l)
    for k in TOP_KEYS:
        if top.count(k) > 1:
            errs.append("top-level %s: %d times" % (k, top.count(k)))
    return errs


def _publish_steps(job):
    """Each step's text in a job (split on '      - '). -> [str]"""
    return [s for s in re.split(r"\n      - ", "\n" + job) if s.strip()]


class TheWorkflowsCanOnlyFailLoud(unittest.TestCase):

    def _loud(self, job, cls, label):
        self.assertTrue(job, "%s: the bank job is gone - re-anchor this law" % label)
        self.assertNotIn("continue-on-error", job, "%s: a bank step may fail and the job still pass" % label)
        self.assertIn("contents: write", job, "%s: the bank job cannot push proof-bank" % label)
        run = [s for s in _publish_steps(job) if "proof_bank.py --publish" in s]
        self.assertEqual(len(run), 1, "%s: not exactly one publish step" % label)
        run = run[0]
        self.assertIn("set -euo pipefail", run, "%s: a failed import/export would run on to a publish" % label)
        for need in ("--import-shards shards/*/.heart2_cache.json", "--export-proved \"$RUNNER_TEMP/out\"",
                     "--head \"$GITHUB_SHA\" --class %s\n" % cls):
            self.assertIn(need, run + "\n", "%s: the publish step lost %r" % (label, need))
        self.assertNotIn("|| true", run, "%s: the publish step shrugs off a failure" % label)
        self.assertNotRegex(run, r"set\s+\+[a-z]*e|set\s+\+o\s+errexit|set\s+\+o\s+pipefail",
                            "%s: the publish step turns errexit/pipefail back off" % label)
        last = [l.strip() for l in run.splitlines() if l.strip()][-1]
        self.assertIn("proof_bank.py --publish", last,
                      "%s: something runs after the publish, and its exit code is the step's" % label)
        self.assertNotRegex(run, r"\|\|\s*(exit 0|:)", "%s: the publish step shrugs off a failure" % label)
        self.assertEqual(run.strip(), PUBLISH_STEP[cls],
                         "%s: the publish step is not the pinned bytes - an added line, key or prefix can skip or "
                         "shrug the publish (exit before it, `true ||`, a step if in any spelling)" % label)
        fan = [s for s in _publish_steps(job) if "--fan-in" in s]
        for s in fan:
            self.assertNotIn("|| true", s, "%s: a refused fan-in would still publish" % label)

    def test_the_linux_census_publishes_after_a_whole_fan_in_or_goes_red(self):
        text = _read(LINUX_WF)
        job = _job(text, "bank")
        self._loud(job, "linux", "proof-keys-shards.yml")
        self.assertIn("needs: [fan-in]", job, "the Linux bank does not wait for a whole set")
        self.assertNotIn("always()", job, "the Linux bank runs after a refused fan-in")
        self.assertIn("runs-on: ubuntu-latest", job)
        self.assertIn("name: proof-shards-${{ github.sha }}", job, "the Linux bank does not read this commit's set")
        self.assertIn("\npermissions:\n  contents: read\n", text, "the shard workflow's default token is not read-only")

    def test_the_windows_census_proves_the_same_plan_and_publishes_or_goes_red(self):
        text, lin = _read(WIN_WF), _read(LINUX_WF)
        n = re.findall(r'^  WIN_PROOF_SHARDS: "(\d+)"$', text, re.M)
        ln = re.findall(r'^  PROOF_SHARDS: "(\d+)"$', lin, re.M)
        self.assertEqual(len(n), 1)
        self.assertEqual(n, ln, "the Windows census cuts another plan than the Linux one")
        m = re.search(r"^        shard: \[([\d, ]+)\]$", text, re.M)
        self.assertEqual([int(x) for x in m.group(1).split(",")], list(range(1, int(n[0]) + 1)))
        shard = _job(text, "win-shard")
        self.assertIn("runs-on: windows-latest", shard)
        self.assertIn('--proof-shard "${{ matrix.shard }}/${WIN_PROOF_SHARDS}"', shard)
        self.assertIn('test "$v" = "true"', shard, "the Windows producer does not insist on the PCs' autocrlf")
        self.assertLess(shard.index("core.autocrlf"), shard.index("actions/checkout"),
                        "autocrlf is asked after the checkout already converted the tree")
        for jn, j in (("win-shard", shard), ("win-bank", _job(text, "win-bank"))):
            self.assertIn('test "$v" = "true"', j, "%s does not insist on the PCs' autocrlf" % jn)
            self.assertLess(j.index("core.autocrlf"), j.index("actions/checkout"), jn)
            self.assertIn("b'\\r\\n' in b", j, "%s never looks for CRLF on disk after its checkout" % jn)
            self.assertLess(j.index("actions/checkout"), j.index("b'\\r\\n' in b"), jn)
            self.assertIn('test -z "$(git status --porcelain)"', j, "%s may key a dirty checkout" % jn)
            for step in _publish_steps(j):
                if not any(w in step for w in ("core.autocrlf", "b'\\r\\n'", "git status --porcelain")):
                    continue
                self.assertNotIn("continue-on-error", step, jn)
                for line in step.splitlines():
                    if "||" not in line:
                        continue
                    ok = line.strip() == 'v=$(git config --get core.autocrlf || true)' or \
                        re.search(r"\|\| \{ .*exit 1; \}$", line.strip())
                    self.assertTrue(ok, "%s: a byte check can be shrugged off: %r" % (jn, line.strip()))
        self.assertIn("claude.cmd", shard, "on Windows a `claude` sh script is not what a subprocess finds")
        self.assertIn("exit /b 97", shard)
        job = _job(text, "win-bank")
        self._loud(job, "windows", "proof-bank-windows.yml")
        self.assertIn("needs: [win-shard]", job)
        self.assertIn("runs-on: windows-latest", job, "a Windows bank keyed on another class never meets a PC's key")
        self.assertTrue(any("--fan-in" in s for s in _publish_steps(job)), "the Windows bank skips the fan-in")
        self.assertEqual([s.strip() for s in _publish_steps(job) if "--fan-in" in s], [WIN_FAN_IN_STEP],
                         "the Windows fan-in step is not the pinned bytes")
        self.assertLess(job.index("--fan-in"), job.index("proof_bank.py --publish"))
        self.assertIn("\npermissions:\n  contents: read\n", text)

    def test_neither_producer_runs_on_main(self):
        lin = _read(LINUX_WF)
        self.assertEqual(triggers(lin), ["push", "workflow_dispatch"], "the Linux census triggers changed")
        on = lin.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertIn("'ci/proof-keys-*'", on)
        self.assertNotIn("main", on, "the Linux census runs on main")
        # exact, so `&& false` (or anything else) on a guard is red, not a silently skipped job
        self.assertEqual(job_if(lin, "bank"), "${{ %s }}" % GUARD, "the Linux bank's ref guard changed")
        win = _read(WIN_WF)
        self.assertEqual(job_if(win, "win-bank"), "${{ always() && %s }}" % GUARD, "win-bank's ref guard changed")
        self.assertEqual(job_if(win, "win-shard"), "${{ %s }}" % GUARD,
                         "a dispatch from main would start 16 billed Windows runners")
        for text, j in ((lin, "bank"), (win, "win-bank")):
            for st in _publish_steps(_job(text, j)):
                if "proof_bank.py --publish" in st or "--fan-in" in st:
                    self.assertNotRegex(st.split("run: |", 1)[0], r"(?m)^\s*(\"if\"|'if'|if)\s*:",
                                        "%s: a step-level if can skip the publish" % j)
        # billing: EVERY job on a Windows runner (any name) starts only on a ci/proof-keys-* ref
        allowed = ("${{ %s }}" % GUARD, "${{ always() && %s }}" % GUARD)
        for text in (lin, win):
            wins = windows_jobs(text)
            for j in wins:
                self.assertIn(job_if(text, j), allowed, "%s runs on Windows without the ci/proof-keys-* guard" % j)
        self.assertEqual(sorted(windows_jobs(win)), ["win-bank", "win-shard"], "BASELINE: the Windows jobs")
        for path in (LINUX_WF, WIN_WF):
            text, base = _read(path), os.path.basename(path)
            self.assertEqual(shape_errors(text), [], "%s holds a line the law cannot read" % base)
            self.assertEqual(job_names(text), JOBS[base], "%s: the job list changed - re-anchor this law" % base)

    def test_the_windows_producer_is_off_until_the_owner_turns_it_on(self):
        # owner ruling 2026-10-24: Linux bank only (Windows minutes cost 2x). Only a manual dispatch may start it.
        self.assertEqual(triggers(_read(WIN_WF)), ["workflow_dispatch"], "proof-bank-windows.yml can start itself")

    def test_the_trigger_reader_sees_every_yaml_spelling(self):
        base = "name: x\n%s\npermissions:\n  contents: read\njobs: {}\n"
        for body, want in (
                ("on:\n  workflow_dispatch:", ["workflow_dispatch"]),
                ("on:\n  push :\n    branches: [x]\n  workflow_dispatch:", ["push", "workflow_dispatch"]),
                ("on:\n  \"push\":\n  'schedule' :\n    - cron: '0 3 * * *'", ["push", "schedule"]),
                ("\"on\":\n    pull_request_target:", ["pull_request_target"]),
                ("on : [push, workflow_dispatch]", ["push", "workflow_dispatch"]),
                ("on: push", ["push"]),
                ("true:\n  push:", ["push"]),
                ("on:\n  - push\n  - schedule", ["push", "schedule"]),
                ("on:  # c\n  # push:\n  workflow_dispatch:", ["workflow_dispatch"])):
            self.assertEqual(triggers(base % body), want, body)
        with self.assertRaises(AssertionError):
            triggers(base % "on:\n  workflow_dispatch:" + "on:\n  push:\n")
        self.assertEqual(job_if("jobs:\n  a:\n    if: ${{ x }} && false\n", "a"), "${{ x }} && false")
        for body, want in (("on: [workflow_dispatch,\n  push]", ["workflow_dispatch", "push"]),
                           ("on: [workflow_dispatch, # c\n  'fork']", ["workflow_dispatch", "fork"])):
            self.assertEqual(triggers(base % body), want, body)
        with self.assertRaises(AssertionError):
            triggers(base % "on:\n  workflow_dispatch:" + '"\\u006fn": push\n')
        jt = "jobs:\n  a:\n    runs-on: ubuntu-latest\n  b:\n    runs-on: windows-2022\n  'c':\n    runs-on: ${{ matrix.os }}\n" \
             "  d:\n    runs-on:\n      - self-hosted\n"
        self.assertEqual(windows_jobs(jt), ["b", "c", "d"])
        jt2 = "jobs:\n  a:\n    runs-on: ubuntu-24.04-arm\n"
        self.assertEqual(windows_jobs(jt2), [])
        good = "name: x\non:\n  workflow_dispatch:\njobs:\n  a:\n    if: ${{ x }}\n    runs-on: ubuntu-latest\n"
        self.assertEqual(shape_errors(good), [])
        for bad in (good + "!!str on:\n  push:\n", good + "? on\n:\n  push:\n", good + '"\\u006fn": push\n',
                    good + "jobs:\n  b:\n", good.replace("  a:\n", "  ? extra\n  :\n    runs-on: windows-latest\n  a:\n"),
                    good.replace("    if: ${{ x }}\n", "    if: ${{ x }}\n      || true\n"),
                    good + '    "\\u0069f": true\n', good + "    runs-on: windows-latest\n",
                    good + '    "continue-on-\\u0065rror": true\n'):
            self.assertTrue(shape_errors(bad), bad)

    def test_the_docs_say_linux_bank_only(self):
        for doc, label in ((PB.__doc__, "proof_bank.py"), (__doc__, "this law")):
            self.assertIn("Linux bank only", doc, "%s's docstring does not state the ruling" % label)
            self.assertNotRegex(doc, r"(?i)\btwo (ci )?producers", "%s's docstring still describes a live Windows writer" % label)


def _git(cwd, *a):
    p = subprocess.run(["git"] + list(a), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


class ThePublisherDriven(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="bank.")
        self.remote = os.path.join(self.d, "remote.git")
        self.repo = os.path.join(self.d, "repo")
        _git(self.d, "init", "-q", "--bare", self.remote)
        os.makedirs(self.repo)
        _git(self.repo, "init", "-q")
        _git(self.repo, "remote", "add", "origin", self.remote)
        self.out = []

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def export(self, head=H1, n=2, dirty=False, count=None, extra=None, name="e.json", why=None):
        ent = dict(("k%d" % i, {"gate": "g", "verdict": "PROVEN", "tree": "exported:%04d" % i}) for i in range(n))
        if extra:
            ent["k0"]["target"] = extra
        if why:
            ent["k0"]["why"] = why
        body = {"format": 2, "entries": ent,
                "export": {"v": 1, "head": head, "dirty": dirty, "entries": n if count is None else count, "at": 1}}
        p = os.path.join(self.d, name)
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(body))
        return p

    def pub(self, path, head=H1, cls="linux", keep=PB.KEEP, plat=None):
        return PB.publish(path, head, cls, keep=keep, repo=self.repo, platform_class=plat or cls,
                          say=self.out.append)

    def remote_files(self):
        rc, out = _git(self.remote, "ls-tree", "--name-only", "proof-bank")
        return sorted(out.split()) if rc == 0 else None

    def test_a_bank_lands_reads_back_and_is_what_self_prove_fetches(self):
        p = self.export()
        self.assertEqual(self.pub(p), H1 + ".linux.json")
        self.assertEqual(self.remote_files(), [H1 + ".linux.json"])
        rc, body = _git(self.remote, "show", "proof-bank:%s" % SP.bank_name(H1, "linux"))
        self.assertEqual(rc, 0)
        self.assertEqual(body, _read(p), "origin serves other bytes than the export")
        # self_prove's own fetch, over this remote, at this head
        clone = os.path.join(self.d, "pc")
        _git(self.d, "clone", "-q", self.remote, clone)

        def git(*a, **k):
            if a[:2] == ("rev-parse", "HEAD"):
                return 0, H1
            rc, out = _git(clone, *a)
            return rc, out
        got, why = SP.fetch_bank(clone, git=git, cls="linux")
        self.assertIsNotNone(got, "self_prove could not fetch the published bank: %s" % why)
        self.assertEqual(json.loads(_read(got))["export"]["head"], H1)
        self.assertEqual(SP.fetch_bank(clone, git=git, cls="windows")[0], None, "BASELINE: no windows bank yet")

    def test_every_bad_export_is_exit_1_and_nothing_lands(self):
        cases = [
            ("missing", dict(path=os.path.join(self.d, "nope.json"))),
            ("empty", dict(path=self.export(n=0, name="bad1.json"))),
            ("count lies", dict(path=self.export(count=9, name="bad2.json"))),
            ("other commit", dict(path=self.export(head=H2, name="bad3.json"))),
            ("dirty", dict(path=self.export(dirty=True, name="bad4.json"))),
            ("mac path", dict(path=self.export(extra="/Users/someone/x", name="bad5.json"))),
            ("linux home", dict(path=self.export(extra="/home/box/x", name="bad6.json"))),
            ("windows path", dict(path=self.export(extra="C:\\Users\\dean\\x", name="bad7.json"))),
            ("runner path", dict(path=self.export(extra="/home/runner/work/x", name="bad8.json"))),
            ("windows runner path", dict(path=self.export(extra="D:\\a\\repo\\x", name="bad10.json"))),
            ("msys runner path", dict(path=self.export(extra="/d/a/repo/x", name="bad12.json"))),
            ("escaped windows path", dict(path=self.export(extra="C:\\\\Users\\\\x", name="bad11.json"))),
            ("other class", dict(path=self.export(name="bad9.json"), plat="windows")),
        ]
        for label, kw in cases:
            with self.assertRaises(PB.Refused, msg="%s was published" % label):
                self.pub(kw["path"], plat=kw.get("plat"))
        self.assertIsNone(self.remote_files(), "a refused bank reached proof-bank")
        bad = self.export(n=0)
        rc = PB.main(["--check", bad, "--head", H1, "--class", PB.CLASSES[0]])
        self.assertEqual(rc, 1, "a refused check exited %r, not 1" % rc)
        self.assertEqual(PB.main(["--check", os.path.join(self.d, "nope.json"), "--head", H1, "--class", "linux"]), 1)

    def test_a_why_quoting_public_source_still_publishes(self):
        # the live beacon proof's why quotes 'C:\\Users\\Dean Smith\\...' - it is committed source, not machine data
        self.pub(self.export(why="review 3 - the user-folder scrub is dropped: 'C:\\\\Users\\\\Dean Smith\\\\...' leaks"))
        self.assertEqual(self.remote_files(), [H1 + ".linux.json"])

    def test_an_unreachable_remote_is_a_refusal_not_a_pass(self):
        _git(self.repo, "remote", "set-url", "origin", os.path.join(self.d, "gone.git"))
        with self.assertRaises(PB.Refused):
            self.pub(self.export())

    def test_a_rejected_push_is_a_refusal(self):
        hook = os.path.join(self.remote, "hooks", "pre-receive")
        with io.open(hook, "w", newline="\n") as fh:
            fh.write("#!/bin/sh\nexit 1\n")
        os.chmod(hook, 0o755)
        with self.assertRaises(PB.Refused):
            self.pub(self.export())
        self.assertIsNone(self.remote_files())

    def _pc_bytes(self, crlf=True, autocrlf="true"):
        os.makedirs(os.path.join(self.repo, "tv"), exist_ok=True)
        with open(os.path.join(self.repo, "tv", "heart2.py"), "wb") as fh:
            fh.write(b"a = 1\r\nb = 2\r\n" if crlf else b"a = 1\nb = 2\n")
        _git(self.repo, "config", "core.autocrlf", autocrlf)

    def test_a_windows_bank_needs_the_pcs_bytes_on_disk(self):
        for label, kw in (("LF on disk", dict(crlf=False)), ("autocrlf input", dict(autocrlf="input")),
                          ("autocrlf false", dict(autocrlf="false"))):
            self._pc_bytes(**kw)
            with self.assertRaises(PB.Refused, msg="%s published a .windows bank" % label):
                self.pub(self.export(name="w.json"), cls="windows")
        self.assertIsNone(self.remote_files())
        self._pc_bytes()
        self.pub(self.export(name="w.json"), cls="windows")
        self.assertEqual(self.remote_files(), [H1 + ".windows.json"], "BASELINE: the PCs' bytes do publish")
        self._pc_bytes(crlf=False)
        self.pub(self.export(name="l.json"), cls="linux")  # a linux bank never asks

    def test_two_producers_both_land(self):
        self._pc_bytes()
        self.pub(self.export(name="l.json"), cls="linux")
        self.pub(self.export(name="w.json"), cls="windows")
        self.assertEqual(self.remote_files(), sorted([H1 + ".linux.json", H1 + ".windows.json"]))

    def test_old_banks_are_pruned_to_keep(self):
        for h in (H1, H2, H3):
            self.pub(self.export(head=h, name=h[:1] + ".json"), head=h, keep=2)
        self.assertEqual(self.remote_files(), sorted([H2 + ".linux.json", H3 + ".linux.json"]))
        self.assertEqual(PB.prune([H3 + ".linux.json", H3 + ".windows.json", H2 + ".linux.json", H1 + ".linux.json",
                                   "README"], 2), [H1 + ".linux.json"])

    def _spy(self, on):
        real = PB._git
        def spy(cwd, *a):
            return on(real, cwd, *a)
        PB._git = spy
        self.addCleanup(setattr, PB, "_git", real)

    def test_the_checkout_token_header_rides_into_the_scratch_push_and_is_never_printed(self):
        key = "http.https://github.invalid/.extraheader"
        _git(self.repo, "config", "--local", "--add", key, "AUTHORIZATION: basic SECRETSECRET")
        seen = []
        def on(real, cwd, *a):
            if a[:1] == ("push",):
                seen.append(real(cwd, "config", "--local", "--get-all", key)[1].strip())
            return real(cwd, *a)
        self._spy(on)
        self.pub(self.export())
        self.assertEqual(seen, ["AUTHORIZATION: basic SECRETSECRET"], "the scratch push ran without the header")
        self.assertNotIn("SECRET", "\n".join(self.out), "the token header was printed")
        self.assertEqual(self.remote_files(), [H1 + ".linux.json"])

    def test_a_failed_first_push_onto_a_new_branch_is_retried_and_lands(self):
        hook = os.path.join(self.remote, "hooks", "pre-receive")
        flag = os.path.join(self.d, "once")
        with io.open(hook, "w", newline="\n") as fh:
            fh.write('#!/bin/sh\nif [ ! -e "%s" ]; then touch "%s"; exit 1; fi\nexit 0\n' % (flag, flag))
        os.chmod(hook, 0o755)
        self.pub(self.export())
        self.assertTrue(os.path.exists(flag), "BASELINE: the first push was not rejected")
        self.assertEqual(self.remote_files(), [H1 + ".linux.json"])
        self.assertTrue(any("1/" in o for o in self.out), "BASELINE: no retry was reported")
        self.assertEqual(_git(self.remote, "rev-list", "--count", "proof-bank")[1].strip(), "1",
                         "the retried orphan carried the rejected commit along")

    def test_other_bytes_served_back_are_a_refusal(self):
        def on(real, cwd, *a):
            rc, out = real(cwd, *a)
            if a[:1] == ("show",) and rc == 0:
                return rc, out + " "
            return rc, out
        self._spy(on)
        with self.assertRaises(PB.Refused):
            self.pub(self.export())
        self.assertEqual(self.remote_files(), [H1 + ".linux.json"], "BASELINE: the push itself landed")

    def test_the_cli_refuses_a_bad_keep_and_a_short_head(self):
        self.assertEqual(PB.main(["--publish", self.export(), "--head", H1, "--class", "linux", "--keep", "0"]), 1)
        self.assertEqual(PB.main(["--check", self.export(), "--head", "abc", "--class", "linux"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
