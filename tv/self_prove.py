# -*- coding: utf-8 -*-
"""#50 — EVERY PC PROVES ITS OWN INSTRUMENTS, IN THE BACKGROUND, WITHOUT BEING ASKED (REG-1447).

His ruling, 2026-09-29: *"i think it does need to get proved on the windows alt right? and on deans?"*
Measured the same morning, it does. A heart census proves that THIS machine's gates can still go red, and
the Mac's proof does not speak for Windows:
  · at the same clean commit the ALT's gate fingerprint was 2d9eff1d against the Mac's 56b2a8c3 - on
    Windows run_gates would not even import (REG-1445), and with that fixed it lists 679 gates to 678;
  · a one-law trial prove on the ALT found the river-outlet law BLIND there (green through its own
    sabotage) while it goes red on the Mac - the Mac's sandbox happened to carry one of HIS reels.

So the census is per-machine, and until today only the pre-push gate on his Mac ever wrote one. Every
other PC - the ALT, Dean's - had `.heart2.json` absent, so `self_arming.may()` answered "the heart has
never run here" and every lock stayed shut: 76 ALT reels at EMPTY never ROUTED.

This lane closes that. On an INSTALLED console (clean tree, at its upstream) whose census is absent or
stale for the gates now on disk, it starts `heart2.py --prove` in the background - hidden, at the lowest
ordinary priority, one lane - but only while the machine is idle. It never runs on a DEVELOPMENT tree:
there the pre-push gate is the prover, and a background prove would fight it for the CPU (a fleet during a
push starved the render gate, 2026-09-2x). Nothing here decides a verdict; heart2 writes the census and
self_arming reads it, exactly as on his Mac.

THE SHARED VOCABULARY (heart-first rule 3): on · worked · lastTs · owed, with owed None = UNKNOWN.
"""
import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
IS_WIN = os.name == "nt"

STORE = ".self_prove.json"
#: Busier than this (percent of the machine) and a proof does not START - he is playing, or the console is
#: working. A running proof is never killed for it: it already runs below everything he does.
MAX_BUSY_TO_START = 45.0
#: A proof that ended without making the census current is not retried for this long - a failing prover
#: must not become a machine that proves in a loop all day.
RETRY_AFTER_FAIL_S = 3 * 3600
#: Windows priority class for the prover: BELOW_NORMAL, so his game and the console always come first.
_BELOW_NORMAL = 0x00004000
_CREATE_NO_WINDOW = 0x08000000


def enabled(env=None):
    """TV_SELF_PROVE=0 turns the lane off. -> bool"""
    return (env if env is not None else os.environ).get("TV_SELF_PROVE", "1") != "0"


def _store_path(path=None):
    if path:
        return path
    try:
        import tv_diablo as _tvd
        return os.path.join(_tvd._fixture_root(HERE), STORE)
    except ImportError:
        return os.path.join(HERE, STORE)


def load(path=None):
    """The lane's memory. -> dict ({} when it has never run; {"unreadable": why} when it would not read)"""
    p = _store_path(path)
    if not os.path.exists(p):
        return {}
    try:
        with io.open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {"unreadable": "not an object"}
    except Exception as e:
        return {"unreadable": "%s" % type(e).__name__}


def save(d, path=None):
    p = _store_path(path)
    tmp = p + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1, sort_keys=True)
    os.replace(tmp, p)


def pid_alive(pid):
    """Is `pid` a living process? -> bool. Safe on Windows.

    ⚠⚠ `os.kill(pid, 0)` IS NOT A PROBE ON WINDOWS. There, signal 0 is CTRL_C_EVENT, delivered with
    GenerateConsoleCtrlEvent - so the Unix idiom heart2 used to ask "is the sandbox owner alive?" would
    send a Ctrl-C instead. Windows asks with OpenProcess + GetExitCodeProcess, the way control_app does.
    """
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if IS_WIN:
        try:
            import ctypes
            from ctypes import wintypes
            k32 = ctypes.windll.kernel32
            h = k32.OpenProcess(0x1000, False, pid)      # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return False
            try:
                code = wintypes.DWORD()
                if not k32.GetExitCodeProcess(h, ctypes.byref(code)):
                    return False
                return int(code.value) == 259          # STILL_ACTIVE
            finally:
                k32.CloseHandle(h)
        except Exception:
            return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def census_state():
    """Is THIS machine's census current for the gates on disk? -> dict

    state: current | stale | missing | unreadable | unknown. Only `current` means nothing is owed.
    """
    try:
        import heart2 as _h2
    except Exception as e:
        return {"state": "unknown", "why": "heart2 would not import (%s) - whether this PC is proven "
                                           "is UNKNOWN" % type(e).__name__}
    p = _h2.STATE
    if not os.path.exists(p):
        try:
            fp = _h2.gates_fingerprint()
        except Exception:
            fp = None
        return {"state": "missing", "why": "this PC has never proved its instruments", "fingerprint": fp}
    try:
        with io.open(p, encoding="utf-8") as fh:
            st = json.load(fh)
    except Exception as e:
        return {"state": "unreadable", "why": "the census would not parse (%s)" % type(e).__name__}
    try:
        have = _h2.gates_fingerprint()
    except Exception as e:
        return {"state": "unknown", "why": "the gate fingerprint could not be computed (%s)"
                                           % type(e).__name__}
    want = st.get("gatesFingerprint")
    out = {"proved": st.get("proved"), "declared": st.get("declared"),
           "blind": list(st.get("blind") or []), "ranAt": st.get("ranAt"),
           "fingerprint": have}
    if want != have:
        out.update(state="stale", why="the gates changed since this PC last proved them (%s != %s)"
                                      % (str(want)[:8], have[:8]))
    else:
        out.update(state="current", why="proved for the gates on disk: %s of %s, %d blind"
                                        % (st.get("proved"), st.get("declared"), len(out["blind"])))
    return out


