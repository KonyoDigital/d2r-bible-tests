#!/usr/bin/env python3
"""RUN THE SUITE AS A CI RUNNER SEES IT — no board, no footage, none of his history.

⚠ WHY THIS EXISTS. On 2026-08-28 the agent-tests workflow was found RED FOR TEN CONSECUTIVE RUNS,
since v2200, over a day and roughly thirty-five versions. Every one of those ships was green on his
Mac. Two tests in TestV2080TheExtractPruneCycleIsClosed asserted that the retention cycle DELETES,
and v2167 had made the deleter refuse on any board world that is not CONFIRMED. His board has been
recorded; a GitHub runner's never has. So the refusal was correct, the tests were wrong, and the
signal was invisible from here.

A gate that is always red carries exactly as much information as one that is always green, and both
train you to stop reading it. That is the failure this file is against.

WHAT IT DOES: neutralises the things a runner does not have, then runs the suite and reports which
tests depend on his machine. It does NOT modify any test — it only reveals.

⚠ IT IS NOT A REPLACEMENT FOR CI. It stubs the host dependencies we KNOW about. A test that leans on
something not listed in HOST_STUBS will still pass here and fail there — so a green run of this is
"none of the KNOWN host traps", never "CI will pass". Saying otherwise would make this the very kind
of over-claiming gate it exists to catch. [[unknown-stays-unknown]]

A HOST PROVIDES THREE KINDS OF THING, AND UNTIL v3425 THIS FILE COULD EXPRESS ONE.
  1. a python MODULE ATTRIBUTE      -> HOST_STUBS      (patchable; all three original entries)
  2. a PATH ON DISK                 -> HOST_PATHS      (stubbable ABSENT or NOT-EXECUTABLE)
  3. a PLATFORM FACT about this      -> PLATFORM_FACTS  (NOT stubbable - reported UNKNOWN)
     interpreter, kernel or CPU
Neither CI-vs-Mac disagreement found in the week of 2026-09-23 was kind 1, so this tool said
"no KNOWN host dependency" about both of them. Kind 3 has no fix and must not pretend to one:
**you cannot patch a Mac into being Linux**, so the answer there is UNKNOWN, never green.

EXIT CODES, and 3 is NOT a failure:
  0  ran, and nothing KNOWN to differ on a runner was touched
  1  ran, and something failed once the known host things were taken away
  2  NOTHING was simulated - a stub is inert, or the name could not be loaded. UNKNOWN.
  3  ran clean, but part of what ran turns on a platform fact no stub can neutralise, so the
     green is not earned. UNKNOWN, and deliberately distinct from 2 (which means "no run").
"""

import ast
import inspect
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))

# Each entry: (module, attribute, value a RUNNER would really see, why).
# Add to this list whenever CI disagrees with this Mac — the list IS the record of what his machine
# silently provides.
HOST_STUBS = (
    ("control_app", "board_identity_drift",
     lambda: {"state": "unknown", "why": "the board's world has never been recorded"},
     "a runner has never opened his board, so no world can be confirmed (v2167 refuses on this)"),
    ("control_app", "_tree_is_mid_edit",
     lambda *a, **k: (False, ""),
     "git working-tree state is the DEVELOPER's, not the code's: v2323 made auto-relaunch refuse "
     "while the tree is mid-edit (REG-400), which is right in production and a hidden input in a "
     "test. Unstubbed it passes on a clean checkout and fails on the machine of anyone actually "
     "editing the repo - CI green, his Mac red, for a reason that is not in the diff"),
    # ⚠⚠ v3319 — ADDED BECAUSE CI DISAGREED WITH HIS MAC FOR TEN CONSECUTIVE DEPLOYS AND THIS
    # SIMULATOR COULD NOT SEE IT. `slow_surface()` always returns len(SLOW) rows and emits
    # UNMEASURED when no full pass was ever stored ("NEVER, not missing"). His Mac has stored
    # passes so `the other doctors` reads ok; a runner never has, so it reads UNMEASURED — and
    # since v3293 the eagle buckets 'unknown' OR 'unmeasured'.
    # MEASURED by reproducing both worlds on the engine: slow=UNMEASURED -> unknown 2,
    # slow=ok -> unknown 1. That 2 failed `test_UNKNOWN_is_never_folded_into_all_clear` on every
    # Publish run, so THE LIVE SITE DID NOT DEPLOY ALL DAY while the code was correct throughout.
    # ⚠ The stub returns [] rather than an ok row ON PURPOSE: [] claims nothing about the slow
    # tier's health, it only removes the VENUE from the count. [[test-venue]]
    ("console_doctor", "slow_surface",
     lambda *a, **k: [],
     "slow_surface is a CACHED read of _load_slow, not a sub-doctor run, so patching run() never "
     "reaches it. On his Mac a stored full pass makes it 'ok'; on a runner nothing was ever stored "
     "so it is UNMEASURED and counts toward `unknown` - CI red, his Mac green, for a reason that "
     "is not in the diff"),
)

