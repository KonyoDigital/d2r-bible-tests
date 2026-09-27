# -*- coding: utf-8 -*-
"""2026-09-27 — A BATCH BUILT ON AN INTEGRATION BRANCH SHIPPED CODE NO EYE COULD BE SHOWN.

v3515-v3517 were built in worktrees, merged, then stamped as three bump-only commits. The runner looks at the
ONE commit a version is bound to, so v3517's look was 2,692 chars of version strings and the eye answered
cannot-tell - correctly - and re-asking could only answer the same. The v3518 push was then refused at the
gate for a look no re-ask could ever supply.

`second_eye_run.py vNNNN --base REV` widens the look to every change from REV to the bound commit, the prompt
says the diff spans N commits, and the row says what it covered. Measured on v3517: 2,692 -> 460,877 raw diff
chars (shared into the 26,000 cap across the changed files), and the eye came back with 6 findings, one of them
a real regression (a key stack locked no longer; reproduced and fixed in v3519).

DRIVEN on a throwaway git repo (never this one - CI checks out one commit deep): feature, then a bump-only stamp.
RED_PROOF below.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import second_eye_run as SER  # noqa: E402


def _git(repo, *args):
    return subprocess.check_output(["git"] + list(args), cwd=repo,
                                   env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                                            GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")).decode().strip()


class ALookCanCoverABatch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.repo = tempfile.mkdtemp(prefix="eye_batch_")
        r = cls.repo
        _git(r, "init", "-q")
        os.makedirs(os.path.join(r, "tv"))
        with open(os.path.join(r, "tv", "feature.py"), "w") as fh:
            fh.write("def base():\n    return 1\n")
        with open(os.path.join(r, "tv", "stamp.py"), "w") as fh:
            fh.write('VERSION = "v1"\n')
        _git(r, "add", "-A")
        _git(r, "commit", "-q", "-m", "v1: base")
        cls.base = _git(r, "rev-parse", "HEAD")
        with open(os.path.join(r, "tv", "feature.py"), "a") as fh:
            fh.write("\n\ndef the_real_change(stack):\n    return stack.strip().lower() == 'key'\n")
        _git(r, "commit", "-q", "-am", "feat: the real change")
        with open(os.path.join(r, "tv", "stamp.py"), "w") as fh:
            fh.write('VERSION = "v2"\n')
        _git(r, "commit", "-q", "-am", "v2: stamp")
        cls.bump = _git(r, "rev-parse", "HEAD")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.repo, ignore_errors=True)

    def setUp(self):
        self._saved = (SER.REPO, SER.REVIEW_BASE)
        SER.REPO = self.repo

    def tearDown(self):
        SER.REPO, SER.REVIEW_BASE = self._saved

    def test_premise_the_bound_commit_alone_carries_only_the_stamp(self):
        SER.REVIEW_BASE = None
        prompt = SER.payload_for(self.bump)[0]
        self.assertIn("stamp.py", prompt)
        self.assertNotIn("the_real_change", prompt, "premise: the bump commit already carried the feature")

    def test_a_base_widens_the_look_to_the_batch_and_says_so(self):
        SER.REVIEW_BASE = self.base
        prompt, dropped = SER.payload_for(self.bump)[:2]
        self.assertIn("the_real_change", prompt, "the widened look still shows only the bound commit")
        self.assertIn("THIS DIFF SPANS 2 COMMITS", prompt, "the eye is not told the diff spans the batch")
        self.assertIn("covers %s..%s (2 commits)" % (self.base[:8], self.bump[:8]), dropped,
                      "the row does not say what the look covered")

    def test_every_changed_file_of_the_batch_is_on_the_roster(self):
        SER.REVIEW_BASE = self.base
        absent, why = SER.absent_from(self.bump, "")
        self.assertEqual(sorted(absent), ["tv/feature.py", "tv/stamp.py"],
                         "the missing-file roster still lists only the bound commit's files: %r %s" % (absent, why))

    def test_a_base_that_is_not_an_ancestor_is_never_asked(self):
        """DRIVEN through run_one: v9001 is bound to the FIRST commit and the base is the LAST, so the range is
        empty and "covers base..sha" would be a false claim. It must refuse before building anything."""
        with open(os.path.join(self.repo, "TASKS.md"), "w") as fh:
            fh.write("| **v9001** | `%s` | v9001 - base |\n| **v9002** | `%s` | v9002 - stamp |\n"
                     % (self.base[:8], self.bump[:8]))
        try:
            SER.REVIEW_BASE = self.bump
            self.assertFalse(SER.run_one("v9001", dry=True), "a base that is not an ancestor was asked anyway")
            SER.REVIEW_BASE = self.base
            self.assertTrue(SER.run_one("v9002", dry=True), "premise: a real ancestor base is asked")
        finally:
            os.remove(os.path.join(self.repo, "TASKS.md"))


RED_PROOF = [
    {
        "why": "2026-09-27 - --base is ignored: a batch shipped as bump-only commits can never be shown to the eye",
        "file": "second_eye_run.py",
        "find": "    if REVIEW_BASE:\n        return [\"git\", \"diff\"]",
        "replace": "    if False:\n        return [\"git\", \"diff\"]",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - a base that is not an ancestor is asked anyway: the row claims a range that is empty",
        "file": "second_eye_run.py",
        "find": "        if _anc is None:\n            print(\"  %s: --base %s is not an ancestor",
        "replace": "        if False:\n            print(\"  %s: --base %s is not an ancestor",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the widened look does not tell the eye it spans several commits, nor the row what it covered",
        "file": "second_eye_run.py",
        "find": "    if REVIEW_BASE:\n        _span, _ = _sh(",
        "replace": "    if False:\n        _span, _ = _sh(",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
