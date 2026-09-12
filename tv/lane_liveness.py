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
UNKNOWN = "UNKNOWN"      # never ticked, and NOBODY KNOWS WHY — the honest floor
DORMANT = "DORMANT"      # never ticked, and the reason is KNOWN and by design

_LOCK = threading.Lock()
_TICKS = {}
#: lanes that are deliberately not running, and the reason. A lane declares itself here rather
#: than leaving a reader to infer it.
_DORMANT = {}


def dormant(lane, why):
    """Declare that `lane` is deliberately not ticking, and say why. -> None

    ⚠⚠ WHY THIS IS NOT JUST A NICER WORD FOR UNKNOWN. Measured on his console 2026-09-08: three of
    the eight DARK supervisors reported `live: UNKNOWN, tickAgeS: None`, which reads as "nobody can
    tell whether this is alive". The truth was three DIFFERENT and entirely knowable facts:

        _mini_watchdog      EPISODIC — spawned per MINI session with (token, ends_ts); no session
                            has run since boot, so its absence is correct
        _orphan_watch       ANOTHER PROCESS — started inside the board window, so its stamps can
                            never reach this reader however healthy it is
        _orphan_exit_loop   DECLINED BY DESIGN — `if not ppid: return` before its first tick,
                            because his primary console has no TV_PARENT_PID and must never
                            self-exit

    Reported as one word, all three send a reader looking for a fault that is not there — and,
    worse, they make a REAL failure invisible: if `_orphan_exit_loop` ever declines on a scratch
    console that DOES have a parent, that is a genuine defect and it currently renders identically
    to the healthy case. Collapsing a known reason into UNKNOWN is the mirror of reporting an
    unmeasured thing as zero, and it costs the same way.

    This is the same split v2610 made one level up, where DARK stopped meaning both "nothing
    watches this worker" and "nothing watches the watchman".
    [[unknown-stays-unknown]] [[label-outlived-referent]]
    """
    lane = str(lane or "").strip()
    if not lane:
        raise ValueError("dormant() needs a lane name")
    why = str(why or "").strip()
    if not why:
        # a reason-less dormancy IS an unknown, and must not be dressed as a decision
        raise ValueError("dormant(%r) needs a REASON — without one this is UNKNOWN wearing a "
                         "calmer word, which is the defect it exists to fix" % lane)
    with _LOCK:
        _DORMANT[lane] = why


def waking(lane):
    """A lane that was dormant has started. Called by whatever spawns it."""
    with _LOCK:
        _DORMANT.pop(str(lane or "").strip(), None)


