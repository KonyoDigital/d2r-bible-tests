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
#   Frugality (protects your plan limits): a read fires ONLY when the screen
#   goes STABLE (two identical captures in a row = you stopped to look at
#   items) after having changed. Running around = every frame differs = zero
#   reads. Hard caps: ≥20s between reads, 120 reads per session.
# ═══════════════════════════════════════════════════════════════════════════════
import json, os, subprocess, sys, threading, time, hashlib, signal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE   = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(HERE, "frames")
STATE  = os.path.join(HERE, "state.json")
PORT   = int(os.environ.get("TV_PORT", "17771"))   # v711 — overridable (tests · port conflicts)
MIN_GAP_S    = 6      # baseline gap between vision fires
PRIORITY_GAP_S = 2.5  # v727 Autopilot: after HARD motion then settle → near-instant eyes
# v726 — no empty-gameplay cool (blocked pile stops). Thrash = same-view + gap only.
SESSION_CAP  = 240
POLL_S       = 0.25
WATCH_MODE   = "--watch" in sys.argv
# v727 — motion “wow” threshold: walking/panel open swings past this
MOTION_PEAK  = 0.12
SETTLE       = 0.03

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
READ_PROMPT = (
    "Image {path} = Diablo II Resurrected (RoW). Reply with STRICT JSON only, no markdown, no prose:\n"
    "{{\"area\":\"\",\"tz\":[],\"scene\":\"gameplay\",\"stashTab\":\"\",\"names\":[],\"conf\":0.0}}\n"
    "scene = one of: town | stash | inventory | loot | gameplay.\n"
    "area = zone name from top-right Game block / ENTERING banner / automap, else \"\".\n"
    "tz = purple terror-zone lines in that block, else [].\n"
    "stashTab = ONLY when scene=stash: which LEFT stash tab is active — "
    "personal | shared | gems | materials | runes | \"\" if unknown. "
    "Stash tell: left panel tabs + inventory often open on the right.\n"
    "names = READABLE text labels only (tooltips first line, ground loot labels, open inventory/stash "
    "name text). Never invent from icons alone. Never complete partial names.\n"
    "Never put merc/NPC/player names, HP bars, waypoint labels, or chat into names.\n"
    "inventory/stash: also list anchors if visible — Horadric Cube, Tome of Town Portal, Tome of Identify.\n"
    "conf = 0.0-1.0 confidence. Be fast and precise."
)

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
    "ver": "v740",
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

def ap_interest(peak, stable_ticks, priority, empty_streak, named_recent):
    """0–1 score: hard motion → stop is the 'money moment' (pile / panel)."""
    s = 0.15
    if peak >= MOTION_PEAK: s += 0.45
    elif peak >= 0.06: s += 0.2
    if priority: s += 0.25
    if named_recent: s += 0.1
    if empty_streak >= 3: s -= 0.08   # slight downrank only — never blocks
    if stable_ticks >= 1: s += 0.1
    return max(0.0, min(1.0, s))

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
            if self.path.startswith("/state"):
                with _state_lock:
                    st = _load(); st["online"] = True; st["now"] = int(time.time()*1000)
                    st["beat"] = dict(_BEAT); st["events"] = list(_EVENTS); st["ap"] = dict(_AP)
                self._hdr(); self.wfile.write(json.dumps(st).encode())
            elif self.path.startswith("/ping"):
                self._hdr(); self.wfile.write(b'{"ok":true,"tv":"diablo"}')
            elif self.path.startswith("/frame"):
                # v724 — last vision JPEG · v735 — ?id=N_ts for per-read hist archive (1920 eye)
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
                    jp = os.path.join(FRAMES, "read.jpg")
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
                    except Exception:
                        self._hdr(500); self.wfile.write(b'{"error":"frame read failed"}')
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

def capture_mac(path):
    """One silent full-screen capture. BMP = deterministic pixels → md5 frame-diff works."""
    r = subprocess.run(["screencapture", "-x", "-t", "bmp", path], capture_output=True)
    return r.returncode == 0 and os.path.exists(path)

def newest_watched_frame():
    """Windows mode: capture_win.ps1 drops frames into tv/frames — consume the newest."""
    try:
        fs = [os.path.join(FRAMES, f) for f in os.listdir(FRAMES) if f.lower().endswith((".bmp", ".png"))]
        return max(fs, key=os.path.getmtime) if fs else None
    except Exception:
        return None

