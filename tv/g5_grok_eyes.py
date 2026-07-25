# ══════════════════════════════════════════════════════════════════════════════
# G5 · GROK EYES — SUBSCRIPTION CLI LANE  (self-contained, removable bolt-on)
# ══════════════════════════════════════════════════════════════════════════════
# Konyo (2026-07-25): optional parallel / future-primary vision brain via LOCAL
# SuperGrok login — same spirit as Claude's `claude -p` subscription lane.
#
#   POWER SOURCE:  `grok -p`  +  OIDC login (grok login / SuperGrok)
#   NOT:           XAI_API_KEY / console API tokens / api.x.ai Bearer calls
#
# EXTRA only. OFF by default. Claude path unchanged when OFF.
#
# Modes:
#   off      — instant no-op (default, cousin-safe)
#   shadow   — Claude still drives ON AIR; Grok also reads & is logged (no replace)
#   primary  — Grok drives vision reads (Claude-sub gap / future cancel Claude)
#
# ┌─ HOW TO REMOVE THE ENTIRE G5 FEATURE (zero behavior change) ──────────────────┐
# │ 1. delete this file  (tv/g5_grok_eyes.py)                                     │
# │ 2. delete fenced blocks: # ══ GROK EYES (G5) ══ … # ══ END GROK EYES (G5) ══ │
# │ 3. delete tv/g5_sidecar/ + tv/G5_GROK_EYES_REMOVAL.md + G5_PHASE_CHECKLIST   │
# │ grep -rn "GROK EYES (G5)\|g5_grok_eyes\|/api/g5" tv/                         │
# └──────────────────────────────────────────────────────────────────────────────┘
#
# When OFF or not logged in: is_on() false, g5_vision_read() returns None, no CLI.

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_STATE_FILE = os.path.join(HERE, "g5_grok_eyes.state")  # gitignored; per-machine
_SHADOW_LOG = os.path.join(HERE, "g5_shadow.jsonl")    # gitignored; shadow comparisons
_BUDGET_PATH = os.path.join(HERE, "g5_subscription_budget.json")

_HOURLY_MAX = max(0, int(os.environ.get("G5_GROK_HOURLY_MAX", "30")))
_DAILY_MAX = max(0, int(os.environ.get("G5_GROK_DAILY_MAX", "200")))
_TIMEOUT_S = float(os.environ.get("G5_GROK_TIMEOUT_S", "140"))
_MODES = ("off", "shadow", "primary")

# API-style secrets we ALWAYS strip so vision cannot ride console tokens
_API_STRIP = (
    "XAI_API_KEY", "G5_XAI_KEY", "G4_XAI_KEY",
    "OPENAI_API_KEY", "OPENAI_BASE_URL",
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
)

_CALL_LOG: list[float] = []
_STATS = {
    "calls": 0, "ok": 0, "errors": 0, "skipped_budget": 0, "shadow": 0, "primary": 0,
    "last": None, "last_error": None, "lane": "subscription-cli",
}
_LOCK = threading.Lock()
_AUTH_LOGGED = False

_DEFAULT_VISION_PROMPT = (
    "Diablo II Resurrected (RoW) screenshot at path:\n{path}\n\n"
    "Open that image file with the read_file tool FIRST, then reply with STRICT JSON only, "
    "no markdown fences, no prose:\n"
    '{{"area":"","tz":[],"scene":"gameplay","stashTab":"","names":[],'
    '"names_loc":{{}},"sockets":{{}},"discovered":[],"conf":0.0}}\n'
    "scene = one of: town | stash | inventory | loot | gameplay | transition.\n"
    "transition = fullscreen loading/portal with NO bottom HUD; dark combat WITH HUD = gameplay.\n"
    "area = zone name if legible, else \"\".\n"
    "tz = purple terror-zone lines if any, else [].\n"
    "stashTab = only when scene=stash: personal | shared | gems | materials | runes | \"\".\n"
    "names = READABLE item name text only — never invent from icons; never complete partials.\n"
    "sockets = name -> N when Socketed (N) or N holes visible; else {{}}.\n"
    "names_loc = for each name: equipped | inventory | stash | floor.\n"
    "discovered = item names from chat discovery lines only; else [].\n"
    "conf = 0.0-1.0. Be precise."
)


