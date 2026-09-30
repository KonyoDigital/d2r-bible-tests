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
import re
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
#: ⚠ REG-1624 (2026-09-30) - 2048 was set for a proof BESIDE a stream. MEASURED on the ALT with the game off, the
#: console relaunched and nothing else running: 1,781 MB available - so the one PC this lane exists for could never
#: start a proof at all, and he had to close things by hand. A proof never starts while he plays (the question above
#: this one), and guard() now stands a RUNNING proof aside within one rescue tick (10 s) of the game starting or
#: memory falling under the running floor. So the start bar only has to leave the proof room above that floor.
MIN_FREE_MB_TO_START = 1536
MIN_FREE_MB_WHILE_RUNNING = 1024

# ⚠⚠ REG-1511 — THE REVIEW OF v3524 FOUND THE STAND-ASIDE COULD KILL A STRANGER, FLAP, AND NEVER LET THE ALT PROVE.
#   · a finished prover's pid stayed in `_STARTED`, and the store's pid outlived a restart; `pid_alive` asks only
#     "is SOME process there", so a REUSED pid read as the running proof and got `taskkill /T /F` the first time he
#     played. Now a pid is the prover only when its BIRTH (process creation time, recorded at spawn) matches.
#   · a proof its own memory pushed under the line was killed, restarted once RAM came back, killed again - every ten
#     minutes, the census never current. Now nothing starts for STAND_ASIDE_COOLDOWN_S after a stand-aside.
#   · Boosteroid sitting in his tray counted as "playing" forever, so the ALT - the PC this lane exists for - never
#     proved and the doctor called it healthy. Now a cloud client plays only above CLOUD_STREAM_MIN_MB private bytes.
#: after a proof stands aside, no new proof starts for this long (seconds) - whatever the reason was
STAND_ASIDE_COOLDOWN_S = 1800
#: #99 — ONE SLICE of a census: the owed gates, cheapest first, up to this many estimated seconds of proving (a gate's
#: registered cost x its red-proofs + 1, from gate_costs.json) and at most SLICE_MAX_GATES. A PC he plays on most of the
#: day never gave a whole census (~90 min on his Mac) one idle window, so it never wrote one and every lock stayed shut;
#: a slice fits an idle gap, and a stand-aside costs only the slice it ends.
SLICE_BUDGET_S = 600
SLICE_MAX_GATES = 40
#: a gate gate_costs.json has never timed is planned at this many seconds per run
SLICE_UNKNOWN_COST_S = 30.0
#: a proof whose census is ALREADY current for its gates is left to finish its cleanup this long (seconds) before a
#: stand-aside may end it; one console tick is 600 s, so it gets exactly one tick
FINISH_GRACE_S = 600
#: private bytes (MB) above which a cloud client counts as STREAMING. A live Boosteroid stream was measured at ~2 GB;
#: the client idling in the tray is a fraction of that. D2R.exe itself always counts.
CLOUD_STREAM_MIN_MB = 600
#: the clients whose streaming footprint HAS been measured, so the threshold may decide for them. GeForce NOW has not
#: been: whether its stream lives in GeForceNOW.exe or in a child process is unknown here, and a Boosteroid number is
#: not a measurement of it - so its name alone still counts, as before, until someone measures it.
MEMORY_GATED_EXES = ("boosteroid.exe",)
#: how long end_tree watches for the prover to be gone after it was told to end (seconds)
END_WAIT_S = 10.0


def _is_game_exe(n):
    return n.startswith("d2r") or "diabloii" in n.replace(" ", "")


def is_play_exe(name):
    """A process name (any case) that CAN mean he is playing here: the game, or a cloud client. Pure.
    Whether a cloud client is actually STREAMING is is_play_proc's question (REG-1511)."""
    n = (name or "").lower()
    return _is_game_exe(n) or n in PLAY_EXES


