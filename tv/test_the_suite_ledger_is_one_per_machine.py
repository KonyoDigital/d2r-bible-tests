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
REG-2449 - what a run MADE carries only where it would make it again. A worktree's PASS whose run found an ignored
store ABSENT and created it (exists() then create, an append onto nothing, a mkdir) carried into the main checkout,
which holds that store with other bytes - where the same gate fails - and so did one whose run appended to a store it
found there, and one that wrote into an ignored folder main lacks. A node child's listing of a tracked folder was never
held (it wrote L and no D). Driven here with REAL traced runs in a linked worktree; in its own checkout the run's
leftovers stay today's rule.
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
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import gate_ledger as GL  # noqa: E402

_HAVE_GIT = shutil.which("git") is not None
_HAVE_NODE = shutil.which("node") is not None
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
        # This ledger is the fixture, not the runner's verdict. The CI block stays on for the suite.
        self._ci = mock.patch("gate_ledger.ci_blocks", return_value=False)
        self._ci.start()
        self.addCleanup(self._ci.stop)
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


# ── REG-2449: what the run made, held across checkouts by real traced runs ─────────────────────────────────────────────
#: law bodies, each a gate that PASSES on a fresh tree and FAILS where the ignored path it makes is already there
_MADE_LAWS = {
    "exists then create": ("tv/live.store", "p = os.path.join(H, 'live.store')\n"
                                            "if not os.path.exists(p):\n"
                                            "    with open(p, 'w') as fh:\n"
                                            "        fh.write('ok')\n"
                                            "with open(p) as fh:\n"
                                            "    sys.exit(0 if fh.read() == 'ok' else 1)\n"),
    "append onto nothing": ("tv/journal.store", "p = os.path.join(H, 'journal.store')\n"
                                                "with open(p, 'a') as fh:\n"
                                                "    fh.write('x')\n"
                                                "with open(p) as fh:\n"
                                                "    sys.exit(0 if fh.read() == 'x' else 1)\n"),
    "mkdir": ("tv/made.store", "os.mkdir(os.path.join(H, 'made.store'))\n"),
}
_KEPT_LAW = ("p = os.path.join(H, 'log.store')\n"
             "with open(p, 'a') as fh:\n"
             "    fh.write('+')\n"
             "with open(p) as fh:\n"
             "    sys.exit(0 if fh.read().startswith('seed') else 1)\n")
_INTO_LAW = ("with open(os.path.join(H, 'scratch', 'out.store'), 'w') as fh:\n"
             "    fh.write('written into a folder it found')\n")
_GLOB_LAW = ("import glob\n"
             "sys.exit(1 if glob.glob(os.path.join(H, 'footage', '*.jpg')) else 0)\n")
_NODE_LISTER = ("const fs = require('fs');\n"
                "process.exit(fs.readdirSync(__dirname).some((n) => n.endsWith('.flag')) ? 1 : 0);\n")


