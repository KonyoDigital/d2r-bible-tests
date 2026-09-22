# -*- coding: utf-8 -*-
"""v3422 (#170) — A DIRECTORY CREATED AT IMPORT IS CREATED BY EVERY READER, FOREVER.

`EYE_CWD = tempfile.mkdtemp(...)` sat at module level, so it ran on IMPORT rather than on use.
THIRTY-ONE modules import `second_eye_run` — every gate that touches the eye, the ledger,
`corroborate`, `console_doctor`, `run_gates` — and each gate runs as its own subprocess, so ONE
full gate run left roughly thirty directories behind. **MEASURED 2026-09-23: three BARE imports,
no look asked and no eye run, minted three directories.** 115 were on his Mac from two days, 33 of
them that day.

⚠ #170 FILED THIS AS "a temp dir per LOOK". The measurement refutes its own premise: the looks
were never the cause. A handful of looks a day cannot produce 33 directories, and reading the task
title instead of measuring would have sent the fix to the wrong end of the file — a reaper for the
runner, while the import kept minting them. [[feedback-suspect-the-instrument]]

⚠ AND A REAPER WOULD HAVE BEEN THE WRONG FIX EVEN IF IT WORKED. The cheapest cleanup is not
accumulating: computing a path allocates nothing. [[process-port-discipline]] §5f says the teardown
that kills the port also removes the profile — this is that rule one step earlier, at the moment
the thing is made.
"""
import ast
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import second_eye_run as R                                            # noqa: E402

SRC = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8", errors="replace").read()


def _scratch_dirs():
    t = tempfile.gettempdir()
    try:
        return {n for n in os.listdir(t) if n.startswith("second_eye_")}
    except Exception:
        return set()