def is_play_proc(name, private_mb=None):
    """Does THIS process mean he is playing here? -> bool. Pure.

    REG-1511 — the game always counts. A measured cloud client (MEMORY_GATED_EXES) counts only while it streams: at
    CLOUD_STREAM_MIN_MB private bytes or more; any other cloud client still counts by name. `private_mb` None (its
    memory could not be read) counts as playing - the conservative answer, because a proof beside a live stream is
    what crashed dwm on the ALT, and a proof deferred is only a proof later."""
    n = (name or "").lower()
    if _is_game_exe(n):
        return True
    if n not in PLAY_EXES:
        return False
    if n not in MEMORY_GATED_EXES:
        return True
    try:
        mb = None if private_mb is None else float(private_mb)
    except (TypeError, ValueError):
        mb = None
    if mb is None or mb != mb:
        return True
    return mb >= CLOUD_STREAM_MIN_MB


def _play_proc_pred(name, pid):
    """The Toolhelp walk's question for one process. Its memory is read only for a cloud client's name."""
    return is_play_proc(name, proc_private_mb(pid) if (name or "").lower() in MEMORY_GATED_EXES else None)


#: what the POSIX `ps` listing is searched for - the same three names the Windows walk knows
_POSIX_PLAY = re.compile(r"D2R\.exe|Boosteroid|GeForceNOW", re.I)


def posix_play_line(line):
    """One `ps -Ao pid=,command=` line -> does it mean he is playing? Pure.

    REG-1511 — ⚠ NEVER A PYTHON PROCESS OR A .py FILE. MEASURED on his Mac: `pgrep -if` matched the prover's OWN law,
    `python .../tv/test_a_bare_boosteroid_window_must_show_the_hud.py`, so while heart2 ran it the lane read
    "playing" and stood its own proof aside - at the same offset on every restart, so the proof never finished."""
    parts = (line or "").split()
    if len(parts) < 2:
        return False
    argv = parts[1:]
    if not _POSIX_PLAY.search(" ".join(argv)):
        return False
    exe = os.path.basename(argv[0]).lower()
    if exe.startswith("python") or any(a.lower().endswith(".py") for a in argv):
        return False
    return True


def playing_state():
    """Is he playing on THIS machine - D2R.exe or a cloud client streaming it? -> True | False | None (UNKNOWN)"""
    try:
        if IS_WIN:
            import tv_diablo as _tvd
            return _tvd._toolhelp_any(_play_proc_pred, with_pid=True)
        out = subprocess.run(["ps", "-Ao", "pid=,command="], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3)
        lines = [ln for ln in (out.stdout or "").splitlines() if ln.strip()]
        if out.returncode != 0 or not lines:
            return None                        # no listing is not "nobody is playing" [[zero-needs-a-denominator]]
        return any(posix_play_line(ln) for ln in lines)
    except Exception:
        return None


_K32 = {}


def _k32():
    """Windows: a PRIVATE kernel32 with the handle prototypes set. Private because setting restype/argtypes on
    `ctypes.windll.kernel32` would change them for every other caller in the console process."""
    k = _K32.get("k")
    if k is None:
        import ctypes
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = wintypes.HANDLE
        k.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        k.CloseHandle.argtypes = (wintypes.HANDLE,)
        k.GetProcessTimes.restype = wintypes.BOOL
        k.GetProcessTimes.argtypes = (wintypes.HANDLE,) + (ctypes.POINTER(wintypes.FILETIME),) * 4
        try:
            k.K32GetProcessMemoryInfo.restype = wintypes.BOOL
            k.K32GetProcessMemoryInfo.argtypes = (wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD)
        except AttributeError:
            pass                                  # an older kernel32: proc_private_mb asks psapi instead
        _K32["k"] = k
    return k


