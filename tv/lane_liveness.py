#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IS THIS LANE ALIVE? — the fact none of the stores on disk can answer.

⚠⚠ WHY THIS EXISTS, AND WHY IT IS NOT THE HEARTBEAT THAT WAS CANCELLED. His A1 ruling stands and
is quoted here on purpose: *"I DO NOT want this to randomly just connect wires to it if theres no
need dont do it"*. It cancelled a heartbeat once already, correctly — the vault in/out lanes were
each leaving a DATED ROW (`vault_swept.json` 30 of 30, `retro_triage.json` 437 of 437,
`reel_tombstones.json` 410 of 410), so a heartbeat there would have been **a second copy of a fact
already on disk**.

**This is a different fact.** Those rows record WORK DONE. Nothing records THREAD ALIVE, and the
two come apart the moment a lane has nothing to do. Measured 2026-09-04: `retro_triage_tick()` has
**six early returns before it writes anything** — the lane is off, he is playing, load is too high,
a capture is live, a paid sweep owns the CPU, or there is nothing to triage. On any of those it
returns having written nothing at all. So the age of `retro_triage.json` cannot distinguish:

    · the loop ran and correctly declined          (healthy)
    · the loop died three days ago                 (broken, and invisible)

Both look identical from disk: a store that stopped growing. On his machine at the time of writing,
`disk_history.jsonl` (0.1h) and `shadow_watch.json` (0.0h) prove some lanes are ticking, while
`retro_triage.json` (75.7h), `vault_swept.json` (77.9h) and `chron_autoread.json` (86.8h) have
written nothing for three to four days **with the console up the whole time**. Which of those are
healthy-and-idle and which are dead is not answerable today, by anyone.

⚠ AND IT IS NOT HYPOTHETICAL. `_console_rescue_loop` is itself one of the six SUPERVISORS nothing
supervises (REG-589), and two real defects were found in it on 2026-09-04 (REG-594, REG-596). Had
it DIED rather than misjudged, nothing anywhere would have noticed — the console would simply have
stopped being rescued, silently, forever.

⚠⚠ EVERY LANE DECLARES ITS OWN PERIOD, AND A GLOBAL THRESHOLD WOULD HAVE BEEN THE WHOLE BUG.
Measured across the console's loops: `_mini_watchdog` sleeps **0.5s** and `_retention_loop` sleeps
**900s** — a spread of 1,800x. One constant cannot serve both: set for the fast lane it reports
every slow lane dead, set for the slow lane it cannot see a fast one stop for a quarter of an hour.
So the period travels WITH the stamp, from the loop that owns it.
[[feedback-threshold-above-the-ceiling]]

⚠ A LANE WITH NO DECLARED PERIOD IS `UNTIMED`, NOT LATE. `_ledger_backup_loop` sleeps a computed
`_wait`, and `_engine_driver` has four different sleeps. Their age is real and their staleness is
not decidable, which is a third answer and not a soft version of either other one.
[[unknown-stays-unknown]]