# ─── KIND 2: A PATH ON DISK ─────────────────────────────────────────────────────────
# ⚠⚠ EVERY HOST_STUBS ENTRY ABOVE PATCHES `module.attribute`, AND "THIS EXECUTABLE CANNOT RUN
# HERE" IS NOT ONE. It is a filesystem fact, so the simulator could not express it and answered
# "🟢 no KNOWN host dependency" about a suite whose dependency it had no vocabulary for -
# exactly the shape the v3319 comment above describes, which cost a day of red Publish runs over
# code that was correct throughout.
#
# Each entry: (path relative to tv/, mode, why a runner sees it differently).
#
#   "absent"          the file is NOT in a runner's checkout: os.path.exists / os.path.isfile /
#                     os.access read False for it, and exec raises FileNotFoundError.
#   "not-executable"  the file IS in the checkout, exec bit and all - so exists/isfile/access are
#                     left UNCHANGED, because that is what CI really sees - and only the EXEC fails.
#
# ⚠ NEITHER MODE EVER SUPPLIES A WORKING STAND-IN. A stub that answers is a fixture that hides
# the case; the whole point is that the runner gets nothing back. [[unknown-stays-unknown]]
HOST_PATHS = (
    ("bin/ocr_mac", "not-executable",
     "MEASURED 2026-09-23 rather than assumed: `git ls-files` TRACKS tv/bin/ocr_mac and `file` "
     "calls it 'Mach-O 64-bit executable arm64'. So on ubuntu-latest that path is PRESENT with "
     "its exec bit - tv_diablo._ocr_worker_cmd()'s `os.path.isfile(OCR_BIN) and "
     "os.access(OCR_BIN, os.X_OK)` guard passes there and the fast lane IS taken - and the "
     "failure arrives one step later at exec, as OSError errno 8 'Exec format error'. Stubbing "
     "it ABSENT would simulate a world CI does not have and would hide that guard being taken"),
)

# ─── KIND 3: A PLATFORM FACT, WHICH CANNOT BE STUBBED AT ALL ────────────────────────────
# "this interpreter takes fork_exec where Linux takes posix_spawn" is a fact about CPython and
# this kernel. There is no attribute to patch and no path to hide. The honest move is not a
# cleverer stub, it is a DIFFERENT ANSWER: name the tests and report UNKNOWN (exit 3).
#
# ⚠ MEASURED BEFORE THE MARKERS WERE CHOSEN, because a row that cries wolf gets silenced and
# that costs more than the defect. Across every tv/test_*.py: **8,111 test methods scanned, 64
# flagged (0.79%)**; inside test_control.py alone, 16. Both spawning tests of
# TestABrokenPipeMustNotSkipTheReap are flagged, including
# `test_closing_the_worker_stdin_CANNOT_BLOCK_THE_CALLER` - GREEN here in 5.3s, RED on the
# runner at 25.4s against its own >20s bound.
PLATFORM_FACTS = (
    (("subprocess.Popen", "subprocess.run", "subprocess.call",
      "subprocess.check_call", "subprocess.check_output"),
     "spawns a REAL child, so the outcome turns on how THIS CPython starts one (posix_spawn vs "
     "fork_exec, chosen per platform AND per argument shape) and on this kernel's pipe, fd and "
     "signal semantics"),
    (("os.fork", "os.forkpty", "pty.fork", "os.posix_spawn", "os.spawnv", "os.spawnvp",
      "os.system", "os.execv", "os.execve", "os.execvp", "os.execvpe",
      "multiprocessing.Process"),
     "forks or execs directly, so WHAT the child inherits and WHEN the parent is woken belong to "
     "the platform and not to the code under test"),
)

