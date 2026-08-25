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
import re as _re
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
    "last": None, "last_error": None, "last_error_ts": None, "lane": "subscription-cli",
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

# v1514 — THE SECOND EYE ON THE CHRONICLE. Konyo: "grok for me specifically i can use as a second
# pair of eyes and a different view for also these exact things! it must be also coded in so it is
# IDENTICALLY trying to read and retro chronicle these tallied in."
#
# "Identically" is the requirement AND the trap. The two lanes must answer the SAME question in the
# SAME shape — otherwise their answers cannot be compared, and cross-lane agreement (the strongest
# witness the gate has) would be measuring prompt differences instead of the screen. But they must
# not share a prompt WORDING either, or they inherit the same blind spots and the "independent"
# second opinion is theatre. So: same contract, same refusals, its own words.
CHRONICLE_VISION_PROMPT = (
    "Diablo II Resurrected (RotW mod) screenshot at path:\n{path}\n\n"
    "Open that image with the read_file tool FIRST, then reply with STRICT JSON only, no markdown "
    "fences, no prose:\n"
    '{{"ledger":"{ledger}","found":[],"notFound":[],"sets":[],'
    '"printedFound":null,"printedTotal":null,"stateVisible":true,"wrongTab":false,"notChronicle":false,'
    '"foundAt":{{}},"droppedBy":{{}},"conf":0.0}}\n'
    "This is the in-game CHRONICLE (holy grail) panel: a scrollable list of item names, each row "
    "showing whether the player has FOUND it — bright/coloured text vs grey/dim, a tick, a filled "
    "marker.\n"
    "found = ONLY names whose found-state is VISIBLY positive. notFound = names you can read whose "
    "state is dim, empty or ambiguous.\n"
    # v1839 — mirrored from the Claude lane so the two eyes answer in the same units (v1519's rule:
    # cross-lane agreement is only evidence if both lanes are answering the same question).
    "notChronicle = true when the picture is not a Chronicle panel at all - gameplay, a stash, a "
    "menu, or the TV DIABLO console window. That is a different answer from a Chronicle page whose "
    "rows you cannot judge.\n"
    "If you cannot tell found from unfound anywhere on the panel: set stateVisible=false and return "
    "found EMPTY. Do not assume everything shown is owned — this read is unattended and a confident "
    "wrong page permanently mis-tallies his grail.\n"
    # v1827 — A `First Found:` LINE IS ITSELF THE FOUND-STATE, and not saying so was throwing away
    # readable pages. Konyo's sets reel refused 20 of 35 attempts; pulling one of the refusals and
    # LOOKING at it settled why. The frame is a perfectly legible SETS page - M'avina's Tenet
    # (Demon Imp, 05/19/2026), M'avina's Icy Clutch (The Cow King, 05/18/2026), the Trang-Oul's
    # Avatar heading, then Girth and Claws each with their own date - and the reader returned
    # stateVisible=false.
    # The rule above was written for the UNIQUES panel, where unfound rows are dim silhouettes
    # sitting next to bright found ones, so "can you tell them apart" is answerable by contrast. A
    # SETS page showing only owned rows has nothing to contrast against, and an honest reader
    # following that rule literally must refuse it. The refusal was correct behaviour from an
    # incomplete instruction.
    "A row that prints a `First Found:` date IS found - that line is the found-state by itself, and "
    "needs nothing to compare against. A page where EVERY visible row carries one is a page where "
    "every visible row is found; report them and do NOT set stateVisible=false. Only say "
    "stateVisible=false when the rows carry no found-state you can read at all - no dates, no ticks, "
    "no bright/dim distinction.\n"
    "THE LEDGER YOU WERE GIVEN IS {ledger}. uniques = single unique items (Harlequin Crest, "
    "Windforce, Stormshield). sets = rows grouped under SET names (Tal Rasha's Wrappings, Immortal "
    "King). If the panel on screen is the OTHER one, set wrongTab=true and return found empty.\n"
    # v1566 — see tv_diablo.py: the second eye must speak the same shape as the first, or a
    # cross-lane agreement on a COMPLETE set is impossible by construction.
    "sets = only when ledger=sets: [{{\"set\":\"<set name>\",\"pieces\":[<found piece names>],\"complete\":true|false}}].\n"
    "set `complete` true ONLY when the panel itself marks that set finished — never inferred.\n"
    # v1826 — see tv_diablo.py: the same tell, worded the same way. Measured on his swept evidence,
    # 4 of 16 set groups were keyed by a PIECE name rather than a set. The second eye must describe
    # a group the same way the first does or the two can never agree about one.
    "A SETS page groups its rows under a set-name HEADING. The heading is centred, has NO item "
    "icon, NO `Dropped By:` line and NO `First Found:` line. Every PIECE row has all three. Put the "
    "HEADING in \"set\" and the rows beneath it in \"pieces\" — never a piece name in \"set\", and "
    "never a heading in \"pieces\". If you cannot see which heading a row belongs to, leave that "
    "row out rather than inventing a group for it.\n"
    "printedFound / printedTotal = the panel's own progress numbers if it prints any (\"243/403\", "
    "\"Found 108 of 135\") EXACTLY as shown, else null. They are checked against your own count — an "
    "honest mismatch is useful, a fabricated match is not.\n"
    "Only rows you can actually READ belong in either list. A half-remembered item, a plausible "
    "guess at a blurred row, a name you expect to be there — none of those. Leave it out.\n"
    # v1819 — see tv_diablo.py CHRONICLE_READ_PROMPT: the same three fields, worded the same way.
    # The second eye must speak the same shape as the first, or a cross-lane agreement on a find
    # DATE is impossible by construction — which is the same reason `complete` was mirrored here
    # in v1566.
    # v1828 — see tv_diablo.py: `sort` never once arrived (0 of 2358) and the per-row dates make it
    # unnecessary. Removed from both lanes together so the two keep asking for the same thing.
    "foundAt = map each FOUND name -> its exact `First Found:` stamp, copied digit for digit, e.g. "
    '{{"Razorswitch":"08/20/2026, 00:49"}}. Omit any row whose stamp is hidden behind a tooltip or '
    "cut off at the panel edge, and NEVER infer one from a row's position.\n"
    "droppedBy = map each FOUND name -> the monster on its `Dropped By:` line. Omit what you cannot "
    "read.\n"
    "⚠ THE TWO TABS PRINT THOSE LINES IN OPPOSITE ORDER. On UNIQUES a row reads: name / "
    "`First Found: ...` / `Dropped By: ...`. On SETS it reads: name / `Dropped By: ...` / "
    "`First Found: ...`. Read each line by its LABEL, never by its position under the name.\n"
    "conf = 0.0-1.0, your own honest confidence in this page."
)