⚠ MONOTONIC, for the reason `ui_beat_age()` is: on macOS `time.monotonic()` does not advance while
the machine is asleep. Wall time would report a Mac closed overnight as eight hours of silence from
every lane in the console.
"""
import threading
import time

#: how many periods a lane may miss before it is LATE. 1.0 would flag every ordinary jitter — a
#: lane that sleeps 20s and ticks at 20.3s is not stalling — and a gate that cries wolf is one he
#: learns to skip. 3 missed periods is a lane that has stopped, not a lane that was busy.
STALE_SLACK = 3.0

FLOWING = "FLOWING"      # ticked within its own declared period
LATE = "LATE"            # ticked, but longer ago than its period allows
UNTIMED = "UNTIMED"      # ticked, and it declares no period — age known, staleness not decidable
UNKNOWN = "UNKNOWN"      # never ticked. NOT "dead": it may be switched off, or never started

_LOCK = threading.Lock()
_TICKS = {}


def tick(lane, every_s=None):
    """Record that `lane` just ran a cycle. Called from inside the loop, once per turn.

    `every_s` is the loop's OWN sleep interval, passed from the loop that owns it rather than
    inferred here — see the module docstring for why a single global threshold is wrong by three
    orders of magnitude. Pass None when the interval is computed at runtime; that is UNTIMED, and
    it is an honest answer.
    """
    lane = str(lane or "").strip()
    if not lane:
        raise ValueError("tick() needs a lane name - an unnamed stamp cannot be read by anyone")
    try:
        every = float(every_s) if every_s is not None else None
    except (TypeError, ValueError):
        every = None
    if every is not None and every <= 0:
        every = None
    with _LOCK:
        row = _TICKS.get(lane)
        if row is None:
            row = {"mono": None, "everyS": every, "n": 0}
            _TICKS[lane] = row
        row["mono"] = time.monotonic()
        row["n"] += 1
        # ⚠ THE PERIOD IS TAKEN FROM THE MOST RECENT STAMP, not pinned at first sight. A loop whose
        # interval is env-tunable would otherwise be graded forever against whatever it happened to
        # hold the first time it ran. [[label-outlived-referent]]
        row["everyS"] = every


def _row(lane, row, now):
    age = None if row.get("mono") is None else max(0.0, now - row["mono"])
    every = row.get("everyS")
    out = {"lane": lane, "ticks": int(row.get("n") or 0), "everyS": every,
           "tickAgeS": (None if age is None else round(age, 1)),
           # ⚠ REG-547 SHAPE LAW — `bound` is present on every path, so "no bound" and "never
           # computed" cannot render identically.
           "boundS": (None if every is None else round(every * STALE_SLACK, 1))}
    if age is None:
        out["state"] = UNKNOWN
        out["why"] = ("this lane has never stamped a tick. That is not the same as dead - it may "
                      "be switched off, or the console may never have started it. Nobody looked.")
        return out
    if every is None:
        out["state"] = UNTIMED
        out["why"] = ("it last ran %.0fs ago, and it declares no fixed period (its sleep is "
                      "computed), so whether that is late cannot be decided from here" % age)
        return out
    if age > every * STALE_SLACK:
        out["state"] = LATE
        out["why"] = ("it last ran %.0fs ago against its own %.0fs period - %d missed cycles. A "
                      "lane with nothing to do still ticks, so this is silence from the THREAD, "
                      "not from the work." % (age, every, int(age // every)))
        return out
    out["state"] = FLOWING
    out["why"] = "it ran %.0fs ago, within its own %.0fs period" % (age, every)
    return out


def rows(now=None):
    """-> [row], one per lane that has ever been registered, newest-known first by lane name."""
    now = time.monotonic() if now is None else now
    with _LOCK:
        snapshot = dict((k, dict(v)) for k, v in _TICKS.items())
    return [_row(k, snapshot[k], now) for k in sorted(snapshot)]


def report(now=None):
    """-> {"rows": [...], "counts": {...}, "why": ...}

    ⚠ THE COUNTS NEVER COLLAPSE UNKNOWN INTO A VERDICT. A console where nothing has stamped yet
    reports 0 flowing and 0 late, which is not a clean bill and does not read as one.
    """
    rs = rows(now=now)
    counts = {"total": len(rs)}
    for st in (FLOWING, LATE, UNTIMED, UNKNOWN):
        counts[st.lower()] = len([r for r in rs if r["state"] == st])
    if not rs:
        why = ("no lane has stamped a tick, so nothing is known about any of them. This is what a "
               "console that has just started looks like, and also what a console whose loops "
               "never started looks like - the two are not distinguishable from here.")
    elif counts["late"]:
        why = ("%d lane(s) have missed more than %g of their own periods"
               % (counts["late"], STALE_SLACK))
    else:
        why = "%d lane(s) ticking within their own periods" % counts["flowing"]
    return {"rows": rs, "counts": counts, "why": why, "slack": STALE_SLACK}


def forget_all_for_tests():
    """Clear the table. Named so it can never be mistaken for something a lane should call."""
    with _LOCK:
        _TICKS.clear()


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    import json
    print(json.dumps(report(), indent=2))
