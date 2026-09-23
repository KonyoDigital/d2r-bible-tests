# -*- coding: utf-8 -*-
"""Is the code this process LOADED the code that is on disk?

⚠⚠ A SUITE THAT EXECUTES CODE WHICH IS NOT ON DISK IS WORSE THAN A RED ONE, because its verdict is
about a file nobody has. MEASURED 2026-09-23: three pushes of the IDENTICAL tree minutes apart read
`tv suites green`, then `test_control FAILED`, then `tv suites green`. The failing traceback named
`test_control.py line 11902 ... assertIn('spec["store"]', fn` — and the file on disk has that
assertion at line 11938 using the variable `helper`. That older shape is exactly the PRE-v3427
code. The same run also reported an older second-eye version. Three anomalies, one run, and no
explanation in terms of the tree. #179

⚠ WHY THE EXISTING CHECK COULD NOT SEE IT, AND THIS IS NOT A SECOND ANSWER TO ONE QUESTION.
`console_doctor._check_the_running_code_is_the_code_on_disk` asks the CONSOLE over the wire for
`proc.srcSha` and `moduleFreshness`. That is a different question in a different process: it grades
the console's image of control_app.py. The pre-push suite is its own `python3 tv/test_control.py`,
which the console knows nothing about. This module answers "does THIS interpreter's bytecode agree
with the source", for whatever process asks. [[copy-drift]] §1 — one source per question.

⚠ AND IT CANNOT BE DONE BY COMPARING mtime AND SIZE. That is precisely what CPython already does to
decide a `.pyc` is fresh, so a check built from the same two inputs agrees with it by construction —
including when they collide. The only witness that survives a collision is the CODE ITSELF: a
function object carries `co_firstlineno` from the BYTECODE, while the source file is read fresh. If
they disagree, the loaded module is not the file.

⚠ ON THIS MAC THE CACHE IS NOT IN `__pycache__`. `sys.pycache_prefix` relocates it to
~/Library/Caches/com.apple.python/<absolute source path>, so deleting `__pycache__` clears nothing
and a reader looking there concludes wrongly. [[python-pycache-prefix-mac]]
"""
import io
import inspect
import os
import re
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))

if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _source_lines(path):
    try:
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read().split("\n")
    except Exception:
        return None


def _def_lines(path):
    """{name: the line a module-level `def` STARTS on, decorators included}. -> (dict, why)

    ⚠⚠ v3434 — ASKED OF THE AST, NOT WALKED LINE BY LINE, AND THE SECOND EYE IS WHY. The first cut
    scanned forward from `co_firstlineno` skipping `@` and blank lines until it found `def <name>`.
    That heuristic was wrong in three directions at once and the eye named all three:
      · a BLANK line appearing at the function's old line let the walk skip on and re-find the def
        below, so a genuinely stale function read CLEAN. Comments were caught, blanks were not.
      · a MULTI-LINE decorator — `@deco(\n "arg",\n)` — stopped the walk on `"arg",`, so a
        function loaded correctly from disk was reported as DRIFT. Ordinary Python, false alarm.
      · a `lambda` assigned at module level, or an alias `public = _real`, has a dict key that is
        not the `def` name, so both read as drift while bytecode and disk agreed.
    MEASURED on the six watched modules: zero of those shapes are present TODAY, so none of it was
    firing — but all three are ordinary Python and the first one to appear would have broken it.

    The AST knows exactly where a function starts, decorators and all. No walking, no tolerance,
    nothing to tune. ⚠ A name defined TWICE at module level is ambiguous and is reported as
    unlocatable rather than guessed at. [[unknown-stays-unknown]]
    """
    import ast as _ast
    try:
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            tree = _ast.parse(fh.read())
    except Exception as e:
        return None, "the source of %s could not be parsed (%s)" % (os.path.basename(path),
                                                                    type(e).__name__)
    out, dupes = {}, set()
    for node in tree.body:
        if not isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            continue
        start = min([d.lineno for d in node.decorator_list] + [node.lineno])
        if node.name in out and out[node.name] != start:
            dupes.add(node.name)
        out[node.name] = start
    for d in dupes:
        out.pop(d, None)
    return out, None