def g5_chronicle_read(image_path, kind, *, force=True):
    """The Grok lane's chronicle read, in the v1510 worker's response shape.

    Returns None whenever Grok cannot or should not answer (off, not logged in, over budget, error).
    None is a REFUSAL, never an empty page: two_lane_read distinguishes "grok didn't run" from "grok
    saw nothing", and collapsing them would let a dead second lane read as silent agreement.
    """
    ledger = "sets" if str(kind or "").endswith("sets") else "uniques"
    import os as _os
    # v1519 — TV_STUB is the zero-cost seam the Claude lane already honours (v711). Without it here
    # the "free" end-to-end sweep test reached for the real grok CLI: a test that spends money is a
    # test nobody runs, and a second lane nobody exercises is a second lane nobody trusts.
    if _os.environ.get("TV_STUB"):
        try:
            import json as _json
            mp = _os.environ.get("TV_STUB_MANIFEST") or _os.path.join(HERE, "stub_manifest.json")
            with open(mp, encoding="utf-8") as fh:
                man = _json.load(fh)
        except Exception:
            man = {}
        base = _os.path.basename(str(image_path or ""))
        raw = man.get(base + "#chronicle-grok") or man.get("*#chronicle-grok")
        try:
            import chronicle_retro as _cr
        except Exception:
            return None
        # absent from the manifest ⇒ a SILENT lane, which two_lane_read already reports honestly
        return (_cr.normalize_page(raw, kind, "grok", framing="stub")
                if raw is not None else None)
    path = _os.path.abspath(str(image_path or ""))
    # ── v1901 — THE SECOND WITNESS GETS THE SAME PIXELS ───────────────────────────────────────
    # For eleven versions it did not. The Claude lane has cropped to the Chronicle list band since
    # v1780 — measured 0/6 pages full-frame against 5/6 cropped on his own reel — and this lane was
    # handed the whole 2940x1912 desktop grab every single time, because the crop lived inside the
    # Claude reader where nothing else could call it. Two lanes exist so that agreement between them
    # is evidence; agreement between witnesses shown different pictures is worth less than it reads.
    #
    # DUAL ROUTE, exactly as the Claude lane proves it: a refused crop retries the full frame, so
    # this can only ever add a read, never lose one. The retry is gated on g5's own budget — the
    # Claude lane's v1845 lesson was that a retry which never re-asks the cap turns one budget check
    # into a licence for two reads on every refused page.
    import chronicle_crop as _cc
    _read_path, _framing = _cc.list_crop(path)
    raw = g5_vision_read(_read_path,
                         prompt=CHRONICLE_VISION_PROMPT.format(path=_read_path, ledger=ledger),
                         force=force)
    if _read_path != path and _cc.crop_answer_refused(raw):
        _full = g5_vision_read(path, prompt=CHRONICLE_VISION_PROMPT.format(path=path, ledger=ledger),
                               force=force)
        if not _cc.crop_answer_refused(_full):
            raw = _full
            _framing = _cc.FULL
    # v1519 — ONE normalizer, shared with the Claude lane (chronicle_retro.normalize_page). If each
    # lane shaped its own answer, "witness: agree" would mean two different things depending on who
    # said it — and cross-lane agreement is only evidence when both lanes answer in the same units.
    try:
        import chronicle_retro as _cr
    except Exception:
        return None
    return _cr.normalize_page(raw, kind, "grok", framing=_framing)