# ── subscription auth (NOT API keys) ───────────────────────────────────────────
def _grok_bin():
    return (
        os.environ.get("G5_GROK_BIN")
        or os.environ.get("TV_GROK_BIN")
        or shutil.which("grok")
        or ""
    ).strip()


def _subscription_logged_in():
    """True if local SuperGrok/Grok Build OIDC session looks present."""
    auth = os.path.expanduser("~/.grok/auth.json")
    try:
        if not os.path.isfile(auth) or os.path.getsize(auth) < 40:
            return False
        with open(auth, encoding="utf-8") as fh:
            d = json.load(fh)
        if not isinstance(d, dict) or not d:
            return False
        # any entry with a key/token blob counts as logged in
        for v in d.values():
            if isinstance(v, dict) and (v.get("key") or v.get("refresh_token") or v.get("auth_mode")):
                return True
        return True  # non-empty auth.json
    except Exception:
        return False


def has_subscription():
    """CLI on PATH + logged in via grok login (SuperGrok). Never checks API keys."""
    return bool(_grok_bin() and _subscription_logged_in())


# Back-compat alias used by older UI/tests — means "can run Grok eyes", not API key
def _key():
    return "subscription" if has_subscription() else ""


def _grok_env():
    """Env for grok -p: SuperGrok OIDC only — strip API tokens like Claude lane does."""
    env = os.environ.copy()
    stripped = [k for k in _API_STRIP if env.pop(k, None) is not None]
    return env, stripped


def _log_auth_once(stripped):
    global _AUTH_LOGGED
    if _AUTH_LOGGED:
        return
    _AUTH_LOGGED = True
    if stripped:
        _STATS["last_error"] = None  # not an error
        # leave a breadcrumb in stats
        _STATS["stripped_api_env"] = ",".join(stripped)


# ── mode / toggle ─────────────────────────────────────────────────────────────
def _load_state():
    try:
        with open(_STATE_FILE, encoding="utf-8") as fh:
            d = json.load(fh) or {}
        mode = str(d.get("mode") or "off").strip().lower()
        if mode not in _MODES:
            mode = "off"
        if d.get("on") and mode == "off":
            mode = "primary"
        return {"on": bool(d.get("on")) or mode in ("shadow", "primary"), "mode": mode}
    except Exception:
        return {"on": False, "mode": "off"}


def _save_state(on, mode):
    mode = str(mode or "off").strip().lower()
    if mode not in _MODES:
        mode = "off"
    if mode == "off":
        on = False
    else:
        on = True
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as fh:
            json.dump({"on": bool(on), "mode": mode, "ts": time.time(), "lane": "subscription-cli"}, fh)
    except Exception:
        pass
    return status()


def switch_on():
    env = (os.environ.get("TV_G5_GROK_EYES") or "").strip().lower()
    if env in ("0", "off", "false", "no"):
        return False
    if env in ("1", "on", "true", "yes", "shadow", "primary"):
        return True
    st = _load_state()
    return st["on"] and st["mode"] != "off"


def mode_intent():
    env = (os.environ.get("TV_G5_GROK_EYES") or "").strip().lower()
    if env in ("0", "off", "false", "no"):
        return "off"
    if env in ("shadow", "sh"):
        return "shadow"
    if env in ("1", "on", "true", "yes", "primary", "pri"):
        return "primary"
    st = _load_state()
    if not st["on"]:
        return "off"
    return st["mode"] if st["mode"] in _MODES else "off"


def mode():
    """Effective mode: needs subscription login for shadow/primary."""
    intent = mode_intent()
    if intent == "off":
        return "off"
    if not has_subscription():
        return "off"
    return intent


