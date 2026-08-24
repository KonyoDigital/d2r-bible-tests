"""THE SUITE'S CANARIES — the tests must not be able to damage what they are testing.

Three things live in this file, and all three exist because a mechanism READ AS PROTECTION AND
CARRIED NOTHING:
  1. `live_data_is_not_collateral` — fingerprints the irreplaceable gitignored files and fails the
     session if a test changed their bytes. The incident is below.
  2. `redirect_module_path(module, attr, tmp_path)` — the API a path-redirecting test must use, so
     the isolation is ASSERTED rather than assumed. Prevention for the same incident.
  3. `no_orphaned_children` — fails the session naming any child process the suite left running.
     A suite once left tv/tv_diablo.py alive for 22 minutes, writing into live state.

## 1. THE LIVE-DATA CANARY — the suite must not be able to destroy what it is testing.

WHAT IT COST TO LEARN, 2026-08-21. A test written to prove that a not-found receipt survives the
chronicle chain redirected the evidence store with `os.environ["TV_CHRON_EVIDENCE"] = <tmp>` and
then called the real save. **`_CHRON_EVIDENCE_PATH` is a module-level constant bound from that
variable when control_app is first imported** — which, inside a suite, has already happened. The
environment assignment was a no-op. The write landed on his real banked evidence and truncated
`tv/chron_evidence.json` from **525,187 bytes to 748**: 298 proposed uniques and 86 set pieces
across 767 page reads that were each paid for by a real model call, replaced by a two-item fixture.

It was recovered in full, and only by luck: `chron_last_result.json` happens to hold the same
proposal object. Had it not, the only way back would have been re-reading his entire reel history at
full price.

WHY THIS AND NOT A STATIC CHECK. The obvious guard — "no test may assign a live-path env var inside
a function body" — was written first and returned **26 hits, nearly all correct code**: `TV_HIST` and
`TV_SESSIONS` are read at call time as well as at import, so redirecting them mid-test genuinely
works. A guard with 26 false positives is a guard nobody reads. This one has none, because it does
not reason about mechanism at all — it asks the only question that matters: *did the bytes change?*

EVERY FILE BELOW IS GITIGNORED. There is no git recovery for any of them. That is the whole reason
this exists.

⚠ IT IS A CANARY, NOT A LOCK. It reports damage after the fact; it cannot prevent it. The rule it
enforces is the one the incident actually violated: **patch the module ATTRIBUTE, then assert the
redirect took.** Setting up an isolation and never checking it took is the defect — the fixture
looked isolated and was not. [[feedback-fixtures-never-touch-live-data]]
"""
import contextlib
import hashlib
import os
import signal
import subprocess
import sys
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))

# The irreplaceable ones: banked reads, the sweep result, the journal, the visit ledgers. Anything
# whose bytes were paid for by a real model call or by him actually playing belongs here.
LIVE_FILES = (
    "chron_evidence.json",      # banked page reads — the most expensive bytes the console holds
    "chron_last_result.json",   # the last proposal; also the only backstop the incident above had
    "chron_reads.json",
    "chron_autoread.json",
    "chronicle_swept.json",
    "state.json",
    "sessions.jsonl",           # his play journal
    "vault_ledger.json",
    "g5_stats.json",            # cumulative G5 lane counters — 1,731 real calls, no other copy
    "g5_subscription_budget.json",  # the call-timestamp ledger the 240/day cap is computed FROM
    "known_frames.json",        # frame fingerprints learned from him actually playing
    # v2080 — THE CANARY DID NOT KNOW ABOUT THESE, so a test wrote all four and nothing said a word.
    # TestV2078 called the real _eagle_once(), which tends the scar ledger unconditionally. The
    # ledger is the durable record of which faults have COME BACK — it cannot be re-derived from
    # anything, which is exactly the bar this tuple is for. The .healer_bak files are the only copy
    # of his vault stores that exists outside a window's localStorage.
    ".console_scars.json",
    "vault_accum.json.healer_bak",
    "vault_seen.json.healer_bak",
    "vault_swept.json.healer_bak",
)
# Deliberately NOT listed, and the reason is one command: `git ls-files --error-unmatch`.
# stub_manifest.json, vault_accum.json, vault_corpus_index.json, stash_grid_truth.json,
# set_roster.json, unique_roster.json, chronicle_audit_baseline.json, WINDOWS_SHIP.json and
# g5_second_lane_v1789.json are all TRACKED, so `git checkout` restores them byte-for-byte.
# This tuple is for bytes that have no way back — not for everything a test might touch.