def _git(*args, timeout=15):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    r = subprocess.run(["git"] + list(args), cwd=REPO, capture_output=True, text=True,
                       timeout=timeout, env=env)
    return r.returncode, (r.stdout or "").strip()


def tree_state(git=None):
    """Is this an INSTALLED console (clean, at its upstream) or a development tree? -> (kind, why)

    kind: installed | dev | unknown. Only `installed` may prove in the background.
    """
    g = git or _git
    try:
        rc, dirty = g("status", "--porcelain", "--untracked-files=no")
        if rc != 0:
            return "unknown", "git status failed here, so this tree cannot be told apart from a dev tree"
        if dirty:
            return "dev", "the tree has local edits - the pre-push gate proves a development tree"
        rc, counts = g("rev-list", "--left-right", "--count", "@{upstream}...HEAD")
        if rc != 0 or not counts:
            return "unknown", "this checkout has no upstream to compare with"
        behind, ahead = [int(x) for x in counts.split()[:2]]
        if ahead:
            return "dev", "%d local commit(s) not yet on origin - the pre-push gate proves them" % ahead
        if behind:
            return "installed", "an installed console %d commit(s) behind origin" % behind
        return "installed", "an installed console, level with origin"
    except Exception as e:
        return "unknown", "git could not be asked (%s)" % type(e).__name__


