#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Multi-lock capture targeting for TV DIABLO film.

Default remains the safe single D2 pin. Extra pins (Chrome / GeForce NOW) are
opt-in only:

    TV_CAPTURE=multi                 → primary auto (D2) + one Chrome/GFN extra
    TV_CAPTURE_EXTRA=chrome|gfn      → same extras on top of TV_CAPTURE=auto|window|full

Frame lanes (so theatre/shelf never mix sources):

    eye.jpg / live.jpg / hist/f_<ms>.jpg     → primary D2 (unchanged)
    eye.<kind>.jpg / live.<kind>.jpg         → extra live preview
    hist/x_<kind>_<ms>.jpg                   → extra archive (NOT f_*, on purpose)

Status JSON:

    captureTarget   → primary dict {mode, label, wid, kind, file}  (kind/file additive)
    captureTargets  → list of every pin, primary first
    captureLock     → "single" | "multi"
"""
from __future__ import annotations

import os
import re


# Primary TV_CAPTURE values that keep today's D2-only pin. "multi" is an alias
# that means auto + chrome extra; it is NOT a new grabber mode.
_PRIMARY_MODES = ("auto", "window", "win", "game", "full")

# Extra kinds Elad can arm for guest/GFN testing. One extra pin max.
EXTRA_KINDS = ("chrome", "gfn")

_KIND_RE = re.compile(r"^[a-z][a-z0-9]{0,15}$")

# Chromium family only — Safari/Firefox stay out (GFN-in-Chrome is the guest path).
_CHROME_OWNERS = (
    "google chrome",
    "chrome",
    "chromium",
    "microsoft edge",
    "brave browser",
    "brave",
    "chrome.exe",
    "msedge.exe",
    "brave.exe",
)

_GFN_TITLE_TOKENS = (
    "geforce now",
    "geforcenow",
    "geforce-now",
    "play.geforcenow",
    "nvidia geforce now",
)

# Never an extra pin, even when multi is armed. Mirrors the D2 scorer's hard rejects.
_EXTRA_TITLE_BLOCK = (
    "farming bible",
    "d2r bible",
    "tv diablo",
    "localhost",
    "127.0.0.1",
    "crossover",
    "cross over",
    "battle.net",
    "battle net",
)

def _env(env, key, default=""):
    src = env if env is not None else os.environ
    try:
        return (src.get(key) or default)
    except Exception:
        return default


def _norm_kind(tok):
    t = (tok or "").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    if t in ("gfn", "geforce", "geforcenow", "geforcenowchrome", "nvidia"):
        return "gfn"
    if t in ("chrome", "googlechrome", "chromium", "edge", "brave"):
        return "chrome"
    return None


def capture_lock_plan(env=None):
    """Parse TV_CAPTURE + TV_CAPTURE_EXTRA.

    Returns {primary_mode, extra_kinds, lock}. extra_kinds is empty unless opted in.
    Unknown extra tokens are ignored (they do not flip lock to multi).
    """
    raw = (_env(env, "TV_CAPTURE", "auto") or "auto").strip().lower()
    extra_raw = (_env(env, "TV_CAPTURE_EXTRA", "") or "").strip().lower()

    primary = raw if raw else "auto"
    extras = []

    if primary == "multi":
        primary = "auto"
        extras.append("chrome")

    if extra_raw:
        for tok in extra_raw.replace("|", ",").replace(";", ",").replace(" ", ",").split(","):
            tok = tok.strip()
            if not tok:
                continue
            if tok in ("1", "true", "yes", "on"):
                extras.append("chrome")
                continue
            kind = _norm_kind(tok)
            if kind:
                extras.append(kind)

    # One extra pin. gfn is the stricter chrome subset — if both asked, prefer gfn.
    if "gfn" in extras:
        extra_kinds = ("gfn",)
    elif "chrome" in extras:
        extra_kinds = ("chrome",)
    else:
        extra_kinds = ()

    if primary not in _PRIMARY_MODES:
        # capture_mac treats unknown as the full-screen fallback; keep that law here.
        primary = primary or "auto"

    return {
        "primary_mode": primary,
        "extra_kinds": extra_kinds,
        "lock": "multi" if extra_kinds else "single",
    }


def extras_armed(env=None):
    return capture_lock_plan(env)["lock"] == "multi"


def sanitize_kind(kind, default="d2"):
    k = (kind or default or "d2").strip().lower()
    if k in ("game", "d2r", "diablo", "primary", ""):
        return "d2"
    if not _KIND_RE.match(k):
        return default or "d2"
    return k


def eye_filename(kind="d2"):
    k = sanitize_kind(kind)
    return "eye.jpg" if k == "d2" else ("eye.%s.jpg" % k)


def live_filename(kind="d2"):
    k = sanitize_kind(kind)
    return "live.jpg" if k == "d2" else ("live.%s.jpg" % k)


def extra_archive_name(kind, ms):
    """Tagged extra archive. Must NOT use the f_<ms>.jpg prefix the D2 reel owns."""
    k = sanitize_kind(kind, default="chrome")
    if k == "d2":
        return "f_%d.jpg" % int(ms)
    return "x_%s_%d.jpg" % (k, int(ms))


def is_intelligence_skip_name(name):
    """Film / extra-lane / status files that must never starve live.bmp intelligence."""
    n = os.path.basename(name or "").lower()
    if n in ("read.jpg", "eye.jpg", "cap_target.json", "eye.last.jpg"):
        return True
    if n.startswith("eye.") and n.endswith((".jpg", ".jpeg", ".png", ".bmp")):
        return True
    # live.jpg / live.png / live.bmp stay intelligence candidates; live.gfn.jpg does not.
    if n.startswith("live.") and n not in ("live.jpg", "live.png", "live.bmp"):
        return True
    if n.startswith("x_") and n.endswith(".jpg"):
        return True
    if n.startswith("cap_target"):
        return True
    return False


def title_is_gfn(title):
    tl = (title or "").strip().lower()
    if not tl:
        return False
    return any(tok in tl for tok in _GFN_TITLE_TOKENS)


def _owner_is_chrome_family(owner_l):
    ol = (owner_l or "").strip().lower()
    if not ol:
        return False
    # Exact owner names only — "Not Chrome" / helpers must not sneak in via substring.
    return ol in _CHROME_OWNERS


def _extra_owner_blocked(owner_l):
    ol = (owner_l or "").strip().lower()
    if not ol:
        return True
    if "d2r.exe" in ol or ol.endswith("d2r.exe"):
        return True
    if ol in ("crossover", "cross over") or ol.startswith("crossover"):
        return True
    if "battle.net" in ol or ol in ("battle.net.exe", "battle net"):
        return True
    if ol in ("python",) or "tv diablo" in ol:
        return True
    if ol in ("code", "cursor", "visual studio code", "terminal", "iterm2", "warp"):
        return True
    return False


def score_chrome_gfn_window_candidate(owner, title, width, height, onscreen=True,
                                      kind="chrome"):
    """Score a Chrome/GFN window for the EXTRA pin only. None = never pin.

    This scorer is intentionally the inverse of score_d2r_window_candidate: browsers
    that the D2 pin must never take are the only windows this pin may take, and
    Battle.net / CrossOver Home / TV DIABLO / the bible tab stay dead.
    """
    ol = (owner or "").strip().lower()
    tl = (title or "").strip().lower()
    ww, hh = int(width or 0), int(height or 0)
    if ww < 640 or hh < 480:
        return None
    if _extra_owner_blocked(ol):
        return None
    if not _owner_is_chrome_family(ol):
        return None
    if any(b in tl for b in _EXTRA_TITLE_BLOCK):
        return None
    want = sanitize_kind(kind, default="chrome")
    is_gfn = title_is_gfn(tl)
    if want == "gfn" and not is_gfn:
        return None
    score = 100
    if is_gfn:
        score += 5000
    if onscreen:
        score += 40
    if hh >= 700:
        score += 50
    score += min((ww * hh) // 100000, 20)
    return score


def pick_extra_window(windows, kind="chrome"):
    """Pick the best extra pin from an iterable of window dicts.

    Each window: {owner, title, width, height, wid, onscreen}.
    Returns {kind, label, wid, mode} or None.
    """
    want = sanitize_kind(kind, default="chrome")
    best = None  # (score, area, wid, label, resolved_kind)
    for w in windows or []:
        try:
            owner = w.get("owner") or ""
            title = w.get("title") or ""
            ww = int(w.get("width") or 0)
            hh = int(w.get("height") or 0)
            wid = w.get("wid")
            if not wid:
                continue
            sc = score_chrome_gfn_window_candidate(
                owner, title, ww, hh,
                onscreen=bool(w.get("onscreen", True)),
                kind=want)
            if sc is None:
                continue
            label = ("%s" % owner) + ((" · %s" % title) if title else "")
            resolved = "gfn" if title_is_gfn(title) else "chrome"
            if want == "gfn":
                resolved = "gfn"
            cand = (sc, ww * hh, int(wid), label[:80], resolved)
            if best is None or cand > best:
                best = cand
        except Exception:
            continue
    if not best:
        return None
    return {
        "kind": best[4],
        "mode": "window",
        "label": best[3],
        "wid": best[2],
        "file": eye_filename(best[4]),
    }


def waiting_extra(kind):
    k = sanitize_kind(kind, default="chrome")
    label = ("GeForce NOW window not found" if k == "gfn"
             else "Chrome / GeForce NOW window not found")
    return {
        "kind": k,
        "mode": "waiting",
        "label": label,
        "wid": None,
        "file": eye_filename(k),
    }


def as_primary_target(cap, kind="d2"):
    """Backward-compatible captureTarget dict. Additive kind/file only."""
    cap = dict(cap or {})
    mode = (cap.get("mode") or "waiting")
    label = cap.get("label") if cap.get("label") is not None else ""
    out = {
        "mode": mode,
        "label": label,
        "wid": cap.get("wid"),
    }
    k = sanitize_kind(cap.get("kind") or kind)
    out["kind"] = k
    out["file"] = cap.get("file") or eye_filename(k)
    return out


def build_capture_status(primary, extras=None, env=None):
    """Status projection. captureTarget stays a dict; captureTargets is the list.

    extras=None means "not armed / unknown extras" → empty extra list, lock from env.
    A waiting extra (wid None) still counts as multi when the plan opted in, so the
    guest machine can see the lock is armed before Chrome appears.
    """
    plan = capture_lock_plan(env)
    primary_out = as_primary_target(primary)
    extra_list = []
    if plan["lock"] == "multi":
        raw_extras = list(extras or [])
        if not raw_extras:
            for kind in plan["extra_kinds"]:
                extra_list.append(waiting_extra(kind))
        else:
            for e in raw_extras:
                if not isinstance(e, dict):
                    continue
                item = dict(e)
                k = sanitize_kind(item.get("kind") or "chrome", default="chrome")
                item["kind"] = k
                item.setdefault("mode", "waiting")
                item.setdefault("label", "")
                item.setdefault("wid", None)
                item["file"] = item.get("file") or eye_filename(k)
                extra_list.append(item)
    targets = [primary_out] + extra_list
    return {
        "captureTarget": primary_out,
        "captureTargets": targets,
        "captureLock": plan["lock"],
    }


def extras_from_disk_payload(payload):
    """Read extras out of cap_target.json without breaking the classic 3-key shape."""
    if not isinstance(payload, dict):
        return []
    raw = payload.get("captureTargets")
    if not isinstance(raw, list):
        return []
    out = []
    for e in raw:
        if not isinstance(e, dict):
            continue
        k = sanitize_kind(e.get("kind") or "", default="")
        if not k or k == "d2":
            continue
        out.append({
            "kind": k,
            "mode": e.get("mode") or "waiting",
            "label": (e.get("label") or "")[:120],
            "wid": e.get("wid"),
            "file": e.get("file") or eye_filename(k),
        })
    return out


def primary_from_disk_payload(payload):
    """Classic pin only — never return nested captureTargets as captureTarget keys."""
    if not isinstance(payload, dict):
        return {}
    out = {}
    for k in ("mode", "label", "wid"):
        if k in payload:
            out[k] = payload.get(k)
    return out
