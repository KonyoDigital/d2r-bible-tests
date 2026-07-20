#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# 📺 TV DIABLO — Control App (Mac + Windows · v927)
#
#   HD grimoire UI · ON / OFF / STOP / RESTART / SIM · agent HIDDEN.
#   Window: pywebview (real OS app window — NOT Chrome). Browser is fallback only.
#   ONE WINDOW: board = same-origin /board?app=1 · dual-launch refused.
#   Mac:     python3 tv/control_app.py --open  ·  TV DIABLO.app
#   Windows: pythonw tv/control_app.py --open · Desktop shortcut
#            ON = capture_win.ps1 (hidden, auto-pin D2R + eye.jpg) + tv_diablo.py --watch
#   ver stamp MUST match tv_diablo.VERSION (parity lock in test_control).
# ═══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import bisect
import inspect
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import base64
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CONTROL_PORT = int(os.environ.get("TV_CONTROL_PORT", "17772"))
AGENT_PORT = int(os.environ.get("TV_PORT", "17771"))
LOG_PATH = os.path.join(HERE, "control_agent.log")
PID_PATH = os.path.join(HERE, "control_agent.pid")
CAP_PID_PATH = os.path.join(HERE, "control_capture.pid")
UI_PATH = os.path.join(HERE, "control_ui.html")
BIBLE = os.path.join(REPO, "bible.html")
ART_DIR = os.path.realpath(os.path.join(REPO, "art"))
CAPTURE_PS1 = os.path.join(HERE, "capture_win.ps1")
HIST_DIR = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")   # v765 · v885 — TV_HIST = harness isolation
BOARD_PID_PATH = os.path.join(HERE, "board_window.pid")   # v773.1 — the ONE board window


def _hist_frame_paths(fid):
    """v940.4 — candidate on-disk paths for a journaled frameId.
    Verify beats use frameId 'N_ts#v' but the JPEG is always 'N_ts.jpg' (no #v file).
    Reel footage uses 'reel_<sid>/f_<ts>' relative form."""
    if not fid:
        return []
    fid = str(fid).strip()
    base = fid.split("#", 1)[0]  # strip verify suffix
    out = []
    for stem in (fid, base):
        if not stem:
            continue
        if stem.endswith(".jpg"):
            out.append(os.path.join(HIST_DIR, stem))
        else:
            out.append(os.path.join(HIST_DIR, stem + ".jpg"))
            out.append(os.path.join(HIST_DIR, stem))
    # de-dupe preserve order
    seen, uniq = set(), []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def _hist_has_frame(fid):
    """True if the archived photo for this frameId exists (base or #v or reel path)."""
    return any(os.path.isfile(p) for p in _hist_frame_paths(fid))


def _hist_frame_rel(fid):
    """Relative path under /hist/ for the UI (prefer the file that actually exists)."""
    if not fid:
        return ""
    for p in _hist_frame_paths(fid):
        if os.path.isfile(p):
            rel = os.path.relpath(p, HIST_DIR).replace("\\", "/")
            return rel
    return ""

# ── v941 THE DOSSIER — join all three eyes onto one beat ─────────────────────
# The theatre reads each frame three ways: 📸 the LOCKED intake pipeline (tally
# receipts), 🔵 the second-look verify lane, and 🧠 KAI (per-frame class + judge).
# These live as separate journal lanes keyed by different frameId shapes:
#   • verify rows carry frameId 'N_ts#v'      → base == the deep read's 'N_ts'
#   • kai rows carry frameId 'reel_<sid>/f_<ms>' → == the footage beat's frameId
#   • intake receipts carry no read frameId    → matched by tab + ts nearest
# _build_dossier_maps walks the session's rows ONCE (no O(n^2)) into lookup maps;
# _beat_dossier hangs {tally,verify,kai} on a read/footage beat from those maps.
def _build_dossier_maps(sess_rows):
    """v941 — single-pass join index for one session's journal rows.
    Returns {verify, kai, tab_ts, tab_receipts}; keys built for O(1)/O(log n) hits."""
    verify_by_base = {}   # deep frameId (verify '#v' stripped) -> compact verify dict
    kai_by_frame = {}     # reel frameId -> {"cls":.., "judge":..}
    tab_ts = {}           # tab(lower) -> sorted [ts] for bisect-nearest
    tab_receipts = {}     # tab(lower) -> {ts: compact receipt}
    for r in sess_rows:
        ln = r.get("lane")
        if ln == "verify":
            v = r.get("verify")
            if isinstance(v, dict):
                base = str(r.get("frameId") or "").split("#", 1)[0]
                if base:
                    # confirm/missed/not_present journal as name LISTS; the dossier
                    # reports counts. 'corrected' == names the second look ruled
                    # not-present (a correction of the first read).
                    verify_by_base[base] = {
                        "conf": v.get("conf"),
                        "confirm": len(v.get("confirm") or []),
                        "corrected": len(v.get("not_present") or []),
                        "missed": len(v.get("missed") or []),
                    }
        elif ln == "kai":
            k = r.get("kai")
            fid = str(r.get("frameId") or "")
            if fid and isinstance(k, dict):
                slot = kai_by_frame.setdefault(fid, {"cls": None, "judge": None})
                if k.get("cls") is not None:
                    slot["cls"] = k.get("cls")
                j = k.get("judge")
                if isinstance(j, dict):
                    slot["judge"] = {"name": j.get("name") or "",
                                     "tier": j.get("tier") or "",
                                     "score": j.get("score")}
        ik = r.get("intake")
        if isinstance(ik, dict):
            tab = str(ik.get("tab") or ik.get("kind") or "").lower()
            ts = int(r.get("ts") or r.get("captureTs") or 0)
            if tab and ts:
                cnts = ik.get("counts") if isinstance(ik.get("counts"), dict) else {}
                top = sorted(cnts.items(),
                             key=lambda kv: (-int(kv[1] or 0), str(kv[0])))[:8]
                tab_receipts.setdefault(tab, {})[ts] = {
                    "tab": ik.get("tab") or tab,
                    "kind": ik.get("kind") or "",
                    "ok": bool(ik.get("ok", True)),
                    "total": int(ik.get("total") or 0),
                    "counts": [[str(k2), int(v2 or 0)] for k2, v2 in top],
                }
                tab_ts.setdefault(tab, []).append(ts)
    for tab in tab_ts:
        tab_ts[tab].sort()
    # v944.5 (Konyo: "I don't want ANYTHING read 0 — read it according to the updated picture") —
    # the BEST receipt per tab this session: an errored/empty 0-shot must never be the truth when
    # a real read of the same tab exists. Highest ok-total wins; the theatre reads THAT count.
    tab_best = {}
    for tab, byts in tab_receipts.items():
        best = None
        for rc in byts.values():
            if not rc.get("ok", True):
                continue
            if best is None or int(rc.get("total") or 0) > int(best.get("total") or 0):
                best = rc
        if best is not None and int(best.get("total") or 0) > 0:
            tab_best[tab] = best
    return {"verify": verify_by_base, "kai": kai_by_frame,
            "tab_ts": tab_ts, "tab_receipts": tab_receipts, "tab_best": tab_best}


def _nearest_receipt(maps, tab, ts, window_ms=None):
    """Compact intake receipt for `tab` nearest to `ts` (bisect); None if none
    (or outside window_ms when given)."""
    tab = (tab or "").lower()
    tslist = maps["tab_ts"].get(tab)
    if not tslist or not ts:
        return None
    i = bisect.bisect_left(tslist, ts)
    best = None
    for j in (i - 1, i):
        if 0 <= j < len(tslist):
            cand = tslist[j]
            if best is None or abs(cand - ts) < abs(best - ts):
                best = cand
    if best is None or (window_ms is not None and abs(best - ts) > window_ms):
        return None
    return maps["tab_receipts"][tab].get(best)


def _beat_dossier(maps, beat):
    """v941 — {tally, verify, kai} for one read/footage beat, additive-only.
    Reads (lane deep, frameId 'N_ts') hit verify by base + tally by stashTab.
    Footage (frameId 'reel_<sid>/f_<ms>') hits kai exact + tally by KAI stash class."""
    fid = str(beat.get("frameId") or "")
    ts = int(beat.get("captureTs") or beat.get("ts") or 0)
    is_footage = bool(beat.get("footage"))
    verify = maps["verify"].get(fid.split("#", 1)[0]) if fid else None
    kai = maps["kai"].get(fid)
    if kai and kai.get("cls") is None and kai.get("judge") is None:
        kai = None
    tally = None
    # v944.4 — the router label already rides the beat (join at build time). Use it too, so a
    # stash frame gets a receipt even when KAI's own cls was empty (OCR-dark grids).
    _rlabel = str(beat.get("label") or (kai or {}).get("cls") or "")
    if is_footage:
        # Only footage KAI/router proved is a stash tab gets a receipt (ts within ±120s).
        cls = _rlabel
        if isinstance(cls, str) and cls.startswith("stash-"):
            tally = _nearest_receipt(maps, cls[6:], ts, window_ms=120000)
    else:
        tab = str(beat.get("stashTab") or "")
        if tab:
            tally = _nearest_receipt(maps, tab, ts, window_ms=None)
    # v944.4 THE READ-STATUS VERDICT (Konyo: "I don't know if it was read or not correctly here")
    # — turn the router label + tally into a plain answer the retro debugger can SHOW per frame:
    #   read   → this tab's intake fired and counted N (cross-referenced list in tally.counts)
    #   miss   → a stash tab the router recognized, but 0 counted / no receipt = an unread panel
    #   named  → a deep read named item(s) on this frame (verify carries the confirm/miss counts)
    #   scene  → gameplay/other, nothing to register
    read_status = None
    if _rlabel.startswith("stash-") or _rlabel in ("stash", "inventory"):
        _tab = _rlabel[6:] if _rlabel.startswith("stash-") else _rlabel
        # v944.5 — the nearest receipt to THIS frame may be a 0/error shot, but if the tab was
        # really read anywhere this session, that real count is the truth (the "updated picture").
        _best = (maps.get("tab_best") or {}).get(_tab.lower())
        _near_tot = int((tally or {}).get("total") or 0) if tally else 0
        if _best and int(_best.get("total") or 0) > 0:
            # a real read exists → never report 0; surface the real count + supersede the tally
            if _near_tot <= 0:
                tally = _best
            read_status = {"kind": "read", "tab": _tab,
                           "counted": int(_best.get("total") or 0), "superseded": _near_tot <= 0}
        else:
            read_status = {"kind": "miss", "tab": _tab, "counted": _near_tot}
    elif (beat.get("names") or []):
        read_status = {"kind": "named", "counted": len(beat.get("names") or [])}
    return {"tally": tally, "verify": verify or None, "kai": kai,
            "router": {"label": beat.get("label"), "verdict": beat.get("routeVerdict")}
            if beat.get("label") else None,
            "readStatus": read_status}


IS_WIN = sys.platform.startswith("win")
# Windows: CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
_WIN_CREATE = 0x00000200 | 0x08000000 if IS_WIN else 0

_ART_MIME = {
    ".png": "image/png",
    ".gif": "image/gif",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}

_lock = threading.Lock()
_agent_proc = None  # type: ignore
_stop_inflight = False   # v768 (Grok R2) — a threaded stop/farewell is running; ON/RESTART must wait
_capture_proc = None  # type: ignore
_agent_mode = "off"  # off | live | sim
_log_fp = None
_EXIT_STOP_DONE = False
_EXIT_STOP_LOCK = threading.Lock()
_WINDOW_ONLY = False   # v935.8 — secondary --window-only attach must NOT kill ON AIR


def _env_clean(sim=False):
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    extras = []
    if IS_WIN:
        extras = [
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python312"),
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python312\Scripts"),
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python313"),
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python313\Scripts"),
            os.path.expandvars(r"%LocalAppData%\Microsoft\WinGet\Links"),
            os.path.expandvars(r"%ProgramFiles%\Git\cmd"),
            os.path.expanduser(r"~\.local\bin"),
        ]
    else:
        extras = [
            "/opt/homebrew/bin",
            "/usr/local/bin",
            os.path.expanduser("~/.local/bin"),
        ]
    head = os.pathsep.join([p for p in extras if p and os.path.isdir(p)])
    if head:
        env["PATH"] = head + os.pathsep + env.get("PATH", "")
    if sim:
        env["TV_STUB"] = "1"
    else:
        env.pop("TV_STUB", None)
    env["TV_PORT"] = str(AGENT_PORT)
    # v784 — Windows capture default AUTO (pin D2R.exe); Mac agent reads TV_CAPTURE itself
    if IS_WIN and not (env.get("TV_CAPTURE") or "").strip():
        env["TV_CAPTURE"] = "auto"
    return env


_BR_CACHE = {"ping": False, "st": None, "ts": 0.0}
_PID_CACHE = {"pid": None, "ts": 0.0}


def _pid_cached():
    """v872 — the status poll must NEVER pay an lsof subprocess. Prefer the tracked child;
    fall back to a port scan at most every 10s."""
    with _lock:
        if _agent_proc is not None and _agent_proc.poll() is None:
            return int(_agent_proc.pid)
    now = time.time()
    if now - _PID_CACHE["ts"] > 10.0:
        _PID_CACHE["pid"] = _port_listener_pid()
        _PID_CACHE["ts"] = now
    return _PID_CACHE["pid"]


def _console_beacon(event="hb"):
    """v875 (Konyo: 'a tracker so I know whose console is online — like the site visits') —
    phone the presence beacon home. Silent on any failure; never blocks a caller."""
    try:
        import base64 as _b64, socket as _sock
        st = status_payload()
        body = json.dumps({
            "machine": _sock.gethostname().split(".")[0],
            "platform": st.get("platform"), "ver": st.get("ver"),
            "mode": st.get("mode"), "event": event,
            "user": os.environ.get("TVD_USER", ""),
            "reads": st.get("readCount") or 0,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://bull-4-u.com/api/console", data=body,
            headers={"Content-Type": "application/json", "User-Agent": "TVD-Console/1.0",
                     "Authorization": "Basic " + _b64.b64encode(b"app:DeanDiablo").decode()},
            method="POST")
        with urllib.request.urlopen(req, timeout=8) as r:
            r.read()
    except Exception:
        pass


def _console_beacon_async(event):
    threading.Thread(target=_console_beacon, args=(event,), daemon=True).start()


def _console_beacon_loop():
    _console_beacon("boot")
    _last_mode = [None]
    while True:
        time.sleep(240)
        try:
            m = status_payload().get("mode")
            _console_beacon("mode:" + str(m) if m != _last_mode[0] and _last_mode[0] is not None else "hb")
            _last_mode[0] = m
        except Exception:
            pass


def _bridge_prober():
    """v872 (Konyo: 'STANDBY keeps jumping at me mid session') — ONE background thread probes
    the agent bridge every 1.2s; every /api/status poll reads the cache. Under full game load
    the console poll went 300ms × (ping 0.6s + state 0.8s + lsof) and choked itself."""
    while True:
        try:
            ping = _bridge_ping() is not None
            st = _bridge_state() if ping else None
            _BR_CACHE["ping"], _BR_CACHE["st"], _BR_CACHE["ts"] = ping, st, time.time()
            if ping:
                globals()["_BRIDGE_LAST_OK"] = time.time()
        except Exception:
            pass
        time.sleep(1.2)


def _bridge_ping():
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{AGENT_PORT}/ping", timeout=0.6
        ) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _bridge_state():
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{AGENT_PORT}/state", timeout=0.8
        ) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


_TZ_CACHE = {"ts": 0.0, "code": 0, "body": None}
_TZ_LOCK = threading.Lock()
_TZ_UPSTREAM = os.environ.get("TVD_TZ_UPSTREAM", "https://bull-4-u.com/api/tz")
_TZ_AUTH = base64.b64encode(b"app:DeanDiablo").decode("ascii")


def _tz_proxy():
    # Terror Zone tracker relay: the board's /api/tz only exists as a Pages
    # function on the live deploy; the shell serves the board locally, so we
    # fetch upstream (through the site's basic-auth gate) and cache 90s.
    # Upstream dead → serve the last good rotation (stale flag) so the card
    # degrades to old-but-honest instead of "tracker is down".
    with _TZ_LOCK:
        now = time.time()
        if _TZ_CACHE["body"] is not None and now - _TZ_CACHE["ts"] < 90:
            return _TZ_CACHE["code"], _TZ_CACHE["body"]
        try:
            req = urllib.request.Request(
                _TZ_UPSTREAM,
                headers={
                    "Authorization": "Basic " + _TZ_AUTH,
                    # Cloudflare 403s the default Python-urllib UA
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) TVDiablo/944",
                },
            )
            with urllib.request.urlopen(req, timeout=12) as r:
                body = json.loads(r.read().decode("utf-8", "replace"))
            _TZ_CACHE.update(ts=now, code=200, body=body)
            return 200, body
        except Exception as e:
            if _TZ_CACHE["body"] is not None:
                stale = dict(_TZ_CACHE["body"])
                stale["stale"] = True
                return 200, stale
            return 502, {"error": f"tz upstream unreachable: {e}"}


def _port_listener_pid(port=None):
    """PID listening on TCP port (cross-platform)."""
    port = int(port or AGENT_PORT)
    if IS_WIN:
        try:
            # netstat -ano: find LISTENING on :port
            out = subprocess.check_output(
                ["netstat", "-ano", "-p", "tcp"],
                stderr=subprocess.DEVNULL,
                text=True,
                creationflags=_WIN_CREATE,
            )
            needle = f":{port}"
            for line in out.splitlines():
                if "LISTENING" not in line.upper():
                    continue
                if needle not in line:
                    continue
                # only care about local bind
                parts = line.split()
                if len(parts) < 5:
                    continue
                local = parts[1] if parts[0].upper() == "TCP" else parts[0]
                if not local.endswith(needle) and f"]{needle}" not in local:
                    # also accept 0.0.0.0:port / [::]:port
                    if needle not in local:
                        continue
                try:
                    return int(parts[-1])
                except ValueError:
                    continue
        except Exception:
            return None
        return None
    try:
        out = subprocess.check_output(
            ["lsof", f"-tiTCP:{port}", "-sTCP:LISTEN"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if not out:
            return None
        return int(out.splitlines()[0])
    except Exception:
        return None


def _agent_alive():
    global _agent_proc
    with _lock:
        if _agent_proc is not None and _agent_proc.poll() is None:
            return True
    return _pid_cached() is not None   # v877 (army B#1) — the fallback ran a fresh lsof PER POLL


def _write_pid(path, pid):
    try:
        with open(path, "w") as f:
            f.write(str(pid))
    except Exception:
        pass


def _read_pid(path):
    try:
        with open(path) as f:
            return int(f.read().strip())
    except Exception:
        return None


def _kill_pid(pid, force=False):
    if pid is None:
        return
    if IS_WIN:
        args = ["taskkill", "/PID", str(pid), "/T"]
        if force:
            args.append("/F")
        try:
            subprocess.run(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=_WIN_CREATE,
            )
        except Exception:
            pass
        return
    # v847 — agent is NOT setsid on Mac (TCC). killpg(pid) often fails; prefer kill then group.
    sig = signal.SIGKILL if force else signal.SIGTERM
    try:
        os.kill(pid, sig)
    except ProcessLookupError:
        return
    except Exception:
        pass
    try:
        os.killpg(pid, sig)
    except Exception:
        pass


def _ask_agent_shutdown(farewell=True, reason="stop", timeout=2.0):
    """v847 — polite shutdown: agent journals session_end (+ optional farewell) then exits."""
    try:
        from urllib.parse import quote as _quote
        q = "farewell=%s&reason=%s" % ("1" if farewell else "0",
                                        _quote(str(reason)[:40]))
        urllib.request.urlopen(
            f"http://127.0.0.1:{AGENT_PORT}/shutdown?{q}", timeout=timeout
        ).read()
        return True
    except Exception:
        return False


def _collect_agent_pids():
    """Every PID that might be the live agent (owned child, port listener, pid file)."""
    pids = set()
    with _lock:
        if _agent_proc is not None and _agent_proc.poll() is None:
            pids.add(int(_agent_proc.pid))
    for p in (_port_listener_pid(), _read_pid(PID_PATH)):
        if p:
            pids.add(int(p))
    return [p for p in pids if p]


def _pid_alive(pid):
    if pid is None:
        return False
    # v778-pre (BUG A) — our OWN child becomes a ZOMBIE on death until reaped: os.kill(pid,0)
    # succeeds on zombies, so the stop thread stared at a corpse for the full 90s farewell
    # window. poll() both answers truthfully AND reaps.
    try:
        with _lock:
            if _agent_proc is not None and _agent_proc.pid == pid:
                return _agent_proc.poll() is None
    except Exception:
        pass
    if IS_WIN:
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                stderr=subprocess.DEVNULL,
                text=True,
                creationflags=_WIN_CREATE,
            )
            return str(pid) in out
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except Exception:
        return False


def _start_capture(env, log_fp):
    """Windows only: hidden capture_win.ps1 loop."""
    global _capture_proc
    if not IS_WIN:
        return None
    if not os.path.isfile(CAPTURE_PS1):
        log_fp.write("!! capture_win.ps1 missing — Windows ON will have no frames\n")
        log_fp.flush()
        return None
    # already running?
    old = _read_pid(CAP_PID_PATH)
    if old and _pid_alive(old):
        return old
    try:
        _capture_proc = subprocess.Popen(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-WindowStyle",
                "Hidden",
                "-File",
                CAPTURE_PS1,
            ],
            cwd=REPO,
            env=env,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=_WIN_CREATE,
        )
        _write_pid(CAP_PID_PATH, _capture_proc.pid)
        log_fp.write(f"capture_win.ps1 pid {_capture_proc.pid}\n")
        log_fp.flush()
        return _capture_proc.pid
    except Exception as e:
        log_fp.write(f"!! capture start failed: {e}\n")
        log_fp.flush()
        return None


_CAP_RESTARTED = False
def _capture_health():
    """v793 (Grok R4 #5a) — Windows capture lamp: LINKED / DEAD / n/a. A dead capture_win.ps1
    used to leave a frozen eye with the lamp still mint. Auto-restart ONCE, loudly."""
    global _CAP_RESTARTED
    if not IS_WIN:
        return ""
    if _agent_mode not in ("live", "sim"):
        _CAP_RESTARTED = False
        return ""
    pid = None
    try:
        with _lock:
            if _capture_proc is not None and _capture_proc.poll() is None:
                return "LINKED"
        pid = _read_pid(CAP_PID_PATH)
    except Exception:
        pass
    if pid and _pid_alive(pid):
        return "LINKED"
    if not _CAP_RESTARTED and _log_fp:
        _CAP_RESTARTED = True
        try:
            _log_fp.write("!! capture_win.ps1 DIED mid-session — auto-restarting once\n")
            _log_fp.flush()
            _start_capture(_env_clean(sim=(_agent_mode == "sim")), _log_fp)
            return "RESTARTED"
        except Exception:
            pass
    return "DEAD"


