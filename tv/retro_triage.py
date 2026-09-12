"""Dispose of what carries nothing, route what carries something. FREE of AI cost, deletes NOTHING.

Konyo, 2026-09-01: *"the filter and templates built should be disposing the 70% unrelevant reels
and frames from those same sessions and whats left is like 10-15% real images that need to be
routed and funneled to the unfied systmes"*.

WHY IT UNBLOCKS EVERYTHING. The chain is: a reel must be READ before it can be sealed, and sealed
before it can be pruned. **401 of his 411 reels have never been read**, so 6.8 GB is stuck and the
`vault-owes` retention rule never even fires - it is unreachable behind "never chronicle-swept".
Paying an AI to read 14,024 frames to find the few that show a panel is why the backlog never
moves. This gate answers "is a panel open" from PIXELS, with no AI call at all.

⚠ THE COST, MEASURED HONESTLY AND CORRECTED ONCE. A first pass reported 0.019 s/frame and "the
whole backlog in 265 seconds". That was TIMING CACHE HITS - `stash_screen_open_cached` is memoised
on (size, mtime) and the sampling runs kept re-reading the same frames. Measured cold, on frames
the cache had never seen:

    cold (real OCR) : 0.486 s/frame   <- SEE THE CONTRADICTION BELOW; do not plan on this

    ⚠ v2373 — TWO MEASUREMENTS OF THIS DISAGREE BY ~26x AND BOTH ARE RECORDED, because averaging
    them would erase the only useful part. The 0.486 above was itself a CORRECTION: an earlier
    "0.019 s/frame, whole backlog in 265 s" was retracted as having timed cache hits.

    Re-measured 2026-09-01, calling `stash_screen_open` — the UNCACHED function, cold by
    definition, so no memo can flatter it — on 120 frames drawn from 30 reels with a fixed seed:
        mean 0.019   median 0.014   p90 0.032   max 0.096  s/frame
    and the whole 11,146-frame backlog then took 332 s end to end, which is the same order.

    So the retraction may have been the error, not the original. What is NOT established is where
    0.486 came from; a plausible reading is that it averaged in one-off process/model warm-up over
    a short run, which a 120-frame sample amortises away. Until someone reproduces 0.486 with a
    stated method, PLAN ON ~0.02 s/frame and treat 0.486 as unexplained rather than authoritative.
    [[feedback-contradiction-is-the-finding]] [[unknown-stays-unknown]] [[stale-reading]]
    cached          : 0.408 s/frame
    14,024 frames   : ~114 MINUTES of local CPU

Still the right trade - two hours of free local CPU against paying to read 14,024 frames - but it
is two hours, not four minutes, and on his Mac that is two hours of heat. So this runs THROTTLED
and yields: `budget_s` bounds a pass, and `nice_delay_s` puts the CPU back between frames when he
is playing. A sweep that makes his game stutter is a sweep he will switch off.

⚠ AND THE HIT RATE IS NOT ESTABLISHED. Two samples of his own backlog returned 2% and 20% panel
frames. It varies enormously by reel - a stash session is nearly all panel, a farming session is
none - so no single figure describes it, and any "~N frames deserve a read" claim from a sample is
guesswork. Only a FULL pass produces a disposal list, and only a full pass may size the work.
[[unknown-stays-unknown]]

⚠ IT DELETES NOTHING. The prune that ran automatically once already ate two reels (123 MB, 106
pages) that were test fixtures, and was disarmed for it. What comes out of here is a manifest a
person reads.
"""

import glob
import os
import time

# what a panel verdict may be. Anything truthy from the gate is a panel; these are the ones seen.
PANEL_KINDS = ("stash", "stash-runes", "stash-gems", "stash-materials", "runes", "gems",
               "materials", "inventory", "chronicle")


STORE = "retro_triage.json"


