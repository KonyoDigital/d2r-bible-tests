#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#170 (REG-2483) - KEEP THIS PC AWAKE ONLY WHILE A PROOF RUNS, AND LET IT SLEEP THE MOMENT THE PROOF ENDS.

His ruling, 2026-10-21 22:45: *only while working*. Dean's laptop slept in the middle of a proof. MEASURED on his PC
2026-10-22 (powercfg, read-only): standby never on AC or DC, hibernate after 7,200 s on battery only - and the 15:30
drop that day was Kernel-Power 42, "Button or Lid": he closed the lid. So a hold matters on battery, and a lid close
still wins. That stays the OS's call, and his.

THE CONTRACT (the console calls these; nothing else here is public):
    held(why)               a context manager: THIS thread holds the PC awake for the with-block. Never raises; an
                            exception inside the block still propagates, and the hold is released either way.
    hold_for_pid(pid, why)  hold while that process lives. Idempotent per pid, and it ends by itself when the process
                            ends - a normal exit or a kill. Never raises. -> {"held": True|False, "pid", "why"}
    status()                {"on", "holds", "lastTs", "why"} (+ "list", "door", "platform", "taken", "released",
                            "refused"): on = a hold is live right now, holds = how many, lastTs = when one was last
                            taken, released or refused (epoch ms; None = never since this process started).

ONE LOGIC, EVERY PC:
  Windows  SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED) = 0x80000001, and nothing else: never the
           display flag (his screen still turns off), never away mode, never powercfg, never the registry - a hold
           changes no setting of his and leaves nothing behind. The state belongs to the THREAD that set it and the
           OS drops it when that thread ends, so a pid hold lives on a watcher thread that waits on the process
           handle and releases with ES_CONTINUOUS alone the moment the process ends.
  macOS    `caffeinate -i -w <pid>`: an idle-sleep assertion bound to a pid, so it ends when that process does (a dead
           prover; for held(), a dead console). Never -d / -u / -s. Spawned posix_spawn-safe (an absolute executable
           and close_fds=False): the console has the Objective-C runtime loaded, and a fork there is the deadlock
           #150 measured.
  other    nothing is held, and status() says so - never a hold this module could not release.

[[heart-first]] [[i-own-everything-i-start]] [[unknown-stays-unknown]]
"""
import contextlib
import os
import subprocess
import sys
import threading
import time

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
#: the ONLY flags a hold ever asks for (0x80000001)
HOLD_FLAGS = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
#: what ends a hold: ES_CONTINUOUS alone clears this thread's requirement
RELEASE_FLAGS = ES_CONTINUOUS
SYNCHRONIZE = 0x00100000
INFINITE = 0xFFFFFFFF
#: how long hold_for_pid waits for its watcher thread to say whether the hold was taken
TAKE_WAIT_S = 2.0
#: how long a held() block's caffeinate is given to end after it is asked to
END_WAIT_S = 5.0

_LOCK = threading.Lock()
_HOLDS = {}                 # ("pid", pid) | ("block", n) -> the hold's record
_LOCAL = threading.local()  # Windows: this thread's held() depth, and whether its first take succeeded
_SEQ = [0]
_LAST = {"ts": None, "say": "nothing has asked this PC to stay awake since this process started",
         "taken": 0, "released": 0, "refused": 0}
_K = {"k": None}


def _platform():
    """A seam: the law drives each OS's branch on any PC."""
    return sys.platform


def _now_ms():
    return int(time.time() * 1000)


def _note(say, kind=None):
    _LAST["ts"] = _now_ms()
    _LAST["say"] = say
    if kind:
        _LAST[kind] = int(_LAST.get(kind) or 0) + 1


def _kernel():
    """kernel32 through its OWN ctypes handle, with its argument types declared here. -> the library. A seam.

    Never ctypes.windll.kernel32: declaring restype/argtypes on the shared object would change them under
    child_guard and every other module that calls kernel32, and a HANDLE is pointer-wide on 64-bit Windows."""
    if _K["k"] is None:
        import ctypes
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.SetThreadExecutionState.argtypes = [wintypes.DWORD]
        k.SetThreadExecutionState.restype = wintypes.DWORD
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenProcess.restype = wintypes.HANDLE
        k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k.WaitForSingleObject.restype = wintypes.DWORD
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.CloseHandle.restype = wintypes.BOOL
        _K["k"] = k
    return _K["k"]


def caffeinate_argv(pid):
    """The ONE macOS argv: an idle-sleep assertion bound to `pid`, so it ends when that process ends. -> list"""
    return ["caffeinate", "-i", "-w", str(int(pid))]


def _caffeinate_exe():
    """caffeinate's absolute path, or None. posix_spawn is taken only for an executable with a dirname."""
    if os.path.isfile("/usr/bin/caffeinate"):
        return "/usr/bin/caffeinate"
    import shutil
    return shutil.which("caffeinate")