_PATH_MODES = ("absent", "not-executable")
_STUBBED_PATHS = {}          # realpath -> mode
_REAL_IO = {}                # the originals; presence here means the wrappers are installed


def apply_stubs(verbose=True):
    """Bind every host stub. -> [(name, ok, why)]"""
    sys.path.insert(0, HERE)
    out = []
    for mod_name, attr, val, why in HOST_STUBS:
        try:
            mod = __import__(mod_name)
        except Exception as e:
            out.append((("%s.%s" % (mod_name, attr)), False,
                        "module did not import: %s" % str(e)[:70]))
            continue
        if not hasattr(mod, attr):
            # ⚠ A STUB WITH NO TARGET IS A GATE MEASURING NOTHING. If the attribute is renamed this
            # must be loud, or the simulation silently stops simulating.
            out.append((("%s.%s" % (mod_name, attr)), False,
                        "attribute no longer exists — this stub is inert and the simulation is "
                        "weaker than it claims"))
            continue
        setattr(mod, attr, val)
        out.append((("%s.%s" % (mod_name, attr)), True, why))
    if verbose:
        for name, ok, why in out:
            print("  %s %-38s %s" % ("✓" if ok else "✗", name, why[:88]))
    return out


def _path_mode(p):
    """-> the stub mode recorded for `p`, else None. Compares REALPATHS, never text."""
    try:
        return _STUBBED_PATHS.get(os.path.realpath(os.fspath(p)))
    except Exception:
        return None


def _install_path_interception(hide_from_filesystem):
    """Wrap exec (always) and the filesystem (only when an ABSENT path is recorded). Idempotent.

    ⚠ REACH, STATED RATHER THAN ASSUMED. `subprocess.run` / `call` / `check_call` /
    `check_output` all resolve `Popen` out of the subprocess module's globals at CALL time, so
    one wrapper covers all five. A direct `os.execv` / `os.posix_spawn` is NOT intercepted - it
    is reported as a PLATFORM FACT instead, which is the honest bucket for it anyway.
    """
    import subprocess
    if "Popen" not in _REAL_IO:
        _REAL_IO["Popen"] = subprocess.Popen

        def Popen(args, *a, **k):
            argv0 = None
            if isinstance(args, (list, tuple)) and args:
                argv0 = args[0]
            elif isinstance(args, str) and args.split():
                argv0 = args.split()[0]
            m = _path_mode(argv0) if argv0 is not None else None
            if m == "absent":
                raise FileNotFoundError(2, "No such file or directory", str(argv0))
            if m == "not-executable":
                # ⚠ WHAT A LINUX RUNNER REALLY RAISES for a checked-in Mach-O binary. Not a
                # stand-in that works, and not a silent no-op: the call fails, the way it fails
                # there.
                raise OSError(8, "Exec format error", str(argv0))
            return _REAL_IO["Popen"](args, *a, **k)

        Popen._ci_sim_path_stub = True
        subprocess.Popen = Popen
    if hide_from_filesystem and "exists" not in _REAL_IO:
        _REAL_IO["exists"] = os.path.exists
        _REAL_IO["isfile"] = os.path.isfile
        _REAL_IO["access"] = os.access

        def exists(p):
            return False if _path_mode(p) == "absent" else _REAL_IO["exists"](p)

        def isfile(p):
            return False if _path_mode(p) == "absent" else _REAL_IO["isfile"](p)

        def access(p, mode, *a, **k):
            return False if _path_mode(p) == "absent" else _REAL_IO["access"](p, mode, *a, **k)

        for _f in (exists, isfile, access):
            _f._ci_sim_path_stub = True
        os.path.exists, os.path.isfile, os.access = exists, isfile, access


