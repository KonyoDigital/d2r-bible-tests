#!/usr/bin/env python3
"""AN UNSEALED SESSION'S FOOTAGE IS NOT LOST — IT IS JUST NOT IN A REEL YET.

Reel directories exist because of a REEL FOLD that runs at SEAL time (tv_diablo.py, v883): it moves
loose `f_<ms>.jpg` frames whose timestamps fall in the session window into `frames/hist/reel_<sid>/`
with os.replace. v883's own note says why — "loose f_*.jpg footage was a shared pool the reaper shed
FIRST, so every sealed run went hollow within hours."

Nobody handled the session that DIES BEFORE IT SEALS. Its frames stay loose forever, and loose
frames are invisible to every lane and every deleter BY CONSTRUCTION: the vault and chronicle sweeps
iterate `reel_*`, frame_authority.plan_frames globs `hist/reel_*`, and space_warden has `tv/frames`
on its NEVER list. Not protected — UNSEEN, which reads as protected and is worse.

MEASURED on his tree 2026-08-24: 2,385 loose recording frames, 3.15 GB, spanning 01:15:00 to
02:06:22 — a fifty-one minute recording no lane could see.

⚠ THE ONE WAY THIS COULD DO REAL HARM, and it is why the overlap rule below exists.
`reel_index.ensure_reel_index` writes an index via `chronicle_retro.reconstruct_index`, which sets
`sessionId` from the DIRECTORY NAME with `reel_` stripped. PROVEN, not assumed:

    reel_orphan_1787523300658_1  ->  sessionId 'orphan_1787523300658_1'
    reel_s_1787523300658_1       ->  sessionId 's_1787523300658_1'

So folding leftovers of an ALREADY-SEALED session into a new directory mints a NEW SESSION ID for
pixels that came from one recording — which forges exactly the independence the keep gate exists to
demand (KEEP_MIN_WITNESSES counts distinct looks, and the throw bar counts distinct SESSIONS). A
later sweep would then ground rows, or suggest binning an item, on evidence that is one recording
wearing two names. Hence: **a cluster whose window overlaps ANY existing reel is REPORTED AND NEVER
MOVED.**

And the name is `reel_s_<t0>_<n>`, never `reel_orphan_…`, because v2065's recording parser is
`^s_(\\d{10,16})(?:_|$)` — an orphan-named reel would read as UNKNOWN time in the ledger and undo a
fix that shipped the same week.

This module DECIDES and MOVES. It never deletes a frame, never touches a file already inside a
`reel_*` directory, and refuses to act without an explicit --yes.
"""

import argparse
import glob
import json
import os
import time
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:                                   # the report prints a box-file glyph; a CLI that crashes
    from console_safe import enable    # while REPORTING makes a clean tree exit non-zero
    enable()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

# A NEW CLUSTER STARTS AFTER THIS MUCH SILENCE. It is vault_retro.REOPEN_GAP_MS — his number for
# "this is a new look" — rather than one invented here, and the data says the choice is not delicate:
# across his 2,384 loose-frame gaps the LARGEST is 7.4 s (p50 1.1 s, p99 4.7 s) against a
# FOOTAGE_INTERVAL_S of 1.0. Anything from ~30 s upward yields the same single cluster.
GAP_MS = 180_000

FRAME_RE = re.compile(r"^f_(\d{10,16})\.jpg$")


def _reel_windows(hist):
    """Every existing reel's real frame window, read from the filenames rather than its index —
    an index can be missing or stale, and the pixels cannot."""
    out = []
    for d in sorted(glob.glob(os.path.join(hist, "reel_*"))):
        if not os.path.isdir(d):
            continue
        ts = []
        try:
            for n in os.listdir(d):
                m = FRAME_RE.match(n)
                if m:
                    ts.append(int(m.group(1)))
        except OSError:
            continue
        if ts:
            out.append((os.path.basename(d), min(ts), max(ts)))
    return out


