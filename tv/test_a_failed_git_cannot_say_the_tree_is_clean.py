#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3413 — A GIT THAT COULD NOT ANSWER MUST NOT MAKE THE RESUME SAY CLEAN AND NOTHING UNPUSHED.

FOUND BY READING CI AFTER THE PUSH, which is the whole point of that discipline:
```
Routine M — swallowed-exception ratchet    FAILURE on 0520ce20
swallow ratchet — RANK 1 (a failed read handed back as DATA)
   baseline 69   now 70
   WHERE IT ROSE:  tv/resume_state.py   0 -> 1  (+1)
```
The census named the site: `resume_state.py:51`, shape `return-falsy`, *"a failed run becomes
EMPTY-STR — 'could not ask' is indistinguishable from a real measurement"*.

⚠⚠ AND IT IS WORSE THAN RANK 1 SOUNDS, BECAUSE OF WHAT READS THE RESULT. `_git` returned `""`,
and `derived()` feeds that to three renderers that each treat empty as GOOD NEWS:
    len(ahead)                          -> crashes
    "CLEAN" if not dirty                -> says CLEAN
    if ahead: ... else: -> "✅ Nothing is waiting to be pushed"
So a git that could not answer made RESUME_HERE.md — the file a resuming session reads FIRST, the
one carrying *"Nothing has shipped until origin/main equals HEAD"* — assert the opposite of the
truth. Two holes: the `except` swallowed into `""`, and `returncode` was never read, so a git
exiting non-zero with empty stdout came back down the SUCCESS path. Same shape as v3409's
`_pull_once` finding, in a different file.

⚠ ATTRIBUTION, CORRECTED BY MEASUREMENT: Routine M's first run EVER was on 0520ce20
(`502aa2b2: runs=0`, `bad246d5: runs=0`). It did not go green->red — the gate arrived. The line
itself dates to v3401. A gate's first run is not a regression. [[test-venue]] attribute-by-DELTA
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import resume_state as RS  # noqa: E402


class _R(object):
    def __init__(self, rc=0, out=""):
        self.returncode, self.stdout, self.stderr = rc, out, ""


def _with_git(fake):
    """Run the LIVE renderer with subprocess.run stubbed. -> what it prints.

    ⚠ v3474 (#164) — THE TREE STATE MOVED. RESUME_HERE.md no longer states HEAD / origin /
    unpushed / dirty (a file inside a commit cannot know them); `resume_state.py --live` asks git
    at read time. The law moves WITH the renderer — driving derived() now would check a block that
    renders no tree state at all, and every "does NOT say CLEAN" case would pass vacuously.
    """
    import contextlib
    import io as _io
    real = RS.subprocess.run
    RS.subprocess.run = fake
    buf = _io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            RS.print_live()
        return buf.getvalue()
    finally:
        RS.subprocess.run = real


class TestAFailedGitIsNotAMeasurement(unittest.TestCase):

    def test__git_returns_None_when_git_EXITS_NONZERO(self):
        """⚠ exit 128 with empty stdout is how git reports dubious ownership and a held lock."""
        real = RS.subprocess.run
        RS.subprocess.run = lambda *a, **k: _R(128, "")
        try:
            self.assertIsNone(RS._git("rev-parse", "HEAD"),
                              "a non-zero git came back down the SUCCESS path as an empty string")
        finally:
            RS.subprocess.run = real

    def test__git_returns_None_when_the_CALL_RAISES(self):
        real = RS.subprocess.run

        def _boom(*a, **k):
            raise OSError("no git here")

        RS.subprocess.run = _boom
        try:
            self.assertIsNone(RS._git("rev-parse", "HEAD"),
                              "a raised call was swallowed into '' — indistinguishable from git "
                              "running and printing nothing")
        finally:
            RS.subprocess.run = real

    def test_a_failed_git_does_NOT_render_the_tree_as_CLEAN(self):
        out = _with_git(lambda *a, **k: _R(128, ""))
        self.assertNotIn("working tree  CLEAN", out,
                         "a git that could not answer rendered the working tree as CLEAN — the "
                         "file a resuming session trusts, asserting the opposite of the truth")
        self.assertIn("UNKNOWN — git could not answer", out)

    def test_a_failed_git_does_NOT_claim_nothing_is_waiting_to_be_pushed(self):
        out = _with_git(lambda *a, **k: _R(128, ""))
        self.assertNotIn("Nothing is waiting to be pushed", out,
                         "a failed read produced a FALSE ALL-CLEAR on unpushed work")
        self.assertIn("says NOTHING about", out,
                      "the page must say the absence of a list is not an all-clear")

    def test_a_failed_git_does_NOT_report_zero_unpushed(self):
        out = _with_git(lambda *a, **k: _R(128, ""))
        self.assertNotIn("unpushed      0 commit(s)", out,
                         "a failed read was rendered as a measured zero")

    def test_BASELINE_a_WORKING_git_still_renders_the_real_numbers(self):
        """⚠ Without this, a generator hardwired to UNKNOWN would pass every case above."""
        def _fake(args, **k):
            a = list(args)
            if "status" in a:
                return _R(0, " M tv/x.py\n M tv/y.py")
            if "log" in a:
                return _R(0, "abc1234 a commit\ndef5678 another")
            return _R(0, "abc1234")
        out = _with_git(_fake)
        self.assertIn("unpushed      2 commit(s)", out, "a working git no longer renders the real count")
        self.assertIn("working tree  2 file(s) uncommitted", out)
        self.assertNotIn("UNKNOWN — git could not answer", out,
                         "a healthy read was reported as UNKNOWN — a row that always says "
                         "UNKNOWN measures nothing")

    def test_BASELINE_a_CLEAN_tree_still_reads_CLEAN(self):
        def _fake(args, **k):
            a = list(args)
            if "status" in a:
                return _R(0, "")
            if "log" in a:
                return _R(0, "")
            return _R(0, "abc1234")
        out = _with_git(_fake)
        self.assertIn("working tree  CLEAN", out,
                      "a genuinely clean tree must still read CLEAN — otherwise the fix traded "
                      "a false all-clear for a permanent false alarm")
        self.assertIn("Nothing is waiting to be pushed", out)


RED_PROOF = [
    {
        "why": "v3413 — THE EXCEPT SWALLOWED INTO ''. A failed call handed back an empty string, "
               "which renders as CLEAN and as 'nothing waiting to be pushed' on the one file a "
               "resuming session reads first.",
        "file": "resume_state.py",
        "find": "    except Exception:\n        return None\n    if r.returncode != 0:",
        "replace": "    except Exception:\n        return \"\"\n    if r.returncode != 0:",
        "matches": 1,
    },
    {
        "why": "v3413 — RETURNCODE NEVER READ. git exits 128 with EMPTY stdout on dubious "
               "ownership, a broken index or a held lock; without this check every one of those "
               "comes back down the SUCCESS path as ''.",
        "file": "resume_state.py",
        "find": "    if r.returncode != 0:\n        return None",
        "replace": "    if False:\n        return None",
        "matches": 1,
    },
    {
        "why": "v3413 — THE RENDERER READING None AS CLEAN. Restoring the old ternary makes a "
               "git that could not answer report the working tree as CLEAN, which is the false "
               "all-clear this version exists to kill.",
        "file": "resume_state.py",
        # v3474 — RE-ANCHORED: the tree state moved from derived() into print_live(). Same
        # property: a git that could not answer must never render the working tree as CLEAN.
        "find": '    print("working tree  %s" % (unk if st["dirty"] is None else\n',
        "replace": '    print("working tree  %s" % (("CLEAN" if not st["dirty"] else "x") if True else\n',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
