#!/usr/bin/env python3
"""CF-8 — an UNKNOWN that carries its age.

A health check that cannot ask still has a FIRST-SEEN and a LAST-ATTEMPT. Without those,
"unaskable for 5 minutes" and "unaskable for 45 hours" render identically, forever.

This module STAMPS. It never promotes UNKNOWN to ok or missing because time passed.
An UNKNOWN that ages is still UNKNOWN. [[unknown-stays-unknown]] [[stale-reading]]

    python3 -c "import unknown_age as u; print(u.attach([{'check':'x','state':'unknown','why':'closed'}]))"
"""
from __future__ import annotations

import io
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# Tests set TV_UNKNOWN_AGE to a tempfile. Production writes the gitignored default.
def path():
    env = os.environ.get("TV_UNKNOWN_AGE")
    if env:
        return env
    return os.path.join(HERE, ".unknown_age.json")


def _now():
    return int(time.time() * 1000)


def _load():
    """-> dict | None. None is UNKNOWN (could not read). {} is measured-empty (no file yet).

    A missing file is empty history, not a failed read — no except returns {}. A file that
    exists and will not parse is None, and attach() must not _save over it.
    """
    p = path()
    if not os.path.exists(p):
        return {}
    try:
        with io.open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def _save(d):
    p = path()
    tmp = p + ".tmp"
    try:
        with io.open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=1, sort_keys=True)
        os.replace(tmp, p)
    except Exception:
        try:
            os.remove(tmp)
        except Exception:
            pass


def age_say(ms, now_ms=None):
    """Human age of a millisecond timestamp. -> str like '5m' / '3h' / '2d'."""
    try:
        ms = int(ms or 0)
    except (TypeError, ValueError):
        return "UNKNOWN"
    if ms <= 0:
        return "UNKNOWN"
    now = int(now_ms if now_ms is not None else _now())
    sec = max(0, (now - ms) // 1000)
    if sec < 60:
        return "%ds" % sec
    if sec < 3600:
        return "%dm" % (sec // 60)
    if sec < 48 * 3600:
        return "%dh" % (sec // 3600)
    return "%dd" % (sec // 86400)


def attach(rows, now_ms=None):
    """Stamp first-seen / last-attempt onto UNKNOWN rows. Returns the same list, mutated.

    ⚠ NEVER CHANGES `state`. Time passing is not evidence the check became ok or missing.
    """
    now = int(now_ms if now_ms is not None else _now())
    blob = _load()
    writable = isinstance(blob, dict)
    if blob is None:
        blob = {}
    recs = blob.setdefault("checks", {})
    out = rows or []
    for r in out:
        if not isinstance(r, dict):
            continue
        name = r.get("check")
        if not name:
            continue
        rec = recs.get(name) or {}
        state = r.get("state")
        if state == "unknown":
            if not rec.get("firstUnknownTs"):
                rec["firstUnknownTs"] = now
            rec["lastAttemptTs"] = now
            rec["unknownCount"] = int(rec.get("unknownCount") or 0) + 1
            rec["open"] = True
            first = rec["firstUnknownTs"]
            n = rec["unknownCount"]
            last_k = rec.get("lastKnown") or {}
            tail = " · unaskable for %s (%d attempt%s)" % (
                age_say(first, now), n, "" if n == 1 else "s")
            if last_k.get("state") and last_k.get("ts"):
                tail += "; last known %s %s ago" % (last_k["state"], age_say(last_k["ts"], now))
            why = str(r.get("why") or "")
            if "unaskable for " not in why:
                r["why"] = why + tail
            r["firstUnknownTs"] = first
            r["lastAttemptTs"] = now
            r["unknownCount"] = n
        elif state in ("ok", "missing"):
            rec["lastKnown"] = {"state": state, "ts": now}
            rec["open"] = False
            rec["firstUnknownTs"] = None
            rec["unknownCount"] = 0
            rec["lastAttemptTs"] = now
        recs[name] = rec
    blob["checks"] = recs
    if writable:
        _save(blob)
    return out