def _store_path(root=None):
    """Where the survey is remembered. Honours TV_HIST so a harness cannot write the live store.

    ⚠ THE LANE READS A REDIRECTED WORLD AND WROTE A REAL ONE. `control_app.HIST_DIR` honours
    TV_HIST, so under a test harness `survey()` walks FIXTURE reels — but this path did not, so
    those fixture verdicts landed in the real `tv/retro_triage.json`. A gate run would have
    taught the live store that his reels hold no panels, and `worth_reading` would then skip them
    for good. Standing the watcher down in a harness (v2369) closes the loop that mattered; this
    closes it for anything that calls survey() directly too.
    [[feedback-fixtures-never-touch-live-data]]
    """
    if root:
        return os.path.join(root, STORE)
    # ⚠⚠ v2937 — AND THIS ONE DID NOT EVEN REALPATH OR FENCE. It joined TV_HIST straight on, so
    # `TV_HIST="   "` produced the RELATIVE path `"   /retro_triage.json"`, resolved against
    # whatever CWD the process started in. Found by the class law driving every resolver rather
    # than by inspection — it is the SIXTH copy of this rule, after _fixture_root, the control_app
    # fallback, _journal_path, _sub_budget_path, end_routes, chronicle_routes and g5_grok_eyes.
    # Blank-after-strip is nobody asking; a relative value has no fixed meaning. [[copy-drift]]
    hist = (os.environ.get("TV_HIST") or "").strip()
    if hist and os.path.isabs(hist):
        return os.path.join(hist, STORE)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), STORE)


def load(root=None):
    """Everything the structural pass has ever learned. -> (dict, ok).

    `ok` False means the store could not be READ - which is not the same as "nothing has been
    surveyed", and the caller must not treat it as an empty result. [[unknown-stays-unknown]]
    """
    p = _store_path(root)
    if not os.path.isfile(p):
        return {}, True                       # genuinely nothing surveyed yet
    try:
        import json
        with open(p, encoding="utf-8") as fh:
            blob = json.load(fh)
        return (blob if isinstance(blob, dict) else {}), True
    except Exception:
        return {}, False


