#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fleet 3.0 phase 1 — what this PC publishes, and when.

The presence beacon stays on /api/console and never carries an item name.
This module builds a separate body for POST /api/roster. The KV key is the
owner label, not an install id, a hostname, or a path.

A section that was not read is left out. An empty list is not a stand-in
for that. Pictures and frame bytes are dropped before the post. The post
itself is change-only, at most once an hour, plus one at boot when the
body actually changed. The server, not this file, enforces the daily cap.
"""

import json
import os

OWNERS = (
    "Konyo · Mac",
    "Konyo · ALT",
    "Konyo · GrokBot",
    "Dean",
    "Wife PC",
)
SECTIONS = ("characters", "vault", "stash", "owned", "chronicle", "reels")
HOUR_MS = 3600 * 1000
DAY_CAP = 25

_ROW_KEYS = ("name", "cls", "level", "title", "tier", "mule", "locker",
             "looks", "evidence", "date", "station", "provenance")
_INT_KEYS = ("level", "looks", "date")


def budget():
    """The write budget this publish is allowed to add. Presence is already 768."""
    presence, pcs, per = 768, 4, DAY_CAP
    return {"presence": presence, "pcs": pcs, "perPc": per, "roster": pcs * per,
            "ceiling": 1000, "together": presence + pcs * per}


def owner_of(name, platform=None):
    """The roster label for a name this PC already claims, or None.

    A name that is already one of the five labels is that label on every
    platform. The short name Konyo on a mac is the label Konyo · Mac.
    Windows stays unlabeled, and so does a mac named Grok: those machines
    are not this one, and a guess would publish them under the wrong key.
    """
    if name in OWNERS:
        return name
    if name == "Konyo" and platform == "mac":
        return "Konyo · Mac"
    return None


def roster_key(owner):
    if owner not in OWNERS:
        return None
    return "roster:" + owner


def _dirty(v):
    if isinstance(v, str):
        low = v.lower()
        if "data:image" in low or "base64," in low:
            return True
        if any(ext in low for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp")):
            return True
        if len(v) > 400:
            return True
        return False
    if isinstance(v, dict):
        return any(_dirty(k) or _dirty(x) for k, x in v.items())
    if isinstance(v, list):
        return any(_dirty(x) for x in v)
    return False


def _short_text(v, n=80):
    if not isinstance(v, str):
        return None
    s = " ".join(v.split())
    if not s or len(s) > n or _dirty(s):
        return None
    return s


def _short_id(v):
    if not isinstance(v, str):
        return None
    s = v.strip()
    if not s or len(s) > 64 or _dirty(s):
        return None
    if any(c in s for c in "/\\."):
        return None
    return s


def _clean_row(row, allow=None):
    if not isinstance(row, dict):
        return None
    keys = allow or _ROW_KEYS
    out = {}
    for k in keys:
        if k not in row or _dirty(k):
            continue
        v = row[k]
        if k in _INT_KEYS:
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                continue
            out[k] = v
            continue
        if k == "evidence":
            ids = []
            if isinstance(v, list):
                for item in v:
                    sid = _short_id(item)
                    if sid:
                        ids.append(sid)
            if ids:
                out[k] = ids[:8]
            continue
        text = _short_text(v)
        if text:
            out[k] = text
    return out or None


def section_of(raw, now_ms=None):
    """One section, or None when it was not read.

    A bare list, including [], is not a read. counts 0 is a read that found
    nothing, and it carries no rows key.
    """
    if not isinstance(raw, dict) or raw.get("read") is not True:
        return None
    as_of = raw.get("asOf")
    if isinstance(as_of, bool) or not isinstance(as_of, int) or as_of <= 0:
        as_of = now_ms if isinstance(now_ms, int) and not isinstance(now_ms, bool) else None
    if isinstance(as_of, bool) or not isinstance(as_of, int) or as_of <= 0:
        return None
    out = {"asOf": as_of}
    counts = raw.get("counts")
    if isinstance(counts, bool):
        counts = None
    if isinstance(counts, int) and counts >= 0:
        out["counts"] = counts
    elif isinstance(counts, dict):
        cleaned = {}
        for k, v in counts.items():
            if _dirty(k):
                continue
            if isinstance(v, dict):
                pair = {}
                have, total = v.get("have"), v.get("total")
                if isinstance(have, int) and not isinstance(have, bool) and have >= 0:
                    pair["have"] = have
                if isinstance(total, int) and not isinstance(total, bool) and total > 0:
                    pair["total"] = total
                if pair:
                    cleaned[str(k)[:40]] = pair
            elif isinstance(v, int) and not isinstance(v, bool) and v >= 0:
                cleaned[str(k)[:40]] = v
        if cleaned:
            out["counts"] = cleaned
    rows = raw.get("rows")
    allow = raw.get("allow")
    if isinstance(rows, list) and rows:
        kept = []
        for row in rows:
            clean = _clean_row(row, allow if isinstance(allow, tuple) else None)
            if clean:
                kept.append(clean)
        if kept:
            out["rows"] = kept
    if "counts" not in out and "rows" not in out:
        return None
    return out


def sections_from(reads, now_ms=None):
    reads = reads if isinstance(reads, dict) else {}
    out = {}
    for name in SECTIONS:
        sec = section_of(reads.get(name), now_ms)
        if sec is not None:
            out[name] = sec
    return out


def characters_read(present, ledger, learned_rows, now_ms):
    if present is not True or not isinstance(ledger, dict) or learned_rows is None:
        return None
    chars = ledger.get("chars")
    if not isinstance(chars, dict):
        return None
    return {"read": True, "asOf": now_ms, "counts": len(chars), "rows": learned_rows,
            "allow": ("name", "cls", "level", "title")}


def vault_read(state, rows, as_of):
    if state != "ok" or rows is None or not isinstance(rows, list):
        return None
    if isinstance(as_of, bool) or not isinstance(as_of, int) or as_of <= 0:
        return None
    return {"read": True, "asOf": as_of, "counts": len(rows), "rows": rows,
            "allow": ("name", "tier", "mule", "locker", "looks", "evidence")}


def stash_read(rows, as_of):
    """A stash list this PC actually read. None means it was not read."""
    if rows is None or not isinstance(rows, list):
        return None
    if isinstance(as_of, bool) or not isinstance(as_of, int) or as_of <= 0:
        return None
    return {"read": True, "asOf": as_of, "counts": len(rows), "rows": rows,
            "allow": ("name", "provenance")}


def chronicle_read(tally, now_ms):
    """Counts only, and only from a tally that says it was read. No name list."""
    if not isinstance(tally, dict) or tally.get("ok") is not True:
        return None
    counts = {}
    for key in ("sets", "uniques", "runewords"):
        pair = tally.get(key)
        if not isinstance(pair, dict):
            continue
        have, total = pair.get("have"), pair.get("total")
        if isinstance(have, bool) or not isinstance(have, int) or have < 0:
            continue
        item = {"have": have}
        if isinstance(total, int) and not isinstance(total, bool) and total > 0:
            item["total"] = total
        counts[key] = item
    if not counts:
        return None
    at = tally.get("at")
    if isinstance(at, bool) or not isinstance(at, int) or at <= 0:
        at = now_ms
    return {"read": True, "asOf": at, "counts": counts}


def reels_read(names, stamps, station_counts, now_ms):
    """Newest rows from a shelf that was listed. names None means the shelf was not read."""
    if names is None or not isinstance(names, list):
        return None
    named = [n for n in names if isinstance(n, str)]
    ordered = list(named)
    try:
        import reel_retention as rr
        ordered = rr.recent_order(named)
    except Exception:
        pass
    newest = list(reversed(ordered))[:16]
    rows = []
    rr = None
    try:
        import reel_retention as rr
    except Exception:
        rr = None
    for reel in newest:
        row = {}
        ts = None
        if rr is not None:
            try:
                ts = rr._reel_ts(reel)
            except Exception:
                ts = None
        if isinstance(ts, int) and not isinstance(ts, bool):
            row["date"] = ts
        station = None
        if isinstance(stamps, dict):
            station = stamps.get(reel)
            if station is None and reel.startswith("reel_"):
                station = stamps.get(reel[len("reel_"):])
        if isinstance(station, str) and station and station != "UNKNOWN":
            row["station"] = station
        if row:
            rows.append(row)
    counts = {"reels": len(named)}
    if isinstance(station_counts, dict):
        total, ok = 0, True
        for value in station_counts.values():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                ok = False
                break
            total += value
        if ok:
            counts["stations"] = total
    return {"read": True, "asOf": now_ms, "counts": counts, "rows": rows,
            "allow": ("date", "station")}


def for_hash(sections):
    out = {}
    for name in sorted((sections or {}).keys()):
        sec = sections[name]
        if not isinstance(sec, dict):
            continue
        kept = {k: sec[k] for k in sorted(sec) if k not in ("asOf", "hash", "allow")}
        out[name] = kept
    return out


def packed(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash_of(text):
    h = 2166136261
    for ch in text:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return "%x" % h


def due(state, owner, sections, now_ms, boot):
    """-> (body or None, why). Unchanged and inside the hour do not post.

    Boot may post a changed body inside the hour. It does not post an
    unchanged body, and it does not retry a refusal inside the hour.
    """
    state = state if isinstance(state, dict) else {}
    if not roster_key(owner):
        return None, "the owner is not one of the five labels"
    if not sections:
        return None, "nothing on this PC was read"
    digest = hash_of(packed(for_hash(sections)))
    refused = state.get("refuseAt")
    if isinstance(refused, int) and not isinstance(refused, bool) and now_ms - refused < HOUR_MS:
        return None, state.get("why") or "the roster refused the last publish"
    if state.get("hash") == digest:
        return None, "unchanged"
    last = state.get("at")
    if (not boot and isinstance(last, int) and not isinstance(last, bool)
            and now_ms - last < HOUR_MS):
        return None, "within the hour"
    return {"owner": owner, "boot": True if boot else False, "sections": sections}, "post"


def apply_reply(state, sections, reply, now_ms):
    """What the client remembers after the server answers. A skip is not a publish."""
    state = dict(state or {})
    reply = reply if isinstance(reply, dict) else {}
    digest = hash_of(packed(for_hash(sections or {})))
    stored = reply.get("stored") or []
    if reply.get("ok") is True and "roster" in stored:
        state["hash"] = digest
        state["at"] = now_ms
        state.pop("refuseAt", None)
        state["why"] = "published"
        return state
    if reply.get("ok") is True:
        skipped = [s for s in (reply.get("skipped") or []) if isinstance(s, str)]
        if "unchanged" in skipped:
            state["hash"] = digest
        state["at"] = now_ms
        state["why"] = "skipped: " + ",".join(skipped)
        return state
    state["refuseAt"] = now_ms
    why = reply.get("why")
    state["why"] = str(why)[:200] if isinstance(why, str) and why else "refused"
    return state


def _age_state(as_of, now_ms):
    """current, stale, or unknown. A missing clock is unknown, never current."""
    if isinstance(as_of, bool) or not isinstance(as_of, int):
        return "unknown"
    if isinstance(now_ms, bool) or not isinstance(now_ms, int):
        return "unknown"
    if now_ms - as_of > 2 * HOUR_MS:
        return "stale"
    return "current"


def view_one(owner, row, now_ms):
    """One owner's fetch row. A bad hash is corrupt and carries no sections."""
    if owner not in OWNERS:
        return None
    if not isinstance(row, dict) or row.get("owner") != owner or row.get("published") is not True:
        return {"owner": owner, "published": False}
    if row.get("corrupt") is True:
        return {"owner": owner, "published": True, "corrupt": True}
    raw = row.get("sections") if isinstance(row.get("sections"), dict) else {}
    kept = {}
    for name in SECTIONS:
        sec = raw.get(name)
        if isinstance(sec, dict) and sec:
            kept[name] = {k: sec[k] for k in sec if k != "age"}
    digest = hash_of(packed(for_hash(kept)))
    if row.get("hash") != digest:
        return {"owner": owner, "published": True, "corrupt": True}
    out = {"owner": owner, "published": True, "corrupt": False, "hash": digest,
           "age": _age_state(row.get("t"), now_ms)}
    if isinstance(row.get("t"), int) and not isinstance(row.get("t"), bool):
        out["t"] = row["t"]
    if kept:
        shown = {}
        for name, sec in kept.items():
            one = dict(sec)
            one["age"] = _age_state(sec.get("asOf"), now_ms)
            shown[name] = one
        out["sections"] = shown
    return out