def is_on():
    return mode() in ("shadow", "primary")


def is_primary():
    return mode() == "primary"


def is_shadow():
    return mode() == "shadow"


def set_mode(mode_name, on=None):
    m = str(mode_name or "off").strip().lower()
    if m in ("0", "false", "no"):
        m = "off"
    if m in ("1", "true", "yes", "on"):
        m = "primary"
    if m not in _MODES:
        m = "off"
    return _save_state(m != "off", m)


def set_on(on):
    return set_mode("primary" if on else "off")


def status():
    hourly, daily = _budget_counts()
    return {
        "present": True,
        "feature": "g5_grok_eyes",
        "lane": "subscription-cli",  # NOT api.x.ai
        "power": "grok -p + SuperGrok OIDC login (no API keys)",
        "switch": mode_intent(),
        "mode": mode(),
        "on": is_on(),
        "hasKey": has_subscription(),       # UI compat: means "can run", not API key
        "hasSubscription": has_subscription(),
        "grokBin": _grok_bin() or None,
        "model": "subscription-cli",
        "budget": {
            "hourlyUsed": hourly, "hourlyMax": _HOURLY_MAX,
            "dailyUsed": daily, "dailyMax": _DAILY_MAX,
        },
        "stats": dict(_STATS),
        "sidecar": {
            "hint": "python3 tv/g5_sidecar/server.py  (uses same subscription CLI)",
        },
    }


# ── budget (local counters, like intake_local) ────────────────────────────────
def _budget_load():
    try:
        if not os.path.isfile(_BUDGET_PATH):
            return {"calls": []}
        return json.loads(open(_BUDGET_PATH, encoding="utf-8").read()) or {"calls": []}
    except Exception:
        return {"calls": []}


