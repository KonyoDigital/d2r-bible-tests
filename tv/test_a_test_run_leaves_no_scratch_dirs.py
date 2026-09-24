# -*- coding: utf-8 -*-
"""#171 — A TEST RUN LEAVES NO SCRATCH DIRECTORIES BEHIND.

MEASURED 2026-09-24: 138 mkdtemp sites across 46 tv/test_*.py files had no teardown in their own
function or class, and his $TMPDIR held 6,574 bare tmp* dirs. fixture_tmp.contain() holds a test
process's scratch dirs inside one parent removed at exit; this law is the door.

  · COMPILER: every test file with an unpaired mkdtemp site calls fixture_tmp.contain() at MODULE level
    (a call inside a def may never run). PREMISE: the finder finds test_control and test_agent.
  · DRIVEN (a real child process): contain() then three unpaired mkdtemp -> nothing is left in the base.
    PREMISE: the same child WITHOUT contain() leaves its dirs - so the contained case can fail.
  · DRIVEN: the sweep removes a dead run's old parent and spares a live run's and a fresh one.
  · COMPILER: no production file imports fixture_tmp.
RED_PROOF below.
"""
import ast
import glob
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as FT  # noqa: E402

CLEAN = ("rmtree", "cleanup", "addCleanup", "register", "remove_tree")


def _name(c):
    f = c.func
    return f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)


def _cleans(node):
    return any(isinstance(c, ast.Call) and (_name(c) in CLEAN or "clean" in (_name(c) or "").lower())
               for c in ast.walk(node))


def unpaired_sites(path):
    """mkdtemp calls with no cleanup in their own function or in their class (setUp/tearDown). -> [lineno]"""
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    parent = {}
    for n in ast.walk(tree):
        for ch in ast.iter_child_nodes(n):
            parent[ch] = n
    out = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and _name(n) == "mkdtemp"):
            continue
        fn = cls = None
        p = parent.get(n)
        while p is not None:
            if fn is None and isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn = p
            if isinstance(p, ast.ClassDef):
                cls = p
                break
            p = parent.get(p)
        if (fn is not None and _cleans(fn)) or (cls is not None and _cleans(cls)):
            continue
        out.append(n.lineno)
    return out


def _contains_at_module_level(path):
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    return any(isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
               and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == "contain"
               for n in tree.body)


def _tests():
    return sorted(glob.glob(os.path.join(HERE, "test_*.py")))


CHILD = r"""
import os, sys, tempfile
sys.path.insert(0, %r)
if %r:
    import fixture_tmp
    fixture_tmp.contain()
for _ in range(3):
    tempfile.mkdtemp()          # unpaired, on purpose
"""


def _run_child(contained):
    base = tempfile.mkdtemp(prefix="fxtmp-law-")
    try:
        env = dict(os.environ, TMPDIR=base, TEMP=base, TMP=base)
        r = subprocess.run([sys.executable, "-c", CHILD % (HERE, contained)], env=env,
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise AssertionError("the child did not run - UNKNOWN, not passing: %s" % r.stderr[-400:])
        return sorted(os.listdir(base))
    finally:
        shutil.rmtree(base, ignore_errors=True)


class ATestRunLeavesNoScratchDirs(unittest.TestCase):

    def test_premise_the_finder_finds_the_two_big_suites(self):
        found = set(os.path.basename(p) for p in _tests() if unpaired_sites(p))
        for big in ("test_control.py", "test_agent.py"):
            self.assertIn(big, found, "the finder no longer sees %s's unpaired sites - it would miss a new one" % big)

    def test_every_file_with_an_unpaired_site_contains_its_run(self):
        bad = ["%s (%d site(s))" % (os.path.basename(p), len(u)) for p in _tests()
               for u in [unpaired_sites(p)] if u and not _contains_at_module_level(p)]
        self.assertEqual(bad, [], "these suites make scratch dirs they never remove and do not call "
                         "fixture_tmp.contain() at import: %r" % bad)

    def test_premise_an_uncontained_run_leaves_its_dirs(self):
        self.assertEqual(len(_run_child(False)), 3, "premise: an uncontained child should leave 3 dirs")

    def test_a_contained_run_leaves_nothing(self):
        self.assertEqual(_run_child(True), [], "a contained run left scratch dirs behind")

    def test_the_sweep_takes_only_a_dead_runs_old_parent(self):
        base = tempfile.mkdtemp(prefix="fxtmp-sweep-")
        try:
            dead = subprocess.Popen([sys.executable, "-c", "pass"])
            dead.wait()
            old = time.time() - FT.STALE_S - 60
            for name, when in (("%s%d-a" % (FT.PREFIX, dead.pid), old),          # dead + old -> swept
                               ("%s%d-b" % (FT.PREFIX, os.getppid()), old),      # alive (our parent) -> kept
                               ("%s%d-c" % (FT.PREFIX, dead.pid), time.time()),  # dead but fresh -> kept
                               ("tmpother", old)):                               # not ours -> kept
                os.mkdir(os.path.join(base, name))
                os.utime(os.path.join(base, name), (when, when))
            gone = FT.sweep_stale(base)
            self.assertEqual(gone, ["%s%d-a" % (FT.PREFIX, dead.pid)])
            self.assertEqual(sorted(os.listdir(base)),
                             sorted(["%s%d-b" % (FT.PREFIX, os.getppid()), "%s%d-c" % (FT.PREFIX, dead.pid), "tmpother"]))
        finally:
            shutil.rmtree(base, ignore_errors=True)

    def test_production_never_imports_it(self):
        bad = []
        for p in sorted(glob.glob(os.path.join(HERE, "*.py"))):
            b = os.path.basename(p)
            if b.startswith("test_") or b in ("fixture_tmp.py", "fixture_ledgers.py", "conftest.py"):
                continue
            tree = ast.parse(io.open(p, encoding="utf-8").read())
            for n in ast.walk(tree):
                if isinstance(n, ast.Import) and any(a.name == "fixture_tmp" for a in n.names):
                    bad.append(b)
                if isinstance(n, ast.ImportFrom) and n.module == "fixture_tmp":
                    bad.append(b)
        self.assertEqual(bad, [], "production code imports the test-only scratch container: %r" % bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#171 - test_control stops containing its run: its 35 unpaired scratch dirs leak on every gate again",
        "file": "test_control.py",
        "find": "_fx_tmp.contain()\n",
        "replace": "pass\n",
        "matches": 1,
    },
    {
        "why": "#171 - the container is never removed at exit: a contained run still leaves everything",
        "file": "fixture_tmp.py",
        "find": "    shutil.rmtree(d, ignore_errors=True)\n",
        "replace": "    pass\n",
        "matches": 1,
    },
    {
        "why": "#171 - the sweep ignores whether the owning run is alive: a live suite's scratch is deleted under it",
        "file": "fixture_tmp.py",
        "find": "        if age < stale_s or pid == os.getpid() or _alive(pid):\n",
        "replace": "        if age < stale_s or pid == os.getpid():\n",
        "matches": 1,
    },
]
