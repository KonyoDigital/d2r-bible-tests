#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# 📺 TV DIABLO — Autopilot scanner (v740)
#
#   You play Diablo II. This watches the screen, reads the items you're looking
#   at, and feeds the tally to the Farming Bible's 📺 panel — automatically.
#
#   READ-ONLY BY CONSTRUCTION (the compliance doctrine):
#     · launched by YOU, separately, in a terminal — never bundled into the game
#     · it only takes screenshots of what is already on your screen
#     · it NEVER touches the game process: no memory reading, no injection,
#       no input automation, no overlay. Pure screen capture + external notes.
#     (Same class as manually screenshotting your stash — just automated.)
#
#   SUBSCRIPTION, NOT API KEYS: vision reads run through the Claude Code CLI
#   (`claude -p`), billed to YOUR Claude subscription. Your cousin runs the
#   same file on Windows with HIS Claude Code login — his reads, his plan.
#
#   Zero dependencies — python3 stdlib only.
#
#   Run:            python3 tv/tv_diablo.py
#   Windows:        run tv/capture_win.ps1 in one terminal (frames), then
#                   python3 tv/tv_diablo.py --watch  in another (reads+bridge)
#   Then in the bible: ⚡ session → 📺 TV DIABLO → flip the switch.
#
#   ONE AI READER (v846 TESLA DRIVE): settle freeze → dual-lane (OCR flash + Claude deep).
#   No scout secondary. Film is high-FPS HD; intel is snappy settle + one deep at a time.
#   Claude deep is multi-second by nature — OCR chips + smooth film are the "live drive" feel.
# ═══════════════════════════════════════════════════════════════════════════════
import json, os, subprocess, sys, threading, time, hashlib, signal, heapq
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "v877"   # READER POOL — up to POOL_N concurrent vision readers + ordered apply
HERE   = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.environ.get("TV_FRAMES_DIR") or os.path.join(HERE, "frames")   # v752 — replay feeds its own watch dir
STATE  = os.path.join(HERE, "state.json")
PORT   = int(os.environ.get("TV_PORT", "17771"))   # v711 — overridable (tests · port conflicts)
# v780 — one ON cycle = one theatre session. Every journal row carries this id so SIM/theatre
# never glues multiple restarts into one mega-run (the 10min gap alone was too soft).
SESSION_ID = ""
# v846 — TESLA DRIVE pacing (Konyo: ultra smooth / self-driving feel)
MIN_GAP_S    = float(os.environ.get("TV_MIN_GAP", "2.0") or 2.0)       # was 4 — cruise re-reads sooner
HEARTBEAT_S = max(1.0, min(20.0, float(os.environ.get("TV_HEARTBEAT", "2") or 2)))   # v862 (Konyo: 'every 2 secs') — 2s default heartbeat
PRIORITY_GAP_S = float(os.environ.get("TV_PRIORITY_GAP", "0.55") or 0.55)  # was 1.2 — pile snaps hard
# v726 — no empty-gameplay cool (blocked pile stops). Thrash = same-view + gap only.
SESSION_CAP  = 240
POLL_S       = float(os.environ.get("TV_POLL", "0.10") or 0.10)         # was 0.18 — tighter settle clock
WATCH_MODE   = "--watch" in sys.argv
# v727 — motion “wow” threshold: walking/panel open swings past this
MOTION_PEAK  = 0.10   # was 0.12 — slightly more sensitive to walk/stop
SETTLE       = 0.03
# v846 film: target FPS (default 15) · HD+ JPEG (up to 2560px) — console stage + footage
_FILM_FPS = max(5, min(30, int(float(os.environ.get("TV_FILM_FPS", "15") or 15))))
FILM_INTERVAL_S = 1.0 / float(_FILM_FPS)
FILM_MAX_PX = max(1280, min(3840, int(os.environ.get("TV_FILM_MAX_PX", "2048") or 2048)))   # v877 — 2560 burned 4.4GB/hr of footage
FILM_JPEG_Q = max(55, min(95, int(os.environ.get("TV_FILM_Q", "82") or 82)))
_FILM_TIMES = deque(maxlen=64)   # v877 — bounded ring; the old plain list grew ~432k floats overnight

# v710.1 — SCENARIO ENGINE (Konyo: "once those moments are captured it can automatically be
# coded to flag farming when not in town — the corner always shows where we are on the map").
# Every read extracts WHERE (area = the zone name on the HUD/automap corner) and WHICH MOMENT
# (scene: town/loot/inventory/stash/gameplay) alongside the item names.
# Prompt truths calibrated on Konyo's REAL session videos (2026-07-15, town + Cold Plains runs):
#  · top-right block = "Game: <name>" then the CURRENT AREA, then purple lines = today's terror
#    zones — persistent during play, hidden when a right-side panel (inventory) covers it
#  · zone transitions flash a red "ENTERING <ZONE>" banner
#  · panel grids show item ICONS with no text — names ONLY come from hover tooltips (first line
#    = name), ground labels (loot key held), waypoint labels ("<Zone> Waypoint"), and the
#    DETACHED top-left hover label (ground item hovered while a panel is open)
# v730 — shorter prompt (run #4: inventory 25.8s was too hot; less prose → faster JSON)
# v734 — stashTab when scene=stash (RotW left tabs: Personal·Shared·Gems·Materials·Runes)
PROMPT_VER = "p830"   # v832 — bump whenever READ_PROMPT changes; every read journals which prompt read it
_LAST_RAW = ""        # v832 (SIMULATION_SPEC) — the model's literal words for the read in flight
READ_PROMPT = (
    "Image {path} = Diablo II Resurrected (RoW). Reply with STRICT JSON only, no markdown, no prose:\n"
    "{{\"area\":\"\",\"tz\":[],\"scene\":\"gameplay\",\"stashTab\":\"\",\"names\":[],\"names_loc\":{{}},\"discovered\":[],\"conf\":0.0}}\n"
    "scene = one of: town | stash | inventory | loot | gameplay | transition.\n"
    "transition = fullscreen loading/portal art: the burning fire portal, act loading screen, or a "
    "dark frame with NO HUD (no belt/orbs/automap). The player is entering a portal, waypoint, or a "
    "new game — names/area are expected empty.\n"
    "area = zone name from top-right Game block / ENTERING banner / automap, else \"\".\n"
    "tz = purple terror-zone lines in that block, else [].\n"
    "stashTab = ONLY when scene=stash: which LEFT stash tab is active — "
    "personal | shared | gems | materials | runes | \"\" if unknown. "
    "Stash tell: left panel tabs + inventory often open on the right.\n"
    "names = READABLE text labels only (tooltips first line, ground loot labels, open inventory/stash "
    "name text). Never invent from icons alone. Never complete partial names.\n"
    "names_loc = for EVERY name: WHERE its tooltip/label lives — one of "
    "equipped | inventory | stash | floor. Tells: tooltip says 'to Unequip' or hovers the character "
    "equipment doll = equipped (the player's WORN gear, not loot). Tooltip anchored over the RIGHT "
    "inventory grid = inventory (charms saying 'Keep in Inventory' are inventory). Tooltip over the "
    "LEFT stash panel grid = stash. Ground label / detached top-left label = floor. When stash+inventory "
    "are BOTH open, judge by WHICH panel the tooltip covers — never assume stash.\n"
    "Never put merc/NPC/player names, HP bars, waypoint labels, or chat into names.\n"
    "discovered = ITEM names from chat DISCOVERY broadcasts only (lines like "
    "'<player> has found <item>' / 'has discovered'). Just the item names; [] if none. "
    "Normal chat/trade text is NEVER a discovery.\n"
    "inventory/stash: also list anchors if visible — Horadric Cube, Tome of Town Portal, Tome of Identify.\n"
    "conf = 0.0-1.0 confidence. Be fast and precise."
)

# v752 — persistent session journal (tv/sessions.jsonl, gitignored): every published read
# appended as one JSON line. This is what `tvd replay` re-runs — real frames, real reads.
JOURNAL = os.environ.get("TV_SESSIONS") or os.path.join(HERE, "sessions.jsonl")   # v877 — CI harness override
_JOURNAL_WARNED = False
def _journal(rec):
    global _JOURNAL_WARNED
    if os.environ.get("TV_NO_JOURNAL"):   # v753 — a REPLAY is a re-broadcast, never a new session
        return
    try:
        if isinstance(rec, dict) and SESSION_ID and not rec.get("sessionId"):
            rec = dict(rec)
            rec["sessionId"] = SESSION_ID
        need_nl = False
        try:
            if os.path.getsize(JOURNAL) > 0:
                with open(JOURNAL, "rb") as f:
                    f.seek(-1, 2); need_nl = f.read(1) != b"\n"
        except Exception:
            pass
        with open(JOURNAL, "a", encoding="utf-8") as f:
            if need_nl: f.write("\n")
            f.write(json.dumps(rec) + "\n")
            f.flush(); os.fsync(f.fileno())   # v779 (Grok R5/R7) — durable append: a crash mid-write can't erase the night
        try:
            _fid = isinstance(rec, dict) and rec.get("frameId")
            if _fid and isinstance(_JFID_STATE.get("ids"), set) and _JFID_STATE.get("path") == JOURNAL:
                _JFID_STATE["ids"].add(str(_fid) + ".jpg")   # v877 — grows AT APPEND; suffix matches the shield
        except Exception:
            pass
        if os.path.getsize(JOURNAL) > 4_000_000:   # ~4MB → ROTATE (never half-truncate the live file)
            # v811 (Grok R8 #6 + sleeper) — GENERATIONS, not one slot: .1 is newest rotation,
            # older shift up to .5 (~20MB ≈ months). A second heavy night can no longer erase
            # the first with zero lamp.
            _root, _ext = os.path.splitext(JOURNAL)
            for _g in range(4, 0, -1):
                _src = _root + ".%d" % _g + _ext
                if os.path.exists(_src):
                    os.replace(_src, _root + ".%d" % (_g + 1) + _ext)
            os.replace(JOURNAL, _root + ".1" + _ext)
            try: ev("cap", "journal rotated — generation ring .1-.5 (~20MB of nights kept)")
            except Exception: pass
    except Exception as e:
        if not _JOURNAL_WARNED:
            _JOURNAL_WARNED = True
            try: ev("cap", f"journal write failed ({e}) — replay of this session won't be available")
            except Exception: pass

_state_lock = threading.Lock()
def _load():
    try:
        with open(STATE, encoding="utf-8") as f: return json.load(f)
    except Exception:
        return {"online": True, "startedAt": int(time.time()*1000), "reads": [], "readCount": 0}

def _save(st):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(st, f)
    os.replace(tmp, STATE)

_BEAT = {"ts": 0, "phase": "idle", "motion": 0.0}
_EVENTS = []
# v727 Autopilot HUD — continuous driver state (Tesla stack, screen edition)
_AP = {
    "mode": "boot",          # boot|drive|hunt|settle|read|load
    "interest": 0.0,         # 0–1 how badly we want a vision fire
    "peak": 0.0,             # recent max motion (hunting for a stop)
    "priority": False,       # next settle uses short gap
    "emptyStreak": 0,
    "namedStreak": 0,
    "lastNamed": "",
    "gap": MIN_GAP_S,
    "ver": VERSION,
}
def ev(kind, text):
    """v710.6 — the BRAIN LOG: the scanner's real decisions, streamed to the board
    (in-memory ring like the beat; /state merges it — no disk churn)."""
    _EVENTS.append({"ts": int(time.time()*1000), "k": kind, "t": str(text)[:120]})
    del _EVENTS[:-60]
def beat(phase, motion):
    """v710.4 — the LIVE pulse, IN MEMORY only (Grok audit: rewriting state.json twice a
    second thrashed disk + the lock). /state merges it at request time; reads still persist."""
    _BEAT["ts"] = int(time.time()*1000); _BEAT["phase"] = phase; _BEAT["motion"] = round(float(motion), 3)
    _AP["mode"] = {"loading": "load", "watching": "drive", "reading": "read"}.get(phase, phase)

def ap_interest(peak, stable_ticks, priority, empty_streak, named_recent, parts=None):
    """0–1 score: hard motion → stop is the 'money moment' (pile / panel).
    v833 (Grok addendum A2.1) — pass parts={} to receive the DECOMPOSITION: almost every real
    fire scores 1.0, so forensics need the inputs that built it, not the flat number."""
    s = 0.15
    p = {"base": 0.15, "peak": 0.0, "priority": 0.0, "named": 0.0, "empty": 0.0, "stable": 0.0}
    if peak >= MOTION_PEAK: s += 0.45; p["peak"] = 0.45
    elif peak >= 0.06: s += 0.2; p["peak"] = 0.2
    if priority: s += 0.25; p["priority"] = 0.25
    if named_recent: s += 0.1; p["named"] = 0.1
    if empty_streak >= 3: s -= 0.08; p["empty"] = -0.08   # slight downrank only — never blocks
    if stable_ticks >= 1: s += 0.1; p["stable"] = 0.1
    if isinstance(parts, dict):
        parts.update(p)
    return max(0.0, min(1.0, s))

def _film_fps_now():
    """Rolling film FPS over the last ~1.5s of successful eye frames."""
    try:
        now = time.time()
        recent = [t for t in _FILM_TIMES if now - t <= 1.5]   # v877 — deque, no destructive prune
        n = len(recent)
        if n < 2:
            return 0.0
        span = max(0.001, recent[-1] - recent[0])
        return round((n - 1) / span, 1)
    except Exception:
        return 0.0


def _health(st):
    """v789 (Grok R4 #1) — one small truth object for the fault lamp. A 2-hour farm used to
    die quietly (vision stall, game quit, capture death) while the lamp said ON AIR."""
    now = time.time()
    # v877 (army audit #5) — footage fps from the in-memory archive deque; the old
    # os.listdir over ~30k files ran 4×/s from the board poll.
    _foot_fps = _foot_fps_now()
    # v863 (READER POOL) — busy lamp = oldest in-flight reader's age; expose pool depth.
    _pool_pin, _pool_oldest = 0, 0
    try:
        with _pool_lock:
            _pool_pin = len(_in_flight)
            if _in_flight:
                _pool_oldest = min(int(j.get("startedAt") or 0) for j in _in_flight.values())
    except Exception:
        pass
    try:
        import shutil as _shf
        _free_gb = round(_shf.disk_usage(FRAMES).free / 1e9, 1)
    except Exception:
        _free_gb = None
    h = {"eyeAgeMs": _eye_age_ms(), "captureMode": (_CAP_TARGET or {}).get("mode", ""),
         "freeGB": _free_gb, "minFreeGB": MIN_FREE_GB,   # v872.1 — disk emergency is LOUD, never silent
         "footageFps": _foot_fps,   # v861 — the archive floor, alarmed by the UI
         "visionBusyMs": (max(0, int(now * 1000) - _pool_oldest) if (_pool_pin and _pool_oldest) else 0),
         "poolInFlight": _pool_pin, "poolN": POOL_N,
         "poolWarm": sum(1 for _w9 in _WORKERS if getattr(_w9, "warm_ok", False)),   # v870
         "sessionMs": 0, "lastReadAgeMs": -1, "named": 0, "vaulted": 0,
         # v846 — Tesla-drive dashboard truth
         "filmFps": _film_fps_now(), "filmTargetFps": _FILM_FPS,
         "filmLane": globals().get("_FILM_LANE", ""), "filmCapMs": globals().get("_FILM_CAP_MS"),   # v867
         "filmMaxPx": FILM_MAX_PX, "pollMs": int(POLL_S * 1000),
         "gapCruiseS": MIN_GAP_S, "gapPriorityS": PRIORITY_GAP_S}
    try:
        if st.get("startedAt"):
            h["sessionMs"] = max(0, int(now * 1000) - int(st["startedAt"]))
        reads = st.get("reads") or []
        if reads:
            h["lastReadAgeMs"] = max(0, int(now * 1000) - int(reads[-1].get("ts") or 0))
            h["named"] = sum(1 for r in reads if r.get("names"))
            h["vaulted"] = sum(len(r.get("vault_names") or []) for r in reads)
    except Exception:
        pass
    return h


def _eye_age_ms():
    """v785 — how old is the film frame? -1 = no eye at all. The stage uses this to DROP
    film-on instead of claiming LIVE on a dead frame (round-2 sleeper: eye.jpg had no
    lifecycle discipline — it outlived sessions and froze silently when capture died)."""
    try:
        eye = os.path.join(FRAMES, "eye.jpg")
        if not os.path.isfile(eye):
            return -1
        return max(0, int((time.time() - os.path.getmtime(eye)) * 1000))
    except Exception:
        return -1


def _eye_clear():
    """v785 — a session's film dies with the session; next ON never flashes yesterday."""
    try:
        eye = os.path.join(FRAMES, "eye.jpg")
        if os.path.isfile(eye):
            os.remove(eye)
    except Exception:
        pass


def bridge():
    """localhost bridge the bible polls. GET /state → JSON. CORS: any origin may READ."""
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _hdr(self, code=200, ctype="application/json"):
            self.send_response(code)
            self.send_header("content-type", ctype)
            self.send_header("access-control-allow-origin", "*")
            self.send_header("cache-control", "no-store")
            self.end_headers()
        def do_GET(self):
            from urllib.parse import urlparse, parse_qs
            if self.path.startswith("/state"):
                # v770 (Grok R4 perf) — ?since=<ts> returns a THIN delta: full reads ring only
                # when asked from cold; 4 polls/sec no longer parse 200 rich reads every tick.
                _q = parse_qs(urlparse(self.path).query or "")
                _since = 0
                try: _since = int((_q.get("since") or ["0"])[0])
                except Exception: _since = 0
                with _state_lock:
                    st = _load(); st["online"] = True; st["now"] = int(time.time()*1000)
                    st["beat"] = dict(_BEAT); st["events"] = list(_EVENTS); st["ap"] = dict(_AP)
                    st["stopping"] = _STOPPING   # v777.2 — 1-1 sync: the board drops the INSTANT the farewell begins
                    st["captureTarget"] = dict(_CAP_TARGET)  # v772 — window pin (CrossOver/D2R) or full
                    st["eyeAgeMs"] = _eye_age_ms()   # v785 — film honesty: stage drops LIVE when this goes stale
                    st["health"] = _health(st)   # v789 — fault-lamp truth (Grok R4 #1)
                    st["sessionId"] = SESSION_ID
                if _since:
                    st["reads"] = [r for r in (st.get("reads") or []) if (r.get("ts") or 0) > _since]
                    st.pop("seen", None); st.pop("farmed", None)
                self._hdr(); self.wfile.write(json.dumps(st).encode())
            elif self.path.startswith("/ping"):
                try:
                    self._hdr(); self.wfile.write(b'{"ok":true,"tv":"diablo"}')
                except (BrokenPipeError, ConnectionResetError):
                    pass
            elif self.path.startswith("/shutdown"):
                # v847 — control OFF/STOP asks politely: save session, optional farewell, exit.
                # ?farewell=1 (STOP) · ?farewell=0 (OFF soft cut — still seals the reel)
                _q = parse_qs(urlparse(self.path).query or "")
                fare = (_q.get("farewell") or ["1"])[0] not in ("0", "false", "no")
                reason = (_q.get("reason") or ["stop"])[0][:40]
                try:
                    self._hdr()
                    self.wfile.write(json.dumps({
                        "ok": True, "msg": "shutdown accepted",
                        "farewell": fare, "sessionId": SESSION_ID,
                    }).encode())
                except Exception:
                    pass
                def _go():
                    try:
                        close_session(reason=reason, farewell=fare)
                    except Exception:
                        os._exit(0)
                threading.Thread(target=_go, daemon=True, name="tv-shutdown").start()
            elif self.path.startswith("/frame"):
                # v724 — last vision JPEG · v735 — ?id=N_ts for per-read hist archive (1920 eye)
                # v779 — bare /frame prefers the LIVE eye preview (eye.jpg) so fingerprint-skip
                # never freezes the film on a stale desktop read.jpg.
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query or "")
                fid = (qs.get("id") or qs.get("frame") or [None])[0]
                if fid:
                    # only allow simple ids: digits_digits (no path traversal)
                    safe = str(fid).strip()
                    if not all(c.isdigit() or c == "_" for c in safe) or ".." in safe or "/" in safe:
                        self._hdr(400); self.wfile.write(b'{"error":"bad frame id"}'); return
                    jp = os.path.join(FRAMES, "hist", safe + ".jpg")
                else:
                    eye = os.path.join(FRAMES, "eye.jpg")
                    read = os.path.join(FRAMES, "read.jpg")
                    want = (qs.get("which") or [""])[0].strip().lower()
                    if want == "read":
                        jp = read
                    elif want == "eye":
                        jp = eye
                    elif os.path.isfile(eye) and (
                        (not os.path.isfile(read))
                        or os.path.getmtime(eye) >= os.path.getmtime(read)
                    ):
                        jp = eye
                    else:
                        jp = read
                if os.path.isfile(jp):
                    try:
                        with open(jp, "rb") as f: data = f.read()
                        self.send_response(200)
                        self.send_header("content-type", "image/jpeg")
                        self.send_header("access-control-allow-origin", "*")
                        self.send_header("cache-control", "no-store")
                        self.send_header("content-length", str(len(data)))
                        self.end_headers()
                        self.wfile.write(data)
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                    except Exception:
                        try:
                            self._hdr(500); self.wfile.write(b'{"error":"frame read failed"}')
                        except Exception:
                            pass
                else:
                    self._hdr(404); self.wfile.write(b'{"error":"no frame yet"}')
            else:
                self._hdr(404); self.wfile.write(b'{"error":"not found"}')
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    except OSError as e:
        print(f"⛔ cannot bind 127.0.0.1:{PORT} — another TV DIABLO / simulate.py is already running. Ctrl-C it first (or TV_PORT={PORT+1}).\n   {e}")
        sys.exit(2)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

