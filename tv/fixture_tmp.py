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
