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
    Gate("test_tz_art", [sys.executable, os.path.join(HERE, "test_tz_art.py")], 120,
         why="the Terror Zone panel's facts: 67 zones -> game-extracted art + the game's own "
             "density/level, and the tiering that decides which zones get greyed out"),
    Gate("test_tz_relay", [sys.executable, os.path.join(HERE, "test_tz_relay.py")], 60,
         why="the console TZ relay must treat a history-only payload as live, not as "
             "unreachable, and /d2r/api/tz must stay as open as /api/tz"),
    Gate("test_shard_balance", [sys.executable, os.path.join(HERE, "test_shard_balance.py")], 30,
         why="Routine I must peel the every-item simulations into the slow project so "
             "--shard cannot dump them all into one 45-minute file-count bucket"),
    Gate("test_vault_retro", [sys.executable, os.path.join(HERE, "test_vault_retro.py")], 120,
         why="the vault accumulator's laws: merge-max never subtracts, throw-out needs more "
             "evidence than keep, order cannot change the ledger, missing is never zero"),
    Gate("ui_icons", [sys.executable, os.path.join(HERE, "extract_ui_icons.py"), "--check"], 60,
         why="v1614 — every console tab and MINI focus icon is present in art/. The icons are "
             "committed PNGs; this proves none was deleted or renamed out from under the HTML, "
             "which fails SILENTLY: each <img> carries onerror=this.remove(), so a missing file "
             "leaves a tidy label with no picture rather than anything that looks broken"),
    Gate("test_reachability", [sys.executable, os.path.join(HERE, "test_reachability.py")], 120,
         why="LAW19 as a gate, not an intention — BOTH halves. Every DOM id READ must be WRITTEN "
             "in the same document, and every `typeof X === function` guard must name a symbol "
             "that exists. Six bugs were this one shape: REG-083/087, the v1576 dead-safe "
             "classifier, the v1593 TZ crash, ~680 versions of unreachable shelf code (REG-095), "
             "and five ownership changes that never repainted (REG-096)"),
    Gate("test_free_pass_quote", [sys.executable, os.path.join(HERE, "test_free_pass_quote.py")], 180,
         why="the free pass may never quote BELOW what a real sweep spends — it priced only the "
             "classify lane and structurally could not count a page read (v1596)"),
    Gate("test_chronicle_retro", [sys.executable, os.path.join(HERE, "test_chronicle_retro.py")], 300,
         why="the retro sweep's three laws: read-only until Apply, merge-max, pay-for-runs"),
    Gate("test_chronicle_template", [sys.executable, os.path.join(HERE, "test_chronicle_template.py")], 300,
         why="the Chronicle panel's own template is measured, not guessed — the page frame, its "
             "NO TOOLTIP ITEM state, and the MINI-parameter geometry a live read leans on, so the "
             "consumers due in v1691 have a locked shape to read instead of re-deriving it each time"),
    Gate("test_reel_index_durability", [sys.executable, os.path.join(HERE, "test_reel_index_durability.py")], 300,
         why="a sealed reel must always carry a parseable index.json — even when the seal is "
             "interrupted mid-way — because theatre, read_reel and the retro sweep all enter "
             "through the index, and a reel of real frames without one plays BLACK"),
    Gate("test_g5_budget_units", [sys.executable, os.path.join(HERE, "test_g5_budget_units.py")], 120,
         why="g5_subscription_budget.json had TWO writers on TWO clocks — Python seconds, Node "
             "milliseconds — so Python could never prune a Node row (it reads as 1.78 million "
             "million seconds in the FUTURE) and Node deleted every Python row. The count only "
             "climbed, and at 30 the second eye pins itself OFF behind a legitimate-looking "
             "'hourly cap (30/30)' while the real call rate is zero. It stood at 9. This is the "
             "FIRST test that has ever existed on the G5 lane"),
    Gate("test_chronicle_known_wire", [sys.executable, os.path.join(HERE, "test_chronicle_known_wire.py")], 300,
         why="sweep_hist(known_chronicle=) shipped in v1689 and NOTHING EVER PASSED IT, so every "
             "retro sweep re-derived what the live agent had already identified and paid a "
             "classifier to disagree with it. Measured on his own reel: a classifier that "
             "recognises nothing reads 0 pages without the marks and 8 with them. This is the "
             "v1576 defect class again — plumbing built on both ends and never joined"),
    Gate("test_chronicle_chain", [sys.executable, os.path.join(HERE, "test_chronicle_chain.py")], 300,
         why="the WHOLE chronicle chain in one pass — every other suite mocks its neighbours"),
    Gate("test_chronicle_visit_flush", [sys.executable, os.path.join(HERE, "test_chronicle_visit_flush.py")], 120,
         why="a Chronicle visit still OPEN when the session ends must still be journalled — "
             "looking at the Chronicle LAST is the normal way to register finds, and before "
             "v1689 that case wrote no visit row at all, so /api/chronicle_visits stayed []"),
    Gate("test_chronicle_route_guard", [sys.executable, os.path.join(HERE, "test_chronicle_route_guard.py")], 120,
         why="a frame the vision lane read as scene='chronicle' must never be routed into a "
             "stash/vault/tally intake — a kai-vault intake fired on a Chronicle page and came "
             "back ok:false total:0, and the refusal must be NAMED and COUNTED, not silent"),
    Gate("chronicle-doctor", [sys.executable, os.path.join(HERE, "chronicle_doctor.py")], 120,
         why="the arc is wired on THIS machine — lanes, footage, board build"),
    Gate("test_stash_eye_aspect", [sys.executable, os.path.join(HERE, "test_stash_eye_aspect.py")], 120,
         why="the stash crops must stay locked on Konyo's Mac AND reach 16:9 for the cousin"),
    Gate("test_console_fleet", [sys.executable, os.path.join(HERE, "test_console_fleet.py")], 180,
         why="the fleet tracker must SHOW the machines that were here — the 'console:' prefix also "
             "matched every 'consolelog:' key, and the offline window listed the OLDEST 400 events, "
             "so the cousin who ran it yesterday was invisible"),
    Gate("test_g5_grok_eyes", [sys.executable, os.path.join(HERE, "test_g5_grok_eyes.py")], 300,
         why="the vision-eye contract"),
    Gate("test_roundtrip_sim", [sys.executable, os.path.join(HERE, "test_roundtrip_sim.py")], 900,
         why="a full simulated session round trip"),
    Gate("robot_smoke", [sys.executable, os.path.join(HERE, "robot_smoke.py")], 120,
         why="the TV_ROBOT=1 frozen-boot lane must not rot — a 20s stub boot, no model call. "
             "⚠ It lived as a hand-listed CI step while the gate set knew nothing about it, so "
             "consolidating CI onto run_gates.py would have DROPPED it silently. It is not a "
             "tv/test_*.py, so TestNoOrphanSuite could never have caught the omission: that guard "
             "watches for suites missing from this list, and cannot see a runnable check that was "
             "never named as one"),
    Gate("test_button_matrix", [sys.executable, os.path.join(HERE, "test_button_matrix.py")], 300,
         needs_app=True,
         why="every app button, against the LIVE control API"),
]

SKIP_EXIT = 77          # a gate that could not run (must match tv/js_syntax_gate.py)

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
            # v1601 — exit 77 means "I could not run", not "I passed". Without this a gate that
            # self-skipped printed its own ⚠ SKIPPED line and still got counted green, which is the
            # lie this file's docstring opens by forbidding. js-syntax skips on every local run on
            # Konyo's Mac, so the surface least protected was the one showing a tick.
            if p.returncode == SKIP_EXIT:
                status = "SKIP"
            else:
                status = "PASS" if p.returncode == 0 else "FAIL"
            results.append((g, status, dt, tail[0][:150]))
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