# ── v772.1 / v843 — capture target ───────────────────────────────────────────
# Konyo Mac play path (HARDCODED — agents must never invent another):
#   Desktop/CrossOver_patched.app → bottle "Battle.net Desktop App" → Battle.net
#   tile → Diablo II Resurrected Play. Bottle lives at ~/CXPBottles/…
# TV_CAPTURE=full|auto|window — default AUTO: pin D2R.exe game window only.
# NEVER pin: CrossOver Home UI, Battle.net lobby shell, browsers, TV DIABLO UI.
# TV_WINDOW_MATCH=extra,comma,tokens  (only used when window/auto)
_CAP_TARGET = {"mode": "full", "label": "full screen", "wid": None}


# Owner / title tokens — game process first. Bare "wine" alone is too broad.
_PICK_WHY = ""   # v779-pre diag — why the last pick returned None
_CAP_WHY = ""
_LAST_GOOD_WIN = None   # v779 — the pin survives flaky window listings
_D2R_OWNER_HINTS = (
    "d2r.exe", "d2r", "diablo",
    # host apps only as last-resort match tokens (scoring still rejects bare Home)
    "crossover", "cross over", "cxpatcher",
)
_D2R_TITLE_HINTS = (
    "diablo ii: resurrected", "diablo ii resurrected", "diablo ii", "diablo 2",
    "d2r", "resurrected",
)
# Prefer these process/owner names when several match (game exe first)
_D2R_OWNER_PRIORITY = (
    "d2r.exe", "d2r", "diablo", "wine", "wineloader", "cxstart",
)
# v779.1 (live test): Chrome tab "Konyo's D2R Farming Bible" out-scored D2R.exe because
# title tokens matched. Browsers / editors / our own chrome are NEVER the eye.
_PICK_OWNER_BLOCK = (
    "google chrome", "chrome", "chromium", "safari", "firefox", "arc", "brave browser",
    "microsoft edge", "opera", "vivaldi", "orion", "comet",
    "code", "cursor", "visual studio code", "sublime text", "atom",
    "terminal", "iterm2", "warp", "kitty", "alacritty",
    "slack", "discord", "zoom", "figma", "notion",
    # v843 — CrossOver *app* and Battle.net *shell* are never the film target
    "crossover", "cross over",
    "battle.net.exe", "battle.net", "battle net",
)
_PICK_TITLE_BLOCK = (
    "farming bible", "d2r bible", "tv diablo", "localhost", "127.0.0.1",
    "crossover", "battle.net", "battle net",  # Home / lobby chrome titles
)
# Bare CrossOver shell / launcher Home — never the game (D2R.exe owns the real window).
_PICK_LAUNCHER_TITLES = (
    "crossover", "cross over", "battle.net", "battle net", "home",
)


def _match_tokens():
    extra = [t.strip().lower() for t in (os.environ.get("TV_WINDOW_MATCH") or "").split(",") if t.strip()]
    return list(_D2R_TITLE_HINTS) + list(_D2R_OWNER_HINTS) + extra


def _is_d2r_game_owner(owner_l):
    """True when the process is the real game binary (CrossOver-hosted D2R.exe)."""
    ol = (owner_l or "").strip().lower()
    if not ol:
        return False
    if ol == "d2r.exe" or ol.endswith("/d2r.exe") or ol.endswith("\\d2r.exe"):
        return True
    if ol.endswith(".exe") and ("d2r" in ol or "diablo ii" in ol or "diabloii" in ol):
        return True
    return False


def _is_launcher_shell(owner_l, title_l):
    """v843 — CrossOver Home / Battle.net lobby / thin chrome — NEVER the eye."""
    ol, tl = (owner_l or "").lower(), (title_l or "").lower()
    if ol in ("crossover", "cross over") or ol.startswith("crossover"):
        return True
    if "battle.net" in ol or ol in ("battle.net.exe", "battle net"):
        return True
    if tl in _PICK_LAUNCHER_TITLES:
        return True
    if tl in ("home", "crossover", "battle.net"):
        return True
    return False


def score_d2r_window_candidate(owner, title, width, height, onscreen=True):
    """v843 — pure scorer for unit tests + find_d2r_window_mac.
    Returns int score, or None if this window must never be pinned.
    Absolute winner: D2R.exe with a Diablo/Resurrected title and game-sized bounds."""
    ol = (owner or "").strip().lower()
    tl = (title or "").strip().lower()
    ww, hh = int(width or 0), int(height or 0)
    if ww < 640 or hh < 480:
        return None
    if ol == "python" and "tv diablo" in tl:
        return None
    # v852 (Grok R17 (b) — browsers re-entered the pin race): the game-title override applies
    # ONLY to wine-family owners; Chrome/Safari/editors stay hard-dead no matter the title.
    _wine_owner = any(w in ol for w in ("crossover", "wine", "cxstart", "cxpatcher"))
    _title_is_game = (("resurrected" in tl or "diablo ii" in tl or tl == "d2r")
                      and ww >= 800 and hh >= 500 and _wine_owner)
    if any(b in ol for b in _PICK_OWNER_BLOCK) and not _is_d2r_game_owner(ol):
        # block list includes crossover/battle.net — game exe still allowed
        # v849 — and an unambiguous game TITLE at game size passes even under a wine/CrossOver owner
        if not _title_is_game:
            return None
    if any(b in tl for b in _PICK_TITLE_BLOCK) and not _is_d2r_game_owner(ol):
        return None
    if _is_launcher_shell(ol, tl) and not _is_d2r_game_owner(ol):
        # v849 (audit-core #4) — an unambiguous GAME TITLE on a game-sized window overrides
        # the shell reject: Quartz sometimes reports the game's owner as CrossOver/wine.
        if not _title_is_game:
            return None
    # Must be the game process OR a clear Diablo game title (never lobby alone)
    is_game = _is_d2r_game_owner(ol)
    title_game = ("diablo" in tl or "resurrected" in tl or tl == "d2r"
                  or any(t in tl for t in _D2R_TITLE_HINTS))
    if not is_game and not title_game:
        return None
    # Title-only without game owner: reject if it still looks like a shell —
    # v849: UNLESS the title is unambiguously the game at game size (wine-owner case)
    if not is_game and _is_launcher_shell(ol, tl) and not _title_is_game:
        return None
    score = 0
    if is_game:
        score += 10000          # absolute — always beats CrossOver/Battle.net/Chrome
    if "d2r.exe" in ol:
        score += 2000
    if title_game:
        score += 1500
    if "diablo ii: resurrected" in tl or "diablo ii resurrected" in tl:
        score += 500
    if any(t in ol for t in _D2R_OWNER_PRIORITY):
        score += 30
    if onscreen:
        score += 40
    area = ww * hh
    score += min(area // 100000, 20)
    # Prefer taller gameplay view over thin bars that slip past min height
    if hh >= 700:
        score += 50
    return score


def find_d2r_window_mac():
    """Return (window_id:int, label:str) for the best on-screen D2R game window, or None.
    Uses Quartz. Read-only. NEVER returns CrossOver Home or Battle.net shell.
    v783 — short TTL cache so capture doesn't re-scan every frame.
    v843 — score_d2r_window_candidate hard-prefers D2R.exe · Diablo II: Resurrected."""
    global _PICK_WHY, _PICK_CACHE
    now = time.monotonic()
    if _PICK_CACHE and (now - _PICK_CACHE[1]) < _PICK_TTL_S:
        return _PICK_CACHE[0]
    try:
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGWindowListOptionAll,
            kCGNullWindowID,
        )
    except Exception as e:
        _PICK_WHY = "quartz-import: %s" % e
        return None
    try:
        # Fullscreen D2R can live on its own Space — list ALL spaces.
        wins = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID) or []
    except Exception as e:
        _PICK_WHY = "winlist: %s" % e
        return None
    best = None  # (score, area, wid, label)
    for w in wins:
        try:
            layer = int(w.get("kCGWindowLayer") or 0)
            if layer != 0:
                continue  # skip menus/overlays
            owner = (w.get("kCGWindowOwnerName") or "").strip()
            title = (w.get("kCGWindowName") or "").strip()
            b = w.get("kCGWindowBounds") or {}
            ww, hh = int(b.get("Width") or 0), int(b.get("Height") or 0)
            sc = score_d2r_window_candidate(
                owner, title, ww, hh, onscreen=bool(w.get("kCGWindowIsOnscreen")))
            if sc is None:
                continue
            wid = w.get("kCGWindowNumber")
            if not wid:
                continue
            area = ww * hh
            label = f"{owner}" + (f" · {title}" if title else "")
            cand = (sc, area, int(wid), label[:80])
            if best is None or cand > best:
                best = cand
        except Exception:
            continue
    if not best:
        _PICK_WHY = "no D2R.exe game window (CrossOver Home / Battle.net never pin)"
        _PICK_CACHE = (None, now)
        return None
    hit = (best[2], best[3])
    _PICK_CACHE = (hit, now)
    return hit


def screen_recording_ok():
    """v779 — macOS TCC: when Python is the responsible process (control→agent), Terminal's
    Screen Recording grant does NOT cover us. Preflight + request the system prompt."""
    if sys.platform != "darwin":
        return True
    try:
        from Quartz import CGPreflightScreenCaptureAccess, CGRequestScreenCaptureAccess
        if CGPreflightScreenCaptureAccess():
            return True
        # Shows the system dialog once; user must tick Python / TV DIABLO in Settings if denied.
        CGRequestScreenCaptureAccess()
        return bool(CGPreflightScreenCaptureAccess())
    except Exception:
        # Older macOS / no Quartz — fall through; screencapture will succeed or fail on its own.
        return True


