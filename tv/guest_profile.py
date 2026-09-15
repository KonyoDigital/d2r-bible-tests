# -*- coding: utf-8 -*-
"""THE GROK ACTOR — a real profile for the guest seat, and the scrub that keeps it real.

HIS BRIEF, 2026-09-15 (GB-CLAUDE-GROK-PROFILE-SYNC):

    *"Create/maintain a real Grok actor profile for TV DIABLO (nickname Grok, computer grok-bot,
     stable id — rewrite so Konyo is never the live actor) ... Guest /api/status continues to
     report Grok / grok-bot / guest:true"*

WHY THIS IS NOT A COSMETIC RELABEL. The guest seat exists so Grok Bot's eyes can drive SHELF and
VAULT on the box without touching his Mac. Everything it renders comes from a mirror of his live
console, and **this repo is public** — the brief says so in as many words: "No install ids,
hostnames, tokens, or home paths in replies." His real `/api/status` carries an install id, a
`.local` hostname, a unix user and absolute home paths. A rewrite that changed only the nickname
would leave every one of those in the mirror, in the fixture packs built from it, and in any
evidence screenshot posted to a public issue.

So `scrub()` is a REDACTION that also relabels, and the profile is what it relabels TO.

⚠ FAIL CLOSED, ALWAYS. His brief: *"fail closed on unreadable stores (no false HOLDS / empty
wipe)"*. An unreadable store must never become `{}` or `[]` on the guest, because an empty vault
and an unread vault look identical on screen and only one of them means "you own nothing". Every
reader here returns an explicit `unreadable` record instead. [[zero-needs-a-denominator]]

⚠ THE WORD "GUEST" IS ALREADY TAKEN IN THIS CODEBASE AND MEANS SOMETHING ELSE. control_app uses
"guest world" for an UNCLAIMED BOARD IDENTITY — the `I·<id8>·` localStorage prefix that appears
when a probe opens the board without the owner claim. That is a storage-world concept and has
nothing to do with this seat. This module says GUEST SEAT wherever it means the box.
[[label-outlived-referent]]
"""
import hashlib
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass

# ── THE ACTOR ─────────────────────────────────────────────────────────────────────────────────
# A STABLE id, because the seat is a persistent actor rather than a fresh anonymous visitor: the
# board keys some of its stores by identity, so an id that changed per run would mint a new empty
# world on every look and Grok would report an empty SHELF forever. Derived from a constant string
# so it is reproducible on any machine and carries nothing about his.
GROK_NICKNAME = "Grok"
GROK_COMPUTER = "grok-bot"
GROK_USER = "grok"
GROK_PLATFORM = "linux"
GROK_ID = hashlib.sha256(b"tv-diablo-guest-seat/grok-bot/v1").hexdigest()[:32]


def profile():
    """The actor the guest seat reports as. Shaped exactly like control_app's identity payload,
    plus `guest: True` which the box's doctor asserts."""
    return {
        "id": GROK_ID,
        "computer": GROK_COMPUTER,
        "user": GROK_USER,
        "platform": GROK_PLATFORM,
        "createdAt": "2026-09-15T00:00:00",
        "nickname": GROK_NICKNAME,
        "guest": True,
    }


# ── THE SCRUB ─────────────────────────────────────────────────────────────────────────────────
# Anything that identifies HIS machine. Ordered longest-first at build time so a substring never
# eats its own container (e.g. the user name inside the home path).
def _secrets(live_identity=None):
    out = []
    ident = live_identity or {}
    for key, repl in (("id", GROK_ID), ("computer", GROK_COMPUTER), ("user", GROK_USER)):
        v = ident.get(key)
        if isinstance(v, str) and len(v) >= 3:
            out.append((v, repl))
            # hostnames appear both as `konyo-3.local` and bare `konyo-3`
            if key == "computer" and v.endswith(".local"):
                out.append((v[: -len(".local")], GROK_COMPUTER))
    # the home path is not in the identity payload but rides along in file paths everywhere
    home = os.path.expanduser("~")
    if home and home not in ("/", ""):
        out.append((home, "/home/box"))
        base = os.path.basename(home)
        if base and len(base) >= 3:
            out.append((base, GROK_USER))
    out.append(("Konyo", GROK_NICKNAME))
    return sorted(out, key=lambda p: len(p[0]), reverse=True)


