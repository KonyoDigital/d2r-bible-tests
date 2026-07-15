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
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    except OSError as e:
        print(f"⛔ cannot bind 127.0.0.1:{PORT} — is another TV DIABLO / simulate.py already running?\n   {e}")
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

def claude_read(path):
    """One vision read on YOUR Claude subscription. Read-only tools; Sonnet (the intake-calibrated model)."""
    ap = os.path.abspath(path)
    EMPTY = {"area": "", "scene": "gameplay", "names": [], "tz": []}
    if not os.path.isfile(ap):
        print(f"  ⚠ image missing: {ap}")
        return EMPTY
    try:
        r = subprocess.run(
            ["claude", "-p", READ_PROMPT.format(path=ap),
             "--model", "sonnet", "--allowedTools", "Read", "--output-format", "text"],
            capture_output=True, text=True, timeout=180, stdin=subprocess.DEVNULL)
        out = (r.stdout or "").strip()
        # tolerate markdown fences / preamble around the JSON object
        a, b = out.find("{"), out.rfind("}")
        if a < 0 or b <= a:
            if r.returncode != 0:
                err = (r.stderr or "").strip()[:200]
                print(f"  ⚠ claude exit {r.returncode}" + (f": {err}" if err else ""))
            return EMPTY
        j = json.loads(out[a:b+1])
        names = [str(x).strip() for x in j.get("names", []) if str(x).strip()][:60]
        scene = str(j.get("scene", "gameplay")).lower()
        if scene not in ("town", "loot", "inventory", "stash", "gameplay"): scene = "gameplay"
        tz = [str(x).strip()[:40] for x in j.get("tz", []) if str(x).strip()][:8]
        return {"area": str(j.get("area", "")).strip()[:48], "scene": scene, "names": names, "tz": tz}
    except Exception as e:
        print(f"  ⚠ read failed: {e}")
        return EMPTY

def main():
    os.makedirs(FRAMES, exist_ok=True)
    with _state_lock:
        st = _load(); st["startedAt"] = int(time.time()*1000); st["online"] = True; st["reads"] = []; st["readCount"] = 0; _save(st)
    bridge()
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
        try: cur = frame_sig(frame)
        except Exception: continue
        SETTLE = 0.03   # ≤3% of sampled pixels moving = you stopped to look (ambient animation rides under this)
        stable = stable + 1 if sig_diff(cur, last_md5) <= SETTLE else 0
        last_md5 = cur
        # STABLE: two consecutive settled captures (stable==1 on the second) = a read-worthy moment
        if stable != 1 or sig_diff(cur, last_sent_md5) <= SETTLE: continue
        if time.time() - last_read_t < MIN_GAP_S: continue
        if reads >= SESSION_CAP:
            print(f"  ⛔ session cap ({SESSION_CAP} reads) reached — restart to continue"); time.sleep(60); continue
        last_read_t, last_sent_md5 = time.time(), cur
        reads += 1
        print(f"  👁 screen settled — reading ({reads}/{SESSION_CAP}) …")
        rd = claude_read(frame)
        names = rd["names"]
        print(f"  🗺 {(rd['area'] or '?')} · {rd['scene']}  {'📦 ' + ' · '.join(names[:6]) + (' …' if len(names) > 6 else '') if names else '· nothing readable'}")
        with _state_lock:
            st = _load()
            st["reads"].append({"ts": int(time.time()*1000), "names": names, "n": reads, "area": rd["area"], "scene": rd["scene"], "tz": rd.get("tz", [])})
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
