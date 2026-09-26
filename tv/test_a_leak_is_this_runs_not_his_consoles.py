# -*- coding: utf-8 -*-
"""#31 — THE GATE SET BLAMED HIS CONSOLE'S OWN OCR WORKER FOR A LEAK.

run_gates.py ends every run with an orphan check: any process that did NOT exist before the run, exists after it,
and names THIS TREE on its command line is printed as "THIS RUN LEFT N PROCESS(ES) RUNNING". MEASURED 2026-09-26 on
the v3514 gate run: the one process it named was his :17772 console's OCR worker (its parent was the console, which
had been running for hours before the run started). The console forks that worker whenever it reads a frame, so it
is new whenever a read happens mid-run, and it runs a script from this tree. The check was right about both of its
halves and wrong about whose process it was - and its own advice ("kill by PID") would have killed his console's work.

A leak of THIS run can only descend from this run. run_gates waits for every gate, so whatever a gate left behind is
re-parented to launchd (ppid 1) the moment the gate exits, or still hangs under run_gates itself. So the parent chain
decides, not the command line alone:
  · the chain reaches run_gates (or its `ps`) or ppid 1 first          -> OURS, a leak, counted
  · the chain reaches a process that was ALREADY running before the run -> THEIRS, named with its owner, never counted
  · a new parent on the way (a leak's own child)                        -> keep climbing; it lands on one of the two

DRIVEN: `leaked_by_this_run(before, after, me, here)` - the function the check calls - is fed process tables built
the way `conftest._live_processes()` builds them, no live `ps`. RED_PROOF below.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable       # his Windows console is cp1255: this file prints "-" and "·"
    _enable()
except Exception:
    pass

import run_gates as RG                              # noqa: E402

TREE = "/x/d2r_bible_tests/tv"
ME = 4000                                           # run_gates
PS = 4001                                           # the `ps` it ran at the end


def tables():
    """before / after, the shapes _live_processes() returns: {pid: (ppid, command)}."""
    before = {
        1: (0, "/sbin/launchd"),
        100: (1, "python3 %s/control_app.py --no-open" % TREE),        # his console, running before the run
        ME: (90, "python3 %s/run_gates.py" % TREE),
        300: (1, "/usr/sbin/coreaudiod"),
    }
    after = dict(before)
    after.update({
        PS: (ME, "ps -eo pid,ppid,command"),
        500: (100, "python3 %s/ocr_worker.py --frame 12" % TREE),       # HIS console's worker, started mid-run
        501: (500, "python3 %s/ocr_worker.py --child" % TREE),          # ...and ITS child: still his
        600: (1, "python3 %s/tv_diablo.py --stub" % TREE),              # a gate's leak, re-parented to launchd
        601: (600, "python3 %s/tv_diablo.py --reader" % TREE),          # the leak's own child: ours too
        700: (ME, "python3 %s/test_x.py" % TREE),                       # still hanging under run_gates: ours
        800: (1, "python3 /elsewhere/other_tool.py"),                   # new, but not this tree: ignored
        900: (300, "python3 %s/whatever.py" % TREE),                    # names the tree, spawned by a prior daemon
    })
    return before, after


class ALeakIsThisRunsNotHisConsoles(unittest.TestCase):

    def setUp(self):
        self.before, self.after = tables()
        self.leaked, self.theirs = RG.leaked_by_this_run(self.before, self.after, {ME, PS}, TREE)

    def test_his_consoles_worker_is_named_as_his_and_not_counted(self):
        self.assertNotIn(500, self.leaked, "his console's OCR worker was blamed on the gate run (#31)")
        self.assertIn((500, 100), self.theirs, "his console's OCR worker was not named with its owner, pid 100")

    def test_a_worker_of_his_workers_is_his_too(self):
        self.assertNotIn(501, self.leaked)
        self.assertIn((501, 100), self.theirs, "the chain stopped at a NEW parent instead of climbing to its owner")

    def test_a_real_leak_is_still_counted(self):
        self.assertIn(600, self.leaked, "a gate's leak re-parented to launchd was NOT counted - the check went blind")
        self.assertIn(601, self.leaked, "a leak's own child was not counted")
        self.assertIn(700, self.leaked, "a process still hanging under run_gates was not counted")

    def test_only_this_tree_and_only_new_processes(self):
        self.assertNotIn(800, self.leaked + [p for p, _ in self.theirs], "a process outside this tree was judged")
        for pid in self.before:
            self.assertNotIn(pid, self.leaked, "a process that predates the run was counted as its leak")
        self.assertNotIn(PS, self.leaked, "the check's own `ps` was counted")

    def test_exactly_these(self):
        self.assertEqual(sorted(self.leaked), [600, 601, 700])
        self.assertEqual(sorted(self.theirs), [(500, 100), (501, 100), (900, 300)])

    def test_the_check_calls_this_function(self):
        with open(os.path.join(HERE, "run_gates.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count("= leaked_by_this_run("), 1,
                         "run() no longer asks leaked_by_this_run - the law would be testing a function nobody calls")


RED_PROOF = [
    {
        "why": "#31 - the chain is not consulted: every new tree process is a leak again, his console's worker included",
        "file": "run_gates.py",
        "find": "            if pp in before:\n                owner = pp ",
        "replace": "            if pp in before and False:\n                owner = pp ",
        "matches": 1,
    },
    {
        "why": "#31 - a new parent ends the walk, so a worker of his worker is blamed on the run",
        "file": "run_gates.py",
        "find": "            cur = pp                                    # a NEW parent",
        "replace": "            break                                       # a NEW parent",
        "matches": 1,
    },
    {
        "why": "#31 - launchd reads as a prior owner, so every real leak is excused as 'theirs'",
        "file": "run_gates.py",
        "find": "            if pp in me or pp <= 1:\n",
        "replace": "            if pp in me:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
