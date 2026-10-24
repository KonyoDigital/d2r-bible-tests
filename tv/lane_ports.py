# -*- coding: utf-8 -*-
"""#144 — each heart2 prove lane hands a port base. A suite derives its ports from it.

A lone run of a suite (no TV_LANE_PORT_BASE) keeps the port that suite has always used, so
`python3 tv/test_control.py` still stays off his live console. Two prove lanes therefore cannot
both land on 17971 / 17972.

The bind itself deletes nothing. What deletes a tracked file is a request from the OTHER sandbox
that arrives on the shared listener and runs inside this one. The file-watcher law records that
unlink, and records that the same request on a lane's own port leaves the neighbour's file in place.
"""
import io
import os
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

ENV = "TV_LANE_PORT_BASE"
STAMPED = "TV_LANE_CONTROL_STAMPED"      # the control port stamp() itself wrote - the only one a re-stamp may move
# His console, the agent default, Kai, the predicter, Chrome, and the ports a lone suite pins.
FORBIDDEN = frozenset({17771, 17772, 17781, 8848, 9222, 9223, 17971, 17972, 17973, 17994})
# shard_suite owns 17981 upward. Lanes start clear of that and of the pinned suite ports.
BASE0 = 21001
STRIDE = 4          # agent, control, TV_LAW_PORT, and the spare TV_RENDER_PORT — lanes do not overlap

# ══ #160 (REG-2452) — A PROVER SLOT PER PROCESS AND A BROWSER SLOT PER CHROME, BOTH MACHINE-WIDE ══════════════════
# MEASURED at HEAD 7285e7efc: base_for_lane(n) was BASE0 + (n-1)*STRIDE in EVERY process, so the census and a push (or a
# worktree's pre-flight) proving at the same time bound the SAME ports - and a request from one sandbox on a listener the
# other holds is how a tracked file was deleted (the module docstring). stamp() never set TV_RENDER_PORT, so every lane
# inherited the ONE port the hook exports; and nothing capped Chrome machine-wide. So:
#   · claim_slot(): one flock'd file per slot under <git common dir>/heart2/lanes/ (prove_record's walk of .git, never
#     git), the first free one held by an open handle for the life of the process - a holder that dies, however it dies,
#     frees its slot. Windows: msvcrt's byte lock on the same files. Neither: slot 0, as before, and SAID.
#   · base_for_lane(lane, slot): each slot owns LANES_PER_SLOT * STRIDE ports of its own, clear of FORBIDDEN and of
#     shard_suite's range; slot 0 is exactly the old numbering, so a lone caller is unchanged.
#   · stamp(env, lane, slot) also sets TV_RENDER_PORT = base + 3 (the lane's spare): a lane's Chrome is its own.
#   · browser slots: K = min(HEART2_BROWSER_SLOTS or 2, 2) machine-wide - his ruling, at most two headless Chromes at
#     once on his Mac - as try_browser_slot() (never waits: a scheduler's take()), browser_slot() (waits) and
#     BrowserSemaphore (lock-shaped, a drop-in for one shared threading.Lock).
# HEART2_LANES_DIR names the slot directory (a law's seam). The law: test_two_provers_never_share_a_lane_port.
SLOTS = 8                       # provers holding disjoint port ranges at once on one machine
LANES_PER_SLOT = 16             # heart2.prove_workers caps a prove at 16 lanes
SLOT_SPAN = LANES_PER_SLOT * STRIDE
SHARD_PORTS = (17981, 17981 + 2 * 64)   # shard_suite.PORT_BASE + 2 per shard: never a lane's
BROWSER_CAP = 2                 # his ruling: never more than two headless Chromes at once on his Mac
ENV_LANES_DIR = "HEART2_LANES_DIR"
ENV_BROWSER_SLOTS = "HEART2_BROWSER_SLOTS"


def _slot(slot):
    s = int(slot or 0)
    if not 0 <= s < SLOTS:
        raise ValueError("prover slot %s is outside 0..%d" % (slot, SLOTS - 1))
    return s


