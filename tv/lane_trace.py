#!/usr/bin/env python3
"""THE ARTEFACT A LOOP LEAVES BEHIND — one small file per lane, datable by any process.

⚠⚠ WHY THIS EXISTS, MEASURED 2026-09-13. Six surfaces sat at 3 of 4 organs and every one was
missing the SAME organ, the corroborator. That organ needs TWO INDEPENDENT witnesses and for a
loop the natural pair is (a) it stamped a tick and (b) the trace it left. Two of the eight loops
leave a real artefact — `_ledger_backup_loop` writes backup files, `_vault_autoread_loop` writes
`.vault_autoread.json`. The rest computed a result and threw it away in memory.

⚠ THE TICK IS NOT A SECOND WITNESS. `lane_liveness._TICKS` is an in-process dict on a
`time.monotonic()` clock; a separate process sees it EMPTY. Measured: `rows()` returned 0 lanes
while his console was healthy. So a loop with only a tick has ONE witness and no outside reader
can date it at all. [[feedback-suspect-the-instrument]]

⚠⚠ AND THIS MUST CARRY THE LOOP'S RESULT, NOT A BARE HEARTBEAT. A heartbeat would prove only
"the thread woke up", which the watchdog already answers — a second organ saying the first
organ's sentence is not corroboration, it is an echo. What makes this independent is that it
records WHAT THE LOOP DECIDED: the drift verdict, the orphan count, the shadow result. A loop
that is running and producing nothing then reads as a CONTRADICTION rather than as health, and
that contradiction is the only thing this organ can see that no other organ can.

ONE FILE PER LANE, on purpose:
  · mtime is then per-lane, which is exactly the shape `loop_corroborate.LOOPS` already reads
  · no shared-file lock contention between loops ticking at different periods
  · a torn write can never take another lane's trace with it

⚠ WRITES ARE ATOMIC. A plain open(p, "w") TRUNCATES BEFORE IT WRITES, so a crash mid-write leaves
an empty file that reads as "the loop produced nothing" — the exact false alarm this module
exists to prevent. Write to a temp name in the same directory, then os.replace.
[[bible-writes-must-be-atomic]]

⚠ THROTTLE, AND DECLARE THE THROTTLED PERIOD. `_orphan_exit_loop` ticks every 5 s; writing a file
that often is churn on his disk for no added truth. `note(..., min_gap_s=)` skips a write whose
predecessor is younger than the gap — but then the TRACE period is the gap, not the tick period,
and `loop_corroborate.LOOPS` must declare THE GAP. Declaring the tick period instead would make a
correctly-throttled loop read as stale within one staleness window.
"""
import io
import json
import os
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, ".lane_trace")


def path_of(lane):
    """The artefact this lane writes. -> str (it need not exist)"""
    safe = "".join(c if (c.isalnum() or c in "-_.") else "_" for c in str(lane))
    return os.path.join(DIR, "%s.json" % safe)


RAN = "RAN"
DORMANT = "DORMANT"      # deliberately not running, and the reason is KNOWN


def note_dormant(lane, why):
    """This lane is deliberately NOT running, and here is why. -> bool

    ⚠⚠ WITHOUT THIS, A DORMANT LANE IS INDISTINGUISHABLE FROM A DEAD ONE. `_orphan_exit_loop`
    RETURNS before its while-loop whenever there is no TV_PARENT_PID — which is ALWAYS the case on
    his primary console, by design, because a console nobody started must never self-exit. It
    therefore never ticks and never will. `lane_liveness.dormant()` records exactly this, but into
    an in-process dict that no outside reader can see, the same blindness as `_TICKS`.

    So an organ reading only ticks-and-traces would report his healthiest console as carrying a
    dead lane, forever. A fabricated alarm about a working machine is worse than an honest gap.
    [[unknown-stays-unknown]]
    """
    if not str(why or "").strip():
        return False       # a dormancy with no reason is UNKNOWN wearing a verdict's clothes
    return note(lane, state=DORMANT, why=str(why)[:300])


def note(lane, min_gap_s=0.0, state=RAN, **result):
    """Record what this lane just DECIDED. -> bool (False = throttled or unwritable)

    Never raises: a loop must not die because its trace could not be written. A failed write
    leaves the previous artefact in place, which ages and is read as stale — the honest outcome.
    """
    p = path_of(lane)
    try:
        if min_gap_s:
            try:
                if (time.time() - os.path.getmtime(p)) < float(min_gap_s):
                    return False
            except OSError:
                pass                      # no predecessor -> write it
        if not os.path.isdir(DIR):
            os.makedirs(DIR, exist_ok=True)
        body = json.dumps({"lane": str(lane), "ts": int(time.time() * 1000),
                           "state": str(state), "result": result}, sort_keys=True)
        fd, tmp = tempfile.mkstemp(prefix=".lt.", dir=DIR)
        try:
            with io.open(fd, "w", encoding="utf-8") as fh:
                fh.write(body)
            os.replace(tmp, p)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        return True
    except Exception:
        return False


def read(lane):
    """This lane's last recorded decision. -> (dict, ok). ok False = UNKNOWN, never "no work"."""
    try:
        with io.open(path_of(lane), encoding="utf-8") as fh:
            blob = json.load(fh)
        return (blob if isinstance(blob, dict) else {}), isinstance(blob, dict)
    except Exception:
        return {}, False


def age_ms(lane, now_ms=None):
    """How old this lane's trace is. -> (float, ok). ok False = no readable trace = UNKNOWN."""
    blob, ok = read(lane)
    if not ok:
        return 0.0, False
    ts = blob.get("ts")
    if not isinstance(ts, (int, float)):
        return 0.0, False
    now = now_ms if now_ms is not None else time.time() * 1000.0
    return max(0.0, float(now) - float(ts)), True


if __name__ == "__main__":
    # ⚠ THIS FILE CARRIES NON-ASCII AND PRINTS. On a non-UTF-8 console an unguarded print crashes
    # WHILE REPORTING, so a clean tree exits non-zero and the failure looks like a defect in the
    # thing being reported rather than in the reporting. Same guard as loop_corroborate.py.
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
    import sys
    for ln in (sys.argv[1:] or sorted(os.path.splitext(f)[0] for f in os.listdir(DIR))
               if os.path.isdir(DIR) else []):
        a, ok = age_ms(ln)
        print("%-26s %s" % (ln, ("%.1fs ago" % (a / 1000.0)) if ok else "UNKNOWN (no trace)"))
