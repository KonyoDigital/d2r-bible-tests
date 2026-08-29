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
}

#: lanes that should cover the same sessions. A session in the first and not the second is the
#: divergence that hid a five-day stall.
CORROBORATE = [("chronicle", "vault")]


def _load(name):
    """-> (dict|None, why). None means UNREADABLE, which is never healthy."""
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
    return blob, ""


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


def lane(name, now_ms=None):
    """One lane's health. -> dict"""
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
    stalled = age > stall_h
    return {
        "lane": name, "state": ("stalled" if stalled else "fresh"),
        "sessions": len(blob), "ageHours": round(age, 1), "stallAfterHours": stall_h,
        "what": what,
        "why": ("%s: %d session(s), last did work %.1f h ago%s"
                % (name, len(blob), age,
                   (" — past the %.0f h mark, so this lane has STOPPED and nothing else was going "
                    "to say so" % stall_h) if stalled else "")),
    }


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
    return {
        "pair": [a, b], "state": ("diverged" if only else "aligned"),
        "onlyInFirst": len(only), "sample": only[:4],
        "why": ("%d session(s) the %s lane covered that %s never did — and %s's seal is the one "
                "the frame deleter reads, so every one of those reels is held as 'not sealed'"
                % (len(only), a, b, b)) if only else
               ("%s and %s agree on every session" % (a, b)),
    }


def report(now_ms=None):
    """Everything, in one object a caller can render or a gate can fail on. -> dict"""
    lanes = {n: lane(n, now_ms) for n in LANES}
    divs = [divergence(a, b) for a, b in CORROBORATE]
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
