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

A node child carries node_trace.cjs (NODE_OPTIONS --require), which writes the same lines.
A git child aimed outside this checkout (a fixture repository in a tempdir) is not a read of it.
lsof, ps and pgrep read the process table and no file in this checkout, unless an argument
names one. `git ls-files` is a listing of the whole tracked set. `git rev-parse --show-toplevel` reads nothing
that a commit can move. Any other git command reads history or the index, and is a U.

Only paths under TV_GATE_TRACE_ROOT are written, repo-relative. A listing made by the import system
itself is not a listing by the gate. Lines go straight to an O_APPEND descriptor, so a forked child,
os._exit and a kill keep what was already seen. gate_ledger.read_trace() turns this into an input
set, and a gate with any U line, or with no B line for a child it started, is never carried.
After installing the hook, the next `sitecustomize` on sys.path (the system's own) still runs.

REG-2350 (#42 R5) - THE KILL WATCH, armed by TV_GATE_KILLS alone (heart2 arms it on every proof run), into its
own file, in the same line shape:

    K  a child this process waited on or polled ENDED BY A SIGNAL (TEXT: pid, pgid when known, sig, argv0 name)
    X  this process SENT a signal (os.kill / os.killpg; a 0 probe is not one): `pid=N`, `pgid=N` or `all`

heart2 reads the pair: a K that no X of the same run explains is a kill from OUTSIDE the run (a by-pid reap, jetsam,
a Ctrl-C) and the run is UNKNOWN, never a red. MEASURED tonight: a lane child killed by reap or jetsam made its law
exit 1 with an ERROR case, which read as red, and a red tampered run is PROVEN. Children are noted when they start,
and an atexit sweep polls the ones nobody waited on, so a headless Chrome jetsam took mid-run is still said.
Two copies of this folder on sys.path (heart2 arms its own, and a law arms its sandbox's for a fixture gate) boot
ONCE: the chain below skips every gate_trace folder - before, they chained into each other 160 times.
"""
import _thread
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
    state = {"pid": os.getpid(), "n": 0}
    # one guard PER THREAD: emit() drops the GIL in os.write, so a process-wide flag skipped
    # every read another thread made meanwhile
    local = _thread._local()  # LEDGER-TRACE-THREAD
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
        if head in ("ps", "pgrep", "sleep"):
            return  # the process table or a clock: a path in a pgrep pattern is matched, never opened  # TRACE-INERT-CHILD
        if head == "lsof" and not any(
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
        is_node = head in ("node", "nodejs")
        if is_node and traced:
            try:
                opts = (env if env is not None else os.environ).get("NODE_OPTIONS") or ""
            except Exception:
                opts = ""
            if "node_trace.cjs" in opts:
                state["n"] += 1
                emit("P", "%d" % state["n"], once=False)  # node_trace.cjs writes its own B line
                return
        if is_py and traced and not any(a in ("-I", "-E", "-S") for a in args[1:4]):
            state["n"] += 1
            emit("P", "%d" % state["n"], once=False)
            return
        emit("U", "started %s" % (head or "a process"))

    def busy():
        return getattr(local, "busy", False)

    def hook(event, args):
        if busy():
            return
        local.busy = True
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
            local.busy = False

    def stat_wrap(real):
        def wrapped(path, *a, **k):
            if busy() or k.get("dir_fd") is not None:
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

    def probe_wrap(real):
        """os.access and os.readlink: each one asks whether a path is there."""
        def wrapped(path, *a, **k):
            if busy() or k.get("dir_fd") is not None:
                return real(path, *a, **k)
            try:
                out_probe = real(path, *a, **k)
            except FileNotFoundError:
                note(path, "A")
                raise
            except OSError:
                note(path, "S")
                raise
            if out_probe is False:
                note(path, "A")  # LEDGER-TRACE-ACCESS
            else:
                note(path, "S")
            return out_probe
        wrapped.__wrapped__ = real
        return wrapped

    def note(path, kind):
        local.busy = True
        try:
            r = rel(path)
            if r is not None:
                emit(kind, r)
        except Exception:
            pass
        finally:
            local.busy = False

    def after_fork():
        parent = state["pid"]
        state["pid"] = os.getpid()
        seen.clear()
        emit("B", "%d" % parent)

    emit("B", "%d" % os.getppid())
    os.stat = stat_wrap(os.stat)
    os.lstat = stat_wrap(os.lstat)
    os.access = probe_wrap(os.access)
    os.readlink = probe_wrap(os.readlink)  # LEDGER-TRACE-PROBE
    # os.path.realpath needs no wrap: it walks the path through os.lstat, which is wrapped above
    if hasattr(os, "register_at_fork"):
        os.register_at_fork(after_in_child=after_fork)
    sys.addaudithook(hook)
    return here


def _boot_kills():
    """REG-2350 (#42 R5) - K and X lines into TV_GATE_KILLS (see the docstring). Never raises; a process that cannot
    open the file runs unwatched, exactly as before. Booted once per process, whichever copy of this file loads."""
    out = os.environ.get("TV_GATE_KILLS") or ""
    if not out or getattr(sys, "_tv_gate_kills", False):
        return
    try:
        fd = os.open(out, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    except OSError:
        return
    sys._tv_gate_kills = True
    write = os.write
    getpid = os.getpid
    getpgid = getattr(os, "getpgid", None)
    getpgrp = getattr(os, "getpgrp", None)
    getframe = sys._getframe
    st = {"cls": None, "live": None}
    events = frozenset(("os.kill", "os.killpg", "subprocess.Popen"))

    def emit(kind, text):
        try:
            write(fd, ("%s\t%d\t%s\n" % (kind, getpid(), text)).encode("utf-8", "replace"))
        except OSError:
            pass

    def noted(p):
        # the group is asked while the child can still answer: a reaped (or zombie) pid has none on macOS
        if getpgid is not None:
            try:
                if p.returncode is None:
                    p.__dict__["_tv_pgid"] = getpgid(p.pid)
            except Exception:
                pass

    def judged(p):
        try:
            rc = p.returncode
            if isinstance(rc, int) and not isinstance(rc, bool) and rc < 0 and not p.__dict__.get("_tv_k"):
                p.__dict__["_tv_k"] = True
                a = p.args
                head = os.path.basename(str(a[0] if isinstance(a, (list, tuple)) and a else a))[:40]
                emit("K", "pid=%s pgid=%s sig=%d head=%s" % (p.pid, p.__dict__.get("_tv_pgid", "-"), -rc,
                                                             head.replace(" ", "_") or "-"))
        except Exception:
            pass

    def patch(cls):
        real_wait, real_poll = cls.wait, cls.poll

        def wait(self, *a, **k):
            noted(self)
            try:
                return real_wait(self, *a, **k)
            finally:
                judged(self)  # KILL-WATCH-WAIT

        def poll(self, *a, **k):
            noted(self)
            try:
                return real_poll(self, *a, **k)
            finally:
                judged(self)  # KILL-WATCH-POLL
        for f, r in ((wait, real_wait), (poll, real_poll)):
            f.__wrapped__, f.__name__, f.__doc__ = r, r.__name__, r.__doc__
        cls.wait, cls.poll = wait, poll

    def sweep():
        """at exit: a child nobody waited on that a signal ended is said too (a jetsam'd Chrome a test never polled)"""
        for p in list(st["live"] or ()):
            try:
                p.poll() if p.returncode is None else judged(p)  # KILL-WATCH-SWEEP
            except Exception:
                pass

    def hook(event, args):
        if event not in events:
            return
        try:
            if event == "subprocess.Popen":
                sp = sys.modules.get("subprocess")
                if sp is None:
                    return
                if st["cls"] is None:
                    import atexit
                    import weakref
                    st["cls"], st["live"] = sp.Popen, weakref.WeakSet()
                    patch(sp.Popen)
                    atexit.register(sweep)
                f = getframe(1)
                for _i in range(4):
                    if f is None:
                        break
                    me = f.f_locals.get("self")
                    if isinstance(me, sp.Popen):
                        st["live"].add(me)
                        break
                    f = f.f_back
                return
            target, sig = int(args[0]), int(args[1])
            if not sig:
                return  # a probe (signal 0) ends nothing
            if event == "os.killpg":
                who = "pgid=%d" % (target or (getpgrp() if getpgrp else 0))
            elif target > 0:
                who = "pid=%d" % target
            elif target == -1:
                who = "all"
            else:
                who = "pgid=%d" % (-target if target else (getpgrp() if getpgrp else 0))
            emit("X", "%s sig=%d" % (who, sig))  # KILL-WATCH-SENT
        except Exception:
            pass
    sys.addaudithook(hook)


def _is_trace_dir(p):
    """A folder that holds a copy of this hook (this file beside node_trace.cjs). -> bool"""
    try:
        return (os.path.isfile(os.path.join(p or ".", "sitecustomize.py"))
                and os.path.isfile(os.path.join(p or ".", "node_trace.cjs")))
    except Exception:
        return False


def _chain_path(here):
    """Where the sitecustomize this one shadows is looked for. REG-2350 - never in ANOTHER copy of this folder: heart2
    puts its own on PYTHONPATH and a ledger law puts its sandbox's in front of it, and two copies that each chained to
    "the next sitecustomize" booted each other ~160 times (measured). Asked BEFORE any hook is armed, so these stats
    are never facts of the gate's trace."""
    try:
        return [p for p in sys.path if os.path.abspath(p or ".") != here and not _is_trace_dir(p)]  # TRACE-CHAIN-ONCE
    except Exception:
        return [p for p in sys.path if os.path.abspath(p or ".") != here]


def _chain(path):
    """Run the sitecustomize this one shadows, so the system's own hook still loads."""
    try:
        import importlib.machinery
        import importlib.util
        spec = importlib.machinery.PathFinder.find_spec("sitecustomize", path)
        if spec is None or spec.loader is None:
            return
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception:
        pass


_CHAIN_PATH = _chain_path(os.path.dirname(os.path.abspath(__file__)))
_boot_kills()
_boot()
_chain(_CHAIN_PATH)
