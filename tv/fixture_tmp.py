# -*- coding: utf-8 -*-
"""#171 — ONE place a TEST process keeps its scratch directories, and they leave with it.

⚠⚠ WHAT IT COST BEFORE THIS EXISTED. 138 `tempfile.mkdtemp()` sites across 46 test files had no
teardown in their own function or class (test_control 35, test_agent 27, then five or fewer per file),
so every gate run left directories behind in $TMPDIR - MEASURED 2026-09-24 on his Mac: 6,574 bare tmp*
dirs, the volume #171 names. Pairing 138 call sites by hand is 138 chances to miss one, and the next
test written is the 139th. [[heart-first]] rule 4: instrument at the door, and gate the door.

`contain()` gives the calling process ONE parent directory under the real temp dir and points
tempfile (and TMPDIR/TEMP/TMP, so child processes inherit it) at it; every mkdtemp the suite makes -
paired or not - lands inside, and the parent is removed at exit. A run that is KILLED never reaches
atexit, so the next contain() sweeps parents left by processes that are no longer alive and are over a
day old - never a live run's.

A test that already cleans up keeps doing so; this only catches what it does not.
⚠ PRODUCTION CODE MUST NEVER IMPORT THIS. It exists for test processes only - his console's temp files
must outlive nothing and be swept by nobody.
"""
import atexit
import os
import shutil
import tempfile
import time

PREFIX = "d2r-test-"
STALE_S = 24 * 3600

_HELD = {}


def _alive(pid):
    if os.name == "nt":                  # REG-1725 - os.kill(pid, 0) is a Ctrl-C there; ask the safe door
        try:
            import self_prove as _sp
            return _sp.pid_alive(pid)
        except Exception:
            return True                  # cannot tell -> treat as alive, never sweep it
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except Exception:
        return True                      # cannot tell -> treat as alive, never sweep it


def sweep_stale(base, now=None, stale_s=STALE_S):
    """Remove parents a KILLED run left behind: our prefix, owner pid dead, older than stale_s. -> [names]"""
    now = time.time() if now is None else now
    gone = []
    try:
        names = os.listdir(base)
    except OSError:
        return gone
    for n in names:
        if not n.startswith(PREFIX):
            continue
        try:
            pid = int(n[len(PREFIX):].split("-", 1)[0])
        except ValueError:
            continue
        p = os.path.join(base, n)
        try:
            age = now - os.stat(p).st_mtime
        except OSError:
            continue
        if age < stale_s or pid == os.getpid() or _alive(pid):
            continue
        shutil.rmtree(p, ignore_errors=True)
        gone.append(n)
    return gone


def contain():
    """Point this process's scratch directories at one parent removed at exit. Idempotent. -> the parent"""
    if _HELD.get("dir"):
        return _HELD["dir"]
    base = tempfile.gettempdir()
    sweep_stale(base)
    d = tempfile.mkdtemp(prefix="%s%d-" % (PREFIX, os.getpid()), dir=base)
    _HELD.update(dir=d, base=base)
    tempfile.tempdir = d
    for var in ("TMPDIR", "TEMP", "TMP"):
        os.environ[var] = d
    atexit.register(_release, d)
    return d


def _release(d):
    shutil.rmtree(d, ignore_errors=True)


# ══ REG-2362 - A LAW MAY LIST ITS OWN SCRATCH, AND ONLY ITS OWN SCRATCH ══════════════════════════════════════
# heart2 keys a proof on the bytes its law can read, and a law that lists a directory ITSELF (os.listdir, glob.glob,
# os.walk in the law file) reads whatever is there at run time - so heart2 calls it UNKEYABLE and never saves one of
# its proofs. MEASURED 2026-10-21: test_control's 27 proofs ran ~4 min each on every push of the v3783 series and were
# never saved, because the file lists directories at 40 sites - and 26 of them list a temp dir the test made a line
# earlier, which no other process can write. A listing of THIS process's own scratch is decided by the code under
# test, which the key already holds. These two say so by construction: they refuse any path that is not strictly
# inside the parent contain() made for this process, so they can never be pointed at the tree, his footage or a
# temp dir another process shares. A listing of anything else stays os.listdir in the law file, where heart2 sees it.
# Law: test_a_scratch_listing_reads_only_its_own_scratch. [[unknown-stays-unknown]]
def _own(path):
    """-> the real path of `path`, when it lies strictly inside this process's contained scratch parent. Raises
    ValueError otherwise: no contain() in this process, the parent itself, or anywhere outside it (symlinks resolved)."""
    held = _HELD.get("dir")
    if not held:
        raise ValueError("fixture_tmp: this process never called contain(), so no directory can be shown to be its "
                         "own scratch - list it with os.listdir in the law file, where the heart sees it")
    root = os.path.realpath(held)
    p = os.path.realpath(path)
    try:
        inside = os.path.commonpath([root, p]) == root
    except ValueError:                       # a different drive on Windows
        inside = False
    if p == root or not inside:
        raise ValueError("fixture_tmp: %r is not inside this process's own scratch (%s) - a listing of anything else "
                         "is a read of the tree, his footage or a shared temp dir, and belongs in the law file"
                         % (path, root))
    return p


def list_own(path):
    """os.listdir(path), for a directory inside this process's own scratch only (REG-2362). -> [names]"""
    _own(path)
    return os.listdir(path)


def match_own(pattern):
    """glob.glob(pattern), when the pattern's directory is inside this process's own scratch and only its last part
    holds a wildcard (REG-2362). -> [paths]"""
    import glob as _glob
    d = os.path.dirname(pattern)
    if any(c in d for c in "*?["):
        raise ValueError("fixture_tmp: only the last part of %r may hold a wildcard" % pattern)
    _own(d)
    return _glob.glob(pattern)
