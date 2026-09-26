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


_REMOVER = ("rmtree", "clean", "remove", "unlink", "rmdir")
_REGISTRARS = ("addCleanup", "register")


def _removes(fn):
    """Is this callable a remover? A name (shutil.rmtree, _clean_scratch) or a lambda whose body calls one."""
    if isinstance(fn, ast.Lambda):
        return any(isinstance(c, ast.Call) and any(k in (_name(c) or "").lower() for k in _REMOVER)
                   for c in ast.walk(fn.body))
    n = fn.attr if isinstance(fn, ast.Attribute) else (fn.id if isinstance(fn, ast.Name) else "")
    return any(k in (n or "").lower() for k in _REMOVER)


def _cleans(node):
    """Does this function remove what it made? ⚠ 2026-09-26 (the #231 eye on v3508): `addCleanup` / `atexit.register`
    counted by NAME, so `self.addCleanup(lambda: None)` in a setUp vouched for every mkdtemp in the class. A registrar
    counts only when what it registers REMOVES something; a direct rmtree / cleanup call counts as before."""
    for c in ast.walk(node):
        if not isinstance(c, ast.Call):
            continue
        nm = _name(c) or ""
        if nm in _REGISTRARS:
            if c.args and _removes(c.args[0]):
                return True
            continue
        if nm in CLEAN or "clean" in nm.lower():
            return True
    return False


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
        # #243 - the CLASS pairs a site only through its fixture methods. Walking the whole class let ANY cleanup
        # anywhere in it vouch for every site: test_provenance's two bare mkdtemp()s leaked 83 dirs a day while
        # an unrelated cleanup elsewhere in their class kept this finder green.
        _fix = [m for m in (cls.body if cls is not None else [])
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                and m.name in ("setUp", "tearDown", "setUpClass", "tearDownClass", "asyncSetUp", "asyncTearDown")]
        if (fn is not None and _cleans(fn)) or any(_cleans(m) for m in _fix):
            continue
        out.append(n.lineno)
    return out


def _contains_at_module_level(path):
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    return any(isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
               and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == "contain"
               for n in tree.body)


MAKERS = ("mkdtemp", "mkstemp", "TemporaryDirectory", "NamedTemporaryFile")