def _stop_capture():
    global _capture_proc
    pid = None
    with _lock:
        if _capture_proc is not None and _capture_proc.poll() is None:
            pid = _capture_proc.pid
        else:
            pid = _read_pid(CAP_PID_PATH)
        _capture_proc = None
    if pid:
        _kill_pid(pid, force=True)
    try:
        if os.path.isfile(CAP_PID_PATH):
            os.remove(CAP_PID_PATH)
    except Exception:
        pass


def start_agent(sim=False, test=False):
    global _agent_proc, _agent_mode, _log_fp
    # v847 — never "already live" on a stranger/orphan: hard-stop anything on the bridge first
    if _stop_inflight:
        return {"ok": False, "msg": "farewell still finishing — try again in a moment",
                "mode": "stopping", "error": "still stopping"}
    if _agent_alive() or _port_listener_pid() is not None:
        # If we own a healthy child and user re-clicked ON, treat as already on
        with _lock:
            owned = _agent_proc is not None and _agent_proc.poll() is None
        if owned and _bridge_ping() is not None and not sim:
            return {"ok": True, "msg": "already on air", "mode": _agent_mode or "live",
                    "pid": _agent_proc.pid if _agent_proc else None}
        # Orphan / stale / wrong mode → kill cleanly (no second farewell if already stopping)
        stop_agent(farewell=False)
        time.sleep(0.35)

    with _lock:
        if _agent_proc is not None and _agent_proc.poll() is None:
            return {"ok": True, "msg": "already running", "mode": _agent_mode}
        # re-check port after stop
        if _port_listener_pid() is not None:
            # last resort force-kill port holder
            _kill_pid(_port_listener_pid(), force=True)
            time.sleep(0.2)

        os.makedirs(HERE, exist_ok=True)
        if _log_fp:
            try:
                _log_fp.close()
            except Exception:
                pass
        try:   # v765 — cap the agent log (~2MB keeps months; never grows unbounded)
            if os.path.isfile(LOG_PATH) and os.path.getsize(LOG_PATH) > 2_000_000:
                with open(LOG_PATH) as _lf:
                    _tail = _lf.readlines()[-4000:]
                with open(LOG_PATH, "w") as _lf:
                    _lf.writelines(_tail)
        except Exception:
            pass
        _log_fp = open(LOG_PATH, "a", buffering=1)
        plat = "windows" if IS_WIN else "mac"
        _log_fp.write(
            f"\n—— control start {time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"mode={'sim' if sim else 'live'} · {plat} ——\n"
        )
        _log_fp.flush()

        env = _env_clean(sim=sim)
        if test:
            # v786 - button-matrix / harness runs must NEVER become theatre reels
            env["TV_NO_JOURNAL"] = "1"
        # v786 (cousin: 'ON AIR just spins') - LOUD preflight: the #1 silent killer is a
        # missing claude CLI; the agent dies at boot and the UI spun forever with no reason.
        if not sim and not env.get("TV_STUB") and not env.get("TV_CLAUDE_BIN"):
            import shutil as _sh
            if not _sh.which("claude", path=env.get("PATH", "")):
                _agent_mode = "off"
                _log_fp.write("!! claude CLI not found on PATH - agent cannot see\n")
                _log_fp.flush()
                return {"ok": False,
                        "error": "Claude Code CLI not found - install it, then press ON AIR again",
                        "fix": ("irm https://claude.ai/install.ps1 | iex" if IS_WIN
                                else "curl -fsSL https://claude.ai/install.sh | bash"),
                        "mode": "off"}
        # Windows needs the capture half; Mac agent uses screencapture itself
        if IS_WIN:
            _start_capture(env, _log_fp)

        cmd = [sys.executable, os.path.join(HERE, "tv_diablo.py")]
        if IS_WIN:
            cmd.append("--watch")

        popen_kw = dict(
            args=cmd,
            cwd=REPO,
            env=env,
            stdout=_log_fp,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
        )
        if IS_WIN:
            popen_kw["creationflags"] = _WIN_CREATE
        else:
            # v779 — do NOT setsid on Mac. A start_new_session child of a launchd-orphaned
            # control (ppid 1) loses the Screen Recording TCC chain; screencapture then
            # writes nothing and the eye freezes on a stale desktop frame.
            popen_kw["start_new_session"] = False

        _agent_proc = subprocess.Popen(**popen_kw)
        _write_pid(PID_PATH, _agent_proc.pid)
        _agent_mode = "sim" if sim else "live"

    for _ in range(50):
        if _bridge_ping() is not None:
            break
        time.sleep(0.15)
    # v786 - a dead-at-boot agent must SAY SO, not leave the lamp spinning (cousin's Windows hang)
    if _bridge_ping() is None and (_agent_proc is None or _agent_proc.poll() is not None):
        with _lock:
            _agent_mode = "off"
        tail = ""
        try:
            with open(LOG_PATH, "rb") as _lf:
                tail = _lf.read()[-1500:].decode("utf-8", "replace")
        except Exception:
            pass
        return {"ok": False, "error": "agent died at boot - see log", "logTail": tail, "mode": "off"}
    return {
        "ok": True,
        "msg": "started",
        "mode": _agent_mode,
        "pid": _agent_proc.pid if _agent_proc else None,
        "platform": "windows" if IS_WIN else "mac",
        "watch": IS_WIN,
    }


def _prewarm_seal_cache():
    """v880 (Grok j / back-pass #4) — build the theatre's ?w=1280 derivatives for the NEWEST
    sealed session in a low-priority background thread: first playback pays no sips storm.
    Mac only, concurrency 1, errors swallowed, never blocks the seal."""
    if IS_WIN:
        return
    def _run():
        try:
            time.sleep(2.0)
            if HERE not in sys.path:
                sys.path.insert(0, HERE)
            import replay as _rp
            try:
                sessions = _rp.split_sessions(_rp.load_journal())
                rows = sessions[-1] if sessions else []
            except Exception:
                rows = []
            fids = [str(r.get("frameId")) + ".jpg" for r in (rows or []) if r.get("frameId")]
            cache_dir = os.path.join(HIST_DIR, "cache1280")
            os.makedirs(cache_dir, exist_ok=True)
            for fb in fids[:400]:
                src = os.path.join(HIST_DIR, fb)
                dst = os.path.join(cache_dir, fb)
                if not os.path.isfile(src) or os.path.isfile(dst):
                    continue
                try:
                    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "72",
                                    "--resampleHeightWidthMax", "1280", src, "--out", dst],
                                   capture_output=True, timeout=10,
                                   preexec_fn=(lambda: os.nice(15)))
                except Exception:
                    pass
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True, name="tvd-prewarm").start()


def _force_kill_all_agents(reason=""):
    """v926.2 — the guaranteed stop: SIGKILL every agent pid + port holder, clear state, always
    return a valid response. The agent journals incrementally, so a hard kill loses at most the
    session_end marker (the library still shows the run). Used when the polite path raises/hangs."""
    global _agent_proc, _agent_mode, _stop_inflight, _BOARD_OPENED
    try:
        pids = set(_collect_agent_pids()) | set(filter(None, [_port_listener_pid(), _read_pid(PID_PATH)]))
        for pid in pids:
            try: _kill_pid(pid, force=True)
            except Exception: pass
        time.sleep(0.4)
    except Exception:
        pass
    try: _stop_capture()
    except Exception: pass
    with _lock:
        _agent_proc = None
        _agent_mode = "off"
    _stop_inflight = False
    _BOARD_OPENED = False
    try:
        if os.path.isfile(PID_PATH):
            os.remove(PID_PATH)
    except Exception:
        pass
    dead = _port_listener_pid() is None
    return {"ok": True, "msg": "force-stopped · off" + (" · " + reason if reason else ""),
            "farewell": False, "sessionSaved": True, "bridgeDown": dead, "forced": True}


def _console_exit_stop_onair(reason="quit"):
    """v935.8 — EXIT SAFEGUARD (Konyo: 'exiting the console must stop ON AIR — it's always on').

    Closing the pywebview window used to only `srv.shutdown()` and LEAVE the agent live on
    :17771 (the banner even said 'agent left as-is'). That orphan kept ON AIR forever.
    Now every real exit path — window close, atexit, SIGTERM/SIGINT — seals + stops the
    agent (same as tvd stop /api/stop, farewell OFF so quit is instant). Idempotent.
    """
    global _EXIT_STOP_DONE
    # Secondary --window-only attach: the primary control process owns the agent.
    if globals().get("_WINDOW_ONLY"):
        return {"ok": True, "msg": "window-only — primary owns ON AIR", "skipped": True}
    with _EXIT_STOP_LOCK:
        if _EXIT_STOP_DONE:
            return {"ok": True, "msg": "exit stop already ran", "skipped": True}
        _EXIT_STOP_DONE = True
    print(f"📺 exit safeguard — stopping ON AIR ({reason})…", flush=True)
    try:
        # If nothing is on air, stop_agent is cheap and returns already-off.
        if not _agent_alive() and _port_listener_pid() is None and _agent_mode == "off":
            print("   already off — nothing to stop", flush=True)
            return {"ok": True, "msg": "already off", "farewell": False}
    except Exception:
        pass
    try:
        r = stop_agent(farewell=False)
        print(f"   stop_agent → {r.get('msg') or r}", flush=True)
        # Belt + suspenders: anything still holding :17771 dies now
        if _port_listener_pid() is not None or _agent_alive():
            r2 = _force_kill_all_agents(f"exit-safeguard residual ({reason})")
            print(f"   residual force → {r2.get('msg') or r2}", flush=True)
            return r2
        return r
    except Exception as e:
        print(f"   stop_agent raised ({e}) — force kill", flush=True)
        try:
            return _force_kill_all_agents(f"exit-safeguard ({reason}): {e}")
        except Exception as e2:
            print(f"   force kill failed: {e2}", flush=True)
            return {"ok": False, "msg": str(e2)}


def stop_agent(farewell=True):
    """v847/v899 — OFF/STOP both SAVE the session (session_end journal via /shutdown).
    STOP: short farewell (hard-cap ~18s, was 95s). OFF: seal only. Then hard-kill orphans.
    Never leave _stop_inflight True if the agent is already dead (unstick ON AIR)."""
    global _agent_proc, _agent_mode, _stop_inflight, _BOARD_OPENED
    if _stop_inflight:
        # another stop is running — wait briefly, then force-clear if agent already gone
        deadline = time.time() + (18 if farewell else 12)
        while _stop_inflight and time.time() < deadline:
            if not _agent_alive() and _port_listener_pid() is None:
                _stop_inflight = False
                _agent_mode = "off"
                return {"ok": True, "msg": "already off", "farewell": farewell, "sessionSaved": True}
            time.sleep(0.2)
        if not _agent_alive() and _port_listener_pid() is None:
            _stop_inflight = False
            _agent_mode = "off"
            return {"ok": True, "msg": "already off", "farewell": farewell, "sessionSaved": True}
        # hung stop — force clear so ON AIR is not permanently blocked
        _stop_inflight = False
    _stop_inflight = True
    try:
        pids = _collect_agent_pids()
        if not pids and not IS_WIN:
            _agent_mode = "off"
            _stop_capture()
            _BOARD_OPENED = False
            return {"ok": True, "msg": "already off", "farewell": farewell, "sessionSaved": True}

        # 1) Polite shutdown — agent seals sessions.jsonl (session_end) then exits
        asked = _ask_agent_shutdown(
            farewell=bool(farewell),
            reason=("stop" if farewell else "off"),
            timeout=1.5,
        )

        # 2) If polite path didn't engage, fall back to signals
        if not asked and pids:
            sent_break = False
            if IS_WIN:
                with _lock:
                    if (
                        _agent_proc is not None
                        and _agent_proc.poll() is None
                    ):
                        try:
                            _agent_proc.send_signal(signal.CTRL_BREAK_EVENT)
                            sent_break = True
                        except Exception:
                            pass
            if not sent_break:
                for pid in pids:
                    _kill_pid(pid, force=False)

        # 3) Wait for bridge death, then FORCE-KILL — v926 (Konyo: 'i cant end session' again).
        # close_session journals session_end FIRST, so the reel is already sealed on disk before
        # any slow step: a fast force-kill can never lose the session. LIGHT End Session has no
        # farewell vision read, so 6s/3s is plenty — the old 18s/12s made a stuck agent feel dead.
        wait_s = 6 if farewell else 3
        deadline = time.time() + wait_s
        while time.time() < deadline:
            if _port_listener_pid() is None and not any(_pid_alive(p) for p in pids):
                break
            time.sleep(0.2)
        else:
            # force-kill every remaining agent pid + port holder
            for pid in set(pids) | set(filter(None, [_port_listener_pid(), _read_pid(PID_PATH)])):
                _kill_pid(pid, force=True)
            time.sleep(0.25)

        # always stop Windows capture with the agent
        _stop_capture()

        with _lock:
            if _agent_proc is not None:
                try:
                    _agent_proc.poll()  # reap zombie
                except Exception:
                    pass
            _agent_proc = None
            _agent_mode = "off"
        try:
            if os.path.isfile(PID_PATH):
                os.remove(PID_PATH)
        except Exception:
            pass
        # v785 — belt for the agent's own _eye_clear
        try:
            _eye = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames", "eye.jpg")
            if os.path.isfile(_eye):
                os.remove(_eye)
        except Exception:
            pass
        _BOARD_OPENED = False
        dead = _port_listener_pid() is None
        return {
            "ok": True,
            "msg": "session saved · off" if dead else "stop requested · forcing",
            "farewell": bool(farewell),
            "sessionSaved": True,
            "bridgeDown": dead,
        }
    finally:
        _stop_inflight = False
        try:
            _prewarm_seal_cache()   # v879 (Grok j) — theatre derivatives warm while the Mac is quiet
        except Exception:
            pass


def _file_url(path, fragment=""):
    ap = os.path.abspath(path).replace("\\", "/")
    if IS_WIN:
        # file:///C:/Users/...
        if not ap.startswith("/"):
            ap = "/" + ap
        url = "file://" + ap
    else:
        url = "file://" + ap
    if fragment:
        url += "#" + fragment
    return url


_MAC_BROWSERS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]

_BOARD_OPENED = False
def _open_board_once():
    """v764 — ON/SIM auto-open the board only ONCE per control session; afterwards the
    already-open tab lights up by itself (the board's auto-sync probe). No duplicate tabs."""
    global _BOARD_OPENED
    if _BOARD_OPENED:
        return "already-open (auto-sync)"
    _BOARD_OPENED = True
    open_board(auto_on=True)
    return "opened"

def _open_board_native(tab="session"):
    """v767.1 (Konyo: 'no need for Chrome anymore') — the BOARD opens in its own native
    window too: a sibling process runs pywebview on the LOCAL bible.html#tvd. Returns True
    if the native window spawned; False → caller falls back to a browser."""
    try:
        import webview  # noqa: F401
    except ImportError:
        if not ensure_webview():
            return False
    # v773.1 — SINGLETON: Grok's button-testing spawned 26 accumulated board windows (each a
    # python+WebKit tree) and lagged the whole Mac. Exactly ONE board window may live.
    try:
        if os.path.isfile(BOARD_PID_PATH):
            try:
                old = int(open(BOARD_PID_PATH).read().strip() or 0)
                if old:
                    os.kill(old, signal.SIGKILL)
            except Exception:
                pass
    except Exception:
        pass
    try:
        proc = subprocess.Popen(
            [sys.executable, os.path.abspath(__file__), "--board-window", "--hash=" + (tab or "session")],
            cwd=REPO,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_WIN_CREATE if IS_WIN else 0,
        )
        try:
            with open(BOARD_PID_PATH, "w") as f:
                f.write(str(proc.pid))
        except Exception:
            pass
        return True
    except Exception:
        return False

def open_board(auto_on=True, tab="session"):
    """Open the bible TV·D tab. v764: the board AUTO-SYNCS to the bridge now (lamp + probe),
    so the deep link only needs to LAND on #tvd — and macOS `open` DROPS file:// fragments
    (the 'routes me to the wrong page' bug), so prefer a direct browser spawn like Windows."""
    if not os.path.isfile(BIBLE):
        return {"ok": False, "msg": "bible.html missing"}
    if _open_board_native(tab):
        return {"ok": True, "msg": "board opened (native window)", "tab": tab}
    url = _file_url(BIBLE, tab or "session")
    try:
        if sys.platform == "darwin":
            opened = False
            for browser in _MAC_BROWSERS:
                if os.path.isfile(browser):
                    try:
                        subprocess.Popen(
                            [browser, url],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        opened = True
                        break
                    except Exception:
                        continue
            if not opened:
                subprocess.Popen(
                    ["open", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        elif IS_WIN:
            # Prefer a real browser so the #hash survives (os.startfile often drops it)
            opened = False
            for browser in _windows_browsers():
                try:
                    subprocess.Popen(
                        [browser, url],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=_WIN_CREATE,
                    )
                    opened = True
                    break
                except Exception:
                    continue
            if not opened:
                os.startfile(url)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", url])
        return {"ok": True, "msg": "board opened", "url": url}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def _windows_browsers():
    """Ordered Chrome/Edge/Brave paths for --app fallback only."""
    cands = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ]
    return [c for c in cands if c and os.path.isfile(c)]


def ensure_webview():
    """Import pywebview; try a one-shot user pip install if missing."""
    try:
        import webview  # noqa: F401

        return True
    except ImportError:
        pass
    # one attempt — installers also pre-install; this covers first-run edge cases
    # PEP 668 (Homebrew/managed pythons) blocks even --user installs — try plain first,
    # then once more with --break-system-packages (a user-scoped GUI dep, not a system change).
    for extra in ([], ["--break-system-packages"]):
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", "--quiet",
                 "pywebview>=5.0", *extra],
                check=False,
                timeout=180,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=_WIN_CREATE if IS_WIN else 0,
            )
        except Exception:
            continue
        try:
            import webview  # noqa: F401
            break
        except ImportError:
            continue
    try:
        import webview  # noqa: F401

        return True
    except ImportError:
        return False