def remember(reel_dir, hits, frames, kinds=None, root=None, panel_frames=None):
    """Record one reel's structural verdict, so the expensive pass is paid for ONCE.

    THIS IS WHAT MAKES THE FILTER USABLE. A panel-density ordering is the right idea and was left
    unwired for a good reason: `panel_density` samples up to 24 frames per reel at ~0.5-1.3 s
    each, so gating the sweep's estimate on it would cost HOURS every time anyone asked for a
    quote. Surveying once and remembering turns that into a dictionary lookup.
    """
    import json
    p = _store_path(root)
    blob, ok = load(root)
    if not ok:
        return False                          # never overwrite a store we could not read
    row = {
        "panels": int(hits), "frames": int(frames),
        "kinds": dict(kinds or {}), "ts": int(time.time() * 1000),
        "full": True,
    }
    # ⚠⚠ WHICH CLASSIFIER SAID SO. Without this a `panels: 0` verdict — "nothing to extract here"
    # — is UN-INVALIDATABLE: improve the structural gate tomorrow and nothing distinguishes a
    # verdict from the old one, so the reels it wrote off stay written off for ever. The two PAID
    # readers have carried `PROMPT_VER` / `VAULT_PROMPT_VER` for exactly this reason; the FREE gate
    # that decides whether a reel is READ AT ALL had no version anywhere.
    # MEASURED 2026-09-05: all 437 existing rows carry panels/frames/kinds/ts/full and nothing else.
    # ⚠ IT IS ADDITIVE AND NOTHING IS BACK-FILLED. A row without this key is UNKNOWN-classifier and
    # must never be read as agreeing with today's gate — stamping the past would invent a
    # provenance nobody can attribute. [[unknown-stays-unknown]] [[label-outlived-referent]]
    try:
        import control_app as _ca
        row["gateVer"] = _ca.GATE_CLASSIFIER_VER
    except Exception:
        pass          # the stamp is missing, which reads as UNKNOWN — never as "current"
    # ⚠ v2393 — THE PER-FRAME VERDICT, WHICH IS WHAT EVERY DOWNSTREAM STAGE ACTUALLY NEEDS.
    # Konyo: "we said after it earns a cross reference it gets deleted — we are speaking only of
    # the frames that get pruned with tooltips or slot identity, but either way those get tallied
    # and data should get extracted."
    #
    # Until now this function was handed COUNTS. `panels: 18, frames: 2385` cannot answer "may
    # THIS frame go", so the prune stayed at REEL granularity and 3.2 GB sat held because 104 of
    # 2,619 frames might matter. Four separate blockages, one missing record:
    #     gate   couldn't earn a cross-surface witness  — 8,300 sightings, 0 locations
    #     prune  couldn't keep 104 and release 2,515    — no per-frame verdict stored
    #     inbox  couldn't auto-tally                    — needs that witness
    #     disk   couldn't free anything                 — 0 of 6,380 frames releasable
    # The survey loop already HELD this, in `out["keep"]` beside the surface name, and dropped it
    # on the way here. [[heart-first]] rule 6 — persist what you knew, not a summary of it.
    #
    # ⚠ ONLY THE CARRYING FRAMES ARE NAMED, and that is not a shortcut: with `full: True` the
    # complement IS the disposable set, and his measured ratio is 1,019 carriers in 15,956 frames,
    # so naming the carriers is ~6% of the bytes of naming everything.
    #
    # ⚠ AND A MISSING KEY IS UNKNOWN, NOT EMPTY. A reel surveyed before today has no `panelFrames`
    # at all; `{}` means a full pass looked and found none. Collapsing those would let the prune
    # delete frames nobody ever examined. [[unknown-stays-unknown]]
    if panel_frames is not None:
        row["panelFrames"] = {str(k): str(v) for k, v in dict(panel_frames).items()}
    # ⚠⚠ v2968 (#69) — WHAT PRODUCED THIS ROW, not just which classifier version said so.
    # `gateVer` above answers "which gate", and that is a different question from "who wrote this".
    # MEASURED 2026-09-11 by verdict_provenance: 44 stores, ANSWERS 6, PARTIAL 4, SILENT 16, and
    # retro_triage.json was SILENT over 437 rows while being the store that decides EMPTY on the
    # river. A verdict with no producer cannot be INVALIDATED: improve the classifier tomorrow and
    # nothing can name the rows that predate the improvement, so a stale NO survives every future
    # pass looking exactly like a fresh one — and on this river a stale NO means footage is never
    # read again.
    # ⚠ ADDITIVE, AND NOTHING IS BACK-FILLED. Only rows written from here carry it; the 437 that
    # predate it stay UNKNOWN, because stamping the past would invent a provenance nobody can
    # attribute. That is verdict_provenance's own standing ruling and it is not relaxed here.
    # ⚠ SWALLOWED. A store that cannot be stamped must still be written — the verdict is the
    # expensive thing; the stamp is the label on it. [[unknown-stays-unknown]] [[the-unjoined-end]]
    try:
        import provenance as _PV
        row = _PV.stamp_row(row, by="retro_triage")
    except Exception:
        pass
    blob[os.path.basename(reel_dir)] = row
    try:
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(blob, fh)
        os.replace(tmp, p)                    # atomic: a half-written store is a lost survey
        return True
    except Exception:
        return False


def worth_reading(reel_dir, root=None):
    """Does this reel hold anything a paid reader should see? -> True | False | None.

    None means NOT SURVEYED - never False. A reel nobody has looked at must not be skipped as if
    it had been looked at and found empty; that is how footage gets abandoned.
    """
    blob, ok = load(root)
    if not ok:
        return None
    row = blob.get(os.path.basename(reel_dir))
    if not row or not row.get("full"):
        return None
    return bool(row.get("panels"))


