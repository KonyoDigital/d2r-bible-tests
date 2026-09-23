# -*- coding: utf-8 -*-
"""v3429 (#150) — THE DOCTOR MUST NOT fork() A PROCESS THAT HAS LOADED THE OBJECTIVE-C RUNTIME.

`test_control HUNG — killed after 1500s on an IDLE machine` has refused FOUR pushes since
2026-09-20, and the standing diagnosis ("the cheap subset is over budget") was wrong. MEASURED
2026-09-23, back to back, same idle machine:

    run 1 — cd.run(include_slow=False) hung 28 MINUTES at 0.0% CPU and had to be killed
    run 2 — the SAME call FINISHED IN 15.4 SECONDS, 107 rows

⚠ SO IT IS A DEADLOCK, NOT A COST, and RESUME_HERE's ">8 min alone" measured the HUNG case. Its
own puzzle — "the whole is minutes; every part is seconds" — dissolves: the parts ARE seconds. A
hang must never be averaged with a cost.

WHAT IT IS, from the stuck process: the hung parent had exactly ONE child, at 0.0% CPU, with no
grandchildren, **wearing the PARENT'S OWN ARGV** — the signature of a `subprocess.Popen` caught
BETWEEN fork and exec — and holding Quartz / CoreGraphics / QuickLookUI / PyObjC. control_app and
health_engine import those, so by the time any check shells out the Obj-C runtime is initialised,
and forking such a process without immediately exec'ing is the macOS fork-safety deadlock. 0% CPU
for 28 minutes is a lock wait; a busy loop cannot produce it.

THE ESCAPE, PROVEN BY RECORDING WHICH SYSCALL CPYTHON ACTUALLY TAKES rather than reading its
conditions:

    close_fds default (True)          -> fork_exec x1, posix_spawn x0      <- the hang
    absolute exe + close_fds=False    -> posix_spawn x1, fork_exec x0
    bare name "ps" + close_fds=False  -> fork_exec x1                      <- dirname condition

⚠ BOTH HALVES ARE LOAD-BEARING and `close_fds` DEFAULTS TO TRUE, which is why every ordinary call
forks. ⚠ AND close_fds=False IS SCOPED TO SHORT-LIVED READS: the child inherits open descriptors,
which for a long-lived worker would mean holding this console's listening socket past a restart.

==========================================================================================
v3435 (#150, reopened) — **THE CLASS LAW RECORDED TWO OF THE CONDITIONS CPYTHON CHECKS, AND
CPYTHON CHECKS FOURTEEN.**

The v3429 class law asked one question — "is the keyword `close_fds` present?" — and it asked it
only of receivers spelled `subprocess` / `_sp` / `sp`. Both halves of that were too narrow, and
each hid live forking sites:

  · **PRESENCE IS NOT VALUE.** `if "close_fds" not in kws` accepts `close_fds=True`, which is the
    fork. It also never looked at the dirname half at all, though this file's OWN sibling case
    (`test_a_BARE_executable_name_still_forks`) proves dirname is fatal on its own.
  · **THE RECEIVER SET WAS A SPELLING LIST.** `console_doctor` reaches subprocess through
    `git_quiet.run` (imported as `_gq`), a one-door wrapper that forwards `**kw` straight into
    `subprocess.run`. `_gq` is not `subprocess`, so SIX git spawns were skipped outright — and
    every one of them passes `cwd=ROOT`, which is condition six.

⚠ THE FIX IS NOT "ADD `run` TO AN ALLOWLIST". `subprocess.run` and `_gq.run` are both spelled
`run`; a guard widened on the bare attribute admits whatever else is spelled that way. Receivers
are resolved to **DOTTED module names** through the file's own import aliases, and the wrapper is
**DISCOVERED** — any module imported from `tv/` whose function forwards its `**kwargs` into a
subprocess spawner is a door, so the next `git_quiet` is seen without anyone remembering to list
it. [[a-widened-guard-admits-what-it-bans]]

⚠ AND THE NINE ARE NOT A NUMBER I TYPED. `_cpython_guard_vars()` parses
`subprocess.Popen._execute_child` **on the running interpreter** and returns the actual identifiers
its posix_spawn gate reads (14 clauses on CPython 3.9.6). A condition this file does not classify
is a RED, so a future CPython that adds one cannot silently widen the blind spot.
[[feedback-comments-vs-code]]

⚠ THE PREMISE CASES NOW CLASSIFY THE HOST, AND THEY SAY WHICH WORD THEY MEAN. The fork/spawn
premise is macOS-shaped; the gate set runs on `ubuntu-latest`. A premise case that simply passed
there would be a green that measured nothing, and one that simply skipped would be a silence.
`_host_probe()` MEASURES both control shapes at import and each host-dependent case records exactly
one of **MEASURED / NOT-APPLICABLE / UNKNOWN** with its reason, printed, and a completeness law
fails if any case recorded nothing. `0` measured is not `None` unmeasured.
[[unknown-stays-unknown]]
"""
import ast
import inspect
import io
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

DOCTOR = os.path.join(HERE, "console_doctor.py")
with io.open(DOCTOR, encoding="utf-8", errors="replace") as _fh:
    SRC = _fh.read()


# =========================================================================================
# 1. THE SPAWN-ELIGIBILITY CLASSIFIER — one function, every condition CPython actually checks
# =========================================================================================

# Every keyword of `Popen.__init__` that can, on its own, push CPython off posix_spawn and onto
# fork_exec. The names on the LEFT are the local variables read by the guard in
# `Popen._execute_child`; `_cpython_guard_vars()` proves this map is complete on the running
# interpreter, so it cannot silently fall behind the language.
#
#   guard variable      what a CALL SITE writes it with          how it is violated
GUARD_VAR_TO_CONDITION = {
    "executable":        "executable-has-a-dirname",   # argv[0] or executable=
    "preexec_fn":        "preexec_fn-is-None",
    "close_fds":         "close_fds-is-False",         # ⚠ DEFAULTS TO TRUE -> absent == violated
    "pass_fds":          "no-pass_fds",
    "cwd":               "cwd-is-None",                # ⚠ the six git spawns
    "p2cread":           "stdin-is-not-fd-0-1-2",
    "c2pwrite":          "stdout-is-not-fd-0-1-2",
    "errwrite":          "stderr-is-not-fd-0-1-2",
    "start_new_session": "start_new_session-is-falsy",
    "uid":               "user-is-None",
    "gid":               "group-is-None",
    "gids":              "extra_groups-is-None",
    "umask":             "umask-is-negative",
    "process_group":     "process_group-is-default",   # CPython 3.11+
}

# The NINE that a call site in this repo can realistically trip, in the order CPython tests them.
# (uid/gid/gids/umask/process_group are the identity tail — classified, never yet used here.)
NINE_CONDITIONS = (
    "executable-has-a-dirname",
    "preexec_fn-is-None",
    "close_fds-is-False",
    "no-pass_fds",
    "cwd-is-None",
    "stdin-is-not-fd-0-1-2",
    "stdout-is-not-fd-0-1-2",
    "stderr-is-not-fd-0-1-2",
    "start_new_session-is-falsy",
)