def scrub(obj, live_identity=None, _pairs=None):
    """Deep-rewrite every trace of his machine into the Grok actor's. -> a new object.

    Strings, dict keys AND values, lists, nested — all of it. A scrub that only walked values
    would leave `{"/Users/<him>/...": ...}` keys intact, and those are exactly what a per-session
    dump is keyed by.
    """
    pairs = _pairs if _pairs is not None else _secrets(live_identity)
    if isinstance(obj, str):
        s = obj
        for old, new in pairs:
            if old and old in s:
                s = s.replace(old, new)
        return s
    if isinstance(obj, dict):
        return dict((scrub(k, None, pairs), scrub(v, None, pairs)) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return [scrub(x, None, pairs) for x in obj]
    return obj


def rewrite_status(payload, live_identity=None):
    """The one payload the box's doctor asserts on. Scrubbed, then the identity REPLACED outright
    rather than patched — a merge would keep any key of his the scrub did not know about."""
    out = scrub(payload, live_identity or (payload or {}).get("identity"))
    if isinstance(out, dict):
        out["identity"] = profile()
        out["guest"] = True
    return out


def unreadable(what, why):
    """The record an unreadable store leaves. NEVER {} or [] — an empty vault and an unread vault
    look identical on screen and only one of them means he owns nothing."""
    return {"ok": False, "guest": True, "unreadable": True, "what": what, "why": str(why)[:300]}


def is_unreadable(obj):
    return isinstance(obj, dict) and obj.get("unreadable") is True


def leaks(obj, live_identity=None):
    """-> [strings from HIS machine still present]. The gate this module exists to pass.

    Used by the sync script before anything is copied to the box, and by the law. An empty list
    is only meaningful next to the number of secrets it looked for, which the caller prints.
    """
    pairs = _secrets(live_identity)
    blob = json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str) else obj
    found = []
    for old, _new in pairs:
        if old and old in blob:
            found.append(old)
    return found


# ── THE PROGRESS SEED ─────────────────────────────────────────────────────────────────────────
# WHY THE GUEST BOARD READS 0/135 AND THAT IS NOT A BUG. bible.html decides the world with
#     var m = /mac|iphone|ipad|ipod/i.test(plat) ? 'mac' : 'windows';
# so a LINUX box falls to 'windows', gets the isolated W-world and starts from zero. Its own
# comment says why: *"a machine wrongly placed in its OWN world sees an empty console, while a
# machine wrongly placed in the OWNER's world sees someone else's chronicle"* — empty is the
# deliberately safe side, and claiming the mac world on the guest is the failure that rule exists
# to prevent. So the seat is filled by SEEDING the cousin world, never by re-labelling it.
#
# The board already has the door: `exportProgress` / `importProgress`, schema v2, whose `data` is
# a FLAT bare-named store map that `_applyProgress` routes into whichever world is active. This
# builds the same payload from a ledger backup on disk, so no Mac mouse is needed.
PROGRESS_APP = "d2r-bible"
PROGRESS_KIND = "grail-progress"
PROGRESS_VERSION = 2


def progress_seed(ledger_backup, live_identity=None, build="guest-seed"):
    """A snapshot the guest board can IMPORT, built from a ledger backup. -> dict

    ⚠ It carries his progress, which is the point — the seat is useless empty. It does NOT carry
    his machine: every value goes through the same scrub as the mirror.
    """
    with io.open(ledger_backup, encoding="utf-8") as fh:
        book = json.load(fh)
    stores = (book or {}).get("allStores") or {}
    if not isinstance(stores, dict) or not stores:
        return unreadable("progress seed",
                          "the ledger backup carries no allStores map, so there is nothing to "
                          "seed — which is not the same as his having no progress")
    data = {}
    for k, v in stores.items():
        # forked keys export under their BARE names; a prefixed key belongs to another world and
        # must not ride along, exactly as _collectProgress scopes to the ACTIVE account.
        if any(str(k).startswith(p) for p in ("L\u00b7", "W\u00b7", "WL\u00b7", "I\u00b7")):
            continue
        data[k] = v
    out = {
        "app": PROGRESS_APP, "kind": PROGRESS_KIND, "version": PROGRESS_VERSION,
        "meta": {"schemaVersion": PROGRESS_VERSION, "build": build,
                 "profile": "main", "machine": "windows",
                 "seededFor": GROK_NICKNAME,
                 "why": ("a scrubbed snapshot of the owner's progress, staged so the guest seat "
                         "has something real to browse. The guest world stays ISOLATED — "
                         "importing here cannot reach his Mac.")},
        "exported": (book or {}).get("savedTs") or (book or {}).get("ts"),
        "data": data,
    }
    return scrub(out, live_identity)


if __name__ == "__main__":
    print(json.dumps(profile(), indent=2))
