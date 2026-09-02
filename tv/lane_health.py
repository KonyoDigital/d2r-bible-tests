#!/usr/bin/env python3
"""LANE HEALTH — every extraction lane says when it last did work, and a stalled one says so ITSELF.

Konyo, 2026-08-29, after asking why nothing had been extracted "for days" and having to be told:
"eagle eye watchdog.. corroborator all need to be coded accordingly so its all working and
communicating.. we need this ready for traffic and optimized and self looped like the rest of the
system. intelligent architecture code"

⚠ THE FAILURE THIS EXISTS FOR, MEASURED THE DAY IT WAS WRITTEN:

    chronicle_swept.json    36 sessions   newest seal   49.2 h ago    working
    vault_swept.json         8 sessions   newest seal  136.7 h ago    STALLED 5.7 DAYS
    sessions the chronicle lane swept that the vault lane never sealed: 36

frame_authority reads the VAULT seal, so those 36 sessions' frames were all held as "not sealed"
and nothing was prunable. Nothing on the console said the vault lane had stopped. The auto-sweep
watchdog (_chron_autoread_watch, v2139) speaks only when its MESSAGE CHANGES — the right fix for a
loop that logged 1,700 lines a day, and the exact wrong shape for a lane that has been answering
the same thing for five days. Silence had become the report. [[feedback-silence-is-not-evidence]]

THREE THINGS, and they are deliberately separate:
  · FRESHNESS  — when did this lane last produce work, and is that longer than it should be
  · REACH      — how much of the corpus has it covered
  · DIVERGENCE — where two lanes disagree about the SAME session, which is the defect above and
                 which neither lane can see on its own. This is the corroborator's job.

⚠ IT DECIDES NOTHING AND WRITES NOTHING. Same shape as prune_shadow and slot_identity: it reads,
it explains, and an unreadable store makes it answer UNKNOWN rather than healthy. A watchdog that
cannot tell "quiet" from "dead" is the thing being replaced here.
"""
import io
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))

#: name -> (store file, human description, stall threshold in HOURS)
# ⚠ THE THRESHOLDS ARE A JUDGEMENT AND ARE LABELLED AS ONE. They are not tuned against anything;
# they are "longer than this and a person would want to know", which is the only honest basis until
# there is a distribution to fit. They are here, named, rather than buried as literals.
LANES = {
    "chronicle": ("chronicle_swept.json", "reads item NAMES off reels into his Chronicle", 48.0),
    "vault":     ("vault_swept.json",     "seals a reel as fully extracted — the ONLY seal the "
                                          "frame deleter reads", 48.0),
    # ⚠ v2304 — SHADOW-WATCH DELIBERATELY IS NOT A LANE HERE. I added it and it turned the whole
    # lanes check UNKNOWN ("a lane's store could not be read"), because everything in this dict is
    # a SWEEP LEDGER keyed by session id with a timestamp per row, and the watcher writes a single
    # flat record of its last look. Forcing a watcher into a ledger's schema broke the reading for
    # the two lanes that were fine. Its health lives in health_engine.check_shadow_watch and its
    # corroboration in corroborate.py, which is where two independent measurements belong.
}

#: lanes that should cover the same sessions. A session in the first and not the second is the
#: divergence that hid a five-day stall.
CORROBORATE = [("chronicle", "vault")]


def _sid(key):
    """ONE spelling for a session id. -> str

    ★ v2302 — THE TWO LANE STORES SPEAK DIFFERENT DIALECTS, AND THE CORROBORATOR NEVER KNEW.
    MEASURED on his tree 2026-08-30:

        chronicle_swept.json keys look like  'reel_s_1785711283831_49223'   (reel_ prefix)
        vault_swept.json     keys look like  's_1787244002054_15361'        (no prefix)

    divergence() computed set(a) - set(b) on those raw keys, so it compared the two lanes in two
    languages. It reported "36 session(s) the chronicle lane covered that vault never did"; the
    truth, normalised against the 28 reels actually on disk, is 20 — with 8 covered by BOTH and
    read as diverged purely because of the prefix.

    ⚠ AND IT COULD NEVER HAVE SAID "ALIGNED". Every chronicle key carries a prefix no vault key
    ever has, so the difference is non-empty BY CONSTRUCTION on any tree, forever. A corroborator
    that cannot report agreement has stopped carrying information — the same defect as a gate that
    is always green, wearing the other colour. Its own docstring says it exists because "no one
    asked them the same question"; it was asking in two dialects.

    Normalised HERE, at the single place both stores are read, and never at the call sites — the
    next store to arrive would otherwise recreate this. [[copy-drift]] [[the-unjoined-end]]
    """
    k = str(key)
    return k[5:] if k.startswith("reel_") else k


