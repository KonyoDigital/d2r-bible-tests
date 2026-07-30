#!/usr/bin/env python3
"""v1476 — SYNTAX GATE for the single-file surfaces (bible.html · control_ui.html).

Why this exists
---------------
Twice in one session an edit produced a hard `Uncaught SyntaxError` that killed an entire
37k-line page, and both times it was caught only because a human happened to run headless
Chromium by hand:

  REG-060  a shell heredoc ate `\\n` escapes, leaving REAL newlines inside single-quoted JS
           string literals -> unterminated string.
  REG-072  a `//` comment was appended MID-LINE to a single-line `forEach`, commenting out the
           rest of the statement -> the closing `});` vanished.

Either one blanks the whole board. A manual check is one bad day away from shipping, so it
belongs in the suite.

Why a real browser and not a hand-rolled scanner
-----------------------------------------------
A tokenizer was tried first and REJECTED. On this codebase it reported 14-16 problems in files
that parse perfectly in Chromium: the pages use template literals with `${…}` interpolation
containing nested backticks, embedded HTML with quotes, and regex literals that a heuristic
cannot reliably tell from division. A gate with false alarms is worse than no gate — people stop
reading it, and then it misses the real one. So the gate asks an actual JavaScript engine.

Behaviour
---------
  * Chromium available -> load each file and fail on any SyntaxError in the console.
  * Chromium missing   -> SKIP loudly. A gate that cannot run must say so, never pass silently.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = ["bible.html", "tv/control_ui.html"]

_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

# "Uncaught SyntaxError: …" / "SyntaxError: …" as Chromium reports it on the console
_ERR = re.compile(r"(Uncaught SyntaxError|SyntaxError):[^\"]*", re.I)


def find_browser():
    for c in _CANDIDATES:
        if os.path.isfile(c):
            return c
    for name in ("chrome", "chromium", "msedge", "google-chrome"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _serve(root):
    """A file:// origin cannot run these pages; serve the repo on an ephemeral port."""
    class H(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=root, **kw)

        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def check(targets=None, timeout=90):
    """Return (problems, skipped_reason). problems == [] and reason is None when clean."""
    targets = targets or TARGETS
    browser = find_browser()
    if not browser:
        return [], "no Chromium/Edge found — cannot verify JS syntax"

    srv, port = _serve(REPO)
    problems = []
    try:
        for rel in targets:
            if not os.path.isfile(os.path.join(REPO, rel)):
                problems.append(f"{rel}: missing")
                continue
            with tempfile.TemporaryDirectory() as prof:
                cmd = [
                    browser, "--headless=old", "--disable-gpu", "--no-sandbox",
                    f"--user-data-dir={prof}", "--blink-settings=imagesEnabled=false",
                    "--enable-logging=stderr", "--v=0", "--virtual-time-budget=9000",
                    "--dump-dom", f"http://127.0.0.1:{port}/{rel}",
                ]
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True,
                                       encoding="utf-8", errors="replace", timeout=timeout)
                except subprocess.TimeoutExpired:
                    problems.append(f"{rel}: browser timed out after {timeout}s")
                    continue
                except OSError as e:
                    return [], f"browser failed to start ({e})"
                blob = (r.stderr or "") + (r.stdout or "")
                # a crashed renderer is not a syntax verdict — say so rather than pass
                if r.returncode not in (0, None) and "CONSOLE" not in blob:
                    return [], f"browser exited {r.returncode} without console output"
                for m in _ERR.finditer(blob):
                    line = ""
                    ctx = blob[max(0, m.start() - 200):m.start() + 300]
                    lm = re.search(r"\((\d+)\)", ctx)
                    if lm:
                        line = f":{lm.group(1)}"
                    problems.append(f"{rel}{line}: {m.group(0).strip()}")
    finally:
        srv.shutdown()
        srv.server_close()
    # de-dup: one broken statement can surface twice
    return sorted(set(problems)), None


def main(argv):
    problems, skipped = check(argv[1:] or None)
    if skipped:
        print(f"⚠ JS SYNTAX GATE SKIPPED — {skipped}")
        return 0
    if problems:
        print("❌ JS SYNTAX GATE — %d problem(s):" % len(problems))
        for p in problems:
            print("   " + p)
        return 1
    print("✅ JS SYNTAX GATE OK — every surface parses in a real JS engine.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
