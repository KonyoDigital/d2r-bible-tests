# -*- coding: utf-8 -*-
"""v3772 (REG-2293) - WHAT A GATE ACTUALLY READ, written while it runs.

run_gates puts this folder first on PYTHONPATH when the ledger is on, and names a trace file in
TV_GATE_TRACE. Python imports `sitecustomize` before the gate's own script, so an audit hook is in
place before the first byte of the gate is opened. Each line is `KIND<TAB>PID<TAB>TEXT`:

    B  this process started (TEXT is the parent pid)
    R  opened for reading        S  stat'ed (exists/isfile/getsize)   A  stat'ed and absent
    W  opened for writing, or made by rename, copy, mkdir or link
    L  listed (listdir, scandir, glob, walk)                  I  imported a top-level module name
    P  started a python child that will trace itself
    G  ran `git check-ignore`, so every .gitignore is an input
    U  did something this trace cannot follow (a non-python child, a child without the trace env)

A git child aimed outside this checkout (a fixture repository in a tempdir) is not a read of it.
lsof, ps and pgrep read the process table and no file in this checkout, unless an argument
names one. `git ls-files` is a listing of the whole tracked set. `git rev-parse --show-toplevel` reads nothing
that a commit can move. Any other git command reads history or the index, and is a U.

Only paths under TV_GATE_TRACE_ROOT are written, repo-relative. A listing made by the import system
itself is not a listing by the gate. Lines go straight to an O_APPEND descriptor, so a forked child,
os._exit and a kill keep what was already seen. gate_ledger.read_trace() turns this into an input
set, and a gate with any U line, or with no B line for a child it started, is never carried.
After installing the hook, the next `sitecustomize` on sys.path (the system's own) still runs.
"""
import os
import sys