def base_for_lane(lane, slot=0):
    """Port base for prove lane n (1-based) of prover slot `slot`. -> int. Adjacent lanes do not share a port, and two
    slots share none. Slot 0 is the numbering every caller had before #160."""
    n = int(lane)
    if n < 1:
        n = 1
    if n > LANES_PER_SLOT:
        raise ValueError("lane %s is past the %d lanes a prover slot holds" % (lane, LANES_PER_SLOT))
    b = BASE0 + (n - 1) * STRIDE
    b += _slot(slot) * SLOT_SPAN
    if any((b + i) in FORBIDDEN or SHARD_PORTS[0] <= (b + i) < SHARD_PORTS[1] or not (1024 <= (b + i) <= 65535)
           for i in range(STRIDE)):
        raise ValueError("lane %s port base %s collides with a reserved port" % (lane, b))
    return b


def _parse(raw):
    raw = ("" if raw is None else str(raw)).strip()
    if not raw.isdigit():
        return None
    b = int(raw)
    if any((b + i) in FORBIDDEN or not (1024 <= (b + i) <= 65535) for i in (0, 1)):
        return None
    return b


def current_base():
    """The lane base in this process, or None when nobody handed one (or it is not safe)."""
    return _parse(os.environ.get(ENV, ""))


def agent_port(default):
    b = current_base()
    return str(b if b is not None else int(default))


def control_port(default):
    b = current_base()
    return str((b + 1) if b is not None else int(default))


def adopt(agent_default, control_default, keep=False):
    """Set TV_PORT and TV_CONTROL_PORT. A lane base wins over a value already in the environment.

    keep=True is the old setdefault: with no lane base, a port the caller already chose stays.
    """
    if current_base() is None and keep:
        os.environ.setdefault("TV_PORT", agent_port(agent_default))
        os.environ.setdefault("TV_CONTROL_PORT", control_port(control_default))
        return
    os.environ["TV_PORT"] = agent_port(agent_default)
    os.environ["TV_CONTROL_PORT"] = control_port(control_default)


def adopt_agent(default):
    """Set TV_PORT only. A lane base wins; otherwise `default` (the suite's historical port)."""
    os.environ["TV_PORT"] = agent_port(default)


def adopt_control(default):
    """Set TV_CONTROL_PORT only. A lane base's control port wins; otherwise `default`."""
    os.environ["TV_CONTROL_PORT"] = control_port(default)


def stamp(env, lane, slot=0):
    """The ports one prove lane's gate runs with. Mutates `env` and returns it.

    REG-1820 - a TV_CONTROL_PORT already in `env` (run_gates.law_env's reserved dead port, or one the caller chose) SURVIVES:
    it was overwritten with base+1, a live port of this lane, and the law's ask reached a stranger again. Only an unset or
    his-console (17772) value takes the lane's own control port.
    #160 - `slot` is the prover's machine-wide slot (claim_slot), and TV_RENDER_PORT is the lane's own spare (base+3): the
    hook exports ONE render port to every child, so two lanes' Chromes asked for the same port."""
    b = base_for_lane(lane, slot)
    env[ENV] = str(b)
    env["TV_PORT"] = str(b)
    # REG-1857 - re-stamping one env for another lane moves the control port the PREVIOUS stamp gave it (that lane's
    # base+1), or it would sit beside this lane's other ports; a reserved dead port or a caller's choice is never moved.
    # REG-1895 - ...but ONLY a port THIS module stamped (recorded in STAMPED): a caller who reserved prev+1 on purpose, or a dead
    # port that numerically equals it, is the caller's and is never moved.
    if env.get("TV_CONTROL_PORT", "") in ("", "17772") or (env.get(STAMPED) and env.get("TV_CONTROL_PORT") == env.get(STAMPED)):
        env["TV_CONTROL_PORT"] = str(b + 1)
        env[STAMPED] = str(b + 1)
    env["TV_LAW_PORT"] = str(b + 2)
    env["TV_RENDER_PORT"] = str(b + 3)
    return env