def proc_birth(pid):
    """When was process `pid` created? -> an opaque string that is equal only for the SAME process, or None when it
    cannot be told (dead, a zombie, refused, no tool). Never raises.

    REG-1511 — a pid is a number the system hands out again; its creation time is not. Windows: OpenProcess +
    GetProcessTimes (100 ns ticks). POSIX: `ps -o stat=,lstart=` in UTC and the C locale, so a console restarted
    under another locale or zone reads the same string for the same process."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return None
    if pid <= 0:
        return None
    try:
        if IS_WIN:
            import ctypes
            from ctypes import wintypes
            k = _k32()
            h = k.OpenProcess(0x1000, False, pid)       # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return None
            try:
                ft = [wintypes.FILETIME() for _ in range(4)]
                if not k.GetProcessTimes(h, *[ctypes.byref(f) for f in ft]):
                    return None
                v = (int(ft[0].dwHighDateTime) << 32) | int(ft[0].dwLowDateTime)
                return ("ft:%d" % v) if v else None
            finally:
                k.CloseHandle(h)
        r = subprocess.run(["ps", "-o", "stat=,lstart=", "-p", str(pid)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=3, env=dict(os.environ, LC_ALL="C", TZ="UTC"))
        parts = (r.stdout or "").split()
        if r.returncode != 0 or len(parts) < 2 or parts[0].upper().startswith("Z"):
            return None                         # gone, or a zombie: an exited prover is not a running one
        return "ps:" + " ".join(parts[1:])
    except Exception:
        return None


def proc_private_mb(pid):
    """Windows: the private bytes of process `pid`, in MB, or None when they cannot be read. Never raises.
    OpenProcess(QUERY_LIMITED | VM_READ) + K32GetProcessMemoryInfo (psapi's GetProcessMemoryInfo on an older
    kernel32), PROCESS_MEMORY_COUNTERS_EX.PrivateUsage - the number Task Manager calls the commit size."""
    if not IS_WIN:
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class _PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                        ("PrivateUsage", ctypes.c_size_t)]
        k = _k32()
        h = k.OpenProcess(0x1000 | 0x0010, False, int(pid))   # QUERY_LIMITED_INFORMATION | VM_READ, as documented
        if not h:
            h = k.OpenProcess(0x1000, False, int(pid))         # an elevated client refuses VM_READ; Windows 8.1+
        if not h:                                               # answers with QUERY_LIMITED alone
            return None
        try:
            c = _PMC()
            c.cb = ctypes.sizeof(_PMC)
            fn = getattr(k, "K32GetProcessMemoryInfo", None)
            if fn is None:
                fn = ctypes.WinDLL("psapi").GetProcessMemoryInfo
                fn.restype = wintypes.BOOL
                fn.argtypes = (wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD)
            if not fn(h, ctypes.byref(c), c.cb):
                return None
            return int(c.PrivateUsage // (1024 * 1024))
        finally:
            k.CloseHandle(h)
    except Exception:
        return None


def vm_stat_free_mb(text):
    """macOS `vm_stat` output -> available MB (free + inactive pages, the sum psutil calls available), or None. Pure."""
    t = text or ""
    ps = re.search(r"page size of (\d+) bytes", t)
    got = {}
    for label in ("Pages free", "Pages inactive"):
        m = re.search(r"^%s:\s+(\d+)\." % re.escape(label), t, re.M)
        got[label] = int(m.group(1)) if m else None
    if not ps or None in got.values():
        return None
    return int((got["Pages free"] + got["Pages inactive"]) * int(ps.group(1)) // (1024 * 1024))


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
        # REG-1511 — MEASURED on his Mac: no psutil, and Darwin has no SC_AVPHYS_PAGES, so this answered None on
        # every tick and an installed Mac could never start a proof ('mem-unknown' forever). vm_stat is always there.
        if sys.platform == "darwin":
            r = subprocess.run(["vm_stat"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3)
            v = vm_stat_free_mb(r.stdout) if r.returncode == 0 else None
            if v is not None:
                return v
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


def is_ours(pid, birth):
    """Is `pid` alive AND the very process this lane started - the same BIRTH recorded at spawn? -> bool. Never raises.

    REG-1511 — `pid_alive` alone answers "is SOME process there". A pid is handed out again once its process ends
    (Windows reuses them quickly), so a stored pid that outlived its prover named whatever came next. No recorded
    birth (a store from before this fix, or a spawn whose birth could not be read) is NOT ours: an identity that
    cannot be checked is never trusted with a kill."""
    try:
        if birth is None or not pid_alive(pid):
            return False
        return proc_birth(pid) == birth
    except Exception:
        return False


def end_tree(pid, birth=None, wait_s=None):
    """End a proof THIS lane started, with its children (the laws it runs). Never raises.
    -> True when our prover is gone afterwards, False when it SURVIVED the kill.

    REG-1511 — ⚠⚠ ONLY A PID WHOSE BIRTH MATCHES IS EVER SIGNALLED. `taskkill /T /F` on a reused pid force-kills a
    stranger and everything under it (after a reboot the stale store pid can be explorer.exe). And a kill that did
    not take is reported, never assumed: taskkill can time out on a machine paging hard (the 690 MB-free afternoon),
    and a prover that survived must stay tracked, or the lane starts a second one beside it."""
    try:
        if not is_ours(pid, birth):
            return True                   # nothing of ours is there: nothing is signalled, nothing is left running
        if IS_WIN:
            subprocess.run(["taskkill", "/PID", str(int(pid)), "/T", "/F"], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=15, creationflags=_CREATE_NO_WINDOW)
        else:
            import signal
            try:
                os.killpg(int(pid), signal.SIGTERM)  # spawn() gave the prover its own session
            except ProcessLookupError:
                os.kill(int(pid), signal.SIGTERM)    # its birth matched, so this pid IS the prover; no group to end
    except Exception:
        pass
    deadline = time.time() + (END_WAIT_S if wait_s is None else float(wait_s))
    while is_ours(pid, birth):
        if time.time() >= deadline:
            return False                  # it SURVIVED: the caller keeps it, and asks again next tick
        time.sleep(0.2)
    return True


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


def _owed_of(h2, st):
    """#99 — the gates this census owes a proof, for the slice planner. -> {"owed", "owedGates", "owedWhy"} or {} when
    it cannot be asked (then the lane proves the whole census in one run, exactly as before - never a guess)."""
    try:
        so = h2.slice_owed(state=st)
    except Exception:
        return {}
    owed = [(str(n), int(k)) for n, k in (so.get("owed") or [])]
    return {"owed": len(owed), "owedGates": owed,
            "owedWhy": "%s; %d owed - proved a slice at a time while this PC is idle" % (so.get("why"), len(owed))}


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
        return dict({"state": "missing", "why": "this PC has never proved its instruments", "fingerprint": fp},
                    **_owed_of(_h2, {}))
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
        out.update(_owed_of(_h2, st))
    else:
        out.update(state="current", why="proved for the gates on disk: %s of %s, %d blind"
                                        % (st.get("proved"), st.get("declared"), len(out["blind"])))
    return out


def _git(*args, timeout=15):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    r = subprocess.run(["git"] + list(args), cwd=REPO, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout, env=env)
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
        against = ""
        if rc != 0 or not counts:
            # REG-1626 - A CHECKOUT WITH NO TRACKING BRANCH IS STILL COMPARED WITH ORIGIN. MEASURED 2026-09-30 in the
            # fleet: GrokBot's box said pull "level with origin" (fleet_origin_status compares HEAD with origin/main)
            # while this said tree-unknown and never proved - the same tree judged by two refs. Asked the fleet's ref.
            rc, counts = g("rev-list", "--left-right", "--count", "origin/main...HEAD")
            against = " (no tracking branch - compared with origin/main, as the fleet does)"
            if rc != 0 or not counts:
                return "unknown", "this checkout has no upstream and no origin/main to compare with"
        behind, ahead = [int(x) for x in counts.split()[:2]]
        if ahead:
            return "dev", "%d local commit(s) not yet on origin - the pre-push gate proves them%s" % (ahead, against)
        if behind:
            return "installed", "an installed console %d commit(s) behind origin%s" % (behind, against)
        return "installed", "an installed console, level with origin%s" % against
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
    # REG-1511 — A STAND-ASIDE HOLDS THE NEXT START. Simulated in the review of v3524: free RAM 2500 MB idle and 900 MB
    # with the proof running gave start, stood-aside, start, stood-aside... every 600 s tick - each run rebuilt its
    # sandbox and threw the work away, the census never went current, and the doctor called both keys healthy.
    try:
        last_aside = (float(mem.get("lastStoodAsideAt")) / 1000.0
                      if mem.get("lastStoodAsideAt") is not None else None)
    except (TypeError, ValueError):
        # the skeptic on fix24-selfprove: now_s here re-armed the cooldown on EVERY tick, so a corrupt value held the
        # lane shut for ever while the doctor called it healthy. Unreadable = no cooldown; the playing and memory
        # gates above still stand between a proof and his game.
        last_aside = None
    if last_aside is not None and now_s - last_aside < STAND_ASIDE_COOLDOWN_S:
        return {"start": False, "key": "aside-cooldown",
                "why": "a proof stood aside %d min ago (%s) - the next one waits %d min, so a proof that cannot "
                       "finish here does not start and die every tick"
                       % (int(max(0.0, now_s - last_aside) // 60), mem.get("lastStoodAsideWhy") or "?",
                          STAND_ASIDE_COOLDOWN_S // 60)}
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


def _gate_costs(path=None):
    """gate name -> measured seconds per run, from gate_costs.json. None when it cannot be read - UNKNOWN, not "no gate
    costs anything": every gate then plans at SLICE_UNKNOWN_COST_S and the slice's why says its sizes are a guess."""
    try:
        with io.open(path or os.path.join(HERE, "gate_costs.json"), encoding="utf-8") as fh:
            c = json.load(fh).get("costs")
        return c if isinstance(c, dict) else None
    except Exception:
        return None