def drift(mod):
    """-> (checked, mismatches, why). `why` is set only when nothing could be measured.

    ⚠ REACH: MODULE-LEVEL FUNCTIONS ONLY. Methods, classmethods, nested functions and lambdas are
    not in `vars(mod)` and are never opened, so lines inserted inside a CLASS move its methods
    without this noticing. That is a real limit, it is stated rather than implied, and the say()
    text carries it so nobody reads a green as more than it is.

    ⚠ UNWRAP FIRST, AND REQUIRE THE FUNCTION'S OWN FILE. `@contextmanager` and every
    `functools.wraps` decorator copy `__module__` onto a wrapper whose `__code__` lives elsewhere.
    The first cut reported `tick_caches` and `_lock_briefly` as drifted, BOTH at line 242 — the same
    line in two unrelated modules, which is the tell that the instrument was wrong and not the code.
    [[feedback-suspect-the-instrument]]

    ⚠ THE NAME COMPARED IS `co_name`, NOT THE DICT KEY, so `public = _real` and import aliases
    resolve to the function that was actually compiled.
    """
    path = getattr(mod, "__file__", None) or ""
    if not path.endswith(".py"):
        return 0, [], "%s has no .py source" % getattr(mod, "__name__", "?")
    if not os.path.exists(path):
        return 0, [], "the source of %s is not on disk" % os.path.basename(path)
    table, why = _def_lines(path)
    if table is None:
        return 0, [], why
    real = os.path.realpath(path)
    checked, bad = 0, []
    for _key, obj in list(vars(mod).items()):
        if not isinstance(obj, types.FunctionType):
            continue
        if getattr(obj, "__module__", None) != getattr(mod, "__name__", None):
            continue
        try:
            fn = inspect.unwrap(obj)
        except Exception:
            fn = obj
        code = getattr(fn, "__code__", None)
        if code is None:
            continue
        if os.path.realpath(code.co_filename or "") != real:
            continue          # a function whose code lives elsewhere is not this module's to grade
        expected = table.get(code.co_name)
        if expected is None:
            continue          # lambda, nested, or a name defined twice — unlocatable, not drift
        checked += 1
        if code.co_firstlineno != expected:
            bad.append((code.co_name, code.co_firstlineno,
                        "the file says it starts at line %d" % expected))
    return checked, bad, None


def report(modules):
    """-> (checked, mismatches, unmeasured). Sum `drift` over already-imported modules."""
    checked, bad, why = 0, [], []
    for m in modules:
        mod = sys.modules.get(m)
        if mod is None:
            why.append("%s is not imported in this process" % m)
            continue
        c, b, w = drift(mod)
        checked += c
        bad.extend((m, n, ln, txt) for (n, ln, txt) in b)
        if w:
            why.append(w)
    return checked, bad, why


def say(modules):
    """A one-line human verdict. -> (ok, text)"""
    checked, bad, why = report(modules)
    if bad:
        first = bad[0]
        return False, ("%d function(s) in this process are loaded from bytecode that DISAGREES with "
                       "the source on disk - e.g. %s.%s says line %s, where the file has %r. This "
                       "interpreter is running code nobody can read."
                       % (len(bad), first[0], first[1], first[2], first[3]))
    if not checked:
        return None, ("no function could be compared (%s) - that is UNMEASURED, not agreement"
                      % ("; ".join(why) if why else "nothing imported"))
    # ⚠⚠ v3434 — A MIXED ANSWER IS NOT A CLEAN ONE, AND THE SECOND EYE CAUGHT THIS. The first cut
    # returned True whenever `checked > 0` and `bad` was empty, DROPPING every `why`. So if
    # control_app matched while lane_census was missing, unreadable or not a .py, the verdict was a
    # confident OK over a population that had quietly shrunk - and the sentence still said "across
    # N module(s)", counting modules nobody looked at. The all-unmeasured branch above was already
    # honest; the MIXED branch was not, which is the harder half to notice.
    # [[zero-needs-a-denominator]] [[unknown-stays-unknown]]
    if why:
        return None, ("%d function(s) matched, but %d of %d module(s) could not be compared at all "
                      "(%s) - a partial look is UNMEASURED, not agreement"
                      % (checked, len(why), len(modules), "; ".join(why)))
    return True, ("%d function(s) checked across %d module(s): every one starts where the source "
                  "says it does. ⚠ MODULE-LEVEL FUNCTIONS ONLY - methods, nested functions and "
                  "lambdas are not opened, so lines moving inside a class are not covered"
                  % (checked, len(modules)))


if __name__ == "__main__":
    from console_safe import enable as _enable
    _enable()
    mods = sys.argv[1:] or ["control_app", "console_doctor", "second_eye_run", "lane_census"]
    for m in mods:
        try:
            __import__(m)
        except Exception as e:
            print("  %s: import failed (%s)" % (m, type(e).__name__))
    ok, text = say(mods)
    print(("  OK: " if ok else ("  UNMEASURED: " if ok is None else "  DRIFT: ")) + text)
    sys.exit(0 if ok else 1)