# ── #160 — the machine-wide slots ────────────────────────────────────────────────────────────────────────────────────
_HELD = {}                      # "slot" -> (index, open handle): this process's prover slot, held until it exits
_HELD_LOCK = threading.Lock()
_SAID = set()


def _say(say, key, line):
    """A slot warning, once per process and key."""
    if key in _SAID:
        return
    _SAID.add(key)
    try:
        (say or (lambda s: None))(line)
    except Exception:
        pass


def lanes_dir(repo=None):
    """Where this machine's slot files live. -> (dir, None) | (dir, why it is not git's common dir)"""
    seam = os.environ.get(ENV_LANES_DIR)
    if seam:
        return seam, None
    try:
        import prove_record as _pr
        common = _pr._git_common_dir(repo or REPO)
    except Exception:
        common = None
    if common:
        return os.path.join(common, "heart2", "lanes"), None
    import tempfile
    uid = getattr(os, "getuid", lambda: "user")()
    d = os.path.join(tempfile.gettempdir(), "heart2-lanes-%s" % uid)
    return d, ("no git dir was found for this checkout, so the slots live in %s - shared only with provers that fall "
               "back the same way" % d)


def _try_lock(path):
    """Take `path`'s lock without waiting. -> (handle, how) held | (None, how) another holds it | (None, None) no lock
    primitive here. The handle IS the hold: closing it, or the process ending, gives the lock back."""
    fh = io.open(path, "a+b")
    try:
        import fcntl
    except ImportError:
        fcntl = None
    if fcntl is not None:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fh, "flock"
        except BlockingIOError:
            fh.close()
            return None, "flock"
        except OSError:
            fh.close()
            return None, None
    try:
        import msvcrt
    except ImportError:
        msvcrt = None
    if msvcrt is not None:
        try:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            return fh, "msvcrt"
        except OSError:
            fh.close()
            return None, "msvcrt"
    fh.close()
    return None, None


def claim_slot(say=None, wait_s=None, repo=None):
    """#160 - this process's machine-wide prover slot, held until the process ends. -> int 0..SLOTS-1 | None

    The first free slot file is locked and its handle kept, so two provers on one machine (the census, a push, a
    worktree's pre-flight) never hold one slot - and a holder that dies frees its slot with it. Asked again in the same
    process, the same slot. No lock primitive at all -> 0 (the numbering before #160), said. Every slot held -> wait
    up to wait_s (None: for ever, said once a minute), then None, said."""
    with _HELD_LOCK:
        if "slot" in _HELD:
            return _HELD["slot"][0]
        d, why = lanes_dir(repo)
        if why:
            _say(say, ("dir", d), "  \u26a0 #160: %s" % why)
        try:
            os.makedirs(d, exist_ok=True)
        except OSError as e:
            _say(say, ("mkdir", d), "  \u26a0 #160: the slot directory %s could not be made (%s) - prover slot 0 "
                                    "assumed, as before #160; two provers may share ports" % (d, type(e).__name__))
            return 0
        t0, told = time.time(), 0.0
        while True:
            for n in range(SLOTS):
                fh, how = _try_lock(os.path.join(d, "slot-%d.lock" % n))
                if fh is not None:
                    _HELD["slot"] = (n, fh)
                    return n
                if how is None:
                    _say(say, ("nolock", d), "  \u26a0 #160: no file lock on this machine - prover slot 0 assumed, "
                                             "as before #160; two provers may share ports")
                    return 0
            if wait_s is not None and time.time() - t0 >= wait_s:
                _say(say, ("full", d, t0), "  \u26a0 #160: all %d prover slots are held - no slot claimed" % SLOTS)
                return None
            if time.time() - told >= 60.0:
                told = time.time()
                try:
                    (say or (lambda s: None))("  #160: all %d prover slots are held - waiting for one" % SLOTS)
                except Exception:
                    pass
            time.sleep(0.5)


