#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow mode: one console's account stores, uploaded, so another console can show them read only.

The board collects its active world's stores with _collectProgress (the Backup v2 rule: bare names,
this world only, no pointer or identity keys) and posts them to the console. This module decides what
of that may leave the PC, when it is uploaded, and what a viewer is told about its age.

What leaves: `d2r_*` stores only, each one a JSON string as the board wrote it, never re-typed. Stores
that are history logs, film evidence or debug routes stay home (DENY). A string that names a path on
disk or an install id is blanked; nothing else in a store is changed, so the viewer's board reads the
same bytes the owner's board reads and draws the same screens, mods and all.

The upload rides the roster's signing key (roster_sign) to its own worker key `snapshot:<owner>`
(functions/api/snapshot.js). It is change-only and at most once per MIN_GAP_MS, plus one at boot; the
worker holds the daily cap. A viewer reads that record. When the worker cannot be reached the last
copy this PC fetched is shown with the time it was uploaded: shadow works whether the other console
is up or not.
"""

import json
import os
import re

import roster_publish as _rp

OWNERS = _rp.OWNERS
# 20 uploads a day spread over 24 h is one per 72 min; the console waits 75 so the worker's daily cap is
# a backstop, not the pacing. The worker itself only refuses inside 30 min.
MIN_GAP_MS = 75 * 60 * 1000
DAY_CAP = 20
MAX_STORE = 64 * 1024
MAX_TOTAL = 180 * 1024
LIVE_MS = 15 * 60 * 1000

# History, film evidence, AI drafts and debug routes: large, private to that PC, and drawn by no
# screen shadow shows (characters, equipped, inventory, stash, mules, vault).
DENY = frozenset((
    "d2r_tvdHist", "d2r_tvdTallyLog", "d2r_chronicleInboxLog", "d2r_foundEvidence", "d2r_sessionLog",
    "d2r_intakeLog", "d2r_intakeSeen", "d2r_intakeUrl", "d2r_lsrRoute", "d2r_tz_hist_cache",
    "d2r_unseedBackup", "d2r_unseedReport", "d2r_unseedRestoreReport", "d2r_vaultLastReset",
    "d2r_createNow", "d2r_createNowDate", "d2r_createNowAi", "d2r_createNowAiArt", "d2r_createNowAiV",
    "d2r_createNowAiDate", "d2r_aicDraft", "d2r_aicQueue", "d2r_aicThrownLog", "d2r_lastTopScan",
    "d2r_grailFarm", "d2r_storeEmptied", "d2r_installId", "d2r_installIdCache", "d2r_ownerClaim",
    "d2r_activeProfile", "d2r_activeProfileWin", "d2r_activeMachine", "d2r_machineSource",
    "d2r_inboxReader", "d2r_logger", "d2r_testGuest",
))
DENY_PREFIX = ("d2r_quarantine", "d2r_d2jsp_", "d2r_api_")

# Two console answers the board's screens draw beside its stores: the characters this PC's reels learned (with
# what each wore) for the Characters room, and the MAIN gear locks. They ride in the snapshot as d2r_api_<name>,
# the console adds them (a board post may not), and the shadow frame answers GET /api/<name> from them. Only the
# fields the board reads are kept, so a ticking counter does not make every upload "changed".
API_FIELDS = {
    "chars_learned": ("ok", "chars", "gear", "gearWhy", "minVisits", "tierBars", "cPanel"),
    "main_locks": ("ok", "locked", "tracked", "floor", "minSightings", "canEverLock", "blockedWhy"),
    "world": ("machine", "profile", "ledger", "os", "cousin"),
}
# The world the owner's board drew in: which machine and profile its stores belong to, the ledger it keeps and the
# OS it reported. The shadow frame takes these instead of the viewer's own, so a Mac viewing a Windows owner draws
# the Windows world (its ribbon, its seed floor, its prefixes). Closed values only: nothing else rides here.
WORLD_VALUES = {"machine": ("mac", "windows"), "profile": ("main", "ladder"),
                "os": ("MAC", "WINDOWS", "LINUX", "ANDROID", "THIS MACHINE")}
_LEDGER = re.compile(r"^[^\x00-\x1f\"<>\\]{0,40}$")
API_PREFIX = "d2r_api_"

_KEY = re.compile(r"^d2r_[A-Za-z0-9_]{1,60}$")
_PRIVATE = (
    re.compile(r"(?:/Users/|/home/|/private/|/var/folders/)[^\s\"']*"),
    re.compile(r"[A-Za-z]:\\\\?(?:Users|Documents and Settings)\\\\?[^\s\"']*"),
    # An install id is crypto.randomUUID() (v4), dashed or not: the version and variant digits pin the shape so
    # an item or reel hash of 32 hex is left alone.
    re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}(?![0-9a-fA-F])"),
    re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}(?![0-9a-fA-F])"),
    re.compile(r"\b(?:ghp_|gho_|ghs_|github_pat_|xox[abposr]-|sk-)[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\b[A-Za-z0-9][A-Za-z0-9\-]{0,62}\.local\b"),
    re.compile(r"\bI?L?·[0-9a-f]{8}·"),
    re.compile(r"data:image/[^\s\"']*"),
)


def budget():
    """KV writes a day. `together` is today's four PCs: presence 768 + roster 4x25 + snapshot 4xDAY_CAP = 948.
    `worst` is every owner label writing at both caps: 768 + 5x25 + 5xDAY_CAP = 993. Both under the 1000 ceiling."""
    roster = _rp.budget()
    snap = roster["pcs"] * DAY_CAP
    labels = len(OWNERS)
    worst = roster["presence"] + labels * roster["perPc"] + labels * DAY_CAP
    return {"presence": roster["presence"], "roster": roster["roster"], "snapshot": snap,
            "together": roster["together"] + snap, "worst": worst, "ceiling": roster["ceiling"]}


def snapshot_key(owner):
    return ("snapshot:" + owner) if owner in OWNERS else None


def _scrub_text(s):
    out = s
    for rx in _PRIVATE:
        out = rx.sub("", out)
    return out


def _scrub(v):
    """-> (value, changed). Strings that name a path, an install id or a picture are blanked in place."""
    if isinstance(v, str):
        t = _scrub_text(v)
        return t, t != v
    if isinstance(v, list):
        changed = False
        out = []
        for x in v:
            y, c = _scrub(x)
            out.append(y)
            changed = changed or c
        return out, changed
    if isinstance(v, dict):
        changed = False
        out = {}
        for k, x in v.items():
            k2 = _scrub_text(k) if isinstance(k, str) else k
            y, c = _scrub(x)
            out[k2] = y
            changed = changed or c or k2 != k
        return out, changed
    return v, False


def scrub_store(raw):
    """One store's JSON string -> the string that may leave this PC (verbatim when nothing private)."""
    if not isinstance(raw, str):
        return None
    try:
        parsed = json.loads(raw)
    except Exception:
        t = _scrub_text(raw)
        return t
    clean, changed = _scrub(parsed)
    if not changed:
        return raw
    return json.dumps(clean, ensure_ascii=False, separators=(",", ":"))


