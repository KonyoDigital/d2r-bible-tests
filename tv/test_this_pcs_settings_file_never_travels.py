# -*- coding: utf-8 -*-
"""REG-2382 / REG-2385 — THIS PC'S SETTINGS FILE, AND THE LEDGER'S TEMP FILES, ARE NEVER TRACKED.

tv/pc_settings.json holds the intake reader's caps for ONE machine (tv/pc_settings.mjs reads it; the law of that rule is
test_the_reader_cap_comes_from_this_pcs_settings). Tracked, one `git add -A` would publish this PC's limits to a public
repo and ship them to every other PC. The ledger's atomic-write partners (tv_diablo's <ledger>.tmp, the intake runner's
<ledger>.<pid>.tmp) are minted and renamed away under a running console, and a tracked one is a dirty tree mid-push.

Asked of git's own matcher in a throwaway repo seeded with the tree's .gitignore - never his repo.

A law of its own, and node-free on purpose: in the reader-cap law these two cases were the only ones that ran on a PC
without node, so there every node-only proof stayed green "with 2 laws run" and was filed BLIND, and one BLIND shuts
every lock on a PC. Apart, that law skips whole where node is absent and this one runs wherever git does.
RED_PROOF below.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

GIT = shutil.which("git")
#: the one file this law's verdict reads - part of its proof key
PROOF_NEEDS = ["../.gitignore"]


@unittest.skipIf(GIT is None, "git is absent - this law is UNMEASURED, not passing")
class TheSettingsFileNeverTravels(unittest.TestCase):

    def _unignored(self, rels):
        """The paths git would track, asked of its own matcher in a throwaway repo seeded with the tree's .gitignore.
        GIT_* is dropped for these calls only: inside a push hook GIT_DIR points at the real repo and would outrank
        cwd (a leaked GIT_DIR once flipped his live repo to core.bare=true)."""
        d = tempfile.mkdtemp(prefix="pc-settings-ignore-")
        self.addCleanup(shutil.rmtree, d, True)
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        subprocess.run([GIT, "init", "-q", d], check=True, env=env)
        shutil.copyfile(os.path.join(ROOT, ".gitignore"), os.path.join(d, ".gitignore"))
        os.makedirs(os.path.join(d, "tv"))
        return [r for r in rels
                if subprocess.run([GIT, "check-ignore", "-q", "--no-index", r], cwd=d, env=env).returncode != 0]

    def test_tv_pc_settings_json_is_ignored_by_git(self):
        self.assertEqual(self._unignored(["tv/pc_settings.json"]), [],
                         "tv/pc_settings.json is trackable - one `git add -A` publishes this PC's settings to a "
                         "public repo and ships them to every other PC")

    def test_the_ledgers_temp_files_are_ignored_by_git(self):
        """REG-2385 - both writers mint a temp file beside the ledger and rename it away under a running console."""
        self.assertEqual(self._unignored(["tv/.subscription_budget.json.tmp", "tv/.subscription_budget.json.4242.tmp"]),
                         [], "a ledger temp file is trackable")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2382 - this PC's settings file is trackable: one `git add -A` publishes it and ships it to every PC",
        "file": "../.gitignore",
        "find": "\ntv/pc_settings.json\n",
        "replace": "\n",
        "matches": 1,
    },
    {
        "why": "REG-2385 - the ledger's temp files are trackable under a running console",
        "file": "../.gitignore",
        "find": "\ntv/.subscription_budget.json.*\n",
        "replace": "\n",
        "matches": 1,
    },
]
