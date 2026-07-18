#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# 📺 TV DIABLO — Control App (Mac + Windows · v831)
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

import inspect
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
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
HIST_DIR = os.path.join(HERE, "frames", "hist")   # v765 — the theatre's film archive
BOARD_PID_PATH = os.path.join(HERE, "board_window.pid")   # v773.1 — the ONE board window

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
    return _port_listener_pid() is not None


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
    sig = signal.SIGKILL if force else signal.SIGTERM
    try:
        os.killpg(pid, sig)
    except ProcessLookupError:
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            pass
    except Exception:
        try:
            os.kill(pid, sig)
        except Exception:
            pass


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
    with _lock:
        if _agent_proc is not None and _agent_proc.poll() is None:
            return {"ok": True, "msg": "already running", "mode": _agent_mode}
        if _port_listener_pid() is not None:
            _agent_mode = "sim" if sim else "live"
            return {"ok": True, "msg": "bridge already live", "mode": _agent_mode}

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


def stop_agent(farewell=True):
    global _agent_proc, _agent_mode, _stop_inflight, _BOARD_OPENED
    _stop_inflight = True
    try:
        pid = None
        with _lock:
            if _agent_proc is not None and _agent_proc.poll() is None:
                pid = _agent_proc.pid
            else:
                pid = _port_listener_pid() or _read_pid(PID_PATH)

        if pid is None and not IS_WIN:
            _agent_mode = "off"
            _stop_capture()
            _BOARD_OPENED = False
            return {"ok": True, "msg": "already off"}

        if pid is not None:
            # Soft first so the farewell can run. Windows: taskkill-soft sends WM_CLOSE, which a
            # CREATE_NO_WINDOW console app never receives — our OWN child must get CTRL_BREAK_EVENT
            # (it was spawned CREATE_NEW_PROCESS_GROUP; the agent handles SIGBREAK since v760.1).
            sent_break = False
            if IS_WIN:
                with _lock:
                    if (
                        _agent_proc is not None
                        and _agent_proc.poll() is None
                        and _agent_proc.pid == pid
                    ):
                        try:
                            _agent_proc.send_signal(signal.CTRL_BREAK_EVENT)
                            sent_break = True
                        except Exception:
                            pass
            if not sent_break:
                _kill_pid(pid, force=False)

            wait_s = 90 if farewell else 12
            deadline = time.time() + wait_s
            while time.time() < deadline:
                if not _pid_alive(pid):
                    break
                time.sleep(0.25)
            else:
                _kill_pid(pid, force=True)

        # always stop Windows capture with the agent
        _stop_capture()

        with _lock:
            _agent_proc = None
            _agent_mode = "off"
        try:
            if os.path.isfile(PID_PATH):
                os.remove(PID_PATH)
        except Exception:
            pass
        # v785 — belt for the agent's own _eye_clear: a force-killed agent can't clean up,
        # and a stale eye.jpg makes the next ON flash yesterday's film as LIVE.
        try:
            _eye = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames", "eye.jpg")
            if os.path.isfile(_eye):
                os.remove(_eye)
        except Exception:
            pass
        # v773 — next ON/SIM may open the board again; session is dark
        _BOARD_OPENED = False
        return {"ok": True, "msg": "stopped", "farewell": farewell}
    finally:
        # never leave the gate stuck if anything above raises
        _stop_inflight = False


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

def _open_board_native(tab="tvd"):
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
            [sys.executable, os.path.abspath(__file__), "--board-window", "--hash=" + (tab or "tvd")],
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

def open_board(auto_on=True, tab="tvd"):
    """Open the bible TV·D tab. v764: the board AUTO-SYNCS to the bridge now (lamp + probe),
    so the deep link only needs to LAND on #tvd — and macOS `open` DROPS file:// fragments
    (the 'routes me to the wrong page' bug), so prefer a direct browser spawn like Windows."""
    if not os.path.isfile(BIBLE):
        return {"ok": False, "msg": "bible.html missing"}
    if _open_board_native(tab):
        return {"ok": True, "msg": "board opened (native window)", "tab": tab}
    url = _file_url(BIBLE, "tvd")
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
            webview.create_window(**kwargs, icon=icon)
        else:
            webview.create_window(**kwargs)
    except TypeError:
        webview.create_window(
            title="TV DIABLO",
            url=url,
            width=1120,
            height=800,
            min_size=(880, 600),
            background_color="#070605",
        )

    # private_mode=False so localStorage works if we ever need it in the UI
    try:
        webview.start(debug=False)
    except Exception as e:
        print(f"⚠ pywebview failed ({e}) — browser fallback")
        _open_browser_app_fallback(url)