# ── subscription auth (NOT API keys) ───────────────────────────────────────────
_GROK_CANDIDATES = (
    "~/.grok/bin/grok",            # the official installer's home — where Konyo's actually is
    "~/.local/bin/grok",
    "/opt/homebrew/bin/grok",
    "/usr/local/bin/grok",
)


def _grok_bin():
    """v1501 — FIND IT THE WAY WE FIND CLAUDE. `shutil.which` searches the PATH OF THIS PROCESS, and
    the console runs as a GUI app under launchd/pywebview, whose PATH is the bare
    /usr/bin:/bin:/usr/sbin:/sbin — it does NOT inherit the shell PATH where ~/.grok/bin lives.

    Measured on Konyo's Mac: `which grok` in his shell resolves /Users/konyo/.grok/bin/grok, while
    the console reported cliInstalled=False. He had set the switch to PRIMARY — his mandated vision
    lane — and it had been silently dark ever since, with calls=0, errors=0 and last_error=None,
    because a lane that never ATTEMPTS never records a failure.

    control_app.py already carries `_find_claude_bin` for exactly this reason on Windows. The third
    eye gets the same courtesy: env override first, then PATH, then the known install locations."""
    for env in ("G5_GROK_BIN", "TV_GROK_BIN"):
        v = (os.environ.get(env) or "").strip()
        if v and os.path.isfile(os.path.expanduser(v)):
            return os.path.expanduser(v)
    hit = shutil.which("grok")
    if hit and os.path.isfile(hit):
        return hit
    for cand in _GROK_CANDIDATES:
        p = os.path.expanduser(cand)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return ""


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
        _STATS["last_error"] = None; _STATS["last_error_ts"] = None  # not an error
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


