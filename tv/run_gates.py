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
import fcntl
import glob
import os
import re
import tempfile
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
    Gate("test_inbox_engine", [sys.executable, os.path.join(HERE, "test_inbox_engine.py")], 300,
         why="v1794 — bible.html's inbox fold and chronicle_resolve.py's fold must answer "
             "identically. The board cannot call the Python (it is a file:// page and a phone he "
             "opens mid-game), so the second implementation is forced; a second BEHAVIOUR is not. "
             "This extracts the SHIPPED block out of bible.html, runs it in node, and fails on the "
             "first name where the two disagree — a drifted cutoff folds 'Gul' onto 'Gull' and "
             "writes a find he never made"),
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
    Gate("test_kai_missed_recoverable",
         [sys.executable, os.path.join(HERE, "test_kai_missed_recoverable.py")], 120,
         why="a session close that reports 'N frames held text no eye read' must NAME those "
             "frames, not just count them. It journalled 20 verbose rows and nothing else, so on "
             "his 108-frame session the headline was honest while 88 frames existed only inside a "
             "number and no sweep could ever find them"),
    Gate("test_chronicle_still_threshold",
         [sys.executable, os.path.join(HERE, "test_chronicle_still_threshold.py")], 120,
         why="the chronicle sweep's still threshold must stay BELOW what jpeg_sig can produce. At "
             "the shared 0.22 it was above the ceiling of the measurement (largest real diff: "
             "0.133), so no frame pair ever broke a run, a whole 217-frame session became ONE run, "
             "and 9 of his 10 reels read zero pages. Synthetic on purpose so it runs on CI, where "
             "his footage cannot exist"),
    Gate("test_chronicle_seal", [sys.executable, os.path.join(HERE, "test_chronicle_seal.py")], 120,
         why="the retro sweep must never seal a reel it did not read. chronicle_swept.json hides "
             "every reel it names from all future sweeps, and the loop used to record even a "
             "no-index reel that read NOTHING — footage lost until a full `force` re-run. The "
             "tests EXECUTE the shipped loop out of control_app.py rather than copying it, so a "
             "widened predicate turns them red instead of quietly passing"),
    Gate("test_button_matrix", [sys.executable, os.path.join(HERE, "test_button_matrix.py")], 300,
         # v1711 — needs_app was TRUE, so this gate was skipped before it could even try, on
         # every run where Konyo did not happen to have his console open. It now BOOTS ITS OWN
         # control_app on a free ephemeral port (never :17772, his live one) and stops it after,
         # so it runs unattended and in CI. It still reports SKIP — never a pass — if that private
         # instance cannot come up.
         needs_app=False,
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
            results.append((g, "SKIP", 0.0, "control app is not running on :17772", ""))
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
            results.append((g, status, dt, tail[0][:150], blob if status == "FAIL" else ""))
        except subprocess.TimeoutExpired:
            results.append((g, "FAIL", time.time() - t0,
                            "timed out after %ds — a hung gate is a failed gate" % g.timeout, ""))
        except OSError as e:
            results.append((g, "SKIP", time.time() - t0, "could not launch (%s)" % e, ""))
    return results


# v1751 — ONE GATE RUN PER TREE. This is REG-162's reproduced cause, not a theory: two runs were
# started at once and each failed a DIFFERENT gate (robot_smoke in one, test_roundtrip_sim in the
# other) while a clean single run passed 30/30. Every one of those gates passes alone. They share
# ports, reel directories and the journal, so whichever gate happens to need an exclusive one loses
# — and the verdict names the loser, never the collision. A gate that is wrong about the tree
# because of what else is running is the worst kind of red: it sends you to debug working code.
#
# flock, deliberately: the kernel drops it when the process dies, so a crashed or kill -9'd run
# cannot leave a stale lock that refuses every future run. A pid file would need reaping logic, and
# reaping logic is how a lock starts lying.
#
# KEYED ON THE RESOLVED TREE, not on a fixed path, so his two worktrees can gate in parallel — they
# have separate reel dirs and separate journals, and the collision this prevents is within ONE tree.
# [[process-port-discipline]]
_LOCK_FH = None


def _claim_the_tree():
    """Take the per-tree gate lock, or explain who has it. Returns None on success, else a message."""
    global _LOCK_FH
    # D2R_GATE_LOCK_KEY exists for ONE reason: test_control.py is itself a gate, so when CI runs
    # `python3 tv/run_gates.py` the outer run holds this lock while TestOneGateRunPerTree spawns
    # child gate runs to prove the lock works. Without an override those children are refused BY
    # THE RUN TESTING THEM, and the test fails on CI while passing on every laptop — a gate blind
    # to its own venue. The children get their own key; the mechanism under test is unchanged.
    key = os.environ.get("D2R_GATE_LOCK_KEY") or os.path.realpath(REPO)
    safe = re.sub(r"[^A-Za-z0-9]+", "_", key).strip("_")[-80:]
    path = os.path.join(tempfile.gettempdir(), "d2r_gates_%s.lock" % safe)
    fh = open(path, "a+")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.seek(0)
        who = (fh.read() or "").strip() or "an unnamed run"
        fh.close()
        return ("another gate run already holds this tree (%s).\n"
                "   Two runs share ports, reel dirs and the journal, so a gate that needs an "
                "exclusive one fails and the verdict blames the gate.\n"
                "   That is REG-162's signature. Wait for it, or run in a separate worktree."
                % who)
    fh.seek(0)
    fh.truncate()
    fh.write("pid %d, started %s, tree %s\n"
             % (os.getpid(), time.strftime("%Y-%m-%d %H:%M:%S"), key))
    fh.flush()
    _LOCK_FH = fh   # held for the life of the process; the kernel releases it on exit
    return None


# ── FIXTURES NEVER TOUCH LIVE DATA — enforced, not intended ────────────────────────────────────
# The console keeps its state in files beside this script: the persisted sweep, the swept-reel
# marks, the visit marks. Those belong to the RUNNING console on his Mac, and a test must never
# write them.
#
# It did. test_chronicle_chain drove _chron_visit_run directly with the live paths still in place,
# so every gate run on this machine overwrote tv/chron_last_result.json with the fixture "Harlequin
# Crest"/"Windforce" from reels s_100/200/300. Found by opening that file expecting his footage.
#
# It turned dangerous the same day v1765 taught his board to ADOPT a persisted sweep automatically:
# the fixture carries four witnesses, so it would have been applied rather than queued, and neither
# name is in his grail. Two finds he never made, written into the dataset that is meant to be his
# own truth, by his own test suite.
#
# Redirecting the paths in that one setUp fixes today. This makes it STRUCTURAL: the runner
# fingerprints the live files before the set and again after, and fails the whole run if anything
# moved. A future test that forgets cannot pass quietly - which is the only kind of guard worth
# having, because the failure mode here is silent by construction.
# v1778 — THESE NAMES ARE READ FROM control_app.py, NOT GUESSED. The first version of this tuple
# listed "autoread.json" and "chronicle_autoread.json"; the real file is chron_autoread.json, so the
# guard built to catch REG-179 was blind to the visit-mark file for its whole life. Caught by
# review_lite.py, which compares this tuple against the _*_PATH constants themselves.
_LIVE_STATE = ("chron_last_result.json", "chronicle_swept.json", "chron_autoread.json",
               "chron_evidence.json", "vault_swept.json")


def _console_is_running(port=17772):
    """v1774 — the guard below cannot tell a TEST writing his console state from the CONSOLE writing
    it, and the console writes those files as its normal job. Accusing the suite because his app is
    open would be a false red, and a gate that cries wolf gets ignored — so the check is SKIPPED and
    said out loud, never quietly passed. [[feedback_silence_is_not_evidence]]"""
    import socket
    s = socket.socket()
    s.settimeout(0.4)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


_SWEEP_LOCK = os.path.join(HERE, ".sweep.lock")


def _sweep_in_progress(max_age_s=900):
    """v1780 — A SWEEP DECLARES ITSELF, because lsof cannot see one.

    The first attempt asked the kernel who held the state files open; a sweep writes them with
    tmp+rename, so it holds nothing and the guard still blamed the suite. A lock file with a
    heartbeat is the honest signal: a sweep touches it while it runs, and a stale one (older than
    max_age_s) is ignored so a crashed sweep cannot disable the guard forever.
    """
    try:
        age = time.time() - os.path.getmtime(_SWEEP_LOCK)
        return age < max_age_s
    except Exception:
        return False


def _external_writer(names=_LIVE_STATE):
    """v1780 — IS SOMETHING OTHER THAN THE SUITE WRITING THESE RIGHT NOW?

    The guard exists to catch a TEST writing his console state. A background sweep writing the
    accumulated ledger is legitimate and the fingerprint cannot tell them apart, so it accused the
    suite of a change a chronicle sweep had just made. A gate that cries wolf gets disabled, so ask
    the kernel instead: if a process outside this run holds one of these files open, the check is
    SKIPPED and said out loud rather than failed. [[feedback_suspect_the_instrument]]
    """
    import subprocess
    held = []
    for n in names:
        p = os.path.join(HERE, n)
        if not os.path.exists(p):
            continue
        try:
            r = subprocess.run(["lsof", "-t", p], capture_output=True, text=True, timeout=5)
            pids = [x for x in (r.stdout or "").split() if x.strip() and int(x) != os.getpid()]
            if pids:
                held.append("%s (pid %s)" % (n, ",".join(pids[:3])))
        except Exception:
            pass
    return held


def _live_fingerprint():
    import hashlib
    out = {}
    for n in _LIVE_STATE:
        p = os.path.join(HERE, n)
        try:
            with open(p, "rb") as fh:
                out[n] = hashlib.sha256(fh.read()).hexdigest()[:16]
        except FileNotFoundError:
            out[n] = None          # absent is a state too, and creating one IS a mutation
        except Exception as e:
            out[n] = "unreadable:%s" % e
    return out


def _live_state_diff(before, after):
    moved = []
    for n in _LIVE_STATE:
        b, a = before.get(n), after.get(n)
        if b != a:
            was = "absent" if b is None else b
            now = "absent" if a is None else a
            moved.append("%s (%s -> %s)" % (n, was, now))
    return moved


def main(argv):
    ap = argparse.ArgumentParser(description="run the gate set and return one verdict")
    ap.add_argument("--only", nargs="*", help="run only these gate names")
    a = ap.parse_args(argv[1:])

    busy = _claim_the_tree()
    if busy:
        print("⛔ REFUSED — %s" % busy)
        return 2

    print("══ GATE SET ══")
    _console_live = _console_is_running()
    _sweep_live = _external_writer()
    if _sweep_in_progress():
        _sweep_live = _sweep_live or ["a chronicle sweep (tv/.sweep.lock)"]
    _live_before = _live_fingerprint()
    results = run(a.only)
    _live_moved = _live_state_diff(_live_before, _live_fingerprint())
    for g, status, dt, detail, _blob in results:
        mark = {"PASS": "✅", "FAIL": "❌", "SKIP": "⚠"}[status]
        print("%s %-20s %6.1fs  %s" % (mark, g.name, dt, detail))

    failed = [g.name for g, s, _, _, _ in results if s == "FAIL"]
    if _live_moved and not _console_live and not _sweep_live:
        # not a warning: a suite that writes his console's state has already done the damage
        failed.append("live-state-untouched")
    skipped = [(g.name, d) for g, s, _, d, _ in results if s == "SKIP"]
    print("\n── VERDICT ──")
    if _live_moved and (_console_live or _sweep_live):
        why = "the console is running on :17772" if _console_live else ("held by %s" % ", ".join(_sweep_live))
        print("⚠ SKIPPED live-state check — %s, so a change here is not the suite" % why)
        for m in _live_moved:
            print("     %s" % m)
    if _live_moved and not _console_live and not _sweep_live:
        print("❌ THE SUITE WROTE THE LIVE CONSOLE STATE — a fixture reached his data:")
        for m in _live_moved:
            print("     %s" % m)
        print("   Redirect the path in that test's setUp; never write files beside control_app.py.")
    if skipped:
        # never silent: a check that did not happen is not a check that passed
        for n, d in skipped:
            print("⚠ SKIPPED %s — %s" % (n, d))
    if failed:
        # v1711 — SAY WHICH TEST, NOT JUST WHICH GATE.
        # The summary line was the gate's LAST output line, which for a unittest run is
        # "FAILED (failures=1)" — a fact with no address. A CI log carrying that and nothing else
        # cannot be diagnosed remotely, and these gates include browser lanes that SKIP on Konyo's
        # Mac (Chrome never answers --dump-dom over loopback there) and therefore run ONLY on CI.
        # So the one machine that can produce those failures was also the one that could not
        # report them, and the answer was to guess. Now the log carries the addresses.
        for g, st, _dt, _d, blob in results:
            if st != "FAIL":
                continue
            names = [ln.strip() for ln in blob.split("\n")
                     if ln.startswith(("FAIL:", "ERROR:")) or "AssertionError" in ln]
            print("\n── %s — what actually broke ──" % g.name)
            for ln in (names[:12] or [ln for ln in blob.strip().split("\n") if ln.strip()][-12:]):
                print("   " + ln[:200])
            if len(names) > 12:
                print("   … and %d more" % (len(names) - 12))
        print("\n❌ %d gate(s) FAILED: %s" % (len(failed), ", ".join(failed)))
        return 1
    print("✅ %d gate(s) passed%s."
          % (len(results) - len(skipped), (", %d skipped" % len(skipped)) if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