def _open_browser_app_fallback(url):
    """Last resort if pywebview is unavailable — Chrome/Edge app mode."""
    if sys.platform == "darwin":
        for app in (
            "Google Chrome",
            "Chromium",
            "Microsoft Edge",
            "Brave Browser",
            "Arc",
        ):
            try:
                r = subprocess.run(
                    ["open", "-na", app, "--args", f"--app={url}", "--new-window"],
                    capture_output=True,
                    timeout=5,
                )
                if r.returncode == 0:
                    return
            except Exception:
                continue
        subprocess.Popen(["open", url])
        return
    if IS_WIN:
        for browser in _windows_browsers():
            try:
                subprocess.Popen(
                    [browser, f"--app={url}", "--window-size=1100,780"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=_WIN_CREATE,
                )
                return
            except Exception:
                continue
        try:
            os.startfile(url)  # type: ignore[attr-defined]
        except Exception:
            pass
        return
    try:
        import webbrowser

        webbrowser.open(url)
    except Exception:
        pass


def open_control_window():
    """Open the real native app window (pywebview). Blocks until the user closes it."""
    url = f"http://127.0.0.1:{CONTROL_PORT}/"
    # wait for the local server to answer (up to ~3s)
    for _ in range(30):
        try:
            with urllib.request.urlopen(url, timeout=0.3) as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(0.1)

    if not ensure_webview():
        print("⚠ pywebview not installed — falling back to browser app window")
        print("   fix:  python3 -m pip install --user pywebview")
        _loud_fail("TV DIABLO", "Native window engine missing (pywebview/WebView2). "
                   "Opening in your browser instead.\n\nFix: re-run the installer one-liner "
                   "from the website — it now bootstraps everything.\nLog: " + LOG_PATH)
        _open_browser_app_fallback(url)
        return

    import webview

    icon = None
    for cand in (
        os.path.join(HERE, "tv_diablo_icon.png"),
        os.path.join(REPO, "art", "diablo_icon.png"),
    ):
        if os.path.isfile(cand):
            icon = cand
            break

    kwargs = dict(
        title="TV DIABLO",
        url=url,
        width=1120,
        height=800,
        min_size=(880, 600),
        background_color="#070605",
        text_select=False,
        confirm_close=False,
        easy_drag=False,
    )
    # icon= supported on some backends; ignore if it errors
    try:
        if icon:
            globals()["_MAIN_WIN"] = webview.create_window(**kwargs, icon=icon)
        else:
            globals()["_MAIN_WIN"] = webview.create_window(**kwargs)
    except TypeError:
        globals()["_MAIN_WIN"] = webview.create_window(
            title="TV DIABLO",
            url=url,
            width=1120,
            height=800,
            min_size=(880, 600),
            background_color="#070605",
        )

    # v935.8 — window closed → stop ON AIR (events fire before webview.start returns on most backends)
    try:
        win = globals().get("_MAIN_WIN")
        if win is not None and hasattr(win, "events"):
            def _on_win_closed():
                _console_exit_stop_onair("window-closed")
            try:
                win.events.closed += _on_win_closed
            except Exception:
                try:
                    win.events.closing += lambda: _console_exit_stop_onair("window-closing")
                except Exception:
                    pass
    except Exception:
        pass

    # v928→v931 ONE SYSTEM (Konyo: "put it inside the console — better architecture") —
    # the tally/vault/chronicle engines live ONLY in bible.html JS. v928's second window
    # and v930's mini tile are DEAD: the engine is now an invisible same-origin iframe
    # (#tvd-eng) inside control_ui.html itself — one window, JS alive because the console
    # is visible. The control-side driver reaches its board through contentWindow.
    try:
        threading.Thread(target=_engine_driver, daemon=True, name="tvd-engine-driver").start()
        threading.Thread(target=_kai_closer_loop, daemon=True, name="tvd-kai-closer").start()
    except Exception as _ee:
        print(f"⚠ engine driver failed to start ({_ee}) — tallies need a board tab open", flush=True)

    # v928 — private_mode=False FOR REAL: the comment below claimed it since forever, but
    # the call never passed it. pywebview defaults to private (ephemeral) storage, so every
    # tally/grail state in the app board silently evaporated on quit.
    try:
        webview.start(debug=False, private_mode=False)
    except TypeError:
        # older pywebview without private_mode — ephemeral storage beats no window
        print("⚠ pywebview too old for private_mode=False — board storage is EPHEMERAL this run (tallies/grail reset on quit); pip install -U pywebview")
        try:
            webview.start(debug=False)
        except Exception as e:
            print(f"⚠ pywebview failed ({e}) — browser fallback")
            _open_browser_app_fallback(url)
    except Exception as e:
        print(f"⚠ pywebview failed ({e}) — browser fallback")
        _open_browser_app_fallback(url)
    # webview.start() returns when the user closes the window — always stop ON AIR
    _console_exit_stop_onair("webview-returned")


def _ejs(w, code, timeout=4.0):
    """v930 — evaluate_js with a hard timeout: pywebview's call BLOCKS FOREVER on a
    suspended/occluded WKWebView (live evidence: driver thread hung on its first probe).
    Runs the call in a scratch thread; timeout → None (treat as engine-not-responding)."""
    import queue as _q
    box = _q.Queue(maxsize=1)
    def _run():
        try:
            box.put(w.evaluate_js(code))
        except Exception as e:
            box.put(e)
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    try:
        r = box.get(timeout=timeout)
    except Exception:
        return None
    if isinstance(r, Exception):
        raise r
    return r


_KAI_STOP3 = frozenset(("the", "and", "for", "you", "are", "was", "not", "all", "any", "can",
                        "get", "has", "his", "her", "its", "our", "out", "off", "per", "via",
                        "new", "old", "one", "two", "six", "ten", "set", "use", "may", "now"))
_KAI_NOISE = ("stash", "inventory", "personal", "shared", "gems", "materials", "runes",
              "create game", "join game", "lobby", "chat", "options", "save and exit",
              "ctrl", "shift", "click", "left", "right", "move", "tab")


# v935 — KAI VOCAB GROUNDING: the closer's item-ish filter used to keep any alpha line, so
# OCR garble ("YwR PRIvATE STAS") landed in the miss ledger as if it were loot. The vocab is
# the item lexicon of the game itself — hardcoded runes/gems + every name token in bible.html.
_RUNE_NAMES = ("el", "eld", "tir", "nef", "eth", "ith", "tal", "ral", "ort", "thul", "amn",
               "sol", "shael", "dol", "hel", "io", "lum", "ko", "fal", "lem", "pul", "um",
               "mal", "ist", "gul", "vex", "ohm", "lo", "sur", "ber", "jah", "cham", "zod")
_GEM_WORDS = ("chipped", "flawed", "flawless", "perfect", "amethyst", "topaz", "sapphire",
              "emerald", "ruby", "diamond", "skull", "gem")


def _kai_add_name_tokens(vocab, full):
    """Tokenize a full item name into the vocab. Also strip Latent/Renewed so
    'Latent Black Cleft' grounds OCR of bare 'Black Cleft' (RotW sunder family)."""
    full = (full or "").strip()
    if not full:
        return
    bare = re.sub(r"^(Latent|Renewed)\s+", "", full, flags=re.I).strip()
    for name in {full, bare}:
        for tok in re.split(r"[^A-Za-z]+", name):
            if len(tok) >= 4 or (len(tok) == 3 and tok not in _KAI_STOP3):
                vocab.add(tok.lower())
            # 2-letter runes already seeded; don't flood with short junk


def _kai_fullnames():
    """v940.1 — full ITEM NAMES (lowercased) from the same bible literals the vocab uses.
    The judge's affix-scorer is for magic/rare; a grail unique scores 0 there and must
    NEVER be ruled a toss (live miscalibration: 'Hellfire Torch -> TOSS score 0')."""
    c = globals().get("_KAI_FULLNAMES")
    if c is not None:
        return c
    names = set()
    rare_combos = set()   # v943.2 — kept SEPARATE: recognized-but-not-grail-gated (see below)
    try:
        import re as _re
        with open(os.path.join(REPO, "bible.html"), encoding="utf-8", errors="replace") as _bf:
            src = _bf.read()
        pats = (r"(?<![A-Za-z0-9_])(?:name|n)\s*:\s*(['\"])(.*?)\1",          # name:'X' / n:'X'
                r"\"(?:name|n)\"\s*:\s*\"(.*?)\"",                            # JSON "name"/"n": "X"
                r"openDrop\(\s*(['\"])(.*?)\1",                                # v941.2 — RotW tiles (Ars Dul'Mephistos class)
                r"\"([A-Z][A-Za-z'\- ]{2,40})\"\s*:\s*[\[{]")                 # Title-Case JSON keys (drop-odds/grail seed)
        for pat in pats:
            for m in _re.finditer(pat, src):
                v = (m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)).strip()
                if 3 <= len(v) <= 48 and not any(ch in v for ch in "<>{}$"):
                    names.add(v.lower())
        # v943.1 — RotW RARE NAME SPACE. A rare item's name is one shared PREFIX word + one
        # slot SUFFIX word (RARE_NAME_PREFIXES × RARE_NAME_POOLS, from the game's
        # RarePrefix/RareSuffix tables): "Beast Noose" = Beast+Noose, "Plague Wing" = Plague+Wing.
        # The eye reads these BARE (no base word), so the curated EXTRA_ITEMS key
        # "Plague Wing Amulet" never matched a read of "Plague Wing". Harvest both pools and
        # generate the combo space — bounded (fixed pools, no user input), every entry a
        # valid two-word rare name so garble like "YwR PRIvATE STAS" can never ground.
        # v943.2 — these go into a SEPARATE set (rare_combos): the register/recognition path
        # wants them known, but the /kai_verdict GRAIL GATE must NOT auto-promote them — a rare
        # amulet CAN be a toss, and blanket-gating 1,254 rare names would gut the Checker's job.
        _mpre = _re.search(r"RARE_NAME_PREFIXES\s*=\s*\[(.*?)\]", src, _re.S)
        _mpool = _re.search(r"RARE_NAME_POOLS\s*=\s*\{(.*?)\}", src, _re.S)
        if _mpre and _mpool:
            _pref = _re.findall(r"'([A-Za-z][A-Za-z'\- ]{1,19})'", _mpre.group(1))
            _suf = _re.findall(r"'([A-Za-z][A-Za-z'\- ]{1,19})'", _mpool.group(1))
            for _p in _pref:
                for _s in _suf:
                    nm = (_p + " " + _s).strip()
                    if 3 <= len(nm) <= 48 and not any(ch in nm for ch in "<>{}$"):
                        rare_combos.add(nm.lower())
        # v943.3 — curated CRAFTED name pool (CRAFT_NAME_EXAMPLES: slot -> ['Bone Winding',
        # 'Brimstone Grip', …]). Same law as the rares: recognized for the register, but NON-
        # shielded — crafted items are exactly what the Checker judges, so they must stay
        # toss-able. Pull names from the array literals only (skip the slot-name keys).
        _mcraft = _re.search(r"CRAFT_NAME_EXAMPLES\s*=\s*\{(.*?)\}", src, _re.S)
        if _mcraft:
            for _arr in _re.findall(r"\[([^\]]*)\]", _mcraft.group(1)):
                for _nm in _re.findall(r"'([A-Za-z][A-Za-z'\- ]{1,30})'", _arr):
                    nm = _nm.strip()
                    if 3 <= len(nm) <= 48 and not any(ch in nm for ch in "<>{}$"):
                        rare_combos.add(nm.lower())
        names |= rare_combos   # full union still returned for register/recognition
    except Exception:
        pass
    globals()["_KAI_RARE_COMBOS"] = rare_combos
    globals()["_KAI_FULLNAMES"] = names
    return names


def _kai_rarenames():
    """v943.2 — the generated RotW rare-name combo space (RARE_NAME_PREFIXES × RARE_NAME_POOLS).
    Subset of _kai_fullnames(): recognized for the register/ledger, but EXCLUDED from the
    /kai_verdict grail gate so the judge may still toss a bad rare amulet/ring/jewel."""
    r = globals().get("_KAI_RARE_COMBOS")
    if r is None:
        _kai_fullnames()   # builds + caches both sets
        r = globals().get("_KAI_RARE_COMBOS") or set()
    return r


def _kai_vocab():
    """v935 — KAI's item lexicon (cached in a global, built once). Seeds the 33 classic rune
    names + gem words, then harvests alphabetic name tokens (len>=4) from every name:'…' /
    name:"…" literal in bible.html, lowercased and capped ~20k. Also buckets the set by token
    length for O(bucket) edit-distance-1 lookup. Errors swallowed — the rune/gem seed always
    survives so grounding never fully fails open even if bible.html can't be read.

    v939.1 (SuperGrok NIGHT2 open thread #1): also harvest openDrop('…') strings and
    Title-Case JSON object keys (drop-odds / grail seed) so RotW uniques that live as
    keys or onclick labels — Earth Shifter, Herald of Fright, Black Cleft — ground OCR."""
    v = globals().get("_KAI_VOCAB")
    if v is not None:
        return v
    vocab = set(_RUNE_NAMES) | set(_GEM_WORDS)
    try:
        with open(BIBLE, encoding="utf-8", errors="replace") as f:
            txt = f.read()
        # the real item DB (uniques/sets like 'Windforce') lives under the short n: / "n": keys,
        # not just name: — harvest both. The lookbehind stops the bare-n branch from matching the
        # 'n' inside words like min:/gen: (only a boundary or nothing may precede it).
        for pat in (r"""(?<![\w"])(?:name|n)\s*:\s*(['"])(.*?)\1""",
                    r""""(?:name|n)"\s*:\s*(['"])(.*?)\1"""):
            for m in re.finditer(pat, txt):
                _kai_add_name_tokens(vocab, m.group(2))
                if len(vocab) >= 20000:
                    break
            if len(vocab) >= 20000:
                break
        # openDrop('Herald of Fright') / openDrop("Earth Shifter") — RotW tiles + material cards
        if len(vocab) < 20000:
            for m in re.finditer(r"""openDrop\(\s*(['"])(.*?)\1""", txt):
                _kai_add_name_tokens(vocab, m.group(2))
                if len(vocab) >= 20000:
                    break
        # Title-Case JSON keys ("Earth Shifter": 16004764, "Latent Black Cleft": "Jun …")
        # Skip SCREAMING_CODES and single tokens that look like ids (UNI-ARMOR, hellTz).
        if len(vocab) < 20000:
            for m in re.finditer(r'"([A-Z][^"]{2,46})"\s*:', txt):
                key = m.group(1)
                if key.isupper() and " " not in key:
                    continue
                if re.fullmatch(r"[A-Za-z0-9_./+-]+", key) and " " not in key and len(key) < 6:
                    continue
                # must look like a game name: at least one space OR a long capitalised word
                if " " not in key and not re.match(r"^[A-Z][a-z]", key):
                    continue
                _kai_add_name_tokens(vocab, key)
                if len(vocab) >= 20000:
                    break
    except Exception:
        pass
    # never let a UI/noise word (stash, inventory, runes…) ground a loot line: bible.html
    # carries those as name literals too, and 'STAS' would fuzzy-match 'stash' otherwise.
    vocab.difference_update(_KAI_NOISE)
    by_len = {}
    for w in vocab:
        by_len.setdefault(len(w), set()).add(w)
    globals()["_KAI_VOCAB"] = vocab
    globals()["_KAI_VOCAB_BY_LEN"] = by_len
    return vocab


def _edit1(a, b):
    """True if a and b are within Levenshtein distance 1 (equal / one sub / one indel).
    Stdlib-only, short strings — used for fuzzy vocab grounding of noisy OCR tokens."""
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if a == b:
        return True
    if la == lb:                       # single substitution
        return sum(1 for x, y in zip(a, b) if x != y) == 1
    if la > lb:                        # make `a` the shorter — one insertion/deletion
        a, b, la, lb = b, a, lb, la
    i = j = diff = 0
    while i < la and j < lb:
        if a[i] == b[j]:
            i += 1
            j += 1
        else:
            diff += 1
            if diff > 1:
                return False
            j += 1
    return True


def _kai_vocab_hit(tok):
    """v935 — is this OCR token a known item word? Exact membership for any token (so 3-letter
    runes like 'ral'/'amn' pass), plus edit-distance-1 fuzzy against same-length±1 buckets for
    len>=4 (typo tolerance). Empty vocab → fail-open to the old keep-everything behaviour."""
    tok = tok.lower()
    vocab = _kai_vocab()
    if not vocab:
        return True
    if tok in vocab:
        return True
    # short tokens (<=4) are exact-only: at length 4 nearly every OCR garble sits one edit from
    # SOME real 4-letter word, so fuzzy there re-admits noise like 'STAS'. Typo tolerance is for
    # the longer names (len>=5) where an edit-1 neighbour is a real signal, not a coincidence.
    if len(tok) < 5:
        return False
    by_len = globals().get("_KAI_VOCAB_BY_LEN") or {}
    for L in (len(tok) - 1, len(tok), len(tok) + 1):
        for cand in by_len.get(L, ()):
            if _edit1(tok, cand):
                return True
    return False


def _kai_line_is_noise(lo):
    """v939.1 — noise must match as a WORD, not a substring.
    Substring noise killed real items: 'left'⊂cleft (Black Cleft), 'shift'⊂shifter
    (Earth Shifter), 'right'⊂fright (Herald of Fright). Multi-word phrases stay
    substring (they already have spaces: 'create game')."""
    import re as _re
    for n in _KAI_NOISE:
        if not n:
            continue
        if " " in n:
            if n in lo:
                return True
        else:
            if _re.search(r"(?<![a-z])" + _re.escape(n) + r"(?![a-z])", lo):
                return True
    return False


def _kai_itemish(s):
    """KAI v1 + v935 vocab grounding — keep item-ish OCR lines only when at least one token is
    a real game item word (exact, or one edit away for len>=4). Mirror of the agent's filter."""
    s = str(s or "").strip()
    lo = s.lower()
    if len(s) < 3:
        # v938.8 — bare 2-letter RUNE labels (El, Io…) are real; everything else short dies
        return len(s) == 2 and lo in _kai_vocab()
    if len(s) > 48:
        return False
    if _kai_line_is_noise(lo):
        return False
    # v938.8 — 'gold' left the noise list (it nuked Goldskin/Goldwrap/Goldstrike Arch):
    # gold PILES are killed by shape instead ("665 gold" / bare "gold").
    import re as _re
    if lo == "gold" or _re.fullmatch(r"\d[\d,\.]*\s*gold", lo):
        return False
    if sum(c.isdigit() for c in s) > max(3, len(s) // 2):
        return False
    # v938.8 — hyphens split like apostrophes (Trang-Oul, Amn-Sol, rune chains), and
    # 2-letter runes (El, Io…) may token (exact-membership still gates them).
    toks = [p for p in lo.replace("'", " ").replace("-", " ").split() if len(p) >= 2 and p.isalpha()]
    if not toks:
        return False
    return any(_kai_vocab_hit(p) for p in toks)


def _kai_frame_cls(lines, itemish):
    """v935.11 R5 — funnel routing metadata: what KIND of frame held the text, derived from the
    RAW OCR lines (lowercased). The KAI-v2 funnel escalates misses differently per class (a
    stash-panel miss = an owned-inventory reconcile; a tooltip miss = a ground/regret read).
      stash-runes|gems|materials|stash  a stash panel is open (personal/shared or plain 'stash');
                                        which tally tab word appears picks the sub-class.
      inventory                         the inventory panel is open.
      tooltip                           no panel word, but an item name floats (>=1 itemish line).
      gameplay                          otherwise — text with no item signal.
    """
    lo = [str(t).lower() for t in (lines or [])]
    blob = " ".join(lo)
    if "personal" in blob or "shared" in blob or "stash" in blob:
        if "runes" in blob:
            return "stash-runes"
        if "gems" in blob:
            return "stash-gems"
        if "materials" in blob:
            return "stash-materials"
        return "stash"
    if "inventory" in blob:
        return "inventory"
    if itemish:
        return "tooltip"
    return "gameplay"


# ── v943 AUTO-REGISTER stage 1 — THE REGISTER LEDGER ────────────────────────────
# Konyo's law: "it read it, it analyzed it → it's registered — why not." This is the
# EVIDENCE ledger only (what the eyes witnessed this session); the write-into-Chronicle
# arc with dedup law is a later bible-side stage. Nothing here touches board/grail/chronicle.
_REGISTER_ANCHORS = frozenset((
    "horadric cube", "wirt's leg", "wirts leg", "key", "tome",
))


def _register_is_junk(low):
    """Reuse the KAI word-boundary noise sense, plus gold-shape + potion/scroll consumables.
    Real DB grounding already gates most junk; this catches the always-carried filler."""
    if _kai_line_is_noise(low):
        return True
    if low == "gold" or re.fullmatch(r"\d[\d,\.]*\s*gold", low):
        return True
    for w in ("potion", "rejuvenation", "scroll"):
        if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low):
            return True
    return False


def _register_is_anchor(low):
    if low in _REGISTER_ANCHORS:
        return True
    return "tome of" in low   # Tome of Town Portal / Tome of Identify


def _kai_compile_register(sess_rows):
    """v943 — the session's REGISTERABLE ITEMS: union of every deep-read name and every
    KAI judge verdict tiered grail/keep/border, filtered to real DB items (_kai_fullnames)
    minus anchors + noise. One record per unique name, earliest sighting wins.
    Record: {name, firstSeenTs, frameId, loc, tier}. Pure — no side effects."""
    fulln = _kai_fullnames()
    reg = {}   # name.lower() -> record

    def _consider(name, ts, frame_id, loc, tier):
        nm = str(name or "").strip()
        if not nm:
            return
        low = nm.lower()
        if low not in fulln or _register_is_anchor(low) or _register_is_junk(low):
            return
        ts = int(ts or 0)
        cur = reg.get(low)
        if cur is None:
            reg[low] = {"name": nm, "firstSeenTs": ts, "frameId": frame_id or "",
                        "loc": loc, "tier": (tier or None)}
            return
        # earliest sighting wins the frame/ts/loc; a real tier fills a blank one.
        if ts and (not cur["firstSeenTs"] or ts < cur["firstSeenTs"]):
            cur["firstSeenTs"] = ts
            cur["frameId"] = frame_id or cur["frameId"]
            if loc is not None:
                cur["loc"] = loc
        if loc is not None and cur.get("loc") is None:
            cur["loc"] = loc
        if tier and not cur.get("tier"):
            cur["tier"] = tier

    for r in sess_rows:
        ts = int(r.get("ts") or r.get("captureTs") or 0)
        fid = str(r.get("frameId") or "")
        nl = r.get("names_loc") if isinstance(r.get("names_loc"), dict) else {}
        if r.get("lane") == "deep":
            for nm in (r.get("names") or []):
                _consider(nm, ts, fid, nl.get(nm), None)
        if r.get("lane") == "kai":
            k = r.get("kai")
            j = k.get("judge") if isinstance(k, dict) else None
            if isinstance(j, dict):
                tier = str(j.get("tier") or "").lower()
                if tier in ("grail", "keep", "border"):
                    _consider(j.get("name"), ts, fid, nl.get(j.get("name")), tier)
    return sorted(reg.values(), key=lambda x: (x["firstSeenTs"] or 0, x["name"].lower()))


