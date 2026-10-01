# -*- coding: utf-8 -*-
"""EVERY RUNTIME DECISION FILE IS IGNORED BY GIT — the name is read out of the code, not listed by hand.

`control_app._decision_path(name)` mints a per-machine DECISION record (his answers, the eagle's last look, the
auto-relaunch switch). This repo is PUBLIC. On 2026-09-25 his first answer to a console question sat in an untracked
`tv/his_answers.json` one `git add -A` away from being published: #223 added the store and no ignore line. .gitignore
records the same slip three times before (v2413, v2428, the auto_relaunch sweep), each fixed by listing an instance.

  · DRIVEN: every `_decision_path("<name>")` literal in control_app.py, primary AND scratch form, is asked of
    `git check-ignore` - the real matcher, not a re-implementation of it.
  · PREMISE: the code still names decision files (a zero here would be a law that checks nothing).
RED_PROOF below.
"""
import os
import sys
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
ROOT = os.path.dirname(HERE)
GIT = shutil.which("git")


def _names():
    with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
        src = fh.read()
    return sorted(set(re.findall(r'_decision_path\(\s*"([^"]+)"\s*\)', src)))


#: #148 — tracked ON PURPOSE (.gitignore says why): a single kept evidence record, not per-machine state
TRACKED_ON_PURPOSE = {".status_worst.json": "the 612,893 ms request that answered #28 - kept evidence, a ruling"}


def _state_root_names():
    """#148 — every file control_app mints as os.path.join(_fixture_root_for_state(), "<name>"). The decision-path
    reader above could not see these, and shadow_seals.jsonl, .view_request.json and runaway_dumps.txt were not ignored."""
    with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
        src = fh.read()
    return sorted(set(re.findall(r'os\.path\.join\(\s*_fixture_root_for_state\(\)\s*,\s*"([^"]+)"\s*\)', src)))


def _ignored(rels):
    """-> the subset of rels git's real matcher would NOT ignore, asked of a throwaway repo seeded with the tree's own
    .gitignore files (a proof sandbox is not a git work tree)."""
    d = tempfile.mkdtemp(prefix="decision-ignore-")
    try:
        subprocess.run([GIT, "init", "-q", d], check=True)
        os.makedirs(os.path.join(d, "tv"))
        for rel in (".gitignore", os.path.join("tv", ".gitignore")):
            if os.path.isfile(os.path.join(ROOT, rel)):
                shutil.copyfile(os.path.join(ROOT, rel), os.path.join(d, rel))
        return [rel for rel in rels
                if subprocess.run([GIT, "check-ignore", "-q", "--no-index", rel], cwd=d).returncode != 0]
    finally:
        shutil.rmtree(d, True)


@unittest.skipIf(GIT is None, "git is absent - this law is UNMEASURED, not passing")
class EveryDecisionFileIsIgnored(unittest.TestCase):

    def test_the_code_still_names_decision_files(self):
        self.assertGreaterEqual(len(_names()), 3, "fewer decision files than exist today - the reader broke")

    def test_each_one_is_ignored_in_both_forms(self):
        # ⚠ A THROWAWAY REPO SEEDED WITH THE TREE'S OWN .gitignore FILES, so the answer comes from git's
        # real matcher and does not depend on this copy being a git work tree (a proof sandbox is not).
        d = tempfile.mkdtemp(prefix="decision-ignore-")
        self.addCleanup(shutil.rmtree, d, True)
        subprocess.run([GIT, "init", "-q", d], check=True)
        os.makedirs(os.path.join(d, "tv"))
        for rel in (".gitignore", os.path.join("tv", ".gitignore")):
            if os.path.isfile(os.path.join(ROOT, rel)):
                shutil.copyfile(os.path.join(ROOT, rel), os.path.join(d, rel))
        missing = []
        for n in _names():
            stem, ext = os.path.splitext(n)
            for rel in ("tv/" + n, "tv/%s.scratch-17999%s" % (stem, ext)):
                r = subprocess.run([GIT, "check-ignore", "-q", "--no-index", rel], cwd=d)
                if r.returncode != 0:
                    missing.append(rel)
        self.assertEqual(missing, [], "runtime decision files git would publish: %s" % missing)

    def test_the_code_still_mints_files_at_the_state_root(self):
        self.assertGreaterEqual(len(_state_root_names()), 10, "the state-root reader found almost nothing - it broke")
        self.assertIn("shadow_seals.jsonl", _state_root_names())

    def test_every_state_root_file_is_ignored_or_kept_on_purpose(self):
        rels = ["tv/" + n for n in _state_root_names() if n not in TRACKED_ON_PURPOSE]
        rels += ["tv/shadow_seals.jsonl.1"]   # its rollover, minted by os.replace(path, path + ".1")
        self.assertEqual(_ignored(rels), [], "runtime files the console mints that git would publish")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#148 - the shadow door's open/close record is trackable again - one `git add -A` publishes his hours",
        "file": "../.gitignore",
        "find": "\ntv/shadow_seals.jsonl\n",
        "replace": "\n",
        "matches": 1,
    },
    {
        "why": "his answers store is trackable again - one `git add -A` publishes his rulings to a public repo",
        "file": "../.gitignore",
        "find": "\ntv/his_answers.json\n",
        "replace": "\n",
        "matches": 1,
    },
]
