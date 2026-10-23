# -*- coding: utf-8 -*-
"""REG-2612 (#71) - WHEN A SANDBOX FILE VANISHES, THE SANDBOX SAYS WHAT IT SAW, AND EVERY SWEEP LEAVES A LINE.

#144 recurred on the Linux box (2026-10-23 01:11-02:21 IDT stage run, lane 4): every root .md/.html/.json and 13 tv
files went in one gate, while a gate that touches no files was running, and the sandbox it left had lost its owner
file. That box has no dirhelper, cron or tmpreaper, so REG-2438's macOS atime theory is not the whole cause. The pattern
is a whole-sandbox rmtree's, and nothing recorded who ran one.

  · DRIVEN: the stale sweep writes a journal line (sweeper pid, sandbox, owner, why) in the temp dir before it removes,
    and a run that drops its own sandbox writes one too, so the two can be told apart.
  · DRIVEN: a vanish reports whether the owner file survives, the sandbox root's age, and any journal line naming it.
  · DRIVEN: a vanish with the owner file in place and no journal line says so, rather than guessing a remover.
RED_PROOF below. [[unknown-stays-unknown]]
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

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import heart2 as H  # noqa: E402

GATE = (
    "import os, sys\n"
    "here = os.path.dirname(os.path.abspath(__file__))\n"
    "os.remove(os.path.join(here, 'victim.py'))\n"
    "if os.environ.get('ALSO_OWNER') == '1':\n"
    "    os.remove(os.path.join(os.path.dirname(os.path.dirname(here)), '.heart2-owner'))\n"
    "print('OK')\n"
)


class AVanishedSandboxNamesItsRemover(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="h2witness_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.real = os.path.join(self.tmp, "real")
        self.box = os.path.join(self.tmp, "heart2.wit0001")
        self.sb = os.path.join(self.box, "repo", "tv")
        for d in (os.path.join(self.real, "tv"), self.sb):
            os.makedirs(d)
            with io.open(os.path.join(d, "victim.py"), "w") as fh:
                fh.write("X = 1\n")
        with io.open(os.path.join(self.sb, "test_zz_gone.py"), "w") as fh:
            fh.write(GATE)
        with io.open(os.path.join(self.box, H._SANDBOX_OWNER), "w") as fh:
            fh.write(str(os.getpid()))
        p = mock.patch.object(H, "REPO", self.real)
        p.start()
        self.addCleanup(p.stop)
        del H._VANISHED[:]
        self.addCleanup(lambda: H._VANISHED.__delitem__(slice(None)))
        self.addCleanup(os.environ.pop, "ALSO_OWNER", None)

    def _journal(self):
        try:
            with io.open(os.path.join(self.tmp, H._SWEEP_JOURNAL)) as fh:
                return fh.read()
        except OSError:
            return ""

    def test_a_sweep_writes_who_removed_which_sandbox_and_why(self):
        old = os.path.join(self.tmp, "heart2.old0002")
        os.makedirs(os.path.join(old, "repo"))
        then = time.time() - H.SANDBOX_STALE_S - 3600
        os.utime(old, (then, then))
        gone = H.sweep_stale_sandboxes(tmp=self.tmp)
        self.assertIn(old, [p for p, _w in gone], "PREMISE: the stale sandbox was not swept")
        j = self._journal()
        self.assertIn("\theart2.old0002\t", j, "a sweep removed a sandbox and wrote nothing down")
        self.assertIn("swept-by-pid=%d" % os.getpid(), j, "the journal does not name the sweeping process")
        self.assertIn("no proof run lives that long", j, "the journal does not say why")
        self.assertNotIn("heart2.wit0001", j, "a live sandbox was journaled as swept")

    def test_a_run_that_drops_its_own_sandbox_says_so_too(self):
        H._drop_sandbox(self.box)
        self.assertFalse(os.path.exists(self.box), "PREMISE: the drop did not remove the sandbox")
        j = self._journal()
        self.assertIn("\theart2.wit0001\t", j, "a run's own cleanup is not told apart from a sibling's sweep")
        self.assertIn("dropped by its own run", j)

    def test_a_vanish_after_a_sweep_says_the_owner_file_went_and_names_the_sweep(self):
        with io.open(os.path.join(self.tmp, H._SWEEP_JOURNAL), "w") as fh:
            fh.write("1\tswept-by-pid=4242\theart2.wit0001\towner=77\tits owner (pid 77) is dead\n")
        os.environ["ALSO_OWNER"] = "1"
        ok, tail = H._run_gate(self.sb, "test_zz_gone.py", timeout=60)
        self.assertIs(ok, True, tail)
        self.assertIn("owner file GONE", tail)
        self.assertIn("swept-by-pid=4242", tail, "the vanish does not name the sweep that removed its sandbox")

    def test_a_vanish_with_no_remover_on_record_says_so(self):
        with io.open(os.path.join(self.tmp, H._SWEEP_JOURNAL), "w") as fh:     # a SIBLING's sweep is not this one's
            fh.write("1\tswept-by-pid=4242\theart2.wit00012\towner=77\tits owner (pid 77) is dead\n")
        ok, tail = H._run_gate(self.sb, "test_zz_gone.py", timeout=60)
        self.assertIs(ok, True, tail)
        self.assertIn("owner file present", tail)
        self.assertIn("no sweep journal line names it", tail, "a sibling sandbox's sweep was pinned on this one")
        self.assertIn("sandbox root", tail)


RED_PROOF = [
    {"why": "REG-2612 - the sweep removes a sandbox without writing it down",
     "file": "heart2.py",
     "find": "        _sweep_journal(tmp, root, why, owner, now)",
     "replace": "        pass",
     "matches": 1},
    {"why": "REG-2612 - the witness reads the owner file in the wrong place, so a swept sandbox looks owned",
     "file": "heart2.py",
     "find": "    parts = [\"owner file %s\" % (\"present\" if os.path.isfile(os.path.join(base, _SANDBOX_OWNER)) else \"GONE\")]\n",
     "replace": "    parts = [\"owner file %s\" % (\"present\" if True else \"GONE\")]\n",
     "matches": 1},
    {"why": "REG-2612 - a run's own cleanup leaves no line, so it cannot be told apart from a sibling's sweep",
     "file": "heart2.py",
     "find": "    _sweep_journal(os.path.dirname(root), root, \"dropped by its own run\"",
     "replace": "    (lambda *a: None)(os.path.dirname(root), root, \"dropped by its own run\"",
     "matches": 1},
    {"why": "REG-2612 - the vanish note drops the witness",
     "file": "heart2.py",
     "find": "    note = note[:-1] + \" - \" + _witness + \"]\"\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2612 - the journal line is matched loosely, so a sibling sandbox's sweep is pinned on this one",
     "file": "heart2.py",
     "find": "            hits = [ln.strip() for ln in fh if (\"\\t%s\\t\" % name) in ln]\n",
     "replace": "            hits = [ln.strip() for ln in fh]\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main()
