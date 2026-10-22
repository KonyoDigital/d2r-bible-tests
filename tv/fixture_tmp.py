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
    # REG-2455 - the parent's REAL path, resolved ONCE, here: _own() measures every later path against this string,
    # never against a fresh realpath of the parent (which a rename + link swap would answer for)
    _HELD.update(dir=d, base=base, real=os.path.realpath(d))
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
#   HOW A LAW USES THEM: call contain() once at import, BEFORE any tempfile.mkdtemp; a directory that mkdtemp() (no
#   dir= argument) or os.makedirs under one of those made since is its own - `os.listdir(d)` becomes `list_own(d)`,
#   `glob.glob(os.path.join(d, "f_*.jpg"))` becomes `match_own(...)`, same answer. A path mkdtemp made BEFORE
#   contain(), one made with dir= elsewhere, the parent itself, or a link out of it raises ValueError - never a silent
#   empty list. The REG-2362 swap of a law's os.listdir is only that: the same path, the same names.
def _own(path):
    """-> the real path of `path`, when it lies strictly inside this process's contained scratch parent. Raises
    ValueError otherwise: no contain() in this process, the parent itself, or anywhere outside it (symlinks resolved)."""
    held = _HELD.get("dir")
    if not held:
        raise ValueError("fixture_tmp: this process never called contain(), so no directory can be shown to be its "
                         "own scratch - list it with os.listdir in the law file, where the heart sees it")
    root = _HELD.get("real") or os.path.realpath(held)
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


def _still_own(path, p):
    """REG-2455 - after a listing: `path` must still resolve to the directory that was listed, or the listing is not an
    answer about it (a rename + link swap between the check and the read). Raises ValueError."""
    if _own(path) != p:
        raise ValueError("fixture_tmp: %r moved while it was being listed - it now resolves outside what was listed, "
                         "so the listing answers for nothing" % (path,))


def list_own(path):
    """os.listdir(path), for a directory inside this process's own scratch only (REG-2362). -> [names]

    REG-2455 - the RESOLVED directory is listed (the path checked is the path read), and the path is checked again
    after: a swap between the check and the read raises instead of listing another tree."""
    p = _own(path)
    names = os.listdir(p)
    _still_own(path, p)
    return names


def match_own(pattern):
    """glob.glob(pattern), when the pattern's directory is inside this process's own scratch and only its last part
    holds a wildcard (REG-2362). -> [paths], spelled under the caller's directory as glob.glob(pattern) spells them.
    REG-2455 - matched in the RESOLVED directory and checked again after, like list_own."""
    import glob as _glob
    d = os.path.dirname(pattern)
    if any(c in d for c in "*?["):
        raise ValueError("fixture_tmp: only the last part of %r may hold a wildcard" % pattern)
    p = _own(d)
    hits = _glob.glob(os.path.join(p, os.path.basename(pattern)))
    _still_own(d, p)
    return [os.path.join(d, os.path.basename(h)) for h in hits]


# ══ REG-2366 - A DIRECTORY LINK, MADE THE WAY THIS PC CAN ═══════════════════════════════════════════════════════
# list_own's containment rests on realpath, and the one case that shows it (a link inside the scratch pointing at the
# tree) needs a DIRECTORY LINK. Windows refuses os.symlink without a privilege his ALT and Dean's PC do not hold, so on
# them that case skipped in the clean run and in the tampered run alike: the tampered run read green - BLIND - and one
# BLIND record shuts every lock on that PC (REG-1677). REG-1668 met the same wall in the frame-index law: a directory
# JUNCTION needs no privilege, and realpath resolves it (CPython 3.8+). link_dir makes a symlink where it can and a
# junction on Windows where it cannot. can_link_a_directory asks exactly that - the same routine, the same realpath -
# for heart2's PROOF_NEEDS_HOST "dir-link", so a proof that needs a link reads ELSEWHERE, never BLIND, on a PC that can
# make neither. Neither calls contain(): the probe is safe to import and run from the prover.
def link_dir(target, link):
    """Make `link` a directory link to `target`: a symlink, else (Windows) a directory junction. -> "symlink" |
    "junction" | None when this PC can make neither. Never raises."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return "symlink"
    except (OSError, NotImplementedError, AttributeError):
        pass
    if os.name != "nt":
        return None
    try:
        import _winapi                       # CPython's own junction maker (its test_os makes them this way)
        _winapi.CreateJunction(os.path.abspath(target), os.path.abspath(link))
        return "junction"
    except Exception:
        pass
    try:                                     # REG-1668's way: cmd's own `mklink /J`, no privilege needed
        import subprocess
        r = subprocess.run(["cmd", "/c", "mklink", "/J", os.path.abspath(link), os.path.abspath(target)],
                           capture_output=True, timeout=30)
        if r.returncode == 0 and os.path.isdir(link):
            return "junction"
    except Exception:
        pass
    return None


def unlink_dir_link(link):
    """Remove a link link_dir made: the LINK, never what it points at. Never raises."""
    try:
        os.unlink(link)                      # a symlink anywhere; a junction on Windows too
        return
    except OSError:
        pass
    try:
        os.rmdir(link)                       # a junction unlink would not take
    except OSError:
        pass


def can_link_a_directory():
    """heart2's PROOF_NEEDS_HOST probe for "dir-link" (REG-2366): can THIS PC make, in its temp dir, a directory link
    that realpath resolves - made by link_dir, exactly as the law makes it? -> bool. Links two directories of its own,
    removes both, touches nothing else."""
    base = None
    try:
        base = tempfile.mkdtemp(prefix="d2r-linkprobe-")
        target = os.path.join(base, "target")
        os.mkdir(target)
        link = os.path.join(base, "link")
        if not link_dir(target, link):
            return False
        try:
            return os.path.realpath(link) == os.path.realpath(target)
        finally:
            unlink_dir_link(link)
    except OSError:
        return False
    finally:
        if base:
            shutil.rmtree(base, ignore_errors=True)
