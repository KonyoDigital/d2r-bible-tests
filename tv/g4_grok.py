# ══════════════════════════════════════════════════════════════════════════════
# G4 · GROK ACCURACY ADD-ON  —  SELF-CONTAINED, REMOVABLE BOLT-ON  (v1299 scaffold)
# ══════════════════════════════════════════════════════════════════════════════
# Konyo's ruling (2026-07-23): Grok is a SET of cheap, efficient accuracy touchpoints
# with "fingers in a couple of places" — NOT one big watchdog, NOT every frame —
# behind ONE ON/OFF toggle (OFF by default, cousin-safe, needs his own xAI key),
# and "implement it to be taken out eventually" → this whole feature lifts out with
# ZERO scars.
#
# ┌─ HOW TO REMOVE THE ENTIRE G4 FEATURE (zero behavior change) ──────────────────┐
# │ 1. delete this file  (tv/g4_grok.py)                                          │
# │ 2. delete the ONE marked block in control_app.py:                            │
# │       # ══ GROK ADD-ON (G4) ══  …  # ══ END GROK ADD-ON (G4) ══             │
# │ grep -rn "G4\|GROK ADD-ON\|g4_grok\|_g4_verify\|/api/g4" tv/  → every trace. │
# └──────────────────────────────────────────────────────────────────────────────┘
#
# SCAFFOLD ROUND (v1299): the gated shell + a stubbed g4_verify() only. NO touchpoints
# are wired yet — nothing in the engine calls this. When OFF or un-keyed, g4_verify()
# returns None instantly (no network, no import cost), so behavior is byte-identical
# to today. The 2-3 cheap touchpoints (uncertain chronicle route · borderline checker
# keep/toss · grail re-check) land in later rounds by calling g4_verify(context).
#
# The module has NO hard dependency on control_app; it only reads env + a tiny state
# file and uses the stdlib. control_app imports it optionally (try/except) so a missing
# file simply means "feature absent" — never an error.

from __future__ import annotations

import json
import os
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
_STATE_FILE = os.path.join(HERE, "g4_grok.state")   # {"on": bool} — per-machine, gitignored; a future UI toggle writes this

# xAI (OpenAI-compatible) endpoint. Everything is env-overridable; nothing fires OFF.
_XAI_URL = os.environ.get("G4_GROK_URL", "https://api.x.ai/v1/chat/completions")
_XAI_MODEL_DEFAULT = os.environ.get("G4_GROK_MODEL", "grok-4-latest")
_HOURLY_MAX = max(0, int(os.environ.get("G4_GROK_HOURLY_MAX", "40")))    # credit guard: never bulk
_DAILY_MAX = max(0, int(os.environ.get("G4_GROK_DAILY_MAX", "300")))     # credit guard: 24h ceiling
_TIMEOUT_S = float(os.environ.get("G4_GROK_TIMEOUT_S", "12"))

# Selective config: which of the 3 uncertain-only seams may fire. Default = all.
# Set G4_GROK_SEAMS to a comma list (aliases ok) to run only some — e.g.
# G4_GROK_SEAMS=grail-recheck runs ONLY the highest-value seam (cheapest spend).
_SEAM_ALIASES = {
    "chronicle": "chronicle-route", "chronicle-route": "chronicle-route",
    "keep-toss": "checker-keep-toss", "keeptoss": "checker-keep-toss",
    "checker-keep-toss": "checker-keep-toss", "checker": "checker-keep-toss",
    "grail": "grail-recheck", "grail-recheck": "grail-recheck",
}
_ALL_SEAMS = ("chronicle-route", "checker-keep-toss", "grail-recheck")


def _seams_enabled():
    raw = os.environ.get("G4_GROK_SEAMS", "").strip()
    if not raw:
        return set(_ALL_SEAMS)
    out = set()
    for tok in raw.replace(";", ",").split(","):
        c = _SEAM_ALIASES.get(tok.strip().lower())
        if c:
            out.add(c)
    return out or set(_ALL_SEAMS)


def _seam_on(kind):
    return str(kind or "") in _seams_enabled()


# in-process budget ring (cheap, never bulk): timestamps of recent live calls (24h kept)
_CALL_LOG: list[float] = []
_STATS = {"calls": 0, "agree": 0, "disagree": 0, "errors": 0,
          "skipped_budget": 0, "skipped_seam": 0, "last": None}


# ── key + toggle (OFF default, cousin-safe) ─────────────────────────────────────
def _key():
    """The xAI key, from env only (per-machine → cousin-safe). Empty = feature off."""
    return (os.environ.get("XAI_API_KEY") or os.environ.get("G4_XAI_KEY") or "").strip()


def _state_on():
    """Persisted ON/OFF (a future UI toggle writes _STATE_FILE). Missing file = OFF."""
    try:
        with open(_STATE_FILE, encoding="utf-8") as fh:
            return bool((json.load(fh) or {}).get("on"))
    except Exception:
        return False


def switch_on():
    """The raw ON/OFF intent (the switch itself), INDEPENDENT of the key. Two ways to
    switch on: env TV_G4_GROK=1 (the app's TV_* convention, e.g. CI), OR the persisted
    state file (what the UI button flips). Default OFF. Lets a UI honestly show
    'ON — needs your xAI key' (switch on, but still inert) distinct from plain OFF."""
    if os.environ.get("TV_G4_GROK", "0") == "1":
        return True
    if os.environ.get("TV_G4_GROK", "") == "0":
        return False
    return _state_on()