# ── v944/v944.1 🚦 THE KAI ROUTER
# Stage 1 — LABEL TABLE (evidence): per-frame votes + route intent + what actually fired.
# Stage 2 — QUORUM GATE (v944.1): sources that AGREE on the final label only count;
#           confidence = agreement count; <2 → no route (🟡); multi-brain disagreement
#           without a ≥2 winner → skipReason "disagreement".
# Stage 3 — lanes OBEY the ledger (still next: funnel/judge as consumers of routed rows).
def _kai_frame_sig(path):
    """v944 — cheap sampled-bytes fingerprint of a reel JPEG for routing dedupe (frame_sig-style).
    Returns (size, ~2k sampled bytes): the size is the fast first-pass key, the samples confirm
    identity. stdlib only, defensive (None on any error → that frame never dedupe-chains)."""
    try:
        sz = os.path.getsize(path)
        with open(path, "rb") as _f:
            data = _f.read()
        step = max(1, len(data) // 2048)
        return (sz, bytes(data[::step][:2048]))
    except Exception:
        return None


# v944.2 Stage 2 hardening — QUORUM SOURCE INDEPENDENCE. Confidence must count independent
# EVIDENCE CLASSES, not raw votes: 'read' (a deep read named an item on this frame) and 'judge'
# (a verdict on THAT SAME item) are one tooltip witnessed twice, not two brains agreeing. A
# tooltip read-then-judged is one 'content' signal; it clears the ≥2 gate only when a genuinely
# independent brain (pixel OCR / time-map journal) also lands on it.
_ROUTER_INDEP_CLASS = {"ocr": "pixel", "journal": "time", "read": "content", "judge": "content"}


def _router_conf(sources):
    """Independent-class confidence: distinct evidence classes among the agreeing brains."""
    return len({_ROUTER_INDEP_CLASS.get(b, b) for b in (sources or [])})


def _kai_route_for_label(label):
    """Which funnel WOULD take a frame with this label (route intent, not a fire)."""
    if label in ("stash-runes", "stash-gems", "stash-materials"):
        return "tally:" + label[len("stash-"):]
    if label == "tooltip":
        return "judge"
    if label in ("stash", "inventory"):
        return "vault"
    return None


def _kai_quorum_label(votes):
    """v944.1 Stage 2 — pick the final label from per-brain votes + who agrees.

    votes: dict brain → label (omit silent brains). Policy (stash screens are OCR-dark):
      1) journal stash-* / stash always wins when present (time-map is ground truth for panels)
      2) else majority vote among non-gameplay labels
      3) else any single non-gameplay vote
      4) else gameplay
    Returns (label, sources_list, skip_disagreement_or_None).
    sources_list = brains whose vote equals the chosen label (honest quorum).
    skip_disagreement = 'disagreement' when ≥2 distinct non-gameplay labels and no ≥2 winner.
    """
    # drop empties / normalize
    clean = {b: (lb or "gameplay") for b, lb in (votes or {}).items() if b and lb}
    if not clean:
        return "gameplay", [], None
    # 1) journal panel truth
    jv = clean.get("journal")
    if jv and jv != "gameplay" and (jv == "stash" or str(jv).startswith("stash-")):
        agree = sorted(b for b, lb in clean.items() if lb == jv)
        return jv, agree, None
    # tally non-gameplay votes
    from collections import Counter
    ng = {b: lb for b, lb in clean.items() if lb != "gameplay"}
    if not ng:
        agree = sorted(clean.keys())  # all said gameplay
        return "gameplay", agree, None
    counts = Counter(ng.values())
    top_label, top_n = counts.most_common(1)[0]
    # disagreement: 2+ distinct non-gameplay labels and no quorum on the winner
    if len(counts) >= 2 and top_n < 2:
        # no ≥2 agreement — flag, keep top as display label, sources empty for gate
        return top_label, [], "disagreement"
    agree = sorted(b for b, lb in clean.items() if lb == top_label)
    return top_label, agree, None


def _kai_build_routing(scan, sess_rows, sid, journal_rows):
    """v944/v944.1 — THE ROUTING LEDGER. One row per scanned frame:
    {f, ts, label, sources, confidence, route, routed, skipReason}.

    sources = brains whose VOTE equals the final label (Stage 2 honest quorum), not merely
    'any evidence on the frame'. Brains:
      'ocr'     OCR classed the frame (non-gameplay cls),
      'journal' stash time-map placed the frame on an open tab,
      'read'    a deep read named an item within ±4s → votes tooltip,
      'judge'   a judge verdict landed on this frame → votes tooltip.

    confidence = len(sources). Stage 2 gate: confidence < 2 → no fire intent (skip confidence<2
    or disagreement). route = funnel that WOULD take it; routed = what actually fired (receipts).
    Pure — no side effects."""
    read_ts = [int(r.get("captureTs") or r.get("ts") or 0)
               for r in sess_rows
               if r.get("lane") == "deep" and (r.get("names") or [])]
    receipted = set()   # tabs that receipted normally this session (tally route + receipt = no gap)
    for r in sess_rows:
        ik = r.get("intake")
        if isinstance(ik, dict) and ik.get("ok", True):
            t = str(ik.get("tab") or "").lower()
            if t:
                receipted.add(t)
    funnel_by_fid = {}   # reel frameId -> intake kind the funnel wrote
    judge_fids = set()   # reel frameIds a judge verdict landed on
    for r in journal_rows:
        fid = str(r.get("frameId") or "")
        if not fid:
            continue
        ik = r.get("intake")
        if isinstance(ik, dict) and str(ik.get("kind") or "") == "kai-funnel":
            funnel_by_fid[fid] = "kai-funnel"
        if r.get("lane") == "kai" and r.get("mode") == "kai-judge":
            judge_fids.add(fid)
    out = []
    _prev_sig = None
    _run_first = None   # the f that opened the current visual run
    for s in scan:
        f = str(s.get("f") or "")
        ts = int(s.get("ts") or 0)
        fid = ("reel_" + sid + "/" + f.replace(".jpg", "")) if f else ""
        # ── per-brain VOTES (Stage 2) ──
        votes = {}
        ocr_lb = s.get("ocrLabel") or (s.get("label") if s.get("ocr") else None)
        if s.get("ocr") and ocr_lb and ocr_lb != "gameplay":
            votes["ocr"] = ocr_lb
        j_lb = s.get("journalLabel")
        if s.get("journal"):
            votes["journal"] = j_lb or s.get("label") or "stash"
        if any(abs(rt - ts) <= 4000 for rt in read_ts):
            votes["read"] = "tooltip"   # a named deep read near this frame ⇒ item floating
        judged = fid in judge_fids
        if judged:
            votes["judge"] = "tooltip"
        # legacy scan rows without ocrLabel/journalLabel still work via booleans + label
        if not votes and (s.get("ocr") or s.get("journal")):
            if s.get("ocr"):
                votes["ocr"] = s.get("label") or "gameplay"
            if s.get("journal"):
                votes["journal"] = s.get("label") or "stash"
        label, sources, disagree = _kai_quorum_label(votes)
        conf = _router_conf(sources)   # v944.2 — independent evidence classes, not raw votes
        route = _kai_route_for_label(label)
        routed = funnel_by_fid.get(fid) or ("kai-judge" if judged else None)
        skip = None
        # Stage 2 gate — no fire intent without quorum (even if a receipt already exists,
        # skipReason stays null when routed is set; the gate applies to would-fire path)
        if routed is None:
            if disagree:
                skip = "disagreement"
                route = None   # do not advertise a route when brains fight
            elif conf < 2:
                skip = "confidence<2"
                # keep route for drilldown (what WOULD fire if a second brain agreed)
            elif route is None:
                skip = "no-route"
            elif route.startswith("tally:"):
                skip = "no-gap" if route.split(":", 1)[1] in receipted else "not-selected"
            elif route == "judge":
                skip = "cap"
            elif route == "vault":
                skip = "no-vault-fire"
            else:
                skip = "no-route"
        # v944 DEDUPE LAW (routing-only, Konyo explicit) — consecutive frames with an identical
        # cheap signature are a visual run: the FIRST keeps its label+route, each later duplicate
        # keeps its label but is un-routed with a chain ref. The reel/film is NEVER trimmed —
        # every frame stays in the ledger, so the replay is complete.
        _sig = s.get("sig")
        _is_dup = _sig is not None and _sig == _prev_sig
        if _is_dup:
            route = None
            routed = None
            skip = "dup-of:" + (_run_first or "")
        else:
            _run_first = f
        _prev_sig = _sig
        out.append({"f": f, "ts": ts, "label": label, "sources": sources,
                    "confidence": conf, "voteCount": len(sources), "route": route,
                    "routed": routed, "skipReason": skip})
    return out


def _kai_closer_loop():
    """v934 — 🧠 KAI THE CLOSER (layer 3, v1). After a session seals, walk its ENTIRE reel
    with the local OCR worker (no time pressure, nice'd), diff every frame's item-ish text
    against what the session's reads actually caught, and journal a `lane: kai` ledger:
    the frames whose text NO eye read — the ground truth of what was missed. v2 escalates
    misses into deep reads + auto-register + the mule/throw-out regret funnel."""
    if os.environ.get("TV_KAI", "1") == "0":
        return
    ocr_bin = os.path.join(HERE, "bin", "ocr_mac")
    if not (os.path.isfile(ocr_bin) and os.access(ocr_bin, os.X_OK)):
        return
    time.sleep(20.0)
    hist = HIST_DIR
    while True:
        try:
            time.sleep(30.0)
            if not os.path.isdir(hist):
                continue
            # v937.3 (Grok gate #1/#2) — KAI works ONLY between sessions: closing a reel
            # while a NEW session is ON AIR races the funnel's SET wrapper against the live
            # store and fights the game for CPU. Reels wait; they aren't going anywhere.
            if _agent_mode != "off" or _agent_alive():
                continue
            reels = sorted(d for d in os.listdir(hist)
                           if d.startswith("reel_") and os.path.isdir(os.path.join(hist, d))
                           and os.path.isfile(os.path.join(hist, d, "index.json"))
                           and not os.path.isfile(os.path.join(hist, d, "kai_report.json")))
            if not reels:
                continue
            rd = os.path.join(hist, reels[0])
            sid = reels[0][len("reel_"):]
            frames = []
            try:
                with open(os.path.join(rd, "index.json"), encoding="utf-8") as f:
                    frames = (json.load(f) or {}).get("frames") or []
            except Exception:
                pass
            # what the session's eyes actually read (deep + ocr + verify lanes)
            read_text = set()
            try:
                sess_rows = [r for r in _kai_journal_rows() if r.get("sessionId") == sid]
            except Exception:
                sess_rows = []
            for r in sess_rows:
                for nm in (r.get("names") or []) + (r.get("ocr_names") or []):
                    read_text.add(str(nm).strip().lower())
            # v941.3 — STASH TIME-MAP: stash screens are OCR-dark (icon grids, ornate tab
            # labels Vision can't read at footage res — run-3 proof: OCR [] on runes-tab
            # frames). The JOURNAL knows when each tab was open; frames inherit the class.
            stash_times = []
            for r in sess_rows:
                if r.get("lane") == "deep" and str(r.get("scene") or "") == "stash":
                    tb = str(r.get("stashTab") or "").lower()
                    if tb:
                        stash_times.append((int(r.get("captureTs") or r.get("ts") or 0), tb))
            print(f"🧠 KAI: closing {sid} — {len(frames)} frames, {len(read_text)} known texts", flush=True)
            # OCR worker: one warm process, stdin path → stdout JSON line
            import queue as _q
            try:
                wp = subprocess.Popen([ocr_bin, "--worker"], stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, text=True, bufsize=1,
                                      preexec_fn=(lambda: os.nice(15)) if not IS_WIN else None)
            except Exception as e:
                print(f"🧠 KAI: worker spawn failed ({e}) — skipping reel"); continue
            missed = []
            classes = {}
            class_frames = {}          # v935.11 R5 — {cls: count} over every line-producing frame
            routing_scan = []          # v944 🚦 — per-scanned-frame label evidence (routing ledger)
            scanned = textframes = 0
            for it in frames:
                fp = os.path.join(rd, it.get("f") or "")
                if not os.path.isfile(fp):
                    continue
                try:
                    wp.stdin.write(fp + "\n"); wp.stdin.flush()
                    line = wp.stdout.readline()
                    j = json.loads(line) if line else {}
                except Exception:
                    break
                scanned += 1
                raw = j.get("lines") or []
                texts = [t for t in raw if _kai_itemish(t)]
                # R5 — classify every frame that produced OCR lines, before the missed decision.
                _ocr_cls = _kai_frame_cls(raw, texts) if raw else None   # v944 — OCR's own verdict
                cls = _ocr_cls
                # v941.3 — journal-truth override: a frame within ±4s of a stash-tab read IS
                # that stash screen, whatever OCR saw (or didn't).
                _fts5 = int(it.get("ts") or 0)
                _near = next((tb for (st5, tb) in stash_times if abs(st5 - _fts5) <= 4000), None)
                if _near:
                    _scls = ("stash-" + _near) if _near in ("runes", "gems", "materials") else "stash"
                    class_frames[_scls] = {"f": it.get("f"), "ts": it.get("ts")}   # funnel candidate regardless
                    if not cls or cls == "gameplay":
                        cls = _scls
                if cls:
                    classes[cls] = classes.get(cls, 0) + 1
                    class_frames[cls] = {"f": it.get("f"), "ts": it.get("ts")}   # v940.1 — last frame per class
                if texts:
                    textframes += 1
                    new = [t for t in texts if t.strip().lower() not in read_text]
                    if new:
                        missed.append({"f": it.get("f"), "ts": it.get("ts"),
                                       "texts": new[:6], "cls": cls})
                # v944/v944.1 🚦 — per-brain label VOTES for Stage 2 quorum (not just booleans).
                # ocrLabel = OCR's own class; journalLabel = stash time-map class; final
                # 'label' is still the display override (journal wins on panels).
                _jlab = None
                if _near:
                    _jlab = ("stash-" + _near) if _near in ("runes", "gems", "materials") else "stash"
                routing_scan.append({"f": it.get("f"), "ts": int(it.get("ts") or 0),
                                     "ocr": bool(_ocr_cls and _ocr_cls != "gameplay"),
                                     "ocrLabel": _ocr_cls if (_ocr_cls and _ocr_cls != "gameplay") else None,
                                     "journal": bool(_near),
                                     "journalLabel": _jlab,
                                     "label": cls or "gameplay",
                                     "sig": _kai_frame_sig(fp)})   # v944 — dedupe fingerprint
                time.sleep(0.12)   # peaceful — never fights a live session
            try:
                wp.stdin.close(); wp.terminate()
            except Exception:
                pass
            report = {"sid": sid, "scanned": scanned, "textFrames": textframes,
                      "classFrames": class_frames,
                      "missedFrames": len(missed), "missed": missed[:40],
                      "classes": classes,   # R5 — routing metadata for the KAI-v2 funnel
                      "closedAt": int(time.time() * 1000), "kaiVer": 1}
            with open(os.path.join(rd, "kai_report.json"), "w", encoding="utf-8") as f:
                json.dump(report, f)
            # journal the ledger onto the session's timeline (🧠 gold in SIM).
            # v934.1 — GHOST-PROOF: split_sessions sorts by ts and cuts on sid change, so
            # ts=now rows appended after newer sessions would spawn a ghost block (the
            # bak_ghost_purge class). Journal law is ts == captureTs: misses land AT their
            # frame's true moment inside the session span; the summary lands at seal+1ms.
            now_ms = int(time.time() * 1000)
            _sess_last = max((int(r.get("ts") or 0) for r in sess_rows), default=now_ms)
            rows = []
            for m in missed[:20]:
                _fts = int(m.get("ts") or _sess_last)
                rows.append({"ts": _fts, "captureTs": _fts,
                             "completedTs": now_ms, "lane": "kai", "mode": "kai",
                             "scene": "kai", "names": [], "sessionId": sid,
                             "frameId": "reel_" + sid + "/" + str(m.get("f") or "").replace(".jpg", ""),
                             "kai": {"texts": m.get("texts") or [], "cls": m.get("cls")},
                             "note": "🧠 unread text: " + ", ".join((m.get("texts") or [])[:3])})
            rows.append({"ts": _sess_last + 1, "captureTs": _sess_last + 1, "completedTs": now_ms,
                         "lane": "kai", "mode": "kai", "scene": "kai", "names": [],
                         "sessionId": sid, "frameId": "",
                         "kai": {**{k: report[k] for k in ("scanned", "textFrames", "missedFrames")},
                                 "classes": classes},
                         "note": f"🧠 KAI closed the session — {scanned} frames swept · "
                                 f"{len(missed)} frames held text no eye read"})
            try:
                with open(os.path.join(HERE, "sessions.jsonl"), "a", encoding="utf-8") as f:
                    for r in rows:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"🧠 KAI: journal append failed ({e})", flush=True)
            print(f"🧠 KAI report sealed for {sid}: {scanned} swept, {len(missed)} missed-text frames", flush=True)
            # v935 — 🚨 WATCHDOG rides the same reel-close moment (sess_rows already loaded)
            try:
                _watchdog_check(sid, sess_rows)

                # ── v937 📸 KAI FUNNEL slice 1 (Konyo's architecture: frames chauffeured through the
                # LOCKED readers). For each tally tab the session VISITED but never receipted, feed the
                # session's LAST archived frame of that tab class through the matching locked intake —
                # with the SET wrapper (snapshot→subtract for reported keys) so whole-stash photos can
                # never double-count on top of the store. One shot per tab, serialized, journal-confirmed.
                try:
                    _visited = set()
                    _receipted = set()
                    for r2 in sess_rows:
                        if r2.get("lane") == "deep":
                            t2 = str(r2.get("stashTab") or "").lower()
                            if t2 in ("runes", "gems", "materials"):
                                _visited.add(t2)
                        ik2 = r2.get("intake")
                        if isinstance(ik2, dict) and ik2.get("ok", True) and str(ik2.get("tab") or "").lower():
                            _receipted.add(str(ik2.get("tab") or "").lower())   # v938.3 — ok:false ≠ receipted
                    _gaps = [t for t in ("runes", "gems", "materials") if t in _visited and t not in _receipted]
                    _by_tab = {}
                    for mrec in missed:
                        c2 = str(mrec.get("cls") or "")
                        if c2.startswith("stash-") and c2[6:] in _gaps:
                            _by_tab[c2[6:]] = mrec   # last wins = most recent view of that tab
                    for t9 in _gaps:
                        # v940.1 FALLBACK (live gap: runes text was READ so never 'missed' —
                        # funnel had no photo): use the reel's last frame OF THAT CLASS.
                        if t9 not in _by_tab and class_frames.get("stash-" + t9):
                            _by_tab[t9] = class_frames["stash-" + t9]
                    w2 = globals().get("_MAIN_WIN")
                    for t3, mrec in _by_tab.items():
                        if w2 is None or os.environ.get("TV_KAI_FUNNEL", "1") == "0":
                            break
                        _histp = "/hist/reel_" + sid + "/" + str(mrec.get("f") or "")
                        _fid3 = "reel_" + sid + "/" + str(mrec.get("f") or "").replace(".jpg", "")
                        _js = ("(function(){try{var F=document.getElementById('tvd-eng');if(!F||!F.contentWindow)return 0;var W=F.contentWindow;"
                               "if(W._stashShutter)return 2;var FN={runes:'runeIntake',gems:'gemIntake',materials:'materialIntake'}[%s];if(typeof W[FN]!=='function')return 0;"
                               "var LSK={runes:'d2r_runeStash',gems:'d2r_gemStash',materials:'d2r_materialStash'}[%s];"
                               "var ADJ={runes:'adjustRuneStash',gems:'adjustGemStash',materials:'adjustMaterialStash'}[%s];"
                               "var prev={};try{var st0=JSON.parse(W.LSR.getItem(LSK)||'{}');Object.keys(st0).forEach(function(k){prev[k]=parseInt(st0[k],10)||0})}catch(e){}"
                               "fetch(%s+'?'+Date.now()).then(function(r){if(!r.ok)throw 0;return r.blob()}).then(function(b){"
                               "return W[FN]([new W.File([b],'kai-funnel.jpg',{type:'image/jpeg'})])}).then(function(res){"
                               "try{if(res&&res.ok){Object.keys(res.added||{}).forEach(function(k){var was=prev[k]||0;if(was>0&&typeof W[ADJ]==='function')W[ADJ](k,-was)})}}catch(e){}"
                               "try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'kai-funnel',ok:!!(res&&res.ok),counts:(res&&res.added)||{},total:(res&&res.total)||0,errors:(res&&res.errors)||0,frameId:%s})}).catch(function(){})}catch(e){}"
                               "}).catch(function(){});return 1}catch(e){return 0}})()") % (json.dumps(t3), json.dumps(t3), json.dumps(t3), json.dumps(_histp), json.dumps(t3), json.dumps(_fid3))
                        try:
                            _ejs(w2, _js, timeout=5.0)
                            print(f"📸 KAI funnel: fired {t3} from archived frame {mrec.get('f')}", flush=True)
                        except Exception as _fe:
                            print(f"⚠ KAI funnel fire failed ({t3}): {_fe}", flush=True)
                            continue
                        _t0f = time.time()
                        while time.time() - _t0f < 120.0:
                            time.sleep(6.0)
                            try:
                                if any(r3.get("lane") == "intake" and (r3.get("intake") or {}).get("kind") == "kai-funnel"
                                       and (r3.get("intake") or {}).get("tab") == t3
                                       and int(r3.get("completedTs") or 0) >= int(_t0f * 1000)
                                       for r3 in _kai_journal_rows()[-40:]):
                                    print(f"📸 KAI funnel: {t3} receipt journaled ✓", flush=True)
                                    # v937.5 — the funnel RESOLVES the watchdog's flag it just filled
                                    try:
                                        _res = {"ts": _sess_last + 40, "captureTs": _sess_last + 40,
                                                "completedTs": int(time.time() * 1000), "lane": "watchdog",
                                                "mode": "watchdog", "scene": "watchdog", "names": [],
                                                "sessionId": sid, "frameId": "",
                                                "watchdog": {"rule": "resolved-by-kai-funnel", "tab": t3},
                                                "note": f"✅ WATCHDOG resolved — KAI funnel receipted {t3} from the reel"}
                                        with open(os.path.join(HERE, "sessions.jsonl"), "a", encoding="utf-8") as _rf:
                                            _rf.write(json.dumps(_res, ensure_ascii=False) + "\n")
                                        _wl = globals().get("_WATCHDOG_LAST")
                                        if isinstance(_wl, dict) and _wl.get("sid") == sid and _wl.get("violations"):
                                            _wl["violations"] = max(0, int(_wl["violations"]) - 1)
                                    except Exception:
                                        pass
                                    break
                            except Exception:
                                pass
                    # ── v940 🔬 TOOLTIP LANE: missed frames classed 'tooltip' go to the headless
                    # Item Checker (aicJudge) — cap 4/session, fire-and-forget, receipts land on
                    # /kai_verdict with the frame's own timestamp (ghost-proof).
                    try:
                        _jcap = max(0, int(os.environ.get("TV_KAI_JUDGE_MAX", "12")))
                    except Exception:
                        _jcap = 12
                    _tips = [m4 for m4 in missed if str(m4.get("cls") or "") == "tooltip"][:_jcap]   # v941.2 — KAI has all night (was 4; 19 tooltips captured last run)
                    for m4 in _tips:
                        if w2 is None or os.environ.get("TV_KAI_JUDGE", "1") == "0":
                            break
                        _hp4 = "/hist/reel_" + sid + "/" + str(m4.get("f") or "")
                        _fid4 = "reel_" + sid + "/" + str(m4.get("f") or "").replace(".jpg", "")
                        _fts4 = int(m4.get("ts") or 0)
                        _js4 = ("(function(){try{var F=document.getElementById('tvd-eng');if(!F||!F.contentWindow)return 0;var W=F.contentWindow;"
                                "if(typeof W.aicJudge!=='function')return 0;"
                                "fetch(%s+'?'+Date.now()).then(function(r){if(!r.ok)throw 0;return r.blob()}).then(function(b){"
                                "return W.aicJudge(new W.File([b],'kai-judge.jpg',{type:'image/jpeg'}))}).then(function(res){"
                                "res=res||{};res.sid=%s;res.frameId=%s;res.fts=%s;"
                                "fetch('/kai_verdict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(res)}).catch(function(){})"
                                "}).catch(function(){});return 1}catch(e){return 0}})()"
                                ) % (json.dumps(_hp4), json.dumps(sid), json.dumps(_fid4), json.dumps(_fts4))
                        try:
                            _ejs(w2, _js4, timeout=5.0)
                            print(f"🔬 KAI judge: fired on {m4.get('f')}", flush=True)
                            time.sleep(20.0)   # gentle pacing — the judge is a full vision read
                        except Exception as _je:
                            print(f"⚠ KAI judge fire failed: {_je}", flush=True)
                except Exception as _kfe:
                    print(f"⚠ KAI funnel stage error: {_kfe}", flush=True)

                # ── v943 📖 THE REGISTER LEDGER — after watchdog/funnel/judge, compile what the
                # session WITNESSED. Re-read the journal so the judge verdicts that posted during
                # the tooltip stage are counted. Evidence only — no board/grail/chronicle writes.
                try:
                    _reg_rows = [r for r in _kai_journal_rows() if r.get("sessionId") == sid]
                    _register = _kai_compile_register(_reg_rows)
                    report["register"] = _register
                    # v944 🚦 — the ROUTING LEDGER rides the same re-read (funnel/judge receipts
                    # are now in the journal, so 'routed' is truthful). Evidence only — no firing.
                    _routing = _kai_build_routing(routing_scan, sess_rows, sid, _reg_rows)
                    report["routing"] = _routing
                    _rcounts = {}
                    for _rr in _routing:
                        _rcounts[_rr["label"]] = _rcounts.get(_rr["label"], 0) + 1
                    _routed_n = sum(1 for _rr in _routing if _rr.get("routed"))
                    try:
                        with open(os.path.join(rd, "kai_report.json"), "w", encoding="utf-8") as _rf2:
                            json.dump(report, _rf2)
                    except Exception:
                        pass
                    _reg_row = {"ts": _sess_last + 60, "captureTs": _sess_last + 60,
                                "completedTs": int(time.time() * 1000),
                                "lane": "kai", "mode": "kai", "scene": "kai", "names": [],
                                "sessionId": sid, "frameId": "",
                                "kai": {"register": {"count": len(_register),
                                                     "items": _register[:40]},
                                        "routing": {"counts": _rcounts, "routedCount": _routed_n}},
                                "note": f"📖 KAI register ledger — {len(_register)} items witnessed · "
                                        f"🚦 {len(_routing)} frames routed-labelled ({_routed_n} fired)"}
                    with open(os.path.join(HERE, "sessions.jsonl"), "a", encoding="utf-8") as _rf3:
                        _rf3.write(json.dumps(_reg_row, ensure_ascii=False) + "\n")
                    print(f"📖 KAI register: {len(_register)} witnessed · 🚦 routing: {len(_routing)} frames, "
                          f"{_routed_n} fired in {sid}", flush=True)
                except Exception as _rge:
                    print(f"⚠ KAI register/routing stage error: {_rge}", flush=True)
            except Exception as _we:
                print(f"🚨 watchdog: check raised ({_we})", flush=True)
        except Exception:
            time.sleep(10.0)