def owed(hist=None):
    """Reels whose frames this lane has never walked IN FULL. -> dict

    ⚠⚠ v3018 — THE LANE THAT COULD NOT BE CAUGHT IDLE. tvd-retro-triage had liveness (a heartbeat
    says the thread is alive) and no WORK-LEVEL supervision, so "running and doing nothing" was
    invisible — the exact shape vaultAutoread died in, where a lane beat happily for 5.7 days
    without sweeping a single reel. A heartbeat answers "is the thread alive"; this answers "is
    there work it is not doing", and only the second one notices a lane that has quietly stopped
    mattering. [[the-unjoined-end]] [[plumbing-with-no-tap]]

    ⚠ UNKNOWN IS NOT ZERO, and here the distinction is the whole point: a missing reel directory
    or an unreadable store returns owed None with a why, never 0. A confident "nothing owed" from
    a lane that could not look is precisely the reading that lets a dead lane wear a clean bill.
    [[unknown-stays-unknown]] [[zero-needs-a-denominator]]

    ⚠ `full` IS THE BAR, NOT PRESENCE. A reel remembered from a PARTIAL walk still owes a full
    one — `remember()` records `full` per reel, and counting a partial record as done would make
    the lane look caught up on reels it only glanced at.
    """
    #: ⚠ the module defines no HERE — it resolves against __file__ each time (see _store_path),
    #: and TV_HIST is honoured so a harness can never be pointed at his live shelf.
    _here = os.path.dirname(os.path.abspath(__file__))
    h = hist or (os.environ.get("TV_HIST") or "").strip() or os.path.join(_here, "frames", "hist")
    out = {"ok": False, "owed": None, "walked": None, "partial": None, "onDisk": None,
           "reels": [], "why": ""}
    if not os.path.isdir(h):
        out["why"] = ("no reel directory at %s — UNKNOWN, which is not the same as nothing owed"
                      % os.path.basename(h.rstrip("/") or h))
        return out
    try:
        store, store_ok = load()
    except Exception as e:
        out["why"] = ("the survey store could not be read (%s) — UNKNOWN" % type(e).__name__)
        return out
    if not store_ok:
        out["why"] = "the survey store did not read back cleanly — UNKNOWN, never zero"
        return out
    dirs = [d for d in sorted(glob.glob(os.path.join(h, "reel_*"))) if os.path.isdir(d)]
    walked, partial, owing = 0, 0, []
    for d in dirs:
        rec = store.get(os.path.basename(d))
        if isinstance(rec, dict) and rec.get("full"):
            walked += 1
        else:
            if isinstance(rec, dict):
                partial += 1
            owing.append(os.path.basename(d))
    out.update({"ok": True, "owed": len(owing), "walked": walked, "partial": partial,
                "onDisk": len(dirs), "reels": owing[:50]})
    out["why"] = ("%d of %d reel(s) on the shelf carry no FULL survey record%s"
                  % (len(owing), len(dirs),
                     ("; %d of those were walked only in part" % partial) if partial else ""))
    return out


def unread_reels(hist_dir, sealed):
    """Reels the chronicle/vault lanes have never sealed. -> [dir, ...] oldest first."""
    out = []
    for d in sorted(glob.glob(os.path.join(hist_dir, "reel_*"))):
        if not os.path.isdir(d):
            continue
        sess = os.path.basename(d)
        sess = sess[len("reel_"):] if sess.startswith("reel_") else sess
        if sess not in (sealed or {}):
            out.append(d)
    return out