def plan_slice(owed, costs=None, budget_s=None, max_gates=None):
    """#99 — ONE SLICE of the owed gates. Pure. -> [names]

    `owed` is [(name, n_proofs)]. Cheapest first (a gate's cost x (n_proofs + 1): one clean run and one per tamper), up
    to `budget_s` and `max_gates`, and never empty while anything is owed - a gate costlier than the whole budget is a
    slice of its own rather than a gate no slice ever takes."""
    costs = costs if costs is not None else {}
    budget = SLICE_BUDGET_S if budget_s is None else budget_s
    cap = SLICE_MAX_GATES if max_gates is None else max_gates

    def est(item):
        n, k = item
        try:
            c = float(costs.get(n))
        except (TypeError, ValueError):
            c = SLICE_UNKNOWN_COST_S
        if not (c == c) or c < 0:
            c = SLICE_UNKNOWN_COST_S
        return c * (max(0, int(k)) + 1)
    out, spent = [], 0.0
    for item in sorted(owed or [], key=lambda t: (est(t), t[0])):
        e = est(item)
        if out and (spent + e > budget or len(out) >= cap):
            break
        out.append(item[0])
        spent += e
    return out


def _slice_landed(census, names):
    """#99 — how many of a slice's gates the census no longer owes. -> int | None (None: the census cannot say)"""
    if not names:
        return None
    if (census or {}).get("state") == "current":
        return len(names)
    owed = (census or {}).get("owedGates")
    if not isinstance(owed, list):
        return None
    still = {str(t[0]) for t in owed if isinstance(t, (list, tuple)) and t}
    return sum(1 for n in names if n not in still)


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


