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

# ⚠⚠ REG-1502 — A PROOF NEVER RUNS BESIDE HIS GAME. MEASURED 2026-09-29 on the ALT (7.9 GB): a Windows inventory prove
# (the job this lane automates, started by hand) ran five hours beside his Boosteroid session while RAM sat at 690 MB
# free; dwm.exe died of memory exhaustion eight times in an hour and Boosteroid crashed with it. The CPU gate below
# could not see it: a CLOUD client decodes on the GPU and leaves the CPU nearly idle. So "he is playing" is its own
# question - the game itself OR a client streaming it - and so is free memory. Either one stops a proof from starting,
# and either one stands a RUNNING proof aside; a proof that stood aside is not a failure and runs again once he stops.
#: exe names (lowercased) that mean "he is playing on this PC" - the game, or a cloud client streaming it
PLAY_EXES = ("boosteroid.exe", "geforcenow.exe", "nvidia geforce now.exe")
#: available memory, in MB, a proof needs to START, and below which a RUNNING proof stands aside
MIN_FREE_MB_TO_START = 2048
MIN_FREE_MB_WHILE_RUNNING = 1024


def is_play_exe(name):
    """A process name (any case) that means he is playing here. Pure."""
    n = (name or "").lower()
    return n.startswith("d2r") or "diabloii" in n.replace(" ", "") or n in PLAY_EXES


def playing_state():
    """Is he playing on THIS machine - D2R.exe or a cloud client? -> True | False | None (UNKNOWN)"""
    try:
        if IS_WIN:
            import tv_diablo as _tvd
            return _tvd._toolhelp_any(is_play_exe)
        out = subprocess.run(["pgrep", "-if", "D2R.exe|Boosteroid|GeForceNOW"], capture_output=True, timeout=3)
        return True if out.returncode == 0 else (False if out.returncode == 1 else None)
    except Exception:
        return None