# Keyword -> the condition it can violate. `executable` and the three streams are handled by hand.
KW_TO_CONDITION = {
    "preexec_fn": "preexec_fn-is-None",
    "close_fds": "close_fds-is-False",
    "pass_fds": "no-pass_fds",
    "cwd": "cwd-is-None",
    "stdin": "stdin-is-not-fd-0-1-2",
    "stdout": "stdout-is-not-fd-0-1-2",
    "stderr": "stderr-is-not-fd-0-1-2",
    "start_new_session": "start_new_session-is-falsy",
    "user": "user-is-None",
    "group": "group-is-None",
    "extra_groups": "extra_groups-is-None",
    "umask": "umask-is-negative",
    "process_group": "process_group-is-default",
}

SPAWNERS = ("run", "Popen", "call", "check_call", "check_output",
            "getoutput", "getstatusoutput")

# Helpers that turn a bare command into a path WITH a dirname when the tool is installed, and fall
# back to the bare name when it is not. `_spawnable()` in console_doctor is exactly this shape, as
# is `_PS = "/bin/ps" if os.path.exists("/bin/ps") else "ps"`.
PATH_RESOLVERS = ("_spawnable", "shutil.which", "which", "distutils.spawn.find_executable")

# executable-resolution states
ABSOLUTE = "ABSOLUTE"                            # always has a dirname
ABSOLUTE_IF_INSTALLED = "ABSOLUTE_IF_INSTALLED"  # which()-style: dirname whenever the tool exists
BARE = "BARE"                                    # never has a dirname -> ALWAYS forks
EXE_UNKNOWN = "UNKNOWN"                          # nobody can tell from here

FORKS = "FORKS"
SPAWNS = "SPAWNS"
UNKNOWN = "UNKNOWN"


def _cpython_guard_vars():
    """The identifiers the RUNNING interpreter's posix_spawn gate actually reads. -> set or None

    ⚠ READ FROM THE COMPILER, NOT FROM A COMMENT. This file used to record two conditions because
    two is what somebody remembered. `Popen._execute_child` is the only authority on how many
    there are, and it moves between versions (3.11 added `process_group`). None means the source
    was not available — UNKNOWN, never "there are none". [[unknown-stays-unknown]]
    """
    try:
        src = inspect.getsource(subprocess.Popen._execute_child)
    except (OSError, TypeError):
        return None
    try:
        tree = ast.parse("if 1:\n" + "\n".join("    " + l for l in src.splitlines()))
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not isinstance(node.test, ast.BoolOp):
            continue
        if not isinstance(node.test.op, ast.And):
            continue
        ids = {n.id for n in ast.walk(node.test) if isinstance(n, ast.Name)}
        if "_USE_POSIX_SPAWN" in ids:
            # `os` is the module in `os.path.dirname(executable)`; the condition it belongs to is
            # already carried by `executable`.
            return ids - {"_USE_POSIX_SPAWN", "os"}
    return None


def _import_aliases(tree):
    """Every name this module binds to a module, mapped to the DOTTED module it names. -> dict

    ⚠ THE WHOLE POINT OF THE DOTTED FORM. `subprocess.run` and `_gq.run` are both spelled `run`,
    and a guard widened on the bare attribute admits whatever else is spelled that way. Resolving
    `_gq` -> `git_quiet` and `_sp` -> `subprocess` through the file's own imports keeps them two
    different names. Function-local imports count: console_doctor does `import git_quiet as _gq`
    inside five separate check bodies. [[a-widened-guard-admits-what-it-bans]]
    """
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.asname:
                    aliases[a.asname] = a.name
                else:
                    aliases[a.name.split(".")[0]] = a.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for a in node.names:
                aliases[a.asname or a.name] = node.module + "." + a.name
    return aliases


def _dotted(node, aliases):
    """The dotted name a Name/Attribute expression denotes, with aliases resolved. -> str or None"""
    parts = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if not isinstance(cur, ast.Name):
        return None
    parts.append(aliases.get(cur.id, cur.id))
    return ".".join(reversed(parts))


def discover_spawn_doors(tree, where=HERE):
    """Every dotted callable in this tree that ends up in `subprocess`. -> dict name -> why

    Two kinds:
      · DIRECT   — `subprocess.run`, `subprocess.Popen`, ... under whatever alias.
      · WRAPPER  — a module imported from `tv/` with a function that forwards its own `**kwargs`
                   into a subprocess spawner. `git_quiet.run` is one. DISCOVERED, not listed, so
                   the next one-door wrapper is seen without anybody remembering to add it.

    ⚠ A WRAPPER THAT FORWARDS `**kw` FORWARDS THE HAZARD. git_quiet.run does
    `return subprocess.run(argv, **kw)`; it injects nothing on POSIX. So `cwd=` and the missing
    `close_fds=` at the CALL SITE are what decide the syscall, and the call site is what this
    classifier grades.
    """
    aliases = _import_aliases(tree)
    doors = {}
    for alias, mod in aliases.items():
        if mod == "subprocess":
            for fn in SPAWNERS:
                doors["subprocess." + fn] = "direct"
        elif mod.startswith("subprocess."):
            doors[mod] = "direct"
    for mod in sorted(set(aliases.values())):
        if "." in mod or mod == "subprocess":
            continue
        path = os.path.join(where, mod + ".py")
        if not os.path.isfile(path):
            continue
        try:
            with io.open(path, encoding="utf-8", errors="replace") as fh:
                wtree = ast.parse(fh.read())
        except SyntaxError:
            continue
        waliases = _import_aliases(wtree)
        for fn in ast.walk(wtree):
            if not isinstance(fn, ast.FunctionDef):
                continue
            kwarg = fn.args.kwarg.arg if fn.args.kwarg else None
            if not kwarg:
                continue
            for call in ast.walk(fn):
                if not isinstance(call, ast.Call):
                    continue
                d = _dotted(call.func, waliases) or ""
                if not d.startswith("subprocess.") or d.split(".")[-1] not in SPAWNERS:
                    continue
                forwards = any(k.arg is None and isinstance(k.value, ast.Name)
                               and k.value.id == kwarg for k in call.keywords)
                if forwards:
                    doors["%s.%s" % (mod, fn.name)] = "wrapper -> %s (forwards **%s)" % (d, kwarg)
    return doors


def _assigned_values(name, func, tree):
    """Every value `name` is assigned inside `func`, else at module level. -> list of ast nodes"""
    out = []
    for scope in (func, tree):
        if scope is None:
            continue
        for node in ast.walk(scope):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == name:
                        out.append(node.value)
        if out:
            break
    return out


