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


def drift(mod):
    """-> (checked, mismatches, why). `why` is set only when nothing could be measured.

    ⚠ UNWRAP FIRST, AND REQUIRE THE FUNCTION'S OWN FILE. `@contextmanager` and every `functools.wraps`
    decorator copy `__module__` onto a wrapper whose `__code__` lives in contextlib. The first cut of
    this reported `tick_caches` and `_lock_briefly` as drifted, BOTH at line 242 — the same line in
    two unrelated modules, which is the tell that the instrument was wrong and not the code. Line 242
    of contextlib.py is the generic `helper`. Unwrapped they sit at 7437 and 3592 of their own files.
    [[feedback-suspect-the-instrument]]
    """
    path = getattr(mod, "__file__", None) or ""
    if not path.endswith(".py"):
        return 0, [], "%s has no .py source" % getattr(mod, "__name__", "?")
    lines = _source_lines(path)
    if lines is None:
        return 0, [], "the source of %s could not be read" % os.path.basename(path)
    real = os.path.realpath(path)
    checked, bad = 0, []
    for name, obj in list(vars(mod).items()):
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
        # a function whose code lives in another file is not this module's to grade
        if os.path.realpath(code.co_filename or "") != real:
            continue
        ln = code.co_firstlineno
        checked += 1
        if not ln or ln > len(lines):
            bad.append((name, ln, "<past end of file: %d lines>" % len(lines)))
            continue
        # ⚠⚠ WALK PAST THE DECORATORS TO THE `def`, NEVER ACCEPT AN `@` LINE ON ITS OWN. CPython
        # points `co_firstlineno` at the FIRST DECORATOR of a decorated function, so the first cut
        # simply accepted any line beginning with `@`. That escape hatch swallowed everything: a
        # genuinely drifted function whose reported line happened to land on a decorator passed,
        # and the red-proof for `unwrap` came back BLIND at match count 1 twice because both
        # decorator cases exited through it. The count was right and the LAW was weak.
        # Resolving to the actual `def` is what makes the comparison mean anything.
        probe, guard = ln - 1, 0
        while probe < len(lines) and guard < 80:
            s = lines[probe].strip()
            # ⚠ DECORATORS AND BLANKS ONLY — NOT COMMENTS. Skipping comment lines let the walk
            # stroll arbitrarily far looking for a matching `def`: the case that rewrites a file
            # with 40 comment lines above the function then found it again and reported NO drift,
            # which is the exact defect this whole module exists to catch. A tolerance wide enough
            # to re-find the function is a tolerance that cannot detect it moving.
            if s and not s.startswith("@"):
                break
            probe += 1
            guard += 1
        here = lines[probe] if probe < len(lines) else ""
        ok = bool(re.match(r"\s*(async\s+)?def\s+%s\b" % re.escape(name), here))
        if not ok:
            bad.append((name, ln, here.strip()[:70]))
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
    return True, ("%d function(s) checked across %d module(s): every one starts where the source "
                  "says it does" % (checked, len(modules)))


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