def tick(lane, every_s=None, dead_after_s=None):
    """Record that `lane` just ran a cycle. Called from inside the loop, once per turn.

    `every_s` is the loop's OWN sleep interval, passed from the loop that owns it rather than
    inferred here — see the module docstring for why a single global threshold is wrong by three
    orders of magnitude. Pass None when the interval is computed at runtime; that is UNTIMED, and
    it is an honest answer.

    ⚠⚠ v2994 — `dead_after_s` EXISTS BECAUSE ONE FIELD WAS CARRYING TWO QUESTIONS, and a lane that
    could not answer the first lost the second as the price. `every_s` answers *how often does this
    run* — it is what prints "against its own 30s period - 2 missed cycles". LATE actually needs a
    different question: *how long may this be silent before the THREAD is dead*. For a fixed-sleep
    lane the two coincide and `every_s * STALE_SLACK` serves both. For a computed-sleep lane they
    come apart, and there was no way to say "no fixed period, but certainly dead after 60s" — so
    the three loops that sleep on a branch were handed `every_s=None` and became permanently
    UNTIMED, which is honest about the period and silently gives up the red path.

    Measured on his console 2026-09-12, over a 90s window: `_bridge_prober` ticks every 1.2s,
    `_engine_driver` every 2.0s, `_kai_closer_loop` every 30.0s — and all three reported UNTIMED,
    so no silence, of any length, could ever turn them red. 3 of 20 lanes, each one alive and each
    one unfalsifiable.

    ⚠ DO NOT "FIX" THIS BY PADDING `every_s` INSTEAD. A ceiling passed as a period makes the report
    print a period the lane does not have — `_bridge_prober` would read "its own 30s period" about a
    loop that sleeps 1.2s. That is [[label-outlived-referent]] with the number still technically
    correct, which is the version of it that survives review.
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
    try:
        dead = float(dead_after_s) if dead_after_s is not None else None
    except (TypeError, ValueError):
        dead = None
    if dead is not None and dead <= 0:
        dead = None
    with _LOCK:
        row = _TICKS.get(lane)
        if row is None:
            row = {"mono": None, "everyS": every, "deadAfterS": dead, "n": 0}
            _TICKS[lane] = row
        row["mono"] = time.monotonic()
        row["n"] += 1
        # ⚠ THE PERIOD IS TAKEN FROM THE MOST RECENT STAMP, not pinned at first sight. A loop whose
        # interval is env-tunable would otherwise be graded forever against whatever it happened to
        # hold the first time it ran. [[label-outlived-referent]]
        row["everyS"] = every
        # ⚠ SAME REASON AS THE LINE ABOVE — taken from the most recent stamp, so a bound that is
        # widened or tightened in code is not graded against whatever it held at first sight.
        row["deadAfterS"] = dead


def _row(lane, row, now):
    age = None if row.get("mono") is None else max(0.0, now - row["mono"])
    every = row.get("everyS")
    dead = row.get("deadAfterS")
    # v2994 — the silence bound, and which of the two questions produced it. A period implies a
    # bound (period x slack); a declared bound stands on its own and implies NO period.
    # ⚠⚠ v2998 — WHEN A CALLER GAVE BOTH, THE BOUND WAS PUBLISHED AND THEN IGNORED. `everyS: 900,
    # deadAfterS: 120, boundS: 2700` — the field a reader takes for the operative threshold was not
    # one, which is this repo's own plumbing-with-no-tap wearing a number. The TIGHTER of the two
    # now governs: a period says "this is how often I run", a declared bound says "I am certainly
    # dead past here", and honouring the looser one would ignore whichever the author meant.
    # [[plumbing-with-no-tap]] [[label-outlived-referent]]
    _period_bound = (every * STALE_SLACK) if every is not None else None
    _lim = min([x for x in (_period_bound, dead) if x is not None] or [None]) \
        if (_period_bound is not None or dead is not None) else None
    _bound = None if _lim is None else round(_lim, 1)
    out = {"lane": lane, "ticks": int(row.get("n") or 0), "everyS": every,
           "deadAfterS": dead,
           "tickAgeS": (None if age is None else round(age, 1)),
           # ⚠ REG-547 SHAPE LAW — `bound` is present on every path, so "no bound" and "never
           # computed" cannot render identically.
           "boundS": _bound}
    if age is None:
        with _LOCK:
            _why = _DORMANT.get(lane)
        if _why:
            out["state"] = DORMANT
            out["why"] = ("it has never stamped a tick, and that is BY DESIGN: %s. A known reason "
                          "is not an unknown - and keeping them apart is what lets a lane that "
                          "declines when it should NOT be declining still be visible." % _why)
            return out
        out["state"] = UNKNOWN
        out["why"] = ("this lane has never stamped a tick. That is not the same as dead - it may "
                      "be switched off, or the console may never have started it. Nobody looked.")
        return out
    if every is None:
        # ⚠⚠ v2994 — A COMPUTED SLEEP IS NOT A REASON TO BE UNFALSIFIABLE. A lane may honestly have
        # no fixed period and STILL know a length of silence it can never legitimately reach. When
        # it declares one, staleness IS decidable and this stops being UNTIMED.
        if dead is not None:
            if age > dead:
                out["state"] = LATE
                out["why"] = ("it last ran %.0fs ago. It declares no fixed period - its sleep is "
                              "chosen per branch - but no path through it can be silent for %.0fs, "
                              "which is its own declared bound. That is silence from the THREAD, "
                              "not a slow turn." % (age, dead))
                return out
            out["state"] = FLOWING
            out["why"] = ("it ran %.0fs ago. It declares no fixed period (its sleep is computed), "
                          "so this is measured against the longest silence it says is possible, "
                          "%.0fs." % (age, dead))
            return out
        out["state"] = UNTIMED
        out["why"] = ("it last ran %.0fs ago, it declares no fixed period (its sleep is "
                      "computed) AND no bound on how long it may be silent, so whether that is "
                      "late cannot be decided from here" % age)
        return out
    if age > _lim:
        out["state"] = LATE
        _by = ("its own %.0fs period - %d missed cycles" % (every, int(age // every))
               if _lim == _period_bound else
               "its declared %.0fs maximum silence, which is tighter than its %.0fs period"
               % (dead, every))
        out["why"] = ("it last ran %.0fs ago against %s. A lane with nothing to do still ticks, so "
                      "this is silence from the THREAD, not from the work." % (age, _by))
        return out
    out["state"] = FLOWING
    out["why"] = ("it ran %.0fs ago, within its own %.0fs period%s"
                  % (age, every,
                     "" if dead is None else
                     " and within its declared %.0fs maximum silence" % dead))
    return out


def rows(now=None):
    """-> [row], one per lane that has ever been registered, newest-known first by lane name."""
    now = time.monotonic() if now is None else now
    with _LOCK:
        snapshot = dict((k, dict(v)) for k, v in _TICKS.items())
        # ⚠ A DECLARED-DORMANT LANE MUST HAVE A ROW, or `dormant()` is plumbing with no tap: the
        # declaration would be recorded and no reader could ever see it, which is this repo's most
        # repeated defect and the reason a lane that declines when it SHOULD be running would stay
        # invisible. A dormant lane has never ticked, so it has no entry in _TICKS and would
        # otherwise vanish from every report. [[the-unjoined-end]] [[plumbing-with-no-tap]]
        for _lane in _DORMANT:
            snapshot.setdefault(_lane, {"ticks": 0, "everyS": None, "last": None})
    return [_row(k, snapshot[k], now) for k in sorted(snapshot)]


def report(now=None):
    """-> {"rows": [...], "counts": {...}, "why": ...}

    ⚠ THE COUNTS NEVER COLLAPSE UNKNOWN INTO A VERDICT. A console where nothing has stamped yet
    reports 0 flowing and 0 late, which is not a clean bill and does not read as one.
    """
    rs = rows(now=now)
    counts = {"total": len(rs)}
    for st in (FLOWING, LATE, UNTIMED, DORMANT, UNKNOWN):
        counts[st.lower()] = len([r for r in rs if r["state"] == st])
    if not rs:
        why = ("no lane has stamped a tick, so nothing is known about any of them. This is what a "
               "console that has just started looks like, and also what a console whose loops "
               "never started looks like - the two are not distinguishable from here.")
    elif counts["late"]:
        why = ("%d lane(s) are silent past their own bound (a period x%g, or a declared "
               "maximum silence for the lanes whose sleep is computed)"
               % (counts["late"], STALE_SLACK))
    else:
        # ⚠ v2998 — THIS STILL SAID "their own periods" AFTER v2994 MADE FLOWING REACHABLE
        # WITHOUT ONE. The LATE string in the same commit was corrected and this one was not, so a
        # clean bill claimed twenty lanes were inside periods when three of them have everyS: null
        # and were graded against a declared silence bound instead. The number was right and the
        # word was not — which is precisely what the v2994 docstring warns against two files away.
        # [[label-outlived-referent]]
        _bounded = len([r for r in rs if r["state"] == FLOWING and r.get("everyS") is None])
        why = ("%d lane(s) ticking inside their own bound%s"
               % (counts["flowing"],
                  "" if not _bounded else
                  " (%d of them against a declared maximum silence, having no fixed period)"
                  % _bounded))
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