# v1381.2 — no-spam login: one in-flight process; UI only prompts when needsLogin
_LOGIN_LOCK = threading.Lock()
_LOGIN_PROC = None  # type: ignore
_LOGIN_STARTED_AT = 0.0


def start_login(*, prefer_oauth=True):
    """v1381.2 — launch `grok login` so the user can authorize SuperGrok in the browser.

    Pure side-effect helper for the console ⚡ Authorize button. Does NOT spam:
    if already logged in, returns ok without spawning; if a login is already in
    flight, returns the existing status. Never uses API keys.
    """
    global _LOGIN_PROC, _LOGIN_STARTED_AT
    bin_path = _grok_bin()
    if not bin_path:
        return {
            "ok": False, "started": False, "reason": "no-cli",
            "msg": "grok CLI not installed — re-run the TV installer or: "
                   "irm https://x.ai/cli/install.ps1 | iex   (Windows) / "
                   "curl -fsSL https://x.ai/cli/install.sh | bash   (Mac)",
            "hasSubscription": False, "cliInstalled": False,
        }
    if _subscription_logged_in():
        return {
            "ok": True, "started": False, "reason": "already-authorized",
            "msg": "Grok already authorized on this PC — no re-login needed",
            "hasSubscription": True, "cliInstalled": True,
        }
    with _LOGIN_LOCK:
        # still running?
        if _LOGIN_PROC is not None:
            try:
                if _LOGIN_PROC.poll() is None:
                    return {
                        "ok": True, "started": False, "reason": "in-flight",
                        "msg": "login already open — finish the browser authorize, then return here",
                        "hasSubscription": False, "cliInstalled": True,
                        "pid": getattr(_LOGIN_PROC, "pid", None),
                    }
            except Exception:
                pass
            _LOGIN_PROC = None
        env, _stripped = _grok_env()
        args = [bin_path, "login"]
        if prefer_oauth:
            args.append("--oauth")
        try:
            # Detached-ish: open a visible console on Windows so the user sees the URL;
            # on Mac/Linux inherit is fine (browser still pops).
            creation = 0
            if os.name == "nt":
                creation = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            _LOGIN_PROC = subprocess.Popen(
                args, env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=creation if creation else 0,
                start_new_session=(os.name != "nt"),
            )
            _LOGIN_STARTED_AT = time.time()
            _STATS["last"] = "login-started"
            _STATS["last_error"] = None; _STATS["last_error_ts"] = None
            return {
                "ok": True, "started": True, "reason": "spawned",
                "msg": "browser authorize opened — complete SuperGrok login, then PRIMARY stays green",
                "hasSubscription": False, "cliInstalled": True,
                "pid": getattr(_LOGIN_PROC, "pid", None),
            }
        except Exception as e:
            _LOGIN_PROC = None
            _STATS["last_error_ts"] = int(time.time() * 1000)
            _STATS["last_error"] = f"login spawn failed: {e}"
            return {
                "ok": False, "started": False, "reason": "spawn-failed",
                "msg": str(e)[:200],
                "hasSubscription": False, "cliInstalled": True,
            }


def login_inflight():
    """True if a grok login process is still running."""
    global _LOGIN_PROC
    if _LOGIN_PROC is None:
        return False
    try:
        if _LOGIN_PROC.poll() is None:
            return True
    except Exception:
        pass
    _LOGIN_PROC = None
    return False