def _load(name):
    """-> (dict|None, why). None means UNREADABLE, which is never healthy.

    Keys come back NORMALISED through _sid, so every caller compares like with like."""
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return None, "%s does not exist" % name
    try:
        with io.open(p, encoding="utf-8") as fh:
            blob = json.load(fh)
    except Exception as e:
        return None, "%s could not be read: %s" % (name, e)
    if not isinstance(blob, dict):
        return None, "%s is not a mapping of sessions" % name
    # v2302 — one dialect from here down. Collisions cannot occur: two keys only normalise to the
    # same id if they name the same session, which is exactly what we want them to do.
    return {_sid(k): v for k, v in blob.items()}, ""


def _newest_ts(blob):
    """Newest seal timestamp in ms, or None if no row carries one."""
    best = None
    for v in (blob or {}).values():
        if not isinstance(v, dict):
            continue
        ts = v.get("ts")
        try:
            ts = float(ts)
        except (TypeError, ValueError):
            continue
        if ts and (best is None or ts > best):
            best = ts
    return best


def lane(name, now_ms=None, owed=None):
    """One lane's health. -> dict

    ★ v2301 — A LANE WITH NOTHING TO DO IS NOT A LANE THAT STOPPED, and this could not tell them
    apart. It measured ONE thing — how long since the lane last did work — against a stall
    threshold, so a lane that has swept everything and is correctly quiet reports the same
    "STOPPED" as one that is broken.

    MEASURED on his console 2026-08-30, two checks of the same doctor contradicting each other in
    the same breath:
        reel extract      ok       all 28 reel(s) have been read
        extraction lanes  missing  chronicle: last did work 63.5 h ago -- this lane has STOPPED
    Everything was read. There was no work. The lane was idle, and the panel called it stopped —
    which is the kind of red herring that sends him hunting a fault that does not exist, minutes
    before a recording session. [[feedback-contradiction-is-the-finding]]

    `owed` is how many units of work were actually WAITING. IDLE is claimed only on POSITIVE
    evidence that the answer is zero: owed=None means nobody counted, and an uncounted lane stays
    STALLED, because "nothing was owed" and "nobody looked" must never reach the same box.
    [[unknown-stays-unknown]]
    """
    if name not in LANES:
        return {"lane": name, "state": "unknown", "why": "no lane called %r" % name}
    store, what, stall_h = LANES[name]
    blob, why = _load(store)
    if blob is None:
        return {"lane": name, "state": "unknown", "sessions": None, "ageHours": None,
                "why": "%s — an unreadable store is UNKNOWN, never healthy" % why}
    now = float(now_ms if now_ms is not None else time.time() * 1000.0)
    ts = _newest_ts(blob)
    if ts is None:
        return {"lane": name, "state": "unknown", "sessions": len(blob), "ageHours": None,
                "why": ("%d session(s) sealed but not one row carries a timestamp, so HOW LONG AGO "
                        "is unanswerable" % len(blob))}
    age = (now - ts) / 3600000.0
    over = age > stall_h
    idle = bool(over and isinstance(owed, int) and owed == 0)
    stalled = bool(over and not idle)
    if idle:
        tail = (" — but %s owed a read, so this lane is IDLE, not stopped: it has swept everything "
                "there is" % ("nothing" if owed == 0 else "%d" % owed))
    elif stalled:
        tail = (" — past the %.0f h mark, so this lane has STOPPED and nothing else was going "
                "to say so%s" % (stall_h,
                                 "" if owed is not None else
                                 " (and nobody counted what was owed, so IDLE cannot be ruled in)"))
    else:
        tail = ""
    return {
        "lane": name, "state": ("idle" if idle else ("stalled" if stalled else "fresh")),
        "sessions": len(blob), "ageHours": round(age, 1), "stallAfterHours": stall_h,
        "what": what, "owed": owed,
        "why": "%s: %d session(s), last did work %.1f h ago%s" % (name, len(blob), age, tail),
    }


