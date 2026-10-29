# -*- coding: utf-8 -*-
"""REG-3040 - THE PUSH HOOK STAYS EXECUTABLE, OR THE WHOLE GATE SWITCHES ITSELF OFF WITHOUT A WORD.

core.hooksPath=hooks, and git runs a hook only when its file is executable: a hooks/pre-push stored as 100644 is skipped
with a one-line hint, so every local gate - the render gate, the red-proofs, the second-eye check - stops running while
every push still "succeeds". MEASURED 2026-10-29: #161's REG-2963 commit (claude/agent-161, 38399892d) changed
hooks/pre-push 100755 -> 100644 alongside its 25-line edit; cherry-picked for v3838 it would have shipped a main whose
hook never runs. Caught by reading the cherry-pick's own summary ("mode change 100755 => 100644"). The disabled hook
cannot catch itself, so this law runs where the hook does not: CI's gate set reads the git index.

The red case is built in (a file mode cannot be sabotaged by a text find/replace): the checker is proven to refuse a
100644 entry and a missing one before it is trusted on the real index.
"""
import os
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RUN_BY_GIT = ("hooks/pre-push", "hooks/install")


def _mode_ok(line):
    """one `git ls-files -s` line -> True only for an executable regular file (100755)"""
    return bool(line) and line.split()[0] == "100755"


def _index(path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}   # a hook's GIT_DIR must not leak in
    r = subprocess.run(["git", "ls-files", "-s", "--", path], cwd=ROOT, capture_output=True, text=True, env=env, timeout=60)
    if r.returncode != 0:
        raise AssertionError("PREMISE: git ls-files failed here (%s) - the index was not read" % r.stderr.strip())
    return r.stdout.strip()


class ThePushHookStaysExecutable(unittest.TestCase):

    def test_the_checker_refuses_a_hook_that_is_not_executable(self):
        self.assertFalse(_mode_ok("100644 3bb317e7c0cc04fc4f38ad78c8a11b241b783ce1 0\thooks/pre-push"))
        self.assertFalse(_mode_ok(""), "a hook missing from the index read as executable")
        self.assertTrue(_mode_ok("100755 3bb317e7c0cc04fc4f38ad78c8a11b241b783ce1 0\thooks/pre-push"))

    def test_every_hook_git_runs_is_executable_in_the_index(self):
        for p in RUN_BY_GIT:
            line = _index(p)
            self.assertTrue(line, "PREMISE: %s is not in the git index at all" % p)
            self.assertTrue(_mode_ok(line), "%s is stored %s - git will SKIP it and every local gate goes silent" % (p, line.split()[0]))

    def test_the_installer_puts_the_bit_back_on_every_clone(self):
        """hooks/install is what a fresh clone runs; it must re-assert the bit on the hook it enables, so a checkout that
        lost it (a filesystem, an archive, a copy) is repaired by the one documented step."""
        src = open(os.path.join(ROOT, "hooks", "install"), encoding="utf-8").read()
        line = [l for l in src.splitlines() if l.strip().startswith("chmod +x")]
        self.assertTrue(line, "hooks/install sets no executable bit at all")
        self.assertIn("hooks/pre-push", line[0].split(), "hooks/install no longer makes hooks/pre-push executable: %r" % line[0])


# The index half's red case is built in (test_the_checker_refuses_a_hook_that_is_not_executable): a file mode is not text a
# proof can edit. MEASURED RED on the real index too: `git update-index --chmod=-x hooks/pre-push` -> the index case FAILED.
RED_PROOF = [
    {"why": "REG-3040 - hooks/install stops making the push hook executable, so a clone that lost the bit keeps a silent gate",
     "file": "hooks/install",
     "find": "chmod +x hooks/pre-push hooks/install deploy.sh",
     "replace": "chmod +x hooks/install deploy.sh",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
