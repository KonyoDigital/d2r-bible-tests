# -*- coding: utf-8 -*-
"""REG-2442 (#147 R1) - A TRACE NAMES EVERY READ A KEY NEEDS, AND A LATER TREE IS HELD TO ALL OF THEM.

The ledger carries a gate by git's word; a proof memory (heart2, track heart-memory) has to serve a verdict on ANOTHER
tree - the next push's sandbox - so it needs the run's own facts, checked against that tree. Measured at 7285e7efc
(critic could_lie #1-#3): gate_trace dropped every path outside its root without a word (a sandboxed law reading the
real checkout, ~/d2r_ledger_backups or the shared temp dir vanished from its facts), wrote no fact for an environment
read, kept a stat as presence only (a size change, getmtime and getctime all looked alike), and importing sqlite3,
mmap, ctypes or dbm read files no open event names.

Driven here on fixture trees, each run under the REAL hook (gate_trace/sitecustomize.py, node_trace.cjs):
  * TV_GATE_TRACE_DENY / _ALLOW - an open, a listing, a stat or a git child under a denied root that no allowed root
    covers is a U, by the path as given and by its real folder; outside every denied root it is dropped as before.
  * TV_GATE_TRACE_STRICT=1 - importing sqlite3 (mmap, ctypes, dbm) and os.path.getmtime under the root are a U.
  * E facts for single-name environment reads only (os.environ[X], .get, in, os.getenv); a bulk copy writes none, a
    plumbing name is none, a name the process set first is none, and a child's read of a value its parent MADE is none.
  * Z size facts (S stays presence-only), H bytes as read, D listings as listed, T the tracked set ls-files named.
  * REG-2446 - a pathlib probe (Path.stat, .exists, .is_symlink) writes its facts on python 3.9/3.10 too, whose pathlib
    copies os.stat into its accessor: imported before the hook (his Mac's .pth) or after it (`-s`).
  * gate_ledger.facts_of / facts_hold: an identical tree holds; one byte, one size, one listed name, one env value, an
    absent file that appears, a module that would now shadow an import, a kept-bytes (append) file, the tracked set
    and a .gitignore each break it. read_trace() still reads a C line exactly like U by default.
  * REG-2449 - what the run MADE is held where it found something first: a file it found absent and then created
    (exists() then create, an append onto nothing, an 'x' open, a mkdir - python and node), and the folder a made file
    was written into. A node listing writes D, the same digest as python's; a recursive node listing and fs.cp are a U.
    A name gone mid-listing reads `?`, never "the folder is absent".
RED_PROOF below; every git command here runs with GIT_* removed (a hook's GIT_DIR must never reach a throwaway repo).
"""
import hashlib
import io
import json
import os
import re
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

_HAVE_NODE = shutil.which("node") is not None
_HAVE_GIT = shutil.which("git") is not None
_POSIX = os.name == "posix"


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git_free(env):
    """The environment with every GIT_* removed (REG-2392: a hook's GIT_DIR beats cwd= and -C)."""
    return dict((k, v) for k, v in env.items() if not str(k).upper().startswith("GIT_"))


def _write(root, rel, text, mode="w"):
    full = os.path.join(root, *rel.split("/"))
    folder = os.path.dirname(full)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with io.open(full, mode, encoding="utf-8") as fh:
        fh.write(text)


def _gone(root, rel):
    full = os.path.join(root, *rel.split("/"))
    if os.path.isdir(full) and not os.path.islink(full):
        shutil.rmtree(full)
    elif os.path.lexists(full):
        os.remove(full)


def _traced(root, script, env_extra=None, deny=None, allow=None, strict=False, allow_cdp=False, argv0=None):
    """Run `script` (a tv/ file of `root`) under the real hook. -> (completed, facts, why)"""
    trace = GL.trace_path()
    try:
        env = GL.trace_env(_git_free(dict(os.environ, **(env_extra or {}))), root, trace,
                           deny=deny, allow=allow, strict=strict)
        proc = subprocess.run(list(argv0 or [sys.executable]) + [os.path.join(root, "tv", script)], cwd=root, env=env,
                              capture_output=True, text=True, timeout=120)
        facts, why = GL.read_trace(trace, allow_cdp_chrome=allow_cdp)
    finally:
        if os.path.exists(trace):
            os.remove(trace)
    return proc, facts, why


# ── the facts run: one fixture tree, one traced run, every kind of fact ────────────────────────────────────────────────
_PRISTINE = {
    "tv/data.txt": "hello\n",
    "tv/sized.txt": "four",
    "tv/sub/a.txt": "a\n",
    "tv/log.txt": "old log\n",
    "tv/helper_fx.py": "X = 1\n",
    "tv/outbox/keep.txt": "k\n",
}
_FACTS_LAW = r"""import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import helper_fx
open(os.path.join(HERE, 'data.txt')).read()
os.listdir(os.path.join(HERE, 'sub'))
with open(os.path.join(HERE, 'sub', 'made_after.txt'), 'w') as fh:
    fh.write('left behind after the listing')
os.path.getsize(os.path.join(HERE, 'sized.txt'))
os.lstat(os.path.join(HERE, 'data.txt'))
os.path.isdir(os.path.join(HERE, 'sub'))
os.path.exists(os.path.join(HERE, 'absent.flag'))
os.path.exists(os.path.join(HERE, 'data.txt', 'under_a_file'))
with open(os.path.join(HERE, 'log.txt'), 'a') as fh:
    fh.write('more\n')
with open(os.path.join(HERE, 'made.txt'), 'w') as fh:
    fh.write('mine\n')
open(os.path.join(HERE, 'made.txt')).read()
os.path.getsize(os.path.join(HERE, 'made.txt'))
state = os.path.join(HERE, 'state.json')
if not os.path.exists(state):
    with open(state, 'w') as fh:
        fh.write('{}')
open(state).read()
os.path.getsize(state)
with open(os.path.join(HERE, 'fresh.log'), 'a') as fh:
    fh.write('first line\n')
os.mkdir(os.path.join(HERE, 'made_dir'))
with open(os.path.join(HERE, 'excl.txt'), 'x') as fh:
    fh.write('mine alone\n')
with open(os.path.join(HERE, 'outbox', 'sent.txt'), 'w') as fh:
    fh.write('into a folder it found\n')
os.environ['TV_KNOB_A']
os.environ.get('TV_KNOB_B')
'TV_KNOB_C' in os.environ
os.getenv('TV_KNOB_D')
bulk = (dict(os.environ), os.environ.copy(), list(os.environ.items()), list(os.environ.values()), {**os.environ})
os.environ['TV_KNOB_SET'] = 'x'
os.environ['TV_KNOB_SET']
os.environ.get('TMPDIR'), os.environ.get('HEART2_X'), os.environ.get('TV_LANE_PORT_BASE'), os.environ.get('TV_GATE_Q')
child_env = dict(os.environ, CHILD_ONLY='made by the parent')
subprocess.run([sys.executable, '-c', "import os; os.environ.get('CHILD_ONLY'); os.environ['TV_KNOB_A']; "
                "os.environ.get('TV_KNOB_E')"], env=child_env, check=True)
print('facts law ok')
"""
_KNOBS = {"TV_KNOB_A": "alpha", "TV_KNOB_C": "gamma", "TV_KNOB_D": "delta", "TV_KNOB_E": "eps",
          "TV_KNOB_BULK": "read only in bulk", "HEART2_X": "per run", "TV_LANE_PORT_BASE": "17900"}