def frame_sig(path):
    """~4k byte samples across the BMP pixel data — cheap fuzzy fingerprint, stdlib only."""
    with open(path, "rb") as f: data = f.read()
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
    m = min(len(a), len(b))
    return sum(1 for i in range(m) if abs(a[i] - b[i]) > tol) / m

# v735 — per-read frame ring for session history (human eye ~1920; AI still uses 1568)
HIST_DIR = os.path.join(FRAMES, "hist")
try:
    HIST_KEEP = max(10, int(os.environ.get("TV_HIST_KEEP", "80")))
except Exception:
    HIST_KEEP = 80
# MacBook-ish display width for click-to-enlarge (not the AI vision input size)
HIST_MAX_PX = 1920

def _readable_frame(ap):
    """v710.6 LIVE-SESSION FIX (Konyo's first real run): claude's Read tool chokes on a 16MB
    raw BMP — both live reads timed out at 180s. Convert to a 1568px JPEG (the locked intake
    spec) before the vision call. Mac: sips (built-in). Windows: capture_win.ps1 saves live.png
    alongside. Falls back to the original path if conversion isn't available."""
    try:
        if not ap.lower().endswith(".bmp"):
            return ap
        jp = os.path.join(FRAMES, "read.jpg")
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
                r = subprocess.run(
                    ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "82",
                     "--resampleHeightWidthMax", str(HIST_MAX_PX), src, "--out", dest],
                    capture_output=True, timeout=25)
                ok = r.returncode == 0 and os.path.isfile(dest)
            if not ok:
                # last resort: copy vision read.jpg if present
                jp = os.path.join(FRAMES, "read.jpg")
                if os.path.isfile(jp):
                    import shutil
                    shutil.copy2(jp, dest)
                    ok = os.path.isfile(dest)
        if not ok:
            return ""
        # prune oldest beyond HIST_KEEP
        try:
            files = [os.path.join(HIST_DIR, f) for f in os.listdir(HIST_DIR)
                     if f.lower().endswith(".jpg")]
            files.sort(key=lambda p: os.path.getmtime(p))
            for old in files[:-HIST_KEEP]:
                try: os.remove(old)
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
            text=True, bufsize=1, env=env)
        self.q = queue.Queue(); self.turns = 0
        def _pump(proc, q):
            try:
                for line in proc.stdout: q.put(line)
            except Exception: pass
            q.put(None)
        threading.Thread(target=_pump, args=(self.p, self.q), daemon=True).start()
    def stop(self):
        try:
            if self.p and self.p.poll() is None: self.p.kill()
        except Exception: pass
        self.p = None
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

# ═══ v732 — OCR FAST LANE (Konyo: pile→chip in ~0.1–0.2s; LLM floors at 3–6s)
# Local macOS Vision OCR (warm worker ~10–50ms). Claude stays the deep brain.
# Honesty: OCR names are provisional (review-first, never vault_names) until deep/lifecycle.
OCR_BIN = os.environ.get("TV_OCR_BIN") or os.path.join(HERE, "bin", "ocr_mac")
OCR_ENABLED = os.environ.get("TV_OCR", "1") != "0"