def view_of(owners, now_ms):
    """Every label, in label order. An owner the reply left out was not published."""
    by = {}
    if isinstance(owners, list):
        for row in owners:
            if isinstance(row, dict) and row.get("owner") in OWNERS:
                by[row["owner"]] = row
    return [view_one(owner, by.get(owner), now_ms) for owner in OWNERS]


def cache_views(reply, now_ms):
    """Views to store, or None when this answer must not replace the cache.

    ok true with no owners list is not "nobody has published". view_of on a
    missing list would write that lie over the last good fetch.
    """
    if not isinstance(reply, dict) or reply.get("ok") is not True:
        return None
    owners = reply.get("owners")
    if not isinstance(owners, list):
        return None
    return view_of(owners, now_ms)


def never_published_line(owner, section):
    if owner not in OWNERS or section not in SECTIONS:
        return None
    return "%s has not published its %s yet" % (owner, section)


def cache_file_name(owner):
    if owner not in OWNERS:
        return None
    return owner.replace(" · ", "__").replace(" ", "_") + ".json"


def write_cache(directory, views):
    """Write one file per owner inside directory. A path that escapes it is skipped."""
    if not isinstance(directory, str) or not directory:
        return []
    os.makedirs(directory, exist_ok=True)
    root = os.path.abspath(directory)
    written = []
    for view in views or []:
        if not isinstance(view, dict):
            continue
        name = cache_file_name(view.get("owner"))
        if not name:
            continue
        if view.get("published") is True and view.get("corrupt") is not True:
            body = view
        elif view.get("corrupt") is True:
            body = {"owner": view.get("owner"), "published": True, "corrupt": True}
        else:
            body = {"owner": view.get("owner"), "published": False}
        path = os.path.abspath(os.path.join(directory, name))
        if os.path.dirname(path) != root:
            continue
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(body, fh, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        os.replace(tmp, path)
        written.append(name)
    return sorted(written)