def apply_path_stubs(entries=None, verbose=True):
    """Make every recorded host PATH read the way a RUNNER sees it. -> [(name, ok, why)]

    The sibling of apply_stubs() for kind 2. It carries the same refusal, for the same reason:
    a stub with no target measures nothing.
    """
    rows, hide = [], False
    for rel, mode, why in (HOST_PATHS if entries is None else entries):
        full = os.path.join(HERE, rel)
        name = "%s [%s]" % (rel, mode)
        if mode not in _PATH_MODES:
            rows.append((name, False,
                         "unrecognised mode %r - this entry stubs nothing" % (mode,)))
            continue
        # ⚠ THE EQUIVALENT OF THE ATTRIBUTE-NO-LONGER-EXISTS REFUSAL, and it is not optional.
        # A path stub whose path has been renamed, moved or deleted is INERT: nothing is being
        # neutralised, yet the run would print a verdict as if it had been. `lexists` is used
        # deliberately - it is NOT one of the calls this file wraps, so the check cannot be
        # blinded by an interception installed on an earlier pass.
        if not os.path.lexists(full):
            rows.append((name, False,
                         "the path is not on THIS machine, so stubbing it neutralises nothing - "
                         "the record is stale and the simulation is weaker than it claims"))
            continue
        try:
            _STUBBED_PATHS[os.path.realpath(full)] = mode
        except Exception as e:
            rows.append((name, False, "could not resolve the path: %s" % str(e)[:60]))
            continue
        hide = hide or (mode == "absent")
        rows.append((name, True, why))
    if any(ok for _n, ok, _w in rows):
        _install_path_interception(hide)
    if verbose:
        for name, ok, why in rows:
            print("  %s %-38s %s" % ("\u2713" if ok else "\u2717", name, why[:88]))
    return rows


_SRC_INDEX = {}          # source file -> (module alias map, {(class, method): FunctionDef})


def _alias_map(tree):
    """import aliases -> dotted module paths, so `sp.Popen` and `subprocess.Popen` compare equal."""
    m = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                m[a.asname or a.name.split(".")[0]] = a.name
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            for a in n.names:
                m[a.asname or a.name] = "%s.%s" % (n.module, a.name)
    return m


def _dotted(call, aliases):
    """-> the DOTTED name a Call actually names, or None. Never a bare attribute."""
    f, parts = call.func, []
    while isinstance(f, ast.Attribute):
        parts.append(f.attr)
        f = f.value
    if not isinstance(f, ast.Name):
        return None
    parts.append(aliases.get(f.id, f.id))
    return ".".join(reversed(parts))


def _source_index(path):
    """-> (alias map, {(class, method): FunctionDef}) for one file, parsed once."""
    if path not in _SRC_INDEX:
        try:
            with io.open(path, encoding="utf-8", errors="replace") as fh:
                tree = ast.parse(fh.read())
        except Exception:
            _SRC_INDEX[path] = ({}, {})
            return _SRC_INDEX[path]
        idx = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for b in node.body:
                    if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        idx[(node.name, b.name)] = b
        _SRC_INDEX[path] = (_alias_map(tree), idx)
    return _SRC_INDEX[path]


