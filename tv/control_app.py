#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# 📺 TV DIABLO — Control App (Mac first · v758)
#
#   A real windowed control surface: HD grimoire UI, buttons for
#   ON / OFF / STOP / RESTART / SIM. The agent runs HIDDEN (logs to file).
#   The board auto-connects via bible.html#tvd-on.
#
#   Launch:  python3 tv/control_app.py --open
#   Or:      double-click TV DIABLO.app (installer wires this)
#
#   Zero deps — stdlib only. Agent = tv_diablo.py (same engine).
# ═══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CONTROL_PORT = int(os.environ.get("TV_CONTROL_PORT", "17772"))
AGENT_PORT = int(os.environ.get("TV_PORT", "17771"))
LOG_PATH = os.path.join(HERE, "control_agent.log")
PID_PATH = os.path.join(HERE, "control_agent.pid")
UI_PATH = os.path.join(HERE, "control_ui.html")
BIBLE = os.path.join(REPO, "bible.html")
ART_DIR = os.path.realpath(os.path.join(REPO, "art"))

_ART_MIME = {
    ".png": "image/png",
    ".gif": "image/gif",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}

_lock = threading.Lock()
_agent_proc: subprocess.Popen | None = None
_agent_mode: str = "off"  # off | live | sim
_log_fp = None


def _env_clean(sim: bool = False) -> dict:
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    env["PATH"] = (
        "/opt/homebrew/bin:/usr/local/bin:"
        + os.path.expanduser("~/.local/bin")
        + ":"
        + env.get("PATH", "")
    )
    if sim:
        env["TV_STUB"] = "1"
    else:
        env.pop("TV_STUB", None)
    env["TV_PORT"] = str(AGENT_PORT)
    return env


