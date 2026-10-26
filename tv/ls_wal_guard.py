# -*- coding: utf-8 -*-
"""THE MAC CONSOLE'S WEBKIT LOCALSTORAGE WAL IS PRUNED, AND NEVER GROWS SILENTLY AGAIN.

Konyo 2026-10-25: "not only shrink it it needs a automatic pruning there too". The native console
(control_app.py --open, a python3 WebKit window) keeps localStorage in
~/Library/WebKit/com.apple.python3/WebsiteData/.../LocalStorage/localstorage.sqlite3. A hot write
loop (fixed in v3796, law tests/v3797_ls_no_hot_writes.spec.ts) grew its -wal to 26 GB. SQLite
never shrinks a WAL while a connection holds it, and WebKit never truncates it on its own.

THREE PARTS, all additive:
  1. startup_prune()  - before the WebView exists: every localstorage.sqlite3 whose -wal is over
     the threshold and that NO process holds gets wal_checkpoint(TRUNCATE) + integrity_check.
     A file that is held, or whose holders cannot be read, is SKIPPED (fail safe). Never removes
     the db or the WAL itself; SQLite's own last-connection close unlinks the then-empty -wal/-shm
     after the checkpoint (WebKit recreates them). The before/after sizes are logged.
  2. periodic_check() - every 30 min while the console is up: logs the WAL size, publishes it on
     /api/status (lsWal), and warns when over the threshold. While WebKit holds the db it runs a
     PASSIVE checkpoint only. PASSIVE never takes the writer lock and never waits on a reader, so
     it cannot make a WebKit write fail; TRUNCATE/RESTART would hold the writer lock while waiting
     for WebKit's readers, and a WebKit write that hits SQLITE_BUSY there is a lost localStorage
     write. So the file is never truncated while held - the next startup does that.
  3. Any process already holding the file at startup is, by construction, left over from an
     earlier console (this one has no WebView yet) - e.g. the 31-hour WebKit Networking orphan
     seen 2026-10-25. It is REPORTED with pid/age/command, never killed.

macOS only; a no-op elsewhere. Paths come from expanduser, never a literal home.
"""
import glob
import os
import sqlite3
import subprocess
import sys
import time

THRESHOLD_BYTES = 256 * 1024 * 1024
PERIOD_S = 30 * 60
BUSY_TIMEOUT_S = 0.5
_BUNDLE_DIRS = ("~/Library/WebKit/com.apple.python3/WebsiteData",)

#: Last result, read by /api/status with no I/O. None until the first look.
STATE = {"checked": False}


def is_mac(platform=None):
    return (platform or sys.platform) == "darwin"


def webkit_roots():
    return [os.path.expanduser(p) for p in _BUNDLE_DIRS]


def find_dbs(roots):
    # Bounded depth (WebsiteData/Default/<h>/<h>/LocalStorage): never a walk of every WebKit cache.
    out = []
    for r in roots:
        if os.path.isdir(r):
            for depth in range(4):
                out.extend(glob.glob(os.path.join(r, *(["*"] * depth), "LocalStorage", "localstorage.sqlite3")))
    return sorted(set(out))


def _size(p):
    """Byte size, 0 when the file was never written, None when the read failed.

    A missing log and a log that cannot be read are different facts. Returning 0
    for both would let a permission failure look like an empty log.
    """
    try:
        return os.path.getsize(p)
    except FileNotFoundError:
        return 0
    except OSError:
        return None


def holders(db, run=subprocess.run):
    """-> set of pids holding db / -wal / -shm, or None when it could not be read (UNKNOWN)."""
    files = [f for f in (db, db + "-wal", db + "-shm") if os.path.exists(f)]
    try:
        r = run(["lsof", "-t", "--"] + files, capture_output=True, text=True, timeout=10)
    except Exception:
        return None
    # macOS lsof exits 1 when ANY named file has no opener, and also beside a harmless
    # "can't stat() ... file system" warning - so the pid list is read regardless of the code.
    pids = {int(x) for x in (r.stdout or "").split() if x.strip().isdigit()}
    if pids:
        return pids
    if r.returncode in (0, 1):
        return set()       # lsof ran and named nobody - measured, not assumed
    return None


def describe(pids, run=subprocess.run):
    """pid -> 'etime comm' for the report. Unreadable is said, never dropped."""
    out = {}
    for pid in sorted(pids):
        try:
            r = run(["ps", "-o", "etime=,comm=", "-p", str(pid)], capture_output=True, text=True, timeout=5)
            out[pid] = (r.stdout or "").strip() or "unreadable"
        except Exception:
            out[pid] = "unreadable"
    return out