def _exe_state(node, func, tree, aliases, depth=0):
    """Does this expression name an executable WITH a dirname? -> (state, how)"""
    if node is None or depth > 4:
        return EXE_UNKNOWN, "unresolvable"
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return (ABSOLUTE if os.path.dirname(node.value) else BARE), repr(node.value)
    if isinstance(node, ast.Call):
        d = _dotted(node.func, aliases) or ""
        if d in PATH_RESOLVERS or d.split(".")[-1] in ("which", "_spawnable"):
            return ABSOLUTE_IF_INSTALLED, d + "(...)"
        if d in ("os.path.join", "posixpath.join", "ntpath.join"):
            return ABSOLUTE, d + "(...)"
        return EXE_UNKNOWN, (d or type(node).__name__) + "(...)"
    if isinstance(node, ast.Attribute):
        d = _dotted(node, aliases) or ""
        if d in ("sys.executable",):
            return ABSOLUTE, d
        return EXE_UNKNOWN, d or "attribute"
    if isinstance(node, ast.IfExp):
        a, ha = _exe_state(node.body, func, tree, aliases, depth + 1)
        b, hb = _exe_state(node.orelse, func, tree, aliases, depth + 1)
        pair = {a, b}
        if pair == {ABSOLUTE}:
            return ABSOLUTE, "%s / %s" % (ha, hb)
        if pair == {BARE}:
            return BARE, "%s / %s" % (ha, hb)
        if pair <= {ABSOLUTE, ABSOLUTE_IF_INSTALLED, BARE} and ABSOLUTE in pair:
            return ABSOLUTE_IF_INSTALLED, "%s / %s" % (ha, hb)
        return EXE_UNKNOWN, "%s / %s" % (ha, hb)
    if isinstance(node, ast.Name):
        vals = _assigned_values(node.id, func, tree)
        if not vals:
            return EXE_UNKNOWN, node.id + " (never assigned in reach)"
        seen = [_exe_state(v, func, tree, aliases, depth + 1) for v in vals]
        states = {s for s, _ in seen}
        if len(states) == 1:
            return seen[0][0], "%s = %s" % (node.id, seen[0][1])
        if states <= {ABSOLUTE, ABSOLUTE_IF_INSTALLED}:
            return ABSOLUTE_IF_INSTALLED, node.id
        return EXE_UNKNOWN, node.id
    return EXE_UNKNOWN, type(node).__name__


def _argv0(node, func, tree, aliases, depth=0):
    """The first element of an argv expression. -> ast node or None"""
    if node is None or depth > 4:
        return None
    if isinstance(node, (ast.List, ast.Tuple)):
        return node.elts[0] if node.elts else None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _argv0(node.left, func, tree, aliases, depth + 1) or \
            _argv0(node.right, func, tree, aliases, depth + 1)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node                     # a plain string command
    if isinstance(node, ast.Name):
        vals = _assigned_values(node.id, func, tree)
        for v in vals:
            got = _argv0(v, func, tree, aliases, depth + 1)
            if got is not None:
                return got
    return None


def _literal(node):
    """-> (known, value). A non-literal expression is UNKNOWN, never assumed."""
    try:
        return True, ast.literal_eval(node)
    except Exception:
        return False, None


def _stream_verdict(node, aliases):
    """Does this stdin/stdout/stderr argument land the child's fd on 0, 1 or 2? -> 'ok'/'bad'/'?'"""
    known, val = _literal(node)
    if known:
        if val is None:
            return "ok"                                   # inherited -> the guard sees -1
        if isinstance(val, int):
            # PIPE(-1) / STDOUT(-2) / DEVNULL(-3) all produce a fresh fd or -1.
            return "bad" if 0 <= val <= 2 else "ok"
        return "?"
    d = _dotted(node, aliases) or ""
    if d.startswith("subprocess.") and d.split(".")[-1] in ("PIPE", "STDOUT", "DEVNULL"):
        return "ok"
    return "?"


def classify_spawn_call(call, func, tree, aliases):
    """THE ONE CLASSIFIER. Will CPython posix_spawn this call, or fork it? -> dict

    Returns {"verdict": FORKS|SPAWNS|UNKNOWN, "violations": [...], "unknowns": [...], "exe": ...}

    ⚠ ABSENCE IS A VALUE. `close_fds` defaults to **True**, so a call that never mentions it is
    violating the condition just as loudly as one that writes `close_fds=True`. That is the whole
    reason the v3429 presence-check passed six forking sites: it asked whether the word was there.
    [[a-law-about-a-row-must-drive-the-row]]
    """
    violations, unknowns, notes = [], [], []

    kws = {}
    star = False
    for k in call.keywords:
        if k.arg is None:
            star = True
        else:
            kws[k.arg] = k.value

    # ---- condition 1: the executable must have a dirname --------------------------------
    exe_node = kws.get("executable")
    how = ""
    if exe_node is None:
        shell_known, shell_val = _literal(kws["shell"]) if "shell" in kws else (True, False)
        if shell_known and shell_val:
            state, how = ABSOLUTE, "shell=True -> /bin/sh"
        else:
            pos = call.args[0] if call.args else None
            state, how = _exe_state(_argv0(pos, func, tree, aliases), func, tree, aliases)
    else:
        state, how = _exe_state(exe_node, func, tree, aliases)
    if state == BARE:
        violations.append("executable-has-a-dirname")
    elif state == EXE_UNKNOWN:
        unknowns.append("executable-has-a-dirname")
    elif state == ABSOLUTE_IF_INSTALLED:
        notes.append("dirname holds whenever the tool is installed (%s)" % how)

    # ---- condition 3: close_fds must be present AND False -------------------------------
    if "close_fds" not in kws:
        violations.append("close_fds-is-False")
        notes.append("close_fds is ABSENT and defaults to True")
    else:
        known, val = _literal(kws["close_fds"])
        if not known:
            unknowns.append("close_fds-is-False")
        elif val:
            violations.append("close_fds-is-False")

    # ---- conditions 2, 4, 5, 9 and the identity tail ------------------------------------
    for kw, must_be_falsy in (("preexec_fn", True), ("pass_fds", True), ("cwd", True),
                              ("start_new_session", True), ("user", True), ("group", True),
                              ("extra_groups", True)):
        if kw not in kws:
            continue
        known, val = _literal(kws[kw])
        if not known:
            # A non-literal cwd=ROOT / preexec_fn=f is a VALUE, and every value but None/falsy
            # violates. Only an expression that could legitimately be None is unknown.
            violations.append(KW_TO_CONDITION[kw])
            notes.append("%s=<expression> is not None" % kw)
        elif val:
            violations.append(KW_TO_CONDITION[kw])
    if "umask" in kws:
        known, val = _literal(kws["umask"])
        if not known:
            unknowns.append("umask-is-negative")
        elif not (isinstance(val, int) and val < 0):
            violations.append("umask-is-negative")
    if "process_group" in kws:
        known, val = _literal(kws["process_group"])
        if not known:
            unknowns.append("process_group-is-default")
        elif val != -1:
            violations.append("process_group-is-default")

    # ---- conditions 6, 7, 8: no standard stream may land on fd 0/1/2 --------------------
    for kw in ("stdin", "stdout", "stderr"):
        if kw not in kws:
            continue
        v = _stream_verdict(kws[kw], aliases)
        if v == "bad":
            violations.append(KW_TO_CONDITION[kw])
        elif v == "?":
            unknowns.append(KW_TO_CONDITION[kw])

    if star:
        unknowns.append("**kwargs could carry any of them")

    verdict = FORKS if violations else (UNKNOWN if unknowns else SPAWNS)
    return {"verdict": verdict, "violations": violations, "unknowns": unknowns,
            "exe": state, "how": how, "notes": notes}