def plan(hist_dir=None, gap_ms=GAP_MS):
    """What WOULD be folded, and what is refused and why. Writes nothing, moves nothing."""
    hist = hist_dir or os.path.join(HERE, "frames", "hist")
    try:
        names = os.listdir(hist)
    except OSError as e:
        return {"ok": False, "why": "cannot read %s: %s" % (hist, e), "clusters": []}

    # ONE classifier, not two. frame_authority.loose_frames already splits recording frames from
    # probe artifacts and is guarded; a second copy of that rule is how the two drift. [[copy-drift]]
    arte = None
    try:
        import frame_authority as _fa
        lf = _fa.loose_frames(hist)
        if lf.get("ok"):
            arte = len(lf.get("artifact") or [])
    except Exception:
        arte = None

    ts = sorted(int(m.group(1)) for m in (FRAME_RE.match(n) for n in names) if m)
    windows = _reel_windows(hist)
    clusters = []
    if ts:
        start = prev = ts[0]
        run = [ts[0]]
        for t in ts[1:]:
            if t - prev > gap_ms:
                clusters.append((start, prev, run))
                start, run = t, []
            run.append(t)
            prev = t
        clusters.append((start, prev, run))

    # ── v2080 — A RECORDING IN PROGRESS *IS* A PILE OF LOOSE FRAMES ──────────────────────────
    # That is not a race, it is the steady state: while he films, every new frame lands directly in
    # hist/ as `f_<ms>.jpg` and only becomes a reel at SEAL. Which is exactly the population this
    # module folds. A fold running unattended would therefore move the frames of the session he is
    # filming RIGHT NOW into a reel and seal it as a finished recording — and v2080 put this behind
    # an automatic healer on a ten-minute timer, so it would have done it on its own.
    #
    # The cluster boundary cannot tell a finished recording from one still being written: both end
    # at "the newest frame I can see". So the rule is TIME, not shape — a window whose last frame is
    # newer than the same gap that defines a cluster boundary has not been shown to be over.
    # A frame that is still arriving is UNKNOWN, and unknown means leave it alone.
    # [[unknown-stays-unknown]] [[feedback-fixtures-never-touch-live-data]]
    now_ms = int(time.time() * 1000)
    out = []
    for lo, hi, run in clusters:
        # v2082 — AND A CALLER MAY NOT DISABLE THIS BY PASSING ZERO. `--gap-s 0` reaches gap_ms=0,
        # where `(now_ms - hi) < 0` is never true and the refusal vanishes entirely. Measured on six
        # frames of a recording in progress: at the default it refuses; at gap_ms=0 it minted SIX
        # separate session ids for that one recording and moved every frame — exactly the forgery
        # this module's docstring exists to prevent. The window a caller may tune is how far apart
        # two clusters must be; it is NOT how recent a recording may be before we call it finished.
        if (now_ms - hi) < max(gap_ms, GAP_MS):
            out.append({"t0": lo, "t1": hi, "frames": len(run), "bytes": 0,
                        "reel": "reel_s_%d_1" % lo, "overlaps": [], "eligible": False,
                        "why": "REFUSED \u2014 the newest frame here is %.0fs old, inside the %.0fs "
                               "gap that defines a cluster. This may be a recording STILL IN "
                               "PROGRESS, and a recording in progress is indistinguishable from "
                               "loose frames. Folding it would seal a session he is still filming."
                               % ((now_ms - hi) / 1000.0, gap_ms / 1000.0)})
            continue
        hit = [w[0] for w in windows if not (w[2] < lo or w[1] > hi)]
        size = 0
        for t in run:
            try:
                size += os.path.getsize(os.path.join(hist, "f_%d.jpg" % t))
            except OSError:
                pass
        out.append({
            "t0": lo, "t1": hi, "frames": len(run), "bytes": size,
            "reel": "reel_s_%d_1" % lo,
            "overlaps": hit,
            "eligible": not hit,
            "why": ("REFUSED — this window is already covered by %s. Folding it would mint a second "
                    "session id for one recording, which forges the independence the keep and throw "
                    "bars exist to demand." % ", ".join(hit)) if hit else
                   ("no reel covers this window — it is an unsealed recording and folding it makes "
                    "it readable by the lanes for the first time"),
        })
    return {"ok": True, "hist": hist, "clusters": out, "gapMs": gap_ms,
            "artifacts": arte,
            "say": (("%d cluster(s) of loose footage; %d foldable, %d refused for overlapping an "
                     "existing reel." % (len(out), sum(1 for c in out if c["eligible"]),
                                         sum(1 for c in out if not c["eligible"])))
                    if out else "no loose recording frames — every frame on disk belongs to a reel")
                   + ("" if arte is None else
                      " %d probe artifact(s) left alone; they are not a recording." % arte)}