def status():
    hourly, daily = _budget_counts()
    cli = bool(_grok_bin())
    authorized = _subscription_logged_in()
    can_run = bool(cli and authorized)
    inflight = login_inflight()
    return {
        "present": True,
        "feature": "g5_grok_eyes",
        "lane": "subscription-cli",  # NOT api.x.ai
        "power": "grok -p + SuperGrok OIDC login (no API keys)",
        "switch": mode_intent(),
        "mode": mode(),
        # v1501 — SAY IT WHEN INTENT AND REALITY DISAGREE. Konyo had this switched to PRIMARY while
        # the effective mode sat at off, and nothing said so: a lane that never attempts never
        # records an error, so calls/errors/last_error all read clean while the eye was dark. The
        # switch is a statement of intent; when the system cannot honour it, that is the headline.
        # v1767 — AND THE THIRD STATE: STARTS FINE, FAILS EVERY CALL. The two above are structural
        # (no binary, not signed in) and both resolve mode() to "off". A lane that is installed,
        # authorised and answering every request with "402 Payment Required" resolves to primary and
        # reported intentBlocked FALSE with an empty blockedWhy — measured live on his console at
        # 165 calls, 107 errors, last_error the 402. So the honesty field invented precisely to
        # publish intent-vs-reality said nothing was wrong while the eye had been dark for a hundred
        # calls. The v1501 note above describes the mirror ("a lane that never attempts never records
        # an error"); this is the case where it DOES attempt, DOES record, and the headline still
        # reads clean. A hard stop is not a flaky call: it is stated by the far end and it will not
        # clear by retrying, so it belongs in the headline exactly like the other two.
        "intentBlocked": bool(mode_intent() != "off" and (mode() == "off" or _hard_stop_why())),
        "blockedWhy": ("" if mode_intent() == "off"
                       else (_hard_stop_why() if mode() != "off"
                             else ("the grok CLI is not installed where this app can see it"
                             if not _grok_bin() else
                             ("not signed in to SuperGrok — click Authorize" if not _subscription_logged_in()
                              else "the lane is switched on but the app could not start it")))),
        "on": is_on(),
        "hasKey": can_run,       # UI compat: means "can run", not API key
        "hasSubscription": can_run,
        "cliInstalled": cli,
        "authorized": authorized,
        "needsInstall": not cli,
        "needsLogin": bool(cli and not authorized),
        "loginInflight": inflight,
        "grokBin": _grok_bin() or None,
        "model": "subscription-cli",
        "budget": {
            "hourlyUsed": hourly, "hourlyMax": _HOURLY_MAX,
            "dailyUsed": daily, "dailyMax": _DAILY_MAX,
        },
        "stats": stats_view(),
        "sidecar": {
            "hint": "python3 tv/g5_sidecar/server.py  (uses same subscription CLI)",
        },
    }


# ── budget (local counters, like intake_local) ────────────────────────────────
# v1698 — TWO WRITERS, TWO CLOCKS, ONE FILE. g5_subscription_budget.json is written by BOTH this
# module (time.time() -> SECONDS) and tv/intake_grok_sub.mjs (Date.now() -> MILLISECONDS), and
# neither knew about the other. Both halves were broken, in opposite directions:
#
#   Python reading a Node row:  now(1786390330) - 1786385809525 = -1,784,599,419,194 -- hugely
#     NEGATIVE, so `< 86400` is ALWAYS true. Every ms row sits ~1.78 MILLION MILLION seconds in the
#     "future" and can never age out. hourlyUsed only ever CLIMBS.
#   Node reading a Python row:  now_ms - t ~= 20,655 days -- outside 24h, so DROPPED. Node deletes
#     every row Python writes and saves the pruned list back.
#
# At 30 accumulated rows _budget_ok() returns False forever and the second eye reports
# "grok-subscription hourly cap (30/30)" while the real call rate is ZERO. Measured 2026-08-10:
# 9 of 30, i.e. twenty-one Node calls from switching itself off. That is the exact failure this
# lane exists to prevent -- the eye goes dark behind a LEGITIMATE-LOOKING reason, same shape as
# v1501. The tell was on screen and walked past: hourlyUsed 9 alongside stats.calls 0.
#
# THE FIX IS ONE UNIT, DECLARED ONCE, NORMALISED ON READ -- never a conversion at a single call
# site, which is just the second writer again. Canonical is MILLISECONDS: his file already holds
# ms rows, so nothing has to be migrated and no real call is lost. A row in the other unit is
# still understood rather than dropped, because a budget that silently forgets calls is as wrong
# as one that never forgets them.
_MS_FLOOR = 1e11   # 1e11 ms = 1973; 1e11 s = year 5138. Nothing real lands between the two.