def spawn(log_path, python=None, workers=1, popen=None, names=None):
    """Start `heart2.py --prove` hidden and below everything he does. -> pid
    #99 — `names`: prove just these gates as ONE SLICE (`--prove NAMES --slice`); None proves the whole census."""
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
    cmd = [py, os.path.join(HERE, "heart2.py"), "--prove"] + ((list(names) + ["--slice"]) if names else [])
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
#: REG-1511 — it carries the prover's BIRTH too, and is emptied the moment that proof ends (see _forget): a finished
#: prover's pid held here for the console's whole life was the pid a later stand-aside killed.
_STARTED = {"pid": None, "birth": None}


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


def guard(now_s=None, path=None, playing=None, free=None, kill_fn=None, _tick=None, busy=None):
    """REG-1624 — THE FAST STAND-ASIDE. -> None (no proof running, or nothing to do) | the tick's status

    His words, 2026-09-30: "the shadow reader is always on when the game is on regardless of the console" - "everything
    should work smoothly regardless of each other". The lane's tick runs every 10 minutes, so a proof could run beside
    his game for up to ten of them. This is asked on every rescue tick (10 s) WHILE a proof this lane started is
    running, and asks only the two cheap questions - is he playing, how much memory is left. When stand_aside() says
    go, it runs the whole tick at once, which kills the prover, books the stand-aside and starts the cooldown exactly
    as it always has: one door for the kill. Never raises."""
    try:
        mem = load(path)
        pid = mem.get("pid") or _STARTED.get("pid")
        if not pid:
            return None
        # REG-1625 - CONSECUTIVE, NOT ONE A TICK. MEASURED on the ALT 2026-09-30: its first slice (40 gates) took about a
        # minute, then the lane waited out the rest of its 10-minute tick - 663 owed gates would have needed ~3 hours of
        # game-off time. A slice that has ENDED is booked now, and the tick starts the next one if the PC is still idle
        # (every start rule still applies: not playing, the memory bar, cooldowns, backoff).
        # REG-1628 - AND IT IS HANDED THE LOAD PROBE THE LANE'S OWN TICK USES. MEASURED on the ALT on v3534: slices still
        # started only on the 10-minute tick (23:13:24, then 23:23:32). This call booked the ended slice and then decide()
        # met busy=None - "load-unknown", never started on a guess - so the next slice waited for the tick after all.
        if not pid_alive(pid):
            return (_tick or tick)(now_s=now_s, path=path, kill_fn=kill_fn, busy=busy)
        play_now = _ask(playing, playing_state)
        free_now = _ask(free, free_mb)
        aside, _why = stand_aside(play_now, free_now)
        if not aside:
            return None
        return (_tick or tick)(now_s=now_s, path=path, playing=play_now, free=free_now, kill_fn=kill_fn)
    except Exception as e:
        return {"on": None, "worked": None, "lastTs": None, "owed": None, "key": "raised",
                "say": "the self-prove guard raised %s - the tick will ask again" % type(e).__name__}


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