def _reels_on_disk():
    """Session ids that still have FOOTAGE. -> (set|None, why)

    None means the store could not be READ, which is UNKNOWN and must never be read as "no
    reels" — an empty set would silently turn every divergence into "aligned", i.e. a green
    corroborator produced by not looking. [[unknown-stays-unknown]]

    ⚠ Honours TV_HIST, because a fixture that repoints the ledgers and not the footage would
    compare his real reels against a test's sessions. Same resolution rule as
    reel_retention.plan, and a reel is a `reel_*` DIRECTORY there — the loose .jpg frames beside
    them are not reels. Keys come back through _sid so all three dialects compare like with like.
    """
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    try:
        return {_sid(d) for d in os.listdir(hist) if d.startswith("reel_")}, ""
    except OSError as e:
        return None, "cannot read %s: %s" % (hist, e)


def divergence(a, b):
    """Sessions lane A covered that lane B never did. -> dict

    Neither lane can see this on its own, which is exactly why it hid a five-day stall: the
    chronicle lane was correct that it had swept, and the vault lane was correct that it had not,
    and no one asked them the same question.
    """
    sa, wa = _load(LANES.get(a, ("", "", 0))[0])
    sb, wb = _load(LANES.get(b, ("", "", 0))[0])
    if sa is None or sb is None:
        return {"pair": [a, b], "state": "unknown",
                "why": "cannot compare: %s" % (wa or wb)}
    only = sorted(set(sa) - set(sb))

    # ★ v2437 — AND IT STILL COULD NEVER SAY "ALIGNED". v2302 fixed the DIALECT (see _sid) and
    # the identical always-red survived one level up, through a HISTORY-vs-DISK mismatch: this
    # differenced two LIFETIME ledgers with no reference to what footage still exists.
    # MEASURED on his tree 2026-09-02:
    #
    #     chronicle entries 401 · vault entries 30 · reels on disk 40 · diverged 371
    #     of those 371 — reel directory still EXISTS: 25 · NO footage at all: 346
    #
    # The vault lane can only sweep a DIRECTORY, so 346 of them can NEVER be sealed by any
    # amount of lane work — and the count GROWS every time footage is pruned. A corroborator
    # whose red gets worse the more correctly the system behaves has stopped carrying
    # information, which is this module's own stated failure mode wearing the other colour.
    #
    # ⚠ AND A SIBLING CHECK CALLS THE SAME FACT HEALTHY: "reel extract" reports
    # "all 40 reel(s) have been read · 361 more entries retained for footage since pruned
    # (the read is the record)". 401 = 40 on disk + 361 retained. One check counted history as
    # a fault while the other counted it as the record. [[feedback-contradiction-is-the-finding]]
    #
    # So the question becomes ACTIONABLE divergence: sessions one lane covered, the other did
    # not, AND whose footage is still there for the other lane to act on. History-only entries
    # are still reported — they are not deleted from the answer, only from the verdict.
    disk, disk_why = _reels_on_disk()
    if disk is None:
        # UNKNOWN is not "no reels". Without the footage we cannot tell actionable from
        # historic, so fall back to the raw difference and SAY that is what this is.
        actionable, historic = only, None
    else:
        actionable = [s for s in only if s in disk]
        historic = [s for s in only if s not in disk]

    tail = ""
    if historic:
        tail = (" (+%d older session(s) whose footage is already gone — no lane work can ever "
                "change those)" % len(historic))
    elif historic is None:
        tail = " (footage could not be listed: %s — so this is the raw difference)" % disk_why

    if actionable:
        # ⚠ THE OLD SENTENCE ASSERTED A CONSEQUENCE THAT WAS FALSE FOR 93% OF WHAT IT COUNTED.
        # It said "every one of those reels is held as 'not sealed'". Against the frame
        # deleter's own tally of 5022 held frames: NOT SEALED 1247, while the LARGEST held
        # class — 3314 — is reels the vault lane DID seal, and the 346 footage-less sessions
        # hold zero frames between them. [[label-outlived-referent]]
        why = ("%d session(s) with footage still on disk that the %s lane covered and %s never "
               "did — %s's seal is the one the frame deleter reads, so those reels stay held"
               % (len(actionable), a, b, b)) + tail
    else:
        why = ("%s and %s agree on every session whose footage is still on disk" % (a, b)) + tail

    return {
        "pair": [a, b], "state": ("diverged" if actionable else "aligned"),
        "onlyInFirst": len(only),          # unchanged meaning: the raw lifetime difference
        "actionable": len(actionable),     # what a lane could still do something about
        "historyOnly": (None if historic is None else len(historic)),
        "sample": actionable[:4] if actionable else only[:4],
        "why": why,
    }