def _spawn(argv):
    """Start a macOS hold: stdio closed off, posix_spawn-safe. -> Popen. A seam."""
    exe = _caffeinate_exe()
    if not exe:
        raise FileNotFoundError("caffeinate is not on this Mac")
    return subprocess.Popen(argv, executable=exe, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, close_fds=False)


def _end_proc(p):
    """End a held() block's caffeinate and reap it, so nothing we started is left a corpse."""
    if p.poll() is None:
        p.terminate()
        try:
            p.wait(END_WAIT_S)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait(END_WAIT_S)


def _alive(rec):
    """Is this hold live right now? -> bool"""
    if rec.get("state") == "starting" or rec.get("kind") == "block":
        return True
    p = rec.get("proc")
    if p is not None:
        return p.poll() is None
    t = rec.get("thread")
    return bool(t is not None and t.is_alive() and rec.get("taken"))


# -- held(why): this thread, the with-block -------------------------------------------------------------------------

def _take_block(why):
    tok = {"key": None, "taken": False, "why": str(why or "work is running")}
    try:
        plat = _platform()
        with _LOCK:
            _SEQ[0] += 1
            tok["key"] = ("block", _SEQ[0])
        if plat == "win32":
            depth = int(getattr(_LOCAL, "depth", 0) or 0)
            tok["win"] = True
            _LOCAL.depth = depth + 1
            if depth == 0:
                _LOCAL.took = bool(_kernel().SetThreadExecutionState(HOLD_FLAGS))
            tok["taken"] = bool(getattr(_LOCAL, "took", False))
        elif plat == "darwin":
            tok["proc"] = _spawn(caffeinate_argv(os.getpid()))
            tok["taken"] = True
        if tok["taken"]:
            with _LOCK:
                _HOLDS[tok["key"]] = {"kind": "block", "pid": os.getpid(), "why": tok["why"], "since": _now_ms(),
                                      "state": "held", "taken": True, "proc": tok.get("proc")}
            _note("held awake for: %s" % tok["why"], "taken")
        else:
            _note("not held for %s: %s" % (tok["why"], _no_door(plat)), "refused")
    except Exception as e:
        tok["err"] = type(e).__name__
        _note("the hold for %s could not be taken (%s) - this PC sleeps as it always would"
              % (tok["why"], type(e).__name__), "refused")
    return tok


def _end_block(tok):
    try:
        if tok.get("win"):
            depth = max(0, int(getattr(_LOCAL, "depth", 1) or 1) - 1)
            _LOCAL.depth = depth
            if depth == 0 and getattr(_LOCAL, "took", False):
                _LOCAL.took = False
                _kernel().SetThreadExecutionState(RELEASE_FLAGS)
        if tok.get("proc") is not None:
            _end_proc(tok["proc"])
    except Exception as e:
        tok["endErr"] = type(e).__name__
    finally:
        with _LOCK:
            _HOLDS.pop(tok.get("key"), None)
        if tok.get("taken"):
            _note("released: %s ended" % tok.get("why"), "released")


@contextlib.contextmanager
def held(why=""):
    """Hold this PC awake for the with-block, on THIS thread. Never raises; the block's own exception propagates."""
    tok = _take_block(why)
    try:
        yield tok
    finally:
        _end_block(tok)


# -- hold_for_pid(pid, why): while that process lives -------------------------------------------------------------

def _watch_win(k, h, key, rec, started):
    """The watcher thread: take the hold HERE, wait for the process to end, release HERE. The state is per thread."""
    took = False
    try:
        try:
            took = bool(k.SetThreadExecutionState(HOLD_FLAGS))
        finally:
            rec["taken"] = took
            rec["state"] = "held" if took else "refused"
            started.set()
        if took:
            _note("held awake while pid %s runs (%s)" % (rec.get("pid"), rec.get("why")), "taken")
            k.WaitForSingleObject(h, INFINITE)      # returns when the process ends: a normal exit or a kill
    except Exception as e:
        rec["err"] = type(e).__name__
    finally:
        if took:
            try:
                k.SetThreadExecutionState(RELEASE_FLAGS)
            except Exception as e:
                rec["releaseErr"] = type(e).__name__
        try:
            k.CloseHandle(h)
        except Exception as e:
            rec["closeErr"] = type(e).__name__
        rec["state"] = "ended"
        with _LOCK:
            if _HOLDS.get(key) is rec:
                _HOLDS.pop(key, None)
        if took:
            _note("released: pid %s ended (%s)" % (rec.get("pid"), rec.get("why")), "released")


def _reap_mac(p, key, rec):
    """caffeinate -w ends by itself when the pid does; wait for it, so it is never left a corpse."""
    try:
        p.wait()
    except Exception as e:
        rec["err"] = type(e).__name__
    finally:
        rec["state"] = "ended"
        with _LOCK:
            if _HOLDS.get(key) is rec:
                _HOLDS.pop(key, None)
        _note("released: pid %s ended (%s)" % (rec.get("pid"), rec.get("why")), "released")


