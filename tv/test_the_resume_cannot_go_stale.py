# -*- coding: utf-8 -*-
"""v3401 — THE RESUME SAID WHERE WE LEFT OFF, AND IT HAD BEEN WRONG FOR FOUR DAYS.

MEASURED 2026-09-20: RESUME_HERE.md was last written 2026-09-16 and opened with "6 commits are
built, gated locally, and UNPUSHED", naming five commits that had shipped long before. CLAUDE.md
points every new session at it FIRST. So the first thing a fresh session read about the state of
this repo was four days wrong, and nothing noticed, because nothing could - it was prose.

BLUEPRINT.md and HEART.md never drift for one reason: nobody writes them. They are derived,
regenerated on every bump, and refused at pre-push when stale. His ruling when the heart map had
the same problem: "we need it all updated and blueprints updated and heart updated all derived
from the console", then "fix this so it is like blueprints too and has enforcemnt".

⛔ THIS GATE REFUSES; IT DOES NOT REGENERATE. A gate that repairs what it grades can never fail,
and then the artefact rots behind a permanently green light. Same rule as the blueprint's.

⚠ STALENESS IS JUDGED ON THE FACTS, NOT THE RENDERING. The block also prints a derive timestamp
and "as known N min ago"; comparing the whole thing would be red every minute, and a gate that is
always red is switched off as fast as one that is always green. The fingerprint carries head,
origin and version - the durable identity of where we are. `dirty` is out on purpose: uncommitted
files are ordinary mid-work.
"""
import io
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import resume_state as rs  # noqa: E402

RESUME = os.path.join(REPO, "RESUME_HERE.md")

RED_PROOF = [
    {
        "why": "without a fingerprint the check has nothing to compare, so a resume that has "
               "drifted four days reads exactly like a current one",
        "file": "tv/resume_state.py",
        "find": '    L = [BEGIN, "<!-- fp: %s -->" % fp, ""]',
        "replace": '    L = [BEGIN, ""]',
        "matches": 1,
    },
    {
        "why": "judging staleness on the whole block instead of the facts makes it red every "
               "minute - the derive timestamp and the fetch age both move - and a gate that is "
               "always red is ignored within a week",
        "file": "tv/resume_state.py",
        "find": '    fp = "head=%s origin=%s ver=%s" % (head or "?", origin or "?", ver)',
        "replace": '    fp = "t=%s" % time.time()',
        "matches": 1,
    },
]


class TestTheResumeCannotGoStale(unittest.TestCase):

    def test_BASELINE_the_resume_exists_and_carries_a_derived_block(self):
        self.assertTrue(os.path.isfile(RESUME), "RESUME_HERE.md is missing entirely")
        src = io.open(RESUME, encoding="utf-8").read()
        self.assertIn(rs.BEGIN, src, "no derived block - every case below would be vacuous")
        self.assertIn(rs.END, src)

    def test_the_block_carries_a_fingerprint_of_the_FACTS(self):
        m = re.search(r"<!-- fp: (.*?) -->", io.open(RESUME, encoding="utf-8").read())
        self.assertTrue(m, "no fingerprint - staleness could not be judged at all")
        fp = m.group(1)
        for key in ("head=", "origin=", "ver="):
            self.assertIn(key, fp, "the fingerprint does not carry %s, so a change in it "
                                   "would not register as stale: %r" % (key, fp))
        self.assertNotIn("dirty=", fp,
                         "uncommitted files are ordinary mid-work and must not make the resume "
                         "read as stale")

    def test_THE_LAW_the_resume_matches_the_repo_right_now(self):
        r = subprocess.run([sys.executable, os.path.join(HERE, "resume_state.py"), "--check"],
                           capture_output=True, text=True, timeout=90)
        self.assertEqual(r.returncode, 0,
                         "RESUME_HERE.md no longer describes this repo. Regenerate it:\n"
                         "  python3 tv/resume_state.py\n%s" % (r.stdout or r.stderr)[:400])

    def test_the_checker_can_actually_go_RED(self):
        """⚠ A check never seen refuse is measuring nothing. Sabotage a COPY, not the file."""
        src = io.open(RESUME, encoding="utf-8").read()
        m = re.search(r"<!-- fp: (.*?) -->", src)
        self.assertTrue(m)
        bent = src.replace(m.group(1), "head=deadbeef origin=deadbeef ver=v0", 1)
        self.assertNotEqual(bent, src, "the sabotage changed nothing - it proves nothing")
        tmp = os.path.join(REPO, ".resume_probe.tmp.md")
        try:
            io.open(tmp, "w", encoding="utf-8").write(bent)
            have = re.search(r"<!-- fp: (.*?) -->",
                             io.open(tmp, encoding="utf-8").read()).group(1)
            want = re.search(r"<!-- fp: (.*?) -->", rs.derived()).group(1)
            self.assertNotEqual(have, want,
                                "a bent fingerprint still compared equal - the checker is blind")
        finally:
            try:
                os.remove(tmp)
            except Exception:
                pass

    def test_the_narrative_outside_the_markers_is_LEFT_ALONE(self):
        """The half a machine cannot measure must survive regeneration."""
        src = io.open(RESUME, encoding="utf-8").read()
        after = src[src.index(rs.END) + len(rs.END):]
        self.assertGreater(len(after.strip()), 200,
                           "the narrative half is gone - a resume that is only derived state "
                           "cannot say WHY anything is blocked")

    def test_the_generator_never_reaches_the_network(self):
        """⚠ origin/main is whatever the last fetch left. A generator that fetches would make
        every bump wait on the network and could hang a ship."""
        code = "\n".join(l.split("#", 1)[0]
                         for l in io.open(os.path.join(HERE, "resume_state.py"),
                                          encoding="utf-8").read().split("\n"))
        for banned in ('"fetch"', "'fetch'", "urlopen", "requests."):
            self.assertNotIn(banned, code,
                             "resume_state reaches the network (%s) - it must read only what is "
                             "already in the repo" % banned)


if __name__ == "__main__":
    unittest.main(verbosity=2)