def is_on():
    """The effective toggle: ON only if BOTH the switch is on AND a key exists.
    is_on() is what actually gates any Grok call; switch_on() is the intent."""
    return bool(switch_on() and _key())


def set_on(on):
    """Flip the persisted toggle (for a future /api/g4_toggle route / UI button).
    Does NOT touch env. Returns the new state dict."""
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as fh:
            json.dump({"on": bool(on), "ts": time.time()}, fh)
    except Exception:
        pass
    return status()


def status():
    """Lamp for a UI: whether the add-on is present/on/keyed + budget + call stats. Never leaks the key."""
    _hourly, _daily = _budget_counts()
    return {
        "present": True,
        "switch": switch_on(),      # the raw intent (button state), independent of key
        "on": is_on(),              # effective: switch AND key — what actually gates a call
        "hasKey": bool(_key()),
        "model": _XAI_MODEL_DEFAULT,
        "hourlyMax": _HOURLY_MAX,
        "seams": sorted(_seams_enabled()),   # which uncertain-only seams may fire
        "budget": {"hourlyUsed": _hourly, "hourlyMax": _HOURLY_MAX,
                   "dailyUsed": _daily, "dailyMax": _DAILY_MAX},
        "stats": dict(_STATS),
    }


# ── budget guard (only fire on uncertain/important; never bulk) ──────────────────
def _budget_counts(now=None):
    """Trim the ring to 24h; return (hourlyUsed, dailyUsed). Cheap."""
    now = now if now is not None else time.time()
    day = now - 86400.0
    while _CALL_LOG and _CALL_LOG[0] < day:
        _CALL_LOG.pop(0)
    hour = now - 3600.0
    hourly = sum(1 for t in _CALL_LOG if t >= hour)
    return hourly, len(_CALL_LOG)


def _budget_ok(now=None):
    hourly, daily = _budget_counts(now)
    return hourly < _HOURLY_MAX and daily < _DAILY_MAX


# ── the one entry point the touchpoints will call (no-op when OFF) ───────────────
def g4_verify(context):
    """Cheap Grok second-opinion on ONE uncertain/important decision. Returns None the
    instant the add-on is OFF / un-keyed / over-budget / on any error — so a caller can
    always do `v = g4_verify(ctx); if v and not v['agree']: flag()` with zero risk.

    context = {
        "kind": "chronicle-route" | "checker-keep-toss" | "grail-recheck",
        "item": <name>, "proposed": <the deterministic engine's call>,
        "confidence": <num|None>, "detail": {...},   # affixes / tier / sources
    }
    NEVER call this in bulk — only at the 2-3 uncertain/important seams.
    """
    if not is_on():
        return None                      # ← OFF / no key: instant no-op, no network
    if not isinstance(context, dict):
        return None
    if not _seam_on(context.get("kind")):
        _STATS["skipped_seam"] += 1      # this seam is disabled in G4_GROK_SEAMS
        return None
    if not _budget_ok():
        _STATS["skipped_budget"] += 1    # hourly or daily credit ceiling hit
        return None
    try:
        out = _grok_call(context)
        _CALL_LOG.append(time.time())
        _STATS["calls"] += 1
        _STATS["last"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if out and out.get("agree") is True:
            _STATS["agree"] += 1
        elif out and out.get("agree") is False:
            _STATS["disagree"] += 1
        return out
    except Exception as e:
        _STATS["errors"] += 1
        return {"ok": False, "source": "grok", "error": str(e)[:160]}


def _grok_call(context):
    """The actual xAI chat call — a tiny, cheap prompt asking Grok to AGREE/DISAGREE with
    the deterministic verdict for one item. Reached only when the add-on is ON + keyed +
    within budget. Kept deliberately small (low token cost)."""
    kind = str(context.get("kind") or "verify")
    item = str(context.get("item") or "")
    proposed = str(context.get("proposed") or "")
    detail = context.get("detail") or {}
    sys_prompt = (
        "You are a Diablo II: Resurrected (Reign of the Warlock mod) item-accuracy checker. "
        "Given ONE item and the app's deterministic verdict, reply STRICT JSON only: "
        '{"agree": true|false, "verdict": "<your call>", "note": "<=12 words"}. '
        "Be terse. If you lack info to disagree, agree."
    )
    user_prompt = json.dumps({"kind": kind, "item": item, "proposed": proposed, "detail": detail})[:1200]
    body = json.dumps({
        "model": _XAI_MODEL_DEFAULT,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
        "max_tokens": 120,
    }).encode("utf-8")
    req = urllib.request.Request(_XAI_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + _key())
    with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    txt = (((raw.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    parsed = {}
    try:
        parsed = json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
    except Exception:
        parsed = {"agree": None, "verdict": "", "note": txt[:80]}
    return {
        "ok": True,
        "source": "grok",
        "model": _XAI_MODEL_DEFAULT,
        "agree": parsed.get("agree"),
        "verdict": parsed.get("verdict"),
        "note": parsed.get("note"),
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
