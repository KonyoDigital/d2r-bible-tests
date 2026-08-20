#!/usr/bin/env python3
"""v1823 — SWEEP THE WAITING CHRONICLE FOOTAGE WITHOUT THE CONSOLE.

Konyo: "why is nothing automatically sweeping? its been hours.... like why is a couple of
different AI readers not sweeping it one after another? and checking" — then, plainly:
"yes let me read and analyze automatically just obviously safegaurded... like no endless loops".

WHY NOTHING WAS SWEEPING, exactly. The auto-read watchdog is a `threading.Thread` started inside
control_app.py when the console app boots. Its logic was fine and its bounds were already real —
two tries per reel, refuses while a session is live or a sweep runs, marks each reel read-once,
retires with a named reason. It simply never ran, because the process that hosts it was closed.
chronicle_retro's own CLI says the rest out loud: "This sweep needs a reader." The readers live in
the console, so there was no way to tally without opening it.

This is that way. It reuses control_app's OWN wiring — chronicle_sweep_start / chronicle_sweep_state
and the same lanes the console uses — rather than re-deriving the sweep, because a second copy of
this pipeline is exactly how the two would drift apart and only one of them get fixed.

WHAT IT WILL NOT DO, since he asked for safeguarded and not clever:
  · It never spends without being told. With no --yes it prices the work and exits.
  · It processes AT MOST --max reels in one run (default 3) and then stops. There is no loop that
    re-arms itself; when the list is done the process exits.
  · Every wait is bounded by --timeout seconds per reel. A sweep that hangs ends the run with a
    named reason instead of parking forever.
  · It refuses outright while a capture session is live — a reel is only final once it stops
    growing — and while another sweep is already running.
  · It reads and proposes. It does NOT apply: grounding a name into his grail stays a decision he
    makes on the board, exactly as it is from the console.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _fmt(n):
    return "-" if n is None else str(n)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sweep unread Chronicle reels without the console.")
    ap.add_argument("--yes", action="store_true",
                    help="actually spend reads. Without it this prices the work and exits.")
    ap.add_argument("--max", type=int, default=3,
                    help="hard cap on reels swept in ONE run (default 3). There is no loop.")
    ap.add_argument("--timeout", type=int, default=5400,
                    help="seconds to wait for ONE reel (default 5400 = 90 min). Measured on his "
                         "own footage: a 39-frame reel is ~21 still-runs and both lanes read every "
                         "one, and a Grok page read is tens of seconds — the first attempt at this "
                         "used 900s and gave up on a sweep that was working fine.")
    ap.add_argument("--reel", default=None, help="sweep exactly this reel id and stop")
    args = ap.parse_args(argv)

    try:
        import control_app as ca
    except Exception as e:                                    # pragma: no cover - import guard
        print("cannot import control_app: %s" % e)
        return 2

    # ── refuse for the same reasons the watchdog refuses ────────────────────────────────
    if ca._agent_alive():
        print("refusing: a capture session is live — a reel is only final once it stops growing")
        return 1
    if (ca.chronicle_sweep_state() or {}).get("running"):
        print("refusing: a sweep is already running")
        return 1

    lanes = ca._chron_lanes()
    if "claude" not in lanes:
        print("refusing: the primary (Claude) lane is unavailable — nothing to sweep with")
        return 1

    waiting = [r for r in ca._unswept_chron_reels(limit=50)]
    if args.reel:
        waiting = [r for r in waiting if r.get("reel") == args.reel]
    if not waiting:
        print("nothing waiting: every reel with a chosen Chronicle focus has been swept")
        return 0

    print("lanes: %s" % ", ".join(lanes))
    print("waiting (newest first):")
    for r in waiting:
        print("   %-32s %-14s %s frames" % (r["reel"], r["label"], r["n"]))

    quote = ca.chronicle_scan_cost(limit=len(waiting)) or {}
    print("\nthe free pass says: %s page read(s) across %s reel(s), %s classify — %s"
          % (_fmt(quote.get("wouldReadPages")), _fmt((quote.get("totals") or {}).get("reels")),
             _fmt(quote.get("wouldClassify")), (quote.get("verdict") or {}).get("state")))

    if not args.yes:
        print("\nthis was a DRY RUN and spent nothing. To actually read them:")
        print("   python3 tv/chronicle_sweep_now.py --yes")
        return 0

    todo = waiting[:max(0, args.max)]
    print("\nsweeping %d reel(s), then stopping. No loop, no retry beyond the engine's own two."
          % len(todo))

    swept, failed = 0, 0
    for r in todo:
        rid = r["reel"]
        print("\n▶ %s (%s, %s frames)" % (rid, r["label"], r["n"]), flush=True)
        res = ca.chronicle_sweep_start(limit=1, reel_id=rid)
        if not (isinstance(res, dict) and res.get("ok")):
            print("   refused: %s" % ((isinstance(res, dict) and res.get("why")) or res))
            failed += 1
            continue
        deadline = time.time() + args.timeout
        started_at = time.time()
        last_note = 0.0
        gave_up = False
        while time.time() < deadline:
            st = ca.chronicle_sweep_state() or {}
            if not st.get("running"):
                break
            now = time.time()
            if now - last_note >= 60:
                last_note = now
                print("   … %d min in · phase %s · %s page(s) read"
                      % ((now - started_at) / 60, st.get("phase"), _fmt(st.get("pagesRead"))),
                      flush=True)
            time.sleep(3)
        else:
            gave_up = True
        if gave_up:
            # v1824.1 — GIVING UP ON THE WAIT DOES NOT STOP THE SWEEP, and the first run of this
            # tool proved how that cascades: the wait expired, the worker thread carried on holding
            # the job, and every remaining reel was then refused with "a sweep is already running".
            # Three reels, reads spent, nothing kept. There is no kill switch to call here — the
            # honest move is to STOP and say the work is still in flight, not to queue failures
            # behind a thread we cannot stop.
            print("   still running after %d min. STOPPING here rather than queueing refusals "
                  "behind it — the sweep is not cancelled, it is simply not finished." % (args.timeout / 60))
            print("   re-run this later; a reel is only marked swept once its result is on disk, "
                  "so nothing was burned.")
            failed += 1
            break
        st = ca.chronicle_sweep_state() or {}
        tot = ((st.get("result") or {}).get("totals")) or {}
        print("   read %s page(s) · %s unique name(s) · %s set name(s) · refused %s"
              % (_fmt(tot.get("pagesRead")), _fmt(tot.get("uniques")),
                 _fmt(tot.get("sets")), _fmt(tot.get("refused"))))
        if st.get("error"):
            print("   error: %s" % st["error"])
            failed += 1
        else:
            swept += 1

    print("\ndone: %d swept, %d failed. Nothing was applied — open the board to review the "
          "proposal and ground what you accept." % (swept, failed))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