def checkpoint(db, mode):
    """-> (busy, log_frames, checkpointed, integrity). Opens its own short-timeout connection."""
    con = sqlite3.connect(db, timeout=BUSY_TIMEOUT_S)
    try:
        busy, nlog, ncp = con.execute("PRAGMA wal_checkpoint(%s)" % mode).fetchone()
        integ = con.execute("PRAGMA integrity_check").fetchone()[0] if mode == "TRUNCATE" else None
        return busy, nlog, ncp, integ
    finally:
        con.close()


def _log(msg, log):
    (log or (lambda m: print(m, flush=True)))("ls-wal: " + msg)


def startup_prune(roots=None, platform=None, threshold=THRESHOLD_BYTES, run=subprocess.run, log=None):
    """Part 1 + 3. Call BEFORE the WebView is created. -> list of per-db result dicts."""
    if not is_mac(platform):
        return []
    results = []
    for db in find_dbs(roots if roots is not None else webkit_roots()):
        wal = db + "-wal"
        before = _size(wal)
        res = {"db": db, "walBefore": before, "action": "none"}
        if before is None:
            res["action"] = "skipped-unknown-size"
            _log("WAL size unreadable - skipped", log)
            results.append(res)
            continue
        held = holders(db, run=run)
        if held:
            res["leftover"] = describe(held, run=run)
            _log("LEFTOVER process(es) hold %s before this console made a WebView - not killed, "
                 "report only: %s" % (db, res["leftover"]), log)
        if held is not None and not held and before > threshold:
            _log("TRUNCATE starting on %s: WAL %d MB" % (db, before >> 20), log)
        if before <= threshold:
            results.append(res)
            continue
        if held is None:
            res["action"] = "skipped-unknown-holders"
            _log("WAL %d MB over threshold but holders unreadable - skipped" % (before >> 20), log)
        elif held:
            res["action"] = "skipped-held"
            _log("WAL %d MB over threshold but held by %s - skipped" % (before >> 20, sorted(held)), log)
        else:
            try:
                busy, _n, _c, integ = checkpoint(db, "TRUNCATE")
                res.update(action="truncated" if not busy else "busy", integrity=integ,
                           walAfter=_size(wal))
                _log("TRUNCATE %s: WAL %d -> %d bytes, busy=%s, integrity=%s"
                     % (db, before, res["walAfter"], busy, integ), log)
            except Exception as e:
                res.update(action="error", error=ascii(e)[:200])
                _log("checkpoint failed: %s" % ascii(e)[:200], log)
        results.append(res)
    STATE["startup"] = [{k: v for k, v in r.items() if k != "db"} for r in results]
    return results


def periodic_check(roots=None, platform=None, threshold=THRESHOLD_BYTES, log=None, state=None):
    """Part 2. Size + warning + PASSIVE checkpoint only (safe beside a live WebKit writer)."""
    state = STATE if state is None else state
    if not is_mac(platform):
        state.update(checked=True, applies=False)
        return state
    dbs = find_dbs(roots if roots is not None else webkit_roots())
    raw = [(db, _size(db + "-wal")) for db in dbs]
    known = [n for _db, n in raw if n is not None]
    unknown = len(raw) - len(known)
    worst = max(known) if known else None
    known_over = any(n > threshold for n in known)
    if known_over:
        over = True
        warning = ("LocalStorage WAL is %d MB (over %d MB) - restart the console to shrink it"
                   % (worst >> 20, threshold >> 20))
    elif unknown:
        over = None
        warning = "LocalStorage WAL size could not be read"
    else:
        over = False
        warning = None
    state.update(checked=True, applies=True, dbs=len(dbs), walBytes=worst,
                 thresholdBytes=threshold, over=over, atMs=int(time.time() * 1000),
                 warning=warning)
    if worst is None:
        _log("WAL size unreadable across %d db(s)" % len(dbs), log)
    else:
        _log("WAL %d MB across %d db(s)%s" % (worst >> 20, len(dbs), " - OVER THRESHOLD" if known_over else ""), log)
    # published BEFORE the checkpoint, so a long PASSIVE copy is never a silent status
    for db, sz in raw:
        if sz is not None and sz > threshold:
            try:
                checkpoint(db, "PASSIVE")
            except Exception as e:
                _log("PASSIVE checkpoint failed: %s" % ascii(e)[:200], log)
    return state


def _ls_wal_loop(period=PERIOD_S):
    while True:
        try:
            periodic_check()
        except Exception as e:
            _log("periodic check failed: %s" % ascii(e)[:200], None)
        try:
            from control_app import _lane_tick
            _lane_tick("tvd-lswal", period)
        except Exception:
            pass
        time.sleep(period)