def _kai_journal_rows():
    """Fresh journal rows for KAI (module-level read; the handler cache is instance-side)."""
    rows = []
    try:
        with open(os.path.join(HERE, "sessions.jsonl"), encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    try:
                        rows.append(json.loads(ln))
                    except Exception:
                        pass
    except Exception:
        pass
    return rows


def _watchdog_check(sid, sess_rows):
    """v935 — 🚨 WATCHDOG v1 (Konyo: 'hardcoded Diablo II safeguards — expected vs happened').
    After a reel seals, assert the session's ground truths and journal a lane:'watchdog' row for
    every breach. GHOST-PROOF like the KAI rows: ts == captureTs, anchored just past the session's
    last row so violations land INSIDE the session span (split_sessions cuts on sid change + ts).
    Rules:
      1) tally-tab-visited-needs-receipt — a tally tab (runes/gems/materials) seen as stashTab on a
         deep read, but NO intake receipt (row with intake.tab == that tab) landed this session.
      2) stash-open-no-tab-reads — a deep read had scene=='stash', yet not one row carried a
         non-empty stashTab (the stash opened but no tab was ever actually read)."""
    rows = sess_rows or []
    now_ms = int(time.time() * 1000)
    _sess_last = max((int(r.get("ts") or 0) for r in rows), default=now_ms)

    visited = set()
    for r in rows:
        if r.get("lane") == "deep":
            tab = str(r.get("stashTab") or "").lower()
            if tab in ("runes", "gems", "materials"):
                visited.add(tab)
    receipts = set()
    for r in rows:
        ik = r.get("intake")
        if isinstance(ik, dict) and ik.get("ok", True):   # v938.3 — a FAILED shot satisfies nothing
            rt = str(ik.get("tab") or "").lower()
            if rt:
                receipts.add(rt)

    violations = []
    for tab in ("runes", "gems", "materials"):
        if tab in visited and tab not in receipts:
            violations.append({
                "rule": "tally-tab-visited-needs-receipt", "tab": tab,
                "note": "🚨 WATCHDOG: %s tab was visited but NO tally receipt landed" % tab})

    stash_opened = any(r.get("lane") == "deep" and str(r.get("scene") or "") == "stash"
                       for r in rows)
    any_tab_read = any(str(r.get("stashTab") or "").strip() for r in rows)
    # v936.2 — rule 3: TEXT-EYE LIVENESS. A busy session (>=6 deep reads) with ZERO
    # text-eye trigger beats means the tooltip lane was dead the whole run — the
    # "20 items shown, 4 reads" class regressing silently. (Trigger beats journal as
    # kind:skip why:'text-eye' since v936.1.)
    _deep_n = sum(1 for r in rows if r.get("lane") == "deep")
    _te_n = sum(1 for r in rows
                if str(r.get("why") or r.get("skip") or "") == "text-eye"
                or "text-eye" in str(r.get("note") or ""))
    _deep_named = any(r.get("lane") == "deep" and (r.get("names") or []) for r in rows)
    if _deep_n >= 6 and _deep_named and _te_n == 0:
        violations.append({
            "rule": "text-eye-silent-all-session", "tab": "",
            "note": "🚨 WATCHDOG: %d reads but the text eye never triggered once — tooltip lane may be dead" % _deep_n})
    if stash_opened and not any_tab_read:
        violations.append({
            "rule": "stash-open-no-tab-reads", "tab": "",
            "note": "🚨 WATCHDOG: stash was opened but no stash tab was ever read"})

    out_rows = []
    for i, v in enumerate(violations):
        _ts = _sess_last + 2 + i
        out_rows.append({"ts": _ts, "captureTs": _ts, "completedTs": now_ms,
                         "lane": "watchdog", "mode": "watchdog", "scene": "watchdog",
                         "names": [], "sessionId": sid, "frameId": "",
                         "watchdog": {"rule": v["rule"], "tab": v["tab"]},
                         "note": v["note"]})
    if out_rows:
        try:
            with open(os.path.join(HERE, "sessions.jsonl"), "a", encoding="utf-8") as f:
                for r in out_rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"🚨 watchdog: journal append failed ({e})", flush=True)

    globals()["_WATCHDOG_LAST"] = {"sid": sid, "violations": len(out_rows)}
    if out_rows:
        print(f"🚨 watchdog: {len(out_rows)} violation(s) for {sid}", flush=True)
    else:
        print(f"🛡 watchdog: clean session {sid}", flush=True)
    return out_rows


# ── v943.4 ENGINE SELF-HEALING (Grok's engine-liveness deferral) ────────────────
# The off-screen engine iframe can wedge (WKWebView occlusion, a JS fault) so every
# liveness probe comes back dead. Rather than sit dark forever, count consecutive dead
# probes and, at the threshold, kick the iframe by re-assigning its own src (a cheap
# reload). Give up loudly after a few tries so a truly dead engine is visible, not looped.
_ENGINE_REVIVE_AT = 5     # consecutive dead probes before a revive attempt
_ENGINE_REVIVE_MAX = 3    # revive attempts per process before declaring hard-dead


def _engine_selfheal(alive, w):
    """Pure counter transition for engine self-healing. A live probe clears the streak;
    a dead one (probe non-1/2 or _ejs None) advances it. At _ENGINE_REVIVE_AT consecutive
    dead probes: revive the iframe once (src=src) and drop the counter to a half-way value
    so a dead revive re-arms after a settle gap, not on the very next loop. After
    _ENGINE_REVIVE_MAX revives: set _ENGINE_DEAD_HARD once and shout to restart the app.
    Testable with w=None (skips the JS kick, keeps the counter/flag logic)."""
    if alive:
        globals()["_ENG_FAILS"] = 0
        return
    fails = globals().get("_ENG_FAILS", 0) + 1
    globals()["_ENG_FAILS"] = fails
    if fails < _ENGINE_REVIVE_AT:
        return
    revives = globals().get("_ENG_REVIVES", 0)
    if revives < _ENGINE_REVIVE_MAX:
        globals()["_ENG_REVIVES"] = revives + 1
        if w is not None:
            try:
                _ejs(w, "(function(){var f=document.getElementById('tvd-eng'); "
                        "if(f){f.src=f.src;return 1} return 0})()", timeout=3.0)
            except Exception:
                pass
        print("🔌 engine revive attempted", flush=True)
        globals()["_ENG_FAILS"] = _ENGINE_REVIVE_AT // 2   # half-way — settle before re-arming
        globals()["_EJS_STUCK"] = 0                         # let the next loop actually re-probe
    elif not globals().get("_ENGINE_DEAD_HARD"):
        globals()["_ENGINE_DEAD_HARD"] = True
        print("🔌 engine DEAD — restart the app", flush=True)


def _engine_driver():
    """v929.2 — control-side auto-intake driver. The off-screen engine window's JS timers
    suspend under WKWebView occlusion, so control watches the bridge itself: on a deep
    stash read with a tally tab (runes/gems/materials → tvStashAutoIntake; personal/shared
    → tvVaultAutoIntake), fire the engine page's LOCKED pipeline via evaluate_js. One shot
    per tab per stash visit (visit resets on a deep non-stash read) — mirrors bible.html's
    own gate. Also a liveness probe every loop so the ENGINE lamp tells the truth."""
    time.sleep(8.0)   # let the window boot + board JS attach
    # v930.2 (Grok r2 P0) — start the cursor at NOW: a cold driver walking the /state ring
    # fired HISTORICAL stash tabs against the CURRENT eye frame (intake always shoots live).
    seen_ts = int(time.time() * 1000)
    visit_done = {}
    fire_q = []       # v931.1 — serialized intake queue (busy-burn fix)
    inflight = None   # the one job whose journal receipt we await
    _probes_out = 0
    while True:
        try:
            time.sleep(2.0)
            w = globals().get("_MAIN_WIN")
            if w is None:
                continue
            # liveness probe — evaluate_js runs even when timers are throttled
            alive = False
            if globals().get("_EJS_STUCK", 0) >= 3:
                # v930.2 (Grok r2 P0) — leak guard: each timed-out probe leaves a scratch
                # thread blocked in native evaluate_js; a suspended tile must not spawn an
                # unbounded pile. 3 strikes → stop probing until a fire attempt resets.
                globals()["_ENGINE_ALIVE"] = False
                globals()["_ENGINE_READY"] = False
                globals()["_EJS_STUCK"] = max(0, globals()["_EJS_STUCK"] - 0.05)  # slow decay → occasional retry
                _engine_selfheal(False, w)   # v943.4 — a wedged ejs is still a dead probe; keep the revive streak alive
                continue
            try:
                _pv = _ejs(w, "(function(){var f=document.getElementById('tvd-eng');return (f&&f.contentWindow&&f.contentWindow.tvStashAutoIntake)?2:1})()")
                if _pv is None:
                    globals()["_EJS_STUCK"] = globals().get("_EJS_STUCK", 0) + 1
                else:
                    globals()["_EJS_STUCK"] = 0
                alive = _pv in (1, 2, "1", "2")
                globals()["_ENGINE_READY"] = str(_ejs(w, "(function(){var f=document.getElementById('tvd-eng');return (f&&f.contentWindow&&typeof f.contentWindow.tvStashAutoIntake==='function')?1:0})()")) == "1"
                if not alive and globals().get("_ENG_ERR") != repr(_pv):
                    globals()["_ENG_ERR"] = repr(_pv)
                    print(f"🔌 engine probe returned {_pv!r}", flush=True)
            except Exception as _pe:
                globals()["_ENGINE_READY"] = False
                if globals().get("_ENG_ERR") != str(_pe):
                    globals()["_ENG_ERR"] = str(_pe)
                    print(f"🔌 engine probe error: {_pe}", flush=True)
            globals()["_ENGINE_ALIVE"] = bool(alive)
            _engine_selfheal(bool(alive), w)   # v943.4 — engine self-healing streak/revive
            if not alive:
                continue
            try:
                req = urllib.request.Request("http://127.0.0.1:17771/state")
                with urllib.request.urlopen(req, timeout=3) as r:
                    st = json.loads(r.read().decode("utf-8", "replace"))
            except Exception:
                st = {}   # bridge down (agent off / sealed) — no reads, but the inflight
                          # confirm below MUST still run: post-seal receipts land via the
                          # control /intake_result route into the JOURNAL (Grok shell-verdict P0)
            reads = st.get("reads") or []
            for rd in reads:
                ts = max(int(rd.get("completedTs") or 0), int(rd.get("ts") or 0))
                if ts <= seen_ts or rd.get("lane") != "deep" or rd.get("provisional"):
                    continue
                seen_ts = max(seen_ts, ts)
                globals()["_DRV_SEEN"] = globals().get("_DRV_SEEN", 0) + 1
                scene = str(rd.get("scene") or "")
                tab = str(rd.get("stashTab") or "").lower()
                if scene != "stash":
                    if visit_done:
                        visit_done = {}
                        fire_q = []   # stale visit's queued shots die with the visit (inflight may still confirm)
                        try:
                            _ejs(w, "(function(){var f=document.getElementById('tvd-eng');if(f&&f.contentWindow){f.contentWindow._vaultAutoDone=false;f.contentWindow._vaultAutoBusy=false}return 1})()", timeout=2.0)
                        except Exception:
                            pass
                    continue
                fid = str(rd.get("frameId") or "")
                # v931.1 (materials busy-burn, Grok r2 called it) — QUEUE, don't burn:
                # a second tab read while an intake holds the page shutter used to eat
                # the visit slot on a silent 'busy'. Tabs now queue and fire one at a
                # time; a slot is marked done only when its result JOURNALS (or after
                # 2 attempts). visit_done value: 'queued' | 'inflight' | True (done).
                key = None
                if tab in ("runes", "gems", "materials"):
                    key = tab
                elif tab in ("personal", "shared"):
                    key = "vault_" + tab
                if key and not visit_done.get(key):
                    visit_done[key] = "queued"
                    fire_q.append({"key": key, "tab": tab, "fid": fid, "tries": 0})
                    globals()["_DRV_QUEUED"] = globals().get("_DRV_QUEUED", 0) + 1

            # ── serialized fire loop: one intake in flight, confirm via journal ──
            now_ms = int(time.time() * 1000)
            intk = st.get("intakes") or []
            if inflight:
                landed = any(int(i.get("ts") or 0) >= inflight["fired_ms"] - 2000
                             and (i.get("intake") or {}).get("tab") in (inflight["tab"], inflight["key"].replace("vault_", ""))
                             for i in intk)
                if not landed:
                    # bridge-blind confirm: receipts that arrived via control's /intake_result
                    try:
                        landed = any(r.get("lane") == "intake"
                                     and int(r.get("ts") or 0) >= inflight["fired_ms"] - 2000
                                     and (r.get("intake") or {}).get("tab") in (inflight["tab"], inflight["key"].replace("vault_", ""))
                                     for r in _kai_journal_rows()[-80:])
                    except Exception:
                        pass
                if landed:
                    visit_done[inflight["key"]] = True
                    print(f"🧰 engine-driver: {inflight['key']} intake journaled ✓", flush=True)
                    inflight = None
                elif now_ms - inflight["fired_ms"] > 110_000:
                    if inflight["tries"] < 2:
                        inflight["tries"] += 1
                        fire_q.insert(0, inflight)   # retry once
                        print(f"🧰 engine-driver: {inflight['key']} no journal in 110s — retrying", flush=True)
                    else:
                        visit_done[inflight["key"]] = True   # give up, don't loop forever
                        print(f"⚠ engine-driver: {inflight['key']} failed twice — giving up this visit", flush=True)
                    inflight = None
            if not inflight and fire_q:
                job = fire_q.pop(0)
                # v941.4 (run-3: vault shot ok:false, 0 read) — shots photograph the READ'S
                # ARCHIVED FRAME (/hist/<fid>.jpg), never the live eye: by fire time the
                # player has moved on and a live shot sees gameplay. Same law as the funnel.
                _histp5 = "/hist/" + job["fid"] + ".jpg"
                if job["key"].startswith("vault_"):
                    js = ("(function(){try{var F=document.getElementById('tvd-eng');if(!F||!F.contentWindow)return 0;var W=F.contentWindow;"
                          "if(typeof W.vaultIntake!=='function')return 0;"
                          "fetch(%s+'?'+Date.now()).then(function(r){if(!r.ok)throw 0;return r.blob()}).then(function(b){"
                          "return W.vaultIntake([new W.File([b],'drv-vault.jpg',{type:'image/jpeg'})],{fromTv:true})}).then(function(res){"
                          "try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'vault',ok:!!(res&&res.ok),counts:(res&&res.added)||{},total:(res&&res.total)||0,errors:(res&&res.errors)||0,frameId:%s})}).catch(function(){})}catch(e){}"
                          "}).catch(function(){});return 1}catch(e){return 0}})()"
                          ) % (json.dumps(_histp5), json.dumps(job["tab"]), json.dumps(job["fid"]))
                else:
                    js = ("(function(){try{var F=document.getElementById('tvd-eng');if(!F||!F.contentWindow)return 0;var W=F.contentWindow;"
                          "if(W._stashShutter)return 2;var FN={runes:'runeIntake',gems:'gemIntake',materials:'materialIntake'}[%s];if(typeof W[FN]!=='function')return 0;"
                          "var LSK={runes:'d2r_runeStash',gems:'d2r_gemStash',materials:'d2r_materialStash'}[%s];"
                          "var ADJ={runes:'adjustRuneStash',gems:'adjustGemStash',materials:'adjustMaterialStash'}[%s];"
                          "var prev={};try{var st0=JSON.parse(W.LSR.getItem(LSK)||'{}');Object.keys(st0).forEach(function(k){prev[k]=parseInt(st0[k],10)||0})}catch(e){}"
                          "fetch(%s+'?'+Date.now()).then(function(r){if(!r.ok)throw 0;return r.blob()}).then(function(b){"
                          "return W[FN]([new W.File([b],'drv-tally.jpg',{type:'image/jpeg'})])}).then(function(res){"
                          "try{if(res&&res.ok){Object.keys(res.added||{}).forEach(function(k){var was=prev[k]||0;if(was>0&&typeof W[ADJ]==='function')W[ADJ](k,-was)})}}catch(e){}"
                          "try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'tally',ok:!!(res&&res.ok),counts:(res&&res.added)||{},total:(res&&res.total)||0,errors:(res&&res.errors)||0,frameId:%s})}).catch(function(){})}catch(e){}"
                          "}).catch(function(){});return 1}catch(e){return 0}})()"
                          ) % (json.dumps(job["tab"]), json.dumps(job["tab"]), json.dumps(job["tab"]), json.dumps(_histp5), json.dumps(job["tab"]), json.dumps(job["fid"]))
                try:
                    _ejs(w, js, timeout=4.0)
                    job["fired_ms"] = now_ms
                    visit_done[job["key"]] = "inflight"
                    inflight = job
                    globals()["_DRV_FIRED"] = globals().get("_DRV_FIRED", 0) + 1
                    print(f"🧰 engine-driver: fired {job['key']} (frame {job['fid']}, try {job['tries'] + 1})", flush=True)
                except Exception as e:
                    # v934.3 — a failed fire RE-QUEUES (was popped and lost forever)
                    job["tries"] += 1
                    if job["tries"] < 3:
                        fire_q.append(job)
                    else:
                        visit_done[job["key"]] = True
                    print(f"⚠ engine-driver fire failed (try {job['tries']}): {e}", flush=True)
        except Exception as _de:
            globals()["_DRV_ERR"] = str(_de)[:120]   # v934.3 — loop crashes become visible
            time.sleep(3.0)




def _eyes_pulse():
    """v935.11 — truthful badge data: when did the 🔵 verify lane and 🧠 KAI actually
    last act? Derived from the journal (mtime-cached); badges must never claim activity
    they can't prove (Grok shell-verdict #4)."""
    try:
        key = os.path.getmtime(os.path.join(HERE, "sessions.jsonl"))
    except Exception:
        key = None
    c = globals().get("_EYES_CACHE")
    if c and c[0] == key:
        return c[1]
    out = {"verifyTs": 0, "kaiTs": 0, "kaiMissed": None}
    try:
        for r in _kai_journal_rows()[-400:]:
            ln = r.get("lane")
            if ln == "verify":
                out["verifyTs"] = max(out["verifyTs"], int(r.get("completedTs") or r.get("ts") or 0))
            elif ln == "kai":
                out["kaiTs"] = max(out["kaiTs"], int(r.get("completedTs") or r.get("ts") or 0))
                if isinstance(r.get("kai"), dict) and "missedFrames" in r["kai"]:
                    out["kaiMissed"] = r["kai"].get("missedFrames")
    except Exception:
        pass
    globals()["_EYES_CACHE"] = (key, out)
    return out

def status_payload():
    # v872 (Konyo live: 'STANDBY keeps jumping at me mid session') — one slow ping under game
    # load flipped the whole console to STANDBY/IDLE for a beat. STICKY BRIDGE: a live agent
    # process with a bridge seen in the last 10s stays ON; only a truly dead bridge drops it.
    bridge_now = bool(_BR_CACHE["ping"]) and (time.time() - _BR_CACHE["ts"]) < 6.0
    bridge = bridge_now or (
        _agent_alive() and (time.time() - globals().get("_BRIDGE_LAST_OK", 0.0)) < 10.0)
    st = _BR_CACHE["st"] if bridge_now else None
    mode = _agent_mode
    if bridge and mode == "off":
        mode = "live"
    # v926.2 SELF-HEAL — never a ghost ON AIR: if the agent process is gone AND the bridge is
    # dead, the session is over regardless of the stale _agent_mode (crash / external kill).
    # This is why the board stayed "live" after the agent died — mode never got reset.
    if mode != "off" and not bridge and not _agent_alive():
        mode = "off"
    beat = (st or {}).get("beat") or {}
    events = (st or {}).get("events") or []
    tail = []
    for e in events[-8:]:
        tail.append(
            {
                "k": e.get("k", ""),
                "t": (e.get("t") or "")[:100],
                "ts": e.get("ts"),
            }
        )
    return {
        "ok": True,
        "ver": "v944.2",
        "engineAlive": globals().get("_ENGINE_ALIVE"),   # v929.2 — driver-probed truth, not a LS stamp
        "engineReady": globals().get("_ENGINE_READY"),
        "driver": {"seen": globals().get("_DRV_SEEN", 0), "queued": globals().get("_DRV_QUEUED", 0),
                   "fired": globals().get("_DRV_FIRED", 0), "err": globals().get("_DRV_ERR"),
                   "engineDeadHard": bool(globals().get("_ENGINE_DEAD_HARD"))},   # v934.3 — the tally driver's pulse · v943.4 revive give-up flag
        "watchdog": globals().get("_WATCHDOG_LAST"),
        "eyes": _eyes_pulse(),
        "journalMB": (lambda: round(os.path.getsize(os.path.join(HERE, "sessions.jsonl")) / 1e6, 1) if os.path.isfile(os.path.join(HERE, "sessions.jsonl")) else 0.0)(),   # v935 — last reel's expectation-check verdict
        "platform": "windows" if IS_WIN else ("mac" if sys.platform == "darwin" else sys.platform),
        "shell": "pywebview",
        "mode": ("stopping" if _stop_inflight else mode),
        "agent": mode != "off" and bridge,
        "bridge": bridge,
        "stopping": bool(_stop_inflight),
        "pid": _pid_cached(),
        "capture": bool(IS_WIN and (_read_pid(CAP_PID_PATH) and _pid_alive(_read_pid(CAP_PID_PATH)))),
        "intakeRing": ((st or {}).get("intakes") or [])[-12:],   # v903 — the dashboard's 📸 feed
        "readCount": (
            (st or {}).get("readCount")
            if (st or {}).get("readCount") is not None
            else len((st or {}).get("reads") or [])
        ),
        "area": beat.get("area") or (st or {}).get("area") or "",
        "scene": beat.get("scene") or "",
        "phase": beat.get("phase") or ("live" if bridge else "off"),
        "motion": beat.get("motion"),
        "interest": beat.get("interest") or (st or {}).get("interest"),
        "model": (st or {}).get("model") or "",
        "events": tail,
        "logPath": LOG_PATH,
        "agentPort": AGENT_PORT,
        "controlPort": CONTROL_PORT,
        # v772 — pin status (CrossOver on Mac · native D2R on Windows)
        "captureTarget": (st or {}).get("captureTarget") or {},
        "eyeAgeMs": (st or {}).get("eyeAgeMs", -1),   # v785 — film honesty for the stage
        "health": (st or {}).get("health") or {},     # v789 — fault-lamp truth
        # v899 — no-game banner (also mirrored on health from agent)
        "gameOk": (st or {}).get("gameOk", True) if st else True,
        "aiPaused": bool((st or {}).get("aiPaused") or ((st or {}).get("health") or {}).get("aiPaused")),
        "gameMsg": (st or {}).get("gameMsg") or ((st or {}).get("health") or {}).get("gameMsg") or "",
        "captureProc": _capture_health(),             # v793 — Windows capture lamp (LINKED/DEAD/RESTARTED)
        "bibleVer": _bible_ver(),                     # v816 — triple drift lamp (agent·app·board)
    }


