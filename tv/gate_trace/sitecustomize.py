# -*- coding: utf-8 -*-
"""v3772 (REG-2293) - WHAT A GATE ACTUALLY READ, written while it runs.

run_gates puts this folder first on PYTHONPATH when the ledger is on, and names a trace file in
TV_GATE_TRACE. Python imports `sitecustomize` before the gate's own script, so an audit hook is in
place before the first byte of the gate is opened. Each line is `KIND<TAB>PID<TAB>TEXT`:

    B  this process started (TEXT is the parent pid)
    R  opened for reading        W  opened for writing       S  stat'ed (exists/isfile/getsize)
    L  listed (listdir, scandir, glob, walk)                  I  imported a top-level module name
    P  started a python child that will trace itself
    U  did something this trace cannot follow (a non-python child, a child without the trace env)

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

    def child(argv, env):
        args = [str(a) for a in (argv if isinstance(argv, (list, tuple)) else [argv or ""])]
        head = os.path.basename(args[0]) if args else ""
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
            elif event == "import":
                name = str(args[0] or "").split(".")[0]
                if name and name not in stdlib:
                    emit("I", name)
            elif event == "subprocess.Popen":
                exe, argv, _cwd, env = (list(args) + [None] * 4)[:4]
                child(argv if argv else [exe], env)
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
            if not state["busy"] and k.get("dir_fd") is None:
                state["busy"] = True
                try:
                    r = rel(path)
                    if r is not None:
                        emit("S", r)
                except Exception:
                    pass
                finally:
                    state["busy"] = False
            return real(path, *a, **k)
        wrapped.__wrapped__ = real
        return wrapped

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