class OcrWorker:
    """Persistent `ocr_mac --worker` — one process, many frames. Stdlib only."""
    def __init__(self):
        self.p = None
        self.q = None
        self.lock = threading.Lock()
        self.ok = False

    def available(self):
        return bool(OCR_ENABLED and os.path.isfile(OCR_BIN) and os.access(OCR_BIN, os.X_OK))

    def _spawn(self):
        import queue
        if not self.available():
            self.ok = False
            return False
        try:
            self.p = subprocess.Popen(
                [OCR_BIN, "--worker"],
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
        try:
            if self.p and self.p.poll() is None:
                try:
                    self.p.stdin.write("quit\n"); self.p.stdin.flush()
                except Exception:
                    pass
                self.p.kill()
        except Exception:
            pass
        self.p = None
        self.ok = False

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
    if not OCR_ENABLED:
        return None
    t0 = time.time()
    raw = _OCR.read(path)
    wall = int((time.time() - t0) * 1000)
    if not raw:
        return None
    lines = filter_ocr_lines(raw.get("lines") or [])
    confs = raw.get("confs") or []
    avg_c = None
    if confs:
        try:
            avg_c = round(sum(float(c) for c in confs[: len(lines) or 1]) / max(1, min(len(confs), max(1, len(lines)))), 3)
        except Exception:
            avg_c = None
    return {
        "names": lines,
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

_REWARM_T = [0.0]
def _rewarm():
    """after a worker death, quietly warm a fresh session in the background (60s debounce)
    so the NEXT pause reads warm again — one-shot is a bridge, never the new normal."""
    if time.time() - _REWARM_T[0] < 60: return
    _REWARM_T[0] = time.time()
    def _w():
        t0 = time.time()
        if _WORKER.ask("Reply with exactly: ok", timeout=60) is not None:
            ev("boot", f"vision re-warmed in {int(time.time()-t0)}s — back to fast reads")
    threading.Thread(target=_w, daemon=True).start()

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
    """extract + normalize the read JSON from model text; None if no JSON object found."""
    a, b = out.find("{"), out.rfind("}")
    if a < 0 or b <= a: return None
    try: j = json.loads(out[a:b+1])
    except Exception: return None
    names = [str(x).strip() for x in j.get("names", []) if str(x).strip()][:60]
    scene = str(j.get("scene", "gameplay")).lower()
    if scene not in ("town", "loot", "inventory", "stash", "gameplay"): scene = "gameplay"
    tz = [str(x).strip()[:40] for x in j.get("tz", []) if str(x).strip()][:8]
    conf = j.get("conf", None)
    try:
        conf = float(conf) if conf is not None else None
        if conf is not None:
            conf = max(0.0, min(1.0, conf))
    except Exception:
        conf = None
    stash_tab = _norm_stash_tab(j.get("stashTab") or j.get("stash_tab"), scene)
    return {"area": str(j.get("area", "")).strip()[:48], "scene": scene, "names": names,
            "tz": tz, "conf": conf, "stashTab": stash_tab}

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

    def process(self, scene, names, area, conf, now_ms=None):
        now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
        names = [str(n).strip() for n in (names or []) if str(n).strip()]
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
            self._on_stash(names, area, conf, now_ms, out)
        # refresh pending heldMs for snapshot consumers
        for k, p in self.pending.items():
            p["heldMs"] = max(0, now_ms - p["firstHeld"])
        out["farmed_names"] = list(out["vault_names"])
        out["pending_names"] = [p["name"] for p in self.pending.values()]
        return out

    def _has_chain(self, n):
        """v738 — floor SEEN, inv HOLDING, or gone-candidate this session."""
        k = _norm_name(n)
        return bool(k) and (k in self.seen or k in self.pending or k in self.candidates)

    def _commit(self, n, reason, now_ms, out, tag=None):
        k = _norm_name(n)
        if not k or _is_junk(n) or _is_anchor(n) or _is_never_vault(n):
            if _is_never_vault(n) and not _is_anchor(n) and not _is_junk(n):
                out["lifecycle_tags"][n] = "skip-weak"
            return
        if k in self.vaulted:
            out["lifecycle_tags"][n] = "already-vaulted"
            return
        self.vaulted[k] = {"name": n, "reason": reason, "ts": now_ms}
        self.pending.pop(k, None)
        self.candidates.pop(k, None)
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
        if not k or k in self.vaulted:
            if k in self.vaulted:
                out["lifecycle_tags"][n] = "already-vaulted"
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

    def _on_stash(self, names, area, conf, now_ms, out):
        # v738 — stash-commit ONLY with object-permanence chain (SEEN / HOLDING / candidate).
        # Panel-greedy vault of random shared-tab tooltips caused run #4 false farmed.
        out["anchor"] = "ok" if names else "missing"
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
            if k in self.vaulted:
                out["lifecycle_tags"][n] = "already-vaulted"
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

def _oneshot(ap, model, timeout=90):
    """One cold `claude -p` on subscription (strict-mcp, no API key)."""
    env, stripped = _claude_env()
    _log_auth_once(stripped)
    r = subprocess.run(
        [CLAUDE_BIN, "-p", READ_PROMPT.format(path=ap),
         "--model", model, "--allowedTools", "Read", "--output-format", "text",
         "--strict-mcp-config"],
        capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL, env=env)
    out = (r.stdout or "").strip()
    a, b = out.find("{"), out.rfind("}")
    if a < 0 or b <= a:
        err = (r.stderr or "").strip()[:160]
        ev("cap", f"vision returned no JSON ({model} exit {r.returncode})" + (f": {err}" if err else ""))
        if r.returncode != 0:
            print(f"  ⚠ claude exit {r.returncode}" + (f": {err}" if err else ""))
        return None
    return _parse_read(out)

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

def claude_read(path):
    """One vision read on YOUR Claude subscription. Fast model first; genius escalate if needed."""
    # v711 — TV_STUB: the TDD seam. TV_STUB=1 returns canned reads from tv/stub_manifest.json
    # (keyed by frame basename, '*' fallback) — the FULL agent loop runs end-to-end with zero
    # vision cost, in tests and in CI. Never set in real play.
    if os.environ.get("TV_STUB"):
        try:
            with open(os.path.join(HERE, "stub_manifest.json"), encoding="utf-8") as f: man = json.load(f)
        except Exception:
            man = {}
        base = os.path.basename(path)
        rd = man.get(base) or man.get("*") or {}
        scene = rd.get("scene", "gameplay")
        return {"area": rd.get("area", ""), "scene": scene,
                "names": rd.get("names", []), "tz": rd.get("tz", []),
                "conf": rd.get("conf", 1.0), "intent": _intent_for(scene),
                "stashTab": _norm_stash_tab(rd.get("stashTab") or rd.get("stash_tab"), scene),
                "model": "stub", "mode": "stub", "escalated": False, "ms": 0}
    ap = _readable_frame(os.path.abspath(path))
    EMPTY = {"area": "", "scene": "gameplay", "names": [], "tz": [], "conf": None,
             "intent": "context", "stashTab": "",
             "model": FAST_MODEL, "mode": "empty", "escalated": False, "ms": 0}
    if not os.path.isfile(ap):
        print(f"  ⚠ image missing: {ap}")
        return EMPTY
    t0 = time.time()
    out_w = _WORKER.ask(READ_PROMPT.format(path=ap))
    if out_w is not None:
        parsed = _parse_read(out_w)
        if parsed is not None:
            return _maybe_genius(ap, parsed, t0, "warm") or EMPTY
        ev("cap", "worker returned non-JSON — falling back to one-shot")
    else:
        ev("skip", "vision worker died (timeout/stream end) — one-shot for this read, re-warming behind it")
        _rewarm()   # v718 (Grok R10 pick #2): fallback never permanently demotes the session
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
    global _LIFECYCLE
    os.makedirs(FRAMES, exist_ok=True)
    _LIFECYCLE = LootLifecycle()
    with _state_lock:
        _save({"online": True, "startedAt": int(time.time()*1000), "reads": [], "readCount": 0,
               "cap": SESSION_CAP, "seen": [], "farmed": [], "model": FAST_MODEL, "genius": GENIUS_MODEL,
               "lifecycle": _LIFECYCLE.snapshot()})
    bridge()
    ev("boot", f"scanner online — eyes {POLL_S}s · fast={FAST_MODEL} · genius={GENIUS_MODEL} · lifecycle v2")
    if not os.environ.get("TV_STUB"):
        def _warm():
            t0 = time.time()
            if _WORKER.ask("Reply with exactly: ok", timeout=60) is not None:
                ev("boot", f"vision warm — {FAST_MODEL} ready in {int(time.time()-t0)}s (first read will be fast)")
            else:
                ev("skip", "warm-up didn't answer — first read may be slow (one-shot fallback armed)")
        threading.Thread(target=_warm, daemon=True).start()
    if os.environ.get("CLAUDECODE"):
        ev("cap", "⚠ launched INSIDE a Claude session — vision calls can hang. Run me in a bare Terminal.")
        print("  ⚠ you're inside a Claude Code session — claude -p may hang nested. Use a BARE Terminal window.")
    print("📺 TV DIABLO Autopilot v740 — farewell read on stop · chain vault · frame hist")
    print(f"   bridge: http://127.0.0.1:{PORT}/state  ·  mode: {'watch (Windows frames)' if WATCH_MODE else 'mac screencapture'}")
    print(f"   models: fast={FAST_MODEL} · genius={GENIUS_MODEL} · gap={MIN_GAP_S}s · priority gap={PRIORITY_GAP_S}s")
    ocr_tag = "ON " + OCR_BIN if _OCR.available() else "OFF (set TV_OCR_BIN or build tv/bin/ocr_mac)"
    print(f"   ocr lane: {ocr_tag}")
    print("   tip: fullscreen D2R · stop on piles — ⚡ocr chips flash first, Claude confirms behind")
    print("   in the bible: ⚡ session → 📺 TV DIABLO → flip ON. Ctrl-C to stop.\n")
    ev("boot", f"autopilot v740 — farewell on stop · chain vault · OCR · priority gap {PRIORITY_GAP_S}s")
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
    last_md5, stable, last_sent_md5, last_read_t, reads = None, 0, None, 0.0, 0
    peak = 0.0            # recent max motion while hunting
    priority = False      # hard motion seen since last read → short gap + 1-tick settle
    empty_streak = 0
    named_until = 0.0     # boost interest after a named hit
    while True:
        time.sleep(POLL_S)
        if WATCH_MODE:
            f = newest_watched_frame()
            if not f: continue
            frame = f
        elif not capture_mac(frame):
            print("  ⚠ screencapture failed (grant Terminal screen-recording permission in System Settings)"); continue
        elif (not WATCH_MODE) and os.path.getsize(frame) < 200000:
            if not globals().get("_PERM_WARNED"):
                globals()["_PERM_WARNED"] = True
                ev("cap", "capture looks EMPTY — grant Screen Recording to your terminal (System Settings → Privacy) and relaunch")
                print("  ⚠ capture is suspiciously tiny — screen-recording permission is probably missing")
            continue
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
        interest = ap_interest(peak, stable, priority, empty_streak, named_recent)
        _AP.update({"interest": round(interest, 3), "peak": round(peak, 3), "priority": priority,
                    "emptyStreak": empty_streak, "gap": PRIORITY_GAP_S if priority else MIN_GAP_S})
        beat("watching" if motion > SETTLE else "watching", motion)
        if motion > SETTLE:
            stable = 0
            last_md5 = cur
            if priority: _AP["mode"] = "hunt"
            else: _AP["mode"] = "drive"
            continue
        stable = stable + 1
        last_md5 = cur
        # Adaptive settle: priority (hard motion→stop) fires on first stable tick;
        # low-interest needs 2 stable ticks (filters ambient flicker without 20s cools)
        need_ticks = 1 if (priority or interest >= 0.55) else 2
        if stable < need_ticks:
            _AP["mode"] = "settle"
            continue
        if sig_diff(cur, last_sent_md5) <= SETTLE:
            # same view — reset peak so we don't stay priority forever on one freeze
            if stable == need_ticks:
                ev("skip", "settled, but same view I already read — waiting for something new")
            peak = max(0.0, peak * 0.5)
            continue
        gap = PRIORITY_GAP_S if priority else MIN_GAP_S
        if time.time() - last_read_t < gap:
            if stable == need_ticks:
                ev("skip", f"settled, but only {int(time.time()-last_read_t)}s since last read (gap {gap}s · {'PRIORITY' if priority else 'cruise'})")
            continue
        if reads >= SESSION_CAP:
            ev("cap", f"session cap {SESSION_CAP} reached — restart to continue")
            print(f"  ⛔ session cap ({SESSION_CAP} reads) reached — restart to continue"); time.sleep(60); continue
        last_read_t, last_sent_md5 = time.time(), cur
        reads += 1
        read_ts = int(time.time() * 1000)
        # v735 — archive THIS settle's frame for history click-to-enlarge (before vision mutates)
        frame_id = archive_read_frame(frame, reads, read_ts)
        ptag = "⚡PRIORITY " if priority else ""
        print(f"  👁 {ptag}screen settled — reading ({reads}/{SESSION_CAP}) interest={interest:.2f} …"
              + (f" frame={frame_id}" if frame_id else ""))
        ev("settle", f"{ptag}settle · interest {interest:.2f} · peak {peak:.2f} · dual-lane read #{reads}"
           + (f" · frame {frame_id}" if frame_id else ""))
        beat("reading", 0.0)
        _AP["mode"] = "read"
        used_priority = priority
        peak = 0.0
        priority = False

        # ── FAST LANE: local OCR first (target ~10–50ms warm; board poll 250ms) ──
        ocr_rd = ocr_fast(frame)
        if ocr_rd is not None:
            oms = ocr_rd.get("ms") or ocr_rd.get("wall_ms") or 0
            onames = ocr_rd.get("names") or []
            ev("ocr", f"⚡ocr {oms}ms · {len(onames)} name(s)" +
               ((" — " + ", ".join(onames[:4])) if onames else " — no item-ish text") +
               f" (raw {ocr_rd.get('raw_n', 0)})")
            print(f"  ⚡ ocr {oms}ms  {('· ' + ' · '.join(onames[:6])) if onames else '· no item-ish text'}")
            if onames:
                with _state_lock:
                    st = _load()
                    st.setdefault("seen", []); st.setdefault("farmed", [])
                    prec = {
                        "ts": read_ts, "names": onames, "n": reads,
                        "area": "", "scene": "loot", "tz": [],
                        "ms": oms, "mode": "ocr", "lane": "ocr", "model": "ocr-mac",
                        "conf": ocr_rd.get("conf"), "intent": "seen",
                        "escalated": False, "interest": interest, "priority": used_priority,
                        "provisional": True,
                        "frameId": frame_id,
                        "vault_names": [], "farmed_names": [],  # NEVER vault from OCR alone
                        "pending_names": [], "thrown_names": [], "unvault_names": [],
                        "lifecycle_tags": {nm: "ocr" for nm in onames},
                        "anchor": "n/a", "gone_candidates": [], "holdMs": HOLD_MS,
                    }
                    st["reads"].append(prec)
                    st["reads"] = st["reads"][-200:]
                    st["readCount"] = reads
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

        # ── DEEP LANE: Claude (scene/area/verify; 3–8s) ──
        rd = claude_read(frame)
        beat("watching", 0.0)
        rec = emit_deep_read(rd, n=reads, frame_id=frame_id, interest=interest,
                             used_priority=used_priority, ocr_rd=ocr_rd, farewell=False)
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

def emit_deep_read(rd, n, frame_id, interest=0.0, used_priority=False, ocr_rd=None, farewell=False):
    """Publish one deep-lane record (main settle + v740 farewell). Returns the record dict."""
    rd = rd or {"area": "", "scene": "gameplay", "names": [], "tz": [], "conf": None, "mode": "empty"}
    names = rd.get("names") or []
    intent = rd.get("intent") or _intent_for(rd.get("scene"))
    lc = _LIFECYCLE.process(rd.get("scene") or "gameplay", names, rd.get("area") or "", rd.get("conf"))
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
    rec = {
        "ts": int(time.time() * 1000), "names": names, "n": n, "area": rd.get("area") or "",
        "scene": rd.get("scene") or "gameplay", "tz": rd.get("tz", []), "ms": rd.get("ms", 0),
        "mode": rd.get("mode", ""), "lane": "deep", "model": model_tag, "conf": rd.get("conf"),
        "intent": intent, "stashTab": stash_tab, "frameId": frame_id,
        "escalated": bool(rd.get("escalated")), "interest": interest, "priority": used_priority,
        "provisional": False, "farewell": bool(farewell),
        "ocr_ms": ocr_ms, "ocr_names": (ocr_rd or {}).get("names") or [],
        "confirmed_names": confirmed,
        "vault_names": vault_names, "farmed_names": vault_names,
        "pending_names": pending_names, "thrown_names": thrown_names,
        "unvault_names": unvault_names,
        "lifecycle_tags": lc.get("lifecycle_tags") or {},
        "anchor": lc.get("anchor", "n/a"),
        "gone_candidates": lc.get("gone_candidates") or [],
        "holdMs": HOLD_MS,
    }
    with _state_lock:
        st = _load()
        st.setdefault("seen", []); st.setdefault("farmed", [])
        st["reads"].append(rec)
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
                         used_priority=True, ocr_rd=None, farewell=True)
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
def _shutdown_handler(signum, frame):
    """SIGINT/SIGTERM → farewell read then clean exit (tvd stop sends SIGTERM)."""
    global _FAREWELL_DONE
    if _FAREWELL_DONE:
        os._exit(0)
    _FAREWELL_DONE = True
    sig_name = "SIGINT" if signum == signal.SIGINT else ("SIGTERM" if signum == signal.SIGTERM else str(signum))
    print(f"\n  👋 shutdown ({sig_name}) — farewell read…")
    try:
        farewell_read()
    except Exception as e:
        print(f"  👋 farewell failed: {e}")
    with _state_lock:
        try:
            st = _load(); st["online"] = False; _save(st)
        except Exception:
            pass
    print("\n📺 TV DIABLO off — good hunting.")
    # hard exit so we don't re-enter the main loop mid-sleep
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
    except Exception:
        pass
    try:
        main()
    except KeyboardInterrupt:
        # fallback if signal handler not installed (rare)
        if not _FAREWELL_DONE:
            _shutdown_handler(signal.SIGINT, None)
