# -*- coding: utf-8 -*-
"""REG-2438 (#71 / #144) - EVERY FILE OF A SANDBOX IS FRESH TO THE TEMP CLEANER, AND A VANISHING SAYS WHEN.

#144: tracked files vanished from heart2's lane sandboxes mid-run - skills, AGENTS.md, CLAUDE.md, tv/console_safe.py - and
the laws proved there afterwards read UNPROVABLE ("No module named console_safe"). No law's cleanup was ever found to
do it. MEASURED 2026-10-22: shutil's copy2 (safe_copy's copytree) and the APFS clone (`cp -c -R`, _bring_across) both
keep the SOURCE file's access time, and macOS's dirhelper removes $TMPDIR files whose atime is over 3 days old
(CLEAN_FILES_OLDER_THAN_DAYS=3, at 03:35 and at load) - every sandbox lives there. The v3631 push proved 02:52-03:51 and
its vanish was mid-run; the self-prover's log holds 30 vanish events, two lanes at once, each listing every long-unread
root file. So make_sandbox now marks every file as read just now (mtime kept), and the #144 line carries its time.
UNVERIFIED until a 03:35 passes with a live sandbox and nothing vanishes - the time on the line is how that is read.

Driven through the REAL make_sandbox (and safe_copy, and the PROOF_NEEDS clone) over a fixture repo whose every file was
last read ten days ago, and the REAL _run_gate with a law run that loses a file:
  1. every file the sandbox holds - copied, cloned or placed - reads as accessed after the build began; its mtime is the
     source's;
  2. the #144 line names the wall-clock time of the vanishing.
RED_PROOF below.
"""
import io
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

TEN_DAYS_NS = 10 * 24 * 3600 * 10 ** 9
#: the fixture repo, repo-relative: safe_copy's tree (tv/, a root .md, a skill), a root file make_sandbox places by name
#: (bible.html), and a PROOF_NEEDS subject under tv/frames/ - a directory safe_copy never copies, so only the clone
#: brings it
FILES = {
    "tv/control_app.py": "# sandbox marker\n",
    "tv/t_needs_footage.py": "PROOF_NEEDS = ['frames/hist/needed.txt']\n",
    "tv/console_safe_fixture.py": "OK = True\n",
    "tv/frames/hist/needed.txt": "a frame the proof needs\n",
    "AGENTS.md": "# agents\n",
    ".claude/skills/fixture/SKILL.md": "# a skill\n",
    "bible.html": "<html>fixture</html>\n",
}


class ASandboxOutlivesTheTempCleaner(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="atime_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.repo = os.path.join(self.d, "repo")
        self.old = time.time_ns() - TEN_DAYS_NS
        self.mtimes = {}
        for rel, text in FILES.items():
            p = os.path.join(self.repo, *rel.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with io.open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
            os.utime(p, ns=(self.old, self.old + 10 ** 9))          # last read ten days ago, written a second later
            self.mtimes[rel] = os.stat(p).st_mtime_ns

    def test_every_file_of_the_sandbox_reads_as_accessed_now_and_keeps_its_mtime(self):
        for rel in FILES:
            self.assertLess(os.stat(os.path.join(self.repo, *rel.split("/"))).st_atime_ns, time.time_ns() - TEN_DAYS_NS // 2,
                            "PREMISE: the fixture's %s does not read ten days old" % rel)
        said = []
        start = time.time_ns() - 2 * 10 ** 9                         # a filesystem's atime may round down a second
        with mock.patch.object(H, "REPO", self.repo), \
                mock.patch.object(H, "gate_files",
                                  lambda say=None: [("t_needs_footage", os.path.join(self.repo, "tv", "t_needs_footage.py"))]):
            tv, root = H.make_sandbox(say=said.append)
        self.assertIsNotNone(root, "PREMISE: the fixture sandbox was not built: %s" % said)
        self.addCleanup(H._drop_sandbox, root)
        dest = os.path.join(root, "repo")
        for rel in FILES:
            p = os.path.join(dest, *rel.split("/"))
            self.assertTrue(os.path.isfile(p), "PREMISE: the sandbox does not hold %s: %s" % (rel, said))
            st = os.stat(p)
            self.assertGreaterEqual(st.st_atime_ns, start,
                                    "%s reads as last accessed %.1f days ago in the sandbox - the temp cleaner removes it "
                                    "past 3 days, mid-run" % (rel, (time.time_ns() - st.st_atime_ns) / 8.64e13))
            self.assertEqual(st.st_mtime_ns, self.mtimes[rel], "%s's mtime moved - only its access time may" % rel)

    def test_a_vanishing_says_when_it_was_seen(self):
        tv = os.path.join(self.d, "box", "repo", "tv")
        os.makedirs(tv)
        victim = os.path.join(tv, "gone_fixture.py")
        with io.open(victim, "w", encoding="utf-8") as fh:
            fh.write("X = 1\n")

        def once(sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
            if os.path.exists(victim):
                os.remove(victim)                                    # a law run that loses a tracked file
            return True, "Ran 1 tests | OK"
        err = io.StringIO()
        with mock.patch.object(H, "_run_gate_once", once), mock.patch.object(sys, "stderr", err):
            H._run_gate(tv, "law_fixture.py")
        line = [l for l in err.getvalue().splitlines() if "#144 a tracked file vanished" in l]
        self.assertTrue(line, "PREMISE: the vanishing was not said: %r" % err.getvalue())
        self.assertRegex(line[0], r", at \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\)$",
                         "the #144 line does not say WHEN - 03:35 is the suspect and only a time can clear it")


RED_PROOF = [
    {"why": "REG-2438 - a sandbox keeps the source's access time: macOS's temp cleaner removes its files mid-run",
     "file": "heart2.py",
     "find": "    _fresh_atimes(root, say)\n",
     "replace": "    pass\n",
     "matches": 1},
    {"why": "REG-2438 - the atime step moves the mtime too: every key memoised on (size, mtime) is read anew, laws see "
            "a fresh write",
     "file": "heart2.py",
     "find": "                    os.utime(p, ns=(now, st.st_mtime_ns), follow_symlinks=False)  # FRESH-ATIME\n",
     "replace": "                    os.utime(p, ns=(now, now), follow_symlinks=False)  # FRESH-ATIME\n",
     "matches": 1},
    {"why": "REG-2438 - the #144 line does not say when: the 03:35 temp cleaner can never be named or cleared",
     "file": "heart2.py",
     "find": "                        time.strftime(\"%Y-%m-%d %H:%M:%S\", time.localtime())))",
     "replace": "                        \"?\"))",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
