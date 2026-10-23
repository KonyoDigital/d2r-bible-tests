# -*- coding: utf-8 -*-
"""REG-2612 (#71) - WHEN A SANDBOX FILE VANISHES, THE SANDBOX SAYS WHAT IT SAW, AND EVERY SWEEP LEAVES A LINE.

#144 recurred on the Linux box (2026-10-23 01:11-02:21 IDT stage run, lane 4): every root .md/.html/.json and 13 tv
files went in one gate, while a gate that touches no files was running, and the sandbox it left had lost its owner
file. That box has no dirhelper, cron or tmpreaper, so REG-2438's macOS atime theory is not the whole cause. The pattern
is a whole-sandbox rmtree's, and nothing recorded who ran one.

  · DRIVEN: the stale sweep writes a journal line (sweeper pid, sandbox, owner, why) in the temp dir before it removes,
    and a run that drops its own sandbox writes one too, so the two can be told apart.
  · DRIVEN: every new sandbox writes a birth line; a vanish reports whether the owner file and the root survive, the
    birth (never an mtime any unlink moves), and every journal line naming exactly this sandbox. It never raises.
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
        self.assertIn("\tswept\tpid=%d\theart2.old0002\t" % os.getpid(), j,
                      "a sweep removed a sandbox and did not write down which process removed which sandbox")
        self.assertIn("\tstale-24h\n", j, "the journal does not say why")
        self.assertNotIn("heart2.wit0001", j, "a live sandbox was journaled as swept")

    def test_the_sweep_line_is_written_before_the_remove(self):
        old = os.path.join(self.tmp, "heart2.old0003")
        os.makedirs(old)
        then = time.time() - H.SANDBOX_STALE_S - 3600
        os.utime(old, (then, then))
        seen = []

        def _boom(path):
            seen.append(self._journal())
            raise RuntimeError("rmtree stopped here")
        with mock.patch.object(H, "_rmtree_hard", _boom):
            with self.assertRaises(RuntimeError):
                H.sweep_stale_sandboxes(tmp=self.tmp)
        self.assertTrue(seen, "PREMISE: the sweep never reached its remove")
        self.assertIn("\theart2.old0003\t", seen[0], "the remove ran before its journal line was written")

    def test_a_raw_owner_file_never_reaches_the_journal(self):
        old = os.path.join(self.tmp, "heart2.old0004")
        os.makedirs(old)
        with io.open(os.path.join(old, H._SANDBOX_OWNER), "w") as fh:
            fh.write("Ran 3 tests skipped=3")
        then = time.time() - H.SANDBOX_STALE_S - 3600
        os.utime(old, (then, then))
        H.sweep_stale_sandboxes(tmp=self.tmp)
        j = self._journal()
        self.assertIn("\theart2.old0004\towner=?\t", j, "PREMISE: no line for the swept sandbox")
        self.assertNotIn("skipped=", j, "an owner file's raw text reached the journal the gate tail is built from")

    def test_the_journal_is_private(self):
        H._sweep_journal(self.tmp, "created", self.box, "new", "1", time.time())
        if os.name != "nt":
            mode = os.stat(os.path.join(self.tmp, H._SWEEP_JOURNAL)).st_mode & 0o777
            self.assertEqual(mode & 0o077, 0, "the journal is readable by other users (mode %o)" % mode)

    def test_a_run_that_drops_its_own_sandbox_says_so_too(self):
        H._drop_sandbox(self.box)
        self.assertFalse(os.path.exists(self.box), "PREMISE: the drop did not remove the sandbox")
        j = self._journal()
        self.assertIn("\tdropped\tpid=%d\theart2.wit0001\t" % os.getpid(), j,
                      "a run's own cleanup is not told apart from a sibling's sweep")

    def test_a_tracked_sandbox_writes_its_birth(self):
        box = os.path.join(self.tmp, "heart2.new0005")
        os.makedirs(box)
        H._track_sandbox(box)
        self.addCleanup(H._SANDBOXES.discard, box)
        self.assertIn("\tcreated\tpid=%d\theart2.new0005\t" % os.getpid(), self._journal(),
                      "a new sandbox left no birth line, so its age is read off an mtime any unlink moves")

    def test_a_vanish_after_a_sweep_says_the_owner_file_went_and_names_the_sweep(self):
        with io.open(os.path.join(self.tmp, H._SWEEP_JOURNAL), "w") as fh:
            fh.write("%d\tcreated\tpid=77\theart2.wit0001\towner=77\tnew\n" % (int(time.time()) - 600))
            fh.write("1\tswept\tpid=4242\theart2.wit0001\towner=77\towner-dead\n")
        os.environ["ALSO_OWNER"] = "1"
        ok, tail = H._run_gate(self.sb, "test_zz_gone.py", timeout=60)
        self.assertIs(ok, True, tail)
        self.assertIn("owner file GONE", tail)
        self.assertIn("swept by pid 4242 (its owner pid was dead, owner 77)", tail,
                      "the vanish does not name the sweep that removed its sandbox")
        self.assertRegex(tail, r"created (59\d|60\d)s ago by pid 77", "the sandbox's age is not read from its birth line")

    def test_a_vanish_with_the_owner_gone_and_no_line_says_so(self):
        os.environ["ALSO_OWNER"] = "1"                 # the 2026-10-23 leftover: owner gone, nothing on record
        ok, tail = H._run_gate(self.sb, "test_zz_gone.py", timeout=60)
        self.assertIs(ok, True, tail)
        self.assertIn("owner file GONE", tail)
        self.assertIn("no created line", tail)
        self.assertIn("no sweep journal line names it", tail, "a remover was invented for a vanish nothing recorded")

    def test_a_vanish_with_no_remover_on_record_says_so(self):
        with io.open(os.path.join(self.tmp, H._SWEEP_JOURNAL), "w") as fh:     # a SIBLING's sweep is not this one's
            fh.write("1\tswept\tpid=4242\theart2.wit00012\towner=77\towner-dead\n")
        ok, tail = H._run_gate(self.sb, "test_zz_gone.py", timeout=60)
        self.assertIs(ok, True, tail)
        self.assertIn("owner file present", tail)
        self.assertIn("sandbox root present", tail)
        self.assertIn("no sweep journal line names it", tail, "a sibling sandbox's sweep was pinned on this one")

    def test_a_root_gone_before_the_restore_is_said_gone(self):
        seen = {}
        real_once = H._run_gate_once

        def _once(*a, **k):
            r = real_once(*a, **k)
            if not seen:
                seen["x"] = 1
                shutil.rmtree(self.box)            # the whole sandbox went while the gate ran
            return r
        with mock.patch.object(H, "_run_gate_once", _once):
            ok, tail = H._run_gate(self.sb, "test_zz_gone.py", timeout=60)
        self.assertIn("sandbox root GONE", tail, "the restore rebuilt the root before the witness looked")

    def test_an_unreadable_journal_never_skips_the_restore(self):
        with io.open(os.path.join(self.tmp, H._SWEEP_JOURNAL), "wb") as fh:
            fh.write(b"\xff\xfe\x00garbage\n")
        with mock.patch.object(H, "_journal_lines_for", mock.Mock(side_effect=MemoryError())):
            ok, tail = H._run_gate(self.sb, "test_zz_gone.py", timeout=60)
        self.assertIs(ok, True, tail)
        self.assertIn("witness unreadable (MemoryError)", tail)
        self.assertTrue(os.path.isfile(os.path.join(self.sb, "victim.py")),
                        "a witness that raised skipped the restore - the vanished file stayed gone")


RED_PROOF = [
    {"why": "REG-2612 - the sweep removes a sandbox without writing it down",
     "file": "heart2.py",
     "find": "        _sweep_journal(tmp, \"swept\", root,",
     "replace": "        (lambda *a: None)(tmp, \"swept\", root,",
     "matches": 1},
    {"why": "REG-2612 - the witness reads the owner file in the wrong place, so a swept sandbox looks owned",
     "file": "heart2.py",
     "find": "(\"present\" if os.path.isfile(os.path.join(base, _SANDBOX_OWNER)) else \"GONE\")",
     "replace": "(\"present\" if True else \"GONE\")",
     "matches": 1},
    {"why": "REG-2612 - a run's own cleanup leaves no line, so it cannot be told apart from a sibling's sweep",
     "file": "heart2.py",
     "find": "    _sweep_journal(os.path.dirname(root), \"dropped\"",
     "replace": "    (lambda *a: None)(os.path.dirname(root), \"dropped\"",
     "matches": 1},
    {"why": "REG-2612 - the vanish note drops the witness",
     "file": "heart2.py",
     "find": "    note = note[:-1] + \" - \" + _witness + \"]\"\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2612 - the journal line is matched loosely, so a sibling sandbox's sweep is pinned on this one",
     "file": "heart2.py",
     "find": "if len(f) != 6 or f[3] != name or",
     "replace": "if len(f) != 6 or",
     "matches": 1},
    {"why": "REG-2612 - review r1: the remove runs before its journal line",
     "file": "heart2.py",
     "find": "        _sweep_journal(tmp, \"swept\", root, \"owner-dead\" if age < SANDBOX_STALE_S else \"stale-24h\", owner, now)  # REG-2612\n        #           ^ written BEFORE the remove, so a half-done one shows\n        if _rmtree_hard(root):",
     "replace": "        _ok = _rmtree_hard(root)\n        _sweep_journal(tmp, \"swept\", root, \"owner-dead\" if age < SANDBOX_STALE_S else \"stale-24h\", owner, now)\n        if _ok:",
     "matches": 1},
    {"why": "REG-2612 - review r1: a raw owner file is copied into the journal",
     "file": "heart2.py",
     "find": "own if own.isdigit() else (\"?\" if own else \"-\")",
     "replace": "own or \"-\"",
     "matches": 1},
    {"why": "REG-2612 - review r1: the journal is created world-readable",
     "file": "heart2.py",
     "find": "os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)",
     "replace": "os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o666)",
     "matches": 1},
    {"why": "REG-2612 - review r1: a new sandbox writes no birth line",
     "file": "heart2.py",
     "find": "    _sweep_journal(os.path.dirname(root), \"created\", root,",
     "replace": "    (lambda *a: None)(os.path.dirname(root), \"created\", root,",
     "matches": 1},
    {"why": "REG-2612 - review r1: the witness reads after the restore, which rebuilt the root",
     "file": "heart2.py",
     "find": "    _witness = _vanish_witness(_sb_root)     # REG-2612 (#71) - read BEFORE the restore touches it; never raises\n    for n in gone:\n",
     "replace": "    for n in gone:\n        _witness = _vanish_witness(_sb_root)\n",
     "matches": 1},
    {"why": "REG-2612 - review r1: a witness that raises skips the restore",
     "file": "heart2.py",
     "find": "    except Exception as e:\n        return \"witness unreadable (%s)\" % type(e).__name__\n",
     "replace": "    except OSError as e:\n        return \"witness unreadable (%s)\" % type(e).__name__\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main()