def _forget(mem):
    """The proof this lane was tracking is over (ended, or stood aside and gone): drop every trace of it."""
    for k in ("pid", "pidBirth", "startedFor", "finishingSince", "standingAside", "sliceGates"):
        mem.pop(k, None)
    _STARTED.update(pid=None, birth=None)


def _tick(now_s, busy, tree, census, path, spawn_fn, env, playing=None, free=None, kill_fn=None):
    now_s = time.time() if now_s is None else now_s
    now_ms = int(now_s * 1000)
    play_now = _ask(playing, playing_state)
    free_now = _ask(free, free_mb)
    mem = load(path)
    if mem.get("unreadable"):
        return {"on": enabled(env), "worked": None, "lastTs": None, "owed": None, "key": "store-unreadable",
                "say": "the self-prove lane's memory would not read (%s) - UNKNOWN" % mem["unreadable"]}
    census = census_state() if census is None else census
    if not isinstance(census, dict):
        census = {"state": "unknown", "why": "the census reading was not a record"}
    pid, birth = mem.get("pid"), mem.get("pidBirth")
    if not pid and _STARTED["pid"]:
        if is_ours(_STARTED["pid"], _STARTED.get("birth")):
            pid, birth = _STARTED["pid"], _STARTED.get("birth")   # the store lost it; this process did not
        else:
            _STARTED.update(pid=None, birth=None)          # it ended (or its pid moved on) while the store had lost it
    running = pid if (pid and is_ours(pid, birth)) else None
    # the skeptic on fix24-selfprove: a store from before REG-1511 (or a spawn whose birth could not be read) holds a
    # LIVE pid with no birth. is_ours() rightly refuses to trust it with a kill, but the tick then booked it as ENDED -
    # a failure and a 3 h backoff, the pid forgotten, and a second prover could start beside the first. UNVERIFIED:
    # left alone, not booked, and no new proof until that pid is gone.
    unverified = bool(pid) and not running and birth is None and pid_alive(pid)
    # REG-1511 — A PROOF WHOSE CENSUS IS ALREADY CURRENT FOR ITS GATES HAS DONE ITS WORK; it is only cleaning up
    # (heart2 removes its sandbox after the write). Booked as worked NOW, once, and left to finish for one tick: a
    # kill there cost the booking, and one landing inside heart2's plain census write left it truncated for good.
    finishing = bool(running) and census.get("state") == "current" and mem.get("startedFor") is not None \
        and census.get("fingerprint") == mem.get("startedFor")
    if finishing and not mem.get("finishingSince"):
        mem.update(worked=_int(mem.get("worked")) + 1, lastTs=now_ms, lastOk=census.get("why"),
                   finishingSince=now_ms)
    aside, aside_why = stand_aside(play_now, free_now) if running else (False, "")
    if aside and finishing and now_ms - _int(mem.get("finishingSince")) < FINISH_GRACE_S * 1000:
        aside, aside_why = False, ""                       # finishing - still running a tick later is a hang
    gone = None
    if aside:
        # REG-1502 — stood aside, not failed: no failure count, no 3 h backoff; REG-1511 — a cooldown, and a kill
        # that did not take keeps the prover tracked instead of forgetting a process that is still running.
        gone = bool((kill_fn or end_tree)(running, birth))
        if gone:
            mem.update(stoodAside=_int(mem.get("stoodAside")) + 1, lastStoodAsideAt=now_ms,
                       lastStoodAsideWhy=aside_why)
            _forget(mem)
            pid = running = None
        else:
            mem.update(asideSurvived=_int(mem.get("asideSurvived")) + 1, lastAsideSurvivedAt=now_ms,
                       standingAside=aside_why, pid=running, pidBirth=birth)
    if pid and not running and not unverified:
        # the proof we started has ended (or its pid now names another process): did it leave a current census?
        if mem.get("finishingSince"):
            pass                                           # booked as worked the tick its census went current
        elif census.get("state") == "current":
            mem.update(worked=_int(mem.get("worked")) + 1, lastTs=now_ms, lastOk=census.get("why"))
        elif mem.get("standingAside"):
            # told to stand aside, survived that tick, ended since: a stand-aside, never a failure
            mem.update(stoodAside=_int(mem.get("stoodAside")) + 1, lastStoodAsideAt=now_ms,
                       lastStoodAsideWhy=mem.get("standingAside"))
        elif mem.get("sliceGates") and (_slice_landed(census, mem.get("sliceGates")) or 0) > 0:
            # #99 — a SLICE that proved its gates is progress, not a failure: the census is still owed the rest, and
            # the next slice starts on a later tick. (A slice that landed NONE falls through to the failure below.)
            _got = _slice_landed(census, mem.get("sliceGates"))
            mem.update(worked=_int(mem.get("worked")) + 1, lastTs=now_ms, slices=_int(mem.get("slices")) + 1,
                       lastOk="a slice proved %d of its %d gate(s); %s still owed"
                              % (_got, len(mem.get("sliceGates") or []), census.get("owed")))
        elif mem.get("startedFor") and census.get("fingerprint") != mem.get("startedFor"):
            # the console UPDATED while it proved: the proof spoke for the old gates. Not a failure -
            # the new gates are simply unproved, and are proved next, without the backoff.
            mem["lastMoved"] = "the gates changed during the proof (%s -> %s)" % (
                str(mem.get("startedFor"))[:8], str(census.get("fingerprint"))[:8])
        else:
            mem.update(lastFailAt=now_s, lastFailFingerprint=census.get("fingerprint"),
                       lastFailWhy="census still %s after the proof exited" % census.get("state"))
        _forget(mem)
    on = enabled(env)
    d = decide(census, tree if tree is not None else tree_state(), running,
               busy() if callable(busy) else busy, mem, now_s, on=on, playing=play_now, free=free_now)
    if gone is True:
        d = {"start": False, "key": "stood-aside", "why": "the running proof stood aside: " + aside_why}
    elif gone is False:
        d = {"start": False, "key": "aside-survived",
             "why": "the running proof was told to stand aside (%s) but pid %s is still alive - it stays tracked, "
                    "is asked to end again next tick, and nothing new starts beside it" % (aside_why, running)}
    elif finishing and d["key"] == "running":
        d = dict(d, why="the proof made the census current (booked as worked) and is finishing its cleanup "
                        "(pid %s)" % running)
    if unverified:
        d = {"start": False, "key": "running-unverified",
             "why": "proof pid %s is alive but its start time was never recorded (a store from before REG-1511) - it "
                    "is left to finish, never killed, and no second proof starts beside it" % pid}
    if d["start"]:
        try:
            if spawn_fn is None:                           # a real start, not a law's recording spawn
                mem["deps"] = ensure_prover_deps()
            log_path = _store_path(path) + ".log"
            _owed_g = census.get("owedGates")
            _costs = _gate_costs() if isinstance(_owed_g, list) and _owed_g else None
            _slice = plan_slice(_owed_g, _costs) if isinstance(_owed_g, list) and _owed_g else None
            if _slice:
                mem["pid"] = (spawn_fn or spawn)(log_path, names=_slice)
                mem["sliceGates"] = _slice
                d = dict(d, why="%s - this slice: %d gate(s)%s" % (
                    census.get("owedWhy") or d["why"], len(_slice),
                    "" if _costs is not None else " (gate costs unread - sized by the default guess)"))
            else:
                mem["pid"] = (spawn_fn or spawn)(log_path)
            mem["pidBirth"] = proc_birth(mem["pid"])       # REG-1511 — who it is, not just its number
            _STARTED.update(pid=mem["pid"], birth=mem["pidBirth"])
            mem["startedFor"] = census.get("fingerprint")
            mem["startedAt"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_s))
            mem["runs"] = _int(mem.get("runs")) + 1
        except Exception as e:
            d = {"start": False, "key": "spawn-failed", "why": "the prover would not start (%s)" % type(e).__name__}
            mem.update(lastFailAt=now_s, lastFailFingerprint=census.get("fingerprint"), lastFailWhy=d["why"])
    mem.update(lastKey=d["key"], lastWhy=d["why"], lastTick=now_ms)
    try:
        save(mem, path)
    except Exception:
        pass
    st = census.get("state")
    return {"on": on, "worked": _int(mem.get("worked")), "lastTs": mem.get("lastTs"),
            "owed": (0 if st == "current" else (None if st == "unknown" else
                     (census.get("owed") if isinstance(census.get("owed"), int) and census.get("owed") > 0 else 1))),
            "slices": _int(mem.get("slices")),
            "key": d["key"], "say": d["why"], "census": st, "blind": census.get("blind"),
            "running": bool(mem.get("pid")), "playing": play_now, "freeMb": free_now,
            "stoodAside": _int(mem.get("stoodAside")), "asideSurvived": _int(mem.get("asideSurvived"))}