def _as_ms(t):
    """One timestamp -> milliseconds, whichever unit it was written in."""
    v = float(t)
    return v * 1000.0 if v < _MS_FLOOR else v


def _budget_path():
    """v1698 — overridable so a guard can run without touching his live budget file.
    Read per call, not frozen at import, so a test can point it somewhere after importing."""
    return os.environ.get("G5_BUDGET_PATH") or _BUDGET_PATH


def _budget_load():
    try:
        p = _budget_path()
        if not os.path.isfile(p):
            return {"calls": []}
        return json.loads(open(p, encoding="utf-8").read()) or {"calls": []}
    except Exception:
        return {"calls": []}


def _budget_save(state):
    try:
        with open(_budget_path(), "w", encoding="utf-8") as fh:
            json.dump(state, fh)
    except Exception:
        pass


# ── stats, SHARED ACROSS PROCESSES ────────────────────────────────────────────
# v1711 — stats.calls WAS PERMANENTLY 0 AND THE FILE ALREADY SAID SO.
# The note at the budget block above records the tell verbatim: "hourlyUsed 9 alongside
# stats.calls 0." Two counters over the same events disagreed, one was believed, and the
# contradiction sat in a comment instead of being the finding.
#
# The cause is a process boundary. The eye is CALLED from the agent (tv_diablo.py:4855),
# which control_app.py:1858 launches as a separate `subprocess.Popen`. Every _STATS["calls"] += 1
# lands in the AGENT's memory. /api/g5_status is served by CONTROL_APP, which imported its own
# copy of this module and reads its own dict — one that nothing ever increments. So the panel was
# not reporting a quiet eye; it was reporting a different process's blank counter.
#
# hourlyUsed was right for exactly one reason: the budget goes through a FILE. So the stats do too.
# Same shape, same override-per-call env hook, same swallow-on-failure — a stats write must never
# be able to break a vision call.
def _g5_stats_root():
    """v1869 — the same one rule: a fixture's reads are not his G5 statistics.

    v1883 — AND THE FALLBACK MUST APPLY THE RULE, NOT SURRENDER TO HIS TREE. This asked tv_diablo
    for the answer and, on any failure, returned his own directory — and the import CAN fail here,
    because a control app spawned by a harness imports these two modules in an order this one does
    not control. Measured after v1874 with his console down: six harnesses still rewrote his live
    g5_stats.json (test_console_fleet, robot_smoke, test_roundtrip_sim, test_button_matrix,
    test_vault_lane, test_inbox_engine), every one of them with TV_HIST correctly sandboxed.
    An `except: return his_directory` is a fallback that fails toward the thing being protected.
    The rule is six lines; it is inlined rather than surrendered. [[feedback-fixtures-never-touch-live-data]]
    """
    _here = os.path.dirname(os.path.abspath(__file__))
    try:
        import tv_diablo as _tvd
        return _tvd._fixture_root(_here)
    except Exception:
        pass
    hist = os.environ.get("TV_HIST")
    if hist:
        try:
            # v1897 — the SAME comparison tv_diablo makes, and it must stay the same: on Windows a
            # raw startswith on paths of differing case decides a fixture is his real tree.
            import tv_diablo as _tvd2
            if not _tvd2._under(hist, _here):
                return os.path.realpath(hist)
        except Exception:
            try:
                a, b = os.path.normcase(os.path.realpath(hist)), os.path.normcase(os.path.realpath(_here))
                if not (a == b or a.startswith(b + os.sep)):
                    return a
            except Exception:
                pass
    return _here


_STATS_PATH = os.path.join(_g5_stats_root(), "g5_stats.json")
_COUNTERS = ("calls", "ok", "errors", "skipped_budget", "shadow", "primary")


