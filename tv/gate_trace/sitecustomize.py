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

REG-2442 (#147 R1) - THE FACTS A KEY NEEDS, so a proof can be remembered by what its run read (gate_ledger.facts_of /
facts_hold). Five more line kinds, written beside the ones above - every line above is unchanged:

    Z  a stat's answer: `<kind> <size> <path>` - kind f (a file), l (a link, from lstat), d (a directory) or o (anything
       else); size is st_size for f and l, `-` for d and o. S stays presence-only, so the ledger reads as before.
    E  a SINGLE-NAME read of the environment - os.environ[X], .get(X), X in os.environ, os.getenv(X):
       `<sha256 of the value | -> <NAME>`. Never a value, only its digest. Not for the PLUMBING names a prover sets per
       run (_PLUMBING), not for a name this process set or deleted first, and in a child only when the value is the one
       the run's ROOT process had: a value a parent made is covered by the facts of the process that made it. A bulk
       copy (dict(os.environ), .copy(), .items(), {**os.environ}) and a walk of the names write nothing - a python
       child that receives the copy traces its own reads. FLOOR: a run that decides by WHICH names exist, and a C
       library's own getenv(), are outside this trace.
    N  the root's environment, once, at the root's boot: `<sha256> <NAME>` per non-plumbing name. A child reads it to
       tell an inherited value from one the run made.
    T  `git ls-files` with its scope (`=` or `?` - a flag the check cannot repeat -, the cwd under the root, the pathspecs,
       joined by \\x1f): the tracked SET is an input, not just the root listing (L "" stays for the ledger).
    C  a non-python child whose OWN environment carries TV_GATE_TRACE_CDP=1 (render_check's Chrome) while this process's
       does not: an attested Chrome the run started for its pages. gate_ledger.read_trace() reads C exactly like U
       unless its caller passes allow_cdp_chrome=True (REG-2443).

TV_GATE_TRACE_DENY and TV_GATE_TRACE_ALLOW (os.pathsep lists): any open, stat, listing or git child that reaches a path
under a DENIED root (given or real path) that is under no ALLOWED root writes U - a heart2 sandbox's read of the real
checkout, of a backup folder or of the shared temp dir is a read no key of the sandbox can name; before, rel() dropped
every path outside the root without a word. TV_GATE_TRACE_STRICT=1 adds two U's: importing sqlite3, mmap, ctypes or
dbm (their reads raise no open event) and os.path.getmtime/getctime/getatime on a path under the root (a copy's times
are the copy's). FLOOR, said: a raw os.stat(p).st_mtime is not seen; Z keeps the size, never the times.

REG-2350 (#42 R5) - THE KILL WATCH, armed by TV_GATE_KILLS alone (heart2 arms it on every proof run), into its
own file, in the same line shape:

    K  a child this process waited on or polled ENDED BY A SIGNAL (TEXT: pid, pgid when known, sig, argv0 name)
    E  a child of this process that ENDED WITHOUT ONE (REG-2358): `pid=N rc=R head=H`, R its exit code - or `rc=left`,
       still running when this process exited, so init reaps it and no line of the run will ever say its death
    X  this process SENT a signal (os.kill / os.killpg; a 0 probe is not one): `pid=N`, `pgid=N` or `all`, then `sig=S`,
       `dead=1` when the signal can end nothing at its target number, and `gone=a,b` naming the members of a signalled
       group (children of this process) that were already dead. Written BEFORE the signal leaves.

heart2 reads the pair: a K that no X of the same run explains is a kill from OUTSIDE the run (a by-pid reap, jetsam,
a Ctrl-C) and the run is UNKNOWN, never a red. MEASURED tonight: a lane child killed by reap or jetsam made its law
exit 1 with an ERROR case, which read as red, and a red tampered run is PROVEN. Children are noted when they start,
and an atexit sweep polls the ones nobody waited on, so a headless Chrome jetsam took mid-run is still said.
REG-2356 - an X is checked against its target BEFORE it is written, and without reaping anything. A helper killed from
outside stays a zombie until it is reaped, and a teardown that then signalled it by pid or by group once wrote an X
that explained the outside kill away: a BLIND law was banked PROVEN (measured). So the X now says `dead=1` when its pid
is already dead (a zombie or no process: macOS getpgid answers ESRCH for both; Linux's /proc says Z or PF_EXITING),
or, for a group, when that pid leads no group (killpg then reaches no one: ESRCH, measured). It also names in `gone=`
every member it can see already dead. Nothing is reaped here: kill() on a zombie succeeds, and on a reaped pid it
raises ESRCH (measured), so a reap would change what the law's own os.kill returns.
REG-2358 (round 4) - every child's END is said, not only a death by signal: an X may explain only a death of the
process it was sent to, and a pid that ended is a new process the next time it dies. Before, a helper that handled the
law's SIGTERM and exited 0, or one killed and dropped unwaited (Popen's own finalizer reaps it through _internal_poll,
which nothing watched), ended without a line, and the next process to get its pid, killed from outside, read as the
law's own kill. So the E line, Popen._internal_poll is watched too, and at this process's exit every child it started
that is still running is said `rc=left`. Only the process that started a child says its end: a forked copy of this
process inherits its Popen objects, and their waitpid there answers ECHILD, which Popen reads as an exit 0.
Two copies of this folder on sys.path (heart2 arms its own, and a law arms its sandbox's for a fixture gate) boot
ONCE: the chain below skips every gate_trace folder - before, they chained into each other 160 times.

REG-2359 - THE SKIP WATCH, armed by TV_GATE_SKIPS=1 beside TV_GATE_KILLS (heart2 arms both on every proof run):

    O  a case this process's unittest run SKIPPED: `case=<its id, no spaces> reason=<the skip's own words, one line>`

Written from unittest.result.TestResult.addSkip, which every skip reaches (a skipped class, a skipTest, a setUpClass
SkipTest), so the reasons are seen whatever verbosity the law prints at - at verbosity 1 its log carries only an `s`.
The variable is taken off the environment at boot: only the run's OWN process writes O lines, never a child of it. heart2
reads them to tell a law that skipped for want of what this PC lacks (node, by the reason; POSIX, by the case) from
one that skipped for any other reason (REG-2354).
"""
import _thread
import os
import sys

#: REG-2442 - the environment names a prover sets PER RUN (temp dirs, lane ports, its own and the trace's switches): a
#: read of one is never an E fact and the root's N block leaves them out. gate_ledger.TRACE_PLUMBING and node_trace.cjs
#: carry the same set; test_a_trace_names_every_read_a_key_needs holds the three equal. [[copy-drift]]
_PLUMBING = frozenset(("TMPDIR", "TEMP", "TMP", "TV_LANE_PORT_BASE", "TV_PORT", "TV_CONTROL_PORT", "TV_LAW_PORT",
                       "TV_RENDER_PORT", "PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX",
                       "NODE_OPTIONS"))  # TRACE-PLUMBING
_PLUMBING_PREFIXES = ("HEART2_", "TV_GATE_")
#: REG-2442 - under TV_GATE_TRACE_STRICT=1 importing one of these is a U: their reads raise no open audit event
_STRICT_MODULES = frozenset(("sqlite3", "_sqlite3", "mmap", "ctypes", "_ctypes", "dbm", "_dbm", "_gdbm"))


def _plumbing(name):
    """A name the prover sets per run (case-blind, as Windows' environment is). -> bool"""
    u = str(name).upper()
    return u in _PLUMBING or u.startswith(_PLUMBING_PREFIXES)


def _trace_forms(spec):
    """An os.pathsep list of roots -> every form each is reached by: as given, absolute, and its real path. -> [str]"""
    out = []
    for part in str(spec or "").split(os.pathsep):
        part = part.strip()
        if not part:
            continue
        p = os.path.normpath(os.path.abspath(os.path.expanduser(part)))
        for cand in (p, os.path.normpath(os.path.realpath(p))):
            cand = os.path.normcase(cand)
            if cand not in out:
                out.append(cand)
    return out


def _root_env(out):
    """REG-2442 - whose environment this process's E facts are measured against. -> (is_root, {name: digest} | None)

    The run's ROOT - its parent wrote no B line in this trace - answers (True, None) and writes the N block itself. A
    child walks its parents through the B lines to the nearest one that wrote an N block and answers (False, that
    block). A traced ancestry with no block answers (False, None): every read is then a fact - over-wide, never under.
    A trace that cannot be read makes this process a root of its own subtree, the same over-wide direction.
    Read before any hook is armed, so this read is never a fact of the run."""
    try:
        rfd = os.open(out, os.O_RDONLY | getattr(os, "O_BINARY", 0))  # Windows' C runtime reads text mode otherwise
    except OSError:
        return True, None
    chunks = []
    try:
        while True:
            b = os.read(rfd, 1 << 20)
            if not b:
                break
            chunks.append(b)
    except OSError:
        return True, None
    finally:
        os.close(rfd)
    data = b"\n" + b"".join(chunks)
    parent, block = {}, {}
    for tag in (b"\nB\t", b"\nN\t"):  # found by find(), so a long trace costs one C scan, not a split per line
        i = data.find(tag)
        while i >= 0:
            j = data.find(b"\n", i + 1)
            # a trace written on Windows ends its lines \r\n: the line is the text before both
            parts = data[i + 1:(j if j >= 0 else len(data))].rstrip(b"\r").split(b"\t", 2)
            i = data.find(tag, i + 1)
            if len(parts) != 3:
                continue
            if tag == b"\nB\t":
                parent[parts[1]] = parts[2]
            else:
                d, _sp, n = parts[2].partition(b" ")
                block.setdefault(parts[1], {})[n.decode("utf-8", "surrogateescape")] = d.decode("ascii", "replace")
    p = str(os.getppid()).encode("ascii")
    if p not in parent:
        return True, None  # TRACE-ENV-ROOT
    walked = set()
    while p in parent and p not in walked:
        if p in block:
            return False, block[p]
        walked.add(p)
        p = parent[p]
    return False, None


def _boot():
    out = os.environ.get("TV_GATE_TRACE") or ""
    root = os.environ.get("TV_GATE_TRACE_ROOT") or ""
    if not out or not root:
        return
    is_root, root_env = _root_env(out)
    try:
        fd = os.open(out, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    except OSError:
        return
    roots = []
    for cand in (root, os.path.realpath(root)):
        cand = os.path.normpath(cand)
        if cand not in roots:
            roots.append(cand)
    deny = _trace_forms(os.environ.get("TV_GATE_TRACE_DENY"))     # REG-2442 - roots no key of this run can name
    allow = _trace_forms(os.environ.get("TV_GATE_TRACE_ALLOW"))   # ... except these, inside them (the run's own temp)
    strict = os.environ.get("TV_GATE_TRACE_STRICT") == "1"
    import hashlib
    import stat as _stat
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
    normcase = os.path.normcase
    realdirs = {}

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
        if deny and denied(path):
            emit("U", "reached %s, under a root no key of this run can name" % path)  # TRACE-DENY
        return None

    def under(path, bases):
        for b in bases:
            if path == b or path.startswith(b if b.endswith(sep) else b + sep):
                return True
        return False

    def denied(path):
        """REG-2442 - an absolute path under a DENIED root and under no ALLOWED one, as given or by its real folder.
        -> bool. The real folder is asked once per folder (a symlinked /tmp or /var reaches /private/... on macOS)."""
        folder, tail = os.path.split(path)
        real = realdirs.get(folder)
        if real is None:
            try:
                real = os.path.realpath(folder)
            except Exception:
                real = folder
            if len(realdirs) < 8192:
                realdirs[folder] = real
        forms = (normcase(path), normcase(join(real, tail)))
        if allow and any(under(f, allow) for f in forms):
            return False
        return any(under(f, deny) for f in forms)

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
        at = rel(where if where is not None else getcwd())
        if at is None:
            return True  # a fixture repository outside this checkout
        sub = rest[0] if rest else ""
        opts = rest[1:]
        if sub == "ls-files" and not any(o.startswith(("-o", "--others", "-m", "--modified", "-d", "--deleted",
                                                         "-s", "--stage", "--with-tree", "--error-unmatch"))
                                         for o in opts):
            emit("L", "")  # the tracked set: any added or deleted file
            # REG-2442 - and WHICH set: a check repeats this ls-files (same cwd, same pathspecs); a flag it cannot
            # repeat marks the scope `?`, which no tree ever matches
            odd = any(o.startswith("-") and o not in ("-z", "--full-name", "-c", "--cached", "--") for o in opts)
            emit("T", "\x1f".join(["?" if odd else "=", at] + [o for o in opts if not o.startswith("-")]))  # TRACE-TRACKED-SET
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
        if env is not None and not is_py and not is_node and cdp_marked(env):
            emit("C", "started %s, a Chrome this run started for its pages" % (head or "a process"))  # TRACE-CDP-ATTESTED
            return
        emit("U", "started %s" % (head or "a process"))

    def cdp_marked(env):
        """REG-2443 - the child's OWN environment says render_check started it for its pages, and this process's own
        does not: a marker this process carries itself is inheritance, never an attestation for this child. -> bool"""
        try:
            theirs = env.get("TV_GATE_TRACE_CDP")
            if theirs is None:
                theirs = env.get(b"TV_GATE_TRACE_CDP")
            if isinstance(theirs, bytes):
                theirs = theirs.decode("ascii", "replace")
            return theirs == "1" and os.environ.get("TV_GATE_TRACE_CDP") != "1"
        except Exception:
            return False

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
                making = (isinstance(mode, str) and any(c in mode for c in "wx")) or (
                    mode is None and isinstance(flags, int) and flags & (os.O_TRUNC | os.O_EXCL))
                if not writes or not making:
                    bytes_fact(r)  # a read, or a write that keeps the bytes it finds (append, r+): what it found
                if writes:
                    emit("W", r)
                if not writes or (isinstance(mode, str) and "+" in mode) or (
                        mode is None and isinstance(flags, int) and flags & os.O_RDWR):
                    emit("R", r)
            elif event in ("os.listdir", "os.scandir"):
                r = rel(args[0] if args else None)
                if r is not None and not by_importer():
                    emit("L", r)
                    listing_fact(r)
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
                if strict and name in _STRICT_MODULES:
                    emit("U", "imported %s, whose reads raise no open event" % name)  # TRACE-STRICT-IMPORT
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

    def stat_wrap(real, follows=True):
        def wrapped(path, *a, **k):
            if busy() or k.get("dir_fd") is not None:
                return real(path, *a, **k)
            try:
                out_stat = real(path, *a, **k)
            except (FileNotFoundError, NotADirectoryError):
                # REG-2447 - ENOTDIR too: a path under a FILE is absent, and a tree that makes that file a folder moves
                # what the run decided (os.path.exists said False and wrote nothing)
                note(path, "A")  # TRACE-STAT-ABSENT
                raise
            except OSError:
                note(path, "S")  # there but unstattable (a link loop, no permission): a check measures its presence
                raise
            note(path, "S", (out_stat, follows and k.get("follow_symlinks", True) is not False))
            return out_stat
        wrapped.__wrapped__ = real
        return wrapped

    def size_of(st, follows=True):
        """REG-2442 - the Z fact's `<kind> <size>` of one stat answer: the size of a file or a link, a directory and
        anything else by kind alone (a directory's st_size is the filesystem's bookkeeping, not its contents). A stat
        that did not follow links (lstat) says F, D or O for a name that is no link, so a check asks it the same way."""
        m = st.st_mode
        if _stat.S_ISLNK(m):
            return "l %d" % st.st_size
        kind = "f" if _stat.S_ISREG(m) else ("d" if _stat.S_ISDIR(m) else "o")
        size = ("%d" % st.st_size) if kind == "f" else "-"
        return "%s %s" % (kind if follows else kind.upper(), size)

    base_root = roots[0]

    def under_root(r):
        return join(base_root, *r.split("/")) if r else base_root

    def file_sha(full):
        h = hashlib.sha256()
        try:
            rfd = os.open(full, os.O_RDONLY | getattr(os, "O_BINARY", 0))  # the bytes, never a text-mode translation
        except OSError:
            return "?"
        try:
            while True:
                chunk = os.read(rfd, 1 << 20)
                if not chunk:
                    break
                h.update(chunk)
        except OSError:
            return "?"
        finally:
            os.close(rfd)
        return h.hexdigest()

    def bytes_fact(r):
        """REG-2442 - H: the bytes a read finds, measured as it opens: `<sha256 | - absent | d a folder | ? no bytes a
        check could hold> <path>`. Once per path per process; gate_ledger keeps the first that came before any write."""
        key = ("H:", r)
        if key in seen:
            return
        seen.add(key)
        full = under_root(r)
        try:
            st = os.stat(full)  # busy: the real stat, no S line
        except FileNotFoundError:
            d = "-"
        except OSError:
            d = "?"
        else:
            if _stat.S_ISDIR(st.st_mode):
                d = "d"
            elif not _stat.S_ISREG(st.st_mode):
                d = "?"  # a fifo or a device: reading it here could block, and it holds no bytes to keep
            else:
                d = file_sha(full)
        emit("H", "%s %s" % (d, r))  # TRACE-BYTES-FACT

    def listing_fact(r):
        """REG-2442 - D: what a listed folder held as it was listed - each name with its kind and a file's size (never a
        time), sorted, as one sha256; gate_ledger._listing_digest is the same rule. Once per folder per process."""
        key = ("D:", r)
        if key in seen:
            return
        seen.add(key)
        rows = []
        try:
            with os.scandir(under_root(r)) as it:
                for e in it:
                    if e.name == "__pycache__":
                        continue
                    st = e.stat(follow_symlinks=False)
                    kind = "l" if _stat.S_ISLNK(st.st_mode) else ("f" if _stat.S_ISREG(st.st_mode) else (
                        "d" if _stat.S_ISDIR(st.st_mode) else "o"))
                    rows.append("%s\t%s\t%s" % (e.name, kind, ("%d" % st.st_size) if kind in "fl" else "-"))
        except FileNotFoundError:
            d = "-"
        except NotADirectoryError:
            d = "f"
        except OSError:
            d = "?"
        else:
            d = hashlib.sha256("\n".join(sorted(rows)).encode("utf-8", "surrogateescape")).hexdigest()
        emit("D", "%s %s" % (d, r))  # TRACE-LISTING-FACT

    def mtime_wrap(real, what):
        """REG-2442 - TV_GATE_TRACE_STRICT=1: a time read from a file under the root is a U - a copy of the tree keeps
        its bytes, never its times. Any path outside the root reads as before."""
        def wrapped(filename, *a, **k):
            if not busy():
                local.busy = True
                try:
                    r = rel(filename)
                    if r is not None:
                        emit("U", "read the %s of %s, which a copy of the tree does not keep" % (what, r))  # TRACE-STRICT-TIME
                except Exception:
                    emit("U", "the trace hook raised")
                finally:
                    local.busy = False
            return real(filename, *a, **k)
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

    def note(path, kind, st=None):
        local.busy = True
        try:
            r = rel(path)
            if r is not None:
                emit(kind, r)
                if st is not None:
                    emit("Z", "%s %s" % (size_of(st[0], st[1]), r))  # TRACE-SIZE-FACT
        except Exception:
            pass
        finally:
            local.busy = False

    def env_digest(value):
        if isinstance(value, str):
            value = value.encode("utf-8", "surrogateescape")
        return hashlib.sha256(value).hexdigest()

    # REG-2442 - E facts. The ROOT's environment is the run's input; a child compares against the N block its root
    # wrote, so a value a parent of the run made (a fixture's TV_HIST=<its temp dir>) is not a fact of the child.
    env_seen, env_written = set(), set()

    def env_name(envmap, key):
        try:
            k = envmap.encodekey(key)
        except Exception:
            return None
        if isinstance(k, bytes):
            k = k.decode("utf-8", "surrogateescape")
        return str(k)

    def env_note(envmap, key, value, present):
        local.busy = True
        try:
            name = env_name(envmap, key)
            if name is None or _plumbing(name) or name in env_written or name in env_seen:
                return
            env_seen.add(name)
            d = env_digest(value) if present else "-"
            if root_env is not None and root_env.get(name, "-") != d:
                return  # the run made this value: the process that made it holds the fact  # TRACE-ENV-MADE
            emit("E", "%s %s" % (d, name))  # TRACE-ENV-FACT
        except Exception:
            emit("U", "the trace hook raised")
        finally:
            local.busy = False

    def arm_env():
        """REG-2442 - os._Environ's single-name reads write E. A bulk read is told apart by WHO asks: dict(), {**e}
        and .copy() call keys() first and then read every name from the same frame at the same instruction; .items()
        and .values() read from collections.abc's own views. Mapping.get and __contains__ reach __getitem__, so
        .get(X), X in os.environ and os.getenv(X) are single-name reads too."""
        cls = getattr(os, "_Environ", None)
        if cls is None:
            return
        import _collections_abc as _abc
        views = frozenset(f.__code__ for f in (_abc.ItemsView.__iter__, _abc.ValuesView.__iter__,
                                                 _abc.ValuesView.__contains__))
        real_get, real_set, real_del, real_keys = cls.__getitem__, cls.__setitem__, cls.__delitem__, cls.keys

        def getitem(self, key):
            if busy():
                return real_get(self, key)
            try:
                f = getframe(1)
            except ValueError:
                f = None  # no python caller at all: nothing to tell a bulk read by, so a single-name read
            mark = getattr(local, "bulk", None)
            bulk = f is not None and (f.f_code in views or (mark is not None and mark[0] == id(f)
                                                              and mark[1] is f.f_code and mark[2] == f.f_lasti))
            if mark is not None and not bulk:
                local.bulk = None
            try:
                value = real_get(self, key)
            except KeyError:
                if not bulk:
                    env_note(self, key, None, False)
                raise
            if not bulk:
                env_note(self, key, value, True)
            return value

        def keys(self):
            if not busy():
                try:
                    f = getframe(1)
                    local.bulk = (id(f), f.f_code, f.f_lasti)  # TRACE-ENV-BULK
                except ValueError:
                    local.bulk = None
            return real_keys(self)

        def setitem(self, key, value):
            n = env_name(self, key)
            if n is not None:
                env_written.add(n)  # a value this process set is not one it found
            return real_set(self, key, value)

        def delitem(self, key):
            n = env_name(self, key)
            if n is not None:
                env_written.add(n)
            return real_del(self, key)
        for fn, real in ((getitem, real_get), (keys, real_keys), (setitem, real_set), (delitem, real_del)):
            fn.__wrapped__, fn.__name__, fn.__doc__ = real, real.__name__, real.__doc__
        cls.__getitem__, cls.keys, cls.__setitem__, cls.__delitem__ = getitem, keys, setitem, delitem

    def after_fork():
        parent = state["pid"]
        state["pid"] = os.getpid()
        seen.clear()
        emit("B", "%d" % parent)

    emit("B", "%d" % os.getppid())
    if is_root:
        # REG-2442 - the run's environment, once, before any child can start: what a child's E facts are held to
        for _k, _v in list(os.environ.items()):
            if not _plumbing(_k):
                emit("N", "%s %s" % (env_digest(_v), _k))  # TRACE-ENV-ROOT-BLOCK
    # REG-2446 - PYTHON 3.9/3.10's pathlib COPIES os.stat and os.lstat (3.10: os.readlink) INTO ITS _NormalAccessor WHEN
    # IT IS IMPORTED. Measured on his Mac (python 3.9.6): a user site-packages .pth imports pathlib before this file
    # runs, so Path.exists() / .stat() / .is_file() asked the REAL os.stat and wrote no S, A or Z - a law's pathlib probe
    # of an ignored file was no fact of its key, for the ledger and the proof memory alike. And where pathlib loads AFTER
    # this file (a 3.9/3.10 python without that .pth), its class body copied the wrapper - a plain function, which binds
    # as a method - and every Path.stat() of a traced run raised TypeError. So on 3.9/3.10 pathlib is imported here,
    # BEFORE the wrap, and its accessor is pointed at the wrappers as static methods (3.11+ asks os.stat at call time).
    pl_acc, pl_real = None, {}
    if sys.version_info < (3, 11):
        try:
            import pathlib as _pl
            pl_acc = getattr(_pl, "_NormalAccessor", None)
        except Exception:
            pl_acc = None
        pl_real = dict((n, getattr(os, n, None)) for n in ("stat", "lstat", "readlink"))
    os.stat = stat_wrap(os.stat)
    os.lstat = stat_wrap(os.lstat, False)
    os.access = probe_wrap(os.access)
    os.readlink = probe_wrap(os.readlink)  # LEDGER-TRACE-PROBE
    if pl_acc is not None:
        for _n, _real in sorted(pl_real.items()):
            if _real is not None and vars(pl_acc).get(_n) is _real:
                setattr(pl_acc, _n, staticmethod(getattr(os, _n)))  # TRACE-PATHLIB-ACCESSOR
    # os.path.realpath needs no wrap: it walks the path through os.lstat, which is wrapped above
    if strict:
        for _name in sorted(_STRICT_MODULES & set(sys.modules)):
            emit("U", "had %s loaded before the trace began" % _name)
        import genericpath as _gp
        for _mod in (os.path, _gp):
            for _fn, _what in (("getmtime", "mtime"), ("getctime", "ctime"), ("getatime", "atime")):
                _cur = getattr(_mod, _fn, None)
                if _cur is not None and getattr(_cur, "__wrapped__", None) is None:
                    setattr(_mod, _fn, mtime_wrap(_cur, _what))
    arm_env()
    if hasattr(os, "register_at_fork"):
        os.register_at_fork(after_in_child=after_fork)
    sys.addaudithook(hook)
    return here


def _boot_kills():
    """REG-2350 (#42 R5) - K and X lines into TV_GATE_KILLS (see the docstring). Never raises; a process that cannot
    open the file runs unwatched, exactly as before. Booted once per process, whichever copy of this file loads.
    REG-2359 - and O lines, when TV_GATE_SKIPS=1 is set too (see the docstring)."""
    # REG-2359 - the skip watch belongs to the run's OWN process: taken off the environment before anything else, so no
    # child inherits it (a law that runs a fixture suite in a child would add that suite's skips to its own)
    skips = os.environ.pop("TV_GATE_SKIPS", None) == "1"  # SKIP-WATCH-OWN
    out = os.environ.get("TV_GATE_KILLS") or ""
    if not out or getattr(sys, "_tv_gate_kills", False):
        return
    try:
        fd = os.open(out, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    except OSError:
        return
    sys._tv_gate_kills = True
    write = os.write
    os_open, os_read, os_close, rdonly = os.open, os.read, os.close, os.O_RDONLY
    getpid = os.getpid
    getpgid = getattr(os, "getpgid", None)
    getpgrp = getattr(os, "getpgrp", None)
    getframe = sys._getframe
    st = {"cls": None, "live": None, "skips": not skips}    # "skips": True once the skip watch is in (or not wanted)
    events = frozenset(("os.kill", "os.killpg", "subprocess.Popen") + (("import",) if skips else ()))

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

    def zombie_on_proc(n):
        """Linux keeps a zombie's group, so getpgid cannot tell it from a live pid there: /proc says Z, or PF_EXITING
        (0x4 in field 9, set before the dying task closes its files - so before any pipe of it reads EOF). On macOS
        getpgid already answers ESRCH by the time a killed child's pipe reads EOF: 0 of 700 trials, 400 of them under
        12 busy loops (measured). -> bool"""
        try:
            fd = os_open("/proc/%d/stat" % n, rdonly)
        except OSError:
            return False  # no /proc (macOS, where getpgid already answered) or no such pid
        try:
            data = os_read(fd, 512)
        except OSError:
            return False
        finally:
            os_close(fd)
        i = data.rfind(b")")
        rest = data[i + 1:].split() if i >= 0 else []
        try:
            return rest[0] in (b"Z", b"X") or bool(int(rest[6]) & 0x4)
        except (IndexError, ValueError):
            return False

    def unreachable(kind, n):
        """REG-2356 - can a signal sent to this target NUMBER end nothing? A pid that is already dead (a zombie nobody
        reaped yet, or no process at all), or, for a group, a live pid that leads no group. Asked WITHOUT reaping.
        False when it cannot be told: the reader then judges this X as before. -> bool"""
        if kind == "all" or not n or n < 0 or getpgid is None:
            return False
        try:
            g = getpgid(n)
        except ProcessLookupError:
            return True  # macOS: a zombie and a missing pid both answer ESRCH (measured)
        except Exception:
            return False
        if kind == "pgid" and g != n:
            return True  # it lives in another group: killpg(n) reaches no one (ESRCH, measured)
        return zombie_on_proc(n)

    def group_of(p):
        """A child's group, read now if no wait or poll read it while it was alive. -> int | None"""
        g = p.__dict__.get("_tv_pgid")
        if g is None and getpgid is not None:
            try:
                g = p.__dict__["_tv_pgid"] = getpgid(p.pid)
            except Exception:
                g = None  # a zombie on macOS: its K says pgid=-, which no group X can explain
        return g

    def headof(p):
        try:
            a = p.args
            head = os.path.basename(str(a[0] if isinstance(a, (list, tuple)) and a else a))[:40]
        except Exception:
            head = ""
        return head.replace(" ", "_") or "-"

    def mine(p):
        """REG-2358 - did THIS process start p? A forked copy of a process inherits its Popen objects, and a wait or
        poll there answers ECHILD, which Popen reads as an exit 0: that copy must say nothing about a child it never
        started. -> bool (True when nobody recorded who started it, as before)"""
        return p.__dict__.get("_tv_owner", getpid()) == getpid()  # KILL-WATCH-OWNER

    def judged(p):
        """One line per child, from the process that started it, once it has ENDED: K when a signal ended it, and
        (REG-2358) E for any other end - an exit code, whatever it is - so a pid that ended is never read as alive."""
        try:
            rc = p.returncode
            if isinstance(rc, int) and not isinstance(rc, bool) and not p.__dict__.get("_tv_k") and mine(p):
                p.__dict__["_tv_k"] = True
                if rc < 0:
                    emit("K", "pid=%s pgid=%s sig=%d head=%s" % (p.pid, p.__dict__.get("_tv_pgid", "-"), -rc,
                                                                 headof(p)))
                else:
                    emit("E", "pid=%s rc=%d head=%s" % (p.pid, rc, headof(p)))  # KILL-WATCH-END
        except Exception:
            pass

    def patch(cls):
        real_wait, real_poll = cls.wait, cls.poll
        # REG-2358 - Popen's own reap: poll() calls it, and so do __del__ and subprocess._cleanup for a child dropped
        # without a wait. Watched here, so a dropped child's end is said too (before, nothing saw it).
        real_ipoll = getattr(cls, "_internal_poll", None)

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
                if real_ipoll is None:
                    judged(self)  # a Python whose poll() has no _internal_poll to be judged in

        def ipoll(self, *a, **k):
            try:
                return real_ipoll(self, *a, **k)
            finally:
                judged(self)  # KILL-WATCH-POLL
        pairs = ((wait, real_wait), (poll, real_poll)) + (((ipoll, real_ipoll),) if real_ipoll is not None else ())
        for f, r in pairs:
            f.__wrapped__, f.__name__, f.__doc__ = r, r.__name__, r.__doc__
        cls.wait, cls.poll = wait, poll
        if real_ipoll is not None:
            cls._internal_poll = ipoll

    def sweep():
        """at exit (this process's run ends): a child nobody waited on that a signal ended is said too (a jetsam'd
        Chrome a test never polled), and one that ended otherwise is said E. REG-2358 - a child STILL RUNNING is left
        to init, which writes no line: its pid is closed here (`rc=left`), since no line of the run can say its death
        and the next process to get that pid is a new one. Only this process's own children: a forked copy's are not
        its to say."""
        for p in list(st["live"] or ()):
            try:
                if not mine(p):
                    continue
                p.poll() if p.returncode is None else judged(p)  # KILL-WATCH-SWEEP
                if p.returncode is None and not p.__dict__.get("_tv_k"):
                    p.__dict__["_tv_k"] = True
                    emit("E", "pid=%s rc=left head=%s" % (p.pid, headof(p)))  # KILL-WATCH-LEFT
            except Exception:
                pass

    def watch_skips():
        """REG-2359 - once unittest's result module has loaded, every case it records as skipped is written as an O line
        with its reason, whatever the verbosity the law prints at. Asked at each import until then: unittest/__init__
        imports .result first and .case right after, so the next import event finds TestResult defined."""
        m = sys.modules.get("unittest.result")
        cls = getattr(m, "TestResult", None) if m is not None else None
        real = getattr(cls, "addSkip", None) if cls is not None else None
        if real is None:
            return
        st["skips"] = True

        def addSkip(self, test, reason):
            try:
                case = "".join(str(test.id() if hasattr(test, "id") else test).split())[:200] or "-"
                emit("O", "case=%s reason=%s" % (case, " ".join(str(reason).split())[:300]))  # SKIP-WATCH-SAID
            except Exception:
                pass
            return real(self, test, reason)
        addSkip.__wrapped__, addSkip.__name__, addSkip.__doc__ = real, real.__name__, real.__doc__
        cls.addSkip = addSkip

    def hook(event, args):
        if event not in events:
            return
        try:
            if event == "import":
                if not st["skips"]:
                    watch_skips()  # SKIP-WATCH-ARM
                return
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
                        me.__dict__["_tv_owner"] = getpid()  # KILL-WATCH-OWNED - REG-2358: the process that started it
                        st["live"].add(me)
                        break
                    f = f.f_back
                return
            target, sig = int(args[0]), int(args[1])
            if not sig:
                return  # a probe (signal 0) ends nothing
            if event == "os.killpg":
                kind, n = "pgid", (target or (getpgrp() if getpgrp else 0))
            elif target > 0:
                kind, n = "pid", target
            elif target == -1:
                kind, n = "all", 0
            else:
                kind, n = "pgid", (-target if target else (getpgrp() if getpgrp else 0))
            # REG-2356 - before the X is written (the audit hook runs before the signal leaves): what can it NOT end?
            dead = unreachable(kind, n)  # KILL-WATCH-DEAD
            late = []
            if kind != "pid":
                for p in list(st["live"] or ()):
                    if p.returncode is None and p.pid != n and (kind == "all" or group_of(p) == n) \
                            and unreachable("pid", p.pid):
                        late.append("%d" % p.pid)  # KILL-WATCH-GONE
            who = "all" if kind == "all" else "%s=%d" % (kind, n)
            tail = (" dead=1" if dead else "") + (" gone=" + ",".join(late) if late else "")
            emit("X", "%s sig=%d%s" % (who, sig, tail))  # KILL-WATCH-SENT
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