_MEMO = {}


def _facts_run():
    """One traced run of _FACTS_LAW on a fresh fixture, its facts, its record, and the tree put back. Memoised."""
    if "run" in _MEMO:
        return _MEMO["run"]
    root = tempfile.mkdtemp(prefix="facts.")
    for rel, text in _PRISTINE.items():
        _write(root, rel, text)
    _write(root, "tv/t_facts.py", _FACTS_LAW)
    env = dict((k, v) for k, v in _KNOBS.items())
    proc, facts, why = _traced(root, "t_facts.py", env_extra=env)
    rec = GL.facts_of(root, facts) if facts is not None else None
    # the tree the NEXT run would start from: the run's own leftovers gone, its append undone
    for rel in ("tv/sub/made_after.txt", "tv/made.txt", "tv/state.json", "tv/fresh.log", "tv/made_dir", "tv/excl.txt",
                "tv/outbox/sent.txt"):
        _gone(root, rel)
    _write(root, "tv/log.txt", _PRISTINE["tv/log.txt"])
    _MEMO["run"] = (root, proc, facts, why, rec)
    return _MEMO["run"]


def _base_env():
    return dict(os.environ, **dict((k, v) for k, v in _KNOBS.items()))


class TheFactsRunIsTraced(unittest.TestCase):
    def setUp(self):
        self.root, self.proc, self.facts, self.why, self.rec = _facts_run()

    def test_the_fixture_ran_traced(self):
        self.assertEqual(self.proc.returncode, 0, "PREMISE: the fixture law failed: %s" % self.proc.stderr[-800:])
        self.assertIsNone(self.why, "PREMISE: the facts run was untraced: %s" % self.why)


