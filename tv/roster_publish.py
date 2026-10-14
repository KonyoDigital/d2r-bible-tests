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

import html
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
_INT_KEYS = ("level", "looks", "date", "x", "y", "w", "h")
_BUILD_SLOTS = ("head", "neck", "tors", "rarm", "larm", "rrin", "lrin", "belt", "feet", "glov")


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
            if allow == ("build",):
                clean = clean_build(row)
            else:
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
            "allow": ("name", "id", "mule", "x", "y", "w", "h")}


def _gear_item(raw):
    """One worn or stored item: a name, and the id the board renderer already uses."""
    if not isinstance(raw, dict):
        return None
    name = _short_text(raw.get("name"), 80)
    if not name:
        return None
    out = {"name": name}
    ident = raw.get("id")
    if isinstance(ident, str):
        ident = _short_text(ident, 80)
        if ident:
            out["id"] = ident
    for key in ("x", "y", "w", "h"):
        num = raw.get(key)
        if isinstance(num, bool) or not isinstance(num, int) or num < 0 or num > 20:
            continue
        out[key] = num
    return out


def clean_build(raw):
    """One character build, small enough to publish and shaped for the board renderer."""
    if not isinstance(raw, dict):
        return None
    name = _short_text(raw.get("name"), 80)
    if not name:
        return None
    out = {"name": name}
    cls = _short_text(raw.get("cls"), 40)
    if cls:
        out["cls"] = cls
    level = raw.get("level")
    if isinstance(level, int) and not isinstance(level, bool) and 1 <= level <= 99:
        out["level"] = level
    sets = []
    for src in (raw.get("sets") or [])[:4]:
        if not isinstance(src, dict):
            continue
        slots = {}
        for slot, item in (src.get("slots") or {}).items():
            if slot not in _BUILD_SLOTS:
                continue
            clean = _gear_item(item)
            if clean:
                slots[slot] = {k: clean[k] for k in ("id", "name") if k in clean}
        inv = []
        for item in (src.get("inv") or [])[:40]:
            clean = _gear_item(item)
            if clean:
                inv.append(clean)
        sets.append({"name": _short_text(src.get("name"), 40) or "Set 1", "slots": slots, "inv": inv})
    if sets:
        out["sets"] = sets
    stash = []
    for item in (raw.get("stash") or [])[:80]:
        clean = _gear_item(item)
        if clean:
            stash.append(clean)
    if stash:
        out["stash"] = stash
    return out


def clean_book(raw):
    """The console book the page hands this PC. None means there was nothing to keep."""
    if not isinstance(raw, dict):
        return None
    builds = []
    for row in (raw.get("builds") or [])[:12]:
        clean = clean_build(row)
        if clean:
            builds.append(clean)
    owned = []
    for row in (raw.get("owned") or [])[:400]:
        if isinstance(row, str):
            name = _short_text(row, 80)
        elif isinstance(row, dict):
            name = _short_text(row.get("name"), 80)
        else:
            name = None
        if name:
            owned.append(name)
    if not builds and not owned:
        return None
    return {"builds": builds, "owned": owned}


def builds_read(book, now_ms):
    """Character builds the console actually stored. None means the book was not read."""
    if not isinstance(book, dict):
        return None
    builds = book.get("builds")
    if not isinstance(builds, list) or not builds:
        return None
    return {"read": True, "asOf": now_ms, "counts": len(builds), "rows": builds, "allow": ("build",)}


def stash_rows_of(book):
    """Flat stash and inventory cells from a console book. The grid painter uses x, y, w, h."""
    rows = []
    if not isinstance(book, dict):
        return rows
    for build in book.get("builds") or []:
        if not isinstance(build, dict):
            continue
        who = build.get("name") if isinstance(build.get("name"), str) else None
        items = list(build.get("stash") or [])
        for src in build.get("sets") or []:
            if isinstance(src, dict):
                items.extend(src.get("inv") or [])
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                continue
            row = {"name": item["name"]}
            if isinstance(item.get("id"), str):
                row["id"] = item["id"]
            if who:
                row["mule"] = who
            for key in ("x", "y", "w", "h"):
                num = item.get(key)
                if isinstance(num, int) and not isinstance(num, bool):
                    row[key] = num
            rows.append(row)
    return rows


