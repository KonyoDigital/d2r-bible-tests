# -*- coding: utf-8 -*-
"""v3848 SPEED - THE NIGHTLY FULL RUN AT 04:00 IDT SKIPS (AND SAYS SO) WHEN THE MACHINE IS BUSY.

Every gate runs once a night on origin/main so a push only needs the fast set. It must never sit beside a prove,
a census or a push hook (one heavy job, one Chrome), and a skip exits 75 with a logged line so a skipped night is
never read as a green one. Driven with a stub `pgrep` on PATH; nothing real is fetched or run.
"""
import os
import plistlib
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "nightly_full_gates.sh")
PLIST = os.path.join(HERE, "launchd", "com.konyo.tv-nightly-gates.plist")


class TheNightlySkipsWhenTheMachineIsBusy(unittest.TestCase):
    def _run_with_busy(self, pattern):
        d = tempfile.mkdtemp(prefix="tvd-nightly-")
        self.addCleanup(shutil.rmtree, d, True)
        bindir = os.path.join(d, "bin")
        os.mkdir(bindir)
        with open(os.path.join(bindir, "pgrep"), "w") as f:
            f.write('#!/bin/bash\ncase "$*" in *%s*) exit 0;; esac\nexit 1\n' % pattern)
        os.chmod(os.path.join(bindir, "pgrep"), 0o755)
        env = dict(os.environ, PATH=bindir + os.pathsep + os.environ.get("PATH", ""),
                   TV_NIGHTLY_LOGS=os.path.join(d, "logs"), TV_NIGHTLY_TREE=os.path.join(d, "tree"))
        p = subprocess.run(["/bin/bash", SCRIPT], env=env, capture_output=True, text=True, timeout=60)
        with open(os.path.join(d, "logs", "verdicts.log")) as f:
            return p.returncode, f.read()

    def test_a_prove_or_census_running_skips_the_night(self):
        rc, log = self._run_with_busy("heart2")
        self.assertEqual(rc, 75, log)
        self.assertIn("SKIPPED - busy", log)

    def test_a_push_hook_running_skips_the_night(self):
        rc, log = self._run_with_busy("pre-push")
        self.assertEqual(rc, 75, log)
        self.assertIn("SKIPPED - busy", log)

    def test_it_is_scheduled_at_four(self):
        with open(PLIST, "rb") as f:
            when = plistlib.load(f)["StartCalendarInterval"]
        self.assertEqual((when["Hour"], when["Minute"]), (4, 0), "the nightly runs at 04:00 IDT")

    def test_it_keeps_fifteen_gb_free(self):
        src = open(SCRIPT, encoding="utf-8").read()
        self.assertIn('-lt 15 ]', src, "the nightly no longer refuses below 15 GB free")


RED_PROOF = [
    {"why": "v3848 - the nightly runs beside a prove/census",
     "file": "nightly_full_gates.sh",
     "find": 'for _busy in "tv/run_gates.py" "tv/heart2.py" "hooks/pre-push"; do\n',
     "replace": 'for _busy in "tv/run_gates.py" "hooks/pre-push"; do\n',
     "matches": 1},
    {"why": "v3848 - the nightly runs beside a push hook",
     "file": "nightly_full_gates.sh",
     "find": 'for _busy in "tv/run_gates.py" "tv/heart2.py" "hooks/pre-push"; do\n',
     "replace": 'for _busy in "tv/run_gates.py" "tv/heart2.py"; do\n',
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