@unittest.skipUnless(_HAVE_GIT, "no git on PATH - a worktree-shaped fixture cannot be made here")
class WhatTheRunMadeCarriesOnlyWhereItWasNot(_ScrubbedGit):
    def _world(self, body, node=False):
        """A main checkout whose tv/t_law.py is `body`, a fresh linked worktree of it, and a ledger. -> (main, wt)"""
        head = "import os, subprocess, sys\nH = os.path.dirname(os.path.abspath(__file__))\n"
        files = {"tv/t_law.py": head + body, "tv/keep.txt": "k\n"}
        if node:
            files["tv/t_law.py"] = head + "sys.exit(subprocess.run(['node', os.path.join(H, 'list.js')]).returncode)\n"
            files["tv/list.js"] = _NODE_LISTER
        main = _repo(files)
        self.addCleanup(shutil.rmtree, main, True)
        with io.open(os.path.join(main, ".gitignore"), "a", encoding="utf-8") as fh:
            fh.write("*.store\nscratch/\nfootage/\n")
        _git(main, "commit", "-q", "-am", "ignore the stores")
        wt = os.path.realpath(tempfile.mkdtemp(prefix="ledger-made.")) + "-wt"
        _git(main, "worktree", "add", "-q", "--detach", wt)
        self.addCleanup(shutil.rmtree, wt, True)
        self.ledger = os.path.join(os.path.dirname(wt), os.path.basename(wt) + "-ledger", GL.LEDGER_NAME)
        self.addCleanup(shutil.rmtree, os.path.dirname(self.ledger), True)
        return main, wt

    def _gate(self, root):
        class _G(object):
            name = "made-fixture"
            argv = [sys.executable, os.path.join(root, "tv", "t_law.py")]
            timeout = 60
            cwd = root
            needs_app = False
            skip_ok = ()
        return _G()

    def _book(self):
        return GL.Ledger(path=self.ledger, probes={"python": "3", "node": "v1", "playwright": "1"})

    def _record(self, root):
        """Run the gate traced in `root` and record its PASS. -> the trace's facts"""
        trace = GL.trace_path()
        try:
            proc = subprocess.run(self._gate(root).argv, cwd=root, env=GL.trace_env(_git_free(), root, trace),
                                  capture_output=True, text=True, timeout=120)
            facts, why = GL.read_trace(trace)
        finally:
            if os.path.exists(trace):
                os.remove(trace)
        self.assertEqual(proc.returncode, 0, "PREMISE: the gate failed where it was proved: %s" % proc.stderr[-600:])
        self.assertIsNone(why, "PREMISE: the run was untraced: %s" % why)
        book = self._book()
        self.assertTrue(book.record(self._gate(root), True, trace=facts), "PREMISE: not recorded: %s" % book.last_why)
        return facts

    def _carries(self, root):
        entry, why = self._book().lookup(self._gate(root))
        return entry is not None, why

    def _runs(self, root):
        return subprocess.run(self._gate(root).argv, cwd=root, env=_git_free(), capture_output=True, text=True,
                              timeout=120).returncode

    def test_a_pass_whose_run_made_what_it_found_absent_stays_out_of_a_checkout_that_holds_it(self):
        for how, (made, body) in sorted(_MADE_LAWS.items()):
            with self.subTest(how=how):
                main, wt = self._world(body)
                facts = self._record(wt)
                self.assertIn(made, facts["MA"], "PREMISE: the trace did not say the run found %s absent" % made)
                ok, why = self._carries(main)
                self.assertTrue(ok, "PREMISE (%s): the PASS did not carry into main, which lacks %s: %s" % (how, made, why))
                if how == "mkdir":
                    os.makedirs(os.path.join(main, *made.split("/")))
                else:
                    _write(main, made, "his live bytes")
                self.assertNotEqual(self._runs(main), 0, "PREMISE (%s): the gate passes in main anyway" % how)
                ok, why = self._carries(main)
                self.assertFalse(ok, "(%s) a worktree's PASS whose run found %s absent and made it carried into a "
                                     "checkout that holds it - where the gate fails" % (how, made))
                self.assertIn("found it absent and made it", why or "")
                ok, why = self._carries(wt)
                self.assertTrue(ok, "(%s) the run's own leftover stopped the carry in its own checkout: %s" % (how, why))

    def test_a_store_whose_bytes_the_run_kept_carries_only_onto_the_same_bytes(self):
        main, wt = self._world(_KEPT_LAW)
        for root in (main, wt):
            _write(root, "tv/log.store", "seed\n")
        self._record(wt)
        ok, why = self._carries(main)
        self.assertTrue(ok, "PREMISE: the PASS did not carry into main, which holds the same bytes: %s" % why)
        _write(main, "tv/log.store", "other\n")
        self.assertNotEqual(self._runs(main), 0, "PREMISE: the gate passes on other bytes anyway")
        _write(main, "tv/log.store", "other\n")
        ok, why = self._carries(main)
        self.assertFalse(ok, "a PASS whose run appended to and read back an ignored store carried onto other bytes")
        self.assertIn("not the bytes the run found and kept", why or "")

    def test_a_pass_that_wrote_into_an_ignored_folder_stays_out_of_a_checkout_without_it(self):
        main, wt = self._world(_INTO_LAW)
        os.makedirs(os.path.join(wt, "tv", "scratch"))
        self._record(wt)
        self.assertNotEqual(self._runs(main), 0, "PREMISE: the gate passes in main without the folder")
        ok, why = self._carries(main)
        self.assertFalse(ok, "a PASS whose run wrote into an ignored folder carried into a checkout without it")
        self.assertIn("tv/scratch is not a folder", why or "")
        os.makedirs(os.path.join(main, "tv", "scratch"))
        ok, why = self._carries(main)
        self.assertTrue(ok, "the folder is there and the PASS still did not carry: %s" % why)

    def test_a_pass_that_listed_an_absent_ignored_folder_stays_out_of_a_checkout_that_holds_it(self):
        """A glob of an ignored folder the proving checkout lacks is a listing (L, D "-"), no R, S or A: before, no
        per-tree fact held it, so the PASS carried into main where the folder holds a match - and in its own checkout
        once the folder came."""
        main, wt = self._world(_GLOB_LAW)
        facts = self._record(wt)
        self.assertEqual(facts["D"].get("tv/footage"), "-", "PREMISE: the trace did not list the absent folder")
        ok, why = self._carries(main)
        self.assertTrue(ok, "PREMISE: the PASS did not carry into main, which lacks the folder too: %s" % why)
        for root, where in ((main, "another checkout"), (wt, "its own checkout")):
            _write(root, "tv/footage/a.jpg", "a frame")
            self.assertNotEqual(self._runs(root), 0, "PREMISE: the gate passes in %s anyway" % where)
            ok, why = self._carries(root)
            self.assertFalse(ok, "a PASS proved where an ignored folder it listed was absent carried into %s, where "
                                 "it holds a match" % where)
            self.assertIn("tv/footage exists in this checkout", why or "")

    @unittest.skipUnless(_HAVE_NODE, "no node on PATH - the node lister cannot run here")
    def test_a_node_childs_listing_holds_the_folders_ignored_names_across_checkouts(self):
        main, wt = self._world("", node=True)
        facts = self._record(wt)
        self.assertIn("tv", facts["L"], "PREMISE: the node child's listing is not in the trace")
        _write(main, "tv/x.flag", "an ignored name only main holds\n")
        self.assertNotEqual(self._runs(main), 0, "PREMISE: the gate passes in main anyway")
        ok, why = self._carries(main)
        self.assertFalse(ok, "a PASS whose node child listed tv carried into a checkout with another ignored name there")
        self.assertIn("holds other untracked names", why or "")