def _stats_path():
    """Overridable per call so a guard never writes his live stats file (mirrors _budget_path)."""
    return os.environ.get("G5_STATS_PATH") or _STATS_PATH


def _stats_load():
    try:
        p = _stats_path()
        if not os.path.isfile(p):
            return {}
        return json.loads(open(p, encoding="utf-8").read()) or {}
    except Exception:
        return {}


def _stats_flush():
    """Publish this process's counters into the shared file, ADDING deltas rather than
    overwriting — control_app and the agent both call the eye, so a last-writer-wins save
    would silently erase the other process's calls (the very defect this replaces)."""
    try:
        with _LOCK:
            base = _stats_load()
            merged = dict(base)
            for k in _COUNTERS:
                merged[k] = int(base.get(k) or 0) + int(_STATS.get(k) or 0)
            for k in ("last", "last_error", "last_error_ts", "lane", "stripped_api_env"):
                if _STATS.get(k) is not None:
                    merged[k] = _STATS[k]
            merged["ts"] = time.time()
            with open(_stats_path(), "w", encoding="utf-8") as fh:
                json.dump(merged, fh)
            for k in _COUNTERS:          # deltas are banked; reset so they cannot double-count
                _STATS[k] = 0
    except Exception:
        pass


_HARD_STOPS = (
    # each pattern is a refusal the FAR END stated; retrying cannot clear any of them
    ("402", "the Grok balance is exhausted — the second eye cannot read until it is topped up"),
    ("payment required", "the Grok balance is exhausted — the second eye cannot read until it is topped up"),
    ("balance exhausted", "the Grok balance is exhausted — the second eye cannot read until it is topped up"),
    ("insufficient", "the Grok account has no credit left for this lane"),
    ("401", "Grok rejected the credentials — sign in again"),
    ("unauthorized", "Grok rejected the credentials — sign in again"),
    ("invalid api key", "Grok rejected the credentials — sign in again"),
)


_LOOK_IT_UP = object()   # "consult the live stats" — distinct from an explicit None meaning "no error"


def _hard_stop_why(last_error=_LOOK_IT_UP):
    """A refusal the far end STATED, in his words rather than the CLI's.

    v1767 — only the LAST call is consulted, deliberately. A tally of historic errors cannot tell a
    lane that failed all morning and recovered from one that is dead right now, and a lane that has
    recovered must stop announcing a blockage. Silence here means the last call did not hard-stop;
    it never means the lane was checked and found healthy, which is what `calls`/`errors` are for.
    """
    try:
        if last_error is _LOOK_IT_UP:
            last_error = (stats_view() or {}).get("last_error")
    except Exception:
        return ""
    blob = str(last_error or "").lower()
    if not blob:
        return ""
    for needle, say in _HARD_STOPS:
        if needle in blob:
            return say
    return ""


def stats_view():
    """What /api/g5_status must show: the shared totals, plus anything this process holds
    that has not been flushed yet."""
    base = _stats_load()
    out = dict(_STATS)
    for k in _COUNTERS:
        out[k] = int(base.get(k) or 0) + int(_STATS.get(k) or 0)
    for k in ("last", "last_error"):
        if out.get(k) is None and base.get(k) is not None:
            out[k] = base[k]
    return out


def _budget_counts(now=None):
    now_ms = _as_ms(now) if now is not None else time.time() * 1000.0
    state = _budget_load()
    calls = [_as_ms(t) for t in (state.get("calls") or [])]
    calls = [t for t in calls if 0 <= now_ms - t < 86400.0 * 1000.0]
    hour = [t for t in calls if now_ms - t < 3600.0 * 1000.0]
    with _LOCK:
        _CALL_LOG[:] = calls
    return len(hour), len(calls)


def _budget_ok():
    if _HOURLY_MAX <= 0 or _DAILY_MAX <= 0:
        return False
    hourly, daily = _budget_counts()
    return hourly < _HOURLY_MAX and daily < _DAILY_MAX