def _bridge_ping() -> dict | None:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{AGENT_PORT}/ping", timeout=0.6
        ) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _bridge_state() -> dict | None:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{AGENT_PORT}/state", timeout=0.8
        ) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _port_listener_pid() -> int | None:
    """Any process holding the agent bridge (ours or a bare `tvd`)."""
    try:
        out = subprocess.check_output(
            ["lsof", f"-tiTCP:{AGENT_PORT}", "-sTCP:LISTEN"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if not out:
            return None
        return int(out.splitlines()[0])
    except Exception:
        return None


def _agent_alive() -> bool:
    global _agent_proc
    with _lock:
        if _agent_proc is not None and _agent_proc.poll() is None:
            return True
    return _port_listener_pid() is not None


def start_agent(sim: bool = False) -> dict:
    global _agent_proc, _agent_mode, _log_fp
    with _lock:
        if _agent_proc is not None and _agent_proc.poll() is None:
            return {"ok": True, "msg": "already running", "mode": _agent_mode}
        # foreign agent already on the port
        if _port_listener_pid() is not None:
            _agent_mode = "sim" if sim else "live"
            return {"ok": True, "msg": "bridge already live", "mode": _agent_mode}

        os.makedirs(HERE, exist_ok=True)
        if _log_fp:
            try:
                _log_fp.close()
            except Exception:
                pass
        _log_fp = open(LOG_PATH, "a", buffering=1)
        _log_fp.write(
            f"\n—— control start {time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"mode={'sim' if sim else 'live'} ——\n"
        )
        _log_fp.flush()

        cmd = [sys.executable, os.path.join(HERE, "tv_diablo.py")]
        _agent_proc = subprocess.Popen(
            cmd,
            cwd=REPO,
            env=_env_clean(sim=sim),
            stdout=_log_fp,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            with open(PID_PATH, "w") as f:
                f.write(str(_agent_proc.pid))
        except Exception:
            pass
        _agent_mode = "sim" if sim else "live"

    # wait briefly for bridge
    for _ in range(40):
        if _bridge_ping() is not None:
            break
        time.sleep(0.15)
    return {
        "ok": True,
        "msg": "started",
        "mode": _agent_mode,
        "pid": _agent_proc.pid if _agent_proc else None,
    }


def stop_agent(farewell: bool = True) -> dict:
    global _agent_proc, _agent_mode
    pid = None
    with _lock:
        if _agent_proc is not None and _agent_proc.poll() is None:
            pid = _agent_proc.pid
        else:
            pid = _port_listener_pid()

    if pid is None:
        _agent_mode = "off"
        return {"ok": True, "msg": "already off"}

    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    except Exception:
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass

    wait_s = 90 if farewell else 12
    deadline = time.time() + wait_s
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
            time.sleep(0.25)
        except ProcessLookupError:
            break
    else:
        try:
            os.killpg(pid, signal.SIGKILL)
        except Exception:
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass

    with _lock:
        _agent_proc = None
        _agent_mode = "off"
    try:
        if os.path.isfile(PID_PATH):
            os.remove(PID_PATH)
    except Exception:
        pass
    return {"ok": True, "msg": "stopped", "farewell": farewell}


def open_board(auto_on: bool = True) -> dict:
    """Open the bible TV·D tab; #tvd-on flips the board switch via bible boot."""
    if not os.path.isfile(BIBLE):
        return {"ok": False, "msg": "bible.html missing"}
    # file URL — hash works; query often stripped on file://
    tag = "tvd-on" if auto_on else "tvd-off"
    url = f"file://{BIBLE}#{tag}"
    try:
        if sys.platform == "darwin":
            subprocess.Popen(
                ["open", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif sys.platform.startswith("win"):
            os.startfile(url)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", url])
        return {"ok": True, "msg": "board opened", "url": url}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def open_control_window() -> None:
    url = f"http://127.0.0.1:{CONTROL_PORT}/"
    if sys.platform == "darwin":
        # Prefer Chrome/Edge/Brave app window (no browser chrome). Fall back to default.
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
    else:
        try:
            import webbrowser

            webbrowser.open(url)
        except Exception:
            pass


def status_payload() -> dict:
    bridge = _bridge_ping() is not None
    st = _bridge_state() if bridge else None
    mode = _agent_mode
    if bridge and mode == "off":
        mode = "live"  # foreign or orphaned bridge
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
        "ver": "v759",
        "mode": mode,
        "agent": mode != "off" and bridge,
        "bridge": bridge,
        "pid": _port_listener_pid(),
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

def _read_ui() -> bytes:
    if os.path.isfile(UI_PATH):
        with open(UI_PATH, "rb") as f:
            return f.read()
    return b"<h1>TV DIABLO control_ui.html missing</h1>"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silent

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code: int, obj: dict):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_art(self, name: str):
        """Serve a read-only image from the repo art/ dir. Path-traversal-safe."""
        from urllib.parse import unquote

        rel = unquote(name).split("?", 1)[0].split("#", 1)[0]
        target = os.path.realpath(os.path.join(ART_DIR, rel))
        # must stay inside ART_DIR and be a real file
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
            self._serve_art(path[len("/art/"):])
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
            open_board(auto_on=True)
            self._json(200, {**r, "board": "auto-on"})
            return
        if path == "/api/sim":
            # restart into sim if needed
            if _agent_alive():
                stop_agent(farewell=False)
                time.sleep(0.4)
            r = start_agent(sim=True)
            open_board(auto_on=True)
            self._json(200, {**r, "board": "auto-on"})
            return
        if path == "/api/off":
            # board off + stop agent (soft, short wait)
            open_board(auto_on=False)
            r = stop_agent(farewell=False)
            self._json(200, r)
            return
        if path == "/api/stop":
            open_board(auto_on=False)
            r = stop_agent(farewell=True)
            self._json(200, r)
            return
        if path == "/api/restart":
            stop_agent(farewell=False)
            time.sleep(0.5)
            r = start_agent(sim=False)
            open_board(auto_on=True)
            self._json(200, {**r, "board": "auto-on"})
            return
        if path == "/api/board":
            self._json(200, open_board(auto_on=True))
            return
        if path == "/api/quit":
            # stop control server only — leave agent if running
            threading.Thread(target=lambda: (time.sleep(0.3), os._exit(0)), daemon=True).start()
            self._json(200, {"ok": True, "msg": "control quitting"})
            return
        self._json(404, {"ok": False, "msg": "not found"})


def main():
    open_ui = "--open" in sys.argv or "-o" in sys.argv
    no_open = "--no-open" in sys.argv

    # bind control port
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", CONTROL_PORT), Handler)
    except OSError as e:
        print(f"⛔ cannot bind 127.0.0.1:{CONTROL_PORT} — control app already running?\n   {e}")
        if open_ui and not no_open:
            open_control_window()
        sys.exit(1)

    print(f"📺 TV DIABLO Control v759 · http://127.0.0.1:{CONTROL_PORT}/")
    print(f"   agent bridge :{AGENT_PORT} · log {LOG_PATH}")
    print("   window UI — agent stays hidden. Ctrl-C quits control (not the agent).")

    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()

    if open_ui and not no_open:
        time.sleep(0.25)
        open_control_window()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n📺 control UI server stopping (agent left as-is — use STOP in the app).")
        srv.shutdown()


if __name__ == "__main__":
    main()
