#!/usr/bin/env python3
"""v921 — FROZEN-ROBOT BOOT SMOKE (Grok: "tonight proved clean; CI must pin it").

The multi-worker robot is FROZEN behind TV_ROBOT=1 (arc non-goal, debug lane) — but it
shares journal/bridge/capture code that keeps evolving, so it can rot silently. This smoke
boots it for ~20s in stub mode and asserts the lane is alive: robot banner · journal rows ·
no traceback. Cheap (no model calls), CI-safe (stub capture works headless).
"""
import json
import os
import signal
import subprocess
import sys
import tempfile
import time

# v1480 — make our own output survive the operator's console before we print anything.
# A tool whose verdict is its exit code must not die reporting it (REG-044/054/077): on a Hebrew
# cp1255 console every check mark we print is an unencodable character, and the crash lands in the
# dangerous direction — a correct tree reporting FAILURE.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    tmp = tempfile.mkdtemp(prefix="tvd-robot-smoke-")
    journal = os.path.join(tmp, "sessions.jsonl")
    hist = os.path.join(tmp, "hist")
    os.makedirs(hist)
    env = dict(os.environ,
               TV_ROBOT="1", TV_STUB="1", TV_POOL="1", TV_FAREWELL="0",
               TV_SESSIONS=journal, TV_HIST=hist, TV_PORT="17963",
               PYTHONUNBUFFERED="1")   # block-buffered stdout would die unflushed at SIGTERM
    log = os.path.join(tmp, "agent.log")
    with open(log, "wb") as lf:
        pr = subprocess.Popen([sys.executable, os.path.join(HERE, "tv_diablo.py")],
                              stdout=lf, stderr=subprocess.STDOUT, env=env)
        try:
            time.sleep(20)
        finally:
            pr.send_signal(signal.SIGTERM)
            try:
                pr.wait(timeout=15)
            except subprocess.TimeoutExpired:
                pr.kill()
                pr.wait()

    text = open(log, encoding="utf-8", errors="replace").read()
    ok = True
    if "ROBOT (TV_ROBOT=1)" not in text:
        print("FAIL: robot banner missing — TV_ROBOT lane didn't engage")
        ok = False
    if "Traceback" in text:
        print("FAIL: traceback in robot boot:\n" + text[text.index("Traceback"):][:600])
        ok = False
    rows = 0
    try:
        with open(journal) as f:
            rows = sum(1 for l in f if l.strip() and json.loads(l))
    except FileNotFoundError:
        pass
    if rows < 3:
        print("FAIL: only %d journal rows in 20s — robot cadence dead" % rows)
        ok = False
    if not ok:
        print("--- log tail ---\n" + text[-1200:])
        sys.exit(1)
    print("robot smoke OK — banner up · %d journal rows · no traceback" % rows)
    sys.exit(0)


if __name__ == "__main__":
    main()
