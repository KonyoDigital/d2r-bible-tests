# -*- coding: utf-8 -*-
"""REG-1617 — CLAUDE SIGNS IN FROM THE CONSOLE, WITH ONE CLICK, ON THE PC THAT NEEDS IT.

His ask, 2026-09-30, after his ALT read nothing for a day because Claude was signed out there: "how do i sign in on the
console.. make a button there so i can click within the console.. where we said it should render if we are still
connected because this happens monthly i think it just disconnects sometimes".

Two halves, the same shape as Grok's own ⚡ Authorize (g5_grok_eyes.start_login), so the two readers sign in alike:
  · status()  - `claude auth status --json`: the CLI's own word on whether it is signed in. MEASURED on his ALT the
                same evening: "authMethod": "none" while every read failed with "OAuth session expired". None is
                UNKNOWN (no CLI, no answer) and never "signed out".
  · start()   - `claude auth login` in a window HE CAN SEE, on this PC: he finishes in the browser that opens. One
                sign-in in flight at a time (a second click says so and opens nothing). The command is fixed - nothing
                from the page reaches it.

⚠ THE WINDOW IS DELIBERATE, AND ONLY THIS ONE. The console hides every child it starts on Windows (win_quiet, REG-1307:
windows kept jumping over his game). win_quiet respects CREATE_NEW_CONSOLE but still hides the new console unless the
caller hands in its own STARTUPINFO - so this passes both, with SW_SHOWNORMAL: a sign-in he pressed for must be seen
(if the CLI prints a URL or asks for a code, a hidden window would hang for ever). On the Mac the same command opens
in Terminal. Anywhere else it answers with the command to type rather than guessing a terminal.
[[unknown-stays-unknown]] [[heart-first]]
"""
import json
import os
import subprocess
import sys
import threading
import time

#: Windows process flags (subprocess exposes them only on win32; the values are fixed by the OS)
CREATE_NEW_CONSOLE = 0x00000010
STARTF_USESHOWWINDOW = 0x00000001
SW_SHOWNORMAL = 1

_LOCK = threading.Lock()
_PROC = {"proc": None, "at": None}


def status(bin_path, _run=None, timeout=30):
    """The CLI's own word on its sign-in. -> {loggedIn: bool|None, method, why}. Never raises."""
    if not bin_path:
        return {"loggedIn": None, "method": None, "why": "the Claude CLI was not found on this PC"}
    try:
        r = (_run or subprocess.run)([bin_path, "auth", "status", "--json"], capture_output=True, text=True,
                                     timeout=timeout)
        d = json.loads((r.stdout or "").strip() or "{}")
    except Exception as e:
        return {"loggedIn": None, "method": None,
                "why": "claude auth status could not be asked (%s) - UNKNOWN" % type(e).__name__}
    li = d.get("loggedIn") if isinstance(d, dict) else None
    if not isinstance(li, bool):
        return {"loggedIn": None, "method": None, "why": "claude auth status gave no loggedIn - UNKNOWN"}
    return {"loggedIn": li, "method": (d.get("authMethod") or None),
            "why": "claude auth status: %s" % ("signed in" if li else "signed out (%s)" % (d.get("authMethod") or "none"))}


#: REG-1985 — the CLI's own installer, the line ON AIR's "fix" already prints (control_app.start_agent). His "if he clicks
#: it it should route him intelligently to the sign in": a PC with no CLI is the one place a click had nowhere to go - the
#: answer ended at "nothing to sign in with". It now says the one line that gets there, as Grok's own no-cli answer does.
INSTALL = {"win32": "irm https://claude.ai/install.ps1 | iex", "other": "curl -fsSL https://claude.ai/install.sh | bash"}