def _platform_dependent(suite):
    """Tests turning on a fact NO stub can neutralise. -> ([(name, [markers])], [unreadable])

    ⚠ THE COMPILER, NOT THE TEXT. `ocr_mac` inside a docstring is prose; `sp.Popen(...)` is a
    call. This walks each test METHOD's AST and compares DOTTED names with import aliases
    resolved, so `import subprocess as sp` cannot hide a spawn and a string constant cannot
    invent one. [[source-reading-guard]] §1

    ⚠ ITS REACH, STATED IN THE SAME BREATH AS ITS ANSWER: the method's OWN body. A spawn inside
    a helper the method calls is not seen, and any method whose definition could not be found is
    returned as UNREADABLE - unchecked, never clear. [[unknown-stays-unknown]]
    """
    marks = {}
    for names, why in PLATFORM_FACTS:
        for n in names:
            marks[n] = why
    found, unread = [], []

    def defining(cls, method):
        for k in getattr(cls, "__mro__", None) or [cls]:
            if method in getattr(k, "__dict__", {}):
                return k
        return cls

    def walk(s):
        for t in s:
            if isinstance(t, unittest.TestSuite):
                walk(t)
                continue
            name = getattr(t, "_testMethodName", str(t))
            try:
                k = defining(type(t), name)
                aliases, idx = _source_index(inspect.getfile(k))
                node = idx.get((k.__name__, name))
            except Exception:
                node = None
            if node is None:
                unread.append(name)
                continue
            al = dict(aliases)
            al.update(_alias_map(node))
            hits = set()
            for c in ast.walk(node):
                if isinstance(c, ast.Call):
                    d = _dotted(c, al)
                    if d in marks:
                        hits.add(d)
            if hits:
                found.append((name, sorted(hits)))

    walk(suite)
    return found, unread



def _without_tests_of(suite, stubbed, module):
    """Drop tests whose own body calls a stubbed name. -> (suite, [dropped names])

    Read from the SOURCE of each test, not from its name — a name is a guess about what a test does
    and this decides whether it runs at all.
    """
    import inspect
    import re as _re
    keep, dropped = [], []

    def walk(s):
        for t in s:
            if isinstance(t, unittest.TestSuite):
                walk(t)
                continue
            try:
                src = inspect.getsource(getattr(t, t._testMethodName))
            except Exception:
                src = ""
            # ⚠ TWO FIXES BROKE EACH OTHER, AND THIS IS THE JOIN. Mentioning a stubbed name is not
            # the same as depending on the stub:
            #
            #   a test that ASSERTS what board_identity_drift returns  -> its subject is gone, drop it
            #   a test that PATCHES board_identity_drift for a scenario -> its own patch wins over
            #                                                             mine, so the stub is inert
            #                                                             and it MUST still run
            #
            # The first cut dropped both. Adding the patch to the two tests whose CI failure started
            # all of this therefore made the simulator stop checking exactly those two — coverage
            # shrinking precisely where the defect had been. [[two-fixes-broke-each-other]]
            mentions = [a for a in stubbed if _re.search(r"\b%s\b" % _re.escape(a), src)]
            patches = [a for a in mentions
                       if _re.search(r"patch\.object\([^)]*\b%s\b" % _re.escape(a), src)
                       or _re.search(r"patch\([^)]*\b%s\b" % _re.escape(a), src)]
            if mentions and not patches:
                dropped.append(t._testMethodName)
            else:
                keep.append(t)

    walk(suite)
    out = unittest.TestSuite()
    for t in keep:
        out.addTest(t)
    return out, dropped


def _load_failures(suite):
    """-> names unittest could not LOAD. They are wrapped as _FailedTest and would otherwise be
    counted as errors, i.e. as evidence about the machine rather than about the request."""
    out = []
    def walk(s):
        for t in s:
            if isinstance(t, unittest.TestSuite):
                walk(t)
            elif type(t).__name__ == "_FailedTest":
                out.append(getattr(t, "_testMethodName", str(t)))
    walk(suite)
    return out


def _module_defining(name):
    """-> the imported tv/test_*.py module that DEFINES `name`, or None.

    ⚠ Import failures are swallowed on purpose: a module that cannot import here is not the
    subject of the question being asked, and letting one bad file abort the search would turn a
    findable class into an unfindable one.
    """
    import importlib
    for fn in sorted(os.listdir(HERE)):
        if not (fn.startswith("test_") and fn.endswith(".py")):
            continue
        try:
            mod = importlib.import_module(fn[:-3])
        except Exception:
            continue
        if hasattr(mod, name):
            return mod
    return None


