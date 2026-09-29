#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#83 (REG-1515) — THE CHILD SUPERVISOR: one door every long-lived child of this checkout goes through.

His words, 2026-09-29, after FIVE capture_win.ps1 leaked at once and dwm.exe died under them, taking Boosteroid:
*"have a logic coded for this so it bypasses it - architecture something smart to make the ascending of the reel
sessions smooth"*. REG-1502/1509 closed the capture's own races; this is the architecture under all of them.

WHAT A ROLE IS. A role is a NAME for one long-lived child this process keeps - "capture" (capture_win.ps1),
"vision-r0".."vision-rN" (the warm `claude -p` readers), "vision-stall" (the stall-drain reader), "ocr" (the fast
lane's worker). By construction a role holds AT MOST ONE process: `spawn(role, argv)` ends the role's previous
instance first, waits a bounded time for it to die, and only then starts the new one. That is the whole "ascending
of the reel sessions": the next session's capture cannot exist beside the last one's.

WHAT "ENDS" MEANS - THE WHOLE TREE, VERIFIED:
  · Windows: each role's process is put in a Job Object with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE (ctypes, no
    package). A grandchild (powershell's conhost, claude's node helpers) is born into the job and dies with it;
    TerminateJobObject ends the tree in one call, and if THIS process dies without ending anything the OS closes
    the handle and the tree goes with it. When the assignment fails (a launcher already holds us in a job on a
    Windows that cannot nest) the receipt says so and taskkill /T remains the fallback.
  · POSIX: start_new_session, so the child leads its own process group and killpg ends what it spawned.
  · A record carries role / pid / birth (process creation time) / parent. A pid is only ended when it is still
    OURS: our own unreaped Popen (the kernel holds that pid for us), or - for a record left by a previous life of
    this console - a live pid whose creation time matches the record within BIRTH_TOL_S. A pid the OS handed to a
    newer process is a stranger and is dropped, never killed. UNKNOWN birth decides nothing and kills nothing.

THE LEDGER. Every spawn/end writes this process's records to one JSON file per parent under LEDGER_DIR (a temp dir
keyed by this checkout, or TV_CHILD_GUARD_DIR). A console that starts after a crash reads the files of parents
that are gone and ends their children - verified by birth - so a dead console's capture is not filming his
desktop when the next one boots. The agent's workers live in the agent's own file, so the console's watchdog can
see them too.