def chronicle_read(tally, now_ms):
    """Counts only, from a tally that did not fail. No name list.

    REG-2200 (#94): this REQUIRED ok:true, but a banked board_tally.json (written by
    board_tally_merge, read via board_tally_load) carries the owner's sets/uniques/runewords with
    NO 'ok' key — so every PC's chronicle came back None and NO PC ever published its progress. A
    failed read (`{ok: False, why: ...}`) still has no counts and is refused below; an explicit
    ok:False is refused here. The counts themselves are the read; a missing 'ok' is not a failure.
    """
    if not isinstance(tally, dict) or tally.get("ok") is False:
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
    # REG-2205 (#99) — a river stamp survives the reel's deletion, so station_counts (built upstream
    # from EVERY stamp) counted GONE reels: measured 198 stamps against 67 live reels. Count a station
    # only for a reel still on the shelf (named), resolved through the same stamps map the rows use.
    # station_counts is kept for the caller's contract but no longer the total. [[stale-reading]]
    if isinstance(stamps, dict):
        live = 0
        for reel in named:
            st = stamps.get(reel)
            if st is None and reel.startswith("reel_"):
                st = stamps.get(reel[len("reel_"):])
            if isinstance(st, str) and st and st != "UNKNOWN":
                live += 1
        counts["stations"] = live
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
    """current, stale, or unknown. A missing clock is unknown, never current — and so is a FUTURE
    clock: REG-2201 (#99) a reading stamped ahead of now (skew) scored `now - as_of` negative, so it
    read 'current' / 'under 1 min ago' in _ago instead of being owned as unknown. [[stale-reading]]"""
    if isinstance(as_of, bool) or not isinstance(as_of, int):
        return "unknown"
    if isinstance(now_ms, bool) or not isinstance(now_ms, int):
        return "unknown"
    # stamped in the FUTURE beyond a minute of skew is a bad clock, not a fresh reading
    if as_of - now_ms > 60000:
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


def refresh_view(view, now_ms):
    """The stored row with ages recomputed from its clocks. A bad file is corrupt."""
    if not isinstance(view, dict):
        return None
    owner = view.get("owner")
    if owner not in OWNERS:
        return None
    if view.get("published") is not True:
        return {"owner": owner, "published": False}
    if view.get("corrupt") is True:
        return {"owner": owner, "published": True, "corrupt": True}
    sections = view.get("sections") if isinstance(view.get("sections"), dict) else {}
    kept = {}
    for name in SECTIONS:
        sec = sections.get(name)
        if not isinstance(sec, dict) or not sec:
            continue
        one = {k: sec[k] for k in sec if k != "age"}
        one["age"] = _age_state(sec.get("asOf"), now_ms)
        kept[name] = one
    out = {"owner": owner, "published": True, "corrupt": False,
           "age": _age_state(view.get("t"), now_ms)}
    if isinstance(view.get("t"), int) and not isinstance(view.get("t"), bool):
        out["t"] = view["t"]
    if kept:
        out["sections"] = kept
    return out


def read_cache(directory, now_ms):
    """The files on disk. No directory means this PC has not fetched, not that the others are empty."""
    if not isinstance(directory, str) or not os.path.isdir(directory):
        return {"ok": True, "fetched": False, "owners": []}
    owners = []
    found = False
    root = os.path.abspath(directory)
    for owner in OWNERS:
        name = cache_file_name(owner)
        path = os.path.abspath(os.path.join(directory, name))
        if os.path.dirname(path) != root or not os.path.isfile(path):
            continue
        found = True
        try:
            with open(path, encoding="utf-8") as fh:
                view = json.load(fh)
        except Exception:
            owners.append({"owner": owner, "published": True, "corrupt": True})
            continue
        fresh = refresh_view(view, now_ms)
        owners.append(fresh if fresh else {"owner": owner, "published": True, "corrupt": True})
    if not found:
        return {"ok": True, "fetched": False, "owners": []}
    return {"ok": True, "fetched": True, "now": now_ms, "owners": owners}