# ── DOCTOR (v801, Grok R7) ─────────────────────────────────────────────────────
# Windows self-diagnosis. Read-mostly, cross-platform, MUST return <2s, and NEVER
# spawns the Claude CLI (claude_probe is a stub). ok == no severity-'block' failure.
# D2R / the agent never have to be running for ok — pin & frame issues are 'warn'.

_BIBLE_VER_CACHE = {"t": 0.0, "v": ""}
def _bible_ver():
    """v816 (Grok R8 #9) — the board's D2R_BUILD id, cached 30s (34k-line file, cheap regex)."""
    now = time.time()
    if now - _BIBLE_VER_CACHE["t"] < 30:
        return _BIBLE_VER_CACHE["v"]
    v = ""
    try:
        with open(os.path.join(REPO, "bible.html"), encoding="utf-8") as f:
            for line in f:
                if "window.D2R_BUILD" in line:
                    m = re.search(r"id:'(v[\d.]+)'", line)
                    if m:
                        v = m.group(1)
                        break   # v816.1 — first MATCHING line, not first mention
    except Exception:
        pass
    _BIBLE_VER_CACHE["t"] = now; _BIBLE_VER_CACHE["v"] = v
    return v


def _app_ver():
    """Doctor's ver mirrors status_payload's stamp (parity-locked to tv_diablo.VERSION)
    so it can never drift from the ship tag — read the literal, spawn nothing."""
    try:
        m = re.search(r'"ver": "(v[\d.]+)"', inspect.getsource(status_payload))
        return m.group(1) if m else "v?"
    except Exception:
        return "v?"