def _budget_save(state):
    try:
        with open(_BUDGET_PATH, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
    except Exception:
        pass


def _budget_counts(now=None):
    now = now if now is not None else time.time()
    state = _budget_load()
    calls = [float(t) for t in (state.get("calls") or []) if now - float(t) < 86400.0]
    hour = [t for t in calls if now - t < 3600.0]
    with _LOCK:
        _CALL_LOG[:] = calls
    return len(hour), len(calls)


def _budget_ok():
    if _HOURLY_MAX <= 0 or _DAILY_MAX <= 0:
        return False
    hourly, daily = _budget_counts()
    return hourly < _HOURLY_MAX and daily < _DAILY_MAX


def _budget_record():
    now = time.time()
    state = _budget_load()
    calls = [float(t) for t in (state.get("calls") or []) if now - float(t) < 86400.0]
    calls.append(now)
    _budget_save({"calls": calls, "last": now})
    with _LOCK:
        _CALL_LOG[:] = calls


# ── vision via grok -p (subscription) ─────────────────────────────────────────
def g5_vision_read(image_path, prompt=None, *, force=False):
    """Vision read via local `grok -p` SuperGrok login. No API keys.

    Returns None if OFF / not logged in / over budget / error.
    force=True: sidecar prove (ignore mode, still requires subscription login).
    """
    if not force and not is_on():
        return None
    if not has_subscription():
        return None
    if not _budget_ok():
        _STATS["skipped_budget"] += 1
        return None

    path = os.path.abspath(str(image_path or ""))
    if not path or not os.path.isfile(path):
        return None

    bin_path = _grok_bin()
    if not bin_path:
        _STATS["last_error"] = "grok CLI not on PATH"
        return None

    text_prompt = (prompt or _DEFAULT_VISION_PROMPT)
    if "{path}" in text_prompt:
        text_prompt = text_prompt.format(path=path)
    else:
        text_prompt = (
            text_prompt
            + "\n\nThe screenshot is at: " + path
            + " — open it with read_file first. Reply STRICT JSON only."
        )

    # Work in throwaway cwd so monorepo project rules don't load
    work = tempfile.mkdtemp(prefix="tvd-g5-")
    env, stripped = _grok_env()
    _log_auth_once(stripped)

    # Prefer adding image dir for tools
    img_dir = os.path.dirname(path)
    args = [
        bin_path,
        "-p", text_prompt,
        "--output-format", "plain",
        "--always-approve",
        "--tools", "read_file",
        "--cwd", work,
        "--disable-web-search",
    ]
    # Allow reading the frame directory
    if img_dir and os.path.isdir(img_dir):
        # some builds support --add-dir; if not, path is absolute and read_file still works
        pass

    t0 = time.time()
    try:
        r = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_S,
            stdin=subprocess.DEVNULL,
            env=env,
            cwd=work,
        )
    except subprocess.TimeoutExpired:
        _STATS["errors"] += 1
        _STATS["calls"] += 1
        _STATS["last_error"] = f"grok -p timeout {_TIMEOUT_S:.0f}s"
        _cleanup(work)
        return None
    except Exception as e:
        _STATS["errors"] += 1
        _STATS["calls"] += 1
        _STATS["last_error"] = str(e)[:160]
        _cleanup(work)
        return None

    _cleanup(work)
    out = (r.stdout or "").strip()
    _STATS["calls"] += 1
    _STATS["last"] = time.strftime("%Y-%m-%d %H:%M:%S")

    if r.returncode != 0 and not out:
        _STATS["errors"] += 1
        err = (r.stderr or "")[:200]
        _STATS["last_error"] = f"grok exit {r.returncode}: {err}"
        return None

    parsed = _loose_parse(out)
    if parsed is None:
        _STATS["errors"] += 1
        _STATS["last_error"] = "no-json from grok -p"
        return None

    _budget_record()
    _STATS["ok"] += 1
    m = mode() if not force else "force"
    if m == "shadow":
        _STATS["shadow"] += 1
    elif m == "primary":
        _STATS["primary"] += 1
    parsed["model"] = "grok-subscription-cli"
    parsed["mode"] = "g5-" + m
    parsed["escalated"] = False
    parsed["ms"] = int((time.time() - t0) * 1000)
    parsed["_raw_txt"] = out[:2048]
    parsed["_g5"] = True
    parsed["_lane"] = "subscription-cli"
    return parsed


def g5_shadow_log(claude_result, grok_result, image_path=""):
    try:
        rec = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "lane": "subscription-cli",
            "image": os.path.basename(str(image_path or "")),
            "claude_names": (claude_result or {}).get("names") if isinstance(claude_result, dict) else None,
            "grok_names": (grok_result or {}).get("names") if isinstance(grok_result, dict) else None,
            "claude_scene": (claude_result or {}).get("scene") if isinstance(claude_result, dict) else None,
            "grok_scene": (grok_result or {}).get("scene") if isinstance(grok_result, dict) else None,
        }
        with open(_SHADOW_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _cleanup(work):
    try:
        shutil.rmtree(work, ignore_errors=True)
    except Exception:
        pass


def _loose_parse(txt):
    if not txt:
        return None
    try:
        a, b = txt.find("{"), txt.rfind("}")
        if a < 0 or b <= a:
            return None
        j = json.loads(txt[a:b + 1])
        if not isinstance(j, dict):
            return None
        names = j.get("names")
        if not isinstance(names, list):
            names = []
        j["names"] = [str(x).strip() for x in names if str(x).strip()][:60]
        j.setdefault("area", "")
        j.setdefault("scene", "gameplay")
        j.setdefault("tz", [])
        j.setdefault("stashTab", "")
        j.setdefault("names_loc", {})
        j.setdefault("sockets", {})
        j.setdefault("discovered", [])
        if not isinstance(j.get("tz"), list):
            j["tz"] = []
        try:
            j["conf"] = float(j.get("conf") if j.get("conf") is not None else 0.0)
        except Exception:
            j["conf"] = 0.0
        return j
    except Exception:
        return None