def main(argv=None):
    argv = list(argv or [])
    try:
        from console_safe import enable  # noqa: F401
    except Exception:
        pass
    print("CI SIMULATION — the suite as a runner sees it\n")
    stubs = apply_stubs()
    paths = apply_path_stubs()
    # ⚠ ONE REFUSAL FOR BOTH KINDS. A path stub whose path has moved is exactly as inert as
    # an attribute stub whose attribute was renamed, and a run that simulates less than it
    # claims is the failure this whole file is against.
    inert = [n for n, ok, _w in list(stubs) + list(paths) if not ok]
    if inert:
        print("\n\U0001f534 %d stub(s) could not bind, so this run simulates LESS than it says: %s"
              % (len(inert), ", ".join(inert)))
        return 2
    os.chdir(HERE)
    sys.path.insert(0, ".")
    import test_control
    which = argv[0] if argv else None
    loader = unittest.TestLoader()
    # ⚠⚠ v3353 — IT ONLY EVER SIMULATED ONE FILE WHILE CLAIMING THE SUITE, AND A LOAD FAILURE CAME
    # BACK AS A VERDICT ABOUT HIS MACHINE. Asked for a class living in
    # test_an_examined_panel_is_not_an_unread_one.py, this raised
    # "module 'test_control' has no attribute ..." inside the loader, unittest wrapped it as a
    # _FailedTest, the runner counted it as an ERROR, and the tail printed
    # "🔴 1 test(s) depend on something only HIS machine has". The test never ran. A name this
    # tool could not find is UNKNOWN, and turning it into a confident claim about his machine is
    # the collapse this whole file exists to prevent, committed by the file itself.
    # [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
    home = test_control
    if which:
        root = which.split(".")[0]
        if not hasattr(test_control, root):
            home = _module_defining(root) or test_control
    suite = (loader.loadTestsFromName(which, home) if which
             else loader.loadTestsFromModule(test_control))
    # a loader error is NOT a test result — refuse before anything counts it as one
    _bad_load = _load_failures(suite)
    if _bad_load:
        print("\u26a0 could not LOAD %d name(s): %s" % (len(_bad_load), ", ".join(_bad_load)))
        print("   That is UNKNOWN, not a host dependency. This tool searches test_control first "
              "and then every tv/test_*.py that DEFINES the name; if it still cannot be found the "
              "name is wrong or the module does not import here. Nothing was simulated.")
        return 2
    print("   reach: %s" % ("module %s" % home.__name__ if which else
                            "test_control only — other test files are NOT simulated"))
    # ⚠ A TEST OF THE STUBBED FUNCTION IS NOT A TEST THAT DEPENDS ON HIS MACHINE, and the first cut
    # of this file reported four of them as host-dependent. They call `board_identity_drift`
    # directly to assert what it returns; replacing it removes their subject, so they fail for a
    # reason that has nothing to do with CI. A simulator that cries wolf gets ignored exactly like
    # the permanently-red gate it exists to replace — which would make this file the defect it was
    # written against. Drop them from the run and SAY how many, because silently excluding tests is
    # how a sample turns into a verdict. [[regression-guard]]
    stubbed = {attr for _m, attr, _v, _w in HOST_STUBS}
    suite, dropped = _without_tests_of(suite, stubbed, home)
    if dropped:
        print("  \u2139 %d test(s) excluded because they TEST a stubbed function rather than "
              "depend on it:" % len(dropped))
        for d in sorted(dropped)[:8]:
            print("      %s" % d)
    print()
    # ⚠ READ THE SUITE BEFORE IT IS RUN. `unittest.TestSuite._cleanup` is True by
    # default, so the suite REPLACES EACH TEST WITH None as it finishes it - asked
    # afterwards it yields ten Nones, `type(None)` has no source file, and every test
    # came back "could not be read". MEASURED: 10 of 10 unreadable, which is the count
    # being the tell - a detector that fails on ALL of its input is broken, not strict.
    # [[feedback-suspect-the-instrument]]
    plat, unread = _platform_dependent(suite)
    r = unittest.TextTestRunner(verbosity=1).run(suite)
    bad = [t.id().split(".")[-1] for t, _ in list(r.failures) + list(r.errors)]
    print()
    if unread:
        print("\u26a0 %d test(s) could not be read for platform facts \u2014 UNCHECKED, not "
              "clear." % len(unread))
    if bad:
        print("\U0001f534 %d test(s) depend on something only HIS machine has:" % len(bad))
        for b in bad[:20]:
            print("     %s" % b)
        # ⚠ AND SAY WHICH OF THEM THAT CLAIM IS UNPROVEN FOR. A test that spawns a real child
        # may be failing because of THIS kernel rather than because of anything his Mac has,
        # and attributing it anyway is the same over-claim in the other direction.
        _pn = {_n for _n, _h in plat}
        _both = [b for b in bad if b in _pn]
        if _both:
            print("   \u26aa %d of those also turn on a PLATFORM FACT this tool cannot "
                  "neutralise, so \"only HIS machine\" is UNPROVEN for them:" % len(_both))
            for b in _both[:8]:
                print("     \u26aa %s" % b)
        return 1
    # ⚠⚠ UNKNOWN IS A THIRD ANSWER, NOT A SOFT GREEN. Every test below ran and passed; the
    # point is that passing HERE is not evidence about a runner when the subject is how this
    # interpreter, kernel or CPU behaves. Printing the green verdict over that is precisely the
    # over-claim the header of this file forbids. [[unknown-stays-unknown]]
    # ⚠⚠ #196 (v3460) — "COULD NOT BE READ" IS UNKNOWN TOO, AND IT USED TO EXIT 0.
    # `unread` was PRINTED above and then ignored by every return: exit 1 on failures, exit 3 on
    # platform facts, else exit 0 — "no KNOWN host dependency". So a suite whose unreadable tests
    # all passed reported a clean verdict about work this tool never examined. A method added on
    # the class at runtime is unreadable by construction: defining() finds it, inspect.getfile
    # names the class file, and _source_index only holds FunctionDef nodes that appear in the
    # class BODY — so the AST never had it.
    # It lands in exit 3 rather than a fourth code because it is the SAME answer in kind: this
    # tool cannot tell you. The two reasons stay NAMED separately so a reader can act on the
    # right one. [[unknown-stays-unknown]] [[feedback-blind-fixture-green-gate]]
    if plat or unread:
        if unread and not plat:
            print("\u26aa UNKNOWN — no KNOWN host dependency in %d test(s), but %d of them "
                  "COULD NOT BE READ" % (r.testsRun, len(unread)))
            print("   for platform facts at all, so this tool examined only the rest. A skip is "
                  "not a pass.")
            for _u in list(unread)[:12]:
                print("     \u26aa %s" % str(_u)[:70])
            if len(unread) > 12:
                print("     \u26aa … and %d more" % (len(unread) - 12))
            print("   Exit 3 is UNKNOWN, not failure.")
            return 3
        if unread:
            print("\u26aa %d test(s) COULD NOT BE READ, and are counted in this UNKNOWN rather "
                  "than passed over." % len(unread))
    if plat:
        print("\u26aa UNKNOWN — no KNOWN host dependency in %d test(s), but %d of them turn "
              "on a PLATFORM FACT" % (r.testsRun, len(plat)))
        print("   this tool CANNOT neutralise, so their result here is not evidence about CI:")
        for _n, _hits in plat[:12]:
            print("     \u26aa %-56s %s" % (_n[:56], ", ".join(_hits)))
        if len(plat) > 12:
            print("     \u26aa … and %d more" % (len(plat) - 12))
        print("   That is not the same as \"CI will pass\" — only the stubs above were "
              "neutralised, and")
        print("   no stub can make this interpreter, kernel or CPU into a runner's. Exit 3 "
              "is UNKNOWN, not failure.")
        return 3
    print("\U0001f7e2 no KNOWN host dependency in %d test(s)." % r.testsRun)
    print("   That is not the same as \"CI will pass\" — only the stubs above were neutralised.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