def _boot():
    out = os.environ.get("TV_GATE_TRACE") or ""
    root = os.environ.get("TV_GATE_TRACE_ROOT") or ""
    if not out or not root:
        return
    try:
        fd = os.open(out, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    except OSError:
        return
    roots = []
    for cand in (root, os.path.realpath(root)):
        cand = os.path.normpath(cand)
        if cand not in roots:
            roots.append(cand)
    here = os.path.dirname(os.path.abspath(__file__))
    state = {"pid": os.getpid(), "busy": False, "n": 0}
    seen = set()
    write = os.write
    getcwd = os.getcwd
    fsdecode = os.fsdecode
    isabs = os.path.isabs
    join = os.path.join
    normpath = os.path.normpath
    sep = os.sep
    getframe = sys._getframe
    stdlib = frozenset(getattr(sys, "stdlib_module_names", ())) | frozenset(sys.builtin_module_names) | frozenset(
        ("sitecustomize", "usercustomize", "apport_python_hook"))
    wflags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND

    def emit(kind, text, once=True):
        if once:
            key = (kind, text)
            if key in seen:
                return
            seen.add(key)
        line = "%s\t%d\t%s\n" % (kind, state["pid"], text.replace("\n", " ").replace("\t", " "))
        try:
            write(fd, line.encode("utf-8", "surrogateescape"))
        except OSError:
            pass

    def rel(path):
        if path is None:
            path = "."
        if isinstance(path, int):
            return None
        try:
            path = fsdecode(path)
        except Exception:
            return None
        if not isabs(path):
            path = join(getcwd(), path)
        path = normpath(path)
        for base in roots:
            if path == base:
                return ""
            if path.startswith(base + sep):
                out_rel = path[len(base) + 1:].replace(sep, "/")
                if out_rel.startswith("tv/gate_trace/") or "__pycache__" in out_rel.split("/"):
                    return None
                return out_rel
        return None

    def by_importer():
        try:
            frame = getframe(2)
        except Exception:
            return False
        depth = 0
        while frame is not None and depth < 12:
            name = frame.f_code.co_filename
            if name.startswith("<frozen importlib") or name.endswith(("importlib/_bootstrap_external.py",
                                                                      "pkgutil.py", "zipimport.py")):
                return True
            frame = frame.f_back
            depth += 1
        return False

    def from_subprocess():
        try:
            return getframe(2).f_code.co_filename.endswith("subprocess.py")
        except Exception:
            return False

    def git_child(args, env, cwd):
        """A git child that only names tracked paths, or one aimed at another repository. -> bool (handled)"""
        where = cwd
        rest = list(args[1:])
        while rest and rest[0].startswith("-"):
            flag = rest.pop(0)
            if flag in ("-C", "-c") and rest:
                value = rest.pop(0)
                if flag == "-C":
                    where = join(fsdecode(where) if where else getcwd(), value)
            elif flag.startswith("--git-dir") or flag.startswith("--work-tree"):
                return False
        source = env if env is not None else os.environ
        try:
            if any(source.get(k) for k in ("GIT_DIR", "GIT_WORK_TREE")):
                return False
        except Exception:
            return False
        if rel(where if where is not None else getcwd()) is None:
            return True  # a fixture repository outside this checkout
        sub = rest[0] if rest else ""
        opts = rest[1:]
        if sub == "ls-files" and not any(o.startswith(("-o", "--others", "-m", "--modified", "-d", "--deleted",
                                                         "-s", "--stage", "--with-tree", "--error-unmatch"))
                                         for o in opts):
            emit("L", "")  # the tracked set: any added or deleted file
            return True
        if sub == "rev-parse" and opts and all(o in ("--show-toplevel", "--git-dir", "--is-inside-work-tree",
                                                     "--show-cdup", "--show-prefix", "--git-common-dir")
                                               for o in opts):
            return True
        if sub == "init":
            paths = [o for o in opts if not o.startswith("-")]
            base = fsdecode(where) if where is not None else getcwd()
            if paths and rel(join(base, paths[-1])) is None:
                return True  # a new fixture repository outside this checkout
        if sub == "check-ignore":
            emit("G", "")  # every .gitignore
            return True
        return False

    def child(argv, env, cwd=None):
        args = [str(a) for a in (argv if isinstance(argv, (list, tuple)) else [argv or ""])]
        head = os.path.basename(args[0]) if args else ""
        if head == "git" and git_child(args, env, cwd):
            return
        if head in ("lsof", "ps", "pgrep") and not any(
                rel(a) is not None for a in args[1:] if "/" in a):
            return  # the process table, not a file in this checkout
        is_py = bool(args) and (args[0] == sys.executable or head.startswith("python"))
        if env is not None:
            try:
                traced = env.get("TV_GATE_TRACE") == out or env.get(b"TV_GATE_TRACE") == out.encode()
            except Exception:
                traced = False
        else:
            traced = True
        if is_py and traced and not any(a in ("-I", "-E", "-S") for a in args[1:4]):
            state["n"] += 1
            emit("P", "%d" % state["n"], once=False)
            return
        emit("U", "started %s" % (head or "a process"))

    def hook(event, args):
        if state["busy"]:
            return
        state["busy"] = True
        try:
            if event == "open":
                path = args[0]
                mode = args[1] if len(args) > 1 else None
                flags = args[2] if len(args) > 2 else 0
                r = rel(path)
                if r is None:
                    return
                writes = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                    mode is None and isinstance(flags, int) and flags & wflags)
                if writes:
                    emit("W", r)
                if not writes or (isinstance(mode, str) and "+" in mode) or (
                        mode is None and isinstance(flags, int) and flags & os.O_RDWR):
                    emit("R", r)
            elif event in ("os.listdir", "os.scandir"):
                r = rel(args[0] if args else None)
                if r is not None and not by_importer():
                    emit("L", r)
            elif event in ("glob.glob", "glob.glob/2"):
                pat = args[0] if args else None
                if isinstance(pat, (str, bytes)):
                    r = rel(os.path.dirname(fsdecode(pat)) or ".")
                    if r is not None:
                        emit("L", r)
            elif event in ("os.rename", "shutil.copyfile", "shutil.copytree", "shutil.move"):
                if len(args) > 1:
                    if event != "os.rename":
                        r = rel(args[0])
                        if r is not None:
                            emit("R", r)
                    r = rel(args[1])
                    if r is not None:
                        emit("W", r)  # a file this run made is not state it found
            elif event in ("os.mkdir", "os.symlink", "os.link"):
                r = rel(args[1] if event != "os.mkdir" and len(args) > 1 else args[0])
                if r is not None:
                    emit("W", r)
            elif event == "import":
                name = str(args[0] or "").split(".")[0]
                if name and name not in stdlib:
                    emit("I", name)
            elif event == "subprocess.Popen":
                exe, argv, cwd, env = (list(args) + [None] * 4)[:4]
                child(argv if argv else [exe], env, cwd)
            elif event in ("os.posix_spawn", "os.exec"):
                if not from_subprocess():
                    path, argv, env = (list(args) + [None] * 3)[:3]
                    child(argv if argv else [path], env)
            elif event in ("os.system", "os.spawn", "os.startfile", "pty.spawn"):
                emit("U", "started %s" % event)
        except Exception:
            emit("U", "the trace hook raised")
        finally:
            state["busy"] = False

    def stat_wrap(real):
        def wrapped(path, *a, **k):
            if state["busy"] or k.get("dir_fd") is not None:
                return real(path, *a, **k)
            try:
                out_stat = real(path, *a, **k)
            except FileNotFoundError:
                note(path, "A")
                raise
            note(path, "S")
            return out_stat
        wrapped.__wrapped__ = real
        return wrapped

    def note(path, kind):
        state["busy"] = True
        try:
            r = rel(path)
            if r is not None:
                emit(kind, r)
        except Exception:
            pass
        finally:
            state["busy"] = False

    def after_fork():
        parent = state["pid"]
        state["pid"] = os.getpid()
        seen.clear()
        emit("B", "%d" % parent)

    emit("B", "%d" % os.getppid())
    os.stat = stat_wrap(os.stat)
    os.lstat = stat_wrap(os.lstat)
    if hasattr(os, "register_at_fork"):
        os.register_at_fork(after_in_child=after_fork)
    sys.addaudithook(hook)
    return here


def _chain(here):
    """Run the sitecustomize this one shadows, so the system's own hook still loads."""
    try:
        import importlib.machinery
        import importlib.util
        path = [p for p in sys.path if os.path.abspath(p or ".") != here]
        spec = importlib.machinery.PathFinder.find_spec("sitecustomize", path)
        if spec is None or spec.loader is None:
            return
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception:
        pass


_chain(_boot() or os.path.dirname(os.path.abspath(__file__)))