def held_slot():
    """The prover slot this process holds, or None."""
    h = _HELD.get("slot")
    return h[0] if h else None


def release_slot():
    """Give this process's prover slot back before it exits (a law's; a prover keeps it for its life)."""
    with _HELD_LOCK:
        h = _HELD.pop("slot", None)
    if h:
        try:
            h[1].close()
        except Exception:
            pass


def browser_cap():
    """K: min(HEART2_BROWSER_SLOTS or 2, 2) - the variable can lower it to 1, never raise it past his two."""
    raw = str(os.environ.get(ENV_BROWSER_SLOTS, "") or "").strip()
    try:
        k = int(raw) if raw else BROWSER_CAP
    except ValueError:
        k = BROWSER_CAP
    return max(1, min(k, BROWSER_CAP))


class BrowserSlot(object):
    """One of the machine's K browser slots, HELD. release() - or leaving a `with` - gives it back; so does the holder
    dying. `index` is which of the K; `how` the lock that holds it (None: no lock primitive here, so it counts nothing)."""

    def __init__(self, index, fh, how):
        self.index, self._fh, self.how = index, fh, how

    def release(self):
        fh, self._fh = self._fh, None
        if fh is not None:
            try:
                fh.close()
            except Exception:
                pass

    @property
    def held(self):
        return self._fh is not None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.release()
        return False


def try_browser_slot(say=None, repo=None):
    """#160 - a machine-wide browser slot NOW, or None when all K are held (never waits: a scheduler's take())."""
    d, why = lanes_dir(repo)
    if why:
        _say(say, ("dir", d), "  \u26a0 #160: %s" % why)
    try:
        os.makedirs(d, exist_ok=True)
    except OSError as e:
        _say(say, ("bmkdir", d), "  \u26a0 #160: the slot directory %s could not be made (%s) - browser slots are "
                                 "not counted machine-wide" % (d, type(e).__name__))
        return BrowserSlot(0, None, None)
    for k in range(browser_cap()):
        fh, how = _try_lock(os.path.join(d, "browser-%d.lock" % k))
        if fh is not None:
            return BrowserSlot(k, fh, how)
        if how is None:
            _say(say, ("bnolock", d), "  \u26a0 #160: no file lock on this machine - browser slots are not counted "
                                      "machine-wide")
            return BrowserSlot(k, None, None)
    return None


def browser_slot(timeout=None, say=None, repo=None, poll_s=0.2):
    """#160 - a machine-wide browser slot, WAITING for one. -> BrowserSlot | None (only when `timeout` s passed)"""
    t0 = time.time()
    while True:
        s = try_browser_slot(say, repo)
        if s is not None:
            return s
        if timeout is not None and time.time() - t0 >= timeout:
            return None
        time.sleep(poll_s)


class BrowserSemaphore(object):
    """Lock-shaped (acquire / release / with) over the machine's K browser slots: a drop-in for ONE threading.Lock that
    lanes share, but counted across every process on this machine. A thread holds at most one slot; release() gives
    back the calling thread's."""

    def __init__(self, say=None, repo=None):
        self._say, self._repo = say, repo
        self._mine = threading.local()

    def acquire(self, blocking=True, timeout=-1):
        if getattr(self._mine, "slot", None) is not None:
            raise RuntimeError("this thread already holds a browser slot")
        if not blocking:
            s = try_browser_slot(self._say, self._repo)
        else:
            s = browser_slot(None if timeout is None or timeout < 0 else timeout, self._say, self._repo)
        if s is None:
            return False
        self._mine.slot = s
        return True

    def release(self):
        s = getattr(self._mine, "slot", None)
        if s is None:
            raise RuntimeError("release of a browser slot this thread does not hold")
        self._mine.slot = None
        s.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *exc):
        self.release()
        return False
