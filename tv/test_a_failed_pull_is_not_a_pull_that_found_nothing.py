#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3409 — A PULL THAT FAILED IS NOT A PULL THAT FOUND NOTHING.

Every law here was named by the CROSS-FAMILY REVIEW of v3404 (grok-cli, 2026-09-22), reading the
shipped diff cold. They are recorded with their finder because a look that produced four real
defects is the argument for the seat, not a formality.

⚠⚠ THE SHAPE, AND IT IS THE WORST KIND. `_pull_once` ran `git fetch` and `git merge --ff-only`
and read NEITHER return code. Only a timeout or an OS error reached its `except`. So an offline
fetch, a credential refusal, a `FETCH_HEAD.lock` held by `fleet_origin_status` on the SAME 300 s
cadence, a diverged history or a refused fast-forward all left HEAD unmoved — and
`moved = before != after` is False for "nothing to do" and for "it did not work" ALIKE. The lane
then published `already level with origin/main`, which is the one sentence it must never say
falsely. The docstring's own `None` ("cannot ask") was unreachable code.

⚠ AND IT IS STICKY. A SIGKILLed fetch can leave `index.lock` or `FETCH_HEAD.lock` behind, so
every later attempt takes the same false-clean path — a machine drifts further behind while its
own lane reports it current, forever.

⚠ `git status` had the same hole: exit 128 with empty stdout is how git reports "detected dubious
ownership", a broken index, or a held lock, and reading only stdout turned each of those into
"nothing is modified, go ahead and pull".
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca          # noqa: E402
import console_doctor as cd       # noqa: E402


class _R(object):
    """A stand-in for a CompletedProcess, so the door can be driven without a real git."""
    def __init__(self, rc=0, out="", err=""):
        self.returncode, self.stdout, self.stderr = rc, out, err


def _drive_pull(plan):
    """Run _pull_once with git stubbed. `plan` maps the first two argv words -> _R. -> _PULL say."""
    real = ca._git_run
    seen = []

    def _fake(argv, **kw):
        key = " ".join(list(argv)[1:3])
        seen.append(key)
        return plan.get(key, _R(0, ""))

    ca._git_run = _fake
    try:
        out = ca._pull_once()
    finally:
        ca._git_run = real
    return out, dict(ca._PULL), seen


class TestAFailedPullSaysSo(unittest.TestCase):

    def test_BASELINE_a_clean_tree_with_nothing_to_do_reads_level(self):
        """Without this the refusals below prove nothing — a lane jammed shut passes them all."""
        out, pull, seen = _drive_pull({
            "status --porcelain": _R(0, ""),
            "rev-parse --short": _R(0, "abc1234"),
            "fetch origin": _R(0, ""),
            "merge --ff-only": _R(0, ""),
        })
        self.assertIs(out, False, "nothing moved, so the lane reports False (did not move)")
        self.assertIn("level", (pull.get("say") or "").lower(),
                      "a genuinely up-to-date machine must still say so: %r" % pull.get("say"))

    def test_a_FAILED_FETCH_is_not_reported_as_already_level(self):
        out, pull, seen = _drive_pull({
            "status --porcelain": _R(0, ""),
            "rev-parse --short": _R(0, "abc1234"),
            "fetch origin": _R(128, "", "fatal: unable to access origin"),
        })
        say = (pull.get("say") or "")
        self.assertIsNone(out, "a failed fetch is UNKNOWN (None), never False/True")
        self.assertNotIn("level", say.lower(),
                         "the lane claimed it was level after a fetch that FAILED — the one "
                         "sentence it must never say falsely: %r" % say)
        self.assertIn("128", say, "the refusal must carry git's exit code")

    def test_a_REFUSED_FAST_FORWARD_is_not_reported_as_already_level(self):
        out, pull, seen = _drive_pull({
            "status --porcelain": _R(0, ""),
            "rev-parse --short": _R(0, "abc1234"),
            "fetch origin": _R(0, ""),
            "merge --ff-only": _R(128, "", "fatal: Not possible to fast-forward, aborting."),
        })
        say = (pull.get("say") or "")
        self.assertIsNone(out, "a refused fast-forward is UNKNOWN, never 'already level'")
        self.assertNotIn("level", say.lower(), "diverged history read as level: %r" % say)

    def test_git_status_EXIT_128_is_not_read_as_a_clean_tree(self):
        """⚠ 'detected dubious ownership' is exit 128 with EMPTY stdout."""
        out, pull, seen = _drive_pull({
            "status --porcelain": _R(128, "", "fatal: detected dubious ownership in repository"),
        })
        say = (pull.get("say") or "")
        self.assertIsNone(out, "an unreadable tree is UNKNOWN, not clean")
        self.assertNotIn("fetch origin", " ".join(seen),
                         "the lane pulled over a tree it could not read")
        self.assertIn("128", say, "the refusal must carry git's exit code: %r" % say)