def spawn_sites(src, where=HERE):
    """Every spawn door in `src`, classified. -> list of dicts (sorted by line)"""
    tree = ast.parse(src)
    aliases = _import_aliases(tree)
    doors = discover_spawn_doors(tree, where)
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    def enclosing_func(node):
        cur = parents.get(node)
        while cur is not None:
            if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return cur
            cur = parents.get(cur)
        return None

    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        d = _dotted(node.func, aliases)
        if d not in doors:
            continue
        got = classify_spawn_call(node, enclosing_func(node), tree, aliases)
        got["line"] = node.lineno
        got["door"] = d
        got["why_door"] = doors[d]
        out.append(got)
    return sorted(out, key=lambda r: r["line"])


# =========================================================================================
# 2. THE HOST PROBE — what this machine can and cannot be asked
# =========================================================================================

class _SyscallSpy(object):
    """Record which of fork_exec / posix_spawn CPython actually reaches for."""

    def __enter__(self):
        import _posixsubprocess
        self.counts = {"spawn": 0, "fork": 0}
        self._mod = _posixsubprocess
        self._rs, self._rf = os.posix_spawn, _posixsubprocess.fork_exec

        def spawn(*a, **k):
            self.counts["spawn"] += 1
            return self._rs(*a, **k)

        def fork(*a, **k):
            self.counts["fork"] += 1
            return self._rf(*a, **k)

        os.posix_spawn = spawn
        _posixsubprocess.fork_exec = fork
        return self

    def __exit__(self, *e):
        os.posix_spawn = self._rs
        self._mod.fork_exec = self._rf
        return False


def _probe_command():
    """An absolute, silent, instant command plus a bare spelling of it. -> (abs, args, bare)"""
    for cand, args in (("true", []), ("ps", ["-o", "pid="])):
        found = shutil.which(cand)
        if found:
            return found, args, cand
    return sys.executable, ["-c", ""], None


PROBE_ABS, PROBE_ARGS, PROBE_BARE = _probe_command()

MEASURED = "MEASURED"
NOT_APPLICABLE = "NOT-APPLICABLE"

# case name -> (state, reason). Written by `_record`; a completeness law reads it back.
LEDGER = {}
HOST_DEPENDENT = (
    "test_the_baseline_shape_REALLY_DOES_fork",
    "test_a_BARE_executable_name_still_forks",
    "test_the_corpse_row_takes_posix_spawn_and_never_forks",
)


def _record(case, state, reason):
    """Say, out loud, which word this case means. Never a silent skip, never a bare pass."""
    LEDGER[case] = (state, reason)
    sys.stderr.write("  [%s] %s :: %s\n" % (state, case, reason))
    sys.stderr.flush()
    return state


def _fork_count(argv, **kw):
    """Drive a real spawn and report (fork, spawn) or None if it could not run at all."""
    kw.setdefault("stdout", subprocess.DEVNULL)
    kw.setdefault("stderr", subprocess.DEVNULL)
    kw.setdefault("timeout", 20)
    try:
        with _SyscallSpy() as spy:
            try:
                subprocess.run(argv, **kw)
            except (OSError, subprocess.SubprocessError):
                pass                      # the SYSCALL choice is the measurement, not the exit code
            return spy.counts["fork"], spy.counts["spawn"]
    except Exception:
        return None


def _host_probe():
    """MEASURE this host's two control shapes instead of assuming them from sys.platform. -> dict

    ⚠ THE PREMISE CASES ARE macOS-SHAPED AND THE GATE SET RUNS ON ubuntu-latest. Rather than
    branch on the platform string and hope, both control shapes are driven here: the default
    (close_fds=True) which must fork, and the escape (absolute exe + close_fds=False) which must
    spawn. If this interpreter does not discriminate them, the premise cannot be pinned here and
    the honest word is UNKNOWN, not a pass. If it does discriminate but there is no Objective-C
    runtime on this platform, the hazard itself does not exist and the word is NOT-APPLICABLE.
    """
    default = _fork_count([PROBE_ABS] + PROBE_ARGS)
    escape = _fork_count([PROBE_ABS] + PROBE_ARGS, close_fds=False)
    objc = sys.platform == "darwin"
    info = {"platform": sys.platform, "objc_runtime": objc,
            "use_posix_spawn": bool(getattr(subprocess, "_USE_POSIX_SPAWN", False)),
            "default_shape": default, "escape_shape": escape, "probe": PROBE_ABS}
    if default is None or escape is None:
        info["verdict"] = UNKNOWN
        info["reason"] = ("neither control shape could be driven on this host (%r), so nothing "
                          "about fork vs posix_spawn was measured here" % (PROBE_ABS,))
    elif not (default[0] >= 1 and escape[1] >= 1 and escape[0] == 0):
        info["verdict"] = UNKNOWN
        info["reason"] = ("this interpreter does not separate the two shapes: default -> "
                          "fork=%d spawn=%d, escape -> fork=%d spawn=%d. The premise cannot be "
                          "pinned here." % (default + escape))
    elif not objc:
        info["verdict"] = NOT_APPLICABLE
        info["reason"] = ("%s has no Objective-C / Quartz runtime, so the fork-safety deadlock "
                          "this file exists to prevent cannot happen here. The syscall split WAS "
                          "measured (default fork=%d, escape spawn=%d); it is the HAZARD that is "
                          "absent, not the measurement." % (sys.platform, default[0], escape[1]))
    else:
        info["verdict"] = MEASURED
        info["reason"] = ("darwin, and both control shapes discriminate: default fork=%d, escape "
                          "spawn=%d" % (default[0], escape[1]))
    return info


HOST = _host_probe()


# =========================================================================================
# 3. THE LAWS
# =========================================================================================