# v2080 — AND PREVENT IT, not only catch it. The canary above reports a write AFTER it happened;
# this makes the write impossible for the whole session by pointing the scar ledger at a throwaway
# root before any test imports console_healer. Guard the PATH, not the call site — the same rule
# that kept vault_accum.json safe on the night the scar ledger was not.
def _pin_scar_ledger_away_from_his_tree():
    import tempfile
    if not os.environ.get("TV_SCAR_ROOT"):
        os.environ["TV_SCAR_ROOT"] = tempfile.mkdtemp(prefix="scarledger_test_")


_pin_scar_ledger_away_from_his_tree()


def _fingerprint(path):
    """(size, sha1) or None when absent. Absence is recorded too: a suite that CREATES one of these
    has also touched live state, and 'it did not exist before' must not read as 'nothing happened'."""
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except FileNotFoundError:
        return None
    except OSError:
        return "unreadable"
    return (len(data), hashlib.sha1(data).hexdigest())


def _live_console_pids():
    """PIDs of a RUNNING console (`control_app.py --open`) — the one legitimate writer of these
    files that is not this test process.

    ⚠ v1925 — THE CANARY WAS GOING RED FOR A NEIGHBOUR'S REASON, which is the exact class it was
    written to close. An adversarial review measured it: with Konyo's own console alive (pid 96342,
    mid-G5 chronicle call), a clean suite errored with

        A TEST WROTE TO LIVE DATA ... sessions.jsonl 1973509->1974432,
        g5_stats.json 214->213, g5_subscription_budget.json 1205->1395

    and then blamed a fixture env-redirect that never happened. An immediate re-run on the identical
    tree: 0 errors. A 50s idle probe with no test running showed all three files quiescent, and the
    only process holding them was his console.

    An unreproducible red that names a data-loss incident is worse than no canary: the first two
    times it cries wolf, the third real one is furniture. So the question is no longer "did the
    bytes change" alone — it is "did the bytes change AND is there anyone else who could have
    changed them". [[feedback-blind-fixture-green-gate]] [[feedback-suspect-the-instrument]]

    Kill nothing, touch nothing — this only LOOKS. `pkill`-style name matching is banned here; this
    reads the process table and returns PIDs.
    """
    try:
        out = subprocess.run(["ps", "-A", "-o", "pid=,command="],
                             capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return []
    pids = []
    me = os.getpid()
    for line in out.splitlines():
        line = line.strip()
        if not line or "control_app.py" not in line:
            continue
        head = line.split(None, 1)
        if not head:
            continue
        try:
            pid = int(head[0])
        except ValueError:
            continue
        if pid == me:
            continue
        pids.append(pid)
    return pids


@pytest.fixture(scope="session", autouse=True)
def live_data_is_not_collateral():
    before = {n: _fingerprint(os.path.join(HERE, n)) for n in LIVE_FILES}
    console_before = _live_console_pids()
    yield
    damaged = []
    for n in LIVE_FILES:
        after = _fingerprint(os.path.join(HERE, n))
        if after == before[n]:
            continue
        b, a = before[n], after
        if b is None:
            damaged.append("%s was CREATED by the suite (%s bytes)"
                           % (n, a[0] if isinstance(a, tuple) else a))
        elif a is None:
            damaged.append("%s was DELETED by the suite (was %s bytes)"
                           % (n, b[0] if isinstance(b, tuple) else b))
        else:
            bs = b[0] if isinstance(b, tuple) else "?"
            as_ = a[0] if isinstance(a, tuple) else "?"
            damaged.append("%s changed: %s bytes -> %s bytes" % (n, bs, as_))
    if not damaged:
        return
    # ATTRIBUTE BEFORE ACCUSING. A live console writes sessions.jsonl and the G5 ledgers as part of
    # doing its job; those writes are not the suite's and must never be reported as data loss.
    console = sorted(set(_live_console_pids()) | set(console_before))
    if console:
        sys.stderr.write(
            "\n[live-data canary] %d live file(s) changed during this run, and a console was "
            "running (pid %s) — attributing the writes to it rather than to the suite:\n  %s\n"
            "  This is NOT a failure. If you believe a test did it, stop the console and re-run; "
            "with no other writer the canary fails loudly.\n"
            % (len(damaged), ", ".join(str(p) for p in console), "\n  ".join(damaged)))
        return
    pytest.fail(
        "A TEST WROTE TO LIVE DATA, and no console was running to explain it. These files are "
        "gitignored — there is no git recovery:\n  "
        + "\n  ".join(damaged)
        + "\n\nAlmost certainly a fixture redirected a path with os.environ[...] instead of "
          "patching the module attribute. Path constants like control_app._CHRON_EVIDENCE_PATH "
          "are bound ONCE at import, so setting the env var inside a test changes nothing and "
          "the write lands on his real files. Use conftest.redirect_module_path, which patches "
          "the attribute and ASSERTS the redirect took before you write anything.",
        pytrace=False)


# ─────────────────────────────────────────────────────────────────────────────
# THE REDIRECT-TOOK HELPER — prevention for the incident in the module docstring
# ─────────────────────────────────────────────────────────────────────────────

# The helper lives in tv/pathguard.py so a SCRIPT-run suite (run_gates.py runs each file with
# plain python3, on a runner with no pytest) can import it without dragging pytest in. Re-exported
# here so `from conftest import redirect_module_path` keeps working for pytest-run suites.
from pathguard import redirect_module_path  # noqa: E402,F401


@pytest.fixture
def redirect_path():
    """Fixture form of `redirect_module_path`, for tests that prefer injection over import:

        def test_x(redirect_path, tmp_path):
            with redirect_path(control_app, "_CHRON_EVIDENCE_PATH", tmp_path / "ev.json"):
                ...
    """
    return redirect_module_path


# ─────────────────────────────────────────────────────────────────────────────
# THE PROCESS CANARY — the suite must not leave children running on his machine
# ─────────────────────────────────────────────────────────────────────────────

def _live_processes():
    """{pid: (ppid, command)} for every process on the box, plus the pid of the `ps` we ran.

    `ps` lists ITSELF, and it is a child of this process, so its own pid must be excluded or
    every snapshot reports one phantom leak. psutil is deliberately not used — it is not
    guaranteed installed here.
    """
    try:
        proc = subprocess.Popen(["ps", "-eo", "pid,ppid,command"],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        out, _ = proc.communicate(timeout=30)
    except Exception:
        return None, None
    table = {}
    for line in out.splitlines()[1:]:
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        try:
            pid, ppid = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        table[pid] = (ppid, parts[2])
    return table, proc.pid


def _descendants(table, root_pid, exclude=()):
    """Every pid whose parent chain reaches root_pid. Walked from the table, so a child that
    re-parented to launchd (ppid 1) after its spawner died is NOT claimed — we only ever kill
    what we can still prove is ours."""
    kids = {}
    for pid, (ppid, cmd) in table.items():
        kids.setdefault(ppid, []).append(pid)
    seen, stack = set(), list(kids.get(root_pid, []))
    while stack:
        pid = stack.pop()
        if pid in seen or pid in exclude or pid == root_pid:
            continue
        seen.add(pid)
        stack.extend(kids.get(pid, []))
    return seen


@pytest.fixture(scope="session", autouse=True)
def no_orphaned_children():
    """Fail the session naming any process the suite spawned and never reaped.

    WHAT IT COST TO LEARN, 2026-08-21. A suite spawned `tv/tv_diablo.py` and never reaped it.
    It ran for **22 minutes** after the tests finished, writing stub reads into the live
    `tv/state.json` and spending **39 of a 240-a-day read cap** — and its pid was baked into the
    session id, so the damage was signed by the process nobody knew was alive.

    The report is built BEFORE anything is killed, and only pids proven to be descendants of
    this pytest process are ever signalled. `pkill -f` is banned in this repo: a name pattern
    matches his own long-running console just as happily as the test's orphan.
    """
    table, _ = _live_processes()
    mine = os.getpid()
    before = _descendants(table, mine) if table else set()
    yield
    table, ps_pid = _live_processes()
    if table is None:
        return
    leaked = sorted(_descendants(table, mine, exclude={ps_pid}) - before)
    if not leaked:
        return
    lines, reaped = [], []
    for pid in leaked:
        cmd = table[pid][1]
        lines.append("pid %d  %s" % (pid, cmd[:160]))
        if "<defunct>" in cmd:
            continue
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.kill(pid, 0)
            except OSError:
                break
            try:
                os.kill(pid, sig)
                reaped.append(pid)
            except OSError:
                break
            time.sleep(0.4)
    tail = ("\nReaped by pid after reporting: %s" % sorted(set(reaped))) if reaped else ""
    pytest.fail(
        "A TEST LEFT A CHILD PROCESS RUNNING. Descendants of this pytest process (%d) that were "
        "alive when the session ended:\n  %s\n\n"
        "This is not tidiness. A suite once left tv/tv_diablo.py running for 22 minutes after "
        "the tests finished: it wrote stub reads into the live tv/state.json and spent 39 of a "
        "240-a-day read cap, signed with the orphan's own pid. Reap every Popen in a "
        "try/finally (terminate(), then wait(timeout=...), then kill()), or use a fixture that "
        "does. Kill by PID or by port — never `pkill -f`.%s"
        % (mine, "\n  ".join(lines), tail),
        pytrace=False)
