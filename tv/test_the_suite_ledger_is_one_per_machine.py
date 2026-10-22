# -*- coding: utf-8 -*-
"""REG-2445 (#164/#178 class) - THE GATE LEDGER IS ONE PER MACHINE, AND A PASS CARRIES ONLY WHERE IT WAS TRUE.

Measured at 7285e7efc: gate_ledger.ledger_path() was HERE/.gate_ledger.json and its input map sat beside it, so every
fresh push worktree started with no carried suite PASS (test_agent ~0.6 min, sharded test_control ~2.1-2.5 min per
attempt) and lost what it proved when it was removed; his main checkout held no ledger at all. The ledger and its map
now live in git's COMMON dir, found by reading .git (prove_record's reader - never running git), and each checkout's
own file is folded in once per version. REG-2343 withdrew a first cut for four holes; each is driven here:
  (a) a PASS proved where an ignored input was ABSENT is refused where it exists; a row with no per-tree facts (folded)
      carries only in its own checkout; a listed tracked folder's untracked names are held across checkouts;
  (b) a writer writes only its own rows and drops - a row it merely loaded never comes back over another's drop;
  (c) old code never opens the machine file (it keeps writing tv/.gate_ledger.json, folded in, never written);
  (d) a --record with no trace stores nothing and drops nothing.
Every git command here runs on a throwaway repository with GIT_* removed for its own scope (REG-2392).
RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import gate_ledger as GL  # noqa: E402

_HAVE_GIT = shutil.which("git") is not None
#: the modules a fixture checkout needs to answer ledger_path() and fold, copied from THIS tree (a tampered one too)
_CARRIED = ("gate_ledger.py", "prove_record.py", "console_safe.py")


def _git_free():
    return dict((k, v) for k, v in os.environ.items() if not str(k).upper().startswith("GIT_"))


def _git(root, *args):
    proc = subprocess.run(["git", "-C", root] + list(args), env=_git_free(), capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "git failed").strip())
    return proc


def _write(root, rel, text):
    full = os.path.join(root, *rel.split("/"))
    if not os.path.isdir(os.path.dirname(full)):
        os.makedirs(os.path.dirname(full))
    with io.open(full, "w", encoding="utf-8") as fh:
        fh.write(text)


def _repo(files=None):
    """A throwaway main checkout with one commit. -> its root (realpath)"""
    root = os.path.realpath(tempfile.mkdtemp(prefix="ledger-machine."))
    _write(root, ".gitignore", "*.flag\n.gate_ledger.json\n.gate_inputs.json\n*.tmp\n")
    for rel, text in (files or {"tv/t_law.py": "print('ok')\n"}).items():
        _write(root, rel, text)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "ledger@fixture")
    _git(root, "config", "user.name", "ledger")
    _git(root, "config", "commit.gpgsign", "false")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "fixture")
    return root


class _ScrubbedGit(unittest.TestCase):
    """GIT_* out of this process for each case: the ledger's own git questions go to the fixture, never a hook's repo."""

    def setUp(self):
        self._held = dict((k, v) for k, v in os.environ.items() if str(k).upper().startswith("GIT_"))
        for k in self._held:
            os.environ.pop(k, None)
        self._seam = os.environ.pop("TV_GATE_LEDGER", None)
        self.addCleanup(self._restore)

    def _restore(self):
        os.environ.update(self._held)
        if self._seam is not None:
            os.environ["TV_GATE_LEDGER"] = self._seam


@unittest.skipUnless(_HAVE_GIT, "no git on PATH - a worktree-shaped fixture cannot be made here")
class TheLedgerIsTheMachines(_ScrubbedGit):
    def setUp(self):
        super(TheLedgerIsTheMachines, self).setUp()
        self.main = _repo()
        self.addCleanup(shutil.rmtree, self.main, True)
        self.wt = os.path.realpath(tempfile.mkdtemp(prefix="ledger-wt.")) + "-tree"
        _git(self.main, "worktree", "add", "-q", "--detach", self.wt)
        self.addCleanup(shutil.rmtree, self.wt, True)
        self.want = os.path.join(self.main, ".git", GL.LEDGER_DIR, GL.LEDGER_NAME)

    def _carry_modules(self, root):
        for name in _CARRIED:
            shutil.copy2(os.path.join(HERE, name), os.path.join(root, "tv", name))

    def _ask(self, root, code, seam=None):
        env = _git_free()
        env.pop("TV_GATE_LEDGER", None)
        if seam:
            env["TV_GATE_LEDGER"] = seam
        proc = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, %r)\n%s"
                               % (os.path.join(root, "tv"), code)], cwd=root, env=env, capture_output=True, text=True,
                              timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr[-800:])
        return proc.stdout.strip().splitlines()[-1]

    def test_a_worktree_and_its_main_checkout_name_one_ledger(self):
        self.assertEqual(GL.machine_ledger_path(self.wt), (self.want, None))
        self.assertEqual(GL.machine_ledger_path(self.main), (self.want, None))

    def test_a_relative_worktree_pointer_reaches_the_same_ledger(self):
        with io.open(os.path.join(self.wt, ".git"), encoding="utf-8") as fh:
            gitdir = fh.read().split(":", 1)[1].strip()
        with io.open(os.path.join(self.wt, ".git"), "w", encoding="utf-8") as fh:
            fh.write("gitdir: %s\n" % os.path.relpath(gitdir, self.wt))
        self.assertEqual(GL.machine_ledger_path(self.wt)[0], self.want)

    def test_a_tree_with_no_git_keeps_its_own_ledger_and_says_so(self):
        bare = os.path.realpath(tempfile.mkdtemp(prefix="ledger-nogit."))
        self.addCleanup(shutil.rmtree, bare, True)
        path, why = GL.machine_ledger_path(bare)
        self.assertEqual(path, os.path.join(bare, "tv", GL.LEDGER_NAME))
        self.assertIn("no git dir", why or "")

    def test_ledger_path_in_a_worktree_is_the_machines_unless_the_seam_names_one(self):
        self._carry_modules(self.wt)
        got = self._ask(self.wt, "import gate_ledger as GL; print(GL.ledger_path())")
        self.assertEqual(os.path.realpath(got), os.path.realpath(self.want),
                         "a worktree's ledger is not the machine's - each fresh worktree starts with nothing carried")
        seam = os.path.join(self.wt, "seam.json")
        self.assertEqual(self._ask(self.wt, "import gate_ledger as GL; print(GL.ledger_path())", seam=seam), seam)

    def test_each_checkouts_own_file_is_folded_once_and_never_over_the_machines(self):
        row = {"ok": True, "gate": "%s", "sha": "a" * 40, "at": 1, "traced": True, "inputs": [], "listed": [],
               "imports": [], "untracked": [], "snaps": {}, "def": "d", "tools": []}
        for root, gate in ((self.main, "g_main"), (self.wt, "g_wt"), (self.wt, "g_both")):
            path = os.path.join(root, "tv", GL.LEDGER_NAME)
            data = {"v": 2, "entries": {}, "reds": {}}
            if os.path.exists(path):
                with io.open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
            data["entries"][gate] = json.loads(json.dumps(row) % gate)
            with io.open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
        os.makedirs(os.path.dirname(self.want))
        machine = {"v": 2, "entries": {"g_both": dict(json.loads(json.dumps(row) % "g_both"), sha="b" * 40)},
                   "reds": {}}
        with io.open(self.want, "w", encoding="utf-8") as fh:
            json.dump(machine, fh)
        self._carry_modules(self.main)
        self._ask(self.main, "import gate_ledger as GL; GL.Ledger()._ensure(); print('folded')")
        with io.open(self.want, encoding="utf-8") as fh:
            got = json.load(fh)
        rows = got["entries"]
        self.assertEqual(rows.get("g_main", {}).get("tree"), GL._tree_id(self.main), "main's own row was not folded in")
        self.assertEqual(rows.get("g_wt", {}).get("tree"), GL._tree_id(self.wt),
                         "the worktree's own row was not folded in")
        self.assertEqual(rows["g_both"]["sha"], "b" * 40, "a folded row overwrote the machine's own")
        stamp = os.stat(self.want).st_mtime_ns
        self._ask(self.main, "import gate_ledger as GL; GL.Ledger()._ensure(); print('again')")
        self.assertEqual(os.stat(self.want).st_mtime_ns, stamp, "an unchanged checkout file was folded twice")


@unittest.skipUnless(_HAVE_GIT, "no git on PATH - the record fixture cannot be made here")
class APassCarriesOnlyWhereItWasTrue(_ScrubbedGit):
    def setUp(self):
        super(APassCarriesOnlyWhereItWasTrue, self).setUp()
        self.root = _repo({"tv/t_law.py": "import os\nprint(os.path.exists('tv/x.flag'))\n", "tv/keep.txt": "k\n"})
        self.addCleanup(shutil.rmtree, self.root, True)
        self.path = os.path.join(self.root, "ledger", GL.LEDGER_NAME)

    def _gate(self, root=None):
        where = root or self.root

        class _G(object):
            name = "machine-fixture"
            argv = [sys.executable, os.path.join(where, "tv", "t_law.py")]
            timeout = 30
            cwd = where
            needs_app = False
            skip_ok = ()
        return _G()

    def _open(self):
        return GL.Ledger(path=self.path, probes={"python": "3", "node": "v1", "playwright": "1"})

    def _facts(self, **extra):
        facts = {"R": {"tv/t_law.py"}, "W": set(), "S": set(), "A": {"tv/x.flag"}, "L": set(), "I": set(),
                 "G": set(), "M": set(), "D": {}}
        facts.update(extra)
        return facts

    def test_an_ignored_input_proved_absent_stops_the_carry_where_it_exists(self):
        book = self._open()
        self.assertTrue(book.record(self._gate(), True, trace=self._facts()), "PREMISE: %s" % book.last_why)
        entry, why = self._open().lookup(self._gate())
        self.assertIsNotNone(entry, "PREMISE: the PASS does not carry where it was proved: %s" % why)
        _write(self.root, "tv/x.flag", "now here\n")
        entry, why = self._open().lookup(self._gate())
        self.assertIsNone(entry, "a PASS proved without an ignored file carried where the file exists")
        self.assertIn("tv/x.flag exists in this checkout", why or "")

    def test_a_pass_proved_in_main_carries_into_a_fresh_worktree_only_where_its_facts_hold(self):
        wt = os.path.realpath(tempfile.mkdtemp(prefix="ledger-carry.")) + "-wt"
        _git(self.root, "worktree", "add", "-q", "--detach", wt)
        self.addCleanup(shutil.rmtree, wt, True)
        book = self._open()
        self.assertTrue(book.record(self._gate(), True, trace=self._facts()), "PREMISE: %s" % book.last_why)
        entry, why = self._open().lookup(self._gate(wt))
        self.assertIsNotNone(entry, "a PASS proved in main did not carry into a fresh worktree of the same bytes: %s"
                             % why)
        _write(wt, "tv/x.flag", "only in the worktree\n")
        entry, why = self._open().lookup(self._gate(wt))
        self.assertIsNone(entry, "main's PASS carried into a worktree holding an ignored file it was proved without")
        self.assertIn("tv/x.flag exists in this checkout", why or "")

    def test_a_row_with_no_per_tree_facts_carries_only_in_its_own_checkout(self):
        book = self._open()
        self.assertIsNone(book._tree_moved({"tree": GL._tree_id(self.root)}, self.root))
        why = book._tree_moved({"tree": GL._tree_id(self.root + "-elsewhere")}, self.root)
        self.assertIn("another checkout", why or "", "a folded row carried into a checkout it was never proved in")

    def test_a_listed_folders_untracked_names_hold_across_checkouts_only(self):
        _write(self.root, "tv/.ignored.flag", "x")
        book = self._open()
        tf = book._tree_facts(self._facts(D={"tv": "digest"}), self.root)
        self.assertEqual(tf["listed"].get("tv"), [".ignored.flag"], "a listed folder's ignored names were not kept")
        other = {"tree": GL._tree_id(self.root + "-another"), "tree_facts": tf}
        self.assertIsNone(book._tree_moved(other, self.root), "the same untracked names refused a carry")
        _write(self.root, "tv/second.flag", "y")
        self.assertIn("other untracked names", book._tree_moved(other, self.root) or "",
                      "another checkout's different ignored names carried a PASS that listed the folder")
        own = {"tree": GL._tree_id(self.root), "tree_facts": tf}
        self.assertIsNone(book._tree_moved(own, self.root), "the checkout's own ignored names stopped its own carry")

    def test_a_record_with_no_trace_drops_nothing(self):
        book = self._open()
        self.assertTrue(book.record(self._gate(), True, trace=self._facts()), "PREMISE: %s" % book.last_why)
        again = self._open()
        self.assertFalse(again.record(self._gate(), True, trace=None), "a PASS with no trace was stored")
        entry, why = self._open().lookup(self._gate())
        self.assertIsNotNone(entry, "a --record with no trace dropped the stored PASS: %s" % why)

    def test_a_writer_never_writes_back_a_row_it_only_loaded(self):
        first = self._open()
        self.assertTrue(first.record(self._gate(), True, trace=self._facts()), "PREMISE: %s" % first.last_why)
        a, b = self._open(), self._open()
        a._ensure()
        b._ensure()
        b._drop("machine-fixture")  # another writer's FAIL on these bytes
        a.proven = None
        a._own.add("another-gate")
        a.entries["another-gate"] = dict(a.entries["machine-fixture"], gate="another-gate")
        a._write()
        with io.open(self.path, encoding="utf-8") as fh:
            rows = json.load(fh)["entries"]
        self.assertNotIn("machine-fixture", rows, "a row one writer only loaded came back over another's drop")
        self.assertIn("another-gate", rows, "the writer's own row was not written")


RED_PROOF = [
    {"why": "the ledger is this checkout's own again (HERE)", "file": "gate_ledger.py",
     "find": "    return os.environ.get(\"TV_GATE_LEDGER\") or machine_ledger_path()[0]  # LEDGER-PER-MACHINE\n",
     "replace": "    return os.environ.get(\"TV_GATE_LEDGER\") or os.path.join(HERE, LEDGER_NAME)  # LEDGER-PER-MACHINE\n",
     "matches": 1},
    {"why": "the machine ledger is not in git's common dir", "file": "gate_ledger.py",
     "find": "    return os.path.join(common, LEDGER_DIR, LEDGER_NAME), None  # LEDGER-MACHINE-PATH\n",
     "replace": "    return os.path.join(repo, \"tv\", LEDGER_NAME), None  # LEDGER-MACHINE-PATH\n", "matches": 1},
    {"why": "a folded row overwrites the machine's own", "file": "gate_ledger.py",
     "find": "                    if name in disk or name in self.dropped:\n",
     "replace": "                    if name in self.dropped:\n", "matches": 1},
    {"why": "a folded row carries into every checkout", "file": "gate_ledger.py",
     "find": "                        row[\"tree\"] = _tree_id(root)  # LEDGER-FOLD-OWN-TREE\n",
     "replace": "                        pass  # LEDGER-FOLD-OWN-TREE\n", "matches": 1},
    {"why": "an absent ignored input is not kept", "file": "gate_ledger.py",
     "find": "                absent.append(path)  # LEDGER-TREE-ABSENT\n",
     "replace": "                pass  # LEDGER-TREE-ABSENT\n", "matches": 1},
    {"why": "the carry never asks the per-tree facts", "file": "gate_ledger.py",
     "find": "        tree_why = self._tree_moved(entry, root)  # LEDGER-TREE-FACTS\n",
     "replace": "        tree_why = None  # LEDGER-TREE-FACTS\n", "matches": 1},
    {"why": "a row with no per-tree facts carries anywhere", "file": "gate_ledger.py",
     "find": "            if tree and tree != here:\n                return \"this PASS was proved in another checkout",
     "replace": "            if False:\n                return \"this PASS was proved in another checkout", "matches": 1},
    {"why": "another checkout's untracked names are not compared", "file": "gate_ledger.py",
     "find": "                if self._untracked_names(root, folder, tracked, dirs) != names:  # LEDGER-TREE-LISTED\n",
     "replace": "                if False:  # LEDGER-TREE-LISTED\n", "matches": 1},
    {"why": "a record with no trace drops the stored PASS", "file": "gate_ledger.py",
     "find": "            if name and (trace or red):  # LEDGER-NO-TRACE-NO-DROP\n",
     "replace": "            if name:  # LEDGER-NO-TRACE-NO-DROP\n", "matches": 1},
    {"why": "a writer writes back every row it loaded", "file": "gate_ledger.py",
     "find": "                touched = self.dropped | self._own\n",
     "replace": "                touched = self.dropped | self._own | set(self.entries or {})\n", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=1)