def _hold_for_pid(pid, why):
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return {"held": False, "pid": pid, "why": "%r is not a pid - nothing is held" % (pid,)}
    why = str(why or "work is running")
    if pid <= 0:
        return {"held": False, "pid": pid, "why": "%d is not a process - nothing is held" % pid}
    key = ("pid", pid)
    with _LOCK:
        cur = _HOLDS.get(key)
        if cur is not None and _alive(cur):
            return {"held": True, "pid": pid, "already": True,
                    "why": "already held while pid %d runs (%s)" % (pid, cur.get("why"))}
        rec = {"kind": "pid", "pid": pid, "why": why, "since": _now_ms(), "state": "starting", "taken": None}
        _HOLDS[key] = rec
    plat = _platform()
    try:
        if plat == "win32":
            k = _kernel()
            h = k.OpenProcess(SYNCHRONIZE, False, pid)
            if not h:
                raise LookupError("pid %d could not be opened to wait on (it has ended, or it is not this "
                                  "user's)" % pid)
            started = threading.Event()
            t = threading.Thread(target=_watch_win, args=(k, h, key, rec, started), name="keep-awake-%d" % pid)
            t.daemon = True
            rec["thread"] = t
            try:
                t.start()
            except Exception:
                k.CloseHandle(h)            # the watcher never ran, so nothing else will close what we opened
                raise
            started.wait(TAKE_WAIT_S)
            if rec.get("taken"):
                return {"held": True, "pid": pid, "why": "held awake while pid %d runs (%s)" % (pid, why)}
            if rec.get("taken") is None:
                return {"held": None, "pid": pid,
                        "why": "the hold for pid %d had not answered after %.0f s - status() says whether it was "
                               "taken" % (pid, TAKE_WAIT_S)}
            return {"held": False, "pid": pid,
                    "why": "Windows refused the hold for pid %d (%s) - this PC sleeps as it always would"
                           % (pid, rec.get("err") or "SetThreadExecutionState answered 0")}
        if plat == "darwin":
            p = _spawn(caffeinate_argv(pid))
            rec.update(proc=p, taken=True, state="held")
            _note("held awake while pid %d runs (%s)" % (pid, why), "taken")
            t = threading.Thread(target=_reap_mac, args=(p, key, rec), name="keep-awake-%d" % pid)
            t.daemon = True
            t.start()
            return {"held": True, "pid": pid, "why": "held awake while pid %d runs (%s)" % (pid, why)}
        raise LookupError(_no_door(plat))
    except Exception as e:
        with _LOCK:
            if _HOLDS.get(key) is rec:
                _HOLDS.pop(key, None)
        rec["state"] = "refused"
        say = str(e) if isinstance(e, LookupError) else "the hold could not be taken (%s)" % type(e).__name__
        _note("not held for pid %d: %s" % (pid, say), "refused")
        return {"held": False, "pid": pid, "why": "not held: %s" % say}


def hold_for_pid(pid, why=""):
    """Hold this PC awake while `pid` runs. Idempotent; ends when the process ends. Never raises. -> dict"""
    try:
        return _hold_for_pid(pid, why)
    except Exception as e:
        return {"held": False, "pid": pid, "why": "not held: the hold could not be taken (%s)" % type(e).__name__}


# -- status() --------------------------------------------------------------------------------------------------------

def _no_door(plat):
    return "%s has no keep-awake door here - only Windows and macOS hold" % plat


def _door(plat):
    if plat == "win32":
        return "SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)"
    if plat == "darwin":
        return "caffeinate -i -w <pid>"
    return None


def status():
    """The lane's own words. -> {"on", "holds", "lastTs", "why", ...}. Never raises."""
    try:
        with _LOCK:
            live = [r for r in _HOLDS.values() if _alive(r)]
            rows = [{"kind": r.get("kind"), "pid": r.get("pid"), "why": r.get("why"), "since": r.get("since")}
                    for r in live]
        plat = _platform()
        if rows:
            why = ("held awake - idle sleep only, the screen may still turn off - while %s"
                   % "; ".join("%s (pid %s)" % (r["why"], r["pid"]) for r in rows))
        else:
            why = "not held - %s" % _LAST["say"]
        return {"on": bool(rows), "holds": len(rows), "lastTs": _LAST["ts"], "why": why, "list": rows,
                "door": _door(plat), "platform": plat, "taken": _LAST["taken"], "released": _LAST["released"],
                "refused": _LAST["refused"]}
    except Exception as e:
        return {"on": None, "holds": None, "lastTs": None,
                "why": "the keep-awake state could not be read (%s) - UNKNOWN, not off" % type(e).__name__}