def allowed_key(k, board=True):
    """May this store leave the PC? board=False also admits the console's own d2r_api_<name> answers."""
    if not isinstance(k, str) or not _KEY.match(k):
        return False
    if not board and k.startswith(API_PREFIX):
        return k[len(API_PREFIX):] in API_FIELDS
    if k in DENY:
        return False
    return not any(k.startswith(p) for p in DENY_PREFIX)


def world_of(raw):
    """The board's {machine, profile, ledger, os} -> the same dict when every value is one it may be, else None."""
    if not isinstance(raw, dict):
        return None
    out = {}
    for k, allowed in WORLD_VALUES.items():
        if raw.get(k) not in allowed:
            return None
        out[k] = raw[k]
    # a ledger name the closed set cannot carry is sent as "" (unnamed) rather than losing the whole world
    ledger = raw.get("ledger")
    out["ledger"] = ledger if isinstance(ledger, str) and _LEDGER.match(ledger) else ""
    if not isinstance(raw.get("cousin"), bool):
        return None
    out["cousin"] = raw["cousin"]
    return out


def api_store(name, payload):
    """-> (store name, JSON string) for one console answer, or None when it is not one the shadow serves."""
    fields = API_FIELDS.get(name)
    if name == "world":
        payload = world_of(payload)
    if not fields or not isinstance(payload, dict):
        return None
    kept = {f: payload[f] for f in fields if f in payload}
    text = scrub_store(json.dumps(kept, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    if text is None or len(text) > MAX_STORE:
        return None
    return API_PREFIX + name, text


def with_api(stores, answers):
    """The board's cleaned stores plus the console answers that could be read. A failed read stays out."""
    out = dict(stores or {})
    for name in sorted(answers or {}):
        got = api_store(name, answers[name])
        if got:
            out[got[0]] = got[1]
    return out


def clean(body):
    """The board's post -> {"stores": {name: json string}, "dropped": [names]} or None.

    A store that is not allowed, not a string, or too big is dropped and NAMED, never sent empty.
    The total is capped by dropping the largest stores first, so the small account stores
    (builds, mules, vault records) are the last to go."""
    if not isinstance(body, dict):
        return None
    stores = body.get("stores")
    if not isinstance(stores, dict):
        return None
    out, dropped = {}, []
    for k in sorted(stores):
        v = stores[k]
        if not allowed_key(k) or not isinstance(v, str):
            dropped.append(str(k)[:60])
            continue
        s = scrub_store(v)
        if s is None or len(s) > MAX_STORE:
            dropped.append(k)
            continue
        out[k] = s
    total = sum(len(k) + len(v) for k, v in out.items())
    for k in sorted(out, key=lambda n: (-len(out[n]), n)):
        if total <= MAX_TOTAL:
            break
        total -= len(k) + len(out[k])
        del out[k]
        dropped.append(k)
    if not out:
        return None
    return {"stores": out, "dropped": sorted(set(dropped))}


def digest(stores):
    """FNV-1a over the packed stores: the same hash functions/api/snapshot.js computes."""
    return _rp.hash_of(_rp.packed(stores or {}))


def due(state, owner, stores, now_ms, boot):
    """-> (body or None, why). Change-only, MIN_GAP_MS apart, one boot post; a refusal waits MIN_GAP_MS."""
    state = state if isinstance(state, dict) else {}
    if not snapshot_key(owner):
        return None, "the owner is not one of the five labels"
    if not stores:
        return None, "the board has not posted its stores"
    d = digest(stores)
    refused = state.get("refuseAt")
    if isinstance(refused, int) and not isinstance(refused, bool) and now_ms - refused < MIN_GAP_MS:
        return None, state.get("why") or "the snapshot was refused"
    if state.get("hash") == d and not boot:
        return None, "unchanged"
    last = state.get("at")
    if (not boot and isinstance(last, int) and not isinstance(last, bool) and now_ms - last < MIN_GAP_MS):
        return None, "within %d min of the last upload" % (MIN_GAP_MS // 60000)
    return {"owner": owner, "boot": bool(boot), "signedAt": now_ms, "hash": d, "stores": stores}, "post"


def apply_reply(state, stores, reply, now_ms):
    state = dict(state or {})
    reply = reply if isinstance(reply, dict) else {}
    d = digest(stores or {})
    stored = reply.get("stored") or []
    state["post"] = {"at": now_ms, "ok": reply.get("ok") is True,
                     "why": str(reply.get("why") or ("stored" if "snapshot" in stored else
                                                    ",".join(s for s in (reply.get("skipped") or []) if isinstance(s, str))))[:200],
                     "signed": bool((reply.get("signing") or {}).get("signed"))}
    if reply.get("ok") is True and "snapshot" in stored:
        state.update(hash=d, at=now_ms, why="uploaded")
        state.pop("refuseAt", None)
        return state
    if reply.get("ok") is True:
        skipped = [s for s in (reply.get("skipped") or []) if isinstance(s, str)]
        if "unchanged" in skipped:
            state["hash"] = d
        state["at"] = now_ms
        state["why"] = "skipped: " + ",".join(skipped)
        return state
    state["refuseAt"] = now_ms
    why = reply.get("why")
    state["why"] = str(why)[:200] if isinstance(why, str) and why else "refused"
    return state


def record_ok(rec, owner):
    """A worker/cache record is usable only when it is this owner's and its hash matches its stores."""
    if not isinstance(rec, dict) or rec.get("owner") != owner:
        return False
    stores = rec.get("stores")
    if not isinstance(stores, dict) or not stores:
        return False
    if not all(allowed_key(k, board=False) and isinstance(v, str) for k, v in stores.items()):
        return False
    t = rec.get("t")
    if not isinstance(t, int) or isinstance(t, bool) or t <= 0:
        return False
    return rec.get("hash") == digest(stores)


def cache_path(directory, owner):
    name = _rp.cache_file_name(owner)
    if not name or not isinstance(directory, str) or not directory:
        return None
    path = os.path.abspath(os.path.join(directory, name))
    if os.path.dirname(path) != os.path.abspath(directory):
        return None
    return path


def write_cache(directory, rec):
    owner = rec.get("owner") if isinstance(rec, dict) else None
    if not record_ok(rec, owner):
        return False
    os.makedirs(directory, exist_ok=True)
    path = cache_path(directory, owner)
    if not path:
        return False
    keep = {k: rec[k] for k in ("owner", "t", "hash", "stores", "intentVerified", "keyId", "dropped") if k in rec}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(keep, fh, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)
    return True


def read_cache(directory, owner):
    path = cache_path(directory, owner)
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
    except Exception:
        return None
    return rec if record_ok(rec, owner) else None


def online_of(owner, fleet):
    """True / False from the presence fleet, None when the fleet was not read or names nobody as this owner."""
    if not isinstance(fleet, dict) or fleet.get("ok") is False:
        return None
    for state, rows in ((True, fleet.get("online")), (False, fleet.get("offline"))):
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            plat = row.get("platform")
            plat = "mac" if plat in ("darwin", "mac", "macos") else plat
            if _rp.owner_of(row.get("nickname"), plat) == owner:
                return state
    return None


def _ago_words(ms):
    m = max(0, ms) // 60000
    if m < 1:
        return "under 1 min ago"
    if m < 120:
        return "%d min ago" % m
    if m < 48 * 60:
        return "%d hr ago" % (m // 60)
    return "%d days ago" % (m // (24 * 60))


def view(owner, rec, now_ms, online=None, source="worker", fetch_why=None):
    """What /api/snapshot-view serves. `live` is the owner's console being up right now; the stores are
    always the last upload, and `words` always says when that upload was made."""
    if owner not in OWNERS:
        return {"ok": False, "owner": owner, "why": "not one of the five owner labels"}
    if not record_ok(rec, owner):
        why = "%s has not uploaded a console snapshot yet" % owner
        if fetch_why and source == "cache":
            why += " (and the site could not be read: %s)" % str(fetch_why)[:80]
        elif fetch_why:
            why += " (the site says: %s)" % str(fetch_why)[:120]
        return {"ok": False, "owner": owner, "why": why, "source": source}
    t = rec["t"]
    ago = _ago_words(now_ms - t)
    if online is True:
        state, words = "live", "%s · live · last change uploaded %s" % (owner, ago)
    elif online is False:
        state, words = "offline", "%s · offline · last upload %s" % (owner, ago)
    else:
        state, words = "unknown", "%s · online UNKNOWN · last upload %s" % (owner, ago)
    if source == "cache":
        words += " · the site could not be read, showing this PC's last copy"
    out = {"ok": True, "owner": owner, "t": t, "hash": rec["hash"], "stores": rec["stores"],
           "state": state, "words": words, "source": source, "ago": ago}
    iv = rec.get("intentVerified")
    out["intentVerified"] = iv if isinstance(iv, bool) else None
    kid = _rp.short_key_id(rec.get("keyId"))
    if kid:
        out["keyId"] = kid
    return out