def decide(census, tree, running_pid, busy_pct, mem, now_s, on=True):
    """THE ONE DECISION. Pure. -> {"start": bool, "key": str, "why": str}"""
    if not on:
        return {"start": False, "key": "off", "why": "the self-prove lane is off (TV_SELF_PROVE=0)"}
    if running_pid:
        return {"start": False, "key": "running",
                "why": "a proof is running (pid %s, since %s)" % (running_pid, mem.get("startedAt"))}
    st = (census or {}).get("state")
    if st == "current":
        return {"start": False, "key": "current", "why": census.get("why") or "current"}
    if st == "unknown":
        return {"start": False, "key": "unknown", "why": census.get("why") or "UNKNOWN"}
    kind, twhy = tree
    if kind != "installed":
        return {"start": False, "key": "dev" if kind == "dev" else "tree-unknown",
                "why": "not proving here: %s" % twhy}
    try:
        last_fail = float(mem.get("lastFailAt")) if mem.get("lastFailAt") is not None else None
    except (TypeError, ValueError):
        last_fail = now_s                                  # an unreadable failure time backs off, never races
    if last_fail is not None and mem.get("lastFailFingerprint") == (census or {}).get("fingerprint") \
            and now_s - last_fail < RETRY_AFTER_FAIL_S:
        return {"start": False, "key": "backoff",
                "why": "the last proof for these gates ended without a census (%s); retrying after %d h"
                       % (mem.get("lastFailWhy") or "?", RETRY_AFTER_FAIL_S // 3600)}
    try:
        busy_pct = None if busy_pct is None else float(busy_pct)
    except (TypeError, ValueError):
        busy_pct = None
    if busy_pct is None or busy_pct != busy_pct:          # None, junk, or NaN: UNKNOWN, never idle
        return {"start": False, "key": "load-unknown",
                "why": "how busy this machine is could not be measured - a proof is not started on a guess"}
    if busy_pct >= MAX_BUSY_TO_START:
        return {"start": False, "key": "busy",
                "why": "the machine is %.0f%% busy - a proof starts only when it is idle" % busy_pct}
    return {"start": True, "key": "start",
            "why": "census %s (%s) on an idle installed console - proving" % (st, census.get("why"))}


def spawn(log_path, python=None, workers=1, popen=None):
    """Start `heart2.py --prove` hidden and below everything he does. -> pid"""
    py = python or sys.executable
    if IS_WIN and py.lower().endswith("pythonw.exe"):
        cand = py[:-len("pythonw.exe")] + "python.exe"   # pythonw has no stdout for the prover's log
        if os.path.exists(cand):
            py = cand
    env = dict(os.environ, HEART2_PROVE_WORKERS=str(int(workers)), PYTHONIOENCODING="utf-8")
    kw = {"cwd": HERE, "env": env, "stdin": subprocess.DEVNULL}
    if IS_WIN:
        kw["creationflags"] = _BELOW_NORMAL | _CREATE_NO_WINDOW
    else:
        # ⚠ `nice` THE COMMAND, not preexec_fn: this runs inside the console's threaded server, and
        # Python documents preexec_fn as unsafe when threads are running.
        kw["start_new_session"] = True
    cmd = [py, os.path.join(HERE, "heart2.py"), "--prove"]
    if not IS_WIN and os.path.exists("/usr/bin/nice"):
        cmd = ["/usr/bin/nice", "-n", "15"] + cmd
    log = open(log_path, "ab")
    kw["stdout"] = log
    kw["stderr"] = subprocess.STDOUT
    try:
        p = (popen or subprocess.Popen)(cmd, **kw)
    finally:
        log.close()                       # the child holds its own handle
    return p.pid


#: ⚠ second eye (Grok, 2026-09-29): the pid of a proof THIS process started, kept in memory too. If saving
#: the lane's store failed right after a spawn, the next tick read no pid and started a SECOND prover - and
#: another every ten minutes after that. The store is the record; this is the backstop.
_STARTED = {"pid": None}


def tick(now_s=None, busy=None, tree=None, census=None, path=None, spawn_fn=None, env=None):
    """One pass of the lane. NEVER raises - it runs inside the rescue loop that also watches whether the
    console can still answer its own port. -> the lane's status in the shared vocabulary."""
    try:
        return _tick(now_s, busy, tree, census, path, spawn_fn, env)
    except Exception as e:
        return {"on": enabled(env), "worked": None, "lastTs": None, "owed": None, "key": "raised",
                "say": "the self-prove tick raised %s - nothing was started" % type(e).__name__}


def _int(v):
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


def _tick(now_s, busy, tree, census, path, spawn_fn, env):
    now_s = time.time() if now_s is None else now_s
    mem = load(path)
    if mem.get("unreadable"):
        return {"on": enabled(env), "worked": None, "lastTs": None, "owed": None, "key": "store-unreadable",
                "say": "the self-prove lane's memory would not read (%s) - UNKNOWN" % mem["unreadable"]}
    census = census_state() if census is None else census
    if not isinstance(census, dict):
        census = {"state": "unknown", "why": "the census reading was not a record"}
    pid = mem.get("pid")
    if not pid and _STARTED["pid"] and pid_alive(_STARTED["pid"]):
        pid = _STARTED["pid"]                              # the store lost it; this process did not
    running = pid if (pid and pid_alive(pid)) else None
    if pid and not running:
        # the proof we started has ended: did it leave a current census?
        if census.get("state") == "current":
            mem.update(worked=_int(mem.get("worked")) + 1, lastTs=int(now_s * 1000),
                       lastOk=census.get("why"))
        elif mem.get("startedFor") and census.get("fingerprint") != mem.get("startedFor"):
            # the console UPDATED while it proved: the proof spoke for the old gates. Not a failure -
            # the new gates are simply unproved, and are proved next, without the backoff.
            mem["lastMoved"] = "the gates changed during the proof (%s -> %s)" % (
                str(mem.get("startedFor"))[:8], str(census.get("fingerprint"))[:8])
        else:
            mem.update(lastFailAt=now_s, lastFailFingerprint=census.get("fingerprint"),
                       lastFailWhy="census still %s after the proof exited" % census.get("state"))
        mem.pop("pid", None)
        mem.pop("startedFor", None)
    on = enabled(env)
    d = decide(census, tree if tree is not None else tree_state(), running,
               busy() if callable(busy) else busy, mem, now_s, on=on)
    if d["start"]:
        try:
            log_path = _store_path(path) + ".log"
            mem["pid"] = (spawn_fn or spawn)(log_path)
            _STARTED["pid"] = mem["pid"]
            mem["startedFor"] = census.get("fingerprint")
            mem["startedAt"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_s))
            mem["runs"] = _int(mem.get("runs")) + 1
        except Exception as e:
            d = {"start": False, "key": "spawn-failed", "why": "the prover would not start (%s)" % type(e).__name__}
            mem.update(lastFailAt=now_s, lastFailFingerprint=census.get("fingerprint"), lastFailWhy=d["why"])
    mem.update(lastKey=d["key"], lastWhy=d["why"], lastTick=int(now_s * 1000))
    try:
        save(mem, path)
    except Exception:
        pass
    st = census.get("state")
    return {"on": on, "worked": _int(mem.get("worked")), "lastTs": mem.get("lastTs"),
            "owed": (0 if st == "current" else (None if st == "unknown" else 1)),
            "key": d["key"], "say": d["why"], "census": st, "blind": census.get("blind"),
            "running": bool(mem.get("pid"))}