@unittest.skipUnless(_HAVE_GIT, "no git on PATH - the record fixture cannot be made here")
class TheTreeFactsAskWhatTheyMust(_ScrubbedGit):
    def setUp(self):
        super(TheTreeFactsAskWhatTheyMust, self).setUp()
        self.root = _repo({"tv/t_law.py": "print('ok')\n", "tv/keep.txt": "k\n"})
        self.addCleanup(shutil.rmtree, self.root, True)
        self.book = GL.Ledger(path=os.path.join(self.root, "ledger", GL.LEDGER_NAME),
                              probes={"python": "3", "node": "v1", "playwright": "1"})

    def test_an_L_of_a_tracked_folder_is_a_listing_even_without_its_D(self):
        """REG-2449 - a node child wrote L and no D; any L of a folder is a listing. L "" alone is git ls-files."""
        _write(self.root, "tv/.ignored.flag", "x")
        facts = {"R": set(), "W": set(), "S": set(), "A": set(), "L": {"tv", ""}, "I": set(), "G": set(), "M": set(),
                 "D": {}}
        tf = self.book._tree_facts(facts, self.root)
        self.assertEqual(tf["listed"].get("tv"), [".ignored.flag"], "an L without a D was not held as a listing")
        self.assertNotIn("", tf["listed"], "git ls-files' L \"\" was taken for a listing of the root's names")

    def test_a_row_of_another_tree_facts_version_carries_only_in_its_own_checkout(self):
        old = {"absent": [], "folders": [], "listed": {}}
        why = self.book._tree_moved({"tree": GL._tree_id(self.root + "-elsewhere"), "tree_facts": old}, self.root)
        self.assertIn("another checkout", why or "", "a row from before REG-2449 carried into another checkout")
        self.assertIsNone(self.book._tree_moved({"tree": GL._tree_id(self.root), "tree_facts": old}, self.root))


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
    # REG-2449 - what the run made
    {"why": "REG-2449 - read_trace names no path the run found absent and then made", "file": "gate_ledger.py",
     "find": "    facts[\"MA\"] = set(p for p in facts[\"M\"] if first.get(p) == \"A\" or hashed.get(p) == \"-\")  "
             "# LEDGER-FOUND-ABSENT\n",
     "replace": "    facts[\"MA\"] = set()  # LEDGER-FOUND-ABSENT\n", "matches": 1},
    {"why": "REG-2449 - the per-tree facts keep no path the run found absent and made", "file": "gate_ledger.py",
     "find": "                made_absent.append(path)  # LEDGER-TREE-MADE-ABSENT\n",
     "replace": "                pass  # LEDGER-TREE-MADE-ABSENT\n", "matches": 1},
    {"why": "REG-2449 - another checkout is never asked whether it holds what the run found absent and made",
     "file": "gate_ledger.py",
     "find": "                if os.path.lexists(_fact_path(root, path)):  # LEDGER-TREE-MADE-ABSENT-MOVED\n",
     "replace": "                if False:  # LEDGER-TREE-MADE-ABSENT-MOVED\n", "matches": 1},
    {"why": "REG-2449 - the run's own leftovers stop the carry in its own checkout", "file": "gate_ledger.py",
     "find": "        if tree != here:\n            for path in tf.get(\"made_absent\") or ():\n",
     "replace": "        if True:\n            for path in tf.get(\"made_absent\") or ():\n", "matches": 1},
    {"why": "REG-2449 - the bytes a run kept are no per-tree fact", "file": "gate_ledger.py",
     "find": "                kept[path] = hashed[path]  # LEDGER-TREE-KEPT\n",
     "replace": "                pass  # LEDGER-TREE-KEPT\n", "matches": 1},
    {"why": "REG-2449 - another checkout's kept bytes are never compared", "file": "gate_ledger.py",
     "find": "                if _fact_bytes(root, path) != d:  # LEDGER-TREE-KEPT-MOVED\n",
     "replace": "                if False:  # LEDGER-TREE-KEPT-MOVED\n", "matches": 1},
    {"why": "REG-2449 - the folder a made file was written into is no per-tree fact", "file": "gate_ledger.py",
     "find": "            folders.append(folder)  # LEDGER-TREE-WRITE-FOLDER\n",
     "replace": "            pass  # LEDGER-TREE-WRITE-FOLDER\n", "matches": 1},
    {"why": "REG-2449 - only a D is a listing, so a node child's listing is never held", "file": "gate_ledger.py",
     "find": "        for folder in sorted((set(d_facts) | set(p for p in (facts.get(\"L\") or ()) if p)) - made):  "
             "# LEDGER-TREE-L\n",
     "replace": "        for folder in sorted(set(d_facts) - made):  # LEDGER-TREE-L\n", "matches": 1},
    {"why": "REG-2449 - a folder the run listed and found absent is no per-tree fact", "file": "gate_ledger.py",
     "find": "                absent.append(folder)  # LEDGER-TREE-LISTED-ABSENT\n",
     "replace": "                pass  # LEDGER-TREE-LISTED-ABSENT\n", "matches": 1},
    {"why": "REG-2449 - a row of an older tree-facts version carries into another checkout", "file": "gate_ledger.py",
     "find": "        if not isinstance(tf, dict) or tf.get(\"v\") != TREE_FACTS_VERSION:\n",
     "replace": "        if not isinstance(tf, dict):\n", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=1)