def apply_plan(p, yes=False):
    """Fold the ELIGIBLE clusters. Refuses without an explicit yes — this moves his footage."""
    if not yes:
        return {"ok": False, "why": "refusing to move footage without --yes; run without --apply to "
                                    "read the plan"}
    hist = p["hist"]
    moved, made, failed = 0, [], []
    for c in p.get("clusters") or []:
        if not c.get("eligible"):
            continue                       # never fold a window a reel already covers
        dest = os.path.join(hist, c["reel"])
        try:
            os.makedirs(dest, exist_ok=True)
        except OSError as e:
            failed.append({"reel": c["reel"], "why": str(e)[:120]})
            continue
        n = 0
        for name in sorted(os.listdir(hist)):
            m = FRAME_RE.match(name)
            if not m:
                continue                   # artifacts and anything unparsable stay exactly where they are
            t = int(m.group(1))
            if not (c["t0"] <= t <= c["t1"]):
                continue
            try:
                os.replace(os.path.join(hist, name), os.path.join(dest, name))
                n += 1
            except OSError as e:
                failed.append({"frame": name, "why": str(e)[:120]})
        moved += n
        made.append({"reel": c["reel"], "frames": n})
        # the index IS the reel (v1608) — without it the lanes still cannot read what we just folded
        try:
            import reel_index
            reel_index.ensure_reel_index(dest)
        except Exception as e:
            failed.append({"reel": c["reel"], "why": "index not written: %s" % str(e)[:100]})
    return {"ok": not failed, "moved": moved, "reels": made, "failed": failed}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Make an unsealed session's footage visible again.")
    ap.add_argument("--hist", default=None)
    ap.add_argument("--gap-s", type=float, default=GAP_MS / 1000.0)
    ap.add_argument("--apply", action="store_true", help="actually fold (needs --yes)")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args(argv)
    p = plan(a.hist, int(a.gap_s * 1000))
    if not p["ok"]:
        print("refusing: %s" % p["why"])
        return 1
    import datetime
    fmt = lambda t: datetime.datetime.fromtimestamp(t / 1000).strftime("%Y-%m-%d %H:%M:%S")
    print("\U0001f9f5  ORPHAN FOLD — footage belonging to no reel")
    print("   %s" % p["say"])
    for c in p["clusters"]:
        print("   %s  %s -> %s  %4d frame(s)  %6.2f GB  -> %s"
              % ("FOLD  " if c["eligible"] else "REFUSE", fmt(c["t0"]), fmt(c["t1"]),
                 c["frames"], c["bytes"] / 1e9, c["reel"]))
        print("          %s" % c["why"])
    if a.apply:
        r = apply_plan(p, a.yes)
        print("\n%s" % (("folded %d frame(s) into %d reel(s)" % (r["moved"], len(r["reels"])))
                        if r["ok"] else (r.get("why") or "some moves failed")))
        for f in r.get("failed") or []:
            print("   FAILED %s" % f)
        return 0 if r["ok"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