class TestTheDoctorNeverForksAQuartzProcess(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        sys.stderr.write("\nHOST: %s | verdict=%s | %s\n"
                         % (HOST["platform"], HOST["verdict"], HOST["reason"]))

    # ---- driven on the real syscall ------------------------------------------------------

    def test_the_corpse_row_takes_posix_spawn_and_never_forks(self):
        """THE ONE THAT MATTERS. Not "does it pass the conditions" — does CPython take the
        non-forking path when this row actually runs."""
        case = "test_the_corpse_row_takes_posix_spawn_and_never_forks"
        import console_doctor as cd
        fn = dict(cd.CHECKS)["nothing we started is a corpse"]
        with _SyscallSpy() as spy:
            st, say = fn()
        if HOST["verdict"] == UNKNOWN:
            _record(case, UNKNOWN, "%s — the row was driven and took fork=%d spawn=%d, but this "
                                   "host cannot tell the two paths apart, so that pair grades "
                                   "nothing" % (HOST["reason"], spy.counts["fork"],
                                                spy.counts["spawn"]))
            self.assertGreaterEqual(spy.counts["fork"] + spy.counts["spawn"], 1,
                                    "the row spawned nothing at all, so this case measured "
                                    "nothing — 0 with no denominator")
            return
        _record(case, MEASURED, "fork=%d spawn=%d (%s)"
                % (spy.counts["fork"], spy.counts["spawn"],
                   "the hazard is real here" if HOST["objc_runtime"] else
                   "the syscall law still holds off darwin; only the DEADLOCK is macOS-only"))
        self.assertEqual(spy.counts["fork"], 0,
                         "the doctor still fork()s a Quartz-loaded process — that is the 28-minute "
                         "deadlock path, and it refused four pushes (%s)" % say)
        self.assertGreaterEqual(spy.counts["spawn"], 1,
                                "nothing was spawned at all, so this case measured nothing")

    def test_the_baseline_shape_REALLY_DOES_fork(self):
        """⚠ THE PREMISE, PINNED. If a future CPython made close_fds=True spawn anyway, the case
        above would pass for a reason that has nothing to do with this fix, and the comments here
        would be describing a hazard that no longer exists.

        ⚠ v3435 — AND IT SAYS WHICH WORD IT MEANS OFF darwin. The gate set runs on ubuntu-latest,
        where there is no Quartz to deadlock. The measurement is still taken and still printed;
        what changes is that it is recorded as NOT-APPLICABLE instead of graded as if the hazard
        were present. NOT a skip, NOT a bare pass."""
        case = "test_the_baseline_shape_REALLY_DOES_fork"
        got = _fork_count([PROBE_ABS] + PROBE_ARGS, stdout=subprocess.PIPE)
        self.assertIsNotNone(got, "the baseline shape could not be driven at all, so the premise "
                                  "is UNMEASURED rather than confirmed")
        if HOST["verdict"] == MEASURED:
            _record(case, MEASURED, "default shape -> fork=%d spawn=%d" % got)
            self.assertEqual(got[0], 1,
                             "the default shape no longer forks on this interpreter — re-measure "
                             "before trusting anything else in this file")
        else:
            _record(case, HOST["verdict"],
                    "default shape -> fork=%d spawn=%d, but %s" % (got[0], got[1], HOST["reason"]))
            self.assertGreaterEqual(sum(got), 1,
                                    "neither syscall was observed, so nothing was measured here "
                                    "— that is not the same as NOT-APPLICABLE")

    def test_a_BARE_executable_name_still_forks(self):
        """The dirname condition is half the fix and it is invisible: `close_fds=False` alone reads
        like a complete change and still forks."""
        case = "test_a_BARE_executable_name_still_forks"
        if PROBE_BARE is None:
            _record(case, UNKNOWN, "no PATH-resolvable probe command on this host, so the bare-name "
                                   "trap could not be driven")
            self.assertIsNone(PROBE_BARE)
            return
        got = _fork_count([PROBE_BARE] + PROBE_ARGS, close_fds=False, stdout=subprocess.PIPE)
        self.assertIsNotNone(got, "the bare-name shape could not be driven at all")
        if HOST["verdict"] == MEASURED:
            _record(case, MEASURED, "bare %r + close_fds=False -> fork=%d spawn=%d"
                    % (PROBE_BARE, got[0], got[1]))
            self.assertEqual(got[0], 1,
                             "a bare executable name no longer forks — the dirname condition "
                             "changed")
        else:
            _record(case, HOST["verdict"],
                    "bare %r -> fork=%d spawn=%d, but %s" % (PROBE_BARE, got[0], got[1],
                                                             HOST["reason"]))
            self.assertGreaterEqual(sum(got), 1,
                                    "neither syscall was observed for the bare-name shape")

    def test_every_host_dependent_case_said_which_word_it_meant(self):
        """⚠ UNKNOWN IS A STATE, AND A STATE HAS TO BE WRITTEN DOWN. A case that quietly returns
        leaves no trace at all, which reads exactly like a case that measured and agreed. This
        fails if any host-dependent case recorded nothing, or recorded a word outside the three.
        [[unknown-stays-unknown]]

        ⚠ IT DRIVES THE CASES RATHER THAN READING WHAT HAPPENED TO RUN FIRST. unittest orders
        methods by string sort, so the first version of this law ran BEFORE two of the three cases
        it grades and reported them missing. A law that depends on its neighbours' run order is
        measuring the sort, not the behaviour. [[a-law-about-a-row-must-drive-the-row]]"""
        suite = unittest.TestSuite(TestTheDoctorNeverForksAQuartzProcess(n)
                                   for n in HOST_DEPENDENT)
        buf = io.StringIO()
        res = unittest.TextTestRunner(stream=buf, verbosity=0).run(suite)
        self.assertEqual(res.errors, [], "a host-dependent case ERRORED when driven directly, so "
                                         "its state was never written: %r" % (res.errors,))
        missing = [c for c in HOST_DEPENDENT if c not in LEDGER]
        self.assertEqual(missing, [], "these host-dependent cases recorded no state at all, so "
                                      "nobody can tell whether they measured or declined: %r"
                                      % (missing,))
        bad = {c: LEDGER[c] for c in HOST_DEPENDENT
               if LEDGER[c][0] not in (MEASURED, NOT_APPLICABLE, UNKNOWN) or not LEDGER[c][1]}
        self.assertEqual(bad, {}, "a host-dependent case recorded a word that is not one of "
                                  "MEASURED / NOT-APPLICABLE / UNKNOWN, or gave no reason: %r"
                                  % (bad,))

    # ---- the instrument, watching itself -------------------------------------------------

    def test_the_syscall_spy_sees_the_name_subprocess_actually_calls(self):
        """⚠ SUSPECT THE INSTRUMENT FIRST. The spy patches `os.posix_spawn` and
        `_posixsubprocess.fork_exec`. If `subprocess` ever binds either at import time
        (`from _posixsubprocess import fork_exec`), the patch would land on a name nobody reads and
        every case in this file would report fork=0 forever — a green measuring nothing."""
        src = inspect.getsource(subprocess.Popen._execute_child)
        self.assertIn("_posixsubprocess.fork_exec", src,
                      "subprocess no longer calls `_posixsubprocess.fork_exec` by that dotted "
                      "name, so the spy is patching a name it does not read — every fork=0 in "
                      "this file is now unmeasured, not clean")
        self.assertIn("os.posix_spawn", inspect.getsource(subprocess.Popen._posix_spawn),
                      "subprocess no longer calls `os.posix_spawn` by that dotted name")

    # ---- the classifier, pinned to CPython rather than to memory ------------------------

    def test_the_classifier_covers_every_condition_CPYTHON_ACTUALLY_CHECKS(self):
        """⚠ THE REASON THIS GATE WAS BLIND: IT RECORDED TWO CONDITIONS AND CPYTHON CHECKS
        FOURTEEN. The count is not a number anybody types here — `Popen._execute_child` is parsed
        on the running interpreter and every identifier its posix_spawn gate reads must map to a
        condition this file classifies. A new CPython condition turns this RED instead of quietly
        widening the blind spot."""
        got = _cpython_guard_vars()
        self.assertIsNotNone(got, "the posix_spawn guard's source was not readable on this "
                                  "interpreter, so how many conditions it checks is UNKNOWN — "
                                  "this file's classifier is unverified, not verified")
        uncovered = sorted(v for v in got if v not in GUARD_VAR_TO_CONDITION)
        self.assertEqual(uncovered, [], "CPython's posix_spawn guard reads condition variable(s) "
                                        "%r that this classifier does not model, so a call "
                                        "violating one of them would be graded SPAWNS and would "
                                        "fork" % (uncovered,))
        self.assertGreaterEqual(len(got), 9, "the guard reported only %d condition variables, "
                                             "which is fewer than the nine this file names — the "
                                             "extractor is the suspect, not CPython" % len(got))
        for c in NINE_CONDITIONS:
            self.assertIn(c, set(GUARD_VAR_TO_CONDITION.values()),
                          "%r is named as one of the nine but no guard variable maps to it" % c)

    def test_the_receiver_is_a_DOTTED_name_so_two_run_functions_stay_two(self):
        """⚠ `subprocess.run` AND `_gq.run` ARE BOTH CALLED `run`. The v3429 gate matched on the
        RECEIVER SPELLING (`subprocess` / `_sp` / `sp`) and skipped `_gq` entirely; the obvious
        widening — allow the attribute `run` — would admit every unrelated `.run()` in the file.
        Aliases are resolved to dotted module names, so the two stay distinguishable.
        [[a-widened-guard-admits-what-it-bans]]"""
        tree = ast.parse("import subprocess as _sp\nimport git_quiet as _gq\n"
                         "class T:\n    def run(self): pass\n"
                         "_sp.run(['/bin/true'])\n_gq.run(['git'])\nT().run()\nself.runner.run()\n")
        aliases = _import_aliases(tree)
        names = [_dotted(n.func, aliases) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertIn("subprocess.run", names)
        self.assertIn("git_quiet.run", names)
        self.assertNotEqual("subprocess.run", "git_quiet.run")
        self.assertIn("self.runner.run", names,
                      "an unrelated `.run()` must still resolve to its OWN dotted name so it can "
                      "be excluded by name rather than by hope")
        doors = discover_spawn_doors(tree)
        self.assertNotIn("self.runner.run", doors,
                         "an unrelated `.run()` was admitted as a spawn door — that is the "
                         "cry-wolf failure of widening on the bare attribute")

    def test_the_wrapper_door_is_DISCOVERED_not_listed(self):
        """⚠ A LIST OF WRAPPERS IS A LIST OF THE ONES SOMEBODY REMEMBERED. `git_quiet.run` is found
        by reading git_quiet.py and seeing that it forwards its own `**kwargs` into
        `subprocess.run` — so the next one-door wrapper is a door the moment it is imported.

        This also fails if the discovery finds NOTHING, which is the shape a blind gate takes."""
        tree = ast.parse(SRC)
        doors = discover_spawn_doors(tree)
        self.assertIn("subprocess.run", doors, "the direct subprocess door was not discovered at "
                                               "all — the classifier is blind, not clean")
        self.assertIn("git_quiet.run", doors,
                      "git_quiet.run is no longer recognised as a subprocess wrapper, so the six "
                      "git spawns in console_doctor are invisible again. Discovered doors: %r"
                      % (sorted(doors),))
        self.assertTrue(doors["git_quiet.run"].startswith("wrapper"),
                        "git_quiet.run was admitted for the wrong reason: %r"
                        % doors["git_quiet.run"])
        with io.open(os.path.join(HERE, "git_quiet.py"),
                     encoding="utf-8", errors="replace") as fh:
            gq = ast.parse(fh.read())
        injects = [k.arg for n in ast.walk(gq) if isinstance(n, ast.Call)
                   for k in n.keywords if k.arg == "close_fds"]
        self.assertEqual(injects, [], "git_quiet now sets close_fds itself, which changes who is "
                                      "responsible for that condition — this classifier grades "
                                      "the CALL SITE and would start crying wolf")

    def test_the_classifier_goes_FORKING_on_each_condition_ALONE(self):
        """⚠ A CLASSIFIER NOBODY SAW SAY NO IS A CLASSIFIER THAT SAYS YES. One synthetic call per
        condition, violating that condition and nothing else, must come back FORKS — and the
        control, violating none, must come back SPAWNS."""
        head = "import subprocess\n"
        control = "subprocess.run(['/bin/true'], close_fds=False)"

        def verdict(expr):
            tree = ast.parse(head + expr + "\n")
            sites = spawn_sites(head + expr + "\n")
            self.assertEqual(len(sites), 1, "the probe %r produced %d sites, not 1 — the SABOTAGE "
                                            "is the suspect" % (expr, len(sites)))
            del tree
            return sites[0]

        got = verdict(control)
        self.assertEqual(got["verdict"], SPAWNS,
                         "the CONTROL call was not classified spawn-eligible (%r), so every red "
                         "below would be attributable to the control, not to the condition"
                         % (got,))

        # ⚠ ABSENCE AND VALUE ARE TWO DIFFERENT SHAPES OF THE SAME VIOLATION, AND ONLY ONE OF
        # THEM WAS THE v3429 DEFECT. MEASURED: sabotaging the classifier back to the old
        # presence-only test left this law GREEN, because its close_fds probe omitted the keyword
        # — the branch that reads the VALUE was never reached. Cause (b): the test could not reach
        # the line, not a weak guard. Both shapes are probed now.
        # [[a-law-about-a-row-must-drive-the-row]]
        probes = {
            "executable-has-a-dirname": [
                "subprocess.run(['true'], close_fds=False)",
                "subprocess.run(['/bin/sh'], close_fds=False, executable='true')",
            ],
            "preexec_fn-is-None": [
                "subprocess.run(['/bin/true'], close_fds=False, preexec_fn=len)"],
            "close_fds-is-False": [
                "subprocess.run(['/bin/true'])",                        # ABSENT -> defaults True
                "subprocess.run(['/bin/true'], close_fds=True)",        # PRESENT and True
            ],
            "no-pass_fds": ["subprocess.run(['/bin/true'], close_fds=False, pass_fds=(7,))"],
            "cwd-is-None": ["subprocess.run(['/bin/true'], close_fds=False, cwd='/tmp')"],
            "stdin-is-not-fd-0-1-2": ["subprocess.run(['/bin/true'], close_fds=False, stdin=0)"],
            "stdout-is-not-fd-0-1-2": ["subprocess.run(['/bin/true'], close_fds=False, stdout=1)"],
            "stderr-is-not-fd-0-1-2": ["subprocess.run(['/bin/true'], close_fds=False, stderr=2)"],
            "start_new_session-is-falsy": [
                "subprocess.run(['/bin/true'], close_fds=False, start_new_session=True)"],
            "user-is-None": ["subprocess.run(['/bin/true'], close_fds=False, user=501)"],
            "group-is-None": ["subprocess.run(['/bin/true'], close_fds=False, group=20)"],
            "extra_groups-is-None": [
                "subprocess.run(['/bin/true'], close_fds=False, extra_groups=[20])"],
            "umask-is-negative": ["subprocess.run(['/bin/true'], close_fds=False, umask=0o022)"],
            "process_group-is-default": [
                "subprocess.run(['/bin/true'], close_fds=False, process_group=0)"],
        }
        self.assertEqual(len(probes["close_fds-is-False"]), 2,
                         "close_fds must be probed BOTH absent AND present-but-True — the "
                         "present-but-True shape is the one the v3429 gate could not see")
        for cond in sorted(set(GUARD_VAR_TO_CONDITION.values())):
            self.assertIn(cond, probes, "condition %r has no probe, so it was never seen refuse"
                          % cond)
            for expr in probes[cond]:
                got = verdict(expr)
                self.assertEqual(got["verdict"], FORKS,
                                 "violating %r ALONE (%s) was not classified FORKS: %r"
                                 % (cond, expr, got))
                self.assertEqual(got["violations"], [cond],
                                 "%s was classified as violating %r — the probe is impure, so "
                                 "the red is not attributable to %r"
                                 % (expr, got["violations"], cond))

    def test_the_classifier_agrees_with_the_REAL_SYSCALL_on_each_condition(self):
        """⚠ CLASSIFY, THEN DRIVE. An AST predicate that nobody ever compared against the
        interpreter is arithmetic about behaviour. Each condition is violated for real, once, and
        the syscall CPython takes is recorded next to what the classifier said.

        ⚠ TWO ARE NOT DRIVABLE AND SAY SO. `extra_groups` needs setgroups() (root), and `pass_fds`
        cannot be isolated at runtime because `Popen.__init__` FORCES close_fds=True when it is
        set — so it would prove two conditions at once, not one. Those stay classifier-only and
        are recorded as such rather than quietly counted as driven."""
        if HOST["verdict"] == UNKNOWN:
            _record("test_the_classifier_agrees_with_the_REAL_SYSCALL_on_each_condition",
                    UNKNOWN, HOST["reason"])
            self.skipTest("host cannot discriminate fork from spawn: " + HOST["reason"])
        base = [PROBE_ABS] + PROBE_ARGS
        bare = ([PROBE_BARE] + PROBE_ARGS) if PROBE_BARE else None
        supported = set(inspect.signature(subprocess.Popen.__init__).parameters)

        drivable = [
            ("executable-has-a-dirname", bare, {"close_fds": False}),
            ("preexec_fn-is-None", base, {"close_fds": False, "preexec_fn": os.getpid}),
            ("close_fds-is-False", base, {}),
            ("cwd-is-None", base, {"close_fds": False, "cwd": "/"}),
            ("stdin-is-not-fd-0-1-2", base, {"close_fds": False, "stdin": 2}),
            ("stdout-is-not-fd-0-1-2", base, {"close_fds": False, "stdout": 2}),
            ("stderr-is-not-fd-0-1-2", base, {"close_fds": False, "stderr": 2}),
            ("start_new_session-is-falsy", base, {"close_fds": False, "start_new_session": True}),
            ("umask-is-negative", base, {"close_fds": False, "umask": 0o022}),
            ("user-is-None", base, {"close_fds": False, "user": os.getuid()}),
            ("group-is-None", base, {"close_fds": False, "group": os.getgid()}),
        ]
        driven, declined = [], []
        for cond, argv, kw in drivable:
            if argv is None:
                declined.append((cond, "no PATH-resolvable probe command on this host"))
                continue
            need = {"user": "user", "group": "group", "umask": "umask"}
            missing = [k for k in kw if k in need and k not in supported]
            if missing:
                declined.append((cond, "CPython %s has no %r keyword" % (sys.version.split()[0],
                                                                        missing)))
                continue
            got = _fork_count(list(argv), **dict(kw))
            if got is None:
                declined.append((cond, "the shape could not be driven"))
                continue
            self.assertEqual(got[0], 1,
                             "violating %r did NOT make CPython fork: fork=%d spawn=%d. Either "
                             "this interpreter dropped the condition, or the TEST could not reach "
                             "it, or the sabotage was inert — diagnose which before changing the "
                             "classifier." % (cond, got[0], got[1]))
            driven.append(cond)

        _record("classifier-vs-syscall", MEASURED,
                "%d condition(s) driven on the real syscall: %s%s"
                % (len(driven), ", ".join(driven),
                   ("; DECLINED: %r" % (declined,)) if declined else ""))
        self.assertGreaterEqual(len(driven), 8,
                                "only %d conditions were driven on the real syscall (declined: "
                                "%r) — a classifier compared against almost nothing is arithmetic"
                                % (len(driven), declined))
        # The two that cannot be isolated at runtime, said out loud rather than counted as driven.
        _record("conditions-not-drivable", NOT_APPLICABLE,
                "extra_groups needs setgroups()/root; pass_fds forces close_fds=True inside "
                "Popen.__init__ so it can never violate alone. Both are classifier-only.")

    # ---- the class law, now able to see what it was skipping -----------------------------

    def test_EVERY_subprocess_call_in_the_doctor_is_spawn_eligible(self):
        """A law about one row would have the reach the fix did. Any NEW shell-out added to this
        module is a new deadlock site unless every condition holds.

        ⚠ v3435 — THIS READS ALL FOURTEEN CONDITIONS AND EVERY DOOR, INCLUDING THE WRAPPER. The
        v3429 version asked only whether the word `close_fds` appeared, and only of receivers
        spelled `subprocess`/`_sp`/`sp` — so `_gq.run(..., cwd=ROOT)` was skipped six times over,
        and `bad` came back `[]` while six live git spawns forked on every eagle tick."""
        sites = spawn_sites(SRC)
        self.assertGreaterEqual(len(sites), 10,
                                "only %d spawn sites were found in console_doctor — the walker "
                                "is the suspect, not the file (a law that matches nothing passes "
                                "forever)" % len(sites))
        forking = [s for s in sites if s["verdict"] == FORKS]
        report = "\n".join(
            "    line %-6d %-16s violates %s%s"
            % (s["line"], s["door"], ", ".join(s["violations"]),
               ("  [%s]" % "; ".join(s["notes"])) if s["notes"] else "")
            for s in forking)
        self.assertEqual(
            forking, [],
            "%d spawn site(s) in console_doctor.py FORK a process that has the Objective-C "
            "runtime loaded — the 28-minute hang:\n%s\n"
            "⚠ `cwd=` is condition six of CPython's posix_spawn gate and a bare `git` fails the "
            "dirname condition; both are as fatal as a missing close_fds.\n"
            "THE SHAPE THIS CLASSIFIER CAN VERIFY, per site:\n"
            "    _gq.run([_spawnable(\"git\"), \"-C\", ROOT, ...], close_fds=False, ...)\n"
            "  · `git -C <dir>` replaces `cwd=<dir>` — same directory, no cwd keyword.\n"
            "  · `_spawnable(\"git\")` gives argv[0] a dirname. ⚠ Resolving git INSIDE git_quiet\n"
            "    instead would be invisible from the call site and this gate would report the\n"
            "    site UNKNOWN, not green — a fix the reader cannot see is not one it can grade.\n"
            "  · `close_fds=False` is still the call site\'s to declare: git_quiet forwards **kw\n"
            "    and injects nothing on POSIX (pinned by test_the_wrapper_door_is_DISCOVERED)."
            % (len(forking), report))

    def test_no_spawn_site_in_the_doctor_is_UNCLASSIFIABLE(self):
        """⚠ UNKNOWN IS NOT GREEN. A site the classifier cannot read is a site nobody has graded,
        and folding it into the pass column is exactly how `bad == []` meant nothing. It gets its
        own verdict so a real blind spot cannot hide behind a clean forking count.
        [[unknown-stays-unknown]]"""
        sites = spawn_sites(SRC)
        # ⚠ ZERO NEEDS A DENOMINATOR. MEASURED: forcing the walker to match nothing left this law
        # GREEN — "0 unclassifiable of 0 sites" reads exactly like "0 of 12". Cause (a), a blind
        # guard, and the population is now part of the verdict. [[zero-needs-a-denominator]]
        self.assertGreaterEqual(len(sites), 10,
                                "only %d spawn sites were examined, so '0 unclassifiable' is a "
                                "statement about an empty population" % len(sites))
        unknown = [s for s in sites if s["verdict"] == UNKNOWN]
        report = "\n".join("    line %-6d %-16s unknown: %s"
                           % (s["line"], s["door"], ", ".join(s["unknowns"])) for s in unknown)
        self.assertEqual(unknown, [], "%d of %d spawn site(s) in console_doctor.py cannot be "
                                      "classified either way, so whether they fork is "
                                      "UNMEASURED:\n%s" % (len(unknown), len(sites), report))

    def test_the_class_law_would_SEE_a_cwd_added_to_any_door(self):
        """⚠ THE v3429 GATE WENT GREEN ON SIX FORKING SITES, so "it passes" is not evidence that it
        can fail. This drives the classifier over a synthetic copy of each door shape carrying the
        exact defect that was invisible — `cwd=` on a wrapper call — and requires FORKS."""
        for door in ("subprocess.run", "_sp.run", "_gq.run"):
            src = ("import subprocess\nimport subprocess as _sp\nimport git_quiet as _gq\n"
                   "%s(['/bin/git', 'status'], close_fds=False, cwd='/tmp')\n" % door)
            sites = spawn_sites(src)
            self.assertEqual(len(sites), 1, "%s was not recognised as a spawn door at all" % door)
            self.assertEqual(sites[0]["verdict"], FORKS,
                             "%s(..., cwd=...) was not classified as forking: %r"
                             % (door, sites[0]))
            self.assertIn("cwd-is-None", sites[0]["violations"])


RED_PROOF = [
    {
        "why": "v3429 - close_fds REMOVED. CPython takes posix_spawn only when close_fds is false, "
               "and it DEFAULTS TO TRUE - so dropping the keyword silently restores the fork that "
               "deadlocked for 28 minutes at 0% CPU and refused four pushes.",
        "file": "console_doctor.py",
        "find": "                      close_fds=False, timeout=15).stdout.decode(\"utf-8\", \"replace\")",
        "replace": "                      timeout=15).stdout.decode(\"utf-8\", \"replace\")",
        "matches": 1,
    },
    {
        "why": "v3429 - THE ABSOLUTE PATH REMOVED. The other half, and the invisible one: with a "
               "bare name the executable has no dirname, CPython's gate fails, and it forks again "
               "while close_fds=False makes the call LOOK fixed.",
        "file": "console_doctor.py",
        "find": "    _PS = \"/bin/ps\" if os.path.exists(\"/bin/ps\") else \"ps\"",
        "replace": "    _PS = \"ps\"",
        "matches": 1,
    },
    {
        "why": "v3435 - close_fds SET TO TRUE RATHER THAN REMOVED. This is the tamper the v3429 "
               "gate could not see at all: it asked `if \"close_fds\" not in kws`, which is a "
               "PRESENCE test, so `close_fds=True` - the literal fork - read as compliant. The "
               "classifier now reads the VALUE, and this proof fails if it ever stops doing so.",
        "file": "console_doctor.py",
        "find": "        p = _sp.run([_spawnable(\"gh\"), \"api\", \"rate_limit\"], capture_output=True,\n"
                "                    encoding=\"utf-8\", errors=\"replace\", close_fds=False, timeout=12)",
        "replace": "        p = _sp.run([_spawnable(\"gh\"), \"api\", \"rate_limit\"], capture_output=True,\n"
                   "                    encoding=\"utf-8\", errors=\"replace\", close_fds=True, timeout=12)",
        "matches": 1,
    },
    {
        "why": "v3435 - A cwd= ADDED TO A DIRECT subprocess CALL. cwd is condition SIX of "
               "CPython's posix_spawn gate and the v3429 gate never looked at it, which is how "
               "six `_gq.run(..., cwd=ROOT)` git spawns sat forking in a LIVE doctor row. The "
               "classifier must go red on a cwd anywhere, not only on the wrapper.",
        "file": "console_doctor.py",
        "find": "        frames = subprocess.run([_spawnable(\"du\"), \"-sk\", os.path.join(HERE, \"frames\")],\n"
                "                                capture_output=True, text=True, close_fds=False,\n"
                "                                timeout=60)",
        "replace": "        frames = subprocess.run([_spawnable(\"du\"), \"-sk\", os.path.join(HERE, \"frames\")],\n"
                   "                                capture_output=True, text=True, close_fds=False,\n"
                   "                                cwd=HERE, timeout=60)",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
