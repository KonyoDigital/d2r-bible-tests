#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# 📺 TV DIABLO — the live game-screen scanner (v710)
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
PORT   = 17771
MIN_GAP_S    = 20     # never read more often than this
SESSION_CAP  = 120    # hard stop for a whole session
POLL_S       = 3.0    # capture cadence
WATCH_MODE   = "--watch" in sys.argv   # Windows: frames arrive from capture_win.ps1

READ_PROMPT = (
    "Read the image file at {path} — it is a screenshot of Diablo II: Resurrected "
    "(Reign of the Warlock mod). If it shows an inventory, stash, or an item tooltip, list EVERY "
    "item name you can actually read: uniques, set pieces, runes (like 'Ist Rune'), gems, charms, "
    "jewels, bases. Read ONLY text that is genuinely legible — never guess or complete a name you "
    "cannot fully read. If the screen is gameplay with no readable item UI, return an empty list. "
    "Answer with STRICT JSON only, no prose: {{\"names\":[\"...\"]}}"
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
                self._hdr(); self.wfile.write(json.dumps(st).encode())
            elif self.path.startswith("/ping"):
                self._hdr(); self.wfile.write(b'{"ok":true,"tv":"diablo"}')
            else:
                self._hdr(404); self.wfile.write(b'{"error":"not found"}')
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
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

def md5f(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()

def claude_read(path):
    """One vision read on YOUR Claude subscription. Read-only tools; Sonnet (the intake-calibrated model)."""
    try:
        r = subprocess.run(
            ["claude", "-p", READ_PROMPT.format(path=path),
             "--model", "sonnet", "--allowedTools", "Read", "--output-format", "text"],
            capture_output=True, text=True, timeout=180, stdin=subprocess.DEVNULL)
        out = (r.stdout or "").strip()
        a, b = out.find("{"), out.rfind("}")
        if a < 0 or b <= a: return []
        names = json.loads(out[a:b+1]).get("names", [])
        return [str(n).strip() for n in names if str(n).strip()][:60]
    except Exception as e:
        print(f"  ⚠ read failed: {e}")
        return []

def main():
    os.makedirs(FRAMES, exist_ok=True)
    with _state_lock:
        st = _load(); st["startedAt"] = int(time.time()*1000); st["online"] = True; _save(st)
    bridge()
    print("📺 TV DIABLO — live scanner (read-only · your Claude subscription · no API keys)")
    print(f"   bridge: http://127.0.0.1:{PORT}/state  ·  mode: {'watch (Windows frames)' if WATCH_MODE else 'mac screencapture'}")
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
        try: cur = md5f(frame)
        except Exception: continue
        stable = stable + 1 if cur == last_md5 else 0
        last_md5 = cur
        # STABLE twice = you stopped to look at something new → worth one read
        if stable != 1 or cur == last_sent_md5: continue
        if time.time() - last_read_t < MIN_GAP_S: continue
        if reads >= SESSION_CAP:
            print(f"  ⛔ session cap ({SESSION_CAP} reads) reached — restart to continue"); time.sleep(60); continue
        last_read_t, last_sent_md5 = time.time(), cur
        reads += 1
        print(f"  👁 screen settled — reading ({reads}/{SESSION_CAP}) …")
        names = claude_read(frame)
        print(f"  {'📦 ' + ' · '.join(names[:6]) + (' …' if len(names) > 6 else '') if names else '· nothing readable (gameplay frame)'}")
        with _state_lock:
            st = _load()
            st["reads"].append({"ts": int(time.time()*1000), "names": names})
            st["reads"] = st["reads"][-200:]
            st["readCount"] = reads
            _save(st)

if __name__ == "__main__":
    # one-shot validation: python3 tv/tv_diablo.py --test <image>  (run in YOUR terminal —
    # a Claude Code session cannot nest another; from a normal shell this is a plain call)
    if "--test" in sys.argv:
        img = sys.argv[sys.argv.index("--test") + 1]
        print("📺 test read:", img)
        print(json.dumps(claude_read(img), indent=1))
        sys.exit(0)
    try: main()
    except KeyboardInterrupt:
        print("\n📺 TV DIABLO off — good hunting.")