class ASingleNameEnvironmentReadIsAFact(unittest.TestCase):
    def setUp(self):
        self.root, self.proc, self.facts, self.why, self.rec = _facts_run()
        if self.facts is None:
            self.fail("PREMISE: no facts (%s)" % self.why)
        self.env = self.facts["E"]

    def test_each_single_name_read_is_its_value_digest(self):
        self.assertEqual(self.env.get("TV_KNOB_A"), _sha("alpha"), "os.environ[X] wrote no fact")
        self.assertEqual(self.env.get("TV_KNOB_B"), "-", ".get(X) of an absent name wrote no absence fact")
        self.assertEqual(self.env.get("TV_KNOB_C"), _sha("gamma"), "X in os.environ wrote no fact")
        self.assertEqual(self.env.get("TV_KNOB_D"), _sha("delta"), "os.getenv(X) wrote no fact")

    def test_a_bulk_copy_writes_nothing(self):
        self.assertNotIn("TV_KNOB_BULK", self.env, "a bulk copy of the environment became a single-name fact")

    def test_plumbing_and_a_name_the_process_set_are_no_fact(self):
        for name in ("TMPDIR", "HEART2_X", "TV_LANE_PORT_BASE", "TV_GATE_Q", "TV_GATE_TRACE"):
            self.assertNotIn(name, self.env, "the prover's per-run name %s became a fact" % name)
        self.assertNotIn("TV_KNOB_SET", self.env, "a name the process set before reading it became a fact")

    def test_a_child_holds_the_roots_values_and_not_what_its_parent_made(self):
        self.assertEqual(self.env.get("TV_KNOB_E"), _sha("eps"), "a child's read of the run's own value wrote no fact")
        self.assertNotIn("CHILD_ONLY", self.env, "a value the parent made became a fact of the child")

    def test_the_three_plumbing_lists_are_one(self):
        import ast
        with io.open(os.path.join(HERE, "gate_trace", "sitecustomize.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        found = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and \
                    node.targets[0].id in ("_PLUMBING", "_PLUMBING_PREFIXES"):
                val = node.value.args[0] if isinstance(node.value, ast.Call) else node.value
                found[node.targets[0].id] = set(ast.literal_eval(val))
        self.assertEqual(found.get("_PLUMBING"), set(GL.TRACE_PLUMBING), "sitecustomize's plumbing set drifted")
        self.assertEqual(found.get("_PLUMBING_PREFIXES"), set(GL.TRACE_PLUMBING_PREFIXES))
        with io.open(os.path.join(HERE, "gate_trace", "node_trace.cjs"), encoding="utf-8") as fh:
            src = fh.read()
        m = re.search(r"const PLUMBING = new Set\(\[([^\]]*)\]\)", src)
        self.assertIsNotNone(m, "node_trace.cjs no longer declares its plumbing set")
        self.assertEqual(set(re.findall(r"'([A-Z_]+)'", m.group(1))), set(GL.TRACE_PLUMBING),
                         "node_trace.cjs's plumbing set drifted")
        for pre in GL.TRACE_PLUMBING_PREFIXES:
            self.assertIn("u.startsWith('%s')" % pre, src, "node_trace.cjs lost the %s prefix" % pre)


class AStatKeepsItsSizeAndTheLedgerReadsAsBefore(unittest.TestCase):
    def setUp(self):
        self.root, self.proc, self.facts, self.why, self.rec = _facts_run()
        if self.facts is None:
            self.fail("PREMISE: no facts (%s)" % self.why)

    def test_a_stat_writes_kind_and_size(self):
        z = self.facts["Z"]
        self.assertEqual(z.get("tv/sized.txt"), {"f": "4"}, "getsize kept no size: %r" % z.get("tv/sized.txt"))
        self.assertEqual(z.get("tv/data.txt"), {"F": "6"}, "an lstat of a file is not told from a followed stat")
        self.assertEqual(z.get("tv/sub"), {"d": "-"})

    @unittest.skipUnless(_POSIX, "ENOTDIR is POSIX's answer for a path under a file (Windows says not found)")
    def test_a_stat_under_a_file_is_an_absence(self):
        self.assertIn("tv/data.txt/under_a_file", self.facts["A"],
                      "REG-2447 - os.path.exists of a path under a FILE (ENOTDIR) wrote no absence fact")

    def test_a_stat_after_the_run_wrote_the_path_is_not_a_fact(self):
        self.assertNotIn("tv/made.txt", self.facts["Z"], "a stat of the run's own file became a size fact")

    def test_the_presence_set_is_what_the_ledger_read_before(self):
        for rel in ("tv/sized.txt", "tv/data.txt", "tv/sub"):
            self.assertIn(rel, self.facts["S"], "S lost %s - the ledger reads S" % rel)
        self.assertIn("tv/absent.flag", self.facts["A"])

    def test_read_trace_still_untraces_on_C_by_default(self):
        trace = GL.trace_path()
        self.addCleanup(os.remove, trace)
        with io.open(trace, "w", encoding="utf-8") as fh:
            fh.write("B\t11\t1\nR\t11\ttv/x.py\nC\t11\tstarted chrome, a Chrome this run started for its pages\n")
        facts, why = GL.read_trace(trace)
        self.assertIsNone(facts, "a ledger read carried a run with an attested Chrome")
        self.assertIn("which the trace cannot follow", why or "")
        facts, why = GL.read_trace(trace, allow_cdp_chrome=True)
        self.assertIsNone(why)
        self.assertEqual(len(facts["C"]), 1)

    def test_the_new_lines_change_no_ledger_set(self):
        trace = GL.trace_path()
        self.addCleanup(os.remove, trace)
        plain = "B\t11\t1\nR\t11\ttv/x.py\nS\t11\ttv/y\nL\t11\ttv\nW\t11\ttv/w\nI\t11\tfoo\n"
        extra = ("N\t11\t%s HOME\nE\t11\t%s HOME\nZ\t11\tf 3 tv/y\nH\t11\t%s tv/x.py\nD\t11\t%s tv\n"
                 "T\t11\t=\x1f\x1f*.py\n" % ((_sha("h"),) * 4))
        with io.open(trace, "w", encoding="utf-8") as fh:
            fh.write(plain)
        before, _w = GL.read_trace(trace)
        with io.open(trace, "w", encoding="utf-8") as fh:
            fh.write(plain + extra)
        after, _w = GL.read_trace(trace)
        for kind in ("R", "W", "S", "A", "L", "I", "G", "M"):
            self.assertEqual(before[kind], after[kind], "the new lines moved the ledger's %s set" % kind)


class ALaterTreeIsHeldToEveryFact(unittest.TestCase):
    def setUp(self):
        self.root, self.proc, self.facts, self.why, self.rec = _facts_run()
        if self.rec is None:
            self.fail("PREMISE: no record (%s)" % self.why)

    def _holds(self, env=None):
        return GL.facts_hold(self.root, self.rec, _base_env() if env is None else env)

    def _breaks(self, why_part, rel=None, text=None, env=None, mkdir=None):
        if rel is not None:
            full = os.path.join(self.root, *rel.split("/"))
            had = None
            if os.path.exists(full):
                with io.open(full, encoding="utf-8") as fh:
                    had = fh.read()
            _write(self.root, rel, text)
            self.addCleanup(lambda: _write(self.root, rel, had) if had is not None else _gone(self.root, rel))
        if mkdir is not None:
            os.makedirs(os.path.join(self.root, mkdir))
            self.addCleanup(_gone, self.root, mkdir)
        ok, why = self._holds(env)
        self.assertFalse(ok, "the tree changed (%s) and the facts still held" % why_part)
        self.assertIn(why_part, why or "")

    def test_the_identical_tree_holds(self):
        ok, why = self._holds()
        self.assertTrue(ok, "the tree the run read does not hold its own facts: %s" % why)

    def test_one_byte_breaks_it(self):
        self._breaks("tv/data.txt", "tv/data.txt", "hellO\n")

    def test_a_size_breaks_it(self):
        self._breaks("tv/sized.txt", "tv/sized.txt", "five!")

    def test_a_listed_name_breaks_it(self):
        self._breaks("tv/sub", "tv/sub/new.txt", "n")

    def test_an_env_value_breaks_it_and_a_bulk_one_does_not(self):
        self._breaks("TV_KNOB_A", env=dict(_base_env(), TV_KNOB_A="beta"))
        self._breaks("TV_KNOB_B", env=dict(_base_env(), TV_KNOB_B="now set"))
        ok, why = self._holds(dict(_base_env(), TV_KNOB_BULK="other", TMPDIR="/elsewhere", HEART2_X="next run"))
        self.assertTrue(ok, "a name read only in bulk, or a plumbing name, broke the facts: %s" % why)

    def test_an_absent_file_that_appears_breaks_it(self):
        self._breaks("tv/absent.flag", "tv/absent.flag", "")

    def test_a_module_that_would_shadow_an_import_breaks_it(self):
        self._breaks("import helper_fx", mkdir="helper_fx")

    def test_the_bytes_an_append_kept_break_it(self):
        self._breaks("tv/log.txt", "tv/log.txt", "OLD log\n")

    def test_what_the_run_made_and_left_is_not_held(self):
        _write(self.root, "tv/made.txt", "any bytes at all\n")
        self.addCleanup(_gone, self.root, "tv/made.txt")
        ok, why = self._holds()
        self.assertTrue(ok, "a file the run made itself became a fact: %s" % why)

    def test_a_file_the_run_found_absent_and_made_breaks_it_when_there(self):
        """REG-2449 - exists() said no and the run created it: a later tree that already holds the file (another
        checkout's, an older run's) is not the tree the run decided on - there it takes the other branch."""
        self.assertIn("tv/state.json", self.rec["A"], "the absence the run found before it made the file is no fact")
        self._breaks("tv/state.json exists now", "tv/state.json", '{"stale": true}')

    def test_an_append_onto_nothing_holds_the_absence(self):
        self._breaks("tv/fresh.log exists now", "tv/fresh.log", "an older log\n")

    def test_a_mkdir_and_an_exclusive_create_looked_first(self):
        self._breaks("tv/made_dir exists now", mkdir=os.path.join("tv", "made_dir"))
        self._breaks("tv/excl.txt exists now", "tv/excl.txt", "already here\n")

    def test_a_folder_the_run_wrote_into_must_still_be_a_folder(self):
        here, away = os.path.join(self.root, "tv", "outbox"), os.path.join(self.root, "tv", "outbox.away")
        os.rename(here, away)
        self.addCleanup(os.rename, away, here)
        ok, why = self._holds()
        self.assertFalse(ok, "the folder the run wrote a file into is gone and the facts still held")
        self.assertIn("tv/outbox", why or "")

    def test_another_version_or_an_attested_chrome_never_holds(self):
        self.assertFalse(GL.facts_hold(self.root, dict(self.rec, v=0), _base_env())[0])
        rec = dict(self.rec, C=["started chrome, a Chrome this run started for its pages"])
        ok, why = GL.facts_hold(self.root, rec, _base_env())
        self.assertFalse(ok, "a run with an attested Chrome held by default")
        self.assertTrue(GL.facts_hold(self.root, rec, _base_env(), allow_cdp_chrome=True)[0])


# ── a denied root, an allowed folder inside it, and strict mode ────────────────────────────────────────────────────────
class AReadNoKeyCanNameIsUntraced(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="deny-root.")
        self.real = tempfile.mkdtemp(prefix="deny-real.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.addCleanup(shutil.rmtree, self.real, True)
        _write(self.root, "tv/data.txt", "hello\n")
        _write(self.real, "secret.txt", "the real checkout\n")
        _write(self.real, "allowed/ok.txt", "the run's own temp\n")

    def _run(self, body, **kw):
        _write(self.root, "tv/t_deny.py", "import os, subprocess, sys\nREAL = %r\n%s\nprint('ok')\n" % (self.real, body))
        proc, _facts, why = _traced(self.root, "t_deny.py", **kw)
        self.assertEqual(proc.returncode, 0, "PREMISE: the fixture law failed: %s" % proc.stderr[-600:])
        return why

    def test_an_open_a_listing_and_a_stat_under_a_denied_root_untrace_it(self):
        for body in ("open(os.path.join(REAL, 'secret.txt')).read()", "os.listdir(REAL)",
                     "os.path.exists(os.path.join(REAL, 'secret.txt'))"):
            why = self._run(body, deny=[self.real])
            self.assertIn("under a root no key of this run can name", why or "", "%s was dropped silently" % body)

    def test_an_allowed_folder_inside_a_denied_root_is_read_freely(self):
        why = self._run("open(os.path.join(REAL, 'allowed', 'ok.txt')).read()", deny=[self.real],
                        allow=[os.path.join(self.real, "allowed")])
        self.assertIsNone(why, "the run's own allowed temp folder untraced it: %s" % why)

    def test_a_path_outside_every_denied_root_is_dropped_as_before(self):
        why = self._run("open(os.path.join(REAL, 'secret.txt')).read()")
        self.assertIsNone(why, "with no denied root a read outside the checkout untraced the run: %s" % why)

    @unittest.skipUnless(_HAVE_GIT, "no git on PATH - the git-child case cannot run here")
    def test_a_git_child_aimed_at_a_denied_root_untraces_it(self):
        why = self._run("subprocess.run(['git', '-C', REAL, 'rev-parse', '--show-toplevel'], capture_output=True, "
                        "env=dict((k, v) for k, v in os.environ.items() if not k.upper().startswith('GIT_')))",
                        deny=[self.real])
        self.assertIn("under a root no key of this run can name", why or "")

    @unittest.skipUnless(_POSIX, "a symlinked folder needs POSIX here")
    def test_a_denied_root_reached_through_a_symlinked_folder_is_denied(self):
        alias = tempfile.mkdtemp(prefix="deny-alias.")
        self.addCleanup(shutil.rmtree, alias, True)
        link = os.path.join(alias, "to_real")
        os.symlink(self.real, link)
        why = self._run("open(os.path.join(%r, 'secret.txt')).read()" % link, deny=[self.real])
        self.assertIn("under a root no key of this run can name", why or "", "a symlinked alias escaped the deny")

    def test_strict_untraces_sqlite3_and_a_time_read_under_the_root(self):
        why = self._run("import sqlite3", strict=True)
        self.assertIn("imported sqlite3", why or "", "sqlite3 under STRICT stayed traced")
        why = self._run("import sqlite3")
        self.assertIsNone(why, "sqlite3 untraced a run that was not STRICT: %s" % why)
        why = self._run("os.path.getmtime(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.txt'))",
                        strict=True)
        self.assertIn("read the mtime of tv/data.txt", why or "", "getmtime under the root stayed traced")
        why = self._run("os.path.getctime(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.txt'))",
                        strict=True)
        self.assertIn("read the ctime of tv/data.txt", why or "")
        why = self._run("os.path.getmtime(sys.executable)", strict=True)
        self.assertIsNone(why, "a time read outside the root untraced the run: %s" % why)


# ── the tracked set and the .gitignores ────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(_HAVE_GIT, "no git on PATH - the tracked-set cases cannot run here")
class TheTrackedSetAndTheGitignoresAreFacts(unittest.TestCase):
    def setUp(self):
        # facts_of / facts_hold ask git in THIS process: no GIT_* of a hook may point them at another repository
        held = dict((k, v) for k, v in os.environ.items() if str(k).upper().startswith("GIT_"))
        for k in held:
            os.environ.pop(k, None)
        self.addCleanup(os.environ.update, held)
        self.root = tempfile.mkdtemp(prefix="facts-git.")
        self.addCleanup(shutil.rmtree, self.root, True)
        _write(self.root, "tv/a.txt", "a\n")
        _write(self.root, ".gitignore", "*.log\n")
        self.env = _git_free(os.environ)
        self._git("init", "-q")
        self._git("add", "-A")
        self._git("-c", "user.email=law@fixture", "-c", "user.name=law", "commit", "-q", "-m", "fixture")
        _write(self.root, "tv/t_git.py",
               "import os, subprocess\nE = dict((k, v) for k, v in os.environ.items() if not k.upper().startswith('GIT_'))\n"
               "R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\n"
               "subprocess.run(['git', 'ls-files', '-z', '--', '*.txt'], cwd=R, env=E, capture_output=True, check=True)\n"
               "subprocess.run(['git', 'check-ignore', '-q', 'tv/x.log'], cwd=R, env=E)\nprint('ok')\n")
        proc, facts, why = _traced(self.root, "t_git.py")
        self.assertEqual(proc.returncode, 0, "PREMISE: %s" % proc.stderr[-600:])
        self.assertIsNone(why, "PREMISE: the git run was untraced: %s" % why)
        self.rec = GL.facts_of(self.root, facts)

    def _git(self, *args):
        return subprocess.run(["git", "-C", self.root] + list(args), env=self.env, capture_output=True, text=True,
                              check=True)

    def test_an_added_tracked_file_breaks_it(self):
        self.assertTrue(GL.facts_hold(self.root, self.rec)[0], "PREMISE: the identical repo does not hold")
        self.assertTrue(self.rec.get("T"), "git ls-files wrote no tracked-set fact")
        _write(self.root, "tv/b.txt", "b\n")
        self._git("add", "tv/b.txt")
        ok, why = GL.facts_hold(self.root, self.rec)
        self.assertFalse(ok, "a new tracked file the run's ls-files would list left the facts holding")
        self.assertIn("git ls-files", why or "")

    def test_a_gitignore_edit_breaks_it(self):
        self.assertIn(".gitignore", self.rec.get("G") or {}, "git check-ignore kept no .gitignore fact")
        _write(self.root, ".gitignore", "*.tmp\n")
        ok, why = GL.facts_hold(self.root, self.rec)
        self.assertFalse(ok, "a .gitignore edit left a check-ignore run's facts holding")
        self.assertIn(".gitignore", why or "")


# ── a second boot in one process (REG-2448) ────────────────────────────────────────────────────────────────────────────
class ASecondBootArmsTheEnvironmentOnce(unittest.TestCase):
    """REG-2448 - two copies of the hook chaining into each other boot it ~160 times in one process (the boot that
    TRACE-CHAIN-ONCE stops, and test_a_killed_run_is_never_a_red's sabotage of it). Each boot re-read the whole trace,
    wrote the N block again and stacked one more environment layer, so that sabotage ran past its 120 s timeout instead
    of failing in a second - its red-proof could only read UNPROVABLE. A second boot keeps its own B line (the line that
    law counts) and arms the environment facts no second time."""

    def test_a_second_boot_writes_one_N_block_and_one_E_fact_per_read(self):
        root = tempfile.mkdtemp(prefix="facts-reboot.")
        self.addCleanup(shutil.rmtree, root, True)
        hook = os.path.join(HERE, "gate_trace", "sitecustomize.py")
        _write(root, "tv/t_reboot.py", "import os, runpy\nrunpy.run_path(%r, run_name='sitecustomize_again')\n"
                                       "os.environ['TV_KNOB_A']\nprint('ok')\n" % hook)
        trace = GL.trace_path()
        self.addCleanup(lambda: os.path.exists(trace) and os.remove(trace))
        env = GL.trace_env(_git_free(dict(os.environ, TV_KNOB_A="alpha")), root, trace)
        proc = subprocess.run([sys.executable, os.path.join(root, "tv", "t_reboot.py")], cwd=root, env=env,
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(proc.returncode, 0, "PREMISE: the fixture failed: %s" % proc.stderr[-600:])
        with io.open(trace, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        self.assertEqual(len([ln for ln in lines if ln.startswith("B\t")]), 2,
                         "PREMISE: the hook did not boot twice in the fixture's process")
        n_block = [ln for ln in lines if ln.startswith("N\t") and ln.endswith(" TV_KNOB_A")]
        e_facts = [ln for ln in lines if ln.startswith("E\t") and ln.endswith(" TV_KNOB_A")]
        self.assertEqual(len(n_block), 1, "a second boot read the trace again and wrote the N block again")
        self.assertEqual(len(e_facts), 1, "a second boot stacked an environment layer: one read wrote %d E lines"
                         % len(e_facts))


# ── pathlib (REG-2446) ─────────────────────────────────────────────────────────────────────────────────────────────────
class APathlibProbeIsAFact(unittest.TestCase):
    """REG-2446 - python 3.9/3.10's pathlib copies os.stat/os.lstat into its accessor when it is imported. On his Mac a
    user site-packages .pth imports pathlib before the hook, so Path.stat()/.exists()/.is_symlink() wrote no S, A or Z;
    a python that imports pathlib only later (-s: no user site) copied the wrapper, which bound as a method and raised
    TypeError on every Path.stat(). Both ways are driven; on 3.11+ pathlib asks os.stat at call time and both hold."""

    def _run(self, flags):
        root = tempfile.mkdtemp(prefix="facts-pathlib.")
        self.addCleanup(shutil.rmtree, root, True)
        _write(root, "tv/sized.txt", "four")
        _write(root, "tv/t_pathlib.py",
               "import os, pathlib\nH = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))\n"
               "print((H / 'sized.txt').stat().st_size, (H / 'absent.flag').exists(), (H / 'sized.txt').is_symlink())\n")
        return _traced(root, "t_pathlib.py", argv0=[sys.executable] + list(flags))

    def test_a_pathlib_stat_exists_and_lstat_are_facts(self):
        for flags in ((), ("-s",)):
            proc, facts, why = self._run(flags)
            self.assertEqual(proc.returncode, 0, "a traced Path.stat() raised (python %s): %s"
                             % (" ".join(flags) or "with its user site", proc.stderr[-600:]))
            self.assertIsNone(why, "PREMISE: the pathlib run was untraced: %s" % why)
            self.assertEqual(facts["Z"].get("tv/sized.txt"), {"f": "4", "F": "4"},
                             "Path.stat()/.is_symlink() kept no size fact (python %s)" % (" ".join(flags) or "-"))
            self.assertIn("tv/absent.flag", facts["A"], "Path.exists() of an absent file wrote no A fact")


# ── a name gone mid-listing (REG-2449) ─────────────────────────────────────────────────────────────────────────────────
class _Vanishing(object):
    """os.scandir whose every entry is gone by the time it is stat'ed (a name deleted mid-listing), made on demand."""

    def __init__(self, real):
        self.real = real

    def __call__(self, path="."):
        return _VanishingIt(self.real(path))


class _VanishingIt(object):
    def __init__(self, it):
        self.it = it

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.it.close()

    def __iter__(self):
        for e in self.it:
            yield _GoneEntry(e.name)


class _GoneEntry(object):
    def __init__(self, name):
        self.name = name

    def stat(self, follow_symlinks=True):
        raise FileNotFoundError(2, "gone mid-listing", self.name)


_VANISH_CHILD = r"""import os
class Gone(object):
    def __init__(self, name):
        self.name = name
    def stat(self, follow_symlinks=True):
        raise FileNotFoundError(2, 'gone mid-listing', self.name)
class It(object):
    def __init__(self, it):
        self.it = it
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        self.it.close()
    def __iter__(self):
        return (Gone(e.name) for e in self.it)
real = os.scandir
os.scandir = lambda path='.': It(real(path))
os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'box'))
print('ok')
"""


class ANameGoneMidListingIsNoAnswer(unittest.TestCase):
    """REG-2449 - the folder IS there; one of its names vanished between the listing and its stat. Before, that
    FileNotFoundError fell through to the folder's own `-`: the listing read as "absent", and a later tree where the
    folder really is absent held it."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="facts-vanish.")
        self.addCleanup(shutil.rmtree, self.root, True)
        _write(self.root, "tv/box/a.txt", "a\n")

    def test_the_checks_digest_says_unknown(self):
        real = os.scandir
        os.scandir = _Vanishing(real)
        try:
            got = GL._listing_digest(self.root, "tv/box")
        finally:
            os.scandir = real
        self.assertEqual(got, "?", "a name gone mid-listing read as %r - the folder is there" % got)

    def test_the_traced_listing_says_unknown(self):
        # the hook measures its D through os.scandir: in the child every name it finds is gone by its stat
        _write(self.root, "tv/t_vanish.py", _VANISH_CHILD)
        proc, facts, why = _traced(self.root, "t_vanish.py")
        self.assertEqual(proc.returncode, 0, "PREMISE: %s" % proc.stderr[-600:])
        self.assertIsNone(why, "PREMISE: the run was untraced: %s" % why)
        self.assertEqual(facts["D"].get("tv/box"), "?", "the hook's listing of a folder whose name vanished said %r"
                         % facts["D"].get("tv/box"))


# ── the node twin ──────────────────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(_HAVE_NODE, "no node on PATH - the node twin cannot run here")
class ANodeChildWritesTheSameFacts(unittest.TestCase):
    def test_a_node_read_its_spread_and_its_stat(self):
        root = tempfile.mkdtemp(prefix="facts-node.")
        self.addCleanup(shutil.rmtree, root, True)
        _write(root, "tv/sized.txt", "four")
        _write(root, "tv/t_node.js",
               "const fs = require('fs'); const path = require('path');\n"
               "process.env.TV_KNOB_A; process.env.TV_KNOB_B; const all = {...process.env}; Object.entries(process.env);\n"
               "fs.statSync(path.join(__dirname, 'sized.txt')); fs.readFileSync(path.join(__dirname, 'sized.txt'));\n"
               "console.log('ok');\n")
        proc, facts, why = _traced(root, "t_node.js", env_extra=dict(TV_KNOB_A="alpha", TV_KNOB_BULK="bulk"),
                                   argv0=["node"])
        self.assertEqual(proc.returncode, 0, "PREMISE: %s" % proc.stderr[-600:])
        self.assertIsNone(why, "PREMISE: the node run was untraced: %s" % why)
        self.assertEqual(facts["E"].get("TV_KNOB_A"), _sha("alpha"), "node's process.env.X wrote no fact")
        self.assertEqual(facts["E"].get("TV_KNOB_B"), "-")
        self.assertNotIn("TV_KNOB_BULK", facts["E"], "a node spread became a single-name fact")
        self.assertEqual(facts["Z"].get("tv/sized.txt"), {"F": "4"}, "node's stat kept no size")
        self.assertEqual(facts["H"].get("tv/sized.txt"), _sha("four"), "node's read kept no bytes")

    def test_a_node_listing_is_held_as_listed_and_a_node_write_that_looked_holds_the_absence(self):
        """REG-2449 - a node child's readdir wrote L and no D, so the ledger's per-tree facts never held what it saw;
        and its mkdirSync / 'wx' / writeFile({flag: 'a'}) read as made without looking."""
        root = tempfile.mkdtemp(prefix="facts-node-made.")
        self.addCleanup(shutil.rmtree, root, True)
        _write(root, "tv/box/a.txt", "aaa")
        _write(root, "tv/box/sub/b.txt", "b")
        if _POSIX:
            os.symlink("a.txt", os.path.join(root, "tv", "box", "ln"))
        _write(root, "tv/t_made.js",
               "const fs = require('fs'); const path = require('path'); const j = (...a) => path.join(__dirname, ...a);\n"
               "fs.readdirSync(j('box'));\n"
               "fs.mkdirSync(j('made_dir'));\n"
               "fs.closeSync(fs.openSync(j('excl.txt'), 'wx'));\n"
               "fs.writeFileSync(j('fresh.log'), 'x', {flag: 'a'});\n"
               "fs.writeFileSync(j('blind.txt'), 'x');\n"
               "console.log('ok');\n")
        listed = GL._listing_digest(root, "tv/box")
        proc, facts, why = _traced(root, "t_made.js", argv0=["node"])
        self.assertEqual(proc.returncode, 0, "PREMISE: %s" % proc.stderr[-600:])
        self.assertIsNone(why, "PREMISE: the node run was untraced: %s" % why)
        self.assertEqual(facts["D"].get("tv/box"), listed, "a node listing is not held as python's digest holds it")
        for rel in ("tv/made_dir", "tv/excl.txt", "tv/fresh.log"):
            self.assertIn(rel, facts["MA"], "node's write of %s found it absent and reads as made without looking" % rel)
        self.assertNotIn("tv/blind.txt", facts["MA"], "a truncating write looked at nothing and became an absence fact")
        self.assertIn("tv/blind.txt", facts["M"])

    def test_a_recursive_listing_and_fs_cp_untrace_the_run(self):
        root = tempfile.mkdtemp(prefix="facts-node-u.")
        self.addCleanup(shutil.rmtree, root, True)
        _write(root, "tv/box/a.txt", "aaa")
        for body, said in (("fs.readdirSync(__dirname, {recursive: true});", "listed a folder recursively"),
                           ("fs.cpSync(path.join(__dirname, 'box'), path.join(__dirname, 'box2'), {recursive: true});",
                            "copied with fs.cp")):
            _write(root, "tv/t_u.js", "const fs = require('fs'); const path = require('path');\n%s\n" % body)
            proc, facts, why = _traced(root, "t_u.js", argv0=["node"])
            self.assertEqual(proc.returncode, 0, "PREMISE: %s" % proc.stderr[-600:])
            self.assertIn(said, why or "", "node's %s stayed traced" % body)


RED_PROOF = [
    {"why": "a read under a denied root is dropped silently", "file": "gate_trace/sitecustomize.py",
     "find": "        if deny and denied(path):\n", "replace": "        if False and deny and denied(path):\n",
     "matches": 1},
    {"why": "an allowed folder inside a denied root untraces the run", "file": "gate_trace/sitecustomize.py",
     "find": "        if allow and any(under(f, allow) for f in forms):\n",
     "replace": "        if False:\n", "matches": 1},
    {"why": "a denied root reached through a symlinked folder escapes the deny", "file": "gate_trace/sitecustomize.py",
     "find": "        forms = (normcase(path), normcase(join(real, tail)))\n",
     "replace": "        forms = (normcase(path),)\n", "matches": 1, "needs": "posix"},
    {"why": "no E fact is written", "file": "gate_trace/sitecustomize.py",
     "find": "            emit(\"E\", \"%s %s\" % (d, name))  # TRACE-ENV-FACT\n",
     "replace": "            pass  # TRACE-ENV-FACT\n", "matches": 1},
    {"why": "a bulk copy of the environment writes a fact per name", "file": "gate_trace/sitecustomize.py",
     "find": "            bulk = f is not None and (f.f_code in views or (mark is not None and mark[0] == id(f)\n",
     "replace": "            bulk = False and (f.f_code in views or (mark is not None and mark[0] == id(f)\n",
     "matches": 1},
    {"why": "a value the run made is a fact of the child that read it", "file": "gate_trace/sitecustomize.py",
     "find": "                return  # the run made this value: the process that made it holds the fact  # TRACE-ENV-MADE\n",
     "replace": "                pass  # TRACE-ENV-MADE\n", "matches": 1},
    {"why": "the prover's plumbing names are facts", "file": "gate_trace/sitecustomize.py",
     "find": "    return u in _PLUMBING or u.startswith(_PLUMBING_PREFIXES)\n",
     "replace": "    return False\n", "matches": 1},
    {"why": "a stat keeps presence only, no size", "file": "gate_trace/sitecustomize.py",
     "find": "        size = (\"%d\" % st.st_size) if kind == \"f\" else \"-\"\n",
     "replace": "        size = \"-\"\n", "matches": 1},
    {"why": "STRICT lets sqlite3 through", "file": "gate_trace/sitecustomize.py",
     "find": "                if strict and name in _STRICT_MODULES:\n", "replace": "                if False:\n",
     "matches": 1},
    {"why": "STRICT lets a time read under the root through", "file": "gate_trace/sitecustomize.py",
     "find": "                        emit(\"U\", \"read the %s of %s, which a copy of the tree does not keep\" % (what, r))"
             "  # TRACE-STRICT-TIME\n",
     "replace": "                        pass  # TRACE-STRICT-TIME\n", "matches": 1},
    {"why": "a write that keeps the bytes it finds (append) measures nothing", "file": "gate_trace/sitecustomize.py",
     "find": "                if not writes or not making:\n", "replace": "                if not writes:\n", "matches": 1},
    {"why": "a listing is measured after the run, not as it was listed", "file": "gate_trace/sitecustomize.py",
     "find": "                    listing_fact(r)\n", "replace": "                    pass\n", "matches": 1},
    {"why": "git ls-files writes no tracked-set fact", "file": "gate_trace/sitecustomize.py",
     "find": "            emit(\"T\", \"\\x1f\".join([\"?\" if odd else \"=\", at] + [o for o in opts if not o.startswith(\"-\")]))"
             "  # TRACE-TRACKED-SET\n",
     "replace": "            pass  # TRACE-TRACKED-SET\n", "matches": 1},
    {"why": "the reader accepts an attested Chrome by default", "file": "gate_ledger.py",
     "find": "        if kind == \"C\" and allow_cdp_chrome:  # LEDGER-CDP-ATTESTED\n",
     "replace": "        if kind == \"C\":  # LEDGER-CDP-ATTESTED\n", "matches": 1},
    {"why": "a size measured after the run wrote the path is kept", "file": "gate_ledger.py",
     "find": "            if len(bits) == 3 and bits[2] not in wrote:  # LEDGER-SIZE-FACT\n",
     "replace": "            if len(bits) == 3:  # LEDGER-SIZE-FACT\n", "matches": 1},
    {"why": "facts_hold ignores the bytes", "file": "gate_ledger.py",
     "find": "        if d == \"?\" or _fact_bytes(root, p) != d:\n", "replace": "        if d == \"?\":\n", "matches": 1},
    {"why": "facts_hold ignores a size", "file": "gate_ledger.py",
     "find": "            if now != (kind, size):  # FACTS-SIZE\n", "replace": "            if False:  # FACTS-SIZE\n",
     "matches": 1},
    {"why": "facts_hold ignores a listing", "file": "gate_ledger.py",
     "find": "        if d == \"?\" or _listing_digest(root, p) != d:\n", "replace": "        if d == \"?\":\n",
     "matches": 1},
    {"why": "facts_hold ignores the environment", "file": "gate_ledger.py",
     "find": "        if d == \"?\" or _env_digest(env, name) != d:\n", "replace": "        if d == \"?\":\n", "matches": 1},
    {"why": "facts_hold ignores a file that appeared", "file": "gate_ledger.py",
     "find": "        if os.path.lexists(_fact_path(root, p)):\n", "replace": "        if False:\n", "matches": 1},
    {"why": "facts_hold ignores a module that would shadow an import", "file": "gate_ledger.py",
     "find": "        if now_homes.get(name) != was:\n", "replace": "        if False:\n", "matches": 1},
    {"why": "facts_hold ignores the tracked set", "file": "gate_ledger.py",
     "find": "        if d == \"?\" or _tracked_scope(root, scope) != d:\n", "replace": "        if d == \"?\":\n",
     "matches": 1},
    {"why": "the node twin writes no E fact", "file": "gate_trace/node_trace.cjs",
     "find": "    emit('E', d + ' ' + name);  // TRACE-ENV-FACT\n", "replace": "    // TRACE-ENV-FACT\n",
     "matches": 1, "needs": "node"},
    {"why": "the node twin keeps no size", "file": "gate_trace/node_trace.cjs",
     "find": "    emit('Z', sizeOf(st, false) + ' ' + r);  // TRACE-SIZE-FACT\n", "replace": "    // TRACE-SIZE-FACT\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2448 - every boot of the hook in one process re-reads the trace and writes the N block again",
     "file": "gate_trace/sitecustomize.py",
     "find": "    first_env = out not in booted  # TRACE-ENV-ONCE\n", "replace": "    first_env = True  # TRACE-ENV-ONCE\n",
     "matches": 1},
    {"why": "REG-2448 - every boot of the hook in one process stacks another environment layer",
     "file": "gate_trace/sitecustomize.py",
     "find": "        if cls is None or getattr(cls.__getitem__, \"_tv_gate_env\", False):  # TRACE-ENV-ARMED-ONCE\n",
     "replace": "        if cls is None:  # TRACE-ENV-ARMED-ONCE\n", "matches": 1},
    {"why": "REG-2447 - a stat under a file (ENOTDIR) writes no absence", "file": "gate_trace/sitecustomize.py",
     "find": "            except (FileNotFoundError, NotADirectoryError):\n",
     "replace": "            except FileNotFoundError:\n", "matches": 1, "needs": "posix"},
    # REG-2446 - judged on macOS: his Mac's python (3.9) is the one host here whose pathlib copies os.stat into its
    # accessor; a 3.11+ python (CI, the Windows PCs) asks os.stat at call time, so there these change nothing
    {"why": "REG-2446 - pathlib's accessor keeps the real os.stat, so a Path probe writes no fact",
     "file": "gate_trace/sitecustomize.py",
     "find": "                setattr(pl_acc, _n, staticmethod(getattr(os, _n)))  # TRACE-PATHLIB-ACCESSOR\n",
     "replace": "                pass  # TRACE-PATHLIB-ACCESSOR\n", "matches": 1, "needs": "macos"},
    {"why": "REG-2446 - pathlib is not imported before the wrap, so a python that loads it later copies the wrapper "
            "and every traced Path.stat() raises", "file": "gate_trace/sitecustomize.py",
     "find": "            import pathlib as _pl\n", "replace": "            _pl = sys.modules.get(\"pathlib\")\n",
     "matches": 1, "needs": "macos"},
    # REG-2449 - what the run made is held where it found something first
    {"why": "REG-2449 - facts_of drops the absence of a file the run found absent and then made", "file": "gate_ledger.py",
     "find": "    rec[\"A\"] = sorted((set(facts.get(\"A\") or ()) - made) | found_absent)\n",
     "replace": "    rec[\"A\"] = sorted(set(facts.get(\"A\") or ()) - made)\n", "matches": 1},
    {"why": "REG-2449 - an exclusive create ('x') reads as made without looking", "file": "gate_trace/sitecustomize.py",
     "find": "                making = (isinstance(mode, str) and \"w\" in mode) or (mode is None and isinstance(flags, int) and "
             "bool(\n",
     "replace": "                making = (isinstance(mode, str) and any(c in mode for c in \"wx\")) or (mode is None and "
                "isinstance(flags, int) and bool(\n", "matches": 1},
    {"why": "REG-2449 - a mkdir writes no look before it makes the folder", "file": "gate_trace/sitecustomize.py",
     "find": "                    looked(r)  # REG-2449 - each fails on a path that is there, so it looked first  "
             "# TRACE-LOOKED-FIRST\n",
     "replace": "                    pass  # TRACE-LOOKED-FIRST\n", "matches": 1},
    {"why": "REG-2449 - the folder a made file was written into is no fact", "file": "gate_ledger.py",
     "find": "            rec[\"Z\"].setdefault(folder, {}).setdefault(kind, size)\n", "replace": "            pass\n",
     "matches": 1},
    {"why": "REG-2449 - the check reads a name gone mid-listing as the folder being absent", "file": "gate_ledger.py",
     "find": "                    return \"?\"  # REG-2449 - a name gone mid-listing is no answer, never \"the folder is "
             "absent\"\n",
     "replace": "                    raise\n", "matches": 1},
    {"why": "REG-2449 - the hook reads a name gone mid-listing as the folder being absent",
     "file": "gate_trace/sitecustomize.py",
     "find": "                        rows = None  # REG-2449 - a name gone mid-listing is no answer, never \"the folder is "
             "absent\"\n",
     "replace": "                        raise\n", "matches": 1},
    {"why": "REG-2449 - a node listing writes no D", "file": "gate_trace/node_trace.cjs",
     "find": "    emit('D', d + ' ' + r);  // TRACE-LISTING-FACT\n", "replace": "    // TRACE-LISTING-FACT\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2449 - node's mkdirSync writes no look before it makes the folder", "file": "gate_trace/node_trace.cjs",
     "find": "  const looked = (p) => { S(p); W(p); };  // TRACE-LOOKED-FIRST\n",
     "replace": "  const looked = (p) => { W(p); };  // TRACE-LOOKED-FIRST\n", "matches": 1, "needs": "node"},
    {"why": "REG-2449 - node's 'wx' open reads as made without looking", "file": "gate_trace/node_trace.cjs",
     "find": "  const keeps = (flags) => (typeof flags === 'string' ? (/x/.test(flags) || !/w/.test(flags))\n",
     "replace": "  const keeps = (flags) => (typeof flags === 'string' ? !/[wx]/.test(flags)\n", "matches": 1,
     "needs": "node"},
    {"why": "REG-2449 - node's writeFile ignores its flag, so an append onto nothing reads as made without looking",
     "file": "gate_trace/node_trace.cjs",
     "find": "  for (const n of ['writeFileSync', 'writeFile']) wrap(fs, n, (p, data, opts) => wrote(p, flagOf(opts, 'flag', "
             "'w')));\n",
     "replace": "  for (const n of ['writeFileSync', 'writeFile']) wrap(fs, n, (p, data, opts) => wrote(p, 'w'));\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2449 - a recursive node listing stays traced", "file": "gate_trace/node_trace.cjs",
     "find": "      if (rel(p) !== null) emit('U', 'listed a folder recursively (no one D names what it read)');  "
             "// TRACE-RECURSIVE\n",
     "replace": "      // TRACE-RECURSIVE\n", "matches": 1, "needs": "node"},
    {"why": "REG-2449 - node's fs.cp stays traced", "file": "gate_trace/node_trace.cjs",
     "find": "    if (rel(a) !== null || rel(b) !== null) emit('U', 'copied with fs.cp (its reads and writes reach no "
             "wrapped call)');\n",
     "replace": "    // fs.cp\n", "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=1)
