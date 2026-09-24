# -*- coding: utf-8 -*-
"""Children an os.execv relaunch would orphan into <defunct> — collect them first, reap the rest at boot.

⚠⚠ #224, MEASURED 2026-09-24 on his Mac (read-only audit, `ps -axo pid,ppid,stat,ucomm`): his console
(one pid since 09-23 17:05) carried 35 <defunct> children, every one `ocr_mac`, and 36 of 36 child
start times sat exactly one per console image. The console relaunches IN PLACE with os.execv — same
pid, new image — whenever the drift watcher sees new code on disk (35 times in that lifetime). The
warm tv_diablo `ocr_mac --worker` (`_OCR`, loaded in-process by stash_screen_open -> ocr_fast) was
alive at every exec: its Popen object vanished with the old image, its close-on-exec stdin shut, it
exited, and the new image had no handle to wait() it. Nothing in the console ever stopped it; the
v3481 close_ocr_worker fix covers a DIFFERENT worker (the Kai closer's), not this path.

Two halves, because either alone leaves a hole:
  · quiesce_before_exec() — every exec site stops the warm workers this image holds, so nothing is
    left to orphan. Found GENERICALLY (a module-global object holding a live subprocess.Popen in `.p`
    with a callable `.stop()`), so a new warm worker is covered without being named here.
  · children_of() + reap_inherited() — at boot, the children present BEFORE this image spawns anything
    are exactly the ones inherited from the previous image; they are reaped by PID (dead ones now, live
    ones on a daemon thread). ⚠ Never a blanket waitpid(-1): that would steal the exit status of the
    console's OWN Popen children, and CPython reads ECHILD as returncode 0 — a failed child would
    report success. [[the-unjoined-end]] [[process-port-discipline]]

Stdlib only. It stops only what THIS process started; it never kills by name.
"""
import os
import subprocess
import sys
import threading
import time

#: the modules whose module-global warm workers an exec would orphan
WARM_MODULES = ("tv_diablo",)


def warm_workers(modules=None):
    """-> [(module, name, obj)] module globals holding a LIVE Popen in `.p` and able to `.stop()`."""
    out = []
    for modname in (modules or WARM_MODULES):
        m = sys.modules.get(modname)
        if m is None:
            continue
        for name, obj in list(vars(m).items()):
            # a list/tuple of workers counts too — tv_diablo keeps its vision pool as `_WORKERS = [...]`
            pairs = ([("%s[%d]" % (name, i), x) for i, x in enumerate(obj)]
                     if isinstance(obj, (list, tuple)) else [(name, obj)])
            for label, o in pairs:
                p = getattr(o, "p", None)
                if isinstance(p, subprocess.Popen) and p.poll() is None and callable(getattr(o, "stop", None)):
                    out.append((modname, label, o))
    return out


def quiesce_before_exec(modules=None):
    """Stop every warm worker so os.execv leaves no child it can no longer wait on. -> [str]"""
    done = []
    for modname, name, obj in warm_workers(modules):
        try:
            obj.stop()
            done.append("%s.%s stopped" % (modname, name))
        except Exception as e:
            done.append("%s.%s stop FAILED (%s)" % (modname, name, type(e).__name__))
    return done


def children_of(pid=None):
    """-> [pid] children of `pid`, or None when that cannot be read (UNKNOWN, never an empty list)."""
    if os.name != "posix":
        return None
    pid = os.getpid() if pid is None else int(pid)
    try:
        pr = subprocess.Popen(["ps", "-axo", "pid=,ppid="], stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, universal_newlines=True)
        out, _ = pr.communicate(timeout=10)
    except Exception:
        return None
    kids = []
    for line in (out or "").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == str(pid) and parts[0] != str(pr.pid):
            try:
                kids.append(int(parts[0]))
            except ValueError:
                pass
    return kids


def reap_inherited(pids, retry_s=30.0, give_up_s=6 * 3600.0):
    """Reap children inherited across os.execv, BY PID. -> {"reaped", "waiting"}

    Dead ones are collected now; live ones (a worker that had not yet noticed its stdin close) on a
    daemon thread that retries until each is collected or `give_up_s` passes."""
    if os.name != "posix" or not pids:
        return {"reaped": 0, "waiting": 0}
    reaped, left = 0, []
    for p in pids:
        try:
            got, _st = os.waitpid(int(p), os.WNOHANG)
        except ChildProcessError:
            continue                        # not a child any more: nothing to collect
        if got == int(p):
            reaped += 1
        else:
            left.append(int(p))
    if left:
        def _loop(pending=list(left)):
            t0 = time.monotonic()
            while pending and time.monotonic() - t0 < give_up_s:
                time.sleep(retry_s)
                for p in list(pending):
                    try:
                        got, _st = os.waitpid(p, os.WNOHANG)
                        if got == p:
                            pending.remove(p)
                    except ChildProcessError:
                        pending.remove(p)
        threading.Thread(target=_loop, daemon=True, name="tvd-inherited-reaper").start()
    return {"reaped": reaped, "waiting": len(left)}
