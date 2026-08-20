#!/usr/bin/env python3
"""v1823 — SWEEP THE WAITING CHRONICLE FOOTAGE WITHOUT THE CONSOLE.

Konyo: "why is nothing automatically sweeping? its been hours.... like why is a couple of
different AI readers not sweeping it one after another? and checking" — then, plainly:
"yes let me read and analyze automatically just obviously safegaurded... like no endless loops".

WHY NOTHING WAS SWEEPING, exactly. The auto-read watchdog is a `threading.Thread` started inside
control_app.py when the console app boots. Its logic was fine and its bounds were already real —
two tries per reel, skips the reel still recording, refuses while a sweep runs, marks each read-once,
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
  · It skips the ONE reel still receiving frames — a reel is only final once it stops growing —
    and refuses while another sweep is already running. It does NOT refuse merely because a
    capture session is live: v1823 established that a live session says nothing about the sealed
    reels behind it, and this file kept the old blanket refusal until v1832, so the console swept
    while he played and the command line sat idle.
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
    ap.add_argument("--again", default=None, metavar="REEL_ID",
                    help="forget that ONE reel was swept and read it again — for after a prompt "
                         "change. Targeted on purpose: chronicle_forget_swept() clears the memory "
                         "for EVERY reel, which on his hist is 18 of them.")
    args = ap.parse_args(argv)

    try:
        import control_app as ca
    except Exception as e:                                    # pragma: no cover - import guard
        print("cannot import control_app: %s" % e)
        return 2

    # ── refuse for the same reasons the watchdog refuses ────────────────────────────────
    # v1832 — AND THE WATCHDOG STOPPED REFUSING FOR THIS ONE. Konyo: "why refused when session is
    # LIVE? we had a AI reader for live too". v1823 removed the blanket live-session refusal from
    # the console path in as many words — "A live session says nothing about the SEALED reels
    # behind it, and refusing on it meant the sweeper never ran while he was at the machine" — and
    # skips the single reel still receiving frames instead. This file kept the old rule while
    # claiming in its own comment to mirror the watchdog, so the console would sweep while he
    # played and the command line would not. One rule, two copies, one of them updated.
    # [[copy-drift]]
    live = False
    try:
        live = bool(ca._agent_alive())
    except Exception:
        live = False
    if (ca.chronicle_sweep_state() or {}).get("running"):
        print("refusing: a sweep is already running")
        return 1

    lanes = ca._chron_lanes()
    if "claude" not in lanes:
        print("refusing: the primary (Claude) lane is unavailable — nothing to sweep with")
        return 1

    if args.again:
        # v1828 — RE-READ ONE REEL. Two separate records remember that a reel was swept:
        # chronicle_swept.json (the sweep's own skip list) and the "reels" array in
        # chron_autoread.json (the watchdog's). Clearing one and not the other leaves the reel
        # invisible to half the system — two memories for one fact, and only one of them fixed is
        # exactly how a reel comes back as "already done" after you thought you had freed it.
        rid = args.again
        freed = []
        try:
            swept = ca._chron_swept_load() or {}
            if rid in swept:
                swept.pop(rid, None)
                ca._chron_swept_save(swept)
                freed.append("chronicle_swept.json")
        except Exception as e:
            print("could not clear the sweep record: %s" % e)
            return 1
        try:
            seen = ca._chron_reels_seen()
            if rid in seen:
                seen.discard(rid)
                # persist through the app's own writer so the on-disk shape stays its shape
                payload_reels = sorted(seen)
                import json as _json
                with open(ca._CHRON_AUTOREAD_PATH, encoding="utf-8") as fh:
                    cur = _json.load(fh) or {}
                cur["reels"] = payload_reels
                tmp = ca._CHRON_AUTOREAD_PATH + ".tmp"
                with open(tmp, "w", encoding="utf-8") as fh:
                    _json.dump(cur, fh)
                os.replace(tmp, ca._CHRON_AUTOREAD_PATH)
                freed.append("chron_autoread.json")
        except Exception as e:
            print("could not clear the watchdog record: %s" % e)
            return 1
        if not freed:
            print("%s was not marked swept in either record — nothing to free" % rid)
        else:
            print("freed %s from: %s" % (rid, ", ".join(freed)))
        args.reel = rid

    waiting = [r for r in ca._unswept_chron_reels(limit=50)]
    if args.reel:
        waiting = [r for r in waiting if r.get("reel") == args.reel]

    # v1832 — the ONE reel a live session actually protects: the one still receiving frames. Named
    # out loud, because "skipped it" and "there was nothing to do" are different facts and only one
    # of them is worth waiting on.
    hist = os.environ.get("TV_HIST") or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                     "frames", "hist")
    growing = []
    for r in list(waiting):
        try:
            if ca._reel_is_growing(os.path.join(hist, str(r.get("reel")))):
                growing.append(r.get("reel"))
                waiting.remove(r)
        except Exception:
            pass
    if growing:
        print("still recording, left alone: %s" % ", ".join(str(g) for g in growing))
    elif live:
        print("a capture session is live — sweeping the SEALED reels behind it anyway (v1823)")

    # v1834 — NAMING A REEL IS A STATEMENT OF INTENT, and the focus filter must not overrule it.
    # _unswept_chron_reels() deliberately lists only reels that DECLARE a Chronicle focus, so an
    # automatic run never sweeps a stash mini or a gameplay session at full price. Correct for the
    # automatic case, and wrong the moment he names one: --reel and --again both FILTER that list,
    # so an undeclared reel came back "nothing waiting" no matter what you typed.
    #
    # That silently stranded v1830's whole point. The eight reels it reopened — 1,032 frames,
    # including the 483-frame browse whose pages print First Found stamps and his 64% meter — carry
    # no declared focus, because they were ordinary sessions rather than a focused 🏆/🧩 capture.
    # So the seals were voided and nothing could reach them: reopened in the skip set, invisible to
    # the selector. Two halves, each right, never joined. [[the-unjoined-end]]
    if args.reel and not waiting:
        d = os.path.join(hist, str(args.reel))
        if os.path.isdir(d):
            n = len([f for f in os.listdir(d) if f.startswith("f_") and f.endswith(".jpg")])
            if n:
                print("%s declares no Chronicle focus — sweeping it because you named it "
                      "(the classifier decides each run, at full price)" % args.reel)
                waiting = [{"reel": str(args.reel), "label": "no declared focus", "n": n}]
        if not waiting:
            print("no reel named %s in %s" % (args.reel, hist))
            return 1

    if not waiting:
        if growing:
            print("nothing to sweep: the only reel waiting is still being recorded")
            return 0
        print("nothing waiting: every reel with a chosen Chronicle focus has been swept")
        return 0

    print("lanes: %s" % ", ".join(lanes))
    print("waiting (newest first):")
    for r in waiting:
        print("   %-32s %-14s %s frames" % (r["reel"], r["label"], r["n"]))

    quote = ca.chronicle_scan_cost(limit=len(waiting), reel_id=(args.reel or None)) or {}
    # v1834 — COUNT THE REELS IT WOULD ACTUALLY READ. totals.reels counts every reel the walk
    # touched, INCLUDING the ones it skipped as already-swept, so a single targeted reel priced as
    # "440 page read(s) across 18 reel(s)" — the pages were right and the reels described a
    # different set entirely. Both halves of a price he acts on have to name the same thing.
    _priced = [r for r in (quote.get("reels") or []) if (r or {}).get("note") != "already-swept"]
    _nreels = len(_priced) if _priced else _fmt((quote.get("totals") or {}).get("reels"))
    print("\nthe free pass says: %s page read(s) across %s reel(s), %s classify — %s"
          % (_fmt(quote.get("wouldReadPages")), _nreels,
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
        # v1838 — `not-found` rides along as an instrument check. A grail page that yields names
        # and NO not-found rows means the reader saw the ticks and missed the list. It changes
        # nothing in the tally by design.
        print("   read %s page(s) · %s unique name(s) · %s set name(s) · refused %s · %s read as "
              "not-found (audit only)"
              % (_fmt(tot.get("pagesRead")), _fmt(tot.get("uniques")),
                 _fmt(tot.get("sets")), _fmt(tot.get("refused")), _fmt(tot.get("notFound"))))
        # v1843 — THE FOLD'S RECEIPT, WHICH NOTHING HAS EVER SHOWN HIM. control_app builds
        # `_fold_report` and publishes it as result["fold"] at three sites; grepping the tree finds
        # no reader — not the board, not the console, not this CLI. v1789 wrote it FOR this purpose,
        # in its own words: a name folded onto an item he already has, or retired as reader debris,
        # "must not simply vanish: 'we looked and it was not a grail item' and 'nobody looked' have
        # to read differently". They could not, because neither was printed anywhere.
        # It carries real information. On his 08-20 sweep: 49 corrections including Battlecage ->
        # Rattlecage, Naglring -> Nagelring and Twitchthrow -> Twitchthroe, and 25 names retired as
        # debris - every one verified as NOT an exact roster member, so nothing real was thrown
        # away. That is a fact worth being able to see. [[plumbing-with-no-tap]]
        _fold = (st.get("result") or {}).get("fold") or {}
        _fx, _rt = _fold.get("folded") or {}, _fold.get("retired") or []
        if _fx or _rt:
            _eg = ", ".join("%s -> %s" % (k, v) for k, v in list(_fx.items())[:3])
            print("   fold: %d name(s) corrected%s · %d retired as debris"
                  % (len(_fx), (" (%s)" % _eg) if _eg else "", len(_rt)))
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
