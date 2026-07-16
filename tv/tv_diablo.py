#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# 📺 TV DIABLO — the live game-screen scanner (v720)
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
import json, os, subprocess, sys, threading, time, hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE   = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(HERE, "frames")
STATE  = os.path.join(HERE, "state.json")
PORT   = int(os.environ.get("TV_PORT", "17771"))   # v711 — overridable (tests · port conflicts)
MIN_GAP_S    = 20     # never read more often than this
SESSION_CAP  = 120    # hard stop for a whole session
POLL_S       = 0.5    # capture cadence — eyes always open, half-second pulse (Konyo: "make it even half a second ;)")
WATCH_MODE   = "--watch" in sys.argv   # Windows: frames arrive from capture_win.ps1

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
READ_PROMPT = (
    "Read the image file at {path} — a screenshot of Diablo II: Resurrected (Reign of the Warlock mod). "
    "Return FOUR things as STRICT JSON. "
    "(1) \"area\": the current zone. Look for: the top-right info block (line under \'Game: ...\' is the "
    "area name), a red \'ENTERING THE <ZONE>\' banner, or the automap corner text. Verbatim, else \"\". "
    "(2) \"tz\": the purple zone names in that top-right block (today's terror zones), else []. "
    "(3) \"scene\": exactly one of \"town\" (an act town: Rogue Encampment, Lut Gholein, Kurast Docks, "
    "Pandemonium Fortress, Harrogath — town NPCs/stash present), \"stash\" (a STASH-titled panel is open), "
    "\"inventory\" (an INVENTORY panel is open, no stash), \"loot\" (item name labels floating over the "
    "ground), \"gameplay\" (none of those). "
    "(4) \"names\": item names from READABLE TEXT ONLY. Item icons in panel grids carry NO readable name — "
    "NEVER name an item from its icon. Readable names come from: a hover TOOLTIP (FIRST line = the item "
    "name, second = its base type), ground item LABELS, a DETACHED top-left hover label, or a waypoint "
    "label (report \'<Zone> Waypoint\' as area intel, NOT as an item). Include uniques, set pieces, runes "
    "(like \'Ist Rune\'), gems, charms, jewels, bases, potions. Never guess or complete a partially "
    "hidden name; [] if no readable item text. "
    "STRICT JSON only, no prose: {{\"area\":\"...\",\"tz\":[\"...\"],\"scene\":\"...\",\"names\":[\"...\"]}}"
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
def ev(kind, text):
    """v710.6 — the BRAIN LOG: the scanner's real decisions, streamed to the board
    (in-memory ring like the beat; /state merges it — no disk churn)."""
    _EVENTS.append({"ts": int(time.time()*1000), "k": kind, "t": str(text)[:120]})
    del _EVENTS[:-60]
def beat(phase, motion):
    """v710.4 — the LIVE pulse, IN MEMORY only (Grok audit: rewriting state.json twice a
    second thrashed disk + the lock). /state merges it at request time; reads still persist."""
    _BEAT["ts"] = int(time.time()*1000); _BEAT["phase"] = phase; _BEAT["motion"] = round(float(motion), 3)

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
                    st = _load(); st["online"] = True; st["now"] = int(time.time()*1000); st["beat"] = dict(_BEAT); st["events"] = list(_EVENTS)
                self._hdr(); self.wfile.write(json.dumps(st).encode())
            elif self.path.startswith("/ping"):
                self._hdr(); self.wfile.write(b'{"ok":true,"tv":"diablo"}')
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


# ═══ v713 — PERSISTENT VISION WORKER (the SPEED fix). One long-lived claude session in
# stream-json mode: each frame is a TURN, not a cold start (live run #1: cold starts + a
# broken transport = 180s hangs). The worker restarts itself every N turns so conversation
# context never bloats a read, and ANY wobble (timeout · dead process · bad JSON) kills it
# and falls back to the one-shot path. TV_CLAUDE_BIN overrides the binary — the TDD seam
# (tests run a fake bin that speaks stream-json).
CLAUDE_BIN = os.environ.get("TV_CLAUDE_BIN", "claude")
WORKER_MAX_TURNS = 8

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
    def __init__(self):
        self.p = None; self.q = None; self.turns = 0
    def _spawn(self):
        import queue
        env, stripped = _claude_env()
        _log_auth_once(stripped)
        self.p = subprocess.Popen(
            [CLAUDE_BIN, "-p", "--input-format", "stream-json", "--output-format", "stream-json",
             "--verbose", "--model", "sonnet", "--allowedTools", "Read", "--strict-mcp-config"],
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
        """one turn → the result text, or None (caller falls back to one-shot)."""
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
    return {"area": str(j.get("area", "")).strip()[:48], "scene": scene, "names": names, "tz": tz}

def claude_read(path):
    """One vision read on YOUR Claude subscription. Read-only tools; Sonnet (the intake-calibrated model)."""
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
        return {"area": rd.get("area", ""), "scene": rd.get("scene", "gameplay"),
                "names": rd.get("names", []), "tz": rd.get("tz", [])}
    ap = _readable_frame(os.path.abspath(path))
    EMPTY = {"area": "", "scene": "gameplay", "names": [], "tz": []}
    if not os.path.isfile(ap):
        print(f"  ⚠ image missing: {ap}")
        return EMPTY
    t0 = time.time()
    out_w = _WORKER.ask(READ_PROMPT.format(path=ap))
    if out_w is not None:
        parsed = _parse_read(out_w)
        if parsed is not None:
            parsed["ms"] = int((time.time() - t0) * 1000); parsed["mode"] = "warm"
            return parsed
        ev("cap", "worker returned non-JSON — falling back to one-shot")
    else:
        ev("skip", "vision worker died (timeout/stream end) — one-shot for this read, re-warming behind it")
        _rewarm()   # v718 (Grok R10 pick #2): fallback never permanently demotes the session
    try:
        env, stripped = _claude_env()
        _log_auth_once(stripped)
        r = subprocess.run(
            [CLAUDE_BIN, "-p", READ_PROMPT.format(path=ap),
             "--model", "sonnet", "--allowedTools", "Read", "--output-format", "text",
             "--strict-mcp-config"],   # v719.1 — SKIP the user's MCP servers: dead ones (old gateways,
                                       # browser bridges) stall EVERY headless spawn — the real 90s hang
                                       # v720 — also strip ANTHROPIC_API_KEY (see _claude_env)
            capture_output=True, text=True, timeout=90, stdin=subprocess.DEVNULL, env=env)
        out = (r.stdout or "").strip()
        # tolerate markdown fences / preamble around the JSON object
        a, b = out.find("{"), out.rfind("}")
        if a < 0 or b <= a:
            err = (r.stderr or "").strip()[:160]
            ev("cap", f"vision returned no JSON (exit {r.returncode})" + (f": {err}" if err else "") or "")
            if r.returncode != 0:
                print(f"  ⚠ claude exit {r.returncode}" + (f": {err}" if err else ""))
            return EMPTY
        parsed = _parse_read(out)
        if parsed is None: return EMPTY
        parsed["ms"] = int((time.time() - t0) * 1000); parsed["mode"] = "oneshot"
        return parsed
    except subprocess.TimeoutExpired:
        ev("cap", "vision timed out (90s) — if this repeats, run: python3 tv/tv_diablo.py --test <img>")
        print("  ⚠ vision timed out (90s)")
        return EMPTY
    except Exception as e:
        ev("cap", f"read failed: {e}")
        print(f"  ⚠ read failed: {e}")
        return EMPTY

def main():
    os.makedirs(FRAMES, exist_ok=True)
    with _state_lock:
        _save({"online": True, "startedAt": int(time.time()*1000), "reads": [], "readCount": 0})   # fresh — never inherit a stale sim flag
    bridge()
    ev("boot", "scanner online — eyes at 0.5s, read-only, your subscription")
    if not os.environ.get("TV_STUB"):
        def _warm():
            t0 = time.time()
            if _WORKER.ask("Reply with exactly: ok", timeout=60) is not None:
                ev("boot", f"vision warm — session ready in {int(time.time()-t0)}s (first read will be fast)")
            else:
                ev("skip", "warm-up didn't answer — first read may be slow (one-shot fallback armed)")
        threading.Thread(target=_warm, daemon=True).start()
    if os.environ.get("CLAUDECODE"):
        ev("cap", "⚠ launched INSIDE a Claude session — vision calls can hang. Run me in a bare Terminal.")
        print("  ⚠ you're inside a Claude Code session — claude -p may hang nested. Use a BARE Terminal window.")
    print("📺 TV DIABLO — live scanner (read-only · your Claude subscription · no API keys)")
    print(f"   bridge: http://127.0.0.1:{PORT}/state  ·  mode: {'watch (Windows frames)' if WATCH_MODE else 'mac screencapture'}")
    print("   tip: run D2R fullscreen so the menu-bar clock doesn't keep the frame 'moving'")
    print("   in the bible: ⚡ session → 📺 TV DIABLO → flip the switch. Ctrl-C to stop.\n")

    frame = os.path.join(FRAMES, "live.bmp")
    last_md5, stable, last_sent_md5, last_read_t, reads = None, 0, None, 0.0, 0
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
        SETTLE = 0.03   # ≤3% of sampled pixels moving = you stopped to look (ambient animation rides under this)
        motion = sig_diff(cur, last_md5)
        # loading screens between zones are static + near-black — they settle but hold nothing readable
        if sum(cur) / max(1, len(cur)) < 14:
            if _BEAT["phase"] != "loading": ev("skip", "near-black frame (loading screen) — not worth a read")
            beat("loading", motion); last_md5 = cur; continue
        beat("watching", motion)
        stable = stable + 1 if motion <= SETTLE else 0
        last_md5 = cur
        # STABLE: two consecutive settled captures (stable==1 on the second) = a read-worthy moment
        if stable != 1:
            continue
        if sig_diff(cur, last_sent_md5) <= SETTLE:
            ev("skip", "settled, but same view I already read — waiting for something new"); continue
        if time.time() - last_read_t < MIN_GAP_S:
            ev("skip", f"settled, but only {int(time.time()-last_read_t)}s since the last read (gap {MIN_GAP_S}s)"); continue
        if reads >= SESSION_CAP:
            ev("cap", f"session cap {SESSION_CAP} reached — restart to continue")
            print(f"  ⛔ session cap ({SESSION_CAP} reads) reached — restart to continue"); time.sleep(60); continue
        last_read_t, last_sent_md5 = time.time(), cur
        reads += 1
        print(f"  👁 screen settled — reading ({reads}/{SESSION_CAP}) …")
        ev("settle", f"screen settled — something to look at. Vision read #{reads} firing")
        beat("reading", 0.0)
        rd = claude_read(frame)
        beat("watching", 0.0)   # pulse resumes immediately — the CRT verb never sticks on READING after a slow/failed read
        names = rd["names"]
        ev("read", (("🗺 "+rd["area"]+" · ") if rd["area"] else "") + rd["scene"] + " — " + (", ".join(names[:5]) + ("…" if len(names) > 5 else "") if names else "no readable item text (honest empty)") + (" ["+rd.get("mode","?")+" "+str(round(rd.get("ms",0)/1000,1))+"s]" if rd.get("ms") else ""))
        print(f"  🗺 {(rd['area'] or '?')} · {rd['scene']}  {'📦 ' + ' · '.join(names[:6]) + (' …' if len(names) > 6 else '') if names else '· nothing readable'}")
        with _state_lock:
            st = _load()
            st["reads"].append({"ts": int(time.time()*1000), "names": names, "n": reads, "area": rd["area"], "scene": rd["scene"], "tz": rd.get("tz", []), "ms": rd.get("ms", 0)})
            st["reads"] = st["reads"][-200:]
            st["readCount"] = reads
            _save(st)

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
    try:
        main()
    except KeyboardInterrupt:
        with _state_lock:
            try:
                st = _load(); st["online"] = False; _save(st)
            except Exception:
                pass
        print("\n📺 TV DIABLO off — good hunting.")
