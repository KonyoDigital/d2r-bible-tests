# -*- coding: utf-8 -*-
"""#151 - A GROK SESSION DIRECTORY NEVER OUTLIVES THE CALL THAT MINTED IT, IN EITHER LANE.

MEASURED on his Mac 2026-10-28: ~/.grok/sessions held 55 directories named for the intake lane's throwaway cwd
(tvd-intake-g5-...), every one since 10-21. REG-1687 made the G5 read lane remove its own and sweep leftovers, but
both matched "tvd-g5-" only - and "tvd-intake-g5-" does not contain it - while intake_grok_sub.mjs removed its work
dir and never the session directory the Grok CLI minted for it. On 09-01 this same folder reached 11 GB and ENOSPC.

Now the intake lane drops its own session directory (dropSession, matched by its unique basename only) and the read
lane's sweep knows both names (G5_SESSION_MARKS). His own sessions (any other cwd) and the persistent tvd-g5-home are
never matched. Everything here is a fixture sessions folder in a temp dir. RED_PROOF below.
[[the-unjoined-end]] [[copy-drift]]
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
from cb_node_harness import NODE  # noqa: E402
import g5_grok_eyes as G  # noqa: E402

MJS = os.path.join(HERE, "intake_grok_sub.mjs")
DROP_HEAD = "export function dropSession(work, home) {\n"


def _mjs():
    with open(MJS, encoding="utf-8") as fh:
        return fh.read()


def _cut_drop(s):
    assert s.count(DROP_HEAD) == 1, "dropSession is not where this law cuts it (%d)" % s.count(DROP_HEAD)
    i = s.index(DROP_HEAD)
    return s[i:s.index("\n}\n", i) + 3].replace("export function", "function", 1)


def _enc(p):
    return p.replace("/", "%2F")


class _Folder(unittest.TestCase):

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="grokhome_")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.sd = os.path.join(self.home, "sessions")
        os.makedirs(self.sd)

    def plant(self, name, age_s=0):
        p = os.path.join(self.sd, name)
        os.makedirs(os.path.join(p, "s1"))
        with open(os.path.join(p, "s1", "chat_history.jsonl"), "w") as fh:
            fh.write("{}\n")
        if age_s:
            t = time.time() - age_s
            os.utime(p, (t, t))
        return name

    def left(self):
        return sorted(os.listdir(self.sd))


class TheReadLanesSweepKnowsBothNames(_Folder):

    def test_old_leftovers_of_both_lanes_go_and_his_own_stay(self):
        old = G.G5_SESSION_STALE_S + 60
        g5 = self.plant(_enc("/private/var/folders/T/tvd-g5-AbC123"), old)
        intake = self.plant(_enc("/private/var/folders/T/tvd-intake-g5-XyZ789"), old)
        his = self.plant(_enc("/Users/konyo"), old)
        repo = self.plant(_enc("/Users/konyo/d2r_bible_tests"), old)
        homeish = self.plant(_enc("/private/var/folders/T/tvd-g5-home"), old)
        fresh = self.plant(_enc("/private/var/folders/T/tvd-intake-g5-Fresh1"), 0)
        gone = G._sweep_stale_sessions(self.sd)
        self.assertEqual(gone, 2, "the sweep removed %r, left %r" % (gone, self.left()))
        self.assertNotIn(intake, self.left(), "the intake lane's leftover was never swept (#151)")
        self.assertNotIn(g5, self.left())
        for keep in (his, repo, homeish, fresh):
            self.assertIn(keep, self.left(), "the sweep removed %s - never his, never home, never a call in flight" % keep)


@unittest.skipIf(NODE is None, "node is not on this machine - UNMEASURED here, not passing")
class TheIntakeLaneDropsItsOwnSession(_Folder):

    def drop(self, work):
        js = _cut_drop(_mjs()) + (
            "\nconst { readdirSync, existsSync, rmSync } = require('fs');\nconst { join, basename } = require('path');"
            "\nconst { homedir } = require('os');\nprocess.stdout.write(JSON.stringify(dropSession(%s, %s)));\n"
            % (json.dumps(work), json.dumps(self.home)))
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise AssertionError("dropSession would not run in node - UNKNOWN, not passing: %s" % r.stderr[-600:])
        return json.loads(r.stdout)

    def test_only_this_calls_session_goes(self):
        mine = self.plant(_enc("/private/var/folders/T/tvd-intake-g5-Q1w2E3"))
        other = self.plant(_enc("/private/var/folders/T/tvd-intake-g5-R4t5Y6"))
        his = self.plant(_enc("/Users/konyo"))
        n = self.drop("/var/folders/T/tvd-intake-g5-Q1w2E3")
        self.assertEqual(n, 1, "left: %r" % self.left())
        self.assertEqual(self.left(), sorted([other, his]), "it removed another call's session, or his")
        self.assertNotIn(mine, self.left())

    def test_a_work_dir_that_is_not_this_lanes_removes_nothing(self):
        """a cwd LONGER than the lane's prefix, so only the prefix check can refuse it (the length check alone would not)"""
        his = self.plant(_enc("/Users/konyo/d2r_bible_tests"))
        self.assertEqual(self.drop("/Users/konyo/d2r_bible_tests"), 0,
                         "a cwd that is not an intake call's matched his own session")
        self.assertEqual(self.left(), [his])

    def test_the_call_drops_it_after_its_work_dir(self):
        s = _mjs()
        self.assertEqual(s.count("  dropSession(work);\n"), 1, "the intake call never drops its session")
        self.assertGreater(s.index("  dropSession(work);\n"), s.index("if (work) rmdirSync(work, { recursive: true });"),
                           "the session is dropped before the call's own cleanup")


RED_PROOF = [
    {"why": "#151 - the read lane's sweep knows only its own name, so every intake session is left behind",
     "file": "tv/g5_grok_eyes.py",
     "find": "G5_SESSION_MARKS = (\"tvd-g5-\", \"tvd-intake-g5-\")\n",
     "replace": "G5_SESSION_MARKS = (\"tvd-g5-\",)\n",
     "matches": 1},
    {"why": "#151 - the intake lane never drops the session directory its call minted",
     "file": "tv/intake_grok_sub.mjs",
     "find": "  dropSession(work);\n",
     "replace": "",
     "matches": 1},
    {"why": "#151 - the intake lane drops every session in the folder, not its own",
     "file": "tv/intake_grok_sub.mjs",
     "find": "      if (!name.includes(mine)) continue;\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "#151 - a work dir that is not an intake call's (his home) matches his own session and removes it",
     "file": "tv/intake_grok_sub.mjs",
     "find": "    if (!mine.startsWith('tvd-intake-g5-') || ",
     "replace": "    if (",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