THE WATCHDOG (`watchdog_tick`, the console's rescue loop): (1) ends the recorded children of dead parents;
(2) reads the process table for processes of KNOWN roles that carry this checkout's path and ends the UNRECORDED
ones whose parent is gone or is one of ours - an unrecorded child with a live stranger parent (another console's)
is counted and said, never ended. An unreadable table is UNKNOWN: nothing is ended and `owed` is None, never 0.

MEMORY. `free_ram_mb()` reads available RAM (GlobalMemoryStatusEx / MemAvailable / vm_stat) or None when it
cannot; `secondary_spawn_allowed()` refuses a secondary worker (the stall reader, OCR) while free RAM is under
RAM_FLOOR_MB. A warm `claude -p` measured ~400 MB on his PC; the default floor leaves room for two and dwm's own
headroom, the thing that actually died. UNKNOWN free RAM never refuses - a refusal on a guess is the fail-always
the doctor row would then never see. [[unknown-stays-unknown]] [[heart-first]] [[copy-drift]]
"""
from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time

IS_WIN = sys.platform == "win32"
HERE = os.path.dirname(os.path.abspath(__file__))

#: how long an ended tree is given to die before it counts as a survivor. The same ~3 s as CAP_KILL_SETTLE_S
#: (REG-1509): TerminateProcess/TerminateJobObject are asynchronous, and a capture blocked inside PrintWindow can
#: read alive microseconds after the call returned.
END_WAIT_S = 3.0
#: creation times are read with 1 s resolution (`ps -o lstart`), so two readings of ONE process can differ by a
#: second across a boundary. Anything past this is a different process wearing the pid.
BIRTH_TOL_S = 2
#: the memory floor under which no SECONDARY worker starts. A warm claude is ~400 MB (measured on his PC); two of
#: them plus dwm.exe's working set is what the low-virtual-memory events of 2026-09-29 were about.
RAM_FLOOR_MB = int(os.environ.get("TV_RAM_FLOOR_MB") or 1024)
#: free RAM is re-read at most this often - the stall-drain gate asks on every busy tick and vm_stat is a process.
RAM_CACHE_S = 5.0
#: Windows: JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE, and the information class SetInformationJobObject takes it under.
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JobObjectExtendedLimitInformation = 9
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
STILL_ACTIVE = 259

#: the roles this checkout knows. `signature` = substrings that must ALL appear in a command line (beside this
#: checkout's own path, which every row must carry) for the watchdog to call an UNRECORDED process this role.
#: `expect` = [lo, hi] live processes per FAMILY ("vision-r3" -> "vision"); the agent raises vision's hi to POOL_N.
ROLES = {
    "capture": {"expect": [0, 1], "signature": ("capture_win.ps1",),
                "say": "the Windows screen capture (capture_win.ps1)"},
    "vision": {"expect": [0, 1], "signature": ("--input-format", "stream-json", "--add-dir"),
               "say": "the warm claude reader(s) of the live pool"},
    "vision-stall": {"expect": [0, 1], "signature": (),
                     "say": "the stall-drain reader (released after each sweep)"},
    "ocr": {"expect": [0, 1], "signature": ("--worker",), "say": "the fast lane's OCR worker"},
}

LEDGER_DIR = os.environ.get("TV_CHILD_GUARD_DIR") or os.path.join(
    tempfile.gettempdir(), "tvd-child-guard-" + hashlib.sha1(HERE.encode("utf-8", "replace")).hexdigest()[:8])

_LOCK = threading.RLock()
_ROLE_LOCKS = {}
_LIVE = {}              # role -> record of the process this role holds NOW (proc, pid, birth, job, session...)
_EXPECT = {}            # family -> [lo, hi] overrides this process declared (expect())
_SELF_BIRTH = None      # this process's own creation time, read once

RECEIPT = {"on": True, "worked": None, "lastTs": None, "owed": None, "spawns": 0, "ends": 0, "survivors": 0,
           "reused": 0, "say": "no child has gone through the door yet"}
WATCHDOG = {"on": True, "worked": None, "lastTs": None, "owed": None, "ended": [], "kept": [], "failed": [],
            "strangers": [], "unknown": None, "say": "the watchdog has not ticked yet"}
RAM = {"lastFreeMb": None, "lastTs": None, "refused": 0, "unknown": 0, "floorMb": RAM_FLOOR_MB,
       "say": "free RAM not read yet"}


# ── platform edges: every OS call lives behind one small function a law can stub ─────────────────────────────

def _kernel32():
    """The Windows kernel32 module (ctypes). A seam: the laws hand in a fake on a Mac."""
    import ctypes
    return ctypes.windll.kernel32


def _alive_default(pid):
    """Is this pid alive? Windows: OpenProcess + GetExitCodeProcess (never tasklist - REG-1414, it hangs under D2R
    load). POSIX: kill 0 - a zombie reads alive here, which is why our OWN children are judged by poll()."""
    if pid is None:
        return False
    if IS_WIN:
        try:
            import ctypes
            k = _kernel32()
            h = k.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
            if not h:
                return False
            try:
                code = ctypes.c_uint32()
                if not k.GetExitCodeProcess(h, ctypes.byref(code)):
                    return False
                return int(code.value) == STILL_ACTIVE
            finally:
                k.CloseHandle(h)
        except Exception:
            return False
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def _birth_win(pid):
    """Process creation time, epoch seconds, from GetProcessTimes. None = could not be read."""
    try:
        import ctypes
        k = _kernel32()
        h = k.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if not h:
            return None
        try:
            c, e, kt, ut = (ctypes.c_uint64() for _ in range(4))
            if not k.GetProcessTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(kt), ctypes.byref(ut)):
                return None
            # FILETIME: 100 ns ticks since 1601-01-01; the epoch offset is 116444736000000000 ticks
            return int((int(c.value) - 116444736000000000) / 10000000)
        finally:
            k.CloseHandle(h)
    except Exception:
        return None


def _birth_darwin(pid):
    """macOS: sysctl KERN_PROC/KERN_PROC_PID through libc (ctypes, no subprocess). The kinfo_proc it fills starts
    with extern_proc, whose first member is the union holding `p_starttime` (a timeval): the first 8 bytes ARE
    tv_sec. Verified against `ps -o lstart` on his Mac before this shipped. A pid that does not exist fills 0
    bytes -> None. ⚠ NOT `ps`: subprocess.run builds Popen from the subprocess module's globals, and every console
    law stubs that Popen - a `ps` here was counted as a capture spawn (3 for 2 starts, measured 2026-09-29)."""
    try:
        import ctypes
        import ctypes.util
        libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
        mib = (ctypes.c_int * 4)(1, 14, 1, int(pid))          # CTL_KERN, KERN_PROC, KERN_PROC_PID, pid
        size = ctypes.c_size_t(0)
        if libc.sysctl(mib, 4, None, ctypes.byref(size), None, 0) != 0 or size.value < 16:
            return None
        buf = ctypes.create_string_buffer(size.value)
        if libc.sysctl(mib, 4, buf, ctypes.byref(size), None, 0) != 0 or size.value < 16:
            return None
        tv_sec = ctypes.c_int64.from_buffer_copy(buf.raw[:8]).value
        return int(tv_sec) if tv_sec > 0 else None
    except Exception:
        return None


def _birth_posix(pid):
    """Process creation time, epoch seconds. Linux: /proc/<pid>/stat starttime + btime (exact); macOS: sysctl (exact);
    elsewhere `ps -o lstart` (1 s resolution, local clock - both readings of one process go through the same reader,
    so a DST step between two LIVES of this console reads as 'not ours', which is the safe direction). None = UNKNOWN."""
    if sys.platform == "darwin":
        return _birth_darwin(pid)
    try:
        if os.path.isdir("/proc"):
            with open("/proc/%d/stat" % int(pid)) as fh:
                stat = fh.read()
            start_ticks = int(stat.rsplit(")", 1)[1].split()[19])
            btime = None
            with open("/proc/stat") as fh:
                for line in fh:
                    if line.startswith("btime "):
                        btime = int(line.split()[1])
            hz = os.sysconf("SC_CLK_TCK")
            if btime is not None and hz:
                return int(btime + start_ticks / float(hz))
    except Exception:
        pass
    try:
        out = subprocess.run(["ps", "-p", str(int(pid)), "-o", "lstart="], capture_output=True, text=True,
                             timeout=5).stdout.strip()
        if not out:
            return None
        return int(time.mktime(time.strptime(out, "%a %b %d %H:%M:%S %Y")))
    except Exception:
        return None


def _birth_default(pid):
    if pid is None:
        return None
    return _birth_win(pid) if IS_WIN else _birth_posix(pid)


def _kill_tree_default(rec):
    """End a record's whole tree with what the platform gives. Windows: the job if this process holds it, else
    taskkill /T /F. POSIX: the process group when the child leads one, then the pid itself. Never raises."""
    pid = rec.get("pid")
    if IS_WIN:
        job = rec.get("job")
        if job:
            try:
                k = _kernel32()
                k.TerminateJobObject(job, 1)
                k.CloseHandle(job)
                rec["job"] = None
                return "job"
            except Exception:
                pass
        try:
            subprocess.run(["taskkill", "/PID", str(int(pid)), "/T", "/F"], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=15)
        except Exception:
            pass
        return "taskkill"
    how = "kill"
    if rec.get("session"):
        try:
            os.killpg(int(pid), signal.SIGKILL)
            how = "killpg"
        except Exception:
            pass
    try:
        os.kill(int(pid), signal.SIGKILL)
    except Exception:
        pass
    return how


def _win_job_assign(proc):
    """Put a freshly spawned Windows child in its own Job Object with KILL_ON_JOB_CLOSE. -> (handle | None, why).
    ctypes only: the structures are laid out here so no package is needed on his PC. A failure is SAID and the
    record then falls back to taskkill /T - never silent, never fatal."""
    if not IS_WIN:
        return None, "no job: not Windows"
    handle = getattr(proc, "_handle", None)
    if not handle:
        return None, "no job: the spawner gave no process handle"
    try:
        import ctypes
        k = _kernel32()

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [(n, ctypes.c_uint64) for n in ("ReadOperationCount", "WriteOperationCount",
                                                      "OtherOperationCount", "ReadTransferCount",
                                                      "WriteTransferCount", "OtherTransferCount")]

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", ctypes.c_uint32), ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", ctypes.c_uint32),
                        ("Affinity", ctypes.c_size_t), ("PriorityClass", ctypes.c_uint32),
                        ("SchedulingClass", ctypes.c_uint32)]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION), ("IoInfo", IO_COUNTERS),
                        ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

        job = k.CreateJobObjectW(None, None)
        if not job:
            return None, "no job: CreateJobObjectW failed (%s)" % k.GetLastError()
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k.SetInformationJobObject(job, JobObjectExtendedLimitInformation, ctypes.byref(info),
                                         ctypes.sizeof(info)):
            err = k.GetLastError()
            k.CloseHandle(job)
            return None, "no job: SetInformationJobObject failed (%s)" % err
        if not k.AssignProcessToJobObject(job, int(handle)):
            err = k.GetLastError()
            k.CloseHandle(job)
            return None, "no job: AssignProcessToJobObject failed (%s) - a launcher's job holds us; taskkill /T is the fallback" % err
        return job, "job object with KILL_ON_JOB_CLOSE - the tree ends with the handle"
    except Exception as e:
        return None, "no job: %s" % type(e).__name__


def _platform_kwargs(kw):
    """POSIX: the child leads its own session unless the caller chose otherwise (the Mac agent must NOT - v779,
    the Screen Recording TCC chain - and it does not come through this door). Windows: untouched; win_quiet
    already adds CREATE_NO_WINDOW at the module's Popen."""
    kw = dict(kw)
    if not IS_WIN:
        kw.setdefault("start_new_session", True)
    return kw


# ── records and the ledger ───────────────────────────────────────────────────────────────────────────────────

def family_of(role):
    """'vision-r3' -> 'vision'; every other role is its own family."""
    role = str(role or "")
    head, sep, tail = role.rpartition("-r")
    if sep and tail.isdigit():
        return head
    return role


def expect(family, lo, hi):
    """Declare how many live processes a family may hold in THIS process (the agent: vision 0..POOL_N)."""
    with _LOCK:
        _EXPECT[str(family)] = [int(lo), int(hi)]
        _ledger_write()


def _expected(family):
    if family in _EXPECT:
        return list(_EXPECT[family])
    if family in ROLES:
        return list(ROLES[family]["expect"])
    return [0, 1]


def _role_lock(role):
    with _LOCK:
        lk = _ROLE_LOCKS.get(role)
        if lk is None:
            lk = _ROLE_LOCKS[role] = threading.RLock()
        return lk


def _self_birth(birth=None):
    global _SELF_BIRTH
    if _SELF_BIRTH is None:
        _SELF_BIRTH = (birth or _birth_default)(os.getpid())
    return _SELF_BIRTH


def _ledger_path():
    return os.path.join(LEDGER_DIR, "%d.json" % os.getpid())


def _public(rec):
    return {k: rec.get(k) for k in ("role", "pid", "birth", "parent", "parentBirth", "argv0", "ts", "session",
                                    "jobSay")}


def _ledger_write():
    """This process's records -> its own file, atomically. Never raises into a spawner: a ledger that could not be
    written is said on the receipt and the spawn still happens - his session matters more than the bookkeeping."""
    try:
        os.makedirs(LEDGER_DIR, exist_ok=True)
        body = {"parent": os.getpid(), "parentBirth": _self_birth(), "expect": dict(_EXPECT),
                "children": {r: _public(rec) for r, rec in _LIVE.items()},
                "ts": int(time.time() * 1000)}
        path = _ledger_path()
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(body, fh)
        os.replace(tmp, path)
        return True
    except Exception as e:
        RECEIPT["say"] = "the ledger could not be written (%s)" % type(e).__name__
        return False


def _ledger_read_others():
    """[(path, body)] of every OTHER parent's ledger file. A file that cannot be parsed is skipped, not deleted:
    it may be mid-write by a live process."""
    out = []
    try:
        names = sorted(os.listdir(LEDGER_DIR))
    except Exception:
        return out
    mine = os.path.basename(_ledger_path())
    for n in names:
        if not n.endswith(".json") or n == mine:
            continue
        p = os.path.join(LEDGER_DIR, n)
        try:
            with open(p, encoding="utf-8") as fh:
                body = json.load(fh)
            if isinstance(body, dict) and isinstance(body.get("children"), dict):
                out.append((p, body))
        except Exception:
            continue
    return out


def _same_birth(a, b):
    """Two creation-time readings of what should be one process. None on either side = UNKNOWN = not the same."""
    try:
        return a is not None and b is not None and abs(int(a) - int(b)) <= BIRTH_TOL_S
    except Exception:
        return False


def _is_ours(rec, alive, birth):
    """-> (bool, why). Our own unreaped Popen is ours while poll() says running - the kernel keeps that pid for us.
    Anything else must be alive AND born when the record says; a pid born at another time belongs to a newer
    process (Windows hands pids out again within minutes) and is never ours."""
    proc = rec.get("proc")
    if proc is not None:
        try:
            if proc.poll() is None:
                return True, "our own child, still running"
            return False, "our own child, already exited"
        except Exception:
            pass
    pid = rec.get("pid")
    try:
        if not alive(pid):
            return False, "pid %s is gone" % pid
    except Exception:
        return False, "pid %s could not be asked" % pid
    if rec.get("birth") is None:
        return False, "pid %s is alive but its recorded birth is UNKNOWN - never ended on a guess" % pid
    now_birth = birth(pid)
    if now_birth is None:
        return False, "pid %s is alive but its birth cannot be read now - never ended on a guess" % pid
    if _same_birth(rec.get("birth"), now_birth):
        return True, "pid %s alive, born when recorded" % pid
    return False, "pid %s was reused by a process born at %s (recorded %s) - not ours" % (pid, now_birth, rec.get("birth"))


def _gone_within(rec, alive, within_s, step_s=0.1):
    """Wait, bounded, for a record's process to leave. Our own Popen is wait()ed (that reaps it); a foreign pid is
    polled through alive(). -> True once gone. The first answer is taken at once."""
    proc = rec.get("proc")
    deadline = time.time() + max(0.0, float(within_s))
    while True:
        try:
            if proc is not None:
                if proc.poll() is not None:
                    return True
            elif not alive(rec.get("pid")):
                return True
        except Exception:
            return False
        if time.time() >= deadline:
            return False
        time.sleep(step_s)


def _reap_later(proc):
    """v2352's lesson, kept: a child that outlives its bounded wait still gets its wait() - on a daemon thread,
    so the caller keeps its bound and the kernel still gets the exit status (20 <defunct> after 20 h, measured)."""
    try:
        threading.Thread(target=(lambda pr: pr.wait()), args=(proc,), daemon=True, name="reap-child-guard").start()
    except Exception:
        pass


# ── the door ─────────────────────────────────────────────────────────────────────────────────────────────────

def end(role, kill=None, alive=None, birth=None, wait_s=None, proc=None):
    """End the process a role holds, whole tree, and forget it. -> receipt dict
    {role, pid, killedPid, how, ended (True | False survivor | None not waited), say}.

    `kill(pid)` overrides the platform tree kill for the pid step (control_app hands its own taskkill /T, which its
    laws stub); the job step always runs first on Windows. `proc` limits the end to that exact Popen: a worker
    whose record was already replaced by a newer spawn ends only its own. wait_s=0 returns at once (the caller has
    its own settle check); None = END_WAIT_S."""
    alive = alive or _alive_default
    birth = birth or _birth_default
    wait_s = END_WAIT_S if wait_s is None else float(wait_s)
    with _role_lock(role):
        rec = _LIVE.get(role)
        out = {"role": role, "pid": None, "killedPid": None, "how": None, "ended": None, "say": ""}
        if rec is None:
            out["say"] = "nothing recorded for %s" % role
            if proc is not None:
                _end_loose(proc, wait_s)        # a worker that never came through the door still dies by itself
                out.update(pid=getattr(proc, "pid", None), how="loose", say=out["say"] + " - the Popen handed in was ended by itself")
            return out
        if proc is not None and rec.get("proc") is not None and rec.get("proc") is not proc:
            out["say"] = "%s now holds a newer process; the one handed in is not the record's" % role
            _end_loose(proc, wait_s)
            return out
        out["pid"] = rec.get("pid")
        ours, why = _is_ours(rec, alive, birth)
        if not ours:
            if "reused" in why:
                RECEIPT["reused"] = int(RECEIPT.get("reused") or 0) + 1
            _drop(role, rec)
            out.update(how="none", ended=True, say=why)
            if rec.get("proc") is not None:
                _close_job(rec)
            return out
        how = _kill_tree_default(rec) if (IS_WIN and rec.get("job")) else None
        if kill is not None:
            try:
                kill(rec.get("pid"))
                how = (how + "+" if how else "") + "caller"
            except Exception as e:
                how = (how + "+" if how else "") + "caller-raised-%s" % type(e).__name__
        elif how is None:
            how = _kill_tree_default(rec)
        out["killedPid"] = rec.get("pid")
        out["how"] = how
        RECEIPT["ends"] = int(RECEIPT.get("ends") or 0) + 1
        if wait_s > 0:
            gone = _gone_within(rec, alive, wait_s)
            out["ended"] = bool(gone)
            if not gone:
                RECEIPT["survivors"] = int(RECEIPT.get("survivors") or 0) + 1
                if rec.get("proc") is not None:
                    _reap_later(rec["proc"])
            RECEIPT["worked"] = bool(gone)
        else:
            out["ended"] = None
        _close_job(rec)
        _drop(role, rec)
        out["say"] = "%s pid %s ended by %s%s" % (role, rec.get("pid"), how,
                                                 "" if out["ended"] is not False else " - OUTLIVED %.1f s" % wait_s)
        RECEIPT["lastTs"] = int(time.time() * 1000)
        RECEIPT["say"] = out["say"]
        _owed()
        return out


def _end_loose(proc, wait_s):
    """A Popen that is not (or no longer) the record's: killed by itself, never by pid arithmetic on a record."""
    try:
        if proc.poll() is None:
            proc.kill()
        try:
            proc.wait(timeout=max(0.0, wait_s))
        except Exception:
            _reap_later(proc)
    except Exception:
        pass


def _close_job(rec):
    if IS_WIN and rec.get("job"):
        try:
            _kernel32().CloseHandle(rec["job"])
        except Exception:
            pass
        rec["job"] = None


def _drop(role, rec):
    if _LIVE.get(role) is rec:
        _LIVE.pop(role, None)
    _ledger_write()


def _owed():
    """How many ended processes are still alive right now: the receipt's debt. None when nothing can be said."""
    try:
        RECEIPT["owed"] = int(RECEIPT.get("survivors") or 0) if RECEIPT.get("survivors") is not None else None
    except Exception:
        RECEIPT["owed"] = None


def spawn(role, argv, popen=None, kill=None, alive=None, birth=None, wait_s=None, **popen_kw):
    """THE ONE SPAWN DOOR. Ends the role's previous instance (whole tree, verified ours, bounded wait), then starts
    argv with the platform's tree containment and records it. -> the Popen (raises what Popen raises).

    `popen` defaults to subprocess.Popen looked up at call time, so a law's patch of the module's Popen and
    win_quiet's Windows install both apply. `kill`/`alive`/`birth` are the seams the previous instance's end uses."""
    alive = alive or _alive_default
    birth = birth or _birth_default
    with _role_lock(role):
        prev = end(role, kill=kill, alive=alive, birth=birth, wait_s=wait_s)
        kw = _platform_kwargs(popen_kw)
        proc = (popen or subprocess.Popen)(argv, **kw)
        job, job_say = _win_job_assign(proc)
        try:
            argv0 = os.path.basename(str(argv[0])) if argv else ""
        except Exception:
            argv0 = ""
        rec = {"role": role, "pid": getattr(proc, "pid", None), "birth": birth(getattr(proc, "pid", None)),
               "parent": os.getpid(), "parentBirth": _self_birth(birth), "argv0": argv0,
               "ts": int(time.time() * 1000), "session": bool(kw.get("start_new_session")) and not IS_WIN,
               "job": job, "jobSay": job_say, "proc": proc}
        _LIVE[role] = rec
        RECEIPT["spawns"] = int(RECEIPT.get("spawns") or 0) + 1
        RECEIPT["lastTs"] = rec["ts"]
        RECEIPT["say"] = "%s pid %s spawned (%s)%s" % (
            role, rec["pid"], job_say if IS_WIN else ("own session" if rec["session"] else "caller's session"),
            (" after ending pid %s" % prev["killedPid"]) if prev.get("killedPid") else "")
        _ledger_write()
        return proc


def record_of(role):
    """The public record a role holds now, or None."""
    rec = _LIVE.get(role)
    return _public(rec) if rec else None


# ── census, watchdog ─────────────────────────────────────────────────────────────────────────────────────────

def census(alive=None):
    """What every known family holds, in this process and in every live parent's ledger. -> dict
    families: {family: {expected, recorded, alive, ok, pids, say}}, roles: {...}, ok (False on any family over its
    ceiling, None when a count could not be taken), strangers/unrecorded from the watchdog's last look."""
    alive = alive or _alive_default
    roles, fams = {}, {}
    with _LOCK:
        mine = [(r, _public(rec), rec.get("proc")) for r, rec in _LIVE.items()]
        expect_all = dict(_EXPECT)
    rows = []
    for r, pub, proc in mine:
        a = None
        try:
            a = (proc.poll() is None) if proc is not None else bool(alive(pub.get("pid")))
        except Exception:
            a = None
        rows.append((r, pub, a, "this process"))
    for _p, body in _ledger_read_others():
        for fam, lohi in (body.get("expect") or {}).items():
            expect_all.setdefault(fam, lohi)
        for r, pub in (body.get("children") or {}).items():
            try:
                a = bool(alive(pub.get("pid")))
            except Exception:
                a = None
            rows.append((r, pub, a, "parent %s" % body.get("parent")))
    for r, pub, a, who in rows:
        key = r if who == "this process" else "%s@%s" % (r, pub.get("parent"))
        roles[key] = dict(pub, alive=a, owner=who)
        fam = family_of(r)
        f = fams.setdefault(fam, {"expected": expect_all.get(fam) or _expected(fam), "recorded": 0, "alive": 0,
                                  "unknown": 0, "pids": []})
        f["recorded"] += 1
        if a is True:
            f["alive"] += 1
            f["pids"].append(pub.get("pid"))
        elif a is None:
            f["unknown"] += 1
    for fam in ROLES:
        fams.setdefault(fam, {"expected": expect_all.get(fam) or _expected(fam), "recorded": 0, "alive": 0,
                              "unknown": 0, "pids": []})
    ok_all = True
    for fam, f in fams.items():
        lo, hi = f["expected"]
        if f["unknown"]:
            f["ok"] = None
            f["say"] = "%s: %d recorded, %d could not be asked" % (fam, f["recorded"], f["unknown"])
            ok_all = None if ok_all is not False else False
        elif f["alive"] > hi:
            f["ok"] = False
            f["say"] = "%s: %d alive, at most %d expected - pids %s" % (fam, f["alive"], hi, f["pids"])
            ok_all = False
        else:
            f["ok"] = True
            f["say"] = "%s: %d alive (expected %d..%d)" % (fam, f["alive"], lo, hi)
    return {"families": fams, "roles": roles, "ok": ok_all,
            "unrecorded": list(WATCHDOG.get("failed") or []) + list(WATCHDOG.get("strangers") or []),
            "watchdogSay": WATCHDOG.get("say")}


def _rows_posix():
    """[(pid, ppid, born_s | None, command)] of every process whose command line carries this checkout's path, or
    None = UNKNOWN. `ps -axo lstart` is five tokens; the command is the rest of the line."""
    try:
        out = subprocess.run(["ps", "-axo", "pid=,ppid=,lstart=,command="], capture_output=True, text=True,
                             timeout=15)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    rows = []
    for line in out.stdout.splitlines():
        parts = line.split(None, 7)
        if len(parts) < 8 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        cmd = parts[7]
        if HERE not in cmd:
            continue
        born = None
        try:
            born = int(time.mktime(time.strptime(" ".join(parts[2:7]), "%a %b %d %H:%M:%S %Y")))
        except Exception:
            born = None
        rows.append((int(parts[0]), int(parts[1]), born, cmd))
    return rows


def _rows_query_ps(here):
    """The PowerShell that lists this checkout's processes: '<pid>|<ppid>|<born s>|<command line>' per row. Its
    own -Command text carries the path, so `$_.ProcessId -ne $PID` leaves the query out (REG-1509's self-match)."""
    return ("$t = '%s'; Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine "
            "-and $_.CommandLine.IndexOf($t, [StringComparison]::OrdinalIgnoreCase) -ge 0 } | ForEach-Object { "
            "$b = 0; try { if ($_.CreationDate) { $b = ([DateTimeOffset]$_.CreationDate).ToUnixTimeSeconds() } } "
            "catch {}; '{0}|{1}|{2}|{3}' -f $_.ProcessId, $_.ParentProcessId, $b, $_.CommandLine }"
            % here.replace("'", "''"))


def _parse_rows_ps(text, self_pid=None):
    rows = []
    for line in (text or "").splitlines():
        parts = line.split("|", 3)
        if len(parts) != 4 or not parts[0].strip().isdigit() or not parts[1].strip().isdigit():
            continue
        pid = int(parts[0])
        if self_pid is not None and pid == int(self_pid):
            continue
        try:
            born = int(parts[2]) or None
        except Exception:
            born = None
        rows.append((pid, int(parts[1]), born, parts[3]))
    return rows


def _rows_win(timeout=30):
    try:
        proc = subprocess.Popen(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", _rows_query_ps(HERE)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, text=True,
                                encoding="utf-8", errors="replace")
    except Exception:
        return None
    try:
        out, _err = proc.communicate(timeout=timeout)
    except Exception:
        try:
            proc.kill()
            proc.communicate(timeout=5)
        except Exception:
            pass
        return None
    if proc.returncode != 0:
        return None
    return _parse_rows_ps(out, self_pid=proc.pid)


def _rows_default():
    return _rows_win() if IS_WIN else _rows_posix()


def role_of_command(cmd):
    """Which known role a command line belongs to, by its signature, or None. Pure."""
    cmd = str(cmd or "")
    for role, spec in ROLES.items():
        sig = spec.get("signature") or ()
        if sig and all(s in cmd for s in sig):
            return role
    return None


def classify_unrecorded(rows, recorded, our_pids, alive, birth):
    """PURE: rows [(pid, ppid, born_s, cmd)] -> (to_end [(pid, role, why)], kept [(pid, role, why)], strangers
    [(pid, role, ppid)]). `recorded` = {pid: birth} of every process a live ledger knows; `our_pids` = this process
    and every recorded child (a grandchild spawned outside the door is still ours to end).

    A row is ended only when its command is a KNOWN role, it is not recorded (or is recorded under another
    birth - a reused pid), and its parent is gone (dead, reparented to pid 1, or a pid whose holder was born after
    the child - REG-1509's rule) or one of ours. A live stranger parent keeps its child: another console's camera
    is not ours to end, and the census says it is there."""
    to_end, kept, strangers = [], [], []
    for row in rows or []:
        pid, ppid, born, cmd = row[0], row[1], (row[2] if len(row) > 2 else None), (row[3] if len(row) > 3 else "")
        role = role_of_command(cmd)
        if role is None:
            continue
        if pid in recorded and (recorded[pid] is None or born is None or _same_birth(recorded[pid], born)):
            kept.append((pid, role, "recorded"))
            continue
        if ppid in our_pids:
            to_end.append((pid, role, "unrecorded child of ours (parent %s)" % ppid))
            continue
        parent_gone = (not ppid) or ppid <= 1
        if not parent_gone:
            try:
                parent_gone = not alive(ppid)
            except Exception:
                parent_gone = False
        if not parent_gone and born is not None:
            pborn = None
            try:
                pborn = birth(ppid)
            except Exception:
                pborn = None
            if pborn is not None and pborn > born + BIRTH_TOL_S:
                parent_gone = True          # a parent born after its child is a stranger holding a reused pid
        if parent_gone:
            to_end.append((pid, role, "unrecorded orphan (parent %s gone)" % ppid))
        else:
            strangers.append((pid, role, ppid))
    return to_end, kept, strangers


def watchdog_tick(rows_fn=None, kill=None, alive=None, birth=None, now_ms=None, settle_s=None):
    """One pass of the rescue-loop watchdog. -> the WATCHDOG receipt (on/worked/lastTs/owed, never raises).
    (1) the ledgers of parents that are gone: each child verified by birth and ended, the file removed;
    (2) the process table: unrecorded processes of known roles, ended by classify_unrecorded's rule.
    `kill(pid)` ends a pid's tree (default taskkill /T | killpg+kill); rows_fn None = UNKNOWN table."""
    alive = alive or _alive_default
    birth = birth or _birth_default
    settle = END_WAIT_S if settle_s is None else float(settle_s)
    now = int(time.time() * 1000) if now_ms is None else int(now_ms)
    ended, failed, kept, strangers = [], [], [], []

    def _kill(pid, session):
        if kill is not None:
            return kill(pid)
        return _kill_tree_default({"pid": pid, "session": session, "job": None})

    try:
        recorded = {}
        our_pids = {os.getpid()}
        with _LOCK:
            for rec in _LIVE.values():
                recorded[rec.get("pid")] = rec.get("birth")
                our_pids.add(rec.get("pid"))
        for path, body in _ledger_read_others():
            parent, pborn = body.get("parent"), body.get("parentBirth")
            parent_alive = False
            try:
                parent_alive = bool(alive(parent)) and (pborn is None or _same_birth(pborn, birth(parent)))
            except Exception:
                parent_alive = False
            if parent_alive:
                for pub in (body.get("children") or {}).values():
                    recorded[pub.get("pid")] = pub.get("birth")
                continue
            left = 0
            for pub in (body.get("children") or {}).values():
                ours, why = _is_ours(dict(pub), alive, birth)
                if not ours:
                    kept.append((pub.get("pid"), pub.get("role"), why))
                    continue
                _kill(pub.get("pid"), bool(pub.get("session")))
                if _gone_within({"pid": pub.get("pid")}, alive, settle):
                    ended.append((pub.get("pid"), pub.get("role"), "child of dead parent %s" % parent))
                else:
                    failed.append((pub.get("pid"), pub.get("role"), "child of dead parent %s - would not end" % parent))
                    left += 1
            if not left:
                try:
                    os.remove(path)
                except Exception:
                    pass
        rows = (rows_fn or _rows_default)()
        unknown = rows is None
        if not unknown:
            to_end, kept2, strangers = classify_unrecorded(rows, recorded, our_pids, alive, birth)
            kept.extend(kept2)
            for pid, role, why in to_end:
                _kill(pid, True)
                if _gone_within({"pid": pid}, alive, settle):
                    ended.append((pid, role, why))
                else:
                    failed.append((pid, role, why + " - would not end"))
        WATCHDOG.update(on=True, worked=(not failed) if not unknown else None, lastTs=now,
                        owed=(len(failed) if not unknown else None), ended=ended, kept=kept, failed=failed,
                        strangers=strangers, unknown=unknown,
                        say=("UNKNOWN - the process table could not be asked; %d child(ren) of dead parents ended"
                             % len(ended)) if unknown else
                            ("%d ended, %d kept, %d would not end, %d stranger(s) - another parent's, left alone"
                             % (len(ended), len(kept), len(failed), len(strangers))))
    except Exception as e:
        WATCHDOG.update(on=True, worked=None, lastTs=now, owed=None, unknown=True,
                        say="the watchdog raised %s - nothing can be said about this pass" % type(e).__name__)
    return dict(WATCHDOG)


# ── memory ───────────────────────────────────────────────────────────────────────────────────────────────────

def _free_ram_mb_read():
    """Available RAM in MB, or None. Windows: GlobalMemoryStatusEx.ullAvailPhys. Linux: MemAvailable. macOS:
    vm_stat free + inactive + speculative pages (what the kernel would hand out without swapping)."""
    try:
        if IS_WIN:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_uint32), ("dwMemoryLoad", ctypes.c_uint32),
                            ("ullTotalPhys", ctypes.c_uint64), ("ullAvailPhys", ctypes.c_uint64),
                            ("ullTotalPageFile", ctypes.c_uint64), ("ullAvailPageFile", ctypes.c_uint64),
                            ("ullTotalVirtual", ctypes.c_uint64), ("ullAvailVirtual", ctypes.c_uint64),
                            ("ullAvailExtendedVirtual", ctypes.c_uint64)]
            st = MEMORYSTATUSEX()
            st.dwLength = ctypes.sizeof(st)
            if not _kernel32().GlobalMemoryStatusEx(ctypes.byref(st)):
                return None
            return int(int(st.ullAvailPhys) // (1024 * 1024))
        if os.path.isfile("/proc/meminfo"):
            with open("/proc/meminfo") as fh:
                for line in fh:
                    if line.startswith("MemAvailable:"):
                        return int(int(line.split()[1]) // 1024)
            return None
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
        return parse_vm_stat(out)
    except Exception:
        return None


def parse_vm_stat(text):
    """vm_stat's text -> available MB (free + inactive + speculative pages x page size), or None. Pure."""
    import re
    m = re.search(r"page size of (\d+) bytes", text or "")
    if not m:
        return None
    page = int(m.group(1))
    pages = 0
    seen = 0
    for key in ("Pages free", "Pages inactive", "Pages speculative"):
        mm = re.search(r"^%s:\s+(\d+)\." % re.escape(key), text, re.M)
        if mm:
            pages += int(mm.group(1))
            seen += 1
    if not seen:
        return None
    return int(pages * page // (1024 * 1024))


def free_ram_mb(now=None, read=None):
    """Available RAM in MB, cached RAM_CACHE_S, or None = UNKNOWN (never 0: 0 is a measurement)."""
    now = time.time() if now is None else float(now)
    last = RAM.get("lastTs")
    if last is not None and RAM.get("lastFreeMb") is not None and (now - float(last)) < RAM_CACHE_S:
        return RAM["lastFreeMb"]
    v = (read or _free_ram_mb_read)()
    RAM["lastTs"] = now
    RAM["lastFreeMb"] = v if isinstance(v, int) and not isinstance(v, bool) else None
    if RAM["lastFreeMb"] is None:
        RAM["unknown"] = int(RAM.get("unknown") or 0) + 1
    return RAM["lastFreeMb"]


_UNSET = object()


def secondary_spawn_allowed(free_mb=_UNSET, floor_mb=None):
    """May a SECONDARY worker (the stall reader, OCR) start now? -> (bool, why). Under the floor: no. UNKNOWN free
    RAM: yes, and said - a refusal on a guess would silence the fast lane and the stall drain for ever on any
    machine whose meter cannot be read, which is exactly the fail-always no doctor row would then see."""
    floor = RAM_FLOOR_MB if floor_mb is None else int(floor_mb)
    free = free_ram_mb() if free_mb is _UNSET else free_mb
    if free is None:
        RAM["say"] = "free RAM UNKNOWN - the %d MB floor cannot be judged; the spawn is not refused on a guess" % floor
        return True, RAM["say"]
    if int(free) < floor:
        RAM["refused"] = int(RAM.get("refused") or 0) + 1
        RAM["say"] = "free RAM %d MB is under the %d MB floor - no secondary worker until it recovers" % (int(free), floor)
        return False, RAM["say"]
    RAM["say"] = "free RAM %d MB clears the %d MB floor" % (int(free), floor)
    return True, RAM["say"]


def status():
    """Everything /api/status carries about the door: receipts and the census. Never raises."""
    try:
        c = census()
    except Exception as e:
        c = {"ok": None, "families": {}, "roles": {}, "say": "census raised %s" % type(e).__name__}
    return {"door": dict(RECEIPT), "watchdog": dict(WATCHDOG), "ram": dict(RAM), "census": c,
            "ledgerDir": LEDGER_DIR}


if __name__ == "__main__":
    try:
        from console_safe import enable as _enable
        _enable()
    except Exception:
        pass
    print(json.dumps(status(), indent=2, default=str))
