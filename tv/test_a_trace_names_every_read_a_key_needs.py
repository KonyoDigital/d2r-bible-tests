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
  * gate_ledger.facts_of / facts_hold: an identical tree holds; one byte, one size, one listed name, one env value, an
    absent file that appears, a module that would now shadow an import, a kept-bytes (append) file, the tracked set
    and a .gitignore each break it. read_trace() still reads a C line exactly like U by default.
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
with open(os.path.join(HERE, 'log.txt'), 'a') as fh:
    fh.write('more\n')
with open(os.path.join(HERE, 'made.txt'), 'w') as fh:
    fh.write('mine\n')
open(os.path.join(HERE, 'made.txt')).read()
os.path.getsize(os.path.join(HERE, 'made.txt'))
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
    for rel in ("tv/sub/made_after.txt", "tv/made.txt"):
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
]

if __name__ == "__main__":
    unittest.main(verbosity=1)