def open_screen_recording_settings():
    """Deep-link System Settings → Privacy → Screen Recording (best-effort)."""
    if sys.platform != "darwin":
        return
    try:
        subprocess.Popen(
            ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:
        try:
            subprocess.Popen(
                ["open", "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_ScreenCapture"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


def _cap_tmp(path):
    """Unique sibling temp path — never write onto the durable target first."""
    return "%s.tmp.%d.%s" % (path, os.getpid(), str(time.time_ns() if hasattr(time, "time_ns") else int(time.time() * 1000)))


def _cap_promote(tmp, path, min_bytes=10000):
    """v779 — THE STALE-FILE LIE: screencapture can exit 1 WITHOUT touching `path`, leaving a
    previous desktop BMP in place. Trusting `os.path.exists(path)` then claims window-pin success
    on last night's wallpaper. Capture into tmp; only promote when THIS call wrote real bytes."""
    try:
        if not (os.path.exists(tmp) and os.path.getsize(tmp) > min_bytes):
            return False
        os.replace(tmp, path)   # atomic on same volume
        return True
    except Exception:
        return False
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


def _quartz_grab_screen(dest_path, uti="public.jpeg"):
    """v867 — full-screen grab via Quartz (no subprocess): ~50ms vs screencapture's ~300ms.
    The film loop's full-screen lane runs here first; screencapture stays as fallback."""
    try:
        from Quartz import (
            CGWindowListCreateImage, CGRectInfinite,
            kCGWindowListOptionOnScreenOnly, kCGWindowImageDefault, kCGNullWindowID,
            CGImageDestinationCreateWithURL, CGImageDestinationAddImage,
            CGImageDestinationFinalize, CGImageGetWidth,
            CFURLCreateFromFileSystemRepresentation,
        )
        import objc as _objc   # v868 (Grok h) — 15fps retina CGImages need a pool, not GC luck
        with _objc.autorelease_pool():
            return _quartz_finish_screen(dest_path, uti)
    except Exception:
        return False


def _quartz_finish_screen(dest_path, uti="public.jpeg"):
    try:
        from Quartz import (
            CGWindowListCreateImage, CGRectInfinite,
            kCGWindowListOptionOnScreenOnly, kCGWindowImageDefault, kCGNullWindowID,
            CGImageDestinationCreateWithURL, CGImageDestinationAddImage,
            CGImageDestinationFinalize, CGImageGetWidth,
            CFURLCreateFromFileSystemRepresentation,
        )
        img = CGWindowListCreateImage(
            CGRectInfinite, kCGWindowListOptionOnScreenOnly, kCGNullWindowID, kCGWindowImageDefault)
        if img is None or int(CGImageGetWidth(img) or 0) < 32:
            return False
        dest_path = os.path.abspath(dest_path)
        part = dest_path + ".part"
        try:
            if os.path.exists(part):
                os.remove(part)
        except Exception:
            pass
        bpath = part.encode("utf-8")
        url = CFURLCreateFromFileSystemRepresentation(None, bpath, len(bpath), False)
        if url is None:
            return False
        dest = CGImageDestinationCreateWithURL(url, uti, 1, None)
        if dest is None:
            return False
        CGImageDestinationAddImage(dest, img, None)
        if not CGImageDestinationFinalize(dest):
            return False
        if not (os.path.isfile(part) and os.path.getsize(part) > 4000):
            return False
        os.replace(part, dest_path)
        return True
    except Exception:
        return False


def _quartz_grab_window(wid, dest_path, uti="public.png"):
    """v844 — grab a single window via CGWindowListCreateImage. v868 — body under an
    autorelease pool: this is the 15fps lane; retina CGImages must not wait for GC."""
    if not wid:
        return False
    try:
        import objc as _objc
        with _objc.autorelease_pool():
            return _quartz_finish_window(wid, dest_path, uti)
    except Exception:
        return False


def _quartz_finish_window(wid, dest_path, uti="public.png"):
    try:
        from Quartz import (
            CGWindowListCreateImage, CGRectNull,
            kCGWindowListOptionIncludingWindow, kCGWindowImageDefault,
            CGImageDestinationCreateWithURL, CGImageDestinationAddImage,
            CGImageDestinationFinalize, CGImageGetWidth, CGImageGetHeight,
            CFURLCreateFromFileSystemRepresentation,
        )
        img = CGWindowListCreateImage(
            CGRectNull, kCGWindowListOptionIncludingWindow, int(wid), kCGWindowImageDefault)
        if img is None:
            return False
        w, h = int(CGImageGetWidth(img) or 0), int(CGImageGetHeight(img) or 0)
        if w < 32 or h < 32:
            return False
        dest_path = os.path.abspath(dest_path)
        parent = os.path.dirname(dest_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        # write atomically via .part then replace
        part = dest_path + ".part"
        try:
            if os.path.exists(part):
                os.remove(part)
        except Exception:
            pass
        bpath = part.encode("utf-8")
        url = CFURLCreateFromFileSystemRepresentation(None, bpath, len(bpath), False)
        if url is None:
            return False
        dest = CGImageDestinationCreateWithURL(url, uti, 1, None)
        if dest is None:
            return False
        CGImageDestinationAddImage(dest, img, None)
        if not CGImageDestinationFinalize(dest):
            return False
        if not (os.path.isfile(part) and os.path.getsize(part) > 4000):
            return False
        os.replace(part, dest_path)
        return True
    except Exception:
        try:
            part = dest_path + ".part"
            if os.path.exists(part):
                os.remove(part)
        except Exception:
            pass
        return False


def _screencapture_window(wid, tmp_path, fmt="bmp", timeout=12):
    """Try macOS screencapture -l. Returns True if tmp_path has real bytes."""
    try:
        r = subprocess.run(
            ["screencapture", "-l", str(int(wid)), "-o", "-x", "-t", fmt, tmp_path],
            capture_output=True, timeout=timeout,
        )
        return os.path.isfile(tmp_path) and os.path.getsize(tmp_path) > 10000
    except Exception:
        return False


def _capture_window_to_bmp(wid, path, timeout=12):
    """v844 — pin a window to BMP for the intelligence loop.
    1) screencapture -l  2) Quartz grab → PNG → sips BMP. Prefer Quartz when SC fails."""
    tmp = _cap_tmp(path)
    try:
        if _screencapture_window(wid, tmp, fmt="bmp", timeout=timeout):
            if _cap_promote(tmp, path):
                return True
        # clean failed tmp
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        # Quartz path
        png = path + ".qz.png"
        if not _quartz_grab_window(wid, png, uti="public.png"):
            return False
        # convert PNG → BMP for frame_sig (samples BMP body)
        try:
            r = subprocess.run(
                ["sips", "-s", "format", "bmp", png, "--out", tmp],
                capture_output=True, timeout=timeout,
            )
        except Exception:
            r = None
        try:
            if os.path.exists(png):
                os.remove(png)
        except Exception:
            pass
        if _cap_promote(tmp, path, min_bytes=8000):
            return True
        return False
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


_EYE_PREVIEW_AT = 0.0
_FILM_THREAD = None
_PICK_CACHE = None   # (hit, monotonic_t) — avoid Quartz every frame
_PICK_TTL_S = 0.55   # v846 — re-pin faster when windows flip

def _sips_hd_jpeg(src, dest, max_px=None, quality=None, timeout=6):
    """HD+ JPEG for film stage. Default 2560px / q82 (4K-class polish, still WebView-friendly)."""
    max_px = FILM_MAX_PX if max_px is None else max_px
    quality = FILM_JPEG_Q if quality is None else quality
    try:
        r = subprocess.run(
            ["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(quality),
             "--resampleHeightWidthMax", str(max_px), src, "--out", dest],
            capture_output=True, timeout=timeout,
        )
        return r.returncode == 0 and os.path.isfile(dest) and os.path.getsize(dest) > 4000
    except Exception:
        return False


def refresh_eye_preview(bmp_path, min_interval=0.12):
    """v779/v846 — fallback eye from intelligence frame (film thread is primary). HD."""
    global _EYE_PREVIEW_AT
    now = time.time()
    if now - _EYE_PREVIEW_AT < min_interval:
        return
    if not bmp_path or not os.path.isfile(bmp_path):
        return
    try:
        eye = os.path.join(FRAMES, "eye.jpg")
        if _sips_hd_jpeg(bmp_path, eye):
            _EYE_PREVIEW_AT = now
            _FILM_TIMES.append(now)
    except Exception:
        pass


_FOOT_TIMES = deque(maxlen=60)   # v871 — archive timestamps (footage fps without dir scans)


def _foot_fps_now():
    """v871 — archived-footage fps over the last 10s (None until 2 archives)."""
    now = time.time()
    recent = [t for t in _FOOT_TIMES if now - t <= 10.0]
    if len(recent) < 2:
        return None
    return round(len(recent) / 10.0, 2)


def _film_loop():
    """v846 TESLA DRIVE film — high-FPS HD JPEG of the pinned D2R window.
    Target ~15fps (TV_FILM_FPS). Intelligence still uses BMP+frame_sig on the poll loop.
    Claude thinking never freezes this thread."""
    eye = os.path.join(FRAMES, "eye.jpg")
    tmp = eye + ".part.jpg"
    # v867 (Konyo: '180 frames minimum in 3 minutes, verify FOR REAL') — his 0.52fps run was the
    # loop paying a FAILING window grab (screencapture -l on a CrossOver surface burns 1-4s
    # failing) every iteration before the fallback fired. Lane brain: 3 straight window-lane
    # failures demote to the full-screen lane for 30s (~300ms/frame → honest 2fps footage).
    _lane_fail = 0
    _lane_full_until = 0.0
    while True:
        t0 = time.time()
        try:
            os.makedirs(FRAMES, exist_ok=True)
            wid = (_CAP_TARGET or {}).get("wid")
            if (_CAP_TARGET or {}).get("mode") == "waiting":
                wid = None
            if time.time() < _lane_full_until:
                wid = None   # demoted — full-screen lane only, no doomed -l attempts
            wrote = False
            if wid:
                # v846 — Quartz first (fast path when TCC ok), screencapture fallback
                wrote = _quartz_grab_window(wid, tmp, uti="public.jpeg")
                if not wrote:
                    try:
                        r = subprocess.run(
                            ["screencapture", "-l", str(wid), "-o", "-x", "-t", "jpg", tmp],
                            capture_output=True, timeout=4,
                        )
                        wrote = os.path.exists(tmp) and os.path.getsize(tmp) > 4000
                    except Exception:
                        wrote = False
                if wrote:
                    _lane_fail = 0
                else:
                    _lane_fail += 1
                    # v868 (Grok f) — first demotion needs 3 fails; after that, ONE fail
                    # re-demotes (each probe costs up to ~4s — bound the tax) · 15s window
                    _need = 1 if globals().get("_LANE_DEMOTED_ONCE") else 3
                    if _lane_fail >= _need:
                        _lane_full_until = time.time() + 15.0
                        _lane_fail = 0
                        globals()["_LANE_DEMOTED_ONCE"] = True
                        globals()["_FILM_LANE"] = "full(demoted)"
            else:
                # v867 — Quartz full screen first (~50ms), screencapture subprocess fallback
                wrote = _quartz_grab_screen(tmp, uti="public.jpeg")
                if not wrote:
                    try:
                        subprocess.run(
                            ["screencapture", "-x", "-t", "jpg", tmp],
                            capture_output=True, timeout=4,
                        )
                        wrote = os.path.exists(tmp) and os.path.getsize(tmp) > 4000
                    except Exception:
                        wrote = False
            globals()["_FILM_LANE"] = ("window" if wid else ("full(demoted)" if time.time() < _lane_full_until else "full"))
            globals()["_FILM_CAP_MS"] = int((time.time() - t0) * 1000)
            if wrote and os.path.exists(tmp) and os.path.getsize(tmp) > 4000:
                # Retina 2940+ → polish to FILM_MAX_PX @ FILM_JPEG_Q (default 2560 / q82)
                # v861 (Grok #3 amplifier) — `or FILM_MAX_PX < 3000` was ALWAYS true: every good
                # frame paid a sips subprocess. Only genuinely oversize frames pay now.
                if os.path.getsize(tmp) > 450_000:
                    if _sips_hd_jpeg(tmp, eye):
                        try:
                            os.remove(tmp)
                        except Exception:
                            pass
                    else:
                        try:
                            os.replace(tmp, eye)
                        except Exception:
                            pass
                else:
                    try:
                        os.replace(tmp, eye)
                    except Exception:
                        pass
                now_f = time.time()
                globals()["_EYE_PREVIEW_AT"] = now_f
                _FILM_TIMES.append(now_f)
                # Footage ~2fps for theatre (was 1fps) — denser REAL video between AI reads
                try:
                    _due = globals().get("_FOOTAGE_DUE", 0.0)
                    if now_f >= _due:
                        # v868 — absolute 0.5s schedule (quantization-free 2fps); clamp catch-up
                        globals()["_FOOTAGE_DUE"] = max(_due + 0.5, now_f - 0.49) if _due else now_f + 0.5
                        globals()["_FOOTAGE_AT"] = now_f
                        hist_dir = os.path.join(FRAMES, "hist")
                        os.makedirs(hist_dir, exist_ok=True)
                        import shutil as _sh
                        # v877 (army §4) — below the floor the youth shield can't shed anything
                        # young; the copy itself must stop (the DISK FULL fault lamp explains)
                        if _sh.disk_usage(hist_dir).free / 1e9 >= MIN_FREE_GB:
                            _FOOT_TIMES.append(now_f)   # v871 — adaptive-cap telemetry
                            _sh.copyfile(eye, os.path.join(hist_dir, "f_%d.jpg" % int(now_f * 1000)))
                        # v849 (audit-core #5) — reap footage HERE too: if reads stall while the
                        # film runs, footage no longer grows unbounded until the next read.
                        if now_f >= globals().get("_REAP_DUE", 0.0):
                            globals()["_REAP_DUE"] = now_f + 120.0
                            try:
                                import shutil as _shu2
                                if _shu2.disk_usage(hist_dir).free / 1e9 < MIN_FREE_GB:
                                    # v873 — youth shield here too: only frames older than 15min shed
                                    _yc = (time.time() - 900.0) * 1000
                                    ff = sorted(f for f in os.listdir(hist_dir) if f.startswith("f_") and f.endswith(".jpg")
                                                and int(f[2:-4]) < _yc)
                                    for dead in ff[:600]:   # shed oldest OLD footage until the disk breathes
                                        try: os.remove(os.path.join(hist_dir, dead))
                                        except Exception: pass
                            except Exception:
                                pass
                except Exception:
                    pass
            else:
                # v860 (Konyo: '3 frames in 3 minutes') — FOOTAGE NEVER STARVES: when the window
                # path fails, the footage tick still archives a FULL-SCREEN frame (something
                # beats blindness; the theatre labels it footage either way).
                try:
                    now_f2 = time.time()
                    if now_f2 >= globals().get("_FOOTAGE_DUE", 0.0):
                        globals()["_FOOTAGE_DUE"] = now_f2 + 0.5
                        # v868 (Grok #5) — Quartz first: the window lane already burned its
                        # subprocess; don't pay a second one for the never-starve frame
                        if not _quartz_grab_screen(tmp, uti="public.jpeg"):
                            subprocess.run(["screencapture", "-x", "-t", "jpg", tmp],
                                           capture_output=True, timeout=5)
                        if os.path.exists(tmp) and os.path.getsize(tmp) > 4000:
                            globals()["_FOOTAGE_AT"] = now_f2
                            _FOOT_TIMES.append(now_f2)   # v871
                            hist_dir2 = os.path.join(FRAMES, "hist")
                            os.makedirs(hist_dir2, exist_ok=True)
                            import shutil as _sh2
                            _sh2.copyfile(tmp, os.path.join(hist_dir2, "f_%d.jpg" % int(now_f2 * 1000)))
                            os.replace(tmp, eye)
                            globals()["_EYE_PREVIEW_AT"] = now_f2
                except Exception:
                    pass
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except Exception:
                    pass
        except Exception:
            pass
        dt = time.time() - t0
        time.sleep(max(0.02, FILM_INTERVAL_S - dt))


def start_film_thread():
    global _FILM_THREAD
    if WATCH_MODE or sys.platform != "darwin":
        return
    if _FILM_THREAD and _FILM_THREAD.is_alive():
        return
    _FILM_THREAD = threading.Thread(target=_film_loop, daemon=True, name="tv-film")
    _FILM_THREAD.start()


def capture_mac(path, timeout=12):
    """Full-screen capture by default (fullscreen D2R / CrossOver).
    Optional TV_CAPTURE=window|auto pins CrossOver/D2R window. v753 hard timeout.
    v779 — always capture to a temp path first (stale-target trust gate killed)."""
    global _CAP_TARGET, _CAP_WHY, _LAST_GOOD_WIN
    _CAP_WHY = ""
    mode = (os.environ.get("TV_CAPTURE") or "auto").strip().lower()   # v777.1 (Konyo live: 'it's showing the desktop') — AUTO pins the D2R window when one exists; full-screen only as fallback
    # Optional window pin only when explicitly asked (or auto)
    if mode in ("auto", "window", "win", "game"):
        hit = find_d2r_window_mac()
        # v779 — LAST-GOOD CACHE: Quartz listing is flaky from the agent's context; a window
        # that pinned once stays pinned until a capture with it actually fails.
        if hit:
            _LAST_GOOD_WIN = hit
        elif _LAST_GOOD_WIN:
            hit = _LAST_GOOD_WIN
        if not hit:
            _CAP_WHY = "no game window: %s" % (_PICK_WHY or "no match in list")
        if hit:
            wid, label = hit
            try:
                # v844 — screencapture -l OR Quartz CGWindowListCreateImage (SC alone was
                # dying all night with rc=1 size=0 while D2R.exe was right there)
                if _capture_window_to_bmp(wid, path, timeout=timeout):
                    if _CAP_TARGET.get("wid") != wid or _CAP_TARGET.get("mode") != "window":
                        try: ev("cap", "🎯 eye pinned to %s" % label)
                        except Exception: pass
                    _CAP_TARGET = {"mode": "window", "label": label, "wid": wid}
                    return True
                # this wid failed for real — drop the cache so full-screen can take over
                if _LAST_GOOD_WIN and _LAST_GOOD_WIN[0] == wid:
                    _LAST_GOOD_WIN = None
                _CAP_WHY = "window capture failed (screencapture+quartz) wid=%s" % wid
                # keep wid so film thread can still try Quartz on this game window
                _CAP_TARGET = {"mode": "full", "label": "full screen (%s)" % _CAP_WHY, "wid": None}   # v861 (Grok #2 choke) — dead pin releases the wid; film full-screens instead of hammering a corpse
            except Exception as e:
                _CAP_WHY = "window capture exc: %s" % e
        if mode in ("window", "win", "game"):
            _CAP_TARGET = {"mode": "waiting", "label": "Diablo II / CrossOver not found", "wid": None}
            return False
        # auto with no window → fall through to full screen
    # DEFAULT / fallback: entire display (fullscreen game)
    tmp = _cap_tmp(path)
    try:
        r = subprocess.run(
            ["screencapture", "-x", "-t", "bmp", tmp],
            capture_output=True, timeout=timeout,
        )
        ok = _cap_promote(tmp, path)
        if ok:
            _CAP_TARGET = {"mode": "full", "label": ("full screen" + ((" (" + _CAP_WHY + ")") if _CAP_WHY else "")), "wid": None}
        else:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
        return ok
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False

# v771.2 — SIM without Screen Recording: synthetic BMPs so settle+stub reads still fire.
# Real play never sets TV_STUB; this only kicks in when capture fails under stub.
_STUB_CAP_I = 0
def capture_stub_synth(path):
    """Write a valid 24-bit BMP that alternates (motion) then holds (settle).
    Hold ~8 polls (~2s) then hard-switch palette so sig_diff ≫ SETTLE/MOTION_PEAK."""
    global _STUB_CAP_I
    import struct
    _STUB_CAP_I += 1
    slot = (_STUB_CAP_I // 8) % 4
    # far-apart RGB so every sampled byte jumps well past tol=28
    palette = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
    ]
    r, g, b = palette[slot]
    w, h = 640, 400
    row = w * 3
    pad = (4 - (row % 4)) % 4
    pixel_size = (row + pad) * h
    file_size = 54 + pixel_size
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(b"BM")
            f.write(struct.pack("<IHHI", file_size, 0, 0, 54))
            f.write(struct.pack("<IIIHHIIIIII", 40, w, h, 1, 24, 0, pixel_size, 2835, 2835, 0, 0))
            # BGR rows — solid block, maximum sig_diff between slots
            row_bytes = bytes([b, g, r]) * w + (b"\x00" * pad)
            for _y in range(h):
                f.write(row_bytes)
        return os.path.isfile(path) and os.path.getsize(path) > 200000
    except Exception:
        return False

def newest_watched_frame():
    """Windows mode: capture_win.ps1 drops frames into tv/frames — consume the newest."""
    try:
        # Prefer live.bmp (intelligence); ignore eye.jpg / read.jpg (film / vision transport)
        skip = {"read.jpg", "eye.jpg", "cap_target.json"}
        fs = [os.path.join(FRAMES, f) for f in os.listdir(FRAMES)
              if f.lower().endswith((".bmp", ".png", ".jpg", ".jpeg"))
              and f.lower() not in skip
              and not f.lower().endswith(".part.jpg")
              and "tmp" not in f.lower()]
        return max(fs, key=os.path.getmtime) if fs else None
    except Exception:
        return None


def _refresh_cap_target_from_disk():
    """v784 — Windows capture_win.ps1 writes frames/cap_target.json; surface it on /state."""
    global _CAP_TARGET
    try:
        p = os.path.join(FRAMES, "cap_target.json")
        if not os.path.isfile(p):
            return
        with open(p, encoding="utf-8") as f:
            j = json.load(f)
        mode = (j.get("mode") or "full").strip()
        label = (j.get("label") or mode)[:80]
        nxt = {"mode": mode, "label": label, "wid": j.get("wid")}
        if nxt != _CAP_TARGET:
            if mode == "window" and label and _CAP_TARGET.get("label") != label:
                try:
                    ev("cap", "🎯 eye pinned to %s" % label)
                except Exception:
                    pass
            _CAP_TARGET = nxt
    except Exception:
        pass

def frame_sig(path):
    """~4k byte samples across the BMP pixel data — cheap fuzzy fingerprint, stdlib only.
    v877 (army audit #2) — SAMPLED SEEKS: the old full-file read + slice churned ~0.5-1GB/s
    of memory at poll cadence on retina BMPs. Same fingerprint, 4096 × 1-byte reads."""
    try:
        import mmap as _mmap
        with open(path, "rb") as f:
            mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
            try:
                body = memoryview(mm)[54:]
                step = max(1, len(body) // 4096)
                out = bytes(body[::step][:4096])
                body.release()
                return out
            finally:
                mm.close()
    except Exception:
        with open(path, "rb") as f:
            data = f.read()
        body = data[54:]
        step = max(1, len(body) // 4096)
        return bytes(body[::step][:4096])

def sig_diff(a, b, tol=28):
    """fraction of samples that MEANINGFULLY differ. Real-game calibration (Konyo's town
    video): render/recording noise nudges nearly every pixel a little each frame, and the
    background always animates — so equality is useless. A sample counts as changed only
    when its value moved by more than `tol` (ambient flicker stays under it; opening a
    panel / a tooltip / walking moves whole regions far past it)."""
    if a is None or b is None or len(a) == 0 or len(b) == 0: return 1.0
    if a is b or a == b: return 0.0   # v877 — identical frames skip the 4096-sample loop
    m = min(len(a), len(b))
    return sum(1 for i in range(m) if abs(a[i] - b[i]) > tol) / m

# v735 — per-read frame ring for session history (human eye ~1920; AI still uses 1568)
HIST_DIR = os.path.join(FRAMES, "hist")
try:
    HIST_KEEP = max(10, int(os.environ.get("TV_HIST_KEEP", "800")))   # v840 — more AI-read photos protected
    HIST_MB = max(50, int(os.environ.get("TV_HIST_MB", "1500")))      # v839 — footage era: ceiling raised (REG-025)
    FOOT_MB = max(50, int(os.environ.get("TV_FOOT_MB", "400")))       # v840 — footage dies sooner (was 900; 2600 f_ drowned the night)
    FOOT_KEEP = max(60, int(os.environ.get("TV_FOOT_KEEP", "28800")))  # v860 (Konyo: 'change the global cap!') — ~4h @2fps; the MB budget (FOOT_MB) is the real guard, count can never eat older sessions
    MIN_FREE_GB = max(2, int(os.environ.get("TV_MIN_FREE_GB", "8")))   # v861.1 — the ONLY retention governor
except Exception:
    HIST_KEEP = 800
    HIST_MB = 1500
    FOOT_MB = 400
    FOOT_KEEP = 28800
    MIN_FREE_GB = 8
# MacBook-ish display width for click-to-enlarge (not the AI vision input size)
HIST_MAX_PX = int(os.environ.get("TV_HIST_PX", "2560"))   # v753 — retina-crisp fullscreen (was 1920)

# v741 — KNOWN-DEAD FRAMES (Konyo: the loading/portal screen 'is always the same photo — it
# should be recognized'): an empty deep read teaches the agent that frame's signature; when it
# reappears (any zone transition), it is recognized locally in ~0ms — no vision spent, and the
# history registers an honest '⏳ transition' row instead of another 'nothing readable'.
KNOWN_DEAD_CAP = 8
_KNOWN_DEAD = []
_KNOWN_DEAD_FILE = os.path.join(HERE, "known_frames.json")
def _known_dead_load():
    """v742 — learning survives restarts: the loading screen is learned ONCE, ever."""
    try:
        import base64
        with open(_KNOWN_DEAD_FILE, encoding="utf-8") as f:
            for b in json.load(f)[:KNOWN_DEAD_CAP]:
                _KNOWN_DEAD.append(bytes(base64.b64decode(b)))
    except Exception:
        pass

def _known_dead_save():
    try:
        import base64
        with open(_KNOWN_DEAD_FILE, "w", encoding="utf-8") as f:
            json.dump([base64.b64encode(bytes(k)).decode() for k in _KNOWN_DEAD], f)
    except Exception:
        pass

def learn_dead_frame(sig):
    if sig is None: return
    for k in _KNOWN_DEAD:
        if sig_diff(sig, k) <= 0.04: return   # already known
    _KNOWN_DEAD.append(sig)
    del _KNOWN_DEAD[:-KNOWN_DEAD_CAP]
    _known_dead_save()

# v746 — the transition label reads the story so far (Konyo: 'ENTERING a PORTAL or ENTERING A
# NEW GAME, depending on the photos beforehand'). LAST_AREA is the last zone a deep read saw.
LAST_AREA = ""
def transition_note(last_area, n_reads):
    if last_area: return f"through the portal — leaving {last_area}"
    if n_reads == 0: return "entering a new game"
    return "loading — next area coming"

def should_learn_dead(rd):
    """v794 (Grok R5 #4) — learn a dead frame ONLY on an explicit vision-confirmed transition.
    The old gate also learned mode:empty / parse-fail shapes — ONE chatty-CLI hiccup on a real
    inventory freeze wrote that panel into known_frames.json and the eye stayed blind to that
    whole panel class for the rest of the night (and across restarts)."""
    if rd.get("names") or rd.get("area"):
        return False
    if rd.get("mode") in ("empty", "error", "timeout"):
        return False
    return rd.get("scene") == "transition"

def known_dead_match(sig):
    if sig is None: return None
    for k in _KNOWN_DEAD:
        if sig_diff(sig, k) <= 0.04: return k
    return None

def _readable_frame(ap, out_jpg=None):
    """v710.6 LIVE-SESSION FIX (Konyo's first real run): claude's Read tool chokes on a 16MB
    raw BMP — both live reads timed out at 180s. Convert to a 1568px JPEG (the locked intake
    spec) before the vision call. Mac: sips (built-in). Windows: capture_win.ps1 saves live.png
    alongside. Falls back to the original path if conversion isn't available."""
    try:
        if not ap.lower().endswith(".bmp"):
            return ap
        jp = out_jpg or os.path.join(FRAMES, "read.jpg")
        r = subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "80",
                            "--resampleHeightWidthMax", "1568", ap, "--out", jp],
                           capture_output=True, timeout=20)
        if r.returncode == 0 and os.path.isfile(jp):
            global _JPEG_LOGGED
            if not globals().get("_JPEG_LOGGED"):
                _JPEG_LOGGED = True
                ev("boot", f"vision transport OK — frame \u2192 read.jpg {os.path.getsize(jp)//1024}KB (was {os.path.getsize(ap)//1024//1024}MB)")
            return jp
        png = os.path.join(os.path.dirname(ap), "live.png")   # Windows: saved by capture_win.ps1
        if os.path.isfile(png):
            return png
    except Exception:
        pass
    return ap

_JFID_STATE = {"path": None, "ids": None}   # v877 — cold parse keyed on the journal PATH
# The v849 mtime-key cache defeated itself: every append changed the live journal's mtime,
# so the "cache" re-parsed ~24MB of JSONL on nearly every read, forever.
def _journal_frame_ids():
    """v840 — every frameId still referenced by the session journal is UN-PRUNABLE.
    v877 — incremental: one cold parse per process; appends feed the set directly."""
    if _JFID_STATE["ids"] is None or _JFID_STATE["path"] != JOURNAL:
        ids = set()
        try:
            paths = [JOURNAL]
            try:
                d = os.path.dirname(JOURNAL) or "."
                base = os.path.basename(JOURNAL)
                for name in os.listdir(d):
                    if name.startswith(base) or (name.startswith("sessions") and name.endswith(".jsonl")):
                        paths.append(os.path.join(d, name))
            except Exception:
                pass
            seen_p = set()
            for jp in paths:
                if jp in seen_p or not os.path.isfile(jp):
                    continue
                seen_p.add(jp)
                try:
                    with open(jp, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                fid = json.loads(line).get("frameId")
                            except Exception:
                                continue
                            if fid:
                                ids.add(str(fid) + ".jpg")
                except Exception:
                    pass
        except Exception:
            pass
        _JFID_STATE["path"], _JFID_STATE["ids"] = JOURNAL, ids
    ids = _JFID_STATE["ids"]
    PROTECT_CAP = max(200, int(os.environ.get("TV_PROTECT_CAP", "2000") or 2000))
    if len(ids) > PROTECT_CAP:
        def _fid_ms(x):
            try:
                return int(str(x).split(".")[0].rsplit("_", 1)[-1])
            except Exception:
                return 0
        ids = set(sorted(ids, key=_fid_ms)[-PROTECT_CAP:])
    return set(ids)


def archive_read_frame(src_path, n, ts_ms=None):
    """v735 — snapshot the settled screen into frames/hist/{n}_{ts}.jpg (~1920 JPEG).
    Returns frame id string for /frame?id=… so each history row can reopen what the AI saw.
    Keeps last HIST_KEEP files. Never raises into the scan loop."""
    ts_ms = ts_ms if ts_ms is not None else int(time.time() * 1000)
    fid = "%d_%d" % (int(n), int(ts_ms))
    try:
        os.makedirs(HIST_DIR, exist_ok=True)
        dest = os.path.join(HIST_DIR, fid + ".jpg")
        src = os.path.abspath(src_path) if src_path else ""
        ok = False
        if src and os.path.isfile(src):
            # Prefer full capture → 1920 for human eyes (AI path stays 1568 via _readable_frame)
            if src.lower().endswith((".bmp", ".png", ".jpg", ".jpeg")):
                try:
                    r = subprocess.run(
                        ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "82",
                         "--resampleHeightWidthMax", str(HIST_MAX_PX), src, "--out", dest],
                        capture_output=True, timeout=25)
                    ok = r.returncode == 0 and os.path.isfile(dest)
                except Exception:
                    ok = False   # sips is macOS-only — Windows/Linux land in the copy fallbacks
            if not ok:
                # portable fallback #1: the vision JPEG (already converted+downscaled)
                jp = os.path.join(FRAMES, "read.jpg")
                if os.path.isfile(jp):
                    import shutil
                    shutil.copy2(jp, dest)
                    ok = os.path.isfile(dest)
            if not ok:
                # portable fallback #2 (v755.3 — Windows/CI truth): raw copy of the frame.
                # Browsers sniff content, so a PNG/BMP body behind the .jpg name still renders;
                # an archived photo ALWAYS beats an empty history cell.
                try:
                    import shutil
                    shutil.copy2(src, dest)
                    ok = os.path.isfile(dest)
                except Exception:
                    ok = False
        if not ok:
            return ""
        # v877 (army #6) — the eviction below only ever ACTS when free < MIN_FREE_GB; skip the
        # whole 30k-file listing + mtime sort + journal-shield load when the disk is healthy.
        try:
            import shutil as _shq
            if _shq.disk_usage(HIST_DIR).free / 1e9 >= MIN_FREE_GB \
                    and time.time() < globals().get("_ORPHAN_DUE", 0.0):
                return fid   # healthy disk + orphans swept recently → skip the 30k-file walk
            globals()["_ORPHAN_DUE"] = time.time() + 600.0   # full sweep at most every 10min
        except Exception:
            pass
        # prune oldest beyond HIST_KEEP — and beyond the TV_HIST_MB disk ceiling (v753)
        # v813 (Grok R8 #7) — ONE budget: theatre derivative caches (cache1280/cache160) are
        # counted in the ceiling AND deleted with their source frame — no more disk lie.
        try:
            files = [os.path.join(HIST_DIR, f) for f in os.listdir(HIST_DIR)
                     if f.lower().endswith(".jpg")]
            files.sort(key=lambda p: os.path.getmtime(p))
            cache_dirs = [os.path.join(HIST_DIR, d) for d in ("cache1280", "cache160")
                          if os.path.isdir(os.path.join(HIST_DIR, d))]
            def _twins(src):
                b = os.path.basename(src)
                return [os.path.join(cd, b) for cd in cache_dirs]
            def _size_all(src):
                t = 0
                for f in [src] + _twins(src):
                    try: t += os.path.getsize(f)
                    except Exception: pass
                return t
            # v826 — footage frames (f_*.jpg) have their OWN count cap
            read_files = [f for f in files if not os.path.basename(f).startswith("f_")]
            foot_files = [f for f in files if os.path.basename(f).startswith("f_")]
            # v840 — journal shield: never delete a read frame still named in sessions.jsonl
            protected = _journal_frame_ids()
            # v861.1 (Konyo: 'so much smarter without a cap — it's locally stored') — COUNT CAPS
            # ABOLISHED. The one governor is FREE DISK: evict only when under MIN_FREE_GB,
            # footage first (oldest→newest), then oldest UNPROTECTED reads. Every frame that
            # fits on disk LIVES. Journal-named frames stay shielded.
            doomed = set()
            unprotected = [f for f in read_files if os.path.basename(f) not in protected]
            try:
                import shutil as _shu
                free_gb = _shu.disk_usage(HIST_DIR).free / 1e9
            except Exception:
                free_gb = 999
            if free_gb < MIN_FREE_GB:
                # v873 (THE 4GB NIGHT) — YOUTH SHIELD: an emergency may NEVER eat the session
                # being recorded. Frames younger than 15min survive every shed; old sessions
                # die first. If everything is young, we shed nothing and the DISK FULL fault
                # (v872.1) tells Konyo the truth instead of silently chewing his recording.
                _young_cut = time.time() - 900.0
                def _is_old(_f):
                    try:
                        return os.path.getmtime(_f) < _young_cut
                    except Exception:
                        return True
                need = (MIN_FREE_GB - free_gb) * 1e9
                freed = 0
                for f in [x for x in foot_files if _is_old(x)] + [x for x in unprotected if _is_old(x)]:
                    if freed >= need:
                        break
                    freed += _size_all(f)
                    doomed.add(f)
            for old in doomed:
                if os.path.basename(old) in protected and not os.path.basename(old).startswith("f_"):
                    continue  # belt: never unlink a journaled AI frame
                for f in [old] + _twins(old):
                    try: os.remove(f)
                    except Exception: pass
            # orphan derivatives (source already gone) die too
            keep = {os.path.basename(f) for f in files if f not in doomed}
            keep |= protected
            for cd in cache_dirs:
                for f in os.listdir(cd):
                    if f.lower().endswith(".jpg") and f not in keep:
                        try: os.remove(os.path.join(cd, f))
                        except Exception: pass
        except Exception:
            pass
        return fid
    except Exception:
        return ""

def frame_path_for_id(fid):
    """Resolve hist id → absolute path, or '' if missing/unsafe."""
    safe = str(fid or "").strip()
    if not safe or not all(c.isdigit() or c == "_" for c in safe):
        return ""
    p = os.path.join(HIST_DIR, safe + ".jpg")
    return p if os.path.isfile(p) else ""


# ═══ v713 — PERSISTENT VISION WORKER (the SPEED fix). One long-lived claude session in
# stream-json mode: each frame is a TURN, not a cold start (live run #1: cold starts + a
# broken transport = 180s hangs). The worker restarts itself every N turns so conversation
# context never bloats a read, and ANY wobble (timeout · dead process · bad JSON) kills it
# and falls back to the one-shot path. TV_CLAUDE_BIN overrides the binary — the TDD seam
# (tests run a fake bin that speaks stream-json).
CLAUDE_BIN = os.environ.get("TV_CLAUDE_BIN", "claude")
try:
    import shutil as _shw
    CLAUDE_BIN = _shw.which(CLAUDE_BIN) or CLAUDE_BIN   # v877 — resolves claude.cmd on Windows npm installs
except Exception:
    pass
WORKER_MAX_TURNS = 8
# v723/v725 — SPEED + GENIUS LADDER (subscription only):
#   LIVE RUN #3 finding: Haiku warm was 13–16s; Sonnet warm was 6–10s — economics flipped.
#   FAST_MODEL default is now SONNET (felt speed). Haiku remains opt-in via TV_MODEL=haiku.
#   GENIUS escalate only fires when FAST != GENIUS (e.g. haiku→sonnet experiments).
# Override: TV_MODEL=sonnet|haiku  TV_MODEL_ESCALATE=sonnet  TV_ESCALATE_CAP=40
FAST_MODEL = os.environ.get("TV_MODEL", "sonnet").strip() or "sonnet"
GENIUS_MODEL = os.environ.get("TV_MODEL_ESCALATE", "sonnet").strip() or "sonnet"
try:
    ESCALATE_CAP = max(0, int(os.environ.get("TV_ESCALATE_CAP", "40")))
except Exception:
    ESCALATE_CAP = 40
_ESCALATE_N = [0]

# v720 — AUTH PATH FIX (live run #2): if ANTHROPIC_API_KEY (or sibling API tokens) is set in
# the shell, every headless `claude -p` prefers that key over the user's Claude subscription
# login. A dead/rate-limited key hangs past 40–90s with empty stdout — exactly run #2's
# warm + oneshot timeouts. Strip API-key auth so vision rides the *logged-in* claude plan
# (the product contract: "your subscription, not API keys"). Keep OAuth tokens if present.
_API_AUTH_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
def _claude_env():
    """Env for vision subprocesses: subscription login, not shell API keys."""
    env = os.environ.copy()
    stripped = [k for k in _API_AUTH_ENV if env.pop(k, None) is not None]
    return env, stripped

def _log_auth_once(stripped):
    if not stripped or globals().get("_AUTH_LOGGED"):
        return
    globals()["_AUTH_LOGGED"] = True
    ev("boot", f"vision auth: stripped {','.join(stripped)} — using Claude subscription login")

class VisionWorker:
    def __init__(self, model=None):
        # v720.1 — lock: warm thread + settle-read must never interleave on one stream
        self.model = model or FAST_MODEL
        self.p = None; self.q = None; self.turns = 0; self.lock = threading.Lock()
    def _spawn(self):
        import queue
        env, stripped = _claude_env()
        _log_auth_once(stripped)
        self.p = subprocess.Popen(
            [CLAUDE_BIN, "-p", "--input-format", "stream-json", "--output-format", "stream-json",
             "--verbose", "--model", self.model, "--allowedTools", "Read", "--strict-mcp-config"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, bufsize=1, env=env,
            preexec_fn=(None if sys.platform == "win32" else (lambda: os.nice(10))))   # v876 — D2R owns the CPU
        self.q = queue.Queue(); self.turns = 0
        def _pump(proc, q):
            try:
                for line in proc.stdout: q.put(line)
            except Exception: pass
            q.put(None)
        threading.Thread(target=_pump, args=(self.p, self.q), daemon=True).start()
    def stop(self):
        """Kill the warm claude child and close pipes (avoids ResourceWarning leaks)."""
        p = self.p
        self.p = None
        if not p:
            return
        try:
            if p.poll() is None:
                p.kill()
            try:
                p.wait(timeout=2)
            except Exception:
                pass
            for stream in (p.stdin, p.stdout, p.stderr):
                try:
                    if stream:
                        stream.close()
                except Exception:
                    pass
        except Exception:
            pass
    def ask(self, prompt, timeout=75):
        """one turn → the result text, or None (caller falls back to one-shot). Serialized."""
        with self.lock:
            try:
                if self.p is None or self.p.poll() is not None or self.turns >= WORKER_MAX_TURNS:
                    self.stop(); self._spawn()
                msg = {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": prompt}]}}
                self.p.stdin.write(json.dumps(msg) + "\n"); self.p.stdin.flush()
                deadline = time.time() + timeout
                while time.time() < deadline:
                    try: line = self.q.get(timeout=max(0.1, deadline - time.time()))
                    except Exception: break
                    if line is None: break
                    line = line.strip()
                    if not line: continue
                    try: j = json.loads(line)
                    except Exception: continue
                    if j.get("type") == "result":
                        self.turns += 1
                        return j.get("result") or ""
                self.stop()   # timed out / stream ended — never reuse a wedged worker
                return None
            except Exception:
                self.stop()
                return None
_WORKER = VisionWorker()
# v782 — vision must NOT freeze the eye: capture loop keeps writing live.bmp/eye.jpg while
# Claude thinks. (Konyo: ON AIR + moving but film stuck on READING.)
_VISION_BUSY = False
_VISION_BUSY_AT = 0.0   # v789 — when the in-flight vision call started (stall detection)

# v863 (READER POOL) — up to POOL_N concurrent Claude vision readers with ORDERED APPLY.
# Each reader keeps its OWN warm VisionWorker (Popen/lock/turns/restart-at-8) and reads a
# PRIVATE snap/read file, so two readers never collide on snap.bmp/read.jpg. Completions are
# buffered by captureTs and applied only when no OLDER read is still in flight (the
# floor-before-stash lock). Worker 0 == _WORKER (the farewell / POOL_N=1 fast path).
# OWNER DEFAULT = 8 readers. MEMORY: each warm `claude -p` child is ~200-600MB, so a full
# pool of 8 can hold ~1.6-4.8GB resident — set TV_POOL lower on a tight machine. Fail-soft:
# a throttled/queued reader's ask() returns None → one-shot bridge + THAT slot rewarms; the
# slot is always released in finally, so a degraded reader shrinks effective capacity, never
# stalls the pool.
def _pool_default():
    """v876 (Konyo: 'lags a lot when everything is running') — the pool fits the MACHINE:
    8 warm claude workers pin ~1.6-4.8GB; with D2R + CrossOver on a 16GB Mac that IS the lag.
    ≥24GB → 8 workers; below → 4 (the proven cadence at 4 is ~2.5-4s anyway). TV_POOL always wins."""
    gb = 0.0
    try:
        gb = float(os.environ.get("TV_POOL_ASSUME_GB", "") or 0)   # test hook
    except Exception:
        gb = 0.0
    if not gb:
        try:
            if sys.platform == "darwin":
                gb = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], timeout=3)) / 1e9
            else:
                gb = (os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")) / 1e9
        except Exception:
            gb = 16
    return 8 if gb >= 24 else 4


_TP_ENV = os.environ.get("TV_POOL", "").strip()
POOL_N = max(1, min(8, int(_TP_ENV))) if _TP_ENV else max(1, min(8, _pool_default()))
ORDER_HOLD_MS = max(5000, int(os.environ.get("TV_ORDER_HOLD_MS", "90000") or 90000))
_WORKERS = [_WORKER] + [VisionWorker() for _ in range(POOL_N - 1)]
_pool_lock = threading.Lock()
_pool_free = list(range(POOL_N))   # reader ids currently idle
_in_flight = {}                    # job_id -> {readerId, captureTs, sig, origin, startedAt}
_order_buf = []                    # heapq of (captureTs, seq, payload) awaiting ordered apply
_order_seq = [0]
_emit_lock = threading.Lock()
_job_seq = [0]


def _job_files(rid, n):
    """PRIVATE per-job capture + read paths — concurrent readers never share snap.bmp/read.jpg."""
    return (os.path.join(FRAMES, "snap_%d_%d.bmp" % (int(rid), int(n))),
            os.path.join(FRAMES, "read_%d_%d.jpg" % (int(rid), int(n))))


def _vision_in_flight_n():
    with _pool_lock:
        return len(_in_flight)


def _vision_busy():
    """Compat shim for the old single-reader gate: True only when EVERY reader is busy."""
    return _vision_in_flight_n() >= POOL_N


def _heartbeat_cap():
    """v871 — ADAPTIVE (farm-video runs 1-3): fixed cap 6 CHOKED the 16GB Mac — capture spiked
    to 13s, footage collapsed 1.99→0.34fps, reads slowed to 30-50s. FOOTAGE IS KING (Konyo's
    300+ frames): base 2; earn 4 while the film lane is provably healthy (≥1.8fps archive,
    <200ms captures); shed to 1 the moment footage starves. Ceiling 3/4 pool for big machines."""
    hi = max(1, (POOL_N * 3) // 4)
    fps = _foot_fps_now()
    cap_ms = globals().get("_FILM_CAP_MS") or 0
    if (fps is not None and fps < 1.2) or cap_ms > 800:
        return 1
    if fps is not None and fps >= 1.8 and cap_ms < 200:
        return min(hi, 4)
    return min(hi, 2)


def _heartbeat_in_flight_n():
    with _pool_lock:
        return sum(1 for j in _in_flight.values() if j.get("origin") == "heartbeat")


def _heartbeat_in_flight():
    return _heartbeat_in_flight_n() > 0


def _in_flight_has_sig(sig):
    """Anti double-spend: is this exact view already on a reader?"""
    with _pool_lock:
        for j in _in_flight.values():
            try:
                if sig_diff(sig, j.get("sig")) <= SETTLE:
                    return True
            except Exception:
                pass
    return False


def _in_flight_min_capture():
    with _pool_lock:
        if not _in_flight:
            return None
        return min(int(j.get("captureTs") or 0) for j in _in_flight.values())


def _pool_acquire():
    """Reserve a free reader id (caller must release via _pool_release), or None if all busy."""
    with _pool_lock:
        if not _pool_free:
            return None
        return _pool_free.pop(0)


def _pool_release(rid):
    with _pool_lock:
        if rid not in _pool_free:
            _pool_free.append(rid)
            _pool_free.sort()


def _order_push(capture_ts, job, rd, ocr_rd):
    """v863 — enqueue a completed deep read for ordered apply, keyed by captureTs."""
    with _emit_lock:
        _order_seq[0] += 1
        heapq.heappush(_order_buf, (int(capture_ts), _order_seq[0],
                       {"job": job, "rd": rd, "ocr_rd": ocr_rd,
                        "captureTs": int(capture_ts), "bufferedAt": int(time.time() * 1000)}))


def _order_drain():
    """v863 — apply buffered deep reads in captureTs order. A buffered completion emits only when
    NO in-flight reader holds a strictly SMALLER captureTs (floor-before-stash lock); a completion
    that has waited past ORDER_HOLD_MS applies anyway (dispatch.orderSkip='straggler'). Returns
    the list of records applied this call."""
    applied = []
    with _emit_lock:
        now_ms = int(time.time() * 1000)
        while _order_buf:
            capture_ts, seq, payload = _order_buf[0]
            floor = _in_flight_min_capture()
            straggler = (now_ms - int(payload.get("bufferedAt") or now_ms)) >= ORDER_HOLD_MS
            if floor is not None and floor < capture_ts and not straggler:
                break   # an OLDER read is still pending — hold the line
            heapq.heappop(_order_buf)
            job = payload["job"]
            disp = dict(job.get("dispatch") or {})
            if straggler:
                disp["orderSkip"] = "straggler"
            disp["appliedTs"] = now_ms
            disp["orderHoldMs"] = ORDER_HOLD_MS
            try:
                rec = emit_deep_read(payload["rd"], n=job.get("n"), frame_id=job.get("fid"),
                                     interest=job.get("interest", 0.0),
                                     used_priority=job.get("priority", False),
                                     ocr_rd=payload.get("ocr_rd"), farewell=False,
                                     capture_ts=int(capture_ts),
                                     dispatch=disp, raw=job.get("raw"))
                if rec is not None:
                    applied.append(rec)
            except Exception as e:
                try: ev("cap", "ordered apply failed: %s" % e)
                except Exception: pass
    return applied


_POOL_STOPPING = False
def _pool_shutdown(timeout=90.0):
    """v864 (Grok back-pass #1) — farewell must NEVER race in-flight applies: wait up to a full
    vision timeout (not 8s), mark the pool STOPPING so late vision threads only release their
    slot (no order_push, no emit), then force-flush the buffer and stop workers 1..N-1."""
    globals()["_POOL_STOPPING"] = True
    deadline = time.time() + max(0.0, timeout)
    while time.time() < deadline:
        with _pool_lock:
            if not _in_flight:
                break
        time.sleep(0.1)
    try:
        _prev = ORDER_HOLD_MS
        globals()["ORDER_HOLD_MS"] = 0
        _order_drain()
        globals()["ORDER_HOLD_MS"] = _prev
    except Exception:
        pass
    for w in _WORKERS[1:]:
        try: w.stop()
        except Exception: pass
_REFIRE_SIG = None      # v795 (Grok R5 #2) — OCR saw names, deep came back empty: allow ONE re-read of that view

# v845 — ONE AI READER: settle freeze → dual-lane (OCR flash + Claude deep).
# Scout mid-play secondary reader removed (Konyo: too slow / complicated).
# Hard limit: icons alone never invent names (read-only screen truth).

# v825 (Grok R5 #1 / R9 #2) — SETTLE QUEUE ring buffer ──────────────────────────
# A 7–90s Claude vision call runs on a background thread; meanwhile the main loop keeps
# capturing. Distinct freezes that landed during that window used to hit the `if _VISION_BUSY:`
# `continue` and vanish forever (hover A→B→C while A is read: B, C never reached OCR / hist /
# lifecycle / journal). We ring-buffer a COPIED snapshot of each new freeze (the live frame is
# about to be overwritten) and, the instant the in-flight read frees up, drain the NEWEST held
# view (Konyo's most-current screen) through the same dual-lane pipeline.
SETTLE_QUEUE_CAP = max(1, int(os.environ.get("TV_SETTLE_QUEUE_CAP", "4") or 4))
SETTLE_QUEUE_STALE_MS = max(1000, int(os.environ.get("TV_SETTLE_QUEUE_STALE_MS", "120000") or 120000))
_SETTLE_QUEUE = []              # FIFO, newest last; each: {"path","sig","ts","interest","priority"}
_settle_q_lock = threading.Lock()

def _settle_queue_dir():
    d = os.path.join(FRAMES, "queue")
    try: os.makedirs(d, exist_ok=True)
    except Exception: pass
    return d

def _settle_file_del(entry):
    try:
        p = entry.get("path") if isinstance(entry, dict) else entry
        if p and os.path.isfile(p): os.remove(p)
    except Exception:
        pass

def _settle_enqueue(src_frame, sig, interest=0.0, priority=False, origin="settle"):
    """Unit-engine work queue: copy live frame to frames/queue/<sig8>.bmp. Scout text freezes
    and settle freezes share this ring — same clock, same drain. Deduped by sig; FIFO cap;
    stale pruned. Never raises into the scan loop."""
    try:
        now = int(time.time() * 1000)
        reading = globals().get("_LAST_EMIT_SIG")
        if reading is not None and sig_diff(sig, reading) <= SETTLE:
            return   # this is the very view being read — don't re-queue it
        with _settle_q_lock:
            fresh, dropped = [], 0
            for e in _SETTLE_QUEUE:
                if now - e["ts"] > SETTLE_QUEUE_STALE_MS:
                    _settle_file_del(e); dropped += 1
                else:
                    fresh.append(e)
            _SETTLE_QUEUE[:] = fresh
            if dropped:
                ev("cap", "unit-queue — dropped %d stale freeze(s) (>%ds) waiting for a read"
                   % (dropped, SETTLE_QUEUE_STALE_MS // 1000))
            for e in _SETTLE_QUEUE:
                if sig_diff(sig, e["sig"]) <= SETTLE:
                    return   # already holding this view
            sig8 = hashlib.md5(bytes(sig)).hexdigest()[:8]
            dest = os.path.join(_settle_queue_dir(), sig8 + ".bmp")
            try:
                import shutil
                try:
                    if os.path.exists(dest):
                        os.remove(dest)
                    os.link(src_frame, dest)   # v877 — held freezes link, not copy
                except Exception:
                    shutil.copy2(src_frame, dest)
            except Exception:
                return
            _SETTLE_QUEUE.append({"path": dest, "sig": sig, "ts": now,
                                  "interest": round(float(interest), 3), "priority": bool(priority),
                                  "origin": str(origin or "settle")})
            while len(_SETTLE_QUEUE) > SETTLE_QUEUE_CAP:   # newest freeze evicts the oldest held view
                _settle_file_del(_SETTLE_QUEUE.pop(0))
    except Exception:
        pass

def _settle_drain_pop():
    """Pop the NEWEST held freeze (most-current view). Stale entries (>SETTLE_QUEUE_STALE_MS)
    are dropped first with a `cap` ev; the remaining older views are superseded, so their files
    are cleaned too. Returns the entry dict (its snapshot file still on disk) or None."""
    now = int(time.time() * 1000)
    with _settle_q_lock:
        fresh, dropped = [], 0
        for e in _SETTLE_QUEUE:
            if now - e["ts"] > SETTLE_QUEUE_STALE_MS:
                _settle_file_del(e); dropped += 1
            else:
                fresh.append(e)
        _SETTLE_QUEUE[:] = fresh
        if dropped:
            ev("cap", "settle-queue — dropped %d stale freeze(s) (>%ds) before a read freed up"
               % (dropped, SETTLE_QUEUE_STALE_MS // 1000))
        if not _SETTLE_QUEUE:
            return None
        entry = _SETTLE_QUEUE.pop()      # newest = most-current view
        for e in _SETTLE_QUEUE:          # older held views are moot now — clean their files
            _settle_file_del(e)
        _SETTLE_QUEUE[:] = []
        return entry

def _settle_queue_clear():
    """v825 — the queue dies with the session (farewell/shutdown), _eye_clear-style: drop every
    held file so a fresh ON never drains yesterday's freezes. Never raises."""
    with _settle_q_lock:
        for e in _SETTLE_QUEUE:
            _settle_file_del(e)
        _SETTLE_QUEUE[:] = []
    try:
        d = os.path.join(FRAMES, "queue")
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".bmp"):
                    try: os.remove(os.path.join(d, f))
                    except Exception: pass
    except Exception:
        pass

# ═══ v732 — OCR FAST LANE (Konyo: pile→chip in ~0.1–0.2s; LLM floors at 3–6s)
# Local macOS Vision OCR (warm worker ~10–50ms). Claude stays the deep brain.
# Honesty: OCR names are provisional (review-first, never vault_names) until deep/lifecycle.
OCR_BIN = os.environ.get("TV_OCR_BIN") or os.path.join(HERE, "bin", "ocr_mac")
OCR_WIN_PS1 = os.path.join(HERE, "ocr_win.ps1")   # v818 — cousin twin (Windows.Media.Ocr)


def _ocr_worker_cmd():
    """v818 (Grok R8 #3) — the fast lane exists on BOTH platforms. Mac: ocr_mac --worker.
    Windows: powershell ocr_win.ps1 speaking the SAME stdin-path → stdout-JSON protocol.
    Returns None when no worker is available (fast lane off, vision-only)."""
    if os.environ.get("TV_OCR_BIN"):
        return [os.environ["TV_OCR_BIN"], "--worker"]
    if sys.platform.startswith("win"):
        if os.path.isfile(OCR_WIN_PS1):
            return ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", OCR_WIN_PS1]
        return None
    if os.path.isfile(OCR_BIN) and os.access(OCR_BIN, os.X_OK):
        return [OCR_BIN, "--worker"]
    return None
OCR_ENABLED = os.environ.get("TV_OCR", "1") != "0"

class OcrWorker:
    """Persistent `ocr_mac --worker` — one process, many frames. Stdlib only."""
    def __init__(self):
        self.p = None
        self.q = None
        self.lock = threading.Lock()
        self.ok = False

    def available(self):
        return bool(OCR_ENABLED and _ocr_worker_cmd() is not None)   # v818 — platform-aware

    def _spawn(self):
        import queue
        if not self.available():
            self.ok = False
            return False
        try:
            cmd = _ocr_worker_cmd()
            if not cmd:
                self.ok = False
                return False
            self.p = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, bufsize=1)
            self.q = queue.Queue()
            def _pump(proc, q):
                try:
                    for line in proc.stdout:
                        q.put(line)
                except Exception:
                    pass
                q.put(None)
            threading.Thread(target=_pump, args=(self.p, self.q), daemon=True).start()
            self.ok = True
            return True
        except Exception:
            self.ok = False
            self.p = None
            return False

    def stop(self):
        p = self.p
        self.p = None
        self.ok = False
        if not p:
            return
        try:
            if p.poll() is None:
                try:
                    if p.stdin:
                        p.stdin.write("quit\n")
                        p.stdin.flush()
                except Exception:
                    pass
                try:
                    p.kill()
                except Exception:
                    pass
            try:
                p.wait(timeout=2)
            except Exception:
                pass
            for stream in (p.stdin, p.stdout, p.stderr):
                try:
                    if stream:
                        stream.close()
                except Exception:
                    pass
        except Exception:
            pass

    def read(self, path, timeout=1.2):
        """Return {ms, lines, confs, mode} or None. Never raises into the scan loop."""
        with self.lock:
            try:
                if self.p is None or self.p.poll() is not None:
                    self.stop()
                    if not self._spawn():
                        return None
                ap = os.path.abspath(path)
                self.p.stdin.write(ap + "\n")
                self.p.stdin.flush()
                deadline = time.time() + timeout
                while time.time() < deadline:
                    try:
                        line = self.q.get(timeout=max(0.05, deadline - time.time()))
                    except Exception:
                        break
                    if line is None:
                        self.stop()
                        return None
                    line = (line or "").strip()
                    if not line:
                        continue
                    try:
                        j = json.loads(line)
                    except Exception:
                        continue
                    if isinstance(j, dict) and "lines" in j:
                        return j
                self.stop()
                return None
            except Exception:
                self.stop()
                return None

_OCR = OcrWorker()

# HUD / shell noise that is never a D2 item label
_OCR_NOISE = (
    "http", "localhost", "claude", "python", "terminal", "settings", "safari",
    "chrome", "wrangler", "github", "localhost", "127.0.0.1", "subscription",
    "screenshot", "screencapture", "grok", "cursor", "vscode",
)

def filter_ocr_lines(lines):
    """Keep item-ish strings; drop UI chrome. Board vocab does the real route match."""
    out, seen = [], set()
    for raw in lines or []:
        s = str(raw or "").strip()
        if len(s) < 3 or len(s) > 48:
            continue
        lo = s.lower()
        if lo in seen:
            continue
        if any(n in lo for n in _OCR_NOISE):
            continue
        if sum(c.isdigit() for c in s) > max(3, len(s) // 2):
            continue
        # need at least one letter run of 2+
        if not any(len(p) >= 2 and p.isalpha() for p in lo.replace("'", " ").split()):
            continue
        seen.add(lo)
        out.append(s)
        if len(out) >= 16:
            break
    return out

def ocr_fast(path):
    """Fast lane: local OCR → provisional names. Target warm p50 < 50ms, p99 < 200ms."""
    if not OCR_ENABLED or os.environ.get("TV_OCR") == "0":
        return None
    t0 = time.time()
    raw = _OCR.read(path)
    wall = int((time.time() - t0) * 1000)
    if not raw:
        return None
    _raw_lines = [str(x)[:60] for x in (raw.get("lines") or [])][:40]
    lines = filter_ocr_lines(raw.get("lines") or [])
    _kept = set(lines)
    _ocr_dropped = [{"line": x, "why": "line-filter"} for x in _raw_lines if x not in _kept][:20]
    confs = raw.get("confs") or []
    avg_c = None
    if confs:
        try:
            avg_c = round(sum(float(c) for c in confs[: len(lines) or 1]) / max(1, min(len(confs), max(1, len(lines)))), 3)
        except Exception:
            avg_c = None
    return {
        "names": lines,
        "raw_lines": _raw_lines,        # v853 (A2.7) — what the OCR literally saw
        "dropped": _ocr_dropped,        # v853 — what the line-filter ate, with why
        "ms": int(raw.get("ms") or wall),
        "wall_ms": wall,
        "conf": avg_c if avg_c is not None else 0.45,
        "mode": "ocr",
        "lane": "ocr",
        "model": "ocr-mac",
        "scene": "loot",          # provisional — deep lane will set real scene
        "area": "",
        "tz": [],
        "intent": "seen",         # never farmed from OCR alone
        "provisional": True,
        "escalated": False,
        "raw_n": len(raw.get("lines") or []),
    }

_REWARM_T = [0.0]        # legacy compat (unused by the pool path)
_REWARM_AT = {}          # v863 — per-worker last-rewarm ts (id(worker) -> time), independent debounce
def _rewarm(worker=None):
    """v863 — after a reader death/throttle, quietly warm THAT slot's fresh session (60s
    per-worker debounce). One-shot is a bridge; a degraded reader recovers on its own without
    ever stalling the other 7. Defaults to worker 0 for old callers."""
    w = worker or _WORKER
    key = id(w)
    if time.time() - _REWARM_AT.get(key, 0.0) < 60: return
    _REWARM_AT[key] = time.time()
    def _run():
        t0 = time.time()
        try:
            if w.ask("Reply with exactly: ok", timeout=60) is not None:
                ev("boot", f"vision re-warmed in {int(time.time()-t0)}s — that reader is fast again")
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()

_STASH_TABS = frozenset(("personal", "shared", "gems", "materials", "runes"))
_STASH_TAB_ALIASES = {
    "rune": "runes", "runes": "runes",
    "gem": "gems", "gems": "gems",
    "mat": "materials", "mats": "materials", "material": "materials", "materials": "materials",
    "personal": "personal", "shared": "shared",
}

def _norm_stash_tab(raw, scene=None):
    """v734 — active RotW stash tab, or \"\" if not stash / unknown."""
    if scene is not None and scene != "stash":
        return ""
    lo = str(raw or "").strip().lower()
    if not lo:
        return ""
    # allow "Runes Tab" / "Materials stash"
    for key in ("materials", "material", "runes", "rune", "gems", "gem", "personal", "shared"):
        if key in lo:
            return _STASH_TAB_ALIASES.get(key, key if key in _STASH_TABS else "")
    return _STASH_TAB_ALIASES.get(lo, "") if lo in _STASH_TAB_ALIASES else ""

def _parse_read(out):
    """extract + normalize the read JSON from model text; None if no JSON object found.
    v794 (Grok R5 #4) — first-{ to last-} dies on worker chatter/truncation around the real
    payload. Scan for BALANCED candidate objects (right-to-left) and take the first that
    parses AND looks like a read (has a known key).
    v835 (Grok addendum A2.2) — PARSE AUDIT: every clamp/normalize/drop is recorded so SIM
    shows what the model SAID vs what survived (silent clamps burned us before: v769)."""
    j = None
    _audit = {"ok": False, "strategy": "none", "rawLen": len(out or ""), "dropped": [], "normalized": []}
    try:
        a, b = out.find("{"), out.rfind("}")
        if a < 0 or b <= a:
            return None
        try:
            j = json.loads(out[a:b + 1])
            _audit["strategy"] = "first-last"
        except Exception:
            j = None
        if j is None:
            # right-to-left balanced scan: the REAL payload is usually the last clean object
            starts = [k for k, ch in enumerate(out) if ch == "{"]
            for st in reversed(starts):
                depth = 0
                for k in range(st, len(out)):
                    if out[k] == "{":
                        depth += 1
                    elif out[k] == "}":
                        depth -= 1
                        if depth == 0:
                            try:
                                cand = json.loads(out[st:k + 1])
                                if isinstance(cand, dict) and any(x in cand for x in ("names", "scene", "area", "conf")):
                                    j = cand
                                    _audit["strategy"] = "balanced"
                            except Exception:
                                pass
                            break
                if j is not None:
                    break
        if not isinstance(j, dict):
            return None
    except Exception:
        return None
    _names_raw = j.get("names")
    if not isinstance(_names_raw, (list, tuple)):   # v877 fuzz — null/str names crashed or char-split
        if _names_raw not in (None, [], ""):
            _audit["dropped"].append({"field": "names", "why": "not-a-list", "from": str(_names_raw)[:40]})
        _names_raw = []
    _all_names = [str(x).strip() for x in _names_raw if str(x).strip()]
    names = _all_names[:60]
    if len(_all_names) > 60:
        _audit["dropped"].append({"field": "names", "why": "truncated-at-60", "count": len(_all_names) - 60})
    _scene_raw = str(j.get("scene", "gameplay")).lower()
    scene = _scene_raw
    if scene not in ("town", "loot", "inventory", "stash", "gameplay", "transition"):
        _audit["normalized"].append({"field": "scene", "from": _scene_raw, "to": "gameplay", "why": "unknown-scene-clamp"})
        scene = "gameplay"   # v769 — transition is a REAL scene (the parse was silently killing v746)
    _tz_raw = j.get("tz")
    if not isinstance(_tz_raw, (list, tuple)):
        _tz_raw = []
    tz = [str(x).strip()[:40] for x in _tz_raw if str(x).strip()][:8]
    conf = j.get("conf", None)
    try:
        _conf_raw = conf
        conf = float(conf) if conf is not None else None
        if conf is not None:
            if conf < 0.0 or conf > 1.0:
                _audit["normalized"].append({"field": "conf", "from": str(_conf_raw)[:12], "to": str(max(0.0, min(1.0, conf))), "why": "clip-0-1"})
            conf = max(0.0, min(1.0, conf))
    except Exception:
        conf = None
        _audit["dropped"].append({"field": "conf", "from": str(_conf_raw)[:12], "why": "not-a-number"})
    stash_tab = _norm_stash_tab(j.get("stashTab") or j.get("stash_tab"), scene)
    discovered = [str(x).strip() for x in (j.get("discovered") or []) if str(x).strip()][:12]
    names_loc = {}
    try:
        raw_loc = j.get("names_loc") or {}
        if isinstance(raw_loc, dict):
            for k2, v2 in list(raw_loc.items())[:60]:
                v2 = str(v2).strip().lower()
                if v2 in ("equipped", "inventory", "stash", "floor"):
                    names_loc[str(k2).strip()] = v2
                else:
                    _audit["dropped"].append({"field": "names_loc." + str(k2)[:30], "from": v2[:20], "why": "invalid-loc"})
    except Exception:
        names_loc = {}
    return {"area": str(j.get("area", "")).strip()[:48], "scene": scene, "names": names,
            "tz": tz, "conf": conf, "stashTab": stash_tab,
            "discovered": discovered,
            "names_loc": names_loc,
            "_parse_audit": dict(_audit, ok=True)}   # v835 — what the model SAID vs what survived

def _intent_for(scene):
    """v723 — loot lifecycle: floor labels = seen (not farmed); inv/stash = farmed for real."""
    if scene in ("inventory", "stash"): return "farmed"
    if scene == "loot": return "seen"
    return "context"

# ═══ v731 — COMMITMENT VAULT (Konyo: ID→throw must NOT vault)
# floor SEEN → inv HOLDING (pending) → vault only after HOLD_MS still in bag OR town STASH
# drop to floor again = THROW-OUT (cancel pending / reverse mistaken vault)
# GONE alone never vaults. Junk never vaults. Anchors never vault.
# ═══ v738 — RUN #4 FIX (Konyo: Colossus Crossbow + Jewel)
# Stash panel must NOT vault random tooltip text (Blood Shield / Compendium / Unidentified).
# Stash-commit ONLY if name was SEEN (floor), HOLDING (inv), or gone-candidate this session.
# Never vault "Unidentified" / bare generics without a chain.
try:
    HOLD_MS = max(5000, int(os.environ.get("TV_HOLD_MS", "30000")))  # 30s default hold
except Exception:
    HOLD_MS = 30000

_JUNK_SUBSTR = (
    "healing potion", "mana potion", "rejuv", "rejuvenation", "stamina potion",
    "antidote potion", "thawing potion", "energy potion", "rancid", "bile", "gas potion",
    "arrows", "bolts", "quill", " gold",
)
# Bare / vision-fluff labels that must never auto-vault without a real identity chain
_WEAK_EXACT = frozenset({
    "jewel", "ring", "amulet", "shield", "armor", "sword", "bow", "helm", "boots",
    "gloves", "belt", "item", "charm", "scrollof", "scroll", "tome", "key",
    "superior", "ethereal", "unidentified", "unid", "great", "super", "greater",
    "waypoint", "portal",
})
def _norm_name(n):
    s = str(n or "").strip().lower()
    if s.endswith(")") and "(" in s:
        s = s[:s.rfind("(")].strip()
    # v796 (Grok R5 #3) — floor says 'Superior Colossus Crossbow', panel says 'Colossus
    # Crossbow': same physical item, two ledger keys, broken chain. Strip leading quality
    # prefixes (compound-safe, repeatable).
    for _ in range(2):
        for pre in ("ethereal ", "superior ", "eth "):
            if s.startswith(pre):
                s = s[len(pre):]
    return s

def _is_anchor(n):
    lo = _norm_name(n)
    return any(a in lo for a in (
        "horadric cube", "tome of town portal", "tome of identify",
    ))

def _is_junk(n):
    lo = _norm_name(n)
    if lo in ("arrows", "bolts", "key", "gold") or lo.endswith(" gold") or lo.isdigit():
        return True
    if lo.endswith("gold") and any(c.isdigit() for c in lo):
        return True
    return any(j in lo for j in _JUNK_SUBSTR)

def _is_never_vault(n):
    """Hard ban — never farmed/vaulted even if 'seen' as label (run #4 Unidentified)."""
    lo = _norm_name(n)
    if not lo:
        return True
    if "unidentified" in lo or lo in ("unid", "unidentified item"):
        return True
    if lo in ("waypoint", "portal", "identify", "repair"):
        return True
    return False

def _is_weak_name(n):
    """Too generic alone — only stash-commits if already SEEN/HOLDING/candidate."""
    lo = _norm_name(n)
    if _is_never_vault(n):
        return True
    if lo in _WEAK_EXACT:
        return True
    # single short token with no space (e.g. OCR crumbs)
    if " " not in lo and len(lo) < 5:
        return True
    return False

def _area_key(a):
    return str(a or "").strip().lower()

def _is_town_area(area):
    lo = _area_key(area)
    return any(t in lo for t in (
        "rogue encampment", "lut gholein", "kurast docks", "kurast",
        "pandemonium fortress", "harrogath", "town",
    ))

class LootLifecycle:
    """Object permanence + commitment: pending hold → vault; throw-out cancels."""
    def __init__(self):
        self.seen = {}           # floor ledger
        self.candidates = {}     # gone-from-floor pickup candidates
        self.pending = {}        # inv-held, NOT vaulted yet {name, firstHeld, lastHeld, tag}
        self.vaulted = {}        # committed {name, reason, ts}
        self.thrown = []         # ring of throw-out events
        self.confirmed = []      # ring of vault commits

    def restore(self, snap, keyfn):
        """v768 (Grok R2) — the lifecycle survives OFF→ON/crash restarts: rehydrate the chain
        from the last persisted snapshot so a stash read after a restart still finds its
        floor-proven names (no more 'stash-no-chain' for items the run honestly SAW)."""
        try:
            now_ms = int(time.time() * 1000)
            for v in (snap.get("seen") or []):
                n = v.get("name");  k = keyfn(n)
                if n and k not in self.seen:
                    self.seen[k] = {"name": n, "area": v.get("area", ""), "ts": now_ms}
            for v in (snap.get("pending") or []):
                n = v.get("name");  k = keyfn(n)
                if n and k not in self.pending:
                    self.pending[k] = {"name": n, "firstHeld": now_ms, "lastHeld": now_ms,
                                       "tag": v.get("tag", "")}
            for v in (snap.get("candidates") or []):
                n = v.get("name");  k = keyfn(n)
                if n and k not in self.candidates:
                    self.candidates[k] = {"name": n, "ts": now_ms}
            for v in (snap.get("vaulted") or []):
                n = v.get("name");  k = keyfn(n)
                if n and k not in self.vaulted:
                    self.vaulted[k] = {"name": n, "reason": v.get("reason", ""), "ts": now_ms}
            return True
        except Exception:
            return False

    def snapshot(self):
        return {
            "holdMs": HOLD_MS,
            "pending": [{"name": v["name"], "heldMs": 0, "tag": v.get("tag", "")}
                        for v in list(self.pending.values())[-40:]],
            "vaulted": [{"name": v["name"], "reason": v.get("reason", "")}
                        for v in list(self.vaulted.values())[-40:]],
            "seen": [{"name": v["name"], "area": v.get("area", "")}
                     for v in list(self.seen.values())[-40:]],
            "candidates": [{"name": v["name"]} for v in self.candidates.values()],
            "thrown": self.thrown[-20:],
            "confirmed": self.confirmed[-40:],
        }

    def process(self, scene, names, area, conf, now_ms=None, names_loc=None):
        now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
        names = [str(n).strip() for n in (names or []) if str(n).strip()]
        # v830 (Konyo forensics) — LOCATION TRUTH: equipped gear is the player's OWN worn kit
        # (never vault, never hold — tag only); an inventory-side tooltip while the stash is
        # open is HELD loot (hold flow), not a stash commit.
        names_loc = names_loc or {}
        equipped = [n for n in names if names_loc.get(n) == "equipped"]
        inv_side = [n for n in names if names_loc.get(n) == "inventory"]
        if equipped:
            names = [n for n in names if n not in equipped]
        out = {
            "vault_names": [],      # ONLY these may hit tvVaultRegister
            "pending_names": [],    # holding — show HOLDING, not vault
            "thrown_names": [],
            "farmed_names": [],     # alias of vault_names for board compat
            "lifecycle_tags": {},
            "anchor": "n/a",
            "gone_candidates": [],
        }
        if scene == "loot":
            self._on_loot(names, area, now_ms, out)
        elif scene == "inventory":
            self._on_inventory(names, area, conf, now_ms, out)
        elif scene == "stash":
            # v830 — inventory-side names route to the HOLD flow; only true stash-panel
            # names may commit to the vault.
            if inv_side:
                stash_side = [n for n in names if n not in inv_side]
                self._on_inventory(inv_side, area, conf, now_ms, out)
                self._on_stash(stash_side, area, conf, now_ms, out)
            else:
                self._on_stash(names, area, conf, now_ms, out)
        # refresh pending heldMs for snapshot consumers
        for k, p in self.pending.items():
            p["heldMs"] = max(0, now_ms - p["firstHeld"])
        for n in equipped:
            out["lifecycle_tags"][n] = "equipped"   # v830 — worn gear: tag only, chronicle-tally on the board
        out["farmed_names"] = list(out["vault_names"])
        out["pending_names"] = [p["name"] for p in self.pending.values()]
        return out

    def _has_chain(self, n):
        """v738 — floor SEEN, inv HOLDING, or gone-candidate this session."""
        k = _norm_name(n)
        return bool(k) and (k in self.seen or k in self.pending or k in self.candidates)

    def _commit(self, n, reason, now_ms, out, tag=None):
        k = _norm_name(n)
        if k and n not in (out.get("chain") or {}):
            out.setdefault("chain", {})[n] = self._chain_snapshot(k, n)   # v856 — hold-commit path snapshots pre-pop
        if not k or _is_junk(n) or _is_anchor(n) or _is_never_vault(n):
            if _is_never_vault(n) and not _is_anchor(n) and not _is_junk(n):
                out["lifecycle_tags"][n] = "skip-weak"
            return
        if k in self.vaulted:
            # v796 (Grok R5 #3) — MULTISET: a SECOND physical drop of the same name re-enters
            # the chain (commit cleared its provenance, so seen/candidates/pending presence
            # means a genuinely new sighting). Re-vault + count. No fresh provenance = the
            # same instance echoing → still already-vaulted.
            if not (k in self.seen or k in self.candidates or k in self.pending):
                out["lifecycle_tags"][n] = "already-vaulted"
                return
            v = self.vaulted[k]
            v["count"] = int(v.get("count") or 1) + 1
            v["ts"] = now_ms
            self.pending.pop(k, None); self.candidates.pop(k, None); self.seen.pop(k, None)
            self.confirmed.append({"ts": now_ms, "name": n, "reason": reason, "tag": tag or reason, "instance": v["count"]})
            del self.confirmed[:-80]
            out["vault_names"].append(n)
            out["lifecycle_tags"][n] = "vault:" + reason + " ×" + str(v["count"])
            return
        self.vaulted[k] = {"name": n, "reason": reason, "ts": now_ms, "count": 1}
        self.pending.pop(k, None)
        self.candidates.pop(k, None)
        self.seen.pop(k, None)   # v796 — commit consumes provenance; only a FRESH sighting re-vaults
        self.confirmed.append({"ts": now_ms, "name": n, "reason": reason, "tag": tag or reason})
        del self.confirmed[:-80]
        out["vault_names"].append(n)
        out["lifecycle_tags"][n] = "vault:" + reason

    def _throw_out(self, n, now_ms, out, why="dropped"):
        k = _norm_name(n)
        if not k:
            return
        was_pending = k in self.pending
        was_vaulted = k in self.vaulted
        self.pending.pop(k, None)
        self.candidates.pop(k, None)
        if was_vaulted:
            self.vaulted.pop(k, None)
            out.setdefault("unvault_names", []).append(n)
        if was_pending or was_vaulted:
            self.thrown.append({"ts": now_ms, "name": n, "why": why})
            del self.thrown[:-40]
            out["thrown_names"].append(n)
            out["lifecycle_tags"][n] = "throw-out"

    def _on_loot(self, names, area, now_ms, out):
        present = {}
        for n in names:
            if _is_anchor(n) or _is_junk(n):
                if _is_junk(n):
                    out["lifecycle_tags"][n] = "junk"
                continue
            if _is_never_vault(n):
                out["lifecycle_tags"][n] = "skip-weak"
                continue
            k = _norm_name(n)
            if not k:
                continue
            present[k] = n
            # THROW-OUT: was holding or vaulted, now on floor again
            if k in self.pending or k in self.vaulted:
                self._throw_out(n, now_ms, out, why="floor-again")
            e = self.seen.get(k)
            if not e:
                self.seen[k] = {"name": n, "area": area or "", "firstSeen": now_ms,
                                "lastSeen": now_ms, "count": 1, "miss": 0}
            else:
                e["lastSeen"] = now_ms
                e["count"] = e.get("count", 0) + 1
                e["miss"] = 0
                if area:
                    e["area"] = area
            if n not in out["lifecycle_tags"]:
                out["lifecycle_tags"][n] = "seen"
        ak = _area_key(area)
        if not ak:
            return
        for k, e in list(self.seen.items()):
            if _area_key(e.get("area")) != ak or k in present:
                continue
            e["miss"] = e.get("miss", 0) + 1
            if e["miss"] == 1:
                continue
            self.candidates[k] = {"name": e["name"], "area": e.get("area", ""), "goneAt": now_ms}
            out["gone_candidates"].append(e["name"])
            out["lifecycle_tags"][e["name"]] = "gone-candidate"

    def _track_pending(self, n, tag, now_ms, out):
        k = _norm_name(n)
        if not k:
            return
        if k in self.vaulted and not (k in self.seen or k in self.candidates):
            out.setdefault("chain", {})[n] = self._chain_snapshot(k, n)   # v856 — echo path snapshots too
            out["lifecycle_tags"][n] = "already-vaulted"   # v796 — fresh floor provenance may hold a 2nd instance
            return
        if _is_never_vault(n):
            out["lifecycle_tags"][n] = "skip-weak"
            return
        p = self.pending.get(k)
        if not p:
            self.pending[k] = {"name": n, "firstHeld": now_ms, "lastHeld": now_ms, "tag": tag}
            out["lifecycle_tags"][n] = "holding"
        else:
            p["lastHeld"] = now_ms
            p["name"] = n
            held = now_ms - p["firstHeld"]
            if held >= HOLD_MS:
                self._commit(n, "hold", now_ms, out, tag=p.get("tag") or tag)
            else:
                out["lifecycle_tags"][n] = "holding"
                out.setdefault("_holding_ms", {})[n] = held

    def _on_inventory(self, names, area, conf, now_ms, out):
        anchors_hit = [n for n in names if _is_anchor(n)]
        out["anchor"] = "ok" if anchors_hit else "missing"
        low_conf = out["anchor"] == "missing" and (conf is None or conf < 0.75)
        present = set()
        for n in names:
            if _is_anchor(n):
                out["lifecycle_tags"][n] = "anchor"
                continue
            if _is_junk(n):
                out["lifecycle_tags"][n] = "junk"
                continue
            k = _norm_name(n)
            if not k:
                continue
            present.add(k)
            if low_conf:
                out["lifecycle_tags"][n] = "hold-low-conf"
                out["apply_held"] = "anchor-missing"
                continue
            was_cand = k in self.candidates
            was_seen = k in self.seen
            if was_cand:
                tag = "seen→gone→inventory"
            elif was_seen:
                tag = "seen→inventory"
            else:
                tag = "inventory-only"
            self._track_pending(n, tag, now_ms, out)
        # pending items missing from inv — not throw-out yet (may be stash/cube); leave pending
        # (throw-out only when we SEE them on the floor again)
        for k, p in list(self.pending.items()):
            if k not in present and k not in self.vaulted:
                # keep pending; user may have put in cube or closed panel mid-ID
                pass

    def _chain_snapshot(self, k, n):
        """v855 (A2.4) — provenance AT DECISION TIME, so 'stash-no-chain' is diagnosable:
        never-seen vs seen-then-lost vs already-owned. Journaled with the read."""
        c = {"seen": k in self.seen, "pending": k in self.pending,
             "candidate": k in self.candidates, "vaulted": k in self.vaulted}
        try:
            e = self.seen.get(k) or {}
            if e.get("firstSeen"):
                c["firstSeen"] = e["firstSeen"]
                c["seenArea"] = e.get("area", "")
                c["seenCount"] = e.get("count", 1)
            p = self.pending.get(k) or {}
            if p.get("firstHeld"):
                c["firstHeld"] = p["firstHeld"]
            v = self.vaulted.get(k) or {}
            if v.get("ts"):
                c["vaultedTs"] = v["ts"]
                c["vaultCount"] = v.get("count", 1)
        except Exception:
            pass
        # v856 (Grok R18a) — one-glance failure class, closed enum
        if c["vaulted"] and not (c["seen"] or c["pending"] or c["candidate"]):
            c["class"] = "wiped-by-commit"
        elif c["pending"]:
            c["class"] = "hold-chain"
        elif c["seen"] or c["candidate"]:
            c["class"] = "full-chain"
        else:
            c["class"] = "never-seen"
        c["path"] = ("seen→gone→stash" if c["candidate"] else
                     "holding→stash" if c["pending"] else
                     "seen→stash" if c["seen"] else "")
        return c

    def _on_stash(self, names, area, conf, now_ms, out):
        # v738 — stash-commit ONLY with object-permanence chain (SEEN / HOLDING / candidate).
        # Panel-greedy vault of random shared-tab tooltips caused run #4 false farmed.
        out["anchor"] = "ok" if names else "missing"
        out.setdefault("chain", {})
        for n in names:
            if _is_anchor(n):
                out["lifecycle_tags"][n] = "anchor"
                continue
            if _is_junk(n):
                out["lifecycle_tags"][n] = "junk"
                continue
            if _is_never_vault(n):
                out["lifecycle_tags"][n] = "skip-weak"
                continue
            k = _norm_name(n)
            if not k:
                continue
            out["chain"][n] = self._chain_snapshot(k, n)   # v855 — provenance at the moment of decision
            if k in self.vaulted and not (k in self.candidates or k in self.seen or k in self.pending):
                out["lifecycle_tags"][n] = "already-vaulted"   # v796 — a fresh 2nd instance flows to _commit instead
                continue
            was_cand = k in self.candidates
            was_seen = k in self.seen
            was_pend = k in self.pending
            if not (was_cand or was_seen or was_pend):
                # no floor/inv provenance this session — do NOT vault (Blood Shield class)
                out["lifecycle_tags"][n] = "stash-no-chain"
                continue
            if was_cand:
                tag = "seen→gone→stash"
            elif was_pend:
                tag = "holding→stash"
            elif was_seen:
                tag = "seen→stash"
            else:
                tag = "stash-commit"
            self._commit(n, "stash", now_ms, out, tag=tag)

_LIFECYCLE = LootLifecycle()

def _read_score(rd):
    if not rd: return -1
    conf = rd.get("conf")
    if conf is None: conf = 0.5
    return len(rd.get("names") or []) * 10 + conf * 10 + (2 if rd.get("area") else 0)

def _needs_escalate(rd):
    """Haiku → Sonnet when accuracy is suspect. Empty gameplay/town is honest, not a miss."""
    if rd is None: return True
    conf = rd.get("conf")
    scene = rd.get("scene") or "gameplay"
    names = rd.get("names") or []
    # ground loot should show labels if the player paused on a pile
    if scene == "loot" and not names: return True
    # any claimed names with low conf — recheck before we trust them
    if names and conf is not None and conf < 0.55: return True
    # farmed panels with shaky conf on non-empty claims — recheck before auto-vault
    if scene in ("inventory", "stash") and names and conf is not None and conf < 0.7: return True
    return False

_ONESHOT_GATE = threading.Semaphore(1)   # v864 — a throttled pool must not herd 8 oneshots
_ASK_NONE_STREAK = 0
def _oneshot(ap, model, timeout=90):
    """v864 — serialized: under subscription throttle all 8 workers can time out together;
    eight parallel one-shot bridges would herd the same throttle. One at a time."""
    if not _ONESHOT_GATE.acquire(timeout=timeout):
        return None
    try:
        return _oneshot_inner(ap, model, timeout)
    finally:
        _ONESHOT_GATE.release()


def _oneshot_inner(ap, model, timeout=90):
    """One cold `claude -p` on subscription (strict-mcp, no API key)."""
    env, stripped = _claude_env()
    _log_auth_once(stripped)
    r = subprocess.run(
        [CLAUDE_BIN, "-p", READ_PROMPT.format(path=ap),
         "--model", model, "--allowedTools", "Read", "--output-format", "text",
         "--strict-mcp-config"],
        capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL, env=env,
        preexec_fn=(None if sys.platform == "win32" else (lambda: os.nice(10))))   # v876
    out = (r.stdout or "").strip()
    a, b = out.find("{"), out.rfind("}")
    if a < 0 or b <= a:
        err = (r.stderr or "").strip()[:160]
        ev("cap", f"vision returned no JSON ({model} exit {r.returncode})" + (f": {err}" if err else ""))
        if r.returncode != 0:
            print(f"  ⚠ claude exit {r.returncode}" + (f": {err}" if err else ""))
        return None
    globals()["_LAST_RAW"] = str(out)[:2048]   # v832 — THE THOUGHT (one-shot lane)
    _pr = _parse_read(out)
    if _pr is not None:
        _pr["_raw_txt"] = str(out)[:2048]
    return _pr

def _maybe_genius(ap, parsed, t0, mode):
    """v723 — automatic Sonnet escalate when Haiku looks weak (session-capped)."""
    if not _needs_escalate(parsed):
        if parsed is not None:
            parsed["ms"] = int((time.time() - t0) * 1000)
            parsed["mode"] = mode
            parsed["model"] = FAST_MODEL
            parsed["intent"] = _intent_for(parsed.get("scene"))
            parsed["escalated"] = False
        return parsed
    if FAST_MODEL == GENIUS_MODEL or ESCALATE_CAP <= 0 or _ESCALATE_N[0] >= ESCALATE_CAP:
        if parsed is not None:
            parsed["ms"] = int((time.time() - t0) * 1000)
            parsed["mode"] = mode
            parsed["model"] = FAST_MODEL
            parsed["intent"] = _intent_for(parsed.get("scene"))
            parsed["escalated"] = False
        return parsed
    _ESCALATE_N[0] += 1
    ev("boot", f"genius escalate → {GENIUS_MODEL} (#{_ESCALATE_N[0]}/{ESCALATE_CAP}) — accuracy pass")
    try:
        better = _oneshot(ap, GENIUS_MODEL, timeout=90)
    except subprocess.TimeoutExpired:
        better = None
        ev("cap", f"genius {GENIUS_MODEL} timed out — keeping {FAST_MODEL} result")
    except Exception as e:
        better = None
        ev("cap", f"genius fail: {e}")
    if better is not None and _read_score(better) >= _read_score(parsed):
        better["ms"] = int((time.time() - t0) * 1000)
        better["mode"] = "genius"
        better["model"] = GENIUS_MODEL
        better["intent"] = _intent_for(better.get("scene"))
        better["escalated"] = True
        return better
    if parsed is not None:
        parsed["ms"] = int((time.time() - t0) * 1000)
        parsed["mode"] = mode
        parsed["model"] = FAST_MODEL
        parsed["intent"] = _intent_for(parsed.get("scene"))
        parsed["escalated"] = False
    return parsed

def claude_read(path, worker=None, out_jpg=None):
    """One vision read on YOUR Claude subscription. Fast model first; genius escalate if needed."""
    # v711 — TV_STUB: the TDD seam. TV_STUB=1 returns canned reads from tv/stub_manifest.json
    # (keyed by frame basename, '*' fallback) — the FULL agent loop runs end-to-end with zero
    # vision cost, in tests and in CI. Never set in real play.
    if os.environ.get("TV_STUB"):
        try:
            man_path = os.environ.get("TV_STUB_MANIFEST") or os.path.join(HERE, "stub_manifest.json")
            with open(man_path, encoding="utf-8") as f: man = json.load(f)
        except Exception:
            man = {}
        base = os.path.basename(path)
        rd = man.get(base) or man.get("*") or {}
        scene = rd.get("scene", "gameplay")
        globals()["_LAST_RAW"] = "«stub read — no model call»"
        return {"area": rd.get("area", ""), "scene": scene,
                "names": rd.get("names", []), "tz": rd.get("tz", []),
                "conf": rd.get("conf", 1.0), "intent": _intent_for(scene),
                "stashTab": _norm_stash_tab(rd.get("stashTab") or rd.get("stash_tab"), scene),
                "model": "stub", "mode": "stub", "escalated": False, "ms": 0}
    ap = _readable_frame(os.path.abspath(path), out_jpg)
    EMPTY = {"area": "", "scene": "gameplay", "names": [], "tz": [], "conf": None,
             "intent": "context", "stashTab": "",
             "model": FAST_MODEL, "mode": "empty", "escalated": False, "ms": 0}
    if not os.path.isfile(ap):
        print(f"  ⚠ image missing: {ap}")
        return EMPTY
    t0 = time.time()
    w = worker or _WORKER
    out_w = w.ask(READ_PROMPT.format(path=ap))
    if out_w is not None:
        globals()["_LAST_RAW"] = str(out_w)[:2048]   # v832 — THE THOUGHT, verbatim (single-reader compat)
        _raw_local = str(out_w)[:2048]
        parsed = _parse_read(out_w)
        if parsed is not None:
            parsed["_raw_txt"] = _raw_local   # v864 — raw travels WITH the result, no global race
        if parsed is not None:
            return _maybe_genius(ap, parsed, t0, "warm") or EMPTY
        ev("cap", "worker returned non-JSON — falling back to one-shot")
    else:
        ev("skip", "vision worker died (timeout/stream end) — one-shot for this read, re-warming behind it")
        _rewarm(w)  # v718 (Grok R10 pick #2) + v863: rewarm THIS reader's slot only, pool degrades soft
    try:
        parsed = _oneshot(ap, FAST_MODEL, timeout=90)
        if parsed is None:
            return EMPTY
        return _maybe_genius(ap, parsed, t0, "oneshot") or EMPTY
    except subprocess.TimeoutExpired:
        ev("cap", "vision timed out (90s) — if this repeats, run: python3 tv/tv_diablo.py --test <img>")
        print("  ⚠ vision timed out (90s)")
        return EMPTY
    except Exception as e:
        ev("cap", f"read failed: {e}")
        print(f"  ⚠ read failed: {e}")
        return EMPTY

def main():
    global _LIFECYCLE, _VISION_BUSY, SESSION_ID
    os.makedirs(FRAMES, exist_ok=True)
    # v840 — clean stuck capture temps (live night left many live.bmp.tmp.* ghosts)
    try:
        for name in os.listdir(FRAMES):
            if ".tmp." in name or name.endswith(".part.jpg") or name.endswith(".part"):
                try:
                    os.remove(os.path.join(FRAMES, name))
                except Exception:
                    pass
    except Exception:
        pass
    _LIFECYCLE = LootLifecycle()
    # v768 (Grok R2) — restart continuity: if the previous run ended within the session window,
    # rehydrate the loot chain so OFF→ON / crash restarts don't orphan floor-proven items.
    try:
        prev = _load()
        prev_ts = 0
        for r in (prev.get("reads") or [])[-1:]:
            prev_ts = r.get("ts") or 0
        if prev_ts and (int(time.time() * 1000) - prev_ts) < 10 * 60 * 1000 and prev.get("lifecycle"):
            if _LIFECYCLE.restore(prev["lifecycle"], _norm_name):
                print("  ♻ lifecycle rehydrated from the last run (%d seen · %d holding)" % (
                    len(_LIFECYCLE.seen), len(_LIFECYCLE.pending)))
    except Exception:
        pass
    SESSION_ID = "s_%d_%d" % (int(time.time() * 1000), os.getpid())
    _VISION_BUSY = False
    with _pool_lock:
        _in_flight.clear()
        _pool_free[:] = list(range(POOL_N))
    with _emit_lock:
        _order_buf[:] = []
    with _state_lock:
        _save({"online": True, "startedAt": int(time.time()*1000), "reads": [], "readCount": 0,
               "cap": SESSION_CAP, "seen": [], "farmed": [], "model": FAST_MODEL, "genius": GENIUS_MODEL,
               "lifecycle": _LIFECYCLE.snapshot(), "sessionId": SESSION_ID, "ver": VERSION})
    bridge()
    try:
        if sys.platform == "darwin":
            os.nice(5)   # v877 (army §2) — the whole agent yields to D2R; workers add nice(10) on top
    except Exception:
        pass
    start_film_thread()
    ev("boot", f"scanner online — session {SESSION_ID} · eyes {POLL_S}s · film ~{int(1/FILM_INTERVAL_S)}fps · fast={FAST_MODEL} · genius={GENIUS_MODEL} · lifecycle v2")
    _known_dead_load()
    if _KNOWN_DEAD: ev("boot", f"{len(_KNOWN_DEAD)} learned transition frame(s) loaded — they cost 0ms now")
    if not os.environ.get("TV_STUB"):
        def _warm():
            # v870 (farm-video run 2: pool cold 60s, reads blind) — the v863 warm was
            # SEQUENTIAL: each reader's boot blocked the next (~8×8s). Now the STARTS stagger
            # 400ms (no login herd) but the boots run in parallel — full pool warm in ~boot+3s.
            t0 = time.time()
            _wt = []
            def _warm_one(_wk):
                try:
                    if _wk.ask("Reply with exactly: ok", timeout=60) is not None:
                        setattr(_wk, "warm_ok", True)
                except Exception:
                    pass
            for i, _wk in enumerate(_WORKERS):
                if i:
                    time.sleep(0.4)
                _t = threading.Thread(target=_warm_one, args=(_wk,), daemon=True)
                _t.start()
                _wt.append(_t)
            for _t in _wt:
                _t.join(timeout=75)
            ok = sum(1 for _wk in _WORKERS if getattr(_wk, "warm_ok", False))
            if ok:
                ev("boot", f"vision warm — {ok}/{POOL_N} reader(s) ready in {int(time.time()-t0)}s (first reads fast)")
            else:
                ev("skip", "warm-up didn't answer — first reads may be slow (one-shot fallback armed)")
        threading.Thread(target=_warm, daemon=True).start()
    if os.environ.get("CLAUDECODE"):
        ev("cap", "⚠ launched INSIDE a Claude session — vision calls can hang. Run me in a bare Terminal.")
        print("  ⚠ you're inside a Claude Code session — claude -p may hang nested. Use a BARE Terminal window.")
    print(f"📺 TV DIABLO Autopilot {VERSION} — TESLA DRIVE · one AI reader · HD film ~{_FILM_FPS}fps")
    print(f"   bridge: http://127.0.0.1:{PORT}/state  ·  mode: {'watch (Windows frames)' if WATCH_MODE else 'mac screencapture'}")
    print("   capture: AUTO (pins D2R.exe only — never CrossOver Home / Battle.net; TV_CAPTURE=full for display)")
    print(f"   models: fast={FAST_MODEL} · genius={GENIUS_MODEL} · gap={MIN_GAP_S}s · priority gap={PRIORITY_GAP_S}s · poll {POLL_S}s")
    print(f"   film: ~{_FILM_FPS}fps · max {FILM_MAX_PX}px · jpeg q{FILM_JPEG_Q} · env TV_FILM_FPS / TV_FILM_MAX_PX / TV_FILM_Q")
    ocr_tag = "ON " + OCR_BIN if _OCR.available() else "OFF (set TV_OCR_BIN or build tv/bin/ocr_mac)"
    print(f"   ocr lane: {ocr_tag} (flash inside the one dual-lane — not a second reader)")
    print("   tip: pause on loot / panels so the screen settles — one Claude deep at a time")
    print("   in the bible: ⚡ session → 📺 TV DIABLO → flip ON. Ctrl-C to stop.\n")
    # v779 — ask for Screen Recording UP FRONT (Python-as-responsible needs its own grant;
    # Terminal's checkbox does not cover the control-app child agent).
    if not WATCH_MODE and sys.platform == "darwin":
        if screen_recording_ok():
            ev("boot", "Screen Recording OK — eye can pin the D2R window")
        else:
            ev("cap", "⚠ Screen Recording DENIED for this Python — open System Settings → Privacy → Screen Recording, enable Python / TV DIABLO, then RESTART")
            open_screen_recording_settings()
            print("  ⚠ Screen Recording not granted to this process — film will stay dark until you enable Python in System Settings → Privacy → Screen Recording")
    ev("boot", f"autopilot {VERSION} — farewell on stop · chain vault · OCR · priority gap {PRIORITY_GAP_S}s")
    if _OCR.available():
        def _warm_ocr():
            try:
                # warm Vision frameworks so first pile isn't cold
                jp = os.path.join(FRAMES, "read.jpg")
                probe = jp if os.path.isfile(jp) else None
                if not probe:
                    # tiny blank jpeg via sips from any existing frame
                    for cand in (os.path.join(FRAMES, "live.bmp"),):
                        if os.path.isfile(cand):
                            probe = cand
                            break
                if probe:
                    r = _OCR.read(probe, timeout=3.0)
                    if r is not None:
                        ev("boot", f"ocr warm — Vision ready ({r.get('ms', '?')}ms probe)")
                    else:
                        ev("skip", "ocr warm failed — fast lane may miss first settle")
            except Exception as e:
                ev("skip", f"ocr warm error: {e}")
        threading.Thread(target=_warm_ocr, daemon=True).start()
    else:
        ev("skip", "ocr binary missing — Claude-only until tv/bin/ocr_mac is built")

    frame = os.path.join(FRAMES, "live.bmp")
    # v870 — last_read_t starts NOW, not 0: the heartbeat's `and last_read_t` guard meant a
    # constant-motion session (his farm video, run 2) stayed BLIND until the first settle read.
    last_md5, stable, last_sent_md5, last_read_t, reads = None, 0, None, time.time(), 0
    peak = 0.0            # recent max motion while hunting
    priority = False      # hard motion seen since last read → short gap + 1-tick settle
    empty_streak = 0
    named_until = 0.0     # boost interest after a named hit

    def _launch_vision(snap_src, cur_snap, n_this, fid_this, interest_this, used_priority, read_ts):
        """v863 READER POOL — one reader ACT on ITS OWN worker + PRIVATE snap/read files. Builds
        the job (captureTs, origin, dispatch, sig) at fire time and carries it through to the
        ordered apply. Acquires a free reader id; the main loop gates on a free slot."""
        global _VISION_BUSY
        import shutil
        rid = _pool_acquire()
        if rid is None:
            # defensive — the main loop only fires with a free slot; hold the freeze instead
            _settle_enqueue(snap_src, cur_snap, interest_this, used_priority, origin="settle")
            return snap_src
        snap_path, read_jpg = _job_files(rid, n_this)
        try:
            try:
                if os.path.exists(snap_path):
                    os.remove(snap_path)
                os.link(snap_src, snap_path)   # v877 (army #8) — 0-byte snapshot vs a 17-60MB copy
            except Exception:
                shutil.copy2(snap_src, snap_path)
        except Exception:
            snap_path = snap_src
        _job_seq[0] += 1
        job_id = "j%d_%d" % (rid, _job_seq[0])
        _base_ctx = dict(globals().get("_DISPATCH_CTX") or {})
        _origin = _base_ctx.get("origin") or "settle"
        _disp = dict(_base_ctx)
        _disp["readerId"] = rid
        _disp["poolN"] = POOL_N
        with _pool_lock:
            _disp["poolInFlight"] = len(_in_flight) + 1
            _in_flight[job_id] = {"readerId": rid, "captureTs": int(read_ts), "sig": cur_snap,
                                  "origin": _origin, "startedAt": int(time.time() * 1000)}
        job = {"n": n_this, "fid": fid_this, "interest": interest_this,
               "priority": used_priority, "dispatch": _disp, "raw": "",
               "captureTs": int(read_ts), "readerId": rid}
        _VISION_BUSY = True
        globals()["_VISION_BUSY_AT"] = time.time()

        def _vision_job():
            nonlocal empty_streak, named_until
            global _VISION_BUSY
            try:
                # ── FAST LANE: local OCR first (same dual-lane, not a second reader) ──
                ocr_rd = ocr_fast(snap_path)
                if ocr_rd is not None:
                    oms = ocr_rd.get("ms") or ocr_rd.get("wall_ms") or 0
                    onames = [n for n in (ocr_rd.get("names") or []) if _itemish(n)]   # v852 — one predicate everywhere; garbage never flashes seen
                    ev("ocr", f"⚡ocr {oms}ms · {len(onames)} name(s)" +
                       ((" — " + ", ".join(onames[:4])) if onames else " — no item-ish text") +
                       f" (raw {ocr_rd.get('raw_n', 0)})")
                    print(f"  ⚡ ocr {oms}ms  {('· ' + ' · '.join(onames[:6])) if onames else '· no item-ish text'}")
                    if onames:
                        with _state_lock:
                            st = _load()
                            st.setdefault("seen", []); st.setdefault("farmed", [])
                            prec = {
                                "ts": read_ts, "names": onames, "n": n_this,
                                "area": "", "scene": "loot", "tz": [],
                                "ms": oms, "mode": "ocr", "lane": "ocr", "model": "ocr-mac",
                                "conf": ocr_rd.get("conf"), "intent": "seen",
                                "escalated": False, "interest": interest_this, "priority": used_priority,
                                "provisional": True,
                                "frameId": fid_this, "sessionId": SESSION_ID,
                                "vault_names": [], "farmed_names": [],
                                "pending_names": [], "thrown_names": [], "unvault_names": [],
                                "lifecycle_tags": {nm: "ocr" for nm in onames},
                                "anchor": "n/a", "gone_candidates": [], "holdMs": HOLD_MS,
                            }
                            st["reads"].append(prec)
                            st["reads"] = st["reads"][-200:]
                            st["readCount"] = n_this
                            st["ap"] = dict(_AP)
                            st["lifecycle"] = _LIFECYCLE.snapshot()
                            for nm in onames:
                                if not _is_anchor(nm) and not _is_junk(nm):
                                    st["seen"].append({"ts": prec["ts"], "name": nm, "area": "", "scene": "loot", "src": "ocr"})
                                    del st["seen"][:-200]
                            _save(st)
                        empty_streak = 0
                        named_until = time.time() + 45
                        _AP["namedStreak"] = _AP.get("namedStreak", 0) + 1
                        _AP["lastNamed"] = ", ".join(onames[:4])

                # ── DEEP LANE: Claude (this reader's OWN worker + private read.jpg) ──
                rd = claude_read(snap_path, worker=_WORKERS[rid], out_jpg=read_jpg)
                job["raw"] = (rd or {}).get("_raw_txt") or globals().get("_LAST_RAW", "") or ""   # v864 — result-carried raw wins; global only as single-reader fallback
                if should_learn_dead(rd):
                    learn_dead_frame(cur_snap)
                # v863 — ORDERED APPLY: buffer this completion; emit only when no OLDER read is
                # still in flight (the floor-before-stash lock). Stragglers apply after ORDER_HOLD_MS.
                if globals().get("_POOL_STOPPING"):
                    return   # v864 — shutdown in progress: release the slot (finally), never apply late
                _order_push(int(read_ts), job, rd, ocr_rd)
                for rec in _order_drain():
                    names = (rec or {}).get("names") or []
                    if names:
                        empty_streak = 0
                        named_until = time.time() + 45
                        _AP["namedStreak"] = _AP.get("namedStreak", 0) + 1
                        _AP["lastNamed"] = ", ".join(names[:4])
                    else:
                        if not (ocr_rd and ocr_rd.get("names")):
                            empty_streak += 1
                            _AP["namedStreak"] = 0
                _AP["emptyStreak"] = empty_streak
            except Exception as e:
                try: ev("cap", "vision job failed: %s" % e)
                except Exception: pass
            finally:
                try:   # v864 (Grok c) — private job files die with the job (BMP×8×reads was disk growth)
                    for _jf in (locals().get("snap_path"), locals().get("read_jpg")):
                        if _jf and isinstance(_jf, str) and ("snap_" in os.path.basename(_jf) or "read_" in os.path.basename(_jf)) and os.path.isfile(_jf):
                            os.remove(_jf)
                except Exception:
                    pass
                with _pool_lock:
                    _in_flight.pop(job_id, None)
                    if rid not in _pool_free:
                        _pool_free.append(rid); _pool_free.sort()
                    _VISION_BUSY = len(_in_flight) >= 1
                _AP["mode"] = "drive"
                beat("watching", 0.0)
                try:
                    _order_drain()   # a slot freed → a held straggler may now apply
                except Exception:
                    pass

        threading.Thread(target=_vision_job, daemon=True, name="tv-vision-r%d" % rid).start()
        return snap_path

    def _fire_read(origin, snap_src, sig, interest_this, used_priority, note="",
                   motion_v=0.0, peak_v=0.0, settle_ticks=0, gap_ms=0,
                   empty_s=0, named_s=0, ap_mode="", interest_parts=None):
        """ONE AI reader arm: settle or queue drain → shared last_read_t + dual-lane."""
        nonlocal last_read_t, last_sent_md5, reads, peak, priority
        soft_over = reads - SESSION_CAP
        if soft_over >= 0:
            time.sleep(min(30.0, 6.0 + soft_over * 0.05))
        last_read_t, last_sent_md5 = time.time(), sig
        globals()["_LAST_EMIT_SIG"] = sig
        reads += 1
        read_ts = int(time.time() * 1000)
        frame_id = archive_read_frame(snap_src, reads, read_ts)
        tag = "⏭ queue" if "queue" in origin else "👁 settle"
        print(f"  {tag} — dual-lane #{reads}/{SESSION_CAP}"
              + (f" · {note}" if note else "")
              + (f" · frame={frame_id}" if frame_id else ""))
        ev("settle", f"{tag} · dual-lane read #{reads}"
           + (f" · {note}" if note else "")
           + (f" · frame {frame_id}" if frame_id else ""))
        beat("reading", 0.0)
        _AP["mode"] = "read"
        # v849 (audit-core #2 · 'no invented data') — a queued freeze was never measured for
        # motion/peak/settle: OMIT them instead of journaling 0.0000 as if measured.
        _ctx = {
            "interest": round(float(interest_this), 3),
            "interestParts": dict(interest_parts or {}),
            "priority": bool(used_priority),
            "gapMs": int(gap_ms),
            "emptyStreak": int(empty_s),
            "namedStreak": int(named_s),
            "apMode": str(ap_mode or origin),
            "queueDepth": len(_SETTLE_QUEUE),
            "frameSrc": "settle-queue" if "queue" in origin else "live",
            "origin": origin,
            "note": note or ("one AI reader — " + origin),
        }
        if "queue" not in origin:
            _ctx.update({"motion": round(float(motion_v), 4), "peak": round(float(peak_v), 4),
                         "settleTicks": int(settle_ticks)})
        else:
            _ctx["note"] = "queued freeze — motion fields n/a by nature"
        globals()["_DISPATCH_CTX"] = _ctx
        used = _launch_vision(snap_src, sig, reads, frame_id, interest_this, used_priority, read_ts)
        if "queue" in origin:
            peak = 0.0
            priority = False
        return used

    while True:
        time.sleep(POLL_S)
        # ── straggler flush + queue drain: freezes held while readers were busy ──
        try: _order_drain()
        except Exception: pass
        _drained_any = False
        while _vision_in_flight_n() < POOL_N and _SETTLE_QUEUE:
            _q = _settle_drain_pop()
            if _q is None:
                break
            if _in_flight_has_sig(_q["sig"]):
                _settle_file_del(_q)   # this exact view is already on a reader
                continue
            used = _fire_read(
                "settle-queue", _q["path"], _q["sig"],
                _q.get("interest", 0.0), bool(_q.get("priority")),
                note="held while readers busy · drained on free",
                gap_ms=max(0, int(time.time() * 1000) - _q.get("ts", 0)),
                ap_mode="queue-drain",
            )
            if used != _q["path"]:
                try: os.remove(_q["path"])
                except Exception: pass
            _drained_any = True
        if _drained_any:
            continue
        if WATCH_MODE:
            # v784 — Windows capture half reports pin status via cap_target.json
            _refresh_cap_target_from_disk()
            f = newest_watched_frame()
            if not f: continue
            frame = f
            # prefer stable live.bmp path for settle when present
            live_bmp = os.path.join(FRAMES, "live.bmp")
            if os.path.isfile(live_bmp):
                frame = live_bmp
        elif not capture_mac(frame):
            if os.environ.get("TV_STUB"):
                # SIM: no Screen Recording on the control app's Python.app — still drive the loop
                if not capture_stub_synth(frame):
                    time.sleep(0.2)
                    continue
                if not globals().get("_STUB_CAP_WARNED"):
                    globals()["_STUB_CAP_WARNED"] = True
                    ev("cap", "SIM synthetic frames — grant Screen Recording to Python for live play")
                    print("  📺 SIM: no Screen Recording for this process — using synthetic frames + canned reads")
            else:
                # v840 — do NOT spam the log every poll (last night: thousands of identical lines)
                now = time.time()
                last = float(globals().get("_PERM_WARN_AT") or 0)
                if now - last > 30:
                    globals()["_PERM_WARN_AT"] = now
                    if not globals().get("_PERM_WARNED"):
                        globals()["_PERM_WARNED"] = True
                        try:
                            screen_recording_ok()
                            open_screen_recording_settings()
                        except Exception:
                            pass
                        ev("cap", "⚠ capture failed — grant Screen Recording to Python / TV DIABLO (System Settings → Privacy → Screen Recording), then RESTART")
                    else:
                        ev("cap", "⚠ capture still failing — Screen Recording / D2R window?")
                    print("  ⚠ screencapture failed (grant Screen Recording to the TV DIABLO / Python app in System Settings → Privacy)")
                time.sleep(0.5)
                continue
        elif (not WATCH_MODE) and os.path.getsize(frame) < 200000:
            if os.environ.get("TV_STUB") and capture_stub_synth(frame):
                if not globals().get("_STUB_CAP_WARNED"):
                    globals()["_STUB_CAP_WARNED"] = True
                    ev("cap", "SIM synthetic frames (tiny capture) — Screen Recording likely missing")
            else:
                if not globals().get("_PERM_WARNED"):
                    globals()["_PERM_WARNED"] = True
                    ev("cap", "capture looks EMPTY — grant Screen Recording to TV DIABLO / Python (System Settings → Privacy) and relaunch")
                    print("  ⚠ capture is suspiciously tiny — screen-recording permission is probably missing")
                continue
        else:
            # v783 — film thread owns eye.jpg; only backfill if film thread is cold
            if not WATCH_MODE and (time.time() - _EYE_PREVIEW_AT) > 1.5:
                try: refresh_eye_preview(frame, min_interval=0.5)
                except Exception: pass
        try: cur = frame_sig(frame)
        except Exception: continue
        motion = sig_diff(cur, last_md5)
        # loading screens between zones are static + near-black — they settle but hold nothing readable
        if sum(cur) / max(1, len(cur)) < 14:
            if _BEAT["phase"] != "loading": ev("skip", "near-black frame (loading screen) — not worth a read")
            beat("loading", motion); last_md5 = cur; peak = 0.0; stable = 0
            _AP.update({"mode": "load", "interest": 0.0, "peak": 0.0}); continue
        # L2 prediction: track motion peaks (drive → stop is the pile/panel moment)
        if motion > peak: peak = motion
        if motion >= MOTION_PEAK:
            priority = True
            if _AP.get("mode") != "hunt":
                _AP["mode"] = "hunt"
        named_recent = time.time() < named_until
        _iparts = {}
        interest = ap_interest(peak, stable, priority, empty_streak, named_recent, parts=_iparts)
        _AP.update({"interest": round(interest, 3), "peak": round(peak, 3), "priority": priority,
                    "emptyStreak": empty_streak, "gap": PRIORITY_GAP_S if priority else MIN_GAP_S})
        # ── all readers busy: queue distinct freezes only (never a duplicate concurrent read) ──
        if _vision_busy():
            beat("reading", motion)
            if motion > SETTLE:
                stable = 0
                last_md5 = cur
            else:
                stable = stable + 1
                last_md5 = cur
                _settle_enqueue(frame, cur, interest, priority, origin="settle")
            continue
        beat("watching", motion)

        # v866 (Konyo live: '4 reads in 149s, zero heartbeats') — the v861 heartbeat was DOUBLY
        # dead after the pool relocation: below the motion-continue (combat never reached it) and
        # behind an always-false stable guard. It lives HERE now — before motion can skip it.
        _hb_static = sig_diff(cur, last_sent_md5) <= SETTLE if last_sent_md5 else False
        if (_vision_in_flight_n() < POOL_N) and (_heartbeat_in_flight_n() < _heartbeat_cap()) \
                and last_read_t and (time.time() - last_read_t) >= HEARTBEAT_S and not _SETTLE_QUEUE \
                and not _in_flight_has_sig(cur) \
                and ((not _hb_static) or (time.time() - last_read_t) >= 10.0):
            _hb_gap = int((time.time() - last_read_t) * 1000)
            reads += 1
            read_ts = int(time.time() * 1000)
            frame_id = archive_read_frame(frame, reads, read_ts)
            ev("heartbeat", f"💓 heartbeat · {_hb_gap//1000}s since last read · dual-lane #{reads} · pool {_vision_in_flight_n()}/{POOL_N}")
            print(f"  💓 heartbeat read #{reads} — {_hb_gap//1000}s since last · pool {_vision_in_flight_n()}/{POOL_N}")
            beat("reading", motion)
            last_read_t = time.time()
            last_sent_md5 = cur
            last_md5 = cur   # v868 (Grok #4) — no phantom motion spike on the next poll
            globals()["_LAST_EMIT_SIG"] = cur
            globals()["_DISPATCH_CTX"] = {"origin": "heartbeat", "apMode": "heartbeat",
                                          "frameSrc": "live", "gapMs": _hb_gap,
                                          "heartbeatS": HEARTBEAT_S,
                                          "motion": round(float(motion), 4), "peak": round(float(peak), 4),
                                          "settleTicks": int(stable),
                                          "priority": bool(priority), "queueDepth": len(_SETTLE_QUEUE),
                                          "note": "forced read — %ds since last (combat/motion)" % (_hb_gap // 1000)}
            _launch_vision(frame, cur, reads, frame_id, 0.6, priority, read_ts)
            continue

        if motion > SETTLE:
            stable = 0
            last_md5 = cur
            if priority: _AP["mode"] = "hunt"
            else: _AP["mode"] = "drive"
            continue
        stable = stable + 1
        last_md5 = cur
        # settle: priority (hard motion→stop) = 1 tick; low-interest = 2 ticks
        need_ticks = 1 if (priority or interest >= 0.55) else 2
        if stable < need_ticks:
            _AP["mode"] = "settle"
            continue
        # v866 — heartbeat moved ABOVE the motion gate (see the watching block)
        if sig_diff(cur, last_sent_md5) <= SETTLE:
            # v795 — OCR-won / Claude-lost views get ONE re-fire instead of a permanent burn
            global _REFIRE_SIG
            if _REFIRE_SIG is not None and sig_diff(cur, _REFIRE_SIG) <= SETTLE:
                _REFIRE_SIG = None
                ev("cap", "🔁 re-reading — OCR saw names the deep read missed")
            else:
                if stable == need_ticks:
                    ev("skip", "settled, but same view I already read — waiting for something new")
                peak = max(0.0, peak * 0.5)
                continue
        # v746 — LEARNED dead frame: local 0ms transition, no vision spend
        if known_dead_match(cur) is not None:
            note = transition_note(LAST_AREA, reads)
            ev("transition", f"⏳ {note} · recognized instantly (learned frame)")
            print(f"  ⏳ {note}  [known frame · 0ms]")
            t_ts = int(time.time() * 1000)
            t_fid = archive_read_frame(frame, reads + 1, t_ts)
            _journal({"ts": t_ts, "n": reads + 1, "scene": "transition", "names": [], "area": "",
                      "frameId": t_fid, "note": note, "transition_from": LAST_AREA, "ms": 0,
                      "mode": "known", "lane": "known", "sessionId": SESSION_ID})
            with _state_lock:
                st = _load()
                st["reads"].append({
                    "ts": t_ts, "names": [], "n": reads + 1, "area": "", "scene": "transition",
                    "tz": [], "ms": 0, "mode": "known", "lane": "known", "model": "learned",
                    "conf": 1.0, "intent": "context", "transition_from": LAST_AREA,
                    "note": note, "frameId": t_fid, "sessionId": SESSION_ID,
                    "escalated": False, "interest": interest, "priority": False,
                    "provisional": False,
                    "vault_names": [], "farmed_names": [], "pending_names": [],
                    "thrown_names": [], "unvault_names": [], "lifecycle_tags": {},
                    "anchor": "n/a", "gone_candidates": [], "holdMs": HOLD_MS,
                })
                st["reads"] = st["reads"][-200:]
                reads += 1
                st["readCount"] = reads
                st["ap"] = dict(_AP)
                _save(st)
            beat("loading", motion)
            _AP["mode"] = "load"
            last_sent_md5 = cur
            peak = 0.0
            priority = False
            continue
        gap = PRIORITY_GAP_S if priority else MIN_GAP_S
        if time.time() - last_read_t < gap:
            if stable == need_ticks:
                ev("skip", f"settled, but only {int(time.time()-last_read_t)}s since last read (gap {gap}s · {'PRIORITY' if priority else 'cruise'})")
            continue
        # v863 — anti double-spend: never fire a view another reader is already reading
        if _in_flight_has_sig(cur):
            if stable == need_ticks:
                ev("skip", "already reading this exact view on another reader — waiting for something new")
            continue
        # soft session throttle — eye never hard-stops
        soft_over = reads - SESSION_CAP
        if soft_over >= 0:
            if soft_over == 0:
                ev("cap", f"soft threshold {SESSION_CAP} reads — cruise throttle on (eye never stops)")
                print(f"  🌙 soft threshold ({SESSION_CAP} reads) — cruising slower, never stopping")
        _d_gap = int((time.time() - last_read_t) * 1000) if last_read_t else 0
        _d_apmode = str(_AP.get("mode", ""))
        used_priority = priority
        used_peak = peak
        used_interest = interest
        used_parts = dict(_iparts)
        peak = 0.0
        priority = False
        _fire_read(
            "settle", frame, cur, used_interest, used_priority,
            note=("PRIORITY " if used_priority else "") + f"interest {used_interest:.2f} · peak {used_peak:.2f}",
            motion_v=motion, peak_v=used_peak, settle_ticks=stable,
            gap_ms=_d_gap, empty_s=empty_streak,
            named_s=1 if named_recent else 0,
            ap_mode=_d_apmode, interest_parts=used_parts,
        )
        continue

def _itemish(name):
    """v848 — OCR garbage gate for the SEED path + short displays ('QvfST L•' reached the
    stage). Item names are wordy: mostly letters, a vowel, no glyph junk. The drawer keeps
    RAW ocr truth — this only guards what gets seeded/headlined."""
    t = str(name or "").strip()
    # v852 (Grok R17) — bare runes are REAL loot names ('Ist', 'Ber', 'Io', 'El'…)
    _RUNES = {"el","eld","tir","nef","eth","ith","tal","ral","ort","thul","amn","sol","shael",
              "dol","hel","io","lum","ko","fal","lem","pul","um","mal","ist","gul","vex","ohm",
              "lo","sur","ber","jah","cham","zod"}
    if t.lower() in _RUNES or t.lower().replace(" rune", "") in _RUNES:
        return True
    if len(t) < 4 or len(t) > 40:
        return False
    if any(c in t for c in "•*&#@$%{}[]<>|\\_=+~^"):
        return False
    letters = sum(1 for c in t if c.isalpha() or c in " '-")
    if letters / max(1, len(t)) < 0.8:
        return False
    if not any(c in "aeiouAEIOU" for c in t):
        return False
    return True


def _pre_triage(deep_names, ocr_rd):
    """v853 (Grok R17 c / A2.3) — the SILENT FILTERS get a journal: every name that hit a
    gate (itemish/junk/anchor/never-vault) is recorded with its verdict, so SIM can prove
    'the gate saved us' vs 'the gate ate a Ber'."""
    pre = []
    seen = set()
    def _gate(n, lane):
        k = (str(n), lane)
        if k in seen:
            return
        seen.add(k)
        if not _itemish(n):
            g = "not-itemish"
        elif _is_junk(n):
            g = "junk"
        elif _is_anchor(n):
            g = "anchor"
        elif _is_never_vault(n):
            g = "never-vault"
        else:
            g = "pass"
        pre.append({"name": str(n)[:48], "gate": g, "lane": lane})
    for n in (deep_names or []):
        _gate(n, "deep")
    for n in ((ocr_rd or {}).get("names") or []):
        _gate(n, "ocr")
    for d in ((ocr_rd or {}).get("dropped") or [])[:12]:
        pre.append({"name": str(d.get("line", ""))[:48], "gate": "ocr-line-filter", "lane": "ocr"})
    return pre[:40]


def _reason_for(tag, loc=""):
    """v836 (SIMULATION_SPEC) — every verdict tag gets a WHY in the owner's language.
    Tags say WHAT the pipeline did; these say WHY, for the SIM decision chain."""
    t = str(tag or "")
    if t == "equipped":
        return "worn gear (unequip tell) — never farms; chronicle tally only"
    if t.startswith("vault:stash"):
        return "seen earlier this session, then read in the stash panel — committed to the vault"
    if t.startswith("vault:"):
        return "committed to the vault (" + t.split(":", 1)[1] + ")"
    if t == "already-vaulted":
        return "this name already vaulted this session and no fresh sighting since — not counted twice"
    if t == "stash-no-chain":
        return "read in the stash but NEVER seen on floor/inventory this session — no provenance, blocked"
    if t == "skip-weak":
        return "matched the never-vault list (junk/basic) — ignored on purpose"
    if t == "seen":
        return "floor label — entered the SEEN ledger, waiting for pickup"
    if t == "ocr-pending":
        return "the fast OCR lane saw it while the deep read missed — floor-seeded, one re-read armed"
    if t == "holding" or "inventory" in t:
        return "in the inventory (" + (t or "holding") + ") — HOLDING until it reaches the stash"
    if t.startswith("throw-out") or t == "floor-again":
        return "seen on the floor AFTER being held/vaulted — treated as thrown out"
    if loc == "inventory":
        return "inventory-side tooltip — holds, never vaults from here"
    return t or "no verdict this frame"


def effective_lc_scene(scene, names):
    """v753 — run-#8 lesson: a pile read Sonnet labels 'gameplay' but NAMES items is loot-class
    for the lifecycle (else stash can never vault what was honestly seen). Display keeps the label."""
    scene = scene or "gameplay"
    return "loot" if (scene == "gameplay" and names) else scene

def _capture_ts_from_frame_id(frame_id):
    """frameId = '{n}_{captureMs}' — the exact settle freeze time of the archived photo."""
    try:
        if frame_id and "_" in str(frame_id):
            return int(str(frame_id).rsplit("_", 1)[-1])
    except Exception:
        pass
    return None


def emit_deep_read(rd, n, frame_id, interest=0.0, used_priority=False, ocr_rd=None, farewell=False, capture_ts=None, dispatch=None, raw=None):
    """Publish one deep-lane record (main settle + v740 farewell). Returns the record dict.

    v784 — ACCURACY: journal `ts` is the CAPTURE/settle clock (matches frameId suffix and the
    hist JPEG). `completedTs` is when Claude finished. Theatre scrubs by capture time so the
    photo and the AI row are the same moment, not 'photo at T, answer at T+8s' confusion.
    """
    global LAST_AREA
    rd = rd or {"area": "", "scene": "gameplay", "names": [], "tz": [], "conf": None, "mode": "empty"}
    if os.environ.get("TV_NO_JOURNAL"):
        rd = dict(rd)
        rd["sim"] = True   # v787 (R3 sleeper) — a replay/harness read must TELL the board it is not real loot
    if rd.get("area"): LAST_AREA = rd["area"]
    names = rd.get("names") or []
    # v863 — feed the CAPTURE clock into the lifecycle so out-of-order reader completions still
    # age holds by when the shot was TAKEN, not when the AI answered.
    _cap_ms = capture_ts or _capture_ts_from_frame_id(frame_id) or int(time.time() * 1000)
    intent = rd.get("intent") or _intent_for(rd.get("scene"))
    # v795 (Grok R5 #2) — OCR truth is not garbage: when the deep read comes back EMPTY but
    # the fast lane read real names, seed them as floor-SEEN (never vault from here) so a later
    # stash of that item still has its chain, and arm one re-read of this view.
    _ocr_seed = []
    if not names:
        _ocr_seed = [x for x in ((ocr_rd or {}).get("names") or []) if _itemish(x)][:12]   # v848 — garbage never seeds the chain
    if _ocr_seed:
        try:
            _LIFECYCLE.process("loot", _ocr_seed, rd.get("area") or "", None, now_ms=_cap_ms)
            globals()["_REFIRE_SIG"] = globals().get("_LAST_EMIT_SIG")
        except Exception:
            pass
    lc = _LIFECYCLE.process(effective_lc_scene(rd.get("scene"), names), names, rd.get("area") or "", rd.get("conf"),
                            now_ms=_cap_ms, names_loc=rd.get("names_loc") or {})
    vault_names = lc.get("vault_names") or lc.get("farmed_names") or []
    pending_names = lc.get("pending_names") or []
    thrown_names = lc.get("thrown_names") or []
    unvault_names = lc.get("unvault_names") or []
    if vault_names:
        tag = "🏦 vaulted"
    elif pending_names or (intent == "farmed" and names):
        tag = "⏳ holding"
    elif intent == "seen":
        tag = "👁 seen"
    elif thrown_names:
        tag = "🗑 throw"
    elif lc.get("gone_candidates"):
        tag = "👻 gone?"
    else:
        tag = "·"
    model_tag = rd.get("model") or FAST_MODEL
    esc = " ⬆genius" if rd.get("escalated") else ""
    pri = " ⚡" if used_priority else ""
    fare = " 👋FAREWELL" if farewell else ""
    lc_note = ""
    if vault_names:
        lc_note = " · VAULT " + ", ".join(vault_names[:3])
    elif pending_names:
        lc_note = " · HOLDING " + ", ".join(pending_names[:3]) + f" (≥{HOLD_MS//1000}s or stash)"
    elif thrown_names:
        lc_note = " · THROW-OUT " + ", ".join(thrown_names[:3])
    elif lc.get("gone_candidates"):
        lc_note = " · candidate gone " + ", ".join(lc["gone_candidates"][:3])
    elif lc.get("apply_held"):
        lc_note = " · hold apply (" + lc["apply_held"] + ")"
    ocr_ms = (ocr_rd or {}).get("ms")
    stash_tab = _norm_stash_tab(rd.get("stashTab"), rd.get("scene"))
    ocr_set = {_norm_name(x) for x in ((ocr_rd or {}).get("names") or [])}
    confirmed = [nm for nm in names if _norm_name(nm) in ocr_set]
    conf_note = ((" · ✓ocr " + ", ".join(confirmed[:3])) if confirmed else "")
    tab_note = (f" · tab:{stash_tab}" if stash_tab else "")
    line = ((("🗺 "+rd.get("area","")+" · ") if rd.get("area") else "") + tag + " " + str(rd.get("scene") or "")
            + tab_note + " — "
            + (", ".join(names[:5]) + ("…" if len(names) > 5 else "") if names else "no readable item text (honest empty)")
            + lc_note + conf_note
            + (" ["+str(rd.get("mode","?"))+" "+model_tag+esc+pri+fare+" "+str(round((rd.get("ms") or 0)/1000,1))+"s]" if rd.get("ms") else fare)
            + (f" · ocr {ocr_ms}ms" if ocr_ms is not None else ""))
    if farewell:
        ev("read", "👋 farewell · " + line)
        print(f"  👋 farewell · {(rd.get('area') or '?')} · {tag} {rd.get('scene')}{tab_note}  "
              f"{'📦 ' + ' · '.join(names[:6]) + (' …' if len(names) > 6 else '') if names else '· nothing readable'}"
              f"{lc_note}{conf_note}  [{model_tag}]")
    else:
        ev("read", line)
        print(f"  🗺 {(rd.get('area') or '?')} · {tag} {rd.get('scene')}{tab_note}  "
              f"{'📦 ' + ' · '.join(names[:6]) + (' …' if len(names) > 6 else '') if names else '· nothing readable'}"
              f"{lc_note}{conf_note}  [{model_tag}{esc}{pri}]")
    completed_ts = int(time.time() * 1000)
    # capture clock wins: frameId suffix → explicit capture_ts → completed (last resort)
    cap_ts = capture_ts or _capture_ts_from_frame_id(frame_id) or completed_ts
    vision_ms = int(rd.get("ms") or 0) or max(0, completed_ts - cap_ts)
    rec = {
        "ts": cap_ts,                    # v784 — CAPTURE moment (matches hist photo)
        "captureTs": cap_ts,
        "completedTs": completed_ts,     # when AI answer landed
        "names": names, "n": n, "area": rd.get("area") or "",
        "scene": rd.get("scene") or "gameplay", "tz": rd.get("tz", []), "ms": vision_ms,
        "mode": rd.get("mode", ""), "lane": "deep", "model": model_tag, "conf": rd.get("conf"),
        "intent": intent, "stashTab": stash_tab, "frameId": frame_id, "sessionId": SESSION_ID,
        "escalated": bool(rd.get("escalated")), "interest": interest, "priority": used_priority,
        "provisional": False, "farewell": bool(farewell),
        "sim": bool(rd.get("sim")),      # v787 — replay/harness truth travels WITH the read (R3 sleeper)
        "names_loc": rd.get("names_loc") or {},   # v830 — per-name location truth
        "raw": ("" if farewell else (raw if raw is not None else globals().get("_LAST_RAW", ""))) or ("«farewell read»" if farewell else ""),
        "dispatch": dict((dispatch if dispatch is not None else globals().get("_DISPATCH_CTX")) or ({"origin": "farewell"} if farewell else {})),
        "promptVer": PROMPT_VER,   # v832 — which prompt read this frame
        "agentVer": VERSION,
        "promptHash": hashlib.md5(READ_PROMPT.encode()).hexdigest()[:10],   # v838 (A2.9) — bisectable eyes
        "parse": rd.get("_parse_audit") or {},   # v835 — the clamp/drop audit
        "pre": _pre_triage(names, ocr_rd),                       # v853 — the gates, journaled
        "chain": lc.get("chain") or {},                          # v855 — provenance at decision time
        "ocr_raw": ((ocr_rd or {}).get("raw_lines") or [])[:16], # v853 — OCR's literal sight
        "decisions": {n: {"loc": (rd.get("names_loc") or {}).get(n, ""),
                          "tag": (lc.get("lifecycle_tags") or {}).get(n, ""),
                          "why": _reason_for((lc.get("lifecycle_tags") or {}).get(n, ""),
                                             (rd.get("names_loc") or {}).get(n, "")),
                          "chain": (lc.get("chain") or {}).get(n)}
                      for n in names},   # v836/v856 — THE DECISION CHAIN with provenance nested
        "equipped_names": [n for n in names if (rd.get("names_loc") or {}).get(n) == "equipped"],
        "ocr_seeded": _ocr_seed,         # v795 — names the fast lane saved from an empty deep read
        "ocr_ms": ocr_ms, "ocr_names": (ocr_rd or {}).get("names") or [],
        "confirmed_names": confirmed,
        "discovered_names": rd.get("discovered") or [],   # v763 — chat discovery broadcasts: chronicle-only, never vault
        "vault_names": vault_names, "farmed_names": vault_names,
        "pending_names": pending_names, "thrown_names": thrown_names,
        "unvault_names": unvault_names,
        "lifecycle_tags": lc.get("lifecycle_tags") or {},
        "anchor": lc.get("anchor", "n/a"),
        "gone_candidates": lc.get("gone_candidates") or [],
        "holdMs": HOLD_MS,
    }
    if (rd.get("scene") or "") == "transition":
        rec["transition_from"] = LAST_AREA
        rec["note"] = transition_note(LAST_AREA, n)
    _journal(rec)
    with _state_lock:
        st = _load()
        st.setdefault("seen", []); st.setdefault("farmed", [])
        st["reads"].append(dict(rec, raw=""))   # v832 — the ring stays thin; the JOURNAL keeps the thought
        st["reads"] = st["reads"][-200:]
        st["readCount"] = n
        st["ap"] = dict(_AP)
        st["lifecycle"] = _LIFECYCLE.snapshot()
        def _push(arr, name, extra):
            arr.append({"ts": rec["ts"], "name": name, "area": rd.get("area") or "", **extra})
            del arr[:-200]
        if intent == "seen":
            for nm in names:
                if not _is_anchor(nm) and not _is_junk(nm):
                    _push(st["seen"], nm, {"scene": "loot", "src": "deep"})
        for nm in vault_names:
            st["seen"] = [s for s in st["seen"] if s.get("name", "").lower() != nm.lower()]
            _push(st["farmed"], nm, {"scene": rd.get("scene") or "inventory",
                                     "tag": (lc.get("lifecycle_tags") or {}).get(nm, "vault")})
        _save(st)
    return rec

def farewell_read(force_frame=None):
    """v740 — one last capture + deep read on shutdown so end-of-run stash is never lost.

    Run #7 miss: garbage stashed then agent killed within seconds → no settle/gap/read.
    Farewell bypasses settle/gap and always publishes (flag farewell=true).
    force_frame: test seam (path to image); skips capture.
    Returns the published record, or None on hard failure.
    """
    print("\n  👋 farewell read — one last look so end-of-run stash is not lost…")
    ev("boot", "farewell read — capturing final frame")
    beat("reading", 0.0)
    _AP["mode"] = "read"
    frame = force_frame
    if not frame:
        frame = os.path.join(FRAMES, "live.bmp")
        try:
            if WATCH_MODE:
                f = newest_watched_frame()
                if f:
                    frame = f
                elif not os.path.isfile(frame):
                    ev("cap", "farewell: no watch frame")
                    print("  👋 farewell: no frame available — skipping")
                    return None
            else:
                if not capture_mac(frame):
                    # fall back to last vision JPEG if capture fails mid-shutdown
                    jp = os.path.join(FRAMES, "read.jpg")
                    if os.path.isfile(jp):
                        frame = jp
                        ev("skip", "farewell: capture failed — using last read.jpg")
                    else:
                        # v753 — deepest fallback: the newest archived hist frame
                        try:
                            hs = sorted((os.path.join(HIST_DIR, f) for f in os.listdir(HIST_DIR)
                                         if f.lower().endswith(".jpg")), key=os.path.getmtime)
                        except Exception:
                            hs = []
                        if hs:
                            frame = hs[-1]
                            ev("skip", "farewell: capture failed — using newest archived frame")
                        else:
                            ev("cap", "farewell capture failed")
                            print("  👋 farewell: capture failed — skipping")
                            return None
        except Exception as e:
            ev("cap", f"farewell capture error: {e}")
            print(f"  👋 farewell: capture error — {e}")
            return None
    if not os.path.isfile(frame):
        print("  👋 farewell: frame missing — skipping")
        return None
    with _state_lock:
        try:
            n = int((_load().get("readCount") or 0)) + 1
        except Exception:
            n = 1
    read_ts = int(time.time() * 1000)
    frame_id = archive_read_frame(frame, n, read_ts) or ""
    try:
        # deep only — farewell must land; OCR is optional and can wait
        rd = claude_read(frame)
    except Exception as e:
        ev("cap", f"farewell vision failed: {e}")
        print(f"  👋 farewell: vision failed — {e}")
        return None
    if not rd:
        rd = {"area": "", "scene": "gameplay", "names": [], "tz": [], "conf": None,
              "mode": "empty", "model": FAST_MODEL, "ms": 0}
    rec = emit_deep_read(rd, n=n, frame_id=frame_id, interest=1.0,
                         used_priority=True, ocr_rd=None, farewell=True,
                         capture_ts=read_ts)
    names = rec.get("names") or []
    scene = rec.get("scene") or "?"
    tab = rec.get("stashTab") or ""
    vault = rec.get("vault_names") or []
    summary = scene + (f"/{tab}" if tab else "")
    if vault:
        summary += " · VAULT " + ", ".join(vault[:4])
    elif names:
        summary += " — " + ", ".join(names[:4])
    else:
        summary += " — empty"
    print(f"  👋 farewell read done: {summary}")
    ev("boot", f"farewell done · {summary}"[:120])
    return rec

_FAREWELL_DONE = False
_STOPPING = False

def close_session(reason="stop", farewell=True):
    """v847 — seal the theatre reel then exit.
    Always journals session_end (sessions list + SIM shelf). Optional farewell vision on STOP.
    OFF uses farewell=False for a fast cut that still SAVES the session."""
    global _FAREWELL_DONE, _STOPPING
    if _FAREWELL_DONE:
        os._exit(0)
    _FAREWELL_DONE = True
    _STOPPING = True
    reason = str(reason or "stop")[:60]
    print(f"\n  👋 closing session ({reason})" + (" — farewell read…" if farewell else " — sealing reel…"))
    ev("boot", "session close · " + reason + (" · farewell" if farewell else " · soft off"))
    # Seal the reel FIRST so a force-kill mid-farewell still leaves a complete session on disk
    try:
        _journal({
            "ts": int(time.time() * 1000),
            "n": 0,
            "scene": "session_end",
            "names": [],
            "sessionId": SESSION_ID,
            "note": reason,
            "farewell": bool(farewell),
            "mode": "session_end",
            "lane": "system",
            "ver": VERSION,
        })
    except Exception as e:
        print(f"  👋 session_end journal failed: {e}")
    try:
        _pool_shutdown()   # v863/v864 — join in-flight (≤90s), inert late threads, then farewell
    except Exception:
        pass
    if farewell:
        try:
            with _emit_lock:   # v864 — the farewell applies under the same mutex as every pooled emit
                farewell_read()
        except Exception as e:
            print(f"  👋 farewell failed: {e}")
    with _state_lock:
        try:
            st = _load()
            st["online"] = False
            st["stopping"] = False
            st["sessionId"] = SESSION_ID
            _save(st)
        except Exception:
            pass
    try:
        _eye_clear()
    except Exception:
        pass
    try:
        _settle_queue_clear()
    except Exception:
        pass
    print("\n📺 TV DIABLO off — session saved · good hunting.")
    os._exit(0)


def _shutdown_handler(signum, frame):
    """SIGINT/SIGTERM/SIGBREAK → close session (farewell when possible)."""
    global _STOPPING
    _STOPPING = True
    if _FAREWELL_DONE:
        os._exit(0)
    # Force-kill paths often send a second SIGKILL — first signal gets full farewell when possible
    sig_name = "SIGINT" if signum == signal.SIGINT else (
        "SIGTERM" if signum == signal.SIGTERM else (
            "SIGBREAK" if getattr(signal, "SIGBREAK", None) == signum else str(signum)))
    # Env TV_FAREWELL=0 lets control request a soft seal without vision (OFF button)
    fare = os.environ.get("TV_FAREWELL", "1") not in ("0", "false", "no")
    try:
        close_session(reason="signal:" + sig_name, farewell=fare)
    except Exception:
        os._exit(0)

if __name__ == "__main__":
    # one-shot validation: python3 tv/tv_diablo.py --test <image>  (run in YOUR terminal —
    # a Claude Code session cannot nest another; from a normal shell this is a plain call)
    if "--test" in sys.argv:
        try:
            img = sys.argv[sys.argv.index("--test") + 1]
        except IndexError:
            print("usage: python3 tv/tv_diablo.py --test <image.jpg>"); sys.exit(2)
        print("📺 test read:", os.path.abspath(img))
        print(json.dumps(claude_read(img), indent=1))
        sys.exit(0)
    # v740 — farewell on Ctrl-C AND tvd stop (SIGTERM)
    try:
        signal.signal(signal.SIGINT, _shutdown_handler)
        signal.signal(signal.SIGTERM, _shutdown_handler)
        # v760.1 — Windows: the control app's soft-stop arrives as CTRL_BREAK (SIGBREAK);
        # without this the farewell NEVER fires on the cousin's box (taskkill-soft can't
        # reach a windowless console app, and SIGTERM does not exist on Windows).
        if hasattr(signal, "SIGBREAK"):
            signal.signal(signal.SIGBREAK, _shutdown_handler)
    except Exception:
        pass
    try:
        main()
    except KeyboardInterrupt:
        # fallback if signal handler not installed (rare)
        if not _FAREWELL_DONE:
            _shutdown_handler(signal.SIGINT, None)
