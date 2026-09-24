# -*- coding: utf-8 -*-
"""A relaunch that leaves a receipt, a boot that leaves a log, and on Windows a child that waits for its parent.

⚠⚠ #225, MEASURED 2026-09-24 over SSH on the Windows ALT box (read-only audit wf_1d3cd862-475): the console
there has been DEAD since 2026-09-23 00:26 local. It pulled v3419, relaunched itself with os.execv, the new
process imported tv_diablo (its .pyc stamped 00:26:02) and ran its boot git fetch (FETCH_HEAD 00:26:03) — and
then exited before its first beacon, WITH NO TRACE: pythonw drops stdout and stderr, and tv\\control_agent.log
does not exist. On Windows os.execv is not an in-place replace: it starts a NEW pid (measured 14808 -> 48672 on
an earlier relaunch that worked), so for a moment the old image can still hold the named primary mutex and
:17772, and both of those checks in main() end in a quiet sys.exit(0). Which of them killed v3419 is UNKNOWN —
nothing was written down. So this module makes the NEXT death say what it was, and removes the one race the
evidence points at:

  · boot_log()          — append a line per boot and per early exit to tv/.console_boot.log, BEFORE the mutex
                          and bind checks, so a pythonw death leaves its reason on disk.
  · install_excepthook() — an uncaught exception at boot is written there too, traceback and all.
  · write_receipt()      — the exec site records who relaunched, from which pid, to which version.
  · wait_for_parent()    — on Windows the child waits (bounded) for the parent pid to EXIT before it takes the
                           mutex and binds; on POSIX execv keeps the pid, so there is nothing to wait for.

Stdlib only; ctypes only on Windows. Never raises into the boot path: a failure to log must not become the
reason the console fails to start. [[unknown-stays-unknown]] [[the-unjoined-end]]
"""
import io
import json
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
IS_WIN = os.name == "nt"
ENV_PARENT = "TVD_RELAUNCH_PARENT"
LOG_MAX = 200_000          # bytes; the log is trimmed to its newest half past this


def _log_path():
    return os.environ.get("TV_CONSOLE_BOOT_LOG") or os.path.join(HERE, ".console_boot.log")


def _receipt_path():
    return os.environ.get("TV_RELAUNCH_RECEIPT") or os.path.join(HERE, ".relaunch_receipt.json")


def boot_log(event, **fields):
    """Append one line: time, pid, event, fields. -> bool (False when the line could not be written)."""
    try:
        p = _log_path()
        line = "%s pid=%d %s %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid(), event,
                                     json.dumps(fields, sort_keys=True, default=str))
        try:
            if os.path.getsize(p) > LOG_MAX:
                with io.open(p, encoding="utf-8", errors="replace") as fh:
                    keep = fh.read()[-LOG_MAX // 2:]
                with io.open(p, "w", encoding="utf-8") as fh:
                    fh.write(keep)
        except OSError:
            pass
        with io.open(p, "a", encoding="utf-8") as fh:
            fh.write(line)
        return True
    except Exception:
        return False


def install_excepthook():
    """Record an uncaught exception in the boot log, then defer to the previous hook."""
    prev = sys.excepthook

    def _hook(tp, val, tb):
        try:
            boot_log("uncaught-exception", type=getattr(tp, "__name__", str(tp)), error=str(val)[:300],
                     traceback="".join(traceback.format_exception(tp, val, tb))[-2000:])
        finally:
            prev(tp, val, tb)
    sys.excepthook = _hook
    return _hook


def write_receipt(where, to_version=None):
    """Called at an exec site: who relaunched, from which pid, to which version. -> bool"""
    try:
        rec = {"ts": int(time.time() * 1000), "where": str(where), "fromPid": os.getpid(),
               "toVersion": to_version, "platform": sys.platform}
        p = _receipt_path()
        tmp = p + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(rec))
        os.replace(tmp, p)
        os.environ[ENV_PARENT] = str(os.getpid())          # inherited by the exec'd child
        return True
    except Exception:
        return False


def read_receipt():
    """-> the last receipt dict, or None when there is none or it cannot be read (UNKNOWN, never {})."""
    try:
        with io.open(_receipt_path(), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def wait_for_parent(timeout_s=20.0):
    """On Windows, wait for the relaunching parent to EXIT before the mutex/bind checks. -> dict

    {"waited": bool, "parent": pid|None, "exited": True|False|None, "seconds": float, "why": str}.
    `exited` None means it could not be established (no parent named, not Windows, or the wait failed)."""
    raw = os.environ.pop(ENV_PARENT, None)
    out = {"waited": False, "parent": None, "exited": None, "seconds": 0.0, "why": ""}
    if not raw:
        out["why"] = "not a relaunch (no parent named)"
        return out
    try:
        parent = int(raw)
    except ValueError:
        out["why"] = "unreadable parent %r" % raw
        return out
    out["parent"] = parent
    if parent == os.getpid():
        out["why"] = "same pid (POSIX execv replaced the image in place) - nothing to wait for"
        out["exited"] = None
        return out
    if not IS_WIN:
        out["why"] = "not Windows"
        return out
    t0 = time.monotonic()
    try:
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.windll.kernel32
        k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k32.WaitForSingleObject.restype = wintypes.DWORD
        SYNCHRONIZE, WAIT_OBJECT_0, WAIT_TIMEOUT = 0x00100000, 0, 0x102
        h = k32.OpenProcess(SYNCHRONIZE, False, parent)
        if not h:
            out.update(waited=True, exited=True, why="parent already gone")     # cannot open = no process
        else:
            try:
                r = k32.WaitForSingleObject(h, int(timeout_s * 1000))
            finally:
                k32.CloseHandle(h)
            out["waited"] = True
            out["exited"] = (r == WAIT_OBJECT_0)
            out["why"] = ("parent exited" if r == WAIT_OBJECT_0 else
                          "parent still alive after %.0fs" % timeout_s if r == WAIT_TIMEOUT else
                          "wait returned %d" % r)
    except Exception as e:
        out["why"] = "the wait could not run (%s)" % type(e).__name__
    out["seconds"] = round(time.monotonic() - t0, 2)
    return out