def owed_counts():
    """How many units of work each lane actually has WAITING. -> {lane: int or None}

    v2301 — the input `lane()` never had. None means nobody could count it, and an uncounted lane
    stays STALLED: a lane that cannot say what it owes has not earned the word IDLE.
    [[unknown-stays-unknown]]
    """
    out = {n: None for n in LANES}
    try:
        import control_app as _ca
    except Exception:
        return out
    try:
        n = _ca._chron_owed_count()
        if isinstance(n, int):
            out["chronicle"] = n
    except Exception:
        pass
    # ⚠ BOTH LANES, OR THE ONE LEFT OUT IS A SELF-INFLICTED UNKNOWN. _vault_owed_reels already
    # existed; measuring only the chronicle would have left the vault lane reading STOPPED for ever
    # on a machine that had simply swept everything — the exact false alarm this change is for.
    # v2304 — the shadow watcher owes work exactly when the game is on screen and nothing is
    # rolling. That is the ONE state in which it is supposed to act, so it is the only state in
    # which its silence is a stall rather than a lane with nothing to do.
    try:
        st = _ca._shadow_state()
        if not st.get("on"):
            out["shadow-watch"] = 0          # switched off by him: nothing is owed, by choice
        else:
            win = None
            try:
                import tv_diablo as _tv
                win = _tv.find_d2r_window_mac()
            except Exception:
                win = None                    # could not look -> leave it None below
            if win is None:
                out["shadow-watch"] = 0 if st.get("recording") else 0
            else:
                out["shadow-watch"] = 0 if st.get("recording") else 1
    except Exception:
        pass
    try:
        v = _ca._vault_owed_reels()
        if isinstance(v, (list, tuple, set)):
            out["vault"] = len(v)
        elif isinstance(v, int):
            out["vault"] = v
    except Exception:
        pass
    return out


def report(now_ms=None, owed=None):
    """Everything, in one object a caller can render or a gate can fail on. -> dict

    ⚠ v2308 — `owed` IS AN ARGUMENT BECAUSE MEASURING IT REACHES INTO THE LIVE TREE. v2301 called
    owed_counts() unconditionally from here, and owed_counts() imports control_app and asks the
    REAL machine. A fixture that seals a deliberately stalled lane then had its verdict decided by
    his console rather than by the fixture — the stall test went green on a tree where nothing was
    owed. A gate whose answer depends on the machine it runs on is not measuring the fixture.
    Callers that want the live picture pass nothing; tests pass what they are testing.
    [[feedback-fixtures-never-touch-live-data]]
    """
    _owed = owed_counts() if owed is None else dict(owed)
    lanes = {n: lane(n, now_ms, owed=_owed.get(n)) for n in LANES}
    divs = [divergence(a, b) for a, b in CORROBORATE]
    # "idle" is a HEALTHY state: swept everything, nothing owed. Only stalled/unknown are bad.
    bad = [l for l in lanes.values() if l["state"] in ("stalled", "unknown")]
    bad += [d for d in divs if d["state"] in ("diverged", "unknown")]
    return {"ok": not bad, "lanes": lanes, "divergences": divs,
            "why": ("every lane is fresh and aligned" if not bad
                    else "; ".join(x["why"] for x in bad))}


def say(rep):
    """Lines a person reads. -> list[str]"""
    out = []
    for n, l in sorted(rep["lanes"].items()):
        mark = {"fresh": "🟢", "stalled": "🔴", "unknown": "⚪"}.get(l["state"], "·")
        out.append("%s %-10s %s" % (mark, n, l["why"]))
    for d in rep["divergences"]:
        mark = {"aligned": "🟢", "diverged": "🔴", "unknown": "⚪"}[d["state"]]
        out.append("%s %-10s %s" % (mark, "+".join(d["pair"]), d["why"]))
    return out


def main(argv=None):
    rep = report()
    for line in say(rep):
        print("   " + line)
    if rep["ok"]:
        print("\n🟢 every extraction lane is doing work and they agree on what is done.")
        return 0
    print("\n🔴 an extraction lane has stopped or two lanes disagree — nothing downstream of it "
          "can be trusted to be complete.")
    return 1


if __name__ == "__main__":
    import sys
    try:
        sys.path.insert(0, HERE)
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
