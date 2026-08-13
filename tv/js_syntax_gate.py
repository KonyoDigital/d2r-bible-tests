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

import io
import os
import re
import shutil
import subprocess
import signal
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


_LOOPBACK_OK = []   # cached capability verdict: [] = unprobed, [True] / [False] once known


def browser_can_load_localhost(browser=None, timeout=12):
    """Can this browser answer `--dump-dom` for an http://127.0.0.1 page AT ALL?

    v1490 — measured on Konyo's Mac: `--dump-dom` returns instantly for a file:// page and NEVER
    returns for the same page over loopback HTTP — with BOTH Google Chrome and Chrome for Testing,
    with or without proxy flags (there is no proxy configured). Playwright drives the same binaries
    over the same loopback fine, so it is this launch path on this machine, not the network and not
    the page.

    The cost of not knowing: every browser-driven test spent its full timeout and then ERRORED, so
    the pre-push gate took ten minutes and came back red for a reason that says nothing about the
    code being pushed. A capability that cannot be assumed gets PROBED — once, on a 40-byte page —
    and the tests that need it skip with a reason instead of failing a verdict they never reached.
    """
    if _LOOPBACK_OK:
        return _LOOPBACK_OK[0]
    browser = browser or find_browser()
    if not browser:
        _LOOPBACK_OK.append(False)
        return False
    root = tempfile.mkdtemp()
    with open(os.path.join(root, "_probe.html"), "w", encoding="utf-8") as fh:
        fh.write("<!doctype html><html><body>LOOPBACK_OK</body></html>")
    srv, port = _serve(root)
    ok = False
    try:
        with tempfile.TemporaryDirectory() as prof:
            proc = subprocess.Popen(
                [browser, "--headless=new", "--disable-gpu", "--no-sandbox",
                 f"--user-data-dir={prof}", "--virtual-time-budget=2000", "--dump-dom",
                 f"http://127.0.0.1:{port}/_probe.html"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
            try:
                out, _ = proc.communicate(timeout=timeout)
                ok = b"LOOPBACK_OK" in (out or b"")
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except Exception:
                    proc.kill()
                try:
                    proc.communicate(timeout=5)
                except Exception:
                    pass
    except Exception:
        ok = False
    finally:
        srv.shutdown()
        shutil.rmtree(root, ignore_errors=True)
    _LOOPBACK_OK.append(ok)
    return ok


NO_LOOPBACK = ("this browser never answers --dump-dom over http://127.0.0.1 on this machine "
               "(file:// works, and Playwright drives the same binary fine), so the check could "
               "not run and this result proves NOTHING about the code")


def _node_bin():
    for c in ("node", "/usr/local/bin/node", "/opt/homebrew/bin/node"):
        try:
            subprocess.run([c, "--version"], capture_output=True, timeout=20, check=True)
            return c
        except Exception:
            continue
    return None


def check_with_node(targets=None):
    """PARSE every inline <script> with `node --check`. No browser, no loopback, no server.

    v1711 — THE BROWSER PATH SKIPS ON HIS MAC AND HAS FOR ~220 VERSIONS. `--dump-dom` never answers
    over http://127.0.0.1 here (measured v1490), so this gate reported SKIPPED every single local
    run — and a gate that never runs is not protection, it is a line in a report. Its stated job is
    "every surface must PARSE", and parsing does not need a DOM.

    So the browser stays as the richer check (it also catches what a page throws while EXECUTING),
    and this is what runs when the browser cannot. Between them the gate always has a verdict.

    Returns (problems, None). Classic-script semantics: `type=module`/JSON blocks are skipped
    because `node --check` parses them as scripts and would report false errors on import/export.
    """
    node = _node_bin()
    if not node:
        return [], "no node found — cannot parse JS without a browser either"
    problems = []
    for rel in (targets or TARGETS):
        path = os.path.join(REPO, rel)
        if not os.path.isfile(path):
            problems.append(f"{rel}: missing")
            continue
        html = io.open(path, encoding="utf-8", errors="replace").read()
        blocks = 0
        for m in re.finditer(r"<script([^>]*)>(.*?)</script>", html, re.S | re.I):
            attrs, body = m.group(1) or "", m.group(2)
            if "src=" in attrs.lower():
                continue                      # external file, nothing inline to parse
            if re.search(r'type\s*=\s*["\']?(module|application/json|importmap)', attrs, re.I):
                continue                      # not a classic script; node --check would lie
            if not body.strip():
                continue
            blocks += 1
            line0 = html[:m.start(2)].count("\n") + 1
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                             encoding="utf-8") as fh:
                fh.write(body)
                tmp = fh.name
            try:
                r = subprocess.run([node, "--check", tmp], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=60)
                if r.returncode != 0:
                    first = (r.stderr or "").strip().splitlines()
                    detail = next((l for l in first if "SyntaxError" in l), first[0] if first else "")
                    problems.append(f"{rel}: <script> starting at line {line0} — {detail.strip()[:160]}")
            finally:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
        if blocks == 0:
            problems.append(f"{rel}: no inline <script> blocks found — the parser matched nothing, "
                            f"which is an instrument failure, not a clean file")
    return problems, None


def check(targets=None, timeout=90):
    """Return (problems, skipped_reason). problems == [] and reason is None when clean."""
    targets = targets or TARGETS
    browser = find_browser()
    if not browser:
        return check_with_node(targets)          # v1711 — parse it without a browser

    # v1490 — a browser that cannot answer over loopback here can only produce a timeout, and a
    # timeout is not a syntax verdict. Say "did not run" instead of spending 90s per target first.
    if not browser_can_load_localhost(browser):
        return check_with_node(targets)          # v1711 — his Mac never answers over loopback

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


def _safe_console():
    """v1478 — a gate that cannot REPORT is a broken gate.

    This machine's console is Hebrew (cp1255). The check itself passed, reached the success branch,
    and then died inside `print("✅ ...")` with UnicodeEncodeError -> exit 1. A plain run of a
    clean tree reported RED. That is the REG-054 failure mode wearing a different hat: the suite was
    only ever green because PYTHONIOENCODING was being set by hand off-screen.

    Reconfigure rather than strip the glyphs: the verdict stays readable everywhere, and errors are
    replaced instead of raised, so no future character can turn a passing gate into a false alarm.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# Shared with tv/run_gates.py — a gate that could not run says so with this code.
SKIP_EXIT = 77


def main(argv):
    _safe_console()
    problems, skipped = check(argv[1:] or None)
    if skipped:
        # v1601 — EXIT 77, NOT 0. Returning 0 made run_gates print a green tick beside the words
        # "GATE SKIPPED", which is the exact lie run_gates' own docstring forbids: "a check that did
        # not happen is not a check that passed". On this Mac the browser never answers --dump-dom
        # over http://127.0.0.1, so this gate skips on EVERY local run — the one surface most likely
        # to be silently unprotected was the one wearing a tick.
        print(f"⚠ JS SYNTAX GATE SKIPPED — {skipped}")
        return SKIP_EXIT
    if problems:
        print("❌ JS SYNTAX GATE — %d problem(s):" % len(problems))
        for p in problems:
            print("   " + p)
        return 1
    print("✅ JS SYNTAX GATE OK — every surface parses in a real JS engine.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