def made_before_contain(path):
    """Top-level statements that make a temp path BEFORE the module's contain() runs. -> [lineno]

    A path made first lands in the real temp dir, outside the parent contain() removes at exit - the
    cross-family eye found test_gate_cache doing exactly that while the law above stayed green, because
    it asked only whether contain() appears. A statement counts when it calls a maker directly, or
    calls a module-level function whose body does (test_control's census file is made that way)."""
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    makes = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
             and any(isinstance(c, ast.Call) and _name(c) in MAKERS for c in ast.walk(n))}
    out = []
    for n in tree.body:
        if (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == "contain"):
            return out
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if any(isinstance(c, ast.Call) and (_name(c) in MAKERS or _name(c) in makes) for c in ast.walk(n)):
            out.append(n.lineno)
    return []          # never contained: the case above owns that question


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

    def test_an_unrelated_cleanup_in_the_class_does_not_pair_a_site(self):
        """#243 - the finder walked the WHOLE class, so any cleanup anywhere in it paired every site: test_provenance's two
        bare mkdtemp()s leaked 83 dirs a day behind an unrelated cleanup. Only the site's own function, or the class's
        fixture methods (setUp / tearDown / ...Class), pair it."""
        src = ("import tempfile, shutil, unittest\n"
               "class T(unittest.TestCase):\n"
               "    def test_a(self):\n"
               "        d = tempfile.mkdtemp()\n"                      # line 4: leaks
               "    def test_b(self):\n"
               "        e = tempfile.mkdtemp()\n"
               "        shutil.rmtree(e)\n"                            # its OWN cleanup, not test_a's
               "class U(unittest.TestCase):\n"
               "    def setUp(self):\n"
               "        self.addCleanup(lambda: None)\n"
               "    def test_c(self):\n"
               "        f = tempfile.mkdtemp()\n"                     # line 12: LEAKS - a no-op cleanup removes nothing
               "class V(unittest.TestCase):\n"
               "    def setUp(self):\n"
               "        self.d = tempfile.mkdtemp()\n"                # line 15: paired - its fixture registers rmtree
               "        self.addCleanup(shutil.rmtree, self.d, True)\n"
               "    def test_d(self):\n"
               "        g = tempfile.mkdtemp()\n"                     # line 19: paired by the same fixture
               "        self.addCleanup(lambda: shutil.rmtree(g, True))\n")
        tmp = tempfile.mkdtemp(prefix="unpaired-")
        self.addCleanup(shutil.rmtree, tmp, True)
        p = os.path.join(tmp, "t.py")
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(src)
        self.assertEqual(unpaired_sites(p), [4, 12], "a cleanup elsewhere in the class, or a no-op one (the #231 eye on "
                                                     "v3508: addCleanup(lambda: None)), vouched for a leaking site")

    def test_premise_the_finder_finds_the_two_big_suites(self):
        found = set(os.path.basename(p) for p in _tests() if unpaired_sites(p))
        for big in ("test_control.py", "test_agent.py"):
            self.assertIn(big, found, "the finder no longer sees %s's unpaired sites - it would miss a new one" % big)

    def test_every_file_with_an_unpaired_site_contains_its_run(self):
        bad = ["%s (%d site(s))" % (os.path.basename(p), len(u)) for p in _tests()
               for u in [unpaired_sites(p)] if u and not _contains_at_module_level(p)]
        self.assertEqual(bad, [], "these suites make scratch dirs they never remove and do not call "
                         "fixture_tmp.contain() at import: %r" % bad)

    def test_contain_runs_before_the_first_scratch_path(self):
        bad = ["%s:%s" % (os.path.basename(p), ",".join(map(str, early))) for p in _tests()
               for early in [made_before_contain(p)] if early]
        self.assertEqual(bad, [], "these suites make a scratch path before fixture_tmp.contain() runs, so it "
                         "lands outside the parent removed at exit: %r" % bad)

    def test_premise_the_order_finder_sees_a_path_made_first(self):
        import tempfile as _t
        fd, fx = _t.mkstemp(suffix=".py")
        os.close(fd)
        try:
            io.open(fx, "w", encoding="utf-8").write(
                "import tempfile\nimport fixture_tmp as _fx_tmp\n"
                "def _mk():\n    return tempfile.mkstemp()\n"
                "A = tempfile.mkdtemp()\nB = _mk()\n_fx_tmp.contain()\nC = tempfile.mkdtemp()\n")
            self.assertEqual(made_before_contain(fx), [5, 6], "the finder cannot see a direct maker or one "
                             "reached through a module function - the case above would pass on anything")
        finally:
            os.remove(fx)

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
        "why": "the #231 eye on v3508 - a registrar counts by NAME again: addCleanup(lambda: None) vouches for a leaking mkdtemp",
        "file": "test_a_test_run_leaves_no_scratch_dirs.py",
        "find": "            if c.args and _removes(c.args[0]):\n                return True\n            continue\n",
        "replace": "            return True\n",
        "matches": 1,
    },
    {
        "why": "#243 - any cleanup anywhere in a class pairs every site again (test_provenance leaked 83 dirs a day behind one)",
        "file": "test_a_test_run_leaves_no_scratch_dirs.py",
        "find": "        if (fn is not None and _cleans(fn)) or any(_cleans(m) for m in _fix):\n",
        "replace": "        if (fn is not None and _cleans(fn)) or (cls is not None and _cleans(cls)):\n",
        "matches": 1,
    },
    {
        "why": "#171 - test_gate_cache makes its scratch dir before contain() again: that dir leaks on every run",
        "file": "test_gate_cache.py",
        "find": "_fx_tmp.contain()\n_TMP = tempfile.mkdtemp(prefix=\"gatecache_\")\n",
        "replace": "_TMP = tempfile.mkdtemp(prefix=\"gatecache_\")\n_fx_tmp.contain()\n",
        "matches": 1,
    },
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