def free_mb():
    """Available physical memory in MB, or None when it cannot be measured (UNKNOWN, never 'plenty')."""
    try:
        if IS_WIN:
            import ctypes

            class _MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = _MS()
            m.dwLength = ctypes.sizeof(_MS)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
                return None
            return int(m.ullAvailPhys // (1024 * 1024))
        try:
            import psutil
            return int(psutil.virtual_memory().available // (1024 * 1024))
        except Exception:
            pass
        if hasattr(os, "sysconf") and "SC_AVPHYS_PAGES" in os.sysconf_names:
            return int(os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") // (1024 * 1024))
    except Exception:
        return None
    return None


def stand_aside(playing, free):
    """Must a RUNNING proof stop now? -> (bool, why). Pure. UNKNOWN never stops it: it already runs below him."""
    if playing is True:
        return True, "he started playing - a proof never runs beside his game"
    try:
        if free is not None and float(free) < MIN_FREE_MB_WHILE_RUNNING:
            return True, "only %d MB of memory left - the proof gives it back" % int(float(free))
    except (TypeError, ValueError):
        pass
    return False, ""


def end_tree(pid):
    """End a proof THIS lane started, with its children (the laws it runs). Never raises."""
    try:
        if IS_WIN:
            subprocess.run(["taskkill", "/PID", str(int(pid)), "/T", "/F"], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=15, creationflags=_CREATE_NO_WINDOW)
        else:
            import signal
            os.killpg(int(pid), signal.SIGTERM)      # spawn() gave the prover its own session
    except Exception:
        pass


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


def decide(census, tree, running_pid, busy_pct, mem, now_s, on=True, playing=None, free=None):
    """THE ONE DECISION. Pure. -> {"start": bool, "key": str, "why": str}
    `playing` / `free` (REG-1502): None is UNKNOWN, and a proof is never started on a guess."""
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
    if playing is None:
        return {"start": False, "key": "play-unknown",
                "why": "whether he is playing here could not be asked - a proof is not started on a guess"}
    if playing:
        return {"start": False, "key": "playing",
                "why": "he is playing on this PC (the game or its cloud client) - a proof never starts beside it"}
    try:
        free = None if free is None else float(free)
    except (TypeError, ValueError):
        free = None
    if free is None or free != free:
        return {"start": False, "key": "mem-unknown",
                "why": "free memory could not be measured - a proof is not started on a guess"}
    if free < MIN_FREE_MB_TO_START:
        return {"start": False, "key": "low-memory",
                "why": "only %d MB of memory free - a proof starts at %d MB" % (int(free), MIN_FREE_MB_TO_START)}
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


#: What the PROVER needs that a console does not: the browser laws drive Chrome over DevTools with
#: websocket-client. MEASURED on the ALT (#50, REG-1457): once render_check could find Chrome there, all 8
#: browser cases of test_mask_encoders_agree failed with "No module named 'websocket'" - the installer never
#: put it on a Windows PC, because only the pre-push gate on his Mac had ever proved anything.
PROVER_DEPS = (("websocket", "websocket-client"),)


def ensure_prover_deps(find=None, run=None):
    """Make the prover's imports present before a proof starts. -> {"ok", "installed", "why"}. Never raises.

    The same shape as the console's boot Pillow install (control_app): hidden, bounded, `--user`, and it
    SAYS what it did. Only on Windows - his Mac and CI already carry these - and only once per missing
    package per process."""
    import importlib.util as _ilu
    find = find or _ilu.find_spec
    out = {"ok": True, "installed": [], "why": "every prover import is present"}
    missing = []
    for mod, pkg in PROVER_DEPS:
        try:
            if find(mod) is None:
                missing.append(pkg)
        except Exception:
            missing.append(pkg)
    if not missing:
        return out
    if not IS_WIN:
        out.update(ok=False, why="missing %s - not installed automatically off Windows" % ", ".join(missing))
        return out
    exe = sys.executable or "python"
    if exe.lower().endswith("pythonw.exe"):
        exe = exe[:-len("pythonw.exe")] + "python.exe"
    try:
        r = (run or subprocess.run)([exe, "-m", "pip", "install", "--user", "--quiet"] + missing,
                                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                                    timeout=600, creationflags=_CREATE_NO_WINDOW if IS_WIN else 0)
        rc = getattr(r, "returncode", None)
    except Exception as e:
        out.update(ok=False, why="pip could not run (%s)" % type(e).__name__)
        return out
    if rc != 0:
        out.update(ok=False, why="pip exited %s installing %s" % (rc, ", ".join(missing)))
        return out
    out.update(installed=missing, why="installed %s for the prover" % ", ".join(missing))
    return out


def spawn(log_path, python=None, workers=1, popen=None):
    """Start `heart2.py --prove` hidden and below everything he does. -> pid"""
    py = python or sys.executable
    if IS_WIN and py.lower().endswith("pythonw.exe"):
        cand = py[:-len("pythonw.exe")] + "python.exe"   # pythonw has no stdout for the prover's log
        if os.path.exists(cand):
            py = cand
    # HEART2_DEADLINE_SCALE (REG-1454): this proof runs below everything he does, on whatever PC this is, so
    # every gate gets 4x its registered patience - measured on the ALT, a 120 s law timed out every time.
    env = dict(os.environ, HEART2_PROVE_WORKERS=str(int(workers)), PYTHONIOENCODING="utf-8",
               HEART2_DEADLINE_SCALE="4")
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


def tick(now_s=None, busy=None, tree=None, census=None, path=None, spawn_fn=None, env=None,
         playing=None, free=None, kill_fn=None):
    """One pass of the lane. NEVER raises - it runs inside the rescue loop that also watches whether the
    console can still answer its own port. -> the lane's status in the shared vocabulary.
    `playing` / `free` are callables or values (REG-1502); None asks this machine."""
    try:
        return _tick(now_s, busy, tree, census, path, spawn_fn, env, playing, free, kill_fn)
    except Exception as e:
        return {"on": enabled(env), "worked": None, "lastTs": None, "owed": None, "key": "raised",
                "say": "the self-prove tick raised %s - nothing was started" % type(e).__name__}


def _int(v):
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


def _ask(v, probe):
    try:
        return (v() if callable(v) else v) if v is not None else probe()
    except Exception:
        return None


def _tick(now_s, busy, tree, census, path, spawn_fn, env, playing=None, free=None, kill_fn=None):
    now_s = time.time() if now_s is None else now_s
    play_now = _ask(playing, playing_state)
    free_now = _ask(free, free_mb)
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
    aside, aside_why = stand_aside(play_now, free_now) if running else (False, "")
    if aside:
        # REG-1502 — stood aside, not failed: no backoff, no failure count; it proves again once he stops.
        (kill_fn or end_tree)(running)
        mem.update(stoodAside=_int(mem.get("stoodAside")) + 1, lastStoodAsideAt=int(now_s * 1000),
                   lastStoodAsideWhy=aside_why)
        mem.pop("pid", None)
        mem.pop("startedFor", None)
        _STARTED["pid"] = None
        pid = running = None
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
               busy() if callable(busy) else busy, mem, now_s, on=on, playing=play_now, free=free_now)
    if aside:
        d = {"start": False, "key": "stood-aside", "why": "the running proof stood aside: " + aside_why}
    if d["start"]:
        try:
            if spawn_fn is None:                           # a real start, not a law's recording spawn
                mem["deps"] = ensure_prover_deps()
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
            "running": bool(mem.get("pid")), "playing": play_now, "freeMb": free_now,
            "stoodAside": _int(mem.get("stoodAside"))}