def _ago(as_of, now_ms):
    state = _age_state(as_of, now_ms)
    if state == "unknown":
        return state, None
    minutes = (now_ms - as_of) // 60000
    if minutes < 1:
        words = "under 1 min ago"
    elif minutes < 120:
        words = "%d min ago" % minutes
    else:
        words = "%d hr ago" % (minutes // 60)
    return state, words


def _age_words(state, words):
    """The age phrase. A stale clock says stale. An unknown clock stays unknown."""
    if not words:
        return None
    if state == "stale":
        return words + " stale"
    return words


def _count_text(counts):
    """Words for a measured tally. Chronicle and reels store a dict, not one integer."""
    if isinstance(counts, bool) or counts is None:
        return None
    if isinstance(counts, int):
        return str(counts)
    if not isinstance(counts, dict) or not counts:
        return None
    parts = []
    for key, val in counts.items():
        if not isinstance(key, str) or not key:
            continue
        label = key[:40]
        if isinstance(val, bool) or val is None:
            continue
        if isinstance(val, int):
            parts.append("%s %s" % (label, val))
            continue
        if not isinstance(val, dict):
            continue
        have = val.get("have")
        if isinstance(have, bool) or not isinstance(have, int):
            continue
        total = val.get("total")
        if isinstance(total, int) and not isinstance(total, bool) and total > 0:
            parts.append("%s %s/%s" % (label, have, total))
        else:
            parts.append("%s %s" % (label, have))
    if not parts:
        return None
    return " · ".join(parts)


def _show_cell(value, now_ms=None, key=None):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        if key == "date":
            _state, words = _ago(value, now_ms)
            if words:
                return words
            return "age unknown"
        return str(value)
    if not isinstance(value, str) or not value:
        return None
    low = value.lower()
    if (low.startswith("http") or low.startswith("/") or low.startswith("data:")
            or low.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))):
        return None
    return value[:80]


def _row_line(row, now_ms):
    if not isinstance(row, dict):
        return None
    cells = []
    for key in ("name", "cls", "level", "title", "tier", "mule", "locker", "station", "date", "provenance"):
        cell = _show_cell(row.get(key), now_ms, key)
        if cell:
            cells.append(cell)
    if not cells:
        return None
    return " · ".join(cells)


def roster_html(payload):
    """Read-only markup. A missing fetch is not five empty rosters."""
    if not isinstance(payload, dict) or payload.get("fetched") is not True:
        return '<div class="roster-none">this PC has not fetched a roster yet</div>'
    by = {}
    for row in payload.get("owners") or []:
        if isinstance(row, dict) and row.get("owner") in OWNERS:
            by[row["owner"]] = row
    parts = []
    for owner in OWNERS:
        row = by.get(owner)
        who = html.escape(owner, quote=True)
        if row is None:
            parts.append('<section class="roster-owner"><h3>%s</h3><p>%s was not in this fetch</p></section>'
                         % (who, who))
            continue
        if row.get("corrupt") is True:
            parts.append('<section class="roster-owner"><h3>%s</h3><p>roster is corrupt and rows are not shown</p></section>'
                         % who)
            continue
        if row.get("published") is not True:
            lines = []
            for section in SECTIONS:
                said = never_published_line(owner, section)
                lines.append("<li>%s</li>" % html.escape(said, quote=True))
            parts.append('<section class="roster-owner"><h3>%s</h3><ul>%s</ul></section>'
                         % (who, "".join(lines)))
            continue
        parts.append(_published_html(owner, row, payload.get("now")))
    return "".join(parts)


def _published_html(owner, row, now_ms):
    who = html.escape(owner, quote=True)
    state, words = _ago(row.get("t"), now_ms)
    said = _age_words(state, words)
    if said:
        when = "published " + said
    else:
        when = "published, age unknown"
    klass = "roster-owner"
    if state == "stale":
        klass += " roster-stale"
    blocks = ['<section class="%s"><h3>%s</h3><p>%s</p>' % (klass, who, html.escape(when, quote=True))]
    sections = row.get("sections") if isinstance(row.get("sections"), dict) else {}
    for name in SECTIONS:
        sec = sections.get(name)
        if not isinstance(sec, dict):
            said = never_published_line(owner, name)
            blocks.append("<p>%s</p>" % html.escape(said, quote=True))
            continue
        sec_state, sec_words = _ago(sec.get("asOf"), now_ms)
        label = html.escape(name, quote=True)
        sec_said = _age_words(sec_state, sec_words)
        if sec_said:
            age = "as of " + sec_said
        else:
            age = "age unknown"
        sec_class = "roster-stale" if sec_state == "stale" else "roster-sec"
        blocks.append('<div class="%s"><b>%s</b> %s' % (sec_class, label, html.escape(age, quote=True)))
        counted = _count_text(sec.get("counts"))
        if counted:
            blocks.append(" <span>%s</span>" % html.escape(counted, quote=True))
        rows = sec.get("rows") if isinstance(sec.get("rows"), list) else []
        if rows:
            items = []
            for item in rows:
                line = _row_line(item, now_ms)
                if line:
                    items.append("<li>%s</li>" % html.escape(line, quote=True))
            if items:
                blocks.append("<ul>%s</ul>" % "".join(items))
        blocks.append("</div>")
    blocks.append("</section>")
    return "".join(blocks)