def _sock_open(port, host="127.0.0.1", timeout=0.35):
    """True if something is LISTENING on host:port (localhost, fast, never blocks)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, int(port)))
        return True
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


def _chk(cid, ok, severity, detail, fix=None):
    d = {"id": cid, "ok": bool(ok), "severity": severity, "detail": detail}
    if fix and not ok:
        d["fix"] = fix
    return d


def farmgate_payload():
    """GET /api/farmgate (v924, Grok FARM GATE): the ONE-BUTTON acceptance-day preflight.
    Read-only except ONE cheap subscription-lane CLI ping (the only check the default doctor
    is forbidden to run). Contract: {ok, verdict:'GO'|'WARN'|'NO-GO', checks:[...], vers}.
    Never touches capture/prompt/pool — plumbing truth only."""
    import re as _re
    checks = []
    here = os.path.dirname(os.path.abspath(__file__))

    def _stamp(path, pattern):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                m = _re.search(pattern, f.read())
            return m.group(1) if m else None
        except Exception:
            return None

    # 1) ver_match — RUNNING control ≡ disk control ≡ agent ≡ board. The runtime constant is
    # the only thing that catches an un-restarted app (Grok R4: disk stamps false-green it).
    try:
        vr = status_payload().get("ver")
    except Exception:
        vr = None
    vc = _stamp(os.path.abspath(__file__), r'"ver": "(v[\d.]+)"')
    va = _stamp(os.path.join(here, "tv_diablo.py"), r'VERSION = "(v[\d.]+)"')
    vb = _stamp(os.path.join(os.path.dirname(here), "bible.html"), r"id:'(v[\d.]+)'")
    vers = {"running": vr, "control": vc, "agent": va, "board": vb}
    same = vr is not None and vr == vc == va == vb
    fix1 = ("RESTART the console app (running %s, disk %s)" % (vr, vc)) if (vr and vc and vr != vc)         else "git pull, restart the console app, and ⌘⇧R any open site tab (stale ?cb= kills nights)"
    checks.append(_chk(
        "ver_match", same, "block",
        ("one truth: %s" % vr) if same else "SKEW running=%s disk=%s agent=%s board=%s" % (vr, vc, va, vb),
        fix1))

    # 2) claude CLI present
    env = _env_clean()
    exe = shutil.which("claude", path=env.get("PATH")) or shutil.which("claude")
    checks.append(_chk("claude_cli", bool(exe), "block",
                       exe or "claude CLI not found on PATH",
                       "npm i -g @anthropic-ai/claude-code, then sign in once in a Terminal"))

    # 3) claude AUTH — the one live ping (subscription lane, tiny, hard-capped).
    # v924-R4 (Grok): during ON AIR the live readers already prove the lane — never stack a
    # second `claude -p` on top of a warm pool; the gate belongs BEFORE air.
    if exe and _sock_open(AGENT_PORT):
        checks.append(_chk("claude_auth", True, "warn",
                           "skipped during ON AIR — the live readers already prove the lane (press the gate before air next time)"))
    elif exe:
        try:
            penv = dict(env)
            penv.pop("ANTHROPIC_API_KEY", None)
            penv.pop("ANTHROPIC_AUTH_TOKEN", None)
            pr = subprocess.run([exe, "-p", "reply with only: ok"],
                                capture_output=True, timeout=60, env=penv)
            out = (pr.stdout or b"").decode("utf-8", "replace").strip().lower()
            authed = pr.returncode == 0 and "ok" in out[:40]
            checks.append(_chk("claude_auth", authed, "block",
                               "subscription lane answered" if authed
                               else "CLI answered oddly: %s" % ((pr.stderr or pr.stdout or b"")[-160:].decode("utf-8", "replace")),
                               "run `claude` once in a bare Terminal and finish login"))
        except subprocess.TimeoutExpired:
            checks.append(_chk("claude_auth", False, "block", "CLI ping timed out (60s)",
                               "run `claude` in a bare Terminal — first run may need login/consent"))
        except Exception as e:
            checks.append(_chk("claude_auth", False, "block", "ping error: %s" % str(e)[:120],
                               "run `claude` once in a bare Terminal"))
    else:
        checks.append(_chk("claude_auth", False, "block", "skipped — no CLI", "install the CLI first"))

    # 4) disk — hist flood protection
    try:
        free_gb = shutil.disk_usage(here).free / (1024 ** 3)
        ok_d = free_gb >= 2
        checks.append(_chk("disk", ok_d, "block" if free_gb < 2 else "warn",
                           ("%.1f GB free" % free_gb) if ok_d else ("only %.1f GB free" % free_gb),
                           "clear space — the film + hist need room for a night"))
        if ok_d and free_gb < 8:
            checks.append(_chk("disk_low", False, "warn", "%.1f GB free — fine for one night, watch it" % free_gb))
    except Exception:
        checks.append(_chk("disk", True, "warn", "disk usage unreadable"))

    # 5) D2R process — warn only (he may press the gate before launching the game)
    try:
        pr = subprocess.run(["pgrep", "-if", r"D2R\.exe"], capture_output=True, timeout=5)
        running = pr.returncode == 0 and (pr.stdout or b"").strip()
        checks.append(_chk("d2r_window", bool(running), "warn",
                           "D2R.exe is running" if running else "D2R.exe not running yet",
                           "launch D2R, then press the gate again for a clean GO"))
    except Exception:
        checks.append(_chk("d2r_window", False, "warn", "process check unavailable",
                           "launch D2R before ON AIR"))

    # 6) handshake — only meaningful when the agent is live
    ap = _sock_open(AGENT_PORT)
    if ap:
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/state" % AGENT_PORT, timeout=3) as r:
                okb = r.status == 200
            checks.append(_chk("handshake", okb, "block",
                               "agent bridge answers /state" if okb else "bridge port open but /state failed",
                               "restart ON AIR"))
        except Exception as e:
            checks.append(_chk("handshake", False, "block", "bridge stuck: %s" % str(e)[:80], "restart ON AIR"))
    else:
        checks.append(_chk("handshake", True, "warn", "agent OFF — normal before ON AIR"))

    blocked = [c for c in checks if not c["ok"] and c["severity"] == "block"]
    warned = [c for c in checks if not c["ok"] and c["severity"] == "warn"]
    verdict = "NO-GO" if blocked else ("WARN" if warned else "GO")
    return {"ok": True, "verdict": verdict, "vers": vers, "checks": checks}


def doctor_payload():
    """GET /api/doctor contract: {ok, platform, checks:[{id,ok,severity,detail,fix?}],
    logTail, logPath, ver}. See the DOCTOR banner above for the invariants."""
    checks = []

    # 1) claude CLI on the SAME cleaned PATH the agent boots with
    env = _env_clean()
    exe = shutil.which("claude", path=env.get("PATH")) or shutil.which("claude")
    checks.append(_chk(
        "claude_cli", bool(exe), "block",
        exe or "claude CLI not found on PATH",
        "Install Claude Code CLI and put it on PATH (npm i -g @anthropic-ai/claude-code)"))

    # 2) claude probe — deliberately NOT run: the doctor must never spawn the CLI
    checks.append(_chk("claude_probe", True, "warn",
                       "not probed (doctor never spawns the CLI)"))

    # 3) agent bridge port — OFF is normal, so warn only
    ap = _sock_open(AGENT_PORT)
    checks.append(_chk(
        "port_agent", ap, "warn",
        "listening on 127.0.0.1:%d" % AGENT_PORT if ap
        else "no listener on 127.0.0.1:%d (agent OFF is normal)" % AGENT_PORT))

    # 4) control port — we are answering this very request, so it is up by definition
    checks.append(_chk("port_control", True, "block",
                       "control server up on 127.0.0.1:%d" % CONTROL_PORT))

    # 5) python — reject the Windows Store stub (its python.exe alias breaks child spawns)
    pexe = sys.executable or ""
    pver = "%d.%d.%d" % sys.version_info[:3]
    stub = "WindowsApps" in pexe
    checks.append(_chk(
        "python", bool(pexe) and not stub, "block",
        ("Windows Store stub python: %s" % pexe) if stub
        else "%s (%s)" % (pexe or "unknown", pver),
        "Install real Python from python.org and turn OFF the python.exe 'App execution alias'"))

    # 6) WebView2 runtime (Windows app window). Mac = native WKWebView, always fine.
    if not IS_WIN:
        checks.append(_chk("webview2", True, "block", "n/a (mac uses native WKWebView)"))
    else:
        pv = None
        try:
            import winreg
            key = (r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients"
                   r"\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}")
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as k:
                pv, _ = winreg.QueryValueEx(k, "pv")
        except Exception:
            pv = None
        checks.append(_chk(
            "webview2", bool(pv), "block",
            "WebView2 runtime %s" % pv if pv else "WebView2 runtime not found",
            "Install the Microsoft Edge WebView2 Runtime (Evergreen)"))

    # 7) capture loop lamp (Windows only) — reuse the live health probe
    if not IS_WIN:
        checks.append(_chk("capture_proc", True, "warn", "n/a (Windows-only capture loop)"))
    else:
        h = _capture_health()
        checks.append(_chk(
            "capture_proc", h in ("", "LINKED", "RESTARTED"), "warn",
            h or "idle (agent off)",
            "Press RESTART; if it recurs, check capture_win.ps1 and the D2R window"))

    # 8) live frames — freshness only MATTERS (blocks) when we claim to be LIVE
    live = (_agent_mode == "live")
    now = time.time()
    newest, ages = None, []
    for label in ("eye.jpg", "live.bmp"):
        fp = os.path.join(HERE, "frames", label)
        if os.path.isfile(fp):
            age = now - os.path.getmtime(fp)
            ages.append("%s=%.1fs" % (label, age))
            newest = age if newest is None else min(newest, age)
    fresh = newest is not None and newest <= 10
    if live and not fresh:
        checks.append(_chk(
            "live_frames", False, "block",
            ("frames stale: %s" % ", ".join(ages)) if ages else "no eye.jpg / live.bmp while LIVE",
            "Capture is frozen — check the D2R window and capture_win.ps1"))
    else:
        checks.append(_chk(
            "live_frames", True, "warn",
            ", ".join(ages) if ages else "no frames yet (agent off)"))

    # 9) agent bridge heartbeat — OFF is normal, so warn only
    bp = _bridge_ping()
    checks.append(_chk(
        "bridge", bp is not None, "warn",
        "agent bridge responding on :%d" % AGENT_PORT if bp is not None
        else "agent bridge silent (agent OFF is normal)"))

    # 10) stale pid files whose recorded pid is already dead
    stale = []
    for label, p in (("control_agent.pid", PID_PATH), ("control_capture.pid", CAP_PID_PATH)):
        pid = _read_pid(p)
        if pid is not None and not _pid_alive(pid):
            stale.append("%s->pid %d dead" % (label, pid))
    checks.append(_chk(
        "pid_files", not stale, "warn",
        "; ".join(stale) if stale else "no stale pid files",
        "Harmless — STOP then ON rewrites them"))

    # v815 (Grok R8 #8) — can this night be REPLAYED? Frame coverage + id sanity on the
    # journal tail (last ~200 rows): % beats whose hist frame exists, sessionId coverage.
    try:
        _jl = os.environ.get("TV_SESSIONS") or os.path.join(HERE, "sessions.jsonl")   # v877
        _hist = os.path.join(HERE, "frames", "hist")
        rows = []
        if os.path.isfile(_jl):
            with open(_jl, encoding="utf-8") as f:
                for line in f.readlines()[-200:]:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
        if rows:
            with_fid = [r for r in rows if r.get("frameId")]
            have = sum(1 for r in with_fid
                       if os.path.isfile(os.path.join(_hist, str(r["frameId"]) + ".jpg")))
            sid_cov = sum(1 for r in rows if r.get("sessionId"))
            pct = int(100 * have / max(1, len(with_fid)))
            # v840 — always warn-severity so agent OFF nights don't fail the doctor (TestDoctor);
            # detail still shouts missing count. Live ON nights: user sees amber lamp on the UI.
            checks.append(_chk(
                "session_integrity", pct >= 40, "warn",
                "frames %d%% of %d reads · sessionId %d/%d · missing %d" % (
                    pct, len(with_fid), sid_cov, len(rows), max(0, len(with_fid) - have)),
                "v840 journal-shield protects NEW frames; prior nights may stay hollow after the footage flood"))
        else:
            checks.append(_chk("session_integrity", True, "warn", "no journal rows yet"))
    except Exception:
        pass

    # v811 (Grok R8 #6) — journal generation truth: how many rotated nights exist
    try:
        _jroot = os.path.join(HERE, "sessions")
        _gens = [g for g in range(1, 6) if os.path.isfile(_jroot + ".%d.jsonl" % g)]
        _live = os.path.isfile(_jroot + ".jsonl")
        checks.append(_chk("journal_gens", True, "warn",
                           "live=%s gens=%s" % ("yes" if _live else "no",
                                                (",".join(str(g) for g in _gens) or "none"))))
    except Exception:
        pass

    ok = not any((not c["ok"]) and c["severity"] == "block" for c in checks)

    try:
        with open(LOG_PATH, "rb") as f:
            log_tail = f.read()[-2048:].decode("utf-8", "replace")
    except Exception:
        log_tail = "(no log yet)"

    return {
        "ok": ok,
        "platform": "windows" if IS_WIN else ("mac" if sys.platform == "darwin" else sys.platform),
        "checks": checks,
        "logTail": log_tail,
        "logPath": LOG_PATH,
        "ver": _app_ver(),
    }


# ── HTTP ─────────────────────────────────────────────────────────────────────

def _read_ui():
    if os.path.isfile(UI_PATH):
        with open(UI_PATH, "rb") as f:
            return f.read()
    return b"<h1>TV DIABLO control_ui.html missing</h1>"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"   # v877 (army B#7) — keep-alive: no new TCP+thread per poll
    def log_message(self, fmt, *args):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_art(self, name):
        from urllib.parse import unquote

        rel = unquote(name).split("?", 1)[0].split("#", 1)[0]
        target = os.path.realpath(os.path.join(ART_DIR, rel))
        if not (target == ART_DIR or target.startswith(ART_DIR + os.sep)):
            self._json(403, {"ok": False, "msg": "forbidden"})
            return
        if not os.path.isfile(target):
            self._json(404, {"ok": False, "msg": "not found"})
            return
        ext = os.path.splitext(target)[1].lower()
        ctype = _ART_MIME.get(ext)
        if ctype is None:
            self._json(415, {"ok": False, "msg": "unsupported"})
            return
        try:
            with open(target, "rb") as f:
                data = f.read()
        except Exception as e:
            self._json(500, {"ok": False, "msg": str(e)})
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=86400")
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _load_journal_cached(self):
        """v879 (army B#5) — theatre endpoints re-parsed every generation file per call.
        Control never appends, so an mtime key is honest HERE (unlike the agent side)."""
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import replay as _rp
        try:
            d = os.path.dirname(_rp.JOURNAL) or "."
            base = os.path.basename(_rp.JOURNAL)
            key = tuple(sorted(
                (n, os.path.getmtime(os.path.join(d, n)))
                for n in os.listdir(d)
                if n.startswith(base) or (n.startswith("sessions") and n.endswith(".jsonl"))))
        except Exception:
            key = None
        c = globals().setdefault("_JRNL_CACHE", {"key": object(), "rows": None})
        if key is not None and key == c["key"] and c["rows"] is not None:
            return c["rows"]
        rows = _rp.load_journal()
        c["key"], c["rows"] = key, rows
        return rows

    def _theatre_sessions(self):
        """v765 — REPLAY THEATRE: list journaled sessions (newest first) from tv/sessions.jsonl."""
        try:
            if HERE not in sys.path:
                sys.path.insert(0, HERE)
            import replay as _rp
            sessions = _rp.split_sessions(self._load_journal_cached())
            out = []
            for i, sess in enumerate(sessions, 1):
                frames = [r for r in sess if r.get("frameId")
                          and os.path.isfile(os.path.join(HIST_DIR, r["frameId"] + ".jpg"))]
                areas = []
                for r in sess:
                    a = r.get("area")
                    if a and a not in areas:
                        areas.append(a)
                sid = next((r.get("sessionId") for r in sess if r.get("sessionId")), "")
                want = sum(1 for r in sess if r.get("frameId"))
                miss = max(0, want - len(frames))
                _reeln = 0
                _thumb = ""
                try:
                    _rd2 = os.path.join(HIST_DIR, "reel_" + str(sess[0].get("sessionId") or ""))
                    if os.path.isdir(_rd2):
                        _rfs = sorted(f2 for f2 in os.listdir(_rd2) if f2.endswith(".jpg"))
                        _reeln = len(_rfs)
                        if _rfs:
                            # v890 — the card's art IS the run: its middle frame, 160px lane
                            _thumb = "reel_" + str(sess[0].get("sessionId") or "") + "/" + _rfs[len(_rfs) // 2]
                    elif i == 1 and not any(r3.get("sessionEnd") for r3 in sess):   # v930.1 — `n` was a NameError (loop var is i): the LIVE card silently lost its thumb+count every call
                        # v908 (Grok P1) — the LIVE card pins its thumb to the FIRST loose frame
                        # (a mid frame churns every refresh = flicker)
                        try:
                            _lf = sorted(f4 for f4 in os.listdir(HIST_DIR)
                                         if f4.startswith("f_") and f4.endswith(".jpg"))
                            if _lf:
                                _reeln = len(_lf)
                                _thumb = _lf[0]
                        except Exception:
                            pass
                except Exception:
                    pass
                # v937 — the session's STORY fields: verdicts at a glance (shelf + home digest)
                _wd = sum(1 for r2 in sess if r2.get("lane") == "watchdog")
                _tl = sum(1 for r2 in sess if r2.get("lane") == "intake")
                _km, _kc = None, None
                _thrown = set()
                _keepers = []
                _registered = None   # v943 — 📖 how many items KAI witnessed this session
                for r2 in sess:
                    if r2.get("lane") == "kai" and isinstance(r2.get("kai"), dict) and "missedFrames" in r2["kai"]:
                        _km = r2["kai"].get("missedFrames"); _kc = r2["kai"].get("classes")
                    if r2.get("lane") == "kai" and isinstance(r2.get("kai"), dict) and isinstance(r2["kai"].get("register"), dict):
                        _registered = r2["kai"]["register"].get("count")
                    for nm2 in (r2.get("thrown_names") or []):
                        _thrown.add(str(nm2).strip().lower())
                    _jd = (r2.get("kai") or {}).get("judge") if isinstance(r2.get("kai"), dict) else None
                    if isinstance(_jd, dict) and _jd.get("tier") == "keep" and _jd.get("name"):
                        _keepers.append(str(_jd["name"]).strip().lower())
                # v940 💔 — a REGRET = the judge ruled KEEP on something this session threw out
                _regrets = sum(1 for k2 in _keepers if k2 in _thrown)
                out.append({"watchdogViolations": _wd, "tallies": _tl, "kaiMissed": _km, "kaiClasses": _kc,
                            "judged": len(_keepers), "regrets": _regrets, "registered": _registered,
                            "n": i, "t0": sess[0].get("ts"), "t1": sess[-1].get("ts"),
                            "reads": len([r2 for r2 in sess if not r2.get("sessionEnd") and r2.get("scene") != "session_end" and r2.get("mode") != "session_end" and r2.get("kind") != "skip" and r2.get("lane") not in ("kai", "verify", "intake")]), "frames": len(frames),
                            "named": sum(1 for r in sess if r.get("names")),
                            "areas": areas[:6], "stub": (len([r2 for r2 in sess if not r2.get("sessionEnd") and r2.get("scene") != "session_end" and r2.get("mode") != "session_end" and r2.get("kind") != "skip"]) < 3
                             and _reeln == 0),   # v885 (Grok #1) — a 1-read ghost never poses as a run
                    "footageN": _reeln,   # v883 — the shelf tells the truth about video
                    "intakes": len([r2 for r2 in sess if r2.get("lane") == "intake"]),   # v902
                    "thumb": _thumb,      # v890 — HD filmstrip art from the run itself
                    "sessionId": sid,
                            # v840 — SIM honesty: how much of the night is still replayable
                            "frameWant": want, "frameMissing": miss,
                            "archiveOk": miss == 0 and len(frames) > 0})
            return out
        except Exception as e:
            return {"error": str(e)}

    def _thin_footage_beats(self, beats, step_ms=400, near_ms=3000):
        """v894 — server-side film thin: keep all AI reads; quiet film ~2.5fps wall; dense near reads.
        This is the SIM engine fix — not a client 2× button."""
        if len(beats) < 50:
            return beats
        read_ts = sorted(
            int(b.get("ts") or 0)
            for b in beats
            if not b.get("footage") and not b.get("skip")
        )
        def _near(ts):
            for rt in read_ts:
                if abs(rt - ts) <= near_ms:
                    return True
                if rt > ts + near_ms:
                    break
            return False
        out, last_f = [], -10**15
        for b in beats:
            if not b.get("footage"):
                out.append(b)
                continue
            ts = int(b.get("ts") or 0)
            if _near(ts) or (ts - last_f) >= step_ms:
                out.append(b)
                last_f = ts
        return out if len(out) >= 2 else beats

    def _prewarm_session_frames(self, beats, limit=48, width="960"):
        """v894 — build theatre derivatives in the background so play doesn't block on sips."""
        if IS_WIN:
            return
        paths = []
        for b in beats:
            fr = b.get("frame") or ""
            if fr and fr.endswith(".jpg"):
                paths.append(fr)
            if len(paths) >= limit:
                break
        if not paths:
            return

        def _run():
            cache_dir = os.path.join(HIST_DIR, "cache" + width)
            try:
                os.makedirs(cache_dir, exist_ok=True)
            except Exception:
                return
            for fr in paths:
                try:
                    src = os.path.join(HIST_DIR, fr)
                    # reel_ paths are under HIST_DIR
                    if not os.path.isfile(src):
                        continue
                    base = os.path.basename(fr)
                    cached = os.path.join(cache_dir, base)
                    if os.path.isfile(cached):
                        continue
                    subprocess.run(
                        ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "68",
                         "--resampleHeightWidthMax", width, src, "--out", cached],
                        capture_output=True, timeout=8,
                    )
                except Exception:
                    pass
        threading.Thread(target=_run, daemon=True, name="tvd-prewarm-sess").start()

    def _theatre_session(self, n, pack="debug"):
        """v895 — personal visual debugger for one ON AIR session.
        pack=debug|raw: every footage frame + every AI read, capture-clock ordered (default).
        pack=fast: server-thinned quiet film (optional zip mode — not the debugger default)."""
        try:
            if HERE not in sys.path:
                sys.path.insert(0, HERE)
            import replay as _rp
            sessions = _rp.split_sessions(self._load_journal_cached())
            if n < 1 or n > len(sessions):
                return {"error": "no such session"}
            sess = sessions[n - 1]
            beats = []
            for r in sess:
                if r.get("lane") == "intake":
                    # v902 — 📸 intake beat: the library shows what the locked pipeline did,
                    # time-synced to the frame the shot came from
                    _ifid = str(r.get("frameId") or "")
                    _ifr = _hist_frame_rel(_ifid)   # v940.4 — resolve #v / reel paths
                    beats.append({"ts": int(r.get("ts") or 0), "captureTs": int(r.get("ts") or 0),
                                  "intakeBeat": True, "intake": r.get("intake") or {},
                                  "note": r.get("note") or "", "frameId": _ifid,
                                  "frame": _ifr, "frameOk": bool(_ifr),   # v908-R6 — the film paints the SHOT
                                  "names": [], "scene": "intake", "area": "", "lane": "intake"})
                    continue
                if r.get("kind") == "skip":
                    beats.append({"ts": int(r.get("ts") or 0), "captureTs": int(r.get("ts") or 0),
                                  "skip": True, "why": r.get("why") or "", "note": r.get("note") or "",
                                  "names": [], "scene": "", "area": "", "lane": "skip"})
                    continue
                if r.get("scene") == "session_end" or r.get("mode") == "session_end":
                    continue   # v894 — seal rows are not playable beats
                fid = r.get("frameId") or ""
                # v940.4 — frameOk must resolve verify suffix (#v) and reel-relative ids.
                # Exact fid+'.jpg' lied "photo pruned" for every second-eye beat.
                _frel = _hist_frame_rel(fid)
                has = bool(_frel)
                fts = None
                if fid and "_" in str(fid):
                    try:
                        fts = int(str(fid).split("#", 1)[0].rsplit("_", 1)[-1])
                    except Exception:
                        fts = None
                if r.get("captureTs"):
                    cap_ts = int(r["captureTs"])
                elif fts is not None:
                    raw_ts = int(r.get("ts") or 0)
                    if raw_ts and abs(raw_ts - fts) > 2000:
                        cap_ts = fts
                    else:
                        cap_ts = raw_ts or fts
                else:
                    cap_ts = r.get("ts")
                done_ts = r.get("completedTs") or r.get("ts") or cap_ts
                # v894 — lean beat only (forensics via /api/beat). Smaller JSON = faster open.
                beats.append({
                    "ts": cap_ts,
                    "captureTs": cap_ts,
                    "completedTs": done_ts,
                    "n": r.get("n"), "scene": r.get("scene", ""),
                    "area": r.get("area", ""), "names": r.get("names", []),
                    "note": (r.get("note") or "")[:120],
                    "frame": _frel if has else "",
                    "frameId": fid,
                    "frameOk": has,
                    "sessionId": r.get("sessionId") or "",
                    "ms": r.get("ms", 0), "lane": r.get("lane", ""),
                    "model": r.get("model", ""),
                    "vault_names": r.get("vault_names") or [],
                    "pending_names": r.get("pending_names") or [],
                    "thrown_names": r.get("thrown_names") or [],
                    "discovered_names": r.get("discovered_names") or [],
                    "intent": r.get("intent", ""), "stashTab": r.get("stashTab", ""),
                    "farewell": bool(r.get("farewell")),
                    "ocr_names": r.get("ocr_names") or [],
                    "ocr_ms": r.get("ocr_ms") or 0,
                    "names_loc": r.get("names_loc") or {},
                    "equipped_names": r.get("equipped_names") or [],
                    "lean": True,
                    "dispatch": {k: (r.get("dispatch") or {}).get(k)
                                 for k in ("origin", "readerId")
                                 if (r.get("dispatch") or {}).get(k) is not None},
                    "confirmed_names": r.get("confirmed_names") or [],
                    "ocr_seeded": r.get("ocr_seeded") or [],
                    "conf": r.get("conf"),
                    "sim": bool(r.get("sim")),
                })
            # Footage interleave — prefer sealed reel; never double-scan loose hist when reel exists
            try:
                _sid0 = str(sess[0].get("sessionId") or "")
                try:
                    _boot_ms = int(_sid0.split("_")[1]) if _sid0.startswith("s_") else 0
                except Exception:
                    _boot_ms = 0
                t0f = (_boot_ms or (sess[0].get("ts") or 0)) - 2000
                _sealed = any(
                    r2.get("sessionEnd")
                    or r2.get("scene") == "session_end"
                    or r2.get("mode") == "session_end"
                    for r2 in sess
                )
                _is_newest = (n == 1)
                t1f = int(time.time() * 1000) if (not _sealed and _is_newest) else ((sess[-1].get("ts") or 0) + 2000)
                hist_dir = HIST_DIR
                sid_here = (sess[0].get("sessionId") or "")
                _reel_dir = os.path.join(hist_dir, "reel_" + sid_here) if sid_here else ""
                _reel_ok = _reel_dir and os.path.isdir(_reel_dir)
                _foot = []
                if _reel_ok:
                    # v894 — index.json first (O(n) no re-stat name parse thrash when present)
                    _idxp = os.path.join(_reel_dir, "index.json")
                    _frames = None
                    if os.path.isfile(_idxp):
                        try:
                            with open(_idxp, encoding="utf-8") as _jf:
                                _frames = (json.load(_jf) or {}).get("frames") or []
                        except Exception:
                            _frames = None
                    if _frames is None:
                        _frames = []
                        for fn in os.listdir(_reel_dir):
                            if fn.startswith("f_") and fn.endswith(".jpg"):
                                try:
                                    _frames.append({"f": fn, "ts": int(fn[2:-4])})
                                except Exception:
                                    pass
                        _frames.sort(key=lambda x: x.get("ts") or 0)
                    pref = "reel_" + sid_here + "/"
                    # v944 🚦 — join the routing ledger's label + verdict onto each footage beat
                    # (additive, defensive: absent report or key → beat simply carries no label).
                    _routemap = {}
                    try:
                        _krp = os.path.join(_reel_dir, "kai_report.json")
                        if os.path.isfile(_krp):
                            with open(_krp, encoding="utf-8") as _krf:
                                for _rr in ((json.load(_krf) or {}).get("routing") or []):
                                    _routemap[str(_rr.get("f") or "")] = (
                                        _rr.get("label"), _rr.get("routed") or _rr.get("skipReason"))
                    except Exception:
                        _routemap = {}
                    for it in _frames:
                        fn = it.get("f") or ""
                        fts = int(it.get("ts") or 0)
                        if not fn:
                            continue
                        _lbl, _rv = _routemap.get(fn, (None, None))
                        _foot.append({"ts": fts, "captureTs": fts, "footage": True,
                                      "frame": pref + fn, "frameId": pref + fn[:-4],
                                      "names": [], "scene": "", "area": "", "lane": "footage",
                                      "label": _lbl, "routeVerdict": _rv})
                elif os.path.isdir(hist_dir):
                    # live/unsealed fallback only
                    for fn in os.listdir(hist_dir):
                        if not (fn.startswith("f_") and fn.endswith(".jpg")):
                            continue
                        try:
                            fts = int(fn[2:-4])
                        except Exception:
                            continue
                        if t0f <= fts <= t1f:
                            _foot.append({"ts": fts, "captureTs": fts, "footage": True,
                                          "frame": fn, "frameId": fn[:-4], "names": [],
                                          "scene": "", "area": "", "lane": "footage"})
                beats.extend(_foot)
            except Exception:
                pass

            def _photo_clock(b):
                fid = b.get("frameId") or ""
                if "_" in str(fid):
                    try:
                        return int(str(fid).rsplit("_", 1)[1])
                    except Exception:
                        pass
                return b.get("ts") or 0
            for b in beats:
                pc = _photo_clock(b)
                if pc and abs(pc - (b.get("ts") or 0)) > 1500:
                    b["ts"] = pc
            # v895 — capture-clock order; same-ms: film first then AI read (annotation sits on that moment)
            beats.sort(key=lambda b: (
                _photo_clock(b),
                0 if b.get("footage") else (1 if not b.get("skip") else 2),
                b.get("n") or 0,
            ))
            # v895 — DEBUGGER default keeps every frame. Only pack=fast thins quiet film.
            if pack == "fast":
                beats = self._thin_footage_beats(beats, step_ms=400, near_ms=3000)
            # v941 THE DOSSIER — hang all three eyes on each read/footage beat.
            # Maps built ONCE from this session's rows; join is O(1)/O(log n) per beat.
            try:
                _dmaps = _build_dossier_maps(sess)
                for b in beats:
                    if b.get("footage") or b.get("lane") == "deep":
                        b["dossier"] = _beat_dossier(_dmaps, b)
            except Exception:
                pass
            sid = next((r.get("sessionId") for r in sess if r.get("sessionId")), "")
            # prewarm early frames (1280 theatre) so scrub/play is not sips-bound
            try:
                self._prewarm_session_frames(beats, limit=80, width="1280")
            except Exception:
                pass
            n_read = sum(1 for b in beats if not b.get("footage") and not b.get("skip"))
            n_foot = sum(1 for b in beats if b.get("footage"))
            return {
                "n": n, "beats": beats, "sessionId": sid,
                "pack": "debug" if pack != "fast" else "fast",
                "modeHint": "real",   # client: wall-clock debugger default
                "stats": {"reads": n_read, "footage": n_foot, "beats": len(beats)},
                "t0": beats[0].get("ts") if beats else sess[0].get("ts"),
                "t1": beats[-1].get("ts") if beats else sess[-1].get("ts"),
            }
        except Exception as e:
            return {"error": str(e)}

    def _serve_hist(self, name):
        """Serve an archived session frame (tv/frames/hist) — path-safe, jpg only.
        v799 (Grok R6 trap 2) — ?w=1280 serves a disk-cached theatre derivative: a decoded
        2560px JPEG is ~14MB RGBA in the WebView; playback at 4x on full frames = memory death.
        Full 2560 stays one click away (forensics 'open original')."""
        from urllib.parse import unquote, urlparse, parse_qs
        # v820 — the do_GET router strips "?" before routing; the query lives on self.path
        qs = parse_qs(urlparse(self.path).query or "")
        rel = unquote(name).split("?", 1)[0].split("#", 1)[0]
        target = os.path.realpath(os.path.join(HIST_DIR, rel))
        if not target.startswith(os.path.realpath(HIST_DIR) + os.sep) or not target.endswith(".jpg"):
            self._json(403, {"ok": False}); return
        if not os.path.isfile(target):
            self._json(404, {"ok": False}); return
        want_w = (qs.get("w") or [""])[0]
        if want_w in ("1280", "160") and not IS_WIN:   # v802 — 160 = scrub thumbnails
            cache_dir = os.path.join(HIST_DIR, "cache" + want_w)
            cached = os.path.join(cache_dir, os.path.basename(target))
            try:
                if not os.path.isfile(cached):
                    os.makedirs(cache_dir, exist_ok=True)
                    r = subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "72",
                                        "--resampleHeightWidthMax", want_w, target, "--out", cached],
                                       capture_output=True, timeout=10)
                    if r.returncode != 0 or not os.path.isfile(cached):
                        cached = target
                target = cached
            except Exception:
                pass
        try:
            with open(target, "rb") as f:
                data = f.read()
        except Exception:
            self._json(500, {"ok": False}); return
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=31536000, immutable")   # v799 — frameId is content-addressed
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html", "/ui"):
            body = _read_ui()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/status":
            self._json(200, status_payload())
            return
        if path.startswith("/art/"):
            self._serve_art(path[len("/art/") :])
            return
        if path in ("/board", "/board/"):
            # v774 🌙 — THE APP HOSTS THE BOARD: serve the local bible.html same-origin so the
            # native window lives on ONE http origin (no more file:// localStorage split for
            # app users). Engines are never forked — this IS the board.
            try:
                with open(BIBLE, "rb") as f:
                    body = f.read()
            except Exception:
                self._json(404, {"ok": False, "msg": "bible.html missing"})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
            return
        if path.startswith("/tv/frames/hist/"):
            # the board's theatre fallback path resolves same-origin too
            self._serve_hist(path[len("/tv/frames/hist/"):])
            return
        if path == "/api/sessions":
            self._json(200, {"sessions": self._theatre_sessions()})
            return
        if path == "/api/tz":
            # v944 tracker heal — /api/tz is a Cloudflare Pages function; it only
            # exists on the live deploy. The in-app shell serves the board from
            # THIS server, so the Terror Zone tracker 404'd ("tracker is down").
            # Proxy the live endpoint through the site's HTTP-Basic gate, 90s cache.
            self._json(*_tz_proxy())
            return
        if path == "/api/tallies":
            # v929 (Konyo: "I want to see what EXACTLY was tallied — RUNES for runes, GEMS
            # for gems, MATERIALS for materials") — every intake shot from the journal,
            # newest first, with per-key counts + the frame photo it was counted from.
            try:
                shots = []
                for r in self._load_journal_cached():
                    ik = r.get("intake")
                    if not isinstance(ik, dict):
                        continue
                    shots.append({
                        "ts": r.get("ts") or r.get("captureTs") or 0,
                        "tab": ik.get("tab") or ik.get("kind") or "",
                        "kind": ik.get("kind") or "",
                        "ok": bool(ik.get("ok", True)),
                        "counts": ik.get("counts") if isinstance(ik.get("counts"), dict) else {},
                        "total": int(ik.get("total") or 0),
                        "errors": int(ik.get("errors") or 0),
                        "frameId": r.get("frameId") or "",
                        "sessionId": r.get("sessionId") or "",
                    })
                shots.sort(key=lambda s: s["ts"], reverse=True)
                self._json(200, {"ok": True, "shots": shots[:200]})
            except Exception as e:
                self._json(200, {"ok": False, "msg": str(e)[:160], "shots": []})
            return
        if path == "/api/intake_log":
            # v944.4 (Konyo: "a separate log for the backend side of these intakes getting
            # received — like a log") — the raw plumbing view: every intake receipt the journal
            # recorded, newest first, with the transport truth (kind, ok, totals, errors, the
            # frame it came from, session). This is the RECEIPT LEDGER, distinct from /api/tallies
            # (which is the item counts) — here you watch receipts LAND and spot the 0-total misses.
            try:
                rows = []
                for r in self._load_journal_cached():
                    ik = r.get("intake")
                    if not isinstance(ik, dict):
                        continue
                    _tot = int(ik.get("total") or 0)
                    _ok = bool(ik.get("ok", True))
                    rows.append({
                        "ts": r.get("ts") or r.get("captureTs") or 0,
                        "tab": ik.get("tab") or ik.get("kind") or "",
                        "kind": ik.get("kind") or "",
                        "ok": _ok,
                        "total": _tot,
                        "errors": int(ik.get("errors") or 0),
                        "types": len(ik.get("counts") or {}) if isinstance(ik.get("counts"), dict) else 0,
                        "frameId": r.get("frameId") or "",
                        "sessionId": r.get("sessionId") or "",
                        "lane": r.get("lane") or "",
                        # the plumbing verdict: landed-empty misses vs real receipts vs errors
                        "status": ("error" if not _ok else ("empty" if _tot == 0 else "ok")),
                    })
                rows.sort(key=lambda s: s["ts"], reverse=True)
                _empty = sum(1 for r in rows if r["status"] == "empty")
                _err = sum(1 for r in rows if r["status"] == "error")
                self._json(200, {"ok": True, "rows": rows[:400],
                                 "summary": {"total": len(rows), "empty": _empty, "error": _err}})
            except Exception as e:
                self._json(200, {"ok": False, "msg": str(e)[:160], "rows": []})
            return
        if path.startswith("/api/beat"):
            # v879 (Grok B) — the READ CARD's forensic blob, one beat at a time
            try:
                from urllib.parse import urlparse as _up, parse_qs as _pq
                q = _pq(_up(self.path).query or "")
                sid = (q.get("id") or [""])[0]
                bn = int((q.get("n") or ["0"])[0])
                if HERE not in sys.path:
                    sys.path.insert(0, HERE)
                import replay as _rp
                _jr = self._load_journal_cached()
                row = None
                for r in _jr:
                    if (r.get("sessionId") or "") == sid and int(r.get("n") or -1) == bn:
                        row = r
                if row is None:
                    self._json(404, {"ok": False, "msg": "no such beat"})
                    return
                # v941 THE DOSSIER — same three-eye join as the pack, one beat.
                try:
                    _srows = [r for r in _jr if (r.get("sessionId") or "") == sid]
                    _dossier = _beat_dossier(_build_dossier_maps(_srows), row)
                except Exception:
                    _dossier = {"tally": None, "verify": None, "kai": None}
                self._json(200, {"ok": True,
                                 "dossier": _dossier,
                                 "raw": row.get("raw") or "",
                                 "dispatch": row.get("dispatch") or {},
                                 "promptVer": row.get("promptVer") or "",
                                 "parse": row.get("parse") or {},
                                 "decisions": row.get("decisions") or {},
                                 "pre": row.get("pre") or [],
                                 "chain": row.get("chain") or {},
                                 "ocr_raw": row.get("ocr_raw") or [],
                                 "ocr_seeded": row.get("ocr_seeded") or [],
                                 "equipped_names": row.get("equipped_names") or [],
                                 "board": row.get("board") or {},       # v883 — A2.5 feeds the river's BOARD stage
                                 "vision": row.get("vision") or {}})
            except Exception as e:
                self._json(500, {"ok": False, "msg": str(e)})
            return
        if path.startswith("/api/session"):
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            try:
                num = int((q.get("n") or ["1"])[0])
            except Exception:
                num = 1
            # v895 — default pack=debug (every fps frame + every AI read). pack=fast is optional zip.
            pack = (q.get("pack") or ["debug"])[0].strip().lower()
            if pack not in ("debug", "raw", "fast"):
                pack = "debug"
            self._json(200, self._theatre_session(num, pack=pack))
            return
        if path.startswith("/hist/"):
            self._serve_hist(path[len("/hist/"):])
            return
        if path == "/api/log":
            try:
                with open(LOG_PATH, "rb") as f:
                    data = f.read()[-12000:]
                text = data.decode("utf-8", "replace")
            except Exception:
                text = "(no log yet)"
            self._json(200, {"ok": True, "log": text})
            return
        if path == "/api/update":
            # v817 (Grok R8 #2) — ops truth: how far behind origin is this install?
            # Cousins are git clones (installer does git clone/pull) — fetch is cheap + safe.
            try:
                subprocess.run(["git", "fetch", "origin", "main", "--quiet"],
                               cwd=REPO, capture_output=True, timeout=20)
                r = subprocess.run(["git", "rev-list", "HEAD..origin/main", "--count"],
                                   cwd=REPO, capture_output=True, timeout=10, text=True)
                behind = int((r.stdout or "0").strip() or 0)
                subj = ""
                if behind:
                    r2 = subprocess.run(["git", "log", "origin/main", "-1", "--format=%s"],
                                        cwd=REPO, capture_output=True, timeout=10, text=True)
                    subj = (r2.stdout or "").strip()[:120]
                self._json(200, {"ok": True, "behind": behind, "latest": subj,
                                 "howTo": ("git pull, then relaunch TV DIABLO" if behind else "")})
            except Exception as e:
                self._json(200, {"ok": False, "msg": "update check failed: %s" % e})
            return
        if path == "/api/doctor":
            # v801 (Grok R7) — Windows self-diagnosis: fast, read-only, never spawns the CLI.
            self._json(200, doctor_payload())
            return
        if path == "/api/farmgate":
            # v924 — FARM DAY gate: one button, one verdict (the only endpoint allowed a CLI ping)
            self._json(200, farmgate_payload())
            return
        if path.startswith("/api/export"):
            # v809 (Grok R7 wow #3) — 📼 NIGHT CARD: write the session recap to the Desktop.
            # User-triggered only (theatre button); JSON (full beats) + recap.md (CUT story).
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(self.path).query or "")
            try:
                n = int((q.get("n") or ["1"])[0])
            except Exception:
                n = 1
            sess = self._theatre_session(n)
            if not isinstance(sess, dict) or not sess.get("beats"):
                self._json(404, {"ok": False, "msg": "no such session"})
                return
            sid = (sess.get("sessionId") or ("session%d" % n)).replace("/", "_")[:40]
            desk = os.path.expanduser("~/Desktop")
            base = os.path.join(desk, "TVDIABLO_" + sid)
            try:
                # v812 (Grok R8 sleeper sibling) — the Night Card claims FULL: include the RAW
                # journal rows (farmed/unvault/gone_candidates/ocr_ms/interest/mode/tz/…), not
                # just the theatre projection. Filter by sessionId, else by capture-ts range.
                raw_rows = []
                try:
                    want_sid = sess.get("sessionId") or ""
                    t0r = (sess.get("t0") or 0) - 5000
                    t1r = (sess.get("t1") or 0) + 5000
                    _root = os.path.join(HERE, "sessions")
                    _paths = [_root + ".%d.jsonl" % g for g in range(5, 0, -1)] + [_root + ".jsonl"]
                    for _p in _paths:
                        if not os.path.isfile(_p):
                            continue
                        with open(_p, encoding="utf-8") as jf:
                            for line in jf:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    row = json.loads(line)
                                except Exception:
                                    continue
                                if want_sid:
                                    if row.get("sessionId") == want_sid:
                                        raw_rows.append(row)
                                elif t0r <= (row.get("ts") or 0) <= t1r:
                                    raw_rows.append(row)
                except Exception:
                    raw_rows = []
                sess = dict(sess)
                sess["raw"] = raw_rows
                with open(base + ".json", "w", encoding="utf-8") as f:
                    json.dump(sess, f, indent=1)
                beats = sess.get("beats") or []
                t0 = sess.get("t0") or (beats[0].get("ts") if beats else 0)
                lines = ["# 📼 TV DIABLO — Night Card · session %d" % n,
                         "_%s · %d reads_" % (time.strftime("%Y-%m-%d %H:%M", time.localtime((t0 or 0) / 1000)), len(beats)), ""]
                for b in beats:
                    keep = (b.get("vault_names") or b.get("discovered_names")
                            or b.get("thrown_names") or b.get("names") or b.get("farewell"))
                    if not keep:
                        continue
                    rel = max(0, (b.get("ts") or 0) - (t0 or 0))
                    stamp = "T+%d:%02d" % (rel // 60000, (rel % 60000) // 1000)
                    bits = []
                    for nm in (b.get("vault_names") or []):
                        bits.append("🏦 **" + nm + "**")
                    for nm in (b.get("discovered_names") or []):
                        bits.append("💬🏆 " + nm)
                    for nm in (b.get("thrown_names") or []):
                        bits.append("🗑 " + nm)
                    for nm in (b.get("pending_names") or []):
                        bits.append("⏳ " + nm)   # v812 — holds are part of the story
                    if not bits:
                        bits = [", ".join((b.get("names") or [])[:5]) or ("👋 farewell" if b.get("farewell") else "")]
                    lines.append("- `%s` · %s%s%s" % (stamp, (b.get("area") or "?"),
                                 (" · " + b.get("scene")) if b.get("scene") else "",
                                 (" — " + " · ".join(bits)) if any(bits) else ""))
                with open(base + ".md", "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")
                self._json(200, {"ok": True, "json": base + ".json", "md": base + ".md",
                                 "beats": len(beats)})
            except Exception as e:
                self._json(500, {"ok": False, "msg": str(e)})
            return
        self._json(404, {"ok": False, "msg": "not found"})

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length") or 0)
        body = {}
        if length:
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except Exception:
                body = {}

        if path == "/kai_verdict":
            # v940 🔬 — KAI's judge receipts: the engine iframe POSTs aicJudge results here.
            # Ghost-proof journaling: ts == captureTs == the FRAME's moment (passed as fts).
            try:
                _fts = int(body.get("fts") or 0) or int(time.time() * 1000)
                _vname = str(body.get("name") or "")[:60]
                _tier = str(((body.get("verdict") or {}).get("tier")) or "")[:12]
                # v940.1 GRAIL GATE — a known unique/set/runeword name is never a toss/border.
                # v943.2 — but EXCLUDE the generated rare-name combos: a rare "Beast Noose" is
                # recognized (register) yet CAN genuinely be a toss, so it must not auto-promote.
                _vlow = _vname.lower()
                if _vname and _vlow in _kai_fullnames() and _vlow not in _kai_rarenames() and _tier in ("toss", "border"):
                    _tier = "grail"
                rec = {"ts": _fts, "captureTs": _fts, "completedTs": int(time.time() * 1000),
                       "n": 0, "scene": "kai", "lane": "kai", "mode": "kai-judge", "names": [],
                       "area": "", "sessionId": str(body.get("sid") or "")[:48],
                       "frameId": str(body.get("frameId") or "")[:64],
                       "kai": {"judge": {"name": _vname, "base": str(body.get("base") or "")[:40],
                                          "q": str(body.get("q") or "")[:12], "tier": _tier,
                                          "score": int((body.get("verdict") or {}).get("score") or 0),
                                          "ok": bool(body.get("ok", False)),
                                          "why": str(body.get("why") or "")[:120]}},
                       "note": ("🔬 KAI judged " + (_vname or "a tooltip") + " — " + (_tier.upper() or "UNREADABLE"))[:100]}
                with open(os.path.join(HERE, "sessions.jsonl"), "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                self._json(200, {"ok": True})
            except Exception as e:
                self._json(200, {"ok": False, "msg": str(e)[:120]})
            return
        if path == "/intake_result":
            # v935 (Konyo P0: 'tallies silently vanishing') — the board POSTs each auto-intake
            # RESULT to the agent bridge (:17771), but the bridge DIES at session end, so a tally
            # that completes AFTER END SESSION loses its receipt forever (driver proved fired=1,
            # intakes journaled=0). Control's HTTP server outlives the agent — accept the receipt
            # here and journal it in the SAME shape tv_diablo.bridge() do_POST does, tagged to the
            # latest known sessionId from the journal. Dedupe so a receipt landing on BOTH bridges
            # (agent still up) is only journaled once.
            try:
                now_ms = int(time.time() * 1000)
                _ts = int(body.get("ts") or now_ms)
                _tab = str(body.get("tab") or "")[:24]
                _fid = str(body.get("frameId") or "")[:48]
                try:
                    _rows = _kai_journal_rows()
                except Exception:
                    _rows = []
                _sid = ""
                for r in _rows:
                    s = r.get("sessionId")
                    if s:
                        _sid = s   # latest sessionId wins (rows are append-ordered)
                # v935.11 R3 (Grok dedupe verdict) — the ±5min frame+tab dedupe was too greedy:
                # (a) an empty frameId carries no identity, so those receipts must ALWAYS journal
                #     (never collapse two anonymous shots into one); (b) a re-tally of the SAME
                #     frame+tab with DIFFERENT counts is a genuine correction, not a dup, so the
                #     match now also requires an identical counts signature. Only the exact triple
                #     (frameId, tab, counts-sig) within ±5min is a true duplicate.
                _counts = body.get("counts") if isinstance(body.get("counts"), dict) else {}
                _csig = json.dumps([_counts, bool(body.get("ok", True)), int(body.get("total") or 0), int(body.get("errors") or 0)], sort_keys=True)   # v936 Grok: fail↔zero-read flips must journal
                if _fid:
                    for r in _rows:
                        if (r.get("lane") == "intake"
                                and str(r.get("frameId") or "") == _fid
                                and str((r.get("intake") or {}).get("tab") or "") == _tab
                                and json.dumps([(r.get("intake") or {}).get("counts") or {},
                                                bool((r.get("intake") or {}).get("ok", True)),
                                                int((r.get("intake") or {}).get("total") or 0),
                                                int((r.get("intake") or {}).get("errors") or 0)],
                                               sort_keys=True) == _csig   # v938.7 — SAME SHAPE both sides (test-routes caught the dead compare)
                                and abs(int(r.get("ts") or 0) - _ts) <= 300_000):
                            self._json(200, {"ok": True, "dup": True})
                            return
                rec = {
                    "ts": _ts, "captureTs": _ts, "completedTs": now_ms,
                    "n": 0, "scene": "intake", "lane": "intake", "mode": "intake",
                    "names": [], "area": "", "sessionId": _sid,
                    "intake": {
                        "tab": _tab,
                        "kind": str(body.get("kind") or "")[:16],
                        "counts": _counts,
                        "total": int(body.get("total") or 0),
                        "errors": int(body.get("errors") or 0),
                        "items": (body.get("items") or [])[:60],
                        "ok": bool(body.get("ok", True)),
                    },
                    "frameId": _fid,
                    "note": ("📸 intake · " + str(body.get("tab") or body.get("kind") or "shot"))[:80],
                }
                with open(os.path.join(HERE, "sessions.jsonl"), "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                self._json(200, {"ok": True})
            except Exception as e:
                self._json(500, {"ok": False, "msg": str(e)[:160]})
            return

        if path in ("/api/intake", "/api/ask"):
            # v874 (Konyo: 'Forge image AI intake uploads broken in the app console') — the board
            # posts to a RELATIVE /api/intake, which only exists as a Cloudflare function on the
            # live site. In-app (Mac AND Windows) that hit this server and 404'd. Proxy to
            # production with the site's Basic gate (password-only check, username free).
            # v874 — SUBSCRIPTION LANE FIRST (Konyo: 'use the subscription, not API tokens'):
            # tv/intake_local.mjs runs the REAL intake.js/ask.js with a fetch shim that rides
            # the locally-authorized `claude` CLI. Website proxy = fallback only.
            _runner = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intake_local.mjs")
            # v919 (Grok REAL EYES R1) — STRICT mode: a silent local-lane failure falling
            # through to the website proxy can fake-green a "real subscription" run on the
            # website's key. TV_INTAKE_LOCAL_STRICT=1 → answer 502 honestly, never fall back.
            _strict = os.environ.get("TV_INTAKE_LOCAL_STRICT") == "1"
            if os.environ.get("TV_INTAKE_LOCAL", "1") != "0" and os.path.isfile(_runner):
                try:
                    _nice_kw = ({"creationflags": 0x4000 | _WIN_CREATE} if IS_WIN
                                else {"preexec_fn": (lambda: os.nice(10))})   # v879 — intake yields to the game
                    _pr = subprocess.run(
                        ["node", _runner],
                        input=json.dumps({"path": path, "body": body}).encode("utf-8"),
                        capture_output=True, timeout=150, **_nice_kw)
                    if _pr.returncode == 0 and _pr.stdout:
                        _out = json.loads(_pr.stdout.decode("utf-8", "replace"))
                        _pl = (_out.get("body") or "").encode("utf-8")
                        self.send_response(int(_out.get("status") or 200))
                        self.send_header("Content-Type", "application/json")
                        self.send_header("X-Intake-Lane", "subscription")
                        self.send_header("Content-Length", str(len(_pl)))
                        self.end_headers()
                        self.wfile.write(_pl)
                        return
                    if _strict:
                        _err = (_pr.stderr or b"").decode("utf-8", "replace")[-300:]
                        self._json(502, {"ok": False, "lane": "subscription-failed",
                                         "msg": "local intake runner failed (strict: no website fallback)",
                                         "detail": _err})
                        return
                except Exception as _ex:
                    if _strict:
                        self._json(502, {"ok": False, "lane": "subscription-failed",
                                         "msg": "local intake runner error (strict): " + str(_ex)[:200]})
                        return
                    pass   # any local failure → website proxy below
            elif _strict:
                self._json(502, {"ok": False, "lane": "subscription-failed",
                                 "msg": "local intake lane disabled/missing (strict: no website fallback)"})
                return
            try:
                # do_POST already consumed rfile into `body` — a second read blocks forever
                body_in = json.dumps(body).encode("utf-8")
                import base64 as _b64
                req = urllib.request.Request(
                    "https://bull-4-u.com" + path,
                    data=body_in,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "TVD-Console/1.0",   # CF WAF 403s python-urllib's default UA
                        "Authorization": "Basic " + _b64.b64encode(b"app:DeanDiablo").decode(),
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=120) as r:
                    out = r.read()
                    self.send_response(r.status)
                    self.send_header("Content-Type", r.headers.get("Content-Type") or "application/json")
                    self.send_header("Content-Length", str(len(out)))
                    self.end_headers()
                    self.wfile.write(out)
            except urllib.error.HTTPError as e:
                out = e.read() if hasattr(e, "read") else b'{"ok":false}'
                self._json(e.code, {"ok": False, "msg": "intake upstream %d" % e.code,
                                    "detail": out.decode("utf-8", "replace")[:300]})
            except Exception as e:
                self._json(502, {"ok": False, "msg": "intake proxy failed — is the Mac online? " + str(e)[:200]})
            return
        if path == "/api/session/delete":
            # v834 (Konyo: 'an option to delete a session if i want to') — POST {n} removes that
            # session's journal rows (across the generation ring) + its hist frames + footage in
            # its window. User-initiated, session-scoped, never touches other reels.
            try:
                n = int(body.get("n") or 0)
                sess = self._theatre_session(n)
                if not isinstance(sess, dict) or not sess.get("beats"):
                    self._json(404, {"ok": False, "msg": "no such session"})
                    return
                sid = sess.get("sessionId") or ""
                t0d = (sess.get("t0") or 0) - 2000
                t1d = (sess.get("t1") or 0) + 2000
                _root = os.path.join(HERE, "sessions")
                removed = 0
                fids = set()
                for _p in [_root + ".%d.jsonl" % g for g in range(5, 0, -1)] + [_root + ".jsonl"]:
                    if not os.path.isfile(_p):
                        continue
                    keep_lines = []
                    with open(_p, encoding="utf-8") as jf:
                        for line in jf:
                            raw_l = line.rstrip("\n")
                            if not raw_l.strip():
                                continue
                            try:
                                row = json.loads(raw_l)
                            except Exception:
                                keep_lines.append(raw_l)
                                continue
                            mine = (sid and row.get("sessionId") == sid) or \
                                   ((not sid) and t0d <= (row.get("ts") or 0) <= t1d)
                            if mine:
                                removed += 1
                                if row.get("frameId"):
                                    fids.add(str(row["frameId"]))
                            else:
                                keep_lines.append(raw_l)
                    tmp_p = _p + ".tmp"
                    with open(tmp_p, "w", encoding="utf-8") as jf:
                        jf.write("\n".join(keep_lines) + ("\n" if keep_lines else ""))
                    os.replace(tmp_p, _p)
                # frames: read frames by id + footage frames inside the window
                hist_dir = HIST_DIR
                killed_frames = 0
                if os.path.isdir(hist_dir):
                    for fn in os.listdir(hist_dir):
                        if not fn.endswith(".jpg"):
                            continue
                        base = fn[:-4]
                        kill = base in fids
                        if not kill and fn.startswith("f_"):
                            try:
                                kill = t0d <= int(base[2:]) <= t1d
                            except Exception:
                                kill = False
                        if kill:
                            for sub in ("", "cache1280", "cache160"):
                                try:
                                    os.remove(os.path.join(hist_dir, sub, fn) if sub else os.path.join(hist_dir, fn))
                                    if not sub:
                                        killed_frames += 1
                                except Exception:
                                    pass
                self._json(200, {"ok": True, "removedReads": removed, "removedFrames": killed_frames,
                                 "sessionId": sid})
            except Exception as e:
                self._json(500, {"ok": False, "msg": str(e)})
            return
        if path == "/api/on":
            # v891 (Grok C3) — DISK PREFLIGHT: below the floor the reaper can't keep a reel
            # alive; refuse loudly with the exact ask instead of recording a doomed session.
            try:
                import shutil as _shd
                _free = _shd.disk_usage(HIST_DIR).free / 1e9
                if _free < 8.0:
                    self._json(200, {"ok": False, "mode": "off",
                                     "error": "DISK TOO FULL to record — %.1fGB free, need 8GB. Free ~%.0fGB and press ON AIR again." % (_free, 9 - _free)})
                    return
            except Exception:
                pass
            if _stop_inflight:
                # v899 — if the agent is already dead, clear the latch and allow ON
                if not _agent_alive() and _port_listener_pid() is None:
                    globals()["_stop_inflight"] = False
                    # Must use globals() — bare assign makes _agent_mode local to all of
                    # do_POST (UnboundLocalError on any later read; module mode never clears).
                    globals()["_agent_mode"] = "off"
                else:
                    self._json(200, {"ok": False, "msg": "still shutting down — session saving; try ON again in a moment",
                                     "mode": "stopping", "error": "still stopping"})
                    return
            r = start_agent(sim=False, test=bool(body.get("test")))
            _console_beacon_async("onair")   # v875 — the dashboard flips 🔴 within seconds
            self._json(200, r)   # v778-pre — ON opens NOTHING (one-window world)
            return
        if path == "/api/sim":
            if _stop_inflight:
                self._json(200, {
                    "ok": False,
                    "msg": "still shutting down — try again in a moment",
                    "mode": "stopping",
                })
                return
            if _agent_alive():
                stop_agent(farewell=False)
                time.sleep(0.4)
            r = start_agent(sim=True)
            self._json(200, r)
            return
        if path == "/api/off":
            # v847 — OFF seals the session (session_end) WITHOUT long farewell vision, then kills.
            # v926.2 — ALWAYS answer with JSON: a raised stop must never leave END SESSION with an
            # empty response (the real "i cant end session" bug — stop_agent threw, the handler
            # wrote nothing, the board hung). On any failure, hard-kill and report honestly.
            try:
                r = stop_agent(farewell=False)
            except Exception as _e:
                r = _force_kill_all_agents("off (stop_agent raised: %s)" % str(_e)[:120])
            _console_beacon_async("off")   # v875
            self._json(200, r)
            return
        if path == "/api/stop":
            try:
                r = stop_agent(farewell=False)   # v926 LIGHT — never a farewell vision read on End Session
            except Exception as _e:
                r = _force_kill_all_agents("stop (stop_agent raised: %s)" % str(_e)[:120])
            self._json(200, r)
            return
        if path == "/api/restart":
            if _stop_inflight:
                self._json(200, {"ok": False, "msg": "still shutting down — try again in a moment", "mode": "stopping"})
                return
            stop_agent(farewell=False)
            time.sleep(0.4)
            r = start_agent(sim=False)
            self._json(200, r)
            return
        if path == "/api/board":
            # v781 — ONE WINDOW by default: return a same-origin nav target. The UI navigates
            # THIS pywebview to /board?app=1#tab. Spawning a second native window is opt-in
            # only (?popout=1) for the rare explicit pop-out case — never for console buttons.
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            tab = (q.get("tab") or ["session"])[0]
            # v904 (Konyo: 'TV·D is a smooth TOGGLE') — an EXPLICIT #tvd opens the live view;
            # only the legacy on/off aliases land on SESSIONS
            if tab in ("tvd-on", "tvd-off"):
                tab = "session"
            if tab not in ("session", "tools", "forge", "funi", "fsets", "tvd"):
                tab = "session"
            popout = (q.get("popout") or ["0"])[0] in ("1", "true", "yes")
            if popout:
                self._json(200, open_board(auto_on=True, tab=tab))
                return
            self._json(200, {
                "ok": True,
                "msg": "same-window nav",
                "nav": "/board?app=1#%s" % tab,
                "tab": tab,
                "spawned": False,
            })
            return
        if path == "/api/quit":
            threading.Thread(
                target=lambda: (time.sleep(0.3), os._exit(0)), daemon=True
            ).start()
            self._json(200, {"ok": True, "msg": "control quitting"})
            return
        self._json(404, {"ok": False, "msg": "not found"})


def _loud_fail(title, msg):
    """v770 — pythonw has no console: a native-window failure must SHOUT, not vanish."""
    try:
        if IS_WIN:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, msg, title, 0x10)   # MB_ICONERROR
        elif sys.platform == "darwin":
            subprocess.run(["osascript", "-e",
                            f'display alert "{title}" message "{msg}" as critical'],
                           capture_output=True, timeout=10)
    except Exception:
        pass


def board_window():
    """v767.1 — dedicated native window for the LOCAL board (file:// bible.html#tvd).
    v773.2 — orphan guard: if the control server disappears for ~60s, this window self-closes
    (the REG-020 swarm can never rebuild from forgotten windows)."""
    def _orphan_watch():
        misses = 0
        while True:
            time.sleep(20)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{CONTROL_PORT}/api/status", timeout=3):
                    misses = 0
            except Exception:
                misses += 1
                if misses >= 3:
                    os._exit(0)
    threading.Thread(target=_orphan_watch, daemon=True).start()
    # v774 🌙 — same-origin host + deep-link hash (--hash=forge etc.)
    tab = "session"
    for a in sys.argv:
        if a.startswith("--hash="):
            tab = a.split("=", 1)[1] or "session"
    if tab in ("tvd", "tvd-on", "tvd-off"):
        tab = "session"
    url = "http://127.0.0.1:%d/board#%s" % (CONTROL_PORT, tab)
    try:
        import webview
        webview.create_window(
            "TV DIABLO — Board",
            url=url,
            width=1500,
            height=980,
            min_size=(1080, 700),
            background_color="#060504",
        )
        webview.start()
    except Exception as e:
        _loud_fail(
            "TV DIABLO",
            f"Native board window crashed: {e}\n\n"
            f"Opening in your browser instead.\nLog: {LOG_PATH}",
        )
        _open_browser_app_fallback(url)


def main():
    if "--board-window" in sys.argv:
        board_window()
        return
    open_ui = "--open" in sys.argv or "-o" in sys.argv
    no_open = "--no-open" in sys.argv
    # --window-only: attach a native window to an already-running control server
    window_only = "--window-only" in sys.argv

    if window_only:
        # Secondary attach: do NOT kill ON AIR when this window closes (primary owns it).
        globals()["_WINDOW_ONLY"] = True
        open_control_window()
        return

    try:
        srv = ThreadingHTTPServer(("127.0.0.1", CONTROL_PORT), Handler)
    except OSError as e:
        # v781 — ONE WINDOW: a second Desktop launch used to open another pywebview on the
        # already-running control (Konyo: 'another window open sometimes'). Refuse.
        print(
            f"📺 TV DIABLO is already running on :{CONTROL_PORT} — not opening a second window.\n"
            f"   Use the existing app (or STOP/quit it first).\n   ({e})"
        )
        try:
            if sys.platform == "darwin":
                subprocess.run(
                    ["osascript", "-e",
                     'display notification "TV DIABLO is already open — use the existing window." '
                     'with title "TV DIABLO"'],
                    capture_output=True, timeout=5,
                )
        except Exception:
            pass
        sys.exit(0)

    plat = "windows" if IS_WIN else ("mac" if sys.platform == "darwin" else sys.platform)
    print(f"📺 TV DIABLO Control v935.8 · {plat} · native window · http://127.0.0.1:{CONTROL_PORT}/", flush=True)
    print(f"   agent bridge :{AGENT_PORT} · log {LOG_PATH}", flush=True)
    if IS_WIN:
        print("   Windows ON = capture_win.ps1 (hidden) + tv_diablo.py --watch", flush=True)
    print("   close the app window → auto-stops ON AIR (exit safeguard · same as tvd stop).", flush=True)

    # v935.8 — reclaim orphans left by a prior crash/close (the "always on" feeling)
    try:
        if _port_listener_pid() is not None or _agent_alive():
            print("📺 reclaiming orphan ON AIR from a previous session…", flush=True)
            _force_kill_all_agents("boot-orphan-reclaim")
    except Exception as _oe:
        print(f"⚠ orphan reclaim skipped: {_oe}", flush=True)

    # v935.8 — process-level safeguards (window path also wired in open_control_window)
    import atexit
    atexit.register(lambda: _console_exit_stop_onair("atexit"))

    def _sig_exit(signum, _frame):
        try:
            name = signal.Signals(signum).name
        except Exception:
            name = str(signum)
        _console_exit_stop_onair("signal-%s" % name)
        try:
            srv.shutdown()
        except Exception:
            pass
        # 0 = clean; avoid re-entrant signal handlers looping
        os._exit(0)

    try:
        signal.signal(signal.SIGTERM, _sig_exit)
        signal.signal(signal.SIGINT, _sig_exit)
    except Exception:
        pass

    threading.Thread(target=_bridge_prober, daemon=True, name="tvd-prober").start()   # v872
    threading.Thread(target=_console_beacon_loop, daemon=True, name="tvd-beacon").start()   # v875
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.2)

    if open_ui and not no_open:
        # Blocks until the native window is closed; open_control_window stops ON AIR on return
        open_control_window()
        _console_exit_stop_onair("main-after-window")
        try:
            srv.shutdown()
        except Exception:
            pass
        return

    # headless server mode (tests / --no-open)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n📺 control UI server stopping — exit safeguard cuts ON AIR.")
        _console_exit_stop_onair("keyboard-interrupt")
        srv.shutdown()


if __name__ == "__main__":
    main()