def survey(reels, gate, every_frame=True, per_reel_sample=10, budget_s=None,
           on_reel=None, nice_delay_s=0.0, remember_to=None):
    """Classify frames structurally. -> dict. READS NOTHING PAID AND DELETES NOTHING.

    `gate(path)` is control_app.stash_screen_open_cached - a crop plus an OCR of the panel chrome,
    returning a tab name or None.

    `every_frame=False` samples, and the result then carries `sampled: True` so no caller can
    mistake an estimate for a decision. A disposal list is only ever produced from a full pass.
    """
    # ⚠ `remember_to` IS A ROOT PATH, NOT A CALLBACK — its name reads like one, and passing
    # `remember_to=remember` (the obvious guess) sent a FUNCTION into os.path.join and lost a
    # 248-second pass. False disables remembering; None means the default store; a string is a
    # root. Anything else is a caller bug and is refused here rather than swallowed above.
    if not (remember_to is None or remember_to is False or isinstance(remember_to, str)):
        raise TypeError("remember_to is a ROOT PATH (str), False to disable, or None for the "
                        "default store - not %r. It is not a callback." % type(remember_to).__name__)
    t0 = time.time()
    out = {"reels": 0, "frames": 0, "panels": 0, "byKind": {}, "keep": [], "dispose": [],
           "perReel": {}, "sampled": (not every_frame), "errors": 0, "stoppedEarly": False}
    for d in (reels or []):
        if budget_s and (time.time() - t0) > budget_s:
            out["stoppedEarly"] = True
            break
        fs = sorted(glob.glob(os.path.join(d, "*.jpg")))
        if not fs:
            continue
        if not every_frame and len(fs) > per_reel_sample:
            step = max(1, len(fs) // per_reel_sample)
            fs = fs[::step][:per_reel_sample]
        out["reels"] += 1
        hits = 0
        # v2385 — PER-REEL kinds. `out["byKind"]` has always carried the real tab names, but only
        # across the WHOLE pass; what got written per reel was rebuilt below with the literal
        # string "panel". So the store knew 1,019 frames held a panel and could not say which
        # panel, on any of them. [[unknown-stays-unknown]]
        reel_kinds = {}
        reel_panel_frames = {}          # v2393 — basename -> surface, for the frames that CARRY
        for f in fs:
            out["frames"] += 1
            try:
                v = gate(f)
            except Exception:
                out["errors"] += 1
                v = None
            if nice_delay_s:
                # give the CPU back between frames. At the MEASURED ~0.02 s/frame (see the module
                # docstring; 0.486 is unexplained) a full pass is MINUTES, not hours — but the
                # yield stays, because the point is politeness on a machine he plays on, not speed.
                # OCR; unthrottled that is two hours of heat on the machine he plays on.
                time.sleep(nice_delay_s)
            if v:
                k = str(v)
                out["panels"] += 1
                out["byKind"][k] = out["byKind"].get(k, 0) + 1
                reel_kinds[k] = reel_kinds.get(k, 0) + 1
                reel_panel_frames[os.path.basename(f)] = k
                out["keep"].append(f)
                hits += 1
            elif every_frame:
                # only a FULL pass may call a frame disposable; a sample has not looked at enough
                out["dispose"].append(f)
        out["perReel"][os.path.basename(d)] = hits
        # ⚠ ONLY A FULL PASS MAY BE REMEMBERED. A strided sample cannot prove a reel holds no
        # panel, so recording its verdict would let a later lookup skip a reel nobody actually
        # looked at - the exact way footage gets abandoned. [[unknown-stays-unknown]]
        if every_frame and remember_to is not False:
            try:
                # ⚠ v2385 — THIS USED TO WALK out["keep"] AND WRITE {"panel": N}. `gate()` returns
                # a TAB NAME (see this function's own docstring) and the loop above already has
                # it in `k` — it was counted into out["byKind"] and then discarded on the way to
                # the store. MEASURED across his 439 recorded reels before the fix: the aggregate
                # of every `kinds` dict was exactly {'panel': 1019}. One key, 15,956 frames, and
                # the surface thrown away on every one.
                #
                # It is not only the board that wants this. v2380's `cross-surface` witness — the
                # same item on the floor, in the inventory and in the Chronicle list counting as
                # two independent looks — needs a per-sighting surface, and control_app currently
                # re-derives it live from the reel timeline while this pass walks straight past
                # the same fact. [[the-unjoined-end]]
                #
                # ⚠ OLD ROWS ARE NOT BACKFILLED. A reel surveyed before today has an UNKNOWN
                # breakdown, not an empty one, and inventing {"stash": N} for it would be a
                # measurement nobody made.
                remember(d, hits, len(fs), reel_kinds, root=(remember_to or None),
                         panel_frames=reel_panel_frames)
            except Exception as _e:
                # ⚠ v2371 — SAY IT. This was `except: pass`, and a survey is the most expensive
                # thing in this module: 6 of his largest reels cost 248 s of local OCR (4,634
                # frames) and the result was thrown away in silence because the CALLER passed the
                # wrong kind of `remember_to`. Nothing was written, nothing was said, and the
                # reels stayed exactly as unsurveyed as before. A failure to persist expensive
                # work must never look like work that was never done.
                # [[feedback-silence-is-not-evidence]] [[unknown-stays-unknown]]
                out["errors"] += 1
                out.setdefault("notRemembered", []).append(os.path.basename(d))
                print("\u26a0 retro_triage: surveyed %s but could NOT remember it (%s) - that "
                      "reel is still UNSURVEYED and the pass will be paid again"
                      % (os.path.basename(d), str(_e)[:80]), flush=True)
        if on_reel:
            try:
                on_reel(d, hits, len(fs))
            except Exception:
                pass
    out["seconds"] = round(time.time() - t0, 1)
    out["perFrameS"] = round(out["seconds"] / max(1, out["frames"]), 4)
    if out["sampled"]:
        out["say"] = ("SAMPLED %d frame(s) across %d reel(s) in %.0fs - an ESTIMATE only. A "
                      "strided sample cannot prove a reel holds no panel, so nothing here may be "
                      "disposed of." % (out["frames"], out["reels"], out["seconds"]))
    else:
        mb = 0
        for f in out["dispose"]:
            try:
                mb += os.path.getsize(f)
            except OSError:
                pass
        out["disposeMb"] = round(mb / 1e6, 1)
        out["say"] = ("read %d frame(s) across %d reel(s) in %.0fs, free. %d show a panel and are "
                      "worth a paid read; %d (%.1f MB) show none."
                      % (out["frames"], out["reels"], out["seconds"], out["panels"],
                         len(out["dispose"]), out["disposeMb"]))
    return out


def order_by_known_worth(dirs, root=None, fallback=None):
    """Put reels a FULL structural pass found panels in first. -> [dir, ...]

    This is the free half of the panel-density idea. `vault_retro.order_reels(dirs, panel_gate)`
    already sorts by measured density and is CORRECT, but it measures on the spot: up to 24 gate
    calls per reel at ~0.5-1.3 s each, which over 400 reels is hours every time anyone asks for a
    quote. That is why its call site passes no gate and the ordering has been running blind.

    Surveying once and remembering turns the same question into a dictionary lookup.

    THREE GROUPS, in this order, and the middle one is the point:
      1. surveyed and HAS panels      - read these first, they are where the names are
      2. NOT SURVEYED YET             - unknown, and unknown outranks known-empty
      3. surveyed and has NO panels   - looked at, nothing there
    A reel nobody has surveyed must never sort behind one that was surveyed and found empty;
    that would let an unlooked-at reel sink to the bottom forever. [[unknown-stays-unknown]]
    """
    blob, ok = load(root)
    if not ok:
        return list(fallback(dirs) if fallback else dirs)      # store unreadable: change nothing
    def rank(d):
        row = blob.get(os.path.basename(d))
        if not row or not row.get("full"):
            return 1                                            # unknown
        return 0 if row.get("panels") else 2
    base = list(fallback(dirs) if fallback else dirs)
    return sorted(base, key=rank)                               # stable: ties keep caller order


def manifest(survey_out):
    """What the paid reader should be pointed at, and nothing else. -> {reel: [frames]}"""
    by = {}
    for f in (survey_out or {}).get("keep") or []:
        by.setdefault(os.path.basename(os.path.dirname(f)), []).append(os.path.basename(f))
    return by


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import control_app as ca
    import frame_authority as fa
    sealed, _ok = fa.sealed_sessions()
    reels = unread_reels(ca.HIST_DIR, sealed)
    full = "--full" in sys.argv
    n = 0
    for a in sys.argv[1:]:
        if a.isdigit():
            n = int(a)
    if n:
        reels = reels[:n]
    print("unread reels: %d%s" % (len(reels), "" if not n else " (limited to %d)" % n))
    r = survey(reels, ca.stash_screen_open_cached, every_frame=full, budget_s=600)
    print(r["say"])
    if r["byKind"]:
        print("  panels by kind: %s" % r["byKind"])
    if r.get("stoppedEarly"):
        print("  ⚠ stopped on the time budget - the numbers above are PARTIAL")
    if full:
        m = manifest(r)
        print("  reels with something worth reading: %d of %d" % (len(m), r["reels"]))