class TestAScratchDirIsNotMadeByReading(unittest.TestCase):

    # ---- the law, driven for real ------------------------------------------------------

    def test_importing_the_module_creates_NO_directory(self):
        """THE WHOLE DEFECT, driven end to end in a real subprocess.

        It has to be a subprocess: the module is already imported in this one, and a second
        `import` is a no-op that would pass no matter what the code says. Driving it for real is
        also what makes this immune to the shape of the fix — lazy, reaper, or something later,
        the law is the same: READING THIS FILE MUST NOT LEAVE ANYTHING ON HIS DISK."""
        before = _scratch_dirs()
        for _ in range(3):
            rc = subprocess.call([sys.executable, "-c",
                                  "import sys; sys.path.insert(0, %r); import second_eye_run"
                                  % HERE],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.assertEqual(rc, 0, "the module could not even be imported")
        made = _scratch_dirs() - before
        for n in made:                       # never leave our own evidence behind
            shutil.rmtree(os.path.join(tempfile.gettempdir(), n), ignore_errors=True)
        self.assertEqual(made, set(),
                         "three BARE imports — no look asked, no eye run — left %d directory(ies) "
                         "on disk: %r. 31 modules import this one, so this is ~30 per gate run"
                         % (len(made), sorted(made)))

    def test_the_module_does_not_mkdtemp_at_import_time(self):
        """The same law read structurally, so the REASON survives even if the drive above is
        ever weakened. A module-level `mkdtemp` call is the defect in one line."""
        tree = ast.parse(SRC)
        bad = []
        for node in tree.body:               # module level ONLY — inside a function is correct
            for n in ast.walk(node):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "mkdtemp"):
                    bad.append(getattr(node, "lineno", "?"))
        self.assertEqual(bad, [], "mkdtemp runs at MODULE level (line %r) — that is once per "
                                  "importer, not once per use" % (bad,))

    # ---- created at use, removed after ------------------------------------------------

    def test_ready_creates_it_and_cleanup_removes_it(self):
        made = R._eye_cwd_ready()
        self.assertTrue(os.path.isdir(made), "the eye's cwd was not created when asked for")
        self.assertTrue(R.eye_cwd_cleanup(), "cleanup reported it had nothing to remove")
        self.assertFalse(os.path.exists(made), "cleanup left the directory behind")

    def test_a_second_cleanup_is_a_no_op_not_a_crash(self):
        R._eye_cwd_ready()
        R.eye_cwd_cleanup()
        self.assertFalse(R.eye_cwd_cleanup(),
                         "a repeat cleanup claimed it removed something that was already gone")

    def test_cleanup_is_registered_with_atexit_as_well_as_called(self):
        """⚠ TWO ROPES, ONE KNOT. A `finally` never runs when the process is killed — and the eye
        is BOUNDED, so being killed is an ordinary outcome, not an exotic one."""
        self.assertIn("atexit.register(eye_cwd_cleanup)", SRC,
                      "nothing removes the directory when the call is killed rather than returned")

    def test_ask_cleans_up_on_every_exit_from_the_call(self):
        """⚠ AND atexit ALONE IS NOT ENOUGH EITHER, which is the half that is easy to miss: the
        console stays up for DAYS asking look after look, and atexit fires once, at the end."""
        fn = [n for n in ast.walk(ast.parse(SRC))
              if isinstance(n, ast.FunctionDef) and n.name == "ask"]
        self.assertTrue(fn, "ask() is gone — this gate is pointed at nothing")
        fin = [t for n in ast.walk(fn[0]) if isinstance(n, ast.Try) for t in n.finalbody]
        called = {c.func.id for t in fin for c in ast.walk(t)
                  if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
        self.assertIn("eye_cwd_cleanup", called,
                      "ask() has no `finally` that cleans up, so a look that times out or raises "
                      "leaks its directory for the life of a console he leaves open")

    # ---- what must NOT be swept ---------------------------------------------------------

    def test_a_directory_HE_supplied_is_never_removed(self):
        """⚠ THE DANGEROUS HALF OF ANY CLEANUP. `THIRD_EYE_CWD` is an operator override; rmtree'ing
        the folder he pointed us at would be a far worse bug than the leak it fixes."""
        his = tempfile.mkdtemp(prefix="his_own_eye_dir_")
        keep = os.path.join(his, "a_file_he_cares_about.txt")
        io.open(keep, "w", encoding="utf-8").write("do not delete me")
        old_cwd, old_ours = R.EYE_CWD, R._EYE_CWD_IS_OURS
        try:
            R.EYE_CWD, R._EYE_CWD_IS_OURS = his, False
            R._eye_cwd_ready()
            self.assertFalse(R.eye_cwd_cleanup(),
                             "it tried to remove a directory the operator supplied")
            self.assertTrue(os.path.isfile(keep), "HIS file was destroyed by our cleanup")
        finally:
            R.EYE_CWD, R._EYE_CWD_IS_OURS = old_cwd, old_ours
            shutil.rmtree(his, ignore_errors=True)

    # ---- v3408's law must survive this change -------------------------------------------

    def test_the_eye_still_stands_outside_the_repo(self):
        """v3408 put the eye's cwd outside the checkout because a CLI eye is an AGENT WITH TOOLS
        and Grok WAS caught writing to tv/ mid-ship. A lazy path that quietly landed inside the
        repo would undo that while every other case here still passed."""
        self.assertTrue(os.path.isabs(R.EYE_CWD), "EYE_CWD is not absolute: %r" % (R.EYE_CWD,))
        repo = os.path.dirname(HERE)
        self.assertFalse(os.path.abspath(R.EYE_CWD).startswith(os.path.abspath(repo) + os.sep),
                         "EYE_CWD fell INSIDE the repo (%r) — v3408's guard is undone" % R.EYE_CWD)

    def test_each_process_gets_its_own_path(self):
        """⚠ A FIXED NAME WOULD BE SHARED BY CONCURRENT GATE SUBPROCESSES, and one finishing would
        rmtree the directory another was still working in — trading a leak for a race."""
        self.assertIn(str(os.getpid()), os.path.basename(R.EYE_CWD),
                      "EYE_CWD is not per-process: %r" % (R.EYE_CWD,))


class TestTheRowThatWatchesTheScratch(unittest.TestCase):
    """The DOCTOR half. The cases above pin that this module makes no directory; these pin that
    something on his machine would NOTICE if any other one did."""

    def _row(self):
        import console_doctor as cd
        return dict(cd.CHECKS)["our scratch is collected"]

    def test_it_reds_on_a_real_old_directory_of_ours(self):
        import time
        fn = self._row()
        self.assertEqual(fn()[0], "ok", "the machine is already dirty; this case cannot measure")
        mine = tempfile.mkdtemp(prefix="tmp", dir=tempfile.gettempdir())
        old = time.time() - 9 * 86400
        try:
            os.utime(mine, (old, old))
            st, say = fn()
            self.assertNotEqual(st, "ok", "a 9-day-old directory of ours read as clean: %s" % say)
        finally:
            shutil.rmtree(mine, ignore_errors=True)
        self.assertEqual(fn()[0], "ok", "the row did not recover once it was collected")

    def test_a_macOS_container_is_NEVER_counted_as_our_litter(self):
        """⚠ THE DEFECT THIS ROW SHIPPED WITH FOR ABOUT AN HOUR, CAUGHT BEFORE IT WENT OUT.

        Written to count every old directory, it read `missing` with 130 survivors and the sentence
        "they are made by us" — and all 130 were macOS's: 69 `com.apple.*` plus `talagent`,
        `studentd`, `gamed`, `mobiletimerd` and twelve more, every one minted at boot 20 days ago.
        It would have been permanently red, blaming us for Apple's containers, and a row that can
        never go green is one nobody reads within a week."""
        import time
        fn = self._row()
        self.assertEqual(fn()[0], "ok", "the machine is already dirty; this case cannot measure")
        theirs = os.path.join(tempfile.gettempdir(), "com.apple.aTestContainerThatIsNotOurs")
        old = time.time() - 9 * 86400
        try:
            os.makedirs(theirs, exist_ok=True)
            os.utime(theirs, (old, old))
            st, say = fn()
            self.assertEqual(st, "ok",
                             "a macOS container was counted as OUR litter, which is how this row "
                             "would ship permanently red: %s" % say)
        finally:
            shutil.rmtree(theirs, ignore_errors=True)

    def test_matching_nothing_is_UNKNOWN_and_never_a_clean_bill(self):
        """⚠ ZERO ATTRIBUTABLE DIRECTORIES ON A MACHINE THAT RUNS GATES DAILY IS THE INSTRUMENT
        FAILING, not a clean disk — the prefix list has stopped matching what we make."""
        import console_doctor as cd
        fn = self._row()
        real = cd.tempfile.gettempdir if hasattr(cd, "tempfile") else None
        empty = tempfile.mkdtemp(prefix="no_scratch_of_ours_here_")
        import tempfile as _tf
        orig = _tf.gettempdir
        try:
            _tf.gettempdir = lambda: empty
            st, say = fn()
        finally:
            _tf.gettempdir = orig
            shutil.rmtree(empty, ignore_errors=True)
        self.assertEqual(st, cd.UNKNOWN,
                         "an empty scratch root read as %r — a clean bill from a root that "
                         "matched nothing: %s" % (st, say))


RED_PROOF = [
    {
        "why": "v3422 - THE DEFECT ITSELF, PUT BACK. mkdtemp at module level runs once per "
               "IMPORTER, and 31 modules import this file. Three bare imports must leave three "
               "directories, and the drive case must see them.",
        "file": "second_eye_run.py",
        "find": "EYE_CWD = (os.environ.get(\"THIRD_EYE_CWD\")\n           or os.path.join(tempfile.gettempdir(), \"second_eye_%d\" % os.getpid()))",
        "replace": "EYE_CWD = os.environ.get(\"THIRD_EYE_CWD\") or tempfile.mkdtemp(prefix=\"second_eye_\")",
        "matches": 1,
    },
    {
        "why": "v3422 - A CLEANUP THAT DOES NOT DISCRIMINATE. Dropping the ownership guard makes "
               "the sweep delete a directory the OPERATOR supplied via THIRD_EYE_CWD, which is a "
               "worse defect than the leak - and every other case in this file still passes.",
        "file": "second_eye_run.py",
        "find": "    if not (_EYE_CWD_IS_OURS and _EYE_CWD_MADE):\n        return False",
        "replace": "    if not _EYE_CWD_MADE:\n        return False",
        "matches": 1,
    },
    {
        "why": "v3422 - THE LONG-LIVED HALF. Removing the finally leaves atexit as the only rope, "
               "which fires when the PROCESS ends - so his console, up for days, leaks one "
               "directory per look and nothing notices until the disk does.",
        "file": "second_eye_run.py",
        "find": "        eye_cwd_cleanup()\n    raw = (out or b\"\").decode(\"utf-8\", \"replace\").strip()",
        "replace": "        pass\n    raw = (out or b\"\").decode(\"utf-8\", \"replace\").strip()",
        "matches": 1,
    },
    {
        "why": "v3422 - THE ATTRIBUTION FILTER, REMOVED. Without it the row counts macOS's own "
               "per-app containers as our litter - 130 of them on his machine, minted at boot 20 "
               "days ago - and ships PERMANENTLY RED. That is exactly the state it was in for an "
               "hour before the survivors were read.",
        "file": "console_doctor.py",
        "find": "                if not e.name.startswith(MINE):\n                    continue          # somebody else's container; not ours to report on\n",
        "replace": "                if False:\n                    continue\n",
        "matches": 1,
    },
    {
        "why": "v3422 - A ROOT THAT MATCHED NOTHING MUST NOT READ AS A CLEAN BILL. Turning the "
               "UNKNOWN into an OK makes a prefix list that has stopped matching what we make "
               "indistinguishable from a disk with no litter on it.",
        "file": "console_doctor.py",
        "find": "        return UNKNOWN, (\"no directory under the scratch root matched any prefix this repo is \"",
        "replace": "        return OK, (\"no directory under the scratch root matched any prefix this repo is \"",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