def status_payload():
    bridge = _bridge_ping() is not None
    st = _bridge_state() if bridge else None
    mode = _agent_mode
    if bridge and mode == "off":
        mode = "live"
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
        "ver": "v831",
        "platform": "windows" if IS_WIN else ("mac" if sys.platform == "darwin" else sys.platform),
        "shell": "pywebview",
        "mode": ("stopping" if _stop_inflight else mode),
        "agent": mode != "off" and bridge,
        "bridge": bridge,
        "pid": _port_listener_pid(),
        "capture": bool(IS_WIN and (_read_pid(CAP_PID_PATH) and _pid_alive(_read_pid(CAP_PID_PATH)))),
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
                    m = re.search(r"id:'(v\d+)'", line)
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
        m = re.search(r'"ver": "(v\d+)"', inspect.getsource(status_payload))
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
        _jl = os.path.join(HERE, "sessions.jsonl")
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
            checks.append(_chk(
                "session_integrity", pct >= 60, "warn",
                "frames %d%% of %d reads · sessionId %d/%d" % (pct, len(with_fid), sid_cov, len(rows)),
                "old frames pruned is normal; 0%% on a FRESH night = archive_read_frame broken"))
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

    def _theatre_sessions(self):
        """v765 — REPLAY THEATRE: list journaled sessions (newest first) from tv/sessions.jsonl."""
        try:
            if HERE not in sys.path:
                sys.path.insert(0, HERE)
            import replay as _rp
            sessions = _rp.split_sessions(_rp.load_journal())
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
                out.append({"n": i, "t0": sess[0].get("ts"), "t1": sess[-1].get("ts"),
                            "reads": len(sess), "frames": len(frames),
                            "named": sum(1 for r in sess if r.get("names")),
                            "areas": areas[:6], "sessionId": sid})
            return out
        except Exception as e:
            return {"error": str(e)}

    def _theatre_session(self, n):
        try:
            if HERE not in sys.path:
                sys.path.insert(0, HERE)
            import replay as _rp
            sessions = _rp.split_sessions(_rp.load_journal())
            if n < 1 or n > len(sessions):
                return {"error": "no such session"}
            sess = sessions[n - 1]
            beats = []
            for r in sess:
                fid = r.get("frameId") or ""
                has = bool(fid) and os.path.isfile(os.path.join(HIST_DIR, fid + ".jpg"))
                # v784 — capture clock is source of truth for scrub order + film lock
                fts = None
                if fid and "_" in str(fid):
                    try:
                        fts = int(str(fid).rsplit("_", 1)[-1])
                    except Exception:
                        fts = None
                if r.get("captureTs"):
                    cap_ts = int(r["captureTs"])
                elif fts is not None:
                    # pre-v784 rows often stored completion as ts — frameId suffix is the photo clock
                    raw_ts = int(r.get("ts") or 0)
                    if raw_ts and abs(raw_ts - fts) > 2000:
                        cap_ts = fts
                    else:
                        cap_ts = raw_ts or fts
                else:
                    cap_ts = r.get("ts")
                done_ts = r.get("completedTs") or r.get("ts") or cap_ts
                beats.append({
                    "ts": cap_ts,  # primary scrub key = CAPTURE
                    "captureTs": cap_ts,
                    "completedTs": done_ts,
                    "n": r.get("n"), "scene": r.get("scene", ""),
                    "area": r.get("area", ""), "names": r.get("names", []),
                    "note": r.get("note", ""), "frame": (fid + ".jpg") if has else "",
                    "frameId": fid,
                    "frameOk": has,  # exact hist file present
                    "sessionId": r.get("sessionId") or "",
                    "ms": r.get("ms", 0), "lane": r.get("lane", ""),
                    "model": r.get("model", ""),
                    "vault_names": r.get("vault_names") or [],
                    "pending_names": r.get("pending_names") or [],
                    "thrown_names": r.get("thrown_names") or [],
                    "discovered_names": r.get("discovered_names") or [],
                    "intent": r.get("intent", ""), "stashTab": r.get("stashTab", ""),
                    "farewell": bool(r.get("farewell")),
                    # v797 — FULL FORENSICS (Konyo: 'exactly what was analyzed per frame')
                    "ocr_names": r.get("ocr_names") or [],
                    "ocr_ms": r.get("ocr_ms") or 0,   # v823 (Grok R9 sleeper #8) — the fast lane gets its clock
                    "names_loc": r.get("names_loc") or {},          # v830 — per-name location truth
                    "equipped_names": r.get("equipped_names") or [],
                    "confirmed_names": r.get("confirmed_names") or [],
                    "ocr_seeded": r.get("ocr_seeded") or [],
                    "conf": r.get("conf"),
                    "lifecycle_tags": r.get("lifecycle_tags") or {},
                    "sim": bool(r.get("sim")),
                })
            # v826 — FOOTAGE interleave: 1fps eye frames within this session's window become
            # film-only beats; the reel plays as real video with AI reads annotating over it.
            try:
                t0f = (sess[0].get("ts") or 0) - 2000
                t1f = (sess[-1].get("ts") or 0) + 2000
                hist_dir = os.path.join(HERE, "frames", "hist")
                if os.path.isdir(hist_dir):
                    for fn in os.listdir(hist_dir):
                        if not (fn.startswith("f_") and fn.endswith(".jpg")):
                            continue
                        try:
                            fts = int(fn[2:-4])
                        except Exception:
                            continue
                        if t0f <= fts <= t1f:
                            beats.append({"ts": fts, "captureTs": fts, "footage": True,
                                          "frame": fn, "frameId": fn[:-4], "names": [],
                                          "scene": "", "area": "", "lane": "footage"})
            except Exception:
                pass
            # chronological by capture time (never scramble OCR/deep order)
            beats.sort(key=lambda b: (b.get("ts") or 0, b.get("n") or 0))
            sid = next((r.get("sessionId") for r in sess if r.get("sessionId")), "")
            return {"n": n, "beats": beats, "sessionId": sid,
                    "t0": beats[0].get("ts") if beats else sess[0].get("ts"),
                    "t1": beats[-1].get("ts") if beats else sess[-1].get("ts")}
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
        if path.startswith("/api/session"):
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            try:
                num = int((q.get("n") or ["1"])[0])
            except Exception:
                num = 1
            self._json(200, self._theatre_session(num))
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

        if path == "/api/on":
            if _stop_inflight:
                self._json(200, {"ok": False, "msg": "farewell still finishing — try again in a moment", "mode": "stopping"})
                return
            r = start_agent(sim=False, test=bool(body.get("test")))
            self._json(200, r)   # v778-pre — ON opens NOTHING (one-window world)
            return
        if path == "/api/sim":
            if _stop_inflight:
                self._json(200, {
                    "ok": False,
                    "msg": "farewell still finishing — try again in a moment",
                    "mode": "stopping",
                })
                return
            if _agent_alive():
                stop_agent(farewell=False)
                time.sleep(0.4)
            r = start_agent(sim=True)
            # v776.1 (Konyo) — SIM opens NOTHING: one-window world, the app IS the view
            self._json(200, r)
            return
        if path == "/api/off":
            # v767.1 (Konyo's button audit) — OFF opens NOTHING (the board auto-syncs dark), and
            # the response returns IMMEDIATELY: the stop runs in a thread so the UI's lamp/glow
            # can follow the state honestly instead of jamming in 'working'.
            threading.Thread(target=stop_agent, kwargs={"farewell": False}, daemon=True).start()
            self._json(200, {"ok": True, "msg": "stopping (no farewell)"})
            return
        if path == "/api/stop":
            # v765/v767.1 — STOP never opens windows; farewell only for live runs; async so the
            # button shows 'farewell…' while the STATE (not a stuck spinner) tells the story.
            threading.Thread(target=stop_agent, kwargs={"farewell": (_agent_mode != "sim")}, daemon=True).start()
            self._json(200, {"ok": True, "msg": "stopping — farewell read may take up to ~90s"})
            return
        if path == "/api/restart":
            if _stop_inflight:
                self._json(200, {"ok": False, "msg": "farewell still finishing — try again in a moment", "mode": "stopping"})
                return
            stop_agent(farewell=False)
            time.sleep(0.5)
            r = start_agent(sim=False)
            self._json(200, r)   # v778-pre — RESTART opens NOTHING either
            return
        if path == "/api/board":
            # v781 — ONE WINDOW by default: return a same-origin nav target. The UI navigates
            # THIS pywebview to /board?app=1#tab. Spawning a second native window is opt-in
            # only (?popout=1) for the rare explicit pop-out case — never for console buttons.
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            tab = (q.get("tab") or ["tvd"])[0]
            if tab not in ("tvd", "session", "tools", "forge", "funi", "fsets"):
                tab = "tvd"
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
    tab = "tvd"
    for a in sys.argv:
        if a.startswith("--hash="):
            tab = a.split("=", 1)[1] or "tvd"
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
    print(f"📺 TV DIABLO Control v831 · {plat} · native window · http://127.0.0.1:{CONTROL_PORT}/")
    print(f"   agent bridge :{AGENT_PORT} · log {LOG_PATH}")
    if IS_WIN:
        print("   Windows ON = capture_win.ps1 (hidden) + tv_diablo.py --watch")
    print("   close the app window to quit control (agent left as-is unless you STOP).")

    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.2)

    if open_ui and not no_open:
        # Blocks until the native window is closed
        open_control_window()
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
        print(
            "\n📺 control UI server stopping (agent left as-is — use STOP in the app)."
        )
        srv.shutdown()


if __name__ == "__main__":
    main()
