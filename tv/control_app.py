#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# 📺 TV DIABLO — Control App (Mac + Windows · v761 real native window)
#
#   HD grimoire UI · ON / OFF / STOP / RESTART / SIM · agent HIDDEN.
#   Window: pywebview (real OS app window — NOT Chrome). Browser is fallback only.
#   Mac:     python3 tv/control_app.py --open  ·  TV DIABLO.app
#   Windows: pythonw tv/control_app.py --open · Desktop shortcut
#            ON = capture_win.ps1 (hidden) + tv_diablo.py --watch
# ═══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import json
import os
import signal
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


def start_agent(sim=False):
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
            popen_kw["start_new_session"] = True

        _agent_proc = subprocess.Popen(**popen_kw)
        _write_pid(PID_PATH, _agent_proc.pid)
        _agent_mode = "sim" if sim else "live"

    for _ in range(50):
        if _bridge_ping() is not None:
            break
        time.sleep(0.15)
    return {
        "ok": True,
        "msg": "started",
        "mode": _agent_mode,
        "pid": _agent_proc.pid if _agent_proc else None,
        "platform": "windows" if IS_WIN else "mac",
        "watch": IS_WIN,
    }


def stop_agent(farewell=True):
    global _agent_proc, _agent_mode
    pid = None
    with _lock:
        if _agent_proc is not None and _agent_proc.poll() is None:
            pid = _agent_proc.pid
        else:
            pid = _port_listener_pid() or _read_pid(PID_PATH)

    if pid is None and not IS_WIN:
        _agent_mode = "off"
        _stop_capture()
        return {"ok": True, "msg": "already off"}

    if pid is not None:
        # Soft first so the farewell can run. Windows: taskkill-soft sends WM_CLOSE, which a
        # CREATE_NO_WINDOW console app never receives — our OWN child must get CTRL_BREAK_EVENT
        # (it was spawned CREATE_NEW_PROCESS_GROUP; the agent handles SIGBREAK since v760.1).
        sent_break = False
        if IS_WIN:
            with _lock:
                if _agent_proc is not None and _agent_proc.poll() is None and _agent_proc.pid == pid:
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
    return {"ok": True, "msg": "stopped", "farewell": farewell}


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

def open_board(auto_on=True):
    """Open the bible TV·D tab. v764: the board AUTO-SYNCS to the bridge now (lamp + probe),
    so the deep link only needs to LAND on #tvd — and macOS `open` DROPS file:// fragments
    (the 'routes me to the wrong page' bug), so prefer a direct browser spawn like Windows."""
    if not os.path.isfile(BIBLE):
        return {"ok": False, "msg": "bible.html missing"}
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
        "ver": "v765",
        "platform": "windows" if IS_WIN else ("mac" if sys.platform == "darwin" else sys.platform),
        "shell": "pywebview",
        "mode": mode,
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
                out.append({"n": i, "t0": sess[0].get("ts"), "t1": sess[-1].get("ts"),
                            "reads": len(sess), "frames": len(frames),
                            "named": sum(1 for r in sess if r.get("names")),
                            "areas": areas[:6]})
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
                beats.append({"ts": r.get("ts"), "n": r.get("n"), "scene": r.get("scene", ""),
                              "area": r.get("area", ""), "names": r.get("names", []),
                              "note": r.get("note", ""), "frame": (fid + ".jpg") if has else "",
                              "ms": r.get("ms", 0), "lane": r.get("lane", "")})
            return {"n": n, "beats": beats}
        except Exception as e:
            return {"error": str(e)}

    def _serve_hist(self, name):
        """Serve an archived session frame (tv/frames/hist) — path-safe, jpg only."""
        from urllib.parse import unquote
        rel = unquote(name).split("?", 1)[0].split("#", 1)[0]
        target = os.path.realpath(os.path.join(HIST_DIR, rel))
        if not target.startswith(os.path.realpath(HIST_DIR) + os.sep) or not target.endswith(".jpg"):
            self._json(403, {"ok": False}); return
        if not os.path.isfile(target):
            self._json(404, {"ok": False}); return
        try:
            with open(target, "rb") as f:
                data = f.read()
        except Exception:
            self._json(500, {"ok": False}); return
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "max-age=3600")
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
        self._json(404, {"ok": False, "msg": "not found"})

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)

        if path == "/api/on":
            r = start_agent(sim=False)
            board = _open_board_once()
            self._json(200, {**r, "board": board})
            return
        if path == "/api/sim":
            if _agent_alive():
                stop_agent(farewell=False)
                time.sleep(0.4)
            r = start_agent(sim=True)
            board = _open_board_once()
            self._json(200, {**r, "board": board})
            return
        if path == "/api/off":
            open_board(auto_on=False)
            r = stop_agent(farewell=False)
            self._json(200, r)
            return
        if path == "/api/stop":
            # v765 — STOP never opens windows (the board auto-syncs to OFFLINE by itself);
            # a SIM agent has nothing worth a farewell wait — only live runs get the 90s grace.
            r = stop_agent(farewell=(_agent_mode != "sim"))
            self._json(200, r)
            return
        if path == "/api/restart":
            stop_agent(farewell=False)
            time.sleep(0.5)
            r = start_agent(sim=False)
            board = _open_board_once()
            self._json(200, {**r, "board": board})
            return
        if path == "/api/board":
            self._json(200, open_board(auto_on=True))
            return
        if path == "/api/quit":
            threading.Thread(
                target=lambda: (time.sleep(0.3), os._exit(0)), daemon=True
            ).start()
            self._json(200, {"ok": True, "msg": "control quitting"})
            return
        self._json(404, {"ok": False, "msg": "not found"})


def main():
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
        print(
            f"📺 control already on :{CONTROL_PORT} — opening another app window\n   ({e})"
        )
        if open_ui and not no_open:
            open_control_window()
        else:
            sys.exit(1)
        return

    plat = "windows" if IS_WIN else ("mac" if sys.platform == "darwin" else sys.platform)
    print(f"📺 TV DIABLO Control v765 · {plat} · native window · http://127.0.0.1:{CONTROL_PORT}/")
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