def command(bin_path, platform=None):
    """The ONE sign-in command, as the argv to spawn. -> (argv, how) | (None, why)"""
    plat = sys.platform if platform is None else platform
    if not bin_path:
        return None, ("the Claude CLI is not installed on this PC - install it once in %s:  %s  - then click SIGN IN "
                      "(or CLAUDE) again" % (("PowerShell", INSTALL["win32"]) if plat == "win32"
                                             else ("Terminal", INSTALL["other"])))
    if plat == "win32":
        return [bin_path, "auth", "login"], "window"
    if plat == "darwin":
        q = "'" + str(bin_path).replace("'", "'\\''") + "'"
        return (["osascript", "-e", 'tell application "Terminal" to do script "%s auth login"' % q.replace('"', '\\"'),
                 "-e", 'tell application "Terminal" to activate'], "terminal")
    return None, "this PC has no window to open a sign-in in - run `claude auth login` in a terminal"


def inflight():
    """True while the sign-in this console opened is still running."""
    p = _PROC.get("proc")
    if p is None:
        return False
    try:
        return p.poll() is None
    except Exception:
        return False


#: REG-1618 — how long after a click the console keeps saying "waiting" and re-asks the CLI every few seconds. On the Mac
#: the Terminal window is not ours to watch (osascript hands the command over and exits), so the click's own time is
#: the only clock there; on Windows the window's process is watched as well.
WATCH_S = 600

#: REG-1639 - the #231 eye on 5979d7f3, reproduced: on his Mac the sign-in runs in Terminal through osascript, which hands
#: the command over and EXITS - there is no process left to ask whether the sign-in is still open, so inflight() was
#: always False there and two clicks two seconds apart opened two Terminal sign-ins. A second click inside this window
#: opens nothing and says where the first one is; after it a click opens a fresh one (he may have closed the first).
TERMINAL_AGAIN_S = 90


def watching(now=None, window_s=WATCH_S):
    """True while the sign-in this console opened is running, or was opened less than window_s ago."""
    if inflight():
        return True
    at = _PROC.get("at")
    now = time.time() if now is None else now
    try:
        return bool(at) and 0 <= now - float(at) < window_s
    except (TypeError, ValueError):
        return False


def start(bin_path, platform=None, _popen=None, now=None):
    """Open the sign-in, once. -> {ok, started, reason, why}. Never raises."""
    plat = sys.platform if platform is None else platform
    now = time.time() if now is None else now
    argv, how = command(bin_path, plat)
    if argv is None:
        return {"ok": False, "started": False, "reason": "no-window" if bin_path else "no-cli", "why": how}
    with _LOCK:
        if inflight():
            return {"ok": True, "started": False, "reason": "in-flight",
                    "why": "a sign-in window is already open on this PC - finish it in the browser"}
        _at = _PROC.get("at")
        if how == "terminal" and _PROC.get("proc") is None and _at is not None and 0 <= now - float(_at) < TERMINAL_AGAIN_S:
            return {"ok": True, "started": False, "reason": "in-flight",
                    "why": "a sign-in opened in Terminal %d s ago - finish it there (a new one can open after %d s)"
                           % (int(now - float(_at)), TERMINAL_AGAIN_S)}
        kw = {"close_fds": True}
        if plat == "win32":
            si = subprocess.STARTUPINFO() if hasattr(subprocess, "STARTUPINFO") else None
            if si is not None:
                si.dwFlags = int(getattr(si, "dwFlags", 0) or 0) | STARTF_USESHOWWINDOW
                si.wShowWindow = SW_SHOWNORMAL
            kw.update(creationflags=CREATE_NEW_CONSOLE, startupinfo=si)
        else:
            kw.update(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                      start_new_session=True)
        try:
            p = (_popen or subprocess.Popen)(argv, **kw)
        except Exception as e:
            return {"ok": False, "started": False, "reason": "spawn-failed",
                    "why": "the sign-in window would not open (%s)" % type(e).__name__}
        # the Mac's osascript hands the command to Terminal and exits at once - there is nothing to wait on there
        _PROC.update(proc=(p if how == "window" else None), at=now)
    return {"ok": True, "started": True, "reason": "spawned",
            "why": ("a sign-in window opened on this PC - finish in the browser it opens; the CLAUDE lamp turns green "
                    "after the next read")}