def _budget_record():
    # v1698 — writes MILLISECONDS, the one canonical unit both writers now agree on.
    now_ms = time.time() * 1000.0
    state = _budget_load()
    calls = [_as_ms(t) for t in (state.get("calls") or [])]
    calls = [t for t in calls if 0 <= now_ms - t < 86400.0 * 1000.0]
    calls.append(now_ms)
    _budget_save({"calls": calls, "last": now_ms})
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
        # v1711 — this returned None with last_error untouched, so a budget refusal was
        # INDISTINGUISHABLE on the panel from an eye that was simply never asked. "The eye is
        # quiet" and "the eye is rationed" are different facts and he acts on them differently.
        _STATS["skipped_budget"] += 1
        h, d = _budget_counts()          # (this hour, today)
        _STATS["last_error_ts"] = int(time.time() * 1000)
        _STATS["last_error"] = ("budget: %s/%s this hour, %s/%s today — refused, not failed"
                                % (h, _HOURLY_MAX, d, _DAILY_MAX))
        _stats_flush()
        return None

    path = os.path.abspath(str(image_path or ""))
    if not path or not os.path.isfile(path):
        return None

    bin_path = _grok_bin()
    if not bin_path:
        _STATS["last_error_ts"] = int(time.time() * 1000)
        _STATS["last_error"] = "grok CLI not on PATH"
        _stats_flush()
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
        _STATS["last_error_ts"] = int(time.time() * 1000)
        _STATS["last_error"] = f"grok -p timeout {_TIMEOUT_S:.0f}s"
        _stats_flush()
        _cleanup(work)
        return None
    except Exception as e:
        _STATS["errors"] += 1
        _STATS["calls"] += 1
        _STATS["last_error_ts"] = int(time.time() * 1000)
        _STATS["last_error"] = str(e)[:160]
        _stats_flush()
        _cleanup(work)
        return None

    _cleanup(work)
    out = (r.stdout or "").strip()
    _STATS["calls"] += 1
    _STATS["last"] = time.strftime("%Y-%m-%d %H:%M:%S")

    if r.returncode != 0 and not out:
        _STATS["errors"] += 1
        err = (r.stderr or "")[:200]
        _STATS["last_error_ts"] = int(time.time() * 1000)
        _STATS["last_error"] = f"grok exit {r.returncode}: {err}"
        _stats_flush()
        return None

    parsed = _loose_parse(out)
    if parsed is None:
        _STATS["errors"] += 1
        # v1759 — SAY WHAT THE CLI ACTUALLY SAID. The grok CLI reports an API refusal in its OUTPUT
        # and still exits 0, so the returncode check above never fires and this branch was the one
        # that ran — recording "no-json from grok -p", which points at a parser. Measured on his
        # machine while diagnosing a permanently silent second eye:
        #
        #     Internal error: {"message": "API error (status 402 Payment Required):
        #                      Grok Build usage balance exhausted", "http_status": 402}
        #
        # Every guard above was green (is_on, has_subscription, budget, binary found), so the lane
        # reported ready and answered nothing, and the one field that could have said why said
        # "no-json". A reader chasing that goes to the parser; the actual fix is a billing page.
        # The real message is now carried through, and an HTTP status is named explicitly.
        _err = (out or (r.stderr or ""))[:400].replace("\n", " ").strip()
        _status = None
        _m = _re.search(r"status (\d{3})", _err) or _re.search(r"http_status\"?\s*:\s*(\d{3})", _err)
        if _m:
            _status = _m.group(1)
        _STATS["last_error_ts"] = int(time.time() * 1000)
        _STATS["last_error"] = (("grok HTTP %s — %s" % (_status, _err[:220])) if _status
                                else ("grok gave no JSON — said: %s" % (_err[:220] or "(nothing)")))
        _stats_flush()
        return None

    _budget_record()
    _STATS["ok"] += 1
    m = mode() if not force else "force"
    if m == "shadow":
        _STATS["shadow"] += 1
    elif m == "primary":
        _STATS["primary"] += 1
    _stats_flush()
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