class TestTwoAgesAnswerTwoQuestions(unittest.TestCase):

    def test_the_row_does_not_date_BEHIND_from_FETCH_HEAD_alone(self):
        """⚠ `behind` reads the LOCAL ref; FETCH_HEAD is rewritten by a fetch of ANY ref."""
        src = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        i = code.find("def _check_this_machine_is_keeping_itself_current(")
        self.assertGreater(i, -1, "the row is gone")
        blk = code[i:code.find("\ndef ", i + 1)]
        self.assertIn("FETCH_HEAD", blk, "the lane-alive question lost its only evidence")
        self.assertIn("packed-refs", blk,
                      "the row no longer dates origin/main itself, so it cannot say when the ref "
                      "it measured last moved")
        self.assertIn("fetch_h", blk)
        self.assertIn("ref_h", blk)

    def test_the_row_SAYS_that_neither_age_dates_the_other(self):
        st, why = dict(cd.CHECKS)["this machine keeps itself current"]()
        self.assertIn(st, (cd.OK, cd.MISSING, cd.UNKNOWN))
        if st == cd.OK:
            self.assertIn("neither age dates the other", why,
                          "a reader is left to assume one age answers the other's question: %s"
                          % why[:200])


class TestEveryCheckDeclaresWhatItWatches(unittest.TestCase):
    """The law that would have caught THREE rows I added this session and never declared."""

    def test_no_check_is_missing_from_WATCHES(self):
        names = [n for n, _ in cd.CHECKS]
        missing = sorted(n for n in names if n not in cd.WATCHES)
        self.assertEqual(missing, [],
                         "these checks read ABSENT in the organ table — a claim nobody made, "
                         "indistinguishable from a check nobody wrote. An empty tuple is the "
                         "honest declaration, never omission: %s" % missing)
        print("CHECKS %d · WATCHES %d · undeclared 0" % (len(names), len(cd.WATCHES)))


RED_PROOF = [
    {
        "why": "v3409 — WITHOUT THE EXIT-CODE LOOP, A FAILED FETCH READS AS 'ALREADY LEVEL'. "
               "HEAD does not move when the fetch fails, and `moved` is False for 'nothing to do' "
               "and 'it did not work' alike, so the lane publishes the one sentence it must never "
               "say falsely — and a machine drifts further behind while its own lane calls it "
               "current. Named by the cross-family review of v3404.",
        "file": "control_app.py",
        "find": '            if _r.returncode != 0:\n                _set(on=True, before=before, after=None, pulled=None,',
        "replace": '            if False:\n                _set(on=True, before=before, after=None, pulled=None,',
        "matches": 1,
    },
    {
        "why": "v3409 — EXIT 128 WITH EMPTY STDOUT IS NOT A CLEAN TREE. git reports dubious "
               "ownership, a broken index and a held lock that way, and reading only stdout turns "
               "each into 'nothing is modified, go ahead and pull' — on a console that EXECS THE "
               "WORKING TREE.",
        "file": "control_app.py",
        "find": "        if _st.returncode != 0:",
        "replace": "        if False:",
        "matches": 1,
    },
    {
        "why": "v3409 — AN UNDECLARED CHECK READS ABSENT IN THE ORGAN TABLE, which is "
               "indistinguishable from a check nobody wrote. Three rows added in one session "
               "shipped without a declaration and it took a cross-family reader to notice, so the "
               "law is now executable rather than remembered.",
        "file": "console_doctor.py",
        "find": '    "no git child steals his screen": (),\n',
        "replace": "",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
