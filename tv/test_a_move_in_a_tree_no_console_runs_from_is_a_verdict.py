#!/usr/bin/env python3
"""#94 — A LIVE-STATE MOVE IN A TREE NO CONSOLE RUNS FROM IS A VERDICT, NOT A SUSPECT.

REG-1583: the v3526 integration run in a worktree watched that worktree's live-state files, saw four of them move, and
called every one a "suspect" - because his console was up on :17772, and a console writes those files as its normal
job. But his console runs from the MAIN checkout. It cannot write a worktree's files, so the moves were the suite's own
fixture leaks, and a verdict was downgraded to a maybe.

run_gates now asks WHICH tree the console on :17772 runs from (lsof names the listener, ps its script, lsof its cwd). A
console proven to run elsewhere cannot be the writer, so a move here is a verdict. UNKNOWN keeps the old reading: a false
red on his real tree is the cry-wolf this guard was built to avoid. No real process is asked here: every lsof / ps
answer is a fixture. [[unknown-stays-unknown]] [[feedback-suspect-the-instrument]] [[source-reading-guard]]
"""
import ast
import io
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import run_gates as RG  # noqa: E402


class _R(object):
    def __init__(self, out):
        self.stdout = out


def _runner(pid="4242", cmd="/usr/bin/python3 /trees/main/tv/control_app.py --open", cwd="/trees/main"):
    def run(argv, **kw):
        if argv[:2] == ["lsof", "-nP"]:
            return _R(pid + "\n")
        if argv[0] == "ps":
            return _R(cmd + "\n")
        if argv[:2] == ["lsof", "-a"]:
            return _R("p%s\nfcwd\nn%s\n" % (pid, cwd))
        raise AssertionError("unexpected call %r" % (argv,))
    return run


class WhichTreeTheConsoleRunsFrom(unittest.TestCase):

    def test_an_absolute_script_names_its_tree(self):
        self.assertEqual(RG._console_tree(run=_runner()), os.path.realpath("/trees/main/tv"))

    def test_a_relative_script_is_read_against_the_consoles_cwd(self):
        got = RG._console_tree(run=_runner(cmd="python3 tv/control_app.py", cwd="/trees/other"))
        self.assertEqual(got, os.path.realpath("/trees/other/tv"))

    def test_an_answer_that_cannot_be_read_is_unknown(self):
        self.assertIsNone(RG._console_tree(run=_runner(pid="")), "no listener pid must be UNKNOWN, not a tree")
        self.assertIsNone(RG._console_tree(run=_runner(cmd="python3 something_else.py")))

        def boom(argv, **kw):
            raise OSError("no lsof on this machine")
        self.assertIsNone(RG._console_tree(run=boom), "a machine with no lsof must read UNKNOWN")

    def test_a_path_with_a_space_is_read_whole(self):
        # second eye on v3528: split on whitespace, this read `bar/tv/control_app.py`, joined it to the cwd and named a
        # tree the console does not run from - a false verdict where the rule says the tree is its own
        got = RG._console_tree(run=_runner(cmd="/usr/bin/python3 /trees/foo bar/tv/control_app.py --open",
                                           cwd="/elsewhere"))
        self.assertEqual(got, os.path.realpath("/trees/foo bar/tv"))

    def test_the_script_path_in_every_launch_shape(self):
        sp = RG._console_script_path
        self.assertEqual(sp("python3 tv/control_app.py --no-open"), "tv/control_app.py")
        self.assertEqual(sp("/usr/bin/python3 tv/control_app.py"), "tv/control_app.py",
                         "an interpreter named by its absolute path made a RELATIVE script read as absolute")
        self.assertEqual(sp("/Library/My Python/python3 tv/control_app.py"), "tv/control_app.py")
        self.assertEqual(sp("/usr/bin/python3 -X pycache_prefix=/tmp/x /t/foo bar/tv/control_app.py"),
                         "/t/foo bar/tv/control_app.py")
        self.assertEqual(sp("/trees/main/tv/control_app.py --open"), "/trees/main/tv/control_app.py")
        self.assertIsNone(sp("python3 something_else.py"))
        self.assertIsNone(sp(""))


class AConsoleElsewhereIsNotTheWriter(unittest.TestCase):

    def _decide(self, running, tree, here="/trees/work/tv"):
        with mock.patch.object(RG, "_console_is_running", lambda port=17772: running), \
                mock.patch.object(RG, "_console_tree", lambda port=17772, run=None: tree):
            return RG._console_writes_here(here=here)

    def test_a_console_in_another_tree_cannot_have_moved_this_one(self):
        live, why = self._decide(True, "/trees/main/tv")
        self.assertFalse(live, "a console that runs from ANOTHER tree was still counted as this tree's writer - "
                               "the suite's own leaks read as suspects (REG-1583)")
        self.assertIn("verdict", why)

    def test_a_console_in_this_tree_is_still_a_writer(self):
        self.assertTrue(self._decide(True, "/trees/work/tv")[0])

    def test_an_unknown_tree_keeps_the_cautious_reading(self):
        self.assertTrue(self._decide(True, None)[0], "UNKNOWN was read as 'another tree' - a false red waiting to "
                                                     "happen on his real tree")

    def test_no_console_is_no_writer(self):
        self.assertFalse(self._decide(False, "/trees/work/tv")[0])


class TheRunAsksTheTreeNotThePort(unittest.TestCase):

    def test_main_decides_the_writer_by_tree(self):
        tree = ast.parse(io.open(os.path.join(HERE, "run_gates.py"), encoding="utf-8").read())
        main = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "main"]
        self.assertEqual(len(main), 1)
        hits = [n for n in ast.walk(main[0]) if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Tuple) and any(getattr(e, "id", None) == "_console_live" for e in t.elts)
                        for t in n.targets)
                and isinstance(n.value, ast.Call) and getattr(n.value.func, "id", None) == "_console_writes_here"]
        self.assertEqual(len(hits), 1, "main() no longer decides whether the console writes THIS tree - a port "
                                       "answering is not the same question")


RED_PROOF = [
    {
        "why": "#94 - a console proven to run from another tree is counted as this tree's writer again",
        "file": "run_gates.py",
        "find": "    return False, (\"the console on :%d runs from another tree",
        "replace": "    return True, (\"the console on :%d runs from another tree",
        "matches": 1,
    },
    {
        "why": "#94 - main() goes back to asking only whether the port answers",
        "file": "run_gates.py",
        "find": "    _console_live, _console_why = _console_writes_here()\n",
        "replace": "    _console_live, _console_why = _console_is_running(), \"\"\n",
        "matches": 1,
    },
    {
        "why": "second eye on v3528 - the console's command line is split on whitespace again: a path with a space names "
               "another tree",
        "file": "run_gates.py",
        "find": "    j = cmd.rfind(\" /\", 0, i)\n",
        "replace": "    j = -1\n",
        "matches": 1,
    },
    {
        "why": "second eye on v3528 - an interpreter named by its absolute path makes a relative script read as absolute",
        "file": "run_gates.py",
        "find": "    if cmd.startswith(\"/\") and (\" \" not in cmd[:end] or os.path.isfile(cmd[:end])):\n",
        "replace": "    if cmd.startswith(\"/\"):\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
