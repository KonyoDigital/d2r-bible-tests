#!/usr/bin/env python3
"""v1483 — THE GATE SET, in one place, with one verdict.

Why this exists
---------------
`tv/test_routes.py` exited 1 for about a hundred versions and nobody knew (REG-079). It was not
broken in an interesting way — v1381.1 changed a rule, two tests kept asserting the old one — but
it was not in anybody's habit, so its verdict decayed into decoration. It still passed 181 of 183
assertions, which is the trap: a mostly-green orphan looks maintained.

The lesson generalises past that one file. "The gate set" was a thing people carried in their
heads and typed by hand, which means it was different for every person and every session, and a
suite could fall out of it silently. It is now a list in a file, and `TestNoOrphanSuite` fails if a
`tv/test_*.py` exists that this list does not name.

Reporting rules (learned the hard way)
--------------------------------------
* Encoding-safe before anything prints — a gate that dies REPORTING turns a clean tree red
  (REG-044/054/077/078).
* A suite that cannot RUN is reported as SKIPPED, loudly, and never counted as a pass. Silence
  about a check that did not happen is the same lie as a false green.
* The exit code is the verdict: non-zero if any REQUIRED entry failed.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

sys.path.insert(0, HERE)
try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass


class Gate:
    def __init__(self, name, argv, timeout=900, needs_app=False, cwd=REPO, why=""):
        self.name, self.argv, self.timeout = name, argv, timeout
        self.needs_app, self.cwd, self.why = needs_app, cwd, why


# THE GATE SET. Adding a tv/test_*.py without adding it here fails TestNoOrphanSuite.
GATES = [
    Gate("js-syntax",   [sys.executable, os.path.join(HERE, "js_syntax_gate.py")], 300,
         why="every surface must PARSE — a bad edit blanks a 37k-line page"),
    Gate("visual-lock", [sys.executable, os.path.join(REPO, "visual_lock_invariant.py")], 120,
         why="the locked type system may not drift"),
    Gate("test_control", [sys.executable, os.path.join(HERE, "test_control.py")], 900,
         why="the console + storage routing + gate invariants"),
    Gate("test_agent",   [sys.executable, os.path.join(HERE, "test_agent.py")], 900,
         why="the agent, its argv seam and its budget circuit-breaker"),
    Gate("test_routes",  [sys.executable, os.path.join(HERE, "test_routes.py")], 300,
         why="KAI routing, labels and the super-analyze selector"),
    Gate("test_g5_grok_eyes", [sys.executable, os.path.join(HERE, "test_g5_grok_eyes.py")], 300,
         why="the vision-eye contract"),
    Gate("test_roundtrip_sim", [sys.executable, os.path.join(HERE, "test_roundtrip_sim.py")], 900,
         why="a full simulated session round trip"),
    Gate("test_button_matrix", [sys.executable, os.path.join(HERE, "test_button_matrix.py")], 300,
         needs_app=True,
         why="every app button, against the LIVE control API"),
]

_OK = re.compile(r"^(OK|✅|Ran \d+ tests)", re.M)


def _app_up(port=17772, timeout=1.5):
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/api/status" % port, timeout=timeout):
            return True
    except Exception:
        return False


def run(only=None):
    results = []
    app_up = _app_up()
    for g in GATES:
        if only and g.name not in only:
            continue
        if g.needs_app and not app_up:
            results.append((g, "SKIP", 0.0, "control app is not running on :17772"))
            continue
        t0 = time.time()
        try:
            p = subprocess.run(g.argv, cwd=g.cwd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=g.timeout)
            dt = time.time() - t0
            blob = (p.stdout or "") + (p.stderr or "")
            tail = [ln for ln in blob.strip().split("\n") if ln.strip()][-1:] or [""]
            results.append((g, "PASS" if p.returncode == 0 else "FAIL", dt, tail[0][:150]))
        except subprocess.TimeoutExpired:
            results.append((g, "FAIL", time.time() - t0,
                            "timed out after %ds — a hung gate is a failed gate" % g.timeout))
        except OSError as e:
            results.append((g, "SKIP", time.time() - t0, "could not launch (%s)" % e))
    return results


def main(argv):
    ap = argparse.ArgumentParser(description="run the gate set and return one verdict")
    ap.add_argument("--only", nargs="*", help="run only these gate names")
    a = ap.parse_args(argv[1:])

    print("══ GATE SET ══")
    results = run(a.only)
    for g, status, dt, detail in results:
        mark = {"PASS": "✅", "FAIL": "❌", "SKIP": "⚠"}[status]
        print("%s %-20s %6.1fs  %s" % (mark, g.name, dt, detail))

    failed = [g.name for g, s, _, _ in results if s == "FAIL"]
    skipped = [(g.name, d) for g, s, _, d in results if s == "SKIP"]
    print("\n── VERDICT ──")
    if skipped:
        # never silent: a check that did not happen is not a check that passed
        for n, d in skipped:
            print("⚠ SKIPPED %s — %s" % (n, d))
    if failed:
        print("❌ %d gate(s) FAILED: %s" % (len(failed), ", ".join(failed)))
        return 1
    print("✅ %d gate(s) passed%s."
          % (len(results) - len(skipped), (", %d skipped" % len(skipped)) if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
