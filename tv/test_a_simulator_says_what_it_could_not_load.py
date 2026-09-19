# -*- coding: utf-8 -*-
"""v3353 (#107) — A NAME THE SIMULATOR COULD NOT FIND IS UNKNOWN, NEVER A HOST DEPENDENCY.

`ci_sim.py` exists to answer one question: does this test lean on something only his Mac has? It
was answering that question about names it had never loaded.

MEASURED, asking it for a class that lives in `test_an_examined_panel_is_not_an_unread_one.py`:

    AttributeError: module 'test_control' has no attribute
                    'TestAnExaminedPanelIsNotAnUnreadOne'
    🔴 1 test(s) depend on something only HIS machine has:
         TestAnExaminedPanelIsNotAnUnreadOne

**The test never ran.** unittest wraps a loader error as a `_FailedTest`, the runner counts it
among `errors`, and the tail prints every error as a host dependency. A name this tool cannot find
is UNKNOWN — turning it into a confident claim about his machine is the exact collapse the file
was written to prevent, committed by the file itself. [[unknown-stays-unknown]]

=== AND IT ONLY EVER SIMULATED ONE FILE WHILE SAYING "THE SUITE" ===
`main()` did `import test_control` and loaded names from that module alone, under a banner reading
"CI SIMULATION — the suite as a runner sees it". Every other test file was outside its reach and
always had been. Both halves are fixed here, because a tool that silently measures one file while
claiming the suite is the same over-claim wearing different clothes. [[regression-guard]] §1 — a
sample is not a verdict.

⚠ THE SEARCH SWALLOWS IMPORT FAILURES ON PURPOSE. A module that cannot import here is not the
subject of the question being asked, and letting one bad file abort the scan would turn a findable
class into an unfindable one — converting a real answer into a refusal.

⚠⚠ WHAT THIS CHANGED ABOUT A STANDING CLAIM, and it is a correction rather than a discovery: I had
recorded that #99's four seal ERRORs "are CI-ONLY, a VENUE fact" because they pass on his Mac. With
the loader fixed, the class runs 6 tests here and reports NO known host dependency — so passing
locally plus tripping no known stub does not make it venue. It makes the cause UNMEASURED, which is
a different word and the honest one.
"""
import io
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

SIM = os.path.join(HERE, "ci_sim.py")


def _run(*args):
    p = subprocess.Popen([sys.executable, SIM] + list(args),
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=HERE)
    out, _ = p.communicate()
    return p.returncode, (out or b"").decode("utf-8", "replace")


class ANameItCannotLoadIsUnknown(unittest.TestCase):

    def test_an_unfindable_name_is_refused_not_attributed(self):
        """⚠⚠ THE CASE. Before this, a typo produced a verdict about his machine."""
        code, out = _run("TestNoSuchClassAnywhereXYZ")
        self.assertEqual(
            code, 2,
            "an unloadable name did not exit 2. It must be UNKNOWN (2), never a clean pass (0) "
            "and never a host-dependency finding (1). Got %d:\n%s" % (code, out[-600:]))
        self.assertIn(
            "could not LOAD", out,
            "the output does not say it could not load the name, so a reader cannot tell a "
            "missing name from a real finding:\n%s" % out[-600:])
        self.assertNotIn(
            "depend on something only HIS machine has", out,
            "a name that was never loaded is STILL being reported as a host dependency — the "
            "whole defect. Output:\n%s" % out[-600:])

    def test_a_class_outside_test_control_is_actually_found(self):
        """The other half: the reach really did widen, not just the wording."""
        code, out = _run("TestAnExaminedPanelIsNotAnUnreadOne")
        self.assertEqual(
            code, 0,
            "a class that exists in tv/ could not be simulated (exit %d). The search is supposed "
            "to fall through from test_control to whichever test file DEFINES the name:\n%s"
            % (code, out[-600:]))
        self.assertIn(
            "test_an_examined_panel_is_not_an_unread_one", out,
            "the run does not name the module it actually loaded, so its reach is unstated")
        self.assertIn("Ran ", out, "nothing was executed, so nothing was simulated")

    def test_every_run_states_its_reach(self):
        """⚠ The banner said 'the suite' while loading one file. A tool that overstates what it
        measured is the green that lies. [[regression-guard]] §1"""
        code, out = _run("TestAnExaminedPanelIsNotAnUnreadOne")
        self.assertIn("reach:", out,
                      "the run does not state what it covered, so 'no KNOWN host dependency' "
                      "cannot be read against a population")


class TheCodeKeepsTheDistinction(unittest.TestCase):

    def test_load_failures_are_detected_before_they_are_counted(self):
        code = io.open(SIM, encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in code.split("\n"))
        self.assertIn(
            "_load_failures(suite)", code,
            "nothing inspects the suite for loader failures, so a _FailedTest flows into the "
            "runner and is counted as an error — which this tool prints as a host dependency")
        self.assertIn(
            "_FailedTest", code,
            "the detector no longer looks for unittest's loader-error wrapper, so it cannot tell "
            "a name that would not load from a test that ran and failed")

    def test_the_search_does_not_stop_at_test_control(self):
        code = io.open(SIM, encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in code.split("\n"))
        self.assertIn(
            "_module_defining(", code,
            "the loader is back to test_control only, so every other test file is unreachable "
            "while the banner still speaks about the suite")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "dropping the load check lets a name that was never found be counted as an error "
               "and printed as a dependency on his machine — the defect this law exists for",
        "file": "tv/ci_sim.py",
        "find": "    _bad_load = _load_failures(suite)",
        "replace": "    _bad_load = []",
        "matches": 1,
    },
    {
        "why": "narrowing the search back to test_control makes every class in every other test "
               "file unloadable, while the tool goes on claiming it simulated the suite",
        "file": "tv/ci_sim.py",
        "find": "            home = _module_defining(root) or test_control",
        "replace": "            home = test_control",
        "matches": 1,
    },
    {
        "why": "a run that does not state its reach lets 'no KNOWN host dependency' be read as a "
               "verdict over the whole suite when it covered one file",
        "file": "tv/ci_sim.py",
        "find": '    print("   reach: %s" % ("module %s" % home.__name__ if which else',
        "replace": '    _ = ("reach" and ("module %s" % home.__name__ if which else',
        "matches": 1,
    },
]
